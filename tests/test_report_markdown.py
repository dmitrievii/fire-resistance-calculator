from __future__ import annotations

import copy

from standard_core.report_markdown import render_report_markdown


def _value(qid, value, unit=None):
    return {
        "quantity_id": qid,
        "symbol": qid,
        "name_ru": qid,
        "raw_value": value,
        "canonical_unit": unit,
    }


def _report():
    formula_block = {
        "report_block_id": "CALC#1",
        "owner_node_id": "CALC",
        "owner_standard_id": "SP16",
        "sequence": 2,
        "kind": "FORMULA",
        "title": "Проверочная формула",
        "normative_refs": [{"standard_id": "SP16", "section": "8.2"}],
        "inputs": [_value("N", 100.0, "kN")],
        "outputs": [_value("eta", 0.5)],
        "execution_spec": {"mode": "calculation_spec"},
        "execution_evidence": {},
        "human_readable": {
            "mode": "formula_substitution",
            "formula_expression": "N / NRd",
            "substituted_expression": "(100) / (200)",
            "selected_case_index": 1,
            "result_lines": [
                {
                    "quantity_id": "eta",
                    "symbol": "eta",
                    "display_value": "0.5",
                    "raw_value": 0.5,
                    "canonical_unit": None,
                }
            ],
        },
    }
    check_block = {
        "report_block_id": "CHECK#1",
        "owner_node_id": "CHECK",
        "owner_standard_id": "SP16",
        "sequence": 3,
        "kind": "CHECK",
        "title": "Проверка несущей способности",
        "normative_refs": [{"standard_id": "SP16", "section": "8.2"}],
        "inputs": [_value("eta", 0.5)],
        "outputs": [_value("ok", True)],
        "execution_spec": {"mode": "check_spec"},
        "execution_evidence": {},
        "human_readable": {"mode": "trace_values"},
    }
    return {
        "schema": "fire_report_ir_v4",
        "contract": "conservative_engineering_summary_v4",
        "graph_id": "g",
        "graph_sha256": "b" * 64,
        "session_schema": "s",
        "session_status": "WAITING",
        "entry_node_id": "INPUT",
        "current_node_id": "NEXT",
        "block_count": 2,
        "blocks": [formula_block, check_block],
        "sections": [
            {"section_key": "calculation", "title_ru": "Расчёт", "block_ids": ["CALC#1"]},
            {"section_key": "verification", "title_ru": "Проверки", "block_ids": ["CHECK#1"]},
        ],
        "selected_route": [
            {
                "sequence": 1,
                "selected_edge_id": "E1",
                "from_node_id": "INPUT",
                "to_node_id": "CALC",
                "edge_type": "control",
                "condition": None,
            }
        ],
        "dag_census": {},
        "summary": {
            "summary_status": "EXECUTED_BOOLEAN_CHECKS_PASS",
            "summary_status_scope": "report_execution_state_not_global_engineering_certification",
            "session_status": "WAITING",
            "executed_block_count": 2,
            "executed_route_edge_count": 1,
            "check_count": 1,
            "check_counts": {"PASS": 1, "FAIL": 0, "UNRESOLVED": 0},
            "checks": [
                {
                    "report_block_id": "CHECK#1",
                    "sequence": 3,
                    "owner_node_id": "CHECK",
                    "owner_standard_id": "SP16",
                    "title": "Проверка несущей способности",
                    "normative_refs": [{"standard_id": "SP16", "section": "8.2"}],
                    "verdict": "PASS",
                    "verdict_source": "explicit_boolean_check_outputs",
                    "outputs": [
                        {
                            "quantity_id": "ok",
                            "symbol": "ok",
                            "name_ru": "ok",
                            "raw_value": True,
                            "canonical_unit": None,
                            "display_value": "true",
                        }
                    ],
                }
            ],
            "result_block_count": 0,
            "results": [],
            "fail_closed_count": 0,
            "fail_closed": [],
            "governing": {
                "status": "NOT_DECLARED_BY_DAG",
                "reason": "explicit DAG declaration required",
                "candidates": [],
            },
        },
        "audit": {},
        "report_sha256": "a" * 64,
    }


def test_markdown_is_deterministic_and_contains_formula_substitution_and_trace_result():
    report = _report()
    first = render_report_markdown(report)
    second = render_report_markdown(copy.deepcopy(report))
    assert first == second
    assert "N / NRd" in first
    assert "(100) / (200)" in first
    assert "**eta** = `0.5`" in first
    assert "Активная piecewise-ветвь: `case #1`" in first


def test_markdown_contains_summary_normative_reference_and_selected_route():
    text = render_report_markdown(_report())
    assert "Все выполненные boolean-проверки пройдены" in text
    assert "SP16 8.2" in text
    assert "| 1 | E1 | INPUT | CALC | control |" in text
    assert "Управляющие нормативные величины" in text
    assert "NOT_DECLARED_BY_DAG" in text


def test_markdown_renders_executed_scoped_governing_without_global_selection():
    report = _report()
    report["summary"]["governing"] = {
        "status": "EXECUTED_DECLARATIONS",
        "reason": "explicit",
        "candidates": [
            {
                "scope": "sp554_section_10_bending_gamma_T",
                "scope_title_ru": "СП 554, раздел 10 — изгиб",
                "report_block_id": "GOV#1",
                "sequence": 8,
                "owner_node_id": "SP554_C_10_GOV",
                "owner_standard_id": "SP554_2026",
                "title": "Управляющий γT",
                "normative_refs": [{"standard_id": "SP554_2026", "section": "10"}],
                "quantity": {
                    "quantity_id": "gamma_T_bending_governing",
                    "symbol": "γT,gov",
                    "name_ru": "Управляющий γT",
                    "raw_value": 0.81,
                    "canonical_unit": None,
                    "display_value": "0.81",
                },
                "source": "explicit_dag_bound_report_metadata_plus_execution_trace",
            }
        ],
    }
    text = render_report_markdown(report)
    assert "СП 554, раздел 10 — изгиб" in text
    assert "SP554_C_10_GOV" in text
    assert "γT,gov" in text
    assert "0.81" in text
    assert "не вычисляет глобальный максимум/минимум" in text


def test_markdown_explains_declared_but_not_executed_governing_scope():
    report = _report()
    report["summary"]["governing"] = {
        "status": "DECLARED_BY_DAG_NOT_EXECUTED",
        "reason": "not reached",
        "candidates": [],
    }
    text = render_report_markdown(report)
    assert "producer-узлы ещё не выполнены" in text


def test_markdown_renders_fail_closed_without_mutating_it():
    report = _report()
    failure = {
        "report_block_id": "FAIL:T#1",
        "owner_node_id": "T",
        "owner_standard_id": "SP554",
        "sequence": 4,
        "kind": "FAIL_CLOSED",
        "title": "Кручение в пожаре",
        "normative_refs": [{"standard_id": "SP554", "section": "9"}],
        "inputs": [],
        "outputs": [],
        "execution_spec": {"mode": "node_metadata_only"},
        "execution_evidence": {},
        "human_readable": {"mode": "trace_values"},
        "message": "general torsion route unsupported",
        "failure": {"status": "UNSUPPORTED", "quantity_id": "T"},
    }
    report["blocks"].append(failure)
    report["block_count"] = 3
    report["sections"].append({"section_key": "audit", "title_ru": "Диагностика", "block_ids": ["FAIL:T#1"]})
    report["summary"]["summary_status"] = "FAIL_CLOSED"
    report["summary"]["fail_closed_count"] = 1
    report["summary"]["fail_closed"] = [
        {
            "report_block_id": "FAIL:T#1",
            "sequence": 4,
            "owner_node_id": "T",
            "owner_standard_id": "SP554",
            "title": "Кручение в пожаре",
            "normative_refs": [{"standard_id": "SP554", "section": "9"}],
            "message": "general torsion route unsupported",
            "failure": {"status": "UNSUPPORTED", "quantity_id": "T"},
        }
    ]
    before = copy.deepcopy(report)
    text = render_report_markdown(report)
    assert report == before
    assert "FAIL-CLOSED" in text
    assert "general torsion route unsupported" in text
    assert '"quantity_id": "T"' in text


def test_markdown_rejects_non_ir5_source():
    report = _report()
    report["schema"] = "fire_report_ir_v3"
    try:
        render_report_markdown(report)
    except ValueError as exc:
        assert "fire_report_ir_v4" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_markdown_escapes_pipe_in_table_cells():
    report = _report()
    report["summary"]["checks"][0]["title"] = "N | M check"
    text = render_report_markdown(report)
    assert "N \\| M check" in text
