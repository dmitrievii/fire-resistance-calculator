from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG_PATH = ROOT / "normative_graph/dag_v0.3.33_stage_n4.json"


def _dag() -> dict:
    return json.loads(DAG_PATH.read_text(encoding="utf-8"))


def _node(d: dict, node_id: str) -> dict:
    return next(n for n in d["nodes"] if n["id"] == node_id)


def test_n4_dag_validates_against_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_dag())


def test_n4_dag_identity_and_parent_content_retained():
    d = _dag()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-33_stage_n4"
    assert _node(d, "SP16_N3_C_EQ7A")
    assert _node(d, "SP16_N4_C_EQ41")


def test_n4_current_annex_zh3_uses_design_Ry_not_Ryn():
    n = _node(_dag(), "SP16_N4_C_LTB_PHI1_J3_RY")
    assert n["calculation_spec"]["expression"] == "psi*(Iy/Ix)*(h/lef)^2*(E/Ry)"
    bindings = {b["variable"]: b["quantity_id"] for b in n["calculation_spec"]["bindings"]}
    assert bindings["Ry"] == "Ry_annex"
    assert "Ryn" not in bindings


def test_n4_current_monosymmetric_annex_zh_nodes_use_Ry():
    d = _dag()
    for node_id in ("SP16_N4_C_LTB_PHI1_MONO_J6_RY", "SP16_N4_C_LTB_PHI2_MONO_J7_RY"):
        n = _node(d, node_id)
        assert "E/Ry" in n["calculation_spec"]["expression"]
        assert any(b["variable"] == "Ry" and b["quantity_id"] == "Ry_annex" for b in n["calculation_spec"]["bindings"])


def test_n4_eq61_expression_matches_current_sp16():
    n = _node(_dag(), "SP16_N4_C_EQ61_CURRENT")
    assert n["calculation_spec"]["expression"] == "(af*r+0.25-0.0833/r^2)/(af+0.167)"


def test_n4_eq92_has_lambda_a_squared():
    n = _node(_dag(), "SP16_N4_C_EQ92_CURRENT")
    assert n["calculation_spec"]["expression"] == "psi*(1.24+0.476*mu1)*Ry/(la^2)"


def test_n4_guided_strength_route_is_explicit_classification():
    n = _node(_dag(), "SP16_N4_K_STRENGTH_ROUTE")
    assert n["node_type"] == "classification"
    assert n["fallback_behavior"] == "error"
    outputs = {rule["output_value"] for rule in n["classification_rules"]}
    assert {"eq41", "eq50", "specialized"} <= outputs
