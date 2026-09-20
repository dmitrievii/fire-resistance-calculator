"""REPORT-IR2: richer DAG-bound report evidence without a second calculation path.

IR2 is a deterministic enrichment over REPORT-IR1.  It does not evaluate
engineering formulae, perform table interpolation, or derive replacement
results.  It binds the values already present in completed trace records back to
the immutable DAG bindings that owned those values.
"""
from __future__ import annotations

import copy
import json
from collections import Counter
from hashlib import sha256
from typing import Any, Mapping

from .report_ir import build_report_ir

REPORT_IR2_SCHEMA = "fire_report_ir_v2"
REPORT_IR2_CONTRACT = "dag_trace_binding_evidence_v2"


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


def _value_index(block: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    out: dict[str, Mapping[str, Any]] = {}
    for side in ("inputs", "outputs"):
        for row in block.get(side) or []:
            if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
                out[str(row["quantity_id"])] = row
    return out


def _bound_value(index: Mapping[str, Mapping[str, Any]], qid: str) -> dict[str, Any]:
    row = index.get(qid)
    if row is None:
        return {
            "quantity_id": qid,
            "present_in_trace": False,
            "raw_value": None,
            "canonical_unit": None,
        }
    return {
        "quantity_id": qid,
        "present_in_trace": True,
        "raw_value": _deep(row.get("raw_value")),
        "canonical_unit": row.get("canonical_unit"),
        "symbol": row.get("symbol"),
        "name_ru": row.get("name_ru"),
    }


def _formula_binding_evidence(block: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    index = _value_index(block)
    bindings = []
    for binding in spec.get("bindings") or []:
        if not isinstance(binding, Mapping):
            continue
        qid = str(binding.get("quantity_id") or "")
        row = _bound_value(index, qid)
        row.update({"variable": binding.get("variable")})
        bindings.append(row)
    return {
        "evidence_mode": "trace_bound_formula_operands",
        "expression_language": spec.get("expression_language"),
        "expression": spec.get("expression"),
        "bindings": bindings,
        "result_values": _deep(block.get("outputs") or []),
        "report_recomputed_result": False,
    }


def _lookup_binding_evidence(block: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    index = _value_index(block)
    selectors = []
    for binding in spec.get("selector_bindings") or []:
        if not isinstance(binding, Mapping):
            continue
        qid = str(binding.get("quantity_id") or "")
        row = _bound_value(index, qid)
        row.update({"dataset_field": binding.get("dataset_field")})
        selectors.append(row)
    outputs = []
    for binding in spec.get("output_bindings") or []:
        if not isinstance(binding, Mapping):
            continue
        qid = str(binding.get("quantity_id") or "")
        row = _bound_value(index, qid)
        row.update({"dataset_field": binding.get("dataset_field")})
        outputs.append(row)
    return {
        "evidence_mode": "trace_bound_lookup_io",
        "dataset_id": spec.get("dataset_id"),
        "selectors": selectors,
        "output_bindings": outputs,
        "interpolation": _deep(spec.get("interpolation") or {}),
        "selected_dataset_rows": None,
        "selected_dataset_rows_status": "NOT_CAPTURED_BY_RUNTIME_YET",
        "report_recomputed_lookup": False,
    }


def _decision_evidence(block: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidence_mode": "trace_bound_decision",
        "decision_values": _deep(block.get("outputs") or []),
        "selected_edge_id": block.get("selected_edge_id"),
    }


def _geometry_evidence(block: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidence_mode": "trace_bound_geometry_outputs",
        "geometry_spec": _deep(spec),
        "result_values": _deep(block.get("outputs") or []),
        "report_recomputed_geometry": False,
    }


def _execution_evidence_for_block(block: Mapping[str, Any]) -> dict[str, Any]:
    spec = block.get("execution_spec") or {}
    mode = spec.get("mode") if isinstance(spec, Mapping) else None
    if mode in {"calculation_spec", "check_spec"}:
        return _formula_binding_evidence(block, spec)
    if mode == "lookup_spec":
        return _lookup_binding_evidence(block, spec)
    if mode == "geometry_spec":
        return _geometry_evidence(block, spec.get("geometry_spec") or {})
    if block.get("kind") == "BRANCH_DECISION":
        return _decision_evidence(block)
    return {
        "evidence_mode": "trace_values_and_dag_metadata",
        "result_values": _deep(block.get("outputs") or []),
        "report_recomputed_result": False,
    }


def reportability_census(model: Any) -> dict[str, Any]:
    """Census the complete normative DAG for report projection readiness."""
    nodes = getattr(model, "nodes", {})
    graph = getattr(model, "graph", {})
    kind_counts: Counter[str] = Counter()
    node_type_counts: Counter[str] = Counter()
    spec_mode_counts: Counter[str] = Counter()
    nodes_without_normative_refs: list[str] = []
    explicit_report_spec_nodes: list[str] = []

    from .report_ir import _kind_for_node, _node_execution_spec

    for node_id, node in nodes.items():
        kind_counts[_kind_for_node(node)] += 1
        node_type_counts[str(node.get("node_type") or "UNKNOWN")] += 1
        spec_mode_counts[str(_node_execution_spec(model, node).get("mode") or "unknown")] += 1
        if not node.get("normative_refs"):
            nodes_without_normative_refs.append(str(node_id))
        if isinstance(node.get("report_spec"), Mapping):
            explicit_report_spec_nodes.append(str(node_id))

    quantities = graph.get("quantities") if isinstance(graph, Mapping) else []
    datasets = graph.get("datasets") if isinstance(graph, Mapping) else []
    return {
        "graph_id": graph.get("graph_id") if isinstance(graph, Mapping) else None,
        "graph_sha256": getattr(model, "graph_sha256", None),
        "node_count": len(nodes),
        "quantity_count": len(quantities or []),
        "dataset_count": len(datasets or []),
        "report_kind_counts": dict(sorted(kind_counts.items())),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "execution_spec_mode_counts": dict(sorted(spec_mode_counts.items())),
        "nodes_without_normative_refs": sorted(nodes_without_normative_refs),
        "nodes_without_normative_refs_count": len(nodes_without_normative_refs),
        "explicit_report_spec_nodes": sorted(explicit_report_spec_nodes),
        "explicit_report_spec_count": len(explicit_report_spec_nodes),
        "projection_policy": "all executed trace nodes are reportable; unsupported/failures remain explicit FAIL_CLOSED evidence",
    }


def build_report_ir2(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    """Build REPORT-IR2 by enriching REPORT-IR1 with trace-bound DAG evidence."""
    ir1 = build_report_ir(model, session_or_snapshot)
    blocks = []
    for block in ir1.get("blocks") or []:
        row = _deep(block)
        row["execution_evidence"] = _execution_evidence_for_block(row)
        blocks.append(row)

    report = {
        "schema": REPORT_IR2_SCHEMA,
        "contract": REPORT_IR2_CONTRACT,
        "source_report_schema": ir1.get("schema"),
        "source_report_sha256": ir1.get("report_sha256"),
        "graph_id": ir1.get("graph_id"),
        "graph_sha256": ir1.get("graph_sha256"),
        "session_schema": ir1.get("session_schema"),
        "session_status": ir1.get("session_status"),
        "entry_node_id": ir1.get("entry_node_id"),
        "current_node_id": ir1.get("current_node_id"),
        "block_count": len(blocks),
        "blocks": blocks,
        "dag_census": reportability_census(model),
        "audit": {
            "calculation_values_recomputed_by_report": False,
            "table_interpolation_recomputed_by_report": False,
            "formula_bindings_are_trace_values": True,
            "dag_metadata_is_authoritative": True,
            "runtime_selected_dataset_rows_captured": False,
            "runtime_selected_dataset_rows_limitation": "REPORT-IR2 does not infer interpolation brackets; runtime capture is a later gate.",
        },
    }
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()
    return report


def report_ir2_json(model: Any, session_or_snapshot: Any, *, indent: int = 2) -> str:
    report = build_report_ir2(model, session_or_snapshot)
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=indent, allow_nan=False) + "\n"
