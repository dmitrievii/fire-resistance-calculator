"""v0.75 canonical z/y runtime for the guided SP16 Stage-N7 route.

This module deliberately does not materialize or transport principal-axis ``x``
aliases.  The historical frozen graph remains release evidence; the active
Streamlit overlay uses z (strong) and y (weak) for effective length, geometric
slenderness, relative slenderness and central-compression stability.

The historical MECH7 primary binder is retained for non-compression routes.  For
compression routes this module binds the qualified scalar procedures directly to
the z/y quantities.  Any compression+bending route that still depends on the
pre-migration Mx/Ix convention is left DEFERRED rather than reinterpreting x as z.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import sp16_mech7_v075_effective_length_contract as _graph
from .axial_members import central_compression_stability_coefficient, central_compression_stability_utilization, relative_slenderness
from .effective_lengths_and_limiting_slenderness import (
    column_effective_length_eq140,
    compressed_limit_alpha,
    slenderness_check,
    table_30_effective_length_factor,
    table_32_compressed_limiting_slenderness,
)
from .fire_ui0 import ExecutionRegistry, FireUIError
from .local_stability import (
    flange_relative_slenderness,
    flange_slenderness_limit,
    wall_relative_slenderness,
    wall_slenderness_limit,
)
from .profile_catalog import InterimProfileCatalog
from .sp16_mech7_primary_workflow import (
    _axial_strength,
    _ev,
    _num,
    _util_ev,
)
from .sp16_mech7_v072_remediation import _geometry_inputs, _material_formula_inputs
from .sp16_mech7_v074_physical_remediation import _hydrate_source_backed_n1_prerequisites

BINDER_NODE_ID = _graph.BINDER_NODE_ID
STATE_NODE_ID = _graph.STATE_NODE_ID
GRAPH_SUFFIX = _graph.GRAPH_SUFFIX
LEGACY_N7_INTERACTIVE_NODES = _graph.LEGACY_N7_INTERACTIVE_NODES
build_model = _graph.build_model
replay_prefix_on_model = _graph.replay_prefix_on_model
transform_graph = _graph.transform_graph
transform_presentation_policy = _graph.transform_presentation_policy

_EPS = 1.0e-12


def _positive(values: Mapping[str, Any], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"SP16 v0.75 requires {key}")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise FireUIError(f"{key} must be a positive finite number")
    return result


def _profile_axis_state(values: Mapping[str, Any], catalog: InterimProfileCatalog) -> dict[str, Any]:
    """Resolve physical major/minor profile properties and expose only z/y semantics."""
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
    derived = bundle.get("derived_properties")
    table7 = bundle.get("sp16_table7")
    if not isinstance(raw, Mapping) or not isinstance(derived, Mapping) or not isinstance(table7, Mapping):
        raise FireUIError("selected profile lacks qualified inertia/radius/Table-7 properties")

    source_i_1 = float(raw["Ix_mm4"])
    source_i_2 = float(raw["Iy_mm4"])
    source_r_1 = float(derived["radius_x_mm"])
    source_r_2 = float(derived["radius_y_mm"])
    if min(source_i_1, source_i_2, source_r_1, source_r_2) <= 0.0:
        raise FireUIError("selected profile has invalid principal inertias or radii")

    # Ix/Iy are only frozen catalog-column names here.  They are not active
    # structural-axis names.  Physical major/minor inertia determines z/y.
    if source_i_1 >= source_i_2:
        return {
            "i_z": source_r_1,
            "i_y": source_r_2,
            "curve_z": str(table7["x"]["section_type"]),
            "curve_y": str(table7["y"]["section_type"]),
            "source_major_inertia_field": "Ix_mm4",
            "source_minor_inertia_field": "Iy_mm4",
        }
    return {
        "i_z": source_r_2,
        "i_y": source_r_1,
        "curve_z": str(table7["y"]["section_type"]),
        "curve_y": str(table7["x"]["section_type"]),
        "source_major_inertia_field": "Iy_mm4",
        "source_minor_inertia_field": "Ix_mm4",
    }


def _resolve_axis_effective_length(values: Mapping[str, Any], axis: str, length: float) -> tuple[float | None, float, dict[str, Any]]:
    route = values.get(f"sp16_effective_length_route_{axis}")
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
    """Calculate the canonical Stage-N7 z/y state without any x-axis alias."""
    hydrated = _hydrate_source_backed_n1_prerequisites(values)
    _material_formula_inputs(values, hydrated)
    _geometry_inputs(values, hydrated)

    length = _positive(hydrated, "sp16_member_length_mm")
    ry_design = _positive(hydrated, "Ry_formula")
    elastic = _positive(hydrated, "E_norm")
    profile = _profile_axis_state(hydrated, catalog)

    mu_z, leff_z, route_z = _resolve_axis_effective_length(hydrated, "z", length)
    mu_y, leff_y, route_y = _resolve_axis_effective_length(hydrated, "y", length)
    iz = float(profile["i_z"])
    iy = float(profile["i_y"])

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
            "schema": "sp16_v075_principal_axis_contract_v2",
            "principal_strong_axis": "z",
            "principal_weak_axis": "y",
            "legacy_principal_x_semantics_active": False,
            "principal_x_transport_alias_used": False,
            "relative_slenderness_strength_basis": "Ry_formula",
            "profile_axis_mapping": {
                "method": "physical_major_minor_inertia_to_canonical_z_y",
                "major_source_field": profile["source_major_inertia_field"],
                "minor_source_field": profile["source_minor_inertia_field"],
                "source_fields_are_catalog_columns_not_active_axes": True,
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


def _compression_stability_zy(values: Mapping[str, Any], n: float) -> dict[str, Any]:
    area = _num(values, "A_gross", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_compression", positive=True)
    phi_z = _num(values, "phi_z_sp16", positive=True)
    phi_y = _num(values, "phi_y_sp16", positive=True)
    uz = central_compression_stability_utilization(abs(n), area, ry, gc, phi_z)
    uy = central_compression_stability_utilization(abs(n), area, ry, gc, phi_y)
    return _util_ev(max(uz, uy), source="SP16-MECH7 Eq.(7) canonical z/y principal axes", scope=["SP16 7.1.3 Eq.(7)"])


def _slenderness_zy(values: Mapping[str, Any], n: float) -> dict[str, Any]:
    row = values.get("sp16_mech7_table32_row")
    group4 = values.get("sp16_mech7_group4_slenderness_increase")
    if not isinstance(row, str) or not isinstance(group4, bool):
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 10.4.1 Table 32"], reason="Table 32 classification is missing")
    lz = _num(values, "sp16_lambda_z_geom", positive=True)
    ly = _num(values, "sp16_lambda_y_geom", positive=True)
    phi_z = _num(values, "phi_z_sp16", positive=True)
    phi_y = _num(values, "phi_y_sp16", positive=True)
    area = _num(values, "A_gross", positive=True)
    ry = _num(values, "Ry_formula", positive=True)
    gc = _num(values, "gamma_c_compression", positive=True)
    alpha = compressed_limit_alpha(abs(n), min(phi_z, phi_y), area, ry, gc)
    limit = table_32_compressed_limiting_slenderness(row, alpha, group4)
    check = slenderness_check(max(lz, ly), limit)
    return _util_ev(float(check["utilization"]), source=f"SP16-MECH7 Table 32 row {row}, canonical z/y", scope=["SP16 10.4.1 Table 32"])


def _compression_local_stability_zy(values: Mapping[str, Any], check_id: str) -> dict[str, Any]:
    geom = values.get("section_geometry_2d_normalized")
    if not isinstance(geom, Mapping):
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3"], reason="normalized section geometry is missing")
    template = str(geom.get("template") or geom.get("shape") or "")
    if template not in {"i_section", "doubly_symmetric_i"}:
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3"], reason="central-compression local-stability binding is qualified here only for the I-section template")
    try:
        h = float(geom["h_mm"]); b = float(geom["b_mm"]); tw = float(geom["tw_mm"]); tf = float(geom["tf_mm"])
    except (KeyError, TypeError, ValueError):
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3"], reason="I-section h/b/tw/tf geometry is incomplete")
    if min(h, b, tw, tf) <= 0.0 or h <= 2.0 * tf or b <= tw:
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3"], reason="I-section geometry is invalid for local-stability plate checks")
    ry = _num(values, "Ry_formula", positive=True)
    elastic = _num(values, "E_norm", positive=True)
    member_lambda = max(_num(values, "lambda_bar_z", positive=True), _num(values, "lambda_bar_y", positive=True))
    if check_id == "local_stability_web":
        group = values.get("sp16_mech7_table9_group")
        if group != "group_1_i_section":
            return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3.2 Table 9"], reason="selected Table 9 diagram group is not the qualified I-section group")
        actual = wall_relative_slenderness(h - 2.0 * tf, tw, ry, elastic)
        limit = wall_slenderness_limit(str(group), member_lambda)
        return _util_ev(actual / limit, source="SP16-MECH7 Table 9 I-section web, canonical z/y", scope=["SP16 7.3.2 Table 9"])
    group = values.get("sp16_mech7_table10_group")
    edge = values.get("sp16_mech7_flange_edge_stiffened")
    if not isinstance(group, str) or not isinstance(edge, bool):
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3.8 Table 10"], reason="Table 10 diagram group/edge-stiffener classification is missing")
    actual = flange_relative_slenderness(0.5 * (b - tw), tf, ry, elastic)
    try:
        limit = flange_slenderness_limit(group, member_lambda, edge)
    except (TypeError, ValueError) as exc:
        return _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 7.3.8 Table 10"], reason=str(exc))
    return _util_ev(actual / limit, source="SP16-MECH7 Table 10 I-section flange, canonical z/y", scope=["SP16 7.3.8 Table 10"])


def _legacy_axis_deferred(scope: list[str], reason: str) -> dict[str, Any]:
    return _ev("DEFERRED", source="SP16-MECH7 v0.75 canonical-axis gate", scope=scope, reason=reason)


def bind_primary_ambient_evidence_zy(values: Mapping[str, Any]) -> dict[str, Any]:
    """Bind compression evidence directly to z/y; never reinterpret principal x as z."""
    census = values.get("sp16_applicability_census")
    if not isinstance(census, Mapping):
        raise FireUIError("SP16-MECH7 requires sp16_applicability_census")
    active_checks = census.get("active_checks")
    context_checks = census.get("context_driven_checks")
    if not isinstance(active_checks, list) or not isinstance(context_checks, list):
        raise FireUIError("SP16-MECH7 census check collections must be lists")
    active_ids = {str(r["id"]) for r in active_checks if isinstance(r, Mapping) and "id" in r}
    context_ids = {str(r["id"]) for r in context_checks if isinstance(r, Mapping) and "id" in r}
    n = _num(values, "ambient_N_force")
    mx = _num(values, "ambient_M_x") if "ambient_M_x" in values else 0.0
    my = _num(values, "ambient_M_y") if "ambient_M_y" in values else 0.0
    evidence: dict[str, dict[str, Any]] = {}

    if "section_tension" in active_ids or "section_compression" in active_ids:
        target = "section_tension" if n > 0.0 else "section_compression"
        try:
            evidence[target] = _axial_strength(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence[target] = _ev("DEFERRED", source="SP16-MECH7 z/y axial binding", scope=["SP16 7.1.1"], reason=str(exc))

    if "member_compression_stability" in active_ids:
        try:
            evidence["member_compression_stability"] = _compression_stability_zy(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["member_compression_stability"] = _ev("DEFERRED", source="SP16-MECH7 z/y compression stability", scope=["SP16 7.1.3"], reason=str(exc))

    if "effective_length_slenderness" in active_ids:
        try:
            evidence["effective_length_slenderness"] = _slenderness_zy(values, n)
        except (FireUIError, KeyError, TypeError, ValueError) as exc:
            evidence["effective_length_slenderness"] = _ev("DEFERRED", source="SP16-MECH7 z/y Table 32", scope=["SP16 10.4.1"], reason=str(exc))

    # These active checks still depend on the historical action/property x
    # vocabulary.  Do not silently identify that x with canonical z.
    for cid, scope in (
        ("bending_x", ["SP16 8.2.1 Eq.(43)"]),
        ("bending_y", ["SP16 8.2.1 Eq.(43)"]),
        ("biaxial_bending", ["SP16 8.2.1 Eq.(43)"]),
        ("bimoment_B", ["SP16 8.2.1 Eq.(43)"]),
        ("interaction_N_M", ["SP16 9.1", "SP16 9.2"]),
    ):
        if cid in active_ids:
            evidence[cid] = _legacy_axis_deferred(scope, "legacy Mx/Ix principal-axis route is disabled; v0.75 does not reinterpret x as z")
    if "interaction_M_Q" in active_ids:
        evidence["interaction_M_Q"] = _legacy_axis_deferred(["SP16 §8"], "qualified canonical M+Q interaction binding is not yet available")
    if "torsion_T" in active_ids:
        evidence["torsion_T"] = _legacy_axis_deferred(["SP16 torsion mechanics"], "T stress recovery exists but the complete fire/ambient resistance interaction route remains fail-closed")
    if "beam_ltb" in context_ids:
        evidence["beam_ltb"] = _legacy_axis_deferred(["SP16 8.4", "Annex Ж"], "legacy major-axis Mx LTB route is disabled until migrated to the canonical My/Mz action contract")

    for cid, qid in (("local_stability_web", "sp16_n6_web_status"), ("local_stability_flange", "sp16_n6_flange_status")):
        if cid not in context_ids:
            continue
        if qid in values:
            status = values[qid]
            if status == "pass" or status is True:
                evidence[cid] = _ev("PASS", source=qid, scope=["SP16 local stability"]); continue
            if status == "fail" or status is False:
                evidence[cid] = _ev("FAIL", source=qid, scope=["SP16 local stability"]); continue
            if status == "reduced_area_recheck_required":
                evidence[cid] = _ev("DEFERRED", source=qid, scope=["SP16 local stability"], reason="reduced-area recheck required"); continue
        if n < 0.0 and abs(mx) <= _EPS and abs(my) <= _EPS:
            evidence[cid] = _compression_local_stability_zy(values, cid)
        else:
            evidence[cid] = _legacy_axis_deferred(["SP16 local stability"], "bending/beam-column local stability awaits canonical My/Mz migration")

    if "fatigue" in context_ids:
        required = values.get("sp16_mech7_fatigue_required")
        if required is False:
            evidence["fatigue"] = _ev("N.A.", source="sp16_mech7_fatigue_required", scope=["SP16 §12"], reason="engineer classified fatigue as not applicable")
        elif required is True:
            release = values.get("sp16_n9_release_gate")
            evidence["fatigue"] = _ev("PASS" if release is True else "FAIL" if release is False else "DEFERRED", source="SP16 N9" if release is not None else "SP16-MECH7 z/y", scope=["SP16 §12"], reason=None if release is not None else "full N9 workflow evidence is required")
        else:
            evidence["fatigue"] = _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 §12"], reason="fatigue applicability is not classified")

    if "brittle_fracture" in context_ids:
        required = values.get("sp16_mech7_brittle_required")
        if required is False:
            evidence["brittle_fracture"] = _ev("N.A.", source="sp16_mech7_brittle_required", scope=["SP16 §13"], reason="engineer classified brittle fracture as not applicable")
        elif required is True:
            release = values.get("sp16_n10_release_gate")
            evidence["brittle_fracture"] = _ev("PASS" if release is True else "FAIL" if release is False else "DEFERRED", source="SP16 N10" if release is not None else "SP16-MECH7 z/y", scope=["SP16 §13"], reason=None if release is not None else "full N10 workflow evidence is required")
        else:
            evidence["brittle_fracture"] = _ev("DEFERRED", source="SP16-MECH7 z/y", scope=["SP16 §13"], reason="brittle-fracture applicability is not classified")

    resolved = sorted(k for k, v in evidence.items() if v["status"] in {"PASS", "FAIL", "N.A."})
    deferred = sorted(k for k, v in evidence.items() if v["status"] == "DEFERRED")
    bundle = {
        "schema": "sp16_mech7_primary_ambient_evidence_v075_zy_v1",
        "evidence": evidence,
        "resolved_check_ids": resolved,
        "deferred_check_ids": deferred,
        "all_bound_checks_resolved": not deferred,
        "policy": "canonical z/y principal-axis evidence; no x->z reinterpretation",
        "v075_axis_contract": {
            "principal_axes": ["z", "y"],
            "legacy_principal_x_semantics_active": False,
            "principal_x_transport_alias_used": False,
            "relative_slenderness_strength_basis": "Ry_formula",
        },
    }
    return {
        "sp16_mech7_primary_evidence": bundle,
        "sp16_mech7_primary_binding_complete": not deferred,
    }


def install_registry_remediation(registry: ExecutionRegistry, catalog: InterimProfileCatalog) -> ExecutionRegistry:
    """Install the canonical Stage-N7 state and binder without x transport aliases."""
    registry.register(STATE_NODE_ID, lambda values, node: effective_length_state(values, catalog))
    current = registry.executors.get(BINDER_NODE_ID)
    if current is None:
        raise FireUIError(f"v0.75 remediation requires registered {BINDER_NODE_ID}")
    if getattr(current, "_sp16_v075_zy_remediated", False):
        return registry

    def canonical(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        normalized = _hydrate_source_backed_n1_prerequisites(values)
        _material_formula_inputs(values, normalized)
        _geometry_inputs(values, normalized)
        result = bind_primary_ambient_evidence_zy(normalized)
        return result

    setattr(canonical, "_sp16_v072_remediated", True)
    setattr(canonical, "_sp16_v074_remediated", True)
    setattr(canonical, "_sp16_v075_remediated", True)
    setattr(canonical, "_sp16_v075_zy_remediated", True)
    registry.executors[BINDER_NODE_ID] = canonical
    return registry


__all__ = [
    "BINDER_NODE_ID",
    "GRAPH_SUFFIX",
    "LEGACY_N7_INTERACTIVE_NODES",
    "STATE_NODE_ID",
    "bind_primary_ambient_evidence_zy",
    "build_model",
    "effective_length_state",
    "install_registry_remediation",
    "replay_prefix_on_model",
    "transform_graph",
    "transform_presentation_policy",
]
