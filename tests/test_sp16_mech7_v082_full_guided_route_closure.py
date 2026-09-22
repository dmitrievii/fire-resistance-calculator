from __future__ import annotations

import math
from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import build_model as build_v076_model
from standard_core.sp16_mech7_v078_graph_overlay import build_model as build_v078_model
from standard_core.sp16_mech7_v079_guided_route_overlay import build_model as build_v079_model
from standard_core.sp16_mech7_v080_guided_cleanup_overlay import build_model as build_v080_model
from standard_core.sp16_mech7_v081_end_to_end_overlay import build_model as build_v081_model
from standard_core.sp16_mech7_v082_guided_route_overlay import (
    AMBIENT_B_DECISION_NODE_ID,
    AMBIENT_B_INPUT_NODE_ID,
    AMBIENT_LOAD_NODE_ID,
    GAMMA_E_NODE_ID,
    GRAPH_SUFFIX,
    build_model,
)
from standard_core.sp16_mech7_v082_runtime import gamma_e_compression_8_6, install_registry_remediation
from streamlit_guided_ux_v082 import _exact_gamma_case

ROOT = Path(__file__).resolve().parents[1]


def _model_and_registry():
    app = FireUI1Application.from_package_root(ROOT)
    # Production installs these graph overlays cumulatively.  Do not apply
    # v0.82 directly to the frozen v0.3.70 graph: that was the old false-positive
    # test setup and does not match the deployed installer chain.
    model = build_v075_model(app.model)
    model = build_v076_model(model)
    model = build_v078_model(model)
    model = build_v079_model(model)
    model = build_v080_model(model)
    model = build_v081_model(model)
    model = build_model(model)
    registry = install_registry_remediation(app.service.registry)
    return model, registry


def test_v082_graph_inlines_ambient_b_and_retires_duplicate_prompt():
    model, _ = _model_and_registry()
    assert GRAPH_SUFFIX in model.graph["graph_id"]
    nodes = {row["id"]: row for row in model.graph["nodes"]}
    outputs = {row["quantity_id"] for row in nodes[AMBIENT_LOAD_NODE_ID]["produces"]}
    assert "ambient_B_bimoment" in outputs
    assert AMBIENT_B_DECISION_NODE_ID in model.presentation_policy["guided_excluded_nodes"]
    assert AMBIENT_B_INPUT_NODE_ID in model.presentation_policy["guided_excluded_nodes"]
    assert all(edge.get("to_node_id") not in {AMBIENT_B_DECISION_NODE_ID, AMBIENT_B_INPUT_NODE_ID} for edge in model.graph["edges"])


def test_v082_ambient_load_submission_carries_signed_b_without_second_card():
    model, registry = _model_and_registry()
    s = GuidedCalculationSession(model, entry_node_id=AMBIENT_LOAD_NODE_ID, registry=registry)
    payload = {
        "ambient_load_combination": {"schema": "test", "kind": "ambient", "B_kNm2": -2.5},
        "ambient_N_force": -100e3,
        "ambient_M_x": 5e6,
        "ambient_M_y": 0.0,
        "ambient_Q_x": 0.0,
        "ambient_Q_y": 0.0,
        "ambient_T_torsion": 0.0,
        "ambient_B_bimoment": -2.5e9,
    }
    s.submit(payload)
    assert s.plain_values()["ambient_B_bimoment"] == -2.5e9
    assert AMBIENT_B_DECISION_NODE_ID not in s.visited_node_ids
    assert AMBIENT_B_INPUT_NODE_ID not in s.visited_node_ids
    # Non-zero B legitimately schedules the MECH5 pointwise recovery before
    # the census; the UX invariant here is only that no second B authoring card
    # is visited.
    assert s.current_node_id not in {AMBIENT_B_DECISION_NODE_ID, AMBIENT_B_INPUT_NODE_ID}


def test_v082_gamma_e_is_exact_sp554_8_6_producer_on_governing_axis():
    values = {
        "N_force": -400e3,
        "sp16_v081_governing_stability_axis": "y",
        "sp16_l_eff_z": 2100.0,
        "sp16_l_eff_y": 3000.0,
        "sp16_i_z": 120.0,
        "sp16_i_y": 55.0,
        "A_gross": 7600.0,
        "E_norm": 206000.0,
    }
    result = gamma_e_compression_8_6(values)
    j_y = values["A_gross"] * values["sp16_i_y"] ** 2
    expected = abs(values["N_force"]) * values["sp16_l_eff_y"] ** 2 / (math.pi ** 2 * values["E_norm"] * j_y)
    assert math.isclose(result["gamma_e_compression"], expected, rel_tol=1e-12, abs_tol=0.0)


def test_v082_gamma_e_node_is_calculated_not_external_missing_input():
    model, registry = _model_and_registry()
    nodes = {row["id"]: row for row in model.graph["nodes"]}
    node = nodes[GAMMA_E_NODE_ID]
    assert node["node_type"] == "calculation"
    assert node["calculation_spec"]["algorithm_id"] == "sp554_v082_gamma_e_8_6_from_qualified_sp16_axis_v1"
    assert [row["quantity_id"] for row in node["produces"]] == ["gamma_e_compression"]
    assert registry.get(GAMMA_E_NODE_ID) is not None


def test_v082_table1_reuse_accepts_only_exact_prior_classification():
    case_id = "default_unlisted_case_note_5"
    assert _exact_gamma_case({"sp16_table1_compression_case_id": case_id}) == case_id
    assert _exact_gamma_case({"sp16_table1_compression_evidence": {"case_id": case_id, "gamma_c": 1.0}}) == case_id
    assert _exact_gamma_case({"gamma_c_compression": 1.0}) is None
