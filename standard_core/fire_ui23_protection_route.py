"""FIRE-UI2.3 fire-protection route closure.

Closes the guided split between source-traced STO ARSS thermal properties,
manual validated thermal properties, and a concrete product's documented
12.7-12.10 performance matrix.  Raw internal objects are no longer required
from the engineer on the STO ARSS/manual 12.5 route.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui22_routing_protection import (
    build_fire_ui22_registry,
    _build_protection_model_parameters,
    _normalize_performance_dataset,
    _validate_performance_dataset,
    _direct_domain_12_10,
    _inverse_domain_12_10,
    _minimum_thickness_12_10,
    _protected_time_12_10,
)
from .fire_sp554_thermal import sp554_fire_thermal_guided_workflow
from .profile_catalog import InterimProfileCatalog


def _finite(values: Mapping[str, Any], qid: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    raw = values.get(qid)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
        raise FireUIError(f"{qid} must be a finite number")
    value = float(raw)
    if positive and value <= 0.0:
        raise FireUIError(f"{qid} must be > 0")
    if nonnegative and value < 0.0:
        raise FireUIError(f"{qid} must be >= 0")
    return value


def _source_is_fdm(values: Mapping[str, Any]) -> bool:
    return str(values.get("protection_source_mode") or "") in {"sto_arss_library", "manual_properties"}


def _build_model_v23(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    mode = str(values.get("protection_source_mode") or "")
    if mode not in {"sto_arss_library", "manual_properties"}:
        raise FireUIError("protection_source_mode must select STO ARSS or manual properties for the 12.5 model")
    legacy_source = "sto_arss_library" if mode == "sto_arss_library" else "manual_properties"
    payload = dict(values)
    payload["protection_12_5_material_source"] = legacy_source
    out = dict(_build_protection_model_parameters(payload, node))
    model = dict(out["protection_12_5_model_parameters"])
    # SP554 12.5 moisture execution is accepted only inside an explicit 12.6
    # validation envelope.  Do not apply a second per-step latent-heat decrement.
    model["moisture_accounting_mode"] = "external_validation_envelope"
    model["external_validation_envelope_confirmed"] = True
    out["protection_12_5_model_parameters"] = model
    return out


def _arss_validation_basis(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    if str(values.get("protection_source_mode") or "") != "sto_arss_library":
        raise FireUIError("STO ARSS validation basis is applicable only to the STO ARSS library route")
    material = str(values.get("protection_arss_material_id") or "")
    if not material:
        raise FireUIError("protection_arss_material_id is unresolved")
    # STO ARSS 8.1.3.2.2 states that temperature-dependent coefficients are
    # fitted against tested constructions until the temperature discrepancy at
    # every interval is <=20 %.  Preserve the documentary criterion without
    # inventing an unpublished synthetic maximum deviation value.
    basis = (
        "STO ARSS 11251254.001-018-03, 8.1.3.2.2: coefficients calibrated on tested constructions "
        "until temperature discrepancy at every time interval is not more than 20%; "
        f"library material={material}"
    )
    return {
        "protection_12_6_validation_evidence_complete": True,
        "validation_within_20_percent_all_cases": True,
        "protection_12_6_validation_basis": basis,
    }


def _validation_bundle(values: Mapping[str, Any]) -> dict[str, Any]:
    complete = values.get("protection_12_6_validation_evidence_complete")
    within = values.get("validation_within_20_percent_all_cases")
    if complete is not True or within is not True:
        raise FireUIError("SP554 12.6 validation must be complete and within 20% before the 12.5 result may be used")
    max_dev = _finite(values, "protection_12_6_max_deviation_pct", nonnegative=True)
    return {
        "validation_evidence_preconfirmed": True,
        "validation_evidence_complete": True,
        "validation_within_20_percent_all_cases": True,
        "validation_max_deviation_pct": max_dev,
        "validation_evidence_basis": (
            "Engineer-supplied SP554 12.6 validation evidence; thermal properties may originate from STO ARSS "
            "or from a manually authored certified property set"
        ),
    }


def _fdm_case(values: Mapping[str, Any], thickness_mm: float) -> dict[str, Any]:
    if not _source_is_fdm(values):
        raise FireUIError("12.5 FDM is applicable only to STO ARSS/manual thermal-property routes")
    if str(values.get("fire_temperature_regime") or "") != "standard":
        raise FireUIError("FIRE-UI2.3 12.5 protected FDM is scoped to the standard fire regime")
    model = values.get("protection_12_5_model_parameters")
    if not isinstance(model, Mapping):
        raise FireUIError("protection_12_5_model_parameters is unresolved")
    # A small fixed control-volume count with a conservative explicit time step
    # gave stable convergence in the package verification controls.  This is a
    # numerical discretization choice, not a normative material property.
    layer_count = 3
    protection_model = dict(model)
    protection_model.update({"thickness_mm": float(thickness_mm), "layer_count": layer_count})
    case = {
        "thermal_route": "PROTECTED_FDM_12_5",
        "critical_temperature_c": _finite(values, "critical_temperature_c"),
        "reduced_thickness_mm": _finite(values, "delta_pr_protected", positive=True),
        "protection_model": protection_model,
        "steel_properties_source": "sp554_12_2_defaults",
        "initial_temperature_c": 20.0,
        "time_step_min": 0.005,
        "max_time_min": 300.0,
        **_validation_bundle(values),
    }
    return case


def _direct_fdm_12_5(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    thickness = _finite(values, "protection_candidate_thickness_mm", positive=True)
    try:
        result = sp554_fire_thermal_guided_workflow(_fdm_case(values, thickness))
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    if result.get("status") != "COMPLETE" or result.get("actual_fire_resistance_min") is None:
        raise FireUIError(result.get("diagnostic") or "SP554 12.5 protected FDM did not produce a valid result")
    return {
        "protection_thickness_mm": thickness,
        "protected_fire_resistance_min": float(result["actual_fire_resistance_min"]),
        "protection_12_5_calculation_trace": result,
    }


def _inverse_fdm_12_5(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    required = _finite(values, "required_fire_resistance_min", positive=True)
    lo = _finite(values, "protection_search_min_thickness_mm", positive=True)
    hi = _finite(values, "protection_search_max_thickness_mm", positive=True)
    if hi <= lo:
        raise FireUIError("protection_search_max_thickness_mm must be greater than protection_search_min_thickness_mm")

    cache: dict[float, tuple[float, Mapping[str, Any]]] = {}
    def evaluate(thickness: float) -> tuple[float, Mapping[str, Any]]:
        key = round(float(thickness), 9)
        if key not in cache:
            try:
                res = sp554_fire_thermal_guided_workflow(_fdm_case(values, key))
            except (ValueError, TypeError, KeyError) as exc:
                raise FireUIError(str(exc)) from exc
            if res.get("status") != "COMPLETE" or res.get("actual_fire_resistance_min") is None:
                raise FireUIError(res.get("diagnostic") or f"12.5 FDM failed at thickness {key:g} mm")
            cache[key] = (float(res["actual_fire_resistance_min"]), res)
        return cache[key]

    r_lo, _ = evaluate(lo)
    r_hi, _ = evaluate(hi)
    if r_lo >= required - 1e-9:
        selected = lo
    elif r_hi < required - 1e-9:
        raise FireUIError(
            "Required fire resistance is not reached within the engineer-specified thickness-search domain; "
            "extrapolation beyond the upper bound is forbidden"
        )
    else:
        # Fire resistance must be verified, not assumed monotonic globally.  In
        # the bounded bisection interval used here, sample the interval first and
        # require non-decreasing values before solving the first crossing.
        sample_n = 9
        xs = [lo + (hi - lo) * i / (sample_n - 1) for i in range(sample_n)]
        ys = [evaluate(x)[0] for x in xs]
        if any(b < a - 0.05 for a, b in zip(ys, ys[1:])):
            raise FireUIError(
                "12.5 FDM fire-resistance response is non-monotonic inside the requested thickness domain; "
                "automatic minimum-thickness search is fail-closed"
            )
        bracket_lo, bracket_hi = lo, hi
        # Tight enough for construction thickness reporting while avoiding false
        # precision from the finite-difference discretization.
        for _ in range(24):
            mid = 0.5 * (bracket_lo + bracket_hi)
            r_mid, _ = evaluate(mid)
            if r_mid >= required:
                bracket_hi = mid
            else:
                bracket_lo = mid
        selected = bracket_hi

    actual, trace = evaluate(selected)
    return {
        "protection_thickness_mm": float(selected),
        "protected_fire_resistance_min": float(actual),
        "protection_12_5_calculation_trace": {
            "mode": "inverse_minimum_thickness",
            "required_fire_resistance_min": required,
            "search_bounds_mm": [lo, hi],
            "evaluations": len(cache),
            "selected_result": trace,
            "no_extrapolation": True,
        },
    }


def build_fire_ui23_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI2.3 executor registry for the revised fire-protection routes.

    Standard reference:
        Standard: СП 554.1311500.2026 and STO ARSS 11251254.001-018-03
        Version: SP554 enacted baseline used by the package; STO ARSS source-traced protection-property library
        Clause: SP554 Sections 5, 12.5-12.10
        Annex: None
        Equation/Table: SP554 12.5-12.10 protected-member thermal routes
        Audit ID: FIRE-UI23-REGISTRY
        Normative status: implementation_binding

    Parameters:
        catalog:
            Type: InterimProfileCatalog
            Unit: not applicable
            Meaning: Profile catalog used by the cumulative guided-calculation registry.
            Valid range: Initialized catalog instance.
            Source: package profile catalog
        registry:
            Type: ExecutionRegistry | None
            Unit: not applicable
            Meaning: Optional existing registry to extend in place.
            Valid range: None or a valid registry instance.
            Source: application composition

    Returns:
        Type: ExecutionRegistry
        Unit: not applicable
        Meaning: Registry with FIRE-UI2.3 fire-protection executors registered.

    Assumptions:
        - STO ARSS and manual-property routes use explicit SP554 12.6 validation gates.
        - Product-specific matrix routes retain their own source-traced dataset provenance.

    Sign convention:
        - Thermal quantities are scalar; mechanical sign conventions are inherited from upstream FIRE-UI routes.

    Unit convention:
        - Protection thickness is mm, temperature is degC internally, and time is min.
        - STO ARSS temperature-dependent coefficients preserve their source Kelvin basis during conversion.

    Applicability:
        - Guided fire-protection calculations using SP554 protected-member routes.

    Limitations:
        - Qy and general torsion T remain outside the implemented mechanical runtime.
        - Product-specific performance matrices must remain inside their documented interpolation domain.

    Raises:
        TypeError: The supplied catalog or registry is incompatible with the cumulative application setup.
        FireUIError: A registered executor is later called with unresolved or invalid branch inputs.

    Examples:
        >>> reg = build_fire_ui23_registry(InterimProfileCatalog())
        >>> isinstance(reg, ExecutionRegistry)
        True

    Tests:
        Unit tests:
            - tests/test_fire_ui23_protection_route_closure.py
            - tests/test_docstrings.py::test_public_api_docstrings
        Validation cases:
            - FIRE-UI2.3 guided STO ARSS, manual-property, and documented-product matrix routes

    Implementation notes:
        - The function overrides only FIRE-UI2.3 executors and preserves the cumulative parent registry.
        - Raw protection-performance objects are not required from engineers on STO ARSS or manual-property routes.
    """
    reg = build_fire_ui22_registry(catalog, registry)
    # Override the v0.55 material builder and add direct 12.5 result executors.
    reg.register("SP554_C_12_5_BUILD_MODEL_PARAMETERS", _build_model_v23)
    reg.register("SP554_C_12_5_DIRECT_PROTECTED_TIME", _direct_fdm_12_5)
    reg.register("SP554_C_12_5_MINIMUM_THICKNESS_SEARCH", _inverse_fdm_12_5)
    # Retain documented-product matrix runtime from FIRE-UI2.2.
    reg.register("SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET", _normalize_performance_dataset)
    reg.register("SP554_C_12_7_9_FORMAT_VALID", _validate_performance_dataset)
    reg.register("SP554_C_12_10_DOMAIN", _direct_domain_12_10)
    reg.register("SP554_C_12_10_DOMAIN_INVERSE", _inverse_domain_12_10)
    reg.register("SP554_C_12_10_MINIMUM_THICKNESS", _minimum_thickness_12_10)
    reg.register("SP554_C_12_10_PROTECTED_TIME", _protected_time_12_10)
    return reg
