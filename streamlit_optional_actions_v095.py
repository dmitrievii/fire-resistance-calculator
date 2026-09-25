"""v0.95 optional canonical-action input remediation.

Unselected mechanical action components are physical zeros, not missing required
fields.  This installer keeps the v0.92 canonical axis semantics and changes only
the guided input contract: N/Mz/My/Mx/Qz/Qy action fields may be omitted and are
materialized as explicit 0.0 USER_INPUT values at submission time.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from standard_core.fire_ui0 import FireDAGModel, GuidedCalculationService, GuidedCalculationSession

_INSTALLED = "_fire_v095_optional_actions_installed"
_SESSION_PATCHED = "_fire_v095_optional_actions_session_patched"

# B is intentionally excluded: its direct-input applicability is controlled by
# the dedicated bimoment question.  N may also be omitted for pure bending.
_ACTION_QIDS = frozenset({
    "ambient_N_force", "ambient_M_z", "ambient_M_y", "ambient_M_x",
    "ambient_Q_z", "ambient_Q_y",
    "N_force", "M_z", "M_y", "M_x", "Q_z", "Q_y",
})


def _patch_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    for node in out.get("nodes", []):
        if not isinstance(node, dict) or node.get("node_type") not in {"input", "standard_handoff"}:
            continue
        for binding in node.get("produces", []):
            if isinstance(binding, dict) and binding.get("quantity_id") in _ACTION_QIDS:
                binding["required"] = False
                binding["default_value"] = 0.0
    return out


def _patch_model(model: FireDAGModel) -> FireDAGModel:
    patched = _patch_graph(model.graph)
    if patched == model.graph:
        return model
    return FireDAGModel(
        patched,
        source_path=model.source_path,
        presentation_policy=model.presentation_policy,
    )


def _install_session_defaulting() -> None:
    if getattr(GuidedCalculationSession, _SESSION_PATCHED, False):
        return
    previous = GuidedCalculationSession._prepare_interactive_outputs

    def _prepare(self, node, payload, provenance):
        bindings = node.get("produces", []) or []
        action_bindings = [
            b for b in bindings
            if isinstance(b, Mapping) and b.get("quantity_id") in _ACTION_QIDS
        ]
        if action_bindings and len(bindings) > 1:
            if payload is None:
                payload_map: dict[str, Any] = {}
            elif isinstance(payload, Mapping):
                payload_map = dict(payload)
            else:
                return previous(self, node, payload, provenance)
            for binding in action_bindings:
                qid = str(binding["quantity_id"])
                if qid not in payload_map or payload_map[qid] is None:
                    payload_map[qid] = float(binding.get("default_value", 0.0))
            payload = payload_map
        return previous(self, node, payload, provenance)

    GuidedCalculationSession._prepare_interactive_outputs = _prepare
    setattr(GuidedCalculationSession, _SESSION_PATCHED, True)


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    _install_session_defaulting()
    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _upgrade(app):
        new_model = _patch_model(app.model)
        if new_model is app.model:
            return app
        old_sessions = dict(app.service.sessions)
        new_service = GuidedCalculationService(new_model, registry=app.service.registry)
        for sid, session in old_sessions.items():
            session.model = new_model
            session.registry = app.service.registry
            new_service.sessions[sid] = session
        app.model = new_model
        app.service = new_service
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except Exception:
            pass
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_patch_graph"]
