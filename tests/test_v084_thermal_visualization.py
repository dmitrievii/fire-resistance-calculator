from __future__ import annotations

import math

from standard_core.fire_sp554_thermal import sp554_fire_thermal_guided_workflow
from standard_core.fire_sp554_thermal_v084 import install_thermal_solver_patch
from standard_core.sp16_mech7_v084_thermal_visual_runtime import (
    STANDARD_REDUCED_THICKNESSES_MM,
    protected_fdm_visualization,
    unprotected_heating_diagram,
)
from streamlit_guided_ux_v084 import _default_payload_for_node

install_thermal_solver_patch()


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


def _production_fdm_case(initial_temperature_c: float = 20.0) -> dict:
    return {
        'thermal_route':'PROTECTED_FDM_12_5',
        'critical_temperature_c':550.0,
        'reduced_thickness_mm':10.0,
        'initial_temperature_c':initial_temperature_c,
        'time_step_min':0.0005,
        'max_time_min':180.0,
        'visualization_sample_interval_min':0.5,
        'protection_model':{
            'thickness_mm':20.0,
            'layer_count':4,
            'density_kg_m3':500.0,
            'conductivity_A_w_mk':0.2,
            'conductivity_B_w_mk2':0.0,
            'heat_capacity_C_j_kgk':1000.0,
            'heat_capacity_D_j_kgk2':0.0,
            'initial_moisture_percent':0.0,
        },
        'validation_reference_times_min':[100.0],
    }


def test_v084_fdm_charts_are_sampled_from_the_same_production_12_5_solver():
    case=_production_fdm_case()
    result=sp554_fire_thermal_guided_workflow(case)
    reference_case=dict(case)
    reference_case.pop('visualization_sample_interval_min')
    reference=sp554_fire_thermal_guided_workflow(reference_case)
    assert result['status']=='COMPLETE'
    assert math.isclose(result['calculated_time_min'],reference['calculated_time_min'],rel_tol=0.0,abs_tol=1e-12)
    assert result['visualization']['source']=='same_production_SP554_12_5_integration'

    vis=protected_fdm_visualization({'protection_12_5_calculation_trace':result})
    assert vis['schema']=='sp554_v084_fdm_visualization_v1'
    assert vis['layer_count']==4
    assert len(vis['profile_samples'])>=2 and len(vis['time_series'])>=2
    assert math.isclose(vis['time_series'][-1]['steel_temperature_c'],550.0,abs_tol=1e-7)
    assert math.isclose(vis['calculated_time_min'],result['calculated_time_min'],abs_tol=1e-12)
    assert math.isclose(vis['calculated_time_min'],vis['time_series'][-1]['time_min'],abs_tol=1e-12)


def test_v084_fdm_visualization_uses_the_selected_initial_temperature():
    result=sp554_fire_thermal_guided_workflow(_production_fdm_case(initial_temperature_c=25.0))
    vis=result['visualization']
    assert vis['initial_temperature_c']==25.0
    assert vis['time_series'][0]['fire_temperature_c']==25.0
    assert vis['time_series'][0]['steel_temperature_c']==25.0


def test_v084_visible_defaults_are_explicit_and_editable():
    assert _default_payload_for_node('SP554_D_JOINTS',None) is False
    assert _default_payload_for_node('GOST30247_I_INITIAL_FURNACE_TEMPERATURE',None)==20.0
    assert _default_payload_for_node('SP554_I_12_6_VALIDATION_EVIDENCE',None)=={
        'protection_12_6_max_deviation_pct':20.0,
        'protection_12_6_validation_evidence_complete':True,
    }
    # A previously saved or edited answer always wins over the default.
    assert _default_payload_for_node('SP554_D_JOINTS',True) is True
    assert _default_payload_for_node('GOST30247_I_INITIAL_FURNACE_TEMPERATURE',18.0)==18.0


def test_v084_method_selector_is_noninteractive_calculation_in_production_model():
    import sys, types
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        stub=types.ModuleType('streamlit'); stub.session_state={}; stub.rerun=lambda:None; stub.error=lambda *_:None
        sys.modules['streamlit']=stub
    import streamlit_app as ui
    app=ui._new_application()
    node=app.model.nodes['SP554_D_UNPROTECTED_METHOD']
    assert node['node_type']=='calculation'
    assert 'question' not in node and 'options' not in node
