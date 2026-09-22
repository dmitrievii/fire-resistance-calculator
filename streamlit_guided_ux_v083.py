"""v0.83 installer: real guided-route closure and deterministic UI defaults."""
from __future__ import annotations

from typing import Any

import streamlit_guided_ux_v082 as _v082

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v083_full_route_overlay import GRAPH_SUFFIX, build_model
from standard_core.sp16_mech7_v083_runtime import install_registry_remediation

_INSTALLED = "_fire_v083_full_guided_e2e_closure_installed"
_GAMMA_CT_NODE_ID = "SP554_D_GOST27751_GAMMA_CT"
_FIRE_LOAD_NODE_ID = "SP16_D_FIRE_LOAD_CASE_MODE"


def _install_render_defaults(core: Any) -> None:
    previous_generic = core._render_generic

    def _render_generic(card, old_payload, old_provenance, mode_key):
        node_id = card.get("node_id")
        if old_payload is None and node_id == _GAMMA_CT_NODE_ID:
            old_payload = False
        if old_payload is None and node_id == _FIRE_LOAD_NODE_ID:
            old_payload = "same_as_ambient"
        return previous_generic(card, old_payload, old_provenance, mode_key)

    core._render_generic = _render_generic


def _semantic_replay(source: Any, model: Any, registry: Any):
    # v0.82 already preserves exact v0.78 Table-1 classification and retained
    # session answers.  Reuse that migration logic and stop naturally where the
    # v0.83 topology intentionally bypasses a retired legacy prompt.
    migrated = _v082._semantic_replay(source, model, registry)
    _v082._consume_exact_reuse(migrated)
    return migrated


def install(core: Any) -> None:
    _v082.install(core)
    if getattr(core, _INSTALLED, False):
        return

    _install_render_defaults(core)
    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _invalidate_contract_cache() -> None:
        try:
            core._st().session_state.pop("_fire_contract", None)
            core._st().session_state.pop("_fire_contract_map", None)
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
                new_service.sessions[sid] = _semantic_replay(old_session, new_model, registry)
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


__all__ = ["install"]
