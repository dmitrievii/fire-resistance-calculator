"""Streamlit installer for v0.78 explicit SP16 Table-1 compression gamma_c."""
from __future__ import annotations

from typing import Any, Mapping

import streamlit_guided_ux_v077 as _v077

_INSTALLED = "_fire_v078_gamma_c_compression_installed"
_COMPONENT = "sp16_table1_gamma_c_compression"


def _render_gamma_c_editor(core: Any, card: Mapping[str, Any], old_payload: Any, mode_key: str):
    st = core._st()
    presentation = card.get("presentation") or {}
    options = list(presentation.get("options") or [])
    values = [str(row.get("value")) for row in options]
    by_value = {str(row.get("value")): row for row in options}
    current = old_payload if isinstance(old_payload, str) and old_payload in values else None

    selected = st.selectbox(
        "Условия работы элемента по СП16, таблица 1",
        values,
        index=values.index(current) if current in values else None,
        placeholder="— выберите применимый случай таблицы 1 —",
        format_func=lambda value: (
            f"{by_value[value].get('description_ru', value)} — "
            f"γc = {float(by_value[value].get('gamma_c')):.3g}".replace(".", ",")
        ),
        key=core._key(mode_key, card["node_id"], "case"),
    )
    if selected is not None:
        row = by_value[selected]
        st.caption(
            f"Будет использовано γc = {float(row['gamma_c']):.3g}. ".replace(".", ",")
            + "Выбор сохраняется как явная нормативная классификация, а не как значение по умолчанию."
        )
    st.caption(
        "Если текущий случай действительно не оговорен таблицей 1, выберите отдельный пункт "
        "«Примечание 5» (γc = 1,00). Приложение не выбирает его автоматически."
    )
    return selected, None, selected is not None


def install(core: Any) -> None:
    """Install v0.77 first, then insert the v0.78 Table-1 classification step."""
    _v077.install(core)
    if getattr(core, _INSTALLED, False):
        return

    from standard_core.fire_ui0 import GuidedCalculationService
    from standard_core.sp16_mech7_v078_gamma_c import install_registry_remediation
    from standard_core.sp16_mech7_v078_graph_overlay import GRAPH_SUFFIX, build_model, replay_prefix_on_model

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app
    previous_render_card_body = core._render_card_body

    def _invalidate_contract_cache() -> None:
        try:
            core._st().session_state.pop("_fire_contract", None)
            core._st().session_state.pop("_fire_contract_map", None)
        except Exception:
            pass

    def _upgrade(app):
        registry = app.service.registry
        install_registry_remediation(registry)
        graph_id = str(app.model.graph.get("graph_id") or "")
        if GRAPH_SUFFIX in graph_id:
            return app

        old_sessions = dict(app.service.sessions)
        new_model = build_model(app.model)
        new_service = GuidedCalculationService(new_model, registry=registry)
        for sid, old_session in old_sessions.items():
            new_service.sessions[sid] = replay_prefix_on_model(old_session, new_model, registry)
        app.model = new_model
        app.service = new_service
        _invalidate_contract_cache()
        return app

    def _new_application():
        return _upgrade(previous_new_application())

    def _ensure_app():
        return _upgrade(previous_ensure_app())

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        component = str((card.get("presentation") or {}).get("component") or "generic")
        if component == _COMPONENT:
            return _render_gamma_c_editor(core, card, old_payload, mode_key)
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
