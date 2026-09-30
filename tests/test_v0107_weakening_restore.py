from __future__ import annotations

from streamlit_guided_ux_v0106 import _is_legacy_iw, _legacy_payload


def test_v0107_legacy_iw_title_is_hard_suppressed():
    card = {
        "title": "Учитывать изменение моментов инерции и моментов сопротивления после ослабления?",
        "fields": [{"quantity_id": "legacy_net_iw", "data_type": "boolean"}],
        "submit_shape": "object",
    }
    assert _is_legacy_iw(card) is True
    assert _legacy_payload(card, True) == {"legacy_net_iw": True}


def test_v0107_legacy_iw_scalar_shape_is_resolved_as_scalar():
    card = {
        "prompt": "Choosing gross I/W is an explicit engineering assumption; it is never applied silently.",
        "title": "Учитывать изменение моментов инерции и моментов сопротивления после ослабления?",
        "fields": [{"quantity_id": "legacy_net_iw", "data_type": "boolean"}],
        "submit_shape": "scalar",
    }
    assert _is_legacy_iw(card) is True
    assert _legacy_payload(card, False) is False


def test_v0107_manual_net_runtime_contract_remains_canonical():
    from standard_core.fire_ui14_manual_net_v092 import MANUAL_MODE
    assert MANUAL_MODE == "manual_net_properties"
    text = open("streamlit_guided_ux_v0106.py", encoding="utf-8").read()
    for qid in (
        "I_z_n_mm4", "I_y_n_mm4", "W_z_n_mm3", "W_y_n_mm3",
        "W_pl_z_eff_mm3", "W_pl_y_eff_mm3", "I_omega_n_mm6", "W_omega_eff_mm4",
    ):
        assert qid in text
    assert '"net_property_mode": mode' in text
    assert "Aₙ не вводится вручную" in text
