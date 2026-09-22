"""v0.90 Streamlit installer for MECH9 conditional authoring UX."""
from __future__ import annotations

import copy
import json
from typing import Any, Mapping

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech9_v090_ux_overlay import (
    GRAPH_SUFFIX,
    build_model,
    install_registry_remediation,
)
from streamlit_guided_ux_v086 import _semantic_replay

_INSTALLED = "_fire_v090_mech9_ux_installed"
_FATIGUE_NODE = "SP16_I_MECH9_FATIGUE_ORDINARY"
_CONDITIONAL_NODE = "SP16_I_MECH9_BRITTLE_CONDITIONAL"
_ANNEX_CONFIRM = "sp16_mech9_fatigue_annex_k_case_confirmed"


def _old_value(old: Any, qid: str) -> Any:
    return old.get(qid) if isinstance(old, Mapping) else None


def _bool_input(core: Any, label: str, current: Any, key: str) -> bool | None:
    st = core.st
    options = [True, False]
    idx = options.index(current) if isinstance(current, bool) else None
    return st.selectbox(
        label,
        options,
        index=idx,
        placeholder="— выберите —",
        format_func=lambda v: "Да" if v else "Нет",
        key=key,
    )


def _render_section13_conditional(core: Any, env: Mapping[str, Any], card: Mapping[str, Any], old: Any, mode_key: str):
    """Render only the §13.2 questions made applicable by the already answered context."""
    st = core.st
    values = {
        qid: core._ledger_value(env, qid)
        for qid in (
            "sp16_mech9_brittle_welded_structure",
            "sp16_mech9_brittle_cover_plate_flank_welds",
            "sp16_mech9_brittle_guillotine_or_punched",
            "sp16_mech9_brittle_secondary_gusset",
            "Ry_formula",
        )
    }
    payload: dict[str, Any] = {}
    ready = True
    asked = 0

    welded = values["sp16_mech9_brittle_welded_structure"] is True
    if welded:
        asked += 1
        sigma_qid = "sp16_mech9_brittle_weld_sigma_t"
        sigma_old = _old_value(old, sigma_qid)
        sigma = st.number_input(
            "Растягивающее напряжение в зоне сварного соединения σt, МПа",
            min_value=0.0,
            value=float(sigma_old) if isinstance(sigma_old, (int, float)) and not isinstance(sigma_old, bool) else None,
            format="%g",
            key=core._key(mode_key, card["node_id"], sigma_qid),
        )
        if sigma is None:
            ready = False
        else:
            payload[sigma_qid] = float(sigma)

        ry = values["Ry_formula"]
        if not isinstance(ry, (int, float)) or isinstance(ry, bool):
            st.error("Для определения применимости усиленного НК отсутствует квалифицированное Ry.")
            ready = False
        elif sigma is not None:
            threshold = 0.4 * float(ry)
            st.caption(f"Усиленный контроль сварного соединения требуется только при σt > 0,4·Ry = {threshold:.3g} МПа.")
            if float(sigma) > threshold:
                qid = "sp16_mech9_brittle_enhanced_ndt_confirmed"
                value = _bool_input(
                    core,
                    "Усиленный неразрушающий контроль сварного соединения выполнен?",
                    _old_value(old, qid),
                    core._key(mode_key, card["node_id"], qid),
                )
                asked += 1
                if value is None:
                    ready = False
                else:
                    payload[qid] = value

        for qid, label in (
            ("sp16_mech9_brittle_weld_intersections_avoided", "Пересечение сварных швов исключено?"),
            ("sp16_mech9_brittle_runoff_tabs_ndt_confirmed", "Технологические выводные планки и контроль сварных швов выполнены по требованиям раздела 13?"),
        ):
            value = _bool_input(core, label, _old_value(old, qid), core._key(mode_key, card["node_id"], qid))
            asked += 1
            if value is None:
                ready = False
            else:
                payload[qid] = value
    else:
        st.caption("Сварные соединения для этой проверки не заявлены — сварочные подпункты §13.2 не запрашиваются.")

    if values["sp16_mech9_brittle_cover_plate_flank_welds"] is True:
        qid = "sp16_mech9_brittle_flank_termination"
        current = _old_value(old, qid)
        value = st.number_input(
            "Расстояние от окончания флангового шва до края накладки с каждой стороны, мм",
            min_value=0.0,
            value=float(current) if isinstance(current, (int, float)) and not isinstance(current, bool) else None,
            format="%g",
            key=core._key(mode_key, card["node_id"], qid),
        )
        asked += 1
        if value is None:
            ready = False
        else:
            payload[qid] = float(value)

    if values["sp16_mech9_brittle_guillotine_or_punched"] is True:
        qid = "sp16_mech9_brittle_min_thickness_confirmed"
        value = _bool_input(
            core,
            "При гильотинной резке/пробивке соблюдено требование по минимальной толщине?",
            _old_value(old, qid),
            core._key(mode_key, card["node_id"], qid),
        )
        asked += 1
        if value is None:
            ready = False
        else:
            payload[qid] = value

    if values["sp16_mech9_brittle_secondary_gusset"] is True:
        qid = "sp16_mech9_brittle_gusset_bolted_confirmed"
        value = _bool_input(
            core,
            "Вторичная фасонка к растянутому элементу закреплена болтами?",
            _old_value(old, qid),
            core._key(mode_key, card["node_id"], qid),
        )
        asked += 1
        if value is None:
            ready = False
        else:
            payload[qid] = value

    if asked == 0:
        st.info("Для выбранного конструктивного контекста дополнительные условные требования этой карточки отсутствуют.")
    return payload, None, ready


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app
    previous_render_card_body = core._render_card_body

    def _invalidate_contract() -> None:
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
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
            _invalidate_contract()
        return app

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        node_id = str(card.get("node_id") or "")
        if node_id == _FATIGUE_NODE:
            # A typed Annex-K enum selection is the explicit classification.
            # Keep the quantity in the graph for backward-compatible session replay,
            # but do not ask the user to confirm the same selection twice.
            compact = copy.deepcopy(dict(card))
            compact["fields"] = [
                f for f in compact.get("fields", [])
                if f.get("quantity_id") != _ANNEX_CONFIRM
            ]
            return previous_render_card_body(app, sid, env, compact, old_payload, old_provenance, mode_key)
        if node_id == _CONDITIONAL_NODE:
            return _render_section13_conditional(core, env, card, old_payload, mode_key)
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_render_section13_conditional"]
