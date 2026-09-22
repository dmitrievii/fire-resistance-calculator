"""v0.85 numerical mesh and visualization overlay for SP554 12.5.

The frozen normative recurrence remains unchanged.  This layer replaces only
its numerical discretization policy and normalizes the sampled state trace so a
protection temperature field is never confused with the lumped steel node.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from . import fire_sp554_thermal as _thermal
from . import fire_ui23_protection_route as _route
from .fire_sp554_thermal_v084 import install_thermal_solver_patch as _install_v084

MIN_PROTECTION_INTERVALS = 12
MAX_PROTECTION_DX_MM = 1.5
MAX_PROTECTION_INTERVALS = 80
FOURIER_SAFETY_LIMIT = 0.25
MAX_TIME_STEP_MIN = 0.0025
_PATCHED = False
_V084_FDM_CASE = None
_V084_PROTECTED_FDM = None


def _converted_properties(model: Mapping[str, Any]) -> tuple[float, float, float, float, float]:
    rho = float(model["density_kg_m3"])
    A0 = float(model["conductivity_A_w_mk"])
    B = float(model.get("conductivity_B_w_mk2", 0.0))
    C0 = float(model["heat_capacity_C_j_kgk"])
    D = float(model.get("heat_capacity_D_j_kgk2", 0.0))
    basis = str(model.get("temperature_basis") or "degC")
    if basis == "K":
        A = A0 + B * 273.15
        C = C0 + D * 273.15
    elif basis == "degC":
        A, C = A0, C0
    else:
        raise ValueError("protection_model.temperature_basis must be K or degC")
    if rho <= 0.0:
        raise ValueError("protection density must be > 0")
    return rho, A, B, C, D


def select_fvm_discretization(case: Mapping[str, Any], thickness_mm: float) -> dict[str, Any]:
    """Select a mesh and explicit time step from geometry and thermal diffusivity.

    This is a project numerical-control policy, not a material property from
    SP554.  It requires at least 12 equal intervals and no interval wider than
    1.5 mm.  The time increment is then limited by Fo <= 0.25 using the largest
    material diffusivity sampled over the thermal range up to 1200 C.
    """
    if not math.isfinite(float(thickness_mm)) or float(thickness_mm) <= 0.0:
        raise ValueError("protection thickness must be finite and > 0")
    thickness = float(thickness_mm)
    n = max(MIN_PROTECTION_INTERVALS, int(math.ceil(thickness / MAX_PROTECTION_DX_MM)))
    if n > MAX_PROTECTION_INTERVALS:
        raise ValueError(
            f"automatic FVM mesh requires {n} intervals (> {MAX_PROTECTION_INTERVALS}); "
            "the current production discretization scope is exceeded"
        )
    dx_mm = thickness / n
    dx_m = dx_mm / 1000.0
    model = case.get("protection_model")
    if not isinstance(model, Mapping):
        raise ValueError("protection_model is unresolved")
    rho, A, B, C, D = _converted_properties(model)
    initial = float(case.get("initial_temperature_c", 20.0))
    target = float(case.get("critical_temperature_c", 800.0))
    upper = max(initial, target, 1200.0)
    alpha_max = 0.0
    governing_t = initial
    # Sample a nonlinear k(T)/(rho*c(T)) envelope. Linear k/c functions have no
    # hidden oscillation, but the explicit sampling keeps the policy auditable.
    for i in range(121):
        t = initial + (upper - initial) * i / 120.0
        k = A + B * t
        cp = C + D * t
        if k <= 0.0 or cp <= 0.0:
            raise ValueError("protection thermal properties became non-positive inside the mesh-control range")
        alpha = k / (rho * cp)
        if alpha > alpha_max:
            alpha_max = alpha
            governing_t = t
    if alpha_max <= 0.0 or not math.isfinite(alpha_max):
        raise ValueError("maximum protection thermal diffusivity is invalid")
    stable_dt_s = FOURIER_SAFETY_LIMIT * dx_m * dx_m / alpha_max
    dt_min = min(MAX_TIME_STEP_MIN, stable_dt_s / 60.0)
    if dt_min <= 0.0 or not math.isfinite(dt_min):
        raise ValueError("automatic FVM time step is invalid")
    fourier = alpha_max * dt_min * 60.0 / (dx_m * dx_m)
    return {
        "policy_id": "sp554_v085_auto_mesh_dx15_fo025",
        "interval_count": n,
        "dx_mm": dx_mm,
        "time_step_min": dt_min,
        "fourier_number_max": fourier,
        "fourier_limit": FOURIER_SAFETY_LIMIT,
        "alpha_max_m2_s": alpha_max,
        "alpha_governing_temperature_c": governing_t,
        "min_intervals": MIN_PROTECTION_INTERVALS,
        "max_dx_mm": MAX_PROTECTION_DX_MM,
        "max_intervals": MAX_PROTECTION_INTERVALS,
        "status": "QUALIFIED_PROJECT_NUMERICAL_POLICY",
    }


def _fdm_case_v085(values: Mapping[str, Any], thickness_mm: float) -> dict[str, Any]:
    assert _V084_FDM_CASE is not None
    case = dict(_V084_FDM_CASE(values, thickness_mm))
    policy = select_fvm_discretization(case, thickness_mm)
    model = dict(case["protection_model"])
    model["layer_count"] = int(policy["interval_count"])
    case["protection_model"] = model
    case["time_step_min"] = float(policy["time_step_min"])
    case["v085_mesh_policy"] = copy.deepcopy(policy)
    return case


def _normalize_visualization(result: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(result)
    vis = out.get("visualization")
    if not isinstance(vis, Mapping):
        return out
    vis2 = copy.deepcopy(dict(vis))
    n = int(vis2.get("layer_count") or 0)
    thickness = float(vis2.get("protection_thickness_mm") or 0.0)
    dx = float(vis2.get("dx_mm") or (thickness / n if n else 0.0))
    protection_positions = [i * dx for i in range(n)]
    profiles = []
    for row in vis2.get("profile_samples") or []:
        temps = [float(v) for v in row.get("temperatures_c") or []]
        if len(temps) != n + 1:
            continue
        profiles.append({
            "time_min": float(row["time_min"]),
            "protection_node_positions_mm": list(protection_positions),
            "protection_temperatures_c": temps[:n],
            "steel_interface_position_mm": thickness,
            "steel_temperature_c": temps[-1],
        })
    vis2["schema"] = "sp554_v085_fvm_visualization_v2"
    vis2["mesh_policy"] = copy.deepcopy(case.get("v085_mesh_policy") or {})
    vis2["protection_node_positions_mm"] = list(protection_positions)
    vis2["steel_interface_position_mm"] = thickness
    vis2["profile_samples"] = profiles
    if profiles:
        final = max(profiles, key=lambda r: float(r["time_min"]))
        vis2["final_state"] = copy.deepcopy(final)
        ptemps = list(final["protection_temperatures_c"])
        gradients = []
        for i in range(max(0, len(ptemps) - 1)):
            gradients.append({
                "x_mid_mm": 0.5 * (protection_positions[i] + protection_positions[i + 1]),
                "dT_dx_c_per_mm": (ptemps[i + 1] - ptemps[i]) / dx,
            })
        if ptemps and dx > 0.0:
            gradients.append({
                "x_mid_mm": thickness - 0.5 * dx,
                "dT_dx_c_per_mm": (float(final["steel_temperature_c"]) - ptemps[-1]) / dx,
                "segment": "last_protection_node_to_lumped_steel_interface",
            })
        vis2["final_state"]["temperature_gradients_c_per_mm"] = gradients
    out["visualization"] = vis2
    return out


def _protected_fdm_v085(case: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    assert _V084_PROTECTED_FDM is not None
    result = _V084_PROTECTED_FDM(case, delta_mm)
    # Preserve exact v0.84 behavior for callers that did not opt into the v0.85
    # numerical policy.  This keeps cumulative regression order-independent.
    if not isinstance(case.get("v085_mesh_policy"), Mapping):
        return result
    return _normalize_visualization(result, case)


MESH_CONVERGENCE_ABS_TOL_MIN = 0.05
MESH_CONVERGENCE_REL_TOL = 0.001
MAX_REFINED_PROTECTION_INTERVALS = 160


def _policy_for_interval_count(case: Mapping[str, Any], thickness_mm: float, interval_count: int) -> dict[str, Any]:
    """Return the same explicit-stability policy for a prescribed mesh density."""
    base = select_fvm_discretization(case, thickness_mm)
    n = int(interval_count)
    if n < 1 or n > MAX_REFINED_PROTECTION_INTERVALS:
        raise ValueError(f"refined FVM interval count {n} is outside 1..{MAX_REFINED_PROTECTION_INTERVALS}")
    dx_mm = float(thickness_mm) / n
    dx_m = dx_mm / 1000.0
    alpha_max = float(base["alpha_max_m2_s"])
    dt_min = min(MAX_TIME_STEP_MIN, FOURIER_SAFETY_LIMIT * dx_m * dx_m / alpha_max / 60.0)
    fourier = alpha_max * dt_min * 60.0 / (dx_m * dx_m)
    out = dict(base)
    out.update({
        "policy_id": "sp554_v085_refined_mesh_convergence",
        "interval_count": n,
        "dx_mm": dx_mm,
        "time_step_min": dt_min,
        "fourier_number_max": fourier,
        "max_refined_intervals": MAX_REFINED_PROTECTION_INTERVALS,
    })
    return out


def case_with_interval_count(case: Mapping[str, Any], thickness_mm: float, interval_count: int) -> dict[str, Any]:
    """Clone a 12.5 case onto a prescribed stable equal-interval mesh."""
    cloned = copy.deepcopy(dict(case))
    policy = _policy_for_interval_count(cloned, thickness_mm, interval_count)
    model = dict(cloned["protection_model"])
    model["layer_count"] = int(policy["interval_count"])
    model["thickness_mm"] = float(thickness_mm)
    cloned["protection_model"] = model
    cloned["time_step_min"] = float(policy["time_step_min"])
    cloned["v085_mesh_policy"] = policy
    return cloned


def mesh_convergence_check(
    case: Mapping[str, Any],
    delta_mm: float,
    *,
    coarse_result: Mapping[str, Any] | None = None,
    keep_visualization_on_refined: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compare the production mesh with a doubled mesh and return the refined result.

    The acceptance criterion is a project numerical-control rule, not an SP554
    material rule: |Δt_R| <= 0.05 min OR <= 0.1 % between n and 2n.  The
    refined 2n result is retained as the engineering result when the check passes.
    """
    assert _V084_PROTECTED_FDM is not None
    model = case.get("protection_model")
    if not isinstance(model, Mapping):
        raise ValueError("protection_model is unresolved")
    thickness = float(model["thickness_mm"])
    n = int(model["layer_count"])
    n_refined = 2 * n
    if n_refined > MAX_REFINED_PROTECTION_INTERVALS:
        raise ValueError(
            f"mesh-convergence check requires {n_refined} intervals (> {MAX_REFINED_PROTECTION_INTERVALS}); "
            "the current production refinement scope is exceeded"
        )

    coarse_case = copy.deepcopy(dict(case))
    coarse_case.pop("visualization_sample_interval_min", None)
    if coarse_result is None or coarse_result.get("calculated_time_min") is None:
        coarse_result = _V084_PROTECTED_FDM(coarse_case, delta_mm)
    coarse_time = coarse_result.get("calculated_time_min")
    if coarse_time is None:
        raise ValueError("mesh-convergence check requires a completed coarse-grid 12.5 result")

    refined_case = case_with_interval_count(case, thickness, n_refined)
    if not keep_visualization_on_refined:
        refined_case.pop("visualization_sample_interval_min", None)
    refined_result = _V084_PROTECTED_FDM(refined_case, delta_mm)
    if refined_result.get("calculated_time_min") is None:
        raise ValueError("mesh-convergence check requires a completed refined-grid 12.5 result")
    refined_time = float(refined_result["calculated_time_min"])
    coarse_time = float(coarse_time)
    abs_diff = abs(refined_time - coarse_time)
    rel_diff = abs_diff / max(abs(refined_time), 1e-12)
    passed = abs_diff <= MESH_CONVERGENCE_ABS_TOL_MIN or rel_diff <= MESH_CONVERGENCE_REL_TOL
    evidence = {
        "status": "PASS" if passed else "FAIL",
        "criterion": "abs(delta_t_R)<=0.05 min OR rel(delta_t_R)<=0.1%",
        "criterion_type": "PROJECT_NUMERICAL_CONTROL_NOT_NORMATIVE_MATERIAL_PROPERTY",
        "coarse_interval_count": n,
        "refined_interval_count": n_refined,
        "coarse_dx_mm": thickness / n,
        "refined_dx_mm": thickness / n_refined,
        "coarse_fire_resistance_min": coarse_time,
        "refined_fire_resistance_min": refined_time,
        "absolute_difference_min": abs_diff,
        "relative_difference": rel_diff,
        "relative_difference_percent": 100.0 * rel_diff,
    }
    if not passed:
        raise ValueError(
            "protected FVM mesh-convergence criterion failed: "
            f"n={n} -> {n_refined}, Δt_R={abs_diff:.6g} min ({100.0*rel_diff:.4g}%)"
        )
    refined_out = _normalize_visualization(refined_result, refined_case)
    refined_out = dict(refined_out)
    refined_out["mesh_convergence"] = evidence
    vis = refined_out.get("visualization")
    if isinstance(vis, Mapping):
        vis2 = copy.deepcopy(dict(vis))
        policy = dict(vis2.get("mesh_policy") or {})
        policy.update({
            "coarse_interval_count": n,
            "refined_interval_count": n_refined,
            "mesh_convergence_status": "PASS",
            "mesh_convergence_abs_difference_min": abs_diff,
            "mesh_convergence_relative_difference_percent": 100.0 * rel_diff,
        })
        vis2["mesh_policy"] = policy
        vis2["mesh_convergence"] = copy.deepcopy(evidence)
        refined_out["visualization"] = vis2
    return evidence, refined_out

def install_thermal_solver_patch() -> None:
    global _PATCHED, _V084_FDM_CASE, _V084_PROTECTED_FDM
    if _PATCHED:
        return
    _install_v084()
    _V084_FDM_CASE = _route._fdm_case
    _V084_PROTECTED_FDM = _thermal._protected_fdm
    _route._fdm_case = _fdm_case_v085
    _thermal._protected_fdm = _protected_fdm_v085
    _PATCHED = True


__all__ = [
    "FOURIER_SAFETY_LIMIT", "MAX_PROTECTION_DX_MM", "MAX_PROTECTION_INTERVALS",
    "MIN_PROTECTION_INTERVALS", "MAX_REFINED_PROTECTION_INTERVALS",
    "MESH_CONVERGENCE_ABS_TOL_MIN", "MESH_CONVERGENCE_REL_TOL",
    "case_with_interval_count", "install_thermal_solver_patch", "mesh_convergence_check",
    "select_fvm_discretization",
]
