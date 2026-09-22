"""v0.84 executors and chart-data generation for SP554 thermal visualization."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_sp554_thermal_v084 import install_thermal_solver_patch
from .fire_sp554_thermal import (
    _standard_fire_temperature_c,
    _heat_transfer_coefficient_w_m2k,
    _steel_heat_capacity_j_kgk,
)
from .sp16_mech7_v084_thermal_visual_overlay import (
    UNPROTECTED_METHOD_NODE_ID,
    UNPROTECTED_METHOD_QID,
)

STANDARD_REDUCED_THICKNESSES_MM = (3.0, 5.0, 10.0, 15.0, 20.0)


def _number(values: Mapping[str, Any], key: str, default: float | None = None, *, positive: bool = False) -> float:
    value = values.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FireUIError(f"{key} must be a finite number")
    result = float(value)
    if positive and result <= 0.0:
        raise FireUIError(f"{key} must be > 0")
    return result


def automatic_unprotected_step_method(_values: Mapping[str, Any], _node: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {UNPROTECTED_METHOD_QID: "step_calculation"}


def _curve_for_thickness(
    *,
    reduced_thickness_mm: float,
    initial_temperature_c: float,
    horizon_min: float,
    sample_interval_min: float,
    dt_min: float,
    rho: float,
    c0: float,
    kc: float,
    eps: float,
    critical_temperature_c: float,
) -> tuple[list[dict[str, float]], float | None]:
    delta_m = reduced_thickness_mm / 1000.0
    steel_t = initial_temperature_c
    t = 0.0
    next_sample = 0.0
    points = [{"time_min": 0.0, "temperature_c": float(steel_t)}]
    crossing: float | None = 0.0 if critical_temperature_c <= steel_t else None
    while t < horizon_min - 1e-12:
        nt = min(t + dt_min, horizon_min)
        fire_t = _standard_fire_temperature_c(nt, initial_temperature_c)
        alpha = _heat_transfer_coefficient_w_m2k(fire_t, steel_t, eps)
        cp = _steel_heat_capacity_j_kgk(c0, kc, steel_t)
        next_steel = steel_t + (nt - t) * 60.0 * alpha * (fire_t - steel_t) / (rho * delta_m * cp)
        if not math.isfinite(next_steel) or next_steel < steel_t - 1e-9:
            raise FireUIError("SP554 v0.84 unprotected diagram recurrence became unstable")
        if crossing is None and next_steel >= critical_temperature_c:
            f = (critical_temperature_c - steel_t) / (next_steel - steel_t) if next_steel > steel_t else 0.0
            crossing = t + f * (nt - t)
        while next_sample + sample_interval_min <= nt + 1e-12:
            next_sample += sample_interval_min
            if next_sample > horizon_min + 1e-12:
                break
            f = (next_sample - t) / (nt - t) if nt > t else 1.0
            f = min(1.0, max(0.0, f))
            temp = steel_t + f * (next_steel - steel_t)
            points.append({"time_min": float(next_sample), "temperature_c": float(temp)})
        steel_t = next_steel
        t = nt
    if points[-1]["time_min"] < horizon_min - 1e-9:
        points.append({"time_min": float(horizon_min), "temperature_c": float(steel_t)})
    return points, crossing


def unprotected_heating_diagram(values: Mapping[str, Any], *, initial_temperature_c: float = 20.0) -> dict[str, Any]:
    """Generate the exact calculated chart data used by the v0.84 UI.

    The standard 3/5/10/15/20 mm curves and the actual reduced-thickness curve
    all use the same explicit SP554 12.1-12.4 recurrence.  ISO 834 / GOST
    30247.0 formula (1) is returned as a separate fire-temperature curve.
    """
    actual = _number(values, "delta_pr", positive=True)
    critical = _number(values, "critical_temperature_c")
    dt = min(_number(values, "sp554_dt_unprotected_min", 0.1, positive=True), 0.1)
    rho = _number(values, "sp554_steel_density_12_2", 7850.0, positive=True)
    c0 = _number(values, "sp554_steel_c0_12_2", 480.0, positive=True)
    kc = _number(values, "sp554_steel_c_temp_coeff_12_2", 0.00063)
    eps = _number(values, "sp554_eps_reduced_12_4", 0.5, positive=True)
    if eps > 1.0:
        raise FireUIError("sp554_eps_reduced_12_4 must be <= 1")

    # First obtain the actual crossing on a generous engineering horizon, then
    # choose a compact display domain.  This does not alter the production result.
    _, actual_crossing = _curve_for_thickness(
        reduced_thickness_mm=actual,
        initial_temperature_c=initial_temperature_c,
        horizon_min=180.0,
        sample_interval_min=2.0,
        dt_min=dt,
        rho=rho,
        c0=c0,
        kc=kc,
        eps=eps,
        critical_temperature_c=critical,
    )
    horizon = 60.0
    if actual_crossing is not None:
        horizon = max(60.0, min(180.0, math.ceil(actual_crossing * 1.20 / 5.0) * 5.0))
    sample_interval = 0.5

    series: list[dict[str, Any]] = []
    standard_crossings: dict[str, float | None] = {}
    for thickness in STANDARD_REDUCED_THICKNESSES_MM:
        pts, cross = _curve_for_thickness(
            reduced_thickness_mm=thickness,
            initial_temperature_c=initial_temperature_c,
            horizon_min=horizon,
            sample_interval_min=sample_interval,
            dt_min=dt,
            rho=rho,
            c0=c0,
            kc=kc,
            eps=eps,
            critical_temperature_c=critical,
        )
        standard_crossings[f"{thickness:g}"] = cross
        for row in pts:
            series.append({**row, "series": f"δпр={thickness:g} мм", "kind": "standard", "thickness_mm": thickness})

    actual_pts, actual_crossing = _curve_for_thickness(
        reduced_thickness_mm=actual,
        initial_temperature_c=initial_temperature_c,
        horizon_min=horizon,
        sample_interval_min=sample_interval,
        dt_min=dt,
        rho=rho,
        c0=c0,
        kc=kc,
        eps=eps,
        critical_temperature_c=critical,
    )
    for row in actual_pts:
        series.append({**row, "series": f"Расчётная δпр={actual:g} мм", "kind": "actual", "thickness_mm": actual})

    fire_curve = [
        {
            "time_min": float(i * sample_interval),
            "temperature_c": _standard_fire_temperature_c(float(i * sample_interval), initial_temperature_c),
            "series": "ISO 834 / ГОСТ 30247.0",
            "kind": "fire",
        }
        for i in range(int(round(horizon / sample_interval)) + 1)
    ]
    return {
        "schema": "sp554_v084_unprotected_heating_diagram_v1",
        "standard_reduced_thicknesses_mm": list(STANDARD_REDUCED_THICKNESSES_MM),
        "actual_reduced_thickness_mm": actual,
        "critical_temperature_c": critical,
        "initial_temperature_c": float(initial_temperature_c),
        "horizon_min": horizon,
        "actual_crossing_time_min": actual_crossing,
        "standard_crossing_times_min": standard_crossings,
        "steel_series": series,
        "fire_series": fire_curve,
        "calculation_method": "SP554 12.1-12.4 explicit recurrence",
    }



def protected_fdm_visualization(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return visualization emitted by the exact production SP554 12.5 solver.

    v0.84 deliberately does not re-run the FDM/FVM recurrence in the
    presentation layer.  The production ``PROTECTED_FDM_12_5`` integration
    records a sampled visualization trace; this helper only normalizes the
    direct/inverse result envelope and returns that trace.
    """
    trace = values.get("protection_12_5_calculation_trace")
    if not isinstance(trace, Mapping):
        raise FireUIError("protection_12_5_calculation_trace is unresolved")
    if isinstance(trace.get("selected_result"), Mapping):
        trace = trace["selected_result"]
    visualization = trace.get("visualization")
    if not isinstance(visualization, Mapping) or visualization.get("schema") != "sp554_v084_fdm_visualization_v1":
        raise FireUIError("production SP554 12.5 result does not contain the v0.84 visualization trace")
    return dict(visualization)


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    install_thermal_solver_patch()
    fn = automatic_unprotected_step_method
    setattr(fn, "_sp554_v084_auto_step_method", True)
    registry.register(UNPROTECTED_METHOD_NODE_ID, fn)
    return registry


__all__ = [
    "STANDARD_REDUCED_THICKNESSES_MM",
    "automatic_unprotected_step_method",
    "install_registry_remediation",
    "unprotected_heating_diagram",
    "protected_fdm_visualization",
]
