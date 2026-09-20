from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.section_model import SectionPropertyModel
from standard_core.sp16_mech6_gate import aggregate_sp16_mechanical_verification

ROOT = Path(__file__).resolve().parents[1]


def _census(active, contextual=None):
    context_rows = [{"applicability": "conditional_context", **row} for row in (contextual or [])]
    return {
        "schema": "sp16_mech2_applicability_census_v1",
        "active_checks": active,
        "context_driven_checks": context_rows,
    }


def test_mech6_graph_identity_and_gate_metadata():
    app = FireUI1Application.from_package_root(ROOT)
    assert app.model.graph["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    md = app.model.graph["metadata"]
    assert md["sp16_mech6_aggregate_gate_semantics_closed"] is True
    assert md["sp16_mech6_sp16_mechanical_pass_quantity_closed"] is True
    assert md["sp16_mech6_sp554_transition_requires_pass"] is True
    assert md["sp16_mech6_all_n3_n10_primary_flow_bindings_closed"] is False


def test_pure_shear_with_explicit_normative_evidence_can_pass_when_no_other_checks_are_applicable():
    values = {
        "sp16_applicability_census": _census([
            {"id": "shear_x", "family": "shear", "label": "Qx", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 8.2"]}
        ]),
        "ambient_axis_shear_state": {
            "clause_8_2_3_components": {"applicable": True, "utilization_tau_x_823": 0.42},
            "mechanics_component_checks": {"available": True},
        },
    }
    out = aggregate_sp16_mechanical_verification(values)
    assert out["sp16_mechanical_gate_status"] == "PASS"
    assert out["sp16_mechanical_pass"] is True
    row = out["sp16_mechanical_verification"]["rows"][0]
    assert row["status"] == "PASS"
    assert row["utilization"] == 0.42


def test_explicit_normative_failure_dominates_unresolved_checks():
    values = {
        "sp16_applicability_census": _census([
            {"id": "shear_x", "family": "shear", "label": "Qx", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 8.2"]},
            {"id": "torsion_T", "family": "torsion", "label": "T", "runtime_status": "sp16_mech4_free_torsion_mechanics_closed", "normative_scope": []},
        ]),
        "ambient_axis_shear_state": {
            "clause_8_2_3_components": {"applicable": True, "utilization_tau_x_823": 1.2},
            "mechanics_component_checks": {"available": True},
        },
        "ambient_torsion_runtime_closed": True,
    }
    out = aggregate_sp16_mechanical_verification(values)
    assert out["sp16_mechanical_gate_status"] == "FAIL"
    assert out["sp16_mechanical_has_failed"] is True
    assert out["sp16_mechanical_has_unresolved"] is True
    assert "shear_x" in out["sp16_mechanical_verification"]["failed_check_ids"]
    assert "torsion_T" in out["sp16_mechanical_verification"]["unresolved_check_ids"]


def test_missing_axial_stage_evidence_is_fail_closed_not_implicit_pass():
    values = {
        "sp16_applicability_census": _census([
            {"id": "section_compression", "family": "section_strength", "label": "compression", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 §7"]}
        ])
    }
    out = aggregate_sp16_mechanical_verification(values)
    assert out["sp16_mechanical_gate_status"] == "INCOMPLETE_FAIL_CLOSED"
    assert out["sp16_mechanical_pass"] is False
    assert out["sp16_mechanical_verification"]["rows"][0]["status"] == "DEFERRED"


def test_existing_n3_and_n7_evidence_is_consumed_when_present():
    values = {
        "sp16_applicability_census": _census([
            {"id": "section_compression", "family": "section_strength", "label": "compression", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 §7"]},
            {"id": "member_compression_stability", "family": "member_stability", "label": "stability", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 §7"]},
            {"id": "effective_length_slenderness", "family": "member_stability", "label": "slenderness", "runtime_status": "inherited_runtime", "normative_scope": ["SP16 §10"]},
        ]),
        "sp16_n3_eq5_eta_yield": 0.55,
        "sp16_n3_eta7": 0.72,
        "sp16_n7_slenderness_pass": True,
    }
    out = aggregate_sp16_mechanical_verification(values)
    assert out["sp16_mechanical_gate_status"] == "PASS"
    assert out["sp16_mechanical_governing_utilization"] == 0.72


def test_context_ltb_not_required_is_na_but_unresolved_fatigue_blocks_gate():
    values = {
        "sp16_applicability_census": _census([], [
            {"id": "beam_ltb", "family": "member_stability", "label": "LTB", "trigger": "restraints", "normative_scope": []},
            {"id": "fatigue", "family": "special_limit_state", "label": "fatigue", "trigger": "cyclic action", "normative_scope": ["SP16 §12"]},
        ]),
        "ltb_check_required": False,
    }
    out = aggregate_sp16_mechanical_verification(values)
    rows = {r["id"]: r for r in out["sp16_mechanical_verification"]["rows"]}
    assert rows["beam_ltb"]["status"] == "N.A."
    assert rows["fatigue"]["status"] == "CONTEXT_UNRESOLVED"
    assert out["sp16_mechanical_gate_status"] == "INCOMPLETE_FAIL_CLOSED"


def test_primary_guided_flow_now_stops_before_fire_when_sp16_evidence_is_incomplete():
    app = FireUI1Application.from_package_root(ROOT)
    session = GuidedCalculationSession(app.model, entry_node_id="SP16_I_AMBIENT_LOADS", registry=app.service.registry)
    p = SectionPropertyModel.doubly_symmetric_i_sharp(300.0, 150.0, 8.0, 12.0)
    session.submit({
        "ambient_load_combination": {"schema": "test"},
        "ambient_N_force": 0.0,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_Q_x": 100e3,
        "ambient_Q_y": 0.0,
        "ambient_T_torsion": 0.0,
    })
    for qid, value in {
        "section_geometry_2d_normalized": {"template": "i_section", "h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        "A_gross": p.area_mm2,
        "J_x": p.ix_mm4,
        "J_y": p.iy_mm4,
        "Rs_formula": 200.0,
        "gamma_c_bending_strength": 1.0,
        "sp16_shear_hole_alpha45": 1.0,
    }.items():
        session._set_quantity(qid, value, node_id="TEST_SEED", source_kind="CALCULATED")
    assert session.current_node_id == "SP16_D_AMBIENT_BIMOMENT_REQUIRED"
    session.submit(False)
    assert session.current_node_id == "SP16_D_AMBIENT_CENSUS_CONFIRM"
    session.submit(True)
    assert session.current_node_id == "SP16_D_MECH7_FATIGUE_REQUIRED"
    session.submit(True)  # explicitly applicable, but no N9 workflow evidence in this isolated test
    assert session.current_node_id == "SP16_D_MECH7_BRITTLE_REQUIRED"
    session.submit(False)
    assert session.current_node_id == "SP16_D_MECH9_FATIGUE_ROUTE"
    # Crane-runway fatigue is intentionally outside the MECH9 auto-execution scope,
    # therefore the strict ambient gate must remain fail-closed.
    session.submit("crane_runway_12_2")
    assert session.current_node_id == "SP16_R_AMBIENT_MECHANICAL_INCOMPLETE"
    values = session.plain_values()
    assert values["sp16_mechanical_pass"] is False
    assert values["sp16_mechanical_gate_status"] == "INCOMPLETE_FAIL_CLOSED"
    assert "fatigue" in values["sp16_mechanical_verification"]["unresolved_check_ids"]
    assert "brittle_fracture" not in values["sp16_mechanical_verification"]["unresolved_check_ids"]
