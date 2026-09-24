"""v0.92 section-weakening engineering narrative.

Presentation only.  Net-property values come from typed calculation evidence
stored by the weakening runtime; the SP16 Eq.(45) result comes from the
executed ``sp16_shear_hole_alpha45`` quantity.  Automatic geometry is rendered
as formula -> numerical substitution -> recorded result.  Manual net I/W values
are explicitly labelled as user input and are never dressed up as calculated
formula results.  A_net remains geometry-derived in both modes.
"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.fire_ui14_section_weakening import WEAKENING_TRACE_SCHEMA
from standard_core.fire_ui14_manual_net_v092 import MANUAL_SOURCE_TEXT_RU


def _fmt(value: Any) -> str:
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return f"{int(value):,}".replace(",", " ")
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
        "mm6": "мм⁶",
    }.get(str(result.get("unit") or ""), str(result.get("unit") or ""))


def _unit_text(unit: Any) -> str:
    return {
        "mm2": "мм²",
        "mm3": "мм³",
        "mm4": "мм⁴",
        "mm6": "мм⁶",
    }.get(str(unit or ""), str(unit or ""))


def _step_map(trace: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in trace.get("steps") or []:
        if isinstance(row, Mapping) and isinstance(row.get("formula_id"), str):
            result[str(row["formula_id"])] = row
    return result


def _axis_map(trace: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    major = trace.get("major_axis_is_x")
    if major is True:
        return {"x": ("z", "сильной"), "y": ("y", "слабой")}
    if major is False:
        return {"x": ("y", "слабой"), "y": ("z", "сильной")}
    return {"x": ("x", "исходной каталожной"), "y": ("y", "исходной каталожной")}


def _equation(formula: str, substitution: str) -> list[str]:
    return [f"$$ {formula} $$", "", f"$$ {substitution} $$", ""]


def _formula45_lines(trace: Mapping[str, Any], alpha_hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None) -> list[str]:
    formula45 = trace.get("sp16_formula45")
    if not isinstance(formula45, Mapping) or formula45.get("applicable") is not True:
        return []
    inputs = formula45.get("inputs") if isinstance(formula45.get("inputs"), Mapping) else {}
    alpha = _v089._row_raw(alpha_hit)
    lines = ["#### Коэффициент ослабления стенки при сдвиге по формуле (45) СП 16", ""]
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
    return lines


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
            lines.extend(_equation(r"\Delta A=d\,t_w", rf"\Delta A={_fmt(inp.get('d'))}\cdot {_fmt(inp.get('t_w'))}={_fmt(result)}\;\mathrm{{мм^2}}"))

    step = steps.get("A_NET_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(r"A_n=A-\Delta A", rf"A_n={_fmt(inp.get('A'))}-{_fmt(inp.get('Delta_A'))}={_fmt(result)}\;\mathrm{{мм^2}}"))

    step = steps.get("I_XN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend([f"Для {sx_name} главной оси **{sx}-{sx}**:", "", *_equation(rf"I_{{{sx},n}}=I_{sx}-\frac{{t_w d^3}}{{12}}", rf"I_{{{sx},n}}={_fmt(inp.get('I_x'))}-{_fmt(inp.get('Delta_I_x'))}={_fmt(result)}\;\mathrm{{мм^4}}")])

    step = steps.get("I_YN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend([f"Для {sy_name} главной оси **{sy}-{sy}**:", "", *_equation(rf"I_{{{sy},n}}=I_{sy}-\frac{{d t_w^3}}{{12}}", rf"I_{{{sy},n}}={_fmt(inp.get('I_y'))}-{_fmt(inp.get('Delta_I_y'))}={_fmt(result)}\;\mathrm{{мм^4}}")])

    step = steps.get("W_XN_MIN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(rf"W_{{{sx},n,min}}=\min\left(\frac{{I_{{{sx},n}}}}{{y_+}},\frac{{I_{{{sx},n}}}}{{y_-}}\right)", rf"W_{{{sx},n,min}}=\min\left(\frac{{{_fmt(inp.get('I_xn'))}}}{{{_fmt(inp.get('y_pos'))}}},\frac{{{_fmt(inp.get('I_xn'))}}}{{{_fmt(inp.get('y_neg'))}}}\right)={_fmt(result)}\;\mathrm{{мм^3}}"))

    step = steps.get("W_YN_MIN_CENTRAL_WEB_HOLE")
    if step:
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is not None:
            lines.extend(_equation(rf"W_{{{sy},n,min}}=\min\left(\frac{{I_{{{sy},n}}}}{{x_+}},\frac{{I_{{{sy},n}}}}{{x_-}}\right)", rf"W_{{{sy},n,min}}=\min\left(\frac{{{_fmt(inp.get('I_yn'))}}}{{{_fmt(inp.get('x_pos'))}}},\frac{{{_fmt(inp.get('I_yn'))}}}{{{_fmt(inp.get('x_neg'))}}}\right)={_fmt(result)}\;\mathrm{{мм^3}}"))

    lines.extend(_formula45_lines(trace, alpha_hit))
    lines.extend(["Геометрическое уменьшение нетто-характеристик выше относится только к принятой упрощённой модели центрального отверстия в стенке; оно не расширяет область применимости формулы (45) на другие типы ослаблений.", ""])
    return "\n".join(lines).strip()


def _walk_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_mappings(child)


def _consumer_evidence(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        for row in block.get("outputs") or []:
            if not isinstance(row, Mapping):
                continue
            for mapping in _walk_mappings(row.get("raw_value")):
                candidate = mapping.get("manual_net_property_consumption")
                if isinstance(candidate, Mapping):
                    found.append(candidate)
    return found


def _manual_section(trace: Mapping[str, Any], alpha_hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None, report: Mapping[str, Any]) -> str:
    steps = _step_map(trace)
    lines = ["### 1.3 Ослабления сечения", "", "Для отверстия в стенке площадь нетто определяется из принятой геометрии. Моменты инерции и моменты сопротивления нетто не вычисляются приложением: они заданы как готовые характеристики сечения.", ""]

    for key in ("REMOVED_AREA_CENTRAL_WEB_HOLE", "A_NET_CENTRAL_WEB_HOLE"):
        step = steps.get(key)
        if not step:
            continue
        inp = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
        result = _result_value(step)
        if result is None:
            continue
        if key == "REMOVED_AREA_CENTRAL_WEB_HOLE":
            lines.extend(_equation(r"\Delta A=d\,t_w", rf"\Delta A={_fmt(inp.get('d'))}\cdot {_fmt(inp.get('t_w'))}={_fmt(result)}\;\mathrm{{мм^2}}"))
        else:
            lines.extend(_equation(r"A_n=A-\Delta A", rf"A_n={_fmt(inp.get('A'))}-{_fmt(inp.get('Delta_A'))}={_fmt(result)}\;\mathrm{{мм^2}}"))

    manual_rows = [row for row in trace.get("manual_properties") or [] if isinstance(row, Mapping)]
    if manual_rows:
        lines.extend(["#### Готовые характеристики нетто", "", f"Источник: **{MANUAL_SOURCE_TEXT_RU}**.", ""])
        for row in manual_rows:
            symbol = str(row.get("canonical_symbol") or row.get("canonical_input_id") or "")
            value = row.get("value")
            unit = _unit_text(row.get("unit"))
            source_kind = str(row.get("source_kind") or "")
            if source_kind == "DERIVED_FROM_USER_INPUT_NET_PROPERTIES":
                lines.append(f"- ${symbol}$ = **{_fmt(value)} {unit}** — минимум из введённой пары пластических характеристик.")
            else:
                lines.append(f"- ${symbol}$ = **{_fmt(value)} {unit}** — {MANUAL_SOURCE_TEXT_RU}.")
        lines.append("")

    consumers = _consumer_evidence(report)
    if consumers:
        consumed: dict[str, Any] = {}
        for evidence in consumers:
            values = evidence.get("consumed_runtime_quantities")
            if isinstance(values, Mapping):
                consumed.update(values)
        if consumed:
            lines.extend(["#### Использование в выполненных проверках СП 16", ""])
            labels = {"A_net": "A_n", "I_xn": "I_{x,n} (внутренний transport)", "I_yn": "I_{y,n} (внутренний transport)", "W_xn_min": "W_{x,n,min} (внутренний transport)", "W_yn_min": "W_{y,n,min} (внутренний transport)"}
            for key, value in consumed.items():
                if key in labels:
                    lines.append(f"- ${labels[key]}$ = **{_fmt(value)}**.")
            lines.append("")

    lines.extend(_formula45_lines(trace, alpha_hit))
    lines.append("Ручной ввод нетто-характеристик не превращается в вычисленную приложением формулу: отчёт сохраняет provenance пользовательского значения.")
    return "\n".join(lines).strip()


def weakening_section(report: Mapping[str, Any]) -> str:
    net_hit = _v089._find_row(report, qids=("net_section_geometry_2d",))
    alpha_hit = _v089._find_row(report, qids=("sp16_shear_hole_alpha45",))
    raw = _v089._row_raw(net_hit)
    if not isinstance(raw, Mapping):
        return ""
    trace = raw.get("calculation_trace")
    if not isinstance(trace, Mapping) or trace.get("schema") != WEAKENING_TRACE_SCHEMA:
        return ""
    route = str(trace.get("route") or "")
    if route == "identity_no_weakening":
        return _identity_section(trace)
    if route == "representative_central_web_hole":
        return _hole_section(trace, alpha_hit)
    if route == "manual_net_properties":
        return _manual_section(trace, alpha_hit, report)
    return ""


def replace_weakening_section(base: str, report: Mapping[str, Any]) -> str:
    replacement = weakening_section(report)
    if not replacement:
        return base
    pattern = re.compile(r"(?ms)^### 1\.3 Ослабления сечения\s*.*?(?=^### 1\.4\s|^## 2\.|\Z)")
    if pattern.search(base):
        return pattern.sub(replacement + "\n\n", base, count=1)
    marker = "### 1.2"
    pos = base.find(marker)
    if pos >= 0:
        next_section = base.find("\n## 2.", pos)
        if next_section >= 0:
            return base[:next_section].rstrip() + "\n\n" + replacement + "\n\n" + base[next_section:].lstrip()
    return base.rstrip() + "\n\n" + replacement


__all__ = ["replace_weakening_section", "weakening_section"]
