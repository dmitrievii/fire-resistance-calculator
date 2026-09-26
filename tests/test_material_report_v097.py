import math

import standard_core.material_report_v097 as material_report
from standard_core.material_report_v097 import TRACE_QID, augment_material_report_ir_v097, build_material_derivation_trace
from streamlit_material_report_v097 import _material_chapter_v097


def _preview(*_args, **_kwargs):
    return {
        "product_form": "parallel_flange_i",
        "product_form_label": "Двутавр с параллельными гранями полок",
        "source_table": "В.4",
        "source_sha256": "test-source",
        "source_row_index": 1,
        "steel_grade": "С255Б",
        "interval_key": "test-interval",
        "interval_label": "до 10 мм",
        "Ryn_MPa": 255.0,
        "Run_MPa": 380.0,
        "Ry_MPa": 250.0,
        "Ru_MPa": 370.0,
    }


def test_v097_trace_uses_shared_gamma_contract_and_keeps_raw_plus_rounded(monkeypatch):
    monkeypatch.setattr(material_report, "resolve_material_preview", _preview)
    trace = build_material_derivation_trace({
        "steel_product_form": "parallel_flange_i",
        "steel_grade": "С255Б",
        "steel_strength_interval_key": "test-interval",
        "material_safety_category": "statistical_control",
    })
    assert trace is not None
    assert trace["source_table"] == "В.4"
    assert trace["gamma_m"] == 1.025
    assert math.isclose(trace["Ry_unrounded_MPa"], 255.0 / 1.025, rel_tol=1e-12)
    assert math.isclose(trace["Ru_unrounded_MPa"], 380.0 / 1.025, rel_tol=1e-12)
    assert trace["Ry_rounded_MPa"] == 250.0
    assert trace["Ru_rounded_MPa"] == 370.0
    assert trace["annex_default_matches"] is True
    assert trace["mechanical_runtime_uses_rounded_annex_value"] is False


def test_v097_report_ir_publishes_material_trace(monkeypatch):
    monkeypatch.setattr(material_report, "resolve_material_preview", _preview)
    base = {"blocks": [], "audit": {}, "sections": [], "block_count": 0}
    report = augment_material_report_ir_v097(base, {
        "steel_product_form": "parallel_flange_i",
        "steel_grade": "С255Б",
        "steel_strength_interval_key": "test-interval",
        "material_safety_category": "statistical_control",
    })
    block = next(block for block in report["blocks"] if block["owner_node_id"] == "SP16_MATERIAL_STRENGTH_DERIVATION_V097")
    trace_row = next(row for row in block["outputs"] if row["quantity_id"] == TRACE_QID)
    assert trace_row["raw_value"]["gamma_m"] == 1.025
    assert report["audit"]["v097_material_derivation_trace"] is True
    assert report["audit"]["v097_mechanical_values_changed"] is False


def test_v097_material_chapter_is_formula_substitution_result_and_rounding():
    trace = {
        "schema": "sp16_material_strength_derivation_v097",
        "product_form": "parallel_flange_i",
        "product_form_label": "Двутавр с параллельными гранями полок",
        "source_table": "В.4",
        "steel_grade": "С255Б",
        "thickness_interval_label": "до 10 мм",
        "Ryn_MPa": 255.0,
        "Run_MPa": 380.0,
        "material_safety_category": "statistical_control",
        "gamma_m": 1.025,
        "Ry_unrounded_MPa": 255.0 / 1.025,
        "Ru_unrounded_MPa": 380.0 / 1.025,
        "Ry_rounded_MPa": 250.0,
        "Ru_rounded_MPa": 370.0,
        "Ry_tabulated_MPa": 250.0,
        "Ru_tabulated_MPa": 370.0,
        "annex_default_matches": True,
    }
    report = {
        "blocks": [{
            "progress_state": "COMPLETE",
            "inputs": [],
            "outputs": [{"quantity_id": TRACE_QID, "raw_value": trace}],
        }]
    }
    text = _material_chapter_v097(report)
    assert "## 2. Материал и расчётные характеристики" in text
    assert "\\gamma_m=1.025" in text
    assert "таблице 3" in text
    assert "$$ R_y=\\frac{R_{yn}}{\\gamma_m}=\\frac{255}{1.025}=" in text
    assert "$$ R_u=\\frac{R_{un}}{\\gamma_m}=\\frac{380}{1.025}=" in text
    assert "\n$$ R_y=\\frac{R_{yn}}{\\gamma_m} $$\n" not in text
    assert "\n$$ R_u=\\frac{R_{un}}{\\gamma_m} $$\n" not in text
    assert "250" in text
    assert "370" in text
    assert "округление до **5 Н/мм²**" in text
    assert "табл. В.4" in text
    assert "Контроль с опубликованной строкой" not in text
    assert "Report IR использует общий нормативный material helper" not in text


def test_v097_entrypoint_installed_after_v094():
    text = open("streamlit_app.py", encoding="utf-8").read()
    assert "from streamlit_material_report_v097 import install as _install_material_report_v097" in text
    assert text.index("_install_report_v094(_core)") < text.index("_install_material_report_v097(_core)")
