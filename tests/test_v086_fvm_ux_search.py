from __future__ import annotations

import math

from standard_core.fire_sp554_thermal_v085 import install_thermal_solver_patch
from standard_core.fire_ui23_protection_route import _build_model_v23
from standard_core.sp16_mech7_v086_fvm_runtime import (
    _direct_fdm_12_5_v086,
    _inverse_fdm_12_5_v086,
)
from streamlit_guided_ux_v086 import (
    _PROTECTED_TIME_STYLES,
    _fvm_model_svg,
    _profile_chart,
    _svg_chart,
)


def _manual_values() -> dict:
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


def _arss_inverse_values() -> dict:
    values = {
        "protection_source_mode": "sto_arss_library",
        "protection_arss_material_id": "mineral_wool_board",
        "delta_pr_protected": 10.0,
        "critical_temperature_c": 600.0,
        "fire_temperature_regime": "standard",
        "protection_material_density_kg_m3": 100.0,
        "protection_material_moisture_percent": 0.5,
        "protection_material_emissivity": 0.92,
        "protection_material_lambda_A": -0.107,
        "protection_material_lambda_B": 0.00058,
        "protection_material_cp_C": 582.0,
        "protection_material_cp_D": 0.63,
        "protection_material_temperature_basis": "K",
        "protection_12_6_max_deviation_pct": 15.0,
        "protection_12_6_validation_evidence_complete": True,
        "validation_within_20_percent_all_cases": True,
        "required_fire_resistance_min": 60.0,
        "protection_search_min_thickness_mm": 5.0,
        "protection_search_max_thickness_mm": 40.0,
    }
    values.update(_build_model_v23(values, {}))
    return values


def test_v086_interactive_direct_uses_one_working_mesh_not_mandatory_2n():
    install_thermal_solver_patch()
    result = _direct_fdm_12_5_v086(_manual_values(), {})
    trace = result["protection_12_5_calculation_trace"]
    vis = trace["visualization"]
    assert "mesh_convergence" not in trace
    assert vis["layer_count"] == 14
    assert vis["mesh_policy"]["interval_count"] == 14
    assert math.isclose(vis["dx_mm"], 20.0 / 14.0, abs_tol=1e-12)


def test_v086_fvm_model_hides_gradient_debug_diagram_and_doubled_mesh_message():
    install_thermal_solver_patch()
    vis = _direct_fdm_12_5_v086(_manual_values(), {})["protection_12_5_calculation_trace"]["visualization"]
    svg = _fvm_model_svg(vis)
    assert "Температурный градиент последнего шага" not in svg
    assert "dT/dx" not in svg
    assert "n→2n используется только в validation/debug" in svg
    assert "рабочая сетка n=14" in svg


def test_v086_thickness_profile_has_explicit_absolute_time_legend():
    install_thermal_solver_patch()
    vis = _direct_fdm_12_5_v086(_manual_values(), {})["protection_12_5_calculation_trace"]["visualization"]
    svg = _profile_chart(vis)
    times = [float(row["time_min"]) for row in vis["profile_samples"]]
    assert len(times) >= 2
    for t in times:
        assert f"t = {t:.2f} мин" in svg
    assert "stroke-dasharray=\"4 3\"" in svg


def test_v086_time_chart_has_named_legend_and_five_minute_axis():
    rows = []
    for name in _PROTECTED_TIME_STYLES:
        rows.extend([
            {"x": 0.0, "y": 20.0, "series": name},
            {"x": 12.2, "y": 400.0, "series": name},
        ])
    svg = _svg_chart(
        rows,
        x_key="x",
        y_key="y",
        group_key="series",
        x_tick_step=5.0,
        style_map=_PROTECTED_TIME_STYLES,
        actual_group="Сталь",
        fire_group="ISO 834 / ГОСТ 30247.0",
    )
    for name in _PROTECTED_TIME_STYLES:
        assert name in svg
    for tick in (0, 5, 10, 15):
        assert f">{tick}<" in svg
    assert ">12.2<" not in svg


def test_v086_inverse_search_finds_real_midrange_arss_solution_without_2n_qualification():
    install_thermal_solver_patch()
    result = _inverse_fdm_12_5_v086(_arss_inverse_values(), {})
    assert 5.0 < result["protection_thickness_mm"] < 40.0
    assert result["protected_fire_resistance_min"] >= 60.0
    trace = result["protection_12_5_calculation_trace"]
    assert trace["mode"] == "inverse_minimum_thickness_v086_first_feasible_crossing"
    assert trace["selected_result_basis"] == "single_qualified_production_mesh; final-only visualization trace"
    assert trace["selected_result"]["visualization"]["schema"] == "sp554_v085_fvm_visualization_v2"
    assert "mesh_convergence" not in trace["selected_result"]
    assert 20.0 < result["protection_thickness_mm"] < 25.0
