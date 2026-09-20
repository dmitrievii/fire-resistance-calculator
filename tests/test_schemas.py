import json
from pathlib import Path

from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

from standard_core.release_metadata import RELEASE_STAGE

ROOT = Path(__file__).resolve().parents[1]


def _load(schema_name, example_name):
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    case = json.loads((ROOT / "examples" / example_name).read_text(encoding="utf-8"))
    return schema, case


def test_minimal_case_validates():
    schema, case = _load("minimal_case.schema.json", "minimal_case_example.json")
    assert validate_case(case, schema) == []


def test_axial_case_validates():
    schema, case = _load("axial_member_case.schema.json", "axial_member_example.json")
    assert validate_case(case, schema) == []


def test_unknown_property_is_rejected():
    schema, case = _load("axial_member_case.schema.json", "axial_member_example.json")
    case["hidden_default"] = 1
    assert any("Unexpected property" in error for error in validate_case(case, schema))


def test_axial_applicability_confirmation_is_enforced():
    schema, case = _load("axial_member_case.schema.json", "axial_member_example.json")
    case["single_angle_clause_7_1_2_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_material_runner_writes_outputs():
    result = run_case(ROOT / "examples/minimal_case_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["foundation_anchor_bolt_tension_design_resistance_n_mm2"] == 284.0
    assert (ROOT / "outputs/material_resistance_result.json").exists()


def test_axial_runner_writes_outputs():
    result = run_case(ROOT / "examples/axial_member_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["relative_slenderness"] == 2.0
    assert result["results"]["table_d1_phi"] == 0.826
    assert (ROOT / "outputs/axial_member_result.json").exists()


def test_built_up_case_validates():
    schema, case = _load("built_up_axial_member_case.schema.json", "built_up_axial_member_example.json")
    assert validate_case(case, schema) == []


def test_built_up_applicability_confirmation_is_enforced():
    schema, case = _load("built_up_axial_member_case.schema.json", "built_up_axial_member_example.json")
    case["clause_7_2_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_built_up_runner_writes_outputs():
    result = run_case(ROOT / "examples/built_up_axial_member_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["clause_7_2_2_method"] == "table_8_effective_slenderness"
    assert result["results"]["equation_18_fictitious_shear_force_n"] > 0.0
    assert (ROOT / "outputs/built_up_axial_member_result.json").exists()


def test_local_stability_case_validates():
    schema, case = _load("local_stability_case.schema.json", "local_stability_example.json")
    assert validate_case(case, schema) == []


def test_local_stability_applicability_confirmation_is_enforced():
    schema, case = _load("local_stability_case.schema.json", "local_stability_example.json")
    case["clause_7_3_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_local_stability_runner_writes_outputs():
    result = run_case(ROOT / "examples/local_stability_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["reduced_area_status"] == "applied"
    assert result["results"]["design_area_mm2"] < result["inputs"]["gross_area_mm2"]
    assert (ROOT / "outputs/local_stability_result.json").exists()


def test_bending_case_validates():
    schema, case = _load("bending_member_case.schema.json", "bending_member_example.json")
    assert validate_case(case, schema) == []


def test_bending_required_confirmations_are_enforced():
    schema, case = _load("bending_member_case.schema.json", "bending_member_example.json")
    case["required_clause_checks_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_bending_runner_writes_outputs():
    result = run_case(ROOT / "examples/bending_member_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["equation_41_elastic_bending_utilization"] > 0.0
    assert result["results"]["equation_60_bimetal_biaxial_utilization"] > 0.0
    assert (ROOT / "outputs/bending_member_result.json").exists()


def test_base_plate_combined_case_validates():
    schema, case = _load("base_plates_and_combined_force_strength_case.schema.json", "base_plates_and_combined_force_strength_example.json")
    assert validate_case(case, schema) == []


def test_base_plate_foundation_confirmation_is_enforced():
    schema, case = _load("base_plates_and_combined_force_strength_case.schema.json", "base_plates_and_combined_force_strength_example.json")
    case["foundation_strength_check_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_base_plate_combined_runner_writes_outputs():
    result = run_case(ROOT / "examples/base_plates_and_combined_force_strength_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_101_required_base_plate_thickness_mm"] > 0.0
    assert result["results"]["equation_105_utilization"] > 0.0
    assert (ROOT / "outputs/base_plates_and_combined_force_strength_result.json").exists()


def test_beam_column_stability_case_validates():
    schema, case = _load("beam_column_stability_case.schema.json", "beam_column_stability_example.json")
    assert validate_case(case, schema) == []


def test_beam_column_stability_confirmations_are_enforced():
    schema, case = _load("beam_column_stability_case.schema.json", "beam_column_stability_example.json")
    case["same_load_combination_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_beam_column_stability_runner_writes_outputs():
    result = run_case(ROOT / "examples/beam_column_stability_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_109_utilization"] > 0.0
    assert result["results"]["equation_120_utilization"] > 0.0
    assert (ROOT / "outputs/beam_column_stability_result.json").exists()


def test_built_up_beam_column_combined_local_case_validates():
    schema, case = _load(
        "built_up_beam_columns_and_combined_local_stability_case.schema.json",
        "built_up_beam_columns_and_combined_local_stability_example.json",
    )
    assert validate_case(case, schema) == []


def test_built_up_beam_column_combined_local_confirmation_is_enforced():
    schema, case = _load(
        "built_up_beam_columns_and_combined_local_stability_case.schema.json",
        "built_up_beam_columns_and_combined_local_stability_example.json",
    )
    case["sections_9_3_and_9_4_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_built_up_beam_column_combined_local_runner_writes_outputs():
    result = run_case(ROOT / "examples/built_up_beam_columns_and_combined_local_stability_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_123_relative_eccentricity_m"] == 2.0
    assert result["results"]["equation_124_additional_branch_force_n"] > 0.0
    assert (ROOT / "outputs/built_up_beam_columns_and_combined_local_stability_result.json").exists()


def test_effective_lengths_case_validates():
    schema, case = _load(
        "effective_lengths_and_limiting_slenderness_case.schema.json",
        "effective_lengths_and_limiting_slenderness_example.json",
    )
    assert validate_case(case, schema) == []


def test_effective_lengths_runner_writes_outputs():
    result = run_case(ROOT / "examples/effective_lengths_and_limiting_slenderness_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_136_truss_in_plane_effective_length_mm"] > 0.0
    assert (ROOT / "outputs/effective_lengths_and_limiting_slenderness_result.json").exists()


def test_effective_length_guided_case_validates():
    schema, case = _load(
        "effective_length_guided_case.schema.json",
        "effective_length_guided_example.json",
    )
    assert validate_case(case, schema) == []


def test_effective_length_guided_runner_writes_outputs():
    result = run_case(ROOT / "examples/effective_length_guided_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["effective_length"]["effective_length_mm"] == 600.0
    assert result["results"]["actual_slenderness"] == 30.0
    assert result["results"]["pass"] is True
    assert (ROOT / "outputs/effective_length_guided_result.json").exists()


def test_sheet_structures_case_validates():
    schema, case = _load(
        "sheet_structures_strength_and_stability_case.schema.json",
        "sheet_structures_strength_and_stability_example.json",
    )
    assert validate_case(case, schema) == []


def test_sheet_structures_runner_writes_outputs():
    result = run_case(ROOT / "examples/sheet_structures_strength_and_stability_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_148_utilization"] > 0.0
    assert result["results"]["equation_164_cone_critical_force_n"] > 0.0
    assert result["results"]["equation_169_utilization"] > 0.0
    assert (ROOT / "outputs/sheet_structures_strength_and_stability_result.json").exists()


def test_fatigue_design_case_validates():
    schema, case = _load("fatigue_design_case.schema.json", "fatigue_design_example.json")
    assert validate_case(case, schema) == []


def test_fatigue_design_confirmations_are_enforced():
    schema, case = _load("fatigue_design_case.schema.json", "fatigue_design_example.json")
    case["annex_k_case_selection_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_fatigue_design_runner_writes_outputs():
    result = run_case(ROOT / "examples/fatigue_design_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_170_utilization"] > 0.0
    assert result["results"]["equation_173_utilization"] > 0.0
    assert (ROOT / "outputs/fatigue_design_result.json").exists()


def test_brittle_fracture_and_welded_connections_case_validates():
    schema, case = _load(
        "brittle_fracture_and_welded_connections_case.schema.json",
        "brittle_fracture_and_welded_connections_example.json",
    )
    assert validate_case(case, schema) == []


def test_brittle_fracture_engineering_classification_is_enforced():
    schema, case = _load(
        "brittle_fracture_and_welded_connections_case.schema.json",
        "brittle_fracture_and_welded_connections_example.json",
    )
    case["engineering_classifications_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_brittle_fracture_and_welded_connections_runner_writes_outputs():
    result = run_case(ROOT / "examples/brittle_fracture_and_welded_connections_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert "equation_174_base_risk_percent" in result["results"]
    assert result["results"]["equation_175_utilization"] > 0.0
    assert result["results"]["spot_weld_equations_184_185"]["governing_capacity_n"] > 0.0
    assert (ROOT / "outputs/brittle_fracture_and_welded_connections_result.json").exists()


def test_bolted_and_friction_case_validates_and_runs():
    schema, case = _load("bolted_and_friction_connections_case.schema.json", "bolted_and_friction_connections_example.json")
    assert validate_case(case, schema) == []
    result = run_case(ROOT / "examples/bolted_and_friction_connections_example.json", ROOT)
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_186_shear_capacity_n"] > 0
    assert result["results"]["equation_192_friction_bolt_count"]["required_bolts"] > 0
    assert (ROOT / "outputs/bolted_and_friction_connections_result.json").exists()

def test_bolted_and_friction_confirmation_is_enforced():
    schema, case = _load("bolted_and_friction_connections_case.schema.json", "bolted_and_friction_connections_example.json")
    case["sections_14_2_and_14_3_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_built_up_beam_flange_connections_case_validates():
    schema, case = _load(
        "built_up_beam_flange_connections_case.schema.json",
        "built_up_beam_flange_connections_example.json",
    )
    assert validate_case(case, schema) == []


def test_built_up_beam_flange_connections_confirmation_is_enforced():
    schema, case = _load(
        "built_up_beam_flange_connections_case.schema.json",
        "built_up_beam_flange_connections_example.json",
    )
    case["clause_14_4_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_built_up_beam_flange_connections_runner_writes_outputs():
    result = run_case(
        ROOT / "examples/built_up_beam_flange_connections_example.json", ROOT
    )
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["flange_shear_flow_t_n_mm"] == 360.0
    assert result["results"]["equation_198_utilization"] > 0.0
    assert (
        ROOT / "outputs/built_up_beam_flange_connections_result.json"
    ).exists()


def test_structural_detailing_and_support_bearings_case_validates():
    schema, case = _load(
        "structural_detailing_and_support_bearings_case.schema.json",
        "structural_detailing_and_support_bearings_example.json",
    )
    assert validate_case(case, schema) == []


def test_structural_detailing_and_support_bearings_confirmation_is_enforced():
    schema, case = _load(
        "structural_detailing_and_support_bearings_case.schema.json",
        "structural_detailing_and_support_bearings_example.json",
    )
    case["section_15_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_structural_detailing_and_support_bearings_runner_writes_outputs():
    result = run_case(
        ROOT / "examples/structural_detailing_and_support_bearings_example.json", ROOT
    )
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["temperature_joint_spacing_assessment"]["table_compliance_pass"] is True
    assert result["results"]["equation_199_cylindrical_hinge"]["equation_199_utilization"] > 0.0
    assert result["results"]["equation_200_roller_bearing"]["equation_200_utilization"] > 0.0
    assert (ROOT / "outputs/structural_detailing_and_support_bearings_result.json").exists()


def test_overhead_line_and_switchyard_supports_case_validates():
    schema, case = _load(
        "overhead_line_and_switchyard_supports_case.schema.json",
        "overhead_line_and_switchyard_supports_example.json",
    )
    assert validate_case(case, schema) == []


def test_overhead_line_and_switchyard_supports_confirmation_is_enforced():
    schema, case = _load(
        "overhead_line_and_switchyard_supports_case.schema.json",
        "overhead_line_and_switchyard_supports_example.json",
    )
    case["section_16_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_overhead_line_and_switchyard_supports_runner_writes_outputs():
    result = run_case(ROOT / "examples/overhead_line_and_switchyard_supports_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_201_maximum_slenderness"] == 12.0
    assert result["results"]["table_46_deformation_check"]["pass"] is True
    assert result["results"]["equations_213_to_214_polygonal_tube_wall"]["equation_213_pass"] is True
    assert (ROOT / "outputs/overhead_line_and_switchyard_supports_result.json").exists()


def test_antenna_structures_case_validates():
    schema, case = _load(
        "antenna_structures_case.schema.json",
        "antenna_structures_example.json",
    )
    assert validate_case(case, schema) == []


def test_antenna_structures_confirmation_is_enforced():
    schema, case = _load(
        "antenna_structures_case.schema.json",
        "antenna_structures_example.json",
    )
    case["section_17_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_antenna_structures_runner_writes_outputs():
    result = run_case(ROOT / "examples/antenna_structures_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_215_minimum_damper_distance_m"] > 0.0
    assert result["results"]["all_executable_section_17_checks_pass"] is True
    assert (ROOT / "outputs/antenna_structures_result.json").exists()


def test_reconstruction_assessment_case_validates():
    schema, case = _load(
        "reconstruction_assessment_case.schema.json",
        "reconstruction_assessment_example.json",
    )
    assert validate_case(case, schema) == []


def test_reconstruction_assessment_confirmation_is_enforced():
    schema, case = _load(
        "reconstruction_assessment_case.schema.json",
        "reconstruction_assessment_example.json",
    )
    case["section_18_applicability_confirmed"] = False
    assert any("must equal True" in error for error in validate_case(case, schema))


def test_reconstruction_assessment_runner_writes_outputs():
    result = run_case(ROOT / "examples/reconstruction_assessment_example.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_216_utilization"] > 0.0
    assert result["results"]["equation_218_stability_utilization"] > 0.0
    assert result["results"]["equation_224_composite_factor_k"] > 0.0
    assert (ROOT / "outputs/reconstruction_assessment_result.json").exists()
