"""v0.109 atomic weakening route remediation.

The structured ``section_weakening_model`` is the sole guided source for section
weakening. Older DAG interaction nodes that separately ask how I/W should be
handled are retained only for audit/backward package compatibility and are
excluded from the guided route and navigation.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping


_INSTALLED = "_fire_v0109_atomic_weakening_route_installed"
CANONICAL_HOLE_MODEL = "central_web_bolt_hole_formula45_v1"
NET_RESOLVER_NODE = "SP554_G_NET_SECTION_PROPERTIES"
LEGACY_GUIDED_NODES = frozenset(
    {
        "SP554_D_NET_PROPERTY_REDUCTION",
        "SP554_I_NET_SECTION_MANUAL_PROPERTIES",
    }
)


def _apply_atomic_route(app: Any) -> Any:
    """Route both weakening states directly to the canonical net-property resolver."""
    policy = app.model.presentation_policy
    overrides = policy.setdefault("navigation_overrides", {})
    rules = list(overrides.get("SP16_D_WEAKENING") or [])

    rewritten: list[dict[str, Any]] = []
    seen: set[bool] = set()
    for raw in rules:
        rule = copy.deepcopy(dict(raw))
        when = rule.get("when") or {}
        if when.get("quantity_id") == "sp16_has_weakening" and isinstance(when.get("value"), bool):
            value = bool(when["value"])
            seen.add(value)
            rule["to_node_id"] = NET_RESOLVER_NODE
            rule["id"] = f"V0109_WEAKENING_{'HOLES' if value else 'NONE'}_TO_NET_RESOLVER"
        rewritten.append(rule)

    for value in (False, True):
        if value not in seen:
            rewritten.append(
                {
                    "when": {"quantity_id": "sp16_has_weakening", "value": value},
                    "to_node_id": NET_RESOLVER_NODE,
                    "id": f"V0109_WEAKENING_{'HOLES' if value else 'NONE'}_TO_NET_RESOLVER",
                }
            )
    overrides["SP16_D_WEAKENING"] = rewritten

    excluded = list(policy.get("guided_excluded_nodes") or [])
    for node_id in sorted(LEGACY_GUIDED_NODES):
        if node_id not in excluded:
            excluded.append(node_id)
    policy["guided_excluded_nodes"] = excluded

    hidden = list(policy.get("hidden_normative_nodes") or [])
    for node_id in sorted(LEGACY_GUIDED_NODES):
        if node_id not in hidden:
            hidden.append(node_id)
    policy["hidden_normative_nodes"] = hidden
    return app


def _normalize_weakening_payload(card: Mapping[str, Any], payload: Any) -> Any:
    """Normalize the unified editor payload to the executor's canonical model ID."""
    component = str((card.get("presentation") or {}).get("component") or "")
    if component != "section_weakening_editor" or not isinstance(payload, Mapping):
        return payload
    normalized = copy.deepcopy(dict(payload))
    holes = normalized.get("holes_present")
    if holes is True:
        # v0.107/v0.108 emitted a presentation-only model name that the core
        # executor does not support. The editor represents the existing
        # formula-(45) central web-hole model, so submit its canonical ID.
        normalized["model"] = CANONICAL_HOLE_MODEL
    elif holes is False:
        normalized["model"] = "none"
    return normalized


def _filtered_history_env(env: Mapping[str, Any]) -> dict[str, Any]:
    """Remove internal compatibility interactions from Back/jump/history UI."""
    clean = copy.deepcopy(dict(env))
    state = copy.deepcopy(dict(clean.get("state") or {}))
    history = []
    for row in state.get("interaction_history") or []:
        if isinstance(row, Mapping) and str(row.get("node_id") or "") in LEGACY_GUIDED_NODES:
            continue
        history.append(row)
    state["interaction_history"] = history
    clean["state"] = state
    return clean


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app
    previous_card_body = core._render_card_body
    previous_render_history = core._render_history
    previous_card_map = core._card_map

    def _new_application():
        return _apply_atomic_route(previous_new_application())

    def _ensure_app():
        return _apply_atomic_route(previous_ensure_app())

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        result = previous_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)
        if not isinstance(result, tuple) or len(result) != 3:
            return result
        payload, provenance, ready = result
        return _normalize_weakening_payload(card, payload), provenance, ready

    def _render_history(app, env):
        return previous_render_history(app, _filtered_history_env(env))

    def _card_map(app):
        cards = previous_card_map(app)
        return {node_id: card for node_id, card in cards.items() if node_id not in LEGACY_GUIDED_NODES}

    core._new_application = _new_application
    core._ensure_app = _ensure_app
    core._render_card_body = _render_card_body
    core._render_history = _render_history
    core._card_map = _card_map
    setattr(core, _INSTALLED, True)


__all__ = [
    "CANONICAL_HOLE_MODEL",
    "LEGACY_GUIDED_NODES",
    "NET_RESOLVER_NODE",
    "_apply_atomic_route",
    "_filtered_history_env",
    "_normalize_weakening_payload",
    "install",
]
