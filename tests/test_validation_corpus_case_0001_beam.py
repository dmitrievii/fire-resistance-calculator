from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from standard_core.bending_members import bolt_hole_factor_eq45, elastic_bending_utilization_eq41

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "VAL-SP16-BEAM-0001"
CASE_DIR = ROOT / "validation" / "cases" / CASE_ID


def _load(name: str):
    return json.loads((CASE_DIR / name).read_text(encoding="utf-8"))


def test_validation_case_0001_source_is_preserved_verbatim_by_hash():
    case = _load("case.json")
    source = ROOT / case["source"]["stored_path"]
    assert source.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == case["source"]["sha256"]
    assert case["source"]["preservation"] == "verbatim_binary_copy"


def test_validation_case_0001_eq45_replays_printed_report_value():
    expected = _load("expected.json")
    check = next(x for x in expected["checks"] if x["check_id"] == "SRC-EQ45")
    actual = bolt_hole_factor_eq45(300.0, 8.0)
    assert actual == pytest.approx(check["published_value"], abs=check["absolute_tolerance"])


def test_validation_case_0001_eq41_replays_page_2_printed_operands_and_verdict():
    expected = _load("expected.json")
    check = next(x for x in expected["checks"] if x["check_id"] == "SRC-EQ41")
    actual = elastic_bending_utilization_eq41(862_981_995.05747, 1_000_000.0, 269.5, 0.95)
    assert actual == pytest.approx(check["published_value"], abs=check["absolute_tolerance"])
    assert actual > 1.0
    assert check["expected_pass_fail"] == "FAIL"


def test_validation_case_0001_does_not_hide_source_section_modulus_conflict():
    case = _load("case.json")
    page1 = case["source_reported_inputs"]["section_page_1"]
    page2 = case["source_reported_inputs"]["section_modulus_used_in_final_eq41_page_2_mm3"]
    assert page1["Wxn1_mm3"] == 196_000.0
    assert page1["Wxn2_mm3"] == 196_000.0
    assert page2 == 1_000_000.0
    ids = {x["finding_id"] for x in case["source_consistency_findings"]}
    assert "SRC-CONFLICT-001" in ids
    assert case["validation_classification"]["count_as_full_end_to_end_golden_case"] is False
    assert case["validation_classification"]["overall_status"] == "PARTIAL_SOURCE_INCONSISTENT"


def test_validation_case_0001_counterfactual_page1_section_modulus_is_materially_different():
    result = _load("production_result.json")
    counterfactual = result["diagnostic_counterfactual"]["actual_utilization"]
    assert counterfactual == pytest.approx(
        elastic_bending_utilization_eq41(862_981_995.05747, 196_000.0, 269.5, 0.95)
    )
    assert counterfactual > 5.0 * 3.37069


def test_validation_case_0001_registry_and_comparison_are_fail_closed():
    registry = json.loads((ROOT / "validation" / "registry" / "validation_registry.json").read_text(encoding="utf-8"))
    row = next(x for x in registry["cases"] if x["case_id"] == CASE_ID)
    comparison = _load("comparison.json")
    assert row["status"] == "PARTIAL_SOURCE_INCONSISTENT"
    assert row["full_end_to_end_golden"] is False
    assert comparison["scalar_replay_summary"] == {"passed": 2, "failed": 0, "total": 2}
    assert comparison["end_to_end_gate"]["status"] == "NOT_ACCEPTED"
    assert set(comparison["end_to_end_gate"]["reason_codes"]) == {"SRC-CONFLICT-001", "SRC-CONFLICT-002"}
