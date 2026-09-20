"""Live REPORT-IR2 presentation for Streamlit.

This module renders the report projection only. It does not run normative DAG
nodes, evaluate equations, or interpolate datasets.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from standard_core.report_ir2 import build_report_ir2


def _value_line(core: Any, row: Mapping[str, Any]) -> str:
    symbol = row.get("symbol") or row.get("quantity_id")
    unit = f" {row['canonical_unit']}" if row.get("canonical_unit") else ""
    return f"**{symbol}** = `{core._fmt(row.get('raw_value'))}{unit}`"


def _render_block(core: Any, block: Mapping[str, Any], *, expanded: bool = False) -> None:
    st = core.st
    kind = str(block.get("kind") or "STEP")
    sequence = block.get("sequence")
    title = str(block.get("title") or block.get("owner_node_id") or "Расчётный шаг")
    label = f"{sequence}. [{kind}] {title}"
    with st.expander(label, expanded=expanded):
        st.caption(
            f"DAG node: {block.get('owner_node_id')} · standard: {block.get('owner_standard_id') or '—'}"
        )
        core._refs({"normative_refs": block.get("normative_refs") or []})

        if block.get("kind") == "FAIL_CLOSED":
            st.error(block.get("message") or "Ветвь остановлена fail-closed.")
            if block.get("failure"):
                st.json(block["failure"], expanded=False)
            return

        inputs = list(block.get("inputs") or [])
        if inputs:
            st.markdown("**Исходные величины этого шага**")
            for row in inputs:
                st.markdown(_value_line(core, row))

        spec = block.get("execution_spec") or {}
        evidence = block.get("execution_evidence") or {}
        mode = spec.get("mode")
        if mode in {"calculation_spec", "check_spec"}:
            expression = spec.get("expression")
            if expression:
                st.markdown("**Формула из DAG**")
                st.code(str(expression), language=None)
            bindings = evidence.get("bindings") or []
            if bindings:
                st.markdown("**Подстановка — значения из execution trace**")
                rows = []
                for row in bindings:
                    rows.append(
                        {
                            "Переменная": row.get("variable"),
                            "Quantity": row.get("quantity_id"),
                            "Значение": core._fmt(row.get("raw_value")) if row.get("present_in_trace") else "—",
                            "Ед.": row.get("canonical_unit") or "",
                        }
                    )
                st.dataframe(rows, width="stretch", hide_index=True)
        elif mode == "lookup_spec":
            st.markdown(f"**Dataset:** `{spec.get('dataset_id')}`")
            interpolation = spec.get("interpolation") or {}
            st.caption(
                f"Метод: {interpolation.get('method') or 'none'}"
                + (f" · ось: {interpolation.get('axis')}" if interpolation.get("axis") else "")
            )
            selectors = evidence.get("selectors") or []
            if selectors:
                st.markdown("**Селекторы таблицы / интерполяции**")
                st.dataframe(
                    [
                        {
                            "Поле dataset": row.get("dataset_field"),
                            "Quantity": row.get("quantity_id"),
                            "Значение": core._fmt(row.get("raw_value")) if row.get("present_in_trace") else "—",
                            "Ед.": row.get("canonical_unit") or "",
                        }
                        for row in selectors
                    ],
                    width="stretch",
                    hide_index=True,
                )
            if evidence.get("selected_dataset_rows_status") == "NOT_CAPTURED_BY_RUNTIME_YET":
                st.info(
                    "REPORT-IR2 пока намеренно не восстанавливает строки интерполяции повторным расчётом. "
                    "Точные нижняя/верхняя строки должны быть записаны самим runtime executor в следующем gate."
                )

        outputs = list(block.get("outputs") or [])
        if outputs:
            st.markdown("**Результат шага — из execution trace**")
            for row in outputs:
                st.markdown(_value_line(core, row))

        if block.get("selected_edge_id"):
            st.caption(f"Выбранная DAG edge: {block['selected_edge_id']}")


def install(core: Any) -> None:
    """Add the live report as the primary right-side diagnostic view."""
    st = core.st
    original = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        report_tab, diagnostic_tab = st.tabs(["Ход расчёта", "Величины / Trace"])
        with report_tab:
            app = st.session_state.get("_fire_app")
            sid = st.session_state.get("_fire_session_id")
            if app is None or not sid or sid not in app.service.sessions:
                st.caption("REPORT-IR станет доступен после создания расчётной сессии.")
            else:
                session = app.service.get_session(sid)
                report = build_report_ir2(app.service.model, session)
                c1, c2, c3 = st.columns(3)
                c1.metric("Report blocks", report.get("block_count", 0))
                c2.metric("DAG nodes", report.get("dag_census", {}).get("node_count", 0))
                c3.metric("Datasets", report.get("dag_census", {}).get("dataset_count", 0))
                st.caption(f"REPORT-IR2 · DAG `{report.get('graph_id')}` · `{report.get('report_sha256')}`")
                st.download_button(
                    "Скачать Report IR JSON",
                    data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    file_name="fire_report_ir_v2.json",
                    mime="application/json",
                    width="stretch",
                    on_click="ignore",
                    key="fire:report:download",
                )
                blocks = list(report.get("blocks") or [])
                if not blocks:
                    st.caption("Отчёт будет собираться автоматически по мере прохождения DAG.")
                for i, block in enumerate(blocks):
                    _render_block(core, block, expanded=(i == len(blocks) - 1))
        with diagnostic_tab:
            original(env)

    core._render_ledger_trace = _render_ledger_trace
