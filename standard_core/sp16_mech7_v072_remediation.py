"""v0.72 SP16-MECH7 runtime contract remediation.

This module closes integration gaps between already-qualified guided producers
and the MECH7 primary evidence binder.  It does not add normative equations:
Ry/Ru/Rs use the existing current-SP16 Table 2 functions and geometric
slenderness uses the frozen DAG definition lambda=l_eff/i.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .material_resistance import (
    design_shear_resistance_n_mm2,
    design_ultimate_resistance_n_mm2,
    design_yield_resistance_n_mm2,
    material_safety_factor,
)


def _positive(values: Mapping[str, Any], key: str) -> float | None:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0.0 else None


def _material_formula_inputs(values: Mapping[str, Any], out: dict[str, Any]) -> None:
    """Materialize qualified Table-2 values in the local MECH7 execution view."""
    if _positive(out, "Ry_formula") is not None:
        return

    # Compatibility with callers that already materialized the N1 formula
    # bundle under its explicit unit-suffixed API names.
    for dst, src in (
        ("Ry_formula", "Ry_formula_MPa"),
        ("Ru_formula", "Ru_formula_MPa"),
        ("Rs_formula", "Rs_formula_MPa"),
    ):
        value = _positive(out, src)
        if value is not None and dst not in out:
            out[dst] = value

    if _positive(out, "Ry_formula") is not None:
        return

    fy = _positive(out, "fy_norm")
    fu = _positive(out, "fu_norm")
    gamma = _positive(out, "gamma_m")
    if gamma is None:
        category = out.get("material_safety_category")
        if isinstance(category, str) and category.strip():
            gamma = float(material_safety_factor(category))
            out["gamma_m"] = gamma

    # No hidden default: without an explicit Table-3 category/gamma_m the
    # original fail-closed behaviour is preserved.
    if fy is None or gamma is None:
        return
    out["Ry_formula"] = design_yield_resistance_n_mm2(fy, gamma)
    out.setdefault("Rs_formula", design_shear_resistance_n_mm2(fy, gamma))
    if fu is not None:
        out.setdefault("Ru_formula", design_ultimate_resistance_n_mm2(fu, gamma))


def _slenderness_inputs(values: Mapping[str, Any], out: dict[str, Any]) -> None:
    """Materialize lambda_x/lambda_y from already-qualified l_eff and i values."""
    for axis in ("x", "y"):
        target = f"sp16_lambda_{axis}_geom"
        if _positive(out, target) is not None:
            continue
        leff = _positive(out, f"sp16_l_eff_{axis}")
        radius = _positive(out, f"sp16_i_{axis}")
        if radius is None:
            area = _positive(out, "A_gross")
            inertia = _positive(out, f"J_{axis}")
            if area is not None and inertia is not None:
                radius = math.sqrt(inertia / area)
                out[f"sp16_i_{axis}"] = radius
        if leff is not None and radius is not None:
            out[target] = leff / radius


def _geometry_inputs(values: Mapping[str, Any], out: dict[str, Any]) -> None:
    """Normalize the catalog I-section geometry contract used elsewhere by MECH3."""
    geom = out.get("section_geometry_2d_normalized")
    if not isinstance(geom, Mapping):
        return
    raw = str(geom.get("template") or geom.get("shape") or geom.get("shape_group") or "")
    aliases = {"I_ROLLED_DSYMM": "i_section", "doubly_symmetric_i": "i_section"}
    shape = aliases.get(raw, raw)
    if shape != "i_section":
        return
    dims = geom.get("dimensions") if isinstance(geom.get("dimensions"), Mapping) else geom
    patched = dict(geom)
    patched["template"] = "i_section"
    for key in ("h_mm", "b_mm", "tw_mm", "tf_mm"):
        if key in dims and key not in patched:
            patched[key] = dims[key]
    out["section_geometry_2d_normalized"] = patched


def normalize_mech7_inputs(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return a local, auditable compatibility view for the MECH7 binder."""
    out = dict(values)
    _material_formula_inputs(values, out)
    _slenderness_inputs(values, out)
    _geometry_inputs(values, out)
    return out


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Wrap the existing MECH7 binder once, without weakening its fail-closed gate."""
    node_id = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"
    original = registry.executors.get(node_id)
    if original is None:
        raise FireUIError(f"v0.72 remediation requires registered {node_id}")
    if getattr(original, "_sp16_v072_remediated", False):
        return registry

    def remediated(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        return original(normalize_mech7_inputs(values), node)

    setattr(remediated, "_sp16_v072_remediated", True)
    setattr(remediated, "_sp16_v072_original", original)
    registry.executors[node_id] = remediated
    return registry
