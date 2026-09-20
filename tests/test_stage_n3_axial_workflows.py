from __future__ import annotations

import json
import math
from pathlib import Path
import shutil

import pytest

from standard_core import axial_workflows as aw
from standard_core import built_up_axial_members as bm
from standard_core.axial_members import central_compression_stability_coefficient
from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

ROOT = Path(__file__).resolve().parents[1]


def _isolated_runner_root(tmp_path: Path) -> Path:
    isolated = tmp_path / "runner_root"
    isolated.mkdir()
    shutil.copytree(ROOT / "schemas", isolated / "schemas")
    (isolated / "outputs").mkdir()
    (isolated / "reports").mkdir()
    return isolated


@pytest.mark.parametrize(
    "force_state,ryn,post_yield,expected",
    [
        ("compression", 440.0, False, "yield"),
        ("compression", 440.000001, False, "ultimate"),
        ("tension", 440.0, False, "yield"),
        ("tension", 440.0, True, "ultimate"),
        ("tension", 500.0, False, "ultimate"),
    ],
)
def test_n3_clause_7_1_1_branch_selection_boundaries(force_state, ryn, post_yield, expected):
    result = aw.select_equation_5_resistance_branch(force_state, ryn, post_yield)
    assert result["branch"] == expected


def test_n3_geometric_slenderness_is_effective_length_over_radius():
    assert aw.geometric_slenderness_from_effective_length(4000.0, 40.0) == pytest.approx(100.0)
    with pytest.raises(ValueError):
        aw.geometric_slenderness_from_effective_length(4000.0, 0.0)


def test_n3_gamma_res_245_endpoint_and_boundary():
    assert aw.residual_stress_factor_gamma_res(3.0, 245.0)["gamma_res"] == pytest.approx(1.0)
    assert aw.residual_stress_factor_gamma_res(3.000001, 245.0)["gamma_res"] == pytest.approx(1.0000001)
    assert aw.residual_stress_factor_gamma_res(4.0, 200.0)["gamma_res"] == pytest.approx(1.1)


def test_n3_gamma_res_390_endpoint_literal_current_source_rule():
    assert aw.residual_stress_factor_gamma_res(5.0, 390.0)["gamma_res"] == pytest.approx(1.0)
    assert aw.residual_stress_factor_gamma_res(5.000001, 390.0)["gamma_res"] == pytest.approx(1.9000002)
    assert aw.residual_stress_factor_gamma_res(6.0, 500.0)["gamma_res"] == pytest.approx(2.1)


def test_n3_gamma_res_interpolates_in_Ry_between_endpoint_rules():
    ry = 300.0
    lam = 4.0
    low = 1.1
    high = 1.0
    f = (ry - 245.0) / (390.0 - 245.0)
    expected = low + f * (high - low)
    assert aw.residual_stress_factor_gamma_res(lam, ry)["gamma_res"] == pytest.approx(expected)


def test_n3_eq7a_uses_gamma_res_in_denominator():
    u = aw.central_compression_stability_utilization_eq7a(100000.0, 1000.0, 250.0, 1.0, 0.8, 1.25)
    assert u == pytest.approx(100000.0 / (1.25 * 0.8 * 1000.0 * 250.0))


def test_n3_tension_workflow_does_not_run_compression_or_single_angle_unless_requested():
    result = aw.solid_axial_member_workflow(
        force_state="tension", axial_force_n=100000.0, gross_area_mm2=1000.0, net_area_mm2=900.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, post_yield_service_possible=False, elastic_modulus_n_mm2=206000.0,
    )
    assert result["equation_5"]["resistance_branch"]["branch"] == "yield"
    assert result["compression_stability"]["status"] == "not_applicable_for_tension"
    assert result["equation_6_single_angle"]["status"] == "not_applicable"


def test_n3_tension_post_yield_uses_ultimate_branch():
    result = aw.solid_axial_member_workflow(
        force_state="tension", axial_force_n=100000.0, gross_area_mm2=1000.0, net_area_mm2=900.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, post_yield_service_possible=True, elastic_modulus_n_mm2=206000.0,
    )
    assert result["equation_5"]["resistance_branch"]["branch"] == "ultimate"


def test_n3_compression_requires_local_stability_prerequisite():
    with pytest.raises(ValueError, match="7.3.2-7.3.9"):
        aw.solid_axial_member_workflow(
            force_state="compression", axial_force_n=100000.0, gross_area_mm2=1000.0, net_area_mm2=1000.0,
            normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
            design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
            working_condition_factor=1.0, post_yield_service_possible=False, elastic_modulus_n_mm2=206000.0,
            effective_length_mm=3000.0, radius_of_gyration_mm=30.0, section_type="b",
            stability_formula="equation_7", local_stability_prerequisites_satisfied=False,
        )


def test_n3_compression_eq7_workflow_derives_lambda_and_phi():
    result = aw.solid_axial_member_workflow(
        force_state="compression", axial_force_n=100000.0, gross_area_mm2=1000.0, net_area_mm2=1000.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, post_yield_service_possible=False, elastic_modulus_n_mm2=206000.0,
        effective_length_mm=3000.0, radius_of_gyration_mm=30.0, section_type="b",
        stability_formula="equation_7", local_stability_prerequisites_satisfied=True,
    )
    st = result["compression_stability"]
    assert st["geometric_slenderness"] == pytest.approx(100.0)
    expected_lb = 100.0 * math.sqrt(345.0 / 206000.0)
    assert st["relative_slenderness"] == pytest.approx(expected_lb)
    assert st["phi"] == pytest.approx(central_compression_stability_coefficient(expected_lb, "b"))
    assert st["equation_7a"] is None


def test_n3_eq7a_requires_rolled_i_confirmation():
    with pytest.raises(ValueError, match="rolled I-section"):
        aw.solid_axial_member_workflow(
            force_state="compression", axial_force_n=100000.0, gross_area_mm2=1000.0, net_area_mm2=1000.0,
            normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
            design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
            working_condition_factor=1.0, post_yield_service_possible=False, elastic_modulus_n_mm2=206000.0,
            effective_length_mm=3000.0, radius_of_gyration_mm=30.0, section_type="b",
            stability_formula="equation_7a_rolled_i", local_stability_prerequisites_satisfied=True,
            rolled_i_section_confirmed=False,
        )


def test_n3_single_angle_route_is_optional_and_branch_safe():
    result = aw.solid_axial_member_workflow(
        force_state="tension", axial_force_n=50000.0, gross_area_mm2=500.0, net_area_mm2=450.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, post_yield_service_possible=False, elastic_modulus_n_mm2=206000.0,
        single_angle_clause_7_1_2={
            "applicability_confirmed": True,
            "table_6_geometry_case_confirmed": True,
            "table_6_case": "multi_bolt_3",
            "attached_leg_net_strip_area_mm2": 100.0,
            "special_ten_percent_reduction_applies": False,
        },
    )
    assert result["equation_6_single_angle"]["status"] == "applicable_and_evaluated"
    assert result["equation_6_single_angle"]["utilization"] > 0.0


@pytest.mark.parametrize(
    "stype,system,expected_eq",
    [(1,"battens",12),(2,"battens",13),(3,"battens",14),(1,"lattice",15),(2,"lattice",16),(3,"lattice",17)],
)
def test_n3_selected_table8_dispatches_only_requested_formula(stype, system, expected_eq):
    data = {
        "whole_member_slenderness_y": 45.0, "whole_member_max_slenderness": 50.0,
        "branch_slenderness_1": 20.0, "branch_slenderness_2": 22.0, "branch_slenderness_3": 18.0,
        "branch_inertia_axis_1_mm4": 2_000_000.0, "branch_inertia_axis_2_mm4": 2_200_000.0, "branch_inertia_axis_3_mm4": 1_800_000.0,
        "branch_axis_spacing_b_mm": 400.0, "branch_axis_spacing_b1_mm": 350.0, "branch_axis_spacing_b2_mm": 450.0,
        "batten_inertia_mm4": 8_000_000.0, "batten_inertia_plane_1_mm4": 8_000_000.0, "batten_inertia_plane_2_mm4": 8_500_000.0,
        "batten_pitch_mm": 1000.0, "panel_length_mm": 1000.0,
        "total_area_mm2": 5000.0, "diagonal_area_plane_1_mm2": 500.0, "diagonal_area_plane_2_mm2": 550.0,
        "diagonal_area_one_face_mm2": 500.0, "diagonal_length_d_mm": 600.0, "diagonal_length_d1_mm": 600.0, "diagonal_length_d2_mm": 650.0,
    }
    result = aw.selected_table8_effective_slenderness(stype, system, data)
    assert result["equation"] == expected_eq
    assert result["effective_slenderness"] > 0.0
    assert set(result) == {"section_type","connector_system","equation","effective_slenderness","source_table"}


def test_n3_built_up_panel_count_5_battens_fail_closed_to_frame_analysis():
    result = aw.built_up_axial_member_workflow(
        force_state="compression", axial_force_n=100000.0, total_net_area_mm2=1000.0, gross_area_mm2=1000.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, elastic_modulus_n_mm2=206000.0, post_yield_service_possible=False,
        panel_count=5, connector_system="battens",
    )
    assert result["clause_7_2_2_to_7_2_5_stability"]["status"] == "external_frame_analysis_required"


def test_n3_built_up_panel_count_5_lattice_does_not_invent_table8_lambda():
    result = aw.built_up_axial_member_workflow(
        force_state="compression", axial_force_n=100000.0, total_net_area_mm2=1000.0, gross_area_mm2=1000.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=345.0,
        design_ultimate_resistance_n_mm2=460.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, elastic_modulus_n_mm2=206000.0, post_yield_service_possible=False,
        panel_count=5, connector_system="lattice",
    )
    st = result["clause_7_2_2_to_7_2_5_stability"]
    assert st["status"] == "clause_7_2_5_route_requires_external_effective_member_slenderness"
    assert st["equation_7"] is None


def test_n3_built_up_table8_type1_lattice_and_connector_forces():
    result = aw.built_up_axial_member_workflow(
        force_state="compression", axial_force_n=800000.0, total_net_area_mm2=5000.0, gross_area_mm2=5000.0,
        normative_yield_resistance_n_mm2=355.0, design_yield_resistance_n_mm2=350.0,
        design_ultimate_resistance_n_mm2=480.0, ultimate_resistance_safety_factor=1.3,
        working_condition_factor=1.0, elastic_modulus_n_mm2=206000.0, post_yield_service_possible=False,
        panel_count=8, connector_system="lattice", built_up_section_type=1,
        table8_data={"whole_member_slenderness_y":45.0,"diagonal_area_plane_1_mm2":500.0,"diagonal_length_d_mm":600.0,"branch_axis_spacing_b_mm":400.0,"panel_length_mm":1000.0},
        branch_relative_slenderness=3.0, branch_section_type="b",
        connector_force_check={"distribution_mode":"connectors_only","connector_system_count":2,"diagonal_length_d_mm":600.0,"branch_axis_spacing_b_mm":400.0,"lattice_force_coefficient_alpha_1":0.5},
    )
    st = result["clause_7_2_2_to_7_2_5_stability"]
    assert st["table_8_selected_route"]["equation"] == 15
    assert st["equation_7_with_7_2_5_if_needed"]["utilization"] > 0.0
    conn = result["clause_7_2_7_to_7_2_10_connectors"]
    assert conn["equation_18_Qfic_n"] > 0.0
    assert conn["equation_21_Nd_n"] > 0.0


def test_n3_close_contact_exact_boundaries_are_accepted():
    assert bm.close_contact_connection_spacing_check(400.0, 10.0, "compression", 2)["pass"] is True
    assert bm.close_contact_connection_spacing_check(800.0, 10.0, "tension", 0)["pass"] is True
    assert bm.close_contact_connection_spacing_check(400.0001, 10.0, "compression", 2)["pass"] is False


def test_n3_lattice_branch_boundaries_2_7_3_2_4_1():
    assert bm.lattice_branch_stability_coefficient(2.7, "b") == pytest.approx(1.0)
    assert bm.lattice_branch_stability_coefficient(3.2, "b") < 1.0
    assert bm.lattice_branch_slenderness_assessment(4.1, 2.0, True)["permitted"] is True
    assert bm.lattice_branch_slenderness_assessment(4.100001, 5.0, True)["permitted"] is False


def test_n3_guided_schemas_validate_examples_after_reference_hydration_via_runner(tmp_path):
    isolated = _isolated_runner_root(tmp_path)
    solid = run_case(ROOT / "examples/axial_member_guided_example.json", isolated)
    assert solid["results"]["compression_stability"]["selected_formula"] == "both"
    assert solid["inputs"]["section_type"] == "b"
    assert solid["inputs"]["rolled_i_section_confirmed"] is True
    assert solid["inputs"]["net_area_mm2"] == pytest.approx(solid["inputs"]["gross_area_mm2"])
    assert solid["resolution_trace"]["material"]["selected_design_resistance_source"] == "annex_tabulated"
    assert solid["resolution_trace"]["profile"]["original_gost_audit_complete"] is False

    built = run_case(ROOT / "examples/built_up_axial_member_guided_example.json", isolated)
    assert built["results"]["clause_7_2_2_to_7_2_5_stability"]["table_8_selected_route"]["equation"] == 15
    assert built["inputs"]["total_net_area_mm2"] == pytest.approx(built["inputs"]["gross_area_mm2"])


def test_n3_schema_files_are_valid_for_fully_hydrated_minimal_cases():
    for schema_name, example_name in [
        ("axial_member_guided_case.schema.json", "axial_member_guided_example.json"),
        ("built_up_axial_member_guided_case.schema.json", "built_up_axial_member_guided_example.json"),
    ]:
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
        assert schema["properties"]["action"]["const"] in {"axial_member_guided","built_up_axial_member_guided"}
