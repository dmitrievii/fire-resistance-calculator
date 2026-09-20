"""REPORT-IR5 summary and DAG report-readiness panel for Streamlit."""
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
        locator = ref.get("clause") or ref.get("section") or ref.get("table_ref") or ""
        text = " ".join(str(x) for x in (standard, locator) if x)
        if text:
            out.append(text)
    return "; ".join(out)


def _render_readiness(core: Any, readiness: Mapping[str, Any]) -> None:
    st = core.st
    verdict = readiness.get("check_verdict_readiness") or {}
    governing = readiness.get("governing_readiness") or {}
    blockers = readiness.get("blocking_metadata_gaps") or []
    metadata = readiness.get("report_metadata") or {}

    with st.expander("Готовность нормативного DAG к полному расчётному отчёту", expanded=False):
        status = readiness.get("status")
        if status == "REPORT_METADATA_COMPLETE":
            st.success("Метаданные отчёта достаточны для однозначной текущей report-семантики.")
        else:
            st.warning(
                "Отчёт воспроизводит выполненный расчёт, но часть итоговой семантики пока нельзя "
                "формировать без явных DAG-bound метаданных."
            )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Узлов DAG", readiness.get("node_count", 0))
        c2.metric("CHECK без verdict", verdict.get("needs_explicit_verdict_count", 0))
        if governing.get("status") == "DECLARED":
            c3.metric("Governing-области", governing.get("declaration_count", 0))
        else:
            c3.metric("Governing-области", "не объявлены")
        c4.metric("Блокирующих gaps", readiness.get("blocking_metadata_gap_count", 0))

        if governing.get("valid_declarations"):
            st.markdown("**Объявленные governing-области**")
            st.dataframe(
                [
                    {
                        "Область": row.get("scope_title_ru") or row.get("scope"),
                        "DAG node": row.get("node_id"),
                        "Quantity": row.get("quantity_id"),
                    }
                    for row in governing.get("valid_declarations") or []
                ],
                width="stretch",
                hide_index=True,
            )

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
            f"явный report_spec/sidecar: {presentation.get('nodes_with_report_spec', 0)}/{readiness.get('node_count', 0)}. "
            f"Report metadata: {metadata.get('revision_id') or 'inline only'}."
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
            "Census анализирует только DAG/report metadata: он не запускает расчёт, не читает значения сессии "
            "и не меняет frozen execution graph."
        )


def _render_governing(core: Any, governing: Mapping[str, Any]) -> None:
    st = core.st
    status = governing.get("status")
    rows = [row for row in governing.get("candidates") or [] if isinstance(row, Mapping)]
    if status == "EXECUTED_DECLARATIONS" and rows:
        st.markdown("**Управляющие нормативные величины**")
        st.dataframe(
            [
                {
                    "Область": row.get("scope_title_ru") or row.get("scope"),
                    "DAG node": row.get("owner_node_id"),
                    "Величина": (row.get("quantity") or {}).get("symbol") or (row.get("quantity") or {}).get("quantity_id"),
                    "Значение": (row.get("quantity") or {}).get("display_value"),
                    "Норма": _refs_text(row.get("normative_refs")),
                }
                for row in rows
            ],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Это независимые governing-области, явно объявленные DAG-bound metadata и фактически выполненные runtime. "
            "Отчёт не сравнивает их между собой и не вычисляет глобальный max/min."
        )
    elif status == "DECLARED_BY_DAG_NOT_EXECUTED":
        st.caption(
            "Governing-области объявлены DAG-bound metadata, но соответствующие producer-узлы ещё не выполнены "
            "на текущем маршруте."
        )
    else:
        st.caption(
            "Governing result не выбирается эвристически: без явной декларации в DAG-bound metadata он остаётся "
            "NOT_DECLARED_BY_DAG."
        )


def _render_summary(core: Any, report: Mapping[str, Any], readiness: Mapping[str, Any]) -> None:
    st = core.st
    summary = report.get("summary") or {}
    status = str(summary.get("summary_status") or "")

    st.markdown("### Итоговая расчётная сводка")
    message = _STATUS_RU.get(status, status or "—")
    if status in {"FAIL_CLOSED", "EXECUTED_CHECK_FAILED"}:
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

    _render_governing(core, summary.get("governing") or {})

    results = summary.get("results") or []
    if results:
        st.markdown("**Итоговые result-узлы**")
        for row in results:
            st.markdown(f"**{row.get('title') or row.get('owner_node_id')}**")
            for output in row.get("outputs") or []:
                st.markdown(f"{output.get('symbol') or output.get('quantity_id')} = `{output.get('display_value')}`")

    failures = summary.get("fail_closed") or []
    if failures:
        st.markdown("**Fail-closed ограничения активного маршрута**")
        for row in failures:
            st.error(f"{row.get('title') or row.get('owner_node_id')}: {row.get('message') or 'blocked'}")

    st.caption(
        "Сводка описывает только реально выполненные trace-проверки. Числовые коэффициенты не трактуются "
        "как PASS/FAIL без boolean verdict, а governing-величины не выбираются отчётом по величине."
    )
    _render_readiness(core, readiness)


def install(core: Any) -> None:
    """Render calculation summary plus static DAG report-readiness census."""
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
            rev = (readiness.get("report_metadata") or {}).get("revision_id") or "inline"
            st.caption(f"REPORT-IR5 · `{report.get('report_sha256')}` · report metadata `{rev}`")
        original(env)

    core._render_ledger_trace = _render_ledger_trace
