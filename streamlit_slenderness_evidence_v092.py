"""Install v0.92 Table-32 limiting-slenderness evidence on guided sessions.

This layer is intentionally installed after manual-net remediation because that
layer also wraps the MECH7 primary binder. Existing sessions are semantically
replayed so completed binder evidence receives the same trace contract.
"""
from __future__ import annotations

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v075_zy_runtime import BINDER_NODE_ID
from standard_core.sp16_mech7_v092_slenderness_evidence import install_registry_remediation
from streamlit_guided_ux_v086 import _semantic_replay

_INSTALLED = "_fire_v092_slenderness_evidence_installed"


def install(core) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _upgrade(app):
        registry = app.service.registry
        current = registry.get(BINDER_NODE_ID)
        already = bool(getattr(current, "_sp16_v092_slenderness_evidence", False))
        install_registry_remediation(registry)
        if already:
            return app

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
