"""Scope v0.91 guided executors to the DAG contract that declares them.

``standard_core`` is imported by historical frozen FIRE-UI regression packages as
well as by the current Streamlit application.  v0.91 must not mutate the
engineering contract of those older frozen graphs.  The current v0.91 graph is
identified structurally by its typed trace outputs; only that graph receives the
new two-axis §§8.6/9.2 executors.  Older graphs retain the executor selected by
their own registry builder.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import fire_bridge2_qualified_state as _bridge2
from .fire_sp554_runtime_v091 import (
    _gamma_e_8_6_declarative_final,
    _phi_9_2_declarative_final,
)
from .fire_sp554_v091_guided_overlay import (
    PHI_NODE_ID,
    STIFFNESS_TRACE_QID,
    STRENGTH_TRACE_QID,
)
from .sp16_mech7_v083_full_route_overlay import GAMMA_E_NODE_ID


def _declares(node: Mapping[str, Any] | None, quantity_id: str) -> bool:
    if not isinstance(node, Mapping):
        return False
    return any(
        isinstance(row, Mapping) and row.get("quantity_id") == quantity_id
        for row in node.get("produces") or []
    )


def install() -> None:
    """Restore frozen-DAG isolation while retaining v0.91 production executors."""
    if getattr(_bridge2, "_v091_registry_scope_installed", False):
        return

    # fire_sp554_runtime_v091 stores the pre-v0.91 builder explicitly.  Calling
    # it here gives historical graphs exactly the registry they had before the
    # final-SP554 overlay, rather than trying to emulate their formulas.
    legacy_builder = getattr(_bridge2, "_v091_previous_registry_builder", None)
    if legacy_builder is None:
        legacy_builder = _bridge2._build_fire_bridge2_registry

    def _build_scoped(catalog, registry=None):
        reg = legacy_builder(catalog, registry)
        legacy_phi = reg.get(PHI_NODE_ID)
        legacy_gamma = reg.get(GAMMA_E_NODE_ID)

        def _phi_scoped(values, node):
            if _declares(node, STRENGTH_TRACE_QID):
                return _phi_9_2_declarative_final(values, node)
            if legacy_phi is None:
                raise ValueError(f"no legacy executor registered for {PHI_NODE_ID}")
            return legacy_phi(values, node)

        def _gamma_scoped(values, node):
            if _declares(node, STIFFNESS_TRACE_QID):
                return _gamma_e_8_6_declarative_final(values, node)
            if legacy_gamma is None:
                raise ValueError(f"no legacy executor registered for {GAMMA_E_NODE_ID}")
            return legacy_gamma(values, node)

        reg.register(PHI_NODE_ID, _phi_scoped)
        reg.register(GAMMA_E_NODE_ID, _gamma_scoped)
        return reg

    _bridge2._build_fire_bridge2_registry = _build_scoped
    _bridge2._v091_registry_scope_installed = True


__all__ = ["install"]
