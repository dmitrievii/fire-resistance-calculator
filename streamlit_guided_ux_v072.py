from __future__ import annotations

"""v0.72 guided UX/runtime integration hotfix.

The UI keeps the v0.71 presentation refinements, restores the explicit SP16
Table-3 material-safety choice omitted by the compact material editor, installs
the v0.72 MECH7 compatibility adapter on every Streamlit application, and makes
the completion-diagnostic renderer structurally idempotent.
"""

from typing import Any, Mapping

import streamlit_guided_ux as _base
import streamlit_guided_ux_v071 as _v071
from standard_core.sp16_mech7_v072_remediation import install_registry_remediation

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
    current = existing if existing in values else st.session_state.get(key)
    category = st.selectbox(
        "Условия контроля свойств проката для выбора γm · СП16, таблица 3",
        values,
        index=values.index(current) if current in values else None,
        placeholder="— выберите категорию таблицы 3 —",
        format_func=lambda value: _MATERIAL_SAFETY_LABELS[value],
        key=key,
    )
    st.caption("γm не принимается по умолчанию: выбор сохраняется как явный исходный параметр СП16 таблицы 3.")
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
            category = st.session_state.get(_category_state_key(str(card.get("node_id") or "material")))
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
                    provenance={"ui_surface": "material_strength_editor", "standard": "SP16 Table 3"},
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

    # Keep v0.71 human-readable indexed property labels and gamma_ct preflight.
    _base._profile_line = _v071._profile_line
    _base._humanize_mech7_card = _v071._humanize_card
    _base._render_material = _render_material

    # Capture canonical callables before the base installer wraps them.  On a
    # module reload these attributes survive on streamlit_app_core, so wrapper
    # chains cannot grow with Streamlit reruns.
    if not hasattr(core, _CANONICAL_NONINTERACTIVE):
        setattr(core, _CANONICAL_NONINTERACTIVE, core._render_noninteractive)

    _base.install(core)
    _install_single_diagnostic_renderer(core)
    _install_runtime_application_patch(core)
    _install_material_category_submit_patch(core)
    setattr(core, _INSTALL_SENTINEL, True)
