from __future__ import annotations

from types import SimpleNamespace

import streamlit_expertise_report_v090_install as layer


class _St:
    def __init__(self):
        self.session_state = {}


def test_v0104_transient_widget_rerun_reuses_report_bundle(monkeypatch):
    calls = {"build": 0, "render": 0}
    st = _St()
    core = SimpleNamespace(st=st)
    session = object()
    app = SimpleNamespace(
        service=SimpleNamespace(
            model=object(),
            get_session=lambda sid: session,
        )
    )
    env = {"state": {"status": "AWAITING_INPUT", "interaction_history": [{"node_id": "loads"}], "ledger": [{"quantity_id": "N", "value": 1.0}]}}

    def build(model, got_session):
        calls["build"] += 1
        assert got_session is session
        return {"blocks": [{"id": "report"}]}

    def render(report):
        calls["render"] += 1
        return "# report"

    monkeypatch.setattr(layer, "build_report_ir_v092", build)
    monkeypatch.setattr(layer, "render_expertise_narrative_markdown_v092", render)

    first = layer._report_bundle(core, env, app, "sid")
    second = layer._report_bundle(core, env, app, "sid")

    assert first == second
    assert calls == {"build": 1, "render": 1}


def test_v0104_accepted_state_change_invalidates_report_bundle(monkeypatch):
    calls = {"build": 0, "render": 0}
    core = SimpleNamespace(st=_St())
    app = SimpleNamespace(service=SimpleNamespace(model=object(), get_session=lambda sid: object()))

    monkeypatch.setattr(layer, "build_report_ir_v092", lambda model, session: calls.__setitem__("build", calls["build"] + 1) or {"blocks": []})
    monkeypatch.setattr(layer, "render_expertise_narrative_markdown_v092", lambda report: calls.__setitem__("render", calls["render"] + 1) or "report")

    env1 = {"state": {"interaction_history": [{"node_id": "loads"}], "ledger": []}}
    env2 = {"state": {"interaction_history": [{"node_id": "loads"}, {"node_id": "next"}], "ledger": [{"quantity_id": "N", "value": 1000.0}]}}

    layer._report_bundle(core, env1, app, "sid")
    layer._report_bundle(core, env2, app, "sid")

    assert calls == {"build": 2, "render": 2}
    assert layer._state_fingerprint(env1) != layer._state_fingerprint(env2)


def test_v0104_export_reuses_prebuilt_markdown_source():
    source = open("streamlit_expertise_report_v090_install.py", encoding="utf-8").read()
    assert "def _render_export(core: Any, report: Mapping[str, Any], markdown: str)" in source
    export_body = source.split("def _render_export", 1)[1].split("def render_expertise_report_v090", 1)[0]
    assert "render_expertise_narrative_markdown_v092(report)" not in export_body
