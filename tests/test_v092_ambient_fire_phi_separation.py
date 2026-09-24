from __future__ import annotations

import math

import pytest

from standard_core import fire_sp554_runtime as fire_runtime
from standard_core.axial_members import (
    central_compression_stability_coefficient,
    relative_slenderness,
)
from standard_core.fire_sp554_runtime_v091 import GAMMA_CT, SP16_STEEL_E_N_MM2


def _fire_case(*, ryn: float = 255.0) -> dict:
    lambda_z = 35.28
    lambda_y = 119.39
    return {
        "member_route": "central_compression",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": ryn,
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
            # Contradictory ambient-only legacy evidence must never govern fire.
            "lambda_bar": 0.01,
            "phi_sp16_formula8": 0.999,
        },
    }


def test_ambient_sp16_phi_uses_Ry_while_fire_sp554_phi_uses_Ryn():
    """Finding #15: ambient and fire stability states are distinct by contract."""
    lambda_geom = 119.39
    curve = "c"
    ry_design = 240.0
    ryn = 255.0

    ambient_lambda_bar = relative_slenderness(
        lambda_geom,
        ry_design,
        SP16_STEEL_E_N_MM2,
    )
    ambient_phi = central_compression_stability_coefficient(ambient_lambda_bar, curve)

    result = fire_runtime.sp554_fire_mechanical_guided_workflow(_fire_case(ryn=ryn))
    trace = result["route_trace"]
    fire_axis = trace["axes"]["y"]

    expected_fire_lambda_bar = lambda_geom * math.sqrt(ryn / SP16_STEEL_E_N_MM2)
    expected_fire_phi = central_compression_stability_coefficient(expected_fire_lambda_bar, curve)

    assert ambient_lambda_bar == pytest.approx(lambda_geom * math.sqrt(ry_design / SP16_STEEL_E_N_MM2))
    assert fire_axis["lambda_bar_fire"] == pytest.approx(expected_fire_lambda_bar)
    assert fire_axis["phi_fire"] == pytest.approx(expected_fire_phi)
    assert fire_axis["lambda_bar_fire"] != pytest.approx(ambient_lambda_bar)
    assert fire_axis["phi_fire"] != pytest.approx(ambient_phi)
    assert trace["governing_strength_axis"] == "y"
    assert trace["gamma_ct"] == pytest.approx(GAMMA_CT)
    assert GAMMA_CT == pytest.approx(1.1)


def test_fire_result_is_invariant_to_contradictory_ambient_phi_and_lambda_bar():
    first = _fire_case()
    second = _fire_case()
    first["route"].update({"lambda_bar": 0.01, "phi_sp16_formula8": 0.999})
    second["route"].update({"lambda_bar": 9.0, "phi_sp16_formula8": 0.02})

    a = fire_runtime.sp554_fire_mechanical_guided_workflow(first)
    b = fire_runtime.sp554_fire_mechanical_guided_workflow(second)

    assert a["gamma_T_required"] == pytest.approx(b["gamma_T_required"])
    assert a["gamma_E_required"] == pytest.approx(b["gamma_E_required"])
    assert a["critical_temperature_c"] == pytest.approx(b["critical_temperature_c"])
    assert a["route_trace"]["axes"] == b["route_trace"]["axes"]


def test_gammaT_gammaE_are_inverted_independently_and_Tcr_is_the_minimum():
    result = fire_runtime.sp554_fire_mechanical_guided_workflow(_fire_case())

    t_gamma_t = result["strength_curve_inversion"]["temperature_c"]
    t_gamma_e = result["modulus_curve_inversion"]["temperature_c"]
    assert t_gamma_t is not None
    assert t_gamma_e is not None
    assert result["gamma_T_required"] > 0.0
    assert result["gamma_E_required"] > 0.0
    assert result["critical_temperature_c"] == pytest.approx(min(t_gamma_t, t_gamma_e))
    expected_kind = "gamma_T" if t_gamma_t <= t_gamma_e else "gamma_E"
    assert result["critical_temperature_controlling_kind"] == expected_kind


def test_fire_gammaT_uses_Ryn_phi_fire_gamma_ct_and_gamma_c_exactly():
    case = _fire_case()
    result = fire_runtime.sp554_fire_mechanical_guided_workflow(case)
    trace = result["route_trace"]
    axis = trace["governing_strength_axis"]
    phi_fire = trace["axes"][axis]["phi_fire"]

    expected = 400_000.0 / (phi_fire * 5282.0 * 255.0 * 1.1 * 0.9)
    assert result["gamma_T_required"] == pytest.approx(expected)
    assert trace["Ryn_n_mm2"] == pytest.approx(255.0)
    assert trace["gamma_ct"] == pytest.approx(1.1)
