"""v0.76 guided overlay: one canonical z/y effective-length card.

The v0.75 numerical z/y contract remains the parent.  This overlay replaces its
seven sequential effective-length input/decision cards with one structured card
covering both canonical principal axes.  The frozen source DAG is not modified.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from .sp16_mech7_v075_graph_overlay import STATE_NODE_ID

GRAPH_SUFFIX = "_v076_effective_length_card"
INPUT_NODE_ID = "SP16_I_V076_EFFECTIVE_LENGTH_ZY"
DEFINITION_QID = "sp16_effective_length_definition_zy"

V075_EFFECTIVE_LENGTH_INPUT_NODES = {
    "SP16_I_V075_MEMBER_LENGTH",
    "SP16_D_V075_EFFECTIVE_ROUTE_Z",
    "SP16_D_V075_TABLE30_Z",
    "SP16_I_V075_VERIFIED_LEFF_Z",
    "SP16_D_V075_EFFECTIVE_ROUTE_Y",
    "SP16_D_V075_TABLE30_Y",
    "SP16_I_V075_VERIFIED_LEFF_Y",
}

# Human-readable descriptions are a presentation of the eight diagrams in
# SP16 Table 30, left-to-right.  The active v0.76 card stores S1..S8 only; the
# qualified Section-10 producer receives its historical scheme_1..scheme_8 key
# inside the runtime adapter, never through a user-facing legacy enum.
TABLE30_OPTIONS: list[dict[str, Any]] = [
    {
        "value": "S1",
        "label": "Шарнирное закрепление обоих концов",
        "description": "Сосредоточенная продольная сила N; μ = 1,00.",
        "mu": 1.0,
    },
    {
        "value": "S2",
        "label": "Один конец защемлён, другой шарнирно закреплён",
        "description": "Сосредоточенная продольная сила N; μ = 0,70.",
        "mu": 0.7,
    },
    {
        "value": "S3",
        "label": "Жёсткое закрепление обоих концов",
        "description": "Сосредоточенная продольная сила N; μ = 0,50.",
        "mu": 0.5,
    },
    {
        "value": "S4",
        "label": "Консоль: один конец защемлён, другой свободен",
        "description": "Сосредоточенная продольная сила N приложена к свободному концу; μ = 2,00.",
        "mu": 2.0,
    },
    {
        "value": "S5",
        "label": "Оба конца защемлены; поперечное смещение конца допускается",
        "description": "Схема со смещением по таблице 30; сосредоточенная сила N; μ = 1,00.",
        "mu": 1.0,
    },
    {
        "value": "S6",
        "label": "Один конец защемлён, другой шарнирный; поперечное смещение допускается",
        "description": "Схема со смещением по таблице 30; сосредоточенная сила N; μ = 2,00.",
        "mu": 2.0,
    },
    {
        "value": "S7",
        "label": "Шарнирное закрепление; продольная сила возрастает к Nmax",
        "description": "Линейно изменяющаяся по длине продольная сила по схеме таблицы 30; μ = 0,725.",
        "mu": 0.725,
    },
    {
        "value": "S8",
        "label": "Консоль; продольная сила возрастает к Nmax у защемления",
        "description": "Линейно изменяющаяся по длине продольная сила по схеме таблицы 30; μ = 1,12.",
        "mu": 1.12,
    },
]


def _definition_quantity() -> dict[str, Any]:
    return {
        "id": DEFINITION_QID,
        "symbol": None,
        "name_ru": "Определение расчётных длин по осям z/y",
        "data_type": "object",
        "role": "input",
        "physical_dimension": None,
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {
            "primary_source_type": "USER_INPUT",
            "allowed_source_types": ["USER_INPUT"],
            "override_policy": "forbidden",
        },
    }


def _input_node() -> dict[str, Any]:
    return {
        "id": INPUT_NODE_ID,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": "СП16 — расчётные длины по главным осям z/y",
        "normative_refs": [
            {"standard_id": "SP16_2017", "reference_kind": "clause", "section": "10", "clause": "10.3.1"},
            {"standard_id": "SP16_2017", "reference_kind": "table", "section": "10", "clause": "10.3.3", "table_ref": "30"},
        ],
        "consumes": [],
        "produces": [{"quantity_id": DEFINITION_QID, "required": True, "binding_role": "output"}],
        "applicability": None,
        "input_spec": {
            "input_method": "user_input",
            "required": True,
            "user_prompt": "Как определяется расчётная длина элемента по сильной оси z и слабой оси y?",
        },
        "notes": {
            "engineering_meaning": "One source-traced Stage-N7 definition for both canonical principal axes.",
            "limitations": "Table 30 requires geometric member length; a directly specified l_eff requires an explicit basis.",
            "normative_warning": "Оси: z — сильная, y — слабая. Скрытые коэффициенты μ и скрытые расчётные длины не применяются.",
        },
    }


def _edge(edge_id: str, from_node: str, to_node: str, *, condition: Mapping[str, Any] | None = None, qids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": edge_id,
        "from_node_id": from_node,
        "to_node_id": to_node,
        "edge_type": "branch" if condition is not None else "control",
        "label": edge_id,
        "condition": copy.deepcopy(condition),
        "quantity_ids": list(qids or []),
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    quantities = {q["id"]: q for q in out["quantities"]}
    nodes = {n["id"]: n for n in out["nodes"]}
    if DEFINITION_QID not in quantities:
        q = _definition_quantity()
        out["quantities"].append(q)
        quantities[DEFINITION_QID] = q
    if INPUT_NODE_ID not in nodes:
        n = _input_node()
        out["nodes"].append(n)
        nodes[INPUT_NODE_ID] = n

    # The old v0.75 cards are retained only as release history nodes. They are
    # disconnected from active guided navigation; no scheme_# enum reaches the
    # user-facing contract in v0.76.
    out["edges"] = [
        edge for edge in out["edges"]
        if edge.get("from_node_id") not in V075_EFFECTIVE_LENGTH_INPUT_NODES
        and edge.get("to_node_id") not in V075_EFFECTIVE_LENGTH_INPUT_NODES
    ]

    # Remove a stale direct compression edge defensively if an older parent DAG
    # is supplied, then bind the single card to the canonical state producer.
    out["edges"] = [edge for edge in out["edges"] if edge.get("id") != "MECH7_E_BRITTLE_TO_COMPRESSION"]
    additions = [
        _edge(
            "V076_E_BRITTLE_TO_EFFECTIVE_LENGTH",
            "SP16_D_MECH7_BRITTLE_REQUIRED",
            INPUT_NODE_ID,
            condition={"type": "comparison", "quantity_id": "ambient_N_force", "operator": "lt", "value": 0.0},
            qids=["ambient_N_force"],
        ),
        _edge("V076_E_EFFECTIVE_LENGTH_TO_STATE", INPUT_NODE_ID, STATE_NODE_ID, qids=[DEFINITION_QID]),
    ]
    existing = {edge["id"] for edge in out["edges"]}
    out["edges"].extend(edge for edge in additions if edge["id"] not in existing)

    state = nodes.get(STATE_NODE_ID)
    if state:
        old_route_qids = {
            "sp16_member_length_mm",
            "sp16_effective_length_route_z", "sp16_table30_scheme_z",
            "sp16_verified_l_eff_z_mm", "sp16_verified_l_eff_z_basis",
            "sp16_effective_length_route_y", "sp16_table30_scheme_y",
            "sp16_verified_l_eff_y_mm", "sp16_verified_l_eff_y_basis",
            "profile_ref",
        }
        consumes = [copy.deepcopy(row) for row in state.get("consumes", []) if row.get("quantity_id") not in old_route_qids]
        if not any(row.get("quantity_id") == DEFINITION_QID for row in consumes):
            consumes.insert(0, {"quantity_id": DEFINITION_QID, "required": True, "binding_role": "input"})
        # These are already-produced selected-section identities/state. They are
        # optional dependencies because non-catalog section routes remain
        # fail-closed later if a qualified Table-7 curve cannot be established.
        for qid in (
            "section_catalog_family_id", "section_designation", "section_catalog_source_row_id",
            "section_geometry_2d_normalized", "A_gross", "J_x", "J_y", "Ry_formula", "E_norm",
        ):
            if qid in quantities and not any(row.get("quantity_id") == qid for row in consumes):
                consumes.append({"quantity_id": qid, "required": False, "binding_role": "input"})
        state["consumes"] = consumes
        state["title"] = "СП16 — расчётные длины, гибкости и φ по каноническим осям z/y (v0.76)"
        state["calculation_spec"] = {
            "formula_type": "executor",
            "expression_language": "executor_v1",
            "algorithm_id": "sp16_v076_effective_length_zy_v1",
            "bindings": [],
            "rounding": {"mode": "none"},
        }
        state.setdefault("notes", {})["engineering_meaning"] = "Single-card Section-10 definition feeding canonical z/y stability state."

    out["graph_id"] = str(out["graph_id"]) + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.76 consolidates effective-length authoring into one z/y card, uses S1-S8 only "
        "at the UI boundary, and removes profile_ref as an active prerequisite."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(V075_EFFECTIVE_LENGTH_INPUT_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)
    table = dict(out.get("node_presentation") or {})
    table[INPUT_NODE_ID] = {
        "component": "effective_length_zy_editor",
        "stage": "СП16 · Stage N7",
        "title": "Расчётные длины элемента",
        "subtitle": "Для каждой главной оси выберите способ определения l_eff. Таблица 30 применяется только к соответствующим схемам п. 10.3.3.",
        "table30_options": copy.deepcopy(TABLE30_OPTIONS),
    }
    out["node_presentation"] = table
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if str(model.graph.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=transform_presentation_policy(model.presentation_policy),
    )


def replay_prefix_on_model(session: GuidedCalculationSession, model: FireDAGModel, registry: ExecutionRegistry) -> GuidedCalculationSession:
    migrated = GuidedCalculationSession(model, entry_node_id=session.entry_node_id, registry=registry)
    for row in copy.deepcopy(session.interaction_history):
        expected = str(row.get("node_id") or "")
        if migrated.current_node_id != expected:
            break
        migrated.submit(row.get("payload"), provenance=row.get("provenance"))
    return migrated


__all__ = [
    "DEFINITION_QID", "GRAPH_SUFFIX", "INPUT_NODE_ID", "STATE_NODE_ID",
    "TABLE30_OPTIONS", "V075_EFFECTIVE_LENGTH_INPUT_NODES",
    "build_model", "replay_prefix_on_model", "transform_graph", "transform_presentation_policy",
]
