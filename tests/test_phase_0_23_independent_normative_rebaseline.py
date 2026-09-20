import json
from pathlib import Path

import pytest

from standard_core import __release_stage__, __version__
from standard_core.independent_validation import run_independent_validation
from standard_core.normative_rebaseline import run_normative_rebaseline
from standard_core.release_metadata import RELEASE_STAGE
from standard_core import overhead_line_and_switchyard_supports as line_supports

ROOT = Path(__file__).resolve().parents[1]


def test_phase_0_23_canonical_release_identity():
    assert __version__ == "0.67.0"
    assert __release_stage__ == RELEASE_STAGE
    assert RELEASE_STAGE == "v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1"


def test_independent_normative_rebaseline_passes_without_reusing_final_audit_result():
    report = run_normative_rebaseline(ROOT)
    assert report["rebaseline_pass"] is True
    assert report["inventory"]["equations"]["total"] == 241
    assert report["inventory"]["tables"]["total"] == 88
    assert report["inventory"]["procedures"]["total"] == 304
    assert len(report["external_reference_tables"]) == 20
    assert report["adversarial_static_scan"]["literal_dict_get_fallbacks_in_engineering_modules"] == []
    assert report["adversarial_static_scan"]["broad_exception_handlers_in_engineering_modules"] == []


def test_independent_route_boundary_mutation_and_schema_evidence_passes():
    report = run_independent_validation(ROOT)
    assert report["release_scope_pass"] is True
    assert report["primary_route_count"] == 21
    assert report["independent_oracle_case_count"] == 25
    assert len(report["boundary_cases"]) == 24
    assert len(report["mutation_probes"]) == 42
    assert report["targeted_mutation_score"] == 1.0
    assert len(report["schema_adversarial_probes"]) == 6
    assert report["schema_adversarial_all_passed"] is True


def test_table_46_blank_cells_require_explicit_audited_null_semantics(monkeypatch):
    original = line_supports._TABLE_46
    mutated = json.loads(json.dumps(original))
    row = next(r for r in mutated["rows"] if r["row_id"] == "VL_ANCHOR_UNDER_60_ALONG_WIRES")
    row["null_meaning"].pop("horizontal_span")
    monkeypatch.setattr(line_supports, "_TABLE_46", mutated)
    with pytest.raises(ValueError, match="without explicit audited null semantics"):
        line_supports.table_46_deformation_check(
            "VL_ANCHOR_UNDER_60_ALONG_WIRES", "horizontal_span", 0.0
        )


def test_all_materialized_runner_outputs_have_current_phase_provenance():
    result_files = sorted((ROOT / "outputs").glob("*_result.json"))
    assert len(result_files) == 34
    for path in result_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["release_stage"] == RELEASE_STAGE, path.name
