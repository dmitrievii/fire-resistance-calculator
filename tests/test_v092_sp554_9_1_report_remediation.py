from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel
from standard_core.fire_sp554_runtime_v092 import (
    GAMMA_CT,
    TENSION_EXPRESSION,
    TENSION_FORMULA_ID,
    TENSION_FORMULA_LATEX,
    TENSION_NODE_ID,
    TENSION_TRACE_QID,
    TENSION_TRACE_SCHEMA,
    _central_tension_final,
    _central_tension_guided_final,
    install_guided_registry_remediation_v092,
)
from standard_core.fire_sp554_v092_guided_overlay import (
    GRAPH_SUFFIX,
    TENSION_ALGORITHM_ID,
    build_model,
)
from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir_v092 import build_report_ir_v092


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"

VALUES = {
    "N_force": 867_940.0,
    "A_net": 5964.0,
    "fy_norm": 245.0,
    "gamma_c_tension": 1.0,
}
EXPECTED = abs(VALUES["N_force"]) / (
    VALUES["A_net"] * VALUES["fy_norm"] * GAMMA_CT * VALUES["gamma_c_tension"]
)
LEGACY_WITHOUT_GAMMA_CT = abs(VALUES["N_force"]) / (
    VALUES["A_net"] * VALUES["fy_norm"] * VALUES["gamma_c_tension"]
)


def _active_model() -> FireDAGModel:
    return build_model(FireDAGModel.load(DAG))


def _trace(sequence: int, node: dict, inputs: dict, outputs: dict) -> dict:
    return {
        "sequence": sequence,
        "node_id": node["id"],
        "node_type": node["node_type"],
        "event_kind": "execution",
        "status": "COMPLETE",
        "inputs": dict(inputs),
        "outputs": dict(outputs),
        "selected_edge_id": None,
        "normative_refs": node.get("normative_refs") or [],
        "message": None,
    }


def _state(model: FireDAGModel, outputs: dict) -> dict:
    node = model.nodes[TENSION_NODE_ID]
    return {
        "schema": "fire_ui_session_v1",
        "graph_id": model.graph["graph_id"],
        "graph_sha256": model.graph_sha256,
        "entry_node_id": TENSION_NODE_ID,
        "current_node_id": TENSION_NODE_ID,
        "status": "AWAITING_INPUT",
        "ledger": [],
        "trace": [_trace(1, node, VALUES, outputs)],
        "branch_failures": [],
    }


def test_frozen_dag_remains_historical_but_active_v092_node_has_final_gamma_ct_formula():
    frozen = FireDAGModel.load(DAG)
    frozen_spec = frozen.nodes[TENSION_NODE_ID]["calculation_spec"]
    assert frozen_spec["expression"] == "abs(N_force)/(A_net*fy_norm*gamma_c_tension)"
    assert "gamma_ct" not in frozen_spec["formula_latex"]

    active = build_model(frozen)
    spec = active.nodes[TENSION_NODE_ID]["calculation_spec"]
    produced = {
        row["quantity_id"] for row in active.nodes[TENSION_NODE_ID]["produces"]
    }

    assert GRAPH_SUFFIX in active.graph["graph_id"]
    assert spec["algorithm_id"] == TENSION_ALGORITHM_ID
    assert spec["expression"] == TENSION_EXPRESSION
    assert spec["formula_latex"] == TENSION_FORMULA_LATEX
    assert "1.1" in spec["expression"]
    assert TENSION_TRACE_QID in produced


def test_guided_v092_9_1_uses_mandatory_gamma_ct_and_publishes_typed_trace():
    model = _active_model()
    node = model.nodes[TENSION_NODE_ID]

    registry = ExecutionRegistry()
    install_guided_registry_remediation_v092(registry)
    executor = registry.get(TENSION_NODE_ID)
    assert executor is not None
    out = executor(VALUES, node)

    assert out["gamma_T_9_1"] == pytest.approx(EXPECTED)
    assert out["gamma_T_9_1"] == pytest.approx(LEGACY_WITHOUT_GAMMA_CT / 1.1)
    assert out["gamma_T_9_1"] != pytest.approx(LEGACY_WITHOUT_GAMMA_CT)

    trace = out[TENSION_TRACE_QID]
    assert trace["schema"] == TENSION_TRACE_SCHEMA
    assert trace["formula_id"] == TENSION_FORMULA_ID
    assert trace["formula_latex"] == TENSION_FORMULA_LATEX
    assert trace["inputs"]["gamma_ct"]["value"] == pytest.approx(1.1)
    assert trace["inputs"]["gamma_ct"]["source"] == "mandatory_normative_constant"
    assert trace["result"]["value"] == pytest.approx(EXPECTED)


def test_standalone_and_guided_v092_9_1_are_numerically_and_trace_equivalent():
    model = _active_model()
    guided = _central_tension_guided_final(VALUES, model.nodes[TENSION_NODE_ID])
    candidates, gamma_e, standalone_trace = _central_tension_final(
        {"fy_norm_n_mm2": VALUES["fy_norm"]},
        {
            "N_n": VALUES["N_force"],
            "A_net_mm2": VALUES["A_net"],
            "gamma_c": VALUES["gamma_c_tension"],
        },
    )

    assert gamma_e is None
    assert candidates[0]["gamma_T_required"] == pytest.approx(guided["gamma_T_9_1"])
    assert standalone_trace["formula_id"] == guided[TENSION_TRACE_QID]["formula_id"]
    assert standalone_trace["inputs"]["gamma_ct"]["value"] == pytest.approx(1.1)
    assert standalone_trace["result"]["value"] == pytest.approx(EXPECTED)


def test_active_v092_report_renders_formula_substitution_result_with_gamma_ct():
    model = _active_model()
    outputs = _central_tension_guided_final(VALUES, model.nodes[TENSION_NODE_ID])
    report = build_report_ir_v092(model, _state(model, outputs))
    block = next(
        row for row in report["blocks"] if row["owner_node_id"] == TENSION_NODE_ID
    )
    equation = build_trace_bound_equation(block)

    assert equation is not None
    assert equation["formula_latex"] == TENSION_FORMULA_LATEX
    assert "gamma_{ct}" in equation["formula_latex"]
    assert "1.1" in equation["substitution_result_latex"]
    assert "867940" in equation["substitution_result_latex"]
    assert "5964" in equation["substitution_result_latex"]
    assert "245" in equation["substitution_result_latex"]
    assert r"\boxed{0.540}" in equation["substitution_result_latex"]
    assert equation["evaluated_formula"] is False
    assert equation["converted_units"] is False

    audit = report["audit"]
    assert audit["v092_sp554_9_1_active"] is True
    assert audit["v092_sp554_9_1_remediated_block_count"] == 1
    assert audit["v092_sp554_9_1_frozen_sidecar_formula_superseded"] is True
    assert audit["v092_sp554_9_1_engineering_values_recomputed_by_report"] is False


def test_active_v092_report_fails_closed_if_typed_9_1_trace_is_missing():
    model = _active_model()
    outputs = {"gamma_T_9_1": EXPECTED}
    with pytest.raises(ValueError, match="no typed runtime trace"):
        build_report_ir_v092(model, _state(model, outputs))
