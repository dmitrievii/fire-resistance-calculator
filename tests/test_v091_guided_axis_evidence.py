import math

import pytest

import streamlit_app as ui
from standard_core.fire_sp554_runtime_v091 import (
    SP16_STEEL_E_N_MM2,
    _gamma_e_8_6_declarative_final,
    _phi_9_2_declarative_final,
)
from standard_core.fire_sp554_v091_guided_overlay import (
    GRAPH_SUFFIX,
    PHI_NODE_ID,
    STIFFNESS_TRACE_QID,
    STRENGTH_TRACE_QID,
)
from standard_core.sp16_mech7_v083_full_route_overlay import (
    GAMMA_E_INTERNAL_QID,
    GAMMA_E_NODE_ID,
    GAMMA_E_REQUIRED_QID,
)


def test_v091_active_guided_graph_removes_legacy_gamma_e_dependencies_and_declares_trace_outputs():
    app = ui._new_application()
    assert GRAPH_SUFFIX in app.model.graph["graph_id"]
    nodes = {row["id"]: row for row in app.model.graph["nodes"]}

    gamma = nodes[GAMMA_E_NODE_ID]
    consumed = {row["quantity_id"] for row in gamma["consumes"]}
    produced = {row["quantity_id"] for row in gamma["produces"]}
    assert "E_norm" not in consumed
    assert "sp16_v081_governing_stability_axis" not in consumed
    assert {
        "N_force",
        "A_gross",
        "sp16_l_eff_z",
        "sp16_l_eff_y",
        "sp16_i_z",
        "sp16_i_y",
    } <= consumed
    assert {GAMMA_E_INTERNAL_QID, GAMMA_E_REQUIRED_QID, STIFFNESS_TRACE_QID} <= produced

    phi = nodes[PHI_NODE_ID]
    phi_outputs = {row["quantity_id"] for row in phi["produces"]}
    assert STRENGTH_TRACE_QID in phi_outputs


def test_v091_guided_gamma_e_uses_normative_E_and_independent_two_axis_governing_state():
    values = {
        "N_force": -400_000.0,
        "A_gross": 5282.0,
        "sp16_l_eff_z": 3000.0,
        "sp16_l_eff_y": 6000.0,
        "sp16_i_z": 85.0,
        "sp16_i_y": 50.0,
        # Deliberately contradictory legacy values: neither may govern.
        "E_norm": 1.0,
        "sp16_v081_governing_stability_axis": "z",
    }
    node = {
        "produces": [
            {"quantity_id": GAMMA_E_INTERNAL_QID},
            {"quantity_id": GAMMA_E_REQUIRED_QID},
            {"quantity_id": STIFFNESS_TRACE_QID},
        ]
    }
    first = _gamma_e_8_6_declarative_final(values, node)
    second = _gamma_e_8_6_declarative_final(
        dict(values, E_norm=9.9e9, sp16_v081_governing_stability_axis="y"),
        node,
    )
    assert first == second

    expected_z = (
        400_000.0 * 3000.0**2
        / (math.pi**2 * 206000.0 * 5282.0 * 85.0**2)
    )
    expected_y = (
        400_000.0 * 6000.0**2
        / (math.pi**2 * 206000.0 * 5282.0 * 50.0**2)
    )
    trace = first[STIFFNESS_TRACE_QID]
    assert trace["E_n_mm2"] == pytest.approx(SP16_STEEL_E_N_MM2)
    assert trace["axes"]["z"]["gamma_e"] == pytest.approx(expected_z)
    assert trace["axes"]["y"]["gamma_e"] == pytest.approx(expected_y)
    assert trace["governing_stiffness_axis"] == "y"
    assert first[GAMMA_E_INTERNAL_QID] == pytest.approx(expected_y)
    assert first[GAMMA_E_REQUIRED_QID] == pytest.approx(expected_y)


def test_v091_guided_phi_publishes_exact_fire_slenderness_evidence_without_e_norm_control():
    values = {
        "sp16_lambda_z_geom": 35.28,
        "sp16_lambda_y_geom": 119.39,
        "sp16_curve_z": "b",
        "sp16_curve_y": "c",
        "fy_norm": 255.0,
        "E_norm": 1.0,
    }
    node = {
        "produces": [
            {"quantity_id": "phi_compression_sp554"},
            {"quantity_id": STRENGTH_TRACE_QID},
        ]
    }
    result = _phi_9_2_declarative_final(values, node)
    trace = result[STRENGTH_TRACE_QID]
    assert trace["E_n_mm2"] == pytest.approx(206000.0)
    assert trace["Ryn_n_mm2"] == pytest.approx(255.0)
    assert trace["axes"]["z"]["lambda_bar_fire"] == pytest.approx(
        35.28 * math.sqrt(255.0 / 206000.0)
    )
    assert trace["axes"]["y"]["lambda_bar_fire"] == pytest.approx(
        119.39 * math.sqrt(255.0 / 206000.0)
    )
    assert trace["governing_strength_axis"] == "y"
    assert result["phi_compression_sp554"] == pytest.approx(
        trace["axes"]["y"]["phi_fire"]
    )
