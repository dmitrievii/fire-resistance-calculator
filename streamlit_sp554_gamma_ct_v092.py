"""Streamlit installer for the v0.92 mandatory-gamma_ct guided remediation."""
from __future__ import annotations

from typing import Any

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.fire_sp554_runtime_v092 import install_guided_registry_remediation_v092
from standard_core.fire_sp554_v092_guided_overlay import (
    GRAPH_SUFFIX,
    build_model,
    replay_without_obsolete_gamma_ct,
)

_INSTALLED = "_fire_v092_gamma_ct_guided_bypass_installed"


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
        old_sessions = dict(app.service.sessions)
        registry = app.service.registry
        # Registry binding is intentionally repeated for retained applications:
        # an already transformed graph may still carry the pre-remediation
        # executor object in memory after a hot reload.
        install_guided_registry_remediation_v092(registry)
        new_model = build_model(app.model)
        graph_changed = new_model is not app.model
        if graph_changed:
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = replay_without_obsolete_gamma_ct(
                    old_session, new_model, registry
                )
            app.model = new_model
            app.service = new_service
            _invalidate_contract()
        elif not str(app.model.graph.get("graph_id") or "").endswith(GRAPH_SUFFIX):
            # Defensive fail-closed guard: build_model must establish the active
            # v0.92 graph contract before the application can continue.
            raise RuntimeError("v0.92 gamma_ct guided graph remediation was not installed")
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
