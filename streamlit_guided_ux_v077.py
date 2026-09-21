"""v0.77 retained-session replay and history-edit remediation.

v0.76 introduced a descendant graph overlay.  The v0.75 installer previously
mistook that descendant graph for an old graph on every Streamlit rerun and
replayed the live session.  The parent installers are now descendant-aware.

This layer additionally preserves the user's explicit SP16 Table-3 material
safety category when editing a later history step.  That category is authored
inside the compact material card and therefore is not itself an interaction
history row; a vanilla history replay would otherwise discard it and trigger the
legacy migration prompt again.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

import streamlit_guided_ux_v076 as _v076
import streamlit_guided_ux_v072 as _v072
from standard_core.fire_ui0 import FireUIError, GuidedCalculationSession
from standard_core.sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    MATERIAL_SAFETY_INPUT_NODE_ID,
    MATERIAL_SAFETY_QUANTITY_ID,
)

_INSTALLED = "_fire_v077_session_replay_remediation_installed"


def _material_category_for_edit(core: Any, session: GuidedCalculationSession) -> str | None:
    """Return the already-explicit Table-3 category without inventing a default."""
    current = session.plain_values().get(MATERIAL_SAFETY_QUANTITY_ID)
    if isinstance(current, str) and current in _v072._MATERIAL_SAFETY_LABELS:
        return current
    key = _v072._category_state_key(MATERIAL_EDITOR_NODE_ID)
    widget_value = core._st().session_state.get(key)
    if isinstance(widget_value, str) and widget_value in _v072._MATERIAL_SAFETY_LABELS:
        return widget_value
    return None


def _edit_with_material_safety_anchor(
    session: GuidedCalculationSession,
    node_id: str,
    payload: Any,
    *,
    provenance: Mapping[str, Any] | None,
    category: str,
) -> GuidedCalculationSession:
    """Transactionally edit one history answer while retaining explicit Table-3 input."""
    indices = [i for i, row in enumerate(session.interaction_history) if row["node_id"] == node_id]
    if not indices:
        raise FireUIError(f"node {node_id} has not been answered")
    idx = indices[0]
    prior = copy.deepcopy(session.interaction_history[:idx])

    old_qv = session.values.get(MATERIAL_SAFETY_QUANTITY_ID)
    anchor_provenance = copy.deepcopy(getattr(old_qv, "provenance", None)) or {
        "ui_surface": "v0.77_history_edit_replay",
        "standard": "SP16 Table 3",
        "migration": "preserve_explicit_material_safety_category",
    }

    migrated = GuidedCalculationSession(
        session.model,
        entry_node_id=session.entry_node_id,
        registry=session.registry,
    )

    injected = False

    def inject_if_needed(next_node_id: str) -> None:
        nonlocal injected
        if injected or next_node_id != MATERIAL_EDITOR_NODE_ID:
            return
        migrated._set_quantity(
            MATERIAL_SAFETY_QUANTITY_ID,
            category,
            node_id=MATERIAL_SAFETY_INPUT_NODE_ID,
            source_kind="USER_INPUT",
            provenance=anchor_provenance,
        )
        injected = True

    for row in prior:
        expected = str(row.get("node_id") or "")
        if migrated.current_node_id != expected:
            raise FireUIError("cannot replay history after DAG/branch inconsistency")
        inject_if_needed(expected)
        migrated.submit(row.get("payload"), provenance=row.get("provenance"))

    if migrated.current_node_id != node_id:
        raise FireUIError("edited node is no longer reachable after replay")
    inject_if_needed(node_id)
    migrated.submit(payload, provenance=provenance)
    return migrated


def install(core: Any) -> None:
    """Install v0.76, then make history replay preserve the explicit Table-3 anchor."""
    _v076.install(core)
    if getattr(core, _INSTALLED, False):
        return

    previous_submit = core._submit

    def _submit(app, sid, card, payload, provenance, editing):
        if not editing:
            return previous_submit(app, sid, card, payload, provenance, editing)

        session = app.service.get_session(sid)
        node_id = str(card.get("node_id") or "")
        material_in_replay = node_id == MATERIAL_EDITOR_NODE_ID or any(
            str(row.get("node_id") or "") == MATERIAL_EDITOR_NODE_ID
            for row in session.interaction_history[: next(
                (i for i, row in enumerate(session.interaction_history) if row.get("node_id") == node_id),
                len(session.interaction_history),
            )]
        )
        if not material_in_replay:
            return previous_submit(app, sid, card, payload, provenance, editing)

        category = _material_category_for_edit(core, session)
        if category is None:
            core._st().error(
                "Не найден ранее выбранный параметр контроля проката по таблице 3 СП16. "
                "Скрытое значение γm не подставляется; откройте шаг материала и выберите категорию явно."
            )
            return None

        try:
            migrated = _edit_with_material_safety_anchor(
                session,
                node_id,
                payload,
                provenance=provenance,
                category=category,
            )
        except FireUIError as exc:
            core._st().error(str(exc))
            return None

        app.service.sessions[sid] = migrated
        core._st().session_state["_fire_edit_node"] = None
        core._st().rerun()
        return None

    core._submit = _submit
    setattr(core, _INSTALLED, True)


__all__ = ["_edit_with_material_safety_anchor", "install"]
