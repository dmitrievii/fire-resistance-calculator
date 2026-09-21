"""FIRE-BRIDGE2 typed handoff from qualified SP16 state into SP554 fire mechanics.

The bridge deliberately separates three questions that were previously mixed in
one legacy Qy/T fail-closed terminal:

1. Has the ambient member passed the strict SP16 mechanical gate?
2. Is the FIRE_LOAD_CASE pointwise normal-stress state complete and traceable?
3. Does SP554 provide a qualified fire-resistance route for every active action?

SP554 clause 8.7 is treated only as a normal-stress route for gamma_T.  It is
not used as a universal substitute for missing transverse-shear or torsion fire
checks.  Therefore non-zero Qy or T remains fail-closed in v0.67 even though
SP16-MECH3/4 can mechanically recover the associated stress fields.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech9_remaining_ambient import build_sp16_mech9_registry
from .sp16_mech7_runtime_remediation import install_sp16_mech7_v072_remediation

_EPS = 1.0e-12


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise FireUIError(f"{name} must be finite")
    return result


def _governing_normal_stress(pointwise_state: Mapping[str, Any]) -> tuple[float, dict[str, Any]]:
    if not isinstance(pointwise_state, Mapping):
        raise FireUIError("fire_complete_pointwise_stress_state must be an object")
    if pointwise_state["normal_stress_complete"] is not True:
        raise FireUIError("FIRE-BRIDGE2 requires complete normal-stress recovery")
    points = pointwise_state["points"]
    if not isinstance(points, list) or not points:
        raise FireUIError("FIRE-BRIDGE2 requires non-empty pointwise stress points")
    rows: list[tuple[float, dict[str, Any]]] = []
    for point in points:
        if not isinstance(point, Mapping):
            raise FireUIError("pointwise stress point must be an object")
        sigma = _finite_number(point["sigma_N_Mx_My_B_n_mm2"], "sigma_N_Mx_My_B_n_mm2")
        rows.append((abs(sigma), dict(point)))
    magnitude, row = max(rows, key=lambda item: item[0])
    return magnitude, row


def _classify_fire_bridge2_handoff(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Classify the qualified SP16-to-SP554 handoff and derive an internal clause-8.7 normal-stress value from the same-point FIRE mechanical state.

    Standard reference:
        SP 554.1311500.2026 clause 4.1 (SP16 mechanical basis), clause 8.7 (gamma_T from static-analysis normal stress), Sections 9-11 explicit member fire checks.  SP16 mechanics are supplied by the cumulative MECH1-MECH9 layer.

    Parameters:
        values: Resolved guided-session quantities containing ``sp16_mechanical_pass``, canonical FIRE actions ``Q_y`` and ``T_torsion``, and ``fire_complete_pointwise_stress_state``.

    Returns:
        A dictionary containing a typed bridge contract and route status. The governing absolute normal stress in MPa/N/mm2 is produced only when complete pointwise normal-stress recovery is available for the internal clause-8.7 route.

    Assumptions:
        The FIRE_LOAD_CASE is already materialized after the strict ambient SP16 gate.  The pointwise state is a 20 C mechanical characterization and retains the canonical signed N/M/Q/T/B semantics.

    Sign convention:
        Point stresses preserve their signed SP16 recovery convention.  Clause 8.7 uses the governing absolute normal-stress magnitude, consistent with the existing SP554 runtime which evaluates ``abs(sigma_n_static)``.

    Unit convention:
        Stress is N/mm2, numerically equal to MPa.  Canonical actions retain package units from prior MECH stages.

    Applicability:
        v0.67 FIRE-BRIDGE2.  Full transition into existing SP554 Sections 9-11 or internal clause-8.7 execution is qualified only when ``Qy=0`` and ``T=0``.  Biaxial bending and direct B are permitted in the normal-stress state when their upstream pointwise recovery is complete.

    Limitations:
        Non-zero Qy and/or general torsion T remain fail-closed because SP554 clause 8.7 does not replace missing shear/torsion fire checks.  This stage does not invent a resultant Q, does not map Qy to Qx, and does not derive B from T.

    Raises:
        FireUIError for an explicit false SP16 gate, malformed available pointwise stress data, or non-finite actions/stresses. An incomplete pointwise normal-stress state does not block explicit Sections 9-11 routes; it only makes the internal clause-8.7 route unavailable.

    Examples:
        A qualified FIRE state with Qy=T=0 and complete N/Mx/My/B pointwise stress returns ``FULLY_SUPPORTED`` and a derived internal ``sigma_n_static`` value.

    Tests:
        ``tests/test_fire_bridge2_qualified_state.py`` covers full explicit handoff, internal clause-8.7 stress derivation, and Qy/T fail-closed classifications.

    Implementation notes:
        A derived clause-8.7 stress value may be available diagnostically even for a blocked Qy/T state, but ``internal_8_7_full_route_allowed`` is false unless all active actions are covered by the current SP554 fire runtime.
    """
    if "sp16_mechanical_pass" in values and values["sp16_mechanical_pass"] is not True:
        raise FireUIError("FIRE-BRIDGE2 requires SP16_MECHANICAL_PASS = true")
    pass_state: Any = True if "sp16_mechanical_pass" in values else "CONTROL_FLOW_PRECONDITION"

    qy = _finite_number(values["Q_y"], "Q_y")
    torsion = _finite_number(values["T_torsion"], "T_torsion")

    pointwise_state = values["fire_complete_pointwise_stress_state"]
    normal_available = False
    sigma_abs: float | None = None
    governing_point: dict[str, Any] | None = None
    if isinstance(pointwise_state, Mapping):
        if "normal_stress_complete" in pointwise_state and pointwise_state["normal_stress_complete"] is True:
            if "points" in pointwise_state:
                points = pointwise_state["points"]
                if isinstance(points, list) and points:
                    sigma_abs, governing_point = _governing_normal_stress(pointwise_state)
                    normal_available = True

    unsupported: list[str] = []
    if abs(qy) > _EPS:
        unsupported.append("Qy")
    if abs(torsion) > _EPS:
        unsupported.append("T")

    if not unsupported:
        status = "FULLY_SUPPORTED"
        full = True
        reason = "All active actions are within the current explicit SP554/qualified normal-stress handoff scope."
    elif unsupported == ["Qy"]:
        status = "FAIL_CLOSED_QY"
        full = False
        reason = "Qy mechanics is available upstream, but a qualified SP554 fire-resistance handoff for this transverse shear component is not closed."
    elif unsupported == ["T"]:
        status = "FAIL_CLOSED_T"
        full = False
        reason = "Free-torsion mechanics is available upstream, but SP554 has no project-qualified universal fire-resistance route for arbitrary T."
    else:
        status = "FAIL_CLOSED_QY_T"
        full = False
        reason = "Both Qy and T require fire-specific checks that are not replaced by SP554 clause 8.7."

    contract = {
        "schema": "fire_bridge2_qualified_sp16_state_v1",
        "status": status,
        "sp16_mechanical_pass_required": True,
        "sp16_mechanical_pass": pass_state,
        "full_sp554_handoff_closed": full,
        "explicit_sections_9_11_route_allowed": full,
        "internal_8_7_normal_stress_available": normal_available,
        "internal_8_7_full_route_allowed": full and normal_available,
        "unsupported_fire_actions": unsupported,
        "Qy_to_Qx_substitution_forbidden": True,
        "T_to_B_substitution_forbidden": True,
        "clause_8_7_not_universal_shear_or_torsion_bypass": True,
        "sigma_n_static_abs_n_mm2": sigma_abs,
        "sigma_n_static_source": "SP16_MECH5_fire_complete_pointwise_stress_state" if normal_available else None,
        "governing_normal_stress_point": governing_point,
        "reason": reason,
    }
    result: dict[str, Any] = {
        "fire_bridge2_contract": contract,
        "fire_bridge2_route_status": status,
        "fire_bridge2_full_handoff_closed": full,
    }
    if normal_available and sigma_abs is not None:
        result["fire_bridge2_sigma_n_static"] = sigma_abs
    return result


def _bridge_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return _classify_fire_bridge2_handoff(values)


def _internal_8_7_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    contract = values["fire_bridge2_contract"]
    if not isinstance(contract, Mapping):
        raise FireUIError("fire_bridge2_contract must be an object")
    if contract["internal_8_7_full_route_allowed"] is not True:
        raise FireUIError("internal SP554 8.7 route is blocked by unresolved Qy/T fire checks")
    sigma = _finite_number(values["fire_bridge2_sigma_n_static"], "fire_bridge2_sigma_n_static")
    if sigma <= 0.0:
        raise FireUIError("SP554 8.7 requires a positive governing normal-stress magnitude")
    return {"sigma_n_static": sigma}


def _build_fire_bridge2_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Extend the cumulative v0.66 execution registry with FIRE-BRIDGE2 typed handoff and internal clause-8.7 stress producers.

    Standard reference:
        SP 554.1311500.2026 clauses 4.1 and 8.7 plus Sections 9-11; upstream mechanics and PASS evidence remain governed by current SP16.

    Parameters:
        catalog: Interim profile catalogue used by all inherited guided executors. registry: Optional existing registry to extend.

    Returns:
        ExecutionRegistry containing all SP16-MECH1..9/FIRE executors plus FIRE-BRIDGE2 node executors.

    Assumptions:
        Used with DAG v0.3.70 and the FIRE-BRIDGE2 presentation policy.

    Sign convention:
        Inherited canonical signed-action convention; no axis/action remapping is performed.

    Unit convention:
        Inherited canonical units; internal clause-8.7 stress is N/mm2 (MPa).

    Applicability:
        Cumulative v0.67 guided runtime.

    Limitations:
        Does not close non-zero Qy or arbitrary T fire resistance.  Does not alter existing SP554 Sections 9-11 formula executors.

    Raises:
        Propagates catalogue/registry construction errors and FIRE-BRIDGE2 input-contract violations.

    Examples:
        ``_build_fire_bridge2_registry(InterimProfileCatalog())`` builds the registry used by the v0.67 local application.

    Tests:
        ``tests/test_fire_bridge2_qualified_state.py`` and cumulative FIRE-UI regression tests.

    Implementation notes:
        Existing external ``software_static_stress`` clause-8.7 authoring remains available alongside the new internally derived qualified SP16 pointwise-stress option.
    """
    reg = build_sp16_mech9_registry(catalog, registry)
    install_sp16_mech7_v072_remediation(reg)
    reg.register("SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE", _bridge_executor)
    reg.register("SP554_FIRE_BRIDGE2_C_INTERNAL_8_7_STRESS", _internal_8_7_executor)
    return reg
