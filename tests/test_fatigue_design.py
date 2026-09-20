import math

import pytest

from standard_core import fatigue_design as fd


def test_table35_catalog_exists():
    data = fd.table_35_catalog()
    assert data["standard"] == "СП 16.13330.2017"
    assert len(data["steel_bins"]) == 5


def test_table35_all_values():
    group1 = [120, 128, 132, 136, 145]
    group2 = [100, 106, 108, 110, 116]
    run_nodes = [420, 440, 520, 580, 675]
    assert [fd.fatigue_design_resistance_table35(1, x) for x in run_nodes] == group1
    assert [fd.fatigue_design_resistance_table35(2, x) for x in run_nodes] == group2
    assert [fd.fatigue_design_resistance_table35(g, 355) for g in range(3, 9)] == [90, 75, 60, 45, 36, 27]


def test_table35_bin_boundaries():
    assert fd.fatigue_design_resistance_table35(1, 420.0) == 120.0
    assert fd.fatigue_design_resistance_table35(1, 420.0001) == 128.0
    assert fd.fatigue_design_resistance_table35(2, 580.0001) == 116.0


def test_table35_outside_range_rejected_for_groups_1_2():
    with pytest.raises(ValueError):
        fd.fatigue_design_resistance_table35(1, 675.1)


def test_table35_invalid_group_rejected():
    with pytest.raises(ValueError):
        fd.fatigue_design_resistance_table35(9, 355.0)


def test_eq171_normal():
    assert fd.cycle_factor_group_1_2_eq171(1_000_000) == pytest.approx(1.314)


def test_eq171_lower_boundary():
    expected = 0.064 * 0.1**2 - 0.5 * 0.1 + 1.75
    assert fd.cycle_factor_group_1_2_eq171(100_000) == pytest.approx(expected)


def test_eq171_upper_branch_rejected():
    with pytest.raises(ValueError):
        fd.cycle_factor_group_1_2_eq171(3_900_000)


def test_eq172_normal():
    assert fd.cycle_factor_group_3_8_eq172(1_000_000) == pytest.approx(1.63)


def test_eq172_lower_boundary():
    expected = 0.07 * 0.1**2 - 0.64 * 0.1 + 2.2
    assert fd.cycle_factor_group_3_8_eq172(100_000) == pytest.approx(expected)


def test_eq172_upper_branch_rejected():
    with pytest.raises(ValueError):
        fd.cycle_factor_group_3_8_eq172(3_900_000)


def test_cycle_factor_routing():
    assert fd.fatigue_cycle_factor_alpha(1_000_000, 1) == pytest.approx(1.314)
    assert fd.fatigue_cycle_factor_alpha(1_000_000, 4) == pytest.approx(1.63)
    assert fd.fatigue_cycle_factor_alpha(3_900_000, 1) == 0.77
    assert fd.fatigue_cycle_factor_alpha(10_000_000, 8) == 0.77


def test_cycle_factor_below_ordinary_fatigue_range_rejected():
    with pytest.raises(ValueError):
        fd.fatigue_cycle_factor_alpha(99_999, 4)


def test_stress_asymmetry_ratio():
    assert fd.stress_asymmetry_ratio(100.0, -50.0) == -0.5
    assert fd.stress_asymmetry_ratio(-100.0, -20.0) == 0.2


def test_stress_asymmetry_ordering_rejected():
    with pytest.raises(ValueError):
        fd.stress_asymmetry_ratio(50.0, 60.0)


def test_table36_piecewise_values():
    assert fd.fatigue_asymmetry_factor_table36(100.0, -100.0) == pytest.approx(1.0)
    assert fd.fatigue_asymmetry_factor_table36(100.0, 0.0) == pytest.approx(2.5 / 1.5)
    assert fd.fatigue_asymmetry_factor_table36(100.0, 80.0) == pytest.approx(5.0)
    assert fd.fatigue_asymmetry_factor_table36(100.0, 90.0) == pytest.approx(10.0)
    assert fd.fatigue_asymmetry_factor_table36(-100.0, 0.0) == pytest.approx(2.0)
    assert fd.fatigue_asymmetry_factor_table36(-100.0, 50.0) == pytest.approx(4.0 / 3.0)


def test_table36_rho_one_rejected():
    with pytest.raises(ValueError):
        fd.fatigue_asymmetry_factor_table36(100.0, 100.0)


def test_eq170_normal():
    assert fd.fatigue_utilization_eq170(50.0, 1.25, 100.0, 2.0) == pytest.approx(0.2)


def test_eq170_zero_boundary():
    assert fd.fatigue_utilization_eq170(0.0, 1.0, 100.0, 1.0) == 0.0


def test_eq170_negative_demand_rejected():
    with pytest.raises(ValueError):
        fd.fatigue_utilization_eq170(-1.0, 1.0, 100.0, 1.0)


def test_resistance_cap_check():
    passed = fd.fatigue_resistance_cap_check_clause_12_1_2(1.0, 100.0, 1.0, 400.0, 1.3)
    failed = fd.fatigue_resistance_cap_check_clause_12_1_2(2.0, 200.0, 1.0, 400.0, 1.3)
    assert passed["pass"] is True
    assert failed["pass"] is False
    assert failed["cap_utilization"] > 1.0


def test_fatigue_applicability_route():
    assert fd.fatigue_applicability_route_clause_12_1_1_12_1_3(100_000)["ordinary_fatigue_required"] is True
    low = fd.fatigue_applicability_route_clause_12_1_1_12_1_3(99_999)
    assert low["route"] == "external_low_cycle_fatigue_rules"
    resonant_low = fd.fatigue_applicability_route_clause_12_1_1_12_1_3(10, True)
    assert resonant_low["ordinary_fatigue_required"] is False
    assert resonant_low["resonant_vortex_fatigue_assessment_required"] is True
    assert resonant_low["clause_12_1_3_current_status"] == "EXCLUDED_FROM_2025_01_10_CHANGE_6"


def test_annex_k_catalog_complete():
    data = fd.annex_k_catalog()
    assert len(data["entries"]) == 35
    assert {entry["group"] for entry in data["entries"]} == set(range(1, 9))
    assert {entry["page"] for entry in data["entries"]} == {177, 178, 179, 180, 181}


def test_annex_k_lookup():
    assert fd.annex_k_group("K1-16-TRANSVERSE_WELD_SMOOTH") == 4
    assert fd.annex_k_group("K1-19-DOUBLE_FLANK_WELDS") == 8
    with pytest.raises(ValueError):
        fd.annex_k_group("K1-UNKNOWN")


def test_annex_k_tube_case20_boundaries():
    assert fd.annex_k_tube_joint_group_case20(1 / 14)["group"] == 7
    assert fd.annex_k_tube_joint_group_case20(1 / 20)["group"] == 8
    with pytest.raises(ValueError):
        fd.annex_k_tube_joint_group_case20(1 / 21)


def test_annex_k_tube_case21_boundaries():
    assert fd.annex_k_tube_joint_group_case21(0.4, 1 / 14)["group"] == 6
    assert fd.annex_k_tube_joint_group_case21(0.7, 1 / 20)["group"] == 7
    assert fd.annex_k_tube_joint_group_case21(0.5, 1 / 35)["group"] == 8
    with pytest.raises(ValueError):
        fd.annex_k_tube_joint_group_case21(0.39, 1 / 14)
    with pytest.raises(ValueError):
        fd.annex_k_tube_joint_group_case21(0.5, 1 / 36)


def test_crane_cycle_factor():
    assert fd.crane_runway_cycle_factor_clause_12_2("8K", False) == 0.77
    assert fd.crane_runway_cycle_factor_clause_12_2("7К", True) == 0.77
    assert fd.crane_runway_cycle_factor_clause_12_2("7K", False) == 1.1
    assert fd.crane_runway_cycle_factor_clause_12_2("6K", True) == 1.1


def test_crane_web_resistance_values():
    assert fd.crane_runway_web_fatigue_resistance_clause_12_2("welded", "compression") == 75.0
    assert fd.crane_runway_web_fatigue_resistance_clause_12_2("friction", "compression") == 96.0
    assert fd.crane_runway_web_fatigue_resistance_clause_12_2("welded", "tension") == 65.0
    assert fd.crane_runway_web_fatigue_resistance_clause_12_2("friction", "tension") == 89.0


def test_eq173_normal():
    expected = (0.5 * math.sqrt(40.0**2 + 0.36 * 20.0**2) + 0.4 * 10.0 + 0.5 * 5.0) / 75.0
    assert fd.crane_runway_web_fatigue_utilization_eq173(40.0, 20.0, 10.0, 5.0, 75.0) == pytest.approx(expected)


def test_eq173_zero_boundary():
    assert fd.crane_runway_web_fatigue_utilization_eq173(0.0, 0.0, 0.0, 0.0, 75.0) == 0.0


def test_eq173_negative_component_rejected():
    with pytest.raises(ValueError):
        fd.crane_runway_web_fatigue_utilization_eq173(-1.0, 0.0, 0.0, 0.0, 75.0)
