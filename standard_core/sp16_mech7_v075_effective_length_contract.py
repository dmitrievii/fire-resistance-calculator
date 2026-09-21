"""v0.75 canonical z/y effective-length contract for the guided SP16 MECH7 route.

The frozen v0.67 DAG is retained as release evidence, but the active guided
Streamlit model is upgraded in-memory so Section 10 effective-length inputs are
asked before the MECH7 evidence binder.  The active principal stability axes are
``z`` (strong) and ``y`` (weak).  No active user-facing stability quantity uses
``x`` as a principal axis; ``x`` is reserved for the member longitudinal axis /
torsion in the project-wide convention.

Historical x/y quantity IDs are never written to the session ledger by this
module.  The old MECH7 binder is called through a local transport adapter only,
so archived implementation IDs cannot leak back into the active contract.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from .axial_members import central_compression_stability_coefficient, relative_slenderness
from .effective_lengths_and_limiting_slenderness import (
    column_effective_length_eq140,
    table_30_effective_length_factor,
)
from .fire_ui0 import (
    ExecutionRegistry,
    FireDAGModel,
    FireUIError,
    GuidedCalculationSession,
)
from .profile_catalog import InterimProfileCatalog
from .sp16_mech7_v072_remediation import _geometry_inputs, _material_formula_inputs
from .sp16_mech7_v074_physical_remediation import _hydrate_source_backed_n1_prerequisites

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
    {"value": f"scheme_{i}", "label": f"Схема {i}", "description": desc}
    for i, desc in enumerate(
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
    out: dict[str, Any] = {
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
        out["enum_values"] = copy.deepcopy(enum_values)
    return out


def _cmp(qid: str, value: Any) -> dict[str, Any]:
    return {"type": "comparison", "quantity_id": qid, "operator": "eq", "value": value}


def _input_node(
    nid: str,
    title: str,
    produces: list[tuple[str, bool]],
    *,
    section: str = "10",
    clause: str | None = None,
    table: str | None = None,
    prompt: str | None = None,
) -> dict[str, Any]:
    ref: dict[str, Any] = {"standard_id": "SP16_2017", "reference_kind": "clause", "section": section}
    if clause:
        ref["clause"] = clause
    if table:
        ref["reference_kind"] = "table"
        ref["table_ref"] = table
    return {
        "id": nid,
        "node_type": "input",
        "owner_standard_id": "SP16_2017",
        "title": title,
        "normative_refs": [ref],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": req, "binding_role": "output"} for qid, req in produces],
        "applicability": None,
        "input_spec": {"input_method": "user_input", "required": True, "user_prompt": prompt or title},
        "notes": {
            "engineering_meaning": "v0.75 canonical z/y Section 10 guided input.",
            "limitations": None,
            "normative_warning": "Ось x не используется как главная ось сечения в активном контракте.",
        },
    }


def _decision_node(nid: str, title: str, qid: str, options: list[dict[str, Any]], *, prompt: str) -> dict[str, Any]:
    return {
        "id": nid,
        "node_type": "decision",
        "owner_standard_id": "SP16_2017",
        "title": title,
        "normative_refs": [
            {
                "standard_id": "SP16_2017",
                "reference_kind": "clause",
                "section": "10",
                "clause": "10.3",
            }
        ],
        "consumes": [],
        "produces": [{"quantity_id": qid, "required": True, "binding_role": "output"}],
        "applicability": None,
        "question": prompt,
        "decision_quantity_id": qid,
        "options": copy.deepcopy(options),
        "notes": {
            "engineering_meaning": "Selects the source-traced effective-length route for one canonical principal axis.",
            "limitations": None,
            "normative_warning": "Числовое значение расчётной длины не подставляется без выбранного нормативного маршрута.",
        },
    }


def _edge(eid: str, a: str, b: str, *, condition: Mapping[str, Any] | None = None, qids: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": eid,
        "from_node_id": a,
        "to_node_id": b,
        "edge_type": "branch" if condition is not None else "control",
        "label": eid,
        "condition": copy.deepcopy(condition),
        "quantity_ids": list(qids or []),
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Return the v0.75 active graph with the missing N7 guided block inserted."""
    out = copy.deepcopy(dict(graph))
    if str(out.get("graph_id", "")).endswith(GRAPH_SUFFIX):
        return out

    quantities = {q["id"]: q for q in out["quantities"]}
    nodes = {n["id"]: n for n in out["nodes"]}

    new_quantities = [
        _q("sp16_member_length_mm", "Геометрическая длина элемента L", unit="mm"),
        _q(
            "sp16_effective_length_route_z",
            "Маршрут определения расчётной длины по сильной оси z",
            dtype="enum",
            role="decision_state",
            enum_values=[
                {"value": "table30", "label": "Таблица 30 СП16", "description": "Расчёт μ по выбранной схеме таблицы 30."},
                {"value": "verified_analysis", "label": "Проверенная расчётная модель / специальный маршрут СП16", "description": "Задать l_eff с обязательным основанием."},
            ],
        ),
        _q(
            "sp16_effective_length_route_y",
            "Маршрут определения расчётной длины по слабой оси y",
            dtype="enum",
            role="decision_state",
            enum_values=[
                {"value": "table30", "label": "Таблица 30 СП16", "description": "Расчёт μ по выбранной схеме таблицы 30."},
                {"value": "verified_analysis", "label": "Проверенная расчётная модель / специальный маршрут СП16", "description": "Задать l_eff с обязательным основанием."},
            ],
        ),
        _q("sp16_table30_scheme_z", "Схема закрепления по таблице 30 для сильной оси z", dtype="enum", enum_values=_TABLE30_OPTIONS),
        _q("sp16_table30_scheme_y", "Схема закрепления по таблице 30 для слабой оси y", dtype="enum", enum_values=_TABLE30_OPTIONS),
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
        _q("sp16_curve_z", "Тип кривой устойчивости по таблице 7 для оси z", dtype="enum", role="intermediate", source="CALCULATED",
           enum_values=[{"value": x, "label": x} for x in ("a", "b", "c")]),
        _q("sp16_curve_y", "Тип кривой устойчивости по таблице 7 для оси y", dtype="enum", role="intermediate", source="CALCULATED",
           enum_values=[{"value": x, "label": x} for x in ("a", "b", "c")]),
        _q("phi_z_sp16", "Коэффициент устойчивости φz", role="intermediate", source="CALCULATED"),
        _q("phi_y_sp16", "Коэффициент устойчивости φy", role="intermediate", source="CALCULATED"),
        _q("sp16_v075_axis_contract", "Активный контракт главных осей z/y", dtype="object", role="intermediate", source="CALCULATED"),
    ]
    for q in new_quantities:
        if q["id"] not in quantities:
            out["quantities"].append(q)
            quantities[q["id"]] = q

    length_node = _input_node(
        "SP16_I_V075_MEMBER_LENGTH",
        "СП16 — геометрическая длина элемента",
        [("sp16_member_length_mm", True)],
        clause="10.3.1",
        prompt="Задайте геометрическую длину элемента L, мм.",
    )
    route_z = _decision_node(
        "SP16_D_V075_EFFECTIVE_ROUTE_Z",
        "СП16 — расчётная длина по сильной оси z",
        "sp16_effective_length_route_z",
        quantities["sp16_effective_length_route_z"]["enum_values"],
        prompt="Как определяется расчётная длина в плоскости потери устойчивости относительно сильной оси z?",
    )
    scheme_z = {
        **_decision_node(
            "SP16_D_V075_TABLE30_Z",
            "СП16 — закрепление по сильной оси z",
            "sp16_table30_scheme_z",
            _TABLE30_OPTIONS,
            prompt="Выберите фактическую схему закрепления элемента по таблице 30 СП16 для сильной оси z.",
        ),
        "normative_refs": [{"standard_id": "SP16_2017", "reference_kind": "table", "section": "10", "clause": "10.3.3", "table_ref": "30"}],
    }
    verified_z = _input_node(
        "SP16_I_V075_VERIFIED_LEFF_Z",
        "СП16 — l_eff,z из проверенной расчётной модели",
        [("sp16_verified_l_eff_z_mm", True), ("sp16_verified_l_eff_z_basis", True)],
        clause="10.3",
        prompt="Задайте l_eff,z и укажите расчётное/нормативное основание. Свободная числовая подстановка без основания запрещена.",
    )
    route_y = _decision_node(
        "SP16_D_V075_EFFECTIVE_ROUTE_Y",
        "СП16 — расчётная длина по слабой оси y",
        "sp16_effective_length_route_y",
        quantities["sp16_effective_length_route_y"]["enum_values"],
        prompt="Как определяется расчётная длина в плоскости потери устойчивости относительно слабой оси y?",
    )
    scheme_y = {
        **_decision_node(
            "SP16_D_V075_TABLE30_Y",
            "СП16 — закрепление по слабой оси y",
            "sp16_table30_scheme_y",
            _TABLE30_OPTIONS,
            prompt="Выберите фактическую схему закрепления элемента по таблице 30 СП16 для слабой оси y.",
        ),
        "normative_refs": [{"standard_id": "SP16_2017", "reference_kind": "table", "section": "10", "clause": "10.3.3", "table_ref": "30"}],
    }
    verified_y = _input_node(
        "SP16_I_V075_VERIFIED_LEFF_Y",
        "СП16 — l_eff,y из проверенной расчётной модели",
        [("sp16_verified_l_eff_y_mm", True), ("sp16_verified_l_eff_y_basis", True)],
        clause="10.3",
        prompt="Задайте l_eff,y и укажите расчётное/нормативное основание. Свободная числовая подстановка без основания запрещена.",
    )
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
            {"quantity_id": qid, "required": qid in {
                "sp16_member_length_mm", "sp16_effective_length_route_z", "sp16_effective_length_route_y"
            }, "binding_role": "input"}
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
                "sp16_i_z", "sp16_i_y",
                "sp16_lambda_z_geom", "sp16_lambda_y_geom",
                "lambda_bar_z", "lambda_bar_y",
                "sp16_curve_z", "sp16_curve_y",
                "phi_z_sp16", "phi_y_sp16",
                "sp16_v075_axis_contract",
            )
        ],
        "applicability": None,
        "calculation_spec": {
            "formula_type": "executor",
            "expression_language": "executor_v1",
            "algorithm_id": "sp16_v075_effective_length_zy_v1",
            "bindings": [],
            "rounding": {"mode": "none"},
        },
        "notes": {
            "engineering_meaning": "Closes the missing Section 10 path before MECH7 and materializes only canonical z/y principal-axis stability quantities.",
            "limitations": "The verified-analysis route requires an explicit basis string and remains auditable; no free hidden effective length is accepted.",
            "normative_warning": "Relative slenderness uses design Ry, not Ryn/fy_norm. Principal-axis x aliases are not session quantities in v0.75.",
        },
    }

    for n in (length_node, route_z, scheme_z, verified_z, route_y, scheme_y, verified_y, state_node):
        if n["id"] not in nodes:
            out["nodes"].append(n)
            nodes[n["id"]] = n

    # Rewire only the active MECH7 compression branch. Historical N7 nodes stay
    # in the frozen graph as evidence but are no longer on the active path.
    out["edges"] = [e for e in out["edges"] if e.get("id") != "MECH7_E_BRITTLE_TO_COMPRESSION"]
    new_edges = [
        _edge("V075_E_BRITTLE_TO_LENGTH", "SP16_D_MECH7_BRITTLE_REQUIRED", "SP16_I_V075_MEMBER_LENGTH",
              condition={"type": "comparison", "quantity_id": "ambient_N_force", "operator": "lt", "value": 0.0},
              qids=["ambient_N_force"]),
        _edge("V075_E_LENGTH_TO_ROUTE_Z", "SP16_I_V075_MEMBER_LENGTH", "SP16_D_V075_EFFECTIVE_ROUTE_Z", qids=["sp16_member_length_mm"]),
        _edge("V075_E_ROUTE_Z_TABLE30", "SP16_D_V075_EFFECTIVE_ROUTE_Z", "SP16_D_V075_TABLE30_Z",
              condition=_cmp("sp16_effective_length_route_z", "table30"), qids=["sp16_effective_length_route_z"]),
        _edge("V075_E_ROUTE_Z_VERIFIED", "SP16_D_V075_EFFECTIVE_ROUTE_Z", "SP16_I_V075_VERIFIED_LEFF_Z",
              condition=_cmp("sp16_effective_length_route_z", "verified_analysis"), qids=["sp16_effective_length_route_z"]),
        _edge("V075_E_TABLE30_Z_TO_ROUTE_Y", "SP16_D_V075_TABLE30_Z", "SP16_D_V075_EFFECTIVE_ROUTE_Y", qids=["sp16_table30_scheme_z"]),
        _edge("V075_E_VERIFIED_Z_TO_ROUTE_Y", "SP16_I_V075_VERIFIED_LEFF_Z", "SP16_D_V075_EFFECTIVE_ROUTE_Y",
              qids=["sp16_verified_l_eff_z_mm", "sp16_verified_l_eff_z_basis"]),
        _edge("V075_E_ROUTE_Y_TABLE30", "SP16_D_V075_EFFECTIVE_ROUTE_Y", "SP16_D_V075_TABLE30_Y",
              condition=_cmp("sp16_effective_length_route_y", "table30"), qids=["sp16_effective_length_route_y"]),
        _edge("V075_E_ROUTE_Y_VERIFIED", "SP16_D_V075_EFFECTIVE_ROUTE_Y", "SP16_I_V075_VERIFIED_LEFF_Y",
              condition=_cmp("sp16_effective_length_route_y", "verified_analysis"), qids=["sp16_effective_length_route_y"]),
        _edge("V075_E_TABLE30_Y_TO_STATE", "SP16_D_V075_TABLE30_Y", STATE_NODE_ID, qids=["sp16_table30_scheme_y"]),
        _edge("V075_E_VERIFIED_Y_TO_STATE", "SP16_I_V075_VERIFIED_LEFF_Y", STATE_NODE_ID,
              qids=["sp16_verified_l_eff_y_mm", "sp16_verified_l_eff_y_basis"]),
        _edge("V075_E_STATE_TO_COMPRESSION_CLASS", STATE_NODE_ID, "SP16_I_MECH7_COMPRESSION_SLENDERNESS",
              qids=["phi_z_sp16", "phi_y_sp16", "sp16_lambda_z_geom", "sp16_lambda_y_geom", "lambda_bar_z", "lambda_bar_y"]),
    ]
    existing_ids = {e["id"] for e in out["edges"]}
    out["edges"].extend(e for e in new_edges if e["id"] not in existing_ids)

    # Rewrite the MECH7 binder contract itself to canonical z/y quantities. The
    # executor compatibility bridge is local and never writes legacy x aliases.
    binder = nodes.get(BINDER_NODE_ID)
    if binder:
        mapping = {
            "phi_x_sp16": "phi_z_sp16",
            "sp16_lambda_x_geom": "sp16_lambda_z_geom",
            "lambda_bar_x": "lambda_bar_z",
        }
        seen: set[str] = set()
        patched = []
        for b in binder.get("consumes", []):
            row = copy.deepcopy(b)
            row["quantity_id"] = mapping.get(row["quantity_id"], row["quantity_id"])
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
        " v0.75 active guided overlay inserts the omitted Section 10 effective-length questions "
        "and replaces principal-axis x/y stability semantics by canonical z/y semantics."
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


def _positive(values: Mapping[str, Any], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"SP16 v0.75 requires {key}")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise FireUIError(f"{key} must be a positive finite number")
    return result


def _profile_axis_state(values: Mapping[str, Any], catalog: InterimProfileCatalog) -> dict[str, Any]:
    ref = values.get("profile_ref")
    if not isinstance(ref, Mapping):
        raise FireUIError("v0.75 z/y effective-length route requires a resolved catalog profile_ref")
    try:
        bundle = catalog.resolve(
            int(ref["family_id"]),
            str(ref["designation"]),
            source_row_id=int(ref["source_row_id"]) if ref.get("source_row_id") is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise FireUIError("cannot resolve selected catalog profile for canonical z/y radii") from exc

    raw = bundle.get("catalog_properties_interim")
    derived = bundle.get("derived")
    table7 = bundle.get("sp16_table7")
    if not isinstance(raw, Mapping) or not isinstance(derived, Mapping) or not isinstance(table7, Mapping):
        raise FireUIError("selected profile lacks qualified inertia/radius/Table-7 properties")

    ix = float(raw["Ix_mm4"])
    iy = float(raw["Iy_mm4"])
    rx = float(derived["radius_x_mm"])
    ry = float(derived["radius_y_mm"])
    if min(ix, iy, rx, ry) <= 0.0:
        raise FireUIError("selected profile has invalid principal inertias or radii")

    # x/y here are historical source-column names only. Canonical semantics are
    # selected by physical major/minor inertia, then immediately exposed as z/y.
    if ix >= iy:
        return {
            "i_z": rx,
            "i_y": ry,
            "curve_z": str(table7["x"]["section_type"]),
            "curve_y": str(table7["y"]["section_type"]),
            "source_major_inertia_field": "Ix_mm4",
            "source_minor_inertia_field": "Iy_mm4",
        }
    return {
        "i_z": ry,
        "i_y": rx,
        "curve_z": str(table7["y"]["section_type"]),
        "curve_y": str(table7["x"]["section_type"]),
        "source_major_inertia_field": "Iy_mm4",
        "source_minor_inertia_field": "Ix_mm4",
    }


def _resolve_axis_effective_length(values: Mapping[str, Any], axis: str, length: float) -> tuple[float | None, float, dict[str, Any]]:
    route_key = f"sp16_effective_length_route_{axis}"
    route = values.get(route_key)
    if route == "table30":
        scheme = values.get(f"sp16_table30_scheme_{axis}")
        if not isinstance(scheme, str):
            raise FireUIError(f"Table 30 route for axis {axis} requires an explicit support scheme")
        mu = float(table_30_effective_length_factor(scheme))
        return mu, float(column_effective_length_eq140(length, mu)), {
            "route": "table30",
            "scheme_id": scheme,
            "mu": mu,
            "normative_scope": "SP16 10.3.3 Table 30 + Eq.(140)",
        }
    if route == "verified_analysis":
        leff = _positive(values, f"sp16_verified_l_eff_{axis}_mm")
        basis = values.get(f"sp16_verified_l_eff_{axis}_basis")
        if not isinstance(basis, str) or not basis.strip():
            raise FireUIError(f"verified l_eff,{axis} requires a non-empty calculation/normative basis")
        return None, leff, {
            "route": "verified_analysis",
            "basis": basis.strip(),
            "normative_scope": "explicit source-traced SP16 Section 10 route",
        }
    raise FireUIError(f"unsupported effective-length route for axis {axis}: {route!r}")


def effective_length_state(values: Mapping[str, Any], catalog: InterimProfileCatalog) -> dict[str, Any]:
    hydrated = _hydrate_source_backed_n1_prerequisites(values)
    _material_formula_inputs(values, hydrated)
    _geometry_inputs(values, hydrated)

    length = _positive(hydrated, "sp16_member_length_mm")
    ry_design = _positive(hydrated, "Ry_formula")
    elastic = _positive(hydrated, "E_norm")
    profile = _profile_axis_state(hydrated, catalog)

    mu_z, leff_z, route_z = _resolve_axis_effective_length(hydrated, "z", length)
    mu_y, leff_y, route_y = _resolve_axis_effective_length(hydrated, "y", length)
    iz, iy = float(profile["i_z"]), float(profile["i_y"])

    lambda_z = leff_z / iz
    lambda_y = leff_y / iy
    lambda_bar_z = relative_slenderness(lambda_z, ry_design, elastic)
    lambda_bar_y = relative_slenderness(lambda_y, ry_design, elastic)
    curve_z = str(profile["curve_z"])
    curve_y = str(profile["curve_y"])
    phi_z = central_compression_stability_coefficient(lambda_bar_z, curve_z)
    phi_y = central_compression_stability_coefficient(lambda_bar_y, curve_y)

    result: dict[str, Any] = {
        "sp16_l_eff_z": leff_z,
        "sp16_l_eff_y": leff_y,
        "sp16_i_z": iz,
        "sp16_i_y": iy,
        "sp16_lambda_z_geom": lambda_z,
        "sp16_lambda_y_geom": lambda_y,
        "lambda_bar_z": lambda_bar_z,
        "lambda_bar_y": lambda_bar_y,
        "sp16_curve_z": curve_z,
        "sp16_curve_y": curve_y,
        "phi_z_sp16": phi_z,
        "phi_y_sp16": phi_y,
        "sp16_v075_axis_contract": {
            "schema": "sp16_v075_principal_axis_contract_v1",
            "member_longitudinal_axis": "x",
            "principal_strong_axis": "z",
            "principal_weak_axis": "y",
            "torsion_moment_symbol": "Mx",
            "bending_moment_symbols": ["Mz", "My"],
            "shear_symbols": ["Qy", "Qz"],
            "legacy_principal_x_semantics_active": False,
            "relative_slenderness_strength_basis": "Ry_formula",
            "profile_axis_mapping": {
                "method": "major_minor_inertia_to_canonical_z_y",
                "major_source_field": profile["source_major_inertia_field"],
                "minor_source_field": profile["source_minor_inertia_field"],
            },
            "effective_length_z": route_z,
            "effective_length_y": route_y,
        },
    }
    if mu_z is not None:
        result["sp16_mu_z"] = mu_z
    if mu_y is not None:
        result["sp16_mu_y"] = mu_y
    return result


def install_registry_remediation(registry: ExecutionRegistry, catalog: InterimProfileCatalog) -> ExecutionRegistry:
    """Install the v0.75 state executor and canonical MECH7 binder wrapper."""
    registry.register(STATE_NODE_ID, lambda values, node: effective_length_state(values, catalog))

    current = registry.executors.get(BINDER_NODE_ID)
    if current is None:
        raise FireUIError(f"v0.75 remediation requires registered {BINDER_NODE_ID}")
    if getattr(current, "_sp16_v075_remediated", False):
        return registry

    # Peel v0.74/v0.72 wrappers: they materialize historical principal-axis x
    # aliases. v0.75 keeps their material/geometry source hydration but not that
    # axis adapter.
    base = current
    seen: set[int] = set()
    while id(base) not in seen:
        seen.add(id(base))
        nxt = getattr(base, "_sp16_v074_original", None)
        if nxt is None:
            nxt = getattr(base, "_sp16_v072_original", None)
        if nxt is None:
            break
        base = nxt

    def canonical(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        normalized = _hydrate_source_backed_n1_prerequisites(values)
        _material_formula_inputs(values, normalized)
        _geometry_inputs(values, normalized)

        # Private transport aliases for the pre-v0.75 implementation function.
        # They exist only in this ephemeral call mapping, never in the session
        # model or ledger, and preserve z/y semantics exactly.
        aliases = {
            "phi_x_sp16": "phi_z_sp16",
            "sp16_lambda_x_geom": "sp16_lambda_z_geom",
            "lambda_bar_x": "lambda_bar_z",
        }
        for legacy, canonical_key in aliases.items():
            if canonical_key in normalized:
                normalized[legacy] = normalized[canonical_key]

        result = dict(base(normalized, node))
        bundle = result.get("sp16_mech7_primary_evidence")
        if isinstance(bundle, Mapping):
            patched = dict(bundle)
            patched["v075_axis_contract"] = {
                "principal_axes": ["z", "y"],
                "legacy_principal_x_semantics_active": False,
                "transport_aliases_persisted": False,
                "relative_slenderness_strength_basis": "Ry_formula",
            }
            result["sp16_mech7_primary_evidence"] = patched
        return result

    setattr(canonical, "_sp16_v075_remediated", True)
    setattr(canonical, "_sp16_v075_original", base)
    registry.executors[BINDER_NODE_ID] = canonical
    return registry


def replay_prefix_on_model(
    session: GuidedCalculationSession,
    model: FireDAGModel,
    registry: ExecutionRegistry,
) -> GuidedCalculationSession:
    """Replay the unchanged prefix of one legacy session onto the v0.75 model.

    Replay stops at the first topology divergence (normally the newly inserted
    member-length card). The original session is not mutated.
    """
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
    "STATE_NODE_ID",
    "build_model",
    "effective_length_state",
    "install_registry_remediation",
    "replay_prefix_on_model",
    "transform_graph",
    "transform_presentation_policy",
]
