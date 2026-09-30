"""v0.106 guided UX closure.

Closes six user-visible defects without changing normative arithmetic:
- weakening choice has no implicit default and cannot become ready until the user
  explicitly chooses no holes / bolt holes;
- legacy I/W weakening compatibility cards are never rendered;
- retained Table-1 selectors use human-readable engineering descriptions;
- compression gamma_c is explicitly distinguished from bending gamma_c;
- the heavy expertise report is rendered only on explicit request, so ordinary
  widget reruns (fatigue/brittle/slenderness etc.) stay lightweight;
- MECH7 route repair itself lives in the v0.106 graph overlay.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v0106_guided_ux_closure_installed"

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
    text = " ".join(str(card.get(k) or "") for k in ("node_id", "title", "prompt" )).lower()
    notes = card.get("notes") or {}
    text += " " + " ".join(str(v) for v in notes.values()).lower()
    fields = {str(f.get("quantity_id") or "").lower() for f in card.get("fields", []) if isinstance(f, Mapping)}
    if any(token in text for token in _LEGACY_IW_TEXT):
        return True
    return any(("weak" in q or "net" in q) and ("inertia" in q or "iw" in q or "section_mod" in q) for q in fields)


def _ledger_value(env: Mapping[str, Any], qid: str):
    for row in (env.get("state") or {}).get("ledger", []):
        if row.get("quantity_id") == qid:
            return row.get("value")
    return None


def _weakening_editor(core: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core.st
    old = old if isinstance(old, Mapping) else {}
    old_choice = None
    if old:
        old_choice = "holes" if old.get("holes_present") else "none"
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
    ready = d > 0 and s > d and (t is None or t > 0)
    if s <= d:
        st.warning("Требуется s > d.")
    payload = {"schema": "section_weakening_model_v0.49", "holes_present": True, "model": "round_bolt_hole_universal_v1", "hole_diameter_mm": float(d), "hole_pitch_mm": float(s)}
    if t is not None and t > 0:
        payload["local_thickness_mm"] = float(t)
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
    selected = st.selectbox(
        "Условия работы элемента",
        values,
        index=values.index(current) if current in values else None,
        placeholder="— выберите описание, соответствующее вашему элементу —",
        format_func=lambda value: _TABLE1_HUMAN.get(str(value), str(by_value[value].get("label") or value)),
        key=core._key(mode_key, card["node_id"], "table1-human"),
    )
    if selected is not None:
        row = by_value[selected]
        detail = row.get("description")
        if detail:
            st.caption(f"Нормативное значение: {detail}.")
    st.caption("Номер позиции таблицы сохраняется в evidence, но в интерфейсе основной выбор показан по инженерному смыслу, а не по коду позиции.")
    return selected, None, selected is not None


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
            model = _ledger_value(env, "section_weakening_model")
            if isinstance(model, Mapping):
                # Compatibility value only; never expose a second engineering question.
                answer = bool(model.get("holes_present"))
                if mode_key == "current":
                    try:
                        app.service.submit(sid, answer, provenance={"source": "section_weakening_model", "ui_surface": "v0.106_compatibility_auto_resolution"})
                        core.st.rerun()
                    except Exception:
                        pass
            return None, None, False

        table1 = _table1_editor(core, card, old_payload, mode_key)
        if table1 is not None:
            return table1

        if str(card.get("node_id") or "") == "SP16_I_V078_GAMMA_C_COMPRESSION_CASE":
            core.st.info("Это γc именно для проверки сжатия/устойчивости. Ранее выбранный случай для изгиба относится к другой расчётной проверке и не переносится автоматически, если нормативный случай не доказан однозначно.")

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


__all__ = ["install", "_is_legacy_iw", "_TABLE1_HUMAN"]
