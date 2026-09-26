"""v0.97 material derivation closure for the active expertise report."""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v090_install as _report
import streamlit_expertise_report_v093_progressive_hotfix as _v093
from standard_core.material_report_v097 import TRACE_QID, augment_from_session

_INSTALLED = "_fire_v097_material_report_derivation_installed"
_CHAPTER_2 = re.compile(r"(?ms)^## 2\.\s.*?(?=^## [3-9]\.\s|^## Текущий незавершённый шаг|\Z)")


def _trace(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    hit = _v093._find(report, TRACE_QID)
    value = _v093._raw(hit) if hit else None
    return value if isinstance(value, Mapping) else None


def _fmt(value: Any) -> str:
    return _v093._fmt(value)


def _material_chapter_v097(report: Mapping[str, Any]) -> str:
    trace = _trace(report)
    if trace is None:
        return ""

    category = str(trace.get("material_safety_category") or "")
    category_label = _v093._MATERIAL_SAFETY_LABELS.get(category, category)
    gamma_m = trace.get("gamma_m")
    source_table = str(trace.get("source_table") or "")
    grade = str(trace.get("steel_grade") or "")
    product_label = str(trace.get("product_form_label") or trace.get("product_form") or "")
    interval_label = str(trace.get("thickness_interval_label") or "")
    ryn = trace.get("Ryn_MPa")
    run = trace.get("Run_MPa")
    ry_raw = trace.get("Ry_unrounded_MPa")
    ru_raw = trace.get("Ru_unrounded_MPa")
    ry_round = trace.get("Ry_rounded_MPa")
    ru_round = trace.get("Ru_rounded_MPa")
    ry_tab = trace.get("Ry_tabulated_MPa")
    ru_tab = trace.get("Ru_tabulated_MPa")

    lines = ["## 2. Материал и расчётные характеристики", ""]
    if grade:
        lines.extend([f"Марка стали: **{grade}**.", ""])
    if product_label:
        lines.extend([f"Вид проката: **{product_label}**.", ""])
    if interval_label:
        lines.extend([f"Нормативный диапазон толщины: **{interval_label}**.", ""])

    lines.extend([
        "### 2.1 Коэффициент надёжности по материалу", "",
        f"{category_label}: **$\\gamma_m={_fmt(gamma_m)}$**.", "",
        "Коэффициент $\\gamma_m$ принят по **таблице 3 СП 16.13330.2017**; он используется для получения расчётных сопротивлений из нормативных.", "",
    ])

    lines.extend(["### 2.2 Нормативные и расчётные сопротивления", ""])
    lines.append(f"- Нормативное сопротивление по пределу текучести $R_{{yn}}$: **{_fmt(ryn)} МПа**")
    lines.append(f"- Нормативное временное сопротивление $R_{{un}}$: **{_fmt(run)} МПа**")
    lines.append("")

    lines.extend([
        "Расчётное сопротивление по пределу текучести:", "",
        "$$ R_y=\\frac{R_{yn}}{\\gamma_m} $$", "",
        f"$$ R_y=\\frac{{{_fmt(ryn)}}}{{{_fmt(gamma_m)}}}={_fmt(ry_raw)}\\;\\mathrm{{MPa}}\\;\\rightarrow\\;{_fmt(ry_round)}\\;\\mathrm{{MPa}} $$", "",
        "Расчётное сопротивление по временному сопротивлению:", "",
        "$$ R_u=\\frac{R_{un}}{\\gamma_m} $$", "",
        f"$$ R_u=\\frac{{{_fmt(run)}}}{{{_fmt(gamma_m)}}}={_fmt(ru_raw)}\\;\\mathrm{{MPa}}\\;\\rightarrow\\;{_fmt(ru_round)}\\;\\mathrm{{MPa}} $$", "",
        "Стрелкой показано округление до **5 Н/мм²**, применённое для расчётных сопротивлений в таблицах приложения В.", "",
    ])

    if source_table:
        lines.extend([f"*Нормативное основание исходной строки: СП 16.13330.2017, табл. {source_table}; $\\gamma_m$ — табл. 3.*", ""])
    if ry_tab is not None and ru_tab is not None:
        if bool(trace.get("annex_default_matches")):
            lines.extend([f"Контроль с опубликованной строкой табл. {source_table}: $R_y={_fmt(ry_tab)}$ МПа, $R_u={_fmt(ru_tab)}$ МПа — **совпадение**.", ""])
        else:
            lines.extend([f"Опубликованные значения табл. {source_table} ($R_y={_fmt(ry_tab)}$ МПа, $R_u={_fmt(ru_tab)}$ МПа) относятся к нормативному табличному случаю; при явно выбранной иной категории $\\gamma_m$ выше показан пересчёт от $R_{{yn}},R_{{un}}$.", ""])

    lines.append("*Report IR использует общий нормативный material helper v0.96; presentation layer только отображает зафиксированный v0.97 trace и не изменяет механический расчёт.*")
    return "\n".join(lines).strip()


def _replace_material(text: str, report: Mapping[str, Any]) -> str:
    chapter = _material_chapter_v097(report)
    if not chapter:
        return text
    if _CHAPTER_2.search(text):
        return _CHAPTER_2.sub(lambda _m: chapter + "\n\n", text, count=1)
    anchor = re.search(r"(?m)^## (?:3|Текущий)\b", text)
    if anchor:
        return text[:anchor.start()] + chapter + "\n\n" + text[anchor.start():]
    return text.rstrip() + "\n\n" + chapter + "\n"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_build = _report.build_report_ir_v092
    previous_render = _report.render_expertise_narrative_markdown_v092

    def build(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
        base = previous_build(model, session_or_snapshot)
        return augment_from_session(base, session_or_snapshot)

    def render(report: Mapping[str, Any]) -> str:
        text = previous_render(report)
        return _replace_material(text, report)

    _report.build_report_ir_v092 = build
    _report.render_expertise_narrative_markdown_v092 = render
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_material_chapter_v097"]
