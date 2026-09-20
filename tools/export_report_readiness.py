from __future__ import annotations

import argparse
import json
from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.report_readiness import build_report_readiness


ACTIVE_DAG = "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export static REPORT-IR readiness census for the active DAG.")
    parser.add_argument("--dag", default=f"normative_graph/{ACTIVE_DAG}")
    parser.add_argument("--output", default="artifacts/report_readiness_active_dag.json")
    args = parser.parse_args()

    model = FireDAGModel.load(Path(args.dag))
    report = build_report_readiness(model)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checks = report["check_verdict_readiness"]
    print(f"graph_id={report['graph_id']}")
    print(f"node_count={report['node_count']}")
    print(f"quantity_count={report['quantity_count']}")
    print(f"check_node_count={checks['check_node_count']}")
    print(f"unambiguous_check_count={checks['unambiguous_check_count']}")
    print(f"needs_explicit_verdict_count={checks['needs_explicit_verdict_count']}")
    print(f"governing_status={report['governing_readiness']['status']}")
    print(f"blocking_metadata_gap_count={report['blocking_metadata_gap_count']}")
    print("needs_explicit_verdict_nodes=")
    for row in checks["checks"]:
        if row["status"] == "NEEDS_BOOLEAN_VERDICT_OUTPUT":
            print(f"  {row['node_id']}: outputs={row['output_quantity_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
