"""DAG-first auditable calculation report intermediate representation.

REPORT-IR1 deliberately does not calculate engineering quantities.  It projects
an already executed :class:`GuidedCalculationSession` into a deterministic,
machine-readable report using only:

* immutable normative DAG metadata;
* the session execution trace;
* the session quantity ledger/provenance;
* branch failures/results recorded by the scheduler.

This makes the report a view of the calculation that actually ran rather than a
second calculation engine.  Editing an earlier answer is safe because FIRE-UI
replays the DAG and this module rebuilds the report from the replayed state.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping

REPORT_IR_SCHEMA = "fire_report_ir_v1"
REPORT_BLOCK_SCHEMA = "fire_report_block_v1"
REPORT_IR_CONTRACT = "dag_trace_projection_v1"

REPORT_KINDS = frozenset(
    {
        "INPUT",
        "ASSUMPTION",
        "GEOMETRY",
        "FORMULA",
        "TABLE_LOOKUP",
        "INTERPOLATION",
        "BRANCH_DECISION",
        "CHECK",
        "WARNING",
        "FAIL_CLOSED",
        "RESULT",
    }
)


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


def _fallback(mapping: Mapping[str, Any], key: str, default: Any) -> Any:
    return mapping[key] if key in mapping else default


def _snapshot(session_or_snapshot: Any) -> dict[str, Any]:
    if isinstance(session_or_snapshot, Mapping):
        return _deep(dict(session_or_snapshot))
    snapshot = getattr(session_or_snapshot, "snapshot", None)
    if not callable(snapshot):
        raise TypeError("report source must be a session with snapshot() or a snapshot mapping")
    state = snapshot()
    if not isinstance(state, Mapping):
        raise TypeError("session.snapshot() must return a mapping")
    return _deep(dict(state))


def _quantity_metadata(model: Any, quantity_id: str) -> Mapping[str, Any]:
    quantities = getattr(model, "quantities", {})
    row = quantities.get(quantity_id) if isinstance(quantities, Mapping) else None
    return row if isinstance(row, Mapping) else {}


def _ledger_index(state: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for row in _fallback(state, "ledger", []) or []:
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
            index[str(row["quantity_id"])] = row
    return index


def _value_record(
    model: Any,
    ledger: Mapping[str, Mapping[str, Any]],
    quantity_id: str,
    value: Any,
    *,
    owner_node_id: str,
    sequence: int,
) -> dict[str, Any]:
    """Describe a value without transforming or recalculating it."""
    meta = _quantity_metadata(model, quantity_id)
    ledger_row = ledger.get(quantity_id)
    provenance = None
    source_kind = None
    producer_node_id = None
    # Ledger enrichment is admissible only when it refers to this exact trace
    # value producer.  A later producer may have overwritten the same quantity.
    if isinstance(ledger_row, Mapping) and ledger_row.get("producer_node_id") == owner_node_id:
        provenance = _deep(ledger_row.get("provenance"))
        source_kind = ledger_row.get("source_kind")
        producer_node_id = ledger_row.get("producer_node_id")
    return {
        "quantity_id": quantity_id,
        "symbol": meta.get("symbol"),
        "name_ru": meta.get("name_ru") or quantity_id,
        "raw_value": _deep(value),
        "canonical_unit": meta.get("canonical_unit"),
        "data_type": meta.get("data_type"),
        "source_kind": source_kind,
        "producer_node_id": producer_node_id or owner_node_id,
        "execution_sequence": int(sequence),
        "provenance": provenance,
    }


def _dataset_index(model: Any) -> dict[str, Mapping[str, Any]]:
    graph = getattr(model, "graph", {})
    rows = graph.get("datasets") if isinstance(graph, Mapping) else None
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows or []:
        if isinstance(row, Mapping) and isinstance(row.get("id"), str):
            out[str(row["id"])] = row
    return out


def _dataset_evidence(model: Any, dataset_id: str) -> dict[str, Any]:
    row = _dataset_index(model).get(dataset_id, {})
    storage = row.get("storage") if isinstance(row, Mapping) else None
    storage = storage if isinstance(storage, Mapping) else {}
    evidence = {
        "dataset_id": dataset_id,
        "dataset_type": row.get("dataset_type") if isinstance(row, Mapping) else None,
        "owner_standard_id": row.get("owner_standard_id") if isinstance(row, Mapping) else None,
        "normative_refs": _deep(row.get("normative_refs") or []) if isinstance(row, Mapping) else [],
        "storage_mode": storage.get("mode"),
    }
    if storage.get("mode") == "external":
        evidence.update(
            {
                "uri": storage.get("uri"),
                "sha256": storage.get("sha256"),
                "format": storage.get("format"),
            }
        )
    return evidence


def _node_execution_spec(model: Any, node: Mapping[str, Any]) -> dict[str, Any]:
    """Copy the frozen DAG specification used by the real executor.

    No expression is evaluated here.  The purpose is audit provenance: the
    report block points to the same specification that produced its trace row.
    """
    evidence: dict[str, Any] = {"mode": "node_metadata_only"}
    datasets: list[dict[str, Any]] = []

    if isinstance(node.get("calculation_spec"), Mapping):
        spec = node["calculation_spec"]
        evidence.update(
            {
                "mode": "calculation_spec",
                "expression_language": spec.get("expression_language"),
                "expression": spec.get("expression"),
                "bindings": _deep(spec.get("bindings") or []),
                "cases": _deep(spec.get("cases") or []),
            }
        )
    elif isinstance(node.get("lookup_spec"), Mapping):
        spec = node["lookup_spec"]
        dataset_id = str(spec.get("dataset_id"))
        evidence.update(
            {
                "mode": "lookup_spec",
                "dataset_id": dataset_id,
                "selector_bindings": _deep(spec.get("selector_bindings") or []),
                "output_bindings": _deep(spec.get("output_bindings") or []),
                "interpolation": _deep(spec.get("interpolation") or {}),
            }
        )
        datasets.append(_dataset_evidence(model, dataset_id))
    elif isinstance(node.get("check_spec"), Mapping):
        spec = node["check_spec"]
        evidence.update(
            {
                "mode": "check_spec",
                "expression_language": spec.get("expression_language"),
                "expression": spec.get("expression"),
                "bindings": _deep(spec.get("bindings") or []),
                "cases": _deep(spec.get("cases") or []),
            }
        )
    elif node.get("check_condition") is not None:
        evidence.update({"mode": "check_condition", "condition": _deep(node.get("check_condition"))})
    elif isinstance(node.get("geometry_spec"), Mapping):
        spec = node["geometry_spec"]
        evidence.update({"mode": "geometry_spec", "geometry_spec": _deep(spec)})
        dataset_id = spec.get("catalog_dataset_id")
        if dataset_id:
            datasets.append(_dataset_evidence(model, str(dataset_id)))
    elif node.get("classification_rules") is not None:
        evidence.update(
            {
                "mode": "classification_rules",
                "classification_rules": _deep(node.get("classification_rules") or []),
                "fallback_behavior": node.get("fallback_behavior"),
                "fallback_value": _deep(node.get("fallback_value")),
            }
        )

    if datasets:
        evidence["datasets"] = datasets
    return evidence


def _kind_for_node(node: Mapping[str, Any]) -> str:
    # Future DAG versions may carry presentation-only report_spec metadata.  It
    # may select a supported report kind, but never provides calculation values.
    report_spec = node.get("report_spec")
    if isinstance(report_spec, Mapping):
        requested = report_spec.get("kind")
        if requested in REPORT_KINDS:
            return str(requested)

    ntype = str(node.get("node_type") or "")
    if ntype in {"input", "standard_handoff"}:
        return "INPUT"
    if ntype in {"decision", "applicability_check", "classification"}:
        return "BRANCH_DECISION"
    if ntype == "geometry_provider":
        return "GEOMETRY"
    if ntype == "lookup":
        interpolation = _fallback(node.get("lookup_spec") or {}, "interpolation", {})
        method = interpolation.get("method") if isinstance(interpolation, Mapping) else None
        return "INTERPOLATION" if method not in {None, "none"} else "TABLE_LOOKUP"
    if ntype == "calculation":
        return "FORMULA"
    if ntype == "compliance_check":
        return "CHECK"
    if ntype == "result":
        return "RESULT"
    if ntype == "unsupported":
        return "FAIL_CLOSED"
    return "ASSUMPTION"


def _section_for_node(node: Mapping[str, Any]) -> str:
    report_spec = node.get("report_spec")
    if isinstance(report_spec, Mapping) and isinstance(report_spec.get("section_key"), str):
        return str(report_spec["section_key"])
    ntype = str(node.get("node_type") or "")
    if ntype in {"input", "standard_handoff"}:
        return "input_data"
    if ntype in {"decision", "applicability_check", "classification"}:
        return "routing_and_assumptions"
    if ntype == "geometry_provider":
        return "geometry"
    if ntype in {"calculation", "lookup"}:
        return "calculation"
    if ntype == "compliance_check":
        return "verification"
    if ntype == "result":
        return "results"
    return "audit"


def _title_for_node(node: Mapping[str, Any]) -> str:
    report_spec = node.get("report_spec")
    if isinstance(report_spec, Mapping):
        title = report_spec.get("title_ru") or report_spec.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return str(node.get("title") or node.get("id") or "Расчётный шаг")


def _report_presentation(node: Mapping[str, Any]) -> dict[str, Any]:
    """Return presentation metadata only; never calculation instructions."""
    report_spec = node.get("report_spec")
    if not isinstance(report_spec, Mapping):
        return {}
    allowed = {
        "section_key",
        "kind",
        "title",
        "title_ru",
        "title_key",
        "formula_latex",
        "substitution_template_latex",
        "result_quantity_ids",
        "display_precision",
        "visibility",
    }
    return {key: _deep(value) for key, value in report_spec.items() if key in allowed}


def _trace_blocks(model: Any, state: Mapping[str, Any]) -> list[dict[str, Any]]:
    ledger = _ledger_index(state)
    nodes = getattr(model, "nodes", {})
    blocks: list[dict[str, Any]] = []
    ordinals: dict[str, int] = {}

    for trace in _fallback(state, "trace", []) or []:
        if not isinstance(trace, Mapping) or trace.get("status") != "COMPLETE":
            continue
        node_id = trace.get("node_id")
        if not isinstance(node_id, str) or node_id not in nodes:
            continue
        node = nodes[node_id]
        sequence = int(trace.get("sequence") or 0)
        ordinals[node_id] = ordinals.get(node_id, 0) + 1
        ordinal = ordinals[node_id]

        inputs = [
            _value_record(model, ledger, str(qid), value, owner_node_id=node_id, sequence=sequence)
            for qid, value in sorted((trace.get("inputs") or {}).items())
        ]
        outputs = [
            _value_record(model, ledger, str(qid), value, owner_node_id=node_id, sequence=sequence)
            for qid, value in sorted((trace.get("outputs") or {}).items())
        ]

        block = {
            "schema": REPORT_BLOCK_SCHEMA,
            "report_block_id": f"{node_id}#{ordinal}",
            "owner_node_id": node_id,
            "owner_standard_id": node.get("owner_standard_id"),
            "sequence": sequence,
            "event_kind": trace.get("event_kind"),
            "kind": _kind_for_node(node),
            "section_key": _section_for_node(node),
            "title": _title_for_node(node),
            "normative_refs": _deep(node.get("normative_refs") or trace.get("normative_refs") or []),
            "inputs": inputs,
            "outputs": outputs,
            "selected_edge_id": trace.get("selected_edge_id"),
            "execution_spec": _node_execution_spec(model, node),
            "presentation": _report_presentation(node),
            "message": trace.get("message"),
        }
        blocks.append(block)
    return blocks


def _failure_blocks(model: Any, state: Mapping[str, Any], *, start_sequence: int) -> list[dict[str, Any]]:
    nodes = getattr(model, "nodes", {})
    blocks: list[dict[str, Any]] = []
    ordinals: dict[str, int] = {}
    seq = start_sequence
    for failure in _fallback(state, "branch_failures", []) or []:
        if not isinstance(failure, Mapping):
            continue
        node_id = failure.get("node_id")
        if not isinstance(node_id, str) or node_id not in nodes:
            continue
        # Only current fail-closed diagnostics belong in the report. Transient
        # failures are cleared by the session when their node succeeds later.
        seq += 1
        ordinals[node_id] = ordinals.get(node_id, 0) + 1
        node = nodes[node_id]
        blocks.append(
            {
                "schema": REPORT_BLOCK_SCHEMA,
                "report_block_id": f"FAIL:{node_id}#{ordinals[node_id]}",
                "owner_node_id": node_id,
                "owner_standard_id": node.get("owner_standard_id"),
                "sequence": seq,
                "event_kind": "branch_failure",
                "kind": "FAIL_CLOSED",
                "section_key": "audit",
                "title": _title_for_node(node),
                "normative_refs": _deep(node.get("normative_refs") or []),
                "inputs": [],
                "outputs": [],
                "selected_edge_id": None,
                "execution_spec": _node_execution_spec(model, node),
                "presentation": _report_presentation(node),
                "message": failure.get("message") or failure.get("status"),
                "failure": _deep(dict(failure)),
            }
        )
    return blocks


def build_report_ir(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
    """Build a deterministic report IR from the calculation state.

    The function is intentionally pure: it does not mutate the session, does not
    run DAG nodes, does not evaluate formula expressions and does not perform
    table interpolation.  Every numerical value in a normal report block comes
    from an already completed trace event.
    """
    state = _snapshot(session_or_snapshot)
    graph = getattr(model, "graph", {})
    graph_id = graph.get("graph_id") if isinstance(graph, Mapping) else state.get("graph_id")
    graph_sha256 = getattr(model, "graph_sha256", None) or state.get("graph_sha256")

    trace_blocks = _trace_blocks(model, state)
    max_sequence = max((int(block["sequence"]) for block in trace_blocks), default=0)
    blocks = trace_blocks + _failure_blocks(model, state, start_sequence=max_sequence)
    blocks.sort(key=lambda block: (int(block["sequence"]), str(block["report_block_id"])))

    report: dict[str, Any] = {
        "schema": REPORT_IR_SCHEMA,
        "contract": REPORT_IR_CONTRACT,
        "graph_id": graph_id,
        "graph_sha256": graph_sha256,
        "session_schema": state.get("schema"),
        "session_status": state.get("status"),
        "entry_node_id": state.get("entry_node_id"),
        "current_node_id": state.get("current_node_id"),
        "block_count": len(blocks),
        "blocks": blocks,
        "audit": {
            "calculation_values_recomputed_by_report": False,
            "normal_block_value_source": "completed_session_trace",
            "dag_metadata_is_authoritative": True,
            "deterministic_order": "execution_sequence_then_report_block_id",
            "wall_clock_time_in_identity": False,
        },
    }
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    report["report_sha256"] = sha256(canonical).hexdigest()
    return report


def report_ir_json(model: Any, session_or_snapshot: Any, *, indent: int = 2) -> str:
    """Serialize REPORT-IR1 deterministically for persistence/golden tests."""
    report = build_report_ir(model, session_or_snapshot)
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=indent, allow_nan=False) + "\n"
