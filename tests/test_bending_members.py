import json
import math
from pathlib import Path

import pytest

from standard_core import bending_members as b
from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

ROOT = Path(__file__).resolve().parents[1]


def test_bending_member_class_requirements():
    assert b.bending_member_class_requirements(1, False, False, False)["required_route"] == "elastic"
    assert b.bending_member_class_requirements(2, True, False, True)["permitted"] is True
    assert b.bending_member_class_requirements(2, True, True, False)["permitted"] is False


def test_equation_41_normal_zero_and_units():
    assert b.elastic_bending_utilization_eq41(1e8, 1e6, 250, 1) == pytest.approx(0.4)
    assert b.elastic_bending_utilization_eq41(0, 1e6, 250, 1) == 0
    with pytest.raises(ValueError):
        b.elastic_bending_utilization_eq41(1, 0, 250, 1)


def test_equation_42_normal_zero_and_units():
    value = b.elastic_shear_utilization_eq42(100000, 200000, 2e8, 8, 145, 1)
    assert value == pytest.approx(100000 * 200000 / (2e8 * 8 * 145))
    assert b.elastic_shear_utilization_eq42(0, 200000, 2e8, 8, 145, 1) == 0
    with pytest.raises(ValueError):
        b.elastic_shear_utilization_eq42(1, 1, 1, 0, 1, 1)


def test_equation_43_sign_and_units():
    positive = b.elastic_combined_normal_utilization_eq43(1e8, 2e7, 1e10, 2e8, 1e8, 1e12, 200, 50, 10000, 355, 1)
    negative = b.elastic_combined_normal_utilization_eq43(-1e8, -2e7, -1e10, 2e8, 1e8, 1e12, 200, 50, 10000, 355, 1)
    assert positive == pytest.approx(210 / 355)
    assert negative == pytest.approx(positive)
    assert b.elastic_combined_normal_utilization_eq43(0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1) == 0


def test_equation_44_normal_zero_and_sign():
    result = b.elastic_web_equivalent_stress_checks_eq44(100, 20, 50, 355, 205.9, 1)
    expected = 0.87 * math.sqrt(100**2 - 100 * 20 + 20**2 + 3 * 50**2) / 355
    assert result["equivalent_utilization"] == pytest.approx(expected)
    sign = b.elastic_web_equivalent_stress_checks_eq44(-100, -20, -50, 355, 205.9, 1)
    assert sign["equivalent_utilization"] == pytest.approx(result["equivalent_utilization"])
    zero = b.elastic_web_equivalent_stress_checks_eq44(0, 0, 0, 355, 205.9, 1)
    assert zero["governing_utilization"] == 0


def test_equation_45_normal_boundary_and_units():
    assert b.bolt_hole_factor_eq45(100, 20) == pytest.approx(1.25)
    assert b.bolt_hole_factor_eq45(100, 0) == 1
    with pytest.raises(ValueError):
        b.bolt_hole_factor_eq45(20, 20)


def test_apply_bolt_hole_factor():
    assert b.apply_bolt_hole_factor(0.8, 1.25) == 1.0
    assert b.apply_bolt_hole_factor(0, 1) == 0
    with pytest.raises(ValueError):
        b.apply_bolt_hole_factor(1, 0.9)


def test_equations_46_and_47():
    stress = b.local_web_compression_stress_eq47(80000, 100, 8)
    assert stress == 100
    assert b.local_web_compression_utilization_eq46(stress, 250, 1) == 0.4
    assert b.local_web_compression_stress_eq47(0, 100, 8) == 0


def test_equations_48_and_49():
    assert b.effective_load_length_eq48(100, 20) == 140
    assert b.effective_load_length_crane_eq49(3.25, 8e6, 8) == pytest.approx(325)
    with pytest.raises(ValueError):
        b.effective_load_length_eq48(0, 0)


def test_effective_load_length_router():
    assert b.effective_load_length_by_case("welded_or_rolled", 100, 20, None, None, None) == 140
    assert b.effective_load_length_by_case("crane_wheel", None, None, 3.25, 8e6, 8) == pytest.approx(325)
    with pytest.raises(ValueError):
        b.effective_load_length_by_case("crane_wheel", 1, None, 3.25, 8e6, 8)


def test_annex_e1_catalogue_and_exact_nodes():
    data = b.annex_e1_plastic_coefficient_catalog()
    assert data["table_number"] == "Е.1"
    assert len(data["section_types"]) == 12
    assert b.annex_e1_base_coefficients("1", 0.25, True) == {"c_x": 1.19, "c_y": 1.47, "n": 1.5}
    assert b.annex_e1_base_coefficients("9a", 2.0, True) == {"c_x": 1.6, "c_y": 1.19, "n": 3.0}


def test_annex_e1_interpolation_and_footnote():
    value = b.annex_e1_base_coefficients("1", 0.75, False)
    assert value["c_x"] == pytest.approx(1.095)
    assert value["c_y"] == pytest.approx(1.47)
    assert value["n"] == 1.5
    assert b.annex_e1_base_coefficients("5a", None, False)["n"] == 2
    assert b.annex_e1_base_coefficients("5b", None, False)["n"] == 3
    with pytest.raises(ValueError):
        b.annex_e1_base_coefficients("1", 3.0, True)


def test_annex_e1_cap():
    assert b.apply_annex_e1_load_factor_cap(1.47, 1.1) == pytest.approx(1.265)
    assert b.apply_annex_e1_load_factor_cap(1.1, 2.0) == 1.1
    with pytest.raises(ValueError):
        b.apply_annex_e1_load_factor_cap(1.1, 0)


def test_annex_e1_design_coefficients():
    result = b.annex_e1_design_coefficients("1", 1.0, False, 1.3)
    assert result["c_x"] == 1.07
    assert result["c_y"] == 1.47
    assert result["n"] == 1.5


def test_plastic_bending_applicability():
    assert b.plastic_bending_applicability(2, "i_section", 355, 100, 145, True, False)["permitted"] is True
    result = b.plastic_bending_applicability(2, "i_section", 450, 140, 145, False, True)
    assert result["permitted"] is False
    assert len(result["failed_gates"]) == 4


def test_equation_52_branches_and_limits():
    assert b.plastic_shear_reduction_factor_eq52(50, 100, 1) == 1
    expected = 1 - 0.2 / 1.25 * 0.8**4
    assert b.plastic_shear_reduction_factor_eq52(80, 100, 1) == pytest.approx(expected)
    with pytest.raises(ValueError):
        b.plastic_shear_reduction_factor_eq52(91, 100, 1)


def test_equations_50_and_51():
    assert b.plastic_bending_utilization_eq50(1e8, 1.2, 1, 1e6, 250, 1) == pytest.approx(1 / 3)
    biaxial = b.plastic_biaxial_bending_utilization_eq51(1e8, 2e7, 1.2, 1.2, 1, 1e6, 5e5, 250, 1)
    assert biaxial == pytest.approx(1 / 3 + 2e7 / (1.2 * 5e5 * 250))
    assert b.plastic_biaxial_bending_utilization_eq51(0, 0, 1, 1, 1, 1, 1, 1, 1) == 0


def test_table_10a_catalogue_and_nodes():
    data = b.table_10a_constrained_torsion_catalog()
    assert len(data["nodes"]) == 11
    assert data["nodes"][0] == {"ratio": 0.0, "c_omega": 1.47}
    assert data["nodes"][-1] == {"ratio": 0.99, "c_omega": 3.496}


def test_table_10a_interpolation_and_bounds():
    assert b.constrained_torsion_coefficient_table_10a(0.15) == pytest.approx((1.636 + 1.845) / 2)
    assert b.constrained_torsion_coefficient_table_10a(0) == 1.47
    with pytest.raises(ValueError):
        b.constrained_torsion_coefficient_table_10a(1.0)


def test_equation_53():
    value = b.constrained_torsion_utilization_eq53(1e8, 1e10, 1.2, 1, 1e6, 2, 1e8, 250, 1)
    assert value == pytest.approx(1 / 3 + 0.2)
    assert b.constrained_torsion_utilization_eq53(0, 0, 1, 1, 1, 1, 1, 1, 1) == 0


def test_pure_bending_modified_coefficients():
    assert b.pure_bending_modified_coefficients(1.2, 1.4) == {"c_xm": 1.1, "c_ym": 1.2}
    with pytest.raises(ValueError):
        b.pure_bending_modified_coefficients(0, 1)


def test_equations_54_and_55():
    assert b.support_shear_x_utilization_eq54(100000, 1000, 100, 1) == 1
    assert b.support_shear_y_utilization_eq55(100000, 500, 100, 1) == 1
    assert b.support_shear_x_utilization_eq54(0, 1, 1, 1) == 0


def test_variable_section_routing():
    assert b.variable_section_plastic_routing(True, False)["route"] == "full_clause_8_2_3"
    assert b.variable_section_plastic_routing(False, True)["route"] == "reduced_plastic_coefficients"
    assert b.variable_section_plastic_routing(False, False)["route"] == "elastic_clause_8_2_1"


def test_continuous_beam_applicability():
    assert b.continuous_beam_partial_redistribution_applicability(10000, 11000, True, True, True)["permitted"] is True
    assert b.continuous_beam_partial_redistribution_applicability(10000, 13000, True, True, True)["permitted"] is False


def test_equations_56_to_58():
    meff = b.effective_moment_hinged_end_eq57([120, 150], [0, 5], 10)
    assert meff == 120
    assert b.effective_moment_intermediate_span_eq58(160) == 80
    assert b.redistributed_design_moment_eq56(180, meff) == 150
    with pytest.raises(ValueError):
        b.effective_moment_hinged_end_eq57([], [], 10)


def test_effective_moment_router():
    assert b.effective_moment_by_end_condition("intermediate_span", [100], None, None) == 50
    assert b.effective_moment_by_end_condition("fixed_ends", [140], None, None) == 70
    with pytest.raises(ValueError):
        b.effective_moment_by_end_condition("fixed_ends", [1, 2], None, None)


def test_biaxial_redistribution_route():
    assert b.biaxial_redistribution_route(True, True)["permitted"] is True
    assert b.biaxial_redistribution_route(True, False)["permitted"] is False


def test_class_3_route():
    assert b.class_3_plastic_hinge_route(True, True, True, True, True, True)["permitted"] is True
    result = b.class_3_plastic_hinge_route(True, False, True, True, True, True)
    assert result["missing_confirmations"] == ["8.4.6"]


def test_equation_61():
    expected = (1.0 * 1.2 + 0.25 - 0.0833 / 1.2**2) / (1.0 + 0.167)
    assert b.bimetal_major_axis_coefficient_eq61(1.2, 1.0, 1.2) == pytest.approx(expected)
    # Frozen legacy c_xf argument must not affect current-SP16 equation (61).
    assert b.bimetal_major_axis_coefficient_eq61(99.0, 1.0, 1.2) == pytest.approx(expected)
    with pytest.raises(ValueError):
        b.bimetal_major_axis_coefficient_eq61(1, 1, 0)


def test_equation_62_branches():
    assert b.bimetal_shear_reduction_factor_eq62(50, 100, 1, 1.2) == 1
    expected = 1 - 0.2 / 1.45 * 0.8**4
    assert b.bimetal_shear_reduction_factor_eq62(80, 100, 1, 1.2) == pytest.approx(expected)
    with pytest.raises(ValueError):
        b.bimetal_shear_reduction_factor_eq62(91, 100, 1, 1.2)


def test_bimetal_minor_axis_coefficient():
    assert b.bimetal_minor_axis_coefficient("i_section", 1.5) == 1.15
    assert b.bimetal_minor_axis_coefficient("box_section", 1.5) == pytest.approx(0.7)


def test_bimetal_applicability():
    assert b.bimetal_bending_applicability("i_section", True, True, 100, 145, 50, 145, False)["permitted"] is True
    assert b.bimetal_bending_applicability("i_section", False, False, 140, 145, 80, 145, True)["permitted"] is False


def test_equations_59_and_60():
    eq59 = b.bimetal_bending_utilization_eq59(1e8, 1.2, 1, 1e6, 250, 1)
    assert eq59 == pytest.approx(1 / 3)
    eq60 = b.bimetal_biaxial_bending_utilization_eq60(1e8, 2e7, 1.2, 1.15, 1, 1e6, 5e5, 250, 300, 1)
    assert eq60 == pytest.approx(1 / 3 + 2e7 / (1.15 * 5e5 * 300))
    assert b.bimetal_biaxial_bending_utilization_eq60(0, 0, 1, 1, 1, 1, 1, 1, 1, 1) == 0


def test_bending_schema_and_runner():
    schema = json.loads((ROOT / "schemas/bending_member_case.schema.json").read_text(encoding="utf-8"))
    example = json.loads((ROOT / "examples/bending_member_example.json").read_text(encoding="utf-8"))
    assert validate_case(example, schema) == []
    result = run_case(ROOT / "examples/bending_member_example.json", ROOT)
    assert result["results"]["equation_41_elastic_bending_utilization"] > 0
    assert (ROOT / "outputs/bending_member_result.json").exists()
