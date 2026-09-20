import math

import pytest

from standard_core import reconstruction_assessment as r


def test_condition_categories_and_monitoring_route():
    assert r.technical_condition_category_clause_18_1_1(
        defects_or_damage_present=False,
        local_character_only=True,
        restricts_normal_operation=False,
        requires_monitoring_or_strengthening=False,
        sudden_failure_or_global_instability_risk=False,
    )["category"] == "normative"
    assert r.technical_condition_category_clause_18_1_1(
        defects_or_damage_present=True,
        local_character_only=False,
        restricts_normal_operation=True,
        requires_monitoring_or_strengthening=True,
        sudden_failure_or_global_instability_risk=False,
    )["category"] == "limited_serviceable"
    assert r.technical_condition_category_clause_18_1_1(
        defects_or_damage_present=True,
        local_character_only=False,
        restricts_normal_operation=True,
        requires_monitoring_or_strengthening=True,
        sudden_failure_or_global_instability_risk=True,
    )["category"] == "emergency"
    assert r.strengthening_and_monitoring_route_clause_18_1_2(
        "limited_serviceable",
        monitoring_program_confirmed=True,
        smooth_load_transfer_to_strengthening_confirmed=True,
        construction_stage_capacity_confirmed=True,
    )["pass"]


def test_verification_calculation_exemption():
    assert r.verification_calculation_exemption_clause_18_1_3(
        20,
        defects_or_damage_present=False,
        operating_conditions_worsened=False,
        loads_increased=False,
        main_member_strengthening_required=False,
    )["verification_calculation_may_be_omitted"]
    assert not r.verification_calculation_exemption_clause_18_1_3(
        14.9,
        defects_or_damage_present=False,
        operating_conditions_worsened=False,
        loads_increased=False,
        main_member_strengthening_required=False,
    )["verification_calculation_may_be_omitted"]


def test_material_evidence_and_test_program():
    assert r.material_evidence_route_clause_18_2_1(
        factory_certificate_available=True,
        sample_tests_completed=False,
        executive_documentation_complete=True,
        metal_quality_doubt_present=False,
    )["pass"]
    test_program = r.metal_test_program_clause_18_2_2(
        "open_hearth",
        chemical_composition_tested=True,
        tensile_properties_tested=True,
        stress_strain_diagram_obtained=True,
        impact_toughness_tested_if_required=True,
        macro_microstructure_tested_if_required=True,
        sulfur_percent=0.03,
        phosphorus_percent=0.03,
    )
    assert test_program["impact_toughness_required"]
    assert test_program["pass"]
    exception = r.metal_test_program_clause_18_2_2(
        "puddled",
        chemical_composition_tested=True,
        tensile_properties_tested=True,
        stress_strain_diagram_obtained=True,
        impact_toughness_tested_if_required=False,
        macro_microstructure_tested_if_required=True,
        sulfur_percent=0.03,
        phosphorus_percent=0.03,
    )
    assert not exception["impact_toughness_required"]
    assert exception["pass"]


def test_pre_1950_route_and_existing_steel_resistances():
    assert r.pre_1950_specialized_institute_route_clause_18_2_3(
        "before_1950",
        specialized_research_institute_confirmed=True,
        steel_production_method_identified=True,
    )["pass"]
    modern = r.existing_steel_design_resistances_clause_18_2_4(
        "after_1988_statistical_certificate", 355, 510
    )
    assert modern["gamma_m"] == 1.05
    assert modern["design_yield_resistance_n_mm2"] == pytest.approx(355 / 1.05)
    old = r.existing_steel_design_resistances_clause_18_2_4(
        "before_1950_tests", 300, 420, steel_process="puddled"
    )
    assert old["design_yield_resistance_n_mm2"] == 170


def test_weld_and_unknown_bolt_defaults():
    weld = r.existing_weld_resistance_defaults_clause_18_2_5(500, 300, "after_1972")
    assert weld["fillet_weld_metal_resistance_n_mm2"] == 220
    assert weld["tension_butt_weld_resistance_n_mm2"] == 255
    bolt = r.unknown_bolt_resistance_defaults_clause_18_2_6()
    assert bolt == {
        "bolt_shear_design_resistance_n_mm2": 150.0,
        "bolt_tension_design_resistance_n_mm2": 160.0,
    }


def test_table_48_catalog_and_values():
    assert len(r.table_48_catalog()["rows"]) == 7
    assert r.table_48_rivet_resistance("shear", "B", "St2_St3") == 180
    assert r.table_48_rivet_resistance("shear", "B", "09G2") == 220
    assert r.table_48_rivet_resistance("shear", "C", "St2_St3") == 160
    assert r.table_48_rivet_resistance("tension_head_pull_off", "B", "09G2") == 150
    assert r.table_48_rivet_resistance(
        "bearing", "C", "St2_St3", connected_steel_design_yield_n_mm2=300
    ) == 510
    assert r.table_48_rivet_resistance(
        "shear", "B", "St2_St3", countersunk_or_semicountersunk_head=True
    ) == 144
    with pytest.raises(ValueError):
        r.table_48_rivet_resistance(
            "tension_head_pull_off", "B", "St2_St3", countersunk_or_semicountersunk_head=True
        )


def test_rivet_capacities():
    shear = r.rivet_connection_capacity_clause_18_2_7("shear", 180, 20, shear_planes=2)
    assert shear["rivet_area_mm2"] == pytest.approx(314.0)
    assert shear["capacity_n"] == pytest.approx(180 * 314 * 2)
    bearing = r.rivet_connection_capacity_clause_18_2_7(
        "bearing", 510, 20, connected_thickness_sum_mm=24
    )
    assert bearing["capacity_n"] == pytest.approx(510 * 20 * 24)


def test_strengthening_decision_and_execution_routes():
    route = r.existing_structure_strengthening_route_clauses_18_3_1_to_18_3_4(
        brittle_steel_temperature_condition_triggered=False,
        post_reconstruction_stress_not_above_existing_confirmed=True,
        actual_geometry_supports_and_defects_in_model_confirmed=True,
        mandatory_code_checks_pass=True,
        serviceability_exceedance_blocks_operation=False,
        slenderness_exceedance_acceptable_by_test_or_calculation=False,
    )
    assert route["decision"] == "retain_without_strengthening"
    execution = r.strengthening_execution_checks_clauses_18_3_5_to_18_3_10(
        construction_stage_capacity_confirmed=True,
        additional_holes_and_welding_effects_included=True,
        load_state_during_work_defined=True,
        intermittent_flange_weld_used=True,
        structure_group=3,
        design_temperature_c=-40,
        environment="mild",
        combined_connection_type="rivets_plus_friction",
    )
    assert execution["pass"]


def test_weld_heating_limit_and_common_resistance():
    assert r.weld_heating_stress_limit_clause_18_3_9(1, 300) == 60
    assert r.weld_heating_stress_limit_clause_18_3_9(2, 300) == 120
    assert r.weld_heating_stress_limit_clause_18_3_9(4, 300) == 240
    common = r.common_or_separate_design_resistance_clause_18_3_11(300, 330)
    assert common["use_one_common_resistance"]
    assert common["common_resistance_n_mm2"] == 300
    separate = r.common_or_separate_design_resistance_clause_18_3_11(300, 360)
    assert not separate["use_one_common_resistance"]


def test_equation_216_and_gamma_n():
    gamma_n = r.gamma_n_clause_18_3_13(
        welding_used=True, initial_design_stress_n_mm2=100, design_yield_resistance_n_mm2=400
    )
    assert gamma_n == pytest.approx(0.8875)
    util = r.symmetric_compression_strength_utilization_eq216(500000, 3000, 400, gamma_n, 1)
    assert util == pytest.approx(500000 / (3000 * 400 * gamma_n))


def test_equation_217_and_gamma_m():
    gamma_m = r.gamma_m_clause_18_3_13(1, 300000, 2000, 300, 0.9)
    assert gamma_m == 0.95
    forced = r.gamma_m_clause_18_3_13(2, 360000, 2000, 300, 0.88)
    assert forced == 0.88
    result = r.asymmetric_strength_utilization_eq217(
        300000, 2000, 1e7, 8e6, 100, -2e6, 4e6, 50, 300, gamma_m, 1
    )
    expected_stress = 300000 / 2000 + 1e7 * 100 / 8e6 - 2e6 * 50 / 4e6
    assert result["signed_stress_n_mm2"] == pytest.approx(expected_stress)
    assert result["utilization"] == pytest.approx(abs(expected_stress) / (300 * gamma_m))


def test_equations_218_to_221():
    assert r.strengthened_member_stability_utilization_eq218(500000, .8, 3000, 320, .9) == pytest.approx(
        500000 / (.8 * 3000 * 320 * .9)
    )
    assert r.reduced_relative_eccentricity_eq219(10, 3000, 300000) == pytest.approx(.1)
    alpha_n = r.longitudinal_force_influence_alpha_n_clause_18_3_14(1e6, 2e5)
    assert alpha_n == pytest.approx(1.25)
    f_after = r.post_strengthening_initial_deflection_eq221(10, alpha_n, 1000, 9000)
    assert f_after == pytest.approx(8.75)
    k_fw = r.welding_deflection_factor_k_fw_clause_18_3_14(13.75, -2)
    assert k_fw == .5
    ef = r.equivalent_eccentricity_eq220(5, f_after, k_fw, -2)
    assert ef == pytest.approx(12.75)


def test_equation_222_and_weld_parameter():
    v = r.weld_shortening_parameter_v(.8)
    assert v == pytest.approx(.0256)
    fw = r.welding_residual_deflection_eq222(
        1, 1.25, 100,
        [{"n_i": 1.2, "v_i": v, "y_i": 2.0}, {"n_i": .8, "v_i": v, "y_i": -1.0}],
    )
    expected = 1 * 1.25 * 100**2 / 8 * (1.2 * v * 2 + .8 * v * -1)
    assert fw == pytest.approx(expected)


def test_equations_223_and_224():
    k = r.composite_resistance_factor_eq224(345, 300, 2000, 3000, 8e6, 12e6)
    expected = (345 / 300 * (1 - 2 / 3) + 2 / 3) ** 2
    assert k == pytest.approx(expected)
    assert r.effective_design_resistance_eq223(300, k) == pytest.approx(300 * math.sqrt(k))


def test_existing_deviation_acceptance():
    result = r.existing_deviation_acceptance_clause_18_3_16(
        listed_deviation_only=True,
        damage_caused_by_deviation_absent=True,
        adverse_operating_change_excluded=True,
        capacity_and_stiffness_justified=True,
        fatigue_and_brittle_fracture_measures_confirmed=True,
    )
    assert result["accepted_without_strengthening"]
    assert result["central_compression_section_type_substitution"] == "b_instead_of_c"
