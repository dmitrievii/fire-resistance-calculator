from __future__ import annotations

from types import SimpleNamespace

import pytest

from streamlit_guided_ux_v0106 import (
    _LegacyIWResolutionError,
    _is_legacy_iw,
    _legacy_payload,
    _table1_editor,
)


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


def test_v0108_legacy_iw_enum_scalar_uses_declared_net_gross_values():
    card = {
        "title": "Учитывать изменение моментов инерции и моментов сопротивления после ослабления?",
        "fields": [
            {
                "quantity_id": "legacy_net_iw_choice",
                "data_type": "enum",
                "enum_values": ["gross", "net"],
            }
        ],
        "submit_shape": "scalar",
    }

    assert _legacy_payload(card, True) == "net"
    assert _legacy_payload(card, False) == "gross"


def test_v0108_legacy_iw_enum_can_resolve_from_option_labels_not_order():
    card = {
        "fields": [{"quantity_id": "legacy_net_iw_choice", "data_type": "enum"}],
        "options": [
            {"value": "A", "label": "Не учитывать изменение I/W — использовать gross"},
            {"value": "B", "label": "Учитывать ослабление — использовать net"},
        ],
        "submit_shape": "object",
    }

    assert _legacy_payload(card, True) == {"legacy_net_iw_choice": "B"}
    assert _legacy_payload(card, False) == {"legacy_net_iw_choice": "A"}


def test_v0108_legacy_iw_enum_fails_closed_when_semantics_are_unknown():
    card = {
        "fields": [
            {
                "quantity_id": "legacy_net_iw_choice",
                "data_type": "enum",
                "enum_values": ["option_a", "option_b"],
            }
        ],
        "submit_shape": "scalar",
    }

    with pytest.raises(_LegacyIWResolutionError, match="no unambiguous"):
        _legacy_payload(card, True)


def test_v0108_legacy_iw_enum_fails_closed_when_semantics_are_ambiguous():
    card = {
        "fields": [
            {
                "quantity_id": "legacy_net_iw_choice",
                "data_type": "enum",
                "enum_values": ["net", "net_reduced", "gross"],
            }
        ],
        "submit_shape": "scalar",
    }

    with pytest.raises(_LegacyIWResolutionError, match="multiple"):
        _legacy_payload(card, True)


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


def test_v0107_compression_gamma_c_keeps_v0106_distinction_message():
    calls = []

    class ST:
        @staticmethod
        def markdown(message):
            calls.append(("markdown", message))

        @staticmethod
        def info(message):
            calls.append(("info", message))

        @staticmethod
        def selectbox(label, values, **kwargs):
            calls.append(("selectbox", label))
            return values[0]

        @staticmethod
        def caption(message):
            calls.append(("caption", message))

    core = SimpleNamespace(st=ST(), _key=lambda *args: "gamma-c-test")
    card = {
        "node_id": "SP16_I_V078_GAMMA_C_COMPRESSION_CASE",
        "fields": [{"quantity_id": "sp16_gamma_c_case_compression"}],
        "options": [{"value": "default", "label": "default", "description": "γc = 1,00"}],
    }

    result = _table1_editor(core, card, None, "current")

    assert result == ("default", None, True)
    info_messages = [message for kind, message in calls if kind == "info"]
    assert info_messages
    assert "сжатия/устойчивости" in info_messages[0]
    assert "для изгиба" in info_messages[0]
    assert "не переносится автоматически" in info_messages[0]
