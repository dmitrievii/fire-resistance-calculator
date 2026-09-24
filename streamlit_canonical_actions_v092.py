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
from standard_core.sp16_mech_v092_presentation import (
    PRESENTATION_MARKER,
    build_presentation_model,
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
        graph_already_canonical = GRAPH_SUFFIX in str(app.model.graph.get("graph_id") or "")
        presentation_already_canonical = bool(app.model.presentation_policy.get(PRESENTATION_MARKER))
        old_sessions = dict(app.service.sessions)

        graph_model = app.model if graph_already_canonical else build_model(app.model)
        new_model = build_presentation_model(graph_model)

        # Scope compatibility wrappers from the final active canonical model.
        # Unrelated v0.91 final-SP554 executors retain exact identity.
        install_registry_remediation(registry, new_model)

        if not graph_already_canonical:
            # Action meanings changed: historical sessions must be replayed only
            # up to the first semantically changed load interaction.
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = replay_prefix_without_axis_alias(
                    old_session, new_model, registry
                )
            app.model = new_model
            app.service = new_service
            _invalidate_contract()
        elif not presentation_already_canonical:
            # Only presentation metadata changed. Preserve the canonical ledger
            # and interaction history exactly; rebind retained sessions to the
            # rebuilt model so current cards/overrides use the new policy.
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, session in old_sessions.items():
                session.model = new_model
                session.registry = registry
                new_service.sessions[sid] = session
            app.model = new_model
            app.service = new_service
            _invalidate_contract()
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
