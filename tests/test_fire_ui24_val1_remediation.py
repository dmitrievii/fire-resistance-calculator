from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application

ROOT = Path(__file__).resolve().parents[1]


def _seed(s: GuidedCalculationSession, qid: str, value) -> None:
    s._set_quantity(qid, value, node_id="TEST_SEED", source_kind="USER_INPUT")


def _static_stress_session(stress_state: str) -> GuidedCalculationSession:
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(
        app.model,
        entry_node_id="SP554_D_GAMMA_T_METHOD",
        registry=app.service.registry,
    )
    for qid, value in {
        "stress_state": stress_state,
        "special_load_combination": {"schema": "fire_ui24_test"},
        "fy_norm": 250.0,
        "steel_strength_group": "ordinary",
        "fire_d2_temperature_governing_policy_reconciled": True,
    }.items():
        _seed(s, qid, value)
    return s


def test_ui24_graph_identity_and_val1_flags():
    app = FireUI1Application.from_package_root(ROOT)
    assert app.model.graph["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    assert app.model.graph["metadata"]["fire_ui24_val1_d001_static_stress_compression_gammae_closed"] is True
    assert app.model.graph["metadata"]["fire_ui24_val1_d005_gamma_t_dependency_reconciled"] is True


def test_d001_d005_static_stress_compression_resolves_gammae_and_reaches_tcr():
    s = _static_stress_session("central_compression")
    for qid, value in {
        "E_norm": 206000.0,
        "J_min": 2.0e7,
        "A_gross": 5000.0,
        "N_force": -200000.0,
    }.items():
        _seed(s, qid, value)
    s.submit("software_static_stress")
    s.submit({"sigma_n_static": 120.0}, provenance={"source_document": "solver", "source_reference": "VAL1-D001"})
    assert s.current_node_id == "SP554_I_COMPRESSION_CONTEXT"
    s.submit({"member_length": 3000.0})
    s.submit("table30")
    s.submit("S1")
    values = s.plain_values()
    assert values["gamma_T_required"] > 0.0
    assert values["gamma_e_compression"] > 0.0
    assert values["gamma_E_required"] == values["gamma_e_compression"]
    assert values["fire_d2_critical_temperature_status"] == "COMPLETE"
    assert values["fire_d2_critical_temperature_c"] > 0.0
    assert "SP554_FIRE_UI17_C_TCR_COMPRESSION" in s.visited_node_ids
    assert not s.branch_failures


def test_d002_static_stress_bending_continues_to_strength_tcr():
    s = _static_stress_session("bending")
    s.submit("software_static_stress")
    s.submit({"sigma_n_static": 120.0}, provenance={"source_document": "solver", "source_reference": "VAL1-D002"})
    values = s.plain_values()
    assert values["gamma_T_required"] == 0.48
    assert values["fire_d2_critical_temperature_status"] == "COMPLETE"
    assert "SP554_C_CTRL_STRENGTH_ONLY" in s.visited_node_ids
    assert "SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY" in s.visited_node_ids
    assert not s.branch_failures


def test_compression_diagnostic_delta_is_not_a_guided_production_edge():
    app = FireUI1Application.from_package_root(ROOT)
    edge = next(e for e in app.model.edges if e["id"] == "E1098")
    assert edge["edge_type"] == "data"
    out = [e for e in app.model.outgoing["SP554_C_CTRL_COMPRESSION"] if e["edge_type"] in {"control", "branch", "handoff"}]
    assert [e["id"] for e in out] == ["UI24_E_CTRL_COMPRESSION_TO_TCR"]


def test_d003_all_exposed_gamma_c_choices_exist_in_table_1_and_other_is_removed():
    app = FireUI1Application.from_package_root(ROOT)
    ds = next(d for d in app.model.graph["datasets"] if d["id"] == "SP16_TABLE1_GAMMA_C")
    cases = {row["case"] for row in ds["storage"]["rows"]}
    for nid in ("SP16_D_GC_T", "SP16_D_GC_C", "SP16_D_GC_B", "SP16_D_GC_NM"):
        options = {o["value"] for o in app.model.nodes[nid]["options"]}
        assert "other" not in options
        assert options <= cases
    assert {o["value"] for o in app.model.nodes["SP16_D_CURVE"]["options"]} == {"a", "b", "c"}


def test_d004_local_stress_yes_requests_force_before_equation_47():
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id="SP16_D_SIGLOC", registry=app.service.registry)
    _seed(s, "t_w_eff", 8.0)
    s.submit(True)
    assert s.current_node_id == "SP16_I_LOCAL_STRESS_CONTEXT"
    fields = {f["quantity_id"]: f for f in s.current_card()["fields"]}
    assert fields["sp16_local_load_F"]["required"] is True
    s.submit({
        "sp16_local_load_case_8_2_2": "FIG6_A_WELDED",
        "sp16_local_load_F": 100000.0,
        "sp16_local_bearing_width_b": 100.0,
        "sp16_local_distribution_h": 20.0,
    })
    values = s.plain_values()
    assert values["sp16_local_load_F"] == 100000.0
    assert values["sp16_local_lef"] == 140.0
    assert values["sigma_loc_value"] > 0.0
    # Starting at the middle of the bending route may later block on unrelated
    # section-field inputs, but Eq. (47) itself must have executed successfully.
    assert "SP16_C_SIGMA_LOC_47" in s.visited_node_ids


def test_d006_internal_required_r_provenance_object_is_hidden_from_guided_ui():
    app = FireUI1Application.from_package_root(ROOT)
    excluded = set(app.model.presentation_policy.get("guided_excluded_nodes", []))
    assert "SP554_FIRE_D4_I_REQUIRED_R_PROVENANCE" in excluded
