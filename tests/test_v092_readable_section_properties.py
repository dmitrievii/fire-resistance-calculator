from __future__ import annotations

import pytest

from standard_core.report_ir_v092 import _humanize_executed_section_properties
from streamlit_section_properties_v092 import canonical_profile_rows


def _row_index(rows):
    return {row["symbol"]: row for row in rows}


def test_catalog_preview_maps_source_major_minor_to_canonical_z_y_and_shows_complete_core_properties():
    resolved = {
        "dimensions": {
            "h_mm": 400.0,
            "b_mm": 200.0,
            "tw_mm": 8.0,
            "tf_mm": 13.0,
        },
        "catalog_properties_interim": {
            "A_mm2": 6500.0,
            "Ix_mm4": 180_000_000.0,
            "Iy_mm4": 14_000_000.0,
            "Wx1_mm3": 900_000.0,
            "Wx2_mm3": 900_000.0,
            "Wy1_mm3": 140_000.0,
            "Wy2_mm3": 140_000.0,
            "Sx_mm3": 510_000.0,
            "Sy_mm3": 85_000.0,
            "mass_kg_m": 51.0,
        },
        "derived_properties": {
            "radius_x_mm": 166.41,
            "radius_y_mm": 46.41,
        },
    }

    rows = canonical_profile_rows(resolved)
    by_symbol = _row_index(rows)

    for symbol in ("h", "b", "t_w", "t_f", "A", "I_z", "I_y", "i_z", "i_y", "W_z", "W_y", "S_z", "S_y"):
        assert symbol in by_symbol

    assert by_symbol["I_z"]["value"] == pytest.approx(180_000_000.0)
    assert by_symbol["I_y"]["value"] == pytest.approx(14_000_000.0)
    assert by_symbol["i_z"]["value"] == pytest.approx(166.41)
    assert by_symbol["i_y"]["value"] == pytest.approx(46.41)
    assert by_symbol["W_z"]["value"] == pytest.approx(900_000.0)
    assert by_symbol["W_y"]["value"] == pytest.approx(140_000.0)
    assert by_symbol["S_z"]["value"] == pytest.approx(510_000.0)
    assert by_symbol["S_y"]["value"] == pytest.approx(85_000.0)
    assert by_symbol["I_z"]["name_ru"].startswith("Момент инерции относительно сильной")
    assert by_symbol["I_y"]["name_ru"].startswith("Момент инерции относительно слабой")

    # Technical source fields are provenance only; they are not engineering labels.
    engineering_symbols = set(by_symbol)
    assert "Ix_mm4" not in engineering_symbols
    assert "Iy_mm4" not in engineering_symbols


def test_catalog_preview_axis_mapping_is_physical_not_mechanical_x_to_z_rename():
    resolved = {
        "dimensions": {},
        "catalog_properties_interim": {
            "A_mm2": 1000.0,
            "Ix_mm4": 20_000.0,
            "Iy_mm4": 80_000.0,
            "Wx1_mm3": 2000.0,
            "Wx2_mm3": 2000.0,
            "Wy1_mm3": 8000.0,
            "Wy2_mm3": 8000.0,
            "Sx_mm3": 1000.0,
            "Sy_mm3": 4000.0,
        },
        "derived_properties": {
            "radius_x_mm": 4.47213595,
            "radius_y_mm": 8.94427191,
        },
    }

    by_symbol = _row_index(canonical_profile_rows(resolved))
    assert by_symbol["I_z"]["value"] == pytest.approx(80_000.0)
    assert by_symbol["I_y"]["value"] == pytest.approx(20_000.0)
    assert by_symbol["W_z"]["value"] == pytest.approx(8000.0)
    assert by_symbol["W_y"]["value"] == pytest.approx(2000.0)
    assert by_symbol["S_z"]["value"] == pytest.approx(4000.0)
    assert by_symbol["S_y"]["value"] == pytest.approx(1000.0)


def test_report_humanizes_only_executed_rows_and_keeps_quantity_ids_for_audit():
    report = {
        "blocks": [
            {
                "inputs": [],
                "outputs": [
                    {"quantity_id": "major_axis_is_x", "raw_value": True, "canonical_unit": "1"},
                    {"quantity_id": "A_gross", "raw_value": 6500.0, "canonical_unit": "mm2", "name_ru": "A_gross", "symbol": None},
                    {"quantity_id": "J_x", "raw_value": 180_000_000.0, "canonical_unit": "mm4", "name_ru": "J_x", "symbol": None},
                    {"quantity_id": "J_y", "raw_value": 14_000_000.0, "canonical_unit": "mm4", "name_ru": "J_y", "symbol": None},
                    {"quantity_id": "W_el_x_pos", "raw_value": 900_000.0, "canonical_unit": "mm3", "name_ru": "W_el_x_pos", "symbol": None},
                    {"quantity_id": "W_el_y_pos", "raw_value": 140_000.0, "canonical_unit": "mm3", "name_ru": "W_el_y_pos", "symbol": None},
                    {"quantity_id": "S_shear_gross", "raw_value": 510_000.0, "canonical_unit": "mm3", "name_ru": "S_shear_gross", "symbol": None},
                ],
            }
        ]
    }

    changed = _humanize_executed_section_properties(report)
    assert changed == 6
    outputs = {row["quantity_id"]: row for row in report["blocks"][0]["outputs"]}

    assert outputs["A_gross"]["name_ru"] == "Площадь поперечного сечения"
    assert outputs["A_gross"]["symbol"] == "A"
    assert outputs["A_gross"]["display_value"] == "6500 мм²"
    assert outputs["J_x"]["symbol"] == "I_z"
    assert "сильной главной оси z-z" in outputs["J_x"]["name_ru"]
    assert outputs["J_y"]["symbol"] == "I_y"
    assert "слабой главной оси y-y" in outputs["J_y"]["name_ru"]
    assert outputs["W_el_x_pos"]["symbol"] == "W_{z,+}"
    assert outputs["W_el_y_pos"]["symbol"] == "W_{y,+}"
    assert outputs["S_shear_gross"]["symbol"] == "S"

    # Machine/audit identity stays intact; only presentation semantics change.
    assert outputs["J_x"]["quantity_id"] == "J_x"
    assert outputs["J_x"]["technical_quantity_id_visible_in_main_report"] is False


def test_report_does_not_guess_legacy_axis_without_explicit_axis_evidence():
    report = {
        "blocks": [
            {
                "inputs": [],
                "outputs": [
                    {"quantity_id": "A_gross", "raw_value": 6500.0, "canonical_unit": "mm2", "name_ru": "A_gross", "symbol": None},
                    {"quantity_id": "J_x", "raw_value": 180_000_000.0, "canonical_unit": "mm4", "name_ru": "J_x", "symbol": None},
                ],
            }
        ]
    }

    changed = _humanize_executed_section_properties(report)
    outputs = {row["quantity_id"]: row for row in report["blocks"][0]["outputs"]}
    assert changed == 1
    assert outputs["A_gross"]["symbol"] == "A"
    assert outputs["J_x"]["name_ru"] == "J_x"
    assert outputs["J_x"]["symbol"] is None
