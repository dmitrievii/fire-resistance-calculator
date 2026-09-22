"""v0.80 guided cleanup: exact Table-1 reuse and scalar-lambda retirement."""
from __future__ import annotations

from typing import Any

import streamlit_guided_ux_v079 as _v079

from standard_core.fire_ui0 import FireUIError, GuidedCalculationService
from standard_core.sp16_mech7_v078_gamma_c import (
    INPUT_QID as GAMMA_CASE_QID,
    resolve_gamma_c_compression,
)
from standard_core.sp16_mech7_v078_graph_overlay import INPUT_NODE_ID as GAMMA_INPUT_NODE_ID
from standard_core.sp16_mech7_v080_guided_cleanup_overlay import (
    GRAPH_SUFFIX,
    LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES,
    build_model,
)

_INSTALLED = "_fire_v080_guided_cleanup_installed"
_RETAINED_ATTR = "_v079_retained_interaction_history"


def _semantic_replay(source: Any, model: Any, registry: Any):
    """Reuse v0.79 semantic replay while dropping retired scalar-lambda rows."""
    class FilteredSource:
        entry_node_id = source.entry_node_id
        interaction_history = [
            row
            for row in source.interaction_history
            if str(row.get("node_id") or "") not in LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES
        ]

        @staticmethod
        def plain_values():
            return source.plain_values()

    migrated = _v079._semantic_replay(FilteredSource(), model, registry)
    retained = [
        row
        for row in list(getattr(migrated, _RETAINED_ATTR, []) or [])
        if str(row.get("node_id") or "") not in LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES
    ]
    setattr(migrated, _RETAINED_ATTR, retained)
    return migrated


def _reuse_gamma_c_case(session: Any) -> bool:
    """Submit only an already explicit Table-1 case when the same prompt repeats.

    The numeric gamma_c value is deliberately insufficient for reuse because it
    does not uniquely identify the normative Table-1 classification.  Only the
    exact previously selected case id may be reused.
    """
    if session.current_node_id != GAMMA_INPUT_NODE_ID:
        return False

    case_id = session.plain_values().get(GAMMA_CASE_QID)
    if not isinstance(case_id, str) or not case_id:
        return False
    try:
        resolve_gamma_c_compression(case_id)
    except FireUIError:
        return False

    session.submit(
        case_id,
        provenance={
            "ui_surface": "v0.80_exact_input_reuse",
            "source_node_id": GAMMA_INPUT_NODE_ID,
            "quantity": GAMMA_CASE_QID,
            "rule": "exact reuse only; no inference from numeric gamma_c",
        },
    )
    return True


def _consume_exact_reuse(session: Any) -> None:
    """Consume retained exact-node answers and exact duplicate inputs safely."""
    for _ in range(16):
        before = (session.current_node_id, len(session.interaction_history))
        _v079._consume_retained_history(session)
        reused_gamma = _reuse_gamma_c_case(session)
        after = (session.current_node_id, len(session.interaction_history))
        if after == before:
            break
        if not reused_gamma:
            # v0.79 retained replay already runs until the next mismatch.  If
            # that mismatch is not an exact duplicate gamma question, stop.
            break


def install(core: Any) -> None:
    """Install v0.79, then upgrade active and retained sessions to v0.80."""
    _v079.install(core)
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _invalidate_contract_cache() -> None:
        try:
            core._st().session_state.pop("_fire_contract", None)
            core._st().session_state.pop("_fire_contract_map", None)
        except Exception:
            pass

    def _upgrade(app):
        graph_id = str(app.model.graph.get("graph_id") or "")
        if GRAPH_SUFFIX not in graph_id:
            registry = app.service.registry
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


__all__ = [
    "_consume_exact_reuse",
    "_reuse_gamma_c_case",
    "_semantic_replay",
    "install",
]
