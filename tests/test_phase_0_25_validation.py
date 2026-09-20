from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from standard_core.phase_0_25_validation import run_phase_0_25_validation
from standard_core.release_metadata import ENGINEERING_USE_READY, PACKAGE_VERSION, RELEASE_STAGE

ROOT = Path(__file__).resolve().parents[1]


def test_phase_0_25_release_identity_and_gate():
    assert PACKAGE_VERSION == "0.67.0"
    assert RELEASE_STAGE == "v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1"
    assert ENGINEERING_USE_READY is False


def test_phase_0_25_independent_oracle_expansion_passes():
    report = run_phase_0_25_validation(ROOT)
    assert report["phase_0_25_validation_pass"] is True
    assert report["phase_0_24_parent_oracle_case_count"] == 40
    assert report["phase_0_25_added_oracle_case_count"] == 20
    assert report["combined_independently_oracled_function_count"] == 60
    assert report["engineering_public_function_count"] == 581
    assert report["open_gaps"]["engineering_functions_without_independent_direct_oracle"] == 521
    assert all(x["pass_fail"] == "pass" for x in report["expanded_independent_oracles"])


def test_phase_0_25_external_scad_golden_comparison_is_partial_but_passes():
    report = run_phase_0_25_validation(ROOT)
    external = report["external_golden_validation"]
    assert external["case_count"] == 6
    assert external["passed_count"] == 6
    assert external["failed_count"] == 0
    assert external["pass"] is True
    assert report["externally_compared_distinct_function_count"] == 5
    assert report["external_independent_validation_complete"] is False
    assert report["open_gaps"]["live_vendor_replay_performed"] is False


def test_phase_0_25_golden_contract_rejects_malformed_and_nonfinite_cases():
    report = run_phase_0_25_validation(ROOT)
    probes = report["golden_contract_adversarial_probes"]
    assert len(probes) == 8
    assert all(p["rejected"] and p["pass_fail"] == "pass" for p in probes)


def test_phase_0_25_engineering_api_is_unchanged_from_parent_v0_24():
    compat = run_phase_0_25_validation(ROOT)["parent_v0_24_engineering_api_compatibility"]
    assert compat["pass"] is True
    assert compat["parent_engineering_function_count"] == 581
    assert compat["current_engineering_function_count"] == 581
    assert compat["removed_engineering_functions"] == []
    assert compat["added_engineering_functions"] == []
    assert compat["changed_engineering_signatures"] == []


def test_external_benchmark_corpus_is_strictly_finite_and_has_source_metadata():
    data = json.loads((ROOT / "data/external_scad_benchmarks_v0_25_reconstructed_r1.json").read_text(encoding="utf-8"))
    assert len(data["cases"]) == 6
    assert data["verification_compendium"]["source_url"].startswith("https://scadsoft.com/")
    for case in data["cases"]:
        assert case["source_pdf_pages"]
        assert case["absolute_tolerance"] >= 0
        assert math.isfinite(case["published_value"])
        assert case["function"].startswith("standard_core.")
