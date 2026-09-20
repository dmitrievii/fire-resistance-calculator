from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireDAGModel
from standard_core.report_metadata import (
    ACTIVE_REPORT_METADATA_FILENAME,
    report_metadata_for_model,
    report_spec_for_node,
)


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def test_active_report_metadata_is_bound_to_exact_frozen_graph_and_does_not_mutate_it():
    root = Path(__file__).resolve().parents[1]
    model = FireDAGModel.load(root / "normative_graph" / ACTIVE_DAG)
    before_graph = json.dumps(model.graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    before_sha = model.graph_sha256

    metadata = report_metadata_for_model(model)
    spec10 = report_spec_for_node(model, "SP554_C_10_GOV")
    spec11 = report_spec_for_node(model, "SP554_C_11_GOV")

    after_graph = json.dumps(model.graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert metadata["revision_id"] == "v0.3.71_REPORT_META1"
    assert metadata["base_graph_sha256"] == before_sha
    assert before_sha == "49228df2c374fdaf7db1924be580f14919d0195290d59cbc433def1862306d68"
    assert before_graph == after_graph
    assert model.graph_sha256 == before_sha
    assert spec10["governing_quantity_id"] == "gamma_T_bending_governing"
    assert spec10["governing_scope"] == "sp554_section_10_bending_gamma_T"
    assert spec11["governing_quantity_id"] == "gamma_T_nm_governing"
    assert spec11["governing_scope"] == "sp554_section_11_axial_bending_gamma_T"


def test_report_metadata_sidecar_contains_no_execution_mutation_fields():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "normative_graph" / ACTIVE_REPORT_METADATA_FILENAME).read_text(encoding="utf-8"))
    forbidden = {
        "calculation_spec",
        "check_spec",
        "lookup_spec",
        "classification_rules",
        "applicability",
        "consumes",
        "produces",
        "edges",
        "quantities",
        "datasets",
    }
    for node_id, spec in payload["node_report_specs"].items():
        assert forbidden.isdisjoint(spec), node_id
    assert payload["execution_semantics_changed"] is False


def test_sidecar_sha_mismatch_fails_closed(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    dag = root / "normative_graph" / ACTIVE_DAG
    local_dag = tmp_path / ACTIVE_DAG
    local_dag.write_bytes(dag.read_bytes())
    payload = json.loads((root / "normative_graph" / ACTIVE_REPORT_METADATA_FILENAME).read_text(encoding="utf-8"))
    payload["base_graph_sha256"] = "0" * 64
    (tmp_path / ACTIVE_REPORT_METADATA_FILENAME).write_text(json.dumps(payload), encoding="utf-8")

    model = FireDAGModel.load(local_dag)
    with pytest.raises(ValueError, match="base_graph_sha256"):
        report_metadata_for_model(model)
