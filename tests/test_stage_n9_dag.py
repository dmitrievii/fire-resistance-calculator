from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.38_stage_n9.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def test_n9_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph" / "dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_n9_dag_identity_counts_and_frozen_n8_parent():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-38_stage_n9"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (714, 629, 1066, 34)
    assert _n(d, "SP16_N8_R_RELEASE_GATE")
    assert _n(d, "SP16_N9_R_RELEASE_GATE")
    e = next(x for x in d["edges"] if x["id"] == "N9_E_001")
    assert e["from_node_id"] == "SP16_N8_R_RELEASE_GATE"
    assert e["label"] == "N1-N8 frozen"


def test_n9_table35_dataset_has_exact_printed_values_and_no_interpolation():
    d = _d()
    ds = next(x for x in d["datasets"] if x["id"] == "SP16_N9_TABLE35")
    assert ds["interpolation"]["method"] == "none"
    assert ds["interpolation"]["extrapolation"] == "forbidden"
    rows = ds["storage"]["rows"]
    bins = [x for x in rows if "upper_inclusive" in x]
    assert [(x["upper_inclusive"], x["group_1"], x["group_2"]) for x in bins] == [
        (420.0,120.0,100.0),(440.0,128.0,106.0),(520.0,132.0,108.0),(580.0,136.0,110.0),(675.0,145.0,116.0)
    ]
    constants = {x["group"]: x["all_steel_rv"] for x in rows if "group" in x}
    assert constants == {3:90.0,4:75.0,5:60.0,6:45.0,7:36.0,8:27.0}


def test_n9_table36_and_annex_k_datasets_are_materialized():
    d = _d()
    t36 = next(x for x in d["datasets"] if x["id"] == "SP16_N9_TABLE36")
    assert len(t36["storage"]["rows"]) == 4
    assert {x["formula"] for x in t36["storage"]["rows"]} == {"2.5/(1.5-rho)","2.0/(1.2-rho)","1.0/(1.0-rho)","2.0/(1.0-rho)"}
    k1 = next(x for x in d["datasets"] if x["id"] == "SP16_N9_TABLE_K1")
    assert len(k1["storage"]["rows"]) == 35
    assert {x["group"] for x in k1["storage"]["rows"]} == set(range(1,9))


def test_n9_change6_exclusion_of_12_1_3_is_explicit_not_a_formula_node():
    d = _d()
    ds = next(x for x in d["datasets"] if x["id"] == "SP16_N9_CLAUSE1213_CHANGE6")
    assert ds["storage"]["rows"] == [{"status":"excluded_change6_2025_01_10"}]
    n = _n(d, "SP16_N9_K_CHANGE6_1213")
    assert "No low-cycle equation is invented" in n["notes"]["normative_warning"]


def test_n9_release_gate_consumes_route_external_and_change6_status():
    n = _n(_d(), "SP16_N9_R_RELEASE_GATE")
    q = {x["quantity_id"] for x in n["consumes"]}
    assert q == {"sp16_n9_route_policy","sp16_n9_external_gate_status","sp16_n9_clause1213_status"}
