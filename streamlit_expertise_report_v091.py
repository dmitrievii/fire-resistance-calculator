"""v0.91 presentation refinement for final-SP554 §9.2 mechanics.

Presentation only.  The module consumes the already executed v0.91 mechanical
runtime evidence and inserts the governing SP16 axes and the fire-slenderness
substitution into the engineering narrative.  It performs no independent
capacity, temperature, thermal or compliance calculation.
"""
from __future__ import annotations

from typing import Any, Mapping

from streamlit_expertise_report_v090_thermal_refinement import (
    _CRITICAL_HEADING,
    _mechanical_fire_result,
    render_expertise_narrative_markdown_v090_thermal_refinement as _render_previous,
)


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _fmt(value: Any) -> str:
    number = _num(value)
    if number is None:
        return str(value)
    return f"{number:.6g}"


def _axis_label(axis: str) -> str:
    return {"z": "z (сильная)", "y": "y (слабая)"}.get(axis, axis)


def _v091_axis_block(report: Mapping[str, Any]) -> str:
    result = _mechanical_fire_result(report)
    if not isinstance(result, Mapping):
        return ""
    trace = result.get("route_trace")
    if not isinstance(trace, Mapping) or trace.get("route") != "central_compression":
        return ""
    axes = trace.get("axes")
    if not isinstance(axes, Mapping):
        return ""

    strength_axis = str(trace.get("governing_strength_axis", ""))
    stiffness_axis = str(trace.get("governing_stiffness_axis", ""))
    strength_state = axes.get(strength_axis)
    stiffness_state = axes.get(stiffness_axis)
    if not isinstance(strength_state, Mapping) or not isinstance(stiffness_state, Mapping):
        return ""

    e_n = _num(trace.get("E_n_mm2"))
    ryn = None
    candidates = result.get("gamma_T_candidates")
    if isinstance(candidates, list) and candidates and isinstance(candidates[0], Mapping):
        details = candidates[0].get("details")
        if isinstance(details, Mapping):
            ryn = _num(details.get("Ryn_n_mm2"))
    lambda_geom = _num(strength_state.get("lambda_geom"))
    lambda_bar = _num(strength_state.get("lambda_bar_fire"))
    phi = _num(strength_state.get("phi_fire"))
    curve = strength_state.get("curve")
    gamma_e = _num(stiffness_state.get("gamma_e"))

    lines = [
        "#### Определяющие оси по п. 9.2",
        "",
        f"- по прочности / коэффициенту $φ$: **ось {_axis_label(strength_axis)}**;",
        f"- по устойчивости / коэффициенту $γ_E$: **ось {_axis_label(stiffness_axis)}**.",
        "",
    ]
    if e_n is not None:
        lines.extend([
            f"Для стали в этой ветви принято нормативное **$E={_fmt(e_n)}$ Н/мм²** "
            "(СП 16.13330.2017, приложение Б, таблица Б.1); пользовательское `E_norm` не используется.",
            "",
        ])
    if None not in (lambda_geom, lambda_bar, ryn, e_n):
        lines.extend([
            "Для определяющей по прочности оси относительная гибкость при пожаре показана как "
            "«формула = подстановка = результат»: ",
            "",
            rf"$\bar{{λ}}_{{{strength_axis}}}=λ_{{{strength_axis}}}\sqrt{{R_{{yn}}/E}}"
            rf"={_fmt(lambda_geom)}\sqrt{{{_fmt(ryn)}/{_fmt(e_n)}}}={_fmt(lambda_bar)}$.",
            "",
        ])
    if lambda_bar is not None and phi is not None:
        lines.extend([
            rf"$φ_{{{strength_axis}}}=φ(\bar{{λ}}_{{{strength_axis}}},\;тип\;{curve})"
            rf"=φ({_fmt(lambda_bar)},\;{curve})={_fmt(phi)}$.",
            "",
        ])
    if gamma_e is not None:
        lines.extend([
            f"Для определяющей по устойчивости оси runtime получил "
            f"**$γ_{{E,{stiffness_axis}}}={_fmt(gamma_e)}$**; именно эта ось передана в независимую "
            "инверсию температурной зависимости модуля упругости.",
            "",
        ])
    return "\n".join(lines).rstrip()


def render_expertise_narrative_markdown_v091(report: Mapping[str, Any]) -> str:
    markdown = _render_previous(report)
    block = _v091_axis_block(report)
    if not block:
        return markdown
    marker = _CRITICAL_HEADING
    if marker not in markdown:
        return markdown
    return markdown.replace(marker, marker + "\n\n" + block, 1)


__all__ = ["render_expertise_narrative_markdown_v091", "_v091_axis_block"]
