import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireDAGModel, GuidedCalculationSession, ExecutionRegistry, FireUIError
from standard_core.fire_ui14_section_weakening import (
    _alpha45_executor,
    _net_geometry_executor,
)

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.55_fire_ui19_sp554_table1_heated_perimeter_matrix.json"
POLICY = ROOT / "data" / "fire_ui19_presentation_policy.json"


def test_single_object_interactive_payload_is_value_not_multi_field_container():
    graph = {
        "graph_id": "single-object",
        "engine_contract": {"expression_language": "expr_v1"},
        "quantities": [{
            "id": "section_weakening_model", "name_ru": "m", "data_type": "object", "role": "geometry_input",
            "canonical_unit": None, "allowed_units": [], "source_policy": {"primary_source_type": "GEOMETRY_INPUT"},
        }],
        "nodes": [{
            "id": "I", "node_type": "input", "owner_standard_id": "X", "title": "m", "normative_refs": [],
            "consumes": [], "produces": [{"quantity_id": "section_weakening_model", "required": True}],
            "input_spec": {"user_prompt": "m"},
        }],
        "edges": [],
    }
    payload = {"holes_present": False}
    s = GuidedCalculationSession(FireDAGModel(graph), entry_node_id="I")
    state = s.submit(payload)
    assert state["values"]["section_weakening_model"]["value"] == payload

    s2 = GuidedCalculationSession(FireDAGModel(graph), entry_node_id="I")
    wrapped = {"section_weakening_model": payload}
    state2 = s2.submit(wrapped)
    assert state2["values"]["section_weakening_model"]["value"] == payload


def test_ui14_dag_metadata_and_weakening_node_are_consistent():
    model = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    assert model.graph["graph_id"] == "sp16_sp554_dag_v0-3-55_fire_ui19_sp554_table1_heated_perimeter_matrix"
    assert "v0.3.55" in model.graph["graph_title"]
    node = model.nodes["SP16_D_WEAKENING"]
    assert node["node_type"] == "calculation"
    assert node["produces"] == [{"quantity_id": "sp16_has_weakening", "required": True, "binding_role": "output"}]


def _base_i_values():
    return {
        "A_gross": 5000.0,
        "J_x": 50_000_000.0,
        "J_y": 5_000_000.0,
        "W_el_x_pos": 400_000.0,
        "W_el_x_neg": 400_000.0,
        "W_el_y_pos": 100_000.0,
        "W_el_y_neg": 100_000.0,
        "sp16_i_symmetry_class": "double_symmetric",
        "t_w": 8.0,
        "section_geometry_2d_normalized": {"template": "i_section", "h_mm": 250.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
    }


def test_ui14_no_holes_resolves_identity_net_properties():
    values = _base_i_values()
    values["section_weakening_model"] = {"schema": "section_weakening_model_v0.47", "holes_present": False, "model": "none"}
    out = _net_geometry_executor(values, {})
    assert out["A_net"] == pytest.approx(values["A_gross"])
    assert out["I_xn"] == pytest.approx(values["J_x"])
    assert out["I_yn"] == pytest.approx(values["J_y"])
    assert out["sp16_shear_weakening_mode"] == "none"
    assert out["sp16_net_removed_area"] == 0.0


def test_ui14_central_web_hole_resolves_basic_net_properties_and_eq45_inputs():
    values = _base_i_values()
    values["section_weakening_model"] = {
        "schema": "section_weakening_model_v0.47",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
    }
    out = _net_geometry_executor(values, {})
    assert out["sp16_net_removed_area"] == pytest.approx(20.0 * 8.0)
    assert out["A_net"] == pytest.approx(5000.0 - 160.0)
    assert out["I_xn"] == pytest.approx(50_000_000.0 - 8.0 * 20.0**3 / 12.0)
    assert out["I_yn"] == pytest.approx(5_000_000.0 - 20.0 * 8.0**3 / 12.0)
    assert out["sp16_shear_weakening_mode"] == "formula45"
    assert out["sp16_wall_hole_pitch_s"] == 80.0
    assert out["sp16_wall_hole_diameter_d"] == 20.0
    alpha = _alpha45_executor(out, {})["sp16_shear_hole_alpha45"]
    assert alpha == pytest.approx(80.0 / 60.0)


def test_ui14_rejects_s_not_greater_than_d_and_non_i_net_route():
    values = _base_i_values()
    values["section_weakening_model"] = {
        "holes_present": True, "model": "central_web_bolt_hole_formula45_v1", "hole_diameter_mm": 20.0, "hole_pitch_mm": 20.0,
    }
    with pytest.raises(FireUIError, match="s >"):
        _net_geometry_executor(values, {})
    values["section_weakening_model"]["hole_pitch_mm"] = 80.0
    values["sp16_i_symmetry_class"] = "not_i"
    with pytest.raises(FireUIError, match="doubly symmetric I-sections"):
        _net_geometry_executor(values, {})


def test_ui14_frontend_removed_old_weakening_fields():
    source = (ROOT / "fire_ui1_web/src/app.ts").read_text(encoding="utf-8")
    block = source[source.index("function renderSectionWeakeningEditor"):source.index("function renderRequiredRSelector")]
    assert "ID активного поперечного сечения" not in block
    assert "Количество" not in block
    assert "weak-count" not in block
    assert "weak-section" not in block
    assert "weak-type" not in block
    assert "weak-zone" not in block
    assert "round_bolt_hole_universal_v1" in block
    assert "s > d" in block


def _reach_20k1_weakening_session():
    from standard_core.fire_ui1_http import FireUI1Application
    app = FireUI1Application.from_package_root(ROOT)
    sid = app.service.create_session()["session_id"]
    session = app.service.get_session(sid)
    for answer in [True, False, "hot_rolled_section", "catalog_section"]:
        session.submit(answer)
    row = next(x for x in app.profile_catalog.list_profiles(35) if x["designation"] == "20К1")
    session.submit({
        "section_catalog_standard": "ГОСТ Р 57837-2017",
        "section_designation": "20К1",
        "section_family": "i_section",
        "sp16_i_symmetry_class": "double_symmetric",
        "section_catalog_family_id": 35,
        "section_catalog_source_row_id": row["source_row_id"],
    })
    catalog = app.material_strength_catalog()
    product = next(p for p in catalog["products"] if p["value"] == "parallel_flange_i")
    grade = next(g for g in product["grades"] if g["steel_grade"] == "С255Б")
    interval = next(r for r in grade["intervals"] if r["thickness_interval"]["max_mm"] == 10)
    session.submit({
        "steel_product_form": "parallel_flange_i",
        "steel_grade": "С255Б",
        "steel_strength_interval_key": interval["interval_key"],
        "governing_product_thickness_mm": 10.0,
    })
    assert session.current_node_id == "SP554_I_SECTION_WEAKENING"
    return session


def test_ui14_real_session_no_holes_submits_raw_object_and_auto_resolves_duplicate_decision():
    session = _reach_20k1_weakening_session()
    state = session.submit({"schema": "section_weakening_model_v0.47", "holes_present": False, "model": "none"})
    assert state["status"] == "AWAITING_INPUT"
    assert session.current_node_id == "SP554_D_GOST27751_GAMMA_CT"
    vals = session.plain_values()
    assert vals["sp16_has_weakening"] is False
    assert vals["A_net"] == pytest.approx(vals["A_gross"])
    assert vals["sp16_shear_hole_alpha45"] == pytest.approx(1.0)
    assert "SP16_D_WEAKENING" not in [row["node_id"] for row in session.interaction_history]
    assert "SP16_D_WEAKENING" in session.visited_node_ids


def test_ui14_real_session_holes_reaches_eq45_without_count_or_active_section_id():
    session = _reach_20k1_weakening_session()
    payload = {
        "schema": "section_weakening_model_v0.47",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
    }
    state = session.submit(payload)
    assert state["status"] == "AWAITING_INPUT"
    assert session.current_node_id == "SP554_D_NET_PROPERTY_REDUCTION"
    state = session.submit("area_only_keep_gross")
    assert state["status"] == "AWAITING_INPUT"
    assert session.current_node_id == "SP554_D_GOST27751_GAMMA_CT"
    vals = session.plain_values()
    assert vals["sp16_has_weakening"] is True
    assert vals["sp16_net_removed_area"] == pytest.approx(20.0 * 6.5)
    assert vals["sp16_shear_hole_alpha45"] == pytest.approx(80.0 / (80.0 - 20.0))
    stored = session.interaction_history[-1]["payload"]
    assert "count" not in stored and "active_transverse_section_id" not in stored and "features" not in stored


def _reach_tee_weakening_session(designation: str = "10КТ1"):
    from standard_core.fire_ui1_http import FireUI1Application
    app = FireUI1Application.from_package_root(ROOT)
    sid = app.service.create_session()["session_id"]
    session = app.service.get_session(sid)
    for answer in [True, False, "hot_rolled_section", "catalog_section"]:
        session.submit(answer)
    row = next(x for x in app.profile_catalog.list_profiles(14) if x["designation"] == designation)
    session.submit({
        "section_catalog_standard": "Тавры колонные",
        "section_designation": designation,
        "section_family": "tee",
        "sp16_i_symmetry_class": "not_i",
        "section_catalog_family_id": 14,
        "section_catalog_source_row_id": row["source_row_id"],
    })
    catalog = app.material_strength_catalog()
    product = next(p for p in catalog["products"] if p["value"] == "shaped_rolled")
    grade = next(g for g in product["grades"] if g["steel_grade"] == "С255")
    interval = next(r for r in grade["intervals"] if r["thickness_interval"]["max_mm"] == 10)
    session.submit({
        "steel_product_form": "shaped_rolled",
        "steel_grade": "С255",
        "steel_strength_interval_key": interval["interval_key"],
        "governing_product_thickness_mm": 10.0,
    })
    assert session.current_node_id == "SP554_I_SECTION_WEAKENING"
    return session


def test_ui15_tee_without_holes_never_exposes_net_producer_and_continues():
    session = _reach_tee_weakening_session()
    state = session.submit({"schema": "section_weakening_model_v0.47", "holes_present": False, "model": "none"})
    assert state["status"] == "AWAITING_INPUT"
    assert session.current_node_id == "SP554_D_GOST27751_GAMMA_CT"
    assert session.current_card()["interactive"] is True
    assert session.plain_values()["A_net"] == pytest.approx(session.plain_values()["A_gross"])
    assert session.plain_values()["I_xn"] == pytest.approx(session.plain_values()["J_x"])
    assert session.plain_values()["I_yn"] == pytest.approx(session.plain_values()["J_y"])
    assert "SP554_G_NET_SECTION_PROPERTIES" in session.visited_node_ids
    assert "SP554_G_NET_SECTION_PROPERTIES" not in [r["node_id"] for r in session.interaction_history]


def test_ui15_all_catalog_tees_without_holes_resolve_identity_net_properties():
    from standard_core.fire_ui1_http import FireUI1Application
    app = FireUI1Application.from_package_root(ROOT)
    for profile in app.profile_catalog.list_profiles(14):
        row = app.profile_catalog.resolve(14, profile["designation"], source_row_id=profile["source_row_id"])
        p = row["catalog_properties_interim"]
        values = {
            "A_gross": p["A_mm2"], "J_x": p["Ix_mm4"], "J_y": p["Iy_mm4"],
            "W_el_x_pos": p["Wx1_mm3"], "W_el_x_neg": p["Wx2_mm3"],
            "W_el_y_pos": p["Wy1_mm3"], "W_el_y_neg": p["Wy2_mm3"],
            "sp16_i_symmetry_class": "not_i",
            "section_weakening_model": {"schema": "section_weakening_model_v0.47", "holes_present": False, "model": "none"},
        }
        out = _net_geometry_executor(values, {})
        assert out["A_net"] == pytest.approx(p["A_mm2"])
        assert out["I_xn"] == pytest.approx(p["Ix_mm4"])
        assert out["I_yn"] == pytest.approx(p["Iy_mm4"])
