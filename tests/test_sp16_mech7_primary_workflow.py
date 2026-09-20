from __future__ import annotations
from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel
from standard_core.sp16_mech7_primary_workflow import bind_primary_ambient_evidence

ROOT=Path(__file__).resolve().parents[1]


def _census(active, contextual=()):
    return {
        'schema':'sp16_mech2_applicability_census_v1',
        'active_checks':[{'id':cid,'family':'test','label':cid,'applicability':'applicable','runtime_status':'inherited_runtime','normative_scope':[]} for cid in active],
        'context_driven_checks':[{'id':cid,'family':'test','label':cid,'applicability':'conditional_context','trigger':'test','runtime_status':'context_resolution_required','normative_scope':[]} for cid in contextual],
    }


def test_mech7_graph_identity_and_metadata():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md=app.model.graph['metadata']
    assert md['sp16_mech7_primary_binding_layer_closed'] is True
    assert md['sp16_mech7_all_n3_n10_primary_flow_bindings_closed'] is False
    assert md['sp16_mech7_engineering_use_ready'] is False


def test_primary_pure_shear_can_reach_strict_sp16_pass_after_context_classification():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id='SP16_I_AMBIENT_LOADS',registry=app.service.registry)
    p=SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)
    s.submit({'ambient_load_combination':{'schema':'test'},'ambient_N_force':0.0,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_Q_x':50e3,'ambient_Q_y':0.0,'ambient_T_torsion':0.0})
    for qid,value in {
      'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
      'A_gross':p.area_mm2,'J_x':p.ix_mm4,'J_y':p.iy_mm4,
      'Rs_formula':200.0,'gamma_c_bending_strength':1.0,'sp16_shear_hole_alpha45':1.0,
    }.items(): s._set_quantity(qid,value,node_id='TEST_SEED',source_kind='CALCULATED')
    assert s.current_node_id=='SP16_D_AMBIENT_BIMOMENT_REQUIRED'
    s.submit(False)
    assert s.current_node_id=='SP16_D_AMBIENT_CENSUS_CONFIRM'
    s.submit(True)
    assert s.current_node_id=='SP16_D_MECH7_FATIGUE_REQUIRED'
    s.submit(False)
    assert s.current_node_id=='SP16_D_MECH7_BRITTLE_REQUIRED'
    s.submit(False)
    # N==0 routes directly through the calculation binder and strict aggregator.
    assert s.current_node_id=='SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM'
    v=s.plain_values()
    assert v['sp16_mechanical_pass'] is True
    assert v['sp16_mechanical_gate_status']=='PASS'
    assert v['sp16_mech7_primary_evidence']['evidence']['fatigue']['status']=='N.A.'
    assert v['sp16_mech7_primary_evidence']['evidence']['brittle_fracture']['status']=='N.A.'


def test_tension_eq5_binding_requires_explicit_postyield_classification():
    values={
      'sp16_applicability_census':_census(['section_tension'],['fatigue','brittle_fracture']),
      'ambient_N_force':100e3,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_B_bimoment':0.0,
      'A_net':1000.0,'Ry_formula':250.0,'Ru_formula':360.0,'fy_norm':255.0,'gamma_u':1.3,
      'gamma_c_tension':1.0,'sp16_mech7_tension_post_yield_possible':False,
      'sp16_mech7_fatigue_required':False,'sp16_mech7_brittle_required':False,
    }
    out=bind_primary_ambient_evidence(values)['sp16_mech7_primary_evidence']['evidence']
    assert out['section_tension']['status']=='PASS'
    assert out['section_tension']['utilization']==0.4
    assert out['fatigue']['status']=='N.A.'
    assert out['brittle_fracture']['status']=='N.A.'


def test_compression_strength_stability_and_table32_slenderness_are_bound():
    values={
      'sp16_applicability_census':_census(['section_compression','member_compression_stability','effective_length_slenderness']),
      'ambient_N_force':-100e3,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_B_bimoment':0.0,
      'A_net':2000.0,'A_gross':2000.0,'Ry_formula':250.0,'Ru_formula':360.0,'fy_norm':255.0,'gamma_u':1.3,
      'gamma_c_compression':1.0,'phi_x_sp16':0.8,'phi_y_sp16':0.7,
      'sp16_lambda_x_geom':50.0,'sp16_lambda_y_geom':60.0,
      'sp16_mech7_table32_row':'3','sp16_mech7_group4_slenderness_increase':False,
    }
    ev=bind_primary_ambient_evidence(values)['sp16_mech7_primary_evidence']['evidence']
    assert ev['section_compression']['status']=='PASS'
    assert ev['member_compression_stability']['status']=='PASS'
    assert ev['effective_length_slenderness']['status']=='PASS'


def test_required_fatigue_without_n9_remains_fail_closed_and_mq_is_not_fabricated():
    values={
      'sp16_applicability_census':_census(['interaction_M_Q'],['fatigue']),
      'ambient_N_force':0.0,'ambient_M_x':10.0,'ambient_M_y':0.0,'ambient_B_bimoment':0.0,
      'sp16_mech7_fatigue_required':True,
    }
    ev=bind_primary_ambient_evidence(values)['sp16_mech7_primary_evidence']['evidence']
    assert ev['interaction_M_Q']['status']=='DEFERRED'
    assert ev['fatigue']['status']=='DEFERRED'

def test_central_compression_i_section_local_stability_is_bound_with_explicit_table_groups():
    values={
      'sp16_applicability_census':_census([],['local_stability_web','local_stability_flange']),
      'ambient_N_force':-100e3,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_B_bimoment':0.0,
      'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
      'Ry_formula':250.0,'E_norm':206000.0,'lambda_bar_x':1.0,'lambda_bar_y':1.2,
      'sp16_mech7_table9_group':'group_1_i_section','sp16_mech7_table10_group':'group_1','sp16_mech7_flange_edge_stiffened':False,
    }
    ev=bind_primary_ambient_evidence(values)['sp16_mech7_primary_evidence']['evidence']
    assert ev['local_stability_web']['status'] in {'PASS','FAIL'}
    assert ev['local_stability_flange']['status'] in {'PASS','FAIL'}
    assert ev['local_stability_web']['utilization'] is not None
    assert ev['local_stability_flange']['utilization'] is not None
