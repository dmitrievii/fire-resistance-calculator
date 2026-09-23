"""Keep v0.91 guided executors isolated from historical frozen FIRE-UI DAGs.

The FIRE-UI scheduler deliberately supports two execution paths for a calculation
node: an explicitly registered Python executor, or the declarative specification
stored in the frozen DAG.  Historical graphs use that declarative fallback for
some SP554 nodes.  Therefore v0.91 must not install a compatibility wrapper for
those node IDs globally: even a wrapper that only delegates conditionally would
shadow the historical declarative path.

``fire_sp554_runtime_v091.install()`` retains the legacy package-initialisation
hook for backward compatibility and records the pre-v0.91 bridge-registry
builder.  This module restores that original builder after the current mechanics
overlay is installed.  The v0.91 Streamlit/application installer then binds the
new two-axis §§8.6/9.2 executors explicitly to the v0.91 application registry.
"""
from __future__ import annotations

from . import fire_bridge2_qualified_state as _bridge2


def install() -> None:
    """Restore the native frozen-DAG registry builder and leave v0.91 binding explicit."""
    if getattr(_bridge2, "_v091_registry_scope_installed", False):
        return

    previous_builder = getattr(_bridge2, "_v091_previous_registry_builder", None)
    if previous_builder is not None:
        # Critical isolation rule: historical DAGs must see the exact registry
        # builder that existed before v0.91.  Missing explicit executors are
        # intentional there and allow fire_ui0 to execute the frozen
        # calculation_spec through its declarative runtime.
        _bridge2._build_fire_bridge2_registry = previous_builder

    _bridge2._v091_registry_scope_installed = True
    _bridge2._v091_frozen_dag_declarative_fallback_preserved = True


__all__ = ["install"]
