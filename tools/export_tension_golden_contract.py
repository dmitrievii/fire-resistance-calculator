"""Export exact frozen-node contracts for the REPORT-IR9 central-tension golden route.

Audit-only: reads the frozen DAG and emits node/quantity metadata plus producer
candidates. No node is executed and no engineering value is calculated.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from standard_core.fire_ui0 import FireDAGModel

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
OUT = ROOT / "artifacts" / "tension_golden_contract_active_dag.json"

NODE_IDS = [
    "SP554_C_9_1",
    "SP554_C_GAMMAT_FROM_9_1",
    "SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY",
    "SP554_FIRE_D3_C_D2_TCR_HANDOFF",
    "SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1",
    "SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1",
    "SP554_C_DELTA_PR_PROTECTED_12_2",
    "SP554_D_12_10_MODE",
    "SP554_C_12_10_DOMAIN_INVERSE",
    "SP554_C_12_10_MINIMUM_THICKNESS",
    "SP554_C_12_10_DOMAIN",
    "SP554_C_12_10_PROTECTED_TIME",
    "SP554_Q_PROTECTED",
    "SP554_C_R_DESIGNATION_PROTECTED",
    "SP554_R_PROTECTED_CALCULATION_COMPLETE",
    "SP554_R_FINAL_PROTECTED",
    "SP554_H_REQUIRED_R",
]


def _bindings(node: Mapping[str, Any], key: str) -> list[str]:
    return [
        str(row["quantity_id"])
        for row in node.get(key) or []
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str)
    ]


def main() -> None:
    model = FireDAGModel.load(DAG)
    missing = [nid for nid in NODE_IDS if nid not in model.nodes]
    if missing:
        raise SystemExit(f"missing expected nodes: {missing}")

    qids: set[str] = set()
    nodes: dict[str, Any] = {}
    producer_candidates: dict[str, list[dict[str, Any]]] = {}

    for node_id in NODE_IDS:
        node = model.nodes[node_id]
        nodes[node_id] = node
        qids.update(_bindings(node, "consumes"))
        qids.update(_bindings(node, "produces"))

    for qid in sorted(qids):
        candidates = []
        for producer_id in model.producer_nodes.get(qid) or []:
            producer = model.nodes[producer_id]
            candidates.append(
                {
                    "node_id": producer_id,
                    "node_type": producer.get("node_type"),
                    "owner_standard_id": producer.get("owner_standard_id"),
                    "title": producer.get("title"),
                    "normative_refs": producer.get("normative_refs") or [],
                    "applicability": producer.get("applicability"),
                }
            )
        producer_candidates[qid] = candidates

    quantities = {
        qid: model.quantities[qid]
        for qid in sorted(qids)
        if qid in model.quantities
    }

    edge_rows = []
    selected = set(NODE_IDS)
    for edge in model.edges:
        if edge.get("from_node_id") in selected or edge.get("to_node_id") in selected:
            edge_rows.append(edge)

    payload = {
        "schema": "fire_report_tension_golden_contract_v1",
        "graph_id": model.graph.get("graph_id"),
        "graph_sha256": model.graph_sha256,
        "audit": {
            "executes_dag": False,
            "computes_engineering_values": False,
            "mutates_graph": False,
        },
        "node_ids": NODE_IDS,
        "nodes": nodes,
        "quantities": quantities,
        "producer_candidates": producer_candidates,
        "incident_edges": edge_rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"tension golden contract: {len(nodes)} nodes / {len(quantities)} quantities -> {OUT}")


if __name__ == "__main__":
    main()
