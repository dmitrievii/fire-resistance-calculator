"""v0.85 overlay: qualified protected-member FVM mesh/visualization contract."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v084_thermal_visual_overlay import build_model as build_v084_model

GRAPH_SUFFIX = "_v085_fvm_mesh_gradient"


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.85 replaces the fixed three-interval protected FVM discretization with an "
        "automatic spatial mesh and stable time step, and separates protection-node and "
        "lumped-steel temperatures in the visualization contract."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v084_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=copy.deepcopy(parent.presentation_policy),
    )


__all__ = ["GRAPH_SUFFIX", "build_model", "transform_graph"]
