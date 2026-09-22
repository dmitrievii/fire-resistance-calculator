"""v0.90 REPORT4 refinement: engineering presentation of gamma_T and gamma_e.

Presentation only.  This layer consumes already executed REPORT-IR5 evidence and
never evaluates SP554 equations or derives PASS/FAIL.  It replaces the raw
formula-expression rendering of the fire-reduction coefficients with the
engineering notation used in the report while retaining the stored runtime
results.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from streamlit_expertise_report_v090 import render_expertise_narrative_markdown_v090 as _render_v090


_START_HEADING = "### 4.2 Коэффициенты $γ_T$ и $γ_e$"
_END_HEADING = "### 4.3 Критическая температура стали"


def _formula_items(block: Mapping[str, Any] | None) -> list[dict[str, str]]:
    return _v089._formula_evidence(block)


def _first_formula_text(block: Mapping[str, Any] | None, *, substitution: bool) -> str | None:
    items = _formula_items(block)
    for item in items:
        label = str(item.get("label") or "").lower()
        is_subst = "подстанов" in label
        if is_subst == substitution and item.get("text"):
            return str(item["text"])
    return None


def _known_gamma_t_formula(expression: str | None) -> bool:
    if not expression:
        return False
    compact = re.sub(r"\s+", "", expression).lower()
    required = ("n_force", "phi_compression_sp554", "a_gross", "fy_norm", "gamma_c_compression")
    return all(token in compact for token in required)


def _gamma_t_substitution_latex(expression: str | None, result: Any) -> str | None:
    """Pretty-print the executed substitution without recomputing its value."""
    if not expression:
        return None
    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", expression)
    if len(numbers) < 5:
        return None
    n, phi, area, fy, gamma_c = numbers[:5]
    result_text = _v089._fmt_number(result)
    return (
        rf"\gamma_T=\frac{{\left|{n}\right|}}"
        rf"{{{phi}\cdot {area}\cdot {fy}\cdot {gamma_c}}}={result_text}"
    )


def _section_fire_coefficients(report: Mapping[str, Any]) -> list[str]:
    gamma_t = _v089._find_row(
        report,
        symbols=("γ_T",),
        names=("температурный коэффициент по формуле 9.2", "требуемый температурный коэффициент снижения прочности"),
    )
    gamma_e = _v089._find_row(
        report,
        symbols=("γ_e",),
        names=("требуемый температурный коэффициент снижения модуля упругости", "γe по потере устойчивости"),
    )
    gt_block = _v089._find_block(report, "γt", "центральном сжатии") or (gamma_t[1] if gamma_t else None)
    ge_block = _v089._find_block(report, "γe", "критической температуры") or (gamma_e[1] if gamma_e else None)

    lines = [
        "### 4.2 Требуемые коэффициенты снижения прочности и жёсткости", "",
        "При нагреве расчётные характеристики стали уменьшаются. Для определения критической температуры "
        "пожарная механическая ветвь формирует два независимых предельных требования: по прочности и по устойчивости.", "",
    ]

    if gamma_t:
        gt_raw = _v089._row_raw(gamma_t)
        formula_raw = _first_formula_text(gt_block, substitution=False)
        subst_raw = _first_formula_text(gt_block, substitution=True)
        lines.extend([
            "#### Коэффициент $γ_T$ — требование по прочности", "",
            "Для активной ветви центрального сжатия требуемый коэффициент снижения прочности определяется из условия, "
            "что несущая способность нагретого сечения должна оставаться не меньше действующего продольного усилия.", "",
        ])
        if _known_gamma_t_formula(formula_raw):
            lines.extend([
                "В инженерных обозначениях отчёта расчётная зависимость имеет вид:", "",
                "$$ \\gamma_T=\\frac{|N|}{\\varphi\,A\,f_y\,\\gamma_c} $$", "",
                "где $N$ — продольная сила; $\\varphi$ — коэффициент продольного изгиба для активной ветви; "
                "$A$ — площадь сечения; $f_y$ — принятое расчётное значение прочности стали; "
                "$\\gamma_c$ — коэффициент условий работы.", "",
            ])
            pretty_subst = _gamma_t_substitution_latex(subst_raw, gt_raw)
            if pretty_subst:
                lines.extend(["Подстановка значений выполненного расчёта:", "", f"$$ {pretty_subst} $$", ""])
        else:
            # Preserve trace-bound evidence when the active branch differs from the
            # known central-compression expression; do not invent a replacement.
            _v089._append_formula_evidence(lines, gt_block)
        lines.extend([
            f"Получено **$γ_T={_v089._fmt_number(gt_raw)}$**. Это требуемый уровень сохранения прочности стали: "
            "при определении критической температуры соответствующий температурный коэффициент материала должен "
            "достичь этого предельного значения.", "",
            "*Нормативное основание: СП 554.1311500.2026, раздел 9, п. 9.2, формула (9.2).*", "",
        ])
    else:
        lines.extend(["#### Коэффициент $γ_T$ — требование по прочности", "", "**PENDING:** требуемый коэффициент снижения прочности ещё не сформирован выполненным runtime.", ""])

    if gamma_e:
        ge_raw = _v089._row_raw(gamma_e)
        ge_formula = _first_formula_text(ge_block, substitution=False)
        ge_subst = _first_formula_text(ge_block, substitution=True)
        lines.extend([
            "#### Коэффициент $γ_e$ — требование по устойчивости", "",
            "Для потери устойчивости дополнительно контролируется снижение жёсткости стали. "
            f"По выполненной нормативной ветви получено **$γ_e={_v089._fmt_number(ge_raw)}$**.", "",
        ])
        if ge_formula:
            # Use existing trace-bound evidence only; unlike gamma_T, no synthetic
            # closed-form expression is introduced when the runtime did not emit one.
            _v089._append_formula_evidence(lines, ge_block)
        elif ge_subst:
            _v089._append_formula_evidence(lines, ge_block)
        lines.extend([
            "Значение $γ_e$ используется при определении температуры, при которой уменьшение модуля упругости "
            "становится предельным для устойчивости рассматриваемого элемента.", "",
            "*Нормативное основание: СП 554.1311500.2026, п. 8.6; приложение Б, таблица Б.1 и рисунки Б.1–Б.8.*", "",
        ])
    else:
        lines.extend(["#### Коэффициент $γ_e$ — требование по устойчивости", "", "**PENDING:** требуемый коэффициент снижения жёсткости ещё не сформирован выполненным runtime.", ""])

    if gamma_t and gamma_e:
        lines.extend([
            "**Инженерный смысл.** Значения $γ_T$ и $γ_e$ не являются двумя вариантами одного коэффициента. "
            "Они задают независимые ограничения по прочности и устойчивости и далее передаются в процедуру поиска "
            "критической температуры. Определяющей становится та пожарная ветвь, которая достигает своего предельного "
            "состояния при более низкой температуре.", "",
        ])
    return lines


def render_expertise_narrative_markdown_v090_fire_coeffs(report: Mapping[str, Any]) -> str:
    markdown = _render_v090(report)
    start = markdown.find(_START_HEADING)
    end = markdown.find(_END_HEADING, start if start >= 0 else 0)
    if start < 0 or end < 0 or end <= start:
        # Fail closed in presentation: if the base report layout changed, return it
        # unchanged rather than deleting unrelated engineering evidence.
        return markdown
    replacement = "\n".join(_section_fire_coefficients(report)).rstrip() + "\n\n"
    return markdown[:start] + replacement + markdown[end:]


__all__ = ["render_expertise_narrative_markdown_v090_fire_coeffs", "_section_fire_coefficients"]
