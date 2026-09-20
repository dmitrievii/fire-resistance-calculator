from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.material_resistance import SteelMaterialStrengthResolver

ROOT = Path(__file__).resolve().parents[1]
MATRIX = json.loads((ROOT / "validation/stage_n1/boundary_probe_matrix_stage_n1.json").read_text(encoding="utf-8"))
SOURCE = json.loads((ROOT / "validation/stage_n1/current_sp16_source_capture_stage_n1.json").read_text(encoding="utf-8"))
R = SteelMaterialStrengthResolver()


def test_n1_exhaustive_boundary_matrix_is_source_derived_and_nontrivial():
    assert MATRIX["normative_source_sha256"] == SOURCE["normative_source"]["source_sha256"]
    assert MATRIX["summary"]["probe_count"] == len(MATRIX["probes"])
    assert MATRIX["summary"]["probe_count"] >= 900
    assert MATRIX["summary"]["expected_fail_closed"] > 0
    assert MATRIX["summary"]["by_table"] == {"В.3": 708, "В.4": 157, "В.5": 116}


def test_n1_every_source_interval_boundary_and_nextafter_probe_matches_production():
    failures = []
    for p in MATRIX["probes"]:
        expected = p["expected"]
        args = (p["product_form"], p["steel_grade"], p["thickness_mm"])
        if "error" in expected:
            try:
                R.lookup_strength_row(*args)
            except ValueError:
                continue
            except Exception as exc:  # a different failure mode is also a defect
                failures.append({"probe": p, "observed_exception": repr(exc)})
                continue
            failures.append({"probe": p, "observed": "RESOLVED_BUT_SOURCE_EXPECTS_FAIL_CLOSED"})
            continue

        try:
            got = R.lookup_strength_row(*args)
        except Exception as exc:
            failures.append({"probe": p, "observed_exception": repr(exc)})
            continue

        observed = {
            "source_row_index": got["source_row_index"],
            "Ryn_MPa": got["Ryn_MPa"],
            "Run_MPa": got["Run_MPa"],
            "Ry_MPa": got["Ry_tabulated_MPa"],
            "Ru_MPa": got["Ru_tabulated_MPa"],
        }
        if observed != expected:
            failures.append({"probe": p, "observed": observed})

    assert failures == []


def test_n1_all_current_grade_identifiers_accept_latin_leading_c_with_traceable_normalization():
    for table_key, product_form in (("V3", "plate_sheet_strip"), ("V4", "parallel_flange_i"), ("V5", "shaped_rolled")):
        for row in SOURCE[table_key]["rows"]:
            iv = row["thickness_interval"]
            lo, hi = iv.get("min_mm"), iv.get("max_mm")
            if lo is None:
                t = max(1.0, float(hi) / 2.0)
            elif hi is None:
                t = float(lo) + max(1.0, abs(float(lo)) * 0.01)
            else:
                t = (float(lo) + float(hi)) / 2.0
            for grade in row["grades"]:
                assert grade.startswith("С")
                latin = "C" + grade[1:]
                got = R.lookup_strength_row(product_form, latin, t)
                assert got["steel_grade_input"] == latin
                assert got["steel_grade_normalized"] == grade
                assert got["Ryn_MPa"] == row["Ryn_MPa"]
                assert got["Run_MPa"] == row["Run_MPa"]


@pytest.mark.parametrize("category,gamma", [
    ("statistical_control", 1.025),
    ("nonstatistical_high_yield_or_hot_finished_or_foreign", 1.1),
    ("other_conforming", 1.05),
    ("ks1_limited_service", 1.0),
])
def test_n1_all_table3_categories_drive_all_table2_resistances_exactly(category: str, gamma: float):
    out = R.formula_resistances(355.0, 490.0, category)
    assert out["gamma_m"] == gamma
    assert out["Ry_formula_MPa"] == pytest.approx(355.0 / gamma)
    assert out["Ru_formula_MPa"] == pytest.approx(490.0 / gamma)
    assert out["Rs_formula_MPa"] == pytest.approx(0.58 * 355.0 / gamma)
    assert out["Rp_formula_MPa"] == pytest.approx(490.0 / gamma)
    assert out["Rlp_formula_MPa"] == pytest.approx(0.5 * 490.0 / gamma)
    assert out["Rcd_formula_MPa"] == pytest.approx(0.025 * 490.0 / gamma)
