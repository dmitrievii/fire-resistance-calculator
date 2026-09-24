"""v0.92 active canonical-action migration for the SP16 -> SP554 guided runtime.

The frozen historical DAG is retained unchanged on disk.  This overlay rewrites
only the active in-memory contract to the SP16 natural action convention used by
v0.92:

    N   axial force
    Mz  bending about the strong principal z axis
    My  bending about the weak principal y axis
    Mx  torsion about the member x axis
    Qz  transverse force associated with the z direction
    Qy  transverse force associated with the y direction
    B   bimoment

The previous active graph used Mx for strong-axis bending and a separate T for
torsion.  That historical meaning is NEVER replayed into the new ``Mx``.  Old
sessions are replayed only up to the first interaction that produced an action
quantity whose meaning changed; the user must then re-enter the action state.

Existing qualified numerical executors are retained behind a one-way adapter:
canonical ledger values are translated to the historical *local variable names*
expected by those frozen functions and their outputs are translated back before
they reach the active ledger.  The adapter is installed only on graph nodes
whose contract actually crosses the changed action quantities or aggregate
MECH2 action/verification objects.  Unrelated executors retain exact object
identity, preserving historical registry isolation.
"""
from __future__ import annotations

import copy
from functools import wraps
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession, FireUIError

GRAPH_SUFFIX = "_v092_canonical_actions"
REGISTRY_MARKER = "_sp16_v092_canonical_actions_installed"
REGISTRY_TARGETS_MARKER = "_sp16_v092_canonical_action_target_nodes"

# Historical DAG quantity id -> active v0.92 quantity id.
# Unchanged y-axis and axial quantities are intentionally absent.
LEGACY_TO_CANONICAL_QID: dict[str, str] = {
    "ambient_M_x": "ambient_M_z",
    "ambient_Q_x": "ambient_Q_z",
    "ambient_T_torsion": "ambient_M_x",
    "M_x": "M_z",
    "Q_x": "Q_z",
    "T_torsion": "M_x",
}
CANONICAL_TO_LEGACY_QID: dict[str, str] = {
    canonical: legacy for legacy, canonical in LEGACY_TO_CANONICAL_QID.items()
}

# Nested action-object keys used by MECH2 load-case states.
LEGACY_TO_CANONICAL_ACTION_KEY = {
    "Mx": "Mz",
    "My": "My",
    "Qx": "Qz",
    "Qy": "Qy",
    "T": "Mx",
    "N": "N",
    "B": "B",
}
CANONICAL_TO_LEGACY_ACTION_KEY = {
    canonical: legacy for legacy, canonical in LEGACY_TO_CANONICAL_ACTION_KEY.items()
}

_CHANGED_LEGACY_QIDS = frozenset(LEGACY_TO_CANONICAL_QID)
_CHANGED_CANONICAL_QIDS = frozenset(LEGACY_TO_CANONICAL_QID.values())

# These quantities keep their top-level ids but contain axis-sensitive nested
# payloads. Consumers/producers must cross the same compatibility adapter.
_CANONICALIZED_AGGREGATE_QIDS = frozenset(
    {
        "ambient_load_case",
        "ambient_mechanical_action_state",
        "mechanical_action_state",
        "sp16_applicability_census",
        "verification_plan",
        "fire_load_case",
    }
)

_CANONICAL_QUANTITY_META: dict[str, dict[str, Any]] = {
    "ambient_M_z": {
        "symbol": "M_z",
        "name_ru": "Изгибающий момент Mz относительно сильной оси z",
    },
    "ambient_M_y": {
        "symbol": "M_y",
        "name_ru": "Изгибающий момент My относительно слабой оси y",
    },
    "ambient_M_x": {
        "symbol": "M_x",
        "name_ru": "Крутящий момент Mx относительно продольной оси x",
    },
    "ambient_Q_z": {
        "symbol": "Q_z",
        "name_ru": "Поперечная сила Qz",
    },
    "ambient_Q_y": {
        "symbol": "Q_y",
        "name_ru": "Поперечная сила Qy",
    },
    "M_z": {
        "symbol": "M_z",
        "name_ru": "Изгибающий момент Mz относительно сильной оси z при пожаре",
    },
    "M_y": {
        "symbol": "M_y",
        "name_ru": "Изгибающий момент My относительно слабой оси y при пожаре",
    },
    "M_x": {
        "symbol": "M_x",
        "name_ru": "Крутящий момент Mx относительно продольной оси x при пожаре",
    },
    "Q_z": {
        "symbol": "Q_z",
        "name_ru": "Поперечная сила Qz при пожаре",
    },
    "Q_y": {
        "symbol": "Q_y",
        "name_ru": "Поперечная сила Qy при пожаре",
    },
}

_CANONICAL_AXIS_CONVENTION = {
    "member_axis": "x",
    "section_principal_axes": ["z-z", "y-y"],
    "N": "positive=tension; negative=compression",
    "Mz": "bending moment about the strong principal z-z axis",
    "My": "bending moment about the weak principal y-y axis",
    "Mx": "torsional moment about the longitudinal member x axis",
    "Qz": "transverse force in the canonical z direction",
    "Qy": "transverse force in the canonical y direction",
    "B": "bimoment; direct conditional input in current scope",
}
_HISTORICAL_AXIS_CONVENTION = {
    "member_axis": "s",
    "section_principal_axes": ["x-x", "y-y"],
    "N": "positive=tension; negative=compression",
    "T": "torsional moment about member axis s",
    "B": "bimoment; direct conditional input in current scope",
}

_CANONICAL_SIGN_CONVENTION = {
    "N": "positive=tension, negative=compression",
    "x": "member longitudinal axis",
    "Mz": "bending about SP16 strong principal z-z",
    "My": "bending about SP16 weak principal y-y",
    "Mx": "torsion about longitudinal x",
    "Qz": "SP16 Qz",
    "Qy": "SP16 Qy",
    "B": "bimoment, direct conditional input",
}
_HISTORICAL_SIGN_CONVENTION = {
    "N": "positive=tension, negative=compression",
    "s": "member longitudinal axis",
    "Mx": "bending about SP16 principal x-x",
    "My": "bending about SP16 principal y-y",
    "Qx": "SP16 Qx",
    "Qy": "SP16 Qy",
    "T": "torsion about longitudinal s",
    "B": "bimoment, direct conditional input",
}

# Exact semantic ids emitted by historical MECH1/MECH2 aggregate objects.
# Only exact ids are changed; arbitrary text and normative references are not
# subject to blind substring replacement.
_ID_VALUE_RENAMES = {
    "bending_x": "bending_z",
    "shear_x": "shear_z",
    "bending_Mx": "bending_Mz",
    "shear_Qx": "shear_Qz",
    "torsion_T": "torsion_Mx",
    "interaction_M_Qx": "interaction_M_Qz",
}
_CANONICAL_TO_LEGACY_ID_VALUE = {value: key for key, value in _ID_VALUE_RENAMES.items()}
_ID_LIST_PARENT_KEYS = frozenset({"deferred_branch_ids"})

_BRANCH_LABEL_RENAMES = {
    "bending_Mx": "Изгиб Mz относительно сильной главной оси z-z",
    "shear_Qx": "Поперечная сила Qz",
    "torsion_T": "Кручение Mx относительно продольной оси x",
    "interaction_M_Qx": "Взаимодействие M + Qz",
    "biaxial_bending": "Двухосный изгиб Mz + My",
    "interaction_N_M": "Взаимодействие N + Mz + My",
}
_HISTORICAL_BRANCH_LABELS = {
    "bending_Mx": "Изгиб Mx относительно главной оси x-x",
    "shear_Qx": "Поперечная сила Qx / текущий scalar web-shear route",
    "torsion_T": "Кручение T относительно продольной оси s",
    "interaction_M_Qx": "Взаимодействие M + Qx",
    "biaxial_bending": "Двухосный изгиб Mx + My",
    "interaction_N_M": "Взаимодействие N + Mx + My",
}
_BRANCH_NOTE_RENAMES = {
    "torsion_T": (
        "В активном контракте v0.92 Mx обозначает кручение относительно продольной оси x; "
        "кручение не подменяется бимоментом B. Поддержка определяется последующими MECH-этапами."
    ),
}
_HISTORICAL_BRANCH_NOTES = {
    "torsion_T": (
        "SP16-MECH1 не подменяет T бимоментом B; torsion runtime закрывается отдельным этапом."
    ),
}

_SCHEMA_RENAMES = {
    "sp16_mech1_canonical_mechanical_action_state_v1": "sp16_mech1_mechanical_action_state_v092_canonical_axes",
    "sp16_mech1_verification_plan_v1": "sp16_mech1_verification_plan_v092_canonical_axes",
    "sp16_mech2_load_case_v1": "sp16_mech2_load_case_v092_canonical_axes",
    "sp16_mech2_ambient_mechanical_action_state_v1": "sp16_mech2_ambient_mechanical_action_state_v092_canonical_axes",
    "sp16_mech2_applicability_census_v1": "sp16_mech2_applicability_census_v092_canonical_axes",
}
_CANONICAL_TO_LEGACY_SCHEMA = {value: key for key, value in _SCHEMA_RENAMES.items()}


def _rename_exact(value: Any, mapping: Mapping[str, str]) -> Any:
    """Recursively replace only strings exactly equal to mapped quantity ids."""
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_rename_exact(item, mapping) for item in value]
    if isinstance(value, tuple):
        return tuple(_rename_exact(item, mapping) for item in value)
    if isinstance(value, Mapping):
        return {key: _rename_exact(item, mapping) for key, item in value.items()}
    return copy.deepcopy(value)


def _patch_quantity_metadata(graph: dict[str, Any]) -> None:
    for quantity in graph.get("quantities", []):
        if not isinstance(quantity, dict):
            continue
        qid = quantity.get("id")
        meta = _CANONICAL_QUANTITY_META.get(str(qid))
        if meta:
            quantity.update(copy.deepcopy(meta))


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Return the active graph with canonical Mz/My/Mx and Qz/Qy quantities."""
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    out = _rename_exact(out, LEGACY_TO_CANONICAL_QID)
    _patch_quantity_metadata(out)

    ids = [str(row.get("id")) for row in out.get("quantities", []) if isinstance(row, Mapping)]
    if len(ids) != len(set(ids)):
        raise FireUIError("v0.92 canonical-action transform produced duplicate quantity ids")

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.92 active action contract: Mz strong-axis bending, My weak-axis "
        "bending, Mx torsion only, Qz/Qy transverse forces; no old-Mx replay."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if str(model.graph.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=model.presentation_policy,
    )


def _canonicalize_engineering_object(value: Any, *, parent_key: str | None = None) -> Any:
    """Canonicalize known nested MECH state/plan objects without changing formulas."""
    if isinstance(value, list):
        return [_canonicalize_engineering_object(item, parent_key=parent_key) for item in value]
    if not isinstance(value, Mapping):
        if parent_key == "schema" and isinstance(value, str):
            return _SCHEMA_RENAMES.get(value, value)
        if parent_key == "compatibility_aliases" and value == "Q_x":
            return "Q_z"
        if parent_key in _ID_LIST_PARENT_KEYS and isinstance(value, str):
            return _ID_VALUE_RENAMES.get(value, value)
        return copy.deepcopy(value)

    if parent_key == "actions":
        result: dict[str, Any] = {}
        for key, item in value.items():
            result[LEGACY_TO_CANONICAL_ACTION_KEY.get(str(key), str(key))] = _canonicalize_engineering_object(item)
        return result
    if parent_key == "axis_convention":
        return copy.deepcopy(_CANONICAL_AXIS_CONVENTION)
    if parent_key == "sign_convention":
        return copy.deepcopy(_CANONICAL_SIGN_CONVENTION)
    if parent_key == "compatibility_aliases":
        return {
            str(key): ("Q_z" if item == "Q_x" else _canonicalize_engineering_object(item))
            for key, item in value.items()
        }

    historical_id = str(value.get("id")) if isinstance(value.get("id"), str) else None
    result: dict[str, Any] = {}
    for key, item in value.items():
        new_item = _canonicalize_engineering_object(item, parent_key=str(key))
        if key == "id" and isinstance(new_item, str):
            new_item = _ID_VALUE_RENAMES.get(new_item, new_item)
        result[key] = new_item
    if historical_id in _BRANCH_LABEL_RENAMES and "label" in result:
        result["label"] = _BRANCH_LABEL_RENAMES[historical_id]
    if historical_id in _BRANCH_NOTE_RENAMES and "note" in result:
        result["note"] = _BRANCH_NOTE_RENAMES[historical_id]
    return result


def _legacy_engineering_object(value: Any, *, parent_key: str | None = None) -> Any:
    """Create an executor-local historical view of canonical MECH aggregates."""
    if isinstance(value, list):
        return [_legacy_engineering_object(item, parent_key=parent_key) for item in value]
    if not isinstance(value, Mapping):
        if parent_key == "schema" and isinstance(value, str):
            return _CANONICAL_TO_LEGACY_SCHEMA.get(value, value)
        if parent_key == "compatibility_aliases" and value == "Q_z":
            return "Q_x"
        if parent_key in _ID_LIST_PARENT_KEYS and isinstance(value, str):
            return _CANONICAL_TO_LEGACY_ID_VALUE.get(value, value)
        return copy.deepcopy(value)

    if parent_key == "actions":
        result: dict[str, Any] = {}
        for key, item in value.items():
            result[CANONICAL_TO_LEGACY_ACTION_KEY.get(str(key), str(key))] = _legacy_engineering_object(item)
        return result
    if parent_key == "axis_convention":
        return copy.deepcopy(_HISTORICAL_AXIS_CONVENTION)
    if parent_key == "sign_convention":
        return copy.deepcopy(_HISTORICAL_SIGN_CONVENTION)
    if parent_key == "compatibility_aliases":
        return {
            str(key): ("Q_x" if item == "Q_z" else _legacy_engineering_object(item))
            for key, item in value.items()
        }

    canonical_id = str(value.get("id")) if isinstance(value.get("id"), str) else None
    historical_id = _CANONICAL_TO_LEGACY_ID_VALUE.get(canonical_id, canonical_id) if canonical_id else None
    result: dict[str, Any] = {}
    for key, item in value.items():
        new_item = _legacy_engineering_object(item, parent_key=str(key))
        if key == "id" and isinstance(new_item, str):
            new_item = _CANONICAL_TO_LEGACY_ID_VALUE.get(new_item, new_item)
        result[key] = new_item
    if historical_id in _HISTORICAL_BRANCH_LABELS and "label" in result:
        result["label"] = _HISTORICAL_BRANCH_LABELS[historical_id]
    if historical_id in _HISTORICAL_BRANCH_NOTES and "note" in result:
        result["note"] = _HISTORICAL_BRANCH_NOTES[historical_id]
    return result


def _legacy_values(values: Mapping[str, Any]) -> dict[str, Any]:
    """Create an executor-local historical-name view from canonical ledger values."""
    # Remove changed canonical ids first because ambient_M_x / M_x now mean
    # torsion and must never leak into the historical bending slots.
    out = {
        key: _legacy_engineering_object(value)
        for key, value in values.items()
        if key not in _CHANGED_CANONICAL_QIDS
    }
    for canonical, legacy in CANONICAL_TO_LEGACY_QID.items():
        if canonical in values:
            out[legacy] = _legacy_engineering_object(values[canonical])
    return out


def _canonical_outputs(outputs: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in outputs.items():
        canonical_key = LEGACY_TO_CANONICAL_QID.get(str(key), str(key))
        result[canonical_key] = _canonicalize_engineering_object(value)
    return result


def _legacy_node(node: Mapping[str, Any]) -> dict[str, Any]:
    return _rename_exact(node, CANONICAL_TO_LEGACY_QID)


def canonical_registry_node_ids(model: FireDAGModel) -> set[str]:
    """Return only registry nodes whose public contract crosses changed semantics."""
    changed = _CHANGED_LEGACY_QIDS | _CHANGED_CANONICAL_QIDS | _CANONICALIZED_AGGREGATE_QIDS
    targets: set[str] = set()
    for node_id, node in model.nodes.items():
        quantity_ids: set[str] = set()
        for key in ("consumes", "produces"):
            for row in node.get(key, []):
                if isinstance(row, Mapping) and isinstance(row.get("quantity_id"), str):
                    quantity_ids.add(str(row["quantity_id"]))
        decision_qid = node.get("decision_quantity_id")
        if isinstance(decision_qid, str):
            quantity_ids.add(decision_qid)
        if quantity_ids.intersection(changed):
            targets.add(str(node_id))
    return targets


def install_registry_remediation(
    registry: ExecutionRegistry,
    model: FireDAGModel | None = None,
) -> None:
    """Wrap only executors whose graph contract crosses canonical action semantics.

    ``model=None`` is retained for focused unit tests and explicit low-level use;
    in that mode every registered executor is adapted. Production installers
    must pass the active model so unrelated executors retain exact identity.
    The function also heals a retained session created by the earlier v0.92
    all-registry wrapper implementation by unwrapping now-unrelated executors.
    """
    targets = canonical_registry_node_ids(model) if model is not None else set(registry.executors)

    for node_id, executor in list(registry.executors.items()):
        is_wrapped = bool(getattr(executor, "_sp16_v092_canonical_wrapper", False))
        if node_id not in targets:
            if is_wrapped:
                original = getattr(executor, "_sp16_v092_wrapped_executor", None)
                if original is not None:
                    registry.executors[node_id] = original
            continue
        if is_wrapped:
            continue

        def make_wrapper(fn):
            @wraps(fn)
            def wrapped(values: Mapping[str, Any], node: Mapping[str, Any]):
                raw = fn(_legacy_values(values), _legacy_node(node))
                if not isinstance(raw, Mapping):
                    raise FireUIError("v0.92 canonical registry wrapper received non-mapping executor output")
                return _canonical_outputs(raw)

            setattr(wrapped, "_sp16_v092_canonical_wrapper", True)
            setattr(wrapped, "_sp16_v092_wrapped_executor", fn)
            return wrapped

        registry.executors[node_id] = make_wrapper(executor)

    setattr(registry, REGISTRY_MARKER, True)
    setattr(registry, REGISTRY_TARGETS_MARKER, frozenset(targets))


def legacy_axis_interaction_node_ids(model: FireDAGModel) -> set[str]:
    """Interactive nodes whose historical answers cannot be replayed into v0.92."""
    unsafe: set[str] = set()
    for node_id, node in model.nodes.items():
        produced = {
            str(row.get("quantity_id"))
            for row in node.get("produces", [])
            if isinstance(row, Mapping)
        }
        decision_qid = node.get("decision_quantity_id")
        if isinstance(decision_qid, str):
            produced.add(decision_qid)
        if produced.intersection(_CHANGED_LEGACY_QIDS):
            unsafe.add(str(node_id))
    return unsafe


def replay_prefix_without_axis_alias(
    source: GuidedCalculationSession,
    model: FireDAGModel,
    registry: ExecutionRegistry,
) -> GuidedCalculationSession:
    """Replay safely and stop before any historical action whose meaning changed."""
    migrated = GuidedCalculationSession(model, entry_node_id=source.entry_node_id, registry=registry)
    unsafe_nodes = legacy_axis_interaction_node_ids(source.model)

    for row in copy.deepcopy(source.interaction_history):
        expected = str(row.get("node_id") or "")
        if expected in unsafe_nodes:
            break
        if migrated.current_node_id != expected:
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except FireUIError:
            break
    return migrated


def canonical_action_contract() -> dict[str, Any]:
    return {
        "schema": "sp16_v092_canonical_action_contract_v1",
        "member_axis": "x",
        "strong_axis_bending": "M_z",
        "weak_axis_bending": "M_y",
        "torsion": "M_x",
        "shear_components": ["Q_z", "Q_y"],
        "verification_plan_branch_ids": {
            "strong_axis_bending": "bending_Mz",
            "z_shear": "shear_Qz",
            "torsion": "torsion_Mx",
            "bending_shear_interaction": "interaction_M_Qz",
        },
        "legacy_old_Mx_to_new_Mz_replay_allowed": False,
        "legacy_T_to_new_Mx_replay_allowed": False,
    }


__all__ = [
    "CANONICAL_TO_LEGACY_QID",
    "GRAPH_SUFFIX",
    "LEGACY_TO_CANONICAL_QID",
    "build_model",
    "canonical_action_contract",
    "canonical_registry_node_ids",
    "install_registry_remediation",
    "legacy_axis_interaction_node_ids",
    "replay_prefix_without_axis_alias",
    "transform_graph",
]
