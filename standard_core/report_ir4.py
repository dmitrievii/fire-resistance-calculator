"""REPORT-IR4: human-readable calculation report projection.

This layer turns REPORT-IR2/3 evidence into report-ready presentation data:
formula -> numeric substitution -> production result, table interpolation
substitution, section grouping, and the exact selected DAG route.

It is deliberately display-only.  Expressions and interpolation formulae are
never evaluated here.  Numerical results always come from the completed
production trace, while selected piecewise expressions/rules come from runtime
audit evidence captured immediately after the successful declarative execution.
"""
from __future__ import annotations

import copy
import json
import re
from hashlib import sha256
from typing import Any, Mapping

from .declarative_case_evidence import get_case_runtime_evidence
from .report_ir2 import build_report_ir2

REPORT_IR4_SCHEMA = "fire_report_ir_v3"
REPORT_IR4_CONTRACT = "human_readable_trace_projection_v3"

SECTION_ORDER = (
    "input_data",
    "routing_and_assumptions",
    "geometry",
    "calculation",
    "verification",
    "results",
    "audit",
)
SECTION_TITLES_RU = {
    "input_data": "Исходные данные",
    "routing_and_assumptions": "Расчётная схема, применимость и принятые ветви",
    "geometry": "Геометрические характеристики",
    "calculation": "Расчёт",
    "verification": "Проверки",
    "results": "Результаты",
    "audit": "Диагностика и ограничения",
}


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


def _raw_value_map(rows: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in rows or []:
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
            out[str(row["quantity_id"])] = _deep(row.get("raw_value"))
    return out


def _fmt_scalar(value: Any) -> str:
    """Deterministic display formatting only; no engineering conversion."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return str(value)


def _display_value(row: Mapping[str, Any]) -> str:
    value = _fmt_scalar(row.get("raw_value"))
    unit = row.get("canonical_unit")
    return f"{value} {unit}" if unit else value


def _token_substitute(expression: str, bindings: list[Mapping[str, Any]]) -> tuple[str, list[str]]:
    """Textually substitute complete variable tokens without evaluating them."""
    rendered = str(expression)
    missing: list[str] = []
    usable: list[tuple[str, Any]] = []
    for row in bindings:
        variable = row.get("variable")
        if not isinstance(variable, str) or not variable:
            continue
        if not row.get("present_in_trace"):
            missing.append(variable)
            continue
        usable.append((variable, row.get("raw_value")))

    # Longest first is defensive for non-identifier expression languages.  The
    # identifier lookarounds also ensure x never replaces the x inside xx/max.
    for variable, value in sorted(usable, key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(variable) + r"(?![A-Za-z0-9_])")
        rendered = pattern.sub(f"({_fmt_scalar(value)})", rendered)
    return rendered, sorted(set(missing))


def _formula_human_readable(
    block: Mapping[str, Any],
    runtime_case: Mapping[str, Any] | None,
) -> dict[str, Any]:
    evidence = block.get("execution_evidence") or {}
    spec = block.get("execution_spec") or {}
    expression = None
    expression_source = "dag_expression"
    case_status = "NOT_REQUIRED"

    if isinstance(runtime_case, Mapping):
        if runtime_case.get("capture_status") == "CAPTURED" and runtime_case.get("selected_expression"):
            expression = str(runtime_case["selected_expression"])
            expression_source = "runtime_selected_dag_expression"
            case_status = "CAPTURED_BY_RUNTIME_AUDIT"
        elif spec.get("cases"):
            case_status = str(runtime_case.get("capture_status") or "NOT_CAPTURED_BY_RUNTIME")
    if expression is None and isinstance(evidence.get("expression"), str):
        expression = str(evidence["expression"])
    if expression is None and isinstance(spec.get("expression"), str):
        expression = str(spec["expression"])

    bindings = [row for row in evidence.get("bindings") or [] if isinstance(row, Mapping)]
    substituted = None
    missing: list[str] = []
    if expression:
        substituted, missing = _token_substitute(expression, bindings)

    binding_lines = [
        {
            "variable": row.get("variable"),
            "quantity_id": row.get("quantity_id"),
            "symbol": row.get("symbol"),
            "display_value": _display_value(row) if row.get("present_in_trace") else "—",
            "present_in_trace": bool(row.get("present_in_trace")),
        }
        for row in bindings
    ]
    result_lines = [
        {
            "quantity_id": row.get("quantity_id"),
            "symbol": row.get("symbol") or row.get("quantity_id"),
            "display_value": _display_value(row),
            "raw_value": _deep(row.get("raw_value")),
            "canonical_unit": row.get("canonical_unit"),
        }
        for row in block.get("outputs") or []
        if isinstance(row, Mapping)
    ]

    return {
        "mode": "formula_substitution",
        "formula_expression": expression,
        "expression_source": expression_source,
        "substituted_expression": substituted,
        "missing_binding_variables": missing,
        "bindings": binding_lines,
        "result_lines": result_lines,
        "piecewise_case_status": case_status,
        "selected_case_index": runtime_case.get("selected_case_index") if isinstance(runtime_case, Mapping) else None,
        "selected_case_condition": _deep((runtime_case.get("selected_case") or {}).get("when")) if isinstance(runtime_case, Mapping) else None,
        "report_evaluated_expression": False,
        "result_source": "production_execution_trace",
    }


def _role_rows(selected_rows: Any) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for item in selected_rows or []:
        if not isinstance(item, Mapping) or not isinstance(item.get("role"), str):
            continue
        row = item.get("row")
        if isinstance(row, Mapping):
            out[str(item["role"])] = row
    return out


def _lookup_human_readable(block: Mapping[str, Any]) -> dict[str, Any]:
    evidence = block.get("execution_evidence") or {}
    runtime = evidence.get("runtime_lookup_evidence") or {}
    selected = evidence.get("selected_dataset_rows") or []
    role_rows = _role_rows(selected)
    selection_mode = runtime.get("selection_mode")
    output_lines: list[dict[str, Any]] = []

    for output in evidence.get("output_bindings") or []:
        if not isinstance(output, Mapping):
            continue
        field = output.get("dataset_field")
        symbol = output.get("symbol") or output.get("quantity_id") or field
        formula = None
        substitution = None

        if selection_mode == "linear_bracket" and field is not None:
            lower = role_rows.get("lower") or {}
            upper = role_rows.get("upper") or {}
            if field in lower and field in upper:
                fraction = runtime.get("fraction")
                formula = f"{symbol} = {field}_0 + f·({field}_1 - {field}_0)"
                substitution = (
                    f"{symbol} = {_fmt_scalar(lower[field])} + {_fmt_scalar(fraction)}·"
                    f"({_fmt_scalar(upper[field])} - {_fmt_scalar(lower[field])})"
                )
        elif selection_mode in {"exact", "linear_exact_knot"} and field is not None:
            exact = role_rows.get("exact") or {}
            if field in exact:
                formula = f"{symbol} = {field}"
                substitution = f"{symbol} = {_fmt_scalar(exact[field])}"
        elif selection_mode == "bilinear_grid" and field is not None:
            required = ("x0_y0", "x1_y0", "x0_y1", "x1_y1")
            if all(field in (role_rows.get(role) or {}) for role in required):
                axes = list(runtime.get("axes") or [])
                fractions = runtime.get("fractions") or {}
                fx = fractions.get(axes[0]) if len(axes) > 0 else None
                fy = fractions.get(axes[1]) if len(axes) > 1 else None
                q00 = role_rows["x0_y0"][field]
                q10 = role_rows["x1_y0"][field]
                q01 = role_rows["x0_y1"][field]
                q11 = role_rows["x1_y1"][field]
                formula = (
                    f"{symbol} = (1-fx)(1-fy)·q00 + fx(1-fy)·q10 + "
                    "(1-fx)fy·q01 + fx·fy·q11"
                )
                substitution = (
                    f"{symbol} = (1-{_fmt_scalar(fx)})(1-{_fmt_scalar(fy)})·{_fmt_scalar(q00)} + "
                    f"{_fmt_scalar(fx)}(1-{_fmt_scalar(fy)})·{_fmt_scalar(q10)} + "
                    f"(1-{_fmt_scalar(fx)}){_fmt_scalar(fy)}·{_fmt_scalar(q01)} + "
                    f"{_fmt_scalar(fx)}·{_fmt_scalar(fy)}·{_fmt_scalar(q11)}"
                )

        output_lines.append(
            {
                "quantity_id": output.get("quantity_id"),
                "symbol": symbol,
                "dataset_field": field,
                "formula_expression": formula,
                "substituted_expression": substitution,
                "display_result": _display_value(output) if output.get("present_in_trace") else "—",
                "raw_result": _deep(output.get("raw_value")),
                "canonical_unit": output.get("canonical_unit"),
            }
        )

    return {
        "mode": "lookup_substitution",
        "dataset_id": evidence.get("dataset_id"),
        "runtime_row_status": evidence.get("selected_dataset_rows_status"),
        "selection_mode": selection_mode,
        "output_lines": output_lines,
        "report_evaluated_interpolation": False,
        "result_source": "production_execution_trace",
    }


def _decision_human_readable(block: Mapping[str, Any], edge: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "mode": "route_decision",
        "selected_edge_id": block.get("selected_edge_id"),
        "from_node_id": edge.get("from_node_id") if isinstance(edge, Mapping) else block.get("owner_node_id"),
        "to_node_id": edge.get("to_node_id") if isinstance(edge, Mapping) else None,
        "edge_type": edge.get("edge_type") if isinstance(edge, Mapping) else None,
        "condition": _deep(edge.get("condition")) if isinstance(edge, Mapping) else None,
        "decision_outputs": _deep(block.get("outputs") or []),
        "route_condition_recomputed_by_report": False,
        "route_source": "completed_execution_trace.selected_edge_id",
    }


def _edge_index(model: Any) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for edge in getattr(model, "edges", []) or []:
        if isinstance(edge, Mapping) and isinstance(edge.get("id"), str):
            out[str(edge["id"])] = edge
    return out


def _section_index(blocks: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    first_sequence: dict[str, int] = {}
    for block in blocks:
        key = str(block.get("section_key") or "audit")
        grouped.setdefault(key, []).append(str(block.get("report_block_id")))
        first_sequence.setdefault(key, int(block.get("sequence") or 0))

    ordered_keys = [key for key in SECTION_ORDER if key in grouped]
    ordered_keys.extend(
        key
        for key in sorted(grouped, key=lambda k: (first_sequence.get(k, 0), k))
        if key not in ordered_keys
    )
    return [
        {
            "section_key": key,
            "title_ru": SECTION_TITLES_RU.get(key, key),
            "block_ids": grouped[key],
        }
        for key in ordered_keys
    ]


def build_report_ir4(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    """Build report-ready evidence without running any engineering calculation."""
    ir2 = build_report_ir2(model, session_or_snapshot)
    edges = _edge_index(model)
    blocks: list[dict[str, Any]] = []
    route: list[dict[str, Any]] = []

    for source in ir2.get("blocks") or []:
        block = _deep(source)
        node_id = str(block.get("owner_node_id") or "")
        runtime_case = get_case_runtime_evidence(
            model,
            node_id,
            _raw_value_map(block.get("inputs")),
            _raw_value_map(block.get("outputs")),
        )
        block["runtime_case_evidence"] = runtime_case

        mode = (block.get("execution_spec") or {}).get("mode")
        edge_id = block.get("selected_edge_id")
        edge = edges.get(str(edge_id)) if edge_id else None
        if mode in {"calculation_spec", "check_spec"}:
            block["human_readable"] = _formula_human_readable(block, runtime_case)
        elif mode == "lookup_spec":
            block["human_readable"] = _lookup_human_readable(block)
        elif block.get("kind") == "BRANCH_DECISION" or edge_id:
            block["human_readable"] = _decision_human_readable(block, edge)
        else:
            block["human_readable"] = {
                "mode": "trace_values",
                "result_lines": [
                    {
                        "quantity_id": row.get("quantity_id"),
                        "symbol": row.get("symbol") or row.get("quantity_id"),
                        "display_value": _display_value(row),
                    }
                    for row in block.get("outputs") or []
                    if isinstance(row, Mapping)
                ],
                "result_source": "production_execution_trace",
            }

        if edge_id:
            route.append(
                {
                    "sequence": block.get("sequence"),
                    "report_block_id": block.get("report_block_id"),
                    "selected_edge_id": edge_id,
                    "from_node_id": edge.get("from_node_id") if isinstance(edge, Mapping) else node_id,
                    "to_node_id": edge.get("to_node_id") if isinstance(edge, Mapping) else None,
                    "edge_type": edge.get("edge_type") if isinstance(edge, Mapping) else None,
                    "condition": _deep(edge.get("condition")) if isinstance(edge, Mapping) else None,
                }
            )
        blocks.append(block)

    report = {
        "schema": REPORT_IR4_SCHEMA,
        "contract": REPORT_IR4_CONTRACT,
        "source_report_schema": ir2.get("schema"),
        "source_report_sha256": ir2.get("report_sha256"),
        "graph_id": ir2.get("graph_id"),
        "graph_sha256": ir2.get("graph_sha256"),
        "session_schema": ir2.get("session_schema"),
        "session_status": ir2.get("session_status"),
        "entry_node_id": ir2.get("entry_node_id"),
        "current_node_id": ir2.get("current_node_id"),
        "block_count": len(blocks),
        "blocks": blocks,
        "sections": _section_index(blocks),
        "selected_route": route,
        "dag_census": _deep(ir2.get("dag_census") or {}),
        "audit": {
            "calculation_values_recomputed_by_report": False,
            "formula_expressions_evaluated_by_report": False,
            "table_interpolation_recomputed_by_report": False,
            "route_conditions_recomputed_by_report": False,
            "numeric_substitution_is_text_only": True,
            "result_source": "completed_production_execution_trace",
            "formula_source": "frozen_dag_plus_runtime_selected_case_evidence",
            "lookup_row_source": "runtime_audit_of_production_lookup",
            "route_source": "completed_execution_trace.selected_edge_id",
            "source_ir2_audit": _deep(ir2.get("audit") or {}),
        },
    }
    canonical = json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()
    return report


def report_ir4_json(model: Any, session_or_snapshot: Any, *, indent: int = 2) -> str:
    report = build_report_ir4(model, session_or_snapshot)
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=indent, allow_nan=False) + "\n"
