"""SP554 FIRE-D3/D3.1 Section 12 thermal runtime and full-scope reconciliation.

This module deliberately keeps the FIRE-D2 mechanical producers frozen.  It consumes a
critical steel temperature and resolves time-to-critical-temperature through the explicit
Section 12 routes that can be executed without inventing missing product data.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence


_SP554_DT_DEFAULT_MIN = 0.1
_SP554_RHO_STEEL_DEFAULT = 7850.0
_SP554_C_STEEL_DEFAULT = 480.0
_SP554_D_STEEL_DEFAULT = 0.00063
_SP554_EPS_FIRE_DEFAULT = 0.85
_SP554_EPS_STEEL_DEFAULT = 0.625
_SP554_WATER_LATENT_HEAT_J_KG = 2260.0e3
_FIGURE1_DELTA_NODES_MM = (3.0, 5.0, 10.0, 15.0, 20.0)


def _number(data: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in data:
        raise ValueError(f"Missing required thermal input: {key}")
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{key} must be a finite number")
    x = float(value)
    if positive and x <= 0.0:
        raise ValueError(f"{key} must be > 0")
    if nonnegative and x < 0.0:
        raise ValueError(f"{key} must be >= 0")
    return x


def _optional_number(data: Mapping[str, Any], key: str, default: float) -> float:
    if key not in data:
        return float(default)
    return _number(data, key)


def _standard_fire_temperature_c(time_min: float, initial_temperature_c: float) -> float:
    if time_min < 0.0:
        raise ValueError("time_min must be >= 0")
    # ГОСТ 30247.0 formula (1): T - T0 = 345 lg(8t + 1), t in minutes.
    return float(initial_temperature_c + 345.0 * math.log10(8.0 * time_min + 1.0))


def _reduced_emissivity(eps_fire: float, eps_surface: float) -> float:
    if not (0.0 < eps_fire <= 1.0 and 0.0 < eps_surface <= 1.0):
        raise ValueError("Emissivities must be in (0, 1]")
    denominator = 1.0 / eps_fire + 1.0 / eps_surface - 1.0
    if denominator <= 0.0:
        raise ValueError("Reduced-emissivity denominator must be positive")
    return 1.0 / denominator


def _heat_transfer_coefficient_w_m2k(
    fire_temperature_c: float,
    surface_temperature_c: float,
    reduced_emissivity: float,
) -> float:
    """Evaluate SP554 (12.3) using absolute temperature in the fourth-power radiation term."""
    delta = fire_temperature_c - surface_temperature_c
    tf_k = fire_temperature_c + 273.15
    ts_k = surface_temperature_c + 273.15
    if abs(delta) < 1e-12:
        # Limit of (a^4-b^4)/(a-b), including the /100 scaling printed in (12.3).
        radiation_quotient = 4.0 * (ts_k / 100.0) ** 3 / 100.0
    else:
        radiation_quotient = ((tf_k / 100.0) ** 4 - (ts_k / 100.0) ** 4) / delta
    return 29.0 + 5.77 * reduced_emissivity * radiation_quotient


def _steel_heat_capacity_j_kgk(base: float, coefficient_per_c: float, temperature_c: float) -> float:
    # The coefficient 0.00063 supplied after (12.4) is a relative temperature coefficient.
    # This is also the interpretation used by the frozen reconstructed Figure 1 dataset.
    cp = base * (1.0 + coefficient_per_c * temperature_c)
    if cp <= 0.0 or not math.isfinite(cp):
        raise ValueError("Steel heat capacity became non-positive/non-finite")
    return cp


def sp554_fictitious_temperature_12_8(
    *,
    initial_moisture_percent: float,
    protection_density_kg_m3: float,
    layer_thickness_m: float,
    protection_heat_capacity_j_kgk: float,
    steel_density_kg_m3: float,
    reduced_steel_thickness_m: float,
    steel_heat_capacity_j_kgk: float,
    latent_heat_j_kg: float = _SP554_WATER_LATENT_HEAT_J_KG,
) -> float:
    """
    Summary:
        Evaluate the scalar fictitious-temperature quantity printed in SP554 formula (12.8).

    Standard reference:
        Standard: СП 554.1311500.2026, Section 12
        Version: enacted 2026 baseline reconciled in FIRE-D3.1
        Clause: 12.5
        Annex: None
        Equation/Table: (12.8)
        Audit ID: FIRE-D31-12.8-001
        Normative status: algebraically_executable_recurrence_fail_closed

    Mathematical form:
        t_phi = W*r / (100*(C_p + 2*rho_s*delta_s*C_s/(rho_p*dx))).

    Parameters:
        initial_moisture_percent:
            Type: float
            Unit: percent by mass
            Meaning: Initial mass moisture W of fire-protection material.
            Valid range: >= 0
            Source: SP554 (12.8).
        protection_density_kg_m3, layer_thickness_m, protection_heat_capacity_j_kgk:
            Type: float
            Unit: kg/m3, m, J/(kg K)
            Meaning: Protection-layer physical properties entering (12.8).
            Valid range: > 0
            Source: Product/test-derived thermal model.
        steel_density_kg_m3, reduced_steel_thickness_m, steel_heat_capacity_j_kgk:
            Type: float
            Unit: kg/m3, m, J/(kg K)
            Meaning: Lumped steel physical properties entering (12.8).
            Valid range: > 0
            Source: SP554 steel model / resolved section geometry.
        latent_heat_j_kg:
            Type: float
            Unit: J/kg
            Meaning: Latent heat of water vaporization r.
            Valid range: > 0
            Source: SP554 (12.8), default 2260e3 J/kg.

    Returns:
        Type: float
        Unit: degrees Celsius as a temperature decrement quantity
        Meaning: Scalar fictitious-temperature value t_phi from formula (12.8).

    Assumptions:
        - The supplied heat capacities are the values intended for the evaluated state.
        - This function performs algebra only and does not evolve moisture content in time.

    Sign convention:
        - Returned t_phi is non-negative for non-negative moisture.

    Unit convention:
        - SI units are required; W is supplied in percent exactly as printed by (12.8).

    Applicability:
        - Algebraic evaluation of SP554 (12.8), including audit/trace use in FIRE-D3.1.

    Limitations:
        - The function does not interpret t_phi as a repeatable per-time-step temperature decrement.
        - No moisture-depletion law is invented. Literal repeated recurrence remains fail-closed.

    Raises:
        ValueError: Any required physical input is non-finite, non-positive where positivity is required, or W is negative.

    Examples:
        >>> round(sp554_fictitious_temperature_12_8(initial_moisture_percent=0.0, protection_density_kg_m3=900.0, layer_thickness_m=0.005, protection_heat_capacity_j_kgk=860.0, steel_density_kg_m3=7850.0, reduced_steel_thickness_m=0.01, steel_heat_capacity_j_kgk=500.0), 6)
        0.0

    Tests:
        Unit tests:
            - tests/test_fire_d31_section12_reconciliation.py

    Implementation notes:
        - FIRE-D3.1 separates this scalar formula from executable moisture accounting.
        - If moisture is already embedded in validated thermal properties, explicit t_phi subtraction is prohibited to avoid double counting.
    """
    values = {
        "initial_moisture_percent": initial_moisture_percent,
        "protection_density_kg_m3": protection_density_kg_m3,
        "layer_thickness_m": layer_thickness_m,
        "protection_heat_capacity_j_kgk": protection_heat_capacity_j_kgk,
        "steel_density_kg_m3": steel_density_kg_m3,
        "reduced_steel_thickness_m": reduced_steel_thickness_m,
        "steel_heat_capacity_j_kgk": steel_heat_capacity_j_kgk,
        "latent_heat_j_kg": latent_heat_j_kg,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be a finite number")
    W = float(initial_moisture_percent)
    rho_p = float(protection_density_kg_m3)
    dx = float(layer_thickness_m)
    cp_p = float(protection_heat_capacity_j_kgk)
    rho_s = float(steel_density_kg_m3)
    delta_s = float(reduced_steel_thickness_m)
    cp_s = float(steel_heat_capacity_j_kgk)
    r = float(latent_heat_j_kg)
    if W < 0.0:
        raise ValueError("initial_moisture_percent must be >= 0")
    if min(rho_p, dx, cp_p, rho_s, delta_s, cp_s, r) <= 0.0:
        raise ValueError("All physical parameters in formula (12.8), except moisture which may be zero, must be > 0")
    denominator = 100.0 * (cp_p + 2.0 * rho_s * delta_s * cp_s / (rho_p * dx))
    if denominator <= 0.0 or not math.isfinite(denominator):
        raise ValueError("Formula (12.8) denominator must be positive and finite")
    return W * r / denominator


def _moisture_accounting_policy(
    model: Mapping[str, Any],
    *,
    moisture_percent: float,
    initial_t_phi_c: float,
) -> dict[str, Any]:
    """Resolve the FIRE-D3.1 moisture policy without silently double counting latent heat."""
    if moisture_percent <= 1e-12:
        return {
            "mode": "none_dry",
            "initial_moisture_percent": moisture_percent,
            "explicit_t_phi_applied": False,
            "initial_t_phi_c": 0.0,
            "status": "DRY_ROUTE",
        }
    mode = str(model["moisture_accounting_mode"]) if "moisture_accounting_mode" in model else ""
    if mode == "embedded_in_thermal_properties":
        if model.get("moisture_embedded_in_properties_confirmed") is not True:
            raise ValueError(
                "W>0 with moisture_accounting_mode=embedded_in_thermal_properties requires "
                "moisture_embedded_in_properties_confirmed=true; otherwise latent-heat double counting cannot be excluded"
            )
        return {
            "mode": mode,
            "initial_moisture_percent": moisture_percent,
            "explicit_t_phi_applied": False,
            "initial_t_phi_c": initial_t_phi_c,
            "status": "SUPPORTED_WITH_EXPERIMENTALLY_FITTED_OR_NONLINEAR_PROPERTIES_AND_12_6_VALIDATION",
            "basis": (
                "SP554 12.5 permits experimentally identified/nonlinear thermal properties; "
                "ARSS expert clarification states t_phi is omitted when moisture is already included "
                "in conductivity/heat-capacity input data."
            ),
        }
    if mode == "external_validation_envelope":
        if model.get("external_validation_envelope_confirmed") is not True:
            raise ValueError(
                "W>0 with moisture_accounting_mode=external_validation_envelope requires "
                "external_validation_envelope_confirmed=true"
            )
        return {
            "mode": mode,
            "initial_moisture_percent": moisture_percent,
            "explicit_t_phi_applied": False,
            "initial_t_phi_c": initial_t_phi_c,
            "status": "SUPPORTED_ONLY_INSIDE_CONFIRMED_12_6_VALIDATION_ENVELOPE",
            "basis": (
                "Moisture is not subtracted a second time as a per-step t_phi term. "
                "The effective thermal-property model is accepted only when the engineer has supplied "
                "complete SP554 12.6 validation evidence with maximum deviation <=20%."
            ),
        }
    if mode == "explicit_t_phi_12_8":
        raise ValueError(
            "FIRE-D3.1 reconciles formula (12.8) but fails closed for literal repeated t_phi execution: "
            "the enacted SP554 and predecessor formula define t_phi but no moisture-depletion/state rule that makes "
            "a per-time-step subtraction discretization-invariant. Use validated thermal properties with "
            "moisture_accounting_mode=embedded_in_thermal_properties, or provide a separately validated product model."
        )
    raise ValueError(
        "W>0 requires explicit protection_model.moisture_accounting_mode: "
        "embedded_in_thermal_properties or explicit_t_phi_12_8. No implicit moisture fallback is allowed."
    )


def _resolve_reduced_thickness_mm(case: Mapping[str, Any]) -> tuple[float, dict[str, Any]]:
    if "reduced_thickness_mm" in case:
        delta = _number(case, "reduced_thickness_mm", positive=True)
        return delta, {"producer": "explicit_reduced_thickness", "equation_ref": "12.2"}
    if "area_mm2" in case and "heated_perimeter_mm" in case:
        area = _number(case, "area_mm2", positive=True)
        perimeter = _number(case, "heated_perimeter_mm", positive=True)
        delta = area / perimeter
        return delta, {
            "producer": "area_over_heated_perimeter",
            "equation_ref": "12.2",
            "area_mm2": area,
            "heated_perimeter_mm": perimeter,
        }
    raise ValueError("Provide reduced_thickness_mm or both area_mm2 and heated_perimeter_mm")


def _unprotected_parameters(case: Mapping[str, Any]) -> dict[str, float | str]:
    source = str(case["steel_properties_source"]) if "steel_properties_source" in case else "sp554_12_2_defaults"
    if source not in {"sp554_12_2_defaults", "explicit"}:
        raise ValueError("steel_properties_source must be sp554_12_2_defaults or explicit")
    if source == "sp554_12_2_defaults":
        rho = _SP554_RHO_STEEL_DEFAULT
        c0 = _SP554_C_STEEL_DEFAULT
        kc = _SP554_D_STEEL_DEFAULT
        eps_fire = _SP554_EPS_FIRE_DEFAULT
        eps_steel = _SP554_EPS_STEEL_DEFAULT
    else:
        rho = _number(case, "steel_density_kg_m3", positive=True)
        c0 = _number(case, "steel_heat_capacity_base_j_kgk", positive=True)
        kc = _number(case, "steel_heat_capacity_temp_coeff_per_c", nonnegative=True)
        eps_fire = _number(case, "furnace_emissivity", positive=True)
        eps_steel = _number(case, "steel_emissivity", positive=True)
    if eps_fire > 1.0 or eps_steel > 1.0:
        raise ValueError("Emissivities must not exceed 1")
    return {
        "source": source,
        "rho": rho,
        "c0": c0,
        "kc": kc,
        "eps_fire": eps_fire,
        "eps_steel": eps_steel,
    }


def _unprotected_step_time(case: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    target = _number(case, "critical_temperature_c")
    initial = _optional_number(case, "initial_temperature_c", 20.0)
    dt_min = _optional_number(case, "time_step_min", _SP554_DT_DEFAULT_MIN)
    max_time_min = _optional_number(case, "max_time_min", 300.0)
    if dt_min <= 0.0 or dt_min > 0.1 + 1e-12:
        raise ValueError("FIRE-D3 r1 requires 0 < time_step_min <= 0.1 min for the explicit 12.1 step route")
    if max_time_min <= 0.0:
        raise ValueError("max_time_min must be > 0")
    params = _unprotected_parameters(case)
    if target > 800.0 + 1e-12 and params["source"] == "sp554_12_2_defaults":
        raise ValueError(
            "SP554 default steel density is stated only for 20-800 C; target above 800 C requires explicit steel thermal properties"
        )
    if target <= initial:
        return {
            "status": "COMPLETE",
            "actual_fire_resistance_min": 0.0,
            "calculated_time_min": 0.0,
            "steel_temperature_c": initial,
            "fire_temperature_c": initial,
            "step_count": 0,
            "crossing_bracket": [0.0, 0.0],
            "thermal_trace": [],
            "material_parameters": params,
        }

    delta_m = delta_mm / 1000.0
    rho = float(params["rho"])
    c0 = float(params["c0"])
    kc = float(params["kc"])
    eps_red = _reduced_emissivity(float(params["eps_fire"]), float(params["eps_steel"]))
    steel_t = initial
    time_min = 0.0
    steps = 0
    trace: list[dict[str, float]] = []
    while time_min < max_time_min - 1e-12:
        next_time = min(time_min + dt_min, max_time_min)
        actual_dt_min = next_time - time_min
        fire_t = _standard_fire_temperature_c(next_time, initial)
        alpha = _heat_transfer_coefficient_w_m2k(fire_t, steel_t, eps_red)
        cp = _steel_heat_capacity_j_kgk(c0, kc, steel_t)
        next_steel = steel_t + (actual_dt_min * 60.0) * alpha * (fire_t - steel_t) / (rho * delta_m * cp)
        if not math.isfinite(next_steel) or next_steel < steel_t - 1e-9:
            raise ValueError("Unprotected explicit thermal step became numerically unstable/non-monotone")
        steps += 1
        if steps <= 5 or steps % 100 == 0:
            trace.append({
                "time_min": next_time,
                "fire_temperature_c": fire_t,
                "steel_temperature_c": next_steel,
                "alpha_w_m2k": alpha,
                "steel_cp_j_kgk": cp,
            })
        if next_steel >= target:
            fraction = (target - steel_t) / (next_steel - steel_t) if next_steel > steel_t else 0.0
            crossing = time_min + fraction * actual_dt_min
            fire_cross = _standard_fire_temperature_c(crossing, initial)
            return {
                "status": "COMPLETE",
                "actual_fire_resistance_min": float(crossing),
                "calculated_time_min": float(crossing),
                "steel_temperature_c": float(target),
                "fire_temperature_c": float(fire_cross),
                "step_count": steps,
                "crossing_bracket": [float(time_min), float(next_time)],
                "thermal_trace": trace,
                "reduced_emissivity": eps_red,
                "material_parameters": params,
            }
        time_min = next_time
        steel_t = next_steel

    return {
        "status": "INCOMPLETE_FAIL_CLOSED",
        "actual_fire_resistance_min": None,
        "calculated_time_min": None,
        "steel_temperature_c_at_max_time": float(steel_t),
        "max_time_min": max_time_min,
        "step_count": steps,
        "thermal_trace": trace,
        "reduced_emissivity": eps_red,
        "material_parameters": params,
        "diagnostic": "Critical temperature was not reached inside max_time_min; no extrapolation performed.",
    }


def _figure1_time(case: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    if delta_mm < _FIGURE1_DELTA_NODES_MM[0] - 1e-12 or delta_mm > _FIGURE1_DELTA_NODES_MM[-1] + 1e-12:
        raise ValueError("Figure 1 route is limited to the printed/reconstructed reduced-thickness range 3-20 mm")
    target = _number(case, "critical_temperature_c")
    # Figure 1 frozen reconstruction covers 0-60 min with SP554 defaults and T0=20 C.
    local = dict(case)
    local["steel_properties_source"] = "sp554_12_2_defaults"
    local["initial_temperature_c"] = 20.0
    local["time_step_min"] = 0.1
    local["max_time_min"] = 60.0
    left = max(x for x in _FIGURE1_DELTA_NODES_MM if x <= delta_mm + 1e-12)
    right = min(x for x in _FIGURE1_DELTA_NODES_MM if x >= delta_mm - 1e-12)
    rl = _unprotected_step_time(local, left)
    if rl["status"] != "COMPLETE":
        raise ValueError("Target is outside the frozen Figure 1 curve envelope; extrapolation is forbidden")
    if math.isclose(left, right, abs_tol=1e-12):
        value = float(rl["actual_fire_resistance_min"])
    else:
        rr = _unprotected_step_time(local, right)
        if rr["status"] != "COMPLETE":
            raise ValueError("Target is outside the frozen Figure 1 curve envelope; extrapolation is forbidden")
        fraction = (delta_mm - left) / (right - left)
        value = float(rl["actual_fire_resistance_min"]) + fraction * (
            float(rr["actual_fire_resistance_min"]) - float(rl["actual_fire_resistance_min"])
        )
    return {
        "status": "COMPLETE",
        "actual_fire_resistance_min": value,
        "calculated_time_min": value,
        "critical_temperature_c": target,
        "figure1_bracketing_reduced_thickness_mm": [left, right],
        "interpolation": "linear_in_reduced_thickness_after_0.1_min_curve_reconstruction",
        "source_defaults_enforced": True,
        "no_extrapolation": True,
    }


def _validate_axis(values: Sequence[Any], name: str) -> list[float]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) < 2:
        raise ValueError(f"{name} must contain at least two nodes")
    out: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} contains a non-finite/non-numeric value")
        out.append(float(value))
    if any(b <= a for a, b in zip(out, out[1:])):
        raise ValueError(f"{name} must be strictly increasing")
    return out


def _validate_matrix_dataset(dataset: Mapping[str, Any], target_temperature_c: float) -> dict[str, Any]:
    if not isinstance(dataset, Mapping):
        raise ValueError("performance_dataset must be an object")
    documented_t = _number(dataset, "critical_temperature_c")
    if not math.isclose(documented_t, target_temperature_c, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(
            "12.10 matrix/nomogram route requires an exact documented critical-temperature level; FIRE-D3 does not invent Tcr interpolation"
        )
    steel_group = str(dataset["steel_group"]) if "steel_group" in dataset else "ordinary"
    if steel_group not in {"ordinary", "increased", "high", "fire_resistant"}:
        raise ValueError("performance_dataset.steel_group is unsupported")
    upper = 850.0 if steel_group == "fire_resistant" else 700.0
    if documented_t < 400.0 - 1e-9 or documented_t > upper + 1e-9:
        raise ValueError("Dataset critical temperature is outside the 12.8/12.9 range")
    # Published datasets are established at 50 C increments; the selected slice must be one such level.
    if abs((documented_t - 400.0) / 50.0 - round((documented_t - 400.0) / 50.0)) > 1e-9:
        raise ValueError("12.8/12.9 dataset critical-temperature level must follow the 50 C grid")
    fire_regime = str(dataset["fire_regime"]) if "fire_regime" in dataset else "standard"
    if fire_regime != "standard":
        raise ValueError("FIRE-D3 r1 matrix route is scoped to the standard fire regime")
    technical_docs_confirmed = bool(dataset["technical_documentation_12_7_9_confirmed"]) if "technical_documentation_12_7_9_confirmed" in dataset else False
    if not technical_docs_confirmed:
        raise ValueError("12.7 requires the protection-performance nomogram/matrix to be documented for the fire-protection product")
    source_kind = str(dataset["source_kind"]) if "source_kind" in dataset else "technical_documentation_12_7_9"
    validation_confirmed = bool(dataset["validation_12_6_confirmed"]) if "validation_12_6_confirmed" in dataset else False
    if source_kind == "validated_model_12_5" and not validation_confirmed:
        raise ValueError("A 12.5-generated matrix requires confirmed 12.6 validation")
    if source_kind not in {"technical_documentation_12_7_9", "fire_tests_12_4", "validated_model_12_5"}:
        raise ValueError("Unsupported performance_dataset.source_kind")
    if "reduced_thickness_axis_mm" not in dataset:
        raise ValueError("performance_dataset.reduced_thickness_axis_mm is required")
    delta_axis = _validate_axis(dataset["reduced_thickness_axis_mm"], "reduced_thickness_axis_mm")
    if "protection_thickness_axis_mm" not in dataset:
        raise ValueError("performance_dataset.protection_thickness_axis_mm is required")
    protection_axis = _validate_axis(dataset["protection_thickness_axis_mm"], "protection_thickness_axis_mm")
    matrix = dataset.get("time_matrix_min")
    if not isinstance(matrix, list) or len(matrix) != len(delta_axis):
        raise ValueError("time_matrix_min row count must match reduced_thickness_axis_mm")
    normalized: list[list[float]] = []
    for r, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != len(protection_axis):
            raise ValueError("Each time_matrix_min row must match protection_thickness_axis_mm")
        nr: list[float] = []
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"time_matrix_min[{r}][{c}] must be finite and >= 0")
            nr.append(float(value))
        normalized.append(nr)
    return {
        "product_id": str(dataset["product_id"]) if "product_id" in dataset else "UNSPECIFIED_PRODUCT",
        "source_kind": source_kind,
        "critical_temperature_c": documented_t,
        "steel_group": steel_group,
        "delta_axis": delta_axis,
        "protection_axis": protection_axis,
        "matrix": normalized,
        "allow_greater_delta_carry_forward": bool(dataset["allow_greater_delta_carry_forward"]) if "allow_greater_delta_carry_forward" in dataset else False,
    }


def _bracket(axis: Sequence[float], x: float, *, allow_upper_carry: bool = False) -> tuple[int, int, float, bool]:
    if x < axis[0] - 1e-12:
        raise ValueError("Query is below the documented interpolation domain")
    if x > axis[-1] + 1e-12:
        if allow_upper_carry:
            idx = len(axis) - 1
            return idx, idx, 0.0, True
        raise ValueError("Query is above the documented interpolation domain; extrapolation is forbidden")
    for i, value in enumerate(axis):
        if math.isclose(x, value, rel_tol=0.0, abs_tol=1e-12):
            return i, i, 0.0, False
    for i in range(len(axis) - 1):
        if axis[i] < x < axis[i + 1]:
            f = (x - axis[i]) / (axis[i + 1] - axis[i])
            return i, i + 1, f, False
    raise ValueError("Could not bracket query")


def _interpolate_delta_curve(dataset: Mapping[str, Any], delta_mm: float) -> tuple[list[float], dict[str, Any]]:
    axis = dataset["delta_axis"]
    i0, i1, f, carried = _bracket(axis, delta_mm, allow_upper_carry=bool(dataset["allow_greater_delta_carry_forward"]))
    matrix = dataset["matrix"]
    if i0 == i1:
        curve = list(matrix[i0])
    else:
        curve = [a + f * (b - a) for a, b in zip(matrix[i0], matrix[i1])]
    return curve, {
        "delta_bracket_mm": [axis[i0], axis[i1]],
        "delta_fraction": f,
        "greater_delta_carry_forward": carried,
    }


def _matrix_direct(case: Mapping[str, Any], dataset: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    thickness = _number(case, "protection_thickness_mm", positive=True)
    curve, delta_trace = _interpolate_delta_curve(dataset, delta_mm)
    p_axis = dataset["protection_axis"]
    j0, j1, f, carried = _bracket(p_axis, thickness, allow_upper_carry=False)
    assert not carried
    if j0 == j1:
        time_min = curve[j0]
    else:
        time_min = curve[j0] + f * (curve[j1] - curve[j0])
    nonmonotonic = any(b < a - 1e-9 for a, b in zip(curve, curve[1:]))
    warnings: list[str] = []
    if nonmonotonic:
        warnings.append("Resolved protection-thickness time curve is non-monotonic; source values were preserved without smoothing.")
    return {
        "status": "COMPLETE",
        "actual_fire_resistance_min": float(time_min),
        "calculated_time_min": float(time_min),
        "protection_thickness_mm": thickness,
        "matrix_interpolation_trace": {
            **delta_trace,
            "protection_bracket_mm": [p_axis[j0], p_axis[j1]],
            "protection_fraction": f,
        },
        "source_curve_nonmonotonic": nonmonotonic,
        "warnings": warnings,
    }


def _matrix_inverse(case: Mapping[str, Any], dataset: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    required = _number(case, "required_fire_resistance_min", positive=True)
    curve, delta_trace = _interpolate_delta_curve(dataset, delta_mm)
    axis = dataset["protection_axis"]
    nonmonotonic = any(b < a - 1e-9 for a, b in zip(curve, curve[1:]))
    thickness: float | None = None
    bracket: list[float] | None = None
    # Scan from the minimum thickness.  This finds the first continuous piecewise-linear
    # location at which the requirement is met, without assuming monotonic source data.
    if curve[0] >= required - 1e-12:
        thickness = axis[0]
        bracket = [axis[0], axis[0]]
    else:
        for j in range(len(axis) - 1):
            y0, y1 = curve[j], curve[j + 1]
            if y0 >= required - 1e-12:
                thickness = axis[j]
                bracket = [axis[j], axis[j]]
                break
            if y0 < required <= y1 + 1e-12:
                if math.isclose(y0, y1, abs_tol=1e-15):
                    thickness = axis[j + 1]
                else:
                    thickness = axis[j] + (required - y0) * (axis[j + 1] - axis[j]) / (y1 - y0)
                bracket = [axis[j], axis[j + 1]]
                break
    warnings: list[str] = []
    if nonmonotonic:
        warnings.append(
            "Resolved matrix curve is non-monotonic; inverse 12.10 search used the first qualifying piecewise-linear crossing and did not smooth the source data."
        )
    if thickness is None:
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "actual_fire_resistance_min": None,
            "minimum_protection_thickness_mm": None,
            "required_fire_resistance_min": required,
            "source_curve_nonmonotonic": nonmonotonic,
            "warnings": warnings,
            "diagnostic": "Required fire resistance is not reached within the documented protection-thickness domain; extrapolation is forbidden.",
            "matrix_interpolation_trace": delta_trace,
        }
    return {
        "status": "COMPLETE",
        "actual_fire_resistance_min": required,
        "minimum_protection_thickness_mm": float(thickness),
        "protection_thickness_mm": float(thickness),
        "required_fire_resistance_min": required,
        "inverse_crossing_bracket_mm": bracket,
        "source_curve_nonmonotonic": nonmonotonic,
        "warnings": warnings,
        "matrix_interpolation_trace": delta_trace,
    }


def _protected_fdm(case: Mapping[str, Any], delta_mm: float) -> dict[str, Any]:
    model = case.get("protection_model")
    if not isinstance(model, Mapping):
        raise ValueError("PROTECTED_FDM_12_5 requires protection_model")
    moisture = _number(model, "initial_moisture_percent", nonnegative=True)
    thickness_mm = _number(model, "thickness_mm", positive=True)
    layer_count_raw = model.get("layer_count")
    if isinstance(layer_count_raw, bool) or not isinstance(layer_count_raw, int) or layer_count_raw < 1:
        raise ValueError("protection_model.layer_count must be an integer >= 1")
    n = int(layer_count_raw)
    rho_p = _number(model, "density_kg_m3", positive=True)
    A_source = _number(model, "conductivity_A_w_mk")
    B = _number(model, "conductivity_B_w_mk2")
    C_source = _number(model, "heat_capacity_C_j_kgk", positive=True)
    D = _number(model, "heat_capacity_D_j_kgk2")
    temperature_basis = str(model["temperature_basis"]) if "temperature_basis" in model else "degC"
    if temperature_basis == "K":
        # Source law is lambda=A+B*T_K and c=C+D*T_K.  The solver state is in
        # degC, so shift only the intercepts; slopes and temperature differences
        # are unchanged.  This is algebraically exact: T_K=T_C+273.15.
        A = A_source + B * 273.15
        C = C_source + D * 273.15
    elif temperature_basis == "degC":
        A = A_source
        C = C_source
    else:
        raise ValueError("protection_model.temperature_basis must be K or degC")
    if A <= 0.0:
        raise ValueError("Protection conductivity at 0 C-equivalent state is non-positive after temperature-basis conversion")
    target = _number(case, "critical_temperature_c")
    initial = _optional_number(case, "initial_temperature_c", 20.0)
    dt_min = _optional_number(case, "time_step_min", 0.01)
    max_time_min = _optional_number(case, "max_time_min", 300.0)
    if dt_min <= 0.0 or dt_min > 0.1 + 1e-12:
        raise ValueError("PROTECTED_FDM_12_5 requires 0 < time_step_min <= 0.1 min")
    if max_time_min <= 0.0:
        raise ValueError("max_time_min must be > 0")
    params = _unprotected_parameters(case)
    if target > 800.0 + 1e-12 and params["source"] == "sp554_12_2_defaults":
        raise ValueError("Target above 800 C requires explicit steel thermal properties")
    surface_eps = float(params["eps_steel"])
    if "surface_emissivity" in model:
        surface_eps = _number(model, "surface_emissivity", positive=True)
        if surface_eps > 1.0:
            raise ValueError("protection_model.surface_emissivity must not exceed 1")
    eps_red = _reduced_emissivity(float(params["eps_fire"]), surface_eps)
    rho_s = float(params["rho"])
    c_s = float(params["c0"])
    d_s = float(params["kc"])
    delta_m = delta_mm / 1000.0
    dx = thickness_mm / 1000.0 / n
    protection_cp_initial = C + D * initial
    steel_cp_initial = _steel_heat_capacity_j_kgk(c_s, d_s, initial)
    initial_t_phi = sp554_fictitious_temperature_12_8(
        initial_moisture_percent=moisture,
        protection_density_kg_m3=rho_p,
        layer_thickness_m=dx,
        protection_heat_capacity_j_kgk=protection_cp_initial,
        steel_density_kg_m3=rho_s,
        reduced_steel_thickness_m=delta_m,
        steel_heat_capacity_j_kgk=steel_cp_initial,
    )
    moisture_policy = _moisture_accounting_policy(
        model, moisture_percent=moisture, initial_t_phi_c=initial_t_phi
    )
    # In the supported W>0 mode, moisture is already embodied in the experimentally
    # identified/nonlinear material properties, so t_phi is intentionally NOT subtracted.
    # This prevents double counting and retains mandatory 12.6 validation.
    # ``layer_count`` is the number of equal Δx intervals across the protection.
    # The state vector stores the heated-surface node plus the protection nodes
    # immediately preceding the steel interface; the final half protection cell is
    # lumped with the steel by (12.7).
    temperatures = [initial] * n
    steel_t = initial
    time_min = 0.0
    steps = 0
    history: list[dict[str, Any]] = []
    if target <= initial:
        calc_time = 0.0
    else:
        calc_time = None
        while time_min < max_time_min - 1e-12:
            next_time = min(time_min + dt_min, max_time_min)
            dt_s = (next_time - time_min) * 60.0
            fire_t = _standard_fire_temperature_c(next_time, initial)
            old = temperatures
            new = list(old)
            alpha = _heat_transfer_coefficient_w_m2k(fire_t, old[0], eps_red)
            cap0 = C + D * old[0]
            if cap0 <= 0.0:
                raise ValueError("Protection heat capacity C+D*T became non-positive at heated surface")
            right0 = old[1] if n > 1 else steel_t
            conduction0 = A * (right0 - old[0]) + 0.5 * B * (right0 ** 2 - old[0] ** 2)
            new[0] = old[0] + 2.0 * dt_s * (conduction0 + alpha * (fire_t - old[0]) * dx) / (rho_p * dx * dx * cap0)
            for i in range(1, n):
                cap = C + D * old[i]
                if cap <= 0.0:
                    raise ValueError("Protection heat capacity C+D*T became non-positive in an internal layer")
                right = old[i + 1] if i + 1 < n else steel_t
                lap_t = old[i - 1] - 2.0 * old[i] + right
                lap_t2 = old[i - 1] ** 2 - 2.0 * old[i] ** 2 + right ** 2
                new[i] = old[i] + dt_s * (A * lap_t + 0.5 * B * lap_t2) / (rho_p * dx * dx * cap)
            # Steel/protection interface, formula (12.7).  The protection half-cell and
            # the lumped steel section share the interface control volume.
            cap_interface = C + D * steel_t
            cp_steel = _steel_heat_capacity_j_kgk(c_s, d_s, steel_t)
            denominator = dx * (rho_p * dx * cap_interface + 2.0 * rho_s * delta_m * cp_steel)
            if denominator <= 0.0:
                raise ValueError("Protected-steel interface heat capacity became non-positive")
            last_protection = old[-1]
            flux_term = A * (last_protection - steel_t) + 0.5 * B * (last_protection ** 2 - steel_t ** 2)
            next_steel = steel_t + 2.0 * dt_s * flux_term / denominator
            all_new = [*new, next_steel]
            if any(not math.isfinite(x) for x in all_new):
                raise ValueError("Protected FDM produced a non-finite temperature")
            # Explicit-scheme stability gate: substantial reverse/overshoot states are not accepted.
            if next_steel < steel_t - 1e-7 or new[0] > fire_t + 5.0:
                raise ValueError("Protected FDM time step is numerically unstable; reduce time_step_min or increase layer size")
            steps += 1
            if steps <= 5 or steps % 500 == 0:
                history.append({
                    "time_min": next_time,
                    "fire_temperature_c": fire_t,
                    "surface_temperature_c": new[0],
                    "steel_temperature_c": next_steel,
                    "alpha_w_m2k": alpha,
                })
            if next_steel >= target:
                fraction = (target - steel_t) / (next_steel - steel_t) if next_steel > steel_t else 0.0
                calc_time = time_min + fraction * (next_time - time_min)
                temperatures = new
                steel_t = next_steel
                time_min = next_time
                break
            temperatures = new
            steel_t = next_steel
            time_min = next_time

    if calc_time is None:
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "actual_fire_resistance_min": None,
            "calculated_time_min": None,
            "steel_temperature_c_at_max_time": steel_t,
            "step_count": steps,
            "thermal_trace": history,
            "diagnostic": "Critical temperature was not reached inside max_time_min; no extrapolation performed.",
            "errata_overlay": _errata_overlay(),
            "moisture_accounting": moisture_policy,
            "surface_emissivity": surface_eps,
        }

    validation_rows: list[dict[str, float | bool]] = []
    if case.get("validation_evidence_preconfirmed") is True:
        complete = case.get("validation_evidence_complete")
        max_dev = case.get("validation_max_deviation_pct")
        criterion_confirmed = case.get("validation_within_20_percent_all_cases")
        basis = case.get("validation_evidence_basis")
        if complete is not True:
            raise ValueError("12.5 preconfirmed validation requires validation_evidence_complete=true")
        if max_dev is not None:
            if isinstance(max_dev, bool) or not isinstance(max_dev, (int, float)) or not math.isfinite(float(max_dev)) or float(max_dev) < 0.0:
                raise ValueError("validation_max_deviation_pct must be finite and >=0 when supplied")
            all_ok = float(max_dev) <= 20.0 + 1e-12
            validation_rows.append({
                "maximum_reported_deviation_pct": float(max_dev),
                "within_20_percent": all_ok,
                "evidence_complete": True,
                "evidence_basis": basis,
            })
        elif criterion_confirmed is True and isinstance(basis, str) and basis.strip():
            # Some source-traced libraries document the acceptance criterion
            # (<=20 %) and the calibration procedure without publishing a single
            # synthetic maximum-deviation number.  Preserve that distinction: do
            # not invent a numeric deviation merely to satisfy the runtime.
            all_ok = True
            validation_rows.append({
                "within_20_percent": True,
                "evidence_complete": True,
                "evidence_basis": basis.strip(),
                "maximum_reported_deviation_pct": None,
            })
        else:
            raise ValueError(
                "12.5 preconfirmed validation requires either validation_max_deviation_pct or "
                "validation_within_20_percent_all_cases=true with a non-empty validation_evidence_basis"
            )
    else:
        references = case.get("validation_reference_times_min")
        if not isinstance(references, list) or not references:
            raise ValueError("12.5 runtime requires validation_reference_times_min or preconfirmed 12.6 validation evidence")
        all_ok = True
        for idx, value in enumerate(references):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"validation_reference_times_min[{idx}] must be finite and > 0")
            ref = float(value)
            deviation = abs(float(calc_time) - ref) / ref
            ok = deviation <= 0.20 + 1e-12
            all_ok = all_ok and ok
            validation_rows.append({"reference_time_min": ref, "relative_deviation": deviation, "within_20_percent": ok})
    return {
        "status": "COMPLETE" if all_ok else "INVALID_BY_12_6",
        "actual_fire_resistance_min": float(calc_time) if all_ok else None,
        "calculated_time_min": float(calc_time),
        "critical_temperature_c": target,
        "step_count": steps,
        "thermal_trace": history,
        "validation_12_6": {
            "all_within_20_percent": all_ok,
            "cases": validation_rows,
            "result_valid": all_ok,
        },
        "dry_protection_only": moisture <= 1e-12,
        "moisture_accounting": moisture_policy,
        "errata_overlay": _errata_overlay(),
        "material_parameters": {
            **params,
            "protection_source_coefficients": {
                "conductivity_A_w_mk": A_source,
                "conductivity_B_w_mk2": B,
                "heat_capacity_C_j_kgk": C_source,
                "heat_capacity_D_j_kgk2": D,
                "temperature_basis": temperature_basis,
            },
            "protection_solver_coefficients_degC_basis": {
                "conductivity_A_w_mk": A,
                "conductivity_B_w_mk2": B,
                "heat_capacity_C_j_kgk": C,
                "heat_capacity_D_j_kgk2": D,
            },
        },
        "surface_emissivity": surface_eps,
    }


def _errata_overlay() -> dict[str, Any]:
    return {
        "status": "CONFIRMED_NORMATIVE_ERRATA_OVERLAY",
        "formula_12_5": {
            "source_literal": "+ t_n - t_phi",
            "production": "+ t_0 - t_phi",
            "basis": "predecessor ARSS finite-difference scheme + control-volume state consistency",
        },
        "formula_12_6": {
            "source_literal_denominator": "C + D*t_0",
            "production_denominator": "C + D*t_n",
            "basis": "predecessor ARSS finite-difference scheme + local-node heat capacity consistency",
        },
    }


def sp554_fire_thermal_guided_workflow(case: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute the FIRE-D3 SP554 Section 12 time-to-critical-temperature workflow without changing FIRE-D2 mechanical producers.

    Standard reference:
        Standard: SP554_2026 locked source, cross-checked against the enacted 2026 SP text
        Version: FIRE-D3 source lock inherited from v0.38
        Clause: 12.1-12.10 and result definition 13.2
        Annex: None
        Equation/Table: (12.1)-(12.8), Table 1, Figure 1, clauses 12.6-12.10
        Audit ID: FIRE-D3-RUNTIME-001
        Normative status: executable_with_confirmed_errata_overlay

    Mathematical form:
        Critical steel temperature -> standard-fire thermal integration or documented protection-performance interpolation -> time to critical temperature.

    Parameters:
        case:
            Type: Mapping[str, Any]
            Unit: mixed and explicitly named by field
            Meaning: Validated FIRE-D3 case containing the thermal route, critical temperature, reduced thickness and route-specific data.
            Valid range: Defined by SP554 Section 12 and the fail-closed runtime gates.
            Source: FIRE-D2 handoff plus user/product thermal data.

    Returns:
        Type: dict[str, Any]
        Unit: minutes, degrees Celsius, millimetres and dimensionless trace data as named
        Meaning: Actual fire-resistance time or a fail-closed/invalid diagnostic bundle.

    Assumptions:
        - Temperature is uniform over the steel cross-section per 12.1.
        - The standard fire is evaluated at the end of each explicit time increment.
        - The radiation fourth-power term is evaluated in absolute temperature while temperature differences remain numerically identical in K and C.
        - FIRE-D2 supplies the governing critical steel temperature; this module does not recalculate member resistance.

    Sign convention:
        - Heat flow from the furnace toward the steel/protection is positive.
        - Temperatures use degrees Celsius for state variables; absolute temperature is used only inside radiation fourth powers.

    Unit convention:
        - Time is minutes at the API and seconds internally in heat-balance updates.
        - Reduced steel and protection thicknesses are millimetres at the API and metres internally.
        - Density is kg/m3, heat capacity J/(kg K), conductivity W/(m K), alpha W/(m2 K).

    Applicability:
        - UNPROTECTED_STEP_12_2: formulas (12.1)-(12.4) under the standard fire.
        - UNPROTECTED_FIGURE1_12_2: the printed/reconstructed 3-20 mm Figure 1 domain with linear interpolation.
        - PROTECTED_MATRIX_12_10: documented 12.7-12.9 matrix/nomogram slice at an exact critical-temperature level, direct or inverse task.
        - PROTECTED_FDM_12_5: one-dimensional protection model with mandatory 12.6 validation; W=0 is direct, while W>0 is executable only when moisture is explicitly confirmed as embedded in validated thermal properties.

    Limitations:
        - No critical-temperature interpolation is invented for 12.8/12.9 matrices; an exact documented 50 C level is required.
        - Protection-thickness extrapolation is forbidden. Greater reduced-thickness carry-forward is allowed only when explicitly documented under 12.4.
        - Formula (12.8) is algebraically implemented and its use reconciled against predecessor/ARSS clarification. Literal repeated t_phi subtraction remains fail-closed because no moisture-depletion state is specified; W>0 may execute only when moisture is already embedded in validated thermal properties, in which case t_phi is omitted to avoid double counting.
        - FIRE-D3 does not cover connection fire resistance.

    Raises:
        ValueError: Required route inputs are absent, the query is outside the normative/data domain, validation fails structurally, or a numerical step is unstable.

    Examples:
        >>> sp554_fire_thermal_guided_workflow({"thermal_route":"UNPROTECTED_STEP_12_2","critical_temperature_c":525.0192844353662,"reduced_thickness_mm":10.0})["actual_fire_resistance_min"]
        14.326394173167

    Tests:
        Unit tests:
            - tests/test_fire_d3_sp554_thermal.py
        Validation cases:
            - FIRE-D3-UNPROTECTED-CONTROL-001
            - FIRE-D3-MATRIX-001
            - FIRE-D3-FDM-DRY-001

    Implementation notes:
        - The two locked-text errors in (12.5) and (12.6) are never executed literally; the production corrections are emitted in every FDM result.
        - Non-monotonic product matrices are preserved. Inverse 12.10 uses the first qualifying piecewise-linear crossing rather than smoothing or assuming monotonicity.
        - SP554 default steel heat capacity uses C*(1+D*T), matching the frozen reconstructed Figure 1 producer already present in the cumulative DAG.
        - FIRE-D3.1 separates scalar evaluation of (12.8) from executable moisture accounting; it never treats t_phi as an unbounded per-time-step decrement.
    """
    if not isinstance(case, Mapping):
        raise TypeError("case must be a mapping")
    route = str(case["thermal_route"]) if "thermal_route" in case else ""
    target = _number(case, "critical_temperature_c")
    delta_mm, delta_trace = _resolve_reduced_thickness_mm(case)
    base = {
        "thermal_route": route,
        "critical_temperature_c": target,
        "reduced_thickness_mm": delta_mm,
        "reduced_thickness_trace": delta_trace,
        "result_definition": "SP554_13.2_time_from_heat_exposure_start_to_critical_steel_temperature",
        "fire_regime": "standard",
        "fire_d2_handoff_preserved": True,
    }
    if route == "UNPROTECTED_STEP_12_2":
        result = _unprotected_step_time(case, delta_mm)
        result.update(base)
        result["normative_route"] = "SP554_12.1_12.2_formulas_12.1_to_12.4"
        return result
    if route == "UNPROTECTED_FIGURE1_12_2":
        result = _figure1_time(case, delta_mm)
        result.update(base)
        result["normative_route"] = "SP554_12.2_Figure_1"
        return result
    if route == "PROTECTED_MATRIX_12_10":
        if "performance_dataset" not in case:
            raise ValueError("performance_dataset is required for PROTECTED_MATRIX_12_10")
        dataset = _validate_matrix_dataset(case["performance_dataset"], target)
        mode = str(case["protected_task_mode"]) if "protected_task_mode" in case else "verify_given_thickness"
        if mode == "verify_given_thickness":
            result = _matrix_direct(case, dataset, delta_mm)
        elif mode == "determine_minimum_thickness":
            result = _matrix_inverse(case, dataset, delta_mm)
        else:
            raise ValueError("protected_task_mode must be verify_given_thickness or determine_minimum_thickness")
        result.update(base)
        result["normative_route"] = "SP554_12.7_12.10_documented_performance_matrix"
        result["product_id"] = dataset["product_id"]
        result["performance_data_source_kind"] = dataset["source_kind"]
        return result
    if route == "PROTECTED_FDM_12_5":
        result = _protected_fdm(case, delta_mm)
        result.update(base)
        result["normative_route"] = "SP554_12.5_1D_FDM_with_12.6_validation"
        return result
    raise ValueError(
        "thermal_route must be UNPROTECTED_STEP_12_2, UNPROTECTED_FIGURE1_12_2, PROTECTED_MATRIX_12_10, or PROTECTED_FDM_12_5"
    )
