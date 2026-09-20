import json
import math
from pathlib import Path

import pytest

from standard_core.axial_members import open_u_section_phi_1, open_u_section_torsional_flexural_utilization
from standard_core.general_requirements import table_1_working_condition_factor
from standard_core.schema_validation import validate_case

ROOT = Path(__file__).resolve().parents[1]


def test_equation_11():
    assert open_u_section_phi_1(0.8, 2.0) == pytest.approx(1.52)


def test_equation_11_rejects_zero_slenderness():
    with pytest.raises(ValueError):
        open_u_section_phi_1(0.8, 0.0)


def test_equation_10_historical_seed():
    value = open_u_section_torsional_flexural_utilization(500000.0, 3000.0, 340.0, 1.05, 0.8, 2.0)
    assert value == pytest.approx(0.4672271897817039)


def test_equation_10_piecewise_threshold_and_upper_cap():
    # phi1=0.85 exactly -> lower branch
    c_threshold = 0.85 * 4.0 / 7.6
    expected = 100000.0 / (0.85 * 1000.0 * 300.0)
    assert open_u_section_torsional_flexural_utilization(100000.0, 1000.0, 300.0, 1.0, c_threshold, 2.0) == pytest.approx(expected)
    # very large phi1 -> phi_c must not exceed 1
    assert open_u_section_torsional_flexural_utilization(100000.0, 1000.0, 300.0, 1.0, 1.0, 0.5) == pytest.approx(1.0/3.0)


def test_table_1_note_5_and_representative_rows():
    assert table_1_working_condition_factor("default_unlisted_case_note_5") == 1.0
    assert table_1_working_condition_factor("3_single_storey_industrial_columns_with_overhead_cranes") == 1.05
    assert table_1_working_condition_factor("9c_bearing_plate_60_lt_t_le_80mm") == 1.10
    with pytest.raises(ValueError):
        table_1_working_condition_factor("invented_case")


def test_schema_validation_is_recursive_and_rejects_nan():
    schema = {
        "type":"object", "required":["outer"], "additionalProperties":False,
        "properties":{"outer":{"type":"object","required":["values"],"additionalProperties":False,
            "properties":{"values":{"type":"array","minItems":1,"items":{"type":"number","minimum":0}}}}}
    }
    assert validate_case({"outer":{"values":[1.0, 2]}}, schema) == []
    errors = validate_case({"outer":{"values":[1.0, float("nan")], "extra":1}}, schema)
    assert any("must be finite" in item for item in errors)
    assert any("Unexpected property" in item for item in errors)


def test_annex_reconstruction_catalog_is_fail_closed():
    data = json.loads((ROOT/"data/annex_reconstruction_catalog_v0_22.json").read_text(encoding="utf-8"))
    assert len(data["tables"]) == 24
    assert {item["status"] for item in data["tables"]} == {"external_reference_required"}
    assert all(item["interpolation_policy"] == "none_invented" for item in data["tables"])
