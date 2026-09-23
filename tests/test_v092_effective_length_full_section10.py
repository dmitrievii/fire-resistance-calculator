from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.effective_length_workflows import effective_length_guided_workflow
from standard_core.fire_ui0 import FireDAGModel, FireUIError
from standard_core.profile_catalog import InterimProfileCatalog
from standard_core.sp16_mech7_v075_graph_overlay import build_model as build_v075_model
from standard_core.sp16_mech7_v076_graph_overlay import (
    DEFINITION_QID,
    INPUT_NODE_ID,
    STATE_NODE_ID,
    build_model as build_v076_model,
)
from standard_core.sp16_mech7_v092_effective_length import (
    EVIDENCE_QID,
    GRAPH_SUFFIX,
    SECTION10_METHOD,
    SECTION10_ROUTE_KINDS,
    build_model,
    effective_length_state_v092,
)

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _active_model() -> FireDAGModel:
    base = FireDAGModel.load(DAG, presentation_policy_path=POLICY)
    return build_model(build_v076_model(build_v075_model(base)))


def _catalog_values(catalog: InterimProfileCatalog) -> dict:
    family = catalog.list_families()[0]
    profile = catalog.list_profiles(int(family["family_id"]))[0]
    fid = int(family["family_id"])
    designation = str(profile["designation"])
    row = int(profile["source_row_id"])
    bundle = catalog.resolve(fid, designation, source_row_id=row)
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


def _stage_n7_length(route: dict) -> float:
    out = effective_length_guided_workflow(
        {
            "case_id": "expected",
            "standard": "СП 16.13330.2017",
            "action": "effective_length_guided",
            "effective_length_route": route,
            "radius": {"mode": "explicit", "value_mm": 1.0},
            "limiting_slenderness": {"mode": "none", "group_4_applies": False},
        }
    )
    assert out["status"] == "COMPLETE"
    return float(out["effective_length"]["effective_length_mm"])


def test_v092_graph_adds_full_section10_options_and_typed_evidence():
    model = _active_model()
    assert GRAPH_SUFFIX in str(model.graph["graph_id"])
    assert EVIDENCE_QID in model.quantities
    assert EVIDENCE_QID in {
        row["quantity_id"] for row in model.nodes[STATE_NODE_ID]["produces"]
    }
    card = model.node_card(INPUT_NODE_ID)
    options = card["presentation"]["section10_route_options"]
    assert {row["value"] for row in options} == {row[0] for row in SECTION10_ROUTE_KINDS}
    assert card["presentation"]["component"] == "effective_length_zy_editor"


def test_v092_keeps_v076_table30_fast_route_unchanged():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    values[DEFINITION_QID] = {
        "member_length_mm": 3000.0,
        "z": {"method": "table30", "scheme_id": "S3"},
        "y": {"method": "table30", "scheme_id": "S2"},
    }
    out = effective_length_state_v092(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(1500.0)
    assert out["sp16_l_eff_y"] == pytest.approx(2100.0)
    assert out["sp16_mu_z"] == pytest.approx(0.5)
    assert out["sp16_mu_y"] == pytest.approx(0.7)


def test_v092_eq136_route_is_executed_by_stage_n7_and_reported_on_z_axis():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    route = {
        "kind": "eq136_truss_chord_in_plane",
        "segment_length_mm": 3000.0,
        "adjacent_force_ratio_alpha": 0.5,
    }
    values[DEFINITION_QID] = {
        "z": {"method": SECTION10_METHOD, "route": route},
        "y": {
            "method": "verified_analysis",
            "effective_length_mm": 2400.0,
            "basis": "qualified weak-axis model",
        },
    }
    out = effective_length_state_v092(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(_stage_n7_length(route))
    assert out["sp16_l_eff_y"] == pytest.approx(2400.0)
    evidence = out[EVIDENCE_QID]
    assert evidence["schema"] == "sp16_v092_effective_length_zy_trace_v1"
    assert evidence["z"]["route"]["route_kind"] == "eq136_truss_chord_in_plane"
    assert evidence["z"]["route"]["stage_n7_workflow"]["status"] == "COMPLETE"
    assert evidence["axis_convention"] == {
        "z": "strong principal axis",
        "y": "weak principal axis",
    }
    contract = out["sp16_v075_axis_contract"]
    assert contract["legacy_principal_x_semantics_active"] is False
    assert contract["principal_x_transport_alias_used"] is False


def test_v092_table31_frame_route_uses_existing_stage_n7_producer():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    route = {
        "kind": "table31_frame_column",
        "same_load_combination_confirmed": True,
        "mu_method": "eq145_nonsway",
        "p_parameter": 1.0,
        "n_parameter": 1.0,
        "column_length_mm": 3600.0,
        "apply_eq146_nonuniform_loading": False,
        "apply_eq147_deformation_reduction": False,
    }
    values[DEFINITION_QID] = {
        "z": {"method": SECTION10_METHOD, "route": route},
        "y": {"method": "table30", "scheme_id": "S1"},
        "member_length_mm": 3000.0,
    }
    out = effective_length_state_v092(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(_stage_n7_length(route))
    assert out[EVIDENCE_QID]["z"]["route"]["route_kind"] == "table31_frame_column"
    assert out[EVIDENCE_QID]["z"]["route"]["stage_n7_workflow"]["effective_length"]["mu"] > 0.0


def test_v092_external_route_fails_closed_without_provenance():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    values[DEFINITION_QID] = {
        "z": {
            "method": SECTION10_METHOD,
            "route": {"kind": "stepped_column_10_3_7_external"},
        },
        "y": {
            "method": "verified_analysis",
            "effective_length_mm": 2000.0,
            "basis": "qualified weak-axis model",
        },
    }
    with pytest.raises(FireUIError, match="fail-closed"):
        effective_length_state_v092(values, catalog)


def test_v092_external_route_accepts_positive_length_with_explicit_basis():
    catalog = InterimProfileCatalog()
    values = _catalog_values(catalog)
    route = {
        "kind": "stepped_column_10_3_7_external",
        "external_effective_length": {
            "value_mm": 2750.0,
            "basis": "Annex И / qualified frame-analysis record EL-17",
        },
    }
    values[DEFINITION_QID] = {
        "z": {"method": SECTION10_METHOD, "route": route},
        "y": {
            "method": "verified_analysis",
            "effective_length_mm": 2300.0,
            "basis": "qualified weak-axis model",
        },
    }
    out = effective_length_state_v092(values, catalog)
    assert out["sp16_l_eff_z"] == pytest.approx(2750.0)
    trace = out[EVIDENCE_QID]["z"]["route"]["stage_n7_workflow"]
    assert trace["effective_length"]["status"] == "EXTERNAL_EFFECTIVE_LENGTH_USED"
    assert trace["effective_length"]["source"] == route["external_effective_length"]["basis"]


def test_v092_route_census_contains_table31_special_case_support():
    kinds = {row[0] for row in SECTION10_ROUTE_KINDS}
    assert "table31_frame_column" in kinds
    route = {
        "kind": "table31_frame_column",
        "same_load_combination_confirmed": True,
        "mu_method": "table31_special_case",
        "special_case_id": "nonsway_p0",
        "special_case_parameter": 1.0,
        "column_length_mm": 3000.0,
    }
    assert _stage_n7_length(route) > 0.0
