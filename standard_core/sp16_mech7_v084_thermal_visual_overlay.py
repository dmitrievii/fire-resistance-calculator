"""v0.84 thermal-visualization overlay for the production guided route.

The unprotected-member method is no longer an engineering choice in the guided
UI.  The application always executes SP554 12.1-12.4 and visualizes that exact
calculation together with the reconstructed standard reduced-thickness curves.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v083_full_route_overlay import build_model as build_v083_model

GRAPH_SUFFIX = "_v084_thermal_visualization"
UNPROTECTED_METHOD_NODE_ID = "SP554_D_UNPROTECTED_METHOD"
UNPROTECTED_METHOD_QID = "unprotected_heating_method"


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    nodes = {row["id"]: row for row in out.get("nodes", [])}
    node = nodes.get(UNPROTECTED_METHOD_NODE_ID)
    if node is None:
        raise ValueError(f"v0.84 requires {UNPROTECTED_METHOD_NODE_ID}")
    node["node_type"] = "calculation"
    node.pop("question", None)
    node.pop("decision_quantity_id", None)
    node.pop("options", None)
    node["calculation_spec"] = {
        "formula_type": "executor",
        "expression_language": "executor_v1",
        "algorithm_id": "sp554_v084_unprotected_step_route_v1",
        "bindings": [],
        "rounding": {"mode": "none"},
    }
    notes = dict(node.get("notes") or {})
    notes.update({
        "engineering_meaning": (
            "Guided production route uses the explicit SP554 12.1-12.4 calculation; "
            "the former Figure-1/method selector is replaced by a calculated diagram."
        ),
        "normative_warning": (
            "The plotted 3/5/10/15/20 mm curves and the actual reduced-thickness curve "
            "are generated from the same 12.1-12.4 recurrence; the chart is not a second calculation method."
        ),
    })
    node["notes"] = notes
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.84 removes the unprotected nomogram-vs-calculation question and binds the guided route "
        "to explicit SP554 12.1-12.4 calculation with calculated thermal visualization."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v083_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=copy.deepcopy(parent.presentation_policy),
    )


__all__ = [
    "GRAPH_SUFFIX",
    "UNPROTECTED_METHOD_NODE_ID",
    "UNPROTECTED_METHOD_QID",
    "build_model",
    "transform_graph",
]
