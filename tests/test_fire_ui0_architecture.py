import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import (
    FireDAGModel,
    FireUIError,
    GuidedCalculationSession,
    ExecutionRegistry,
    _condition_value,
)
from standard_core.fire_ui0_integrated import run_integrated_member_fire_case

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.44_fire_d4.json"


def model():
    return FireDAGModel.load(DAG)


def test_contract_is_generated_from_frozen_dag_and_has_live_ledger_trace_contract():
    m = model()
    c = m.build_ui_contract()
    assert c["schema"] == "fire_ui_contract_v1"
    assert c["graph_id"] == "sp16_sp554_dag_v0-3-44_fire_d4"
    assert c["counts"]["quantities"] == 748
    assert c["counts"]["nodes"] == 657
    assert c["counts"]["edges"] == 1108
    assert c["counts"]["interactive_nodes"] == 139
    assert c["ledger_contract"]["show_normative_refs"] is True
    assert c["trace_contract"]["report_ready"] is True


def test_first_guided_steps_follow_actual_sp554_control_edges():
    s = GuidedCalculationSession(model())
    assert s.current_node_id == "SP554_I_BUILDING_USE"
    s.submit("industrial")
    assert s.current_node_id == "SP554_D_LOAD_BEARING"
    s.submit(True)
    assert s.current_node_id == "SP554_D_ENCLOSING"
    s.submit(False)
    assert s.current_node_id == "SP554_D_PRODUCT_ROUTE"
    s.submit("hot_rolled_section")
    assert s.current_node_id == "SP554_H_REQUIRED_R"
    assert s.current_card()["external_handoff"] is True


def test_external_handoff_requires_source_provenance():
    s = GuidedCalculationSession(model())
    s.submit("industrial"); s.submit(True); s.submit(False); s.submit("hot_rolled_section")
    with pytest.raises(FireUIError, match="provenance"):
        s.submit(15.0)
    s.submit(15.0, provenance={"source_document": "project fire requirement", "source_reference": "R15"})
    assert s.current_node_id == "SP554_D_METHOD"
    row = next(x for x in s.ledger() if x["quantity_id"] == "required_fire_resistance_min")
    assert row["value"] == 15.0
    assert row["source_kind"] == "EXTERNAL_STANDARD_RESULT"


def test_decision_validation_rejects_non_enum_value():
    s = GuidedCalculationSession(model())
    s.submit("industrial"); s.submit(True); s.submit(False)
    with pytest.raises(FireUIError):
        s.submit("not_a_route")


def test_edit_replays_history_and_invalidates_old_downstream_branch():
    s = GuidedCalculationSession(model())
    s.submit("industrial"); s.submit(True); s.submit(False); s.submit("hot_rolled_section")
    s.submit(15.0, provenance={"source_document": "x", "source_reference": "R15"})
    assert "required_fire_resistance_min" in s.values
    state = s.edit_answer("SP554_D_LOAD_BEARING", False)
    assert state["current_node_id"] == "SP554_R_NOT_LOAD_BEARING_OUTSIDE_R_SCOPE"
    assert "required_fire_resistance_min" not in s.values
    assert [h["node_id"] for h in s.interaction_history] == ["SP554_I_BUILDING_USE", "SP554_D_LOAD_BEARING"]


def test_missing_calculation_executor_blocks_instead_of_skipping():
    # Advance to an actual early path then inspect explicit blocking behavior on
    # a synthetic calculation graph to avoid depending on future path ordering.
    m = model()
    graph = {
        "graph_id": "mini",
        "engine_contract": m.graph["engine_contract"],
        "quantities": [
            {"id": "x", "name_ru": "x", "data_type": "number", "role": "input", "canonical_unit": None, "allowed_units": [], "source_policy": {"primary_source_type": "USER_INPUT"}},
            {"id": "y", "name_ru": "y", "data_type": "number", "role": "intermediate", "canonical_unit": None, "allowed_units": [], "source_policy": {"primary_source_type": "CALCULATED"}},
        ],
        "nodes": [
            {"id": "I", "node_type": "input", "owner_standard_id": "X", "title": "x", "normative_refs": [], "consumes": [], "produces": [{"quantity_id": "x", "required": True}], "input_spec": {"user_prompt": "x"}},
            {"id": "C", "node_type": "calculation", "owner_standard_id": "X", "title": "y", "normative_refs": [], "consumes": [{"quantity_id": "x", "required": True}], "produces": [{"quantity_id": "y", "required": True}]},
        ],
        "edges": [{"id": "E", "from_node_id": "I", "to_node_id": "C", "edge_type": "control", "label": None, "condition": None, "quantity_ids": []}],
    }
    mini = FireDAGModel(graph)
    s = GuidedCalculationSession(mini, entry_node_id="I")
    s.submit(2.0)
    assert s.current_node_id == "C"
    assert s.status == "BLOCKED_EXECUTOR_REQUIRED:C"


def test_registered_executor_populates_read_only_ledger_and_trace():
    base = model()
    graph = {
        "graph_id": "mini2", "engine_contract": base.graph["engine_contract"],
        "quantities": [
            {"id": "x", "name_ru": "x", "data_type": "number", "role": "input", "canonical_unit": "mm", "allowed_units": ["mm"], "source_policy": {"primary_source_type": "USER_INPUT"}},
            {"id": "y", "name_ru": "y", "data_type": "number", "role": "intermediate", "canonical_unit": "mm", "allowed_units": ["mm"], "source_policy": {"primary_source_type": "CALCULATED"}},
        ],
        "nodes": [
            {"id": "I", "node_type": "input", "owner_standard_id": "X", "title": "x", "normative_refs": [], "consumes": [], "produces": [{"quantity_id": "x", "required": True}], "input_spec": {"user_prompt": "x"}},
            {"id": "C", "node_type": "calculation", "owner_standard_id": "X", "title": "y", "normative_refs": [{"standard_id":"X","reference_kind":"formula","formula_ref":"(1)"}], "consumes": [{"quantity_id": "x", "required": True}], "produces": [{"quantity_id": "y", "required": True}]},
            {"id": "R", "node_type": "result", "owner_standard_id": "X", "title": "done", "normative_refs": [], "consumes": [{"quantity_id": "y", "required": True}], "produces": []},
        ],
        "edges": [
            {"id": "E1", "from_node_id": "I", "to_node_id": "C", "edge_type": "control", "label": None, "condition": None, "quantity_ids": []},
            {"id": "E2", "from_node_id": "C", "to_node_id": "R", "edge_type": "control", "label": None, "condition": None, "quantity_ids": []},
        ],
    }
    reg = ExecutionRegistry(); reg.register("C", lambda values, node: {"y": values["x"] * 2.0})
    s = GuidedCalculationSession(FireDAGModel(graph), entry_node_id="I", registry=reg)
    s.submit(3.0)
    assert s.status == "RESULT"
    y = next(row for row in s.ledger() if row["quantity_id"] == "y")
    assert y["value"] == 6.0 and y["read_only"] is True
    assert s.trace[-1].node_id == "C" and s.trace[-1].selected_edge_id == "E2"


def test_condition_language_used_by_dag_is_supported():
    vals = {"a": 3, "b": "x"}
    assert _condition_value({"type":"comparison","quantity_id":"a","operator":"gte","value":3}, vals) is True
    assert _condition_value({"type":"comparison","quantity_id":"b","operator":"in","value":["x","y"]}, vals) is True
    assert _condition_value({"type":"all_of","conditions":[{"type":"comparison","quantity_id":"a","operator":"gt","value":2},{"type":"comparison","quantity_id":"b","operator":"eq","value":"x"}]}, vals) is True
    assert _condition_value({"type":"comparison","quantity_id":"missing","operator":"eq","value":1}, vals) is None


def test_session_snapshot_is_dag_locked_and_report_ready():
    s = GuidedCalculationSession(model()); s.submit("industrial")
    snap = s.snapshot()
    assert snap["schema"] == "fire_ui_session_v1"
    assert len(snap["graph_sha256"]) == 64
    assert snap["trace"][0]["schema"] == "fire_ui_trace_v1"
    assert snap["trace"][0]["normative_refs"]
    other = GuidedCalculationSession(model())
    other.restore(snap)
    assert other.current_node_id == s.current_node_id


def test_integrated_reference_adapter_reuses_frozen_fire_d2_d3_d4():
    mechanical = json.load(open(ROOT / "examples" / "fire_d2_sp554_critical_temperature_case.json", encoding="utf-8"))
    downstream = {
        "thermal_route": "UNPROTECTED_STEP_12_2",
        "reduced_thickness_mm": 10.0,
        "initial_temperature_c": 20.0,
        "time_step_min": 0.1,
        "max_time_min": 120.0,
        "steel_properties_source": "sp554_12_2_defaults",
        "required_fire_resistance_min": 15.0,
        "fire_regime": "standard",
        "requirement_provenance": {
            "source_kind": "external_normative_requirement",
            "source_document": "UI0 control requirement",
            "source_reference": "R15",
            "value_min": 15.0,
        },
    }
    result = run_integrated_member_fire_case(mechanical, downstream)
    assert result["status"] == "COMPLETE"
    assert result["fire_d2"]["critical_temperature_c"] == pytest.approx(525.0192844353662, abs=1e-10)
    assert result["ledger_outputs"]["required_fire_resistance_min"] == 15.0
    assert result["ledger_outputs"]["unprotected_fire_resistance_min"] == pytest.approx(14.326394173167056, abs=1e-10)
    assert result["ledger_outputs"]["unprotected_compliance"] is False

def test_parallel_supporting_standard_branch_does_not_steal_guided_navigation():
    s = GuidedCalculationSession(model())
    s.submit("industrial"); s.submit(True); s.submit(False); s.submit("hot_rolled_section")
    s.submit(15.0, provenance={"source_document": "x", "source_reference": "R15"})
    s.submit("calculation_analytical")
    assert s.current_node_id == "SP554_D_FIRE_REGIME"
    s.submit("standard")
    # E0013 stays inside SP554; E1192 starts a parallel GOST30247 subgraph.
    assert s.current_node_id == "SP554_D_SEISMIC"
