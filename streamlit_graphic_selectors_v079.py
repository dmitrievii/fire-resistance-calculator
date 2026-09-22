from __future__ import annotations

"""v0.79 compatibility patch for graphic selector selection feedback.

Streamlit rejects the plain checkmark string passed through the ``icon=``
parameter on the deployed version.  Keep the same visual feedback without using
that version-sensitive parameter.  The patch is applied to the base module even
when its v0.72 installer sentinel is already present in a retained Streamlit
process.
"""

from typing import Any, Mapping

import streamlit_graphic_selectors as _base
import streamlit_graphic_selectors_v072 as _v072


def _choice_cards_safe(
    core: Any,
    card: Mapping[str, Any],
    old: Any,
    mode_key: str,
    rows: list[dict[str, Any]],
    *,
    columns: int,
) -> tuple[Any, None, bool]:
    st = _base.st
    state_key = core._key(mode_key, card["node_id"], "graphic-choice")
    values = [row["value"] for row in rows]
    if state_key not in st.session_state:
        st.session_state[state_key] = old if old in values else None
    selected = st.session_state[state_key]

    for start in range(0, len(rows), columns):
        cols = st.columns(columns)
        for col, row in zip(cols, rows[start:start + columns]):
            with col:
                st.markdown(row["svg"], unsafe_allow_html=True)
                title = row.get("title") or str(row["value"])
                if selected == row["value"]:
                    # Do not use st.success(..., icon="✓"): Streamlit requires
                    # a supported icon token/emoji and raises APIException here.
                    st.success(f"Выбрано: {title}")
                if st.button(
                    title,
                    key=core._key(mode_key, card["node_id"], "graphic-button", row["value"]),
                    width="stretch",
                ):
                    selected = row["value"]
                    st.session_state[state_key] = selected
                if row.get("note"):
                    st.caption(row["note"])
    return selected, None, selected is not None


def install(core: Any) -> None:
    _base._choice_cards = _choice_cards_safe
    _v072.install(core)


__all__ = ["install"]
