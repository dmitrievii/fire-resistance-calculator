from __future__ import annotations

"""v0.72 guided UX/runtime integration, amended by v0.96 material contract."""

from typing import Any, Mapping

import streamlit_guided_ux as _base
import streamlit_guided_ux_v071 as _v071
from standard_core.sp16_mech7_v072_remediation import install_registry_remediation
from standard_core.material_gamma_default_v096 import resolve_annex_v_design_strengths

_INSTALL_SENTINEL = "_guided_ux_v072_installed"
_CANONICAL_NONINTERACTIVE = "_guided_ux_v072_canonical_noninteractive"
_CANONICAL_NEW_APP = "_guided_ux_v072_canonical_new_application"
_CANONICAL_SUBMIT = "_guided_ux_v072_canonical_submit"
_BASE_RENDER_MATERIAL = _base._render_material

_MATERIAL_SAFETY_OPTIONS = [
    ("statistical_control", "Статистический контроль свойств проката — γm = 1,025"),
    ("nonstatistical_high_yield_or_hot_finished_or_foreign", "Нестатистический контроль для высокопрочной / термообработанной / зарубежной стали — γm = 1,10"),
    ("other_conforming", "Другие соответствующие требованиям стали — γm = 1,05"),
    ("ks1_limited_service", "Ограниченный случай КС-1 по таблице 3 — γm = 1,00"),
]
_MATERIAL_SAFETY_LABELS = dict(_MATERIAL_SAFETY_OPTIONS)
_DEFAULT_MATERIAL_SAFETY_CATEGORY = "statistical_control"


def _category_state_key(node_id: str) -> str:
    return f"fire:v072:material-safety:{node_id}"


def _render_material(core: Any, app: Any, sid: str, card: Mapping[str, Any], old: Any, mode_key: str):
    payload, provenance, ready = _BASE_RENDER_MATERIAL(core, app, sid, card, old, mode_key)
    if not ready or payload is None:
        return payload, provenance, ready

    st = core._st()
    key = _category_state_key(str(card.get("node_id") or "material"))
    existing = core._ledger_value(app.session_payload(sid), "material_safety_category")
    values = [value for value, _ in _MATERIAL_SAFETY_OPTIONS]
    # Annex V.3/V.4/V.5 printed Ry/Ru are based on Table-3 gamma_m and rounded
    # to 5 N/mm2.  Their selector default is therefore the statistical-control
    # category (1.025), while an explicit user change remains authoritative.
    current = existing if existing in values else st.session_state.get(key, _DEFAULT_MATERIAL_SAFETY_CATEGORY)
    category = st.selectbox(
        "Коэффициент надёжности по материалу γm · СП16, таблица 3",
        values,
        index=values.index(current),
        format_func=lambda value: _MATERIAL_SAFETY_LABELS[value],
        key=key,
    )

    # Show the exact normative derivation in the same material card.  Preview
    # data are resolved from the selected Annex-V row; the production value is
    # still materialized into the ledger on submit below.
    try:
        preview = app.material_strength_preview(
            str(payload["steel_product_form"]),
            str(payload["steel_grade"]),
            str(payload["steel_strength_interval_key"]),
        )
        calc = resolve_annex_v_design_strengths(
            Ryn_MPa=float(preview["Ryn_MPa"]),
            Run_MPa=float(preview["Run_MPa"]),
            Ry_tabulated_MPa=preview.get("Ry_MPa"),
            Ru_tabulated_MPa=preview.get("Ru_MPa"),
            gamma_m_category=None if category == _DEFAULT_MATERIAL_SAFETY_CATEGORY else category,
        )
        st.caption(calc["gamma_m_basis"] + ". Расчётные сопротивления округляются до 5 Н/мм² согласно примечанию к таблицам приложения В.")
        st.latex(rf"R_y=\frac{{R_{{yn}}}}{{\gamma_m}}=\frac{{{preview['Ryn_MPa']}}}{{{calc['gamma_m']}}}={calc['Ry_formula_MPa']}\;\mathrm{{MPa}}")
        st.latex(rf"R_u=\frac{{R_{{un}}}}{{\gamma_m}}=\frac{{{preview['Run_MPa']}}}{{{calc['gamma_m']}}}={calc['Ru_formula_MPa']}\;\mathrm{{MPa}}")
    except Exception as exc:
        st.warning(f"Не удалось сформировать preview γm → Ry/Ru: {exc}")
    return payload, provenance, category is not None


def _install_runtime_application_patch(core: Any) -> None:
    if not hasattr(core, _CANONICAL_NEW_APP):
        setattr(core, _CANONICAL_NEW_APP, core._new_application)
    canonical = getattr(core, _CANONICAL_NEW_APP)

    def remediated_new_application():
        app = canonical()
        install_registry_remediation(app.service.registry)
        return app

    core._new_application = remediated_new_application


def _install_material_category_submit_patch(core: Any) -> None:
    if not hasattr(core, _CANONICAL_SUBMIT):
        setattr(core, _CANONICAL_SUBMIT, core._submit)
    canonical = getattr(core, _CANONICAL_SUBMIT)

    def remediated_submit(app, sid, card, payload, provenance, editing):
        if str((card.get("presentation") or {}).get("component") or "") == "material_strength_editor" or str(card.get("node_id") or "") == "SP554_I_STEEL_STRENGTH_EDITOR":
            st = core._st()
            category = st.session_state.get(_category_state_key(str(card.get("node_id") or "material")), _DEFAULT_MATERIAL_SAFETY_CATEGORY)
            if category not in _MATERIAL_SAFETY_LABELS:
                st.error("Выберите условия контроля свойств проката по таблице 3 СП16.")
                return
            session = app.service.get_session(sid)
            current = session.plain_values().get("material_safety_category")
            if current != category:
                session._set_quantity(
                    "material_safety_category",
                    category,
                    node_id="SP16_I_MATERIAL_SAFETY_CATEGORY",
                    source_kind="USER_INPUT",
                    provenance={
                        "ui_surface": "material_strength_editor",
                        "standard": "SP16 Table 3",
                        "default_from_annex_v": category == _DEFAULT_MATERIAL_SAFETY_CATEGORY,
                    },
                )
        return canonical(app, sid, card, payload, provenance, editing)

    core._submit = remediated_submit


def _install_single_diagnostic_renderer(core: Any) -> None:
    if not hasattr(core, _CANONICAL_NONINTERACTIVE):
        setattr(core, _CANONICAL_NONINTERACTIVE, core._render_noninteractive)
    canonical = getattr(core, _CANONICAL_NONINTERACTIVE)

    def render_once(env: Mapping[str, Any], card: Mapping[str, Any] | None):
        canonical(env, card)
        _base._render_sp16_completion_diagnostics(core, env)

    setattr(render_once, "_guided_ux_v072_single_diagnostic", True)
    core._render_noninteractive = render_once


def install(core: Any) -> None:
    if getattr(core, _INSTALL_SENTINEL, False):
        return
    _base._profile_line = _v071._profile_line
    _base._humanize_mech7_card = _v071._humanize_card
    _base._render_material = _render_material
    if not hasattr(core, _CANONICAL_NONINTERACTIVE):
        setattr(core, _CANONICAL_NONINTERACTIVE, core._render_noninteractive)
    _base.install(core)
    _install_single_diagnostic_renderer(core)
    _install_runtime_application_patch(core)
    _install_material_category_submit_patch(core)
    setattr(core, _INSTALL_SENTINEL, True)
