"""Isolated installer for v0.90 REPORT4.

The v0.90 narrative renderer is installed into ``streamlit_app_core`` without
mutating the retained v0.89 module.  This keeps rollback/regression semantics
stable while making REPORT4 the active UI renderer.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

import streamlit_expertise_report_v088 as _v088
import streamlit_expertise_report_v089 as _v089
import streamlit_live_report_v087 as _v087
from standard_core.report_ir5 import build_report_ir5
from streamlit_expertise_report_v090_fire_coeffs import render_expertise_narrative_markdown_v090_fire_coeffs

_INSTALLED = "_fire_expertise_report_v090_isolated_installed"


def _render_export(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    markdown = render_expertise_narrative_markdown_v090_fire_coeffs(report)
    st.download_button(
        "Скачать расчётный отчёт (.md)",
        data=markdown,
        file_name="fire_resistance_expertise_report.md",
        mime="text/markdown",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v090:download:markdown",
    )
    st.download_button(
        "Скачать Report IR (.json)",
        data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        file_name="fire_report_ir_v4.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v090:download:ir",
    )
    st.caption("Экранный и Markdown-отчёт строятся из одного REPORT-IR5. Численные результаты не пересчитываются presentation-слоем.")


def render_expertise_report_v090(core: Any, env: Mapping[str, Any]) -> None:
    st = core.st
    app = st.session_state.get("_fire_app")
    sid = st.session_state.get("_fire_session_id")
    if app is None or not sid or sid not in app.service.sessions:
        st.info("Расчётная сессия ещё не создана.")
        return
    session = app.service.get_session(sid)
    report = build_report_ir5(app.service.model, session)
    markdown = render_expertise_narrative_markdown_v090_fire_coeffs(report)

    st.markdown("### Расчётный отчёт")
    st.caption("Отчёт обновляется после каждого принятого шага. Основной текст собран по инженерным разделам, а служебные этапы расчётного графа скрыты во вкладке Audit.")
    tab_report, tab_export, tab_audit = st.tabs(["Расчётный отчёт", "Экспорт", "Audit"])
    with tab_report:
        _v088._report_status(st, report)
        with st.container(height=1120, border=True):
            st.markdown(markdown)
    with tab_export:
        _render_export(core, report)
    with tab_audit:
        _v087._render_audit(core, report, env)


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    # v0.89 remains an immutable retained layer.  REPORT4 is bound only at the
    # core renderer hook, so importing/using v0.89 directly still gives v0.89.
    previous = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        render_expertise_report_v090(core, env)

    core._fire_expertise_report_v090_previous_renderer = previous
    core._render_ledger_trace = _render_ledger_trace
    setattr(core, _INSTALLED, True)


__all__ = ["install", "render_expertise_report_v090"]
