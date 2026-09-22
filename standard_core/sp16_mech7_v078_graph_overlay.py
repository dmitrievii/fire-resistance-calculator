"""v0.78 graph overlay for explicit SP16 Table-1 compression gamma_c.

The overlay is deliberately inserted after the v0.76 effective-length card and
before the canonical z/y state producer.  Existing v0.76/v0.77 interactive
history therefore replays unchanged and stops at exactly one new normative
question instead of invalidating the user's calculation.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from .material_resistance import material_safety_factor
from .sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    MATERIAL_SAFETY_INPUT_NODE_ID,
    MATERIAL_SAFETY_QUANTITY_ID,
)
from .sp16_mech7_v076_graph_overlay import INPUT_NODE_ID as V076_INPUT_NODE_ID, STATE_NODE_ID
from .sp16_mech7_v078_gamma_c import (
    CALC_NODE_ID, EVIDENCE_QID, INPUT_QID, OUTPUT_QID, compression_case_options,
)

GRAPH_SUFFIX = "_v078_gamma_c_compression"
INPUT_NODE_ID = "SP16_I_V078_GAMMA_C_COMPRESSION_CASE"
EDGE_INPUT_TO_STATE_V076 = "V076_E_EFFECTIVE_LENGTH_TO_STATE"


def _quantity(qid: str, *, name: str, data_type: str, role: str, enum_values: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    out = {
        "id": qid,
        "symbol": None,
        "name_ru": name,
        "data_type": data_type,
        "role": role,
        "physical_dimension": None,
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {
            "primary_source_type": "USER_INPUT" if role == "input" else "CALCULATED",
            "allowed_source_types": ["USER_INPUT"] if role == "input" else ["CALCULATED"],
            "override_policy": "forbidden",
        },
    }
    if enum_values is not None:
        out["enum_values"] = copy.deepcopy(enum_values)
    return out


def _input_node() -> dict[str, Any]:
    return {
        "id": INPUT_NODE_ID,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": "СП16 — коэффициент условий работы γc для сжатого элемента",
        "normative_refs": [
            {"standard_id": "SP16_2017", "reference_kind": "clause", "section": "4", "clause": "4.3.2"},
            {"standard_id": "SP16_2017", "reference_kind": "table", "section": "4", "clause": "4.3.2", "table_ref": "1"},
        ],
        "consumes": [],
        "produces": [{"quantity_id": INPUT_QID, "required": True, "binding_role": "output"}],
        "applicability": None,
        "input_spec": {
            "input_method": "user_input",
            "required": True,
            "user_prompt": "Какой случай таблицы 1 СП16 определяет γc для текущего сжатого элемента?",
        },
        "notes": {
            "engineering_meaning": "Explicit classification of the working-condition factor used by compression strength, stability and limiting slenderness checks.",
            "limitations": "The application does not infer a Table-1 case from profile geometry or building type.",
            "normative_warning": "γc не принимается скрыто. Если случай не оговорен таблицей 1, явно выберите примечание 5 (γc = 1,00).",
        },
    }


def _calc_node() -> dict[str, Any]:
    return {
        "id": CALC_NODE_ID,
        "node_type": "calculation",
        "owner_standard_id": "SP16_2017",
        "title": "СП16 — γc по таблице 1",
        "normative_refs": [
            {"standard_id": "SP16_2017", "reference_kind": "clause", "section": "4", "clause": "4.3.2"},
            {"standard_id": "SP16_2017", "reference_kind": "table", "section": "4", "clause": "4.3.2", "table_ref": "1"},
        ],
        "consumes": [{"quantity_id": INPUT_QID, "required": True, "binding_role": "input"}],
        "produces": [
            {"quantity_id": OUTPUT_QID, "required": True, "binding_role": "output"},
            {"quantity_id": EVIDENCE_QID, "required": True, "binding_role": "output"},
        ],
        "applicability": None,
        "calculation_spec": {
            "formula_type": "executor",
            "expression_language": "executor_v1",
            "algorithm_id": "sp16_v078_table1_gamma_c_compression_v1",
            "bindings": [],
            "rounding": {"mode": "none"},
        },
    }


def _edge(edge_id: str, from_node: str, to_node: str, qids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": edge_id,
        "from_node_id": from_node,
        "to_node_id": to_node,
        "edge_type": "control",
        "label": edge_id,
        "condition": None,
        "quantity_ids": list(qids or []),
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    graph_id = str(out.get("graph_id") or "")
    if GRAPH_SUFFIX in graph_id:
        return out

    quantities = {q["id"]: q for q in out["quantities"]}
    options = compression_case_options()
    enum_values = [
        {
            "value": row["value"],
            "label": f"{row['description_ru']} — γc = {str(row['gamma_c']).replace('.', ',')}",
        }
        for row in options
    ]
    if INPUT_QID not in quantities:
        out["quantities"].append(_quantity(INPUT_QID, name="Случай таблицы 1 для сжатого элемента", data_type="enum", role="input", enum_values=enum_values))
    if OUTPUT_QID not in quantities:
        out["quantities"].append(_quantity(OUTPUT_QID, name="Коэффициент условий работы при сжатии γc", data_type="number", role="calculated"))
    if EVIDENCE_QID not in quantities:
        out["quantities"].append(_quantity(EVIDENCE_QID, name="Основание выбора γc по таблице 1", data_type="object", role="calculated"))

    nodes = {n["id"]: n for n in out["nodes"]}
    if INPUT_NODE_ID not in nodes:
        out["nodes"].append(_input_node())
    if CALC_NODE_ID not in nodes:
        out["nodes"].append(_calc_node())

    # Replace the old direct v0.76 handoff.  This is the only active compression
    # route change: effective-length authoring is preserved, then gamma_c is
    # explicitly classified, then the same canonical z/y state continues.
    out["edges"] = [edge for edge in out["edges"] if edge.get("id") != EDGE_INPUT_TO_STATE_V076]
    existing = {edge["id"] for edge in out["edges"]}
    additions = [
        _edge("V078_E_EFFECTIVE_LENGTH_TO_GAMMA_C", V076_INPUT_NODE_ID, INPUT_NODE_ID),
        _edge("V078_E_GAMMA_C_INPUT_TO_LOOKUP", INPUT_NODE_ID, CALC_NODE_ID, [INPUT_QID]),
        _edge("V078_E_GAMMA_C_TO_EFFECTIVE_STATE", CALC_NODE_ID, STATE_NODE_ID, [OUTPUT_QID]),
    ]
    out["edges"].extend(edge for edge in additions if edge["id"] not in existing)
    out["graph_id"] = graph_id + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.78 requires an explicit SP16 Table-1 compression working-condition classification "
        "before canonical z/y compression verification."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    table = dict(out.get("node_presentation") or {})
    table[INPUT_NODE_ID] = {
        "component": "sp16_table1_gamma_c_compression",
        "stage": "СП16 · п. 4.3.2",
        "title": "Коэффициент условий работы γc",
        "subtitle": "Выберите применимый случай таблицы 1. Для случая, не указанного в таблице, используется только явно выбранное примечание 5.",
        "options": copy.deepcopy(compression_case_options()),
    }
    out["node_presentation"] = table
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=transform_presentation_policy(model.presentation_policy),
    )


def replay_prefix_on_model(session: GuidedCalculationSession, model: FireDAGModel, registry: ExecutionRegistry) -> GuidedCalculationSession:
    """Replay old answers onto v0.78 while preserving explicit Table-3 input.

    material_safety_category is authored inside the material card and therefore
    is not its own interaction-history row.  Preserve it if and only if it is
    already present and valid in the source session; never infer a replacement.
    """
    migrated = GuidedCalculationSession(model, entry_node_id=session.entry_node_id, registry=registry)
    category = session.plain_values().get(MATERIAL_SAFETY_QUANTITY_ID)
    if category is not None:
        try:
            material_safety_factor(category)
        except (KeyError, TypeError, ValueError):
            category = None

    injected = False
    for row in copy.deepcopy(session.interaction_history):
        expected = str(row.get("node_id") or "")
        if migrated.current_node_id != expected:
            break
        if expected == MATERIAL_EDITOR_NODE_ID and category is not None and not injected:
            migrated._set_quantity(
                MATERIAL_SAFETY_QUANTITY_ID,
                category,
                node_id=MATERIAL_SAFETY_INPUT_NODE_ID,
                source_kind="USER_INPUT",
                provenance={
                    "ui_surface": "v0.78_graph_migration",
                    "standard": "SP16 Table 3",
                    "migration": "preserve_existing_explicit_material_safety_category",
                },
            )
            injected = True
        migrated.submit(row.get("payload"), provenance=row.get("provenance"))
    return migrated


__all__ = [
    "CALC_NODE_ID", "GRAPH_SUFFIX", "INPUT_NODE_ID", "build_model", "replay_prefix_on_model",
    "transform_graph", "transform_presentation_policy",
]
