import math

import pytest

from standard_core import fire_sp554_runtime as runtime
from standard_core.fire_sp554_runtime_v091 import _phi_9_2_declarative_final


def _compression_case():
    return {"fy_norm_n_mm2": 250.0, "E_norm_n_mm2": 206000.0}


def _compression_route(**legacy):
    route = {
        "N_n": 1_000_000.0,
        "A_gross_mm2": 10_000.0,
        "gamma_c": 1.0,
        "buckling_curve_type": "b",
        "mu_length_sp16": 1.0,
        "member_length_mm": 3000.0,
        "J_min_mm4": 6_324_000.0,
        # Retained only for saved-case compatibility.  v0.91 must ignore them.
        "lambda_bar": 0.10,
        "phi_sp16_formula8": 0.99,
    }
    route.update(legacy)
    return route


def test_v091_sp554_9_2_rebuilds_fire_slenderness_from_geometry_ryn_and_e():
    candidates, gamma_e, trace = runtime._central_compression(_compression_case(), _compression_route())
    expected_lambda = 3000.0 / math.sqrt(6_324_000.0 / 10_000.0)
    expected_lambda_bar = expected_lambda * math.sqrt(250.0 / 206000.0)

    assert trace["lambda_geom"] == pytest.approx(expected_lambda)
    assert trace["lambda_bar_fire"] == pytest.approx(expected_lambda_bar)
    assert trace["phi"] == pytest.approx(0.4284032722542145)
    assert candidates[0]["gamma_T_required"] == pytest.approx(0.9336996841673048)
    assert gamma_e == pytest.approx(0.6999768586775605)


def test_v091_sp554_9_2_ignores_legacy_ambient_lambda_and_phi():
    first = runtime._central_compression(
        _compression_case(), _compression_route(lambda_bar=0.01, phi_sp16_formula8=0.999)
    )
    second = runtime._central_compression(
        _compression_case(), _compression_route(lambda_bar=8.0, phi_sp16_formula8=0.05)
    )
    assert first[0][0]["gamma_T_required"] == pytest.approx(second[0][0]["gamma_T_required"])
    assert first[2]["phi"] == pytest.approx(second[2]["phi"])
    assert first[2]["lambda_bar_fire"] == pytest.approx(second[2]["lambda_bar_fire"])


def test_v091_guided_phi_executor_uses_fire_lambda_bar_not_legacy_values():
    base_values = {
        "sp16_lambda_geom": 119.29584674762738,
        "fy_norm": 250.0,
        "E_norm": 206000.0,
        "sp16_buckling_curve_type": "b",
        "lambda_bar": 0.01,
        "phi_sp16_formula8": 0.999,
    }
    first = _phi_9_2_declarative_final(base_values, {})
    changed = dict(base_values, lambda_bar=9.0, phi_sp16_formula8=0.02)
    second = _phi_9_2_declarative_final(changed, {})
    assert first == pytest.approx({"phi_compression_sp554": 0.4284032722542145})
    assert second == pytest.approx(first)


def test_v091_published_final_appendix_b1_rows_are_active():
    assert runtime._forward_b1("increased", "gamma_E", 450.0) == pytest.approx(0.81)
    assert runtime._forward_b1("increased", "gamma_E", 500.0) == pytest.approx(0.75)
    assert runtime._forward_b1("increased", "gamma_E", 550.0) == pytest.approx(0.71)
    assert runtime._forward_b1("high", "gamma_E", 300.0) == pytest.approx(0.89)


def test_v091_true_low_slenderness_rule_still_returns_phi_one_for_curve_b():
    # lambda_bar_fire = lambda_geom*sqrt(250/206000) < 0.6
    values = {
        "sp16_lambda_geom": 10.0,
        "fy_norm": 250.0,
        "E_norm": 206000.0,
        "sp16_buckling_curve_type": "b",
    }
    assert _phi_9_2_declarative_final(values, {})["phi_compression_sp554"] == pytest.approx(1.0)
