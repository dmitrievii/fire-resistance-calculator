from __future__ import annotations

import json
from typing import Any

import streamlit as st


MOBILE_STYLES = r"""
<style>
.fire-card h3 {
  font-size: 1.55rem;
  line-height: 1.25;
  letter-spacing: -.018em;
  font-weight: 720;
}
.fire-status-line {
  display: flex;
  flex-wrap: wrap;
  gap: .42rem;
  align-items: center;
  margin: .05rem 0 .55rem 0;
}
.fire-status-line .fire-status { margin-right: 0; }
.fire-tech-footer { color: var(--fire-muted); font-size: .78rem; }
.fire-graph-id {
  overflow-wrap: anywhere;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: .75rem;
  color: var(--fire-muted);
}
@media (max-width: 768px) {
  [data-testid="stHeader"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    /* Streamlit does not guarantee a public --background-color CSS variable.
       The previous white fallback therefore forced a white mobile header in
       dark mode.  The header is a child of the themed app view container, so
       inheriting its computed background follows light/dark/custom themes. */
    background-color: inherit !important;
    background-image: none !important;
    border-bottom: 1px solid rgba(128, 128, 128, 0.24) !important;
    z-index: 1000000 !important;
  }
  [data-testid="stToolbar"] {
    position: relative !important;
    z-index: 1000001 !important;
  }
  .block-container {
    padding-top: calc(3.85rem + env(safe-area-inset-top, 0px)) !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-bottom: 1.5rem !important;
  }
  .fire-hero {
    padding: .05rem 0 .42rem 0;
    margin-top: .15rem;
  }
  .fire-title { font-size: 1.44rem; line-height: 1.14; }
  .fire-subtitle { font-size: .84rem; line-height: 1.35; }
  .fire-status { padding: .24rem .5rem; font-size: .72rem; }
  .fire-card { padding: .78rem .82rem; border-radius: 13px; }
  .fire-card h3 { font-size: 1.34rem; line-height: 1.27; margin-top: .08rem; }
  .fire-kicker { font-size: .69rem; margin-bottom: .25rem; }
  .fire-ref { font-size: .69rem; padding: .17rem .34rem; }
  .fire-tech-footer { display: none; }
  div[data-testid="stButton"] > button,
  div[data-testid="stDownloadButton"] > button { min-height: 2.75rem; }
  div[data-testid="stExpander"] details summary { min-height: 2.7rem; }
}
</style>
"""

_SUPPRESSED_SUBTITLES = {
    "do not assume ambient and fire combinations are identical unless explicitly selected later.",
}


def _status_label(status: str) -> str:
    if status == "AWAITING_INPUT":
        return "Ожидается ввод"
    if status == "RESULT":
        return "Результат"
    if status == "COMPLETE":
        return "Завершено"
    if status.startswith("BLOCKED"):
        return "Остановлено"
    return status or "—"


def _show_subtitle(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.lower() not in _SUPPRESSED_SUBTITLES


def install(core: Any) -> None:
    """Install a mobile-first page composition without touching calculation runtime."""
    if getattr(core, "_MOBILE_UX_INSTALLED", False):
        return
    core._MOBILE_UX_INSTALLED = True
    core.STYLES = core.STYLES + MOBILE_STYLES

    def main() -> None:
        st.set_page_config(
            page_title="FIRE Resistance Calculator — СП16 ↔ СП554",
            page_icon="🔥",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        st.markdown(core.STYLES, unsafe_allow_html=True)

        app = core._ensure_app()
        sid = core._ensure_session(app)
        env = app.session_payload(sid)
        contract = st.session_state.get("_fire_contract") or app.ui_contract()
        st.session_state["_fire_contract"] = contract

        history = list(env["state"].get("interaction_history") or [])
        status = str(env["state"].get("status") or "")
        step_no = len(history) + 1

        st.markdown(
            '<div class="fire-hero"><div class="fire-title">FIRE Resistance Calculator</div>'
            '<div class="fire-subtitle">СП 16 ↔ СП 554 · Пошаговый инженерный расчёт</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="fire-status-line">'
            f'<span class="fire-status">{_status_label(status)}</span>'
            f'<span class="fire-status">Шаг {step_no}</span>'
            '<span class="fire-status">DAG locked</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # File/session administration stays above the active step, but history
        # and back-navigation live below the current question and its submit button.
        with st.expander("Расчёт · файл", expanded=False):
            st.markdown(
                f'<div class="fire-graph-id">DAG: {contract.get("graph_id") or "—"}</div>',
                unsafe_allow_html=True,
            )
            action1, action2 = st.columns(2)
            if action1.button("Новый расчёт", width="stretch", key="fire:mobile:new"):
                core._reset_calculation()
                st.rerun()
            snapshot_json = json.dumps(env["state"], ensure_ascii=False, indent=2)
            action2.download_button(
                "Сохранить JSON",
                data=snapshot_json,
                file_name="fire_calculation.json",
                mime="application/json",
                width="stretch",
                on_click="ignore",
                key="fire:mobile:save",
            )
            uploaded = st.file_uploader(
                "Загрузить сохранённый расчёт",
                type=["json"],
                key="fire:upload",
            )
            if uploaded is not None and st.button("Восстановить JSON", key="fire:restore"):
                core._load_snapshot(app, uploaded)

        left, right = st.columns([1.65, 1], gap="large")
        with left:
            edit_card, old_payload, old_provenance = core._edit_context(app, env)
            editing = edit_card is not None
            card = edit_card or env.get("current_card")
            if editing:
                st.info("Редактирование предыдущего шага. После применения downstream-состояние будет детерминированно переиграно.")
                if st.button("К текущему вопросу", key="fire:cancel-edit"):
                    st.session_state["_fire_edit_node"] = None
                    st.rerun()
            if card and card.get("interactive"):
                presentation = card.get("presentation") or {}
                stage = presentation.get("stage") or card.get("owner_standard_id") or "DAG"
                st.markdown(
                    f'<div class="fire-card"><div class="fire-kicker">{stage}</div>'
                    f'<h3>{card.get("prompt") or card.get("title") or card["node_id"]}</h3>',
                    unsafe_allow_html=True,
                )
                subtitle = presentation.get("subtitle")
                if _show_subtitle(subtitle):
                    st.caption(str(subtitle))
                notes = card.get("notes") or {}
                if notes.get("normative_warning"):
                    st.warning(str(notes["normative_warning"]))
                mode_key = "edit" if editing else "current"
                payload, provenance, ready = core._render_card_body(
                    app, sid, env, card, old_payload, old_provenance, mode_key
                )
                core._refs(card)
                st.markdown("</div>", unsafe_allow_html=True)
                label = "Применить изменение" if editing else "Далее"
                if st.button(
                    label,
                    type="primary",
                    disabled=not ready,
                    width="stretch",
                    key=core._key(mode_key, card["node_id"], "submit"),
                ):
                    core._submit(app, sid, card, payload, provenance, editing)
            else:
                core._render_noninteractive(env, card)

            # Request UX contract: Back / previous-question selector / history
            # follows the active calculation step rather than preceding it.
            core._render_history(app, env)

        with right:
            with st.expander("Расчётные величины · Trace", expanded=False):
                core._render_ledger_trace(env)

        st.markdown(
            '<div class="fire-tech-footer">Presentation layer only · '
            'нормативная логика, DAG routing и fail-closed gates остаются в standard_core.</div>',
            unsafe_allow_html=True,
        )

    core.main = main
