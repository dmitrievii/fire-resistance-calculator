"""Streamlit installer for v0.75 Stage-N7 z/y guided effective-length contract."""
from __future__ import annotations

from typing import Any

import streamlit_guided_ux_v074 as _v074

_INSTALLED = "_fire_v075_effective_length_contract_installed"


def install(core: Any) -> None:
    """Install v0.74 first, then upgrade fresh and retained apps to v0.75."""
    _v074.install(core)
    if getattr(core, _INSTALLED, False):
        return

    from standard_core.fire_ui0 import GuidedCalculationService
    from standard_core.sp16_mech7_v075_zy_runtime import (
        GRAPH_SUFFIX,
        build_model,
        install_registry_remediation,
        replay_prefix_on_model,
    )

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _invalidate_contract_cache() -> None:
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except Exception:
            # Test doubles may expose only a minimal session_state surface.
            pass

    def _upgrade(app):
        graph_id = str(app.model.graph.get("graph_id", ""))
        registry = app.service.registry

        # Always enforce the canonical binder, including retained apps whose
        # registry was already wrapped by v0.72-v0.74.
        install_registry_remediation(registry, app.profile_catalog)

        if graph_id.endswith(GRAPH_SUFFIX):
            return app

        old_sessions = dict(app.service.sessions)
        new_model = build_model(app.model)
        new_service = GuidedCalculationService(new_model, registry=registry)

        # Existing calculations are not discarded. Replay the unchanged prefix
        # transactionally; when the new Section-10 block is reached, replay
        # stops and the user is shown the first previously missing question.
        for sid, old_session in old_sessions.items():
            migrated = replay_prefix_on_model(old_session, new_model, registry)
            new_service.sessions[sid] = migrated

        app.model = new_model
        app.service = new_service
        _invalidate_contract_cache()
        return app

    def _new_application():
        return _upgrade(previous_new_application())

    def _ensure_app():
        return _upgrade(previous_ensure_app())

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    setattr(core, _INSTALLED, True)
