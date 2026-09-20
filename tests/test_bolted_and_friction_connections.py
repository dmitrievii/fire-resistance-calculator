import math
import pytest
from standard_core import bolted_and_friction_connections as b

def test_table40_holes_and_distances():
    assert b.table_40_hole_diameter(20,"A",clearance_mm=0)==20
    assert b.table_40_hole_diameter(20,"B",clearance_mm=2)==22
    r=b.table_40_distance_requirements(22,12,355,edge_type="cut",stress_state="tension",row_location="middle_or_edge_with_angles")
    assert r["minimum_center_spacing_mm"]==55
    assert r["maximum_center_spacing_mm"]==min(16*22,24*12)
    assert b.table_40_check_layout(60,50,40,r)["pass"]

def test_table40_boundaries_and_errors():
    assert b.table_40_distance_requirements(22,12,540,row_location="edge_without_angles")["minimum_center_spacing_mm"]==66
    assert b.table_40_distance_requirements(22,12,400,friction_connection=True,friction_planes=1)["minimum_center_spacing_mm"]==66
    with pytest.raises(ValueError): b.table_40_hole_diameter(20,"B")

def test_table41_values_and_interpolation():
    assert b.table_41_connection_factor("A",multi_bolt=True)==1
    assert b.table_41_connection_factor("B",multi_bolt=True)==.9
    assert b.table_41_connection_factor("B",multi_bolt=True,bearing_geometry="a_1_5d_s_2d")==pytest.approx(.72)
    assert b.table_41_connection_factor("A",multi_bolt=True,bearing_geometry="intermediate",interpolation_fraction=.5)==pytest.approx(.9)

def test_equations_186_to_188():
    assert b.bolt_shear_capacity_eq186(240,245,2,.9,1)==pytest.approx(105840)
    assert b.bolt_bearing_capacity_eq187(450,20,24,.9,1)==pytest.approx(194400)
    assert b.bolt_tension_capacity_eq188(360,190,1)==pytest.approx(68400)

def test_equation_189_and_long_joint():
    beta=b.long_joint_reduction_factor_14_2_10(440,22)
    assert beta==pytest.approx(.98)
    result=b.required_bolt_count_eq189(300000,105840,194400,68400,applicable_modes=["shear","bearing"],long_joint_reduction_factor=beta)
    assert result["governing_mode"]=="shear"
    assert result["required_bolts"]==3

def test_bolt_group_distribution_equilibrium():
    r=b.bolt_group_force_distribution_14_2_11_12([[-50,-40],[50,-40],[-50,40],[50,40]],100000,0,5000000)
    assert sum(x["force_x_n"] for x in r["bolt_forces"])==pytest.approx(100000)
    assert sum(x["force_y_n"] for x in r["bolt_forces"])==pytest.approx(0)
    assert r["maximum_resultant_n"]>25000

def test_equation_190():
    expected=math.sqrt((40000/105840)**2+(30000/68400)**2)
    assert b.bolt_shear_tension_interaction_eq190(40000,30000,105840,68400)==pytest.approx(expected)
    assert b.bolt_shear_tension_interaction_eq190(0,0,105840,68400)==0

def test_count_adjustment():
    assert b.bolt_count_detailing_adjustment_14_2_14(10,"packing_or_single_cover_plate")["adjusted_bolt_count"]==11
    assert b.bolt_count_detailing_adjustment_14_2_14(50,"packing_or_single_cover_plate")["adjusted_bolt_count"]==55
    assert b.bolt_count_detailing_adjustment_14_2_14(100,"packing_or_single_cover_plate")["adjusted_bolt_count"]==110
    assert b.bolt_count_detailing_adjustment_14_2_14(10,"angle_or_channel_short_piece")["adjusted_bolt_count"]==15

def test_table40_staggered_longitudinal_minimum_is_enforced():
    req=b.table_40_distance_requirements(20,13,235,edge_type="cut",stress_state="tension",transverse_row_spacing_mm=140)
    assert req["minimum_staggered_longitudinal_spacing_mm"]==170
    bad_req=dict(req,staggered_layout=True,actual_staggered_longitudinal_spacing_mm=100)
    bad=b.table_40_check_layout(120,60,80,bad_req)
    assert bad["checks"]["staggered_longitudinal_min"] is False
    assert bad["pass"] is False
    good_req=dict(req,staggered_layout=True,actual_staggered_longitudinal_spacing_mm=170)
    good=b.table_40_check_layout(120,60,80,good_req)
    assert good["pass"] is True

def test_table42_values_and_routes():
    p=b.table_42_friction_parameters("shot_blast_no_preservation","torque","dynamic",3)
    assert p["friction_coefficient"]==.58 and p["gamma_h"]==1.35
    p=b.table_42_friction_parameters("steel_brushed_no_preservation","nut_rotation","static",2)
    assert p["gamma_h"]==pytest.approx(1.17*.9)
    with pytest.raises(ValueError): b.table_42_friction_parameters("untreated","torque","dynamic",2)

def test_equations_191_and_192():
    q=b.friction_plane_capacity_eq191(360,190,.58,1.35)
    assert q==pytest.approx(360*190*.58/1.35)
    r=b.required_friction_bolt_count_eq192(200000,q,2,1)
    assert r["required_bolts"]==5 and r["connection_factor_gamma_b"]==.9

def test_friction_tension_diameter_washer_area():
    red=b.friction_tension_reduction_14_3_6(.9,10000,360,190)
    assert red["bolt_pretension_n"]==68400
    assert red["adjusted_connection_factor_gamma_b"]<.9
    assert b.friction_bolt_diameter_check_14_3_7(60,20)["pass"]
    assert not b.friction_bolt_diameter_check_14_3_7(81,20)["pass"]
    assert b.friction_connection_washer_requirement_14_3_10(4,510,enlarged_head_and_nut=True)["one_washer_under_nut_permitted"]
    assert b.friction_connection_effective_area_14_3_11(1000,800,"static")["selected_area_mm2"]==pytest.approx(944)
    assert b.friction_connection_effective_area_14_3_11(1000,900,"static")["area_type"]=="gross"
    assert b.friction_connection_effective_area_14_3_11(1000,900,"dynamic")["area_type"]=="net"

def test_catalogs_and_external_routes():
    assert b.table_40_catalog()["table"]=="40"
    assert b.table_41_catalog()["table"]=="41"
    assert b.table_42_catalog()["table"]=="42"
    assert "SP 43.13330" in b.bolted_and_friction_external_requirements()["anchor_bolts"]
