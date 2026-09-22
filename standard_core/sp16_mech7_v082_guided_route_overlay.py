"""v0.82 guided-route closure: inline ambient B and executable SP554 8.6 gamma_e."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v081_end_to_end_overlay import build_model as build_v081_model

GRAPH_SUFFIX = "_v082_full_guided_route_closure"
AMBIENT_LOAD_NODE_ID = "SP16_I_AMBIENT_LOADS"
AMBIENT_B_DECISION_NODE_ID = "SP16_D_AMBIENT_BIMOMENT_REQUIRED"
AMBIENT_B_INPUT_NODE_ID = "SP16_I_AMBIENT_BIMOMENT_DIRECT"
AMBIENT_CENSUS_NODE_ID = "SP16_C_AMBIENT_APPLICABILITY_CENSUS"
GAMMA_E_NODE_ID = "SP554_C_GAMMAE_OUTPUT"
GAMMA_E_QID = "gamma_e_compression"


def _edge(edge_id: str, source: str, target: str, qids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": edge_id,
        "from_node_id": source,
        "to_node_id": target,
        "edge_type": "control",
        "label": edge_id,
        "condition": None,
        "quantity_ids": list(qids or []),
    }


def _binding(qid: str, role: str) -> dict[str, Any]:
    return {"quantity_id": qid, "required": True, "binding_role": role}


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    nodes = {row["id"]: row for row in out.get("nodes", [])}
    ambient = nodes.get(AMBIENT_LOAD_NODE_ID)
    if ambient is None:
        raise ValueError(f"v0.82 requires {AMBIENT_LOAD_NODE_ID}")
    produced = {row.get("quantity_id") for row in ambient.get("produces", [])}
    if "ambient_B_bimoment" not in produced:
        ambient.setdefault("produces", []).append(_binding("ambient_B_bimoment", "output"))

    gamma = nodes.get(GAMMA_E_NODE_ID)
    if gamma is None:
        raise ValueError(f"v0.82 requires frozen SP554 node {GAMMA_E_NODE_ID}")
    gamma["node_type"] = "calculation"
    gamma["consumes"] = [
        _binding("N_force", "input"),
        _binding("sp16_v081_governing_stability_axis", "input"),
        _binding("sp16_l_eff_z", "input"),
        _binding("sp16_l_eff_y", "input"),
        _binding("sp16_i_z", "input"),
        _binding("sp16_i_y", "input"),
        _binding("A_gross", "input"),
        _binding("E_norm", "input"),
    ]
    gamma["produces"] = [_binding(GAMMA_E_QID, "output")]
    gamma.pop("input_spec", None)
    gamma["calculation_spec"] = {
        "formula_type": "executor",
        "expression_language": "executor_v1",
        "algorithm_id": "sp554_v082_gamma_e_8_6_from_qualified_sp16_axis_v1",
        "bindings": [],
        "rounding": {"mode": "none"},
    }
    notes = dict(gamma.get("notes") or {})
    notes.update({
        "engineering_meaning": "SP554 8.6 gamma_e is calculated from the same governing SP16 principal axis selected by the v0.81 stability handoff.",
        "limitations": "No gamma_e default, interpolation, axis averaging or hidden extrapolation is permitted.",
        "normative_warning": "Uses exact identity J=A*i^2 on the selected principal axis in N-mm units: gamma_e=|N|*l_eff^2/(pi^2*E*J).",
    })
    gamma["notes"] = notes

    retired = {AMBIENT_B_DECISION_NODE_ID, AMBIENT_B_INPUT_NODE_ID}
    out["edges"] = [edge for edge in out.get("edges", []) if edge.get("to_node_id") not in retired]
    edge_ids = {edge.get("id") for edge in out["edges"]}
    if "V082_E_AMBIENT_LOADS_TO_CENSUS" not in edge_ids:
        out["edges"].append(_edge(
            "V082_E_AMBIENT_LOADS_TO_CENSUS",
            AMBIENT_LOAD_NODE_ID,
            AMBIENT_CENSUS_NODE_ID,
            ["ambient_B_bimoment"],
        ))

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.82 inlines signed ambient bimoment B into the ordinary-design load card, "
        "retires its duplicate prompt, and makes SP554 8.6 gamma_e an executable exact producer."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    retired = {AMBIENT_B_DECISION_NODE_ID, AMBIENT_B_INPUT_NODE_ID}
    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(retired)
    out["hidden_normative_nodes"] = sorted(hidden)
    excluded = set(out.get("guided_excluded_nodes") or [])
    excluded.update(retired)
    out["guided_excluded_nodes"] = sorted(excluded)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v081_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=transform_presentation_policy(parent.presentation_policy),
    )


__all__ = [
    "AMBIENT_B_DECISION_NODE_ID", "AMBIENT_B_INPUT_NODE_ID", "AMBIENT_LOAD_NODE_ID",
    "GAMMA_E_NODE_ID", "GAMMA_E_QID", "GRAPH_SUFFIX", "build_model", "transform_graph",
    "transform_presentation_policy",
]
