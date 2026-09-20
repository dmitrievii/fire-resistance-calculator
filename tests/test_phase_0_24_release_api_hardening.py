from __future__ import annotations

import json
from pathlib import Path

from standard_core.api_hardening import run_api_hardening
from standard_core.function_level_validation import run_function_level_validation
from standard_core.normative_rebaseline import run_normative_rebaseline
from standard_core.release_metadata import ENGINEERING_USE_READY, PACKAGE_VERSION, RELEASE_STAGE

ROOT = Path(__file__).resolve().parents[1]


def test_phase_0_24_release_identity_and_engineering_gate():
    assert PACKAGE_VERSION == "0.67.0"
    assert RELEASE_STAGE == "v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1"
    assert ENGINEERING_USE_READY is False


def test_phase_0_24_api_hardening_and_parent_compatibility():
    report = run_api_hardening(ROOT)
    assert report["api_hardening_pass"] is True
    assert report["public_api"]["engineering_functions"] == 581
    assert report["public_api"]["missing_parameter_annotations"] == []
    assert report["public_api"]["missing_return_annotations"] == []
    assert report["public_api"]["varargs_or_varkw"] == []
    assert report["public_api"]["mutable_defaults"] == []
    assert report["public_api"]["functions_without_audit_id"] == []
    assert report["compatibility_with_v0_22_freeze"]["backward_call_compatibility_pass"] is True
    parent = report["compatibility_with_parent_v0_23_freeze"]
    assert parent["backward_call_compatibility_pass"] is True
    assert len(parent["annotation_only_changes"]) == 62
    assert parent["removed_objects"] == []
    assert parent["incompatible_call_shape_changes"] == []


def test_phase_0_24_function_level_evidence_taxonomy_and_scope():
    report = run_function_level_validation(ROOT)
    assert report["function_level_validation_pass"] is True
    assert report["engineering_public_function_count"] == 581
    assert report["direct_named_test_reference_count"] == 581
    assert report["executed_function_body_count"] == 581
    assert report["independent_direct_function_oracle_case_count"] == 40
    assert report["independently_oracled_function_count"] == 40
    assert report["independent_public_function_validation_complete"] is False
    assert report["open_gap"]["functions_without_independent_direct_oracle"] == 541
    assert all(case["pass_fail"] == "pass" for case in report["independent_direct_oracles"])


def test_phase_0_24_normative_rebaseline_still_passes():
    report = run_normative_rebaseline(ROOT)
    assert report["rebaseline_pass"] is True
    assert len(report["external_reference_tables"]) == 20


def test_materialized_outputs_carry_current_release_stage():
    outputs = sorted((ROOT / "outputs").glob("*.json"))
    assert len(outputs) == 34
    for path in outputs:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["release_stage"] == RELEASE_STAGE
