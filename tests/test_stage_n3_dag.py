from __future__ import annotations
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = ROOT / "normative_graph/dag_v0.3.32_stage_n3.json"
DAG = json.loads(DAG_PATH.read_text(encoding="utf-8"))


def _node(node_id: str):
    return next(x for x in DAG["nodes"] if x["id"] == node_id)


def test_n3_dag_schema_and_identity():
    import fastjsonschema
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    fastjsonschema.compile(schema)(DAG)
    assert DAG["graph_id"] == "sp16_sp554_dag_v0-3-32_stage_n3"


def test_n3_lambda_bar_uses_design_ry_not_sp554_normative_strength():
    n = _node("SP16_N3_C_LBAR_RY")
    consumed = {x["quantity_id"] for x in n["consumes"]}
    assert "Ry_annex" in consumed
    assert "fy_norm" not in consumed
    assert "Ry" in n["calculation_spec"]["expression"]


def test_n3_current_equation_7a_and_literal_gamma_res_390_rule_are_present():
    eq7a = _node("SP16_N3_C_EQ7A")
    assert any(r.get("formula_ref") == "(7a)" for r in eq7a["normative_refs"])
    g390 = _node("SP16_N3_C_GAMMA_RES_390")
    expressions = [c["expression"] for c in g390["calculation_spec"]["cases"]]
    assert "0.2*lbar+0.9" in expressions


def test_n3_table8_route_and_all_six_current_formulas_are_atomic_nodes():
    route = _node("SP16_N3_K_TABLE8_ROUTE")
    assert len(route["classification_rules"]) == 6
    assert route["applicability"] == {"type":"comparison","quantity_id":"sp16_n3_panel_count","operator":"gte","value":6}
    for eq in range(12, 18):
        n = _node(f"SP16_N3_C_EQ{eq}")
        assert any(r.get("formula_ref") == f"({eq})" for r in n["normative_refs"])
        assert n["applicability"]["quantity_id"] == "sp16_n3_table8_route"
        assert n["applicability"]["value"] == f"eq{eq}"


def test_n3_phi_node_preserves_classified_source_boundary_ambiguity():
    n = _node("SP16_N3_C_PHI_FINAL")
    warning = n["notes"]["normative_warning"]
    assert "SOURCE_AMBIGUITY" in warning
    assert "3.8/4.4/5.8" in warning


def test_n3_qfic_formula_18_is_explicit():
    n = _node("SP16_N3_C_EQ18_QFIC")
    assert n["calculation_spec"]["expression"] == "7.15e-6*(2330-E/Ry)*N/phi"
    assert any(r.get("formula_ref") == "(18)" for r in n["normative_refs"])
