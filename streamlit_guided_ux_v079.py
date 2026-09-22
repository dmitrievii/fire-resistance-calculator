"""v0.79 retained-session and duplicate effective-length route remediation."""
from __future__ import annotations

import copy
from typing import Any, Mapping

import streamlit_guided_ux_v077 as _v077
import streamlit_guided_ux_v078 as _v078_ui

from standard_core.fire_ui0 import FireUIError, GuidedCalculationSession, GuidedCalculationService
from standard_core.sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    MATERIAL_SAFETY_INPUT_NODE_ID,
    MATERIAL_SAFETY_QUANTITY_ID,
)
from standard_core.sp16_mech7_v076_graph_overlay import DEFINITION_QID
from standard_core.sp16_mech7_v078_gamma_c import install_registry_remediation as install_gamma_c_registry
from standard_core.sp16_mech7_v079_guided_route_overlay import (
    GRAPH_SUFFIX,
    RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES,
    build_model,
)

_INSTALLED = "_fire_v079_retained_guided_route_installed"
_GAMMA_COMPONENT = "sp16_table1_gamma_c_compression"
_COMPRESSION_CONTEXT_NODE = "SP554_I_COMPRESSION_CONTEXT"
_RETAINED_ATTR = "_v079_retained_interaction_history"


def _explicit_material_category(session: GuidedCalculationSession) -> str | None:
    value = session.plain_values().get(MATERIAL_SAFETY_QUANTITY_ID)
    return value if isinstance(value, str) and value else None


def _inject_material_category_if_needed(
    migrated: GuidedCalculationSession,
    category: str | None,
    *,
    injected: bool,
) -> bool:
    if injected or category is None or migrated.current_node_id != MATERIAL_EDITOR_NODE_ID:
        return injected
    migrated._set_quantity(
        MATERIAL_SAFETY_QUANTITY_ID,
        category,
        node_id=MATERIAL_SAFETY_INPUT_NODE_ID,
        source_kind="USER_INPUT",
        provenance={
            "ui_surface": "v0.79_semantic_session_migration",
            "standard": "SP16 Table 3",
            "migration": "preserve_existing_explicit_material_safety_category",
        },
    )
    return True


def _known_member_length_mm(session: GuidedCalculationSession) -> float | None:
    """Return only an already explicit geometric L from the canonical v0.76 card."""
    definition = session.plain_values().get(DEFINITION_QID)
    if not isinstance(definition, Mapping):
        return None
    value = definition.get("member_length_mm")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0.0:
        return None
    return float(value)


def _reuse_member_length_context(session: GuidedCalculationSession) -> bool:
    """Auto-submit SP554's duplicate L prompt only when exactly the same L is known.

    No length is inferred from l_eff or mu.  If the canonical card did not contain
    geometric L (e.g. both axes used directly supplied l_eff), this function does
    nothing and the downstream route remains fail-closed/user-authored.
    """
    if session.current_node_id != _COMPRESSION_CONTEXT_NODE:
        return False
    length = _known_member_length_mm(session)
    if length is None:
        return False

    node = session.model.nodes[_COMPRESSION_CONTEXT_NODE]
    produced = [row.get("quantity_id") for row in node.get("produces", [])]
    if produced != ["member_length"]:
        return False
    session.submit(
        length,
        provenance={
            "ui_surface": "v0.79_exact_input_reuse",
            "source_node_id": "SP16_I_V076_EFFECTIVE_LENGTH_ZY",
            "quantity": "geometric member length L",
            "rule": "exact reuse only; no inference",
        },
    )
    return True


def _semantic_replay(
    source: GuidedCalculationSession,
    model: Any,
    registry: Any,
) -> GuidedCalculationSession:
    """Replay compatible answers while skipping superseded authoring nodes.

    Unlike the old prefix replay, insertion of a new node does not discard the
    untouched tail.  The tail is retained on the migrated session and is applied
    automatically after the user answers the new node, as long as node identities
    remain exact.  No answer is moved to a different normative node.
    """
    migrated = GuidedCalculationSession(model, entry_node_id=source.entry_node_id, registry=registry)
    category = _explicit_material_category(source)
    injected = False
    rows = copy.deepcopy(source.interaction_history)
    index = 0

    while index < len(rows):
        row = rows[index]
        expected = str(row.get("node_id") or "")
        if expected in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES:
            index += 1
            continue

        injected = _inject_material_category_if_needed(migrated, category, injected=injected)
        if migrated.current_node_id == expected:
            try:
                migrated.submit(row.get("payload"), provenance=row.get("provenance"))
            except FireUIError:
                break
            index += 1
            continue

        # SP554's historical compression context asks for the same geometric L
        # already contained in the v0.76 card.  Reuse only that exact value.
        if _reuse_member_length_context(migrated):
            continue
        break

    retained = [
        row for row in rows[index:]
        if str(row.get("node_id") or "") not in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES
    ]
    setattr(migrated, _RETAINED_ATTR, retained)
    return migrated


def _consume_retained_history(session: GuidedCalculationSession) -> None:
    """Apply retained exact-node answers after a newly inserted question is answered."""
    retained = list(getattr(session, _RETAINED_ATTR, []) or [])
    safety = 0
    while safety < 200:
        safety += 1
        if _reuse_member_length_context(session):
            continue
        while retained and str(retained[0].get("node_id") or "") in RETIRED_EFFECTIVE_LENGTH_GUIDED_NODES:
            retained.pop(0)
        if not retained or session.current_node_id is None:
            break
        row = retained[0]
        if session.current_node_id != str(row.get("node_id") or ""):
            break
        try:
            session.submit(row.get("payload"), provenance=row.get("provenance"))
        except FireUIError:
            break
        retained.pop(0)
    setattr(session, _RETAINED_ATTR, retained)


def _render_string_decision_selectbox(core: Any, card: Mapping[str, Any], old_payload: Any, mode_key: str):
    """Render decision options as a selectbox even when the quantity type is string.

    The frozen FIRE load-case decision uses data_type=string but declares an
    explicit decision option set.  The generic renderer previously treated that
    as free text.  Decision options are authoritative regardless of scalar dtype.
    """
    fields = list(card.get("fields") or [])
    options = list(card.get("options") or [])
    if card.get("node_type") != "decision" or len(fields) != 1 or not options:
        return None
    if fields[0].get("data_type") not in {"string", "text"}:
        return None

    st = core._st()
    values = [row.get("value") for row in options]
    labels = {row.get("value"): str(row.get("label") or row.get("value")) for row in options}
    descriptions = {row.get("value"): str(row.get("description") or "") for row in options}
    current = old_payload if old_payload in values else None
    selected = st.selectbox(
        fields[0].get("label") or "Вариант",
        values,
        index=values.index(current) if current in values else None,
        placeholder="— выберите —",
        format_func=lambda value: labels.get(value, str(value)),
        key=core._key(mode_key, card["node_id"], fields[0].get("quantity_id") or "decision"),
    )
    if selected is not None and descriptions.get(selected):
        st.caption(descriptions[selected])
    return selected, None, selected is not None


def install(core: Any) -> None:
    """Install v0.77 base UX and own the v0.78->v0.79 migration transactionally."""
    # Deliberately do not call v0.78.install(): its prefix-only migration is the
    # defect fixed here.  We reuse its renderer and graph/runtime producers but
    # migrate sessions ourselves.
    _v077.install(core)
    if getattr(core, _INSTALLED, False):
        return

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
        install_gamma_c_registry(registry)
        graph_id = str(app.model.graph.get("graph_id") or "")

        if GRAPH_SUFFIX not in graph_id:
            old_sessions = dict(app.service.sessions)
            new_model = build_model(app.model)
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = _semantic_replay(old_session, new_model, registry)
            app.model = new_model
            app.service = new_service
            _invalidate_contract_cache()

        for session in app.service.sessions.values():
            _consume_retained_history(session)
        return app

    def _new_application():
        return _upgrade(previous_new_application())

    def _ensure_app():
        return _upgrade(previous_ensure_app())

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        component = str((card.get("presentation") or {}).get("component") or "generic")
        if component == _GAMMA_COMPONENT:
            st = core._st()
            st.info(
                "Таблица 1 здесь определяет коэффициент условий работы γc. "
                "Это не схема закрепления элемента: закрепление и μ относятся к таблице 30 "
                "и повторно на этом шаге не задаются."
            )
            return _v078_ui._render_gamma_c_editor(core, card, old_payload, mode_key)

        decision = _render_string_decision_selectbox(core, card, old_payload, mode_key)
        if decision is not None:
            return decision
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = [
    "_consume_retained_history",
    "_known_member_length_mm",
    "_render_string_decision_selectbox",
    "_reuse_member_length_context",
    "_semantic_replay",
    "install",
]
