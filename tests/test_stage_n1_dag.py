from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAG = json.loads((ROOT / "normative_graph/dag_v0.3.30_stage_n1.json").read_text(encoding="utf-8"))


def _node(node_id: str):
    return next(x for x in DAG["nodes"] if x["id"] == node_id)


def _dataset(dataset_id: str):
    return next(x for x in DAG["datasets"] if x["id"] == dataset_id)


def test_n1_dag_material_route_maps_tube_and_bar_to_v3():
    n = _node("SP16_K_MATERIAL_ROUTE")
    mapped = {}
    for r in n["classification_rules"]:
        w = r["when"]
        if w["type"] == "comparison":
            mapped[w["value"]] = r["output_value"]
    assert mapped["tube"] == "V3"
    assert mapped["bar_rolled"] == "V3"
    assert mapped["plate_sheet_strip"] == "V3"
    assert mapped["parallel_flange_i"] == "V4"
    assert mapped["shaped_rolled"] == "V5"
    assert mapped["other"] == "external"


def test_n1_dag_v3_restores_c355_100_160_and_aliases():
    rows = _dataset("SP16_TABLE_V3_RYN")["storage"]["rows"]
    c355 = [r for r in rows if r["steel_grade"] == "С355" and r["thickness_interval"] == {"min_mm": 100, "max_mm": 160, "min_inclusive": False, "max_inclusive": True}]
    assert len(c355) == 1
    assert (c355[0]["Ryn_MPa"], c355[0]["Run_MPa"], c355[0]["Ry_MPa"], c355[0]["Ru_MPa"]) == (295,470,285,460)
    for grade in ("С355-1", "С355-К"):
        assert len([r for r in rows if r["steel_grade"] == grade]) == 3


def test_n1_dag_strength_lookups_expose_full_annex_row():
    for nid in ("SP16_L_RYN_V3", "SP16_L_RYN_V4", "SP16_L_RYN_V5"):
        n = _node(nid)
        assert [x["quantity_id"] for x in n["produces"]] == ["fy_norm", "fu_norm", "Ry_annex", "Ru_annex"]
        outputs = {x["dataset_field"]: x["quantity_id"] for x in n["lookup_spec"]["output_bindings"]}
        assert outputs == {"Ryn_MPa":"fy_norm","Run_MPa":"fu_norm","Ry_MPa":"Ry_annex","Ru_MPa":"Ru_annex"}


def test_n1_dag_b1_and_table2_table3_nodes_are_materialized():
    ds = _dataset("SP16_B1_E")
    row = ds["storage"]["rows"][0]
    assert row == {"material":"rolled_steel","E_norm":206000.0,"G_norm":79000.0,"steel_density":7850.0,"steel_linear_expansion":1.2e-5,"steel_poisson_ratio":0.3}
    ids = {n["id"] for n in DAG["nodes"]}
    assert {"SP16_L_GAMMA_M","SP16_C_GAMMA_U","SP16_C_RY_TABLE2","SP16_C_RU_TABLE2","SP16_C_RS_TABLE2"} <= ids
