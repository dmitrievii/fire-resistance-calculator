"""Typed report-metadata sidecar bound to one frozen normative DAG.

The sidecar is presentation/report semantics only. It cannot alter quantities,
edges, datasets, calculations, routing, applicability or executor behavior. The
loader verifies the exact base ``graph_id`` and ``graph_sha256`` before exposing
any metadata to REPORT-IR.
"""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

REPORT_METADATA_SCHEMA = "fire_dag_report_metadata_v1"
ACTIVE_REPORT_METADATA_FILENAME = "report_metadata_v0.3.72_tension_golden.json"

_ALLOWED_REPORT_SPEC_KEYS = frozenset(
    {
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
        "verdict_quantity_id",
        "governing_scope",
        "governing_scope_title_ru",
        "governing_quantity_id",
    }
)


def _deep(value: Any) -> Any:
    return copy.deepcopy(value)


@lru_cache(maxsize=8)
def _read_json(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("report metadata root must be an object")
    return value


def _outputs(node: Mapping[str, Any]) -> set[str]:
    return {
        str(row["quantity_id"])
        for row in node.get("produces") or []
        if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str)
    }


def _is_boolean_quantity(model: Any, quantity_id: str) -> bool:
    quantities = getattr(model, "quantities", {})
    row = quantities.get(quantity_id) if isinstance(quantities, Mapping) else None
    if not isinstance(row, Mapping):
        return False
    return str(row.get("data_type") or row.get("type") or "").lower() in {"bool", "boolean"}


def _validate(model: Any, payload: Mapping[str, Any], *, source_path: Path) -> dict[str, Any]:
    if payload.get("schema") != REPORT_METADATA_SCHEMA:
        raise ValueError(f"unsupported report metadata schema in {source_path}")

    graph = getattr(model, "graph", {})
    graph_id = graph.get("graph_id") if isinstance(graph, Mapping) else None
    graph_sha256 = getattr(model, "graph_sha256", None)
    if payload.get("base_graph_id") != graph_id:
        raise ValueError(
            f"report metadata base_graph_id mismatch: {payload.get('base_graph_id')!r} != {graph_id!r}"
        )
    if payload.get("base_graph_sha256") != graph_sha256:
        raise ValueError("report metadata base_graph_sha256 does not match the loaded frozen DAG")

    specs = payload.get("node_report_specs") or {}
    if not isinstance(specs, Mapping):
        raise ValueError("node_report_specs must be an object")
    nodes = getattr(model, "nodes", {})

    for node_id, raw_spec in specs.items():
        if node_id not in nodes:
            raise ValueError(f"report metadata references unknown node {node_id}")
        if not isinstance(raw_spec, Mapping):
            raise ValueError(f"report metadata for {node_id} must be an object")
        extra = sorted(set(raw_spec).difference(_ALLOWED_REPORT_SPEC_KEYS))
        if extra:
            raise ValueError(f"report metadata for {node_id} contains forbidden keys: {extra}")

        outputs = _outputs(nodes[node_id])
        verdict_qid = raw_spec.get("verdict_quantity_id")
        if verdict_qid is not None:
            if not isinstance(verdict_qid, str) or verdict_qid not in outputs:
                raise ValueError(f"verdict_quantity_id for {node_id} must be an output of that node")
            if not _is_boolean_quantity(model, verdict_qid):
                raise ValueError(f"verdict_quantity_id for {node_id} must reference a boolean quantity")

        governing_qid = raw_spec.get("governing_quantity_id")
        governing_scope = raw_spec.get("governing_scope")
        if governing_qid is not None:
            if not isinstance(governing_qid, str) or governing_qid not in outputs:
                raise ValueError(f"governing_quantity_id for {node_id} must be an output of that node")
            if not isinstance(governing_scope, str) or not governing_scope.strip():
                raise ValueError(f"governing_quantity_id for {node_id} requires a non-empty governing_scope")
        elif governing_scope is not None:
            raise ValueError(f"governing_scope for {node_id} requires governing_quantity_id")

    return _deep(dict(payload))


def report_metadata_for_model(model: Any) -> dict[str, Any]:
    """Load and validate the active metadata sidecar for a file-backed DAG.

    Models without ``source_path`` intentionally fall back to inline
    ``node.report_spec`` metadata only; this keeps unit tests and synthetic DAGs
    independent of package files.
    """
    source = getattr(model, "source_path", None)
    if not source:
        return {
            "schema": REPORT_METADATA_SCHEMA,
            "revision_id": None,
            "base_graph_id": None,
            "base_graph_sha256": None,
            "node_report_specs": {},
            "source_path": None,
        }
    path = Path(source).resolve().parent / ACTIVE_REPORT_METADATA_FILENAME
    if not path.is_file():
        return {
            "schema": REPORT_METADATA_SCHEMA,
            "revision_id": None,
            "base_graph_id": None,
            "base_graph_sha256": None,
            "node_report_specs": {},
            "source_path": str(path),
        }
    payload = _validate(model, _read_json(str(path)), source_path=path)
    payload["source_path"] = str(path)
    return payload


def report_spec_for_node(model: Any, node_id: str, node: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return merged inline + sidecar report metadata for one DAG node.

    Conflicting duplicate keys fail closed. No execution metadata is accepted in
    the sidecar, so this merge cannot affect engineering calculations.
    """
    if node is None:
        nodes = getattr(model, "nodes", {})
        node = nodes.get(node_id) if isinstance(nodes, Mapping) else None
    node = node if isinstance(node, Mapping) else {}
    inline = node.get("report_spec")
    merged = _deep(dict(inline)) if isinstance(inline, Mapping) else {}

    sidecar = report_metadata_for_model(model)
    raw = (sidecar.get("node_report_specs") or {}).get(node_id)
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if key in merged and merged[key] != value:
                raise ValueError(f"conflicting inline/sidecar report metadata for {node_id}.{key}")
            merged[key] = _deep(value)
    return merged


def report_metadata_identity(model: Any) -> dict[str, Any]:
    payload = report_metadata_for_model(model)
    return {
        "schema": payload.get("schema"),
        "revision_id": payload.get("revision_id"),
        "base_graph_id": payload.get("base_graph_id"),
        "base_graph_sha256": payload.get("base_graph_sha256"),
        "source_path": payload.get("source_path"),
        "node_report_spec_count": len(payload.get("node_report_specs") or {}),
    }
