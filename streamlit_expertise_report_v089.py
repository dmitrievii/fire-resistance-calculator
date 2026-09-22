"""v0.89 REPORT3: semantic expertise narrative with broad trace-bound formula coverage.

Presentation only.  The module never executes an engineering formula, interpolates a
normative table, selects a DAG branch, converts engineering units, or infers PASS/FAIL
from a numeric value.  All numerical results come from REPORT-IR5 / execution trace.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Iterable, Mapping

from standard_core.report_equations import build_trace_bound_equation
from standard_core.report_ir5 import build_report_ir5
import streamlit_expertise_report_v088 as _v088
import streamlit_live_report_v087 as _v087


_INTERNAL_TOKENS = (
    "SP16-MECH",
    "FIRE-BRIDGE",
    "FIRE-D",
    "FIRE-UI",
    "Applicability Census",
    "normative evidence binding",
    "route reconciliation",
)

_ENUM_LABELS = {
    "central_compression": "центральное сжатие",
    "same_as_ambient": "усилия пожарной ситуации приняты равными усилиям при нормальной температуре",
    "standard": "стандартный температурный режим",
    "four_sides": "обогрев с четырёх сторон",
    "contour": "огнезащита по контуру сечения",
    "mineral_wool_board": "минераловатная плита",
    "hot_rolled_section": "горячекатаное сечение",
    "parallel_flange_i": "двутавр с параллельными гранями полок",
    "calculation_analytical": "расчётный аналитический метод",
    "verify_given_thickness": "проверка заданной толщины огнезащиты",
    "design_fire_protection": "подбор/проверка огнезащиты",
    "finish_protected": "расчёт защищённого элемента завершён",
    "ordinary": "обычная конструкционная сталь",
    "area_only_keep_gross": "площадь нетто учитывается, I и W приняты по брутто",
}

_UNIT_LABELS = {
    "degC": "°C",
    "min": "мин",
    "mm": "мм",
    "m": "м",
    "mm2": "мм²",
    "mm3": "мм³",
    "mm4": "мм⁴",
    "N": "Н",
    "Nmm": "Н·мм",
    "Nmm2": "Н·мм²",
    "MPa": "МПа",
    "kg/m3": "кг/м³",
    "J/(kg*K)": "Дж/(кг·К)",
    "J/(kg*K2)": "Дж/(кг·К²)",
    "W/(m*K)": "Вт/(м·К)",
    "W/(m*K2)": "Вт/(м·К²)",
    "%": "%",
    "1/K": "1/К",
    "1/C": "1/°C",
}


def _blocks(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [x for x in report.get("blocks") or [] if isinstance(x, Mapping)]


def _rows(block: Mapping[str, Any], field: str) -> list[Mapping[str, Any]]:
    return [x for x in block.get(field) or [] if isinstance(x, Mapping)]


def _all_rows(report: Mapping[str, Any], *, outputs_first: bool = True) -> list[tuple[Mapping[str, Any], Mapping[str, Any], str]]:
    result: list[tuple[Mapping[str, Any], Mapping[str, Any], str]] = []
    for block in _blocks(report):
        fields = ("inputs", "outputs") if outputs_first else ("outputs", "inputs")
        for field in fields:
            for row in _rows(block, field):
                result.append((row, block, field))
    return result


def _norm_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower().replace("ё", "е"))


def _find_row(
    report: Mapping[str, Any],
    *,
    qids: Iterable[str] = (),
    symbols: Iterable[str] = (),
    names: Iterable[str] = (),
) -> tuple[Mapping[str, Any], Mapping[str, Any]] | None:
    qset = {str(x) for x in qids}
    sset = {str(x).strip() for x in symbols}
    nset = {_norm_text(x) for x in names}
    rows = _all_rows(report)
    # Latest trace occurrence wins; outputs are encountered before inputs within a block.
    for row, block, _ in reversed(rows):
        if qset and str(row.get("quantity_id") or "") in qset:
            return row, block
    for row, block, _ in reversed(rows):
        name = _norm_text(row.get("name_ru"))
        if nset and name and any(token in name for token in nset):
            return row, block
    for row, block, _ in reversed(rows):
        if sset and str(row.get("symbol") or "").strip() in sset:
            return row, block
    return None


def _find_block(report: Mapping[str, Any], *tokens: str) -> Mapping[str, Any] | None:
    wanted = [_norm_text(x) for x in tokens if x]
    for block in reversed(_blocks(report)):
        hay = _norm_text(block.get("title")) + " " + " ".join(
            _norm_text(r.get("name_ru")) + " " + _norm_text(r.get("symbol"))
            for r in _rows(block, "outputs")
        )
        if all(token in hay for token in wanted):
            return block
    return None


def _row_raw(hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None) -> Any:
    return hit[0].get("raw_value") if hit else None


def _fmt_number(value: Any) -> str:
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, str):
        return _ENUM_LABELS.get(value, value)
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        a = abs(value)
        if a >= 10000:
            text = f"{value:,.2f}"
        elif a >= 100:
            text = f"{value:.2f}"
        elif a >= 10:
            text = f"{value:.2f}"
        elif a >= 1:
            text = f"{value:.3f}"
        elif a == 0:
            text = "0"
        elif a >= 0.01:
            text = f"{value:.4f}"
        else:
            text = f"{value:.4g}"
        text = text.rstrip("0").rstrip(".") if "." in text else text
        return text.replace(",", " ")
    return str(value)


def _display(hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None) -> str:
    if not hit:
        return "—"
    row = hit[0]
    value = _fmt_number(row.get("raw_value"))
    unit = row.get("canonical_unit")
    unit_text = _UNIT_LABELS.get(str(unit), str(unit)) if unit and unit != "1" else ""
    return f"{value} {unit_text}".strip()


def _symbol(hit: tuple[Mapping[str, Any], Mapping[str, Any]] | None, fallback: str) -> str:
    if hit and hit[0].get("symbol"):
        return str(hit[0]["symbol"])
    return fallback


def _ref(block: Mapping[str, Any] | None) -> str:
    if not block:
        return ""
    return _v087._refs_text(block.get("normative_refs"))


def _explicit_verdicts(report: Mapping[str, Any]) -> dict[str, str]:
    return _v088._verdict_map(report)


def _formula_evidence(block: Mapping[str, Any] | None) -> list[dict[str, str]]:
    """Return display-only formula evidence from existing report metadata.

    Priority: explicit trace-bound LaTeX -> REPORT-IR human_readable formula/lookup.
    No expression is evaluated here.
    """
    if not block:
        return []
    out: list[dict[str, str]] = []
    eq = build_trace_bound_equation(block)
    if eq:
        formula = eq.get("formula_latex")
        subst = eq.get("substitution_result_latex") or eq.get("substitution_latex")
        if formula:
            out.append({"kind": "latex", "label": "Расчётная формула", "text": str(formula)})
        if subst:
            out.append({"kind": "latex", "label": "Подстановка и результат", "text": str(subst)})
        if out:
            return out

    human = block.get("human_readable") if isinstance(block.get("human_readable"), Mapping) else {}
    mode = human.get("mode")
    if mode == "formula_substitution":
        formula = human.get("formula_expression")
        subst = human.get("substituted_expression")
        if formula:
            out.append({"kind": "code", "label": "Расчётная зависимость", "text": str(formula)})
        if subst and str(subst) != str(formula):
            out.append({"kind": "code", "label": "Подстановка значений из выполненного расчёта", "text": str(subst)})
        return out
    if mode == "lookup_substitution":
        for row in human.get("output_lines") or []:
            if not isinstance(row, Mapping):
                continue
            if row.get("formula_expression"):
                out.append({"kind": "code", "label": "Нормативная зависимость / интерполяция", "text": str(row["formula_expression"])})
            if row.get("substituted_expression"):
                out.append({"kind": "code", "label": "Подстановка", "text": str(row["substituted_expression"])})
        return out
    return []


def _append_formula_evidence(lines: list[str], block: Mapping[str, Any] | None) -> None:
    for item in _formula_evidence(block):
        lines.extend([f"**{item['label']}**", ""])
        if item["kind"] == "latex":
            lines.extend([f"$$ {item['text']} $$", ""])
        else:
            lines.extend(["```text", item["text"], "```", ""])


def _append_ref(lines: list[str], block: Mapping[str, Any] | None) -> None:
    text = _ref(block)
    if text:
        lines.extend([f"*Нормативное основание: {text}*", ""])


def _append_equation(lines: list[str], latex: str, *, caption: str | None = None) -> None:
    if caption:
        lines.extend([f"**{caption}**", ""])
    lines.extend([f"$$ {latex} $$", ""])


def _section_inputs(report: Mapping[str, Any]) -> list[str]:
    profile = _find_row(report, names=("обозначение профиля",))
    grade = _find_row(report, names=("марка/класс стали",))
    section_family = _find_row(report, names=("семейство сечения",))
    h = _find_row(report, symbols=("h",), names=("высота сечения",))
    b = _find_row(report, symbols=("b",), names=("ширина сечения",))
    tw = _find_row(report, symbols=("t_w",), names=("толщина стенки",))
    tf = _find_row(report, symbols=("t_f",), names=("толщина полки",))
    a = _find_row(report, qids=("section_area_gross",), symbols=("A",), names=("площадь сечения брутто",))
    ix = _find_row(report, symbols=("J_x", "I_x"), names=("момент инерции относительно x",))
    iy = _find_row(report, symbols=("J_y", "I_y"), names=("момент инерции относительно y",))
    steel_type = _find_row(report, names=("тип получения стального сечения",))

    N = _find_row(report, qids=("ambient_N_force",), names=("ambient: продольная сила",))
    Mx = _find_row(report, qids=("ambient_M_x",), names=("ambient: изгибающий момент mx",))
    My = _find_row(report, qids=("ambient_M_y",), names=("ambient: изгибающий момент my",))
    Qx = _find_row(report, qids=("ambient_Q_x",), names=("ambient: поперечная сила qx",))
    Qy = _find_row(report, qids=("ambient_Q_y",), names=("ambient: поперечная сила qy",))
    T = _find_row(report, qids=("ambient_T_torsion",), names=("ambient: крутящий момент t",))
    B = _find_row(report, names=("ambient: бимомент",))

    lines = [
        "## 1. Исходные данные",
        "",
        "Для расчёта принят стальной несущий элемент со следующими исходными характеристиками.",
        "",
    ]
    if profile or grade:
        lines.append(
            f"Принято сечение **{_display(profile)}**" +
            (f" из стали **{_display(grade)}**" if grade else "") + "."
        )
        lines.append("")
    if steel_type:
        lines.extend([f"Тип сечения: **{_display(steel_type)}**.", ""])
    if any((h, b, tw, tf, a, ix, iy)):
        lines.extend(["### 1.1 Геометрия поперечного сечения", ""])
        vals = []
        for label, hit in (("h", h), ("b", b), ("t_w", tw), ("t_f", tf), ("A", a), ("I_x", ix), ("I_y", iy)):
            if hit:
                vals.append(f"${label}$ = **{_display(hit)}**")
        lines.extend([";  ".join(vals) + ".", ""])
    if section_family:
        raw = _row_raw(section_family)
        if raw not in {"i_section", "box", "channel", None}:
            lines.extend([f"Тип поперечного сечения: **{_display(section_family)}**.", ""])

    loads = [("N", N), ("M_x", Mx), ("M_y", My), ("Q_x", Qx), ("Q_y", Qy), ("T", T), ("B", B)]
    if any(hit for _, hit in loads):
        lines.extend(["### 1.2 Расчётные усилия", ""])
        rendered = [f"${label}$ = **{_display(hit)}**" for label, hit in loads if hit]
        lines.extend([";  ".join(rendered) + ".", ""])
        nonzero = []
        for label, hit in loads:
            if hit and isinstance(_row_raw(hit), (int, float)) and abs(float(_row_raw(hit))) > 1e-12:
                nonzero.append(label)
        state = _find_row(report, names=("вид напряженно-деформированного состояния",))
        if state:
            lines.extend([f"Расчётное состояние классифицировано как **{_display(state)}**.", ""])
        elif nonzero:
            lines.extend(["Ненулевые силовые факторы: " + ", ".join(nonzero) + ".", ""])

    an = _find_row(report, symbols=("A_n",), names=("площадь сечения нетто",))
    d = _find_row(report, symbols=("d",), names=("диаметр отверстия стенки",))
    s = _find_row(report, symbols=("s",), names=("шаг отверстий",))
    if d and s:
        lines.extend(["### 1.3 Ослабления сечения", ""])
        lines.extend([
            f"В сечении учтены круглые болтовые отверстия: $d$ = **{_display(d)}**, шаг $s$ = **{_display(s)}**.",
            "",
        ])
        if an:
            lines.extend([f"Площадь нетто, используемая в применимых проверках: $A_n$ = **{_display(an)}**.", ""])
        alpha = _find_row(report, symbols=("α_h", "alpha_h"), names=("коэффициент учета отверстий",))
        _append_equation(lines, r"\alpha_h=\frac{s}{s-d}", caption="Коэффициент учёта отверстий стенки по формуле (45)")
        if alpha:
            lines.extend([f"По выполненному расчёту $\alpha_h$ = **{_display(alpha)}**.", ""])
            _append_ref(lines, alpha[1])
    return lines


def _section_material(report: Mapping[str, Any]) -> list[str]:
    grade = _find_row(report, names=("марка/класс стали",))
    ryn = _find_row(report, symbols=("R_yn",), names=("нормативный предел текучести",))
    run = _find_row(report, symbols=("R_un",), names=("нормативное временное сопротивление",))
    ry = _find_row(report, symbols=("R_y",), names=("расчетное сопротивление по пределу текучести",))
    ru = _find_row(report, symbols=("R_u",), names=("расчетное сопротивление по временному сопротивлению",))
    lookup_block = (ry or ryn or grade)[1] if (ry or ryn or grade) else None
    lines = ["## 2. Материал и расчётные характеристики", ""]
    if grade:
        lines.extend([f"Марка стали: **{_display(grade)}**.", ""])
    vals = []
    for symbol, hit in (("R_{yn}", ryn), ("R_{un}", run), ("R_y", ry), ("R_u", ru)):
        if hit:
            vals.append(f"${symbol}$ = **{_display(hit)}**")
    if vals:
        lines.extend(["По нормативным данным для принятой толщины проката получены:", "", ";  ".join(vals) + ".", ""])
    block = _find_block(report, "ryn", "run") or lookup_block
    _append_formula_evidence(lines, block)
    _append_ref(lines, block)
    return lines


def _section_sp16(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "## 3. Проверка несущей способности по СП 16",
        "",
        "В основном тексте приведены только расчётно значимые проверки. Служебные проверки применимости и внутренние контрольные этапы сохранены во вкладке Audit и не перегружают основной расчёт.",
        "",
        "### 3.1 Расчётные длины и гибкости",
        "",
    ]
    mu_z = _find_row(report, symbols=("μz", "μ_z"), names=("коэффициент расчетной длины μz",))
    mu_y = _find_row(report, symbols=("μy", "μ_y"), names=("μy",))
    lez = _find_row(report, symbols=("l_ef,z",), names=("расчетная длина l_eff,z",))
    ley = _find_row(report, symbols=("l_ef,y",), names=("lef,y",))
    iz = _find_row(report, symbols=("i_z",), names=("радиус инерции iz",))
    iy = _find_row(report, symbols=("i_y",), names=("iy",))
    lam_z = _find_row(report, symbols=("λ_z",), names=("геометрическая гибкость λz",))
    lam_y = _find_row(report, symbols=("λ_y",), names=("геометрическая гибкость λy",))
    bar_z = _find_row(report, symbols=("λ̄_z",), names=("условная гибкость λ̄z",))
    bar_y = _find_row(report, symbols=("λ̄_y",), names=("условная гибкость по y",))
    phi_z = _find_row(report, symbols=("φ_z",), names=("коэффициент устойчивости φz",))
    phi_y = _find_row(report, symbols=("φ_y",), names=("коэффициент устойчивости φy",))
    curve_z = _find_row(report, names=("тип кривой устойчивости по таблице 7 для оси z",))
    curve_y = _find_row(report, names=("кривая a/b/c по y",))

    _append_equation(lines, r"i=\sqrt{\frac{I}{A}},\qquad l_{ef}=\mu L,\qquad \lambda=\frac{l_{ef}}{i}")
    axis_rows = []
    if any((mu_z, lez, iz, lam_z, bar_z, phi_z)):
        axis_rows.append(
            "**Ось z:** " + ", ".join(x for x in [
                f"$μ_z$={_display(mu_z)}" if mu_z else "",
                f"$l_{{ef,z}}$={_display(lez)}" if lez else "",
                f"$i_z$={_display(iz)}" if iz else "",
                f"$λ_z$={_display(lam_z)}" if lam_z else "",
                f"$λ̄_z$={_display(bar_z)}" if bar_z else "",
                f"$φ_z$={_display(phi_z)}" if phi_z else "",
            ] if x)
        )
    if any((mu_y, ley, iy, lam_y, bar_y, phi_y)):
        axis_rows.append(
            "**Ось y:** " + ", ".join(x for x in [
                f"$μ_y$={_display(mu_y)}" if mu_y else "",
                f"$l_{{ef,y}}$={_display(ley)}" if ley else "",
                f"$i_y$={_display(iy)}" if iy else "",
                f"$λ_y$={_display(lam_y)}" if lam_y else "",
                f"$λ̄_y$={_display(bar_y)}" if bar_y else "",
                f"$φ_y$={_display(phi_y)}" if phi_y else "",
            ] if x)
        )
    for row in axis_rows:
        lines.extend([row, ""])
    if curve_z or curve_y:
        parts = []
        if curve_z:
            parts.append(f"для оси z — кривая **{_display(curve_z)}**")
        if curve_y:
            parts.append(f"для оси y — кривая **{_display(curve_y)}**")
        lines.extend(["По таблице 7 СП 16 приняты: " + "; ".join(parts) + ".", ""])

    stability_block = _find_block(report, "расчетные длины", "гибкости") or _find_block(report, "расчётные длины", "гибкости")
    _append_formula_evidence(lines, stability_block)
    _append_ref(lines, stability_block)

    lines.extend(["### 3.2 Проверка центрального сжатия и определяющий результат", ""])
    N = _find_row(report, qids=("ambient_N_force",), names=("ambient: продольная сила",))
    gamma_c = _find_row(report, symbols=("γ_c",), names=("γc для центрального сжатия",))
    gov_eta = _find_row(report, symbols=("η", "eta"), names=("управляющий коэффициент использования",))
    mech_pass = _find_row(report, qids=("SP16_MECHANICAL_PASS",), names=("sp16_mechanical_pass", "status механического gate"))
    if N:
        lines.extend([f"Расчётная продольная сила: $N$ = **{_display(N)}**.", ""])
    if gamma_c:
        lines.extend([f"Коэффициент условий работы: $γ_c$ = **{_display(gamma_c)}**.", ""])
    compression_block = None
    for block in reversed(_blocks(report)):
        title = _norm_text(block.get("title"))
        refs = _ref(block)
        if "сжат" in title and "SP16" in refs.upper() and _formula_evidence(block):
            compression_block = block
            break
    _append_formula_evidence(lines, compression_block)
    _append_ref(lines, compression_block)
    if gov_eta:
        lines.extend([f"Определяющий коэффициент использования по выполненному маршруту: **{_display(gov_eta)}**.", ""])
    if mech_pass and isinstance(_row_raw(mech_pass), bool):
        lines.extend([
            "**Вывод:** выполненные применимые проверки СП 16 " + ("пройдены." if _row_raw(mech_pass) else "не пройдены."),
            "",
        ])

    actions = []
    for label, hit in (
        ("M_x", _find_row(report, qids=("ambient_M_x",), names=("ambient: изгибающий момент mx",))),
        ("M_y", _find_row(report, qids=("ambient_M_y",), names=("ambient: изгибающий момент my",))),
        ("Q_x", _find_row(report, qids=("ambient_Q_x",), names=("ambient: поперечная сила qx",))),
        ("Q_y", _find_row(report, qids=("ambient_Q_y",), names=("ambient: поперечная сила qy",))),
        ("T", _find_row(report, qids=("ambient_T_torsion",), names=("ambient: крутящий момент t",))),
        ("B", _find_row(report, names=("ambient: бимомент",))),
    ):
        if hit and isinstance(_row_raw(hit), (int, float)) and abs(float(_row_raw(hit))) <= 1e-12:
            actions.append(label)
    if actions:
        lines.extend([
            "Для данного сочетания " + " = ".join([f"${x}$" for x in actions]) + " = 0; соответствующие проверки изгиба, среза, кручения и их сочетаний не являются определяющими.",
            "",
        ])
    return lines


def _section_fire_mechanics(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "## 4. Расчёт при пожаре по СП 554",
        "",
        "### 4.1 Коэффициенты $γ_T$ и $γ_e$",
        "",
    ]
    gamma_t = _find_row(report, symbols=("γ_T",), names=("температурный коэффициент по формуле 9.2", "требуемый температурный коэффициент снижения прочности"))
    gamma_e = _find_row(report, symbols=("γ_e",), names=("требуемый температурный коэффициент снижения модуля упругости", "γe по потере устойчивости"))
    gt_block = _find_block(report, "γt", "центральном сжатии") or (gamma_t[1] if gamma_t else None)
    ge_block = _find_block(report, "γe", "критической температуры") or (gamma_e[1] if gamma_e else None)
    if gamma_t:
        lines.extend([f"По активной ветви центрального сжатия получено $γ_T$ = **{_display(gamma_t)}**.", ""])
        _append_formula_evidence(lines, gt_block)
        _append_ref(lines, gt_block)
    if gamma_e:
        lines.extend([f"Для проверки потери устойчивости получено $γ_e$ = **{_display(gamma_e)}**.", ""])
        _append_formula_evidence(lines, ge_block)
        _append_ref(lines, ge_block)

    lines.extend(["### 4.2 Критическая температура стали", ""])
    tcr = _find_row(report, qids=("critical_temperature_c",), names=("критическая температура стали", "управляющая критическая температура"))
    branch = _find_row(report, names=("определяющая температурная ветвь",))
    tcr_block = _find_block(report, "критическая температура", "независимые") or (tcr[1] if tcr else None)
    _append_formula_evidence(lines, tcr_block)
    if tcr:
        lines.extend([f"Критическая температура, принятая для теплотехнического расчёта: **{_display(tcr)}**.", ""])
    if branch:
        lines.extend([f"Определяющая температурная ветвь: **{_display(branch)}**.", ""])
    _append_ref(lines, tcr_block)
    return lines


def _section_thermal(report: Mapping[str, Any]) -> list[str]:
    lines = ["## 5. Теплотехнический расчёт", "", "### 5.1 Незащищённый стальной элемент", ""]
    A = _find_row(report, symbols=("A",), names=("площадь сечения брутто",))
    P = _find_row(report, symbols=("P",), names=("обогреваемый периметр",))
    delta = _find_row(report, symbols=("δ_pr",), names=("приведенная толщина металла", "приведённая толщина металла"))
    eps = _find_row(report, symbols=("ε_pr",), names=("приведенная степень черноты",))
    t0 = _find_row(report, symbols=("T0",), names=("начальная температура печи",))
    runprot = _find_row(report, symbols=("R_unprot",), names=("фактический предел без огнезащиты",))
    fire_block = _find_block(report, "пошаговый прогрев", "незащищенной") or _find_block(report, "пошаговый прогрев", "незащищённой")
    eps_block = eps[1] if eps else None

    if A and P:
        _append_equation(lines, r"\delta_{pr}=\frac{A}{P}", caption="Приведённая толщина металла по формуле (12.2)")
        lines.extend([f"$A$ = **{_display(A)}**, $P$ = **{_display(P)}**.", ""])
        if delta:
            lines.extend([f"По выполненному расчёту $δ_{{pr}}$ = **{_display(delta)}**.", ""])
            _append_ref(lines, delta[1])
    if eps:
        lines.extend([f"Приведённая степень черноты $ε_{{pr}}$ = **{_display(eps)}**.", ""])
        _append_formula_evidence(lines, eps_block)
        _append_ref(lines, eps_block)
    if t0:
        _append_equation(lines, r"T_g-T_0=345\log_{10}(8t+1)", caption="Стандартный температурный режим по ГОСТ 30247.0-94")
        lines.extend([f"Начальная температура $T_0$ = **{_display(t0)}**.", ""])
    _append_formula_evidence(lines, fire_block)
    _append_ref(lines, fire_block)
    if runprot:
        lines.extend([f"Температура стали достигает критического значения через **{_display(runprot)}**; это значение принято как фактический предел огнестойкости без огнезащиты.", ""])

    lines.extend(["### 5.2 Защищённый элемент", ""])
    df = _find_row(report, symbols=("δ_f",), names=("толщина огнезащитного покрытия", "проверяемая толщина огнезащиты"))
    rprot = _find_row(report, symbols=("R_prot",), names=("фактический предел с огнезащитой",))
    rho_f = _find_row(report, symbols=("ρ_f",), names=("плотность огнезащиты",))
    kA = _find_row(report, names=("коэффициент a теплопроводности",))
    kB = _find_row(report, names=("коэффициент b теплопроводности",))
    cC = _find_row(report, symbols=("C",), names=("коэффициент c теплоемкости", "коэффициент c теплоёмкости"))
    cD = _find_row(report, symbols=("D",), names=("коэффициент d теплоемкости", "коэффициент d теплоёмкости"))
    if df:
        lines.extend([f"Расчёт выполнен для толщины огнезащиты $δ_f$ = **{_display(df)}**.", ""])
    props = []
    for label, hit in (("ρ_f", rho_f), ("A_λ", kA), ("B_λ", kB), ("C_c", cC), ("D_c", cD)):
        if hit:
            props.append(f"${label}$ = **{_display(hit)}**")
    if props:
        lines.extend(["Расчётные теплофизические параметры огнезащиты: " + ";  ".join(props) + ".", ""])
    lines.extend([
        "Температурное поле защищённого элемента определяется численным интегрированием модели СП 554, п. 12.5. В основном отчёте приводятся нормативные уравнения модели и итоговые результаты, а подробные пошаговые данные численной модели остаются в техническом журнале.",
        "",
    ])
    protected_block = _find_block(report, "фактический предел", "модель 12.5")
    _append_formula_evidence(lines, protected_block)
    _append_ref(lines, protected_block)
    if rprot:
        lines.extend([f"Фактический предел огнестойкости защищённого элемента: **{_display(rprot)}**.", ""])
    validation = _find_row(report, names=("отклонение расчета от испытаний не более 20", "отклонение расчёта от испытаний не более 20"))
    if validation and isinstance(_row_raw(validation), bool):
        lines.extend(["Валидационное условие п. 12.6: **" + ("выполняется" if _row_raw(validation) else "не выполняется") + "**.", ""])
        _append_ref(lines, validation[1])
    return lines


def _section_conclusion(report: Mapping[str, Any]) -> list[str]:
    tcr = _find_row(report, qids=("critical_temperature_c",), names=("критическая температура стали", "управляющая критическая температура"))
    runprot = _find_row(report, symbols=("R_unprot",), names=("фактический предел без огнезащиты",))
    rprot = _find_row(report, symbols=("R_prot",), names=("фактический предел с огнезащитой",))
    df = _find_row(report, symbols=("δ_f",), names=("толщина огнезащитного покрытия",))
    rreq = _find_row(report, symbols=("R_req", "Rreq"), names=("требуемый предел огнестойкости", "требуемый предел"))
    unprot_ok = _find_row(report, qids=("unprotected_compliance",), names=("соответствие без огнезащиты", "unprotected compliance"))
    prot_ok = _find_row(report, qids=("protected_compliance",), names=("соответствие с огнезащитой", "protected compliance"))
    lines = ["## 6. Заключение", ""]
    if tcr:
        lines.extend([f"Критическая температура стали: **{_display(tcr)}**.", ""])
    if runprot:
        lines.extend([f"Фактический предел огнестойкости без огнезащиты: **{_display(runprot)}**.", ""])
    if df and rprot:
        lines.extend([f"При толщине огнезащиты **{_display(df)}** фактический предел огнестойкости составляет **{_display(rprot)}**.", ""])
    if rreq:
        lines.extend([f"Требуемый предел огнестойкости: **{_display(rreq)}**.", ""])
    if prot_ok and isinstance(_row_raw(prot_ok), bool):
        lines.extend(["**Итог:** требование по огнестойкости защищённого элемента " + ("выполняется." if _row_raw(prot_ok) else "не выполняется."), ""])
    elif unprot_ok and isinstance(_row_raw(unprot_ok), bool):
        lines.extend(["**Итог:** требование по огнестойкости незащищённого элемента " + ("выполняется." if _row_raw(unprot_ok) else "не выполняется."), ""])
    else:
        lines.extend(["Итоговый PASS/FAIL в этом разделе не выводится по сравнению чисел самостоятельно: он отображается только при наличии явного логического результата выполненного расчёта.", ""])
    return lines


def render_expertise_narrative_markdown(report: Mapping[str, Any]) -> str:
    """Build one semantic engineering document rather than a block-by-block DAG transcript."""
    lines = [
        "# Расчёт огнестойкости стального элемента",
        "",
        "Расчёт выполнен по фактически пройденному нормативному маршруту. В основной текст включены только инженерно значимые исходные данные, применимые расчётные зависимости и результаты. Служебные этапы маршрутизации и полный технический журнал приведены отдельно во вкладке Audit.",
        "",
    ]
    for builder in (_section_inputs, _section_material, _section_sp16, _section_fire_mechanics, _section_thermal, _section_conclusion):
        section = builder(report)
        if section:
            lines.extend(section)
    return "\n".join(lines).strip() + "\n"


def _render_export(core: Any, report: Mapping[str, Any]) -> None:
    st = core.st
    markdown = render_expertise_narrative_markdown(report)
    st.download_button(
        "Скачать расчётный отчёт (.md)",
        data=markdown,
        file_name="fire_resistance_expertise_report.md",
        mime="text/markdown",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v089:download:markdown",
    )
    st.download_button(
        "Скачать Report IR (.json)",
        data=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        file_name="fire_report_ir_v4.json",
        mime="application/json",
        width="stretch",
        on_click="ignore",
        key="fire:expertise-report-v089:download:ir",
    )
    st.caption("Экранный и Markdown-отчёт строятся из одного REPORT-IR5. Численные результаты не пересчитываются presentation-слоем.")


def render_expertise_report(core: Any, env: Mapping[str, Any]) -> None:
    st = core.st
    app = st.session_state.get("_fire_app")
    sid = st.session_state.get("_fire_session_id")
    if app is None or not sid or sid not in app.service.sessions:
        st.info("Расчётная сессия ещё не создана.")
        return
    session = app.service.get_session(sid)
    report = build_report_ir5(app.service.model, session)
    markdown = render_expertise_narrative_markdown(report)

    st.markdown("### Расчётный отчёт")
    st.caption("Отчёт обновляется после каждого принятого шага. Основной текст собран по инженерным разделам, а служебные этапы расчётного графа скрыты во вкладке Audit.")
    tab_report, tab_export, tab_audit = st.tabs(["Расчётный отчёт", "Экспорт", "Audit"])
    with tab_report:
        _v088._report_status(st, report)
        with st.container(height=1120, border=True):
            st.markdown(markdown)
    with tab_export:
        _render_export(core, report)
    with tab_audit:
        _v087._render_audit(core, report, env)


def install(core: Any) -> None:
    if getattr(core, "_fire_expertise_report_v089_installed", False):
        return
    core._fire_expertise_report_v089_installed = True
    core._fire_expertise_report_v089_previous_renderer = core._render_ledger_trace

    def _render_ledger_trace(env: Mapping[str, Any]) -> None:
        render_expertise_report(core, env)

    core._render_ledger_trace = _render_ledger_trace


__all__ = [
    "install",
    "render_expertise_report",
    "render_expertise_narrative_markdown",
    "_formula_evidence",
    "_find_row",
    "_find_block",
]
