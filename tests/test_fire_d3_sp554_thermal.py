from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_sp554_thermal import sp554_fire_thermal_guided_workflow
from standard_core.runner import run_case

ROOT = Path(__file__).resolve().parents[1]


def _unprotected(**extra):
    case = {
        "thermal_route": "UNPROTECTED_STEP_12_2",
        "critical_temperature_c": 525.0192844353662,
        "reduced_thickness_mm": 10.0,
        "initial_temperature_c": 20.0,
        "time_step_min": 0.1,
        "max_time_min": 60.0,
        "steel_properties_source": "sp554_12_2_defaults",
    }
    case.update(extra)
    return case


def _matrix_dataset(matrix=None, allow_carry=False):
    return {
        "product_id": "TEST-PRODUCT",
        "source_kind": "technical_documentation_12_7_9",
        "critical_temperature_c": 550.0,
        "steel_group": "ordinary",
        "fire_regime": "standard",
        "technical_documentation_12_7_9_confirmed": True,
        "allow_greater_delta_carry_forward": allow_carry,
        "reduced_thickness_axis_mm": [5.0, 10.0],
        "protection_thickness_axis_mm": [10.0, 20.0, 30.0],
        "time_matrix_min": matrix or [[30.0, 60.0, 90.0], [40.0, 80.0, 120.0]],
    }


def test_fire_d3_unprotected_control_couples_exact_fire_d2_temperature():
    result = sp554_fire_thermal_guided_workflow(_unprotected())
    assert result["status"] == "COMPLETE"
    assert result["actual_fire_resistance_min"] == pytest.approx(14.326394173167056, abs=1e-12)
    assert result["crossing_bracket"] == pytest.approx([14.3, 14.4])
    assert result["fire_d2_handoff_preserved"] is True


def test_fire_d3_reduced_thickness_from_area_and_heated_perimeter_is_equivalent():
    case = _unprotected()
    case.pop("reduced_thickness_mm")
    case.update({"area_mm2": 5000.0, "heated_perimeter_mm": 500.0})
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["reduced_thickness_mm"] == pytest.approx(10.0)
    assert result["actual_fire_resistance_min"] == pytest.approx(14.326394173167056)
    assert result["reduced_thickness_trace"]["equation_ref"] == "12.2"


def test_fire_d3_figure1_route_matches_step_route_at_printed_10mm_curve():
    case = _unprotected(thermal_route="UNPROTECTED_FIGURE1_12_2")
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["actual_fire_resistance_min"] == pytest.approx(14.326394173167056)
    assert result["figure1_bracketing_reduced_thickness_mm"] == [10.0, 10.0]


def test_fire_d3_figure1_linear_interpolation_between_printed_curves():
    left = sp554_fire_thermal_guided_workflow(_unprotected(thermal_route="UNPROTECTED_FIGURE1_12_2", reduced_thickness_mm=10.0))
    right = sp554_fire_thermal_guided_workflow(_unprotected(thermal_route="UNPROTECTED_FIGURE1_12_2", reduced_thickness_mm=15.0))
    mid = sp554_fire_thermal_guided_workflow(_unprotected(thermal_route="UNPROTECTED_FIGURE1_12_2", reduced_thickness_mm=12.5))
    assert mid["actual_fire_resistance_min"] == pytest.approx((left["actual_fire_resistance_min"] + right["actual_fire_resistance_min"]) / 2.0)


def test_fire_d3_figure1_extrapolation_is_forbidden():
    with pytest.raises(ValueError, match="3-20 mm"):
        sp554_fire_thermal_guided_workflow(_unprotected(thermal_route="UNPROTECTED_FIGURE1_12_2", reduced_thickness_mm=25.0))


def test_fire_d3_default_steel_properties_fail_above_800c():
    with pytest.raises(ValueError, match="20-800 C"):
        sp554_fire_thermal_guided_workflow(_unprotected(critical_temperature_c=850.0, max_time_min=120.0))


def test_fire_d3_explicit_properties_can_cover_target_above_800c():
    case = _unprotected(
        critical_temperature_c=820.0,
        max_time_min=120.0,
        steel_properties_source="explicit",
        steel_density_kg_m3=7850.0,
        steel_heat_capacity_base_j_kgk=480.0,
        steel_heat_capacity_temp_coeff_per_c=0.00063,
        furnace_emissivity=0.85,
        steel_emissivity=0.625,
    )
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["status"] == "COMPLETE"
    assert result["actual_fire_resistance_min"] > 0.0


def test_fire_d3_matrix_exact_node_direct():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 10.0,
        "protected_task_mode": "verify_given_thickness",
        "protection_thickness_mm": 20.0,
        "performance_dataset": _matrix_dataset(),
    }
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["actual_fire_resistance_min"] == pytest.approx(80.0)


def test_fire_d3_matrix_bilinear_interpolation_in_delta_and_protection_only():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 7.5,
        "protected_task_mode": "verify_given_thickness",
        "protection_thickness_mm": 15.0,
        "performance_dataset": _matrix_dataset(),
    }
    result = sp554_fire_thermal_guided_workflow(case)
    # delta interpolation gives [35,70,105], then thickness 15 -> 52.5
    assert result["actual_fire_resistance_min"] == pytest.approx(52.5)


def test_fire_d3_matrix_critical_temperature_interpolation_is_not_invented():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 525.0192844353662,
        "reduced_thickness_mm": 7.5,
        "protected_task_mode": "verify_given_thickness",
        "protection_thickness_mm": 15.0,
        "performance_dataset": _matrix_dataset(),
    }
    with pytest.raises(ValueError, match="exact documented critical-temperature"):
        sp554_fire_thermal_guided_workflow(case)


def test_fire_d3_matrix_inverse_minimum_thickness():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 10.0,
        "protected_task_mode": "determine_minimum_thickness",
        "required_fire_resistance_min": 100.0,
        "performance_dataset": _matrix_dataset(),
    }
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["minimum_protection_thickness_mm"] == pytest.approx(25.0)


def test_fire_d3_matrix_inverse_preserves_nonmonotonic_source_and_finds_first_crossing():
    dataset = _matrix_dataset(matrix=[[30.0, 80.0, 70.0], [30.0, 80.0, 70.0]])
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 7.0,
        "protected_task_mode": "determine_minimum_thickness",
        "required_fire_resistance_min": 60.0,
        "performance_dataset": dataset,
    }
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["minimum_protection_thickness_mm"] == pytest.approx(16.0)
    assert result["source_curve_nonmonotonic"] is True
    assert result["warnings"]


def test_fire_d3_matrix_inverse_no_extrapolation_if_requirement_not_met():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 10.0,
        "protected_task_mode": "determine_minimum_thickness",
        "required_fire_resistance_min": 130.0,
        "performance_dataset": _matrix_dataset(),
    }
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert result["minimum_protection_thickness_mm"] is None


def test_fire_d3_matrix_12_4_greater_delta_is_carry_forward_not_slope_extrapolation():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 12.0,
        "protected_task_mode": "verify_given_thickness",
        "protection_thickness_mm": 20.0,
        "performance_dataset": _matrix_dataset(allow_carry=True),
    }
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["actual_fire_resistance_min"] == pytest.approx(80.0)
    assert result["matrix_interpolation_trace"]["greater_delta_carry_forward"] is True


def test_fire_d3_matrix_greater_delta_without_explicit_12_4_permission_fails_closed():
    case = {
        "thermal_route": "PROTECTED_MATRIX_12_10",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 12.0,
        "protected_task_mode": "verify_given_thickness",
        "protection_thickness_mm": 20.0,
        "performance_dataset": _matrix_dataset(allow_carry=False),
    }
    with pytest.raises(ValueError, match="extrapolation is forbidden"):
        sp554_fire_thermal_guided_workflow(case)


def _fdm(reference=100.0, moisture=0.0):
    return {
        "thermal_route": "PROTECTED_FDM_12_5",
        "critical_temperature_c": 550.0,
        "reduced_thickness_mm": 10.0,
        "time_step_min": 0.0005,
        "max_time_min": 180.0,
        "protection_model": {
            "thickness_mm": 20.0,
            "layer_count": 4,
            "density_kg_m3": 500.0,
            "conductivity_A_w_mk": 0.2,
            "conductivity_B_w_mk2": 0.0,
            "heat_capacity_C_j_kgk": 1000.0,
            "heat_capacity_D_j_kgk2": 0.0,
            "initial_moisture_percent": moisture,
        },
        "validation_reference_times_min": [reference],
    }


def test_fire_d3_protected_fdm_dry_executes_confirmed_errata_and_12_6_pass_gate():
    result = sp554_fire_thermal_guided_workflow(_fdm(reference=100.0))
    assert result["status"] == "COMPLETE"
    assert result["calculated_time_min"] == pytest.approx(85.4999000586283, rel=1e-10)
    assert result["validation_12_6"]["all_within_20_percent"] is True
    assert result["errata_overlay"]["formula_12_5"]["production"] == "+ t_0 - t_phi"
    assert result["errata_overlay"]["formula_12_6"]["production_denominator"] == "C + D*t_n"


def test_fire_d3_protected_fdm_12_6_more_than_20_percent_invalidates_result():
    result = sp554_fire_thermal_guided_workflow(_fdm(reference=120.0))
    assert result["status"] == "INVALID_BY_12_6"
    assert result["actual_fire_resistance_min"] is None
    assert result["validation_12_6"]["result_valid"] is False


def test_fire_d3_protected_fdm_moisture_requires_explicit_reconciled_policy():
    with pytest.raises(ValueError, match="moisture_accounting_mode"):
        sp554_fire_thermal_guided_workflow(_fdm(moisture=5.0))


def test_fire_d3_runner_materializes_case_and_report():
    result = run_case(ROOT / "examples/fire_d3_sp554_thermal_case.json", ROOT)
    assert result["engineering_calculation_performed"] is True
    assert result["results"]["actual_fire_resistance_min"] == pytest.approx(14.326394173167056)
    assert (ROOT / "outputs/sp554_fire_thermal_guided_result.json").exists()
    assert (ROOT / "reports/sp554_fire_thermal_guided_case_report.md").exists()
