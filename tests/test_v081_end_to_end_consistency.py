from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import build_model as build_v076_model
from standard_core.sp16_mech7_v081_end_to_end_overlay import (
    GOVERNING_AXIS_QID,
    GRAPH_SUFFIX,
    HANDOFF_NODE_ID,
    RETIRED_SCALAR_STABILITY_NODES,
    build_model,
)
from standard_core.sp16_mech7_v081_runtime import governing_stability_handoff
from streamlit_guided_ux_v081 import _consume_exact_reuse, _semantic_replay

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    # Reproduce the production installer ancestry. v0.78+ overlays consume the
    # canonical Stage-N7 nodes introduced by v0.75/v0.76; applying them directly
    # to the frozen v0.67 DAG would create a deliberately invalid dangling edge.
    return build_model(build_v076_model(build_v075_model(base)))


def test_v081_scalar_chain_is_preserved_as_evidence_but_unschedulable():
    model = _active_model()
    assert str(model.graph["graph_id"]).endswith(GRAPH_SUFFIX)
    assert {
        "SP16_C_I_MIN",
        "SP16_C_LAMBDA",
        "SP16_C_LBAR",
        "SP16_D_CURVE",
        "SP16_L_TABLE7",
        "SP16_C_DELTA9",
        "SP16_C_PHI8_RAW",
        "SP16_C_PHI_LIMITS",
    } == RETIRED_SCALAR_STABILITY_NODES
    assert RETIRED_SCALAR_STABILITY_NODES <= set(model.nodes)

    # No control, branch, handoff *or data* dependency may enter the retired
    # chain. This is stronger than the v0.80 presentation-only cleanup.
    incoming = [
        edge
        for edge in model.graph["edges"]
        if edge.get("to_node_id") in RETIRED_SCALAR_STABILITY_NODES
    ]
    assert incoming == []

    hidden = set(model.presentation_policy.get("hidden_normative_nodes") or [])
    excluded = set(model.presentation_policy.get("guided_excluded_nodes") or [])
    assert RETIRED_SCALAR_STABILITY_NODES <= hidden
    assert RETIRED_SCALAR_STABILITY_NODES <= excluded


def test_v081_handoff_is_the_only_active_scalar_stability_producer():
    model = _active_model()
    handoff = model.nodes[HANDOFF_NODE_ID]
    consumed = {row["quantity_id"] for row in handoff["consumes"]}
    produced = {row["quantity_id"] for row in handoff["produces"]}

    assert {
        "lambda_bar_z",
        "lambda_bar_y",
        "sp16_curve_z",
        "sp16_curve_y",
        "phi_z_sp16",
        "phi_y_sp16",
    } <= consumed
    assert {
        "lambda_bar",
        "sp16_buckling_curve_type",
        "phi_sp16_formula8",
        GOVERNING_AXIS_QID,
    } <= produced

    excluded = set(model.presentation_policy.get("guided_excluded_nodes") or [])
    for qid in ("lambda_bar", "sp16_buckling_curve_type", "phi_sp16_formula8"):
        active = [nid for nid in model.producer_nodes[qid] if nid not in excluded]
        assert active == [HANDOFF_NODE_ID]


def test_v081_handoff_keeps_lambda_curve_phi_from_one_governing_axis():
    values = {
        "lambda_bar_z": 1.8,
        "lambda_bar_y": 2.7,
        "sp16_curve_z": "a",
        "sp16_curve_y": "c",
        "phi_z_sp16": 0.71,
        "phi_y_sp16": 0.46,
    }
    result = governing_stability_handoff(values)
    assert result[GOVERNING_AXIS_QID] == "y"
    assert result["lambda_bar"] == 2.7
    assert result["sp16_buckling_curve_type"] == "c"
    assert result["phi_sp16_formula8"] == 0.46

    # Equal phi is deterministic and still returns a physical single-axis tuple.
    tie = governing_stability_handoff(
        {
            "lambda_bar_z": 2.0,
            "lambda_bar_y": 3.0,
            "sp16_curve_z": "b",
            "sp16_curve_y": "c",
            "phi_z_sp16": 0.5,
            "phi_y_sp16": 0.5,
        }
    )
    assert tie[GOVERNING_AXIS_QID] == "z"
    assert (tie["lambda_bar"], tie["sp16_buckling_curve_type"], tie["phi_sp16_formula8"]) == (2.0, "b", 0.5)


def _q(qid: str):
    return {
        "id": qid,
        "symbol": None,
        "name_ru": qid,
        "data_type": "string",
        "role": "input",
        "physical_dimension": None,
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {
            "primary_source_type": "USER_INPUT",
            "allowed_source_types": ["USER_INPUT"],
            "override_policy": "forbidden",
        },
    }


def _input(nid: str, qid: str):
    return {
        "id": nid,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": nid,
        "normative_refs": [],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": True, "binding_role": "output"}],
        "applicability": None,
        "input_spec": {"input_method": "user_input", "required": True, "user_prompt": nid},
    }


def test_v081_migration_drops_scalar_rows_and_preserves_existing_retained_tail():
    graph = {
        "graph_id": "v081_replay_fixture",
        "graph_title": "fixture",
        "graph_type": "normative_calculation_dag",
        "description": "fixture",
        "engine_contract": {},
        "quantities": [_q("qa"), _q("qnew"), _q("qb")],
        "nodes": [_input("A", "qa"), _input("NEW", "qnew"), _input("B", "qb")],
        "edges": [
            {"id": "E1", "from_node_id": "A", "to_node_id": "NEW", "edge_type": "control", "label": None, "condition": None, "quantity_ids": []},
            {"id": "E2", "from_node_id": "NEW", "to_node_id": "B", "edge_type": "control", "label": None, "condition": None, "quantity_ids": []},
        ],
    }
    model = FireDAGModel(graph)

    class Source:
        entry_node_id = "A"
        interaction_history = [
            {"node_id": "A", "payload": "old-a", "provenance": None},
            {"node_id": "SP16_C_LBAR", "payload": None, "provenance": None},
        ]

        @staticmethod
        def plain_values():
            return {}

    source = Source()
    setattr(
        source,
        "_v079_retained_interaction_history",
        [{"node_id": "B", "payload": "old-b", "provenance": None}],
    )

    migrated = _semantic_replay(source, model, ExecutionRegistry())
    assert migrated.current_node_id == "NEW"
    assert [row["node_id"] for row in migrated.interaction_history] == ["A"]
    assert [row["node_id"] for row in getattr(migrated, "_v079_retained_interaction_history")] == ["B"]

    migrated.submit("new-answer")
    _consume_exact_reuse(migrated)
    assert migrated.status == "COMPLETE"
    assert [row["node_id"] for row in migrated.interaction_history] == ["A", "NEW", "B"]
    assert migrated.plain_values()["qb"] == "old-b"


def test_v081_is_the_active_streamlit_entrypoint_and_keeps_v080_chain():
    app = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    v081 = (ROOT / "streamlit_guided_ux_v081.py").read_text(encoding="utf-8")
    assert "from streamlit_guided_ux_v081 import install as _install_guided_ux" in app
    assert "streamlit_guided_ux_v080" not in app
    assert "import streamlit_guided_ux_v080 as _v080" in v081
    assert "_v080.install(core)" in v081
    assert "rows.extend" in v081
