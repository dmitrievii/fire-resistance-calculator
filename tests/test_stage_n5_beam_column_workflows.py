import copy
import json
import math
from pathlib import Path

import pytest

from standard_core import beam_column_workflows as n5
from standard_core.beam_column_stability import annex_d3_stability_coefficient
from standard_core.runner import _prepare_case_for_validation, run_case

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "beam_column_guided_example.json"


def _raw():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def _prepared(raw=None):
    c, _, trace = _prepare_case_for_validation(raw or _raw(), ROOT)
    return c, trace


def test_n5_guided_example_complete_exact_d3_node():
    result = run_case(EXAMPLE, ROOT)
    w = result["results"]
    assert w["status"] == "COMPLETE"
    assert w["d2_d3_x"]["status"] == "D3_EXACT_NODE"
    assert w["derived"]["relative_slenderness_x"] == pytest.approx(1.5)
    assert w["d2_d3_x"]["m_eff"] == pytest.approx(1.0)
    assert w["d2_d3_x"]["phi_e"] == pytest.approx(0.593)
    assert w["pass"] is True


def test_n5_hydrates_current_sp16_c255_material_not_historical_normcad_values():
    _, trace = _prepared()
    values = trace["material"]["resolved_values"]
    assert values["normative_yield_resistance_n_mm2"] == 245.0
    assert values["design_yield_resistance_n_mm2"] == 240.0
    assert values["elastic_modulus_n_mm2"] == 206000.0
    assert values["normative_yield_resistance_n_mm2"] != 255.0
    assert values["design_yield_resistance_n_mm2"] != 250.0


def test_n5_hydrates_profile_radii_and_change6_table7_axes():
    c, trace = _prepared()
    assert c["radius_x_mm"] == pytest.approx(math.sqrt(26291600.0 / 5964.0))
    assert c["radius_y_mm"] == pytest.approx(math.sqrt(8796600.0 / 5964.0))
    assert c["table7_section_type_x"] == "b"
    assert c["table7_section_type_y"] == "c"
    assert trace["profile"]["torsional_inertia_mm4"] == pytest.approx(497080.0)


def test_n5_strength_auto_selects_equation_105_when_applicable():
    result = run_case(EXAMPLE, ROOT)["results"]
    assert result["strength"]["route"] == "9.1.1_EQ105"
    assert result["strength"]["applicability_eq105"]["permitted"] is True


def test_n5_non_node_d3_is_bilinearly_interpolated_inside_printed_domain():
    raw = _raw()
    raw["effective_length_x_mm"] = 3000.0
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["d2_d3_x"]["status"] == "D3_BILINEAR_INTERPOLATED"
    assert result["d2_d3_x"]["phi_e"] is not None
    assert "phi_e_x" not in result["required_unresolved"]
    assert result["governing_utilization"] is not None
    assert result["status"] == "COMPLETE"


def test_n5_in_domain_interpolation_takes_precedence_over_external_override():
    raw = _raw()
    raw["effective_length_x_mm"] = 3000.0
    raw["stability"] = {"external_phi_e_x": {"value": 0.55, "basis": "legacy external interpolation TEST"}}
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["d2_d3_x"]["status"] == "D3_BILINEAR_INTERPOLATED"
    assert result["d2_d3_x"]["source"] == "table_D.3_bilinear_digital_policy_no_extrapolation"
    assert result["d2_d3_x"]["phi_e"] != pytest.approx(0.55)
    assert result["status"] == "COMPLETE"


def test_n5_interpolated_phi_e_is_capped_by_central_compression_phi():
    value = annex_d3_stability_coefficient(1.61095, 6.67245, 0.18)
    assert value == pytest.approx(0.18)


def test_n5_dynamic_load_routes_to_eq106_and_fails_closed_without_point_data():
    raw = _raw()
    raw["strength"]["direct_dynamic_load"] = True
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["strength"]["route"] == "9.1.1_EQ106_REQUIRED"
    assert result["strength"]["status"] == "EQ106_POINT_DATA_REQUIRED"
    assert result["status"] == "INCOMPLETE_FAIL_CLOSED"


def test_n5_dynamic_load_eq106_runs_when_point_data_is_explicit():
    raw = _raw()
    raw["strength"]["direct_dynamic_load"] = True
    raw["strength"]["eq106_points"] = [{
        "point_x_mm": 0.0,
        "point_y_mm": 80.0,
        "sectorial_coordinate_mm2": 0.0,
        "net_sectorial_inertia_mm6": 1.0
    }]
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["strength"]["route"] == "9.1.1_EQ106"
    assert result["strength"]["utilization"] is not None
    assert result["status"] == "COMPLETE"


def test_n5_built_up_route_is_not_duplicated():
    raw = _raw(); raw["member_form"] = "built_up"
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["specialized_action"] == "built_up_beam_columns_and_combined_local_stability"
    assert result["pass"] is None


def test_n5_box_route_is_not_duplicated():
    raw = _raw(); raw["member_form"] = "solid_box"
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["specialized_action"] == "beam_column_stability"
    assert result["pass"] is None

    # Clause 9.1.3 high-strength asymmetric tension-fibre branch is never silently omitted:
    # the guided scope hands it to the retained detailed action when its applicability is met.
    c2, _ = _prepared()
    c2["normative_yield_resistance_n_mm2"] = 500.0
    c2["strength"]["section_is_asymmetric_about_axis_perpendicular_to_bending_plane"] = True
    high = n5.beam_column_guided_workflow(c2)
    assert high["strength"]["route"] == "9.1.3_EQ107_DETAILED_ACTION_REQUIRED"
    assert high["status"] == "INCOMPLETE_FAIL_CLOSED"


def test_n5_nonqualified_symmetry_route_is_fail_closed_to_detailed_action():
    raw = _raw(); raw["major_stiffness_plane_coincides_with_symmetry_plane"] = False
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    assert result["status"] == "DETAILED_ACTION_REQUIRED"
    assert result["governing_utilization"] is None


def test_n5_clause_9_2_9_meff_y_gt20_keeps_independent_lambda_trigger():
    raw = _raw()
    raw["moment_y_n_mm"] = 107499579.80885312
    # Preserve the historical NormCAD relative eccentricity geometry but avoid its anomalous 2.95 mm lefy.
    raw["annex_d2_flange_to_web_area_ratio_y"] = 1.0
    # lambda_bar_y = 0.5 under current C255 material / current Table-7 mapping.
    raw["effective_length_y_mm"] = 0.5 * math.sqrt(8796600.0 / 5964.0) / math.sqrt(240.0 / 206000.0)
    c, _ = _prepared(raw)
    result = n5.beam_column_guided_workflow(c)
    route = result["stability_branch"]
    assert result["d2_d3_y"]["m_eff"] > 20.0
    assert route["equation_116_required"] is False
    assert route["section_8_y_route_required"] is True
    assert route["equation_109_with_ey_zero_required"] is True
    assert any(x["equation"] == "109_ey_zero" for x in result["stability_checks"])


def test_n5_normcad_d3_point_is_reproduced_by_bilinear_interpolation():
    assert annex_d3_stability_coefficient(1.61095, 6.67245, 0.87958) == pytest.approx(0.18770813331, abs=1e-12)
