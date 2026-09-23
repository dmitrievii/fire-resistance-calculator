from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core import fire_sp554_runtime as runtime
from standard_core.schema_validation import validate_case


ROOT = Path(__file__).resolve().parents[1]


def test_v091_standalone_compression_example_is_strict_and_has_no_e_norm_input():
    schema = json.loads(
        (ROOT / "schemas/sp554_fire_central_compression_v091_case.schema.json").read_text(
            encoding="utf-8"
        )
    )
    case = json.loads(
        (ROOT / "examples/fire_d2_sp554_critical_temperature_case_v091.json").read_text(
            encoding="utf-8"
        )
    )
    assert validate_case(case, schema) == []
    assert "E_norm_n_mm2" not in case
    assert "lambda_bar" not in case["route"]
    assert "J_min_mm4" not in case["route"]

    result = runtime.sp554_fire_mechanical_guided_workflow(case)
    assert result["status"] == "COMPLETE"
    assert result["E_normative_n_mm2"] == pytest.approx(206000.0)
    assert result["route_trace"]["governing_strength_axis"] == "y"
    assert result["route_trace"]["governing_stiffness_axis"] == "y"
    assert result["critical_temperature_c"] == pytest.approx(
        min(
            float(result["strength_curve_inversion"]["temperature_c"]),
            float(result["modulus_curve_inversion"]["temperature_c"]),
        )
    )
