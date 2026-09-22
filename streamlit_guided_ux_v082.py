"""v0.82 installer for full guided-route closure."""
from __future__ import annotations

import copy
from typing import Any, Mapping

import streamlit_guided_ux_v081 as _v081

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v078_gamma_c import INPUT_QID as GAMMA_C_CASE_QID, resolve_gamma_c_compression
from standard_core.sp16_mech7_v078_graph_overlay import INPUT_NODE_ID as GAMMA_C_INPUT_NODE_ID
from standard_core.sp16_mech7_v082_guided_route_overlay import GRAPH_SUFFIX, build_model
from standard_core.sp16_mech7_v082_runtime import install_registry_remediation

_INSTALLED = "_fire_v082_full_guided_route_closure_installed"
_TABLE1_EVIDENCE_QID = "sp16_table1_compression_evidence"
_TABLE1_EXACT_CANDIDATES = (
    GAMMA_C_CASE_QID,
    "sp16_table1_case_id",
    "sp16_table1_working_condition_case_id",
)


def _valid_gamma_case(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        resolve_gamma_c_compression(value)
    except Exception:
        return None
    return value


def _exact_gamma_case(values: Mapping[str, Any]) -> str | None:
    for key in _TABLE1_EXACT_CANDIDATES:
        case_id = _valid_gamma_case(values.get(key))
        if case_id is not None:
            return case_id
    evidence = values.get(_TABLE1_EVIDENCE_QID)
    if isinstance(evidence, Mapping):
        case_id = _valid_gamma_case(evidence.get("case_id"))
        if case_id is not None:
            return case_id
    return None


def _reuse_exact_table1(session: Any) -> bool:
    if session.current_node_id != GAMMA_C_INPUT_NODE_ID:
        return False
    case_id = _exact_gamma_case(session.plain_values())
    if case_id is None:
        case_id = _valid_gamma_case(getattr(session, "_v080_retained_gamma_c_case_id", None))
    if case_id is None:
        return False
    session.submit(case_id, provenance={
        "ui_surface": "v0.82_exact_table1_reuse",
        "source_node_id": GAMMA_C_INPUT_NODE_ID,
        "quantity": GAMMA_C_CASE_QID,
        "rule": "reuse exact previously classified Table-1 case only; numeric gamma_c reverse inference forbidden",
    })
    return True


def _consume_exact_reuse(session: Any) -> None:
    for _ in range(24):
        before = (session.current_node_id, len(session.interaction_history))
        _v081._consume_exact_reuse(session)
        _reuse_exact_table1(session)
        after = (session.current_node_id, len(session.interaction_history))
        if after == before:
            break


def _semantic_replay(source: Any, model: Any, registry: Any):
    migrated = _v081._semantic_replay(source, model, registry)
    _consume_exact_reuse(migrated)
    return migrated


def _install_renderers(core: Any) -> None:
    previous_load = core._render_load_menu
    previous_generic = core._render_generic

    def _render_load_menu(card, old, mode_key, kind):
        payload, provenance, ready = previous_load(card, old, mode_key, kind)
        if kind != "ambient" or not isinstance(payload, dict):
            return payload, provenance, ready
        old_map = old if isinstance(old, Mapping) else {}
        current = old_map.get("ambient_B_bimoment", 0.0)
        b0 = float(current) / 1e9 if isinstance(current, (int, float)) and not isinstance(current, bool) else 0.0
        st = core._st()
        b = st.number_input(
            "B, кН·м²",
            value=b0,
            key=core._key(mode_key, card["node_id"], "B_inline_v082"),
        )
        st.caption("Бимомент B входит в тот же обычный расчётный случай. Знак сохраняется end-to-end; B не вычисляется из крутящего момента T.")
        payload["ambient_B_bimoment"] = float(b) * 1e9
        combo = payload.get("ambient_load_combination")
        if isinstance(combo, dict):
            combo["B_kNm2"] = float(b)
            display = dict(combo.get("display_units") or {})
            display["bimoment"] = "kN*m^2"
            combo["display_units"] = display
        return payload, provenance, ready

    def _render_generic(card, old_payload, old_provenance, mode_key):
        # Explicit UI default only.  The submitted value remains the normal
        # decision value and the user can still select a separate fire case.
        if card.get("node_id") == "SP16_D_FIRE_LOAD_CASE_MODE" and old_payload is None:
            old_payload = "same_as_ambient"
        return previous_generic(card, old_payload, old_provenance, mode_key)

    core._render_load_menu = _render_load_menu
    core._render_generic = _render_generic


def install(core: Any) -> None:
    _v081.install(core)
    if getattr(core, _INSTALLED, False):
        return

    _install_renderers(core)
    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _invalidate_contract_cache() -> None:
        try:
            core._st().session_state.pop("_fire_contract", None)
            core._st().session_state.pop("_fire_contract_map", None)
        except Exception:
            pass

    def _upgrade(app):
        registry = app.service.registry
        install_registry_remediation(registry)
        if GRAPH_SUFFIX not in str(app.model.graph.get("graph_id") or ""):
            old_sessions = dict(app.service.sessions)
            new_model = build_model(app.model)
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = _semantic_replay(old_session, new_model, registry)
            app.model = new_model
            app.service = new_service
            _invalidate_contract_cache()
        for session in app.service.sessions.values():
            _consume_exact_reuse(session)
        return app

    def _new_application():
        return _upgrade(previous_new_application())

    def _ensure_app():
        return _upgrade(previous_ensure_app())

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    setattr(core, _INSTALLED, True)


__all__ = ["_consume_exact_reuse", "_exact_gamma_case", "_reuse_exact_table1", "install"]
