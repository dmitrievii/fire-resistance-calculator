from __future__ import annotations

import importlib


def test_v090_streamlit_install_does_not_mutate_v089_renderer():
    v089 = importlib.import_module("streamlit_expertise_report_v089")
    original = v089.render_expertise_narrative_markdown

    # Importing the deployment entrypoint executes the cumulative installer chain.
    importlib.import_module("streamlit_app")

    assert v089.render_expertise_narrative_markdown is original


def test_v090_isolated_installer_is_active_in_streamlit_core():
    core = importlib.import_module("streamlit_app_core")
    importlib.import_module("streamlit_app")

    assert getattr(core, "_fire_expertise_report_v090_isolated_installed", False) is True
    assert hasattr(core, "_fire_expertise_report_v090_previous_renderer")
