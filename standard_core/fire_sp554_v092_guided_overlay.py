"""v0.92 guided-SP554 overlay: remove the obsolete user gamma_ct decision.

Final SP 554.1311500.2026 uses the mandatory special-limit-state coefficient
``gamma_ct = 1.1`` in the migrated fire-mechanics runtime.  The historical
FIRE-UI DAG still contains an interactive boolean node
``SP554_D_GOST27751_GAMMA_CT``.  Asking that question is therefore both
redundant and unsafe: a user answer must not select or override the normative
coefficient.

This module leaves the frozen DAG file unchanged and transforms only the active
in-memory graph.  The obsolete node is removed structurally.  Its predecessors
are connected to its single unique successor.  If the historical node has more
than one distinct successor, the transform fails closed rather than inventing a
route.  Saved-session replay skips the obsolete interaction and never injects a
synthetic answer or stale decision value into the new ledger.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession, FireUIError

OBSOLETE_GAMMA_CT_NODE_ID = "SP554_D_GOST27751_GAMMA_CT"
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
    for edge in graph.get("edges", []):
        if not isinstance(edge, Mapping):
            continue
        for qid in edge.get("quantity_ids", []) or []:
            if isinstance(qid, str):
                refs.add(qid)
    return refs


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Remove the obsolete gamma_ct decision and create a deterministic bypass."""
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    nodes = [row for row in out.get("nodes", []) if isinstance(row, Mapping)]
    obsolete = next(
        (row for row in nodes if row.get("id") == OBSOLETE_GAMMA_CT_NODE_ID),
        None,
    )
    if obsolete is None:
        # A later frozen graph may already contain the remediation.  Mark the
        # active graph but do not mutate routing a second time.
        out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
        return out

    edges = [copy.deepcopy(row) for row in out.get("edges", [])]
    incoming = [row for row in edges if row.get("to_node_id") == OBSOLETE_GAMMA_CT_NODE_ID]
    outgoing = [row for row in edges if row.get("from_node_id") == OBSOLETE_GAMMA_CT_NODE_ID]
    successors = {str(row.get("to_node_id")) for row in outgoing if row.get("to_node_id")}

    if not incoming:
        raise FireUIError(
            f"v0.92 gamma_ct bypass: {OBSOLETE_GAMMA_CT_NODE_ID} has no predecessor"
        )
    if len(successors) != 1:
        raise FireUIError(
            "v0.92 gamma_ct bypass is ambiguous: obsolete decision must have "
            f"exactly one unique successor, found {sorted(successors)}"
        )
    successor = next(iter(successors))
    if successor == OBSOLETE_GAMMA_CT_NODE_ID:
        raise FireUIError("v0.92 gamma_ct bypass cannot target itself")

    obsolete_qids = _produced_quantity_ids(obsolete)
    retained_edges = [
        row
        for row in edges
        if row.get("from_node_id") != OBSOLETE_GAMMA_CT_NODE_ID
        and row.get("to_node_id") != OBSOLETE_GAMMA_CT_NODE_ID
    ]

    existing_pairs = {
        (str(row.get("from_node_id")), str(row.get("to_node_id")))
        for row in retained_edges
    }
    for index, source_edge in enumerate(incoming, start=1):
        predecessor = str(source_edge.get("from_node_id") or "")
        if not predecessor:
            raise FireUIError("v0.92 gamma_ct bypass found predecessor-less incoming edge")
        if (predecessor, successor) in existing_pairs:
            continue
        carried = [
            str(qid)
            for qid in (source_edge.get("quantity_ids") or [])
            if isinstance(qid, str) and qid not in obsolete_qids
        ]
        retained_edges.append(
            {
                "id": f"V092_GAMMA_CT_BYPASS_{index}_{predecessor}_TO_{successor}",
                "from_node_id": predecessor,
                "to_node_id": successor,
                "edge_type": source_edge.get("edge_type", "control"),
                "label": "v0.92: gamma_ct=1.1 normative; user decision bypassed",
                # Preserve only the predecessor-side routing condition.  The
                # obsolete node's own true/false condition is intentionally
                # discarded because it no longer has normative meaning.
                "condition": copy.deepcopy(source_edge.get("condition")),
                "quantity_ids": carried,
            }
        )
        existing_pairs.add((predecessor, successor))

    out["nodes"] = [
        copy.deepcopy(row)
        for row in out.get("nodes", [])
        if row.get("id") != OBSOLETE_GAMMA_CT_NODE_ID
    ]
    out["edges"] = retained_edges

    # Remove only quantities that were produced solely by the deleted decision
    # and are now true orphans.  Declarations still needed elsewhere are kept.
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
            table.pop(OBSOLETE_GAMMA_CT_NODE_ID, None)

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.92: obsolete SP554 user gamma_ct decision removed; final gamma_ct "
        "is a mandatory runtime constant equal to 1.1."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if str(model.graph.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return model
    graph = transform_graph(model.graph)
    presentation = copy.deepcopy(model.presentation_policy)
    table = presentation.get("node_presentation") if isinstance(presentation, dict) else None
    if isinstance(table, dict):
        table.pop(OBSOLETE_GAMMA_CT_NODE_ID, None)
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
    """Replay a retained session while dropping the obsolete user decision."""
    migrated = GuidedCalculationSession(
        model,
        entry_node_id=source.entry_node_id,
        registry=registry,
    )
    for row in copy.deepcopy(source.interaction_history):
        expected = str(row.get("node_id") or "")
        if expected == OBSOLETE_GAMMA_CT_NODE_ID:
            continue
        if migrated.current_node_id != expected:
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except FireUIError:
            break
    return migrated


__all__ = [
    "GRAPH_SUFFIX",
    "OBSOLETE_GAMMA_CT_NODE_ID",
    "build_model",
    "replay_without_obsolete_gamma_ct",
    "transform_graph",
]
