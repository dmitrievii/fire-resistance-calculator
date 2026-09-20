"""Applicability-safe guided orchestration for SP 16.13330.2017 Section 9 beam-columns."""
from __future__ import annotations

import math
from typing import Any

from . import axial_members as axial
from . import beam_column_stability as bc
from . import base_plates_and_combined_force_strength as strength


def _number(case: dict[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in case:
        raise ValueError(f"beam_column_guided requires {key}")
    value = case[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{key} must be a finite real number")
    value = float(value)
    if positive and value <= 0:
        raise ValueError(f"{key} must be greater than zero")
    if nonnegative and value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def _resolve_phi_e(
    axis: str,
    lambda_bar: float,
    m: float,
    central_phi: float,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Resolve eta/meff and D.3 with explicit in-domain bilinear interpolation and no extrapolation."""
    if m == 0.0:
        return {
            "status": "CENTRAL_COMPRESSION_LIMITING_CASE",
            "eta": None,
            "m_eff": 0.0,
            "phi_e": central_phi,
            "source": "clause_7.1.3_limit_M_equals_0",
        }
    if m > 20.0:
        return {
            "status": "SECTION_8_REQUIRED_M_GT_20",
            "eta": None,
            "m_eff": None,
            "phi_e": None,
            "source": "clause_9.2.2_fail_closed_before_D2",
        }
    if m < 0.1:
        return {
            "status": "UNRESOLVED_M_BELOW_D2_SUPPORTED_DOMAIN",
            "eta": None,
            "m_eff": None,
            "phi_e": None,
            "source": "no_hidden_extrapolation",
        }

    section_type = str(case[f"annex_d2_section_type_{axis}"])
    ratio = case.get(f"annex_d2_flange_to_web_area_ratio_{axis}")
    offset = case.get(f"annex_d2_offset_ratio_a1_to_h_{axis}")
    eta = bc.annex_d2_shape_influence_coefficient(
        section_type,
        lambda_bar,
        m,
        None if ratio is None else float(ratio),
        None if offset is None else float(offset),
    )
    m_eff = bc.effective_relative_eccentricity_eq110(eta, m)
    if m_eff > 20.0:
        return {
            "status": "SECTION_8_REQUIRED_MEFF_GT_20",
            "eta": eta,
            "m_eff": m_eff,
            "phi_e": None,
            "source": "clause_9.2.2",
        }

    try:
        raw_exact = bc.annex_d3_table_coefficient(lambda_bar, m_eff)
        phi_e = min(raw_exact, central_phi)
        return {
            "status": "D3_EXACT_NODE",
            "eta": eta,
            "m_eff": m_eff,
            "phi_e": phi_e,
            "source": "table_D.3_exact_printed_node",
        }
    except ValueError as exact_exc:
        try:
            phi_e = bc.annex_d3_stability_coefficient(lambda_bar, m_eff, central_phi)
            return {
                "status": "D3_BILINEAR_INTERPOLATED",
                "eta": eta,
                "m_eff": m_eff,
                "phi_e": phi_e,
                "source": "table_D.3_bilinear_digital_policy_no_extrapolation",
                "exact_lookup_error": str(exact_exc),
            }
        except ValueError as interpolation_exc:
            external = case["stability"].get(f"external_phi_e_{axis}")
            if isinstance(external, dict):
                value = float(external["value"])
                basis = str(external["basis"]).strip()
                if not basis:
                    raise ValueError(f"stability.external_phi_e_{axis}.basis must be non-empty")
                if not 0.0 < value <= central_phi + 1e-12:
                    raise ValueError(f"external phi_e_{axis} must satisfy 0 < phi_e <= central compression phi")
                return {
                    "status": "EXTERNAL_D3_COEFFICIENT_USED",
                    "eta": eta,
                    "m_eff": m_eff,
                    "phi_e": min(value, central_phi),
                    "source": basis,
                    "exact_lookup_error": str(exact_exc),
                    "interpolation_error": str(interpolation_exc),
                }
            return {
                "status": "EXTERNAL_D3_COEFFICIENT_REQUIRED",
                "eta": eta,
                "m_eff": m_eff,
                "phi_e": None,
                "source": "table_D.3_outside_printed_domain_no_extrapolation",
                "exact_lookup_error": str(exact_exc),
                "interpolation_error": str(interpolation_exc),
            }


def _coefficient_c(case: dict[str, Any], mx: float, lambda_bar_y: float, phi_y: float) -> dict[str, Any]:
    table_type = str(case["table_21_section_type"])
    ratio = case.get("table_21_smaller_to_larger_flange_inertia_ratio")
    ratio_f = None if ratio is None else float(ratio)
    # Table 21 alpha is only used by eq. (112), including the m=5 endpoint for interpolation.
    alpha = bc.table_21_alpha(table_type, min(mx, 5.0), ratio_f)
    phi_at_314 = axial.central_compression_stability_coefficient(3.14, str(case["table7_section_type_y"]))
    beta = bc.table_21_beta(table_type, lambda_bar_y, phi_y, phi_at_314, ratio_f)
    stability = case["stability"]
    if mx > 5.0:
        if "bending_stability_phi_b" not in stability:
            return {"status": "BENDING_PHI_B_REQUIRED_FOR_C", "c": None, "alpha": alpha, "beta": beta}
        phi_b = float(stability["bending_stability_phi_b"])
    else:
        phi_b = 1.0  # not used by equation (112)
    if lambda_bar_y > 3.14:
        if "annex_d_c_max" not in stability:
            return {"status": "ANNEX_D_C_MAX_REQUIRED", "c": None, "alpha": alpha, "beta": beta}
        cmax = float(stability["annex_d_c_max"])
    else:
        cmax = 1.0
    routed = bc.out_of_plane_coefficient_c(mx, alpha, beta, phi_y, phi_b, cmax)
    return {"status": "RESOLVED", "alpha": alpha, "beta": beta, "phi_at_3_14": phi_at_314, **routed}


def _strength(case: dict[str, Any]) -> dict[str, Any]:
    cfg = case["strength"]
    n = _number(case, "axial_force_n", positive=True)
    an = _number(case, "net_area_mm2", positive=True)
    ry = _number(case, "design_yield_resistance_n_mm2", positive=True)
    rs = _number(case, "design_shear_resistance_n_mm2", positive=True)
    ryn = _number(case, "normative_yield_resistance_n_mm2", positive=True)
    gamma_c = _number(case, "working_condition_factor", positive=True)
    tau = float(cfg["shear_stress_n_mm2"])
    high_strength_route = strength.equation_107_applicability(
        ryn, bool(cfg["section_is_asymmetric_about_axis_perpendicular_to_bending_plane"])
    )
    if high_strength_route["permitted"]:
        return {
            "route": "9.1.3_EQ107_DETAILED_ACTION_REQUIRED",
            "equation_107_applicability": high_strength_route,
            "status": "HIGH_STRENGTH_ASYMMETRIC_TENSION_FIBER_DATA_REQUIRED",
            "utilization": None,
            "pass": None,
        }

    applicability = strength.equation_105_applicability(
        ryn,
        bool(cfg["direct_dynamic_load"]),
        tau,
        rs,
        n,
        an,
        ry,
        bool(cfg["clause_8_5_8_confirmed"]),
        bool(cfg["clause_8_5_18_confirmed"]),
    )
    mode = str(cfg["method"])
    use_105 = mode == "auto" and applicability["permitted"]
    mx = abs(_number(case, "moment_x_n_mm"))
    my = abs(_number(case, "moment_y_n_mm"))
    bim = abs(_number(case, "bimoment_n_mm2"))
    if use_105:
        coeff = strength.combined_force_coefficients_from_annex_e1(
            str(cfg["annex_e1_section_type"]),
            float(cfg["annex_e1_flange_to_web_area_ratio"]),
            my > 0.0,
        )
        util = strength.combined_force_strength_utilization_eq105(
            n, an, mx, my, bim,
            coeff["n"], coeff["c_x"], coeff["c_y"],
            _number(case, "minimum_net_section_modulus_x_mm3", positive=True),
            _number(case, "minimum_net_section_modulus_y_mm3", positive=True),
            _number(case, "minimum_net_sectorial_section_modulus_mm4", positive=True),
            ry, gamma_c,
        )
        return {"route": "9.1.1_EQ105", "applicability_eq105": applicability, "annex_e1": coeff, "utilization": util, "pass": util <= 1.0}

    points = cfg.get("eq106_points")
    if not isinstance(points, list) or not points:
        return {
            "route": "9.1.1_EQ106_REQUIRED",
            "applicability_eq105": applicability,
            "status": "EQ106_POINT_DATA_REQUIRED",
            "utilization": None,
            "pass": None,
        }
    utils = []
    for p in points:
        utils.append(strength.combined_force_point_utilization_eq106(
            n, an,
            _number(case, "moment_x_n_mm"), float(p["point_y_mm"]), _number(case, "net_inertia_x_mm4", positive=True),
            _number(case, "moment_y_n_mm"), float(p["point_x_mm"]), _number(case, "net_inertia_y_mm4", positive=True),
            _number(case, "bimoment_n_mm2"), float(p["sectorial_coordinate_mm2"]), float(p["net_sectorial_inertia_mm6"]),
            ry, gamma_c,
        ))
    util = max(utils)
    return {"route": "9.1.1_EQ106", "applicability_eq105": applicability, "point_utilizations": utils, "utilization": util, "pass": util <= 1.0}


def beam_column_guided_workflow(case: dict[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Compose applicability-safe current-SP16 Section 9 beam-column strength and stability checks.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; clauses 9.1.1-9.2.10 and Annex D.

    Parameters:
        case: Strictly validated Stage N5 input mapping after explicit N1 material and N2 profile hydration.

    Returns:
        A trace dictionary containing derived slenderness/eccentricity values, selected normative branches, utilizations, unresolved requirements, and pass state.

    Assumptions:
        N and M belong to one load combination; section classification and geometric applicability flags supplied by the caller are truthful.

    Sign convention:
        Positive axial_force_n denotes compression; signed moments are retained for strength equation (106), while stability eccentricities use moment magnitudes.

    Unit convention:
        Forces N, moments N*mm, lengths mm, section properties in mm powers, stresses N/mm2.

    Applicability:
        Qualified guided route covers solid open sections in the declared 9.1/9.2 scope; box and built-up routes are handed to retained detailed actions.

    Limitations:
        Global frame analysis, effective-length derivation, arbitrary geometry classification, governing-point search for equation (106), and an unstated general interpolation rule for Table D.3 are not inferred.

    Raises:
        ValueError when required branch data are absent, inconsistent, or outside an encoded normative domain; TypeError when case is not a mapping.

    Examples:
        Use examples/beam_column_guided_example.json through standard_core.runner.run_case.

    Tests:
        tests/test_stage_n5_beam_column_workflows.py and tests/test_stage_n5_dag.py.

    Implementation notes:
        The workflow composes frozen audited Section 9 primitives. Table D.3 preserves exact printed nodes and uses the audited in-domain bilinear digital-table policy for intermediate lambda_bar/m_eff values; extrapolation remains forbidden and external phi_e is accepted only as an explicit out-of-domain provenance route.
    """
    if not isinstance(case, dict):
        raise TypeError("case must be a dictionary")
    if not bool(case["same_load_combination_confirmed"]):
        raise ValueError("Clause 9.2.3 requires N and M from the same load combination")
    if not bool(case["section_classification_confirmed"]):
        raise ValueError("Section classification must be explicitly confirmed")
    form = str(case["member_form"])
    if form == "built_up":
        return {
            "status": "SPECIALIZED_ACTION_REQUIRED",
            "specialized_action": "built_up_beam_columns_and_combined_local_stability",
            "reason": "Stage N5 guided solid-section route does not duplicate clauses 9.3-9.4.",
            "governing_utilization": None,
            "pass": None,
        }
    if form == "solid_box":
        return {
            "status": "SPECIALIZED_ACTION_REQUIRED",
            "specialized_action": "beam_column_stability",
            "reason": "Clause 9.2.10 box-section route remains in the detailed Section 9 action.",
            "governing_utilization": None,
            "pass": None,
        }
    if not bool(case["major_stiffness_plane_coincides_with_symmetry_plane"]):
        return {
            "status": "DETAILED_ACTION_REQUIRED",
            "specialized_action": "beam_column_stability",
            "reason": "Guided route is qualified for Ix>Iy with the major-stiffness plane coincident with symmetry plane.",
            "governing_utilization": None,
            "pass": None,
        }

    n = _number(case, "axial_force_n", positive=True)
    area = _number(case, "gross_area_mm2", positive=True)
    ry = _number(case, "design_yield_resistance_n_mm2", positive=True)
    e_mod = _number(case, "elastic_modulus_n_mm2", positive=True)
    gamma_c = _number(case, "working_condition_factor", positive=True)
    lx = _number(case, "effective_length_x_mm", positive=True) / _number(case, "radius_x_mm", positive=True)
    ly = _number(case, "effective_length_y_mm", positive=True) / _number(case, "radius_y_mm", positive=True)
    lbx = axial.relative_slenderness(lx, ry, e_mod)
    lby = axial.relative_slenderness(ly, ry, e_mod)
    phi_x = axial.central_compression_stability_coefficient(lbx, str(case["table7_section_type_x"]))
    phi_y = axial.central_compression_stability_coefficient(lby, str(case["table7_section_type_y"]))

    mx_abs = abs(_number(case, "moment_x_n_mm"))
    my_abs = abs(_number(case, "moment_y_n_mm"))
    wcx = _number(case, "compressed_section_modulus_x_mm3", positive=True)
    wcy = _number(case, "compressed_section_modulus_y_mm3", positive=True)
    mx = (mx_abs / n) * (area / wcx)
    my = (my_abs / n) * (area / wcy)
    x = _resolve_phi_e("x", lbx, mx, phi_x, case)
    y = _resolve_phi_e("y", lby, my, phi_y, case)
    c = _coefficient_c(case, mx, lby, phi_y) if mx_abs > 0.0 else {"status": "NOT_REQUIRED_MX_ZERO", "c": None}

    checks: list[dict[str, Any]] = []
    unresolved: list[str] = []
    branch: dict[str, Any]
    if mx_abs > 0.0 and my_abs == 0.0:
        branch = {"route": "9.2.1_9.2.2_9.2.4_ONE_PLANE_MAJOR"}
        if x["phi_e"] is None:
            unresolved.append("phi_e_x")
        else:
            u109 = bc.beam_column_in_plane_utilization_eq109(n, x["phi_e"], area, ry, gamma_c)
            checks.append({"equation": "109", "utilization": u109, "pass": u109 <= 1.0})
        if c.get("c") is None:
            unresolved.append("coefficient_c")
        else:
            u111 = bc.beam_column_out_of_plane_utilization_eq111(n, float(c["c"]), phi_y, area, ry, gamma_c)
            checks.append({"equation": "111", "utilization": u111, "pass": u111 <= 1.0})
    elif my_abs > 0.0 and mx_abs == 0.0:
        route = bc.minor_axis_bending_route_clause_9_2_8(lbx, lby)
        branch = {"route": "9.2.8_ONE_PLANE_MINOR", **route}
        if y["phi_e"] is None:
            unresolved.append("phi_e_y")
        else:
            u109 = bc.beam_column_in_plane_utilization_eq109(n, y["phi_e"], area, ry, gamma_c)
            checks.append({"equation": "109_y", "utilization": u109, "pass": u109 <= 1.0})
        if route["out_of_plane_central_compression_check_required"]:
            u115 = bc.central_compression_out_of_plane_utilization_eq115(n, phi_x, area, ry, gamma_c)
            checks.append({"equation": "115", "utilization": u115, "pass": u115 <= 1.0})
    elif mx_abs > 0.0 and my_abs > 0.0:
        meff_y = y["m_eff"]
        if meff_y is None:
            branch = {"route": "9.2.9_BIAXIAL_UNRESOLVED_MEFF_Y"}
            unresolved.append("m_eff_y")
        else:
            route = bc.biaxial_additional_checks_clause_9_2_9(meff_y, mx, lbx, lby)
            branch = {"route": "9.2.9_BIAXIAL", **route}
            if route["equation_116_required"]:
                if y["phi_e"] is None:
                    unresolved.append("phi_e_y")
                if c.get("c") is None:
                    unresolved.append("coefficient_c")
                if y["phi_e"] is not None and c.get("c") is not None:
                    phi_exy = bc.biaxial_stability_coefficient_eq117(y["phi_e"], float(c["c"]))
                    u116 = bc.biaxial_beam_column_utilization_eq116(n, phi_exy, area, ry, gamma_c)
                    checks.append({"equation": "116", "phi_exy": phi_exy, "utilization": u116, "pass": u116 <= 1.0})
            if route["equation_109_with_ey_zero_required"]:
                if x["phi_e"] is None:
                    unresolved.append("phi_e_x_for_9.2.9_additional")
                else:
                    u109x = bc.beam_column_in_plane_utilization_eq109(n, x["phi_e"], area, ry, gamma_c)
                    checks.append({"equation": "109_ey_zero", "utilization": u109x, "pass": u109x <= 1.0})
            if route["equation_111_with_ey_zero_required"]:
                if c.get("c") is None:
                    unresolved.append("coefficient_c_for_9.2.9_additional")
                else:
                    u111 = bc.beam_column_out_of_plane_utilization_eq111(n, float(c["c"]), phi_y, area, ry, gamma_c)
                    checks.append({"equation": "111_ey_zero", "utilization": u111, "pass": u111 <= 1.0})
    else:
        branch = {"route": "CENTRAL_COMPRESSION_SECTION_7_REQUIRED"}
        u = axial.central_compression_stability_utilization(n, area, ry, gamma_c, min(phi_x, phi_y))
        checks.append({"equation": "7.1.3", "utilization": u, "pass": u <= 1.0})

    strength_result = _strength(case)
    if strength_result.get("utilization") is None:
        unresolved.append("strength_eq106_point_data")
    all_utils = [float(cn["utilization"]) for cn in checks]
    if strength_result.get("utilization") is not None:
        all_utils.append(float(strength_result["utilization"]))
    governing = max(all_utils) if all_utils and not unresolved else None
    pass_flag = (governing <= 1.0 and all(cn["pass"] for cn in checks) and bool(strength_result.get("pass"))) if governing is not None else None
    return {
        "status": "COMPLETE" if not unresolved else "INCOMPLETE_FAIL_CLOSED",
        "derived": {
            "geometric_slenderness_x": lx, "geometric_slenderness_y": ly,
            "relative_slenderness_x": lbx, "relative_slenderness_y": lby,
            "central_phi_x": phi_x, "central_phi_y": phi_y,
            "relative_eccentricity_x": mx, "relative_eccentricity_y": my,
        },
        "d2_d3_x": x,
        "d2_d3_y": y,
        "coefficient_c": c,
        "stability_branch": branch,
        "stability_checks": checks,
        "strength": strength_result,
        "required_unresolved": sorted(set(unresolved)),
        "governing_utilization": governing,
        "pass": pass_flag,
        "trace_policy": "FIRST_APPLICABLE_BRANCH_WITH_EXPLICIT_D3_BILINEAR_INTERPOLATION_NO_EXTRAPOLATION",
    }
