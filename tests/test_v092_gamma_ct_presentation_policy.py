from __future__ import annotations

import json
from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.fire_sp554_v092_guided_overlay import (
    BYPASS_SUCCESSOR_NODE_ID,
    OBSOLETE_GAMMA_CT_CALC_NODE_ID,
    OBSOLETE_GAMMA_CT_SUBGRAPH,
    build_model,
)
from standard_core.report_metadata import report_metadata_for_model, report_spec_for_node


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _load_real_model() -> FireDAGModel:
    with DAG.open("r", encoding="utf-8") as fh:
        graph = json.load(fh)
    with POLICY.open("r", encoding="utf-8") as fh:
        policy = json.load(fh)
    return FireDAGModel(graph, source_path=str(DAG), presentation_policy=policy)


def _override_targets(policy: dict) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for source, rules in (policy.get("navigation_overrides") or {}).items():
        for rule in rules or []:
            rows.append((str(source), str(rule.get("id") or ""), str(rule.get("to_node_id") or "")))
    return rows


def test_real_presentation_policy_contains_legacy_gamma_targets_before_v092():
    model = _load_real_model()
    targets = _override_targets(model.presentation_policy)

    legacy = [row for row in targets if row[2] in OBSOLETE_GAMMA_CT_SUBGRAPH]
    assert legacy, "fixture must prove the frozen presentation policy still contains legacy gamma navigation"
    assert any(row[0] == "SP16_C_SHEAR_ALPHA_IDENTITY_WEAK" for row in legacy)
    assert any(row[0] == "SP16_C_SHEAR_ALPHA45" for row in legacy)


def test_v092_build_model_redirects_all_presentation_gamma_targets_to_ambient_loads():
    model = build_model(_load_real_model())
    targets = _override_targets(model.presentation_policy)

    assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(model.nodes)
    assert all(target not in OBSOLETE_GAMMA_CT_SUBGRAPH for _, _, target in targets)

    by_source = {
        source: target
        for source, _, target in targets
        if source in {"SP16_C_SHEAR_ALPHA_IDENTITY_WEAK", "SP16_C_SHEAR_ALPHA45"}
    }
    assert by_source == {
        "SP16_C_SHEAR_ALPHA_IDENTITY_WEAK": BYPASS_SUCCESSOR_NODE_ID,
        "SP16_C_SHEAR_ALPHA45": BYPASS_SUCCESSOR_NODE_ID,
    }


def test_v092_presentation_policy_has_no_removed_gamma_node_as_source_or_target():
    model = build_model(_load_real_model())
    policy = model.presentation_policy

    overrides = policy.get("navigation_overrides") or {}
    assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(overrides)
    for source, rules in overrides.items():
        assert source not in OBSOLETE_GAMMA_CT_SUBGRAPH
        for rule in rules or []:
            assert rule.get("to_node_id") not in OBSOLETE_GAMMA_CT_SUBGRAPH

    for key in ("hidden_normative_nodes", "guided_excluded_nodes"):
        assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(set(policy.get(key) or []))
    assert OBSOLETE_GAMMA_CT_SUBGRAPH.isdisjoint(set((policy.get("deferred_nodes") or {}).keys()))


def test_v092_report_metadata_stays_bound_to_frozen_source_after_overlay_removes_gamma_nodes():
    model = build_model(_load_real_model())

    assert OBSOLETE_GAMMA_CT_CALC_NODE_ID not in model.nodes
    metadata = report_metadata_for_model(model)

    # The immutable sidecar may retain historical metadata for a node that
    # existed in the frozen source DAG.  Validation must therefore succeed
    # against source_path rather than rejecting the active overlay.
    assert OBSOLETE_GAMMA_CT_CALC_NODE_ID in (metadata.get("node_report_specs") or {})

    # Removed overlay nodes are not active report nodes and must not leak back
    # into REPORT-IR through sidecar lookup.
    assert report_spec_for_node(model, OBSOLETE_GAMMA_CT_CALC_NODE_ID) == {}
