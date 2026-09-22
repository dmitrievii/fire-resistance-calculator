from __future__ import annotations

import math

from standard_core.fire_sp554_thermal_v085 import (
    FOURIER_SAFETY_LIMIT,
    install_thermal_solver_patch,
    select_fvm_discretization,
)
from standard_core.sp16_mech7_v085_fvm_runtime import _direct_fdm_12_5_v085
from streamlit_guided_ux_v085 import _fvm_model_svg, _profile_chart, _temperature_bounds


def _values() -> dict:
    return {
        "protection_source_mode": "manual_properties",
        "critical_temperature_c": 550.0,
        "delta_pr_protected": 10.0,
        "fire_temperature_regime": "standard",
        "protection_candidate_thickness_mm": 20.0,
        "protection_12_5_model_parameters": {
            "density_kg_m3": 500.0,
            "conductivity_A_w_mk": 0.2,
            "conductivity_B_w_mk2": 0.0,
            "heat_capacity_C_j_kgk": 1000.0,
            "heat_capacity_D_j_kgk2": 0.0,
            "initial_moisture_percent": 0.0,
            "temperature_basis": "degC",
        },
        "protection_12_6_validation_evidence_complete": True,
        "validation_within_20_percent_all_cases": True,
        "protection_12_6_max_deviation_pct": 20.0,
    }


def _bare_case() -> dict:
    v = _values()
    return {
        "critical_temperature_c": v["critical_temperature_c"],
        "initial_temperature_c": 20.0,
        "protection_model": dict(v["protection_12_5_model_parameters"]),
    }


def test_v085_temperature_axes_start_at_zero_and_round_to_exact_100c_ticks():
    ymin, ymax = _temperature_bounds([{"T": 20.0}, {"T": 537.2}], "T")
    assert ymin == 0.0
    assert ymax == 600.0
    assert ymax % 100.0 == 0.0


def test_v085_base_mesh_is_geometry_driven_and_explicit_step_respects_fourier_limit():
    policy = select_fvm_discretization(_bare_case(), 20.0)
    assert policy["interval_count"] == 14
    assert policy["interval_count"] > 3
    assert policy["dx_mm"] <= 1.5 + 1e-12
    assert policy["fourier_number_max"] <= FOURIER_SAFETY_LIMIT + 1e-12


def test_v085_direct_result_is_reported_on_refined_converged_mesh_and_keeps_steel_separate():
    install_thermal_solver_patch()
    result = _direct_fdm_12_5_v085(_values(), {})
    trace = result["protection_12_5_calculation_trace"]
    conv = trace["mesh_convergence"]
    vis = trace["visualization"]
    policy = vis["mesh_policy"]

    assert conv["status"] == "PASS"
    assert conv["coarse_interval_count"] == 14
    assert conv["refined_interval_count"] == 28
    assert policy["interval_count"] == 28
    assert vis["layer_count"] == 28
    assert math.isclose(vis["dx_mm"], 20.0 / 28.0, rel_tol=0.0, abs_tol=1e-12)

    positions = vis["protection_node_positions_mm"]
    final = vis["final_state"]
    assert len(positions) == 28
    assert len(final["protection_temperatures_c"]) == 28
    assert positions[-1] < vis["steel_interface_position_mm"] == 20.0
    assert len(final["temperature_gradients_c_per_mm"]) == 28
    assert math.isclose(final["steel_temperature_c"], 550.0, abs_tol=1e-7)


def test_v085_fvm_svg_explicitly_renders_last_step_temperature_gradient():
    install_thermal_solver_patch()
    trace = _direct_fdm_12_5_v085(_values(), {})["protection_12_5_calculation_trace"]
    svg = _fvm_model_svg(trace["visualization"])
    assert "Температурный градиент последнего шага" in svg
    assert "dT/dx, °C/мм" in svg
    assert "Проверка сходимости" in svg
    assert "n=14 → 28" in svg


def test_v085_thickness_profile_uses_protection_nodes_and_dashed_interface_to_lumped_steel():
    install_thermal_solver_patch()
    trace = _direct_fdm_12_5_v085(_values(), {})["protection_12_5_calculation_trace"]
    svg = _profile_chart(trace["visualization"])
    assert "stroke-dasharray=\"4 3\"" in svg
    assert "сталь 550 °C" in svg
    # Steel is not appended to the protection-node polyline as a fake material node.
    assert trace["visualization"]["protection_node_positions_mm"][-1] < 20.0
