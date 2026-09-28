from __future__ import annotations

from types import SimpleNamespace

from standard_core.weakening_report_v098 import augment_weakening_report_ir_v098
import streamlit_weakening_v098 as weakening_ui
from streamlit_weakening_v098 import _normalized_weakening_section, _redundant_answer, _replace_weakening


def _base_values():
    return {
        "A_gross": 7577.0,
        "J_x": 80_000_000.0,
        "J_y": 8_000_000.0,
        "W_el_x_pos": 500_000.0,
        "W_el_x_neg": 500_000.0,
        "W_el_y_pos": 100_000.0,
        "W_el_y_neg": 100_000.0,
        "major_axis_is_x": True,
        "sp16_i_symmetry_class": "double_symmetric",
        "section_geometry_2d_normalized": {
            "template": "i_section",
            "h_mm": 300.0,
            "b_mm": 160.0,
            "tw_mm": 8.0,
            "tf_mm": 12.0,
        },
    }


def _empty_report():
    return {"blocks": [], "audit": {}, "sections": [], "block_count": 0}


def test_v098_reconciles_automatic_geometry_trace_and_explains_alpha_separately():
    values = _base_values()
    values["section_weakening_model"] = {
        "schema": "section_weakening_model_v0.92",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "automatic_geometry",
    }
    report = augment_weakening_report_ir_v098(_empty_report(), values)
    text = _normalized_weakening_section(report)

    assert "### 1.2 Ослабления поперечного сечения" in text
    assert "REPORT-EVIDENCE GAP" not in text
    assert r"\Delta A=20\cdot 8=160\;\mathrm{мм^2}" in text
    assert r"A_n=7 577-160=7 417\;\mathrm{мм^2}" in text
    assert "геометрическое уменьшение $A$, $I$ и $W$" in text
    assert r"\alpha_h=\frac{80}{80-20}=1.333" in text
    assert "не используется для определения площади нетто" in text
    assert "при сдвиге" in text


def test_v098_manual_net_report_lists_all_user_entered_required_properties():
    values = _base_values()
    values["section_weakening_model"] = {
        "schema": "section_weakening_model_v0.92",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "manual_net_properties",
        "manual_net_properties": {
            "I_z_n_mm4": 70_000_000.0,
            "I_y_n_mm4": 7_000_000.0,
            "W_z_n_mm3": 450_000.0,
            "W_y_n_mm3": 90_000.0,
            "W_pl_z_eff_mm3": 500_000.0,
            "W_pl_y_eff_mm3": 100_000.0,
            "I_omega_n_mm6": 12_000_000_000.0,
            "W_omega_eff_mm4": 60_000_000.0,
        },
    }
    report = augment_weakening_report_ir_v098(_empty_report(), values)
    text = _normalized_weakening_section(report)

    assert "#### Готовые характеристики нетто" in text
    assert "введено пользователем как характеристики нетто" in text
    for number in ("70 000 000", "7 000 000", "450 000", "90 000", "500 000", "100 000", "12 000 000 000", "60 000 000"):
        assert number in text
    assert r"A_n=7 577-160=7 417\;\mathrm{мм^2}" in text
    assert "Площадь $A_n$ не является ручным параметром" in text
    assert "не используется для определения площади нетто" in text


def test_v098_redundant_iw_question_is_derived_from_primary_weakening_model():
    assert _redundant_answer({"holes_present": True}) is True
    assert _redundant_answer({"holes_present": False}) is False
    assert _redundant_answer("circular_bolt_holes") is True
    assert _redundant_answer("no_weakening") is False
    assert _redundant_answer(None) is None


def test_v099_legacy_iw_card_never_falls_through_to_renderer(monkeypatch):
    calls = []

    class Service:
        def submit(self, *args, **kwargs):
            calls.append((args, kwargs))

    class Streamlit:
        def rerun(self):
            calls.append("rerun")

    def legacy_renderer(*args, **kwargs):
        raise AssertionError("legacy I/W card must never render")

    core = SimpleNamespace(_render_card_body=legacy_renderer, st=Streamlit())
    monkeypatch.setattr(weakening_ui, "_is_redundant_weakening_question", lambda card: True)
    weakening_ui.install(core)

    app = SimpleNamespace(service=Service())
    card = {"fields": [{"quantity_id": "legacy_iw"}], "submit_shape": "scalar"}

    # Critical regression: even when section_weakening_model is not yet
    # available, the compatibility card is suppressed instead of delegated.
    result = core._render_card_body(app, "sid", {"state": {"ledger": []}}, card, None, None, "current")
    assert result is None
    assert calls == []

    # Historical/edit presentation is suppressed as well.
    result = core._render_card_body(app, "sid", {"state": {"ledger": []}}, card, None, None, "history")
    assert result is None
    assert calls == []


def test_v099_legacy_iw_card_auto_resolves_when_primary_model_is_available(monkeypatch):
    calls = []

    class Service:
        def submit(self, *args, **kwargs):
            calls.append((args, kwargs))

    class Streamlit:
        def rerun(self):
            calls.append("rerun")

    core = SimpleNamespace(_render_card_body=lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not render")), st=Streamlit())
    monkeypatch.setattr(weakening_ui, "_is_redundant_weakening_question", lambda card: True)
    weakening_ui.install(core)

    env = {"state": {"ledger": [{"quantity_id": "section_weakening_model", "value": {"holes_present": True}}]}}
    card = {"fields": [{"quantity_id": "legacy_iw"}], "submit_shape": "scalar"}
    core._render_card_body(SimpleNamespace(service=Service()), "sid", env, card, None, None, "current")

    assert calls[0][0] == ("sid", True)
    assert calls[0][1]["provenance"]["source"] == "section_weakening_model"
    assert calls[1] == "rerun"


def test_v098_final_replace_removes_old_gap_and_old_weakening_section():
    values = _base_values()
    values["section_weakening_model"] = {
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "automatic_geometry",
    }
    report = augment_weakening_report_ir_v098(_empty_report(), values)
    old = """## 1. Геометрия

### 1.2 Ослабления поперечного сечения

**REPORT-EVIDENCE GAP:** old gap

## 2. Материал
"""
    text = _replace_weakening(old, report)
    assert "REPORT-EVIDENCE GAP" not in text
    assert text.count("### 1.2 Ослабления поперечного сечения") == 1
    assert "## 2. Материал" in text


def test_v098_is_installed_after_v097_and_retained_v095_layers():
    text = open("streamlit_app.py", encoding="utf-8").read()
    assert "from streamlit_weakening_v098 import install as _install_weakening_v098" in text
    assert text.index("_install_weakening_atomic_v095(_core)") < text.index("_install_weakening_v098(_core)")
    assert text.index("_install_material_report_v097(_core)") < text.index("_install_weakening_v098(_core)")
