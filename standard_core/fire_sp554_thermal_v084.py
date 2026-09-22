"""v0.84 scoped instrumentation overlay for the frozen SP554 12.5 solver.

The normative solver itself remains frozen.  When visualization is requested,
this overlay samples local states from the *same* production integration at the
line immediately after the new protection/steel temperatures are calculated.
No presentation-only thermal recurrence is executed.
"""
from __future__ import annotations

import inspect
import math
import sys
from typing import Any, Mapping

from . import fire_sp554_thermal as _thermal
from . import fire_ui23_protection_route as _route

_ORIGINAL_PROTECTED_FDM = _thermal._protected_fdm
_ORIGINAL_FDM_CASE = _route._fdm_case
_PATCHED = False


def _capture_line() -> int:
    lines, start = inspect.getsourcelines(_ORIGINAL_PROTECTED_FDM)
    for offset, line in enumerate(lines):
        if "all_new = [*new, next_steel]" in line:
            return start + offset
    raise RuntimeError("v0.84 cannot locate the frozen SP554 12.5 state-update marker")


_CAPTURE_LINE = _capture_line()


def _protected_fdm_v084(case: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    interval_raw = case.get("visualization_sample_interval_min")
    if interval_raw is None:
        return _ORIGINAL_PROTECTED_FDM(case, delta_mm)
    if (
        isinstance(interval_raw, bool)
        or not isinstance(interval_raw, (int, float))
        or not math.isfinite(float(interval_raw))
        or float(interval_raw) <= 0.0
    ):
        raise ValueError("visualization_sample_interval_min must be finite and > 0")
    interval = float(interval_raw)

    model = case.get("protection_model")
    if not isinstance(model, Mapping):
        return _ORIGINAL_PROTECTED_FDM(case, delta_mm)
    thickness = float(model["thickness_mm"])
    n = int(model["layer_count"])
    initial = float(case.get("initial_temperature_c", 20.0))
    target = float(case["critical_temperature_c"])
    positions = [i * thickness / n for i in range(n)] + [thickness]
    time_series: list[dict[str, float]] = [{
        "time_min": 0.0,
        "fire_temperature_c": initial,
        "surface_temperature_c": initial,
        "mid_protection_temperature_c": initial,
        "interface_protection_temperature_c": initial,
        "steel_temperature_c": initial,
    }]
    archive: list[dict[str, Any]] = [{
        "time_min": 0.0,
        "positions_mm": list(positions),
        "temperatures_c": [initial] * (n + 1),
    }]
    next_sample = interval

    def add_state(t: float, protection: list[float], steel: float) -> None:
        if time_series and abs(time_series[-1]["time_min"] - t) <= 1e-10:
            return
        time_series.append({
            "time_min": float(t),
            "fire_temperature_c": float(_thermal._standard_fire_temperature_c(t, initial)),
            "surface_temperature_c": float(protection[0]),
            "mid_protection_temperature_c": float(protection[n // 2]),
            "interface_protection_temperature_c": float(protection[-1]),
            "steel_temperature_c": float(steel),
        })
        archive.append({
            "time_min": float(t),
            "positions_mm": list(positions),
            "temperatures_c": [*[float(x) for x in protection], float(steel)],
        })

    def local_trace(frame, event, arg):
        nonlocal next_sample
        if event != "line" or frame.f_lineno != _CAPTURE_LINE:
            return local_trace
        loc = frame.f_locals
        old = loc.get("old")
        new = loc.get("new")
        if not isinstance(old, list) or not isinstance(new, list) or len(old) != n or len(new) != n:
            return local_trace
        t0 = float(loc["time_min"])
        t1 = float(loc["next_time"])
        s0 = float(loc["steel_t"])
        s1 = float(loc["next_steel"])
        end = t1
        crossing = None
        if s1 >= target and target > s0:
            f_cross = (target - s0) / (s1 - s0)
            crossing = t0 + f_cross * (t1 - t0)
            end = crossing
        while next_sample <= end + 1e-12:
            f = (next_sample - t0) / (t1 - t0) if t1 > t0 else 1.0
            f = min(1.0, max(0.0, f))
            protection = [old[i] + f * (new[i] - old[i]) for i in range(n)]
            steel = s0 + f * (s1 - s0)
            add_state(next_sample, protection, steel)
            next_sample += interval
        if crossing is not None:
            f = (crossing - t0) / (t1 - t0) if t1 > t0 else 1.0
            protection = [old[i] + f * (new[i] - old[i]) for i in range(n)]
            add_state(crossing, protection, target)
        return local_trace

    def global_trace(frame, event, arg):
        if event == "call" and frame.f_code is _ORIGINAL_PROTECTED_FDM.__code__:
            return local_trace
        return None

    previous_trace = sys.gettrace()
    sys.settrace(global_trace)
    try:
        result = _ORIGINAL_PROTECTED_FDM(case, delta_mm)
    finally:
        sys.settrace(previous_trace)

    if result.get("status") not in {"COMPLETE", "INVALID_BY_12_6"} or result.get("calculated_time_min") is None:
        return result
    calc_time = float(result["calculated_time_min"])
    target_times = [calc_time * f for f in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    profiles: list[dict[str, Any]] = []
    seen: set[float] = set()
    for wanted in target_times:
        row = min(archive, key=lambda r: abs(float(r["time_min"]) - wanted))
        key = round(float(row["time_min"]), 9)
        if key in seen:
            continue
        seen.add(key)
        profiles.append({
            "time_min": float(row["time_min"]),
            "positions_mm": [float(x) for x in row["positions_mm"]],
            "temperatures_c": [float(x) for x in row["temperatures_c"]],
        })
    result = dict(result)
    result["visualization"] = {
        "schema": "sp554_v084_fdm_visualization_v1",
        "source": "same_production_SP554_12_5_integration",
        "sampling_implementation": "runtime_state_instrumentation_no_second_solver",
        "layer_count": n,
        "protection_thickness_mm": thickness,
        "dx_mm": thickness / n,
        "positions_mm": list(positions),
        "sample_interval_min": interval,
        "time_series": time_series,
        "profile_samples": profiles,
        "critical_temperature_c": target,
        "calculated_time_min": calc_time,
        "initial_temperature_c": initial,
    }
    return result


def _fdm_case_v084(values: Mapping[str, Any], thickness_mm: float) -> dict[str, Any]:
    case = dict(_ORIGINAL_FDM_CASE(values, thickness_mm))
    if "gost30247_initial_furnace_temperature_c" in values:
        raw = values["gost30247_initial_furnace_temperature_c"]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise ValueError("gost30247_initial_furnace_temperature_c must be finite")
        case["initial_temperature_c"] = float(raw)
    else:
        case["initial_temperature_c"] = 20.0
    case["visualization_sample_interval_min"] = 0.5
    return case


def install_thermal_solver_patch() -> None:
    global _PATCHED
    if _PATCHED:
        return
    _thermal._protected_fdm = _protected_fdm_v084
    _route._fdm_case = _fdm_case_v084
    _PATCHED = True


__all__ = ["install_thermal_solver_patch"]
