from __future__ import annotations

import copy
from pathlib import Path

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.report_ir import build_report_ir, report_ir_json


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _notes():
    return {"engineering_meaning": None, "limitations": None, "normative_warning": None}


def _ref(section: str):
    return [{"standard_id": "TEST_STD", "section": section}]


def _graph():
    return {
        "graph_id": "report_ir_test_graph",
        "engine_contract": {},
        "quantities": [
            {
                "id": "x",
                "name_ru": "Исходное значение",
                "symbol": "x",
                "data_type": "number",
                "canonical_unit": "kN",
            },
            {
                "id": "y",
                "name_ru": "Расчётное значение",
                "symbol": "y",
                "data_type": "number",
                "canonical_unit": "kN",
            },
        ],
        "datasets": [],
        "nodes": [
            {
                "id": "INPUT_X",
                "node_type": "input",
                "owner_standard_id": "TEST_STD",
                "title": "Исходное значение",
                "normative_refs": _ref("1"),
                "consumes": [],
                "produces": [{"quantity_id": "x", "required": True}],
                "applicability": None,
                "notes": _notes(),
                "input_spec": {
                    "input_method": "user_number",
                    "required": True,
                    "user_prompt": "Введите x",
                },
            },
            {
                "id": "CALC_Y",
                "node_type": "calculation",
                "owner_standard_id": "TEST_STD",
                "title": "Расчёт y",
                "normative_refs": _ref("2"),
                "consumes": [{"quantity_id": "x", "required": True}],
                "produces": [{"quantity_id": "y", "required": True}],
                "applicability": None,
                "notes": _notes(),
                "calculation_spec": {
                    "expression_language": "expr_v1",
                    "expression": "x * 2",
                    "bindings": [{"variable": "x", "quantity_id": "x"}],
                },
            },
        ],
        "edges": [
            {
                "id": "E_INPUT_CALC",
                "from_node_id": "INPUT_X",
                "to_node_id": "CALC_Y",
                "edge_type": "control",
                "condition": None,
                "quantity_ids": [],
            }
        ],
    }


def _session(*, failing: bool = False):
    model = FireDAGModel(_graph())
    registry = ExecutionRegistry()

    def calc(values, node):
        if failing:
            raise ValueError("deliberate test failure")
        return {"y": float(values["x"]) * 2.0}

    registry.register("CALC_Y", calc)
    return model, GuidedCalculationSession(model, entry_node_id="INPUT_X", registry=registry)


def _by_owner(report):
    return {block["owner_node_id"]: block for block in report["blocks"]}


def test_report_ir_projects_actual_completed_dag_trace_without_recalculation():
    model, session = _session()
    session.submit(3.0)

    report = build_report_ir(model, session)
    blocks = _by_owner(report)

    assert report["schema"] == "fire_report_ir_v1"
    assert report["audit"]["calculation_values_recomputed_by_report"] is False
    assert blocks["INPUT_X"]["kind"] == "INPUT"
    assert blocks["CALC_Y"]["kind"] == "FORMULA"
    assert blocks["CALC_Y"]["outputs"][0]["quantity_id"] == "y"
    assert blocks["CALC_Y"]["outputs"][0]["raw_value"] == session.values["y"].value == 6.0
    assert blocks["CALC_Y"]["execution_spec"]["expression"] == "x * 2"
    assert blocks["CALC_Y"]["normative_refs"] == _ref("2")
    assert blocks["CALC_Y"]["report_block_id"] == "CALC_Y#1"


def test_report_ir_replay_replaces_stale_downstream_values_and_keeps_stable_ids():
    model, session = _session()
    session.submit(3.0)
    before = build_report_ir(model, session)
    before_ids = [block["report_block_id"] for block in before["blocks"]]
    assert _by_owner(before)["CALC_Y"]["outputs"][0]["raw_value"] == 6.0

    session.edit_answer("INPUT_X", 4.0)
    after = build_report_ir(model, session)
    after_ids = [block["report_block_id"] for block in after["blocks"]]

    assert before_ids == after_ids == ["INPUT_X#1", "CALC_Y#1"]
    assert _by_owner(after)["INPUT_X"]["outputs"][0]["raw_value"] == 4.0
    assert _by_owner(after)["CALC_Y"]["outputs"][0]["raw_value"] == 8.0
    assert all(
        value.get("raw_value") != 6.0
        for block in after["blocks"]
        for value in block.get("outputs", [])
    )


def test_report_ir_is_byte_deterministic_for_same_session_state():
    model, session = _session()
    session.submit(5.5)

    a = report_ir_json(model, session)
    b = report_ir_json(model, copy.deepcopy(session.snapshot()))

    assert a == b
    assert build_report_ir(model, session)["report_sha256"] == build_report_ir(model, session)["report_sha256"]


def test_report_ir_emits_fail_closed_block_but_no_fake_calculation_result():
    model, session = _session(failing=True)
    session.submit(3.0)

    report = build_report_ir(model, session)
    calc_blocks = [block for block in report["blocks"] if block["owner_node_id"] == "CALC_Y"]

    assert len(calc_blocks) == 1
    assert calc_blocks[0]["kind"] == "FAIL_CLOSED"
    assert calc_blocks[0]["outputs"] == []
    assert calc_blocks[0]["failure"]["status"] == "EXECUTION_FAILED"
    assert "deliberate test failure" in calc_blocks[0]["message"]


def test_report_ir_loads_the_active_v0370_normative_dag_without_mutating_it():
    root = Path(__file__).resolve().parents[1]
    dag_path = root / "normative_graph" / ACTIVE_DAG
    model = FireDAGModel.load(dag_path)
    state = {
        "schema": "fire_ui_session_v1",
        "graph_id": model.graph["graph_id"],
        "graph_sha256": model.graph_sha256,
        "entry_node_id": model.guided_entry_node_id(),
        "current_node_id": model.guided_entry_node_id(),
        "status": "AWAITING_INPUT",
        "ledger": [],
        "trace": [],
        "branch_failures": [],
    }

    report = build_report_ir(model, state)

    assert dag_path.name == ACTIVE_DAG
    assert report["graph_id"] == model.graph["graph_id"]
    assert report["graph_sha256"] == model.graph_sha256
    assert report["block_count"] == 0
    assert report["blocks"] == []
