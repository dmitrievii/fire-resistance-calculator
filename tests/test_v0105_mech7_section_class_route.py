from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import _condition_value
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech_v092_canonical_actions import build_model as canonical_model
from standard_core.sp16_mech7_v0105_section_class_route import (
    BINDER,
    CLASS_COPY,
    CLASS_DECISION,
    GRAPH_SUFFIX,
    OLD_GRAPH_SUFFIX,
    _CLASS_EDGE_SUFFIX,
    _PRE_BINDER_EDGES,
    _RETURN_EDGE,
    build_model,
)

ROOT = Path(__file__).resolve().parents[1]


def _base():
    return canonical_model(FireUI1Application.from_package_root(ROOT).model)


def test_v0106_primary_paths_split_contextually_on_canonical_mq():
    model = build_model(_base())
    edges = {edge["id"]: edge for edge in model.edges}
    assert GRAPH_SUFFIX in model.graph["graph_id"]
    for eid in _PRE_BINDER_EDGES:
        assert edges[eid]["to_node_id"] == BINDER
        assert edges[eid + _CLASS_EDGE_SUFFIX]["to_node_id"] == CLASS_DECISION
    assert edges[_RETURN_EDGE]["from_node_id"] == CLASS_COPY
    assert edges[_RETURN_EDGE]["to_node_id"] == BINDER


def test_v0106_mq_requires_class_but_pure_axial_does_not_and_never_uses_qx():
    model = build_model(_base())
    edges = {edge["id"]: edge for edge in model.edges}
    direct = edges["MECH7_E_COMPRESSION_TO_BINDER"]
    classify = edges["MECH7_E_COMPRESSION_TO_BINDER" + _CLASS_EDGE_SUFFIX]
    pure_n = {"ambient_M_z": 0.0, "ambient_M_y": 0.0, "ambient_Q_z": 0.0, "ambient_Q_y": 0.0}
    mq = {"ambient_M_z": 10.0, "ambient_M_y": 0.0, "ambient_Q_z": 5.0, "ambient_Q_y": 0.0}
    assert _condition_value(direct["condition"], pure_n) is True
    assert _condition_value(classify["condition"], pure_n) is False
    assert _condition_value(direct["condition"], mq) is False
    assert _condition_value(classify["condition"], mq) is True
    assert "ambient_Q_x" not in repr(direct["condition"])
    assert "ambient_Q_x" not in repr(classify["condition"])
    assert "ambient_M_x" not in repr(classify["condition"])


def test_v0106_binder_routing_is_total_for_all_allowed_section_classes_when_mq_is_present():
    model = build_model(_base())
    outgoing = [e for e in model.outgoing[BINDER] if e["edge_type"] == "branch"]
    base_values = {"ambient_M_z": 10.0, "ambient_M_y": 0.0, "ambient_Q_z": 5.0, "ambient_Q_y": 0.0}
    for section_class in ("1", "2", "3", "other"):
        values = {**base_values, "sp16_section_class": section_class}
        states = [_condition_value(edge.get("condition"), values) for edge in outgoing]
        assert None not in states, (section_class, states)
        assert states.count(True) == 1, (section_class, states)


def test_v0106_retained_v0105_graph_is_migrated_not_double_wrapped():
    # Build a synthetic retained v0.105 shape by applying the historical wrapper
    # structure to the canonical base, then mark its graph id accordingly.
    import copy
    retained = copy.deepcopy(_base().graph)
    by_id = {e["id"]: e for e in retained["edges"]}
    old_no_mq = {"type": "any_of", "conditions": [
        {"type": "all_of", "conditions": [
            {"type": "comparison", "quantity_id": "ambient_M_x", "operator": "eq", "value": 0.0},
            {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "eq", "value": 0.0}]},
        {"type": "all_of", "conditions": [
            {"type": "comparison", "quantity_id": "ambient_Q_x", "operator": "eq", "value": 0.0},
            {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "eq", "value": 0.0}]},
    ]}
    old_mq = {"type": "all_of", "conditions": [
        {"type": "any_of", "conditions": [
            {"type": "comparison", "quantity_id": "ambient_M_x", "operator": "neq", "value": 0.0},
            {"type": "comparison", "quantity_id": "ambient_M_y", "operator": "neq", "value": 0.0}]},
        {"type": "any_of", "conditions": [
            {"type": "comparison", "quantity_id": "ambient_Q_x", "operator": "neq", "value": 0.0},
            {"type": "comparison", "quantity_id": "ambient_Q_y", "operator": "neq", "value": 0.0}]},
    ]}
    additions = []
    for eid in _PRE_BINDER_EDGES:
        edge = by_id[eid]
        original = copy.deepcopy(edge.get("condition"))
        edge["condition"] = {"type": "all_of", "conditions": [original, old_no_mq]} if original else old_no_mq
        additions.append({"id": eid + _CLASS_EDGE_SUFFIX, "from_node_id": edge["from_node_id"], "to_node_id": CLASS_DECISION, "edge_type": "branch", "condition": {"type": "all_of", "conditions": [original, old_mq]} if original else old_mq, "quantity_ids": []})
    retained["edges"].extend(additions)
    retained["edges"].append({"id": _RETURN_EDGE, "from_node_id": CLASS_COPY, "to_node_id": BINDER, "edge_type": "control", "condition": None, "quantity_ids": ["sp16_section_class"]})
    retained["graph_id"] += OLD_GRAPH_SUFFIX
    from standard_core.fire_ui0 import FireDAGModel
    migrated = build_model(FireDAGModel(retained, source_path=_base().source_path, presentation_policy=_base().presentation_policy))
    assert GRAPH_SUFFIX in migrated.graph["graph_id"]
    assert "ambient_Q_x" not in repr([e["condition"] for e in migrated.edges if e["id"] in _PRE_BINDER_EDGES or e["id"].endswith(_CLASS_EDGE_SUFFIX)])


def test_v0106_transform_is_idempotent():
    first = build_model(_base())
    second = build_model(first)
    assert second.graph_sha256 == first.graph_sha256
