from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.39_stage_n10.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def _ds(d, dataset_id):
    return next(x for x in d["datasets"] if x["id"] == dataset_id)


def test_n10_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph" / "dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_n10_dag_identity_counts_and_frozen_n9_parent():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-39_stage_n10"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (729, 635, 1072, 36)
    assert _n(d, "SP16_N9_R_RELEASE_GATE")
    assert _n(d, "SP16_N10_R_RELEASE_GATE")
    e = next(x for x in d["edges"] if x["id"] == "N10_E_001")
    assert e["from_node_id"] == "SP16_N9_R_RELEASE_GATE"
    assert e["label"] == "N1-N9 frozen"


def test_n10_table37_is_materialized_without_interpolation_and_exact_values():
    ds = _ds(_d(), "SP16_N10_TABLE37")
    assert ds["interpolation"] == {"method": "none", "extrapolation": "forbidden"}
    rows = ds["storage"]["rows"]
    cf = {r["case"]: r["value"] for r in rows if r["category"] == "connection_form"}
    assert cf == {
        "no_z_direction_stress": -25.0,
        "symmetric_fillet": -10.0,
        "intermediate_deposited_layer": -5.0,
        "ordinary_tee_fillet": 0.0,
        "tee_full_or_partial_penetration": 3.0,
        "fillet_near_free_plate_edge": 5.0,
        "corner_full_penetration": 8.0,
    }
    analytic = {(r["category"], r["expression"]) for r in rows if "expression" in r}
    assert analytic == {("plate_thickness", "0.2*S"), ("weld_leg", "0.3*a")}
    assert {r["case"]: r["value"] for r in rows if r["category"] == "restraint"} == {
        "low_free_shrinkage": 0.0, "medium": 3.0, "high": 5.0
    }


def test_n10_current_clause13_policy_has_four_factors_and_literal_boundaries():
    rows = _ds(_d(), "SP16_N10_CLAUSE13_POLICY")["storage"]["rows"]
    by = {r["policy"]: r for r in rows}
    assert by["clause_13_1_factor_groups"]["value"] == [
        "low_temperature", "dynamic_or_vibratory_loads", "high_local_stresses", "transverse_stress_concentrators"
    ]
    assert by["enhanced_ndt_trigger"] == {"policy":"enhanced_ndt_trigger","operator":"gt","value":"0.4*Ry"}
    assert by["cover_plate_flank_weld_termination_each_side_mm"]["value"] == 25.0
    assert by["static_through_thickness_compression_multiplier"]["value"] == 0.5
    assert by["dynamic_or_vibratory_through_thickness_multiplier"]["value"] == 1.1


def test_n10_eq174_node_and_z_quality_route_are_explicit():
    d = _d()
    eq = _n(d, "SP16_N10_C_EQ174")
    assert eq["calculation_spec"]["expression"] == "psi_zf + psi_zt + psi_zsh + psi_zj + psi_zs"
    assert {b["quantity_id"] for b in eq["calculation_spec"]["bindings"]} == {
        "sp16_n10_psi_zf","sp16_n10_psi_zt","sp16_n10_psi_zsh","sp16_n10_psi_zj","sp16_n10_psi_zs"
    }
    zr = _n(d, "SP16_N10_K_Z_ROUTE")
    assert zr["fallback_behavior"] == "unsupported"
    assert {r["output_value"] for r in zr["classification_rules"]} == {"Z15","Z25","Z35"}
    assert any(r["output_value"] == "Z35" and "15.9.10" in r["label"] for r in zr["classification_rules"])


def test_n10_release_gate_requires_general_and_external_evidence_and_conditional_risk_outputs():
    n = _n(_d(), "SP16_N10_R_RELEASE_GATE")
    req = {x["quantity_id"]: x["required"] for x in n["consumes"]}
    assert req == {
        "sp16_n10_general_prevention_status": True,
        "sp16_n10_psi_zr": False,
        "sp16_n10_required_z_group": False,
        "sp16_n10_external_gate_status": True,
    }
