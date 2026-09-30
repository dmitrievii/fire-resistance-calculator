"""v0.107 guided UX closure.

Restores the complete weakening authoring contract after the v0.106 UX
regression while retaining explicit no-default hole selection, human-readable
Table-1 selectors and lazy report rendering.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v0107_guided_ux_closure_installed"

_LEGACY_IW_TEXT = (
    "учитывать изменение моментов инерции",
    "моментов сопротивления после ослабления",
)

_TABLE1_HUMAN = {
    "default": "Случай не указан в таблице 1 — γc = 1,00 (примечание 5)",
    "row1": "Балки сплошного сечения и соответствующие сжатые элементы ферм перекрытий — случай 1",
    "row2": "Колонны общественных/жилых и многоэтажных зданий — случай 2",
    "row2_095": "Колонны и опоры, для которых таблица 1 задаёт γc = 0,95 — случай 2",
    "row3": "Колонны одноэтажных производственных зданий с мостовыми кранами — случай 3",
    "row3_105": "Колонны одноэтажных производственных зданий с мостовыми кранами — γc = 1,05",
    "row4": "Сжатые основные элементы решётки составного таврового сечения при λ > 60 — случай 4",
    "row5": "Растянутые элементы при расчёте прочности по неослабленному сечению — случай 5",
    "row6": "Ослабленное болтовыми отверстиями сечение при статической нагрузке — случай 6",
    "row7a": "Сжатые элементы решётки пространственных конструкций — случай 7а",
    "row7b": "Элементы с креплением одним болтом или через фасонку — случай 7б",
    "row8": "Сжатые элементы из одиночных уголков/лямбда-профилей, прикреплённых одной полкой — случай 8",
    "row9": "Опорные плиты — случай 9",
}


def _is_legacy_iw(card: Mapping[str, Any]) -> bool:
    text = " ".join(str(card.get(k) or "") for k in ("node_id", "title", "prompt")).lower()
    notes = card.get("notes") or {}
    if isinstance(notes, Mapping):
        text += " " + " ".join(str(v) for v in notes.values()).lower()
    fields = {str(f.get("quantity_id") or "").lower() for f in card.get("fields", []) if isinstance(f, Mapping)}
    if any(token in text for token in _LEGACY_IW_TEXT):
        return True
    return any(("weak" in q or "net" in q) and ("inertia" in q or "iw" in q or "section_mod" in q) for q in fields)


def _ledger_value(env: Mapping[str, Any], qid: str):
    for row in reversed(list((env.get("state") or {}).get("ledger", []))):
        if isinstance(row, Mapping) and row.get("quantity_id") == qid:
            return row.get("value")
    return None


def _positive_input(st, label: str, value: Any, key: str, *, optional: bool = False):
    default = float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else (None if optional else 0.0)
    return st.number_input(label, min_value=0.0, value=default, key=key)


def _weakening_editor(core: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core.st
    old = old if isinstance(old, Mapping) else {}
    old_choice = "holes" if old.get("holes_present") is True else ("none" if old.get("holes_present") is False else None)
    choice = st.selectbox(
        "Ослабление сечения",
        ["none", "holes"],
        index=["none", "holes"].index(old_choice) if old_choice in {"none", "holes"} else None,
        placeholder="— выберите: отверстий нет / есть круглые болтовые отверстия —",
        format_func=lambda x: "Круглые болтовые отверстия" if x == "holes" else "Отверстий нет",
        key=core._key(mode_key, card["node_id"], "weak-explicit"),
    )
    if choice is None:
        st.caption("Выбор должен быть сделан явно; приложение не принимает «отверстий нет» по умолчанию.")
        return None, None, False
    if choice == "none":
        return {"schema": "section_weakening_model_v0.49", "holes_present": False, "model": "none"}, None, True

    d = st.number_input("Диаметр отверстия d, мм", min_value=0.0, value=float(old.get("hole_diameter_mm", 20.0)), key=core._key(mode_key, card["node_id"], "d-explicit"))
    s = st.number_input("Шаг отверстий s, мм", min_value=0.0, value=float(old.get("hole_pitch_mm", 80.0)), key=core._key(mode_key, card["node_id"], "s-explicit"))
    t0 = old.get("local_thickness_mm")
    t = st.number_input("Локальная толщина tₕ, мм (оставьте пустой для определения из модели сечения)", min_value=0.0, value=float(t0) if isinstance(t0, (int, float)) else None, key=core._key(mode_key, card["node_id"], "t-explicit"))

    st.markdown("**Как определить характеристики нетто после ослабления?**")
    old_mode = old.get("net_property_mode")
    mode = st.radio(
        "Характеристики нетто",
        ["automatic_geometry", "manual_net_properties"],
        index=1 if old_mode == "manual_net_properties" else 0,
        format_func=lambda x: (
            "Рассчитать автоматически по геометрии ослабления"
            if x == "automatic_geometry"
            else "Площадь Aₙ рассчитать автоматически, Iₙ/Wₙ ввести вручную"
        ),
        key=core._key(mode_key, card["node_id"], "net-property-mode"),
    )

    payload = {
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": float(d),
        "hole_pitch_mm": float(s),
        "net_property_mode": mode,
    }
    if t is not None and t > 0:
        payload["local_thickness_mm"] = float(t)

    ready = d > 0 and s > d and (t is None or t > 0)
    if s <= d:
        st.warning("Требуется s > d.")

    if mode == "manual_net_properties":
        st.caption("Aₙ не вводится вручную: оно всегда рассчитывается как Aₙ = A − d·tₕ. Ниже задаются готовые характеристики нетто в главных осях z/y.")
        old_manual = old.get("manual_net_properties") if isinstance(old.get("manual_net_properties"), Mapping) else {}
        c1, c2 = st.columns(2)
        Iz = _positive_input(c1, "I_z,n, мм⁴", old_manual.get("I_z_n_mm4"), core._key(mode_key, card["node_id"], "Iz-net"))
        Iy = _positive_input(c2, "I_y,n, мм⁴", old_manual.get("I_y_n_mm4"), core._key(mode_key, card["node_id"], "Iy-net"))
        c1, c2 = st.columns(2)
        Wz = _positive_input(c1, "W_z,n, мм³", old_manual.get("W_z_n_mm3"), core._key(mode_key, card["node_id"], "Wz-net"))
        Wy = _positive_input(c2, "W_y,n, мм³", old_manual.get("W_y_n_mm3"), core._key(mode_key, card["node_id"], "Wy-net"))
        st.caption("Дополнительные характеристики задаются только при наличии в расчётной модели.")
        c1, c2 = st.columns(2)
        Wplz = _positive_input(c1, "W_pl,z,eff, мм³ (необязательно)", old_manual.get("W_pl_z_eff_mm3"), core._key(mode_key, card["node_id"], "Wplz-net"), optional=True)
        Wply = _positive_input(c2, "W_pl,y,eff, мм³ (необязательно)", old_manual.get("W_pl_y_eff_mm3"), core._key(mode_key, card["node_id"], "Wply-net"), optional=True)
        c1, c2 = st.columns(2)
        Iomega = _positive_input(c1, "I_ω,n, мм⁶ (необязательно)", old_manual.get("I_omega_n_mm6"), core._key(mode_key, card["node_id"], "Iomega-net"), optional=True)
        Womega = _positive_input(c2, "W_ω,eff, мм⁴ (необязательно)", old_manual.get("W_omega_eff_mm4"), core._key(mode_key, card["node_id"], "Womega-net"), optional=True)
        manual = {"I_z_n_mm4": float(Iz), "I_y_n_mm4": float(Iy), "W_z_n_mm3": float(Wz), "W_y_n_mm3": float(Wy)}
        ready = ready and all(v > 0 for v in manual.values())
        plastic_pair = (Wplz is not None, Wply is not None)
        if plastic_pair[0] != plastic_pair[1]:
            st.warning("Пластические характеристики необходимо задать парой: W_pl,z,eff и W_pl,y,eff.")
            ready = False
        if Wplz is not None and Wply is not None:
            if Wplz <= 0 or Wply <= 0:
                ready = False
            else:
                manual.update({"W_pl_z_eff_mm3": float(Wplz), "W_pl_y_eff_mm3": float(Wply)})
        if Iomega is not None:
            ready = ready and Iomega > 0
            if Iomega > 0:
                manual["I_omega_n_mm6"] = float(Iomega)
        if Womega is not None:
            ready = ready and Womega > 0
            if Womega > 0:
                manual["W_omega_eff_mm4"] = float(Womega)
        payload["manual_net_properties"] = manual

    return (payload if ready else None), None, ready


def _table1_editor(core: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core.st
    fields = list(card.get("fields") or [])
    if len(fields) != 1:
        return None
    field = fields[0]
    qid = str(field.get("quantity_id") or "")
    if not qid.startswith("sp16_gamma_c_case_"):
        return None
    options = list(card.get("options") or field.get("enum_values") or [])
    if not options:
        return None
    values = [row.get("value") for row in options]
    by_value = {row.get("value"): row for row in options}
    current = old if old in values else None
    role = qid.removeprefix("sp16_gamma_c_case_")
    role_ru = {"bending": "изгиба", "compression": "сжатия", "tension": "растяжения", "nm": "совместного действия N и M"}.get(role, "текущей проверки")
    st.markdown(f"**Коэффициент условий работы γc для {role_ru}**")
    if role == "compression":
        st.info("Это γc именно для проверки сжатия/устойчивости. Ранее выбранный случай для изгиба относится к другой расчётной проверке и не переносится автоматически, если нормативный случай не доказан однозначно.")
    selected = st.selectbox("Условия работы элемента", values, index=values.index(current) if current in values else None, placeholder="— выберите описание, соответствующее вашему элементу —", format_func=lambda value: _TABLE1_HUMAN.get(str(value), str(by_value[value].get("label") or value)), key=core._key(mode_key, card["node_id"], "table1-human"))
    if selected is not None:
        detail = by_value[selected].get("description")
        if detail:
            st.caption(f"Нормативное значение: {detail}.")
    st.caption("Номер позиции таблицы сохраняется в evidence, но в интерфейсе основной выбор показан по инженерному смыслу, а не по коду позиции.")
    return selected, None, selected is not None


def _legacy_payload(card: Mapping[str, Any], answer: bool):
    fields = list(card.get("fields") or [])
    if card.get("submit_shape") == "scalar":
        return answer
    if len(fields) == 1 and fields[0].get("quantity_id"):
        return {fields[0]["quantity_id"]: answer}
    return None


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous_card = core._render_card_body
    previous_trace = core._render_ledger_trace

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        component = str((card.get("presentation") or {}).get("component") or "generic")
        if component == "section_weakening_editor":
            return _weakening_editor(core, card, old_payload, mode_key)

        if _is_legacy_iw(card):
            if mode_key == "current":
                model = _ledger_value(env, "section_weakening_model")
                if isinstance(model, Mapping) and isinstance(model.get("holes_present"), bool):
                    payload = _legacy_payload(card, bool(model["holes_present"]))
                    if payload is not None:
                        app.service.submit(sid, payload, provenance={"source": "section_weakening_model", "ui_surface": "v0.107_compatibility_auto_resolution"})
                        core.st.rerun()
            # Hard invariant: compatibility card is never rendered, including history/edit.
            return None, None, False

        table1 = _table1_editor(core, card, old_payload, mode_key)
        if table1 is not None:
            return table1
        return previous_card(app, sid, env, card, old_payload, old_provenance, mode_key)

    def _render_ledger_trace(env):
        st = core.st
        key = "fire:v0106:show-report"
        show = st.checkbox("Показать расчётный отчёт", value=bool(st.session_state.get(key, False)), key=key)
        if not show:
            st.caption("Отчёт скрыт для ускорения ввода. Он строится только по запросу; расчётный DAG при этом продолжает выполняться независимо.")
            return
        previous_trace(env)

    core._render_card_body = _render_card_body
    core._render_ledger_trace = _render_ledger_trace
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_is_legacy_iw", "_legacy_payload", "_TABLE1_HUMAN"]
