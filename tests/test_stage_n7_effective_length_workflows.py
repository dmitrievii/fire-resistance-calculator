import copy
import json
import math
from pathlib import Path

import pytest

from standard_core import effective_length_workflows as n7w
from standard_core import effective_lengths_and_limiting_slenderness as s10
from standard_core.runner import run_case, _prepare_case_for_validation

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'examples'/'effective_length_guided_example.json'


def _raw(): return json.loads(EXAMPLE.read_text(encoding='utf-8'))
def _case(route, radius=None, limit=None):
    return {
        'case_id':'N7-TEST','standard':'СП 16.13330.2017','action':'effective_length_guided',
        'effective_length_route':route,
        'radius': radius or {'mode':'explicit','value_mm':20.0},
        'limiting_slenderness': limit or {'mode':'none','group_4_applies':False},
    }


def test_n7_example_uses_corrected_eq138_floor_and_table32():
    r=run_case(EXAMPLE,ROOT)['results']
    assert r['status']=='COMPLETE'
    assert r['effective_length']['effective_length_mm']==pytest.approx(600.0)
    assert r['actual_slenderness']==pytest.approx(30.0)
    assert r['limiting_slenderness']['alpha']==pytest.approx(0.5)
    assert r['limiting_slenderness']['limit']==pytest.approx(150.0)
    assert r['pass'] is True


def test_n7_atomic_eq138_lower_bound_is_0_6_l_current_sp16():
    assert s10.built_up_column_branch_effective_length_in_plane_eq138(1000,0)==pytest.approx(600.0)


def test_n7_atomic_eq139_lower_bound_is_0_5_l1_current_sp16():
    assert s10.built_up_column_branch_effective_length_out_of_plane_eq139(2000,2,0)==pytest.approx(1000.0)


def test_n7_eq141_uses_official_fcs_typo_correction():
    assert s10.sway_frame_mu_eq141(1.0)==pytest.approx(2.0*math.sqrt(1.38))
    assert s10.sway_frame_mu_eq141(1.0)!=pytest.approx(2.0+math.sqrt(1.38))


def test_n7_eq136_and_eq137_selected_routes():
    a=n7w.effective_length_guided_workflow(_case({'kind':'eq136_truss_chord_in_plane','segment_length_mm':1000,'adjacent_force_ratio_alpha':-0.55}))
    b=n7w.effective_length_guided_workflow(_case({'kind':'eq137_truss_chord_out_of_plane','braced_length_mm':2000,'section_count_k':3,'other_force_sum_ratio_beta':2}))
    assert a['effective_length']['effective_length_mm']>=800
    assert b['effective_length']['effective_length_mm']==pytest.approx(2000)


def test_n7_table24_route_and_single_angle_radius_selection():
    c=_case(
        {'kind':'table24_truss_member','table24_case':'single_angle_equal_restraint_distances','member_role':'chord','geometric_length_mm':1000},
        {'mode':'single_angle_10_1_4','node_spacing_mm':1000,'buckling_direction':'parallel_to_truss_plane','i_min_mm':10,'i_x_mm':20,'i_y_mm':25},
    )
    w=n7w.effective_length_guided_workflow(c)
    assert w['effective_length']['effective_length_mm']==pytest.approx(850)
    assert w['radius']['selector']=='i_min'
    assert w['actual_slenderness']==pytest.approx(85)


def test_n7_table25_cross_lattice_route():
    w=n7w.effective_length_guided_workflow(_case({'kind':'table25_cross_lattice','joint_case':'both_members_continuous','supporting_state':'inactive','node_to_intersection_length_mm':500,'full_member_length_mm':1200}))
    assert w['effective_length']['effective_length_mm']==pytest.approx(840)


def test_n7_table26_structural_route_selects_radius():
    c=_case(
        {'kind':'table26_structural_member','member_case':'single_angle_welded_or_two_bolts','geometric_length_mm':1000,'geometric_slenderness_l_over_i_min':100,'is_lattice_member':False,'is_beam_column':True,'bending_plane_relation':'perpendicular_axis_x'},
        {'mode':'selector_values','i_min_mm':8,'i_x_mm':30,'i_y_mm':15},
    )
    w=n7w.effective_length_guided_workflow(c)
    assert w['effective_length']['effective_length_mm']==pytest.approx(900)
    assert w['radius']['selector']=='i_x'
    assert w['actual_slenderness']==pytest.approx(30)


def test_n7_table27_29_route_retains_printed_n_interpolation():
    route={
        'kind':'table27_29_spatial_member','table27_row':'diagonal_15ad','force_state':'compression',
        'base_lengths_mm':{'ld':1000,'ld1':900},'chord_min_inertia_mm4':200,'diagonal_length_mm':1000,
        'diagonal_min_inertia_mm4':50,'chord_panel_length_mm':1000,'alternate_diagonal_length_mm':900,
        'table28_joint_case':'support_interrupted_fig15d','supporting_state':'inactive',
        'connection_case':'welded_or_two_bolts','geometric_slenderness_l_over_i_min':100,
        'gusset_configuration':'no_gusset_ends','out_of_plane_variant':False,
    }
    w=n7w.effective_length_guided_workflow(_case(route,{'mode':'selector_values','i_min_mm':25,'i_x_mm':20,'i_y_mm':15}))
    assert w['effective_length']['table28_n']==pytest.approx(3.0)  # raw 4 is clamped by Table 28 note
    assert 0.0<w['effective_length']['table29_adjusted_mu_d']<2.0
    assert w['effective_length']['effective_length_mm']>0


def test_n7_table30_column_route_eq140():
    w=n7w.effective_length_guided_workflow(_case({'kind':'table30_column','scheme_id':'scheme_3','column_length_mm':3000}))
    assert w['effective_length']['mu']==pytest.approx(.5)
    assert w['effective_length']['effective_length_mm']==pytest.approx(1500)


def test_n7_table31_eq141_route_is_corrected_and_complete():
    route={'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq141_sway_p0','n_parameter':1.0,'column_length_mm':3000}
    w=n7w.effective_length_guided_workflow(_case(route))
    expected=2*math.sqrt(1.38)
    assert w['effective_length']['mu']==pytest.approx(expected)
    assert w['effective_length']['effective_length_mm']==pytest.approx(3000*expected)
    assert 'Исх-8076' in w['effective_length']['mu_trace']['method']


def test_n7_table31_same_load_combination_is_fail_closed():
    route={'kind':'table31_frame_column','same_load_combination_confirmed':False,'mu_method':'eq141_sway_p0','n_parameter':1.0,'column_length_mm':3000}
    w=n7w.effective_length_guided_workflow(_case(route))
    assert w['status']=='INCOMPLETE_FAIL_CLOSED'
    assert w['effective_length']['effective_length_mm'] is None


def test_n7_table31_equations_142_143_144_145_are_selectable():
    routes=[
      {'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq142_sway_p_inf','n_parameter':0.0,'column_length_mm':3000},
      {'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq143_sway_n_le_0_2','p_parameter':1.0,'n_parameter':0.2,'column_length_mm':3000},
      {'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq144_sway_n_gt_0_2','p_parameter':1.0,'n_parameter':1.0,'column_length_mm':3000},
      {'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq145_nonsway','p_parameter':1.0,'n_parameter':1.0,'column_length_mm':3000},
    ]
    for r in routes:
        w=n7w.effective_length_guided_workflow(_case(r))
        assert w['status']=='COMPLETE'
        assert w['effective_length']['effective_length_mm']>0


def test_n7_eq146_requires_eq141_or_eq142_base_route():
    r={'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq145_nonsway','p_parameter':1.0,'n_parameter':1.0,'column_length_mm':3000,'apply_eq146_nonuniform_loading':True,'checked_column_inertia_mm4':100,'total_column_force_n':1000,'checked_column_force_n':500,'total_column_inertia_mm4':400}
    with pytest.raises(ValueError,match='Equation \\(146\\) requires'):
        n7w.effective_length_guided_workflow(_case(r))


def test_n7_eq146_applies_lower_bound_and_same_route():
    r={'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq141_sway_p0','n_parameter':1.0,'column_length_mm':3000,'apply_eq146_nonuniform_loading':True,'checked_column_inertia_mm4':100,'total_column_force_n':1000,'checked_column_force_n':500,'total_column_inertia_mm4':400}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert w['effective_length']['mu_trace']['equation_146_mu_eff']>=.7


def test_n7_eq147_deformation_reduction_selected_route():
    r={'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq141_sway_p0','n_parameter':1.0,'column_length_mm':3000,'apply_eq147_deformation_reduction':True,'relative_slenderness':2,'moment_n_mm':1000,'nonsway_reference_moment_n_mm':900,'area_mm2':100,'axial_force_n':100,'compressed_fibre_section_modulus_mm3':100}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert 0<w['effective_length']['equation_147']['psi']<=1


def test_n7_clause_10_3_5_h_over_b_trigger_is_fail_closed_until_confirmed():
    r={'kind':'table31_frame_column','same_load_combination_confirmed':True,'mu_method':'eq141_sway_p0','n_parameter':1.0,'column_length_mm':3000,'frame_total_height_mm':60000,'frame_width_mm':10000,'global_frame_stability_confirmed':False}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert w['status']=='INCOMPLETE_FAIL_CLOSED'
    assert w['effective_length']['global_frame_stability_required'] is True
    r['global_frame_stability_confirmed']=True
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='COMPLETE'


def test_n7_10_3_7_stepped_column_requires_external_provenance():
    r={'kind':'stepped_column_10_3_7_external'}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert w['status']=='INCOMPLETE_FAIL_CLOSED'
    r['external_effective_length']={'value_mm':2500,'basis':'Annex И engineer-approved calculation TEST'}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert w['status']=='COMPLETE' and w['effective_length']['effective_length_mm']==2500


def test_n7_10_3_9_restraint_spacing_or_external_analysis():
    a=n7w.effective_length_guided_workflow(_case({'kind':'out_of_plane_column_10_3_9','use_restraint_spacing':True,'restraint_spacing_mm':3000}))
    assert a['effective_length']['effective_length_mm']==3000
    b=n7w.effective_length_guided_workflow(_case({'kind':'out_of_plane_column_10_3_9','use_restraint_spacing':False,'external_effective_length':{'value_mm':2800,'basis':'analysis reflecting actual restraints TEST'}}))
    assert b['status']=='COMPLETE'


def test_n7_gallery_support_requires_whole_support_stability_confirmation():
    r={'kind':'gallery_support_10_3_10','direction':'transverse','support_height_mm':5000,'node_spacing_mm':2000,'mu':.7,'overall_built_up_cantilever_stability_confirmed':False}
    w=n7w.effective_length_guided_workflow(_case(r))
    assert w['status']=='INCOMPLETE_FAIL_CLOSED'
    assert w['effective_length']['effective_length_mm']==2000
    r['overall_built_up_cantilever_stability_confirmed']=True
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='COMPLETE'


def test_n7_certified_software_route_requires_all_10_3_11_assumptions():
    r={'kind':'certified_software_10_3_11','certified_software_confirmed':True,'elastic_steel_confirmed':True,'undeformed_scheme_confirmed':False,'external_effective_length':{'value_mm':2400,'basis':'certified solver TEST'}}
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='INCOMPLETE_FAIL_CLOSED'
    r['undeformed_scheme_confirmed']=True
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='COMPLETE'


def test_n7_external_crossing_brace_route_does_not_invent_formula():
    r={'kind':'crossing_brace_external_10_1_3'}
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='INCOMPLETE_FAIL_CLOSED'
    r['external_effective_length']={'value_mm':1700,'basis':'applicable steel-structure design rule TEST'}
    assert n7w.effective_length_guided_workflow(_case(r))['status']=='COMPLETE'


def test_n7_table32_group4_increase_and_same_stability_case():
    limit={'mode':'compressed_table32','group_4_applies':True,'same_stability_case_confirmed':True,'axial_force_n':0,'stability_coefficient_phi':.8,'gross_area_mm2':1000,'design_yield_resistance_n_mm2':240,'working_condition_factor':1,'table32_row':'1b'}
    w=n7w.effective_length_guided_workflow(_case({'kind':'table30_column','scheme_id':'scheme_3','column_length_mm':1000},{'mode':'explicit','value_mm':10},limit))
    assert w['limiting_slenderness']['limit']==pytest.approx(132)
    limit['same_stability_case_confirmed']=False
    assert n7w.effective_length_guided_workflow(_case({'kind':'table30_column','scheme_id':'scheme_3','column_length_mm':1000},{'mode':'explicit','value_mm':10},limit))['status']=='INCOMPLETE_FAIL_CLOSED'


def test_n7_table33_notes_prestressed_and_low_sag():
    base={'mode':'tension_table33','group_4_applies':False,'table33_row':'5','load_category':'static','low_self_weight_sag_for_row_5':True,'crane_modes_1k_to_6k_for_row_3':False,'prestressed_tension_member':False}
    w=n7w.effective_length_guided_workflow(_case({'kind':'table30_column','scheme_id':'scheme_1','column_length_mm':1000},{'mode':'explicit','value_mm':5},base))
    assert w['limiting_slenderness']['limit']==500
    base['prestressed_tension_member']=True
    w=n7w.effective_length_guided_workflow(_case({'kind':'table30_column','scheme_id':'scheme_1','column_length_mm':1000},{'mode':'explicit','value_mm':5},base))
    assert w['limiting_slenderness']['limit'] is None
    assert w['limiting_slenderness']['check']['unlimited'] is True


def test_n7_guided_schema_rejects_hidden_extra_fields():
    raw=_raw(); raw['effective_length_route']['hidden_default']=123
    with pytest.raises(ValueError,match='Unexpected property'):
        _prepare_case_for_validation(raw,ROOT)
