"""v0.76 runtime for the consolidated canonical z/y effective-length card."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .axial_members import central_compression_stability_coefficient, relative_slenderness
from .effective_lengths_and_limiting_slenderness import column_effective_length_eq140, table_30_effective_length_factor
from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech7_v072_remediation import _geometry_inputs, _material_formula_inputs
from .sp16_mech7_v074_physical_remediation import _hydrate_source_backed_n1_prerequisites
from .sp16_mech7_v075_zy_runtime import BINDER_NODE_ID, install_registry_remediation as install_v075_registry_remediation
from .sp16_mech7_v076_graph_overlay import DEFINITION_QID, STATE_NODE_ID

SCHEME_TO_CORE = {f"S{i}": f"scheme_{i}" for i in range(1, 9)}


def _positive_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{name} must be a positive finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise FireUIError(f"{name} must be a positive finite number")
    return result


def _definition(values: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = values.get(DEFINITION_QID)
    if not isinstance(raw, Mapping):
        raise FireUIError("v0.76 requires the consolidated z/y effective-length definition")
    for axis in ("z", "y"):
        if not isinstance(raw.get(axis), Mapping):
            raise FireUIError(f"effective-length definition requires axis {axis}")
    return raw


def _catalog_identity(values: Mapping[str, Any]) -> tuple[int, str, int | None]:
    """Recover the already-selected catalog identity; no synthetic profile_ref is required."""
    fid = values.get("section_catalog_family_id")
    designation = values.get("section_designation")
    row = values.get("section_catalog_source_row_id")

    geom = values.get("section_geometry_2d_normalized")
    if isinstance(geom, Mapping) and str(geom.get("source") or "") == "profile_catalog":
        if fid is None:
            fid = geom.get("family_id")
        if designation is None:
            designation = geom.get("designation")
        if row is None:
            row = geom.get("source_row_id")

    try:
        family_id = int(fid)
    except (TypeError, ValueError) as exc:
        raise FireUIError(
            "v0.76 cannot identify the selected catalog family. Re-select the catalog profile; "
            "profile_ref is not required and is no longer part of the active contract."
        ) from exc
    if not isinstance(designation, str) or not designation.strip():
        raise FireUIError("v0.76 cannot identify the selected catalog designation")
    try:
        source_row_id = int(row) if row is not None else None
    except (TypeError, ValueError) as exc:
        raise FireUIError("v0.76 catalog source_row_id is invalid") from exc
    return family_id, designation.strip(), source_row_id


def _profile_axis_state(values: Mapping[str, Any], catalog: InterimProfileCatalog) -> dict[str, Any]:
    """Resolve canonical strong/weak properties from the selected catalog row.

    The catalog's historical property-column names are never exposed as active
    axes.  The canonical mapping is determined only by major/minor inertia
    magnitude: major -> z, minor -> y.
    """
    family_id, designation, source_row_id = _catalog_identity(values)
    try:
        bundle = catalog.resolve(family_id, designation, source_row_id=source_row_id)
    except (KeyError, TypeError, ValueError) as exc:
        raise FireUIError("cannot resolve the selected catalog profile for the z/y stability state") from exc

    raw = bundle.get("catalog_properties_interim")
    table7 = bundle.get("sp16_table7")
    if not isinstance(raw, Mapping) or not isinstance(table7, Mapping):
        raise FireUIError("selected catalog profile lacks qualified inertia/Table-7 data")

    area = _positive_number(raw.get("A_mm2"), "catalog A")
    inertia_1 = _positive_number(raw.get("Ix_mm4"), "catalog principal inertia 1")
    inertia_2 = _positive_number(raw.get("Iy_mm4"), "catalog principal inertia 2")

    # Verify that the catalog identity still describes the section state carried
    # by the guided ledger.  This catches stale/mixed profile selections instead
    # of silently using a different row.
    if "A_gross" in values:
        current_area = _positive_number(values.get("A_gross"), "A_gross")
        if not math.isclose(current_area, area, rel_tol=1e-9, abs_tol=1e-9):
            raise FireUIError("selected catalog identity does not match the materialized section area")
    current_inertias: list[float] = []
    for qid in ("J_x", "J_y"):
        if qid in values and isinstance(values.get(qid), (int, float)) and not isinstance(values.get(qid), bool):
            current_inertias.append(_positive_number(values.get(qid), qid))
    if len(current_inertias) == 2:
        if any(
            not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)
            for a, b in zip(sorted(current_inertias), sorted((inertia_1, inertia_2)))
        ):
            raise FireUIError("selected catalog identity does not match the materialized section inertias")

    if inertia_1 >= inertia_2:
        major_inertia, minor_inertia = inertia_1, inertia_2
        major_curve = str(table7["x"]["section_type"])
        minor_curve = str(table7["y"]["section_type"])
    else:
        major_inertia, minor_inertia = inertia_2, inertia_1
        major_curve = str(table7["y"]["section_type"])
        minor_curve = str(table7["x"]["section_type"])

    return {
        "i_z": math.sqrt(major_inertia / area),
        "i_y": math.sqrt(minor_inertia / area),
        "curve_z": major_curve,
        "curve_y": minor_curve,
        "catalog_identity": {
            "family_id": family_id,
            "designation": designation,
            "source_row_id": source_row_id,
        },
        "mapping_method": "major_inertia_to_z__minor_inertia_to_y",
    }


def _axis_effective_length(definition: Mapping[str, Any], axis: str) -> tuple[float | None, float, dict[str, Any]]:
    axis_def = definition.get(axis)
    if not isinstance(axis_def, Mapping):
        raise FireUIError(f"effective-length definition requires axis {axis}")
    method = axis_def.get("method")
    if method == "table30":
        scheme = axis_def.get("scheme_id")
        if scheme not in SCHEME_TO_CORE:
            raise FireUIError(f"Table 30 scheme for axis {axis} must be one of {sorted(SCHEME_TO_CORE)}")
        length = _positive_number(definition.get("member_length_mm"), "geometric member length L")
        core_scheme = SCHEME_TO_CORE[str(scheme)]
        mu = float(table_30_effective_length_factor(core_scheme))
        leff = float(column_effective_length_eq140(length, mu))
        return mu, leff, {
            "method": "table30",
            "scheme_id": str(scheme),
            "mu": mu,
            "member_length_mm": length,
            "normative_scope": "SP16 10.3.3 Table 30 + Eq.(140)",
        }
    if method == "verified_analysis":
        leff = _positive_number(axis_def.get("effective_length_mm"), f"l_eff,{axis}")
        basis = axis_def.get("basis")
        if not isinstance(basis, str) or not basis.strip():
            raise FireUIError(f"direct l_eff,{axis} requires a non-empty calculation/normative basis")
        return None, leff, {
            "method": "verified_analysis",
            "effective_length_mm": leff,
            "basis": basis.strip(),
            "normative_scope": "explicit source-traced SP16 Section 10 route",
        }
    raise FireUIError(f"unsupported effective-length method for axis {axis}: {method!r}")


def effective_length_state(values: Mapping[str, Any], catalog: InterimProfileCatalog) -> dict[str, Any]:
    """Build l_eff, slenderness and phi from one v0.76 z/y definition."""
    hydrated = _hydrate_source_backed_n1_prerequisites(values)
    _material_formula_inputs(values, hydrated)
    _geometry_inputs(values, hydrated)

    definition = _definition(hydrated)
    ry_design = _positive_number(hydrated.get("Ry_formula"), "Ry_formula")
    elastic = _positive_number(hydrated.get("E_norm"), "E_norm")
    profile = _profile_axis_state(hydrated, catalog)

    mu_z, leff_z, route_z = _axis_effective_length(definition, "z")
    mu_y, leff_y, route_y = _axis_effective_length(definition, "y")
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

    contract = {
        "schema": "sp16_v076_effective_length_zy_v1",
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
        "effective_length_z": route_z,
        "effective_length_y": route_y,
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
        # The quantity ID is retained for downstream compatibility, but its
        # payload explicitly identifies the active v0.76 contract.
        "sp16_v075_axis_contract": contract,
    }
    if mu_z is not None:
        result["sp16_mu_z"] = mu_z
    if mu_y is not None:
        result["sp16_mu_y"] = mu_y
    return result


def install_registry_remediation(registry: ExecutionRegistry, catalog: InterimProfileCatalog) -> ExecutionRegistry:
    """Keep the v0.75 canonical binder and replace only the Stage-N7 state producer."""
    install_v075_registry_remediation(registry, catalog)
    executor = lambda values, node: effective_length_state(values, catalog)
    setattr(executor, "_sp16_v076_effective_length_remediated", True)
    registry.register(STATE_NODE_ID, executor)
    return registry


__all__ = [
    "BINDER_NODE_ID", "SCHEME_TO_CORE", "STATE_NODE_ID",
    "effective_length_state", "install_registry_remediation",
]
