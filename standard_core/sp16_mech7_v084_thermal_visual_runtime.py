"""v0.84 executors and chart-data generation for SP554 thermal visualization."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
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


def _curve_for_thickness(*, reduced_thickness_mm: float, initial_temperature_c: float, horizon_min: float,
                         sample_interval_min: float, dt_min: float, rho: float, c0: float, kc: float,
                         eps: float, critical_temperature_c: float) -> tuple[list[dict[str, float]], float | None]:
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
    actual = _number(values, "delta_pr", positive=True)
    critical = _number(values, "critical_temperature_c")
    dt = min(_number(values, "sp554_dt_unprotected_min", 0.1, positive=True), 0.1)
    rho = _number(values, "sp554_steel_density_12_2", 7850.0, positive=True)
    c0 = _number(values, "sp554_steel_c0_12_2", 480.0, positive=True)
    kc = _number(values, "sp554_steel_c_temp_coeff_12_2", 0.00063)
    eps = _number(values, "sp554_eps_reduced_12_4", 0.5, positive=True)
    if eps > 1.0:
        raise FireUIError("sp554_eps_reduced_12_4 must be <= 1")
    _, actual_crossing = _curve_for_thickness(reduced_thickness_mm=actual, initial_temperature_c=initial_temperature_c,
        horizon_min=180.0, sample_interval_min=2.0, dt_min=dt, rho=rho, c0=c0, kc=kc, eps=eps,
        critical_temperature_c=critical)
    horizon = 60.0
    if actual_crossing is not None:
        horizon = max(60.0, min(180.0, math.ceil(actual_crossing * 1.20 / 5.0) * 5.0))
    sample_interval = 0.5
    series: list[dict[str, Any]] = []
    standard_crossings: dict[str, float | None] = {}
    for thickness in STANDARD_REDUCED_THICKNESSES_MM:
        pts, cross = _curve_for_thickness(reduced_thickness_mm=thickness, initial_temperature_c=initial_temperature_c,
            horizon_min=horizon, sample_interval_min=sample_interval, dt_min=dt, rho=rho, c0=c0, kc=kc, eps=eps,
            critical_temperature_c=critical)
        standard_crossings[f"{thickness:g}"] = cross
        for row in pts:
            series.append({**row, "series": f"δпр={thickness:g} мм", "kind": "standard", "thickness_mm": thickness})
    actual_pts, actual_crossing = _curve_for_thickness(reduced_thickness_mm=actual, initial_temperature_c=initial_temperature_c,
        horizon_min=horizon, sample_interval_min=sample_interval, dt_min=dt, rho=rho, c0=c0, kc=kc, eps=eps,
        critical_temperature_c=critical)
    for row in actual_pts:
        series.append({**row, "series": f"Расчётная δпр={actual:g} мм", "kind": "actual", "thickness_mm": actual})
    fire_curve = [{"time_min": float(i * sample_interval),
                   "temperature_c": _standard_fire_temperature_c(float(i * sample_interval), initial_temperature_c),
                   "series": "ISO 834 / ГОСТ 30247.0", "kind": "fire"}
                  for i in range(int(round(horizon / sample_interval)) + 1)]
    return {"schema": "sp554_v084_unprotected_heating_diagram_v1",
            "standard_reduced_thicknesses_mm": list(STANDARD_REDUCED_THICKNESSES_MM),
            "actual_reduced_thickness_mm": actual, "critical_temperature_c": critical,
            "initial_temperature_c": float(initial_temperature_c), "horizon_min": horizon,
            "actual_crossing_time_min": actual_crossing, "standard_crossing_times_min": standard_crossings,
            "steel_series": series, "fire_series": fire_curve,
            "calculation_method": "SP554 12.1-12.4 explicit recurrence"}


def protected_fdm_visualization(values: Mapping[str, Any]) -> dict[str, Any]:
    model = values.get("protection_12_5_model_parameters")
    if not isinstance(model, Mapping):
        raise FireUIError("protection_12_5_model_parameters is unresolved")
    thickness = _number(values, "protection_thickness_mm", positive=True)
    target = _number(values, "critical_temperature_c")
    delta_mm = _number(values, "delta_pr_protected", positive=True)
    initial = 20.0; n = 3; dt_min = 0.005; max_time = 300.0
    rho_p = float(model.get("density_kg_m3")); A = float(model.get("conductivity_A_w_mk")); B = float(model.get("conductivity_B_w_mk2"))
    C = float(model.get("heat_capacity_C_j_kgk")); D = float(model.get("heat_capacity_D_j_kgk2"))
    if str(model.get("temperature_basis") or "degC") == "K":
        A += B * 273.15; C += D * 273.15
    surface_eps = float(model.get("surface_emissivity", 0.625)); eps_fire = 0.85
    eps = 1.0 / (1.0 / eps_fire + 1.0 / surface_eps - 1.0)
    rho_s = 7850.0; c_s = 480.0; d_s = 0.00063
    delta_m = delta_mm / 1000.0; dx = thickness / 1000.0 / n
    pos = [i * thickness / n for i in range(n)] + [thickness]
    prot = [initial] * n; steel = initial; t = 0.0; next_sample = 0.5
    ts = [{"time_min": 0.0, "fire_temperature_c": initial, "surface_temperature_c": initial,
           "mid_protection_temperature_c": initial, "interface_protection_temperature_c": initial,
           "steel_temperature_c": initial}]
    archive = [{"time_min": 0.0, "positions_mm": pos, "temperatures_c": [initial] * (n + 1)}]
    crossing = None
    while t < max_time - 1e-12:
        nt = min(t + dt_min, max_time); dts = (nt - t) * 60.0; fire = _standard_fire_temperature_c(nt, initial)
        old = prot; new = list(old)
        alpha = _heat_transfer_coefficient_w_m2k(fire, old[0], eps); cap0 = C + D * old[0]; right0 = old[1] if n > 1 else steel
        new[0] = old[0] + 2 * dts * (A * (right0 - old[0]) + 0.5 * B * (right0**2 - old[0]**2) + alpha * (fire - old[0]) * dx) / (rho_p * dx * dx * cap0)
        for i in range(1, n):
            cap = C + D * old[i]; right = old[i + 1] if i + 1 < n else steel
            new[i] = old[i] + dts * (A * (old[i - 1] - 2 * old[i] + right) + 0.5 * B * (old[i - 1]**2 - 2 * old[i]**2 + right**2)) / (rho_p * dx * dx * cap)
        cp = _steel_heat_capacity_j_kgk(c_s, d_s, steel); capi = C + D * steel
        den = dx * (rho_p * dx * capi + 2 * rho_s * delta_m * cp); last = old[-1]
        next_steel = steel + 2 * dts * (A * (last - steel) + 0.5 * B * (last**2 - steel**2)) / den
        while next_sample <= nt + 1e-12:
            f = (next_sample - t) / (nt - t) if nt > t else 1.0; pv = [old[i] + f * (new[i] - old[i]) for i in range(n)]; sv = steel + f * (next_steel - steel)
            ts.append({"time_min": next_sample, "fire_temperature_c": _standard_fire_temperature_c(next_sample, initial),
                       "surface_temperature_c": pv[0], "mid_protection_temperature_c": pv[n//2],
                       "interface_protection_temperature_c": pv[-1], "steel_temperature_c": sv})
            archive.append({"time_min": next_sample, "positions_mm": pos, "temperatures_c": [*pv, sv]}); next_sample += 0.5
        if next_steel >= target:
            f = (target - steel) / (next_steel - steel) if next_steel > steel else 0.0; crossing = t + f * (nt - t); pv = [old[i] + f * (new[i] - old[i]) for i in range(n)]
            archive = [r for r in archive if r["time_min"] <= crossing + 1e-9]; ts = [r for r in ts if r["time_min"] <= crossing + 1e-9]
            archive.append({"time_min": crossing, "positions_mm": pos, "temperatures_c": [*pv, target]})
            ts.append({"time_min": crossing, "fire_temperature_c": _standard_fire_temperature_c(crossing, initial),
                       "surface_temperature_c": pv[0], "mid_protection_temperature_c": pv[n//2],
                       "interface_protection_temperature_c": pv[-1], "steel_temperature_c": target}); break
        prot = new; steel = next_steel; t = nt
    if crossing is None:
        raise FireUIError("FVM visualization did not reach critical temperature inside 300 min")
    targets = [crossing * f for f in (0, .2, .4, .6, .8, 1.0)]; profiles = []; seen = set()
    for tt in targets:
        row = min(archive, key=lambda r: abs(r["time_min"] - tt)); k = round(row["time_min"], 8)
        if k not in seen:
            profiles.append(row); seen.add(k)
    return {"schema": "sp554_v084_fdm_visualization_v1", "layer_count": n,
            "protection_thickness_mm": thickness, "dx_mm": thickness / n, "positions_mm": pos,
            "time_series": ts, "profile_samples": profiles, "critical_temperature_c": target,
            "calculated_time_min": crossing}


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    fn = automatic_unprotected_step_method
    setattr(fn, "_sp554_v084_auto_step_method", True)
    registry.register(UNPROTECTED_METHOD_NODE_ID, fn)
    return registry


__all__ = ["STANDARD_REDUCED_THICKNESSES_MM", "automatic_unprotected_step_method",
           "install_registry_remediation", "unprotected_heating_diagram", "protected_fdm_visualization"]
