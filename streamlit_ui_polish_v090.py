"""v0.90 presentation polish for graphic selectors and thermal diagrams.

No quantity values, graph routing or engineering calculations are changed here.
The layer only makes the selected graphic option visible immediately and gives
reference heating curves persistent colour + dash identities.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_graphic_selectors as _graphics
import streamlit_guided_ux_v086 as _v086

_INSTALLED = "_fire_ui_polish_v090_installed"

_REFERENCE_CURVE_STYLES = {
    3.0: {"stroke": "#1f77b4", "width": 1.9, "dash": ""},
    5.0: {"stroke": "#2ca02c", "width": 1.9, "dash": "7 3"},
    10.0: {"stroke": "#9467bd", "width": 1.9, "dash": "10 3 2 3"},
    15.0: {"stroke": "#ff7f0e", "width": 1.9, "dash": "2 3"},
    20.0: {"stroke": "#8c564b", "width": 1.9, "dash": "12 4"},
}


def _choice_cards_v090(
    core: Any,
    card: Mapping[str, Any],
    old: Any,
    mode_key: str,
    rows: list[dict[str, Any]],
    *,
    columns: int,
) -> tuple[Any, None, bool]:
    """Graphic selector with first-click redraw and an unambiguous selected state."""
    st = _graphics.st
    state_key = core._key(mode_key, card["node_id"], "graphic-choice")
    values = [row["value"] for row in rows]
    if state_key not in st.session_state:
        st.session_state[state_key] = old if old in values else None
    selected = st.session_state[state_key]

    for start in range(0, len(rows), columns):
        cols = st.columns(columns)
        for col, row in zip(cols, rows[start:start + columns]):
            with col:
                title = row.get("title") or str(row["value"])
                st.markdown(row["svg"], unsafe_allow_html=True)
                st.markdown(f"**{title}**")
                if selected == row["value"]:
                    st.success("✓ ВЫБРАНО")
                else:
                    clicked = st.button(
                        "Выбрать",
                        key=core._key(mode_key, card["node_id"], "graphic-button", row["value"]),
                        width="stretch",
                    )
                    if clicked:
                        selected = row["value"]
                        st.session_state[state_key] = selected
                        rerun = getattr(st, "rerun", None)
                        if callable(rerun):
                            rerun()
                if row.get("note"):
                    st.caption(row["note"])
    return selected, None, selected is not None


def _protection_perimeter_v090(core: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    contour = (
        '<path d="M42 18H108V30H82V64H108V76H42V64H68V30H42Z" fill="none" stroke="#4b5563" stroke-width="6"/>'
        '<path d="M32 10H118V38H92V56H118V84H32V56H58V38H32Z" fill="none" stroke="#d97706" stroke-width="3"/>'
        '<text x="75" y="88" text-anchor="middle" font-size="10" fill="#d97706">слой повторяет контур</text>'
    )
    box = (
        '<path d="M48 22H102M75 22V70M48 70H102" fill="none" stroke="#4b5563" stroke-width="7"/>'
        '<rect x="28" y="10" width="94" height="72" fill="none" stroke="#2563eb" stroke-width="3" stroke-dasharray="9 4"/>'
        '<text x="75" y="88" text-anchor="middle" font-size="10" fill="#2563eb">внешний короб</text>'
    )
    rows = [
        {
            "value": "contour",
            "title": "По контуру",
            "svg": _graphics._svg(contour, "Огнезащита по контуру"),
            "note": "Оранжевая линия показывает слой, повторяющий контур стального профиля.",
        },
        {
            "value": "box",
            "title": "В виде короба",
            "svg": _graphics._svg(box, "Огнезащита в виде короба"),
            "note": "Синий штриховой прямоугольник показывает внешний короб вокруг профиля.",
        },
    ]
    return _choice_cards_v090(core, card, old, mode_key, rows, columns=2)


def _series_style_v090(
    name: str,
    *,
    actual_group: str | None,
    fire_group: str | None,
    style_map: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[str, float, str]:
    if style_map and name in style_map:
        spec = style_map[name]
        return str(spec.get("stroke") or "#777"), float(spec.get("width") or 1.8), str(spec.get("dash") or "")
    if name == actual_group:
        return "#d62728", 3.0, ""
    if name == fire_group:
        return "#111111", 2.3, "8 5"
    match = re.search(r"δпр\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*мм", str(name))
    if match:
        thickness = float(match.group(1))
        spec = _REFERENCE_CURVE_STYLES.get(thickness)
        if spec:
            return str(spec["stroke"]), float(spec["width"]), str(spec["dash"])
    return "#6b7280", 1.6, "3 3"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    # All existing scalar-selector closures resolve these globals at render time.
    _graphics._choice_cards = _choice_cards_v090
    _graphics._protection_perimeter = _protection_perimeter_v090
    # v0.86 chart renderer resolves _series_style from its module globals.
    _v086._series_style = _series_style_v090
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_choice_cards_v090", "_series_style_v090", "_protection_perimeter_v090"]
