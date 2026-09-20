"""Stage N8 applicability-safe orchestration for SP16 Section 11 sheet structures."""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import sheet_structures_strength_and_stability as s11
from .axial_members import central_compression_stability_coefficient

CURRENT_SP16_SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def _num(m: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in m:
        raise ValueError(f"sheet_structure_guided requires {key}")
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


def _basis(m: Mapping[str, Any], key: str) -> str:
    if key not in m or not isinstance(m[key], str) or not m[key].strip():
        raise ValueError(f"{key} must be a non-empty provenance string")
    return str(m[key]).strip()


def _critical_c(case: Mapping[str, Any], route: Mapping[str, Any], radius: float, thickness: float) -> dict[str, Any]:
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    e = _num(case, "elastic_modulus_n_mm2", positive=True)
    ratio = radius / thickness
    external = route.get("external_table34_c")
    if external is None:
        bundle = s11.cylindrical_axial_critical_stress(radius, thickness, ry, e)
        bundle["table34_source"] = "exact_printed_node"
        return bundle
    if not isinstance(external, Mapping):
        raise ValueError("external_table34_c must be an object")
    c = _num(external, "value", positive=True)
    basis = _basis(external, "basis")
    bundle = s11.cylindrical_axial_critical_stress(radius, thickness, ry, e, c_coefficient=c)
    bundle["table34_source"] = "external_explicit_value"
    bundle["table34_external_basis"] = basis
    bundle["radius_to_thickness_ratio"] = ratio
    return bundle


def _strength_check(case: Mapping[str, Any], sx: float, sy: float, tau: float, route: Mapping[str, Any]) -> dict[str, Any]:
    if route.get("perform_strength_check") is not True:
        return {"status": "NOT_REQUESTED", "equation_148_utilization": None, "principal_stress_check": None}
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    gamma = _num(case, "working_condition_factor", positive=True)
    rt = _num(route, "tension_design_resistance_n_mm2", positive=True)
    rc = _num(route, "compression_design_resistance_n_mm2", positive=True)
    u = s11.membrane_strength_utilization_eq148(sx, sy, tau, ry, gamma)
    principal = s11.principal_stress_resistance_check_clause_11_1_1(sx, sy, tau, rt, rc, gamma)
    return {
        "status": "EVALUATED",
        "equation_148_utilization": u,
        "equation_148_pass": u <= 1.0,
        "principal_stress_check": principal,
        "pass": u <= 1.0 and bool(principal["pass"]),
    }


def _edge_spatial_gate(route: Mapping[str, Any]) -> dict[str, Any]:
    discontinuity = bool(route["has_geometry_thickness_or_load_discontinuity"]) if "has_geometry_thickness_or_load_discontinuity" in route else False
    arbitrary = bool(route["arbitrary_configuration_or_spatial_state"]) if "arbitrary_configuration_or_spatial_state" in route else False
    base = s11.shell_analysis_route_clause_11_1_4_11_1_5(discontinuity, arbitrary)
    incomplete: list[str] = []
    if discontinuity and route.get("local_edge_effect_analysis_confirmed") is not True:
        incomplete.append("11.1.4 local edge-effect analysis")
    if arbitrary:
        if route.get("certified_spatial_software_confirmed") is not True:
            incomplete.append("11.1.5 certified spatial software")
        if route.get("clauses_11_1_2_to_11_1_4_requirements_confirmed") is not True:
            incomplete.append("11.1.5 compliance with 11.1.2-11.1.4")
    return {**base, "unresolved_requirements": incomplete, "complete": not incomplete}


def _ring_check(case: Mapping[str, Any], route: Mapping[str, Any], pressure: float, radius: float, spacing: float, thickness: float) -> dict[str, Any]:
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    e = _num(case, "elastic_modulus_n_mm2", positive=True)
    gamma = _num(case, "working_condition_factor", positive=True)
    req = s11.ring_stiffener_requirements_clause_11_2_4(pressure, radius, spacing, thickness, e, ry)
    missing = [k for k in ("ring_effective_area_mm2", "ring_radius_of_gyration_mm", "ring_table7_section_type") if k not in route]
    if missing:
        return {"status": "INCOMPLETE_FAIL_CLOSED", "requirements": req, "missing": missing}
    area = _num(route, "ring_effective_area_mm2", positive=True)
    i = _num(route, "ring_radius_of_gyration_mm", positive=True)
    section_type = str(route["ring_table7_section_type"])
    lam = req["ring_effective_length_mm"] / i
    lam_bar = lam * math.sqrt(ry / e)
    phi = central_compression_stability_coefficient(lam_bar, section_type)
    util = req["ring_compression_force_n"] / (phi * area * ry * gamma)
    unresolved: list[str] = []
    if lam_bar > 6.5:
        unresolved.append("11.2.4 conditional ring slenderness exceeds 6.5")
    if route.get("ring_is_one_sided") is True and route.get("one_sided_ring_inertia_axis_confirmed") is not True:
        unresolved.append("11.2.4 one-sided ring inertia about nearest shell surface")
    return {
        "status": "COMPLETE" if not unresolved else "INCOMPLETE_FAIL_CLOSED",
        "requirements": req,
        "geometric_slenderness": lam,
        "relative_slenderness": lam_bar,
        "phi": phi,
        "equation_7_utilization": util,
        "equation_7_pass": util <= 1.0,
        "unresolved_requirements": unresolved,
    }


def _route(case: Mapping[str, Any]) -> dict[str, Any]:
    route = case["route"]
    if not isinstance(route, Mapping):
        raise ValueError("route must be an object")
    kind = str(route["kind"])
    ry = _num(case, "design_yield_resistance_n_mm2", positive=True)
    e = _num(case, "elastic_modulus_n_mm2", positive=True)
    gamma = _num(case, "working_condition_factor", positive=True)
    gate = _edge_spatial_gate(route)

    if kind == "membrane_general_11_1_1":
        sx = _num(route, "sigma_x_n_mm2"); sy = _num(route, "sigma_y_n_mm2"); tau = _num(route, "tau_xy_n_mm2")
        strength = _strength_check(case, sx, sy, tau, {**route, "perform_strength_check": True})
        status = "COMPLETE" if gate["complete"] else "INCOMPLETE_FAIL_CLOSED"
        return {"status": status, "route": kind, "strength": strength, "analysis_gate": gate, "governing_utilization": max(strength["equation_148_utilization"], strength["principal_stress_check"]["tension_utilization"], strength["principal_stress_check"]["compression_utilization"])}

    if kind in {"axisymmetric_membrane_11_1_2", "internal_pressure_cylinder_11_1_3", "internal_pressure_sphere_11_1_3", "internal_pressure_cone_11_1_3"}:
        if kind == "axisymmetric_membrane_11_1_2":
            s1 = s11.meridional_stress_eq149(_num(route, "projected_pressure_force_n"), _num(route, "radius_mm", positive=True), _num(route, "thickness_mm", positive=True), _num(route, "beta_degrees"))
            s2 = s11.circumferential_stress_eq150(_num(route, "pressure_n_mm2"), _num(route, "thickness_mm", positive=True), s1, _num(route, "meridional_radius_mm", positive=True), _num(route, "circumferential_radius_mm", positive=True))
            equation = "149-150"
        elif kind == "internal_pressure_cylinder_11_1_3":
            s1, s2 = s11.cylindrical_internal_pressure_stresses_eq151(_num(route, "pressure_n_mm2"), _num(route, "radius_mm", positive=True), _num(route, "thickness_mm", positive=True)); equation = "151"
        elif kind == "internal_pressure_sphere_11_1_3":
            s1, s2 = s11.spherical_internal_pressure_stresses_eq152(_num(route, "pressure_n_mm2"), _num(route, "radius_mm", positive=True), _num(route, "thickness_mm", positive=True)); equation = "152"
        else:
            s1, s2 = s11.conical_internal_pressure_stresses_eq153(_num(route, "pressure_n_mm2"), _num(route, "radius_mm", positive=True), _num(route, "thickness_mm", positive=True), _num(route, "beta_degrees")); equation = "153"
        strength = _strength_check(case, s1, s2, 0.0, route)
        status = "COMPLETE" if gate["complete"] else "INCOMPLETE_FAIL_CLOSED"
        return {"status": status, "route": kind, "stress_equation": equation, "sigma_1_n_mm2": s1, "sigma_2_n_mm2": s2, "strength": strength, "analysis_gate": gate, "governing_utilization": strength.get("equation_148_utilization")}

    if kind == "cylinder_axial_11_2_1":
        r = _num(route, "radius_mm", positive=True); t = _num(route, "thickness_mm", positive=True); sigma = _num(route, "axial_compressive_stress_n_mm2", nonnegative=True)
        crit = _critical_c(case, route, r, t)
        adjusted = float(crit["critical_stress_n_mm2"])
        eccentric = None
        if route.get("eccentric_compression_or_pure_bending") is True:
            eccentric = s11.eccentric_compression_critical_stress_multiplier_clause_11_2_1(sigma, _num(route, "minimum_signed_stress_n_mm2"), _num(route, "shear_stress_n_mm2"), e, r, t)
            if eccentric["applicable"]:
                adjusted *= float(eccentric["multiplier"])
        util = s11.cylindrical_axial_stability_utilization_eq154(sigma, adjusted, gamma)
        return {"status": "COMPLETE" if gate["complete"] else "INCOMPLETE_FAIL_CLOSED", "route": kind, "critical": crit, "eccentric_adjustment": eccentric, "adjusted_critical_stress_n_mm2": adjusted, "equation_154_utilization": util, "pass": util <= 1.0, "analysis_gate": gate, "governing_utilization": util}

    if kind == "tube_11_2_2":
        r = _num(route, "radius_mm", positive=True); t = _num(route, "thickness_mm", positive=True); lb = _num(route, "relative_slenderness", nonnegative=True)
        classification = s11.tube_local_stability_route_clause_11_2_2(r, t, ry, e, lb)
        if classification["route"] == "global_stability_only_sections_7_and_9":
            confirmed = route.get("sections_7_and_9_global_stability_confirmed") is True
            return {"status": "COMPLETE" if confirmed else "INCOMPLETE_FAIL_CLOSED", "route": kind, "classification": classification, "required": None if confirmed else "Sections 7 and 9 global stability", "governing_utilization": None}
        if classification["route"] != "equation_156_local_stability_no_separate_global_check":
            return {"status": "INCOMPLETE_FAIL_CLOSED", "route": kind, "classification": classification, "required": "outside direct 11.2.2 route; separate engineering route required", "governing_utilization": None}
        crit = _critical_c(case, route, r, t)
        util = s11.tube_local_stability_utilization_eq156(_num(route, "axial_force_n", nonnegative=True), lb, _num(route, "gross_area_mm2", positive=True), _num(route, "relative_eccentricity_m", nonnegative=True), ry, float(crit["critical_stress_n_mm2"]), r, t, e)
        return {"status": "COMPLETE", "route": kind, "classification": classification, "critical": crit, "equation_156_utilization": util, "pass": util <= 1.0, "governing_utilization": util}

    if kind == "cylindrical_panel_11_2_3":
        b = _num(route, "panel_width_mm", positive=True); r = _num(route, "radius_mm", positive=True); t = _num(route, "thickness_mm", positive=True); sigma = _num(route, "compressive_stress_n_mm2", positive=True)
        classification = s11.cylindrical_panel_route_clause_11_2_3(b, r, t)
        if classification["route"] == "panel_equations_157_158":
            limit = s11.cylindrical_panel_limit(sigma, ry, e); ratio = b/t; util = ratio/float(limit["limit_b_over_t"])
            return {"status": "COMPLETE", "route": kind, "classification": classification, "limit": limit, "actual_b_over_t": ratio, "utilization": util, "pass": util <= 1.0, "governing_utilization": util}
        if route.get("shell_clause_11_2_1_confirmed") is not True:
            return {"status": "INCOMPLETE_FAIL_CLOSED", "route": kind, "classification": classification, "required": "11.2.1 shell stability route", "governing_utilization": None}
        crit = _critical_c(case, route, r, t); util = s11.cylindrical_axial_stability_utilization_eq154(sigma, float(crit["critical_stress_n_mm2"]), gamma)
        return {"status": "COMPLETE", "route": kind, "classification": classification, "critical": crit, "equation_154_utilization": util, "pass": util <= 1.0, "governing_utilization": util}

    if kind in {"cylinder_external_pressure_11_2_4", "cylinder_combined_11_2_5"}:
        r = _num(route, "radius_mm", positive=True); t = _num(route, "thickness_mm", positive=True); p = _num(route, "external_pressure_n_mm2", nonnegative=True)
        ring = route.get("ring_stiffened") is True
        length = _num(route, "ring_spacing_mm", positive=True) if ring else _num(route, "length_mm", positive=True)
        cr2 = s11.cylindrical_external_pressure_critical_stress(e, r, length, t); s2 = p*r/t
        u2 = s11.cylindrical_external_pressure_utilization_eq159(s2, float(cr2["critical_stress_n_mm2"]), gamma)
        ring_check = _ring_check(case, route, p, r, length, t) if ring else None
        if kind == "cylinder_external_pressure_11_2_4":
            status = "COMPLETE" if ring_check is None or ring_check["status"] == "COMPLETE" else "INCOMPLETE_FAIL_CLOSED"
            gov = max(u2, float(ring_check["equation_7_utilization"])) if ring_check and "equation_7_utilization" in ring_check else u2
            return {"status": status, "route": kind, "external_pressure_critical": cr2, "equation_159_utilization": u2, "ring_check": ring_check, "pass": status == "COMPLETE" and gov <= 1.0, "governing_utilization": gov}
        sigma1 = _num(route, "axial_compressive_stress_n_mm2", nonnegative=True); cr1 = _critical_c(case, route, r, t)
        u = s11.cylindrical_combined_stability_utilization_eq162(sigma1, float(cr1["critical_stress_n_mm2"]), s2, float(cr2["critical_stress_n_mm2"]), gamma)
        status = "COMPLETE" if ring_check is None or ring_check["status"] == "COMPLETE" else "INCOMPLETE_FAIL_CLOSED"
        gov = max(u, float(ring_check["equation_7_utilization"])) if ring_check and "equation_7_utilization" in ring_check else u
        return {"status": status, "route": kind, "axial_critical": cr1, "external_pressure_critical": cr2, "equation_162_utilization": u, "ring_check": ring_check, "pass": status == "COMPLETE" and gov <= 1.0, "governing_utilization": gov}

    if kind in {"cone_axial_11_2_6", "cone_external_pressure_11_2_7", "cone_combined_11_2_8"}:
        r1 = _num(route, "top_radius_mm", positive=True); r2 = _num(route, "bottom_radius_mm", positive=True); beta = _num(route, "beta_degrees"); t = _num(route, "thickness_mm", positive=True); h = _num(route, "height_mm", positive=True)
        rm = s11.conical_equivalent_radius_eq165(r1, r2, beta)
        result: dict[str, Any] = {"status": "COMPLETE", "route": kind, "equation_165_equivalent_radius_mm": rm}
        n = _num(route, "axial_force_n", nonnegative=True) if kind in {"cone_axial_11_2_6", "cone_combined_11_2_8"} else 0.0
        p = _num(route, "external_pressure_n_mm2", nonnegative=True) if kind in {"cone_external_pressure_11_2_7", "cone_combined_11_2_8"} else 0.0
        ncr = None; cr2 = None; s2 = None
        if kind in {"cone_axial_11_2_6", "cone_combined_11_2_8"}:
            crit1 = _critical_c(case, route, rm, t); ncr = s11.conical_critical_force_eq164(t, float(crit1["critical_stress_n_mm2"]), rm, beta); u1 = s11.conical_axial_stability_utilization_eq163(n, ncr, gamma)
            result.update({"axial_critical": crit1, "equation_164_critical_force_n": ncr, "equation_163_utilization": u1})
        if kind in {"cone_external_pressure_11_2_7", "cone_combined_11_2_8"}:
            s2 = p*rm/t; cr2 = s11.conical_external_pressure_critical_stress_eq167(e, rm, h, t); u2 = s11.conical_external_pressure_utilization_eq166(s2, cr2, gamma)
            result.update({"equation_167_critical_hoop_stress_n_mm2": cr2, "equation_166_utilization": u2})
        if kind == "cone_combined_11_2_8":
            assert ncr is not None and cr2 is not None and s2 is not None
            u = s11.conical_combined_stability_utilization_eq168(n, ncr, s2, cr2, gamma); result["equation_168_utilization"] = u; result["governing_utilization"] = u; result["pass"] = u <= 1.0
        elif kind == "cone_axial_11_2_6":
            result["governing_utilization"] = result["equation_163_utilization"]; result["pass"] = result["equation_163_utilization"] <= 1.0
        else:
            result["governing_utilization"] = result["equation_166_utilization"]; result["pass"] = result["equation_166_utilization"] <= 1.0
        return result

    if kind == "sphere_external_pressure_11_2_9":
        r = _num(route, "radius_mm", positive=True); t = _num(route, "thickness_mm", positive=True); p = _num(route, "external_pressure_n_mm2", nonnegative=True)
        cr = s11.spherical_external_pressure_critical_stress_clause_11_2_9(e, r, t, ry); u = s11.spherical_external_pressure_utilization_eq169(p, r, t, cr, gamma)
        return {"status": "COMPLETE", "route": kind, "critical_stress_n_mm2": cr, "equation_169_utilization": u, "pass": u <= 1.0, "governing_utilization": u}

    raise ValueError(f"unsupported Section 11 route kind: {kind}")


def sheet_structure_guided_workflow(case: dict[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute one applicability-selected current-SP16 Section 11 sheet-structure route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 11.1-11.2
        Annex: None
        Equation/Table: Equations (148)-(169), Table 34
        Audit ID: SP16-N8-GUIDED-SECTION11
        Normative status: normative orchestration

    Mathematical form:
        Selected route -> audited Section-11 scalar producers -> explicit utilization/check bundle.

    Parameters:
        case:
            Type: dict[str, Any]
            Unit: mixed, explicit in field names
            Meaning: Strictly validated Stage-N8 case with one selected route.
            Valid range: Route-specific Section-11 domains.
            Source: user input plus explicit Stage-N1 material hydration when material_ref is supplied.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Selected route, intermediate normative values, fail-closed obligations and governing utilization.

    Assumptions:
        - The caller selects the actual shell topology and supplies the required actions/geometry.
        - Stress-resultant generation, local edge effects and spatial shell analysis are external unless explicitly confirmed.

    Sign convention:
        - Compression and pressure demands are non-negative magnitudes in stability routes.
        - Membrane stress routes retain signed normal/shear stresses where required by Section 11.

    Unit convention:
        - Forces N, lengths mm, stresses and moduli N/mm2, angles degrees.

    Applicability:
        - Current-SP16 Section 11 clauses 11.1-11.2 within the explicit routes implemented here.

    Limitations:
        - Does not infer shell geometry, loading, stress fields, local edge effects or certified-software results.
        - Table 34 uses exact printed nodes unless an explicit externally sourced c value with provenance is supplied.

    Raises:
        ValueError: Required route data are missing, a domain is violated, or an unsupported route is selected.
        TypeError: Underlying audited scalar producers reject an invalid type.

    Examples:
        See examples/sheet_structure_guided_example.json.

    Tests:
        Unit tests:
            - tests/test_stage_n8_sheet_structure_workflows.py
        Validation cases:
            - Stage N8 exact-node and branch-routing qualification cases.

    Implementation notes:
        - N1-N7 remain frozen dependencies.
        - The legacy all-routes demo action is retained for backwards compatibility but is not the Stage-N8 guided route.
    """
    if not isinstance(case, dict):
        raise TypeError("case must be a dict")
    return _route(case)
