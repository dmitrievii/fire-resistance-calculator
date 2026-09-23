from __future__ import annotations

import pytest

from standard_core import fire_sp554_runtime as runtime
from standard_core.fire_sp554_runtime_v091 import GAMMA_CT
from standard_core.fire_sp554_runtime_v092 import (
    CANONICAL_ACTION_CONTRACT,
    SP554_V092_ROUTE_CENSUS,
)


def _base(route_name: str, route: dict) -> dict:
    return {
        "member_route": route_name,
        "steel_strength_group": "ordinary",
        "high_strength_gost9651_qualified": False,
        "fire_resistant_gost9651_qualified": False,
        "fy_norm_n_mm2": 255.0,
        "route": route,
    }


def _compression_route() -> dict:
    return {
        "N_n": 400_000.0,
        "A_gross_mm2": 5282.0,
        "gamma_c": 0.9,
        "sp16_lambda_z_geom": 35.28,
        "sp16_lambda_y_geom": 119.39,
        "sp16_l_eff_z": 3000.0,
        "sp16_l_eff_y": 6000.0,
        "sp16_i_z": 3000.0 / 35.28,
        "sp16_i_y": 6000.0 / 119.39,
        "sp16_curve_z": "b",
        "sp16_curve_y": "c",
    }


def test_v092_census_has_no_executable_sections_9_11_route_without_gamma_ct():
    assert GAMMA_CT == pytest.approx(1.1)
    assert set(SP554_V092_ROUTE_CENSUS) == {
        "central_tension",
        "central_compression",
        "bending",
        "combined_nm",
    }
    for row in SP554_V092_ROUTE_CENSUS.values():
        assert row["gamma_ct"] == pytest.approx(1.1)
        assert row["status"] in {
            "MIGRATED",
            "MIGRATED_V091",
            "FAIL_CLOSED_PENDING_CANONICAL_ACTION_MIGRATION",
        }


def test_v092_section_9_1_uses_mandatory_gamma_ct_and_needs_no_e_seed():
    case = _base(
        "central_tension",
        {
            "N_n": 400_000.0,
            "A_net_mm2": 5152.0,
            "gamma_c": 0.9,
        },
    )
    result = runtime.sp554_fire_mechanical_guided_workflow(case)
    expected = 400_000.0 / (5152.0 * 255.0 * 1.1 * 0.9)

    assert result["gamma_T_required"] == pytest.approx(expected)
    assert result["gamma_T_governing_formula_ref"] == "9.1"
    assert result["gamma_E_required"] is None
    assert result["gamma_ct"] == pytest.approx(1.1)
    details = result["gamma_T_candidates"][0]["details"]
    assert details["Ryn_n_mm2"] == pytest.approx(255.0)
    assert details["gamma_ct"] == pytest.approx(1.1)
    assert "E_norm_n_mm2" not in case


def test_v092_section_9_1_does_not_allow_case_or_route_to_override_gamma_ct():
    baseline = _base(
        "central_tension",
        {"N_n": 400_000.0, "A_net_mm2": 5152.0, "gamma_c": 0.9},
    )
    hostile = _base(
        "central_tension",
        {
            "N_n": 400_000.0,
            "A_net_mm2": 5152.0,
            "gamma_c": 0.9,
            "gamma_ct": 1.0,
        },
    )
    hostile["gamma_ct"] = 1.0

    first = runtime.sp554_fire_mechanical_guided_workflow(baseline)
    second = runtime.sp554_fire_mechanical_guided_workflow(hostile)
    assert second["gamma_T_required"] == pytest.approx(first["gamma_T_required"])
    assert second["gamma_ct"] == pytest.approx(1.1)
    assert second["route_trace"]["legacy_user_gamma_ct_ignored"] == pytest.approx(1.0)


def test_v092_section_9_2_retains_separate_fire_phi_and_gamma_ct():
    result = runtime.sp554_fire_mechanical_guided_workflow(
        _base("central_compression", _compression_route())
    )
    trace = result["route_trace"]

    assert result["gamma_T_candidates"][0]["details"]["gamma_ct"] == pytest.approx(1.1)
    assert trace["governing_strength_axis"] == "y"
    assert trace["axes"]["y"]["lambda_bar_fire"] > trace["axes"]["z"]["lambda_bar_fire"]
    assert trace["axes"]["y"]["phi_fire"] < trace["axes"]["z"]["phi_fire"]


def test_v092_section_10_legacy_axis_route_is_fail_closed_until_canonical_migration():
    case = _base(
        "bending",
        {
            "gamma_c": 1.0,
            "checks": {
                "eq_10_1": {
                    "M_x_nmm": 10_000_000.0,
                    "M_y_nmm": 0.0,
                    "W_pl_min_eff_mm3": 100_000.0,
                }
            },
        },
    )
    with pytest.raises(ValueError, match="old Mx -> new Mz translation is forbidden"):
        runtime.sp554_fire_mechanical_guided_workflow(case)


def test_v092_section_11_legacy_axis_route_is_fail_closed_until_canonical_migration():
    case = _base("combined_nm", {"N_n": 100_000.0})
    with pytest.raises(ValueError, match="M_z = strong-axis bending"):
        runtime.sp554_fire_mechanical_guided_workflow(case)


def test_v092_canonical_action_contract_is_explicit_and_forbids_aliasing():
    assert CANONICAL_ACTION_CONTRACT == {
        "strong_axis_bending": "M_z",
        "weak_axis_bending": "M_y",
        "torsion": "M_x",
        "legacy_Mx_to_Mz_translation_allowed": False,
    }
