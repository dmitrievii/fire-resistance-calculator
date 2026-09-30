from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from standard_core.fire_ui14_manual_net_v092 import _manual_raw
from standard_core.fire_ui14_section_weakening import _parse_model
from streamlit_weakening_route_v0109 import (
    CANONICAL_HOLE_MODEL,
    LEGACY_GUIDED_NODES,
    NET_RESOLVER_NODE,
    _apply_atomic_route,
    _filtered_history_env,
    _normalize_weakening_payload,
)


def _fake_app():
    policy = {
        "hidden_normative_nodes": [],
        "navigation_overrides": {
            "SP16_D_WEAKENING": [
                {
                    "when": {"quantity_id": "sp16_has_weakening", "value": False},
                    "to_node_id": NET_RESOLVER_NODE,
                    "id": "OLD_NONE",
                },
                {
                    "when": {"quantity_id": "sp16_has_weakening", "value": True},
                    "to_node_id": "SP554_D_NET_PROPERTY_REDUCTION",
                    "id": "OLD_HOLES_TO_LEGACY_POLICY",
                },
            ]
        },
    }
    return SimpleNamespace(model=SimpleNamespace(presentation_policy=policy))


def test_v0109_both_weakening_states_route_directly_to_net_resolver():
    app = _apply_atomic_route(_fake_app())
    rules = app.model.presentation_policy["navigation_overrides"]["SP16_D_WEAKENING"]
    by_value = {rule["when"]["value"]: rule for rule in rules}

    assert by_value[False]["to_node_id"] == NET_RESOLVER_NODE
    assert by_value[True]["to_node_id"] == NET_RESOLVER_NODE
    assert LEGACY_GUIDED_NODES.issubset(set(app.model.presentation_policy["guided_excluded_nodes"]))
    assert LEGACY_GUIDED_NODES.issubset(set(app.model.presentation_policy["hidden_normative_nodes"]))


def test_v0109_automatic_editor_payload_uses_core_supported_geometry_model():
    card = {"presentation": {"component": "section_weakening_editor"}}
    payload = {
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": 22.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "automatic_geometry",
    }

    normalized = _normalize_weakening_payload(card, payload)
    assert normalized["model"] == CANONICAL_HOLE_MODEL
    parsed = _parse_model({"section_weakening_model": normalized})
    assert parsed is not None
    assert parsed.model == CANONICAL_HOLE_MODEL


def test_v0109_manual_net_values_remain_inline_and_are_consumed_by_core_override():
    card = {"presentation": {"component": "section_weakening_editor"}}
    payload = {
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": 22.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "manual_net_properties",
        "manual_net_properties": {
            "I_z_n_mm4": 1.1e8,
            "I_y_n_mm4": 2.2e7,
            "W_z_n_mm3": 8.1e5,
            "W_y_n_mm3": 2.5e5,
        },
    }

    normalized = _normalize_weakening_payload(card, payload)
    manual = _manual_raw({"section_weakening_model": normalized})

    assert normalized["model"] == CANONICAL_HOLE_MODEL
    assert manual == normalized["manual_net_properties"]


def test_v0109_back_history_drops_both_retained_weakening_cards():
    env = {
        "state": {
            "interaction_history": [
                {"node_id": "SP554_I_SECTION_WEAKENING", "payload": {"holes_present": True}},
                {"node_id": "SP554_D_NET_PROPERTY_REDUCTION", "payload": "manual_net_properties"},
                {"node_id": "SP554_I_NET_SECTION_MANUAL_PROPERTIES", "payload": {"I_z_n_mm4": 1.0}},
                {"node_id": "SP554_I_AMBIENT_LOADS", "payload": {"N": 1.0}},
            ]
        }
    }

    clean = _filtered_history_env(env)
    ids = [row["node_id"] for row in clean["state"]["interaction_history"]]

    assert ids == ["SP554_I_SECTION_WEAKENING", "SP554_I_AMBIENT_LOADS"]
    assert not (set(ids) & LEGACY_GUIDED_NODES)


def test_v0109_entrypoint_installs_atomic_route_after_v0108_guided_closure():
    text = Path("streamlit_app.py").read_text(encoding="utf-8")
    guided = text.index("_install_guided_ux_v0106(_core)")
    atomic = text.index("_install_weakening_route_v0109(_core)")
    assert atomic > guided
