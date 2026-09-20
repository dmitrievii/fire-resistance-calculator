from __future__ import annotations

import json
from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession, QuantityValue
from standard_core.fire_ui1_http import FireUI1Application

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph/dag_v0.3.58_fire_ui22_routing_protection_library_hotfix.json"
POLICY = ROOT / "data/fire_ui22_presentation_policy.json"


def _seed(session, app, qid: str, value):
    q = app.model.quantities[qid]
    session.values[qid] = QuantityValue(qid, value, q.get("canonical_unit"), "CALCULATED", "TEST_SEED", 1, None)


def test_all_result_nodes_with_guided_outgoing_edges_have_explicit_continuation_or_terminal_policy():
    graph = json.loads(DAG.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    outgoing = {}
    for edge in graph["edges"]:
        if edge.get("edge_type") in {"control", "branch", "handoff"}:
            outgoing.setdefault(edge["from_node_id"], []).append(edge)
    presentation = policy.get("node_presentation", {})
    failures = []
    for nid, edges in outgoing.items():
        if nodes[nid]["node_type"] != "result":
            continue
        ui = presentation.get(nid, {})
        if ui.get("terminal_result") is True:
            continue
        if ui.get("continue_after_result") is not True:
            failures.append((nid, [(e["id"], e["to_node_id"]) for e in edges]))
    assert failures == []


def test_unprotected_result_reaches_post_result_action_selector_and_protection_branch():
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id="SP554_R_UNPROTECTED", registry=app.service.registry)
    _seed(s, app, "unprotected_fire_resistance_min", 17.3)
    s._auto_progress()
    assert s.current_node_id == "SP554_D_AFTER_UNPROTECTED"
    assert s.status == "AWAITING_INPUT"
    card = s.current_card()
    assert card is not None
    assert any(x["value"] == "design_fire_protection" for x in card["options"])
    s.submit("design_fire_protection")
    assert s.current_node_id == "SP554_D_PROTECTION_SOURCE_MODE"
    assert s.status == "AWAITING_INPUT"


def test_protected_result_reaches_post_result_action_selector():
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id="SP554_R_PROTECTED", registry=app.service.registry)
    _seed(s, app, "protected_fire_resistance_min", 62.0)
    s._auto_progress()
    assert s.current_node_id == "SP554_D_AFTER_PROTECTED"
    assert s.status == "AWAITING_INPUT"
