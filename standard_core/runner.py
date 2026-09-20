"""User-facing runners for the v0.9 package examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import built_up_axial_members as bm
from . import axial_workflows as axw
from . import bending_workflows as bdw
from . import beam_column_workflows as bcw
from . import built_up_beam_column_workflows as n6w
from . import effective_length_workflows as n7w
from . import sheet_structure_workflows as n8w
from . import fatigue_workflows as n9w
from . import brittle_fracture_workflows as n10w
from . import fire_sp554_bridge as fire_bridge
from . import fire_sp554_runtime as fire_runtime
from . import fire_sp554_thermal as fire_thermal
from . import fire_sp554_assessment as fire_assessment
from . import local_stability as ls
from . import bending_members as bend
from . import crane_runway_and_bending_stability as stab
from . import bending_member_local_stability as bls
from . import base_plates_and_combined_force_strength as bc
from . import beam_column_stability as beamcol
from . import built_up_beam_columns_and_combined_local_stability as v11
from . import effective_lengths_and_limiting_slenderness as v12
from . import sheet_structures_strength_and_stability as v13
from . import fatigue_design as v14
from . import brittle_fracture_and_welded_connections as v15
from . import bolted_and_friction_connections as v16
from . import built_up_beam_flange_connections as v17
from . import structural_detailing_and_support_bearings as v18
from . import overhead_line_and_switchyard_supports as v19
from . import antenna_structures as v20
from . import reconstruction_assessment as v21
from .axial_members import (
    annex_d1_stability_coefficient,
    axial_strength_utilization_ultimate,
    axial_strength_utilization_yield,
    central_compression_stability_coefficient,
    central_compression_stability_utilization,
    relative_slenderness,
    single_angle_connection_strength_utilization,
    single_angle_working_condition_factor,
    table_6_angle_coefficients,
)
from .material_resistance import (
    bolt_shear_design_resistance_n_mm2,
    bolt_tension_design_resistance_n_mm2,
    butt_weld_design_shear_resistance_n_mm2,
    butt_weld_design_ultimate_resistance_with_ndt_n_mm2,
    butt_weld_design_yield_resistance_with_ndt_n_mm2,
    butt_weld_design_yield_resistance_without_ndt_n_mm2,
    connected_element_bearing_design_resistance_n_mm2,
    design_end_bearing_resistance_n_mm2,
    design_pin_local_bearing_resistance_n_mm2,
    design_roller_diametral_compression_resistance_n_mm2,
    design_shear_resistance_n_mm2,
    design_ultimate_resistance_n_mm2,
    design_yield_resistance_n_mm2,
    fillet_weld_fusion_boundary_design_shear_resistance_n_mm2,
    fillet_weld_metal_design_shear_resistance_n_mm2,
    foundation_anchor_bolt_tension_design_resistance_n_mm2,
    high_strength_wire_tension_design_resistance_n_mm2,
    material_safety_factor,
    steel_rope_design_tension_force_n,
    u_bolt_tension_design_resistance_n_mm2,
    weld_metal_safety_factor,
    SteelMaterialStrengthResolver,
)
from .schema_validation import validate_case
from .release_metadata import RELEASE_STAGE
from .profile_catalog import InterimProfileCatalog, hydrate_case_with_profile


def _schema_name_for_action(action: str) -> str:
    mapping = {
        "profile_catalog_resolve": "profile_catalog_case.schema.json",
        "material_resistance_bundle": "minimal_case.schema.json",
        "axial_member_strength_and_stability": "axial_member_case.schema.json",
        "axial_member_guided": "axial_member_guided_case.schema.json",
        "built_up_axial_members": "built_up_axial_member_case.schema.json",
        "built_up_axial_member_guided": "built_up_axial_member_guided_case.schema.json",
        "centrally_compressed_local_stability": "local_stability_case.schema.json",
        "bending_member_strength": "bending_member_case.schema.json",
        "bending_member_guided": "bending_member_guided_case.schema.json",
        "beam_column_guided": "beam_column_guided_case.schema.json",
        "built_up_beam_column_guided": "built_up_beam_column_guided_case.schema.json",
        "crane_runway_and_bending_stability": "crane_runway_and_bending_stability_case.schema.json",
        "bending_member_local_stability": "bending_member_local_stability_case.schema.json",
        "base_plates_and_combined_force_strength": "base_plates_and_combined_force_strength_case.schema.json",
        "beam_column_stability": "beam_column_stability_case.schema.json",
        "built_up_beam_columns_and_combined_local_stability": "built_up_beam_columns_and_combined_local_stability_case.schema.json",
        "effective_lengths_and_limiting_slenderness": "effective_lengths_and_limiting_slenderness_case.schema.json",
        "effective_length_guided": "effective_length_guided_case.schema.json",
        "sheet_structures_strength_and_stability": "sheet_structures_strength_and_stability_case.schema.json",
        "sheet_structure_guided": "sheet_structure_guided_case.schema.json",
        "fatigue_design": "fatigue_design_case.schema.json",
        "fatigue_guided": "fatigue_guided_case.schema.json",
        "brittle_fracture_guided": "brittle_fracture_guided_case.schema.json",
        "sp554_sp16_fire_dependency_bridge": "sp554_sp16_fire_dependency_bridge_case.schema.json",
        "sp554_fire_mechanical_guided": "sp554_fire_mechanical_guided_case.schema.json",
        "sp554_fire_thermal_guided": "sp554_fire_thermal_guided_case.schema.json",
        "sp554_fire_result_assessment": "sp554_fire_result_assessment_case.schema.json",
        "brittle_fracture_and_welded_connections": "brittle_fracture_and_welded_connections_case.schema.json",
        "bolted_and_friction_connections": "bolted_and_friction_connections_case.schema.json",
        "built_up_beam_flange_connections": "built_up_beam_flange_connections_case.schema.json",
        "structural_detailing_and_support_bearings": "structural_detailing_and_support_bearings_case.schema.json",
        "overhead_line_and_switchyard_supports": "overhead_line_and_switchyard_supports_case.schema.json",
        "antenna_structures": "antenna_structures_case.schema.json",
        "reconstruction_assessment": "reconstruction_assessment_case.schema.json",
    }
    try:
        return mapping[action]
    except KeyError as exc:
        raise ValueError(f"Unsupported action: {action}") from exc


def _write_case_report(root: Path, stem: str, result: dict[str, Any], title: str) -> None:
    (root / "outputs").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "outputs" / f"{stem}_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "reports" / f"{stem}_case_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [f"# {title}", "", f"- Case ID: `{result['case_id']}`", f"- Release: `{result['release_stage']}`", ""]
    lines.extend(["## Results", ""])
    for key, value in result["results"].items():
        if isinstance(value, float):
            lines.append(f"- `{key}`: {value:.12g}")
        else:
            lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Scope limitation", "", result["scope_note"]])
    (root / "reports" / f"{stem}_case_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_sp554_sp16_fire_dependency_bridge_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    bridge = fire_bridge._bridge_workflow(root, bool(case_data["require_connection_scope"]))
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": False,
        "inputs": case_data,
        "results": bridge,
        "scope_note": (
            "FIRE-D1 is a dependency-closure audit for SP554 Sections 8-11 member mechanics. "
            "It does not execute the fire-side temperature-reduction equations, Appendix B critical-temperature inversion, "
            "connection fire resistance, or thermal Section 12."
        ),
    }
    _write_case_report(root, "sp554_sp16_fire_dependency_bridge", result, "FIRE-D1 SP554-SP16 member mechanical dependency bridge")
    return result


def _run_sp554_fire_mechanical_guided_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    fire_result = fire_runtime.sp554_fire_mechanical_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": fire_result,
        "scope_note": (
            "FIRE-D2 executes SP554 Sections 8-11 member fire mechanics and Appendix-B critical-temperature inversion. "
            "It uses normative-strength FIRE-D1 handoffs and does not solve SP554 Section 12 heat transfer or connection fire resistance."
        ),
    }
    _write_case_report(root, "sp554_fire_mechanical_guided", result, "FIRE-D2 SP554 member critical-temperature calculation")
    return result


def _run_sp554_fire_thermal_guided_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    thermal_result = fire_thermal.sp554_fire_thermal_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": thermal_result,
        "scope_note": (
            "FIRE-D3 executes SP554 Section 12 thermal time-to-critical-temperature routes over the frozen FIRE-D2 critical-temperature handoff. "
            "Unprotected 12.2 and documented protected-matrix 12.10 routes are executable. The 12.5 FDM route is executable for dry W=0 protection only and is subject to the mandatory 12.6 validation gate; W>0 remains fail-closed because the source does not define an unambiguous phase-change activation algorithm."
        ),
    }
    _write_case_report(root, "sp554_fire_thermal_guided", result, "FIRE-D3 SP554 Section 12 thermal fire-resistance calculation")
    return result



def _run_sp554_fire_result_assessment_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    assessment_result = fire_assessment.sp554_fire_result_assessment_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": assessment_result,
        "scope_note": (
            "FIRE-D4 executes SP554 Section 13 result assessment over the frozen FIRE-D3 thermal producer. "
            "The required fire-resistance time is an explicit external normative/project input with mandatory provenance; "
            "FIRE-D4 does not infer building fire-resistance requirements. Section 13.3 R notation uses the exact calculated time without class rounding. "
            "Alternative/real fire regimes remain fail-closed pending FIRE-D7."
        ),
    }
    _write_case_report(root, "sp554_fire_result_assessment", result, "FIRE-D4 SP554 Section 13 result assessment")
    return result

def _run_profile_catalog_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    catalog = InterimProfileCatalog()
    bundle = catalog.resolve_for_axis(
        int(case_data["family_id"]),
        str(case_data["designation"]),
        str(case_data["axis"]),
        source_row_id=case_data.get("source_row_id"),
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": bundle,
        "scope_note": (
            "Stage N2 interim profile resolution. Imported catalog rows are runtime-enabled but remain "
            "PENDING_ORIGINAL_GOST_AUDIT. Mass, radii, Table 7 coefficients and supported torsion quantities "
            "are recomputed; known corrupt NormCAD mass/afw/It fields are not used as runtime truth."
        ),
    }
    _write_case_report(root, "profile_catalog", result, "Stage N2 profile-catalog resolution")
    return result


def _run_material_resistance_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    gamma_m = material_safety_factor(case_data["material_control_category"])
    ryn = float(case_data["normative_yield_resistance_n_mm2"])
    run = float(case_data["normative_ultimate_resistance_n_mm2"])
    rwun = float(case_data["normative_weld_metal_ultimate_resistance_n_mm2"])
    rbun = float(case_data["normative_bolt_ultimate_resistance_n_mm2"])
    ry = design_yield_resistance_n_mm2(ryn, gamma_m)
    ru = design_ultimate_resistance_n_mm2(run, gamma_m)
    rs = design_shear_resistance_n_mm2(ryn, gamma_m)
    gamma_wm = weld_metal_safety_factor(rwun)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "material_safety_factor": gamma_m,
            "design_yield_resistance_n_mm2": ry,
            "design_ultimate_resistance_n_mm2": ru,
            "design_shear_resistance_n_mm2": rs,
            "design_end_bearing_resistance_n_mm2": design_end_bearing_resistance_n_mm2(run, gamma_m),
            "design_pin_local_bearing_resistance_n_mm2": design_pin_local_bearing_resistance_n_mm2(run, gamma_m),
            "design_roller_diametral_compression_resistance_n_mm2": design_roller_diametral_compression_resistance_n_mm2(run, gamma_m),
            "butt_weld_yield_with_ndt_n_mm2": butt_weld_design_yield_resistance_with_ndt_n_mm2(ry),
            "butt_weld_ultimate_with_ndt_n_mm2": butt_weld_design_ultimate_resistance_with_ndt_n_mm2(ru),
            "butt_weld_yield_without_ndt_n_mm2": butt_weld_design_yield_resistance_without_ndt_n_mm2(ry),
            "butt_weld_shear_n_mm2": butt_weld_design_shear_resistance_n_mm2(rs),
            "weld_metal_safety_factor": gamma_wm,
            "fillet_weld_metal_design_shear_resistance_n_mm2": fillet_weld_metal_design_shear_resistance_n_mm2(rwun, gamma_wm),
            "fillet_weld_fusion_boundary_design_shear_resistance_n_mm2": fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(run),
            "bolt_shear_design_resistance_n_mm2": bolt_shear_design_resistance_n_mm2(rbun, case_data["bolt_strength_class"]),
            "bolt_tension_design_resistance_n_mm2": bolt_tension_design_resistance_n_mm2(rbun, case_data["bolt_strength_class"]),
            "connected_element_bearing_design_resistance_n_mm2": connected_element_bearing_design_resistance_n_mm2(
                ru, case_data["bolt_hole_accuracy_class"], float(case_data["connected_steel_yield_strength_n_mm2"])
            ),
            "foundation_anchor_bolt_tension_design_resistance_n_mm2": foundation_anchor_bolt_tension_design_resistance_n_mm2(ryn),
            "u_bolt_tension_design_resistance_n_mm2": u_bolt_tension_design_resistance_n_mm2(ryn),
            "high_strength_wire_tension_design_resistance_n_mm2": high_strength_wire_tension_design_resistance_n_mm2(run),
            "steel_rope_design_tension_force_n": steel_rope_design_tension_force_n(float(case_data["rope_breaking_force_n"])),
        },
        "scope_note": "Selected Section 6 material/connection resistance formulas only; full member and joint design remains outside this action.",
    }
    _write_case_report(root, "material_resistance", result, "Material-resistance case")
    return result


def _run_axial_member_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    force = float(case_data["axial_force_n"])
    net_area = float(case_data["net_area_mm2"])
    gross_area = float(case_data["gross_area_mm2"])
    ry = float(case_data["design_yield_resistance_n_mm2"])
    ru = float(case_data["design_ultimate_resistance_n_mm2"])
    gamma_u = float(case_data["ultimate_resistance_safety_factor"])
    gamma_c = float(case_data["working_condition_factor"])
    branch = case_data["equation_5_resistance_branch"]
    if branch == "yield":
        equation_5 = axial_strength_utilization_yield(force, net_area, ry, gamma_c)
    else:
        equation_5 = axial_strength_utilization_ultimate(force, net_area, ru, gamma_u, gamma_c)

    lambda_bar = relative_slenderness(
        float(case_data["geometric_slenderness"]), ry, float(case_data["elastic_modulus_n_mm2"])
    )
    phi = central_compression_stability_coefficient(lambda_bar, case_data["section_type"])
    equation_7 = central_compression_stability_utilization(force, gross_area, ry, gamma_c, phi)

    alpha1, alpha2, beta = table_6_angle_coefficients(case_data["angle_table_6_case"])
    gamma_c1 = single_angle_working_condition_factor(
        net_area,
        float(case_data["angle_attached_leg_net_strip_area_mm2"]),
        alpha1,
        alpha2,
        beta,
        case_data["special_ten_percent_reduction_applies"],
    )
    equation_6 = single_angle_connection_strength_utilization(force, net_area, ru, gamma_u, gamma_c1)

    try:
        table_d1_phi: float | None = annex_d1_stability_coefficient(lambda_bar, case_data["section_type"])
        table_d1_status = "exact_node_available"
    except ValueError:
        table_d1_phi = None
        table_d1_status = "not_an_exact_table_node_no_interpolation_applied"

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "equation_5_resistance_branch": branch,
            "equation_5_strength_utilization": equation_5,
            "equation_5_pass": equation_5 <= 1.0,
            "relative_slenderness": lambda_bar,
            "section_type": case_data["section_type"],
            "stability_coefficient_phi": phi,
            "table_d1_phi": table_d1_phi,
            "table_d1_lookup_status": table_d1_status,
            "equation_7_stability_utilization": equation_7,
            "equation_7_pass": equation_7 <= 1.0,
            "table_6_alpha1": alpha1,
            "table_6_alpha2": alpha2,
            "table_6_beta": beta,
            "single_angle_working_condition_factor_gamma_c1": gamma_c1,
            "equation_6_single_angle_utilization": equation_6,
            "equation_6_pass": equation_6 <= 1.0,
        },
        "scope_note": "LEGACY multi-check diagnostic retained for backward compatibility. It evaluates equation (5), compression stability and the special single-angle branch together and is NOT the Stage N3 qualified applicability-safe workflow. Use action axial_member_guided for normative branch selection.",
    }
    _write_case_report(root, "axial_member", result, "Axial-member strength and stability case")
    return result




def _run_axial_member_guided_case(
    case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any] | None = None
) -> dict[str, Any]:
    workflow = axw.solid_axial_member_workflow(
        force_state=case_data["force_state"],
        axial_force_n=float(case_data["axial_force_n"]),
        gross_area_mm2=float(case_data["gross_area_mm2"]),
        net_area_mm2=float(case_data["net_area_mm2"]),
        normative_yield_resistance_n_mm2=float(case_data["normative_yield_resistance_n_mm2"]),
        design_yield_resistance_n_mm2=float(case_data["design_yield_resistance_n_mm2"]),
        design_ultimate_resistance_n_mm2=float(case_data["design_ultimate_resistance_n_mm2"]),
        ultimate_resistance_safety_factor=float(case_data["ultimate_resistance_safety_factor"]),
        working_condition_factor=float(case_data["working_condition_factor"]),
        post_yield_service_possible=bool(case_data["post_yield_service_possible"]),
        elastic_modulus_n_mm2=float(case_data["elastic_modulus_n_mm2"]),
        effective_length_mm=case_data.get("effective_length_mm"),
        radius_of_gyration_mm=case_data.get("radius_of_gyration_mm"),
        section_type=case_data.get("section_type"),
        local_stability_prerequisites_satisfied=case_data.get("local_stability_prerequisites_satisfied"),
        stability_formula=case_data.get("stability_formula"),
        rolled_i_section_confirmed=bool(case_data["rolled_i_section_confirmed"]) if "rolled_i_section_confirmed" in case_data else False,
        single_angle_clause_7_1_2=case_data.get("single_angle_clause_7_1_2"),
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "resolution_trace": resolution_trace or {},
        "results": workflow,
        "scope_note": (
            "Stage N3 guided clauses 7.1.1-7.1.3. Branch selection is normative and only applicable "
            "checks are evaluated. Compression stability requires explicit 7.3.2-7.3.9 prerequisite confirmation. "
            "The optional rolled-I equation (7a) route is current-СП16 source-backed."
        ),
    }
    _write_case_report(root, "axial_member_guided", result, "Stage N3 guided solid axial-member case")
    return result


def _run_built_up_axial_member_guided_case(
    case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any] | None = None
) -> dict[str, Any]:
    workflow = axw.built_up_axial_member_workflow(
        force_state=case_data["force_state"],
        axial_force_n=float(case_data["axial_force_n"]),
        total_net_area_mm2=float(case_data["total_net_area_mm2"]),
        gross_area_mm2=float(case_data["gross_area_mm2"]),
        normative_yield_resistance_n_mm2=float(case_data["normative_yield_resistance_n_mm2"]),
        design_yield_resistance_n_mm2=float(case_data["design_yield_resistance_n_mm2"]),
        design_ultimate_resistance_n_mm2=float(case_data["design_ultimate_resistance_n_mm2"]),
        ultimate_resistance_safety_factor=float(case_data["ultimate_resistance_safety_factor"]),
        working_condition_factor=float(case_data["working_condition_factor"]),
        elastic_modulus_n_mm2=float(case_data["elastic_modulus_n_mm2"]),
        post_yield_service_possible=bool(case_data["post_yield_service_possible"]),
        panel_count=case_data.get("panel_count"),
        connector_system=case_data.get("connector_system"),
        built_up_section_type=case_data.get("built_up_section_type"),
        table8_data=case_data.get("table8_data"),
        branch_relative_slenderness=case_data.get("branch_relative_slenderness"),
        branch_section_type=case_data.get("branch_section_type"),
        close_contact_check=case_data.get("close_contact_check"),
        connector_force_check=case_data.get("connector_force_check"),
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "resolution_trace": resolution_trace or {},
        "results": workflow,
        "scope_note": (
            "Stage N3 guided clauses 7.2.1-7.2.10. Only the selected Table 8 branch is evaluated. "
            "For fewer than six panels, Table 8 is not used; required external frame/effective-slenderness routes "
            "remain fail-closed rather than being invented."
        ),
    }
    _write_case_report(root, "built_up_axial_member_guided", result, "Stage N3 guided built-up axial-member case")
    return result


def _run_built_up_axial_member_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    force = float(case_data["axial_force_n"])
    gross_area = float(case_data["gross_area_mm2"])
    net_area = float(case_data["total_net_area_mm2"])
    ry = float(case_data["design_yield_resistance_n_mm2"])
    ru = float(case_data["design_ultimate_resistance_n_mm2"])
    gamma_u = float(case_data["ultimate_resistance_safety_factor"])
    gamma_c = float(case_data["working_condition_factor"])
    elastic = float(case_data["elastic_modulus_n_mm2"])

    strength = bm.built_up_axial_strength_utilization(
        force,
        net_area,
        case_data["equation_5_resistance_branch"],
        ry,
        ru,
        gamma_u,
        gamma_c,
    )
    method = bm.built_up_stability_method(int(case_data["panel_count"]), case_data["connector_system"])

    eq12 = bm.battened_effective_slenderness_type_1(
        float(case_data["whole_member_slenderness_y"]),
        float(case_data["branch_slenderness_1"]),
        float(case_data["branch_inertia_axis_1_mm4"]),
        float(case_data["branch_axis_spacing_b_mm"]),
        float(case_data["batten_inertia_mm4"]),
        float(case_data["batten_pitch_mm"]),
    )
    eq13 = bm.battened_effective_slenderness_type_2(
        float(case_data["whole_member_max_slenderness"]),
        float(case_data["branch_slenderness_1"]),
        float(case_data["branch_slenderness_2"]),
        float(case_data["branch_inertia_axis_1_mm4"]),
        float(case_data["branch_inertia_axis_2_mm4"]),
        float(case_data["branch_axis_spacing_b1_mm"]),
        float(case_data["branch_axis_spacing_b2_mm"]),
        float(case_data["batten_inertia_plane_1_mm4"]),
        float(case_data["batten_inertia_plane_2_mm4"]),
        float(case_data["batten_pitch_mm"]),
    )
    eq14 = bm.battened_effective_slenderness_type_3(
        float(case_data["whole_member_max_slenderness"]),
        float(case_data["branch_slenderness_3"]),
        float(case_data["branch_inertia_axis_3_mm4"]),
        float(case_data["branch_axis_spacing_b_mm"]),
        float(case_data["batten_inertia_mm4"]),
        float(case_data["batten_pitch_mm"]),
    )
    eq15 = bm.lattice_effective_slenderness_type_1(
        float(case_data["whole_member_slenderness_y"]),
        gross_area,
        float(case_data["diagonal_area_plane_1_mm2"]),
        float(case_data["diagonal_length_d_mm"]),
        float(case_data["branch_axis_spacing_b_mm"]),
        float(case_data["panel_length_mm"]),
    )
    eq16 = bm.lattice_effective_slenderness_type_2(
        float(case_data["whole_member_max_slenderness"]),
        gross_area,
        float(case_data["diagonal_area_plane_1_mm2"]),
        float(case_data["diagonal_area_plane_2_mm2"]),
        float(case_data["diagonal_length_d1_mm"]),
        float(case_data["diagonal_length_d2_mm"]),
        float(case_data["branch_axis_spacing_b1_mm"]),
        float(case_data["branch_axis_spacing_b2_mm"]),
        float(case_data["panel_length_mm"]),
    )
    eq17 = bm.lattice_effective_slenderness_type_3(
        float(case_data["whole_member_max_slenderness"]),
        gross_area,
        float(case_data["diagonal_area_one_face_mm2"]),
        float(case_data["diagonal_length_d_mm"]),
        float(case_data["branch_axis_spacing_b_mm"]),
        float(case_data["panel_length_mm"]),
    )

    effective_relative_slenderness = relative_slenderness(eq15, ry, elastic)
    branch_relative = float(case_data["lattice_branch_relative_slenderness"])
    branch_assessment = bm.lattice_branch_slenderness_assessment(
        branch_relative,
        effective_relative_slenderness,
        bool(case_data["clause_7_2_5_check_performed"]),
    )
    stability = bm.lattice_built_up_stability_utilization(
        force,
        gross_area,
        ry,
        gamma_c,
        effective_relative_slenderness,
        branch_relative,
        case_data["branch_section_type"],
    )
    batten_branch = bm.batten_branch_slenderness_check(float(case_data["batten_branch_relative_slenderness"]))
    spacing = bm.close_contact_connection_spacing_check(
        float(case_data["connection_spacing_mm"]),
        float(case_data["selected_radius_of_gyration_mm"]),
        case_data["close_contact_force_state"],
        int(case_data["intermediate_connection_count"]),
    )

    q_fic = bm.fictitious_shear_force_n(
        force,
        elastic,
        ry,
        stability["overall_stability_coefficient_phi"],
    )
    distribution = bm.distribute_fictitious_shear(
        q_fic,
        case_data["fictitious_shear_distribution_mode"],
        int(case_data["connector_system_count"]),
    )
    q_s = float(distribution["per_connector_system_force_n"])
    eq19 = bm.batten_shear_force_n(q_s, float(case_data["batten_pitch_mm"]), float(case_data["branch_axis_spacing_b_mm"]))
    eq20 = bm.batten_bending_moment_n_mm(q_s, float(case_data["batten_pitch_mm"]))
    eq21 = bm.lattice_diagonal_force_n(
        q_s,
        float(case_data["diagonal_length_d_mm"]),
        float(case_data["branch_axis_spacing_b_mm"]),
        float(case_data["lattice_force_coefficient_alpha_1"]),
    )
    alpha2 = bm.cross_lattice_alpha_2(
        float(case_data["diagonal_length_d_mm"]),
        float(case_data["panel_length_mm"]),
        float(case_data["branch_axis_spacing_b_mm"]),
    )
    eq22 = bm.cross_lattice_additional_diagonal_force_n(
        float(case_data["one_branch_force_n"]),
        float(case_data["one_diagonal_area_mm2"]),
        float(case_data["one_branch_area_mm2"]),
        alpha2,
    )
    brace_force = bm.reduced_length_brace_design_force_n(q_fic)
    spacer_force = bm.column_branch_spacer_fictitious_shear_n(
        float(case_data["column_branch_force_1_n"]),
        float(case_data["column_branch_force_2_n"]),
        elastic,
        ry,
        stability["overall_stability_coefficient_phi"],
    )

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "clause_7_2_1_strength_utilization": strength,
            "clause_7_2_1_strength_pass": strength <= 1.0,
            "clause_7_2_2_method": method,
            "equation_12_battened_type_1_effective_slenderness": eq12,
            "equation_13_battened_type_2_effective_slenderness": eq13,
            "equation_14_battened_type_3_effective_slenderness": eq14,
            "equation_15_lattice_type_1_effective_slenderness": eq15,
            "equation_16_lattice_type_2_effective_slenderness": eq16,
            "equation_17_lattice_type_3_effective_slenderness": eq17,
            "equation_15_effective_relative_slenderness": effective_relative_slenderness,
            "batten_branch_limit": batten_branch,
            "lattice_branch_assessment": branch_assessment,
            "lattice_stability": stability,
            "close_contact_spacing": spacing,
            "equation_18_fictitious_shear_force_n": q_fic,
            "fictitious_shear_distribution": distribution,
            "equation_19_batten_shear_force_n": eq19,
            "equation_20_batten_bending_moment_n_mm": eq20,
            "equation_21_lattice_diagonal_force_n": eq21,
            "equation_22_alpha_2": alpha2,
            "equation_22_additional_diagonal_force_n": eq22,
            "clause_7_2_10_brace_design_force_n": brace_force,
            "clause_7_2_10_column_spacer_force_n": spacer_force,
        },
        "scope_note": "LEGACY exhaustive multi-formula diagnostic retained for backward compatibility. It evaluates all Table 8 formulas and is NOT the Stage N3 qualified branch-safe workflow. Use action built_up_axial_member_guided, which evaluates only the selected normative route.",
    }
    _write_case_report(root, "built_up_axial_member", result, "Built-up axial-member case")
    return result

def _run_local_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    member_lambda = float(case_data["member_relative_slenderness"])
    h_eff = float(case_data["effective_web_height_mm"])
    t_w = float(case_data["web_thickness_mm"])
    b_eff = float(case_data["effective_flange_outstand_mm"])
    t_f = float(case_data["flange_thickness_mm"])
    ry = float(case_data["design_yield_resistance_n_mm2"])
    elastic = float(case_data["elastic_modulus_n_mm2"])
    gross_area = float(case_data["gross_area_mm2"])
    force = float(case_data["axial_force_n"])
    phi = float(case_data["stability_coefficient_phi"])

    actual_wall = ls.wall_relative_slenderness(h_eff, t_w, ry, elastic)
    base_wall_limit = ls.wall_slenderness_limit(
        case_data["table_9_diagram_group"],
        member_lambda,
        float(case_data["tee_flange_width_mm"]),
        h_eff,
    )
    beta = ls.longitudinal_stiffener_wall_limit_multiplier_eq30(
        float(case_data["longitudinal_stiffener_inertia_mm4"]), h_eff, t_w
    )
    wall_limit_after_longitudinal = (
        base_wall_limit * beta if bool(case_data["apply_longitudinal_stiffener_multiplier"]) else base_wall_limit
    )

    actual_flange = ls.flange_relative_slenderness(b_eff, t_f, ry, elastic)
    base_flange_limit = ls.flange_slenderness_limit(
        case_data["table_10_diagram_group"], member_lambda, bool(case_data["edge_stiffened"])
    )

    if bool(case_data["two_plane_condition_governs"]):
        two_plane_factor = ls.two_plane_slenderness_increase_factor(phi, gross_area, ry, force)
    else:
        two_plane_factor = 1.0
    final_wall_limit = ls.apply_two_plane_slenderness_increase(wall_limit_after_longitudinal, two_plane_factor)
    final_flange_limit = ls.apply_two_plane_slenderness_increase(base_flange_limit, two_plane_factor)

    stiffeners = ls.transverse_stiffener_requirements(
        actual_wall,
        h_eff,
        ry,
        elastic,
        case_data["transverse_stiffener_arrangement"],
        float(case_data["provided_transverse_stiffener_outstand_mm"]),
        bool(case_data["geometrically_nonlinear_design"]),
        bool(case_data["solid_branch_of_built_up_column"]),
    )
    edge_requirements = ls.edge_stiffener_requirements(
        b_eff, ry, elastic, bool(case_data["member_reinforced_with_battens"])
    )
    reduction = ls.reduced_area_required(actual_wall, final_wall_limit)
    reduced_web_height = h_eff
    reduced_box_flange_width = float(case_data["effective_box_flange_plate_width_mm"])
    reduced_area = gross_area
    reduced_area_status = "not_required"

    if reduction["required"]:
        if not reduction["within_central_compression_reduction_domain"]:
            reduced_area_status = "outside_clause_7_3_5_central_compression_domain"
        else:
            family = case_data["reduced_area_section_family"]
            expected_group = {
                "i_section": "group_1_i_section",
                "box_section": "group_2_box_section",
                "channel_section": "group_3_channel_section",
            }[family]
            if case_data["table_9_diagram_group"] != expected_group:
                raise ValueError("reduced_area_section_family is inconsistent with table_9_diagram_group")
            if family == "i_section":
                reduced_web_height = ls.reduced_web_height_i_section_eq34(
                    t_w, actual_wall, final_wall_limit, member_lambda, ry, elastic
                )
                reduced_area = ls.reduced_area_i_or_channel_eq31(gross_area, h_eff, reduced_web_height, t_w)
            elif family == "channel_section":
                reduced_web_height = ls.reduced_web_height_channel_eq36(
                    t_w, actual_wall, final_wall_limit, ry, elastic
                )
                reduced_area = ls.reduced_area_i_or_channel_eq31(gross_area, h_eff, reduced_web_height, t_w)
            else:
                reduced_web_height = ls.reduced_plate_dimension_box_eq35(
                    t_w, actual_wall, final_wall_limit, member_lambda, ry, elastic
                )
                box_width = float(case_data["effective_box_flange_plate_width_mm"])
                box_thickness = float(case_data["box_flange_thickness_mm"])
                box_actual = ls.flange_relative_slenderness(box_width, box_thickness, ry, elastic)
                if box_actual > final_flange_limit:
                    if box_actual > 2.0 * final_flange_limit:
                        raise ValueError("Box flange plate exceeds twice its limiting slenderness")
                    reduced_box_flange_width = ls.reduced_plate_dimension_box_eq35(
                        box_thickness, box_actual, final_flange_limit, member_lambda, ry, elastic
                    )
                reduced_area = ls.reduced_area_box_central_eq32(
                    gross_area,
                    h_eff,
                    reduced_web_height,
                    t_w,
                    box_width,
                    reduced_box_flange_width,
                    box_thickness,
                )
            reduced_area_status = "applied"

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "actual_wall_relative_slenderness": actual_wall,
            "base_wall_limiting_relative_slenderness": base_wall_limit,
            "equation_30_longitudinal_stiffener_multiplier": beta,
            "wall_limit_after_longitudinal_stiffener": wall_limit_after_longitudinal,
            "two_plane_increase_factor": two_plane_factor,
            "final_wall_limiting_relative_slenderness": final_wall_limit,
            "wall_local_stability_pass": actual_wall <= final_wall_limit,
            "actual_flange_relative_slenderness": actual_flange,
            "base_flange_limiting_relative_slenderness": base_flange_limit,
            "final_flange_limiting_relative_slenderness": final_flange_limit,
            "flange_local_stability_pass": actual_flange <= final_flange_limit,
            "transverse_stiffener_requirements": stiffeners,
            "edge_stiffener_requirements": edge_requirements,
            "reduced_area_assessment": reduction,
            "reduced_area_status": reduced_area_status,
            "reduced_web_height_mm": reduced_web_height,
            "reduced_box_flange_width_mm": reduced_box_flange_width,
            "design_area_mm2": reduced_area,
        },
        "scope_note": "Clauses 7.3.1-7.3.11 only. Diagram-group selection and effective-dimension extraction from geometry remain explicit engineering inputs. Equation (33) is available in the core but complete eccentric-compression design is outside this runner.",
    }
    _write_case_report(root, "local_stability", result, "Centrally compressed member local-stability case")
    return result



def _run_bending_member_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    class_route = bend.bending_member_class_requirements(
        int(case_data["member_class"]),
        bool(case_data["load_is_static"]),
        bool(case_data["is_crane_runway_beam"]),
        bool(case_data["is_bimetal_beam"]),
    )
    ry = float(case_data["design_yield_resistance_n_mm2"])
    rs = float(case_data["design_shear_resistance_n_mm2"])
    gamma_c = float(case_data["working_condition_factor"])
    mx = float(case_data["moment_x_n_mm"])
    my = float(case_data["moment_y_n_mm"])
    bimoment = float(case_data["bimoment_n_mm2"])
    wx = float(case_data["minimum_net_section_modulus_x_mm3"])
    wy = float(case_data["minimum_net_section_modulus_y_mm3"])

    eq41 = bend.elastic_bending_utilization_eq41(mx, wx, ry, gamma_c)
    eq42 = bend.elastic_shear_utilization_eq42(
        float(case_data["shear_force_n"]),
        float(case_data["first_moment_area_mm3"]),
        float(case_data["gross_second_moment_area_mm4"]),
        float(case_data["web_thickness_mm"]),
        rs,
        gamma_c,
    )
    eq43 = bend.elastic_combined_normal_utilization_eq43(
        mx,
        my,
        bimoment,
        float(case_data["net_inertia_x_mm4"]),
        float(case_data["net_inertia_y_mm4"]),
        float(case_data["net_sectorial_inertia_mm6"]),
        float(case_data["point_y_mm"]),
        float(case_data["point_x_mm"]),
        float(case_data["sectorial_coordinate_mm2"]),
        ry,
        gamma_c,
    )
    raw_shear_stress_xy = float(case_data["shear_stress_xy_n_mm2"])
    eq44_unadjusted = bend.elastic_web_equivalent_stress_checks_eq44(
        float(case_data["longitudinal_normal_stress_n_mm2"]),
        float(case_data["transverse_normal_stress_n_mm2"]),
        raw_shear_stress_xy,
        ry,
        rs,
        gamma_c,
    )
    hole_factor = bend.bolt_hole_factor_eq45(
        float(case_data["hole_pitch_mm"]), float(case_data["hole_diameter_mm"])
    )
    applied_hole_factor = hole_factor if bool(case_data["web_has_bolt_holes"]) else 1.0
    eq42_adjusted = bend.apply_bolt_hole_factor(eq42, applied_hole_factor)
    adjusted_shear_stress_xy = raw_shear_stress_xy * applied_hole_factor
    eq44 = bend.elastic_web_equivalent_stress_checks_eq44(
        float(case_data["longitudinal_normal_stress_n_mm2"]),
        float(case_data["transverse_normal_stress_n_mm2"]),
        adjusted_shear_stress_xy,
        ry,
        rs,
        gamma_c,
    )
    eq44_shear_adjusted = float(eq44["shear_utilization"])

    if case_data["figure_6_case"] == "welded_or_rolled":
        effective_length = bend.effective_load_length_by_case(
            "welded_or_rolled",
            float(case_data["bearing_width_mm"]),
            float(case_data["flange_and_weld_or_fillet_height_mm"]),
            None,
            None,
            None,
        )
    else:
        effective_length = bend.effective_load_length_by_case(
            "crane_wheel",
            None,
            None,
            float(case_data["distribution_coefficient_psi"]),
            float(case_data["flange_and_rail_inertia_mm4"]),
            float(case_data["web_thickness_mm"]),
        )
    local_stress = bend.local_web_compression_stress_eq47(
        float(case_data["concentrated_force_n"]), effective_length, float(case_data["web_thickness_mm"])
    )
    local_utilization = bend.local_web_compression_utilization_eq46(local_stress, ry, gamma_c)

    e1 = bend.annex_e1_design_coefficients(
        case_data["table_e1_section_type"],
        float(case_data["flange_to_web_area_ratio"]),
        bool(case_data["minor_axis_moment_is_zero"]),
        float(case_data["equivalent_load_safety_factor"]),
    )
    plastic_applicability = bend.plastic_bending_applicability(
        int(case_data["member_class"]),
        case_data["plastic_section_family"],
        float(case_data["normative_yield_resistance_n_mm2"]),
        float(case_data["shear_stress_x_n_mm2"]),
        rs,
        bool(case_data["required_clause_checks_confirmed"]),
        bool(case_data["is_support_section"]),
    )
    beta = bend.plastic_shear_reduction_factor_eq52(
        float(case_data["shear_stress_x_n_mm2"]), rs, float(case_data["flange_to_web_area_ratio"])
    )
    eq50 = bend.plastic_bending_utilization_eq50(mx, e1["c_x"], beta, wx, ry, gamma_c)
    eq51 = bend.plastic_biaxial_bending_utilization_eq51(
        mx, my, e1["c_x"], e1["c_y"], beta, wx, wy, ry, gamma_c
    )
    table_10a_ratio = mx / (e1["c_x"] * wx * ry * gamma_c)
    c_omega = bend.constrained_torsion_coefficient_table_10a(table_10a_ratio)
    eq53 = bend.constrained_torsion_utilization_eq53(
        mx,
        bimoment,
        e1["c_x"],
        beta,
        wx,
        c_omega,
        float(case_data["minimum_net_sectorial_section_modulus_mm4"]),
        ry,
        gamma_c,
    )
    pure = bend.pure_bending_modified_coefficients(e1["c_x"], e1["c_y"])
    eq54 = bend.support_shear_x_utilization_eq54(
        float(case_data["support_shear_force_x_n"]),
        float(case_data["web_area_mm2"]),
        rs,
        gamma_c,
    )
    eq55 = bend.support_shear_y_utilization_eq55(
        float(case_data["support_shear_force_y_n"]),
        float(case_data["one_flange_area_mm2"]),
        rs,
        gamma_c,
    )

    continuous_applicability = bend.continuous_beam_partial_redistribution_applicability(
        float(case_data["adjacent_span_1_mm"]),
        float(case_data["adjacent_span_2_mm"]),
        bool(case_data["continuous_constant_section"]),
        bool(case_data["continuous_doubly_symmetric_section"]),
        bool(case_data["continuous_required_clause_checks_confirmed"]),
    )
    meff_hinged = bend.effective_moment_hinged_end_eq57(
        [float(case_data["end_span_moment_1_n_mm"]), float(case_data["end_span_moment_2_n_mm"])],
        [float(case_data["end_span_distance_1_mm"]), float(case_data["end_span_distance_2_mm"])],
        float(case_data["end_span_length_mm"]),
    )
    meff_intermediate = bend.effective_moment_intermediate_span_eq58(
        float(case_data["intermediate_span_moment_n_mm"])
    )
    meff_fixed = bend.effective_moment_by_end_condition(
        "fixed_ends", [float(case_data["fixed_end_reference_moment_n_mm"])], None, None
    )
    redistributed = bend.redistributed_design_moment_eq56(
        float(case_data["maximum_elastic_moment_n_mm"]), meff_hinged
    )
    biaxial_route = bend.biaxial_redistribution_route(
        bool(case_data["redistribution_completed_in_x_plane"]),
        bool(case_data["redistribution_completed_in_y_plane"]),
    )
    class_3_route = bend.class_3_plastic_hinge_route(
        bool(case_data["clause_8_2_5_confirmed"]),
        bool(case_data["clause_8_4_6_confirmed"]),
        bool(case_data["clause_8_5_8_confirmed"]),
        bool(case_data["clause_8_5_9_confirmed"]),
        bool(case_data["clause_8_5_18_confirmed"]),
        bool(case_data["maximum_moment_sections_include_shear_effect"]),
    )

    ryw = float(case_data["web_design_yield_resistance_n_mm2"])
    ryf = float(case_data["flange_design_yield_resistance_n_mm2"])
    rsw = float(case_data["web_design_shear_resistance_n_mm2"])
    rsf = float(case_data["flange_design_shear_resistance_n_mm2"])
    r = ryf / ryw
    cxr = bend.bimetal_major_axis_coefficient_eq61(
        float(case_data["flange_reference_coefficient_c_xf"]),
        float(case_data["flange_to_web_area_ratio"]),
        r,
    )
    beta_r = bend.bimetal_shear_reduction_factor_eq62(
        float(case_data["bimetal_shear_stress_x_n_mm2"]),
        rsw,
        float(case_data["flange_to_web_area_ratio"]),
        r,
    )
    cyr = bend.bimetal_minor_axis_coefficient(case_data["bimetal_section_family"], r)
    bimetal_applicability = bend.bimetal_bending_applicability(
        case_data["bimetal_section_family"],
        bool(case_data["bimetal_has_two_symmetry_axes"]),
        bool(case_data["bimetal_required_clause_checks_confirmed"]),
        float(case_data["bimetal_shear_stress_x_n_mm2"]),
        rsw,
        float(case_data["bimetal_shear_stress_y_n_mm2"]),
        rsf,
        bool(case_data["bimetal_is_support_section"]),
    )
    eq59 = bend.bimetal_bending_utilization_eq59(mx, cxr, beta_r, wx, ryw, gamma_c)
    eq60 = bend.bimetal_biaxial_bending_utilization_eq60(
        mx, my, cxr, cyr, beta_r, wx, wy, ryw, ryf, gamma_c
    )

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "clause_8_1_class_route": class_route,
            "equation_41_elastic_bending_utilization": eq41,
            "equation_42_elastic_shear_utilization": eq42,
            "equation_42_with_bolt_hole_factor": eq42_adjusted,
            "equation_43_combined_normal_utilization": eq43,
            "equation_44_web_checks": eq44,
            "equation_44_web_checks_unadjusted_diagnostic": eq44_unadjusted,
            "equation_44_adjusted_shear_stress_n_mm2": adjusted_shear_stress_xy,
            "equation_44_shear_with_bolt_hole_factor": eq44_shear_adjusted,
            "equation_45_bolt_hole_factor": hole_factor,
            "equation_48_or_49_effective_load_length_mm": effective_length,
            "equation_47_local_web_stress_n_mm2": local_stress,
            "equation_46_local_web_utilization": local_utilization,
            "annex_e1_design_coefficients": e1,
            "clause_8_2_3_applicability": plastic_applicability,
            "equation_52_beta": beta,
            "equation_50_plastic_bending_utilization": eq50,
            "equation_51_plastic_biaxial_utilization": eq51,
            "table_10a_ratio": table_10a_ratio,
            "table_10a_c_omega": c_omega,
            "equation_53_constrained_torsion_utilization": eq53,
            "pure_bending_modified_coefficients": pure,
            "equation_54_support_shear_x_utilization": eq54,
            "equation_55_support_shear_y_utilization": eq55,
            "continuous_beam_applicability": continuous_applicability,
            "equation_57_effective_moment_hinged_n_mm": meff_hinged,
            "equation_58_effective_moment_intermediate_n_mm": meff_intermediate,
            "fixed_end_effective_moment_n_mm": meff_fixed,
            "equation_56_redistributed_design_moment_n_mm": redistributed,
            "clause_8_2_6_biaxial_route": biaxial_route,
            "clause_8_2_7_class_3_route": class_3_route,
            "bimetal_applicability": bimetal_applicability,
            "bimetal_yield_resistance_ratio_r": r,
            "equation_61_c_xr": cxr,
            "equation_62_beta_r": beta_r,
            "bimetal_c_yr": cyr,
            "equation_59_bimetal_bending_utilization": eq59,
            "equation_60_bimetal_biaxial_utilization": eq60,
        },
        "scope_note": "Clauses 8.1-8.2 only. Global stability, local plate stability, force recovery, section classification, and referenced clauses 8.4-8.5 remain separate explicit checks.",
    }
    _write_case_report(root, "bending_member", result, "Bending-member strength case")
    return result


def _run_crane_runway_and_bending_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    beta_factor = 0.87 if case_data["crane_beta_case"] == "simply_supported" else 0.77
    local_torsional_moment = stab.crane_runway_local_torsional_moment_eq68(
        float(case_data["crane_load_factor"]),
        float(case_data["wheel_dynamic_factor"]),
        float(case_data["normative_wheel_load_n"]),
        float(case_data["rail_eccentricity_mm"]),
        float(case_data["transverse_horizontal_load_n"]),
        float(case_data["rail_height_mm"]),
    )
    stresses = stab.crane_runway_stress_components_eq67(
        float(case_data["crane_bending_moment_n_mm"]),
        float(case_data["crane_net_section_modulus_mm3"]),
        float(case_data["crane_load_factor"]),
        float(case_data["wheel_dynamic_factor"]),
        float(case_data["normative_wheel_load_n"]),
        float(case_data["effective_load_length_mm"]),
        float(case_data["web_thickness_mm"]),
        local_torsional_moment,
        float(case_data["stiffener_spacing_mm"]),
        float(case_data["rail_and_flange_torsional_inertia_mm4"]),
        float(case_data["web_height_mm"]),
        float(case_data["crane_shear_force_n"]),
    )
    eq63 = stab.crane_runway_equivalent_stress_utilization_eq63(
        beta_factor,
        stresses["sigma_x_n_mm2"],
        stresses["sigma_local_x_n_mm2"],
        stresses["sigma_local_y_n_mm2"],
        stresses["tau_xy_n_mm2"],
        stresses["tau_local_xy_n_mm2"],
        float(case_data["design_yield_resistance_n_mm2"]),
    )
    eq64 = stab.crane_runway_longitudinal_normal_utilization_eq64(
        stresses["sigma_x_n_mm2"], stresses["sigma_local_x_n_mm2"], float(case_data["design_yield_resistance_n_mm2"])
    )
    eq65 = stab.crane_runway_transverse_normal_utilization_eq65(
        stresses["sigma_local_y_n_mm2"], stresses["sigma_f_y_n_mm2"], float(case_data["design_yield_resistance_n_mm2"])
    )
    eq66 = stab.crane_runway_shear_utilization_eq66(
        stresses["tau_xy_n_mm2"], stresses["tau_local_xy_n_mm2"], stresses["tau_f_xy_n_mm2"], float(case_data["design_shear_resistance_n_mm2"])
    )

    alpha = stab.annex_zh_alpha_rolled_eq_zh4(
        float(case_data["torsional_inertia_mm4"]),
        float(case_data["minor_axis_inertia_mm4"]),
        float(case_data["stability_effective_length_mm"]),
        float(case_data["section_height_mm"]),
        bool(case_data["compression_flange_braced_in_span"]),
    )
    psi = stab.annex_zh_table_1_psi(case_data["annex_zh_table_1_case"], alpha, case_data.get("annex_zh_load_flange"))
    phi_bundle = stab.annex_zh_symmetric_i_phi_b(
        psi,
        float(case_data["minor_axis_inertia_mm4"]),
        float(case_data["major_axis_inertia_mm4"]),
        float(case_data["section_height_mm"]),
        float(case_data["stability_effective_length_mm"]),
        float(case_data["elastic_modulus_n_mm2"]),
        float(case_data["design_yield_resistance_n_mm2"]),
    )
    eq69 = stab.lateral_torsional_stability_utilization_eq69(
        float(case_data["stability_major_moment_n_mm"]),
        phi_bundle["phi_b"],
        float(case_data["compressed_major_section_modulus_mm3"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq70 = stab.crane_runway_lateral_torsional_stability_utilization(
        float(case_data["stability_major_moment_n_mm"]),
        float(case_data["stability_minor_moment_n_mm"]),
        float(case_data["stability_bimoment_n_mm2"]),
        phi_bundle["phi_b"],
        float(case_data["compressed_major_section_modulus_mm3"]),
        float(case_data["compressed_minor_section_modulus_mm3"]),
        float(case_data["compressed_sectorial_section_modulus_mm4"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    actual_lambda_b = stab.compressed_flange_relative_slenderness(
        float(case_data["stability_effective_length_mm"]),
        float(case_data["compressed_flange_width_mm"]),
        float(case_data["compressed_flange_design_resistance_n_mm2"]),
        float(case_data["elastic_modulus_n_mm2"]),
    )
    limit_lambda_b = stab.table_11_limit(
        case_data["table_11_load_position"],
        float(case_data["compressed_flange_width_mm"]),
        float(case_data["compressed_flange_thickness_mm"]),
        float(case_data["flange_axis_spacing_mm"]),
        bool(case_data["friction_flange_connections"]),
        float(case_data["compressed_flange_design_resistance_n_mm2"]),
        float(case_data["compressed_flange_stress_n_mm2"]),
    )
    equivalent_force = stab.compressed_flange_equivalent_force_eq74(
        float(case_data["compressed_flange_area_mm2"]),
        float(case_data["web_area_mm2"]),
        float(case_data["compressed_flange_design_resistance_n_mm2"]),
        float(case_data["web_design_resistance_n_mm2"]),
    )
    discrete_force = stab.discrete_bracing_fictitious_force(
        equivalent_force,
        float(case_data["stability_effective_length_mm"]),
        float(case_data["compressed_flange_radius_of_gyration_mm"]),
        float(case_data["elastic_modulus_n_mm2"]),
        float(case_data["web_design_resistance_n_mm2"]),
    )
    continuous_force = stab.continuous_bracing_force_per_length_eq75(
        stab.discrete_bracing_fictitious_force(
            equivalent_force,
            float(case_data["stability_effective_length_mm"]),
            float(case_data["compressed_flange_radius_of_gyration_mm"]),
            float(case_data["elastic_modulus_n_mm2"]),
            float(case_data["web_design_resistance_n_mm2"]),
        )["q_fictitious_n"],
        float(case_data["beam_span_mm"]),
    )
    c1x = stab.class_2_3_coefficient_eq77(
        float(case_data["class_2_3_moment_n_mm"]),
        float(case_data["class_2_3_net_section_modulus_mm3"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
        float(case_data["class_2_3_shear_reduction_beta"]),
        float(case_data["class_2_3_plastic_coefficient_cx"]),
    )
    delta = stab.class_2_3_stability_reduction_eq76(c1x, float(case_data["class_2_3_plastic_coefficient_cx"]))
    class_2_3_plastic_region_applies = bool(case_data["class_2_3_plastic_region_applies"]) if "class_2_3_plastic_region_applies" in case_data else False
    effective_limit_lambda_b = delta * limit_lambda_b if class_2_3_plastic_region_applies else limit_lambda_b
    exemption = stab.lateral_stability_check_exemption(
        bool(case_data["rigid_continuous_deck"]),
        actual_lambda_b,
        effective_limit_lambda_b,
        float(case_data["tension_to_compression_flange_width_ratio"]),
    )

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "crane_beta_factor": beta_factor,
            "equation_68_local_torsional_moment_n_mm": local_torsional_moment,
            "equation_67_stress_components": stresses,
            "equation_63_equivalent_utilization": eq63,
            "equation_64_longitudinal_utilization": eq64,
            "equation_65_transverse_utilization": eq65,
            "equation_66_shear_utilization": eq66,
            "annex_zh_alpha": alpha,
            "annex_zh_psi": psi,
            "annex_zh_phi_bundle": phi_bundle,
            "equation_69_lateral_torsional_utilization": eq69,
            "equation_70_combined_stability_utilization": eq70,
            "actual_relative_flange_slenderness": actual_lambda_b,
            "table_11_limiting_flange_slenderness": limit_lambda_b,
            "class_2_3_plastic_region_applies": class_2_3_plastic_region_applies,
            "effective_limiting_flange_slenderness_for_exemption": effective_limit_lambda_b,
            "clause_8_4_4_exemption": exemption,
            "equation_74_equivalent_compressed_flange_force_n": equivalent_force,
            "discrete_bracing_force_bundle": discrete_force,
            "equation_75_continuous_bracing_force_n_per_mm": continuous_force,
            "equation_77_c1x": c1x,
            "equation_76_delta": delta,
            "class_2_3_plastic_region_limit": delta * limit_lambda_b,
        },
        "scope_note": "Clauses 8.3-8.4 and Annex Ж are implemented. Tables 12-13 are transcribed as forward dependencies, but the clause 8.5 web-stability equations that consume them remain outside this runner.",
    }
    _write_case_report(root, "crane_runway_and_bending_stability", result, "Crane-runway and bending-stability case")
    return result


def _run_bending_member_local_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    sigma = bls.bending_normal_stress_eq78(
        float(case_data["moment_n_mm"]),
        float(case_data["distance_from_neutral_axis_mm"]),
        float(case_data["major_inertia_mm4"]),
    )
    tau = bls.average_web_shear_stress_eq79(
        float(case_data["shear_force_n"]),
        float(case_data["web_thickness_mm"]),
        float(case_data["full_web_height_mm"]),
    )
    ry = float(case_data["design_yield_resistance_n_mm2"])
    rs = float(case_data["design_shear_resistance_n_mm2"])
    e = float(case_data["elastic_modulus_n_mm2"])
    tw = float(case_data["web_thickness_mm"])
    hef = float(case_data["effective_web_height_mm"])
    a = float(case_data["panel_length_mm"])
    lambda_w = (hef / tw) * (ry / e) ** 0.5
    d = min(a, hef)
    mu = max(a, hef) / d
    lambda_d = (d / tw) * (ry / e) ** 0.5
    delta = bls.flange_restraint_parameter_eq84(
        float(case_data["beta_factor"]),
        float(case_data["flange_width_mm"]),
        hef,
        float(case_data["flange_thickness_mm"]),
        tw,
    )
    c1 = bls.table_14_c1(float(case_data["table_14_rho"]), float(case_data["table_14_panel_ratio"]))
    c2 = bls.table_15_c2(float(case_data["table_15_delta"]), float(case_data["table_15_panel_ratio"]))
    from .crane_runway_and_bending_stability import table_12_c_cr_coefficient
    ccr = table_12_c_cr_coefficient("welded", delta)
    sigma_cr = bls.critical_normal_web_stress_eq81(ccr, ry, lambda_w)
    sigma_loc_cr = bls.critical_local_web_stress_eq82(c1, c2, ry, lambda_w)
    tau_cr = bls.critical_web_shear_stress_eq83(mu, rs, lambda_d)
    utilization = bls.symmetric_web_buckling_utilization_eq80(
        max(0.0, sigma),
        float(case_data["local_stress_n_mm2"]),
        tau,
        sigma_cr,
        sigma_loc_cr,
        tau_cr,
        float(case_data["working_condition_factor"]),
    )
    actual_flange_slenderness = (float(case_data["flange_outstand_mm"]) / float(case_data["flange_thickness_mm"])) * (float(case_data["flange_design_yield_resistance_n_mm2"]) / e) ** 0.5
    if int(case_data["section_class"]) == 1:
        flange_limit = bls.flange_outstand_limit_eq97(
            float(case_data["flange_design_yield_resistance_n_mm2"]),
            float(case_data["compressed_flange_stress_n_mm2"]),
        )
        flange_limit_equation = 97
    else:
        flange_limit = bls.class_2_3_flange_outstand_limit_eq99(lambda_w)
        flange_limit_equation = 99
    prelim = bls.preliminary_web_check_exemption_8_5_1(lambda_w, float(case_data["local_stress_n_mm2"]) > 0.0, True)
    stiffeners = bls.transverse_stiffener_requirements_8_5_9(
        int(case_data["section_class"]), lambda_w, False, int(case_data["section_class"]) in {2, 3}, hef
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "equation_78_normal_stress_n_mm2": sigma,
            "equation_79_average_shear_stress_n_mm2": tau,
            "web_relative_slenderness": lambda_w,
            "plate_relative_slenderness": lambda_d,
            "panel_aspect_ratio_mu": mu,
            "equation_84_delta": delta,
            "table_12_c_cr": ccr,
            "table_14_c1": c1,
            "table_15_c2": c2,
            "equation_81_sigma_cr_n_mm2": sigma_cr,
            "equation_82_sigma_local_cr_n_mm2": sigma_loc_cr,
            "equation_83_tau_cr_n_mm2": tau_cr,
            "equation_80_web_utilization": utilization,
            "equation_80_pass": utilization <= 1.0,
            "preliminary_clause_8_5_1": prelim,
            "transverse_stiffener_requirement": stiffeners,
            "actual_flange_relative_slenderness": actual_flange_slenderness,
            "flange_limit_equation": flange_limit_equation,
            "limiting_flange_relative_slenderness": flange_limit,
            "flange_local_stability_pass": actual_flange_slenderness <= flange_limit,
        },
        "scope_note": "Clauses 8.5.1-8.5.20 are implemented as scalar equations, exact table lookups, and explicit routing procedures. Geometry extraction, global analysis, and external flexible-web rules remain outside this action.",
    }
    _write_case_report(root, "bending_member_local_stability", result, "Bending-member local-stability case")
    return result


def _run_base_plates_and_combined_force_strength_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    foundation_boundary = bc.base_plate_foundation_area_boundary(case_data["foundation_strength_check_confirmed"])
    if not foundation_boundary["permitted"]:
        raise ValueError("Clause 8.6.1 foundation-strength check must be confirmed")

    q = float(case_data["foundation_pressure_n_mm2"])
    m1 = bc.base_plate_cantilever_moment_eq102(q, float(case_data["cantilever_projection_mm"]))
    four_coeff = bc.annex_e2_base_plate_coefficients("four_sides", float(case_data["four_side_ratio_b_over_a"]))
    m2 = bc.base_plate_four_side_moments_eq103(
        q,
        float(case_data["four_side_short_side_mm"]),
        four_coeff["alpha_1"],
        four_coeff["alpha_2"],
    )
    three_coeff = bc.annex_e2_base_plate_coefficients("three_sides", float(case_data["three_side_ratio_a1_over_d1"]))
    m3 = bc.base_plate_three_side_moment_eq104(
        q,
        float(case_data["three_side_free_side_length_mm"]),
        three_coeff["alpha_3"],
    )
    mmax = bc.base_plate_maximum_unit_width_moment([
        m1,
        m2["moment_short_direction_n_mm_per_mm"],
        m2["moment_long_direction_n_mm_per_mm"],
        m3,
    ])
    thickness = bc.base_plate_required_thickness_eq101(
        mmax,
        float(case_data["base_plate_design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )

    coeff = bc.combined_force_coefficients_from_annex_e1(
        case_data["annex_e1_section_type"],
        float(case_data["flange_to_web_area_ratio"]),
        float(case_data["bending_moment_y_n_mm"]) != 0.0,
    )
    applicability_105 = bc.equation_105_applicability(
        float(case_data["normative_yield_resistance_n_mm2"]),
        case_data["direct_dynamic_load"],
        float(case_data["shear_stress_n_mm2"]),
        float(case_data["design_shear_resistance_n_mm2"]),
        float(case_data["axial_force_n"]),
        float(case_data["net_area_mm2"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        case_data["clause_8_5_8_confirmed"],
        case_data["clause_8_5_18_confirmed"],
    )
    if not applicability_105["permitted"]:
        raise ValueError(f"Equation (105) applicability failed: {applicability_105['reasons']}")
    eq105 = bc.combined_force_strength_utilization_eq105(
        float(case_data["axial_force_n"]),
        float(case_data["net_area_mm2"]),
        float(case_data["bending_moment_x_n_mm"]),
        float(case_data["bending_moment_y_n_mm"]),
        float(case_data["bimoment_n_mm2"]),
        coeff["n"], coeff["c_x"], coeff["c_y"],
        float(case_data["minimum_net_section_modulus_x_mm3"]),
        float(case_data["minimum_net_section_modulus_y_mm3"]),
        float(case_data["minimum_net_sectorial_section_modulus_mm4"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq106 = bc.combined_force_point_utilization_eq106(
        float(case_data["signed_axial_force_n"]),
        float(case_data["net_area_mm2"]),
        float(case_data["signed_bending_moment_x_n_mm"]),
        float(case_data["point_y_mm"]),
        float(case_data["net_inertia_x_mm4"]),
        float(case_data["signed_bending_moment_y_n_mm"]),
        float(case_data["point_x_mm"]),
        float(case_data["net_inertia_y_mm4"]),
        float(case_data["signed_bimoment_n_mm2"]),
        float(case_data["sectorial_coordinate_mm2"]),
        float(case_data["net_sectorial_inertia_mm6"]),
        float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    omission = bc.equation_105_omission_rule_clause_9_1_2(
        float(case_data["reduced_relative_eccentricity"]),
        case_data["section_is_unweakened"],
        case_data["strength_and_stability_moments_are_equal"],
    )
    applicability_107 = bc.equation_107_applicability(
        float(case_data["high_strength_normative_yield_resistance_n_mm2"]),
        case_data["high_strength_section_asymmetry_confirmed"],
    )
    if not applicability_107["permitted"]:
        raise ValueError(f"Equation (107) applicability failed: {applicability_107['reasons']}")
    delta = bc.high_strength_asymmetric_delta_eq108(
        float(case_data["high_strength_compression_force_n"]),
        float(case_data["high_strength_relative_slenderness"]),
        float(case_data["high_strength_gross_area_mm2"]),
        float(case_data["high_strength_design_yield_resistance_n_mm2"]),
    )
    eq107 = bc.high_strength_asymmetric_tension_fiber_utilization_eq107(
        float(case_data["high_strength_compression_force_n"]),
        float(case_data["high_strength_net_area_mm2"]),
        float(case_data["high_strength_bending_moment_n_mm"]),
        delta,
        float(case_data["high_strength_tension_fiber_section_modulus_mm3"]),
        float(case_data["high_strength_design_ultimate_resistance_n_mm2"]),
        float(case_data["ultimate_resistance_safety_factor"]),
        float(case_data["working_condition_factor"]),
    )

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "equation_102_cantilever_moment_n_mm_per_mm": m1,
            "table_e2_four_side_alpha_1": four_coeff["alpha_1"],
            "table_e2_four_side_alpha_2": four_coeff["alpha_2"],
            "equation_103_short_direction_moment_n_mm_per_mm": m2["moment_short_direction_n_mm_per_mm"],
            "equation_103_long_direction_moment_n_mm_per_mm": m2["moment_long_direction_n_mm_per_mm"],
            "table_e2_three_side_alpha_3": three_coeff["alpha_3"],
            "equation_104_three_side_moment_n_mm_per_mm": m3,
            "maximum_unit_width_moment_n_mm_per_mm": mmax,
            "equation_101_required_base_plate_thickness_mm": thickness,
            "annex_e1_c_x": coeff["c_x"],
            "annex_e1_c_y": coeff["c_y"],
            "annex_e1_n": coeff["n"],
            "equation_105_applicability": applicability_105,
            "equation_105_utilization": eq105,
            "equation_105_pass": eq105 <= 1.0,
            "equation_106_point_utilization": eq106,
            "equation_106_pass": eq106 <= 1.0,
            "clause_9_1_2_omission_rule": omission,
            "equation_107_applicability": applicability_107,
            "equation_108_delta": delta,
            "equation_107_tension_fiber_utilization": eq107,
            "equation_107_pass": eq107 <= 1.0,
        },
        "scope_note": "Clause 8.6 and Section 9.1 scalar procedures are implemented. Foundation resistance, geometry classification, global analysis, stability, and complete connection design remain external.",
    }
    _write_case_report(root, "base_plates_and_combined_force_strength", result, "Base plates and combined-force strength case")
    return result


def _run_beam_column_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    if not case_data["clause_9_2_applicability_confirmed"]:
        raise ValueError("Clause 9.2 applicability must be confirmed")
    if not case_data["same_load_combination_confirmed"]:
        raise ValueError("N and M must come from the same load combination under 9.2.3")
    if not case_data["section_classification_confirmed"]:
        raise ValueError("Table D.2 and Table 21 section classifications must be confirmed")
    if not case_data["required_reduced_area_confirmed"]:
        raise ValueError("The input area must include any required linked-clause reduction")

    axial = float(case_data["axial_force_n"])
    area = float(case_data["gross_or_reduced_area_mm2"])
    ry = float(case_data["design_yield_resistance_n_mm2"])
    gamma_c = float(case_data["working_condition_factor"])
    lx = float(case_data["relative_slenderness_x"])
    ly = float(case_data["relative_slenderness_y"])
    mx = float(case_data["relative_eccentricity_x"])
    my = float(case_data["relative_eccentricity_y"])

    eta_x = beamcol.annex_d2_shape_influence_coefficient(
        case_data["annex_d2_section_type_x"], lx, mx,
        case_data["annex_d2_flange_to_web_area_ratio_x"],
        case_data["annex_d2_offset_ratio_a1_to_h_x"],
    )
    eta_y = beamcol.annex_d2_shape_influence_coefficient(
        case_data["annex_d2_section_type_y"], ly, my,
        case_data["annex_d2_flange_to_web_area_ratio_y"],
        case_data["annex_d2_offset_ratio_a1_to_h_y"],
    )
    meff_x = beamcol.effective_relative_eccentricity_eq110(eta_x, mx)
    meff_y = beamcol.effective_relative_eccentricity_eq110(eta_y, my)
    route = beamcol.beam_column_section_9_2_route(
        max(meff_x, meff_y), case_data["section_is_box"],
        case_data["bending_in_one_plane"], case_data["bending_in_two_planes"],
    )
    additional = beamcol.biaxial_additional_checks_clause_9_2_9(meff_y, mx, lx, ly)
    # Annex D.3 is not applicable to a plane whose m_eff exceeds 20; that
    # plane is routed to Section 8. Do not call D.3 unconditionally.
    phi_ex = None if meff_x > 20.0 else beamcol.annex_d3_stability_coefficient(lx, meff_x, float(case_data["central_compression_phi_x"]))
    phi_ey = None if meff_y > 20.0 else beamcol.annex_d3_stability_coefficient(ly, meff_y, float(case_data["central_compression_phi_y"]))
    eq109 = (beamcol.beam_column_in_plane_utilization_eq109(axial, phi_ex, area, ry, gamma_c)
             if phi_ex is not None else None)

    table21_alpha = beamcol.table_21_alpha(
        case_data["table_21_section_type"], mx, case_data["table_21_smaller_to_larger_flange_inertia_ratio"]
    )
    table21_beta = beamcol.table_21_beta(
        case_data["table_21_section_type"], ly, float(case_data["central_compression_phi_y"]),
        float(case_data["central_compression_phi_at_3_14"]),
        case_data["table_21_smaller_to_larger_flange_inertia_ratio"],
    )
    c_bundle = beamcol.out_of_plane_coefficient_c(
        mx, table21_alpha, table21_beta, float(case_data["central_compression_phi_y"]),
        float(case_data["bending_stability_phi_b"]), float(case_data["annex_d_c_max"]),
    )
    eq111 = beamcol.beam_column_out_of_plane_utilization_eq111(
        axial, float(c_bundle["c"]), float(case_data["central_compression_phi_y"]), area, ry, gamma_c
    )
    eq115 = beamcol.central_compression_out_of_plane_utilization_eq115(
        axial, float(case_data["central_compression_phi_x"]), area, ry, gamma_c
    )
    if additional["equation_116_required"] and phi_ey is not None:
        phi_exy = beamcol.biaxial_stability_coefficient_eq117(phi_ey, float(c_bundle["c"]))
        eq116 = beamcol.biaxial_beam_column_utilization_eq116(axial, phi_exy, area, ry, gamma_c)
    else:
        phi_exy = None
        eq116 = None

    calculated_mx = beamcol.relative_eccentricity_x_eq118(
        float(case_data["eccentricity_x_mm"]), area, float(case_data["compressed_section_modulus_x_mm3"])
    )
    calculated_my = beamcol.relative_eccentricity_y_eq119(
        float(case_data["eccentricity_y_mm"]), area, float(case_data["compressed_section_modulus_y_mm3"])
    )
    table20_m = beamcol.table_20_design_moment(
        float(case_data["maximum_moment_n_mm"]), float(case_data["middle_third_moment_n_mm"]),
        float(case_data["auxiliary_moment_m2_n_mm"]), float(case_data["maximum_relative_eccentricity"]), lx,
    )
    d5_meff = beamcol.annex_d5_effective_relative_eccentricity(
        float(case_data["end_moment_ratio_delta"]), float(case_data["geometric_slenderness_for_d5"]),
        float(case_data["reference_effective_eccentricity_d5"]),
    )
    adjusted_mx = beamcol.adjusted_relative_eccentricity_x_clause_9_2_9(
        mx, case_data["major_stiffness_plane_coincides_with_symmetry_plane"], case_data["table_21_section_type"]
    )

    dx = beamcol.box_delta_eq122(axial, lx, area, ry)
    dy = beamcol.box_delta_eq122(axial, ly, area, ry)
    if case_data["section_is_box"]:
        if phi_ex is None or phi_ey is None:
            raise ValueError("Box-section equations (120)-(122) require m_eff<=20 in both evaluated planes")
        box_phi = beamcol.box_major_axis_phi_clause_9_2_10(
            case_data["box_bending_in_major_stiffness_plane"], case_data["box_minor_axis_moment_is_zero"], phi_ex, phi_ey
        )
    else:
        # Preserve example diagnostics without requiring a D.3 coefficient that is
        # inapplicable after an m_eff>20 Section-8 route.
        box_phi = phi_ex if phi_ex is not None else float(case_data["central_compression_phi_x"])
    eq120 = beamcol.box_major_axis_utilization_eq120(
        axial, box_phi, area, ry, gamma_c, float(case_data["box_major_axis_moment_n_mm"]),
        float(case_data["box_plastic_coefficient_cx"]), dx, float(case_data["box_minimum_section_modulus_x_mm3"]),
    )
    eq121 = beamcol.box_minor_axis_utilization_eq121(
        axial, phi_ey, area, ry, gamma_c, float(case_data["box_minor_axis_moment_n_mm"]),
        float(case_data["box_plastic_coefficient_cy"]), dy, float(case_data["box_minimum_section_modulus_y_mm3"]),
    )

    d2_parameters = beamcol.annex_d_open_section_parameters_eq_d2(
        float(case_data["open_section_alpha_ratio"]), float(case_data["open_section_beta_parameter"]),
        float(case_data["major_axis_inertia_mm4"]), float(case_data["minor_axis_inertia_mm4"]),
        float(case_data["sectorial_inertia_mm6"]), float(case_data["torsional_inertia_mm4"]),
        float(case_data["geometric_slenderness_y"]), area, float(case_data["section_height_mm"]),
        float(case_data["eccentricity_x_mm"]),
    )
    d1_cmax = beamcol.annex_d_open_section_cmax_eq_d1(d2_parameters)
    d4_cmax = beamcol.annex_d_continuous_bracing_cmax_eq_d4(
        float(case_data["major_axis_inertia_mm4"]), float(case_data["minor_axis_inertia_mm4"]),
        float(case_data["major_axis_radius_mm"]), float(case_data["minor_axis_radius_mm"]),
        float(case_data["section_height_mm"]), float(case_data["eccentricity_x_mm"]),
        float(case_data["annex_zh_alpha_parameter"]),
    )

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "section_9_2_route": route,
            "annex_d2_eta_x": eta_x, "annex_d2_eta_y": eta_y,
            "equation_110_m_eff_x": meff_x, "equation_110_m_eff_y": meff_y,
            "annex_d3_phi_ex": phi_ex, "annex_d3_phi_ey": phi_ey,
            "equation_109_utilization": eq109, "equation_109_pass": None if eq109 is None else eq109 <= 1.0,
            "table_21_alpha": table21_alpha, "table_21_beta": table21_beta,
            "equations_112_to_114_c": c_bundle,
            "equation_111_utilization": eq111, "equation_111_pass": eq111 <= 1.0,
            "equation_115_utilization": eq115, "equation_115_pass": eq115 <= 1.0,
            "equation_117_phi_exy": phi_exy,
            "equation_116_utilization": eq116, "equation_116_pass": None if eq116 is None else eq116 <= 1.0,
            "equation_118_m_x_from_geometry": calculated_mx, "equation_119_m_y_from_geometry": calculated_my,
            "table_20_design_moment_n_mm": table20_m, "table_d5_effective_eccentricity": d5_meff,
            "clause_9_2_9_additional_checks": additional, "clause_9_2_9_adjusted_m_x": adjusted_mx,
            "equation_122_delta_x": dx, "equation_122_delta_y": dy,
            "equation_120_utilization": eq120, "equation_120_pass": eq120 <= 1.0,
            "equation_121_utilization": eq121, "equation_121_pass": eq121 <= 1.0,
            "annex_d_equation_d2_parameters": d2_parameters,
            "annex_d_equation_d1_c_max": d1_cmax,
            "annex_d_equation_d4_c_max": d4_cmax,
            "annex_d6_section_parameters": beamcol.annex_d6_section_parameters(case_data["annex_d6_section_type"]),
        },
        "scope_note": "Section 9.2 scalar stability checks and exact Annex D table-node lookups are implemented. Global analysis, automatic section/diagram classification, interpolation not stated by the standard, and linked local-stability checks remain explicit external boundaries.",
    }
    _write_case_report(root, "beam_column_stability", result, "Beam-column stability case")
    return result


def _run_built_up_beam_columns_and_combined_local_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the user-facing Sections 9.3-9.4 example wrapper."""
    m = v11.built_up_relative_eccentricity_eq123(
        float(case_data["eccentricity_mm"]), float(case_data["gross_area_mm2"]),
        float(case_data["compressed_branch_axis_distance_mm"]), float(case_data["free_axis_inertia_mm4"]),
    )
    whole = v11.built_up_whole_member_stability_clause_9_3_2(
        float(case_data["relative_effective_slenderness"]), m, float(case_data["central_compression_phi"])
    )
    nad = v11.biaxial_branch_additional_force_eq124(
        float(case_data["moment_y_n_mm"]), float(case_data["spacing_b1_mm"]),
        float(case_data["moment_x_n_mm"]), float(case_data["spacing_b2_mm"]),
    )
    branch_force = v11.branch_force_with_additional_component(float(case_data["base_branch_axial_force_n"]), nad)
    connector = v11.connector_design_shear_clause_9_3_7(
        float(case_data["actual_shear_force_n"]), float(case_data["fictitious_shear_force_n"])
    )
    web_actual = v11.combined_web_relative_slenderness(
        float(case_data["effective_web_height_mm"]), float(case_data["web_thickness_mm"]),
        float(case_data["design_yield_resistance_n_mm2"]), float(case_data["elastic_modulus_n_mm2"]),
    )
    stress = v11.table_22_stress_parameters(
        float(case_data["sigma_1_n_mm2"]), float(case_data["sigma_2_n_mm2"]),
        float(case_data["average_shear_stress_n_mm2"]), float(case_data["c_cr"]),
    )
    type1 = v11.table_22_type_1_limit(
        float(case_data["member_relative_slenderness_x"]), float(case_data["relative_eccentricity_mx"]),
        float(case_data["central_compression_web_limit"]), float(case_data["bending_member_web_limit_m20"]),
    )
    type2 = v11.web_limit_eq127(
        float(stress["alpha"]), float(stress["beta"]), float(case_data["c_cr"]),
        float(case_data["design_yield_resistance_n_mm2"]), float(case_data["working_condition_factor"]),
        float(case_data["sigma_1_n_mm2"]),
    )
    type3 = v11.web_limit_eq128(type2, float(stress["alpha"]))
    type4 = v11.web_limit_eq129(
        float(case_data["member_relative_slenderness_x"]), float(case_data["flange_width_mm"]),
        float(case_data["effective_web_height_mm"]),
    )
    type5 = v11.table_22_type_5_limit(
        float(case_data["relative_eccentricity_my"]), float(case_data["central_compression_web_limit"]),
        float(case_data["gross_area_mm2"]), float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]), float(case_data["axial_force_n"]),
    )
    adjusted = v11.web_limit_adjustment_eq131(type1, type2, float(case_data["axial_stability_utilization"]))
    flange_actual = v11.combined_flange_relative_slenderness(
        float(case_data["effective_flange_outstand_mm"]), float(case_data["flange_thickness_mm"]),
        float(case_data["design_yield_resistance_n_mm2"]), float(case_data["elastic_modulus_n_mm2"]),
    )
    flange_limit = v11.table_23_limit(
        1, float(case_data["central_compression_flange_limit"]),
        float(case_data["member_relative_slenderness_x"]), float(case_data["member_relative_slenderness_y"]),
        float(case_data["relative_eccentricity_mx"]), float(case_data["bending_member_flange_limit_m20"]),
    )
    flange_edge_limit = v11.edge_return_flange_limit_clause_9_4_8(flange_limit, bool(case_data["edge_return_applicable"]))
    phi_values = [float(case_data["central_compression_phi"])]
    if whole["phi_e"] is not None:
        phi_values.append(float(whole["phi_e"]))
    two_plane_factor = v11.two_plane_limit_increase_clause_9_4_9(
        phi_values, float(case_data["gross_area_mm2"]), float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["axial_force_n"]),
    )
    result = {
        "case_id": case_data["case_id"], "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"], "engineering_calculation_performed": True, "inputs": case_data,
        "results": {
            "equation_123_relative_eccentricity_m": m,
            "clause_9_3_2_whole_member_route": whole,
            "equation_124_additional_branch_force_n": nad,
            "design_branch_compression_force_n": branch_force,
            "clause_9_3_7_connector_shear": connector,
            "actual_web_relative_slenderness": web_actual,
            "table_22_alpha": stress["alpha"], "table_22_beta": stress["beta"],
            "table_22_type_1_limit": type1, "equation_127_type_2_limit": type2,
            "equation_128_type_3_limit": type3, "equation_129_type_4_limit": type4,
            "equation_130_type_5_limit": type5, "equation_131_adjusted_web_limit": adjusted,
            "actual_web_pass_against_adjusted_limit": web_actual <= adjusted,
            "actual_flange_relative_slenderness": flange_actual,
            "table_23_type_1_limit": flange_limit,
            "clause_9_4_8_edge_return_limit": flange_edge_limit,
            "clause_9_4_9_two_plane_factor": two_plane_factor,
            "two_plane_increased_web_limit": adjusted * two_plane_factor,
            "two_plane_increased_flange_limit": flange_edge_limit * two_plane_factor,
        },
        "scope_note": "Sections 9.3-9.4 scalar formulas and normative routing are implemented. Global frame analysis, branch effective lengths, automatic section classification, Section 16, and complete connection design remain explicit external boundaries.",
    }
    _write_case_report(root, "built_up_beam_columns_and_combined_local_stability", result, "Built-up beam-column and combined local-stability case")
    return result


def _run_effective_length_guided_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the Stage N7 applicability-selected Section 10 workflow."""
    workflow=n7w.effective_length_guided_workflow(case_data)
    result={
        "case_id":case_data["case_id"],
        "standard":case_data["standard"],
        "release_stage":RELEASE_STAGE,
        "action":case_data["action"],
        "engineering_calculation_performed":workflow["status"]=="COMPLETE",
        "inputs":case_data,
        "results":workflow,
        "scope_note":"Stage N7 implements applicability-selected current-SP16 Section 10 routes. Annex И, specified crossing-brace external rules, and certified-program global analysis remain explicit provenance-gated boundaries rather than inferred formulas.",
    }
    _write_case_report(root,"effective_length_guided",result,"Stage N7 guided effective-length and limiting-slenderness case")
    return result


def _run_effective_lengths_and_limiting_slenderness_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the user-facing Section 10 example wrapper."""
    eq136=v12.truss_chord_effective_length_in_plane_eq136(float(case_data["truss_segment_length_mm"]),float(case_data["truss_adjacent_force_ratio_alpha"]))
    eq137=v12.truss_chord_effective_length_out_of_plane_eq137(float(case_data["truss_braced_length_mm"]),int(case_data["section_count_k"]),float(case_data["truss_other_force_sum_ratio_beta"]))
    eq138=v12.built_up_column_branch_effective_length_in_plane_eq138(float(case_data["column_segment_length_mm"]),float(case_data["column_adjacent_force_ratio_alpha"]))
    eq139=v12.built_up_column_branch_effective_length_out_of_plane_eq139(float(case_data["column_braced_length_mm"]),int(case_data["section_count_k"]),float(case_data["column_other_force_sum_ratio_beta"]))
    t24=v12.table_24_effective_length(case_data["table_24_case"],case_data["table_24_member_role"],float(case_data["truss_segment_length_mm"]),float(case_data["truss_braced_length_mm"]))
    t25=v12.table_25_cross_lattice_effective_length(case_data["table_25_joint_case"],case_data["table_25_supporting_state"],float(case_data["node_to_intersection_length_mm"]),float(case_data["full_member_length_mm"]))
    t26=v12.table_26_structural_member_effective_length(case_data["table_26_member_case"],float(case_data["full_member_length_mm"]),float(case_data["geometric_slenderness_l_over_i_min"]),bool(case_data["is_lattice_member"]))
    n28=v12.table_28_n_parameter(float(case_data["chord_min_inertia_mm4"]),float(case_data["diagonal_length_mm"]),float(case_data["diagonal_min_inertia_mm4"]),float(case_data["chord_panel_length_mm"]))
    l28=v12.table_28_intersection_conditional_length(case_data["table_28_joint_case"],case_data["table_28_supporting_state"],float(case_data["diagonal_length_mm"]),float(case_data["alternate_diagonal_length_mm"]),n28)
    mu29_base=v12.table_29_diagonal_length_factor(case_data["table_29_connection_case"],n28,float(case_data["geometric_slenderness_l_over_i_min"]))
    mu29=v12.table_29_end_connection_adjustment(mu29_base,case_data["table_29_gusset_configuration"])
    mu30=v12.table_30_effective_length_factor(case_data["table_30_scheme_id"])
    eq140=v12.column_effective_length_eq140(float(case_data["column_length_mm"]),mu30)
    frame_n=float(case_data["frame_n"]); frame_p=float(case_data["frame_p"])
    eq141=v12.sway_frame_mu_eq141(frame_n); eq142=v12.sway_frame_mu_eq142(frame_n)
    eq143=v12.sway_frame_mu_eq143(frame_p,frame_n) if frame_n<=0.2 else None
    eq144=v12.sway_frame_mu_eq144(frame_p,frame_n) if frame_n>0.2 else None
    eq145=v12.nonsway_frame_mu_eq145(frame_p,frame_n)
    eq146=v12.nonuniform_sway_frame_effective_length_eq146(float(case_data["base_mu"]),float(case_data["checked_column_inertia_mm4"]),float(case_data["total_column_force_n"]),float(case_data["checked_column_force_n"]),float(case_data["total_column_inertia_mm4"]))
    eq147=v12.frame_deformation_reduction_factor_eq147(float(case_data["relative_slenderness"]),float(case_data["moment_n_mm"]),float(case_data["nonsway_reference_moment_n_mm"]),float(case_data["area_mm2"]),float(case_data["axial_force_n"]),float(case_data["compressed_fibre_section_modulus_mm3"]))
    actual=v12.actual_slenderness(eq140,float(case_data["radius_of_gyration_mm"]))
    alpha=v12.compressed_limit_alpha(float(case_data["axial_force_n"]),float(case_data["stability_coefficient_phi"]),float(case_data["area_mm2"]),float(case_data["design_yield_resistance_n_mm2"]),float(case_data["working_condition_factor"]))
    limit32=v12.table_32_compressed_limiting_slenderness(case_data["table_32_row"],alpha,bool(case_data["group_4_applies"]))
    limit33=v12.table_33_tension_limiting_slenderness(case_data["table_33_row"],case_data["table_33_load_category"],bool(case_data["group_4_applies"]))
    result={
      "case_id":case_data["case_id"],"standard":case_data["standard"],"release_stage":RELEASE_STAGE,"action":case_data["action"],"engineering_calculation_performed":True,"inputs":case_data,
      "results":{
        "equation_136_truss_in_plane_effective_length_mm":eq136,"equation_137_truss_out_of_plane_effective_length_mm":eq137,"equation_138_branch_in_plane_effective_length_mm":eq138,"equation_139_branch_out_of_plane_effective_length_mm":eq139,
        "table_24_effective_length_mm":t24,"table_25_effective_length_mm":t25,"table_26_effective_length_mm":t26,"table_28_n_parameter":n28,"table_28_conditional_length_mm":l28,"table_29_base_mu_d":mu29_base,"table_29_adjusted_mu_d":mu29,
        "table_30_mu":mu30,"equation_140_column_effective_length_mm":eq140,"equation_141_mu":eq141,"equation_142_mu":eq142,"equation_143_mu":eq143,"equation_144_mu":eq144,"equation_145_mu":eq145,"equation_146_mu_effective":eq146,"equation_147_bundle":eq147,
        "actual_column_slenderness":actual,"table_32_alpha":alpha,"table_32_limiting_slenderness":limit32,"table_32_check":v12.slenderness_check(actual,limit32),"table_33_limiting_slenderness":limit33
      },
      "scope_note":"Section 10 scalar formulas, table routing, and limiting-slenderness checks are implemented. Diagram classification, global frame analysis, stepped-column Annex И calculation, elastic end-restraint formulas from the separate design rules, and certification of external software remain explicit boundaries."}
    _write_case_report(root,"effective_lengths_and_limiting_slenderness",result,"Effective lengths and limiting slenderness case")
    return result


def _run_sheet_structure_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    """Execute the Stage N8 applicability-safe Section 11 guided workflow."""
    workflow = n8w.sheet_structure_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow.get("governing_utilization") is not None,
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N8 applicability-safe current-SP16 Section 11 workflow. Exactly one shell/panel route is evaluated. "
            "Table 34 is exact-node only unless an explicitly sourced external c coefficient is supplied. Local edge effects, "
            "arbitrary spatial shell analysis and unavailable global/member checks remain explicit fail-closed dependencies."
        ),
    }
    _write_case_report(root, "sheet_structure_guided", result, "Stage N8 guided sheet-structure case")
    return result


def _run_sheet_structures_strength_and_stability_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the user-facing Section 11 sheet-structure example wrapper."""
    gamma=float(case_data["working_condition_factor"]); ry=float(case_data["design_yield_resistance_n_mm2"]); e=float(case_data["elastic_modulus_n_mm2"])
    sx=float(case_data["sigma_x_n_mm2"]); sy=float(case_data["sigma_y_n_mm2"]); tau=float(case_data["tau_xy_n_mm2"])
    eq148=v13.membrane_strength_utilization_eq148(sx,sy,tau,ry,gamma)
    principal=v13.principal_stress_resistance_check_clause_11_1_1(sx,sy,tau,float(case_data["tension_design_resistance_n_mm2"]),float(case_data["compression_design_resistance_n_mm2"]),gamma)
    r=float(case_data["shell_radius_mm"]); t=float(case_data["shell_thickness_mm"]); beta=float(case_data["beta_degrees"]); p=float(case_data["pressure_n_mm2"])
    eq149=v13.meridional_stress_eq149(float(case_data["projected_pressure_force_n"]),r,t,beta)
    eq150=v13.circumferential_stress_eq150(p,t,eq149,float(case_data["meridional_radius_mm"]),float(case_data["circumferential_radius_mm"]))
    eq151=v13.cylindrical_internal_pressure_stresses_eq151(p,r,t)
    eq152=v13.spherical_internal_pressure_stresses_eq152(p,r,t)
    eq153=v13.conical_internal_pressure_stresses_eq153(p,r,t,beta)
    axial_critical=v13.cylindrical_axial_critical_stress(r,t,ry,e)
    axial_stress=float(case_data["cylinder_axial_compressive_stress_n_mm2"])
    eq154=v13.cylindrical_axial_stability_utilization_eq154(axial_stress,float(axial_critical["critical_stress_n_mm2"]),gamma)
    eccentric_adjust=v13.eccentric_compression_critical_stress_multiplier_clause_11_2_1(axial_stress,float(case_data["cylinder_minimum_signed_stress_n_mm2"]),float(case_data["cylinder_shear_stress_n_mm2"]),e,r,t)
    tube_route=v13.tube_local_stability_route_clause_11_2_2(float(case_data["tube_radius_mm"]),float(case_data["tube_thickness_mm"]),ry,e,float(case_data["tube_relative_slenderness"]))
    tube_scr={"critical_stress_n_mm2":float(case_data["tube_axial_critical_stress_n_mm2"]),"source":"explicit audited input because Table 34 has no printed node at the selected r/t"}
    eq156=v13.tube_local_stability_utilization_eq156(float(case_data["tube_axial_force_n"]),float(case_data["tube_relative_slenderness"]),float(case_data["tube_area_mm2"]),float(case_data["tube_relative_eccentricity_m"]),ry,float(tube_scr["critical_stress_n_mm2"]),float(case_data["tube_radius_mm"]),float(case_data["tube_thickness_mm"]),e)
    panel_limit=v13.cylindrical_panel_limit(float(case_data["panel_compressive_stress_n_mm2"]),ry,e)
    panel_route=v13.cylindrical_panel_route_clause_11_2_3(float(case_data["panel_width_mm"]),r,t)
    er=float(case_data["external_cylinder_radius_mm"]); et=float(case_data["external_cylinder_thickness_mm"]); el=float(case_data["external_cylinder_length_mm"]); ep=float(case_data["external_pressure_n_mm2"])
    ext_critical=v13.cylindrical_external_pressure_critical_stress(e,er,el,et)
    hoop_stress=ep*er/et
    eq159=v13.cylindrical_external_pressure_utilization_eq159(hoop_stress,float(ext_critical["critical_stress_n_mm2"]),gamma)
    ring=v13.ring_stiffener_requirements_clause_11_2_4(ep,er,float(case_data["ring_spacing_mm"]),et,e,ry)
    eq162=v13.cylindrical_combined_stability_utilization_eq162(axial_stress,float(axial_critical["critical_stress_n_mm2"]),hoop_stress,float(ext_critical["critical_stress_n_mm2"]),gamma)
    cr1=float(case_data["cone_top_radius_mm"]); cr2=float(case_data["cone_bottom_radius_mm"]); ch=float(case_data["cone_height_mm"]); ct=float(case_data["cone_thickness_mm"])
    rm=v13.conical_equivalent_radius_eq165(cr1,cr2,beta)
    cone_axial_critical=v13.cylindrical_axial_critical_stress(rm,ct,ry,e)
    ncr=v13.conical_critical_force_eq164(ct,float(cone_axial_critical["critical_stress_n_mm2"]),rm,beta)
    eq163=v13.conical_axial_stability_utilization_eq163(float(case_data["cone_axial_force_n"]),ncr,gamma)
    cone_p=float(case_data["cone_external_pressure_n_mm2"]); cone_sigma2=cone_p*rm/ct
    cone_cr2=v13.conical_external_pressure_critical_stress_eq167(e,rm,ch,ct)
    eq166=v13.conical_external_pressure_utilization_eq166(cone_sigma2,cone_cr2,gamma)
    eq168=v13.conical_combined_stability_utilization_eq168(float(case_data["cone_axial_force_n"]),ncr,cone_sigma2,cone_cr2,gamma)
    sr=float(case_data["sphere_radius_mm"]); st=float(case_data["sphere_thickness_mm"]); sp=float(case_data["sphere_external_pressure_n_mm2"])
    sphere_cr=v13.spherical_external_pressure_critical_stress_clause_11_2_9(e,sr,st,ry)
    eq169=v13.spherical_external_pressure_utilization_eq169(sp,sr,st,sphere_cr,gamma)
    analysis_route=v13.shell_analysis_route_clause_11_1_4_11_1_5(bool(case_data["has_geometry_thickness_or_load_discontinuity"]),bool(case_data["arbitrary_configuration_or_spatial_state"]))
    result={
      "case_id":case_data["case_id"],"standard":case_data["standard"],"release_stage":RELEASE_STAGE,"action":case_data["action"],"engineering_calculation_performed":True,"inputs":case_data,
      "results":{
        "equation_148_utilization":eq148,"equation_148_pass":eq148<=1.0,"principal_stress_check":principal,
        "equation_149_meridional_stress_n_mm2":eq149,"equation_150_circumferential_stress_n_mm2":eq150,
        "equation_151_cylinder_stresses_n_mm2":list(eq151),"equation_152_sphere_stresses_n_mm2":list(eq152),"equation_153_cone_stresses_n_mm2":list(eq153),
        "table_34_axial_critical_bundle":axial_critical,"equation_154_utilization":eq154,"equation_154_pass":eq154<=1.0,"eccentric_compression_adjustment":eccentric_adjust,
        "tube_route":tube_route,"tube_critical_bundle":tube_scr,"equation_156_utilization":eq156,"equation_156_pass":eq156<=1.0,
        "panel_limit_bundle":panel_limit,"panel_route":panel_route,
        "external_pressure_critical_bundle":ext_critical,"equation_159_utilization":eq159,"equation_159_pass":eq159<=1.0,"ring_stiffener_requirements":ring,
        "equation_162_combined_cylinder_utilization":eq162,"equation_162_pass":eq162<=1.0,
        "equation_165_equivalent_cone_radius_mm":rm,"cone_axial_critical_bundle":cone_axial_critical,"equation_164_cone_critical_force_n":ncr,"equation_163_utilization":eq163,"equation_163_pass":eq163<=1.0,
        "equation_167_cone_critical_hoop_stress_n_mm2":cone_cr2,"equation_166_utilization":eq166,"equation_166_pass":eq166<=1.0,"equation_168_combined_cone_utilization":eq168,"equation_168_pass":eq168<=1.0,
        "sphere_critical_stress_n_mm2":sphere_cr,"equation_169_utilization":eq169,"equation_169_pass":eq169<=1.0,"clauses_11_1_4_11_1_5_route":analysis_route
      },
      "scope_note":"Section 11 scalar membrane-strength and shell-stability formulas are implemented. Local edge effects, arbitrary shell finite-element analysis, automatic geometry classification, global member stability, and complete ring-stiffener section design remain explicit external boundaries."}
    _write_case_report(root,"sheet_structures_strength_and_stability",result,"Sheet-structure strength and stability case")
    return result


def _run_fatigue_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    """Execute the Stage N9 applicability-safe current-SP16 Section 12 guided workflow."""
    workflow = n9w.fatigue_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow["status"] == "COMPLETE",
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N9 applicability-safe current-SP16 Section 12 workflow. Exactly one ordinary-fatigue, crane-runway, "
            "or low-cycle boundary route is evaluated. Change No. 6 exclusion of clause 12.1.3 is explicit; no replacement "
            "low-cycle formula, SP20 load derivation, stress-history extraction, cumulative-damage rule, or automatic Annex-K "
            "detail recognition is invented."
        ),
    }
    _write_case_report(root, "fatigue_guided", result, "Stage N9 guided fatigue case")
    return result


def _run_fatigue_design_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the user-facing Section 12 fatigue-design example wrapper."""
    route = v14.fatigue_applicability_route_clause_12_1_1_12_1_3(
        float(case_data["load_cycles"]), bool(case_data["resonant_vortex_excitation"])
    )
    group = v14.annex_k_group(case_data["annex_k_case_id"])
    resistance = v14.fatigue_design_resistance_table35(
        group, float(case_data["normative_ultimate_resistance_n_mm2"])
    )
    alpha = v14.fatigue_cycle_factor_alpha(float(case_data["load_cycles"]), group)
    maximum_signed = float(case_data["maximum_signed_stress_n_mm2"])
    minimum_signed = float(case_data["minimum_signed_stress_n_mm2"])
    rho = v14.stress_asymmetry_ratio(maximum_signed, minimum_signed)
    gamma_v = v14.fatigue_asymmetry_factor_table36(maximum_signed, minimum_signed)
    eq170 = v14.fatigue_utilization_eq170(abs(maximum_signed), alpha, resistance, gamma_v)
    cap = v14.fatigue_resistance_cap_check_clause_12_1_2(
        alpha, resistance, gamma_v,
        float(case_data["design_ultimate_resistance_n_mm2"]),
        float(case_data["ultimate_resistance_safety_factor"]),
    )
    crane_alpha = v14.crane_runway_cycle_factor_clause_12_2(
        case_data["crane_group"], bool(case_data["crane_in_metallurgical_shop"])
    )
    crane_resistance = v14.crane_runway_web_fatigue_resistance_clause_12_2(
        case_data["crane_flange_connection_type"], case_data["crane_web_zone_state"]
    )
    eq173 = v14.crane_runway_web_fatigue_utilization_eq173(
        float(case_data["crane_sigma_x_n_mm2"]),
        float(case_data["crane_sigma_xy_n_mm2"]),
        float(case_data["crane_local_sigma_y_n_mm2"]),
        float(case_data["crane_flange_sigma_y_n_mm2"]),
        crane_resistance,
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "fatigue_applicability_route": route,
            "annex_k_case_id": case_data["annex_k_case_id"],
            "annex_k_element_group": group,
            "table_35_fatigue_resistance_n_mm2": resistance,
            "cycle_factor_alpha": alpha,
            "stress_asymmetry_ratio_rho": rho,
            "table_36_asymmetry_factor_gamma_v": gamma_v,
            "equation_170_utilization": eq170,
            "equation_170_pass": eq170 <= 1.0 and bool(cap["pass"]),
            "fatigue_resistance_cap_check": cap,
            "clause_12_2_crane_cycle_factor_alpha": crane_alpha,
            "clause_12_2_crane_web_fatigue_resistance_n_mm2": crane_resistance,
            "equation_173_utilization": eq173,
            "equation_173_pass": eq173 <= 1.0,
        },
        "scope_note": (
            "Section 12 equations (170)-(173), Tables 35-36, and Annex K Table K.1 are implemented. "
            "Load derivation under SP 20.13330, stress-history extraction, low-cycle fatigue, cumulative "
            "damage for variable-amplitude spectra, and automatic detail recognition remain external boundaries."
        ),
    }
    _write_case_report(root, "fatigue_design", result, "Fatigue-design case")
    return result




def _run_brittle_fracture_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    """Execute the Stage N10 applicability-safe current-SP16 Section 13 guided workflow."""
    workflow = n10w.brittle_fracture_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow["status"] == "COMPLETE",
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N10 applicability-safe current-SP16 Section 13 workflow. Clause 13.2 conditional detailing/NDT obligations, "
            "clause 13.3 engineering applicability, clause 13.4 evidence, equation (174), Table 37 and Z-quality routing are explicit. "
            "No drawing recognition, material-certificate inference, NDT interpretation, or unstated lamellar-tearing rule is invented."
        ),
    }
    _write_case_report(root, "brittle_fracture_guided", result, "Stage N10 guided brittle-fracture case")
    return result

def _run_brittle_fracture_and_welded_connections_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Execute the user-facing Sections 13 and 14.1 example wrapper."""
    psi_zf = v15.table_37_connection_form_factor(case_data["connection_form_case"])
    psi_zt = v15.table_37_plate_thickness_factor(float(case_data["plate_thickness_mm"]))
    psi_zsh = v15.table_37_weld_leg_factor(float(case_data["risk_weld_leg_mm"]))
    psi_zj = v15.table_37_restraint_factor(case_data["restraint_level"])
    psi_zs = v15.table_37_welding_technology_factor(
        case_data["pass_count"], case_data["weld_sequence"], case_data["preheat"]
    )
    eq174 = v15.lamellar_tearing_risk_sum_eq174(psi_zf, psi_zt, psi_zsh, psi_zj, psi_zs)
    adjusted = v15.lamellar_tearing_adjusted_risk_clause_13_5(eq174, case_data["through_thickness_action"])
    required_z = v15.required_z_quality_group_clause_13_5(
        int(case_data["construction_group"]), case_data["consequence_class"],
        bool(case_data["flange_connection_or_normal_force"]),
    )
    selected_z_check = v15.lamellar_tearing_check_clause_13_5(adjusted, case_data["selected_z_quality_group"])
    table38 = v15.minimum_fillet_weld_leg_table38(
        case_data["table38_connection_type"], float(case_data["thicker_element_thickness_mm"]),
        float(case_data["thinner_element_thickness_mm"]), float(case_data["steel_yield_strength_n_mm2"]),
    )
    table39 = v15.table_39_fillet_weld_coefficients(
        case_data["table39_welding_process"], case_data["table39_weld_position"],
        float(case_data["fillet_weld_leg_mm"]),
    )
    beta_f=float(table39["beta_f"]); beta_z=float(table39["beta_z"]); gamma=float(case_data["working_condition_factor"])
    butt_length = v15.effective_butt_weld_length_clause_14_1_14(
        float(case_data["butt_full_length_mm"]), float(case_data["butt_thickness_mm"]),
        bool(case_data["butt_runout_tabs_used"]),
    )
    eq175 = v15.butt_weld_axial_utilization_eq175(
        float(case_data["butt_axial_force_n"]), float(case_data["butt_thickness_mm"]), butt_length,
        float(case_data["butt_design_resistance_n_mm2"]), gamma,
    )
    butt_combined = v15.butt_weld_combined_stress_clause_14_1_15(
        float(case_data["butt_sigma_x_n_mm2"]), float(case_data["butt_sigma_y_n_mm2"]),
        float(case_data["butt_tau_xy_n_mm2"]), float(case_data["butt_yield_resistance_n_mm2"]),
        float(case_data["butt_shear_resistance_n_mm2"]), gamma,
    )
    fillet_length = v15.fillet_weld_effective_length_clause_14_1_16(
        [float(value) for value in case_data["fillet_segment_lengths_mm"]]
    )
    eq176 = v15.fillet_weld_axial_metal_utilization_eq176(
        float(case_data["fillet_axial_force_n"]), beta_f, float(case_data["fillet_weld_leg_mm"]), fillet_length,
        float(case_data["weld_metal_resistance_n_mm2"]), gamma,
    )
    eq177 = v15.fillet_weld_axial_fusion_utilization_eq177(
        float(case_data["fillet_axial_force_n"]), beta_z, float(case_data["fillet_weld_leg_mm"]), fillet_length,
        float(case_data["fusion_boundary_resistance_n_mm2"]), gamma,
    )
    eq178 = v15.fillet_weld_out_of_plane_moment_metal_utilization_eq178(
        float(case_data["fillet_out_of_plane_moment_n_mm"]), float(case_data["weld_metal_section_modulus_mm3"]),
        float(case_data["weld_metal_resistance_n_mm2"]), gamma,
    )
    eq179 = v15.fillet_weld_out_of_plane_moment_fusion_utilization_eq179(
        float(case_data["fillet_out_of_plane_moment_n_mm"]), float(case_data["fusion_section_modulus_mm3"]),
        float(case_data["fusion_boundary_resistance_n_mm2"]), gamma,
    )
    eq180 = v15.fillet_weld_in_plane_moment_metal_utilization_eq180(
        float(case_data["fillet_in_plane_moment_n_mm"]), float(case_data["weld_x_mm"]), float(case_data["weld_y_mm"]),
        float(case_data["weld_metal_inertia_x_mm4"]), float(case_data["weld_metal_inertia_y_mm4"]),
        float(case_data["weld_metal_resistance_n_mm2"]), gamma,
    )
    eq181 = v15.fillet_weld_in_plane_moment_fusion_utilization_eq181(
        float(case_data["fillet_in_plane_moment_n_mm"]), float(case_data["weld_x_mm"]), float(case_data["weld_y_mm"]),
        float(case_data["fusion_inertia_x_mm4"]), float(case_data["fusion_inertia_y_mm4"]),
        float(case_data["fusion_boundary_resistance_n_mm2"]), gamma,
    )
    resultant = v15.resultant_shear_stress_eq183(
        float(case_data["tau_n_n_mm2"]), float(case_data["tau_mx_n_mm2"]),
        float(case_data["tau_v_n_mm2"]), float(case_data["tau_my_n_mm2"]),
    )
    eq182 = v15.combined_fillet_weld_utilizations_eq182(
        resultant, resultant, float(case_data["weld_metal_resistance_n_mm2"]),
        float(case_data["fusion_boundary_resistance_n_mm2"]), gamma,
    )
    spot = v15.spot_weld_governing_capacity_clause_14_1_20(
        float(case_data["spot_first_thickness_mm"]), float(case_data["spot_second_thickness_mm"]),
        float(case_data["spot_diameter_mm"]), float(case_data["normative_weld_metal_ultimate_resistance_n_mm2"]),
        float(case_data["normative_connected_steel_ultimate_resistance_n_mm2"]),
    )
    result = {
        "case_id": case_data["case_id"], "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"], "engineering_calculation_performed": True, "inputs": case_data,
        "results": {
            "table_37_factors_percent": {"psi_zf":psi_zf,"psi_zt":psi_zt,"psi_zsh":psi_zsh,"psi_zj":psi_zj,"psi_zs":psi_zs},
            "equation_174_base_risk_percent": eq174, "adjusted_lamellar_tearing_risk_percent": adjusted,
            "required_z_quality_group": required_z, "selected_z_quality_check": selected_z_check,
            "table_38_minimum_fillet_weld": table38, "table_39_coefficients": table39,
            "butt_weld_effective_length_mm": butt_length, "equation_175_utilization": eq175, "equation_175_pass": eq175<=1.0,
            "butt_weld_combined_stress_check": butt_combined, "fillet_weld_effective_length_mm": fillet_length,
            "equation_176_utilization": eq176, "equation_177_utilization": eq177,
            "equation_178_utilization": eq178, "equation_179_utilization": eq179,
            "equation_180_utilization": eq180, "equation_181_utilization": eq181,
            "equation_183_resultant_shear_n_mm2": resultant, "equation_182_combined_check": eq182,
            "spot_weld_equations_184_185": spot,
        },
        "scope_note": (
            "Sections 13 and 14.1 are implemented for the audited risk-factor, detailing-route, butt-weld, "
            "fillet-weld, and arc spot-weld checks. Steel selection, fracture-mechanics assessment, NDT evidence, "
            "automatic detail recognition, weld procedure qualification, and global load derivation remain external boundaries."
        ),
    }
    _write_case_report(root, "brittle_fracture_and_welded_connections", result,
                       "Brittle-fracture and welded-connection case")
    return result


def _run_bolted_and_friction_connections_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    if not case_data["sections_14_2_and_14_3_applicability_confirmed"]:
        raise ValueError("Clauses 14.2-14.3 applicability must be confirmed")
    hole_d = v16.table_40_hole_diameter(
        float(case_data["bolt_diameter_mm"]), case_data["accuracy_class"],
        overhead_line_switchyard_or_contact_network=case_data["special_class_b_structure"],
        clearance_mm=float(case_data["hole_clearance_mm"]),
    )
    distances = v16.table_40_distance_requirements(
        hole_d, float(case_data["outer_element_thickness_mm"]),
        float(case_data["connected_steel_normative_yield_resistance_n_mm2"]),
        friction_connection=case_data["layout_is_friction_connection"],
        friction_planes=int(case_data["layout_friction_planes"]),
        edge_type=case_data["edge_type"], stress_state=case_data["stress_state"],
        row_location=case_data["row_location"],
        transverse_row_spacing_mm=float(case_data["transverse_row_spacing_mm"]),
    )
    layout = v16.table_40_check_layout(
        float(case_data["actual_center_spacing_mm"]),
        float(case_data["actual_edge_along_force_mm"]),
        float(case_data["actual_edge_transverse_force_mm"]), distances,
        friction_connection=case_data["layout_is_friction_connection"],
    )
    gamma_b = v16.table_41_connection_factor(
        case_data["accuracy_class"], multi_bolt=case_data["multi_bolt_connection"],
        bearing_geometry=case_data["bearing_geometry"],
        interpolation_fraction=case_data.get("bearing_interpolation_fraction"),
    )
    nbs = v16.bolt_shear_capacity_eq186(
        float(case_data["bolt_shear_resistance_n_mm2"]), float(case_data["gross_bolt_area_mm2"]),
        int(case_data["shear_planes"]), gamma_b, float(case_data["working_condition_factor"]),
    )
    nbp = v16.bolt_bearing_capacity_eq187(
        float(case_data["bearing_resistance_n_mm2"]), float(case_data["bolt_diameter_mm"]),
        float(case_data["summed_bearing_thickness_mm"]), gamma_b, float(case_data["working_condition_factor"]),
    )
    nbt = v16.bolt_tension_capacity_eq188(
        float(case_data["bolt_tension_resistance_n_mm2"]), float(case_data["net_thread_area_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    beta = v16.long_joint_reduction_factor_14_2_10(
        float(case_data["joint_length_along_shear_mm"]), hole_d,
        load_applied_over_full_length=case_data["load_applied_over_full_joint_length"],
    )
    bolt_count = v16.required_bolt_count_eq189(
        float(case_data["bolted_connection_design_force_n"]), nbs, nbp, nbt,
        applicable_modes=case_data["bolted_applicable_modes"], long_joint_reduction_factor=beta,
    )
    group = v16.bolt_group_force_distribution_14_2_11_12(
        case_data["bolt_coordinates_mm"], float(case_data["group_force_x_n"]),
        float(case_data["group_force_y_n"]), float(case_data["group_moment_z_n_mm"]),
    )
    eq190 = v16.bolt_shear_tension_interaction_eq190(
        float(case_data["combined_bolt_shear_force_n"]), float(case_data["combined_bolt_tension_force_n"]), nbs, nbt
    )
    adjusted_count = v16.bolt_count_detailing_adjustment_14_2_14(bolt_count["required_bolts"],case_data["connection_detail"])
    friction_params = v16.table_42_friction_parameters(
        case_data["surface_treatment"],case_data["tightening_control"],case_data["friction_load_type"],
        float(case_data["friction_hole_clearance_mm"]),
    )
    qbh = v16.friction_plane_capacity_eq191(
        float(case_data["bolt_tension_resistance_n_mm2"]),float(case_data["net_thread_area_mm2"]),
        friction_params["friction_coefficient"],friction_params["gamma_h"],
    )
    friction_count = v16.required_friction_bolt_count_eq192(
        float(case_data["friction_design_shear_force_n"]),qbh,int(case_data["friction_planes"]),
        float(case_data["working_condition_factor"]),
    )
    tensile_reduction = v16.friction_tension_reduction_14_3_6(
        friction_count["connection_factor_gamma_b"],float(case_data["friction_tension_force_per_bolt_n"]),
        float(case_data["bolt_tension_resistance_n_mm2"]),float(case_data["net_thread_area_mm2"]),
    )
    diameter = v16.friction_bolt_diameter_check_14_3_7(
        float(case_data["friction_summed_shifted_thickness_mm"]),float(case_data["bolt_diameter_mm"]),
    )
    washer = v16.friction_connection_washer_requirement_14_3_10(
        float(case_data["friction_hole_clearance_mm"]),float(case_data["connected_steel_ultimate_resistance_n_mm2"]),
        enlarged_head_and_nut=case_data["enlarged_head_and_nut"],
    )
    area = v16.friction_connection_effective_area_14_3_11(
        float(case_data["gross_connected_area_mm2"]),float(case_data["net_connected_area_mm2"]),case_data["friction_load_type"]
    )
    result={
        "case_id":case_data["case_id"],"standard":case_data["standard"],"release_stage":RELEASE_STAGE,
        "action":case_data["action"],"engineering_calculation_performed":True,"inputs":case_data,
        "results":{
            "table_40_hole_diameter_mm":hole_d,"table_40_requirements":distances,"table_40_layout_check":layout,
            "table_41_gamma_b":gamma_b,"equation_186_shear_capacity_n":nbs,"equation_187_bearing_capacity_n":nbp,
            "equation_188_tension_capacity_n":nbt,"long_joint_beta":beta,"equation_189_bolt_count":bolt_count,
            "bolt_group_distribution":group,"equation_190_utilization":eq190,"equation_190_pass":eq190<=1.0,
            "clause_14_2_14_adjusted_count":adjusted_count,"table_42_parameters":friction_params,
            "equation_191_capacity_per_friction_plane_n":qbh,"equation_192_friction_bolt_count":friction_count,
            "clause_14_3_6_tension_reduction":tensile_reduction,"clause_14_3_7_diameter_check":diameter,
            "clause_14_3_10_washer":washer,"clause_14_3_11_selected_area":area,
            "external_requirements":v16.bolted_and_friction_external_requirements(),
        },
        "scope_note":"Clauses 14.2-14.3, equations (186)-(192), and Tables 40-42 are implemented. Product standards, anchor design, installation verification, CAD recognition, and global load derivation remain external boundaries.",
    }
    _write_case_report(root,"bolted_and_friction_connections",result,"Bolted and friction-connection case")
    return result



def _run_built_up_beam_flange_connections_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    if not case_data["clause_14_4_applicability_confirmed"]:
        raise ValueError("Clause 14.4 applicability must be confirmed")

    shear_flow = v17.flange_shear_flow_t_n_mm(
        float(case_data["transverse_shear_force_n"]),
        float(case_data["flange_static_moment_mm3"]),
        float(case_data["gross_section_moment_inertia_mm4"]),
    )
    local_pressure = v17.local_load_line_pressure_v_n_mm(
        float(case_data["load_factor_gamma_f"]),
        float(case_data["local_load_factor_gamma_f1"]),
        float(case_data["concentrated_load_n"]),
        float(case_data["effective_distribution_length_mm"]),
    )
    route = v17.table_43_load_route(
        case_data["nominal_load_character"],
        case_data["loaded_flange"],
        transverse_stiffener_at_load=case_data["transverse_stiffener_at_load"],
    )
    alpha = v17.table_43_alpha(
        case_data["loaded_flange"],
        web_edge_planed_to_loaded_upper_flange=case_data["web_edge_planed_to_loaded_upper_flange"],
    )

    eq193 = v17.stationary_weld_metal_utilization_eq193(
        shear_flow,
        int(case_data["weld_line_count"]),
        float(case_data["weld_coefficient_beta_f"]),
        float(case_data["weld_leg_mm"]),
        float(case_data["weld_metal_design_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq194 = v17.stationary_fusion_boundary_utilization_eq194(
        shear_flow,
        int(case_data["weld_line_count"]),
        float(case_data["weld_coefficient_beta_z"]),
        float(case_data["weld_leg_mm"]),
        float(case_data["fusion_boundary_design_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq195 = v17.stationary_friction_utilization_eq195(
        shear_flow,
        float(case_data["bolt_pitch_mm"]),
        float(case_data["friction_plane_capacity_n"]),
        int(case_data["friction_plane_count"]),
        float(case_data["working_condition_factor"]),
    )
    eq196 = v17.moving_weld_metal_utilization_eq196(
        shear_flow,
        local_pressure,
        float(case_data["weld_coefficient_beta_f"]),
        float(case_data["weld_leg_mm"]),
        float(case_data["weld_metal_design_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq197 = v17.moving_fusion_boundary_utilization_eq197(
        shear_flow,
        local_pressure,
        float(case_data["weld_coefficient_beta_z"]),
        float(case_data["weld_leg_mm"]),
        float(case_data["fusion_boundary_design_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    eq198 = v17.moving_friction_utilization_eq198(
        shear_flow,
        local_pressure,
        alpha,
        float(case_data["bolt_pitch_mm"]),
        float(case_data["friction_plane_capacity_n"]),
        int(case_data["friction_plane_count"]),
        float(case_data["working_condition_factor"]),
    )
    penetration = v17.full_penetration_web_weld_equivalence_14_4_1(
        case_data["full_penetration_through_web_thickness"]
    )
    multilayer = v17.multilayer_flange_sheet_attachment_force_14_4_2(
        float(case_data["sheet_section_force_capacity_n"]),
        case_data["attachment_segment"],
    )

    if route["effective_load_character"] == "stationary":
        applicable_weld_equations = ["193", "194"]
        applicable_friction_equations = ["195"]
        governing_weld = max(eq193, eq194)
        governing_friction = eq195
    else:
        applicable_weld_equations = ["196", "197"]
        applicable_friction_equations = ["198"]
        governing_weld = max(eq196, eq197)
        governing_friction = eq198

    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "table_43_route": route,
            "table_43_alpha": alpha,
            "flange_shear_flow_t_n_mm": shear_flow,
            "local_pressure_v_n_mm": local_pressure,
            "equation_193_utilization": eq193,
            "equation_193_pass": eq193 <= 1.0,
            "equation_194_utilization": eq194,
            "equation_194_pass": eq194 <= 1.0,
            "equation_195_utilization": eq195,
            "equation_195_pass": eq195 <= 1.0,
            "equation_196_utilization": eq196,
            "equation_196_pass": eq196 <= 1.0,
            "equation_197_utilization": eq197,
            "equation_197_pass": eq197 <= 1.0,
            "equation_198_utilization": eq198,
            "equation_198_pass": eq198 <= 1.0,
            "applicable_weld_equations": applicable_weld_equations,
            "applicable_friction_equations": applicable_friction_equations,
            "governing_applicable_weld_utilization": governing_weld,
            "governing_applicable_weld_pass": governing_weld <= 1.0,
            "governing_applicable_friction_utilization": governing_friction,
            "governing_applicable_friction_pass": governing_friction <= 1.0,
            "full_penetration_weld_classification": penetration,
            "multilayer_flange_sheet_attachment": multilayer,
            "table_43_catalog": v17.table_43_catalog(),
        },
        "scope_note": (
            "Clause 14.4, equations (193)-(198), and Table 43 are implemented. "
            "Global force derivation, weld inspection, transverse-stiffener capacity, bolt-layout design, "
            "cutoff-point location, and CAD/BIM recognition remain external boundaries."
        ),
    }
    _write_case_report(
        root,
        "built_up_beam_flange_connections",
        result,
        "Built-up beam flange-connection case",
    )
    return result

def _run_structural_detailing_and_support_bearings_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    spacing = v18.temperature_joint_spacing_assessment_15_1(
        float(case_data["actual_temperature_block_distance_m"]),
        case_data["building_type"],
        case_data["direction"],
        float(case_data["design_air_temperature_c"]),
        case_data["frame_stiffness_increased_by_walls_or_other_structures"],
    )
    paired_limit = v18.paired_vertical_bracing_max_spacing_m_15_1(
        "open_trestle" if case_data["building_type"] == "open_trestle" else "building",
        float(case_data["design_air_temperature_c"]),
    )
    paired_actual = float(case_data["paired_vertical_brace_axis_spacing_m"])
    paired_present = case_data["paired_vertical_braces_present"]
    paired_check = {
        "applicable": paired_present,
        "maximum_axis_spacing_m": paired_limit if paired_present else None,
        "actual_axis_spacing_m": paired_actual if paired_present else None,
        "pass": (paired_actual <= paired_limit) if paired_present else None,
    }
    selection = v18.support_bearing_selection_15_12_1(
        case_data["strict_uniform_pressure_distribution_required"],
        case_data["reaction_class"],
        case_data["relieve_substructure_from_horizontal_forces"],
    )
    friction = v18.support_bearing_friction_coefficient_15_12_1(case_data["movable_bearing_type"])
    hinge = v18.cylindrical_hinge_bearing_check_15_12_2(
        float(case_data["support_force_n"]),
        float(case_data["hinge_contact_central_angle_deg"]),
        float(case_data["hinge_radius_mm"]),
        float(case_data["hinge_length_mm"]),
        float(case_data["local_bearing_design_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    roller = v18.roller_bearing_check_15_12_3(
        float(case_data["support_force_n"]),
        int(case_data["roller_count"]),
        float(case_data["roller_diameter_mm"]),
        float(case_data["roller_length_mm"]),
        float(case_data["roller_diametral_compression_resistance_n_mm2"]),
        float(case_data["working_condition_factor"]),
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "temperature_joint_spacing_assessment": spacing,
            "paired_vertical_bracing_spacing_assessment": paired_check,
            "support_bearing_selection": selection,
            "movable_bearing_friction_coefficient": friction,
            "equation_199_cylindrical_hinge": hinge,
            "equation_200_roller_bearing": roller,
            "table_44_catalog": v18.table_44_catalog(),
            "section_15_requirement_classification_summary": v18.section_15_requirement_catalog()["summary"],
        },
        "scope_note": (
            "Section 15 requirements are classified by execution route. Table 44, clause 15.12.1 fixed coefficients, "
            "and equations (199)-(200) are executable. The remaining detailing clauses require drawing evidence, "
            "linked checks, or external structural analysis as recorded in the Section 15 catalogue."
        ),
    }
    _write_case_report(root, "structural_detailing_and_support_bearings", result, "Structural detailing and support-bearing case")
    return result


def _run_overhead_line_and_switchyard_supports_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    applicability = v19.section_16_applicability_route(case_data["structure_case"])
    gamma_c_45 = v19.table_45_working_condition_factor(
        case_data["table_45_case_id"],
        applied_to_node_connection=case_data["table_45_applied_to_node_connection"],
    )
    eq201 = v19.maximum_slenderness_eq201(float(case_data["length_mm"]), float(case_data["chord_axis_spacing_mm"]))
    eq202 = v19.maximum_slenderness_eq202(float(case_data["length_mm"]), float(case_data["chord_axis_spacing_mm"]))
    pyramidal_mu = v19.pyramidal_effective_length_factor_clause_16_5(
        float(case_data["upper_spacing_mm"]), float(case_data["lower_spacing_mm"])
    )
    eq203 = v19.maximum_slenderness_eq203(
        float(case_data["height_mm"]), float(case_data["upper_spacing_mm"]), float(case_data["lower_spacing_mm"])
    )
    eq204 = v19.relative_eccentricity_eq204(
        float(case_data["moment_n_mm"]), float(case_data["axial_force_n"]),
        float(case_data["chord_axis_spacing_mm"]), float(case_data["connection_beta"]),
    )
    eq205 = v19.relative_eccentricity_eq205(
        float(case_data["moment_n_mm"]), float(case_data["axial_force_n"]),
        float(case_data["chord_axis_spacing_mm"]), float(case_data["connection_beta"]),
    )
    auxiliaries = v19.guyed_support_second_order_auxiliaries(
        float(case_data["length_mm"]), float(case_data["area_mm2"]),
        float(case_data["reduced_slenderness"]), float(case_data["axial_force_n"]),
        float(case_data["elastic_modulus_n_mm2"]),
    )
    eq206 = v19.guyed_rectangular_moment_eq206(
        float(case_data["first_order_midspan_moment_n_mm"]), float(case_data["connection_beta"]),
        float(case_data["axial_force_n"]), auxiliaries["delta"],
        float(case_data["transverse_deflection_mm"]), auxiliaries["initial_bow_mm"],
    )
    eq207 = v19.guyed_rectangular_shear_eq207(
        float(case_data["first_order_max_shear_n"]), float(case_data["connection_beta"]),
        float(case_data["axial_force_n"]), auxiliaries["delta"], float(case_data["length_mm"]),
        float(case_data["transverse_deflection_mm"]), auxiliaries["initial_bow_mm"],
    )
    eq208 = v19.triangular_additional_chord_force_eq208(
        float(case_data["moment_x_n_mm"]), float(case_data["moment_y_n_mm"]),
        float(case_data["chord_axis_spacing_mm"]),
    )
    angle_factors = v19.angle_member_eccentricity_factors_clause_16_12(
        case_data["angle_member"], case_data["angle_connection"], float(case_data["c_over_b"]),
        float(case_data["reduced_slenderness"]), float(case_data["n_md_over_n_m"]),
        bolt_line_ratio=float(case_data["brace_bolt_line_ratio"]),
        figure_15_g_or_d=case_data["figure_15_g_or_d"],
        welded_centering=case_data["welded_centering"],
        broken_wire_combination=case_data["broken_wire_combination"],
    )
    table_46 = v19.table_46_deformation_check(
        case_data["table_46_row_id"], case_data["table_46_measure"],
        float(case_data["actual_relative_deformation"]), load_mode=case_data["table_46_load_mode"],
    )
    detailing = v19.section_16_detailing_checks(
        traverse_member=case_data["traverse_member"], panel_length_mm=float(case_data["panel_length_mm"]),
        alternate_chord_length_mm=float(case_data["alternate_chord_length_mm"]),
        actual_first_lower_brace_slenderness=float(case_data["actual_first_lower_brace_slenderness"]),
        support_system=case_data["support_system"], actual_diaphragm_spacing_m=float(case_data["actual_diaphragm_spacing_m"]),
        diaphragm_at_concentrated_loads=case_data["diaphragm_at_concentrated_loads"],
        diaphragm_at_chord_breaks=case_data["diaphragm_at_chord_breaks"],
        edge_distance_mm=float(case_data["edge_distance_mm"]), bolt_diameter_mm=float(case_data["bolt_diameter_mm"]),
        permanently_tensioned_single_bolt_element=case_data["permanently_tensioned_single_bolt_element"],
        braces_on_both_sides_of_chord_leg=case_data["braces_on_both_sides_of_chord_leg"],
        splice_total_bolts=int(case_data["splice_total_bolts"]),
        splice_bolts_per_leg_each_side=int(case_data["splice_bolts_per_leg_each_side"]),
        splice_rows_per_leg_each_side=int(case_data["splice_rows_per_leg_each_side"]),
        use_seven_bolt_exception=case_data["use_seven_bolt_exception"],
    )
    polygonal = v19.polygonal_tube_wall_stability_check(
        int(case_data["polygonal_face_count"]), float(case_data["polygonal_face_width_mm"]),
        float(case_data["polygonal_wall_thickness_mm"]), float(case_data["maximum_compressive_stress_n_mm2"]),
        float(case_data["minimum_stress_n_mm2"]), float(case_data["design_yield_resistance_n_mm2"]),
        float(case_data["elastic_modulus_n_mm2"]), float(case_data["working_condition_factor"]),
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "section_16_applicability_route": applicability,
            "table_45_working_condition_factor": gamma_c_45,
            "equation_201_maximum_slenderness": eq201,
            "equation_202_maximum_slenderness": eq202,
            "clause_16_5_pyramidal_mu": pyramidal_mu,
            "equation_203_maximum_slenderness": eq203,
            "equation_204_relative_eccentricity": eq204,
            "equation_205_relative_eccentricity": eq205,
            "clauses_16_8_to_16_9_auxiliaries": auxiliaries,
            "equation_206_amplified_moment_n_mm": eq206,
            "equation_207_design_shear_n": eq207,
            "equation_208_additional_chord_force": eq208,
            "equations_209_to_212_angle_factors": angle_factors,
            "table_46_deformation_check": table_46,
            "clauses_16_13_to_16_19_detailing": detailing,
            "equations_213_to_214_polygonal_tube_wall": polygonal,
        },
        "scope_note": (
            "Section 16 equations (201)-(214), Tables 45-46, and executable clauses 16.1-16.20 are implemented. "
            "Loads, combinations, global second-order analysis, section classification, complete node design, and evidence from drawings remain explicit external boundaries. "
            "Equation (215) and Table 47 are implemented in the Section 17 antenna-structure route; equations (216)-(224) and Table 48 belong to Section 18 and remain outside v0.20."
        ),
    }
    _write_case_report(root, "overhead_line_and_switchyard_supports", result, "Overhead-line and switchyard-support case")
    return result


def _run_antenna_structures_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    material = v20.antenna_structure_material_group_route_clause_17_1(
        int(case_data["component_group"]), case_data["steel_grade"],
        is_pipe=case_data["is_pipe"],
        annex_v_grade_selection_confirmed=case_data["annex_v_grade_selection_confirmed"],
    )
    rope = v20.steel_rope_selection_clause_17_2(
        float(case_data["rope_design_force_kn"]), case_data["rope_environment"],
        case_data["rope_construction"], case_data["rope_core_type"],
        built_in_nut_insulator=case_data["built_in_nut_insulator"],
        radio_allows_nonmetallic_core=case_data["radio_allows_nonmetallic_core"],
        round_wire_rope_capacity_kn=float(case_data["round_wire_rope_capacity_kn"]),
        end_binding_length_increased_25_percent=case_data["end_binding_length_increased_25_percent"],
    )
    termination = v20.rope_end_zinc_alloy_check_clause_17_3(case_data["selected_rope_end_alloy"])
    wire_route = v20.antenna_wire_material_route_clause_17_4(
        annex_b_table_b2_selection_confirmed=case_data["annex_b_table_b2_selection_confirmed"],
        copper_wire_used=case_data["copper_wire_used"],
        technological_necessity_confirmed=case_data["technological_necessity_confirmed"],
    )
    wire_design = v20.wire_design_tension_force_clause_17_5(
        float(case_data["wire_breaking_force_n"]), case_data["wire_type"],
        float(case_data["wire_nominal_area_mm2"]),
    )
    gamma_c_47 = v20.table_47_working_condition_factor(case_data["table_47_case_id"])
    deviation = v20.support_relative_deviation_check_clause_17_7(
        float(case_data["actual_support_deviation_mm"]), float(case_data["support_height_mm"]),
        case_data["support_deviation_load_case"],
    )
    erection = v20.erection_connection_check_clause_17_8(
        case_data["erection_accuracy_class"], case_data["erection_bolt_strength_class"],
        sign_changing_force=case_data["sign_changing_force"],
        controlled_pretension_confirmed=case_data["controlled_pretension_confirmed"],
        erection_weld_used=case_data["erection_weld_used"],
        installer_agreement_confirmed=case_data["installer_agreement_confirmed"],
    )
    cross = v20.cross_lattice_and_platform_checks_clause_17_9(
        float(case_data["cross_brace_slenderness"]), case_data["cross_braces_tied_at_intersection"],
        float(case_data["platform_vertical_deflection_mm"]),
        float(case_data["platform_horizontal_deflection_mm"]), float(case_data["platform_span_mm"]),
    )
    diaphragm = v20.diaphragm_check_clause_17_10(
        float(case_data["actual_diaphragm_spacing_mm"]), float(case_data["mean_support_section_size_mm"]),
        diaphragm_at_concentrated_loads=case_data["diaphragm_at_concentrated_loads"],
        diaphragm_at_chord_breaks=case_data["diaphragm_at_chord_breaks"],
    )
    flange_bolts = v20.pipe_flange_bolt_layout_check_clause_17_11(
        one_circle=case_data["flange_bolts_on_one_circle"],
        minimum_possible_circle_diameter=case_data["flange_bolt_circle_minimum_diameter"],
        equal_spacing=case_data["flange_bolts_equally_spaced"],
    )
    node = v20.truss_node_detailing_checks_clause_17_12(
        members_centered_on_chord_axis=case_data["members_centered_on_chord_axis"],
        eccentricity_mm=float(case_data["node_eccentricity_mm"]),
        chord_cross_section_size_mm=float(case_data["chord_cross_section_size_mm"]),
        node_moment_analysis_performed=case_data["node_moment_analysis_performed"],
        slot_end_hole_diameter_mm=float(case_data["slot_end_hole_diameter_mm"]),
        round_brace_diameter_mm=float(case_data["round_brace_diameter_mm"]),
    )
    guy = v20.guy_attachment_detailing_checks_clause_17_13(
        guy_centered_at_chord_strut_intersection=case_data["guy_centered_at_chord_strut_intersection"],
        eye_plate_stiffened_against_bending=case_data["eye_plate_stiffened_against_bending"],
        attachment_exceeds_transport_envelope=case_data["attachment_exceeds_transport_envelope"],
        separate_rigid_insert_provided=case_data["separate_rigid_insert_provided"],
    )
    insert = v20.flexible_cable_insert_check_clause_17_14(
        float(case_data["flexible_insert_clear_length_mm"]), float(case_data["rope_diameter_mm"])
    )
    mechanical = v20.mechanical_detail_evidence_clause_17_15(
        standard_detail_used=case_data["standard_mechanical_detail_used"],
        strength_tested=case_data["mechanical_detail_strength_tested"],
        fatigue_tested=case_data["mechanical_detail_fatigue_tested"],
        threaded_tension_element=case_data["threaded_tension_element"],
        rounded_thread_root_confirmed=case_data["rounded_thread_root_confirmed"],
    )
    eq215 = v20.vibration_damper_distance_eq215(
        float(case_data["rope_diameter_mm"]), float(case_data["rope_pretension_n"]),
        float(case_data["rope_mass_per_length_kg_m"]),
    )
    vibration = v20.vibration_damper_design_clause_17_16(
        float(case_data["rope_diameter_mm"]), float(case_data["rope_pretension_n"]),
        float(case_data["rope_mass_per_length_kg_m"]), float(case_data["rope_span_m"]),
        low_frequency_hz=float(case_data["low_frequency_damper_hz"]),
        high_frequency_hz=float(case_data["high_frequency_damper_hz"]),
        paired_sequential_dampers=case_data["paired_sequential_dampers"],
        low_frequency_selected_from_fundamental_mode=case_data["low_frequency_selected_from_fundamental_mode"],
        high_frequency_damper_above_low_at_distance_s=case_data["high_frequency_damper_above_low_at_distance_s"],
        dampers_installed=case_data["dampers_installed"],
        galloping_risk_present=case_data["galloping_risk_present"],
        free_length_modified_with_leashes=case_data["free_length_modified_with_leashes"],
    )
    marking = v20.obstruction_marking_and_lighting_check_clause_17_17(
        case_data["obstruction_marking_and_lighting_confirmed"]
    )
    galvanizing = v20.galvanizing_check_clause_17_18(
        guy_mechanical_details_galvanized=case_data["guy_mechanical_details_galvanized"],
        insulator_fittings_galvanized=case_data["insulator_fittings_galvanized"],
        fasteners_galvanized=case_data["fasteners_galvanized"],
    )
    checks = [
        material["pass"], rope["pass"], termination["pass"], wire_route["pass"], deviation["pass"],
        erection["pass"], cross["pass"], diaphragm["pass"], flange_bolts["pass"], node["pass"],
        guy["pass"], insert["pass"], mechanical["pass"], vibration["pass"], marking["pass"], galvanizing["pass"],
    ]
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "clause_17_1_material_group_route": material,
            "clause_17_2_rope_selection": rope,
            "clause_17_3_rope_end_alloy": termination,
            "clause_17_4_wire_material_route": wire_route,
            "clause_17_5_wire_design_tension": wire_design,
            "table_47_working_condition_factor": gamma_c_47,
            "clause_17_7_support_deviation": deviation,
            "clause_17_8_erection_connection": erection,
            "clause_17_9_cross_lattice_and_platform": cross,
            "clause_17_10_diaphragm": diaphragm,
            "clause_17_11_flange_bolts": flange_bolts,
            "clause_17_12_node_detailing": node,
            "clause_17_13_guy_attachment": guy,
            "clause_17_14_flexible_insert": insert,
            "clause_17_15_mechanical_detail_evidence": mechanical,
            "equation_215_minimum_damper_distance_m": eq215,
            "clause_17_16_vibration_damper_design": vibration,
            "clause_17_17_marking_and_lighting": marking,
            "clause_17_18_galvanizing": galvanizing,
            "all_executable_section_17_checks_pass": all(checks),
        },
        "scope_note": (
            "Section 17 applies to antenna structures up to 500 m. Equation (215), Table 47, and executable clauses 17.1-17.18 are implemented. "
            "Loads and combinations, Annex V and B.2 product selection, rope and wire certificates, global analysis, aeroelastic response, testing records, fabrication quality, marking regulations, and coating inspection remain explicit external boundaries. "
            "Equations (216)-(224) belong to Section 18 reconstruction provisions and are not part of v0.20."
        ),
    }
    _write_case_report(root, "antenna_structures", result, "Antenna-structure case")
    return result



def _run_reconstruction_assessment_case(case_data: dict[str, Any], root: Path) -> dict[str, Any]:
    condition = v21.technical_condition_category_clause_18_1_1(
        defects_or_damage_present=case_data["defects_or_damage_present"],
        local_character_only=case_data["local_character_only"],
        restricts_normal_operation=case_data["restricts_normal_operation"],
        requires_monitoring_or_strengthening=case_data["requires_monitoring_or_strengthening"],
        sudden_failure_or_global_instability_risk=case_data["sudden_failure_or_global_instability_risk"],
    )
    monitoring = v21.strengthening_and_monitoring_route_clause_18_1_2(
        condition["category"],
        monitoring_program_confirmed=case_data["monitoring_program_confirmed"],
        smooth_load_transfer_to_strengthening_confirmed=case_data["smooth_load_transfer_to_strengthening_confirmed"],
        construction_stage_capacity_confirmed=case_data["construction_stage_capacity_confirmed"],
    )
    exemption = v21.verification_calculation_exemption_clause_18_1_3(
        float(case_data["years_in_service"]),
        defects_or_damage_present=case_data["defects_or_damage_present"],
        operating_conditions_worsened=case_data["operating_conditions_worsened"],
        loads_increased=case_data["loads_increased"],
        main_member_strengthening_required=case_data["main_member_strengthening_required"],
    )
    material_evidence = v21.material_evidence_route_clause_18_2_1(
        factory_certificate_available=case_data["factory_certificate_available"],
        sample_tests_completed=case_data["sample_tests_completed"],
        executive_documentation_complete=case_data["executive_documentation_complete"],
        metal_quality_doubt_present=case_data["metal_quality_doubt_present"],
    )
    test_program = v21.metal_test_program_clause_18_2_2(
        case_data["steel_process"],
        chemical_composition_tested=case_data["chemical_composition_tested"],
        tensile_properties_tested=case_data["tensile_properties_tested"],
        stress_strain_diagram_obtained=case_data["stress_strain_diagram_obtained"],
        impact_toughness_tested_if_required=case_data["impact_toughness_tested_if_required"],
        macro_microstructure_tested_if_required=case_data["macro_microstructure_tested_if_required"],
        sulfur_percent=float(case_data["sulfur_percent"]),
        phosphorus_percent=float(case_data["phosphorus_percent"]),
    )
    pre1950 = v21.pre_1950_specialized_institute_route_clause_18_2_3(
        case_data["manufacture_period"],
        specialized_research_institute_confirmed=case_data["specialized_research_institute_confirmed"],
        steel_production_method_identified=case_data["steel_production_method_identified"],
    )
    steel = v21.existing_steel_design_resistances_clause_18_2_4(
        case_data["steel_resistance_route"],
        float(case_data["normative_or_test_yield_n_mm2"]),
        float(case_data["normative_or_test_ultimate_n_mm2"]),
        steel_process=case_data["steel_process"] if case_data["steel_process"] != "unknown_carbon" else "open_hearth",
    )
    weld = v21.existing_weld_resistance_defaults_clause_18_2_5(
        float(case_data["normative_or_test_ultimate_n_mm2"]),
        float(steel["design_yield_resistance_n_mm2"]),
        case_data["weld_construction_period"],
    )
    bolt_defaults = v21.unknown_bolt_resistance_defaults_clause_18_2_6()
    rivet_resistance = v21.table_48_rivet_resistance(
        case_data["rivet_limit_state"], case_data["rivet_connection_group"], case_data["rivet_steel"],
        connected_steel_design_yield_n_mm2=float(steel["design_yield_resistance_n_mm2"]),
        countersunk_or_semicountersunk_head=case_data["rivet_countersunk_or_semicountersunk_head"],
    )
    rivet_capacity = v21.rivet_connection_capacity_clause_18_2_7(
        case_data["rivet_limit_state"], rivet_resistance, float(case_data["rivet_diameter_mm"]),
        shear_planes=int(case_data["rivet_shear_planes"]),
        connected_thickness_sum_mm=float(case_data["rivet_connected_thickness_sum_mm"]),
        working_condition_factor=float(case_data["rivet_working_condition_factor"]),
    )
    strengthening_route = v21.existing_structure_strengthening_route_clauses_18_3_1_to_18_3_4(
        brittle_steel_temperature_condition_triggered=case_data["brittle_steel_temperature_condition_triggered"],
        post_reconstruction_stress_not_above_existing_confirmed=case_data["post_reconstruction_stress_not_above_existing_confirmed"],
        actual_geometry_supports_and_defects_in_model_confirmed=case_data["actual_geometry_supports_and_defects_in_model_confirmed"],
        mandatory_code_checks_pass=case_data["mandatory_code_checks_pass"],
        serviceability_exceedance_blocks_operation=case_data["serviceability_exceedance_blocks_operation"],
        slenderness_exceedance_acceptable_by_test_or_calculation=case_data["slenderness_exceedance_acceptable_by_test_or_calculation"],
    )
    execution = v21.strengthening_execution_checks_clauses_18_3_5_to_18_3_10(
        construction_stage_capacity_confirmed=case_data["construction_stage_capacity_confirmed"],
        additional_holes_and_welding_effects_included=case_data["additional_holes_and_welding_effects_included"],
        load_state_during_work_defined=case_data["load_state_during_work_defined"],
        intermittent_flange_weld_used=case_data["intermittent_flange_weld_used"],
        structure_group=int(case_data["structure_group"]),
        design_temperature_c=float(case_data["design_temperature_c"]),
        environment=case_data["environment"],
        combined_connection_type=case_data["combined_connection_type"],
    )
    heating_limit = v21.weld_heating_stress_limit_clause_18_3_9(
        int(case_data["structure_group"]), float(steel["design_yield_resistance_n_mm2"])
    )
    common_resistance = v21.common_or_separate_design_resistance_clause_18_3_11(
        float(case_data["existing_design_resistance_n_mm2"]),
        float(case_data["reinforcement_design_resistance_n_mm2"]),
    )
    gamma_n = v21.gamma_n_clause_18_3_13(
        welding_used=case_data["welding_used_for_strengthening"],
        initial_design_stress_n_mm2=float(case_data["initial_design_stress_n_mm2"]),
        design_yield_resistance_n_mm2=float(case_data["reinforcement_design_resistance_n_mm2"]),
    )
    eq216 = v21.symmetric_compression_strength_utilization_eq216(
        float(case_data["axial_force_n"]), float(case_data["strengthened_area_mm2"]),
        float(case_data["reinforcement_design_resistance_n_mm2"]), gamma_n,
        float(case_data["working_condition_factor"]),
    )
    gamma_m = v21.gamma_m_clause_18_3_13(
        int(case_data["structure_group"]), float(case_data["axial_force_n"]),
        float(case_data["strengthened_area_mm2"]), float(case_data["reinforcement_design_resistance_n_mm2"]), gamma_n,
    )
    eq217 = v21.asymmetric_strength_utilization_eq217(
        float(case_data["axial_force_n"]), float(case_data["strengthened_area_mm2"]),
        float(case_data["moment_x_n_mm"]), float(case_data["inertia_x_mm4"]), float(case_data["point_y_mm"]),
        float(case_data["moment_y_n_mm"]), float(case_data["inertia_y_mm4"]), float(case_data["point_x_mm"]),
        float(case_data["reinforcement_design_resistance_n_mm2"]), gamma_m, float(case_data["working_condition_factor"]),
    )
    alpha_n = v21.longitudinal_force_influence_alpha_n_clause_18_3_14(
        float(case_data["euler_critical_force_n"]), float(case_data["initial_axial_force_n"])
    )
    f_after = v21.post_strengthening_initial_deflection_eq221(
        float(case_data["initial_deflection_mm"]), alpha_n,
        float(case_data["reinforcement_own_centroidal_inertia_sum_mm4"]), float(case_data["original_inertia_mm4"]),
    )
    v_parameter = v21.weld_shortening_parameter_v(float(case_data["weld_leg_cm"]))
    weld_terms = [{"n_i": float(item["n_i"]), "v_i": v_parameter, "y_i": float(item["y_i"])} for item in case_data["weld_terms"]]
    f_w = v21.welding_residual_deflection_eq222(
        float(case_data["average_weld_continuity_factor"]), alpha_n,
        float(case_data["effective_length_for_weld_deflection"]), weld_terms,
    )
    base_ef = float(case_data["axial_force_eccentricity_mm"]) + f_after
    k_fw = v21.welding_deflection_factor_k_fw_clause_18_3_14(base_ef, f_w)
    e_f = v21.equivalent_eccentricity_eq220(
        float(case_data["axial_force_eccentricity_mm"]), f_after, k_fw, f_w
    )
    eq219 = v21.reduced_relative_eccentricity_eq219(
        e_f, float(case_data["strengthened_area_mm2"]), float(case_data["compressed_fiber_section_modulus_mm3"])
    )
    k = v21.composite_resistance_factor_eq224(
        float(case_data["reinforcement_design_resistance_n_mm2"]), float(case_data["existing_design_resistance_n_mm2"]),
        float(case_data["original_area_mm2"]), float(case_data["strengthened_area_mm2"]),
        float(case_data["original_inertia_mm4"]), float(case_data["strengthened_inertia_mm4"]),
    )
    ry_eff = v21.effective_design_resistance_eq223(float(case_data["existing_design_resistance_n_mm2"]), k)
    eq218 = v21.strengthened_member_stability_utilization_eq218(
        float(case_data["axial_force_n"]), float(case_data["phi_e"]),
        float(case_data["strengthened_area_mm2"]), ry_eff, float(case_data["working_condition_factor"]),
    )
    deviation = v21.existing_deviation_acceptance_clause_18_3_16(
        listed_deviation_only=case_data["listed_deviation_only"],
        damage_caused_by_deviation_absent=case_data["damage_caused_by_deviation_absent"],
        adverse_operating_change_excluded=case_data["adverse_operating_change_excluded"],
        capacity_and_stiffness_justified=case_data["capacity_and_stiffness_justified"],
        fatigue_and_brittle_fracture_measures_confirmed=case_data["fatigue_and_brittle_fracture_measures_confirmed"],
    )
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": True,
        "inputs": case_data,
        "results": {
            "clause_18_1_1_technical_condition": condition,
            "clause_18_1_2_monitoring_and_strengthening": monitoring,
            "clause_18_1_3_verification_calculation_exemption": exemption,
            "clause_18_2_1_material_evidence": material_evidence,
            "clause_18_2_2_test_program": test_program,
            "clause_18_2_3_pre1950_route": pre1950,
            "clause_18_2_4_existing_steel_resistances": steel,
            "clause_18_2_5_existing_weld_defaults": weld,
            "clause_18_2_6_unknown_bolt_defaults": bolt_defaults,
            "table_48_rivet_resistance_n_mm2": rivet_resistance,
            "clause_18_2_7_rivet_capacity": rivet_capacity,
            "clauses_18_3_1_to_18_3_4_route": strengthening_route,
            "clauses_18_3_5_to_18_3_10_execution": execution,
            "clause_18_3_9_weld_heating_stress_limit_n_mm2": heating_limit,
            "clause_18_3_11_resistance_route": common_resistance,
            "equation_216_gamma_n": gamma_n,
            "equation_216_utilization": eq216,
            "equation_217_gamma_m": gamma_m,
            "equation_217_result": eq217,
            "clause_18_3_14_alpha_n": alpha_n,
            "equation_221_post_strengthening_initial_deflection": f_after,
            "equation_222_weld_shortening_parameter_v": v_parameter,
            "equation_222_welding_residual_deflection": f_w,
            "equation_220_k_fw": k_fw,
            "equation_220_equivalent_eccentricity": e_f,
            "equation_219_relative_eccentricity": eq219,
            "equation_224_composite_factor_k": k,
            "equation_223_effective_design_resistance_n_mm2": ry_eff,
            "equation_218_stability_utilization": eq218,
            "clause_18_3_16_existing_deviation_acceptance": deviation,
        },
        "scope_note": (
            "Section 18 equations (216)-(224), Table 48 and executable assessment/strengthening routes are implemented. "
            "Survey conclusions, laboratory tests, material identification, load combinations, actual-geometry global analysis, Figure 24 n_i values, construction-stage analysis and professional decisions remain explicit external evidence boundaries."
        ),
    }
    _write_case_report(root, "reconstruction_assessment", result, "Reconstruction assessment case")
    return result


def _hydrate_case_with_material_ref(
    case_data: dict[str, Any], material_ref: dict[str, Any], allowed_fields: set[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = {"product_form", "steel_grade", "thickness_mm", "material_safety_category", "design_resistance_source"}
    missing = required - set(material_ref)
    if missing:
        raise ValueError(f"material_ref missing fields: {sorted(missing)}")
    source = str(material_ref["design_resistance_source"])
    if source not in {"annex_tabulated", "table_2_formula"}:
        raise ValueError("material_ref.design_resistance_source must be 'annex_tabulated' or 'table_2_formula'")
    resolver = SteelMaterialStrengthResolver()
    bundle = resolver.resolve(
        str(material_ref["product_form"]), str(material_ref["steel_grade"]),
        float(material_ref["thickness_mm"]), str(material_ref["material_safety_category"]),
    )
    annex = bundle["annex_strength"]
    formula = bundle["table_2_formula_resistances"]
    if source == "annex_tabulated":
        ry = float(annex["Ry_tabulated_MPa"])
        ru = float(annex["Ru_tabulated_MPa"])
    else:
        ry = float(formula["Ry_formula_MPa"])
        ru = float(formula["Ru_formula_MPa"])
    candidates = {
        "normative_yield_resistance_n_mm2": float(annex["Ryn_MPa"]),
        "normative_ultimate_resistance_n_mm2": float(annex["Run_MPa"]),
        "design_yield_resistance_n_mm2": ry,
        "design_ultimate_resistance_n_mm2": ru,
        "design_shear_resistance_n_mm2": float(formula["Rs_formula_MPa"]),
        "elastic_modulus_n_mm2": float(bundle["physical_properties"]["E_MPa"]),
        "shear_modulus_n_mm2": float(bundle["physical_properties"]["G_MPa"]),
        "ultimate_resistance_safety_factor": float(bundle["gamma_u"]),
    }
    out = dict(case_data)
    overwrite = bool(material_ref["overwrite_material_fields"]) if "overwrite_material_fields" in material_ref else False
    for key, value in candidates.items():
        if key not in allowed_fields:
            continue
        if overwrite or key not in out:
            out[key] = value
    trace = {
        "material_ref": dict(material_ref),
        "selected_design_resistance_source": source,
        "resolved_values": {k: v for k, v in candidates.items() if k in allowed_fields},
        "stage_n1_bundle": bundle,
    }
    return out, trace


def _apply_guided_section_weakening(case_data: dict[str, Any], action: str) -> dict[str, Any]:
    if action not in {"axial_member_guided", "built_up_axial_member_guided", "bending_member_guided", "beam_column_guided"}:
        return case_data
    out = dict(case_data)
    weakening = out.get("section_weakening")

    if action in {"axial_member_guided", "built_up_axial_member_guided"}:
        if weakening == "none":
            if "gross_area_mm2" not in out:
                raise ValueError("section_weakening='none' requires a resolved gross_area_mm2")
            target = "net_area_mm2" if action == "axial_member_guided" else "total_net_area_mm2"
            if target in out and abs(float(out[target]) - float(out["gross_area_mm2"])) > 1e-9:
                raise ValueError(f"{target} must equal gross_area_mm2 when section_weakening='none'")
            out[target] = float(out["gross_area_mm2"])
        elif weakening == "explicit_net_area":
            target = "net_area_mm2" if action == "axial_member_guided" else "total_net_area_mm2"
            if target not in out:
                raise ValueError(f"section_weakening='explicit_net_area' requires {target}")
        return out

    if action == "beam_column_guided":
        if weakening == "none":
            if "gross_area_mm2" not in out:
                raise ValueError("beam_column_guided section_weakening='none' requires gross_area_mm2")
            out["net_area_mm2"] = float(out["gross_area_mm2"])
            mapping = {
                "compressed_section_modulus_x_mm3": "minimum_net_section_modulus_x_mm3",
                "compressed_section_modulus_y_mm3": "minimum_net_section_modulus_y_mm3",
                "inertia_x_mm4": "net_inertia_x_mm4",
                "inertia_y_mm4": "net_inertia_y_mm4",
            }
            for source, target in mapping.items():
                if source not in out:
                    raise ValueError(f"beam_column_guided section_weakening='none' requires {source}")
                out[target] = float(out[source])
        elif weakening == "explicit_net_properties":
            required = {"net_area_mm2", "minimum_net_section_modulus_x_mm3", "minimum_net_section_modulus_y_mm3", "net_inertia_x_mm4", "net_inertia_y_mm4"}
            missing = required - set(out)
            if missing:
                raise ValueError(f"beam_column_guided explicit net properties missing: {sorted(missing)}")
        else:
            raise ValueError("beam_column_guided section_weakening must be none or explicit_net_properties")
        return out

    if action == "bending_member_guided":
        if weakening == "none":
            required = {
                "compressed_section_modulus_x_mm3": "minimum_net_section_modulus_x_mm3",
                "compressed_section_modulus_y_mm3": "minimum_net_section_modulus_y_mm3",
                "inertia_x_mm4": "net_inertia_x_mm4",
                "inertia_y_mm4": "net_inertia_y_mm4",
            }
            for source, target in required.items():
                if source not in out:
                    raise ValueError(f"section_weakening='none' requires resolved {source}")
                if target in out and abs(float(out[target]) - float(out[source])) > 1e-9:
                    raise ValueError(f"{target} must equal {source} when section_weakening='none'")
                out[target] = float(out[source])
        elif weakening == "explicit_net_properties":
            for target in ("minimum_net_section_modulus_x_mm3", "minimum_net_section_modulus_y_mm3"):
                if target not in out:
                    raise ValueError(f"section_weakening='explicit_net_properties' requires {target}")
        else:
            raise ValueError("bending_member_guided section_weakening must be none or explicit_net_properties")
    return out


def _run_bending_member_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    workflow = bdw.bending_member_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow.get("governing_utilization") is not None,
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N4 applicability-safe guided bending workflow. It evaluates only the selected ordinary-beam strength branch, "
            "an explicit lateral-stability route and an explicit local-stability route. Crane-runway/bimetal and full deep "
            "8.5 interaction checks retain their dedicated detailed actions. Imported profile rows remain pending final original-GOST audit."
        ),
    }
    _write_case_report(root, "bending_member_guided", result, "Stage N4 guided bending-member case")
    return result


def _run_beam_column_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    workflow = bcw.beam_column_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow.get("governing_utilization") is not None,
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N5 applicability-safe solid beam-column workflow for current SP16 Section 9. "
            "N1 material and N2 section hydration are explicit; N3/N4 primitives are reused. "
            "Table D.3 is exact-node only unless an explicitly sourced external phi_e is supplied. "
            "Built-up and box routes retain their existing detailed actions."
        ),
    }
    _write_case_report(root, "beam_column_guided", result, "Stage N5 guided beam-column case")
    return result



def _run_built_up_beam_column_guided_case(case_data: dict[str, Any], root: Path, resolution_trace: dict[str, Any]) -> dict[str, Any]:
    workflow = n6w.built_up_beam_column_guided_workflow(case_data)
    result = {
        "case_id": case_data["case_id"],
        "standard": case_data["standard"],
        "release_stage": RELEASE_STAGE,
        "action": case_data["action"],
        "engineering_calculation_performed": workflow.get("governing_utilization") is not None,
        "inputs": case_data,
        "resolution_trace": resolution_trace,
        "results": workflow,
        "scope_note": (
            "Stage N6 applicability-safe built-up beam-column and combined local-stability workflow for current SP16 clauses 9.3-9.4. "
            "Stage N3 Table-8/equation-18 and Stage N5 equation-109 primitives are reused. Table D.4 is exact-node only unless an "
            "explicitly sourced external phi_e is supplied; the explicit interpolation rules printed in Tables 22 and 23 are retained. "
            "Topology-specific branch analyses not fully determined by clauses 9.3.3-9.3.6 remain fail-closed rather than inferred."
        ),
    }
    _write_case_report(root, "built_up_beam_column_guided", result, "Stage N6 guided built-up beam-column case")
    return result

def _prepare_case_for_validation(
    raw_case: dict[str, Any], package_root: str | Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Prepare an explicit-reference case for strict action-schema validation."""
    root = Path(package_root)
    case_data = dict(raw_case)
    action = case_data.get("action")
    if not isinstance(action, str):
        raise ValueError("Case must contain a string action")
    schema_name = _schema_name_for_action(action)
    schema = json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))

    # N2+ reference hydration is deterministic pre-schema preparation, not a hidden
    # engineering default. The user's explicit profile/material references and the
    # resolved provenance are retained separately in resolution_trace.
    resolution_trace: dict[str, Any] = {}
    profile_ref = case_data.pop("profile_ref", None)
    if profile_ref is not None and action != "profile_catalog_resolve":
        if not isinstance(profile_ref, dict):
            raise ValueError("profile_ref must be an object")
        catalog = InterimProfileCatalog()
        bundle = catalog.resolve(
            int(profile_ref["family_id"]),
            str(profile_ref["designation"]),
            source_row_id=profile_ref.get("source_row_id"),
        )
        case_data = hydrate_case_with_profile(
            case_data, bundle,
            axis=str(profile_ref["axis"]) if "axis" in profile_ref else "x",
            overwrite=bool(profile_ref["overwrite_section_fields"]) if "overwrite_section_fields" in profile_ref else False,
            use_gross_as_net=bool(profile_ref["use_gross_as_net"]) if "use_gross_as_net" in profile_ref else False,
            allowed_fields=set(schema["properties"]),
        )
        if action in {"axial_member_guided", "bending_member_guided", "beam_column_guided"} and "rolled_i_section_confirmed" in schema["properties"] and "rolled_i_section_confirmed" not in case_data:
            case_data["rolled_i_section_confirmed"] = bundle.get("shape_group") == "I_ROLLED_DSYMM"
        resolution_trace["profile"] = {
            "profile_ref": dict(profile_ref),
            "catalog_status": bundle["catalog_status"],
            "original_gost_audit_complete": bundle["original_gost_audit_complete"],
            "shape_group": bundle["shape_group"],
            "torsion_policy": bundle["derived_properties"].get("torsion_policy"),
            "torsional_inertia_mm4": bundle["derived_properties"].get("torsional_inertia_mm4"),
            "source": bundle["source"],
        }

    material_ref = case_data.pop("material_ref", None)
    if material_ref is not None:
        if not isinstance(material_ref, dict):
            raise ValueError("material_ref must be an object")
        case_data, material_trace = _hydrate_case_with_material_ref(case_data, material_ref, set(schema["properties"]))
        resolution_trace["material"] = material_trace

    case_data = _apply_guided_section_weakening(case_data, action)
    errors = validate_case(case_data, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return case_data, schema, resolution_trace


def run_case(case_path: str | Path, package_root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Validate and execute a supported v0.41 engineering, fire-mechanics, fire-thermal, or fire-assessment JSON case.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Implemented selected SP16 scope through Section 18 plus FIRE-D1 dependency closure, FIRE-D2 SP554 Sections 8-11 fire-mechanics runtime, and FIRE-D3 Section 12 thermal runtime, and FIRE-D4 Section 13 result assessment
        Annex: D, E, and Ж
        Equation/Table: Implemented equations through (224), Tables 2-48 and implemented annex data
        Audit ID: AUDIT-RUNNER-005
        Normative status: no_code_explanatory

    Mathematical form:
        JSON input -> action-specific schema -> audited scalar functions -> JSON and Markdown reports.

    Parameters:
        case_path:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Path to a supported user-facing JSON case.
            Valid range: Existing file matching the selected action schema.
            Source: user input
        package_root:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Root folder of the package.
            Valid range: Existing package root.
            Source: runner

    Returns:
        Type: dict[str, Any]
        Unit: mixed, explicitly named
        Meaning: Calculation result bundle.

    Assumptions:
        - The action field selects the applicable schema and calculation wrapper.
        - All applicability confirmations in the input are truthful.

    Sign convention:
        - Magnitude-based actions are non-negative; equation (106) inputs use explicit signs.

    Unit convention:
        - Forces use N, areas mm2, and stresses N/mm2.

    Applicability:
        - Includes current SP16 actions, FIRE-D1 dependency audit, FIRE-D2 SP554 critical-temperature member runtime, FIRE-D3 SP554 Section 12 thermal runtime, and FIRE-D4 SP554 Section 13 result assessment.

    Limitations:
        - This runner can hydrate supported section properties from an explicit Stage N2 profile_ref; it does not infer loads, effective lengths, governing points, reductions/net weakening, or applicability confirmations.

    Raises:
        ValueError: The action is unsupported, schema validation fails, or a calculation domain is invalid.
        FileNotFoundError: The case or schema file is absent.

    Examples:
        >>> result = run_case("examples/axial_member_example.json", ".")
        >>> result["action"]
        'axial_member_strength_and_stability'

    Tests:
        Unit tests:
            - tests/test_schemas.py::test_axial_runner_writes_outputs
        Validation cases:
            - AXIAL-RUN-001

    Implementation notes:
        - Stage N2 profile hydration is explicit via profile_ref and occurs before schema validation.
        - Non-section defaults remain explicit in the input configuration.
    """
    root = Path(package_root)
    case_file = Path(case_path)
    raw_case = json.loads(case_file.read_text(encoding="utf-8"))
    case_data, schema, resolution_trace = _prepare_case_for_validation(raw_case, root)
    action = case_data["action"]
    if action == "profile_catalog_resolve":
        return _run_profile_catalog_case(case_data, root)
    if action == "material_resistance_bundle":
        return _run_material_resistance_case(case_data, root)
    if action == "sp554_sp16_fire_dependency_bridge":
        return _run_sp554_sp16_fire_dependency_bridge_case(case_data, root)
    if action == "sp554_fire_mechanical_guided":
        return _run_sp554_fire_mechanical_guided_case(case_data, root)
    if action == "sp554_fire_thermal_guided":
        return _run_sp554_fire_thermal_guided_case(case_data, root)
    if action == "sp554_fire_result_assessment":
        return _run_sp554_fire_result_assessment_case(case_data, root)
    if action == "axial_member_strength_and_stability":
        return _run_axial_member_case(case_data, root)
    if action == "axial_member_guided":
        return _run_axial_member_guided_case(case_data, root, resolution_trace)
    if action == "built_up_axial_members":
        return _run_built_up_axial_member_case(case_data, root)
    if action == "built_up_axial_member_guided":
        return _run_built_up_axial_member_guided_case(case_data, root, resolution_trace)
    if action == "centrally_compressed_local_stability":
        return _run_local_stability_case(case_data, root)
    if action == "bending_member_strength":
        return _run_bending_member_case(case_data, root)
    if action == "bending_member_guided":
        return _run_bending_member_guided_case(case_data, root, resolution_trace)
    if action == "crane_runway_and_bending_stability":
        return _run_crane_runway_and_bending_stability_case(case_data, root)
    if action == "bending_member_local_stability":
        return _run_bending_member_local_stability_case(case_data, root)
    if action == "base_plates_and_combined_force_strength":
        return _run_base_plates_and_combined_force_strength_case(case_data, root)
    if action == "beam_column_guided":
        return _run_beam_column_guided_case(case_data, root, resolution_trace)
    if action == "built_up_beam_column_guided":
        return _run_built_up_beam_column_guided_case(case_data, root, resolution_trace)
    if action == "beam_column_stability":
        return _run_beam_column_stability_case(case_data, root)
    if action == "built_up_beam_columns_and_combined_local_stability":
        return _run_built_up_beam_columns_and_combined_local_stability_case(case_data, root)
    if action == "effective_length_guided":
        return _run_effective_length_guided_case(case_data, root)
    if action == "effective_lengths_and_limiting_slenderness":
        return _run_effective_lengths_and_limiting_slenderness_case(case_data, root)
    if action == "sheet_structure_guided":
        return _run_sheet_structure_guided_case(case_data, root, resolution_trace)
    if action == "sheet_structures_strength_and_stability":
        return _run_sheet_structures_strength_and_stability_case(case_data, root)
    if action == "fatigue_guided":
        return _run_fatigue_guided_case(case_data, root, resolution_trace)
    if action == "fatigue_design":
        return _run_fatigue_design_case(case_data, root)
    if action == "brittle_fracture_guided":
        return _run_brittle_fracture_guided_case(case_data, root, resolution_trace)
    if action == "brittle_fracture_and_welded_connections":
        return _run_brittle_fracture_and_welded_connections_case(case_data, root)
    if action == "bolted_and_friction_connections":
        return _run_bolted_and_friction_connections_case(case_data, root)
    if action == "built_up_beam_flange_connections":
        return _run_built_up_beam_flange_connections_case(case_data, root)
    if action == "structural_detailing_and_support_bearings":
        return _run_structural_detailing_and_support_bearings_case(case_data, root)
    if action == "overhead_line_and_switchyard_supports":
        return _run_overhead_line_and_switchyard_supports_case(case_data, root)
    if action == "antenna_structures":
        return _run_antenna_structures_case(case_data, root)
    if action == "reconstruction_assessment":
        return _run_reconstruction_assessment_case(case_data, root)
    raise ValueError(f"Unsupported action: {action}")
