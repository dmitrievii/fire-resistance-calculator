from __future__ import annotations

from standard_core.fire_ui0 import FireDAGModel, GuidedCalculationSession
from streamlit_optional_actions_v095 import _install_session_defaulting, _patch_graph


def _graph():
    qids = ["ambient_N_force", "ambient_M_z", "ambient_M_y", "ambient_M_x", "ambient_Q_z", "ambient_Q_y"]
    return {
        "graph_id": "test_v095_optional_actions",
        "engine_contract": {},
        "quantities": [
            {"id": qid, "data_type": "number", "name_ru": qid, "canonical_unit": "kN"}
            for qid in qids
        ],
        "nodes": [{
            "id": "ACTIONS",
            "node_type": "input",
            "owner_standard_id": "SP16_2017",
            "produces": [{"quantity_id": qid, "required": True} for qid in qids],
        }],
        "edges": [],
    }


def test_v095_action_bindings_are_optional_with_zero_default():
    patched = _patch_graph(_graph())
    bindings = patched["nodes"][0]["produces"]
    assert all(row["required"] is False for row in bindings)
    assert all(row["default_value"] == 0.0 for row in bindings)


def test_v095_n_only_submission_materializes_other_actions_as_zero():
    _install_session_defaulting()
    model = FireDAGModel(_patch_graph(_graph()))
    session = GuidedCalculationSession(model, entry_node_id="ACTIONS")
    session.submit({"ambient_N_force": -100.0})
    values = session.plain_values()
    assert values["ambient_N_force"] == -100.0
    assert values["ambient_M_z"] == 0.0
    assert values["ambient_M_y"] == 0.0
    assert values["ambient_M_x"] == 0.0
    assert values["ambient_Q_z"] == 0.0
    assert values["ambient_Q_y"] == 0.0
