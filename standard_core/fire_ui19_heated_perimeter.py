"""FIRE-UI1.9 SP554 Table 1 heated-perimeter matrix and guided bindings.

The module keeps the perimeter geometry in one production implementation and
binds it to the cumulative FIRE-UI registry.  It distinguishes the unprotected
steel-contour perimeter from protected contour/box execution and never infers a
Table-1 row for an unsupported or ambiguous section geometry.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui18_workflow import build_fire_ui18_registry
from .profile_catalog import InterimProfileCatalog


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FireUIError(f"{name} must be a finite number")
    x=float(value)
    if x <= 0.0:
        raise FireUIError(f"{name} must be > 0")
    return x


def _normalized_shape(geometry: Mapping[str, Any], family: str) -> tuple[str, Mapping[str, Any]]:
    if not isinstance(geometry, Mapping):
        raise FireUIError("section_geometry_2d_normalized must be an object")
    dims=geometry.get("dimensions") if isinstance(geometry.get("dimensions"), Mapping) else geometry
    shape=str(geometry.get("shape_group") or geometry.get("template") or family or "").strip()
    aliases={
        "I_ROLLED_DSYMM":"i_section", "i_section":"i_section",
        "CHANNEL":"channel", "channel":"channel",
        "TEE":"tee", "tee":"tee",
        "RHS_SHS":"rhs_shs", "rhs_shs":"rhs_shs",
        "CHS":"chs", "chs":"chs",
    }
    return aliases.get(shape, aliases.get(str(family), shape.lower())), dims


def _dim(dims: Mapping[str, Any], *keys: str) -> float:
    for key in keys:
        if key in dims and dims[key] is not None:
            return _finite_positive(dims[key], key)
    raise FireUIError(f"Table 1 geometry requires one of dimensions: {', '.join(keys)}")


def _table1_perimeter(values: Mapping[str, Any], *, protection_mode: str) -> tuple[float, dict[str, Any]]:
    geometry=values.get("section_geometry_2d_normalized")
    family=str(values.get("section_family") or "")
    shape,dims=_normalized_shape(geometry,family)
    exposure=str(values.get("heated_exposure_configuration") or "")
    if exposure not in {"three_sides","four_sides"}:
        raise FireUIError("SP554 Table 1 automatic perimeter supports only three_sides or four_sides")
    sides=3 if exposure=="three_sides" else 4
    if protection_mode not in {"unprotected","contour","box"}:
        raise FireUIError("protection_mode must be unprotected, contour or box")
    effective="contour" if protection_mode=="unprotected" else protection_mode

    B=D=t=None
    if shape in {"i_section","channel"}:
        B=_dim(dims,"b_mm","B_mm","sec_b")
        D=_dim(dims,"h_mm","D_mm","sec_h")
        t=_dim(dims,"tw_mm","t_w_mm","t_mm","t_w")
        if effective=="contour":
            if sides==4:
                p_mm=4.0*B+2.0*D-2.0*t; formula="4B + 2D - 2t"
            else:
                p_mm=3.0*B+2.0*D-2.0*t; formula="3B + 2D - 2t"
        else:
            if sides==4:
                p_mm=2.0*B+2.0*D; formula="2B + 2D"
            else:
                p_mm=B+2.0*D; formula="B + 2D"
    elif shape in {"tee","rhs_shs"}:
        B=_dim(dims,"b_mm","B_mm","sec_b")
        D=_dim(dims,"h_mm","D_mm","sec_h")
        # These Table-1 rows use the bounding dimensions for both contour and
        # box execution.  The protected mode remains in the trace because it is
        # an explicit project input even when the algebra is identical.
        if sides==4:
            p_mm=2.0*B+2.0*D; formula="2B + 2D"
        else:
            p_mm=B+2.0*D; formula="B + 2D"
    elif shape=="chs":
        D=_dim(dims,"D_mm","d_mm","h_mm","sec_h")
        p_mm=math.pi*D; formula="πD"
    else:
        raise FireUIError(f"SP554 Table 1 automatic perimeter is not mapped for section family/shape {shape!r}")

    if not math.isfinite(p_mm) or p_mm<=0.0:
        raise FireUIError("calculated heated perimeter must be positive")
    trace={
        "schema":"sp554_table1_heated_perimeter_trace_v1",
        "standard":"SP554_2026",
        "section":"12.2",
        "table":"1",
        "section_shape":shape,
        "heated_sides":sides,
        "protection_geometry":protection_mode,
        "effective_table_column":"contour" if effective=="contour" else "box",
        "formula":formula,
        "B_mm":B,
        "D_mm":D,
        "t_mm":t,
        "P_mm":p_mm,
        "P_m":p_mm/1000.0,
    }
    return p_mm/1000.0,trace


def _auto_domain(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return whether the selected section has an explicit automatic SP554 Table-1 perimeter mapping."""
    try:
        _table1_perimeter(values,protection_mode="unprotected")
        ok=True
    except FireUIError:
        ok=False
    return {"sp554_unprotected_perimeter_domain_ok":ok}


def _unprotected_perimeter(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    p,trace=_table1_perimeter(values,protection_mode="unprotected")
    return {"P_heated":p,"sp554_table1_perimeter_trace":trace}


def _protected_auto_domain(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mode=str(values.get("fire_protection_perimeter_mode") or "")
    try:
        _table1_perimeter(values,protection_mode=mode)
        ok=True
    except FireUIError:
        ok=False
    return {"sp554_protected_perimeter_domain_ok":ok}


def _protected_perimeter(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mode=str(values.get("fire_protection_perimeter_mode") or "")
    p,trace=_table1_perimeter(values,protection_mode=mode)
    return {"P_heated_protected":p,"sp554_protected_table1_perimeter_trace":trace}


def build_fire_ui19_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI1.9 registry and bind SP554 Table-1 heated-perimeter calculations for unprotected, contour-protected and box-protected members.

    Standard reference:
        SP554 Section 12.2, formula (12.2) and Table 1 heated-perimeter expressions; protected design follows Sections 5 and 12.4-12.10.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited geometry bindings.
        registry: Optional execution registry to extend.

    Returns:
        ExecutionRegistry containing FIRE-UI1.8 bindings plus FIRE-UI1.9 Table-1 perimeter/domain executors.

    Assumptions:
        Three- or four-sided exposure is selected explicitly. Automatic mappings are limited to section families represented unambiguously by the packaged Table-1 algebra; unsupported geometry falls back to explicit manual heated-perimeter input.

    Sign convention:
        Not applicable; all perimeter dimensions are positive.

    Unit convention:
        Normalized section dimensions are millimetres, generated P is metres, A remains mm², and reduced thickness downstream is mm through SP554 (12.2).

    Applicability:
        FIRE-UI1.9 guided Section-12 thermal authoring.

    Limitations:
        Built-up/arbitrary shapes without an explicit Table-1 mapping are not approximated. Manual P is required. This module does not infer the fire-protection geometry from the product name.

    Raises:
        Executor calls raise FireUIError for malformed/unsupported automatic geometry; registry construction itself delegates inherited errors.

    Examples:
        ``registry = build_fire_ui19_registry(InterimProfileCatalog())``.

    Tests:
        FIRE-UI1.9 heated-perimeter matrix, protected/unprotected reduced-thickness handoff, frontend and fresh-extraction regression suites.

    Implementation notes:
        Unprotected steel uses the steel-contour Table-1 basis. For protected members the user explicitly selects contour or box execution; the protected reduced thickness is a separate quantity and is the only one consumed by protected 12.5/12.10 routes.
    """
    reg=build_fire_ui18_registry(catalog,registry)
    bindings={
        "SP554_A_HEATED_PERIMETER_TABLE1":_auto_domain,
        "SP554_C_HEATED_PERIMETER_TABLE1":_unprotected_perimeter,
        "SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1":_protected_auto_domain,
        "SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1":_protected_perimeter,
    }
    for node_id,fn in bindings.items():
        if reg.get(node_id) is None:
            reg.register(node_id,fn)
    return reg
