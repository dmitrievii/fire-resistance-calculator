from __future__ import annotations

from types import SimpleNamespace

import streamlit_expertise_report_v088 as v088


def _value(qid, value, unit=None, *, name=None, symbol=None):
    return {
        "quantity_id": qid,
        "name_ru": name or qid,
        "symbol": symbol or qid,
        "raw_value": value,
        "canonical_unit": unit,
        "display_value": f"{value} {unit}" if unit else str(value),
    }


def _block(block_id, *, section_key, kind, standard="SP16", title="Проверка устойчивости", verdict_q=None):
    outputs = [_value("eta", 0.72, "1", name="Коэффициент использования", symbol="eta")]
    presentation = {
        "formula_latex": r"\eta = \frac{N}{\varphi A R_y \gamma_c}",
        "substitution_template_latex": r"\eta = \frac{{N}}{{phi}\cdot{A}\cdot{Ry}\cdot{gc}}",
        "display_precision": 3,
    }
    if verdict_q:
        outputs.append(_value(verdict_q, True, None, name="Условие выполняется", symbol=verdict_q))
        presentation["verdict_quantity_id"] = verdict_q
    return {
        "report_block_id": block_id,
        "owner_node_id": "INTERNAL_NODE_SHOULD_NOT_RENDER",
        "owner_standard_id": standard,
        "section_key": section_key,
        "kind": kind,
        "title": title,
        "normative_refs": [
            {"standard_id": standard, "clause": "8.2.1", "formula_ref": "(8.4)"}
        ],
        "inputs": [
            _value("N", 600000.0, "N", name="Продольная сила", symbol="N"),
            _value("phi", 0.873, "1", name="Коэффициент продольного изгиба", symbol="phi"),
            _value("A", 10000.0, "mm2", name="Площадь сечения", symbol="A"),
            _value("Ry", 248.8, "MPa", name="Расчётное сопротивление", symbol="R_y"),
            _value("gc", 1.0, "1", name="Коэффициент условий работы", symbol="gamma_c"),
        ],
        "outputs": outputs,
        "presentation": presentation,
        "execution_evidence": {
            "bindings": [
                {"variable": "N", "raw_value": 600000.0, "present_in_trace": True},
                {"variable": "phi", "raw_value": 0.873, "present_in_trace": True},
                {"variable": "A", "raw_value": 10000.0, "present_in_trace": True},
                {"variable": "Ry", "raw_value": 248.8, "present_in_trace": True},
                {"variable": "gc", "raw_value": 1.0, "present_in_trace": True},
            ]
        },
    }


def test_expertise_sections_separate_sp16_sp554_and_results():
    report = {
        "blocks": [
            _block("b1", section_key="input_data", kind="INPUT", title="Исходные усилия"),
            _block("b2", section_key="verification", kind="CHECK", standard="SP16"),
            _block("b3", section_key="calculation", kind="FORMULA", standard="SP554", title="Критическая температура"),
            _block("b4", section_key="results", kind="RESULT", standard="SP554", title="Предел огнестойкости"),
        ]
    }
    sections = v088.compose_expertise_sections(report)
    keys = [row["key"] for row in sections]
    assert keys == ["input", "sp16", "sp554", "results"]
    titles = [row["title"] for row in sections]
    assert any("СП 16" in title for title in titles)
    assert any("СП 554" in title for title in titles)


def test_markdown_is_human_readable_and_uses_trace_bound_formula():
    block = _block(
        "check#1",
        section_key="verification",
        kind="CHECK",
        standard="SP16",
        verdict_q="check_pass",
    )
    report = {
        "blocks": [block],
        "summary": {
            "checks": [
                {
                    "report_block_id": "check#1",
                    "verdict": "PASS",
                }
            ]
        },
    }
    text = v088.render_expertise_markdown(report)
    assert "Проверка стального элемента по СП 16" in text
    assert "Расчётная формула" in text
    assert "Подстановка и результат" in text
    assert "условие «Проверка устойчивости» выполняется" in text
    assert "Нормативное основание: SP16 · п. 8.2.1 · формула (8.4)" in text
    assert "INTERNAL_NODE_SHOULD_NOT_RENDER" not in text
    assert "owner_node_id" not in text
    assert "selected_edge_id" not in text


def test_fail_and_unresolved_conclusions_are_not_numerically_inferred():
    block = _block("x", section_key="verification", kind="CHECK")
    assert "не выполняется" in v088._conclusion_text(block, "FAIL")
    unresolved = v088._conclusion_text(block, "UNRESOLVED")
    assert "не зафиксирован однозначно" in unresolved
    assert "не определяет его самостоятельно" in unresolved


def test_layout_overlay_widens_only_main_two_pane_columns():
    calls = []

    class FakeSt:
        def columns(self, spec, *args, **kwargs):
            calls.append((spec, args, kwargs))
            return spec

    core = SimpleNamespace(
        st=FakeSt(),
        STYLES='<style>.block-container {max-width: 1500px;}</style>',
        _render_ledger_trace=lambda env: None,
    )
    v088.install(core)

    main = core.st.columns([1.65, 1], gap="large")
    nested = core.st.columns([1, 1], gap="large")
    metrics = core.st.columns(3)

    assert main == [0.85, 1.15]
    assert nested == [1, 1]
    assert metrics == 3
    assert "max-width: 1800px;" in core.STYLES


def test_v088_is_presentation_only_by_contract():
    source = open("streamlit_expertise_report_v088.py", encoding="utf-8").read()
    assert "eval(" not in source
    assert "exec(" not in source
    assert "build_report_ir5" in source
    assert "build_trace_bound_equation" in source
    assert "app.service.submit" not in source
    assert "app.service.edit" not in source
