"""Public API hardening and compatibility audit for Phase 0.24."""

from __future__ import annotations

import ast
import csv
import re
import hashlib
import importlib
import inspect
import json
from pathlib import Path
from typing import Any

from .release_metadata import (
    ENGINEERING_USE_READY,
    PACKAGE_VERSION,
    PARENT_RELEASE,
    RELEASE_QUALIFICATION,
    RELEASE_STAGE,
    STANDARD_TITLE,
)

# Modules containing engineering/normative public functions. Infrastructure is
# intentionally excluded from the engineering API contract, but remains visible
# in the complete freeze as tooling API.
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

_TOOLING_MODULES: tuple[str, ...] = (
    "api_hardening",
    "final_audit",
    "function_level_validation",
    "independent_validation",
    "inventory",
    "normative_rebaseline",
    "runner",
    "schema_validation",
    "validation",
)

_REQUIRED_DOCSTRING_MARKERS: tuple[str, ...] = (
    "Summary:",
    "Standard reference:",
    "Parameters:",
    "Returns:",
    "Applicability:",
    "Limitations:",
    "Tests:",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _public_functions(module_name: str) -> list[tuple[str, Any]]:
    module = importlib.import_module(f"standard_core.{module_name}")
    out: list[tuple[str, Any]] = []
    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            out.append((name, obj))
    return sorted(out, key=lambda item: item[0])


def _call_shape(signature: inspect.Signature | str) -> str:
    """Return the invocation-relevant part of an inspect signature.

    Return annotations are intentionally excluded because Phase 0.24 adds
    missing return typing without changing how callers invoke a function.
    Parameter annotations are retained, making accidental parameter contract
    changes visible.
    """
    text = str(signature)
    return text.split(" -> ", 1)[0]


def _audit_ids(doc: str | None) -> list[str]:
    if not doc:
        return []
    import re
    ids: list[str] = []
    # Accept both the historical multiline field and compact one-line docstrings.
    for match in re.finditer(r"Audit ID:\s*([^\n.]+)", doc):
        value = match.group(1).strip()
        ids.extend(x.strip() for x in value.replace(";", ",").split(",") if x.strip())
    return sorted(set(ids))


def _ast_function_metadata(path: Path) -> dict[str, dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name.startswith("_"):
            continue
        mutable_defaults = []
        for default in list(node.args.defaults) + [x for x in node.args.kw_defaults if x is not None]:
            if isinstance(default, (ast.Dict, ast.List, ast.Set)):
                mutable_defaults.append(ast.unparse(default))
        out[node.name] = {
            "line": node.lineno,
            "has_return_annotation": node.returns is not None,
            "parameter_annotations_complete": all(
                arg.annotation is not None
                for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                if arg.arg not in {"self", "cls"}
            ),
            "has_varargs": node.args.vararg is not None,
            "has_varkw": node.args.kwarg is not None,
            "mutable_defaults": mutable_defaults,
        }
    return out


def _build_entry(module_name: str, name: str, obj: Any, root: Path) -> dict[str, Any]:
    signature = inspect.signature(obj)
    doc = inspect.getdoc(obj) or ""
    source_path = root / "standard_core" / f"{module_name}.py"
    ast_meta = _ast_function_metadata(source_path).get(name, {})
    api_class = "engineering" if module_name in _ENGINEERING_MODULES else "tooling"
    return {
        "kind": "function",
        "module": f"standard_core.{module_name}",
        "name": name,
        "api_class": api_class,
        "signature": str(signature),
        "call_shape": _call_shape(signature),
        "returns": None if signature.return_annotation is inspect.Signature.empty else inspect.formatannotation(signature.return_annotation),
        "audit_ids": _audit_ids(doc),
        "source_line": ast_meta.get("line"),
        "parameter_annotations_complete": bool(ast_meta.get("parameter_annotations_complete")),
        "return_annotation_present": bool(ast_meta.get("has_return_annotation")),
        "varargs_present": bool(ast_meta.get("has_varargs")),
        "varkw_present": bool(ast_meta.get("has_varkw")),
        "mutable_defaults": ast_meta.get("mutable_defaults", []),
        "docstring_markers_missing": [marker for marker in _REQUIRED_DOCSTRING_MARKERS if marker not in doc] if api_class == "engineering" else [],
    }


def _compatibility_against_freeze(root: Path, entries: list[dict[str, Any]], relative_path: str) -> dict[str, Any]:
    baseline_path = root / relative_path
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    old = {(item["module"], item["name"]): item for item in baseline["entries"]}
    current = {(item["module"], item["name"]): item for item in entries}

    removed = sorted([f"{m}.{n}" for m, n in set(old) - set(current)])
    added = sorted([f"{m}.{n}" for m, n in set(current) - set(old)])
    incompatible_call_shape: list[dict[str, str]] = []
    annotation_only_changes: list[dict[str, str]] = []
    unchanged = 0
    for key in sorted(set(old) & set(current)):
        old_sig = old[key]["signature"]
        cur_sig = current[key]["signature"]
        old_call = _call_shape(old_sig)
        cur_call = current[key]["call_shape"]
        if old_call != cur_call:
            incompatible_call_shape.append(
                {
                    "object": f"{key[0]}.{key[1]}",
                    "baseline_signature": old_sig,
                    "current_signature": cur_sig,
                }
            )
        elif old_sig != cur_sig:
            annotation_only_changes.append(
                {
                    "object": f"{key[0]}.{key[1]}",
                    "baseline_signature": old_sig,
                    "current_signature": cur_sig,
                    "classification": "nonbreaking_return_annotation_hardening",
                }
            )
        else:
            unchanged += 1

    added_engineering = [
        item for item in added
        if current[tuple(item.rsplit(".", 1))]["api_class"] == "engineering"
    ]
    return {
        "baseline_file": baseline_path.relative_to(root).as_posix(),
        "baseline_sha256": _sha256(baseline_path),
        "baseline_object_count": len(old),
        "removed_objects": removed,
        "added_objects": added,
        "added_engineering_objects": added_engineering,
        "incompatible_call_shape_changes": incompatible_call_shape,
        "annotation_only_changes": annotation_only_changes,
        "unchanged_full_signatures": unchanged,
        "backward_call_compatibility_pass": not removed and not incompatible_call_shape and not added_engineering,
    }


def _implementation_map_audit_ids(root: Path, entries: list[dict[str, Any]]) -> None:
    """Augment function entries with trace links from the canonical implementation map."""
    path = root / "audit_inventory" / "implementation_map.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for entry in entries:
        name = entry["name"]
        mapped: list[str] = []
        pattern = re.compile(r"\b" + re.escape(name) + r"\b")
        for row in rows:
            target = row.get("implemented_function_or_data_file", "") or ""
            if pattern.search(target):
                audit_id = (row.get("audit_id") or "").strip()
                if audit_id:
                    mapped.append(audit_id)
        entry["implementation_map_audit_ids"] = sorted(set(mapped))
        entry["trace_audit_ids"] = sorted(set(entry.get("audit_ids", [])) | set(mapped))


def run_api_hardening(root: str | Path) -> dict[str, Any]:
    """
    Summary:
        Audit, classify, and freeze the Phase 0.24 public Python API.

    Standard reference:
        СП 16.13330.2017 implementation release engineering; no normative formula is changed by this audit. Audit ID: RELEASE-API-024-001.

    Parameters:
        root: Package root containing ``standard_core`` and the frozen v0.22 API baseline.

    Returns:
        Structured API-hardening report and canonical freeze content.

    Assumptions:
        The v0.22 freeze is an immutable compatibility baseline and public names are module-level callables not beginning with an underscore.

    Sign convention:
        Not applicable; compatibility findings are categorical.

    Unit convention:
        Counts are dimensionless API-object counts.

    Applicability:
        Phase 0.24 cumulative reconstructed release.

    Limitations:
        Call-shape compatibility does not prove semantic backward compatibility of every result value.

    Raises:
        FileNotFoundError or ValueError when mandatory package/freeze evidence is absent or malformed.

    Examples:
        ``run_api_hardening('.')['api_hardening_pass']``

    Tests:
        tests/test_phase_0_24_release_api_hardening.py

    Implementation notes:
        Return-annotation-only changes are separated from invocation call-shape changes and are not treated as breaking calls.
    """
    root_path = Path(root)
    modules = list(_ENGINEERING_MODULES) + list(_TOOLING_MODULES)
    entries: list[dict[str, Any]] = []
    for module_name in modules:
        module_path = root_path / "standard_core" / f"{module_name}.py"
        if not module_path.exists():
            # function_level_validation is created in the same phase; fail closed
            # only when a declared module should exist in a finalized package.
            continue
        for name, obj in _public_functions(module_name):
            entries.append(_build_entry(module_name, name, obj, root_path))
    entries.sort(key=lambda item: (item["module"], item["name"]))
    _implementation_map_audit_ids(root_path, entries)

    engineering = [item for item in entries if item["api_class"] == "engineering"]
    tooling = [item for item in entries if item["api_class"] == "tooling"]

    missing_param_annotations = [f"{x['module']}.{x['name']}" for x in engineering if not x["parameter_annotations_complete"]]
    missing_return_annotations = [f"{x['module']}.{x['name']}" for x in engineering if not x["return_annotation_present"]]
    varargs = [f"{x['module']}.{x['name']}" for x in engineering if x["varargs_present"] or x["varkw_present"]]
    mutable_defaults = [
        {"object": f"{x['module']}.{x['name']}", "defaults": x["mutable_defaults"]}
        for x in engineering if x["mutable_defaults"]
    ]
    incomplete_doc_contract = [
        {"object": f"{x['module']}.{x['name']}", "missing": x["docstring_markers_missing"]}
        for x in engineering if x["docstring_markers_missing"]
    ]
    no_audit_id = [f"{x['module']}.{x['name']}" for x in engineering if not x["trace_audit_ids"]]

    compatibility = _compatibility_against_freeze(root_path, entries, "data/api_freeze_v0_22_reconstructed_r1.json")
    parent_compatibility = _compatibility_against_freeze(
        root_path, entries, "data/api_freeze_v0_23_parent_reconstructed_from_parent_package.json"
    )
    checks = {
        "engineering_parameter_annotations_complete": not missing_param_annotations,
        "engineering_return_annotations_complete": not missing_return_annotations,
        "engineering_has_no_varargs_or_varkw": not varargs,
        "engineering_has_no_mutable_defaults": not mutable_defaults,
        "engineering_docstring_contract_complete": not incomplete_doc_contract,
        "engineering_normative_audit_id_trace_complete": not no_audit_id,
        "v0_22_public_call_shapes_backward_compatible": compatibility["backward_call_compatibility_pass"],
        "parent_v0_23_public_call_shapes_backward_compatible": parent_compatibility["backward_call_compatibility_pass"],
    }

    freeze = {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "standard": STANDARD_TITLE,
        "generation": "runtime_introspection_plus_ast_contract_audit",
        "public_object_count": len(entries),
        "engineering_public_function_count": len(engineering),
        "tooling_public_function_count": len(tooling),
        "entries": entries,
    }

    return {
        "package_version": PACKAGE_VERSION,
        "release_stage": RELEASE_STAGE,
        "release_qualification": RELEASE_QUALIFICATION,
        "parent_release": PARENT_RELEASE,
        "engineering_use_ready": ENGINEERING_USE_READY,
        "scope": "Release/API hardening; no claim of full engineering certification.",
        "public_api": {
            "total_functions": len(entries),
            "engineering_functions": len(engineering),
            "tooling_functions": len(tooling),
            "missing_parameter_annotations": missing_param_annotations,
            "missing_return_annotations": missing_return_annotations,
            "varargs_or_varkw": varargs,
            "mutable_defaults": mutable_defaults,
            "incomplete_docstring_contract": incomplete_doc_contract,
            "functions_without_audit_id": no_audit_id,
        },
        "compatibility_with_v0_22_freeze": compatibility,
        "compatibility_with_parent_v0_23_freeze": parent_compatibility,
        "checks": checks,
        "api_hardening_pass": all(checks.values()),
        "freeze": freeze,
    }


def write_api_hardening_reports(report: dict[str, Any], root: str | Path) -> None:
    """
    Summary:
        Write deterministic Phase 0.24 API-freeze and API-hardening reports.

    Standard reference:
        СП 16.13330.2017 package release engineering. Audit ID: RELEASE-API-024-002.

    Parameters:
        report: Result returned by :func:`run_api_hardening`.
        root: Package root receiving ``data`` and ``reports`` artifacts.

    Returns:
        None; JSON and Markdown evidence files are written.

    Assumptions:
        The supplied report was generated from the same source tree being materialized.

    Sign convention:
        Not applicable.

    Unit convention:
        Not applicable to serialization; counts remain dimensionless.

    Applicability:
        Phase 0.24 cumulative reconstructed release.

    Limitations:
        Serialization does not strengthen the underlying compatibility evidence.

    Raises:
        OSError or ValueError when deterministic evidence cannot be written/serialized.

    Examples:
        ``write_api_hardening_reports(run_api_hardening('.'), '.')``

    Tests:
        tests/test_phase_0_24_release_api_hardening.py

    Implementation notes:
        JSON is emitted with ``allow_nan=False`` to keep the release evidence standards-compliant and fail closed on non-finite values.
    """
    root_path = Path(root)
    data_dir = root_path / "data"
    reports_dir = root_path / "reports"
    data_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    freeze_path = data_dir / "api_freeze_v0_24_release_api_hardening_reconstructed_r1.json"
    freeze_path.write_text(json.dumps(report["freeze"], ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    report_copy = dict(report)
    report_copy.pop("freeze", None)
    (reports_dir / "api_hardening_report_v0_24.json").write_text(
        json.dumps(report_copy, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    compat = report["compatibility_with_v0_22_freeze"]
    parent_compat = report["compatibility_with_parent_v0_23_freeze"]
    lines = [
        "# API hardening report — Phase 0.24",
        "",
        f"- Verdict: **{'PASS' if report['api_hardening_pass'] else 'FAIL'}**",
        f"- Engineering public functions: **{report['public_api']['engineering_functions']}**",
        f"- Tooling public functions: **{report['public_api']['tooling_functions']}**",
        f"- Backward-compatible v0.22 call shapes: **{'PASS' if compat['backward_call_compatibility_pass'] else 'FAIL'}**",
        f"- Backward-compatible immediate-parent v0.23 call shapes: **{'PASS' if parent_compat['backward_call_compatibility_pass'] else 'FAIL'}**",
        f"- Non-breaking return-annotation hardenings vs parent: **{len(parent_compat['annotation_only_changes'])}**",
        f"- Removed public objects: **{len(compat['removed_objects'])}**",
        f"- Incompatible call-shape changes: **{len(compat['incompatible_call_shape_changes'])}**",
        "",
        "The freeze distinguishes engineering API from release/validation tooling. Return-annotation additions are explicitly classified as non-breaking because invocation call shapes are unchanged.",
    ]
    (reports_dir / "api_hardening_report_v0_24.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
