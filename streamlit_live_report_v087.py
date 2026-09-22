"""v0.87 LIVE-REPORT1: dedicated trace-bound engineering report pane.

This is presentation-only. It never evaluates engineering expressions, runs DAG
nodes, performs table interpolation, or infers PASS/FAIL from numeric values.
The pane is rebuilt from REPORT-IR5 after each accepted guided-calculation step.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from standard_core.report_ir5 import build_report_ir5
from standard_core.report_markdown import render_report_markdown
import streamlit_report_ui_impl as _report_ui


_STATUS_RU = {
    "FAIL_CLOSED": "Расчёт остановлен fail-closed",
    "EXECUTED_CHECK_FAILED": "Есть невыполненная нормативная проверка",
    "CHECK_VERDICT_NOT_EXPLICIT": "Часть проверок не имеет явного boolean-вердикта",
    "EXECUTED_BOOLEAN_CHECKS_PASS": "Все выполненные boolean-проверки пройдены",
    "NO_COMPLETED_CHECKS_YET": "Нормативные проверки ещё не выполнены",
}


def _normative_reference_text(ref: Mapping[str, Any]) -> str:
    """Render every explicit normative locator carried by the execution block."""
    standard = ref.get("standard_id") or ref.get("document_id") or "Норма"
    parts = [str(standard)]
    fields = (
        ("section", "разд."),
        ("clause", "п."),
        ("formula_ref", "формула"),
        ("table_ref", "табл."),
        ("figure_ref", "рис."),
        ("appendix_ref", "прил."),
    )
    for key, label in fields:
        value = ref.get(key)
        if value not in (None, ""):
            parts.append(f"{label} {value}")
    return " · ".join(parts)


def _refs_text(refs: Any) -> str:
    rows = [_normative_reference_text(ref) for ref in refs or [] if isinstance(ref, Mapping)]
    return "; ".join(dict.fromkeys(row for row in rows if row))


def _report_view_model(report: Mapping[str, Any]) -> dict[str, Any]:
    """Create a presentation index only; numerical content remains untouched."""
    blocks = [row for row in report.get("blocks") or [] if isinstance(row, Mapping)]
    by_id = {
        str(row.get("report_block_id")): row
        for row in blocks
        if isinstance(row.get("report_block_id"), str)
    }
    sections: list[dict[str, Any]] = []
    for section in report.get("sections") or []:
        if not isinstance(section, Mapping):
            continue
        ids = [str(x) for x in section.get("block_ids") or [] if str(x) in by_id]
        if ids:
            sections.append(
                {
                    "section_key": section.get("section_key"),
                    "title": section.get("title_ru") or section.get("section_key") or "Раздел",
                    "block_ids": ids,
                }
            )

    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    verdicts: dict[str, str] = {}
    for row in summary.get("checks") or []:
        if isinstance(row, Mapping) and isinstance(row.get("report_block_id"), str):
            verdicts[str(row["report_block_id"])] = str(row.get("verdict") or "UNRESOLVED")

    return {
        "blocks": blocks,
        "by_id": by_id,
        "sections": sections,
        "latest_block": blocks[-1] if blocks else None,
        "verdicts": verdicts,
        "summary": summary,
    }


def _render_verdict(st: Any, verdict: str | None) -> None:
    if verdict == "PASS":
        st.success("Нормативная проверка: PASS")
    elif verdict == "FAIL":
        st.error("Нормативная проверка: FAIL")
    elif verdict == "UNRESOLVED":
        st.warning("Вердикт проверки не объявлен однозначно в execution trace.")


def _render_latest(core: Any, view: Mapping[str, Any]) -> None:
    st = core.st
    block = view.get("latest_block")
    if not isinstance(block, Mapping):
        st.info("Живой отчёт начнёт заполняться после первого принятого расчётного шага.")
        return
    st.markdown("#### Последний выполненный шаг")
    st.caption(
        "Этот блок обновляется после успешной валидации ответа и выполнения соответствующего DAG-маршрута."
    )
    _render_verdict(st, (view.get("verdicts") or {}).get(str(block.get("report_block_id"))))
    with st.container(border=True):
        _report_ui._render_block(core, block)


def _render_full_document(core: Any, report: Mapping[str, Any], view: Mapping[str, Any]) -> None:
    st = core.st
    if not view.get("blocks"):
        return
    st.markdown("#### Полный расчётный протокол")
    st.caption(
        "Формулы, подстановки, результаты и нормативные ссылки ниже являются представлением REPORT-IR5 "
        "для фактически выполненного execution trace."
    )
    with st.container(height=900, border=True):
        for section in view.get("sections") or []:
            st.markdown(f"### {section.get('title')}")
            for block_id in section.get("block_ids") or []:
                block = (view.get("by_id") or {}).get(str(block_id))
                if not isinstance(block, Mapping):
                    continue
                _render_verdict(st, (view.get("verdicts") or {}).get(str(block_id)))
                _report_ui._render_block(core, block)
                st.divider()

        st.caption(
            f"REPORT-IR5 · `{report.get('report_sha256')}` · "
            f"blocks {report.get('block_count', len(view.get('blocks') or []))}"
        )


def _render_summary_export(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    status = str(summary.get("summary_status") or "")
    message = _STATUS_RU.get(status, status or "—")
    if status in {"FAIL_CLOSED", "EXECUTED_CHECK_FAILED"}:
        st.error(message)
    elif status == "CHECK_VERDICT_NOT_EXPLICIT":
        st.warning(message)
    elif status == "EXECUTED_BOOLEAN_CHECKS_PASS":
        st.success(message)
    else:
        st.info(message)

    counts = summary.get("check_counts") if isinstance(summary.get("check_counts"), Mapping) else {}
    c1, c2 = st.columns(2)
    c1.metric("Проверок", summary.get("check_count", 0))
    c2.metric("PASS", counts.get("PASS", 0))
    c3, c4 = st.columns(2)
    c3.metric("FAIL", counts.get("FAIL", 0))
    c4.metric("Неоднозначно", counts.get("UNRESOLVED", 0))

    markdown = render_report_markdown(report)
    st.download_button(
        "Скачать текущий отчёт (.md)",
        data=markdown,
        file_name="fire_resistance_calculation_report.md",
        mime="text/markdown",
        width="stretch",
        on_click="ignore",
        key="fire:live-report-v087:download:markdown",
    )
    st.download_button(
        "Скачать текущий Report IR (.json)",
        data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        file_name="fire_report_ir_v4.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
        key="fire:live-report-v087:download:ir",
    )
    st.caption(
        "Экспорт и экран строятся из одного REPORT-IR5. Presentation-слой не выполняет повторный инженерный расчёт."
    )


def _render_audit(core: Any, report: Mapping[str, Any], env: Mapping[str, Any]) -> None:
    st = core.st
    st.caption(
        "Диагностические данные отделены от инженерного текста, чтобы raw ledger/trace не перегружали основной отчёт."
    )
    with st.expander("Report identity", expanded=False):
        st.json(
            {
                "schema": report.get("schema"),
                "contract": report.get("contract"),
                "report_sha256": report.get("report_sha256"),
                "session_status": report.get("session_status"),
                "block_count": report.get("block_count"),
            }
        )
    state = env.get("state") if isinstance(env.get("state"), Mapping) else {}
    with st.expander("Quantity ledger", expanded=False):
        st.json(state.get("ledger") or [])
    with st.expander("Execution trace", expanded=False):
        st.json(state.get("trace") or [])
    if state.get("branch_failures"):
        with st.expander("Branch failures", expanded=False):
            st.json(state.get("branch_failures"))


def render_live_report(core: Any, env: Mapping[str, Any]) -> None:
    """Render the current session as one dedicated right-hand engineering pane."""
    st = core.st
    app = st.session_state.get("_fire_app")
    sid = st.session_state.get("_fire_session_id")
    if app is None or not sid or sid not in app.service.sessions:
        st.info("Расчётная сессия ещё не создана.")
        return

    session = app.service.get_session(sid)
    report = build_report_ir5(app.service.model, session)
    view = _report_view_model(report)

    # Existing trace-bound block renderer is intentionally reused. Only the
    # locator formatter is upgraded so all explicit clause/formula/table refs
    # carried by REPORT-IR are visible in the live pane.
    _report_ui._refs_text = _refs_text

    st.markdown("### Живой расчётный отчёт")
    st.caption(
        "Справа отображается текущее принятое состояние расчёта. Изменение предыдущего ответа переигрывает DAG, "
        "после чего этот отчёт полностью строится заново из нового execution trace."
    )
    tab_report, tab_summary, tab_audit = st.tabs(["Отчёт", "Сводка / экспорт", "Audit"])
    with tab_report:
        _render_latest(core, view)
        _render_full_document(core, report, view)
    with tab_summary:
        _render_summary_export(core, report)
    with tab_audit:
        _render_audit(core, report, env)


def install(core: Any) -> None:
    """Install LIVE-REPORT1 as the final right-pane renderer."""
    if getattr(core, "_fire_live_report_v087_installed", False):
        return
    core._fire_live_report_v087_installed = True

    # Keep a rollback/debug handle but deliberately do not call the stacked
    # legacy Summary -> Report -> Ledger wrapper in the normal v0.87 pane.
    core._fire_live_report_v087_previous_renderer = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        render_live_report(core, env)

    core._render_ledger_trace = _render_ledger_trace


__all__ = [
    "install",
    "render_live_report",
    "_refs_text",
    "_normative_reference_text",
    "_report_view_model",
]
