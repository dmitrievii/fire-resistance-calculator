import math
import pytest
from standard_core import effective_lengths_and_limiting_slenderness as el

def test_catalogs():
    for i in range(24,34):
        assert getattr(el,f"table_{i}_catalog")()

def test_equations_136_to_140():
    assert el.truss_chord_effective_length_in_plane_eq136(1000,1)==pytest.approx(1000)
    assert el.truss_chord_effective_length_in_plane_eq136(1000,-0.55)>=800
    assert el.truss_chord_effective_length_out_of_plane_eq137(2000,3,2)==pytest.approx(2000)
    assert el.built_up_column_branch_effective_length_in_plane_eq138(1000,1)==pytest.approx(math.sqrt(.95)*1000)
    assert el.built_up_column_branch_effective_length_out_of_plane_eq139(2000,2,1)>=1020
    assert el.column_effective_length_eq140(3000,.7)==2100

def test_table_24_and_25():
    assert el.table_24_effective_length('in_plane_general','other_web',1000)==800
    assert el.table_24_effective_length('out_of_plane_butt_web','other_web',1000,2000)==1800
    assert el.table_25_cross_lattice_effective_length('both_members_continuous','inactive',500,1200)==840

def test_radius_selection():
    assert el.single_angle_radius_selection_clause_10_1_4(850,1000,'parallel_to_truss_plane')=='i_min'
    assert el.single_angle_radius_selection_clause_10_1_4(800,1000,'parallel_to_truss_plane')=='i_y'
    assert el.structural_member_radius_selection_clause_10_2_2(False,'parallel_axis_y')=='i_min'

def test_table_26():
    assert el.table_26_structural_member_effective_length('continuous_or_butt_node',1000)==850
    assert el.table_26_structural_member_effective_length('single_angle_welded_or_two_bolts',1000,100)==900
    with pytest.raises(ValueError): el.table_26_structural_member_effective_length('single_angle_welded_or_two_bolts',1000,130,False)

def test_tables_27_to_29():
    r=el.table_27_spatial_member_properties('chord_15gd','compression',{'lm':1000})
    assert r['effective_length']==730 and r['radius_selector']=='i_min'
    n=el.table_28_n_parameter(100,1000,50,1000); assert n==2
    assert el.table_28_intersection_conditional_length('support_interrupted_fig15d','tension',1000,800,n)==1450
    assert el.table_29_diagonal_length_factor('welded_or_two_bolts',2,100)==pytest.approx(.9)
    low=el.table_29_diagonal_length_factor('welded_or_two_bolts',2,100)
    high=el.table_29_diagonal_length_factor('welded_or_two_bolts',7,100)
    mid=el.table_29_diagonal_length_factor('welded_or_two_bolts',4,100)
    assert mid==pytest.approx((low+high)/2)
    assert el.table_29_end_connection_adjustment(.8,'one_gusset_end')==.9

def test_table_30_and_frame_ratios():
    assert el.table_30_effective_length_factor('scheme_3')==.5
    assert el.frame_stiffness_ratio(100,3000,200,6000)==.25
    p=el.table_31_multistory_parameters('sway','top',2,1,2,3,4)
    assert p==pytest.approx({'p':2,'n':28/3})

def test_equations_141_to_145():
    assert el.sway_frame_mu_eq141(1)==pytest.approx(2*math.sqrt(1.38))
    assert el.sway_frame_mu_eq142(1)==pytest.approx(math.sqrt(1.56/1.14))
    assert el.sway_frame_mu_eq143(1,.2)>0
    assert el.sway_frame_mu_eq144(1,1)>0
    assert el.nonsway_frame_mu_eq145(1,1)<1

def test_table_31_special_cases():
    assert el.table_31_special_case_mu('sway_p0_n_0_03_to_0_2',.1)==pytest.approx(2.15*math.sqrt(.32/.1))
    assert el.table_31_special_case_mu('nonsway_p0',1)==pytest.approx(math.sqrt(1.46/1.93))

def test_equations_146_and_147():
    assert el.nonuniform_sway_frame_effective_length_eq146(2,100,1000,500,400)==pytest.approx(2*math.sqrt(.5))
    b=el.frame_deformation_reduction_factor_eq147(2,1000,900,100,100,100)
    assert 0<b['psi']<=1

def test_out_of_plane_and_gallery():
    assert el.out_of_plane_column_effective_length_clause_10_3_9(3000)==3000
    assert el.gallery_support_branch_effective_length_clause_10_3_10('longitudinal',5000,2000,.7)==3500
    assert el.gallery_support_branch_effective_length_clause_10_3_10('transverse',5000,2000,.7)==2000

def test_tables_32_and_33():
    assert el.compressed_limit_alpha(0,.8,1000,355,1)==.5
    assert el.table_32_compressed_limiting_slenderness('1a',.5)==150
    assert el.table_32_compressed_limiting_slenderness('1b',.5,True)==pytest.approx(132)
    assert el.table_33_tension_limiting_slenderness('5','static',low_self_weight_sag_for_row_5=True)==500
    assert el.table_33_tension_limiting_slenderness('3','crane_or_rail',crane_modes_1k_to_6k_for_row_3=True)==200
    assert el.table_33_tension_limiting_slenderness('1','static',prestressed_tension_member=True) is None

def test_slenderness_check():
    assert el.actual_slenderness(3000,20)==150
    assert el.slenderness_check(150,180)['pass']
    assert el.slenderness_check(999,None)['unlimited']

def test_invalid_domains():
    with pytest.raises(ValueError): el.truss_chord_effective_length_in_plane_eq136(1,-1)
    with pytest.raises(ValueError): el.sway_frame_mu_eq143(1,.3)
    with pytest.raises(ValueError): el.table_33_tension_limiting_slenderness('3','static')
