"""v0.81 installer: retire scalar stability replay and bind the z/y handoff."""
from __future__ import annotations

import copy
from typing import Any

import streamlit_guided_ux_v080 as _v080

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v081_end_to_end_overlay import (
    GRAPH_SUFFIX,
    RETIRED_SCALAR_STABILITY_NODES,
    build_model,
)
from standard_core.sp16_mech7_v081_runtime import install_registry_remediation

_INSTALLED = "_fire_v081_end_to_end_consistency_installed"
_RETAINED_ATTR = "_v079_retained_interaction_history"
_RETAINED_GAMMA_ATTR = "_v080_retained_gamma_c_case_id"


def _filtered_rows(source: Any) -> list[dict[str, Any]]:
    """Return the complete exact-answer stream minus retired scalar nodes.

    v0.79 stores answers that occur after an inserted question in a retained
    tail.  A later release migration must treat that tail as part of the source
    answer stream or those exact user answers would be lost merely because the
    app graph was upgraded again before the inserted question was answered.
    """
    rows = copy.deepcopy(list(getattr(source, "interaction_history", []) or []))
    rows.extend(copy.deepcopy(list(getattr(source, _RETAINED_ATTR, []) or [])))
    return [
        row
        for row in rows
        if str(row.get("node_id") or "") not in RETIRED_SCALAR_STABILITY_NODES
    ]


def _semantic_replay(source: Any, model: Any, registry: Any):
    """Reuse v0.80 exact migration while dropping the complete legacy chain."""
    rows = _filtered_rows(source)

    class FilteredSource:
        entry_node_id = source.entry_node_id
        interaction_history = rows

        @staticmethod
        def plain_values():
            return source.plain_values()

    migrated = _v080._semantic_replay(FilteredSource(), model, registry)
    retained = [
        row
        for row in list(getattr(migrated, _RETAINED_ATTR, []) or [])
        if str(row.get("node_id") or "") not in RETIRED_SCALAR_STABILITY_NODES
    ]
    setattr(migrated, _RETAINED_ATTR, retained)

    # A Table-1 case retained by v0.80 may not yet exist in the quantity ledger;
    # preserve that exact case id across another graph migration without reverse
    # mapping from the numeric gamma_c value.
    gamma_case = getattr(source, _RETAINED_GAMMA_ATTR, None)
    if _v080._validated_gamma_case(gamma_case) is not None:
        setattr(migrated, _RETAINED_GAMMA_ATTR, gamma_case)
    return migrated


def _consume_exact_reuse(session: Any) -> None:
    retained = [
        row
        for row in list(getattr(session, _RETAINED_ATTR, []) or [])
        if str(row.get("node_id") or "") not in RETIRED_SCALAR_STABILITY_NODES
    ]
    setattr(session, _RETAINED_ATTR, retained)
    _v080._consume_exact_reuse(session)


def install(core: Any) -> None:
    """Install v0.80, then transactionally upgrade live sessions to v0.81."""
    _v080.install(core)
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
        registry = app.service.registry
        install_registry_remediation(registry)
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
            _consume_exact_reuse(session)
        return app

    def _new_application():
        return _upgrade(previous_new_application())

    def _ensure_app():
        return _upgrade(previous_ensure_app())

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    setattr(core, _INSTALLED, True)


__all__ = ["_consume_exact_reuse", "_filtered_rows", "_semantic_replay", "install"]
