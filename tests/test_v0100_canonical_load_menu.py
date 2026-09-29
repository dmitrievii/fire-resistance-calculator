from __future__ import annotations

from streamlit_canonical_load_menu_v0100 import _contract, _payload_for_contract


def _card(*qids: str):
    return {"fields": [{"quantity_id": qid} for qid in qids]}


def test_v0101_ambient_contract_uses_full_active_canonical_ids_including_bimoment():
    card = _card(
        "ambient_load_combination",
        "ambient_N_force",
        "ambient_M_z",
        "ambient_M_y",
        "ambient_M_x",
        "ambient_Q_z",
        "ambient_Q_y",
        "ambient_B_bimoment",
    )
    q = _contract("ambient", card)
    assert q == {
        "N": "ambient_N_force",
        "Mz": "ambient_M_z",
        "My": "ambient_M_y",
        "Mx": "ambient_M_x",
        "Qz": "ambient_Q_z",
        "Qy": "ambient_Q_y",
        "B": "ambient_B_bimoment",
        "combo": "ambient_load_combination",
    }
    assert "ambient_Q_x" not in q.values()
    assert "ambient_T_torsion" not in q.values()


def test_v0101_payload_emits_bimoment_and_cannot_emit_legacy_qx_or_t_fields():
    q = _contract(
        "ambient",
        _card(
            "ambient_load_combination",
            "ambient_N_force",
            "ambient_M_z",
            "ambient_M_y",
            "ambient_M_x",
            "ambient_Q_z",
            "ambient_Q_y",
            "ambient_B_bimoment",
        ),
    )
    payload = _payload_for_contract(
        q,
        {"N": -100.0, "Mz": 12.0, "My": 3.0, "Mx": 2.0, "Qz": 5.0, "Qy": 1.0, "B": 0.25},
        kind="ambient",
    )
    assert set(payload) == {
        "ambient_load_combination",
        "ambient_N_force",
        "ambient_M_z",
        "ambient_M_y",
        "ambient_M_x",
        "ambient_Q_z",
        "ambient_Q_y",
        "ambient_B_bimoment",
    }
    assert "ambient_Q_x" not in payload
    assert "ambient_T_torsion" not in payload
    assert payload["ambient_M_z"] == 12.0e6
    assert payload["ambient_M_x"] == 2.0e6
    assert payload["ambient_Q_z"] == 5.0e3
    assert payload["ambient_B_bimoment"] == 0.25e9
    combo = payload["ambient_load_combination"]
    assert combo["B_kNm2"] == 0.25
    assert combo["display_units"]["bimoment"] == "kNm2"


def test_v0101_contract_never_invents_b_or_other_fields_absent_from_card():
    q = _contract("ambient", _card("ambient_N_force", "ambient_M_z"))
    payload = _payload_for_contract(
        q,
        {"N": -10.0, "Mz": 4.0, "My": 0.0, "Mx": 0.0, "Qz": 0.0, "Qy": 0.0, "B": 0.0},
        kind="ambient",
    )
    assert payload == {"ambient_N_force": -10.0e3, "ambient_M_z": 4.0e6}
    assert q["B"] is None


def test_v0101_fire_contract_restores_fire_bimoment_too():
    q = _contract("fire", _card("N_force", "M_z", "B_bimoment"))
    assert q["B"] == "B_bimoment"
    payload = _payload_for_contract(
        q,
        {"N": -1.0, "Mz": 2.0, "My": 0.0, "Mx": 0.0, "Qz": 0.0, "Qy": 0.0, "B": 0.1},
        kind="fire",
    )
    assert payload["B_bimoment"] == 0.1e9


def test_v0100_installed_after_canonical_action_and_optional_action_layers():
    text = open("streamlit_app.py", encoding="utf-8").read()
    assert "_install_canonical_load_menu_v0100(_core)" in text
    assert text.index("_install_canonical_actions_v092(_core)") < text.index("_install_canonical_load_menu_v0100(_core)")
    assert text.index("_install_optional_actions_v095(_core)") < text.index("_install_canonical_load_menu_v0100(_core)")
