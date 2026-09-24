from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.sp16_mech_v092_canonical_actions import (
    GRAPH_SUFFIX,
    build_model,
    canonical_action_contract,
    install_registry_remediation,
    replay_prefix_without_axis_alias,
    transform_graph,
)


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _quantity(qid: str, dtype: str = "number") -> dict:
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


def _input(node_id: str, qids: list[str]) -> dict:
    return {
        "id": node_id,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": node_id,
        "normative_refs": [],
        "consumes": [],
        "produces": [
            {"quantity_id": qid, "required": True, "binding_role": "output"}
            for qid in qids
        ],
        "applicability": None,
        "input_spec": {"input_method": "user_input", "required": True, "user_prompt": node_id},
        "notes": {},
    }


def _minimal_legacy_model() -> FireDAGModel:
    graph = {
        "graph_id": "legacy_axis_test",
        "description": "test",
        "quantities": [
            _quantity("safe_text", "text"),
            _quantity("ambient_M_x"),
            _quantity("ambient_T_torsion"),
        ],
        "nodes": [
            _input("SAFE", ["safe_text"]),
            _input("LOADS", ["ambient_M_x", "ambient_T_torsion"]),
            {
                "id": "RESULT",
                "node_type": "result",
                "owner_standard_id": "SP16_2017",
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
                "id": "E1", "from_node_id": "SAFE", "to_node_id": "LOADS",
                "edge_type": "control", "label": "E1", "condition": None,
                "quantity_ids": ["safe_text"],
            },
            {
                "id": "E2", "from_node_id": "LOADS", "to_node_id": "RESULT",
                "edge_type": "control", "label": "E2", "condition": None,
                "quantity_ids": ["ambient_M_x", "ambient_T_torsion"],
            },
        ],
        "engine_contract": {},
    }
    return FireDAGModel(graph, presentation_policy={"entry_node_id": "SAFE"})


def test_v092_real_frozen_dag_action_ids_transform_without_collision():
    with DAG.open("r", encoding="utf-8") as fh:
        source = json.load(fh)
    transformed = transform_graph(source)

    assert transformed["graph_id"].endswith(GRAPH_SUFFIX)
    ids = [row["id"] for row in transformed["quantities"]]
    assert len(ids) == len(set(ids))

    assert "ambient_M_z" in ids
    assert "ambient_M_y" in ids
    assert "ambient_M_x" in ids
    assert "ambient_Q_z" in ids
    assert "ambient_Q_y" in ids
    assert "ambient_T_torsion" not in ids
    assert "ambient_Q_x" not in ids

    assert "M_z" in ids
    assert "M_y" in ids
    assert "M_x" in ids
    assert "Q_z" in ids
    assert "Q_y" in ids
    assert "T_torsion" not in ids
    assert "Q_x" not in ids

    rows = {row["id"]: row for row in transformed["quantities"]}
    assert rows["ambient_M_z"]["symbol"] == "M_z"
    assert "сильной оси z" in rows["ambient_M_z"]["name_ru"]
    assert rows["ambient_M_x"]["symbol"] == "M_x"
    assert "Крутящий" in rows["ambient_M_x"]["name_ru"]


def test_v092_registry_adapter_is_directional_canonical_to_legacy_local_names():
    registry = ExecutionRegistry()
    seen = {}

    def legacy_executor(values, node):
        seen.update(values)
        consumed = [row["quantity_id"] for row in node["consumes"]]
        assert consumed == ["ambient_M_x", "ambient_T_torsion"]
        return {
            "mechanical_action_state": {
                "schema": "sp16_mech2_ambient_mechanical_action_state_v1",
                "axis_convention": {
                    "member_axis": "s",
                    "section_principal_axes": ["x-x", "y-y"],
                },
                "actions": {
                    "N": 0.0,
                    "Mx": values["ambient_M_x"],
                    "My": 5.0,
                    "Qx": 7.0,
                    "Qy": 8.0,
                    "T": values["ambient_T_torsion"],
                    "B": 0.0,
                },
            }
        }

    registry.register("NODE", legacy_executor)
    install_registry_remediation(registry)
    wrapped = registry.get("NODE")
    node = {
        "id": "NODE",
        "consumes": [
            {"quantity_id": "ambient_M_z"},
            {"quantity_id": "ambient_M_x"},
        ],
        "produces": [{"quantity_id": "mechanical_action_state"}],
    }
    out = wrapped(
        {
            "ambient_M_z": 120.0,
            "ambient_M_x": 30.0,
        },
        node,
    )

    # New Mz is fed to the historical local bending variable Mx; new Mx is fed
    # only to the historical local torsion variable T.  No old user data is
    # being migrated here.
    assert seen["ambient_M_x"] == pytest.approx(120.0)
    assert seen["ambient_T_torsion"] == pytest.approx(30.0)

    state = out["mechanical_action_state"]
    assert state["schema"] == "sp16_mech2_ambient_mechanical_action_state_v092_canonical_axes"
    assert state["axis_convention"]["member_axis"] == "x"
    assert state["axis_convention"]["section_principal_axes"] == ["z-z", "y-y"]
    assert state["actions"] == {
        "N": 0.0,
        "Mz": 120.0,
        "My": 5.0,
        "Qz": 7.0,
        "Qy": 8.0,
        "Mx": 30.0,
        "B": 0.0,
    }


def test_v092_old_session_stops_before_changed_load_input_instead_of_replaying_mx():
    old_model = _minimal_legacy_model()
    old_session = GuidedCalculationSession(old_model, registry=ExecutionRegistry())
    old_session.submit("kept")
    assert old_session.current_node_id == "LOADS"
    old_session.submit({"ambient_M_x": 90.0, "ambient_T_torsion": 15.0})

    new_model = build_model(old_model)
    migrated = replay_prefix_without_axis_alias(old_session, new_model, ExecutionRegistry())

    assert migrated.current_node_id == "LOADS"
    plain = migrated.plain_values()
    assert plain["safe_text"] == "kept"
    assert "ambient_M_z" not in plain
    assert "ambient_M_x" not in plain
    assert "ambient_T_torsion" not in plain
    assert len(migrated.interaction_history) == 1


def test_v092_contract_explicitly_forbids_both_legacy_semantic_replays():
    contract = canonical_action_contract()
    assert contract["strong_axis_bending"] == "M_z"
    assert contract["weak_axis_bending"] == "M_y"
    assert contract["torsion"] == "M_x"
    assert contract["shear_components"] == ["Q_z", "Q_y"]
    assert contract["legacy_old_Mx_to_new_Mz_replay_allowed"] is False
    assert contract["legacy_T_to_new_Mx_replay_allowed"] is False
