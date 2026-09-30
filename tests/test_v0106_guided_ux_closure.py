from __future__ import annotations

from types import SimpleNamespace

from streamlit_guided_ux_v0106 import _TABLE1_HUMAN, _is_legacy_iw, install


def test_v0106_legacy_iw_card_is_detected_by_user_visible_semantics():
    card = {
        "node_id": "SOME_RETAINED_COMPAT_NODE",
        "title": "Учитывать изменение моментов инерции и моментов сопротивления после ослабления?",
        "fields": [{"quantity_id": "some_old_boolean", "data_type": "boolean"}],
    }
    assert _is_legacy_iw(card) is True


def test_v0106_table1_labels_are_engineering_readable_not_position_codes():
    assert "Балки" in _TABLE1_HUMAN["row1"]
    assert "Колонны" in _TABLE1_HUMAN["row2_095"]
    assert "Примечание".lower() in _TABLE1_HUMAN["default"].lower()
    for label in _TABLE1_HUMAN.values():
        assert not label.lower().startswith("табл.1 поз.")
        assert not label.lower().startswith("позиция ")


def test_v0106_closed_report_gate_does_not_call_heavy_renderer():
    calls = []

    class ST:
        session_state = {}
        @staticmethod
        def checkbox(*args, **kwargs):
            return False
        @staticmethod
        def caption(message):
            calls.append(("caption", message))

    def heavy(env):
        calls.append(("HEAVY", env))

    core = SimpleNamespace(
        st=ST(),
        _render_ledger_trace=heavy,
        _render_card_body=lambda *args, **kwargs: (None, None, False),
    )
    install(core)
    core._render_ledger_trace({"state": {"ledger": list(range(1000))}})
    assert not any(row[0] == "HEAVY" for row in calls)


def test_v0106_report_gate_calls_heavy_renderer_only_when_explicitly_enabled():
    calls = []

    class ST:
        session_state = {}
        @staticmethod
        def checkbox(*args, **kwargs):
            return True
        @staticmethod
        def caption(message):
            calls.append(("caption", message))

    def heavy(env):
        calls.append(("HEAVY", env))

    core = SimpleNamespace(
        st=ST(),
        _render_ledger_trace=heavy,
        _render_card_body=lambda *args, **kwargs: (None, None, False),
    )
    install(core)
    env = {"state": {"ledger": []}}
    core._render_ledger_trace(env)
    assert ("HEAVY", env) in calls


def test_v0106_is_installed_after_v098_final_weakening_layer():
    text = open("streamlit_app.py", encoding="utf-8").read()
    assert "_install_guided_ux_v0106(_core)" in text
    assert text.index("_install_weakening_v098(_core)") < text.index("_install_guided_ux_v0106(_core)")
