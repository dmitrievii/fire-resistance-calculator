import json
from pathlib import Path

from standard_core.validation import run_core_validation_cases, write_validation_reports

ROOT = Path(__file__).resolve().parents[1]


def test_core_self_checks_pass_and_have_error_fields():
    report = run_core_validation_cases()
    assert report["all_passed"] is True
    assert len(report["validation_cases"]) == 1876
    required = {"calculated_value", "reference_value", "absolute_error", "relative_error", "tolerance", "pass_fail"}
    assert all(required <= case.keys() for case in report["validation_cases"])


def test_built_up_validation_cases_are_present():
    report = run_core_validation_cases()
    built_up = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("BUILTUP-")]
    assert len(built_up) == 15
    assert all(case["pass_fail"] == "pass" for case in built_up)


def test_local_stability_validation_cases_are_present():
    report = run_core_validation_cases()
    local = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("LOCAL-")]
    assert len(local) == 25
    assert all(case["pass_fail"] == "pass" for case in local)


def test_complete_table_d1_cross_check_is_present():
    report = run_core_validation_cases()
    d1 = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("AXIAL-D1-")]
    assert len(d1) == 129
    assert all(case["pass_fail"] == "pass" for case in d1)


def test_validation_report_writer():
    report = run_core_validation_cases()
    write_validation_reports(report, ROOT / "reports")
    data = json.loads((ROOT / "reports/validation_report.json").read_text(encoding="utf-8"))
    assert data["all_passed"] is True
    assert (ROOT / "reports/validation_report.md").exists()


def test_bending_validation_cases_and_normative_tables_are_present():
    report = run_core_validation_cases()
    bending = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("BEND-")]
    table_10a = [case for case in bending if case["validation_case_id"].startswith("BEND-10A-")]
    table_e1 = [case for case in bending if case["validation_case_id"].startswith("BEND-E1-")]
    equations = [case for case in bending if case["validation_case_id"].startswith("BEND-EQ-")]
    assert len(bending) == 121
    assert len(table_10a) == 11
    assert len(table_e1) == 70
    assert len(equations) == 22
    assert all(case["pass_fail"] == "pass" for case in bending)


def test_crane_and_annex_zh_validation_cases_are_present():
    report = run_core_validation_cases()
    crane = [case for case in report["validation_cases"] if case["validation_case_id"].startswith(("CRANE-", "STAB-"))]
    annex_zh = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("ZH-")]
    assert len(crane) == 24
    assert len(annex_zh) == 20
    assert all(case["pass_fail"] == "pass" for case in crane + annex_zh)


def test_bending_local_stability_validation_cases_are_present():
    report = run_core_validation_cases()
    cases = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("BLS-")]
    assert len(cases) == 191
    assert all(case["pass_fail"] == "pass" for case in cases)


def test_sheet_structure_validation_cases_are_present():
    report = run_core_validation_cases()
    cases = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("V13-")]
    assert len(cases) == 37
    assert all(case["pass_fail"] == "pass" for case in cases)


def test_built_up_beam_flange_connection_validation_cases_are_present():
    report = run_core_validation_cases()
    cases = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("V17-")]
    assert len(cases) == 11
    assert all(case["pass_fail"] == "pass" for case in cases)


def test_overhead_line_and_switchyard_support_validation_cases_are_present():
    report = run_core_validation_cases()
    cases = [case for case in report["validation_cases"] if case["validation_case_id"].startswith("V19-")]
    assert len(cases) == 30
    assert all(case["pass_fail"] == "pass" for case in cases)
