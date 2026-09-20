import json
import math
from pathlib import Path

import pytest

from standard_core import bending_member_local_stability as bls
from standard_core.runner import run_case

from standard_core.release_metadata import RELEASE_STAGE

ROOT = Path(__file__).resolve().parents[1]


def test_equations_78_84():
    assert bls.bending_normal_stress_eq78(1e8, 300, 2e8) == pytest.approx(150.0)
    assert bls.average_web_shear_stress_eq79(200000, 10, 1000) == pytest.approx(20.0)
    sigma_cr = bls.critical_normal_web_stress_eq81(30, 355, 3)
    assert sigma_cr == pytest.approx(30 * 355 / 9)
    sigma_loc_cr = bls.critical_local_web_stress_eq82(28.5, 1.56, 355, 3)
    assert sigma_loc_cr == pytest.approx(28.5 * 1.56 * 355 / 9)
    tau_cr = bls.critical_web_shear_stress_eq83(2, 205, 3)
    assert tau_cr == pytest.approx(10.3 * (1 + 0.76 / 4) * 205 / 9)
    assert bls.flange_restraint_parameter_eq84(0.75, 320, 960, 24, 12) == pytest.approx(2.0)
    utilization = bls.symmetric_web_buckling_utilization_eq80(50, 10, 20, 200, 100, 80, 1.0)
    assert utilization == pytest.approx(math.sqrt((50 / 200 + 10 / 100) ** 2 + (20 / 80) ** 2))


def test_equations_78_84_boundaries_and_units():
    assert bls.average_web_shear_stress_eq79(0, 10, 1000) == 0
    assert bls.symmetric_web_buckling_utilization_eq80(0, 0, 0, 1, 1, 1, 1) == 0
    with pytest.raises(ValueError):
        bls.average_web_shear_stress_eq79(-1, 10, 1000)
    with pytest.raises(ValueError):
        bls.critical_web_shear_stress_eq83(0.9, 205, 3)
    with pytest.raises(ValueError):
        bls.flange_restraint_parameter_eq84(0.8, 300, 0, 20, 10)


def test_equations_85_88():
    eta85 = bls.asymmetric_tension_flange_web_utilization_eq85(200, -100, 30, 300, 100, 20, 1.0)
    alpha = 1.5
    beta = (300 / 200) * (30 / 100)
    expected = 0.5 * 200 * (2 - alpha + math.sqrt(alpha**2 + 4 * beta**2)) / 300
    assert eta85 == pytest.approx(expected)
    eta86 = bls.class_2_3_symmetric_web_utilization_eq86(1e9, 355, 1, 1000, 10, 0.5, 1, 0.2)
    assert eta86 == pytest.approx(1e9 / (355 * 1000**2 * 10 * 0.7))
    h1 = bls.compressed_web_zone_height_eq88(10000, 10, 4000, 100, 5000, 150, 355, 50)
    assert math.isfinite(h1)
    eta87 = bls.class_2_3_asymmetric_web_utilization_eq87(1e9, 200, 5000, 400, 100, 4000, 1000, 10, 0.2, 355, 50, 1)
    assert eta87 > 0


def test_equations_85_88_domain_checks():
    with pytest.raises(ValueError):
        bls.compressed_web_zone_height_eq88(10000, 10, 4000, 100, 5000, 150, 100, 60)
    with pytest.raises(ValueError):
        bls.class_2_3_asymmetric_web_utilization_eq87(1, 1, 1, 1000, 1, 1, 1000, 10, 0.2, 355, 10, 1)


def test_equations_89_96():
    assert bls.upper_plate_utilization_eq89(50, 10, 20, 200, 100, 80, 1) == pytest.approx(50 / 200 + 10 / 100 + (20 / 80) ** 2)
    assert bls.upper_plate_critical_normal_no_local_eq90(355, 2, 200, 1000) == pytest.approx(4.76 * 355 / (0.8 * 4))
    assert bls.upper_plate_critical_normal_with_local_eq91(4, 355, 2, 200, 1000) == pytest.approx(1.19 * 4 * 355 / (0.8 * 4))
    assert bls.upper_plate_critical_local_eq92(6.25, 2, 355, 3) == pytest.approx(6.25 * (1.24 + 0.476 * 2) * 355 / 9)
    bundle = bls.upper_plate_psi_and_slenderness_eq93(400, 200, 10, 355, 206000)
    assert bundle["mu1_used"] == 2.0
    assert bundle["psi"] == pytest.approx(6.25)
    eta94 = bls.lower_plate_utilization_eq94(50, 5, 20, 200, 1000, 200, 100, 80, 1)
    expected = math.sqrt((50 * 0.6 / 200 + 5 / 100) ** 2 + (20 / 80) ** 2)
    assert eta94 == pytest.approx(expected)
    assert bls.lower_plate_critical_normal_eq95(355, 2, 200, 1000) == pytest.approx(5.43 * 355 / ((0.3) ** 2 * 4))
    assert bls.lower_plate_relative_slenderness_eq96(800, 10, 355, 206000) == pytest.approx(80 * math.sqrt(355 / 206000))


def test_equations_89_96_boundaries():
    assert bls.upper_plate_utilization_eq89(0, 0, 0, 1, 1, 1, 1) == 0
    with pytest.raises(ValueError):
        bls.upper_plate_critical_normal_no_local_eq90(355, 2, 1000, 1000)
    with pytest.raises(ValueError):
        bls.upper_plate_critical_local_eq92(4, 2.1, 355, 3)
    with pytest.raises(ValueError):
        bls.lower_plate_critical_normal_eq95(355, 2, 500, 1000)


def test_equations_97_100():
    assert bls.flange_outstand_limit_eq97(355, 200) == pytest.approx(0.5 * math.sqrt(355 / 200))
    assert bls.box_flange_plate_limit_eq98(355, 200) == pytest.approx(1.5 * math.sqrt(355 / 200))
    assert bls.class_2_3_flange_outstand_limit_eq99(3.0) == pytest.approx(0.35)
    assert bls.class_2_3_box_flange_limit_eq100(3.0) == pytest.approx(1.125)
    assert bls.class_2_3_flange_outstand_limit_eq99(1.0) == pytest.approx(0.17 + 0.06 * 2.2)
    assert bls.class_2_3_box_flange_limit_eq100(10.0) == pytest.approx(0.675 + 0.15 * 5.5)


def test_tables_14_to_18():
    assert bls.table_14_c1(0.10, 1.0) == 28.5
    assert bls.table_14_c1(0.40, 2.5) == 6.1
    assert bls.table_15_c2(0.5, 1.0) == 1.56
    assert bls.table_15_c2(40, 2.0) == 2.52
    assert bls.table_16_c_cr(0.8, 34.6) == 34.6
    assert bls.table_16_c_cr(1.4, 34.6) == 52.8
    assert bls.table_16_c_cr(3.0, 34.6) == 84.7
    assert bls.table_17_c_cr(1.4) == 15.5
    assert bls.table_18_alpha(0.5, 3.0) == 0.197
    with pytest.raises(ValueError):
        bls.table_14_c1(0.12, 1.0)
    with pytest.raises(ValueError):
        bls.table_18_alpha(0.55, 3.0)


def test_table_19_and_procedures():
    result = bls.table_19_stiffener_inertias(0.25, 1000, 1000, 10)
    assert result["transverse_required_mm4"] == pytest.approx(3_000_000)
    assert result["longitudinal_required_mm4"] == pytest.approx(1_100_000)
    mid = bls.table_19_stiffener_inertias(0.225, 1000, 1000, 10)
    assert mid["longitudinal_required_mm4"] == pytest.approx((2_000_000 + 1_100_000) / 2)
    assert bls.preliminary_web_check_exemption_8_5_1(3.0, False, True)["detailed_check_may_be_omitted"]
    req = bls.transverse_stiffener_requirements_8_5_9(1, 3.3, False, False, 1000)
    assert req["required"] and req["maximum_spacing_mm"] == pytest.approx(2000)
    dims = bls.transverse_stiffener_dimensions_8_5_9(1000, 355, 206000, False)
    assert dims["minimum_projection_mm"] == pytest.approx(1000 / 30 + 25)
    load = bls.concentrated_load_stiffener_effective_section_8_5_10(10, 206000, 355, 1000, False)
    assert load["model"] == "centrally_compressed_column"
    assert bls.longitudinal_stiffener_required_8_5_11(8, 355, 200, False)["required"]
    assert bls.flexible_web_route_8_5_16(9, 355, 200)["external_flexible_web_rules_required"]
    support = bls.support_stiffener_effective_section_8_5_17(10, 206000, 355, 1000, 300, 160)
    assert support["projection_ok"]
    edge = bls.edge_stiffened_flange_limit_8_5_20(0.5, 40, 100, 5, 355, 206000)
    assert edge["eligible"] and edge["modified_limit"] == pytest.approx(0.75)


def test_table_19_domains_and_unstated_cases():
    with pytest.raises(ValueError):
        bls.table_19_stiffener_inertias(0.19, 1000, 1000, 10)
    with pytest.raises(ValueError):
        bls.preliminary_web_check_exemption_8_5_1(2.0, True, False)


def test_data_file_contains_all_tables():
    data = json.loads((ROOT / "data/tables_14_to_19_bending_local_stability.json").read_text(encoding="utf-8"))
    assert all(f"table_{i}" in data for i in range(14, 20))
    assert len(data["table_14"]["values"]) == 7
    assert len(data["table_18"]["values"]) == 6


def test_schema_and_runner_writes_outputs(tmp_path):
    result = run_case(ROOT / "examples/bending_member_local_stability_example.json", ROOT)
    assert result["release_stage"] == RELEASE_STAGE
    assert result["results"]["equation_80_web_utilization"] >= 0
    assert (ROOT / "outputs/bending_member_local_stability_result.json").exists()
    assert (ROOT / "reports/bending_member_local_stability_case_report.md").exists()


def test_clause_specific_routing_helpers() -> None:
    route = bls.panel_check_routing_8_5_5(1.0, True)
    assert route["number_of_checks"] == 2
    assert route["checks"][1]["ratio_for_c1_c2"] == pytest.approx(0.5)

    route_large = bls.panel_check_routing_8_5_5(2.0, True)
    assert route_large["checks"][1]["ratio_for_c1_c2"] == pytest.approx(0.67)

    asym = bls.asymmetric_compressed_flange_substitution_8_5_6(1000.0, 350.0)
    assert asym["substituted_height_mm"] == pytest.approx(700.0)

    intermediate = bls.intermediate_stiffener_panel_length_8_5_13(1200.0, 400.0)
    assert intermediate["plate_1_length_mm"] == pytest.approx(400.0)
    assert intermediate["plate_2_route"] == "clause_8.5.12_b"

    substitutions = bls.asymmetric_split_web_substitutions_8_5_14(
        sigma_1_n_mm2=200.0,
        sigma_2_n_mm2=-100.0,
        plate_1_height_mm=200.0,
        effective_web_height_mm=1000.0,
    )
    assert substitutions["upper_ratio_replacement"] == pytest.approx(0.15)
    assert substitutions["lower_denominator_replacement"] == pytest.approx(200.0 / 300.0 - 0.2)

    milled_bearing = bls.support_stiffener_end_resistance_8_5_17(
        end_arrangement="milled_end",
        projection_a_mm=12.0,
        plate_thickness_mm=10.0,
        bearing_resistance_n_mm2=400.0,
        compression_resistance_n_mm2=300.0,
    )
    assert milled_bearing["resistance_type"] == "bearing"

    milled_compression = bls.support_stiffener_end_resistance_8_5_17(
        end_arrangement="milled_end",
        projection_a_mm=20.0,
        plate_thickness_mm=10.0,
        bearing_resistance_n_mm2=400.0,
        compression_resistance_n_mm2=300.0,
    )
    assert milled_compression["resistance_type"] == "compression"

    remote = bls.support_stiffener_end_resistance_8_5_17(
        end_arrangement="fitted_or_welded_remote",
        projection_a_mm=20.0,
        plate_thickness_mm=10.0,
        bearing_resistance_n_mm2=400.0,
        compression_resistance_n_mm2=300.0,
    )
    assert remote["resistance_type"] == "bearing"
