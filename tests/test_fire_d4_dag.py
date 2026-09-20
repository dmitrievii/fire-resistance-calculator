from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.44_fire_d4.json"


def _d():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _n(d, node_id):
    return next(x for x in d["nodes"] if x["id"] == node_id)


def test_fire_d4_dag_validates_frozen_schema():
    schema = json.loads((ROOT / "normative_graph/dag_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_fire_d4_dag_identity_counts_and_sha_are_frozen():
    d = _d()
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-44_fire_d4"
    assert (len(d["quantities"]), len(d["nodes"]), len(d["edges"]), len(d["datasets"])) == (748, 657, 1108, 38)
    assert hashlib.sha256(DAG.read_bytes()).hexdigest() == "cb5143967c7503c5280283e227d6ab63fcfd305782fff2d3c26e4f1c43e5dfed"


def test_fire_d4_r_designation_is_independent_of_compliance_and_has_no_rounding():
    d = _d()
    for nid in ("SP554_C_R_DESIGNATION_UNPROTECTED", "SP554_C_R_DESIGNATION_PROTECTED"):
        node = _n(d, nid)
        consumed = {x["quantity_id"] for x in node["consumes"]}
        assert "unprotected_compliance" not in consumed
        assert "protected_compliance" not in consumed
        assert node["calculation_spec"]["rounding"]["mode"] == "none"
        assert node["applicability"]["conditions"] == [
            {"type": "comparison", "quantity_id": "fire_temperature_regime", "operator": "eq", "value": "standard"}
        ]


def test_fire_d4_required_r_is_external_and_provenance_guarded():
    d = _d()
    q = next(x for x in d["quantities"] if x["id"] == "required_fire_resistance_min")
    assert q["source_policy"]["primary_source_type"] == "EXTERNAL_STANDARD_RESULT"
    guard = _n(d, "SP554_FIRE_D4_C_REQUIRED_R_PROVENANCE_GUARD")
    assert {x["quantity_id"] for x in guard["consumes"]} == {"required_fire_resistance_min", "fire_d4_required_r_provenance"}


def test_fire_d4_closes_standard_fire_section13_but_not_nonstandard_fire():
    d = _d()
    assert _n(d, "SP554_FIRE_D4_C_13_4_INDICATOR_RUNTIME")["calculation_spec"]["expression"] == "true"
    assert _n(d, "SP554_FIRE_D4_C_NONSTANDARD_FIRE_FLAG")["calculation_spec"]["expression"] == "false"
    result = _n(d, "SP554_FIRE_D4_R_SECTION13_RUNTIME")
    assert set(result["result_quantity_ids"]) == {"fire_d4_section13_runtime_closed", "fire_d4_nonstandard_fire_runtime_closed"}
