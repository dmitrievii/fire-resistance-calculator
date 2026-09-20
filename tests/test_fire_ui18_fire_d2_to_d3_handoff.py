from __future__ import annotations

from pathlib import Path
import pytest

from standard_core.fire_ui0 import GuidedCalculationSession, QuantityValue
from standard_core.fire_ui1_http import FireUI1Application

ROOT=Path(__file__).resolve().parents[1]


def _seed(session: GuidedCalculationSession, qid: str, value, seq: int = 1) -> None:
    q=session.model.quantities[qid]
    session.values[qid]=QuantityValue(qid,value,q.get("canonical_unit"),"CALCULATED","TEST_SEED",seq,None)


def _position_exact_result(tcr: float) -> GuidedCalculationSession:
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model, entry_node_id="SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", registry=app.service.registry)
    _seed(session,"fire_d2_critical_temperature_status","COMPLETE")
    _seed(session,"fire_d2_critical_temperature_c",tcr)
    _seed(session,"fire_d2_critical_temperature_controlling_kind","gamma_T")
    _seed(session,"fire_d2_strength_inversion_result",{
        "status":"EXACT_WITHIN_PUBLISHED_CURVE","temperature_c":tcr,
        "temperature_relation":"=","coefficient_kind":"gamma_T"})
    _seed(session,"fire_d2_runtime_closed",True)
    return session


def test_user_regression_exact_638_temperature_continues_to_section12_exposure():
    session=_position_exact_result(638.011628)
    session._auto_progress()
    assert session.status == "AWAITING_INPUT"
    assert session.current_node_id == "SP554_I_EXPOSURE"
    assert session.pending_node_ids == []
    assert session.branch_failures == []
    vals=session.plain_values()
    assert vals["critical_temperature_c"] == pytest.approx(638.011628)
    assert vals["fire_d3_critical_temperature_handoff_c"] == pytest.approx(638.011628)
    assert session.current_card()["prompt"] == "Схема обогрева"


def test_ambient_capacity_failure_does_not_enter_section12_with_fake_exact_temperature():
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model, entry_node_id="SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", registry=app.service.registry)
    _seed(session,"fire_d2_critical_temperature_status","AMBIENT_CAPACITY_EXCEEDED")
    _seed(session,"fire_d2_critical_temperature_c",20.0)
    _seed(session,"fire_d2_critical_temperature_controlling_kind","gamma_T")
    _seed(session,"fire_d2_strength_inversion_result",{
        "status":"AMBIENT_CAPACITY_EXCEEDED","temperature_c":20.0,
        "temperature_relation":"<=","coefficient_kind":"gamma_T"})
    _seed(session,"fire_d2_runtime_closed",True)
    session._auto_progress()
    assert session.status == "RESULT"
    assert session.current_node_id == "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE"
    assert "critical_temperature_c" not in session.plain_values()


def test_bounded_only_temperature_remains_fail_closed_until_bounded_thermal_route_exists():
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model, entry_node_id="SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", registry=app.service.registry)
    _seed(session,"fire_d2_critical_temperature_status","INCOMPLETE_FAIL_CLOSED")
    _seed(session,"fire_d2_critical_temperature_lower_bound_c",700.0)
    _seed(session,"fire_d2_critical_temperature_controlling_kind","bounded")
    _seed(session,"fire_d2_strength_inversion_result",{
        "status":"ABOVE_PUBLISHED_TEMPERATURE_RANGE","temperature_lower_bound_c":700.0,
        "temperature_relation":">","coefficient_kind":"gamma_T"})
    _seed(session,"fire_d2_runtime_closed",True)
    session._auto_progress()
    assert session.status == "RESULT"
    assert session.current_node_id == "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE"
    assert "critical_temperature_c" not in session.plain_values()


def test_ui18_dag_has_explicit_exact_result_handoff_and_thermal_entry():
    app=FireUI1Application.from_package_root(ROOT)
    policy=app.model.presentation_policy
    ui=app.model.ui_policy_for_node("SP554_FIRE_D2_R_CRITICAL_TEMPERATURE")
    assert ui["terminal_result"] is False
    assert ui["continue_after_result"] is True
    edges=app.model.graph["edges"]
    e1=next(e for e in edges if e["id"]=="FIRE_D3_E_001")
    assert e1["edge_type"] == "handoff"
    assert e1["condition"]["quantity_id"] == "fire_d2_critical_temperature_status"
    assert e1["condition"]["value"] == "COMPLETE"
    e2=next(e for e in edges if e["id"]=="FIRE_UI18_E_D3_HANDOFF_TO_EXPOSURE")
    assert e2["to_node_id"] == "SP554_I_EXPOSURE"
    assert policy["thermal_entry_node_id"] == "SP554_I_EXPOSURE"


def test_parallel_mechanical_queue_is_drained_before_exact_tcr_handoff():
    from examples.fire_ui16_route_census import run
    loads=dict(N_force=400000.0,load_My_local=0.0,load_Mz_local=0.0,
               load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0)
    status,session,_=run("ui18_tension",loads,maxsteps=260)
    assert status == "THERMAL_ENTRY"
    assert session.current_node_id == "SP554_I_EXPOSURE"
    assert session.pending_node_ids == []
    assert session.branch_failures == []
    assert session.plain_values()["critical_temperature_c"] == pytest.approx(session.plain_values()["fire_d2_critical_temperature_c"])
