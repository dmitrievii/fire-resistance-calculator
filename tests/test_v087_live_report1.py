from __future__ import annotations

import inspect

import streamlit_live_report_v087 as live


def test_v087_normative_reference_renders_all_explicit_locators():
    text = live._refs_text(
        [
            {
                "standard_id": "SP16",
                "section": "8",
                "clause": "8.2.1",
                "formula_ref": "(8.4)",
                "table_ref": "7",
            },
            {
                "standard_id": "SP554",
                "clause": "12.5",
                "figure_ref": "1",
            },
        ]
    )
    assert "SP16" in text
    assert "разд. 8" in text
    assert "п. 8.2.1" in text
    assert "формула (8.4)" in text
    assert "табл. 7" in text
    assert "SP554" in text
    assert "п. 12.5" in text
    assert "рис. 1" in text


def test_v087_view_model_preserves_report_order_and_explicit_check_verdicts():
    report = {
        "blocks": [
            {"report_block_id": "A#1", "sequence": 1, "kind": "INPUT"},
            {"report_block_id": "B#1", "sequence": 2, "kind": "CHECK"},
        ],
        "sections": [
            {"section_key": "input_data", "title_ru": "Исходные данные", "block_ids": ["A#1"]},
            {"section_key": "verification", "title_ru": "Проверки", "block_ids": ["B#1"]},
        ],
        "summary": {
            "checks": [
                {"report_block_id": "B#1", "verdict": "PASS"},
            ]
        },
    }
    view = live._report_view_model(report)
    assert view["latest_block"]["report_block_id"] == "B#1"
    assert [row["section_key"] for row in view["sections"]] == ["input_data", "verification"]
    assert view["verdicts"] == {"B#1": "PASS"}
    assert view["blocks"] == report["blocks"]


def test_v087_live_report_is_projection_only_not_second_calculation_engine():
    source = inspect.getsource(live)
    assert "build_report_ir5" in source
    assert "render_report_markdown" in source
    assert "sp554_fire_thermal_guided_workflow" not in source
    assert "ExecutionRegistry" not in source
    assert "register(" not in source
    assert "eval(" not in source


def test_v087_install_replaces_stacked_right_renderer_and_keeps_rollback_handle():
    calls = []

    class Core:
        pass

    core = Core()

    def legacy(env):
        calls.append(env)

    core._render_ledger_trace = legacy
    live.install(core)

    assert core._fire_live_report_v087_installed is True
    assert core._fire_live_report_v087_previous_renderer is legacy
    assert core._render_ledger_trace is not legacy
    # Idempotent install must not move the rollback handle to the v0.87 wrapper.
    live.install(core)
    assert core._fire_live_report_v087_previous_renderer is legacy
    assert calls == []


def test_v087_live_report_installer_is_last_in_streamlit_entrypoint():
    import streamlit_app

    source = inspect.getsource(streamlit_app)
    assert "from streamlit_live_report_v087 import install as _install_live_report" in source
    assert source.index("_install_guided_ux(_core)") < source.index("_install_live_report(_core)")
