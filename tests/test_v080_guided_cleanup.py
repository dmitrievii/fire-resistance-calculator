from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.sp16_mech7_v075_graph_overlay import (
    STATE_NODE_ID,
    build_model as build_v075_model,
)
from standard_core.sp16_mech7_v076_graph_overlay import build_model as build_v076_model
from standard_core.sp16_mech7_v078_gamma_c import INPUT_QID as GAMMA_CASE_QID
from standard_core.sp16_mech7_v078_graph_overlay import INPUT_NODE_ID as GAMMA_INPUT_NODE_ID
from standard_core.sp16_mech7_v080_guided_cleanup_overlay import (
    GRAPH_SUFFIX,
    LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES,
    build_model,
)
from streamlit_guided_ux_v080 import _reuse_gamma_c_case

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    return build_model(build_v076_model(build_v075_model(base)))


def test_v080_retires_legacy_scalar_lambda_without_axis_alias():
    model = _active_model()
    assert str(model.graph["graph_id"]).endswith(GRAPH_SUFFIX)
    assert "SP16_C_LAMBDA" in model.nodes
    assert LEGACY_SCALAR_EFFECTIVE_LENGTH_NODES == {"SP16_C_LAMBDA"}

    incoming_navigation = [
        edge
        for edge in model.graph["edges"]
        if edge.get("edge_type") in {"control", "branch", "handoff"}
        and edge.get("to_node_id") == "SP16_C_LAMBDA"
    ]
    assert incoming_navigation == []

    excluded = set(model.presentation_policy.get("guided_excluded_nodes") or [])
    assert "SP16_C_LAMBDA" in excluded

    # The replacement contract remains explicitly two-axis. v0.80 must not
    # collapse either canonical axis back into the old scalar l_eff contract.
    state = model.nodes[STATE_NODE_ID]
    produced = {row.get("quantity_id") for row in state.get("produces", [])}
    assert {"sp16_l_eff_z", "sp16_l_eff_y", "sp16_lambda_z_geom", "sp16_lambda_y_geom"} <= produced


def test_v080_reuses_only_exact_previous_table1_case():
    class FakeSession:
        current_node_id = GAMMA_INPUT_NODE_ID

        def __init__(self, values):
            self.values = dict(values)
            self.submitted = []

        def plain_values(self):
            return dict(self.values)

        def submit(self, payload, *, provenance=None):
            self.submitted.append((payload, provenance))
            self.current_node_id = "NEXT"

    case_id = "2_multistorey_columns_height_le_150m"
    exact = FakeSession({GAMMA_CASE_QID: case_id, "gamma_c_compression": 0.95})
    assert _reuse_gamma_c_case(exact) is True
    assert exact.submitted[0][0] == case_id
    assert exact.submitted[0][1]["rule"] == "exact reuse only; no inference from numeric gamma_c"

    # Migration may reach a new question before replay gets back to the old
    # Table-1 row. Retain the exact user-authored case id without injecting it
    # into quantity state early; consume it only when the same node is reached.
    retained = FakeSession({"gamma_c_compression": 0.95})
    setattr(retained, "_v080_retained_gamma_c_case_id", case_id)
    assert _reuse_gamma_c_case(retained) is True
    assert retained.submitted[0][0] == case_id
    assert not hasattr(retained, "_v080_retained_gamma_c_case_id")

    # A numeric gamma alone is not a unique normative classification and must
    # never be reverse-mapped to a Table-1 case.
    numeric_only = FakeSession({"gamma_c_compression": 0.95})
    assert _reuse_gamma_c_case(numeric_only) is False
    assert numeric_only.submitted == []

    invalid = FakeSession({GAMMA_CASE_QID: "not_a_table1_case"})
    assert _reuse_gamma_c_case(invalid) is False
    assert invalid.submitted == []


def test_v080_entrypoint_preserves_v079_installer_chain():
    entrypoint = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    v080 = (ROOT / "streamlit_guided_ux_v080.py").read_text(encoding="utf-8")
    assert "from streamlit_guided_ux_v080 import install as _install_guided_ux" in entrypoint
    assert "import streamlit_guided_ux_v079 as _v079" in v080
    assert "_v079.install(core)" in v080
    assert "resolve_gamma_c_compression(value)" in v080
