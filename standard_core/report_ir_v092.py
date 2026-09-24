"""v0.92 REPORT-IR remediation for final SP554 §9.1 and progressive visibility.

The frozen v0.3.70 DAG and its v0.3.72 report sidecar intentionally preserve
the pre-final-publication §9.1 expression.  The active v0.92 guided overlay,
however, executes the final equation with mandatory ``gamma_ct=1.1`` and emits
a typed calculation-evidence object.

This module is a report-only reconciliation layer over REPORT-IR5.  It does not
calculate engineering quantities.  It enforces three active-v0.92 contracts:

* executed ``SP554_C_9_1`` blocks must carry the final typed runtime trace and
  are presented with the final gamma_ct equation;
* the main progressive report contains completed trace evidence plus at most
  one current ``PENDING_CURRENT`` node that is actually awaiting user input;
* section-property quantities that actually occur in completed trace evidence
  receive engineering Russian labels, canonical z/y symbols and typographic
  display units.  No unused property is injected into the report.

Future, N/A and deferred graph nodes are not projected into report blocks.  A
completed v0.92 §9.1 block without the typed evidence fails closed rather than
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
from .report_ir import _kind_for_node, _section_for_node, _title_for_node
from .report_ir5 import _rebuild_sections, build_report_ir5
from .report_metadata import report_spec_for_node

REPORT_V092_CONTRACT = "v092_progressive_report_and_sp554_9_1_runtime_trace_reconciled"
PENDING_CURRENT_STATE = "PENDING_CURRENT"
TENSION_SUBSTITUTION_TEMPLATE_LATEX = (
    r"\gamma_T=\frac{|{N_force}|}"
    r"{{A_net}\cdot {fy_norm}\cdot 1.1\cdot {gamma_c_tension}}"
)

# Presentation-only semantic labels.  Internal quantity IDs remain unchanged in
# REPORT-IR/Audit.  Historical x/y geometry IDs are handled separately below
# and are mapped to z/y only when explicit ``major_axis_is_x`` trace evidence is
# available.
_SECTION_PROPERTY_LABELS: dict[str, tuple[str, str]] = {
    "A_gross": ("Площадь поперечного сечения", "A"),
    "A_net": ("Площадь сечения нетто", "A_n"),
    "sp16_i_z": ("Радиус инерции относительно сильной главной оси z-z", "i_z"),
    "sp16_i_y": ("Радиус инерции относительно слабой главной оси y-y", "i_y"),
    "I_shear_gross": ("Момент инерции, используемый при расчёте касательных напряжений", "I_Q"),
    "S_shear_gross": ("Статический момент площади для расчёта касательных напряжений", "S"),
    "W_pl_min_gross": ("Минимальный пластический момент сопротивления", "W_{pl,min}"),
    "I_omega_gross": ("Секториальный момент инерции", "I_\omega"),
    "W_omega_gross": ("Секториальный момент сопротивления", "W_\omega"),
    "t_w": ("Толщина стенки", "t_w"),
    "sec_tw": ("Толщина стенки", "t_w"),
    "sec_h": ("Высота сечения", "h"),
    "sec_b": ("Ширина сечения / полки", "b"),
    "t_f": ("Толщина полки", "t_f"),
}

_PRETTY_UNITS = {
    "mm": "мм",
    "mm2": "мм²",
    "mm^2": "мм²",
    "mm3": "мм³",
    "mm^3": "мм³",
    "mm4": "мм⁴",
    "mm^4": "мм⁴",
    "mm6": "мм⁶",
    "mm^6": "мм⁶",
    "m": "м",
    "m2": "м²",
    "m^2": "м²",
    "N": "Н",
    "N/mm2": "Н/мм²",
    "N/mm^2": "Н/мм²",
    "MPa": "МПа",
    "kg/m": "кг/м",
    "1": "",
}


def _source_state(session_or_snapshot: Any) -> dict[str, Any]:
    if isinstance(session_or_snapshot, Mapping):
        return copy.deepcopy(dict(session_or_snapshot))
    snapshot = getattr(session_or_snapshot, "snapshot", None)
    if not callable(snapshot):
        raise TypeError("report source must be a session with snapshot() or a snapshot mapping")
    value = snapshot()
    if not isinstance(value, Mapping):
        raise TypeError("session.snapshot() must return a mapping")
    return copy.deepcopy(dict(value))


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
    if (
        len(output_values) != 1
        or not isinstance(trace_value, (int, float))
        or isinstance(trace_value, bool)
    ):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 result evidence is incomplete")
    actual = output_values[0]
    if not isinstance(actual, (int, float)) or isinstance(actual, bool):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 execution result is non-numeric")
    if not math.isclose(float(actual), float(trace_value), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("v0.92 REPORT-IR: SP554 §9.1 trace/result mismatch")


def _explicit_major_axis_evidence(report: Mapping[str, Any]) -> bool | None:
    values: set[bool] = set()
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        for collection in (block.get("inputs") or [], block.get("outputs") or []):
            for row in collection:
                if not isinstance(row, Mapping) or row.get("quantity_id") != "major_axis_is_x":
                    continue
                value = row.get("raw_value")
                if isinstance(value, bool):
                    values.add(value)
    if len(values) > 1:
        raise ValueError("v0.92 REPORT-IR: contradictory major_axis_is_x execution evidence")
    return next(iter(values)) if values else None


def _legacy_axis_label(qid: str, major_axis_is_x: bool | None) -> tuple[str, str] | None:
    """Map retained geometry IDs to z/y only with explicit runtime axis evidence."""
    if major_axis_is_x is None:
        return None
    source_to_active = (
        {"x": ("z", "сильной"), "y": ("y", "слабой")}
        if major_axis_is_x
        else {"x": ("y", "слабой"), "y": ("z", "сильной")}
    )
    table = {
        "J_x": ("x", "I", "Момент инерции"),
        "J_y": ("y", "I", "Момент инерции"),
        "W_el_x_pos": ("x", "W", "Упругий момент сопротивления", "+"),
        "W_el_x_neg": ("x", "W", "Упругий момент сопротивления", "-"),
        "W_el_y_pos": ("y", "W", "Упругий момент сопротивления", "+"),
        "W_el_y_neg": ("y", "W", "Упругий момент сопротивления", "-"),
        "W_pl_x": ("x", "W_{pl}", "Пластический момент сопротивления"),
        "W_pl_y": ("y", "W_{pl}", "Пластический момент сопротивления"),
    }
    spec = table.get(qid)
    if spec is None:
        return None
    source_axis, base_symbol, name = spec[:3]
    active_axis, qualifier = source_to_active[source_axis]
    side = spec[3] if len(spec) > 3 else None
    if base_symbol == "W":
        symbol = f"W_{{{active_axis},{side}}}" if side else f"W_{active_axis}"
    elif base_symbol == "W_{pl}":
        symbol = f"W_{{pl,{active_axis}}}"
    else:
        symbol = f"{base_symbol}_{active_axis}"
    suffix = f", сторона {side}" if side else ""
    return (
        f"{name} относительно {qualifier} главной оси {active_axis}-{active_axis}{suffix}",
        symbol,
    )


def _pretty_display_value(row: Mapping[str, Any]) -> str | None:
    value = row.get("raw_value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    unit = row.get("canonical_unit")
    pretty_unit = _PRETTY_UNITS.get(str(unit), str(unit or ""))
    text = format(number, ".12g")
    return f"{text} {pretty_unit}".strip()


def _humanize_executed_section_properties(report: dict[str, Any]) -> int:
    """Rename only section-property rows that already exist in completed trace blocks."""
    major_axis_is_x = _explicit_major_axis_evidence(report)
    changed = 0
    for block in report.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        for key in ("inputs", "outputs"):
            rows = block.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                qid = str(row.get("quantity_id") or "")
                label = _SECTION_PROPERTY_LABELS.get(qid)
                if label is None:
                    label = _legacy_axis_label(qid, major_axis_is_x)
                if label is None:
                    continue
                row["name_ru"], row["symbol"] = label
                display = _pretty_display_value(row)
                if display is not None:
                    row["display_value"] = display
                row["presentation_semantics"] = "active_v092_engineering_label"
                row["technical_quantity_id_visible_in_main_report"] = False
                changed += 1
    return changed


def _pending_current_block(model: Any, state: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any] | None:
    """Project only the actually entered current input node; never future DAG nodes."""
    if str(state.get("status") or "") != "AWAITING_INPUT":
        return None
    node_id = state.get("current_node_id")
    nodes = getattr(model, "nodes", {})
    if not isinstance(node_id, str) or not isinstance(nodes, Mapping) or node_id not in nodes:
        return None

    # A current fail-closed diagnostic is already represented by branch_failures;
    # do not duplicate it as a benign pending input.
    for failure in state.get("branch_failures") or []:
        if isinstance(failure, Mapping) and failure.get("node_id") == node_id:
            return None

    node = nodes[node_id]
    spec = report_spec_for_node(model, node_id, node)
    sequence = max(
        (int(row.get("sequence") or 0) for row in report.get("blocks") or [] if isinstance(row, Mapping)),
        default=0,
    ) + 1
    title = spec.get("title_ru") or spec.get("title") or _title_for_node(node)
    section_key = spec.get("section_key") or _section_for_node(node)
    kind = spec.get("kind") or _kind_for_node(node)

    # Presentation deliberately excludes formula/substitution metadata.  The
    # formula becomes visible only after a COMPLETE execution trace exists.
    presentation = {
        "visibility": "current_pending_only",
        "progress_state": PENDING_CURRENT_STATE,
    }
    return {
        "schema": "fire_report_block_v1",
        "report_block_id": f"PENDING:{node_id}",
        "owner_node_id": node_id,
        "owner_standard_id": node.get("owner_standard_id"),
        "sequence": sequence,
        "event_kind": "pending_current_node",
        "kind": str(kind),
        "section_key": str(section_key),
        "title": str(title),
        "normative_refs": copy.deepcopy(node.get("normative_refs") or []),
        "inputs": [],
        "outputs": [],
        "selected_edge_id": None,
        "execution_spec": {"mode": "not_executed_current_node"},
        "execution_evidence": {
            "evidence_mode": "current_node_state_only",
            "report_recomputed_result": False,
        },
        "presentation": presentation,
        "message": "Текущий шаг ожидает ввода данных; расчёт ещё не выполнен.",
        "progress_state": PENDING_CURRENT_STATE,
    }


def _append_progressive_pending(model: Any, state: Mapping[str, Any], report: dict[str, Any]) -> int:
    pending = _pending_current_block(model, state, report)
    if pending is None:
        return 0
    report.setdefault("blocks", []).append(pending)
    report["blocks"].sort(
        key=lambda row: (int(row.get("sequence") or 0), str(row.get("report_block_id") or ""))
    )
    report["block_count"] = len(report["blocks"])
    report["sections"] = _rebuild_sections(
        [row for row in report["blocks"] if isinstance(row, Mapping)]
    )
    return 1


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
    """Build active-v0.92 progressive REPORT-IR without recomputing engineering values."""
    state = _source_state(session_or_snapshot)
    report = copy.deepcopy(build_report_ir5(model, state))
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

    humanized_section_property_rows = _humanize_executed_section_properties(report)
    pending_count = _append_progressive_pending(model, state, report)

    audit = report.get("audit")
    audit = dict(audit) if isinstance(audit, Mapping) else {}
    audit.update(
        {
            "v092_report_contract": REPORT_V092_CONTRACT,
            "v092_progressive_visibility": True,
            "v092_future_dag_nodes_projected_to_main_report": False,
            "v092_pending_current_block_count": pending_count,
            "v092_pending_formula_visible_before_execution": False,
            "v092_section_properties_humanized_from_completed_trace_only": True,
            "v092_section_property_humanized_row_count": humanized_section_property_rows,
            "v092_section_axis_mapping_requires_runtime_evidence": True,
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
    "PENDING_CURRENT_STATE",
    "REPORT_V092_CONTRACT",
    "TENSION_SUBSTITUTION_TEMPLATE_LATEX",
    "build_report_ir_v092",
]
