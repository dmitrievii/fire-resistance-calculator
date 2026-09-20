from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from standard_core.section_model import (
    CURRENT_SP16_SOURCE_SHA256,
    HistoricalNormCADProfileCatalog,
    SectionPropertyModel,
)

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "validation/stage_n2/normcad_capture/normcad_profile_catalog_historical.json"
AUDIT = ROOT / "validation/stage_n2/normcad_capture/normcad_profile_catalog_audit.json"
OBS = ROOT / "validation/stage_n2/evidence/normcad_runtime_observation_15K4.json"
SCOPE = ROOT / "validation/stage_n2/evidence/n2_source_scope.json"
DISCREP = ROOT / "validation/stage_n2/evidence/n2_discrepancy_register.json"


def test_n2_rectangle_geometry_exact_and_radius_identity():
    p = SectionPropertyModel.rectangle(100.0, 200.0)
    assert p.area_mm2 == 20000.0
    assert p.ix_mm4 == pytest.approx(100.0 * 200.0**3 / 12.0)
    assert p.iy_mm4 == pytest.approx(200.0 * 100.0**3 / 12.0)
    assert p.wx_pos_mm3 == pytest.approx(100.0 * 200.0**2 / 6.0)
    assert p.wy_pos_mm3 == pytest.approx(200.0 * 100.0**2 / 6.0)
    assert p.sx_mm3 == pytest.approx(100.0 * 200.0**2 / 8.0)
    assert p.radius_x_mm == pytest.approx(math.sqrt(p.ix_mm4 / p.area_mm2))
    assert p.radius_y_mm == pytest.approx(math.sqrt(p.iy_mm4 / p.area_mm2))
    assert p.provenance == "GEOMETRY_DERIVED"


def test_n2_rhs_sharp_corner_is_outer_minus_inner_exact():
    p = SectionPropertyModel.rectangular_hollow_sharp(120.0, 200.0, 8.0)
    bi = 120.0 - 16.0
    hi = 200.0 - 16.0
    assert p.area_mm2 == pytest.approx(120.0 * 200.0 - bi * hi)
    assert p.ix_mm4 == pytest.approx((120.0 * 200.0**3 - bi * hi**3) / 12.0)
    assert p.iy_mm4 == pytest.approx((200.0 * 120.0**3 - hi * bi**3) / 12.0)
    assert p.geometry_model == "rhs_shs_sharp_corner_exact"


def test_n2_symmetric_i_sharp_corner_is_explicitly_not_rolled_catalog_geometry():
    p = SectionPropertyModel.doubly_symmetric_i_sharp(160.0, 152.0, 10.0, 15.0)
    # Exact sharp-plate idealization excludes the rolled fillets present in the
    # historical 15K4 catalog row.  The difference is deliberate and provenance-visible.
    assert p.area_mm2 == 5860.0
    assert p.ix_mm4 == pytest.approx(25_884_833.333333332)
    assert p.iy_mm4 == pytest.approx(8_790_353.333333334)
    assert p.wx_pos_mm3 == pytest.approx(323_560.4166666666)
    assert p.wy_pos_mm3 == pytest.approx(115_662.54385964913)
    assert p.sx_mm3 == pytest.approx(186_425.0)
    assert p.sy_mm3 == pytest.approx(88_265.0)
    assert p.mass_kg_m_at_7850 == pytest.approx(46.001)
    assert p.geometry_model == "i_doubly_symmetric_sharp_corner_exact"


def test_n2_circle_and_chs_exact_geometry_symmetry():
    solid = SectionPropertyModel.solid_circle(100.0)
    assert solid.area_mm2 == pytest.approx(math.pi * 100.0**2 / 4.0)
    assert solid.ix_mm4 == pytest.approx(math.pi * 100.0**4 / 64.0)
    assert solid.iy_mm4 == solid.ix_mm4
    assert solid.wx_pos_mm3 == pytest.approx(math.pi * 100.0**3 / 32.0)

    chs = SectionPropertyModel.circular_hollow(100.0, 5.0)
    assert chs.area_mm2 == pytest.approx(math.pi * (100.0**2 - 90.0**2) / 4.0)
    assert chs.ix_mm4 == pytest.approx(math.pi * (100.0**4 - 90.0**4) / 64.0)
    assert chs.iy_mm4 == chs.ix_mm4


def test_n2_invalid_geometry_is_fail_closed():
    with pytest.raises(ValueError):
        SectionPropertyModel.rectangular_hollow_sharp(100.0, 100.0, 50.0)
    with pytest.raises(ValueError):
        SectionPropertyModel.doubly_symmetric_i_sharp(100.0, 50.0, 10.0, 50.0)
    with pytest.raises(ValueError):
        SectionPropertyModel.circular_hollow(100.0, 50.0)
    with pytest.raises(TypeError):
        SectionPropertyModel.rectangle(True, 100.0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "section_type,k",
    [
        ("i_doubly_symmetric", 1.29),
        ("i_singly_symmetric", 1.25),
        ("tee", 1.20),
        ("channel", 1.12),
        ("p_section", 1.12),
    ],
)
def test_n2_current_sp16_annex_d_k_mapping(section_type, k):
    assert SectionPropertyModel.annex_d_k(section_type) == k


def test_n2_current_sp16_annex_d_it_for_15k4_nominal_dimensions():
    result = SectionPropertyModel.annex_d_it_for_doubly_symmetric_i_mm4(160.0, 152.0, 10.0, 15.0)
    assert result["k"] == 1.29
    assert result["sum_b_i_t_i3_mm4"] == pytest.approx(1_155_999.9999999998)
    assert result["I_t_sp16_annex_d_mm4"] == pytest.approx(497_080.0)
    assert result["source_sha256"] == CURRENT_SP16_SOURCE_SHA256
    assert result["provenance"] == "CURRENT_SP16_FORMULA_RESULT"


def test_n2_annex_d_it_is_kept_distinct_from_historical_normcad_catalog_it():
    catalog = HistoricalNormCADProfileCatalog(CAPTURE)
    row = catalog.lookup(35, "15К4", allow_historical_inspection=True)
    assert row["It_mm4_db"] == pytest.approx(385_333.0)
    sp16 = SectionPropertyModel.annex_d_it_for_doubly_symmetric_i_mm4(
        row["h_mm"], row["b_mm"], row["tw_mm"], row["tf_mm"]
    )
    assert sp16["I_t_sp16_annex_d_mm4"] == pytest.approx(497_080.0)
    assert sp16["I_t_sp16_annex_d_mm4"] != pytest.approx(row["It_mm4_db"], rel=1e-3)


def test_n2_historical_normcad_catalog_is_fail_closed_for_production():
    catalog = HistoricalNormCADProfileCatalog(CAPTURE)
    assert catalog.profile_count == 4069
    assert catalog.family_count == 37
    with pytest.raises(PermissionError, match="forbidden as a production"):
        catalog.lookup(35, "15К4")
    row = catalog.lookup(35, "15К4", allow_historical_inspection=True)
    assert row["source_role"] == "HISTORICAL_SECONDARY_ORACLE_NOT_NORMATIVE"
    assert row["production_eligible"] is False
    assert "ГОСТ Р 57837-2017" in row["family_caption"]


def test_n2_15k4_static_capture_matches_prior_normcad_runtime_observation():
    catalog = HistoricalNormCADProfileCatalog(CAPTURE)
    row = catalog.lookup(35, "15К4", allow_historical_inspection=True)
    observed = json.loads(OBS.read_text(encoding="utf-8"))["observed"]
    for key in (
        "h_mm", "b_mm", "tw_mm", "tf_mm", "r_mm", "A_mm2", "Ix_mm4", "Iy_mm4",
        "Wx1_mm3", "Wx2_mm3", "Wy1_mm3", "Wy2_mm3", "Sx_mm3", "Sy_mm3", "afwx", "afwy",
    ):
        assert row[key] == pytest.approx(observed[key])
    assert row["It_mm4_db"] == pytest.approx(observed["It_mm4"], abs=1.0)
    # Runtime report mass is exactly the area-based rho=7850 value, while the raw DB
    # keeps a rounded 46.8 kg/m field.
    assert SectionPropertyModel.mass_kg_m_from_area(row["A_mm2"]) == pytest.approx(observed["mass_kg_m"])
    assert row["mass_kg_m_db"] == pytest.approx(46.8, abs=1e-5)


def test_n2_normcad_capture_audit_is_deterministic_and_exposes_anomalies():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["verdict"] == "PASS_HISTORICAL_CAPTURE_AUDITED_NOT_PRODUCTION_ELIGIBLE"
    assert all(audit["checks"].values())
    assert audit["capture_summary"]["profile_rows"] == 4069
    assert audit["capture_summary"]["family_rows"] == 37
    anomalies = audit["anomaly_summary"]
    assert anomalies["mass_area_mismatch_count_gt_2pct_and_0_15kg_m"] == 25
    assert anomalies["mass_area_mismatch_count_gt_5pct_and_0_15kg_m"] == 23
    assert anomalies["mass_area_mismatch_count_gt_10pct_and_0_15kg_m"] == 17
    assert anomalies["huge_It_gt_1e12_count"] == 268
    assert anomalies["negative_field_counts"] == {
        "r_mm": 1,
        "mass_kg_m_db": 1,
        "Sx_mm3": 1,
        "Sy_mm3": 1,
        "It_mm4_db": 1,
    }
    largest = anomalies["largest_mass_area_mismatches"][0]
    assert largest["id_data"] == 851
    assert largest["designation"] == "Гн. 230х100х8"


def test_n2_normcad_static_algorithm_evidence_localizes_it_first_divergence():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    evidence = audit["static_algorithm_evidence"]
    assert evidence["vb6_source"]["expression_normalized"] == "Jt=(1/3)*(tw^3*(h-2*tf)+2*tf^3*b)"
    assert evidence["sp16_normcad_dsl"]["normalized_sequence"] == [
        "sum_b_t3=3*Jt",
        "Jt_adjusted=(k/3)*sum_b_t3",
        "gr_m=8*omega+0.156*Jt*lambda_y^2/(A*h^2)",
    ]
    p = audit["known_profile_15k4"]
    assert p["unadjusted_plate_sum_over_3_mm4"] == pytest.approx(385_333.3333333333)
    assert p["current_sp16_annex_d_It_mm4"] == pytest.approx(497_080.0)


def test_n2_source_scope_defers_original_gost_profile_audit_by_user_decision():
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    assert scope["authoritative_sp16_source"]["sha256"] == CURRENT_SP16_SOURCE_SHA256
    assert scope["authoritative_sp16_source"]["status"] == "SOLE_NORMATIVE_TRUTH_FOR_SP16"
    assert scope["file_library_search_result"]["current_product_standard_full_tables_found"] is False
    assert "DEFERRED_BY_USER" in scope["substage_policy"]["N2C_CURRENT_PROFILE_CATALOG_REBASELINE"]
    assert scope["runtime_integration_decision"]["requested_by_user"] is True
    assert scope["runtime_integration_decision"]["engineering_use_ready"] is False


def test_n2_discrepancy_register_has_no_open_defects_and_preserves_deferred_gost_gate():
    register = json.loads(DISCREP.read_text(encoding="utf-8"))
    assert register["summary"]["total"] == 7
    assert register["summary"]["open_package_or_dag_defects"] == 0
    assert register["summary"]["open_external_source_dependency"] == 0
    assert register["summary"]["deferred_external_source_dependency"] == 1
    assert not [x for x in register["items"] if x["status"].startswith("OPEN")]
    d6 = next(x for x in register["items"] if x["id"] == "N2-D-006")
    assert d6["status"] == "DEFERRED_BY_USER_TO_FINAL_PROFILE_GOST_AUDIT"
    d7 = next(x for x in register["items"] if x["id"] == "N2-D-007")
    assert d7["status"] == "REMEDIATED_RUNTIME"
