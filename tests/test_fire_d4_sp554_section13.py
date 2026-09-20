from __future__ import annotations

import pytest

from standard_core.fire_sp554_assessment import (
    sp554_fire_protection_efficiency_indicators_13_4,
    sp554_fire_result_assessment_workflow,
    sp554_section13_assessment,
)


def _prov(value=15.0):
    return {
        "source_kind": "external_normative_requirement",
        "source_document": "Explicit project fire-safety requirement",
        "source_reference": "Required R value",
        "value_min": value,
    }


def _base_case(required=15.0):
    return {
        "thermal_route": "UNPROTECTED_STEP_12_2",
        "critical_temperature_c": 525.0192844353662,
        "reduced_thickness_mm": 10.0,
        "initial_temperature_c": 20.0,
        "time_step_min": 0.1,
        "max_time_min": 60.0,
        "steel_properties_source": "sp554_12_2_defaults",
        "required_fire_resistance_min": required,
        "fire_regime": "standard",
        "requirement_provenance": _prov(required),
    }


def test_fire_d4_control_case_fails_r15_without_rounding():
    result = sp554_fire_result_assessment_workflow(_base_case())
    a = result["assessment"]
    assert a["actual_fire_resistance_min"] == pytest.approx(14.326394173167056)
    assert a["required_fire_resistance_min"] == 15.0
    assert a["compliance"] == "FAIL"
    assert a["next_action"] == "FIRE_PROTECTION_DESIGN_REQUIRED"
    assert a["actual_r_notation"] == "R 14.3263941732"
    assert a["class_rounding_applied"] is False


def test_fire_d4_exact_boundary_passes():
    a = sp554_section13_assessment(
        critical_temperature_c=500.0,
        actual_fire_resistance_min=15.0,
        required_fire_resistance_min=15.0,
        requirement_provenance=_prov(),
    )
    assert a["compliance"] == "PASS"
    assert a["margin_min"] == 0.0
    assert a["next_action"] == "REQUIREMENT_SATISFIED"


def test_fire_d4_does_not_round_14_999999_to_r15():
    a = sp554_section13_assessment(
        critical_temperature_c=500.0,
        actual_fire_resistance_min=14.999999,
        required_fire_resistance_min=15.0,
        requirement_provenance=_prov(),
    )
    assert a["compliance"] == "FAIL"
    assert a["actual_r_notation"] == "R 14.999999"


def test_fire_d4_r_notation_exists_even_when_compliance_fails():
    a = sp554_section13_assessment(
        critical_temperature_c=500.0,
        actual_fire_resistance_min=10.0,
        required_fire_resistance_min=60.0,
        requirement_provenance=_prov(60.0),
    )
    assert a["compliance"] == "FAIL"
    assert a["actual_r_notation"] == "R 10"
    assert a["required_r_notation"] == "R 60"


def test_fire_d4_requirement_provenance_value_must_match():
    with pytest.raises(ValueError, match="exactly match"):
        sp554_section13_assessment(
            critical_temperature_c=500.0,
            actual_fire_resistance_min=60.0,
            required_fire_resistance_min=45.0,
            requirement_provenance=_prov(60.0),
        )


def test_fire_d4_requirement_provenance_is_mandatory():
    with pytest.raises(ValueError, match="requirement_provenance"):
        sp554_section13_assessment(
            critical_temperature_c=500.0,
            actual_fire_resistance_min=60.0,
            required_fire_resistance_min=45.0,
            requirement_provenance=None,
        )


def test_fire_d4_nonstandard_fire_is_fail_closed_pending_d7():
    with pytest.raises(ValueError, match="FIRE-D7"):
        sp554_section13_assessment(
            critical_temperature_c=500.0,
            actual_fire_resistance_min=60.0,
            required_fire_resistance_min=45.0,
            requirement_provenance=_prov(45.0),
            fire_regime="alternative",
        )


def test_fire_d4_protected_failure_routes_to_redesign():
    a = sp554_section13_assessment(
        critical_temperature_c=500.0,
        actual_fire_resistance_min=30.0,
        required_fire_resistance_min=45.0,
        requirement_provenance=_prov(45.0),
        protection_state="PROTECTED",
    )
    assert a["next_action"] == "FIRE_PROTECTION_REDESIGN_REQUIRED"


def test_fire_d4_13_4_records_valid_indicators_without_certification_claim():
    out = sp554_fire_protection_efficiency_indicators_13_4([
        {"reduced_thickness_mm": 5.0, "protection_thickness_mm": 10.0, "critical_temperature_c": 500.0, "time_to_critical_min": 45.0, "source_clause": "12.4", "result_valid": True},
        {"reduced_thickness_mm": 10.0, "protection_thickness_mm": 20.0, "critical_temperature_c": 500.0, "time_to_critical_min": 90.0, "source_clause": "12.5", "result_valid": True},
    ])
    assert out["indicator_count"] == 2
    assert out["unique_reduced_thickness_count"] == 2
    assert out["unique_protection_thickness_count"] == 2
    assert out["certification_claimed"] is False
    assert out["extrapolation_applied"] is False


def test_fire_d4_13_4_rejects_invalid_upstream_result():
    with pytest.raises(ValueError, match="result_valid=true"):
        sp554_fire_protection_efficiency_indicators_13_4([
            {"reduced_thickness_mm": 10.0, "protection_thickness_mm": 20.0, "critical_temperature_c": 500.0, "time_to_critical_min": 60.0, "source_clause": "12.5", "result_valid": False}
        ])
