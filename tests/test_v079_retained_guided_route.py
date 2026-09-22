from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import DEFINITION_QID, build_model as build_v076_model
from standard_core.sp16_mech7_v079_guided_route_overlay import (
    GRAPH_SUFFIX,
    RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES,
    build_model,
)
from streamlit_guided_ux_v079 import (
    _consume_retained_history,
    _render_string_decision_selectbox,
    _reuse_member_length_context,
    _semantic_replay,
)

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    return build_model(build_v076_model(build_v075_model(base)))


def test_v079_removes_navigation_into_retired_mu_authoring():
    model = _active_model()
    assert str(model.graph["graph_id"]).endswith(GRAPH_SUFFIX)
    assert "SP16_D_MU_ROUTE" in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
    assert "SP16_D_MU_SCHEME" in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
    assert "SP16_D_MU_ROUTE_X" in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
    assert "SP16_D_MU_ROUTE_Y" in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES

    bad = [
        edge
        for edge in model.graph["edges"]
        if edge.get("edge_type") in {"control", "branch", "handoff"}
        and edge.get("to_node_id") in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
    ]
    assert bad == []

    excluded = set(model.presentation_policy.get("guided_excluded_nodes") or [])
    assert RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES <= excluded


def test_v079_fire_load_case_string_decision_has_real_options():
    model = _active_model()
    node = next(
        row for row in model.nodes.values()
        if row.get("decision_quantity_id") == "fire_load_case_mode"
    )
    card = model.node_card(node["id"])
    assert card["node_type"] == "decision"
    assert card["fields"][0]["data_type"] == "string"
    assert [row["value"] for row in card["options"]] == ["same_as_ambient", "separate"]

    class FakeSt:
        def __init__(self):
            self.calls = []

        def selectbox(self, label, values, **kwargs):
            self.calls.append((label, list(values), kwargs))
            return values[0]

        def caption(self, _text):
            pass

    fake_st = FakeSt()

    class FakeCore:
        @staticmethod
        def _st():
            return fake_st

        @staticmethod
        def _key(*parts):
            return ":".join(str(x) for x in parts)

    payload, provenance, ready = _render_string_decision_selectbox(FakeCore, card, None, "calc")
    assert ready is True
    assert provenance is None
    assert payload == "same_as_ambient"
    assert fake_st.calls
    assert fake_st.calls[0][1] == ["same_as_ambient", "separate"]


def test_v079_reuses_only_exact_geometric_length_from_v076_card():
    class FakeSession:
        current_node_id = "SP554_I_COMPRESSION_CONTEXT"

        class Model:
            nodes = {
                "SP554_I_COMPRESSION_CONTEXT": {
                    "produces": [{"quantity_id": "member_length", "required": True}]
                }
            }

        model = Model()

        def __init__(self, definition):
            self.definition = definition
            self.submitted = []

        def plain_values(self):
            return {DEFINITION_QID: self.definition}

        def submit(self, payload, *, provenance=None):
            self.submitted.append((payload, provenance))

    session = FakeSession({"member_length_mm": 3000.0, "z": {}, "y": {}})
    assert _reuse_member_length_context(session) is True
    assert session.submitted[0][0] == 3000.0
    assert session.submitted[0][1]["rule"] == "exact reuse only; no inference"

    direct_only = FakeSession({"z": {"method": "verified_analysis"}, "y": {"method": "verified_analysis"}})
    assert _reuse_member_length_context(direct_only) is False
    assert direct_only.submitted == []


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


def test_v079_semantic_replay_retains_tail_across_new_question_and_skips_retired_rows():
    graph = {
        "graph_id": "v079_replay_fixture",
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
            {"node_id": "SP16_D_MU_ROUTE", "payload": "table30", "provenance": None},
            {"node_id": "B", "payload": "old-b", "provenance": None},
        ]

        @staticmethod
        def plain_values():
            return {}

    migrated = _semantic_replay(Source(), model, ExecutionRegistry())
    assert migrated.current_node_id == "NEW"
    assert [row["node_id"] for row in migrated.interaction_history] == ["A"]
    assert [row["node_id"] for row in getattr(migrated, "_v079_retained_interaction_history")] == ["B"]

    migrated.submit("new-answer")
    _consume_retained_history(migrated)
    assert migrated.status == "COMPLETE"
    assert [row["node_id"] for row in migrated.interaction_history] == ["A", "NEW", "B"]
    assert migrated.plain_values()["qb"] == "old-b"


def test_v079_entrypoint_and_graphic_crash_remediation_are_active():
    app_source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    assert "streamlit_guided_ux_v079" in app_source
    assert "streamlit_graphic_selectors_v079" in app_source

    graphic = (ROOT / "streamlit_graphic_selectors_v079.py").read_text(encoding="utf-8")
    assert 'st.success(f"Выбрано: {title}", icon=' not in graphic
    assert 'st.success(f"Выбрано: {title}")' in graphic

    guided = (ROOT / "streamlit_guided_ux_v079.py").read_text(encoding="utf-8")
    assert "Таблица 1 здесь определяет коэффициент условий работы γc" in guided
    assert "replay_prefix_on_model" not in guided
