from __future__ import annotations

from standard_core import fire_sp554_runtime as runtime
from streamlit_expertise_report_v091 import _v091_axis_block


def _report_with_raw_result(result):
    return {
        "blocks": [{
            "report_block_id": "v091#mechanics",
            "title": "SP554 §9.2",
            "kind": "RESULT",
            "inputs": [],
            "outputs": [{
                "quantity_id": "fire_mechanical_result",
                "raw_value": result,
                "name_ru": "Результат механического расчёта при пожаре",
                "symbol": None,
                "canonical_unit": None,
            }],
            "human_readable": {},
            "normative_refs": [],
            "presentation": {},
        }],
        "summary": {"checks": []},
    }


def _mechanical_result():
    lambda_z = 35.28
    lambda_y = 119.39
    return runtime.sp554_fire_mechanical_guided_workflow({
        "member_route": "central_compression",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": 255.0,
        "route": {
            "N_n": 400_000.0,
            "A_gross_mm2": 5282.0,
            "gamma_c": 0.9,
            "sp16_lambda_z_geom": lambda_z,
            "sp16_lambda_y_geom": lambda_y,
            "sp16_l_eff_z": 3000.0,
            "sp16_l_eff_y": 6000.0,
            "sp16_i_z": 3000.0 / lambda_z,
            "sp16_i_y": 6000.0 / lambda_y,
            "sp16_curve_z": "b",
            "sp16_curve_y": "c",
        },
    })


def test_v091_report_exposes_governing_axes_and_numeric_fire_slenderness_substitution():
    result = _mechanical_result()
    block = _v091_axis_block(_report_with_raw_result(result))

    assert "ось y (слабая)" in block
    assert "по прочности / коэффициенту $φ$" in block
    assert "по устойчивости / коэффициенту $γ_E$" in block
    assert "$E=206000" in block
    assert "пользовательское `E_norm` не используется" in block
    assert "\\bar{λ}_{y}=λ_{y}\\sqrt{R_{yn}/E}" in block
    assert "119.39" in block
    assert "255" in block
    assert "206000" in block
    assert "$φ_{y}=φ(" in block
    assert "$γ_{E,y}" in block
