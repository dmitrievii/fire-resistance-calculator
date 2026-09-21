"""v0.73 compatibility remediation for already-open Streamlit calculation sessions.

This module does not add or alter any SP16/SP554 equation.  It migrates a legacy
FIRE-UI1 session that was created before v0.72 by replaying its explicit
interaction history into a fresh session while injecting the user's explicit
SP16 Table-3 material-safety category immediately before the existing material
editor answer is replayed.  All downstream calculations are therefore executed
again through the current registry instead of patching a blocked result in
place.
"""
from __future__ import annotations

import copy
from typing import Any

from .fire_ui0 import FireUIError, GuidedCalculationSession
from .material_resistance import material_safety_factor

MATERIAL_EDITOR_NODE_ID = "SP554_I_STEEL_STRENGTH_EDITOR"
MATERIAL_SAFETY_QUANTITY_ID = "material_safety_category"
MATERIAL_SAFETY_INPUT_NODE_ID = "SP16_I_MATERIAL_SAFETY_CATEGORY"


def replay_with_material_safety_category(
    session: GuidedCalculationSession,
    category: str,
) -> GuidedCalculationSession:
    """Return a freshly replayed session with one explicit SP16 Table-3 choice.

    The original session is never mutated.  Callers may replace it in the
    service session map only after this function returns successfully.
    """
    if not isinstance(category, str) or not category.strip():
        raise FireUIError("material_safety_category requires an explicit SP16 Table-3 category")

    # Validate against the already-qualified Table-3 producer.  The numerical
    # gamma_m result is deliberately not stored here: v0.72 materializes it
    # through the qualified runtime adapter, preserving one source of truth.
    try:
        material_safety_factor(category)
    except (KeyError, TypeError, ValueError) as exc:
        raise FireUIError(f"unsupported SP16 Table-3 material safety category: {category}") from exc

    history = copy.deepcopy(session.interaction_history)
    if not any(str(row.get("node_id") or "") == MATERIAL_EDITOR_NODE_ID for row in history):
        raise FireUIError("legacy session has no completed material-strength editor to migrate")

    migrated = GuidedCalculationSession(
        session.model,
        entry_node_id=session.entry_node_id,
        registry=session.registry,
    )
    injected = False

    for row in history:
        node_id = str(row.get("node_id") or "")
        if migrated.current_node_id != node_id:
            raise FireUIError(
                "cannot replay legacy session after v0.73 remediation: "
                f"expected {node_id}, reached {migrated.current_node_id}"
            )

        if node_id == MATERIAL_EDITOR_NODE_ID:
            migrated._set_quantity(
                MATERIAL_SAFETY_QUANTITY_ID,
                category,
                node_id=MATERIAL_SAFETY_INPUT_NODE_ID,
                source_kind="USER_INPUT",
                provenance={
                    "ui_surface": "v0.73_existing_session_remediation",
                    "standard": "SP16 Table 3",
                    "migration": "legacy_open_session_replay",
                },
            )
            injected = True

        migrated.submit(row.get("payload"), provenance=row.get("provenance"))

    if not injected:
        raise FireUIError("SP16 Table-3 category was not injected during legacy-session replay")

    return migrated


__all__ = [
    "MATERIAL_EDITOR_NODE_ID",
    "MATERIAL_SAFETY_INPUT_NODE_ID",
    "MATERIAL_SAFETY_QUANTITY_ID",
    "replay_with_material_safety_category",
]
