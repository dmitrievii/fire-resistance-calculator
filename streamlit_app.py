from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import streamlit as st

from standard_core.fire_ui0 import FireUIError
from standard_core.fire_ui1_http import FireUI1Application


ROOT = Path(__file__).resolve().parent

BASIC_TYPES = {"number", "integer", "boolean", "enum", "string", "text"}

STRUCTURED_COMPONENTS = {
    "manual_section_properties_editor",
    "section_weakening_editor",
    "documented_performance_matrix_editor",
    "ambient_signed_load_menu",
    "fire_signed_load_menu",
}

SCALAR_COMPONENTS = {
    "section_editor_entry",
    "required_r_selector",
    "bimoment_direct_input",
    "table30_scheme_selector",
    "table7_curve_selector",
    "table21_type_selector",
    "heated_sides_selector",
    "protection_perimeter_mode_selector",
    "post_fire_resistance_action_selector",
}

SUMMARY_COMPONENTS = {
    "verification_plan_summary",
    "applicability_census_summary",
}

CUSTOM_COMPONENTS = STRUCTURED_COMPONENTS | SCALAR_COMPONENTS | SUMMARY_COMPONENTS | {
    "profile_catalog_selector",
    "parametric_section_editor",
    "double_branch_section_editor",
    "material_strength_editor",
}

STYLES = r"""
<style>
:root {
  --fire-border: rgba(49, 51, 63, 0.18);
  --fire-soft: rgba(49, 51, 63, 0.055);
  --fire-muted: rgba(49, 51, 63, 0.68);
}
.block-container {padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 1500px;}
[data-testid="stHeader"] {background: transparent;}
.fire-hero {padding: .3rem 0 1rem 0;}
.fire-title {font-size: 1.72rem; font-weight: 760; letter-spacing: -.025em; margin-bottom: .1rem;}
.fire-subtitle {color: var(--fire-muted); font-size: .96rem;}
.fire-status {
  display: inline-flex; gap: .45rem; align-items: center; padding: .36rem .68rem;
  border: 1px solid var(--fire-border); border-radius: 999px; font-size: .82rem;
  background: var(--fire-soft); margin-right: .35rem;
}
.fire-card {
  border: 1px solid var(--fire-border); border-radius: 16px; padding: 1rem 1.05rem;
  background: rgba(255,255,255,.018); margin-bottom: .75rem;
}
.fire-kicker {font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: var(--fire-muted); margin-bottom: .35rem;}
.fire-card h3 {margin: .15rem 0 .35rem 0;}
.fire-note {color: var(--fire-muted); font-size: .9rem;}
.fire-ref {
  display: inline-block; border: 1px solid var(--fire-border); border-radius: 8px;
  padding: .22rem .42rem; margin: .18rem .22rem .05rem 0; font-size: .76rem;
}
.fire-ledger-row {padding: .52rem 0; border-bottom: 1px solid var(--fire-border);}
.fire-ledger-name {font-size: .86rem; color: var(--fire-muted);}
.fire-ledger-value {font-size: 1rem; font-weight: 650;}
.fire-small {font-size: .78rem; color: var(--fire-muted);}
.fire-result {padding: .8rem 1rem; border-left: 4px solid currentColor; background: var(--fire-soft); border-radius: 8px;}
div[data-testid="stMetric"] {border: 1px solid var(--fire-border); padding: .6rem .7rem; border-radius: 12px;}
</style>
"""


def _key(prefix: str, *parts: Any) -> str:
    return "fire:" + prefix + ":" + ":".join(str(p) for p in parts)


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        a = abs(value)
        if (a and a < 1e-4) or a >= 1e7:
            return f"{value:.5e}"
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _option_label(option: Mapping[str, Any]) -> str:
    return str(option.get("label") or option.get("value"))


def _card_map(app: FireUI1Application) -> dict[str, dict[str, Any]]:
    if "_fire_contract_map" not in st.session_state:
        contract = app.ui_contract()
        st.session_state["_fire_contract"] = contract
        st.session_state["_fire_contract_map"] = {c["node_id"]: c for c in contract["node_cards"]}
    return st.session_state["_fire_contract_map"]


def _new_application() -> FireUI1Application:
    return FireUI1Application.from_package_root(ROOT)


def _ensure_app() -> FireUI1Application:
    app = st.session_state.get("_fire_app")
    if app is None:
        app = _new_application()
        st.session_state["_fire_app"] = app
    return app


def _ensure_session(app: FireUI1Application) -> str:
    sid = st.session_state.get("_fire_session_id")
    if not sid or sid not in app.service.sessions:
        created = app.create_session()
        sid = created["session_id"]
        st.session_state["_fire_session_id"] = sid
        st.session_state["_fire_edit_node"] = None
    return sid


def _reset_calculation() -> None:
    st.session_state["_fire_app"] = _new_application()
    st.session_state.pop("_fire_contract", None)
    st.session_state.pop("_fire_contract_map", None)
    created = st.session_state["_fire_app"].create_session()
    st.session_state["_fire_session_id"] = created["session_id"]
    st.session_state["_fire_edit_node"] = None
    for k in list(st.session_state):
        if k.startswith("fire:"):
            del st.session_state[k]


def _refs(card: Mapping[str, Any] | None) -> None:
    refs = list((card or {}).get("normative_refs") or [])
    if not refs:
        return
    text = []
    for r in refs:
        parts = [str(r.get("standard_id") or "Норма")]
        if r.get("section"):
            parts.append(f"разд. {r['section']}")
        if r.get("clause"):
            parts.append(f"п. {r['clause']}")
        if r.get("formula_ref"):
            parts.append(f"формула {r['formula_ref']}")
        if r.get("table_ref"):
            parts.append(f"табл. {r['table_ref']}")
        text.append(f'<span class="fire-ref">{" · ".join(parts)}</span>')
    st.markdown("".join(text), unsafe_allow_html=True)


def _ledger_value(env: Mapping[str, Any], qid: str, default: Any = None) -> Any:
    for row in env["state"].get("ledger", []):
        if row.get("quantity_id") == qid:
            return row.get("value")
    return default


def _history_payload(env: Mapping[str, Any], node_id: str) -> tuple[Any, Any]:
    for row in env["state"].get("interaction_history", []):
        if row.get("node_id") == node_id:
            return row.get("payload"), row.get("provenance")
    return None, None


def _edit_context(app: FireUI1Application, env: Mapping[str, Any]) -> tuple[dict[str, Any] | None, Any, Any]:
    node_id = st.session_state.get("_fire_edit_node")
    if not node_id:
        return None, None, None
    card = _card_map(app).get(node_id)
    if card is None:
        st.session_state["_fire_edit_node"] = None
        return None, None, None
    payload, provenance = _history_payload(env, node_id)
    return card, payload, provenance


def _submit(
    app: FireUI1Application,
    sid: str,
    card: Mapping[str, Any],
    payload: Any,
    provenance: Mapping[str, Any] | None,
    editing: bool,
) -> None:
    try:
        if editing:
            app.service.edit(sid, card["node_id"], payload, provenance=provenance)
            st.session_state["_fire_edit_node"] = None
        else:
            app.service.submit(sid, payload, provenance=provenance)
        st.rerun()
    except FireUIError as exc:
        st.error(str(exc))


def _generic_options(card: Mapping[str, Any], field: Mapping[str, Any]) -> list[dict[str, Any]]:
    if field.get("data_type") == "boolean":
        return [{"value": True, "label": "Да"}, {"value": False, "label": "Нет"}]
    if card.get("node_type") == "decision" and card.get("options"):
        return list(card["options"])
    return list(field.get("enum_values") or [])


def _render_generic(
    card: Mapping[str, Any],
    old_payload: Any,
    old_provenance: Mapping[str, Any] | None,
    mode_key: str,
) -> tuple[Any, dict[str, Any] | None, bool]:
    fields = list(card.get("fields") or [])
    structured = [f for f in fields if f.get("data_type") not in BASIC_TYPES]
    if structured:
        st.error(
            "Эта ветвь требует специального структурированного редактора. "
            "Streamlit не подменяет его ручным JSON и останавливается fail-closed."
        )
        st.caption(", ".join(f"{f['quantity_id']} ({f.get('data_type')})" for f in structured))
        return None, None, False

    scalar = card.get("submit_shape") == "scalar"
    result: dict[str, Any] = {}
    ready = True

    for field in fields:
        qid = field["quantity_id"]
        dtype = field.get("data_type")
        current = old_payload if scalar else (old_payload or {}).get(qid)
        label = field.get("label") or qid
        unit = field.get("canonical_unit")
        shown_label = f"{label}" + (f", {unit}" if unit else "")
        k = _key(mode_key, card["node_id"], qid)

        value: Any = None
        if dtype in {"number", "integer"}:
            if dtype == "integer":
                base = int(current) if isinstance(current, (int, float)) and not isinstance(current, bool) else None
                value = st.number_input(shown_label, value=base, step=1, key=k)
                if value is not None:
                    value = int(value)
            else:
                base = float(current) if isinstance(current, (int, float)) and not isinstance(current, bool) else None
                value = st.number_input(shown_label, value=base, format="%g", key=k)
                if value is not None:
                    value = float(value)
        elif dtype in {"enum", "boolean"}:
            options = _generic_options(card, field)
            values = [o["value"] for o in options]
            labels = {json.dumps(o["value"], ensure_ascii=False): _option_label(o) for o in options}
            idx = values.index(current) if current in values else None
            value = st.selectbox(
                shown_label,
                values,
                index=idx,
                placeholder="— выберите —",
                format_func=lambda v: labels.get(json.dumps(v, ensure_ascii=False), str(v)),
                key=k,
            )
        elif dtype == "text":
            value = st.text_area(shown_label, value=str(current or ""), key=k)
            value = value.strip() or None
        else:
            value = st.text_input(shown_label, value=str(current or ""), key=k)
            value = value.strip() or None

        if value is None:
            if field.get("required") is not False:
                ready = False
        else:
            result[qid] = value

    payload: Any
    if scalar:
        qid = fields[0]["quantity_id"] if fields else None
        payload = result.get(qid) if qid else old_payload
        ready = ready and payload is not None
    else:
        payload = result

    provenance: dict[str, Any] | None = dict(old_provenance or {}) if old_provenance else None
    if card.get("external_handoff"):
        st.info(card.get("handoff_reason") or "Требуется проверяемый внешний нормативный источник.")
        doc = st.text_input(
            "Документ-источник",
            value=str((old_provenance or {}).get("source_document") or ""),
            key=_key(mode_key, card["node_id"], "prov_doc"),
        ).strip()
        ref = st.text_input(
            "Ссылка / пункт",
            value=str((old_provenance or {}).get("source_reference") or ""),
            key=_key(mode_key, card["node_id"], "prov_ref"),
        ).strip()
        provenance = {"source_document": doc, "source_reference": ref}
        if not doc or not ref:
            ready = False

    return payload, provenance, ready


def _render_section_entry(card: Mapping[str, Any], old: Any, mode_key: str):
    options = [
        ("catalog_section", "Из сортамента", "Семейство ГОСТ → профиль → свойства автоматически"),
        ("parametric_section", "Параметрическое", "Геометрические размеры по типу сечения"),
        ("double_branch_section", "Двухветвевое", "Две одинаковые ветви из сортамента"),
        ("arbitrary_section", "Произвольное", "Ручной ввод готовых характеристик"),
    ]
    values = [x[0] for x in options]
    labels = {x[0]: x[1] for x in options}
    current = old if old in values else None
    value = st.radio(
        "Способ задания сечения",
        values,
        index=values.index(current) if current in values else None,
        format_func=lambda v: labels[v],
        key=_key(mode_key, card["node_id"], "mode"),
    )
    for val, title, note in options:
        if value == val:
            st.caption(note)
    return value, None, value is not None


def _section_family_from_shape(shape: str) -> str:
    return {
        "I_ROLLED_DSYMM": "i_section",
        "CHANNEL": "channel",
        "ANGLE": "angle",
        "TEE": "tee",
        "RHS_SHS": "rhs_shs",
        "CHS": "chs",
        "C_LIPPED_SECTION": "other",
        "Z_SECTION": "other",
    }.get(shape, "other")


def _render_profile_catalog(app: FireUI1Application, card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    data = app.profile_catalog_families()
    families = [
        f for f in data["families"]
        if f.get("shape_group") not in {"C_LIPPED_SECTION", "Z_SECTION"}
    ]
    family_ids = [int(f["family_id"]) for f in families]
    fmap = {int(f["family_id"]): f for f in families}
    current_family = int(old.get("section_catalog_family_id") or 0)
    family_id = st.selectbox(
        "Сортамент / семейство",
        family_ids,
        index=family_ids.index(current_family) if current_family in family_ids else None,
        placeholder="— выберите семейство —",
        format_func=lambda fid: str(fmap[fid].get("caption") or fid),
        key=_key(mode_key, card["node_id"], "family"),
    )
    if family_id is None:
        return None, None, False

    rows = app.profile_catalog_profiles(int(family_id))["profiles"]
    refs = [(str(r["designation"]), int(r["source_row_id"])) for r in rows]
    current_ref = (
        str(old.get("section_designation") or ""),
        int(old.get("section_catalog_source_row_id") or 0),
    )
    selected = st.selectbox(
        "Профиль",
        refs,
        index=refs.index(current_ref) if current_ref in refs else None,
        placeholder="— выберите профиль —",
        format_func=lambda r: r[0],
        key=_key(mode_key, card["node_id"], "profile", family_id),
    )
    if selected is None:
        return None, None, False

    designation, source_row_id = selected
    resolved = app.profile_catalog_resolve(int(family_id), designation, source_row_id)
    shape = str(resolved.get("shape_group") or "OTHER")
    dims = resolved.get("dimensions") or {}
    props = resolved.get("catalog_properties_interim") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("h", f"{_fmt(dims.get('h_mm'))} mm")
    c2.metric("b", f"{_fmt(dims.get('b_mm'))} mm")
    c3.metric("A", f"{_fmt(props.get('A_mm2'))} mm²")
    c4.metric("Ix", f"{_fmt(props.get('Ix_mm4'))} mm⁴")
    st.caption(
        f"Тип: {shape}. Каталог interim до original-GOST audit; "
        f"source row {source_row_id}."
    )
    payload = {
        "section_catalog_standard": (
            (resolved.get("source") or {}).get("product_standard_label_unverified")
            or (resolved.get("family") or {}).get("caption")
            or "catalog"
        ),
        "section_designation": designation,
        "section_family": _section_family_from_shape(shape),
        "sp16_i_symmetry_class": "double_symmetric" if shape == "I_ROLLED_DSYMM" else "not_i",
        "section_catalog_family_id": int(family_id),
        "section_catalog_source_row_id": int(source_row_id),
    }
    return payload, None, True


def _render_parametric(card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    families = {
        "i_section": "Двутавр",
        "channel": "Швеллер",
        "angle": "Уголок",
        "tee": "Тавр",
        "rhs_shs": "Замкнутый прямоугольный/квадратный профиль",
        "chs": "Круглая труба",
    }
    vals = list(families)
    oldfam = old.get("section_family")
    fam = st.selectbox(
        "Тип сечения",
        vals,
        index=vals.index(oldfam) if oldfam in vals else None,
        placeholder="— выберите —",
        format_func=lambda v: families[v],
        key=_key(mode_key, card["node_id"], "family"),
    )
    if not fam:
        return None, None, False

    config = {
        "i_section": [("sec_h", "h, мм", True), ("sec_b", "b, мм", True), ("t_w", "tw, мм", True), ("t_f", "tf, мм", True), ("r_root", "r, мм", False)],
        "channel": [("sec_h", "h, мм", True), ("sec_b", "b, мм", True), ("t_w", "tw, мм", True), ("t_f", "tf, мм", True), ("r_root", "r, мм", False)],
        "tee": [("sec_h", "h, мм", True), ("sec_b", "b, мм", True), ("t_w", "tw, мм", True), ("t_f", "tf, мм", True), ("r_root", "r, мм", False)],
        "angle": [("sec_h", "полка 1, мм", True), ("sec_b", "полка 2, мм", True), ("t_w", "t, мм", True), ("r_root", "r, мм", False)],
        "rhs_shs": [("sec_h", "h, мм", True), ("sec_b", "b, мм", True), ("t_w", "t, мм", True)],
        "chs": [("sec_h", "D, мм", True), ("t_w", "t, мм", True)],
    }
    payload: dict[str, Any] = {"section_family": fam}
    ready = True
    cols = st.columns(2)
    for i, (qid, label, required) in enumerate(config[fam]):
        base = old.get(qid)
        val = cols[i % 2].number_input(
            label,
            value=float(base) if isinstance(base, (int, float)) else None,
            min_value=0.0,
            key=_key(mode_key, card["node_id"], fam, qid),
        )
        if val is None:
            if required:
                ready = False
        elif val <= 0:
            ready = False
        else:
            payload[qid] = float(val)
    if fam == "i_section":
        payload["sp16_i_symmetry_class"] = "double_symmetric"
    return payload if ready else None, None, ready


def _render_manual_section(card: Mapping[str, Any], old: Any, mode_key: str):
    old_obj = {}
    if isinstance(old, Mapping) and isinstance(old.get("section_geometry_2d"), Mapping):
        old_obj = dict(old["section_geometry_2d"])
    required = [
        ("A_gross", "A, мм²"),
        ("J_x", "Jx, мм⁴"),
        ("J_y", "Jy, мм⁴"),
        ("W_el_x_pos", "Wx,+, мм³"),
        ("W_el_x_neg", "Wx,−, мм³"),
        ("W_el_y_pos", "Wy,+, мм³"),
        ("W_el_y_neg", "Wy,−, мм³"),
        ("W_pl_x", "Wpl,x, мм³"),
        ("W_pl_y", "Wpl,y, мм³"),
    ]
    optional = [
        ("I_shear_gross", "I для среза, мм⁴"),
        ("S_shear_gross", "S для среза, мм³"),
        ("I_omega_gross", "Iω, мм⁶"),
        ("W_omega_gross", "Wω, мм⁴"),
        ("P_heated_m", "Нагреваемый периметр Π, м"),
    ]
    obj: dict[str, Any] = {}
    ready = True
    st.caption("Введите готовые характеристики сечения. 2D-контур в текущем scope не используется.")
    for i in range(0, len(required), 2):
        cols = st.columns(2)
        for col, (qid, label) in zip(cols, required[i:i+2]):
            base = old_obj.get(qid)
            v = col.number_input(
                label,
                value=float(base) if isinstance(base, (int, float)) else None,
                min_value=0.0,
                key=_key(mode_key, card["node_id"], qid),
            )
            if v is None or v <= 0:
                ready = False
            else:
                obj[qid] = float(v)
    with st.expander("Дополнительные характеристики"):
        for qid, label in optional:
            base = old_obj.get(qid)
            v = st.number_input(
                label,
                value=float(base) if isinstance(base, (int, float)) else None,
                min_value=0.0,
                key=_key(mode_key, card["node_id"], qid),
            )
            if v is not None and v > 0:
                obj[qid] = float(v)

    fams = ["other", "i_section", "channel", "rhs_shs", "chs"]
    labels = {
        "other": "Другое",
        "i_section": "Двутавр",
        "channel": "Швеллер",
        "rhs_shs": "Коробчатое",
        "chs": "Круглая труба",
    }
    oldfam = old_obj.get("section_family", "other")
    fam = st.selectbox(
        "Классификация",
        fams,
        index=fams.index(oldfam) if oldfam in fams else 0,
        format_func=lambda x: labels[x],
        key=_key(mode_key, card["node_id"], "manual_family"),
    )
    obj.update({
        "section_family": fam,
        "section_is_box": fam == "rhs_shs",
        "section_is_channel": fam == "channel",
        "section_is_pipe": fam == "chs",
        "sp16_i_symmetry_class": "double_symmetric" if fam == "i_section" else "not_i",
    })
    return ({"section_geometry_2d": obj} if ready else None), None, ready


def _render_double_branch(app: FireUI1Application, card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    axis = st.selectbox(
        "Ось симметрии",
        ["y", "x"],
        index=0 if old.get("double_branch_symmetry_axis", "y") == "y" else 1,
        format_func=lambda x: "Y — ветви разнесены по X" if x == "y" else "X — ветви разнесены по Y",
        key=_key(mode_key, card["node_id"], "axis"),
    )
    spacing = st.number_input(
        "Расстояние между центрами ветвей, мм",
        value=float(old["double_branch_spacing_mm"]) if isinstance(old.get("double_branch_spacing_mm"), (int, float)) else None,
        min_value=0.0,
        key=_key(mode_key, card["node_id"], "spacing"),
    )
    data = app.profile_catalog_families()
    families = [f for f in data["families"] if f.get("shape_group") not in {"C_LIPPED_SECTION", "Z_SECTION"}]
    ids = [int(f["family_id"]) for f in families]
    fmap = {int(f["family_id"]): f for f in families}
    of = int(old.get("double_branch_family_id") or 0)
    fid = st.selectbox(
        "Сортамент ветви",
        ids,
        index=ids.index(of) if of in ids else None,
        placeholder="— выберите —",
        format_func=lambda x: str(fmap[x].get("caption") or x),
        key=_key(mode_key, card["node_id"], "family"),
    )
    if fid is None or spacing is None or spacing <= 0:
        return None, None, False
    rows = app.profile_catalog_profiles(fid)["profiles"]
    refs = [(str(r["designation"]), int(r["source_row_id"])) for r in rows]
    oldref = (str(old.get("double_branch_designation") or ""), int(old.get("double_branch_source_row_id") or 0))
    ref = st.selectbox(
        "Профиль ветви",
        refs,
        index=refs.index(oldref) if oldref in refs else None,
        placeholder="— выберите профиль —",
        format_func=lambda x: x[0],
        key=_key(mode_key, card["node_id"], "profile", fid),
    )
    if ref is None:
        return None, None, False
    designation, row = ref
    resolved = app.profile_catalog_resolve(fid, designation, row)
    st.caption(f"{designation} · {(resolved.get('family') or {}).get('caption', '')} · source row {row}")
    return {
        "double_branch_symmetry_axis": axis,
        "double_branch_spacing_mm": float(spacing),
        "double_branch_family_id": int(fid),
        "double_branch_designation": designation,
        "double_branch_source_row_id": int(row),
    }, None, True


def _interval_contains(row: Mapping[str, Any], thickness: float) -> bool:
    x = row.get("thickness_interval") or {}
    lo, hi = x.get("min_mm"), x.get("max_mm")
    if lo is not None and (thickness < float(lo) or (thickness == float(lo) and not x.get("min_inclusive"))):
        return False
    if hi is not None and (thickness > float(hi) or (thickness == float(hi) and not x.get("max_inclusive"))):
        return False
    return True


def _render_material(app: FireUI1Application, sid: str, card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    catalog = app.material_strength_catalog()
    context = app.material_strength_context(sid)
    products = list(catalog.get("products") or [])
    pvals = [str(p["value"]) for p in products]
    pmap = {str(p["value"]): p for p in products}
    suggested = str(old.get("steel_product_form") or context.get("suggested_product_form") or "")
    product = st.selectbox(
        "Вид проката / изделия",
        pvals,
        index=pvals.index(suggested) if suggested in pvals else None,
        placeholder="— выберите —",
        format_func=lambda x: f"{pmap[x].get('label', x)} · СП16 {pmap[x].get('source_table','')}",
        key=_key(mode_key, card["node_id"], "product"),
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
        "Марка стали",
        gvals,
        index=gvals.index(oldg) if oldg in gvals else None,
        placeholder="— выберите —",
        key=_key(mode_key, card["node_id"], "grade", product),
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
        match = next((r for r in intervals if _interval_contains(r, float(exact))), None)
        if match:
            suggested_i = str(match["interval_key"])
    interval = st.selectbox(
        "Толщина для выбора Ryn",
        ivals,
        index=ivals.index(suggested_i) if suggested_i in ivals else None,
        placeholder="— выберите диапазон —",
        format_func=lambda x: str(imap[x].get("interval_label") or x),
        key=_key(mode_key, card["node_id"], "interval", product, grade),
    )
    if isinstance(exact, (int, float)) and exact > 0:
        st.caption(f"Определяющая толщина из геометрии: {_fmt(exact)} мм")
    if not interval:
        return None, None, False

    r = imap[interval]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ryn", f"{_fmt(r.get('Ryn_MPa'))} MPa")
    c2.metric("Run", f"{_fmt(r.get('Run_MPa'))} MPa")
    c3.metric("Ry", f"{_fmt(r.get('Ry_MPa'))} MPa")
    c4.metric("Ru", f"{_fmt(r.get('Ru_MPa'))} MPa")
    payload = {
        "steel_product_form": product,
        "steel_grade": grade,
        "steel_strength_interval_key": interval,
    }
    if isinstance(exact, (int, float)) and exact > 0 and context.get("suggested_product_form") == product and _interval_contains(r, float(exact)):
        payload["governing_product_thickness_mm"] = float(exact)
    return payload, None, True


def _render_weakening(card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    has_old = bool(old.get("holes_present"))
    choice = st.radio(
        "Ослабления",
        ["none", "holes"],
        index=1 if has_old else 0,
        format_func=lambda x: "Есть болтовые отверстия" if x == "holes" else "Отверстий нет",
        horizontal=True,
        key=_key(mode_key, card["node_id"], "weak"),
    )
    if choice == "none":
        return {"schema": "section_weakening_model_v0.49", "holes_present": False, "model": "none"}, None, True

    d = st.number_input(
        "Диаметр отверстия d, мм",
        min_value=0.0,
        value=float(old.get("hole_diameter_mm", 20.0)),
        key=_key(mode_key, card["node_id"], "d"),
    )
    s = st.number_input(
        "Шаг s, мм",
        min_value=0.0,
        value=float(old.get("hole_pitch_mm", 80.0)),
        key=_key(mode_key, card["node_id"], "s"),
    )
    t0 = old.get("local_thickness_mm")
    t = st.number_input(
        "Локальная толщина tₕ, мм (необязательно)",
        min_value=0.0,
        value=float(t0) if isinstance(t0, (int, float)) else None,
        key=_key(mode_key, card["node_id"], "t"),
    )
    ready = d > 0 and s > d and (t is None or t > 0)
    if s <= d:
        st.warning("Для формулы (45) требуется s > d.")
    payload = {
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": float(d),
        "hole_pitch_mm": float(s),
    }
    if t is not None and t > 0:
        payload["local_thickness_mm"] = float(t)
    return (payload if ready else None), None, ready


def _render_load_menu(card: Mapping[str, Any], old: Any, mode_key: str, kind: str):
    old = old if isinstance(old, Mapping) else {}
    ambient = kind == "ambient"
    q = (
        {"N": "ambient_N_force", "Mx": "ambient_M_x", "My": "ambient_M_y", "Qx": "ambient_Q_x", "Qy": "ambient_Q_y", "T": "ambient_T_torsion", "combo": "ambient_load_combination"}
        if ambient else
        {"N": "N_force", "Mx": "M_x", "My": "M_y", "Qx": "Q_x", "Qy": "Q_y", "T": "T_torsion", "combo": "special_load_combination"}
    )
    def oldv(qid: str, scale: float) -> float:
        v = old.get(qid, 0.0)
        return float(v) / scale if isinstance(v, (int, float)) else 0.0

    cols = st.columns(3)
    N = cols[0].number_input("N, кН", value=oldv(q["N"], 1e3), key=_key(mode_key, card["node_id"], "N"))
    Mx = cols[1].number_input("Mx, кН·м", value=oldv(q["Mx"], 1e6), key=_key(mode_key, card["node_id"], "Mx"))
    My = cols[2].number_input("My, кН·м", value=oldv(q["My"], 1e6), key=_key(mode_key, card["node_id"], "My"))
    cols = st.columns(3)
    Qx = cols[0].number_input("Qx, кН", value=oldv(q["Qx"], 1e3), key=_key(mode_key, card["node_id"], "Qx"))
    Qy = cols[1].number_input("Qy, кН", value=oldv(q["Qy"], 1e3), key=_key(mode_key, card["node_id"], "Qy"))
    T = cols[2].number_input("T, кН·м", value=oldv(q["T"], 1e6), key=_key(mode_key, card["node_id"], "T"))
    if Qy != 0 or T != 0:
        st.warning("Qy/T сохраняются как самостоятельные компоненты; неподдержанная downstream-ветвь остановится fail-closed. Qy→Qx и T→B запрещены.")
    combo = {
        "schema": "sp16_mech2_ambient_combination_v1" if ambient else "sp16_mech2_fire_special_combination_v1",
        "kind": "ambient" if ambient else "fire",
        "convention": "N>0 tension; N<0 compression; s member axis; x-x/y-y SP16 principal section axes",
        "display_units": {"force": "kN", "moment": "kNm"},
        "N_kN": N, "Mx_kNm": Mx, "My_kNm": My, "Qx_kN": Qx, "Qy_kN": Qy, "T_kNm": T,
    }
    payload = {
        q["combo"]: combo,
        q["N"]: float(N) * 1e3,
        q["Mx"]: float(Mx) * 1e6,
        q["My"]: float(My) * 1e6,
        q["Qx"]: float(Qx) * 1e3,
        q["Qy"]: float(Qy) * 1e3,
        q["T"]: float(T) * 1e6,
    }
    if not ambient and any(f.get("quantity_id") == "sp16_local_load_F" for f in card.get("fields", [])):
        oldF = old.get("sp16_local_load_F")
        f = st.number_input(
            "Местная сосредоточенная сила F, кН (необязательно)",
            value=(float(oldF) / 1e3) if isinstance(oldF, (int, float)) else None,
            key=_key(mode_key, card["node_id"], "localF"),
        )
        if f is not None:
            payload["sp16_local_load_F"] = float(f) * 1e3
    return payload, None, True


def _render_bimoment(card: Mapping[str, Any], old: Any, mode_key: str):
    current = float(old) / 1e9 if isinstance(old, (int, float)) else 0.0
    value = st.number_input(
        "B, кН·м²",
        value=current,
        key=_key(mode_key, card["node_id"], "B"),
    )
    st.caption("1 кН·м² = 10⁹ Н·мм². Знак B сохраняется end-to-end; B не вычисляется из T.")
    return float(value) * 1e9, None, True


def _render_summary(env: Mapping[str, Any], card: Mapping[str, Any], component: str):
    if component == "verification_plan_summary":
        plan = _ledger_value(env, "verification_plan", {}) or {}
        st.markdown("#### План нормативных проверок")
        st.write(f"Основная ветвь: **{plan.get('stress_state', '—')}**")
        for branch in plan.get("branches", []):
            status = branch.get("status", "")
            label = branch.get("label") or branch.get("id")
            st.markdown(f"- **{label}** — {status}" + (f": {branch.get('note')}" if branch.get("note") else ""))
        if plan.get("deferred_branch_ids"):
            st.warning("Fail-closed/отложенные ветви: " + ", ".join(plan["deferred_branch_ids"]))
    else:
        census = _ledger_value(env, "sp16_applicability_census", {}) or {}
        st.markdown("#### SP16 Applicability Census")
        for row in census.get("active_checks", []):
            st.markdown(f"- **{row.get('label') or row.get('id')}** — {row.get('runtime_status', 'APPLICABLE')}")
        if census.get("deferred_active_check_ids"):
            st.warning("Fail-closed: " + ", ".join(census["deferred_active_check_ids"]))
    return True, None, True


def _render_required_r(card: Mapping[str, Any], old: Any, mode_key: str):
    presets = [15, 30, 45, 60, 90, 120, 150, 180]
    use_custom = isinstance(old, (int, float)) and old not in presets
    mode = st.radio(
        "Требуемый предел",
        ["preset", "custom"],
        index=1 if use_custom else 0,
        format_func=lambda x: "Стандартное R" if x == "preset" else "Другое значение",
        horizontal=True,
        key=_key(mode_key, card["node_id"], "rmode"),
    )
    if mode == "preset":
        v = st.selectbox(
            "R, мин",
            presets,
            index=presets.index(int(old)) if isinstance(old, (int, float)) and int(old) in presets else None,
            placeholder="— выберите —",
            format_func=lambda x: f"R{x}",
            key=_key(mode_key, card["node_id"], "rpreset"),
        )
        return v, None, v is not None
    v = st.number_input(
        "R, мин",
        min_value=1.0,
        value=float(old) if use_custom else None,
        key=_key(mode_key, card["node_id"], "rcustom"),
    )
    return v, None, v is not None


def _parse_vector(text: str) -> list[float] | None:
    clean = text.replace(";", " ").replace(",", " ").split()
    if len(clean) < 2:
        return None
    try:
        vals = [float(x) for x in clean]
    except ValueError:
        return None
    return vals if all(math.isfinite(x) for x in vals) else None


def _parse_matrix(text: str) -> list[list[float]] | None:
    rows = [r.strip() for r in text.splitlines() if r.strip()]
    if len(rows) < 2:
        return None
    out: list[list[float]] = []
    for row in rows:
        vals = _parse_vector(row)
        if not vals:
            return None
        out.append(vals)
    return out


def _render_performance_matrix(env: Mapping[str, Any], card: Mapping[str, Any], old: Any, mode_key: str):
    old = old if isinstance(old, Mapping) else {}
    product_id = str(old.get("product_id") or _ledger_value(env, "protection_product_id", "") or "")
    steel_group = str(old.get("steel_group") or _ledger_value(env, "steel_strength_group", "ordinary"))
    fire_regime = str(old.get("fire_regime") or _ledger_value(env, "fire_temperature_regime", "standard"))
    tcr_current = _ledger_value(env, "critical_temperature_c")
    if tcr_current is not None:
        st.info(f"Текущая расчётная критическая температура: {_fmt(tcr_current)} °C")
    st.text_input("Марка продукта", value=product_id, disabled=True, key=_key(mode_key, card["node_id"], "product"))
    tcr = st.number_input(
        "Критическая температура матрицы, °C",
        value=float(old["critical_temperature_c"]) if isinstance(old.get("critical_temperature_c"), (int, float)) else None,
        key=_key(mode_key, card["node_id"], "tcr"),
    )
    da0 = ", ".join(str(x) for x in old.get("reduced_thickness_axis_mm", []))
    pa0 = ", ".join(str(x) for x in old.get("protection_thickness_axis_mm", []))
    mx0 = "\n".join(", ".join(str(x) for x in row) for row in old.get("time_matrix_min", []))
    da_text = st.text_input("Ось приведённой толщины δпр, мм", value=da0, key=_key(mode_key, card["node_id"], "da"))
    pa_text = st.text_input("Ось толщины огнезащиты δf, мм", value=pa0, key=_key(mode_key, card["node_id"], "pa"))
    mx_text = st.text_area("Матрица времени, мин — одна строка на каждое δпр", value=mx0, height=180, key=_key(mode_key, card["node_id"], "mx"))
    confirmed = st.checkbox(
        "Подтверждаю, что оси и матрица взяты из технической документации выбранного средства огнезащиты.",
        value=bool(old.get("technical_documentation_12_7_9_confirmed")),
        key=_key(mode_key, card["node_id"], "confirm"),
    )
    carry = st.checkbox(
        "Документация явно разрешает перенос результата на большую δпр за верхней границей таблицы.",
        value=bool(old.get("allow_greater_delta_carry_forward")),
        key=_key(mode_key, card["node_id"], "carry"),
    )
    da, pa, mx = _parse_vector(da_text), _parse_vector(pa_text), _parse_matrix(mx_text)
    dims_ok = bool(da and pa and mx and len(mx) == len(da) and all(len(r) == len(pa) for r in mx))
    ready = tcr is not None and bool(product_id) and dims_ok and confirmed
    if not dims_ok and (da_text or pa_text or mx_text):
        st.warning("Размер матрицы: число строк = числу δпр; число значений в каждой строке = числу толщин δf.")
    payload = None
    if ready:
        payload = {
            "product_id": product_id,
            "source_kind": "technical_documentation_12_7_9",
            "critical_temperature_c": float(tcr),
            "steel_group": steel_group,
            "fire_regime": fire_regime,
            "technical_documentation_12_7_9_confirmed": True,
            "reduced_thickness_axis_mm": da,
            "protection_thickness_axis_mm": pa,
            "time_matrix_min": mx,
            "allow_greater_delta_carry_forward": bool(carry),
        }
    return payload, None, ready


def _render_scalar_custom(card: Mapping[str, Any], old: Any, mode_key: str, component: str):
    if component == "section_editor_entry":
        return _render_section_entry(card, old, mode_key)
    if component == "required_r_selector":
        return _render_required_r(card, old, mode_key)
    if component == "bimoment_direct_input":
        return _render_bimoment(card, old, mode_key)
    return _render_generic(card, old, None, mode_key)


def _render_card_body(
    app: FireUI1Application,
    sid: str,
    env: Mapping[str, Any],
    card: Mapping[str, Any],
    old_payload: Any,
    old_provenance: Mapping[str, Any] | None,
    mode_key: str,
):
    component = str((card.get("presentation") or {}).get("component") or "generic")
    if component in SCALAR_COMPONENTS:
        return _render_scalar_custom(card, old_payload, mode_key, component)
    if component == "profile_catalog_selector":
        return _render_profile_catalog(app, card, old_payload, mode_key)
    if component == "parametric_section_editor":
        return _render_parametric(card, old_payload, mode_key)
    if component == "manual_section_properties_editor":
        return _render_manual_section(card, old_payload, mode_key)
    if component == "double_branch_section_editor":
        return _render_double_branch(app, card, old_payload, mode_key)
    if component == "material_strength_editor":
        return _render_material(app, sid, card, old_payload, mode_key)
    if component == "section_weakening_editor":
        return _render_weakening(card, old_payload, mode_key)
    if component == "ambient_signed_load_menu":
        return _render_load_menu(card, old_payload, mode_key, "ambient")
    if component == "fire_signed_load_menu":
        return _render_load_menu(card, old_payload, mode_key, "fire")
    if component in SUMMARY_COMPONENTS:
        return _render_summary(env, card, component)
    if component == "documented_performance_matrix_editor":
        return _render_performance_matrix(env, card, old_payload, mode_key)
    return _render_generic(card, old_payload, old_provenance, mode_key)


def _render_history(app: FireUI1Application, env: Mapping[str, Any]) -> None:
    history = list(env["state"].get("interaction_history") or [])
    cards = _card_map(app)
    with st.expander(f"История шагов ({len(history)})", expanded=False):
        if not history:
            st.caption("Расчёт ещё не содержит ответов.")
            return
        for i, row in enumerate(history):
            card = cards.get(row["node_id"], {})
            cols = st.columns([5, 1])
            cols[0].write(f"{i+1}. {card.get('title') or row['node_id']}")
            if cols[1].button("Изм.", key=_key("history", i, row["node_id"])):
                st.session_state["_fire_edit_node"] = row["node_id"]
                st.rerun()


def _render_ledger_trace(env: Mapping[str, Any]) -> None:
    tab_ledger, tab_trace = st.tabs(["Величины", "Trace"])
    with tab_ledger:
        rows = list(env["state"].get("ledger") or [])
        search = st.text_input("Поиск величины", key="fire:ledger:search", placeholder="Название, символ или ID")
        sources = ["Все"] + sorted({str(r.get("source_kind")) for r in rows})
        source = st.selectbox("Источник", sources, key="fire:ledger:source")
        visible = []
        query = search.strip().lower()
        for row in rows:
            if source != "Все" and row.get("source_kind") != source:
                continue
            hay = f"{row.get('name_ru','')} {row.get('symbol','')} {row.get('quantity_id','')}".lower()
            if query and query not in hay:
                continue
            visible.append(row)
        if not visible:
            st.caption("Расчётные величины появятся после ответов.")
        for row in visible:
            unit = f" {row['unit']}" if row.get("unit") else ""
            st.markdown(
                f'<div class="fire-ledger-row">'
                f'<div class="fire-ledger-name">{row.get("name_ru") or row["quantity_id"]}'
                f'{" · " + str(row.get("symbol")) if row.get("symbol") else ""}</div>'
                f'<div class="fire-ledger-value">{_fmt(row.get("value"))}{unit}</div>'
                f'<div class="fire-small">{row.get("source_kind")} · {row.get("producer_node_id")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with tab_trace:
        trace = list(env["state"].get("trace") or [])
        if not trace:
            st.caption("Execution trace пока пуст.")
        for row in trace:
            with st.expander(f"{row.get('sequence')}. {row.get('node_id')} · {row.get('event_kind')}"):
                st.write(f"Status: `{row.get('status')}`")
                if row.get("selected_edge_id"):
                    st.write(f"Edge: `{row['selected_edge_id']}`")
                if row.get("outputs"):
                    st.json(row["outputs"], expanded=False)
                if row.get("message"):
                    st.caption(row["message"])


def _render_noninteractive(env: Mapping[str, Any], card: Mapping[str, Any] | None) -> None:
    status = str(env["state"].get("status") or "")
    if status.startswith("BLOCKED"):
        st.error("Расчётная ветвь остановлена fail-closed.")
        st.code(status)
        st.write("Недостаточный production-путь не подменяется приближением или скрытой экстраполяцией.")
    else:
        st.markdown('<div class="fire-result">', unsafe_allow_html=True)
        st.subheader((card or {}).get("title") or "Маршрут завершён")
        st.write("Статус:", status or "COMPLETE")
        st.markdown("</div>", unsafe_allow_html=True)
    if env["state"].get("branch_failures"):
        with st.expander("Диагностика ветвей"):
            st.json(env["state"]["branch_failures"], expanded=False)
    _refs(card)


def _load_snapshot(app: FireUI1Application, uploaded) -> None:
    try:
        snapshot = json.loads(uploaded.getvalue().decode("utf-8"))
        restored = app.restore_session(snapshot)
        st.session_state["_fire_session_id"] = restored["session_id"]
        st.session_state["_fire_edit_node"] = None
        for k in list(st.session_state):
            if k.startswith("fire:") and not k.startswith("fire:upload"):
                del st.session_state[k]
        st.success("Расчёт восстановлен из JSON.")
        st.rerun()
    except (UnicodeDecodeError, json.JSONDecodeError, FireUIError) as exc:
        st.error(f"Не удалось загрузить расчёт: {exc}")


def main() -> None:
    st.set_page_config(
        page_title="FIRE Resistance Calculator — СП16 ↔ СП554",
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(STYLES, unsafe_allow_html=True)

    app = _ensure_app()
    sid = _ensure_session(app)
    env = app.session_payload(sid)
    contract = st.session_state.get("_fire_contract") or app.ui_contract()
    st.session_state["_fire_contract"] = contract

    st.markdown(
        '<div class="fire-hero"><div class="fire-title">FIRE Resistance Calculator</div>'
        '<div class="fire-subtitle">СП 16 ↔ СП 554 · Engineering guided calculation · Streamlit presentation over frozen runtime</div></div>',
        unsafe_allow_html=True,
    )
    top1, top2, top3, top4 = st.columns([1.1, 1, 1, 1.4])
    top1.markdown(f'<span class="fire-status">{env["state"].get("status","—")}</span>', unsafe_allow_html=True)
    top2.markdown(f'<span class="fire-status">Шаг {len(env["state"].get("interaction_history", [])) + 1}</span>', unsafe_allow_html=True)
    top3.markdown(f'<span class="fire-status">DAG locked</span>', unsafe_allow_html=True)
    top4.caption(str(contract.get("graph_id") or ""))

    action1, action2, action3 = st.columns([1, 1, 3])
    if action1.button("Новый расчёт", width="stretch"):
        _reset_calculation()
        st.rerun()
    snapshot_json = json.dumps(env["state"], ensure_ascii=False, indent=2)
    action2.download_button(
        "Сохранить JSON",
        data=snapshot_json,
        file_name="fire_calculation.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
    )
    uploaded = action3.file_uploader("Загрузить сохранённый расчёт", type=["json"], key="fire:upload")
    if uploaded is not None and action3.button("Восстановить JSON", key="fire:restore"):
        _load_snapshot(app, uploaded)

    _render_history(app, env)

    left, right = st.columns([1.65, 1], gap="large")
    with left:
        edit_card, old_payload, old_provenance = _edit_context(app, env)
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
            if presentation.get("subtitle"):
                st.caption(str(presentation["subtitle"]))
            notes = card.get("notes") or {}
            if notes.get("normative_warning"):
                st.warning(str(notes["normative_warning"]))
            mode_key = "edit" if editing else "current"
            payload, provenance, ready = _render_card_body(
                app, sid, env, card, old_payload, old_provenance, mode_key
            )
            _refs(card)
            st.markdown("</div>", unsafe_allow_html=True)
            label = "Применить изменение" if editing else "Далее"
            if st.button(label, type="primary", disabled=not ready, width="stretch", key=_key(mode_key, card["node_id"], "submit")):
                _submit(app, sid, card, payload, provenance, editing)
        else:
            _render_noninteractive(env, card)

    with right:
        _render_ledger_trace(env)

    st.divider()
    st.caption(
        "Streamlit UI — presentation layer only. Нормативная логика, DAG routing, "
        "producer execution и fail-closed gates остаются в standard_core."
    )


if __name__ == "__main__":
    main()
