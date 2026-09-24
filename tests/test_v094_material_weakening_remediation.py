from __future__ import annotations

import streamlit_expertise_report_v094_weakening as report94
import streamlit_report_v094_install as install94
import streamlit_weakening_single_card_v094 as ux94


def _row(qid, value):
    return {"quantity_id": qid, "raw_value": value}


def _report(*rows):
    return {"blocks": [{"owner_node_id": "FIRE_UI14_WEAKENING", "progress_state": "COMPLETE", "inputs": [], "outputs": list(rows)}]}


def test_circular_hole_trace_is_formula_substitution_result():
    rep = _report(
        _row("section_weakening_model", "circular_bolt_holes"),
        _row("section_weakening_trace", {
            "kind": "circular_bolt_holes",
            "A_gross_mm2": 5000.0,
            "hole_diameter_mm": 30.0,
            "web_thickness_mm": 10.0,
            "holes_count": 2,
            "area_reduction_mm2": 600.0,
            "A_net_mm2": 4400.0,
        }),
    )
    text = report94._weakening_section(rep)
    assert "\\Delta A=n_h d t_w" in text
    assert "\\Delta A=2\\cdot30\\cdot10=600" in text
    assert "A_n=A-\\Delta A" in text
    assert "A_n=5000-600=4400" in text


def test_no_weakening_is_explicit_and_has_no_fake_formula():
    text = report94._weakening_section(_report(_row("section_weakening_model", "no_weakening")))
    assert "Ослабления отсутствуют" in text
    assert "\\Delta A" not in text


def test_gamma_alias_uses_only_existing_gamma_row():
    rep = _report(_row("sp16_gamma_m_table3", 1.025))
    patched = report94._patch_gamma_aliases(rep)
    qids = [r["quantity_id"] for b in patched["blocks"] for r in b.get("outputs", [])]
    assert "gamma_m" in qids
    # No inference from resistance ratios is permitted.
    rep2 = _report(_row("fy_norm", 355.0), _row("Ry_formula", 345.0))
    patched2 = report94._patch_gamma_aliases(rep2)
    qids2 = [r["quantity_id"] for b in patched2["blocks"] for r in b.get("outputs", [])]
    assert "gamma_m" not in qids2


def test_duplicate_detector_only_accepts_boolean_hole_question():
    duplicate = {"title": "Круглые болтовые отверстия", "fields": [{"quantity_id": "has_holes", "data_type": "boolean"}]}
    detail = {"title": "Круглые болтовые отверстия", "fields": [{"quantity_id": "d", "data_type": "number"}]}
    assert ux94._is_redundant_hole_boolean(duplicate)
    assert not ux94._is_redundant_hole_boolean(detail)


def test_empty_thermal_passport_is_not_allowed_without_thermal_evidence():
    assert not install94._has_thermal_evidence(_report(_row("section_weakening_model", "no_weakening")))
    thermal = {"blocks": [{"owner_node_id": "SP554_THERMAL_PROTECTED", "progress_state": "COMPLETE", "outputs": []}]}
    assert install94._has_thermal_evidence(thermal)
