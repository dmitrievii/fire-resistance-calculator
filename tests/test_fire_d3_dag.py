from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.42_fire_d3.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def test_fire_d3_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_fire_d3_dag_identity_counts_and_sha_are_frozen():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-42_fire_d3"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (740, 647, 1096, 38)
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == "ec4f36f7a61de834d7dd4ae69e8f3f7e667f392c0edd4c236431a66581ab7dd3"


def test_fire_d3_dag_preserves_fire_d2_handoff_and_section12_routes():
    d = _d()
    handoff = _n(d, "SP554_FIRE_D3_C_D2_TCR_HANDOFF")
    assert any(x["quantity_id"] == "fire_d2_critical_temperature_c" for x in handoff["consumes"])
    assert _n(d, "SP554_C_UNPROTECTED_STEP_12_1_12_4")["calculation_spec"]["expression"].startswith("unprotected_step_time")
    assert "confirmed_errata" in _n(d, "SP554_C_12_5_1D_PERFORMANCE_DATASET")["calculation_spec"]["expression"]
    assert _n(d, "SP554_C_12_10_PROTECTED_TIME")["calculation_spec"]["expression"].startswith("protected_time_12_10_linear")


def test_fire_d3_dag_explicitly_does_not_overclaim_full_section12_scope():
    d = _d()
    flag = _n(d, "SP554_FIRE_D3_C_FULL_SCOPE_FLAG")
    assert flag["calculation_spec"]["expression"] == "false"
    assert "moisture" in (flag["notes"]["limitations"] or "").lower() or "W>0" in (flag["notes"]["limitations"] or "")
