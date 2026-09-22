from __future__ import annotations

import math
import sys
import types

# The production entrypoint installs the cumulative Streamlit adapter chain at
# import time.  Local validation environments may not have Streamlit installed;
# the route test needs only session_state/rerun/error because it drives the same
# public submit adapter without rendering widgets.
try:  # pragma: no cover - exercised only in lightweight local validation
    import streamlit  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    stub = types.ModuleType("streamlit")
    stub.session_state = {}
    stub.rerun = lambda: None
    stub.error = lambda message: (_ for _ in ()).throw(AssertionError(str(message)))
    sys.modules["streamlit"] = stub

import streamlit_app as ui
import streamlit_app_core as core
from standard_core.sp16_mech7_v083_full_route_overlay import (
    FIRE_LOAD_MODE_NODE_ID,
    FIRE_LOAD_MODE_QID,
    GAMMA_E_NODE_ID,
    GAMMA_E_REQUIRED_QID,
    GRAPH_SUFFIX,
    LEGACY_TABLE1_COMPRESSION_NODES,
)
from streamlit_guided_ux_v083 import _install_render_defaults


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.errors: list[str] = []

    def rerun(self) -> None:
        return None

    def error(self, message: object) -> None:
        self.errors.append(str(message))
        raise AssertionError(str(message))


def _submit(app, sid: str, expected_node: str, payload) -> None:
    session = app.service.get_session(sid)
    assert session.current_node_id == expected_node, (
        f"expected guided node {expected_node}, got {session.current_node_id}; "
        f"status={session.status}, failures={session.branch_failures}"
    )
    card = app.session_payload(sid)["current_card"]
    assert card is not None and card["node_id"] == expected_node
    ui._submit(app, sid, card, payload, None, False)
    assert not session.status.startswith("BLOCKED"), (
        f"route blocked after {expected_node}: {session.status}; "
        f"failures={session.branch_failures}"
    )


def test_v083_ui_defaults_are_explicit_without_auto_submitting_answers():
    calls: list[tuple[str, object]] = []

    class DummyCore:
        @staticmethod
        def _render_generic(card, old_payload, old_provenance, mode_key):
            calls.append((card["node_id"], old_payload))
            return old_payload, old_provenance, True

    dummy = DummyCore()
    _install_render_defaults(dummy)

    dummy._render_generic({"node_id": "SP554_D_GOST27751_GAMMA_CT"}, None, None, "new")
    dummy._render_generic({"node_id": FIRE_LOAD_MODE_NODE_ID}, None, None, "new")

    assert calls == [
        ("SP554_D_GOST27751_GAMMA_CT", False),
        (FIRE_LOAD_MODE_NODE_ID, "same_as_ambient"),
    ]


def test_v083_contract_has_real_fire_selector_and_gamma_e_consumer_output():
    app = ui._new_application()
    assert GRAPH_SUFFIX in app.model.graph["graph_id"]

    quantities = {row["id"]: row for row in app.model.graph["quantities"]}
    assert quantities[FIRE_LOAD_MODE_QID]["data_type"] == "enum"
    assert [row["value"] for row in quantities[FIRE_LOAD_MODE_QID]["enum_values"]] == [
        "same_as_ambient",
        "separate",
    ]

    nodes = {row["id"]: row for row in app.model.graph["nodes"]}
    gamma_outputs = {row["quantity_id"] for row in nodes[GAMMA_E_NODE_ID]["produces"]}
    assert {"gamma_e_compression", GAMMA_E_REQUIRED_QID} <= gamma_outputs
    assert all(
        edge.get("to_node_id") not in LEGACY_TABLE1_COMPRESSION_NODES
        for edge in app.model.graph["edges"]
    )


def test_v083_new_calculation_reaches_terminal_fire_result_without_internal_quantity_seeding(monkeypatch):
    """Drive the real production guided route from a new session to terminal R.

    No test call uses GuidedCalculationSession._set_quantity or seeds an internal
    quantity.  Every value enters through the same Streamlit submit adapter used
    by the application.  The only session-state assignment below represents the
    visible SP16 Table-3 selector embedded in the material editor; the production
    submit adapter itself materializes that user input into the ledger.
    """
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(core, "_st", lambda: fake_st)

    app = ui._new_application()
    created = app.create_session()
    sid = created["session_id"]
    session = app.service.get_session(sid)

    _submit(app, sid, "SP554_D_LOAD_BEARING", True)
    _submit(app, sid, "SP554_D_ENCLOSING", False)
    _submit(app, sid, "SP554_D_PRODUCT_ROUTE", "hot_rolled_section")
    _submit(app, sid, "SP554_D_GEOMETRY_MODE", "catalog_section")

    profile = next(row for row in app.profile_catalog.list_profiles(3) if row["designation"] == "20К1")
    _submit(app, sid, "SP554_I_CATALOG", {
        "section_catalog_standard": "ГОСТ 26020",
        "section_designation": "20К1",
        "section_family": "i_section",
        "sp16_i_symmetry_class": "double_symmetric",
        "section_catalog_family_id": 3,
        "section_catalog_source_row_id": profile["source_row_id"],
    })

    material_catalog = app.material_strength_catalog()
    product = next(row for row in material_catalog["products"] if row["value"] == "parallel_flange_i")
    grade = next(row for row in product["grades"] if row["steel_grade"] == "С255Б")
    interval = next(row for row in grade["intervals"] if row["thickness_interval"]["max_mm"] == 10)
    fake_st.session_state["fire:v072:material-safety:SP554_I_STEEL_STRENGTH_EDITOR"] = "other_conforming"
    _submit(app, sid, "SP554_I_STEEL_STRENGTH_EDITOR", {
        "steel_product_form": "parallel_flange_i",
        "steel_grade": "С255Б",
        "steel_strength_interval_key": interval["interval_key"],
        "governing_product_thickness_mm": 10.0,
    })

    _submit(app, sid, "SP554_I_SECTION_WEAKENING", {
        "schema": "section_weakening_model_v0.49",
        "holes_present": False,
        "model": "none",
    })
    _submit(app, sid, "SP554_D_GOST27751_GAMMA_CT", False)
    _submit(app, sid, "SP16_I_AMBIENT_LOADS", {
        "ambient_load_combination": {"schema": "v083_e2e", "kind": "ambient"},
        "ambient_N_force": -600_000.0,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_Q_x": 0.0,
        "ambient_Q_y": 0.0,
        "ambient_T_torsion": 0.0,
        "ambient_B_bimoment": 0.0,
    })
    _submit(app, sid, "SP16_D_AMBIENT_CENSUS_CONFIRM", True)
    _submit(app, sid, "SP16_D_MECH7_FATIGUE_REQUIRED", False)
    _submit(app, sid, "SP16_D_MECH7_BRITTLE_REQUIRED", False)
    _submit(app, sid, "SP16_I_V076_EFFECTIVE_LENGTH_ZY", {
        "member_length_mm": 4500.0,
        "z": {"method": "table30", "scheme_id": "S2"},
        "y": {"method": "table30", "scheme_id": "S2"},
    })

    # The user classifies SP16 Table 1 exactly once in the entire calculation.
    _submit(app, sid, "SP16_I_V078_GAMMA_C_COMPRESSION_CASE", "default_unlisted_case_note_5")
    _submit(app, sid, "SP16_I_MECH7_COMPRESSION_SLENDERNESS", {
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    })
    _submit(app, sid, "SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM", True)

    # This is the default displayed by v0.83; submit it exactly as a user pressing Continue.
    _submit(app, sid, FIRE_LOAD_MODE_NODE_ID, "same_as_ambient")
    _submit(app, sid, "SP554_D_VERIFICATION_PLAN_CONFIRM", True)
    _submit(app, sid, "SP554_D_GAMMA_T_METHOD", "section_formulas")

    values = session.plain_values()
    assert session.current_node_id == "SP554_I_EXPOSURE"
    assert values["fire_d2_critical_temperature_status"] == "COMPLETE"
    assert math.isclose(values[GAMMA_E_REQUIRED_QID], values["gamma_e_compression"], rel_tol=0.0, abs_tol=0.0)
    assert values["fire_load_case"]["source"] == "inherited_from_ambient"
    assert values["fire_load_case"]["actions"] == values["ambient_load_case"]["actions"]

    history_ids = [row["node_id"] for row in session.interaction_history]
    assert history_ids.count("SP16_I_V078_GAMMA_C_COMPRESSION_CASE") == 1
    assert not (LEGACY_TABLE1_COMPRESSION_NODES & set(history_ids))
    assert "SP554_I_COMPRESSION_CONTEXT" not in history_ids

    _submit(app, sid, "SP554_I_EXPOSURE", "four_sides")
    # Descendant v0.84 auto-executes the former method selector and the combined
    # thermal card submits the visible T0 field together with the standard regime.
    _submit(app, sid, "SP554_D_FIRE_REGIME", "standard")
    _submit(app, sid, "SP554_D_AFTER_UNPROTECTED", "check_requirement")
    _submit(app, sid, "SP554_H_REQUIRED_R", 5.0)

    values = session.plain_values()
    assert values["unprotected_compliance"] is True
    assert values["unprotected_fire_resistance_min"] > values["required_fire_resistance_min"]
    assert values["fire_resistance_designation"].startswith("R ")

    # After compliance has been checked, the UI intentionally returns to the
    # action card so the user can explicitly finish or start protection design.
    _submit(app, sid, "SP554_D_AFTER_UNPROTECTED", "finish_unprotected")

    assert session.current_node_id == "SP554_R_UNPROTECTED_CALCULATION_COMPLETE"
    assert session.status == "RESULT"
    assert session.branch_failures == []
    assert session.pending_node_ids == []
    assert session.branch_results[-1] == {
        "node_id": "SP554_R_UNPROTECTED_CALCULATION_COMPLETE",
        "status": "TERMINAL_RESULT",
    }
