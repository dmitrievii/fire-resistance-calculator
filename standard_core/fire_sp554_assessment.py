"""FIRE-D4 SP554 Section 13 result-assessment runtime.

The module consumes a valid FIRE-D3 thermal result and an explicit externally
sourced required fire-resistance time.  It deliberately does not derive the
required value from building classification rules; that handoff belongs to the
external fire-safety standard/project requirement producer.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .fire_sp554_thermal import sp554_fire_thermal_guided_workflow


def _finite_number(value: Any, name: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    x = float(value)
    if positive and x <= 0.0:
        raise ValueError(f"{name} must be > 0")
    if nonnegative and x < 0.0:
        raise ValueError(f"{name} must be >= 0")
    return x


def _nonempty_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _format_minutes_exact(value: float) -> str:
    """Format a calculated time without class rounding or hidden flooring."""
    return format(float(value), ".12g")


def _requirement_provenance(provenance: Mapping[str, Any], required_min: float) -> dict[str, Any]:
    if not isinstance(provenance, Mapping):
        raise ValueError("requirement_provenance must be an object")
    source_kind = _nonempty_text(provenance.get("source_kind"), "requirement_provenance.source_kind")
    if source_kind not in {"external_normative_requirement", "project_requirement_with_normative_source"}:
        raise ValueError("requirement_provenance.source_kind must identify an external normative/project requirement")
    source_document = _nonempty_text(provenance.get("source_document"), "requirement_provenance.source_document")
    source_reference = _nonempty_text(provenance.get("source_reference"), "requirement_provenance.source_reference")
    value_min = _finite_number(provenance.get("value_min"), "requirement_provenance.value_min", positive=True)
    if not math.isclose(value_min, required_min, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("requirement_provenance.value_min must exactly match required_fire_resistance_min")
    result = {
        "source_kind": source_kind,
        "source_document": source_document,
        "source_reference": source_reference,
        "value_min": value_min,
    }
    if "source_date" in provenance:
        result["source_date"] = _nonempty_text(provenance["source_date"], "requirement_provenance.source_date")
    if "note" in provenance:
        result["note"] = _nonempty_text(provenance["note"], "requirement_provenance.note")
    return result


def sp554_section13_assessment(
    *,
    critical_temperature_c: float,
    actual_fire_resistance_min: float,
    required_fire_resistance_min: float,
    requirement_provenance: Mapping[str, Any],
    fire_regime: str = "standard",
    protection_state: str = "UNPROTECTED",
) -> dict[str, Any]:
    """
    Summary:
        Assess an SP554 Section-13 fire-resistance result against an explicit required time.

    Standard reference:
        Standard: СП 554.1311500.2026
        Version: enacted 2026 baseline
        Clause: 13.1-13.3, with workflow consequence from 5.3-5.5
        Annex: None
        Equation/Table: no numbered equation; exact comparison R_fact >= R_req
        Audit ID: FIRE-D4-13.1-13.3-001
        Normative status: executable

    Mathematical form:
        margin = R_fact - R_req; PASS iff R_fact >= R_req.  The R notation is
        formed from the exact calculated time and is not rounded to a standard class.

    Parameters:
        critical_temperature_c:
            Type: float. Unit: degC. Meaning: Section-13.1 critical steel temperature from FIRE-D2.
        actual_fire_resistance_min:
            Type: float. Unit: min. Meaning: Section-13.2 time to the critical temperature from FIRE-D3.
        required_fire_resistance_min:
            Type: float. Unit: min. Meaning: externally prescribed required fire resistance.
        requirement_provenance:
            Type: Mapping. Meaning: mandatory provenance of the external required value, including matching value_min.
        fire_regime:
            Type: str. Meaning: only ``standard`` is qualified for the Section-13.3 R designation in FIRE-D4.
        protection_state:
            Type: str. Meaning: ``UNPROTECTED`` or ``PROTECTED``; controls the downstream workflow action after failure.

    Returns:
        Type: dict[str, Any]. Meaning: exact Section-13 result, R notation, margin, PASS/FAIL and next action.

    Assumptions:
        - The upstream thermal result is valid and corresponds to the supplied critical temperature.
        - The required value is resolved by an external normative/project producer and is not inferred here.

    Sign convention:
        - Positive margin means reserve; negative margin means deficiency.

    Unit convention:
        - Temperature in degC and time in minutes.

    Applicability:
        - Standard-fire member results governed by loss of load-bearing capacity R.

    Limitations:
        - Alternative/real fire regimes remain fail-closed pending FIRE-D7 equivalent-duration/exposure qualification.
        - No nearest-class rounding, ceiling, flooring or tolerance is applied to the compliance decision.

    Raises:
        ValueError: invalid numeric input, missing/mismatched provenance, unsupported regime or protection state.

    Examples:
        >>> r = sp554_section13_assessment(critical_temperature_c=525.0, actual_fire_resistance_min=14.3, required_fire_resistance_min=15.0, requirement_provenance={"source_kind":"external_normative_requirement","source_document":"project fire requirement","source_reference":"R15","value_min":15.0})
        >>> r["compliance"]
        'FAIL'

    Tests:
        Unit tests:
            - tests/test_fire_d4_sp554_section13.py

    Implementation notes:
        - The calculated R notation exists even when the requirement is not met; PASS/FAIL is a separate state.
        - Compliance uses the unrounded floating-point calculation result exactly as delivered by FIRE-D3.
    """
    tcr = _finite_number(critical_temperature_c, "critical_temperature_c")
    actual = _finite_number(actual_fire_resistance_min, "actual_fire_resistance_min", nonnegative=True)
    required = _finite_number(required_fire_resistance_min, "required_fire_resistance_min", positive=True)
    regime = _nonempty_text(fire_regime, "fire_regime").lower()
    if regime != "standard":
        raise ValueError("FIRE-D4 Section 13.3 R designation is qualified only for the standard fire regime; use FIRE-D7 for other regimes")
    state = _nonempty_text(protection_state, "protection_state").upper()
    if state not in {"UNPROTECTED", "PROTECTED"}:
        raise ValueError("protection_state must be UNPROTECTED or PROTECTED")
    provenance = _requirement_provenance(requirement_provenance, required)

    passed = actual >= required
    margin = actual - required
    actual_notation = f"R {_format_minutes_exact(actual)}"
    required_notation = f"R {_format_minutes_exact(required)}"
    if passed:
        next_action = "REQUIREMENT_SATISFIED"
    elif state == "UNPROTECTED":
        next_action = "FIRE_PROTECTION_DESIGN_REQUIRED"
    else:
        next_action = "FIRE_PROTECTION_REDESIGN_REQUIRED"

    return {
        "status": "COMPLETE",
        "normative_scope": "SP554_13.1_13.3",
        "critical_temperature_c": tcr,
        "actual_fire_resistance_min": actual,
        "required_fire_resistance_min": required,
        "fire_regime": regime,
        "limit_state_symbol": "R",
        "actual_r_notation": actual_notation,
        "required_r_notation": required_notation,
        "class_rounding_applied": False,
        "comparison_rounding_applied": False,
        "compliance": "PASS" if passed else "FAIL",
        "compliance_pass": passed,
        "margin_min": margin,
        "protection_state": state,
        "next_action": next_action,
        "requirement_provenance": provenance,
        "section_13_1_result_definition": "critical_temperature_at_loss_of_load_bearing_capacity",
        "section_13_2_result_definition": "time_from_start_of_heat_exposure_to_critical_temperature",
        "section_13_3_designation_definition": "R_plus_exact_time_to_limit_state_under_standard_fire",
    }


def sp554_fire_protection_efficiency_indicators_13_4(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """
    Summary:
        Materialize SP554 13.4 fire-protection-efficiency indicator records from valid protected thermal results.

    Standard reference:
        Standard: СП 554.1311500.2026
        Version: enacted 2026 baseline
        Clause: 13.4 with upstream 12.3-12.5 result provenance
        Annex: None
        Equation/Table: no numbered equation
        Audit ID: FIRE-D4-13.4-001
        Normative status: executable_reporting_semantics

    Mathematical form:
        No new physical equation; validated tuples (delta_pr, d_prot, T_cr, t_cr) are retained as the indicators named by 13.4.

    Parameters:
        records:
            Type: sequence of mappings. Unit: mixed. Meaning: protected-result records carrying reduced thickness,
            protection thickness, critical temperature, time to critical temperature, source clause and validity flag.

    Returns:
        Type: dict[str, Any]. Meaning: normalized indicator set and variation census.

    Assumptions:
        - Each record originates from an upstream Section-12 route and has already satisfied its applicable validity gates.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Thicknesses in mm, temperature in degC, time in min.

    Applicability:
        - Results produced under clauses 12.3, 12.4 or 12.5 for fire-protected steel.

    Limitations:
        - This function does not certify a product or infer missing test points; it records/calculates no extrapolated points.

    Raises:
        ValueError: empty records, invalid source clause, invalid result flag or malformed numeric values.

    Examples:
        >>> x = sp554_fire_protection_efficiency_indicators_13_4([{"reduced_thickness_mm":10,"protection_thickness_mm":20,"critical_temperature_c":500,"time_to_critical_min":60,"source_clause":"12.5","result_valid":True}])
        >>> x["indicator_count"]
        1

    Tests:
        Unit tests:
            - tests/test_fire_d4_sp554_section13.py

    Implementation notes:
        - Variation counts are diagnostics only; SP554 13.4 does not prescribe a minimum grid size here.
    """
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence) or len(records) == 0:
        raise ValueError("records must be a non-empty sequence")
    normalized: list[dict[str, Any]] = []
    allowed_clauses = {"12.3", "12.4", "12.5"}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"records[{index}] must be an object")
        source_clause = _nonempty_text(record.get("source_clause"), f"records[{index}].source_clause")
        if source_clause not in allowed_clauses:
            raise ValueError(f"records[{index}].source_clause must be one of 12.3, 12.4, 12.5")
        if record.get("result_valid") is not True:
            raise ValueError(f"records[{index}] must have result_valid=true")
        normalized.append({
            "reduced_thickness_mm": _finite_number(record.get("reduced_thickness_mm"), f"records[{index}].reduced_thickness_mm", positive=True),
            "protection_thickness_mm": _finite_number(record.get("protection_thickness_mm"), f"records[{index}].protection_thickness_mm", positive=True),
            "critical_temperature_c": _finite_number(record.get("critical_temperature_c"), f"records[{index}].critical_temperature_c"),
            "time_to_critical_min": _finite_number(record.get("time_to_critical_min"), f"records[{index}].time_to_critical_min", nonnegative=True),
            "source_clause": source_clause,
            "result_valid": True,
        })
    return {
        "status": "INDICATORS_RECORDED",
        "normative_scope": "SP554_13.4",
        "indicator_count": len(normalized),
        "unique_reduced_thickness_count": len({row["reduced_thickness_mm"] for row in normalized}),
        "unique_protection_thickness_count": len({row["protection_thickness_mm"] for row in normalized}),
        "records": normalized,
        "certification_claimed": False,
        "extrapolation_applied": False,
    }


def sp554_fire_result_assessment_workflow(case: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute the FIRE-D4 end-to-end Section-13 assessment over the frozen FIRE-D3 thermal runtime.

    Standard reference:
        Standard: СП 554.1311500.2026
        Version: enacted 2026 baseline
        Clause: 13.1-13.4, with 5.3-5.5 downstream decision semantics
        Annex: None
        Equation/Table: Section-13 result definitions and exact R_fact >= R_req comparison
        Audit ID: FIRE-D4-RUNTIME-001
        Normative status: executable

    Mathematical form:
        FIRE-D3(T_cr, thermal inputs) -> R_fact; then exact comparison with externally sourced R_req.

    Parameters:
        case:
            Type: Mapping[str, Any]. Meaning: FIRE-D4 case containing a valid FIRE-D3 thermal case plus required value and provenance.

    Returns:
        Type: dict[str, Any]. Meaning: upstream thermal result, Section-13 assessment and optional 13.4 indicator record.

    Assumptions:
        - FIRE-D3 remains the sole thermal producer; FIRE-D4 does not recalculate heat transfer independently.

    Sign convention:
        - Positive compliance margin is reserve.

    Unit convention:
        - Follows FIRE-D3 plus minutes for required/actual fire resistance.

    Applicability:
        - Standard-fire SP554 member calculations with an explicit externally sourced required R time.

    Limitations:
        - Required fire resistance is not derived from SP2/building classification in this stage.
        - Alternative fire regimes remain deferred to FIRE-D7.

    Raises:
        ValueError: invalid/missing requirement provenance, invalid FIRE-D3 result, or unsupported regime.

    Examples:
        >>> case = {"thermal_route":"UNPROTECTED_STEP_12_2","critical_temperature_c":525.0192844353662,"reduced_thickness_mm":10.0,"required_fire_resistance_min":15.0,"fire_regime":"standard","requirement_provenance":{"source_kind":"external_normative_requirement","source_document":"project fire requirement","source_reference":"R15","value_min":15.0}}
        >>> sp554_fire_result_assessment_workflow(case)["assessment"]["compliance"]
        'FAIL'

    Tests:
        Unit tests:
            - tests/test_fire_d4_sp554_section13.py
        Validation cases:
            - FIRE-D4-SECTION13-CONTROL-001

    Implementation notes:
        - A D3 result with status other than COMPLETE or a null actual fire-resistance time is rejected.
        - Protected 13.4 records are emitted only from a valid completed upstream protected route.
    """
    if not isinstance(case, Mapping):
        raise TypeError("case must be a mapping")
    thermal = sp554_fire_thermal_guided_workflow(case)
    if thermal.get("status") != "COMPLETE" or thermal.get("actual_fire_resistance_min") is None:
        raise ValueError("FIRE-D4 requires a valid COMPLETE FIRE-D3 thermal result")
    route = str(thermal["thermal_route"])
    protection_state = "UNPROTECTED" if route.startswith("UNPROTECTED_") else "PROTECTED"
    if "fire_regime" not in case:
        raise ValueError("fire_regime is required for FIRE-D4")
    assessment = sp554_section13_assessment(
        critical_temperature_c=_finite_number(thermal.get("critical_temperature_c"), "thermal.critical_temperature_c"),
        actual_fire_resistance_min=_finite_number(thermal.get("actual_fire_resistance_min"), "thermal.actual_fire_resistance_min", nonnegative=True),
        required_fire_resistance_min=_finite_number(case.get("required_fire_resistance_min"), "required_fire_resistance_min", positive=True),
        requirement_provenance=case.get("requirement_provenance"),
        fire_regime=str(case["fire_regime"]),
        protection_state=protection_state,
    )
    result: dict[str, Any] = {
        "status": "COMPLETE",
        "normative_scope": "SP554_SECTION13",
        "upstream_thermal_result": thermal,
        "assessment": assessment,
        "section_13_runtime_closed": True,
        "required_fire_resistance_source_is_external": True,
    }
    if protection_state == "PROTECTED":
        thickness = thermal.get("protection_thickness_mm")
        if thickness is None and isinstance(case.get("protection_model"), Mapping):
            thickness = case["protection_model"].get("thickness_mm")
        if thickness is None:
            thickness = case.get("protection_thickness_mm")
        source_clause = "12.5" if route == "PROTECTED_FDM_12_5" else "12.4"
        if thickness is not None:
            result["section_13_4_indicator"] = sp554_fire_protection_efficiency_indicators_13_4([{
                "reduced_thickness_mm": thermal["reduced_thickness_mm"],
                "protection_thickness_mm": thickness,
                "critical_temperature_c": thermal["critical_temperature_c"],
                "time_to_critical_min": thermal["actual_fire_resistance_min"],
                "source_clause": source_clause,
                "result_valid": True,
            }])
    return result
