from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.report_metadata import report_metadata_for_model
from standard_core.sp16_mech7_v075_graph_overlay import GRAPH_SUFFIX, build_model


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def test_v075_report_metadata_remains_bound_to_frozen_source_dag():
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    overlay = build_model(base)

    assert overlay.graph["graph_id"].endswith(GRAPH_SUFFIX)
    assert overlay.graph_sha256 != base.graph_sha256
    assert overlay.source_path == base.source_path

    metadata = report_metadata_for_model(overlay)
    assert metadata["base_graph_id"] == base.graph["graph_id"]
    assert metadata["base_graph_sha256"] == base.graph_sha256
    assert metadata["node_report_specs"]
