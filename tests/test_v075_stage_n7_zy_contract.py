from __future__ import annotations

import math
from pathlib import Path

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel
from standard_core.profile_catalog import InterimProfileCatalog
from standard_core.sp16_mech7_v075_zy_runtime import (
    BINDER_NODE_ID,
    GRAPH_SUFFIX,
    bind_primary_ambient_evidence_zy,
    build_model,
    effective_length_state,
    install_registry_remediation,
    transform_graph,
)


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _first_profile_ref(catalog: InterimProfileCatalog) -> dict:
    family = catalog.list_families()[0]
    profiles = catalog.list_profiles(int(family["family_id"]))
    profile = profiles[0]
    return {
        "family_id": int(family["family_id"]),
        "designation": str(profile["designation"]),
        "source_row_id": int(profile["source_row_id"]),
    }


def test_v075_active_graph_inserts_missing_length_and_restraint_cards_before_mech7_binder():
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    graph = transform_graph(base.graph)
    assert str(graph["graph_id"]).endswith(GRAPH_SUFFIX)

    edges = {e["id"]: e for e in graph["edges"]}
    assert "MECH7_E_BRITTLE_TO_COMPRESSION" not in edges
    assert edges["V075_E_BRITTLE_TO_LENGTH"]["to_node_id"] == "SP16_I_V075_MEMBER_LENGTH"
    assert edges["V075_E_LENGTH_TO_ROUTE_Z"]["to_node_id"] == "SP16_D_V075_EFFECTIVE_ROUTE_Z"
    assert edges["V075_E_STATE_TO_COMPRESSION_CLASS"]["to_node_id"] == "SP16_I_MECH7_COMPRESSION_SLENDERNESS"

    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes["SP16_I_V075_MEMBER_LENGTH"]["produces"][0]["quantity_id"] == "sp16_member_length_mm"
    assert nodes["SP16_D_V075_TABLE30_Z"]["decision_quantity_id"] == "sp16_table30_scheme_z"
    assert nodes["SP16_D_V075_TABLE30_Y"]["decision_quantity_id"] == "sp16_table30_scheme_y"


def test_v075_binder_contract_uses_z_y_and_no_principal_x_alias():
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    model = build_model(base)
    binder = model.nodes[BINDER_NODE_ID]
    qids = {row["quantity_id"] for row in binder["consumes"]}

    assert "phi_z_sp16" in qids
    assert "phi_y_sp16" in qids
    assert "sp16_lambda_z_geom" in qids
    assert "sp16_lambda_y_geom" in qids
    assert "lambda_bar_z" in qids
    assert "lambda_bar_y" in qids

    assert "phi_x_sp16" not in qids
    assert "sp16_lambda_x_geom" not in qids
    assert "lambda_bar_x" not in qids


def test_v075_table30_state_is_canonical_zy_and_lambda_bar_uses_design_Ry():
    catalog = InterimProfileCatalog()
    profile_ref = _first_profile_ref(catalog)
    bundle = catalog.resolve(
        profile_ref["family_id"],
        profile_ref["designation"],
        source_row_id=profile_ref["source_row_id"],
    )
    raw = bundle["catalog_properties_interim"]
    derived = bundle["derived_properties"]

    values = {
        "profile_ref": profile_ref,
        "sp16_member_length_mm": 3000.0,
        "sp16_effective_length_route_z": "table30",
        "sp16_table30_scheme_z": "scheme_3",  # mu=0.5
        "sp16_effective_length_route_y": "table30",
        "sp16_table30_scheme_y": "scheme_2",  # mu=0.7
        "Ry_formula": 240.0,
        "fy_norm": 355.0,  # deliberately different: must NOT govern lambda_bar
        "E_norm": 206000.0,
    }
    out = effective_length_state(values, catalog)

    assert out["sp16_mu_z"] == pytest.approx(0.5)
    assert out["sp16_mu_y"] == pytest.approx(0.7)
    assert out["sp16_l_eff_z"] == pytest.approx(1500.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2100.0)

    if float(raw["Ix_mm4"]) >= float(raw["Iy_mm4"]):
        iz = float(derived["radius_x_mm"])
        iy = float(derived["radius_y_mm"])
    else:
        iz = float(derived["radius_y_mm"])
        iy = float(derived["radius_x_mm"])

    expected_lz = 1500.0 / iz
    expected_ly = 2100.0 / iy
    assert out["sp16_lambda_z_geom"] == pytest.approx(expected_lz)
    assert out["sp16_lambda_y_geom"] == pytest.approx(expected_ly)
    assert out["lambda_bar_z"] == pytest.approx(expected_lz * math.sqrt(240.0 / 206000.0))
    assert out["lambda_bar_y"] == pytest.approx(expected_ly * math.sqrt(240.0 / 206000.0))
    axis = out["sp16_v075_axis_contract"]
    assert axis["legacy_principal_x_semantics_active"] is False
    assert axis["principal_x_transport_alias_used"] is False
    assert axis["principal_strong_axis"] == "z"
    assert axis["principal_weak_axis"] == "y"


def test_v075_verified_effective_length_requires_basis_and_does_not_invent_mu():
    catalog = InterimProfileCatalog()
    profile_ref = _first_profile_ref(catalog)
    values = {
        "profile_ref": profile_ref,
        "sp16_member_length_mm": 3000.0,
        "sp16_effective_length_route_z": "verified_analysis",
        "sp16_verified_l_eff_z_mm": 2450.0,
        "sp16_verified_l_eff_z_basis": "Расчетная модель по СП16, п.10.3.9",
        "sp16_effective_length_route_y": "verified_analysis",
        "sp16_verified_l_eff_y_mm": 2800.0,
        "sp16_verified_l_eff_y_basis": "Расчетная модель по СП16, п.10.3.11",
        "Ry_formula": 240.0,
        "E_norm": 206000.0,
    }
    out = effective_length_state(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(2450.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2800.0)
    assert "sp16_mu_z" not in out
    assert "sp16_mu_y" not in out

    bad = dict(values)
    bad["sp16_verified_l_eff_z_basis"] = ""
    with pytest.raises(Exception, match="basis"):
        effective_length_state(bad, catalog)


def test_v075_registry_does_not_feed_principal_x_aliases_into_binder():
    seen = []

    def legacy_executor(values, node):
        seen.append(dict(values))
        return {"sp16_mech7_primary_evidence": {"evidence": {}}, "sp16_mech7_primary_binding_complete": True}

    registry = ExecutionRegistry({BINDER_NODE_ID: legacy_executor})
    catalog = InterimProfileCatalog()
    install_registry_remediation(registry, catalog)
    executor = registry.executors[BINDER_NODE_ID]

    # The canonical executor replaces the legacy one.  It must never call it or
    # create principal-axis x compatibility quantities.
    assert executor is not legacy_executor
    assert getattr(executor, "_sp16_v075_zy_remediated", False) is True
    assert seen == []


def test_v075_canonical_binder_reads_z_y_for_central_compression():
    values = {
        "sp16_applicability_census": {
            "active_checks": [
                {"id": "member_compression_stability"},
                {"id": "effective_length_slenderness"},
            ],
            "context_driven_checks": [],
        },
        "ambient_N_force": -100000.0,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "A_gross": 2000.0,
        "Ry_formula": 240.0,
        "gamma_c_compression": 1.0,
        "phi_z_sp16": 0.8,
        "phi_y_sp16": 0.7,
        "sp16_lambda_z_geom": 50.0,
        "sp16_lambda_y_geom": 75.0,
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
    }
    out = bind_primary_ambient_evidence_zy(values)
    evidence = out["sp16_mech7_primary_evidence"]["evidence"]
    assert evidence["member_compression_stability"]["status"] in {"PASS", "FAIL"}
    assert evidence["effective_length_slenderness"]["status"] in {"PASS", "FAIL"}
    assert "phi_x_sp16" not in str(out)
    assert "lambda_x" not in str(out)


def test_v075_ui_contract_hides_legacy_n7_axis_cards_and_exposes_new_zy_cards():
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    model = build_model(base)
    contract = model.build_ui_contract()
    cards = {c["node_id"]: c for c in contract["node_cards"]}

    assert cards["SP16_I_V075_MEMBER_LENGTH"]["hidden_in_primary_ui"] is False
    assert cards["SP16_D_V075_TABLE30_Z"]["hidden_in_primary_ui"] is False
    assert cards["SP16_D_V075_TABLE30_Y"]["hidden_in_primary_ui"] is False
    for legacy in ("SP16_D_MU_ROUTE_X", "SP16_D_MU_SCHEME_X", "SP16_D_MU_ROUTE_Y", "SP16_D_MU_SCHEME_Y"):
        if legacy in cards:
            assert cards[legacy]["hidden_in_primary_ui"] is True
