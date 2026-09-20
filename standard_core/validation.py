"""Implementation self-checks and normative-table cross-validation for the v0.21 selected scope."""

from __future__ import annotations

import json
import math
from pathlib import Path
from .release_metadata import RELEASE_STAGE
from typing import Any, Callable

from . import axial_members as am
from . import built_up_axial_members as bm
from . import material_resistance as mr
from . import local_stability as ls
from . import bending_members as bend
from . import crane_runway_and_bending_stability as stab
from . import bending_member_local_stability as bls
from . import base_plates_and_combined_force_strength as bc
from . import beam_column_stability as beamcol
from . import built_up_beam_columns_and_combined_local_stability as combined_local
from . import effective_lengths_and_limiting_slenderness as eff
from . import sheet_structures_strength_and_stability as sheet
from . import fatigue_design as fatigue
from . import brittle_fracture_and_welded_connections as welded
from . import bolted_and_friction_connections as bolted
from . import built_up_beam_flange_connections as flange
from . import structural_detailing_and_support_bearings as detail
from . import overhead_line_and_switchyard_supports as line_supports
from . import antenna_structures as antenna
from . import reconstruction_assessment as reconstruction

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _validation_case(
    case_id: str,
    standard_reference: str,
    classification: str,
    calculated: float,
    reference: float,
    tolerance: float,
    unit: str,
    comments: str,
) -> dict[str, Any]:
    absolute_error = abs(calculated - reference)
    relative_error = 0.0 if reference == 0.0 and absolute_error == 0.0 else (
        None if reference == 0.0 else absolute_error / abs(reference)
    )
    return {
        "validation_case_id": case_id,
        "standard_reference": standard_reference,
        "classification": classification,
        "input_file": "internal fixed self-check",
        "calculated_value": calculated,
        "reference_value": reference,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "tolerance": tolerance,
        "pass_fail": "pass" if absolute_error <= tolerance else "fail",
        "unit": unit,
        "comments": comments,
    }


def run_core_validation_cases() -> dict[str, Any]:
    """
    Summary:
        Run arithmetic self-checks and compare implemented formulas against all transcribed Table D.1, 10a, and E.1 values.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: Implemented scope through Section 18, including Annexes D, E, and Ж
        Annex: D and E
        Equation/Table: Implemented equations through (224), Tables 34-48 and Annex K Table K.1, and previously audited tables and annex formulas
        Audit ID: VALIDATION-CORE-005
        Normative status: implemented_as_validation_reference

    Mathematical form:
        Audited functions compared with hand-calculable references and every transcribed value in Tables D.1, 10a, and E.1.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: Fixed package validation cases are used.
            Valid range: not applicable
            Source: package validation design and Table D.1 data

    Returns:
        Type: dict[str, Any]
        Unit: mixed, explicitly stated per case
        Meaning: Validation status and case-level errors/pass-fail fields.

    Assumptions:
        - Table D.1 printed integers are rounded values of phi multiplied by 1000.
        - Arithmetic self-checks are not normative worked examples.

    Sign convention:
        - Forces, areas, resistances, and coefficients are non-negative magnitudes.

    Unit convention:
        - Stress uses N/mm2, force uses N, and utilization is dimensionless.

    Applicability:
        - Phase 0.23 reconstructed cumulative implementation/classification scope.

    Limitations:
        - No complete numerical worked example was identified in the supplied clauses.
        - Normative-table cross-checks verify transcription and lookup/interpolation behavior, not an independent experimental model.

    Raises:
        RuntimeError: A configured self-check cannot be evaluated.

    Examples:
        >>> report = run_core_validation_cases()
        >>> report["all_passed"]
        True

    Tests:
        Unit tests:
            - tests/test_validation_examples.py::test_core_self_checks_pass_and_have_error_fields
        Validation cases:
            - CORE-SELF-CHECK-v0.18
            - AXIAL-D1-*

    Implementation notes:
        - Table D.1 tolerance is slightly above 0.001 because the printed values are given to three decimals and are not consistently nearest-rounded at every boundary node.
        - Defaults must be explicit in the input configuration.
    """
    configured: list[tuple[str, str, Callable[[], float], float, float, str]] = [
        ("CORE-TBL-2-RY", "6.1 Table 2", lambda: mr.design_yield_resistance_n_mm2(355.0, 1.05), 355.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-2-RU", "6.1 Table 2", lambda: mr.design_ultimate_resistance_n_mm2(510.0, 1.05), 510.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-2-RS", "6.1 Table 2", lambda: mr.design_shear_resistance_n_mm2(355.0, 1.05), 0.58 * 355.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-2-RP", "6.1 Table 2", lambda: mr.design_end_bearing_resistance_n_mm2(510.0, 1.05), 510.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-2-RLP", "6.1 Table 2", lambda: mr.design_pin_local_bearing_resistance_n_mm2(510.0, 1.05), 0.5 * 510.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-2-RCD", "6.1 Table 2", lambda: mr.design_roller_diametral_compression_resistance_n_mm2(510.0, 1.05), 0.025 * 510.0 / 1.05, 1e-12, "N/mm2"),
        ("CORE-TBL-3", "6.1 Table 3", lambda: mr.material_safety_factor("other_conforming"), 1.05, 0.0, "dimensionless"),
        ("CORE-TBL-4-RWY-NDT", "6.4 Table 4", lambda: mr.butt_weld_design_yield_resistance_with_ndt_n_mm2(338.0), 338.0, 0.0, "N/mm2"),
        ("CORE-TBL-4-RWY", "6.4 Table 4", lambda: mr.butt_weld_design_yield_resistance_without_ndt_n_mm2(338.0), 287.3, 1e-12, "N/mm2"),
        ("CORE-TBL-4-RWF", "6.4 Table 4", lambda: mr.fillet_weld_metal_design_shear_resistance_n_mm2(490.0, 1.25), 0.55 * 490.0 / 1.25, 1e-12, "N/mm2"),
        ("CORE-TBL-4-RWZ", "6.4 Table 4", lambda: mr.fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(510.0), 0.45 * 510.0, 1e-12, "N/mm2"),
        ("CORE-TBL-5-RBS", "6.5 Table 5", lambda: mr.bolt_shear_design_resistance_n_mm2(800.0, "8.8"), 0.40 * 800.0, 1e-12, "N/mm2"),
        ("CORE-TBL-5-RBT", "6.5 Table 5", lambda: mr.bolt_tension_design_resistance_n_mm2(800.0, "8.8"), 0.54 * 800.0, 1e-12, "N/mm2"),
        ("CORE-TBL-5-RBP", "6.5 Table 5", lambda: mr.connected_element_bearing_design_resistance_n_mm2(485.0, "A", 355.0), 1.60 * 485.0, 1e-12, "N/mm2"),
        ("CORE-EQ-001", "6.6 equation (1)", lambda: mr.foundation_anchor_bolt_tension_design_resistance_n_mm2(355.0), 284.0, 1e-12, "N/mm2"),
        ("CORE-EQ-002", "6.6 equation (2)", lambda: mr.u_bolt_tension_design_resistance_n_mm2(355.0), 301.75, 1e-12, "N/mm2"),
        ("CORE-EQ-004", "6.8 equation (4)", lambda: mr.high_strength_wire_tension_design_resistance_n_mm2(510.0), 321.3, 1e-12, "N/mm2"),
        ("CORE-PROC-6.9", "6.9", lambda: mr.steel_rope_design_tension_force_n(1600000.0), 1000000.0, 1e-9, "N"),
        ("AXIAL-EQ-005-YIELD", "7.1.1 equation (5)", lambda: am.axial_strength_utilization_yield(500000.0, 2000.0, 355.0, 1.0), 500000.0 / (2000.0 * 355.0), 1e-12, "dimensionless"),
        ("AXIAL-EQ-005-ULTIMATE", "7.1.1 equation (5), R_u/gamma_u branch", lambda: am.axial_strength_utilization_ultimate(500000.0, 2000.0, 485.0, 1.3, 1.0), 500000.0 * 1.3 / (2000.0 * 485.0), 1e-12, "dimensionless"),
        ("AXIAL-TBL-006", "7.1.2 Table 6", lambda: am.table_6_angle_coefficients("multi_bolt_3")[0], 1.45, 0.0, "dimensionless"),
        ("AXIAL-PROC-GAMMA-C1", "7.1.2 gamma_c1", lambda: am.single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, False), 0.65, 1e-12, "dimensionless"),
        ("AXIAL-PROC-GAMMA-C1-REDUCED", "7.1.2 10% reduction", lambda: am.single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, True), 0.585, 1e-12, "dimensionless"),
        ("AXIAL-EQ-006", "7.1.2 equation (6)", lambda: am.single_angle_connection_strength_utilization(200000.0, 1000.0, 485.0, 1.3, 0.65), 200000.0 * 1.3 / (1000.0 * 485.0 * 0.65), 1e-12, "dimensionless"),
        ("AXIAL-PROC-RELATIVE-SLENDERNESS", "7.1.3 lambda_bar definition", lambda: am.relative_slenderness(2.0 / math.sqrt(355.0 / 206000.0), 355.0, 206000.0), 2.0, 1e-12, "dimensionless"),
        ("AXIAL-TBL-007", "7.1.3 Table 7", lambda: am.table_7_section_coefficients("c")[1], 0.14, 0.0, "dimensionless"),
        ("AXIAL-EQ-009", "7.1.3 equation (9)", lambda: am.stability_delta(2.0, 0.04, 0.09), 9.87 * (1.0 - 0.04 + 0.09 * 2.0) + 4.0, 1e-12, "dimensionless"),
        ("AXIAL-EQ-008", "7.1.3 equation (8)", lambda: am.central_compression_stability_coefficient(2.0, "b"), 0.5 * (15.2518 - math.sqrt(15.2518**2 - 39.48 * 4.0)) / 4.0, 1e-12, "dimensionless"),
        ("AXIAL-EQ-008-LOW", "7.1.3 low-slenderness rule", lambda: am.central_compression_stability_coefficient(0.4, "a"), 1.0, 0.0, "dimensionless"),
        ("AXIAL-EQ-008-CAP", "7.1.3 upper cap rule", lambda: am.central_compression_stability_coefficient(5.0, "a"), 7.6 / 25.0, 1e-12, "dimensionless"),
        ("AXIAL-EQ-007", "7.1.3 equation (7)", lambda: am.central_compression_stability_utilization(500000.0, 2500.0, 355.0, 1.0, 0.8), 500000.0 / (0.8 * 2500.0 * 355.0), 1e-12, "dimensionless"),
        ("AXIAL-EQ-011-RECONSTRUCTION", "7.1.5 equation (11)", lambda: am.open_u_section_phi_1(0.8, 2.0), 1.52, 1e-12, "dimensionless"),
        ("AXIAL-EQ-010-RECONSTRUCTION", "7.1.5 equations (10)-(11)", lambda: am.open_u_section_torsional_flexural_utilization(500000.0, 3000.0, 340.0, 1.05, 0.8, 2.0), 0.4672271897817039, 1e-12, "dimensionless"),

        ("BUILTUP-TBL-008", "7.2 Table 8", lambda: float(len(bm.table_8_formula_catalog()["formula_rows"])), 6.0, 0.0, "formula rows"),
        ("BUILTUP-EQ-012", "7.2 Table 8 equation (12)", lambda: bm.battened_effective_slenderness_type_1(2.0, 1.0, 200000.0, 400.0, 500000.0, 1000.0), math.sqrt(4.0 + 0.82*(1.0 + 200000.0*400.0/(500000.0*1000.0))), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-013", "7.2 Table 8 equation (13)", lambda: bm.battened_effective_slenderness_type_2(2.0, 1.0, 1.1, 200000.0, 220000.0, 350.0, 450.0, 500000.0, 550000.0, 1000.0), math.sqrt(4.0 + 0.82*((1.0 + 200000.0*350.0/(500000.0*1000.0))*1.0**2 + (1.0 + 220000.0*450.0/(550000.0*1000.0))*1.1**2)), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-014", "7.2 Table 8 equation (14)", lambda: bm.battened_effective_slenderness_type_3(2.0, 1.0, 180000.0, 400.0, 500000.0, 1000.0), math.sqrt(4.0 + 0.82*(1.0 + 3.0*180000.0*400.0/(500000.0*1000.0))), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-015", "7.2 Table 8 equation (15)", lambda: bm.lattice_effective_slenderness_type_1(2.0, 5000.0, 500.0, 600.0, 400.0, 1000.0), math.sqrt(4.0 + (10.0*600.0**3/(400.0**2*1000.0))*5000.0/500.0), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-016", "7.2 Table 8 equation (16)", lambda: bm.lattice_effective_slenderness_type_2(2.0, 5000.0, 500.0, 550.0, 600.0, 650.0, 350.0, 450.0, 1000.0), math.sqrt(4.0 + ((10.0*600.0**3/(350.0**2*1000.0)) + (10.0*650.0**3/(450.0**2*1000.0))*500.0/550.0)*5000.0/500.0), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-017", "7.2 Table 8 equation (17)", lambda: bm.lattice_effective_slenderness_type_3(2.0, 5000.0, 500.0, 600.0, 400.0, 1000.0), math.sqrt(4.0 + 0.67*(10.0*600.0**3/(400.0**2*1000.0))*5000.0/500.0), 1e-12, "dimensionless"),
        ("BUILTUP-EQ-018", "7.2.7 equation (18)", lambda: bm.fictitious_shear_force_n(1000000.0, 206000.0, 355.0, 0.8), 7.15e-6*(2330.0-206000.0/355.0)*1000000.0/0.8, 1e-9, "N"),
        ("BUILTUP-EQ-019", "7.2.8 equation (19)", lambda: bm.batten_shear_force_n(1000.0, 800.0, 400.0), 2000.0, 1e-12, "N"),
        ("BUILTUP-EQ-020", "7.2.8 equation (20)", lambda: bm.batten_bending_moment_n_mm(1000.0, 800.0), 400000.0, 1e-9, "N*mm"),
        ("BUILTUP-EQ-021", "7.2.9 equation (21)", lambda: bm.lattice_diagonal_force_n(1000.0, 600.0, 400.0, 0.5), 750.0, 1e-12, "N"),
        ("BUILTUP-EQ-022", "7.2.9 equation (22)", lambda: bm.cross_lattice_additional_diagonal_force_n(200000.0, 500.0, 2500.0, bm.cross_lattice_alpha_2(600.0, 800.0, 400.0)), (600.0*800.0**2/(2.0*400.0**3+600.0**3))*200000.0*500.0/2500.0, 1e-9, "N"),
        ("BUILTUP-PROC-7.2.2-METHOD", "7.2.2 method route", lambda: 1.0 if bm.built_up_stability_method(5, "battens") == "frame_system_analysis_required" else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BUILTUP-PROC-7.2.5-PHI1", "7.2.5 branch phi_1", lambda: bm.lattice_branch_stability_coefficient(2.7, "b"), 1.0, 0.0, "dimensionless"),
        ("BUILTUP-PROC-7.2.7-DISTRIBUTION", "7.2.7 distribution", lambda: bm.distribute_fictitious_shear(1000.0, "solid_sheet_and_connectors", 2)["per_connector_system_force_n"], 250.0, 0.0, "N"),
        ("LOCAL-TBL-009", "7.3.2 Table 9", lambda: float(len(ls.table_9_wall_slenderness_catalog()["diagram_groups"])), 4.0, 0.0, "diagram groups"),
        ("LOCAL-EQ-023", "7.3.2 equation (23)", lambda: ls.wall_slenderness_limit_eq23(2.0), 1.30 + 0.15*2.0**2, 1e-12, "dimensionless"),
        ("LOCAL-EQ-024", "7.3.2 equation (24)", lambda: ls.wall_slenderness_limit_eq24(4.0), 2.3, 0.0, "dimensionless"),
        ("LOCAL-EQ-025", "7.3.2 equation (25)", lambda: ls.wall_slenderness_limit_eq25(1.0), 1.2, 0.0, "dimensionless"),
        ("LOCAL-EQ-026", "7.3.2 equation (26)", lambda: ls.wall_slenderness_limit_eq26(2.0), 1.4, 1e-12, "dimensionless"),
        ("LOCAL-EQ-027", "7.3.2 equation (27)", lambda: ls.wall_slenderness_limit_eq27(0.8), 1.0, 0.0, "dimensionless"),
        ("LOCAL-EQ-028", "7.3.2 equation (28)", lambda: ls.wall_slenderness_limit_eq28(2.0), 1.23, 1e-12, "dimensionless"),
        ("LOCAL-EQ-029", "7.3.2 equation (29)", lambda: ls.wall_slenderness_limit_eq29(2.0, 500.0, 500.0), 0.675, 1e-12, "dimensionless"),
        ("LOCAL-PROC-WEB-SLENDERNESS", "7.3.2 web slenderness", lambda: ls.wall_relative_slenderness(500.0, 8.0, 355.0, 206000.0), (500.0/8.0)*math.sqrt(355.0/206000.0), 1e-12, "dimensionless"),
        ("LOCAL-EQ-030", "7.3.4 equation (30)", lambda: ls.longitudinal_stiffener_wall_limit_multiplier_eq30(5.0*600.0*8.0**3, 600.0, 8.0), 2.0, 1e-12, "dimensionless"),
        ("LOCAL-EQ-031", "7.3.6 equation (31)", lambda: ls.reduced_area_i_or_channel_eq31(10000.0, 500.0, 400.0, 8.0), 9200.0, 1e-9, "mm2"),
        ("LOCAL-EQ-032", "7.3.6 equation (32)", lambda: ls.reduced_area_box_central_eq32(12000.0, 500.0, 450.0, 8.0, 300.0, 270.0, 10.0), 10600.0, 1e-9, "mm2"),
        ("LOCAL-EQ-033", "7.3.6 equation (33)", lambda: ls.reduced_area_box_eccentric_eq33(12000.0, 500.0, 450.0, 8.0), 11200.0, 1e-9, "mm2"),
        ("LOCAL-EQ-034", "7.3.6 equation (34)", lambda: ls.reduced_web_height_i_section_eq34(8.0, 2.5, 2.0, 2.5, 355.0, 206000.0), 8.0*(2.0-(2.5/2.0-1.0)*(2.0-1.2-0.15*2.5))*math.sqrt(206000.0/355.0), 1e-9, "mm"),
        ("LOCAL-EQ-035", "7.3.6 equation (35)", lambda: ls.reduced_plate_dimension_box_eq35(8.0, 2.0, 1.5, 2.0, 355.0, 206000.0), 8.0*(1.5-(2.0/1.5-1.0)*(1.5-2.9-0.2*2.0+0.7*1.5))*math.sqrt(206000.0/355.0), 1e-9, "mm"),
        ("LOCAL-EQ-036", "7.3.6 equation (36)", lambda: ls.reduced_web_height_channel_eq36(8.0, 1.5, 1.2, 355.0, 206000.0), 8.0*1.2*math.sqrt(206000.0/355.0), 1e-9, "mm"),
        ("LOCAL-TBL-010", "7.3.8 Table 10", lambda: float(len(ls.table_10_flange_slenderness_catalog()["diagram_groups"])), 4.0, 0.0, "diagram groups"),
        ("LOCAL-EQ-037", "7.3.8 equation (37)", lambda: ls.flange_slenderness_limit_eq37(2.0), 0.56, 1e-12, "dimensionless"),
        ("LOCAL-EQ-038", "7.3.8 equation (38)", lambda: ls.flange_slenderness_limit_eq38(2.0), 0.59, 1e-12, "dimensionless"),
        ("LOCAL-EQ-039", "7.3.8 equation (39)", lambda: ls.flange_slenderness_limit_eq39(2.0), 0.54, 1e-12, "dimensionless"),
        ("LOCAL-EQ-040", "7.3.8 equation (40)", lambda: ls.flange_slenderness_limit_eq40(2.0), 1.23, 1e-12, "dimensionless"),
        ("LOCAL-PROC-FLANGE-SLENDERNESS", "7.3.8 flange slenderness", lambda: ls.flange_relative_slenderness(120.0, 12.0, 355.0, 206000.0), 10.0*math.sqrt(355.0/206000.0), 1e-12, "dimensionless"),
        ("LOCAL-PROC-TABLE-10", "7.3.8 Table 10 edge multiplier", lambda: ls.flange_slenderness_limit("group_3", 2.0, True), (0.40+0.07*2.0)*1.6, 1e-12, "dimensionless"),
        ("LOCAL-PROC-7.3.10", "7.3.10 edge stiffener", lambda: ls.edge_stiffener_requirements(100.0, 355.0, 206000.0, False)["minimum_edge_height_mm"], 30.0, 0.0, "mm"),
        ("LOCAL-PROC-7.3.11", "7.3.11 two-plane factor cap", lambda: ls.two_plane_slenderness_increase_factor(1.0, 10000.0, 355.0, 1000000.0), 1.25, 0.0, "dimensionless"),

        ("BEND-EQ-041", "8.2.1 equation (41)", lambda: bend.elastic_bending_utilization_eq41(1e8, 1e6, 250.0, 1.0), 0.4, 1e-12, "dimensionless"),
        ("BEND-EQ-042", "8.2.1 equation (42)", lambda: bend.elastic_shear_utilization_eq42(100000.0, 200000.0, 2e8, 8.0, 145.0, 1.0), 100000.0*200000.0/(2e8*8.0*145.0), 1e-12, "dimensionless"),
        ("BEND-EQ-043", "8.2.1 equation (43)", lambda: bend.elastic_combined_normal_utilization_eq43(1e8, 2e7, 1e10, 2e8, 1e8, 1e12, 200.0, 50.0, 10000.0, 355.0, 1.0), 210.0/355.0, 1e-12, "dimensionless"),
        ("BEND-EQ-044", "8.2.1 equation (44)", lambda: float(bend.elastic_web_equivalent_stress_checks_eq44(100.0, 20.0, 50.0, 355.0, 205.9, 1.0)["equivalent_utilization"]), 0.87*math.sqrt(100.0**2-100.0*20.0+20.0**2+3.0*50.0**2)/355.0, 1e-12, "dimensionless"),
        ("BEND-EQ-045", "8.2.1 equation (45)", lambda: bend.bolt_hole_factor_eq45(100.0, 20.0), 1.25, 1e-12, "dimensionless"),
        ("BEND-EQ-046", "8.2.2 equation (46)", lambda: bend.local_web_compression_utilization_eq46(100.0, 250.0, 1.0), 0.4, 1e-12, "dimensionless"),
        ("BEND-EQ-047", "8.2.2 equation (47)", lambda: bend.local_web_compression_stress_eq47(80000.0, 100.0, 8.0), 100.0, 1e-12, "N/mm2"),
        ("BEND-EQ-048", "8.2.2 equation (48)", lambda: bend.effective_load_length_eq48(100.0, 20.0), 140.0, 1e-12, "mm"),
        ("BEND-EQ-049", "8.2.2 equation (49)", lambda: bend.effective_load_length_crane_eq49(3.25, 8e6, 8.0), 325.0, 1e-9, "mm"),
        ("BEND-EQ-050", "8.2.3 equation (50)", lambda: bend.plastic_bending_utilization_eq50(1e8, 1.2, 1.0, 1e6, 250.0, 1.0), 1.0/3.0, 1e-12, "dimensionless"),
        ("BEND-EQ-051", "8.2.3 equation (51)", lambda: bend.plastic_biaxial_bending_utilization_eq51(1e8, 2e7, 1.2, 1.2, 1.0, 1e6, 5e5, 250.0, 1.0), 1.0/3.0+2e7/(1.2*5e5*250.0), 1e-12, "dimensionless"),
        ("BEND-EQ-052", "8.2.3 equation (52)", lambda: bend.plastic_shear_reduction_factor_eq52(80.0, 100.0, 1.0), 1.0-0.2/1.25*0.8**4, 1e-12, "dimensionless"),
        ("BEND-EQ-053", "8.2.3 equation (53)", lambda: bend.constrained_torsion_utilization_eq53(1e8, 1e10, 1.2, 1.0, 1e6, 2.0, 1e8, 250.0, 1.0), 1.0/3.0+0.2, 1e-12, "dimensionless"),
        ("BEND-EQ-054", "8.2.3 equation (54)", lambda: bend.support_shear_x_utilization_eq54(100000.0, 1000.0, 100.0, 1.0), 1.0, 1e-12, "dimensionless"),
        ("BEND-EQ-055", "8.2.3 equation (55)", lambda: bend.support_shear_y_utilization_eq55(100000.0, 500.0, 100.0, 1.0), 1.0, 1e-12, "dimensionless"),
        ("BEND-EQ-056", "8.2.5 equation (56)", lambda: bend.redistributed_design_moment_eq56(180.0, 120.0), 150.0, 1e-12, "N*mm"),
        ("BEND-EQ-057", "8.2.5 equation (57)", lambda: bend.effective_moment_hinged_end_eq57([120.0,150.0],[0.0,5.0],10.0), 120.0, 1e-12, "N*mm"),
        ("BEND-EQ-058", "8.2.5 equation (58)", lambda: bend.effective_moment_intermediate_span_eq58(160.0), 80.0, 1e-12, "N*mm"),
        ("BEND-EQ-059", "8.2.8 equation (59)", lambda: bend.bimetal_bending_utilization_eq59(1e8, 1.2, 1.0, 1e6, 250.0, 1.0), 1.0/3.0, 1e-12, "dimensionless"),
        ("BEND-EQ-060", "8.2.8 equation (60)", lambda: bend.bimetal_biaxial_bending_utilization_eq60(1e8, 2e7, 1.2, 1.15, 1.0, 1e6, 5e5, 250.0, 300.0, 1.0), 1.0/3.0+2e7/(1.15*5e5*300.0), 1e-12, "dimensionless"),
        ("BEND-EQ-061", "8.2.8 equation (61)", lambda: bend.bimetal_major_axis_coefficient_eq61(1.2, 1.0, 1.2), (1.0*1.2+0.25-0.0833/1.2**2)/(1.0+0.167), 1e-12, "dimensionless"),
        ("BEND-EQ-062", "8.2.8 equation (62)", lambda: bend.bimetal_shear_reduction_factor_eq62(80.0, 100.0, 1.0, 1.2), 1.0-0.2/1.45*0.8**4, 1e-12, "dimensionless"),
        ("BEND-TBL-10A", "8.2.3 Table 10a", lambda: float(len(bend.table_10a_constrained_torsion_catalog()["nodes"])), 11.0, 0.0, "nodes"),
        ("BEND-TBL-E1", "Annex E Table E.1", lambda: float(len(bend.annex_e1_plastic_coefficient_catalog()["section_types"])), 12.0, 0.0, "section types"),
        ("BEND-PROC-8.1", "8.1 class routing", lambda: 1.0 if bend.bending_member_class_requirements(1, False, False, False)["required_route"] == "elastic" else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.1-STRESS", "8.2.1 stress-point route", lambda: bend.elastic_combined_normal_utilization_eq43(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0), 0.0, 0.0, "dimensionless"),
        ("BEND-PROC-8.2.1-HOLES", "8.2.1 bolt-hole adjustment", lambda: bend.apply_bolt_hole_factor(0.8, 1.25), 1.0, 1e-12, "dimensionless"),
        ("BEND-PROC-8.2.2-LENGTH", "8.2.2 load-length route", lambda: bend.effective_load_length_by_case("welded_or_rolled",100.0,20.0,None,None,None), 140.0, 1e-12, "mm"),
        ("BEND-PROC-8.2.3-APPLICABILITY", "8.2.3 plastic applicability", lambda: 1.0 if bend.plastic_bending_applicability(2,"i_section",355.0,100.0,145.0,True,False)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-E1-INTERPOLATION", "Annex E Table E.1 interpolation", lambda: bend.annex_e1_base_coefficients("1",0.75,False)["c_x"], 1.095, 1e-12, "dimensionless"),
        ("BEND-PROC-E1-CAP", "Annex E Table E.1 cap", lambda: bend.apply_annex_e1_load_factor_cap(1.47,1.1), 1.265, 1e-12, "dimensionless"),
        ("BEND-PROC-10A-INTERPOLATION", "Table 10a interpolation", lambda: bend.constrained_torsion_coefficient_table_10a(0.15), (1.636+1.845)/2.0, 1e-12, "dimensionless"),
        ("BEND-PROC-PURE-BENDING", "8.2.3 pure-bending coefficients", lambda: bend.pure_bending_modified_coefficients(1.2,1.4)["c_xm"], 1.1, 1e-12, "dimensionless"),
        ("BEND-PROC-8.2.4", "8.2.4 variable-section route", lambda: 1.0 if bend.variable_section_plastic_routing(True,False)["route"] == "full_clause_8_2_3" else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.5-APPLICABILITY", "8.2.5 continuous-beam applicability", lambda: 1.0 if bend.continuous_beam_partial_redistribution_applicability(10000.0,11000.0,True,True,True)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.5-MOMENT", "8.2.5 effective-moment route", lambda: bend.effective_moment_by_end_condition("intermediate_span",[100.0],None,None), 50.0, 1e-12, "N*mm"),
        ("BEND-PROC-8.2.6", "8.2.6 biaxial redistribution", lambda: 1.0 if bend.biaxial_redistribution_route(True,True)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.7", "8.2.7 class-3 route", lambda: 1.0 if bend.class_3_plastic_hinge_route(True,True,True,True,True,True)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.8-APPLICABILITY", "8.2.8 bimetal applicability", lambda: 1.0 if bend.bimetal_bending_applicability("i_section",True,True,100.0,145.0,50.0,145.0,False)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("BEND-PROC-8.2.8-CYR", "8.2.8 bimetal minor coefficient", lambda: bend.bimetal_minor_axis_coefficient("i_section",1.5), 1.15, 1e-12, "dimensionless"),

        ("CRANE-EQ-063", "8.3.3 equation (63)", lambda: stab.crane_runway_equivalent_stress_utilization_eq63(0.87,100.0,10.0,20.0,30.0,5.0,355.0), 0.87/355.0*math.sqrt(110.0**2-110.0*20.0+20.0**2+3.0*35.0**2), 1e-12, "dimensionless"),
        ("CRANE-EQ-064", "8.3.3 equation (64)", lambda: stab.crane_runway_longitudinal_normal_utilization_eq64(100.0,20.0,300.0), 0.4, 1e-12, "dimensionless"),
        ("CRANE-EQ-065", "8.3.3 equation (65)", lambda: stab.crane_runway_transverse_normal_utilization_eq65(80.0,20.0,250.0), 0.4, 1e-12, "dimensionless"),
        ("CRANE-EQ-066", "8.3.3 equation (66)", lambda: stab.crane_runway_shear_utilization_eq66(30.0,10.0,10.0,100.0), 0.5, 1e-12, "dimensionless"),
        ("CRANE-EQ-067-SIGMA-X", "8.3.3 equation (67)", lambda: stab.crane_runway_stress_components_eq67(1e8,1e6,1.1,1.2,100000.0,200.0,10.0,3765000.0,1000.0,1e8,800.0,200000.0)["sigma_x_n_mm2"], 100.0, 1e-12, "N/mm2"),
        ("CRANE-EQ-067-SIGMA-LOC-Y", "8.3.3 equation (67)", lambda: stab.crane_runway_stress_components_eq67(1e8,1e6,1.1,1.2,100000.0,200.0,10.0,3765000.0,1000.0,1e8,800.0,200000.0)["sigma_local_y_n_mm2"], 66.0, 1e-12, "N/mm2"),
        ("CRANE-EQ-068", "8.3.3 equation (68)", lambda: stab.crane_runway_local_torsional_moment_eq68(1.1,1.2,100000.0,20.0,10000.0,150.0), 3765000.0, 1e-9, "N*mm"),
        ("CRANE-PROC-8.3.5", "8.3.5 bimetal crane route", lambda: stab.bimetal_crane_runway_strength_utilization(1e8,2e7,1.2,1.0,1e6,5e5,300.0,355.0,1.0,True), abs(1e8/(1.2*1e6*300.0)+2e7/(1.15*5e5*355.0)), 1e-12, "dimensionless"),
        ("STAB-EQ-069", "8.4.1 equation (69)", lambda: stab.lateral_torsional_stability_utilization_eq69(1e8,0.8,1e6,250.0,1.0), 0.5, 1e-12, "dimensionless"),
        ("STAB-EQ-070", "8.4.1 equation (70)", lambda: stab.lateral_torsional_combined_utilization_eq70(1e8,2e7,1e9,0.8,1e6,5e5,1e10,250.0,1.0), 0.5+2e7/(5e5*250.0)+1e9/(1e10*250.0), 1e-12, "dimensionless"),
        ("STAB-PROC-8.4.3", "8.4.3 crane stability route", lambda: stab.crane_runway_lateral_torsional_stability_utilization(1e8,2e7,1e9,0.8,1e6,5e5,1e10,250.0,1.0), 0.5+2e7/(5e5*250.0)+1e9/(1e10*250.0), 1e-12, "dimensionless"),
        ("STAB-EQ-071", "8.4.4 equation (71)", lambda: stab.table_11_limit_eq71(300.0,20.0,600.0), 0.35+0.0032*15.0+(0.76-0.02*15.0)*0.5, 1e-12, "dimensionless"),
        ("STAB-EQ-072", "8.4.4 equation (72)", lambda: stab.table_11_limit_eq72(300.0,20.0,600.0), 0.57+0.0032*15.0+(0.92-0.02*15.0)*0.5, 1e-12, "dimensionless"),
        ("STAB-EQ-073", "8.4.4 equation (73)", lambda: stab.table_11_limit_eq73(300.0,20.0,600.0), 0.41+0.0032*15.0+(0.73-0.016*15.0)*0.5, 1e-12, "dimensionless"),
        ("STAB-EQ-074", "8.4.5 equation (74)", lambda: stab.compressed_flange_equivalent_force_eq74(2000.0,3000.0,355.0,355.0), 976250.0, 1e-9, "N"),
        ("STAB-EQ-075", "8.4.5 equation (75)", lambda: stab.continuous_bracing_force_per_length_eq75(10000.0,5000.0), 6.0, 1e-12, "N/mm"),
        ("STAB-EQ-076", "8.4.6 equation (76)", lambda: stab.class_2_3_stability_reduction_eq76(1.5,2.0), 0.7, 1e-12, "dimensionless"),
        ("STAB-EQ-077", "8.4.6 equation (77)", lambda: stab.class_2_3_coefficient_eq77(250e6,1e6,250.0,1.0,0.8,1.5), 1.2, 1e-12, "dimensionless"),
        ("STAB-PROC-REL-SLENDERNESS", "8.4.4 compressed-flange slenderness", lambda: stab.compressed_flange_relative_slenderness(5000.0,300.0,355.0,206000.0), 5000.0/300.0*math.sqrt(355.0/206000.0), 1e-12, "dimensionless"),
        ("STAB-TBL-011-NOTE", "8.4.4 Table 11 notes 2-3", lambda: stab.table_11_limit("upper_flange",300.0,20.0,600.0,True,355.0,142.0), (0.35+0.0032*15.0+(0.76-0.02*15.0)*0.5)*1.2*math.sqrt(355.0/142.0), 1e-12, "dimensionless"),
        ("STAB-PROC-8.4.2", "8.4.2 effective length", lambda: stab.effective_length_by_restraint(10000.0,[2500.0,6000.0],False,False), 4000.0, 0.0, "mm"),
        ("STAB-PROC-8.4.4", "8.4.4 exemption", lambda: 1.0 if stab.lateral_stability_check_exemption(False,0.4,0.5,0.75)["exempt"] else 0.0, 1.0, 0.0, "boolean as 0/1"),
        ("STAB-TBL-012", "8.5.4 Table 12 exact node", lambda: stab.table_12_c_cr_coefficient("welded",4.0), 34.6, 0.0, "dimensionless"),
        ("STAB-TBL-013", "8.5.4 Table 13 finite case", lambda: stab.table_13_beta("other_case"), 0.8, 0.0, "dimensionless"),
        ("ZH-EQ-001", "Annex Ж equation (Ж.1)", lambda: stab.annex_zh_phi_b_eq_zh1(0.85), 0.85, 0.0, "dimensionless"),
        ("ZH-EQ-002", "Annex Ж equation (Ж.2)", lambda: stab.annex_zh_phi_b_eq_zh2(1.0), 0.89, 1e-12, "dimensionless"),
        ("ZH-EQ-003", "Annex Ж equation (Ж.3)", lambda: stab.annex_zh_phi1_eq_zh3(10.0,1e8,1e10,500.0,5000.0,206000.0,355.0), 10.0*0.01*0.01*206000.0/355.0, 1e-12, "dimensionless"),
        ("ZH-EQ-004", "Annex Ж equation (Ж.4)", lambda: stab.annex_zh_alpha_rolled_eq_zh4(1e6,1e8,5000.0,500.0,False), 1.0, 1e-12, "dimensionless"),
        ("ZH-EQ-005", "Annex Ж equation (Ж.5)", lambda: stab.annex_zh_alpha_built_up_eq_zh5(5000.0,20.0,500.0,300.0,10.0,False), 4.0*(5000.0*20.0/(500.0*300.0))**2*(1.0+0.5*500.0*10.0**3/(300.0*20.0**3)), 1e-12, "dimensionless"),
        ("ZH-EQ-006", "Annex Ж equation (Ж.6)", lambda: stab.annex_zh_monosymmetric_phi1_eq_zh6(10.0,1e8,1e10,500.0,300.0,5000.0,206000.0,355.0), 10.0*0.01*2.0*500.0*300.0/5000.0**2*206000.0/355.0, 1e-12, "dimensionless"),
        ("ZH-EQ-007", "Annex Ж equation (Ж.7)", lambda: stab.annex_zh_monosymmetric_phi2_eq_zh7(10.0,1e8,1e10,500.0,200.0,5000.0,206000.0,355.0), 10.0*0.01*2.0*500.0*200.0/5000.0**2*206000.0/355.0, 1e-12, "dimensionless"),
        ("ZH-EQ-008", "Annex Ж equation (Ж.8)", lambda: stab.annex_zh_flange_inertia_ratio_n_eq_zh8(3.0,1.0), 0.75, 0.0, "dimensionless"),
        ("ZH-EQ-009", "Annex Ж equation (Ж.9)", lambda: stab.annex_zh_psi_a_eq_zh9(2.0,9.0,0.5), (2.0+math.sqrt(13.0))*0.5, 1e-12, "dimensionless"),
        ("ZH-EQ-010", "Annex Ж equation (Ж.10)", lambda: stab.annex_zh_delta_eq_zh10(0.75,0.1), 0.75+0.734*0.1, 1e-12, "dimensionless"),
        ("ZH-EQ-011", "Annex Ж equation (Ж.11)", lambda: stab.annex_zh_mu_eq_zh11(0.75,0.1), 0.75+1.145*0.1, 1e-12, "dimensionless"),
        ("ZH-EQ-012", "Annex Ж equation (Ж.12)", lambda: stab.annex_zh_beta_eq_zh12(0.75,300.0,500.0), (2.0*0.75-1.0)*(0.47-0.035*0.6*(1.0+0.6-0.072*0.6**2)), 1e-12, "dimensionless"),
        ("ZH-EQ-013", "Annex Ж equation (Ж.13)", lambda: stab.annex_zh_eta_eq_zh13(0.75,3.0,1.0,5000.0,500.0), (1.0-0.75)*(9.87*0.75+0.385*3.0*(5000.0/500.0)**2), 1e-12, "dimensionless"),
        ("ZH-TBL-001", "Annex Ж Table Ж.1", lambda: stab.annex_zh_table_1_psi("unbraced_pure_bending",10.0), math.sqrt(0.95*10.0+5.78), 1e-12, "dimensionless"),
        ("ZH-TBL-002", "Annex Ж Table Ж.2", lambda: stab.annex_zh_table_2_psi("point_load_at_tip","tension",20.0), 4.2, 1e-12, "dimensionless"),
        ("ZH-TBL-003", "Annex Ж Table Ж.3", lambda: stab.annex_zh_table_3_phi_b("less_developed",1.0,1.0,0.75), 0.89, 1e-12, "dimensionless"),
        ("ZH-TBL-004", "Annex Ж Table Ж.4", lambda: stab.annex_zh_table_4_b("diagram_row_2","point_midspan",1.5,2.0,0.2), 0.5, 0.0, "dimensionless"),
        ("ZH-TBL-005", "Annex Ж Table Ж.5", lambda: stab.annex_zh_table_5_c_d("point_midspan","i_section_n_le_0.9",eta=10.0)[0], 3.3, 1e-12, "dimensionless"),
        ("ZH-PROC-INTERPOLATION", "Annex Ж.6 interpolation", lambda: stab.annex_zh_interpolate_psi_a_for_n(0.95,2.0,4.0), 3.0, 1e-12, "dimensionless"),
        ("ZH-PROC-T-MODIFIER", "Annex Ж.6 T-section modifier", lambda: stab.apply_t_section_low_alpha_modifier(5.0,20.0,"point_midspan"), 4.4, 1e-12, "dimensionless"),
    ]

    cases: list[dict[str, Any]] = []
    for case_id, reference, function, expected, tolerance, unit in configured:
        cases.append(
            _validation_case(
                case_id,
                reference,
                "implementation_self_check",
                float(function()),
                float(expected),
                tolerance,
                unit,
                "Arithmetic/transcription self-check; not a worked example supplied by the standard.",
            )
        )

    table_d1 = json.loads((_DATA_DIR / "annex_d_table_d1_stability_coefficients.json").read_text(encoding="utf-8"))
    scale = float(table_d1["scale_factor"])
    for row in table_d1["rows"]:
        slenderness = float(row["relative_slenderness"])
        for section_type in ("a", "b", "c"):
            reference = float(row[section_type]) / scale
            calculated = am.central_compression_stability_coefficient(slenderness, section_type)
            cases.append(
                _validation_case(
                    f"AXIAL-D1-{section_type.upper()}-{slenderness:g}",
                    f"Annex D Table D.1, type {section_type}, lambda_bar={slenderness:g}",
                    "standard_table_cross_check",
                    calculated,
                    reference,
                    0.0010001,
                    "dimensionless",
                    "Compared with the printed integer divided by 1000; tolerance represents rounding to three decimals.",
                )
            )

    table_10a = json.loads((_DATA_DIR / "table_10a_constrained_torsion_coefficients.json").read_text(encoding="utf-8"))
    for node in table_10a["nodes"]:
        ratio = float(node["ratio"])
        reference = float(node["c_omega"])
        cases.append(
            _validation_case(
                f"BEND-10A-{ratio:g}",
                f"Table 10a, normalized ratio={ratio:g}",
                "standard_table_exact_node_cross_check",
                bend.constrained_torsion_coefficient_table_10a(ratio),
                reference,
                1e-12,
                "dimensionless",
                "Exact printed node transcribed from Table 10a.",
            )
        )

    table_e1 = json.loads((_DATA_DIR / "annex_e_table_e1_plastic_coefficients.json").read_text(encoding="utf-8"))
    for section_type, row in table_e1["section_types"].items():
        if row.get("ratio_nodes") is None:
            ratios = [None]
            cx_values = [float(row["c_x_constant"])]
            cy_values = [float(row["c_y_constant"])]
        else:
            ratios = [float(value) for value in row["ratio_nodes"]]
            cx_values = [float(value) for value in row["c_x"]]
            cy_values = [float(value) for value in row["c_y"]]
        for ratio, cx_reference, cy_reference in zip(ratios, cx_values, cy_values):
            result = bend.annex_e1_base_coefficients(section_type, ratio, True)
            ratio_label = "constant" if ratio is None else f"{ratio:g}"
            cases.append(_validation_case(f"BEND-E1-{section_type}-CX-{ratio_label}", f"Annex E Table E.1, type {section_type}, A_f/A_w={ratio_label}, c_x", "standard_table_exact_node_cross_check", float(result["c_x"]), cx_reference, 1e-12, "dimensionless", "Exact transcribed Table E.1 coefficient."))
            cases.append(_validation_case(f"BEND-E1-{section_type}-CY-{ratio_label}", f"Annex E Table E.1, type {section_type}, A_f/A_w={ratio_label}, c_y", "standard_table_exact_node_cross_check", float(result["c_y"]), cy_reference, 1e-12, "dimensionless", "Exact transcribed Table E.1 coefficient."))
        n_result = bend.annex_e1_base_coefficients(section_type, ratios[0], True)
        cases.append(_validation_case(f"BEND-E1-{section_type}-N", f"Annex E Table E.1, type {section_type}, n when M_y=0", "standard_table_exact_node_cross_check", float(n_result["n"]), float(row["n_when_my_zero"]), 1e-12, "dimensionless", "Exact transcribed Table E.1 exponent."))


    # v0.8 equations (78)-(100) representative arithmetic checks.
    cases.extend([
        _validation_case("BLS-EQ-078", "8.5.2 equation (78)", "arithmetic_self_check", bls.bending_normal_stress_eq78(1e8, 300, 2e8), 150.0, 1e-12, "N/mm2", "Direct M*y/I check."),
        _validation_case("BLS-EQ-079", "8.5.2 equation (79)", "arithmetic_self_check", bls.average_web_shear_stress_eq79(200000, 10, 1000), 20.0, 1e-12, "N/mm2", "Direct Q/(tw*hw) check."),
        _validation_case("BLS-EQ-081", "8.5.3 equation (81)", "arithmetic_self_check", bls.critical_normal_web_stress_eq81(30, 355, 3), 30*355/9, 1e-12, "N/mm2", "Direct critical stress check."),
        _validation_case("BLS-EQ-082", "8.5.3 equation (82)", "arithmetic_self_check", bls.critical_local_web_stress_eq82(28.5, 1.56, 355, 3), 28.5*1.56*355/9, 1e-12, "N/mm2", "Direct critical local stress check."),
        _validation_case("BLS-EQ-083", "8.5.3 equation (83)", "arithmetic_self_check", bls.critical_web_shear_stress_eq83(2, 205, 3), 10.3*(1+0.76/4)*205/9, 1e-12, "N/mm2", "Direct critical shear check."),
        _validation_case("BLS-EQ-084", "8.5.4 equation (84)", "arithmetic_self_check", bls.flange_restraint_parameter_eq84(0.75,320,960,24,12), 2.0, 1e-12, "dimensionless", "Direct delta check."),
        _validation_case("BLS-EQ-090", "8.5.12 equation (90)", "arithmetic_self_check", bls.upper_plate_critical_normal_no_local_eq90(355,2,200,1000), 4.76*355/(0.8*4), 1e-12, "N/mm2", "Direct plate-1 critical stress check."),
        _validation_case("BLS-EQ-093", "8.5.12 equation (93)", "arithmetic_self_check", bls.upper_plate_psi_and_slenderness_eq93(400,200,10,355,206000)["psi"], 6.25, 1e-12, "dimensionless", "mu1 cap and psi check."),
        _validation_case("BLS-EQ-097", "8.5.18 equation (97)", "arithmetic_self_check", bls.flange_outstand_limit_eq97(355,200), 0.5*math.sqrt(355/200), 1e-12, "dimensionless", "Direct flange limit check."),
        _validation_case("BLS-EQ-098", "8.5.18 equation (98)", "arithmetic_self_check", bls.box_flange_plate_limit_eq98(355,200), 1.5*math.sqrt(355/200), 1e-12, "dimensionless", "Direct box flange limit check."),
        _validation_case("BLS-EQ-099", "8.5.19 equation (99)", "arithmetic_self_check", bls.class_2_3_flange_outstand_limit_eq99(3.0), 0.35, 1e-12, "dimensionless", "Direct class-2/3 flange limit check."),
        _validation_case("BLS-EQ-100", "8.5.19 equation (100)", "arithmetic_self_check", bls.class_2_3_box_flange_limit_eq100(3.0), 1.125, 1e-12, "dimensionless", "Direct class-2/3 box limit check."),
    ])

    table_data = json.loads((_DATA_DIR / "tables_14_to_19_bending_local_stability.json").read_text(encoding="utf-8"))
    for i, rho in enumerate(table_data["table_14"]["row_nodes"]):
        for j, ratio in enumerate(table_data["table_14"]["column_nodes"]):
            ref = float(table_data["table_14"]["values"][i][j])
            cases.append(_validation_case(f"BLS-T14-{rho}-{ratio}", "Table 14", "standard_table_exact_node_cross_check", bls.table_14_c1(float(rho), float(ratio)), ref, 1e-12, "dimensionless", "Exact printed Table 14 node."))
    for i, delta in enumerate(table_data["table_15"]["row_nodes"]):
        for j, ratio in enumerate(table_data["table_15"]["column_nodes"]):
            ref = float(table_data["table_15"]["values"][i][j])
            cases.append(_validation_case(f"BLS-T15-{delta}-{ratio}", "Table 15", "standard_table_exact_node_cross_check", bls.table_15_c2(float(delta), float(ratio)), ref, 1e-12, "dimensionless", "Exact printed Table 15 node."))
    for ratio, ref in zip(table_data["table_16"]["ratio_nodes"], table_data["table_16"]["c_cr"]):
        cases.append(_validation_case(f"BLS-T16-{ratio}", "Table 16", "standard_table_exact_node_cross_check", bls.table_16_c_cr(float(ratio), 30.0), float(ref), 1e-12, "dimensionless", "Exact printed Table 16 node."))
    for alpha, ref in zip(table_data["table_17"]["alpha_nodes"], table_data["table_17"]["c_cr"]):
        cases.append(_validation_case(f"BLS-T17-{alpha}", "Table 17", "standard_table_exact_node_cross_check", bls.table_17_c_cr(float(alpha)), float(ref), 1e-12, "dimensionless", "Exact printed Table 17 node."))
    for i, shear_ratio in enumerate(table_data["table_18"]["row_nodes"]):
        for j, slenderness in enumerate(table_data["table_18"]["column_nodes"]):
            ref = float(table_data["table_18"]["values"][i][j])
            cases.append(_validation_case(f"BLS-T18-{shear_ratio}-{slenderness}", "Table 18", "standard_table_exact_node_cross_check", bls.table_18_alpha(float(shear_ratio), float(slenderness)), ref, 1e-12, "dimensionless", "Exact printed Table 18 node."))

    # v0.9 base-plate and combined-force checks.
    cases.extend([
        _validation_case("BPCS-EQ-101", "8.6.2 equation (101)", "implementation_self_check", bc.base_plate_required_thickness_eq101(125000.0, 250.0, 1.0), math.sqrt(3000.0), 1e-12, "mm", "Direct arithmetic check."),
        _validation_case("BPCS-EQ-102", "8.6.2 equation (102)", "implementation_self_check", bc.base_plate_cantilever_moment_eq102(1.0, 100.0), 5000.0, 1e-12, "N*mm/mm", "Direct arithmetic check."),
        _validation_case("BPCS-EQ-103A", "8.6.2 equation (103)", "implementation_self_check", bc.base_plate_four_side_moments_eq103(1.0, 100.0, 0.048, 0.037)["moment_short_direction_n_mm_per_mm"], 480.0, 1e-12, "N*mm/mm", "Short-direction arithmetic check."),
        _validation_case("BPCS-EQ-103B", "8.6.2 equation (103)", "implementation_self_check", bc.base_plate_four_side_moments_eq103(1.0, 100.0, 0.048, 0.037)["moment_long_direction_n_mm_per_mm"], 370.0, 1e-12, "N*mm/mm", "Long-direction arithmetic check."),
        _validation_case("BPCS-EQ-104", "8.6.2 equation (104)", "implementation_self_check", bc.base_plate_three_side_moment_eq104(1.0, 100.0, 0.112), 1120.0, 1e-12, "N*mm/mm", "Direct arithmetic check."),
        _validation_case("BPCS-EQ-105", "9.1.1 equation (105)", "implementation_self_check", bc.combined_force_strength_utilization_eq105(100000.0,2000.0,1e7,2e7,1e9,1.0,1.0,1.0,1e6,2e6,1e9,250.0,1.0), 0.284, 1e-12, "dimensionless", "Direct term-by-term check."),
        _validation_case("BPCS-EQ-106", "9.1.1 equation (106)", "implementation_self_check", bc.combined_force_point_utilization_eq106(100000.0,2000.0,1e7,100.0,1e9,2e7,-50.0,2e9,1e9,100.0,1e12,250.0,1.0), 50.6/250.0, 1e-12, "dimensionless", "Signed stress-superposition check."),
        _validation_case("BPCS-EQ-107", "9.1.3 equation (107)", "implementation_self_check", bc.high_strength_asymmetric_tension_fiber_utilization_eq107(100000.0,2000.0,2e7,0.8,1e6,500.0,1.3,1.0), 0.065, 1e-12, "dimensionless", "Direct subtraction and absolute-value check."),
        _validation_case("BPCS-EQ-108", "9.1.3 equation (108)", "implementation_self_check", bc.high_strength_asymmetric_delta_eq108(100000.0,2.0,2000.0,250.0), 0.92, 1e-12, "dimensionless", "Direct arithmetic check."),
        _validation_case("BPCS-PROC-MAX", "8.6.2 governing moment", "implementation_self_check", bc.base_plate_maximum_unit_width_moment([100.0,250.0,200.0]), 250.0, 0.0, "N*mm/mm", "Maximum selection check."),
        _validation_case("BPCS-PROC-TWO-SIDE", "8.6.2 two-adjacent-side geometry", "implementation_self_check", bc.base_plate_two_adjacent_sides_geometry(300.0,400.0)["diagonal_d1_mm"], 500.0, 1e-12, "mm", "3-4-5 rectangle geometry."),
        _validation_case("BPCS-PROC-9.1.1", "9.1.1 applicability", "implementation_self_check", 1.0 if bc.equation_105_applicability(355.0,False,40.0,100.0,100000.0,2000.0,250.0,True,True)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1", "Applicability routing check."),
        _validation_case("BPCS-PROC-9.1.2", "9.1.2 omission", "implementation_self_check", 1.0 if bc.equation_105_omission_rule_clause_9_1_2(20.0,True,True)["may_omit_equation_105"] else 0.0, 1.0, 0.0, "boolean as 0/1", "Boundary omission check."),
        _validation_case("BPCS-PROC-9.1.3", "9.1.3 applicability", "implementation_self_check", 1.0 if bc.equation_107_applicability(460.0,True)["permitted"] else 0.0, 1.0, 0.0, "boolean as 0/1", "High-strength asymmetric-section route."),
    ])
    e2 = bc.annex_e2_catalog()
    for index, ratio in enumerate(e2["four_sides"]["ratio_nodes"]):
        lookup = bc.annex_e2_base_plate_coefficients("four_sides", float(ratio))
        cases.append(_validation_case(f"BPCS-E2-A1-{ratio}", "Annex E Table E.2", "standard_table_exact_node_cross_check", lookup["alpha_1"], float(e2["four_sides"]["coefficients"]["alpha_1"][index]), 0.0, "dimensionless", "Exact printed alpha_1 node."))
        cases.append(_validation_case(f"BPCS-E2-A2-{ratio}", "Annex E Table E.2", "standard_table_exact_node_cross_check", lookup["alpha_2"], float(e2["four_sides"]["coefficients"]["alpha_2"][index]), 0.0, "dimensionless", "Exact printed alpha_2 node."))
    for index, ratio in enumerate(e2["three_sides"]["ratio_nodes"]):
        lookup = bc.annex_e2_base_plate_coefficients("three_sides", float(ratio))
        cases.append(_validation_case(f"BPCS-E2-A3-{ratio}", "Annex E Table E.2", "standard_table_exact_node_cross_check", lookup["alpha_3"], float(e2["three_sides"]["coefficients"]["alpha_3"][index]), 0.0, "dimensionless", "Exact printed alpha_3 node."))
    cases.append(_validation_case("BPCS-E2-A1-GT2", "Annex E Table E.2", "standard_table_terminal_column_cross_check", bc.annex_e2_base_plate_coefficients("four_sides",2.1)["alpha_1"], 0.125, 0.0, "dimensionless", "Printed >2 terminal column."))
    cases.append(_validation_case("BPCS-E2-A2-GT2", "Annex E Table E.2", "standard_table_terminal_column_cross_check", bc.annex_e2_base_plate_coefficients("four_sides",2.1)["alpha_2"], 0.037, 0.0, "dimensionless", "Printed >2 terminal column."))
    cases.append(_validation_case("BPCS-E2-A3-GT2", "Annex E Table E.2", "standard_table_terminal_column_cross_check", bc.annex_e2_base_plate_coefficients("three_sides",2.1)["alpha_3"], 0.133, 0.0, "dimensionless", "Printed >2 terminal column."))

    # v0.10 Section 9.2 and Annex D checks.
    cases.extend([
        _validation_case("BC-EQ-109", "9.2.2 equation (109)", "implementation_self_check", beamcol.beam_column_in_plane_utilization_eq109(200000.0,0.8,3000.0,250.0,1.0), 1.0/3.0, 1e-12, "dimensionless", "Direct utilization check."),
        _validation_case("BC-EQ-110", "9.2.2 equation (110)", "implementation_self_check", beamcol.effective_relative_eccentricity_eq110(1.2,2.0), 2.4, 1e-12, "dimensionless", "Direct eta*m check."),
        _validation_case("BC-EQ-111", "9.2.4 equation (111)", "implementation_self_check", beamcol.beam_column_out_of_plane_utilization_eq111(200000.0,0.5,0.8,3000.0,250.0,1.0), 2.0/3.0, 1e-12, "dimensionless", "Direct out-of-plane utilization check."),
        _validation_case("BC-EQ-112", "9.2.5 equation (112)", "implementation_self_check", beamcol.out_of_plane_coefficient_c_eq112(0.7,1.0,2.0), 1.0/2.4, 1e-12, "dimensionless", "Direct low-eccentricity c check."),
        _validation_case("BC-EQ-113", "9.2.5 equation (113)", "implementation_self_check", beamcol.out_of_plane_coefficient_c_eq113(10.0,0.8,0.9), 1.0/(1.0+10.0*0.8/0.9), 1e-12, "dimensionless", "Direct high-eccentricity c check."),
        _validation_case("BC-EQ-114", "9.2.5 equation (114)", "implementation_self_check", beamcol.out_of_plane_coefficient_c_eq114(7.5,0.2,0.1), 0.15, 1e-12, "dimensionless", "Midpoint interpolation check."),
        _validation_case("BC-EQ-115", "9.2.8 equation (115)", "implementation_self_check", beamcol.central_compression_out_of_plane_utilization_eq115(100000.0,0.8,2000.0,250.0,1.0), 0.25, 1e-12, "dimensionless", "Direct central-compression check."),
        _validation_case("BC-EQ-116", "9.2.9 equation (116)", "implementation_self_check", beamcol.biaxial_beam_column_utilization_eq116(100000.0,0.5,2000.0,250.0,1.0), 0.4, 1e-12, "dimensionless", "Direct biaxial utilization check."),
        _validation_case("BC-EQ-117", "9.2.9 equation (117)", "implementation_self_check", beamcol.biaxial_stability_coefficient_eq117(0.6,0.5), 0.6*(0.6*0.5**(1/3)+0.4*0.5**0.25), 1e-12, "dimensionless", "Direct phi_exy check."),
        _validation_case("BC-EQ-118", "9.2.9 equation (118)", "implementation_self_check", beamcol.relative_eccentricity_x_eq118(20.0,3000.0,500000.0), 0.12, 1e-12, "dimensionless", "Direct m_x check."),
        _validation_case("BC-EQ-119", "9.2.9 equation (119)", "implementation_self_check", beamcol.relative_eccentricity_y_eq119(10.0,3000.0,250000.0), 0.12, 1e-12, "dimensionless", "Direct m_y check."),
        _validation_case("BC-EQ-122", "9.2.10 equation (122)", "implementation_self_check", beamcol.box_delta_eq122(100000.0,2.0,3000.0,250.0), 1.0-0.1*100000.0*4.0/750000.0, 1e-12, "dimensionless", "Direct delta check."),
        _validation_case("BC-TBL-20", "Table 20", "implementation_self_check", beamcol.table_20_design_moment(100.0,60.0,70.0,2.0,2.0), 80.0, 1e-12, "N*mm", "Low-m and lambda<4 branch."),
        _validation_case("BC-TBL-21-ALPHA", "Table 21", "implementation_self_check", beamcol.table_21_alpha('1',2.0,None), 0.75, 1e-12, "dimensionless", "Type-1 alpha branch."),
        _validation_case("BC-TBL-21-BETA", "Table 21", "implementation_self_check", beamcol.table_21_beta('1',3.14,0.8,0.7,None), 1.0, 0.0, "dimensionless", "Boundary beta branch."),
        _validation_case("BC-EQ-D1", "Annex D equation (D.1)", "implementation_self_check", beamcol.annex_d_open_section_cmax_eq_d1({'delta':1.0,'B':1.0,'mu':4.0,'alpha':0.0,'eccentricity_ratio':0.0}), 1.0, 1e-12, "dimensionless", "Direct c_max check."),
        _validation_case("BC-EQ-D4", "Annex D equation (D.4)", "implementation_self_check", beamcol.annex_d_continuous_bracing_cmax_eq_d4(8e6,2e6,50,25,300,0,20), (1+4+20/9.87)/(1+4*((50**2+25**2)/300**2)), 1e-12, "dimensionless", "Direct continuous-bracing c_max check."),
    ])
    annex_d = json.loads((_DATA_DIR / "annex_d_tables_d2_to_d6.json").read_text(encoding="utf-8"))
    for lambda_key,row in annex_d["tables"]["D3"]["rows"].items():
        for m_key,raw in row.items():
            reference=float(raw)/float(annex_d["tables"]["D3"]["scale_divisor"])
            cases.append(_validation_case(f"BC-D3-{lambda_key}-{m_key}","Annex D Table D.3","standard_table_exact_node_cross_check",beamcol.annex_d3_table_coefficient(float(lambda_key),float(m_key)),reference,0.0,"dimensionless","Exact printed D.3 node."))
    for lambda_key,row in annex_d["tables"]["D4"]["rows"].items():
        for m_key,raw in row.items():
            reference=float(raw)/float(annex_d["tables"]["D4"]["scale_divisor"])
            cases.append(_validation_case(f"BC-D4-{lambda_key}-{m_key}","Annex D Table D.4","standard_table_exact_node_cross_check",beamcol.annex_d4_table_coefficient(float(lambda_key),float(m_key)),reference,0.0,"dimensionless","Exact printed D.4 node."))
    for delta_key,lambda_rows in annex_d["tables"]["D5"]["rows"].items():
        for lambda_key,row in lambda_rows.items():
            for m_key,reference in row.items():
                cases.append(_validation_case(f"BC-D5-{delta_key}-{lambda_key}-{m_key}","Annex D Table D.5","standard_table_exact_node_cross_check",beamcol.annex_d5_effective_relative_eccentricity(float(delta_key),float(lambda_key),float(m_key)),float(reference),0.0,"dimensionless","Exact printed D.5 node."))

    # v0.11 Sections 9.3-9.4 checks.
    cases.extend([
        _validation_case("V11-EQ-123", "9.3.2 equation (123)", "implementation_self_check", combined_local.built_up_relative_eccentricity_eq123(80.0,12000.0,300.0,144000000.0), 2.0, 1e-12, "dimensionless", "Direct e*A*a/I check."),
        _validation_case("V11-EQ-124", "9.3.3 equation (124)", "implementation_self_check", combined_local.biaxial_branch_additional_force_eq124(120e6,600.0,60e6,500.0), 160000.0, 1e-9, "N", "Direct biaxial branch-force check."),
        _validation_case("V11-EQ-125", "9.4.2 equation (125)", "implementation_self_check", combined_local.web_limit_eq125(1.5), 1.6375, 1e-12, "dimensionless", "Direct polynomial check."),
        _validation_case("V11-EQ-126", "9.4.2 equation (126)", "implementation_self_check", combined_local.web_limit_eq126(4.0), 2.6, 1e-12, "dimensionless", "Direct capped linear check."),
        _validation_case("V11-EQ-127", "9.4.2 equation (127)", "implementation_self_check", combined_local.web_limit_eq127(1.2,0.2,15.5,355.0,1.0,180.0), min(1.42*math.sqrt(15.5*355.0/(180.0*(2.0-1.2+math.sqrt(1.2**2+4*0.2**2)))),0.7+2.4*1.2), 1e-12, "dimensionless", "Direct square-root and cap check."),
        _validation_case("V11-EQ-128", "9.4.2 equation (128)", "implementation_self_check", combined_local.web_limit_eq128(3.0,1.2), 2.25, 1e-12, "dimensionless", "Direct multiplier and cap check."),
        _validation_case("V11-EQ-129", "9.4.2 equation (129)", "implementation_self_check", combined_local.web_limit_eq129(0.1,700.0,600.0), (0.4+0.07*0.8)*(1+0.25*math.sqrt(2-700/600)), 1e-12, "dimensionless", "Lower slenderness clamp check."),
        _validation_case("V11-EQ-130", "9.4.2 equation (130)", "implementation_self_check", combined_local.web_limit_eq130(12000.0,355.0,1.0,1000000.0), min(2*math.sqrt(12000*355/1000000),5.5), 1e-12, "dimensionless", "Direct area-force check."),
        _validation_case("V11-EQ-131", "9.4.3 equation (131)", "implementation_self_check", combined_local.web_limit_adjustment_eq131(2.0,3.0,0.9), 2.5, 1e-12, "dimensionless", "Mid-range interpolation check."),
        _validation_case("V11-EQ-132", "9.4.7 equation (132)", "implementation_self_check", combined_local.flange_limit_eq132(0.65,2.0,5.0), 0.505, 1e-12, "dimensionless", "Direct type-1 flange check."),
        _validation_case("V11-EQ-133", "9.4.7 equation (133)", "implementation_self_check", combined_local.flange_limit_eq133(0.65,2.0,5.0), 0.255, 1e-12, "dimensionless", "Direct type-2 flange check."),
        _validation_case("V11-EQ-134", "9.4.7 equation (134)", "implementation_self_check", combined_local.flange_limit_eq134(0.1), 0.44, 1e-12, "dimensionless", "Lower slenderness clamp check."),
        _validation_case("V11-EQ-135", "9.4.7 equation (135)", "implementation_self_check", combined_local.flange_limit_eq135(5.0), 0.76, 1e-12, "dimensionless", "Upper slenderness clamp check."),
        _validation_case("V11-TBL-22", "Table 22", "implementation_self_check", float(len(combined_local.table_22_catalog()["section_types"])), 5.0, 0.0, "section types", "Catalogue completeness check."),
        _validation_case("V11-TBL-23", "Table 23", "implementation_self_check", float(len(combined_local.table_23_catalog()["section_types"])), 4.0, 0.0, "section types", "Catalogue completeness check."),
        _validation_case("V11-PROC-9.3.7", "9.3.7 governing shear", "implementation_self_check", combined_local.connector_design_shear_clause_9_3_7(80.0,60.0)["governing_shear_force_n"], 80.0, 0.0, "N", "Maximum rule check."),
        _validation_case("V11-PROC-9.4.8", "9.4.8 edge return", "implementation_self_check", combined_local.edge_return_flange_limit_clause_9_4_8(0.6,True), 0.9, 1e-12, "dimensionless", "Multiplier check."),
    ])

    # v0.12 Section 10 checks.
    cases.extend([
        _validation_case("V12-EQ-136", "10.1.2 equation (136)", "implementation_self_check", eff.truss_chord_effective_length_in_plane_eq136(1000.0,0.5), (0.17*0.5**3+0.83)*1000.0, 1e-12, "length", "Direct equation check."),
        _validation_case("V12-EQ-137", "10.1.2 equation (137)", "implementation_self_check", eff.truss_chord_effective_length_out_of_plane_eq137(2000.0,3,1.0), (0.75+0.25*(1/2)**3)*2000.0, 1e-12, "length", "Direct equation check."),
        _validation_case("V12-EQ-138", "10.1.2 equation (138)", "implementation_self_check", eff.built_up_column_branch_effective_length_in_plane_eq138(1000.0,0.5), max(math.sqrt(0.36+0.59*0.5**3)*1000,610), 1e-12, "length", "Direct equation check."),
        _validation_case("V12-EQ-139", "10.1.2 equation (139)", "implementation_self_check", eff.built_up_column_branch_effective_length_out_of_plane_eq139(2000.0,3,1.0), max((0.6*math.sqrt(3)+0.54)*2000/3,1020), 1e-12, "length", "Direct equation check."),
        _validation_case("V12-EQ-140", "10.3.1 equation (140)", "implementation_self_check", eff.column_effective_length_eq140(3000,0.7),2100,0.0,"length","Direct equation check."),
        _validation_case("V12-EQ-141", "10.3.4 equation (141)", "implementation_self_check", eff.sway_frame_mu_eq141(1),2*math.sqrt(1.38),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-142", "10.3.4 equation (142)", "implementation_self_check", eff.sway_frame_mu_eq142(1),math.sqrt(1.56/1.14),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-143", "10.3.4 equation (143)", "implementation_self_check", eff.sway_frame_mu_eq143(1,0.2),(1.68*math.sqrt(.42))/math.sqrt(.68*1*1.9*.28+.02),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-144", "10.3.4 equation (144)", "implementation_self_check", eff.sway_frame_mu_eq144(1,1),(1.63*math.sqrt(1.28))/math.sqrt(1.9+.1),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-145", "10.3.4 equation (145)", "implementation_self_check", eff.nonsway_frame_mu_eq145(1,1),math.sqrt(2.10/3.57),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-146", "10.3.6 equation (146)", "implementation_self_check", eff.nonuniform_sway_frame_effective_length_eq146(2,100,1000,500,400),2*math.sqrt(.5),1e-12,"dimensionless","Direct equation check."),
        _validation_case("V12-EQ-147", "10.3.8 equation (147)", "implementation_self_check", eff.frame_deformation_reduction_factor_eq147(0,1000,1000,100,100,100)["psi"],0.35,1e-12,"dimensionless","At beta=0 and omega=0, psi=1-0.65."),
        _validation_case("V12-TBL-24", "Table 24", "standard_table_exact_node_cross_check", eff.table_24_effective_length("in_plane_general","other_web",1000),800,0.0,"length","Exact factor check."),
        _validation_case("V12-TBL-25", "Table 25", "standard_table_exact_node_cross_check", eff.table_25_cross_lattice_effective_length("both_members_continuous","inactive",500,1000),700,0.0,"length","Exact factor check."),
        _validation_case("V12-TBL-26", "Table 26", "standard_table_exact_node_cross_check", eff.table_26_structural_member_effective_length("single_angle_one_bolt",1000,100),950,0.0,"length","Exact factor check."),
        _validation_case("V12-TBL-27", "Table 27", "standard_table_exact_node_cross_check", eff.table_27_spatial_member_properties("chord_15e","compression",{"lm":1000})["effective_length"],640,0.0,"length","Exact factor check."),
        _validation_case("V12-TBL-28", "Table 28", "standard_table_exact_node_cross_check", eff.table_28_intersection_conditional_length("both_continuous","inactive",1000,800,2),1300,0.0,"length","Exact factor check."),
        _validation_case("V12-TBL-29", "Table 29", "standard_table_exact_node_cross_check", eff.table_29_diagonal_length_factor("one_bolt_without_gusset",2,100),0.928,1e-12,"dimensionless","Formula-band check."),
        _validation_case("V12-TBL-30", "Table 30", "standard_table_exact_node_cross_check", eff.table_30_effective_length_factor("scheme_7"),0.725,0.0,"dimensionless","Exact diagram value."),
        _validation_case("V12-TBL-31", "Table 31 special case", "standard_table_exact_node_cross_check", eff.table_31_special_case_mu("nonsway_p0",1),math.sqrt(1.46/1.93),1e-12,"dimensionless","Exact special-case formula."),
        _validation_case("V12-TBL-32", "Table 32", "standard_table_exact_node_cross_check", eff.table_32_compressed_limiting_slenderness("2b",0.5),200,0.0,"dimensionless","Exact row formula."),
        _validation_case("V12-TBL-33", "Table 33", "standard_table_exact_node_cross_check", eff.table_33_tension_limiting_slenderness("4","crane_or_rail"),200,0.0,"dimensionless","Exact table value."),
    ])

    # v0.13 Section 11 sheet-structure strength and stability checks.
    cases.extend([
        _validation_case("V13-EQ-148", "11.1.1 equation (148)", "implementation_self_check", sheet.membrane_strength_utilization_eq148(100.0,40.0,20.0,355.0,1.0), math.sqrt(100.0**2-100.0*40.0+40.0**2+3.0*20.0**2)/355.0, 1e-12, "dimensionless", "Signed membrane equivalent-stress check."),
        _validation_case("V13-EQ-149", "11.1.2 equation (149)", "implementation_self_check", sheet.meridional_stress_eq149(2.0*math.pi*1000.0*10.0,1000.0,10.0,0.0), 1.0, 1e-12, "N/mm2", "Direct meridional stress check."),
        _validation_case("V13-EQ-150", "11.1.2 equation (150)", "implementation_self_check", sheet.circumferential_stress_eq150(2.0,10.0,50.0,1000.0,500.0), 75.0, 1e-12, "N/mm2", "Direct circumferential stress check."),
        _validation_case("V13-EQ-151-MER", "11.1.2 equation (151)", "implementation_self_check", sheet.cylindrical_internal_pressure_stresses_eq151(1.0,1000.0,10.0)[0], 50.0, 1e-12, "N/mm2", "Cylinder meridional stress."),
        _validation_case("V13-EQ-151-HOOP", "11.1.2 equation (151)", "implementation_self_check", sheet.cylindrical_internal_pressure_stresses_eq151(1.0,1000.0,10.0)[1], 100.0, 1e-12, "N/mm2", "Cylinder hoop stress."),
        _validation_case("V13-EQ-152", "11.1.2 equation (152)", "implementation_self_check", sheet.spherical_internal_pressure_stresses_eq152(1.0,1000.0,10.0)[0], 50.0, 1e-12, "N/mm2", "Sphere membrane stress."),
        _validation_case("V13-EQ-153-MER", "11.1.2 equation (153)", "implementation_self_check", sheet.conical_internal_pressure_stresses_eq153(1.0,1000.0,10.0,30.0)[0], 50.0/math.cos(math.radians(30.0)), 1e-12, "N/mm2", "Cone meridional stress."),
        _validation_case("V13-EQ-153-HOOP", "11.1.2 equation (153)", "implementation_self_check", sheet.conical_internal_pressure_stresses_eq153(1.0,1000.0,10.0,30.0)[1], 100.0/math.cos(math.radians(30.0)), 1e-12, "N/mm2", "Cone hoop stress."),
        _validation_case("V13-EQ-154", "11.2.1 equation (154)", "implementation_self_check", sheet.cylindrical_axial_stability_utilization_eq154(100.0,200.0,0.8), 0.625, 1e-12, "dimensionless", "Direct axial shell stability check."),
        _validation_case("V13-EQ-155", "11.2.1 equation (155)", "implementation_self_check", sheet.cylindrical_psi_eq155(200.0,355.0,206000.0), 0.97-(0.00025+0.95*355.0/206000.0)*200.0, 1e-12, "dimensionless", "Direct psi check."),
        _validation_case("V13-EQ-156", "11.2.2 equation (156)", "implementation_self_check", sheet.tube_local_stability_utilization_eq156(100000.0,1.0,2000.0,0.2,355.0,100.0,1000.0,20.0,206000.0), 100000.0*2.0/(2000.0*((100.0/8.0*(9.0-(1.0-0.2)/(1.0+0.2))+1.2*355.0*math.pi**2)-math.sqrt((100.0/8.0*(9.0-(1.0-0.2)/(1.0+0.2))+1.2*355.0*math.pi**2)**2-4.0*355.0*(100.0/8.0*(9.0-(1.0-0.2)/(1.0+0.2)))*math.pi**2))), 1e-12, "dimensionless", "Direct tube local-stability check."),
        _validation_case("V13-EQ-157", "11.2.3 equation (157)", "implementation_self_check", sheet.cylindrical_panel_limit_eq157(206000.0,100.0), 1.9*math.sqrt(206000.0/100.0), 1e-12, "dimensionless", "Elastic panel limit."),
        _validation_case("V13-EQ-158", "11.2.3 equation (158)", "implementation_self_check", sheet.cylindrical_panel_limit_eq158(355.0,206000.0), 37.0/math.sqrt(1.0+500.0*355.0/206000.0), 1e-12, "dimensionless", "Yield panel limit."),
        _validation_case("V13-EQ-159", "11.2.4 equation (159)", "implementation_self_check", sheet.cylindrical_external_pressure_utilization_eq159(20.0,50.0,0.8), 0.5, 1e-12, "dimensionless", "External-pressure utilization."),
        _validation_case("V13-EQ-160", "11.2.4 equation (160)", "implementation_self_check", sheet.cylindrical_external_pressure_critical_stress_eq160(206000.0,1000.0,5000.0,10.0), 0.55*206000.0*(1000.0/5000.0)*(10.0/1000.0)**1.5, 1e-12, "N/mm2", "Short-cylinder pressure critical stress."),
        _validation_case("V13-EQ-161", "11.2.4 equation (161)", "implementation_self_check", sheet.cylindrical_external_pressure_critical_stress_eq161(206000.0,1000.0,10.0), 0.17*206000.0*(10.0/1000.0)**2, 1e-12, "N/mm2", "Long-cylinder pressure critical stress."),
        _validation_case("V13-EQ-162", "11.2.5 equation (162)", "implementation_self_check", sheet.cylindrical_combined_stability_utilization_eq162(20.0,100.0,30.0,150.0,0.8), 0.5, 1e-12, "dimensionless", "Combined cylindrical shell check."),
        _validation_case("V13-EQ-163", "11.2.6 equation (163)", "implementation_self_check", sheet.conical_axial_stability_utilization_eq163(100000.0,200000.0,0.8), 0.625, 1e-12, "dimensionless", "Cone axial utilization."),
        _validation_case("V13-EQ-164", "11.2.6 equation (164)", "implementation_self_check", sheet.conical_critical_force_eq164(10.0,100.0,1000.0,30.0), 6.28*10.0*100.0*1000.0*math.cos(math.radians(30.0))**2, 1e-9, "N", "Literal 6.28 coefficient retained from the standard."),
        _validation_case("V13-EQ-165", "11.2.6 equation (165)", "implementation_self_check", sheet.conical_equivalent_radius_eq165(500.0,1000.0,30.0), (0.9*1000.0+0.1*500.0)/math.cos(math.radians(30.0)), 1e-12, "mm", "Equivalent cone radius."),
        _validation_case("V13-EQ-166", "11.2.7 equation (166)", "implementation_self_check", sheet.conical_external_pressure_utilization_eq166(40.0,100.0,0.8), 0.5, 1e-12, "dimensionless", "Cone external-pressure utilization."),
        _validation_case("V13-EQ-167", "11.2.7 equation (167)", "implementation_self_check", sheet.conical_external_pressure_critical_stress_eq167(206000.0,1000.0,2000.0,10.0), 0.55*206000.0*(1000.0/2000.0)*(10.0/1000.0)**1.5, 1e-12, "N/mm2", "Cone pressure critical stress."),
        _validation_case("V13-EQ-168", "11.2.8 equation (168)", "implementation_self_check", sheet.conical_combined_stability_utilization_eq168(20.0,100.0,30.0,150.0,0.8), 0.5, 1e-12, "dimensionless", "Combined cone stability check."),
        _validation_case("V13-EQ-169", "11.2.9 equation (169)", "implementation_self_check", sheet.spherical_external_pressure_utilization_eq169(0.1,1000.0,10.0,20.0,1.0), 0.25, 1e-12, "dimensionless", "Spherical shell external-pressure check."),
        _validation_case("V13-PROC-11.1.1", "11.1.1 principal stresses", "implementation_self_check", sheet.principal_stresses_2d(100.0,40.0,20.0)[0], 106.05551275464, 1e-10, "N/mm2", "Principal stress transformation."),
        _validation_case("V13-PROC-11.2.1", "11.2.1 critical stress", "implementation_self_check", sheet.cylindrical_axial_critical_stress(3000.0,10.0,355.0,206000.0)["radius_to_thickness_ratio"], 300.0, 0.0, "dimensionless", "Exact Table 34 node route."),
        _validation_case("V13-PROC-11.2.4", "11.2.4 ring force", "implementation_self_check", sheet.ring_stiffener_requirements_clause_11_2_4(0.1,1000.0,500.0,10.0,206000.0,355.0)["ring_compression_force_n"], 50000.0, 1e-9, "N", "Ring force p*r*s."),
        _validation_case("V13-PROC-11.2.9", "11.2.9 spherical critical stress", "implementation_self_check", sheet.spherical_external_pressure_critical_stress_clause_11_2_9(206000.0,1000.0,10.0,355.0), min(0.1*206000.0*10.0/1000.0,355.0), 1e-12, "N/mm2", "Spherical critical stress cap."),
    ])
    table_34 = sheet.table_34_catalog()["values"]
    for ratio, coefficient in table_34.items():
        cases.append(_validation_case(f"V13-T34-{ratio}", "Table 34", "standard_table_exact_node_cross_check", sheet.table_34_c_coefficient(float(ratio)), float(coefficient), 0.0, "dimensionless", "Exact printed Table 34 node."))

    # v0.14 Section 12 fatigue design.
    cases.extend([
        _validation_case("V14-EQ-170", "12.1.2 equation (170)", "implementation_self_check", fatigue.fatigue_utilization_eq170(50.0,1.314,75.0,2.5/1.9), 50.0/(1.314*75.0*(2.5/1.9)), 1e-12, "dimensionless", "Fatigue utilization."),
        _validation_case("V14-EQ-171", "12.1.2 equation (171)", "implementation_self_check", fatigue.cycle_factor_group_1_2_eq171(1_000_000.0), 0.064-0.5+1.75, 1e-12, "dimensionless", "Cycle factor for groups 1-2."),
        _validation_case("V14-EQ-172", "12.1.2 equation (172)", "implementation_self_check", fatigue.cycle_factor_group_3_8_eq172(1_000_000.0), 0.07-0.64+2.2, 1e-12, "dimensionless", "Cycle factor for groups 3-8."),
        _validation_case("V14-EQ-173", "12.2 equation (173)", "implementation_self_check", fatigue.crane_runway_web_fatigue_utilization_eq173(40.0,20.0,10.0,5.0,75.0), (0.5*math.sqrt(40.0**2+0.36*20.0**2)+0.4*10.0+0.5*5.0)/75.0, 1e-12, "dimensionless", "Crane-runway web fatigue utilization."),
        _validation_case("V14-T36-TENSION", "Table 36", "standard_table_analytic_cross_check", fatigue.fatigue_asymmetry_factor_table36(50.0,-20.0), 2.5/(1.5-(-0.4)), 1e-12, "dimensionless", "Tension branch with stress reversal."),
        _validation_case("V14-T36-COMPRESSION", "Table 36", "standard_table_analytic_cross_check", fatigue.fatigue_asymmetry_factor_table36(-50.0,-20.0), 2.0/(1.0-0.4), 1e-12, "dimensionless", "Compression branch."),
        _validation_case("V14-PROC-ALPHA-CAP", "12.1.2", "implementation_self_check", fatigue.fatigue_cycle_factor_alpha(3_900_000.0,4), 0.77, 0.0, "dimensionless", "Terminal alpha at n>=3.9e6."),
        _validation_case("V14-PROC-CRANE-ALPHA", "12.2", "implementation_self_check", fatigue.crane_runway_cycle_factor_clause_12_2("8K",False), 0.77, 0.0, "dimensionless", "8K crane-runway cycle factor."),
    ])
    table35=fatigue.table_35_catalog()
    for binrow in table35["steel_bins"]:
        run=binrow["upper_inclusive"]
        for group in (1,2):
            cases.append(_validation_case(f"V14-T35-{binrow['id']}-G{group}", "Table 35", "standard_table_exact_node_cross_check", fatigue.fatigue_design_resistance_table35(group,run), float(binrow[f"group_{group}"]), 0.0, "N/mm2", "Exact Table 35 bin boundary."))
    for group,value in table35["all_steel_values"].items():
        cases.append(_validation_case(f"V14-T35-G{group}", "Table 35", "standard_table_exact_value_cross_check", fatigue.fatigue_design_resistance_table35(int(group),440.0), float(value), 0.0, "N/mm2", "Table 35 all-steel group value."))
    for entry in fatigue.annex_k_catalog()["entries"]:
        cases.append(_validation_case(f"V14-K1-{entry['case_id']}", "Annex K Table K.1", "standard_table_case_cross_check", float(fatigue.annex_k_group(entry["case_id"])), float(entry["group"]), 0.0, "group", "Explicit audited Annex K case lookup."))

    cases.extend([
        _validation_case("V15-EQ174", "13.5 equation (174)", "implementation_self_check", welded.lamellar_tearing_risk_sum_eq174(3,5,2,3,-4), 9.0, 0.0, "percent", "Signed sum of five risk factors."),
        _validation_case("V15-EQ175", "14.1.14 equation (175)", "implementation_self_check", welded.butt_weld_axial_utilization_eq175(100000,10,200,250,1), 0.2, 1e-12, "dimensionless", "Butt-weld axial utilization."),
        _validation_case("V15-EQ176", "14.1.16 equation (176)", "implementation_self_check", welded.fillet_weld_axial_metal_utilization_eq176(100000,.7,10,200,200,1), 100000/(.7*10*200*200), 1e-12, "dimensionless", "Weld-metal plane."),
        _validation_case("V15-EQ177", "14.1.16 equation (177)", "implementation_self_check", welded.fillet_weld_axial_fusion_utilization_eq177(100000,1,10,200,150,1), 100000/(10*200*150), 1e-12, "dimensionless", "Fusion-boundary plane."),
        _validation_case("V15-EQ178", "14.1.17 equation (178)", "implementation_self_check", welded.fillet_weld_out_of_plane_moment_metal_utilization_eq178(1e6,1e4,200,1), .5, 1e-12, "dimensionless", "Out-of-plane moment weld-metal plane."),
        _validation_case("V15-EQ179", "14.1.17 equation (179)", "implementation_self_check", welded.fillet_weld_out_of_plane_moment_fusion_utilization_eq179(1e6,1e4,100,1), 1.0, 1e-12, "dimensionless", "Out-of-plane moment fusion plane."),
        _validation_case("V15-EQ180", "14.1.18 equation (180)", "implementation_self_check", welded.fillet_weld_in_plane_moment_metal_utilization_eq180(1e5,10,0,1e4,1e4,200,1), .25, 1e-12, "dimensionless", "In-plane moment weld-metal plane."),
        _validation_case("V15-EQ181", "14.1.18 equation (181)", "implementation_self_check", welded.fillet_weld_in_plane_moment_fusion_utilization_eq181(1e5,10,0,1e4,1e4,200,1), .25, 1e-12, "dimensionless", "In-plane moment fusion plane."),
        _validation_case("V15-EQ182", "14.1.19 equation (182)", "implementation_self_check", welded.combined_fillet_weld_utilizations_eq182(50,40,200,150,1)["governing_utilization"], 40/150, 1e-12, "dimensionless", "Governing two-plane utilization."),
        _validation_case("V15-EQ183", "14.1.19 equation (183)", "implementation_self_check", welded.resultant_shear_stress_eq183(10,20,30,-5), math.sqrt(30**2+25**2), 1e-12, "N/mm2", "Resultant shear with algebraic component sums."),
        _validation_case("V15-EQ184", "14.1.20 equation (184)", "implementation_self_check", welded.spot_weld_shear_capacity_eq184(10,400), 11200.0, 1e-9, "N", "Arc spot-weld shear capacity."),
        _validation_case("V15-EQ185", "14.1.20 equation (185)", "implementation_self_check", welded.spot_weld_tearout_capacity_eq185(1.1,10,2,400), 8800.0, 1e-9, "N", "Arc spot-weld tear-out capacity."),
        _validation_case("V15-T37", "Table 37", "standard_table_exact_value_cross_check", welded.table_37_connection_form_factor("corner_full_penetration"), 8.0, 0.0, "percent", "Exact Table 37 geometry factor."),
        _validation_case("V15-T38", "Table 38", "standard_table_exact_value_cross_check", welded.minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner",12,8,355)["minimum_weld_leg_mm"], 6.0, 0.0, "mm", "Exact Table 38 lookup."),
        _validation_case("V15-T39-BF", "Table 39", "standard_table_exact_value_cross_check", welded.table_39_fillet_weld_coefficients("automatic_d3_5","lower",10)["beta_f"], .9, 0.0, "dimensionless", "Exact beta_f lookup."),
        _validation_case("V15-T39-BZ", "Table 39", "standard_table_exact_value_cross_check", welded.table_39_fillet_weld_coefficients("automatic_d3_5","lower",10)["beta_z"], 1.05, 0.0, "dimensionless", "Exact beta_z lookup."),
    ])

    cases.extend([
        _validation_case("V16-EQ186", "14.2.9 equation (186)", "implementation_self_check", bolted.bolt_shear_capacity_eq186(240,245,2,0.9,1), 105840.0, 1e-9, "N", "One-bolt shear capacity."),
        _validation_case("V16-EQ187", "14.2.9 equation (187)", "implementation_self_check", bolted.bolt_bearing_capacity_eq187(450,20,24,0.9,1), 194400.0, 1e-9, "N", "One-bolt bearing capacity."),
        _validation_case("V16-EQ188", "14.2.9 equation (188)", "implementation_self_check", bolted.bolt_tension_capacity_eq188(360,190,1), 68400.0, 1e-9, "N", "One-bolt tension capacity."),
        _validation_case("V16-EQ189", "14.2.10 equation (189)", "implementation_self_check", float(bolted.required_bolt_count_eq189(300000,105840,194400,68400)["required_bolts"]), 3.0, 0.0, "bolts", "Centroidal bolt count."),
        _validation_case("V16-EQ190", "14.2.13 equation (190)", "implementation_self_check", bolted.bolt_shear_tension_interaction_eq190(40000,30000,105840,68400), math.sqrt((40000/105840)**2+(30000/68400)**2), 1e-12, "dimensionless", "Shear-tension interaction."),
        _validation_case("V16-EQ191", "14.3.3 equation (191)", "implementation_self_check", bolted.friction_plane_capacity_eq191(360,190,.58,1.35), 360*190*.58/1.35, 1e-9, "N", "Friction-plane capacity."),
        _validation_case("V16-EQ192", "14.3.4 equation (192)", "implementation_self_check", float(bolted.required_friction_bolt_count_eq192(200000,360*190*.58/1.35,2,1)["required_bolts"]), 5.0, 0.0, "bolts", "Implicit friction bolt count."),
        _validation_case("V16-T40", "Table 40", "standard_table_exact_value_cross_check", bolted.table_40_hole_diameter(20,"B",clearance_mm=2), 22.0, 0.0, "mm", "Class B hole diameter."),
        _validation_case("V16-T41", "Table 41", "standard_table_exact_value_cross_check", bolted.table_41_connection_factor("B",multi_bolt=True,bearing_geometry="a_1_5d_s_2d"), .72, 1e-12, "dimensionless", "Simultaneous Table 41 factors."),
        _validation_case("V16-T42-MU", "Table 42", "standard_table_exact_value_cross_check", bolted.table_42_friction_parameters("shot_blast_no_preservation","torque","dynamic",3)["friction_coefficient"], .58, 0.0, "dimensionless", "Table 42 friction coefficient."),
        _validation_case("V16-T42-GH", "Table 42", "standard_table_exact_value_cross_check", bolted.table_42_friction_parameters("steel_brushed_no_preservation","nut_rotation","static",2)["gamma_h"], 1.17*.9, 1e-12, "dimensionless", "Table 42 nut-rotation multiplier."),
        _validation_case("V16-PROC-LONG", "14.2.10", "implementation_self_check", bolted.long_joint_reduction_factor_14_2_10(440,22), 1-.005*(20-16), 1e-12, "dimensionless", "Long-joint factor."),
        _validation_case("V16-PROC-AREA", "14.3.11", "implementation_self_check", bolted.friction_connection_effective_area_14_3_11(1000,800,"static")["selected_area_mm2"], 944.0, 1e-12, "mm2", "Static effective area below 0.85A."),
    ])


    cases.extend([
        _validation_case("V17-PROC-T", "14.4.1 Table 43 definitions", "implementation_self_check", flange.flange_shear_flow_t_n_mm(240000,1.2e6,8e8), 360.0, 1e-12, "N/mm", "Flange shear flow T=QS/I."),
        _validation_case("V17-PROC-V", "14.4.1 Table 43 definitions", "implementation_self_check", flange.local_load_line_pressure_v_n_mm(1.2,1.1,100000,250), 528.0, 1e-12, "N/mm", "Concentrated-load pressure per unit length."),
        _validation_case("V17-EQ193", "14.4.1 equation (193)", "implementation_self_check", flange.stationary_weld_metal_utilization_eq193(360,2,.8,8,240,1), 360/(2*.8*8*240), 1e-12, "dimensionless", "Stationary welded flange connection, weld-metal plane."),
        _validation_case("V17-EQ194", "14.4.1 equation (194)", "implementation_self_check", flange.stationary_fusion_boundary_utilization_eq194(360,2,1,8,215,1), 360/(2*1*8*215), 1e-12, "dimensionless", "Stationary welded flange connection, fusion-boundary plane."),
        _validation_case("V17-EQ195", "14.4.1 equation (195)", "implementation_self_check", flange.stationary_friction_utilization_eq195(360,80,25000,2,1), 360*80/(25000*2), 1e-12, "dimensionless", "Stationary friction flange connection."),
        _validation_case("V17-EQ196", "14.4.1 equation (196)", "implementation_self_check", flange.moving_weld_metal_utilization_eq196(360,528,.8,8,240,1), math.hypot(360,528)/(2*.8*8*240), 1e-12, "dimensionless", "Moving-load welded flange connection, weld-metal plane."),
        _validation_case("V17-EQ197", "14.4.1 equation (197)", "implementation_self_check", flange.moving_fusion_boundary_utilization_eq197(360,528,1,8,215,1), math.hypot(360,528)/(2*1*8*215), 1e-12, "dimensionless", "Moving-load welded flange connection, fusion-boundary plane."),
        _validation_case("V17-EQ198", "14.4.1 equation (198)", "implementation_self_check", flange.moving_friction_utilization_eq198(360,528,.4,80,25000,2,1), 80*math.hypot(360,.4*528)/(25000*2), 1e-12, "dimensionless", "Moving-load friction flange connection."),
        _validation_case("V17-T43-ROWS", "Table 43", "standard_table_structure_cross_check", float(len(flange.table_43_catalog()["rows"])), 4.0, 0.0, "rows", "Four printed load/connection rows."),
        _validation_case("V17-PROC-ALPHA", "Table 43 alpha definition", "standard_table_exact_value_cross_check", flange.table_43_alpha("upper",web_edge_planed_to_loaded_upper_flange=True), .4, 0.0, "dimensionless", "Upper flange with planed web edge."),
        _validation_case("V17-PROC-MULTILAYER", "14.4.2", "implementation_self_check", flange.multilayer_flange_sheet_attachment_force_14_4_2(500000,"beyond_theoretical_cutoff")["required_attachment_force_n"], 250000.0, 0.0, "N", "Half sheet force beyond theoretical cutoff."),
    ])


    cases.extend([
        _validation_case("V18-SP16-TBL-44", "15.1 Table 44", "standard_table_exact_value_cross_check", detail.table_44_maximum_spacing_m("heated_building","between_joints_along_block",-45.0), 230.0, 0.0, "m", "Exact warm-column Table 44 value at the -45 degree boundary."),
        _validation_case("V18-SP16-TBL-44-COLD", "15.1 Table 44", "standard_table_exact_value_cross_check", detail.table_44_maximum_spacing_m("open_trestle","joint_or_end_to_nearest_vertical_bracing_axis",-50.0), 40.0, 0.0, "m", "Exact cold-column Table 44 value."),
        _validation_case("V18-SP16-PROC-15.1-SPACING-ASSESSMENT", "15.1", "implementation_self_check", float(detail.temperature_joint_spacing_assessment_15_1(242.0,"heated_building","between_joints_along_block",-30.0,False)["climatic_temperature_effects_inelastic_deformations_and_joint_flexibility_analysis_required"]), 1.0, 0.0, "boolean", "More-than-five-percent enhanced-analysis trigger."),
        _validation_case("V18-SP16-PROC-15.1-PAIRED-BRACING", "15.1 Table 44 note", "standard_table_exact_value_cross_check", detail.paired_vertical_bracing_max_spacing_m_15_1("building",-50.0), 40.0, 0.0, "m", "Smaller building range value below -45 degrees C."),
        _validation_case("V18-SP16-PROC-15.12.1-FRICTION-FLAT", "15.12.1", "standard_clause_exact_value_cross_check", detail.support_bearing_friction_coefficient_15_12_1("flat_sliding"), 0.3, 0.0, "dimensionless", "Flat movable bearing friction coefficient."),
        _validation_case("V18-SP16-PROC-15.12.1-FRICTION-ROLLER", "15.12.1", "standard_clause_exact_value_cross_check", detail.support_bearing_friction_coefficient_15_12_1("roller"), 0.03, 0.0, "dimensionless", "Roller movable bearing friction coefficient."),
        _validation_case("V18-SP16-EQ-199", "15.12.2 equation (199)", "implementation_self_check", detail.cylindrical_hinge_local_bearing_utilization_eq199(1200000.0,150.0,300.0,242.85714285714286,1.0), 1200000.0/(1.25*150.0*300.0*242.85714285714286), 1e-12, "dimensionless", "Cylindrical-hinge local-bearing utilization."),
        _validation_case("V18-SP16-PROC-15.12.2-ANGLE-APPLICABILITY", "15.12.2", "implementation_self_check", float(detail.cylindrical_hinge_bearing_check_15_12_2(1200000.0,90.0,150.0,300.0,242.85714285714286,1.0)["equation_199_applicable"]), 1.0, 0.0, "boolean", "Equation (199) is applicable at the printed 90 degree boundary."),
        _validation_case("V18-SP16-EQ-200", "15.12.3 equation (200)", "implementation_self_check", detail.roller_diametral_compression_utilization_eq200(1200000.0,4,120.0,300.0,12.142857142857142,1.0), 1200000.0/(4.0*120.0*300.0*12.142857142857142), 1e-12, "dimensionless", "Roller diametral-compression utilization."),
        _validation_case("V18-SP16-PROC-15-CLASSIFICATION", "Section 15", "catalogue_structure_cross_check", float(len(detail.section_15_requirement_catalog()["entries"])), 80.0, 0.0, "clauses", "All Section 15 register entries are classified by execution route."),
    ])


    # v0.19 Section 16 overhead-line, switchyard, and contact-network supports.
    _aux19 = line_supports.guyed_support_second_order_auxiliaries(12000.0, 8000.0, 120.0, 1_000_000.0, 206000.0)
    _mu19 = 1.25 * (1.0 / 3.0) ** 2 - 2.75 * (1.0 / 3.0) + 3.5
    _delta19 = 1.0 - 0.1 * 1_000_000.0 * 12000.0**2 / (206000.0 * 80_000_000.0)
    _eq20619 = 80_000_000.0 + 1.2 * 1_000_000.0 / _delta19 * (12.0 + 15.6)
    _eq20719 = 45_000.0 + 3.14 * 1.2 * 1_000_000.0 * (12.0 + 15.6) / (_delta19 * 12000.0)
    _eq20919 = 1.0 + (0.6 - 0.55 + 2.0 * (0.2 - 0.05 * 2.0)) * 0.3
    _eq21019 = 0.95 + 0.1 * 0.5 + (0.34 - 0.62 * 0.5 + 2.0 * (0.2 - 0.05 * 2.0)) * 0.2
    _eq21119 = 1.18 - 0.36 * 0.6 + (1.8 * 0.6 - 0.86) * 0.3
    _eq21219 = 1.0 - 0.04 * 0.5 + (0.36 - 0.41 * 0.5) * 0.2
    _lam19 = 50.0 * math.sqrt(345.0 / 206000.0)
    _lam_used19 = min(_lam19, 2.4)
    _beta19 = 0.58 + 1.81 * _lam_used19**2
    _psi19 = 1.0 + 0.033 * _lam_used19 * (1.0 - (-20.0) / 100.0)
    _sigma_cr19 = min((_beta19 - math.sqrt(_beta19**2 - 3.8 * _lam_used19**2)) * _psi19 * 345.0, 345.0)
    _detail19 = line_supports.section_16_detailing_checks(
        traverse_member="chord_primary", panel_length_mm=3000.0, alternate_chord_length_mm=2500.0,
        actual_first_lower_brace_slenderness=140.0, support_system="free_standing", actual_diaphragm_spacing_m=20.0,
        diaphragm_at_concentrated_loads=True, diaphragm_at_chord_breaks=True, edge_distance_mm=40.0,
        bolt_diameter_mm=20.0, permanently_tensioned_single_bolt_element=True, braces_on_both_sides_of_chord_leg=True,
        splice_total_bolts=8, splice_bolts_per_leg_each_side=4, splice_rows_per_leg_each_side=4, use_seven_bolt_exception=False,
    )
    cases.extend([
        _validation_case("V19-SP16-TBL-45-ROWS", "16.4 Table 45", "standard_table_structure_cross_check", float(len(line_supports.table_45_catalog()["rows"])), 8.0, 0.0, "rows", "All printed Table 45 rows."),
        _validation_case("V19-SP16-TBL-45-FIRST", "16.4 Table 45", "standard_table_exact_value_cross_check", line_supports.table_45_working_condition_factor("FREE_STANDING_FIRST_TWO_PANELS_WELDED_CHORD"), 0.95, 0.0, "dimensionless", "Welded first-panel chord factor."),
        _validation_case("V19-SP16-TBL-45-LAST", "16.4 Table 45", "standard_table_exact_value_cross_check", line_supports.table_45_working_condition_factor("GUY_ANCHOR_OR_ANGLE_SUPPORT_EMERGENCY"), 0.90, 0.0, "dimensionless", "Emergency guy factor."),
        _validation_case("V19-SP16-TBL-46-ROWS", "16.15 Table 46", "standard_table_structure_cross_check", float(len(line_supports.table_46_catalog()["rows"])), 8.0, 0.0, "rows", "All printed Table 46 rows."),
        _validation_case("V19-SP16-TBL-46-SWITCHYARD", "16.15 Table 46", "standard_table_exact_value_cross_check", float(line_supports.table_46_deformation_check("SWITCHYARD_SUPPORT_ALONG_WIRES", "top_deviation", 0.0)["limit_denominator"]), 100.0, 0.0, "denominator", "Switchyard top-deviation limit 1/100."),
        _validation_case("V19-SP16-TBL-46-EQUIPMENT", "16.15 Table 46", "standard_table_exact_value_cross_check", float(line_supports.table_46_deformation_check("EQUIPMENT_BEAM", "vertical_span", 0.0)["limit_denominator"]), 300.0, 0.0, "denominator", "Equipment-beam span deflection 1/300."),
        _validation_case("V19-SP16-EQ-201", "16.5 equation (201)", "implementation_self_check", line_supports.maximum_slenderness_eq201(12000.0,2000.0), 12.0, 0.0, "dimensionless", "Four-sided member maximum slenderness."),
        _validation_case("V19-SP16-EQ-202", "16.5 equation (202)", "implementation_self_check", line_supports.maximum_slenderness_eq202(12000.0,2000.0), 15.0, 0.0, "dimensionless", "Three-sided member maximum slenderness."),
        _validation_case("V19-SP16-PROC-16.5-MU", "16.5 mu definition", "implementation_self_check", line_supports.pyramidal_effective_length_factor_clause_16_5(1000.0,3000.0), _mu19, 1e-12, "dimensionless", "Pyramidal coefficient."),
        _validation_case("V19-SP16-EQ-203", "16.5 equation (203)", "implementation_self_check", line_supports.maximum_slenderness_eq203(30000.0,1000.0,3000.0), 2.0*_mu19*30000.0/3000.0, 1e-12, "dimensionless", "Pyramidal support maximum slenderness."),
        _validation_case("V19-SP16-EQ-204", "16.6 equation (204)", "implementation_self_check", line_supports.relative_eccentricity_eq204(100e6,1e6,1000.0,1.2), 0.4152, 1e-12, "dimensionless", "Triangular member eccentricity, perpendicular plane."),
        _validation_case("V19-SP16-EQ-205", "16.6 equation (205)", "implementation_self_check", line_supports.relative_eccentricity_eq205(100e6,1e6,1000.0,1.2), 0.36, 1e-12, "dimensionless", "Triangular member eccentricity, parallel plane."),
        _validation_case("V19-SP16-PROC-16.8-BOW", "16.8 initial bow", "implementation_self_check", _aux19["initial_bow_mm"], 15.6, 1e-12, "mm", "Initial bow f_n=0.0013l."),
        _validation_case("V19-SP16-PROC-16.8-INERTIA", "16.8 equivalent inertia", "implementation_self_check", _aux19["equivalent_inertia_mm4"], 80_000_000.0, 1e-6, "mm4", "I_ef=A l^2/lambda_ef^2."),
        _validation_case("V19-SP16-PROC-16.8-DELTA", "16.8 second-order delta", "implementation_self_check", _aux19["delta"], _delta19, 1e-12, "dimensionless", "Second-order denominator."),
        _validation_case("V19-SP16-EQ-206", "16.8 equation (206)", "implementation_self_check", line_supports.guyed_rectangular_moment_eq206(80e6,1.2,1e6,_delta19,12.0,15.6), _eq20619, 1e-6, "Nmm", "Amplified moment."),
        _validation_case("V19-SP16-EQ-207", "16.9 equation (207)", "implementation_self_check", line_supports.guyed_rectangular_shear_eq207(45000.0,1.2,1e6,_delta19,12000.0,12.0,15.6), _eq20719, 1e-9, "N", "Design shear."),
        _validation_case("V19-SP16-EQ-208", "16.10 equation (208)", "implementation_self_check", line_supports.triangular_additional_chord_force_eq208(100e6,50e6,1000.0)["governing_n"], 116000.0, 1e-9, "N", "Governing biaxial additional force."),
        _validation_case("V19-SP16-EQ-209", "16.12 equation (209)", "implementation_self_check", line_supports.bolted_angle_chord_factor_eq209(0.6,2.0,0.3), _eq20919, 1e-12, "dimensionless", "Upper c/b chord branch."),
        _validation_case("V19-SP16-EQ-210", "16.12 equation (210)", "implementation_self_check", line_supports.bolted_angle_chord_factor_eq210(0.5,2.0,0.2), _eq21019, 1e-12, "dimensionless", "Lower c/b chord branch."),
        _validation_case("V19-SP16-EQ-211", "16.12 equation (211)", "implementation_self_check", line_supports.bolted_angle_brace_factor_eq211(0.6,0.3), _eq21119, 1e-12, "dimensionless", "Upper c/b brace branch."),
        _validation_case("V19-SP16-EQ-212", "16.12 equation (212)", "implementation_self_check", line_supports.bolted_angle_brace_factor_eq212(0.5,0.2), _eq21219, 1e-12, "dimensionless", "Lower c/b brace branch."),
        _validation_case("V19-SP16-PROC-16.12-WELDED", "16.12 welded rule", "implementation_self_check", float(line_supports.angle_member_eccentricity_factors_clause_16_12("brace","welded",0.6,2.0,0.3,welded_centering="brace_axes_to_chord_heel")["alpha_d"]), 1.036, 1e-12, "dimensionless", "Welded brace-axis route."),
        _validation_case("V19-SP16-PROC-16.15-EMERGENCY", "16.15 Table 46 note 1", "implementation_self_check", float(line_supports.table_46_deformation_check("SWITCHYARD_SUPPORT_ALONG_WIRES","top_deviation",1.0,load_mode="emergency")["applicable"]), 0.0, 0.0, "boolean", "ORU deviation is not standardized in emergency mode."),
        _validation_case("V19-SP16-PROC-16.13-LENGTH", "16.13", "implementation_self_check", float(_detail19["clause_16_13_effective_length_route"]["effective_length_mm"]), 3000.0, 0.0, "mm", "Primary traverse chord effective length."),
        _validation_case("V19-SP16-PROC-16.14-SLENDERNESS", "16.14", "implementation_self_check", float(_detail19["clause_16_14_first_lower_brace"]["pass"]), 1.0, 0.0, "boolean", "First lower brace is within 160."),
        _validation_case("V19-SP16-PROC-16.16-DIAPHRAGM", "16.16", "implementation_self_check", float(_detail19["clause_16_16_diaphragms"]["maximum_spacing_m"]), 25.0, 0.0, "m", "Free-standing diaphragm maximum spacing."),
        _validation_case("V19-SP16-PROC-16.20-LAMBDA", "16.20 wall slenderness", "implementation_self_check", line_supports.polygonal_tube_wall_relative_slenderness(500.0,10.0,345.0,206000.0), _lam19, 1e-12, "dimensionless", "Polygonal wall relative slenderness."),
        _validation_case("V19-SP16-EQ-214", "16.20 equation (214)", "implementation_self_check", line_supports.polygonal_tube_critical_stress_eq214(_lam19,100.0,-20.0,345.0)["critical_stress_n_mm2"], _sigma_cr19, 1e-10, "N/mm2", "Polygonal wall critical stress."),
        _validation_case("V19-SP16-EQ-213", "16.20 equation (213)", "implementation_self_check", line_supports.polygonal_tube_wall_stability_utilization_eq213(100.0,_sigma_cr19,1.0), 100.0/_sigma_cr19, 1e-12, "dimensionless", "Polygonal wall stability utilization."),
    ])


    _eq215_v20 = 0.41e-3 * 20.0 * math.sqrt(100000.0 / 2.0)
    cases.extend([
        _validation_case("V20-SP16-EQ-215", "17.16 equation (215)", "implementation_self_check", antenna.vibration_damper_distance_eq215(20.0, 100000.0, 2.0), _eq215_v20, 1e-12, "m", "Minimum damper distance."),
        _validation_case("V20-SP16-PROC-17.1-MATERIAL-GROUP", "17.1", "implementation_self_check", float(antenna.antenna_structure_material_group_route_clause_17_1(2, "C345", is_pipe=True, annex_v_grade_selection_confirmed=True)["pass"]), 1.0, 0.0, "boolean", "Pipe grade and group route."),
        _validation_case("V20-SP16-PROC-17.2-ROPE-SELECTION", "17.2", "implementation_self_check", float(antenna.steel_rope_selection_clause_17_2(300.0, "non_aggressive", "spiral_nonspinning", "metallic", built_in_nut_insulator=False, radio_allows_nonmetallic_core=False, round_wire_rope_capacity_kn=400.0, end_binding_length_increased_25_percent=False)["pass"]), 1.0, 0.0, "boolean", "Spiral rope within 325 kN route."),
        _validation_case("V20-SP16-PROC-17.2-ZINC", "17.2", "implementation_self_check", 1.0 if antenna.steel_rope_selection_clause_17_2(300.0, "strong", "spiral_nonspinning", "metallic", built_in_nut_insulator=False, radio_allows_nonmetallic_core=False, round_wire_rope_capacity_kn=400.0, end_binding_length_increased_25_percent=False)["required_zinc_group"] == "ЖС" else 0.0, 1.0, 0.0, "boolean", "Medium/strong environment requires ЖС."),
        _validation_case("V20-SP16-PROC-17.3-ZINC-TERMINATION", "17.3", "implementation_self_check", float(antenna.rope_end_zinc_alloy_check_clause_17_3("ЦАМ9-1,5Л")["pass"]), 1.0, 0.0, "boolean", "Required casting alloy."),
        _validation_case("V20-SP16-PROC-17.4-WIRE-ROUTE", "17.4", "implementation_self_check", float(antenna.antenna_wire_material_route_clause_17_4(annex_b_table_b2_selection_confirmed=True, copper_wire_used=False, technological_necessity_confirmed=False)["pass"]), 1.0, 0.0, "boolean", "Table B.2 route."),
        _validation_case("V20-SP16-PROC-17.5-GAMMA-AL", "17.5", "implementation_self_check", antenna.wire_material_safety_factor_clause_17_5("aluminium"), 2.5, 0.0, "dimensionless", "Aluminium wire gamma_m."),
        _validation_case("V20-SP16-PROC-17.5-GAMMA-SA16", "17.5", "implementation_self_check", antenna.wire_material_safety_factor_clause_17_5("steel_aluminium", 16.0), 2.8, 0.0, "dimensionless", "Steel-aluminium 16 mm2."),
        _validation_case("V20-SP16-PROC-17.5-GAMMA-SA95", "17.5", "implementation_self_check", antenna.wire_material_safety_factor_clause_17_5("steel_aluminium", 95.0), 2.5, 0.0, "dimensionless", "Steel-aluminium 35-95 mm2."),
        _validation_case("V20-SP16-PROC-17.5-GAMMA-SA120", "17.5", "implementation_self_check", antenna.wire_material_safety_factor_clause_17_5("steel_aluminium", 120.0), 2.2, 0.0, "dimensionless", "Steel-aluminium 120 mm2 and above."),
        _validation_case("V20-SP16-PROC-17.5-GAMMA-BIMETAL", "17.5", "implementation_self_check", antenna.wire_material_safety_factor_clause_17_5("bimetal_steel_copper"), 2.0, 0.0, "dimensionless", "Bimetal steel-copper wire."),
        _validation_case("V20-SP16-PROC-17.5-DESIGN-TENSION", "17.5", "implementation_self_check", antenna.wire_design_tension_force_clause_17_5(250000.0, "aluminium")["design_tension_force_n"], 100000.0, 0.0, "N", "Breaking force divided by gamma_m."),
        _validation_case("V20-SP16-PROC-17.7-DEVIATION-WIND", "17.7", "implementation_self_check", antenna.support_relative_deviation_check_clause_17_7(300.0, 30000.0, "wind_or_ice")["utilization"], 1.0, 1e-12, "dimensionless", "Wind/ice 1/100 boundary."),
        _validation_case("V20-SP16-PROC-17.7-DEVIATION-UNILATERAL", "17.7", "implementation_self_check", antenna.support_relative_deviation_check_clause_17_7(100.0, 30000.0, "unilateral_antenna_no_wind")["utilization"], 1.0, 1e-12, "dimensionless", "Unilateral no-wind 1/300 boundary."),
        _validation_case("V20-SP16-PROC-17.8-ERECTION-CONNECTION", "17.8", "implementation_self_check", float(antenna.erection_connection_check_clause_17_8("B", "8.8", sign_changing_force=True, controlled_pretension_confirmed=True, erection_weld_used=False, installer_agreement_confirmed=False)["pass"]), 1.0, 0.0, "boolean", "Sign-changing connection with controlled pretension."),
        _validation_case("V20-SP16-PROC-17.9-DEFLECTION", "17.9", "implementation_self_check", antenna.cross_lattice_and_platform_checks_clause_17_9(260.0, True, 10.0, 8.0, 3000.0)["deflection_limit_mm"], 12.0, 0.0, "mm", "Platform and diaphragm member 1/250 limit."),
        _validation_case("V20-SP16-PROC-17.10-DIAPHRAGM", "17.10", "implementation_self_check", antenna.diaphragm_check_clause_17_10(6000.0, 2500.0, diaphragm_at_concentrated_loads=True, diaphragm_at_chord_breaks=True)["maximum_spacing_mm"], 7500.0, 0.0, "mm", "Three mean section dimensions."),
        _validation_case("V20-SP16-PROC-17.12-ECCENTRICITY", "17.12", "implementation_self_check", antenna.truss_node_detailing_checks_clause_17_12(members_centered_on_chord_axis=True, eccentricity_mm=20.0, chord_cross_section_size_mm=90.0, node_moment_analysis_performed=False, slot_end_hole_diameter_mm=24.0, round_brace_diameter_mm=20.0)["eccentricity_limit_mm"], 30.0, 0.0, "mm", "One-third chord-size limit."),
        _validation_case("V20-SP16-PROC-17.12-HOLE", "17.12", "implementation_self_check", antenna.truss_node_detailing_checks_clause_17_12(members_centered_on_chord_axis=True, eccentricity_mm=20.0, chord_cross_section_size_mm=90.0, node_moment_analysis_performed=False, slot_end_hole_diameter_mm=24.0, round_brace_diameter_mm=20.0)["slot_end_hole_minimum_mm"], 24.0, 0.0, "mm", "Slot-end hole diameter 1.2d."),
        _validation_case("V20-SP16-PROC-17.14-FLEXIBLE-INSERT", "17.14", "implementation_self_check", antenna.flexible_cable_insert_check_clause_17_14(500.0, 20.0)["minimum_clear_length_mm"], 400.0, 0.0, "mm", "Minimum 20 rope diameters."),
        _validation_case("V20-SP16-PROC-17.16-SPAN-TRIGGER", "17.16", "implementation_self_check", float(antenna.vibration_damper_design_clause_17_16(20.0,100000.0,2.0,350.0,low_frequency_hz=2.0,high_frequency_hz=10.0,paired_sequential_dampers=True,low_frequency_selected_from_fundamental_mode=True,high_frequency_damper_above_low_at_distance_s=True,dampers_installed=True,galloping_risk_present=False,free_length_modified_with_leashes=False)["mandatory_by_span_over_300_m"]), 1.0, 0.0, "boolean", "Dampers mandatory above 300 m."),
        _validation_case("V20-SP16-PROC-17.17-MARKING", "17.17", "implementation_self_check", float(antenna.obstruction_marking_and_lighting_check_clause_17_17(True)["pass"]), 1.0, 0.0, "boolean", "External marking and lighting evidence gate."),
        _validation_case("V20-SP16-PROC-17.18-GALVANIZING", "17.18", "implementation_self_check", float(antenna.galvanizing_check_clause_17_18(guy_mechanical_details_galvanized=True,insulator_fittings_galvanized=True,fasteners_galvanized=True)["pass"]), 1.0, 0.0, "boolean", "All specified detail groups galvanized."),
    ])
    for row in antenna.table_47_catalog()["rows"]:
        cases.append(_validation_case(
            f"V20-SP16-TBL-47-{row['case_id']}", "17.6 Table 47", "normative_table_transcription",
            antenna.table_47_working_condition_factor(row["case_id"]), float(row["gamma_c"]), 0.0,
            "dimensionless", "Exact Table 47 categorical lookup."
        ))

    # v0.21 — Section 18 reconstruction assessment and strengthening.
    eq216_gamma = reconstruction.gamma_n_clause_18_3_13(
        welding_used=True, initial_design_stress_n_mm2=100.0, design_yield_resistance_n_mm2=330.0
    )
    eq216_reference_gamma = 0.95 - 0.25 * 100.0 / 330.0
    eq216_reference = 500000.0 / (3000.0 * 330.0 * eq216_reference_gamma * 0.9)
    eq217_gamma = reconstruction.gamma_m_clause_18_3_13(3, 500000.0, 3000.0, 330.0, eq216_gamma)
    eq217_stress = 500000.0 / 3000.0 + 10000000.0 * 100.0 / 8000000.0 + (-2000000.0) * 50.0 / 4000000.0
    eq217_reference = abs(eq217_stress) / (330.0 * eq217_gamma * 0.9)
    alpha_n_reference = 1000000.0 / (1000000.0 - 200000.0)
    eq221_reference = 10.0 * (1.0 - alpha_n_reference * 1000.0 / (8000000.0 + 1000.0))
    v_reference = 0.04 * 0.8**2
    eq222_reference = 1.0 * alpha_n_reference * 100.0**2 / 8.0 * (1.2 * v_reference * 2.0 + 0.8 * v_reference * -1.0)
    eq220_reference = 5.0 + eq221_reference + eq222_reference
    eq219_reference = eq220_reference * 3000.0 / 300000.0
    eq224_reference = (330.0 / 300.0 * (1.0 - 2000.0 / 3000.0) + 2000.0 / 3000.0) * (330.0 / 300.0 * (1.0 - 8000000.0 / 12000000.0) + 8000000.0 / 12000000.0)
    eq223_reference = 300.0 * math.sqrt(eq224_reference)
    eq218_reference = 500000.0 / (0.8 * 3000.0 * eq223_reference * 0.9)
    v21_cases = [
        _validation_case("V21-SP16-PROC-18.1.1-CATEGORY", "18.1.1", "implementation_self_check", float(reconstruction.technical_condition_category_clause_18_1_1(defects_or_damage_present=False, local_character_only=True, restricts_normal_operation=False, requires_monitoring_or_strengthening=False, sudden_failure_or_global_instability_risk=False)["category"] == "normative"), 1.0, 0.0, "boolean", "Normative technical-condition route."),
        _validation_case("V21-SP16-PROC-18.1.3-EXEMPTION", "18.1.3", "implementation_self_check", float(reconstruction.verification_calculation_exemption_clause_18_1_3(15.0, defects_or_damage_present=False, operating_conditions_worsened=False, loads_increased=False, main_member_strengthening_required=False)["verification_calculation_may_be_omitted"]), 1.0, 0.0, "boolean", "Verification-calculation exemption at 15 years."),
        _validation_case("V21-SP16-PROC-18.2.4-RY", "18.2.4", "implementation_self_check", reconstruction.existing_steel_design_resistances_clause_18_2_4("after_1988_statistical_certificate", 355.0, 510.0)["design_yield_resistance_n_mm2"], 355.0/1.05, 1e-12, "N/mm2", "Existing steel design yield resistance."),
        _validation_case("V21-SP16-PROC-18.2.5-RWF", "18.2.5", "implementation_self_check", reconstruction.existing_weld_resistance_defaults_clause_18_2_5(510.0, 300.0, "after_1972")["fillet_weld_metal_resistance_n_mm2"], 224.4, 1e-12, "N/mm2", "Default fillet-weld resistance."),
        _validation_case("V21-SP16-PROC-18.2.6-RBS", "18.2.6", "implementation_self_check", reconstruction.unknown_bolt_resistance_defaults_clause_18_2_6()["bolt_shear_design_resistance_n_mm2"], 150.0, 0.0, "N/mm2", "Unknown-bolt shear resistance default."),
        _validation_case("V21-SP16-PROC-18.2.7-RIVET-CAPACITY", "18.2.7", "implementation_self_check", reconstruction.rivet_connection_capacity_clause_18_2_7("shear", 180.0, 20.0, shear_planes=2)["capacity_n"], 180.0*0.785*20.0**2*2.0, 1e-9, "N", "One-rivet shear capacity."),
        _validation_case("V21-SP16-PROC-18.3.9-GROUP1", "18.3.9", "implementation_self_check", reconstruction.weld_heating_stress_limit_clause_18_3_9(1, 300.0), 60.0, 0.0, "N/mm2", "Group 1 weld-heating stress limit."),
        _validation_case("V21-SP16-PROC-18.3.9-GROUP2", "18.3.9", "implementation_self_check", reconstruction.weld_heating_stress_limit_clause_18_3_9(2, 300.0), 120.0, 0.0, "N/mm2", "Group 2 weld-heating stress limit."),
        _validation_case("V21-SP16-PROC-18.3.9-GROUP4", "18.3.9", "implementation_self_check", reconstruction.weld_heating_stress_limit_clause_18_3_9(4, 300.0), 240.0, 0.0, "N/mm2", "Group 3-4 weld-heating stress limit."),
        _validation_case("V21-SP16-EQ-216-GAMMA-N", "18.3.13 equation (216)", "implementation_self_check", eq216_gamma, eq216_reference_gamma, 1e-12, "dimensionless", "Welding reduction factor gamma_N."),
        _validation_case("V21-SP16-EQ-216", "18.3.13 equation (216)", "implementation_self_check", reconstruction.symmetric_compression_strength_utilization_eq216(500000.0, 3000.0, 330.0, eq216_gamma, 0.9), eq216_reference, 1e-12, "dimensionless", "Symmetric compressed strengthened section."),
        _validation_case("V21-SP16-EQ-217-GAMMA-M", "18.3.13 equation (217)", "implementation_self_check", eq217_gamma, 1.0, 0.0, "dimensionless", "Group 3 gamma_M below the axial-stress override threshold."),
        _validation_case("V21-SP16-EQ-217", "18.3.13 equation (217)", "implementation_self_check", reconstruction.asymmetric_strength_utilization_eq217(500000.0,3000.0,10000000.0,8000000.0,100.0,-2000000.0,4000000.0,50.0,330.0,eq217_gamma,0.9)["utilization"], eq217_reference, 1e-12, "dimensionless", "Asymmetric strengthened section stress utilization."),
        _validation_case("V21-SP16-EQ-218", "18.3.15 equation (218)", "implementation_self_check", reconstruction.strengthened_member_stability_utilization_eq218(500000.0,0.8,3000.0,eq223_reference,0.9), eq218_reference, 1e-12, "dimensionless", "Strengthened member stability utilization."),
        _validation_case("V21-SP16-EQ-219", "18.3.14 equation (219)", "implementation_self_check", reconstruction.reduced_relative_eccentricity_eq219(eq220_reference,3000.0,300000.0), eq219_reference, 1e-12, "dimensionless", "Reduced relative eccentricity."),
        _validation_case("V21-SP16-EQ-220", "18.3.14 equation (220)", "implementation_self_check", reconstruction.equivalent_eccentricity_eq220(5.0,eq221_reference,1.0,eq222_reference), eq220_reference, 1e-12, "mm", "Equivalent eccentricity."),
        _validation_case("V21-SP16-EQ-221", "18.3.14 equation (221)", "implementation_self_check", reconstruction.post_strengthening_initial_deflection_eq221(10.0,alpha_n_reference,1000.0,8000000.0), eq221_reference, 1e-12, "mm", "Retained initial deflection."),
        _validation_case("V21-SP16-EQ-222-V", "18.3.14 equation (222)", "implementation_self_check", reconstruction.weld_shortening_parameter_v(0.8), v_reference, 1e-15, "equation-specific", "Weld shortening parameter V."),
        _validation_case("V21-SP16-EQ-222", "18.3.14 equation (222)", "implementation_self_check", reconstruction.welding_residual_deflection_eq222(1.0,alpha_n_reference,100.0,[{"n_i":1.2,"v_i":v_reference,"y_i":2.0},{"n_i":0.8,"v_i":v_reference,"y_i":-1.0}]), eq222_reference, 1e-12, "mm", "Welding residual deflection with explicit Figure 24 coefficients."),
        _validation_case("V21-SP16-EQ-223", "18.3.15 equation (223)", "implementation_self_check", reconstruction.effective_design_resistance_eq223(300.0,eq224_reference), eq223_reference, 1e-12, "N/mm2", "Effective strengthened-section resistance."),
        _validation_case("V21-SP16-EQ-224", "18.3.15 equation (224)", "implementation_self_check", reconstruction.composite_resistance_factor_eq224(330.0,300.0,2000.0,3000.0,8000000.0,12000000.0), eq224_reference, 1e-12, "dimensionless", "Composite resistance factor."),
        _validation_case("V21-SP16-PROC-18.3.16-DEVIATION", "18.3.16", "implementation_self_check", float(reconstruction.existing_deviation_acceptance_clause_18_3_16(listed_deviation_only=True, damage_caused_by_deviation_absent=True, adverse_operating_change_excluded=True, capacity_and_stiffness_justified=True, fatigue_and_brittle_fracture_measures_confirmed=True)["pass"]), 1.0, 0.0, "boolean", "All deviation-retention conditions satisfied."),
    ]
    cases.extend(v21_cases)
    for row in reconstruction.table_48_catalog()["rows"]:
        state = row["limit_state"]
        group = "B" if row["connection_group"] == "B_or_C" else row["connection_group"]
        steel = row.get("rivet_steel", "St2_St3")
        if state == "bearing":
            calculated = reconstruction.table_48_rivet_resistance(state, group, steel, connected_steel_design_yield_n_mm2=300.0)
            reference = (2.0 if group == "B" else 1.7) * 300.0
        else:
            calculated = reconstruction.table_48_rivet_resistance(state, group, steel)
            reference = float(row["value"])
        cases.append(_validation_case(
            f"V21-SP16-TBL-48-{state}-{group}-{steel}", "18.2.7 Table 48", "normative_table_transcription",
            calculated, reference, 0.0, "N/mm2", "Exact Table 48 categorical lookup."
        ))
    cases.append(_validation_case("V21-SP16-TBL-48-COUNTERSUNK", "18.2.7 Table 48 note", "normative_table_transcription", reconstruction.table_48_rivet_resistance("shear","B","St2_St3",countersunk_or_semicountersunk_head=True), 144.0, 0.0, "N/mm2", "Countersunk-head 0.8 reduction."))

    return {
        "standard": "СП 16.13330.2017 «Стальные конструкции»",
        "release_stage": RELEASE_STAGE,
        "validation_status": "cumulative_internal_regression_and_normative_table_transcription_checks_through_equation_224_including_reconstructed_equations_10_11;_not_external_certification",
        "all_passed": all(case["pass_fail"] == "pass" for case in cases),
        "validation_cases": cases,
        "limitations": [
            "The supplied implemented clauses through Section 18 and Annexes Д and Ж contain no complete numerical worked example for independent normative reproduction.",
            "Table D.1 is a rounded tabulation of equations (8)-(9), so this cross-check is not independent of the normative formula model.",
        ],
    }


def write_validation_reports(report: dict[str, Any], reports_dir: str | Path) -> None:
    """
    Summary:
        Write machine-readable and human-readable Phase 0.23 reconstructed validation reports.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: Package validation infrastructure
        Annex: D
        Equation/Table: None
        Audit ID: VALIDATION-WRITER-004
        Normative status: no_code_explanatory

    Mathematical form:
        Validation dictionary -> JSON and Markdown serialization.

    Parameters:
        report:
            Type: dict[str, Any]
            Unit: mixed
            Meaning: Result returned by run_core_validation_cases.
            Valid range: Dictionary with validation_cases.
            Source: validation runner
        reports_dir:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Destination directory.
            Valid range: Writable path.
            Source: package layout

    Returns:
        Type: None
        Unit: not applicable
        Meaning: validation_report.json and validation_report.md are written.

    Assumptions:
        - Every case contains the required error and pass/fail fields.

    Sign convention:
        - Errors are non-negative.

    Unit convention:
        - Units are serialized per case.

    Applicability:
        - Phase 0.23 reconstructed validation reporting.

    Limitations:
        - Markdown is compact and JSON is the authoritative full record.

    Raises:
        OSError: The destination cannot be created or written.

    Examples:
        >>> write_validation_reports(run_core_validation_cases(), "reports")

    Tests:
        Unit tests:
            - tests/test_validation_examples.py::test_validation_report_writer
        Validation cases:
            - CORE-SELF-CHECK-v0.18

    Implementation notes:
        - No failing case is suppressed from either report.
        - Defaults must be explicit in the input configuration.
    """
    destination = Path(reports_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Validation report",
        "",
        f"- Release: `{report['release_stage']}`",
        f"- Status: `{report['validation_status']}`",
        f"- All checks passed: **{'yes' if report['all_passed'] else 'no'}**",
        f"- Cases: {len(report['validation_cases'])}",
        "",
        "The report contains arithmetic self-checks and cross-checks of the transcribed Tables D.1-D.6, 10a, E.1, E.2, 11-48, Annex K Table K.1, and Ж.1-Ж.5. It contains no invented standard worked example.",
        "",
        "| Case | Reference | Calculated | Reference value | Abs. error | Tolerance | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for case in report["validation_cases"]:
        lines.append(
            f"| {case['validation_case_id']} | {case['standard_reference']} | {case['calculated_value']:.12g} | "
            f"{case['reference_value']:.12g} | {case['absolute_error']:.3g} | {case['tolerance']:.3g} | {case['pass_fail']} |"
        )
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in report.get("limitations", [])]])
    (destination / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
