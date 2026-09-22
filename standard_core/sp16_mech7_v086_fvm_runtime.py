"""v0.86 protected-FVM runtime: single production mesh and robust bounded search."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from . import fire_ui23_protection_route as _route
from .fire_sp554_thermal import sp554_fire_thermal_guided_workflow
from .sp16_mech7_v085_fvm_runtime import install_registry_remediation as _install_v085_registry

SEARCH_SAMPLE_COUNT = 9
THICKNESS_SEARCH_RESOLUTION_MM = 0.01
SEARCH_MAX_BISECTIONS = 16


def _run_case(values: Mapping[str, Any], thickness_mm: float, *, visualization: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one v0.85-qualified mesh; omit state sampling during search evaluations."""
    case = _route._fdm_case(values, float(thickness_mm))
    if not visualization:
        case.pop("visualization_sample_interval_min", None)
    try:
        result = sp554_fire_thermal_guided_workflow(case)
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    if result.get("status") != "COMPLETE" or result.get("actual_fire_resistance_min") is None:
        raise FireUIError(result.get("diagnostic") or f"SP554 12.5 FVM failed at thickness {thickness_mm:g} mm")
    return case, dict(result)


def _direct_fdm_12_5_v086(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    thickness = _route._finite(values, "protection_candidate_thickness_mm", positive=True)
    _case, result = _run_case(values, thickness, visualization=True)
    return {
        "protection_thickness_mm": float(thickness),
        "protected_fire_resistance_min": float(result["actual_fire_resistance_min"]),
        "protection_12_5_calculation_trace": result,
    }


def _ceil_to_resolution(value: float, resolution: float) -> float:
    return math.ceil((float(value) - 1e-12) / resolution) * resolution


def _inverse_fdm_12_5_v086(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Find the first feasible thickness inside the explicit engineer-specified bounds.

    The search deliberately does not demand global numerical monotonicity. It scouts
    the full bounded interval, identifies the first sampled infeasible->feasible
    crossing, then refines only that local bracket. Search evaluations do not collect
    visualization traces; only the final selected thickness does.
    """
    required = _route._finite(values, "required_fire_resistance_min", positive=True)
    lo = _route._finite(values, "protection_search_min_thickness_mm", positive=True)
    hi = _route._finite(values, "protection_search_max_thickness_mm", positive=True)
    if hi <= lo:
        raise FireUIError("protection_search_max_thickness_mm must be greater than protection_search_min_thickness_mm")

    cache: dict[float, float] = {}
    failed: dict[float, str] = {}

    def evaluate(thickness: float) -> float:
        key = round(float(thickness), 9)
        if key in cache:
            return cache[key]
        if key in failed:
            raise FireUIError(failed[key])
        try:
            _case, result = _run_case(values, key, visualization=False)
        except FireUIError as exc:
            failed[key] = str(exc)
            raise
        resistance = float(result["actual_fire_resistance_min"])
        cache[key] = resistance
        return resistance

    r_lo = evaluate(lo)
    if r_lo >= required:
        selected = lo
        bracket = [lo, lo]
        scout_rows = [{"thickness_mm": lo, "fire_resistance_min": r_lo}]
    else:
        xs = [lo + (hi - lo) * i / (SEARCH_SAMPLE_COUNT - 1) for i in range(SEARCH_SAMPLE_COUNT)]
        scout_rows: list[dict[str, Any]] = [{"thickness_mm": lo, "fire_resistance_min": r_lo}]
        previous_x, previous_r = lo, r_lo
        crossing: tuple[float, float] | None = None
        best = (r_lo, lo)

        for x in xs[1:]:
            try:
                r = evaluate(x)
                scout_rows.append({"thickness_mm": float(x), "fire_resistance_min": r})
            except FireUIError as exc:
                scout_rows.append({"thickness_mm": float(x), "error": str(exc)})
                continue
            if r > best[0]:
                best = (r, float(x))
            if crossing is None and previous_r < required <= r:
                crossing = (previous_x, float(x))
                break
            previous_x, previous_r = float(x), r

        if crossing is None:
            feasible = [r for r in scout_rows if isinstance(r.get("fire_resistance_min"), (int, float)) and float(r["fire_resistance_min"]) >= required]
            if feasible:
                first = min(feasible, key=lambda row: float(row["thickness_mm"]))
                x_hi = float(first["thickness_mm"])
                lower = [r for r in scout_rows if isinstance(r.get("fire_resistance_min"), (int, float)) and float(r["thickness_mm"]) < x_hi and float(r["fire_resistance_min"]) < required]
                if lower:
                    x_lo = max(lower, key=lambda row: float(row["thickness_mm"]))["thickness_mm"]
                    crossing = (float(x_lo), x_hi)
                else:
                    selected = x_hi
                    bracket = [x_hi, x_hi]
            else:
                raise FireUIError(
                    "Required fire resistance was not found inside the engineer-specified thickness-search domain. "
                    f"Best completed scout result: R={best[0]:.3f} min at δ={best[1]:.3f} mm; "
                    f"required R={required:.3f} min; domain {lo:g}..{hi:g} mm. "
                    "No extrapolation beyond the upper bound was used."
                )

        if crossing is not None:
            bracket_lo, bracket_hi = crossing
            for _ in range(SEARCH_MAX_BISECTIONS):
                if bracket_hi - bracket_lo <= THICKNESS_SEARCH_RESOLUTION_MM:
                    break
                mid = 0.5 * (bracket_lo + bracket_hi)
                try:
                    r_mid = evaluate(mid)
                except FireUIError:
                    bracket_lo = mid
                    continue
                if r_mid >= required:
                    bracket_hi = mid
                else:
                    bracket_lo = mid
            selected = min(hi, _ceil_to_resolution(bracket_hi, THICKNESS_SEARCH_RESOLUTION_MM))
            bracket = [bracket_lo, bracket_hi]

    _case, final = _run_case(values, selected, visualization=True)
    final_r = float(final["actual_fire_resistance_min"])
    while final_r < required and selected + THICKNESS_SEARCH_RESOLUTION_MM <= hi + 1e-12:
        selected = min(hi, selected + THICKNESS_SEARCH_RESOLUTION_MM)
        _case, final = _run_case(values, selected, visualization=True)
        final_r = float(final["actual_fire_resistance_min"])
    if final_r < required:
        raise FireUIError(
            "A feasible scout bracket was found, but the final conservative thickness could not satisfy the requirement "
            f"inside {lo:g}..{hi:g} mm. Last result: δ={selected:.3f} mm, R={final_r:.3f} min < {required:.3f} min."
        )

    return {
        "protection_thickness_mm": float(selected),
        "protected_fire_resistance_min": final_r,
        "protection_12_5_calculation_trace": {
            "mode": "inverse_minimum_thickness_v086_first_feasible_crossing",
            "required_fire_resistance_min": required,
            "search_bounds_mm": [lo, hi],
            "scout_samples": scout_rows,
            "local_refinement_bracket_mm": bracket,
            "search_resolution_mm": THICKNESS_SEARCH_RESOLUTION_MM,
            "evaluations_without_visualization": len(cache),
            "failed_scout_evaluations": failed,
            "selected_result_basis": "single_qualified_production_mesh; final-only visualization trace",
            "selected_result": final,
            "no_extrapolation": True,
        },
    }


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    _install_v085_registry(registry)
    registry.register("SP554_C_12_5_DIRECT_PROTECTED_TIME", _direct_fdm_12_5_v086)
    registry.register("SP554_C_12_5_MINIMUM_THICKNESS_SEARCH", _inverse_fdm_12_5_v086)
    return registry


__all__ = [
    "SEARCH_SAMPLE_COUNT", "SEARCH_MAX_BISECTIONS", "THICKNESS_SEARCH_RESOLUTION_MM",
    "install_registry_remediation", "_direct_fdm_12_5_v086", "_inverse_fdm_12_5_v086",
]
