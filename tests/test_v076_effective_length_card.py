from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireDAGModel, FireUIError
from standard_core.profile_catalog import InterimProfileCatalog
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import (
    DEFINITION_QID,
    GRAPH_SUFFIX,
    INPUT_NODE_ID,
    STATE_NODE_ID,
    TABLE30_OPTIONS,
    V075_EFFECTIVE_LENGTH_INPUT_NODES,
    build_model,
)
from standard_core.sp16_mech7_v076_runtime import effective_length_state

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    return build_model(build_v075_model(base))


def _first_profile(catalog: InterimProfileCatalog):
    family = catalog.list_families()[0]
    profile = catalog.list_profiles(int(family["family_id"]))[0]
    fid = int(family["family_id"])
    designation = str(profile["designation"])
    row = int(profile["source_row_id"])
    bundle = catalog.resolve(fid, designation, source_row_id=row)
    return fid, designation, row, bundle


def _catalog_values(catalog: InterimProfileCatalog) -> dict:
    fid, designation, row, bundle = _first_profile(catalog)
    raw = bundle["catalog_properties_interim"]
    return {
        "section_catalog_family_id": fid,
        "section_designation": designation,
        "section_catalog_source_row_id": row,
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "family_id": fid,
            "designation": designation,
            "source_row_id": row,
        },
        "A_gross": float(raw["A_mm2"]),
        "J_x": float(raw["Ix_mm4"]),
        "J_y": float(raw["Iy_mm4"]),
        "Ry_formula": 240.0,
        "E_norm": 206000.0,
    }


def test_v076_replaces_sequential_v075_questions_by_one_effective_length_card():
    model = _active_model()
    assert str(model.graph["graph_id"]).endswith(GRAPH_SUFFIX)

    edges = model.graph["edges"]
    assert any(
        e["id"] == "V076_E_BRITTLE_TO_EFFECTIVE_LENGTH" and e["to_node_id"] == INPUT_NODE_ID
        for e in edges
    )
    assert any(
        e["id"] == "V076_E_EFFECTIVE_LENGTH_TO_STATE" and e["to_node_id"] == STATE_NODE_ID
        for e in edges
    )
    assert not any(
        e.get("from_node_id") in V075_EFFECTIVE_LENGTH_INPUT_NODES
        or e.get("to_node_id") in V075_EFFECTIVE_LENGTH_INPUT_NODES
        for e in edges
    )

    node = model.nodes[INPUT_NODE_ID]
    assert node["produces"] == [{"quantity_id": DEFINITION_QID, "required": True, "binding_role": "output"}]
    card = model.node_card(INPUT_NODE_ID)
    assert card["submit_shape"] == "scalar"
    assert card["presentation"]["component"] == "effective_length_zy_editor"


def test_v076_table30_options_are_human_readable_and_use_one_canonical_id_family():
    assert [row["value"] for row in TABLE30_OPTIONS] == [f"S{i}" for i in range(1, 9)]
    assert TABLE30_OPTIONS[0]["label"] == "Шарнирное закрепление обоих концов"
    assert "μ = 1,00" in TABLE30_OPTIONS[0]["description"]
    assert "защемлён" in TABLE30_OPTIONS[1]["label"]
    assert "Консоль" in TABLE30_OPTIONS[3]["label"]
    assert all(not str(row["label"]).startswith("Схема ") for row in TABLE30_OPTIONS)


def test_v076_state_no_longer_requires_profile_ref_and_accepts_y_table30_scheme():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    assert "profile_ref" not in values
    values[DEFINITION_QID] = {
        "member_length_mm": 3000.0,
        "z": {"method": "table30", "scheme_id": "S3"},
        "y": {"method": "table30", "scheme_id": "S2"},
    }

    out = effective_length_state(values, catalog)
    assert out["sp16_mu_z"] == pytest.approx(0.5)
    assert out["sp16_mu_y"] == pytest.approx(0.7)
    assert out["sp16_l_eff_z"] == pytest.approx(1500.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2100.0)
    contract = out["sp16_v075_axis_contract"]
    assert contract["schema"] == "sp16_v076_effective_length_zy_v1"
    assert contract["profile_mapping"]["profile_ref_required"] is False
    assert contract["principal_strong_axis"] == "z"
    assert contract["principal_weak_axis"] == "y"


def test_v076_direct_effective_lengths_work_without_member_length_or_profile_ref():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    values[DEFINITION_QID] = {
        "z": {
            "method": "verified_analysis",
            "effective_length_mm": 1800.0,
            "basis": "verified structural model — z plane",
        },
        "y": {
            "method": "verified_analysis",
            "effective_length_mm": 2300.0,
            "basis": "verified structural model — y plane",
        },
    }

    out = effective_length_state(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(1800.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2300.0)
    assert "sp16_mu_z" not in out
    assert "sp16_mu_y" not in out


def test_v076_mixed_route_uses_geometric_length_only_for_table30_axis():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    values[DEFINITION_QID] = {
        "member_length_mm": 3200.0,
        "z": {"method": "table30", "scheme_id": "S1"},
        "y": {
            "method": "verified_analysis",
            "effective_length_mm": 2600.0,
            "basis": "separate verified weak-axis model",
        },
    }
    out = effective_length_state(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(3200.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2600.0)


def test_v076_rejects_legacy_scheme_ids_at_the_active_ui_runtime_boundary():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    values[DEFINITION_QID] = {
        "member_length_mm": 3000.0,
        "z": {"method": "table30", "scheme_id": "scheme_1"},
        "y": {"method": "table30", "scheme_id": "S1"},
    }
    with pytest.raises(FireUIError, match="must be one of"):
        effective_length_state(values, catalog)


def test_v076_state_contract_does_not_consume_synthetic_profile_ref_or_old_route_quantities():
    model = _active_model()
    consumes = {row["quantity_id"] for row in model.nodes[STATE_NODE_ID]["consumes"]}
    assert DEFINITION_QID in consumes
    assert "profile_ref" not in consumes
    for qid in (
        "sp16_member_length_mm",
        "sp16_effective_length_route_z", "sp16_table30_scheme_z",
        "sp16_effective_length_route_y", "sp16_table30_scheme_y",
    ):
        assert qid not in consumes
