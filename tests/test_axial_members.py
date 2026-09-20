import json
import math
from pathlib import Path

import pytest

from standard_core import axial_members as am

ROOT = Path(__file__).resolve().parents[1]


def test_equation_5_yield_normal_zero_and_units():
    expected = 500000.0 / (2000.0 * 355.0 * 0.95)
    assert am.axial_strength_utilization_yield(500000.0, 2000.0, 355.0, 0.95) == pytest.approx(expected)
    assert am.axial_strength_utilization_yield(0.0, 2000.0, 355.0, 0.95) == 0.0
    assert am.axial_strength_utilization_yield(500000.0, 2000.0, 355.0, 1.0) == pytest.approx(
        am.axial_strength_utilization_yield(500.0, 2.0, 355.0, 1.0)
    )


def test_equation_5_ultimate_branch_and_sign_rejection():
    expected = 500000.0 * 1.3 / (2000.0 * 485.0)
    assert am.axial_strength_utilization_ultimate(500000.0, 2000.0, 485.0, 1.3, 1.0) == pytest.approx(expected)
    with pytest.raises(ValueError):
        am.axial_strength_utilization_ultimate(-1.0, 2000.0, 485.0, 1.3, 1.0)
    with pytest.raises(ValueError):
        am.axial_strength_utilization_ultimate(1.0, 0.0, 485.0, 1.3, 1.0)


def test_table_6_lookup_existence_and_values():
    expected = {
        "one_bolt_a_1_35d": (1.70, 0.05, 0.65),
        "one_bolt_a_1_5d": (1.70, 0.05, 0.85),
        "one_bolt_a_2d": (1.70, 0.05, 1.0),
        "multi_bolt_2": (1.77, 0.19, 1.0),
        "multi_bolt_3": (1.45, 0.36, 1.0),
        "multi_bolt_4": (1.17, 0.47, 1.0),
    }
    assert {key: am.table_6_angle_coefficients(key) for key in expected} == expected
    with pytest.raises(ValueError):
        am.table_6_angle_coefficients("multi_bolt_5")


def test_gamma_c1_formula_boundary_and_special_reduction():
    base = am.single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, False)
    assert base == pytest.approx(0.65)
    assert am.single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, True) == pytest.approx(0.585)
    assert am.single_angle_working_condition_factor(1000.0, 0.0, 1.45, 0.36, 1.0, False) == pytest.approx(0.36)
    with pytest.raises(ValueError):
        am.single_angle_working_condition_factor(1000.0, 1001.0, 1.45, 0.36, 1.0, False)
    with pytest.raises(TypeError):
        am.single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, 1)


def test_equation_6_normal_zero_and_invalid_domains():
    expected = 200000.0 * 1.3 / (1000.0 * 485.0 * 0.65)
    assert am.single_angle_connection_strength_utilization(200000.0, 1000.0, 485.0, 1.3, 0.65) == pytest.approx(expected)
    assert am.single_angle_connection_strength_utilization(0.0, 1000.0, 485.0, 1.3, 0.65) == 0.0
    with pytest.raises(ValueError):
        am.single_angle_connection_strength_utilization(1.0, 1000.0, 485.0, 1.3, 0.0)


def test_relative_slenderness_normal_zero_and_unit_consistency():
    value = am.relative_slenderness(100.0, 355.0, 206000.0)
    assert value == pytest.approx(100.0 * math.sqrt(355.0 / 206000.0))
    assert am.relative_slenderness(0.0, 355.0, 206000.0) == 0.0
    assert value == pytest.approx(am.relative_slenderness(100.0, 355000000.0, 206000000000.0))
    with pytest.raises(ValueError):
        am.relative_slenderness(100.0, 355.0, 0.0)


def test_table_7_lookup_and_rejection():
    assert am.table_7_section_coefficients("a") == (0.03, 0.06)
    assert am.table_7_section_coefficients("b") == (0.04, 0.09)
    assert am.table_7_section_coefficients("c") == (0.04, 0.14)
    with pytest.raises(ValueError):
        am.table_7_section_coefficients("d")


def test_equation_9_delta_normal_boundary_and_sign():
    assert am.stability_delta(2.0, 0.04, 0.09) == pytest.approx(9.87 * (1.0 - 0.04 + 0.18) + 4.0)
    assert am.stability_delta(0.0, 0.04, 0.09) == pytest.approx(9.87 * 0.96)
    with pytest.raises(ValueError):
        am.stability_delta(-0.1, 0.04, 0.09)


def test_equation_8_low_slenderness_formula_and_caps():
    assert am.central_compression_stability_coefficient(0.4, "a") == 1.0
    assert am.central_compression_stability_coefficient(0.59, "b") == 1.0
    assert am.central_compression_stability_coefficient(0.6, "a") == pytest.approx(0.9938128479757034)
    assert am.central_compression_stability_coefficient(0.4, "c") == pytest.approx(0.9840007778759206)
    assert am.central_compression_stability_coefficient(3.8, "a") == pytest.approx(7.6 / 3.8**2)
    assert am.central_compression_stability_coefficient(5.8, "c") == pytest.approx(7.6 / 5.8**2)
    assert am.central_compression_stability_coefficient(8.0, "b") == pytest.approx(7.6 / 8.0**2)
    assert am.central_compression_stability_coefficient(0.0386, "a") == 1.0
    assert am.central_compression_stability_coefficient(0.00265, "b") == 1.0
    with pytest.raises(ValueError):
        am.central_compression_stability_coefficient(0.399, "c")


def test_annex_d1_exact_lookup_and_no_interpolation():
    assert am.annex_d1_stability_coefficient(2.0, "b") == 0.826
    assert am.annex_d1_stability_coefficient(10.0, "c") == 0.076
    with pytest.raises(ValueError):
        am.annex_d1_stability_coefficient(2.1, "b")


def test_all_annex_d1_cells_are_formula_consistent():
    data = json.loads((ROOT / "data/annex_d_table_d1_stability_coefficients.json").read_text(encoding="utf-8"))
    for row in data["rows"]:
        slenderness = float(row["relative_slenderness"])
        for section_type in ("a", "b", "c"):
            tabulated = float(row[section_type]) / 1000.0
            calculated = am.central_compression_stability_coefficient(slenderness, section_type)
            assert abs(calculated - tabulated) <= 0.0010001, (slenderness, section_type, calculated, tabulated)


def test_equation_7_normal_zero_and_phi_domain():
    expected = 500000.0 / (0.8 * 2500.0 * 355.0)
    assert am.central_compression_stability_utilization(500000.0, 2500.0, 355.0, 1.0, 0.8) == pytest.approx(expected)
    assert am.central_compression_stability_utilization(0.0, 2500.0, 355.0, 1.0, 0.8) == 0.0
    with pytest.raises(ValueError):
        am.central_compression_stability_utilization(1.0, 2500.0, 355.0, 1.0, 1.01)
