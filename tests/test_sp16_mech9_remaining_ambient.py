from __future__ import annotations
from pathlib import Path

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui16_declarative import condition_value
from standard_core.sp16_mech6_gate import aggregate_sp16_mechanical_verification
from standard_core.sp16_mech9_remaining_ambient import bind_mech9_remaining_ambient_evidence

ROOT=Path(__file__).resolve().parents[1]


def _census(active=(), context=()):
    return {
        'schema':'sp16_mech2_applicability_census_v1',
        'active_checks':[{'id':cid,'family':'test','label':cid,'applicability':'applicable','runtime_status':'inherited_runtime','normative_scope':[]} for cid in active],
        'context_driven_checks':[{'id':cid,'family':'test','label':cid,'applicability':'context_dependent','runtime_status':'context_required','normative_scope':[]} for cid in context],
    }


def _parent(active=(), context=()):
    ids=list(active)+list(context)
    return {
      'schema':'sp16_mech8_primary_evidence_v1',
      'evidence':{cid:{'status':'DEFERRED','utilization':None,'pass':None,'evidence_source':'MECH8','evidence_scope':['SP16']} for cid in ids},
    }


def test_mech9_graph_identity_and_metadata():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md=app.model.graph['metadata']
    assert md['sp16_mech9_class3_mq_one_plane_closed'] is True
    assert md['sp16_mech9_n9_ordinary_primary_auto_execution_closed'] is True
    assert md['sp16_mech9_n10_section13_primary_auto_execution_closed'] is True
    assert md['sp16_mech9_universal_torsion_normative_check_closed'] is False


def _class3_values():
    return {
      'sp16_mech8_primary_evidence':_parent(['interaction_M_Q']),
      'sp16_applicability_census':_census(['interaction_M_Q']),
      'sp16_section_class':'3',
      'ambient_N_force':0.0,'ambient_M_x':50e6,'ambient_M_y':0.0,'ambient_Q_x':40e3,'ambient_Q_y':0.0,'ambient_T_torsion':0.0,'ambient_B_bimoment':0.0,
      'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
      'ambient_axis_shear_state':{'clause_8_2_3_components':{'applicable':True,'tau_x_effective_n_mm2':40.0,'tau_y_n_mm2':0.0,'A_w_mm2':2208.0,'A_f_one_flange_mm2':1800.0}},
      'Rs_formula':145.0,'fy_norm':250.0,'Ry_formula':245.0,'gamma_c_bending_strength':1.0,
      'W_xn_min':600000.0,
      'sp16_mech8_annex_e1_section_type':'1','sp16_mech8_equivalent_load_safety_factor':1.1,'sp16_mech8_is_support_section':False,
      'sp16_mech7_fatigue_required':False,'sp16_mech7_brittle_required':False,
      'sp16_mech9_c3_clause_8_2_5_confirmed':True,
      'sp16_mech9_c3_clause_8_4_6_confirmed':True,
      'sp16_mech9_c3_clause_8_5_8_confirmed':True,
      'sp16_mech9_c3_clause_8_5_9_confirmed':True,
      'sp16_mech9_c3_clause_8_5_18_confirmed':True,
      'sp16_mech9_c3_max_moment_shear_effect_confirmed':True,
    }


def test_class3_one_plane_mq_closes_with_explicit_827_confirmations():
    out=bind_mech9_remaining_ambient_evidence(_class3_values())
    row=out['sp16_mech9_primary_evidence']['evidence']['interaction_M_Q']
    assert row['status'] in {'PASS','FAIL'}
    assert '8.2.7' in row['evidence_source']
    assert row['details']['class_3_route']['permitted'] is True
    assert out['sp16_mech9_class3_mq_binding_complete'] is True


def test_class3_missing_confirmation_stays_deferred():
    values=_class3_values()
    values['sp16_mech9_c3_clause_8_5_9_confirmed']=False
    row=bind_mech9_remaining_ambient_evidence(values)['sp16_mech9_primary_evidence']['evidence']['interaction_M_Q']
    assert row['status']=='DEFERRED'
    assert '8.5.9' in row['details']['missing_confirmations']


def test_ordinary_fatigue_auto_execution_closes_n9_evidence():
    values={
      'sp16_mech8_primary_evidence':_parent(context=['fatigue']),
      'sp16_applicability_census':_census(context=['fatigue']),
      'sp16_section_class':'1',
      'ambient_N_force':0.0,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_Q_x':0.0,'ambient_Q_y':0.0,'ambient_T_torsion':0.0,'ambient_B_bimoment':0.0,
      'sp16_mech7_fatigue_required':True,'sp16_mech7_brittle_required':False,
      'sp16_mech9_fatigue_route_kind':'ordinary_fatigue_12_1_2',
      'sp16_mech9_fatigue_load_cycles':1_000_000.0,
      'sp16_mech9_fatigue_resonant_vortex_excitation':False,
      'sp16_mech9_fatigue_sp20_load_basis_confirmed':True,
      'sp16_mech9_fatigue_net_stress_basis_confirmed':True,
      'sp16_mech9_fatigue_same_loading_extremes_confirmed':True,
      'sp16_mech9_fatigue_annex_k_case_confirmed':True,
      'sp16_mech9_fatigue_annex_k_case_id':'K1-16-TRANSVERSE_WELD_SMOOTH',
      'sp16_mech9_fatigue_sigma_max':50.0,
      'sp16_mech9_fatigue_sigma_min':-25.0,
      'fu_norm':440.0,'Ru_formula':400.0,'gamma_u':1.3,
    }
    out=bind_mech9_remaining_ambient_evidence(values)
    row=out['sp16_mech9_primary_evidence']['evidence']['fatigue']
    assert row['status']=='PASS'
    assert row['details']['n9_result']['status']=='COMPLETE'
    assert out['sp16_mech9_n9_primary_execution_complete'] is True


def test_crane_fatigue_remains_explicit_fail_closed_boundary():
    values={
      'sp16_mech8_primary_evidence':_parent(context=['fatigue']),
      'sp16_applicability_census':_census(context=['fatigue']),
      'sp16_section_class':'1',
      'ambient_N_force':0.0,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_Q_x':0.0,'ambient_Q_y':0.0,'ambient_T_torsion':0.0,'ambient_B_bimoment':0.0,
      'sp16_mech7_fatigue_required':True,'sp16_mech7_brittle_required':False,
      'sp16_mech9_fatigue_route_kind':'crane_runway_12_2',
    }
    row=bind_mech9_remaining_ambient_evidence(values)['sp16_mech9_primary_evidence']['evidence']['fatigue']
    assert row['status']=='DEFERRED'
    assert 'crane' in row['reason'].lower()


def test_section13_non_lamellar_auto_execution_closes_n10_evidence():
    values={
      'sp16_mech8_primary_evidence':_parent(context=['brittle_fracture']),
      'sp16_applicability_census':_census(context=['brittle_fracture']),
      'sp16_section_class':'1',
      'ambient_N_force':0.0,'ambient_M_x':0.0,'ambient_M_y':0.0,'ambient_Q_x':0.0,'ambient_Q_y':0.0,'ambient_T_torsion':0.0,'ambient_B_bimoment':0.0,
      'sp16_mech7_fatigue_required':False,'sp16_mech7_brittle_required':True,
      'Ry_formula':240.0,'governing_product_thickness_mm':20.0,
      'sp16_mech9_brittle_welded_structure':False,
      'sp16_mech9_brittle_steel_selection_confirmed':True,
      'sp16_mech9_brittle_stress_concentration_confirmed':True,
      'sp16_mech9_brittle_solid_web_lattice_considered':True,
      'sp16_mech9_brittle_cover_plate_flank_welds':False,
      'sp16_mech9_brittle_guillotine_or_punched':False,
      'sp16_mech9_brittle_secondary_gusset':False,
      'sp16_mech9_brittle_steel_grade_number':235.0,
      'sp16_mech9_brittle_joint_type':'other_welded',
      'sp16_mech9_brittle_through_thickness_tension':False,
      'sp16_mech9_brittle_13_3_review_confirmed':True,
      'sp16_mech9_brittle_lamellar_required':False,
    }
    out=bind_mech9_remaining_ambient_evidence(values)
    row=out['sp16_mech9_primary_evidence']['evidence']['brittle_fracture']
    assert row['status']=='PASS'
    assert row['details']['n10_result']['status']=='COMPLETE'
    assert out['sp16_mech9_n10_primary_execution_complete'] is True


def test_mech6_gate_prefers_mech9_overlay():
    values=_class3_values()
    values.update(bind_mech9_remaining_ambient_evidence(values))
    out=aggregate_sp16_mechanical_verification(values)
    assert out['sp16_mechanical_gate_status'] in {'PASS','FAIL'}
    row=out['sp16_mechanical_verification']['rows'][0]
    assert row['id']=='interaction_M_Q'
    assert row['status'] in {'PASS','FAIL'}


def test_class3_branch_is_exclusive_for_zero_minor_components():
    app=FireUI1Application.from_package_root(ROOT)
    edges={e['id']:e for e in app.model.graph['edges']}
    values={
      'ambient_M_x':50e6,'ambient_M_y':0.0,
      'ambient_Q_x':40e3,'ambient_Q_y':0.0,
      'sp16_section_class':'3',
      'sp16_mech7_fatigue_required':False,
      'sp16_mech7_brittle_required':False,
    }
    assert condition_value(edges['MECH9_E_MECH8_TO_C3']['condition'],values) is True
    assert condition_value(edges['MECH9_E_MECH8_TO_CALC_NONE']['condition'],values) is False
