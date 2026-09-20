import math
from pathlib import Path

import pytest

from standard_core import sheet_structures_strength_and_stability as sh


def test_table_34_catalog_exists_and_has_nine_nodes():
    data = sh.table_34_catalog()
    assert data["audit_id"] == "SP16-TBL-34"
    assert len(data["values"]) == 9


def test_table_34_lookup_value_consistency():
    assert sh.table_34_c_coefficient(100.0) == pytest.approx(0.22)
    assert sh.table_34_c_coefficient(2500.0) == pytest.approx(0.06)


def test_table_34_lookup_rejects_unstated_interpolation():
    with pytest.raises(ValueError):
        sh.table_34_c_coefficient(150.0)


def test_eq148_normal():
    value = sh.membrane_strength_utilization_eq148(100.0, 40.0, 20.0, 355.0, 1.0)
    expected = math.sqrt(100.0**2 - 100.0*40.0 + 40.0**2 + 3.0*20.0**2) / 355.0
    assert value == pytest.approx(expected)


def test_eq148_zero_boundary():
    assert sh.membrane_strength_utilization_eq148(0.0, 0.0, 0.0, 355.0, 1.0) == 0.0


def test_eq148_signed_stress_convention():
    assert sh.membrane_strength_utilization_eq148(-100.0, -40.0, -20.0, 355.0, 1.0) == pytest.approx(
        sh.membrane_strength_utilization_eq148(100.0, 40.0, 20.0, 355.0, 1.0)
    )


def test_eq149_normal():
    assert sh.meridional_stress_eq149(2.0 * math.pi * 1000.0 * 10.0, 1000.0, 10.0, 0.0) == pytest.approx(1.0)


def test_eq149_zero_force_boundary():
    assert sh.meridional_stress_eq149(0.0, 1000.0, 10.0, 30.0) == 0.0


def test_eq149_angle_domain():
    with pytest.raises(ValueError):
        sh.meridional_stress_eq149(1000.0, 1000.0, 10.0, 90.0)


def test_eq150_normal():
    assert sh.circumferential_stress_eq150(2.0, 10.0, 50.0, 1000.0, 500.0) == pytest.approx(75.0)


def test_eq150_zero_pressure_signed_result():
    assert sh.circumferential_stress_eq150(0.0, 10.0, 50.0, 1000.0, 500.0) == pytest.approx(-25.0)


def test_eq150_positive_radius_required():
    with pytest.raises(ValueError):
        sh.circumferential_stress_eq150(1.0, 10.0, 0.0, 0.0, 500.0)


def test_eq151_normal():
    assert sh.cylindrical_internal_pressure_stresses_eq151(1.0, 1000.0, 10.0) == pytest.approx((50.0, 100.0))


def test_eq151_zero_pressure_boundary():
    assert sh.cylindrical_internal_pressure_stresses_eq151(0.0, 1000.0, 10.0) == (0.0, 0.0)


def test_eq151_length_unit_consistency():
    assert sh.cylindrical_internal_pressure_stresses_eq151(1.0, 1.0, 0.01) == pytest.approx((50.0, 100.0))


def test_eq152_normal():
    assert sh.spherical_internal_pressure_stresses_eq152(1.0, 1000.0, 10.0) == pytest.approx((50.0, 50.0))


def test_eq152_zero_pressure_boundary():
    assert sh.spherical_internal_pressure_stresses_eq152(0.0, 1000.0, 10.0) == (0.0, 0.0)


def test_eq152_positive_thickness_required():
    with pytest.raises(ValueError):
        sh.spherical_internal_pressure_stresses_eq152(1.0, 1000.0, 0.0)


def test_eq153_normal():
    c = math.cos(math.radians(30.0))
    assert sh.conical_internal_pressure_stresses_eq153(1.0, 1000.0, 10.0, 30.0) == pytest.approx((50.0 / c, 100.0 / c))


def test_eq153_zero_pressure_boundary():
    assert sh.conical_internal_pressure_stresses_eq153(0.0, 1000.0, 10.0, 30.0) == (0.0, 0.0)


def test_eq153_angle_domain():
    with pytest.raises(ValueError):
        sh.conical_internal_pressure_stresses_eq153(1.0, 1000.0, 10.0, -1.0)


def test_eq154_normal():
    assert sh.cylindrical_axial_stability_utilization_eq154(100.0, 200.0, 0.9) == pytest.approx(100.0 / 180.0)


def test_eq154_zero_boundary():
    assert sh.cylindrical_axial_stability_utilization_eq154(0.0, 200.0, 1.0) == 0.0


def test_eq154_negative_compression_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_axial_stability_utilization_eq154(-1.0, 200.0, 1.0)


def test_eq155_normal():
    expected = 0.97 - (0.00025 + 0.95 * 355.0 / 206000.0) * 200.0
    assert sh.cylindrical_psi_eq155(200.0, 355.0, 206000.0) == pytest.approx(expected)


def test_eq155_boundary_300():
    assert sh.cylindrical_psi_eq155(300.0, 355.0, 206000.0) > 0.0


def test_eq155_above_domain_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_psi_eq155(300.0001, 355.0, 206000.0)


def test_eq156_normal():
    value = sh.tube_local_stability_utilization_eq156(100000.0, 1.0, 2000.0, 0.2, 355.0, 100.0, 1000.0, 20.0, 206000.0)
    scrb = 100.0 / 8.0 * (9.0 - (1.0 - 0.2) / (1.0 + 0.2))
    a = scrb + 1.2 * 355.0 * math.pi**2
    b = 4.0 * 355.0 * scrb * math.pi**2
    expected = 100000.0 * 2.0 / (2000.0 * (a - math.sqrt(a*a-b)))
    assert value == pytest.approx(expected)


def test_eq156_zero_force_boundary():
    assert sh.tube_local_stability_utilization_eq156(0.0, 1.0, 2000.0, 0.0, 355.0, 100.0, 1000.0, 20.0, 206000.0) == 0.0


def test_eq156_slenderness_domain():
    with pytest.raises(ValueError):
        sh.tube_local_stability_utilization_eq156(1000.0, 0.64, 2000.0, 0.0, 355.0, 100.0, 1000.0, 20.0, 206000.0)


def test_eq157_normal():
    assert sh.cylindrical_panel_limit_eq157(206000.0, 100.0) == pytest.approx(1.9 * math.sqrt(2060.0))


def test_eq157_zero_stress_boundary_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_panel_limit_eq157(206000.0, 0.0)


def test_eq157_unit_ratio_behavior():
    assert sh.cylindrical_panel_limit_eq157(206.0, 0.1) == pytest.approx(sh.cylindrical_panel_limit_eq157(206000.0, 100.0))


def test_eq158_normal():
    assert sh.cylindrical_panel_limit_eq158(355.0, 206000.0) == pytest.approx(37.0 / math.sqrt(1.0 + 500.0 * 355.0 / 206000.0))


def test_eq158_low_yield_boundary():
    assert sh.cylindrical_panel_limit_eq158(1e-6, 206000.0) == pytest.approx(37.0, rel=1e-8)


def test_eq158_positive_modulus_required():
    with pytest.raises(ValueError):
        sh.cylindrical_panel_limit_eq158(355.0, 0.0)


def test_eq159_normal():
    assert sh.cylindrical_external_pressure_utilization_eq159(20.0, 50.0, 0.8) == pytest.approx(0.5)


def test_eq159_zero_boundary():
    assert sh.cylindrical_external_pressure_utilization_eq159(0.0, 50.0, 1.0) == 0.0


def test_eq159_negative_demand_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_external_pressure_utilization_eq159(-1.0, 50.0, 1.0)


def test_eq160_normal():
    assert sh.cylindrical_external_pressure_critical_stress_eq160(206000.0, 1000.0, 5000.0, 10.0) == pytest.approx(0.55 * 206000.0 * 0.2 * 0.01**1.5)


def test_eq160_ratio_boundaries():
    assert sh.cylindrical_external_pressure_critical_stress_eq160(206000.0, 1000.0, 500.0, 10.0) > 0.0
    assert sh.cylindrical_external_pressure_critical_stress_eq160(206000.0, 1000.0, 10000.0, 10.0) > 0.0


def test_eq160_ratio_outside_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_external_pressure_critical_stress_eq160(206000.0, 1000.0, 10001.0, 10.0)


def test_eq161_normal():
    assert sh.cylindrical_external_pressure_critical_stress_eq161(206000.0, 1000.0, 10.0) == pytest.approx(0.17 * 206000.0 * 0.01**2)


def test_eq161_thickness_scaling():
    a = sh.cylindrical_external_pressure_critical_stress_eq161(206000.0, 1000.0, 10.0)
    b = sh.cylindrical_external_pressure_critical_stress_eq161(206000.0, 1000.0, 20.0)
    assert b == pytest.approx(4.0 * a)


def test_eq161_positive_radius_required():
    with pytest.raises(ValueError):
        sh.cylindrical_external_pressure_critical_stress_eq161(206000.0, 0.0, 10.0)


def test_eq162_normal():
    assert sh.cylindrical_combined_stability_utilization_eq162(20.0, 100.0, 30.0, 150.0, 0.8) == pytest.approx(0.5)


def test_eq162_zero_boundary():
    assert sh.cylindrical_combined_stability_utilization_eq162(0.0, 100.0, 0.0, 150.0, 1.0) == 0.0


def test_eq162_negative_demand_rejected():
    with pytest.raises(ValueError):
        sh.cylindrical_combined_stability_utilization_eq162(-1.0, 100.0, 0.0, 150.0, 1.0)


def test_eq163_normal():
    assert sh.conical_axial_stability_utilization_eq163(100000.0, 200000.0, 0.8) == pytest.approx(0.625)


def test_eq163_zero_boundary():
    assert sh.conical_axial_stability_utilization_eq163(0.0, 200000.0, 1.0) == 0.0


def test_eq163_negative_force_rejected():
    with pytest.raises(ValueError):
        sh.conical_axial_stability_utilization_eq163(-1.0, 200000.0, 1.0)


def test_eq164_normal():
    expected = 6.28 * 10.0 * 100.0 * 1000.0 * math.cos(math.radians(30.0))**2
    assert sh.conical_critical_force_eq164(10.0, 100.0, 1000.0, 30.0) == pytest.approx(expected)


def test_eq164_beta_60_boundary():
    assert sh.conical_critical_force_eq164(10.0, 100.0, 1000.0, 60.0) > 0.0


def test_eq164_beta_above_60_rejected():
    with pytest.raises(ValueError):
        sh.conical_critical_force_eq164(10.0, 100.0, 1000.0, 60.1)


def test_eq165_normal():
    expected = (0.9 * 1000.0 + 0.1 * 500.0) / math.cos(math.radians(30.0))
    assert sh.conical_equivalent_radius_eq165(500.0, 1000.0, 30.0) == pytest.approx(expected)


def test_eq165_beta_zero_boundary():
    assert sh.conical_equivalent_radius_eq165(500.0, 1000.0, 0.0) == pytest.approx(950.0)


def test_eq165_beta_above_60_rejected():
    with pytest.raises(ValueError):
        sh.conical_equivalent_radius_eq165(500.0, 1000.0, 61.0)


def test_eq166_normal():
    assert sh.conical_external_pressure_utilization_eq166(40.0, 100.0, 0.8) == pytest.approx(0.5)


def test_eq166_zero_boundary():
    assert sh.conical_external_pressure_utilization_eq166(0.0, 100.0, 1.0) == 0.0


def test_eq166_negative_demand_rejected():
    with pytest.raises(ValueError):
        sh.conical_external_pressure_utilization_eq166(-1.0, 100.0, 1.0)


def test_eq167_normal():
    assert sh.conical_external_pressure_critical_stress_eq167(206000.0, 1000.0, 2000.0, 10.0) == pytest.approx(0.55 * 206000.0 * 0.5 * 0.01**1.5)


def test_eq167_height_scaling():
    a = sh.conical_external_pressure_critical_stress_eq167(206000.0, 1000.0, 2000.0, 10.0)
    b = sh.conical_external_pressure_critical_stress_eq167(206000.0, 1000.0, 4000.0, 10.0)
    assert b == pytest.approx(0.5 * a)


def test_eq167_positive_height_required():
    with pytest.raises(ValueError):
        sh.conical_external_pressure_critical_stress_eq167(206000.0, 1000.0, 0.0, 10.0)


def test_eq168_normal():
    assert sh.conical_combined_stability_utilization_eq168(20.0, 100.0, 30.0, 150.0, 0.8) == pytest.approx(0.5)


def test_eq168_zero_boundary():
    assert sh.conical_combined_stability_utilization_eq168(0.0, 100.0, 0.0, 150.0, 1.0) == 0.0


def test_eq168_negative_force_rejected():
    with pytest.raises(ValueError):
        sh.conical_combined_stability_utilization_eq168(-1.0, 100.0, 0.0, 150.0, 1.0)


def test_eq169_normal():
    assert sh.spherical_external_pressure_utilization_eq169(0.1, 1000.0, 10.0, 20.0, 1.0) == pytest.approx(0.25)


def test_eq169_zero_boundary():
    assert sh.spherical_external_pressure_utilization_eq169(0.0, 1000.0, 10.0, 20.0, 1.0) == 0.0


def test_eq169_positive_critical_required():
    with pytest.raises(ValueError):
        sh.spherical_external_pressure_utilization_eq169(0.1, 1000.0, 10.0, 0.0, 1.0)


def test_principal_stress_check_and_signed_compression():
    result = sh.principal_stress_resistance_check_clause_11_1_1(-100.0, -50.0, 0.0, 355.0, 300.0, 1.0)
    assert result["compression_utilization"] == pytest.approx(1.0 / 3.0)
    assert result["pass"] is True


def test_axial_critical_stress_branches():
    result = sh.cylindrical_axial_critical_stress(3000.0, 10.0, 355.0, 206000.0)
    assert result["radius_to_thickness_ratio"] == 300.0
    assert result["critical_stress_n_mm2"] == min(result["yield_branch_n_mm2"], result["elastic_branch_n_mm2"])


def test_eccentric_compression_adjustment_shear_threshold():
    result = sh.eccentric_compression_critical_stress_multiplier_clause_11_2_1(100.0, -20.0, 0.0, 206000.0, 1000.0, 10.0)
    assert result["applicable"] is True
    assert result["multiplier"] == pytest.approx(1.12)


def test_tube_route_thresholds():
    result = sh.tube_local_stability_route_clause_11_2_2(1000.0, 20.0, 355.0, 206000.0, 1.0)
    assert result["route"] in {"global_stability_only_sections_7_and_9", "equation_156_local_stability_no_separate_global_check"}


def test_panel_interpolation_midpoint():
    ry = 355.0
    e = 206000.0
    result = sh.cylindrical_panel_limit(0.9 * ry, ry, e)
    low = sh.cylindrical_panel_limit_eq157(e, 0.8 * ry)
    high = sh.cylindrical_panel_limit_eq158(ry, e)
    assert result["limit_b_over_t"] == pytest.approx(0.5 * (low + high))


def test_panel_shell_route_boundary_20():
    result = sh.cylindrical_panel_route_clause_11_2_3(math.sqrt(20.0 * 1000.0 * 10.0), 1000.0, 10.0)
    assert result["route"] == "panel_equations_157_158"


def test_external_pressure_interpolation_midpoint():
    result = sh.cylindrical_external_pressure_critical_stress(206000.0, 1000.0, 15000.0, 10.0)
    at10 = sh.cylindrical_external_pressure_critical_stress_eq160(206000.0, 1000.0, 10000.0, 10.0)
    at20 = sh.cylindrical_external_pressure_critical_stress_eq161(206000.0, 1000.0, 10.0)
    assert result["critical_stress_n_mm2"] == pytest.approx(0.5 * (at10 + at20))


def test_ring_stiffener_requirements():
    result = sh.ring_stiffener_requirements_clause_11_2_4(0.01, 1000.0, 500.0, 10.0, 206000.0, 355.0)
    assert result["ring_compression_force_n"] == pytest.approx(5000.0)
    assert result["ring_effective_length_mm"] == pytest.approx(1800.0)
    assert result["maximum_relative_slenderness"] == 6.5


def test_spherical_critical_stress_cap_and_ratio_boundary():
    result = sh.spherical_external_pressure_critical_stress_clause_11_2_9(206000.0, 7500.0, 10.0, 355.0)
    assert result == pytest.approx(min(0.1 * 206000.0 / 750.0, 355.0))
    with pytest.raises(ValueError):
        sh.spherical_external_pressure_critical_stress_clause_11_2_9(206000.0, 7501.0, 10.0, 355.0)


def test_shell_analysis_route_flags():
    result = sh.shell_analysis_route_clause_11_1_4_11_1_5(True, True)
    assert result["local_edge_effect_analysis_required"] is True
    assert result["certified_spatial_software_required"] is True
