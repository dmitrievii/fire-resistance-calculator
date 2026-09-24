"""v0.93 post-render hotfix for the progressive expertise-report contract."""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.report_ir_v092 import PENDING_CURRENT_STATE
from streamlit_expertise_report_v092_slenderness import (
    render_expertise_narrative_markdown_v092_slenderness as _render_base,
)

_CHAPTER_RE = {
    number: re.compile(rf"(?ms)^## {number}\.\s.*?(?=^## [1-9]\.\s|^## Текущий незавершённый шаг|\Z)")
    for number in (1, 2, 3, 4, 5, 6)
}
_MATERIAL_SAFETY_LABELS = {
    "statistical_control": "Статистический контроль свойств проката",
    "nonstatistical_high_yield_or_hot_finished_or_foreign": "Нестатистический контроль для высокопрочной / термообработанной / зарубежной стали",
    "other_conforming": "Другие соответствующие требованиям стали",
    "ks1_limited_service": "Ограниченный случай КС-1 по таблице 3",
}
_MECH_OWNER_TOKENS = ("SP16_MECH", "SP16_I_AMBIENT", "SP16_APPLICABILITY", "MECH7", "MECH8", "MECH9", "FATIGUE", "BRITTLE", "TABLE32", "SLENDERNESS", "EFFECTIVE_LENGTH")
_FIRE_OWNER_TOKENS = ("FIRE-BRIDGE", "SP554_C_", "SP554_FIRE", "FIRE_MECH", "FIRE-D2")
_THERMAL_OWNER_TOKENS = ("THERMAL", "UNPROTECTED", "PROTECTED", "FIRE-D3", "SP554_R_", "SP554_12", "PROTECTION")
_RESULT_OWNER_TOKENS = ("RREQ", "R_REQ", "REQUIRED_FIRE", "COMPARISON", "TERMINAL")


def _blocks(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [b for b in report.get("blocks") or [] if isinstance(b, Mapping) and b.get("progress_state") != PENDING_CURRENT_STATE]


def _all_rows(report: Mapping[str, Any]):
    for block in _blocks(report):
        for field in ("inputs", "outputs"):
            for row in block.get(field) or []:
                if isinstance(row, Mapping):
                    yield row, block


def _find(report: Mapping[str, Any], *qids: str):
    wanted = {str(x) for x in qids}
    for row, block in reversed(list(_all_rows(report))):
        if str(row.get("quantity_id") or "") in wanted:
            return row, block
    return None


def _owner_ids(report: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(b.get("owner_node_id") or "").upper() for b in _blocks(report))


def _has_owner_token(report: Mapping[str, Any], tokens: tuple[str, ...]) -> bool:
    return any(any(token in owner for token in tokens) for owner in _owner_ids(report))


def _has_qid(report: Mapping[str, Any], *qids: str) -> bool:
    return _find(report, *qids) is not None


def _stage_visibility(report: Mapping[str, Any]) -> dict[int, bool]:
    mechanics = _has_owner_token(report, _MECH_OWNER_TOKENS) or _has_qid(report, "SP16_MECHANICAL_PASS", "sp16_effective_length_zy_trace", "governing_utilization")
    fire = _has_owner_token(report, _FIRE_OWNER_TOKENS) or _has_qid(report, "gamma_T_required", "gamma_E_required", "gamma_e_compression", "critical_temperature_c")
    thermal = _has_owner_token(report, _THERMAL_OWNER_TOKENS) or _has_qid(report, "R_unprot", "R_prot", "R_fact", "thermal_unprotected_trace", "thermal_protected_trace")
    conclusion = _has_owner_token(report, _RESULT_OWNER_TOKENS) or _has_qid(report, "R_req", "fire_resistance_pass", "R_required", "R_fact_vs_R_req")
    return {1: True, 2: True, 3: mechanics, 4: fire, 5: thermal, 6: conclusion}


def _prune_future_chapters(markdown: str, report: Mapping[str, Any]) -> str:
    text = str(markdown or "")
    visibility = _stage_visibility(report)
    for number in (6, 5, 4, 3):
        if not visibility[number]:
            text = _CHAPTER_RE[number].sub(lambda _m: "", text, count=1)
    return text


def _display(hit: Any) -> str:
    return _v089._display(hit) if hit else "—"


def _raw(hit: Any) -> Any:
    return _v089._row_raw(hit) if hit else None


def _fmt(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    number = float(value)
    if not math.isfinite(number):
        return str(value)
    return _v089._fmt_number(number)


def _material_chapter(report: Mapping[str, Any]) -> str:
    grade = _find(report, "steel_grade")
    category = _find(report, "material_safety_category")
    gamma_m = _find(report, "gamma_m", "material_safety_factor")
    ryn = _find(report, "fy_norm", "Ryn", "R_yn")
    run = _find(report, "fu_norm", "Run", "R_un")
    ry = _find(report, "Ry_formula", "Ry")
    ru = _find(report, "Ru_formula", "Ru")
    rs = _find(report, "Rs_formula", "Rs")
    if not any((grade, category, gamma_m, ryn, run, ry, ru, rs)):
        return ""

    lines = ["## 2. Материал и расчётные характеристики", ""]
    if grade:
        lines.extend([f"Марка стали: **{_display(grade)}**.", ""])
    gm = _raw(gamma_m)
    gm_ready = isinstance(gm, (int, float)) and not isinstance(gm, bool) and float(gm) > 0
    if category or gm_ready:
        lines.extend(["### 2.1 Коэффициент надёжности по материалу", ""])
        category_key = _raw(category)
        label = _MATERIAL_SAFETY_LABELS.get(str(category_key), str(category_key or "условия выбора зафиксированы расчётом"))
        if gm_ready:
            lines.extend([f"{label}: **$\\gamma_m={_fmt(gm)}$**.", ""])
        else:
            lines.extend([f"Условия выбора: **{label}**. Значение $\\gamma_m$ ещё не сформировано выполненным шагом.", ""])
        source = gamma_m[1] if gamma_m else (category[1] if category else None)
        ref = _v089._ref(source) if source else ""
        if ref:
            lines.extend([f"*Нормативное основание: {ref}.*", ""])

    if ryn or run or (gm_ready and (ry or ru or rs)):
        lines.extend(["### 2.2 Нормативные и расчётные сопротивления", ""])
        if ryn:
            lines.append(f"- Нормативное сопротивление по пределу текучести $R_{{yn}}$: **{_display(ryn)}**")
        if run:
            lines.append(f"- Нормативное временное сопротивление $R_{{un}}$: **{_display(run)}**")
        lines.append("")
        if gm_ready and ryn and ry:
            lines.extend(["Расчётное сопротивление по пределу текучести:", "", "$$ R_y=\\frac{R_{yn}}{\\gamma_m} $$", "", f"$$ R_y=\\frac{{{_fmt(_raw(ryn))}}}{{{_fmt(gm)}}}={_fmt(_raw(ry))}\\;\\mathrm{{MPa}} $$", ""])
        if gm_ready and run and ru:
            lines.extend(["Расчётное сопротивление по временному сопротивлению:", "", "$$ R_u=\\frac{R_{un}}{\\gamma_m} $$", "", f"$$ R_u=\\frac{{{_fmt(_raw(run))}}}{{{_fmt(gm)}}}={_fmt(_raw(ru))}\\;\\mathrm{{MPa}} $$", ""])
        if gm_ready and rs:
            lines.extend([f"Расчётное сопротивление сдвигу $R_s$: **{_display(rs)}**.", ""])
        source = ry or ru or ryn or run
        ref = _v089._ref(source[1]) if source else ""
        if ref:
            lines.extend([f"*Нормативное основание: {ref}.*", ""])
    return "\n".join(lines).strip()


def _replace_material(markdown: str, report: Mapping[str, Any]) -> str:
    chapter = _material_chapter(report)
    pattern = _CHAPTER_RE[2]
    if pattern.search(markdown):
        replacement = (chapter + "\n\n") if chapter else ""
        # Callable replacement is mandatory here: LaTeX contains backslashes
        # such as \gamma and \frac that must remain literal Markdown/MathJax,
        # not be interpreted by re.sub's replacement-template parser.
        return pattern.sub(lambda _m: replacement, markdown, count=1)
    if not chapter:
        return markdown
    marker = re.search(r"(?m)^## (?:3|Текущий)\b", markdown)
    if marker:
        return markdown[:marker.start()] + chapter + "\n\n" + markdown[marker.start():]
    return markdown.rstrip() + "\n\n" + chapter


def _section_property_rows(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for row, _ in _all_rows(report):
        if row.get("presentation_semantics") != "active_v092_engineering_label":
            continue
        qid = str(row.get("quantity_id") or "")
        if not qid or qid in seen:
            continue
        value = row.get("raw_value")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            out.append(row)
            seen.add(qid)
    return out


def _profile_section(report: Mapping[str, Any]) -> str:
    rows = _section_property_rows(report)
    if not rows:
        return ""
    lines = ["### 1.1 Характеристики поперечного сечения", ""]
    for row in rows:
        name = str(row.get("name_ru") or row.get("quantity_id") or "Характеристика")
        symbol = str(row.get("symbol") or "").strip()
        value = row.get("display_value") or _v089._fmt_number(row.get("raw_value"))
        symbol_text = f" ${symbol}$" if symbol else ""
        lines.append(f"- {name}{symbol_text}: **{value}**")
    lines.extend(["", "Показаны только характеристики сечения, уже присутствующие в выполненном расчётном evidence; неиспользованные свойства остаются в Audit.", ""])
    return "\n".join(lines)


def _replace_profile_section(markdown: str, report: Mapping[str, Any]) -> str:
    section = _profile_section(report)
    if not section:
        return markdown
    text = re.sub(r"(?ms)^### 1\.1\s.*?(?=^### 1\.2\s|^## 2\.\s|\Z)", lambda _m: "", markdown, count=1)
    anchor = re.search(r"(?m)^### 1\.2\s|^## 2\.\s", text)
    if anchor:
        return text[:anchor.start()] + section + "\n" + text[anchor.start():]
    chapter = _CHAPTER_RE[1].search(text)
    if chapter:
        insert_at = chapter.end()
        return text[:insert_at].rstrip() + "\n\n" + section + "\n" + text[insert_at:].lstrip()
    return text


def render_expertise_narrative_markdown_v093_progressive(report: Mapping[str, Any]) -> str:
    text = _render_base(report)
    text = _replace_material(text, report)
    text = _replace_profile_section(text, report)
    text = _prune_future_chapters(text, report)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip() + "\n"


__all__ = ["render_expertise_narrative_markdown_v093_progressive"]
