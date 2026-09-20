import json
import math
from pathlib import Path

import pytest

from standard_core import crane_runway_and_bending_stability as s
from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

from standard_core.release_metadata import RELEASE_STAGE

ROOT = Path(__file__).resolve().parents[1]


def test_equations_63_to_66_normal_zero_and_units():
    eq63 = s.crane_runway_equivalent_stress_utilization_eq63(0.87, 100, 10, 20, 30, 5, 355)
    expected = 0.87 / 355 * math.sqrt(110**2 - 110 * 20 + 20**2 + 3 * 35**2)
    assert eq63 == pytest.approx(expected)
    assert s.crane_runway_equivalent_stress_utilization_eq63(0.87, 0, 0, 0, 0, 0, 355) == 0
    assert s.crane_runway_longitudinal_normal_utilization_eq64(100, 20, 300) == 0.4
    assert s.crane_runway_transverse_normal_utilization_eq65(80, 20, 250) == 0.4
    assert s.crane_runway_shear_utilization_eq66(30, 10, 10, 100) == 0.5
    with pytest.raises(ValueError):
        s.crane_runway_shear_utilization_eq66(-1, 0, 0, 100)


def test_equations_67_and_68_components():
    mt = s.crane_runway_local_torsional_moment_eq68(1.1, 1.2, 100000, 20, 10000, 150)
    assert mt == 3_765_000
    components = s.crane_runway_stress_components_eq67(
        100_000_000, 1_000_000, 1.1, 1.2, 100_000, 200, 10,
        mt, 1000, 100_000_000, 800, 200_000,
    )
    assert components["sigma_x_n_mm2"] == 100
    assert components["sigma_local_y_n_mm2"] == 66
    assert components["sigma_local_x_n_mm2"] == 16.5
    assert components["sigma_f_y_n_mm2"] == pytest.approx(mt * 10 * 1000 / (0.75 * 100_000_000 * 800))
    assert components["tau_xy_n_mm2"] == 25
    assert components["tau_local_xy_n_mm2"] == pytest.approx(19.8)
    assert components["tau_f_xy_n_mm2"] == pytest.approx(0.25 * components["sigma_f_y_n_mm2"])
    zero = s.crane_runway_stress_components_eq67(0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0)
    assert all(value == 0 for value in zero.values())


def test_equations_69_and_70_sign_handling():
    assert s.lateral_torsional_stability_utilization_eq69(100_000_000, 0.8, 1_000_000, 250, 1) == 0.5
    combined = s.lateral_torsional_combined_utilization_eq70(
        100_000_000, 20_000_000, 1_000_000_000,
        0.8, 1_000_000, 500_000, 10_000_000_000, 250, 1,
    )
    expected = abs(0.5 + 20_000_000 / (500_000 * 250) + 1_000_000_000 / (10_000_000_000 * 250))
    assert combined == pytest.approx(expected)
    cancel = s.lateral_torsional_combined_utilization_eq70(
        100_000_000, -62_500_000, 0, 0.8, 1_000_000, 500_000, 1, 250, 1
    )
    assert cancel == 0


def test_table_11_equations_and_routing():
    b, t, h = 300.0, 20.0, 600.0
    eq71 = 0.35 + 0.0032 * 15 + (0.76 - 0.02 * 15) * 0.5
    eq72 = 0.57 + 0.0032 * 15 + (0.92 - 0.02 * 15) * 0.5
    eq73 = 0.41 + 0.0032 * 15 + (0.73 - 0.016 * 15) * 0.5
    assert s.table_11_limit_eq71(b, t, h) == pytest.approx(eq71)
    assert s.table_11_limit_eq72(b, t, h) == pytest.approx(eq72)
    assert s.table_11_limit_eq73(b, t, h) == pytest.approx(eq73)
    routed = s.table_11_limit("upper_flange", b, t, h, True, 355, 142)
    assert routed == pytest.approx(eq71 * 1.2 * math.sqrt(355 / 142))
    with pytest.raises(ValueError):
        s.table_11_limit_eq71(300, 5, 600)


def test_compressed_flange_relative_slenderness():
    expected = 5000 / 300 * math.sqrt(355 / 206000)
    assert s.compressed_flange_relative_slenderness(5000, 300, 355, 206000) == pytest.approx(expected)
    with pytest.raises(ValueError):
        s.compressed_flange_relative_slenderness(0, 300, 355, 206000)


def test_equations_74_to_77():
    assert s.compressed_flange_equivalent_force_eq74(2000, 3000, 355, 355) == 976250
    with pytest.raises(ValueError):
        s.compressed_flange_equivalent_force_eq74(2000, 3000, 300, 355)
    assert s.continuous_bracing_force_per_length_eq75(10000, 5000) == 6
    assert s.class_2_3_coefficient_eq77(250_000_000, 1_000_000, 250, 1, 0.8, 1.5) == pytest.approx(1.2)
    assert s.class_2_3_coefficient_eq77(0, 1_000_000, 250, 1, 0, 1.5) == 1
    assert s.class_2_3_stability_reduction_eq76(1.5, 2.0) == 0.7
    assert s.class_2_3_stability_reduction_eq76(1.0, 1.0) == 1


def test_effective_length_by_restraint_routes():
    assert s.effective_length_by_restraint(10000, [2500, 6000], False, False) == 4000
    assert s.effective_length_by_restraint(3000, [1000], True, False) == 3000
    assert s.effective_length_by_restraint(3000, [1000], True, True) == 2000
    with pytest.raises(ValueError):
        s.effective_length_by_restraint(3000, [2000, 1000], False, False)


def test_lateral_stability_exemption_routes():
    assert s.lateral_stability_check_exemption(True, 10, 1, 0)["exempt"] is True
    result = s.lateral_stability_check_exemption(False, 0.4, 0.5, 0.75)
    assert result == {"exempt": True, "route": "table_11", "slenderness_ok": True, "flange_width_ratio_ok": True}
    assert s.lateral_stability_check_exemption(False, 0.6, 0.5, 0.9)["exempt"] is False


def test_discrete_and_continuous_bracing_force_chain():
    result = s.discrete_bracing_fictitious_force(500000, 5000, 100, 206000, 355)
    assert result["geometric_slenderness"] == 50
    assert result["relative_slenderness"] == pytest.approx(50 * math.sqrt(355 / 206000))
    assert 0 < result["phi"] <= 1
    assert result["q_fictitious_n"] >= 0
    assert s.continuous_bracing_force_per_length_eq75(result["q_fictitious_n"], 6000) >= 0


def test_table_12_lookup_exact_nodes_and_bounds():
    assert s.table_12_c_cr_coefficient("welded", 0.5) == 30.0
    assert s.table_12_c_cr_coefficient("welded", 1.0) == 31.5
    assert s.table_12_c_cr_coefficient("welded", 30.0) == 35.5
    assert s.table_12_c_cr_coefficient("friction", 3.14159) == 35.2
    with pytest.raises(ValueError):
        s.table_12_c_cr_coefficient("welded", 3.0)


def test_table_13_lookup_and_infinity():
    assert s.table_13_beta("crane_rail_not_welded") == 2.0
    assert s.table_13_beta("other_case") == 0.8
    assert math.isinf(s.table_13_beta("crane_rail_welded"))
    with pytest.raises(ValueError):
        s.table_13_beta("unknown")


def test_annex_zh_equations_1_to_5():
    assert s.annex_zh_phi_b_eq_zh1(0.85) == 0.85
    assert s.annex_zh_phi_b_eq_zh2(1.0) == pytest.approx(0.89)
    assert s.annex_zh_phi_b_eq_zh2(10.0) == 1.0
    phi1 = s.annex_zh_phi1_eq_zh3(10, 1e8, 1e10, 500, 5000, 206000, 355)
    assert phi1 == pytest.approx(10 * 0.01 * 0.01 * 206000 / 355)
    assert s.annex_zh_alpha_rolled_eq_zh4(1e6, 1e8, 5000, 500, False) == 1.0
    assert s.annex_zh_alpha_rolled_eq_zh4(1e6, 1e8, 5000, 500, True) == 1.54
    base = 4 * (5000 * 20 / (500 * 300)) ** 2 * (1 + 0.5 * 500 * 10**3 / (300 * 20**3))
    assert s.annex_zh_alpha_built_up_eq_zh5(5000, 20, 500, 300, 10, False) == pytest.approx(base)
    assert s.annex_zh_alpha_built_up_eq_zh5(5000, 20, 500, 300, 10, True) == pytest.approx(2 * base)


def test_annex_zh_equations_6_to_9():
    common = (10, 1e8, 1e10, 500, 300, 5000, 206000, 355)
    phi1 = s.annex_zh_monosymmetric_phi1_eq_zh6(*common)
    expected = 10 * 0.01 * 2 * 500 * 300 / 5000**2 * 206000 / 355
    assert phi1 == pytest.approx(expected)
    phi2 = s.annex_zh_monosymmetric_phi2_eq_zh7(10, 1e8, 1e10, 500, 200, 5000, 206000, 355)
    assert phi2 == pytest.approx(expected * 2 / 3)
    assert s.annex_zh_flange_inertia_ratio_n_eq_zh8(3, 1) == 0.75
    assert s.annex_zh_psi_a_eq_zh9(2, 9, 0.5) == pytest.approx((2 + math.sqrt(13)) * 0.5)


def test_annex_zh_equations_10_to_13():
    n = 0.75
    beta = 0.1
    assert s.annex_zh_delta_eq_zh10(n, beta) == pytest.approx(n + 0.734 * beta)
    assert s.annex_zh_mu_eq_zh11(n, beta) == pytest.approx(n + 1.145 * beta)
    x = 0.6
    expected_beta = (2 * n - 1) * (0.47 - 0.035 * x * (1 + x - 0.072 * x**2))
    assert s.annex_zh_beta_eq_zh12(n, 300, 500) == pytest.approx(expected_beta)
    expected_eta = (1 - n) * (9.87 * n + 0.385 * 3 / 1 * (5000 / 500) ** 2)
    assert s.annex_zh_eta_eq_zh13(n, 3, 1, 5000, 500) == pytest.approx(expected_eta)


def test_annex_zh_table_1_transverse_and_moment_cases():
    a = 10.0
    compressed = s.annex_zh_table_1_psi("unbraced_point_midspan", a, "compressed")
    tension = s.annex_zh_table_1_psi("unbraced_point_midspan", a, "tension")
    assert tension > compressed
    assert s.annex_zh_table_1_psi("unbraced_pure_bending", a) == pytest.approx(math.sqrt(0.95 * a + 5.78))
    with pytest.raises(ValueError):
        s.annex_zh_table_1_psi("unbraced_point_midspan", a)


def test_annex_zh_table_1_braced_cases_and_boundaries():
    assert s.annex_zh_table_1_psi("two_or_more_braces", 40) == pytest.approx(2.25 + 0.07 * 40)
    assert s.annex_zh_table_1_psi("two_or_more_braces", 100) == pytest.approx(3.6 + 0.04 * 100 - 3.5e-5 * 100**2)
    base = s.annex_zh_table_1_psi("two_or_more_braces", 10)
    assert s.annex_zh_table_1_psi("one_mid_brace_point_midspan", 10) == pytest.approx(1.75 * base)
    assert s.annex_zh_table_1_psi("one_mid_brace_uniform", 10, "compressed") == pytest.approx(1.14 * base)


def test_annex_zh_table_2_cases():
    assert s.annex_zh_table_2_psi("point_load_at_tip", "tension", 20) == 4.2
    assert s.annex_zh_table_2_psi("point_load_at_tip", "tension", 40) == 6.0
    assert s.annex_zh_table_2_psi("point_load_at_tip", "compressed", 20) == pytest.approx(7.8)
    assert s.annex_zh_table_2_psi("uniformly_distributed", "tension", 25) == pytest.approx(7.1)
    with pytest.raises(ValueError):
        s.annex_zh_table_2_psi("uniformly_distributed", "compressed", 25)


def test_annex_zh_tables_3_to_5():
    assert s.annex_zh_table_3_phi_b("more_developed", 0.8, 0.7, 0.75) == 0.8
    p = s.annex_zh_table_3_phi_b("more_developed", 1.0, 1.0, 0.75)
    assert p == pytest.approx(0.89)
    assert s.annex_zh_table_3_phi_b("less_developed", 1.0, 1.0, 0.75) == pytest.approx(0.89)
    assert s.annex_zh_table_4_b("diagram_row_2", "point_midspan", 1.5, 2.0, 0.2) == 0.5
    assert s.annex_zh_table_4_b("diagram_row_3", "pure_bending", 1.5, 2.0, 0.2) == -0.2
    c, d = s.annex_zh_table_5_c_d("point_midspan", "i_section_n_le_0.9", eta=10)
    assert c == pytest.approx(3.3)
    assert d == 3.265
    c, d = s.annex_zh_table_5_c_d("pure_bending", "t_section_n_eq_1", alpha=100)
    assert c == pytest.approx(2.53)
    assert d == 4.315


def test_annex_zh_wrappers_and_modifiers():
    bundle = s.annex_zh_symmetric_i_phi_b(10, 1e8, 1e10, 500, 5000, 206000, 355)
    assert bundle["phi_1"] > 0
    assert 0 < bundle["phi_b"] <= 1
    assert s.annex_zh_channel_phi_b(1.0) == 0.7
    assert s.apply_less_developed_compressed_flange_modifier(1.0, 0.8, 1000, 100) == pytest.approx(0.875)
    assert s.apply_less_developed_compressed_flange_modifier(0.9, 0.7, 1000, 100) == 0.9
    with pytest.raises(ValueError):
        s.apply_less_developed_compressed_flange_modifier(1.0, 0.8, 2600, 100)


def test_v07_schema_and_example_validate():
    schema = json.loads((ROOT / "schemas/crane_runway_and_bending_stability_case.schema.json").read_text(encoding="utf-8"))
    case = json.loads((ROOT / "examples/crane_runway_and_bending_stability_example.json").read_text(encoding="utf-8"))
    assert validate_case(case, schema) == []


def test_v07_runner_writes_reports(tmp_path):
    source = ROOT / "examples/crane_runway_and_bending_stability_example.json"
    result = run_case(source, ROOT)
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_68_local_torsional_moment_n_mm"] > 0
    assert result["results"]["annex_zh_phi_bundle"]["phi_b"] > 0
    assert (ROOT / "outputs/crane_runway_and_bending_stability_result.json").exists()
    assert (ROOT / "reports/crane_runway_and_bending_stability_case_report.md").exists()


def test_annex_zh6_interpolation():
    assert s.annex_zh_interpolate_psi_a_for_n(0.9, 2.0, 4.0) == 2.0
    assert s.annex_zh_interpolate_psi_a_for_n(0.95, 2.0, 4.0) == pytest.approx(3.0)
    assert s.annex_zh_interpolate_psi_a_for_n(1.0, 2.0, 4.0) == pytest.approx(4.0)
    with pytest.raises(ValueError):
        s.annex_zh_interpolate_psi_a_for_n(0.89, 2.0, 4.0)


def test_annex_zh6_t_section_modifier():
    assert s.apply_t_section_low_alpha_modifier(5.0, 20.0, "point_midspan") == pytest.approx(4.4)
    assert s.apply_t_section_low_alpha_modifier(5.0, 20.0, "uniformly_distributed") == pytest.approx(4.4)
    assert s.apply_t_section_low_alpha_modifier(5.0, 20.0, "pure_bending") == 5.0
    assert s.apply_t_section_low_alpha_modifier(5.0, 40.0, "point_midspan") == 5.0
    with pytest.raises(ValueError):
        s.apply_t_section_low_alpha_modifier(5.0, 20.0, "unsupported")


def test_bimetal_crane_runway_route():
    value = s.bimetal_crane_runway_strength_utilization(
        1e8, 2e7, 1.2, 1.0, 1e6, 5e5, 300.0, 355.0, 1.0, True
    )
    expected = 1e8 / (1.2 * 1e6 * 300.0) + 2e7 / (1.15 * 5e5 * 355.0)
    assert value == pytest.approx(abs(expected))
    with pytest.raises(ValueError):
        s.bimetal_crane_runway_strength_utilization(1e8, 2e7, 1.2, 1.0, 1e6, 5e5, 200.0, 355.0, 1.0, True)


def test_crane_runway_stability_route():
    routed = s.crane_runway_lateral_torsional_stability_utilization(
        1e8, 2e7, 1e9, 0.8, 1e6, 5e5, 1e10, 355.0, 1.0
    )
    direct = s.lateral_torsional_combined_utilization_eq70(
        1e8, 2e7, 1e9, 0.8, 1e6, 5e5, 1e10, 355.0, 1.0
    )
    assert routed == direct
