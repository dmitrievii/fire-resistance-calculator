from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech7_v0105_section_class_route import (
    BINDER,
    CLASS_COPY,
    CLASS_DECISION,
    GRAPH_SUFFIX,
    _PRE_BINDER_EDGES,
    _RETURN_EDGE,
    build_model,
)

ROOT = Path(__file__).resolve().parents[1]


def test_v0105_all_primary_mech7_paths_resolve_section_class_before_binder():
    base = FireUI1Application.from_package_root(ROOT).model
    model = build_model(base)
    assert GRAPH_SUFFIX in model.graph["graph_id"]

    edges = {edge["id"]: edge for edge in model.edges}
    for eid in _PRE_BINDER_EDGES:
        assert edges[eid]["to_node_id"] == CLASS_DECISION
    assert edges[_RETURN_EDGE]["from_node_id"] == CLASS_COPY
    assert edges[_RETURN_EDGE]["to_node_id"] == BINDER
    assert edges[_RETURN_EDGE]["quantity_ids"] == ["sp16_section_class"]


def test_v0105_binder_mech8_predicates_have_section_class_produced_upstream():
    model = build_model(FireUI1Application.from_package_root(ROOT).model)
    binder_out = [e for e in model.outgoing[BINDER] if e["edge_type"] in {"branch", "control", "handoff"}]
    assert binder_out
    # The historical defect was that these predicates consumed sp16_section_class
    # without any guided path producing it before the binder.
    assert any("sp16_section_class" in e.get("quantity_ids", []) for e in binder_out)
    incoming = model.incoming[BINDER]
    assert any(e["id"] == _RETURN_EDGE and "sp16_section_class" in e.get("quantity_ids", []) for e in incoming)


def test_v0105_no_direct_mech7_predecessor_can_reach_binder_without_classification():
    model = build_model(FireUI1Application.from_package_root(ROOT).model)
    direct = {
        e["id"]
        for e in model.incoming[BINDER]
        if e["id"] in _PRE_BINDER_EDGES
    }
    assert direct == set()


def test_v0105_transform_is_idempotent():
    first = build_model(FireUI1Application.from_package_root(ROOT).model)
    second = build_model(first)
    assert second.graph_sha256 == first.graph_sha256
