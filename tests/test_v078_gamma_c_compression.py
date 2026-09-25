from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireDAGModel, FireUIError
from standard_core.sp16_mech7_primary_workflow import bind_primary_ambient_evidence
from standard_core.sp16_mech7_v074_physical_remediation import normalize_mech7_inputs
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import (
    INPUT_NODE_ID as V076_INPUT_NODE_ID,
    STATE_NODE_ID,
    build_model as build_v076_model,
)
from standard_core.sp16_mech7_v078_gamma_c import (
    COMPRESSION_CASE_IDS,
    INPUT_QID,
    compression_case_options,
    resolve_gamma_c_compression,
)
from standard_core.sp16_mech7_v078_graph_overlay import (
    CALC_NODE_ID,
    GRAPH_SUFFIX,
    INPUT_NODE_ID,
    build_model,
)

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    return build_model(build_v076_model(build_v075_model(base)))


def _census(active=()):
    return {
        "schema": "sp16_mech2_applicability_census_v1",
        "active_checks": [
            {
                "id": cid,
                "family": "test",
                "label": cid,
                "applicability": "applicable",
                "runtime_status": "inherited_runtime",
                "normative_scope": [],
            }
            for cid in active
        ],
        "context_driven_checks": [],
    }


def test_v078_table1_compression_lookup_is_explicit_and_exact():
    options = compression_case_options()
    ids = [row["value"] for row in options]
    assert ids == list(COMPRESSION_CASE_IDS)
    assert "5_tension_members_gross_section_strength" not in ids
    assert "6_static_steel_fy_le_440_net_section_with_bolt_holes_non_friction" not in ids
    assert not any(case_id.startswith("9") for case_id in ids)

    row = resolve_gamma_c_compression("2_multistorey_columns_height_le_150m")
    assert row["gamma_c_compression"] == pytest.approx(0.95)
    assert row["sp16_table1_compression_evidence"]["classification_source"] == "explicit_user_selection"
    assert "1-6" in row["sp16_table1_compression_evidence"]["version_basis"]

    note5 = resolve_gamma_c_compression("default_unlisted_case_note_5")
    assert note5["gamma_c_compression"] == pytest.approx(1.0)

    with pytest.raises(FireUIError, match="requires an explicit"):
        resolve_gamma_c_compression("")
    with pytest.raises(FireUIError, match="unsupported"):
        resolve_gamma_c_compression("5_tension_members_gross_section_strength")


def test_v078_graph_inserts_table1_card_between_effective_length_and_state():
    model = _active_model()
    assert str(model.graph["graph_id"]).endswith(GRAPH_SUFFIX)
    edges = model.graph["edges"]
    assert not any(edge.get("id") == "V076_E_EFFECTIVE_LENGTH_TO_STATE" for edge in edges)
    assert any(
        edge.get("from_node_id") == V076_INPUT_NODE_ID and edge.get("to_node_id") == INPUT_NODE_ID
        for edge in edges
    )
    assert any(
        edge.get("from_node_id") == INPUT_NODE_ID and edge.get("to_node_id") == CALC_NODE_ID
        for edge in edges
    )
    assert any(
        edge.get("from_node_id") == CALC_NODE_ID and edge.get("to_node_id") == STATE_NODE_ID
        for edge in edges
    )
    card = model.node_card(INPUT_NODE_ID)
    assert card["submit_shape"] == "scalar"
    assert card["presentation"]["component"] == "sp16_table1_gamma_c_compression"
    assert INPUT_QID in {row["quantity_id"] for row in card["fields"]}


def test_v078_step17_compression_gap_closes_only_after_explicit_table1_choice():
    values = {
        "sp16_applicability_census": _census(
            ["section_compression", "member_compression_stability", "effective_length_slenderness"]
        ),
        "ambient_N_force": -100e3,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "A_net": 2000.0,
        "A_gross": 2000.0,
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "material_safety_category": "statistical_control",
        "phi_x_sp16": 0.8,
        "phi_y_sp16": 0.7,
        "sp16_l_eff_x": 2500.0,
        "sp16_i_x": 50.0,
        "sp16_l_eff_y": 3000.0,
        "sp16_i_y": 50.0,
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "shape_group": "I_ROLLED_DSYMM",
            "dimensions": {"h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        },
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    }
    normalized = normalize_mech7_inputs(values)
    before = bind_primary_ambient_evidence(normalized)["sp16_mech7_primary_evidence"]["evidence"]
    for cid in ("section_compression", "member_compression_stability", "effective_length_slenderness"):
        assert "requires gamma_c_compression" in str(before[cid].get("reason") or "")

    normalized.update(resolve_gamma_c_compression("default_unlisted_case_note_5"))
    after = bind_primary_ambient_evidence(normalized)["sp16_mech7_primary_evidence"]["evidence"]
    for cid in ("section_compression", "member_compression_stability", "effective_length_slenderness"):
        assert after[cid]["status"] in {"PASS", "FAIL"}, (cid, after[cid])
        assert "requires gamma_c_compression" not in str(after[cid].get("reason") or "")


def test_v078_amendment6_table1_text_includes_lambda_profiles():
    text = (ROOT / "data" / "table_1_working_condition_factors.json").read_text(encoding="utf-8")
    assert "Amendments No. 1-6" in text
    assert text.count("лямбда-профилей") >= 4


def test_v078_layer_remains_in_active_descendant_chain():
    source = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    v086 = (ROOT / "streamlit_guided_ux_v086.py").read_text(encoding="utf-8")
    v085 = (ROOT / "streamlit_guided_ux_v085.py").read_text(encoding="utf-8")
    v084 = (ROOT / "streamlit_guided_ux_v084.py").read_text(encoding="utf-8")
    v083 = (ROOT / "streamlit_guided_ux_v083.py").read_text(encoding="utf-8")
    v082 = (ROOT / "streamlit_guided_ux_v082.py").read_text(encoding="utf-8")
    v081 = (ROOT / "streamlit_guided_ux_v081.py").read_text(encoding="utf-8")
    v080 = (ROOT / "streamlit_guided_ux_v080.py").read_text(encoding="utf-8")
    v079 = (ROOT / "streamlit_guided_ux_v079.py").read_text(encoding="utf-8")

    # Historical v0.78 must remain reachable through the current production
    # entrypoint.  Do not pin an old layer as the direct streamlit_app import.
    assert "from streamlit_guided_ux_v086 import install as _install_guided_ux" in source
    assert "import streamlit_guided_ux_v085 as _v085" in v086
    assert "_v085.install(core)" in v086
    assert "import streamlit_guided_ux_v084 as _v084" in v085
    assert "_v084.install(core)" in v085
    assert "import streamlit_guided_ux_v083 as _v083" in v084
    assert "import streamlit_guided_ux_v082 as _v082" in v083
    assert "import streamlit_guided_ux_v081 as _v081" in v082
    assert "import streamlit_guided_ux_v080 as _v080" in v081
    assert "import streamlit_guided_ux_v079 as _v079" in v080
    assert "import streamlit_guided_ux_v078 as _v078_ui" in v079
    assert "install_gamma_c_registry" in v079
