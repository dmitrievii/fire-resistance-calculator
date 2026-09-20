"""SP16-MECH7 primary ambient verification evidence binding.

This stage binds already-qualified SP16 scalar procedures to the primary ambient
load case.  It does not invent missing normative routes: every evidence row is
explicitly PASS/FAIL/N.A./DEFERRED and the downstream SP16-MECH6 gate remains
strictly fail-closed.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .axial_members import (
    axial_strength_utilization_yield,
    axial_strength_utilization_ultimate,
    central_compression_stability_utilization,
)
from .axial_workflows import select_equation_5_resistance_branch
from .base_plates_and_combined_force_strength import combined_force_point_utilization_eq106
from .beam_column_stability import (
    beam_column_in_plane_utilization_eq109,
    beam_column_out_of_plane_utilization_eq111,
    central_compression_out_of_plane_utilization_eq115,
    biaxial_beam_column_utilization_eq116,
    biaxial_stability_coefficient_eq117,
    biaxial_additional_checks_clause_9_2_9,
)
from .bending_members import elastic_combined_normal_utilization_eq43
from .crane_runway_and_bending_stability import lateral_torsional_stability_utilization_eq69
from .effective_lengths_and_limiting_slenderness import (
    compressed_limit_alpha,
    table_32_compressed_limiting_slenderness,
    slenderness_check,
)
from .fire_ui0 import ExecutionRegistry, FireUIError
from .local_stability import wall_relative_slenderness, wall_slenderness_limit, flange_relative_slenderness, flange_slenderness_limit
from .profile_catalog import InterimProfileCatalog
from .sp16_mech6_gate import build_sp16_mech6_registry

_EPS = 1e-12


def _num(values: Mapping[str, Any], key: str, *, positive: bool = False) -> float:
    if key not in values:
        raise FireUIError(f"SP16-MECH7 requires {key}")
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{key} must be numeric")
    x = float(value)
    if not math.isfinite(x) or (positive and x <= 0.0):
        raise FireUIError(f"{key} has invalid value")
    return x


def _maybe_num(values: Mapping[str, Any], key: str) -> float | None:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    x = float(value)
    return x if math.isfinite(x) else None


def _ev(status: str, *, utilization: float | None = None, source: str, scope: list[str], reason: str | None = None) -> dict[str, Any]:
    if status not in {"PASS", "FAIL", "N.A.", "DEFERRED"}:
        raise ValueError("invalid MECH7 evidence status")
    row: dict[str, Any] = {
        "status": status,
        "utilization": utilization,
        "pass": True if status == "PASS" else False if status == "FAIL" else None,
        "evidence_source": source,
        "evidence_scope": scope,
    }
    if reason is not None:
        row["reason"] = reason
    return row


def _util_ev(utilization: float, *, source: str, scope: list[str]) -> dict[str, Any]:
    u = float(utilization)
    return _ev("PASS" if u <= 1.0 + _EPS else "FAIL", utilization=u, source=source, scope=scope)


def _points(values: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], Mapping[str, Any]]:
    state = values.get("ambient_complete_pointwise_stress_state")
    if not isinstance(state, Mapping) or state.get("runtime_closed") is not True:
        raise FireUIError("ambient complete pointwise state is unavailable")
    points = state.get("points")
    if not isinstance(points, list) or not points:
        raise FireUIError("ambient pointwise state has no material points")
    return [p for p in points if isinstance(p, Mapping)], state


def _eq43_governing(values: Mapping[str, Any], *, use_mx: bool, use_my: bool, use_b: bool) -> float:
    points, state = _points(values)
    mx = _num(values, "ambient_M_x") if use_mx else 0.0
    my = _num(values, "ambient_M_y") if use_my else 0.0
    b = _num(values, "ambient_B_bimoment") if use_b else 0.0
    ix = _num(values, "I_xn", positive=True)
    iy = _num(values, "I_yn", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_bending_strength", positive=True)
    if abs(b) > _EPS:
        iw = state.get("I_omega_n_mm6")
        if isinstance(iw, bool) or not isinstance(iw, (int, float)) or float(iw) <= 0.0:
            raise FireUIError("nonzero B requires qualified I_omega in MECH5 state")
        iwf = float(iw)
    else:
        iwf = 1.0
    utils: list[float] = []
    for p in points:
        omega = float(p["sectorial_coordinate_omega_mm2"]) if abs(b) > _EPS else 0.0
        utils.append(elastic_combined_normal_utilization_eq43(
            mx, my, b, ix, iy, iwf,
            float(p["y_mm"]), float(p["x_mm"]), omega, ry, gc,
        ))
    return max(utils)


def _eq106_governing(values: Mapping[str, Any]) -> float:
    points, state = _points(values)
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x")
    my = _num(values, "ambient_M_y")
    b = _num(values, "ambient_B_bimoment")
    an = _num(values, "A_net", positive=True)
    ix = _num(values, "I_xn", positive=True)
    iy = _num(values, "I_yn", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_nm_strength", positive=True)
    if abs(b) > _EPS:
        iw = state.get("I_omega_n_mm6")
        if isinstance(iw, bool) or not isinstance(iw, (int, float)) or float(iw) <= 0.0:
            raise FireUIError("nonzero B requires qualified I_omega in MECH5 state")
        iwf = float(iw)
    else:
        iwf = 1.0
    utils: list[float] = []
    for p in points:
        omega = float(p["sectorial_coordinate_omega_mm2"]) if abs(b) > _EPS else 0.0
        utils.append(combined_force_point_utilization_eq106(
            n, an, mx, float(p["y_mm"]), ix, my, float(p["x_mm"]), iy,
            b, omega, iwf, ry, gc,
        ))
    return max(utils)


def _axial_strength(values: Mapping[str, Any], n: float) -> dict[str, Any]:
    an = _num(values, "A_net", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    ru = _num(values, "Ru_formula", positive=True)
    ryn = _num(values, "fy_norm", positive=True)
    gu = _num(values, "gamma_u", positive=True)
    if n > 0.0:
        gc = _num(values, "gamma_c_tension", positive=True)
        post = values.get("sp16_mech7_tension_post_yield_possible")
        if not isinstance(post, bool):
            return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.1.1 Eq.(5)"], reason="tension post-yield-service classification is missing")
        branch = select_equation_5_resistance_branch("tension", ryn, post)
        if branch["branch"] == "ultimate":
            u = axial_strength_utilization_ultimate(abs(n), an, ru, gu, gc)
            return _util_ev(u, source="SP16-MECH7 Eq.(5) Ru/gamma_u branch", scope=["SP16 7.1.1 Eq.(5)"])
        u = axial_strength_utilization_yield(abs(n), an, ry, gc)
        return _util_ev(u, source="SP16-MECH7 Eq.(5) Ry branch", scope=["SP16 7.1.1 Eq.(5)"])
    gc = _num(values, "gamma_c_compression", positive=True)
    u = axial_strength_utilization_yield(abs(n), an, ry, gc)
    return _util_ev(u, source="SP16-MECH7 Eq.(5) compression Ry branch", scope=["SP16 7.1.1 Eq.(5)"])


def _compression_stability(values: Mapping[str, Any], n: float) -> dict[str, Any]:
    area = _num(values, "A_gross", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_compression", positive=True)
    phix = _num(values, "phi_x_sp16", positive=True)
    phiy = _num(values, "phi_y_sp16", positive=True)
    ux = central_compression_stability_utilization(abs(n), area, ry, gc, phix)
    uy = central_compression_stability_utilization(abs(n), area, ry, gc, phiy)
    return _util_ev(max(ux, uy), source="SP16-MECH7 Eq.(7) both principal axes", scope=["SP16 7.1.3 Eq.(7)"])


def _slenderness(values: Mapping[str, Any], n: float) -> dict[str, Any]:
    row = values.get("sp16_mech7_table32_row")
    group4 = values.get("sp16_mech7_group4_slenderness_increase")
    if not isinstance(row, str) or not isinstance(group4, bool):
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 10.4.1 Table 32"], reason="Table 32 classification is missing")
    lx = _num(values, "sp16_lambda_x_geom", positive=True)
    ly = _num(values, "sp16_lambda_y_geom", positive=True)
    phix = _num(values, "phi_x_sp16", positive=True)
    phiy = _num(values, "phi_y_sp16", positive=True)
    area = _num(values, "A_gross", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_compression", positive=True)
    phi = min(phix, phiy)
    alpha = compressed_limit_alpha(abs(n), phi, area, ry, gc)
    limit = table_32_compressed_limiting_slenderness(row, alpha, group4)
    check = slenderness_check(max(lx, ly), limit)
    return _util_ev(float(check["utilization"]), source=f"SP16-MECH7 Table 32 row {row}", scope=["SP16 10.4.1 Table 32"])


def _ltb(values: Mapping[str, Any], mx: float, my: float) -> dict[str, Any]:
    required = values.get("ltb_check_required")
    if required is False:
        return _ev("N.A.", source="ltb_check_required", scope=["SP16 8.4", "Annex Ж"], reason="LTB explicitly classified as not required")
    if required is not True:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 8.4", "Annex Ж"], reason="LTB applicability is not classified")
    # Current primary LTB chain is major-axis only; minor/biaxial stability requires a dedicated route.
    if abs(my) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 8.4", "Annex Ж"], reason="primary LTB binder currently closes only the qualified major-axis Mx route")
    phi_b = _maybe_num(values, "phi_bending")
    if phi_b is None or phi_b <= 0.0:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 Eq.(69)"], reason="qualified phi_b is missing")
    wplus = _num(values, "W_el_x_pos", positive=True)
    wminus = _num(values, "W_el_x_neg", positive=True)
    wc = min(wplus, wminus)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_bending_stability", positive=True)
    u = lateral_torsional_stability_utilization_eq69(abs(mx), phi_b, wc, ry, gc)
    return _util_ev(u, source="SP16-MECH7 Eq.(69) primary LTB binding", scope=["SP16 8.4.1 Eq.(69)"])


def _nm_interaction(values: Mapping[str, Any], n: float, mx: float, my: float) -> dict[str, Any]:
    try:
        section_u = _eq106_governing(values)
    except (FireUIError, KeyError, TypeError, ValueError) as exc:
        return _ev("DEFERRED", source="SP16-MECH7 Eq.(106)", scope=["SP16 9.1.1 Eq.(106)"], reason=str(exc))
    utils = [section_u]
    sources = ["Eq.(106) section-point strength"]
    if n < 0.0:
        area = _num(values, "A_gross", positive=True)
        ry = _num(values, "Ry_formula", positive=True)
        gc = _num(values, "gamma_c_nm_stability", positive=True)
        phix = _maybe_num(values, "phi_x_sp16")
        phiy = _maybe_num(values, "phi_y_sp16")
        if phix is None or phiy is None or phix <= 0.0 or phiy <= 0.0:
            return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2"], reason="central compression phi_x/phi_y is missing")
        if abs(mx) > _EPS and abs(my) <= _EPS:
            phiex = _maybe_num(values, "phi_ex_sp16") or _maybe_num(values, "phi_e_sp16")
            c = _maybe_num(values, "c_sp16")
            if phiex is None or c is None or phiex <= 0.0 or c <= 0.0:
                return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2 Eq.(109)/(111)"], reason="phi_ex or c is missing")
            utils.append(beam_column_in_plane_utilization_eq109(abs(n), phiex, area, ry, gc)); sources.append("Eq.(109)")
            utils.append(beam_column_out_of_plane_utilization_eq111(abs(n), c, phiy, area, ry, gc)); sources.append("Eq.(111)")
        elif abs(my) > _EPS and abs(mx) <= _EPS:
            phiey = _maybe_num(values, "phi_ey_sp16") or _maybe_num(values, "phi_e_sp16")
            if phiey is None or phiey <= 0.0:
                return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2 Eq.(109)/(115)"], reason="phi_ey is missing")
            utils.append(beam_column_in_plane_utilization_eq109(abs(n), phiey, area, ry, gc)); sources.append("Eq.(109), y-plane")
            utils.append(central_compression_out_of_plane_utilization_eq115(abs(n), phix, area, ry, gc)); sources.append("Eq.(115)")
        elif abs(mx) > _EPS and abs(my) > _EPS:
            phiey = _maybe_num(values, "phi_ey_sp16")
            c = _maybe_num(values, "c_sp16")
            meff_y = _maybe_num(values, "sp16_m_eff_lookup")
            m_x = _maybe_num(values, "sp16_m_x")
            lbx = _maybe_num(values, "lambda_bar_x")
            lby = _maybe_num(values, "lambda_bar_y")
            phiex = _maybe_num(values, "phi_ex_sp16")
            if None in {phiey, c, meff_y, m_x, lbx, lby} or float(phiey) <= 0.0 or float(c) <= 0.0:
                return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2.9"], reason="biaxial 9.2.9 routing quantities are incomplete")
            route = biaxial_additional_checks_clause_9_2_9(float(meff_y), float(m_x), float(lbx), float(lby))
            if route["section_8_y_route_required"]:
                return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2.9"], reason="m_eff,y>20 requires the linked Section 8 y-route which is not yet bound in MECH7")
            if route["equation_116_required"]:
                phiexy = biaxial_stability_coefficient_eq117(float(phiey), float(c))
                utils.append(biaxial_beam_column_utilization_eq116(abs(n), phiexy, area, ry, gc)); sources.append("Eq.(116)/(117)")
            if route["equation_109_with_ey_zero_required"]:
                if phiex is None or phiex <= 0.0:
                    return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 9.2.9"], reason="additional Eq.(109) requires phi_ex")
                utils.append(beam_column_in_plane_utilization_eq109(abs(n), phiex, area, ry, gc)); sources.append("Eq.(109), e_y=0")
            if route["equation_111_with_ey_zero_required"]:
                utils.append(beam_column_out_of_plane_utilization_eq111(abs(n), float(c), phiy, area, ry, gc)); sources.append("Eq.(111), e_y=0")
    return _util_ev(max(utils), source="SP16-MECH7 " + " + ".join(sources), scope=["SP16 9.1.1 Eq.(106)", "SP16 9.2 where compression applies"])



def _compression_local_stability(values: Mapping[str, Any], check_id: str) -> dict[str, Any]:
    geom = values.get("section_geometry_2d_normalized")
    if not isinstance(geom, Mapping):
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3"], reason="normalized section geometry is missing")
    template = str(geom.get("template") or geom.get("shape") or "")
    if template not in {"i_section", "doubly_symmetric_i"}:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3"], reason="MECH7 primary local-stability binding currently closes central compression only for the qualified I-section template")
    try:
        h=float(geom["h_mm"]); b=float(geom["b_mm"]); tw=float(geom["tw_mm"]); tf=float(geom["tf_mm"])
    except (KeyError, TypeError, ValueError):
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3"], reason="I-section h/b/tw/tf geometry is incomplete")
    if min(h,b,tw,tf) <= 0.0 or h <= 2.0*tf or b <= tw:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3"], reason="I-section geometry is invalid for local-stability plate checks")
    ry=_num(values,"Ry_formula",positive=True); elastic=_num(values,"E_norm",positive=True)
    lbx=_num(values,"lambda_bar_x",positive=True); lby=_num(values,"lambda_bar_y",positive=True)
    member_lambda=max(lbx,lby)
    if check_id == "local_stability_web":
        group=values.get("sp16_mech7_table9_group")
        if not isinstance(group,str):
            return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3.2 Table 9"], reason="Table 9 diagram group is missing")
        if group != "group_1_i_section":
            return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3.2 Table 9"], reason="selected Table 9 diagram group is not the qualified I-section group")
        heff=h-2.0*tf
        actual=wall_relative_slenderness(heff,tw,ry,elastic)
        limit=wall_slenderness_limit(group,member_lambda)
        return _util_ev(actual/limit, source="SP16-MECH7 Table 9 I-section web local stability", scope=["SP16 7.3.2 Table 9"])
    group=values.get("sp16_mech7_table10_group"); edge=values.get("sp16_mech7_flange_edge_stiffened")
    if not isinstance(group,str) or not isinstance(edge,bool):
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3.8 Table 10"], reason="Table 10 diagram group/edge-stiffener classification is missing")
    outstand=0.5*(b-tw)
    actual=flange_relative_slenderness(outstand,tf,ry,elastic)
    try:
        limit=flange_slenderness_limit(group,member_lambda,edge)
    except (TypeError,ValueError) as exc:
        return _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 7.3.8 Table 10"], reason=str(exc))
    return _util_ev(actual/limit, source="SP16-MECH7 Table 10 I-section flange local stability", scope=["SP16 7.3.8 Table 10"])

def bind_primary_ambient_evidence(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Bind qualified SP16 ambient verification procedures to the primary MECH7 load-case state.

    Standard reference:
        SP 16.13330.2017 Sections 7-10 and the qualified N3-N10 procedures consumed by the cumulative package; Audit ID: SP16-MECH7-BIND-001.

    Parameters:
        values: Cumulative guided-runtime quantity mapping containing the MECH2 applicability census, MECH3-MECH5 mechanics state, section properties, material resistances and any required explicit applicability classifications.

    Returns:
        Mapping containing ``sp16_mech7_primary_evidence`` rows and the primary-binding completeness flag consumed by the strict MECH6 gate.

    Assumptions:
        All numerical producers referenced by a closed evidence route were qualified in earlier cumulative stages; absence of required evidence is never interpreted as PASS.

    Sign convention:
        Signed N, Mx, My, Qx, Qy, T and B values are preserved from the canonical MECH1 action state; N>0 denotes tension.

    Unit convention:
        Uses the canonical internal units declared by the active DAG (N, mm, MPa, N*mm and N*mm^2 as applicable).

    Applicability:
        Primary ambient SP16 verification routes for geometries and checks explicitly supported by the cumulative N3-N10/MECH1-MECH7 implementation.

    Limitations:
        M+Q interaction, universal torsional resistance interaction, unsupported local-stability geometries, and required fatigue/brittle-fracture workflows remain fail-closed unless qualified evidence is present.

    Raises:
        FireUIError when the mandatory applicability census or required canonical quantity structure is missing or malformed.

    Examples:
        ``result = bind_primary_ambient_evidence(values)`` returns evidence for the downstream ``SP16_MECHANICAL_PASS`` aggregator.

    Tests:
        Covered by ``tests/test_sp16_mech7_primary_workflow.py`` and cumulative MECH6 gate integration tests.

    Implementation notes:
        The binder reuses qualified scalar functions and emits explicit evidence rows; it never converts stress recovery alone into normative PASS.
    """
    census = values.get("sp16_applicability_census")
    if not isinstance(census, Mapping):
        raise FireUIError("SP16-MECH7 requires sp16_applicability_census")
    if "active_checks" not in census or "context_driven_checks" not in census:
        raise FireUIError("SP16-MECH7 census is missing required check collections")
    active_checks = census["active_checks"]
    context_checks = census["context_driven_checks"]
    if not isinstance(active_checks, list) or not isinstance(context_checks, list):
        raise FireUIError("SP16-MECH7 census check collections must be lists")
    active_ids = {str(r["id"]) for r in active_checks if isinstance(r, Mapping) and "id" in r}
    context_ids = {str(r["id"]) for r in context_checks if isinstance(r, Mapping) and "id" in r}
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x")
    my = _num(values, "ambient_M_y")
    b = _num(values, "ambient_B_bimoment")
    evidence: dict[str, dict[str, Any]] = {}

    if "section_tension" in active_ids or "section_compression" in active_ids:
        target = "section_tension" if n > 0.0 else "section_compression"
        try:
            evidence[target] = _axial_strength(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence[target] = _ev("DEFERRED", source="SP16-MECH7 axial binding", scope=["SP16 7.1.1"], reason=str(exc))

    if "member_compression_stability" in active_ids:
        try:
            evidence["member_compression_stability"] = _compression_stability(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["member_compression_stability"] = _ev("DEFERRED", source="SP16-MECH7 compression stability binding", scope=["SP16 7.1.3"], reason=str(exc))

    if "effective_length_slenderness" in active_ids:
        try:
            evidence["effective_length_slenderness"] = _slenderness(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["effective_length_slenderness"] = _ev("DEFERRED", source="SP16-MECH7 Table 32 binding", scope=["SP16 10.4.1"], reason=str(exc))

    for cid, ux, uy, ub, scope in [
        ("bending_x", True, False, False, ["SP16 8.2.1 Eq.(43)"]),
        ("bending_y", False, True, False, ["SP16 8.2.1 Eq.(43)"]),
        ("biaxial_bending", True, True, False, ["SP16 8.2.1 Eq.(43)"]),
        ("bimoment_B", True, True, True, ["SP16 8.2.1 Eq.(43)"]),
    ]:
        if cid in active_ids:
            try:
                evidence[cid] = _util_ev(_eq43_governing(values, use_mx=ux, use_my=uy, use_b=ub), source="SP16-MECH7 pointwise Eq.(43)", scope=scope)
            except (FireUIError, KeyError, TypeError, ValueError) as exc:
                evidence[cid] = _ev("DEFERRED", source="SP16-MECH7 pointwise Eq.(43)", scope=scope, reason=str(exc))

    if "interaction_N_M" in active_ids:
        evidence["interaction_N_M"] = _nm_interaction(values, n, mx, my)

    # M+Q and free torsion remain explicit boundaries unless a dedicated qualified
    # normative interaction criterion is supplied by a later stage.
    if "interaction_M_Q" in active_ids:
        evidence["interaction_M_Q"] = _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 §8"], reason="qualified primary M+Q interaction binding is not yet available; pointwise mechanics alone is not PASS")
    if "torsion_T" in active_ids:
        evidence["torsion_T"] = _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 torsion mechanics"], reason="T stress recovery is available but a complete normative resistance interaction route is not yet bound")

    if "beam_ltb" in context_ids:
        try:
            evidence["beam_ltb"] = _ltb(values, mx, my)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["beam_ltb"] = _ev("DEFERRED", source="SP16-MECH7 LTB binding", scope=["SP16 8.4", "Annex Ж"], reason=str(exc))

    # Prefer explicit N6 evidence when present.  For central compression of the
    # qualified I-section, MECH7 can execute the existing Table 9/10 scalar
    # procedures directly after explicit diagram-group classification.
    for cid, qid in [("local_stability_web", "sp16_n6_web_status"), ("local_stability_flange", "sp16_n6_flange_status")]:
        if cid not in context_ids:
            continue
        if qid in values:
            status = values[qid]
            if status == "pass" or status is True:
                evidence[cid] = _ev("PASS", source=qid, scope=["SP16 local stability"])
                continue
            if status == "fail" or status is False:
                evidence[cid] = _ev("FAIL", source=qid, scope=["SP16 local stability"])
                continue
            if status == "reduced_area_recheck_required":
                evidence[cid] = _ev("DEFERRED", source=qid, scope=["SP16 local stability"], reason="reduced-area recheck required")
                continue
        if n < 0.0 and abs(mx) <= _EPS and abs(my) <= _EPS:
            evidence[cid] = _compression_local_stability(values, cid)
        else:
            evidence[cid] = _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 local stability"], reason="dedicated bending/beam-column local-stability workflow is not yet bound to the primary route")

    if "fatigue" in context_ids:
        required = values.get("sp16_mech7_fatigue_required")
        if required is False:
            evidence["fatigue"] = _ev("N.A.", source="sp16_mech7_fatigue_required", scope=["SP16 §12"], reason="engineer classified Section 12 fatigue as not applicable to this design situation")
        elif required is True:
            release = values.get("sp16_n9_release_gate")
            evidence["fatigue"] = _ev("PASS" if release is True else "FAIL" if release is False else "DEFERRED", source="SP16 N9" if release is not None else "SP16-MECH7", scope=["SP16 §12"], reason=None if release is not None else "fatigue is applicable; full N9 workflow evidence is required")
        else:
            evidence["fatigue"] = _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 §12"], reason="fatigue applicability is not classified")

    if "brittle_fracture" in context_ids:
        required = values.get("sp16_mech7_brittle_required")
        if required is False:
            evidence["brittle_fracture"] = _ev("N.A.", source="sp16_mech7_brittle_required", scope=["SP16 §13"], reason="engineer classified the dedicated Section 13 route as not applicable to this design situation")
        elif required is True:
            release = values.get("sp16_n10_release_gate")
            evidence["brittle_fracture"] = _ev("PASS" if release is True else "FAIL" if release is False else "DEFERRED", source="SP16 N10" if release is not None else "SP16-MECH7", scope=["SP16 §13"], reason=None if release is not None else "Section 13 review is applicable; full N10 workflow evidence is required")
        else:
            evidence["brittle_fracture"] = _ev("DEFERRED", source="SP16-MECH7", scope=["SP16 §13"], reason="brittle-fracture applicability is not classified")

    resolved = sorted(k for k, v in evidence.items() if v["status"] in {"PASS", "FAIL", "N.A."})
    deferred = sorted(k for k, v in evidence.items() if v["status"] == "DEFERRED")
    bundle = {
        "schema": "sp16_mech7_primary_ambient_evidence_v1",
        "evidence": evidence,
        "resolved_check_ids": resolved,
        "deferred_check_ids": deferred,
        "all_bound_checks_resolved": not deferred,
        "policy": "qualified scalar/workflow evidence only; unsupported interactions remain fail-closed",
    }
    return {
        "sp16_mech7_primary_evidence": bundle,
        "sp16_mech7_primary_binding_complete": not deferred,
    }


def _executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return bind_primary_ambient_evidence(values)


def build_sp16_mech7_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Extend the cumulative SP16 runtime with the MECH7 primary ambient evidence-binding executor.

    Standard reference:
        SP 16.13330.2017 ambient verification workflow orchestration over the already qualified N3-N10 procedures; Audit ID: SP16-MECH7-REG-001.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited guided executors.
        registry: Optional cumulative execution registry to extend in place.

    Returns:
        ExecutionRegistry containing all inherited MECH6 executors plus ``SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER``.

    Assumptions:
        The parent MECH6 registry and profile catalog satisfy their cumulative release contracts.

    Sign convention:
        The registry preserves the canonical signed N/Mx/My/Qx/Qy/T/B convention established by SP16-MECH1.

    Unit convention:
        Units are inherited from the active MECH7 DAG quantity declarations.

    Applicability:
        Guided ambient SP16 calculations using the cumulative MECH7 DAG.

    Limitations:
        Registering the binder does not imply that every N3-N10 primary-flow route is closed; unresolved applicable checks remain fail-closed in MECH6.

    Raises:
        Propagates inherited registry/catalog validation errors and duplicate-executor registration errors.

    Examples:
        ``registry = build_sp16_mech7_registry(InterimProfileCatalog())``.

    Tests:
        Covered by ``tests/test_sp16_mech7_primary_workflow.py`` and frontend registry/contract regression tests.

    Implementation notes:
        The function extends the MECH6 registry in place and registers only the MECH7 binder executor; strict gate semantics remain in MECH6.
    """
    reg = build_sp16_mech6_registry(catalog, registry)
    reg.register("SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER", _executor)
    return reg
