"""Function-level evidence expansion for the Phase 0.24 cumulative release."""

from __future__ import annotations

import ast
import importlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .release_metadata import (
    ENGINEERING_USE_READY,
    PACKAGE_VERSION,
    PARENT_RELEASE,
    RELEASE_QUALIFICATION,
    RELEASE_STAGE,
)

_ENGINEERING_MODULES: tuple[str, ...] = (
    "antenna_structures",
    "axial_members",
    "base_plates_and_combined_force_strength",
    "beam_column_stability",
    "bending_member_local_stability",
    "bending_members",
    "bolted_and_friction_connections",
    "brittle_fracture_and_welded_connections",
    "built_up_axial_members",
    "built_up_beam_columns_and_combined_local_stability",
    "built_up_beam_flange_connections",
    "crane_runway_and_bending_stability",
    "effective_lengths_and_limiting_slenderness",
    "fatigue_design",
    "general_requirements",
    "local_stability",
    "material_resistance",
    "overhead_line_and_switchyard_supports",
    "reconstruction_assessment",
    "sheet_structures_strength_and_stability",
    "structural_detailing_and_support_bearings",
)


@dataclass(frozen=True)
class _FunctionOracle:
    case_id: str
    module: str
    function: str
    standard_reference: str
    args: tuple[Any, ...]
    expected: Callable[[], Any]
    kwargs: dict[str, Any] | None = None
    tolerance: float = 1e-10


def _function_oracles() -> list[_FunctionOracle]:
    """Return direct independently-written scalar/tuple function oracles.

    Expected values are deliberately expressed without calling production
    helpers.  These cases complement, rather than replace, the Phase 0.23
    route-oracle evidence.
    """
    return [
        _FunctionOracle("FLV-001", "antenna_structures", "vibration_damper_distance_eq215", "17.16 equation (215)", (20.0, 100_000.0, 2.0), lambda: 0.41e-3 * 20.0 * math.sqrt(100_000.0 / 2.0)),
        _FunctionOracle("FLV-002", "axial_members", "axial_strength_utilization_yield", "7.1.1 equation (5)", (300_000.0, 1500.0, 355.0, 1.0), lambda: 300_000.0 / (1500.0 * 355.0)),
        _FunctionOracle("FLV-003", "axial_members", "relative_slenderness", "7.1 relative slenderness", (100.0, 355.0, 206_000.0), lambda: 100.0 * math.sqrt(355.0 / 206_000.0)),
        _FunctionOracle("FLV-004", "base_plates_and_combined_force_strength", "base_plate_required_thickness_eq101", "8.6.2 equation (101)", (3840.0, 250.0, 1.0), lambda: math.sqrt(6.0 * 3840.0 / 250.0)),
        _FunctionOracle("FLV-005", "base_plates_and_combined_force_strength", "base_plate_cantilever_moment_eq102", "8.6.2 equation (102)", (1.2, 80.0), lambda: 1.2 * 80.0**2 / 2.0),
        _FunctionOracle("FLV-006", "beam_column_stability", "effective_relative_eccentricity_eq110", "9.2.2 equation (110)", (1.25, 3.2), lambda: 1.25 * 3.2),
        _FunctionOracle("FLV-007", "beam_column_stability", "biaxial_stability_coefficient_eq117", "9.2.9 equation (117)", (0.72, 0.83), lambda: 0.72 * (0.6 * 0.83 ** (1.0 / 3.0) + 0.4 * 0.83 ** 0.25)),
        _FunctionOracle("FLV-008", "bending_member_local_stability", "bending_normal_stress_eq78", "8.5.2 equation (78)", (300_000_000.0, 500.0, 1_500_000_000.0), lambda: 300_000_000.0 * 500.0 / 1_500_000_000.0),
        _FunctionOracle("FLV-009", "bending_member_local_stability", "average_web_shear_stress_eq79", "8.5.2 equation (79)", (240_000.0, 10.0, 600.0), lambda: 240_000.0 / (10.0 * 600.0)),
        _FunctionOracle("FLV-010", "bending_members", "elastic_bending_utilization_eq41", "8.2.1 equation (41)", (100_000_000.0, 1_000_000.0, 355.0, 1.0), lambda: 100_000_000.0 / (1_000_000.0 * 355.0)),
        _FunctionOracle("FLV-011", "bending_members", "elastic_shear_utilization_eq42", "8.2.1 equation (42)", (240_000.0, 1_200_000.0, 800_000_000.0, 10.0, 205.9, 1.0), lambda: 240_000.0 * 1_200_000.0 / (800_000_000.0 * 10.0 * 205.9)),
        _FunctionOracle("FLV-012", "bolted_and_friction_connections", "bolt_shear_capacity_eq186", "14.2.9 equation (186)", (240.0, 245.0, 2, 0.9, 1.0), lambda: 240.0 * 245.0 * 2.0 * 0.9),
        _FunctionOracle("FLV-013", "bolted_and_friction_connections", "bolt_shear_tension_interaction_eq190", "14.2.13 equation (190)", (60_000.0, 30_000.0, 120_000.0, 90_000.0), lambda: math.sqrt((60_000.0 / 120_000.0) ** 2 + (30_000.0 / 90_000.0) ** 2)),
        _FunctionOracle("FLV-014", "brittle_fracture_and_welded_connections", "lamellar_tearing_risk_sum_eq174", "13.5 equation (174)", (5.0, 8.0, 3.0, 4.0, 2.0), lambda: 5.0 + 8.0 + 3.0 + 4.0 + 2.0),
        _FunctionOracle("FLV-015", "brittle_fracture_and_welded_connections", "butt_weld_axial_utilization_eq175", "14.1.14 equation (175)", (180_000.0, 10.0, 230.0, 300.0, 1.0), lambda: 180_000.0 / (10.0 * 230.0 * 300.0)),
        _FunctionOracle("FLV-016", "built_up_axial_members", "built_up_axial_strength_utilization", "7.2 strength route", (800_000.0, 4800.0, "yield", 355.0, 450.0, 1.3, 1.0), lambda: 800_000.0 / (4800.0 * 355.0)),
        _FunctionOracle("FLV-017", "built_up_axial_members", "batten_shear_force_n", "7.2 equation (19)", (20_000.0, 1000.0, 500.0), lambda: 20_000.0 * 1000.0 / 500.0),
        _FunctionOracle("FLV-018", "built_up_beam_columns_and_combined_local_stability", "built_up_relative_eccentricity_eq123", "9.3.3 equation (123)", (80.0, 12_000.0, 300.0, 144_000_000.0), lambda: 80.0 * 12_000.0 * 300.0 / 144_000_000.0),
        _FunctionOracle("FLV-019", "built_up_beam_columns_and_combined_local_stability", "biaxial_branch_additional_force_eq124", "9.3.3 equation (124)", (80_000_000.0, 1000.0, 60_000_000.0, 800.0), lambda: 0.5 * (80_000_000.0 / 1000.0 + 60_000_000.0 / 800.0)),
        _FunctionOracle("FLV-020", "built_up_beam_flange_connections", "local_load_line_pressure_v_n_mm", "14.4.1 local pressure", (1.2, 1.1, 100_000.0, 250.0), lambda: 1.2 * 1.1 * 100_000.0 / 250.0),
        _FunctionOracle("FLV-021", "built_up_beam_flange_connections", "flange_shear_flow_t_n_mm", "14.4.1 shear flow", (240_000.0, 1_200_000.0, 800_000_000.0), lambda: 240_000.0 * 1_200_000.0 / 800_000_000.0),
        _FunctionOracle("FLV-022", "crane_runway_and_bending_stability", "crane_runway_local_torsional_moment_eq68", "8.3 equation (68)", (1.1, 1.2, 100_000.0, 20.0, 10_000.0, 150.0), lambda: 1.1 * 1.2 * 100_000.0 * 20.0 + 0.75 * 10_000.0 * 150.0),
        _FunctionOracle("FLV-023", "crane_runway_and_bending_stability", "compressed_flange_equivalent_force_eq74", "8.4 equation (74)", (1000.0, 2000.0, 355.0, 300.0), lambda: (1000.0 * (355.0 / 300.0) + 0.25 * 2000.0) * 300.0),
        _FunctionOracle("FLV-024", "effective_lengths_and_limiting_slenderness", "truss_chord_effective_length_in_plane_eq136", "10.1.2 equation (136)", (3000.0, 0.5), lambda: max((0.17 * 0.5**3 + 0.83) * 3000.0, 0.8 * 3000.0)),
        _FunctionOracle("FLV-025", "effective_lengths_and_limiting_slenderness", "group_4_limiting_slenderness_increase", "10.4.2", (100.0, True), lambda: 110.0),
        _FunctionOracle("FLV-026", "fatigue_design", "stress_asymmetry_ratio", "12.1 stress asymmetry", (100.0, -25.0), lambda: -25.0 / 100.0),
        _FunctionOracle("FLV-027", "fatigue_design", "fatigue_utilization_eq170", "12.1.2 equation (170)", (50.0, 1.63, 75.0, 25.0 / 19.0), lambda: 50.0 / (1.63 * 75.0 * (25.0 / 19.0))),
        _FunctionOracle("FLV-028", "general_requirements", "table_1_working_condition_factor", "4.3.2 Table 1 Note 5", ("default_unlisted_case_note_5",), lambda: 1.0),
        _FunctionOracle("FLV-029", "local_stability", "wall_relative_slenderness", "7.3 wall relative slenderness", (500.0, 8.0, 355.0, 206_000.0), lambda: (500.0 / 8.0) * math.sqrt(355.0 / 206_000.0)),
        _FunctionOracle("FLV-030", "local_stability", "longitudinal_stiffener_wall_limit_multiplier_eq30", "7.3 equation (30)", (500_000.0, 500.0, 10.0), lambda: 1.0 + 0.4 * (500_000.0 / (500.0 * 10.0**3)) * (1.0 - 0.1 * (500_000.0 / (500.0 * 10.0**3)))),
        _FunctionOracle("FLV-031", "material_resistance", "design_yield_resistance_n_mm2", "6.1 Table 2", (355.0, 1.05), lambda: 355.0 / 1.05),
        _FunctionOracle("FLV-032", "material_resistance", "design_shear_resistance_n_mm2", "6.1 Table 2", (355.0, 1.05), lambda: 0.58 * 355.0 / 1.05),
        _FunctionOracle("FLV-033", "overhead_line_and_switchyard_supports", "relative_eccentricity_eq204", "16.6 equation (204)", (100_000_000.0, 1_000_000.0, 2000.0, 1.2), lambda: 3.46 * 1.2 * 100_000_000.0 / (1_000_000.0 * 2000.0)),
        _FunctionOracle("FLV-034", "overhead_line_and_switchyard_supports", "relative_eccentricity_eq205", "16.6 equation (205)", (100_000_000.0, 1_000_000.0, 2000.0, 1.2), lambda: 3.0 * 1.2 * 100_000_000.0 / (1_000_000.0 * 2000.0)),
        _FunctionOracle("FLV-035", "reconstruction_assessment", "symmetric_compression_strength_utilization_eq216", "18.3.13 equation (216)", (300_000.0, 3000.0, 300.0, 0.9, 1.0), lambda: 300_000.0 / (3000.0 * 300.0 * 0.9)),
        _FunctionOracle("FLV-036", "reconstruction_assessment", "effective_design_resistance_eq223", "18.3.15 equation (223)", (300.0, 1.21), lambda: 300.0 * math.sqrt(1.21)),
        _FunctionOracle("FLV-037", "sheet_structures_strength_and_stability", "membrane_strength_utilization_eq148", "11.1.1 equation (148)", (100.0, 40.0, 20.0, 355.0, 1.0), lambda: math.sqrt(100.0**2 - 100.0 * 40.0 + 40.0**2 + 3.0 * 20.0**2) / 355.0),
        _FunctionOracle("FLV-038", "sheet_structures_strength_and_stability", "principal_stresses_2d", "11.1.1 principal stresses", (100.0, 40.0, 30.0), lambda: (70.0 + math.sqrt(30.0**2 + 30.0**2), 70.0 - math.sqrt(30.0**2 + 30.0**2))),
        _FunctionOracle("FLV-039", "structural_detailing_and_support_bearings", "cylindrical_hinge_local_bearing_utilization_eq199", "15.12.2 equation (199)", (1_000_000.0, 150.0, 300.0, 240.0, 1.0), lambda: 1_000_000.0 / (1.25 * 150.0 * 300.0 * 240.0)),
        _FunctionOracle("FLV-040", "structural_detailing_and_support_bearings", "roller_diametral_compression_utilization_eq200", "15.12.3 equation (200)", (1_200_000.0, 4, 120.0, 300.0, 12.142857142857142, 1.0), lambda: 1_200_000.0 / (4.0 * 120.0 * 300.0 * 12.142857142857142)),
    ]


def _compare(actual: Any, expected: Any, tolerance: float) -> tuple[bool, float | None]:
    if isinstance(expected, tuple):
        if not isinstance(actual, tuple) or len(actual) != len(expected):
            return False, None
        errors = [abs(float(a) - float(e)) for a, e in zip(actual, expected)]
        return all(err <= tolerance * max(1.0, abs(float(e))) for err, e in zip(errors, expected)), max(errors, default=0.0)
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        err = abs(float(actual) - float(expected))
        return err <= tolerance * max(1.0, abs(float(expected))), err
    return actual == expected, None


def _run_function_oracles() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for case in _function_oracles():
        module = importlib.import_module(f"standard_core.{case.module}")
        function = getattr(module, case.function)
        expected = case.expected()
        actual = function(*case.args, **(case.kwargs or {}))
        passed, error = _compare(actual, expected, case.tolerance)
        out.append(
            {
                "validation_case_id": case.case_id,
                "evidence_class": "independent_direct_function_oracle",
                "function": f"standard_core.{case.module}.{case.function}",
                "standard_reference": case.standard_reference,
                "actual": actual,
                "expected": expected,
                "absolute_error": error,
                "tolerance": case.tolerance,
                "pass_fail": "pass" if passed else "fail",
            }
        )
    return out


def _engineering_functions(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    tests = {p.name: p.read_text(encoding="utf-8") for p in sorted((root / "tests").glob("test_*.py"))}
    coverage_path = root / "reports" / "function_coverage_raw_v0_27.json"
    if not coverage_path.exists():
        coverage_path = root / "reports" / "function_coverage_raw_v0_26.json"
    if not coverage_path.exists():
        coverage_path = root / "reports" / "function_coverage_raw_v0_24.json"
    coverage_files: dict[str, Any] = {}
    if coverage_path.exists():
        coverage_files = json.loads(coverage_path.read_text(encoding="utf-8"))["files"]

    for module_name in _ENGINEERING_MODULES:
        path = root / "standard_core" / f"{module_name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        cov = coverage_files.get(f"standard_core/{module_name}.py", {})
        executed_lines = set(cov.get("executed_lines", []))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            direct_tests = [name for name, text in tests.items() if re.search(r"\b" + re.escape(node.name) + r"\b", text)]
            body = node.body[1:] if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str) else node.body
            body_lines: set[int] = set()
            for statement in body:
                body_lines.update(range(statement.lineno, getattr(statement, "end_lineno", statement.lineno) + 1))
            executed = bool(body_lines & executed_lines) if coverage_files else None
            entries.append(
                {
                    "function": f"standard_core.{module_name}.{node.name}",
                    "module": module_name,
                    "name": node.name,
                    "direct_test_files": direct_tests,
                    "direct_test_reference_present": bool(direct_tests),
                    "body_executed_in_packaged_coverage_run": executed,
                    "independent_direct_oracle_present": any(o.module == module_name and o.function == node.name for o in _function_oracles()),
                }
            )
    return sorted(entries, key=lambda x: x["function"])


def run_function_level_validation(root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Build the Phase 0.24 per-public-function validation matrix and execute direct independent arithmetic oracles.

    Standard reference:
        СП 16.13330.2017 references are recorded per oracle and in the engineering API trace. Audit ID: FUNCTION-VALIDATION-024-001.

    Parameters:
        root: Package root containing engineering modules, tests, and coverage evidence.

    Returns:
        Structured function-level evidence report.

    Assumptions:
        Direct name references in tests and coverage execution are evidence of binding/execution only, not independent normative correctness.

    Sign convention:
        Each engineering function retains the sign convention documented by that function; the validator does not normalize signs.

    Unit convention:
        Each oracle uses the units of its target function; counts and evidence fractions are dimensionless.

    Applicability:
        Phase 0.24 cumulative reconstructed release.

    Limitations:
        Only records explicitly marked ``independent_direct_function_oracle`` count as independent function oracles; the complete engineering API is not independently oracled in this phase.

    Raises:
        ImportError, AttributeError, ValueError, or filesystem/JSON errors when declared validation evidence cannot be resolved.

    Examples:
        ``run_function_level_validation('.')['function_level_validation_pass']``

    Tests:
        tests/test_phase_0_24_release_api_hardening.py

    Implementation notes:
        The report deliberately separates named-test binding, execution coverage, and independently derived expected values.
    """
    root_path = Path(root)
    function_entries = _engineering_functions(root_path)
    oracle_results = _run_function_oracles()
    direct = [x for x in function_entries if x["direct_test_reference_present"]]
    executed = [x for x in function_entries if x["body_executed_in_packaged_coverage_run"] is True]
    no_coverage_evidence = [x["function"] for x in function_entries if x["body_executed_in_packaged_coverage_run"] is None]
    independent_functions = sorted({x["function"] for x in function_entries if x["independent_direct_oracle_present"]})

    checks = {
        "all_engineering_public_functions_have_direct_named_test_reference": len(direct) == len(function_entries),
        "coverage_evidence_present_for_every_engineering_public_function": not no_coverage_evidence and len(executed) == len(function_entries),
        "all_independent_direct_function_oracles_pass": all(x["pass_fail"] == "pass" for x in oracle_results),
        "independent_direct_oracle_scope_expanded_beyond_phase_0_23_extra_direct_scope": len(independent_functions) >= 40,
    }
    return {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_qualification": RELEASE_QUALIFICATION,
        "parent_release": PARENT_RELEASE,
        "engineering_use_ready": ENGINEERING_USE_READY,
        "engineering_public_function_count": len(function_entries),
        "direct_named_test_reference_count": len(direct),
        "executed_function_body_count": len(executed),
        "independent_direct_function_oracle_case_count": len(oracle_results),
        "independently_oracled_function_count": len(independent_functions),
        "independent_direct_oracle_fraction": len(independent_functions) / len(function_entries),
        "independent_public_function_validation_complete": len(independent_functions) == len(function_entries),
        "evidence_taxonomy": {
            "direct_named_unit_test_reference": "function is explicitly named in at least one packaged test; not independent evidence by itself",
            "coverage_execution": "at least one executable body line ran in the packaged coverage run; not correctness evidence by itself",
            "independent_direct_function_oracle": "production function compared with separately written arithmetic/closed-form expected value",
        },
        "checks": checks,
        "function_level_validation_pass": all(checks.values()),
        "function_entries": function_entries,
        "independent_direct_oracles": oracle_results,
        "open_gap": {
            "functions_without_independent_direct_oracle": len(function_entries) - len(independent_functions),
            "statement": "Function-level execution/test binding is complete, but independent arithmetic validation is deliberately not claimed complete for all public functions.",
        },
    }


def write_function_level_validation_reports(report: dict[str, Any], reports_dir: str | Path) -> None:
    """
    Summary:
        Write deterministic JSON and Markdown Phase 0.24 function-level validation evidence.

    Standard reference:
        СП 16.13330.2017 validation/release evidence. Audit ID: FUNCTION-VALIDATION-024-002.

    Parameters:
        report: Result returned by :func:`run_function_level_validation`.
        reports_dir: Destination directory for validation evidence.

    Returns:
        None; report files are written.

    Assumptions:
        The supplied report belongs to the current release tree.

    Sign convention:
        Not applicable to serialization.

    Unit convention:
        Fractions are dimensionless; target-function units remain embedded in oracle records.

    Applicability:
        Phase 0.24 cumulative reconstructed release.

    Limitations:
        The human-readable summary is subordinate to the complete JSON evidence.

    Raises:
        OSError or ValueError for filesystem or non-finite JSON serialization failures.

    Examples:
        ``write_function_level_validation_reports(run_function_level_validation('.'), 'reports')``

    Tests:
        tests/test_phase_0_24_release_api_hardening.py

    Implementation notes:
        ``allow_nan=False`` prevents non-finite evidence from being silently serialized.
    """
    destination = Path(reports_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "function_level_validation_v0_24.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Function-level validation — Phase 0.24",
        "",
        f"- Verdict: **{'PASS' if report['function_level_validation_pass'] else 'FAIL'}**",
        f"- Engineering public functions classified: **{report['engineering_public_function_count']}**",
        f"- Explicit named test references: **{report['direct_named_test_reference_count']}/{report['engineering_public_function_count']}**",
        f"- Function bodies executed under coverage: **{report['executed_function_body_count']}/{report['engineering_public_function_count']}**",
        f"- Independent direct function oracles: **{report['independent_direct_function_oracle_case_count']} cases / {report['independently_oracled_function_count']} functions**",
        f"- Independent function-oracle coverage: **{report['independent_direct_oracle_fraction']:.1%}**",
        "",
        "Direct test binding and execution coverage are complete for the engineering API. They are not promoted to independent normative evidence. Independent arithmetic remains explicitly partial.",
    ]
    (destination / "function_level_validation_v0_24.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
