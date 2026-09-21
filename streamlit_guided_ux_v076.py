"""Streamlit installer for v0.76 consolidated Stage-N7 effective-length authoring."""
from __future__ import annotations

import json
from typing import Any, Mapping

import streamlit_guided_ux_v075 as _v075

_INSTALLED = "_fire_v076_effective_length_card_installed"
_COMPONENT = "effective_length_zy_editor"


def _old_axis(old: Mapping[str, Any], axis: str) -> Mapping[str, Any]:
    value = old.get(axis)
    return value if isinstance(value, Mapping) else {}


def _render_effective_length_editor(core: Any, card: Mapping[str, Any], old_payload: Any, mode_key: str):
    st = core.st
    old = old_payload if isinstance(old_payload, Mapping) else {}
    presentation = card.get("presentation") or {}
    table_options = list(presentation.get("table30_options") or [])
    option_values = [row.get("value") for row in table_options]
    option_labels = {row.get("value"): str(row.get("label") or row.get("value")) for row in table_options}
    option_desc = {row.get("value"): str(row.get("description") or "") for row in table_options}

    methods = ["table30", "verified_analysis"]
    method_labels = {
        "table30": "Выбрать схему закрепления по СП16, таблица 30",
        "verified_analysis": "Задать расчётную длину l_eff напрямую",
    }

    axes: dict[str, dict[str, Any]] = {}
    ready = True
    cols = st.columns(2, gap="large")
    for col, axis, title in zip(cols, ("z", "y"), ("Сильная ось z", "Слабая ось y")):
        prior = _old_axis(old, axis)
        with col:
            st.markdown(f"**{title}**")
            current_method = prior.get("method") if prior.get("method") in methods else None
            method = st.radio(
                "Как определяется расчётная длина?",
                methods,
                index=methods.index(current_method) if current_method in methods else None,
                format_func=lambda value: method_labels[value],
                key=core._key(mode_key, card["node_id"], axis, "method"),
            )
            axis_payload: dict[str, Any] = {}
            if method == "table30":
                current_scheme = prior.get("scheme_id") if prior.get("scheme_id") in option_values else None
                scheme = st.selectbox(
                    "Схема закрепления и вид нагрузки",
                    option_values,
                    index=option_values.index(current_scheme) if current_scheme in option_values else None,
                    placeholder="— выберите фактическую схему —",
                    format_func=lambda value: option_labels.get(value, str(value)),
                    key=core._key(mode_key, card["node_id"], axis, "scheme"),
                )
                if scheme is not None:
                    st.caption(option_desc.get(scheme, ""))
                    axis_payload = {"method": "table30", "scheme_id": scheme}
                else:
                    ready = False
            elif method == "verified_analysis":
                current_length = prior.get("effective_length_mm")
                base = float(current_length) if isinstance(current_length, (int, float)) and not isinstance(current_length, bool) else None
                leff = st.number_input(
                    f"Расчётная длина l_eff,{axis}, мм",
                    value=base,
                    format="%g",
                    key=core._key(mode_key, card["node_id"], axis, "leff"),
                )
                basis = st.text_input(
                    "Основание / расчётная модель",
                    value=str(prior.get("basis") or ""),
                    placeholder="Например: расчётная схема КЭ, СП16 п. 10.3.11 …",
                    key=core._key(mode_key, card["node_id"], axis, "basis"),
                ).strip()
                if leff is None or float(leff) <= 0.0 or not basis:
                    ready = False
                else:
                    axis_payload = {
                        "method": "verified_analysis",
                        "effective_length_mm": float(leff),
                        "basis": basis,
                    }
            else:
                ready = False
            axes[axis] = axis_payload

    any_table30 = any(axis_payload.get("method") == "table30" for axis_payload in axes.values())
    member_length = None
    if any_table30:
        st.divider()
        st.caption("Для схем таблицы 30 коэффициент μ применяется к геометрической длине того же элемента по формуле (140): l_eff = μL.")
        current = old.get("member_length_mm")
        base = float(current) if isinstance(current, (int, float)) and not isinstance(current, bool) else None
        member_length = st.number_input(
            "Геометрическая длина элемента L, мм",
            value=base,
            format="%g",
            key=core._key(mode_key, card["node_id"], "member_length"),
        )
        if member_length is None or float(member_length) <= 0.0:
            ready = False

    payload: dict[str, Any] = {"z": axes["z"], "y": axes["y"]}
    if any_table30 and member_length is not None:
        payload["member_length_mm"] = float(member_length)

    st.caption(
        "В активном контракте используются только главные оси z/y. "
        "Внутренние исторические идентификаторы схем в эту карточку не передаются."
    )
    return payload, None, bool(ready and axes["z"] and axes["y"])


def install(core: Any) -> None:
    """Install v0.75 first, then replace its Stage-N7 authoring surface by v0.76."""
    _v075.install(core)
    if getattr(core, _INSTALLED, False):
        return

    from standard_core.fire_ui0 import GuidedCalculationService
    from standard_core.sp16_mech7_v076_graph_overlay import GRAPH_SUFFIX, build_model, replay_prefix_on_model
    from standard_core.sp16_mech7_v076_runtime import install_registry_remediation

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app
    previous_render_card_body = core._render_card_body

    def _invalidate_contract_cache() -> None:
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except Exception:
            pass

    def _upgrade(app):
        registry = app.service.registry
        install_registry_remediation(registry, app.profile_catalog)
        graph_id = str(app.model.graph.get("graph_id", ""))
        if graph_id.endswith(GRAPH_SUFFIX):
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
            return _render_effective_length_editor(core, card, old_payload, mode_key)
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
