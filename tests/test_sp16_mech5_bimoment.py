from __future__ import annotations

import math
from pathlib import Path
import pytest

from standard_core.fire_ui0 import GuidedCalculationSession, FireUIError
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel
from standard_core.sp16_mech4_torsion import recover_free_torsion_and_combined_stress
from standard_core.sp16_mech5_bimoment import recover_direct_bimoment_pointwise

ROOT=Path(__file__).resolve().parents[1]


def _geom(): return {"template":"i_section","h_mm":300.0,"b_mm":150.0,"tw_mm":8.0,"tf_mm":12.0}
def _props(): return SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)


def _nmqt(*, B=0.0, T=2e6):
    p=_props()
    if T:
        return recover_free_torsion_and_combined_stress(
            geometry=_geom(),area_mm2=p.area_mm2,inertia_x_mm4=p.ix_mm4,inertia_y_mm4=p.iy_mm4,
            N_n=-200e3,Mx_nmm=35e6,My_nmm=8e6,Qx_n=100e3,Qy_n=-50e3,T_nmm=T,B_nmm2=B)
    raise RuntimeError('test helper expects nonzero T')


def _seed(s, geometry=None):
    p=_props()
    for qid,v in {
        "section_geometry_2d_normalized": geometry or _geom(), "A_gross":p.area_mm2,"J_x":p.ix_mm4,"J_y":p.iy_mm4,
        "Rs_formula":200.0,"gamma_c_bending_strength":1.0,"sp16_shear_hole_alpha45":1.0,
    }.items(): s._set_quantity(qid,v,node_id='TEST_SEED',source_kind='CALCULATED')


def _ambient_payload(B_question_only=False):
    return {"ambient_load_combination":{"schema":"test"},"ambient_N_force":-200e3,"ambient_M_x":35e6,"ambient_M_y":8e6,
            "ambient_Q_x":100e3,"ambient_Q_y":50e3,"ambient_T_torsion":2e6}


def test_graph_identity_and_mech5_flags():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md=app.model.graph['metadata']
    assert md['sp16_mech5_direct_bimoment_input_policy_preserved'] is True
    assert md['sp16_mech5_bimoment_from_t_solver_closed'] is False
    assert md['sp16_mech5_i_section_sectorial_pointwise_recovery_closed'] is True
    assert md['sp16_mech5_all_section_bimoment_geometry_closed'] is False


def test_i_section_direct_b_recovers_sigma_b_with_consistent_iomega_and_sign():
    B=-7.0e9
    state=recover_direct_bimoment_pointwise(geometry=_geom(),B_nmm2=B,combined_nmqt_state={"pointwise_recovery":_nmqt(B=B)})
    yf=(300.0-12.0)/2.0
    expected_iw=12.0*yf*yf*150.0**3/6.0
    assert math.isclose(state['I_omega_n_mm6'],expected_iw,rel_tol=1e-12)
    assert state['normal_stress_complete'] is True
    assert state['warping_normal_stress_included'] is True
    flange=[p for p in state['points'] if p.get('sectorial_region')=='top_flange' and abs(p['x_mm'])>1]
    assert flange
    p=flange[0]
    assert math.isclose(p['sigma_B_n_mm2'],B*p['sectorial_coordinate_omega_mm2']/expected_iw,rel_tol=1e-12,abs_tol=1e-12)
    assert math.isclose(p['sigma_N_Mx_My_B_n_mm2'],p['sigma_N_Mx_My_n_mm2']+p['sigma_B_n_mm2'],rel_tol=1e-12,abs_tol=1e-12)


def test_b_zero_is_complete_without_requiring_sectorial_geometry():
    prior={"pointwise_recovery":_nmqt(B=0.0)}
    state=recover_direct_bimoment_pointwise(geometry={"template":"arbitrary_manual_properties"},B_nmm2=0.0,combined_nmqt_state=prior)
    assert state['runtime_closed'] is True
    assert state['normal_stress_complete'] is True
    assert state['sectorial_properties_required'] is False
    assert all(p['sigma_B_n_mm2']==0.0 for p in state['points'])


def test_nonzero_b_channel_is_fail_closed_in_direct_function():
    channel={"template":"channel","h_mm":300.0,"b_mm":90.0,"tw_mm":8.0,"tf_mm":12.0}
    with pytest.raises(FireUIError):
        recover_direct_bimoment_pointwise(geometry=channel,B_nmm2=5e9,combined_nmqt_state={"pointwise_recovery":_nmqt(B=5e9)})


def test_ambient_direct_b_i_section_is_closed_and_removed_from_deferred_census():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id='SP16_I_AMBIENT_LOADS',registry=app.service.registry)
    s.submit(_ambient_payload()); _seed(s)
    assert s.current_node_id=='SP16_D_AMBIENT_BIMOMENT_REQUIRED'
    s.submit(True)
    assert s.current_node_id=='SP16_I_AMBIENT_BIMOMENT_DIRECT'
    s.submit(-7.0e9)
    assert s.current_node_id=='SP16_D_AMBIENT_CENSUS_CONFIRM'
    v=s.plain_values(); c=v['sp16_applicability_census']
    assert v['ambient_bimoment_runtime_closed'] is True
    assert v['ambient_complete_pointwise_stress_state']['normal_stress_complete'] is True
    b=next(x for x in c['active_checks'] if x['id']=='bimoment_B')
    assert b['runtime_status']=='sp16_mech5_direct_bimoment_pointwise_closed'
    assert 'bimoment_B' not in c['deferred_active_check_ids']
    assert 'bimoment_B' not in c['partial_active_check_ids']


def test_ambient_direct_b_unsupported_geometry_remains_deferred():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id='SP16_I_AMBIENT_LOADS',registry=app.service.registry)
    payload=_ambient_payload(); payload['ambient_Q_x']=0.0;payload['ambient_Q_y']=0.0;payload['ambient_T_torsion']=0.0
    s.submit(payload); _seed(s,{"template":"channel","h_mm":300.0,"b_mm":90.0,"tw_mm":8.0,"tf_mm":12.0})
    s.submit(True); s.submit(5e9)
    v=s.plain_values(); c=v['sp16_applicability_census']
    assert v['ambient_bimoment_runtime_closed'] is False
    assert 'bimoment_B' in c['deferred_active_check_ids']


def test_fire_direct_b_state_is_characterized_but_existing_qy_t_sp554_gate_is_preserved():
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id='SP16_D_FIRE_LOAD_CASE_MODE',registry=app.service.registry)
    payload=_ambient_payload()
    for qid,value in payload.items(): s._set_quantity(qid,value,node_id='TEST_UPSTREAM_SP16_PASS',source_kind='CALCULATED')
    s._set_quantity('ambient_B_bimoment',6e9,node_id='TEST_UPSTREAM_SP16_PASS',source_kind='CALCULATED')
    s._set_quantity('sp16_mechanical_pass',True,node_id='TEST_UPSTREAM_SP16_PASS',source_kind='CALCULATED')
    _seed(s)
    s.submit('same_as_ambient')
    v=s.plain_values()
    assert v['fire_bimoment_mechanics_runtime_closed'] is True
    assert v['fire_complete_pointwise_stress_state']['normal_stress_complete'] is True
    assert s.current_node_id=='SP554_D_VERIFICATION_PLAN_CONFIRM'
    s.submit(True)
    assert s.current_node_id=='SP554_R_UI16_DEFERRED_BRANCHES'
