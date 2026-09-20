from __future__ import annotations

from typing import Any, Mapping

import streamlit as st


def _svg(body: str, label: str, width: int = 150, height: int = 92) -> str:
    return (
        f'<div style="height:{height + 12}px;display:flex;align-items:center;justify-content:center;'
        'border:1px solid rgba(49,51,63,.18);border-radius:12px;margin:.15rem 0 .45rem 0">'
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{label}" '
        'style="max-width:100%;color:currentColor">'
        f'{body}</svg></div>'
    )


def _choice_cards(core, card: Mapping[str, Any], old: Any, mode_key: str, rows: list[dict[str, Any]], *, columns: int) -> tuple[Any, None, bool]:
    state_key = core._key(mode_key, card["node_id"], "graphic-choice")
    values = [r["value"] for r in rows]
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
                    st.success(f"Выбрано: {title}", icon="✓")
                if st.button(title, key=core._key(mode_key, card["node_id"], "graphic-button", row["value"]), width="stretch"):
                    selected = row["value"]
                    st.session_state[state_key] = selected
                if row.get("note"):
                    st.caption(row["note"])
    return selected, None, selected is not None


def _table21(core, card, old, mode_key):
    option_map = {str(o.get("value")): o for o in card.get("options", [])}
    rows = []
    # UI schematics intentionally remain schematic: exact row matching still follows SP16 Table 21.
    bodies = {
        "1": '<path d="M35 20H115M75 20V76M35 76H115" fill="none" stroke="currentColor" stroke-width="7"/>'
             '<line x1="18" y1="48" x2="132" y2="48" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>'
             '<path d="M112 34H140M132 28L140 34L132 40" fill="none" stroke="currentColor" stroke-width="2"/>',
        "2": '<path d="M35 20H115M75 20V76M35 76H115" fill="none" stroke="currentColor" stroke-width="7"/>'
             '<line x1="75" y1="8" x2="75" y2="86" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>'
             '<path d="M92 12V42M86 20L92 12L98 20" fill="none" stroke="currentColor" stroke-width="2"/>',
        "3": '<path d="M30 20H108M62 20V76M30 76H122" fill="none" stroke="currentColor" stroke-width="7"/>'
             '<line x1="14" y1="48" x2="136" y2="48" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>'
             '<path d="M110 35H140M132 29L140 35L132 41" fill="none" stroke="currentColor" stroke-width="2"/>',
        "4": '<path d="M24 20H126M67 20V76M42 76H96" fill="none" stroke="currentColor" stroke-width="7"/>'
             '<line x1="67" y1="8" x2="67" y2="86" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>'
             '<path d="M88 12V42M82 20L88 12L94 20" fill="none" stroke="currentColor" stroke-width="2"/>',
    }
    notes = {
        "1": "Сопоставьте форму, ось изгиба и направление эксцентриситета с 1-й графической строкой табл. 21.",
        "2": "Сопоставьте форму, ось изгиба и направление эксцентриситета со 2-й графической строкой табл. 21.",
        "3": "Сопоставьте форму, ось изгиба и направление эксцентриситета с 3-й графической строкой табл. 21.",
        "4": "Для типа 4 downstream использует I₂/I₁ меньшей и большей полок относительно y–y.",
    }
    for value in ["1", "2", "3", "4"]:
        if option_map and value not in option_map:
            continue
        label = option_map.get(value, {}).get("label") or f"Тип {value}"
        rows.append({"value": value, "title": label, "svg": _svg(bodies[value], f"Таблица 21, тип {value}"), "note": notes[value]})
    st.caption("Выбор выполняется по графической схеме таблицы 21. Схемы в UI — схематическая перерисовка для навигации; при неоднозначности тип не угадывается.")
    return _choice_cards(core, card, old, mode_key, rows, columns=4)


def _table7(core, card, old, mode_key):
    rows = [
        {
            "value": "a", "title": "Тип a",
            "svg": _svg('<rect x="36" y="22" width="78" height="48" fill="none" stroke="currentColor" stroke-width="6"/><line x1="75" y1="8" x2="75" y2="84" stroke="currentColor" stroke-dasharray="5 4"/>', "Таблица 7, тип a"),
            "note": "α = 0,03; β = 0,06",
        },
        {
            "value": "b", "title": "Тип b",
            "svg": _svg('<path d="M35 22H115M75 22V70M35 70H115" fill="none" stroke="currentColor" stroke-width="7"/><line x1="16" y1="46" x2="134" y2="46" stroke="currentColor" stroke-dasharray="5 4"/>', "Таблица 7, тип b"),
            "note": "α = 0,04; β = 0,09",
        },
        {
            "value": "c", "title": "Тип c",
            "svg": _svg('<path d="M35 22H115M75 22V72" fill="none" stroke="currentColor" stroke-width="7"/><line x1="75" y1="8" x2="75" y2="84" stroke="currentColor" stroke-dasharray="5 4"/>', "Таблица 7, тип c"),
            "note": "α = 0,04; β = 0,14",
        },
    ]
    st.caption("Тип кривой выбирается по форме сечения и расчётной плоскости СП16, табл. 7.")
    return _choice_cards(core, card, old, mode_key, rows, columns=3)


def _table30(core, card, old, mode_key):
    schemes = [
        ("S1", "Шарнир — шарнир", "μ = 1,00", "hinged", "hinged"),
        ("S2", "Защемление — шарнир", "μ = 0,70", "fixed", "hinged"),
        ("S3", "Защемление — защемление", "μ = 0,50", "fixed", "fixed"),
        ("S4", "Консоль", "μ = 2,00", "fixed", "free"),
        ("S5", "Схема 5", "μ = 1,00 · сверить нагрузку", "special", "special"),
        ("S6", "Схема 6", "μ = 2,00 · сверить нагрузку", "special", "special"),
        ("S7", "Схема 7", "μ = 0,725 · сверить нагрузку", "special", "special"),
        ("S8", "Схема 8", "μ = 1,12 · сверить нагрузку", "special", "special"),
    ]
    def body(left: str, right: str, label: str) -> str:
        left_mark = '<rect x="18" y="26" width="12" height="40" fill="currentColor"/>' if left == "fixed" else ('<circle cx="25" cy="46" r="8" fill="none" stroke="currentColor" stroke-width="3"/>' if left == "hinged" else '<circle cx="25" cy="46" r="3" fill="currentColor"/>')
        right_mark = '<rect x="120" y="26" width="12" height="40" fill="currentColor"/>' if right == "fixed" else ('<circle cx="125" cy="46" r="8" fill="none" stroke="currentColor" stroke-width="3"/>' if right == "hinged" else '<circle cx="125" cy="46" r="3" fill="currentColor"/>')
        if left == "special":
            return f'<line x1="28" y1="46" x2="122" y2="46" stroke="currentColor" stroke-width="5"/><text x="75" y="34" text-anchor="middle" font-size="18" fill="currentColor">{label}</text>'
        return left_mark + '<line x1="30" y1="46" x2="120" y2="46" stroke="currentColor" stroke-width="5"/>' + right_mark
    rows = [
        {"value": v, "title": title, "svg": _svg(body(l, r, v), f"Таблица 30, {v}"), "note": note}
        for v, title, note, l, r in schemes
    ]
    st.caption("S1–S4 распознаются по классическим закреплениям. Для S5–S8 обязательно сверяется также нормативная схема нагрузки таблицы 30.")
    return _choice_cards(core, card, old, mode_key, rows, columns=4)


def _heated_sides(core, card, old, mode_key):
    rows = [
        {
            "value": "four_sides", "title": "Обогрев с 4 сторон",
            "svg": _svg('<path d="M50 18H100M75 18V74M50 74H100" fill="none" stroke="currentColor" stroke-width="7"/><path d="M24 46H46M104 46H126M75 2V14M75 78V90" stroke="currentColor" stroke-width="2"/><path d="M42 41L48 46L42 51M108 41L102 46L108 51M70 10L75 16L80 10M70 82L75 76L80 82" fill="none" stroke="currentColor" stroke-width="2"/>', "Обогрев с четырех сторон"),
            "note": "Открыт весь расчётный периметр.",
        },
        {
            "value": "three_sides", "title": "Обогрев с 3 сторон",
            "svg": _svg('<path d="M50 18H100M75 18V74M50 74H100" fill="none" stroke="currentColor" stroke-width="7"/><line x1="38" y1="7" x2="112" y2="7" stroke="currentColor" stroke-width="4"/><path d="M24 46H46M104 46H126M75 78V90" stroke="currentColor" stroke-width="2"/><path d="M42 41L48 46L42 51M108 41L102 46L108 51M70 82L75 76L80 82" fill="none" stroke="currentColor" stroke-width="2"/>', "Обогрев с трех сторон"),
            "note": "Верхняя сторона экранирована.",
        },
    ]
    return _choice_cards(core, card, old, mode_key, rows, columns=2)


def _protection_perimeter(core, card, old, mode_key):
    contour = '<path d="M42 18H108V30H82V64H108V76H42V64H68V30H42Z" fill="none" stroke="currentColor" stroke-width="6"/><path d="M32 10H118V38H92V56H118V84H32V56H58V38H32Z" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>'
    box = '<path d="M48 22H102M75 22V70M48 70H102" fill="none" stroke="currentColor" stroke-width="7"/><rect x="28" y="10" width="94" height="72" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="5 4"/>'
    rows = [
        {"value": "contour", "title": "По контуру", "svg": _svg(contour, "Огнезащита по контуру"), "note": "Слой повторяет контур стального профиля."},
        {"value": "box", "title": "В виде короба", "svg": _svg(box, "Огнезащита в виде короба"), "note": "Огнезащита образует внешний короб; это не тип стального сечения."},
    ]
    return _choice_cards(core, card, old, mode_key, rows, columns=2)


def install(core) -> None:
    original = core._render_scalar_custom

    def patched(card, old, mode_key, component):
        if component == "table21_type_selector":
            return _table21(core, card, old, mode_key)
        if component == "table7_curve_selector":
            return _table7(core, card, old, mode_key)
        if component == "table30_scheme_selector":
            return _table30(core, card, old, mode_key)
        if component == "heated_sides_selector":
            return _heated_sides(core, card, old, mode_key)
        if component == "protection_perimeter_mode_selector":
            return _protection_perimeter(core, card, old, mode_key)
        return original(card, old, mode_key, component)

    core._render_scalar_custom = patched
