from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

from standard_core.fire_ui0 import FireDAGModel


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _output_ids(node: Mapping[str, Any]) -> list[str]:
    return [
        str(row["quantity_id"])
        for row in node.get("produces") or []
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str)
    ]


def _is_candidate(node_id: str, node: Mapping[str, Any]) -> bool:
    title = str(node.get("title") or "").lower()
    nid = node_id.lower()
    return (
        "_gov" in nid
        or "governing" in nid
        or "governing" in title
        or "управля" in title
        or "определя" in title
    )


def _spec(node: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("calculation_spec", "check_spec", "lookup_spec"):
        value = node.get(key)
        if isinstance(value, Mapping):
            return {"kind": key, "value": copy.deepcopy(dict(value))}
    return {"kind": None, "value": None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export structural hints for existing governing producers.")
    parser.add_argument("--dag", default=f"normative_graph/{ACTIVE_DAG}")
    parser.add_argument("--output", default="artifacts/governing_candidates_active_dag.json")
    args = parser.parse_args()

    model = FireDAGModel.load(Path(args.dag))
    rows: list[dict[str, Any]] = []
    for node_id in sorted(model.nodes):
        node = model.nodes[node_id]
        if not _is_candidate(node_id, node):
            continue
        outputs = _output_ids(node)
        rows.append(
            {
                "node_id": node_id,
                "node_type": node.get("node_type"),
                "owner_standard_id": node.get("owner_standard_id"),
                "title": node.get("title"),
                "normative_refs": copy.deepcopy(node.get("normative_refs") or []),
                "consumes": copy.deepcopy(node.get("consumes") or []),
                "produces": copy.deepcopy(node.get("produces") or []),
                "output_quantities": [copy.deepcopy(model.quantities[qid]) for qid in outputs if qid in model.quantities],
                "execution_spec": _spec(node),
                "result_kind": node.get("result_kind"),
                "result_quantity_ids": copy.deepcopy(node.get("result_quantity_ids") or []),
            }
        )

    report = {
        "schema": "fire_report_governing_candidate_audit_v1",
        "graph_id": model.graph["graph_id"],
        "graph_sha256": model.graph_sha256,
        "candidate_selection": (
            "structural audit hint only: id/title contains GOV/governing/управля/определя; "
            "never used by REPORT-IR to select an engineering governing result"
        ),
        "candidate_count": len(rows),
        "candidates": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"candidate_count={len(rows)}")
    for row in rows:
        print(f"{row['node_id']}: {[q.get('id') for q in row['output_quantities']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
