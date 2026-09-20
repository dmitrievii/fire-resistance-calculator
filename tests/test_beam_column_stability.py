import json
import math
from pathlib import Path

import pytest

from standard_core import beam_column_stability as bc

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/annex_d_tables_d2_to_d6.json").read_text(encoding="utf-8"))


def test_equation_109_normal_zero_and_units():
    assert bc.beam_column_in_plane_utilization_eq109(200000.0, 0.8, 3000.0, 250.0, 1.0) == pytest.approx(1.0 / 3.0)
    assert bc.beam_column_in_plane_utilization_eq109(0.0, 0.8, 3000.0, 250.0, 1.0) == 0.0
    with pytest.raises(ValueError):
        bc.beam_column_in_plane_utilization_eq109(-1.0, 0.8, 3000.0, 250.0, 1.0)
    with pytest.raises(ValueError):
        bc.beam_column_in_plane_utilization_eq109(1.0, 0.0, 3000.0, 250.0, 1.0)


def test_equation_110_and_bending_route():
    assert bc.effective_relative_eccentricity_eq110(1.2, 2.0) == pytest.approx(2.4)
    assert bc.beam_column_section_9_2_route(20.0, False, True, False)["route"] == "equations_109_to_115"
    assert bc.beam_column_section_9_2_route(20.1, False, True, False)["route"] == "section_8_bending_member"


def test_equation_111_and_c_domain():
    expected = 200000.0 / (0.5 * 0.8 * 3000.0 * 250.0)
    assert bc.beam_column_out_of_plane_utilization_eq111(200000.0, 0.5, 0.8, 3000.0, 250.0, 1.0) == pytest.approx(expected)
    with pytest.raises(ValueError):
        bc.beam_column_out_of_plane_utilization_eq111(1.0, 0.29, 0.8, 3000.0, 250.0, 1.0)


def test_equations_112_to_114_and_router():
    assert bc.out_of_plane_coefficient_c_eq112(0.7, 1.0, 2.0) == pytest.approx(1.0 / 2.4)
    assert bc.out_of_plane_coefficient_c_eq113(10.0, 0.8, 0.9) == pytest.approx(1.0 / (1.0 + 10.0 * 0.8 / 0.9))
    c5 = bc.out_of_plane_coefficient_c_eq112(0.7, 1.0, 5.0)
    c10 = bc.out_of_plane_coefficient_c_eq113(10.0, 0.8, 0.9)
    assert bc.out_of_plane_coefficient_c_eq114(7.5, c5, c10) == pytest.approx(0.5 * (c5 + c10))
    assert bc.out_of_plane_coefficient_c(2.0, 0.7, 1.0, 0.8, 0.9, 0.9)["branch"] == "equation_112"
    assert bc.out_of_plane_coefficient_c(7.5, 0.7, 1.0, 0.8, 0.9, 0.9)["branch"] == "equation_114"
    assert bc.out_of_plane_coefficient_c(10.0, 0.7, 1.0, 0.8, 0.9, 0.9)["branch"] == "equation_113"
    assert bc.out_of_plane_coefficient_c(100.0, 0.7, 1.0, 0.8, 0.9, 0.9)["c"] == 0.3


def test_equation_115_and_clause_9_2_8_route():
    assert bc.central_compression_out_of_plane_utilization_eq115(100000.0, 0.8, 2000.0, 250.0, 1.0) == pytest.approx(0.25)
    assert bc.minor_axis_bending_route_clause_9_2_8(3.0, 2.0)["equation_115_required"] is True
    assert bc.minor_axis_bending_route_clause_9_2_8(2.0, 2.0)["equation_115_required"] is False


def test_equations_116_to_119_and_additional_routes():
    phi = bc.biaxial_stability_coefficient_eq117(0.6, 0.5)
    assert phi == pytest.approx(0.6 * (0.6 * 0.5 ** (1.0 / 3.0) + 0.4 * 0.5 ** 0.25))
    assert bc.biaxial_beam_column_utilization_eq116(100000.0, phi, 3000.0, 250.0, 1.0) == pytest.approx(100000.0 / (phi * 750000.0))
    assert bc.relative_eccentricity_x_eq118(20.0, 3000.0, 500000.0) == pytest.approx(0.12)
    assert bc.relative_eccentricity_y_eq119(10.0, 3000.0, 250000.0) == pytest.approx(0.12)
    route = bc.biaxial_additional_checks_clause_9_2_9(0.5, 1.0, 3.0, 2.0)
    assert route["equation_109_with_ey_zero_required"] is True
    assert route["equation_111_with_ey_zero_required"] is True
    assert bc.adjusted_relative_eccentricity_x_clause_9_2_9(2.0, False, "1") == 2.5
    assert bc.adjusted_relative_eccentricity_x_clause_9_2_9(2.0, False, "3") == 2.0


def test_equations_120_to_122_and_major_axis_substitution():
    assert bc.box_delta_eq122(100000.0, 1.0, 3000.0, 250.0) == 1.0
    delta = bc.box_delta_eq122(100000.0, 2.0, 3000.0, 250.0)
    assert delta == pytest.approx(1.0 - 0.1 * 100000.0 * 4.0 / 750000.0)
    phi = bc.box_major_axis_phi_clause_9_2_10(True, True, 0.7, 0.8)
    assert phi == 0.8
    expected_x = 100000.0 / (phi * 3000.0 * 250.0) + 10e6 / (1.1 * delta * 500000.0 * 250.0)
    assert bc.box_major_axis_utilization_eq120(100000.0, phi, 3000.0, 250.0, 1.0, 10e6, 1.1, delta, 500000.0) == pytest.approx(expected_x)
    expected_y = 100000.0 / (0.7 * 3000.0 * 250.0) + 5e6 / (1.2 * delta * 250000.0 * 250.0)
    assert bc.box_minor_axis_utilization_eq121(100000.0, 0.7, 3000.0, 250.0, 1.0, 5e6, 1.2, delta, 250000.0) == pytest.approx(expected_y)
    with pytest.raises(ValueError):
        bc.box_delta_eq122(1e9, 10.0, 100.0, 100.0)


def test_table_20_all_branches_and_boundaries():
    assert bc.table_20_design_moment(100.0, 60.0, 70.0, 2.0, 2.0) == pytest.approx(80.0)
    assert bc.table_20_design_moment(100.0, 60.0, 70.0, 3.0, 4.0) == 60.0
    assert bc.table_20_design_moment(100.0, 60.0, 70.0, 11.5, 2.0) == pytest.approx(85.0)
    assert bc.table_20_design_moment(100.0, 60.0, 70.0, 11.5, 4.0) == pytest.approx(80.0)
    with pytest.raises(ValueError):
        bc.table_20_design_moment(100.0, 40.0, 70.0, 2.0, 2.0)


def test_table_21_alpha_beta_all_types():
    for section_type in ("1", "2", "3"):
        assert bc.table_21_alpha(section_type, 1.0, None) == 0.7
        assert bc.table_21_alpha(section_type, 5.0, None) == 0.9
        assert bc.table_21_beta(section_type, 3.14, 0.6, 0.7, None) == 1.0
        assert bc.table_21_beta(section_type, 4.0, 0.6, 0.7, None) == pytest.approx(math.sqrt(0.7 / 0.6))
    assert bc.table_21_alpha("4", 1.0, 0.5) == 0.85
    assert bc.table_21_alpha("4", 5.0, 0.5) == 0.95
    assert bc.table_21_beta("4", 4.0, 0.6, 0.7, 0.4) == 1.0
    root = math.sqrt(0.7 / 0.6)
    assert bc.table_21_beta("4", 4.0, 0.6, 0.7, 0.75) == pytest.approx(1.0 - (1.0 - root) * 0.5)


def test_annex_d2_all_section_type_families():
    values = {
        "1": bc.annex_d2_shape_influence_coefficient("1", 2.0, 3.0, None, None),
        "2": bc.annex_d2_shape_influence_coefficient("2", 2.0, 3.0, None, None),
        "3": bc.annex_d2_shape_influence_coefficient("3", 2.0, 3.0, None, None),
        "4": bc.annex_d2_shape_influence_coefficient("4", 2.0, 3.0, None, None),
        "5": bc.annex_d2_shape_influence_coefficient("5", 2.0, 3.0, 0.5, None),
        "6": bc.annex_d2_shape_influence_coefficient("6", 2.0, 3.0, 0.5, 0.1),
        "7": bc.annex_d2_shape_influence_coefficient("7", 2.0, 3.0, 0.5, 0.1),
        "8": bc.annex_d2_shape_influence_coefficient("8", 2.0, 3.0, 0.5, None),
        "9": bc.annex_d2_shape_influence_coefficient("9", 2.0, 3.0, 0.5, None),
        "10": bc.annex_d2_shape_influence_coefficient("10", 2.0, 3.0, 1.0, None),
        "11": bc.annex_d2_shape_influence_coefficient("11", 2.0, 3.0, 1.0, None),
    }
    assert all(value > 0.0 for value in values.values())
    assert values["1"] == 1.0
    with pytest.raises(ValueError):
        bc.annex_d2_shape_influence_coefficient("5", 2.0, 3.0, 0.75, None)


def test_all_annex_d3_cells_match_json():
    table = DATA["tables"]["D3"]
    count = 0
    for lambda_key, row in table["rows"].items():
        for m_key, raw in row.items():
            expected = raw / table["scale_divisor"]
            assert bc.annex_d3_table_coefficient(float(lambda_key), float(m_key)) == expected
            assert bc.annex_d3_stability_coefficient(float(lambda_key), float(m_key), 1.0) == expected
            count += 1
    assert count == 367
    assert bc.annex_d3_stability_coefficient(1.5, 1.0, 0.5) == 0.5


def test_all_annex_d4_cells_match_json():
    table = DATA["tables"]["D4"]
    count = 0
    for lambda_key, row in table["rows"].items():
        for m_key, raw in row.items():
            expected = raw / table["scale_divisor"]
            assert bc.annex_d4_table_coefficient(float(lambda_key), float(m_key)) == expected
            assert bc.annex_d4_stability_coefficient(float(lambda_key), float(m_key), 1.0) == expected
            count += 1
    assert count == 297
    assert bc.annex_d4_stability_coefficient(1.5, 1.0, 0.3) == 0.3


def test_all_annex_d5_cells_match_json():
    table = DATA["tables"]["D5"]
    count = 0
    for delta_key, lambda_rows in table["rows"].items():
        for lambda_key, row in lambda_rows.items():
            for m_key, expected in row.items():
                assert bc.annex_d5_effective_relative_eccentricity(float(delta_key), float(lambda_key), float(m_key)) == expected
                count += 1
    assert count == 308
    assert bc.annex_d5_effective_relative_eccentricity(0.0, 1.0, 4.0) == 2.55


def test_annex_d6_metadata_exists():
    for section_type in ("1", "2", "3", "4"):
        row = bc.annex_d6_section_parameters(section_type)
        assert row["alpha_star"]
        assert row["beta_star"]


def test_annex_d_equations_d1_d2_and_d4():
    params = bc.annex_d_open_section_parameters_eq_d2(0.0, 0.0, 8e6, 2e6, 4e10, 1e4, 50.0, 3000.0, 300.0, 0.0)
    assert params["rho"] == pytest.approx((8e6 + 2e6) / (3000.0 * 300.0**2))
    assert bc.annex_d_open_section_cmax_eq_d1({"delta": 1.0, "B": 1.0, "mu": 4.0, "alpha": 0.0, "eccentricity_ratio": 0.0}) == 1.0
    expected = (1.0 + 8e6 / 2e6 + 20.0 / 9.87) / (1.0 + 4.0 * ((50.0**2 + 25.0**2) / 300.0**2))
    assert bc.annex_d_continuous_bracing_cmax_eq_d4(8e6, 2e6, 50.0, 25.0, 300.0, 0.0, 20.0) == pytest.approx(expected)


def test_clause_9_2_6_moment_selection():
    assert bc.design_moment_clause_9_2_6("laterally_restrained_ends", 100.0, 40.0, 0.0, 0.0) == 50.0
    assert bc.design_moment_clause_9_2_6("laterally_restrained_ends", 100.0, 70.0, 0.0, 0.0) == 70.0
    assert bc.design_moment_clause_9_2_6("cantilever", 0.0, 0.0, 80.0, 90.0) == 90.0


def test_clause_routes():
    assert bc.stability_check_route_clause_9_2_1(True) == {"in_plane_required": True, "out_of_plane_required": True}
    assert bc.beam_column_section_9_2_route(2.0, True, True, False)["route"] == "equations_120_to_122"
    assert bc.beam_column_section_9_2_route(2.0, False, False, True)["route"] == "equations_116_to_119"
    with pytest.raises(ValueError):
        bc.beam_column_section_9_2_route(2.0, False, True, True)


def test_validation_regression_d2_type5_ratio_ge1_uses_0_02_coefficient():
    lam=1.61095111
    m=4.83990898
    expected=(1.90-0.1*m)-0.02*(6.0-m)*lam
    assert bc.annex_d2_shape_influence_coefficient("5",lam,m,1.0,0.125)==pytest.approx(expected)

def test_clause_9_2_9_meff_y_gt20_keeps_independent_lambda_trigger():
    route=bc.biaxial_additional_checks_clause_9_2_9(25.8495,4.83991,46.6898,0.07681)
    assert route["equation_116_required"] is False
    assert route["section_8_y_route_required"] is True
    assert route["equation_109_with_ey_zero_required"] is True
