"""Explicit guided-calculation navigation for the Streamlit presentation layer.

The normative session already supports deterministic edit/replay.  This module
only makes that capability visible: previous-question navigation and direct jump
to any answered interactive DAG node.  Applying an edited answer continues to
use GuidedCalculationSession.edit_answer(), so downstream state is rebuilt from
the DAG rather than mutated locally.
"""
from __future__ import annotations

from typing import Any, Mapping


def history_rows(env: Mapping[str, Any], cards: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, item in enumerate(env.get("state", {}).get("interaction_history") or []):
        if not isinstance(item, Mapping):
            continue
        node_id = str(item.get("node_id") or "")
        if not node_id:
            continue
        card = cards.get(node_id) or {}
        presentation = card.get("presentation") or {}
        rows.append(
            {
                "index": i,
                "step_number": i + 1,
                "node_id": node_id,
                "title": card.get("title") or card.get("prompt") or node_id,
                "stage": presentation.get("stage") or card.get("owner_standard_id") or "DAG",
                "payload": item.get("payload"),
                "provenance": item.get("provenance"),
            }
        )
    return rows


def previous_answered_node_id(
    env: Mapping[str, Any],
    cards: Mapping[str, Mapping[str, Any]],
    editing_node_id: str | None = None,
) -> str | None:
    rows = history_rows(env, cards)
    if not rows:
        return None
    if editing_node_id:
        positions = [i for i, row in enumerate(rows) if row["node_id"] == editing_node_id]
        if positions:
            pos = positions[0]
            if pos == 0:
                return rows[0]["node_id"]
            return rows[pos - 1]["node_id"]
    return rows[-1]["node_id"]


def install(core: Any) -> None:
    """Install explicit navigation in place of the hidden history-only editor."""
    st = core.st

    def _open_node(node_id: str) -> None:
        st.session_state["_fire_edit_node"] = node_id
        st.rerun()

    def _render_history(app: Any, env: Mapping[str, Any]) -> None:
        cards = core._card_map(app)
        rows = history_rows(env, cards)
        editing_node_id = st.session_state.get("_fire_edit_node")
        previous_id = previous_answered_node_id(env, cards, editing_node_id)

        st.markdown("#### Навигация по расчёту")
        back_col, jump_col, go_col = st.columns([1.05, 2.55, 0.8])
        if back_col.button(
            "← Назад",
            disabled=previous_id is None,
            width="stretch",
            key="fire:navigation:back",
            help="Открыть предыдущий отвеченный вопрос. Изменение ответа переиграет downstream-ветвь по DAG.",
        ):
            _open_node(str(previous_id))

        options = [row["node_id"] for row in rows]
        labels = {
            row["node_id"]: f"{row['step_number']}. {row['title']} · {row['stage']}"
            for row in rows
        }
        target = jump_col.selectbox(
            "Перейти к шагу / вопросу",
            options,
            index=None,
            placeholder="— выберите предыдущий вопрос —",
            format_func=lambda node_id: labels.get(node_id, node_id),
            key="fire:navigation:target",
            label_visibility="collapsed",
        )
        if go_col.button(
            "Перейти",
            disabled=target is None,
            width="stretch",
            key="fire:navigation:go",
        ):
            _open_node(str(target))

        if editing_node_id:
            current = next((row for row in rows if row["node_id"] == editing_node_id), None)
            if current:
                st.caption(
                    f"Открыт шаг {current['step_number']}: {current['title']}. "
                    "После применения изменения все зависимые последующие узлы будут пересчитаны через DAG replay."
                )

        with st.expander(f"История шагов ({len(rows)})", expanded=False):
            if not rows:
                st.caption("Расчёт ещё не содержит ответов.")
                return
            for row in rows:
                cols = st.columns([5.2, 1])
                cols[0].write(f"{row['step_number']}. {row['title']}")
                cols[0].caption(f"{row['stage']} · {row['node_id']}")
                if cols[1].button("Открыть", key=core._key("history", row["index"], row["node_id"])):
                    _open_node(row["node_id"])

    core._render_history = _render_history
