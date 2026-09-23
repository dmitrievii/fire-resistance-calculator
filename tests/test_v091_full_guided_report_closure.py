from __future__ import annotations

import math
import sys
import types

try:  # pragma: no cover - lightweight local validation only
    import streamlit  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    stub = types.ModuleType("streamlit")
    stub.session_state = {}
    stub.rerun = lambda: None
    stub.error = lambda message: (_ for _ in ()).throw(AssertionError(str(message)))
    sys.modules["streamlit"] = stub

import streamlit_app as ui
import streamlit_app_core as core
from standard_core.report_ir5 import build_report_ir5
from standard_core.sp16_mech7_v083_full_route_overlay import FIRE_LOAD_MODE_NODE_ID
from streamlit_expertise_report_v091 import render_expertise_narrative_markdown_v091


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


def test_v091_real_guided_session_closes_through_fire_result_and_same_ledger_report(monkeypatch):
    """Current production UI -> SP16 -> SP554 -> thermal -> R-check -> REPORT-IR5.

    The report assertions remain the v0.91 final-SP554 closure assertions, while
    the active UI action input follows the cumulative v0.92 canonical contract:
    Mz strong-axis bending, My weak-axis bending, Mx torsion, Qz/Qy shear.
    """
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(core, "_st", lambda: fake_st)

    app = ui._new_application()
    sid = app.create_session()["session_id"]
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
        "ambient_load_combination": {"schema": "v091_closure", "kind": "ambient"},
        "ambient_N_force": -600_000.0,
        "ambient_M_z": 0.0,
        "ambient_M_y": 0.0,
        "ambient_Q_z": 0.0,
        "ambient_Q_y": 0.0,
        "ambient_M_x": 0.0,
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
    _submit(app, sid, "SP16_I_V078_GAMMA_C_COMPRESSION_CASE", "default_unlisted_case_note_5")
    _submit(app, sid, "SP16_I_MECH7_COMPRESSION_SLENDERNESS", {
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    })
    _submit(app, sid, "SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM", True)

    _submit(app, sid, FIRE_LOAD_MODE_NODE_ID, "same_as_ambient")
    _submit(app, sid, "SP554_D_VERIFICATION_PLAN_CONFIRM", True)
    _submit(app, sid, "SP554_D_GAMMA_T_METHOD", "section_formulas")

    values = session.plain_values()
    assert session.current_node_id == "SP554_I_EXPOSURE"
    assert values["fire_d2_critical_temperature_status"] == "COMPLETE"

    # Final SP554 §9.2 must be independent of any user/manual E_norm seed.
    history_ids = [row["node_id"] for row in session.interaction_history]
    assert all("E_NORM" not in node_id.upper() for node_id in history_ids)

    _submit(app, sid, "SP554_I_EXPOSURE", "four_sides")
    _submit(app, sid, "SP554_D_FIRE_REGIME", "standard")
    _submit(app, sid, "SP554_D_AFTER_UNPROTECTED", "check_requirement")
    _submit(app, sid, "SP554_H_REQUIRED_R", 5.0)

    values = session.plain_values()
    assert values["unprotected_compliance"] is True
    assert values["unprotected_fire_resistance_min"] > values["required_fire_resistance_min"]
    assert math.isclose(values["required_fire_resistance_min"], 5.0, rel_tol=0.0, abs_tol=0.0)

    _submit(app, sid, "SP554_D_AFTER_UNPROTECTED", "finish_unprotected")
    assert session.current_node_id == "SP554_R_UNPROTECTED_CALCULATION_COMPLETE"
    assert session.status == "RESULT"
    assert session.branch_failures == []

    report = build_report_ir5(app.service.model, session)
    markdown = render_expertise_narrative_markdown_v091(report)

    # The terminal report must be a projection of the same ledger/session.
    assert report["session_status"] == "RESULT"
    assert report["audit"]["summary_recomputed_engineering_checks"] is False
    assert report["audit"]["summary_inferred_numeric_check_verdicts"] is False
    assert report["audit"]["summary_inferred_governing_result"] is False

    # v0.91 final-SP554 evidence must survive all the way into the human report.
    assert "206000" in markdown
    assert "пользовательское `E_norm` не используется" in markdown
    assert "Критическая температура" in markdown
    assert "Предел огнестойкости" in markdown or "огнестойк" in markdown.lower()
    assert "5" in markdown
