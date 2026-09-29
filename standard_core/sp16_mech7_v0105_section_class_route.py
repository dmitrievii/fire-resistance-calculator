"""v0.105 close the MECH7 -> MECH8 section-class routing dependency.

The frozen graph routes the MECH7 primary evidence binder into three MECH8
branches whose predicates require ``sp16_section_class``.  In the guided ambient
route that class was never scheduled before the binder, so all three predicates
became unresolved and FIRE-UI stopped at
``BLOCKED_UNRESOLVED_BRANCH_CONDITION:SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER``.

This overlay does not infer a class.  It routes every completed MECH7
axial/slenderness path through the existing SP16 §4.2.7 class decision and its
existing identity producer before returning to the binder.  Thus the branch
predicate is fully authored before MECH8 routing is evaluated.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel, FireUIError

GRAPH_SUFFIX = "_v0105_mech7_section_class_before_binder"
BINDER = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"
CLASS_DECISION = "SP16_D_CLASS"
CLASS_COPY = "SP16_C_CLASS_COPY"
_PRE_BINDER_EDGES = {
    "MECH7_E_BRITTLE_TO_BINDER_N0",
    "MECH7_E_TENSION_TO_BINDER",
    "MECH7_E_COMPRESSION_TO_BINDER",
}
_RETURN_EDGE = "V0105_E_SECTION_CLASS_TO_MECH7_BINDER"


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    nodes = {str(row.get("id")): row for row in out.get("nodes", []) if isinstance(row, Mapping)}
    for required in (BINDER, CLASS_DECISION, CLASS_COPY):
        if required not in nodes:
            raise FireUIError(f"v0.105 section-class routing requires {required}")

    touched: set[str] = set()
    for edge in out.get("edges", []):
        if not isinstance(edge, dict):
            continue
        eid = str(edge.get("id") or "")
        if eid in _PRE_BINDER_EDGES:
            if edge.get("to_node_id") != BINDER:
                raise FireUIError(f"v0.105 expected {eid} to target {BINDER}")
            edge["to_node_id"] = CLASS_DECISION
            edge["label"] = str(edge.get("label") or eid) + " → classify section before MECH8 routing"
            touched.add(eid)
    if touched != _PRE_BINDER_EDGES:
        raise FireUIError(f"v0.105 missing pre-binder edges: {sorted(_PRE_BINDER_EDGES - touched)}")

    existing = {str(edge.get("id")) for edge in out.get("edges", []) if isinstance(edge, Mapping)}
    if _RETURN_EDGE not in existing:
        out.setdefault("edges", []).append({
            "id": _RETURN_EDGE,
            "from_node_id": CLASS_COPY,
            "to_node_id": BINDER,
            "edge_type": "control",
            "label": "SP16 §4.2.7 section class resolved → MECH7 primary binder",
            "condition": None,
            "quantity_ids": ["sp16_section_class"],
        })

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.105 resolves SP16 section class before MECH7->MECH8 branch selection; "
        "no class is inferred or defaulted."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=model.presentation_policy,
    )


__all__ = ["GRAPH_SUFFIX", "build_model", "transform_graph"]
