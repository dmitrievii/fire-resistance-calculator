from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.41_fire_d2.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def _ds(d, dataset_id):
    return next(x for x in d["datasets"] if x["id"] == dataset_id)


def test_fire_d2_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_fire_d2_dag_identity_counts_and_sha_are_frozen():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-41_fire_d2"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (737, 643, 1088, 38)
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == "e89862567eab7bc4084c803376b8e6d479d6acd24e6666f2763a83d18c556e6e"


def test_fire_d2_section_10_and_11_governing_gamma_t_are_remediated_to_max_required():
    d = _d()
    n10 = _n(d, "SP554_C_10_GOV")
    n11 = _n(d, "SP554_C_11_GOV")
    assert n10["calculation_spec"]["expression"].startswith("max_non_null(")
    assert n11["calculation_spec"]["expression"].startswith("max_non_null(")
    assert "smallest" in n10["notes"]["normative_warning"] or "smallest" in n11["notes"]["normative_warning"]


def test_fire_d2_clause_8_6_source_literal_min_coefficient_is_diagnostic_only():
    d = _d()
    node = _n(d, "SP554_C_CTRL_COMPRESSION")
    assert node["calculation_spec"]["expression"] == "min(gamma_T_required,gamma_E_required)"
    assert "diagnostic only" in node["title"]
    assert "Do not use" in node["notes"]["normative_warning"]


def test_fire_d2_independent_appendix_b_inverse_datasets_for_strength_and_modulus_exist():
    d = _d()
    st = _ds(d, "SP554_FIRE_D2_CURVE_B1_INVERSE_GAMMA_T")
    em = _ds(d, "SP554_FIRE_D2_CURVE_B1_INVERSE_GAMMA_E")
    assert st["interpolation"]["extrapolation"] == "forbidden"
    assert em["interpolation"]["extrapolation"] == "forbidden"
    assert st["output_quantity_ids"] == ["fire_d2_critical_temperature_strength_c"]
    assert em["output_quantity_ids"] == ["fire_d2_critical_temperature_modulus_c"]
    ordinary_strength = [r for r in st["storage"]["rows"] if r["steel_group"] == "ordinary"]
    ordinary_modulus = [r for r in em["storage"]["rows"] if r["steel_group"] == "ordinary"]
    assert {r["gamma_control"] for r in ordinary_strength} >= {1.0, 0.84, 0.61, 0.2}
    assert {r["gamma_control"] for r in ordinary_modulus} >= {1.0, 0.94, 0.73, 0.43}


def test_fire_d2_critical_temperature_node_takes_min_after_independent_inversion():
    d = _d()
    node = _n(d, "SP554_FIRE_D2_C_CRITICAL_TEMPERATURE_GOV")
    assert node["calculation_spec"]["expression"] == (
        "min_non_null(fire_d2_critical_temperature_strength_c,fire_d2_critical_temperature_modulus_c)"
    )
    assert node["notes"]["normative_warning"].startswith("This node supersedes")


def test_fire_d2_runtime_closure_depends_on_fire_d1_and_explicit_reconciliation():
    d = _d()
    node = _n(d, "SP554_FIRE_D2_Q_RUNTIME_CLOSURE")
    assert node["check_spec"]["expression"] == (
        "fire_d1_member_mechanical_closure and fire_d2_temperature_governing_policy_reconciled"
    )
    result = _n(d, "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE")
    assert result["result_kind"] == "critical_temperature"
    assert result["result_quantity_ids"] == ["fire_d2_critical_temperature_c", "fire_d2_runtime_closed"]
