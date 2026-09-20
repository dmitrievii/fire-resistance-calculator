from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path

import pytest

from standard_core.profile_catalog import (
    INTERIM_CATALOG_STATUS,
    ORIGINAL_GOST_AUDIT_COMPLETE,
    TABLE7_COEFFICIENTS,
    InterimProfileCatalog,
)
from standard_core.runner import run_case

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DATA = ROOT / "data/profile_catalog_interim_v0_28_stage_n2.json"
FAMILY_REGISTRY = ROOT / "data/profile_family_registry_v0_28_stage_n2.json"


def _payload() -> dict:
    return json.loads(CATALOG_DATA.read_text(encoding="utf-8"))


def _isolated_runner_root(tmp_path: Path) -> Path:
    import shutil
    isolated = tmp_path / "runner_root"
    isolated.mkdir()
    shutil.copytree(ROOT / "schemas", isolated / "schemas")
    (isolated / "outputs").mkdir()
    (isolated / "reports").mkdir()
    return isolated


def test_n2_interim_catalog_cardinality_and_deferred_source_gate():
    catalog = InterimProfileCatalog()
    assert catalog.profile_count == 4069
    assert catalog.family_count == 37
    assert sum(len(catalog.list_profiles(f["family_id"])) for f in catalog.list_families()) == 4069
    assert ORIGINAL_GOST_AUDIT_COMPLETE is False
    assert _payload()["status"] == INTERIM_CATALOG_STATUS
    assert _payload()["original_gost_audit_complete"] is False


def test_n2_duplicate_designation_requires_source_row_id_and_is_resolvable():
    catalog = InterimProfileCatalog()
    with pytest.raises(ValueError, match="ambiguous profile designation"):
        catalog.resolve(14, "17,5КТ1")
    row80 = catalog.resolve(14, "17,5КТ1", source_row_id=80)
    row82 = catalog.resolve(14, "17,5КТ1", source_row_id=82)
    assert row80["dimensions"]["h_mm"] == 168.0
    assert row82["dimensions"]["h_mm"] == 173.0
    assert row80["profile_ref"]["source_row_id"] == 80
    assert row82["profile_ref"]["source_row_id"] == 82


def test_n2_every_imported_profile_resolves_with_positive_runtime_core_properties():
    catalog = InterimProfileCatalog()
    payload = _payload()
    unresolved_torsion = []
    nonfinite = []
    for row in payload["profiles"]:
        bundle = catalog.resolve(row["family_id"], row["designation"], source_row_id=row["source_row_id"])
        p = bundle["catalog_properties_interim"]
        d = bundle["derived_properties"]
        runtime_values = {
            "A": p["A_mm2"], "Ix": p["Ix_mm4"], "Iy": p["Iy_mm4"],
            "rx": d["radius_x_mm"], "ry": d["radius_y_mm"],
            "mass": d["mass_kg_m_at_7850"], "It": d["torsional_inertia_mm4"],
        }
        for key, value in runtime_values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or float(value) <= 0:
                nonfinite.append((row["source_row_id"], row["designation"], key, value))
        if d["torsion_policy"] == "UNRESOLVED_FAIL_CLOSED":
            unresolved_torsion.append((row["source_row_id"], row["designation"]))
        assert d["mass_kg_m_at_7850"] == pytest.approx(float(p["A_mm2"]) * 0.00785)
        assert d["radius_x_mm"] == pytest.approx(math.sqrt(float(p["Ix_mm4"]) / float(p["A_mm2"])))
        assert d["radius_y_mm"] == pytest.approx(math.sqrt(float(p["Iy_mm4"]) / float(p["A_mm2"])))
        assert float(d["torsional_inertia_mm4"]) < 1e12
        for axis in ("x", "y"):
            t7 = bundle["sp16_table7"][axis]
            expected = TABLE7_COEFFICIENTS[t7["section_type"]]
            assert t7["alpha"] == expected["alpha"]
            assert t7["beta"] == expected["beta"]
            assert t7["phi_cap_lambda_bar_threshold"] == expected["phi_cap_lambda_bar_threshold"]
    assert nonfinite == []
    assert unresolved_torsion == []


def test_n2_table7_representative_family_mapping_and_coefficients():
    c = InterimProfileCatalog()

    i15 = c.resolve(35, "15К4")
    assert i15["sp16_table7"]["x"]["section_type"] == "b"
    assert i15["sp16_table7"]["x"]["alpha"] == 0.04
    assert i15["sp16_table7"]["x"]["beta"] == 0.09
    assert i15["sp16_table7"]["y"]["section_type"] == "c"
    assert i15["sp16_table7"]["y"]["beta"] == 0.14

    i100 = c.resolve(1, "100Б1")
    assert i100["dimensions"]["h_mm"] == 990.0
    assert i100["sp16_table7"]["x"]["section_type"] == "a"  # Table 7 Note 1, h > 500 mm
    assert i100["sp16_table7"]["x"]["alpha"] == 0.03
    assert i100["sp16_table7"]["x"]["beta"] == 0.06
    assert i100["sp16_table7"]["y"]["section_type"] == "c"

    shs = c.resolve(5, "Гн.[]50х2")
    assert (shs["sp16_table7"]["x"]["section_type"], shs["sp16_table7"]["y"]["section_type"]) == ("a", "a")

    chs = c.resolve(17, "Тр. 83x3")
    assert (chs["sp16_table7"]["x"]["section_type"], chs["sp16_table7"]["y"]["section_type"]) == ("a", "a")

    tee = c.resolve(14, "10КТ1")
    assert (tee["sp16_table7"]["x"]["section_type"], tee["sp16_table7"]["y"]["section_type"]) == ("c", "c")

    channel = c.resolve(22, "[ 5")
    assert (channel["sp16_table7"]["x"]["section_type"], channel["sp16_table7"]["y"]["section_type"]) == ("c", "c")

    angle = c.resolve(18, "L 25x16x3")
    assert (angle["sp16_table7"]["x"]["section_type"], angle["sp16_table7"]["y"]["section_type"]) == ("c", "c")

    zed = c.resolve(10, "Гн. Z 40x32x2")
    assert (zed["sp16_table7"]["x"]["section_type"], zed["sp16_table7"]["y"]["section_type"]) == ("b", "b")


def test_n2_torsion_policies_compute_instead_of_using_known_bad_normcad_fields():
    c = InterimProfileCatalog()

    i = c.resolve(35, "15К4")
    assert i["derived_properties"]["torsion_policy"] == "CURRENT_SP16_ANNEX_D_FORMULA"
    assert i["derived_properties"]["annex_d_k"] == 1.29
    assert i["derived_properties"]["torsional_inertia_mm4"] == pytest.approx(497080.0)
    assert i["historical_fields_not_used_as_runtime_truth"]["It_mm4_db"] == pytest.approx(385333.0)

    pipe = c.resolve(17, "Тр. 83x3")
    assert pipe["derived_properties"]["torsion_policy"] == "GEOMETRY_IDENTITY_CIRCULAR_J_EQUALS_IX_PLUS_IY"
    assert pipe["derived_properties"]["torsional_inertia_mm4"] == pytest.approx(1_208_000.0)
    assert pipe["historical_fields_not_used_as_runtime_truth"]["It_mm4_db"] == pytest.approx(12_080_000_000.0)

    rhs = c.resolve(5, "Гн.[]50х2")
    assert rhs["derived_properties"]["torsion_policy"].startswith("GEOMETRY_DERIVED_CLOSED_THIN_WALL_BREDT")
    assert rhs["derived_properties"]["torsional_inertia_mm4"] > 0

    angle = c.resolve(18, "L 25x16x3")
    assert angle["derived_properties"]["torsion_policy"].startswith("GEOMETRY_DERIVED_OPEN_THIN_WALL")
    assert angle["derived_properties"]["torsional_inertia_mm4"] > 0


def test_n2_corrupt_historical_mass_and_afw_never_leak_into_runtime_truth():
    c = InterimProfileCatalog()
    row = c.resolve(6, "Гн. 230х100х8")
    hist = row["historical_fields_not_used_as_runtime_truth"]
    assert hist["mass_kg_m_db"] > 1e12
    assert row["derived_properties"]["mass_kg_m_at_7850"] == pytest.approx(4859.2001953 * 0.00785)
    assert row["derived_properties"]["mass_kg_m_at_7850"] < 100.0

    pipe = c.resolve(17, "Тр. 83x3")
    histp = pipe["historical_fields_not_used_as_runtime_truth"]
    assert histp["afwx_db"] > 1e20
    assert histp["afwy_db"] > 1e20
    assert pipe["derived_properties"]["alpha_f_x"] is None
    assert pipe["derived_properties"]["alpha_f_y"] is None


def test_n2_alpha_f_is_recomputed_for_supported_groups():
    c = InterimProfileCatalog()
    i = c.resolve(35, "15К4")
    h = 160.0; b = 152.0; tw = 10.0; tf = 15.0
    expected_x = tf * b / (tw * (h - 2 * tf))
    expected_y = tw * (h - 2 * tf) / (2 * tf * b)
    assert i["derived_properties"]["alpha_f_x"] == pytest.approx(expected_x)
    assert i["derived_properties"]["alpha_f_y"] == pytest.approx(expected_y)
    # Historical values are preserved only for evidence and are not used as runtime truth.
    assert i["derived_properties"]["alpha_f_x"] != pytest.approx(i["historical_fields_not_used_as_runtime_truth"]["afwx_db"])


def test_n2_profile_catalog_direct_runner_action_operates(tmp_path: Path):
    isolated = _isolated_runner_root(tmp_path)
    result = run_case(ROOT / "examples/profile_catalog_example.json", isolated)
    assert result["action"] == "profile_catalog_resolve"
    assert result["results"]["designation"] == "15К4"
    assert result["results"]["selected_axis_properties"]["table7_section_type"] == "b"
    assert result["results"]["derived_properties"]["torsional_inertia_mm4"] == pytest.approx(497080.0)
    assert result["results"]["original_gost_audit_complete"] is False


def test_n2_profile_ref_hydrates_existing_axial_branch_before_schema_validation(tmp_path: Path):
    case = json.loads((ROOT / "examples/axial_member_example.json").read_text(encoding="utf-8"))
    case["case_id"] = "N2-PROFILE-HYDRATED-AXIAL-001"
    case.pop("gross_area_mm2")
    case.pop("net_area_mm2")
    case.pop("section_type")
    case["profile_ref"] = {
        "family_id": 35,
        "designation": "15К4",
        "axis": "x",
        "use_gross_as_net": True,
    }
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    isolated = _isolated_runner_root(tmp_path)
    result = run_case(path, isolated)
    assert result["inputs"]["gross_area_mm2"] == pytest.approx(5964.0)
    assert result["inputs"]["net_area_mm2"] == pytest.approx(5964.0)
    assert result["inputs"]["section_type"] == "b"
    assert result["results"]["section_type"] == "b"
    assert result["engineering_calculation_performed"] is True


def test_n2_profile_ref_y_axis_hydrates_table7_type_c(tmp_path: Path):
    case = json.loads((ROOT / "examples/axial_member_example.json").read_text(encoding="utf-8"))
    case["case_id"] = "N2-PROFILE-HYDRATED-AXIAL-Y-001"
    case.pop("gross_area_mm2")
    case.pop("net_area_mm2")
    case.pop("section_type")
    case["profile_ref"] = {
        "family_id": 35,
        "designation": "15К4",
        "axis": "y",
        "use_gross_as_net": True,
    }
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    isolated = _isolated_runner_root(tmp_path)
    result = run_case(path, isolated)
    assert result["inputs"]["section_type"] == "c"


def test_n2_family_registry_carries_exact_current_sp16_table7_coefficients():
    registry = json.loads(FAMILY_REGISTRY.read_text(encoding="utf-8"))
    assert registry["table7_coefficients"] == {
        "a": {"alpha": 0.03, "beta": 0.06},
        "b": {"alpha": 0.04, "beta": 0.09},
        "c": {"alpha": 0.04, "beta": 0.14},
    }
    assert len(registry["families"]) == 37


def test_n2_atomic_dag_uses_interim_external_profile_catalog_with_hash_gate():
    import hashlib
    dag_path = ROOT / "normative_graph/dag_v0.3.31_stage_n2.json"
    dag = json.loads(dag_path.read_text(encoding="utf-8"))
    dataset = next(x for x in dag["datasets"] if x["id"] == "SECTION_CATALOG_STAGE2")
    assert dataset["storage"]["mode"] == "external"
    assert dataset["storage"]["uri"] == "../data/profile_catalog_interim_v0_28_stage_n2.json"
    actual = hashlib.sha256(CATALOG_DATA.read_bytes()).hexdigest()
    assert dataset["storage"]["sha256"] == actual
    assert "PENDING_ORIGINAL_GOST_AUDIT" in dataset["notes"]


def test_n2_runtime_integration_summary_covers_all_profiles_and_torsion_policies():
    summary = json.loads((ROOT / "validation/stage_n2/evidence/n2_runtime_integration_summary.json").read_text(encoding="utf-8"))
    assert summary["runtime_catalog"]["profile_rows"] == 4069
    assert summary["runtime_catalog"]["families"] == 37
    assert summary["runtime_catalog"]["all_rows_resolved"] is True
    assert summary["runtime_catalog"]["resolution_errors"] == []
    assert sum(summary["derived_runtime_policy_counts"]["torsion"].values()) == 4069
    assert summary["derived_runtime_policy_counts"]["torsion"] == {
        "CURRENT_SP16_ANNEX_D_FORMULA": 887,
        "GEOMETRY_DERIVED_CLOSED_THIN_WALL_BREDT_APPROXIMATION_PENDING_ORIGINAL_GOST_AUDIT": 1018,
        "GEOMETRY_DERIVED_OPEN_THIN_WALL_APPROXIMATION_PENDING_ORIGINAL_GOST_AUDIT": 304,
        "GEOMETRY_IDENTITY_CIRCULAR_J_EQUALS_IX_PLUS_IY": 1860,
    }
    assert summary["runtime_catalog"]["original_gost_audit_complete"] is False
