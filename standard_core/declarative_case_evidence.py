"""Runtime audit evidence for declarative case/rule selection.

The normative/declarative executor remains the sole engineering calculation
path.  This module wraps that executor after successful execution and records
which frozen expression case, classification rule, or check condition was used.
It never evaluates the selected engineering expression a second time.

Evidence is keyed by graph SHA, node id, the trace-visible consumed inputs and
the actual production outputs, so replay after editing an earlier answer cannot
reuse evidence from a stale branch.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from threading import RLock
from typing import Any, Mapping

_INSTALLED = False
_LOCK = RLock()
_CACHE: dict[str, dict[str, Any]] = {}
_ORIGINAL_EXECUTE = None


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    )


def _consumed_values(node: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for binding in node.get("consumes") or []:
        qid = binding.get("quantity_id")
        if isinstance(qid, str) and qid in values:
            out[qid] = copy.deepcopy(values[qid])
    return out


def evidence_cache_key(
    model: Any,
    node: Mapping[str, Any],
    trace_inputs: Mapping[str, Any],
    outputs: Mapping[str, Any],
) -> str:
    payload = {
        "graph_sha256": getattr(model, "graph_sha256", None),
        "node_id": node.get("id"),
        "inputs": copy.deepcopy(dict(trace_inputs)),
        "outputs": copy.deepcopy(dict(outputs)),
    }
    return sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _capture_case_evidence(
    model: Any,
    node: Mapping[str, Any],
    values: Mapping[str, Any],
    outputs: Mapping[str, Any],
) -> dict[str, Any] | None:
    del model  # graph identity is carried by the cache key; no model data are mutated.
    from . import fire_ui16_declarative as decl

    base: dict[str, Any] = {
        "capture_status": "CAPTURED",
        "capture_phase": "immediately_after_successful_declarative_execution",
        "node_id": node.get("id"),
        "outputs": copy.deepcopy(dict(outputs)),
        "result_recomputed": False,
        "expression_recomputed": False,
    }

    rules = node.get("classification_rules")
    if rules and node.get("output_quantity_id"):
        matches: list[tuple[int, Mapping[str, Any]]] = []
        for index, rule in enumerate(rules):
            if decl.condition_value(rule.get("when"), values) is True:
                matches.append((index, rule))
        base["kind"] = "classification"
        if len(matches) == 1:
            index, rule = matches[0]
            base.update(
                {
                    "selection_mode": "classification_rule",
                    "selected_rule_index": index,
                    "selected_rule": copy.deepcopy(dict(rule)),
                }
            )
        elif not matches and node.get("fallback_behavior") == "explicit_value" and "fallback_value" in node:
            base.update(
                {
                    "selection_mode": "classification_fallback",
                    "fallback_value": copy.deepcopy(node.get("fallback_value")),
                }
            )
        else:
            # A successful production execution should not normally reach this
            # state. Keep it fail-transparent rather than inventing a rule.
            base["capture_status"] = "SUCCESSFUL_EXECUTION_BUT_RULE_SELECTION_UNRESOLVED"
            base["matching_rule_count"] = len(matches)
        return base

    if node.get("check_condition") is not None:
        base.update(
            {
                "kind": "check_condition",
                "selection_mode": "check_condition",
                "condition": copy.deepcopy(node.get("check_condition")),
            }
        )
        return base

    spec = node.get("calculation_spec") or node.get("check_spec")
    if not isinstance(spec, Mapping):
        return None

    base["kind"] = "expression"
    expression = spec.get("expression")
    if isinstance(expression, str) and expression:
        base.update(
            {
                "selection_mode": "single_expression",
                "selected_expression": expression,
                "selected_case_index": None,
                "selected_case": None,
            }
        )
        return base

    cases = list(spec.get("cases") or [])
    if not cases:
        return None

    matches: list[tuple[int, Mapping[str, Any]]] = []
    for index, case in enumerate(cases):
        if decl.condition_value(case.get("when"), values) is True:
            matches.append((index, case))
    if len(matches) == 1:
        index, case = matches[0]
        base.update(
            {
                "selection_mode": "piecewise_case",
                "selected_case_index": index,
                "selected_case": copy.deepcopy(dict(case)),
                "selected_expression": case.get("expression"),
            }
        )
    else:
        base["capture_status"] = "SUCCESSFUL_EXECUTION_BUT_CASE_SELECTION_UNRESOLVED"
        base["matching_case_count"] = len(matches)
    return base


def _instrumented_execute(model: Any, node: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    assert _ORIGINAL_EXECUTE is not None
    outputs = _ORIGINAL_EXECUTE(model, node, values)
    # Lookup row/interpolation evidence is owned by declarative_runtime_evidence.
    # This layer captures only expression/rule/check selection.
    if not node.get("lookup_spec"):
        evidence = _capture_case_evidence(model, node, values, outputs)
        if evidence is not None:
            trace_inputs = _consumed_values(node, values)
            key = evidence_cache_key(model, node, trace_inputs, outputs)
            with _LOCK:
                _CACHE[key] = evidence
    return outputs


def install() -> None:
    """Install the transparent case-selection hook once for this process."""
    global _INSTALLED, _ORIGINAL_EXECUTE
    if _INSTALLED:
        return
    from . import fire_ui16_declarative as decl

    _ORIGINAL_EXECUTE = decl.execute_declarative
    decl.execute_declarative = _instrumented_execute
    _INSTALLED = True


def get_case_runtime_evidence(
    model: Any,
    node_id: str,
    trace_inputs: Mapping[str, Any],
    trace_outputs: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return matching runtime case/rule/check evidence for a completed trace row."""
    node = getattr(model, "nodes", {}).get(node_id)
    if not isinstance(node, Mapping) or node.get("lookup_spec"):
        return None
    key = evidence_cache_key(model, node, trace_inputs, trace_outputs)
    with _LOCK:
        evidence = _CACHE.get(key)
    return copy.deepcopy(evidence) if evidence is not None else None


def clear_case_runtime_evidence_cache() -> None:
    """Test helper; calculation/session state is unaffected."""
    with _LOCK:
        _CACHE.clear()
