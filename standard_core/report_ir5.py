"""REPORT-IR5: conservative engineering summary over REPORT-IR4.

The summary reports only execution evidence that already exists in the trace.
PASS/FAIL comes from explicit boolean outputs (or a declared boolean verdict
quantity). Governing values are shown only when a DAG-bound report metadata
contract explicitly declares both a scope and a produced quantity.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping

from .report_ir4 import build_report_ir4
from .report_metadata import report_metadata_for_model, report_metadata_identity, report_spec_for_node

REPORT_IR5_SCHEMA = "fire_report_ir_v4"
REPORT_IR5_CONTRACT = "conservative_engineering_summary_v4"


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


def _display_value(row: Mapping[str, Any]) -> str:
    value = row.get("raw_value")
    if isinstance(value, float):
        text = format(value, ".12g")
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif value is None:
        text = "null"
    else:
        text = str(value)
    unit = row.get("canonical_unit")
    return f"{text} {unit}" if unit else text


def _output_view(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "quantity_id": row.get("quantity_id"),
        "symbol": row.get("symbol") or row.get("quantity_id"),
        "name_ru": row.get("name_ru") or row.get("quantity_id"),
        "raw_value": _deep(row.get("raw_value")),
        "canonical_unit": row.get("canonical_unit"),
        "display_value": _display_value(row),
    }


def _check_verdict(
    outputs: list[Mapping[str, Any]],
    presentation: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Read only explicit boolean verdict evidence; never infer from numbers."""
    presentation = presentation if isinstance(presentation, Mapping) else {}
    declared = presentation.get("verdict_quantity_id")
    if isinstance(declared, str):
        matches = [row for row in outputs if row.get("quantity_id") == declared]
        if len(matches) == 1 and isinstance(matches[0].get("raw_value"), bool):
            return (
                "PASS" if matches[0]["raw_value"] else "FAIL",
                "declared_boolean_verdict_quantity",
            )
        return "UNRESOLVED", "declared_verdict_quantity_missing_or_non_boolean_in_trace"

    bool_values = [row.get("raw_value") for row in outputs if isinstance(row.get("raw_value"), bool)]
    non_bool_values = [row for row in outputs if not isinstance(row.get("raw_value"), bool)]
    if bool_values and not non_bool_values:
        if all(bool_values):
            return "PASS", "explicit_boolean_check_outputs"
        return "FAIL", "explicit_boolean_check_outputs"
    return "UNRESOLVED", "no_unambiguous_boolean_verdict_in_trace"


def _governing_declarations_from_blocks(blocks: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    seen_scopes: set[str] = set()
    for block in blocks:
        presentation = block.get("presentation") or {}
        if not isinstance(presentation, Mapping):
            continue
        qid = presentation.get("governing_quantity_id")
        scope = presentation.get("governing_scope")
        if not isinstance(qid, str) or not isinstance(scope, str) or not scope.strip():
            continue
        if scope in seen_scopes:
            continue
        outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
        matches = [row for row in outputs if row.get("quantity_id") == qid]
        if len(matches) != 1:
            continue
        seen_scopes.add(scope)
        declarations.append(
            {
                "scope": scope,
                "scope_title_ru": presentation.get("governing_scope_title_ru") or scope,
                "report_block_id": block.get("report_block_id"),
                "sequence": block.get("sequence"),
                "owner_node_id": block.get("owner_node_id"),
                "owner_standard_id": block.get("owner_standard_id"),
                "title": block.get("title"),
                "normative_refs": _deep(block.get("normative_refs") or []),
                "quantity": _output_view(matches[0]),
                "source": "explicit_dag_bound_report_metadata_plus_execution_trace",
            }
        )
    return declarations


def _summary_from_ir4(ir4: Mapping[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    fail_closed: list[dict[str, Any]] = []
    blocks = [row for row in ir4.get("blocks") or [] if isinstance(row, Mapping)]

    for block in blocks:
        kind = block.get("kind")
        outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
        common = {
            "report_block_id": block.get("report_block_id"),
            "sequence": block.get("sequence"),
            "owner_node_id": block.get("owner_node_id"),
            "owner_standard_id": block.get("owner_standard_id"),
            "title": block.get("title"),
            "normative_refs": _deep(block.get("normative_refs") or []),
        }
        if kind == "CHECK":
            verdict, source = _check_verdict(outputs, block.get("presentation"))
            checks.append(
                {
                    **common,
                    "verdict": verdict,
                    "verdict_source": source,
                    "outputs": [_output_view(row) for row in outputs],
                }
            )
        elif kind == "RESULT":
            results.append({**common, "outputs": [_output_view(row) for row in outputs]})
        elif kind == "FAIL_CLOSED":
            fail_closed.append(
                {
                    **common,
                    "message": block.get("message"),
                    "failure": _deep(block.get("failure")),
                }
            )

    check_counts = {
        "PASS": sum(1 for row in checks if row["verdict"] == "PASS"),
        "FAIL": sum(1 for row in checks if row["verdict"] == "FAIL"),
        "UNRESOLVED": sum(1 for row in checks if row["verdict"] == "UNRESOLVED"),
    }

    if fail_closed:
        summary_status = "FAIL_CLOSED"
    elif check_counts["FAIL"]:
        summary_status = "EXECUTED_CHECK_FAILED"
    elif check_counts["UNRESOLVED"]:
        summary_status = "CHECK_VERDICT_NOT_EXPLICIT"
    elif checks:
        summary_status = "EXECUTED_BOOLEAN_CHECKS_PASS"
    else:
        summary_status = "NO_COMPLETED_CHECKS_YET"

    governing_rows = _governing_declarations_from_blocks(blocks)
    governing = {
        "status": "EXECUTED_DECLARATIONS" if governing_rows else "NOT_DECLARED_BY_DAG",
        "reason": (
            "Only governing quantities explicitly declared by DAG-bound report metadata and materialized "
            "by the execution trace are shown; REPORT-IR performs no global max/min selection."
            if governing_rows
            else "REPORT-IR does not infer governing utilization from quantity names or values."
        ),
        "candidates": governing_rows,
    }

    return {
        "summary_status": summary_status,
        "summary_status_scope": "report_execution_state_not_global_engineering_certification",
        "session_status": ir4.get("session_status"),
        "executed_block_count": ir4.get("block_count", 0),
        "executed_route_edge_count": len(ir4.get("selected_route") or []),
        "check_count": len(checks),
        "check_counts": check_counts,
        "checks": checks,
        "result_block_count": len(results),
        "results": results,
        "fail_closed_count": len(fail_closed),
        "fail_closed": fail_closed,
        "governing": governing,
    }


def _enrich_ir4_with_report_metadata(model: Any, ir4: Mapping[str, Any]) -> dict[str, Any]:
    enriched = _deep(ir4)
    for block in enriched.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        node_id = block.get("owner_node_id")
        if not isinstance(node_id, str):
            continue
        spec = report_spec_for_node(model, node_id)
        if not spec:
            continue
        presentation = block.get("presentation")
        merged = dict(presentation) if isinstance(presentation, Mapping) else {}
        for key, value in spec.items():
            if key in merged and merged[key] != value:
                raise ValueError(f"conflicting REPORT-IR presentation metadata for {node_id}.{key}")
            merged[key] = _deep(value)
        block["presentation"] = merged
        title = spec.get("title_ru") or spec.get("title")
        if isinstance(title, str) and title.strip():
            block["title"] = title.strip()
    return enriched


def _declared_metadata_scopes(model: Any) -> list[str]:
    payload = report_metadata_for_model(model)
    scopes: list[str] = []
    for spec in (payload.get("node_report_specs") or {}).values():
        if isinstance(spec, Mapping) and isinstance(spec.get("governing_scope"), str):
            scopes.append(str(spec["governing_scope"]))
    return sorted(set(scopes))


def build_report_ir5(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    ir4 = _enrich_ir4_with_report_metadata(model, build_report_ir4(model, session_or_snapshot))
    summary = _summary_from_ir4(ir4)
    declared_scopes = _declared_metadata_scopes(model)
    if summary["governing"]["status"] == "NOT_DECLARED_BY_DAG" and declared_scopes:
        summary["governing"] = {
            "status": "DECLARED_BY_DAG_NOT_EXECUTED",
            "reason": (
                "Scoped governing metadata exists in the DAG-bound sidecar, but none of those producer nodes "
                "has completed on the current execution route."
            ),
            "candidates": [],
        }

    report = _deep(ir4)
    report["schema"] = REPORT_IR5_SCHEMA
    report["contract"] = REPORT_IR5_CONTRACT
    report["source_report_schema"] = ir4.get("schema")
    report["source_report_sha256"] = ir4.get("report_sha256")
    report["summary"] = summary
    report["audit"] = _deep(ir4.get("audit") or {})
    metadata_identity = report_metadata_identity(model)
    report["audit"].update(
        {
            "summary_recomputed_engineering_checks": False,
            "summary_inferred_numeric_check_verdicts": False,
            "summary_inferred_governing_result": False,
            "boolean_check_verdict_source": "completed_CHECK_block_trace_outputs_or_declared_boolean_quantity",
            "governing_value_source": "explicit_dag_bound_report_metadata_plus_completed_trace",
            "report_metadata_revision_id": metadata_identity.get("revision_id"),
            "report_metadata_base_graph_sha256": metadata_identity.get("base_graph_sha256"),
        }
    )
    report.pop("report_sha256", None)
    canonical = json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()
    return report


def report_ir5_json(model: Any, session_or_snapshot: Any, *, indent: int = 2) -> str:
    report = build_report_ir5(model, session_or_snapshot)
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=indent, allow_nan=False) + "\n"
