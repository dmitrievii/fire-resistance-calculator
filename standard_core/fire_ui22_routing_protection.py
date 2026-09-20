"""FIRE-UI2.2 routing continuity and fire-protection material authoring.

This layer does not introduce new SP16/SP554 resistance equations. It restores
missing guided navigation and materializes the SP554 12.5 thermal-property
object from either the source-traced STO ARSS table or explicit engineer input.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui21_ui_hardening import build_fire_ui21_registry
from .profile_catalog import InterimProfileCatalog
from .fire_sp554_thermal import _validate_matrix_dataset, _matrix_direct, _matrix_inverse
from .fire_sp554_assessment import _format_minutes_exact, _requirement_provenance


def _num(values: Mapping[str, Any], qid: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    value = values.get(qid)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FireUIError(f"{qid} must be a finite number")
    x = float(value)
    if positive and x <= 0.0:
        raise FireUIError(f"{qid} must be > 0")
    if nonnegative and x < 0.0:
        raise FireUIError(f"{qid} must be >= 0")
    return x


def _build_protection_model_parameters(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Build the canonical 12.5 material-property object without raw JSON authoring."""
    source = str(values.get("protection_12_5_material_source") or "")
    if source not in {"sto_arss_library", "manual_properties"}:
        raise FireUIError("protection_12_5_material_source is unresolved")
    rho = _num(values, "protection_material_density_kg_m3", positive=True)
    moisture = _num(values, "protection_material_moisture_percent", nonnegative=True)
    emissivity = _num(values, "protection_material_emissivity", positive=True)
    if emissivity > 1.0:
        raise FireUIError("protection_material_emissivity must be <= 1")
    A = _num(values, "protection_material_lambda_A")
    B = _num(values, "protection_material_lambda_B")
    C = _num(values, "protection_material_cp_C", positive=True)
    D = _num(values, "protection_material_cp_D")
    basis = str(values.get("protection_material_temperature_basis") or "")
    if basis not in {"K", "degC"}:
        raise FireUIError("protection_material_temperature_basis must be K or degC")

    material_id = values.get("protection_arss_material_id") if source == "sto_arss_library" else None
    provenance: dict[str, Any] = {
        "source_kind": source,
        "material_id": material_id,
        "temperature_basis": basis,
    }
    if source == "sto_arss_library":
        provenance.update({
            "standard_id": "STO_ARSS_11251254_001_018_03",
            "table": "Теплофизические характеристики огнезащитных материалов",
            "valid_temperature_min_k": 273.0,
            "coefficients_retained_in_source_kelvin_form": True,
        })
        if material_id == "mineral_wool_board":
            provenance.update({
                "source_density_range_kg_m3": [80.0, 100.0],
                "active_project_density_kg_m3": 100.0,
                "density_selection_basis": "user-fixed upper value for FIRE-UI2.2",
            })

    model = {
        "density_kg_m3": rho,
        "conductivity_A_w_mk": A,
        "conductivity_B_w_mk2": B,
        "heat_capacity_C_j_kgk": C,
        "heat_capacity_D_j_kgk2": D,
        "initial_moisture_percent": moisture,
        "surface_emissivity": emissivity,
        "temperature_basis": basis,
        "source_provenance": provenance,
    }
    if source == "sto_arss_library":
        model["valid_temperature_min_k"] = 273.0
    return {
        "protection_12_5_model_parameters": model,
        "protection_material_provenance": provenance,
    }



def _required_tests_12_4(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = values.get("protection_12_4_thickness_variant_count")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or int(raw) != float(raw) or int(raw) < 1:
        raise FireUIError("protection_12_4_thickness_variant_count must be a positive integer")
    n = int(raw)
    required = 3 if n == 1 else 6 if n == 2 else 9
    return {"protection_12_4_required_test_count": required}


def _blocked_12_4_dataset_builder(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    raise FireUIError(
        "SP554 12.4 raw fire-test-series to performance-matrix generation is not yet promoted to the production runtime; "
        "use a source-traced documented 12.7-12.9 matrix/nomogram route. No test data are interpolated or fabricated."
    )


def _blocked_12_5_dataset_builder(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    raise FireUIError(
        "SP554 12.5 automatic performance-matrix generation is not yet production-qualified. "
        "The material-property library/manual A-B-C-D model is available, but it does not replace the mandatory 12.6 validation evidence. "
        "Supply a source-traced validated performance dataset; no matrix is synthesized here."
    )


def _normalize_performance_dataset(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = values.get("protection_performance_dataset_raw")
    if not isinstance(raw, Mapping):
        raise FireUIError("protection_performance_dataset_raw must be an object")
    out = dict(raw)
    source_kind = str(values.get("protection_performance_source_kind") or out.get("source_kind") or "")
    steel_group = str(values.get("steel_strength_group") or out.get("steel_group") or "")
    product_id = str(values.get("protection_product_id") or out.get("product_id") or "")
    fire_regime = str(values.get("fire_temperature_regime") or out.get("fire_regime") or "")
    if source_kind:
        out["source_kind"] = source_kind
    if steel_group:
        out["steel_group"] = steel_group
    if product_id:
        out["product_id"] = product_id
    if fire_regime:
        out["fire_regime"] = fire_regime
    # A normalized dataset must retain its source matrix literally; do not
    # smooth, extrapolate or invent missing axes/values at this stage.
    return {"protection_performance_dataset_normalized": out}


def _validate_performance_dataset(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    dataset = values.get("protection_performance_dataset_normalized")
    if not isinstance(dataset, Mapping):
        return {"protection_performance_format_valid": False, "protection_performance_dataset_ready": False}
    try:
        target = dataset.get("critical_temperature_c")
        if isinstance(target, bool) or not isinstance(target, (int, float)):
            raise ValueError("critical_temperature_c is required in the documented performance dataset")
        _validate_matrix_dataset(dataset, float(target))
    except (ValueError, TypeError, KeyError):
        return {"protection_performance_format_valid": False, "protection_performance_dataset_ready": False}
    return {"protection_performance_format_valid": True, "protection_performance_dataset_ready": True}


def _validated_matrix(values: Mapping[str, Any]) -> dict[str, Any]:
    dataset = values.get("protection_performance_dataset_normalized")
    if not isinstance(dataset, Mapping):
        raise FireUIError("protection_performance_dataset_normalized must be an object")
    target = _num(values, "critical_temperature_c")
    try:
        return _validate_matrix_dataset(dataset, target)
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc


def _direct_domain_12_10(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        dataset = _validated_matrix(values)
        delta = _num(values, "delta_pr_protected", positive=True)
        thickness = _num(values, "protection_candidate_thickness_mm", positive=True)
        _matrix_direct({"protection_thickness_mm": thickness}, dataset, delta)
        ok = True
    except (FireUIError, ValueError, TypeError, KeyError):
        ok = False
    return {"sp554_12_10_query_domain_ok": ok}


def _inverse_domain_12_10(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        dataset = _validated_matrix(values)
        delta = _num(values, "delta_pr_protected", positive=True)
        required = _num(values, "required_fire_resistance_min", positive=True)
        result = _matrix_inverse({"required_fire_resistance_min": required}, dataset, delta)
        ok = result.get("status") == "COMPLETE" and result.get("minimum_protection_thickness_mm") is not None
    except (FireUIError, ValueError, TypeError, KeyError):
        ok = False
    return {"sp554_12_10_inverse_query_domain_ok": bool(ok)}


def _minimum_thickness_12_10(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    dataset = _validated_matrix(values)
    delta = _num(values, "delta_pr_protected", positive=True)
    required = _num(values, "required_fire_resistance_min", positive=True)
    try:
        result = _matrix_inverse({"required_fire_resistance_min": required}, dataset, delta)
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    if result.get("status") != "COMPLETE" or result.get("minimum_protection_thickness_mm") is None:
        raise FireUIError(result.get("diagnostic") or "required fire resistance is outside the documented 12.10 domain")
    return {"protection_thickness_mm": float(result["minimum_protection_thickness_mm"])}


def _protected_time_12_10(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    dataset = _validated_matrix(values)
    delta = _num(values, "delta_pr_protected", positive=True)
    thickness = _num(values, "protection_thickness_mm", positive=True)
    try:
        result = _matrix_direct({"protection_thickness_mm": thickness}, dataset, delta)
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    return {"protected_fire_resistance_min": float(result["actual_fire_resistance_min"])}


def _annex_a_metadata_packet(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    keys = (
        "annex_a_row_number", "annex_a_structure_name_code", "annex_a_element_mark",
        "annex_a_steel_mass_t", "annex_a_quantity_m", "annex_a_heated_sides_count",
        "annex_a_protection_area_m2",
    )
    return {"annex_a_reporting_metadata": {k: values[k] for k in keys}}


def _format_r_designation(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    if "protected_fire_resistance_min" in values and any(p["quantity_id"] == "protected_fire_resistance_designation" for p in node["produces"]):
        t = _num(values, "protected_fire_resistance_min", nonnegative=True)
        designation = f"R {_format_minutes_exact(t)}"
        return {"protected_fire_resistance_designation": designation, "fire_resistance_designation": designation}
    t = _num(values, "unprotected_fire_resistance_min", nonnegative=True)
    designation = f"R {_format_minutes_exact(t)}"
    return {"unprotected_fire_resistance_designation": designation, "fire_resistance_designation": designation}


def _annex_a_schedule(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    # Reporting-only producer: copy canonical calculation results; never
    # recalculate thermal/mechanical quantities here.
    schedule = {
        "schema": "sp554_annex_a_schedule_fragment_v2",
        "metadata": values.get("annex_a_reporting_metadata"),
        "section_designation": values.get("section_designation"),
        "section_standard": values.get("section_catalog_standard"),
        "section_geometry": values.get("section_geometry_2d_normalized"),
        "heated_perimeter_m": values.get("P_heated_protected"),
        "reduced_thickness_mm": values.get("delta_pr_protected"),
        "critical_temperature_c": values.get("critical_temperature_c"),
        "actual_fire_resistance_min": values.get("protected_fire_resistance_min"),
        "required_fire_resistance_min": values.get("required_fire_resistance_min"),
        "protection_product_id": values.get("protection_product_id"),
        "protection_thickness_mm": values.get("protection_thickness_mm"),
        "fire_resistance_designation": values.get("protected_fire_resistance_designation"),
    }
    return {"fire_protection_schedule": schedule}


def _validate_required_r_provenance(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    required = _num(values, "required_fire_resistance_min", positive=True)
    provenance = values.get("fire_d4_required_r_provenance")
    try:
        _requirement_provenance(provenance, required)  # type: ignore[arg-type]
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    return {"fire_d4_required_r_provenance_valid": True}

def build_fire_ui22_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI2.2 executor registry over the verified FIRE-UI2.1 runtime.

    Standard reference:
        SP554 Section 12.5 material-property authoring; STO ARSS 11251254.001-018-03 thermal-property table as a source-traced secondary dataset.

    Parameters:
        catalog: Frozen interim section-profile catalog inherited by earlier FIRE-UI registry layers.
        registry: Optional registry to extend in place.

    Returns:
        ExecutionRegistry with the inherited FIRE-UI2.1 executors plus the FIRE-UI2.2 protection-material model builder.

    Assumptions:
        The active package uses DAG v0.3.58 and preserves the printed temperature basis of source material coefficients.

    Sign convention:
        Unchanged from FIRE-UI2.1; signed mechanical actions remain algebraic quantities.

    Unit convention:
        Material density uses kg/m3, moisture percent, emissivity dimensionless, conductivity W/(m*K), and heat capacity J/(kg*K).

    Applicability:
        FIRE-UI2.2 guided SP16-to-SP554 workflow, including SP554 12.5 fire-protection material authoring.

    Limitations:
        The material library does not fabricate SP554 12.6 validation evidence. General Qy and torsion-T mechanics remain fail-closed.

    Raises:
        Propagates errors raised by inherited registry builders; material-model execution raises FireUIError for invalid property domains.

    Examples:
        ``registry = build_fire_ui22_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_fire_ui22_routing_protection_library.py`` plus cumulative FIRE-UI regression suites.

    Implementation notes:
        The wrapper extends FIRE-UI2.1 only with the internal material-object builder; routing changes remain declarative in DAG v0.3.58.
    """
    reg = build_fire_ui21_registry(catalog, registry)
    reg.register("SP554_C_12_5_BUILD_MODEL_PARAMETERS", _build_protection_model_parameters)
    reg.register("SP554_C_12_4_REQUIRED_TEST_COUNT", _required_tests_12_4)
    reg.register("SP554_C_12_4_BUILD_PERFORMANCE_DATASET", _blocked_12_4_dataset_builder)
    reg.register("SP554_C_12_5_1D_PERFORMANCE_DATASET", _blocked_12_5_dataset_builder)
    reg.register("SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET", _normalize_performance_dataset)
    reg.register("SP554_C_12_7_9_FORMAT_VALID", _validate_performance_dataset)
    reg.register("SP554_C_12_10_DOMAIN", _direct_domain_12_10)
    reg.register("SP554_C_12_10_DOMAIN_INVERSE", _inverse_domain_12_10)
    reg.register("SP554_C_12_10_MINIMUM_THICKNESS", _minimum_thickness_12_10)
    reg.register("SP554_C_12_10_PROTECTED_TIME", _protected_time_12_10)
    reg.register("SP554_C_ANNEX_A_METADATA_PACKET", _annex_a_metadata_packet)
    reg.register("SP554_C_R_DESIGNATION_UNPROTECTED", _format_r_designation)
    reg.register("SP554_C_R_DESIGNATION_PROTECTED", _format_r_designation)
    reg.register("SP554_C_ANNEX_A_SCHEDULE", _annex_a_schedule)
    reg.register("SP554_FIRE_D4_C_REQUIRED_R_PROVENANCE_GUARD", _validate_required_r_provenance)
    return reg
