from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core import fatigue_design as s12
from standard_core import fatigue_workflows as n9w
from standard_core.runner import _prepare_case_for_validation

ROOT = Path(__file__).resolve().parents[1]


def _ordinary(**updates):
    route = {
        "kind": "ordinary_fatigue_12_1_2",
        "load_cycles": 1_000_000,
        "resonant_vortex_excitation": False,
        "sp20_load_basis_confirmed": True,
        "net_section_stress_without_dynamic_and_stability_coefficients_confirmed": True,
        "same_loading_for_extreme_stresses_confirmed": True,
        "annex_k_case_selection_confirmed": True,
        "annex_k_case_id": "K1-16-TRANSVERSE_WELD_SMOOTH",
        "normative_ultimate_resistance_n_mm2": 440.0,
        "design_ultimate_resistance_n_mm2": 400.0,
        "ultimate_resistance_safety_factor": 1.3,
        "maximum_signed_stress_n_mm2": 50.0,
        "minimum_signed_stress_n_mm2": -25.0,
    }
    route.update(updates)
    return {"case_id": "N9-TEST", "standard": "СП 16.13330.2017", "action": "fatigue_guided", "route": route}


def _crane(**updates):
    route = dict(_ordinary()["route"])
    route.update({
        "kind": "crane_runway_12_2",
        "crane_loads_sp20_confirmed": True,
        "crane_group": "8K",
        "crane_in_metallurgical_shop": False,
        "built_up_crane_runway_beam": False,
    })
    route.update(updates)
    return {"case_id": "N9-CRANE", "standard": "СП 16.13330.2017", "action": "fatigue_guided", "route": route}


def test_n9_current_section12_source_metadata_mentions_change6_and_excluded_12_1_3():
    assert "Changes No. 1-6 through 09.12.2024" in s12.__doc__
    assert "12.1.3 is excluded" in s12.__doc__
    assert "SP16-PROC-12.1.1-LOW-CYCLE-BOUNDARY-CURRENT" in s12.IMPLEMENTED_PROCEDURE_IDS
    assert "SP16-PROC-12.1.3-LOW-CYCLE-ROUTE" not in s12.IMPLEMENTED_PROCEDURE_IDS


def test_n9_low_cycle_boundary_is_current_change6_fail_closed():
    case = _ordinary(kind="low_cycle_lt_1e5_12_1_1", load_cycles=99_999)
    r = n9w.fatigue_guided_workflow(case)
    assert r["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert r["applicability"]["clause_12_1_3_current_status"] == "EXCLUDED_FROM_2025_01_10_CHANGE_6"
    assert "external low-cycle" in r["required"]


def test_n9_resonant_vortex_does_not_silently_enable_eq170_below_1e5():
    case = _ordinary(load_cycles=10_000, resonant_vortex_excitation=True)
    r = n9w.fatigue_guided_workflow(case)
    assert r["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert r["applicability"]["resonant_vortex_fatigue_assessment_required"] is True
    assert r["governing_utilization"] is None


def test_n9_ordinary_route_computes_table35_36_eq171_and_eq170():
    r = n9w.fatigue_guided_workflow(_ordinary())
    assert r["status"] == "COMPLETE"
    g = r["general_fatigue_check"]
    assert g["annex_k_element_group"] == 4
    assert g["table_35_fatigue_resistance_n_mm2"] == 75.0
    assert g["cycle_factor_alpha"] == pytest.approx(1.63)
    assert g["stress_asymmetry_ratio_rho"] == pytest.approx(-0.5)
    assert g["table_36_asymmetry_factor_gamma_v"] == pytest.approx(1.25)
    assert g["equation_170_utilization"] == pytest.approx(50/(1.63*75*1.25))


def test_n9_group1_uses_eq171_and_table35_run_bin():
    case = _ordinary(annex_k_case_id="K1-01-ROLLED_OR_MACHINED_EDGE", normative_ultimate_resistance_n_mm2=440.0)
    r = n9w.fatigue_guided_workflow(case)
    g = r["general_fatigue_check"]
    assert g["annex_k_element_group"] == 1
    assert g["table_35_fatigue_resistance_n_mm2"] == 128.0
    assert g["cycle_factor_alpha"] == pytest.approx(1.314)


def test_n9_at_3_9e6_alpha_is_exactly_0_77():
    r = n9w.fatigue_guided_workflow(_ordinary(load_cycles=3_900_000))
    assert r["general_fatigue_check"]["cycle_factor_alpha"] == 0.77


def test_n9_resistance_cap_failure_is_not_silently_capped():
    r = n9w.fatigue_guided_workflow(_ordinary(
        load_cycles=100_000,
        normative_ultimate_resistance_n_mm2=355.0,
        design_ultimate_resistance_n_mm2=100.0,
        ultimate_resistance_safety_factor=1.3,
    ))
    cap = r["general_fatigue_check"]["fatigue_resistance_cap_check"]
    assert cap["pass"] is False
    assert r["pass"] is False
    assert r["governing_utilization"] >= cap["cap_utilization"] > 1.0


@pytest.mark.parametrize("key", [
    "sp20_load_basis_confirmed",
    "net_section_stress_without_dynamic_and_stability_coefficients_confirmed",
    "same_loading_for_extreme_stresses_confirmed",
    "annex_k_case_selection_confirmed",
])
def test_n9_ordinary_route_fail_closed_when_required_confirmation_missing(key):
    case = _ordinary()
    del case["route"][key]
    r = n9w.fatigue_guided_workflow(case)
    assert r["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert r["governing_utilization"] is None


def test_n9_unknown_annex_k_case_rejected():
    with pytest.raises(ValueError, match="Unknown Annex K"):
        n9w.fatigue_guided_workflow(_ordinary(annex_k_case_id="K1-UNKNOWN"))


def test_n9_table35_above_675_for_groups1_2_rejected():
    with pytest.raises(ValueError, match="Run=675"):
        n9w.fatigue_guided_workflow(_ordinary(
            annex_k_case_id="K1-01-ROLLED_OR_MACHINED_EDGE",
            normative_ultimate_resistance_n_mm2=675.1,
        ))


def test_n9_zero_governing_stress_fails_closed_instead_of_inventing_rho():
    with pytest.raises(ValueError, match="must be non-zero"):
        n9w.fatigue_guided_workflow(_ordinary(maximum_signed_stress_n_mm2=0.0, minimum_signed_stress_n_mm2=0.0))


def test_n9_crane_8k_uses_clause12_2_alpha_override_not_eq171_172():
    r = n9w.fatigue_guided_workflow(_crane(crane_group="8K", load_cycles=1_000_000))
    assert r["status"] == "COMPLETE"
    assert r["crane_cycle_factor_alpha"] == 0.77
    assert r["general_fatigue_check"]["cycle_factor_alpha"] == 0.77
    assert r["general_fatigue_check"]["cycle_factor_source"] == "12.2 crane-runway alpha override"


def test_n9_crane_7k_metallurgical_is_0_77_otherwise_1_1():
    a = n9w.fatigue_guided_workflow(_crane(crane_group="7K", crane_in_metallurgical_shop=True))
    b = n9w.fatigue_guided_workflow(_crane(crane_group="7K", crane_in_metallurgical_shop=False))
    c = n9w.fatigue_guided_workflow(_crane(crane_group="6K", crane_in_metallurgical_shop=True))
    assert a["crane_cycle_factor_alpha"] == 0.77
    assert b["crane_cycle_factor_alpha"] == 1.1
    assert c["crane_cycle_factor_alpha"] == 1.1


def test_n9_crane_route_requires_sp20_crane_load_confirmation():
    case = _crane()
    del case["route"]["crane_loads_sp20_confirmed"]
    r = n9w.fatigue_guided_workflow(case)
    assert r["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert any("crane loads" in x for x in r["missing_confirmations"])


def test_n9_built_up_crane_beam_requires_equation67_stress_confirmation():
    r = n9w.fatigue_guided_workflow(_crane(built_up_crane_runway_beam=True))
    assert r["status"] == "INCOMPLETE_FAIL_CLOSED"
    assert any("equation (173) stresses" in x for x in r["unresolved_requirements"])


def test_n9_built_up_crane_beam_eq173_welded_compression():
    r = n9w.fatigue_guided_workflow(_crane(
        built_up_crane_runway_beam=True,
        equation_67_stresses_confirmed=True,
        crane_flange_connection_type="welded",
        crane_web_zone_state="compression",
        crane_sigma_x_n_mm2=40.0,
        crane_sigma_xy_n_mm2=20.0,
        crane_local_sigma_y_n_mm2=10.0,
        crane_flange_sigma_y_n_mm2=5.0,
    ))
    assert r["status"] == "COMPLETE"
    web = r["built_up_upper_web_check"]
    assert web["fatigue_resistance_n_mm2"] == 75.0
    assert web["equation_173_utilization"] == pytest.approx(s12.crane_runway_web_fatigue_utilization_eq173(40,20,10,5,75))


def test_n9_non_built_up_crane_beam_does_not_invent_eq173():
    r = n9w.fatigue_guided_workflow(_crane(built_up_crane_runway_beam=False))
    assert r["status"] == "COMPLETE"
    assert r["built_up_upper_web_check"] is None


def test_n9_guided_schema_accepts_example_and_rejects_hidden_field():
    raw = json.loads((ROOT/"examples"/"fatigue_guided_example.json").read_text(encoding="utf-8"))
    case, _, _ = _prepare_case_for_validation(raw, ROOT)
    assert case["action"] == "fatigue_guided"
    raw["route"]["hidden_default"] = 1
    with pytest.raises(ValueError, match="Unexpected property"):
        _prepare_case_for_validation(raw, ROOT)
