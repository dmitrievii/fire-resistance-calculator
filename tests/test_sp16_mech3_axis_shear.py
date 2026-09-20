from __future__ import annotations

import math
from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel
from standard_core.sp16_mech3_axis_shear import recover_pointwise_axis_shear

ROOT = Path(__file__).resolve().parents[1]


def _geom():
    return {"template":"i_section","h_mm":300.0,"b_mm":150.0,"tw_mm":8.0,"tf_mm":12.0}


def _props():
    return SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)


def _seed_geometry_and_shear_material(s: GuidedCalculationSession) -> None:
    p=_props()
    vals={
        "section_geometry_2d_normalized": _geom(),
        "A_gross":p.area_mm2,
        "J_x":p.ix_mm4,
        "J_y":p.iy_mm4,
        "Rs_formula":200.0,
        "gamma_c_bending_strength":1.0,
        "sp16_shear_hole_alpha45":1.0,
    }
    for qid,value in vals.items():
        s._set_quantity(qid,value,node_id="TEST_SEED",source_kind="CALCULATED")


def _ambient_payload(*,Qx=100e3,Qy=50e3,T=0.0):
    return {
        "ambient_load_combination":{"schema":"test","name":"ambient"},
        "ambient_N_force":-200e3,
        "ambient_M_x":35e6,
        "ambient_M_y":8e6,
        "ambient_Q_x":Qx,
        "ambient_Q_y":Qy,
        "ambient_T_torsion":T,
    }


def test_graph_identity_and_mech3_flags():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph["graph_id"]=="sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    md=app.model.graph["metadata"]
    assert md["sp16_mech3_axis_specific_qx_qy_closed"] is True
    assert md["sp16_mech3_clause_8_2_3_qy_component_closed"] is True
    assert md["sp16_mech3_pointwise_shear_state_closed"] is True
    assert md["sp16_mech3_sp554_qy_handoff_closed"] is False


def test_pointwise_recovery_keeps_qx_qy_separate_at_same_points():
    p=_props()
    r=recover_pointwise_axis_shear(
        geometry=_geom(), area_mm2=p.area_mm2, inertia_x_mm4=p.ix_mm4, inertia_y_mm4=p.iy_mm4,
        N_n=-200e3, Mx_nmm=35e6, My_nmm=8e6, Qx_n=100e3, Qy_n=-50e3, B_nmm2=0.0,
    )
    assert r["point_count"]>10
    assert r["normal_stress_complete"] is True
    assert r["geometry_provenance"]["geometry_exactness"]=="exact_sharp_geometry"
    pts=r["points"]
    assert any(x["tau_x_n_mm2"]>0 for x in pts)
    assert any(x["tau_y_n_mm2"]<0 for x in pts)
    for row in pts:
        assert math.isclose(row["tau_resultant_n_mm2"], math.hypot(row["tau_x_n_mm2"],row["tau_y_n_mm2"]), rel_tol=1e-12, abs_tol=1e-12)
    # No result object may replace the two actions by a scalar resultant Q.
    assert "Q_resultant" not in r and "Q_total" not in r


def test_ambient_i_section_qy_closes_mech3_census_and_materializes_823_components():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_I_AMBIENT_LOADS",registry=app.service.registry)
    s.submit(_ambient_payload())
    _seed_geometry_and_shear_material(s)
    s.submit(False)
    assert s.current_node_id=="SP16_D_AMBIENT_CENSUS_CONFIRM"
    v=s.plain_values(); state=v["ambient_axis_shear_state"]
    assert v["ambient_qy_runtime_closed"] is True
    c=state["clause_8_2_3_components"]
    aw=8.0*(300.0-2*12.0); af=150.0*12.0
    assert math.isclose(c["tau_x_gross_n_mm2"],100e3/aw,rel_tol=1e-12)
    assert math.isclose(c["tau_y_n_mm2"],50e3/(2*af),rel_tol=1e-12)
    census=v["sp16_applicability_census"]
    shear_y=next(x for x in census["active_checks"] if x["id"]=="shear_y")
    assert shear_y["runtime_status"]=="sp16_mech3_axis_shear_closed"
    assert "shear_y" not in census["deferred_active_check_ids"]


def test_mech4_closes_supported_torsion_after_qy_closure():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_I_AMBIENT_LOADS",registry=app.service.registry)
    s.submit(_ambient_payload(Qy=50e3,T=2e6)); _seed_geometry_and_shear_material(s); s.submit(False)
    v=s.plain_values(); c=v["sp16_applicability_census"]
    assert c["deferred_active_check_ids"]==[]
    assert v["ambient_qy_runtime_closed"] is True
    assert v["ambient_torsion_runtime_closed"] is True


def test_fire_case_gets_mech3_state_but_qy_stays_fail_closed_at_legacy_sp554_handoff():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_D_FIRE_LOAD_CASE_MODE",registry=app.service.registry)
    payload=_ambient_payload(Qy=30e3)
    for qid,value in payload.items(): s._set_quantity(qid,value,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    s._set_quantity("ambient_B_bimoment",0.0,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    s._set_quantity("sp16_mechanical_pass",True,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    _seed_geometry_and_shear_material(s)
    s.submit("same_as_ambient")
    # Fire shear recovery is automatic; the existing SP554 plan is still interactive.
    assert "fire_axis_shear_state" in s.plain_values()
    assert s.plain_values()["fire_qy_mechanics_runtime_closed"] is True
    assert s.current_node_id=="SP554_D_VERIFICATION_PLAN_CONFIRM"
    s.submit(True)
    assert s.current_node_id=="SP554_R_UI16_DEFERRED_BRANCHES"
