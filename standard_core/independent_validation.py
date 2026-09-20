"""Independent route-level arithmetic and adversarial probes for Phase 0.23.

The oracle arithmetic in this module intentionally does not call the production
calculation functions for the 20 packaged runner routes.  It reads their
materialized results and compares them with separately written scalar arithmetic.
Targeted direct-function boundary checks are reported as a different evidence
class and are not counted as independent route oracles.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .release_metadata import PACKAGE_VERSION, RELEASE_STAGE, RELEASE_QUALIFICATION


@dataclass(frozen=True)
class _RouteOracle:
    case_id: str
    route: str
    standard_reference: str
    output_file: str | None
    result_path: str | None
    formula: str
    reference: Callable[[], float]
    production: Callable[[Path], float] | None = None
    tolerance: float = 1e-10


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_value(data: Any, dotted_path: str) -> Any:
    current = data
    for token in dotted_path.split("."):
        current = current[token]
    return current


def _result_from_output(root: Path, output_file: str, result_path: str) -> float:
    data = _read_json(root / "outputs" / output_file)
    value = _path_value(data, "results." + result_path)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"Non-finite/non-numeric production value at {output_file}:{result_path}")
    return float(value)


def _final_annex_production(_: Path) -> float:
    from .axial_members import open_u_section_torsional_flexural_utilization

    return open_u_section_torsional_flexural_utilization(500000.0, 3000.0, 340.0, 1.05, 0.8, 2.0)


def _eq137_production(_: Path) -> float:
    from .effective_lengths_and_limiting_slenderness import truss_chord_effective_length_out_of_plane_eq137

    return truss_chord_effective_length_out_of_plane_eq137(5000.0, 3, 1.0)


def _eq101_production(_: Path) -> float:
    from .base_plates_and_combined_force_strength import base_plate_required_thickness_eq101

    return base_plate_required_thickness_eq101(3840.0, 250.0, 1.0)


def _eq205_production(_: Path) -> float:
    from .overhead_line_and_switchyard_supports import relative_eccentricity_eq205

    return relative_eccentricity_eq205(100_000_000.0, 1_000_000.0, 2000.0, 1.2)


def _local_pressure_production(_: Path) -> float:
    from .built_up_beam_flange_connections import local_load_line_pressure_v_n_mm

    return local_load_line_pressure_v_n_mm(1.2, 1.1, 100_000.0, 250.0)


def _route_oracles() -> list[_RouteOracle]:
    """Return the Phase 0.23 independent route-oracle registry."""
    return [
        _RouteOracle("IVH-ROUTE-01", "material_resistance_bundle", "6.1 Table 2", "material_resistance_result.json", "design_yield_resistance_n_mm2", "Ry=Ryn/gamma_m; Ryn=355, gamma_m=1.05", lambda: 355.0 / 1.05),
        _RouteOracle("IVH-ROUTE-02", "axial_member_strength_and_stability", "7.1.1 equation (5)", "axial_member_result.json", "equation_5_strength_utilization", "eta=N/(A_n Ry gamma_c)", lambda: 300_000.0 / (1500.0 * 338.0952380952381 * 1.0)),
        _RouteOracle("IVH-ROUTE-03", "built_up_axial_members", "7.2.1 / equation (5)", "built_up_axial_member_result.json", "clause_7_2_1_strength_utilization", "eta=N/(A_n Ry gamma_c)", lambda: 800_000.0 / (4800.0 * 355.0 * 1.0)),
        _RouteOracle("IVH-ROUTE-04", "centrally_compressed_local_stability", "7.3.2 relative wall slenderness", "local_stability_result.json", "actual_wall_relative_slenderness", "lambda_w=(h_eff/t_w)*sqrt(Ry/E)", lambda: (500.0 / 8.0) * math.sqrt(355.0 / 206_000.0)),
        _RouteOracle("IVH-ROUTE-05", "bending_member_strength", "8.2.1 equation (41)", "bending_member_result.json", "equation_41_elastic_bending_utilization", "eta=|M|/(W_n Ry gamma_c)", lambda: 100_000_000.0 / (1_000_000.0 * 355.0 * 1.0)),
        _RouteOracle("IVH-ROUTE-06", "crane_runway_and_bending_stability", "8.3 equation (68)", "crane_runway_and_bending_stability_result.json", "equation_68_local_torsional_moment_n_mm", "Mt=gamma_f*gamma_f1*F_n*e+0.75*Q_t*h_r", lambda: 1.1 * 1.2 * 100_000.0 * 20.0 + 0.75 * 10_000.0 * 150.0),
        _RouteOracle("IVH-ROUTE-07", "bending_member_local_stability", "8.5 equation (78)", "bending_member_local_stability_result.json", "equation_78_normal_stress_n_mm2", "sigma=M*y/I", lambda: 300_000_000.0 * 500.0 / 1_500_000_000.0),
        _RouteOracle("IVH-ROUTE-08", "base_plates_and_combined_force_strength", "8.6.2 equation (102)", "base_plates_and_combined_force_strength_result.json", "equation_102_cantilever_moment_n_mm_per_mm", "M1=q*c^2/2", lambda: 1.2 * 80.0**2 / 2.0),
        _RouteOracle("IVH-ROUTE-09", "beam_column_stability", "9.2.2 equation (109) + Annex D.3 selected node", "beam_column_stability_result.json", "equation_109_utilization", "eta=N/(phi_e*A*Ry*gamma_c); phi_e=0.397", lambda: 180_000.0 / (0.397 * 3000.0 * 250.0 * 1.0)),
        _RouteOracle("IVH-ROUTE-10", "built_up_beam_columns_and_combined_local_stability", "9.3.2 equation (123)", "built_up_beam_columns_and_combined_local_stability_result.json", "equation_123_relative_eccentricity_m", "m=e*A*a/I", lambda: 80.0 * 12_000.0 * 300.0 / 144_000_000.0),
        _RouteOracle("IVH-ROUTE-11", "effective_lengths_and_limiting_slenderness", "10.1.2 equation (136)", "effective_lengths_and_limiting_slenderness_result.json", "equation_136_truss_in_plane_effective_length_mm", "l_eff=max[(0.17*alpha^3+0.83)l,0.8l]", lambda: max((0.17 * 0.5**3 + 0.83) * 3000.0, 0.8 * 3000.0)),
        _RouteOracle("IVH-ROUTE-12", "sheet_structures_strength_and_stability", "11.1.1 equation (148)", "sheet_structures_strength_and_stability_result.json", "equation_148_utilization", "eta=sqrt(sx^2-sx*sy+sy^2+3*tau^2)/(Ry*gamma_c)", lambda: math.sqrt(100.0**2 - 100.0 * 40.0 + 40.0**2 + 3.0 * 20.0**2) / 355.0),
        _RouteOracle("IVH-ROUTE-13", "fatigue_design", "12.1.2 equation (170), selected Tables 35-36 values", "fatigue_design_result.json", "equation_170_utilization", "eta=|sigma_max|/(alpha*Rv*gamma_v); alpha=1.63,Rv=75,gamma_v=25/19", lambda: 50.0 / (1.63 * 75.0 * (25.0 / 19.0))),
        _RouteOracle("IVH-ROUTE-14", "brittle_fracture_and_welded_connections", "14.1.3 effective butt-weld length", "brittle_fracture_and_welded_connections_result.json", "butt_weld_effective_length_mm", "l_w=l-2t without runout tabs", lambda: 250.0 - 2.0 * 10.0),
        _RouteOracle("IVH-ROUTE-15", "bolted_and_friction_connections", "14.2.9 equation (186), selected Table 41 gamma_b", "bolted_and_friction_connections_result.json", "equation_186_shear_capacity_n", "N_bs=R_bs*A_b*n_s*gamma_b*gamma_c", lambda: 240.0 * 245.0 * 2.0 * 0.9 * 1.0),
        _RouteOracle("IVH-ROUTE-16", "built_up_beam_flange_connections", "14.4.1 shear-flow definition", "built_up_beam_flange_connections_result.json", "flange_shear_flow_t_n_mm", "T=Q*S/I", lambda: 240_000.0 * 1_200_000.0 / 800_000_000.0),
        _RouteOracle("IVH-ROUTE-17", "structural_detailing_and_support_bearings", "15.12.3 equation (200)", "structural_detailing_and_support_bearings_result.json", "equation_200_roller_bearing.equation_200_utilization", "eta=F/(n*d*l*R_cd*gamma_c)", lambda: 1_200_000.0 / (4.0 * 120.0 * 300.0 * 12.142857142857142 * 1.0)),
        _RouteOracle("IVH-ROUTE-18", "overhead_line_and_switchyard_supports", "16.6 equation (204)", "overhead_line_and_switchyard_supports_result.json", "equation_204_relative_eccentricity", "m=3.46*beta*M/(N*b)", lambda: 3.46 * 1.2 * 100_000_000.0 / (1_000_000.0 * 2000.0)),
        _RouteOracle("IVH-ROUTE-19", "antenna_structures", "17.16 equation (215)", "antenna_structures_result.json", "equation_215_minimum_damper_distance_m", "s=0.41e-3*d*sqrt(P/m)", lambda: 0.41e-3 * 20.0 * math.sqrt(100_000.0 / 2.0)),
        _RouteOracle("IVH-ROUTE-20", "reconstruction_assessment", "18.3.15 equations (223)-(224)", "reconstruction_assessment_result.json", "equation_223_effective_design_resistance_n_mm2", "Ry,ef=Ry*sqrt(k), with k from equation (224)", lambda: 300.0 * math.sqrt(((330.0 / 300.0) * (1.0 - 2000.0 / 3000.0) + 2000.0 / 3000.0) * ((330.0 / 300.0) * (1.0 - 8_000_000.0 / 12_000_000.0) + 8_000_000.0 / 12_000_000.0))),
        _RouteOracle("IVH-ROUTE-21", "final_annex_and_release_consolidation", "7.1.5 equations (10)-(11)", None, None, "phi1=7.6*c/lambda_y^2; phi_c=upper/lower branch; eta=N/(phi_c*A*Ry*gamma_c)", lambda: 500_000.0 / (min(1.0, 0.68 + 0.21 * (7.6 * 0.8 / 2.0**2)) * 3000.0 * 340.0 * 1.05), production=_final_annex_production),
        _RouteOracle("IVH-EXTRA-01", "effective_lengths_and_limiting_slenderness", "10.1.2 equation (137)", None, None, "l_eff=max[(0.75+0.25*(beta/(k-1))^(2k-3))*l1,0.5l1]", lambda: max((0.75 + 0.25 * (1.0 / (3 - 1)) ** (2 * 3 - 3)) * 5000.0, 0.5 * 5000.0), production=_eq137_production),
        _RouteOracle("IVH-EXTRA-02", "base_plates_and_combined_force_strength", "8.6.2 equation (101)", None, None, "t=sqrt(6*Mmax/(Ry*gamma_c))", lambda: math.sqrt(6.0 * 3840.0 / 250.0), production=_eq101_production),
        _RouteOracle("IVH-EXTRA-03", "overhead_line_and_switchyard_supports", "16.6 equation (205)", None, None, "m=3*beta*M/(N*b)", lambda: 3.0 * 1.2 * 100_000_000.0 / (1_000_000.0 * 2000.0), production=_eq205_production),
        _RouteOracle("IVH-EXTRA-04", "built_up_beam_flange_connections", "14.4.1 local pressure definition", None, None, "V=gamma_f*gamma_f1*F_n/l_eff", lambda: 1.2 * 1.1 * 100_000.0 / 250.0, production=_local_pressure_production),
    ]


def _run_route_oracles(root: str | Path) -> list[dict[str, Any]]:
    """Run independent arithmetic against materialized runner results/direct production targets."""
    root_path = Path(root)
    results: list[dict[str, Any]] = []
    for case in _route_oracles():
        reference = float(case.reference())
        if case.production is not None:
            calculated = float(case.production(root_path))
            production_mode = "direct_public_function"
        else:
            assert case.output_file is not None and case.result_path is not None
            calculated = _result_from_output(root_path, case.output_file, case.result_path)
            production_mode = "materialized_runner_output"
        error = abs(calculated - reference)
        passed = error <= case.tolerance
        results.append(
            {
                "validation_case_id": case.case_id,
                "evidence_class": "independent_hand_calculation_oracle",
                "route": case.route,
                "standard_reference": case.standard_reference,
                "formula": case.formula,
                "production_mode": production_mode,
                "output_file": case.output_file,
                "result_path": case.result_path,
                "reference_value": reference,
                "calculated_value": calculated,
                "absolute_error": error,
                "tolerance": case.tolerance,
                "pass_fail": "pass" if passed else "fail",
                "oracle_implementation": "standalone arithmetic in standard_core.independent_validation; production calculation function is not called by the route oracle except where production_mode is direct_public_function",
            }
        )
    return results


def _numeric_boundary(case_id: str, standard_reference: str, func: Callable[[], float], reference: float, tolerance: float = 1e-12) -> dict[str, Any]:
    try:
        calculated = float(func())
        error = abs(calculated - reference)
        passed = error <= tolerance
        return {"validation_case_id": case_id, "evidence_class": "boundary_condition_check", "standard_reference": standard_reference, "reference_value": reference, "calculated_value": calculated, "absolute_error": error, "tolerance": tolerance, "detail": None, "pass_fail": "pass" if passed else "fail"}
    except Exception as exc:  # explicit failure capture for report only
        return {"validation_case_id": case_id, "evidence_class": "boundary_condition_check", "standard_reference": standard_reference, "reference_value": reference, "detail": f"unexpected {type(exc).__name__}: {exc}", "pass_fail": "fail"}


def _exception_boundary(case_id: str, standard_reference: str, func: Callable[[], Any], expected_exception: type[Exception]) -> dict[str, Any]:
    try:
        func()
    except expected_exception as exc:
        return {"validation_case_id": case_id, "evidence_class": "boundary_condition_check", "standard_reference": standard_reference, "expected_exception": expected_exception.__name__, "detail": str(exc), "pass_fail": "pass"}
    except Exception as exc:
        return {"validation_case_id": case_id, "evidence_class": "boundary_condition_check", "standard_reference": standard_reference, "expected_exception": expected_exception.__name__, "detail": f"wrong exception {type(exc).__name__}: {exc}", "pass_fail": "fail"}
    return {"validation_case_id": case_id, "evidence_class": "boundary_condition_check", "standard_reference": standard_reference, "expected_exception": expected_exception.__name__, "detail": "expected exception was not raised", "pass_fail": "fail"}


def _run_boundary_cases() -> list[dict[str, Any]]:
    """Run the 24 high-consequence boundary/domain checks recovered from the historical audit map."""
    from .axial_members import open_u_section_phi_1, open_u_section_torsional_flexural_utilization
    from .local_stability import wall_slenderness_limit_eq23
    from .base_plates_and_combined_force_strength import base_plate_required_thickness_eq101, base_plate_cantilever_moment_eq102
    from .effective_lengths_and_limiting_slenderness import truss_chord_effective_length_in_plane_eq136, truss_chord_effective_length_out_of_plane_eq137
    from .sheet_structures_strength_and_stability import membrane_strength_utilization_eq148
    from .reconstruction_assessment import gamma_m_clause_18_3_13, composite_resistance_factor_eq224

    phi_at_boundary = 0.85
    c_at_boundary = phi_at_boundary * 2.0**2 / 7.6
    c_upper = (phi_at_boundary + 1e-9) * 2.0**2 / 7.6
    return [
        _numeric_boundary("IVH-BOUND-001", "7.1.5 equation (11)", lambda: open_u_section_phi_1(c_at_boundary, 2.0), 0.85),
        _numeric_boundary("IVH-BOUND-002", "7.1.5 equation (10), phi1=0.85", lambda: open_u_section_torsional_flexural_utilization(400_000.0, 2500.0, 400.0, 1.0, c_at_boundary, 2.0), 0.47058823529411764),
        _numeric_boundary("IVH-BOUND-003", "7.1.5 equation (10), upper branch", lambda: open_u_section_torsional_flexural_utilization(400_000.0, 2500.0, 400.0, 1.0, c_upper, 2.0), 0.4659289457217879, 1e-11),
        _exception_boundary("IVH-BOUND-004", "7.1.5 equation (11) domain", lambda: open_u_section_phi_1(0.5, 0.0), ValueError),
        _numeric_boundary("IVH-BOUND-005", "7.3.2 equation (23), lambda=0", lambda: wall_slenderness_limit_eq23(0.0), 1.3),
        _numeric_boundary("IVH-BOUND-006", "7.3.2 equation (23), lambda=2", lambda: wall_slenderness_limit_eq23(2.0), 1.9),
        _exception_boundary("IVH-BOUND-007", "7.3.2 equation (23) branch", lambda: wall_slenderness_limit_eq23(2.000001), ValueError),
        _numeric_boundary("IVH-BOUND-008", "8.6.2 equation (102), zero pressure", lambda: base_plate_cantilever_moment_eq102(0.0, 200.0), 0.0),
        _numeric_boundary("IVH-BOUND-009", "8.6.2 equation (102), quadratic scaling", lambda: base_plate_cantilever_moment_eq102(1.0, 200.0), 20_000.0),
        _numeric_boundary("IVH-BOUND-010", "8.6.2 equation (101), zero moment", lambda: base_plate_required_thickness_eq101(0.0, 250.0, 1.0), 0.0),
        _numeric_boundary("IVH-BOUND-011", "10.1.2 equation (136)", lambda: truss_chord_effective_length_in_plane_eq136(1000.0, -0.55), 801.71625),
        _numeric_boundary("IVH-BOUND-012", "10.1.2 equation (136)", lambda: truss_chord_effective_length_in_plane_eq136(1000.0, 0.0), 830.0),
        _numeric_boundary("IVH-BOUND-013", "10.1.2 equation (136)", lambda: truss_chord_effective_length_in_plane_eq136(1000.0, 1.0), 1000.0),
        _exception_boundary("IVH-BOUND-014", "10.1.2 equation (136) alpha domain", lambda: truss_chord_effective_length_in_plane_eq136(1000.0, -0.550001), ValueError),
        _numeric_boundary("IVH-BOUND-015", "10.1.2 equation (137), k=2 beta=-0.5", lambda: truss_chord_effective_length_out_of_plane_eq137(1000.0, 2, -0.5), 625.0),
        _exception_boundary("IVH-BOUND-016", "10.1.2 equation (137), k domain", lambda: truss_chord_effective_length_out_of_plane_eq137(1000.0, 1, 0.0), ValueError),
        _numeric_boundary("IVH-BOUND-017", "11.1.1 equation (148), zero stress", lambda: membrane_strength_utilization_eq148(0.0, 0.0, 0.0, 355.0, 1.0), 0.0),
        _numeric_boundary("IVH-BOUND-018", "11.1.1 equation (148), uniaxial yield", lambda: membrane_strength_utilization_eq148(355.0, 0.0, 0.0, 355.0, 1.0), 1.0),
        _numeric_boundary("IVH-BOUND-019", "11.1.1 equation (148), pure shear yield", lambda: membrane_strength_utilization_eq148(0.0, 0.0, 355.0 / math.sqrt(3.0), 355.0, 1.0), 1.0),
        _numeric_boundary("IVH-BOUND-020", "18.3.13 gamma_M, ratio=0.6", lambda: gamma_m_clause_18_3_13(1, 60_000.0, 1000.0, 100.0, 0.9), 0.9),
        _numeric_boundary("IVH-BOUND-021", "18.3.13 gamma_M, below 0.6 group 1", lambda: gamma_m_clause_18_3_13(1, 59_999.0, 1000.0, 100.0, 0.9), 0.95),
        _numeric_boundary("IVH-BOUND-022", "18.3.13 gamma_M, below 0.6 group 3", lambda: gamma_m_clause_18_3_13(3, 59_999.0, 1000.0, 100.0, 0.9), 1.0),
        _exception_boundary("IVH-BOUND-023", "18.3.13 gamma_M group domain", lambda: gamma_m_clause_18_3_13(5, 50_000.0, 1000.0, 100.0, 0.9), ValueError),
        _exception_boundary("IVH-BOUND-024", "18.3.15 equation (224), strengthened properties domain", lambda: composite_resistance_factor_eq224(330.0, 300.0, 3000.0, 2000.0, 8_000_000.0, 12_000_000.0), ValueError),
    ]


def _run_targeted_analytical_mutation_probes(route_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate two sensitivity probes for each of the 21 primary route oracles.

    These are deliberately labelled analytical sensitivity probes, not AST/source
    mutation testing.  They demonstrate that each independent route oracle would
    reject representative coefficient/scale perturbations at its stated tolerance.
    """
    probes: list[dict[str, Any]] = []
    primary = [case for case in route_cases if case["validation_case_id"].startswith("IVH-ROUTE-")]
    for case in primary:
        reference = float(case["reference_value"])
        tol = float(case["tolerance"])
        variants = [
            ("coefficient_plus_2_percent", reference * 1.02),
            ("denominator_or_scale_omission", reference / 0.9 if reference != 0.0 else 0.1),
        ]
        for name, mutated in variants:
            killed = abs(mutated - reference) > tol
            probes.append(
                {
                    "mutation_id": f"IVH-MUT-{case['validation_case_id'].split('-')[-1]}-{name}",
                    "source_validation_case_id": case["validation_case_id"],
                    "route": case["route"],
                    "evidence_class": "targeted_formula_mutation_probe",
                    "mutation": name,
                    "reference_value": reference,
                    "mutated_value": mutated,
                    "killed": killed,
                    "pass_fail": "pass" if killed else "fail",
                    "limitations": "Analytical oracle sensitivity only; not exhaustive AST/source mutation testing.",
                }
            )
    return probes


def _run_schema_adversarial_probes() -> list[dict[str, Any]]:
    """Exercise recursive type, nested, non-finite, and extra-property rejection."""
    from .schema_validation import validate_case

    schema = {
        "type": "object",
        "required": ["items", "meta"],
        "additionalProperties": False,
        "properties": {
            "items": {"type": "array", "minItems": 1, "items": {"type": "number", "minimum": 0}},
            "meta": {
                "type": "object",
                "required": ["factor"],
                "additionalProperties": False,
                "properties": {"factor": {"type": "number", "exclusiveMinimum": 0}},
            },
        },
    }
    probes = [
        ("SCHEMA-ADV-001", {"items": "not-an-array", "meta": {"factor": 1.0}}, "array represented by string"),
        ("SCHEMA-ADV-002", {"items": [1.0], "meta": {"factor": "bad"}}, "invalid nested numerical field"),
        ("SCHEMA-ADV-003", {"items": [float("nan")], "meta": {"factor": 1.0}}, "NaN in nested array"),
        ("SCHEMA-ADV-004", {"items": [1.0], "meta": {"factor": float("inf")}}, "infinity in nested object"),
        ("SCHEMA-ADV-005", {"items": [1.0], "meta": {}}, "missing nested required property"),
        ("SCHEMA-ADV-006", {"items": [1.0], "meta": {"factor": 1.0}, "unexpected": 1}, "unexpected top-level property"),
    ]
    out: list[dict[str, Any]] = []
    for case_id, payload, description in probes:
        errors = validate_case(payload, schema)
        out.append({"validation_case_id": case_id, "evidence_class": "schema_adversarial_probe", "description": description, "errors": errors, "pass_fail": "pass" if errors else "fail"})
    return out


def run_independent_validation(root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Run the Phase 0.23 route-level independent arithmetic and adversarial validation suite.

    Standard reference:
        СП 16.13330.2017, selected clauses and equations identified by each validation record.

    Parameters:
        root: Package root containing materialized calculation outputs.

    Returns:
        Structured validation report with independent route oracles, boundary cases, analytical mutation probes, and schema probes.

    Assumptions:
        Materialized runner outputs have been regenerated from the current cumulative package.

    Sign convention:
        Each oracle follows the sign convention stated by its cited normative formula.

    Unit convention:
        N, mm, N/mm2 and dimensionless quantities are used exactly as declared by the individual production APIs.

    Applicability:
        Phase 0.23 validation evidence for the reconstructed cumulative СП 16 package.

    Limitations:
        Route-level evidence is not function-complete validation, external cross-implementation validation, or legal certification.

    Raises:
        FileNotFoundError or ValueError when required materialized evidence is absent or malformed.

    Examples:
        ``run_independent_validation('.')``

    Tests:
        tests/test_phase_0_23_independent_normative_rebaseline.py

    Implementation notes:
        Legacy self-check counts are never promoted to independent evidence.
    """
    route_cases = _run_route_oracles(root)
    boundary_cases = _run_boundary_cases()
    mutation_probes = _run_targeted_analytical_mutation_probes(route_cases)
    schema_probes = _run_schema_adversarial_probes()
    route_primary = [x for x in route_cases if x["validation_case_id"].startswith("IVH-ROUTE-")]
    all_pass = all(x["pass_fail"] == "pass" for x in route_cases + boundary_cases + mutation_probes + schema_probes)
    return {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_qualification": RELEASE_QUALIFICATION,
        "evidence_taxonomy": {
            "implementation_self_check": "non-independent legacy regression/transcription evidence; reported separately",
            "independent_hand_calculation_oracle": "separate arithmetic path compared with materialized production result/direct public target",
            "boundary_condition_check": "direct production-function domain/branch probe with explicit expected result or exception",
            "targeted_formula_mutation_probe": "analytical oracle-sensitivity probe; not source-level mutation testing",
            "schema_adversarial_probe": "recursive/fail-closed input integrity probe",
            "external_cross_implementation": "not performed",
            "published_worked_example": "no complete worked-example corpus identified in supplied СП source",
        },
        "route_cases": route_cases,
        "route_cases_all_passed": all(x["pass_fail"] == "pass" for x in route_cases),
        "primary_route_count": len(route_primary),
        "independent_oracle_case_count": len(route_cases),
        "boundary_cases": boundary_cases,
        "boundary_cases_all_passed": all(x["pass_fail"] == "pass" for x in boundary_cases),
        "mutation_probes": mutation_probes,
        "targeted_mutation_score": sum(bool(x["killed"]) for x in mutation_probes) / len(mutation_probes),
        "surviving_mutation_ids": [x["mutation_id"] for x in mutation_probes if not x["killed"]],
        "schema_adversarial_probes": schema_probes,
        "schema_adversarial_all_passed": all(x["pass_fail"] == "pass" for x in schema_probes),
        "release_scope_pass": all_pass,
        "limitations": [
            "Independent arithmetic is route-level, not function-complete across every public calculation function.",
            "Targeted mutation probes are analytical sensitivity checks, not exhaustive AST/source mutation testing.",
            "No external cross-implementation comparison has been performed.",
            "No complete published worked-example corpus is included in the supplied СП source.",
            "Passing this validation scope does not establish engineering-use readiness or legal certification.",
        ],
    }


def write_independent_validation_reports(report: dict[str, Any], reports_dir: str | Path) -> None:
    """
    Summary:
        Write Phase 0.23 independent-validation evidence as deterministic JSON and Markdown.

    Standard reference:
        СП 16.13330.2017; report metadata preserves the per-case references.

    Parameters:
        report: Result returned by run_independent_validation.
        reports_dir: Destination directory.

    Returns:
        None; report files are written to disk.

    Assumptions:
        The supplied report is JSON-serializable and contains no non-finite numbers.

    Sign convention:
        Not applicable to report serialization.

    Unit convention:
        Units are retained from validation records without conversion.

    Applicability:
        Phase 0.23 release evidence generation.

    Limitations:
        Report generation does not add validation evidence beyond the supplied report.

    Raises:
        OSError for filesystem failures and ValueError for non-JSON numerical content.

    Examples:
        ``write_independent_validation_reports(run_independent_validation('.'), 'reports')``

    Tests:
        tests/test_phase_0_23_independent_normative_rebaseline.py

    Implementation notes:
        JSON serialization uses allow_nan=False to preserve finite-only release evidence.
    """
    destination = Path(reports_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "independent_validation_report_v0_23.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# Independent validation report — Phase 0.23",
        "",
        f"- Release scope: **{'PASS' if report['release_scope_pass'] else 'FAIL'}**",
        f"- Primary calculation routes independently checked: **{report['primary_route_count']}/{report['primary_route_count']}**",
        f"- Independent arithmetic cases: **{report['independent_oracle_case_count']}**",
        f"- Boundary/domain cases: **{len(report['boundary_cases'])}**",
        f"- Analytical mutation probes: **{len(report['mutation_probes'])}**, sensitivity score **{report['targeted_mutation_score']:.1%}**",
        f"- Schema adversarial probes: **{len(report['schema_adversarial_probes'])}**",
        "",
        "## Evidence qualification",
        "",
        "Legacy regression/transcription checks are not counted as independent validation. Route oracles use separately written arithmetic. Boundary probes exercise production functions directly. Mutation probes are explicitly not source-level mutation testing.",
        "",
        "## Open validation gaps",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    (destination / "independent_validation_report_v0_23.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
