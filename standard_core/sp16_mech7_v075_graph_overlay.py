"""Active v0.75 graph overlay for the missing SP16 Stage-N7 guided contract.

The frozen v0.67 DAG remains unchanged on disk as release evidence.  This module
builds the active guided model in memory.  It inserts the omitted Section-10
member-length/effective-length questions and changes the active stability
contract from the historical principal x/y vocabulary to z/y.

This file contains graph/presentation migration only.  It intentionally contains
no numerical stability executor and no x-to-z transport alias.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession

BINDER_NODE_ID = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"
STATE_NODE_ID = "SP16_C_V075_EFFECTIVE_LENGTH_STATE"
GRAPH_SUFFIX = "_v075_stage_n7_zy_contract"

LEGACY_N7_INTERACTIVE_NODES = {
    "SP16_D_MU_ROUTE_X",
    "SP16_D_MU_SCHEME_X",
    "SP16_D_MU_ROUTE_Y",
    "SP16_D_MU_SCHEME_Y",
    "SP16_I_MU_ANALYSIS_X",
    "SP16_I_MU_ANALYSIS_Y",
    "SP16_I_MU_ADVANCED_X",
    "SP16_I_MU_ADVANCED_Y",
}

_TABLE30_OPTIONS = [
    {"value": f"scheme_{i}", "label": f"Схема {i}", "description": description}
    for i, description in enumerate(
        (
            "Таблица 30: μ = 1,00.",
            "Таблица 30: μ = 0,70.",
            "Таблица 30: μ = 0,50.",
            "Таблица 30: μ = 2,00.",
            "Таблица 30: μ = 1,00.",
            "Таблица 30: μ = 2,00.",
            "Таблица 30: μ = 0,725.",
            "Таблица 30: μ = 1,12.",
        ),
        start=1,
    )
]


def _q(
    qid: str,
    name: str,
    *,
    dtype: str = "number",
    role: str = "input",
    unit: str | None = None,
    source: str = "USER_INPUT",
    enum_values: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": qid,
        "symbol": None,
        "name_ru": name,
        "data_type": dtype,
        "role": role,
        "physical_dimension": "length" if unit == "mm" else None,
        "canonical_unit": unit,
        "allowed_units": [unit] if unit else [],
        "source_policy": {
            "primary_source_type": source,
            "allowed_source_types": [source],
            "override_policy": "forbidden",
        },
    }
    if enum_values is not None:
        row["enum_values"] = copy.deepcopy(enum_values)
    return row


def _cmp(qid: str, value: Any) -> dict[str, Any]:
    return {"type": "comparison", "quantity_id": qid, "operator": "eq", "value": value}


def _input_node(
    node_id: str,
    title: str,
    produces: list[tuple[str, bool]],
    *,
    clause: str,
    prompt: str,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": title,
        "normative_refs": [
            {
                "standard_id": "SP16_2017",
                "reference_kind": "clause",
                "section": "10",
                "clause": clause,
            }
        ],
        "consumes": [],
        "produces": [
            {"quantity_id": qid, "required": required, "binding_role": "output"}
            for qid, required in produces
        ],
        "applicability": None,
        "input_spec": {
            "input_method": "user_input",
            "required": True,
            "user_prompt": prompt,
        },
        "notes": {
            "engineering_meaning": "Canonical z/y Stage-N7 guided input.",
            "limitations": None,
            "normative_warning": "Главные оси активного контракта: z (сильная) и y (слабая).",
        },
    }


def _decision_node(
    node_id: str,
    title: str,
    qid: str,
    options: list[dict[str, Any]],
    *,
    prompt: str,
    table30: bool = False,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "standard_id": "SP16_2017",
        "reference_kind": "clause",
        "section": "10",
        "clause": "10.3",
    }
    if table30:
        ref.update({"reference_kind": "table", "clause": "10.3.3", "table_ref": "30"})
    return {
        "id": node_id,
        "node_type": "decision",
        "owner_standard_id": "SP16_2017",
        "title": title,
        "normative_refs": [ref],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": True, "binding_role": "output"}],
        "applicability": None,
        "question": prompt,
        "decision_quantity_id": qid,
        "options": copy.deepcopy(options),
        "notes": {
            "engineering_meaning": "Source-traced effective-length route for one canonical principal axis.",
            "limitations": None,
            "normative_warning": "Расчётная длина не подставляется без явного нормативного маршрута.",
        },
    }


def _edge(
    edge_id: str,
    from_node: str,
    to_node: str,
    *,
    condition: Mapping[str, Any] | None = None,
    qids: list[str] | None = None,
) -> dict[str, Any]:
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
    """Insert the omitted Stage-N7 questions and expose only z/y stability IDs."""
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    quantities = {q["id"]: q for q in out["quantities"]}
    nodes = {n["id"]: n for n in out["nodes"]}

    route_options = [
        {
            "value": "table30",
            "label": "Таблица 30 СП16",
            "description": "Определить μ по выбранной схеме таблицы 30.",
        },
        {
            "value": "verified_analysis",
            "label": "Проверенная расчётная модель / специальный маршрут СП16",
            "description": "Задать l_eff с обязательным расчётным или нормативным основанием.",
        },
    ]

    additions = [
        _q("sp16_member_length_mm", "Геометрическая длина элемента L", unit="mm"),
        _q("sp16_effective_length_route_z", "Маршрут расчётной длины по сильной оси z", dtype="enum", role="decision_state", enum_values=route_options),
        _q("sp16_effective_length_route_y", "Маршрут расчётной длины по слабой оси y", dtype="enum", role="decision_state", enum_values=route_options),
        _q("sp16_table30_scheme_z", "Схема таблицы 30 для сильной оси z", dtype="enum", enum_values=_TABLE30_OPTIONS),
        _q("sp16_table30_scheme_y", "Схема таблицы 30 для слабой оси y", dtype="enum", enum_values=_TABLE30_OPTIONS),
        _q("sp16_verified_l_eff_z_mm", "Расчётная длина l_eff,z из проверенной модели", unit="mm"),
        _q("sp16_verified_l_eff_y_mm", "Расчётная длина l_eff,y из проверенной модели", unit="mm"),
        _q("sp16_verified_l_eff_z_basis", "Основание определения l_eff,z", dtype="text"),
        _q("sp16_verified_l_eff_y_basis", "Основание определения l_eff,y", dtype="text"),
        _q("sp16_mu_z", "Коэффициент расчётной длины μz", role="intermediate", source="CALCULATED"),
        _q("sp16_mu_y", "Коэффициент расчётной длины μy", role="intermediate", source="CALCULATED"),
        _q("sp16_l_eff_z", "Расчётная длина l_eff,z", role="intermediate", unit="mm", source="CALCULATED"),
        _q("sp16_l_eff_y", "Расчётная длина l_eff,y", role="intermediate", unit="mm", source="CALCULATED"),
        _q("sp16_i_z", "Радиус инерции iz по сильной оси z", role="intermediate", unit="mm", source="CALCULATED"),
        _q("sp16_i_y", "Радиус инерции iy по слабой оси y", role="intermediate", unit="mm", source="CALCULATED"),
        _q("sp16_lambda_z_geom", "Геометрическая гибкость λz", role="intermediate", source="CALCULATED"),
        _q("sp16_lambda_y_geom", "Геометрическая гибкость λy", role="intermediate", source="CALCULATED"),
        _q("lambda_bar_z", "Условная гибкость λ̄z", role="intermediate", source="CALCULATED"),
        _q("lambda_bar_y", "Условная гибкость λ̄y", role="intermediate", source="CALCULATED"),
        _q("sp16_curve_z", "Тип кривой устойчивости по таблице 7 для оси z", dtype="enum", role="intermediate", source="CALCULATED", enum_values=[{"value": v, "label": v} for v in ("a", "b", "c")]),
        _q("sp16_curve_y", "Тип кривой устойчивости по таблице 7 для оси y", dtype="enum", role="intermediate", source="CALCULATED", enum_values=[{"value": v, "label": v} for v in ("a", "b", "c")]),
        _q("phi_z_sp16", "Коэффициент устойчивости φz", role="intermediate", source="CALCULATED"),
        _q("phi_y_sp16", "Коэффициент устойчивости φy", role="intermediate", source="CALCULATED"),
        _q("sp16_v075_axis_contract", "Активный контракт главных осей z/y", dtype="object", role="intermediate", source="CALCULATED"),
    ]
    for quantity in additions:
        if quantity["id"] not in quantities:
            out["quantities"].append(quantity)
            quantities[quantity["id"]] = quantity

    new_nodes = [
        _input_node(
            "SP16_I_V075_MEMBER_LENGTH",
            "СП16 — геометрическая длина элемента",
            [("sp16_member_length_mm", True)],
            clause="10.3.1",
            prompt="Задайте геометрическую длину элемента L, мм.",
        ),
        _decision_node(
            "SP16_D_V075_EFFECTIVE_ROUTE_Z",
            "СП16 — расчётная длина по сильной оси z",
            "sp16_effective_length_route_z",
            route_options,
            prompt="Как определяется расчётная длина в плоскости потери устойчивости относительно сильной оси z?",
        ),
        _decision_node(
            "SP16_D_V075_TABLE30_Z",
            "СП16 — закрепление по сильной оси z",
            "sp16_table30_scheme_z",
            _TABLE30_OPTIONS,
            prompt="Выберите фактическую схему закрепления по таблице 30 СП16 для сильной оси z.",
            table30=True,
        ),
        _input_node(
            "SP16_I_V075_VERIFIED_LEFF_Z",
            "СП16 — l_eff,z из проверенной расчётной модели",
            [("sp16_verified_l_eff_z_mm", True), ("sp16_verified_l_eff_z_basis", True)],
            clause="10.3",
            prompt="Задайте l_eff,z и расчётное/нормативное основание. Свободная числовая подстановка запрещена.",
        ),
        _decision_node(
            "SP16_D_V075_EFFECTIVE_ROUTE_Y",
            "СП16 — расчётная длина по слабой оси y",
            "sp16_effective_length_route_y",
            route_options,
            prompt="Как определяется расчётная длина в плоскости потери устойчивости относительно слабой оси y?",
        ),
        _decision_node(
            "SP16_D_V075_TABLE30_Y",
            "СП16 — закрепление по слабой оси y",
            "sp16_table30_scheme_y",
            _TABLE30_OPTIONS,
            prompt="Выберите фактическую схему закрепления по таблице 30 СП16 для слабой оси y.",
            table30=True,
        ),
        _input_node(
            "SP16_I_V075_VERIFIED_LEFF_Y",
            "СП16 — l_eff,y из проверенной расчётной модели",
            [("sp16_verified_l_eff_y_mm", True), ("sp16_verified_l_eff_y_basis", True)],
            clause="10.3",
            prompt="Задайте l_eff,y и расчётное/нормативное основание. Свободная числовая подстановка запрещена.",
        ),
    ]

    state_node = {
        "id": STATE_NODE_ID,
        "node_type": "calculation",
        "owner_standard_id": "SP16_2017",
        "title": "СП16 — расчётные длины, гибкости и φ по каноническим осям z/y",
        "normative_refs": [
            {"standard_id": "SP16_2017", "reference_kind": "clause", "section": "7", "clause": "7.1.3"},
            {"standard_id": "SP16_2017", "reference_kind": "clause", "section": "10", "clause": "10.3.1"},
            {"standard_id": "SP16_2017", "reference_kind": "table", "section": "10", "clause": "10.3.3", "table_ref": "30"},
            {"standard_id": "SP16_2017", "reference_kind": "table", "section": "7", "clause": "7.1.3", "table_ref": "7"},
        ],
        "consumes": [
            {
                "quantity_id": qid,
                "required": qid in {"sp16_member_length_mm", "sp16_effective_length_route_z", "sp16_effective_length_route_y"},
                "binding_role": "input",
            }
            for qid in (
                "sp16_member_length_mm",
                "sp16_effective_length_route_z", "sp16_table30_scheme_z",
                "sp16_verified_l_eff_z_mm", "sp16_verified_l_eff_z_basis",
                "sp16_effective_length_route_y", "sp16_table30_scheme_y",
                "sp16_verified_l_eff_y_mm", "sp16_verified_l_eff_y_basis",
                "profile_ref", "A_gross", "Ry_formula", "E_norm",
            )
            if qid in quantities
        ],
        "produces": [
            {"quantity_id": qid, "required": qid not in {"sp16_mu_z", "sp16_mu_y"}, "binding_role": "output"}
            for qid in (
                "sp16_mu_z", "sp16_mu_y", "sp16_l_eff_z", "sp16_l_eff_y",
                "sp16_i_z", "sp16_i_y", "sp16_lambda_z_geom", "sp16_lambda_y_geom",
                "lambda_bar_z", "lambda_bar_y", "sp16_curve_z", "sp16_curve_y",
                "phi_z_sp16", "phi_y_sp16", "sp16_v075_axis_contract",
            )
        ],
        "applicability": None,
        "calculation_spec": {
            "formula_type": "executor",
            "expression_language": "executor_v1",
            "algorithm_id": "sp16_v075_effective_length_zy_v2",
            "bindings": [],
            "rounding": {"mode": "none"},
        },
        "notes": {
            "engineering_meaning": "Closes the omitted Section-10 guided path using only z/y principal-axis quantities.",
            "limitations": "Verified-analysis route requires explicit source/basis; no hidden l_eff is accepted.",
            "normative_warning": "Условная гибкость рассчитывается с Ry; principal-x alias отсутствует.",
        },
    }
    new_nodes.append(state_node)
    for node in new_nodes:
        if node["id"] not in nodes:
            out["nodes"].append(node)
            nodes[node["id"]] = node

    # Replace the direct compression jump with the explicit Stage-N7 sequence.
    out["edges"] = [edge for edge in out["edges"] if edge.get("id") != "MECH7_E_BRITTLE_TO_COMPRESSION"]
    new_edges = [
        _edge("V075_E_BRITTLE_TO_LENGTH", "SP16_D_MECH7_BRITTLE_REQUIRED", "SP16_I_V075_MEMBER_LENGTH", condition={"type": "comparison", "quantity_id": "ambient_N_force", "operator": "lt", "value": 0.0}, qids=["ambient_N_force"]),
        _edge("V075_E_LENGTH_TO_ROUTE_Z", "SP16_I_V075_MEMBER_LENGTH", "SP16_D_V075_EFFECTIVE_ROUTE_Z", qids=["sp16_member_length_mm"]),
        _edge("V075_E_ROUTE_Z_TABLE30", "SP16_D_V075_EFFECTIVE_ROUTE_Z", "SP16_D_V075_TABLE30_Z", condition=_cmp("sp16_effective_length_route_z", "table30"), qids=["sp16_effective_length_route_z"]),
        _edge("V075_E_ROUTE_Z_VERIFIED", "SP16_D_V075_EFFECTIVE_ROUTE_Z", "SP16_I_V075_VERIFIED_LEFF_Z", condition=_cmp("sp16_effective_length_route_z", "verified_analysis"), qids=["sp16_effective_length_route_z"]),
        _edge("V075_E_TABLE30_Z_TO_ROUTE_Y", "SP16_D_V075_TABLE30_Z", "SP16_D_V075_EFFECTIVE_ROUTE_Y", qids=["sp16_table30_scheme_z"]),
        _edge("V075_E_VERIFIED_Z_TO_ROUTE_Y", "SP16_I_V075_VERIFIED_LEFF_Z", "SP16_D_V075_EFFECTIVE_ROUTE_Y", qids=["sp16_verified_l_eff_z_mm", "sp16_verified_l_eff_z_basis"]),
        _edge("V075_E_ROUTE_Y_TABLE30", "SP16_D_V075_EFFECTIVE_ROUTE_Y", "SP16_D_V075_TABLE30_Y", condition=_cmp("sp16_effective_length_route_y", "table30"), qids=["sp16_effective_length_route_y"]),
        _edge("V075_E_ROUTE_Y_VERIFIED", "SP16_D_V075_EFFECTIVE_ROUTE_Y", "SP16_I_V075_VERIFIED_LEFF_Y", condition=_cmp("sp16_effective_length_route_y", "verified_analysis"), qids=["sp16_effective_length_route_y"]),
        _edge("V075_E_TABLE30_Y_TO_STATE", "SP16_D_V075_TABLE30_Y", STATE_NODE_ID, qids=["sp16_table30_scheme_y"]),
        _edge("V075_E_VERIFIED_Y_TO_STATE", "SP16_I_V075_VERIFIED_LEFF_Y", STATE_NODE_ID, qids=["sp16_verified_l_eff_y_mm", "sp16_verified_l_eff_y_basis"]),
        _edge("V075_E_STATE_TO_COMPRESSION_CLASS", STATE_NODE_ID, "SP16_I_MECH7_COMPRESSION_SLENDERNESS", qids=["phi_z_sp16", "phi_y_sp16", "sp16_lambda_z_geom", "sp16_lambda_y_geom", "lambda_bar_z", "lambda_bar_y"]),
    ]
    existing_edge_ids = {edge["id"] for edge in out["edges"]}
    out["edges"].extend(edge for edge in new_edges if edge["id"] not in existing_edge_ids)

    # The active binder contract is rewritten, not adapted at runtime through x.
    binder = nodes.get(BINDER_NODE_ID)
    if binder:
        replacement = {
            "phi_x_sp16": "phi_z_sp16",
            "sp16_lambda_x_geom": "sp16_lambda_z_geom",
            "lambda_bar_x": "lambda_bar_z",
        }
        patched: list[dict[str, Any]] = []
        seen: set[str] = set()
        for binding in binder.get("consumes", []):
            row = copy.deepcopy(binding)
            row["quantity_id"] = replacement.get(row["quantity_id"], row["quantity_id"])
            if row["quantity_id"] not in seen:
                patched.append(row)
                seen.add(row["quantity_id"])
        for qid in ("phi_z_sp16", "phi_y_sp16", "sp16_lambda_z_geom", "sp16_lambda_y_geom", "lambda_bar_z", "lambda_bar_y"):
            if qid not in seen:
                patched.append({"quantity_id": qid, "required": False, "binding_role": "input"})
                seen.add(qid)
        binder["consumes"] = patched

    out["graph_id"] = str(out["graph_id"]) + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.75 active overlay inserts the omitted Section-10 effective-length questions "
        "and uses canonical z/y principal-axis stability semantics without an x transport alias."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(LEGACY_N7_INTERACTIVE_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if str(model.graph.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=transform_presentation_policy(model.presentation_policy),
    )


def replay_prefix_on_model(
    session: GuidedCalculationSession,
    model: FireDAGModel,
    registry: ExecutionRegistry,
) -> GuidedCalculationSession:
    """Transactionally replay legacy interaction history until new topology diverges."""
    migrated = GuidedCalculationSession(model, entry_node_id=session.entry_node_id, registry=registry)
    for row in copy.deepcopy(session.interaction_history):
        expected = str(row.get("node_id") or "")
        if migrated.current_node_id != expected:
            break
        migrated.submit(row.get("payload"), provenance=row.get("provenance"))
    return migrated


__all__ = [
    "BINDER_NODE_ID",
    "GRAPH_SUFFIX",
    "LEGACY_N7_INTERACTIVE_NODES",
    "STATE_NODE_ID",
    "build_model",
    "replay_prefix_on_model",
    "transform_graph",
    "transform_presentation_policy",
]
