from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import FireDAGModel
from standard_core.fire_sp554_runtime_v092 import TENSION_NODE_ID
from standard_core.fire_sp554_v092_guided_overlay import build_model
from standard_core.report_ir_v092 import PENDING_CURRENT_STATE, build_report_ir_v092
from streamlit_expertise_report_v092 import render_expertise_narrative_markdown_v092


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _model() -> FireDAGModel:
    return build_model(FireDAGModel.load(DAG))


def _state(model: FireDAGModel, *, current: str, status: str, trace: list[dict] | None = None) -> dict:
    return {
        "schema": "fire_ui_session_v1",
        "graph_id": model.graph["graph_id"],
        "graph_sha256": model.graph_sha256,
        "entry_node_id": "SP554_D_LOAD_BEARING",
        "current_node_id": current,
        "status": status,
        "ledger": [],
        "trace": list(trace or []),
        "branch_failures": [],
    }


def _complete(node: dict, sequence: int = 1) -> dict:
    return {
        "sequence": sequence,
        "node_id": node["id"],
        "node_type": node["node_type"],
        "event_kind": "answer",
        "status": "COMPLETE",
        "inputs": {},
        "outputs": {},
        "selected_edge_id": None,
        "normative_refs": node.get("normative_refs") or [],
        "message": None,
    }


def test_progressive_report_at_start_contains_only_current_pending_node_and_no_future_formula():
    model = _model()
    current = "SP554_D_LOAD_BEARING"
    report = build_report_ir_v092(
        model,
        _state(model, current=current, status="AWAITING_INPUT"),
    )

    assert report["block_count"] == 1
    block = report["blocks"][0]
    assert block["owner_node_id"] == current
    assert block["progress_state"] == PENDING_CURRENT_STATE
    assert block["event_kind"] == "pending_current_node"
    assert block["execution_spec"]["mode"] == "not_executed_current_node"
    assert "formula_latex" not in block["presentation"]
    assert "substitution_template_latex" not in block["presentation"]
    assert TENSION_NODE_ID not in {row["owner_node_id"] for row in report["blocks"]}

    assert report["audit"]["v092_progressive_visibility"] is True
    assert report["audit"]["v092_future_dag_nodes_projected_to_main_report"] is False
    assert report["audit"]["v092_pending_current_block_count"] == 1
    assert report["audit"]["v092_pending_formula_visible_before_execution"] is False

    markdown = render_expertise_narrative_markdown_v092(report)
    assert "Текущий незавершённый шаг" in markdown
    assert "Статус: PENDING" in markdown
    assert "формула, числовая подстановка и результат будут добавлены" in markdown.lower()
    assert TENSION_NODE_ID not in markdown
    assert r"\gamma_T" not in markdown


def test_progressive_report_contains_completed_trace_plus_exactly_one_current_pending_node():
    model = _model()
    completed_id = "SP554_D_LOAD_BEARING"
    current = "SP554_D_ENCLOSING"
    completed = _complete(model.nodes[completed_id])

    report = build_report_ir_v092(
        model,
        _state(model, current=current, status="AWAITING_INPUT", trace=[completed]),
    )

    owners = [row["owner_node_id"] for row in report["blocks"]]
    pending = [row for row in report["blocks"] if row.get("progress_state") == PENDING_CURRENT_STATE]
    assert owners == [completed_id, current]
    assert len(pending) == 1
    assert pending[0]["owner_node_id"] == current
    assert pending[0]["sequence"] > report["blocks"][0]["sequence"]
    assert report["summary"]["executed_block_count"] == 1
    assert report["block_count"] == 2
    assert TENSION_NODE_ID not in owners


def test_progressive_report_result_state_has_no_pending_block():
    model = _model()
    completed_id = "SP554_D_LOAD_BEARING"
    completed = _complete(model.nodes[completed_id])

    report = build_report_ir_v092(
        model,
        _state(model, current=completed_id, status="RESULT", trace=[completed]),
    )

    assert all(row.get("progress_state") != PENDING_CURRENT_STATE for row in report["blocks"])
    assert report["audit"]["v092_pending_current_block_count"] == 0
    assert report["block_count"] == 1
