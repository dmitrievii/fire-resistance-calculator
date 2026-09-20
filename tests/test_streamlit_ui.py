from pathlib import Path

from standard_core.fire_ui1_http import FireUI1Application

import streamlit_app as sui


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_is_presentation_only_and_has_no_http_api_dependency():
    entry = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    core = (ROOT / "streamlit_app_core.py").read_text(encoding="utf-8")
    source = entry + "\n" + core
    assert "FireUI1Application" in source
    assert "/api/" not in source
    assert "standard_core" in source
    assert "gamma_t_required /" not in source
    assert "gamma_e_required /" not in source


def test_streamlit_contract_structured_inputs_have_renderer_or_are_explicitly_fail_closed():
    app = FireUI1Application.from_package_root(ROOT)
    contract = app.ui_contract()
    policy = contract["presentation_policy"]
    excluded = set(policy.get("guided_excluded_nodes", []))
    prefixes = tuple(policy.get("guided_excluded_node_prefixes", []))
    intentionally_fail_closed = {"SP554_H_SP14"}

    missing = []
    for card in contract["node_cards"]:
        if not card.get("interactive"):
            continue
        dtypes = {f.get("data_type") for f in card.get("fields", [])}
        if all(dtype in sui.BASIC_TYPES for dtype in dtypes):
            continue
        node_id = card["node_id"]
        if node_id in excluded or node_id.startswith(prefixes):
            continue
        component = (card.get("presentation") or {}).get("component") or "generic"
        if component in sui.STRUCTURED_COMPONENTS:
            continue
        if node_id in intentionally_fail_closed:
            continue
        missing.append((node_id, component, sorted(dtypes)))

    assert missing == []


def test_streamlit_runtime_uses_exact_guided_entry_and_section_editor_contract():
    app = FireUI1Application.from_package_root(ROOT)
    created = app.create_session()
    sid = created["session_id"]
    assert created["current_card"]["node_id"] == "SP554_D_LOAD_BEARING"
    for value in [True, False, "hot_rolled_section"]:
        state = app.service.submit(sid, value)
    assert state["current_card"]["node_id"] == "SP554_D_GEOMETRY_MODE"
    assert state["current_card"]["presentation"]["component"] == "section_editor_entry"


def test_streamlit_matrix_parsers_are_strict_and_dimension_friendly():
    assert sui._parse_vector("3, 5, 7") == [3.0, 5.0, 7.0]
    assert sui._parse_vector("3; 5; 7") == [3.0, 5.0, 7.0]
    assert sui._parse_vector("3") is None
    assert sui._parse_matrix("25,45\n30,50") == [[25.0, 45.0], [30.0, 50.0]]
    assert sui._parse_matrix("25,45") is None


def test_graphic_selectors_cover_table21_table7_table30_and_thermal_geometry():
    source = (ROOT / "streamlit_graphic_selectors.py").read_text(encoding="utf-8")
    for token in [
        'component == "table21_type_selector"',
        'component == "table7_curve_selector"',
        'component == "table30_scheme_selector"',
        'component == "heated_sides_selector"',
        'component == "protection_perimeter_mode_selector"',
        '<svg',
    ]:
        assert token in source
    for value in ['"1"', '"2"', '"3"', '"4"']:
        assert value in source


def test_streamlit_entrypoint_smoke_via_apptest():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=45)
    assert not at.exception
    assert any("FIRE Resistance Calculator" in md.value for md in at.markdown)
