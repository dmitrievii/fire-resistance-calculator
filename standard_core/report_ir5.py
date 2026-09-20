"""REPORT-IR5: conservative engineering summary over REPORT-IR4.

The summary answers the questions a calculation report reader asks first:
which checks actually ran, what they returned, what final result nodes emitted,
and whether any executed route stopped fail-closed.

This layer deliberately does *not* infer a governing utilization or invent an
overall structural PASS from quantity names. A governing result is emitted only
when the frozen DAG explicitly declares presentation metadata for it in a future
revision. Until then the report states that governing selection is not declared.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping

from .report_ir4 import build_report_ir4

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


def _check_verdict(outputs: list[Mapping[str, Any]]) -> tuple[str, str]:
    """Interpret only explicit boolean outputs of a CHECK block.

    A numeric utilization is intentionally not interpreted from its name or
    magnitude. That would duplicate normative semantics in the report layer.
    """
    bool_values = [row.get("raw_value") for row in outputs if isinstance(row.get("raw_value"), bool)]
    non_bool_values = [row for row in outputs if not isinstance(row.get("raw_value"), bool)]
    if bool_values and not non_bool_values:
        if all(bool_values):
            return "PASS", "explicit_boolean_check_outputs"
        return "FAIL", "explicit_boolean_check_outputs"
    return "UNRESOLVED", "no_unambiguous_boolean_verdict_in_trace"


def _summary_from_ir4(ir4: Mapping[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    fail_closed: list[dict[str, Any]] = []

    for block in ir4.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
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
            verdict, source = _check_verdict(outputs)
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

    # This is deliberately a report-state classification, not an engineering
    # compliance verdict for the member as a whole.
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
        "governing": {
            "status": "NOT_DECLARED_BY_DAG",
            "reason": (
                "REPORT-IR does not infer governing utilization from quantity names or values. "
                "A governing result must be explicitly declared by frozen DAG presentation metadata."
            ),
            "candidates": [],
        },
    }


def build_report_ir5(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    ir4 = build_report_ir4(model, session_or_snapshot)
    summary = _summary_from_ir4(ir4)
    report = _deep(ir4)
    report["schema"] = REPORT_IR5_SCHEMA
    report["contract"] = REPORT_IR5_CONTRACT
    report["source_report_schema"] = ir4.get("schema")
    report["source_report_sha256"] = ir4.get("report_sha256")
    report["summary"] = summary
    report["audit"] = _deep(ir4.get("audit") or {})
    report["audit"].update(
        {
            "summary_recomputed_engineering_checks": False,
            "summary_inferred_numeric_check_verdicts": False,
            "summary_inferred_governing_result": False,
            "boolean_check_verdict_source": "completed_CHECK_block_trace_outputs_only",
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
