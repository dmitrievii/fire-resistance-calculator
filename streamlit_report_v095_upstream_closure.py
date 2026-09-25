"""v0.95 closure for real runtime material/weakening evidence.

This layer does not invent engineering values.  It consumes the exact executed
net-section trace already stored by FIRE-UI1.4 in ``net_section_geometry_2d`` and
accepts Table-3 gamma_m only when it is explicitly present in executed evidence.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v093_progressive_hotfix as _v093
import streamlit_expertise_report_v094_weakening as _v094


def _rows(report: Mapping[str, Any]):
    yield from _v094._rows(report)


def _hit(report: Mapping[str, Any], *qids: str):
    return _v094._hit(report, *qids)


def _trace_from_runtime(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return the exact FIRE-UI1.4 calculation trace from executed geometry."""
    hit = _hit(report, "net_section_geometry_2d")
    raw = hit[0].get("raw_value") if hit else None
    if isinstance(raw, Mapping):
        trace = raw.get("calculation_trace")
        if isinstance(trace, Mapping):
            return trace
    # Keep compatibility with any future direct trace quantity.
    direct = _hit(report, "section_weakening_trace")
    raw_direct = direct[0].get("raw_value") if direct else None
    return raw_direct if isinstance(raw_direct, Mapping) else None


def _step_lines(step: Mapping[str, Any]) -> list[str]:
    formula = step.get("formula_latex")
    inputs = step.get("inputs") if isinstance(step.get("inputs"), Mapping) else {}
    result = step.get("result") if isinstance(step.get("result"), Mapping) else {}
    if not formula or result.get("value") is None:
        return []
    unit = str(result.get("unit") or "")
    # Build a deterministic substitution from the producer-owned operands.
    subst = str(formula)
    for key, value in sorted(inputs.items(), key=lambda kv: -len(str(kv[0]))):
        subst = re.sub(rf"(?<![A-Za-z]){re.escape(str(key))}(?![A-Za-z])", _v093._fmt(value), subst)
    suffix = f"\\;\\mathrm{{{unit}}}" if unit else ""
    return [f"$$ {formula} $$", "", f"$$ {subst}={_v093._fmt(result['value'])}{suffix} $$", ""]


def _weakening_section(report: Mapping[str, Any]) -> str:
    trace = _trace_from_runtime(report)
    model = _hit(report, "section_weakening_model")
    an = _hit(report, "A_net", "An", "A_n")
    alpha = _hit(report, "sp16_shear_hole_alpha45", "alpha_h")
    if not any((trace, model, an, alpha)):
        return ""
    lines = ["### 1.2 Ослабления поперечного сечения", ""]
    if isinstance(trace, Mapping):
        route = trace.get("route")
        if route == "identity_no_weakening":
            lines.extend(["Ослабления отсутствуют; характеристики нетто равны характеристикам брутто.", ""])
        else:
            basis = trace.get("engineering_basis")
            if basis:
                lines.extend([f"Расчётная модель: {basis}.", ""])
            for step in trace.get("steps") or []:
                if isinstance(step, Mapping):
                    lines.extend(_step_lines(step))
    elif an:
        # Fail visibly rather than pretending that the final An alone is a
        # reproducible weakening calculation.
        lines.extend([
            "**REPORT-EVIDENCE GAP:** runtime опубликовал итоговую площадь нетто, но не передал расчётный trace ослабления. Формула и числовая подстановка намеренно не восстанавливаются presentation-слоем.", "",
            f"Зафиксированный результат: $A_n={_v093._fmt(an[0].get('raw_value'))}\\;\\mathrm{{mm^2}}$.", "",
        ])

    # Formula (45) belongs to its own executed SP16 calculation node.
    if alpha:
        s = _hit(report, "sp16_wall_hole_pitch_s")
        d = _hit(report, "sp16_wall_hole_diameter_d")
        if s and d:
            sv, dv, av = s[0].get("raw_value"), d[0].get("raw_value"), alpha[0].get("raw_value")
            lines.extend([
                "Коэффициент ослабления стенки по формуле (45):", "",
                "$$ \\alpha_h=\\frac{s}{s-d} $$", "",
                f"$$ \\alpha_h=\\frac{{{_v093._fmt(sv)}}}{{{_v093._fmt(sv)}-{_v093._fmt(dv)}}}={_v093._fmt(av)} $$", "",
            ])
    return "\n".join(lines).strip()


def _insert_weakening(text: str, report: Mapping[str, Any]) -> str:
    section = _weakening_section(report)
    if not section:
        return text
    text = re.sub(r"(?ms)^### 1\.2\s+Ослабления.*?(?=^### 1\.[3-9]\s|^## 2\.\s|\Z)", lambda _m: "", text, count=1)
    anchor = re.search(r"(?m)^## 2\.\s", text)
    if anchor:
        return text[:anchor.start()].rstrip() + "\n\n" + section + "\n\n" + text[anchor.start():]
    return text.rstrip() + "\n\n" + section + "\n"


def render(report: Mapping[str, Any], previous) -> str:
    text = previous(report)
    return _insert_weakening(text, report)


__all__ = ["render", "_trace_from_runtime", "_weakening_section"]
