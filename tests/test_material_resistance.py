import math

import pytest

from standard_core import material_resistance as mr


def test_table_2_design_yield_normal_boundary_and_units():
    assert mr.design_yield_resistance_n_mm2(355.0, 1.05) == pytest.approx(355.0 / 1.05)
    assert mr.design_yield_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(ValueError): mr.design_yield_resistance_n_mm2(-1.0, 1.05)


def test_table_2_design_ultimate_normal_boundary_and_units():
    assert mr.design_ultimate_resistance_n_mm2(510.0, 1.05) == pytest.approx(510.0 / 1.05)
    assert mr.design_ultimate_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(ValueError): mr.design_ultimate_resistance_n_mm2(510.0, 0.0)


def test_table_2_design_shear_normal_boundary_and_units():
    assert mr.design_shear_resistance_n_mm2(355.0, 1.05) == pytest.approx(0.58 * 355.0 / 1.05)
    assert mr.design_shear_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(ValueError): mr.design_shear_resistance_n_mm2(-355.0, 1.05)


def test_table_2_end_bearing_normal_boundary_and_units():
    assert mr.design_end_bearing_resistance_n_mm2(510.0, 1.05) == pytest.approx(510.0 / 1.05)
    assert mr.design_end_bearing_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(TypeError): mr.design_end_bearing_resistance_n_mm2("510", 1.05)


def test_table_2_pin_bearing_normal_boundary_and_units():
    assert mr.design_pin_local_bearing_resistance_n_mm2(510.0, 1.05) == pytest.approx(0.5 * 510.0 / 1.05)
    assert mr.design_pin_local_bearing_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(ValueError): mr.design_pin_local_bearing_resistance_n_mm2(510.0, -1.0)


def test_table_2_roller_compression_normal_boundary_and_units():
    assert mr.design_roller_diametral_compression_resistance_n_mm2(510.0, 1.05) == pytest.approx(0.025 * 510.0 / 1.05)
    assert mr.design_roller_diametral_compression_resistance_n_mm2(0.0, 1.05) == 0.0
    with pytest.raises(ValueError): mr.design_roller_diametral_compression_resistance_n_mm2(-1.0, 1.05)


def test_table_3_exists_lookup_and_consistency():
    expected={"statistical_control":1.025,"nonstatistical_high_yield_or_hot_finished_or_foreign":1.1,"other_conforming":1.05,"ks1_limited_service":1.0}
    assert {key:mr.material_safety_factor(key) for key in expected} == expected
    with pytest.raises(ValueError): mr.material_safety_factor("inferred")


def test_clause_6_2_identity_normal_boundary_and_units():
    assert mr.cold_formed_section_design_resistance_n_mm2(338.0) == 338.0
    assert mr.cold_formed_section_design_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.cold_formed_section_design_resistance_n_mm2(-0.1)


def test_table_4_butt_weld_yield_with_ndt():
    assert mr.butt_weld_design_yield_resistance_with_ndt_n_mm2(338.0) == 338.0
    assert mr.butt_weld_design_yield_resistance_with_ndt_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.butt_weld_design_yield_resistance_with_ndt_n_mm2(-1.0)


def test_table_4_butt_weld_ultimate_with_ndt():
    assert mr.butt_weld_design_ultimate_resistance_with_ndt_n_mm2(486.0) == 486.0
    assert mr.butt_weld_design_ultimate_resistance_with_ndt_n_mm2(0.0) == 0.0
    with pytest.raises(TypeError): mr.butt_weld_design_ultimate_resistance_with_ndt_n_mm2(None)


def test_table_4_butt_weld_yield_without_ndt():
    assert mr.butt_weld_design_yield_resistance_without_ndt_n_mm2(338.0) == pytest.approx(287.3)
    assert mr.butt_weld_design_yield_resistance_without_ndt_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.butt_weld_design_yield_resistance_without_ndt_n_mm2(-1.0)


def test_table_4_butt_weld_shear():
    assert mr.butt_weld_design_shear_resistance_n_mm2(196.0) == 196.0
    assert mr.butt_weld_design_shear_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.butt_weld_design_shear_resistance_n_mm2(-1.0)


def test_table_4_weld_metal_safety_factor_boundaries_and_gap():
    assert mr.weld_metal_safety_factor(490.0) == 1.25
    assert mr.weld_metal_safety_factor(590.0) == 1.35
    with pytest.raises(ValueError, match="does not specify"): mr.weld_metal_safety_factor(540.0)


def test_table_4_fillet_weld_metal_normal_boundary_and_units():
    assert mr.fillet_weld_metal_design_shear_resistance_n_mm2(490.0, 1.25) == pytest.approx(0.55*490.0/1.25)
    assert mr.fillet_weld_metal_design_shear_resistance_n_mm2(0.0, 1.25) == 0.0
    with pytest.raises(ValueError): mr.fillet_weld_metal_design_shear_resistance_n_mm2(490.0, 0.0)


def test_table_4_fusion_boundary_normal_boundary_and_units():
    assert mr.fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(510.0) == pytest.approx(229.5)
    assert mr.fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(-1.0)


def test_clause_6_4_dissimilar_steel_minimum():
    assert mr.dissimilar_steel_butt_weld_governing_resistance_n_mm2(338.0,315.0) == 315.0
    assert mr.dissimilar_steel_butt_weld_governing_resistance_n_mm2(0.0,315.0) == 0.0
    with pytest.raises(ValueError): mr.dissimilar_steel_butt_weld_governing_resistance_n_mm2(-1.0,315.0)


def test_table_5_shear_exists_lookup_and_consistency():
    expected={"5.6":0.42,"5.8":0.41,"8.8":0.40,"10.9":0.40,"12.9":0.35}
    assert {k:mr.bolt_shear_design_resistance_n_mm2(1.0,k) for k in expected} == expected
    assert mr.bolt_shear_design_resistance_n_mm2(0.0,"8.8") == 0.0
    with pytest.raises(ValueError): mr.bolt_shear_design_resistance_n_mm2(800.0,"4.6")


def test_table_5_tension_exists_lookup_and_consistency():
    expected={"5.6":0.45,"5.8":0.41,"8.8":0.54,"10.9":0.70,"12.9":0.70}
    assert {k:mr.bolt_tension_design_resistance_n_mm2(1.0,k) for k in expected} == expected
    assert mr.bolt_tension_design_resistance_n_mm2(0.0,"8.8") == 0.0
    with pytest.raises(ValueError): mr.bolt_tension_design_resistance_n_mm2(-1.0,"8.8")


def test_table_5_bearing_lookup_boundary_and_applicability():
    assert mr.connected_element_bearing_design_resistance_n_mm2(485.0,"A",450.0) == pytest.approx(1.60*485.0)
    assert mr.connected_element_bearing_design_resistance_n_mm2(485.0,"B",355.0) == pytest.approx(1.35*485.0)
    with pytest.raises(ValueError,match="<= 450"): mr.connected_element_bearing_design_resistance_n_mm2(485.0,"A",450.0001)


def test_equation_1_normal_zero_and_sign_unit_convention():
    assert mr.foundation_anchor_bolt_tension_design_resistance_n_mm2(355.0) == pytest.approx(284.0)
    assert mr.foundation_anchor_bolt_tension_design_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.foundation_anchor_bolt_tension_design_resistance_n_mm2(-355.0)


def test_equation_2_normal_zero_and_sign_unit_convention():
    assert mr.u_bolt_tension_design_resistance_n_mm2(355.0) == pytest.approx(301.75)
    assert mr.u_bolt_tension_design_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.u_bolt_tension_design_resistance_n_mm2(-355.0)


def test_equation_4_normal_zero_and_sign_unit_convention():
    assert mr.high_strength_wire_tension_design_resistance_n_mm2(510.0) == pytest.approx(321.3)
    assert mr.high_strength_wire_tension_design_resistance_n_mm2(0.0) == 0.0
    with pytest.raises(ValueError): mr.high_strength_wire_tension_design_resistance_n_mm2(-510.0)


def test_clause_6_9_rope_normal_zero_and_units():
    assert mr.steel_rope_design_tension_force_n(1600000.0) == 1000000.0
    assert mr.steel_rope_design_tension_force_n(0.0) == 0.0
    with pytest.raises(ValueError): mr.steel_rope_design_tension_force_n(-1.0)
