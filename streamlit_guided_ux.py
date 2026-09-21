from __future__ import annotations

"""Presentation-only guided UX refinements for the Streamlit calculator.

This module does not change normative equations, DAG routing, or PASS/FAIL gates.
It only supplies explicit UI defaults, human-readable labels, diagnostics and
compact summaries.
"""

from copy import deepcopy
import json
from typing import Any, Mapping


TABLE32_LABELS = {
    "1a": "1a — Пояса, опорные раскосы и стойки, передающие опорные реакции: плоские фермы и пространственные конструкции из труб/парных уголков высотой до 50 м",
    "1b": "1b — То же: пространственные конструкции из одиночных уголков, а также из труб/парных уголков высотой свыше 50 м",
    "2a": "2a — Элементы, кроме позиций 1 и 7: плоские фермы, сварные пространственные/структурные конструкции, трубы и парные уголки",
    "2b": "2b — Элементы пространственных и структурных конструкций из одиночных уголков с болтовыми соединениями",
    "3": "3 — Верхние пояса ферм, не закреплённые в процессе монтажа",
    "4": "4 — Основные колонны",
    "5": "5 — Второстепенные колонны, элементы решётки колонн, вертикальные связи ниже подкрановых балок, балки и прогоны с учётом сжатия",
    "6": "6 — Элементы связей, стержни для уменьшения расчётной длины и другие ненагруженные элементы (кроме позиций 5 и 7)",
    "7": "7 — Сжатые/ненагруженные элементы пространственных конструкций таврового или крестового сечения при проверке от ветра в вертикальной плоскости",
}

TABLE9_LABELS = {
    "group_1_i_section": "Группа 1 — двутавровые и родственные двусимметричные сечения",
    "group_2_box_section": "Группа 2 — замкнутые / коробчатые сечения",
    "group_3_channel_section": "Группа 3 — открытые швеллерные сечения",
    "group_4_tee_section": "Группа 4 — тавровые сечения",
}

TABLE10_LABELS = {
    "group_1": "Группа 1 — полки двутавровых и тавровых сечений (первая строка диаграмм)",
    "group_2": "Группа 2 — свесы открытых прокатных/гнутых профилей (вторая строка диаграмм)",
    "group_3": "Группа 3 — свесы уголкового типа (третья строка диаграмм)",
    "group_4": "Группа 4 — профили с отгибом/краевым элементом (четвёртая строка диаграмм)",
}

PROFILE_LABELS = {
    "h_mm": ("Высота сечения", "h", "mm"),
    "b_mm": ("Ширина полки", "b", "mm"),
    "s_mm": ("Толщина стенки", "s", "mm"),
    "tw_mm": ("Толщина стенки", "t_w", "mm"),
    "t_mm": ("Толщина полки", "t", "mm"),
    "tf_mm": ("Толщина полки", "t_f", "mm"),
    "r_mm": ("Радиус сопряжения", "r", "mm"),
    "A_mm2": ("Площадь сечения", "A", "mm²"),
    "Ix_mm4": ("Момент инерции", "I_x", "mm⁴"),
    "Iy_mm4": ("Момент инерции", "I_y", "mm⁴"),
    "Wx_mm3": ("Момент сопротивления", "W_x", "mm³"),
    "Wy_mm3": ("Момент сопротивления", "W_y", "mm³"),
    "ix_mm": ("Радиус инерции", "i_x", "mm"),
    "iy_mm": ("Радиус инерции", "i_y", "mm"),
    "Sx_mm3": ("Статический момент", "S_x", "mm³"),
    "Sy_mm3": ("Статический момент", "S_y", "mm³"),
    "mass_kg_m": ("Масса 1 м профиля", "m", "kg/m"),
}

MATERIAL_LABELS = (
    ("Ryn_MPa", "Нормативное сопротивление по пределу текучести", "Ryn"),
    ("Run_MPa", "Нормативное сопротивление по временному сопротивлению", "Run"),
    ("Ry_MPa", "Расчётное сопротивление по пределу текучести", "Ry"),
    ("Ru_MPa", "Расчётное сопротивление по временному сопротивлению", "Ru"),
)


def _card_text(card: Mapping[str, Any]) -> str:
    return json.dumps(card, ensure_ascii=False, default=str).lower()


def _bool_default(card: Mapping[str, Any], qid: str) -> bool | None:
    """Return only presentation defaults explicitly approved for guided input."""
    if qid in {"sp16_mech7_fatigue_required", "sp16_mech7_brittle_required"}:
        return False

    text = _card_text(card)
    if "потеря элемента" in text and "прогрессирующ" in text:
        return True
    if "мембран" in text and "оболоч" in text:
        return False
    if "бимомент" in text and ("обычн" in text or "ambient" in text or "расчетн" in text or "расчётн" in text):
        return False
    return None


def _ledger_value(core: Any, qid: str) -> Any:
    try:
        app = core._ensure_app()
        sid = core._ensure_session(app)
        env = app.session(sid)
        return core._ledger_value(env, qid)
    except Exception:
        return None


def _with_guided_defaults(core: Any, card: Mapping[str, Any], old_payload: Any) -> Any:
    """Apply only non-normative, explicitly approved convenience defaults.

    Table 9/10 diagram groups and the flange-edge-stiffener flag are
    intentionally excluded. Their bundled normative catalogues require
    explicit engineering classification and do not provide an automatic
    geometry classifier.
    """
    fields = list(card.get("fields") or [])
    scalar = card.get("submit_shape") == "scalar"
    out = old_payload if scalar else dict(old_payload or {})

    for field in fields:
        qid = str(field.get("quantity_id") or "")
        current = out if scalar else out.get(qid)
        if current is not None:
            continue

        default: Any = None
        if field.get("data_type") == "boolean":
            default = _bool_default(card, qid)

        if default is not None:
            if scalar:
                out = default
            else:
                out[qid] = default
    return out


def _humanize_mech7_card(card: Mapping[str, Any]) -> dict[str, Any]:
    patched = deepcopy(dict(card))
    fields = []
    for raw in list(card.get("fields") or []):
        field = deepcopy(dict(raw))
        qid = str(field.get("quantity_id") or "")
        if qid == "sp16_mech7_table32_row":
            field["label"] = "Элемент конструкции по таблице 32 СП16"
        elif qid == "sp16_mech7_group4_slenderness_increase":
            field["label"] = "Относится ли конструкция к группе 4 для увеличения предельной гибкости?"
        elif qid == "sp16_mech7_table9_group":
            field["label"] = "Группа диаграммы таблицы 9 для стенки"
        elif qid == "sp16_mech7_table10_group":
            field["label"] = "Группа диаграммы таблицы 10 для полки"
        elif qid == "sp16_mech7_flange_edge_stiffened":
            field["label"] = "Есть ли краевое подкрепление свободного края полки?"
        fields.append(field)
    patched["fields"] = fields

    qids = {str(f.get("quantity_id") or "") for f in fields}
    guidance = list((patched.get("presentation") or {}).get("guidance") or [])

    if "sp16_mech7_group4_slenderness_increase" in qids:
        note = (
            "Важно: «группа 4» здесь — классификация конструкции для таблицы 32, "
            "а не группа поперечного сечения. Её нельзя определять только по тому, "
            "что выбран двутавр, швеллер или другой профиль."
        )
        if note not in guidance:
            guidance.append(note)

    if qids & {
        "sp16_mech7_table9_group",
        "sp16_mech7_table10_group",
        "sp16_mech7_flange_edge_stiffened",
    }:
        note = (
            "Таблицы 9 и 10 требуют явной инженерной классификации по схемам СП16. "
            "Выбранный профиль помогает сузить варианты, но приложение не записывает "
            "группу диаграммы или наличие краевого подкрепления автоматически."
        )
        if note not in guidance:
            guidance.append(note)

    if guidance:
        presentation = deepcopy(dict(patched.get("presentation") or {}))
        presentation["guidance"] = guidance
        patched["presentation"] = presentation
    return patched


def _sp16_completion_diagnostics(env: Mapping[str, Any]) -> dict[str, Any] | None:
    """Extract an auditable UI-only SP16 completion diagnosis from the ledger."""
    state = env.get("state")
    if not isinstance(state, Mapping):
        return None

    report = None
    for row in state.get("ledger", []) or []:
        if isinstance(row, Mapping) and row.get("quantity_id") == "sp16_mechanical_verification":
            report = row.get("value")
            break
    if not isinstance(report, Mapping):
        return None

    gate_status = str(report.get("gate_status") or "")
    rows = [dict(row) for row in report.get("rows", []) or [] if isinstance(row, Mapping)]
    unresolved = [
        row for row in rows
        if row.get("status") in {"DEFERRED", "CONTEXT_UNRESOLVED"}
    ]
    failed = [row for row in rows if row.get("status") == "FAIL"]
    return {
        "gate_status": gate_status,
        "unresolved": unresolved,
        "failed": failed,
        "unresolved_check_ids": list(report.get("unresolved_check_ids") or []),
        "failed_check_ids": list(report.get("failed_check_ids") or []),
    }


def _render_sp16_completion_diagnostics(core: Any, env: Mapping[str, Any]) -> None:
    diag = _sp16_completion_diagnostics(env)
    if not diag:
        return
    gate_status = diag["gate_status"]
    if gate_status not in {"INCOMPLETE_FAIL_CLOSED", "FAIL"}:
        return

    st = core._st()
    if gate_status == "INCOMPLETE_FAIL_CLOSED":
        rows = diag["unresolved"]
        st.warning(
            "СП16 не завершён: ниже показаны конкретные незакрытые проверки. "
            "Переход к СП554 остаётся fail-closed до их разрешения."
        )
    else:
        rows = diag["failed"]
        st.error("СП16 завершён с непройденными проверками. Переход к СП554 запрещён.")

    if not rows:
        ids = diag["unresolved_check_ids"] if gate_status == "INCOMPLETE_FAIL_CLOSED" else diag["failed_check_ids"]
        if ids:
            st.markdown("**Проверки:** " + ", ".join(f"`{item}`" for item in ids))
        return

    for row in rows:
        check_id = str(row.get("id") or "unknown")
        label = str(row.get("label") or check_id)
        status = str(row.get("status") or "")
        st.markdown(f"- **{label}** (`{check_id}`) — `{status}`")
        reason = row.get("reason")
        if reason:
            st.caption(str(reason))
        source = row.get("evidence_source")
        scope = row.get("normative_scope") or row.get("evidence_scope") or []
        details = []
        if source:
            details.append(f"evidence: {source}")
        if scope:
            details.append("scope: " + ", ".join(str(item) for item in scope))
        if details:
            st.caption(" · ".join(details))


def _profile_line(core: Any, key: str, value: Any) -> str:
    label = PROFILE_LABELS.get(key)
    if label:
        name, symbol, unit = label
        return f"- {name} **{symbol} = {core._fmt(value)} {unit}**"
    return f"- `{key}` = **{core._fmt(value)}**"


def _render_profile_catalog(core: Any, app: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core._st()
    old = old if isinstance(old, Mapping) else {}
    data = app.profile_catalog_families()
    families = [f for f in data["families"] if f.get("shape_group") not in {"C_LIPPED_SECTION", "Z_SECTION"}]
    family_ids = [int(f["family_id"]) for f in families]
    fmap = {int(f["family_id"]): f for f in families}
    current_family = int(old.get("section_catalog_family_id") or 0)
    family_id = st.selectbox(
        "Сортамент / семейство", family_ids,
        index=family_ids.index(current_family) if current_family in family_ids else None,
        placeholder="— выберите семейство —",
        format_func=lambda fid: str(fmap[fid].get("caption") or fid),
        key=core._key(mode_key, card["node_id"], "family"),
    )
    if family_id is None:
        return None, None, False

    rows = app.profile_catalog_profiles(int(family_id))["profiles"]
    refs = [(str(r["designation"]), int(r["source_row_id"])) for r in rows]
    current_ref = (str(old.get("section_designation") or ""), int(old.get("section_catalog_source_row_id") or 0))
    selected = st.selectbox(
        "Профиль", refs,
        index=refs.index(current_ref) if current_ref in refs else None,
        placeholder="— выберите профиль —", format_func=lambda r: r[0],
        key=core._key(mode_key, card["node_id"], "profile", family_id),
    )
    if selected is None:
        return None, None, False

    designation, source_row_id = selected
    resolved = app.profile_catalog_resolve(int(family_id), designation, source_row_id)
    shape = str(resolved.get("shape_group") or "OTHER")
    dims = resolved.get("dimensions") or {}
    props = resolved.get("catalog_properties_interim") or {}

    with st.container(border=True):
        st.markdown(f"**Характеристики профиля {designation}**")
        for key, value in {**dims, **props}.items():
            if value is not None:
                st.markdown(_profile_line(core, str(key), value))
    st.caption(f"Тип: {shape}. Каталог interim до original-GOST audit; source row {source_row_id}.")

    payload = {
        "section_catalog_standard": ((resolved.get("source") or {}).get("product_standard_label_unverified") or (resolved.get("family") or {}).get("caption") or "catalog"),
        "section_designation": designation,
        "section_family": core._section_family_from_shape(shape),
        "sp16_i_symmetry_class": "double_symmetric" if shape == "I_ROLLED_DSYMM" else "not_i",
        "section_catalog_family_id": int(family_id),
        "section_catalog_source_row_id": int(source_row_id),
    }
    return payload, None, True


def _render_material(core: Any, app: Any, sid: str, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core._st()
    old = old if isinstance(old, Mapping) else {}
    catalog = app.material_strength_catalog()
    context = app.material_strength_context(sid)
    products = list(catalog.get("products") or [])
    pvals = [str(p["value"]) for p in products]
    pmap = {str(p["value"]): p for p in products}
    suggested = str(old.get("steel_product_form") or context.get("suggested_product_form") or "")
    product = st.selectbox(
        "Вид проката / изделия", pvals,
        index=pvals.index(suggested) if suggested in pvals else None,
        placeholder="— выберите —",
        format_func=lambda x: f"{pmap[x].get('label', x)} · СП16 {pmap[x].get('source_table','')}",
        key=core._key(mode_key, card["node_id"], "product"),
    )
    if context.get("suggestion_reason"):
        st.caption(f"Предложено по выбранному сечению: {context['suggestion_reason']}")
    if not product:
        return None, None, False

    grades = list(pmap[product].get("grades") or [])
    gvals = [str(g["steel_grade"]) for g in grades]
    gmap = {str(g["steel_grade"]): g for g in grades}
    oldg = str(old.get("steel_grade") or "")
    grade = st.selectbox(
        "Марка стали", gvals,
        index=gvals.index(oldg) if oldg in gvals else None,
        placeholder="— выберите —",
        key=core._key(mode_key, card["node_id"], "grade", product),
    )
    if not grade:
        return None, None, False

    intervals = list(gmap[grade].get("intervals") or [])
    ivals = [str(r["interval_key"]) for r in intervals]
    imap = {str(r["interval_key"]): r for r in intervals}
    oldi = str(old.get("steel_strength_interval_key") or "")
    exact = context.get("exact_governing_thickness_mm")
    suggested_i = oldi
    if suggested_i not in ivals and isinstance(exact, (int, float)) and exact > 0 and context.get("suggested_product_form") == product:
        match = next((r for r in intervals if core._interval_contains(r, float(exact))), None)
        if match:
            suggested_i = str(match["interval_key"])
    interval = st.selectbox(
        "Толщина для выбора сопротивлений", ivals,
        index=ivals.index(suggested_i) if suggested_i in ivals else None,
        placeholder="— выберите диапазон —",
        format_func=lambda x: str(imap[x].get("interval_label") or x),
        key=core._key(mode_key, card["node_id"], "interval", product, grade),
    )
    if isinstance(exact, (int, float)) and exact > 0:
        st.caption(f"Определяющая толщина из геометрии: {core._fmt(exact)} мм")
    if not interval:
        return None, None, False

    r = imap[interval]
    with st.container(border=True):
        st.markdown("**Расчётные характеристики стали**")
        for key, name, symbol in MATERIAL_LABELS:
            st.markdown(f"- {name}, **{symbol} = {core._fmt(r.get(key))} MPa**")

    payload = {"steel_product_form": product, "steel_grade": grade, "steel_strength_interval_key": interval}
    if isinstance(exact, (int, float)) and exact > 0 and context.get("suggested_product_form") == product and core._interval_contains(r, float(exact)):
        payload["governing_product_thickness_mm"] = float(exact)
    return payload, None, True


def install(core: Any) -> None:
    original_generic = core._render_generic
    original_options = core._generic_options
    original_noninteractive = core._render_noninteractive

    def guided_options(card: Mapping[str, Any], field: Mapping[str, Any]):
        qid = str(field.get("quantity_id") or "")
        mapping = None
        if qid == "sp16_mech7_table32_row":
            mapping = TABLE32_LABELS
        elif qid == "sp16_mech7_table9_group":
            mapping = TABLE9_LABELS
        elif qid == "sp16_mech7_table10_group":
            mapping = TABLE10_LABELS
        if mapping is not None:
            return [{"value": value, "label": label} for value, label in mapping.items()]
        return original_options(card, field)

    def guided_generic(card: Mapping[str, Any], old_payload: Any, old_provenance: Mapping[str, Any] | None, mode_key: str):
        patched_card = _humanize_mech7_card(card)
        patched_old = _with_guided_defaults(core, patched_card, old_payload)
        return original_generic(patched_card, patched_old, old_provenance, mode_key)

    def guided_profile(app: Any, card: Mapping[str, Any], old: Any, mode_key: str):
        return _render_profile_catalog(core, app, card, old, mode_key)

    def guided_material(app: Any, sid: str, card: Mapping[str, Any], old: Any, mode_key: str):
        return _render_material(core, app, sid, card, old, mode_key)

    def guided_noninteractive(env: Mapping[str, Any], card: Mapping[str, Any] | None):
        original_noninteractive(env, card)
        _render_sp16_completion_diagnostics(core, env)

    core._generic_options = guided_options
    core._render_generic = guided_generic
    core._render_profile_catalog = guided_profile
    core._render_material = guided_material
    core._render_noninteractive = guided_noninteractive
