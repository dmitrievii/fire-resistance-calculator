"""Runtime audit evidence for declarative DAG execution.

This module instruments ``fire_ui16_declarative.execute_declarative`` without
changing any engineering result.  The existing executor remains the sole
calculation path.  After a successful lookup, the instrumentation records which
immutable dataset rows bracketed the already-resolved selector so REPORT-IR can
show auditable table/interpolation evidence without recalculating the result.

The evidence cache is deterministic and keyed by graph SHA, node id, selector
values and actual executor outputs.  It is therefore replay-safe: stale evidence
cannot match a changed trace after ``GuidedCalculationSession.edit_answer``.
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
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def _lookup_selector_values(node: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    spec = node.get("lookup_spec") or {}
    out: dict[str, Any] = {}
    for binding in spec.get("selector_bindings") or []:
        qid = binding.get("quantity_id")
        if qid in values:
            out[str(qid)] = copy.deepcopy(values[qid])
    return out


def evidence_cache_key(model: Any, node: Mapping[str, Any], values: Mapping[str, Any], outputs: Mapping[str, Any]) -> str:
    payload = {
        "graph_sha256": getattr(model, "graph_sha256", None),
        "node_id": node.get("id"),
        "selectors": _lookup_selector_values(node, values),
        "outputs": copy.deepcopy(dict(outputs)),
    }
    return sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _row_record(index: int, role: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {"row_index": int(index), "role": role, "row": copy.deepcopy(dict(row))}


def _capture_lookup_rows(model: Any, node: Mapping[str, Any], values: Mapping[str, Any], outputs: Mapping[str, Any]) -> dict[str, Any]:
    # Reuse the same immutable dataset loader as the production declarative
    # executor.  This routine selects evidence rows only; it never interpolates
    # or derives an engineering output.
    from . import fire_ui16_declarative as decl

    spec = node.get("lookup_spec") or {}
    dataset_id = str(spec["dataset_id"])
    ds = decl._dataset(model, dataset_id)
    rows = decl._rows_for_dataset(model, ds)
    selector_bindings = list(spec.get("selector_bindings") or [])
    selectors = {
        b["dataset_field"]: values[b["quantity_id"]]
        for b in selector_bindings
        if b["quantity_id"] in values
    }
    if len(selectors) != len(selector_bindings):
        return {
            "kind": "lookup",
            "dataset_id": dataset_id,
            "capture_status": "SELECTOR_VALUES_INCOMPLETE",
            "result_recomputed": False,
            "outputs": copy.deepcopy(dict(outputs)),
        }

    interpolation = spec.get("interpolation") or {}
    method = str(interpolation.get("method") or "none")
    evidence: dict[str, Any] = {
        "kind": "lookup",
        "dataset_id": dataset_id,
        "capture_status": "CAPTURED",
        "capture_phase": "immediately_after_successful_declarative_lookup",
        "selector_fields": copy.deepcopy(selectors),
        "selector_quantity_values": _lookup_selector_values(node, values),
        "interpolation": copy.deepcopy(dict(interpolation)),
        "selected_rows": [],
        "result_recomputed": False,
        "outputs": copy.deepcopy(dict(outputs)),
    }

    indexed = list(enumerate(rows))
    if method == "none":
        matches = [(i, r) for i, r in indexed if all(r.get(k) == v for k, v in selectors.items())]
        if len(matches) == 1:
            i, row = matches[0]
            evidence["selected_rows"] = [_row_record(i, "exact", row)]
            evidence["selection_mode"] = "exact"
        else:
            evidence["capture_status"] = "ROW_SELECTION_AMBIGUOUS"
            evidence["selection_match_count"] = len(matches)
        return evidence

    axis_text = str(interpolation.get("axis") or "")
    axes = [x.strip() for x in axis_text.split(",") if x.strip()]
    if method == "linear" and len(axes) == 1:
        ax = axes[0]
        x = float(selectors[ax])
        cats = {k: v for k, v in selectors.items() if k != ax}
        cand = sorted(
            [(i, r) for i, r in indexed if all(r.get(k) == v for k, v in cats.items())],
            key=lambda pair: float(pair[1][ax]),
        )
        exact = [(i, r) for i, r in cand if float(r[ax]) == x]
        if exact:
            i, row = exact[0]
            evidence["selected_rows"] = [_row_record(i, "exact", row)]
            evidence["selection_mode"] = "linear_exact_knot"
            evidence["axis"] = ax
            evidence["axis_value"] = x
            evidence["fraction"] = 0.0
            return evidence
        lo = [(i, r) for i, r in cand if float(r[ax]) < x]
        hi = [(i, r) for i, r in cand if float(r[ax]) > x]
        if not lo or not hi:
            evidence["capture_status"] = "OUTSIDE_INTERPOLATION_DOMAIN"
            return evidence
        ia, a = lo[-1]
        ib, b = hi[0]
        x0, x1 = float(a[ax]), float(b[ax])
        evidence["selected_rows"] = [_row_record(ia, "lower", a), _row_record(ib, "upper", b)]
        evidence["selection_mode"] = "linear_bracket"
        evidence["axis"] = ax
        evidence["axis_value"] = x
        evidence["axis_lower"] = x0
        evidence["axis_upper"] = x1
        evidence["fraction"] = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
        return evidence

    if method == "bilinear" and len(axes) == 2:
        ax, ay = axes
        x, y = float(selectors[ax]), float(selectors[ay])
        cats = {k: v for k, v in selectors.items() if k not in axes}
        cand = [(i, r) for i, r in indexed if all(r.get(k) == v for k, v in cats.items())]
        xs = sorted({float(r[ax]) for _, r in cand})
        ys = sorted({float(r[ay]) for _, r in cand})

        def bracket(vals: list[float], z: float) -> tuple[float, float] | None:
            if z in vals:
                return z, z
            lower = [v for v in vals if v < z]
            upper = [v for v in vals if v > z]
            if not lower or not upper:
                return None
            return lower[-1], upper[0]

        xb, yb = bracket(xs, x), bracket(ys, y)
        if xb is None or yb is None:
            evidence["capture_status"] = "OUTSIDE_INTERPOLATION_DOMAIN"
            return evidence
        x0, x1 = xb
        y0, y1 = yb

        def row_at(xx: float, yy: float) -> tuple[int, Mapping[str, Any]] | None:
            rr = [(i, r) for i, r in cand if float(r[ax]) == xx and float(r[ay]) == yy]
            return rr[0] if len(rr) == 1 else None

        corners = [
            ("x0_y0", x0, y0),
            ("x1_y0", x1, y0),
            ("x0_y1", x0, y1),
            ("x1_y1", x1, y1),
        ]
        selected = []
        for role, xx, yy in corners:
            found = row_at(xx, yy)
            if found is None:
                evidence["capture_status"] = "BILINEAR_GRID_POINT_MISSING"
                evidence["missing_grid_role"] = role
                return evidence
            idx, row = found
            selected.append(_row_record(idx, role, row))
        evidence["selected_rows"] = selected
        evidence["selection_mode"] = "bilinear_grid"
        evidence["axes"] = [ax, ay]
        evidence["axis_values"] = {ax: x, ay: y}
        evidence["bracket"] = {ax: [x0, x1], ay: [y0, y1]}
        evidence["fractions"] = {
            ax: 0.0 if x1 == x0 else (x - x0) / (x1 - x0),
            ay: 0.0 if y1 == y0 else (y - y0) / (y1 - y0),
        }
        return evidence

    evidence["capture_status"] = "UNSUPPORTED_INTERPOLATION_EVIDENCE_SHAPE"
    return evidence


def _instrumented_execute(model: Any, node: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    assert _ORIGINAL_EXECUTE is not None
    outputs = _ORIGINAL_EXECUTE(model, node, values)
    if node.get("lookup_spec"):
        evidence = _capture_lookup_rows(model, node, values, outputs)
        key = evidence_cache_key(model, node, values, outputs)
        with _LOCK:
            _CACHE[key] = evidence
    return outputs


def install() -> None:
    """Install the transparent evidence hook once for this Python process."""
    global _INSTALLED, _ORIGINAL_EXECUTE
    if _INSTALLED:
        return
    from . import fire_ui16_declarative as decl
    _ORIGINAL_EXECUTE = decl.execute_declarative
    decl.execute_declarative = _instrumented_execute
    _INSTALLED = True


def get_lookup_runtime_evidence(
    model: Any,
    node_id: str,
    trace_inputs: Mapping[str, Any],
    trace_outputs: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return matching evidence for one completed lookup trace record."""
    node = getattr(model, "nodes", {}).get(node_id)
    if not isinstance(node, Mapping) or not node.get("lookup_spec"):
        return None
    values = dict(trace_inputs)
    key = evidence_cache_key(model, node, values, trace_outputs)
    with _LOCK:
        evidence = _CACHE.get(key)
    return copy.deepcopy(evidence) if evidence is not None else None


def clear_runtime_evidence_cache() -> None:
    """Test helper; does not affect calculation state."""
    with _LOCK:
        _CACHE.clear()
