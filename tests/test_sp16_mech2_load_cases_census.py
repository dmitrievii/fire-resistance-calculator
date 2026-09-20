from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel

ROOT = Path(__file__).resolve().parents[1]


def _ambient_payload(*, N=-400e3, Mx=40e6, My=-10e6, Qx=50e3, Qy=0.0, T=0.0):
    return {
        "ambient_load_combination": {"schema":"test_ambient","name":"ULS ambient"},
        "ambient_N_force": N,
        "ambient_M_x": Mx,
        "ambient_M_y": My,
        "ambient_Q_x": Qx,
        "ambient_Q_y": Qy,
        "ambient_T_torsion": T,
    }


def _fire_payload(*, N=-250e3, Mx=20e6, My=5e6, Qx=30e3, Qy=0.0, T=0.0):
    return {
        "special_load_combination": {"schema":"test_fire","name":"accidental fire"},
        "N_force": N,
        "M_x": Mx,
        "M_y": My,
        "Q_x": Qx,
        "Q_y": Qy,
        "T_torsion": T,
    }


def _start_ambient() -> GuidedCalculationSession:
    app = FireUI1Application.from_package_root(ROOT)
    return GuidedCalculationSession(app.model, entry_node_id="SP16_I_AMBIENT_LOADS", registry=app.service.registry)



def _seed_mech3_dependencies(s: GuidedCalculationSession) -> None:
    p=SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)
    values={
        "section_geometry_2d_normalized":{"template":"i_section","h_mm":300.0,"b_mm":150.0,"tw_mm":8.0,"tf_mm":12.0},
        "A_gross":p.area_mm2,"J_x":p.ix_mm4,"J_y":p.iy_mm4,
        "Rs_formula":200.0,"gamma_c_bending_strength":1.0,"sp16_shear_hole_alpha45":1.0,
    }
    for qid,value in values.items():
        s._set_quantity(qid,value,node_id="TEST_SEED",source_kind="CALCULATED")




def _start_fire_subflow_from_ambient(payload: dict, *, ambient_B: float = 0.0) -> GuidedCalculationSession:
    """Isolate downstream FIRE_LOAD_CASE behavior after a hypothetically passed upstream SP16 gate."""
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id="SP16_D_FIRE_LOAD_CASE_MODE", registry=app.service.registry)
    actions = {
        "N": payload["ambient_N_force"], "Mx": payload["ambient_M_x"], "My": payload["ambient_M_y"],
        "Qx": payload["ambient_Q_x"], "Qy": payload["ambient_Q_y"], "T": payload["ambient_T_torsion"], "B": ambient_B,
    }
    seed = dict(payload)
    seed["ambient_B_bimoment"] = ambient_B
    seed["ambient_load_case"] = {"schema":"sp16_mech2_load_case_v1", "kind":"ambient", "source":"test_upstream_passed", "actions": actions}
    for qid, value in seed.items():
        s._set_quantity(qid, value, node_id="TEST_UPSTREAM_SP16_PASS", source_kind="CALCULATED")
    _seed_mech3_dependencies(s)
    return s


def test_mech2_graph_identity_and_policy():
    app = FireUI1Application.from_package_root(ROOT)
    assert app.model.graph["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    md=app.model.graph["metadata"]
    assert md["sp16_mech2_ambient_fire_load_cases_closed"] is True
    assert md["sp16_mech2_applicability_census_closed"] is True
    assert md["sp16_mech2_full_ambient_gate_closed"] is False
    assert app.model.ui_policy_for_node("SP16_I_AMBIENT_LOADS")["component"] == "ambient_signed_load_menu"
    assert app.model.ui_policy_for_node("SP554_H_SP20_LOADS")["component"] == "fire_signed_load_menu"


def test_ambient_census_enumerates_action_and_context_checks():
    s=_start_ambient()
    s.submit(_ambient_payload()); _seed_mech3_dependencies(s)
    assert s.current_node_id == "SP16_D_AMBIENT_BIMOMENT_REQUIRED"
    s.submit(False)
    assert s.current_node_id == "SP16_D_AMBIENT_CENSUS_CONFIRM"
    v=s.plain_values()
    c=v["sp16_applicability_census"]
    ids=set(c["active_check_ids"])
    assert {"section_compression","member_compression_stability","bending_x","bending_y","biaxial_bending","shear_x","interaction_N_M","interaction_M_Q"} <= ids
    context={x["id"] for x in c["context_driven_checks"]}
    assert {"beam_ltb","local_stability_web","local_stability_flange","fatigue","brittle_fracture"} <= context
    assert c["deferred_active_check_ids"] == []
    assert c["full_ambient_gate_closed"] is False


def test_same_as_ambient_fire_case_is_explicit_value_preserving_copy():
    p=_ambient_payload(N=-400e3,Mx=40e6,My=-10e6,Qx=50e3)
    s=_start_fire_subflow_from_ambient(p)
    s.submit("same_as_ambient")
    v=s.plain_values()
    assert v["N_force"] == p["ambient_N_force"]
    assert v["M_x"] == p["ambient_M_x"]
    assert v["M_y"] == p["ambient_M_y"]
    assert v["Q_x"] == p["ambient_Q_x"]
    assert v["B_bimoment"] == v["ambient_B_bimoment"] == 0.0
    assert v["fire_load_case"]["source"] == "inherited_from_ambient"
    assert v["fire_load_case"]["actions"] == v["ambient_load_case"]["actions"]
    assert v["special_load_combination"]["explicit_user_choice"] == "same_as_ambient"
    assert "SP16_C_FIRE_LOADS_INHERIT_AMBIENT" in s.visited_node_ids


def test_separate_fire_case_does_not_overwrite_ambient_case():
    ambient=_ambient_payload(N=-400e3,Mx=40e6,My=0,Qx=10e3)
    s=_start_fire_subflow_from_ambient(ambient)
    s.submit("separate")
    assert s.current_node_id == "SP554_H_SP20_LOADS"
    fire=_fire_payload(N=-180e3,Mx=12e6,My=3e6,Qx=7e3)
    s.submit(fire)
    assert s.current_node_id == "SP16_D_BIMOMENT_REQUIRED"
    s.submit(False)
    v=s.plain_values()
    assert v["ambient_load_case"]["actions"]["N"] == -400e3
    assert v["fire_load_case"]["actions"]["N"] == -180e3
    assert v["fire_load_case"]["actions"]["Mx"] == 12e6
    assert v["ambient_load_case"]["actions"]["Mx"] == 40e6
    assert v["fire_load_case"]["source"] == "separate_user_input"
    assert "SP16_C_FIRE_LOAD_CASE_FINALIZE" in s.visited_node_ids


def test_ambient_qy_is_visible_to_census_and_stops_before_fire_case():
    s=_start_ambient()
    s.submit(_ambient_payload(Qy=9e3)); _seed_mech3_dependencies(s); s.submit(False)
    c=s.plain_values()["sp16_applicability_census"]
    assert c["deferred_active_check_ids"] == []
    shear_y=next(x for x in c["active_checks"] if x["id"]=="shear_y")
    assert shear_y["runtime_status"] == "sp16_mech3_axis_shear_closed"
    assert s.current_node_id == "SP16_D_AMBIENT_CENSUS_CONFIRM"
    s.submit(True)
    assert s.current_node_id == "SP16_D_MECH7_FATIGUE_REQUIRED"
    s.submit(False)
    assert s.current_node_id == "SP16_D_MECH7_BRITTLE_REQUIRED"
    s.submit(False)
    assert s.current_node_id == "SP16_I_MECH7_COMPRESSION_SLENDERNESS"
    assert "SP16_D_FIRE_LOAD_CASE_MODE" not in s.visited_node_ids


def test_ambient_torsion_is_visible_to_census_and_mech4_closed_for_supported_geometry():
    s=_start_ambient()
    s.submit(_ambient_payload(T=2e6)); _seed_mech3_dependencies(s); s.submit(False)
    v=s.plain_values(); c=v["sp16_applicability_census"]
    assert c["deferred_active_check_ids"] == []
    tor=next(x for x in c["active_checks"] if x["id"]=="torsion_T")
    assert tor["runtime_status"] == "sp16_mech4_free_torsion_mechanics_closed"
    assert v["ambient_torsion_runtime_closed"] is True
    s.submit(True)
    assert s.current_node_id == "SP16_D_MECH7_FATIGUE_REQUIRED"
    s.submit(False); s.submit(False)
    assert s.current_node_id == "SP16_I_MECH7_COMPRESSION_SLENDERNESS"
    assert "SP16_D_FIRE_LOAD_CASE_MODE" not in s.visited_node_ids


def test_ambient_bimoment_is_scoped_separately_from_fire_bimoment():
    s=_start_ambient()
    s.submit(_ambient_payload(N=-100e3,Mx=5e6)); _seed_mech3_dependencies(s)
    s.submit(True)
    assert s.current_node_id == "SP16_I_AMBIENT_BIMOMENT_DIRECT"
    s.submit(-2.5e10)
    c=s.plain_values()["sp16_applicability_census"]
    assert "bimoment_B" not in c["partial_active_check_ids"]
    b=next(x for x in c["active_checks"] if x["id"]=="bimoment_B")
    assert b["runtime_status"]=="sp16_mech5_direct_bimoment_pointwise_closed"
    s.submit(True)
    assert s.current_node_id == "SP16_D_MECH7_FATIGUE_REQUIRED"
    s.submit(False); s.submit(False)
    assert s.current_node_id == "SP16_I_MECH7_COMPRESSION_SLENDERNESS"
    fire_session=_start_fire_subflow_from_ambient(_ambient_payload(N=-100e3,Mx=5e6), ambient_B=-2.5e10)
    fire_session.submit("separate")
    fire_session.submit(_fire_payload(N=-80e3,Mx=4e6,My=0,Qx=0))
    fire_session.submit(False)
    v=fire_session.plain_values()
    assert v["ambient_B_bimoment"] == -2.5e10
    assert v["B_bimoment"] == 0.0
    assert v["fire_load_case"]["actions"]["B"] == 0.0
