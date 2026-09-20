"""SP16-MECH4 free-torsion mechanics over the canonical SP16 action state.

This stage resolves the previously deferred canonical torsional action ``T`` as
an explicit Saint-Venant/free-torsion mechanical stress field for the section
families supported by the cumulative guided geometry layer.  It never aliases
``T`` to ``Mx`` or to the bimoment ``B``.  ``B`` remains a separate signed
conditional direct input, per the project decision for the current scope.

The stage is intentionally a mechanics/provenance layer.  The final aggregate
SP16 PASS gate remains the responsibility of SP16-MECH6, and the SP16→SP554
complex-state handoff remains fail-closed for non-zero T/Qy until FIRE-BRIDGE2.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .section_model import SectionPropertyModel
from .sp16_mech3_axis_shear import (
    _EPS,
    _number,
    _normalized_shape,
    _rectangle_decomposition,
    recover_pointwise_axis_shear,
    build_sp16_mech3_registry,
)


def _center(r: Mapping[str, float]) -> tuple[float, float]:
    return (0.5 * (r["xmin"] + r["xmax"]), 0.5 * (r["ymin"] + r["ymax"]))


def _contains(r: Mapping[str, float], x: float, y: float) -> bool:
    return r["xmin"] - _EPS <= x <= r["xmax"] + _EPS and r["ymin"] - _EPS <= y <= r["ymax"] + _EPS


def _torsion_properties(geometry: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve the free-torsion property model with explicit provenance."""
    shape, d, source = _normalized_shape(geometry)

    def p(key: str) -> float:
        if key not in d:
            raise FireUIError(f"section geometry missing {key}")
        return _number(d[key], key, positive=True)

    if shape == "i_section":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if 2.0 * tf >= h or tw >= b:
            raise FireUIError("invalid I-section dimensions")
        annex = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
            "i_doubly_symmetric", [(h - 2.0 * tf, tw), (b, tf), (b, tf)]
        )
        return {
            "shape": shape,
            "I_t_mm4": float(annex["I_t_sp16_annex_d_mm4"]),
            "property_method": "SP16_ANNEX_D_I_t",
            "normative_reference": annex["normative_reference"],
            "source_geometry_kind": source,
            "detail": annex,
            "stress_model": "open_thin_wall_saint_venant_plate_field",
        }
    if shape == "tee":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if tf >= h or tw >= b:
            raise FireUIError("invalid tee dimensions")
        annex = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
            "tee", [(h - tf, tw), (b, tf)]
        )
        return {
            "shape": shape,
            "I_t_mm4": float(annex["I_t_sp16_annex_d_mm4"]),
            "property_method": "SP16_ANNEX_D_I_t",
            "normative_reference": annex["normative_reference"],
            "source_geometry_kind": source,
            "detail": annex,
            "stress_model": "open_thin_wall_saint_venant_plate_field",
        }
    if shape == "channel":
        h, b, tw, tf = p("h_mm"), p("b_mm"), p("tw_mm"), p("tf_mm")
        if 2.0 * tf >= h or tw >= b:
            raise FireUIError("invalid channel dimensions")
        annex = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
            "channel", [(h - 2.0 * tf, tw), (b, tf), (b, tf)]
        )
        return {
            "shape": shape,
            "I_t_mm4": float(annex["I_t_sp16_annex_d_mm4"]),
            "property_method": "SP16_ANNEX_D_I_t",
            "normative_reference": annex["normative_reference"],
            "source_geometry_kind": source,
            "detail": annex,
            "stress_model": "open_thin_wall_saint_venant_plate_field",
        }
    if shape == "rhs_shs":
        h, b = p("h_mm"), p("b_mm")
        tw = _number(d.get("tw_mm", d.get("t_mm")), "tw_mm", positive=True)
        tf = _number(d.get("tf_mm", d.get("t_mm")), "tf_mm", positive=True)
        if 2.0 * tw >= b or 2.0 * tf >= h:
            raise FireUIError("invalid RHS/SHS dimensions")
        bm = b - tw
        hm = h - tf
        am = bm * hm
        denom = 2.0 * bm / tf + 2.0 * hm / tw
        if min(am, denom) <= 0.0:
            raise FireUIError("invalid RHS/SHS median-line torsion geometry")
        it = 4.0 * am * am / denom
        return {
            "shape": shape,
            "I_t_mm4": it,
            "property_method": "BREDT_SINGLE_CELL_THIN_WALL",
            "normative_reference": "mechanics support calculation; SP16 uses I_t as the free-torsion section property",
            "source_geometry_kind": source,
            "detail": {
                "median_area_mm2": am,
                "median_width_mm": bm,
                "median_height_mm": hm,
                "sum_s_over_t": denom,
                "top_bottom_thickness_mm": tf,
                "side_thickness_mm": tw,
            },
            "stress_model": "closed_single_cell_bredt_shear_flow",
        }
    raise FireUIError(f"free-torsion recovery unsupported for section shape {shape!r}")


def _open_torsion_vector(shape: str, rects: list[dict[str, float]], idx: int, x: float, y: float, T: float, It: float) -> tuple[float, float]:
    """Thin-wall Saint-Venant plate field at one sampled point.

    For a horizontal wall, local through-thickness coordinate is y-yc and the
    dominant traction is x-directed; for a vertical wall it is x-xc and the
    dominant traction is y-directed.  The sign convention is positive T by the
    right-hand rule about +s.
    """
    cx, cy = _center(rects[idx])
    if shape == "i_section":
        orientation = ["h", "h", "v"][idx]
    elif shape == "tee":
        orientation = ["h", "v"][idx]
    elif shape == "channel":
        orientation = ["v", "h", "h"][idx]
    else:
        raise FireUIError("open torsion vector requested for non-open supported shape")
    if orientation == "h":
        return (-2.0 * T * (y - cy) / It, 0.0)
    return (0.0, 2.0 * T * (x - cx) / It)


def _rhs_torsion_vector(rects: list[dict[str, float]], idx: int, T: float, props: Mapping[str, Any]) -> tuple[float, float]:
    detail = props["detail"]
    am = float(detail["median_area_mm2"])
    tf = float(detail["top_bottom_thickness_mm"])
    tw = float(detail["side_thickness_mm"])
    q = T / (2.0 * am)
    # Rectangle order inherited from MECH3: top, bottom, right, left.
    if idx == 0:
        return (-q / tf, 0.0)
    if idx == 1:
        return (q / tf, 0.0)
    if idx == 2:
        return (0.0, q / tw)
    if idx == 3:
        return (0.0, -q / tw)
    raise FireUIError("unexpected RHS wall index")


def recover_free_torsion_and_combined_stress(
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
    T_nmm: float,
    B_nmm2: float = 0.0,
    axis_shear_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Recover free-torsion shear from signed T and merge it point-by-point with the existing canonical N/Mx/My/Qx/Qy mechanics state.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; Annex A distinguishes T/free-torsion properties from B/I_omega, and Annex D defines I_t=(k/3)sum(b_i*t_i^3) for supported open sections.

    Parameters:
        geometry: Normalized section geometry. area_mm2, inertia_x_mm4, inertia_y_mm4: gross properties. N_n, Mx_nmm, My_nmm, Qx_n, Qy_n, T_nmm: signed canonical actions. B_nmm2: independently supplied signed bimoment. axis_shear_state: optional MECH3 state reused when it already contains pointwise Qx/Qy recovery.

    Returns:
        A free-torsion state with I_t provenance and a same-point N/M/Q/T stress field containing torsional and total shear-vector components.

    Assumptions:
        T is the Saint-Venant/free-torsion component. If B is also non-zero, T and B are assumed to be an externally consistent decomposed torsion state; v0.61 does not derive either from a total restrained-torsion moment.

    Sign convention:
        Positive T follows the right-hand rule about member axis +s. Positive closed-cell circulation is counter-clockwise in the x-y section view. Canonical N/M/Q/B signs are preserved.

    Unit convention:
        N, N*mm, N*mm2, mm, mm2, mm4 and N/mm2.

    Applicability:
        Supported templates: doubly symmetric I, channel, tee and RHS/SHS. Open-section I_t uses the current SP16 Annex-D expression; RHS uses a labelled single-cell Bredt thin-wall mechanics model.

    Limitations:
        Open-section local torsion stresses are a thin-wall Saint-Venant mechanics recovery using the Annex-D I_t; SP16 does not print this pointwise field as a standalone resistance formula. B/warping normal stress is not recovered. The final SP16_MECHANICAL_PASS gate remains open until SP16-MECH6.

    Raises:
        FireUIError for unsupported geometry; TypeError/ValueError for invalid numerical inputs.

    Examples:
        Use ``recover_free_torsion_and_combined_stress`` with a supported I-section and signed T to obtain the same-point N/M/Q/T mechanics field.

    Tests:
        tests/test_sp16_mech4_torsion.py.

    Implementation notes:
        Qx/Qy shear is reused from MECH3 where available; the torsional shear vector is then added component-wise at exactly the same deterministic material points.
    """
    area = _number(area_mm2, "area_mm2", positive=True)
    ix = _number(inertia_x_mm4, "inertia_x_mm4", positive=True)
    iy = _number(inertia_y_mm4, "inertia_y_mm4", positive=True)
    N = _number(N_n, "N_n")
    Mx = _number(Mx_nmm, "Mx_nmm")
    My = _number(My_nmm, "My_nmm")
    Qx = _number(Qx_n, "Qx_n")
    Qy = _number(Qy_n, "Qy_n")
    T = _number(T_nmm, "T_nmm")
    B = _number(B_nmm2, "B_nmm2")
    if abs(T) <= _EPS:
        raise FireUIError("nonzero free-torsion recovery requires T != 0")

    props = _torsion_properties(geometry)
    It = float(props["I_t_mm4"])
    shape, rects, geom_meta = _rectangle_decomposition(geometry)

    recovery = None
    if isinstance(axis_shear_state, Mapping):
        maybe = axis_shear_state.get("pointwise_recovery")
        if isinstance(maybe, Mapping) and isinstance(maybe.get("points"), list) and maybe["points"]:
            recovery = maybe
    if recovery is None:
        recovery = recover_pointwise_axis_shear(
            geometry=geometry,
            area_mm2=area,
            inertia_x_mm4=ix,
            inertia_y_mm4=iy,
            N_n=N,
            Mx_nmm=Mx,
            My_nmm=My,
            Qx_n=Qx,
            Qy_n=Qy,
            B_nmm2=B,
        )

    out_points: list[dict[str, Any]] = []
    for base in recovery["points"]:
        x = float(base["x_mm"]); y = float(base["y_mm"])
        memberships = [i for i, r in enumerate(rects) if _contains(r, x, y)]
        if not memberships:
            raise FireUIError("pointwise torsion recovery lost material membership")
        # Rectangles are non-overlapping except shared boundaries; deterministic first
        # membership is sufficient because edge points are sampling artefacts only.
        idx = memberships[0]
        if shape == "rhs_shs":
            tx_t, ty_t = _rhs_torsion_vector(rects, idx, T, props)
        else:
            tx_t, ty_t = _open_torsion_vector(shape, rects, idx, x, y, T, It)
        tx_q = float(base["tau_x_n_mm2"])
        ty_q = float(base["tau_y_n_mm2"])
        tx = tx_q + tx_t
        ty = ty_q + ty_t
        tr = math.hypot(tx, ty)
        sigma = float(base["sigma_N_Mx_My_n_mm2"])
        vm = math.sqrt(max(0.0, sigma * sigma + 3.0 * tr * tr))
        row = dict(base)
        row.update({
            "tau_T_x_n_mm2": tx_t,
            "tau_T_y_n_mm2": ty_t,
            "tau_T_resultant_n_mm2": math.hypot(tx_t, ty_t),
            "tau_total_x_n_mm2": tx,
            "tau_total_y_n_mm2": ty,
            "tau_total_resultant_n_mm2": tr,
            "von_mises_N_M_Q_T_mechanics_n_mm2": vm,
        })
        out_points.append(row)

    max_t = max(out_points, key=lambda p: p["tau_T_resultant_n_mm2"])
    max_total = max(out_points, key=lambda p: p["tau_total_resultant_n_mm2"])
    max_vm = max(out_points, key=lambda p: p["von_mises_N_M_Q_T_mechanics_n_mm2"])
    return {
        "schema": "sp16_mech4_free_torsion_state_v1",
        "action_T_nmm": T,
        "bimoment_B_nmm2": B,
        "T_semantics": "Saint_Venant_free_torsion_component_about_member_axis_s",
        "B_semantics": "independent_direct_bimoment_input_not_derived_from_T",
        "axis_convention": {"member_axis": "s", "section_axes": ["x-x", "y-y"]},
        "torsion_properties": props,
        "geometry_provenance": geom_meta,
        "pointwise_method": "same_points_as_MECH3_plus_free_torsion_vector",
        "normal_stress_complete": B == 0.0,
        "warping_normal_stress_included": False,
        "point_count": len(out_points),
        "points": out_points,
        "governing_points": {
            "max_free_torsion_shear": max_t,
            "max_total_shear_Q_plus_T": max_total,
            "max_von_mises_N_M_Q_T_mechanics": max_vm,
        },
        "runtime_closed": True,
        "normative_status": "mechanics_support_state_for_later_SP16_checks",
        "warning": "This is not by itself the final SP16 PASS criterion; B/warping stress and aggregate applicability remain separate.",
    }


def _zero_torsion_bundle(*, B: float) -> dict[str, Any]:
    return {
        "schema": "sp16_mech4_free_torsion_state_v1",
        "action_T_nmm": 0.0,
        "bimoment_B_nmm2": B,
        "T_semantics": "Saint_Venant_free_torsion_component_about_member_axis_s",
        "B_semantics": "independent_direct_bimoment_input_not_derived_from_T",
        "status": "zero_T_no_free_torsion_recovery_required",
        "runtime_closed": True,
        "normal_stress_complete": B == 0.0,
        "warping_normal_stress_included": False,
        "normative_status": "mechanics_support_state_for_later_SP16_checks",
    }


def _combined_state_from_zero_t(axis_state: Mapping[str, Any], B: float) -> dict[str, Any]:
    pointwise = axis_state.get("pointwise_recovery") if isinstance(axis_state, Mapping) else None
    return {
        "schema": "sp16_mech4_combined_pointwise_state_v1",
        "free_torsion_active": False,
        "axis_shear_state": axis_state,
        "pointwise_recovery": pointwise,
        "normal_stress_complete": B == 0.0,
        "warping_normal_stress_included": False,
    }


def _ambient_zero_torsion(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    T = _number(values["ambient_T_torsion"], "ambient_T_torsion")
    B = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
    if abs(T) > _EPS:
        raise FireUIError("zero-torsion producer requires ambient T=0")
    axis = values["ambient_axis_shear_state"]
    return {
        "ambient_free_torsion_state": _zero_torsion_bundle(B=B),
        "ambient_torsion_runtime_closed": True,
        "ambient_combined_pointwise_stress_state": _combined_state_from_zero_t(axis, B),
    }


def _ambient_torsion_recovery(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    T = _number(values["ambient_T_torsion"], "ambient_T_torsion")
    B = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
    try:
        state = recover_free_torsion_and_combined_stress(
            geometry=values["section_geometry_2d_normalized"],
            area_mm2=values["A_gross"],
            inertia_x_mm4=values["J_x"],
            inertia_y_mm4=values["J_y"],
            N_n=values["ambient_N_force"],
            Mx_nmm=values["ambient_M_x"],
            My_nmm=values["ambient_M_y"],
            Qx_n=values["ambient_Q_x"],
            Qy_n=values["ambient_Q_y"],
            T_nmm=T,
            B_nmm2=B,
            axis_shear_state=values.get("ambient_axis_shear_state"),
        )
        closed = True
        combined = {
            "schema": "sp16_mech4_combined_pointwise_state_v1",
            "free_torsion_active": True,
            "pointwise_recovery": state,
            "normal_stress_complete": state["normal_stress_complete"],
            "warping_normal_stress_included": False,
        }
    except (FireUIError, KeyError, TypeError, ValueError) as exc:
        closed = False
        state = {
            "schema": "sp16_mech4_free_torsion_state_v1",
            "action_T_nmm": T,
            "bimoment_B_nmm2": B,
            "status": "unsupported_or_unresolved_free_torsion_geometry",
            "runtime_closed": False,
            "reason": str(exc),
        }
        combined = {
            "schema": "sp16_mech4_combined_pointwise_state_v1",
            "free_torsion_active": True,
            "status": "incomplete",
            "reason": str(exc),
        }
    return {
        "ambient_free_torsion_state": state,
        "ambient_torsion_runtime_closed": closed,
        "ambient_combined_pointwise_stress_state": combined,
    }


def _fire_zero_torsion(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    T = _number(values["T_torsion"], "T_torsion")
    B = _number(values["B_bimoment"], "B_bimoment")
    if abs(T) > _EPS:
        raise FireUIError("zero-torsion producer requires fire T=0")
    axis = values["fire_axis_shear_state"]
    return {
        "fire_free_torsion_state": _zero_torsion_bundle(B=B),
        "fire_torsion_mechanics_runtime_closed": True,
        "fire_combined_pointwise_stress_state": _combined_state_from_zero_t(axis, B),
    }


def _fire_torsion_recovery(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mapped = dict(values)
    mapped.update({
        "ambient_T_torsion": values["T_torsion"],
        "ambient_B_bimoment": values["B_bimoment"],
        "ambient_N_force": values["N_force"],
        "ambient_M_x": values["M_x"],
        "ambient_M_y": values["M_y"],
        "ambient_Q_x": values["Q_x"],
        "ambient_Q_y": values["Q_y"],
        "ambient_axis_shear_state": values["fire_axis_shear_state"],
    })
    out = _ambient_torsion_recovery(mapped, node)
    return {
        "fire_free_torsion_state": out["ambient_free_torsion_state"],
        "fire_torsion_mechanics_runtime_closed": out["ambient_torsion_runtime_closed"],
        "fire_combined_pointwise_stress_state": out["ambient_combined_pointwise_stress_state"],
    }


def build_sp16_mech4_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.61 execution registry by extending SP16-MECH3 with ambient and fire free-torsion producers.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; Annex A distinguishes It/Iω/B and Annex D provides It for supported open-section families.

    Parameters:
        catalog: Interim profile catalogue used by the inherited cumulative registry. registry: Optional existing execution registry to extend.

    Returns:
        ExecutionRegistry containing all prior executors plus the SP16-MECH4 zero/free-torsion ambient and fire producers.

    Assumptions:
        The caller uses the v0.61 DAG and presentation policy so node identifiers and executor contracts remain synchronized.

    Sign convention:
        Positive T follows the right-hand rule about member axis +s; B remains an independently supplied signed quantity.

    Unit convention:
        Registry contracts use canonical N, N*mm, N*mm2, mm, mm2, mm4, and N/mm2 units as applicable.

    Applicability:
        Cumulative v0.61 guided/runtime execution for the supported free-torsion templates; legacy SP554 Qy/T handoff remains fail-closed.

    Limitations:
        No restrained-torsion solver, no automatic B derivation, no warping-normal-stress recovery, and no final SP16_MECHANICAL_PASS aggregator are introduced here.

    Raises:
        Propagates catalogue or registry construction errors from the inherited cumulative builder.

    Examples:
        ``build_sp16_mech4_registry(catalog)`` constructs the registry consumed by FireUI1Application for the v0.61 DAG.

    Tests:
        tests/test_sp16_mech4_torsion.py and cumulative FIRE-UI regression tests.

    Implementation notes:
        The registry extends SP16-MECH3 rather than replacing any previously qualified executor, preserving cumulative runtime provenance.
    """
    reg = build_sp16_mech3_registry(catalog, registry)
    reg.register("SP16_C_AMBIENT_TORSION_ZERO", _ambient_zero_torsion)
    reg.register("SP16_C_AMBIENT_FREE_TORSION_RECOVERY", _ambient_torsion_recovery)
    reg.register("SP16_C_FIRE_TORSION_ZERO", _fire_zero_torsion)
    reg.register("SP16_C_FIRE_FREE_TORSION_RECOVERY", _fire_torsion_recovery)
    return reg
