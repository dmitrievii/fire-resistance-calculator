"""Release audit for traceability, implementation mappings, schemas, tests, and docstrings."""

from __future__ import annotations

import ast
import csv
import importlib
import json
from collections import Counter
from pathlib import Path
from .release_metadata import RELEASE_STAGE
from typing import Any

from .equations import EQUATION_FUNCTIONS, IMPLEMENTED_EQUATION_IDS
from .material_resistance import IMPLEMENTED_PROCEDURE_IDS as MATERIAL_PROCEDURE_IDS
from .axial_members import IMPLEMENTED_PROCEDURE_IDS as AXIAL_PROCEDURE_IDS
from .built_up_axial_members import IMPLEMENTED_PROCEDURE_IDS as BUILT_UP_PROCEDURE_IDS
from .local_stability import IMPLEMENTED_PROCEDURE_IDS as LOCAL_STABILITY_PROCEDURE_IDS
from .bending_members import IMPLEMENTED_PROCEDURE_IDS as BENDING_PROCEDURE_IDS
from .crane_runway_and_bending_stability import IMPLEMENTED_PROCEDURE_IDS as STABILITY_PROCEDURE_IDS
from .bending_member_local_stability import IMPLEMENTED_PROCEDURE_IDS as BENDING_LOCAL_STABILITY_PROCEDURE_IDS
from .base_plates_and_combined_force_strength import IMPLEMENTED_PROCEDURE_IDS as BASE_PLATE_COMBINED_PROCEDURE_IDS
from .beam_column_stability import IMPLEMENTED_PROCEDURE_IDS as BEAM_COLUMN_PROCEDURE_IDS
from .built_up_beam_columns_and_combined_local_stability import IMPLEMENTED_PROCEDURE_IDS as COMBINED_LOCAL_PROCEDURE_IDS
from .effective_lengths_and_limiting_slenderness import IMPLEMENTED_PROCEDURE_IDS as EFFECTIVE_LENGTH_PROCEDURE_IDS
from .sheet_structures_strength_and_stability import IMPLEMENTED_PROCEDURE_IDS as SHEET_STRUCTURE_PROCEDURE_IDS
from .fatigue_design import IMPLEMENTED_PROCEDURE_IDS as FATIGUE_PROCEDURE_IDS
from .brittle_fracture_and_welded_connections import IMPLEMENTED_PROCEDURE_IDS as WELDED_PROCEDURE_IDS
from .bolted_and_friction_connections import IMPLEMENTED_PROCEDURE_IDS as BOLTED_PROCEDURE_IDS
from .built_up_beam_flange_connections import IMPLEMENTED_PROCEDURE_IDS as FLANGE_CONNECTION_PROCEDURE_IDS
from .structural_detailing_and_support_bearings import IMPLEMENTED_PROCEDURE_IDS as DETAILING_BEARING_PROCEDURE_IDS
from .overhead_line_and_switchyard_supports import IMPLEMENTED_PROCEDURE_IDS as LINE_SUPPORT_PROCEDURE_IDS
from .antenna_structures import IMPLEMENTED_PROCEDURE_IDS as ANTENNA_STRUCTURE_PROCEDURE_IDS
from .reconstruction_assessment import IMPLEMENTED_PROCEDURE_IDS as RECONSTRUCTION_PROCEDURE_IDS
from .schema_validation import validate_case
from .tables import IMPLEMENTED_TABLE_IDS, TABLE_DATA_FILES
from .independent_validation import run_independent_validation
from .normative_rebaseline import run_normative_rebaseline
from .runner import _prepare_case_for_validation

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = MATERIAL_PROCEDURE_IDS + AXIAL_PROCEDURE_IDS + BUILT_UP_PROCEDURE_IDS + LOCAL_STABILITY_PROCEDURE_IDS + BENDING_PROCEDURE_IDS + STABILITY_PROCEDURE_IDS + BENDING_LOCAL_STABILITY_PROCEDURE_IDS + BASE_PLATE_COMBINED_PROCEDURE_IDS + BEAM_COLUMN_PROCEDURE_IDS + COMBINED_LOCAL_PROCEDURE_IDS + EFFECTIVE_LENGTH_PROCEDURE_IDS + SHEET_STRUCTURE_PROCEDURE_IDS + FATIGUE_PROCEDURE_IDS + WELDED_PROCEDURE_IDS + BOLTED_PROCEDURE_IDS + FLANGE_CONNECTION_PROCEDURE_IDS + DETAILING_BEARING_PROCEDURE_IDS + LINE_SUPPORT_PROCEDURE_IDS + ANTENNA_STRUCTURE_PROCEDURE_IDS + RECONSTRUCTION_PROCEDURE_IDS

ALLOWED_STATUSES = {
    "implemented", "implemented_as_data", "implemented_as_validation_reference",
    "no_code_informative", "no_code_explanatory", "external_reference_required",
    "not_yet_implemented",
}
FUNCTION_SECTIONS = ["Summary:", "Standard reference:", "Parameters:", "Returns:", "Assumptions:", "Sign convention:", "Unit convention:", "Applicability:", "Limitations:", "Raises:", "Examples:", "Tests:", "Implementation notes:"]
CLASS_SECTIONS = ["Summary:", "Standard reference:", "Fields:", "Validation:", "Used by:"]


def audit_public_docstrings(package_dir: str | Path) -> dict[str, Any]:
    """
    Summary:
        Inspect public functions and classes for mandatory structured docstring sections.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024
        Clause: Package quality control
        Annex: None
        Equation/Table: None
        Audit ID: AUDIT-DOCSTRING-001
        Normative status: no_code_explanatory

    Mathematical form:
        Public API AST traversal followed by required-section set inclusion checks.

    Parameters:
        package_dir:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Directory containing Python implementation modules.
            Valid range: Existing package directory.
            Source: package layout

    Returns:
        Type: dict[str, Any]
        Unit: counts and names
        Meaning: Public API and missing-section audit results.

    Assumptions:
        - Names beginning with an underscore are private.

    Sign convention:
        - Counts are non-negative.

    Unit convention:
        - Returned numerical values are API object counts.

    Applicability:
        - All package release stages.

    Limitations:
        - Static inspection does not prove semantic accuracy of a docstring.

    Raises:
        FileNotFoundError: The package directory does not exist.

    Examples:
        >>> result = audit_public_docstrings("standard_core")
        >>> result["docstrings_failed"]
        0

    Tests:
        Unit tests:
            - tests/test_docstrings.py::test_public_api_docstrings
        Validation cases:
            - AUDIT-RUN-003

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    directory=Path(package_dir)
    if not directory.exists(): raise FileNotFoundError(directory)
    public_functions=0; public_classes=0; failed=[]
    for path in sorted(directory.glob("*.py")):
        tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                public_functions+=1; doc=ast.get_docstring(node) or ""; missing=[s for s in FUNCTION_SECTIONS if s not in doc]
                if missing: failed.append({"object":f"{path.name}:{node.name}","missing_sections":missing})
            elif isinstance(node,ast.ClassDef) and not node.name.startswith("_"):
                public_classes+=1; doc=ast.get_docstring(node) or ""; missing=[s for s in CLASS_SECTIONS if s not in doc]
                if missing: failed.append({"object":f"{path.name}:{node.name}","missing_sections":missing})
    checked=public_functions+public_classes
    return {"public_functions_checked":public_functions,"public_classes_checked":public_classes,"docstrings_passed":checked-len(failed),"docstrings_failed":len(failed),"missing_sections":failed}


def run_final_audit(package_root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Execute the Phase 0.23 reconstructed cumulative release audit with explicit implementation and external-reference classifications.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024
        Clause: Entire supplied inventory with selected implementation through Section 18 and Annexes Д, Е, Ж, and К
        Annex: A-K
        Equation/Table: Equations (1)-(224), including implemented (78)-(173), (Д.1), (Д.2), and (Д.4), and inventoried tables
        Audit ID: AUDIT-FINAL-003
        Normative status: no_code_explanatory

    Mathematical form:
        Inventory classification + registry/function/data/test/schema/validation/docstring consistency checks.

    Parameters:
        package_root:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Root folder of the release package.
            Valid range: Existing package root.
            Source: command-line runner

    Returns:
        Type: dict[str, Any]
        Unit: counts, identifiers, and booleans
        Meaning: Machine-readable final audit report.

    Assumptions:
        - Inventory CSV headers follow the documented schemas.
        - Test status fields truthfully identify implemented-row coverage and are checked against test-file existence.

    Sign convention:
        - Counts are non-negative; unresolved rows are not suppressed.

    Unit convention:
        - Numerical outputs are audit counts rather than engineering values.

    Applicability:
        - Current cumulative release; Phase 0.23 evidence remains a parent validation layer.

    Limitations:
        - Static mapping checks do not replace independent engineering validation.

    Raises:
        ValueError: An inventory status, mapping, schema, validation case, or registry is inconsistent.
        FileNotFoundError: A required release file is missing.

    Examples:
        >>> report = run_final_audit(".")
        >>> report["release_stage"]
        RELEASE_STAGE

    Tests:
        Unit tests:
            - tests/test_final_audit.py::test_final_audit_selected_scope_and_unresolved_rows
        Validation cases:
            - AUDIT-RUN-003

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    root=Path(package_root)
    def rows(name):
        with (root/name).open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
    equations=rows("audit_inventory/equation_inventory.csv")
    tables=rows("audit_inventory/table_inventory.csv")
    procedures=rows("audit_inventory/procedure_inventory.csv")
    clauses=rows("audit_inventory/clause_register.csv")
    mapping=rows("audit_inventory/implementation_map.csv")
    all_items=equations+tables+procedures
    invalid_status=[r["audit_id"] for r in all_items if r["implementation_status"] not in ALLOWED_STATUSES]
    duplicate_ids=[x for x,c in Counter(r["audit_id"] for r in all_items).items() if c>1]
    if invalid_status: raise ValueError(f"Invalid implementation statuses: {invalid_status}")
    if duplicate_ids: raise ValueError(f"Duplicate audit IDs across inventories: {duplicate_ids}")
    mapping_by_id={r["audit_id"]:r for r in mapping}
    missing_mapping=[r["audit_id"] for r in all_items if r["audit_id"] not in mapping_by_id]
    if missing_mapping: raise ValueError(f"Inventory rows missing implementation mapping: {missing_mapping[:10]}")
    status_mismatch=[r["audit_id"] for r in all_items if mapping_by_id[r["audit_id"]]["status"] != r["implementation_status"]]
    if status_mismatch: raise ValueError(f"Implementation-map status mismatch: {status_mismatch}")

    equation_registry_missing=[r["audit_id"] for r in equations if r["implementation_status"]=="implemented" and r["audit_id"] not in IMPLEMENTED_EQUATION_IDS]
    equation_registry_extra=[x for x in IMPLEMENTED_EQUATION_IDS if not any(r["audit_id"]==x and r["implementation_status"]=="implemented" for r in equations)]
    function_errors=[]
    for audit_id,path in EQUATION_FUNCTIONS.items():
        module_name,function_name=path.rsplit(".",1)
        obj=getattr(importlib.import_module(module_name),function_name,None)
        if not callable(obj): function_errors.append({"audit_id":audit_id,"path":path})
    table_registry_missing=[r["audit_id"] for r in tables if r["implementation_status"] in {"implemented","implemented_as_data"} and r["audit_id"] not in IMPLEMENTED_TABLE_IDS]
    table_registry_extra=[x for x in IMPLEMENTED_TABLE_IDS if not any(r["audit_id"]==x and r["implementation_status"] in {"implemented","implemented_as_data"} for r in tables)]
    missing_table_data=[{"audit_id":x,"path":TABLE_DATA_FILES.get(x)} for x in IMPLEMENTED_TABLE_IDS if x not in TABLE_DATA_FILES or not (root/TABLE_DATA_FILES[x]).exists()]
    procedure_registry_missing=[r["audit_id"] for r in procedures if r["implementation_status"]=="implemented" and r["audit_id"] not in IMPLEMENTED_PROCEDURE_IDS]
    test_file_errors=[]
    for r in all_items:
        if r["implementation_status"] in {"implemented","implemented_as_data"}:
            m=mapping_by_id[r["audit_id"]]
            if not m.get("test_file") or not (root/m["test_file"]).exists() or r.get("test_status") in {"","not_started"}:
                test_file_errors.append(r["audit_id"])
    no_code_without_justification=[r["audit_id"] for r in all_items if r["implementation_status"].startswith("no_code") and not r.get("comments","").strip()]
    external_without_explanation=[r["audit_id"] for r in all_items if r["implementation_status"]=="external_reference_required" and not r.get("comments","").strip()]

    schema_pairs=[
        ("schemas/profile_catalog_case.schema.json", "examples/profile_catalog_example.json"),
        ("schemas/minimal_case.schema.json", "examples/minimal_case_example.json"),
        ("schemas/axial_member_case.schema.json", "examples/axial_member_example.json"),
        ("schemas/built_up_axial_member_case.schema.json", "examples/built_up_axial_member_example.json"),
        ("schemas/local_stability_case.schema.json", "examples/local_stability_example.json"),
        ("schemas/bending_member_case.schema.json", "examples/bending_member_example.json"),
        ("schemas/bending_member_guided_case.schema.json", "examples/bending_member_guided_example.json"),
        ("schemas/crane_runway_and_bending_stability_case.schema.json", "examples/crane_runway_and_bending_stability_example.json"),
        ("schemas/bending_member_local_stability_case.schema.json", "examples/bending_member_local_stability_example.json"),
        ("schemas/base_plates_and_combined_force_strength_case.schema.json", "examples/base_plates_and_combined_force_strength_example.json"),
        ("schemas/beam_column_stability_case.schema.json", "examples/beam_column_stability_example.json"),
        ("schemas/built_up_beam_columns_and_combined_local_stability_case.schema.json", "examples/built_up_beam_columns_and_combined_local_stability_example.json"),
        ("schemas/effective_lengths_and_limiting_slenderness_case.schema.json", "examples/effective_lengths_and_limiting_slenderness_example.json"),
        ("schemas/effective_length_guided_case.schema.json", "examples/effective_length_guided_example.json"),
        ("schemas/sheet_structures_strength_and_stability_case.schema.json", "examples/sheet_structures_strength_and_stability_example.json"),
        ("schemas/sheet_structure_guided_case.schema.json", "examples/sheet_structure_guided_example.json"),
        ("schemas/fatigue_design_case.schema.json", "examples/fatigue_design_example.json"),
        ("schemas/fatigue_guided_case.schema.json", "examples/fatigue_guided_example.json"),
        ("schemas/brittle_fracture_guided_case.schema.json", "examples/brittle_fracture_guided_example.json"),
        ("schemas/brittle_fracture_and_welded_connections_case.schema.json", "examples/brittle_fracture_and_welded_connections_example.json"),
        ("schemas/bolted_and_friction_connections_case.schema.json", "examples/bolted_and_friction_connections_example.json"),
        ("schemas/built_up_beam_flange_connections_case.schema.json", "examples/built_up_beam_flange_connections_example.json"),
        ("schemas/structural_detailing_and_support_bearings_case.schema.json", "examples/structural_detailing_and_support_bearings_example.json"),
        ("schemas/overhead_line_and_switchyard_supports_case.schema.json", "examples/overhead_line_and_switchyard_supports_example.json"),
        ("schemas/antenna_structures_case.schema.json", "examples/antenna_structures_example.json"),
        ("schemas/reconstruction_assessment_case.schema.json", "examples/reconstruction_assessment_example.json"),
    ]
    schema_errors=[]
    for schema_path, example_path in schema_pairs:
        schema=json.loads((root/schema_path).read_text(encoding="utf-8"))
        example=json.loads((root/example_path).read_text(encoding="utf-8"))
        if "profile_ref" in example or "material_ref" in example:
            try:
                prepared, prepared_schema, _ = _prepare_case_for_validation(example, root)
            except Exception as exc:
                schema_errors.append(f"{example_path}: pre-schema reference hydration failed: {exc}")
                continue
            if prepared_schema.get("$id") != schema.get("$id"):
                schema_errors.append(f"{example_path}: action resolved to an unexpected schema")
                continue
            schema_errors.extend(f"{example_path}: {error}" for error in validate_case(prepared,prepared_schema))
        else:
            schema_errors.extend(f"{example_path}: {error}" for error in validate_case(example,schema))
    validation=json.loads((root/"reports/validation_report.json").read_text(encoding="utf-8"))
    validation_case_errors=[c.get("validation_case_id","<missing>") for c in validation.get("validation_cases",[]) if c.get("pass_fail") not in {"pass","fail"} or any(k not in c for k in ["calculated_value","reference_value","absolute_error","relative_error","tolerance"])]
    failed_validation=[c["validation_case_id"] for c in validation.get("validation_cases",[]) if c.get("pass_fail")=="fail"]
    docstrings=audit_public_docstrings(root/"standard_core")
    test_count=0
    for path in (root/"tests").glob("test_*.py"):
        tree=ast.parse(path.read_text(encoding="utf-8"))
        test_count+=sum(1 for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_"))

    eq_counts=Counter(r["implementation_status"] for r in equations); tb_counts=Counter(r["implementation_status"] for r in tables); pr_counts=Counter(r["implementation_status"] for r in procedures)
    unresolved_eq=[r["audit_id"] for r in equations if r["implementation_status"]=="not_yet_implemented"]
    unresolved_tb=[r["audit_id"] for r in tables if r["implementation_status"]=="not_yet_implemented"]
    unresolved_pr=[r["audit_id"] for r in procedures if r["implementation_status"]=="not_yet_implemented"]
    independent_validation = run_independent_validation(root)
    normative_rebaseline = run_normative_rebaseline(root)

    checks={
        "all_rows_have_allowed_status":not invalid_status,
        "all_inventory_rows_mapped":not missing_mapping,
        "implementation_map_statuses_match":not status_mismatch,
        "implemented_equations_registered":not equation_registry_missing and not equation_registry_extra,
        "implemented_equation_functions_exist":not function_errors,
        "implemented_tables_registered_and_data_exist":not table_registry_missing and not table_registry_extra and not missing_table_data,
        "implemented_procedures_registered":not procedure_registry_missing,
        "implemented_items_have_tests":not test_file_errors,
        "no_code_rows_have_justification":not no_code_without_justification,
        "external_reference_rows_have_explanation":not external_without_explanation,
        "example_validates_against_schema":not schema_errors,
        "validation_cases_have_required_status_and_fields":not validation_case_errors,
        "validation_self_checks_pass":not failed_validation and bool(validation.get("validation_cases")),
        "public_api_docstrings_pass":docstrings["docstrings_failed"]==0,
        "independent_validation_release_scope_pass": bool(independent_validation.get("release_scope_pass")),
        "independent_normative_rebaseline_pass": bool(normative_rebaseline.get("rebaseline_pass")),
    }
    selected_ids={*IMPLEMENTED_EQUATION_IDS, *IMPLEMENTED_TABLE_IDS, *IMPLEMENTED_PROCEDURE_IDS}
    selected_complete=all(any(r["audit_id"]==x and r["implementation_status"] in {"implemented","implemented_as_data"} for r in all_items) for x in selected_ids)
    return {
        "standard":"СП 16.13330.2017 «Стальные конструкции»",
        "release_stage":RELEASE_STAGE,
        "audit_scope":"FIRE-D1 audits SP554 Sections 8-11 member-mechanical dependencies against frozen current-SP16 N1-N7 producers and the normative-strength basis; FIRE-D2 executes the member fire-mechanics formulas, Appendix-B independent curve inversions, and governing critical-temperature selection with explicit reconciliation of locked-draft clauses 8.6/10.3/11.9; Selected Section 6 formulas; clauses 7.1.1-7.3.11; clauses 8.1-8.6.2; sections 9.1-9.4; Section 10; Section 11 equations (148)-(169), Table 34, and associated shell-strength/stability procedures; Section 12 equations (170)-(173), Tables 35-36, Annex K Table K.1, and associated fatigue procedures; Sections 13 and 14.1 equations (174)-(185), Tables 37-39, and associated brittle-fracture and welded-connection procedures; Sections 14.2-14.3 equations (186)-(192), Tables 40-42, and associated bolted and friction-connection procedures; Section 14.4 equations (193)-(198), Table 43, and associated built-up beam flange-connection procedures; Section 15 execution classification, Table 44, clause 15.12.1 support-bearing routes, and equations (199)-(200); Section 16 equations (201)-(214), Tables 45-46, and associated VL, ORU, and KS member, deformation, detailing, and polygonal-tube procedures; Section 17 equation (215), Table 47, and associated antenna-structure material, rope, wire, deformation, connection, detailing, vibration, marking, and galvanizing routes; Section 18 equations (216)-(224), Table 48, and technical-condition, material-evidence, existing-connection, strengthening, welding-deformation, and retained-deviation routes; Annex D Tables D.1-D.6 and equations (D.1), (D.2), (D.4); Annex E Tables E.1-E.2; and Annex Ж equations (Ж.1)-(Ж.13), Tables Ж.1-Ж.5, and Ж.6-Ж.7 procedures. Equations (10)-(11) and Table 1 are closed in this reconstruction; Annexes Б, В, Г and И that cannot be safely reconstructed numerically are explicitly classified as external normative reference boundaries.",
        "selected_scope_complete":selected_complete,
        "full_standard_implemented_or_classified":not (unresolved_eq or unresolved_tb or unresolved_pr),
        "total_equations":len(equations),"implemented_equations":eq_counts.get("implemented",0),"no_code_informative_equations":eq_counts.get("no_code_informative",0)+eq_counts.get("no_code_explanatory",0),"external_reference_required_equations":eq_counts.get("external_reference_required",0),"unresolved_equations":len(unresolved_eq),"unresolved_equation_ids":unresolved_eq,
        "total_tables":len(tables),"implemented_tables":tb_counts.get("implemented",0)+tb_counts.get("implemented_as_data",0),"reference_only_tables":tb_counts.get("implemented_as_validation_reference",0),"external_reference_required_tables":tb_counts.get("external_reference_required",0),"external_reference_required_table_ids":[r["audit_id"] for r in tables if r["implementation_status"]=="external_reference_required"],"no_code_tables":tb_counts.get("no_code_informative",0)+tb_counts.get("no_code_explanatory",0),"unresolved_tables":len(unresolved_tb),"unresolved_table_ids":unresolved_tb,
        "total_procedures":len(procedures),"implemented_procedures":pr_counts.get("implemented",0),"unresolved_procedures":len(unresolved_pr),"unresolved_procedure_ids":unresolved_pr,
        "total_clause_register_rows":len(clauses),"public_api_docstring_status":docstrings,"test_function_count":test_count,"validation_status":validation.get("validation_status"),"validation_case_count":len(validation.get("validation_cases",[])),
        "independent_validation": {
            "primary_routes": independent_validation.get("primary_route_count"),
            "oracle_cases": independent_validation.get("independent_oracle_case_count"),
            "boundary_cases": len(independent_validation.get("boundary_cases", [])),
            "targeted_analytical_mutation_probes": len(independent_validation.get("mutation_probes", [])),
            "schema_adversarial_probes": len(independent_validation.get("schema_adversarial_probes", [])),
            "release_scope_pass": independent_validation.get("release_scope_pass"),
        },
        "normative_rebaseline_pass": normative_rebaseline.get("rebaseline_pass"),
        "checks":checks,
        "audit_errors":{"invalid_status":invalid_status,"missing_mapping":missing_mapping,"status_mismatch":status_mismatch,"equation_registry_missing":equation_registry_missing,"equation_registry_extra":equation_registry_extra,"function_errors":function_errors,"table_registry_missing":table_registry_missing,"table_registry_extra":table_registry_extra,"missing_table_data":missing_table_data,"procedure_registry_missing":procedure_registry_missing,"test_file_errors":test_file_errors,"no_code_without_justification":no_code_without_justification,"external_without_explanation":external_without_explanation,"schema_errors":schema_errors,"validation_case_errors":validation_case_errors,"failed_validation":failed_validation},
        "known_limitations":["Stage N2 interim profile catalog contains 4069 imported NormCAD rows across 37 families so existing branches can run; each row remains PENDING_ORIGINAL_GOST_AUDIT and engineering_use_ready stays false until the final product-standard reconciliation gate.","Stage N1 is cumulative over the v0.26 validation-campaign baseline; historical parent evidence layers are retained separately and external golden validation remains partial.","Annex Б.1 and Annex В.3/В.4/В.5 are materialized from the locked current source; 20 remaining Annex Б/В/Г/И tables stay explicit external-reference boundaries.","The Table 4 gamma_wm interval 490 < Rwun < 590 N/mm2 is not specified and is rejected unless handled by a future audited source.","Section types in Tables 7-10 must be selected manually from the standard diagrams; arbitrary geometry classification is not implemented.","The frame-system analysis required for battened members with fewer than six panels is surfaced but not solved.","For Figure 3 g, clause 7.2.9 does not explicitly state the equation (21) alpha_1 value; the API does not infer it.","The local-stability functions do not derive effective web height or flange outstand from CAD geometry; clause 7.3.1 and 7.3.7 measurement rules are exposed as audited metadata.","Equation (33) is implemented for inventory completeness but the runner does not perform a complete eccentric-compression check.","Longitudinal-stiffener one-sided inertia-axis equivalence and corrugated-web unfolded geometry remain explicit engineering inputs.","Table D.1 lookup is exact-node only; no interpolation rule is invented.","The clause text says the phi cap applies above the thresholds, while Table D.1 uses the capped values at the boundary nodes; the implementation follows the table at equality and records this ambiguity.","Table E.1 section type must be selected manually from the annex diagrams; the package does not infer it from arbitrary geometry.","Bending-member local-stability equations are implemented as scalar procedures, but arbitrary geometry classification and automatic panel segmentation remain external.","Table 10a interpolation is limited to the printed range 0 to 0.99; extrapolation is rejected.","Continuous-beam redistribution helpers calculate the specified moment transformations but do not perform a global frame analysis.","Tables 12 and 14-18 use exact printed nodes because the supplied standard does not state interpolation rules; terminal inequality columns are applied where printed.","Table 13 infinity entries are represented as mathematical infinity and are not serialized by the example runner.","Annex Ж diagram rows and load cases must be selected manually; arbitrary geometry and moment-diagram recognition is not implemented.","Equation (67) uses web thickness for the printed symbol t in sigma_f,y, supported by dimensional consistency; this transcription choice is documented.","Clause 8.3.4 states a monorail local-stress requirement but supplies no calculation method; it is classified as no_code_explanatory rather than reconstructed.","Annex Ж.6 interpolation requires endpoint values calculated consistently for n=0.9 and n=1.0.","Table 19 interpolation is limited to the required longitudinal-stiffener inertia between printed h1/hef nodes.","Equation (87) does not silently cap flange stresses; applicability and any stress cap remain external engineering checks.","Clause 8.5.16 routes very slender webs to an external flexible-web design method that is not implemented in this package.","Support-stiffener procedures do not complete weld, bearing, buckling, or connection design.","Table E.2 lookups use exact printed nodes and the terminal >2 columns; interpolation is not specified and is therefore rejected.","Clause 8.6.1 foundation resistance remains an explicit external calculation boundary.","Equation (106) checks one signed section point at a time; governing-point search remains external.","Section classification for Tables E.1 and D.2 remains an engineering input.","Table D.3 preserves exact nodes and uses the audited in-domain bilinear digital-table interpolation policy validated against retained NormCAD evidence; extrapolation is forbidden. Tables D.4-D.5 remain exact-node-only because no interpolation policy has been adopted for them.","Table D.5 diagram selection and sign convention remain explicit engineering inputs; the printed 2.55 anomaly is preserved and documented.","Table D.6 type 5 is excluded by Amendment No. 5 and is not exposed as an active calculation row.","Section 9.2 functions do not perform global frame analysis, moment-diagram recognition, effective-length calculation, or automatic section classification.","The Section 9.2 runner requires explicit confirmation that any linked reduced-area and local-stability requirements have been applied.","Sections 9.3-9.4 do not perform global analysis, branch effective-length calculation, automatic section classification, Section 16 design, or complete connector design.","Table 22 and Table 23 interpolation is implemented only where their notes explicitly prescribe linear interpolation; linked endpoint limits remain explicit inputs.","Table 34 is exact-node only because the supplied clause does not state an interpolation rule; non-node c values remain explicit externally justified inputs.","Section 11 functions do not calculate edge effects, arbitrary-shell finite-element stresses, global member stability, or a complete ring-stiffener section and connection.","Equation (156) requires an axial shell critical stress input when r/t is not a printed Table 34 node; no unstated Table 34 interpolation is applied.","Section 12 does not derive load spectra under SP 20.13330, perform rainflow counting, cumulative damage, low-cycle fatigue, or automatic Annex K detail recognition.","Stage N10 closes current-SP16 Section 13 selected routing, but Sections 13 and retained downstream 14.1 do not select steel automatically, perform fracture-mechanics assessment, verify NDT records, qualify welding procedures, or recognize connection geometry from CAD/BIM.","Table 37 and Tables 38-39 require explicit engineering classification; no unstated interpolation is applied.","Sections 14.2-14.3 do not select bolt products, derive actions from a global model, verify installation records, or design anchor bolts governed by external standards.","Table 41 intermediate-geometry interpolation requires an explicitly verified interpolation fraction because the printed two-variable path is not uniquely prescribed.","Section 14.4 does not derive global beam actions, classify Table 43 geometry from CAD/BIM, verify full-penetration weld evidence, design transverse stiffeners, or locate multilayer flange-sheet cut-offs.","Clause 14.4.2 returns the required attachment force but does not complete the individual weld or bolt design.","Section 15 clauses other than Table 44 and 15.12.1-15.12.3 are classified by execution route but are not all encoded as individual scalar functions.","Table 44 category and direction must be selected by the engineer; the 5 percent statement is an enhanced-analysis trigger and not a spacing tolerance.","Equations (199)-(200) do not model bearing contact nonlinearity, wear, skew, anchorage, track bending, or substructure response.","Section 16 requires external determination of loads, combinations, global first- and second-order actions, section properties, and normative geometry categories.","Tables 45-46 use exact categorical rows; Table 45 does not apply to node connections, and Table 46 emergency/erection exclusions and stricter equipment specifications remain explicit.","Equations (209)-(212) require manual Figure 15 and connection classification; unstated interpolation or geometry inference is not performed.","Equations (213)-(214) apply only to 8-12-sided polygonal tubes and do not replace the linked circular-tube and global support checks.","Section 17 requires external loads and combinations, Annex V and Table B.2 product selection, certificates, rope and wire capacity evidence, global analysis, fabrication and test records, aeroelastic assessment, marking regulations, and coating inspection.","Equation (215) is implemented with the printed units and coefficient; it does not replace a vibration or galloping analysis. Table 47 is exact categorical lookup only.","Section 18 does not perform the physical survey, monitoring, laboratory material identification, load generation, global or construction-stage analysis, NDT, or professional acceptance decision.","Table 48 is exact categorical lookup only; unavailable cells are rejected and countersunk-head restrictions are explicit.","Equations (216)-(224) require verified actions, initial stresses and deformations, section properties, stability coefficients, actual defects, and compatible sign conventions from the assessment model.","Figure 24 n_i values for equation (222) remain explicit externally selected inputs; the graph is not digitized or interpolated, and welding heat/residual-stress mechanics are not simulated.","Equation (217) checks one supplied point using absolute algebraic stress; governing-point search remains external. Equation (218) requires externally verified phi_e and gamma_c not exceeding 0.9.","FIRE-D2 closes SP554 Sections 8-11 member fire-mechanics and Appendix-B critical-temperature inversion. It does not close connection fire resistance or SP554 Section 12 heat transfer. Locked-draft clauses 8.6/10.3/11.9 are reconciled explicitly to earliest-critical-temperature control; the source-literal smaller-coefficient wording remains provenance only.","Self-checks are not normative worked-example validation."],
        "next_step":"FIRE-D2 SP554 Sections 8-11 member critical-temperature runtime is complete. Next execute FIRE-D3: SP554 Section 12 thermal calculation and couple the temperature-time solution to FIRE-D2 critical temperature. Connection fire resistance remains a later explicit scope; N1-N10 and FIRE-D1 stay frozen.",
        "release_pass":all(checks.values()) and selected_complete,
    }


def write_audit_reports(report: dict[str, Any], reports_dir: str | Path) -> None:
    """
    Summary:
        Write the current cumulative final audit report as JSON and Markdown.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024
        Clause: Package quality control
        Annex: None
        Equation/Table: None
        Audit ID: AUDIT-WRITER-003
        Normative status: no_code_explanatory

    Mathematical form:
        Audit dictionary -> JSON and Markdown serialization.

    Parameters:
        report:
            Type: dict[str, Any]
            Unit: mixed
            Meaning: Final audit result.
            Valid range: Result returned by run_final_audit.
            Source: audit runner
        reports_dir:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Destination directory.
            Valid range: Writable path.
            Source: package layout

    Returns:
        Type: None
        Unit: not applicable
        Meaning: Report files are written.

    Assumptions:
        - Report fields follow run_final_audit.

    Sign convention:
        - Counts are non-negative.

    Unit convention:
        - Audit values are counts and statuses.

    Applicability:
        - Current cumulative release reporting.

    Limitations:
        - Markdown lists unresolved identifiers compactly.

    Raises:
        OSError: The destination cannot be created or written.

    Examples:
        >>> write_audit_reports(run_final_audit("."), "reports")

    Tests:
        Unit tests:
            - tests/test_final_audit.py::test_main_report_files_exist
        Validation cases:
            - AUDIT-RUN-003

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    destination=Path(reports_dir);destination.mkdir(parents=True,exist_ok=True)
    (destination/"final_audit_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[f"# Final audit report - {RELEASE_STAGE}","",f"- Release audit: **{'PASS' if report['release_pass'] else 'FAIL'}**",f"- Selected scope complete: **{'yes' if report['selected_scope_complete'] else 'no'}**",f"- Full standard implemented/classified: **{'yes' if report['full_standard_implemented_or_classified'] else 'no'}**","","## Inventory status","",f"- Equations: {report['total_equations']} total; {report['implemented_equations']} implemented; {report['unresolved_equations']} unresolved.",f"- Tables: {report['total_tables']} total; {report['implemented_tables']} implemented as code/data; {report.get('external_reference_required_tables',0)} external-reference; {report['unresolved_tables']} unresolved.",f"- Procedures: {report['total_procedures']} total; {report['implemented_procedures']} implemented; {report['unresolved_procedures']} unresolved.","","## API and tests","",f"- Public functions checked: {report['public_api_docstring_status']['public_functions_checked']}",f"- Public classes checked: {report['public_api_docstring_status']['public_classes_checked']}",f"- Docstrings failed: {report['public_api_docstring_status']['docstrings_failed']}",f"- Test functions: {report['test_function_count']}",f"- Validation cases: {report['validation_case_count']} ({report['validation_status']})",f"- Independent primary routes: {report.get('independent_validation',{}).get('primary_routes')}",f"- Independent arithmetic oracle cases: {report.get('independent_validation',{}).get('oracle_cases')}",f"- Boundary/domain cases: {report.get('independent_validation',{}).get('boundary_cases')}",f"- Targeted analytical mutation probes: {report.get('independent_validation',{}).get('targeted_analytical_mutation_probes')}",f"- Schema adversarial probes: {report.get('independent_validation',{}).get('schema_adversarial_probes')}","","## Audit checks",""]
    lines.extend(f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in report['checks'].items())
    lines.extend(["","## Known limitations","",*['- '+x for x in report['known_limitations']],"","## Unresolved inventory","",f"- Unresolved equation IDs: {', '.join(report['unresolved_equation_ids'])}",f"- Unresolved table IDs: {', '.join(report['unresolved_table_ids'])}","","## Next step","",report['next_step'],"","Implemented and tested the selected equations, tables, and procedures from СП 16.13330.2017, with traceability and validation status documented in this audit report. This is not legal certification."])
    (destination/"final_audit_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
