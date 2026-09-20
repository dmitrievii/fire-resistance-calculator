from __future__ import annotations

import math
from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel
from standard_core.sp16_mech4_torsion import recover_free_torsion_and_combined_stress

ROOT = Path(__file__).resolve().parents[1]


def _geom():
    return {"template":"i_section","h_mm":300.0,"b_mm":150.0,"tw_mm":8.0,"tf_mm":12.0}


def _props():
    return SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)


def _seed_geometry_and_shear_material(s: GuidedCalculationSession, geometry=None) -> None:
    p=_props()
    vals={
        "section_geometry_2d_normalized": geometry or _geom(),
        "A_gross":p.area_mm2,
        "J_x":p.ix_mm4,
        "J_y":p.iy_mm4,
        "Rs_formula":200.0,
        "gamma_c_bending_strength":1.0,
        "sp16_shear_hole_alpha45":1.0,
    }
    for qid,value in vals.items():
        s._set_quantity(qid,value,node_id="TEST_SEED",source_kind="CALCULATED")


def _ambient_payload(*,Qx=0.0,Qy=0.0,T=2.0e6):
    return {
        "ambient_load_combination":{"schema":"test","name":"ambient"},
        "ambient_N_force":-200e3,
        "ambient_M_x":35e6,
        "ambient_M_y":8e6,
        "ambient_Q_x":Qx,
        "ambient_Q_y":Qy,
        "ambient_T_torsion":T,
    }


def test_graph_identity_and_mech4_flags():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph["graph_id"]=="sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    md=app.model.graph["metadata"]
    assert md["sp16_mech4_free_torsion_supported_templates_closed"] is True
    assert md["sp16_mech4_t_distinct_from_mx_and_b"] is True
    assert md["sp16_mech4_pointwise_nmqt_mechanics_state_closed"] is True
    assert md["sp16_mech4_restrained_torsion_solver_closed"] is False
    assert md["sp16_mech4_sp554_t_handoff_closed"] is False


def test_i_section_it_matches_sp16_annex_d_and_t_is_not_b():
    p=_props()
    T=2.4e6
    r=recover_free_torsion_and_combined_stress(
        geometry=_geom(), area_mm2=p.area_mm2, inertia_x_mm4=p.ix_mm4, inertia_y_mm4=p.iy_mm4,
        N_n=0.0, Mx_nmm=0.0, My_nmm=0.0, Qx_n=0.0, Qy_n=0.0, T_nmm=T, B_nmm2=0.0,
    )
    expected=(1.29/3.0)*((300.0-24.0)*8.0**3 + 2.0*150.0*12.0**3)
    assert math.isclose(r["torsion_properties"]["I_t_mm4"], expected, rel_tol=1e-12)
    assert r["T_semantics"].startswith("Saint_Venant")
    assert r["B_semantics"]=="independent_direct_bimoment_input_not_derived_from_T"
    assert r["action_T_nmm"]==T
    assert r["bimoment_B_nmm2"]==0.0
    assert any(x["tau_T_resultant_n_mm2"]>0 for x in r["points"])


def test_qx_qy_t_are_combined_as_same_point_shear_vectors_not_scalar_actions():
    p=_props()
    r=recover_free_torsion_and_combined_stress(
        geometry=_geom(), area_mm2=p.area_mm2, inertia_x_mm4=p.ix_mm4, inertia_y_mm4=p.iy_mm4,
        N_n=-200e3, Mx_nmm=35e6, My_nmm=8e6, Qx_n=100e3, Qy_n=-50e3, T_nmm=2e6, B_nmm2=0.0,
    )
    for row in r["points"]:
        assert math.isclose(row["tau_total_x_n_mm2"], row["tau_x_n_mm2"]+row["tau_T_x_n_mm2"], rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(row["tau_total_y_n_mm2"], row["tau_y_n_mm2"]+row["tau_T_y_n_mm2"], rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(row["tau_total_resultant_n_mm2"], math.hypot(row["tau_total_x_n_mm2"],row["tau_total_y_n_mm2"]), rel_tol=1e-12, abs_tol=1e-12)
    assert "Q_resultant" not in r and "T_equivalent_Q" not in r


def test_ambient_supported_t_is_no_longer_deferred_in_census():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_I_AMBIENT_LOADS",registry=app.service.registry)
    s.submit(_ambient_payload(Qx=100e3,Qy=50e3,T=2e6)); _seed_geometry_and_shear_material(s)
    s.submit(False)  # B not required
    assert s.current_node_id=="SP16_D_AMBIENT_CENSUS_CONFIRM"
    v=s.plain_values()
    assert v["ambient_torsion_runtime_closed"] is True
    assert v["ambient_free_torsion_state"]["runtime_closed"] is True
    c=v["sp16_applicability_census"]
    tor=next(x for x in c["active_checks"] if x["id"]=="torsion_T")
    assert tor["runtime_status"]=="sp16_mech4_free_torsion_mechanics_closed"
    assert "torsion_T" not in c["deferred_active_check_ids"]


def test_unsupported_t_geometry_stays_fail_closed():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_I_AMBIENT_LOADS",registry=app.service.registry)
    s.submit(_ambient_payload(Qx=0,Qy=0,T=2e6))
    _seed_geometry_and_shear_material(s, {"template":"arbitrary_manual_properties"})
    s.submit(False)
    v=s.plain_values()
    assert v["ambient_torsion_runtime_closed"] is False
    c=v["sp16_applicability_census"]
    assert "torsion_T" in c["deferred_active_check_ids"]


def test_fire_t_gets_mechanics_state_but_legacy_sp554_handoff_stays_deferred():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id="SP16_D_FIRE_LOAD_CASE_MODE",registry=app.service.registry)
    payload=_ambient_payload(Qx=80e3,Qy=0,T=2e6)
    for qid,value in payload.items(): s._set_quantity(qid,value,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    s._set_quantity("ambient_B_bimoment",0.0,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    s._set_quantity("sp16_mechanical_pass",True,node_id="TEST_UPSTREAM_SP16_PASS",source_kind="CALCULATED")
    _seed_geometry_and_shear_material(s)
    s.submit("same_as_ambient")
    v=s.plain_values()
    assert v["fire_torsion_mechanics_runtime_closed"] is True
    assert v["fire_free_torsion_state"]["runtime_closed"] is True
    assert s.current_node_id=="SP554_D_VERIFICATION_PLAN_CONFIRM"
    s.submit(True)
    assert s.current_node_id=="SP554_R_UI16_DEFERRED_BRANCHES"


def test_direct_b_is_not_derived_from_t_and_marks_normal_stress_incomplete():
    p=_props()
    r=recover_free_torsion_and_combined_stress(
        geometry=_geom(), area_mm2=p.area_mm2, inertia_x_mm4=p.ix_mm4, inertia_y_mm4=p.iy_mm4,
        N_n=0.0, Mx_nmm=0.0, My_nmm=0.0, Qx_n=0.0, Qy_n=0.0, T_nmm=2e6, B_nmm2=-7e9,
    )
    assert r["action_T_nmm"]==2e6
    assert r["bimoment_B_nmm2"]==-7e9
    assert r["normal_stress_complete"] is False
    assert r["warping_normal_stress_included"] is False
