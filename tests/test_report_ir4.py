from __future__ import annotations

from standard_core.declarative_case_evidence import clear_case_runtime_evidence_cache
from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.report_ir4 import _token_substitute, build_report_ir4, report_ir4_json


def _notes():
    return {"engineering_meaning": None, "limitations": None, "normative_warning": None}


def _ref(section: str):
    return [{"standard_id": "TEST_STD", "section": section}]


def _graph():
    return {
        "graph_id": "report_ir4_piecewise_test_graph",
        "engine_contract": {},
        "quantities": [
            {"id": "x", "name_ru": "Аргумент", "symbol": "x", "data_type": "number", "canonical_unit": "kN"},
            {"id": "mode", "name_ru": "Режим", "symbol": "mode", "data_type": "string", "canonical_unit": None},
            {"id": "y", "name_ru": "Результат", "symbol": "y", "data_type": "number", "canonical_unit": "kN"},
        ],
        "datasets": [],
        "nodes": [
            {
                "id": "INPUT",
                "node_type": "input",
                "owner_standard_id": "TEST_STD",
                "title": "Исходные данные",
                "normative_refs": _ref("1"),
                "consumes": [],
                "produces": [
                    {"quantity_id": "x", "required": True},
                    {"quantity_id": "mode", "required": True},
                ],
                "applicability": None,
                "notes": _notes(),
                "input_spec": {"input_method": "user", "required": True, "user_prompt": "input"},
            },
            {
                "id": "CALC",
                "node_type": "calculation",
                "owner_standard_id": "TEST_STD",
                "title": "Piecewise calculation",
                "normative_refs": _ref("2"),
                "consumes": [
                    {"quantity_id": "x", "required": True},
                    {"quantity_id": "mode", "required": True},
                ],
                "produces": [{"quantity_id": "y", "required": True}],
                "applicability": None,
                "notes": _notes(),
                "calculation_spec": {
                    "expression_language": "expr_v1",
                    "bindings": [{"variable": "x", "quantity_id": "x"}],
                    "cases": [
                        {
                            "when": {"type": "comparison", "quantity_id": "mode", "operator": "eq", "value": "A"},
                            "expression": "x * 2",
                        },
                        {
                            "when": {"type": "comparison", "quantity_id": "mode", "operator": "eq", "value": "B"},
                            "expression": "x * 3",
                        },
                    ],
                },
            },
        ],
        "edges": [
            {
                "id": "E_INPUT_CALC",
                "from_node_id": "INPUT",
                "to_node_id": "CALC",
                "edge_type": "control",
                "condition": None,
                "quantity_ids": [],
            }
        ],
    }


def _session(x: float = 3.0, mode: str = "A"):
    clear_case_runtime_evidence_cache()
    model = FireDAGModel(_graph())
    session = GuidedCalculationSession(model, entry_node_id="INPUT", registry=ExecutionRegistry())
    session.submit({"x": x, "mode": mode})
    return model, session


def test_piecewise_runtime_case_is_bound_to_report_formula_and_numeric_substitution():
    model, session = _session(3.0, "A")
    assert session.values["y"].value == 6.0

    report = build_report_ir4(model, session)
    block = next(row for row in report["blocks"] if row["owner_node_id"] == "CALC")
    runtime = block["runtime_case_evidence"]
    human = block["human_readable"]

    assert runtime["capture_status"] == "CAPTURED"
    assert runtime["selection_mode"] == "piecewise_case"
    assert runtime["selected_case_index"] == 0
    assert runtime["selected_expression"] == "x * 2"
    assert human["formula_expression"] == "x * 2"
    assert human["substituted_expression"] == "(3) * 2"
    assert human["piecewise_case_status"] == "CAPTURED_BY_RUNTIME_AUDIT"
    assert human["result_lines"][0]["raw_value"] == 6.0
    assert human["report_evaluated_expression"] is False
    assert report["audit"]["formula_expressions_evaluated_by_report"] is False
    assert report["audit"]["calculation_values_recomputed_by_report"] is False


def test_report_route_comes_from_trace_selected_edge_without_rechecking_condition():
    model, session = _session()
    report = build_report_ir4(model, session)

    assert report["selected_route"]
    first = report["selected_route"][0]
    assert first["selected_edge_id"] == "E_INPUT_CALC"
    assert first["from_node_id"] == "INPUT"
    assert first["to_node_id"] == "CALC"
    assert report["audit"]["route_conditions_recomputed_by_report"] is False


def test_piecewise_evidence_is_replay_safe_after_editing_earlier_answer():
    model, session = _session(3.0, "A")
    before = build_report_ir4(model, session)
    before_calc = next(row for row in before["blocks"] if row["owner_node_id"] == "CALC")
    assert before_calc["human_readable"]["substituted_expression"] == "(3) * 2"

    session.edit_answer("INPUT", {"x": 4.0, "mode": "B"})
    after = build_report_ir4(model, session)
    calc = next(row for row in after["blocks"] if row["owner_node_id"] == "CALC")

    assert session.values["y"].value == 12.0
    assert calc["runtime_case_evidence"]["selected_case_index"] == 1
    assert calc["runtime_case_evidence"]["selected_expression"] == "x * 3"
    assert calc["human_readable"]["substituted_expression"] == "(4) * 3"
    assert calc["human_readable"]["result_lines"][0]["raw_value"] == 12.0


def test_token_substitution_replaces_only_complete_variable_names():
    rendered, missing = _token_substitute(
        "max(x, xx) + x",
        [
            {"variable": "x", "present_in_trace": True, "raw_value": 2.0},
            {"variable": "xx", "present_in_trace": True, "raw_value": 5.0},
        ],
    )
    assert rendered == "max((2), (5)) + (2)"
    assert missing == []


def test_ir4_is_deterministic_and_sections_reference_existing_blocks():
    model, session = _session()
    assert report_ir4_json(model, session) == report_ir4_json(model, session)

    report = build_report_ir4(model, session)
    block_ids = {row["report_block_id"] for row in report["blocks"]}
    section_ids = {bid for section in report["sections"] for bid in section["block_ids"]}
    assert section_ids == block_ids
