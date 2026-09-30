from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import _condition_value
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech7_v0105_section_class_route import (
    BINDER,
    CLASS_COPY,
    CLASS_DECISION,
    GRAPH_SUFFIX,
    _CLASS_EDGE_SUFFIX,
    _PRE_BINDER_EDGES,
    _RETURN_EDGE,
    build_model,
)

ROOT = Path(__file__).resolve().parents[1]


def test_v0105_primary_paths_split_contextually_on_mq():
    model = build_model(FireUI1Application.from_package_root(ROOT).model)
    edges = {edge["id"]: edge for edge in model.edges}
    assert GRAPH_SUFFIX in model.graph["graph_id"]
    for eid in _PRE_BINDER_EDGES:
        assert edges[eid]["to_node_id"] == BINDER
        assert edges[eid + _CLASS_EDGE_SUFFIX]["to_node_id"] == CLASS_DECISION
    assert edges[_RETURN_EDGE]["from_node_id"] == CLASS_COPY
    assert edges[_RETURN_EDGE]["to_node_id"] == BINDER
    assert edges[_RETURN_EDGE]["quantity_ids"] == ["sp16_section_class"]


def test_v0105_mq_requires_class_but_pure_axial_does_not():
    model = build_model(FireUI1Application.from_package_root(ROOT).model)
    edges = {edge["id"]: edge for edge in model.edges}
    # Compression predecessor is a control edge in the baseline and therefore
    # isolates the new contextual predicate cleanly.
    direct = edges["MECH7_E_COMPRESSION_TO_BINDER"]
    classify = edges["MECH7_E_COMPRESSION_TO_BINDER" + _CLASS_EDGE_SUFFIX]
    pure_n = {"ambient_M_x": 0.0, "ambient_M_y": 0.0, "ambient_Q_x": 0.0, "ambient_Q_y": 0.0}
    mq = {"ambient_M_x": 10.0, "ambient_M_y": 0.0, "ambient_Q_x": 5.0, "ambient_Q_y": 0.0}
    assert _condition_value(direct["condition"], pure_n) is True
    assert _condition_value(classify["condition"], pure_n) is False
    assert _condition_value(direct["condition"], mq) is False
    assert _condition_value(classify["condition"], mq) is True


def test_v0105_binder_routing_is_total_for_all_allowed_section_classes_when_mq_is_present():
    model = build_model(FireUI1Application.from_package_root(ROOT).model)
    outgoing = [e for e in model.outgoing[BINDER] if e["edge_type"] == "branch"]
    base_values = {"ambient_M_x": 10.0, "ambient_M_y": 0.0, "ambient_Q_x": 5.0, "ambient_Q_y": 0.0}
    for section_class in ("1", "2", "3", "other"):
        values = {**base_values, "sp16_section_class": section_class}
        states = [_condition_value(edge.get("condition"), values) for edge in outgoing]
        assert None not in states, (section_class, states)
        assert states.count(True) == 1, (section_class, states)


def test_v0105_transform_is_idempotent():
    first = build_model(FireUI1Application.from_package_root(ROOT).model)
    second = build_model(first)
    assert second.graph_sha256 == first.graph_sha256
