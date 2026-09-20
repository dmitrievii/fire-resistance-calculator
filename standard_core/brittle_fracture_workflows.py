"""Stage N10 applicability-safe orchestration for current SP16 Section 13 brittle-fracture prevention."""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import brittle_fracture_and_welded_connections as s13

CURRENT_SP16_SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def _num(m: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in m:
        raise ValueError(f"brittle_fracture_guided requires {key}")
    value = m[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{key} must be a finite real number")
    if positive and result <= 0.0:
        raise ValueError(f"{key} must be greater than zero")
    if nonnegative and result < 0.0:
        raise ValueError(f"{key} must be non-negative")
    return result


def _bool(m: Mapping[str, Any], key: str) -> bool:
    if key not in m or not isinstance(m[key], bool):
        raise ValueError(f"{key} must be boolean")
    return bool(m[key])


def _text(m: Mapping[str, Any], key: str) -> str:
    if key not in m or not isinstance(m[key], str) or not m[key].strip():
        raise ValueError(f"{key} must be a non-empty string")
    return str(m[key]).strip()


def _optional_bool(m: Mapping[str, Any], key: str) -> bool | None:
    if key not in m:
        return None
    if not isinstance(m[key], bool):
        raise ValueError(f"{key} must be boolean when supplied")
    return bool(m[key])


def _general_prevention(route: Mapping[str, Any]) -> dict[str, Any]:
    ry = _num(route, "design_yield_resistance_n_mm2", positive=True)
    welded = _bool(route, "welded_structure")
    checks: dict[str, dict[str, Any]] = {}
    checks["steel_selection_5_2_table_v1"] = {
        "applicable": True,
        "confirmed": _bool(route, "steel_selection_5_2_table_v1_confirmed"),
    }
    checks["stress_concentration_and_work_hardening_reduction"] = {
        "applicable": True,
        "confirmed": _bool(route, "stress_concentration_and_work_hardening_reduction_confirmed"),
    }
    checks["solid_web_vs_lattice_concentration_considered"] = {
        "applicable": True,
        "confirmed": _bool(route, "solid_web_vs_lattice_concentration_considered"),
    }

    if welded:
        sigma_t = _num(route, "weld_zone_tensile_stress_n_mm2", nonnegative=True)
        threshold = 0.4 * ry
        enhanced_required = sigma_t > threshold
        enhanced_ndt = _optional_bool(route, "enhanced_ndt_for_welds_above_0_4_ry_confirmed")
        if enhanced_required and enhanced_ndt is None:
            raise ValueError("enhanced_ndt_for_welds_above_0_4_ry_confirmed is required when weld tensile stress exceeds 0.4Ry")
        checks["enhanced_ndt_above_0_4_ry"] = {
            "applicable": enhanced_required,
            "stress_n_mm2": sigma_t,
            "threshold_n_mm2": threshold,
            "confirmed": True if not enhanced_required else bool(enhanced_ndt),
        }
        checks["weld_intersections_avoided"] = {
            "applicable": True,
            "confirmed": _bool(route, "weld_intersections_avoided_confirmed"),
        }
        checks["runoff_tabs_and_weld_ndt"] = {
            "applicable": True,
            "confirmed": _bool(route, "runoff_tabs_and_weld_ndt_confirmed"),
        }
    else:
        checks["enhanced_ndt_above_0_4_ry"] = {"applicable": False, "confirmed": True}
        checks["weld_intersections_avoided"] = {"applicable": False, "confirmed": True}
        checks["runoff_tabs_and_weld_ndt"] = {"applicable": False, "confirmed": True}

    cover = _bool(route, "cover_plate_splice_with_flank_welds")
    if cover:
        d = _num(route, "flank_weld_termination_distance_each_side_mm", nonnegative=True)
        checks["flank_weld_termination_25_mm_each_side"] = {
            "applicable": True,
            "provided_mm": d,
            "minimum_mm": 25.0,
            "confirmed": d >= 25.0,
        }
    else:
        checks["flank_weld_termination_25_mm_each_side"] = {"applicable": False, "confirmed": True}

    cutting = _bool(route, "guillotine_cutting_or_punched_holes")
    if cutting:
        checks["minimum_section_thickness_for_guillotine_or_punching"] = {
            "applicable": True,
            "confirmed": _bool(route, "minimum_section_thickness_used_confirmed"),
        }
    else:
        checks["minimum_section_thickness_for_guillotine_or_punching"] = {"applicable": False, "confirmed": True}

    gusset = _bool(route, "secondary_gusset_to_tension_member")
    if gusset:
        checks["secondary_gusset_bolted_to_tension_member"] = {
            "applicable": True,
            "confirmed": _bool(route, "bolted_secondary_gusset_attachment_confirmed"),
        }
    else:
        checks["secondary_gusset_bolted_to_tension_member"] = {"applicable": False, "confirmed": True}

    failed = sorted(key for key, item in checks.items() if bool(item["applicable"]) and not bool(item["confirmed"]))
    return {
        "clause_13_1_factor_register": s13.brittle_fracture_factor_register_clause_13_1(),
        "clause_13_2_checks": checks,
        "failed_requirements": failed,
        "pass": not failed,
    }


def _lamellar_route(route: Mapping[str, Any]) -> dict[str, Any] | None:
    grade = _num(route, "steel_grade_number", positive=True)
    thickness = _num(route, "plate_thickness_mm", positive=True)
    joint = _text(route, "joint_type")
    tension = _bool(route, "through_thickness_tension")
    screen = s13.lamellar_tearing_applicability_clause_13_3(grade, thickness, joint, tension)
    review_confirmed = _bool(route, "clause_13_3_engineering_review_confirmed")
    if not review_confirmed:
        raise ValueError("clause_13_3_engineering_review_confirmed must be true before Section 13.3 routing")
    required = _bool(route, "lamellar_tearing_assessment_required")
    if bool(screen["risk_assessment_required"]) and not required:
        raise ValueError("lamellar_tearing_assessment_required cannot be false when the conservative clause-13.3 screen is true")
    if not required:
        return {
            "required": False,
            "clause_13_3_screen": screen,
            "status": "NOT_APPLICABLE_BY_CONFIRMED_ENGINEERING_REVIEW",
        }

    evidence = s13.through_thickness_property_test_route_clause_13_4(
        _bool(route, "through_thickness_test_evidence_available")
    )
    if not bool(evidence["test_result_available"]):
        return {
            "required": True,
            "clause_13_3_screen": screen,
            "clause_13_4_test_evidence": evidence,
            "status": "INCOMPLETE_FAIL_CLOSED",
            "required_evidence": "verified through-thickness tensile-test / certified Z-quality evidence",
        }
    if not _bool(route, "selected_z_quality_certificate_confirmed"):
        return {
            "required": True,
            "clause_13_3_screen": screen,
            "clause_13_4_test_evidence": evidence,
            "status": "INCOMPLETE_FAIL_CLOSED",
            "required_evidence": "selected Z-quality group certificate for the actual rolled product",
        }

    psi_zf = s13.table_37_connection_form_factor(_text(route, "connection_form_case"))
    psi_zt = s13.table_37_plate_thickness_factor(thickness)
    psi_zsh = s13.table_37_weld_leg_factor(_num(route, "risk_weld_leg_mm", nonnegative=True))
    psi_zj = s13.table_37_restraint_factor(_text(route, "restraint_level"))
    psi_zs = s13.table_37_welding_technology_factor(
        _text(route, "pass_count"), _text(route, "weld_sequence"), _text(route, "preheat")
    )
    base = s13.lamellar_tearing_risk_sum_eq174(psi_zf, psi_zt, psi_zsh, psi_zj, psi_zs)
    adjusted = s13.lamellar_tearing_adjusted_risk_clause_13_5(base, _text(route, "through_thickness_action"))
    required_group = s13.required_z_quality_group_clause_13_5(
        int(_num(route, "construction_group", positive=True)),
        _text(route, "consequence_class"),
        _bool(route, "flange_connection_15_9_10_or_force_normal_to_plate"),
    )
    selected_group = _text(route, "selected_z_quality_group")
    ranks = {"Z15": 15, "Z25": 25, "Z35": 35}
    if selected_group not in ranks:
        raise ValueError("selected_z_quality_group must be Z15, Z25, or Z35")
    quality_sufficient = ranks[selected_group] >= ranks[required_group]
    check = s13.lamellar_tearing_check_clause_13_5(adjusted, selected_group)
    passed = quality_sufficient and bool(check["pass"])
    return {
        "required": True,
        "status": "COMPLETE",
        "clause_13_3_screen": screen,
        "clause_13_4_test_evidence": evidence,
        "table_37_factors_percent": {
            "psi_zf": psi_zf,
            "psi_zt": psi_zt,
            "psi_zsh": psi_zsh,
            "psi_zj": psi_zj,
            "psi_zs": psi_zs,
        },
        "equation_174_base_risk_percent": base,
        "adjusted_risk_percent": adjusted,
        "required_z_quality_group": required_group,
        "selected_z_quality_group": selected_group,
        "selected_quality_meets_minimum_group": quality_sufficient,
        "risk_check": check,
        "governing_utilization": max(float(check["utilization"]), ranks[required_group] / ranks[selected_group]),
        "pass": passed,
    }


def brittle_fracture_guided_workflow(case: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Evaluate current-SP16 Section 13 brittle-fracture prevention and, when applicable, the lamellar-tearing risk route with explicit evidence gates.
    Standard reference:
        СП 16.13330.2017, Changes No. 1-6 through 09.12.2024, clauses 13.1-13.5, equation (174), Table 37.
    Parameters:
        case is a validated brittle_fracture_guided mapping with one route object containing explicit project confirmations and, when required, Table-37/Z-quality inputs.
    Returns:
        Auditable Section-13 result with clause-13.2 checks, clause-13.3 applicability evidence, equation-(174) factors, Z-quality adequacy, status and pass/fail.
    Assumptions:
        Engineering classification of the welded detail and product certificate/test evidence are supplied explicitly; no drawing recognition or material-certificate inference is performed.
    Sign convention:
        Table-37 beneficial factors may be negative; risk modifiers act algebraically on the equation-(174) sum.
    Unit convention:
        Stresses are N/mm2, dimensions are mm, Table-37 risk factors are percent points, and utilizations are dimensionless.
    Applicability:
        Section 13 brittle-fracture prevention for steel structures and lamellar-tearing assessment of rolled products in welded details under clauses 13.3-13.5.
    Limitations:
        Does not certify steel selection under Annex V/product standards, interpret NDT records, recognize connection geometry automatically, or resolve project-specific ambiguity without explicit engineering review.
    Raises:
        ValueError for missing, inconsistent, non-finite or unsupported inputs and for attempts to suppress a positive conservative 13.3 screen.
    Examples:
        See examples/brittle_fracture_guided_example.json.
    Tests:
        tests/test_stage_n10_brittle_fracture_workflows.py and tests/test_brittle_fracture_and_welded_connections.py.
    Implementation notes:
        Clause 13.2 is not a partial checklist: every applicable current requirement represented by the workflow must be explicit. Table 37 uses only printed factors; selected Z quality must satisfy both the minimum group route and psi_zr <= psi_zn.
    """
    if not isinstance(case, Mapping):
        raise ValueError("brittle_fracture_guided case must be an object")
    if "route" not in case or not isinstance(case["route"], Mapping):
        raise ValueError("brittle_fracture_guided requires route object")
    route = case["route"]
    if _text(route, "kind") != "section13_full_review":
        raise ValueError("Unsupported Stage N10 brittle-fracture route")
    general = _general_prevention(route)
    lamellar = _lamellar_route(route)
    if lamellar is not None and lamellar["status"] == "INCOMPLETE_FAIL_CLOSED":
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "section13_full_review",
            "general_prevention": general,
            "lamellar_tearing": lamellar,
            "governing_utilization": None,
        }
    lamellar_pass = True if lamellar is None or not bool(lamellar["required"]) else bool(lamellar["pass"])
    governing = None if lamellar is None or not bool(lamellar["required"]) else float(lamellar["governing_utilization"])
    return {
        "status": "COMPLETE",
        "route": "section13_full_review",
        "general_prevention": general,
        "lamellar_tearing": lamellar,
        "governing_utilization": governing,
        "pass": bool(general["pass"]) and lamellar_pass,
    }
