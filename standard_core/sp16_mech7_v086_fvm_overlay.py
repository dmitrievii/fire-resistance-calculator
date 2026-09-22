"""v0.86 overlay: faster protected-FVM production/search UX contract."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v085_fvm_mesh_overlay import build_model as build_v085_model

GRAPH_SUFFIX = "_v086_fvm_fast_search_legends"


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.86 uses one qualified production FVM mesh in interactive calculations, "
        "keeps doubled-mesh convergence as a validation-only utility, and hardens the "
        "bounded minimum-thickness search around the first feasible crossing."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v085_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=copy.deepcopy(parent.presentation_policy),
    )


__all__ = ["GRAPH_SUFFIX", "build_model", "transform_graph"]
