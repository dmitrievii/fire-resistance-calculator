"""Install v0.92 full-phi evidence on fresh and retained guided sessions."""
from __future__ import annotations

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v076_graph_overlay import STATE_NODE_ID
from standard_core.sp16_mech7_v092_phi_evidence import install_registry_remediation
from streamlit_guided_ux_v086 import _semantic_replay

_INSTALLED = "_fire_v092_full_phi_evidence_installed"


def install(core) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _upgrade(app):
        registry = app.service.registry
        previous = registry.get(STATE_NODE_ID)
        already = bool(getattr(previous, "_sp16_v092_full_phi_evidence", False))
        install_registry_remediation(registry)
        if already:
            return app

        # Existing completed MECH7 state traces predate the richer evidence.
        # Replay semantic user interactions through the same model with the
        # enriched executor so retained sessions get the same trace contract.
        old_sessions = dict(app.service.sessions)
        if old_sessions:
            service = GuidedCalculationService(app.model, registry=registry)
            for sid, old_session in old_sessions.items():
                service.sessions[sid] = _semantic_replay(old_session, app.model, registry)
            app.service = service
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
