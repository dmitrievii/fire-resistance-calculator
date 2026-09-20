from __future__ import annotations

from pathlib import Path
import pytest

from standard_core.fire_ui0 import GuidedCalculationSession, QuantityValue
from standard_core.fire_ui1_http import FireUI1Application

ROOT=Path(__file__).resolve().parents[1]


def _seed(session: GuidedCalculationSession, qid: str, value) -> None:
    q=session.model.quantities[qid]
    session.values[qid]=QuantityValue(qid,value,q.get("canonical_unit"),"CALCULATED","TEST_SEED",1,None)


def _i20k1_geometry():
    return {
        "source":"profile_catalog",
        "shape_group":"I_ROLLED_DSYMM",
        "dimensions":{"h_mm":196.0,"b_mm":199.0,"tw_mm":6.5,"tf_mm":10.0},
    }


def _perimeter_session(entry: str, *, sides: str = "four_sides") -> GuidedCalculationSession:
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model,entry_node_id=entry,registry=app.service.registry)
    _seed(session,"section_family","i_section")
    _seed(session,"A_gross",5269.0)
    _seed(session,"section_geometry_2d_normalized",_i20k1_geometry())
    if entry != "SP554_I_EXPOSURE":
        _seed(session,"heated_exposure_configuration",sides)
    return session


def test_unprotected_i_section_four_sides_uses_table1_contour_formula_and_continues():
    session=_perimeter_session("SP554_I_EXPOSURE")
    session.submit("four_sides")
    vals=session.plain_values()
    assert vals["P_heated"] == pytest.approx(1.175)
    assert vals["delta_pr"] == pytest.approx(5269.0/1175.0)
    assert vals["sp554_table1_perimeter_trace"]["formula"] == "4B + 2D - 2t"
    assert vals["sp554_table1_perimeter_trace"]["protection_geometry"] == "unprotected"
    assert session.current_node_id == "SP554_D_UNPROTECTED_METHOD"
    assert session.status == "AWAITING_INPUT"


def test_unprotected_i_section_three_sides_uses_table1_contour_formula():
    session=_perimeter_session("SP554_I_EXPOSURE")
    session.submit("three_sides")
    vals=session.plain_values()
    assert vals["P_heated"] == pytest.approx(0.976)
    assert vals["delta_pr"] == pytest.approx(5269.0/976.0)
    assert vals["sp554_table1_perimeter_trace"]["formula"] == "3B + 2D - 2t"


def test_protected_i_section_contour_and_box_have_distinct_perimeters_and_delta():
    contour=_perimeter_session("SP554_D_PROTECTION_PERIMETER_MODE")
    contour.submit("contour")
    cv=contour.plain_values()
    assert cv["P_heated_protected"] == pytest.approx(1.175)
    assert cv["delta_pr_protected"] == pytest.approx(5269.0/1175.0)
    assert cv["sp554_protected_table1_perimeter_trace"]["formula"] == "4B + 2D - 2t"
    assert contour.current_node_id == "SP554_D_JOINTS"

    box=_perimeter_session("SP554_D_PROTECTION_PERIMETER_MODE")
    box.submit("box")
    bv=box.plain_values()
    assert bv["P_heated_protected"] == pytest.approx(0.790)
    assert bv["delta_pr_protected"] == pytest.approx(5269.0/790.0)
    assert bv["sp554_protected_table1_perimeter_trace"]["formula"] == "2B + 2D"
    assert box.current_node_id == "SP554_D_JOINTS"
    assert bv["delta_pr_protected"] > cv["delta_pr_protected"]


def test_protected_i_section_box_three_sides_uses_B_plus_2D():
    session=_perimeter_session("SP554_D_PROTECTION_PERIMETER_MODE",sides="three_sides")
    session.submit("box")
    vals=session.plain_values()
    assert vals["P_heated_protected"] == pytest.approx(0.591)
    assert vals["sp554_protected_table1_perimeter_trace"]["formula"] == "B + 2D"


def test_unmapped_angle_falls_back_to_manual_unprotected_perimeter():
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model,entry_node_id="SP554_I_EXPOSURE",registry=app.service.registry)
    _seed(session,"section_family","angle")
    _seed(session,"A_gross",1000.0)
    _seed(session,"section_geometry_2d_normalized",{"template":"angle","leg1_mm":100.0,"leg2_mm":75.0,"t_mm":8.0})
    session.submit("four_sides")
    assert session.current_node_id == "SP554_I_HEATED_PERIMETER_MANUAL"
    assert session.status == "AWAITING_INPUT"
    session.submit(0.42)
    assert session.plain_values()["P_heated"] == pytest.approx(0.42)
    assert session.plain_values()["delta_pr"] == pytest.approx(1000.0/420.0)
    assert session.current_node_id == "SP554_D_UNPROTECTED_METHOD"


def test_protected_12_10_nodes_consume_protected_reduced_thickness_not_unprotected():
    app=FireUI1Application.from_package_root(ROOT)
    for nid in ("SP554_C_12_10_DOMAIN","SP554_C_12_10_MINIMUM_THICKNESS","SP554_C_12_10_PROTECTED_TIME","SP554_C_12_5_1D_PERFORMANCE_DATASET"):
        consumes={b["quantity_id"] for b in app.model.nodes[nid].get("consumes",[])}
        assert "delta_pr_protected" in consumes
        assert "delta_pr" not in consumes
    annex=app.model.nodes["SP554_C_ANNEX_A_SCHEDULE"]
    consumes={b["quantity_id"] for b in annex.get("consumes",[])}
    assert "P_heated_protected" in consumes
    assert "delta_pr_protected" in consumes


def test_ui19_contract_has_separate_heated_sides_and_protection_geometry_components():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.ui_policy_for_node("SP554_I_EXPOSURE")["component"] == "heated_sides_selector"
    assert app.model.ui_policy_for_node("SP554_D_PROTECTION_PERIMETER_MODE")["component"] == "protection_perimeter_mode_selector"
    q=app.model.quantities["heated_exposure_configuration"]
    assert {x["value"] for x in q["enum_values"]} == {"three_sides","four_sides"}
