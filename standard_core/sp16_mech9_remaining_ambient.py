"""SP16-MECH9 remaining ambient applicability closure.

This stage extends the strict ambient verification workflow with three bounded
routes that were deliberately left fail-closed in SP16-MECH8:

* class-3 one-plane Mx+Qx through the explicit 8.2.7 confirmation gate and
  the 8.2.3 Eq.(50)/(52) resistance expression;
* ordinary Section-12 fatigue through the already qualified Stage-N9 workflow;
* Section-13 brittle-fracture review through the already qualified Stage-N10
  workflow.

No universal torsion-T resistance rule, crane-fatigue shortcut, low-cycle
fatigue formula, or unsupported local-stability geometry is invented here.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import bending_members as bend
from . import fatigue_workflows as n9
from . import brittle_fracture_workflows as n10
from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech8_interactions import build_sp16_mech8_registry

_EPS = 1e-12
_VALID = {"PASS", "FAIL", "N.A.", "DEFERRED", "CONTEXT_UNRESOLVED"}


def _num(values: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in values:
        raise FireUIError(f"SP16-MECH9 requires {key}")
    raw = values[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise FireUIError(f"{key} must be numeric")
    value = float(raw)
    if not math.isfinite(value):
        raise FireUIError(f"{key} must be finite")
    if positive and value <= 0.0:
        raise FireUIError(f"{key} must be positive")
    if nonnegative and value < 0.0:
        raise FireUIError(f"{key} must be non-negative")
    return value


def _bool(values: Mapping[str, Any], key: str) -> bool:
    if key not in values or not isinstance(values[key], bool):
        raise FireUIError(f"SP16-MECH9 requires boolean {key}")
    return bool(values[key])


def _text(values: Mapping[str, Any], key: str) -> str:
    if key not in values or not isinstance(values[key], str) or not values[key].strip():
        raise FireUIError(f"SP16-MECH9 requires text {key}")
    return str(values[key]).strip()


def _ev(
    status: str,
    *,
    source: str,
    scope: list[str],
    utilization: float | None = None,
    reason: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in _VALID:
        raise ValueError("invalid SP16-MECH9 evidence status")
    row: dict[str, Any] = {
        "status": status,
        "utilization": utilization,
        "pass": True if status == "PASS" else False if status == "FAIL" else None,
        "evidence_source": source,
        "evidence_scope": list(scope),
    }
    if reason is not None:
        row["reason"] = reason
    if details is not None:
        row["details"] = dict(details)
    return row


def _util_ev(utilization: float, *, source: str, scope: list[str], details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    u = float(utilization)
    if not math.isfinite(u) or u < 0.0:
        raise ValueError("utilization must be finite and non-negative")
    return _ev("PASS" if u <= 1.0 + _EPS else "FAIL", utilization=u, source=source, scope=scope, details=details)


def _geometry_family(values: Mapping[str, Any]) -> str:
    geom = values.get("section_geometry_2d_normalized")
    if not isinstance(geom, Mapping):
        raise FireUIError("SP16-MECH9 requires section_geometry_2d_normalized")
    raw = geom.get("template")
    if not isinstance(raw, str):
        raw = geom.get("shape_group")
    if not isinstance(raw, str):
        raise FireUIError("section geometry template is missing")
    key = raw.strip().lower()
    if key in {"i", "i-section", "i_section"}:
        return "i_section"
    if key in {"rhs", "shs", "rhs_shs", "box", "box_section"}:
        return "box_section"
    return key


def _mech3_components(values: Mapping[str, Any]) -> Mapping[str, Any]:
    state = values.get("ambient_axis_shear_state")
    if not isinstance(state, Mapping):
        raise FireUIError("ambient_axis_shear_state is missing")
    comp = state.get("clause_8_2_3_components")
    if not isinstance(comp, Mapping):
        raise FireUIError("SP16 8.2.3 component state is missing")
    return comp


def _class3_mq(values: Mapping[str, Any]) -> dict[str, Any]:
    """Close the bounded class-3 one-plane Mx+Qx route of SP16 8.2.7."""
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x")
    my = _num(values, "ambient_M_y")
    qx = _num(values, "ambient_Q_x")
    qy = _num(values, "ambient_Q_y")
    b = _num(values, "ambient_B_bimoment")
    if abs(n) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.7"], reason="class-3 beam route is not extended to N+M+Q")
    if abs(mx) <= _EPS or abs(qx) <= _EPS:
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.7"], reason="qualified class-3 route requires nonzero Mx and Qx")
    if abs(my) > _EPS or abs(qy) > _EPS or abs(b) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.7"], reason="qualified class-3 route is one-plane Mx+Qx only")

    family = _geometry_family(values)
    if family not in {"i_section", "box_section"}:
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.7"], reason="qualified class-3 route supports I and box sections")

    confirmations = {
        "8.2.5": _bool(values, "sp16_mech9_c3_clause_8_2_5_confirmed"),
        "8.4.6": _bool(values, "sp16_mech9_c3_clause_8_4_6_confirmed"),
        "8.5.8": _bool(values, "sp16_mech9_c3_clause_8_5_8_confirmed"),
        "8.5.9": _bool(values, "sp16_mech9_c3_clause_8_5_9_confirmed"),
        "8.5.18": _bool(values, "sp16_mech9_c3_clause_8_5_18_confirmed"),
        "shear_effect": _bool(values, "sp16_mech9_c3_max_moment_shear_effect_confirmed"),
    }
    route = bend.class_3_plastic_hinge_route(
        confirmations["8.2.5"], confirmations["8.4.6"], confirmations["8.5.8"],
        confirmations["8.5.9"], confirmations["8.5.18"], confirmations["shear_effect"],
    )
    if not route["permitted"]:
        return _ev(
            "DEFERRED",
            source="SP16-MECH9 class-3 applicability",
            scope=["SP16 8.2.7", "SP16 8.2.5", "SP16 8.4.6", "SP16 8.5.8", "SP16 8.5.9", "SP16 8.5.18"],
            reason="class-3 route confirmations are incomplete",
            details={"missing_confirmations": route["missing_confirmations"]},
        )

    comp = _mech3_components(values)
    if comp.get("applicable") is not True:
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.3", "SP16 8.2.7"], reason="8.2.3 shear component state is unavailable")
    tau_x = abs(float(comp["tau_x_effective_n_mm2"]))
    aw = float(comp["A_w_mm2"])
    af = float(comp["A_f_one_flange_mm2"])
    rs = _num(values, "Rs_formula", positive=True)
    ryn = _num(values, "fy_norm", positive=True)
    support = _bool(values, "sp16_mech8_is_support_section")
    referenced = confirmations["8.4.6"] and confirmations["8.5.8"] and confirmations["8.5.9"] and confirmations["8.5.18"]
    app = bend.plastic_bending_applicability(3, family, ryn, tau_x, rs, referenced, support)
    if app["permitted"] is not True:
        return _ev(
            "DEFERRED",
            source="SP16-MECH9 8.2.3/8.2.7 applicability",
            scope=["SP16 8.2.3", "SP16 8.2.7"],
            reason="class-3 plastic-hinge resistance route is outside the qualified applicability domain",
            details={"failed_gates": app["failed_gates"]},
        )

    row_id = _text(values, "sp16_mech8_annex_e1_section_type")
    gamma_f = _num(values, "sp16_mech8_equivalent_load_safety_factor", positive=True)
    catalog = bend.annex_e1_plastic_coefficient_catalog()
    rows = catalog["section_types"]
    if row_id not in rows:
        raise FireUIError("invalid Annex E Table E.1 row")
    alpha_f = af / aw
    ratio = None if rows[row_id].get("ratio_nodes") is None else alpha_f
    coeff = bend.annex_e1_design_coefficients(row_id, ratio, True, gamma_f)
    beta = bend.plastic_shear_reduction_factor_eq52(tau_x, rs, alpha_f)
    wx = _num(values, "W_xn_min", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gamma_c = _num(values, "gamma_c_bending_strength", positive=True)
    utilization = bend.plastic_bending_utilization_eq50(abs(mx), coeff["c_x"], beta, wx, ry, gamma_c)
    return _util_ev(
        utilization,
        source="SP16-MECH9 class-3 Eq.(50)+(52)+8.2.7",
        scope=["SP16 8.2.7", "SP16 8.2.3 Eq.(50)", "SP16 Eq.(52)", "Annex E Table E.1"],
        details={
            "class_3_route": route,
            "same_moment_section_shear_effect_confirmed": confirmations["shear_effect"],
            "c_x": coeff["c_x"], "beta": beta, "alpha_f": alpha_f,
            "tau_x_n_mm2": tau_x, "table_e1_row": row_id,
        },
    )


def _fatigue(values: Mapping[str, Any]) -> dict[str, Any]:
    if values.get("sp16_mech7_fatigue_required") is not True:
        return _ev("N.A.", source="sp16_mech7_fatigue_required", scope=["SP16 §12"], reason="fatigue classified not applicable")
    kind = _text(values, "sp16_mech9_fatigue_route_kind")
    if kind != "ordinary_fatigue_12_1_2":
        reason = "low-cycle fatigue remains an external-method boundary" if kind == "low_cycle_lt_1e5_12_1_1" else "crane-runway fatigue requires the dedicated Stage-N9 crane route"
        return _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 §12"], reason=reason, details={"selected_route": kind})
    route = {
        "kind": kind,
        "load_cycles": _num(values, "sp16_mech9_fatigue_load_cycles", nonnegative=True),
        "resonant_vortex_excitation": _bool(values, "sp16_mech9_fatigue_resonant_vortex_excitation"),
        "sp20_load_basis_confirmed": _bool(values, "sp16_mech9_fatigue_sp20_load_basis_confirmed"),
        "net_section_stress_without_dynamic_and_stability_coefficients_confirmed": _bool(values, "sp16_mech9_fatigue_net_stress_basis_confirmed"),
        "same_loading_for_extreme_stresses_confirmed": _bool(values, "sp16_mech9_fatigue_same_loading_extremes_confirmed"),
        "annex_k_case_selection_confirmed": _bool(values, "sp16_mech9_fatigue_annex_k_case_confirmed"),
        "annex_k_case_id": _text(values, "sp16_mech9_fatigue_annex_k_case_id"),
        "normative_ultimate_resistance_n_mm2": _num(values, "fu_norm", positive=True),
        "design_ultimate_resistance_n_mm2": _num(values, "Ru_formula", positive=True),
        "ultimate_resistance_safety_factor": _num(values, "gamma_u", positive=True),
        "maximum_signed_stress_n_mm2": _num(values, "sp16_mech9_fatigue_sigma_max"),
        "minimum_signed_stress_n_mm2": _num(values, "sp16_mech9_fatigue_sigma_min"),
    }
    result = n9.fatigue_guided_workflow({"route": route})
    if result.get("status") != "COMPLETE":
        return _ev("DEFERRED", source="SP16 N9 primary auto-execution", scope=["SP16 §12"], reason=str(result.get("required") or result.get("missing_confirmations") or "N9 route incomplete"), details={"n9_result": result})
    utilization = result.get("governing_utilization")
    if not isinstance(utilization, (int, float)):
        utilization = 0.0 if result.get("pass") is True else 1.0 + _EPS
    return _util_ev(float(utilization), source="SP16 N9 ordinary fatigue auto-execution", scope=["SP16 12.1.1", "SP16 12.1.2 Eq.(170)-(172)", "Tables 35-36", "Annex K"], details={"n9_result": result})


def _brittle(values: Mapping[str, Any]) -> dict[str, Any]:
    if values.get("sp16_mech7_brittle_required") is not True:
        return _ev("N.A.", source="sp16_mech7_brittle_required", scope=["SP16 §13"], reason="Section 13 review classified not applicable")
    route: dict[str, Any] = {
        "kind": "section13_full_review",
        "design_yield_resistance_n_mm2": _num(values, "Ry_formula", positive=True),
        "welded_structure": _bool(values, "sp16_mech9_brittle_welded_structure"),
        "steel_selection_5_2_table_v1_confirmed": _bool(values, "sp16_mech9_brittle_steel_selection_confirmed"),
        "stress_concentration_and_work_hardening_reduction_confirmed": _bool(values, "sp16_mech9_brittle_stress_concentration_confirmed"),
        "solid_web_vs_lattice_concentration_considered": _bool(values, "sp16_mech9_brittle_solid_web_lattice_considered"),
        "cover_plate_splice_with_flank_welds": _bool(values, "sp16_mech9_brittle_cover_plate_flank_welds"),
        "guillotine_cutting_or_punched_holes": _bool(values, "sp16_mech9_brittle_guillotine_or_punched"),
        "secondary_gusset_to_tension_member": _bool(values, "sp16_mech9_brittle_secondary_gusset"),
        "steel_grade_number": _num(values, "sp16_mech9_brittle_steel_grade_number", positive=True),
        "plate_thickness_mm": _num(values, "governing_product_thickness_mm", positive=True),
        "joint_type": _text(values, "sp16_mech9_brittle_joint_type"),
        "through_thickness_tension": _bool(values, "sp16_mech9_brittle_through_thickness_tension"),
        "clause_13_3_engineering_review_confirmed": _bool(values, "sp16_mech9_brittle_13_3_review_confirmed"),
        "lamellar_tearing_assessment_required": _bool(values, "sp16_mech9_brittle_lamellar_required"),
    }
    if route["welded_structure"]:
        route.update({
            "weld_zone_tensile_stress_n_mm2": _num(values, "sp16_mech9_brittle_weld_sigma_t", nonnegative=True),
            "enhanced_ndt_for_welds_above_0_4_ry_confirmed": _bool(values, "sp16_mech9_brittle_enhanced_ndt_confirmed"),
            "weld_intersections_avoided_confirmed": _bool(values, "sp16_mech9_brittle_weld_intersections_avoided"),
            "runoff_tabs_and_weld_ndt_confirmed": _bool(values, "sp16_mech9_brittle_runoff_tabs_ndt_confirmed"),
        })
    if route["cover_plate_splice_with_flank_welds"]:
        route["flank_weld_termination_distance_each_side_mm"] = _num(values, "sp16_mech9_brittle_flank_termination", nonnegative=True)
    if route["guillotine_cutting_or_punched_holes"]:
        route["minimum_section_thickness_used_confirmed"] = _bool(values, "sp16_mech9_brittle_min_thickness_confirmed")
    if route["secondary_gusset_to_tension_member"]:
        route["bolted_secondary_gusset_attachment_confirmed"] = _bool(values, "sp16_mech9_brittle_gusset_bolted_confirmed")
    if route["lamellar_tearing_assessment_required"]:
        route.update({
            "through_thickness_test_evidence_available": _bool(values, "sp16_mech9_brittle_z_test_available"),
            "selected_z_quality_certificate_confirmed": _bool(values, "sp16_mech9_brittle_z_certificate_confirmed"),
            "connection_form_case": _text(values, "sp16_mech9_brittle_connection_form_case"),
            "risk_weld_leg_mm": _num(values, "sp16_mech9_brittle_risk_weld_leg", nonnegative=True),
            "restraint_level": _text(values, "sp16_mech9_brittle_restraint_level"),
            "pass_count": _text(values, "sp16_mech9_brittle_pass_count"),
            "weld_sequence": _text(values, "sp16_mech9_brittle_weld_sequence"),
            "preheat": _text(values, "sp16_mech9_brittle_preheat"),
            "through_thickness_action": _text(values, "sp16_mech9_brittle_through_thickness_action"),
            "construction_group": int(_num(values, "sp16_mech9_brittle_construction_group", positive=True)),
            "consequence_class": _text(values, "sp16_mech9_brittle_consequence_class"),
            "flange_connection_15_9_10_or_force_normal_to_plate": _bool(values, "sp16_mech9_brittle_special_flange_or_normal_force"),
            "selected_z_quality_group": _text(values, "sp16_mech9_brittle_selected_z_group"),
        })
    result = n10.brittle_fracture_guided_workflow({"route": route})
    if result.get("status") != "COMPLETE":
        return _ev("DEFERRED", source="SP16 N10 primary auto-execution", scope=["SP16 §13"], reason=str(result.get("required_evidence") or "N10 route incomplete"), details={"n10_result": result})
    utilization = result.get("governing_utilization")
    passed = bool(result.get("pass"))
    if isinstance(utilization, (int, float)):
        return _util_ev(float(utilization) if passed else max(float(utilization), 1.0 + _EPS), source="SP16 N10 Section 13 auto-execution", scope=["SP16 13.1-13.5", "Eq.(174)", "Table 37"], details={"n10_result": result})
    return _ev("PASS" if passed else "FAIL", source="SP16 N10 Section 13 auto-execution", scope=["SP16 13.1-13.5"], reason=None if passed else "one or more Section 13 prevention requirements failed", details={"n10_result": result})


def bind_mech9_remaining_ambient_evidence(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Overlay bounded class-3 M+Q and primary N9/N10 execution evidence on SP16-MECH8.

    Standard reference:
        SP 16.13330.2017 with Changes No. 1-6 through 09.12.2024; clauses 8.2.3/8.2.7, Section 12 and Section 13.

    Parameters:
        values: Current guided-session mapping containing the MECH8 evidence bundle plus explicit MECH9 classifications and route inputs.

    Returns:
        Cumulative ``sp16_mech9_primary_evidence`` bundle and route-completion diagnostics for the unchanged strict MECH6 gate.

    Assumptions:
        The inherited MECH8 evidence and N9/N10 scalar workflows are the qualified implementations from the cumulative parent release.

    Sign convention:
        Canonical signed ambient actions are preserved; absolute values are applied only at SP16 equations that use magnitudes.

    Unit convention:
        N, mm, N*mm, N*mm2 and N/mm2 (MPa) according to the active DAG quantity declarations.

    Applicability:
        Class-3 one-plane Mx+Qx for explicitly confirmed 8.2.7 applicability, ordinary fatigue 12.1.2, and explicit Section-13 full review.

    Limitations:
        Does not close arbitrary T resistance, class-3 biaxial M+Q, N+M+Q, crane fatigue, current low-cycle external-method boundary, or unsupported detailed local-stability geometries.

    Raises:
        FireUIError for malformed mandatory MECH8 evidence or missing required explicit route inputs; qualified N9/N10 workflows may raise ValueError for inconsistent engineering classifications.

    Examples:
        ``bind_mech9_remaining_ambient_evidence(values)`` returns an overlay consumed by the strict SP16 mechanical gate.

    Tests:
        Covered by ``tests/test_sp16_mech9_remaining_ambient.py`` and cumulative regression suites.

    Implementation notes:
        A route that cannot be fully executed is DEFERRED rather than inferred as PASS.
    """
    parent = values.get("sp16_mech8_primary_evidence")
    if not isinstance(parent, Mapping):
        raise FireUIError("SP16-MECH9 requires sp16_mech8_primary_evidence")
    parent_ev = parent.get("evidence")
    if not isinstance(parent_ev, Mapping):
        raise FireUIError("SP16-MECH8 evidence bundle is malformed")
    evidence = {str(k): dict(v) for k, v in parent_ev.items() if isinstance(v, Mapping)}

    census = values.get("sp16_applicability_census")
    if not isinstance(census, Mapping):
        raise FireUIError("SP16-MECH9 requires sp16_applicability_census")
    active = census.get("active_checks")
    context = census.get("context_driven_checks")
    if not isinstance(active, list) or not isinstance(context, list):
        raise FireUIError("SP16-MECH9 census check collections are malformed")
    active_ids = {str(r["id"]) for r in active if isinstance(r, Mapping) and "id" in r}
    context_ids = {str(r["id"]) for r in context if isinstance(r, Mapping) and "id" in r}

    if "interaction_M_Q" in active_ids and _text(values, "sp16_section_class") == "3":
        try:
            evidence["interaction_M_Q"] = _class3_mq(values)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["interaction_M_Q"] = _ev("DEFERRED", source="SP16-MECH9", scope=["SP16 8.2.7"], reason=str(exc))

    if "fatigue" in context_ids and values.get("sp16_mech7_fatigue_required") is True:
        try:
            evidence["fatigue"] = _fatigue(values)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["fatigue"] = _ev("DEFERRED", source="SP16-MECH9 N9 binding", scope=["SP16 §12"], reason=str(exc))

    if "brittle_fracture" in context_ids and values.get("sp16_mech7_brittle_required") is True:
        try:
            evidence["brittle_fracture"] = _brittle(values)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["brittle_fracture"] = _ev("DEFERRED", source="SP16-MECH9 N10 binding", scope=["SP16 §13"], reason=str(exc))

    resolved = sorted(k for k, row in evidence.items() if row.get("status") in {"PASS", "FAIL", "N.A."})
    deferred = sorted(k for k, row in evidence.items() if row.get("status") in {"DEFERRED", "CONTEXT_UNRESOLVED"})
    class3_closed = True
    if "interaction_M_Q" in active_ids and _text(values, "sp16_section_class") == "3":
        class3_closed = evidence["interaction_M_Q"].get("status") in {"PASS", "FAIL", "N.A."}
    n9_required = "fatigue" in context_ids and values.get("sp16_mech7_fatigue_required") is True
    n10_required = "brittle_fracture" in context_ids and values.get("sp16_mech7_brittle_required") is True
    n9_closed = (not n9_required) or ("fatigue" in evidence and evidence["fatigue"]["status"] in {"PASS", "FAIL"})
    n10_closed = (not n10_required) or ("brittle_fracture" in evidence and evidence["brittle_fracture"]["status"] in {"PASS", "FAIL"})
    bundle = {
        "schema": "sp16_mech9_primary_ambient_evidence_v1",
        "evidence": evidence,
        "resolved_check_ids": resolved,
        "deferred_check_ids": deferred,
        "class3_mq_primary_route_closed": class3_closed,
        "ordinary_fatigue_primary_route_closed": n9_closed,
        "section13_primary_route_closed": n10_closed,
        "all_bound_checks_resolved": not deferred,
        "policy": "explicit bounded MECH9 routes only; unsupported local stability, T and special N9 routes stay fail-closed",
    }
    return {
        "sp16_mech9_primary_evidence": bundle,
        "sp16_mech9_class3_mq_binding_complete": class3_closed,
        "sp16_mech9_n9_primary_execution_complete": n9_closed,
        "sp16_mech9_n10_primary_execution_complete": n10_closed,
    }


def _executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return bind_mech9_remaining_ambient_evidence(values)


def build_sp16_mech9_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Extend the cumulative guided registry with SP16-MECH9 remaining-ambient evidence execution.

    Standard reference:
        SP 16.13330.2017 Sections 8, 12 and 13 over the frozen MECH8 parent runtime.

    Parameters:
        catalog: Frozen interim profile catalogue.
        registry: Optional existing registry to extend.

    Returns:
        ExecutionRegistry containing inherited MECH8 executors and ``SP16_C_MECH9_REMAINING_AMBIENT_BINDER``.

    Assumptions:
        The parent registry satisfies the v0.65 cumulative release contract.

    Sign convention:
        Canonical MECH1 signed action convention is preserved.

    Unit convention:
        Active DAG canonical units.

    Applicability:
        Guided ambient SP16 verification using the v0.66 MECH9 graph.

    Limitations:
        Registry extension does not imply engineering-use readiness; unresolved routes remain fail-closed.

    Raises:
        Propagates inherited registry/catalog errors and duplicate executor registration errors.

    Examples:
        ``build_sp16_mech9_registry(InterimProfileCatalog())``.

    Tests:
        Covered by ``tests/test_sp16_mech9_remaining_ambient.py``.

    Implementation notes:
        The strict SP16_MECHANICAL_PASS semantics remain owned by MECH6.
    """
    reg = build_sp16_mech8_registry(catalog, registry)
    reg.register("SP16_C_MECH9_REMAINING_AMBIENT_BINDER", _executor)
    return reg
