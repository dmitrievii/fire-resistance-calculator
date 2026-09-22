from __future__ import annotations

import math

from standard_core.sp16_mech7_v084_thermal_visual_runtime import (
    STANDARD_REDUCED_THICKNESSES_MM,
    unprotected_heating_diagram,
)


def test_v084_unprotected_diagram_uses_standard_nodes_actual_curve_iso_and_crossing():
    data=unprotected_heating_diagram({
        'delta_pr':7.5,
        'critical_temperature_c':500.0,
        'sp554_dt_unprotected_min':0.1,
        'sp554_steel_density_12_2':7850.0,
        'sp554_steel_c0_12_2':480.0,
        'sp554_steel_c_temp_coeff_12_2':0.00063,
        'sp554_eps_reduced_12_4':0.5,
    },initial_temperature_c=20.0)
    assert tuple(data['standard_reduced_thicknesses_mm'])==STANDARD_REDUCED_THICKNESSES_MM
    assert data['actual_reduced_thickness_mm']==7.5
    assert data['actual_crossing_time_min'] is not None and data['actual_crossing_time_min']>0
    assert any(r['series']=='ISO 834 / ГОСТ 30247.0' for r in data['fire_series'])
    assert any(r['kind']=='actual' for r in data['steel_series'])
    assert {r['thickness_mm'] for r in data['steel_series'] if r['kind']=='standard'}==set(STANDARD_REDUCED_THICKNESSES_MM)


def test_v084_fdm_visualization_reaches_critical_temperature_and_has_both_chart_families():
    from standard_core.sp16_mech7_v084_thermal_visual_runtime import protected_fdm_visualization
    vis=protected_fdm_visualization({
        'critical_temperature_c':500.0,'delta_pr_protected':10.0,'protection_thickness_mm':5.0,
        'protection_12_5_model_parameters':{
            'density_kg_m3':100.0,'conductivity_A_w_mk':0.04,'conductivity_B_w_mk2':0.0,
            'heat_capacity_C_j_kgk':1000.0,'heat_capacity_D_j_kgk2':0.0,'temperature_basis':'degC','surface_emissivity':0.625,
        }
    })
    assert vis['schema']=='sp554_v084_fdm_visualization_v1'
    assert len(vis['profile_samples'])>=2 and len(vis['time_series'])>=2
    assert math.isclose(vis['time_series'][-1]['steel_temperature_c'],500.0,abs_tol=1e-7)
    assert math.isclose(vis['calculated_time_min'],vis['time_series'][-1]['time_min'],abs_tol=1e-10)
