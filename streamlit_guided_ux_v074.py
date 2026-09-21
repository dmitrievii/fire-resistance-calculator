from __future__ import annotations

"""v0.74 SP16 Annex Б.1 physical-property hydration integration.

The v0.73 UI/session migration remains authoritative for legacy Table-3 input.
This layer upgrades both freshly-created and already-retained FireUI1Application
objects to the v0.74 MECH7 compatibility wrapper, which materializes ``E_norm``
from the qualified СП16 Table Б.1 dataset when no explicit producer exists.
"""

from typing import Any

import streamlit_guided_ux_v073 as _v073
from standard_core.sp16_mech7_v074_physical_remediation import install_registry_remediation

_INSTALL_SENTINEL = "_guided_ux_v074_installed"
_CANONICAL_NEW_APP = "_guided_ux_v074_canonical_new_application"
_CANONICAL_ENSURE_APP = "_guided_ux_v074_canonical_ensure_app"


def _remediate_application(app: Any) -> Any:
    """Upgrade the service registry and every detached live-session registry."""
    install_registry_remediation(app.service.registry)
    for session in list(app.service.sessions.values()):
        if session.registry is not app.service.registry:
            install_registry_remediation(session.registry)
    return app


def _install_new_application_patch(core: Any) -> None:
    if not hasattr(core, _CANONICAL_NEW_APP):
        setattr(core, _CANONICAL_NEW_APP, core._new_application)
    canonical = getattr(core, _CANONICAL_NEW_APP)

    def remediated_new_application():
        return _remediate_application(canonical())

    setattr(remediated_new_application, "_guided_ux_v074_new_app_remediation", True)
    core._new_application = remediated_new_application


def _install_existing_application_patch(core: Any) -> None:
    if not hasattr(core, _CANONICAL_ENSURE_APP):
        setattr(core, _CANONICAL_ENSURE_APP, core._ensure_app)
    canonical = getattr(core, _CANONICAL_ENSURE_APP)

    def remediated_ensure_app():
        return _remediate_application(canonical())

    setattr(remediated_ensure_app, "_guided_ux_v074_existing_app_remediation", True)
    core._ensure_app = remediated_ensure_app


def install(core: Any) -> None:
    if getattr(core, _INSTALL_SENTINEL, False):
        return

    # v0.73 first: retain the explicit Table-3 legacy-session replay and all
    # presentation/runtime patches already qualified there.  v0.74 then wraps
    # the resulting application accessors, so hot-reloaded sessions are upgraded
    # without discarding their calculation history.
    _v073.install(core)
    _install_new_application_patch(core)
    _install_existing_application_patch(core)
    setattr(core, _INSTALL_SENTINEL, True)


__all__ = ["install"]
