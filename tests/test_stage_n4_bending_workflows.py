from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from standard_core import bending_members as bend
from standard_core.bending_workflows import bending_member_guided_workflow
from standard_core.runner import _prepare_case_for_validation, run_case

ROOT = Path(__file__).resolve().parents[1]


def _raw() -> dict:
    return json.loads((ROOT / "examples/bending_member_guided_example.json").read_text(encoding="utf-8"))


def _prepared() -> dict:
    case, _, _ = _prepare_case_for_validation(_raw(), ROOT)
    return case


def test_n4_guided_example_resolves_n1_n2_and_runs_end_to_end():
    result = run_case(ROOT / "examples/bending_member_guided_example.json", ROOT)
    assert result["action"] == "bending_member_guided"
    assert result["resolution_trace"]["profile"]["shape_group"] == "I_ROLLED_DSYMM"
    assert result["resolution_trace"]["material"]["resolved_values"]["elastic_modulus_n_mm2"] == 206000.0
    assert result["results"]["strength"]["route"] == "8.2.1_EQ41_X"
    assert result["results"]["strength"]["shear_route"] == "8.2.1_EQ42"
    assert result["results"]["lateral_stability"]["mode"] == "calculate_phi_b"
    assert result["results"]["local_stability"]["mode"] == "geometry_and_stiffener_screen"


def test_n4_guided_example_expected_numerical_trace():
    r = bending_member_guided_workflow(_prepared())
    assert r["strength"]["strength_utilization"] == pytest.approx(1.05850908994681)
    assert r["strength"]["shear_utilization"] == pytest.approx(0.44146454117079015)
    assert r["lateral_stability"]["alpha_eq_zh4"] == pytest.approx(30.593890679353393)
    assert r["lateral_stability"]["psi"] == pytest.approx(4.391572347554738)
    assert r["lateral_stability"]["phi_1"] == pytest.approx(2.4955337676595235)
    assert r["lateral_stability"]["phi_b"] == 1.0
    assert r["governing_utilization"] == pytest.approx(1.05850908994681)
    assert r["pass"] is False


def test_n4_equation_61_is_current_sp16_and_legacy_parameter_is_inert():
    expected = (0.7 * 1.3 + 0.25 - 0.0833 / 1.3**2) / (0.7 + 0.167)
    a = bend.bimetal_major_axis_coefficient_eq61(999.0, 0.7, 1.3)
    b = bend.bimetal_major_axis_coefficient_eq61(0.01, 0.7, 1.3)
    assert a == pytest.approx(expected)
    assert b == pytest.approx(expected)


def test_n4_class1_biaxial_requires_point_data_for_eq43():
    case = _prepared()
    case["moment_y_n_mm"] = 10e6
    with pytest.raises(ValueError, match=r"equation \(43\) point data"):
        bending_member_guided_workflow(case)


def test_n4_rigid_deck_exempts_lateral_stability():
    case = _prepared()
    case["lateral_stability"] = {"mode": "rigid_deck_exemption"}
    r = bending_member_guided_workflow(case)
    assert r["lateral_stability"]["pass"] is True
    assert r["lateral_stability"]["exemption"]["exempt"] is True


def test_n4_not_assessed_lateral_is_explicit_not_silent_pass():
    case = _prepared()
    case["lateral_stability"] = {"mode": "not_assessed"}
    r = bending_member_guided_workflow(case)
    assert r["lateral_stability"]["pass"] is None
    assert r["lateral_stability"]["status"] == "SEPARATE_ASSESSMENT_REQUIRED"


def test_n4_phi_b_route_requires_confirmed_rolled_i():
    case = _prepared()
    case["rolled_i_section_confirmed"] = False
    with pytest.raises(ValueError, match="doubly symmetric rolled I"):
        bending_member_guided_workflow(case)


def test_n4_phi_b_uses_design_Ry_not_Ryn():
    case = _prepared()
    base = bending_member_guided_workflow(case)["lateral_stability"]["phi_1"]
    case["normative_yield_resistance_n_mm2"] *= 0.5
    unchanged = bending_member_guided_workflow(case)["lateral_stability"]["phi_1"]
    assert unchanged == pytest.approx(base)
    case["design_yield_resistance_n_mm2"] *= 0.5
    changed = bending_member_guided_workflow(case)["lateral_stability"]["phi_1"]
    assert changed == pytest.approx(base * 2.0)


def test_n4_local_stability_screen_is_explicitly_screen_only():
    case = _prepared()
    r = bending_member_guided_workflow(case)["local_stability"]
    assert r["status"] == "SCREEN_ONLY_FULL_8_5_INTERACTION_REMAINS_SEPARATE"
    assert r["pass"] is None
    assert r["preliminary_8_5_1"]["detailed_check_may_be_omitted"] is True


def test_n4_crane_runway_routes_to_specialized_action():
    case = _prepared()
    case["beam_category"] = "crane_runway"
    r = bending_member_guided_workflow(case)
    assert r["strength"]["route"] == "SPECIALIZED_ACTION_REQUIRED"
    assert r["strength"]["specialized_action"] == "crane_runway_and_bending_stability"


def test_n4_bimetal_routes_to_detailed_action():
    case = _prepared()
    case["beam_category"] = "bimetal"
    r = bending_member_guided_workflow(case)
    assert r["strength"]["route"] == "SPECIALIZED_ACTION_REQUIRED"
    assert r["strength"]["specialized_action"] == "bending_member_strength"


def test_n4_class2_selects_eq50_only_when_explicitly_applicable():
    case = _prepared()
    case["member_class"] = 2
    case["lateral_stability"] = {"mode": "not_assessed"}
    case["local_stability"] = {"mode": "not_assessed"}
    case["one_flange_area_mm2"] = 1500.0
    case["web_area_mm2"] = 2000.0
    case["flange_to_web_area_ratio"] = 0.75
    case["plastic"] = {
        "section_family": "i_section",
        "table_e1_section_type": "1",
        "equivalent_load_safety_factor": 1.0,
        "required_clause_checks_confirmed": True,
        "is_support_section": False,
    }
    # Use a low shear level so Eq.52 remains in its unreduced branch.
    case["shear_force_x_n"] = 1000.0
    case["shear_force_y_n"] = 0.0
    try:
        r = bending_member_guided_workflow(case)
    except ValueError as exc:
        # If the canonical E.1 key is not i_section in this release, fail with useful context.
        pytest.fail(str(exc))
    assert r["strength"]["route"] == "8.2.3_EQ50"
    assert r["strength"]["strength_utilization"] >= 0.0


def test_n4_reference_hydration_validates_before_strict_schema():
    raw = _raw()
    assert "minimum_net_section_modulus_x_mm3" not in raw
    prepared, schema, trace = _prepare_case_for_validation(raw, ROOT)
    assert prepared["minimum_net_section_modulus_x_mm3"] > 0.0
    assert prepared["design_yield_resistance_n_mm2"] > 0.0
    assert trace["profile"]["catalog_status"].startswith("INTERIM_IMPORTED_FROM_NORMCAD")
    assert schema["$id"] == "bending_member_guided_case.schema.json"
