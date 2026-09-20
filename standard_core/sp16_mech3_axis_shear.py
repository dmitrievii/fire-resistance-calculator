"""SP16-MECH3 axis-specific shear and pointwise section-stress recovery.

This stage closes the canonical ``Qx``/``Qy`` component mechanics needed by the
SP16 mechanical layer without collapsing the two transverse actions into one
resultant force.  For clause 8.2.3 I/box sections it materializes the normative
component stresses ``tau_x=Qx/Aw`` and ``tau_y=Qy/(2Af)``.  In parallel it
builds a deterministic mechanics recovery field for section templates that can
be represented as non-overlapping axis-aligned rectangles.

The pointwise field is a mechanics/provenance object, not by itself a final
SP16 PASS gate.  SP16-MECH6 remains responsible for aggregating all applicable
normative checks.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech2_load_cases import build_sp16_mech2_registry


_EPS = 1e-9


def _number(value: Any, name: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0.0:
        raise ValueError(f"{name} must be > 0")
    if nonnegative and result < 0.0:
        raise ValueError(f"{name} must be >= 0")
    return result


def _normalized_shape(geometry: Mapping[str, Any]) -> tuple[str, Mapping[str, Any], str]:
    """Return canonical shape key, dimension mapping and provenance role."""
    if not isinstance(geometry, Mapping):
        raise FireUIError("section_geometry_2d_normalized must be an object")
    if isinstance(geometry.get("dimensions"), Mapping):
        dims = geometry["dimensions"]
        raw = str(geometry.get("shape_group") or "")
        source = "profile_catalog"
    else:
        dims = geometry
        raw = str(geometry.get("template") or geometry.get("shape_group") or "")
        source = str(geometry.get("source") or "parametric")
    aliases = {
        "I_ROLLED_DSYMM": "i_section", "i_section": "i_section",
        "RHS_SHS": "rhs_shs", "rhs_shs": "rhs_shs",
        "CHANNEL": "channel", "channel": "channel",
        "TEE": "tee", "tee": "tee",
        "CHS": "chs", "chs": "chs",
        "ANGLE": "angle", "angle": "angle",
    }
    return aliases.get(raw, raw), dims, source


def _rect(width: float, height: float, cx: float, cy: float) -> dict[str, float]:
    if min(width, height) <= 0.0:
        raise FireUIError("rectangle dimensions must be positive")
    return {
        "xmin": cx - width / 2.0,
        "xmax": cx + width / 2.0,
        "ymin": cy - height / 2.0,
        "ymax": cy + height / 2.0,
    }


def _centroid_shift(rects: Sequence[Mapping[str, float]]) -> list[dict[str, float]]:
    area = 0.0
    sx = 0.0
    sy = 0.0
    for r in rects:
        a = (r["xmax"] - r["xmin"]) * (r["ymax"] - r["ymin"])
        cx = 0.5 * (r["xmin"] + r["xmax"])
        cy = 0.5 * (r["ymin"] + r["ymax"])
        area += a
        sx += a * cx
        sy += a * cy
    if area <= 0.0:
        raise FireUIError("section rectangle decomposition has non-positive area")
    cx0 = sx / area
    cy0 = sy / area
    return [
        {"xmin": r["xmin"] - cx0, "xmax": r["xmax"] - cx0,
         "ymin": r["ymin"] - cy0, "ymax": r["ymax"] - cy0}
        for r in rects
    ]


def _rectangle_decomposition(geometry: Mapping[str, Any]) -> tuple[str, list[dict[str, float]], dict[str, Any]]:
    """Build a non-overlapping sharp-corner section decomposition.

    The decomposition is exact for parametric sharp I/RHS/channel/tee templates.
    For catalog rolled sections it is a nominal-dimension mechanics model and is
    labelled accordingly; normative catalogue inertia/property values remain the
    controlling source for the standard checks.
    """
    shape, d, source = _normalized_shape(geometry)

    def p(key: str) -> float:
        if key not in d:
            raise FireUIError(f"section geometry missing {key}")
        return _number(d[key], key, positive=True)

    if shape == "i_section":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if 2.0 * tf >= h or tw >= b:
            raise FireUIError("invalid I-section dimensions")
        hw = h - 2.0 * tf
        rects = [
            _rect(b, tf, 0.0, +(h - tf) / 2.0),
            _rect(b, tf, 0.0, -(h - tf) / 2.0),
            _rect(tw, hw, 0.0, 0.0),
        ]
    elif shape == "rhs_shs":
        h, b = p("h_mm"), p("b_mm")
        t_raw = d.get("t_mm", d.get("tw_mm"))
        t = _number(t_raw, "t_mm", positive=True)
        if 2.0 * t >= min(h, b):
            raise FireUIError("invalid RHS/SHS dimensions")
        hw = h - 2.0 * t
        rects = [
            _rect(b, t, 0.0, +(h - t) / 2.0),
            _rect(b, t, 0.0, -(h - t) / 2.0),
            _rect(t, hw, +(b - t) / 2.0, 0.0),
            _rect(t, hw, -(b - t) / 2.0, 0.0),
        ]
    elif shape == "channel":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if 2.0 * tf >= h or tw >= b:
            raise FireUIError("invalid channel dimensions")
        # Same non-overlapping sharp model used by the geometry producer.
        rects0 = [
            _rect(tw, h, tw / 2.0, h / 2.0),
            _rect(b - tw, tf, tw + (b - tw) / 2.0, h - tf / 2.0),
            _rect(b - tw, tf, tw + (b - tw) / 2.0, tf / 2.0),
        ]
        rects = _centroid_shift(rects0)
    elif shape == "tee":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if tf >= h or tw >= b:
            raise FireUIError("invalid tee dimensions")
        rects0 = [
            _rect(b, tf, b / 2.0, h - tf / 2.0),
            _rect(tw, h - tf, b / 2.0, (h - tf) / 2.0),
        ]
        rects = _centroid_shift(rects0)
    else:
        raise FireUIError(f"pointwise rectangular shear recovery unsupported for section shape {shape!r}")

    exactness = "exact_sharp_geometry" if source != "profile_catalog" else "nominal_sharp_geometry_catalog_dimensions"
    return shape, rects, {"source": source, "geometry_exactness": exactness}


def _line_intervals(rects: Sequence[Mapping[str, float]], coordinate: float, *, horizontal: bool) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    for r in rects:
        if horizontal:
            if r["ymin"] - _EPS <= coordinate <= r["ymax"] + _EPS:
                intervals.append((r["xmin"], r["xmax"]))
        else:
            if r["xmin"] - _EPS <= coordinate <= r["xmax"] + _EPS:
                intervals.append((r["ymin"], r["ymax"]))
    if not intervals:
        return []
    intervals.sort()
    merged: list[list[float]] = []
    for a, b in intervals:
        if not merged or a > merged[-1][1] + _EPS:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    return [(a, b) for a, b in merged]


def _material_at(rects: Sequence[Mapping[str, float]], x: float, y: float) -> bool:
    return any(r["xmin"] - _EPS <= x <= r["xmax"] + _EPS and r["ymin"] - _EPS <= y <= r["ymax"] + _EPS for r in rects)


def _first_moment_above(rects: Sequence[Mapping[str, float]], y: float) -> float:
    value = 0.0
    for r in rects:
        low = max(y, r["ymin"])
        high = r["ymax"]
        if high > low:
            width = r["xmax"] - r["xmin"]
            value += width * 0.5 * (high * high - low * low)
    return value


def _first_moment_right(rects: Sequence[Mapping[str, float]], x: float) -> float:
    value = 0.0
    for r in rects:
        low = max(x, r["xmin"])
        high = r["xmax"]
        if high > low:
            height = r["ymax"] - r["ymin"]
            value += height * 0.5 * (high * high - low * low)
    return value


def _candidate_coordinates(rects: Sequence[Mapping[str, float]], axis: str) -> list[float]:
    edges = sorted({float(r[f"{axis}min"]) for r in rects} | {float(r[f"{axis}max"]) for r in rects})
    candidates = {0.0}
    span = max(edges) - min(edges)
    eps = max(1e-7 * max(span, 1.0), 1e-6)
    for a, b in zip(edges[:-1], edges[1:]):
        if b - a > _EPS:
            candidates.add(0.5 * (a + b))
            candidates.add(a + min(eps, 0.25 * (b - a)))
            candidates.add(b - min(eps, 0.25 * (b - a)))
    # Include outer edges very slightly inside so zero-shear boundaries are represented.
    candidates.add(edges[0] + eps)
    candidates.add(edges[-1] - eps)
    return sorted(candidates)


def recover_pointwise_axis_shear(
    *,
    geometry: Mapping[str, Any],
    area_mm2: float,
    inertia_x_mm4: float,
    inertia_y_mm4: float,
    N_n: float,
    Mx_nmm: float,
    My_nmm: float,
    Qx_n: float,
    Qy_n: float,
    B_nmm2: float = 0.0,
) -> dict[str, Any]:
    """
    Summary:
        Recover signed Qx/Qy shear components and the concurrent N/Mx/My normal stress on deterministic material points of a supported section.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; component shear semantics follow clause 8.2.3 while the pointwise Jourawski field is a mechanics support calculation rather than an independent normative PASS rule.

    Parameters:
        geometry: Normalized section geometry mapping. area_mm2, inertia_x_mm4, inertia_y_mm4: Gross section properties. N_n, Mx_nmm, My_nmm, Qx_n, Qy_n: Signed canonical actions. B_nmm2: Signed bimoment carried for completeness; warping normal stress is not recovered at this stage.

    Returns:
        A trace mapping with same-point signed tau_x/tau_y, their resultant stress magnitude, N/Mx/My normal stress, mechanics von Mises value, governing points, and geometry provenance.

    Assumptions:
        Supported geometry is represented by the deterministic sharp-corner rectangular decomposition encoded in this module; catalogue rounded geometry is explicitly marked nominal.

    Sign convention:
        x-x and y-y are SP16 principal section axes, s is the member axis, and all supplied canonical actions retain their input sign end-to-end.

    Unit convention:
        Forces N, moments N*mm, bimoment N*mm2, dimensions mm, area mm2, inertias mm4, stresses N/mm2.

    Applicability:
        Mechanics recovery is implemented for supported I, RHS/SHS, channel, and tee templates. It supports later interaction checks but does not itself close the complete SP16 mechanical verification gate.

    Limitations:
        No resultant transverse force is formed; B/warping stress, torsional shear, curved-wall exact recovery, arbitrary geometry, and the final all-check SP16 aggregator are outside SP16-MECH3.

    Raises:
        TypeError or ValueError for invalid numerical inputs; FireUIError for unsupported or inconsistent section geometry.

    Examples:
        Use the SP16-MECH3 guided session or tests/test_sp16_mech3_axis_shear.py to recover Qx/Qy stresses for a sharp I-section.

    Tests:
        tests/test_sp16_mech3_axis_shear.py.

    Implementation notes:
        tau_x and tau_y are calculated independently at the same material point and only then combined as a stress-vector magnitude; sqrt(Qx^2+Qy^2) is never used as a substitute load.
    """
    area = _number(area_mm2, "area_mm2", positive=True)
    ix = _number(inertia_x_mm4, "inertia_x_mm4", positive=True)
    iy = _number(inertia_y_mm4, "inertia_y_mm4", positive=True)
    N = _number(N_n, "N_n")
    Mx = _number(Mx_nmm, "Mx_nmm")
    My = _number(My_nmm, "My_nmm")
    Qx = _number(Qx_n, "Qx_n")
    Qy = _number(Qy_n, "Qy_n")
    B = _number(B_nmm2, "B_nmm2")

    shape, rects, geom_meta = _rectangle_decomposition(geometry)
    xs = _candidate_coordinates(rects, "x")
    ys = _candidate_coordinates(rects, "y")
    points: list[dict[str, Any]] = []
    for y in ys:
        hx = _line_intervals(rects, y, horizontal=True)
        bx = sum(b - a for a, b in hx)
        sx = _first_moment_above(rects, y) if bx > _EPS else 0.0
        tau_x = Qx * sx / (ix * bx) if bx > _EPS else 0.0
        for x in xs:
            if not _material_at(rects, x, y):
                continue
            vy = _line_intervals(rects, x, horizontal=False)
            by = sum(b - a for a, b in vy)
            sy = _first_moment_right(rects, x) if by > _EPS else 0.0
            tau_y = Qy * sy / (iy * by) if by > _EPS else 0.0
            sigma_base = N / area + Mx * y / ix + My * x / iy
            tau_res = math.hypot(tau_x, tau_y)
            vm_base = math.sqrt(max(0.0, sigma_base * sigma_base + 3.0 * tau_res * tau_res))
            points.append({
                "id": f"p{len(points):03d}",
                "x_mm": x, "y_mm": y,
                "Sx_cut_mm3": sx, "Sy_cut_mm3": sy,
                "b_x_cut_mm": bx, "b_y_cut_mm": by,
                "tau_x_n_mm2": tau_x,
                "tau_y_n_mm2": tau_y,
                "tau_resultant_n_mm2": tau_res,
                "sigma_N_Mx_My_n_mm2": sigma_base,
                "von_mises_N_M_Q_mechanics_n_mm2": vm_base,
            })
    if not points:
        raise FireUIError("no material points generated for shear recovery")

    max_tau_x = max(points, key=lambda p: abs(p["tau_x_n_mm2"]))
    max_tau_y = max(points, key=lambda p: abs(p["tau_y_n_mm2"]))
    max_tau_r = max(points, key=lambda p: p["tau_resultant_n_mm2"])
    max_vm = max(points, key=lambda p: p["von_mises_N_M_Q_mechanics_n_mm2"])
    return {
        "schema": "sp16_mech3_pointwise_shear_recovery_v1",
        "shape": shape,
        "axis_convention": {
            "member_axis": "s",
            "section_axes": ["x-x", "y-y"],
            "Qx": "SP16 Qx; shear component recovered with Sx/Jx",
            "Qy": "SP16 Qy; shear component recovered with Sy/Jy",
        },
        "method": "Jourawski_component_recovery_on_same_material_points",
        "geometry_provenance": geom_meta,
        "bimoment_status": "not_included_in_normal_stress" if B != 0.0 else "B_equals_zero",
        "normal_stress_complete": B == 0.0,
        "point_count": len(points),
        "points": points,
        "governing_points": {
            "max_abs_tau_x": max_tau_x,
            "max_abs_tau_y": max_tau_y,
            "max_tau_resultant": max_tau_r,
            "max_von_mises_N_M_Q_mechanics": max_vm,
        },
        "warning": "Mechanics recovery supports later interaction/stress routing; final SP16 applicability and PASS aggregation remain separate.",
    }


def _clause_823_component_check(
    *, geometry: Mapping[str, Any], Qx_n: float, Qy_n: float,
    Rs_n_mm2: float, alpha_web_holes: float,
) -> dict[str, Any]:
    shape, d, _ = _normalized_shape(geometry)
    if shape not in {"i_section", "rhs_shs"}:
        return {
            "applicable": False,
            "reason": "SP16 8.2.3 component formula implemented here only for I and box sections",
        }
    qx = abs(_number(Qx_n, "Qx_n")); qy = abs(_number(Qy_n, "Qy_n"))
    rs = _number(Rs_n_mm2, "Rs_n_mm2", positive=True)
    alpha = _number(alpha_web_holes, "alpha_web_holes", positive=True)
    if alpha < 1.0:
        raise ValueError("alpha_web_holes must be >= 1")

    if shape == "i_section":
        h = _number(d["h_mm"], "h_mm", positive=True)
        b = _number(d["b_mm"], "b_mm", positive=True)
        tw = _number(d["tw_mm"], "tw_mm", positive=True)
        tf = _number(d["tf_mm"], "tf_mm", positive=True)
        aw = tw * (h - 2.0 * tf)
        af = b * tf
    else:
        h = _number(d["h_mm"], "h_mm", positive=True)
        b = _number(d["b_mm"], "b_mm", positive=True)
        t = _number(d.get("t_mm", d.get("tw_mm")), "t_mm", positive=True)
        # Clause convention: both webs form Aw, one flange is Af.
        aw = 2.0 * t * max(h - 2.0 * t, _EPS)
        af = b * t

    tau_x_gross = qx / aw
    tau_x_effective = alpha * tau_x_gross
    tau_y = qy / (2.0 * af)
    ux = tau_x_effective / (0.9 * rs)
    uy = tau_y / (0.5 * rs)
    return {
        "applicable": True,
        "normative_reference": "SP16 8.2.3",
        "A_w_mm2": aw,
        "A_f_one_flange_mm2": af,
        "web_hole_alpha45": alpha,
        "tau_x_gross_n_mm2": tau_x_gross,
        "tau_x_effective_n_mm2": tau_x_effective,
        "tau_y_n_mm2": tau_y,
        "limit_tau_x_n_mm2": 0.9 * rs,
        "limit_tau_y_n_mm2": 0.5 * rs,
        "utilization_tau_x_823": ux,
        "utilization_tau_y_823": uy,
        "pass_tau_x_823": ux <= 1.0 + 1e-12,
        "pass_tau_y_823": uy <= 1.0 + 1e-12,
        "pass_components_823": ux <= 1.0 + 1e-12 and uy <= 1.0 + 1e-12,
    }



def _zero_shear_bundle() -> dict[str, Any]:
    return {
        "schema": "sp16_mech3_axis_shear_state_v1",
        "actions": {"Qx": 0.0, "Qy": 0.0},
        "pointwise_recovery": {
            "schema": "sp16_mech3_pointwise_shear_recovery_v1",
            "status": "zero_shear_actions_no_recovery_required",
        },
        "pointwise_runtime_closed": True,
        "pointwise_exact_for_normative_shear": True,
        "pointwise_runtime_reason": None,
        "clause_8_2_3_components": {"applicable": False, "reason": "Qx=Qy=0; no shear check required"},
        "mechanics_component_checks": {"available": True, "zero_actions": True},
        "qy_runtime_closed": True,
        "local_shear_checks_pass": True,
        "governing_shear_utilization": 0.0,
        "scope_note": "Zero Qx/Qy state; no material-dependent shear recovery is required.",
    }


def _ambient_zero_shear(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    qx = _number(values["ambient_Q_x"], "ambient_Q_x")
    qy = _number(values["ambient_Q_y"], "ambient_Q_y")
    if abs(qx) > _EPS or abs(qy) > _EPS:
        raise FireUIError("zero-shear producer requires ambient Qx=Qy=0")
    bundle = _zero_shear_bundle()
    return {
        "ambient_axis_shear_state": bundle,
        "ambient_qy_runtime_closed": True,
        "ambient_shear_local_pass": True,
        "ambient_shear_governing_utilization": 0.0,
    }


def _fire_zero_shear(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    qx = _number(values["Q_x"], "Q_x")
    qy = _number(values["Q_y"], "Q_y")
    if abs(qx) > _EPS or abs(qy) > _EPS:
        raise FireUIError("zero-shear producer requires fire Qx=Qy=0")
    bundle = _zero_shear_bundle()
    return {
        "fire_axis_shear_state": bundle,
        "fire_qy_mechanics_runtime_closed": True,
        "fire_shear_local_pass": True,
        "fire_shear_governing_utilization": 0.0,
    }

def _ambient_shear_recovery(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    qx = _number(values["ambient_Q_x"], "ambient_Q_x")
    qy = _number(values["ambient_Q_y"], "ambient_Q_y")
    N = _number(values["ambient_N_force"], "ambient_N_force")
    mx = _number(values["ambient_M_x"], "ambient_M_x")
    my = _number(values["ambient_M_y"], "ambient_M_y")
    bim = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
    geom = values.get("section_geometry_2d_normalized")
    area = _number(values["A_gross"], "A_gross", positive=True)
    jx = _number(values["J_x"], "J_x", positive=True)
    jy = _number(values["J_y"], "J_y", positive=True)
    rs = _number(values["Rs_formula"], "Rs_formula", positive=True)
    gamma = _number(values["gamma_c_bending_strength"], "gamma_c_bending_strength", positive=True)
    alpha_raw = values["sp16_shear_hole_alpha45"] if "sp16_shear_hole_alpha45" in values else 1.0
    alpha = _number(alpha_raw, "sp16_shear_hole_alpha45", positive=True)

    recovery: dict[str, Any]
    pointwise_supported = True
    pointwise_reason = None
    try:
        recovery = recover_pointwise_axis_shear(
            geometry=geom, area_mm2=area, inertia_x_mm4=jx, inertia_y_mm4=jy,
            N_n=N, Mx_nmm=mx, My_nmm=my, Qx_n=qx, Qy_n=qy, B_nmm2=bim,
        )
    except (FireUIError, KeyError, TypeError, ValueError) as exc:
        pointwise_supported = False
        pointwise_reason = str(exc)
        recovery = {
            "schema": "sp16_mech3_pointwise_shear_recovery_v1",
            "status": "not_available_for_section_geometry",
            "reason": pointwise_reason,
        }

    component = _clause_823_component_check(
        geometry=geom, Qx_n=qx, Qy_n=qy, Rs_n_mm2=rs, alpha_web_holes=alpha,
    )
    pointwise_exact = bool(
        pointwise_supported
        and ("geometry_provenance" in recovery and recovery["geometry_provenance"].get("geometry_exactness") == "exact_sharp_geometry")
    )
    qy_runtime_closed = bool(component.get("applicable")) or pointwise_exact

    # General mechanics ratios use the pointwise maxima and Eq.42-style Rs*gamma_c
    # normalization. They are kept separate from the explicit 8.2.3 limits.
    mechanics: dict[str, Any] = {"available": pointwise_supported}
    if pointwise_supported:
        gp = recovery["governing_points"]
        tx = abs(gp["max_abs_tau_x"]["tau_x_n_mm2"]) * alpha
        ty = abs(gp["max_abs_tau_y"]["tau_y_n_mm2"])
        mechanics.update({
            "max_abs_tau_x_effective_n_mm2": tx,
            "max_abs_tau_y_n_mm2": ty,
            "utilization_tau_x_Rs_gamma_c": tx / (rs * gamma),
            "utilization_tau_y_Rs_gamma_c": ty / (rs * gamma),
            "pass_tau_x_Rs_gamma_c": tx <= rs * gamma + 1e-12,
            "pass_tau_y_Rs_gamma_c": ty <= rs * gamma + 1e-12,
        })

    utilizations = []
    if component.get("applicable"):
        utilizations += [float(component["utilization_tau_x_823"]), float(component["utilization_tau_y_823"])]
    if mechanics.get("available"):
        utilizations += [float(mechanics["utilization_tau_x_Rs_gamma_c"]), float(mechanics["utilization_tau_y_Rs_gamma_c"])]
    governing = max(utilizations) if utilizations else 0.0
    local_pass = all(u <= 1.0 + 1e-12 for u in utilizations) if utilizations else (qx == 0.0 and qy == 0.0)

    bundle = {
        "schema": "sp16_mech3_axis_shear_state_v1",
        "actions": {"Qx": qx, "Qy": qy},
        "pointwise_recovery": recovery,
        "pointwise_runtime_closed": pointwise_supported,
        "pointwise_exact_for_normative_shear": pointwise_exact,
        "pointwise_runtime_reason": pointwise_reason,
        "clause_8_2_3_components": component,
        "mechanics_component_checks": mechanics,
        "qy_runtime_closed": qy_runtime_closed,
        "local_shear_checks_pass": local_pass,
        "governing_shear_utilization": governing,
        "scope_note": "Qx/Qy component mechanics only; full SP16 mechanical PASS is not claimed at SP16-MECH3.",
    }
    return {
        "ambient_axis_shear_state": bundle,
        "ambient_qy_runtime_closed": qy_runtime_closed,
        "ambient_shear_local_pass": local_pass,
        "ambient_shear_governing_utilization": governing,
    }



def _fire_shear_recovery(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mapped = dict(values)
    mapped.update({
        "ambient_Q_x": values["Q_x"],
        "ambient_Q_y": values["Q_y"],
        "ambient_N_force": values["N_force"],
        "ambient_M_x": values["M_x"],
        "ambient_M_y": values["M_y"],
        "ambient_B_bimoment": values["B_bimoment"],
    })
    out = _ambient_shear_recovery(mapped, node)
    return {
        "fire_axis_shear_state": out["ambient_axis_shear_state"],
        "fire_qy_mechanics_runtime_closed": out["ambient_qy_runtime_closed"],
        "fire_shear_local_pass": out["ambient_shear_local_pass"],
        "fire_shear_governing_utilization": out["ambient_shear_governing_utilization"],
    }

def build_sp16_mech3_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.60 execution registry by extending SP16-MECH2 with ambient and fire axis-specific shear recovery producers.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; clause 8.2.3 for the explicit I/box Qx/Qy component checks.

    Parameters:
        catalog: Interim profile catalogue used by the inherited cumulative registry. registry: Optional existing execution registry to extend.

    Returns:
        ExecutionRegistry containing all prior SP16/FIRE executors plus SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY and SP16_C_FIRE_AXIS_SHEAR_RECOVERY.

    Assumptions:
        The caller uses the v0.60 DAG and presentation policy so node identifiers and executor contracts remain synchronized.

    Sign convention:
        Canonical actions use SP16 principal section axes x-x/y-y, member axis s, and signed N/Mx/My/Qx/Qy/T/B quantities.

    Unit convention:
        Registry contracts use the package canonical base units: N, N*mm, N*mm2, mm, mm2, mm4, and N/mm2 as applicable.

    Applicability:
        Cumulative v0.60 guided/runtime execution only. Qy mechanics is closed for supported routes; T remains deferred and the SP554 Qy handoff remains fail-closed.

    Limitations:
        This builder does not implement free torsion, restrained torsion, automatic bimoment recovery, the full SP16 mechanical PASS gate, or the later SP554 complex-state bridge.

    Raises:
        Propagates catalogue or registry construction errors from the inherited cumulative builder.

    Examples:
        build_sp16_mech3_registry(catalog) constructs the registry consumed by FireUI1Application for the v0.60 DAG.

    Tests:
        tests/test_sp16_mech3_axis_shear.py and affected FIRE-UI regression tests.

    Implementation notes:
        The function deliberately extends rather than replaces SP16-MECH2 so previously qualified executors retain their implementation and provenance.
    """
    reg = build_sp16_mech2_registry(catalog, registry)
    reg.register("SP16_C_AMBIENT_AXIS_SHEAR_ZERO", _ambient_zero_shear)
    reg.register("SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY", _ambient_shear_recovery)
    reg.register("SP16_C_FIRE_AXIS_SHEAR_ZERO", _fire_zero_shear)
    reg.register("SP16_C_FIRE_AXIS_SHEAR_RECOVERY", _fire_shear_recovery)
    return reg
