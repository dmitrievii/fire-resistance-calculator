"""Streamlit installer for the v0.92 canonical SP16 action contract."""
from __future__ import annotations

from typing import Any

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech_v092_canonical_actions import (
    GRAPH_SUFFIX,
    build_model,
    install_registry_remediation,
    replay_prefix_without_axis_alias,
)

_INSTALLED = "_fire_v092_canonical_actions_installed"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

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
                new_service.sessions[sid] = replay_prefix_without_axis_alias(
                    old_session, new_model, registry
                )
            app.model = new_model
            app.service = new_service
            _invalidate_contract()
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
