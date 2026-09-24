from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.fire_sp554_runtime_v091 import GAMMA_CT
from standard_core.fire_sp554_v092_guided_overlay import (
    BYPASS_SUCCESSOR_NODE_ID,
    GRAPH_SUFFIX,
    OBSOLETE_GAMMA_CT_CALC_NODE_ID,
    OBSOLETE_GAMMA_CT_NODE_ID,
    OBSOLETE_GAMMA_CT_RESULT_NODE_ID,
    OBSOLETE_GAMMA_CT_SUBGRAPH,
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


def _decision(node_id: str, qid: str) -> dict:
    node = _input(node_id, qid, "boolean")
    node.update(
        {
            "node_type": "decision",
            "question": node_id,
            "decision_quantity_id": qid,
            "options": [
                {"value": False, "label": "Нет", "description": "legacy false"},
                {"value": True, "label": "Да", "description": "legacy true"},
            ],
        }
    )
    return node


def _calculation(node_id: str) -> dict:
    return {
        "id": node_id,
        "node_type": "calculation",
        "owner_standard_id": "SP554_2026",
        "title": node_id,
        "normative_refs": [],
        "consumes": [],
        "produces": [],
        "applicability": None,
        "notes": {},
    }


def _result(node_id: str) -> dict:
    return {
        "id": node_id,
        "node_type": "result",
        "owner_standard_id": "SP554_2026",
        "title": node_id,
        "normative_refs": [],
        "consumes": [],
        "produces": [],
        "applicability": None,
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
            _decision(OBSOLETE_GAMMA_CT_NODE_ID, "legacy_gamma_ct_answer"),
            _calculation(OBSOLETE_GAMMA_CT_CALC_NODE_ID),
            _result(OBSOLETE_GAMMA_CT_RESULT_NODE_ID),
            _input(BYPASS_SUCCESSOR_NODE_ID, "ambient_N_force", "number"),
            _result("RESULT"),
        ],
        "edges": [
            {
                "id": "E1",
                "from_node_id": "BEFORE",
                "to_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
                "edge_type": "control",
                "label": "before",
                "condition": None,
                "quantity_ids": ["safe_before"],
            },
            {
                "id": "E2_FALSE",
                "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
                "to_node_id": BYPASS_SUCCESSOR_NODE_ID,
                "edge_type": "branch",
                "label": "false",
                "condition": {
                    "type": "comparison",
                    "quantity_id": "legacy_gamma_ct_answer",
                    "operator": "eq",
                    "value": False,
                },
                "quantity_ids": [],
            },
            {
                "id": "E2_TRUE",
                "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
                "to_node_id": OBSOLETE_GAMMA_CT_CALC_NODE_ID,
                "edge_type": "branch",
                "label": "true",
                "condition": {
                    "type": "comparison",
                    "quantity_id": "legacy_gamma_ct_answer",
                    "operator": "eq",
                    "value": True,
                },
                "quantity_ids": [],
            },
            {
                "id": "E2_DIAG_STATE",
                "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
                "to_node_id": OBSOLETE_GAMMA_CT_RESULT_NODE_ID,
                "edge_type": "data",
                "label": "legacy state",
                "condition": None,
                "quantity_ids": ["legacy_gamma_ct_answer"],
            },
            {
                "id": "E2_DIAG_VALUE",
                "from_node_id": OBSOLETE_GAMMA_CT_CALC_NODE_ID,
                "to_node_id": OBSOLETE_GAMMA_CT_RESULT_NODE_ID,
                "edge_type": "data",
                "label": "legacy gamma",
                "condition": None,
                "quantity_ids": [],
            },
            {
                "id": "E3",
                "from_node_id": BYPASS_SUCCESSOR_NODE_ID,
                "to_node_id": "RESULT",
                "edge_type": "control",
                "label": "result",
                "condition": None,
                "quantity_ids": ["ambient_N_force"],
            },
        ],
        "engine_contract": {},
    }
    return FireDAGModel(graph, presentation_policy={"entry_node_id": "BEFORE"})


def test_real_frozen_dag_gamma_ct_diagnostic_subgraph_is_removed_and_bypassed():
    with DAG.open("r", encoding="utf-8") as fh:
        source = json.load(fh)

    source_nodes = {row["id"] for row in source["nodes"]}
    assert OBSOLETE_GAMMA_CT_SUBGRAPH.issubset(source_nodes)
    outgoing = [
        row
        for row in source["edges"]
        if row.get("from_node_id") == OBSOLETE_GAMMA_CT_NODE_ID
    ]
    successors = {row["to_node_id"] for row in outgoing}
    assert successors == {
        BYPASS_SUCCESSOR_NODE_ID,
        OBSOLETE_GAMMA_CT_CALC_NODE_ID,
        OBSOLETE_GAMMA_CT_RESULT_NODE_ID,
    }

    transformed = transform_graph(source)
    assert transformed["graph_id"].endswith(GRAPH_SUFFIX)
    transformed_nodes = {row["id"] for row in transformed["nodes"]}
    assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(transformed_nodes)
    assert all(
        row.get("from_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
        and row.get("to_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
        for row in transformed["edges"]
    )

    predecessors = {
        row["from_node_id"]
        for row in source["edges"]
        if row.get("to_node_id") == OBSOLETE_GAMMA_CT_NODE_ID
        and row.get("from_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH
    }
    assert predecessors
    for predecessor in predecessors:
        assert any(
            row.get("from_node_id") == predecessor
            and row.get("to_node_id") == BYPASS_SUCCESSOR_NODE_ID
            for row in transformed["edges"]
        )

    # The obsolete user boolean becomes an orphan and must disappear from the
    # active quantity catalogue rather than survive as a hidden answer.
    active_qids = {row["id"] for row in transformed["quantities"]}
    assert "gost27751_special_check" not in active_qids


def test_bypass_target_is_explicit_even_when_legacy_node_has_multiple_successors():
    graph = _synthetic_legacy_model().graph
    graph["nodes"].insert(-1, _input("OTHER", "ambient_N_force", "number"))
    graph["edges"].append(
        {
            "id": "EXTRA_LEGACY_EXIT",
            "from_node_id": OBSOLETE_GAMMA_CT_NODE_ID,
            "to_node_id": "OTHER",
            "edge_type": "branch",
            "label": "historical extra exit",
            "condition": None,
            "quantity_ids": [],
        }
    )

    transformed = transform_graph(graph)
    assert OBSOLETE_GAMMA_CT_NODE_ID not in {row["id"] for row in transformed["nodes"]}
    assert any(
        row.get("from_node_id") == "BEFORE"
        and row.get("to_node_id") == BYPASS_SUCCESSOR_NODE_ID
        for row in transformed["edges"]
    )
    assert not any(
        row.get("from_node_id") == "BEFORE" and row.get("to_node_id") == "OTHER"
        for row in transformed["edges"]
    )


def test_bypass_fails_closed_when_canonical_continuation_is_missing():
    graph = _synthetic_legacy_model().graph
    graph["nodes"] = [row for row in graph["nodes"] if row["id"] != BYPASS_SUCCESSOR_NODE_ID]
    graph["edges"] = [
        row
        for row in graph["edges"]
        if row.get("from_node_id") != BYPASS_SUCCESSOR_NODE_ID
        and row.get("to_node_id") != BYPASS_SUCCESSOR_NODE_ID
    ]
    with pytest.raises(Exception, match="canonical continuation node"):
        transform_graph(graph)


def test_retained_session_skips_historical_boolean_and_keeps_no_stale_gamma_answer():
    old_model = _synthetic_legacy_model()
    old = GuidedCalculationSession(old_model, registry=ExecutionRegistry())
    old.submit("kept")
    assert old.current_node_id == OBSOLETE_GAMMA_CT_NODE_ID
    old.submit(False)
    assert old.current_node_id == BYPASS_SUCCESSOR_NODE_ID
    old.submit(123.0)

    new_model = build_model(old_model)
    migrated = replay_without_obsolete_gamma_ct(old, new_model, ExecutionRegistry())
    values = migrated.plain_values()

    assert values["safe_before"] == "kept"
    assert values["ambient_N_force"] == pytest.approx(123.0)
    assert "legacy_gamma_ct_answer" not in values
    assert all(
        row["node_id"] not in OBSOLETE_GAMMA_CT_SUBGRAPH
        for row in migrated.interaction_history
    )


def test_fresh_session_routes_from_predecessor_directly_to_loads_without_gamma_question():
    model = build_model(_synthetic_legacy_model())
    session = GuidedCalculationSession(model, registry=ExecutionRegistry())
    session.submit("kept")
    assert session.current_node_id == BYPASS_SUCCESSOR_NODE_ID
    assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(model.nodes)


def test_gamma_ct_is_runtime_constant_not_guided_answer():
    assert GAMMA_CT == pytest.approx(1.1)
