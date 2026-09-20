import math

import pytest

from standard_core import base_plates_and_combined_force_strength as bc


def test_equation_101_normal_zero_and_units():
    assert bc.base_plate_required_thickness_eq101(125000.0, 250.0, 1.0) == pytest.approx(math.sqrt(3000.0))
    assert bc.base_plate_required_thickness_eq101(0.0, 250.0, 1.0) == 0.0
    assert bc.base_plate_required_thickness_eq101(500000.0, 250.0, 1.0) == pytest.approx(2.0 * math.sqrt(3000.0))
    with pytest.raises(ValueError):
        bc.base_plate_required_thickness_eq101(-1.0, 250.0, 1.0)


def test_equation_102_normal_zero_and_quadratic_scaling():
    assert bc.base_plate_cantilever_moment_eq102(1.0, 100.0) == 5000.0
    assert bc.base_plate_cantilever_moment_eq102(0.0, 100.0) == 0.0
    assert bc.base_plate_cantilever_moment_eq102(1.0, 200.0) == 20000.0
    with pytest.raises(ValueError):
        bc.base_plate_cantilever_moment_eq102(1.0, -1.0)


def test_equation_103_normal_zero_and_direction_mapping():
    result = bc.base_plate_four_side_moments_eq103(1.0, 100.0, 0.048, 0.037)
    assert result["moment_short_direction_n_mm_per_mm"] == 480.0
    assert result["moment_long_direction_n_mm_per_mm"] == 370.0
    zero = bc.base_plate_four_side_moments_eq103(0.0, 100.0, 0.048, 0.037)
    assert zero == {"moment_short_direction_n_mm_per_mm": 0.0, "moment_long_direction_n_mm_per_mm": 0.0}
    with pytest.raises(ValueError):
        bc.base_plate_four_side_moments_eq103(1.0, 100.0, -0.1, 0.284)


def test_equation_104_normal_zero_and_quadratic_scaling():
    assert bc.base_plate_three_side_moment_eq104(1.0, 100.0, 0.112) == 1120.0
    assert bc.base_plate_three_side_moment_eq104(0.0, 100.0, 0.112) == 0.0
    assert bc.base_plate_three_side_moment_eq104(1.0, 200.0, 0.112) == 4480.0
    with pytest.raises(ValueError):
        bc.base_plate_three_side_moment_eq104(1.0, 0.0, 0.112)


def test_table_e2_exact_lookup_terminal_and_no_interpolation():
    assert bc.annex_e2_base_plate_coefficients("four_sides", 1.0) == {"alpha_1": 0.048, "alpha_2": 0.048}
    assert bc.annex_e2_base_plate_coefficients("four_sides", 2.01) == {"alpha_1": 0.125, "alpha_2": 0.037}
    assert bc.annex_e2_base_plate_coefficients("three_sides", 2.01) == {"alpha_3": 0.133}
    with pytest.raises(ValueError):
        bc.annex_e2_base_plate_coefficients("four_sides", 1.05)


def test_table_e2_catalog_consistency():
    data = bc.annex_e2_catalog()
    assert len(data["four_sides"]["ratio_nodes"]) == 11
    assert len(data["four_sides"]["coefficients"]["alpha_1"]) == 11
    assert len(data["three_sides"]["ratio_nodes"]) == 9
    assert data["interpolation_rule"] == "not_specified_exact_nodes_only"


def test_two_adjacent_side_geometry():
    result = bc.base_plate_two_adjacent_sides_geometry(300.0, 400.0)
    assert result["diagonal_d1_mm"] == 500.0
    assert result["perpendicular_distance_a1_mm"] == 240.0
    assert result["ratio_a1_over_d1"] == 0.48
    with pytest.raises(ValueError):
        bc.base_plate_two_adjacent_sides_geometry(0.0, 400.0)


def test_maximum_plate_moment():
    assert bc.base_plate_maximum_unit_width_moment([100.0, 250.0, 200.0]) == 250.0
    assert bc.base_plate_maximum_unit_width_moment([0.0]) == 0.0
    with pytest.raises(ValueError):
        bc.base_plate_maximum_unit_width_moment([])
    with pytest.raises(ValueError):
        bc.base_plate_maximum_unit_width_moment([1.0, -1.0])


def test_foundation_area_boundary():
    assert bc.base_plate_foundation_area_boundary(True)["permitted"] is True
    assert bc.base_plate_foundation_area_boundary(False)["permitted"] is False
    with pytest.raises(TypeError):
        bc.base_plate_foundation_area_boundary(1)


def test_equation_105_normal_zero_and_units():
    result = bc.combined_force_strength_utilization_eq105(
        100000.0, 2000.0, 1e7, 2e7, 1e9, 1.0, 1.0, 1.0,
        1e6, 2e6, 1e9, 250.0, 1.0,
    )
    assert result == pytest.approx(0.284)
    assert bc.combined_force_strength_utilization_eq105(
        0.0, 2000.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
        1e6, 2e6, 1e9, 250.0, 1.0,
    ) == 0.0
    doubled = bc.combined_force_strength_utilization_eq105(
        200000.0, 4000.0, 2e7, 4e7, 2e9, 1.0, 1.0, 1.0,
        2e6, 4e6, 2e9, 250.0, 1.0,
    )
    assert doubled == pytest.approx(result)
    with pytest.raises(ValueError):
        bc.combined_force_strength_utilization_eq105(
            -1.0, 2000.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
            1e6, 2e6, 1e9, 250.0, 1.0,
        )


def test_equation_106_sign_superposition_zero_and_units():
    result = bc.combined_force_point_utilization_eq106(
        100000.0, 2000.0, 1e7, 100.0, 1e9,
        2e7, -50.0, 2e9, 1e9, 100.0, 1e12, 250.0, 1.0,
    )
    expected_stress = 50.0 + 1.0 - 0.5 + 0.1
    assert result == pytest.approx(abs(expected_stress) / 250.0)
    cancellation = bc.combined_force_point_utilization_eq106(
        100000.0, 2000.0, -5e8, 100.0, 1e9,
        0.0, 0.0, 2e9, 0.0, 0.0, 1e12, 250.0, 1.0,
    )
    assert cancellation == 0.0
    scaled = bc.combined_force_point_utilization_eq106(
        200000.0, 4000.0, 2e7, 100.0, 2e9,
        4e7, -50.0, 4e9, 2e9, 100.0, 2e12, 250.0, 1.0,
    )
    assert scaled == pytest.approx(result)


def test_equation_108_normal_zero_and_dimensionless_scaling():
    assert bc.high_strength_asymmetric_delta_eq108(100000.0, 2.0, 2000.0, 250.0) == pytest.approx(0.92)
    assert bc.high_strength_asymmetric_delta_eq108(0.0, 2.0, 2000.0, 250.0) == 1.0
    assert bc.high_strength_asymmetric_delta_eq108(200000.0, 2.0, 4000.0, 250.0) == pytest.approx(0.92)
    with pytest.raises(ValueError):
        bc.high_strength_asymmetric_delta_eq108(-1.0, 2.0, 2000.0, 250.0)


def test_equation_107_normal_zero_and_subtraction_sign():
    result = bc.high_strength_asymmetric_tension_fiber_utilization_eq107(
        100000.0, 2000.0, 2e7, 0.8, 1e6, 500.0, 1.3, 1.0
    )
    assert result == pytest.approx(0.065)
    zero = bc.high_strength_asymmetric_tension_fiber_utilization_eq107(
        0.0, 2000.0, 0.0, 0.8, 1e6, 500.0, 1.3, 1.0
    )
    assert zero == 0.0
    cancellation = bc.high_strength_asymmetric_tension_fiber_utilization_eq107(
        100000.0, 2000.0, 4e7, 0.8, 1e6, 500.0, 1.3, 1.0
    )
    assert cancellation == 0.0
    with pytest.raises(ValueError):
        bc.high_strength_asymmetric_tension_fiber_utilization_eq107(
            1.0, 1.0, 1.0, 0.0, 1.0, 500.0, 1.3, 1.0
        )


def test_equation_105_applicability_boundaries():
    assert bc.equation_105_applicability(355.0, False, 49.999, 100.0, 100000.0, 2000.0, 250.0, True, True)["permitted"]
    assert not bc.equation_105_applicability(355.0, False, 50.0, 100.0, 100000.0, 2000.0, 250.0, True, True)["permitted"]
    low = bc.equation_105_applicability(355.0, False, 10.0, 100.0, 10000.0, 2000.0, 250.0, False, True)
    assert low["low_axial_stress_branch"] is True
    assert low["permitted"] is False
    assert not bc.equation_105_applicability(441.0, False, 10.0, 100.0, 100000.0, 2000.0, 250.0, True, True)["permitted"]


def test_combined_force_coefficients_use_annex_e1():
    result = bc.combined_force_coefficients_from_annex_e1("1", 0.75, False)
    assert result["c_x"] == pytest.approx(1.095)
    assert result["n"] > 0.0
    with pytest.raises(ValueError):
        bc.combined_force_coefficients_from_annex_e1("1", 100.0, False)


def test_equation_105_omission_rule():
    assert bc.equation_105_omission_rule_clause_9_1_2(20.0, True, True)["may_omit_equation_105"]
    assert not bc.equation_105_omission_rule_clause_9_1_2(20.01, True, True)["may_omit_equation_105"]
    assert not bc.equation_105_omission_rule_clause_9_1_2(10.0, False, True)["may_omit_equation_105"]


def test_equation_107_applicability():
    assert bc.equation_107_applicability(460.0, True)["permitted"]
    assert not bc.equation_107_applicability(440.0, True)["permitted"]
    assert not bc.equation_107_applicability(460.0, False)["permitted"]
