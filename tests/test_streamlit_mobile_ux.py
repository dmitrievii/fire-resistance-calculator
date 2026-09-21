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


def test_mobile_styles_reserve_streamlit_toolbar_safe_area():
    css = mobile.MOBILE_STYLES
    assert "padding-top: calc(3.85rem + env(safe-area-inset-top, 0px)) !important;" in css
    assert "margin-top: .15rem;" in css
    assert ".fire-title { font-size: 1.44rem;" in css
    assert "padding-top: .55rem !important;" not in css


def test_mobile_streamlit_header_is_fixed_opaque_and_theme_aware_while_scrolling():
    css = mobile.MOBILE_STYLES
    assert '[data-testid="stHeader"]' in css
    assert "position: fixed !important;" in css
    assert "background-color: inherit !important;" in css
    assert "background-image: none !important;" in css
    assert "var(--background-color, #ffffff)" not in css
    assert "z-index: 1000000 !important;" in css
    assert "border-bottom: 1px solid rgba(128, 128, 128, 0.24) !important;" in css
    assert '[data-testid="stToolbar"]' in css
    assert "z-index: 1000001 !important;" in css


def test_mobile_composition_keeps_file_admin_collapsed_and_history_after_active_step():
    source = (ROOT / "streamlit_mobile_ux.py").read_text(encoding="utf-8")
    file_admin = 'st.expander("Расчёт · файл", expanded=False)'
    trace = 'st.expander("Расчётные величины · Trace", expanded=False)'
    render = "core._render_card_body("
    submit = "core._submit(app, sid, card, payload, provenance, editing)"
    history = "core._render_history(app, env)"

    assert file_admin in source
    assert trace in source
    assert source.count(history) == 1
    assert source.index(file_admin) < source.index(render)
    assert source.index(render) < source.index(submit) < source.index(history)
    assert "DAG: {contract.get" in source


def test_streamlit_entrypoint_installs_mobile_layer_after_graphic_layer():
    source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    graph = source.index("_install_graphic_selectors(_core)")
    mobile_install = source.index("_install_mobile_ux(_core)")
    assert graph < mobile_install


def test_mobile_layer_is_presentation_only():
    source = (ROOT / "streamlit_mobile_ux.py").read_text(encoding="utf-8")
    assert "from standard_core" not in source
    assert "import standard_core" not in source
    assert "/api/" not in source
    assert "FireUI1Application" not in source
    assert "core._render_card_body" in source
    assert "core._submit" in source
