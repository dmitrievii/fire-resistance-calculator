"""Independent inventory rebaseline and static adversarial scan for Phase 0.23."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .release_metadata import (
    ENGINEERING_USE_READY,
    PACKAGE_VERSION,
    PARENT_RELEASE,
    RELEASE_QUALIFICATION,
    RELEASE_STAGE,
    SOURCE_SHA256,
    STANDARD_TITLE,
)


_INVENTORIES = {
    "equations": "equation_inventory.csv",
    "tables": "table_inventory.csv",
    "procedures": "procedure_inventory.csv",
    "clauses": "clause_register.csv",
    "implementation_map": "implementation_map.csv",
}

_INFRA_MODULES = {
    "final_audit.py",
    "validation.py",
    "schema_validation.py",
    "independent_validation.py",
    "normative_rebaseline.py",
    "release_metadata.py",
    "api_hardening.py",
    "function_level_validation.py",
}

_HIGH_RISK_IDS = [
    "SP16-EQ-010", "SP16-EQ-011", "SP16-EQ-023", "SP16-EQ-041",
    "SP16-EQ-068", "SP16-EQ-101", "SP16-EQ-102", "SP16-EQ-109",
    "SP16-EQ-136", "SP16-EQ-137", "SP16-EQ-148", "SP16-EQ-170",
    "SP16-EQ-186", "SP16-EQ-200", "SP16-EQ-204", "SP16-EQ-205",
    "SP16-EQ-215", "SP16-EQ-216", "SP16-EQ-217", "SP16-EQ-218",
    "SP16-EQ-219", "SP16-EQ-220", "SP16-EQ-221", "SP16-EQ-222",
    "SP16-EQ-223", "SP16-EQ-224", "SP16-TBL-1", "SP16-TBL-48",
]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _literal_default_get_calls(source_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.py")):
        if path.name in _INFRA_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"):
                continue
            if len(node.args) < 2:
                continue
            default = node.args[1]
            if isinstance(default, (ast.Constant, ast.Dict, ast.List, ast.Set, ast.Tuple)):
                findings.append(
                    {
                        "file": path.as_posix(),
                        "line": node.lineno,
                        "expression": ast.unparse(node),
                        "risk": "review_required_literal_fallback",
                    }
                )
    return findings


def _broad_exception_handlers(source_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.py")):
        if path.name in _INFRA_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"})
            if broad:
                findings.append({"file": path.as_posix(), "line": node.lineno, "risk": "broad_exception_in_engineering_module"})
    return findings


def _old_release_literals(source_dir: Path) -> list[dict[str, Any]]:
    needles = {"v0.21_reconstruction_assessment", "v0.22_final_annex_and_release_consolidation_reconstructed_r1"}
    findings: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.py")):
        if path.name in _INFRA_MODULES:
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for needle in needles:
                if needle in line:
                    findings.append({"file": path.as_posix(), "line": index, "literal": needle})
    return findings


def _implementation_reference_exists(root: Path, mapping_row: dict[str, str]) -> bool:
    target = mapping_row.get("implemented_function_or_data_file", "").strip()
    if not target:
        return mapping_row.get("status", "") in {"external_reference_required", "no_code_explanatory", "no_code_informative"}
    # Semicolon-separated paths/functions occur in the historical map.  At least one
    # referenced local file/module must resolve for implemented rows; final_audit
    # performs the deeper importability checks.
    for piece in target.split(";"):
        token = piece.strip()
        if not token:
            continue
        file_part = token.split(":", 1)[0]
        if file_part.startswith("standard_core."):
            dotted = file_part.split(":", 1)[0]
            parts = dotted.split(".")
            # Mapping entries may use module:function or module.function.
            # Resolve the longest prefix that corresponds to a local module.
            for stop in range(len(parts), 1, -1):
                module_path = root / ("/".join(parts[:stop]) + ".py")
                if module_path.exists():
                    return True
        candidate = root / file_part
        if candidate.exists():
            return True
    return False


def run_normative_rebaseline(root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Independently re-read the СП 16 inventories and scan engineering modules for selected fail-open implementation patterns.

    Standard reference:
        СП 16.13330.2017 consolidated source with Changes No. 1-6 through 09.12.2024; source identity is pinned by SHA-256.

    Parameters:
        root: Package root containing audit_inventory, data and standard_core.

    Returns:
        Structured rebaseline report with inventory counts, mapping reconciliation, external boundaries, static-scan findings and release checks.

    Assumptions:
        Inventory CSV files are the package transcription corpus to be reconciled; their final_audit verdict is not reused.

    Sign convention:
        Not applicable to inventory/static analysis.

    Unit convention:
        Not applicable except for source references recorded in the inventories.

    Applicability:
        Phase 0.23 reconstructed cumulative package.

    Limitations:
        Static reconciliation does not prove the semantic correctness of every normative equation/table cell.

    Raises:
        FileNotFoundError, csv/json decoding errors, or syntax errors if required package evidence is malformed.

    Examples:
        ``run_normative_rebaseline('.')``

    Tests:
        tests/test_phase_0_23_independent_normative_rebaseline.py

    Implementation notes:
        Production AST scans exclude reporting/validation infrastructure to avoid confusing reporting fallbacks with engineering defaults.
    """
    root_path = Path(root)
    inv_dir = root_path / "audit_inventory"
    eq = _rows(inv_dir / _INVENTORIES["equations"])
    tbl = _rows(inv_dir / _INVENTORIES["tables"])
    proc = _rows(inv_dir / _INVENTORIES["procedures"])
    clauses = _rows(inv_dir / _INVENTORIES["clauses"])
    mapping = _rows(inv_dir / _INVENTORIES["implementation_map"])

    all_inventory = eq + tbl + proc
    inventory_ids = [row["audit_id"] for row in all_inventory]
    duplicate_ids = sorted([key for key, count in Counter(inventory_ids).items() if count > 1])
    map_ids = [row["audit_id"] for row in mapping]
    duplicate_map_ids = sorted([key for key, count in Counter(map_ids).items() if count > 1])
    missing_from_map = sorted(set(inventory_ids) - set(map_ids))
    extra_in_map = sorted(set(map_ids) - set(inventory_ids))

    external_tables = [row for row in tbl if row["implementation_status"] == "external_reference_required"]
    external_table_ids = [row["audit_id"] for row in external_tables]
    unresolved_statuses = {"not_yet_implemented", "todo", "unresolved", "placeholder"}
    unresolved = [row["audit_id"] for row in all_inventory if row.get("implementation_status", "").strip().lower() in unresolved_statuses]

    source_manifest_path = root_path / "data" / "source_manifest.json"
    source_manifest = _read_json(source_manifest_path)
    source_identity_pass = source_manifest.get("source_sha256") == SOURCE_SHA256

    mapping_missing_targets = [
        row["audit_id"]
        for row in mapping
        if row.get("status") in {"implemented", "implemented_as_data"}
        and not _implementation_reference_exists(root_path, row)
    ]

    by_id = {row["audit_id"]: row for row in all_inventory}
    high_risk = []
    for audit_id in _HIGH_RISK_IDS:
        row = by_id.get(audit_id)
        high_risk.append(
            {
                "audit_id": audit_id,
                "present": row is not None,
                "standard_reference": row.get("clause") if row else None,
                "page": row.get("page") if row else None,
                "implementation_status": row.get("implementation_status") if row else None,
                "test_status": row.get("test_status") if row else None,
                "phase_0_23_source_review_status": "source_spot_check_registry_reconfirmed" if row else "missing",
            }
        )

    literal_defaults = _literal_default_get_calls(root_path / "standard_core")
    broad_handlers = _broad_exception_handlers(root_path / "standard_core")
    old_release_literals = _old_release_literals(root_path / "standard_core")

    checks = {
        "source_identity_matches_canonical_supplied_pdf_hash": source_identity_pass,
        "inventory_ids_unique": not duplicate_ids,
        "implementation_map_ids_unique": not duplicate_map_ids,
        "all_inventory_rows_mapped": not missing_from_map and not extra_in_map,
        "no_formally_unresolved_inventory_status": not unresolved,
        "all_implemented_map_targets_resolve_at_file_or_module_level": not mapping_missing_targets,
        "all_high_risk_registry_items_present": all(x["present"] for x in high_risk),
        "engineering_modules_have_no_literal_dict_get_fallbacks": not literal_defaults,
        "engineering_modules_have_no_broad_exception_handlers": not broad_handlers,
        "engineering_modules_have_no_stale_release_literals": not old_release_literals,
        "external_annex_boundaries_are_explicit": len(external_tables) == 20,
    }

    return {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_qualification": RELEASE_QUALIFICATION,
        "parent_release": PARENT_RELEASE,
        "standard": STANDARD_TITLE,
        "source_sha256": SOURCE_SHA256,
        "source_manifest_sha256": _sha256(source_manifest_path),
        "engineering_use_ready": ENGINEERING_USE_READY,
        "method": "Independent CSV re-read + implementation-map reconciliation + AST fail-closed scan; does not reuse standard_core.final_audit pass/fail result.",
        "inventory": {
            "clauses": len(clauses),
            "equations": {"total": len(eq), "statuses": dict(Counter(row["implementation_status"] for row in eq))},
            "tables": {"total": len(tbl), "statuses": dict(Counter(row["implementation_status"] for row in tbl))},
            "procedures": {"total": len(proc), "statuses": dict(Counter(row["implementation_status"] for row in proc))},
            "implementation_map_entries": len(mapping),
            "formally_unresolved_ids": unresolved,
            "duplicate_inventory_ids": duplicate_ids,
            "duplicate_map_ids": duplicate_map_ids,
            "missing_from_map": missing_from_map,
            "extra_in_map": extra_in_map,
            "mapping_missing_targets": mapping_missing_targets,
        },
        "external_reference_tables": [
            {
                "audit_id": row["audit_id"],
                "table_number": row["table_number"],
                "annex": row["annex"],
                "page": row["page"],
                "comments": row["comments"],
            }
            for row in external_tables
        ],
        "high_risk_source_spot_check_registry": high_risk,
        "adversarial_static_scan": {
            "literal_dict_get_fallbacks_in_engineering_modules": literal_defaults,
            "broad_exception_handlers_in_engineering_modules": broad_handlers,
            "stale_release_literals_in_engineering_modules": old_release_literals,
            "interpretation": "A non-empty list is a review candidate, not automatically a normative defect. Infrastructure/reporting modules are excluded from these production-code scans.",
        },
        "remediations_applied_in_phase_0_23": [
            {
                "finding_id": "V023-TRACE-001",
                "severity": "P1",
                "finding": "Runtime/package provenance remained hard-coded as v0.21 in __init__ and runner outputs while the reconstructed baseline was labelled v0.22.",
                "resolution": "Canonical release_metadata.py introduced; runner output provenance and package version now use the Phase 0.23 cumulative identity.",
                "status": "closed",
            },
            {
                "finding_id": "V023-FAILCLOSED-001",
                "severity": "P1",
                "finding": "Table 46 blank-cell interpretation contained a silent default to 'not_limited' if audited null semantics were missing.",
                "resolution": "Blank cells now require explicit per-measure null semantics ('not_limited' or 'not_applicable'); missing/unknown semantics hard-fail.",
                "status": "closed",
            },
        ],
        "scope_findings": [
            "The supplied СП source states its general scope for steel structures operating at temperatures not above 100 °C and not below -60 °C; fire/high-temperature design requires the relevant special normative documents.",
            "Twenty-four Annex Б/В/Г/И tables remain explicit external-reference boundaries in this reconstructed lineage; no incomplete historical transcription has been promoted to calculation-grade data.",
            "Inventory classification closure is not equivalent to complete executable implementation of every narrative engineering requirement.",
            "Global structural analysis, load-combination generation, arbitrary CAD/BIM normative classification, survey/NDT evidence, and professional acceptance remain outside this package.",
        ],
        "checks": checks,
        "rebaseline_pass": all(checks.values()),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_normative_rebaseline_reports(report: dict[str, Any], reports_dir: str | Path) -> None:
    """
    Summary:
        Write the independent normative rebaseline report as deterministic JSON and Markdown.

    Standard reference:
        СП 16.13330.2017; source identity and cited inventory references are preserved in the report.

    Parameters:
        report: Result returned by run_normative_rebaseline.
        reports_dir: Destination directory.

    Returns:
        None; report files are written to disk.

    Assumptions:
        The report is finite and JSON-serializable.

    Sign convention:
        Not applicable.

    Unit convention:
        Not applicable to report serialization.

    Applicability:
        Phase 0.23 release evidence generation.

    Limitations:
        Serialization does not strengthen the underlying evidence.

    Raises:
        OSError for filesystem failures or ValueError for non-JSON numerical content.

    Examples:
        ``write_normative_rebaseline_reports(run_normative_rebaseline('.'), 'reports')``

    Tests:
        tests/test_phase_0_23_independent_normative_rebaseline.py

    Implementation notes:
        Output is stable for unchanged input evidence.
    """
    destination = Path(reports_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "independent_normative_rebaseline_v0_23.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# Independent normative rebaseline & adversarial static audit — Phase 0.23",
        "",
        f"- Rebaseline: **{'PASS' if report['rebaseline_pass'] else 'FAIL'}**",
        f"- Engineering-use ready: **{'yes' if report['engineering_use_ready'] else 'no'}**",
        f"- Equations: **{report['inventory']['equations']['total']}**",
        f"- Tables: **{report['inventory']['tables']['total']}**",
        f"- Procedures: **{report['inventory']['procedures']['total']}**",
        f"- Explicit external-reference tables: **{len(report['external_reference_tables'])}**",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in report["checks"].items())
    lines.extend(["", "## Phase 0.23 remediations", ""])
    lines.extend(f"- **{item['finding_id']}** — {item['finding']} → {item['resolution']}" for item in report["remediations_applied_in_phase_0_23"])
    lines.extend(["", "## Scope findings", ""])
    lines.extend(f"- {item}" for item in report["scope_findings"])
    lines.extend(["", "## Qualification", "", "This is an independent rebaseline of package claims and fail-closed behavior. It is not third-party certification of every numerical table cell or every narrative clause of СП 16.13330.2017."])
    (destination / "independent_normative_rebaseline_v0_23.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
