"""SP16-MECH5 direct-bimoment warping-stress recovery.

This stage closes the project-approved simplified bimoment policy without
introducing a restrained-torsion solver: the user still decides whether B is
required and, when required, enters signed B directly.  SP16-MECH5 recovers the
associated warping normal stress ``sigma_B=B*omega/I_omega`` on the same
material points already used by SP16-MECH3/4.

The first qualified geometry is the doubly-symmetric I-section, for which the
sectorial-coordinate field is deterministic under the package thin-wall sharp
section model.  Other non-zero-B section families remain fail-closed rather
than receiving an unqualified W_omega approximation.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech3_axis_shear import _EPS, _number, _rectangle_decomposition
from .sp16_mech4_torsion import build_sp16_mech4_registry


def _extract_pointwise_points(combined_state: Mapping[str, Any]) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
    if not isinstance(combined_state, Mapping):
        raise FireUIError("combined pointwise state must be an object")
    pw = combined_state.get("pointwise_recovery")
    if not isinstance(pw, Mapping):
        raise FireUIError("combined pointwise state has no pointwise_recovery")
    points = pw.get("points")
    if not isinstance(points, list) or not points:
        raise FireUIError("pointwise recovery has no material points")
    return [dict(p) for p in points], pw


def _contains(r: Mapping[str, float], x: float, y: float) -> bool:
    return r["xmin"] - _EPS <= x <= r["xmax"] + _EPS and r["ymin"] - _EPS <= y <= r["ymax"] + _EPS


def _i_section_sectorial_model(geometry: Mapping[str, Any]) -> dict[str, Any]:
    """Return one internally consistent thin-wall sectorial model for a DS I-section.

    The sectorial origin is the centroid/shear centre.  The web mid-line has
    omega=0.  On the flange mid-lines ``omega=-x*y_f`` where ``y_f`` is the
    signed flange-midline ordinate.  The corresponding sectorial inertia is
    integrated over the two flange plates; the web contribution is zero in
    this idealized thin-wall model.
    """
    shape, rects, geom_meta = _rectangle_decomposition(geometry)
    if shape != "i_section" or len(rects) != 3:
        raise FireUIError("SP16-MECH5 nonzero-B pointwise warping recovery currently supports only doubly symmetric I-sections")
    top, bottom, web = rects
    b_top = top["xmax"] - top["xmin"]
    b_bottom = bottom["xmax"] - bottom["xmin"]
    tf_top = top["ymax"] - top["ymin"]
    tf_bottom = bottom["ymax"] - bottom["ymin"]
    y_top = 0.5 * (top["ymin"] + top["ymax"])
    y_bottom = 0.5 * (bottom["ymin"] + bottom["ymax"])
    # Integral of omega^2 dA over a rectangular flange with omega=-x*y_f.
    iw_top = tf_top * y_top * y_top * b_top**3 / 12.0
    iw_bottom = tf_bottom * y_bottom * y_bottom * b_bottom**3 / 12.0
    iw = iw_top + iw_bottom
    if not math.isfinite(iw) or iw <= 0.0:
        raise FireUIError("derived I_omega is non-positive")
    omega_max = max(abs(0.5 * b_top * y_top), abs(0.5 * b_bottom * y_bottom))
    if omega_max <= 0.0:
        raise FireUIError("derived sectorial-coordinate range is degenerate")
    return {
        "shape": shape,
        "rectangles": rects,
        "I_omega_mm6": iw,
        "W_omega_mm4": iw / omega_max,
        "omega_max_abs_mm2": omega_max,
        "method": "doubly_symmetric_I_thin_wall_sectorial_coordinate_omega_minus_x_times_y_flange_midline",
        "sectorial_origin": "centroid_equals_shear_center",
        "web_omega": 0.0,
        "geometry_provenance": geom_meta,
        "normative_role": "geometry/mechanics support for SP16 Eq.(43)/Eq.(106) B*omega/I_omega term",
    }


def _i_section_omega_at_point(model: Mapping[str, Any], x: float, y: float) -> tuple[float, str]:
    rects = model["rectangles"]
    memberships = [i for i, r in enumerate(rects) if _contains(r, x, y)]
    if not memberships:
        raise FireUIError("warping recovery lost material membership")
    idx = memberships[0]
    if idx in (0, 1):
        r = rects[idx]
        yf = 0.5 * (r["ymin"] + r["ymax"])
        return -x * yf, "top_flange" if idx == 0 else "bottom_flange"
    return 0.0, "web"


def recover_direct_bimoment_pointwise(
    *,
    geometry: Mapping[str, Any],
    B_nmm2: float,
    combined_nmqt_state: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Summary:
        Add the signed direct-bimoment warping normal stress to the already recovered same-point N/M/Q/T mechanics state.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024, Eq. (43) and Eq. (106): the point normal-stress expression contains the signed term B*omega/I_omega.

    Parameters:
        geometry: Normalized section geometry. B_nmm2: Signed directly entered bimoment. combined_nmqt_state: SP16-MECH4 pointwise state carrying the same material points and N/M/Q/T stress components.

    Returns:
        A pointwise N/M/Q/T/B mechanics state with sectorial coordinate, sigma_B, complete normal stress and mechanics von-Mises diagnostic at every material point.

    Assumptions:
        B is supplied directly by the user/external structural analysis and is not derived from T.  For nonzero B the current qualified sectorial geometry is a doubly-symmetric sharp/thin-wall I-section with centroid equal to shear centre.

    Sign convention:
        Canonical signed B is preserved.  omega=-x*y_f on flange mid-lines in the selected sectorial-coordinate convention; sigma_B=B*omega/I_omega.

    Unit convention:
        B in N*mm2, omega in mm2, I_omega in mm6, stress in N/mm2.

    Applicability:
        B=0 for every MECH4-supported geometry; B!=0 pointwise recovery for doubly-symmetric I-section only in v0.62.

    Limitations:
        No restrained-torsion solver and no automatic B derivation.  Channel, tee, RHS/SHS and arbitrary nonzero-B warping geometry remain fail-closed.  This mechanics state is not itself the final SP16_MECHANICAL_PASS gate.

    Raises:
        FireUIError for unresolved pointwise state or unsupported nonzero-B geometry; TypeError/ValueError for invalid B.

    Examples:
        Use ``recover_direct_bimoment_pointwise`` with a qualified doubly-symmetric I-section, signed B and an SP16-MECH4 state to obtain the complete same-point N/M/Q/T/B mechanics field.

    Tests:
        tests/test_sp16_mech5_bimoment.py.

    Implementation notes:
        The same deterministic material points are preserved from MECH3/4; only the sectorial coordinate and B-induced normal-stress term are added.
    """
    B = _number(B_nmm2, "B_nmm2")
    points, prior = _extract_pointwise_points(combined_nmqt_state)

    if abs(B) <= _EPS:
        out_points: list[dict[str, Any]] = []
        for base in points:
            row = dict(base)
            sigma_base = float(row["sigma_N_Mx_My_n_mm2"])
            
            if "tau_total_resultant_n_mm2" in row:
                tau = float(row["tau_total_resultant_n_mm2"])
            elif "tau_resultant_n_mm2" in row:
                tau = float(row["tau_resultant_n_mm2"])
            else:
                raise FireUIError("pointwise state missing shear resultant")
            vm = math.sqrt(max(0.0, sigma_base * sigma_base + 3.0 * tau * tau))
            row.update({
                "sectorial_coordinate_omega_mm2": 0.0,
                "sectorial_coordinate_status": "not_required_B_equals_zero",
                "sigma_B_n_mm2": 0.0,
                "sigma_N_Mx_My_B_n_mm2": sigma_base,
                "von_mises_N_M_Q_T_B_mechanics_n_mm2": vm,
            })
            out_points.append(row)
        max_sigma = max(out_points, key=lambda p: abs(p["sigma_N_Mx_My_B_n_mm2"]))
        max_vm = max(out_points, key=lambda p: p["von_mises_N_M_Q_T_B_mechanics_n_mm2"])
        return {
            "schema": "sp16_mech5_complete_pointwise_state_v1",
            "bimoment_B_nmm2": B,
            "bimoment_active": False,
            "warping_normal_stress_included": True,
            "normal_stress_complete": True,
            "sectorial_properties_required": False,
            "point_count": len(out_points),
            "points": out_points,
            "governing_points": {"max_abs_complete_normal_stress": max_sigma, "max_complete_mechanics_von_mises": max_vm},
            "runtime_closed": True,
            "normative_status": "mechanics_support_state_for_later_SP16_checks",
        }

    model = _i_section_sectorial_model(geometry)
    iw = float(model["I_omega_mm6"])
    out_points = []
    for base in points:
        row = dict(base)
        x = float(row["x_mm"]); y = float(row["y_mm"])
        omega, region = _i_section_omega_at_point(model, x, y)
        sigma_b = B * omega / iw
        sigma_base = float(row["sigma_N_Mx_My_n_mm2"])
        sigma = sigma_base + sigma_b
        
        if "tau_total_resultant_n_mm2" in row:
            tau = float(row["tau_total_resultant_n_mm2"])
        elif "tau_resultant_n_mm2" in row:
            tau = float(row["tau_resultant_n_mm2"])
        else:
            raise FireUIError("pointwise state missing shear resultant")
        vm = math.sqrt(max(0.0, sigma * sigma + 3.0 * tau * tau))
        row.update({
            "sectorial_coordinate_omega_mm2": omega,
            "sectorial_region": region,
            "sectorial_coordinate_status": "derived_same_point",
            "sigma_B_n_mm2": sigma_b,
            "sigma_N_Mx_My_B_n_mm2": sigma,
            "von_mises_N_M_Q_T_B_mechanics_n_mm2": vm,
        })
        out_points.append(row)
    max_b = max(out_points, key=lambda p: abs(p["sigma_B_n_mm2"]))
    max_sigma = max(out_points, key=lambda p: abs(p["sigma_N_Mx_My_B_n_mm2"]))
    max_vm = max(out_points, key=lambda p: p["von_mises_N_M_Q_T_B_mechanics_n_mm2"])
    return {
        "schema": "sp16_mech5_complete_pointwise_state_v1",
        "bimoment_B_nmm2": B,
        "bimoment_active": True,
        "B_semantics": "independent_direct_signed_input_not_derived_from_T",
        "warping_model": {k: v for k, v in model.items() if k != "rectangles"},
        "I_omega_n_mm6": iw,
        "W_omega_n_mm4": float(model["W_omega_mm4"]),
        "warping_normal_stress_included": True,
        "normal_stress_complete": True,
        "sectorial_properties_required": True,
        "point_count": len(out_points),
        "points": out_points,
        "governing_points": {
            "max_abs_sigma_B": max_b,
            "max_abs_complete_normal_stress": max_sigma,
            "max_complete_mechanics_von_mises": max_vm,
        },
        "runtime_closed": True,
        "normative_status": "mechanics_support_state_for_later_SP16_checks",
        "warning": "Direct B is recovered but not generated from restraint/torsion; final SP16 applicability/PASS aggregation remains separate.",
    }


def _recover_case(values: Mapping[str, Any], *, prefix: str) -> Mapping[str, Any]:
    if prefix == "ambient":
        B = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
        prior = values["ambient_combined_pointwise_stress_state"]
        q_state = "ambient_direct_bimoment_state"
        q_closed = "ambient_bimoment_runtime_closed"
        q_complete = "ambient_complete_pointwise_stress_state"
    else:
        B = _number(values["B_bimoment"], "B_bimoment")
        prior = values["fire_combined_pointwise_stress_state"]
        q_state = "fire_direct_bimoment_state"
        q_closed = "fire_bimoment_mechanics_runtime_closed"
        q_complete = "fire_complete_pointwise_stress_state"
    try:
        state = recover_direct_bimoment_pointwise(
            geometry=values["section_geometry_2d_normalized"],
            B_nmm2=B,
            combined_nmqt_state=prior,
        )
        closed = True
        complete = state
    except (FireUIError, KeyError, TypeError, ValueError) as exc:
        state = {
            "schema": "sp16_mech5_direct_bimoment_state_v1",
            "bimoment_B_nmm2": B,
            "status": "unsupported_or_unresolved_bimoment_warping_geometry",
            "runtime_closed": False,
            "reason": str(exc),
        }
        closed = False
        complete = {
            "schema": "sp16_mech5_complete_pointwise_state_v1",
            "status": "incomplete",
            "bimoment_B_nmm2": B,
            "normal_stress_complete": False,
            "warping_normal_stress_included": False,
            "reason": str(exc),
        }
    return {q_state: state, q_closed: closed, q_complete: complete}


def _ambient_bimoment(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return _recover_case(values, prefix="ambient")


def _fire_bimoment(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return _recover_case(values, prefix="fire")


def build_sp16_mech5_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.62 execution registry by extending SP16-MECH4 with direct-bimoment pointwise warping-stress recovery.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; Eq. (43) and Eq. (106) contain the B*omega/I_omega normal-stress term.

    Parameters:
        catalog: Interim profile catalogue used by the inherited cumulative registry. registry: Optional existing execution registry to extend.

    Returns:
        ExecutionRegistry containing all prior executors plus ambient and fire SP16-MECH5 direct-B recovery producers.

    Assumptions:
        The caller uses the v0.62 DAG/presentation policy and the project-approved policy that B is entered directly rather than derived from T.

    Sign convention:
        Signed B is preserved; the qualified I-section sectorial convention is omega=-x*y_f on flange mid-lines.

    Unit convention:
        B uses N*mm2, omega mm2, I_omega mm6 and stress N/mm2.

    Applicability:
        Cumulative v0.62 guided/runtime execution; nonzero-B pointwise recovery is qualified for doubly symmetric I-sections.

    Limitations:
        No restrained-torsion solver, no automatic B-from-T derivation, no all-section warping geometry and no final SP16_MECHANICAL_PASS aggregator.

    Raises:
        Propagates catalogue or registry construction errors from inherited cumulative builders.

    Examples:
        ``build_sp16_mech5_registry(catalog)`` constructs the registry used by FireUI1Application for the v0.62 DAG.

    Tests:
        tests/test_sp16_mech5_bimoment.py and cumulative FIRE-UI regression tests.

    Implementation notes:
        The registry extends SP16-MECH4 and does not replace frozen earlier engineering executors.
    """
    reg = build_sp16_mech4_registry(catalog, registry)
    reg.register("SP16_C_AMBIENT_BIMOMENT_POINTWISE_RECOVERY", _ambient_bimoment)
    reg.register("SP16_C_FIRE_BIMOMENT_POINTWISE_RECOVERY", _fire_bimoment)
    return reg
