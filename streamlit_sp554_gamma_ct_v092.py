"""Streamlit installer for the v0.92 mandatory-gamma_ct guided remediation."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from standard_core.fire_ui0 import FireDAGModel, GuidedCalculationService
from standard_core.fire_sp554_runtime_v092 import (
    TENSION_NODE_ID,
    install_guided_registry_remediation_v092,
)
from standard_core.fire_sp554_v092_guided_overlay import (
    GRAPH_SUFFIX,
    TENSION_ALGORITHM_ID,
    _remediate_tension_node,
    build_model,
    replay_without_obsolete_gamma_ct,
)

_INSTALLED = "_fire_v092_gamma_ct_guided_bypass_installed"


def _tension_contract_is_current(app: Any) -> bool:
    node = app.model.nodes.get(TENSION_NODE_ID)
    if not isinstance(node, Mapping):
        return True  # synthetic/minimal graphs used outside the full fire route
    spec = node.get("calculation_spec")
    return isinstance(spec, Mapping) and spec.get("algorithm_id") == TENSION_ALGORITHM_ID


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

        graph_id = str(app.model.graph.get("graph_id") or "")
        has_route_marker = GRAPH_SUFFIX in graph_id
        has_tension_contract = _tension_contract_is_current(app)

        if not has_route_marker:
            # Fresh/pre-v0.92 model: perform the complete obsolete-subgraph bypass
            # and §9.1 active-contract remediation.
            new_model = build_model(app.model)
        elif not has_tension_contract:
            # Retained application created by the earlier v0.92 bypass already
            # has later cumulative suffixes. Re-applying transform_graph would
            # duplicate the gamma marker; patch only the active §9.1 node/trace
            # declaration and preserve all later overlays verbatim.
            graph = copy.deepcopy(app.model.graph)
            _remediate_tension_node(graph)
            new_model = FireDAGModel(
                graph,
                source_path=app.model.source_path,
                presentation_policy=app.model.presentation_policy,
            )
        else:
            new_model = app.model

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

        if GRAPH_SUFFIX not in str(app.model.graph.get("graph_id") or ""):
            raise RuntimeError("v0.92 gamma_ct guided graph remediation was not installed")
        if not _tension_contract_is_current(app):
            raise RuntimeError("v0.92 SP554 §9.1 guided runtime contract was not installed")
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
