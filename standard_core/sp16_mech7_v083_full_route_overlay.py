"""v0.83 production-route closure for central-compression SP16 -> SP554 guided flow.

This overlay closes defects found only by replaying the real Streamlit guided
calculation from its public entry node: the fire-load decision was typed as a
free string, the fire section-formula route re-entered a legacy Table-1 prompt
and member-length chain after the exact SP16 classification/effective-length
state already existed, and the executable SP554 8.6 producer did not expose the
``gamma_E_required`` quantity consumed by FIRE-UI1.7.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v082_guided_route_overlay import build_model as build_v082_model

GRAPH_SUFFIX = "_v083_full_guided_e2e_closure"
FIRE_LOAD_MODE_QID = "fire_load_case_mode"
FIRE_LOAD_MODE_NODE_ID = "SP16_D_FIRE_LOAD_CASE_MODE"
GAMMA_E_NODE_ID = "SP554_C_GAMMAE_OUTPUT"
GAMMA_E_INTERNAL_QID = "gamma_e_compression"
GAMMA_E_REQUIRED_QID = "gamma_E_required"
COMPRESSION_CONTEXT_NODE_ID = "SP554_I_COMPRESSION_CONTEXT"
COMPRESSION_GAMMA_T_NODE_ID = "SP554_C_9_2"
GAMMA_T_METHOD_NODE_ID = "SP554_D_GAMMA_T_METHOD"
LEGACY_TABLE1_COMPRESSION_NODES = {"SP16_D_GC_C", "SP16_L_GC_C"}


def _binding(qid: str, role: str, *, required: bool = True) -> dict[str, Any]:
    return {"quantity_id": qid, "required": required, "binding_role": role}


def _branch(edge_id: str, source: str, target: str, condition: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": edge_id,
        "from_node_id": source,
        "to_node_id": target,
        "edge_type": "branch",
        "label": "v0.83 exact SP16 state -> SP554 central-compression section formula",
        "condition": copy.deepcopy(dict(condition)),
        "quantity_ids": ["gamma_c_compression"],
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    quantities = {row["id"]: row for row in out.get("quantities", [])}
    nodes = {row["id"]: row for row in out.get("nodes", [])}

    # The node is a decision with two explicit choices.  Typing its quantity as
    # enum makes the generic renderer a real selector instead of a free string.
    mode_q = quantities.get(FIRE_LOAD_MODE_QID)
    mode_node = nodes.get(FIRE_LOAD_MODE_NODE_ID)
    if mode_q is None or mode_node is None:
        raise ValueError("v0.83 requires the FIRE_LOAD_CASE mode decision")
    mode_q["data_type"] = "enum"
    mode_q["enum_values"] = [
        {"value": row["value"], "label": row.get("label") or row["value"]}
        for row in mode_node.get("options", [])
    ]

    # v0.82 calculated the physical coefficient correctly but changed the
    # frozen bridge node to expose only the internal name.  FIRE-UI1.7 consumes
    # gamma_E_required.  One executor now writes both names from the same exact
    # number; no default, approximation or reverse inference is introduced.
    gamma_node = nodes.get(GAMMA_E_NODE_ID)
    if gamma_node is None:
        raise ValueError(f"v0.83 requires {GAMMA_E_NODE_ID}")
    gamma_node["produces"] = [
        _binding(GAMMA_E_INTERNAL_QID, "output"),
        _binding(GAMMA_E_REQUIRED_QID, "output"),
    ]
    spec = dict(gamma_node.get("calculation_spec") or {})
    spec["algorithm_id"] = "sp554_v083_gamma_e_8_6_dual_contract_v1"
    gamma_node["calculation_spec"] = spec

    # The exact compression Table-1 case was already authored upstream by v0.78
    # and gamma_c_compression is already in the ledger before the SP16 PASS gate.
    # Re-entering SP16_D_GC_C asks a second, less precise question.  Remove only
    # scheduling edges into that obsolete compression-only pair.
    out["edges"] = [
        edge for edge in out.get("edges", [])
        if edge.get("to_node_id") not in LEGACY_TABLE1_COMPRESSION_NODES
    ]

    # For the central-compression section-formula route, the old compression
    # context existed to author a scalar member length / mu / Table-1 chain.
    # Canonical z/y effective lengths, the governing axis and exact gamma_c have
    # already passed SP16.  Route directly to SP554 9.2; its missing dependency
    # scheduler resolves the v0.81 governing stability handoff as needed.
    section_compression_condition = {
        "type": "all_of",
        "conditions": [
            {"type": "comparison", "quantity_id": "strength_coefficient_method", "operator": "eq", "value": "section_formulas"},
            {"type": "comparison", "quantity_id": "stress_state", "operator": "eq", "value": "central_compression"},
        ],
    }
    out["edges"] = [
        edge for edge in out["edges"]
        if not (
            edge.get("from_node_id") == GAMMA_T_METHOD_NODE_ID
            and edge.get("to_node_id") == COMPRESSION_CONTEXT_NODE_ID
            and edge.get("condition") == section_compression_condition
        )
    ]
    if not any(edge.get("id") == "V083_E_METHOD_TO_COMPRESSION_9_2" for edge in out["edges"]):
        out["edges"].append(_branch(
            "V083_E_METHOD_TO_COMPRESSION_9_2",
            GAMMA_T_METHOD_NODE_ID,
            COMPRESSION_GAMMA_T_NODE_ID,
            section_compression_condition,
        ))

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.83 closes the real central-compression guided route: FIRE load mode "
        "is an enum selector, the already-explicit SP16 Table-1 classification is "
        "not asked again, legacy scalar member-length authoring is bypassed, and "
        "SP554 8.6 supplies gamma_E_required to FIRE-UI1.7."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(LEGACY_TABLE1_COMPRESSION_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)
    excluded = set(out.get("guided_excluded_nodes") or [])
    excluded.update(LEGACY_TABLE1_COMPRESSION_NODES)
    out["guided_excluded_nodes"] = sorted(excluded)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v082_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=transform_presentation_policy(parent.presentation_policy),
    )


__all__ = [
    "COMPRESSION_CONTEXT_NODE_ID",
    "FIRE_LOAD_MODE_NODE_ID",
    "FIRE_LOAD_MODE_QID",
    "GAMMA_E_NODE_ID",
    "GAMMA_E_REQUIRED_QID",
    "GRAPH_SUFFIX",
    "LEGACY_TABLE1_COMPRESSION_NODES",
    "build_model",
    "transform_graph",
    "transform_presentation_policy",
]
