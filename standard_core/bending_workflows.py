"""Branch-safe guided orchestration for SP 16.13330.2017 bending-member checks."""

from __future__ import annotations

import math
from typing import Any

from . import bending_members as bend
from . import crane_runway_and_bending_stability as stab
from . import bending_member_local_stability as bls


def _num(case: dict[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in case:
        raise ValueError(f"bending_member_guided requires {key}")
    value = case[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{key} must be a finite real number")
    result = float(value)
    if positive and result <= 0.0:
        raise ValueError(f"{key} must be greater than zero")
    if nonnegative and result < 0.0:
        raise ValueError(f"{key} must be non-negative")
    return result


def _bool(case: dict[str, Any], key: str) -> bool:
    if key not in case or not isinstance(case[key], bool):
        raise ValueError(f"bending_member_guided requires boolean {key}")
    return bool(case[key])


def _strength_route(case: dict[str, Any]) -> dict[str, Any]:
    member_class = int(case["member_class"])
    load_is_static = _bool(case, "load_is_static")
    beam_category = str(case["beam_category"])
    if beam_category not in {"ordinary", "crane_runway", "bimetal"}:
        raise ValueError("beam_category must be ordinary, crane_runway, or bimetal")
    if beam_category == "crane_runway":
        return {
            "route": "SPECIALIZED_ACTION_REQUIRED",
            "specialized_action": "crane_runway_and_bending_stability",
            "reason": "Clause 8.3 crane-runway route has dedicated inputs and checks.",
        }
    if beam_category == "bimetal":
        return {
            "route": "SPECIALIZED_ACTION_REQUIRED",
            "specialized_action": "bending_member_strength",
            "reason": "Clause 8.2.8 bimetal route remains available in the detailed bending action.",
        }

    class_route = bend.bending_member_class_requirements(member_class, load_is_static, False, False)
    if not class_route["permitted"]:
        raise ValueError(f"Clause 8.1 route is not permitted: {class_route['reason']}")

    mx = _num(case, "moment_x_n_mm", nonnegative=True)
    my = _num(case, "moment_y_n_mm", nonnegative=True)
    bimoment = _num(case, "bimoment_n_mm2", nonnegative=True)
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    rs = _num(case, "design_shear_resistance_n_mm2", positive=True)
    gamma_c = _num(case, "working_condition_factor", positive=True)
    wx = _num(case, "minimum_net_section_modulus_x_mm3", positive=True)
    wy = _num(case, "minimum_net_section_modulus_y_mm3", positive=True)

    result: dict[str, Any] = {"class_route": class_route, "member_class": member_class}

    if member_class == 1:
        if bimoment == 0.0 and (mx == 0.0 or my == 0.0):
            if mx > 0.0:
                utilization = bend.elastic_bending_utilization_eq41(mx, wx, ry, gamma_c)
                result.update({"route": "8.2.1_EQ41_X", "strength_utilization": utilization, "strength_pass": utilization <= 1.0})
            elif my > 0.0:
                utilization = bend.elastic_bending_utilization_eq41(my, wy, ry, gamma_c)
                result.update({"route": "8.2.1_EQ41_Y", "strength_utilization": utilization, "strength_pass": utilization <= 1.0})
            else:
                result.update({"route": "8.2.1_EQ41_ZERO_MOMENT", "strength_utilization": 0.0, "strength_pass": True})
        else:
            required = ["net_inertia_x_mm4", "net_inertia_y_mm4", "net_sectorial_inertia_mm6", "point_y_mm", "point_x_mm", "sectorial_coordinate_mm2"]
            missing = [key for key in required if key not in case]
            if missing:
                raise ValueError(f"Biaxial/bimoment class-1 route requires equation (43) point data: {missing}")
            utilization = bend.elastic_combined_normal_utilization_eq43(
                mx, my, bimoment,
                _num(case, "net_inertia_x_mm4", positive=True),
                _num(case, "net_inertia_y_mm4", positive=True),
                _num(case, "net_sectorial_inertia_mm6", positive=True),
                _num(case, "point_y_mm"), _num(case, "point_x_mm"), _num(case, "sectorial_coordinate_mm2"),
                ry, gamma_c,
            )
            result.update({"route": "8.2.1_EQ43", "strength_utilization": utilization, "strength_pass": utilization <= 1.0})
    else:
        plastic = case.get("plastic")
        if not isinstance(plastic, dict):
            raise ValueError("Class 2/3 guided bending requires a plastic object with explicit applicability data")
        section_family = str(plastic["section_family"]) if "section_family" in plastic else (_ for _ in ()).throw(ValueError("plastic.section_family is required"))
        table_type = str(plastic["table_e1_section_type"]) if "table_e1_section_type" in plastic else (_ for _ in ()).throw(ValueError("plastic.table_e1_section_type is required"))
        eq_load_factor = float(plastic["equivalent_load_safety_factor"]) if "equivalent_load_safety_factor" in plastic else (_ for _ in ()).throw(ValueError("plastic.equivalent_load_safety_factor is required"))
        required_checks = bool(plastic["required_clause_checks_confirmed"]) if "required_clause_checks_confirmed" in plastic else (_ for _ in ()).throw(ValueError("plastic.required_clause_checks_confirmed is required"))
        is_support = bool(plastic["is_support_section"]) if "is_support_section" in plastic else (_ for _ in ()).throw(ValueError("plastic.is_support_section is required"))
        web_area = _num(case, "web_area_mm2", positive=True)
        one_flange_area = _num(case, "one_flange_area_mm2", positive=True)
        qx = _num(case, "shear_force_x_n", nonnegative=True)
        qy = _num(case, "shear_force_y_n", nonnegative=True)
        tau_x = qx / web_area
        tau_y = qy / (2.0 * one_flange_area)
        applicability = bend.plastic_bending_applicability(
            member_class, section_family,
            _num(case, "normative_yield_resistance_n_mm2", positive=True),
            tau_x, rs, required_checks, is_support,
        )
        result["plastic_applicability"] = applicability
        result["shear_stress_x_n_mm2"] = tau_x
        result["shear_stress_y_n_mm2"] = tau_y
        if is_support:
            ux = bend.support_shear_x_utilization_eq54(qx, web_area, rs, gamma_c)
            uy = bend.support_shear_y_utilization_eq55(qy, one_flange_area, rs, gamma_c)
            result.update({
                "route": "8.2.3_SUPPORT_EQ54_EQ55",
                "support_shear_x_utilization": ux,
                "support_shear_y_utilization": uy,
                "strength_utilization": max(ux, uy),
                "strength_pass": max(ux, uy) <= 1.0,
            })
        else:
            if not applicability["permitted"]:
                raise ValueError(f"Clause 8.2.3 plastic route not permitted: {applicability['failed_gates']}")
            if my > 0.0 and tau_y > 0.5 * rs + 1e-12:
                raise ValueError("Equation (51) requires tau_y <= 0.5*Rs")
            e1 = bend.annex_e1_design_coefficients(
                table_type,
                _num(case, "flange_to_web_area_ratio", nonnegative=True),
                my == 0.0,
                eq_load_factor,
            )
            beta = bend.plastic_shear_reduction_factor_eq52(tau_x, rs, _num(case, "flange_to_web_area_ratio", nonnegative=True))
            if bimoment > 0.0:
                if my > 0.0:
                    raise ValueError("Current guided constrained-torsion route supports Mx+B only; use detailed bending action for additional combinations")
                if "minimum_net_sectorial_section_modulus_mm4" not in case:
                    raise ValueError("Equation (53) requires minimum_net_sectorial_section_modulus_mm4")
                ratio = mx / (e1["c_x"] * wx * ry * gamma_c)
                c_omega = bend.constrained_torsion_coefficient_table_10a(ratio)
                utilization = bend.constrained_torsion_utilization_eq53(
                    mx, bimoment, e1["c_x"], beta, wx, c_omega,
                    _num(case, "minimum_net_sectorial_section_modulus_mm4", positive=True), ry, gamma_c,
                )
                route = "8.2.3_EQ53"
            elif my > 0.0:
                utilization = bend.plastic_biaxial_bending_utilization_eq51(mx, my, e1["c_x"], e1["c_y"], beta, wx, wy, ry, gamma_c)
                route = "8.2.3_EQ51"
            else:
                utilization = bend.plastic_bending_utilization_eq50(mx, e1["c_x"], beta, wx, ry, gamma_c)
                route = "8.2.3_EQ50"
            result.update({"route": route, "annex_e1": e1, "beta_eq52": beta, "strength_utilization": utilization, "strength_pass": utilization <= 1.0})

        if member_class == 3:
            confirmations = plastic.get("class_3_confirmations")
            if not isinstance(confirmations, dict):
                raise ValueError("Class 3 guided bending requires class_3_confirmations")
            c3 = bend.class_3_plastic_hinge_route(
                bool(confirmations["clause_8_2_5_confirmed"]) if "clause_8_2_5_confirmed" in confirmations else False,
                bool(confirmations["clause_8_4_6_confirmed"]) if "clause_8_4_6_confirmed" in confirmations else False,
                bool(confirmations["clause_8_5_8_confirmed"]) if "clause_8_5_8_confirmed" in confirmations else False,
                bool(confirmations["clause_8_5_9_confirmed"]) if "clause_8_5_9_confirmed" in confirmations else False,
                bool(confirmations["clause_8_5_18_confirmed"]) if "clause_8_5_18_confirmed" in confirmations else False,
                bool(confirmations["maximum_moment_sections_include_shear_effect"]) if "maximum_moment_sections_include_shear_effect" in confirmations else False,
            )
            result["class_3_route"] = c3
            if not c3["permitted"]:
                raise ValueError(f"Class 3 route missing confirmations: {c3['missing_confirmations']}")

    qx = _num(case, "shear_force_x_n", nonnegative=True)
    if qx > 0.0 and member_class == 1:
        sx = _num(case, "first_moment_area_x_mm3", nonnegative=True)
        ix = _num(case, "inertia_x_mm4", positive=True)
        tw = _num(case, "web_thickness_mm", positive=True)
        u42 = bend.elastic_shear_utilization_eq42(qx, sx, ix, tw, rs, gamma_c)
        if _bool(case, "web_has_bolt_holes"):
            u42 = bend.apply_bolt_hole_factor(u42, bend.bolt_hole_factor_eq45(_num(case, "hole_pitch_mm", positive=True), _num(case, "hole_diameter_mm", nonnegative=True)))
        result["shear_route"] = "8.2.1_EQ42"
        result["shear_utilization"] = u42
        result["shear_pass"] = u42 <= 1.0
    else:
        result["shear_route"] = "included_in_plastic_route" if member_class in (2, 3) else "not_requested"

    concentrated = case.get("concentrated_load")
    if concentrated is not None:
        if not isinstance(concentrated, dict):
            raise ValueError("concentrated_load must be an object")
        force = float(concentrated["force_n"]) if "force_n" in concentrated else (_ for _ in ()).throw(ValueError("concentrated_load.force_n is required"))
        if force < 0.0:
            raise ValueError("concentrated_load.force_n must be non-negative")
        if force > 0.0:
            mode = str(concentrated["figure_6_case"]) if "figure_6_case" in concentrated else (_ for _ in ()).throw(ValueError("concentrated_load.figure_6_case is required when force_n > 0"))
            if mode == "welded_or_rolled":
                le = bend.effective_load_length_eq48(float(concentrated["bearing_width_mm"]), float(concentrated["flange_and_weld_or_fillet_height_mm"]))
            elif mode == "crane_wheel":
                le = bend.effective_load_length_crane_eq49(float(concentrated["distribution_coefficient_psi"]), float(concentrated["flange_and_rail_inertia_mm4"]), _num(case, "web_thickness_mm", positive=True))
            else:
                raise ValueError("concentrated_load.figure_6_case must be welded_or_rolled or crane_wheel")
            sloc = bend.local_web_compression_stress_eq47(force, le, _num(case, "web_thickness_mm", positive=True))
            uloc = bend.local_web_compression_utilization_eq46(sloc, ry, gamma_c)
            result["concentrated_load"] = {"effective_length_mm": le, "sigma_loc_n_mm2": sloc, "utilization_eq46": uloc, "pass": uloc <= 1.0}
    return result


def _lateral_stability_route(case: dict[str, Any]) -> dict[str, Any]:
    cfg = case.get("lateral_stability")
    if not isinstance(cfg, dict):
        raise ValueError("bending_member_guided requires lateral_stability object")
    mode = str(cfg["mode"]) if "mode" in cfg else (_ for _ in ()).throw(ValueError("mode is required"))
    if mode == "not_assessed":
        return {"mode": mode, "status": "SEPARATE_ASSESSMENT_REQUIRED", "pass": None}
    if mode == "rigid_deck_exemption":
        exemption = stab.lateral_stability_check_exemption(True, 0.0, 0.0, 1.0)
        return {"mode": mode, "exemption": exemption, "pass": True}
    if mode == "table_11_exemption":
        lef = float(cfg["effective_length_mm"])
        b = _num(case, "flange_width_mm", positive=True)
        tf = _num(case, "flange_thickness_mm", positive=True)
        h_axes = _num(case, "flange_axis_spacing_mm", positive=True)
        ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
        e = _num(case, "elastic_modulus_n_mm2", positive=True)
        actual = stab.compressed_flange_relative_slenderness(lef, b, ry, e)
        sigma = cfg.get("compressed_flange_stress_n_mm2")
        limit = stab.table_11_limit(
            str(cfg["load_position"]), b, tf, h_axes,
            bool(cfg["friction_flange_connections"]) if "friction_flange_connections" in cfg else False,
            ry if sigma is not None else None,
            float(sigma) if sigma is not None else None,
        )
        exemption = stab.lateral_stability_check_exemption(False, actual, limit, float(cfg["tension_to_compression_flange_width_ratio"]) if "tension_to_compression_flange_width_ratio" in cfg else 1.0)
        return {"mode": mode, "effective_length_mm": lef, "lambda_b": actual, "lambda_b_limit": limit, "exemption": exemption, "pass": bool(exemption["exempt"])}
    if mode == "calculate_phi_b":
        if not _bool(case, "rolled_i_section_confirmed"):
            raise ValueError("calculate_phi_b guided route currently requires a doubly symmetric rolled I profile")
        if _num(case, "moment_y_n_mm", nonnegative=True) != 0.0 or _num(case, "bimoment_n_mm2", nonnegative=True) != 0.0:
            raise ValueError("Guided calculate_phi_b route uses equation (69); use detailed stability action for equation (70)")
        lef = float(cfg["effective_length_mm"])
        it = _num(case, "torsional_inertia_mm4", positive=True)
        iy = _num(case, "inertia_y_mm4", positive=True)
        ix = _num(case, "inertia_x_mm4", positive=True)
        h = _num(case, "section_height_mm", positive=True)
        e = _num(case, "elastic_modulus_n_mm2", positive=True)
        ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
        alpha = stab.annex_zh_alpha_rolled_eq_zh4(it, iy, lef, h, bool(cfg["compression_flange_braced_in_span"]))
        table_name = str(cfg["annex_zh_table"]) if "annex_zh_table" in cfg else (_ for _ in ()).throw(ValueError("lateral_stability.annex_zh_table is required"))
        if table_name == "zh1":
            psi = stab.annex_zh_table_1_psi(str(cfg["case_id"]), alpha, cfg["load_flange"] if "load_flange" in cfg else None)
        elif table_name == "zh2":
            psi = stab.annex_zh_table_2_psi(str(cfg["case_id"]), str(cfg["load_flange"]), alpha)
        else:
            raise ValueError("annex_zh_table must be zh1 or zh2")
        phis = stab.annex_zh_symmetric_i_phi_b(psi, iy, ix, h, lef, e, ry)
        util = stab.lateral_torsional_stability_utilization_eq69(
            _num(case, "moment_x_n_mm", nonnegative=True), phis["phi_b"],
            _num(case, "compressed_section_modulus_x_mm3", positive=True), ry,
            _num(case, "working_condition_factor", positive=True),
        )
        return {"mode": mode, "effective_length_mm": lef, "alpha_eq_zh4": alpha, "psi": psi, **phis, "utilization_eq69": util, "pass": util <= 1.0}
    raise ValueError("Unsupported lateral_stability.mode")


def _local_stability_route(case: dict[str, Any]) -> dict[str, Any]:
    cfg = case.get("local_stability")
    if not isinstance(cfg, dict):
        raise ValueError("bending_member_guided requires local_stability object")
    mode = str(cfg["mode"]) if "mode" in cfg else (_ for _ in ()).throw(ValueError("mode is required"))
    if mode == "not_assessed":
        return {"mode": mode, "status": "SEPARATE_ASSESSMENT_REQUIRED", "pass": None}
    if mode != "geometry_and_stiffener_screen":
        raise ValueError("local_stability.mode must be not_assessed or geometry_and_stiffener_screen")
    hef = _num(case, "effective_web_height_mm", positive=True)
    tw = _num(case, "web_thickness_mm", positive=True)
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    e = _num(case, "elastic_modulus_n_mm2", positive=True)
    lambda_w = hef / tw * math.sqrt(ry / e)
    member_class = int(case["member_class"])
    moving = bool(cfg["moving_flange_load_present"]) if "moving_flange_load_present" in cfg else False
    plastic_region = bool(cfg["plastic_deformation_region"]) if "plastic_deformation_region" in cfg else (member_class in (2, 3))
    stiff = bls.transverse_stiffener_requirements_8_5_9(member_class, lambda_w, moving, plastic_region, hef, bool(cfg["class_1_extended_spacing_conditions_met"]) if "class_1_extended_spacing_conditions_met" in cfg else False)
    preliminary = None
    if member_class == 1:
        preliminary = bls.preliminary_web_check_exemption_8_5_1(lambda_w, bool(cfg["local_stress_present"]) if "local_stress_present" in cfg else False, bool(cfg["double_sided_flange_welds"]) if "double_sided_flange_welds" in cfg else True)
    return {
        "mode": mode,
        "web_relative_slenderness": lambda_w,
        "preliminary_8_5_1": preliminary,
        "transverse_stiffener_requirements_8_5_9": stiff,
        "status": "SCREEN_ONLY_FULL_8_5_INTERACTION_REMAINS_SEPARATE",
        "pass": None,
    }


def bending_member_guided_workflow(case: dict[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute the Stage N4 applicability-safe guided bending-member workflow without evaluating inapplicable Section 8 branches.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.1-8.5
        Annex: Е and Ж
        Equation/Table: Equations (41)-(100), Tables 10a-19, Annex Ж as routed by the selected case
        Audit ID: SP16-N4-GUIDED-BENDING-WORKFLOW
        Normative status: normative orchestration of already implemented atomic checks

    Mathematical form:
        Explicit member/load/applicability state -> one applicable strength branch -> explicit lateral-stability route -> explicit local-stability route.

    Parameters:
        case:
            Type: dict[str, Any]
            Unit: mixed named engineering units
            Meaning: Schema-validated and reference-hydrated Stage N4 case.
            Valid range: See schemas/bending_member_guided_case.schema.json and conditional checks in this function.
            Source: user input plus explicit N1/N2 reference hydration.

    Returns:
        Type: dict[str, Any]
        Unit: mixed results
        Meaning: Branch trace, utilization results, stability results and explicit unresolved/separate-assessment statuses.

    Assumptions:
        - N1 material and N2 profile references have been explicitly selected or equivalent scalar inputs have been supplied.
        - Applicability confirmations supplied by the user/analysis model are truthful.

    Sign convention:
        - Guided strength moments and shear forces are non-negative magnitudes; detailed point-sign equation (43) data remain explicit when required.

    Unit convention:
        - Forces N, moments N*mm, lengths mm, section properties in mm powers, stresses N/mm2.

    Applicability:
        - Ordinary homogeneous bending members; crane-runway and bimetal branches are routed to their existing dedicated detailed actions.

    Limitations:
        - The local-stability screen does not replace the full equation (80)-(100) detailed action.
        - The guided phi_b calculation currently automates the common doubly symmetric rolled-I equation (69) route; equation (70), monosymmetric and channel routes remain available in the low-level/detailed stability action.
        - Load derivation and restraint adequacy are external structural-analysis inputs.

    Raises:
        ValueError: Required conditional data are missing or a requested normative branch is not applicable.
        TypeError: case is not a dictionary.

    Examples:
        >>> isinstance(bending_member_guided_workflow({"member_class": 1}), dict)
        False

    Tests:
        Unit tests:
            - tests/test_stage_n4_bending_workflows.py
        Validation cases:
            - N4-GUIDED-BEAM-001

    Implementation notes:
        - This orchestration layer intentionally does not belong to the frozen low-level engineering API registry; it composes existing audited functions.
        - Fail-closed routing is preferred over silently calculating unrelated equations.
    """
    if not isinstance(case, dict):
        raise TypeError("case must be a dictionary")
    strength = _strength_route(case)
    if strength.get("route") == "SPECIALIZED_ACTION_REQUIRED":
        return {"strength": strength, "lateral_stability": {"status": "NOT_EVALUATED"}, "local_stability": {"status": "NOT_EVALUATED"}, "governing_utilization": None, "pass": None}
    lateral = _lateral_stability_route(case)
    local = _local_stability_route(case)
    utilisations = [float(strength["strength_utilization"])]
    if "shear_utilization" in strength:
        utilisations.append(float(strength["shear_utilization"]))
    if isinstance(strength.get("concentrated_load"), dict):
        utilisations.append(float(strength["concentrated_load"]["utilization_eq46"]))
    if "utilization_eq69" in lateral:
        utilisations.append(float(lateral["utilization_eq69"]))
    governing = max(utilisations) if utilisations else None
    pass_flag = governing <= 1.0 if governing is not None else None
    return {
        "strength": strength,
        "lateral_stability": lateral,
        "local_stability": local,
        "governing_utilization": governing,
        "pass": pass_flag,
        "trace_policy": "FIRST_APPLICABLE_BRANCH_ONLY",
    }
