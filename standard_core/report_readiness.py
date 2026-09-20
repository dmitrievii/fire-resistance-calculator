"""Static report-readiness census for the frozen SP16/SP554 DAG.

REPORT-IR7 does not execute the calculation graph and does not derive any
engineering result.  It answers a narrower audit question: is the metadata in
the frozen DAG sufficient for an unambiguous, publication-grade calculation
report without the presentation layer guessing normative semantics?

The census is deliberately conservative.  A compliance check is considered to
have explicit verdict semantics only when its produced quantities are boolean
(or a future ``report_spec.verdict_quantity_id`` points to a boolean output).
Likewise, a governing result is considered declared only through the explicit
``report_spec.governing_quantity_id`` contract.  Numeric quantity names and
magnitudes are never interpreted heuristically.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Mapping


REPORT_READINESS_SCHEMA = "fire_report_readiness_v1"
REPORT_READINESS_CONTRACT = "static_dag_report_metadata_census_v1"


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


def _quantity_index(model: Any) -> dict[str, Mapping[str, Any]]:
    graph = getattr(model, "graph", {})
    out: dict[str, Mapping[str, Any]] = {}
    for row in (graph.get("quantities") if isinstance(graph, Mapping) else []) or []:
        if isinstance(row, Mapping) and isinstance(row.get("id"), str):
            out[str(row["id"])] = row
    return out


def _output_ids(node: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for row in node.get("produces") or []:
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
            out.append(str(row["quantity_id"]))
    return out


def _report_spec(node: Mapping[str, Any]) -> Mapping[str, Any]:
    value = node.get("report_spec")
    return value if isinstance(value, Mapping) else {}


def _is_boolean_quantity(quantity: Mapping[str, Any] | None) -> bool:
    if not isinstance(quantity, Mapping):
        return False
    dtype = str(quantity.get("data_type") or quantity.get("type") or "").lower()
    return dtype in {"bool", "boolean"}


def _check_readiness(
    node_id: str,
    node: Mapping[str, Any],
    quantities: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    outputs = _output_ids(node)
    bool_outputs = [qid for qid in outputs if _is_boolean_quantity(quantities.get(qid))]
    spec = _report_spec(node)
    declared = spec.get("verdict_quantity_id")

    if isinstance(declared, str) and declared in bool_outputs:
        status = "EXPLICIT_VERDICT_QUANTITY"
        blocker = None
    elif outputs and len(bool_outputs) == len(outputs):
        status = "BOOLEAN_OUTPUTS_UNAMBIGUOUS"
        blocker = None
    else:
        status = "NEEDS_BOOLEAN_VERDICT_OUTPUT"
        blocker = {
            "kind": "CHECK_VERDICT_SEMANTICS",
            "node_id": node_id,
            "message": (
                "Compliance check has no unambiguous boolean verdict output. "
                "REPORT-IR must not infer PASS/FAIL from numeric quantity names or magnitudes."
            ),
            "output_quantity_ids": outputs,
            "boolean_output_quantity_ids": bool_outputs,
        }

    return {
        "node_id": node_id,
        "status": status,
        "output_quantity_ids": outputs,
        "boolean_output_quantity_ids": bool_outputs,
        "declared_verdict_quantity_id": declared if isinstance(declared, str) else None,
        "blocker": blocker,
    }


def _governing_declarations(
    nodes: Mapping[str, Mapping[str, Any]],
    quantities: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    declarations: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for node_id, node in nodes.items():
        spec = _report_spec(node)
        qid = spec.get("governing_quantity_id")
        if not isinstance(qid, str):
            continue
        outputs = _output_ids(node)
        row = {
            "node_id": str(node_id),
            "quantity_id": qid,
            "is_produced_by_node": qid in outputs,
            "quantity_exists": qid in quantities,
        }
        if row["is_produced_by_node"] and row["quantity_exists"]:
            declarations.append(row)
        else:
            invalid.append(row)
    return declarations, invalid


def build_report_readiness(model: Any) -> dict[str, Any]:
    """Return a deterministic static census of report metadata readiness.

    No session is accepted by design: this function cannot execute a route,
    evaluate expressions, interpolate tables or inspect calculation values.
    """
    graph = getattr(model, "graph", {})
    nodes_raw = getattr(model, "nodes", {})
    nodes: dict[str, Mapping[str, Any]] = {
        str(node_id): node
        for node_id, node in (nodes_raw.items() if isinstance(nodes_raw, Mapping) else [])
        if isinstance(node, Mapping)
    }
    quantities = _quantity_index(model)

    node_type_counts: Counter[str] = Counter()
    nodes_without_normative_refs: list[str] = []
    nodes_with_report_spec: list[str] = []
    formula_nodes_without_presentation_formula: list[str] = []
    check_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    for node_id in sorted(nodes):
        node = nodes[node_id]
        ntype = str(node.get("node_type") or "UNKNOWN")
        node_type_counts[ntype] += 1
        refs = node.get("normative_refs") or []
        if not refs:
            nodes_without_normative_refs.append(node_id)

        spec = _report_spec(node)
        if spec:
            nodes_with_report_spec.append(node_id)

        if ntype in {"calculation", "compliance_check"}:
            formula = spec.get("formula_latex")
            if not isinstance(formula, str) or not formula.strip():
                formula_nodes_without_presentation_formula.append(node_id)

        if ntype == "compliance_check":
            row = _check_readiness(node_id, node, quantities)
            check_rows.append(row)
            if row["blocker"] is not None:
                blockers.append(_deep(row["blocker"]))

    governing, invalid_governing = _governing_declarations(nodes, quantities)
    if invalid_governing:
        for row in invalid_governing:
            blockers.append(
                {
                    "kind": "INVALID_GOVERNING_DECLARATION",
                    **_deep(row),
                    "message": "Declared governing quantity is not a valid output of the declaring node.",
                }
            )
    if not governing:
        blockers.append(
            {
                "kind": "GOVERNING_RESULT_SEMANTICS",
                "node_id": None,
                "message": (
                    "No report_spec.governing_quantity_id is declared in the frozen DAG. "
                    "The report must therefore keep governing selection as NOT_DECLARED_BY_DAG."
                ),
            }
        )

    check_status_counts = Counter(str(row["status"]) for row in check_rows)
    explicit_formula_count = (
        node_type_counts.get("calculation", 0)
        + node_type_counts.get("compliance_check", 0)
        - len(formula_nodes_without_presentation_formula)
    )
    formula_candidate_count = node_type_counts.get("calculation", 0) + node_type_counts.get("compliance_check", 0)

    if blockers:
        status = "NEEDS_DAG_METADATA"
    else:
        status = "REPORT_METADATA_COMPLETE"

    return {
        "schema": REPORT_READINESS_SCHEMA,
        "contract": REPORT_READINESS_CONTRACT,
        "graph_id": graph.get("graph_id") if isinstance(graph, Mapping) else None,
        "graph_sha256": getattr(model, "graph_sha256", None),
        "status": status,
        "status_scope": "report_metadata_readiness_not_engineering_readiness",
        "node_count": len(nodes),
        "quantity_count": len(quantities),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "normative_reference_coverage": {
            "nodes_with_refs": len(nodes) - len(nodes_without_normative_refs),
            "nodes_without_refs": len(nodes_without_normative_refs),
            "nodes_without_refs_ids": nodes_without_normative_refs,
        },
        "presentation_metadata_coverage": {
            "nodes_with_report_spec": len(nodes_with_report_spec),
            "nodes_without_report_spec": len(nodes) - len(nodes_with_report_spec),
            "nodes_with_report_spec_ids": nodes_with_report_spec,
            "formula_or_check_node_count": formula_candidate_count,
            "formula_or_check_nodes_with_formula_latex": explicit_formula_count,
            "formula_or_check_nodes_without_formula_latex": len(formula_nodes_without_presentation_formula),
            "formula_or_check_nodes_without_formula_latex_ids": formula_nodes_without_presentation_formula,
            "note": (
                "formula_latex is presentation metadata only. Its absence does not block trace reporting; "
                "the frozen execution expression can still be shown verbatim."
            ),
        },
        "check_verdict_readiness": {
            "check_node_count": len(check_rows),
            "status_counts": dict(sorted(check_status_counts.items())),
            "checks": check_rows,
            "unambiguous_check_count": sum(
                1
                for row in check_rows
                if row["status"] in {"EXPLICIT_VERDICT_QUANTITY", "BOOLEAN_OUTPUTS_UNAMBIGUOUS"}
            ),
            "needs_explicit_verdict_count": sum(
                1 for row in check_rows if row["status"] == "NEEDS_BOOLEAN_VERDICT_OUTPUT"
            ),
        },
        "governing_readiness": {
            "status": "DECLARED" if governing else "NOT_DECLARED_BY_DAG",
            "valid_declarations": governing,
            "invalid_declarations": invalid_governing,
            "contract": "report_spec.governing_quantity_id must reference an output quantity of the same node",
        },
        "blocking_metadata_gap_count": len(blockers),
        "blocking_metadata_gaps": blockers,
        "audit": {
            "executes_dag_nodes": False,
            "reads_session_values": False,
            "recomputes_engineering_values": False,
            "infers_numeric_pass_fail": False,
            "infers_governing_from_names_or_values": False,
        },
    }
