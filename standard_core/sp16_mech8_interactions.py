"""SP16-MECH8 M+Q normative interaction binding and torsion-scope reconciliation.

This stage closes explicitly supported SP16 bending-plus-shear routes without
turning pointwise mechanics into a normative PASS.  Free torsion T remains a
mechanics quantity unless a clause-specific SP16 resistance route applies.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .bending_members import (
    annex_e1_design_coefficients,
    annex_e1_plastic_coefficient_catalog,
    constrained_torsion_coefficient_table_10a,
    constrained_torsion_utilization_eq53,
    elastic_web_equivalent_stress_checks_eq44,
    plastic_bending_applicability,
    plastic_bending_utilization_eq50,
    plastic_biaxial_bending_utilization_eq51,
    plastic_shear_reduction_factor_eq52,
)
from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech7_primary_workflow import build_sp16_mech7_registry

_EPS = 1e-12
_VALID = {"PASS", "FAIL", "N.A.", "DEFERRED", "CONTEXT_UNRESOLVED"}


def _num(values: Mapping[str, Any], key: str, *, positive: bool = False) -> float:
    if key not in values:
        raise FireUIError(f"SP16-MECH8 requires {key}")
    raw = values[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise FireUIError(f"{key} must be numeric")
    value = float(raw)
    if not math.isfinite(value) or (positive and value <= 0.0):
        raise FireUIError(f"{key} has invalid value")
    return value


def _boolean(values: Mapping[str, Any], key: str) -> bool:
    if key not in values or not isinstance(values[key], bool):
        raise FireUIError(f"SP16-MECH8 requires boolean {key}")
    return bool(values[key])


def _text(values: Mapping[str, Any], key: str) -> str:
    if key not in values or not isinstance(values[key], str) or not values[key]:
        raise FireUIError(f"SP16-MECH8 requires {key}")
    return str(values[key])


def _ev(status: str, *, source: str, scope: list[str], utilization: float | None = None, reason: str | None = None, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if status not in _VALID:
        raise ValueError("invalid SP16-MECH8 evidence status")
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


def _geometry(values: Mapping[str, Any]) -> Mapping[str, Any]:
    geom = values.get("section_geometry_2d_normalized")
    if not isinstance(geom, Mapping):
        raise FireUIError("SP16-MECH8 requires normalized section geometry")
    return geom


def _shape(geometry: Mapping[str, Any]) -> str:
    raw = geometry.get("template")
    if not isinstance(raw, str):
        raw = geometry.get("shape_group")
    if not isinstance(raw, str):
        raise FireUIError("section geometry has no supported template")
    key = raw.strip().lower()
    aliases = {
        "i": "i_section", "i_section": "i_section", "i-section": "i_section",
        "rhs": "rhs_shs", "shs": "rhs_shs", "rhs_shs": "rhs_shs", "box": "rhs_shs",
    }
    return aliases[key] if key in aliases else key


def _mech3_components(values: Mapping[str, Any]) -> Mapping[str, Any]:
    state = values.get("ambient_axis_shear_state")
    if not isinstance(state, Mapping):
        raise FireUIError("ambient_axis_shear_state is missing")
    comp = state.get("clause_8_2_3_components")
    if not isinstance(comp, Mapping):
        raise FireUIError("SP16 8.2.3 component state is missing")
    return comp


def _pointwise_mech3(values: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    state = values.get("ambient_axis_shear_state")
    if not isinstance(state, Mapping):
        raise FireUIError("ambient_axis_shear_state is missing")
    rec = state.get("pointwise_recovery")
    if not isinstance(rec, Mapping):
        raise FireUIError("MECH3 pointwise recovery is missing")
    points = rec.get("points")
    if not isinstance(points, list) or not points:
        raise FireUIError("MECH3 pointwise recovery has no material points")
    return [p for p in points if isinstance(p, Mapping)]


def _class1_eq44(values: Mapping[str, Any]) -> dict[str, Any]:
    """Bind SP16 8.2.1 Eq.(44) for the explicitly supported I-beam Mx+Qx case."""
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x")
    my = _num(values, "ambient_M_y")
    qx = _num(values, "ambient_Q_x")
    qy = _num(values, "ambient_Q_y")
    b = _num(values, "ambient_B_bimoment")
    if abs(n) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)"], reason="Eq.(44) binder is limited to the beam M+Q route with N=0; N+M+Q requires a dedicated combined route")
    if abs(mx) <= _EPS or abs(qx) <= _EPS:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)"], reason="current Eq.(44) binder requires nonzero Mx and Qx")
    if abs(my) > _EPS or abs(qy) > _EPS or abs(b) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)"], reason="biaxial/B/Qy web interaction requires the dedicated two-plane/local-stress route and is not inferred from the one-plane Eq.(44) binder")
    if not _boolean(values, "sp16_mech8_eq44_no_transverse_local_stress"):
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)", "SP16 8.2.2 Eq.(47)"], reason="transverse/local web stress is present; sigma_y must be recovered explicitly at the same point")
    geom = _geometry(values)
    if _shape(geom) != "i_section":
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)"], reason="qualified same-point Eq.(44) binder currently supports the parametric I-section")
    h = float(geom["h_mm"]); tw = float(geom["tw_mm"]); tf = float(geom["tf_mm"])
    ixn = _num(values, "I_xn", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    rs = _num(values, "Rs_formula", positive=True)
    gamma = _num(values, "gamma_c_bending_strength", positive=True)
    comp = _mech3_components(values)
    if comp.get("applicable") is not True:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.1 Eq.(44)"], reason="qualified Qx component state is unavailable")
    alpha = float(comp["web_hole_alpha45"])
    points = _pointwise_mech3(values)
    web_half_height = h / 2.0 - tf
    web_half_width = tw / 2.0
    rows: list[dict[str, Any]] = []
    for point in points:
        x = float(point["x_mm"]); y = float(point["y_mm"])
        if abs(x) > web_half_width + 1e-9 or abs(y) > web_half_height + 1e-9:
            continue
        sigma_x = mx * y / ixn
        tau = alpha * float(point["tau_x_n_mm2"])
        check = elastic_web_equivalent_stress_checks_eq44(sigma_x, 0.0, tau, ry, rs, gamma)
        rows.append({"point_id": point["id"], "x_mm": x, "y_mm": y, "sigma_x_n_mm2": sigma_x, "sigma_y_n_mm2": 0.0, "tau_xy_n_mm2": tau, **check})
    if not rows:
        raise FireUIError("Eq.(44) binder found no web material points")
    governing = max(rows, key=lambda r: float(r["governing_utilization"]))
    return _util_ev(float(governing["governing_utilization"]), source="SP16-MECH8 pointwise Eq.(44)", scope=["SP16 8.2.1 Eq.(44)", "SP16 Eq.(45) where holes apply"], details={"same_point": True, "transverse_normal_stress_assumption": "explicit_zero_by_user_classification", "governing": governing, "checked_point_count": len(rows)})


def _table_e1(values: Mapping[str, Any], alpha_f: float, my_zero: bool) -> dict[str, float]:
    row_id = _text(values, "sp16_mech8_annex_e1_section_type")
    gamma_f = _num(values, "sp16_mech8_equivalent_load_safety_factor", positive=True)
    catalog = annex_e1_plastic_coefficient_catalog()
    rows = catalog["section_types"]
    if row_id not in rows:
        raise FireUIError("invalid Annex E Table E.1 row")
    ratio = None if rows[row_id].get("ratio_nodes") is None else alpha_f
    return annex_e1_design_coefficients(row_id, ratio, my_zero, gamma_f)


def _class2_plastic(values: Mapping[str, Any]) -> dict[str, Any]:
    """Bind SP16 8.2.3 equations (50)-(53) for explicitly supported class-2 beam states."""
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x")
    my = _num(values, "ambient_M_y")
    qx = _num(values, "ambient_Q_x")
    qy = _num(values, "ambient_Q_y")
    b = _num(values, "ambient_B_bimoment")
    if abs(n) > _EPS:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3"], reason="8.2.3 beam binder is limited to N=0; N+M+Q is not silently reduced to a beam-only formula")
    geom = _geometry(values)
    shape = _shape(geom)
    family = "i_section" if shape == "i_section" else "box_section" if shape == "rhs_shs" else ""
    if not family:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3"], reason="8.2.3 binder supports I and box sections only")
    comp = _mech3_components(values)
    if comp.get("applicable") is not True:
        return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3"], reason="SP16 8.2.3 Qx/Qy component state is unavailable")
    tau_x = float(comp["tau_x_effective_n_mm2"])
    tau_y = float(comp["tau_y_n_mm2"])
    aw = float(comp["A_w_mm2"]); af = float(comp["A_f_one_flange_mm2"])
    rs = _num(values, "Rs_formula", positive=True)
    required = _boolean(values, "sp16_mech8_required_clause_checks_confirmed")
    support = _boolean(values, "sp16_mech8_is_support_section")
    applicability = plastic_bending_applicability(2, family, _num(values, "fy_norm", positive=True), tau_x, rs, required, support)
    if applicability["permitted"] is not True:
        return _ev("DEFERRED", source="SP16-MECH8 8.2.3 applicability", scope=["SP16 8.2.3", "SP16 8.4.6", "SP16 8.5.8", "SP16 8.5.9", "SP16 8.5.18"], reason="8.2.3 applicability gates are not all satisfied", details={"failed_gates": applicability["failed_gates"]})
    alpha_f = af / aw
    coeff = _table_e1(values, alpha_f, abs(my) <= _EPS)
    beta = plastic_shear_reduction_factor_eq52(tau_x, rs, alpha_f)
    wx = _num(values, "W_xn_min", positive=True)
    wy = _num(values, "W_yn_min", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gamma = _num(values, "gamma_c_bending_strength", positive=True)
    common = {"c_x": coeff["c_x"], "c_y": coeff["c_y"], "beta": beta, "alpha_f": alpha_f, "tau_x_n_mm2": tau_x, "tau_y_n_mm2": tau_y, "table_e1_row": _text(values, "sp16_mech8_annex_e1_section_type")}

    if abs(b) <= _EPS and abs(my) <= _EPS:
        if abs(qy) > _EPS:
            return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3 Eq.(50)"], reason="Qy is nonzero while the one-plane Eq.(50) route is selected; no Qy interaction is inferred")
        u = plastic_bending_utilization_eq50(abs(mx), coeff["c_x"], beta, wx, ry, gamma)
        return _util_ev(u, source="SP16-MECH8 Eq.(50)+(52)+Table E.1", scope=["SP16 8.2.3 Eq.(50)", "SP16 Eq.(52)", "Annex E Table E.1"], details=common)

    if abs(b) <= _EPS and abs(my) > _EPS:
        if tau_y > 0.5 * rs + _EPS:
            return _ev("FAIL", source="SP16-MECH8 8.2.3 tau_y gate", scope=["SP16 8.2.3"], utilization=tau_y / (0.5 * rs), reason="tau_y exceeds 0.5 Rs for Eq.(51)", details=common)
        u = plastic_biaxial_bending_utilization_eq51(abs(mx), abs(my), coeff["c_x"], coeff["c_y"], beta, wx, wy, ry, gamma)
        return _util_ev(u, source="SP16-MECH8 Eq.(51)+(52)+Table E.1", scope=["SP16 8.2.3 Eq.(51)", "SP16 Eq.(52)", "Annex E Table E.1"], details=common)

    if abs(b) > _EPS and abs(my) <= _EPS and family == "i_section":
        if abs(qy) > _EPS:
            return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3 Eq.(53)"], reason="Eq.(53) Mx+B route is not extended to a nonzero Qy interaction")
        womega = _num(values, "W_omega_eff", positive=True)
        ratio = abs(mx) / (coeff["c_x"] * wx * ry * gamma)
        if ratio > 0.99 + _EPS:
            return _ev("FAIL", source="SP16-MECH8 Table 10a domain", scope=["SP16 8.2.3 Eq.(53)", "Table 10a"], utilization=ratio, reason="Table 10a independent ratio exceeds its printed 0.99 domain", details=common)
        c_omega = constrained_torsion_coefficient_table_10a(ratio)
        u = constrained_torsion_utilization_eq53(abs(mx), abs(b), coeff["c_x"], beta, wx, c_omega, womega, ry, gamma)
        detail = dict(common); detail.update({"table_10a_ratio": ratio, "c_omega": c_omega})
        return _util_ev(u, source="SP16-MECH8 Eq.(53)+(52)+Table E.1+Table 10a", scope=["SP16 8.2.3 Eq.(53)", "SP16 Eq.(52)", "Annex E Table E.1", "SP16 Table 10a"], details=detail)

    return _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 8.2.3"], reason="current qualified 8.2.3 binder does not cover simultaneous My and B or box-section B")


def bind_mech8_interaction_evidence(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Merge SP16-MECH8 bending-plus-shear normative evidence into the MECH7 ambient evidence bundle and explicitly reconcile free-torsion T scope.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; clauses 8.2.1 Eq.(44), 8.2.3 Eq.(50)-(53), Annex E Table E.1 and Table 10a.

    Parameters:
        values: Current guided-session quantities containing the MECH7 evidence bundle, ambient canonical actions, section/material data and explicit MECH8 applicability classifications.

    Returns:
        Mapping containing ``sp16_mech8_primary_evidence`` and completion/status diagnostics for the downstream strict MECH6 gate.

    Assumptions:
        Existing MECH3/MECH5 mechanics states and scalar SP16 functions were produced by the qualified cumulative parent release.

    Sign convention:
        Canonical signed N/Mx/My/Qx/Qy/T/B are preserved; SP16 formulas using magnitudes receive explicit absolute values only at the normative equation boundary.

    Unit convention:
        Forces are N, moments N*mm, bimoment N*mm2, lengths mm and stresses N/mm2 (MPa).

    Applicability:
        Ambient SP16 primary workflow after SP16-MECH7 evidence binding.

    Limitations:
        Class-1 Eq.(44) is closed only for the explicit I-beam Mx+Qx route with N=My=Qy=B=0 and explicit absence of transverse/local web stress. Class-2 8.2.3 is closed only for qualified I/box routes. Class 3 and universal arbitrary free-torsion resistance remain fail-closed.

    Raises:
        FireUIError for malformed mandatory parent evidence or required MECH8 inputs; underlying normative functions may raise TypeError/ValueError for invalid domains.

    Examples:
        ``bind_mech8_interaction_evidence(values)`` augments ``interaction_M_Q`` while retaining strict deferred evidence for unsupported torsion.

    Tests:
        ``tests/test_sp16_mech8_interactions.py`` plus cumulative SP16/FIRE-UI regression suites.

    Implementation notes:
        The stage never derives a universal T resistance criterion from Saint-Venant stress recovery. Such a criterion is absent from the generic SP16 member routes audited for this release, so ``torsion_T`` remains DEFERRED outside clause-specific checks.
    """
    parent = values.get("sp16_mech7_primary_evidence")
    if not isinstance(parent, Mapping):
        raise FireUIError("SP16-MECH8 requires sp16_mech7_primary_evidence")
    parent_ev = parent.get("evidence")
    if not isinstance(parent_ev, Mapping):
        raise FireUIError("SP16-MECH7 evidence bundle is malformed")
    evidence = {str(k): dict(v) for k, v in parent_ev.items() if isinstance(v, Mapping)}
    census = values.get("sp16_applicability_census")
    if not isinstance(census, Mapping):
        raise FireUIError("SP16-MECH8 requires sp16_applicability_census")
    active = census.get("active_checks")
    if not isinstance(active, list):
        raise FireUIError("SP16-MECH8 census active_checks is malformed")
    active_ids = {str(r["id"]) for r in active if isinstance(r, Mapping) and "id" in r}

    if "interaction_M_Q" in active_ids:
        section_class = _text(values, "sp16_section_class")
        try:
            if section_class == "1":
                evidence["interaction_M_Q"] = _class1_eq44(values)
            elif section_class == "2":
                evidence["interaction_M_Q"] = _class2_plastic(values)
            else:
                evidence["interaction_M_Q"] = _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 §8"], reason=f"M+Q primary binding for section class {section_class} is not qualified in MECH8; class-3 redistribution/related clause confirmations remain explicit")
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["interaction_M_Q"] = _ev("DEFERRED", source="SP16-MECH8", scope=["SP16 §8"], reason=str(exc))

    if "torsion_T" in active_ids:
        closed = values.get("ambient_torsion_runtime_closed")
        reason = "Free Saint-Venant T→tau_T mechanics is available, but current SP16 Appendix A defines It/B/Iω while the audited general member clauses do not provide one universal standalone arbitrary-T resistance equation; only clause-specific torsion routes may close this check."
        if closed is False:
            reason = "Free-torsion mechanics is unresolved for the selected geometry; universal normative T resistance is therefore also unresolved."
        evidence["torsion_T"] = _ev("DEFERRED", source="SP16-MECH8 torsion scope reconciliation", scope=["SP16 Appendix A: It/B/Iω", "SP16 clause-specific torsion routes"], reason=reason, details={"free_torsion_mechanics_closed": closed is True, "universal_torsion_normative_check_closed": False, "scope_reconciled": True})

    unresolved = sorted(k for k, row in evidence.items() if row.get("status") in {"DEFERRED", "CONTEXT_UNRESOLVED"})
    mq_complete = True
    if "interaction_M_Q" in active_ids:
        mq_row = evidence["interaction_M_Q"]
        mq_complete = mq_row.get("status") in {"PASS", "FAIL", "N.A."}
    torsion_reconciled = True
    if "torsion_T" in active_ids:
        torsion_row = evidence["torsion_T"]
        torsion_details = torsion_row.get("details")
        torsion_reconciled = isinstance(torsion_details, Mapping) and torsion_details.get("scope_reconciled") is True
    bundle = {
        "schema": "sp16_mech8_primary_evidence_v1",
        "parent_schema": parent.get("schema"),
        "evidence": evidence,
        "resolved_check_ids": sorted(k for k, row in evidence.items() if row.get("status") in {"PASS", "FAIL", "N.A."}),
        "deferred_check_ids": unresolved,
        "m_q_binding_complete": mq_complete,
        "torsion_scope_reconciled": torsion_reconciled,
        "universal_torsion_normative_check_closed": False,
    }
    return {
        "sp16_mech8_primary_evidence": bundle,
        "sp16_mech8_mq_binding_complete": bool(bundle["m_q_binding_complete"]),
        "sp16_mech8_torsion_scope_reconciled": bool(bundle["torsion_scope_reconciled"]),
    }


def _executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return bind_mech8_interaction_evidence(values)


def build_sp16_mech8_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Extend the cumulative runtime with the SP16-MECH8 M+Q interaction binder and torsion-scope reconciler.

    Standard reference:
        СП 16.13330.2017 clauses 8.2.1, 8.2.3, Annex E Table E.1 and Appendix A; Audit ID SP16-MECH8-REG-001.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited guided executors.
        registry: Optional cumulative execution registry to extend in place.

    Returns:
        ExecutionRegistry containing inherited MECH7 executors plus ``SP16_C_MECH8_INTERACTION_BINDER``.

    Assumptions:
        The parent MECH7 registry satisfies its cumulative release contract.

    Sign convention:
        Signed canonical N/Mx/My/Qx/Qy/T/B convention is preserved.

    Unit convention:
        Units follow the active MECH8 DAG declarations.

    Applicability:
        Guided ambient SP16 calculation using the cumulative MECH8 DAG.

    Limitations:
        Registry installation does not make unsupported class-3 M+Q or universal arbitrary T resistance applicable.

    Raises:
        Propagates inherited registry validation and duplicate-registration errors.

    Examples:
        ``build_sp16_mech8_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_sp16_mech8_interactions.py`` and cumulative frontend registry tests.

    Implementation notes:
        Strict SP16_MECHANICAL_PASS semantics remain owned by MECH6; MECH8 only supplies explicit evidence.
    """
    reg = build_sp16_mech7_registry(catalog, registry)
    reg.register("SP16_C_MECH8_INTERACTION_BINDER", _executor)
    return reg
