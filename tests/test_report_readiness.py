from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.report_readiness import build_report_readiness


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


class DummyModel:
    def __init__(self, graph):
        self.graph = graph
        self.nodes = {row["id"]: row for row in graph["nodes"]}
        self.quantities = {row["id"]: row for row in graph["quantities"]}
        self.graph_sha256 = "dummy-sha"
        self.source_path = None


def _q(qid: str, dtype: str = "number"):
    return {
        "id": qid,
        "name_ru": qid,
        "symbol": qid,
        "data_type": dtype,
        "canonical_unit": None,
    }


def _node(node_id: str, node_type: str, outputs, *, report_spec=None):
    row = {
        "id": node_id,
        "node_type": node_type,
        "owner_standard_id": "TEST",
        "title": node_id,
        "normative_refs": [{"standard_id": "TEST", "section": "1"}],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": True} for qid in outputs],
    }
    if report_spec is not None:
        row["report_spec"] = report_spec
    return row


def test_readiness_accepts_boolean_check_and_explicit_scoped_governing_declaration():
    graph = {
        "graph_id": "ready",
        "quantities": [_q("ok", "boolean"), _q("eta")],
        "nodes": [
            _node("CHECK", "compliance_check", ["ok"]),
            _node(
                "RESULT",
                "result",
                ["eta"],
                report_spec={
                    "governing_scope": "test_scope",
                    "governing_quantity_id": "eta",
                },
            ),
        ],
    }
    report = build_report_readiness(DummyModel(graph))

    assert report["schema"] == "fire_report_readiness_v1"
    assert report["status"] == "REPORT_METADATA_COMPLETE"
    assert report["check_verdict_readiness"]["unambiguous_check_count"] == 1
    assert report["check_verdict_readiness"]["needs_explicit_verdict_count"] == 0
    assert report["governing_readiness"]["status"] == "DECLARED"
    assert report["governing_readiness"]["scopes"] == ["test_scope"]
    assert report["blocking_metadata_gap_count"] == 0
    assert report["audit"]["recomputes_engineering_values"] is False


def test_readiness_refuses_to_infer_numeric_check_verdict_or_governing_result():
    graph = {
        "graph_id": "not-ready",
        "quantities": [_q("eta")],
        "nodes": [_node("CHECK_NUMERIC", "compliance_check", ["eta"])],
    }
    report = build_report_readiness(DummyModel(graph))

    assert report["status"] == "NEEDS_DAG_METADATA"
    assert report["check_verdict_readiness"]["needs_explicit_verdict_count"] == 1
    assert report["governing_readiness"]["status"] == "NOT_DECLARED_BY_DAG"
    kinds = {row["kind"] for row in report["blocking_metadata_gaps"]}
    assert "CHECK_VERDICT_SEMANTICS" in kinds
    assert "GOVERNING_RESULT_SEMANTICS" in kinds


def test_readiness_rejects_governing_quantity_not_produced_by_declaring_node():
    graph = {
        "graph_id": "invalid-governing",
        "quantities": [_q("eta"), _q("other")],
        "nodes": [
            _node(
                "RESULT",
                "result",
                ["eta"],
                report_spec={
                    "governing_scope": "test_scope",
                    "governing_quantity_id": "other",
                },
            )
        ],
    }
    report = build_report_readiness(DummyModel(graph))

    assert report["governing_readiness"]["status"] == "NOT_DECLARED_BY_DAG"
    assert report["governing_readiness"]["invalid_declarations"][0]["quantity_id"] == "other"
    kinds = [row["kind"] for row in report["blocking_metadata_gaps"]]
    assert "INVALID_GOVERNING_DECLARATION" in kinds
    assert "GOVERNING_RESULT_SEMANTICS" in kinds


def test_active_v0370_dag_uses_v0371_report_metadata_sidecar_without_execution_changes():
    root = Path(__file__).resolve().parents[1]
    model = FireDAGModel.load(root / "normative_graph" / ACTIVE_DAG)

    report = build_report_readiness(model)

    assert report["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    assert report["graph_sha256"] == "49228df2c374fdaf7db1924be580f14919d0195290d59cbc433def1862306d68"
    assert report["node_count"] == 734
    assert report["quantity_count"] == 922
    assert report["check_verdict_readiness"]["check_node_count"] == 11
    assert report["check_verdict_readiness"]["needs_explicit_verdict_count"] == 0
    assert report["governing_readiness"]["status"] == "DECLARED"
    assert report["governing_readiness"]["declaration_count"] == 2
    assert set(report["governing_readiness"]["scopes"]) == {
        "sp554_section_10_bending_gamma_T",
        "sp554_section_11_axial_bending_gamma_T",
    }
    assert report["report_metadata"]["revision_id"] == "v0.3.71_REPORT_META1"
    assert report["report_metadata"]["base_graph_sha256"] == report["graph_sha256"]
    assert report["audit"]["executes_dag_nodes"] is False
    assert report["audit"]["reads_session_values"] is False
    assert report["audit"]["infers_numeric_pass_fail"] is False
    assert report["audit"]["infers_governing_from_names_or_values"] is False
    assert report["audit"]["report_metadata_changes_execution_graph"] is False
