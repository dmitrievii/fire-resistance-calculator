"""v0.92 progressive/compact expertise-report presentation.

Executed engineering narrative remains owned by the retained v0.91 renderer.
This wrapper adds active-v0.92 presentation guarantees without recalculating any
engineering value:

* only completed evidence plus one current ``PENDING_CURRENT`` step is shown;
* technical implementation vocabulary is removed from the main narrative;
* empty headings and excessive blank lines are removed;
* visual hierarchy is controlled by report-scoped CSS;
* the material chapter restores the explicit SP16 Table-3 category -> gamma_m
  provenance and renders Table-2 Ry/Ru formulas from completed execution blocks.
"""
from __future__ import annotations

import copy
import re
from typing import Any, Mapping

from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir_v092 import PENDING_CURRENT_STATE
import streamlit_expertise_report_v089 as _v089
from streamlit_expertise_report_v091 import render_expertise_narrative_markdown_v091

REPORT_MARKER_CLASS = "fire-report-v092-marker"
REPORT_COMPACT_CSS = r"""
<style>
/* Scoped by a marker placed inside the bordered report container. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] p {
    margin-top: 0.12rem !important;
    margin-bottom: 0.18rem !important;
    line-height: 1.28 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] ul,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] ol {
    margin-top: 0.18rem !important;
    margin-bottom: 0.28rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] li {
    margin-top: 0.04rem !important;
    margin-bottom: 0.04rem !important;
    line-height: 1.28 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h2 {
    margin-top: 1.65rem !important;
    margin-bottom: 0.52rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h3 {
    margin-top: 1.05rem !important;
    margin-bottom: 0.36rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h4 {
    margin-top: 0.68rem !important;
    margin-bottom: 0.24rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) .katex-display {
    margin-top: 0.24rem !important;
    margin-bottom: 0.30rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) hr {
    margin-top: 0.85rem !important;
    margin-bottom: 0.85rem !important;
}
</style>
""".strip()

_TECHNICAL_WORDING = (
    (re.compile(r"\bмеханическим\s+runtime\b", re.IGNORECASE), "механическим расчётом"),
    (re.compile(r"\bпо\s+выполненному\s+runtime\b", re.IGNORECASE), "по выполненному расчёту"),
    (re.compile(r"\bruntime\s+получил\b", re.IGNORECASE), "в расчёте получен"),
    (re.compile(r"\bruntime\b", re.IGNORECASE), "расчёт"),
    (re.compile(r"\bREPORT-IR\b", re.IGNORECASE), "расчётном протоколе"),
    (re.compile(r"\bpresentation-слой\b", re.IGNORECASE), "отчёт"),
    (re.compile(r"\bpresentation layer\b", re.IGNORECASE), "отчёт"),
    (re.compile(r"\btrace\b", re.IGNORECASE), "расчётный протокол"),
)

_MATERIAL_SAFETY_LABELS = {
    "statistical_control": "Статистический контроль свойств проката",
    "nonstatistical_high_yield_or_hot_finished_or_foreign": (
        "Нестатистический контроль для высокопрочной / термообработанной / зарубежной стали"
    ),
    "other_conforming": "Другие соответствующие требованиям стали",
    "ks1_limited_service": "Ограниченный случай КС-1 по таблице 3",
}


def _pending_blocks(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in report.get("blocks") or []
        if isinstance(row, Mapping) and row.get("progress_state") == PENDING_CURRENT_STATE
    ]


def _remove_empty_headings(markdown: str) -> str:
    """Drop headings whose entire section contains no non-heading content."""
    lines = str(markdown or "").splitlines()
    headings: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+\S", line)
        if match:
            headings.append((index, len(match.group(1))))
    drop: set[int] = set()
    for position, (line_index, level) in enumerate(headings):
        end = len(lines)
        for next_index, next_level in headings[position + 1 :]:
            if next_level <= level:
                end = next_index
                break
        substantive = any(
            line.strip() and not re.match(r"^#{1,6}\s+", line)
            for line in lines[line_index + 1 : end]
        )
        if not substantive:
            drop.add(line_index)
    return "\n".join(line for idx, line in enumerate(lines) if idx not in drop)


def compact_engineering_markdown(markdown: str) -> str:
    """Remove implementation jargon, empty headings and excessive whitespace only."""
    text = str(markdown or "")
    for pattern, replacement in _TECHNICAL_WORDING:
        text = pattern.sub(replacement, text)
    text = _remove_empty_headings(text)
    # Markdown requires one empty line between block elements; more than one is
    # visual noise and conflicts with the compact-report contract.
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def report_marker_html() -> str:
    return f'<span class="{REPORT_MARKER_CLASS}" aria-hidden="true"></span>'


def _block_by_owner(report: Mapping[str, Any], owner_node_id: str) -> Mapping[str, Any] | None:
    for block in reversed(report.get("blocks") or []):
        if isinstance(block, Mapping) and block.get("owner_node_id") == owner_node_id:
            return block
    return None


def _latex_equation_lines(block: Mapping[str, Any] | None) -> list[str]:
    if not block:
        return []
    equation = build_trace_bound_equation(block)
    if not equation:
        return []
    formula = equation.get("formula_latex")
    substitution = equation.get("substitution_result_latex") or equation.get("substitution_latex")
    lines: list[str] = []
    if formula:
        lines.extend([f"$$ {formula} $$", ""])
    if substitution:
        lines.extend([f"$$ {substitution} $$", ""])
    return lines


def _material_chapter(report: Mapping[str, Any]) -> str:
    """Build Chapter 2 strictly from material values/equations already in evidence."""
    grade = _v089._find_row(report, qids=("steel_grade",), names=("марка/класс стали",))
    category = _v089._find_row(report, qids=("material_safety_category",))
    gamma_m = _v089._find_row(report, qids=("gamma_m",), symbols=("γ_m",))
    ryn = _v089._find_row(report, qids=("fy_norm",), symbols=("R_yn",), names=("нормативный предел текучести",))
    run = _v089._find_row(report, qids=("fu_norm",), symbols=("R_un",), names=("нормативное временное сопротивление",))
    ry = _v089._find_row(report, qids=("Ry_formula",), symbols=("R_y",), names=("расчетное сопротивление по пределу текучести",))
    ru = _v089._find_row(report, qids=("Ru_formula",), symbols=("R_u",), names=("расчетное сопротивление по временному сопротивлению",))
    rs = _v089._find_row(report, qids=("Rs_formula",), symbols=("R_s",), names=("расчетное сопротивление сдвигу",))

    if not any((grade, category, gamma_m, ryn, run, ry, ru, rs)):
        return ""

    lines = ["## 2. Материал и расчётные характеристики", ""]
    if grade:
        lines.extend([f"Марка стали: **{_v089._display(grade)}**.", ""])

    if category or gamma_m:
        lines.extend(["### 2.1 Коэффициент надёжности по материалу", ""])
        category_key = _v089._row_raw(category)
        label = _MATERIAL_SAFETY_LABELS.get(str(category_key), str(category_key or "категория не зафиксирована"))
        gamma_raw = _v089._row_raw(gamma_m)
        if isinstance(gamma_raw, (int, float)) and not isinstance(gamma_raw, bool):
            gamma_text = _v089._fmt_number(float(gamma_raw)).replace(".", ",")
            lines.extend([
                f"Коэффициент надёжности по материалу: **{label} — $γ_m={gamma_text}$**.",
                "",
            ])
        else:
            lines.extend([f"Условия контроля свойств проката: **{label}**.", ""])
        gamma_block = _block_by_owner(report, "SP16_L_GAMMA_M")
        if gamma_block:
            ref = _v089._ref(gamma_block)
            if ref:
                lines.extend([f"*Нормативное основание: {ref}. Категория выбрана явно; скрытое значение $γ_m$ не применяется.*", ""])

    if any((ryn, run, ry, ru, rs)):
        lines.extend(["### 2.2 Нормативные и расчётные сопротивления", ""])
        # Formula -> substitution -> result must precede the summary list.
        lines.extend(_latex_equation_lines(_block_by_owner(report, "SP16_C_RY_TABLE2")))
        lines.extend(_latex_equation_lines(_block_by_owner(report, "SP16_C_RU_TABLE2")))
        if rs:
            lines.extend(_latex_equation_lines(_block_by_owner(report, "SP16_C_RS_TABLE2")))

        items = [
            ("Нормативное сопротивление по пределу текучести", "$R_{yn}$", ryn),
            ("Нормативное временное сопротивление", "$R_{un}$", run),
            ("Расчётное сопротивление по пределу текучести", "$R_y$", ry),
            ("Расчётное сопротивление по временному сопротивлению", "$R_u$", ru),
            ("Расчётное сопротивление сдвигу", "$R_s$", rs),
        ]
        for name, symbol, hit in items:
            if hit:
                lines.append(f"- {name} {symbol}: **{_v089._display(hit)}**")
        lines.append("")

        formula_block = _block_by_owner(report, "SP16_C_RY_TABLE2") or _block_by_owner(report, "SP16_C_RU_TABLE2")
        if formula_block:
            ref = _v089._ref(formula_block)
            if ref:
                lines.extend([f"*Нормативное основание: {ref}.*", ""])

    return compact_engineering_markdown("\n".join(lines))


def _replace_material_chapter(markdown: str, report: Mapping[str, Any]) -> str:
    chapter = _material_chapter(report)
    pattern = re.compile(r"(?ms)^## 2\. Материал[^\n]*\n.*?(?=^## 3\.|\Z)")
    if pattern.search(markdown):
        replacement = (chapter + "\n\n") if chapter else ""
        return pattern.sub(replacement, markdown, count=1)
    if chapter:
        marker = re.search(r"(?m)^## 3\.", markdown)
        if marker:
            return markdown[: marker.start()] + chapter + "\n\n" + markdown[marker.start() :]
        return markdown.rstrip() + "\n\n" + chapter
    return markdown


def render_expertise_narrative_markdown_v092(report: Mapping[str, Any]) -> str:
    pending = _pending_blocks(report)
    if len(pending) > 1:
        raise ValueError("v0.92 progressive report may contain at most one PENDING_CURRENT block")

    # The retained renderer is fed completed blocks only so it cannot describe
    # an unfinished node as already executed or expose a future formula.
    executed = copy.deepcopy(dict(report))
    executed["blocks"] = [
        row
        for row in executed.get("blocks") or []
        if not (isinstance(row, Mapping) and row.get("progress_state") == PENDING_CURRENT_STATE)
    ]
    executed["block_count"] = len(executed["blocks"])
    markdown = render_expertise_narrative_markdown_v091(executed)
    markdown = _replace_material_chapter(markdown, executed)
    markdown = compact_engineering_markdown(markdown)

    if not pending:
        return markdown + ("\n" if markdown else "")

    block = pending[0]
    title = str(block.get("title") or block.get("owner_node_id") or "Текущий шаг")
    pending_text = compact_engineering_markdown(
        "\n".join(
            [
                "## Текущий незавершённый шаг",
                "",
                f"### {title}",
                "",
                "**Статус: PENDING.** Текущий шаг уже открыт и ожидает ввода данных.",
                "",
                "Расчётная формула, числовая подстановка и результат будут добавлены в отчёт только после фактического выполнения этого шага.",
            ]
        )
    )
    if markdown:
        return compact_engineering_markdown(markdown + "\n\n" + pending_text) + "\n"
    return "# Расчёт огнестойкости стального элемента\n\n" + pending_text + "\n"


__all__ = [
    "REPORT_COMPACT_CSS",
    "REPORT_MARKER_CLASS",
    "compact_engineering_markdown",
    "render_expertise_narrative_markdown_v092",
    "report_marker_html",
]
