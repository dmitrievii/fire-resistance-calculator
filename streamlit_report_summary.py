"""Conservative REPORT-IR5 summary and REPORT-IR7 readiness panel for Streamlit."""
from __future__ import annotations

import json
from typing import Any, Mapping

from standard_core.report_ir5 import build_report_ir5
from standard_core.report_markdown import render_report_markdown
from standard_core.report_readiness import build_report_readiness


_STATUS_RU = {
    "FAIL_CLOSED": "Расчёт остановлен fail-closed",
    "EXECUTED_CHECK_FAILED": "Есть невыполненная проверка",
    "CHECK_VERDICT_NOT_EXPLICIT": "Часть проверок не имеет явного boolean-вердикта",
    "EXECUTED_BOOLEAN_CHECKS_PASS": "Все выполненные boolean-проверки пройдены",
    "NO_COMPLETED_CHECKS_YET": "Проверки ещё не выполнены",
}


def _refs_text(refs: Any) -> str:
    out = []
    for ref in refs or []:
        if not isinstance(ref, Mapping):
            continue
        standard = ref.get("standard_id") or ""
        section = ref.get("section") or ref.get("clause") or ""
        text = " ".join(str(x) for x in (standard, section) if x)
        if text:
            out.append(text)
    return "; ".join(out)


def _render_readiness(core: Any, readiness: Mapping[str, Any]) -> None:
    st = core.st
    verdict = readiness.get("check_verdict_readiness") or {}
    governing = readiness.get("governing_readiness") or {}
    blockers = readiness.get("blocking_metadata_gaps") or []

    with st.expander("Готовность нормативного DAG к полному расчётному отчёту", expanded=False):
        status = readiness.get("status")
        if status == "REPORT_METADATA_COMPLETE":
            st.success("Метаданные отчёта достаточны для однозначной публикационной сводки.")
        else:
            st.warning(
                "Отчёт уже воспроизводит выполненный расчёт, но часть итоговой семантики пока нельзя "
                "формировать без явных метаданных нормативного DAG."
            )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Узлов DAG", readiness.get("node_count", 0))
        c2.metric("CHECK без явного verdict", verdict.get("needs_explicit_verdict_count", 0))
        c3.metric("Governing", "объявлен" if governing.get("status") == "DECLARED" else "не объявлен")
        c4.metric("Блокирующих gaps", readiness.get("blocking_metadata_gap_count", 0))

        if blockers:
            st.dataframe(
                [
                    {
                        "Тип": row.get("kind"),
                        "Узел": row.get("node_id") or "—",
                        "Причина": row.get("message"),
                    }
                    for row in blockers
                ],
                width="stretch",
                hide_index=True,
            )

        refs = readiness.get("normative_reference_coverage") or {}
        presentation = readiness.get("presentation_metadata_coverage") or {}
        st.caption(
            f"Нормативные ссылки: {refs.get('nodes_with_refs', 0)}/{readiness.get('node_count', 0)} узлов; "
            f"явный report_spec: {presentation.get('nodes_with_report_spec', 0)}/{readiness.get('node_count', 0)}. "
            "Отсутствие formula_latex не блокирует trace-отчёт: expression из frozen DAG всё равно показывается дословно."
        )
        st.download_button(
            "Скачать census готовности (.json)",
            data=json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            file_name="fire_report_readiness_v1.json",
            mime="application/json",
            width="stretch",
            on_click="ignore",
            key="fire:report:download:readiness",
        )
        st.caption(
            "Этот census анализирует только метаданные DAG. Он не запускает расчёт, не читает значения сессии "
            "и не является оценкой инженерной готовности расчётного комплекса."
        )


def _render_summary(core: Any, report: Mapping[str, Any], readiness: Mapping[str, Any]) -> None:
    st = core.st
    summary = report.get("summary") or {}
    status = str(summary.get("summary_status") or "")

    st.markdown("### Итоговая расчётная сводка")
    message = _STATUS_RU.get(status, status or "—")
    if status == "FAIL_CLOSED":
        st.error(message)
    elif status == "EXECUTED_CHECK_FAILED":
        st.error(message)
    elif status == "CHECK_VERDICT_NOT_EXPLICIT":
        st.warning(message)
    elif status == "EXECUTED_BOOLEAN_CHECKS_PASS":
        st.success(message)
    else:
        st.info(message)

    counts = summary.get("check_counts") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Проверок", summary.get("check_count", 0))
    c2.metric("PASS", counts.get("PASS", 0))
    c3.metric("FAIL", counts.get("FAIL", 0))
    c4.metric("Неоднозначно", counts.get("UNRESOLVED", 0))

    markdown = render_report_markdown(report)
    d1, d2 = st.columns(2)
    d1.download_button(
        "Скачать расчётный отчёт (.md)",
        data=markdown,
        file_name="fire_resistance_calculation_report.md",
        mime="text/markdown",
        width="stretch",
        on_click="ignore",
        key="fire:report:download:markdown",
    )
    d2.download_button(
        "Скачать полный Report IR (.json)",
        data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        file_name="fire_report_ir_v4.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
        key="fire:report:download:ir5",
    )

    checks = summary.get("checks") or []
    if checks:
        st.markdown("**Выполненные проверки**")
        st.dataframe(
            [
                {
                    "Шаг": row.get("sequence"),
                    "Проверка": row.get("title"),
                    "Норма": _refs_text(row.get("normative_refs")),
                    "Вердикт": row.get("verdict"),
                    "Результат": "; ".join(
                        f"{out.get('symbol') or out.get('quantity_id')} = {out.get('display_value')}"
                        for out in row.get("outputs") or []
                    ),
                }
                for row in checks
            ],
            width="stretch",
            hide_index=True,
        )

    results = summary.get("results") or []
    if results:
        st.markdown("**Итоговые result-узлы**")
        for row in results:
            st.markdown(f"**{row.get('title') or row.get('owner_node_id')}**")
            for output in row.get("outputs") or []:
                st.markdown(
                    f"{output.get('symbol') or output.get('quantity_id')} = `{output.get('display_value')}`"
                )

    failures = summary.get("fail_closed") or []
    if failures:
        st.markdown("**Fail-closed ограничения активного маршрута**")
        for row in failures:
            st.error(f"{row.get('title') or row.get('owner_node_id')}: {row.get('message') or 'blocked'}")

    governing = summary.get("governing") or {}
    if governing.get("status") == "NOT_DECLARED_BY_DAG":
        st.caption(
            "Governing utilization пока намеренно не выбирается отчётом: он будет показан только после "
            "явного объявления governing quantity в нормативном DAG, без эвристики по именам или значениям."
        )
    st.caption(
        "Сводка описывает только реально выполненные trace-проверки. Она не заменяет нормативный verdict "
        "и не интерпретирует числовые коэффициенты как PASS/FAIL без явного boolean-результата."
    )
    _render_readiness(core, readiness)


def install(core: Any) -> None:
    """Render the calculation summary and static report-readiness census."""
    if getattr(core, "_fire_report_summary_installed", False):
        return
    core._fire_report_summary_installed = True

    st = core.st
    original = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        app = st.session_state.get("_fire_app")
        sid = st.session_state.get("_fire_session_id")
        if app is not None and sid and sid in app.service.sessions:
            session = app.service.get_session(sid)
            report = build_report_ir5(app.service.model, session)
            readiness = build_report_readiness(app.service.model)
            _render_summary(core, report, readiness)
            st.caption(f"REPORT-IR5 summary · `{report.get('report_sha256')}` · REPORT-IR7 readiness")
        original(env)

    core._render_ledger_trace = _render_ledger_trace
