"""Live REPORT-IR presentation for Streamlit.

The renderer consumes REPORT-IR4 only. It does not run normative DAG nodes,
evaluate equations, or interpolate datasets.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from standard_core.report_ir4 import build_report_ir4


def _value_line(core: Any, row: Mapping[str, Any]) -> str:
    symbol = row.get("symbol") or row.get("quantity_id")
    unit = f" {row['canonical_unit']}" if row.get("canonical_unit") else ""
    return f"**{symbol}** = `{core._fmt(row.get('raw_value'))}{unit}`"


def _render_lookup_rows(core: Any, evidence: Mapping[str, Any]) -> None:
    st = core.st
    rows = evidence.get("selected_dataset_rows") or []
    status = evidence.get("selected_dataset_rows_status")
    if status != "CAPTURED_BY_RUNTIME_AUDIT" or not rows:
        st.info(
            "Для этого lookup нет совпавшего runtime-evidence блока. Отчёт не восстанавливает строки таблицы самостоятельно."
        )
        return

    st.markdown("**Строки нормативной таблицы, зафиксированные runtime**")
    flat = []
    for item in rows:
        row = item.get("row") if isinstance(item, Mapping) else None
        record = {
            "Роль": item.get("role") if isinstance(item, Mapping) else None,
            "Индекс строки": item.get("row_index") if isinstance(item, Mapping) else None,
        }
        if isinstance(row, Mapping):
            record.update(dict(row))
        flat.append(record)
    st.dataframe(flat, width="stretch", hide_index=True)

    runtime = evidence.get("runtime_lookup_evidence") or {}
    mode = runtime.get("selection_mode")
    if mode == "linear_bracket":
        st.caption(
            "Интервал runtime: "
            f"{runtime.get('axis')} = {core._fmt(runtime.get('axis_lower'))} … {core._fmt(runtime.get('axis_upper'))}; "
            f"расчётная точка = {core._fmt(runtime.get('axis_value'))}; "
            f"доля интервала = {core._fmt(runtime.get('fraction'))}."
        )
    elif mode == "linear_exact_knot":
        st.caption(f"Точное табличное значение на узле {runtime.get('axis')} = {core._fmt(runtime.get('axis_value'))}.")
    elif mode == "bilinear_grid":
        st.caption(
            f"Bilinear runtime grid: {runtime.get('bracket')} · fractions: {runtime.get('fractions')}"
        )


def _render_formula_substitution(core: Any, human: Mapping[str, Any]) -> None:
    st = core.st
    formula = human.get("formula_expression")
    substitution = human.get("substituted_expression")
    if formula:
        st.markdown("**Расчётная формула — активное выражение из DAG**")
        st.code(str(formula), language=None)
    if substitution:
        st.markdown("**Подстановка чисел**")
        st.code(str(substitution), language=None)
    if human.get("selected_case_index") is not None:
        st.caption(
            f"Активная piecewise-ветвь: case #{human.get('selected_case_index')} · "
            "зафиксирована runtime после успешного production-расчёта."
        )
    elif human.get("piecewise_case_status") not in {None, "NOT_REQUIRED", "CAPTURED_BY_RUNTIME_AUDIT"}:
        st.warning(
            "Для piecewise-формулы не удалось связать runtime case evidence; отчёт не выбирает ветвь повторно."
        )

    missing = human.get("missing_binding_variables") or []
    if missing:
        st.warning("В подстановке отсутствуют trace-значения для: " + ", ".join(map(str, missing)))

    results = human.get("result_lines") or []
    if results:
        st.markdown("**Результат production-расчёта**")
        for row in results:
            st.markdown(f"**{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_value')}`")


def _render_lookup_substitution(core: Any, human: Mapping[str, Any]) -> None:
    st = core.st
    lines = human.get("output_lines") or []
    for row in lines:
        formula = row.get("formula_expression")
        substitution = row.get("substituted_expression")
        if formula:
            st.markdown("**Интерполяционная формула**")
            st.code(str(formula), language=None)
        if substitution:
            st.markdown("**Подстановка по зафиксированным строкам таблицы**")
            st.code(str(substitution), language=None)
        st.markdown(
            f"**{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_result')}` "
            "— результат production lookup"
        )


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
        human = block.get("human_readable") or {}
        mode = spec.get("mode")

        if human.get("mode") == "formula_substitution":
            _render_formula_substitution(core, human)
            bindings = evidence.get("bindings") or []
            if bindings:
                with st.expander("Привязка переменных к quantities", expanded=False):
                    st.dataframe(
                        [
                            {
                                "Переменная": row.get("variable"),
                                "Quantity": row.get("quantity_id"),
                                "Значение": core._fmt(row.get("raw_value")) if row.get("present_in_trace") else "—",
                                "Ед.": row.get("canonical_unit") or "",
                            }
                            for row in bindings
                        ],
                        width="stretch",
                        hide_index=True,
                    )
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
            _render_lookup_rows(core, evidence)
            if human.get("mode") == "lookup_substitution":
                _render_lookup_substitution(core, human)
        elif human.get("mode") == "route_decision":
            target = human.get("to_node_id")
            if block.get("selected_edge_id"):
                st.markdown(
                    f"**Выбранная ветвь:** `{block.get('selected_edge_id')}`"
                    + (f" → `{target}`" if target else "")
                )
            if human.get("decision_outputs"):
                st.caption("Решение взято из completed execution trace; условие маршрута отчётом повторно не вычисляется.")

        outputs = list(block.get("outputs") or [])
        # Formula/lookup renderers already print their trace results immediately
        # after the substitution. Other block kinds keep the generic result view.
        if outputs and human.get("mode") not in {"formula_substitution", "lookup_substitution"}:
            st.markdown("**Результат шага — из execution trace**")
            for row in outputs:
                st.markdown(_value_line(core, row))

        if block.get("selected_edge_id") and human.get("mode") != "route_decision":
            route_target = None
            if isinstance(human, Mapping):
                route_target = human.get("to_node_id")
            st.caption(
                f"Выбранная DAG edge: {block['selected_edge_id']}"
                + (f" → {route_target}" if route_target else "")
            )


def install(core: Any) -> None:
    """Add the report-ready calculation view to the right-side panel."""
    if getattr(core, "_fire_report_ui_installed", False):
        return
    core._fire_report_ui_installed = True

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
                report = build_report_ir4(app.service.model, session)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Report blocks", report.get("block_count", 0))
                c2.metric("DAG nodes", report.get("dag_census", {}).get("node_count", 0))
                c3.metric("Datasets", report.get("dag_census", {}).get("dataset_count", 0))
                c4.metric("Route edges", len(report.get("selected_route") or []))
                st.caption(f"REPORT-IR4 · DAG `{report.get('graph_id')}` · `{report.get('report_sha256')}`")
                st.download_button(
                    "Скачать Report IR JSON",
                    data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    file_name="fire_report_ir_v3.json",
                    mime="application/json",
                    width="stretch",
                    on_click="ignore",
                    key="fire:report:download",
                )

                blocks = list(report.get("blocks") or [])
                if not blocks:
                    st.caption("Отчёт будет собираться автоматически по мере прохождения DAG.")
                else:
                    by_id = {str(block.get("report_block_id")): block for block in blocks}
                    last_id = str(blocks[-1].get("report_block_id"))
                    rendered: set[str] = set()
                    for section in report.get("sections") or []:
                        ids = [str(x) for x in section.get("block_ids") or [] if str(x) in by_id]
                        if not ids:
                            continue
                        st.markdown(f"### {section.get('title_ru') or section.get('section_key')}")
                        for block_id in ids:
                            _render_block(core, by_id[block_id], expanded=(block_id == last_id))
                            rendered.add(block_id)
                    for block in blocks:
                        block_id = str(block.get("report_block_id"))
                        if block_id not in rendered:
                            _render_block(core, block, expanded=(block_id == last_id))

                route = report.get("selected_route") or []
                if route:
                    with st.expander("Активный маршрут DAG", expanded=False):
                        st.dataframe(
                            [
                                {
                                    "Шаг": row.get("sequence"),
                                    "Edge": row.get("selected_edge_id"),
                                    "От": row.get("from_node_id"),
                                    "К": row.get("to_node_id"),
                                }
                                for row in route
                            ],
                            width="stretch",
                            hide_index=True,
                        )
        with diagnostic_tab:
            original(env)

    core._render_ledger_trace = _render_ledger_trace
