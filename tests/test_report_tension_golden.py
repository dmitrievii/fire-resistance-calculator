from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireDAGModel
from standard_core.fire_ui16_declarative import execute_declarative
from standard_core.fire_ui17_workflow import _critical_temperature_selection
from standard_core.fire_ui18_workflow import _fire_d2_to_d3_exact_tcr_handoff
from standard_core.fire_ui19_heated_perimeter import _protected_perimeter
from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir5 import build_report_ir5
from standard_core.report_metadata import report_spec_for_node


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _trace(sequence, node, inputs, outputs):
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


def _by_owner(report):
    return {block["owner_node_id"]: block for block in report["blocks"]}


def _model():
    root = Path(__file__).resolve().parents[1]
    return FireDAGModel.load(root / "normative_graph" / ACTIVE_DAG)


def _production_trace_prefix(model):
    traces = []
    seq = 0

    tension_inputs = {
        "N_force": 867_940.0,
        "A_net": 5964.0,
        "fy_norm": 245.0,
        "gamma_c_tension": 1.0,
    }
    n9 = model.nodes["SP554_C_9_1"]
    out9 = execute_declarative(model, n9, tension_inputs)
    seq += 1
    traces.append(_trace(seq, n9, tension_inputs, out9))

    ng = model.nodes["SP554_C_GAMMAT_FROM_9_1"]
    g_inputs = {"gamma_T_9_1": out9["gamma_T_9_1"]}
    outg = execute_declarative(model, ng, g_inputs)
    seq += 1
    traces.append(_trace(seq, ng, g_inputs, outg))

    nt = model.nodes["SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY"]
    t_inputs = {
        "steel_strength_group": "ordinary",
        "gamma_T_required": outg["gamma_T_required"],
        "fire_d2_temperature_governing_policy_reconciled": True,
    }
    outt = _critical_temperature_selection(t_inputs, nt)
    seq += 1
    traces.append(_trace(seq, nt, t_inputs, outt))

    nh = model.nodes["SP554_FIRE_D3_C_D2_TCR_HANDOFF"]
    h_inputs = {
        "fire_d2_critical_temperature_status": outt["fire_d2_critical_temperature_status"],
        "fire_d2_critical_temperature_c": outt["fire_d2_critical_temperature_c"],
    }
    outh = _fire_d2_to_d3_exact_tcr_handoff(h_inputs, nh)
    seq += 1
    traces.append(_trace(seq, nh, h_inputs, outh))

    np = model.nodes["SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1"]
    p_inputs = {
        "section_geometry_2d_normalized": {
            "shape_group": "i_section",
            "dimensions": {"b_mm": 152.0, "h_mm": 160.0, "tw_mm": 10.0},
        },
        "section_family": "i_section",
        "heated_exposure_configuration": "four_sides",
        "fire_protection_perimeter_mode": "contour",
        "sp554_protected_perimeter_domain_ok": True,
    }
    outp = _protected_perimeter(p_inputs, np)
    seq += 1
    traces.append(_trace(seq, np, p_inputs, outp))

    nd = model.nodes["SP554_C_DELTA_PR_PROTECTED_12_2"]
    d_inputs = {"A_gross": 5964.0, "P_heated_protected": outp["P_heated_protected"]}
    outd = execute_declarative(model, nd, d_inputs)
    seq += 1
    traces.append(_trace(seq, nd, d_inputs, outd))

    nr = model.nodes["SP554_H_REQUIRED_R"]
    r_inputs = {}
    outr = {"required_fire_resistance_min": 120.0}
    seq += 1
    traces.append(_trace(seq, nr, r_inputs, outr))

    return traces, out9, outg, outt, outp, outd


def test_central_tension_golden_uses_frozen_9_1_expression_without_hidden_gamma_ct():
    model = _model()
    node = model.nodes["SP554_C_9_1"]
    expression = node["calculation_spec"]["expression"]
    bindings = [row["quantity_id"] for row in node["calculation_spec"]["bindings"]]

    assert expression == "abs(N_force)/(A_net*fy_norm*gamma_c_tension)"
    assert bindings == ["N_force", "A_net", "fy_norm", "gamma_c_tension"]
    assert "gamma_ct" not in expression
    assert "gamma_ct" not in bindings

    outputs = execute_declarative(
        model,
        node,
        {"N_force": 867_940.0, "A_net": 5964.0, "fy_norm": 245.0, "gamma_c_tension": 1.0},
    )
    assert outputs["gamma_T_9_1"] == pytest.approx(0.5939993703718912)


def test_gamma_ct_is_explicit_but_automatic_composition_is_fail_closed_by_frozen_dag():
    model = _model()
    gamma_node = model.nodes["SP554_C_GAMMA_CT_8_1"]
    ambiguity = model.nodes["SP554_R_GAMMA_CT_APPLICATION_INTERPRETATION_REQUIRED"]

    gamma = execute_declarative(model, gamma_node, {})
    assert gamma["gamma_ct"] == pytest.approx(1.1)
    text = " ".join(
        str(x)
        for x in (
            ambiguity.get("title"),
            ambiguity.get("notes", {}).get("engineering_meaning"),
            ambiguity.get("notes", {}).get("limitations"),
            ambiguity.get("notes", {}).get("normative_warning"),
        )
    ).lower()
    assert "1.1" in text or "1,1" in text
    assert "automatic" in text or "автомат" in text or "multiply" in text
    assert report_spec_for_node(model, ambiguity["id"])["kind"] == "WARNING"


def test_tension_golden_prefix_runs_production_gamma_t_tcr_perimeter_and_reduced_thickness():
    model = _model()
    traces, out9, outg, outt, outp, outd = _production_trace_prefix(model)

    assert outg["gamma_T_required"] == pytest.approx(out9["gamma_T_9_1"])
    assert isinstance(outt["fire_d2_critical_temperature_c"], float)
    assert outt["fire_d2_critical_temperature_c"] > 20.0
    assert outp["P_heated_protected"] == pytest.approx(0.908)
    assert outd["delta_pr_protected"] == pytest.approx(5964.0 / (0.908 * 1000.0))

    state = {
        "schema": "fire_ui_session_v1",
        "graph_id": model.graph["graph_id"],
        "graph_sha256": model.graph_sha256,
        "entry_node_id": "SP554_C_9_1",
        "current_node_id": "SP554_H_REQUIRED_R",
        "status": "AWAITING_INPUT",
        "ledger": [],
        "trace": traces,
        "branch_failures": [],
    }
    report = build_report_ir5(model, state)
    blocks = _by_owner(report)

    assert report["audit"]["report_metadata_revision_id"] == "v0.3.72_REPORT_META2_TENSION_GOLDEN"
    assert blocks["SP554_C_9_1"]["section_key"] == "critical_temperature_strength"
    assert blocks["SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY"]["section_key"] == "critical_temperature"
    assert blocks["SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1"]["section_key"] == "thermal_geometry"
    assert blocks["SP554_C_DELTA_PR_PROTECTED_12_2"]["section_key"] == "thermal_geometry"
    assert blocks["SP554_H_REQUIRED_R"]["section_key"] == "fire_resistance_requirement"

    section_keys = [row["section_key"] for row in report["sections"]]
    assert section_keys.index("fire_resistance_requirement") < section_keys.index("critical_temperature_strength")
    assert section_keys.index("critical_temperature_strength") < section_keys.index("critical_temperature")
    assert section_keys.index("critical_temperature") < section_keys.index("thermal_geometry")

    eq = build_trace_bound_equation(blocks["SP554_C_9_1"])
    assert eq is not None
    assert eq["formula_latex"] == r"\gamma_T=\frac{|N|}{A_n R_{yn}\gamma_c}"
    assert "867940" in eq["substitution_result_latex"]
    assert "5964" in eq["substitution_result_latex"]
    assert "245" in eq["substitution_result_latex"]
    assert r"\boxed{0.594}" in eq["substitution_result_latex"]
    assert "gamma_ct" not in eq["substitution_result_latex"]
    assert eq["evaluated_formula"] is False
    assert eq["converted_units"] is False
