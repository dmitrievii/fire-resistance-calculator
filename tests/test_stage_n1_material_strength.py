from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.material_resistance import SteelMaterialStrengthResolver

ROOT = Path(__file__).resolve().parents[1]
R = SteelMaterialStrengthResolver()
SOURCE_SHA = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def _lookup(product: str, grade: str, t: float) -> tuple[float, float, float | None, float | None]:
    x = R.lookup_strength_row(product, grade, t)
    return x["Ryn_MPa"], x["Run_MPa"], x["Ry_tabulated_MPa"], x["Ru_tabulated_MPa"]


def test_n1_b1_rolled_steel_physical_constants_source_exact():
    p = R.physical_properties()
    assert p["density_kg_m3"] == 7850.0
    assert p["linear_expansion_per_C"] == pytest.approx(1.2e-5)
    assert p["E_MPa"] == 206000.0
    assert p["G_MPa"] == 79000.0
    assert p["poisson_ratio"] == 0.3
    assert p["source_sha256"] == SOURCE_SHA


def test_n1_table_routes_include_tubes_in_v3():
    assert R.material_table_route("plate_sheet_strip") == "В.3"
    assert R.material_table_route("bar_rolled") == "В.3"
    assert R.material_table_route("tube") == "В.3"
    assert R.material_table_route("parallel_flange_i") == "В.4"
    assert R.material_table_route("shaped_rolled") == "В.5"
    with pytest.raises(ValueError, match="external product standard"):
        R.material_table_route("other")


@pytest.mark.parametrize(
    "product,grade,t,expected",
    [
        # Current СП 16 Table В.3 source-backed goldens.
        ("plate_sheet_strip", "С235", 2.0, (235, 360, 230, 350)),
        ("tube", "С255", 3.9, (255, 380, 250, 370)),
        ("tube", "С255", 4.0, (245, 380, 240, 370)),
        ("tube", "С255", 10.0, (245, 380, 240, 370)),
        ("tube", "С255", 10.0001, (245, 370, 240, 360)),
        ("plate_sheet_strip", "С355", 100.0001, (295, 470, 285, 460)),
        ("plate_sheet_strip", "С355", 160.0, (295, 470, 285, 460)),
        ("plate_sheet_strip", "С355", 160.0001, (285, 470, 280, 460)),
        ("plate_sheet_strip", "С355-К", 49.999, (335, 490, 330, 480)),
        ("plate_sheet_strip", "С390-1", 100.0001, (360, 510, 350, 500)),
        ("plate_sheet_strip", "С690", 50.0, (690, 785, None, None)),
        # Current СП 16 Table В.4 source-backed goldens.
        ("parallel_flange_i", "С255Б", 10.0, (255, 380, 250, 370)),
        ("parallel_flange_i", "С255Б-1", 10.0001, (245, 370, 240, 360)),
        ("parallel_flange_i", "С345Б-1", 10.0, (345, 490, 335, 480)),
        ("parallel_flange_i", "С355Б", 100.0001, (295, 460, 290, 450)),
        ("parallel_flange_i", "С390Б", 30.0001, (370, 490, 360, 480)),
        ("parallel_flange_i", "С440Б", 100.0001, (380, 500, 370, 490)),
        # Current СП 16 Table В.5 source-backed goldens.
        ("shaped_rolled", "С255", 8.0, (255, 380, 250, 370)),
        ("shaped_rolled", "С255", 10.0001, (245, 370, 240, 360)),
        ("shaped_rolled", "С345", 20.0001, (305, 460, 300, 450)),
        ("shaped_rolled", "С355-1", 40.0001, (340, 470, 330, 460)),
        ("shaped_rolled", "С390", 10.0001, (380, 500, 370, 480)),
        ("shaped_rolled", "С440", 40.0001, (420, 520, 410, 505)),
    ],
)
def test_n1_source_backed_selected_goldens(product, grade, t, expected):
    assert _lookup(product, grade, t) == expected


def test_n1_v3_exact_source_gap_3_9_to_4_0_is_not_interpolated():
    # The current В.3 transcription prints 2.0–3.9 and 4.0–10.0 for C255.
    # A value strictly between those printed bounds is therefore deliberately fail-closed.
    with pytest.raises(ValueError, match="interpolation and extrapolation are forbidden"):
        R.lookup_strength_row("tube", "С255", 3.95)


def test_n1_v5_flange_thickness_boundaries_are_exact_and_fail_closed():
    assert _lookup("shaped_rolled", "С255", 10.0) == (255, 380, 250, 370)
    assert _lookup("shaped_rolled", "С255", 10.000001) == (245, 370, 240, 360)
    assert _lookup("shaped_rolled", "С255", 20.0) == (245, 370, 240, 360)
    assert _lookup("shaped_rolled", "С255", 20.000001) == (235, 370, 230, 360)
    with pytest.raises(ValueError):
        R.lookup_strength_row("shaped_rolled", "С255", 3.9999)
    with pytest.raises(ValueError):
        R.lookup_strength_row("shaped_rolled", "С255", 40.000001)


def test_n1_identifier_normalization_is_explicit_in_trace():
    got = R.lookup_strength_row("shaped_rolled", "C255", 8.0)
    assert got["steel_grade_input"] == "C255"
    assert got["steel_grade_normalized"] == "С255"
    assert got["Ryn_MPa"] == 255


def test_n1_formula_bundle_keeps_tabulated_rounding_separate():
    x = R.resolve("shaped_rolled", "С255", 8.0, "statistical_control")
    assert x["annex_strength"]["Ry_tabulated_MPa"] == 250
    assert x["annex_strength"]["Ru_tabulated_MPa"] == 370
    assert x["table_2_formula_resistances"]["gamma_m"] == 1.025
    assert x["table_2_formula_resistances"]["Ry_formula_MPa"] == pytest.approx(255 / 1.025)
    assert x["table_2_formula_resistances"]["Ru_formula_MPa"] == pytest.approx(380 / 1.025)
    assert x["table_2_formula_resistances"]["Rs_formula_MPa"] == pytest.approx(0.58 * 255 / 1.025)
    assert x["gamma_u"] == 1.3
    assert x["normative_source_sha256"] == SOURCE_SHA


def test_n1_all_materialized_rows_have_one_resolvable_interior_point():
    files = [
        ("data/annex_v3_strength_resistances.json", "plate_sheet_strip"),
        ("data/annex_v4_parallel_flange_i_strength_resistances.json", "parallel_flange_i"),
        ("data/annex_v5_shaped_strength_resistances.json", "shaped_rolled"),
    ]
    for rel, product in files:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for row in data["rows"]:
            interval = row["thickness_interval"]
            lo, hi = interval["min_mm"], interval["max_mm"]
            if lo is None:
                t = min(1.0, hi / 2.0)
            elif hi is None:
                t = lo + max(1.0, abs(lo) * 0.01)
            else:
                t = (lo + hi) / 2.0
                if not interval["min_inclusive"] and t == lo:
                    t = lo + 1e-6
            for grade in row["grades"]:
                got = R.lookup_strength_row(product, grade, t)
                assert got["Ryn_MPa"] == row["Ryn_MPa"]
                assert got["Run_MPa"] == row["Run_MPa"]
                assert got["Ry_tabulated_MPa"] == row["Ry_MPa"]
                assert got["Ru_tabulated_MPa"] == row["Ru_MPa"]


def test_n1_missing_grade_and_extrapolation_fail_closed():
    with pytest.raises(ValueError):
        R.lookup_strength_row("shaped_rolled", "С999", 10.0)
    with pytest.raises(ValueError):
        R.lookup_strength_row("plate_sheet_strip", "С235", 4.0001)
    with pytest.raises(ValueError):
        R.lookup_strength_row("tube", "С550", 50.0001)
    with pytest.raises(ValueError):
        R.lookup_strength_row("other", "С255", 8.0)


def test_n1_gamma_m_and_gamma_u_are_explicit_not_hidden_defaults():
    with pytest.raises(TypeError):
        # resolve requires a material-safety category, preventing hidden gamma_m.
        R.resolve("shaped_rolled", "С255", 8.0)  # type: ignore[call-arg]
    x = R.resolve("shaped_rolled", "С255", 8.0, "ks1_limited_service")
    assert x["table_2_formula_resistances"]["gamma_m"] == 1.0
    assert x["gamma_u"] == 1.3


def test_n1_ui_strength_catalog_exposes_exact_printed_intervals_without_delivery_standard():
    catalog = R.strength_selection_catalog("parallel_flange_i")
    assert catalog["source_table"] == "В.4"
    grades = {item["steel_grade"]: item["intervals"] for item in catalog["grades"]}
    assert "С255Б" in grades
    first = grades["С255Б"][0]
    assert first["interval_key"] == "*:0|10:1"
    assert first["interval_label"] == "до 10 мм включ."
    assert first["Ryn_MPa"] == 255
    assert first["Run_MPa"] == 380
    assert "delivery_standard" not in first


def test_n1_ui_exact_interval_key_resolves_same_annex_row_as_thickness_lookup():
    by_key = R.lookup_strength_row_by_interval_key("parallel_flange_i", "C255Б", "*:0|10:1")
    by_t = R.lookup_strength_row("parallel_flange_i", "С255Б", 10.0)
    assert by_key["source_table"] == "В.4"
    assert by_key["source_row_index"] == by_t["source_row_index"]
    assert by_key["Ryn_MPa"] == by_t["Ryn_MPa"] == 255
    assert by_key["Run_MPa"] == by_t["Run_MPa"] == 380
    assert by_key["Ry_tabulated_MPa"] == by_t["Ry_tabulated_MPa"] == 250
    assert by_key["Ru_tabulated_MPa"] == by_t["Ru_tabulated_MPa"] == 370


def test_n1_ui_interval_key_fail_closed_for_nonexistent_grade_interval_pair():
    with pytest.raises(ValueError, match="interpolation and extrapolation are forbidden"):
        R.lookup_strength_row_by_interval_key("parallel_flange_i", "С255Б", "10:0|999:1")
