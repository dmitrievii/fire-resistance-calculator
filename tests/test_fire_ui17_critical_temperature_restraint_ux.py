from __future__ import annotations

from pathlib import Path
import pytest

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui17_workflow import build_fire_ui17_registry
from standard_core.profile_catalog import InterimProfileCatalog

ROOT=Path(__file__).resolve().parents[1]


def _select(node_id: str, values: dict):
    reg=build_fire_ui17_registry(InterimProfileCatalog())
    fn=reg.get(node_id)
    assert fn is not None
    return fn(values,{"id":node_id})


def test_gamma_t_over_one_is_ambient_failure_not_extrapolation_and_overrides_modulus_branch():
    out=_select("SP554_FIRE_UI17_C_TCR_COMPRESSION",{
        "steel_strength_group":"ordinary",
        "gamma_T_required":2.1747363885430664,
        "gamma_E_required":0.5,
    })
    assert out["fire_d2_critical_temperature_status"] == "AMBIENT_CAPACITY_EXCEEDED"
    assert out["fire_d2_critical_temperature_c"] == pytest.approx(20.0)
    assert out["fire_d2_critical_temperature_controlling_kind"] == "gamma_T"
    assert out["fire_d2_strength_inversion_result"]["temperature_relation"] == "<="
    assert out["fire_d2_modulus_inversion_result"]["temperature_c"] > 20.0


def test_gamma_t_exact_and_gamma_e_below_published_minimum_uses_exact_strength_temperature():
    out=_select("SP554_FIRE_UI17_C_TCR_COMPRESSION",{
        "steel_strength_group":"ordinary",
        "gamma_T_required":0.946011,
        "gamma_E_required":0.3793841,
    })
    assert out["fire_d2_critical_temperature_status"] == "COMPLETE"
    assert out["fire_d2_critical_temperature_controlling_kind"] == "gamma_T"
    assert out["fire_d2_strength_inversion_result"]["status"] == "EXACT_WITHIN_PUBLISHED_CURVE"
    assert out["fire_d2_modulus_inversion_result"]["status"] == "ABOVE_PUBLISHED_TEMPERATURE_RANGE"
    assert out["fire_d2_modulus_inversion_result"]["temperature_lower_bound_c"] == pytest.approx(700.0)
    assert out["fire_d2_critical_temperature_c"] == pytest.approx(out["fire_d2_strength_inversion_result"]["temperature_c"])


def test_both_branches_below_published_minimum_return_relational_lower_bound_without_extrapolation():
    out=_select("SP554_FIRE_UI17_C_TCR_COMPRESSION",{
        "steel_strength_group":"ordinary",
        "gamma_T_required":0.1,
        "gamma_E_required":0.3,
    })
    assert out["fire_d2_critical_temperature_status"] == "INCOMPLETE_FAIL_CLOSED"
    assert "fire_d2_critical_temperature_c" not in out
    assert out["fire_d2_critical_temperature_lower_bound_c"] == pytest.approx(700.0)
    assert out["fire_d2_critical_temperature_controlling_kind"] == "bounded"


def test_ui17_dag_removes_legacy_single_domain_gate_from_guided_production():
    app=FireUI1Application.from_package_root(ROOT)
    excluded=set(app.model.presentation_policy["guided_excluded_nodes"])
    assert "SP554_A_B1_INVERSE_DOMAIN" in excluded
    assert "SP554_FIRE_D2_L_B1_STRENGTH_TCR" in excluded
    assert "SP554_FIRE_D2_L_B1_MODULUS_TCR" in excluded
    assert app.model.ui_policy_for_node("SP16_D_MU_SCHEME")["component"] == "table30_scheme_selector"
    assert app.model.ui_policy_for_node("SP16_D_CURVE")["component"] == "table7_curve_selector"


def test_table30_and_table7_contract_labels_are_engineering_readable():
    app=FireUI1Application.from_package_root(ROOT)
    mu=app.model.nodes["SP16_D_MU_SCHEME"]
    labels={o["value"]:o["label"] for o in mu["options"]}
    assert labels["S1"] == "Шарнир — шарнир"
    assert "Защемление" in labels["S2"]
    assert "μ = 0,725" in next(o["description"] for o in mu["options"] if o["value"]=="S7")
    curves=app.model.nodes["SP16_D_CURVE"]
    desc={o["value"]:o["description"] for o in curves["options"]}
    assert "α = 0,03" in desc["a"] and "β = 0,06" in desc["a"]
    assert "α = 0,04" in desc["c"] and "β = 0,14" in desc["c"]


def test_frontend_bundle_contains_new_normative_selectors():
    js=(ROOT/"fire_ui1_web/dist/app.js").read_text(encoding="utf-8")
    assert "renderTable30SchemeSelector" in js
    assert "renderTable7CurveSelector" in js
    assert "Шарнир — шарнир" in js
    assert "схематическая перерисовка" in js


def test_ordinary_compression_context_no_longer_exposes_raw_restraint_object():
    app=FireUI1Application.from_package_root(ROOT)
    node=app.model.nodes["SP554_I_COMPRESSION_CONTEXT"]
    produced=[b["quantity_id"] for b in node["produces"]]
    assert produced == ["member_length"]
    assert app.model.nodes["SP16_D_MU_ROUTE"]["consumes"] == []
