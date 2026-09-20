import math

import pytest

from standard_core import overhead_line_and_switchyard_supports as s


def test_table_45_catalog_and_values():
    catalog = s.table_45_catalog()
    assert catalog["table"] == "45"
    assert len(catalog["rows"]) == 8
    assert s.table_45_working_condition_factor("FREE_STANDING_FIRST_TWO_PANELS_WELDED_CHORD") == 0.95
    assert s.table_45_working_condition_factor("GUY_ANCHOR_OR_ANGLE_SUPPORT_NORMAL") == 0.80


def test_table_45_rejects_node_connections():
    with pytest.raises(ValueError):
        s.table_45_working_condition_factor("FLAT_TRAVERSE_DIAGONAL_OR_STRUT", applied_to_node_connection=True)


def test_section_16_group_route():
    result = s.section_16_applicability_route("GROUP_1_SPECIAL_WELDED_CROSSING_OVER_60M")
    assert result["group"] == 1
    assert result["external_loads_required"] is True
    assert result["clause_16_3_status"] == "excluded_by_amendment_2"


def test_equations_201_to_203_and_pyramidal_mu():
    assert s.maximum_slenderness_eq201(12000, 2000) == 12.0
    assert s.maximum_slenderness_eq202(12000, 2000) == 15.0
    mu = 1.25 * (1 / 3) ** 2 - 2.75 * (1 / 3) + 3.5
    assert s.pyramidal_effective_length_factor_clause_16_5(1000, 3000) == pytest.approx(mu)
    assert s.maximum_slenderness_eq203(30000, 1000, 3000) == pytest.approx(2 * mu * 30000 / 3000)


def test_equations_204_and_205():
    assert s.relative_eccentricity_eq204(100e6, 1e6, 1000, 1.2) == pytest.approx(0.4152)
    assert s.relative_eccentricity_eq205(100e6, 1e6, 1000, 1.2) == pytest.approx(0.36)


def test_equations_206_and_207_with_auxiliaries():
    aux = s.guyed_support_second_order_auxiliaries(12000, 8000, 120, 1e6, 206000)
    assert aux["initial_bow_mm"] == pytest.approx(15.6)
    assert aux["equivalent_inertia_mm4"] == pytest.approx(80_000_000.0)
    expected_delta = 1 - 0.1 * 1e6 * 12000**2 / (206000 * 80_000_000)
    assert aux["delta"] == pytest.approx(expected_delta)
    expected_m = 80e6 + 1.2e6 / expected_delta * (12 + 15.6)
    expected_q = 45000 + 3.14 * 1.2e6 * (12 + 15.6) / (expected_delta * 12000)
    assert s.guyed_rectangular_moment_eq206(80e6, 1.2, 1e6, expected_delta, 12, 15.6) == pytest.approx(expected_m)
    assert s.guyed_rectangular_shear_eq207(45000, 1.2, 1e6, expected_delta, 12000, 12, 15.6) == pytest.approx(expected_q)


def test_equation_208_selects_larger_candidate():
    result = s.triangular_additional_chord_force_eq208(100e6, 50e6, 1000)
    assert result["candidate_1_n"] == pytest.approx(116000)
    assert result["candidate_2_n"] == pytest.approx(108000)
    assert result["governing_n"] == pytest.approx(116000)


def test_equations_209_and_210():
    expected_209 = 1 + (0.6 - 0.55 + 2 * (0.2 - 0.05 * 2)) * 0.3
    assert s.bolted_angle_chord_factor_eq209(0.6, 2, 0.3) == pytest.approx(expected_209)
    expected_210 = 0.95 + 0.1 * 0.5 + (0.34 - 0.62 * 0.5 + 2 * (0.2 - 0.05 * 2)) * 0.2
    assert s.bolted_angle_chord_factor_eq210(0.5, 2, 0.2) == pytest.approx(expected_210)


def test_equations_211_and_212_and_five_percent_modifier():
    expected_211 = 1.18 - 0.36 * 0.6 + (1.8 * 0.6 - 0.86) * 0.3
    assert s.bolted_angle_brace_factor_eq211(0.6, 0.3) == pytest.approx(expected_211)
    assert s.bolted_angle_brace_factor_eq211(0.6, 0.3, bolt_line_ratio=0.5) == pytest.approx(1.05 * expected_211)
    expected_212 = 1 - 0.04 * 0.5 + (0.36 - 0.41 * 0.5) * 0.2
    assert s.bolted_angle_brace_factor_eq212(0.5, 0.2) == pytest.approx(expected_212)


def test_angle_member_route_and_welded_rules():
    bolted = s.angle_member_eccentricity_factors_clause_16_12("chord", "bolted", 0.6, 2, 0.3)
    assert bolted["route"] == "equation_209"
    assert bolted["alpha_m"] >= 1.0
    welded = s.angle_member_eccentricity_factors_clause_16_12(
        "brace", "welded", 0.6, 2, 0.3, welded_centering="brace_axes_to_chord_heel"
    )
    assert welded["alpha_d"] == pytest.approx(1.036)
    accidental = s.angle_member_eccentricity_factors_clause_16_12(
        "brace", "welded", 0.6, 2, 0.3, welded_centering="brace_axes_to_chord_heel", broken_wire_combination=True
    )
    assert accidental["alpha_d"] == 1.0


def test_table_46_exact_values_and_normal_check():
    catalog = s.table_46_catalog()
    assert catalog["table"] == "46"
    assert len(catalog["rows"]) == 8
    check = s.table_46_deformation_check("SWITCHYARD_SUPPORT_ALONG_WIRES", "top_deviation", 0.008)
    assert check["limit_denominator"] == 100.0
    assert check["utilization"] == pytest.approx(0.8)
    assert check["pass"]


def test_table_46_emergency_and_equipment_routes():
    emergency = s.table_46_deformation_check(
        "SWITCHYARD_SUPPORT_ALONG_WIRES", "top_deviation", 1.0, load_mode="emergency"
    )
    assert emergency["applicable"] is False
    equipment = s.table_46_deformation_check(
        "EQUIPMENT_BEAM", "vertical_span", 1 / 350, stricter_equipment_limit_denominator=350
    )
    assert equipment["limit_denominator"] == 350.0
    assert equipment["pass"]


def test_section_16_detailing_checks():
    result = s.section_16_detailing_checks(
        traverse_member="chord_primary", panel_length_mm=3000, alternate_chord_length_mm=2500,
        actual_first_lower_brace_slenderness=140, support_system="free_standing", actual_diaphragm_spacing_m=20,
        diaphragm_at_concentrated_loads=True, diaphragm_at_chord_breaks=True,
        edge_distance_mm=40, bolt_diameter_mm=20, permanently_tensioned_single_bolt_element=True,
        braces_on_both_sides_of_chord_leg=True, splice_total_bolts=8,
        splice_bolts_per_leg_each_side=4, splice_rows_per_leg_each_side=4, use_seven_bolt_exception=False,
    )
    assert result["clause_16_13_effective_length_route"] == {"effective_length_mm": 3000.0, "radius": "i_min"}
    assert result["clause_16_14_first_lower_brace"]["pass"]
    assert result["clause_16_16_diaphragms"]["pass"]
    assert result["clause_16_19_splice"]["pass"]


def test_seven_bolt_exception_and_edge_failure_are_explicit():
    result = s.section_16_detailing_checks(
        traverse_member="strut", panel_length_mm=3000, alternate_chord_length_mm=2500,
        actual_first_lower_brace_slenderness=170, support_system="guyed", actual_diaphragm_spacing_m=16,
        diaphragm_at_concentrated_loads=False, diaphragm_at_chord_breaks=True,
        edge_distance_mm=25, bolt_diameter_mm=20, permanently_tensioned_single_bolt_element=True,
        braces_on_both_sides_of_chord_leg=False, splice_total_bolts=14,
        splice_bolts_per_leg_each_side=7, splice_rows_per_leg_each_side=7, use_seven_bolt_exception=True,
    )
    assert not result["clause_16_14_first_lower_brace"]["pass"]
    assert not result["clause_16_16_diaphragms"]["pass"]
    assert not result["clause_16_17_single_bolt_edge"]["pass"]
    assert result["clause_16_19_splice"]["gamma_b_multiplier"] == 0.85


def test_equations_213_and_214_polygonal_tube():
    lam = s.polygonal_tube_wall_relative_slenderness(500, 10, 345, 206000)
    assert lam == pytest.approx(50 * math.sqrt(345 / 206000))
    critical = s.polygonal_tube_critical_stress_eq214(lam, 100, -20, 345)
    beta = 0.58 + 1.81 * min(lam, 2.4) ** 2
    psi = 1 + 0.033 * min(lam, 2.4) * (1 - (-20) / 100)
    expected = min((beta - math.sqrt(beta**2 - 3.8 * min(lam, 2.4) ** 2)) * psi * 345, 345)
    assert critical["critical_stress_n_mm2"] == pytest.approx(expected)
    utilization = s.polygonal_tube_wall_stability_utilization_eq213(100, expected, 1)
    assert utilization == pytest.approx(100 / expected)


def test_polygonal_tube_wrapper_and_domain_errors():
    result = s.polygonal_tube_wall_stability_check(10, 500, 10, 100, -20, 345, 206000, 1)
    assert result["equation_213_pass"]
    assert result["linked_round_tube_requirements"] == ["11.2.1", "11.2.2"]
    with pytest.raises(ValueError):
        s.polygonal_tube_wall_stability_check(7, 500, 10, 100, -20, 345, 206000, 1)
    with pytest.raises(ValueError):
        s.bolted_angle_chord_factor_eq209(0.6, 2, 0.8)
