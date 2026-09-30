"""Install v0.105 MECH7 section-class routing into new and retained apps."""
from __future__ import annotations

import copy
from typing import Any

from standard_core.fire_ui0 import GuidedCalculationService, GuidedCalculationSession, FireUIError
from standard_core.sp16_mech7_v0105_section_class_route import GRAPH_SUFFIX, build_model

_INSTALLED = "_fire_v0105_mech7_section_class_route_installed"


def _replay(session, model, registry):
    migrated = GuidedCalculationSession(model, entry_node_id=session.entry_node_id, registry=registry)
    for row in copy.deepcopy(session.interaction_history):
        expected = str(row.get("node_id") or "")
        if migrated.current_node_id != expected:
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except FireUIError:
            break
    return migrated


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous_new = core._new_application
    previous_ensure = core._ensure_app

    def upgrade(app):
        if GRAPH_SUFFIX in str(app.model.graph.get("graph_id") or ""):
            return app
        old_sessions = dict(app.service.sessions)
        model = build_model(app.model)
        service = GuidedCalculationService(model, registry=app.service.registry)
        for sid, session in old_sessions.items():
            service.sessions[sid] = _replay(session, model, service.registry)
        app.model = model
        app.service = service
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except Exception:
            pass
        return app

    core._new_application = lambda: upgrade(previous_new())
    core._ensure_app = lambda: upgrade(previous_ensure())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
