from __future__ import annotations

import math

import pytest

from standard_core.sp16_mech7_primary_workflow import bind_primary_ambient_evidence
from standard_core.sp16_mech7_runtime_remediation import hydrate_mech_prerequisites


def _census(active=(), contextual=()):
    return {
        "schema": "sp16_mech2_applicability_census_v1",
        "active_checks": [
            {
                "id": cid,
                "family": "test",
                "label": cid,
                "applicability": "applicable",
                "runtime_status": "inherited_runtime",
                "normative_scope": [],
            }
            for cid in active
        ],
        "context_driven_checks": [
            {
                "id": cid,
                "family": "test",
                "label": cid,
                "applicability": "conditional_context",
                "trigger": "test",
                "runtime_status": "context_resolution_required",
                "normative_scope": [],
            }
            for cid in contextual
        ],
    }


def test_v072_hydrates_only_qualified_material_and_slenderness_aliases():
    values = {
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "gamma_m": 1.025,
        "E_norm": 206000.0,
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
    }
    hydrated, trace = hydrate_mech_prerequisites(values)

    assert hydrated["Ry_formula"] == pytest.approx(255.0 / 1.025)
    assert hydrated["Ru_formula"] == pytest.approx(380.0 / 1.025)
    assert hydrated["Rs_formula"] == pytest.approx(0.58 * 255.0 / 1.025)
    assert hydrated["sp16_lambda_x_geom"] == pytest.approx(math.sqrt(206000.0 / 255.0))
    assert hydrated["sp16_lambda_y_geom"] == pytest.approx(1.2 * math.sqrt(206000.0 / 255.0))
    qids = {row["quantity_id"] for row in trace}
    assert {"Ry_formula", "Ru_formula", "Rs_formula", "sp16_lambda_x_geom", "sp16_lambda_y_geom"} <= qids


def test_v072_does_not_invent_ry_without_gamma_m():
    hydrated, trace = hydrate_mech_prerequisites({"fy_norm": 255.0, "E_norm": 206000.0})
    assert "Ry_formula" not in hydrated
    assert all(row["quantity_id"] != "Ry_formula" for row in trace)


def test_v072_adapts_catalog_i_geometry_without_changing_catalog_dimensions():
    original = {
        "source": "profile_catalog",
        "shape_group": "I_ROLLED_DSYMM",
        "family_id": 1,
        "designation": "20К1",
        "source_row_id": 7,
        "dimensions": {"h_mm": 200.0, "b_mm": 200.0, "tw_mm": 6.5, "tf_mm": 10.0, "r_mm": 13.0},
    }
    values = {"section_geometry_2d_normalized": original}
    hydrated, trace = hydrate_mech_prerequisites(values)
    geom = hydrated["section_geometry_2d_normalized"]

    assert geom["template"] == "i_section"
    assert geom["h_mm"] == 200.0
    assert geom["b_mm"] == 200.0
    assert geom["tw_mm"] == 6.5
    assert geom["tf_mm"] == 10.0
    assert geom["dimensions"] == original["dimensions"]
    assert original.get("template") is None
    assert any(row["source"] == "catalog_geometry_contract_adapter" for row in trace)


def test_v072_closes_table32_slenderness_when_only_relative_slenderness_is_materialized():
    values = {
        "sp16_applicability_census": _census(["effective_length_slenderness"]),
        "ambient_N_force": -100e3,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "A_gross": 4000.0,
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "gamma_m": 1.025,
        "E_norm": 206000.0,
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
        "phi_x_sp16": 0.82,
        "phi_y_sp16": 0.76,
        "gamma_c_compression": 1.0,
        "sp16_mech7_table32_row": "4",
        "sp16_mech7_group4_slenderness_increase": False,
    }
    hydrated, _ = hydrate_mech_prerequisites(values)
    ev = bind_primary_ambient_evidence(hydrated)["sp16_mech7_primary_evidence"]["evidence"]
    assert ev["effective_length_slenderness"]["status"] in {"PASS", "FAIL"}
    assert ev["effective_length_slenderness"].get("reason") is None


def test_v072_catalog_i_local_stability_no_longer_defers_on_geometry_contract():
    values = {
        "sp16_applicability_census": _census([], ["local_stability_web", "local_stability_flange"]),
        "ambient_N_force": -100e3,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "shape_group": "I_ROLLED_DSYMM",
            "dimensions": {"h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        },
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "gamma_m": 1.025,
        "E_norm": 206000.0,
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    }
    hydrated, _ = hydrate_mech_prerequisites(values)
    ev = bind_primary_ambient_evidence(hydrated)["sp16_mech7_primary_evidence"]["evidence"]

    assert ev["local_stability_web"]["status"] in {"PASS", "FAIL"}
    assert ev["local_stability_flange"]["status"] in {"PASS", "FAIL"}
    assert ev["local_stability_web"]["utilization"] is not None
    assert ev["local_stability_flange"]["utilization"] is not None
