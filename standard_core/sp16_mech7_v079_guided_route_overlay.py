"""v0.79 graph/presentation remediation for retained guided sessions.

v0.76 introduced the canonical two-axis effective-length card.  Historical
single/axis-specific mu authoring nodes remain in the frozen source DAG for
release evidence, but they must not remain parallel guided branches after the
canonical card has been answered.  v0.79 removes only navigation edges *into*
those retired authoring nodes and marks them excluded from dependency-driven
navigation.  Numerical producers and the frozen source DAG are not deleted.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v076_graph_overlay import V075_EFFECTIVE_LENGTH_INPUT_NODES
from .sp16_mech7_v078_graph_overlay import build_model as build_v078_model

GRAPH_SUFFIX = "_v079_retained_guided_route"

# These nodes are superseded at the guided UI boundary by the v0.76 canonical
# z/y effective-length definition.  The first four entries are the original
# single/legacy SP16 Section-10 route that caused the repeated L/mu/Table-30
# questions reported against v0.78.  X/Y variants are likewise historical.
RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES = {
    "SP16_D_MU_ROUTE",
    "SP16_D_MU_SCHEME",
    "SP16_D_MU_ROUTE_X",
    "SP16_D_MU_SCHEME_X",
    "SP16_D_MU_ROUTE_Y",
    "SP16_D_MU_SCHEME_Y",
    "SP16_D_MU_ADV_METHOD_X",
    "SP16_D_MU_ADV_METHOD_Y",
    "SP16_I_MU_ANALYSIS_X",
    "SP16_I_MU_ANALYSIS_Y",
    "SP16_I_MU_ADVANCED_X",
    "SP16_I_MU_ADVANCED_Y",
    *V075_EFFECTIVE_LENGTH_INPUT_NODES,
}


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    # Do not delete historical nodes/calculation producers.  Only remove guided
    # control/branch/handoff entries into superseded authoring nodes.  Data edges
    # stay available to the engine for traceability, while guided dependency
    # scheduling is blocked by the presentation exclusion below.
    out["edges"] = [
        edge
        for edge in out["edges"]
        if not (
            edge.get("edge_type") in {"control", "branch", "handoff"}
            and edge.get("to_node_id") in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
        )
    ]
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.79 retires duplicate historical L/mu/Table-30 guided authoring "
        "after the canonical v0.76 z/y effective-length card."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)

    excluded = set(out.get("guided_excluded_nodes") or [])
    excluded.update(RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES)
    out["guided_excluded_nodes"] = sorted(excluded)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    """Build the v0.78 normative model, then apply only v0.79 route policy."""
    parent = build_v078_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=transform_presentation_policy(parent.presentation_policy),
    )


__all__ = [
    "GRAPH_SUFFIX",
    "RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES",
    "build_model",
    "transform_graph",
    "transform_presentation_policy",
]
