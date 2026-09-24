"""Isolated installer for the active progressive expertise report.

The retained report modules remain available for audit/rollback.  The final
v0.93 renderer applies the v0.92 trace-bound mechanics overlays and then enforces
progressive chapter visibility, engineering-readable executed section properties
and explicit gamma_m -> Table-2 resistance provenance.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

import streamlit_expertise_report_v088 as _v088
import streamlit_live_report_v087 as _v087
from standard_core.report_ir_v092 import build_report_ir_v092
from streamlit_expertise_report_v092 import REPORT_COMPACT_CSS, report_marker_html
from streamlit_expertise_report_v093_progressive_hotfix import (
    render_expertise_narrative_markdown_v093_progressive as render_expertise_narrative_markdown_v092,
)

_INSTALLED = "_fire_expertise_report_v090_isolated_installed"


def _render_export(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    markdown = render_expertise_narrative_markdown_v092(report)
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
    st.caption("Экранный и Markdown-отчёт формируются из одних и тех же зафиксированных результатов расчёта; экранный слой не пересчитывает инженерные величины.")


def render_expertise_report_v090(core: Any, env: Mapping[str, Any]) -> None:
    st = core.st
    app = st.session_state.get("_fire_app")
    sid = st.session_state.get("_fire_session_id")
    if app is None or not sid or sid not in app.service.sessions:
        st.info("Расчётная сессия ещё не создана.")
        return
    session = app.service.get_session(sid)
    report = build_report_ir_v092(app.service.model, session)
    markdown = render_expertise_narrative_markdown_v092(report)

    st.markdown(REPORT_COMPACT_CSS, unsafe_allow_html=True)
    st.markdown("### Расчётный отчёт")
    st.caption("Отчёт обновляется после каждого принятого шага. Показываются только фактически выполненные расчётные шаги, ненулевые силовые факторы и текущий незавершённый ввод; будущие и неприменимые ветви доступны во вкладке Audit.")
    tab_report, tab_export, tab_audit = st.tabs(["Расчётный отчёт", "Экспорт", "Audit"])
    with tab_report:
        _v088._report_status(st, report)
        with st.container(height=1120, border=True):
            st.markdown(report_marker_html(), unsafe_allow_html=True)
            st.markdown(markdown)
    with tab_export:
        _render_export(core, report)
    with tab_audit:
        _v087._render_audit(core, report, env)


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        render_expertise_report_v090(core, env)

    core._fire_expertise_report_v090_previous_renderer = previous
    core._render_ledger_trace = _render_ledger_trace
    setattr(core, _INSTALLED, True)


__all__ = ["install", "render_expertise_report_v090"]
