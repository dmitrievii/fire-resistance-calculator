from __future__ import annotations

import pytest

from examples.fire_ui16_route_census import run, app_session, auto_answer, Q_DEFAULTS


def _loads(**kw):
    base = dict(N_force=0.0, load_My_local=0.0, load_Mz_local=0.0,
                load_Qy_local=0.0, load_Qz_local=0.0, T_torsion=0.0)
    base.update(kw)
    return base


@pytest.mark.parametrize("name,loads,allowed_nodes", [
    ("tension", _loads(N_force=400e3), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE"}),
    ("compression", _loads(N_force=-400e3), {"SP554_R_B1_INVERSE_OUT_OF_RANGE", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE"}),
    ("My", _loads(load_My_local=30e6), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("Mz", _loads(load_Mz_local=10e6), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("biax", _loads(load_My_local=30e6, load_Mz_local=10e6), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("Qz", _loads(load_Qz_local=50e3), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("MyQz", _loads(load_My_local=30e6, load_Qz_local=50e3), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("NcMy", _loads(N_force=-400e3, load_My_local=30e6), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("NtMy", _loads(N_force=400e3, load_My_local=30e6), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
    ("general", _loads(N_force=-400e3, load_My_local=30e6, load_Mz_local=10e6, load_Qz_local=50e3), {"SP554_R_CRITICAL_TEMP_ATOMIC", "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE", "SP554_R_B1_INVERSE_OUT_OF_RANGE"}),
])
def test_signed_load_supported_routes_finish_with_no_pending_or_failures(name, loads, allowed_nodes):
    status, session, _ = run(name, loads, maxsteps=180)
    assert status in {"RESULT", "MECHANICAL_RESULT", "THERMAL_ENTRY"}
    if status == "THERMAL_ENTRY":
        assert session.current_node_id == "SP554_I_EXPOSURE"
    else:
        assert session.current_node_id in allowed_nodes
    assert session.pending_node_ids == []
    assert session.branch_failures == []


@pytest.mark.parametrize("name,loads,deferred_id", [
    ("Qy", _loads(N_force=400e3, load_Qy_local=50e3), "shear_Qy"),
    ("T", _loads(N_force=400e3, T_torsion=5e6), "torsion_T"),
])
def test_unsupported_signed_load_branches_fail_closed_explicitly(name, loads, deferred_id):
    status, session, _ = run(name, loads, maxsteps=180)
    assert status == "RESULT"
    assert session.current_node_id == "SP554_R_UI16_DEFERRED_BRANCHES"
    assert session.pending_node_ids == []
    assert session.branch_failures == []
    plan = session.plain_values()["verification_plan"]
    assert deferred_id in plan["deferred_branch_ids"]


def test_compression_has_in_domain_independent_temperature_inversion_case():
    old = {k: Q_DEFAULTS[k] for k in ("L_member", "member_length", "L_x", "L_y")}
    try:
        for k in old:
            Q_DEFAULTS[k] = 4500.0
        status, session, _ = run("compression_in_domain", _loads(N_force=-600e3), maxsteps=180)
    finally:
        Q_DEFAULTS.update(old)
    assert status == "THERMAL_ENTRY"
    assert session.current_node_id == "SP554_I_EXPOSURE"
    assert session.pending_node_ids == []
    assert session.branch_failures == []
    vals = session.plain_values()
    assert vals["gamma_T_required"] == pytest.approx(0.66946298441076)
    assert vals["gamma_E_required"] == pytest.approx(0.45463056846286376)
    # Independent FIRE-D2 inversions are both retained; the governing temperature
    # is the lower of the strength- and modulus-curve inverse temperatures.
    assert vals["fire_d2_critical_temperature_c"] == pytest.approx(450.44751299103336)


def test_area_only_hole_reduces_area_but_keeps_gross_inertia_and_moduli():
    session = app_session(_loads(N_force=400e3), holes=True)[1]
    vals = session.plain_values()
    assert vals["A_net"] == pytest.approx(vals["A_gross"] - 20.0 * vals["t_w"])
    assert vals["I_xn"] == pytest.approx(vals["J_x"])
    assert vals["I_yn"] == pytest.approx(vals["J_y"])
    assert vals["W_xn_min"] == pytest.approx(min(vals["W_el_x_pos"], vals["W_el_x_neg"]))
    assert vals["W_yn_min"] == pytest.approx(min(vals["W_el_y_pos"], vals["W_el_y_neg"]))


def test_manual_net_properties_are_effective_downstream_not_decorative():
    # Build the ordinary 20K1 path until the weakening editor.
    from pathlib import Path
    from standard_core.fire_ui1_http import FireUI1Application
    root = Path(__file__).resolve().parents[1]
    app = FireUI1Application.from_package_root(root)
    s = app.service.get_session(app.service.create_session()["session_id"])
    for a in [True, False, "hot_rolled_section", "catalog_section"]:
        s.submit(a)
    row = next(x for x in app.profile_catalog.list_profiles(35) if x["designation"] == "20К1")
    s.submit({"section_catalog_standard":"ГОСТ Р 57837-2017","section_designation":"20К1","section_family":"i_section",
              "sp16_i_symmetry_class":"double_symmetric","section_catalog_family_id":35,"section_catalog_source_row_id":row["source_row_id"]})
    catalog = app.material_strength_catalog()
    product = next(p for p in catalog["products"] if p["value"] == "parallel_flange_i")
    grade = next(g for g in product["grades"] if g["steel_grade"] == "С255Б")
    interval = next(r for r in grade["intervals"] if r["thickness_interval"]["max_mm"] == 10)
    s.submit({"steel_product_form":"parallel_flange_i","steel_grade":"С255Б",
              "steel_strength_interval_key":interval["interval_key"],"governing_product_thickness_mm":10.0})
    s.submit({"schema":"section_weakening_model_v0.49","holes_present":True,"model":"round_bolt_hole_universal_v1",
              "hole_diameter_mm":20.0,"hole_pitch_mm":80.0})
    s.submit("manual_net_properties")
    manual = {"manual_I_xn":30_000_000.0,"manual_I_yn":10_000_000.0,
              "manual_W_xn_min":200_000.0,"manual_W_yn_min":100_000.0,
              "manual_W_pl_x_eff":220_000.0,"manual_W_pl_y_eff":110_000.0}
    s.submit(manual)
    vals = s.plain_values()
    assert vals["A_net"] == pytest.approx(5139.0)
    assert vals["I_xn"] == pytest.approx(manual["manual_I_xn"])
    assert vals["I_yn"] == pytest.approx(manual["manual_I_yn"])
    assert vals["W_xn_min"] == pytest.approx(manual["manual_W_xn_min"])
    assert vals["W_yn_min"] == pytest.approx(manual["manual_W_yn_min"])
    assert vals["W_pl_x_eff"] == pytest.approx(manual["manual_W_pl_x_eff"])
    assert vals["W_pl_y_eff"] == pytest.approx(manual["manual_W_pl_y_eff"])
    assert vals["W_pl_min_eff"] == pytest.approx(110_000.0)


def test_universal_area_only_weakening_accepts_catalog_tee():
    from pathlib import Path
    from standard_core.fire_ui1_http import FireUI1Application
    root = Path(__file__).resolve().parents[1]
    app = FireUI1Application.from_package_root(root)
    s = app.service.get_session(app.service.create_session()["session_id"])
    for a in [True, False, "hot_rolled_section", "catalog_section"]:
        s.submit(a)
    row = next(x for x in app.profile_catalog.list_profiles(14) if x["designation"] == "10КТ1")
    s.submit({"section_catalog_standard":"Тавры колонные","section_designation":"10КТ1","section_family":"tee",
              "sp16_i_symmetry_class":"not_i","section_catalog_family_id":14,"section_catalog_source_row_id":row["source_row_id"]})
    catalog = app.material_strength_catalog()
    product = next(p for p in catalog["products"] if p["value"] == "shaped_rolled")
    grade = next(g for g in product["grades"] if g["steel_grade"] == "С255")
    interval = next(r for r in grade["intervals"] if r["thickness_interval"]["max_mm"] == 10)
    s.submit({"steel_product_form":"shaped_rolled","steel_grade":"С255",
              "steel_strength_interval_key":interval["interval_key"],"governing_product_thickness_mm":10.0})
    s.submit({"schema":"section_weakening_model_v0.49","holes_present":True,"model":"round_bolt_hole_universal_v1",
              "hole_diameter_mm":20.0,"hole_pitch_mm":80.0})
    s.submit("area_only_keep_gross")
    vals = s.plain_values()
    assert vals["A_gross"] == pytest.approx(2619.0)
    assert vals["A_net"] == pytest.approx(2489.0)
    assert vals["I_xn"] == pytest.approx(vals["J_x"])
    assert vals["I_yn"] == pytest.approx(vals["J_y"])
    assert s.current_node_id == "SP554_D_GOST27751_GAMMA_CT"
