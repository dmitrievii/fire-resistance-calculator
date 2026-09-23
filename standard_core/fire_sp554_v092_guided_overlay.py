"""v0.92 guided-SP554 overlay: remove the obsolete user gamma_ct branch.

Final SP 554.1311500.2026 uses the mandatory special-limit-state coefficient
``gamma_ct = 1.1`` in the migrated fire-mechanics runtime.  The historical
FIRE-UI DAG still contains an interactive boolean decision followed by a
calculation node and a diagnostic result saying that composition of gamma_ct
with Sections 9-11 requires interpretation.  That diagnostic subgraph belongs
to the pre-final-publication implementation and must not remain in the active
v0.92 guided route.

The frozen DAG file remains unchanged.  This module transforms only the active
in-memory graph:

* the obsolete decision, historical gamma_ct calculation and interpretation
  result are removed;
* predecessors of the obsolete decision continue to the normal ambient-load
  workflow node ``SP16_I_AMBIENT_LOADS``;
* no historical true/false answer is copied into the new ledger;
* ``gamma_ct = 1.1`` is owned by the final-publication mechanical runtime, not
  by a hidden or synthetic guided answer.

The real frozen DAG deliberately has more than one outgoing edge from the old
decision (false branch, true branch and a diagnostic data edge).  Therefore the
v0.92 bypass target is explicit and normative-workflow-specific rather than
inferred from a fictitious single-successor topology.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession, FireUIError

OBSOLETE_GAMMA_CT_NODE_ID = "SP554_D_GOST27751_GAMMA_CT"
OBSOLETE_GAMMA_CT_CALC_NODE_ID = "SP554_C_GAMMA_CT_8_1"
OBSOLETE_GAMMA_CT_RESULT_NODE_ID = "SP554_R_GAMMA_CT_APPLICATION_INTERPRETATION_REQUIRED"
BYPASS_SUCCESSOR_NODE_ID = "SP16_I_AMBIENT_LOADS"
OBSOLETE_GAMMA_CT_SUBGRAPH = frozenset(
    {
        OBSOLETE_GAMMA_CT_NODE_ID,
        OBSOLETE_GAMMA_CT_CALC_NODE_ID,
        OBSOLETE_GAMMA_CT_RESULT_NODE_ID,
    }
)
GRAPH_SUFFIX = "_v092_gamma_ct_guided_bypass"


def _produced_quantity_ids(node: Mapping[str, Any]) -> set[str]:
    qids = {
        str(row["quantity_id"])
        for row in node.get("produces", [])
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str)
    }
    decision_qid = node.get("decision_quantity_id")
    if isinstance(decision_qid, str):
        qids.add(decision_qid)
    return qids


def _referenced_quantity_ids(graph: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for node in graph.get("nodes", []):
        if not isinstance(node, Mapping):
            continue
        for key in ("consumes", "produces"):
            for row in node.get(key, []):
                if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
                    refs.add(str(row["quantity_id"]))
        qid = node.get("decision_quantity_id")
        if isinstance(qid, str):
            refs.add(qid)
        applicability = node.get("applicability")
        if isinstance(applicability, Mapping):
            qid = applicability.get("quantity_id")
            if isinstance(qid, str):
                refs.add(qid)
    for edge in graph.get("edges", []):
        if not isinstance(edge, Mapping):
            continue
        for qid in edge.get("quantity_ids", []) or []:
            if isinstance(qid, str):
                refs.add(qid)
        condition = edge.get("condition")
        if isinstance(condition, Mapping):
            qid = condition.get("quantity_id")
            if isinstance(qid, str):
                refs.add(qid)
    return refs


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Remove the historical gamma_ct diagnostic subgraph from the active DAG."""
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    nodes = [row for row in out.get("nodes", []) if isinstance(row, Mapping)]
    node_ids = {str(row.get("id")) for row in nodes}
    obsolete = next(
        (row for row in nodes if row.get("id") == OBSOLETE_GAMMA_CT_NODE_ID),
        None,
    )
    if obsolete is None:
        # A later frozen graph may already contain the remediation.  Mark the
        # active graph but do not attempt to manufacture historical topology.
        out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
        return out
    if BYPASS_SUCCESSOR_NODE_ID not in node_ids:
        raise FireUIError(
            "v0.92 gamma_ct bypass: canonical continuation node "
            f"{BYPASS_SUCCESSOR_NODE_ID} is absent"
        )

    edges = [copy.deepcopy(row) for row in out.get("edges", [])]
    incoming = [
        row
        for row in edges
        if row.get("to_node_id") == OBSOLETE_GAMMA_CT_NODE_ID
        and row.get("from_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
    ]
    if not incoming:
        raise FireUIError(
            f"v0.92 gamma_ct bypass: {OBSOLETE_GAMMA_CT_NODE_ID} has no predecessor"
        )

    obsolete_qids = _produced_quantity_ids(obsolete)
    retained_edges = [
        row
        for row in edges
        if row.get("from_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
        and row.get("to_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
    ]

    # The final-publication runtime owns gamma_ct=1.1.  The active guided graph
    # therefore continues through the same normal mechanical workflow that was
    # historically reached after the old decision, without preserving either
    # true/false condition from that decision.
    existing_pairs = {
        (
            str(row.get("from_node_id")),
            str(row.get("to_node_id")),
            str(row.get("edge_type") or ""),
        )
        for row in retained_edges
    }
    for index, source_edge in enumerate(incoming, start=1):
        predecessor = str(source_edge.get("from_node_id") or "")
        if not predecessor:
            raise FireUIError("v0.92 gamma_ct bypass found predecessor-less incoming edge")
        edge_type = str(source_edge.get("edge_type") or "control")
        pair = (predecessor, BYPASS_SUCCESSOR_NODE_ID, edge_type)
        if pair in existing_pairs:
            continue
        carried = [
            str(qid)
            for qid in (source_edge.get("quantity_ids") or [])
            if isinstance(qid, str) and qid not in obsolete_qids
        ]
        retained_edges.append(
            {
                "id": (
                    f"V092_GAMMA_CT_BYPASS_{index}_{predecessor}_TO_"
                    f"{BYPASS_SUCCESSOR_NODE_ID}"
                ),
                "from_node_id": predecessor,
                "to_node_id": BYPASS_SUCCESSOR_NODE_ID,
                "edge_type": edge_type,
                "label": "v0.92: gamma_ct=1.1 owned by final runtime; obsolete guided branch removed",
                "condition": copy.deepcopy(source_edge.get("condition")),
                "quantity_ids": carried,
            }
        )
        existing_pairs.add(pair)

    out["nodes"] = [
        copy.deepcopy(row)
        for row in out.get("nodes", [])
        if row.get("id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
    ]
    out["edges"] = retained_edges

    # The old boolean state is no longer a normative input.  Remove it when it
    # became a true orphan after deleting the diagnostic subgraph.  gamma_ct
    # itself is retained if any other historical declaration still references
    # it; the active v0.92 runtime does not read a user value from it.
    refs = _referenced_quantity_ids(out)
    removable = obsolete_qids.difference(refs)
    if removable:
        out["quantities"] = [
            copy.deepcopy(row)
            for row in out.get("quantities", [])
            if row.get("id") not in removable
        ]

    policy = out.get("presentation_policy")
    if isinstance(policy, dict):
        table = policy.get("node_presentation")
        if isinstance(table, dict):
            for node_id in OBSOLETE_GAMMA_CT_SUBGRAPH:
                table.pop(node_id, None)
        hidden = policy.get("hidden_normative_nodes")
        if isinstance(hidden, list):
            policy["hidden_normative_nodes"] = [
                node_id for node_id in hidden if node_id not in OBSOLETE_GAMMA_CT_SUBGRAPH
            ]
        deferred = policy.get("deferred_nodes")
        if isinstance(deferred, dict):
            for node_id in OBSOLETE_GAMMA_CT_SUBGRAPH:
                deferred.pop(node_id, None)

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.92: obsolete guided gamma_ct decision/calculation/interpretation "
        "subgraph removed; gamma_ct=1.1 is a mandatory final-runtime constant."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if str(model.graph.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return model
    graph = transform_graph(model.graph)
    presentation = copy.deepcopy(model.presentation_policy)
    if isinstance(presentation, dict):
        table = presentation.get("node_presentation")
        if isinstance(table, dict):
            for node_id in OBSOLETE_GAMMA_CT_SUBGRAPH:
                table.pop(node_id, None)
        hidden = presentation.get("hidden_normative_nodes")
        if isinstance(hidden, list):
            presentation["hidden_normative_nodes"] = [
                node_id for node_id in hidden if node_id not in OBSOLETE_GAMMA_CT_SUBGRAPH
            ]
        deferred = presentation.get("deferred_nodes")
        if isinstance(deferred, dict):
            for node_id in OBSOLETE_GAMMA_CT_SUBGRAPH:
                deferred.pop(node_id, None)
    return FireDAGModel(
        graph,
        source_path=model.source_path,
        presentation_policy=presentation,
    )


def replay_without_obsolete_gamma_ct(
    source: GuidedCalculationSession,
    model: FireDAGModel,
    registry: ExecutionRegistry,
) -> GuidedCalculationSession:
    """Replay a retained session while dropping obsolete gamma_ct interactions."""
    migrated = GuidedCalculationSession(
        model,
        entry_node_id=source.entry_node_id,
        registry=registry,
    )
    for row in copy.deepcopy(source.interaction_history):
        expected = str(row.get("node_id") or "")
        if expected in OBSOLETE_GAMMA_CT_SUBGRAPH:
            continue
        if migrated.current_node_id != expected:
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except FireUIError:
            break
    return migrated


__all__ = [
    "BYPASS_SUCCESSOR_NODE_ID",
    "GRAPH_SUFFIX",
    "OBSOLETE_GAMMA_CT_CALC_NODE_ID",
    "OBSOLETE_GAMMA_CT_NODE_ID",
    "OBSOLETE_GAMMA_CT_RESULT_NODE_ID",
    "OBSOLETE_GAMMA_CT_SUBGRAPH",
    "build_model",
    "replay_without_obsolete_gamma_ct",
    "transform_graph",
]
