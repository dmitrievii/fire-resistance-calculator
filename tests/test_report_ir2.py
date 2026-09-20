from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.report_ir2 import build_report_ir2, report_ir2_json, reportability_census
from standard_core.declarative_runtime_evidence import clear_runtime_evidence_cache


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _notes():
    return {"engineering_meaning": None, "limitations": None, "normative_warning": None}


def _ref(section: str):
    return [{"standard_id": "TEST_STD", "section": section}]


def _graph():
    return {
        "graph_id": "report_ir2_test_graph",
        "engine_contract": {},
        "quantities": [
            {"id": "x", "name_ru": "x", "symbol": "x", "data_type": "number", "canonical_unit": "kN"},
            {"id": "y", "name_ru": "y", "symbol": "y", "data_type": "number", "canonical_unit": "kN"},
            {"id": "table_x", "name_ru": "Аргумент", "symbol": "a", "data_type": "number", "canonical_unit": "mm"},
            {"id": "table_y", "name_ru": "Табличный результат", "symbol": "b", "data_type": "number", "canonical_unit": "min"},
        ],
        "datasets": [
            {
                "id": "TEST_TABLE",
                "dataset_type": "normative_table",
                "owner_standard_id": "TEST_STD",
                "title": "Test table",
                "normative_refs": _ref("3"),
                "axes": [],
                "output_quantity_ids": ["table_y"],
                "interpolation": {"method": "linear", "axis": "a"},
                "storage": {"mode": "inline", "rows": [{"a": 1.0, "b": 10.0}, {"a": 2.0, "b": 20.0}]},
                "notes": None,
            }
        ],
        "nodes": [
            {
                "id": "INPUT_X",
                "node_type": "input",
                "owner_standard_id": "TEST_STD",
                "title": "Input x",
                "normative_refs": _ref("1"),
                "consumes": [],
                "produces": [{"quantity_id": "x", "required": True}, {"quantity_id": "table_x", "required": True}],
                "applicability": None,
                "notes": _notes(),
                "input_spec": {"input_method": "user_number", "required": True, "user_prompt": "input"},
            },
            {
                "id": "CALC_Y",
                "node_type": "calculation",
                "owner_standard_id": "TEST_STD",
                "title": "Formula y",
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
            {
                "id": "LOOKUP",
                "node_type": "lookup",
                "owner_standard_id": "TEST_STD",
                "title": "Lookup b",
                "normative_refs": _ref("3"),
                "consumes": [{"quantity_id": "table_x", "required": True}],
                "produces": [{"quantity_id": "table_y", "required": True}],
                "applicability": None,
                "notes": _notes(),
                "lookup_spec": {
                    "dataset_id": "TEST_TABLE",
                    "selector_bindings": [{"quantity_id": "table_x", "dataset_field": "a"}],
                    "output_bindings": [{"quantity_id": "table_y", "dataset_field": "b"}],
                    "interpolation": {"method": "linear", "axis": "a"},
                },
            },
        ],
        "edges": [
            {"id": "E1", "from_node_id": "INPUT_X", "to_node_id": "CALC_Y", "edge_type": "control", "condition": None, "quantity_ids": []},
            {"id": "E2", "from_node_id": "CALC_Y", "to_node_id": "LOOKUP", "edge_type": "control", "condition": None, "quantity_ids": []},
        ],
    }


def _session():
    clear_runtime_evidence_cache()
    model = FireDAGModel(_graph())
    registry = ExecutionRegistry()
    registry.register("CALC_Y", lambda values, node: {"y": values["x"] * 2.0})
    # LOOKUP is deliberately left declarative: the existing production lookup
    # computes table_y and the audit hook records its selected dataset rows.
    session = GuidedCalculationSession(model, entry_node_id="INPUT_X", registry=registry)
    session.submit({"x": 3.0, "table_x": 1.5})
    return model, session


def test_ir2_binds_formula_variables_to_actual_trace_values_without_recalculation():
    model, session = _session()
    report = build_report_ir2(model, session)
    calc = next(block for block in report["blocks"] if block["owner_node_id"] == "CALC_Y")
    evidence = calc["execution_evidence"]

    assert evidence["evidence_mode"] == "trace_bound_formula_operands"
    assert evidence["expression"] == "x * 2"
    assert evidence["bindings"][0]["variable"] == "x"
    assert evidence["bindings"][0]["raw_value"] == 3.0
    assert evidence["result_values"][0]["raw_value"] == 6.0
    assert evidence["report_recomputed_result"] is False


def test_runtime_linear_lookup_evidence_records_exact_bracket_rows_without_report_recalculation():
    model, session = _session()
    assert session.values["table_y"].value == 15.0

    report = build_report_ir2(model, session)
    block = next(block for block in report["blocks"] if block["owner_node_id"] == "LOOKUP")
    evidence = block["execution_evidence"]
    runtime = evidence["runtime_lookup_evidence"]

    assert evidence["dataset_id"] == "TEST_TABLE"
    assert evidence["selectors"][0]["dataset_field"] == "a"
    assert evidence["selectors"][0]["raw_value"] == 1.5
    assert evidence["output_bindings"][0]["raw_value"] == 15.0
    assert evidence["selected_dataset_rows_status"] == "CAPTURED_BY_RUNTIME_AUDIT"
    assert [row["role"] for row in evidence["selected_dataset_rows"]] == ["lower", "upper"]
    assert evidence["selected_dataset_rows"][0]["row"] == {"a": 1.0, "b": 10.0}
    assert evidence["selected_dataset_rows"][1]["row"] == {"a": 2.0, "b": 20.0}
    assert runtime["selection_mode"] == "linear_bracket"
    assert runtime["axis"] == "a"
    assert runtime["axis_value"] == 1.5
    assert runtime["axis_lower"] == 1.0
    assert runtime["axis_upper"] == 2.0
    assert runtime["fraction"] == 0.5
    assert runtime["result_recomputed"] is False
    assert evidence["report_recomputed_lookup"] is False
    assert report["audit"]["table_interpolation_recomputed_by_report"] is False
    assert report["audit"]["runtime_selected_dataset_rows_captured"] is True
    assert report["audit"]["runtime_lookup_block_count"] == 1
    assert report["audit"]["runtime_lookup_blocks_with_rows"] == 1


def test_runtime_evidence_key_is_replay_safe_after_changed_input():
    model, session = _session()
    before = build_report_ir2(model, session)
    before_lookup = next(block for block in before["blocks"] if block["owner_node_id"] == "LOOKUP")
    assert before_lookup["execution_evidence"]["runtime_lookup_evidence"]["axis_value"] == 1.5

    session.edit_answer("INPUT_X", {"x": 4.0, "table_x": 2.0})
    after = build_report_ir2(model, session)
    lookup = next(block for block in after["blocks"] if block["owner_node_id"] == "LOOKUP")
    runtime = lookup["execution_evidence"]["runtime_lookup_evidence"]

    assert session.values["table_y"].value == 20.0
    assert runtime["selection_mode"] == "linear_exact_knot"
    assert runtime["axis_value"] == 2.0
    assert runtime["selected_rows"][0]["row"] == {"a": 2.0, "b": 20.0}
    assert lookup["execution_evidence"]["selected_dataset_rows"] == runtime["selected_rows"]


def test_ir2_is_deterministic():
    model, session = _session()
    assert report_ir2_json(model, session) == report_ir2_json(model, session)


def test_active_v0370_dag_reportability_census_is_complete():
    model = FireDAGModel.load(ACTIVE_DAG)
    census = reportability_census(model)

    assert census["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    assert census["node_count"] == 734
    assert census["quantity_count"] == 922
    assert census["dataset_count"] == 39
    assert sum(census["node_type_counts"].values()) == 734
    assert sum(census["report_kind_counts"].values()) == 734
