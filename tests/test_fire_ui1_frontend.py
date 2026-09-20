import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from standard_core.fire_ui1_http import create_local_server, run_server_in_thread

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def local_ui_server():
    server = create_local_server(ROOT, port=0)
    thread = run_server_in_thread(server)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield server, base
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def _json(base, path, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8")), dict(response.headers)


def _reach_geometry_mode(base, sid):
    state = None
    for value in [True, False, "hot_rolled_section"]:
        _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload": value})
    return state


def test_ui11_server_is_loopback_only_and_health_is_dag_locked(local_ui_server):
    server, base = local_ui_server
    assert server.server_address[0] == "127.0.0.1"
    status, body, headers = _json(base, "/api/health")
    assert status == 200 and body["status"] == "ok" and body["local_only"] is True
    assert body["graph_id"] == "sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff"
    assert len(body["graph_sha256"]) == 64
    assert "default-src 'self'" in headers["Content-Security-Policy"]


def test_ui11_static_frontend_is_offline_and_contains_section_editor_and_multi_back(local_ui_server):
    _, base = local_ui_server
    with urlopen(base + "/", timeout=5) as response: html = response.read().decode("utf-8")
    with urlopen(base + "/assets/app.js", timeout=5) as response: js = response.read().decode("utf-8")
    with urlopen(base + "/assets/styles.css", timeout=5) as response: css = response.read().decode("utf-8")
    assert "FIRE Resistance Calculator" in html and "Расчётные величины" in html
    assert "http://" not in html and "https://" not in html
    assert "/api/profile-catalog/families" in js
    assert "historyCursor" in (ROOT / "fire_ui1_web/src/app.ts").read_text(encoding="utf-8")
    assert "Ответ изменяет только текущую ветвь DAG" not in js
    assert "section-composition-grid" in css and "profile-preview" in css


def test_ui11_contract_uses_presentation_policy_and_new_entry(local_ui_server):
    _, base = local_ui_server
    status, contract, _ = _json(base, "/api/ui-contract")
    assert status == 200
    assert contract["counts"] == {"quantities": 922, "nodes": 734, "edges": 1246, "interactive_nodes": 176, "result_nodes": 54}
    assert contract["entry_node_id"] == "SP554_D_LOAD_BEARING"
    assert contract["presentation_policy"]["deferred_nodes"]["SP554_H_REQUIRED_R"] == "post_actual_fire_resistance"
    assert contract["presentation_policy"]["deferred_nodes"]["SP554_D_FIRE_REGIME"] == "thermal_after_critical_temperature"
    assert "SP554_I_BUILDING_USE" in contract["presentation_policy"]["hidden_normative_nodes"]


def test_ui11_guided_start_skips_orphan_rreq_fire_regime_seismic_and_software_questions(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {})
    sid = created["session_id"]
    assert created["current_card"]["node_id"] == "SP554_D_LOAD_BEARING"
    state = _reach_geometry_mode(base, sid)
    assert state["current_card"]["node_id"] == "SP554_D_GEOMETRY_MODE"
    history_ids = [x["node_id"] for x in state["state"]["interaction_history"]]
    assert history_ids == ["SP554_D_LOAD_BEARING", "SP554_D_ENCLOSING", "SP554_D_PRODUCT_ROUTE"]
    auto = {x["quantity_id"]: x for x in state["state"]["ledger"] if x["source_kind"] == "AUTO_RESOLVED"}
    assert auto["determination_method"]["value"] == "calculation_analytical"
    assert auto["uses_software_complex"]["value"] is True
    assert "required_fire_resistance_min" not in state["state"]["values"]
    assert "fire_temperature_regime" not in state["state"]["values"]
    assert "is_seismic_region" not in state["state"]["values"]


def test_profile_catalog_api_exposes_real_families_profiles_and_exact_row(local_ui_server):
    _, base = local_ui_server
    _, fam, _ = _json(base, "/api/profile-catalog/families")
    assert fam["family_count"] == 37 and fam["profile_count"] == 4069
    _, rows, _ = _json(base, "/api/profile-catalog/families/3/profiles")
    row = next(x for x in rows["profiles"] if x["designation"] == "20К1")
    _, resolved, _ = _json(base, f"/api/profile-catalog/resolve?family_id=3&designation=20%D0%9A1&source_row_id={row['source_row_id']}")
    assert resolved["designation"] == "20К1"
    assert resolved["dimensions"]["h_mm"] > 0 and resolved["catalog_properties_interim"]["A_mm2"] > 0


def test_catalog_geometry_input_requires_no_manual_provenance(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid = created["session_id"]
    _reach_geometry_mode(base, sid)
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload": "catalog_section"})
    assert state["current_card"]["node_id"] == "SP554_I_CATALOG"
    payload = {
        "section_catalog_standard": "ГОСТ 26020",
        "section_designation": "20К1",
        "section_family": "i_section",
        "sp16_i_symmetry_class": "double_symmetric",
        "section_catalog_family_id": 3,
        "section_catalog_source_row_id": 654,
    }
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload": payload})
    assert state["state"]["status"] == "AWAITING_INPUT"
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    assert state["state"]["values"]["section_designation"]["provenance"] is None
    assert state["state"]["values"]["A_gross"]["value"] > 5000
    assert state["state"]["values"]["J_x"]["value"] > state["state"]["values"]["J_y"]["value"]


def test_rreq_provenance_is_optional_in_primary_ui_contract(local_ui_server):
    _, base = local_ui_server
    _, contract, _ = _json(base, "/api/ui-contract")
    card = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_H_REQUIRED_R")
    assert card["presentation"]["component"] == "required_r_selector"
    assert card["provenance_mode"] == "optional"
    assert card["external_handoff"] is False


def test_ui11_edit_endpoint_replays_and_invalidates_downstream(local_ui_server):
    _, base = local_ui_server
    _, state, _ = _json(base, "/api/sessions", "POST", {}); sid = state["session_id"]
    state = _reach_geometry_mode(base, sid)
    assert "section_product_route" in state["state"]["values"]
    _, edited, _ = _json(base, f"/api/sessions/{sid}/answers/SP554_D_LOAD_BEARING", "PUT", {"payload": False})
    assert edited["state"]["current_node_id"] == "SP554_R_NOT_LOAD_BEARING_OUTSIDE_R_SCOPE"
    assert "section_product_route" not in edited["state"]["values"]
    assert len(edited["state"]["interaction_history"]) == 1


def test_ui11_saved_snapshot_restores_only_against_same_dag(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid = created["session_id"]
    _, created, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload": True})
    snapshot = created["state"]
    _, restored, _ = _json(base, "/api/sessions/restore", "POST", {"snapshot": snapshot})
    assert restored["session_id"] != sid and restored["state"]["current_node_id"] == "SP554_D_ENCLOSING"
    bad = dict(snapshot); bad["graph_sha256"] = "0" * 64
    req = Request(base + "/api/sessions/restore", data=json.dumps({"snapshot": bad}).encode("utf-8"), method="POST", headers={"Content-Type": "application/json"})
    with pytest.raises(HTTPError) as exc: urlopen(req, timeout=5)
    assert exc.value.code == 400


def test_ui11_frontend_source_contains_no_embedded_normative_equation_implementation():
    source = (ROOT / "fire_ui1_web" / "src" / "app.ts").read_text(encoding="utf-8")
    assert "standard_core" not in source and "sp554_fire" not in source and "_critical_selection" not in source
    assert "gamma_t_required /" not in source and "gamma_e_required /" not in source
    assert "/api/sessions" in source


def test_ui11_typescript_build_is_materialized_and_source_tracked():
    source = ROOT / "fire_ui1_web/src/app.ts"; build = ROOT / "fire_ui1_web/dist/app.js"; config = ROOT / "fire_ui1_web/tsconfig.json"
    assert source.is_file() and build.is_file() and config.is_file() and build.stat().st_size > 10_000
    assert "void boot();" in source.read_text(encoding="utf-8") and "boot();" in build.read_text(encoding="utf-8")


def test_ui11_path_traversal_and_unknown_api_are_not_served(local_ui_server):
    _, base = local_ui_server
    for path in ["/../README.md", "/api/not-real"]:
        with pytest.raises(HTTPError) as exc: urlopen(base + path, timeout=5)
        assert exc.value.code == 404



def test_ui12_frontend_has_shape_specific_icons_and_manual_arbitrary_properties():
    source = (ROOT / "fire_ui1_web/src/app.ts").read_text(encoding="utf-8")
    for token in ["I_ROLLED_DSYMM", "RHS_SHS", "CHS", "CHANNEL", "ANGLE", "TEE", "Z_SECTION", "C_LIPPED_SECTION"]:
        assert token in source
    assert "2D-редактор контура" not in source
    assert "Готовые характеристики сечения" in source
    assert "P_heated_m" in source


def test_ui12_parametric_contract_is_shape_dependent_and_double_branch_is_active(local_ui_server):
    _, base = local_ui_server
    _, contract, _ = _json(base, "/api/ui-contract")
    par = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_I_PARAMETRIC")
    arb = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_I_ARBITRARY")
    dbl = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_I_DOUBLE_BRANCH")
    assert par["presentation"]["component"] == "parametric_section_editor"
    assert arb["presentation"]["component"] == "manual_section_properties_editor"
    assert dbl["presentation"]["component"] == "double_branch_section_editor"
    geom = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_D_GEOMETRY_MODE")
    assert any(o["value"] == "double_branch_section" for o in geom["options"])


def test_ui12_double_branch_catalog_geometry_continues_to_material(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid=created["session_id"]
    _reach_geometry_mode(base,sid)
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"double_branch_section"})
    assert state["current_card"]["node_id"] == "SP554_I_DOUBLE_BRANCH"
    payload={"double_branch_symmetry_axis":"y","double_branch_spacing_mm":300.0,"double_branch_family_id":3,"double_branch_designation":"20К1","double_branch_source_row_id":654}
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":payload})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    assert state["state"]["values"]["A_gross"]["value"] > 10000
    assert state["state"]["values"]["J_y"]["value"] > 2*13_000_000


def test_ui12_parametric_chs_uses_shape_specific_inputs_and_continues(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid=created["session_id"]
    _reach_geometry_mode(base,sid)
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"parametric_section"})
    assert state["current_card"]["node_id"] == "SP554_I_PARAMETRIC"
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":{"section_family":"chs","sec_h":219.0,"t_w":8.0}})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    assert state["state"]["values"]["section_is_pipe"]["value"] is True
    assert state["state"]["values"]["A_gross"]["value"] > 0


def test_ui12_manual_arbitrary_properties_continue_and_materialize_heated_perimeter(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid=created["session_id"]
    _reach_geometry_mode(base,sid)
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"arbitrary_section"})
    manual={"A_gross":5000,"J_x":4e7,"J_y":1e7,"W_el_x_pos":4e5,"W_el_x_neg":4e5,"W_el_y_pos":1e5,"W_el_y_neg":1e5,"W_pl_x":4.5e5,"W_pl_y":1.2e5,"P_heated_m":1.2,"section_family":"other"}
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":{"section_geometry_2d":manual}})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    assert state["state"]["values"]["P_heated"]["value"] == pytest.approx(1.2)


def test_ui12_catalog_gost_r_57837_20k1_continues_past_geometry_provider(local_ui_server):
    _, base = local_ui_server
    _, rows, _ = _json(base, "/api/profile-catalog/families/35/profiles")
    row = next(x for x in rows["profiles"] if x["designation"] == "20К1")
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid=created["session_id"]
    _reach_geometry_mode(base,sid)
    _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"catalog_section"})
    payload={"section_catalog_standard":"ГОСТ Р 57837-2017","section_designation":"20К1","section_family":"i_section","sp16_i_symmetry_class":"double_symmetric","section_catalog_family_id":35,"section_catalog_source_row_id":row["source_row_id"]}
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":payload})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    assert state["state"]["values"]["A_gross"]["value"] == pytest.approx(5269.0)


def test_ui13_contract_uses_compact_material_strength_editor_and_hides_legacy_material_inputs(local_ui_server):
    _, base = local_ui_server
    _, contract, _ = _json(base, "/api/ui-contract")
    card = next(c for c in contract["node_cards"] if c["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR")
    assert card["presentation"]["component"] == "material_strength_editor"
    required = {f["quantity_id"] for f in card["fields"] if f["required"]}
    assert required == {"steel_product_form", "steel_grade", "steel_strength_interval_key"}
    assert "steel_delivery_standard" not in {f["quantity_id"] for f in card["fields"]}
    hidden = set(contract["presentation_policy"]["hidden_normative_nodes"])
    assert {"SP554_I_STEEL_GRADE", "SP554_I_STEEL_PRODUCT_DATA"}.issubset(hidden)


def test_ui13_material_catalog_exposes_exact_tables_grades_and_intervals(local_ui_server):
    _, base = local_ui_server
    _, catalog, _ = _json(base, "/api/material-strength/catalog")
    products = {p["value"]: p for p in catalog["products"]}
    assert products["parallel_flange_i"]["source_table"] == "В.4"
    assert products["shaped_rolled"]["source_table"] == "В.5"
    assert products["tube"]["source_table"] == "В.3"
    c255b = next(g for g in products["parallel_flange_i"]["grades"] if g["steel_grade"] == "С255Б")
    first = c255b["intervals"][0]
    assert first["interval_label"] == "до 10 мм включ."
    assert first["Ryn_MPa"] == 255 and first["Ry_MPa"] == 250
    _, preview, _ = _json(base, f"/api/material-strength/resolve?product_form=parallel_flange_i&steel_grade=%D0%A1255%D0%91&interval_key={first['interval_key'].replace('|','%7C')}")
    assert preview["Ryn_MPa"] == 255 and preview["Run_MPa"] == 380


def test_ui13_catalog_20k1_auto_context_and_material_runtime_continue_to_weakening(local_ui_server):
    _, base = local_ui_server
    _, rows, _ = _json(base, "/api/profile-catalog/families/35/profiles")
    row = next(x for x in rows["profiles"] if x["designation"] == "20К1")
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid = created["session_id"]
    _reach_geometry_mode(base, sid)
    _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"catalog_section"})
    payload={"section_catalog_standard":"ГОСТ Р 57837-2017","section_designation":"20К1","section_family":"i_section","sp16_i_symmetry_class":"double_symmetric","section_catalog_family_id":35,"section_catalog_source_row_id":row["source_row_id"]}
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":payload})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    _, ctx, _ = _json(base, f"/api/sessions/{sid}/material-strength-context")
    assert ctx["suggested_product_form"] == "parallel_flange_i"
    assert ctx["exact_governing_thickness_mm"] == pytest.approx(10.0)
    _, catalog, _ = _json(base, "/api/material-strength/catalog")
    prod = next(p for p in catalog["products"] if p["value"] == "parallel_flange_i")
    grade = next(g for g in prod["grades"] if g["steel_grade"] == "С255Б")
    interval = next(r for r in grade["intervals"] if r["thickness_interval"]["max_mm"] == 10)
    mat={"steel_product_form":"parallel_flange_i","steel_grade":"С255Б","steel_strength_interval_key":interval["interval_key"],"governing_product_thickness_mm":10.0}
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":mat})
    assert state["state"]["status"] == "AWAITING_INPUT"
    assert state["current_card"]["node_id"] == "SP554_I_SECTION_WEAKENING"
    vals = state["state"]["values"]
    assert vals["sp16_material_table_route"]["value"] == "V4"
    assert vals["fy_norm"]["value"] == 255.0
    assert vals["fu_norm"]["value"] == 380.0
    assert vals["Ry_annex"]["value"] == 250.0
    assert vals["Ru_annex"]["value"] == 370.0
    assert "steel_delivery_standard" not in vals


def test_ui13_parametric_chs_context_suggests_tube_and_actual_wall_thickness(local_ui_server):
    _, base = local_ui_server
    _, created, _ = _json(base, "/api/sessions", "POST", {}); sid=created["session_id"]
    _reach_geometry_mode(base,sid)
    _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":"parametric_section"})
    _, state, _ = _json(base, f"/api/sessions/{sid}/answer", "POST", {"payload":{"section_family":"chs","sec_h":219.0,"t_w":8.0}})
    assert state["current_card"]["node_id"] == "SP554_I_STEEL_STRENGTH_EDITOR"
    _, ctx, _ = _json(base, f"/api/sessions/{sid}/material-strength-context")
    assert ctx["suggested_product_form"] == "tube"
    assert ctx["exact_governing_thickness_mm"] == pytest.approx(8.0)


def test_ui13_frontend_contains_material_dropdown_editor_without_delivery_standard_input():
    source = (ROOT / "fire_ui1_web/src/app.ts").read_text(encoding="utf-8")
    assert "renderMaterialStrengthEditor" in source
    assert "/api/material-strength/catalog" in source
    assert "Толщина для выбора Ryn" in source
    material_block = source[source.index("async function renderMaterialStrengthEditor"):source.index("function renderSectionWeakeningEditor")]
    assert "steel_delivery_standard" not in material_block


def test_fire_ui15_frontend_guards_duplicate_submit_race():
    source = (ROOT / "fire_ui1_web/src/app.ts").read_text(encoding="utf-8")
    assert "let submitInFlight = false;" in source
    assert "if (!envelope || submitInFlight) return;" in source
    assert "submitInFlight = true;" in source
    assert "submitInFlight = false;" in source
