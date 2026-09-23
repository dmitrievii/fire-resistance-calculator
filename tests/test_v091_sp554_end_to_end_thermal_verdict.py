from __future__ import annotations

import pytest

from standard_core import fire_sp554_runtime as mechanical_runtime
from standard_core.fire_sp554_assessment import sp554_fire_result_assessment_workflow


R_REQ_MIN = 15.0


def _compression_case(n_n: float) -> dict:
    lambda_z = 35.28
    lambda_y = 119.39
    return {
        "member_route": "central_compression",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": 255.0,
        "route": {
            "N_n": n_n,
            "A_gross_mm2": 5282.0,
            "gamma_c": 0.9,
            "sp16_lambda_z_geom": lambda_z,
            "sp16_lambda_y_geom": lambda_y,
            "sp16_l_eff_z": 3000.0,
            "sp16_l_eff_y": 6000.0,
            "sp16_i_z": 3000.0 / lambda_z,
            "sp16_i_y": 6000.0 / lambda_y,
            "sp16_curve_z": "b",
            "sp16_curve_y": "c",
        },
    }


def _section13_case(critical_temperature_c: float) -> dict:
    return {
        "thermal_route": "UNPROTECTED_STEP_12_2",
        "critical_temperature_c": critical_temperature_c,
        "reduced_thickness_mm": 10.0,
        "initial_temperature_c": 20.0,
        "time_step_min": 0.1,
        "max_time_min": 60.0,
        "steel_properties_source": "sp554_12_2_defaults",
        "required_fire_resistance_min": R_REQ_MIN,
        "fire_regime": "standard",
        "requirement_provenance": {
            "source_kind": "external_normative_requirement",
            "source_document": "Explicit project fire-safety requirement",
            "source_reference": "Regression case R15",
            "value_min": R_REQ_MIN,
        },
    }


def test_v091_full_sp554_chain_recomputes_thermal_resistance_and_verdict_from_tcr():
    # Same member/thermal geometry, different qualified design action.  No
    # E_norm_n_mm2 is supplied anywhere: v0.91 §9.2 must use E=206000 N/mm².
    lower_action = mechanical_runtime.sp554_fire_mechanical_guided_workflow(
        _compression_case(250_000.0)
    )
    higher_action = mechanical_runtime.sp554_fire_mechanical_guided_workflow(
        _compression_case(550_000.0)
    )

    tcr_low_action = float(lower_action["critical_temperature_c"])
    tcr_high_action = float(higher_action["critical_temperature_c"])
    assert tcr_low_action > tcr_high_action
    assert lower_action["route_trace"]["governing_strength_axis"] == "y"
    assert lower_action["route_trace"]["governing_stiffness_axis"] == "y"
    assert higher_action["route_trace"]["governing_strength_axis"] == "y"
    assert higher_action["route_trace"]["governing_stiffness_axis"] == "y"

    lower_assessed = sp554_fire_result_assessment_workflow(
        _section13_case(tcr_low_action)
    )
    higher_assessed = sp554_fire_result_assessment_workflow(
        _section13_case(tcr_high_action)
    )

    lower_thermal = lower_assessed["thermal_result"]
    higher_thermal = higher_assessed["thermal_result"]
    lower_verdict = lower_assessed["assessment"]
    higher_verdict = higher_assessed["assessment"]

    # D2 -> D3 handoff: each thermal run must preserve exactly the mechanical Tcr.
    assert lower_thermal["critical_temperature_c"] == pytest.approx(tcr_low_action)
    assert higher_thermal["critical_temperature_c"] == pytest.approx(tcr_high_action)

    r_fact_lower_action = float(lower_thermal["actual_fire_resistance_min"])
    r_fact_higher_action = float(higher_thermal["actual_fire_resistance_min"])
    assert r_fact_lower_action > r_fact_higher_action

    # D3 -> D4 handoff: Section 13 consumes the exact unrounded thermal result.
    assert lower_verdict["actual_fire_resistance_min"] == pytest.approx(r_fact_lower_action)
    assert higher_verdict["actual_fire_resistance_min"] == pytest.approx(r_fact_higher_action)
    assert lower_verdict["required_fire_resistance_min"] == pytest.approx(R_REQ_MIN)
    assert higher_verdict["required_fire_resistance_min"] == pytest.approx(R_REQ_MIN)
    assert lower_verdict["margin_min"] == pytest.approx(r_fact_lower_action - R_REQ_MIN)
    assert higher_verdict["margin_min"] == pytest.approx(r_fact_higher_action - R_REQ_MIN)

    # This pair deliberately straddles R15.  It proves that a mechanical change
    # propagates through Tcr and the real thermal solver into the final verdict.
    assert lower_verdict["compliance"] == "PASS"
    assert lower_verdict["compliance_pass"] is True
    assert higher_verdict["compliance"] == "FAIL"
    assert higher_verdict["compliance_pass"] is False
