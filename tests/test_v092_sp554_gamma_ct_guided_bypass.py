from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.fire_sp554_runtime_v091 import GAMMA_CT
from standard_core.fire_sp554_v092_guided_overlay import (
    GRAPH_SUFFIX,
    OBSOLETE_GAMMA_CT_NODE_ID,
    build_model,
    replay_without_obsolete_gamma_ct,
    transform_graph,
)

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _quantity(qid: str, dtype: str = "boolean") -> dict:
    return {
        "id": qid,
        "symbol": None,
        "name_ru": qid,
        "data_type": dtype,
        "role": "input",
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {
            "primary_source_type": "USER_INPUT",
            "allowed_source_types": ["USER_INPUT"],
            "override_policy": "forbidden",
        },
    }


def _input(node_id: str, qid: str, dtype: str = "boolean") -> dict:
    return {
        "id": node_id,
        "node_type": "input",
        "owner_standard_id": "SP554_2026",
        "title": node_id,
        "normative_refs": [],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": True, "binding_role": "output"}],
        "applicability": None,
        "input_spec": {"input_method": "user_input", "required": True, "user_prompt": node_id},
        "notes": {},
    }


def _synthetic_legacy_model() -> FireDAGModel:
    graph = {
        "graph_id": "gamma_ct_legacy_test",
        "description": "test",
        "quantities": [
            _quantity("safe_before", "text"),
            _quantity("legacy_gamma_ct_answer", "boolean"),
            _quantity("ambient_N_force", "number"),
        ],
        "nodes": [
            _input("BEFORE", "safe_before", "text"),
            {
                **_input(OBSOLETE_GAMMA_CT_NODE_ID, "legacy_gamma_ct_answer"),
                "decision_quantity_id": "legacy_gamma_ct_answer",
            },
            _input("SP16_I_AMBIENT_LOADS", "ambient_N_force", "number"),
            {
                "id": "RESULT",
                "node_type": "result",
                "owner_standard_id": "SP554_2026",
                "title": "result",
                "normative_refs": [],
                "consumes": [],
                "produces": [],
                "applicability": None,
                "notes": {},
            },
        ],
        "edges": [
            {
                "id": "E1", "from_node_id": "BEFORE", "to_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
                "edge_type": "control", "label": "before", "condition": None,
                "quantity_ids": ["safe_before"],
            },
            {
                "id": "E2_FALSE", "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID, "to_node_id": "SP16_I_AMBIENT_LOADS",
                "edge_type": "control", "label": "false", "condition": {"operator": "eq", "quantity_id": "legacy_gamma_ct_answer", "value": False},
                "quantity_ids": ["legacy_gamma_ct_answer"],
            },
            {
                "id": "E2_TRUE", "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID, "to_node_id": "SP16_I_AMBIENT_LOADS",
                "edge_type": "control", "label": "true", "condition": {"operator": "eq", "quantity_id": "legacy_gamma_ct_answer", "value": True},
                "quantity_ids": ["legacy_gamma_ct_answer"],
            },
            {
                "id": "E3", "from_node_id": "SP16_I_AMBIENT_LOADS", "to_node_id": "RESULT",
                "edge_type": "control", "label": "result", "condition": None,
                "quantity_ids": ["ambient_N_force"],
            },
        ],
        "engine_contract": {},
    }
    return FireDAGModel(graph, presentation_policy={"entry_node_id": "BEFORE"})


def test_real_frozen_dag_gamma_ct_node_has_single_unique_successor_and_is_removed():
    with DAG.open("r", encoding="utf-8") as fh:
        source = json.load(fh)

    source_nodes = {row["id"] for row in source["nodes"]}
    assert OBSOLETE_GAMMA_CT_NODE_ID in source_nodes
    outgoing = [
        row for row in source["edges"]
        if row.get("from_node_id") == OBSOLETE_GAMMA_CT_NODE_ID
    ]
    successors = {row["to_node_id"] for row in outgoing}
    assert len(successors) == 1, successors

    transformed = transform_graph(source)
    assert transformed["graph_id"].endswith(GRAPH_SUFFIX)
    assert OBSOLETE_GAMMA_CT_NODE_ID not in {row["id"] for row in transformed["nodes"]}
    assert all(
        row.get("from_node_id") != OBSOLETE_GAMMA_CT_NODE_ID
        and row.get("to_node_id") != OBSOLETE_GAMMA_CT_NODE_ID
        for row in transformed["edges"]
    )

    successor = next(iter(successors))
    predecessors = {
        row["from_node_id"] for row in source["edges"]
        if row.get("to_node_id") == OBSOLETE_GAMMA_CT_NODE_ID
    }
    for predecessor in predecessors:
        assert any(
            row.get("from_node_id") == predecessor and row.get("to_node_id") == successor
            for row in transformed["edges"]
        )


def test_bypass_fails_closed_when_obsolete_choice_has_multiple_distinct_successors():
    graph = _synthetic_legacy_model().graph
    graph["nodes"].insert(-1, _input("OTHER", "ambient_N_force", "number"))
    graph["edges"].append(
        {
            "id": "AMBIGUOUS", "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID, "to_node_id": "OTHER",
            "edge_type": "control", "label": "ambiguous", "condition": None, "quantity_ids": [],
        }
    )
    with pytest.raises(Exception, match="exactly one unique successor"):
        transform_graph(graph)


def test_retained_session_skips_historical_boolean_and_keeps_no_stale_gamma_answer():
    old_model = _synthetic_legacy_model()
    old = GuidedCalculationSession(old_model, registry=ExecutionRegistry())
    old.submit("kept")
    assert old.current_node_id == OBSOLETE_GAMMA_CT_NODE_ID
    old.submit(False)
    assert old.current_node_id == "SP16_I_AMBIENT_LOADS"
    old.submit(123.0)

    new_model = build_model(old_model)
    migrated = replay_without_obsolete_gamma_ct(old, new_model, ExecutionRegistry())
    values = migrated.plain_values()

    assert values["safe_before"] == "kept"
    assert values["ambient_N_force"] == pytest.approx(123.0)
    assert "legacy_gamma_ct_answer" not in values
    assert OBSOLETE_GAMMA_CT_NODE_ID not in [row["node_id"] for row in migrated.interaction_history]


def test_fresh_session_routes_from_predecessor_directly_to_loads_without_gamma_question():
    model = build_model(_synthetic_legacy_model())
    session = GuidedCalculationSession(model, registry=ExecutionRegistry())
    session.submit("kept")
    assert session.current_node_id == "SP16_I_AMBIENT_LOADS"
    assert OBSOLETE_GAMMA_CT_NODE_ID not in model.nodes


def test_gamma_ct_is_runtime_constant_not_guided_answer():
    assert GAMMA_CT == pytest.approx(1.1)
