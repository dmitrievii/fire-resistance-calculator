"""Streamlit installer for the v0.91 final-SP554 guided runtime contract."""
from __future__ import annotations

from typing import Any

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.fire_sp554_runtime_v091 import install_guided_registry_remediation
from standard_core.fire_sp554_v091_guided_overlay import GRAPH_SUFFIX, build_model
from streamlit_guided_ux_v086 import _semantic_replay


_INSTALLED = "_fire_v091_final_sp554_guided_installed"


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
        install_guided_registry_remediation(registry)
        if GRAPH_SUFFIX not in str(app.model.graph.get("graph_id") or ""):
            old_sessions = dict(app.service.sessions)
            new_model = build_model(app.model)
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = _semantic_replay(old_session, new_model, registry)
            app.model = new_model
            app.service = new_service
            _invalidate_contract()
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
