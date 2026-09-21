"""Trace-bound LaTeX presentation for REPORT-IR blocks.

This module performs text formatting only. It never evaluates formulae,
interpolates datasets, converts engineering units, selects a route, or derives a
verdict from a numeric quantity. Substitution placeholders are filled only from
values already captured in the execution trace.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping


def _fmt_trace_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite trace value is not reportable")
        return format(value, ".12g")
    return str(value)


def _fmt_result_scalar(value: Any, precision: int | None) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite trace value is not reportable")
        if isinstance(precision, int) and precision >= 0:
            return f"{value:.{precision}f}"
        return format(value, ".12g")
    return str(value)


def _unit_latex(unit: Any) -> str:
    if not unit or unit == "1":
        return ""
    table = {
        "N": r"\mathrm{N}",
        "kN": r"\mathrm{kN}",
        "mm": r"\mathrm{mm}",
        "m": r"\mathrm{m}",
        "mm2": r"\mathrm{mm^2}",
        "MPa": r"\mathrm{MPa}",
        "min": r"\mathrm{min}",
        "degC": r"{}^\circ\mathrm{C}",
    }
    return r"\;" + table.get(str(unit), rf"\mathrm{{{unit}}}")


def _binding_values(block: Mapping[str, Any]) -> dict[str, Any]:
    evidence = block.get("execution_evidence") or {}
    out: dict[str, Any] = {}
    for row in evidence.get("bindings") or []:
        if not isinstance(row, Mapping) or not row.get("present_in_trace"):
            continue
        variable = row.get("variable")
        if isinstance(variable, str) and variable:
            out[variable] = copy.deepcopy(row.get("raw_value"))
    return out


def _substitute_template(template: str, values: Mapping[str, Any]) -> tuple[str, list[str]]:
    rendered = str(template)
    used: set[str] = set()
    for variable, value in sorted(values.items(), key=lambda item: len(item[0]), reverse=True):
        token = "{" + variable + "}"
        if token in rendered:
            rendered = rendered.replace(token, _fmt_trace_scalar(value))
            used.add(variable)
    missing: list[str] = []
    # Only known trace variables are substituted. Unknown LaTeX braces are left
    # untouched; therefore the renderer never guesses a quantity binding.
    for variable in values:
        token = "{" + variable + "}"
        if token in template and variable not in used:
            missing.append(variable)
    return rendered, sorted(missing)


def build_trace_bound_equation(block: Mapping[str, Any]) -> dict[str, Any] | None:
    """Create a presentation equation from report metadata + trace values only."""
    presentation = block.get("presentation") or {}
    if not isinstance(presentation, Mapping):
        return None
    formula = presentation.get("formula_latex")
    template = presentation.get("substitution_template_latex")
    if not isinstance(formula, str) and not isinstance(template, str):
        return None

    precision_raw = presentation.get("display_precision")
    precision = precision_raw if isinstance(precision_raw, int) and not isinstance(precision_raw, bool) else None
    values = _binding_values(block)
    substitution = None
    missing: list[str] = []
    if isinstance(template, str):
        substitution, missing = _substitute_template(template, values)

    outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
    result_latex = None
    substitution_result = substitution
    verdict = None

    declared_verdict = presentation.get("verdict_quantity_id")
    if isinstance(declared_verdict, str):
        matches = [row for row in outputs if row.get("quantity_id") == declared_verdict]
        if len(matches) == 1 and isinstance(matches[0].get("raw_value"), bool):
            verdict = "PASS" if matches[0]["raw_value"] else "FAIL"
            if substitution_result:
                substitution_result += rf"\quad\Rightarrow\quad\mathrm{{{verdict}}}"

    numeric_outputs = [
        row
        for row in outputs
        if isinstance(row.get("raw_value"), (int, float))
        and not isinstance(row.get("raw_value"), bool)
    ]
    if len(numeric_outputs) == 1:
        row = numeric_outputs[0]
        value = _fmt_result_scalar(row.get("raw_value"), precision)
        unit = _unit_latex(row.get("canonical_unit"))
        result_latex = rf"\boxed{{{value}{unit}}}"
        if substitution_result:
            substitution_result += "=" + result_latex

    return {
        "schema": "fire_report_equation_presentation_v1",
        "formula_latex": formula if isinstance(formula, str) else None,
        "substitution_template_latex": template if isinstance(template, str) else None,
        "substitution_latex": substitution,
        "substitution_result_latex": substitution_result,
        "result_latex": result_latex,
        "explicit_verdict": verdict,
        "display_precision": precision,
        "missing_trace_bindings": missing,
        "binding_source": "execution_trace_only",
        "result_source": "execution_trace_only",
        "evaluated_formula": False,
        "converted_units": False,
    }
