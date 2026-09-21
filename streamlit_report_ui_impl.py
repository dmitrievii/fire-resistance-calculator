"""Live REPORT-IR5 engineering calculation trail for Streamlit."""
from __future__ import annotations

from typing import Any, Mapping

from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir5 import build_report_ir5


def _display_value(row: Mapping[str, Any]) -> str:
    value = row.get("raw_value")
    if isinstance(value, float):
        text = format(value, ".12g")
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif value is None:
        text = "—"
    else:
        text = str(value)
    unit = row.get("canonical_unit")
    return f"{text} {unit}" if unit else text


def _refs_text(refs: Any) -> str:
    out = []
    for ref in refs or []:
        if not isinstance(ref, Mapping):
            continue
        standard = ref.get("standard_id") or ref.get("document_id") or ""
        locator = ref.get("clause") or ref.get("section") or ref.get("table_ref") or ""
        text = " ".join(str(x) for x in (standard, locator) if x)
        if text:
            out.append(text)
    return "; ".join(out)


def _render_trace_values(st: Any, title: str, rows: Any) -> None:
    rows = [row for row in rows or [] if isinstance(row, Mapping)]
    if not rows:
        return
    st.markdown(f"**{title}**")
    st.dataframe(
        [
            {
                "Обозначение": row.get("symbol") or row.get("quantity_id"),
                "Величина": row.get("name_ru") or row.get("quantity_id"),
                "Значение": _display_value(row),
                "Источник": row.get("source_kind") or "trace",
            }
            for row in rows
        ],
        width="stretch",
        hide_index=True,
    )


def _render_block(core: Any, block: Mapping[str, Any]) -> None:
    st = core.st
    kind = str(block.get("kind") or "STEP")
    title = str(block.get("title") or block.get("owner_node_id") or "Расчётный шаг")
    st.markdown(f"**{block.get('sequence')}. {title}** · `{kind}`")
    refs = _refs_text(block.get("normative_refs"))
    if refs:
        st.caption(refs)

    if kind == "FAIL_CLOSED":
        st.error(block.get("message") or "Расчётная ветвь остановлена fail-closed.")
        if block.get("failure"):
            st.json(block["failure"])
        return
    if kind == "WARNING":
        st.warning(block.get("message") or "Нормативная ветвь требует дополнительного толкования.")

    _render_trace_values(st, "Исходные величины шага", block.get("inputs"))

    equation = build_trace_bound_equation(block)
    equation_has_result = False
    if equation:
        if equation.get("formula_latex"):
            st.markdown("**Нормативная формула**")
            st.latex(str(equation["formula_latex"]))
        substitution = equation.get("substitution_result_latex") or equation.get("substitution_latex")
        if substitution:
            st.markdown("**Подстановка**")
            st.latex(str(substitution))
        equation_has_result = bool(substitution and equation.get("result_latex"))
        if equation.get("missing_trace_bindings"):
            st.warning("Не заполнены trace bindings: " + ", ".join(equation["missing_trace_bindings"]))

    human = block.get("human_readable") or {}
    mode = human.get("mode")
    if mode == "formula_substitution" and not equation:
        if human.get("formula_expression"):
            st.markdown("**Активное выражение DAG**")
            st.code(str(human["formula_expression"]), language="text")
        if human.get("substituted_expression"):
            st.markdown("**Подстановка чисел**")
            st.code(str(human["substituted_expression"]), language="text")
    elif mode == "lookup_substitution":
        evidence = block.get("execution_evidence") or {}
        rows = evidence.get("selected_dataset_rows") or []
        if rows:
            st.markdown("**Строки нормативной таблицы, использованные runtime**")
            st.json(rows)
        for row in human.get("output_lines") or []:
            if not isinstance(row, Mapping):
                continue
            if row.get("formula_expression"):
                st.markdown("**Интерполяционная формула**")
                st.code(str(row["formula_expression"]), language="text")
            if row.get("substituted_expression"):
                st.markdown("**Подстановка**")
                st.code(str(row["substituted_expression"]), language="text")
    elif mode == "route_decision" and (human.get("selected_edge_id") or block.get("selected_edge_id")):
        st.markdown(
            f"**Выбранная ветвь:** `{human.get('selected_edge_id') or block.get('selected_edge_id')}`"
            + (f" → `{human.get('to_node_id')}`" if human.get("to_node_id") else "")
        )

    if block.get("outputs") and not equation_has_result:
        _render_trace_values(st, "Результат production-расчёта", block.get("outputs"))

    with st.expander("Audit details", expanded=False):
        st.caption(f"DAG node: {block.get('owner_node_id')} · report block: {block.get('report_block_id')}")
        st.json(
            {
                "execution_spec": block.get("execution_spec"),
                "execution_evidence": block.get("execution_evidence"),
                "presentation": block.get("presentation"),
                "selected_edge_id": block.get("selected_edge_id"),
            }
        )


def _render_report(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    blocks = [row for row in report.get("blocks") or [] if isinstance(row, Mapping)]
    if not blocks:
        return

    previous_count = int(st.session_state.get("_fire_report_seen_count", 0) or 0)
    newest_id = blocks[-1].get("report_block_id") if len(blocks) > previous_count else None
    st.session_state["_fire_report_seen_count"] = len(blocks)

    st.markdown("### Ход расчёта")
    st.caption(
        "Элементы отчёта строятся из фактически выполненного DAG trace. Формулы, подстановки и результаты "
        "не пересчитываются presentation-слоем."
    )
    by_id = {str(row.get("report_block_id")): row for row in blocks}
    for section in report.get("sections") or []:
        if not isinstance(section, Mapping):
            continue
        ids = [str(x) for x in section.get("block_ids") or [] if str(x) in by_id]
        if not ids:
            continue
        section_title = section.get("title_ru") or section.get("section_key")
        with st.expander(str(section_title), expanded=(newest_id in ids)):
            for block_id in ids:
                _render_block(core, by_id[block_id])

    st.caption(
        f"REPORT-IR5 · `{report.get('report_sha256')}` · blocks {report.get('block_count', len(blocks))}"
    )


def install(core: Any) -> None:
    """Install live REPORT-IR5 rendering ahead of the existing ledger/trace UI."""
    if getattr(core, "_fire_report_ui_installed", False):
        return
    core._fire_report_ui_installed = True
    st = core.st
    original = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        app = st.session_state.get("_fire_app")
        sid = st.session_state.get("_fire_session_id")
        if app is not None and sid and sid in app.service.sessions:
            session = app.service.get_session(sid)
            _render_report(core, build_report_ir5(app.service.model, session))
        original(env)

    core._render_ledger_trace = _render_ledger_trace


__all__ = ["install"]
