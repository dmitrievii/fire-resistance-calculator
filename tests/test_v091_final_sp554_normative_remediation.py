import math

import pytest

from standard_core import fire_sp554_runtime as runtime
from standard_core.fire_sp554_runtime_v091 import (
    GAMMA_CT,
    SP16_STEEL_E_N_MM2,
    SP16_STEEL_E_NORMATIVE_BASIS,
    _phi_9_2_declarative_final,
)


def _compression_case():
    return {
        "member_route": "central_compression",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": 255.0,  # machine key retained; normative meaning is Ryn
        "route": _compression_route(),
    }


def _compression_route(**overrides):
    lambda_z = 35.28
    lambda_y = 119.39
    route = {
        "N_n": 400_000.0,
        "A_gross_mm2": 5282.0,
        "gamma_c": 0.9,
        # Qualified SP16 geometry/classification reused by SP554.
        "sp16_lambda_z_geom": lambda_z,
        "sp16_lambda_y_geom": lambda_y,
        "sp16_l_eff_z": 3000.0,
        "sp16_l_eff_y": 6000.0,
        "sp16_i_z": 3000.0 / lambda_z,
        "sp16_i_y": 6000.0 / lambda_y,
        "sp16_curve_z": "b",
        "sp16_curve_y": "c",
        # Deliberately stale/contradictory legacy values.  They must not govern.
        "lambda_bar": 0.01,
        "phi_sp16_formula8": 0.999,
        "mu_length_sp16": 7.0,
        "member_length_mm": 9999.0,
        "J_min_mm4": 1.0,
    }
    route.update(overrides)
    return route


def test_v091_fire_slenderness_uses_qualified_sp16_lambda_with_ryn_over_e():
    candidates, gamma_e, trace = runtime._central_compression(
        _compression_case(), _compression_route()
    )

    expected_z = 35.28 * math.sqrt(255.0 / 206000.0)
    expected_y = 119.39 * math.sqrt(255.0 / 206000.0)
    assert trace["axes"]["z"]["lambda_bar_fire"] == pytest.approx(expected_z)
    assert trace["axes"]["y"]["lambda_bar_fire"] == pytest.approx(expected_y)
    assert trace["axes"]["z"]["lambda_geom"] == pytest.approx(35.28)
    assert trace["axes"]["y"]["lambda_geom"] == pytest.approx(119.39)
    assert trace["governing_strength_axis"] == "y"
    assert trace["axes"]["y"]["phi_fire"] < trace["axes"]["z"]["phi_fire"]
    assert trace["E_n_mm2"] == pytest.approx(206000.0)
    assert trace["E_normative_basis"] == SP16_STEEL_E_NORMATIVE_BASIS
    assert SP16_STEEL_E_N_MM2 == pytest.approx(206000.0)

    # SP554 9.2 final publication: gamma_ct=1.1 is an explicit denominator.
    phi = trace["axes"][trace["governing_strength_axis"]]["phi_fire"]
    expected_gamma_t = 400_000.0 / (phi * 5282.0 * 255.0 * 1.1 * 0.9)
    assert candidates[0]["gamma_T_required"] == pytest.approx(expected_gamma_t)
    assert candidates[0]["details"]["gamma_ct"] == pytest.approx(1.1)
    assert GAMMA_CT == pytest.approx(1.1)

    # gamma_E is evaluated for both qualified axes; weak y-y governs this case.
    expected_gamma_e_y = (
        400_000.0
        * 6000.0**2
        / (math.pi**2 * 206000.0 * 5282.0 * (6000.0 / 119.39) ** 2)
    )
    assert trace["governing_stiffness_axis"] == "y"
    assert gamma_e == pytest.approx(expected_gamma_e_y)


def test_v091_does_not_rebuild_fire_state_from_legacy_raw_geometry_or_ambient_phi():
    first = runtime._central_compression(
        _compression_case(),
        _compression_route(
            lambda_bar=0.01,
            phi_sp16_formula8=0.999,
            mu_length_sp16=1.0,
            member_length_mm=3000.0,
            J_min_mm4=13_340_000.0,
        ),
    )
    second = runtime._central_compression(
        _compression_case(),
        _compression_route(
            lambda_bar=9.0,
            phi_sp16_formula8=0.02,
            mu_length_sp16=9.0,
            member_length_mm=12345.0,
            J_min_mm4=2.0,
        ),
    )
    assert first[0][0]["gamma_T_required"] == pytest.approx(second[0][0]["gamma_T_required"])
    assert first[1] == pytest.approx(second[1])
    assert first[2]["axes"] == second[2]["axes"]


def test_v091_steel_E_is_normative_constant_not_manual_or_legacy_input():
    baseline = runtime._central_compression(
        _compression_case(), _compression_route()
    )
    stale_case = dict(_compression_case(), E_norm_n_mm2=1.0)
    with_stale_input = runtime._central_compression(stale_case, _compression_route())

    assert baseline[0][0]["gamma_T_required"] == pytest.approx(
        with_stale_input[0][0]["gamma_T_required"]
    )
    assert baseline[1] == pytest.approx(with_stale_input[1])
    assert with_stale_input[2]["E_n_mm2"] == pytest.approx(206000.0)
    assert with_stale_input[2]["legacy_E_norm_n_mm2_ignored"] == pytest.approx(1.0)


def test_v091_full_fire_workflow_inverts_both_criteria_and_selects_earliest_temperature():
    result = runtime.sp554_fire_mechanical_guided_workflow(_compression_case())

    assert result["gamma_T_required"] > 0.0
    assert result["gamma_E_required"] > 0.0
    assert result["strength_curve_inversion"]["temperature_c"] is not None
    assert result["modulus_curve_inversion"]["temperature_c"] is not None

    t_strength = float(result["strength_curve_inversion"]["temperature_c"])
    t_stiffness = float(result["modulus_curve_inversion"]["temperature_c"])
    assert result["critical_temperature_c"] == pytest.approx(min(t_strength, t_stiffness))
    assert result["critical_temperature_controlling_kind"] == (
        "gamma_T" if t_strength <= t_stiffness else "gamma_E"
    )
    # Regression guard against the superseded v0.90 result.
    assert result["critical_temperature_c"] != pytest.approx(296.93268253, abs=1e-6)


def test_v091_guided_phi_executor_uses_two_qualified_axes_without_e_seed():
    values = {
        "sp16_lambda_z_geom": 35.28,
        "sp16_lambda_y_geom": 119.39,
        "sp16_curve_z": "b",
        "sp16_curve_y": "c",
        "fy_norm": 255.0,
        "lambda_bar": 0.01,
        "phi_sp16_formula8": 0.999,
    }
    first = _phi_9_2_declarative_final(values, {})
    second = _phi_9_2_declarative_final(
        dict(
            values,
            E_norm=1.0,  # stale/internal value must not override SP16 Table B.1
            lambda_bar=9.0,
            phi_sp16_formula8=0.02,
        ),
        {},
    )
    assert first == second
    assert 0.0 < first["phi_compression_sp554"] < 1.0


def test_v091_fail_closed_without_qualified_second_axis():
    route = _compression_route()
    del route["sp16_lambda_y_geom"]
    with pytest.raises(ValueError, match="sp16_lambda_y_geom"):
        runtime._central_compression(_compression_case(), route)


def test_v091_published_final_appendix_b1_rows_are_active():
    assert runtime._forward_b1("increased", "gamma_E", 450.0) == pytest.approx(0.81)
    assert runtime._forward_b1("increased", "gamma_E", 500.0) == pytest.approx(0.75)
    assert runtime._forward_b1("increased", "gamma_E", 550.0) == pytest.approx(0.71)
    assert runtime._forward_b1("high", "gamma_E", 300.0) == pytest.approx(0.89)


def test_v091_shared_sp16_phi_low_slenderness_rule_is_preserved():
    values = {
        "sp16_lambda_z_geom": 10.0,
        "sp16_lambda_y_geom": 10.0,
        "sp16_curve_z": "b",
        "sp16_curve_y": "b",
        "fy_norm": 255.0,
    }
    assert _phi_9_2_declarative_final(values, {})["phi_compression_sp554"] == pytest.approx(1.0)
