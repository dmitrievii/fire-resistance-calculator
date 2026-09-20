from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.43_fire_d31.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def test_fire_d31_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_fire_d31_dag_identity_counts_and_sha_are_frozen():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-43_fire_d31"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (743, 651, 1100, 38)
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == "5b19204e3ec29a7289bdbe8a483122c8e4b0c63b5fd0c2aad677bc9529a7892f"


def test_fire_d31_dag_marks_sp554_as_enacted_but_retains_locked_source_provenance():
    d = _d()
    sp = next(x for x in d["standards"] if x["id"] == "SP554_2026")
    assert sp["designation"] == "СП 554.1311500.2026"
    assert sp["status"] == "approved"
    assert sp["source_file"]["sha256"] == "86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3"
    assert "pre-enactment" in sp["notes"]


def test_fire_d31_reconciliation_closes_classification_without_overclaiming_literal_tphi_runtime():
    d = _d()
    assert _n(d, "SP554_FIRE_D31_C_FULL_SCOPE_RECONCILIATION")["calculation_spec"]["expression"] == "true"
    assert _n(d, "SP554_FIRE_D31_C_WET_EMBEDDED_PROPERTIES_ROUTE")["calculation_spec"]["expression"] == "true"
    assert _n(d, "SP554_FIRE_D31_C_LITERAL_TPHI_RECURRENCE_FLAG")["calculation_spec"]["expression"] == "false"
    assert _n(d, "SP554_FIRE_D3_C_FULL_SCOPE_FLAG")["calculation_spec"]["expression"] == "false"
    result = _n(d, "SP554_FIRE_D31_R_SECTION12_RECONCILIATION")
    assert set(result["result_quantity_ids"]) == {
        "fire_d3_full_section12_scope_closed",
        "fire_d31_section12_full_scope_reconciled",
        "fire_d31_wet_embedded_properties_route_closed",
        "fire_d31_literal_t_phi_recurrence_closed",
    }
