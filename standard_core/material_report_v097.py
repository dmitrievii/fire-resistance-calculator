"""v0.97 canonical material derivation evidence for REPORT-IR.

This module closes the v0.96 reporting gap without changing mechanical design
values.  It resolves the same exact Annex-V material row used by the guided UI,
applies the shared Table-3 material-safety helper, and publishes a typed report
trace containing both the exact Table-2 quotient and the Annex-V rounded value.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping

from .fire_ui13_material_strength import resolve_material_preview
from .material_gamma_default_v096 import DEFAULT_CATEGORY, resolve_annex_v_design_strengths
from .report_ir5 import _rebuild_sections

TRACE_QID = "material_strength_derivation_v097"
TRACE_SCHEMA = "sp16_material_strength_derivation_v097"
BLOCK_ID = "V097:SP16_MATERIAL_STRENGTH_DERIVATION"
OWNER_NODE_ID = "SP16_MATERIAL_STRENGTH_DERIVATION_V097"


def _session_values(session_or_snapshot: Any) -> Mapping[str, Any]:
    plain = getattr(session_or_snapshot, "plain_values", None)
    if callable(plain):
        values = plain()
        return values if isinstance(values, Mapping) else {}
    if isinstance(session_or_snapshot, Mapping):
        # Direct values mapping is useful in tests and retained report tooling.
        if all(key in session_or_snapshot for key in ("steel_product_form", "steel_grade", "steel_strength_interval_key")):
            return session_or_snapshot
        values = session_or_snapshot.get("values")
        if isinstance(values, Mapping):
            return values
    return {}


def build_material_derivation_trace(values: Mapping[str, Any]) -> dict[str, Any] | None:
    product = values.get("steel_product_form")
    grade = values.get("steel_grade")
    interval = values.get("steel_strength_interval_key")
    if not all(isinstance(value, str) and value for value in (product, grade, interval)):
        return None

    preview = resolve_material_preview(str(product), str(grade), str(interval))
    category = values.get("material_safety_category")
    if not isinstance(category, str) or not category:
        category = DEFAULT_CATEGORY
    calc = resolve_annex_v_design_strengths(
        Ryn_MPa=float(preview["Ryn_MPa"]),
        Run_MPa=float(preview["Run_MPa"]),
        Ry_tabulated_MPa=preview.get("Ry_MPa"),
        Ru_tabulated_MPa=preview.get("Ru_MPa"),
        gamma_m_category=None if category == DEFAULT_CATEGORY else category,
    )
    return {
        "schema": TRACE_SCHEMA,
        "standard": "SP16_2017",
        "product_form": preview["product_form"],
        "product_form_label": preview["product_form_label"],
        "source_table": preview["source_table"],
        "source_sha256": preview["source_sha256"],
        "source_row_index": preview["source_row_index"],
        "steel_grade": preview["steel_grade"],
        "thickness_interval_key": preview["interval_key"],
        "thickness_interval_label": preview["interval_label"],
        "Ryn_MPa": float(preview["Ryn_MPa"]),
        "Run_MPa": float(preview["Run_MPa"]),
        "material_safety_category": calc["material_safety_category"],
        "gamma_m": float(calc["gamma_m"]),
        "gamma_m_basis": calc["gamma_m_basis"],
        "Ry_unrounded_MPa": float(calc["Ry_unrounded_MPa"]),
        "Ru_unrounded_MPa": float(calc["Ru_unrounded_MPa"]),
        "rounding_step_MPa": float(calc["rounding_step_MPa"]),
        "Ry_rounded_MPa": float(calc["Ry_formula_MPa"]),
        "Ru_rounded_MPa": float(calc["Ru_formula_MPa"]),
        "Ry_tabulated_MPa": preview.get("Ry_MPa"),
        "Ru_tabulated_MPa": preview.get("Ru_MPa"),
        "annex_default_matches": bool(calc["annex_default_matches"]),
        "formula_Ry": "Ry = Ryn / gamma_m",
        "formula_Ru": "Ru = Run / gamma_m",
        "rounding_basis": "СП 16, приложение В: расчетные сопротивления в таблицах округлены до 5 Н/мм2",
        "mechanical_runtime_uses_rounded_annex_value": False,
    }


def _row(qid: str, value: Any, unit: str | None = None) -> dict[str, Any]:
    display = str(value)
    if unit:
        display += f" {unit}"
    return {
        "quantity_id": qid,
        "symbol": qid,
        "name_ru": qid,
        "raw_value": copy.deepcopy(value),
        "canonical_unit": unit,
        "display_value": display,
    }


def augment_material_report_ir_v097(report: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    """Add one idempotent typed material-evidence block to an existing REPORT-IR."""
    trace = build_material_derivation_trace(values)
    if trace is None:
        return copy.deepcopy(dict(report))

    out = copy.deepcopy(dict(report))
    blocks = [
        block for block in (out.get("blocks") or [])
        if not (isinstance(block, Mapping) and block.get("report_block_id") == BLOCK_ID)
    ]
    sequence = max((int(block.get("sequence") or 0) for block in blocks if isinstance(block, Mapping)), default=0) + 1
    block = {
        "schema": "fire_report_block_v1",
        "report_block_id": BLOCK_ID,
        "owner_node_id": OWNER_NODE_ID,
        "owner_standard_id": "SP16_2017",
        "sequence": sequence,
        "event_kind": "active_report_reconciliation",
        "kind": "FORMULA",
        "section_key": "input_data",
        "title": "Коэффициент надежности по материалу и расчетные сопротивления",
        "normative_refs": [
            {"standard_id": "SP16_2017", "reference": "таблица 3"},
            {"standard_id": "SP16_2017", "reference": f"таблица {trace['source_table']}"},
        ],
        "inputs": [],
        "outputs": [
            _row(TRACE_QID, trace),
            _row("material_safety_category", trace["material_safety_category"]),
            _row("gamma_m", trace["gamma_m"]),
            _row("Ry_formula", trace["Ry_unrounded_MPa"], "MPa"),
            _row("Ru_formula", trace["Ru_unrounded_MPa"], "MPa"),
            _row("Ry_annex_rounded", trace["Ry_rounded_MPa"], "MPa"),
            _row("Ru_annex_rounded", trace["Ru_rounded_MPa"], "MPa"),
        ],
        "selected_edge_id": None,
        "execution_spec": {"mode": "canonical_report_derivation_from_material_selection"},
        "execution_evidence": {
            "evidence_mode": "shared_v096_normative_material_helper",
            "report_recomputed_mechanical_state": False,
            "mechanical_values_overridden": False,
        },
        "presentation": {"material_derivation_trace_quantity_id": TRACE_QID},
        "progress_state": "COMPLETE",
    }
    blocks.append(block)
    blocks.sort(key=lambda row: (int(row.get("sequence") or 0), str(row.get("report_block_id") or "")))
    out["blocks"] = blocks
    out["block_count"] = len(blocks)
    out["sections"] = _rebuild_sections([row for row in blocks if isinstance(row, Mapping)])
    audit = dict(out.get("audit") or {})
    audit.update({
        "v097_material_derivation_trace": True,
        "v097_material_derivation_source": "exact_annex_v_row_plus_shared_v096_table3_helper",
        "v097_mechanical_values_changed": False,
    })
    out["audit"] = audit
    out.pop("report_sha256", None)
    canonical = json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    out["report_sha256"] = sha256(canonical).hexdigest()
    return out


def augment_from_session(report: Mapping[str, Any], session_or_snapshot: Any) -> dict[str, Any]:
    return augment_material_report_ir_v097(report, _session_values(session_or_snapshot))


__all__ = [
    "TRACE_QID", "TRACE_SCHEMA", "build_material_derivation_trace",
    "augment_material_report_ir_v097", "augment_from_session",
]
