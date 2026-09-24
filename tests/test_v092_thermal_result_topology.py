from __future__ import annotations

from types import SimpleNamespace

import streamlit_thermal_result_v092 as v092


def _env_with_trace(*, include_rreq: bool = False):
    ledger = [
        {
            "quantity_id": "protection_12_5_calculation_trace",
            "value": {
                "status": "COMPLETE",
                "visualization": {
                    "schema": "sp554_v085_fvm_visualization_v2",
                    "time_series": [],
                    "profile_samples": [],
                },
            },
        }
    ]
    if include_rreq:
        ledger.append({"quantity_id": "required_fire_resistance_min", "value": 60.0})
    return {"state": {"ledger": ledger}}


class _Core(SimpleNamespace):
    def __init__(self, events):
        super().__init__()
        self.events = events

        def body(app, sid, env, card, old_payload, old_provenance, mode_key):
            events.append(("body", card.get("node_id")))
            return "payload", "provenance", True

        self._render_card_body = body

    @staticmethod
    def _ledger_value(env, quantity_id):
        for row in env.get("state", {}).get("ledger", []):
            if row.get("quantity_id") == quantity_id:
                return row.get("value")
        return None


def test_completed_protected_trace_is_detected_without_rreq():
    core = _Core([])
    env = _env_with_trace(include_rreq=False)

    trace = v092.completed_protected_trace(core, env)
    assert trace is not None
    assert trace["status"] == "COMPLETE"
    assert v092.should_render_completed_protected_result(core, env) is True
    assert core._ledger_value(env, "required_fire_resistance_min") is None


def test_current_interactive_card_renders_finished_fdm_before_later_question(monkeypatch):
    events = []
    core = _Core(events)

    def render_fdm(inner_core, env):
        assert inner_core is core
        assert inner_core._ledger_value(env, "required_fire_resistance_min") is None
        events.append(("fdm", "trace-only"))

    monkeypatch.setattr(v092._v086, "_render_fdm_visualizations", render_fdm)
    v092.install(core)

    result = core._render_card_body(
        object(),
        "sid",
        _env_with_trace(include_rreq=False),
        {"node_id": "NEXT_INTERACTIVE_RREQ_OR_OTHER_QUESTION"},
        None,
        None,
        "guided",
    )

    assert events == [
        ("fdm", "trace-only"),
        ("body", "NEXT_INTERACTIVE_RREQ_OR_OTHER_QUESTION"),
    ]
    assert result == ("payload", "provenance", True)


def test_renderer_topology_is_identical_before_and_after_rreq(monkeypatch):
    calls = []
    core = _Core([])
    monkeypatch.setattr(v092._v086, "_render_fdm_visualizations", lambda _core, _env: calls.append("fdm"))
    v092.install(core)

    for include_rreq in (False, True):
        core._render_card_body(
            object(),
            "sid",
            _env_with_trace(include_rreq=include_rreq),
            {"node_id": "CURRENT"},
            None,
            None,
            "guided",
        )

    assert calls == ["fdm", "fdm"]


def test_no_protected_trace_means_no_extra_renderer(monkeypatch):
    calls = []
    core = _Core([])
    monkeypatch.setattr(v092._v086, "_render_fdm_visualizations", lambda _core, _env: calls.append("fdm"))
    v092.install(core)

    core._render_card_body(
        object(),
        "sid",
        {"state": {"ledger": []}},
        {"node_id": "CURRENT"},
        None,
        None,
        "guided",
    )

    assert calls == []
