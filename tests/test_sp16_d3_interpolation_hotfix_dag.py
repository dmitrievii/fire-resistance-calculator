import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.45_sp16_d3_interpolation_hotfix.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def test_d3_interpolation_hotfix_dag_schema_and_identity():
    schema = json.loads((ROOT / "normative_graph" / "dag_schema.json").read_text(encoding="utf-8"))
    d = _d()
    jsonschema.Draft202012Validator(schema).validate(d)
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-45_sp16_d3_interpolation_hotfix"
    assert len(d["quantities"]) == 748
    assert len(d["nodes"]) == 657
    assert len(d["edges"]) == 1108


def test_all_d3_lookup_nodes_use_bilinear_no_extrapolation_policy():
    nodes = {n["id"]: n for n in _d()["nodes"]}
    for node_id in ("SP16_L_D3_PHI_E", "SP16_L_D3_PHI_EX", "SP16_L_D3_PHI_EY"):
        interp = nodes[node_id]["lookup_spec"]["interpolation"]
        assert interp["method"] == "bilinear"
        assert interp["extrapolation"] == "forbidden"
        assert "NormCAD" in interp["standard_rule_note"]


def test_n5_policy_recognizes_bilinear_interpolation_status():
    nodes = {n["id"]: n for n in _d()["nodes"]}
    rules = nodes["SP16_N5_K_D3_POLICY"]["classification_rules"]
    assert any(r["output_value"] == "bilinear_interpolated" for r in rules)
