"""FIRE-D2 member fire-mechanics runtime for the locked 2026 SP554 draft."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence


# Exact Table B.1 knots transcribed from the locked 2026 draft.  The two
# coefficients are independently interpolated only along the published figure
# polylines.  No extrapolation is performed.
_B1: dict[str, tuple[tuple[float, float, float], ...]] = {
    "ordinary": (
        (20.0, 1.00, 1.00), (250.0, 1.00, 1.00), (300.0, 0.94, 0.84),
        (350.0, 0.89, 0.78), (400.0, 0.84, 0.72), (450.0, 0.79, 0.67),
        (500.0, 0.73, 0.61), (550.0, 0.67, 0.54), (600.0, 0.59, 0.45),
        (650.0, 0.52, 0.34), (700.0, 0.43, 0.20),
    ),
    "increased": (
        (20.0, 1.00, 1.00), (250.0, 1.00, 1.00), (300.0, 0.96, 0.84),
        (350.0, 0.92, 0.75), (400.0, 0.88, 0.70), (450.0, 0.85, 0.65),
        (500.0, 0.81, 0.60), (550.0, 0.75, 0.55), (600.0, 0.66, 0.46),
        (650.0, 0.53, 0.34), (700.0, 0.35, 0.18),
    ),
    "high": (
        (20.0, 1.00, 1.00), (250.0, 1.00, 1.00), (300.0, 0.95, 0.8934),
        (350.0, 0.90, 0.83), (400.0, 0.86, 0.79), (450.0, 0.82, 0.75),
        (500.0, 0.78, 0.71), (550.0, 0.73, 0.66), (600.0, 0.68, 0.58),
        (650.0, 0.62, 0.47), (700.0, 0.54, 0.32),
    ),
    "fire_resistant": (
        (20.0, 1.00, 1.00), (250.0, 1.00, 1.00), (300.0, 0.96, 0.96),
        (350.0, 0.93, 0.95), (400.0, 0.90, 0.92), (450.0, 0.86, 0.89),
        (500.0, 0.82, 0.83), (550.0, 0.77, 0.76), (600.0, 0.71, 0.68),
        (650.0, 0.65, 0.58), (700.0, 0.58, 0.47), (750.0, 0.50, 0.33),
        (800.0, 0.42, 0.20), (850.0, 0.33, 0.02),
    ),
}


def _number(obj: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in obj:
        raise ValueError(f"Missing required FIRE-D2 input: {key}")
    value = float(obj[key])
    if not math.isfinite(value):
        raise ValueError(f"FIRE-D2 input {key} must be finite")
    if positive and value <= 0.0:
        raise ValueError(f"FIRE-D2 input {key} must be > 0")
    if nonnegative and value < 0.0:
        raise ValueError(f"FIRE-D2 input {key} must be >= 0")
    return value


def _flag(obj: Mapping[str, Any], key: str) -> bool:
    if key not in obj:
        raise ValueError(f"Missing required FIRE-D2 input: {key}")
    value = obj[key]
    if not isinstance(value, bool):
        raise ValueError(f"FIRE-D2 input {key} must be boolean")
    return value


def _string(obj: Mapping[str, Any], key: str) -> str:
    if key not in obj:
        raise ValueError(f"Missing required FIRE-D2 input: {key}")
    value = obj[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"FIRE-D2 input {key} must be a non-empty string")
    return value.strip()


def _optional_number(obj: Mapping[str, Any], key: str) -> float | None:
    if key not in obj or obj[key] is None:
        return None
    value = float(obj[key])
    if not math.isfinite(value):
        raise ValueError(f"FIRE-D2 input {key} must be finite")
    return value


def _effective_steel_group(case: Mapping[str, Any]) -> tuple[str, list[str]]:
    requested = _string(case, "steel_strength_group")
    if requested not in _B1:
        raise ValueError("steel_strength_group must be ordinary, increased, high, or fire_resistant")
    notes: list[str] = []
    if requested == "high":
        qualified = _flag(case, "high_strength_gost9651_qualified")
        if not qualified:
            notes.append("Table B.1 note 1 fallback applied: unqualified high-strength steel uses increased-strength coefficients.")
            return "increased", notes
    if requested == "fire_resistant":
        qualified = _flag(case, "fire_resistant_gost9651_qualified")
        if not qualified:
            raise ValueError(
                "Fire-resistant Table B.1 coefficients require the explicit GOST 9651 qualification / retention evidence stated in Table B.1 note 2"
            )
    return requested, notes


def _curve_index(kind: str) -> int:
    if kind == "gamma_E":
        return 1
    if kind == "gamma_T":
        return 2
    raise ValueError("Curve kind must be gamma_T or gamma_E")


def _inverse_b1(group: str, kind: str, gamma: float) -> dict[str, Any]:
    if not math.isfinite(gamma) or gamma <= 0.0:
        raise ValueError(f"Required {kind} must be finite and > 0")
    rows = _B1[group]
    idx = _curve_index(kind)
    minimum = rows[-1][idx]
    maximum_temperature = rows[-1][0]
    if gamma > 1.0:
        return {
            "status": "AMBIENT_CAPACITY_EXCEEDED",
            "temperature_c": 20.0,
            "temperature_relation": "<=",
            "published_minimum_gamma": minimum,
            "published_maximum_temperature_c": maximum_temperature,
        }
    if gamma < minimum:
        return {
            "status": "ABOVE_PUBLISHED_TEMPERATURE_RANGE",
            "temperature_c": None,
            "temperature_lower_bound_c": maximum_temperature,
            "temperature_relation": ">",
            "published_minimum_gamma": minimum,
            "published_maximum_temperature_c": maximum_temperature,
        }
    if math.isclose(gamma, 1.0, rel_tol=0.0, abs_tol=1e-12):
        return {
            "status": "EXACT_WITHIN_PUBLISHED_CURVE",
            "temperature_c": 250.0,
            "temperature_relation": "=",
            "published_minimum_gamma": minimum,
            "published_maximum_temperature_c": maximum_temperature,
        }
    # Curves are monotone non-increasing.  Use the upper end of the unit plateau
    # and then linearly interpolate the plotted segments.
    for left, right in zip(rows[1:-1], rows[2:]):
        t0, g0 = left[0], left[idx]
        t1, g1 = right[0], right[idx]
        upper = max(g0, g1)
        lower = min(g0, g1)
        if lower - 1e-12 <= gamma <= upper + 1e-12:
            if math.isclose(g0, g1, rel_tol=0.0, abs_tol=1e-15):
                temperature = t1
            else:
                temperature = t0 + (gamma - g0) * (t1 - t0) / (g1 - g0)
            return {
                "status": "EXACT_WITHIN_PUBLISHED_CURVE",
                "temperature_c": float(temperature),
                "temperature_relation": "=",
                "published_minimum_gamma": minimum,
                "published_maximum_temperature_c": maximum_temperature,
            }
    raise ValueError(f"Could not bracket {kind}={gamma} on the published Table B.1 / figure polyline")


def _forward_b1(group: str, kind: str, temperature_c: float) -> float:
    rows = _B1[group]
    idx = _curve_index(kind)
    if temperature_c < rows[0][0] - 1e-12 or temperature_c > rows[-1][0] + 1e-12:
        raise ValueError("Temperature is outside the published Table B.1 curve domain")
    if temperature_c <= 250.0:
        return 1.0
    for left, right in zip(rows[1:-1], rows[2:]):
        t0, g0 = left[0], left[idx]
        t1, g1 = right[0], right[idx]
        if t0 - 1e-12 <= temperature_c <= t1 + 1e-12:
            if math.isclose(t0, t1):
                return float(g1)
            return float(g0 + (temperature_c - t0) * (g1 - g0) / (t1 - t0))
    return float(rows[-1][idx])


def _phi_9_2(route: Mapping[str, Any]) -> tuple[float, dict[str, Any]]:
    lam = _number(route, "lambda_bar", nonnegative=True)
    curve = _string(route, "buckling_curve_type").lower()
    if curve not in {"a", "b", "c"}:
        raise ValueError("buckling_curve_type must be a, b, or c")
    phi_sp16 = _number(route, "phi_sp16_formula8", positive=True)
    if lam < 0.6 and curve in {"a", "b"}:
        return 1.0, {"rule": "SP554_9_2_LOW_SLENDERNESS", "phi_sp16_formula8": phi_sp16}
    threshold = {"a": 3.8, "b": 4.4, "c": 5.8}[curve]
    cap = None
    phi = phi_sp16
    if lam > threshold:
        cap = 7.6 / (lam * lam)
        phi = min(phi, cap)
    return phi, {"rule": "SP554_9_2_SP16_PHI_WITH_HIGH_SLENDERNESS_CAP", "phi_sp16_formula8": phi_sp16, "phi_cap": cap}


def _gamma_e(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[float, float]:
    n = abs(_number(route, "N_n", nonnegative=True))
    mu = _number(route, "mu_length_sp16", positive=True)
    length = _number(route, "member_length_mm", positive=True)
    e_mod = _number(case, "E_norm_n_mm2", positive=True)
    j_min = _number(route, "J_min_mm4", positive=True)
    l_eff = mu * length
    gamma_e = n * l_eff * l_eff / (math.pi * math.pi * e_mod * j_min)
    return gamma_e, l_eff


def _strength_candidate(formula_ref: str, value: float, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{formula_ref} produced non-positive/non-finite required gamma_T")
    row: dict[str, Any] = {"formula_ref": formula_ref, "gamma_T_required": float(value)}
    if details is not None:
        row["details"] = dict(details)
    return row


def _central_tension(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    n = abs(_number(route, "N_n", positive=True))
    area = _number(route, "A_net_mm2", positive=True)
    fy = _number(case, "fy_norm_n_mm2", positive=True)
    gamma_c = _number(route, "gamma_c", positive=True)
    gamma_t = n / (area * fy * gamma_c)
    return [_strength_candidate("9.1", gamma_t)], None, {"route": "central_tension"}


def _central_compression(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    n = abs(_number(route, "N_n", positive=True))
    area = _number(route, "A_gross_mm2", positive=True)
    fy = _number(case, "fy_norm_n_mm2", positive=True)
    gamma_c = _number(route, "gamma_c", positive=True)
    phi, phi_trace = _phi_9_2(route)
    gamma_t = n / (phi * area * fy * gamma_c)
    gamma_e, l_eff = _gamma_e(case, route)
    return [_strength_candidate("9.2", gamma_t, {"phi": phi, **phi_trace})], gamma_e, {
        "route": "central_compression", "phi": phi, "l_eff_mm": l_eff
    }


def _require_section10_ltb_applicability(check: Mapping[str, Any], formula_ref: str) -> None:
    """Fail closed when SP554 10.2 class/material applicability is not proven."""
    section_family = _string(check, "section_family")
    is_bisteel = _flag(check, "beam_is_bisteel")
    section_class = _string(check, "sp16_section_class")
    if section_family != "i_section":
        raise ValueError(f"{formula_ref} requires an I-beam section under SP554 10.2")
    expected_class = "2" if is_bisteel else "1"
    if section_class != expected_class:
        route_name = "bisteel I-beam" if is_bisteel else "ordinary I-beam"
        raise ValueError(
            f"{formula_ref} applicability failed: {route_name} requires SP16 NDS class {expected_class}; got {section_class}"
        )


def _require_11_2_applicability(route: Mapping[str, Any]) -> None:
    """Fail closed unless all explicit SP554 11.3 gates for formula (11.2) are satisfied."""
    if _string(route, "stress_state") != "compression_plus_bending":
        raise ValueError("11.2 applies only to compression+bending")
    if not _flag(route, "section_is_constant"):
        raise ValueError("11.2 requires a constant section")
    if not _flag(route, "moment_plane_is_symmetry"):
        raise ValueError("11.2 requires the moment plane to coincide with a symmetry plane")
    if _flag(route, "mef_gt_20"):
        raise ValueError("11.2 is not applicable for m_eff > 20; route as a bending member")


def _require_11_7_applicability(route: Mapping[str, Any]) -> None:
    """Fail closed on the SP554 11.7 non-box biaxial N+M classification route."""
    if _string(route, "stress_state") != "compression_plus_bending":
        raise ValueError("11.7 requires compression+bending")
    if not _flag(route, "section_is_constant"):
        raise ValueError("11.7 requires a constant section")
    if _flag(route, "section_is_box"):
        raise ValueError("11.7 is the non-box route; box sections use 11.8-11.10")
    major_symmetry_route = _flag(route, "major_axis_is_x") and _flag(route, "moment_plane_is_symmetry")
    table21_type3_route = _string(route, "sp16_table21_type") == "3"
    if not (major_symmetry_route or table21_type3_route):
        raise ValueError("11.7 requires major-axis symmetry route or SP16 Table 21 section type 3")


def _bending(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    fy = _number(case, "fy_norm_n_mm2", positive=True)
    gamma_c = _number(route, "gamma_c", positive=True)
    if "checks" not in route or not isinstance(route["checks"], Mapping):
        raise ValueError("bending route requires checks object")
    checks: Mapping[str, Any] = route["checks"]
    candidates: list[dict[str, Any]] = []

    if "eq_10_1" in checks:
        c = checks["eq_10_1"]
        mx = abs(_number(c, "M_x_nmm", nonnegative=True))
        my = abs(_number(c, "M_y_nmm", nonnegative=True))
        w = _number(c, "W_pl_min_eff_mm3", positive=True)
        candidates.append(_strength_candidate("10.1", max(mx, my) / (w * fy * gamma_c)))

    if "eq_10_2" in checks:
        c = checks["eq_10_2"]
        alpha_h = _number(c, "alpha_h", positive=True)
        q = abs(_number(c, "Q_n", nonnegative=True))
        s = _number(c, "S_mm3", positive=True)
        inertia = _number(c, "I_mm4", positive=True)
        tw = _number(c, "t_w_mm", positive=True)
        candidates.append(_strength_candidate("10.2", alpha_h * q * s / (inertia * tw * 0.58 * fy * gamma_c)))

    if "eq_10_3" in checks:
        c = checks["eq_10_3"]
        mx = _number(c, "M_x_nmm")
        my = _number(c, "M_y_nmm")
        bim = _number(c, "B_nmm2")
        ix = _number(c, "I_xn_mm4", positive=True)
        iy = _number(c, "I_yn_mm4", positive=True)
        iw = _number(c, "I_omega_n_mm6", positive=True)
        points = c["section_points"] if "section_points" in c else None
        if not isinstance(points, Sequence) or isinstance(points, (str, bytes)) or not points:
            raise ValueError("eq_10_3 requires non-empty section_points")
        values = []
        for point in points:
            if not isinstance(point, Mapping):
                raise ValueError("eq_10_3 section point must be an object")
            x = _number(point, "x_mm")
            y = _number(point, "y_mm")
            omega = _number(point, "omega_mm2")
            term = mx * y / ix + my * x / iy + bim * omega / iw
            values.append(abs(term) / (fy * gamma_c))
        candidates.append(_strength_candidate("10.3", max(values)))

    if "eq_10_4_10_5" in checks:
        c = checks["eq_10_4_10_5"]
        mx = _number(c, "M_x_nmm")
        q = _number(c, "Q_n")
        alpha_h = _number(c, "alpha_h", positive=True)
        s = _number(c, "S_mm3", positive=True)
        inertia_shear = _number(c, "I_shear_mm4", positive=True)
        tw = _number(c, "t_w_mm", positive=True)
        ix = _number(c, "I_xn_mm4", positive=True)
        tau = alpha_h * q * s / (inertia_shear * tw)
        points = c["section_points"] if "section_points" in c else None
        if not isinstance(points, Sequence) or isinstance(points, (str, bytes)) or not points:
            raise ValueError("eq_10_4_10_5 requires non-empty section_points")
        equivalent: list[float] = []
        for point in points:
            if not isinstance(point, Mapping):
                raise ValueError("eq_10_4_10_5 section point must be an object")
            y = _number(point, "y_mm")
            sigma_y = _number(point, "sigma_y_n_mm2")
            sigma_x = mx * y / ix
            invariant = sigma_x * sigma_x - sigma_x * sigma_y + sigma_y * sigma_y + 3.0 * tau * tau
            equivalent.append(0.87 * math.sqrt(max(0.0, invariant)) / (fy * gamma_c))
        candidates.append(_strength_candidate("10.4", max(equivalent)))
        candidates.append(_strength_candidate("10.5", abs(tau) / (0.58 * gamma_c * fy)))

    if "eq_10_6" in checks:
        c = checks["eq_10_6"]
        _require_section10_ltb_applicability(c, "10.6")
        mx = abs(_number(c, "M_x_nmm", positive=True))
        phi_b = _number(c, "phi_b_sp16", positive=True)
        w = _number(c, "W_pl_x_eff_mm3", positive=True)
        candidates.append(_strength_candidate("10.6", mx / (phi_b * w * fy * gamma_c)))

    if "eq_10_7" in checks:
        c = checks["eq_10_7"]
        _require_section10_ltb_applicability(c, "10.7")
        mx = abs(_number(c, "M_x_nmm", nonnegative=True))
        my = abs(_number(c, "M_y_nmm", nonnegative=True))
        bim = abs(_number(c, "B_nmm2", nonnegative=True))
        phi_b = _number(c, "phi_b_sp16", positive=True)
        wx = _number(c, "W_pl_x_eff_mm3", positive=True)
        wy = _number(c, "W_pl_y_eff_mm3", positive=True)
        ww = _number(c, "W_omega_eff_mm4", positive=True)
        sy = _number(c, "M_y_term_sign")
        sb = _number(c, "B_term_sign")
        if sy not in {-1.0, 1.0} or sb not in {-1.0, 1.0}:
            raise ValueError("M_y_term_sign and B_term_sign must be -1 or +1")
        gamma_t = mx / (phi_b * wx * fy * gamma_c) + sy * my / (wy * fy * gamma_c) + sb * bim / (ww * fy * gamma_c)
        candidates.append(_strength_candidate("10.7", gamma_t))

    if not candidates:
        raise ValueError("bending route must enable at least one Section 10 check")
    return candidates, None, {"route": "bending", "governing_policy": "MAX_REQUIRED_GAMMA_T_EQUIVALENT_TO_MIN_CRITICAL_TEMPERATURE"}


def _combined_nm(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    fy = _number(case, "fy_norm_n_mm2", positive=True)
    n = abs(_number(route, "N_n", positive=True))
    gamma_c_strength = _number(route, "gamma_c_strength", positive=True)
    gamma_c_stability = _number(route, "gamma_c_stability", positive=True)
    area_net = _number(route, "A_net_mm2", positive=True)
    wx = _number(route, "W_pl_x_eff_mm3", positive=True)
    wy = _number(route, "W_pl_y_eff_mm3", positive=True)
    mx = abs(_number(route, "M_x_nmm", nonnegative=True))
    my = abs(_number(route, "M_y_nmm", nonnegative=True))
    bim = abs(_number(route, "B_nmm2", nonnegative=True))
    ww = _number(route, "W_omega_eff_mm4", positive=True)
    stress_state = _string(route, "stress_state")
    if stress_state not in {"compression_plus_bending", "tension_plus_bending"}:
        raise ValueError("11.1 requires stress_state compression_plus_bending or tension_plus_bending")
    gamma_11_1 = n / (area_net * fy * gamma_c_strength) + mx / (wx * fy * gamma_c_strength) + my / (wy * fy * gamma_c_strength) + bim / (ww * fy * gamma_c_strength)
    candidates = [_strength_candidate("11.1", gamma_11_1)]
    mode = _string(route, "stability_mode")
    if stress_state == "tension_plus_bending" and mode != "none":
        raise ValueError("tension+bending route may use 11.1 strength only; compression stability modes are not applicable")
    area = _number(route, "A_gross_mm2", positive=True)
    trace: dict[str, Any] = {"route": "combined_nm", "stability_mode": mode, "stress_state": stress_state}

    if mode == "none":
        gamma_e = None
    else:
        gamma_e, l_eff = _gamma_e(case, route)
        trace["l_eff_mm"] = l_eff

    if mode == "in_plane":
        _require_11_2_applicability(route)
        phi_e = _number(route, "phi_e_sp16", positive=True)
        candidates.append(_strength_candidate("11.2", n / (phi_e * area * gamma_c_stability * fy)))
        eta = _optional_number(route, "eta_sp16")
        m_for = _optional_number(route, "M_for_11_3_nmm")
        w_for = _optional_number(route, "W_pl_for_11_3_mm3")
        if eta is not None and m_for is not None and w_for is not None:
            e = abs(m_for) / n
            m = e * area / w_for
            trace.update({"e_11_3_mm": e, "m_11_3": m, "m_eff_11_3": eta * m})
    elif mode == "out_of_plane_major":
        c_sp16 = _number(route, "c_sp16", positive=True)
        phi_y = _number(route, "phi_y_sp16", positive=True)
        candidates.append(_strength_candidate("11.4", n / (c_sp16 * phi_y * area * gamma_c_stability * fy)))
    elif mode == "minor_axis":
        _require_11_2_applicability(route)
        phi_e = _number(route, "phi_e_sp16", positive=True)
        candidates.append(_strength_candidate("11.2", n / (phi_e * area * gamma_c_stability * fy)))
        lambda_x = _number(route, "lambda_bar_x", nonnegative=True)
        lambda_y = _number(route, "lambda_bar_y", nonnegative=True)
        if lambda_x > lambda_y:
            phi_x = _number(route, "phi_x_sp16", positive=True)
            candidates.append(_strength_candidate("11.5", n / (phi_x * area * gamma_c_stability * fy)))
    elif mode == "biaxial_nonbox":
        _require_11_7_applicability(route)
        phi_ey = _number(route, "phi_ey_sp16", positive=True)
        c_sp16 = _number(route, "c_sp16", positive=True)
        phi_exy = phi_ey * (0.6 * c_sp16 ** (1.0 / 3.0) + 0.4 * c_sp16 ** 0.25)
        candidates.append(_strength_candidate("11.6", n / (phi_exy * area * gamma_c_stability * fy), {"phi_exy_11_7": phi_exy}))
        trace["phi_exy_11_7"] = phi_exy
    elif mode == "box":
        phi_ex = _number(route, "phi_ex_sp16", positive=True)
        phi_ey = _number(route, "phi_ey_sp16", positive=True)
        phi_y = _number(route, "phi_y_sp16", positive=True)
        lambda_x = _number(route, "lambda_bar_x", nonnegative=True)
        lambda_y = _number(route, "lambda_bar_y", nonnegative=True)
        delta_x = 1.0 if lambda_x <= 1.0 else 1.0 + 0.1 * n * lambda_x * lambda_x / (area * fy)
        delta_y = 1.0 if lambda_y <= 1.0 else 1.0 + 0.1 * n * lambda_y * lambda_y / (area * fy)
        gx = n / (phi_ex * area * gamma_c_stability * fy) + mx / (delta_x * wx * gamma_c_stability * fy)
        major_axis_is_x = _flag(route, "major_axis_is_x")
        phi_for_y = phi_y if major_axis_is_x and math.isclose(my, 0.0, abs_tol=1e-12) else phi_ey
        gy = n / (phi_for_y * area * gamma_c_stability * fy) + my / (delta_y * wy * gamma_c_stability * fy)
        candidates.append(_strength_candidate("11.8", gx, {"delta_x_11_10": delta_x}))
        candidates.append(_strength_candidate("11.9", gy, {"delta_y_11_10": delta_y, "phi_y_route": phi_for_y}))
        trace.update({"delta_x_11_10": delta_x, "delta_y_11_10": delta_y})
    elif mode != "none":
        raise ValueError("Unsupported combined_nm stability_mode")

    return candidates, gamma_e, trace


def _static_stress(case: Mapping[str, Any], route: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    sigma = abs(_number(route, "sigma_n_static_n_mm2", positive=True))
    fy = _number(case, "fy_norm_n_mm2", positive=True)
    gamma_t = sigma / fy
    compression = _flag(route, "compression_stability_applicable")
    if compression:
        gamma_e, l_eff = _gamma_e(case, route)
        return [_strength_candidate("8.7", gamma_t)], gamma_e, {"route": "static_stress_8_7", "l_eff_mm": l_eff}
    return [_strength_candidate("8.7", gamma_t)], None, {"route": "static_stress_8_7"}


def _critical_selection(group: str, gamma_t: float, gamma_e: float | None) -> dict[str, Any]:
    strength = _inverse_b1(group, "gamma_T", gamma_t)
    modulus = _inverse_b1(group, "gamma_E", gamma_e) if gamma_e is not None else None

    exact: list[tuple[str, float]] = []
    if strength["temperature_c"] is not None:
        exact.append(("gamma_T", float(strength["temperature_c"])))
    if modulus is not None and modulus["temperature_c"] is not None:
        exact.append(("gamma_E", float(modulus["temperature_c"])))

    if any(row[1] <= 20.0 + 1e-12 for row in exact):
        controlling = min(exact, key=lambda item: item[1])
        return {
            "status": "AMBIENT_CAPACITY_EXCEEDED",
            "critical_temperature_c": 20.0,
            "controlling_kind": controlling[0],
            "strength_inversion": strength,
            "modulus_inversion": modulus,
        }

    if exact:
        controlling = min(exact, key=lambda item: item[1])
        # A competing branch beyond the published upper-temperature limit cannot
        # govern earlier than an exact temperature that is already inside the
        # published domain, so the exact lower temperature is sufficient.
        return {
            "status": "COMPLETE",
            "critical_temperature_c": controlling[1],
            "controlling_kind": controlling[0],
            "strength_inversion": strength,
            "modulus_inversion": modulus,
        }

    lower_bounds = [float(strength["temperature_lower_bound_c"])] if "temperature_lower_bound_c" in strength else []
    if modulus is not None and "temperature_lower_bound_c" in modulus:
        lower_bounds.append(float(modulus["temperature_lower_bound_c"]))
    return {
        "status": "INCOMPLETE_FAIL_CLOSED",
        "critical_temperature_c": None,
        "critical_temperature_lower_bound_c": min(lower_bounds) if lower_bounds else None,
        "controlling_kind": None,
        "strength_inversion": strength,
        "modulus_inversion": modulus,
    }


def sp554_fire_mechanical_guided_workflow(case: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute one selected SP554 Sections 8-11 member fire-mechanics route and determine critical steel temperature.

    Standard reference:
        Locked 2026 draft SP554 clauses 7.2, 8.1-8.7, 9.1-9.3, 10.1-10.3, 11.1-11.9; equations (8.1)-(8.4), (9.1)-(9.2), (10.1)-(10.7), (11.1)-(11.10); mandatory Appendix B Table B.1 and Figures B.1-B.8. FIRE-D2 audit ID: FIRE-D2-RUNTIME-001.

    Parameters:
        case: Validated mapping containing member_route, normative yield strength, ambient modulus, Appendix-B steel group / qualification evidence, and route-specific mechanical inputs.

    Returns:
        Traceable dictionary with all applicable gamma_T candidates, governing required gamma_T, optional gamma_E, independent Appendix-B inversions, governing critical temperature, and heated properties at the governing temperature when it lies inside the published curve domain.

    Assumptions:
        The static mechanical assumptions are those stated by SP554 7.2: no fire-time history in the strength solution, no non-uniform section-temperature field, and no thermal-expansion restraint effects in FIRE-D2. Supplied actions are the normative special-combination effects required by SP554 8.1.

    Sign convention:
        Axial checks use force magnitudes. Equation (10.7) requires explicit +1/-1 signs for the transverse-moment and bimoment terms at the governing point. Other formulas follow their printed absolute-value conventions.

    Unit convention:
        N, mm, N*mm, N*mm^2, mm^2, mm^3, mm^4, mm^6, N/mm^2, degrees Celsius; reduction coefficients are dimensionless.

    Applicability:
        Hot-rolled load-bearing steel members in the locked draft scope. Supported routes are central_tension, central_compression, bending, combined_nm, and static_stress_8_7.

    Limitations:
        No Appendix-B extrapolation. High-strength and fire-resistant coefficient groups require the Table-B.1 qualification evidence. FIRE-D2 explicitly remediates the internally inconsistent locked-draft governing wording in 8.6/10.3/11.9 by converting each applicable limit criterion to its own critical temperature and selecting the earliest temperature. This stage does not solve SP554 Section 12 heat transfer or fire resistance of connections.

    Raises:
        ValueError: Missing, non-finite, non-positive, unsupported, unqualified, or otherwise non-auditable inputs; also route combinations that would require inventing a normative rule.

    Examples:
        See examples/fire_d2_sp554_critical_temperature_case.json.

    Tests:
        tests/test_fire_d2_sp554_runtime.py and tests/test_fire_d2_dag.py cover all formula families, Appendix-B domain guards, steel-group qualification, and governing-temperature remediation.

    Implementation notes:
        Appendix-B interpolation is a deterministic digital-polyline interpretation of the published figures between exact Table-B.1 knots. gamma=1 maps to 250 C, the upper end of the published unit-coefficient plateau. The predecessor ARSS method independently converts gamma_T and gamma_E to two temperatures and takes the lower; FIRE-D2 preserves that physically and historically consistent decision rule explicitly.
    """
    route_name = _string(case, "member_route")
    if "route" not in case or not isinstance(case["route"], Mapping):
        raise ValueError("FIRE-D2 case requires route object")
    route: Mapping[str, Any] = case["route"]
    group, qualification_notes = _effective_steel_group(case)
    _number(case, "fy_norm_n_mm2", positive=True)
    _number(case, "E_norm_n_mm2", positive=True)

    if route_name == "central_tension":
        candidates, gamma_e, trace = _central_tension(case, route)
    elif route_name == "central_compression":
        candidates, gamma_e, trace = _central_compression(case, route)
    elif route_name == "bending":
        candidates, gamma_e, trace = _bending(case, route)
    elif route_name == "combined_nm":
        candidates, gamma_e, trace = _combined_nm(case, route)
    elif route_name == "static_stress_8_7":
        candidates, gamma_e, trace = _static_stress(case, route)
    else:
        raise ValueError("Unsupported FIRE-D2 member_route")

    governing_candidate = max(candidates, key=lambda row: float(row["gamma_T_required"]))
    gamma_t = float(governing_candidate["gamma_T_required"])
    critical = _critical_selection(group, gamma_t, gamma_e)
    critical_temperature = critical["critical_temperature_c"]

    result: dict[str, Any] = {
        "status": critical["status"],
        "member_route": route_name,
        "requested_steel_strength_group": case["steel_strength_group"],
        "effective_steel_strength_group": group,
        "qualification_notes": qualification_notes,
        "gamma_T_candidates": candidates,
        "gamma_T_required": gamma_t,
        "gamma_T_governing_formula_ref": governing_candidate["formula_ref"],
        "gamma_E_required": gamma_e,
        "critical_temperature_c": critical_temperature,
        "critical_temperature_controlling_kind": critical["controlling_kind"],
        "strength_curve_inversion": critical["strength_inversion"],
        "modulus_curve_inversion": critical["modulus_inversion"],
        "route_trace": trace,
        "governing_policy": "MIN_CRITICAL_TEMPERATURE_AFTER_INDEPENDENT_CURVE_INVERSION",
        "draft_literal_min_coefficient_policy_executed": False,
    }
    if "critical_temperature_lower_bound_c" in critical:
        result["critical_temperature_lower_bound_c"] = critical["critical_temperature_lower_bound_c"]

    if critical_temperature is not None and critical_temperature >= 20.0:
        gamma_t_at = _forward_b1(group, "gamma_T", float(critical_temperature))
        gamma_e_at = _forward_b1(group, "gamma_E", float(critical_temperature))
        fy = _number(case, "fy_norm_n_mm2", positive=True)
        e_mod = _number(case, "E_norm_n_mm2", positive=True)
        result.update(
            {
                "gamma_T_table_at_critical_temperature": gamma_t_at,
                "gamma_E_table_at_critical_temperature": gamma_e_at,
                "R_yt_critical_n_mm2": fy * gamma_t_at,
                "E_t_critical_n_mm2": e_mod * gamma_e_at,
            }
        )
    return result


def sp554_appendix_b_critical_temperature_selection(
    steel_strength_group: str,
    gamma_t_required: float,
    gamma_e_required: float | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Independently invert the SP554 Appendix-B strength and elastic-modulus reduction curves and select the earliest governing temperature without extrapolation.

    Standard reference:
        SP554 clauses 8.6 and mandatory Appendix B Table B.1 / Figures B.1-B.8; FIRE-D2 governing-temperature reconciliation.

    Parameters:
        steel_strength_group: Frozen Appendix-B steel group identifier (ordinary, increased, high, or fire_resistant).
        gamma_t_required: Required temperature strength-reduction coefficient gamma_T.
        gamma_e_required: Optional required elastic-modulus reduction coefficient gamma_e for compression/stability routes.

    Returns:
        Dictionary containing independent strength/modulus inversion records, exact governing critical temperature when available, lower-bound temperature when both branches lie above the published range, governing branch kind, and status.

    Assumptions:
        Required reduction coefficients were calculated by their applicable SP554 mechanical formulas and the effective steel group has already been normatively classified.

    Sign convention:
        Reduction coefficients are positive dimensionless magnitudes; force/moment signs are resolved upstream.

    Unit convention:
        Temperatures are degrees Celsius and coefficients are dimensionless.

    Applicability:
        FIRE-D2 member critical-temperature selection after the required gamma_T and optional gamma_e have been resolved.

    Limitations:
        No extrapolation beyond the published Appendix-B curves. gamma greater than 1 is classified as ambient-capacity exceeded; gamma below the published minimum produces a relational lower-bound temperature rather than a fabricated exact value.

    Raises:
        ValueError for unsupported steel groups, non-finite/non-positive coefficients, or a curve value that cannot be bracketed within the frozen Appendix-B polyline.

    Examples:
        ``sp554_appendix_b_critical_temperature_selection("ordinary", 0.946, 0.379)`` returns an exact strength-governed temperature while the modulus branch is reported above the published range.

    Tests:
        FIRE-UI1.7 critical-temperature regression tests cover exact/exact, exact/bounded, ambient-failure, and bounded/bounded combinations.

    Implementation notes:
        This public wrapper exposes the already-qualified FIRE-D2 independent-inversion policy to DAG-driven UI execution; it does not duplicate the Appendix-B curve logic.
    """
    return _critical_selection(steel_strength_group, gamma_t_required, gamma_e_required)
