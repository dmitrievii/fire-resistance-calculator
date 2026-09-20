"""Export a static census of DAG nodes relevant to the SP554 central-tension report route.

This tool is audit-only. It does not execute nodes or calculate engineering values.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from standard_core.fire_ui0 import FireDAGModel

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
OUT = ROOT / "artifacts" / "tension_report_route_active_dag.json"


def _refs(node: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(x) for x in node.get("normative_refs") or [] if isinstance(x, Mapping)]


def _qid_list(node: Mapping[str, Any], key: str) -> list[str]:
    return [
        str(row["quantity_id"])
        for row in node.get(key) or []
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str)
    ]


def _selected(node_id: str, node: Mapping[str, Any]) -> tuple[bool, list[str]]:
    owner = str(node.get("owner_standard_id") or "")
    title = str(node.get("title") or "")
    text = f"{node_id} {title}".lower()
    reasons: list[str] = []

    for ref in _refs(node):
        if str(ref.get("standard_id") or "") != "SP554_2026":
            continue
        section = str(ref.get("section") or ref.get("clause") or "")
        annex = str(ref.get("annex_ref") or "")
        table = str(ref.get("table_ref") or "")
        if section.startswith("9"):
            reasons.append("SP554_SECTION_9")
        if section.startswith("12"):
            reasons.append("SP554_SECTION_12")
        if annex.upper() in {"Б", "B"}:
            reasons.append("SP554_ANNEX_B")
        if table.upper().startswith(("Б.", "B.")):
            reasons.append("SP554_ANNEX_B_TABLE")

    lexical = {
        "tension": ("tension", "растяж", "растянут"),
        "critical_temperature": ("critical_temperature", "critical temperature", "критическ", "t_cr", "tcr"),
        "heated_perimeter": ("heated_perimeter", "обогреваем", "периметр"),
        "reduced_thickness": ("reduced_thickness", "приведен", "delta_pr", "δпр"),
        "protection": ("protection", "огнезащ"),
        "fire_resistance": ("fire_resistance", "огнестойк", "r_req", "rfact"),
        "gamma_t": ("gamma_t", "γt"),
    }
    if owner == "SP554_2026":
        for label, needles in lexical.items():
            if any(needle in text for needle in needles):
                reasons.append(f"LEXICAL_{label.upper()}")

    return bool(reasons), sorted(set(reasons))


def main() -> None:
    model = FireDAGModel.load(DAG)
    rows = []
    for node_id in sorted(model.nodes):
        node = model.nodes[node_id]
        keep, reasons = _selected(node_id, node)
        if not keep:
            continue
        spec_kind = next(
            (
                key
                for key in (
                    "calculation_spec",
                    "lookup_spec",
                    "check_spec",
                    "check_condition",
                    "classification_rules",
                    "input_spec",
                )
                if node.get(key) is not None
            ),
            None,
        )
        rows.append(
            {
                "node_id": node_id,
                "node_type": node.get("node_type"),
                "owner_standard_id": node.get("owner_standard_id"),
                "title": node.get("title"),
                "reasons": reasons,
                "normative_refs": _refs(node),
                "consumes": _qid_list(node, "consumes"),
                "produces": _qid_list(node, "produces"),
                "spec_kind": spec_kind,
                "result_quantity_id": node.get("result_quantity_id"),
                "result_quantity_ids": node.get("result_quantity_ids"),
                "applicability": node.get("applicability"),
            }
        )

    payload = {
        "schema": "fire_report_tension_route_census_v1",
        "graph_id": model.graph.get("graph_id"),
        "graph_sha256": model.graph_sha256,
        "audit": {
            "executes_dag": False,
            "computes_engineering_values": False,
            "selection_is_report_route_discovery_only": True,
        },
        "node_count": len(rows),
        "nodes": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"tension-report route census: {len(rows)} nodes -> {OUT}")


if __name__ == "__main__":
    main()
