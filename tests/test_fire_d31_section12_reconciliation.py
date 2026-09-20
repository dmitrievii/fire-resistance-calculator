from __future__ import annotations

import pytest

from standard_core.fire_sp554_thermal import (
    sp554_fictitious_temperature_12_8,
    sp554_fire_thermal_guided_workflow,
)


def _wet_case(mode: str = "embedded_in_thermal_properties"):
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
            "initial_moisture_percent": 5.0,
            "moisture_accounting_mode": mode,
            "moisture_embedded_in_properties_confirmed": True,
        },
        "validation_reference_times_min": [100.0],
    }


def test_fire_d31_formula_12_8_scalar_is_executable_and_zero_for_dry_material():
    base = dict(
        protection_density_kg_m3=900.0,
        layer_thickness_m=0.005,
        protection_heat_capacity_j_kgk=860.0,
        steel_density_kg_m3=7850.0,
        reduced_steel_thickness_m=0.010,
        steel_heat_capacity_j_kgk=486.0,
    )
    assert sp554_fictitious_temperature_12_8(initial_moisture_percent=0.0, **base) == 0.0
    wet = sp554_fictitious_temperature_12_8(initial_moisture_percent=15.0, **base)
    assert wet > 0.0
    assert wet == pytest.approx(19.027840143691066, rel=1e-12)


def test_fire_d31_formula_12_8_scales_linearly_with_initial_moisture():
    args = dict(
        protection_density_kg_m3=500.0,
        layer_thickness_m=0.005,
        protection_heat_capacity_j_kgk=1000.0,
        steel_density_kg_m3=7850.0,
        reduced_steel_thickness_m=0.010,
        steel_heat_capacity_j_kgk=486.0,
    )
    a = sp554_fictitious_temperature_12_8(initial_moisture_percent=2.0, **args)
    b = sp554_fictitious_temperature_12_8(initial_moisture_percent=6.0, **args)
    assert b == pytest.approx(3.0 * a)


def test_fire_d31_wet_material_may_execute_only_when_moisture_is_embedded_and_confirmed():
    result = sp554_fire_thermal_guided_workflow(_wet_case())
    assert result["status"] == "COMPLETE"
    assert result["actual_fire_resistance_min"] == pytest.approx(85.4999000586283, rel=1e-10)
    policy = result["moisture_accounting"]
    assert policy["mode"] == "embedded_in_thermal_properties"
    assert policy["explicit_t_phi_applied"] is False
    assert policy["initial_t_phi_c"] > 0.0
    assert result["validation_12_6"]["result_valid"] is True


def test_fire_d31_embedded_mode_without_explicit_confirmation_fails_closed():
    case = _wet_case()
    case["protection_model"]["moisture_embedded_in_properties_confirmed"] = False
    with pytest.raises(ValueError, match="double counting"):
        sp554_fire_thermal_guided_workflow(case)


def test_fire_d31_literal_repeated_t_phi_mode_is_deliberately_not_executed():
    case = _wet_case("explicit_t_phi_12_8")
    with pytest.raises(ValueError, match="discretization-invariant"):
        sp554_fire_thermal_guided_workflow(case)


def test_fire_d31_protection_surface_emissivity_is_explicitly_supported():
    case = _wet_case()
    case["protection_model"]["surface_emissivity"] = 0.86
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["surface_emissivity"] == pytest.approx(0.86)
    assert result["status"] in {"COMPLETE", "INVALID_BY_12_6"}


def test_fire_d31_12_6_remains_mandatory_for_embedded_moisture_route():
    case = _wet_case()
    case.pop("validation_reference_times_min")
    with pytest.raises(ValueError, match="12.6"):
        sp554_fire_thermal_guided_workflow(case)


def test_fire_d31_wet_embedded_properties_route_is_invalidated_by_12_6_when_deviation_exceeds_20_percent():
    case = _wet_case()
    case["validation_reference_times_min"] = [200.0]
    result = sp554_fire_thermal_guided_workflow(case)
    assert result["status"] == "INVALID_BY_12_6"
    assert result["actual_fire_resistance_min"] is None
    assert result["validation_12_6"]["result_valid"] is False
