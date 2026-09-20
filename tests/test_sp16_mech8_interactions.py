from __future__ import annotations
from pathlib import Path

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech6_gate import aggregate_sp16_mechanical_verification
from standard_core.sp16_mech8_interactions import bind_mech8_interaction_evidence

ROOT=Path(__file__).resolve().parents[1]


def _census(active):
    return {
        'schema':'sp16_mech2_applicability_census_v1',
        'active_checks':[{'id':cid,'family':'test','label':cid,'applicability':'applicable','runtime_status':'inherited_runtime','normative_scope':[]} for cid in active],
        'context_driven_checks':[],
    }


def _parent(active):
    return {'schema':'sp16_mech7_primary_evidence_v1','evidence':{cid:{'status':'DEFERRED','utilization':None,'pass':None,'evidence_source':'MECH7','evidence_scope':['SP16 §8']} for cid in active}}


def test_mech8_graph_identity_and_metadata():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md=app.model.graph['metadata']
    assert md['sp16_mech8_mq_interaction_layer_closed'] is True
    assert md['sp16_mech8_torsion_scope_reconciled'] is True
    assert md['sp16_mech8_universal_torsion_normative_check_closed'] is False


def test_class1_i_mx_qx_eq44_same_point_binding():
    values={
      'sp16_mech7_primary_evidence':_parent(['interaction_M_Q']),
      'sp16_applicability_census':_census(['interaction_M_Q']),
      'sp16_section_class':'1',
      'ambient_N_force':0.0,'ambient_M_x':50e6,'ambient_M_y':0.0,'ambient_Q_x':40e3,'ambient_Q_y':0.0,'ambient_T_torsion':0.0,'ambient_B_bimoment':0.0,
      'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
      'I_xn':80e6,'Ry_formula':250.0,'Rs_formula':145.0,'gamma_c_bending_strength':1.0,
      'sp16_mech8_eq44_no_transverse_local_stress':True,
      'ambient_axis_shear_state':{
        'clause_8_2_3_components':{'applicable':True,'web_hole_alpha45':1.0},
        'pointwise_recovery':{'points':[
          {'id':'p0','x_mm':0.0,'y_mm':0.0,'tau_x_n_mm2':30.0},
          {'id':'p1','x_mm':0.0,'y_mm':100.0,'tau_x_n_mm2':20.0},
          {'id':'flange','x_mm':60.0,'y_mm':144.0,'tau_x_n_mm2':1.0},
        ]},
      },
    }
    out=bind_mech8_interaction_evidence(values)['sp16_mech8_primary_evidence']['evidence']['interaction_M_Q']
    assert out['status']=='PASS'
    assert out['details']['same_point'] is True
    assert out['details']['checked_point_count']==2
    assert out['utilization']>0.0


def _class2_values(*, my=0.0, qy=0.0, b=0.0):
    return {
      'sp16_mech7_primary_evidence':_parent(['interaction_M_Q']),
      'sp16_applicability_census':_census(['interaction_M_Q']),
      'sp16_section_class':'2',
      'ambient_N_force':0.0,'ambient_M_x':50e6,'ambient_M_y':my,'ambient_Q_x':40e3,'ambient_Q_y':qy,'ambient_T_torsion':0.0,'ambient_B_bimoment':b,
      'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
      'ambient_axis_shear_state':{'clause_8_2_3_components':{'applicable':True,'tau_x_effective_n_mm2':40.0,'tau_y_n_mm2':10.0 if qy else 0.0,'A_w_mm2':2208.0,'A_f_one_flange_mm2':1800.0}},
      'Rs_formula':145.0,'fy_norm':250.0,'Ry_formula':245.0,'gamma_c_bending_strength':1.0,
      'W_xn_min':600000.0,'W_yn_min':180000.0,'W_omega_eff':1.0e8,
      'sp16_mech8_annex_e1_section_type':'1','sp16_mech8_equivalent_load_safety_factor':1.1,
      'sp16_mech8_required_clause_checks_confirmed':True,'sp16_mech8_is_support_section':False,
    }


def test_class2_eq50_beta_route_closes():
    out=bind_mech8_interaction_evidence(_class2_values())['sp16_mech8_primary_evidence']['evidence']['interaction_M_Q']
    assert out['status']=='PASS'
    assert 'Eq.(50)' in out['evidence_source']
    assert out['details']['beta']<=1.0


def test_class2_biaxial_eq51_route_closes_with_qy_gate():
    out=bind_mech8_interaction_evidence(_class2_values(my=10e6,qy=20e3))['sp16_mech8_primary_evidence']['evidence']['interaction_M_Q']
    assert out['status'] in {'PASS','FAIL'}
    assert 'Eq.(51)' in out['evidence_source']


def test_class2_bimoment_eq53_route_closes():
    values=_class2_values(b=1e9)
    out=bind_mech8_interaction_evidence(values)['sp16_mech8_primary_evidence']['evidence']['interaction_M_Q']
    assert out['status'] in {'PASS','FAIL'}
    assert 'Eq.(53)' in out['evidence_source']


def test_free_torsion_remains_normatively_deferred_but_scope_is_reconciled():
    values={
      'sp16_mech7_primary_evidence':_parent(['torsion_T']),
      'sp16_applicability_census':_census(['torsion_T']),
      'sp16_section_class':'1',
      'ambient_N_force':0.0,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_Q_x':0.0,'ambient_Q_y':0.0,'ambient_T_torsion':1e6,'ambient_B_bimoment':0.0,
      'ambient_torsion_runtime_closed':True,
    }
    result=bind_mech8_interaction_evidence(values)
    row=result['sp16_mech8_primary_evidence']['evidence']['torsion_T']
    assert row['status']=='DEFERRED'
    assert row['details']['scope_reconciled'] is True
    assert result['sp16_mech8_torsion_scope_reconciled'] is True


def test_mech6_gate_prefers_mech8_overlay():
    values=_class2_values()
    overlay=bind_mech8_interaction_evidence(values)
    values.update(overlay)
    out=aggregate_sp16_mechanical_verification(values)
    assert out['sp16_mechanical_gate_status']=='PASS'
    assert out['sp16_mechanical_pass'] is True
    row=out['sp16_mechanical_verification']['rows'][0]
    assert row['id']=='interaction_M_Q'
    assert row['status']=='PASS'
