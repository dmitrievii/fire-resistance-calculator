"""v0.74 SP16-MECH7 Annex Б.1 physical-property remediation.

This compatibility layer closes the remaining MECH7 integration gap for the
rolled-steel modulus of elasticity. ``E_norm`` is not a new user input and is
not a hidden engineering default: it is materialized from the already-qualified
SP16 Annex Б, Table Б.1 dataset exposed by
:class:`SteelMaterialStrengthResolver`.

The layer deliberately materializes only the canonical quantity currently
consumed by MECH7 (``E_norm``). Other Table Б.1 properties are left untouched
until a production quantity contract consumes them. Existing explicit
``E_norm`` values are never overwritten; malformed explicit values therefore
remain fail-closed in the downstream binder.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .material_resistance import SteelMaterialStrengthResolver
from .sp16_mech7_v072_remediation import (
    install_registry_remediation as install_v072_registry_remediation,
    normalize_mech7_inputs as normalize_v072_mech7_inputs,
)

_BINDER_NODE_ID = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0.0 else None


def _hydrate_annex_b1_elastic_modulus(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with source-backed ``E_norm`` when that quantity is absent."""
    out = dict(values)

    # Never replace an explicit producer, even if it is malformed. That keeps
    # conflicting upstream evidence visible and preserves fail-closed semantics.
    if "E_norm" in out:
        return out

    physical = SteelMaterialStrengthResolver().physical_properties()
    elastic_modulus = _positive_number(physical.get("E_MPa"))
    if elastic_modulus is None:
        raise FireUIError("qualified SP16 Table Б.1 E_MPa is unavailable")

    out["E_norm"] = elastic_modulus
    trace = out.setdefault("_sp16_v074_hydration_trace", [])
    trace.append(
        {
            "quantity_id": "E_norm",
            "source": "SteelMaterialStrengthResolver.physical_properties",
            "source_quantity": "E_MPa",
            "source_table": str(physical.get("source_table") or "Б.1"),
            "source_sha256": physical.get("source_sha256"),
            "normative_scope": "SP16 Annex Б, Table Б.1",
        }
    )
    return out


def normalize_mech7_inputs(values: Mapping[str, Any]) -> dict[str, Any]:
    """Build the complete v0.74 local MECH7 compatibility view.

    Annex Б.1 hydration runs before the v0.72 Table-2/slenderness adapter so the
    latter can use ``E_norm`` when reconstructing exact lambda/lambda_bar aliases.
    """
    return normalize_v072_mech7_inputs(_hydrate_annex_b1_elastic_modulus(values))


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Install v0.72 plus the v0.74 physical-property wrapper exactly once.

    The pre-check is intentionally performed before invoking the historical
    v0.72 installer. Streamlit calls this function on every rerun for retained
    applications; without the pre-check v0.72 could wrap an already-v0.74
    executor and grow an unbounded wrapper chain.
    """
    current = registry.executors.get(_BINDER_NODE_ID)
    if current is None:
        raise FireUIError(f"v0.74 remediation requires registered {_BINDER_NODE_ID}")
    if getattr(current, "_sp16_v074_remediated", False):
        return registry

    # Fresh registries still need the qualified Table-2/slenderness layer.
    # Historical v0.72-only retained registries are left unchanged by its own
    # idempotency guard and are then upgraded below.
    install_v072_registry_remediation(registry)

    original = registry.executors.get(_BINDER_NODE_ID)
    if original is None:
        raise FireUIError(f"v0.74 remediation requires registered {_BINDER_NODE_ID}")
    if getattr(original, "_sp16_v074_remediated", False):
        return registry

    def remediated(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        normalized = normalize_mech7_inputs(values)
        result = dict(original(normalized, node))
        trace = list(normalized.get("_sp16_v074_hydration_trace") or [])
        bundle = result.get("sp16_mech7_primary_evidence")
        if trace and isinstance(bundle, Mapping):
            patched = dict(bundle)
            patched["v074_prerequisite_hydration"] = trace
            result["sp16_mech7_primary_evidence"] = patched
        return result

    # Mark the outer wrapper as satisfying both generations. This matters because
    # a retained v0.73 accessor still invokes the v0.72 installer before the
    # outer v0.74 accessor runs on a Streamlit rerun.
    setattr(remediated, "_sp16_v072_remediated", True)
    setattr(remediated, "_sp16_v074_remediated", True)
    setattr(remediated, "_sp16_v074_original", original)
    registry.executors[_BINDER_NODE_ID] = remediated
    return registry


__all__ = ["install_registry_remediation", "normalize_mech7_inputs"]
