from __future__ import annotations

import pytest

from standard_core.fire_ui0 import ExecutionRegistry
from standard_core.sp16_mech7_primary_workflow import bind_primary_ambient_evidence
from standard_core.sp16_mech7_v072_remediation import (
    install_registry_remediation,
    normalize_mech7_inputs,
)


def _census(active=(), contextual=()):
    return {
        "schema": "sp16_mech2_applicability_census_v1",
        "active_checks": [
            {"id": cid, "family": "test", "label": cid, "applicability": "applicable", "runtime_status": "inherited_runtime", "normative_scope": []}
            for cid in active
        ],
        "context_driven_checks": [
            {"id": cid, "family": "test", "label": cid, "applicability": "conditional_context", "trigger": "test", "runtime_status": "context_resolution_required", "normative_scope": []}
            for cid in contextual
        ],
    }


def test_v072_material_formula_reuses_explicit_table3_category_without_default():
    out = normalize_mech7_inputs({
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "material_safety_category": "statistical_control",
    })
    assert out["gamma_m"] == pytest.approx(1.025)
    assert out["Ry_formula"] == pytest.approx(255.0 / 1.025)
    assert out["Ru_formula"] == pytest.approx(380.0 / 1.025)
    assert out["Rs_formula"] == pytest.approx(0.58 * 255.0 / 1.025)

    blocked = normalize_mech7_inputs({"fy_norm": 255.0, "fu_norm": 380.0})
    assert "Ry_formula" not in blocked
    assert "gamma_m" not in blocked


def test_v072_directional_geometric_slenderness_uses_leff_over_matching_radius():
    out = normalize_mech7_inputs({
        "sp16_l_eff_x": 2100.0,
        "sp16_i_x": 42.0,
        "sp16_l_eff_y": 3000.0,
        "sp16_i_y": 30.0,
    })
    assert out["sp16_lambda_x_geom"] == pytest.approx(50.0)
    assert out["sp16_lambda_y_geom"] == pytest.approx(100.0)


def test_v072_catalog_i_section_contract_is_normalized_without_table9_10_inference():
    out = normalize_mech7_inputs({
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "shape_group": "I_ROLLED_DSYMM",
            "dimensions": {"h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        }
    })
    geom = out["section_geometry_2d_normalized"]
    assert geom["template"] == "i_section"
    assert geom["h_mm"] == 300.0
    assert geom["tw_mm"] == 8.0
    assert "sp16_mech7_table9_group" not in out
    assert "sp16_mech7_table10_group" not in out
    assert "sp16_mech7_flange_edge_stiffened" not in out


def test_v072_user_step15_central_compression_route_resolves_previous_three_integration_gaps():
    values = {
        "sp16_applicability_census": _census(
            ["section_compression", "member_compression_stability", "effective_length_slenderness"],
            ["local_stability_web", "local_stability_flange"],
        ),
        "ambient_N_force": -100e3,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "A_net": 2000.0,
        "A_gross": 2000.0,
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "material_safety_category": "statistical_control",
        "gamma_c_compression": 1.0,
        "phi_x_sp16": 0.8,
        "phi_y_sp16": 0.7,
        "sp16_l_eff_x": 2500.0,
        "sp16_i_x": 50.0,
        "sp16_l_eff_y": 3000.0,
        "sp16_i_y": 50.0,
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "shape_group": "I_ROLLED_DSYMM",
            "dimensions": {"h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        },
        "E_norm": 206000.0,
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    }
    normalized = normalize_mech7_inputs(values)
    evidence = bind_primary_ambient_evidence(normalized)["sp16_mech7_primary_evidence"]["evidence"]
    for cid in (
        "section_compression",
        "member_compression_stability",
        "effective_length_slenderness",
        "local_stability_web",
        "local_stability_flange",
    ):
        assert evidence[cid]["status"] in {"PASS", "FAIL"}, (cid, evidence[cid])
        assert "requires Ry_formula" not in str(evidence[cid].get("reason") or "")
        assert "requires sp16_lambda_x_geom" not in str(evidence[cid].get("reason") or "")
        assert "qualified I-section template" not in str(evidence[cid].get("reason") or "")


def test_v072_registry_wrapper_is_idempotent_and_keeps_original_gate_executor():
    seen = []

    def original(values, node):
        seen.append(dict(values))
        return {"sp16_mech7_primary_evidence": {"evidence": {}}, "sp16_mech7_primary_binding_complete": True}

    reg = ExecutionRegistry({"SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER": original})
    install_registry_remediation(reg)
    first = reg.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"]
    install_registry_remediation(reg)
    assert reg.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"] is first
    first({"fy_norm": 255.0, "material_safety_category": "ks1_limited_service"}, {})
    assert seen[-1]["Ry_formula"] == pytest.approx(255.0)
