import pytest

from standard_core import structural_detailing_and_support_bearings as d


def test_table_44_catalog_and_exact_values():
    catalog = d.table_44_catalog()
    assert catalog["table"] == "44"
    assert len(catalog["rows"]) == 8
    assert d.table_44_maximum_spacing_m("heated_building", "between_joints_along_block", -45) == 230.0
    assert d.table_44_maximum_spacing_m("heated_building", "between_joints_along_block", -45.0001) == 160.0
    assert d.table_44_maximum_spacing_m("unheated_building_or_hot_shop", "between_joints_across_block", -20) == 120.0
    assert d.table_44_maximum_spacing_m("open_trestle", "joint_or_end_to_nearest_vertical_bracing_axis", -50) == 40.0


def test_table_44_rejects_nonexistent_row():
    with pytest.raises(ValueError):
        d.table_44_maximum_spacing_m("open_trestle", "between_joints_across_block", -20)


def test_temperature_joint_spacing_assessment_separates_limit_and_five_percent_trigger():
    within = d.temperature_joint_spacing_assessment_15_1(230, "heated_building", "between_joints_along_block", -30, False)
    assert within["table_compliance_pass"]
    slight = d.temperature_joint_spacing_assessment_15_1(240, "heated_building", "between_joints_along_block", -30, False)
    assert not slight["table_compliance_pass"]
    assert not slight["climatic_temperature_effects_inelastic_deformations_and_joint_flexibility_analysis_required"]
    large = d.temperature_joint_spacing_assessment_15_1(242, "heated_building", "between_joints_along_block", -30, False)
    assert large["exceeds_table_value_by_more_than_five_percent"]
    assert large["climatic_temperature_effects_inelastic_deformations_and_joint_flexibility_analysis_required"]
    stiff = d.temperature_joint_spacing_assessment_15_1(200, "heated_building", "between_joints_along_block", -30, True)
    assert stiff["table_compliance_pass"]
    assert stiff["climatic_temperature_effects_inelastic_deformations_and_joint_flexibility_analysis_required"]


def test_paired_vertical_bracing_note_limits():
    assert d.paired_vertical_bracing_max_spacing_m_15_1("building", -45) == 50.0
    assert d.paired_vertical_bracing_max_spacing_m_15_1("building", -46) == 40.0
    assert d.paired_vertical_bracing_max_spacing_m_15_1("open_trestle", -20) == 30.0
    assert d.paired_vertical_bracing_max_spacing_m_15_1("open_trestle", -50) == 25.0


def test_section_15_catalog_and_route():
    catalog = d.section_15_requirement_catalog()
    assert catalog["section"] == "15"
    assert len(catalog["entries"]) >= 75
    assert d.section_15_requirement_route("15.12.2")["category"] == "implemented_formula"
    assert "external" in d.section_15_requirement_route("15.9.7")["category"]
    with pytest.raises(KeyError):
        d.section_15_requirement_route("15.99")


def test_support_bearing_selection_and_friction():
    route = d.support_bearing_selection_15_12_1(True, "very_large", True)
    assert route["fixed_support_category"] == "balancing_fixed_hinged_support"
    assert route["movable_support_category"] == "flat_sliding_or_roller_movable_support"
    assert d.support_bearing_friction_coefficient_15_12_1("flat_sliding") == 0.3
    assert d.support_bearing_friction_coefficient_15_12_1("roller") == 0.03


def test_equation_199_and_contact_angle_wrapper():
    expected = 1200000 / (1.25 * 150 * 300 * 242.85714285714286)
    assert d.cylindrical_hinge_local_bearing_utilization_eq199(1200000, 150, 300, 242.85714285714286, 1) == pytest.approx(expected)
    result = d.cylindrical_hinge_bearing_check_15_12_2(1200000, 90, 150, 300, 242.85714285714286, 1)
    assert result["equation_199_applicable"]
    assert result["equation_199_pass"]
    with pytest.raises(ValueError):
        d.cylindrical_hinge_bearing_check_15_12_2(1200000, 89.999, 150, 300, 242.85714285714286, 1)


def test_equation_200_and_roller_wrapper():
    expected = 1200000 / (4 * 120 * 300 * 12.142857142857142)
    assert d.roller_diametral_compression_utilization_eq200(1200000, 4, 120, 300, 12.142857142857142, 1) == pytest.approx(expected)
    result = d.roller_bearing_check_15_12_3(1200000, 4, 120, 300, 12.142857142857142, 1)
    assert result["equation_200_capacity_n"] == pytest.approx(4 * 120 * 300 * 12.142857142857142)
    assert result["equation_200_pass"]


def test_zero_force_and_invalid_inputs():
    assert d.cylindrical_hinge_local_bearing_utilization_eq199(0, 1, 1, 1, 1) == 0.0
    zero = d.roller_bearing_check_15_12_3(0, 1, 1, 1, 1, 1)
    assert zero["equation_200_utilization"] == 0.0
    assert zero["equation_200_capacity_n"] == float("inf")
    with pytest.raises(ValueError):
        d.roller_diametral_compression_utilization_eq200(1, 0, 1, 1, 1, 1)
    with pytest.raises(TypeError):
        d.support_bearing_selection_15_12_1(1, "ordinary", False)
