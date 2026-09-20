import math
import pytest

from standard_core import built_up_beam_columns_and_combined_local_stability as v11


def test_table_catalogs():
    assert v11.table_22_catalog()["table_number"] == "22"
    assert set(v11.table_22_catalog()["section_types"]) == {"1", "2", "3", "4", "5"}
    assert v11.table_23_catalog()["table_number"] == "23"
    assert set(v11.table_23_catalog()["section_types"]) == {"1", "2", "3", "4"}


def test_equations_123_and_124():
    assert v11.built_up_relative_eccentricity_eq123(80.0, 12000.0, 300.0, 144000000.0) == pytest.approx(2.0)
    assert v11.built_up_relative_eccentricity_eq123(0.0, 12000.0, 300.0, 144000000.0) == 0.0
    assert v11.biaxial_branch_additional_force_eq124(120e6, 600.0, 60e6, 500.0) == pytest.approx(160000.0)
    with pytest.raises(ValueError):
        v11.built_up_relative_eccentricity_eq123(1.0, 1.0, 1.0, 0.0)


def test_branch_additional_force_rules():
    assert v11.branch_additional_force_y_types_1_3(120e6, 600.0) == pytest.approx(200000.0)
    assert v11.branch_additional_force_y_type_2(120e6, 600.0) == pytest.approx(100000.0)
    assert v11.branch_additional_force_x_type_3(60e6, 500.0) == pytest.approx(139200.0)
    assert v11.branch_additional_force_x_type_2(60e6, 500.0) == pytest.approx(60000.0)
    with pytest.raises(ValueError):
        v11.branch_additional_force_x_type_2(-1.0, 500.0)


def test_whole_member_route_and_connector_force():
    result = v11.built_up_whole_member_stability_clause_9_3_2(2.0, 2.0, 0.9)
    assert result["route"] == "equation_109_with_table_d4"
    assert 0 < result["phi_e"] <= 0.9
    assert v11.built_up_whole_member_stability_clause_9_3_2(2.0, 20.01, 0.9)["route"] == "bending_member_section_8"
    connector = v11.connector_design_shear_clause_9_3_7(80000.0, 60000.0)
    assert connector["governing_shear_force_n"] == 80000.0
    assert connector["lattice_required"] is True


def test_branch_and_external_routes():
    assert v11.branch_force_with_additional_component(500000.0, 160000.0) == 660000.0
    batten = v11.battened_branch_check_route_clause_9_3_4(100000.0, 2e7, 80000.0)
    assert "equation_109" in batten["required_check"]
    assert v11.three_sided_built_up_route_clause_9_3_5(True)["calculation_completed_here"] is False
    two = v11.two_solid_branch_route_clause_9_3_6(60e6, 500000.0, 50.0, False)
    assert two["branch_moment_x_n_mm"] == 25e6
    assert two["branch_routes"] == ["equation_109", "equation_111"]


def test_actual_slenderness_helpers():
    expected_web = 60.0 * math.sqrt(355.0 / 206000.0)
    assert v11.combined_web_relative_slenderness(600.0, 10.0, 355.0, 206000.0) == pytest.approx(expected_web)
    expected_flange = (150.0 / 16.0) * math.sqrt(355.0 / 206000.0)
    assert v11.combined_flange_relative_slenderness(150.0, 16.0, 355.0, 206000.0) == pytest.approx(expected_flange)


def test_table_22_stress_parameters():
    result = v11.table_22_stress_parameters(180.0, -60.0, 30.0, 15.5)
    assert result["alpha"] == pytest.approx(4.0 / 3.0)
    assert result["beta"] == pytest.approx(0.15 * 15.5 * 30.0 / 180.0)


def test_equations_125_to_130():
    assert v11.web_limit_eq125(1.5) == pytest.approx(1.6375)
    assert v11.web_limit_eq126(4.0) == pytest.approx(2.6)
    beta = 0.2
    expected127 = min(1.42 * math.sqrt(15.5 * 355.0 / (180.0 * (2.0 - 1.2 + math.sqrt(1.2**2 + 4.0 * beta**2)))), 0.7 + 2.4 * 1.2)
    assert v11.web_limit_eq127(1.2, beta, 15.5, 355.0, 1.0, 180.0) == pytest.approx(expected127)
    assert v11.web_limit_eq128(3.0, 1.2) == pytest.approx(min(2.25, 2.68))
    assert v11.web_limit_eq129(0.1, 700.0, 600.0) == pytest.approx((0.4 + 0.07 * 0.8) * (1 + 0.25 * math.sqrt(2 - 700 / 600)))
    assert v11.web_limit_eq130(12000.0, 355.0, 1.0, 1800000.0) == pytest.approx(2 * math.sqrt(12000 * 355 / 1800000))
    with pytest.raises(ValueError):
        v11.web_limit_eq125(2.0)
    with pytest.raises(ValueError):
        v11.web_limit_eq127(0.8, beta, 15.5, 355.0, 1.0, 180.0)


def test_table_22_type_1_interpolation():
    base_at_1 = v11.web_limit_eq125(1.5)
    assert v11.table_22_type_1_limit(1.5, 0.5, 1.2, 2.2) == pytest.approx((1.2 + base_at_1) / 2)
    assert v11.table_22_type_1_limit(1.5, 5.0, 1.2, 2.2) == pytest.approx(base_at_1)
    assert v11.table_22_type_1_limit(1.5, 15.0, 1.2, 2.2) == pytest.approx((base_at_1 + 2.2) / 2)


def test_table_22_type_2_and_type_5_interpolation():
    half = v11.table_22_type_2_limit(0.5, 1.8, 1.6, 0.2, 15.5, 355.0, 1.0, 180.0)
    assert half == 1.6
    one = v11.web_limit_eq127(1.0, 0.2, 15.5, 355.0, 1.0, 180.0)
    assert v11.table_22_type_2_limit(0.75, 1.8, 1.6, 0.2, 15.5, 355.0, 1.0, 180.0) == pytest.approx((1.6 + one) / 2)
    eq130 = v11.web_limit_eq130(12000.0, 355.0, 1.0, 1800000.0)
    assert v11.table_22_type_5_limit(0.5, 1.0, 12000.0, 355.0, 1.0, 1800000.0) == pytest.approx((1 + eq130) / 2)


def test_equation_131_and_routes():
    assert v11.web_limit_adjustment_eq131(2.0, 3.0, 1.0) == 2.0
    assert v11.web_limit_adjustment_eq131(2.0, 3.0, 0.9) == pytest.approx(2.5)
    assert v11.web_limit_adjustment_eq131(2.0, 3.0, 0.7) == 3.0
    stiff = v11.transverse_stiffener_route_clause_9_4_4(2.4, 600.0, 355.0, 206000.0, "paired_symmetric", 70.0, False, False)
    assert stiff["required"] is True
    longitudinal = v11.longitudinal_stiffener_route_clause_9_4_5(6 * 600 * 10**3, 600.0, 10.0)
    assert longitudinal["inertia_pass"] is True
    reduced = v11.reduced_area_route_clause_9_4_6(2, 0.5, 2.5, 2.0)
    assert reduced["reduced_area_required"] is True
    assert 111 in reduced["equations_using_reduced_area"]
    with pytest.raises(ValueError):
        v11.web_limit_adjustment_eq131(2.0, 3.0, 1.1)


def test_equations_132_to_135():
    assert v11.flange_limit_eq132(0.65, 2.0, 5.0) == pytest.approx(0.65 - 0.01 * (1.5 + 1.4) * 5)
    assert v11.flange_limit_eq133(0.65, 2.0, 5.0) == pytest.approx(0.65 - 0.01 * (5.3 + 2.6) * 5)
    assert v11.flange_limit_eq134(0.1) == pytest.approx(0.44)
    assert v11.flange_limit_eq135(5.0) == pytest.approx(0.76)
    with pytest.raises(ValueError):
        v11.flange_limit_eq132(0.65, 2.0, 5.1)


def test_table_23_router_and_modifiers():
    at5 = v11.flange_limit_eq132(0.65, 2.0, 5.0)
    result = v11.table_23_limit(1, 0.65, 2.0, 1.8, 12.5, 0.55)
    assert result == pytest.approx((at5 + 0.55) / 2)
    assert v11.table_23_limit(3, 0.65, 2.0, 1.8, 0.0, 0.55) == pytest.approx(0.56)
    assert v11.edge_return_flange_limit_clause_9_4_8(0.6, True) == pytest.approx(0.9)
    factor = v11.two_plane_limit_increase_clause_9_4_9([0.8, 0.7, 0.75], 12000.0, 355.0, 1800000.0)
    assert factor == pytest.approx(min(math.sqrt(0.7 * 12000 * 355 / 1800000), 1.25))
    assert v11.tension_member_local_stability_route_clause_9_4_10(True)["route"] == "bending_member_local_stability_section_8_5"


def test_negative_and_type_guards():
    with pytest.raises(TypeError):
        v11.edge_return_flange_limit_clause_9_4_8(0.5, 1)
    with pytest.raises(ValueError):
        v11.table_23_limit(5, 0.6, 2.0, 2.0, 1.0, 0.5)
    with pytest.raises(ValueError):
        v11.two_plane_limit_increase_clause_9_4_9([], 1.0, 1.0, 1.0)
