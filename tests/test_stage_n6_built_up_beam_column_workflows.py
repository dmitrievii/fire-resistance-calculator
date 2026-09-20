import copy
import json
from pathlib import Path

import pytest

from standard_core import built_up_beam_column_workflows as n6w
from standard_core import built_up_beam_columns_and_combined_local_stability as scalar
from standard_core.runner import _prepare_case_for_validation, run_case

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'examples'/'built_up_beam_column_guided_example.json'


def _raw(): return json.loads(EXAMPLE.read_text(encoding='utf-8'))
def _prepared(raw=None):
    c,_,trace=_prepare_case_for_validation(raw or _raw(),ROOT)
    return c,trace


def test_n6_guided_example_complete_and_passes_exact_d4():
    w=run_case(EXAMPLE,ROOT)['results']
    assert w['status']=='COMPLETE'
    assert w['whole_member']['table8_selected_route']['equation']==15
    assert w['whole_member']['effective_relative_slenderness']==pytest.approx(1.5)
    assert w['whole_member']['relative_eccentricity_m_eq123']==pytest.approx(1.0)
    assert w['whole_member']['d4']['status']=='D4_EXACT_NODE'
    assert w['whole_member']['d4']['phi_e']==pytest.approx(0.454)
    assert w['branch']['additional_force']['value_n']==pytest.approx(75000.0)
    assert w['branch']['check']['status']=='EVALUATED_9.3.3_EQ7'
    assert w['local_stability']['web']['pass'] is True
    assert w['local_stability']['flange']['pass'] is True
    assert w['pass'] is True


def test_n6_material_hydration_uses_current_change6_values():
    _,trace=_prepared()
    v=trace['material']['resolved_values']
    assert v['normative_yield_resistance_n_mm2']==245.0
    assert v['design_yield_resistance_n_mm2']==240.0
    assert v['elastic_modulus_n_mm2']==206000.0


def test_n6_d4_non_node_is_fail_closed_without_hidden_interpolation():
    raw=_raw(); raw['whole_member']['free_axis_moment_n_mm']=33_000_000.0
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['whole_member']['d4']['status']=='EXTERNAL_D4_COEFFICIENT_REQUIRED'
    assert 'table_D4_phi_e' in w['required_unresolved']
    assert w['governing_utilization'] is None


def test_n6_external_d4_value_requires_provenance_and_cap():
    raw=_raw(); raw['whole_member']['free_axis_moment_n_mm']=33_000_000.0
    raw['stability']={'external_phi_e_d4':{'value':0.44,'basis':'engineer-approved D4 interpolation policy TEST'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['whole_member']['d4']['status']=='EXTERNAL_D4_COEFFICIENT_USED'
    assert w['whole_member']['d4']['phi_e']==pytest.approx(0.44)
    assert w['status']=='COMPLETE'


def test_n6_external_d4_cannot_exceed_central_phi():
    raw=_raw(); raw['whole_member']['free_axis_moment_n_mm']=33_000_000.0
    raw['stability']={'external_phi_e_d4':{'value':0.99,'basis':'invalid'}}
    c,_=_prepared(raw)
    with pytest.raises(ValueError,match='must satisfy'):
        n6w.built_up_beam_column_guided_workflow(c)


def test_n6_m_gt20_routes_whole_member_to_section8_fail_closed():
    raw=_raw(); raw['whole_member']['free_axis_moment_n_mm']=630_000_000.0
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['whole_member']['relative_eccentricity_m_eq123']>20
    assert w['whole_member']['d4']['status']=='SECTION_8_REQUIRED_M_GT_20'
    assert 'section_8_bending_member_check_for_m_gt_20' in w['required_unresolved']


def test_n6_type2_biaxial_uses_equation124_only_selected_branch():
    raw=_raw()
    raw['whole_member']['built_up_section_type']=2
    raw['whole_member']['table8_data']={
        'whole_member_max_slenderness':30.0,'total_area_mm2':10000.0,
        'diagonal_area_plane_1_mm2':1000.0,'diagonal_area_plane_2_mm2':1000.0,
        'diagonal_length_d1_mm':400.0,'diagonal_length_d2_mm':400.0,
        'branch_axis_spacing_b1_mm':400.0,'branch_axis_spacing_b2_mm':400.0,'panel_length_mm':1000.0
    }
    raw['moment_x_n_mm']=10_000_000.0; raw['moment_y_n_mm']=20_000_000.0
    raw['branch'].pop('spacing_b_mm',None); raw['branch']['spacing_b1_mm']=400.0; raw['branch']['spacing_b2_mm']=500.0
    # D4 may be non-node; explicit value isolates the branch-force routing under test.
    raw['stability']={'external_phi_e_d4':{'value':0.4,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['branch']['additional_force']['status']=='RESOLVED_EQ124'
    assert w['branch']['additional_force']['value_n']==pytest.approx(0.5*(20_000_000/400+10_000_000/500))


def test_n6_type3_biaxial_does_not_invent_combination_rule():
    raw=_raw(); raw['whole_member']['built_up_section_type']=3
    raw['whole_member']['table8_data']={
        'whole_member_max_slenderness':30.0,'total_area_mm2':10000.0,
        'diagonal_area_one_face_mm2':1000.0,'diagonal_length_d_mm':400.0,
        'branch_axis_spacing_b_mm':400.0,'panel_length_mm':1000.0
    }
    raw['moment_x_n_mm']=10_000_000.0; raw['moment_y_n_mm']=20_000_000.0
    raw['stability']={'external_phi_e_d4':{'value':0.4,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['branch']['additional_force']['status']=='EXTERNAL_BRANCH_FORCE_REQUIRED'
    assert 'branch_detailed_check' in w['required_unresolved']


def test_n6_type3_biaxial_accepts_only_explicit_external_branch_force_provenance():
    raw=_raw(); raw['whole_member']['built_up_section_type']=3
    raw['whole_member']['table8_data']={
        'whole_member_max_slenderness':30.0,'total_area_mm2':10000.0,
        'diagonal_area_one_face_mm2':1000.0,'diagonal_length_d_mm':400.0,
        'branch_axis_spacing_b_mm':400.0,'panel_length_mm':1000.0
    }
    raw['moment_x_n_mm']=10_000_000.0; raw['moment_y_n_mm']=20_000_000.0
    raw['branch']['external_additional_force_n']={'value':90000.0,'basis':'engineer-approved branch force resolution TEST'}
    raw['stability']={'external_phi_e_d4':{'value':0.4,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['branch']['additional_force']['status']=='EXTERNAL_BIAXIAL_TYPE3_FORCE_USED'
    assert w['branch']['additional_force']['value_n']==90000.0


def test_n6_connector_clause_9_3_7_uses_max_and_requires_lattice_when_actual_greater():
    w=run_case(EXAMPLE,ROOT)['results']
    assert w['connectors']['governing_source']=='actual'
    assert w['connectors']['governing_shear_force_n']==5000.0
    assert w['connectors']['lattice_required'] is True


def test_n6_less_than_six_panels_is_explicit_external_route():
    raw=_raw(); raw['whole_member']['panel_count']=5
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['route']=='LESS_THAN_SIX_PANELS'
    assert w['pass'] is None


def test_n6_table22_explicit_interpolation_rules_are_retained():
    # Note 1: m=0..1 and 10..20 are explicit linear interpolations in the current standard.
    low=scalar.table_22_type_1_limit(1.5,0.5,1.2,2.0)
    base=scalar.web_limit_eq125(1.5)
    assert low==pytest.approx((1.2+base)/2)
    high=scalar.table_22_type_1_limit(1.5,15.0,1.2,2.0)
    assert high==pytest.approx((base+2.0)/2)


def test_n6_table23_explicit_m5_to20_interpolation_is_retained():
    at5=scalar.table_23_limit(1,0.5,1.5,1.5,5.0,0.45)
    at20=scalar.table_23_limit(1,0.5,1.5,1.5,20.0,0.45)
    mid=scalar.table_23_limit(1,0.5,1.5,1.5,12.5,0.45)
    assert at20==pytest.approx(0.45)
    assert mid==pytest.approx((at5+at20)/2)


def test_n6_local_web_failure_triggers_reduced_area_fail_closed():
    raw=_raw(); raw['local_stability']['web']['effective_height_mm']=600.0; raw['local_stability']['web']['thickness_mm']=6.0
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    web=w['local_stability']['web']
    assert web['reduced_area_route']['reduced_area_required'] is True
    assert web['status']=='INCOMPLETE_FAIL_CLOSED'
    assert 'web_local_stability' in w['required_unresolved']
    assert w['pass'] is None


def test_n6_table23_edge_return_multiplier_only_when_explicitly_qualified():
    raw=_raw(); raw['local_stability']['flange']['edge_return_qualified']=True
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['local_stability']['flange']['limit']==pytest.approx(1.5*0.4745)


def test_n6_batten_route_does_not_fake_vierendeel_branch_check():
    raw=_raw(); raw['whole_member']['connector_system']='battens'
    # Type-1 equation (12), selected only.
    raw['whole_member']['table8_data']={
        'whole_member_slenderness_y':40.0,'branch_slenderness_1':10.0,
        'branch_inertia_axis_1_mm4':200000.0,'branch_axis_spacing_b_mm':400.0,
        'batten_inertia_mm4':200000.0,'batten_pitch_mm':400.0
    }
    raw['stability']={'external_phi_e_d4':{'value':0.4,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['branch']['check']['status']=='DETAILED_BRANCH_EQ109_LOCAL_BENDING_REQUIRED'
    assert w['pass'] is None


def test_n6_three_sided_equilateral_routes_to_section16_not_general_9_3():
    raw=_raw(); raw['member_topology']='three_sided_equilateral'
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['route']=='CLAUSE_9.3.5_SECTION_16_REQUIRED'
    assert w['pass'] is None


def test_n6_two_solid_branches_route_to_explicit_9_3_6_detailed_requirements():
    raw=_raw(); raw['member_topology']='two_solid_branches'
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['route']=='CLAUSE_9.3.6_DETAILED_TWO_SOLID_BRANCH_CHECK_REQUIRED'
    assert 'branch_eq109_eq111_and_effective_lengths' in w['required_unresolved']


def test_n6_battens_are_invalidated_when_actual_shear_exceeds_qfic():
    raw=_raw(); raw['whole_member']['connector_system']='battens'
    raw['whole_member']['table8_data']={
        'whole_member_slenderness_y':40.0,'branch_slenderness_1':10.0,
        'branch_inertia_axis_1_mm4':200000.0,'branch_axis_spacing_b_mm':400.0,
        'batten_inertia_mm4':200000.0,'batten_pitch_mm':400.0
    }
    raw['stability']={'external_phi_e_d4':{'value':0.4,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['connectors']['lattice_required'] is True
    assert 'clause_9.3.7_actual_shear_exceeds_qfic_lattice_required' in w['required_unresolved']


def test_n6_lattice_branch_eq7_uses_branch_own_stability_coefficient():
    raw=_raw(); raw['branch']['relative_slenderness']=1.2
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    branch=w['branch']['check']
    expected=n6w.axial.central_compression_stability_coefficient(1.2,raw['branch']['table7_section_type'])
    assert branch['status']=='EVALUATED_9.3.3_EQ7'
    assert branch['phi_branch']==pytest.approx(expected)
    assert branch['phi_source']=='clause_9.3.3_equation_7_with_clause_7.1.3_equation_8'


def test_n6_extended_lattice_branch_slenderness_fails_closed_without_7_2_5_whole_member_coupling():
    raw=_raw(); raw['branch']['relative_slenderness']=3.0
    # Keep the complete-member effective slenderness above the branch value so only the explicit 7.2.5 dependency governs.
    raw['whole_member']['table8_data']['whole_member_slenderness_y']=100.0
    raw['stability']={'external_phi_e_d4':{'value':0.25,'basis':'test-only external D4'}}
    c,_=_prepared(raw); w=n6w.built_up_beam_column_guided_workflow(c)
    assert w['branch']['check']['status']=='CLAUSE_7.2.5_WHOLE_MEMBER_COUPLING_REQUIRED'
    assert w['branch']['check']['pass'] is None
    assert 'branch_detailed_check' in w['required_unresolved']


def test_n6_transverse_stiffener_route_checks_spacing_outstand_and_thickness():
    raw=_raw()
    wcfg=raw['local_stability']['web']
    wcfg['section_type']=4
    wcfg['effective_height_mm']=600.0
    wcfg['thickness_mm']=6.0
    wcfg['flange_width_mm']=600.0
    raw['local_stability']['transverse_stiffener']={
        'arrangement':'paired_symmetric',
        'provided_outstand_mm':70.0,
        'provided_thickness_mm':5.0,
        'provided_spacing_mm':1600.0,
        'geometrically_nonlinear_design':False,
        'solid_branch_of_built_up_column':False,
    }
    c,_=_prepared(raw); result=n6w.built_up_beam_column_guided_workflow(c)
    st=result['local_stability']['web']['transverse_stiffener']
    assert st['required'] is True
    assert st['outstand_pass'] is True
    assert st['thickness_pass'] is True
    assert st['spacing_pass'] is True
    assert st['pass'] is True


def test_n6_transverse_stiffener_noncompliance_is_fail_closed():
    raw=_raw()
    wcfg=raw['local_stability']['web']
    wcfg['section_type']=4
    wcfg['effective_height_mm']=600.0
    wcfg['thickness_mm']=6.0
    wcfg['flange_width_mm']=600.0
    raw['local_stability']['transverse_stiffener']={
        'arrangement':'paired_symmetric',
        'provided_outstand_mm':50.0,
        'provided_thickness_mm':2.0,
        'provided_spacing_mm':2000.0,
        'geometrically_nonlinear_design':False,
        'solid_branch_of_built_up_column':False,
    }
    c,_=_prepared(raw); result=n6w.built_up_beam_column_guided_workflow(c)
    web=result['local_stability']['web']
    assert web['transverse_stiffener']['pass'] is False
    assert 'clause_9.4.4_transverse_stiffener_noncompliance' in web['required_unresolved']
    assert result['pass'] is None


def test_n6_longitudinal_stiffener_route_requires_inertia_half_web_and_7_3_4_confirmation():
    raw=_raw()
    raw['local_stability']['longitudinal_stiffener']={
        'provided_inertia_mm4':2_000_000.0,
        'most_loaded_half_web_table22_check':{'pass':True,'basis':'independent half-web Table 22 check TEST'},
        'clause_7_3_4_design_confirmation':{'confirmed':True,'basis':'clause 7.3.4 geometry/design confirmation TEST'},
    }
    c,_=_prepared(raw); result=n6w.built_up_beam_column_guided_workflow(c)
    lon=result['local_stability']['web']['longitudinal_stiffener']
    assert lon['inertia_pass'] is True
    assert lon['pass'] is True
    assert result['status']=='COMPLETE'


def test_n6_longitudinal_stiffener_missing_half_web_compliance_does_not_pass_silently():
    raw=_raw()
    raw['local_stability']['longitudinal_stiffener']={
        'provided_inertia_mm4':1_000_000.0,
        'most_loaded_half_web_table22_check':{'pass':False,'basis':'failed half-web Table 22 check TEST'},
        'clause_7_3_4_design_confirmation':{'confirmed':True,'basis':'clause 7.3.4 geometry/design confirmation TEST'},
    }
    c,_=_prepared(raw); result=n6w.built_up_beam_column_guided_workflow(c)
    assert result['local_stability']['web']['longitudinal_stiffener']['pass'] is False
    assert result['pass'] is None
