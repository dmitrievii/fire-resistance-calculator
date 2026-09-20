import math

import pytest

from standard_core import antenna_structures as a


def test_table_47_catalog_and_all_values():
    catalog = a.table_47_catalog()
    assert catalog["table"] == "47"
    assert len(catalog["rows"]) == 13
    expected = {
        "PRESTRESSED_LATTICE_MEMBER": 0.90,
        "RING_TYPE_FLANGE": 1.10,
        "OTHER_FLANGE_TYPE": 0.90,
        "GUY_OR_ANTENNA_ELEMENT_COUNT_3_TO_5": 0.80,
        "GUY_COUNT_6_TO_8": 0.90,
        "GUY_COUNT_9_OR_MORE": 0.95,
        "THIMBLE_CLAMPS_OR_POINT_CRIMP": 0.75,
        "ROPE_SPLICE_ON_THIMBLE_OR_INSULATOR": 0.55,
        "GUY_OR_ANTENNA_ATTACHMENT_ELEMENT": 0.90,
        "ANCHOR_ROD_TENSION_WITH_BENDING_NO_THREAD": 0.65,
        "EYE_PLATE_IN_TENSION": 0.65,
        "ROPE_ATTACHMENT_MECHANICAL_DETAIL_EXCEPT_HINGE_PIN": 0.80,
        "HINGE_PIN_IN_BEARING": 0.90,
    }
    assert {row["case_id"]: row["gamma_c"] for row in catalog["rows"]} == expected
    for key, value in expected.items():
        assert a.table_47_working_condition_factor(key) == value


def test_material_group_and_pipe_grade_route():
    result = a.antenna_structure_material_group_route_clause_17_1(
        2, "C345", is_pipe=True, annex_v_grade_selection_confirmed=True
    )
    assert result["component_group"] == 2
    assert result["pass"]
    with pytest.raises(ValueError):
        a.antenna_structure_material_group_route_clause_17_1(
            2, "C590", is_pipe=False, annex_v_grade_selection_confirmed=True
        )
    with pytest.raises(ValueError):
        a.antenna_structure_material_group_route_clause_17_1(
            2, "C390", is_pipe=True, annex_v_grade_selection_confirmed=True
        )


def test_rope_selection_routes():
    normal = a.steel_rope_selection_clause_17_2(
        300, "non_aggressive", "spiral_nonspinning", "metallic",
        built_in_nut_insulator=False, radio_allows_nonmetallic_core=False,
        round_wire_rope_capacity_kn=400, end_binding_length_increased_25_percent=False,
    )
    assert normal["required_zinc_group"] == "СС"
    assert normal["pass"]
    high = a.steel_rope_selection_clause_17_2(
        500, "strong", "round_strand_nonspinning_double_cross", "metallic",
        built_in_nut_insulator=False, radio_allows_nonmetallic_core=False,
        round_wire_rope_capacity_kn=450, end_binding_length_increased_25_percent=False,
    )
    assert high["required_zinc_group"] == "ЖС"
    assert high["locked_coil_required"]
    assert not high["pass"]


def test_rope_termination_and_wire_route():
    assert a.rope_end_zinc_alloy_check_clause_17_3("ЦАМ9-1,5Л")["pass"]
    assert not a.rope_end_zinc_alloy_check_clause_17_3("Zn")["pass"]
    assert a.antenna_wire_material_route_clause_17_4(
        annex_b_table_b2_selection_confirmed=True,
        copper_wire_used=False,
        technological_necessity_confirmed=False,
    )["pass"]
    assert not a.antenna_wire_material_route_clause_17_4(
        annex_b_table_b2_selection_confirmed=True,
        copper_wire_used=True,
        technological_necessity_confirmed=False,
    )["pass"]


def test_wire_gamma_m_and_design_force():
    assert a.wire_material_safety_factor_clause_17_5("aluminium") == 2.5
    assert a.wire_material_safety_factor_clause_17_5("bimetal_steel_copper") == 2.0
    assert a.wire_material_safety_factor_clause_17_5("steel_aluminium", 16) == 2.8
    assert a.wire_material_safety_factor_clause_17_5("steel_aluminium", 95) == 2.5
    assert a.wire_material_safety_factor_clause_17_5("steel_aluminium", 120) == 2.2
    result = a.wire_design_tension_force_clause_17_5(250000, "aluminium")
    assert result["design_tension_force_n"] == 100000
    with pytest.raises(ValueError):
        a.wire_material_safety_factor_clause_17_5("steel_aluminium", 100)


def test_support_deviation_limits():
    wind = a.support_relative_deviation_check_clause_17_7(250, 30000, "wind_or_ice")
    assert wind["limit_denominator"] == 100
    assert wind["utilization"] == pytest.approx(5 / 6)
    assert wind["pass"]
    unilateral = a.support_relative_deviation_check_clause_17_7(100, 30000, "unilateral_antenna_no_wind")
    assert unilateral["utilization"] == pytest.approx(1.0)
    assert unilateral["pass"]


def test_erection_connection_rules():
    result = a.erection_connection_check_clause_17_8(
        "B", "8.8", sign_changing_force=True, controlled_pretension_confirmed=True,
        erection_weld_used=False, installer_agreement_confirmed=False,
    )
    assert result["pass"]
    failed = a.erection_connection_check_clause_17_8(
        "A", "10.9", sign_changing_force=False, controlled_pretension_confirmed=False,
        erection_weld_used=False, installer_agreement_confirmed=False,
    )
    assert not failed["pass"]


def test_cross_lattice_platform_and_diaphragm_checks():
    cross = a.cross_lattice_and_platform_checks_clause_17_9(260, True, 10, 8, 3000)
    assert cross["intersection_tie_required"]
    assert cross["deflection_limit_mm"] == 12
    assert cross["pass"]
    diaphragm = a.diaphragm_check_clause_17_10(
        6000, 2500, diaphragm_at_concentrated_loads=True, diaphragm_at_chord_breaks=True
    )
    assert diaphragm["maximum_spacing_mm"] == 7500
    assert diaphragm["pass"]


def test_flange_bolts_node_and_guy_detailing():
    assert a.pipe_flange_bolt_layout_check_clause_17_11(
        one_circle=True, minimum_possible_circle_diameter=True, equal_spacing=True
    )["pass"]
    node = a.truss_node_detailing_checks_clause_17_12(
        members_centered_on_chord_axis=True, eccentricity_mm=20,
        chord_cross_section_size_mm=90, node_moment_analysis_performed=False,
        slot_end_hole_diameter_mm=24, round_brace_diameter_mm=20,
    )
    assert node["pass"]
    guy = a.guy_attachment_detailing_checks_clause_17_13(
        guy_centered_at_chord_strut_intersection=True,
        eye_plate_stiffened_against_bending=True,
        attachment_exceeds_transport_envelope=True,
        separate_rigid_insert_provided=True,
    )
    assert guy["pass"]


def test_flexible_insert_and_mechanical_detail_evidence():
    insert = a.flexible_cable_insert_check_clause_17_14(500, 20)
    assert insert["minimum_clear_length_mm"] == 400
    assert insert["pass"]
    evidence = a.mechanical_detail_evidence_clause_17_15(
        standard_detail_used=True, strength_tested=True, fatigue_tested=True,
        threaded_tension_element=True, rounded_thread_root_confirmed=True,
    )
    assert evidence["pass"]


def test_equation_215():
    expected = 0.41e-3 * 20 * math.sqrt(100000 / 2)
    assert a.vibration_damper_distance_eq215(20, 100000, 2) == pytest.approx(expected)


def test_vibration_damper_complete_route_and_span_trigger():
    result = a.vibration_damper_design_clause_17_16(
        20, 100000, 2, 350,
        low_frequency_hz=2, high_frequency_hz=10,
        paired_sequential_dampers=True,
        low_frequency_selected_from_fundamental_mode=True,
        high_frequency_damper_above_low_at_distance_s=True,
        dampers_installed=True,
        galloping_risk_present=False,
        free_length_modified_with_leashes=False,
    )
    assert result["mandatory_by_span_over_300_m"]
    assert result["pass"]
    failed = a.vibration_damper_design_clause_17_16(
        20, 100000, 2, 350,
        low_frequency_hz=3, high_frequency_hz=50,
        paired_sequential_dampers=False,
        low_frequency_selected_from_fundamental_mode=False,
        high_frequency_damper_above_low_at_distance_s=False,
        dampers_installed=False,
        galloping_risk_present=True,
        free_length_modified_with_leashes=False,
    )
    assert not failed["pass"]


def test_marking_and_galvanizing_evidence():
    assert a.obstruction_marking_and_lighting_check_clause_17_17(True)["pass"]
    assert a.galvanizing_check_clause_17_18(
        guy_mechanical_details_galvanized=True,
        insulator_fittings_galvanized=True,
        fasteners_galvanized=True,
    )["pass"]
