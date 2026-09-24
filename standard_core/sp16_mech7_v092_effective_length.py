"""v0.92 MECH7 effective-length closure over the audited Stage-N7 producer.

The historical v0.76 guided card supported only Table 30 and a direct verified
length.  Stage N7 already implements the broader SP16 Section 10 route census
(Tables 24-31, Equations 136-147 and explicit external-analysis routes).  This
module binds that existing producer into the active z/y guided state without
copying those normative formulae.

Frozen DAG files are not edited.  The active graph receives only one typed
calculation-evidence quantity and presentation metadata; the existing state node
keeps its identity so downstream MECH7/MECH8/MECH9 consumers remain stable.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from .axial_members import central_compression_stability_coefficient, relative_slenderness
from .effective_length_workflows import effective_length_guided_workflow
from .fire_ui0 import ExecutionRegistry, FireDAGModel, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech7_v072_remediation import _geometry_inputs, _material_formula_inputs
from .sp16_mech7_v074_physical_remediation import _hydrate_source_backed_n1_prerequisites
from .sp16_mech7_v076_graph_overlay import DEFINITION_QID, INPUT_NODE_ID, STATE_NODE_ID
from .sp16_mech7_v076_runtime import (
    _axis_effective_length as _legacy_axis_effective_length,
    _definition,
    _positive_number,
    _profile_axis_state,
    install_registry_remediation as install_v076_registry_remediation,
)

GRAPH_SUFFIX = "_v092_full_section10_effective_length"
EVIDENCE_QID = "sp16_effective_length_zy_trace"
SECTION10_METHOD = "section10_route"

SECTION10_ROUTE_KINDS: tuple[tuple[str, str], ...] = (
    ("eq136_truss_chord_in_plane", "Ферма: пояс в плоскости — формула (136)"),
    ("eq137_truss_chord_out_of_plane", "Ферма: пояс из плоскости — формула (137)"),
    ("eq138_built_up_branch_in_plane", "Сквозной стержень: ветвь в плоскости — формула (138)"),
    ("eq139_built_up_branch_out_of_plane", "Сквозной стержень: ветвь из плоскости — формула (139)"),
    ("table24_truss_member", "Элементы ферм — таблица 24"),
    ("table25_cross_lattice", "Перекрёстная решётка — таблица 25"),
    ("table26_structural_member", "Конструктивные элементы — таблица 26"),
    ("table27_29_spatial_member", "Пространственные элементы — таблицы 27–29"),
    ("table30_column", "Колонна постоянного сечения — таблица 30 + (140)"),
    ("table31_frame_column", "Колонна рамы — таблица 31 + (141)–(147)"),
    ("out_of_plane_column_10_3_9", "Колонна из плоскости — п. 10.3.9"),
    ("gallery_support_10_3_10", "Опора галереи — п. 10.3.10"),
    ("stepped_column_10_3_7_external", "Ступенчатая колонна — п. 10.3.7 / приложение И / расчётная модель"),
    ("certified_software_10_3_11", "Сертифицированное ПО — п. 10.3.11"),
    ("crossing_brace_external_10_1_3", "Перекрёстные раскосы — п. 10.1.3 / внешний нормативный маршрут"),
)


def _axis_effective_length(
    definition: Mapping[str, Any], axis: str, radius_mm: float
) -> tuple[float | None, float, dict[str, Any]]:
    axis_def = definition.get(axis)
    if not isinstance(axis_def, Mapping):
        raise FireUIError(f"effective-length definition requires axis {axis}")
    method = axis_def.get("method")
    if method != SECTION10_METHOD:
        return _legacy_axis_effective_length(definition, axis)

    route = axis_def.get("route")
    if not isinstance(route, Mapping):
        raise FireUIError(f"SP16 Section 10 route for axis {axis} must be an object")
    kind = route.get("kind")
    allowed = {row[0] for row in SECTION10_ROUTE_KINDS}
    if kind not in allowed:
        raise FireUIError(
            f"unsupported SP16 Section 10 route for axis {axis}: {kind!r}"
        )

    case = {
        "case_id": f"MECH7-V092-{axis}",
        "standard": "СП 16.13330.2017",
        "action": "effective_length_guided",
        "effective_length_route": copy.deepcopy(dict(route)),
        # The selected catalog profile already resolved the canonical radius for
        # this axis.  Section-10 routing determines l_eff only here; the later
        # MECH7 state uses the same radius to form lambda=l_eff/i.
        "radius": {"mode": "explicit", "value_mm": float(radius_mm)},
        "limiting_slenderness": {"mode": "none", "group_4_applies": False},
    }
    try:
        workflow = effective_length_guided_workflow(case)
    except (KeyError, TypeError, ValueError) as exc:
        raise FireUIError(
            f"SP16 Section 10 effective-length route for axis {axis} is invalid: {exc}"
        ) from exc

    effective = workflow.get("effective_length")
    if not isinstance(effective, Mapping):
        raise FireUIError(f"SP16 Section 10 route for axis {axis} returned no effective-length trace")
    leff = effective.get("effective_length_mm")
    if workflow.get("status") != "COMPLETE" or not isinstance(leff, (int, float)) or isinstance(leff, bool):
        unresolved = workflow.get("required_unresolved") or effective.get("required") or "unresolved Section-10 prerequisite"
        raise FireUIError(
            f"SP16 Section 10 effective-length route for axis {axis} is fail-closed: {unresolved}"
        )
    leff = _positive_number(leff, f"l_eff,{axis}")
    mu_raw = effective.get("mu")
    mu = float(mu_raw) if isinstance(mu_raw, (int, float)) and not isinstance(mu_raw, bool) and math.isfinite(float(mu_raw)) else None
    trace = {
        "method": SECTION10_METHOD,
        "axis": axis,
        "route_kind": str(kind),
        "effective_length_mm": leff,
        "mu": mu,
        "normative_scope": "SP16 Section 10 audited Stage N7 producer",
        "stage_n7_workflow": copy.deepcopy(workflow),
    }
    return mu, leff, trace


def effective_length_state_v092(
    values: Mapping[str, Any], catalog: InterimProfileCatalog
) -> dict[str, Any]:
    """Build canonical z/y l_eff, slenderness and phi using the full Stage-N7 route set."""
    hydrated = _hydrate_source_backed_n1_prerequisites(values)
    _material_formula_inputs(values, hydrated)
    _geometry_inputs(values, hydrated)

    definition = _definition(hydrated)
    ry_design = _positive_number(hydrated.get("Ry_formula"), "Ry_formula")
    elastic = _positive_number(hydrated.get("E_norm"), "E_norm")
    profile = _profile_axis_state(hydrated, catalog)
    iz = float(profile["i_z"])
    iy = float(profile["i_y"])

    mu_z, leff_z, route_z = _axis_effective_length(definition, "z", iz)
    mu_y, leff_y, route_y = _axis_effective_length(definition, "y", iy)
    lambda_z = leff_z / iz
    lambda_y = leff_y / iy
    lambda_bar_z = relative_slenderness(lambda_z, ry_design, elastic)
    lambda_bar_y = relative_slenderness(lambda_y, ry_design, elastic)
    curve_z = str(profile["curve_z"])
    curve_y = str(profile["curve_y"])
    phi_z = central_compression_stability_coefficient(lambda_bar_z, curve_z)
    phi_y = central_compression_stability_coefficient(lambda_bar_y, curve_y)

    evidence = {
        "schema": "sp16_v092_effective_length_zy_trace_v1",
        "normative_basis": "СП 16.13330.2017 с изменениями 1–6, раздел 10",
        "axis_convention": {
            "z": "strong principal axis",
            "y": "weak principal axis",
        },
        "z": {
            "route": copy.deepcopy(route_z),
            "radius_mm": iz,
            "effective_length_mm": leff_z,
            "lambda": lambda_z,
            "lambda_bar": lambda_bar_z,
            "curve": curve_z,
            "phi": phi_z,
        },
        "y": {
            "route": copy.deepcopy(route_y),
            "radius_mm": iy,
            "effective_length_mm": leff_y,
            "lambda": lambda_y,
            "lambda_bar": lambda_bar_y,
            "curve": curve_y,
            "phi": phi_y,
        },
        "governing_axis_by_phi": "z" if phi_z <= phi_y else "y",
        "formula_chain": [
            "l_eff = Section-10 route result",
            "lambda = l_eff / i",
            "lambda_bar = lambda * sqrt(Ry/E)",
            "phi = SP16 Table 7 stability curve",
        ],
    }
    contract = {
        "schema": "sp16_v092_effective_length_zy_v1",
        "principal_strong_axis": "z",
        "principal_weak_axis": "y",
        "legacy_principal_x_semantics_active": False,
        "principal_x_transport_alias_used": False,
        "relative_slenderness_strength_basis": "Ry_formula",
        "profile_mapping": {
            "method": profile["mapping_method"],
            "catalog_identity": profile["catalog_identity"],
            "profile_ref_required": False,
        },
        "effective_length_z": copy.deepcopy(route_z),
        "effective_length_y": copy.deepcopy(route_y),
    }
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
        "sp16_v075_axis_contract": contract,
        EVIDENCE_QID: evidence,
    }
    if mu_z is not None:
        result["sp16_mu_z"] = mu_z
    if mu_y is not None:
        result["sp16_mu_y"] = mu_y
    return result


def _trace_quantity() -> dict[str, Any]:
    return {
        "id": EVIDENCE_QID,
        "symbol": None,
        "name_ru": "Trace расчётных длин, гибкости и коэффициентов устойчивости по осям z/y",
        "data_type": "object",
        "role": "calculation_evidence",
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {"primary_source_type": "CALCULATED"},
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    nodes = {row["id"]: row for row in out.get("nodes", []) if isinstance(row, Mapping)}
    state = nodes.get(STATE_NODE_ID)
    if state is None:
        raise FireUIError(f"v0.92 effective-length overlay requires {STATE_NODE_ID}")
    qids = {row.get("id") for row in out.get("quantities", []) if isinstance(row, Mapping)}
    if EVIDENCE_QID not in qids:
        out.setdefault("quantities", []).append(_trace_quantity())
    produced = {row.get("quantity_id") for row in state.get("produces", []) if isinstance(row, Mapping)}
    if EVIDENCE_QID not in produced:
        state.setdefault("produces", []).append(
            {"quantity_id": EVIDENCE_QID, "required": True, "binding_role": "output"}
        )
    spec = dict(state.get("calculation_spec") or {})
    spec["algorithm_id"] = "sp16_mech7_v092_full_section10_zy_v1"
    state["calculation_spec"] = spec
    notes = dict(state.get("notes") or {})
    notes["engineering_meaning"] = (
        "Active z/y MECH7 state accepts Table 30, source-traced direct l_eff, or any audited Stage-N7 Section-10 route."
    )
    notes["normative_warning"] = (
        "Section-10 equations/tables are executed only by effective_length_guided_workflow; this overlay does not duplicate them."
    )
    state["notes"] = notes
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.92 binds the complete audited SP16 Section-10 effective-length route set into the canonical z/y MECH7 state."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))
    table = out.setdefault("node_presentation", {})
    row = dict(table.get(INPUT_NODE_ID) or {})
    row.update(
        {
            "component": "effective_length_zy_editor",
            "stage": "СП16 · Stage N7",
            "title": "Расчётные длины элемента",
            "subtitle": (
                "Для каждой главной оси выберите таблицу 30, подтверждённую расчётную длину или полный нормативный маршрут СП16 раздела 10."
            ),
            "section10_route_options": [
                {"value": value, "label": label} for value, label in SECTION10_ROUTE_KINDS
            ],
        }
    )
    table[INPUT_NODE_ID] = row
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=transform_presentation_policy(model.presentation_policy),
    )


def install_registry_remediation(
    registry: ExecutionRegistry, catalog: InterimProfileCatalog
) -> ExecutionRegistry:
    install_v076_registry_remediation(registry, catalog)
    executor = lambda values, node: effective_length_state_v092(values, catalog)
    setattr(executor, "_sp16_v092_effective_length_remediated", True)
    registry.register(STATE_NODE_ID, executor)
    return registry


__all__ = [
    "EVIDENCE_QID",
    "GRAPH_SUFFIX",
    "SECTION10_METHOD",
    "SECTION10_ROUTE_KINDS",
    "build_model",
    "effective_length_state_v092",
    "install_registry_remediation",
    "transform_graph",
    "transform_presentation_policy",
]
