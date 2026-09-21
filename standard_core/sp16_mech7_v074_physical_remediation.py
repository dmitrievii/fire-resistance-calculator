"""v0.74 SP16-MECH7 source-backed prerequisite hydration.

This compatibility layer closes two integration gaps between already-qualified
N1 data and the MECH7 primary binder:

* ``E_norm`` is materialized from SP16 Annex Б, Table Б.1 through
  :class:`SteelMaterialStrengthResolver`;
* ``gamma_u`` is materialized from the existing SP16 clause 4.3.2 dataset.

Neither value is a user-entered parameter or an engineering default. Existing
explicit producers are never overwritten, including malformed values, so
conflicting upstream evidence remains visible and downstream execution stays
fail-closed.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .material_resistance import SteelMaterialStrengthResolver
from .sp16_mech7_v072_remediation import (
    install_registry_remediation as install_v072_registry_remediation,
    normalize_mech7_inputs as normalize_v072_mech7_inputs,
)

_BINDER_NODE_ID = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0.0 else None


def _trace(out: dict[str, Any], row: Mapping[str, Any]) -> None:
    out.setdefault("_sp16_v074_hydration_trace", []).append(dict(row))


def _hydrate_annex_b1_elastic_modulus(out: dict[str, Any]) -> None:
    """Materialize source-backed ``E_norm`` only when no producer exists."""
    if "E_norm" in out:
        return

    physical = SteelMaterialStrengthResolver().physical_properties()
    elastic_modulus = _positive_number(physical.get("E_MPa"))
    if elastic_modulus is None:
        raise FireUIError("qualified SP16 Table Б.1 E_MPa is unavailable")

    out["E_norm"] = elastic_modulus
    _trace(
        out,
        {
            "quantity_id": "E_norm",
            "source": "SteelMaterialStrengthResolver.physical_properties",
            "source_quantity": "E_MPa",
            "source_table": str(physical.get("source_table") or "Б.1"),
            "source_sha256": physical.get("source_sha256"),
            "normative_scope": "SP16 Annex Б, Table Б.1",
        },
    )


def _hydrate_clause_4_3_2_gamma_u(out: dict[str, Any]) -> None:
    """Materialize the qualified clause-4.3.2 ``gamma_u`` constant if absent."""
    if "gamma_u" in out:
        return

    path = _DATA_DIR / "clause_4_3_2_gamma_u.json"
    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FireUIError("qualified SP16 clause 4.3.2 gamma_u dataset is unavailable") from exc

    gamma_u = _positive_number(dataset.get("gamma_u"))
    if gamma_u is None:
        raise FireUIError("qualified SP16 clause 4.3.2 gamma_u is unavailable")

    out["gamma_u"] = gamma_u
    source = dataset.get("normative_source") if isinstance(dataset.get("normative_source"), Mapping) else {}
    _trace(
        out,
        {
            "quantity_id": "gamma_u",
            "source": "data/clause_4_3_2_gamma_u.json",
            "source_quantity": "gamma_u",
            "source_clause": str(dataset.get("clause") or "4.3.2"),
            "source_sha256": source.get("source_sha256"),
            "applicability": dataset.get("applicability"),
            "normative_scope": "SP16 clause 4.3.2",
        },
    )


def _hydrate_source_backed_n1_prerequisites(values: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(values)
    _hydrate_annex_b1_elastic_modulus(out)
    _hydrate_clause_4_3_2_gamma_u(out)
    return out


def normalize_mech7_inputs(values: Mapping[str, Any]) -> dict[str, Any]:
    """Build the complete v0.74 local MECH7 compatibility view.

    Source-backed N1 hydration runs before the v0.72 Table-2/slenderness adapter
    so the latter can use ``E_norm`` when reconstructing exact lambda aliases.
    """
    return normalize_v072_mech7_inputs(_hydrate_source_backed_n1_prerequisites(values))


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Install v0.72 plus the v0.74 prerequisite wrapper exactly once.

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

    # v0.73 still invokes the historical v0.72 installer on retained apps before
    # the outer v0.74 accessor; advertise both markers to keep that path stable.
    setattr(remediated, "_sp16_v072_remediated", True)
    setattr(remediated, "_sp16_v074_remediated", True)
    setattr(remediated, "_sp16_v074_original", original)
    registry.executors[_BINDER_NODE_ID] = remediated
    return registry


__all__ = ["install_registry_remediation", "normalize_mech7_inputs"]
