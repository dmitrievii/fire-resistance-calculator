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
        already_canonical = GRAPH_SUFFIX in str(app.model.graph.get("graph_id") or "")
        old_sessions = dict(app.service.sessions) if not already_canonical else {}
        new_model = app.model if already_canonical else build_model(app.model)

        # Scope the compatibility wrappers from the *active canonical model*.
        # This deliberately leaves unrelated v0.91 final-SP554 executors
        # untouched, preserving exact registry identity and frozen-DAG isolation.
        install_registry_remediation(registry, new_model)

        if not already_canonical:
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
