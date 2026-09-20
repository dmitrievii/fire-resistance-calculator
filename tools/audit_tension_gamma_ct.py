"""Audit the frozen DAG for special fire-condition coefficient semantics in SP554 tension.

The tool performs string/metadata census only. It does not execute formulas or
alter the graph.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from standard_core.fire_ui0 import FireDAGModel

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
OUT = ROOT / "artifacts" / "tension_gamma_ct_audit.json"


def _contains(value: Any, needles: tuple[str, ...]) -> bool:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    return any(n.lower() in text for n in needles)


def main() -> None:
    model = FireDAGModel.load(DAG)
    needles = (
        "gamma_ct", "γct", "γ_ct", "gamma_c,t", "gamma_c_t", "1.1",
        "особого предельного", "special limit", "special fire",
    )

    quantities = []
    for qid, q in sorted(model.quantities.items()):
        if _contains(q, needles):
            quantities.append(q)

    nodes = []
    for nid, node in sorted(model.nodes.items()):
        if _contains(node, needles):
            nodes.append(
                {
                    "node_id": nid,
                    "node_type": node.get("node_type"),
                    "owner_standard_id": node.get("owner_standard_id"),
                    "title": node.get("title"),
                    "normative_refs": node.get("normative_refs") or [],
                    "consumes": node.get("consumes") or [],
                    "produces": node.get("produces") or [],
                    "calculation_spec": node.get("calculation_spec"),
                    "check_spec": node.get("check_spec"),
                    "input_spec": node.get("input_spec"),
                    "notes": node.get("notes"),
                }
            )

    exact = model.nodes["SP554_C_9_1"]
    payload = {
        "schema": "fire_report_tension_gamma_ct_audit_v1",
        "graph_id": model.graph.get("graph_id"),
        "graph_sha256": model.graph_sha256,
        "audit": {
            "executes_dag": False,
            "changes_engineering_values": False,
            "search_needles": list(needles),
        },
        "sp554_c_9_1": exact,
        "matching_quantity_count": len(quantities),
        "matching_quantities": quantities,
        "matching_node_count": len(nodes),
        "matching_nodes": nodes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"gamma_ct audit: {len(quantities)} quantities / {len(nodes)} nodes -> {OUT}")


if __name__ == "__main__":
    main()
