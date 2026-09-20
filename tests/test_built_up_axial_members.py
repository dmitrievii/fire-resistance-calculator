import math

import pytest

from standard_core import built_up_axial_members as bm


def test_table_8_catalog_exists_and_is_consistent():
    catalog = bm.table_8_formula_catalog()
    assert catalog["table_number"] == "8"
    assert len(catalog["formula_rows"]) == 6
    assert catalog["formula_rows"]["type_1_battens"]["equation"] == "12"
    catalog["table_number"] = "mutated"
    assert bm.table_8_formula_catalog()["table_number"] == "8"


def test_clause_7_2_1_strength_branches():
    expected_yield = 500000.0 / (2500.0 * 355.0)
    assert bm.built_up_axial_strength_utilization(500000, 2500, "yield", 355, 485, 1.3, 1.0) == pytest.approx(expected_yield)
    expected_ultimate = 500000.0 * 1.3 / (2500.0 * 485.0)
    assert bm.built_up_axial_strength_utilization(500000, 2500, "ultimate", 355, 485, 1.3, 1.0) == pytest.approx(expected_ultimate)
    assert bm.built_up_axial_strength_utilization(0, 2500, "yield", 355, 485, 1.3, 1.0) == 0.0
    with pytest.raises(ValueError):
        bm.built_up_axial_strength_utilization(1, 1, "automatic", 355, 485, 1.3, 1.0)


def test_stability_method_selection():
    assert bm.built_up_stability_method(6, "battens") == "table_8_effective_slenderness"
    assert bm.built_up_stability_method(5, "battens") == "frame_system_analysis_required"
    assert bm.built_up_stability_method(5, "lattice") == "clause_7_2_5_lattice_branch_method"
    with pytest.raises(TypeError):
        bm.built_up_stability_method(6.0, "battens")
    with pytest.raises(ValueError):
        bm.built_up_stability_method(0, "lattice")


def test_equation_12_type_1_battened():
    n = 200000.0 * 400.0 / (500000.0 * 1000.0)
    expected = math.sqrt(2.0**2 + 0.82 * (1.0 + n) * 1.0**2)
    assert bm.battened_effective_slenderness_type_1(2, 1, 200000, 400, 500000, 1000) == pytest.approx(expected)
    assert bm.battened_effective_slenderness_type_1(0, 0, 200000, 400, 500000, 1000) == 0.0
    with pytest.raises(ValueError):
        bm.battened_effective_slenderness_type_1(2, 1, 200000, 400, 0, 1000)


def test_equation_13_type_2_battened():
    n1 = 200000.0 * 350.0 / (500000.0 * 1000.0)
    n2 = 220000.0 * 450.0 / (550000.0 * 1000.0)
    expected = math.sqrt(2.0**2 + 0.82 * ((1+n1) * 1.0**2 + (1+n2) * 1.1**2))
    actual = bm.battened_effective_slenderness_type_2(2, 1, 1.1, 200000, 220000, 350, 450, 500000, 550000, 1000)
    assert actual == pytest.approx(expected)
    with pytest.raises(ValueError):
        bm.battened_effective_slenderness_type_2(2, 1, -0.1, 200000, 220000, 350, 450, 500000, 550000, 1000)


def test_equation_14_type_3_battened():
    n3 = 180000.0 * 400.0 / (500000.0 * 1000.0)
    expected = math.sqrt(2.0**2 + 0.82 * (1 + 3*n3) * 1.0**2)
    assert bm.battened_effective_slenderness_type_3(2, 1, 180000, 400, 500000, 1000) == pytest.approx(expected)
    with pytest.raises(ValueError):
        bm.battened_effective_slenderness_type_3(2, 1, 180000, -400, 500000, 1000)


def test_equation_15_type_1_lattice():
    alpha = 10.0 * 600.0**3 / (400.0**2 * 1000.0)
    expected = math.sqrt(2.0**2 + alpha * 5000.0 / 500.0)
    assert bm.lattice_effective_slenderness_type_1(2, 5000, 500, 600, 400, 1000) == pytest.approx(expected)
    with pytest.raises(ValueError):
        bm.lattice_effective_slenderness_type_1(2, 5000, 0, 600, 400, 1000)


def test_equation_16_type_2_lattice():
    alpha1 = 10.0 * 600.0**3 / (350.0**2 * 1000.0)
    alpha2 = 10.0 * 650.0**3 / (450.0**2 * 1000.0)
    expected = math.sqrt(2.0**2 + (alpha1 + alpha2 * 500.0/550.0) * 5000.0/500.0)
    actual = bm.lattice_effective_slenderness_type_2(2, 5000, 500, 550, 600, 650, 350, 450, 1000)
    assert actual == pytest.approx(expected)
    with pytest.raises(ValueError):
        bm.lattice_effective_slenderness_type_2(2, 5000, 500, 550, 600, 650, 350, 450, 0)


def test_equation_17_type_3_lattice():
    alpha = 10.0 * 600.0**3 / (400.0**2 * 1000.0)
    expected = math.sqrt(2.0**2 + 0.67 * alpha * 5000.0 / 500.0)
    assert bm.lattice_effective_slenderness_type_3(2, 5000, 500, 600, 400, 1000) == pytest.approx(expected)
    with pytest.raises(ValueError):
        bm.lattice_effective_slenderness_type_3(2, -5000, 500, 600, 400, 1000)


def test_batten_branch_limit():
    assert bm.batten_branch_slenderness_check(1.4)["pass"] is True
    assert bm.batten_branch_slenderness_check(1.400001)["pass"] is False
    with pytest.raises(ValueError):
        bm.batten_branch_slenderness_check(-0.1)


def test_lattice_branch_assessment():
    assert bm.lattice_branch_slenderness_assessment(2.5, 3.0, False)["classification"] == "basic_limits_satisfied"
    assert bm.lattice_branch_slenderness_assessment(3.0, 2.5, True)["classification"] == "permitted_only_with_clause_7_2_5"
    assert bm.lattice_branch_slenderness_assessment(3.0, 2.5, False)["classification"] == "clause_7_2_5_check_required"
    assert bm.lattice_branch_slenderness_assessment(4.2, 5.0, True)["permitted"] is False
    assert bm.lattice_branch_slenderness_assessment(2.6, 2.5, False)["classification"] == "exceeds_member_effective_slenderness"


def test_lattice_branch_phi_rules():
    assert bm.lattice_branch_stability_coefficient(2.7, "b") == 1.0
    endpoint = bm.central_compression_stability_coefficient(0.7 * 3.2, "b")
    assert bm.lattice_branch_stability_coefficient(3.2, "b") == pytest.approx(endpoint)
    midpoint = bm.lattice_branch_stability_coefficient(2.95, "b")
    assert midpoint == pytest.approx((1.0 + endpoint) / 2.0)
    assert bm.lattice_branch_stability_coefficient(4.0, "c") == pytest.approx(
        bm.central_compression_stability_coefficient(2.8, "c")
    )


def test_lattice_built_up_stability_utilization():
    result = bm.lattice_built_up_stability_utilization(500000, 5000, 355, 1, 2.0, 3.0, "b")
    expected_phi = bm.central_compression_stability_coefficient(2.0, "b")
    expected_phi1 = bm.lattice_branch_stability_coefficient(3.0, "b")
    expected = 500000.0 / (expected_phi * 5000.0 * expected_phi1 * 355.0)
    assert result["overall_stability_coefficient_phi"] == pytest.approx(expected_phi)
    assert result["branch_stability_coefficient_phi_1"] == pytest.approx(expected_phi1)
    assert result["utilization"] == pytest.approx(expected)


def test_close_contact_spacing_check():
    compression = bm.close_contact_connection_spacing_check(400, 10, "compression", 2)
    assert compression["maximum_spacing_mm"] == 400.0
    assert compression["pass"] is True
    assert bm.close_contact_connection_spacing_check(401, 10, "compression", 2)["pass"] is False
    tension = bm.close_contact_connection_spacing_check(800, 10, "tension", 0)
    assert tension["pass"] is True
    assert tension["intermediate_connection_count_pass"] is None
    with pytest.raises(ValueError):
        bm.close_contact_connection_spacing_check(100, 10, "bending", 0)


def test_equation_18_fictitious_shear():
    expected = 7.15e-6 * (2330.0 - 206000.0/355.0) * 1000000.0 / 0.8
    assert bm.fictitious_shear_force_n(1000000, 206000, 355, 0.8) == pytest.approx(expected)
    assert bm.fictitious_shear_force_n(0, 206000, 355, 0.8) == 0.0
    with pytest.raises(ValueError):
        bm.fictitious_shear_force_n(1000000, 300000, 100, 0.8)
    with pytest.raises(ValueError):
        bm.fictitious_shear_force_n(1000000, 206000, 355, 1.1)


def test_fictitious_shear_distribution():
    only = bm.distribute_fictitious_shear(1000, "connectors_only", 2)
    assert only["per_connector_system_force_n"] == 500.0
    mixed = bm.distribute_fictitious_shear(1000, "solid_sheet_and_connectors", 2)
    assert mixed["solid_sheet_force_n"] == 500.0
    assert mixed["per_connector_system_force_n"] == 250.0
    tri = bm.distribute_fictitious_shear(1000, "equilateral_three_sided", 1)
    assert tri["per_connector_system_force_n"] == 800.0
    assert tri["total_assigned_force_n"] == 2400.0


def test_equation_19_batten_shear():
    assert bm.batten_shear_force_n(1000, 800, 400) == 2000.0
    assert bm.batten_shear_force_n(0, 800, 400) == 0.0
    with pytest.raises(ValueError):
        bm.batten_shear_force_n(1000, 800, 0)


def test_equation_20_batten_moment():
    assert bm.batten_bending_moment_n_mm(1000, 800) == 400000.0
    assert bm.batten_bending_moment_n_mm(0, 800) == 0.0
    with pytest.raises(ValueError):
        bm.batten_bending_moment_n_mm(1000, -800)


def test_equation_21_lattice_diagonal_force():
    assert bm.lattice_diagonal_force_n(1000, 600, 400, 1.0) == 1500.0
    assert bm.lattice_diagonal_force_n(1000, 600, 400, 0.5) == 750.0
    assert bm.lattice_diagonal_force_n(0, 600, 400, 0.5) == 0.0
    with pytest.raises(ValueError):
        bm.lattice_diagonal_force_n(1000, 600, 400, 0.75)


def test_equation_22_alpha_2_and_additional_force():
    expected_alpha = 600.0 * 800.0**2 / (2.0 * 400.0**3 + 600.0**3)
    alpha = bm.cross_lattice_alpha_2(600, 800, 400)
    assert alpha == pytest.approx(expected_alpha)
    expected_force = alpha * 200000.0 * 500.0 / 2500.0
    assert bm.cross_lattice_additional_diagonal_force_n(200000, 500, 2500, alpha) == pytest.approx(expected_force)
    assert bm.cross_lattice_additional_diagonal_force_n(0, 500, 2500, alpha) == 0.0
    with pytest.raises(ValueError):
        bm.cross_lattice_alpha_2(600, 800, 0)


def test_clause_7_2_10_restraint_forces():
    q = bm.fictitious_shear_force_n(1000000, 206000, 355, 0.8)
    assert bm.reduced_length_brace_design_force_n(q) == q
    assert bm.column_branch_spacer_fictitious_shear_n(400000, 600000, 206000, 355, 0.8) == pytest.approx(q)
    with pytest.raises(ValueError):
        bm.reduced_length_brace_design_force_n(-1)
