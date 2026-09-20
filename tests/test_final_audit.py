from pathlib import Path

from standard_core.final_audit import run_final_audit, write_audit_reports
from standard_core.validation import run_core_validation_cases, write_validation_reports

ROOT = Path(__file__).resolve().parents[1]


def _audit():
    write_validation_reports(run_core_validation_cases(), ROOT / "reports")
    return run_final_audit(ROOT)


def test_final_audit_selected_scope_and_unresolved_rows():
    report = _audit()
    assert report["release_pass"] is True
    assert report["selected_scope_complete"] is True
    assert report["implemented_equations"] == 240
    assert report["implemented_tables"] == 67
    assert report["implemented_procedures"] == 303
    assert report["unresolved_equations"] == 0
    assert report["unresolved_tables"] == 0
    assert report["full_standard_implemented_or_classified"] is True


def test_all_release_checks_pass():
    report = _audit()
    assert all(report["checks"].values()), report["audit_errors"]


def test_main_report_files_exist():
    report = _audit()
    write_audit_reports(report, ROOT / "reports")
    assert (ROOT / "reports/final_audit_report.md").exists()
    assert (ROOT / "reports/final_audit_report.json").exists()
