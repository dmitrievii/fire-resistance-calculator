"""v0.80 guided cleanup for superseded scalar effective-length mechanics.

The active Stage-N7 contract is the v0.76 canonical two-axis z/y effective-
length state.  The frozen source DAG still contains the older scalar
``SP16_C_LAMBDA`` producer, which consumes a generic ``l_eff``.  That scalar
quantity cannot be reconstructed from the z/y state without choosing an axis,
so v0.80 retires the legacy calculation node from guided scheduling rather than
inventing an alias or resultant.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v079_guided_route_overlay import build_model as build_v079_model

GRAPH_SUFFIX = "_v080_guided_cleanup"
LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES = {"SP16_C_LAMBDA"}


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    # Preserve the historical calculation node and all data evidence in the
    # frozen model, but make it unreachable from guided control flow.  Data-
    # dependency scheduling is blocked by guided_excluded_nodes below.
    out["edges"] = [
        edge
        for edge in out["edges"]
        if not (
            edge.get("edge_type") in {"control", "branch", "handoff"}
            and edge.get("to_node_id") in LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES
        )
    ]
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.80 retires the legacy scalar SP16_C_LAMBDA guided producer; "
        "the canonical Stage-N7 state remains axis-specific z/y."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))

    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)

    excluded = set(out.get("guided_excluded_nodes") or [])
    excluded.update(LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES)
    out["guided_excluded_nodes"] = sorted(excluded)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    """Build through v0.79, then apply the v0.80 guided-only cleanup."""
    parent = build_v079_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=transform_presentation_policy(parent.presentation_policy),
    )


__all__ = [
    "GRAPH_SUFFIX",
    "LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES",
    "build_model",
    "transform_graph",
    "transform_presentation_policy",
]
