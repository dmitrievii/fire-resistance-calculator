import math
import pytest

from standard_core import brittle_fracture_and_welded_connections as m


def test_table37_catalog_and_values():
    data=m.table_37_catalog()
    assert data["quality_group_thresholds_percent"]=={"Z15":15.0,"Z25":25.0,"Z35":35.0}
    assert m.table_37_connection_form_factor("no_z_direction_stress")==-25.0
    assert m.table_37_connection_form_factor("corner_full_penetration")==8.0


def test_table37_factor_formulas_and_technology():
    assert m.table_37_plate_thickness_factor(25)==5.0
    assert m.table_37_weld_leg_factor(10)==3.0
    assert m.table_37_restraint_factor("high_rigid_no_shrinkage")==5.0
    assert m.table_37_welding_technology_factor("multiple","alternating_sides","with_preheat")==-12.0


def test_table37_invalid_lookup_and_sign_boundary():
    with pytest.raises(KeyError): m.table_37_connection_form_factor("unknown")
    with pytest.raises(ValueError): m.table_37_plate_thickness_factor(-1)
    assert m.table_37_plate_thickness_factor(0)==0.0


def test_equation174_normal_zero_and_signed_sum():
    assert m.lamellar_tearing_risk_sum_eq174(3,5,2,3,-4)==9.0
    assert m.lamellar_tearing_risk_sum_eq174(0,0,0,0,0)==0.0
    assert m.lamellar_tearing_risk_sum_eq174(-25,4,3,0,-2)==-20.0


def test_lamellar_risk_modifier_and_check():
    assert m.lamellar_tearing_adjusted_risk_clause_13_5(20,"static_compression")==10.0
    assert m.lamellar_tearing_adjusted_risk_clause_13_5(20,"dynamic_or_vibratory")==22.0
    assert m.lamellar_tearing_adjusted_risk_clause_13_5(20,"none")==20.0
    result=m.lamellar_tearing_check_clause_13_5(15,"Z15")
    assert result["pass"] and result["utilization"]==1.0


def test_lamellar_quality_group_and_applicability():
    assert m.required_z_quality_group_clause_13_5(1,"KS-3",False) in {"Z15","Z25","Z35"}
    result=m.lamellar_tearing_applicability_clause_13_3(355,30,"tee",True)
    assert result["risk_assessment_required"]
    with pytest.raises(ValueError): m.required_z_quality_group_clause_13_5(9,"KS-3")


def test_brittle_factor_register():
    factors=m.brittle_fracture_factor_register_clause_13_1()
    assert "low_temperature" in factors and "stress_concentration" in factors


def test_through_thickness_test_route():
    assert m.through_thickness_property_test_route_clause_13_4(False)["status"]=="external_reference_required"
    assert m.through_thickness_property_test_route_clause_13_4(True)["status"]=="evidence_available"
    with pytest.raises(TypeError): m.through_thickness_property_test_route_clause_13_4(1)


def test_brittle_prevention_and_welded_detailing_checklists():
    assert m.brittle_fracture_prevention_checklist_clause_13_1_13_2({"steel":True,"detail":True})["pass"]
    failed=m.welded_connection_detailing_checklist_clause_14_1_1_14_1_6({"weld_type":True,"access":False})
    assert not failed["passed"] and failed["failed_checks"]==["access"]


def test_table38_existence_lookup_and_consistency():
    data=m.table_38_catalog()
    assert len(data["thicker_element_bins_mm"])==6
    assert m.minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner",12,8,355)["minimum_weld_leg_mm"]==6.0
    assert m.minimum_fillet_weld_leg_table38("single_sided_corner_or_t",40,25,355)["minimum_weld_leg_mm"]==22.0


def test_table38_external_routes_and_invalid_gap():
    assert m.minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner",41,30,355)["route"]=="calculation_required_above_40_mm"
    assert m.minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner",10,5,355)["route"]=="calculation_required_t_below_0_6T"
    assert m.minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner",5.5,4,355)["route"]=="calculation_required_outside_printed_bins"


def test_fillet_weld_geometry_limits():
    assert m.maximum_fillet_weld_leg_clause_14_1_7(10)==12.0
    assert m.maximum_fillet_weld_leg_clause_14_1_7(10,True)==9.0
    assert m.minimum_fillet_weld_design_length_clause_14_1_7(8)==40.0
    assert m.minimum_fillet_weld_design_length_clause_14_1_7(15)==60.0
    assert m.minimum_lap_length_clause_14_1_7(8)==40.0


def test_flank_weld_length_limit():
    assert m.maximum_flank_weld_length_clause_14_1_7(.8,10,False)==680.0
    assert m.maximum_flank_weld_length_clause_14_1_7(.8,10,True) is None


def test_table39_existence_lookup_and_value_consistency():
    data=m.table_39_catalog()
    assert "automatic_d3_5" in data["processes"]
    result=m.table_39_fillet_weld_coefficients("automatic_d3_5","lower",10)
    assert result["beta_f"]==.9 and result["beta_z"]==1.05
    constant=m.table_39_fillet_weld_coefficients("manual_or_mechanized_d_lt_1_4_or_flux_cored","all_listed_positions",20)
    assert constant["beta_f"]==.7 and constant["beta_z"]==1.0


def test_table39_rejects_13mm_and_unknown_route():
    with pytest.raises(ValueError): m.table_39_fillet_weld_coefficients("automatic_d3_5","boat",13)
    with pytest.raises(ValueError): m.table_39_fillet_weld_coefficients("bad","boat",8)


def test_welding_consumable_compatibility_routes():
    manual=m.welding_consumable_compatibility_clause_14_1_8("manual",210,180,.7,1.0,290)
    assert manual["pass"]
    mechanized=m.welding_consumable_compatibility_clause_14_1_8("mechanized",190,180,.8,1.0,290)
    assert mechanized["pass"]
    automated=m.welding_consumable_compatibility_clause_14_1_8("automatic",240,166.5,1.1,1.15,235)
    assert automated["upper_bound_n_mm2"] == pytest.approx(166.5*1.15/1.1)
    assert automated["pass"] is False
    with pytest.raises(ValueError): m.welding_consumable_compatibility_clause_14_1_8("manual",170,180,.7,1.0,355)


def test_one_sided_weld_route():
    assert not m.one_sided_fillet_weld_route_clause_14_1_9(True,True,False)["accepted"]
    incomplete=m.one_sided_fillet_weld_route_clause_14_1_9(True,False,False)
    assert incomplete["accepted"] is False
    assert incomplete["full_clause_14_1_9_project_conditions_required"] is True
    assert m.one_sided_fillet_weld_route_clause_14_1_9(False,True,True)["accepted"]


def test_intermittent_weld_route_spacing_and_end_length():
    assert m.intermittent_weld_applicability_clause_14_1_10(True,True,False)["proceed_to_spacing_check"]
    assert not m.intermittent_weld_applicability_clause_14_1_10(True,False,True)["accepted"]
    assert m.intermittent_weld_spacing_limit_clause_14_1_10(10,"compression",1)==120.0
    assert m.intermittent_weld_spacing_limit_clause_14_1_10(10,"tension",4)==240.0
    assert m.end_weld_minimum_length_clause_14_1_10(100)==75.0


def test_perimeter_or_plug_route_and_plug_geometry():
    assert m.perimeter_or_plug_weld_route_clause_14_1_11_14_1_12("plug",False)["accepted"]
    assert not m.perimeter_or_plug_weld_route_clause_14_1_11_14_1_12("perimeter",False)["accepted"]
    round_result=m.plug_weld_requirements_clause_14_1_12(8,hole_diameter_mm=20)
    assert round_result["dimension_meets_t_plus_8"] and round_result["minimum_center_spacing_mm"]==80.0
    slot=m.plug_weld_requirements_clause_14_1_12(8,slot_width_mm=20,slot_length_mm=100)
    assert slot["geometry"]=="slot"


def test_combined_connection_force_distribution():
    result=m.combined_connection_force_distribution_clause_14_1_13(100,60,80,True,True)
    assert math.isclose(result["friction_force_n"]+result["weld_force_n"],100)
    assert result["pass"]
    with pytest.raises(ValueError): m.combined_connection_force_distribution_clause_14_1_13(100,60,80,False,True)


def test_butt_weld_effective_length_and_resistance_branch():
    assert m.effective_butt_weld_length_clause_14_1_14(200,10,False)==180.0
    assert m.effective_butt_weld_length_clause_14_1_14(200,10,True)==200.0
    assert m.butt_weld_resistance_branch_clause_14_1_14(True,True,True)["branch"]=="ultimate"
    assert not m.butt_weld_resistance_branch_clause_14_1_14(False,True,True)["accepted"]


def test_equation175_normal_zero_and_sign():
    expected=100000/(10*200*250*1.0)
    assert math.isclose(m.butt_weld_axial_utilization_eq175(100000,10,200,250,1),expected)
    assert m.butt_weld_axial_utilization_eq175(0,10,200,250,1)==0.0
    assert m.butt_weld_axial_utilization_eq175(-100000,10,200,250,1)==expected


def test_butt_weld_combined_stress_route():
    result=m.butt_weld_combined_stress_clause_14_1_15(100,50,20,200,120,1)
    assert result["governing_utilization"]>=result["shear_utilization"]
    assert result["equivalent_pass"]


def test_fillet_effective_length_and_governing_plane():
    assert m.fillet_weld_effective_length_clause_14_1_16([100,50,25])==145.0
    assert m.fillet_weld_governing_plane_clause_14_1_16(.7,200,1.0,150)=="weld_metal"
    assert m.fillet_weld_governing_plane_clause_14_1_16(1.0,300,.7,100)=="fusion_boundary"


def test_equations176_177_normal_zero_and_sign():
    u176=m.fillet_weld_axial_metal_utilization_eq176(100000,.7,10,200,200,1)
    u177=m.fillet_weld_axial_fusion_utilization_eq177(100000,1.0,10,200,150,1)
    assert math.isclose(u176,100000/(.7*10*200*200))
    assert math.isclose(u177,100000/(1.0*10*200*150))
    assert m.fillet_weld_axial_metal_utilization_eq176(0,.7,10,200,200,1)==0
    assert m.fillet_weld_axial_fusion_utilization_eq177(-100000,1,10,200,150,1)==u177


def test_equations178_179_normal_zero_and_sign():
    assert m.fillet_weld_out_of_plane_moment_metal_utilization_eq178(1000000,10000,200,1)==.5
    assert m.fillet_weld_out_of_plane_moment_fusion_utilization_eq179(1000000,10000,100,1)==1.0
    assert m.fillet_weld_out_of_plane_moment_metal_utilization_eq178(0,10000,200,1)==0
    assert m.fillet_weld_out_of_plane_moment_fusion_utilization_eq179(-1000000,10000,100,1)==1.0


def test_equations180_181_normal_zero_and_coordinate_sign():
    u180=m.fillet_weld_in_plane_moment_metal_utilization_eq180(100000,10,0,10000,10000,200,1)
    u181=m.fillet_weld_in_plane_moment_fusion_utilization_eq181(100000,-10,0,10000,10000,200,1)
    assert math.isclose(u180,.25) and math.isclose(u181,.25)
    assert m.fillet_weld_in_plane_moment_metal_utilization_eq180(0,10,0,10000,10000,200,1)==0


def test_equation182_normal_zero_and_governing_plane():
    result=m.combined_fillet_weld_utilizations_eq182(50,40,200,150,1)
    assert result["fusion_boundary_utilization"]>result["weld_metal_utilization"]
    zero=m.combined_fillet_weld_utilizations_eq182(0,0,200,150,1)
    assert zero["governing_utilization"]==0 and zero["pass"]


def test_equation183_normal_zero_and_sign_convention():
    expected=math.sqrt((10+20)**2+(30-5)**2)
    assert math.isclose(m.resultant_shear_stress_eq183(10,20,30,-5),expected)
    assert m.resultant_shear_stress_eq183(0,0,0,0)==0
    assert m.resultant_shear_stress_eq183(-10,-20,-30,5)==expected


def test_equations184_185_normal_zero_boundary():
    assert math.isclose(m.spot_weld_shear_capacity_eq184(10,400),11200.0)
    assert m.spot_weld_tearout_capacity_eq185(1.1,10,2,400)==8800.0
    with pytest.raises(ValueError): m.spot_weld_shear_capacity_eq184(0,400)
    with pytest.raises(ValueError): m.spot_weld_tearout_capacity_eq185(1.1,10,0,400)


def test_spot_beta_and_governing_capacity():
    assert m.spot_weld_beta_clause_14_1_20(2,2)==1.1
    assert m.spot_weld_beta_clause_14_1_20(2,4)==1.9
    assert math.isclose(m.spot_weld_beta_clause_14_1_20(2,3),1.5)
    result=m.spot_weld_governing_capacity_clause_14_1_20(2,2,10,400,400)
    assert result["governing_capacity_n"]==8800.0 and result["governing_mode"]=="tearout"
    with pytest.raises(ValueError): m.spot_weld_governing_capacity_clause_14_1_20(5,2,10,400,400)
