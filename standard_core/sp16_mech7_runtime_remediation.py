"""v0.72 bounded runtime remediation for SP16 MECH7 prerequisite bindings.

The active cumulative DAG already contains qualified producers for current-SP16
material resistances, geometric/relative slenderness and section geometry.  The
guided primary MECH7 binder, however, can be reached with some of those
intermediate aliases absent from the session ledger.  This module does not add
new normative equations.  It reconstructs only mathematically identical
intermediates from already-resolved qualified primitives before delegating to
frozen MECH7/8/9 executors.

Fail-closed semantics are preserved: if the required qualified primitives are
not present, nothing is guessed and the downstream executor remains DEFERRED.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from .fire_ui0 import ExecutionRegistry
from .material_resistance import (
    design_shear_resistance_n_mm2,
    design_ultimate_resistance_n_mm2,
    design_yield_resistance_n_mm2,
)


Executor = Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]


def _finite_positive(values: Mapping[str, Any], key: str) -> float | None:
    raw = values.get(key)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if not math.isfinite(value) or value <= 0.0:
        return None
    return value


def _hydrate_material_resistances(out: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    """Recover Table-2 formula resistances only from resolved Rn and gamma_m."""
    gamma_m = _finite_positive(out, "gamma_m")
    if gamma_m is None:
        return

    fy = _finite_positive(out, "fy_norm")
    fu = _finite_positive(out, "fu_norm")

    if "Ry_formula" not in out and fy is not None:
        out["Ry_formula"] = design_yield_resistance_n_mm2(fy, gamma_m)
        trace.append({
            "quantity_id": "Ry_formula",
            "source": "qualified_N1_design_yield_resistance_n_mm2",
            "inputs": ["fy_norm", "gamma_m"],
            "normative_scope": "SP16 Table 2 + Table 3",
        })
    if "Ru_formula" not in out and fu is not None:
        out["Ru_formula"] = design_ultimate_resistance_n_mm2(fu, gamma_m)
        trace.append({
            "quantity_id": "Ru_formula",
            "source": "qualified_N1_design_ultimate_resistance_n_mm2",
            "inputs": ["fu_norm", "gamma_m"],
            "normative_scope": "SP16 Table 2 + Table 3",
        })
    if "Rs_formula" not in out and fy is not None:
        out["Rs_formula"] = design_shear_resistance_n_mm2(fy, gamma_m)
        trace.append({
            "quantity_id": "Rs_formula",
            "source": "qualified_N1_design_shear_resistance_n_mm2",
            "inputs": ["fy_norm", "gamma_m"],
            "normative_scope": "SP16 Table 2 + Table 3",
        })


def _hydrate_slenderness(out: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    """Recover exact lambda/lambda_bar aliases without inventing effective lengths."""
    e = _finite_positive(out, "E_norm")
    ryn = _finite_positive(out, "fy_norm")

    for axis in ("x", "y"):
        geom_key = f"sp16_lambda_{axis}_geom"
        rel_key = f"lambda_bar_{axis}"
        leff_key = f"sp16_l_eff_{axis}"
        radius_key = f"sp16_i_{axis}"

        if geom_key not in out:
            leff = _finite_positive(out, leff_key)
            radius = _finite_positive(out, radius_key)
            if leff is not None and radius is not None:
                out[geom_key] = leff / radius
                trace.append({
                    "quantity_id": geom_key,
                    "source": "qualified_definition_lambda_equals_leff_over_i",
                    "inputs": [leff_key, radius_key],
                    "normative_scope": "SP16 clause 10.3.1 / geometric slenderness definition",
                })
            else:
                rel = _finite_positive(out, rel_key)
                if rel is not None and e is not None and ryn is not None:
                    out[geom_key] = rel * math.sqrt(e / ryn)
                    trace.append({
                        "quantity_id": geom_key,
                        "source": "inverse_of_qualified_lambda_bar_definition",
                        "inputs": [rel_key, "E_norm", "fy_norm"],
                        "normative_scope": "SP16 relative-slenderness definition",
                    })

        if rel_key not in out:
            geom = _finite_positive(out, geom_key)
            if geom is not None and e is not None and ryn is not None:
                out[rel_key] = geom * math.sqrt(ryn / e)
                trace.append({
                    "quantity_id": rel_key,
                    "source": "qualified_lambda_bar_definition",
                    "inputs": [geom_key, "fy_norm", "E_norm"],
                    "normative_scope": "SP16 relative-slenderness definition",
                })


def _hydrate_catalog_i_geometry(out: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    """Expose the already-normalized catalog I dimensions in MECH7's legacy view."""
    raw = out.get("section_geometry_2d_normalized")
    if not isinstance(raw, Mapping):
        return
    dims = raw.get("dimensions")
    shape = str(raw.get("shape_group") or raw.get("template") or raw.get("shape") or "")
    if shape not in {"I_ROLLED_DSYMM", "i_section", "doubly_symmetric_i"} or not isinstance(dims, Mapping):
        return
    required = ("h_mm", "b_mm", "tw_mm", "tf_mm")
    if not all(_finite_positive(dims, key) is not None for key in required):
        return
    normalized = dict(raw)
    normalized["template"] = "i_section"
    for key in required:
        normalized[key] = float(dims[key])
    out["section_geometry_2d_normalized"] = normalized
    trace.append({
        "quantity_id": "section_geometry_2d_normalized",
        "source": "catalog_geometry_contract_adapter",
        "inputs": ["shape_group", "dimensions.h_mm", "dimensions.b_mm", "dimensions.tw_mm", "dimensions.tf_mm"],
        "normative_scope": "geometry contract only; no resistance formula",
    })


def hydrate_mech_prerequisites(values: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a non-mutating qualified prerequisite view and explicit trace."""
    out = dict(values)
    trace: list[dict[str, Any]] = []
    _hydrate_material_resistances(out, trace)
    _hydrate_slenderness(out, trace)
    _hydrate_catalog_i_geometry(out, trace)
    return out, trace


def _wrap_executor(original: Executor) -> Executor:
    def run(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        hydrated, trace = hydrate_mech_prerequisites(values)
        result = dict(original(hydrated, node))
        # Attach audit evidence only inside the existing MECH evidence bundle.
        # No undeclared top-level DAG output is introduced.
        for key in (
            "sp16_mech7_primary_evidence",
            "sp16_mech8_primary_evidence",
            "sp16_mech9_primary_evidence",
        ):
            bundle = result.get(key)
            if isinstance(bundle, Mapping):
                patched = dict(bundle)
                patched["v072_prerequisite_hydration"] = list(trace)
                result[key] = patched
                break
        return result
    return run


def install_sp16_mech7_v072_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Wrap the cumulative MECH7-9 binders with bounded prerequisite hydration."""
    node_ids = (
        "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER",
        "SP16_C_MECH8_INTERACTION_BINDER",
        "SP16_C_MECH9_REMAINING_AMBIENT_BINDER",
    )
    for node_id in node_ids:
        original = registry.get(node_id)
        if original is not None:
            registry.executors[node_id] = _wrap_executor(original)
    return registry
