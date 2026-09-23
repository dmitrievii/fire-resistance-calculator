import pytest

from standard_core import fire_sp554_runtime as runtime
from standard_core.fire_sp554_runtime_v091 import SP16_STEEL_E_N_MM2


def _compression_route():
    lambda_z = 35.28
    lambda_y = 119.39
    return {
        "N_n": 400_000.0,
        "A_gross_mm2": 5282.0,
        "gamma_c": 0.9,
        "sp16_lambda_z_geom": lambda_z,
        "sp16_lambda_y_geom": lambda_y,
        "sp16_l_eff_z": 3000.0,
        "sp16_l_eff_y": 6000.0,
        "sp16_i_z": 3000.0 / lambda_z,
        "sp16_i_y": 6000.0 / lambda_y,
        "sp16_curve_z": "b",
        "sp16_curve_y": "c",
        # Stale v0.90 fields: retained for session compatibility, never governing.
        "lambda_bar": 0.01,
        "phi_sp16_formula8": 0.999,
        "mu_length_sp16": 7.0,
        "member_length_mm": 9999.0,
        "J_min_mm4": 1.0,
    }


def _compression_case(**overrides):
    case = {
        "member_route": "central_compression",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": 255.0,
        "route": _compression_route(),
    }
    case.update(overrides)
    return case


def test_v091_public_9_2_workflow_needs_no_e_norm_and_uses_normative_e_at_tcr():
    result = runtime.sp554_fire_mechanical_guided_workflow(_compression_case())

    assert result["critical_temperature_c"] is not None
    assert result["E_normative_n_mm2"] == pytest.approx(206000.0)
    assert result["E_t_critical_n_mm2"] == pytest.approx(
        result["gamma_E_table_at_critical_temperature"] * SP16_STEEL_E_N_MM2
    )
    assert result["legacy_E_norm_n_mm2_ignored"] is None


def test_v091_public_9_2_workflow_ignores_stale_e_norm_end_to_end():
    baseline = runtime.sp554_fire_mechanical_guided_workflow(_compression_case())
    stale = runtime.sp554_fire_mechanical_guided_workflow(
        _compression_case(E_norm_n_mm2=1.0)
    )

    for key in (
        "gamma_T_required",
        "gamma_E_required",
        "critical_temperature_c",
        "R_yt_critical_n_mm2",
        "E_t_critical_n_mm2",
    ):
        assert stale[key] == pytest.approx(baseline[key])
    assert stale["legacy_E_norm_n_mm2_ignored"] == pytest.approx(1.0)


def test_v091_non_9_2_routes_retain_legacy_e_norm_contract_fail_closed():
    """Freeze the v0.91 behavior explicitly, not the current v0.92 public API.

    v0.92 intentionally migrated §9.1 and therefore no longer requires the old
    ambient E_norm seed for central tension.  The saved predecessor is the
    correct subject for this historical v0.91 regression.
    """
    tension_case = {
        "member_route": "central_tension",
        "steel_strength_group": "ordinary",
        "fy_norm_n_mm2": 255.0,
        "route": {
            "N_n": 100_000.0,
            "A_net_mm2": 1000.0,
            "gamma_c": 1.0,
        },
    }

    v091_workflow = runtime._v092_previous_sp554_fire_mechanical_guided_workflow
    with pytest.raises(ValueError, match="E_norm_n_mm2"):
        v091_workflow(tension_case)
