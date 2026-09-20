from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from standard_core.fire_sp554_runtime import sp554_fire_mechanical_guided_workflow
from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

ROOT = Path(__file__).resolve().parents[1]


def _base(route_name: str, route: dict) -> dict:
    return {
        "member_route": route_name,
        "steel_strength_group": "ordinary",
        "high_strength_gost9651_qualified": False,
        "fire_resistant_gost9651_qualified": False,
        "fy_norm_n_mm2": 240.0,
        "E_norm_n_mm2": 206000.0,
        "route": route,
    }


def test_fire_d2_schema_is_strict_and_example_validates():
    schema = json.loads((ROOT / "schemas/sp554_fire_mechanical_guided_case.schema.json").read_text(encoding="utf-8"))
    case = json.loads((ROOT / "examples/fire_d2_sp554_critical_temperature_case.json").read_text(encoding="utf-8"))
    assert validate_case(case, schema) == []
    case["hidden_default"] = True
    assert any("Unexpected property" in error for error in validate_case(case, schema))


def test_fire_d2_compression_inverts_gamma_t_and_gamma_e_separately_and_uses_min_temperature():
    case = _base(
        "central_compression",
        {
            "N_n": 1_000_000.0,
            "A_gross_mm2": 10_000.0,
            "gamma_c": 1.0,
            "lambda_bar": 1.5,
            "buckling_curve_type": "b",
            "phi_sp16_formula8": 0.8,
            "mu_length_sp16": 1.0,
            "member_length_mm": 3000.0,
            "J_min_mm4": 6_324_000.0,
        },
    )
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["status"] == "COMPLETE"
    assert result["gamma_T_required"] == pytest.approx(0.5208333333333334)
    assert result["gamma_E_required"] == pytest.approx(0.6999768586775605)
    assert result["strength_curve_inversion"]["temperature_c"] == pytest.approx(560.6481481481482)
    assert result["modulus_curve_inversion"]["temperature_c"] == pytest.approx(525.0192844353662)
    assert result["critical_temperature_c"] == pytest.approx(525.0192844353662)
    assert result["critical_temperature_controlling_kind"] == "gamma_E"
    assert result["draft_literal_min_coefficient_policy_executed"] is False


def test_fire_d2_9_2_low_slenderness_ab_uses_phi_one():
    case = _base("central_compression", {
        "N_n": 240_000.0, "A_gross_mm2": 2000.0, "gamma_c": 1.0,
        "lambda_bar": 0.5, "buckling_curve_type": "a", "phi_sp16_formula8": 0.92,
        "mu_length_sp16": 1.0, "member_length_mm": 1000.0, "J_min_mm4": 1_000_000.0,
    })
    result = sp554_fire_mechanical_guided_workflow(case)
    detail = result["gamma_T_candidates"][0]["details"]
    assert detail["phi"] == 1.0
    assert detail["rule"] == "SP554_9_2_LOW_SLENDERNESS"


def test_fire_d2_9_2_high_slenderness_phi_cap_applies():
    lam = 5.0
    cap = 7.6 / lam**2
    case = _base("central_compression", {
        "N_n": 100_000.0, "A_gross_mm2": 5000.0, "gamma_c": 1.0,
        "lambda_bar": lam, "buckling_curve_type": "b", "phi_sp16_formula8": 0.5,
        "mu_length_sp16": 1.0, "member_length_mm": 1000.0, "J_min_mm4": 1_000_000.0,
    })
    result = sp554_fire_mechanical_guided_workflow(case)
    detail = result["gamma_T_candidates"][0]["details"]
    assert detail["phi"] == pytest.approx(cap)
    assert detail["phi_cap"] == pytest.approx(cap)


def test_fire_d2_central_tension_9_1():
    case = _base("central_tension", {"N_n": 240_000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_T_required"] == pytest.approx(0.5)
    assert result["gamma_T_governing_formula_ref"] == "9.1"
    assert result["gamma_E_required"] is None


def test_fire_d2_bending_governing_uses_max_required_gamma_not_draft_minimum():
    case = _base("bending", {"gamma_c": 1.0, "checks": {
        "eq_10_1": {"M_x_nmm": 120_000_000.0, "M_y_nmm": 0.0, "W_pl_min_eff_mm3": 1_000_000.0},
        "eq_10_2": {"alpha_h": 1.0, "Q_n": 20_000.0, "S_mm3": 50_000.0, "I_mm4": 20_000_000.0, "t_w_mm": 10.0},
    }})
    result = sp554_fire_mechanical_guided_workflow(case)
    values = {x["formula_ref"]: x["gamma_T_required"] for x in result["gamma_T_candidates"]}
    assert values["10.1"] == pytest.approx(0.5)
    assert values["10.2"] < values["10.1"]
    assert result["gamma_T_required"] == values["10.1"]
    assert result["gamma_T_governing_formula_ref"] == "10.1"


def test_fire_d2_eq_10_3_evaluates_section_points():
    case = _base("bending", {"gamma_c": 1.0, "checks": {"eq_10_3": {
        "M_x_nmm": 100_000_000.0, "M_y_nmm": 20_000_000.0, "B_nmm2": 0.0,
        "I_xn_mm4": 100_000_000.0, "I_yn_mm4": 50_000_000.0, "I_omega_n_mm6": 1e12,
        "section_points": [{"x_mm": 50.0, "y_mm": 100.0, "omega_mm2": 0.0}, {"x_mm": -50.0, "y_mm": -100.0, "omega_mm2": 0.0}],
    }}})
    result = sp554_fire_mechanical_guided_workflow(case)
    expected_stress = abs(100_000_000*100/100_000_000 + 20_000_000*50/50_000_000)
    assert result["gamma_T_required"] == pytest.approx(expected_stress / 240.0)


def test_fire_d2_eq_10_4_and_10_5_are_both_emitted():
    case = _base("bending", {"gamma_c": 1.0, "checks": {"eq_10_4_10_5": {
        "M_x_nmm": 50_000_000.0, "Q_n": 30_000.0, "alpha_h": 1.0,
        "S_mm3": 50_000.0, "I_shear_mm4": 20_000_000.0, "t_w_mm": 10.0,
        "I_xn_mm4": 100_000_000.0,
        "section_points": [{"y_mm": 100.0, "sigma_y_n_mm2": 0.0}, {"y_mm": 0.0, "sigma_y_n_mm2": 15.0}],
    }}})
    result = sp554_fire_mechanical_guided_workflow(case)
    refs = {row["formula_ref"] for row in result["gamma_T_candidates"]}
    assert refs == {"10.4", "10.5"}


def test_fire_d2_eq_10_6_ltb():
    case = _base("bending", {"gamma_c": 1.0, "checks": {"eq_10_6": {
        "M_x_nmm": 72_000_000.0, "phi_b_sp16": 0.75, "W_pl_x_eff_mm3": 1_000_000.0,
        "section_family": "i_section", "beam_is_bisteel": False, "sp16_section_class": "1"
    }}})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_T_required"] == pytest.approx(0.4)


def test_fire_d2_eq_10_7_signed_terms_are_explicit():
    case = _base("bending", {"gamma_c": 1.0, "checks": {"eq_10_7": {
        "M_x_nmm": 48_000_000.0, "M_y_nmm": 12_000_000.0, "B_nmm2": 2_400_000_000.0,
        "phi_b_sp16": 0.8, "W_pl_x_eff_mm3": 1_000_000.0, "W_pl_y_eff_mm3": 500_000.0,
        "W_omega_eff_mm4": 100_000_000.0, "M_y_term_sign": 1, "B_term_sign": -1,
        "section_family": "i_section", "beam_is_bisteel": False, "sp16_section_class": "1"
    }}})
    result = sp554_fire_mechanical_guided_workflow(case)
    expected = 48e6/(.8*1e6*240) + 12e6/(.5e6*240) - 2.4e9/(1e8*240)
    assert result["gamma_T_required"] == pytest.approx(expected)


def _nm(mode: str, **extra) -> dict:
    route = {
        "N_n": 400_000.0, "A_net_mm2": 5000.0, "A_gross_mm2": 5500.0,
        "gamma_c_strength": 1.0, "gamma_c_stability": 1.0,
        "M_x_nmm": 24_000_000.0, "M_y_nmm": 12_000_000.0, "B_nmm2": 0.0,
        "W_pl_x_eff_mm3": 600_000.0, "W_pl_y_eff_mm3": 300_000.0, "W_omega_eff_mm4": 1e8,
        "stability_mode": mode,
        "stress_state": "compression_plus_bending",
        "section_is_constant": True,
        "moment_plane_is_symmetry": True,
        "mef_gt_20": False,
        "section_is_box": False,
        "sp16_table21_type": "1",
        "major_axis_is_x": True,
    }
    if mode != "none":
        route.update({"mu_length_sp16": 1.0, "member_length_mm": 2500.0, "J_min_mm4": 4_000_000.0})
    route.update(extra)
    return _base("combined_nm", route)


def test_fire_d2_11_1_strength_route_for_tension_or_nm_without_stability():
    result = sp554_fire_mechanical_guided_workflow(_nm("none"))
    assert result["gamma_T_governing_formula_ref"] == "11.1"
    assert result["gamma_E_required"] is None


def test_fire_d2_11_2_in_plane_and_11_3_trace():
    result = sp554_fire_mechanical_guided_workflow(_nm("in_plane", phi_e_sp16=0.5, eta_sp16=1.2, M_for_11_3_nmm=24e6, W_pl_for_11_3_mm3=600000.0))
    refs = {r["formula_ref"] for r in result["gamma_T_candidates"]}
    assert {"11.1", "11.2"}.issubset(refs)
    assert result["route_trace"]["m_eff_11_3"] == pytest.approx(1.2*(24e6/400000)*5500/600000)


def test_fire_d2_11_4_out_of_plane():
    result = sp554_fire_mechanical_guided_workflow(_nm("out_of_plane_major", c_sp16=0.8, phi_y_sp16=0.7))
    refs = {r["formula_ref"] for r in result["gamma_T_candidates"]}
    assert "11.4" in refs


def test_fire_d2_11_5_minor_axis_additional_check_only_when_lambda_x_gt_lambda_y():
    result = sp554_fire_mechanical_guided_workflow(_nm("minor_axis", phi_e_sp16=0.55, lambda_bar_x=2.0, lambda_bar_y=1.0, phi_x_sp16=0.6))
    refs = {r["formula_ref"] for r in result["gamma_T_candidates"]}
    assert {"11.2", "11.5"}.issubset(refs)
    result2 = sp554_fire_mechanical_guided_workflow(_nm("minor_axis", phi_e_sp16=0.55, lambda_bar_x=0.8, lambda_bar_y=1.0))
    refs2 = {r["formula_ref"] for r in result2["gamma_T_candidates"]}
    assert "11.5" not in refs2


def test_fire_d2_11_6_11_7_biaxial_nonbox():
    result = sp554_fire_mechanical_guided_workflow(_nm("biaxial_nonbox", phi_ey_sp16=0.65, c_sp16=0.81))
    row = next(r for r in result["gamma_T_candidates"] if r["formula_ref"] == "11.6")
    expected_phi = 0.65*(0.6*0.81**(1/3)+0.4*0.81**0.25)
    assert row["details"]["phi_exy_11_7"] == pytest.approx(expected_phi)


def test_fire_d2_11_8_11_9_11_10_box():
    result = sp554_fire_mechanical_guided_workflow(_nm(
        "box", phi_ex_sp16=0.6, phi_ey_sp16=0.55, phi_y_sp16=0.58,
        lambda_bar_x=1.5, lambda_bar_y=0.8, major_axis_is_x=True,
    ))
    refs = {r["formula_ref"] for r in result["gamma_T_candidates"]}
    assert {"11.8", "11.9"}.issubset(refs)
    assert result["route_trace"]["delta_x_11_10"] > 1.0
    assert result["route_trace"]["delta_y_11_10"] == 1.0


def test_fire_d2_static_stress_8_7_without_compression():
    case = _base("static_stress_8_7", {"sigma_n_static_n_mm2": 120.0, "compression_stability_applicable": False})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_T_required"] == pytest.approx(0.5)
    assert result["gamma_T_governing_formula_ref"] == "8.7"


def test_fire_d2_static_stress_8_7_with_compression_adds_gamma_e():
    case = _base("static_stress_8_7", {
        "sigma_n_static_n_mm2": 120.0, "compression_stability_applicable": True,
        "N_n": 200000.0, "mu_length_sp16": 1.0, "member_length_mm": 2000.0, "J_min_mm4": 2e6,
    })
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_E_required"] is not None


def test_fire_d2_unqualified_high_strength_falls_back_to_increased_table_group():
    case = _base("central_tension", {"N_n": 240000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    case["steel_strength_group"] = "high"
    case["high_strength_gost9651_qualified"] = False
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["effective_steel_strength_group"] == "increased"
    assert result["qualification_notes"]


def test_fire_d2_qualified_high_strength_uses_high_curve():
    case = _base("central_tension", {"N_n": 240000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    case["steel_strength_group"] = "high"
    case["high_strength_gost9651_qualified"] = True
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["effective_steel_strength_group"] == "high"


def test_fire_d2_fire_resistant_group_fails_closed_without_required_qualification():
    case = _base("central_tension", {"N_n": 240000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    case["steel_strength_group"] = "fire_resistant"
    with pytest.raises(ValueError, match="GOST 9651"):
        sp554_fire_mechanical_guided_workflow(case)


def test_fire_d2_gamma_above_one_is_ambient_capacity_exceeded():
    case = _base("central_tension", {"N_n": 600000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_T_required"] > 1.0
    assert result["status"] == "AMBIENT_CAPACITY_EXCEEDED"
    assert result["critical_temperature_c"] == 20.0


def test_fire_d2_no_extrapolation_when_only_required_coefficient_is_below_published_curve():
    case = _base("central_tension", {"N_n": 24000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["gamma_T_required"] == pytest.approx(0.05)
    assert result["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert result["critical_temperature_c"] is None
    assert result["critical_temperature_lower_bound_c"] == 700.0


def test_fire_d2_eq_8_1_and_8_2_outputs_are_evaluated_at_critical_temperature():
    case = _base("central_tension", {"N_n": 240000.0, "A_net_mm2": 2000.0, "gamma_c": 1.0})
    result = sp554_fire_mechanical_guided_workflow(case)
    assert result["R_yt_critical_n_mm2"] == pytest.approx(case["fy_norm_n_mm2"] * result["gamma_T_table_at_critical_temperature"])
    assert result["E_t_critical_n_mm2"] == pytest.approx(case["E_norm_n_mm2"] * result["gamma_E_table_at_critical_temperature"])


def test_fire_d2_runner_materializes_critical_temperature_case():
    result = run_case(ROOT / "examples/fire_d2_sp554_critical_temperature_case.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["status"] == "COMPLETE"
    assert result["results"]["critical_temperature_c"] == pytest.approx(525.0192844353662)
    assert (ROOT / "outputs/sp554_fire_mechanical_guided_result.json").exists()
    assert (ROOT / "reports/sp554_fire_mechanical_guided_case_report.json").exists()
