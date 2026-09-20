from pathlib import Path

import streamlit_mobile_ux as mobile


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_styles_define_compact_phone_layout():
    css = mobile.MOBILE_STYLES
    assert "@media (max-width: 768px)" in css
    assert ".fire-card h3" in css
    assert "font-size: 1.34rem" in css
    assert ".block-container" in css
    assert ".fire-tech-footer { display: none; }" in css


def test_mobile_composition_collapses_administration_and_diagnostics():
    source = (ROOT / "streamlit_mobile_ux.py").read_text(encoding="utf-8")
    assert 'st.expander("Расчёт · файл · история", expanded=False)' in source
    assert 'st.expander("Расчётные величины · Trace", expanded=False)' in source
    assert source.count("core._render_history(app, env)") == 1
    assert "DAG: {contract.get" in source


def test_streamlit_entrypoint_installs_mobile_layer_after_graphic_layer():
    source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    graph = source.index("_install_graphic_selectors(_core)")
    mobile_install = source.index("_install_mobile_ux(_core)")
    assert graph < mobile_install


def test_mobile_layer_is_presentation_only():
    source = (ROOT / "streamlit_mobile_ux.py").read_text(encoding="utf-8")
    assert "standard_core" not in source
    assert "/api/" not in source
    assert "FireUI1Application" not in source
    assert "core._render_card_body" in source
    assert "core._submit" in source
