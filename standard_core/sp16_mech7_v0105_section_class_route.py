"""v0.106 close the MECH7 -> MECH8 section-class routing dependency.

The production graph reaching this overlay has already passed the v0.92
canonical-action transform.  Therefore M+Q detection MUST use the canonical
principal-axis vocabulary Mz/My and Qz/Qy.  v0.105 accidentally retained the
pre-v0.92 Mx/My + Qx/Qy vocabulary in its new predicates; Qx no longer exists in
production, so a legitimate M+Q route could remain unresolved after the
slenderness card.

The repair is contextual: simultaneous bending + shear routes through the
existing SP16 section-class decision; other routes remain direct. No class is
inferred or defaulted.
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
_CLASS_EDGE_SUFFIX = "_V0105_MQ_CLASS"
_RETURN_EDGE = "V0105_E_SECTION_CLASS_TO_MECH7_BINDER"

# Canonical v0.92 action axes at the point this overlay is installed:
# Mz/My = bending, Mx = torsion; Qz/Qy = shear.  Torsion must not be used as a
# proxy for bending and the retired Qx quantity must never reappear.
_M_PRESENT = {
    "type": "any_of",
    "conditions": [
        {"type": "comparison", "quantity_id": "ambient_M_z", "operator": "neq", "value": 0.0},
        {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "neq", "value": 0.0},
    ],
}
_Q_PRESENT = {
    "type": "any_of",
    "conditions": [
        {"type": "comparison", "quantity_id": "ambient_Q_z", "operator": "neq", "value": 0.0},
        {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "neq", "value": 0.0},
    ],
}
_MQ_PRESENT = {"type": "all_of", "conditions": [_M_PRESENT, _Q_PRESENT]}
_NO_MQ = {
    "type": "any_of",
    "conditions": [
        {
            "type": "all_of",
            "conditions": [
                {"type": "comparison", "quantity_id": "ambient_M_z", "operator": "eq", "value": 0.0},
                {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "eq", "value": 0.0},
            ],
        },
        {
            "type": "all_of",
            "conditions": [
                {"type": "comparison", "quantity_id": "ambient_Q_z", "operator": "eq", "value": 0.0},
                {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "eq", "value": 0.0},
            ],
        },
    ],
}


def _and(original: Mapping[str, Any] | None, extra: Mapping[str, Any]) -> dict[str, Any]:
    if original is None:
        return copy.deepcopy(dict(extra))
    return {"type": "all_of", "conditions": [copy.deepcopy(dict(original)), copy.deepcopy(dict(extra))]}


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    nodes = {str(row.get("id")): row for row in out.get("nodes", []) if isinstance(row, Mapping)}
    for required in (BINDER, CLASS_DECISION, CLASS_COPY):
        if required not in nodes:
            raise FireUIError(f"v0.106 section-class routing requires {required}")

    # Fail closed if this overlay is accidentally applied before canonical-action
    # migration: production must not silently recreate legacy Qx/T semantics.
    qids = {str(row.get("id")) for row in out.get("quantities", []) if isinstance(row, Mapping)}
    required_actions = {"ambient_M_z", "ambient_M_y", "ambient_Q_z", "ambient_Q_y"}
    if not required_actions <= qids:
        raise FireUIError(f"v0.106 requires canonical action quantities: {sorted(required_actions - qids)}")

    touched: set[str] = set()
    class_edges: list[dict[str, Any]] = []
    for edge in out.get("edges", []):
        if not isinstance(edge, dict):
            continue
        eid = str(edge.get("id") or "")
        if eid not in _PRE_BINDER_EDGES:
            continue
        if edge.get("to_node_id") != BINDER:
            raise FireUIError(f"v0.106 expected {eid} to target {BINDER}")
        original_condition = copy.deepcopy(edge.get("condition"))
        edge["condition"] = _and(original_condition, _NO_MQ)
        edge["label"] = str(edge.get("label") or eid) + " → binder (no simultaneous M+Q)"
        class_edges.append({
            "id": eid + _CLASS_EDGE_SUFFIX,
            "from_node_id": edge["from_node_id"],
            "to_node_id": CLASS_DECISION,
            "edge_type": "branch",
            "label": "simultaneous M+Q → classify section before MECH8 routing",
            "condition": _and(original_condition, _MQ_PRESENT),
            "quantity_ids": list(dict.fromkeys(list(edge.get("quantity_ids") or []) + [
                "ambient_M_z", "ambient_M_y", "ambient_Q_z", "ambient_Q_y"
            ])),
        })
        touched.add(eid)
    if touched != _PRE_BINDER_EDGES:
        raise FireUIError(f"v0.106 missing pre-binder edges: {sorted(_PRE_BINDER_EDGES - touched)}")
    out.setdefault("edges", []).extend(class_edges)

    existing = {str(edge.get("id")) for edge in out.get("edges", []) if isinstance(edge, Mapping)}
    if _RETURN_EDGE not in existing:
        out["edges"].append({
            "id": _RETURN_EDGE,
            "from_node_id": CLASS_COPY,
            "to_node_id": BINDER,
            "edge_type": "control",
            "label": "SP16 section class resolved → MECH7 primary binder",
            "condition": None,
            "quantity_ids": ["sp16_section_class"],
        })

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.106 resolves SP16 section class before class-dependent canonical Mz/My + Qz/Qy MECH8 routing; "
        "class-independent routes remain direct and no class is inferred or defaulted."
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
