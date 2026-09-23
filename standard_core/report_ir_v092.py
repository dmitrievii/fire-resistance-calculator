"""v0.92 REPORT-IR remediation for final SP554 §9.1.

The frozen v0.3.70 DAG and its v0.3.72 report sidecar intentionally preserve
the pre-final-publication §9.1 expression.  The active v0.92 guided overlay,
however, executes the final equation with mandatory ``gamma_ct=1.1`` and emits
a typed calculation-evidence object.

This module is a report-only reconciliation layer over REPORT-IR5.  It does not
calculate gamma_T.  For an executed active-v0.92 ``SP554_C_9_1`` block it:

* requires the typed runtime evidence emitted by that exact producer;
* verifies that the evidence identifies the final §9.1 formula and gamma_ct;
* replaces only the stale presentation formula/template inherited from the
  frozen sidecar;
* leaves all numerical inputs/results and execution evidence untouched.

A completed v0.92 §9.1 block without the typed evidence fails closed rather than
silently falling back to the historical formula.
"""
from __future__ import annotations

import copy
import json
import math
from hashlib import sha256
from typing import Any, Mapping

from .fire_sp554_runtime_v091 import GAMMA_CT
from .fire_sp554_runtime_v092 import (
    TENSION_FORMULA_ID,
    TENSION_FORMULA_LATEX,
    TENSION_NODE_ID,
    TENSION_TRACE_QID,
    TENSION_TRACE_SCHEMA,
)
from .fire_sp554_v092_guided_overlay import GRAPH_SUFFIX, TENSION_ALGORITHM_ID
from .report_ir5 import build_report_ir5

REPORT_V092_CONTRACT = "v092_sp554_9_1_runtime_trace_reconciled"
TENSION_SUBSTITUTION_TEMPLATE_LATEX = (
    r"\gamma_T=\frac{|{N_force}|}"
    r"{{A_net}\cdot {fy_norm}\cdot 1.1\cdot {gamma_c_tension}}"
)


def _active_v092_tension_model(model: Any) -> bool:
    graph = getattr(model, "graph", {})
    graph_id = str(graph.get("graph_id") or "") if isinstance(graph, Mapping) else ""
    if GRAPH_SUFFIX not in graph_id:
        return False
    nodes = getattr(model, "nodes", {})
    node = nodes.get(TENSION_NODE_ID) if isinstance(nodes, Mapping) else None
    spec = node.get("calculation_spec") if isinstance(node, Mapping) else None
    return isinstance(spec, Mapping) and spec.get("algorithm_id") == TENSION_ALGORITHM_ID


def _runtime_trace(block: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for row in block.get("outputs") or []:
        if not isinstance(row, Mapping) or row.get("quantity_id") != TENSION_TRACE_QID:
            continue
        value = row.get("raw_value")
        return value if isinstance(value, Mapping) else None
    return None


def _validate_trace(trace: Mapping[str, Any], block: Mapping[str, Any]) -> None:
    if trace.get("schema") != TENSION_TRACE_SCHEMA:
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 typed trace schema mismatch")
    if trace.get("formula_id") != TENSION_FORMULA_ID:
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 final formula id is absent")
    inputs = trace.get("inputs")
    gamma_ct = inputs.get("gamma_ct") if isinstance(inputs, Mapping) else None
    gamma_ct_value = gamma_ct.get("value") if isinstance(gamma_ct, Mapping) else None
    if not isinstance(gamma_ct_value, (int, float)) or isinstance(gamma_ct_value, bool):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 gamma_ct evidence is missing")
    if not math.isclose(float(gamma_ct_value), float(GAMMA_CT), rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 gamma_ct evidence is not 1.1")

    result = trace.get("result")
    trace_value = result.get("value") if isinstance(result, Mapping) else None
    output_values = [
        row.get("raw_value")
        for row in block.get("outputs") or []
        if isinstance(row, Mapping) and row.get("quantity_id") == "gamma_T_9_1"
    ]
    if len(output_values) != 1 or not isinstance(trace_value, (int, float)):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 result evidence is incomplete")
    actual = output_values[0]
    if not isinstance(actual, (int, float)) or isinstance(actual, bool):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 execution result is non-numeric")
    if not math.isclose(float(actual), float(trace_value), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 trace/result mismatch")


def _rehash(report: dict[str, Any]) -> None:
    report.pop("report_sha256", None)
    canonical = json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()


def build_report_ir_v092(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    """Build REPORT-IR5 and reconcile active final-SP554 §9.1 presentation."""
    report = copy.deepcopy(build_report_ir5(model, session_or_snapshot))
    if not _active_v092_tension_model(model):
        return report

    remediated_blocks = 0
    for block in report.get("blocks") or []:
        if not isinstance(block, dict) or block.get("owner_node_id") != TENSION_NODE_ID:
            continue
        trace = _runtime_trace(block)
        if trace is None:
            raise ValueError(
                "v0.92 REPORT-IR fail-closed: completed SP554_C_9_1 has no typed runtime trace"
            )
        _validate_trace(trace, block)

        presentation = block.get("presentation")
        presentation = dict(presentation) if isinstance(presentation, Mapping) else {}
        presentation.update(
            {
                "section_key": "critical_temperature_strength",
                "kind": "FORMULA",
                "title_ru": "Температурный коэффициент при центральном растяжении",
                "formula_latex": TENSION_FORMULA_LATEX,
                "substitution_template_latex": TENSION_SUBSTITUTION_TEMPLATE_LATEX,
                "display_precision": 3,
                "runtime_trace_quantity_id": TENSION_TRACE_QID,
                "presentation_source": "active_v092_typed_runtime_trace_contract",
            }
        )
        block["presentation"] = presentation
        remediated_blocks += 1

    audit = report.get("audit")
    audit = dict(audit) if isinstance(audit, Mapping) else {}
    audit.update(
        {
            "v092_report_contract": REPORT_V092_CONTRACT,
            "v092_sp554_9_1_active": True,
            "v092_sp554_9_1_remediated_block_count": remediated_blocks,
            "v092_sp554_9_1_formula_source": "active_runtime_contract_plus_typed_execution_trace",
            "v092_sp554_9_1_frozen_sidecar_formula_superseded": True,
            "v092_sp554_9_1_engineering_values_recomputed_by_report": False,
        }
    )
    report["audit"] = audit
    _rehash(report)
    return report


__all__ = [
    "REPORT_V092_CONTRACT",
    "TENSION_SUBSTITUTION_TEMPLATE_LATEX",
    "build_report_ir_v092",
]
