from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.40_fire_d1.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def test_fire_d1_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_fire_d1_dag_identity_counts_and_sha_are_frozen():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-40_fire_d1"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (732, 637, 1075, 36)
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == "1def1f58d0caa0f387083abeef8651e54fd03eb27117b56ff7325d9410ba5260"


def test_fire_d1_source_hashes_are_locked_to_current_sp554_and_current_sp16():
    d = _d()
    standards = {s["id"]: s for s in d["standards"]}
    assert standards["SP554_2026"]["source_file"]["sha256"] == "86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3"
    assert standards["SP16_2017"]["source_file"]["sha256"] == "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def test_fire_d1_handoff_is_explicit_and_tied_to_frozen_n7_and_cumulative_parent():
    d = _d()
    handoff = _n(d, "SP554_FIRE_D1_H_CURRENT_SP16_MEMBER_MECHANICS")
    assert handoff["node_type"] == "standard_handoff"
    assert handoff["target_standard_id"] == "SP16_2017"
    assert set(handoff["required_output_quantity_ids"]) == {
        "fire_d1_sp16_member_mechanics_ready",
        "fire_d1_normative_strength_basis_guard",
    }
    e1 = next(e for e in d["edges"] if e["id"] == "FIRE_D1_E_001")
    assert e1["from_node_id"] == "SP16_N7_R_RELEASE_GATE"
    assert e1["to_node_id"] == handoff["id"]
    assert e1["label"] == "N1-N7 frozen fire-mechanics dependencies"
    e2 = next(e for e in d["edges"] if e["id"] == "FIRE_D1_E_002")
    assert e2["from_node_id"] == "SP16_N10_R_RELEASE_GATE"


def test_fire_d1_closure_check_guards_member_mechanics_and_normative_strength_basis():
    d = _d()
    check = _n(d, "SP554_FIRE_D1_Q_MEMBER_MECHANICAL_CLOSURE")
    assert check["check_spec"]["expression"] == (
        "fire_d1_sp16_member_mechanics_ready and fire_d1_normative_strength_basis_guard"
    )
    assert check["result_quantity_id"] == "fire_d1_member_mechanical_closure"
