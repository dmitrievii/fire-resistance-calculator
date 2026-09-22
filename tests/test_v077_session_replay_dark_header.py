from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    MATERIAL_SAFETY_INPUT_NODE_ID,
    MATERIAL_SAFETY_QUANTITY_ID,
)
from streamlit_guided_ux_v072 import _category_state_key
from streamlit_guided_ux_v077 import (
    _edit_with_material_safety_anchor,
    _repair_missing_table3_from_widget,
)


ROOT = Path(__file__).resolve().parents[1]


def _model() -> FireDAGModel:
    graph = {
        "graph_id": "v077-history-anchor-test",
        "engine_contract": {},
        "quantities": [
            {
                "id": "fy_norm",
                "name_ru": "Ryn",
                "data_type": "number",
                "canonical_unit": "N/mm2",
                "source_policy": {},
            },
            {
                "id": MATERIAL_SAFETY_QUANTITY_ID,
                "name_ru": "Категория таблицы 3",
                "data_type": "enum",
                "canonical_unit": None,
                "enum_values": [
                    {"value": "statistical_control", "label": "statistical_control"},
                    {"value": "other_conforming", "label": "other_conforming"},
                ],
                "source_policy": {},
            },
            {
                "id": "later_value",
                "name_ru": "Поздний ввод",
                "data_type": "number",
                "canonical_unit": None,
                "source_policy": {},
            },
        ],
        "nodes": [
            {
                "id": MATERIAL_EDITOR_NODE_ID,
                "node_type": "input",
                "owner_standard_id": "SP16_2017",
                "title": "Material",
                "produces": [{"quantity_id": "fy_norm", "required": True}],
                "input_spec": {"user_prompt": "Material"},
                "normative_refs": [],
            },
            {
                "id": "LATER_INPUT",
                "node_type": "input",
                "owner_standard_id": "SP16_2017",
                "title": "Later",
                "produces": [{"quantity_id": "later_value", "required": True}],
                "input_spec": {"user_prompt": "Later"},
                "normative_refs": [],
            },
            {
                "id": "RESULT",
                "node_type": "result",
                "owner_standard_id": "SP16_2017",
                "title": "Result",
                "produces": [],
                "consumes": [],
                "normative_refs": [],
            },
        ],
        "edges": [
            {
                "id": "E1",
                "from_node_id": MATERIAL_EDITOR_NODE_ID,
                "to_node_id": "LATER_INPUT",
                "edge_type": "control",
            },
            {
                "id": "E2",
                "from_node_id": "LATER_INPUT",
                "to_node_id": "RESULT",
                "edge_type": "control",
            },
        ],
    }
    return FireDAGModel(graph)


def test_v077_history_edit_preserves_explicit_table3_category():
    model = _model()
    session = GuidedCalculationSession(model, entry_node_id=MATERIAL_EDITOR_NODE_ID, registry=ExecutionRegistry())
    session._set_quantity(
        MATERIAL_SAFETY_QUANTITY_ID,
        "statistical_control",
        node_id=MATERIAL_SAFETY_INPUT_NODE_ID,
        source_kind="USER_INPUT",
        provenance={"ui_surface": "material_strength_editor", "standard": "SP16 Table 3"},
    )
    session.submit(355.0)
    session.submit(1.0)

    assert session.status == "RESULT"
    assert session.plain_values()[MATERIAL_SAFETY_QUANTITY_ID] == "statistical_control"

    migrated = _edit_with_material_safety_anchor(
        session,
        "LATER_INPUT",
        2.0,
        provenance=None,
        category="statistical_control",
    )

    assert migrated is not session
    assert migrated.status == "RESULT"
    assert migrated.plain_values()[MATERIAL_SAFETY_QUANTITY_ID] == "statistical_control"
    assert migrated.plain_values()["later_value"] == 2.0
    assert [row["node_id"] for row in migrated.interaction_history] == [MATERIAL_EDITOR_NODE_ID, "LATER_INPUT"]


def test_v077_repairs_already_open_replayed_session_from_surviving_explicit_widget_value():
    model = _model()
    broken = GuidedCalculationSession(model, entry_node_id=MATERIAL_EDITOR_NODE_ID, registry=ExecutionRegistry())
    broken.submit(355.0)
    broken.submit(1.0)
    assert MATERIAL_SAFETY_QUANTITY_ID not in broken.plain_values()

    app = SimpleNamespace(service=SimpleNamespace(sessions={"fire-000001": broken}))
    state = {_category_state_key(MATERIAL_EDITOR_NODE_ID): "statistical_control"}
    core = SimpleNamespace(_st=lambda: SimpleNamespace(session_state=state))

    repaired_app = _repair_missing_table3_from_widget(core, app)
    repaired = repaired_app.service.sessions["fire-000001"]

    assert repaired is not broken
    assert repaired.status == "RESULT"
    assert repaired.plain_values()[MATERIAL_SAFETY_QUANTITY_ID] == "statistical_control"
    assert repaired.interaction_history == broken.interaction_history


def test_v077_parent_overlay_installers_are_descendant_aware():
    v075 = (ROOT / "streamlit_guided_ux_v075.py").read_text(encoding="utf-8")
    v076 = (ROOT / "streamlit_guided_ux_v076.py").read_text(encoding="utf-8")
    assert "if GRAPH_SUFFIX in graph_id:" in v075
    assert "if GRAPH_SUFFIX in graph_id:" in v076
    assert "if graph_id.endswith(GRAPH_SUFFIX):" not in v075
    assert "if graph_id.endswith(GRAPH_SUFFIX):" not in v076


def test_v077_mobile_header_has_no_forced_white_dark_mode_fallback():
    css = (ROOT / "streamlit_mobile_ux.py").read_text(encoding="utf-8")
    assert "background-color: inherit !important;" in css
    assert "var(--background-color, #ffffff)" not in css


def test_v077_layer_remains_in_descendant_installer_chain():
    entrypoint = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    descendant = (ROOT / "streamlit_guided_ux_v078.py").read_text(encoding="utf-8")
    assert "from streamlit_guided_ux_v078 import install as _install_guided_ux" in entrypoint
    assert "import streamlit_guided_ux_v077 as _v077" in descendant
    assert "_v077.install(core)" in descendant
