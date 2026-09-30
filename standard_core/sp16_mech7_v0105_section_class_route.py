"""v0.106 canonical MECH7 -> MECH8 section-class routing.

v0.105 added a contextual section-class gate for simultaneous bending + shear,
but its new predicates used the retired pre-v0.92 Mx/My + Qx/Qy vocabulary.
Production has already migrated to Mz/My bending, Mx torsion and Qz/Qy shear;
therefore Qx can be absent and the branch can remain unresolved after the
slenderness card.  v0.106 repairs both fresh graphs and retained v0.105 sessions.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel, FireUIError

OLD_GRAPH_SUFFIX = "_v0105_mech7_section_class_before_binder"
GRAPH_SUFFIX = "_v0106_mech7_canonical_section_class_before_binder"
BINDER = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"
CLASS_DECISION = "SP16_D_CLASS"
CLASS_COPY = "SP16_C_CLASS_COPY"
_PRE_BINDER_EDGES = {
    "MECH7_E_BRITTLE_TO_BINDER_N0",
    "MECH7_E_TENSION_TO_BINDER",
    "MECH7_E_COMPRESSION_TO_BINDER",
}
_CLASS_EDGE_SUFFIX = "_V0105_MQ_CLASS"
_RETURN_EDGE = "V0105_E_SECTION_CLASS_TO_MECH7_BINDER"

_M_PRESENT = {"type": "any_of", "conditions": [
    {"type": "comparison", "quantity_id": "ambient_M_z", "operator": "neq", "value": 0.0},
    {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "neq", "value": 0.0},
]}
_Q_PRESENT = {"type": "any_of", "conditions": [
    {"type": "comparison", "quantity_id": "ambient_Q_z", "operator": "neq", "value": 0.0},
    {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "neq", "value": 0.0},
]}
_MQ_PRESENT = {"type": "all_of", "conditions": [_M_PRESENT, _Q_PRESENT]}
_NO_MQ = {"type": "any_of", "conditions": [
    {"type": "all_of", "conditions": [
        {"type": "comparison", "quantity_id": "ambient_M_z", "operator": "eq", "value": 0.0},
        {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "eq", "value": 0.0},
    ]},
    {"type": "all_of", "conditions": [
        {"type": "comparison", "quantity_id": "ambient_Q_z", "operator": "eq", "value": 0.0},
        {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "eq", "value": 0.0},
    ]},
]}


def _and(original: Mapping[str, Any] | None, extra: Mapping[str, Any]) -> dict[str, Any]:
    if original is None:
        return copy.deepcopy(dict(extra))
    return {"type": "all_of", "conditions": [copy.deepcopy(dict(original)), copy.deepcopy(dict(extra))]}


def _original_from_v0105(condition: Any) -> Mapping[str, Any] | None:
    """Recover the pre-v0.105 condition from its deterministic all_of wrapper."""
    if not isinstance(condition, Mapping) or condition.get("type") != "all_of":
        return None
    rows = condition.get("conditions")
    if not isinstance(rows, list) or len(rows) != 2:
        return None
    first = rows[0]
    return copy.deepcopy(dict(first)) if isinstance(first, Mapping) else None


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    graph_id = str(out.get("graph_id") or "")
    if GRAPH_SUFFIX in graph_id:
        return out
    nodes = {str(row.get("id")): row for row in out.get("nodes", []) if isinstance(row, Mapping)}
    for required in (BINDER, CLASS_DECISION, CLASS_COPY):
        if required not in nodes:
            raise FireUIError(f"v0.106 section-class routing requires {required}")

    qids = {str(row.get("id")) for row in out.get("quantities", []) if isinstance(row, Mapping)}
    required_actions = {"ambient_M_z", "ambient_M_y", "ambient_Q_z", "ambient_Q_y"}
    if not required_actions <= qids:
        raise FireUIError(f"v0.106 requires canonical action quantities: {sorted(required_actions - qids)}")

    retained_v0105 = OLD_GRAPH_SUFFIX in graph_id
    edges = out.setdefault("edges", [])
    by_id = {str(e.get("id")): e for e in edges if isinstance(e, dict)}
    touched: set[str] = set()

    for eid in _PRE_BINDER_EDGES:
        edge = by_id.get(eid)
        if not isinstance(edge, dict) or edge.get("to_node_id") != BINDER:
            raise FireUIError(f"v0.106 expected {eid} to target {BINDER}")
        original = _original_from_v0105(edge.get("condition")) if retained_v0105 else copy.deepcopy(edge.get("condition"))
        if retained_v0105 and original is None:
            raise FireUIError(f"v0.106 cannot recover retained v0.105 predicate for {eid}")
        edge["condition"] = _and(original, _NO_MQ)
        edge["label"] = f"{eid} → binder (no simultaneous canonical M+Q)"

        class_id = eid + _CLASS_EDGE_SUFFIX
        class_edge = by_id.get(class_id)
        if class_edge is None:
            class_edge = {
                "id": class_id,
                "from_node_id": edge["from_node_id"],
                "to_node_id": CLASS_DECISION,
                "edge_type": "branch",
            }
            edges.append(class_edge)
            by_id[class_id] = class_edge
        class_edge.update({
            "from_node_id": edge["from_node_id"],
            "to_node_id": CLASS_DECISION,
            "edge_type": "branch",
            "label": "simultaneous canonical Mz/My + Qz/Qy → classify section before MECH8 routing",
            "condition": _and(original, _MQ_PRESENT),
            "quantity_ids": list(dict.fromkeys(list(edge.get("quantity_ids") or []) + [
                "ambient_M_z", "ambient_M_y", "ambient_Q_z", "ambient_Q_y"
            ])),
        })
        touched.add(eid)

    if touched != _PRE_BINDER_EDGES:
        raise FireUIError(f"v0.106 missing pre-binder edges: {sorted(_PRE_BINDER_EDGES - touched)}")

    if _RETURN_EDGE not in by_id:
        edges.append({
            "id": _RETURN_EDGE,
            "from_node_id": CLASS_COPY,
            "to_node_id": BINDER,
            "edge_type": "control",
            "label": "SP16 section class resolved → MECH7 primary binder",
            "condition": None,
            "quantity_ids": ["sp16_section_class"],
        })

    out["graph_id"] = graph_id + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.106 uses only canonical Mz/My bending and Qz/Qy shear for the contextual MECH8 class gate; "
        "retained v0.105 predicates are migrated without inference."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(transform_graph(model.graph), source_path=model.source_path, presentation_policy=model.presentation_policy)


__all__ = ["OLD_GRAPH_SUFFIX", "GRAPH_SUFFIX", "build_model", "transform_graph"]
