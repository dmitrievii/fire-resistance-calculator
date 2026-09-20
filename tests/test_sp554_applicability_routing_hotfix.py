import json
from pathlib import Path

import jsonschema
import pytest

from standard_core.fire_sp554_runtime import sp554_fire_mechanical_guided_workflow

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.46_sp554_applicability_routing_hotfix.json"


def _dag():
    return json.loads(DAG.read_text(encoding="utf-8"))


def _base(route_name: str, route: dict) -> dict:
    return {
        "member_route": route_name,
        "steel_strength_group": "ordinary",
        "high_strength_gost9651_qualified": False,
        "fire_resistant_gost9651_qualified": False,
        "fy_norm_n_mm2": 240.0,
        "E_norm_n_mm2": 206000.0,
        "route": route,
    }


def _nm(mode="in_plane", **extra):
    route = {
        "N_n": 400_000.0,
        "A_net_mm2": 5000.0,
        "A_gross_mm2": 5500.0,
        "gamma_c_strength": 1.0,
        "gamma_c_stability": 1.0,
        "M_x_nmm": 24_000_000.0,
        "M_y_nmm": 0.0,
        "B_nmm2": 0.0,
        "W_pl_x_eff_mm3": 600_000.0,
        "W_pl_y_eff_mm3": 300_000.0,
        "W_omega_eff_mm4": 1e8,
        "stability_mode": mode,
        "stress_state": "compression_plus_bending",
        "section_is_constant": True,
        "moment_plane_is_symmetry": True,
        "mef_gt_20": False,
        "section_is_box": False,
        "sp16_table21_type": "1",
        "major_axis_is_x": True,
        "mu_length_sp16": 1.0,
        "member_length_mm": 2500.0,
        "J_min_mm4": 4_000_000.0,
        "phi_e_sp16": 0.5,
    }
    route.update(extra)
    return _base("combined_nm", route)


def test_hotfix_dag_schema_identity_and_size_stable():
    schema = json.loads((ROOT / "normative_graph" / "dag_schema.json").read_text(encoding="utf-8"))
    d = _dag()
    jsonschema.Draft202012Validator(schema).validate(d)
    assert d["graph_id"] == "sp16_sp554_dag_v0-3-46_sp554_applicability_routing_hotfix"
    assert len(d["quantities"]) == 748
    assert len(d["nodes"]) == 657
    assert len(d["edges"]) == 1108


def test_10_6_10_7_have_explicit_class_and_material_system_gate():
    nodes = {n["id"]: n for n in _dag()["nodes"]}
    for node_id in ("SP554_C_10_6", "SP554_C_10_7"):
        node = nodes[node_id]
        text = json.dumps(node["applicability"], ensure_ascii=False, sort_keys=True)
        assert '"quantity_id": "section_family"' in text
        assert '"value": "i_section"' in text
        assert '"quantity_id": "beam_is_bisteel"' in text
        assert '"quantity_id": "sp16_section_class"' in text
        assert '"value": "1"' in text and '"value": "2"' in text
        assert '"quantity_id": "section_is_pipe"' in text


def test_11_7_uses_table21_type3_not_nds_class3():
    node = {n["id"]: n for n in _dag()["nodes"]}["SP554_K_NM_11_7"]
    consumes = {c["quantity_id"] for c in node["consumes"]}
    assert "sp16_table21_type" in consumes
    assert "sp16_section_class" not in consumes
    text = json.dumps(node["classification_rules"], ensure_ascii=False, sort_keys=True)
    assert '"quantity_id": "sp16_table21_type"' in text
    assert '"quantity_id": "sp16_section_class"' not in text


def test_11_1_and_11_2_applicability_is_self_contained():
    nodes = {n["id"]: n for n in _dag()["nodes"]}
    a11 = json.dumps(nodes["SP554_C_11_1"]["applicability"], sort_keys=True)
    assert "compression_plus_bending" in a11
    assert "tension_plus_bending" in a11
    a12 = json.dumps(nodes["SP554_C_11_2"]["applicability"], sort_keys=True)
    for token in ("compression_plus_bending", "mef_gt_20", "section_is_constant", "moment_plane_is_symmetry"):
        assert token in a12


def test_runtime_10_6_accepts_class1_ordinary_i_and_class2_bisteel_only():
    common = {"M_x_nmm":72e6, "phi_b_sp16":0.75, "W_pl_x_eff_mm3":1e6, "section_family":"i_section"}
    ok1 = _base("bending", {"gamma_c":1.0,"checks":{"eq_10_6":{**common,"beam_is_bisteel":False,"sp16_section_class":"1"}}})
    assert sp554_fire_mechanical_guided_workflow(ok1)["gamma_T_governing_formula_ref"] == "10.6"
    ok2 = _base("bending", {"gamma_c":1.0,"checks":{"eq_10_6":{**common,"beam_is_bisteel":True,"sp16_section_class":"2"}}})
    assert sp554_fire_mechanical_guided_workflow(ok2)["gamma_T_governing_formula_ref"] == "10.6"
    bad = _base("bending", {"gamma_c":1.0,"checks":{"eq_10_6":{**common,"beam_is_bisteel":False,"sp16_section_class":"2"}}})
    with pytest.raises(ValueError, match="requires SP16 NDS class 1"):
        sp554_fire_mechanical_guided_workflow(bad)


def test_runtime_11_2_fails_closed_on_each_new_gate():
    assert sp554_fire_mechanical_guided_workflow(_nm())["status"] == "COMPLETE"
    with pytest.raises(ValueError, match="constant section"):
        sp554_fire_mechanical_guided_workflow(_nm(section_is_constant=False))
    with pytest.raises(ValueError, match="symmetry plane"):
        sp554_fire_mechanical_guided_workflow(_nm(moment_plane_is_symmetry=False))
    with pytest.raises(ValueError, match="m_eff > 20"):
        sp554_fire_mechanical_guided_workflow(_nm(mef_gt_20=True))


def test_runtime_11_1_rejects_non_nm_stress_state_and_tension_stability():
    with pytest.raises(ValueError, match="11.1 requires stress_state"):
        sp554_fire_mechanical_guided_workflow(_nm(stress_state="central_compression"))
    tension = _nm(mode="none", stress_state="tension_plus_bending")
    tension["route"].pop("mu_length_sp16", None)
    tension["route"].pop("member_length_mm", None)
    tension["route"].pop("J_min_mm4", None)
    tension["route"].pop("phi_e_sp16", None)
    assert sp554_fire_mechanical_guided_workflow(tension)["gamma_T_governing_formula_ref"] == "11.1"
    with pytest.raises(ValueError, match="strength only"):
        sp554_fire_mechanical_guided_workflow(_nm(stress_state="tension_plus_bending"))


def test_runtime_11_7_accepts_table21_type3_as_alternative_to_major_symmetry():
    c = _nm(
        mode="biaxial_nonbox",
        M_y_nmm=12e6,
        phi_ey_sp16=0.65,
        c_sp16=0.81,
        major_axis_is_x=False,
        moment_plane_is_symmetry=False,
        sp16_table21_type="3",
    )
    c["route"].pop("phi_e_sp16", None)
    result = sp554_fire_mechanical_guided_workflow(c)
    assert any(x["formula_ref"] == "11.6" for x in result["gamma_T_candidates"])
    c["route"]["sp16_table21_type"] = "2"
    with pytest.raises(ValueError, match="Table 21 section type 3"):
        sp554_fire_mechanical_guided_workflow(c)
