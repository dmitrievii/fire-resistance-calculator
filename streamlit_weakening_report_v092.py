"""v0.92 section-weakening engineering narrative.

Presentation only.  Net-property values come from the typed calculation evidence
stored by :mod:`standard_core.fire_ui14_section_weakening`; the SP16 Eq.(45)
result comes from the executed ``sp16_shear_hole_alpha45`` quantity.  This
module formats ``formula -> numerical substitution -> recorded result`` and
never evaluates geometry or Eq.(45) independently.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.fire_ui14_section_weakening import WEAKENING_TRACE_SCHEMA


def _fmt(value: Any) -> str:
    return _v089._fmt_number(value)


def _result_value(step: Mapping[str, Any]) -> Any:
    result = step.get("result")
    return result.get("value") if isinstance(result, Mapping) else None


def _result_unit(step: Mapping[str, Any]) -> str:
    result = step.get("result")
    if not isinstance(result, Mapping):
        return ""
    return {
        "mm2": "мм²",
        "mm3": "мм³",
        "mm4": "мм⁴",
    }.get(str(result.get("unit") or ""), str(result.get("unit") or ""))


def _step_map(trace: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in trace.get("steps") or []:
        if isinstance(row, Mapping) and isinstance(row.get("formula_id"), str):
            result[str(row["formula_id"])] = row
    return result


def _axis_map(trace: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    """Map historical geometry source axes to active z/y only from runtime evidence."""
    major = trace.get("major_axis_is_x")
    if major is True:
        return {"x": ("z", "сильной"), "y": ("y", "слабой")}
    if major is False:
        return {"x": ("y", "слабой"), "y": ("z", "сильной")}
    # Fail-safe presentation: do not invent active-axis meaning when runtime did
    # not publish the major/minor relation.
    return {"x": ("x", "исходной каталожной"), "y": ("y", "исходной каталожной")}


def _equation(formula: str, substitution: str) -> list[str]:
    return [f"$$ {formula} $$", "", f"$$ {substitution} $$", ""]


def _identity_section(trace: Mapping[str, Any]) -> str:
    steps = _step_map(trace)
    lines = [
        "### 1.3 Ослабления сечения",
        "",
        "Ослабления в активном поперечном сечении отсутствуют. Нетто-характеристики приняты равными брутто-характеристикам.",
        "",
    ]
    for key in ("A_NET_IDENTITY", "I_XN_IDENTITY", "I_YN_IDENTITY"):
        step = steps.get(key)
        if not step:
            continue
        formula = str(step.get("formula_latex") or "")
        value = _result_value(step)
        unit = _result_unit(step)
        if formula and value is not None:
            lines.extend(_equation(formula, f"{formula}={_fmt(value)}\\;\\mathrm{{{unit}}}"))
    lines.append("Коэффициент ослабления стенки по сдвигу в этой ветви: **$α_h=1$**.")
    return "\n".join(lines).strip()


def _hole_section(trace: Mapping[str, Any], alpha_hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None) -> str:
    steps = _step_map(trace)
    axes = _axis_map(trace)
    sx, sx_name = axes["x"]
    sy, sy_name = axes["y"]

    lines = [
        "### 1.3 Ослабления сечения",
        "",
        "Принята упрощённая геометрическая модель: одно круглое болтовое отверстие в стенке представлено в активном поперечном сечении центральным удалённым прямоугольником $d\\times t_w$. Центр отверстия лежит на главных осях, поэтому перенос по теореме Штейнера не требуется.",
        "",
        "Ниже геометрическое уменьшение $A$, $I$ и $W$ показано отдельно от нормативной формулы (45) СП 16. Формула (45) используется только для коэффициента ослабления при сдвиге.",
        "",
    ]

    step = steps.get("REMOVED_AREA_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(
                r"\Delta A=d\,t_w",
                rf"\Delta A={_fmt(inp.get('d'))}\cdot {_fmt(inp.get('t_w'))}={_fmt(result)}\;\mathrm{{мм^2}}",
            ))

    step = steps.get("A_NET_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(
                r"A_n=A-\Delta A",
                rf"A_n={_fmt(inp.get('A'))}-{_fmt(inp.get('Delta_A'))}={_fmt(result)}\;\mathrm{{мм^2}}",
            ))

    step = steps.get("I_XN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend([
                f"Для {sx_name} главной оси **{sx}-{sx}**:",
                "",
                *_equation(
                    rf"I_{{{sx},n}}=I_{sx}-\frac{{t_w d^3}}{{12}}",
                    rf"I_{{{sx},n}}={_fmt(inp.get('I_x'))}-{_fmt(inp.get('Delta_I_x'))}={_fmt(result)}\;\mathrm{{мм^4}}",
                ),
            ])

    step = steps.get("I_YN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend([
                f"Для {sy_name} главной оси **{sy}-{sy}**:",
                "",
                *_equation(
                    rf"I_{{{sy},n}}=I_{sy}-\frac{{d t_w^3}}{{12}}",
                    rf"I_{{{sy},n}}={_fmt(inp.get('I_y'))}-{_fmt(inp.get('Delta_I_y'))}={_fmt(result)}\;\mathrm{{мм^4}}",
                ),
            ])

    step = steps.get("W_XN_MIN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(
                rf"W_{{{sx},n,min}}=\min\left(\frac{{I_{{{sx},n}}}}{{y_+}},\frac{{I_{{{sx},n}}}}{{y_-}}\right)",
                rf"W_{{{sx},n,min}}=\min\left(\frac{{{_fmt(inp.get('I_xn'))}}}{{{_fmt(inp.get('y_pos'))}}},\frac{{{_fmt(inp.get('I_xn'))}}}{{{_fmt(inp.get('y_neg'))}}}\right)={_fmt(result)}\;\mathrm{{мм^3}}",
            ))

    step = steps.get("W_YN_MIN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(
                rf"W_{{{sy},n,min}}=\min\left(\frac{{I_{{{sy},n}}}}{{x_+}},\frac{{I_{{{sy},n}}}}{{x_-}}\right)",
                rf"W_{{{sy},n,min}}=\min\left(\frac{{{_fmt(inp.get('I_yn'))}}}{{{_fmt(inp.get('x_pos'))}}},\frac{{{_fmt(inp.get('I_yn'))}}}{{{_fmt(inp.get('x_neg'))}}}\right)={_fmt(result)}\;\mathrm{{мм^3}}",
            ))

    formula45 = trace.get("sp16_formula45")
    if isinstance(formula45, Mapping) and formula45.get("applicable") is True:
        inputs = formula45.get("inputs") if isinstance(formula45.get("inputs"), Mapping) else {}
        alpha = _v089._row_raw(alpha_hit)
        lines.extend(["#### Коэффициент ослабления стенки при сдвиге по формуле (45) СП 16", ""])
        if isinstance(alpha, (int, float)) and not isinstance(alpha, bool):
            lines.extend(_equation(
                str(formula45.get("formula_latex") or r"\alpha_h=\frac{s}{s-d}"),
                rf"\alpha_h=\frac{{{_fmt(inputs.get('s'))}}}{{{_fmt(inputs.get('s'))}-{_fmt(inputs.get('d'))}}}={_fmt(alpha)}",
            ))
        ref = _v089._ref(alpha_hit[1]) if alpha_hit else ""
        normative_scope = str(formula45.get("normative_scope") or "")
        basis = ref or normative_scope
        if basis:
            lines.extend([f"*Нормативное основание: {basis}.*", ""])

    lines.extend([
        "Геометрическое уменьшение нетто-характеристик выше относится только к принятой упрощённой модели центрального отверстия в стенке; оно не расширяет область применимости формулы (45) на другие типы ослаблений.",
        "",
    ])
    return "\n".join(lines).strip()


def weakening_section(report: Mapping[str, Any]) -> str:
    net_hit = _v089._find_row(report, qids=("net_section_geometry_2d",))
    raw = _v089._row_raw(net_hit)
    if not isinstance(raw, Mapping):
        return ""
    trace = raw.get("calculation_trace")
    if not isinstance(trace, Mapping) or trace.get("schema") != WEAKENING_TRACE_SCHEMA:
        return ""
    route = trace.get("route")
    if route == "identity_no_weakening":
        return _identity_section(trace)
    if route == "representative_central_web_hole":
        alpha_hit = _v089._find_row(report, qids=("sp16_shear_hole_alpha45",))
        return _hole_section(trace, alpha_hit)
    return ""


def replace_weakening_section(markdown: str, report: Mapping[str, Any]) -> str:
    section = weakening_section(report)
    pattern = re.compile(r"(?ms)^### 1\.3 Ослабления сечения\n.*?(?=^### 1\.[4-9]\b|^## 2\.|\Z)")
    if pattern.search(markdown):
        return pattern.sub((section + "\n\n") if section else "", markdown, count=1)
    if not section:
        return markdown
    marker = re.search(r"(?m)^## 2\.", markdown)
    if marker:
        return markdown[: marker.start()] + section + "\n\n" + markdown[marker.start() :]
    return markdown.rstrip() + "\n\n" + section


__all__ = ["replace_weakening_section", "weakening_section"]
