"""FIRE-UI1.4 simplified section-weakening executor bindings.

The UI1.4 scope deliberately supports one compact authoring model only:
round bolt holes in an I-section web, with a representative active transverse
section hole centred on the neutral axis.  SP16 equation (45) keeps its own
normative meaning: ``s`` is the pitch of holes in one vertical row.

This module does not generalise the model to flange holes, arbitrary cut-outs,
staggered net paths or user-authored multi-hole geometry.

v0.92 adds structured calculation evidence inside the already-declared
``net_section_geometry_2d`` object.  This is not a new engineering route: it
records the exact inputs/results already used by UI1.4 so REPORT-IR can show
``formula -> numerical substitution -> recorded result`` without re-evaluating
net-section geometry in the presentation layer.  The SP16 formula (45) result
remains owned by its separate calculation node; the weakening trace only
records its inputs and normative formula identity.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui13_material_strength import build_fire_ui13_registry
from .profile_catalog import InterimProfileCatalog

WEAKENING_TRACE_SCHEMA = "fire_ui14_weakening_calculation_trace_v092"


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{name} must be a finite number > 0")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise FireUIError(f"{name} must be a finite number > 0")
    return result


def _parse_model(values: Mapping[str, Any]) -> dict[str, Any]:
    raw = values.get("section_weakening_model")
    if not isinstance(raw, Mapping):
        raise FireUIError("section_weakening_model must be an object")
    holes = raw.get("holes_present")
    if not isinstance(holes, bool):
        raise FireUIError("section_weakening_model.holes_present must be boolean")
    if not holes:
        return {"holes_present": False, "model": "none"}

    diameter = raw.get("hole_diameter_mm")
    pitch = raw.get("hole_pitch_mm")
    model = raw["model"] if "model" in raw else "central_web_bolt_hole_formula45_v1"

    # Compatibility with the v0.46 editor payload while the new release is
    # under validation. Only the subset that maps exactly to UI1.4 is accepted.
    if diameter is None or pitch is None:
        features = raw.get("features")
        if isinstance(features, list) and len(features) == 1 and isinstance(features[0], Mapping):
            feature = features[0]
            if feature.get("type") not in (None, "circular_hole"):
                raise FireUIError("FIRE-UI1.4 supports circular bolt holes only")
            if feature.get("zone") not in (None, "web"):
                raise FireUIError("FIRE-UI1.4 supports web holes only")
            diameter = feature.get("diameter_mm")
            pitch = feature.get("pitch_mm")
            model = "central_web_bolt_hole_formula45_v1"

    if model != "central_web_bolt_hole_formula45_v1":
        raise FireUIError("unsupported section weakening model; use central_web_bolt_hole_formula45_v1")
    d = _finite_positive(diameter, "hole_diameter_mm")
    s = _finite_positive(pitch, "hole_pitch_mm")
    if s <= d:
        raise FireUIError("SP16 8.2.1 formula (45) requires hole pitch s > hole diameter d")
    return {"holes_present": True, "model": model, "d": d, "s": s}


def _weakening_flag_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"sp16_has_weakening": bool(_parse_model(values)["holes_present"])}


def _geometry_dimensions(values: Mapping[str, Any]) -> tuple[float, float | None, float | None]:
    """Return web thickness, total depth and flange thickness when traceable."""
    if "t_w" in values:
        tw = _finite_positive(values["t_w"], "t_w")
    else:
        tw = 0.0
    h: float | None = None
    tf: float | None = None
    geom = values.get("section_geometry_2d_normalized")
    if isinstance(geom, Mapping):
        if geom.get("template") == "i_section":
            tw = _finite_positive(geom.get("tw_mm"), "section_geometry_2d_normalized.tw_mm")
            h = _finite_positive(geom.get("h_mm"), "section_geometry_2d_normalized.h_mm")
            tf = _finite_positive(geom.get("tf_mm"), "section_geometry_2d_normalized.tf_mm")
        elif geom.get("source") == "profile_catalog" and geom.get("shape_group") == "I_ROLLED_DSYMM":
            dims = geom.get("dimensions")
            if not isinstance(dims, Mapping):
                raise FireUIError("profile-catalog geometry dimensions are missing")
            tw = _finite_positive(dims.get("tw_mm"), "profile_catalog.tw_mm")
            h = _finite_positive(dims.get("h_mm"), "profile_catalog.h_mm")
            tf = _finite_positive(dims.get("tf_mm"), "profile_catalog.tf_mm")
    if tw <= 0:
        raise FireUIError("web thickness t_w is required for the simplified weakening model")
    return tw, h, tf


def _gross_required(values: Mapping[str, Any], key: str) -> float:
    if key not in values:
        raise FireUIError(f"gross section property {key} is required by the weakening resolver")
    return _finite_positive(values[key], key)


def _identity_trace(*, area: float, ix: float, iy: float, wx: float, wy: float, major_axis_is_x: Any) -> dict[str, Any]:
    return {
        "schema": WEAKENING_TRACE_SCHEMA,
        "route": "identity_no_weakening",
        "engineering_basis": "no section weakening; net properties equal gross properties",
        "major_axis_is_x": major_axis_is_x if isinstance(major_axis_is_x, bool) else None,
        "steps": [
            {"formula_id": "A_NET_IDENTITY", "formula_latex": r"A_n=A", "inputs": {"A": area}, "result": {"quantity_id": "A_net", "value": area, "unit": "mm2"}},
            {"formula_id": "I_XN_IDENTITY", "formula_latex": r"I_{x,n}=I_x", "inputs": {"I_x": ix}, "result": {"quantity_id": "I_xn", "value": ix, "unit": "mm4"}},
            {"formula_id": "I_YN_IDENTITY", "formula_latex": r"I_{y,n}=I_y", "inputs": {"I_y": iy}, "result": {"quantity_id": "I_yn", "value": iy, "unit": "mm4"}},
            {"formula_id": "W_XN_IDENTITY", "formula_latex": r"W_{x,n}=W_x", "inputs": {"W_x": wx}, "result": {"quantity_id": "W_xn_min", "value": wx, "unit": "mm3"}},
            {"formula_id": "W_YN_IDENTITY", "formula_latex": r"W_{y,n}=W_y", "inputs": {"W_y": wy}, "result": {"quantity_id": "W_yn_min", "value": wy, "unit": "mm3"}},
        ],
        "sp16_formula45": {"applicable": False, "result_quantity_id": "sp16_shear_hole_alpha45", "identity_value": 1.0},
        "presentation_recomputes_values": False,
    }


def _hole_trace(
    *,
    area: float,
    ix: float,
    iy: float,
    y_pos: float,
    y_neg: float,
    x_pos: float,
    x_neg: float,
    d: float,
    s: float,
    tw: float,
    removed_area: float,
    removed_ix: float,
    removed_iy: float,
    a_net: float,
    ix_net: float,
    iy_net: float,
    wx_net: float,
    wy_net: float,
    major_axis_is_x: Any,
) -> dict[str, Any]:
    """Typed evidence for values already evaluated by the UI1.4 executor."""
    return {
        "schema": WEAKENING_TRACE_SCHEMA,
        "route": "representative_central_web_hole",
        "engineering_basis": (
            "application geometry model: one representative circular bolt hole is represented in the active transverse section "
            "as a centred removed rectangle d x t_w; this geometry reduction is not labelled as SP16 formula (45)"
        ),
        "major_axis_is_x": major_axis_is_x if isinstance(major_axis_is_x, bool) else None,
        "inputs": {
            "A_gross": area,
            "J_x": ix,
            "J_y": iy,
            "y_pos": y_pos,
            "y_neg": y_neg,
            "x_pos": x_pos,
            "x_neg": x_neg,
            "d": d,
            "s": s,
            "t_w": tw,
        },
        "steps": [
            {
                "formula_id": "REMOVED_AREA_CENTRAL_WEB_HOLE",
                "formula_latex": r"\Delta A=d\,t_w",
                "inputs": {"d": d, "t_w": tw},
                "result": {"quantity_id": "sp16_net_removed_area", "value": removed_area, "unit": "mm2"},
            },
            {
                "formula_id": "A_NET_CENTRAL_WEB_HOLE",
                "formula_latex": r"A_n=A-\Delta A",
                "inputs": {"A": area, "Delta_A": removed_area},
                "result": {"quantity_id": "A_net", "value": a_net, "unit": "mm2"},
            },
            {
                "formula_id": "I_XN_CENTRAL_WEB_HOLE",
                "formula_latex": r"I_{x,n}=I_x-\frac{t_w d^3}{12}",
                "inputs": {"I_x": ix, "t_w": tw, "d": d, "Delta_I_x": removed_ix},
                "result": {"quantity_id": "I_xn", "value": ix_net, "unit": "mm4"},
            },
            {
                "formula_id": "I_YN_CENTRAL_WEB_HOLE",
                "formula_latex": r"I_{y,n}=I_y-\frac{d t_w^3}{12}",
                "inputs": {"I_y": iy, "d": d, "t_w": tw, "Delta_I_y": removed_iy},
                "result": {"quantity_id": "I_yn", "value": iy_net, "unit": "mm4"},
            },
            {
                "formula_id": "W_XN_MIN_CENTRAL_WEB_HOLE",
                "formula_latex": r"W_{x,n,min}=\min\left(\frac{I_{x,n}}{y_+},\frac{I_{x,n}}{y_-}\right)",
                "inputs": {"I_xn": ix_net, "y_pos": y_pos, "y_neg": y_neg},
                "result": {"quantity_id": "W_xn_min", "value": wx_net, "unit": "mm3"},
            },
            {
                "formula_id": "W_YN_MIN_CENTRAL_WEB_HOLE",
                "formula_latex": r"W_{y,n,min}=\min\left(\frac{I_{y,n}}{x_+},\frac{I_{y,n}}{x_-}\right)",
                "inputs": {"I_yn": iy_net, "x_pos": x_pos, "x_neg": x_neg},
                "result": {"quantity_id": "W_yn_min", "value": wy_net, "unit": "mm3"},
            },
        ],
        "sp16_formula45": {
            "applicable": True,
            "formula_id": "SP16_EQ_45_SHEAR_HOLE_FACTOR",
            "normative_scope": "SP16 8.2.1 Eq.(45)",
            "formula_latex": r"\alpha_h=\frac{s}{s-d}",
            "inputs": {"s": s, "d": d},
            "result_quantity_id": "sp16_shear_hole_alpha45",
        },
        "presentation_recomputes_values": False,
    }


def _net_geometry_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    model = _parse_model(values)
    area = _gross_required(values, "A_gross")
    ix = _gross_required(values, "J_x")
    iy = _gross_required(values, "J_y")
    wxp = _gross_required(values, "W_el_x_pos")
    wxn = _gross_required(values, "W_el_x_neg")
    wyp = _gross_required(values, "W_el_y_pos")
    wyn = _gross_required(values, "W_el_y_neg")
    y_pos = ix / wxp
    y_neg = ix / wxn
    x_pos = iy / wyp
    x_neg = iy / wyn

    out: dict[str, Any] = {
        "sp16_weakening_model_valid": True,
        "sp16_net_geometry_solver_ok": True,
    }
    if not model["holes_present"]:
        wx_min = min(wxp, wxn)
        wy_min = min(wyp, wyn)
        out.update({
            "net_section_geometry_2d": {
                "schema": "fire_ui14_net_section_v1",
                "mode": "identity_no_weakening",
                "calculation_trace": _identity_trace(
                    area=area,
                    ix=ix,
                    iy=iy,
                    wx=wx_min,
                    wy=wy_min,
                    major_axis_is_x=values.get("major_axis_is_x"),
                ),
            },
            "A_net": area,
            "I_xn": ix,
            "I_yn": iy,
            "W_xn_min": wx_min,
            "W_yn_min": wy_min,
            "sp16_net_removed_area": 0.0,
            "sp16_shear_weakening_mode": "none",
        })
        if "I_omega_gross" in values:
            out["I_omega_n"] = _gross_required(values, "I_omega_gross")
        if "W_omega_gross" in values:
            out["W_omega_eff"] = _gross_required(values, "W_omega_gross")
        if "W_pl_x" in values:
            out["W_pl_x_eff"] = _gross_required(values, "W_pl_x")
        if "W_pl_y" in values:
            out["W_pl_y_eff"] = _gross_required(values, "W_pl_y")
        if "W_pl_min_gross" in values:
            out["W_pl_min_eff"] = _gross_required(values, "W_pl_min_gross")
        return out

    # The simplified net-property algebra is exact only for the declared
    # representative hole in a doubly symmetric I-section web: the removed
    # rectangle d x t_w is centred at both centroidal axes, so no Steiner shift
    # is introduced and the gross centroid/extreme fibres remain unchanged.
    if values.get("sp16_i_symmetry_class") != "double_symmetric":
        raise FireUIError("FIRE-UI1.4 bolt-hole net model supports doubly symmetric I-sections only")
    tw, h, tf = _geometry_dimensions(values)
    d = model["d"]
    s = model["s"]
    if h is not None and tf is not None:
        clear_web = h - 2.0 * tf
        if clear_web <= 0 or d >= clear_web:
            raise FireUIError("hole diameter d must fit entirely inside the clear web depth")

    removed_area = d * tw
    removed_ix = tw * d**3 / 12.0
    removed_iy = d * tw**3 / 12.0
    a_net = area - removed_area
    ix_net = ix - removed_ix
    iy_net = iy - removed_iy
    if min(a_net, ix_net, iy_net) <= 0:
        raise FireUIError("bolt hole produces non-positive net section properties")
    wx_net = min(ix_net / y_pos, ix_net / y_neg)
    wy_net = min(iy_net / x_pos, iy_net / x_neg)

    out.update({
        "net_section_geometry_2d": {
            "schema": "fire_ui14_net_section_v1",
            "mode": "representative_central_web_hole",
            "hole_diameter_mm": d,
            "web_thickness_mm": tw,
            "hole_center_x_mm": 0.0,
            "hole_center_y_mm": 0.0,
            "removed_cross_section_shape": "rectangle_d_by_tw",
            "limitations": [
                "one representative active transverse-section hole",
                "doubly symmetric I-section only",
                "flange holes/cut-outs/multiple active holes not represented",
            ],
            "calculation_trace": _hole_trace(
                area=area,
                ix=ix,
                iy=iy,
                y_pos=y_pos,
                y_neg=y_neg,
                x_pos=x_pos,
                x_neg=x_neg,
                d=d,
                s=s,
                tw=tw,
                removed_area=removed_area,
                removed_ix=removed_ix,
                removed_iy=removed_iy,
                a_net=a_net,
                ix_net=ix_net,
                iy_net=iy_net,
                wx_net=wx_net,
                wy_net=wy_net,
                major_axis_is_x=values.get("major_axis_is_x"),
            ),
        },
        "A_net": a_net,
        "I_xn": ix_net,
        "I_yn": iy_net,
        "W_xn_min": wx_net,
        "W_yn_min": wy_net,
        "net_centroid_x": 0.0,
        "net_centroid_y": 0.0,
        "sp16_net_removed_area": removed_area,
        "sp16_shear_weakening_mode": "formula45",
        "sp16_wall_hole_pitch_s": s,
        "sp16_wall_hole_diameter_d": d,
    })
    return out


def _shear_gross_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "I_shear_eff": _gross_required(values, "I_shear_gross"),
        "S_shear_eff": _gross_required(values, "S_shear_gross"),
        "t_w_eff": _geometry_dimensions(values)[0],
    }


def _shear_supported_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mode = values.get("sp16_shear_weakening_mode")
    if mode not in {"none", "formula45"}:
        return {"sp16_shear_weakening_ok": False}
    return {"sp16_shear_weakening_ok": True}


def _alpha45_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    s = _finite_positive(values.get("sp16_wall_hole_pitch_s"), "sp16_wall_hole_pitch_s")
    d = _finite_positive(values.get("sp16_wall_hole_diameter_d"), "sp16_wall_hole_diameter_d")
    if s <= d:
        raise FireUIError("SP16 8.2.1 formula (45) requires s > d")
    return {"sp16_shear_hole_alpha45": s / (s - d)}


def _alpha_identity_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    if values.get("sp16_shear_weakening_mode") != "none":
        raise FireUIError("alpha=1 identity is valid only when wall-hole weakening mode is none")
    return {"sp16_shear_hole_alpha45": 1.0}


def build_fire_ui14_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """Extend FIRE-UI1.3 with the simplified, fail-closed weakening branch."""
    reg = build_fire_ui13_registry(catalog, registry)
    reg.register("SP16_D_WEAKENING", _weakening_flag_executor)
    reg.register("SP554_G_NET_SECTION_PROPERTIES", _net_geometry_executor)
    reg.register("SP16_C_SHEAR_GROSS_PROPERTIES_WEAK", _shear_gross_executor)
    reg.register("SP16_A_SHEAR_WEAKENING_SUPPORTED", _shear_supported_executor)
    reg.register("SP16_C_SHEAR_ALPHA45", _alpha45_executor)
    reg.register("SP16_C_SHEAR_ALPHA_IDENTITY_WEAK", _alpha_identity_executor)
    return reg


__all__ = [
    "WEAKENING_TRACE_SCHEMA",
    "_alpha45_executor",
    "_net_geometry_executor",
    "build_fire_ui14_registry",
]
