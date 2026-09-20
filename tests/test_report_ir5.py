from __future__ import annotations

import copy

import standard_core.report_ir5 as report_ir5


def _block(kind: str, node: str, outputs=None, **extra):
    row = {
        "report_block_id": f"{node}#1",
        "owner_node_id": node,
        "owner_standard_id": "TEST_STD",
        "sequence": 1,
        "kind": kind,
        "title": node,
        "normative_refs": [{"standard_id": "TEST_STD", "section": "1"}],
        "outputs": outputs or [],
    }
    row.update(extra)
    return row


def _value(qid: str, value, unit=None):
    return {
        "quantity_id": qid,
        "symbol": qid,
        "name_ru": qid,
        "raw_value": value,
        "canonical_unit": unit,
    }


def _ir4(blocks):
    return {
        "schema": "fire_report_ir_v3",
        "contract": "human_readable_trace_projection_v3",
        "report_sha256": "a" * 64,
        "graph_id": "g",
        "graph_sha256": "b" * 64,
        "session_schema": "s",
        "session_status": "WAITING",
        "entry_node_id": "A",
        "current_node_id": "B",
        "block_count": len(blocks),
        "blocks": copy.deepcopy(blocks),
        "sections": [],
        "selected_route": [{"selected_edge_id": "E1"}],
        "dag_census": {},
        "audit": {
            "calculation_values_recomputed_by_report": False,
            "formula_expressions_evaluated_by_report": False,
            "table_interpolation_recomputed_by_report": False,
            "route_conditions_recomputed_by_report": False,
            "numeric_substitution_is_text_only": True,
        },
    }


def test_summary_reads_explicit_boolean_check_outputs_only():
    source = _ir4(
        [
            _block("CHECK", "C1", [_value("ok1", True)]),
            _block("CHECK", "C2", [_value("ok2", False)]),
            _block("CHECK", "C3", [_value("eta", 0.72)]),
        ]
    )
    summary = report_ir5._summary_from_ir4(source)
    assert [row["verdict"] for row in summary["checks"]] == ["PASS", "FAIL", "UNRESOLVED"]
    assert summary["check_counts"] == {"PASS": 1, "FAIL": 1, "UNRESOLVED": 1}
    assert summary["summary_status"] == "EXECUTED_CHECK_FAILED"


def test_fail_closed_has_precedence_and_is_preserved_verbatim():
    source = _ir4(
        [
            _block("CHECK", "C1", [_value("ok", True)]),
            _block(
                "FAIL_CLOSED",
                "FIRE_T",
                [],
                message="torsion route unsupported",
                failure={"status": "UNSUPPORTED", "reason": "T"},
            ),
        ]
    )
    summary = report_ir5._summary_from_ir4(source)
    assert summary["summary_status"] == "FAIL_CLOSED"
    assert summary["fail_closed_count"] == 1
    assert summary["fail_closed"][0]["message"] == "torsion route unsupported"
    assert summary["fail_closed"][0]["failure"]["reason"] == "T"


def test_result_blocks_are_summarized_without_changing_values_or_units():
    source = _ir4([_block("RESULT", "R", [_value("theta_cr", 583.25, "degC")])])
    summary = report_ir5._summary_from_ir4(source)
    assert summary["result_block_count"] == 1
    value = summary["results"][0]["outputs"][0]
    assert value["raw_value"] == 583.25
    assert value["canonical_unit"] == "degC"
    assert value["display_value"] == "583.25 degC"


def test_governing_result_is_not_guessed_from_numeric_outputs():
    source = _ir4([_block("CHECK", "C", [_value("eta", 0.999)])])
    summary = report_ir5._summary_from_ir4(source)
    assert summary["governing"]["status"] == "NOT_DECLARED_BY_DAG"
    assert summary["governing"]["candidates"] == []
    assert summary["checks"][0]["verdict"] == "UNRESOLVED"


def test_build_report_ir5_wraps_ir4_deterministically_and_freezes_audit_flags(monkeypatch):
    source = _ir4([_block("CHECK", "C", [_value("ok", True)])])
    monkeypatch.setattr(report_ir5, "build_report_ir4", lambda model, session: copy.deepcopy(source))

    first = report_ir5.build_report_ir5(object(), object())
    second = report_ir5.build_report_ir5(object(), object())
    assert first == second
    assert first["schema"] == "fire_report_ir_v4"
    assert first["contract"] == "conservative_engineering_summary_v4"
    assert first["source_report_schema"] == "fire_report_ir_v3"
    assert first["summary"]["summary_status"] == "EXECUTED_BOOLEAN_CHECKS_PASS"
    assert first["audit"]["summary_recomputed_engineering_checks"] is False
    assert first["audit"]["summary_inferred_numeric_check_verdicts"] is False
    assert first["audit"]["summary_inferred_governing_result"] is False
