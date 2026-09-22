"""v0.88 LIVE-REPORT2: expertise-style engineering calculation report.

Presentation-only layer. All numerical values, formulas, route choices and
verdicts come from REPORT-IR5 / execution trace. This module never re-runs
engineering calculations or infers PASS/FAIL from numeric values.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping

from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir5 import build_report_ir5
import streamlit_live_report_v087 as _v087


_SECTION_DEFS = (
    (
        "input",
        "1. Исходные данные",
        "В разделе приведены исходные характеристики элемента, материала и геометрии, "
        "принятые для текущего расчётного маршрута.",
    ),
    (
        "assumptions",
        "2. Расчётная схема и принятые предпосылки",
        "Ниже зафиксированы расчётные предпосылки и нормативные ветви, фактически "
        "принятые в текущем расчёте.",
    ),
    (
        "sp16",
        "3. Проверка стального элемента по СП 16",
        "Проверки при нормальной температуре выполняются по тем положениям СП 16, "
        "которые были активированы фактическим сочетанием усилий, геометрией и "
        "расчётной схемой элемента.",
    ),
    (
        "sp554",
        "4. Расчёт огнестойкости по СП 554",
        "После завершения требуемых проверок механического состояния выполняется "
        "расчёт огнестойкости по фактически выбранной ветви СП 554.",
    ),
    (
        "results",
        "5. Результаты и заключение",
        "В разделе приведены итоговые result-узлы и формальные выводы выполненных "
        "нормативных проверок.",
    ),
    (
        "other",
        "6. Дополнительные расчётные положения",
        "В разделе приведены выполненные шаги, которые не относятся однозначно к "
        "основным разделам СП 16 или СП 554.",
    ),
)

_INTERNAL_TITLE = re.compile(r"^[A-ZА-Я0-9_:\-.]+$")


def _display_value(row: Mapping[str, Any]) -> str:
    value = row.get("display_value")
    if value not in (None, ""):
        return str(value)
    raw = row.get("raw_value")
    if isinstance(raw, bool):
        text = "Да" if raw else "Нет"
    elif raw is None:
        text = "—"
    else:
        text = str(raw)
    unit = row.get("canonical_unit")
    return f"{text} {unit}" if unit and unit != "1" else text


def _clean_title(block: Mapping[str, Any]) -> str:
    title = str(block.get("title") or "").strip()
    if title and not _INTERNAL_TITLE.fullmatch(title):
        return title
    outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
    if outputs:
        name = outputs[0].get("name_ru")
        if isinstance(name, str) and name.strip():
            return str(name).strip()
    kind = str(block.get("kind") or "")
    fallback = {
        "CHECK": "Нормативная проверка",
        "FORMULA": "Определение расчётной величины",
        "LOOKUP": "Определение величины по нормативным данным",
        "DECISION": "Принятое расчётное решение",
        "RESULT": "Результат расчёта",
        "WARNING": "Расчётное замечание",
        "FAIL_CLOSED": "Ограничение расчётного маршрута",
    }
    return fallback.get(kind, "Расчётный шаг")


def _standard_family(block: Mapping[str, Any]) -> str:
    candidates: list[str] = []
    owner = block.get("owner_standard_id")
    if owner:
        candidates.append(str(owner))
    for ref in block.get("normative_refs") or []:
        if isinstance(ref, Mapping):
            value = ref.get("standard_id") or ref.get("document_id")
            if value:
                candidates.append(str(value))
    text = " ".join(candidates).upper().replace(" ", "")
    if "554" in text:
        return "sp554"
    if "16" in text and ("SP" in text or "СП" in text):
        return "sp16"
    return "other"


def _group_for_block(block: Mapping[str, Any]) -> str | None:
    section_key = str(block.get("section_key") or "")
    kind = str(block.get("kind") or "")
    if section_key == "audit":
        return None
    if section_key in {"input_data", "geometry"}:
        return "input"
    if section_key == "routing_and_assumptions":
        return "assumptions"
    if section_key == "results" or kind == "RESULT":
        return "results"
    family = _standard_family(block)
    if family in {"sp16", "sp554"}:
        return family
    return "other"


def compose_expertise_sections(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Group already-produced report blocks into expertise-style chapters."""
    grouped: dict[str, list[Mapping[str, Any]]] = {key: [] for key, _, _ in _SECTION_DEFS}
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        key = _group_for_block(block)
        if key:
            grouped[key].append(block)

    result: list[dict[str, Any]] = []
    for key, title, intro in _SECTION_DEFS:
        blocks = grouped[key]
        if blocks:
            result.append({"key": key, "title": title, "intro": intro, "blocks": blocks})
    return result


def _scalar_rows(rows: Any) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        raw = row.get("raw_value")
        if isinstance(raw, (dict, list, tuple)):
            continue
        result.append(row)
    return result


def _verdict_map(report: Mapping[str, Any]) -> dict[str, str]:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    result: dict[str, str] = {}
    for row in summary.get("checks") or []:
        if not isinstance(row, Mapping):
            continue
        block_id = row.get("report_block_id")
        if isinstance(block_id, str):
            result[block_id] = str(row.get("verdict") or "UNRESOLVED")
    return result


def _normative_basis(block: Mapping[str, Any]) -> str:
    return _v087._refs_text(block.get("normative_refs"))


def _purpose_text(block: Mapping[str, Any]) -> str:
    title = _clean_title(block)
    refs = _normative_basis(block)
    basis = f" в соответствии с {refs}" if refs else ""
    kind = str(block.get("kind") or "")
    if kind == "CHECK":
        return f"Выполняется проверка «{title}»{basis}."
    if kind == "FORMULA":
        return f"Для определения расчётной величины «{title}» используется нормативная зависимость{basis}."
    if kind == "LOOKUP":
        return f"Величина «{title}» определяется по нормативным табличным данным{basis}."
    if kind == "DECISION":
        return f"Для дальнейшего расчёта принято расчётное положение «{title}»{basis}."
    if kind == "RESULT":
        return f"По результатам выполненного расчётного маршрута получен результат «{title}»."
    if kind == "FAIL_CLOSED":
        return f"Расчётный маршрут «{title}» остановлен из-за ограничения применимости реализованной методики."
    if kind == "WARNING":
        return f"Для шага «{title}» зафиксировано расчётное замечание."
    return f"Выполнен расчётный шаг «{title}»{basis}."


def _conclusion_text(block: Mapping[str, Any], verdict: str | None) -> str | None:
    title = _clean_title(block)
    if verdict == "PASS":
        return f"Вывод: условие «{title}» выполняется."
    if verdict == "FAIL":
        return f"Вывод: условие «{title}» не выполняется."
    if verdict == "UNRESOLVED":
        return (
            f"Вывод: для проверки «{title}» итоговый вывод не зафиксирован однозначно; "
            "отчёт не определяет его самостоятельно по числовому значению."
        )
    kind = str(block.get("kind") or "")
    if kind == "RESULT":
        outputs = _scalar_rows(block.get("outputs"))
        if outputs:
            rendered = "; ".join(
                f"{row.get('symbol') or row.get('name_ru') or row.get('quantity_id')} = {_display_value(row)}"
                for row in outputs[:4]
            )
            return f"Результат расчёта: {rendered}."
    if kind == "DECISION":
        return "Принятое решение используется в последующих расчётных шагах."
    if kind == "FAIL_CLOSED":
        return "Дальнейший расчёт по данной ветви не выполняется до устранения указанного ограничения."
    return None


def _render_values(st: Any, rows: Any, heading: str) -> None:
    scalar = _scalar_rows(rows)
    if not scalar:
        return
    st.markdown(f"**{heading}**")
    for row in scalar:
        name = row.get("name_ru") or row.get("quantity_id") or "Величина"
        symbol = row.get("symbol")
        symbol_text = f" ({symbol})" if symbol and symbol != name else ""
        st.markdown(f"- {name}{symbol_text}: **{_display_value(row)}**")


def _render_lookup(st: Any, block: Mapping[str, Any]) -> bool:
    human = block.get("human_readable") if isinstance(block.get("human_readable"), Mapping) else {}
    if human.get("mode") != "lookup_substitution":
        return False
    shown = False
    for row in human.get("output_lines") or []:
        if not isinstance(row, Mapping):
            continue
        formula = row.get("formula_expression")
        substitution = row.get("substituted_expression")
        if formula:
            st.markdown("**Нормативная зависимость / интерполяция**")
            st.code(str(formula), language="text")
            shown = True
        if substitution:
            st.markdown("**Подстановка**")
            st.code(str(substitution), language="text")
            shown = True
        if row.get("display_result") not in (None, "", "—"):
            st.markdown(f"**Получено:** {row.get('symbol') or row.get('quantity_id')} = `{row['display_result']}`")
            shown = True
    return shown


def _render_expertise_block(
    core: Any,
    block: Mapping[str, Any],
    verdict: str | None,
    *,
    compact: bool = False,
) -> None:
    st = core.st
    title = _clean_title(block)
    st.markdown(("##### " if compact else "#### ") + title)
    st.write(_purpose_text(block))

    kind = str(block.get("kind") or "")
    if kind == "FAIL_CLOSED":
        st.error(block.get("message") or "Расчётная ветвь остановлена fail-closed.")
    elif kind == "WARNING":
        st.warning(block.get("message") or "Нормативная ветвь требует дополнительного внимания.")

    if kind not in {"DECISION", "RESULT"}:
        _render_values(st, block.get("inputs"), "Исходные величины")

    equation = build_trace_bound_equation(block)
    equation_rendered = False
    if equation:
        if equation.get("formula_latex"):
            st.markdown("**Расчётная формула**")
            st.latex(str(equation["formula_latex"]))
            equation_rendered = True
        substitution = equation.get("substitution_result_latex") or equation.get("substitution_latex")
        if substitution:
            st.markdown("**Подстановка и результат**")
            st.latex(str(substitution))
            equation_rendered = True
        if equation.get("missing_trace_bindings"):
            st.warning(
                "Для отображения полной подстановки не хватает trace bindings: "
                + ", ".join(str(x) for x in equation["missing_trace_bindings"])
            )

    if not equation_rendered:
        _render_lookup(st, block)

    outputs = _scalar_rows(block.get("outputs"))
    if outputs and (not equation_rendered or len(outputs) > 1):
        _render_values(st, outputs, "Результат")

    conclusion = _conclusion_text(block, verdict)
    if conclusion:
        if verdict == "PASS":
            st.success(conclusion)
        elif verdict == "FAIL":
            st.error(conclusion)
        elif verdict == "UNRESOLVED":
            st.warning(conclusion)
        else:
            st.markdown(f"**{conclusion}**")

    refs = _normative_basis(block)
    if refs:
        st.caption(f"Нормативное основание: {refs}")


def _report_status(st: Any, report: Mapping[str, Any]) -> None:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    status = str(summary.get("summary_status") or "")
    text = {
        "FAIL_CLOSED": "Текущий расчёт остановлен из-за ограничения применимости расчётного маршрута.",
        "EXECUTED_CHECK_FAILED": "В текущем расчёте имеется невыполненная нормативная проверка.",
        "CHECK_VERDICT_NOT_EXPLICIT": "Для части выполненных проверок итоговый вывод пока не зафиксирован однозначно.",
        "EXECUTED_BOOLEAN_CHECKS_PASS": "Все выполненные на текущем этапе нормативные проверки с явным итоговым условием пройдены.",
        "NO_COMPLETED_CHECKS_YET": "Нормативные проверки ещё не выполнены.",
    }.get(status, status or "Расчёт выполняется.")
    if status in {"FAIL_CLOSED", "EXECUTED_CHECK_FAILED"}:
        st.error(text)
    elif status == "CHECK_VERDICT_NOT_EXPLICIT":
        st.warning(text)
    elif status == "EXECUTED_BOOLEAN_CHECKS_PASS":
        st.success(text)
    else:
        st.info(text)


def render_expertise_markdown(report: Mapping[str, Any]) -> str:
    """Render the same evidence as a human-readable Markdown calculation report."""
    verdicts = _verdict_map(report)
    lines = [
        "# Расчёт огнестойкости стального элемента",
        "",
        "Расчётный отчёт сформирован по фактически выполненному нормативному маршруту.",
        "Числовые значения и результаты приведены по зафиксированным результатам расчёта без повторного вычисления.",
        "",
    ]
    for section in compose_expertise_sections(report):
        lines.extend([f"## {section['title']}", "", section["intro"], ""])
        for block in section["blocks"]:
            title = _clean_title(block)
            lines.extend([f"### {title}", "", _purpose_text(block), ""])
            inputs = _scalar_rows(block.get("inputs"))
            if inputs and str(block.get("kind") or "") not in {"DECISION", "RESULT"}:
                lines.append("**Исходные величины:**")
                for row in inputs:
                    name = row.get("name_ru") or row.get("quantity_id") or "Величина"
                    symbol = row.get("symbol")
                    symbol_text = f" ({symbol})" if symbol and symbol != name else ""
                    lines.append(f"- {name}{symbol_text}: **{_display_value(row)}**")
                lines.append("")

            equation = build_trace_bound_equation(block)
            if equation and equation.get("formula_latex"):
                lines.extend(["**Расчётная формула:**", "", f"$$ {equation['formula_latex']} $$", ""])
            if equation:
                substitution = equation.get("substitution_result_latex") or equation.get("substitution_latex")
                if substitution:
                    lines.extend(["**Подстановка и результат:**", "", f"$$ {substitution} $$", ""])
            else:
                human = block.get("human_readable") if isinstance(block.get("human_readable"), Mapping) else {}
                if human.get("mode") == "lookup_substitution":
                    for row in human.get("output_lines") or []:
                        if not isinstance(row, Mapping):
                            continue
                        if row.get("formula_expression"):
                            lines.extend(["**Нормативная зависимость / интерполяция:**", "", f"`{row['formula_expression']}`", ""])
                        if row.get("substituted_expression"):
                            lines.extend(["**Подстановка:**", "", f"`{row['substituted_expression']}`", ""])

            outputs = _scalar_rows(block.get("outputs"))
            if outputs and (not equation or len(outputs) > 1):
                lines.append("**Результат:**")
                for row in outputs:
                    lines.append(
                        f"- {row.get('name_ru') or row.get('symbol') or row.get('quantity_id')}: **{_display_value(row)}**"
                    )
                lines.append("")

            block_id = str(block.get("report_block_id") or "")
            conclusion = _conclusion_text(block, verdicts.get(block_id))
            if conclusion:
                lines.extend([f"**{conclusion}**", ""])
            refs = _normative_basis(block)
            if refs:
                lines.extend([f"*Нормативное основание: {refs}*", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_export(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    markdown = render_expertise_markdown(report)
    st.download_button(
        "Скачать расчётный отчёт (.md)",
        data=markdown,
        file_name="fire_resistance_expertise_report.md",
        mime="text/markdown",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v088:download:markdown",
    )
    st.download_button(
        "Скачать Report IR (.json)",
        data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        file_name="fire_report_ir_v4.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v088:download:ir",
    )
    st.caption(
        "Экранный и Markdown-отчёт формируются из одного REPORT-IR5; presentation-слой "
        "не выполняет повторный инженерный расчёт."
    )


def render_expertise_report(core: Any, env: Mapping[str, Any]) -> None:
    """Render a continuously updated, expertise-style calculation document."""
    st = core.st
    app = st.session_state.get("_fire_app")
    sid = st.session_state.get("_fire_session_id")
    if app is None or not sid or sid not in app.service.sessions:
        st.info("Расчётная сессия ещё не создана.")
        return

    session = app.service.get_session(sid)
    report = build_report_ir5(app.service.model, session)
    blocks = [row for row in report.get("blocks") or [] if isinstance(row, Mapping)]
    verdicts = _verdict_map(report)

    st.markdown("### Расчётный отчёт")
    st.caption(
        "Документ обновляется после каждого принятого шага. В основном тексте скрыты "
        "внутренние node/quantity/edge ID; полный trace остаётся во вкладке Audit."
    )
    tab_report, tab_export, tab_audit = st.tabs(["Расчётный отчёт", "Экспорт", "Audit"])

    with tab_report:
        _report_status(st, report)
        if blocks:
            with st.expander("Последнее изменение расчёта", expanded=True):
                latest = blocks[-1]
                _render_expertise_block(
                    core,
                    latest,
                    verdicts.get(str(latest.get("report_block_id") or "")),
                    compact=True,
                )
        else:
            st.info("Отчёт начнёт заполняться после первого принятого расчётного шага.")

        sections = compose_expertise_sections(report)
        if sections:
            with st.container(height=1050, border=True):
                st.markdown("## Расчёт огнестойкости стального элемента")
                st.write(
                    "Настоящий расчётный протокол формируется по фактически выполненному "
                    "нормативному маршруту. Для каждой применимой проверки приведены исходные "
                    "величины, нормативная формула, подстановка, результат и вывод."
                )
                for section in sections:
                    st.markdown(f"### {section['title']}")
                    st.write(section["intro"])
                    for block in section["blocks"]:
                        _render_expertise_block(
                            core,
                            block,
                            verdicts.get(str(block.get("report_block_id") or "")),
                        )
                        st.divider()

    with tab_export:
        _render_export(core, report)

    with tab_audit:
        _v087._render_audit(core, report, env)


def install(core: Any) -> None:
    """Install expertise renderer and widen the report pane without touching runtime."""
    if getattr(core, "_fire_expertise_report_v088_installed", False):
        return
    core._fire_expertise_report_v088_installed = True

    # Expand the usable desktop canvas without modifying the frozen calculation core.
    if isinstance(getattr(core, "STYLES", None), str):
        core.STYLES = core.STYLES.replace(
            "max-width: 1500px;",
            "max-width: 1800px;",
        )

    # Intercept only the one main 2-pane layout call from streamlit_app_core.main().
    # All form-, metric- and chart-level st.columns calls retain their original specs.
    original_columns = core.st.columns

    def _columns(spec: Any, *args: Any, **kwargs: Any):
        if isinstance(spec, (list, tuple)) and len(spec) == 2:
            try:
                pair = [float(spec[0]), float(spec[1])]
            except (TypeError, ValueError):
                pair = []
            if pair == [1.65, 1.0] and kwargs.get("gap") == "large":
                return original_columns([0.85, 1.15], *args, **kwargs)
        return original_columns(spec, *args, **kwargs)

    core._fire_expertise_report_v088_original_columns = original_columns
    core.st.columns = _columns

    core._fire_expertise_report_v088_previous_renderer = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        render_expertise_report(core, env)

    core._render_ledger_trace = _render_ledger_trace


__all__ = [
    "install",
    "render_expertise_report",
    "render_expertise_markdown",
    "compose_expertise_sections",
    "_group_for_block",
    "_conclusion_text",
]
