"""Stage N3 guided axial-member workflows for current SP 16.13330.2017.

This module does not replace the audited scalar equation functions.  It composes them
into branch-safe, user-facing workflows so only normative checks applicable to the
selected member state are evaluated.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

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
from . import built_up_axial_members as bm

CURRENT_SP16_SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def _real(value: float, name: str, *, minimum: float | None = None, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite")
    if positive and x <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    if minimum is not None and x < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return x


def select_equation_5_resistance_branch(
    force_state: str,
    normative_yield_resistance_n_mm2: float,
    post_yield_service_possible: bool,
) -> dict[str, Any]:
    """
    Summary:
        Select the current clause 7.1.1 equation-(5) resistance branch.
    Standard reference:
        СП 16.13330.2017, Changes 1-6 through 09.12.2024, clause 7.1.1, equation (5).
    Parameters:
        force_state, Ryn and the explicit post-yield-service condition.
    Returns:
        Auditable branch identifier and selection reason.
    Assumptions:
        The member is centrally tensioned or compressed and clause 7.1.1 is applicable.
    Sign convention:
        Force state is categorical; resistance is a non-negative magnitude.
    Unit convention:
        Ryn is N/mm2.
    Applicability:
        Solid and built-up axial strength routes that refer to 7.1.1.
    Limitations:
        Does not determine net area, gamma_c or material-table applicability.
    Raises:
        TypeError or ValueError for invalid inputs.
    Examples:
        select_equation_5_resistance_branch("compression", 440.0, False).
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        The 440 N/mm2 boundary and tensile post-yield exception are explicit; no caller-selected branch is trusted.
    """
    if force_state not in {"tension", "compression"}:
        raise ValueError("force_state must be 'tension' or 'compression'")
    ryn = _real(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2", minimum=0.0)
    if not isinstance(post_yield_service_possible, bool):
        raise TypeError("post_yield_service_possible must be boolean")
    if force_state == "tension" and post_yield_service_possible:
        branch = "ultimate"
        reason = "7.1.1 tensile member whose service is possible after reaching yield"
    elif ryn > 440.0:
        branch = "ultimate"
        reason = "7.1.1 Ryn > 440 N/mm2"
    else:
        branch = "yield"
        reason = "7.1.1 Ryn <= 440 N/mm2 and no tensile post-yield-service exception"
    return {
        "branch": branch,
        "force_state": force_state,
        "Ryn_n_mm2": ryn,
        "post_yield_service_possible": post_yield_service_possible,
        "reason": reason,
        "source_clause": "7.1.1",
    }


def geometric_slenderness_from_effective_length(effective_length_mm: float, radius_of_gyration_mm: float) -> float:
    """
    Summary:
        Calculate geometric slenderness lambda=l_eff/i.
    Standard reference:
        СП 16.13330.2017, clause 7.1.3 definition of relative slenderness and member slenderness.
    Parameters:
        Effective length and radius of gyration.
    Returns:
        Dimensionless geometric slenderness.
    Assumptions:
        Effective length and radius refer to the same calculation plane.
    Sign convention:
        Length quantities are non-negative magnitudes.
    Unit convention:
        Both length inputs use mm.
    Applicability:
        Axial compression stability preprocessing.
    Limitations:
        Does not derive effective length from restraint topology.
    Raises:
        TypeError or ValueError for invalid inputs.
    Examples:
        geometric_slenderness_from_effective_length(4000, 40) returns 100.
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        No unit conversion or hidden effective-length coefficient is applied.
    """
    leff = _real(effective_length_mm, "effective_length_mm", minimum=0.0)
    radius = _real(radius_of_gyration_mm, "radius_of_gyration_mm", positive=True)
    return leff / radius


def residual_stress_factor_gamma_res(relative_slenderness_value: float, design_yield_resistance_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Calculate gamma_res for the optional rolled-I equation (7a) route.
    Standard reference:
        СП 16.13330.2017, Changes 1-6 through 09.12.2024, clause 7.1.3, equation (7a) coefficient rules.
    Parameters:
        Relative slenderness and design yield resistance Ry.
    Returns:
        gamma_res with route and source trace.
    Assumptions:
        Equation (7a) is applied only to a rolled I-section.
    Sign convention:
        Slenderness and resistance are positive magnitudes.
    Unit convention:
        Ry is N/mm2; gamma_res and relative slenderness are dimensionless.
    Applicability:
        Optional current-SP16 rolled-I central-compression stability route.
    Limitations:
        Does not independently judge whether using equation (7a) is preferable to equation (7).
    Raises:
        TypeError or ValueError for invalid inputs.
    Examples:
        residual_stress_factor_gamma_res(3.0, 245.0) gives gamma_res=1.
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        The current source is transcribed literally, including 0.2*lambda_bar+0.9 for Ry=390 above lambda_bar=5; intermediate Ry is linearly interpolated.
    """
    lb = _real(relative_slenderness_value, "relative_slenderness_value", minimum=0.0)
    ry = _real(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2", positive=True)

    def g245(lam: float) -> float:
        return 1.0 if lam <= 3.0 else 0.1 * lam + 0.7

    def g390(lam: float) -> float:
        return 1.0 if lam <= 5.0 else 0.2 * lam + 0.9

    if ry <= 245.0:
        gamma = g245(lb)
        route = "Ry<=245: use Ry=245 endpoint rule"
    elif ry >= 390.0:
        gamma = g390(lb)
        route = "Ry>=390: use Ry=390 endpoint rule"
    else:
        low = g245(lb)
        high = g390(lb)
        fraction = (ry - 245.0) / (390.0 - 245.0)
        gamma = low + fraction * (high - low)
        route = "245<Ry<390: linear interpolation in Ry between endpoint gamma_res rules"
    return {
        "gamma_res": gamma,
        "relative_slenderness": lb,
        "design_yield_resistance_n_mm2": ry,
        "route": route,
        "source_clause": "7.1.3",
        "source_equation": "(7a) coefficient rule",
        "source_sha256": CURRENT_SP16_SOURCE_SHA256,
    }


def central_compression_stability_utilization_eq7a(
    axial_force_n: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    stability_coefficient_phi: float,
    residual_stress_factor: float,
) -> float:
    """
    Summary:
        Evaluate the optional current equation (7a) central-compression utilization.
    Standard reference:
        СП 16.13330.2017, clause 7.1.3, equation (7a).
    Parameters:
        N, A, Ry, gamma_c, phi and gamma_res.
    Returns:
        Dimensionless utilization.
    Assumptions:
        Rolled-I applicability and gamma_res selection have already been established.
    Sign convention:
        Compression force is supplied as a non-negative magnitude.
    Unit convention:
        N in N, A in mm2, Ry in N/mm2; coefficients dimensionless.
    Applicability:
        Rolled I-sections under the optional equation (7a) route.
    Limitations:
        Does not calculate phi or gamma_res internally.
    Raises:
        TypeError or ValueError for invalid inputs.
    Examples:
        central_compression_stability_utilization_eq7a(100000,1000,250,1,0.8,1.25).
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        gamma_res is used exactly in the denominator printed in equation (7a).
    """
    n = _real(axial_force_n, "axial_force_n", minimum=0.0)
    area = _real(gross_area_mm2, "gross_area_mm2", positive=True)
    ry = _real(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2", positive=True)
    gamma_c = _real(working_condition_factor, "working_condition_factor", positive=True)
    phi = _real(stability_coefficient_phi, "stability_coefficient_phi", positive=True)
    gamma_res = _real(residual_stress_factor, "residual_stress_factor", positive=True)
    if phi > 1.0:
        raise ValueError("stability_coefficient_phi must not exceed 1")
    return n / (gamma_res * phi * area * ry * gamma_c)


def _exact_d1_reference(lambda_bar: float, section_type: str) -> dict[str, Any]:
    try:
        value = annex_d1_stability_coefficient(lambda_bar, section_type)
    except ValueError:
        return {"status": "not_an_exact_table_node_no_interpolation_applied", "phi": None}
    return {"status": "exact_node_available", "phi": value}


def solid_axial_member_workflow(
    *,
    force_state: str,
    axial_force_n: float,
    gross_area_mm2: float,
    net_area_mm2: float,
    normative_yield_resistance_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    working_condition_factor: float,
    post_yield_service_possible: bool,
    elastic_modulus_n_mm2: float,
    effective_length_mm: float | None = None,
    radius_of_gyration_mm: float | None = None,
    section_type: str | None = None,
    local_stability_prerequisites_satisfied: bool | None = None,
    stability_formula: str | None = None,
    rolled_i_section_confirmed: bool = False,
    single_angle_clause_7_1_2: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Compose an applicability-safe guided solid axial-member calculation.
    Standard reference:
        СП 16.13330.2017, clauses 7.1.1-7.1.3, equations (5)-(9), Tables 6, 7 and Annex D.1 reference.
    Parameters:
        Explicit member state, actions, areas, material values, optional compression and single-angle inputs.
    Returns:
        Structured step-by-step strength/stability trace and governing result for evaluated checks.
    Assumptions:
        Supplied material/section values are already resolved by Stage N1/N2 or equivalent audited inputs.
    Sign convention:
        Axial force is a non-negative magnitude and force_state determines tension/compression.
    Unit convention:
        N, mm, mm2 and N/mm2 are used explicitly.
    Applicability:
        Central tension/compression of solid-section members in the declared 7.1 scope.
    Limitations:
        Local stability 7.3 is only accepted through explicit prerequisite confirmation; effective-length topology is external.
    Raises:
        TypeError or ValueError on missing/inapplicable branch data.
    Examples:
        See examples/axial_member_guided_example.json.
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        Inapplicable branches are not calculated; equation (5) branch selection is derived from the current clause instead of being chosen manually.
    """
    n = _real(axial_force_n, "axial_force_n", minimum=0.0)
    ag = _real(gross_area_mm2, "gross_area_mm2", positive=True)
    an = _real(net_area_mm2, "net_area_mm2", positive=True)
    if an > ag + 1e-9:
        raise ValueError("net_area_mm2 must not exceed gross_area_mm2")
    ry = _real(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2", positive=True)
    ru = _real(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2", positive=True)
    gu = _real(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor", positive=True)
    gc = _real(working_condition_factor, "working_condition_factor", positive=True)
    elastic = _real(elastic_modulus_n_mm2, "elastic_modulus_n_mm2", positive=True)

    branch = select_equation_5_resistance_branch(force_state, normative_yield_resistance_n_mm2, post_yield_service_possible)
    if branch["branch"] == "yield":
        strength = axial_strength_utilization_yield(n, an, ry, gc)
    else:
        strength = axial_strength_utilization_ultimate(n, an, ru, gu, gc)

    out: dict[str, Any] = {
        "force_state": force_state,
        "equation_5": {
            "resistance_branch": branch,
            "utilization": strength,
            "pass": strength <= 1.0,
        },
        "equation_6_single_angle": {"status": "not_applicable", "utilization": None, "pass": None},
        "compression_stability": {"status": "not_applicable_for_tension", "equation_7": None, "equation_7a": None},
    }

    if single_angle_clause_7_1_2 is not None:
        if force_state != "tension":
            raise ValueError("single_angle_clause_7_1_2 is applicable only to tension")
        required = {
            "applicability_confirmed", "table_6_geometry_case_confirmed", "table_6_case",
            "attached_leg_net_strip_area_mm2", "special_ten_percent_reduction_applies",
        }
        missing = required - set(single_angle_clause_7_1_2)
        if missing:
            raise ValueError(f"single_angle_clause_7_1_2 missing fields: {sorted(missing)}")
        if single_angle_clause_7_1_2["applicability_confirmed"] is not True or single_angle_clause_7_1_2["table_6_geometry_case_confirmed"] is not True:
            raise ValueError("single-angle 7.1.2 applicability and Table 6 geometry must be explicitly confirmed")
        if float(normative_yield_resistance_n_mm2) > 380.0:
            raise ValueError("clause 7.1.2 equation (6) route requires steel yield strength <=380 N/mm2")
        a1, a2, beta = table_6_angle_coefficients(str(single_angle_clause_7_1_2["table_6_case"]))
        gamma_c1 = single_angle_working_condition_factor(
            an,
            float(single_angle_clause_7_1_2["attached_leg_net_strip_area_mm2"]),
            a1, a2, beta,
            bool(single_angle_clause_7_1_2["special_ten_percent_reduction_applies"]),
        )
        eq6 = single_angle_connection_strength_utilization(n, an, ru, gu, gamma_c1)
        out["equation_6_single_angle"] = {
            "status": "applicable_and_evaluated",
            "table_6": {"alpha1": a1, "alpha2": a2, "beta": beta},
            "gamma_c1": gamma_c1,
            "utilization": eq6,
            "pass": eq6 <= 1.0,
        }

    if force_state == "compression":
        if local_stability_prerequisites_satisfied is not True:
            raise ValueError("7.1.3 stability requires explicit confirmation that 7.3.2-7.3.9 prerequisites are satisfied")
        if effective_length_mm is None or radius_of_gyration_mm is None or section_type is None:
            raise ValueError("compression stability requires effective_length_mm, radius_of_gyration_mm and section_type")
        if stability_formula not in {"equation_7", "equation_7a_rolled_i", "both"}:
            raise ValueError("stability_formula must be equation_7, equation_7a_rolled_i, or both for compression")
        geom_lambda = geometric_slenderness_from_effective_length(effective_length_mm, radius_of_gyration_mm)
        lambda_bar = relative_slenderness(geom_lambda, ry, elastic)
        phi = central_compression_stability_coefficient(lambda_bar, section_type)
        d1 = _exact_d1_reference(lambda_bar, section_type)
        eq7 = central_compression_stability_utilization(n, ag, ry, gc, phi)
        stability: dict[str, Any] = {
            "status": "evaluated",
            "geometric_slenderness": geom_lambda,
            "relative_slenderness": lambda_bar,
            "section_type": section_type,
            "phi": phi,
            "table_d1_reference": d1,
            "selected_formula": stability_formula,
            "equation_7": {"utilization": eq7, "pass": eq7 <= 1.0} if stability_formula in {"equation_7", "both"} else None,
            "equation_7a": None,
        }
        if stability_formula in {"equation_7a_rolled_i", "both"}:
            if rolled_i_section_confirmed is not True:
                raise ValueError("equation (7a) is permitted only for a rolled I-section; confirmation is required")
            gamma_res = residual_stress_factor_gamma_res(lambda_bar, ry)
            eq7a = central_compression_stability_utilization_eq7a(n, ag, ry, gc, phi, gamma_res["gamma_res"])
            stability["equation_7a"] = {
                "gamma_res": gamma_res,
                "utilization": eq7a,
                "pass": eq7a <= 1.0,
            }
        out["compression_stability"] = stability
    elif stability_formula is not None or effective_length_mm is not None or radius_of_gyration_mm is not None:
        # The inputs are tolerated only when absent; this catches stale UI state that could mislead a trace.
        raise ValueError("tension workflow must not supply compression-stability inputs")

    checks = [out["equation_5"]["pass"]]
    if out["equation_6_single_angle"]["pass"] is not None:
        checks.append(bool(out["equation_6_single_angle"]["pass"]))
    stab = out["compression_stability"]
    if stab.get("status") == "evaluated":
        if stab.get("equation_7") is not None:
            checks.append(bool(stab["equation_7"]["pass"]))
        if stab.get("equation_7a") is not None:
            checks.append(bool(stab["equation_7a"]["pass"]))
    out["governing_pass"] = all(checks)
    return out


def selected_table8_effective_slenderness(
    section_type: int,
    connector_system: str,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Summary:
        Dispatch to exactly one selected Table 8 effective-slenderness formula.
    Standard reference:
        СП 16.13330.2017, clause 7.2.2, Table 8, equations (12)-(17).
    Parameters:
        Built-up section type, connector system and only the branch-specific data mapping.
    Returns:
        Selected equation number and effective slenderness.
    Assumptions:
        Section type and connector arrangement have been classified from the Table 8 diagrams.
    Sign convention:
        Geometric and slenderness quantities are non-negative magnitudes.
    Unit convention:
        Lengths mm, areas mm2, inertias mm4; slenderness dimensionless.
    Applicability:
        Built-up compressed members with at least six panels.
    Limitations:
        Does not infer section type from arbitrary geometry and does not apply Table 8 for fewer than six panels.
    Raises:
        ValueError for unsupported selection or missing branch inputs.
    Examples:
        selected_table8_effective_slenderness(1, "lattice", data).
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        Eliminates the legacy runner defect that evaluated all six Table 8 formulas irrespective of the selected route.
    """
    if isinstance(section_type, bool) or section_type not in {1, 2, 3}:
        raise ValueError("section_type must be integer 1, 2, or 3")
    if connector_system not in {"battens", "lattice"}:
        raise ValueError("connector_system must be 'battens' or 'lattice'")

    def need(*names: str) -> list[float]:
        missing = [n for n in names if n not in data]
        if missing:
            raise ValueError(f"selected Table 8 route missing fields: {missing}")
        return [float(data[n]) for n in names]

    if connector_system == "battens" and section_type == 1:
        args = need("whole_member_slenderness_y", "branch_slenderness_1", "branch_inertia_axis_1_mm4", "branch_axis_spacing_b_mm", "batten_inertia_mm4", "batten_pitch_mm")
        value = bm.battened_effective_slenderness_type_1(*args); eq = 12
    elif connector_system == "battens" and section_type == 2:
        args = need("whole_member_max_slenderness", "branch_slenderness_1", "branch_slenderness_2", "branch_inertia_axis_1_mm4", "branch_inertia_axis_2_mm4", "branch_axis_spacing_b1_mm", "branch_axis_spacing_b2_mm", "batten_inertia_plane_1_mm4", "batten_inertia_plane_2_mm4", "batten_pitch_mm")
        value = bm.battened_effective_slenderness_type_2(*args); eq = 13
    elif connector_system == "battens" and section_type == 3:
        args = need("whole_member_max_slenderness", "branch_slenderness_3", "branch_inertia_axis_3_mm4", "branch_axis_spacing_b_mm", "batten_inertia_mm4", "batten_pitch_mm")
        value = bm.battened_effective_slenderness_type_3(*args); eq = 14
    elif connector_system == "lattice" and section_type == 1:
        args = need("whole_member_slenderness_y", "total_area_mm2", "diagonal_area_plane_1_mm2", "diagonal_length_d_mm", "branch_axis_spacing_b_mm", "panel_length_mm")
        value = bm.lattice_effective_slenderness_type_1(*args); eq = 15
    elif connector_system == "lattice" and section_type == 2:
        args = need("whole_member_max_slenderness", "total_area_mm2", "diagonal_area_plane_1_mm2", "diagonal_area_plane_2_mm2", "diagonal_length_d1_mm", "diagonal_length_d2_mm", "branch_axis_spacing_b1_mm", "branch_axis_spacing_b2_mm", "panel_length_mm")
        value = bm.lattice_effective_slenderness_type_2(*args); eq = 16
    else:
        args = need("whole_member_max_slenderness", "total_area_mm2", "diagonal_area_one_face_mm2", "diagonal_length_d_mm", "branch_axis_spacing_b_mm", "panel_length_mm")
        value = bm.lattice_effective_slenderness_type_3(*args); eq = 17
    return {
        "section_type": section_type,
        "connector_system": connector_system,
        "equation": eq,
        "effective_slenderness": value,
        "source_table": "8",
    }


def built_up_axial_member_workflow(
    *,
    force_state: str,
    axial_force_n: float,
    total_net_area_mm2: float,
    gross_area_mm2: float,
    normative_yield_resistance_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    working_condition_factor: float,
    elastic_modulus_n_mm2: float,
    post_yield_service_possible: bool,
    panel_count: int | None = None,
    connector_system: str | None = None,
    built_up_section_type: int | None = None,
    table8_data: Mapping[str, Any] | None = None,
    branch_relative_slenderness: float | None = None,
    branch_section_type: str | None = None,
    close_contact_check: Mapping[str, Any] | None = None,
    connector_force_check: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Compose a branch-safe guided built-up axial-member workflow.
    Standard reference:
        СП 16.13330.2017, clauses 7.2.1-7.2.10, equations (5), (7)-(9), (12)-(22), Table 8.
    Parameters:
        Member state, material/area values, selected connector topology and optional detailing/connector checks.
    Returns:
        Structured strength, stability, branch, spacing and connector-force trace for applicable checks.
    Assumptions:
        The selected built-up topology and supplied branch geometry correspond to the normative Table 8 diagrams.
    Sign convention:
        Axial and connector forces are non-negative magnitudes.
    Unit convention:
        N, mm, mm2, mm4 and N/mm2 are used explicitly.
    Applicability:
        Centrally tensioned/compressed built-up members in clauses 7.2.1-7.2.10.
    Limitations:
        Fewer-than-six-panel frame analysis and any missing effective-slenderness producer are surfaced as external/fail-closed routes rather than invented.
    Raises:
        TypeError or ValueError on inconsistent topology, invalid ranges or missing selected-branch data.
    Examples:
        See examples/built_up_axial_member_guided_example.json.
    Tests:
        tests/test_stage_n3_axial_workflows.py.
    Implementation notes:
        Only the selected Table 8 formula runs; lattice 7.2.5 reduction is activated transparently and battens use the separate 7.2.3 branch limit.
    """
    n = _real(axial_force_n, "axial_force_n", minimum=0.0)
    ag = _real(gross_area_mm2, "gross_area_mm2", positive=True)
    an = _real(total_net_area_mm2, "total_net_area_mm2", positive=True)
    if an > ag + 1e-9:
        raise ValueError("total_net_area_mm2 must not exceed gross_area_mm2")
    ry = _real(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2", positive=True)
    ru = _real(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2", positive=True)
    gu = _real(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor", positive=True)
    gc = _real(working_condition_factor, "working_condition_factor", positive=True)
    elastic = _real(elastic_modulus_n_mm2, "elastic_modulus_n_mm2", positive=True)

    branch = select_equation_5_resistance_branch(force_state, normative_yield_resistance_n_mm2, post_yield_service_possible)
    strength = bm.built_up_axial_strength_utilization(n, an, branch["branch"], ry, ru, gu, gc)
    out: dict[str, Any] = {
        "force_state": force_state,
        "clause_7_2_1_strength": {"resistance_branch": branch, "utilization": strength, "pass": strength <= 1.0},
        "clause_7_2_2_to_7_2_5_stability": {"status": "not_applicable_for_tension"},
        "clause_7_2_6_close_contact": {"status": "not_requested"},
        "clause_7_2_7_to_7_2_10_connectors": {"status": "not_applicable_or_not_requested"},
    }

    if close_contact_check is not None:
        required = {"connection_spacing_mm", "selected_radius_of_gyration_mm", "intermediate_connection_count"}
        missing = required - set(close_contact_check)
        if missing:
            raise ValueError(f"close_contact_check missing fields: {sorted(missing)}")
        check = bm.close_contact_connection_spacing_check(
            float(close_contact_check["connection_spacing_mm"]),
            float(close_contact_check["selected_radius_of_gyration_mm"]),
            force_state,
            int(close_contact_check["intermediate_connection_count"]),
        )
        out["clause_7_2_6_close_contact"] = {"status": "evaluated", **check}

    if force_state == "compression":
        if panel_count is None or connector_system is None:
            raise ValueError("compressed built-up member requires panel_count and connector_system")
        method = bm.built_up_stability_method(panel_count, connector_system)
        stability: dict[str, Any] = {"status": "route_selected", "method": method}
        overall_phi: float | None = None
        effective_relative: float | None = None

        if method == "table_8_effective_slenderness":
            if built_up_section_type not in {1, 2, 3} or table8_data is None:
                raise ValueError("Table 8 route requires built_up_section_type 1/2/3 and table8_data")
            routed = dict(table8_data)
            routed.setdefault("total_area_mm2", ag)
            selected = selected_table8_effective_slenderness(int(built_up_section_type), connector_system, routed)
            effective_relative = relative_slenderness(selected["effective_slenderness"], ry, elastic)
            overall_phi = central_compression_stability_coefficient(effective_relative, "b")
            stability.update({
                "table_8_selected_route": selected,
                "effective_relative_slenderness": effective_relative,
                "overall_phi_type_b": overall_phi,
            })
            if connector_system == "battens":
                # 7.2.3: selected branch relative slenderness is one of lambda_b1/b2/b3.
                candidates = [
                    float(v) for k, v in routed.items()
                    if k in {"branch_relative_slenderness", "branch_relative_slenderness_1", "branch_relative_slenderness_2", "branch_relative_slenderness_3"}
                ]
                if branch_relative_slenderness is not None:
                    candidates.append(float(branch_relative_slenderness))
                if not candidates:
                    # Table-8 input names are geometric branch slenderness; normalize the governing one for the 7.2.3 limit.
                    raw_names = [k for k in ("branch_slenderness_1", "branch_slenderness_2", "branch_slenderness_3") if k in routed]
                    if raw_names:
                        candidates = [relative_slenderness(float(routed[k]), ry, elastic) for k in raw_names]
                if not candidates:
                    raise ValueError("batten route requires branch slenderness for the 7.2.3 limit")
                governing_branch = max(candidates)
                branch_check = bm.batten_branch_slenderness_check(governing_branch)
                eq7 = central_compression_stability_utilization(n, ag, ry, gc, overall_phi)
                stability.update({"branch_check": branch_check, "equation_7": {"utilization": eq7, "pass": eq7 <= 1.0}})
            else:
                if branch_relative_slenderness is None or branch_section_type is None:
                    raise ValueError("lattice route requires branch_relative_slenderness and branch_section_type")
                # 7.2.5 is automatically performed when needed; phi1=1 below/equal 2.7 makes it algebraically identical to Eq.7.
                branch_assessment = bm.lattice_branch_slenderness_assessment(
                    float(branch_relative_slenderness), effective_relative, True
                )
                if not branch_assessment["permitted"]:
                    stability.update({"branch_assessment": branch_assessment, "equation_7": None})
                else:
                    lat = bm.lattice_built_up_stability_utilization(
                        n, ag, ry, gc, effective_relative, float(branch_relative_slenderness), branch_section_type
                    )
                    stability.update({"branch_assessment": branch_assessment, "equation_7_with_7_2_5_if_needed": lat})
        elif method == "frame_system_analysis_required":
            stability.update({"status": "external_frame_analysis_required", "equation_7": None})
        else:
            # Fewer than six lattice panels: the current clause explicitly redirects to 7.2.5 but does not provide
            # a Table-8 lambda_ef expression.  Do not invent one.
            stability.update({
                "status": "clause_7_2_5_route_requires_external_effective_member_slenderness",
                "equation_7": None,
                "note": "Table 8 is not applicable for panel_count<6; no lambda_ef is invented by this package.",
            })
        out["clause_7_2_2_to_7_2_5_stability"] = stability

        if connector_force_check is not None:
            if overall_phi is None:
                raise ValueError("connector-force calculation requires a resolved overall phi from the >=6-panel Table 8 route")
            mode = str(connector_force_check["distribution_mode"])
            count = int(connector_force_check["connector_system_count"])
            qfic = bm.fictitious_shear_force_n(n, elastic, ry, overall_phi)
            dist = bm.distribute_fictitious_shear(qfic, mode, count)
            connector_result: dict[str, Any] = {"status": "evaluated", "equation_18_Qfic_n": qfic, "distribution": dist}
            qs = float(dist["per_connector_system_force_n"])
            if connector_system == "battens":
                for k in ("batten_pitch_mm", "branch_axis_spacing_b_mm"):
                    if k not in connector_force_check:
                        raise ValueError(f"batten connector-force route requires {k}")
                connector_result["equation_19_Fs_n"] = bm.batten_shear_force_n(qs, float(connector_force_check["batten_pitch_mm"]), float(connector_force_check["branch_axis_spacing_b_mm"]))
                connector_result["equation_20_Ms_n_mm"] = bm.batten_bending_moment_n_mm(qs, float(connector_force_check["batten_pitch_mm"]))
            else:
                for k in ("diagonal_length_d_mm", "branch_axis_spacing_b_mm", "lattice_force_coefficient_alpha_1"):
                    if k not in connector_force_check:
                        raise ValueError(f"lattice connector-force route requires {k}")
                connector_result["equation_21_Nd_n"] = bm.lattice_diagonal_force_n(
                    qs, float(connector_force_check["diagonal_length_d_mm"]), float(connector_force_check["branch_axis_spacing_b_mm"]), float(connector_force_check["lattice_force_coefficient_alpha_1"])
                )
                if all(k in connector_force_check for k in ("panel_length_mm", "one_branch_force_n", "one_diagonal_area_mm2", "one_branch_area_mm2")):
                    alpha2 = bm.cross_lattice_alpha_2(float(connector_force_check["diagonal_length_d_mm"]), float(connector_force_check["panel_length_mm"]), float(connector_force_check["branch_axis_spacing_b_mm"]))
                    connector_result["equation_22_alpha2"] = alpha2
                    connector_result["equation_22_Nad_n"] = bm.cross_lattice_additional_diagonal_force_n(float(connector_force_check["one_branch_force_n"]), float(connector_force_check["one_diagonal_area_mm2"]), float(connector_force_check["one_branch_area_mm2"]), alpha2)
            connector_result["clause_7_2_10_reduced_length_brace_force_n"] = bm.reduced_length_brace_design_force_n(qfic)
            out["clause_7_2_7_to_7_2_10_connectors"] = connector_result
    else:
        if any(x is not None for x in (panel_count, connector_system, built_up_section_type, table8_data, branch_relative_slenderness, branch_section_type, connector_force_check)):
            raise ValueError("tension built-up workflow must not supply compression stability/connector-system inputs")

    checks = [bool(out["clause_7_2_1_strength"]["pass"])]
    cc = out["clause_7_2_6_close_contact"]
    if cc.get("status") == "evaluated":
        checks.append(bool(cc["pass"]))
    st = out["clause_7_2_2_to_7_2_5_stability"]
    if st.get("equation_7") is not None:
        checks.append(bool(st["equation_7"]["pass"]))
    if st.get("equation_7_with_7_2_5_if_needed") is not None:
        checks.append(bool(st["equation_7_with_7_2_5_if_needed"]["utilization"] <= 1.0))
    out["governing_pass_for_evaluated_checks"] = all(checks)
    return out
