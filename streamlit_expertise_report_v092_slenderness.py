"""v0.92 trace-bound SP16 Table-32 limiting-slenderness report block.

This presentation layer reads only the calculation trace attached by the MECH7
binder evidence wrapper. It never chooses the governing axis, evaluates alpha,
looks up Table 32, applies the group-4 factor, computes utilization, or infers
PASS/FAIL.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.sp16_mech7_v092_slenderness_evidence import (
    EVIDENCE_KEY,
    TRACE_SCHEMA,
)
from streamlit_expertise_report_v092 import compact_engineering_markdown
from streamlit_expertise_report_v092_zy import render_expertise_narrative_markdown_v092_zy

_HEADING_RE = re.compile(r"(?m)^### 3\.2 Проверка центрального сжатия и определяющий результат\s*$\n?")


def _fmt(value: Any, digits: int = 6) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"numeric Table-32 evidence expected, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite Table-32 evidence is not reportable")
    return format(number, f".{digits}g")


def _trace(report: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]] | None:
    hit = _v089._find_row(report, qids=("sp16_mech7_primary_evidence",))
    if not hit:
        return None
    bundle = _v089._row_raw(hit)
    if not isinstance(bundle, Mapping):
        return None
    evidence = bundle.get("evidence")
    row = evidence.get(EVIDENCE_KEY) if isinstance(evidence, Mapping) else None
    if not isinstance(row, Mapping) or row.get("status") not in {"PASS", "FAIL"}:
        return None
    trace = row.get("calculation_trace")
    if not isinstance(trace, Mapping):
        raise ValueError("v0.92 Table-32 report: completed binder evidence has no calculation trace")
    if trace.get("schema") != TRACE_SCHEMA:
        raise ValueError("v0.92 Table-32 report: calculation trace schema mismatch")
    if row.get("calculation_trace_validated_against_binder") is not True:
        raise ValueError("v0.92 Table-32 report: trace is not validated against binder")
    check = trace.get("check")
    if not isinstance(check, Mapping):
        raise ValueError("v0.92 Table-32 report: trace check block is absent")
    if bool(check.get("pass")) is not bool(row.get("pass")):
        raise ValueError("v0.92 Table-32 report: trace/binder verdict mismatch")
    return trace, row


def limiting_slenderness_section(report: Mapping[str, Any]) -> str:
    bound = _trace(report)
    if bound is None:
        return ""
    trace, row = bound

    inputs = trace.get("inputs")
    alpha = trace.get("alpha")
    limit = trace.get("limiting_slenderness")
    actual = trace.get("actual_slenderness")
    check = trace.get("check")
    formula = trace.get("table32_row_formula")
    if not all(isinstance(x, Mapping) for x in (inputs, alpha, limit, actual, check, formula)):
        raise ValueError("v0.92 Table-32 report: incomplete typed calculation trace")

    row_id = str(trace.get("table32_row_id") or "")
    if not row_id:
        raise ValueError("v0.92 Table-32 report: Table-32 row id is absent")
    phi_axis = str(alpha.get("governing_phi_axis") or "")
    lambda_axis = str(actual.get("governing_axis") or "")
    if phi_axis not in {"z", "y"} or lambda_axis not in {"z", "y"}:
        raise ValueError("v0.92 Table-32 report: governing axes are invalid")

    n = _fmt(inputs.get("N_magnitude_n"))
    phi = _fmt(alpha.get("governing_phi"))
    area = _fmt(inputs.get("A_gross_mm2"))
    ry = _fmt(inputs.get("Ry_n_mm2"))
    gamma_c = _fmt(inputs.get("gamma_c"))
    alpha_raw = _fmt(alpha.get("raw"))
    alpha_result = _fmt(alpha.get("result"))
    lambda_z = _fmt(actual.get("lambda_z"))
    lambda_y = _fmt(actual.get("lambda_y"))
    lambda_actual = _fmt(actual.get("result"))
    lambda_u_base = _fmt(limit.get("base"))
    lambda_u = _fmt(limit.get("result"))
    utilization = _fmt(check.get("utilization"))
    verdict = "PASS" if check.get("pass") is True else "FAIL"

    lines = [
        "#### Предельная гибкость по таблице 32",
        "",
        f"Выбранная категория: **таблица 32, строка {row_id}**. "
        + ("Для элемента применено увеличение по п. 10.4.2 (группа 4)." if trace.get("group4_classification") is True else "Увеличение для группы 4 не применено."),
        "",
        f"Для вычисления $\alpha$ runtime использовал минимальный коэффициент устойчивости по оси **{phi_axis}**; "
        f"для проверки фактической гибкости — максимальную $\lambda$ по оси **{lambda_axis}**.",
        "",
        r"$$\alpha_{raw}=\frac{|N|}{\varphi A R_y\gamma_c}"
        + rf"=\frac{{{n}}}{{{phi}\cdot {area}\cdot {ry}\cdot {gamma_c}}}={alpha_raw}$$",
        "",
        rf"$$\alpha=\max(\alpha_{{raw}},0.5)=\max({alpha_raw},0.5)={alpha_result}$$",
        "",
    ]

    expression = str(formula.get("expression") or "")
    kind = formula.get("kind")
    if kind == "linear":
        constant = _fmt(formula.get("constant"))
        coefficient = _fmt(formula.get("alpha_coefficient"))
        sign = "+" if float(formula.get("alpha_coefficient")) >= 0.0 else "-"
        coeff_abs = _fmt(abs(float(formula.get("alpha_coefficient"))))
        lines.extend(
            [
                f"Строка {row_id} таблицы 32: `{expression}`.",
                "",
                rf"$$\lambda_{{u,base}}={constant}{sign}{coeff_abs}\alpha"
                rf"={constant}{sign}{coeff_abs}\cdot {alpha_result}={lambda_u_base}$$",
                "",
            ]
        )
    elif kind == "constant":
        lines.extend(
            [
                f"Строка {row_id} таблицы 32 задаёт постоянное значение `{expression}`.",
                "",
                rf"$$\lambda_{{u,base}}={lambda_u_base}$$",
                "",
            ]
        )
    else:
        raise ValueError("v0.92 Table-32 report: unsupported row formula kind")

    if trace.get("group4_classification") is True:
        factor = _fmt(limit.get("group4_factor"))
        lines.extend(
            [
                rf"$$\lambda_u={factor}\lambda_{{u,base}}={factor}\cdot {lambda_u_base}={lambda_u}$$",
                "",
            ]
        )
    else:
        lines.extend([rf"$$\lambda_u=\lambda_{{u,base}}={lambda_u}$$", ""])

    lines.extend(
        [
            rf"$$\lambda=\max(\lambda_z,\lambda_y)=\max({lambda_z},{lambda_y})={lambda_actual}\quad(\text{{ось }}{lambda_axis})$$",
            "",
            rf"$$\eta_\lambda=\frac{{\lambda}}{{\lambda_u}}=\frac{{{lambda_actual}}}{{{lambda_u}}}={utilization}$$",
            "",
            f"**{verdict}:** $\lambda {'\\le' if verdict == 'PASS' else '>'} \lambda_u$. "
            f"Статус взят из MECH7 binder evidence, а не определён presentation-слоем.",
            "",
            f"*Нормативное основание: {trace.get('normative_basis')}.*",
            "",
        ]
    )
    # Cross-check presentation reads the same utilization but never derives it.
    if not math.isclose(float(row.get("utilization")), float(check.get("utilization")), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("v0.92 Table-32 report: displayed utilization differs from binder")
    return "\n".join(lines)


def inject_limiting_slenderness(markdown: str, report: Mapping[str, Any]) -> str:
    section = limiting_slenderness_section(report)
    text = str(markdown or "")
    if not section:
        return text
    match = _HEADING_RE.search(text)
    if not match:
        return compact_engineering_markdown(text.rstrip() + "\n\n" + section) + "\n"
    insertion = match.group(0) + "\n" + section + "\n"
    text = text[: match.start()] + insertion + text[match.end() :]
    return compact_engineering_markdown(text) + "\n"


def render_expertise_narrative_markdown_v092_slenderness(report: Mapping[str, Any]) -> str:
    base = render_expertise_narrative_markdown_v092_zy(report)
    return inject_limiting_slenderness(base, report)


__all__ = [
    "inject_limiting_slenderness",
    "limiting_slenderness_section",
    "render_expertise_narrative_markdown_v092_slenderness",
]
