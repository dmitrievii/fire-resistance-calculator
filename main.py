from pathlib import Path

from standard_core.api_hardening import run_api_hardening
from standard_core.final_audit import run_final_audit, write_audit_reports
from standard_core.function_level_validation import run_function_level_validation
from standard_core.phase_0_25_validation import run_phase_0_25_validation, write_phase_0_25_validation_reports
from standard_core.runner import run_case
from standard_core.validation import run_core_validation_cases, write_validation_reports


def _main() -> None:
    root = Path(__file__).resolve().parent
    run_case(root / "examples/profile_catalog_example.json", root)
    run_case(root / "examples/minimal_case_example.json", root)
    run_case(root / "examples/axial_member_example.json", root)
    run_case(root / "examples/axial_member_guided_example.json", root)
    run_case(root / "examples/built_up_axial_member_example.json", root)
    run_case(root / "examples/built_up_axial_member_guided_example.json", root)
    run_case(root / "examples/local_stability_example.json", root)
    run_case(root / "examples/bending_member_example.json", root)
    run_case(root / "examples/bending_member_guided_example.json", root)
    run_case(root / "examples/crane_runway_and_bending_stability_example.json", root)
    run_case(root / "examples/bending_member_local_stability_example.json", root)
    run_case(root / "examples/base_plates_and_combined_force_strength_example.json", root)
    run_case(root / "examples/beam_column_guided_example.json", root)
    run_case(root / "examples/beam_column_stability_example.json", root)
    run_case(root / "examples/built_up_beam_columns_and_combined_local_stability_example.json", root)
    run_case(root / "examples/built_up_beam_column_guided_example.json", root)
    run_case(root / "examples/effective_lengths_and_limiting_slenderness_example.json", root)
    run_case(root / "examples/effective_length_guided_example.json", root)
    run_case(root / "examples/sheet_structures_strength_and_stability_example.json", root)
    run_case(root / "examples/sheet_structure_guided_example.json", root)
    run_case(root / "examples/fatigue_design_example.json", root)
    run_case(root / "examples/fatigue_guided_example.json", root)
    run_case(root / "examples/brittle_fracture_guided_example.json", root)
    run_case(root / "examples/brittle_fracture_and_welded_connections_example.json", root)
    run_case(root / "examples/bolted_and_friction_connections_example.json", root)
    run_case(root / "examples/built_up_beam_flange_connections_example.json", root)
    run_case(root / "examples/structural_detailing_and_support_bearings_example.json", root)
    run_case(root / "examples/overhead_line_and_switchyard_supports_example.json", root)
    run_case(root / "examples/antenna_structures_example.json", root)
    run_case(root / "examples/reconstruction_assessment_example.json", root)
    run_case(root / "examples/sp554_sp16_fire_dependency_bridge_example.json", root)
    run_case(root / "examples/fire_d2_sp554_critical_temperature_case.json", root)
    run_case(root / "examples/fire_d3_sp554_thermal_case.json", root)
    run_case(root / "examples/fire_d4_sp554_section13_assessment_case.json", root)
    validation = run_core_validation_cases()
    write_validation_reports(validation, root / "reports")
    api = run_api_hardening(root)
    function_validation = run_function_level_validation(root)
    phase_0_25 = run_phase_0_25_validation(root)
    write_phase_0_25_validation_reports(phase_0_25, root)
    audit = run_final_audit(root)
    write_audit_reports(audit, root / "reports")
    print("SP554 ↔ SP16 - FIRE-UI2.4 FIRE-VAL1 Routing Remediation (r1)")
    print(f"Release audit: {'PASS' if audit['release_pass'] else 'FAIL'}")
    print(f"Implemented equations: {audit['implemented_equations']}")
    print(f"Implemented tables: {audit['implemented_tables']}")
    print(f"Implemented procedures: {audit['implemented_procedures']}")
    print(f"Validation cases: {audit['validation_case_count']} ({'PASS' if validation['all_passed'] else 'FAIL'})")
    print(f"Retained Phase 0.25 validation: {'PASS' if phase_0_25['phase_0_25_validation_pass'] else 'FAIL'}")
    print(f"Independent function oracles: {phase_0_25['combined_independently_oracled_function_count']}/{phase_0_25['engineering_public_function_count']}")
    print(f"External golden cases: {phase_0_25['external_golden_validation']['passed_count']}/{phase_0_25['external_golden_validation']['case_count']}")
    print(f"Unresolved equations/tables: {audit['unresolved_equations']}/{audit['unresolved_tables']}")
    print("Reports written to reports/ and calculation outputs to outputs/.")


if __name__ == "__main__":
    _main()
