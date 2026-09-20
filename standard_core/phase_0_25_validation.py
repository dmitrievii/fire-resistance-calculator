"""Independent function-oracle expansion and external golden validation for Phase 0.25."""

from __future__ import annotations

import importlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .api_hardening import run_api_hardening
from .function_level_validation import run_function_level_validation
from .release_metadata import (
    ENGINEERING_USE_READY,
    PACKAGE_VERSION,
    PARENT_RELEASE,
    RELEASE_QUALIFICATION,
    RELEASE_STAGE,
    STANDARD_TITLE,
)


@dataclass(frozen=True)
class _Oracle:
    case_id: str
    module: str
    function: str
    standard_reference: str
    args: tuple[Any, ...]
    expected: Callable[[], Any]
    kwargs: dict[str, Any] | None = None
    tolerance: float = 1e-10


def _expanded_oracles() -> list[_Oracle]:
    """Return Phase 0.25 source-rederived closed-form oracles not present in Phase 0.24."""
    return [
        _Oracle("P025-FLV-041", "bolted_and_friction_connections", "bolt_bearing_capacity_eq187", "14.2.9 equation (187)", (486.0, 20.0, 12.0, 1.0, 0.9), lambda: 486.0 * 20.0 * 12.0 * 1.0 * 0.9),
        _Oracle("P025-FLV-042", "bolted_and_friction_connections", "bolt_tension_capacity_eq188", "14.2.9 equation (188)", (400.0, 245.0, 0.95), lambda: 400.0 * 245.0 * 0.95),
        _Oracle("P025-FLV-043", "bolted_and_friction_connections", "friction_plane_capacity_eq191", "14.3.3 equation (191)", (400.0, 245.0, 0.35, 1.12), lambda: 400.0 * 245.0 * 0.35 / 1.12),
        _Oracle("P025-FLV-044", "sheet_structures_strength_and_stability", "meridional_stress_eq149", "11.1.2 equation (149)", (1_000_000.0, 2000.0, 10.0, 60.0), lambda: 1_000_000.0 / (2.0 * math.pi * 2000.0 * 10.0 * math.cos(math.radians(60.0)))),
        _Oracle("P025-FLV-045", "sheet_structures_strength_and_stability", "circumferential_stress_eq150", "11.1.2 equation (150)", (1.0, 10.0, 100.0, 2000.0, 2000.0), lambda: (1.0 / 10.0 - 100.0 / 2000.0) * 2000.0),
        _Oracle("P025-FLV-046", "sheet_structures_strength_and_stability", "cylindrical_internal_pressure_stresses_eq151", "11.1.3 equation (151)", (1.0, 1000.0, 10.0), lambda: (1.0 * 1000.0 / (2.0 * 10.0), 1.0 * 1000.0 / 10.0)),
        _Oracle("P025-FLV-047", "sheet_structures_strength_and_stability", "spherical_internal_pressure_stresses_eq152", "11.1.3 equation (152)", (1.0, 1000.0, 10.0), lambda: (50.0, 50.0)),
        _Oracle("P025-FLV-048", "sheet_structures_strength_and_stability", "conical_internal_pressure_stresses_eq153", "11.1.3 equation (153)", (1.0, 1000.0, 10.0, 30.0), lambda: (1.0 * 1000.0 / (2.0 * 10.0 * math.cos(math.radians(30.0))), 1.0 * 1000.0 / (10.0 * math.cos(math.radians(30.0))))),
        _Oracle("P025-FLV-049", "sheet_structures_strength_and_stability", "cylindrical_axial_stability_utilization_eq154", "11.2.1 equation (154)", (100.0, 160.0, 1.0), lambda: 100.0 / 160.0),
        _Oracle("P025-FLV-050", "sheet_structures_strength_and_stability", "cylindrical_external_pressure_utilization_eq159", "11.2.4 equation (159)", (80.0, 160.0, 1.0), lambda: 80.0 / 160.0),
        _Oracle("P025-FLV-051", "sheet_structures_strength_and_stability", "cylindrical_external_pressure_critical_stress_eq160", "11.2.4 equation (160)", (206_000.0, 1000.0, 2000.0, 10.0), lambda: 0.55 * 206_000.0 * (1000.0 / 2000.0) * (10.0 / 1000.0) ** 1.5),
        _Oracle("P025-FLV-052", "sheet_structures_strength_and_stability", "cylindrical_external_pressure_critical_stress_eq161", "11.2.4 equation (161)", (206_000.0, 1000.0, 10.0), lambda: 0.17 * 206_000.0 * (10.0 / 1000.0) ** 2),
        _Oracle("P025-FLV-053", "sheet_structures_strength_and_stability", "cylindrical_combined_stability_utilization_eq162", "11.2.5 equation (162)", (80.0, 160.0, 40.0, 100.0, 1.0), lambda: 80.0 / 160.0 + 40.0 / 100.0),
        _Oracle("P025-FLV-054", "sheet_structures_strength_and_stability", "conical_axial_stability_utilization_eq163", "11.2.6 equation (163)", (400_000.0, 800_000.0, 1.0), lambda: 0.5),
        _Oracle("P025-FLV-055", "sheet_structures_strength_and_stability", "conical_critical_force_eq164", "11.2.6 equation (164)", (10.0, 100.0, 1000.0, 30.0), lambda: 6.28 * 10.0 * 100.0 * 1000.0 * math.cos(math.radians(30.0)) ** 2),
        _Oracle("P025-FLV-056", "sheet_structures_strength_and_stability", "conical_equivalent_radius_eq165", "11.2.6 equation (165)", (500.0, 1000.0, 30.0), lambda: (0.9 * 1000.0 + 0.1 * 500.0) / math.cos(math.radians(30.0))),
        _Oracle("P025-FLV-057", "sheet_structures_strength_and_stability", "conical_external_pressure_utilization_eq166", "11.2.7 equation (166)", (50.0, 100.0, 1.0), lambda: 0.5),
        _Oracle("P025-FLV-058", "sheet_structures_strength_and_stability", "conical_external_pressure_critical_stress_eq167", "11.2.7 equation (167)", (206_000.0, 1000.0, 2000.0, 10.0), lambda: 0.55 * 206_000.0 * (1000.0 / 2000.0) * (10.0 / 1000.0) ** 1.5),
        _Oracle("P025-FLV-059", "sheet_structures_strength_and_stability", "conical_combined_stability_utilization_eq168", "11.2.8 equation (168)", (400_000.0, 800_000.0, 40.0, 100.0, 1.0), lambda: 400_000.0 / 800_000.0 + 40.0 / 100.0),
        _Oracle("P025-FLV-060", "sheet_structures_strength_and_stability", "spherical_external_pressure_utilization_eq169", "11.2.9 equation (169)", (1.0, 1000.0, 10.0, 100.0, 1.0), lambda: (1.0 * 1000.0 / (2.0 * 10.0)) / 100.0),
    ]


def _compare(actual: Any, expected: Any, tolerance: float) -> tuple[bool, float | None]:
    if isinstance(expected, tuple):
        if not isinstance(actual, tuple) or len(actual) != len(expected):
            return False, None
        errors = [abs(float(a) - float(e)) for a, e in zip(actual, expected)]
        passed = all(err <= tolerance * max(1.0, abs(float(e))) for err, e in zip(errors, expected))
        return passed, max(errors, default=0.0)
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        error = abs(float(actual) - float(expected))
        return error <= tolerance * max(1.0, abs(float(expected))), error
    return actual == expected, None


def _run_expanded_oracles() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in _expanded_oracles():
        module = importlib.import_module(f"standard_core.{case.module}")
        function = getattr(module, case.function)
        actual = function(*case.args, **(case.kwargs or {}))
        expected = case.expected()
        passed, error = _compare(actual, expected, case.tolerance)
        results.append(
            {
                "validation_case_id": case.case_id,
                "evidence_class": "independent_source_rederived_closed_form_oracle",
                "function": f"standard_core.{case.module}.{case.function}",
                "standard_reference": case.standard_reference,
                "actual": actual,
                "expected": expected,
                "absolute_error": error,
                "tolerance": case.tolerance,
                "pass_fail": "pass" if passed else "fail",
            }
        )
    return results


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, list):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_tree(item) for key, item in value.items())
    return False


def _validate_golden_case(case: dict[str, Any]) -> None:
    required = {
        "case_id", "source_example", "source_pdf_pages", "source_quantity", "function",
        "args", "kwargs", "published_value", "absolute_tolerance", "units", "notes",
    }
    if set(case) != required:
        missing = sorted(required - set(case))
        unexpected = sorted(set(case) - required)
        raise ValueError(f"golden case keys mismatch; missing={missing}, unexpected={unexpected}")
    if not isinstance(case["case_id"], str) or not case["case_id"].strip():
        raise ValueError("case_id must be a non-empty string")
    function_path = case["function"]
    if not isinstance(function_path, str) or not function_path.startswith("standard_core.") or function_path.count(".") != 2:
        raise ValueError("function must be a canonical standard_core.module.function path")
    if not isinstance(case["args"], list) or not isinstance(case["kwargs"], dict):
        raise ValueError("args/kwargs must be array/object")
    if not _finite_tree(case["args"]) or not _finite_tree(case["kwargs"]):
        raise ValueError("golden case arguments must contain only finite JSON-compatible values")
    value = case["published_value"]
    tolerance = case["absolute_tolerance"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("published_value must be finite")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(float(tolerance)) or float(tolerance) < 0.0:
        raise ValueError("absolute_tolerance must be finite and non-negative")
    pages = case["source_pdf_pages"]
    if not isinstance(pages, list) or not pages or any(isinstance(p, bool) or not isinstance(p, int) or p < 1 for p in pages):
        raise ValueError("source_pdf_pages must contain positive integers")
    for field in ("source_example", "source_quantity", "units"):
        if not isinstance(case[field], str) or not case[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    if not isinstance(case["notes"], str):
        raise ValueError("notes must be a string")


def _run_external_golden(root: Path) -> dict[str, Any]:
    path = root / "data" / "external_scad_benchmarks_v0_25_reconstructed_r1.json"
    payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON constant {token}")))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("external benchmark file must contain a cases array")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in payload["cases"]:
        if not isinstance(case, dict):
            raise ValueError("each external golden case must be an object")
        _validate_golden_case(case)
        if case["case_id"] in seen:
            raise ValueError(f"duplicate golden case_id {case['case_id']}")
        seen.add(case["case_id"])
        _, module_name, function_name = case["function"].split(".")
        module = importlib.import_module(f"standard_core.{module_name}")
        function = getattr(module, function_name)
        actual = function(*case["args"], **case["kwargs"])
        if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
            raise ValueError(f"external golden target {case['function']} did not return a finite scalar")
        error = abs(float(actual) - float(case["published_value"]))
        passed = error <= float(case["absolute_tolerance"])
        results.append(
            {
                "case_id": case["case_id"],
                "evidence_class": "external_vendor_published_cross_implementation",
                "function": case["function"],
                "computed_value": actual,
                "published_value": case["published_value"],
                "absolute_error": error,
                "absolute_tolerance": case["absolute_tolerance"],
                "pass": passed,
                "source_example": case["source_example"],
                "source_pdf_pages": case["source_pdf_pages"],
                "qualification_note": case["notes"],
            }
        )
    return {
        "evidence_class": payload.get("evidence_class"),
        "qualification_warning": payload.get("qualification_warning"),
        "software_certificate": payload.get("software_certificate"),
        "verification_compendium": payload.get("verification_compendium"),
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["pass"]),
        "failed_count": sum(1 for item in results if not item["pass"]),
        "pass": bool(results) and all(item["pass"] for item in results),
        "results": results,
        "coverage_limit": "Vendor-published scalar examples cover only a small subset of the engineering API and do not validate upstream generation of supplied coefficients unless the example explicitly exercises it.",
    }


def _contract_adversarial_probes() -> list[dict[str, Any]]:
    base = {
        "case_id": "X", "source_example": "S", "source_pdf_pages": [1], "source_quantity": "Q",
        "function": "standard_core.axial_members.axial_strength_utilization_yield",
        "args": [1.0, 1.0, 1.0, 1.0], "kwargs": {}, "published_value": 1.0,
        "absolute_tolerance": 0.001, "units": "dimensionless", "notes": "",
    }
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("missing_tolerance", lambda x: x.pop("absolute_tolerance")),
        ("negative_tolerance", lambda x: x.__setitem__("absolute_tolerance", -1.0)),
        ("nan_published_value", lambda x: x.__setitem__("published_value", float("nan"))),
        ("infinite_argument", lambda x: x.__setitem__("args", [float("inf")])),
        ("invalid_function_path", lambda x: x.__setitem__("function", "axial_strength_utilization_yield")),
        ("empty_pages", lambda x: x.__setitem__("source_pdf_pages", [])),
        ("unexpected_field", lambda x: x.__setitem__("unexpected", 1)),
        ("bool_tolerance", lambda x: x.__setitem__("absolute_tolerance", True)),
    ]
    out: list[dict[str, Any]] = []
    for name, mutate in mutations:
        candidate = json.loads(json.dumps(base))
        mutate(candidate)
        rejected = False
        try:
            _validate_golden_case(candidate)
        except (TypeError, ValueError):
            rejected = True
        out.append({"probe": name, "rejected": rejected, "pass_fail": "pass" if rejected else "fail"})
    return out



def _parent_v0_24_engineering_compatibility(root: Path) -> dict[str, Any]:
    parent_path = root / "data" / "api_freeze_v0_24_release_api_hardening_reconstructed_r1.json"
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    current = run_api_hardening(root)["freeze"]
    pmap = {f"{e['module']}.{e['name']}": e for e in parent["entries"] if e.get("api_class") == "engineering"}
    cmap = {f"{e['module']}.{e['name']}": e for e in current["entries"] if e.get("api_class") == "engineering"}
    removed = sorted(set(pmap) - set(cmap))
    added = sorted(set(cmap) - set(pmap))
    changed = []
    for key in sorted(set(pmap) & set(cmap)):
        if pmap[key].get("signature") != cmap[key].get("signature"):
            changed.append({"function": key, "parent_signature": pmap[key].get("signature"), "current_signature": cmap[key].get("signature")})
    return {
        "parent_engineering_function_count": len(pmap),
        "current_engineering_function_count": len(cmap),
        "removed_engineering_functions": removed,
        "added_engineering_functions": added,
        "changed_engineering_signatures": changed,
        "pass": not removed and not added and not changed,
    }

def run_phase_0_25_validation(root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Execute Phase 0.25 independent function-oracle expansion and vendor-published golden cross-implementation validation.

    Standard reference:
        СП 16.13330.2017 clauses 11.1-11.2 and 14.2-14.3 plus published SCAD/KRISTALL verification examples. Audit ID: VALIDATION-025-001.

    Parameters:
        root: Package root containing ``standard_core``, ``data``, tests, and parent validation evidence.

    Returns:
        Structured Phase 0.25 validation report with separated internal, independent closed-form, and external evidence classes.

    Assumptions:
        Published comparator values are treated as external vendor evidence and are not represented as live executions made during this release.

    Sign convention:
        Target functions retain their documented sign conventions; comparator cases are accepted only with explicitly mapped inputs.

    Unit convention:
        Each oracle uses target-function units; external cases record units and explicit conversion notes.

    Applicability:
        Phase 0.25 cumulative reconstructed release based on the Phase 0.24 reconstructed parent.

    Limitations:
        Sixty independently oracled engineering functions and six published scalar comparator cases do not constitute complete validation of the full engineering API.

    Raises:
        FileNotFoundError, ImportError, AttributeError, TypeError, or ValueError when mandatory validation evidence is missing or malformed.

    Examples:
        ``run_phase_0_25_validation('.')['phase_0_25_validation_pass']``

    Tests:
        tests/test_phase_0_25_validation.py

    Implementation notes:
        Evidence classes remain separated so regression agreement cannot be misreported as external validation.
    """
    root_path = Path(root)
    parent = run_function_level_validation(root_path)
    expanded = _run_expanded_oracles()
    external = _run_external_golden(root_path)
    probes = _contract_adversarial_probes()
    parent_api = _parent_v0_24_engineering_compatibility(root_path)
    parent_functions = {
        case["function"] for case in parent["independent_direct_oracles"] if case["pass_fail"] == "pass"
    }
    expanded_functions = {case["function"] for case in expanded if case["pass_fail"] == "pass"}
    combined_functions = parent_functions | expanded_functions
    checks = {
        "parent_phase_0_24_function_level_evidence_passes": parent["function_level_validation_pass"],
        "all_20_new_source_rederived_oracles_pass": len(expanded) == 20 and all(x["pass_fail"] == "pass" for x in expanded),
        "expanded_oracle_functions_do_not_duplicate_parent_scope": not (parent_functions & expanded_functions),
        "at_least_60_distinct_engineering_functions_independently_oracled": len(combined_functions) >= 60,
        "external_vendor_published_golden_cases_pass": external["pass"] and external["case_count"] >= 6,
        "golden_contract_is_fail_closed_under_adversarial_probes": all(x["pass_fail"] == "pass" for x in probes),
        "engineering_api_is_call_shape_identical_to_v0_24_parent": parent_api["pass"],
        "engineering_use_ready_remains_false": ENGINEERING_USE_READY is False,
    }
    engineering_count = int(parent["engineering_public_function_count"])
    return {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_qualification": RELEASE_QUALIFICATION,
        "parent_release": PARENT_RELEASE,
        "standard": STANDARD_TITLE,
        "engineering_use_ready": ENGINEERING_USE_READY,
        "engineering_public_function_count": engineering_count,
        "phase_0_24_parent_oracle_case_count": parent["independent_direct_function_oracle_case_count"],
        "phase_0_25_added_oracle_case_count": len(expanded),
        "combined_independently_oracled_function_count": len(combined_functions),
        "combined_independent_function_oracle_fraction": len(combined_functions) / engineering_count,
        "independent_public_function_validation_complete": len(combined_functions) == engineering_count,
        "external_cross_implementation_case_count": external["case_count"],
        "externally_compared_distinct_function_count": len({x["function"] for x in external["results"]}),
        "external_independent_validation_complete": False,
        "evidence_taxonomy": {
            "parent_independent_direct_function_oracle": "separately written closed-form expected value from Phase 0.24",
            "independent_source_rederived_closed_form_oracle": "new Phase 0.25 expected value re-derived from the normative formula without calling a production helper",
            "external_vendor_published_cross_implementation": "comparison against a numerical value published in an external vendor verification example; not a live vendor run",
            "contract_adversarial_probe": "negative test proving malformed/non-finite comparator evidence is rejected",
        },
        "checks": checks,
        "phase_0_25_validation_pass": all(checks.values()),
        "expanded_independent_oracles": expanded,
        "external_golden_validation": external,
        "parent_v0_24_engineering_api_compatibility": parent_api,
        "golden_contract_adversarial_probes": probes,
        "open_gaps": {
            "engineering_functions_without_independent_direct_oracle": engineering_count - len(combined_functions),
            "engineering_functions_without_external_cross_implementation_case": engineering_count - len({x["function"] for x in external["results"]}),
            "annex_tables_remaining_external_reference_required": 24,
            "live_vendor_replay_performed": False,
            "full_external_validation_complete": False,
        },
    }


def write_phase_0_25_validation_reports(report: dict[str, Any], root: str | Path) -> None:
    """
    Summary:
        Materialize deterministic JSON and Markdown evidence for Phase 0.25 validation.

    Standard reference:
        СП 16.13330.2017 release-validation evidence. Audit ID: VALIDATION-025-002.

    Parameters:
        report: Result returned by :func:`run_phase_0_25_validation`.
        root: Package root receiving reports and comparison artifacts.

    Returns:
        None; deterministic evidence files are written below ``reports``.

    Assumptions:
        The report was produced from the same source tree and benchmark corpus being packaged.

    Sign convention:
        Not applicable to serialization.

    Unit convention:
        Numeric comparator units remain recorded per benchmark case.

    Applicability:
        Phase 0.25 cumulative reconstructed release.

    Limitations:
        Serialization does not strengthen the evidentiary class of the underlying comparisons.

    Raises:
        OSError, TypeError, or ValueError if deterministic standards-compliant JSON cannot be written.

    Examples:
        ``write_phase_0_25_validation_reports(run_phase_0_25_validation('.'), '.')``

    Tests:
        tests/test_phase_0_25_validation.py

    Implementation notes:
        JSON emission uses ``allow_nan=False`` and the Markdown report explicitly preserves validation limitations.
    """
    root_path = Path(root)
    reports = root_path / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "phase_0_25_validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (reports / "external_scad_benchmark_comparison_v0_25_reconstructed_r1.json").write_text(
        json.dumps(report["external_golden_validation"], ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Phase 0.25 — Independent Function Oracle Expansion & Golden Cross-Implementation Validation",
        "",
        f"- Verdict: **{'PASS' if report['phase_0_25_validation_pass'] else 'FAIL'}**",
        f"- Engineering public functions: **{report['engineering_public_function_count']}**",
        f"- Independent direct-oracle functions: **{report['combined_independently_oracled_function_count']}**",
        f"- New Phase 0.25 source-rederived oracles: **{report['phase_0_25_added_oracle_case_count']}**",
        f"- External vendor-published cases: **{report['external_cross_implementation_case_count']}**",
        f"- Distinct externally compared functions: **{report['externally_compared_distinct_function_count']}**",
        f"- Engineering-use ready: **{'yes' if report['engineering_use_ready'] else 'no'}**",
        "",
        "External comparator cases reproduce values published in the SCAD Office/KRISTALL verification material. They are not represented as live SCAD runs performed during this release.",
        "",
        "Complete independent function-level and external cross-implementation validation remain open release gaps.",
    ]
    (reports / "phase_0_25_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
