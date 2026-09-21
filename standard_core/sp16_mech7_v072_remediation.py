"""v0.72 SP16-MECH7 runtime contract remediation.

This module closes integration gaps between already-qualified guided producers
and the MECH7 primary evidence binder. It does not add normative equations:
Ry/Ru/Rs reuse the qualified current-SP16 N1 functions; geometric and relative
slenderness are reconstructed only through the frozen definitions already
present in the DAG; catalog geometry is only normalized between two existing
internal contracts.

If the qualified prerequisites are absent, the original fail-closed behaviour is
preserved. No material category, effective length, resistance or section class
is guessed.
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


def _trace(out: dict[str, Any], quantity_id: str, source: str, inputs: list[str], scope: str) -> None:
    rows = out.setdefault("_sp16_v072_hydration_trace", [])
    rows.append({
        "quantity_id": quantity_id,
        "source": source,
        "inputs": list(inputs),
        "normative_scope": scope,
    })


def _material_formula_inputs(values: Mapping[str, Any], out: dict[str, Any]) -> None:
    """Materialize qualified Table-2 values in the local MECH7 execution view."""
    # Compatibility with callers that already materialized the N1 formula
    # bundle under its explicit unit-suffixed API names.
    for dst, src in (
        ("Ry_formula", "Ry_formula_MPa"),
        ("Ru_formula", "Ru_formula_MPa"),
        ("Rs_formula", "Rs_formula_MPa"),
    ):
        value = _positive(out, src)
        if value is not None and _positive(out, dst) is None:
            out[dst] = value
            _trace(out, dst, "qualified_N1_formula_bundle_alias", [src], "SP16 Table 2")

    fy = _positive(out, "fy_norm")
    fu = _positive(out, "fu_norm")
    gamma = _positive(out, "gamma_m")
    if gamma is None:
        category = out.get("material_safety_category")
        if isinstance(category, str) and category.strip():
            # This is not a default: category is an explicit user/ledger input
            # whose mapping is the already-qualified Table-3 N1 producer.
            gamma = float(material_safety_factor(category))
            out["gamma_m"] = gamma
            _trace(out, "gamma_m", "qualified_N1_material_safety_factor", ["material_safety_category"], "SP16 Table 3")

    # No hidden default: without an explicit Table-3 category/gamma_m the
    # original fail-closed behaviour is preserved.
    if fy is None or gamma is None:
        return

    if _positive(out, "Ry_formula") is None:
        out["Ry_formula"] = design_yield_resistance_n_mm2(fy, gamma)
        _trace(out, "Ry_formula", "qualified_N1_design_yield_resistance_n_mm2", ["fy_norm", "gamma_m"], "SP16 Table 2 + Table 3")
    if _positive(out, "Rs_formula") is None:
        out["Rs_formula"] = design_shear_resistance_n_mm2(fy, gamma)
        _trace(out, "Rs_formula", "qualified_N1_design_shear_resistance_n_mm2", ["fy_norm", "gamma_m"], "SP16 Table 2 + Table 3")
    if fu is not None and _positive(out, "Ru_formula") is None:
        out["Ru_formula"] = design_ultimate_resistance_n_mm2(fu, gamma)
        _trace(out, "Ru_formula", "qualified_N1_design_ultimate_resistance_n_mm2", ["fu_norm", "gamma_m"], "SP16 Table 2 + Table 3")


def _slenderness_inputs(values: Mapping[str, Any], out: dict[str, Any]) -> None:
    """Materialize exact lambda/lambda_bar aliases from qualified primitives."""
    e = _positive(out, "E_norm")
    ryn = _positive(out, "fy_norm")

    for axis in ("x", "y"):
        geom_key = f"sp16_lambda_{axis}_geom"
        rel_key = f"lambda_bar_{axis}"
        leff_key = f"sp16_l_eff_{axis}"
        radius_key = f"sp16_i_{axis}"

        if _positive(out, geom_key) is None:
            leff = _positive(out, leff_key)
            radius = _positive(out, radius_key)
            if radius is None:
                area = _positive(out, "A_gross")
                inertia = _positive(out, f"J_{axis}")
                if area is not None and inertia is not None:
                    radius = math.sqrt(inertia / area)
                    out[radius_key] = radius
                    _trace(out, radius_key, "section_radius_identity_sqrt_I_over_A", [f"J_{axis}", "A_gross"], "section geometry identity")

            if leff is not None and radius is not None:
                out[geom_key] = leff / radius
                _trace(out, geom_key, "qualified_definition_lambda_equals_leff_over_i", [leff_key, radius_key], "SP16 clause 10.3.1 / geometric slenderness definition")
            else:
                # MECH3/N7 can already have the qualified relative slenderness
                # while the geometric alias was not materialized in this route.
                # Invert exactly lambda_bar=lambda*sqrt(Ryn/E); no l_eff is guessed.
                relative = _positive(out, rel_key)
                if relative is not None and e is not None and ryn is not None:
                    out[geom_key] = relative * math.sqrt(e / ryn)
                    _trace(out, geom_key, "inverse_of_qualified_lambda_bar_definition", [rel_key, "E_norm", "fy_norm"], "SP16 relative-slenderness definition")

        if _positive(out, rel_key) is None:
            geom = _positive(out, geom_key)
            if geom is not None and e is not None and ryn is not None:
                out[rel_key] = geom * math.sqrt(ryn / e)
                _trace(out, rel_key, "qualified_lambda_bar_definition", [geom_key, "fy_norm", "E_norm"], "SP16 relative-slenderness definition")


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
    required = ("h_mm", "b_mm", "tw_mm", "tf_mm")
    if not all(_positive(dims, key) is not None for key in required):
        return

    patched = dict(geom)
    patched["template"] = "i_section"
    changed = False
    for key in required:
        if key not in patched:
            patched[key] = float(dims[key])
            changed = True
    out["section_geometry_2d_normalized"] = patched
    if changed or raw != "i_section":
        _trace(
            out,
            "section_geometry_2d_normalized",
            "catalog_geometry_contract_adapter",
            ["shape_group", "dimensions.h_mm", "dimensions.b_mm", "dimensions.tw_mm", "dimensions.tf_mm"],
            "geometry contract only; no normative resistance formula",
        )


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
        normalized = normalize_mech7_inputs(values)
        result = dict(original(normalized, node))
        trace = list(normalized.get("_sp16_v072_hydration_trace") or [])
        bundle = result.get("sp16_mech7_primary_evidence")
        if trace and isinstance(bundle, Mapping):
            patched = dict(bundle)
            patched["v072_prerequisite_hydration"] = trace
            result["sp16_mech7_primary_evidence"] = patched
        return result

    setattr(remediated, "_sp16_v072_remediated", True)
    setattr(remediated, "_sp16_v072_original", original)
    registry.executors[node_id] = remediated
    return registry
