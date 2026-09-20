"""FIRE-UI0 DAG-driven guided-calculation architecture.

This module is deliberately UI-framework agnostic.  It converts the frozen
normative DAG into deterministic UI contracts and provides the state machine
used by future browser/desktop frontends.  No SP16/SP554 calculation formula is
reimplemented here; calculation nodes can only run through explicitly
registered production executors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import copy
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Sequence

UI_CONTRACT_SCHEMA = "fire_ui_contract_v1"
SESSION_SCHEMA = "fire_ui_session_v1"
TRACE_SCHEMA = "fire_ui_trace_v1"
DEFAULT_ENTRY_NODE_ID = "SP554_I_BUILDING_USE"


def _fallback(mapping: Mapping[str, Any], key: str, default: Any) -> Any:
    """Return an optional DAG field without using silent engineering ``dict.get`` fallbacks."""
    return mapping[key] if key in mapping else default


class FireUIError(ValueError):
    """
    Summary:
        Base exception for deterministic FIRE-UI0 guided-calculation contract errors.

    Standard reference:
        UI/application architecture only; normative meaning is inherited from the frozen DAG and registered production executors.

    Fields:
        Carries the standard Python exception message only.

    Validation:
        Raised on invalid UI payloads, DAG contract violations, provenance failures or incompatible saved sessions.

    Used by:
        FireDAGModel, GuidedCalculationSession and GuidedCalculationService.
    """


class FireUIBlocked(FireUIError):
    """
    Summary:
        Signals a fail-closed guided-navigation state that cannot be advanced safely.

    Standard reference:
        UI/application architecture only; no normative calculation is substituted when a dependency is unresolved.

    Fields:
        Exception text identifies the blocking node or branch condition.

    Validation:
        Used for missing executors, unresolved branch conditions, no-match routing and unresolved ambiguity.

    Used by:
        GuidedCalculationSession automatic progression and frontend blocking-state presentation.
    """


@dataclass(frozen=True)
class QuantityValue:
    """
    Summary:
        Immutable ledger value carrying value, unit, source, producer and provenance.

    Standard reference:
        Quantity identity and normative ownership come from the frozen SP16 ↔ SP554 DAG.

    Fields:
        quantity_id, value, unit, source_kind, producer_node_id, sequence and optional provenance.

    Validation:
        Values are type-checked against DAG quantity metadata before construction by the session engine.

    Used by:
        GuidedCalculationSession live calculation ledger and report-ready snapshot.
    """
    quantity_id: str
    value: Any
    unit: str | None
    source_kind: str
    producer_node_id: str
    sequence: int
    provenance: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "quantity_id": self.quantity_id,
            "value": self.value,
            "unit": self.unit,
            "source_kind": self.source_kind,
            "producer_node_id": self.producer_node_id,
            "sequence": self.sequence,
            "provenance": copy.deepcopy(self.provenance),
        }


@dataclass(frozen=True)
class TraceRecord:
    """
    Summary:
        Immutable deterministic execution/answer trace record for one DAG node.

    Standard reference:
        Normative references are copied from the exact frozen DAG node that produced or requested the value.

    Fields:
        sequence, node identity/type, event kind/status, inputs, outputs, selected edge, normative references and message.

    Validation:
        Sequence is assigned by the session engine; selected edges must originate from the recorded node.

    Used by:
        UI audit view, JSON calculation case persistence and future automatic report generation.
    """
    sequence: int
    node_id: str
    node_type: str
    event_kind: str
    status: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    selected_edge_id: str | None
    normative_refs: list[dict[str, Any]]
    message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": TRACE_SCHEMA,
            "sequence": self.sequence,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "event_kind": self.event_kind,
            "status": self.status,
            "inputs": copy.deepcopy(self.inputs),
            "outputs": copy.deepcopy(self.outputs),
            "selected_edge_id": self.selected_edge_id,
            "normative_refs": copy.deepcopy(self.normative_refs),
            "message": self.message,
        }


@dataclass
class ExecutionRegistry:
    """
    Summary:
        Explicit registry binding normative DAG calculation nodes to production Python executors.

    Standard reference:
        Each binding preserves the normative references and declared input/output quantities of its DAG node.

    Fields:
        executors maps node IDs to callables that consume current values and immutable node metadata.

    Validation:
        Missing registration blocks execution; returned quantity IDs are checked against the node's declared outputs.

    Used by:
        GuidedCalculationSession automatic execution of calculation/classification/lookup/compliance nodes.

    Implementation note:
        No formula may be reimplemented inside the UI engine; only frozen standard_core producers are admissible.

    

    An executor receives the complete current quantity-value mapping and the
    immutable DAG node.  It must return only quantity IDs declared by the node's
    ``produces`` bindings.  Missing registration blocks progression; nodes are
    never silently skipped.
    """

    executors: dict[str, Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]] = field(default_factory=dict)

    def register(self, node_id: str, executor: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]) -> None:
        if not node_id or not callable(executor):
            raise FireUIError("executor registration requires node_id and callable")
        self.executors[node_id] = executor

    def get(self, node_id: str):
        return self.executors.get(node_id)


class FireDAGModel:
    """
    Summary:
        Validated read-only index and UI-contract compiler for one frozen normative DAG snapshot.

    Standard reference:
        Uses the explicitly supplied compatible normative DAG snapshot; current UI1 baseline uses dag_v0.3.46_sp554_applicability_routing_hotfix.json.

    Fields:
        Graph, quantity/node indexes, incoming/outgoing edge indexes, producer/consumer indexes and canonical SHA-256.

    Validation:
        Rejects missing graph keys, duplicate IDs and edges referencing unknown nodes.

    Used by:
        GuidedCalculationSession, GuidedCalculationService and generated FIRE-UI0 UI contracts.
    """

    def __init__(self, graph: Mapping[str, Any], *, source_path: str | None = None, presentation_policy: Mapping[str, Any] | None = None):
        self.graph = copy.deepcopy(dict(graph))
        self.source_path = source_path
        self.presentation_policy = copy.deepcopy(dict(presentation_policy or {}))
        required = {"graph_id", "quantities", "nodes", "edges", "engine_contract"}
        missing = sorted(required.difference(self.graph))
        if missing:
            raise FireUIError(f"DAG missing required keys: {missing}")
        self.quantities = {q["id"]: q for q in self.graph["quantities"]}
        self.nodes = {n["id"]: n for n in self.graph["nodes"]}
        self.edges = list(self.graph["edges"])
        if len(self.quantities) != len(self.graph["quantities"]):
            raise FireUIError("duplicate quantity ids in DAG")
        if len(self.nodes) != len(self.graph["nodes"]):
            raise FireUIError("duplicate node ids in DAG")
        self.outgoing: dict[str, list[dict[str, Any]]] = {nid: [] for nid in self.nodes}
        self.incoming: dict[str, list[dict[str, Any]]] = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            a, b = edge["from_node_id"], edge["to_node_id"]
            if a not in self.nodes or b not in self.nodes:
                raise FireUIError(f"edge {edge.get('id')} references unknown node")
            self.outgoing[a].append(edge)
            self.incoming[b].append(edge)
        self.producer_nodes: dict[str, list[str]] = {qid: [] for qid in self.quantities}
        self.consumer_nodes: dict[str, list[str]] = {qid: [] for qid in self.quantities}
        for node in self.nodes.values():
            for binding in _fallback(node, "produces", []):
                qid = binding["quantity_id"]
                if qid in self.producer_nodes:
                    self.producer_nodes[qid].append(node["id"])
            for binding in _fallback(node, "consumes", []):
                qid = binding["quantity_id"]
                if qid in self.consumer_nodes:
                    self.consumer_nodes[qid].append(node["id"])
        canonical = json.dumps(self.graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.graph_sha256 = sha256(canonical).hexdigest()

    @classmethod
    def load(cls, path: str | Path, *, presentation_policy_path: str | Path | None = None) -> "FireDAGModel":
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            graph = json.load(fh)
        policy: dict[str, Any] = {}
        if presentation_policy_path is not None:
            pp = Path(presentation_policy_path)
            with pp.open("r", encoding="utf-8") as fh:
                policy = json.load(fh)
        return cls(graph, source_path=str(p), presentation_policy=policy)

    def ui_policy_for_node(self, node_id: str) -> dict[str, Any]:
        """Return UI/presentation metadata for one normative DAG node."""
        table = _fallback(self.presentation_policy, "node_presentation", {})
        value = table[node_id] if node_id in table else {}
        return copy.deepcopy(value)

    def guided_entry_node_id(self) -> str:
        """Return the presentation entry node without mutating normative DAG topology."""
        return str(_fallback(self.presentation_policy, "entry_node_id", DEFAULT_ENTRY_NODE_ID))

    def descendants(self, node_id: str) -> set[str]:
        if node_id not in self.nodes:
            raise FireUIError(f"unknown node_id: {node_id}")
        seen: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for edge in self.outgoing[current]:
                target = edge["to_node_id"]
                if target not in seen:
                    seen.add(target)
                    stack.append(target)
        seen.discard(node_id)
        return seen

    def quantity_widget(self, qid: str, *, required: bool = True) -> dict[str, Any]:
        q = self.quantities[qid]
        dtype = q.get("data_type")
        if dtype == "boolean":
            widget = "boolean_choice"
        elif dtype == "enum":
            widget = "select"
        elif dtype == "number":
            widget = "number"
        elif dtype in {"string", "text"}:
            widget = "text"
        else:
            widget = "structured_value"
        enum_values = copy.deepcopy(_fallback(q, "enum_values", []))
        # FIRE-UI2.1 invariant: every boolean exposed as an engineering selector
        # carries its concrete choices in the generated contract.  This keeps
        # the contract self-contained and prevents an empty dropdown even if a
        # frontend does not implement a boolean-specific fallback.
        if dtype == "boolean":
            enum_values = [{"value": True, "label": "Да"}, {"value": False, "label": "Нет"}]
        return {
            "quantity_id": qid,
            "label": q.get("name_ru") or qid,
            "symbol": q.get("symbol"),
            "data_type": dtype,
            "widget": widget,
            "canonical_unit": q.get("canonical_unit"),
            "allowed_units": copy.deepcopy(_fallback(q, "allowed_units", [])),
            "enum_values": enum_values,
            "source_policy": copy.deepcopy(_fallback(q, "source_policy", {})),
            "role": q.get("role"),
            "required": bool(required),
        }

    def node_card(self, node_id: str) -> dict[str, Any]:
        node = self.nodes[node_id]
        ntype = node["node_type"]
        ui_policy = self.ui_policy_for_node(node_id)
        card: dict[str, Any] = {
            "node_id": node_id,
            "node_type": ntype,
            "owner_standard_id": node.get("owner_standard_id"),
            "title": ui_policy.get("title") or node.get("title") or node_id,
            "normative_refs": copy.deepcopy(_fallback(node, "normative_refs", [])),
            "notes": copy.deepcopy(_fallback(node, "notes", {})),
            "interactive": ntype in {"input", "decision", "standard_handoff"},
            "read_only": ntype not in {"input", "decision", "standard_handoff"},
            "presentation": ui_policy,
            "hidden_in_primary_ui": node_id in set(_fallback(self.presentation_policy, "hidden_normative_nodes", [])),
            "deferred_stage": _fallback(self.presentation_policy, "deferred_nodes", {}).get(node_id),
        }
        if ntype == "decision":
            qid = node["decision_quantity_id"]
            card.update(
                {
                    "prompt": node.get("question") or node.get("title"),
                    "fields": [self.quantity_widget(qid, required=True)],
                    "options": copy.deepcopy(_fallback(node, "options", [])),
                    "submit_shape": "scalar",
                }
            )
        elif ntype in {"input", "standard_handoff"}:
            fields = [self.quantity_widget(b["quantity_id"], required=bool(b.get("required"))) for b in _fallback(node, "produces", [])]
            spec = _fallback(node, "input_spec", {})
            card.update(
                {
                    "prompt": spec.get("user_prompt") or node.get("title"),
                    "fields": fields,
                    "options": [],
                    "submit_shape": "scalar" if len(fields) == 1 else "object",
                    "external_handoff": ntype == "standard_handoff" and ui_policy.get("provenance_mode") != "optional",
                    "provenance_mode": ui_policy.get("provenance_mode", "required" if ntype == "standard_handoff" else "none"),
                    "target_standard_id": node.get("target_standard_id"),
                    "handoff_reason": node.get("reason"),
                }
            )
        else:
            card.update(
                {
                    "prompt": node.get("title"),
                    "fields": [],
                    "options": [],
                    "submit_shape": None,
                }
            )
        return card

    def build_ui_contract(self, *, entry_node_id: str | None = None) -> dict[str, Any]:
        entry_node_id = entry_node_id or self.guided_entry_node_id()
        if entry_node_id not in self.nodes:
            raise FireUIError(f"unknown entry node: {entry_node_id}")
        cards = [self.node_card(n["id"]) for n in self.graph["nodes"] if n["node_type"] in {"input", "decision", "standard_handoff", "result"}]
        # Global FIRE-UI2.1 selector census.  A generic enum/boolean selector
        # with no concrete choices is a package error, not a browser concern.
        selector_issues: list[dict[str, Any]] = []
        selector_field_count = 0
        boolean_selector_count = 0
        enum_selector_count = 0
        decision_selector_count = 0
        for card in cards:
            for field in _fallback(card, "fields", []):
                dtype = field.get("data_type")
                if dtype not in {"enum", "boolean"}:
                    continue
                selector_field_count += 1
                if dtype == "boolean":
                    boolean_selector_count += 1
                else:
                    enum_selector_count += 1
                if card.get("node_type") == "decision":
                    decision_selector_count += 1
                    options = _fallback(card, "options", []) or _fallback(field, "enum_values", [])
                else:
                    options = _fallback(field, "enum_values", [])
                if not options:
                    selector_issues.append({"node_id": card["node_id"], "quantity_id": field["quantity_id"], "data_type": dtype})
        if selector_issues:
            raise FireUIError(f"UI selector audit failed: {selector_issues}")
        return {
            "schema": UI_CONTRACT_SCHEMA,
            "graph_id": self.graph["graph_id"],
            "graph_sha256": self.graph_sha256,
            "entry_node_id": entry_node_id,
            "engine_contract": copy.deepcopy(self.graph["engine_contract"]),
            "counts": {
                "quantities": len(self.quantities),
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "interactive_nodes": sum(c["interactive"] for c in cards),
                "result_nodes": sum(c["node_type"] == "result" for c in cards),
            },
            "selector_audit": {
                "status": "PASS",
                "generic_selector_fields": selector_field_count,
                "boolean_selector_fields": boolean_selector_count,
                "enum_selector_fields": enum_selector_count,
                "decision_selector_fields": decision_selector_count,
                "empty_option_sets": 0,
            },
            "node_cards": cards,
            "ledger_contract": {
                "read_only_computed_values": True,
                "show_unit": True,
                "show_symbol": True,
                "show_source_kind": True,
                "show_producer_node_id": True,
                "show_normative_refs": True,
            },
            "trace_contract": {
                "schema": TRACE_SCHEMA,
                "deterministic_sequence": True,
                "wall_clock_time_required": False,
                "report_ready": True,
            },
            "presentation_policy": copy.deepcopy(self.presentation_policy),
            "navigation_policy": {
                "control_edge_types": ["control", "branch", "handoff"],
                "scheduler_model": "active_branch_queue_with_dependency_call_return",
                "parallel_navigation_edges_are_queued": True,
                "data_edges_are_dependency_edges": True,
                "data_only_consumer_may_continue_current_branch_when_no_navigation_edge": True,
                "dependency_producer_returns_to_suspended_consumer": True,
                "completed_nodes_are_not_reexecuted": True,
                "queued_nodes_recheck_applicability_before_execution": True,
                "session_complete_requires_no_pending_or_blocked_required_branches": True,
                "thermal_stage_waits_for_mechanical_queue": True,
                "ambiguous_dependency_producer_policy": "fail_closed",
            },
        }


def _condition_value(condition: Mapping[str, Any] | None, values: Mapping[str, Any]) -> bool | None:
    # FIRE-UI1.6 shares one condition evaluator with declarative calculation,
    # applicability and queue scheduling.
    from .fire_ui16_declarative import condition_value, DeclarativeExecutionError
    try:
        return condition_value(condition, values)
    except DeclarativeExecutionError as exc:
        raise FireUIError(str(exc)) from exc


def _validate_scalar(quantity: Mapping[str, Any], value: Any) -> Any:
    dtype = quantity.get("data_type")
    qid = quantity["id"]
    if dtype == "boolean":
        if not isinstance(value, bool):
            raise FireUIError(f"{qid} requires boolean")
        return value
    if dtype == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise FireUIError(f"{qid} requires finite number")
        return float(value)
    if dtype == "enum":
        allowed = [row["value"] for row in _fallback(quantity, "enum_values", [])]
        if value not in allowed:
            raise FireUIError(f"{qid} must be one of {allowed}")
        return value
    if dtype in {"string", "text"}:
        if not isinstance(value, str) or not value.strip():
            raise FireUIError(f"{qid} requires non-empty text")
        return value.strip()
    if value is None:
        raise FireUIError(f"{qid} cannot be null")
    return copy.deepcopy(value)


def _provenance_required(quantity: Mapping[str, Any], presentation_policy: Mapping[str, Any] | None = None) -> bool:
    source = _fallback(quantity, "source_policy", {}).get("primary_source_type")
    policy = dict(presentation_policy or {})
    prov = _fallback(policy, "provenance_policy", {})
    required_types = set(_fallback(prov, "required_primary_source_types", ["EXTERNAL_STANDARD_RESULT"]))
    return source in required_types


def _validate_provenance(provenance: Mapping[str, Any] | None, *, required: bool) -> dict[str, Any] | None:
    if provenance is None:
        if required:
            raise FireUIError("external/derived value requires provenance")
        return None
    if not isinstance(provenance, Mapping):
        raise FireUIError("provenance must be an object")
    result = copy.deepcopy(dict(provenance))
    if required:
        if not isinstance(result.get("source_document"), str) or not result["source_document"].strip():
            raise FireUIError("provenance.source_document is required")
        if not isinstance(result.get("source_reference"), str) or not result["source_reference"].strip():
            raise FireUIError("provenance.source_reference is required")
    return result


class GuidedCalculationSession:
    """
    Summary:
        Deterministic state machine implementing sequential questions, branch routing, ledger updates and trace capture.

    Standard reference:
        All prompts, quantities, branch conditions and normative references are sourced from the frozen DAG.

    Fields:
        Current node/status, quantity ledger, trace, interaction history, visited nodes and deterministic sequence counter.

    Validation:
        Answers are checked by quantity type/options/source policy; ambiguous or unexecutable paths fail closed.

    Used by:
        GuidedCalculationService and future local browser/desktop frontend adapters.
    """

    def __init__(self, model: FireDAGModel, *, entry_node_id: str | None = None, registry: ExecutionRegistry | None = None):
        entry_node_id = entry_node_id or model.guided_entry_node_id()
        if entry_node_id not in model.nodes:
            raise FireUIError(f"unknown entry node: {entry_node_id}")
        self.model = model
        self.entry_node_id = entry_node_id
        self.registry = registry or ExecutionRegistry()
        self.current_node_id: str | None = entry_node_id
        self.status = "AWAITING_INPUT"
        self.values: dict[str, QuantityValue] = {}
        self.trace: list[TraceRecord] = []
        self.interaction_history: list[dict[str, Any]] = []
        self.visited_node_ids: list[str] = []
        self.pending_node_ids: list[str] = []
        self.completed_node_ids: list[str] = []
        self.branch_failures: list[dict[str, Any]] = []
        self.branch_results: list[dict[str, Any]] = []
        self.dependency_call_stack: list[dict[str, str]] = []
        self._deferred_at_sequence: dict[str, int] = {}
        self._sequence = 0

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def plain_values(self) -> dict[str, Any]:
        return {qid: qv.value for qid, qv in self.values.items()}

    def current_card(self) -> dict[str, Any] | None:
        if self.current_node_id is None:
            return None
        card = self.model.node_card(self.current_node_id)
        card["session_status"] = self.status
        if not card["interactive"] and self.status.startswith("BLOCKED"):
            card["blocking_reason"] = self.status
        return card

    def ledger(self) -> list[dict[str, Any]]:
        rows = []
        for qv in sorted(self.values.values(), key=lambda x: (x.sequence, x.quantity_id)):
            q = self.model.quantities[qv.quantity_id]
            node = self.model.nodes[qv.producer_node_id] if qv.producer_node_id in self.model.nodes else {}
            rows.append(
                {
                    **qv.as_dict(),
                    "symbol": q.get("symbol"),
                    "name_ru": q.get("name_ru") or qv.quantity_id,
                    "role": q.get("role"),
                    "read_only": qv.source_kind not in {"USER_INPUT", "EXTERNAL_STANDARD_RESULT", "EXTERNAL_INPUT"},
                    "normative_refs": copy.deepcopy(_fallback(node, "normative_refs", [])),
                }
            )
        return rows

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": SESSION_SCHEMA,
            "graph_id": self.model.graph["graph_id"],
            "graph_sha256": self.model.graph_sha256,
            "entry_node_id": self.entry_node_id,
            "current_node_id": self.current_node_id,
            "status": self.status,
            "values": {qid: value.as_dict() for qid, value in sorted(self.values.items())},
            "ledger": self.ledger(),
            "trace": [row.as_dict() for row in self.trace],
            "interaction_history": copy.deepcopy(self.interaction_history),
            "visited_node_ids": list(self.visited_node_ids),
            "pending_node_ids": list(self.pending_node_ids),
            "completed_node_ids": list(self.completed_node_ids),
            "branch_failures": copy.deepcopy(self.branch_failures),
            "branch_results": copy.deepcopy(self.branch_results),
            "dependency_call_stack": copy.deepcopy(self.dependency_call_stack),
        }

    def _set_quantity(self, qid: str, value: Any, *, node_id: str, source_kind: str, provenance: Mapping[str, Any] | None = None) -> None:
        if qid not in self.model.quantities:
            raise FireUIError(f"executor produced unknown quantity: {qid}")
        quantity = self.model.quantities[qid]
        clean = _validate_scalar(quantity, value)
        prov = _validate_provenance(provenance, required=False)
        unit = quantity.get("canonical_unit")
        seq = self._sequence if self._sequence else 0
        self.values[qid] = QuantityValue(qid, clean, unit, source_kind, node_id, seq, prov)

    def _prepare_interactive_outputs(self, node: Mapping[str, Any], payload: Any, provenance: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, dict[str, Any] | None]]:
        bindings = _fallback(node, "produces", [])
        if node["node_type"] == "decision":
            qid = node["decision_quantity_id"]
            value = _validate_scalar(self.model.quantities[qid], payload)
            allowed = [x["value"] for x in _fallback(node, "options", [])]
            if allowed and value not in allowed:
                raise FireUIError(f"decision {node['id']} value must be one of {allowed}")
            return {qid: value}, {qid: None}
        if len(bindings) == 1:
            # A single produced quantity may itself be an object.  Treat the
            # submitted payload as that quantity value even when it is a Mapping.
            # Retain compatibility with the older explicitly wrapped shape
            # {"quantity_id": value} when it is unambiguous.
            qid = bindings[0]["quantity_id"]
            if isinstance(payload, Mapping) and len(payload) == 1 and qid in payload:
                payload_map = {qid: payload[qid]}
            else:
                payload_map = {qid: payload}
        else:
            if not isinstance(payload, Mapping):
                raise FireUIError(f"node {node['id']} requires object payload")
            payload_map = dict(payload)
        outputs: dict[str, Any] = {}
        prov_map: dict[str, dict[str, Any] | None] = {}
        for binding in bindings:
            qid = binding["quantity_id"]
            if qid not in payload_map:
                if bool(binding["required"]) if "required" in binding else False:
                    raise FireUIError(f"missing required field {qid}")
                continue
            quantity = self.model.quantities[qid]
            outputs[qid] = _validate_scalar(quantity, payload_map[qid])
            node_ui = self.model.ui_policy_for_node(node["id"])
            provenance_mode = node_ui.get("provenance_mode")
            required_prov = _provenance_required(quantity, self.model.presentation_policy)
            if provenance_mode == "optional":
                required_prov = False
            elif node["node_type"] == "standard_handoff":
                required_prov = True
            qprov = provenance
            if isinstance(provenance, Mapping) and qid in provenance and isinstance(provenance[qid], Mapping):
                qprov = provenance[qid]
            prov_map[qid] = _validate_provenance(qprov, required=required_prov)
        extras = set(payload_map).difference({b["quantity_id"] for b in bindings})
        if extras:
            raise FireUIError(f"unexpected fields for {node['id']}: {sorted(extras)}")
        return outputs, prov_map

    def _node_applicability(self, node_id: str) -> bool | None:
        node = self.model.nodes[node_id]
        return _condition_value(node.get("applicability"), self.plain_values())

    def _mark_completed(self, node_id: str) -> None:
        if node_id not in self.completed_node_ids:
            self.completed_node_ids.append(node_id)
        # Completed work must not remain as a stale duplicate in the parallel
        # queue.  This matters for stage handoffs that may have been queued
        # while another mechanical branch was still active.
        self.pending_node_ids=[nid for nid in self.pending_node_ids if nid != node_id]

    def _guided_excluded(self, node_id: str) -> bool:
        policy=self.model.presentation_policy
        if node_id in set(_fallback(policy, "guided_excluded_nodes", [])):
            return True
        return any(node_id.startswith(str(prefix)) for prefix in _fallback(policy, "guided_excluded_node_prefixes", []))

    def _clear_transient_failure(self, node_id: str) -> None:
        self.branch_failures = [row for row in self.branch_failures if row.get("node_id") != node_id]
        self._deferred_at_sequence.pop(node_id, None)

    def _stage_rank(self, node_id: str) -> int:
        """Prefer unresolved mechanical branches before thermal/protection stages."""
        node = self.model.nodes[node_id]
        ui = self.model.ui_policy_for_node(node_id)
        stage = str(ui.get("stage") or "")
        if stage in {"thermal_after_critical_temperature", "fire_protection_design", "post_actual_fire_resistance"}:
            return 50
        # SP16 is always part of the mechanical dependency frontier.
        if str(node.get("owner_standard_id")) == "SP16_2017":
            return 10
        # SP554 sections 8-11 are mechanical; section 12+ is thermal/result.
        sections=[]
        for ref in _fallback(node, "normative_refs", []):
            sec=ref.get("section")
            try: sections.append(float(str(sec).split('.')[0]))
            except (TypeError, ValueError): pass
        if sections and min(sections) >= 12:
            return 50
        if sections and min(sections) >= 8 and min(sections) < 12:
            return 10
        if node_id == "SP554_I_EXPOSURE":
            return 50
        return 20

    def _enqueue(self, node_ids: Sequence[str]) -> None:
        for nid in node_ids:
            if nid not in self.model.nodes or nid == self.current_node_id or nid in self.completed_node_ids or nid in self.pending_node_ids:
                continue
            self.pending_node_ids.append(nid)
        # Stable mechanical-first ordering; Python sort is stable for equal ranks.
        self.pending_node_ids.sort(key=self._stage_rank)

    def _next_pending(self) -> str | None:
        # Remove completed duplicates and skip branches that became inapplicable
        # after later quantities were resolved.
        unresolved: list[str] = []
        while self.pending_node_ids:
            nid=self.pending_node_ids.pop(0)
            if nid in self.completed_node_ids:
                continue
            state=self._node_applicability(nid)
            if state is False:
                self._mark_completed(nid)
                self._clear_transient_failure(nid)
                self.branch_results.append({"node_id":nid,"status":"SKIPPED_NOT_APPLICABLE"})
                continue
            if state is None:
                unresolved.append(nid)
                continue
            if unresolved:
                self._enqueue(unresolved)
            return nid
        if unresolved:
            self._enqueue(unresolved)
            return self.pending_node_ids.pop(0)
        return None

    def _node_is_declaratively_executable(self, node_id: str) -> bool:
        from .fire_ui16_declarative import can_execute_declarative
        return self.registry.get(node_id) is not None or can_execute_declarative(self.model.nodes[node_id])

    def _producer_for_quantity(self, qid: str, consumer_node_id: str) -> str | None:
        candidates=[]
        values=self.plain_values()
        for nid in self.model.producer_nodes.get(qid) or []:
            if nid == consumer_node_id or nid in self.completed_node_ids or self._guided_excluded(nid):
                continue
            if self._node_applicability(nid) is False:
                continue
            # Alternative producers are frequently distinguished by the branch
            # condition of the edge that enters them (catalog vs arbitrary,
            # rolled J4 vs built-up J5, etc.). Respect those conditions during
            # dependency resolution instead of treating every producer as viable.
            incoming_nav=[e for e in self.model.incoming.get(nid) or [] if e.get("edge_type") in {"control","branch","handoff"}]
            if incoming_nav:
                states=[]
                for e in incoming_nav:
                    try: states.append(_condition_value(e.get("condition"),values))
                    except FireUIError: states.append(None)
                if all(st is False for st in states):
                    continue
                # If all routes are unresolved, keep the candidate but ambiguity
                # handling below will fail closed rather than inventing a route.
            node=self.model.nodes[nid]
            if node["node_type"] in {"input","decision","standard_handoff"} or self._node_is_declaratively_executable(nid):
                candidates.append(nid)
        if not candidates:
            return None
        # Prefer the owner standard of the waiting consumer, then a unique candidate.
        owner=self.model.nodes[consumer_node_id].get("owner_standard_id")
        same=[nid for nid in candidates if self.model.nodes[nid].get("owner_standard_id")==owner]
        if len(same)==1:
            return same[0]
        if len(candidates)==1:
            return candidates[0]
        # Prefer an already pending producer: this preserves an existing branch order.
        pending=[nid for nid in candidates if nid in self.pending_node_ids]
        if len(pending)==1:
            return pending[0]
        return None

    def _schedule_missing_dependency(self, consumer_node_id: str, missing: Sequence[str]) -> bool:
        for qid in missing:
            producer=self._producer_for_quantity(qid, consumer_node_id)
            if producer is None:
                continue
            if producer in self.pending_node_ids:
                self.pending_node_ids.remove(producer)
            self.dependency_call_stack.append({"callee_node_id":producer,"return_node_id":consumer_node_id,"quantity_id":qid})
            self.current_node_id=producer
            self.status="ADVANCING_DEPENDENCY"
            return True
        return False

    def _applicable_outgoing(self, node_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        values=self.plain_values()
        nav=[]; data=[]; unresolved=[]
        for edge in self.model.outgoing[node_id]:
            try:
                state=_condition_value(edge.get("condition"),values)
            except FireUIError:
                state=None
            if state is None:
                unresolved.append(edge); continue
            if state is not True:
                continue
            if edge.get("edge_type") in {"control","branch","handoff"}:
                nav.append(edge)
            elif edge.get("edge_type")=="data":
                data.append(edge)
        return nav,data,unresolved

    def _apply_navigation_override(self, node_id: str) -> list[dict[str, Any]]:
        overrides=_fallback(self.model.presentation_policy,"navigation_overrides",{})
        if node_id not in overrides:
            return []
        values=self.plain_values(); matched=[]
        for rule in overrides[node_id]:
            when=rule.get("when") or {}
            qid=when.get("quantity_id")
            if qid in values and values[qid]==when.get("value"):
                matched.append({"id":rule["id"],"from_node_id":node_id,"to_node_id":rule["to_node_id"],"edge_type":"control","condition":None,"quantity_ids":[]})
        if len(matched)>1:
            raise FireUIBlocked(f"AMBIGUOUS_UI_NAVIGATION_OVERRIDE:{node_id}")
        return matched

    def _select_outgoing_edge(self, node_id: str) -> dict[str, Any] | None:
        """Compatibility helper: return the first deterministic navigation edge.

        FIRE-UI1.6 itself schedules all applicable branches in `_advance_after_node`.
        """
        over=self._apply_navigation_override(node_id)
        if over: return over[0]
        nav,_,unresolved=self._applicable_outgoing(node_id)
        if len(nav)==1: return nav[0]
        if len(nav)>1: return sorted(nav,key=lambda e:(self._stage_rank(e["to_node_id"]),e["id"]))[0]
        if unresolved: raise FireUIBlocked(f"UNRESOLVED_BRANCH_CONDITION:{node_id}")
        return None

    def _record_selected_edge(self, node_id: str, edge_id: str | None) -> None:
        if self.trace and self.trace[-1].node_id==node_id:
            prev=self.trace[-1]
            self.trace[-1]=TraceRecord(prev.sequence,prev.node_id,prev.node_type,prev.event_kind,prev.status,
                prev.inputs,prev.outputs,edge_id,prev.normative_refs,prev.message)

    def _finish_or_continue(self, node_id: str, *, no_navigation: bool = False) -> None:
        nxt=self._next_pending()
        if nxt is not None:
            self.current_node_id=nxt; self.status="ADVANCING_BRANCH"; self._auto_progress(); return
        # A parallel support branch may legitimately end after the governing
        # result branch has already completed.  Restore that result instead of
        # turning the last support-leaf into a false session dead end/COMPLETE.
        for row in reversed(self.branch_results):
            if row.get("status") in {"RESULT","TERMINAL_RESULT"} and row.get("node_id") in self.model.nodes:
                self.current_node_id=row["node_id"]
                self.status="RESULT"
                return
        self.current_node_id=None
        # With no previously resolved result, a non-result leaf after the
        # verification plan is a real routing defect and remains fail-closed.
        if "verification_plan" in self.values and no_navigation and self.model.nodes[node_id]["node_type"]!="result":
            self.status=f"BLOCKED_NO_NAVIGATION_EDGE:{node_id}"
        else:
            self.status="COMPLETE"

    def _advance_after_node(self, node_id: str) -> None:
        self._mark_completed(node_id)
        # A dependency call is a true call/return.  Do not follow the producer's
        # ordinary downstream UI route when it was invoked solely to resolve a
        # required quantity for another branch.
        if self.dependency_call_stack and self.dependency_call_stack[-1]["callee_node_id"]==node_id:
            call=self.dependency_call_stack.pop()
            self.current_node_id=call["return_node_id"]
            self.status="ADVANCING_DEPENDENCY_RETURN"
            self._record_selected_edge(node_id,None)
            self._auto_progress(); return

        override=self._apply_navigation_override(node_id)
        nav,data,unresolved=self._applicable_outgoing(node_id)
        if override:
            nav=override
        # FIRE-UI1.6: data edges are dependency relations, not guided branches.
        # They are resolved lazily by _schedule_missing_dependency when an active
        # control/branch/handoff node actually requires their quantity.  Blindly
        # queueing every data consumer activates mutually exclusive/alternative
        # producers (e.g. arbitrary geometry, mono-I LTB) and is therefore wrong.
        # Parallel guided verification branches are represented only by applicable
        # control/branch/handoff edges and remain queued independently.
        nav=sorted(nav,key=lambda e:(self._stage_rank(e["to_node_id"]),e["id"]))
        targets=[e["to_node_id"] for e in nav]
        if targets:
            primary=targets[0]
            self._enqueue(targets[1:])
            self.current_node_id=primary
            self.status="ADVANCING"
            self._record_selected_edge(node_id,nav[0]["id"])
            self._auto_progress(); return
        # A calculation/lookup often continues only through data edges. Follow
        # those consumers lazily *only when no explicit navigation exists*.
        # This preserves formula pipelines (e.g. psi -> phi, mu -> gammaE)
        # without the invalid global fan-out from geometry/material producers.
        data_cont=[]
        for e in data:
            tid=e["to_node_id"]; target=self.model.nodes[tid]
            if self._guided_excluded(tid):
                continue
            if target["node_type"] in {"input","decision","standard_handoff"}:
                continue
            if self._node_applicability(tid) is not True:
                continue
            data_cont.append(e)
        data_cont=sorted(data_cont,key=lambda e:(self._stage_rank(e["to_node_id"]),e["id"]))
        if data_cont:
            primary=data_cont[0]["to_node_id"]
            self._enqueue([e["to_node_id"] for e in data_cont[1:]])
            self.current_node_id=primary
            self.status="ADVANCING_DATA_CONTINUATION"
            self._record_selected_edge(node_id,data_cont[0]["id"])
            self._auto_progress(); return
        if unresolved:
            # If another already-resolved parallel branch exists, continue it;
            # otherwise preserve a diagnostic instead of inventing a route.
            nxt=self._next_pending()
            if nxt is not None:
                self.branch_failures.append({"node_id":node_id,"status":"UNRESOLVED_BRANCH_CONDITION","edge_ids":[e["id"] for e in unresolved]})
                self.current_node_id=nxt; self.status="ADVANCING_BRANCH"; self._auto_progress(); return
            self.current_node_id=node_id
            self.status=f"BLOCKED_UNRESOLVED_BRANCH_CONDITION:{node_id}"
            return
        self.branch_results.append({"node_id":node_id,"status":"BRANCH_COMPLETE"})
        self._finish_or_continue(node_id,no_navigation=True)

    def _auto_progress(self) -> None:
        from .fire_ui16_declarative import can_execute_declarative, execute_declarative, required_missing, condition_quantity_ids, DeclarativeExecutionError
        safety=0
        while self.current_node_id is not None:
            safety+=1
            if safety>5000:
                self.status="BLOCKED_SCHEDULER_LOOP_GUARD"; return
            node=self.model.nodes[self.current_node_id]; nid=node["id"]; ntype=node["node_type"]
            # Re-evaluate queued-node applicability immediately before execution.
            app=self._node_applicability(nid)
            if app is False:
                self._mark_completed(nid)
                self._clear_transient_failure(nid)
                self.branch_results.append({"node_id":nid,"status":"SKIPPED_NOT_APPLICABLE"})
                nxt=self._next_pending()
                if nxt is None:
                    # A late skipped parallel branch must not overwrite a
                    # governing RESULT already obtained by another branch.
                    self._finish_or_continue(nid,no_navigation=False)
                    return
                self.current_node_id=nxt; continue
            if app is None:
                qids=sorted(q for q in condition_quantity_ids(node.get("applicability")) if q not in self.values)
                if qids and self._schedule_missing_dependency(nid,qids):
                    continue
                nxt=self._next_pending()
                if nxt is not None and self._stage_rank(nxt) < 50 and self._deferred_at_sequence.get(nid) != self._sequence:
                    self._deferred_at_sequence[nid]=self._sequence
                    self._enqueue([nid])
                    self.current_node_id=nxt; self.status="DEFERRED_UNRESOLVED_APPLICABILITY"; continue
                if nxt is not None:
                    self._enqueue([nxt])
                self.current_node_id=nid; self.status=f"BLOCKED_UNRESOLVED_APPLICABILITY:{nid}"; return

            if ntype in {"input","decision","standard_handoff"}:
                auto=_fallback(self.model.presentation_policy,"auto_answers",{})
                if nid in auto:
                    payload=copy.deepcopy(auto[nid]); seq=self._next_sequence()
                    outputs,prov_map=self._prepare_interactive_outputs(node,payload,None)
                    for qid,value in outputs.items():
                        self.values[qid]=QuantityValue(qid,value,self.model.quantities[qid].get("canonical_unit"),"AUTO_RESOLVED",nid,seq,prov_map.get(qid))
                    self.visited_node_ids.append(nid)
                    self.trace.append(TraceRecord(seq,nid,ntype,"auto_answer","COMPLETE",{},outputs,None,copy.deepcopy(_fallback(node,"normative_refs",[])),"Auto-resolved by presentation policy"))
                    self._advance_after_node(nid)
                    if self.status.startswith("AWAITING") or self.status.startswith("BLOCKED") or self.status in {"RESULT","COMPLETE"}: return
                    continue
                self.status="AWAITING_INPUT"; return

            if ntype=="result":
                self._mark_completed(nid)
                ui=self.model.ui_policy_for_node(nid)
                terminal=bool(ui.get("terminal_result"))
                continue_after_result=bool(ui.get("continue_after_result"))
                self.branch_results.append({"node_id":nid,"status":"TERMINAL_RESULT" if terminal else "RESULT"})
                if terminal:
                    # A fail-closed partial/unsupported summary is the terminal
                    # mechanical outcome. Do not silently proceed into thermal
                    # stages with an incomplete verification plan.
                    self.pending_node_ids=[x for x in self.pending_node_ids if self._stage_rank(x)<50]
                    nxt=self._next_pending()
                    if nxt is not None:
                        self.current_node_id=nxt; self.status="ADVANCING_BRANCH"; continue
                    self.status="RESULT"; return
                if continue_after_result:
                    # FIRE-UI1.8: a non-terminal result can be a stage summary
                    # with an explicit downstream handoff (FIRE-D2 -> FIRE-D3).
                    # The thermal continuation must not bypass unresolved
                    # mechanical branches already queued by the parallel DAG.
                    mechanical_pending=[x for x in self.pending_node_ids if self._stage_rank(x)<50 and x not in self.completed_node_ids]
                    if mechanical_pending:
                        nav,_,unresolved=self._applicable_outgoing(nid)
                        if unresolved:
                            self.status=f"BLOCKED_UNRESOLVED_BRANCH_CONDITION:{nid}"
                            return
                        continuation=[e["to_node_id"] for e in sorted(nav,key=lambda e:(self._stage_rank(e["to_node_id"]),e["id"]))]
                        self._enqueue(continuation)
                        nxt=self._next_pending()
                        if nxt is not None:
                            self.current_node_id=nxt
                            self.status="ADVANCING_MECHANICAL_BEFORE_RESULT_CONTINUATION"
                            continue
                    self._advance_after_node(nid)
                    if self.status.startswith("AWAITING") or self.status.startswith("BLOCKED") or self.status in {"RESULT","COMPLETE"}:
                        return
                    continue
                nxt=self._next_pending()
                if nxt is not None:
                    self.current_node_id=nxt; self.status="ADVANCING_BRANCH"; continue
                self.status="RESULT"; return

            values=self.plain_values()
            missing=required_missing(node,values)
            if missing:
                if self._schedule_missing_dependency(nid,missing):
                    continue
                nxt=self._next_pending()
                if nxt is not None and self._stage_rank(nxt) < 50 and self._deferred_at_sequence.get(nid) != self._sequence:
                    self._deferred_at_sequence[nid]=self._sequence
                    self._enqueue([nid])
                    self.current_node_id=nxt; self.status="DEFERRED_MISSING_INPUTS"; continue
                if nxt is not None:
                    self._enqueue([nxt])
                failure={"node_id":nid,"status":"MISSING_INPUTS","quantity_ids":list(missing)}
                self.branch_failures.append(failure)
                self.status=f"BLOCKED_MISSING_INPUTS:{nid}:{','.join(missing)}"; return

            executor=self.registry.get(nid)
            seq=self._next_sequence()
            consumed={b["quantity_id"]:self.values[b["quantity_id"]].value for b in _fallback(node,"consumes",[]) if b["quantity_id"] in self.values}
            try:
                if executor is not None:
                    raw=executor(values,node)
                elif can_execute_declarative(node):
                    raw=execute_declarative(self.model,node,values)
                else:
                    raise DeclarativeExecutionError("no registered or declarative executor")
            except (FireUIError, DeclarativeExecutionError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
                failure={"node_id":nid,"status":"EXECUTION_FAILED","message":str(exc)}
                self.branch_failures.append(failure)
                nxt=self._next_pending()
                if nxt is not None:
                    self._mark_completed(nid); self.current_node_id=nxt; self.status="ADVANCING_BRANCH_AFTER_FAILURE"; continue
                if executor is None and not can_execute_declarative(node):
                    self.status=f"BLOCKED_EXECUTOR_REQUIRED:{nid}"
                else:
                    self.status=f"BLOCKED_EXECUTION_FAILED:{nid}:{exc}"
                return
            if not isinstance(raw,Mapping): raise FireUIError(f"executor for {nid} must return mapping")
            declared={b["quantity_id"] for b in _fallback(node,"produces",[])}
            if set(raw).difference(declared): raise FireUIError(f"executor {nid} returned undeclared outputs {sorted(set(raw).difference(declared))}")
            for binding in _fallback(node,"produces",[]):
                qid=binding["quantity_id"]
                if binding.get("required") and qid not in raw: raise FireUIError(f"executor {nid} omitted required output {qid}")
            for qid,value in raw.items():
                self.values[qid]=QuantityValue(qid,_validate_scalar(self.model.quantities[qid],value),self.model.quantities[qid].get("canonical_unit"),"CALCULATED",nid,seq,{"executor_node_id":nid,"declarative":executor is None})
            self.visited_node_ids.append(nid)
            self._clear_transient_failure(nid)
            self.trace.append(TraceRecord(seq,nid,ntype,"calculation","COMPLETE",consumed,dict(raw),None,copy.deepcopy(_fallback(node,"normative_refs",[]))))
            self._advance_after_node(nid)
            if self.status.startswith("AWAITING") or self.status.startswith("BLOCKED") or self.status in {"RESULT","COMPLETE"}: return

    def submit(self, payload: Any, *, provenance: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if self.current_node_id is None:
            raise FireUIError("session is complete")
        node = self.model.nodes[self.current_node_id]
        if node["node_type"] not in {"input", "decision", "standard_handoff"}:
            raise FireUIBlocked(f"current node {node['id']} is not interactive")
        seq = self._next_sequence()
        outputs, prov_map = self._prepare_interactive_outputs(node, payload, provenance)
        source = "EXTERNAL_STANDARD_RESULT" if node["node_type"] == "standard_handoff" else "USER_INPUT"
        for qid, value in outputs.items():
            self.values[qid] = QuantityValue(
                qid,
                value,
                self.model.quantities[qid].get("canonical_unit"),
                source,
                node["id"],
                seq,
                prov_map.get(qid),
            )
        self.visited_node_ids.append(node["id"])
        self.interaction_history.append({"node_id": node["id"], "payload": copy.deepcopy(payload), "provenance": copy.deepcopy(provenance)})
        self.trace.append(
            TraceRecord(seq, node["id"], node["node_type"], "answer", "COMPLETE", {}, outputs, None, copy.deepcopy(_fallback(node, "normative_refs", [])))
        )
        try:
            self._advance_after_node(node["id"])
        except FireUIBlocked as exc:
            self.status = f"BLOCKED:{exc}"
        return self.snapshot()

    def edit_answer(self, node_id: str, payload: Any, *, provenance: Mapping[str, Any] | None = None) -> dict[str, Any]:
        indices = [i for i, row in enumerate(self.interaction_history) if row["node_id"] == node_id]
        if not indices:
            raise FireUIError(f"node {node_id} has not been answered")
        idx = indices[0]
        prior = copy.deepcopy(self.interaction_history[:idx])
        self.current_node_id = self.entry_node_id
        self.status = "AWAITING_INPUT"
        self.values.clear()
        self.trace.clear()
        self.interaction_history.clear()
        self.visited_node_ids.clear()
        self.pending_node_ids.clear()
        self.completed_node_ids.clear()
        self.branch_failures.clear()
        self.branch_results.clear()
        self.dependency_call_stack.clear()
        self._sequence = 0
        for row in prior:
            if self.current_node_id != row["node_id"]:
                raise FireUIError("cannot replay history after DAG/branch inconsistency")
            self.submit(row["payload"], provenance=row.get("provenance"))
        if self.current_node_id != node_id:
            raise FireUIError("edited node is no longer reachable after replay")
        return self.submit(payload, provenance=provenance)

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != SESSION_SCHEMA:
            raise FireUIError("unsupported session schema")
        if snapshot.get("graph_id") != self.model.graph["graph_id"] or snapshot.get("graph_sha256") != self.model.graph_sha256:
            raise FireUIError("session DAG identity mismatch")
        history = copy.deepcopy(_fallback(snapshot, "interaction_history", []))
        self.current_node_id = self.entry_node_id
        self.status = "AWAITING_INPUT"
        self.values.clear(); self.trace.clear(); self.interaction_history.clear(); self.visited_node_ids.clear()
        self.pending_node_ids.clear(); self.completed_node_ids.clear(); self.branch_failures.clear(); self.branch_results.clear(); self.dependency_call_stack.clear(); self._deferred_at_sequence.clear(); self._sequence = 0
        for row in history:
            if self.current_node_id != row["node_id"]:
                raise FireUIError("stored interaction history does not replay on this DAG")
            self.submit(row["payload"], provenance=row.get("provenance"))


class GuidedCalculationService:
    """
    Summary:
        In-memory application service managing multiple guided FIRE-UI0 calculation sessions.

    Standard reference:
        Delegates all normative navigation and value metadata to FireDAGModel/GuidedCalculationSession.

    Fields:
        Shared frozen model, executor registry, deterministic local session IDs and session map.

    Validation:
        Unknown session IDs are rejected; all submitted/edit payloads are validated by the session engine.

    Used by:
        Future thin FastAPI/local HTTP adapter or desktop launcher; no public server is required.
    """

    def __init__(self, model: FireDAGModel, *, registry: ExecutionRegistry | None = None):
        self.model = model
        self.registry = registry or ExecutionRegistry()
        self.sessions: dict[str, GuidedCalculationSession] = {}
        self._counter = 0

    def create_session(self) -> dict[str, Any]:
        self._counter += 1
        sid = f"fire-{self._counter:06d}"
        session = GuidedCalculationSession(self.model, registry=self.registry)
        self.sessions[sid] = session
        return {"session_id": sid, "state": session.snapshot(), "current_card": session.current_card()}

    def get_session(self, session_id: str) -> GuidedCalculationSession:
        if session_id not in self.sessions:
            raise FireUIError("unknown session_id")
        return self.sessions[session_id]

    def submit(self, session_id: str, payload: Any, *, provenance: Mapping[str, Any] | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        state = session.submit(payload, provenance=provenance)
        return {"session_id": session_id, "state": state, "current_card": session.current_card()}

    def edit(self, session_id: str, node_id: str, payload: Any, *, provenance: Mapping[str, Any] | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        state = session.edit_answer(node_id, payload, provenance=provenance)
        return {"session_id": session_id, "state": state, "current_card": session.current_card()}
