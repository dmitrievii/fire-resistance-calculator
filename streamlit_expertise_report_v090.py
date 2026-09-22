"""v0.90 REPORT4: engineering report closure for MECH9 and the full report contract.

Presentation only. Numerical engineering results come from REPORT-IR5 / executed
runtime evidence. This layer reformats units and axis labels for the user-facing
report, but does not evaluate SP16/SP554 equations or infer PASS/FAIL from a
numerical comparison.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.sp16_mech9_v090_ux_overlay import _ANNEX_K_LABELS

_INSTALLED = "_fire_expertise_report_v090_installed"

_BASE_SECTION_MATERIAL = _v089._section_material

_CHECK_LABELS = {
    "steel_selection_5_2_table_v1": "Выбор стали по п. 5.2 / табл. В.1",
    "stress_concentration_and_work_hardening_reduction": "Меры по снижению концентрации напряжений и наклёпа",
    "solid_web_vs_lattice_concentration_considered": "Учёт особенностей сплошностенчатой/решётчатой схемы",
    "enhanced_ndt_above_0_4_ry": "Усиленный НК при σt > 0,4Ry",
    "weld_intersections_avoided": "Исключение пересечений сварных швов",
    "runoff_tabs_and_weld_ndt": "Выводные планки и контроль сварных швов",
    "flank_weld_termination_25_mm_each_side": "Окончание фланговых швов не менее 25 мм от края",
    "minimum_section_thickness_for_guillotine_or_punching": "Минимальная толщина при гильотинной резке/пробивке",
    "secondary_gusset_bolted_to_tension_member": "Болтовое крепление вторичной фасонки к растянутому элементу",
}

# Runtime quantity IDs are retained for backward compatibility. The report
# maps them to the accepted SP16 natural system: z strong, y weak, Mx torsion.
_LOAD_ROWS = (
    ("N", ("ambient_N_force",), ("ambient: продольная сила",), 1.0e-3, "кН"),
    ("M_z", ("ambient_M_x",), ("ambient: изгибающий момент mx",), 1.0e-6, "кН·м"),
    ("M_y", ("ambient_M_y",), ("ambient: изгибающий момент my",), 1.0e-6, "кН·м"),
    ("M_x", ("ambient_T_torsion",), ("ambient: крутящий момент t",), 1.0e-6, "кН·м"),
    ("Q_z", ("ambient_Q_x",), ("ambient: поперечная сила qx",), 1.0e-3, "кН"),
    ("Q_y", ("ambient_Q_y",), ("ambient: поперечная сила qy",), 1.0e-3, "кН"),
    ("B", ("ambient_B_bimoment",), ("ambient: бимомент",), 1.0e-9, "кН·м²"),
)


def _num(value: Any) -> str:
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    if isinstance(value, float):
        return _v089._fmt_number(value)
    if value is None:
        return "—"
    return str(value)


def _raw(report: Mapping[str, Any], qid: str) -> Any:
    return _v089._row_raw(_v089._find_row(report, qids=(qid,)))


def _evidence_bundle(report: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = _raw(report, "sp16_mech9_primary_evidence")
    return raw if isinstance(raw, Mapping) else {}


def _required(report: Mapping[str, Any], qid: str) -> bool | None:
    raw = _raw(report, qid)
    return raw if isinstance(raw, bool) else None


def _input(report: Mapping[str, Any], qid: str) -> Any:
    return _raw(report, qid)


def _status_text(row: Mapping[str, Any]) -> str:
    status = str(row.get("status") or "—")
    return {
        "PASS": "PASS — проверка выполнена",
        "FAIL": "FAIL — проверка не выполнена",
        "N.A.": "не применимо",
        "DEFERRED": "не закрыто; переход далее блокируется",
        "CONTEXT_UNRESOLVED": "контекст не разрешён; переход далее блокируется",
    }.get(status, status)


def _engineering_load_rows(report: Mapping[str, Any]) -> list[tuple[str, float, str]]:
    """Return only non-zero actions in user-facing SP16 axes and engineering units."""
    rows: list[tuple[str, float, str]] = []
    for symbol, qids, names, factor, unit in _LOAD_ROWS:
        hit = _v089._find_row(report, qids=qids, names=names)
        raw = _v089._row_raw(hit)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            continue
        value = float(raw)
        if not math.isfinite(value) or abs(value) <= 1.0e-12:
            continue
        rows.append((symbol, value * factor, unit))
    return rows


def _find_named_row(report: Mapping[str, Any], *tokens: str):
    wanted = [_v089._norm_text(t) for t in tokens if t]
    for row, block, _ in reversed(_v089._all_rows(report)):
        name = _v089._norm_text(row.get("name_ru"))
        if name and any(t in name for t in wanted):
            return row, block
    return None


def _section_inputs_v090(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "## 1. Исходные данные",
        "",
        "В основном отчёте приведены только инженерно значимые исходные данные. "
        "Полный вектор состояния, включая нулевые компоненты и внутренние quantity-ID, сохранён во вкладке Audit.",
        "",
    ]

    # Weakening intentionally precedes the action vector.
    an = _v089._find_row(report, qids=("section_area_net",), symbols=("A_n",), names=("площадь сечения нетто",))
    d = _v089._find_row(report, symbols=("d",), names=("диаметр отверстия стенки",))
    s = _v089._find_row(report, symbols=("s",), names=("шаг отверстий",))
    alpha = _v089._find_row(report, symbols=("α_h", "alpha_h"), names=("коэффициент учета отверстий", "коэффициент учёта отверстий"))
    if d and s:
        lines.extend([
            "### 1.1 Ослабления сечения",
            "",
            f"Учтён ряд круглых болтовых отверстий по нейтральной линии: $d$ = **{_v089._display(d)}**, "
            f"шаг $s$ = **{_v089._display(s)}**.",
            "",
            "$$ \\alpha_h=\\frac{s}{s-d} $$",
            "",
        ])
        if alpha:
            lines.extend([f"По выполненному расчёту $\\alpha_h$ = **{_v089._display(alpha)}**.", ""])
            _v089._append_ref(lines, alpha[1])
        if an:
            lines.extend([f"Площадь нетто для применимых проверок: $A_n$ = **{_v089._display(an)}**.", ""])

    lines.extend(["### 1.2 Расчётные усилия", ""])
    loads = _engineering_load_rows(report)
    if loads:
        rendered = [f"${symbol}$ = **{_num(value)} {unit}**" for symbol, value, unit in loads]
        lines.extend([
            ";  \n".join(rendered) + ".",
            "",
            "Оси отчёта: **z — сильная**, **y — слабая**, $M_x$ — крутящий момент; "
            "$Q_y$ и $Q_z$ сохраняются как самостоятельные компоненты без образования фиктивной результирующей.",
            "",
        ])
    else:
        lines.extend([
            "В текущем сохранённом состоянии нет ненулевых силовых факторов для вывода в основном отчёте. "
            "Полный вектор доступен в Audit.",
            "",
        ])

    state = _v089._find_row(report, names=("вид напряженно-деформированного состояния", "расчётное состояние", "расчетное состояние"))
    if state:
        lines.extend([f"Расчётное состояние: **{_v089._display(state)}**.", ""])
    return lines


def _section_material_v090(report: Mapping[str, Any]) -> list[str]:
    lines = ["## 2. Материал и сечение", ""]
    profile = _v089._find_row(report, names=("обозначение профиля",))
    family = _v089._find_row(report, names=("семейство сечения", "тип поперечного сечения"))
    steel_type = _v089._find_row(report, names=("тип получения стального сечения",))
    h = _v089._find_row(report, symbols=("h",), names=("высота сечения",))
    b = _v089._find_row(report, symbols=("b",), names=("ширина сечения",))
    tw = _v089._find_row(report, symbols=("t_w",), names=("толщина стенки",))
    tf = _v089._find_row(report, symbols=("t_f",), names=("толщина полки",))
    area = _v089._find_row(report, qids=("section_area_gross",), symbols=("A",), names=("площадь сечения брутто",))
    iz = _v089._find_row(report, symbols=("J_z", "I_z", "J_x", "I_x"), names=("момент инерции относительно z", "момент инерции относительно x"))
    iy = _v089._find_row(report, symbols=("J_y", "I_y"), names=("момент инерции относительно y",))

    if profile:
        lines.extend([f"Принято сечение **{_v089._display(profile)}**.", ""])
    if family:
        lines.extend([f"Семейство сечения: **{_v089._display(family)}**.", ""])
    if steel_type:
        lines.extend([f"Тип получения сечения: **{_v089._display(steel_type)}**.", ""])

    vals = []
    for symbol, hit in (("h", h), ("b", b), ("t_w", tw), ("t_f", tf), ("A", area), ("I_z", iz), ("I_y", iy)):
        if hit:
            vals.append(f"${symbol}$ = **{_v089._display(hit)}**")
    if vals:
        lines.extend(["Геометрические характеристики принятого сечения:", "", ";  \n".join(vals) + ".", ""])

    base = list(_BASE_SECTION_MATERIAL(report))
    if len(base) >= 2 and str(base[0]).startswith("## 2."):
        base = base[2:]
    lines.extend(base)
    return lines


def _axis_bundle(report: Mapping[str, Any], axis: str) -> dict[str, Any]:
    if axis == "z":
        return {
            "mu": _v089._find_row(report, symbols=("μz", "μ_z"), names=("коэффициент расчетной длины μz", "коэффициент расчётной длины μz")),
            "lef": _v089._find_row(report, symbols=("l_ef,z",), names=("расчетная длина l_eff,z", "расчётная длина l_eff,z")),
            "i": _v089._find_row(report, symbols=("i_z",), names=("радиус инерции iz",)),
            "lam": _v089._find_row(report, symbols=("λ_z",), names=("геометрическая гибкость λz",)),
            "bar": _v089._find_row(report, symbols=("λ̄_z",), names=("условная гибкость λ̄z",)),
            "curve": _v089._find_row(report, names=("тип кривой устойчивости по таблице 7 для оси z", "кривая устойчивости по оси z")),
            "phi": _v089._find_row(report, symbols=("φ_z",), names=("коэффициент устойчивости φz",)),
        }
    return {
        "mu": _v089._find_row(report, symbols=("μy", "μ_y"), names=("коэффициент расчетной длины μy", "коэффициент расчётной длины μy")),
        "lef": _v089._find_row(report, symbols=("l_ef,y",), names=("расчетная длина l_eff,y", "расчётная длина l_eff,y")),
        "i": _v089._find_row(report, symbols=("i_y",), names=("радиус инерции iy",)),
        "lam": _v089._find_row(report, symbols=("λ_y",), names=("геометрическая гибкость λy",)),
        "bar": _v089._find_row(report, symbols=("λ̄_y",), names=("условная гибкость по y", "условная гибкость λ̄y")),
        "curve": _v089._find_row(report, names=("кривая a/b/c по y", "кривая устойчивости по оси y")),
        "phi": _v089._find_row(report, symbols=("φ_y",), names=("коэффициент устойчивости φy",)),
    }


def _slenderness_section(report: Mapping[str, Any]) -> list[str]:
    lines = ["### 3.1 Расчётные длины и гибкости", ""]
    length = _find_named_row(report, "длина элемента", "геометрическая длина", "длина стержня")
    support_z = _find_named_row(report, "закреплен", "закреплён", "схема опирания", "схема закрепления")
    if length:
        lines.extend([f"Исходная длина элемента: **{_v089._display(length)}**.", ""])
    if support_z:
        lines.extend([f"Условие закрепления/схема, сохранённая расчётом: **{_v089._display(support_z)}**.", ""])

    z = _axis_bundle(report, "z")
    y = _axis_bundle(report, "y")
    have_results = any(v for bundle in (z, y) for v in bundle.values())

    lines.extend([
        "$$ i=\\sqrt{\\frac{I}{A}},\\qquad l_{ef}=\\mu L,\\qquad "
        "\\lambda=\\frac{l_{ef}}{i} $$",
        "",
    ])
    if not have_results:
        lines.extend([
            "**PENDING:** расчётные длины/гибкости ещё не сформированы выполненным runtime. "
            "Раздел не считается проверенным до появления trace-bound результатов.",
            "",
        ])
        return lines

    for axis, bundle in (("z", z), ("y", y)):
        parts = []
        for label, key in (
            (f"μ_{axis}", "mu"),
            (f"l_{{ef,{axis}}}", "lef"),
            (f"i_{axis}", "i"),
            (f"λ_{axis}", "lam"),
            (f"λ̄_{axis}", "bar"),
            (f"φ_{axis}", "phi"),
        ):
            if bundle[key]:
                parts.append(f"${label}$ = **{_v089._display(bundle[key])}**")
        if parts:
            lines.extend([f"**Ось {axis}:** " + ";  ".join(parts) + ".", ""])
        if bundle["curve"]:
            lines.extend([f"Кривая устойчивости по оси {axis}: **{_v089._display(bundle['curve'])}**.", ""])

    governing = _find_named_row(report, "определяющая ось", "управляющая ось", "governing axis")
    if governing:
        lines.extend([f"Определяющая ось по выполненному расчёту: **{_v089._display(governing)}**.", ""])
    else:
        lines.extend([
            "Определяющая ось отдельно не выводится presentation-слоем без явного runtime-результата; "
            "значения по обеим осям приведены выше.",
            "",
        ])

    block = _v089._find_block(report, "расчетные длины", "гибкости") or _v089._find_block(report, "расчётные длины", "гибкости")
    _v089._append_formula_evidence(lines, block)
    _v089._append_ref(lines, block)
    return lines


def _section_sp16_v090(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "## 3. Проверка несущей способности по СП 16",
        "",
        "В основной текст включаются расчётно значимые проверки и их trace-bound результаты. "
        "Служебная маршрутизация и внутренние ID остаются в Audit.",
        "",
    ]
    lines.extend(_slenderness_section(report))
    lines.extend(["### 3.2 Определяющая механическая проверка", ""])

    n = _v089._find_row(report, qids=("ambient_N_force",), names=("ambient: продольная сила",))
    gamma_c = _v089._find_row(report, symbols=("γ_c",), names=("γc для центрального сжатия",))
    gov_eta = _v089._find_row(report, symbols=("η", "eta"), names=("управляющий коэффициент использования", "определяющий коэффициент использования"))
    mech_pass = _v089._find_row(report, qids=("SP16_MECHANICAL_PASS",), names=("sp16_mechanical_pass", "status механического gate"))

    compression_block = None
    for block in reversed(_v089._blocks(report)):
        title = _v089._norm_text(block.get("title"))
        refs = _v089._ref(block)
        if "сжат" in title and "SP16" in refs.upper() and _v089._formula_evidence(block):
            compression_block = block
            break

    if n and isinstance(_v089._row_raw(n), (int, float)) and not isinstance(_v089._row_raw(n), bool):
        lines.extend([f"Продольная сила для активной проверки: $N$ = **{_num(float(_v089._row_raw(n))*1e-3)} кН**.", ""])
    if gamma_c:
        lines.extend([f"Коэффициент условий работы $γ_c$ = **{_v089._display(gamma_c)}**.", ""])
    _v089._append_formula_evidence(lines, compression_block)
    _v089._append_ref(lines, compression_block)

    if gov_eta:
        lines.extend([f"Определяющий коэффициент использования: **{_v089._display(gov_eta)}**.", ""])
    if mech_pass and isinstance(_v089._row_raw(mech_pass), bool):
        lines.extend([
            "**Инженерный вывод:** применимые механические проверки СП 16 "
            + ("выполнены." if _v089._row_raw(mech_pass) else "не выполнены."),
            "",
        ])
    elif not any((compression_block, gov_eta)):
        lines.extend([
            "**PENDING:** определяющий результат механической проверки ещё не сформирован runtime.",
            "",
        ])

    evidence = _evidence_bundle(report)
    lines.extend(_fatigue_section(report, evidence))
    lines.extend(_brittle_section(report, evidence))
    return lines


def _fatigue_section(report: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[str]:
    lines = ["### 3.3 Усталость, раздел 12 СП 16", ""]
    required = _required(report, "sp16_mech7_fatigue_required")
    if required is False:
        return lines + ["Отдельная проверка усталости раздела 12 для данного расчётного случая **не требуется**.", ""]

    row = evidence.get("fatigue") if isinstance(evidence.get("fatigue"), Mapping) else None
    if row is None:
        return lines + ["**PENDING:** проверка усталости требуется, но исполнимое evidence N9 ещё не сформировано.", ""]

    details = row.get("details") if isinstance(row.get("details"), Mapping) else {}
    n9 = details.get("n9_result") if isinstance(details.get("n9_result"), Mapping) else {}
    general = n9.get("general_fatigue_check") if isinstance(n9.get("general_fatigue_check"), Mapping) else {}
    lines.extend([f"**Статус N9:** {_status_text(row)}.", ""])
    if row.get("reason"):
        lines.extend([f"Причина/ограничение: {row['reason']}.", ""])

    cycles = _input(report, "sp16_mech9_fatigue_load_cycles")
    sigma_max = _input(report, "sp16_mech9_fatigue_sigma_max")
    sigma_min = _input(report, "sp16_mech9_fatigue_sigma_min")
    case_id = general.get("annex_k_case_id") or _input(report, "sp16_mech9_fatigue_annex_k_case_id")
    if any(v is not None for v in (cycles, sigma_max, sigma_min, case_id)):
        lines.extend(["Исходные данные активной ветви:", ""])
        if cycles is not None:
            lines.append(f"- число циклов $n$ = **{_num(cycles)}**;")
        if sigma_max is not None:
            lines.append(f"- $σ_{{max}}$ = **{_num(sigma_max)} МПа**;")
        if sigma_min is not None:
            lines.append(f"- $σ_{{min}}$ = **{_num(sigma_min)} МПа**;")
        if case_id is not None:
            lines.append(f"- случай приложения К, таблицы К.1: **{_ANNEX_K_LABELS.get(str(case_id), str(case_id))}**.")
        lines.append("")

    if general:
        group = general.get("annex_k_element_group")
        rv = general.get("table_35_fatigue_resistance_n_mm2")
        alpha = general.get("cycle_factor_alpha")
        rho = general.get("stress_asymmetry_ratio_rho")
        gamma_v = general.get("table_36_asymmetry_factor_gamma_v")
        eta = general.get("equation_170_utilization")
        lines.extend([
            f"По приложению К определена группа **{_num(group)}**; по таблице 35 $R_v$ = **{_num(rv)} МПа**.",
            "",
            f"$α$ = **{_num(alpha)}**; $ρ=σ_{{min}}/σ_{{max}}$ = **{_num(rho)}**; "
            f"по таблице 36 $γ_v$ = **{_num(gamma_v)}**.",
            "",
            "$$ \\eta_{170}=\\frac{|\\sigma_{max}|}{\\alpha R_v \\gamma_v}\\le 1.0 $$",
            "",
        ])
        if all(v is not None for v in (sigma_max, alpha, rv, gamma_v, eta)):
            lines.extend([
                f"Подстановка trace-bound значений: "
                f"$|σ_{{max}}|={_num(abs(float(sigma_max)))}$ МПа, $α={_num(alpha)}$, "
                f"$R_v={_num(rv)}$ МПа, $γ_v={_num(gamma_v)}$; "
                f"runtime-результат $η_{{170}}$ = **{_num(eta)}**.",
                "",
            ])
        cap = general.get("fatigue_resistance_cap_check")
        if isinstance(cap, Mapping):
            cap_pass = cap.get("pass")
            lines.extend([
                f"Ограничение $αR_vγ_v\\le R_u/γ_u$: коэффициент использования "
                f"**{_num(cap.get('cap_utilization'))}**, результат "
                f"**{'PASS' if cap_pass is True else 'FAIL' if cap_pass is False else '—'}**.",
                "",
            ])
        if row.get("utilization") is not None:
            lines.extend([f"Определяющий коэффициент использования N9: **{_num(row.get('utilization'))}**.", ""])
    lines.extend([
        "*Нормативное основание: СП 16.13330.2017, п. 12.1.1–12.1.2, "
        "формулы (170)–(172), таблицы 35–36, приложение К.*",
        "",
    ])
    return lines


def _brittle_section(report: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[str]:
    lines = ["### 3.4 Требования раздела 13 и ламеллярное разрушение", ""]
    required = _required(report, "sp16_mech7_brittle_required")
    if required is False:
        return lines + ["Отдельная проверка требований раздела 13 для данного расчётного случая **не требуется**.", ""]

    row = evidence.get("brittle_fracture") if isinstance(evidence.get("brittle_fracture"), Mapping) else None
    if row is None:
        return lines + ["**PENDING:** проверка раздела 13 требуется, но исполнимое evidence N10 ещё не сформировано.", ""]

    details = row.get("details") if isinstance(row.get("details"), Mapping) else {}
    n10 = details.get("n10_result") if isinstance(details.get("n10_result"), Mapping) else {}
    lines.extend([f"**Статус N10:** {_status_text(row)}.", ""])
    if row.get("reason"):
        lines.extend([f"Причина/ограничение: {row['reason']}.", ""])

    general = n10.get("general_prevention") if isinstance(n10.get("general_prevention"), Mapping) else {}
    checks = general.get("clause_13_2_checks") if isinstance(general.get("clause_13_2_checks"), Mapping) else {}
    if checks:
        lines.extend(["**Применимые конструктивные требования §13.2**", ""])
        for key, item in checks.items():
            if not isinstance(item, Mapping) or item.get("applicable") is not True:
                continue
            label = _CHECK_LABELS.get(str(key), str(key))
            confirmed = item.get("confirmed")
            suffix = "PASS" if confirmed is True else "FAIL" if confirmed is False else "—"
            if key == "enhanced_ndt_above_0_4_ry" and item.get("stress_n_mm2") is not None:
                label += f" (σt={_num(item.get('stress_n_mm2'))} МПа; 0,4Ry={_num(item.get('threshold_n_mm2'))} МПа)"
            if key == "flank_weld_termination_25_mm_each_side" and item.get("provided_mm") is not None:
                label += f" (принято {_num(item.get('provided_mm'))} мм)"
            lines.append(f"- {label}: **{suffix}**.")
        lines.append("")

    lam = n10.get("lamellar_tearing") if isinstance(n10.get("lamellar_tearing"), Mapping) else None
    if lam is not None:
        if lam.get("required") is False:
            lines.extend(["По подтверждённому screening §13.3 расчёт ламеллярного разрушения **не требуется**.", ""])
        elif lam.get("required") is True:
            lines.extend(["**Ламеллярное разрушение, §13.3–13.5**", ""])
            factors = lam.get("table_37_factors_percent") if isinstance(lam.get("table_37_factors_percent"), Mapping) else {}
            if factors:
                lines.extend([
                    "Коэффициенты риска по таблице 37:",
                    "",
                    ";  \n".join(f"${k}$ = **{_num(v)} %**" for k, v in factors.items()) + ".",
                    "",
                    "$$ \\psi_z=\\psi_{zf}+\\psi_{zt}+\\psi_{zsh}+\\psi_{zj}+\\psi_{zs} $$",
                    "",
                    f"Runtime-результат формулы (174): **{_num(lam.get('equation_174_base_risk_percent'))} %**; "
                    f"после применимого воздействия: **{_num(lam.get('adjusted_risk_percent'))} %**.",
                    "",
                ])
            required_z = lam.get("required_z_quality_group")
            selected_z = lam.get("selected_z_quality_group")
            if required_z is not None or selected_z is not None:
                lines.extend([
                    f"Требуемая Z-группа: **{_num(required_z)}**; принятая по сертификату: **{_num(selected_z)}**; "
                    f"достаточность: **{'PASS' if lam.get('selected_quality_meets_minimum_group') is True else 'FAIL' if lam.get('selected_quality_meets_minimum_group') is False else '—'}**.",
                    "",
                ])
            if lam.get("governing_utilization") is not None:
                lines.extend([f"Определяющий коэффициент использования: **{_num(lam.get('governing_utilization'))}**.", ""])

    failed = general.get("failed_requirements") if isinstance(general.get("failed_requirements"), list) else []
    if failed:
        lines.extend([
            "Невыполненные применимые требования: **"
            + ", ".join(_CHECK_LABELS.get(str(x), str(x)) for x in failed)
            + "**.",
            "",
        ])
    lines.extend([
        "*Нормативное основание: СП 16.13330.2017, раздел 13, пп. 13.1–13.5, формула (174), таблица 37.*",
        "",
    ])
    return lines


def _section_fire_mechanics_v090(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "## 4. Расчёт при пожаре по СП 554",
        "",
        "### 4.1 Передача результатов СП 16 → СП 554",
        "",
    ]
    mech_pass = _v089._find_row(report, qids=("SP16_MECHANICAL_PASS",), names=("sp16_mechanical_pass", "status механического gate"))
    eta = _v089._find_row(report, symbols=("η", "eta"), names=("управляющий коэффициент использования", "определяющий коэффициент использования"))
    if mech_pass and isinstance(_v089._row_raw(mech_pass), bool):
        lines.extend([
            "Пожарная ветвь использует квалифицированное механическое состояние, сформированное после применимых проверок СП 16. "
            "Результаты не пересчитываются и не заменяются упрощённым набором усилий.",
            "",
            f"Механический gate СП 16: **{'PASS' if _v089._row_raw(mech_pass) else 'FAIL'}**.",
            "",
        ])
        if eta:
            lines.extend([f"Определяющий коэффициент использования СП 16: **{_v089._display(eta)}**.", ""])
    else:
        lines.extend([
            "**PENDING:** квалифицированный механический handoff СП 16 ещё не сформирован; "
            "пожарная механика не должна трактоваться как завершённая.",
            "",
        ])

    lines.extend(["### 4.2 Коэффициенты $γ_T$ и $γ_e$", ""])
    gamma_t = _v089._find_row(report, symbols=("γ_T",), names=("температурный коэффициент по формуле 9.2", "требуемый температурный коэффициент снижения прочности"))
    gamma_e = _v089._find_row(report, symbols=("γ_e",), names=("требуемый температурный коэффициент снижения модуля упругости", "γe по потере устойчивости"))
    gt_block = _v089._find_block(report, "γt", "центральном сжатии") or (gamma_t[1] if gamma_t else None)
    ge_block = _v089._find_block(report, "γe", "критической температуры") or (gamma_e[1] if gamma_e else None)
    if gamma_t:
        lines.extend([f"По активной ветви получено $γ_T$ = **{_v089._display(gamma_t)}**.", ""])
        _v089._append_formula_evidence(lines, gt_block)
        _v089._append_ref(lines, gt_block)
    if gamma_e:
        lines.extend([f"Для проверки устойчивости получено $γ_e$ = **{_v089._display(gamma_e)}**.", ""])
        _v089._append_formula_evidence(lines, ge_block)
        _v089._append_ref(lines, ge_block)
    if not gamma_t and not gamma_e:
        lines.extend(["**PENDING:** коэффициенты пожарной механики ещё не получены.", ""])

    lines.extend(["### 4.3 Критическая температура стали", ""])
    tcr = _v089._find_row(report, qids=("critical_temperature_c",), names=("критическая температура стали", "управляющая критическая температура"))
    branch = _v089._find_row(report, names=("определяющая температурная ветвь",))
    tcr_block = _v089._find_block(report, "критическая температура", "независимые") or (tcr[1] if tcr else None)
    _v089._append_formula_evidence(lines, tcr_block)
    if tcr:
        lines.extend([f"Критическая температура для теплотехнического расчёта: **{_v089._display(tcr)}**.", ""])
    else:
        lines.extend(["**PENDING:** критическая температура ещё не сформирована.", ""])
    if branch:
        lines.extend([f"Определяющая температурная ветвь: **{_v089._display(branch)}**.", ""])
    _v089._append_ref(lines, tcr_block)
    return lines


def _r_designation(raw: Any) -> str | None:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
        return None
    value = float(raw)
    if value <= 0:
        return None
    return f"R{int(value)}" if value.is_integer() else f"R{_v089._fmt_number(value)}"


def _section_conclusion_v090(report: Mapping[str, Any]) -> list[str]:
    tcr = _v089._find_row(report, qids=("critical_temperature_c",), names=("критическая температура стали", "управляющая критическая температура"))
    runprot = _v089._find_row(report, symbols=("R_unprot",), names=("фактический предел без огнезащиты",))
    rprot = _v089._find_row(report, symbols=("R_prot",), names=("фактический предел с огнезащитой",))
    df = _v089._find_row(report, symbols=("δ_f",), names=("толщина огнезащитного покрытия", "проверяемая толщина огнезащиты"))
    rreq = _v089._find_row(report, symbols=("R_req", "Rreq"), names=("требуемый предел огнестойкости", "требуемый предел"))
    unprot_ok = _v089._find_row(report, qids=("unprotected_compliance",), names=("соответствие без огнезащиты", "unprotected compliance"))
    prot_ok = _v089._find_row(report, qids=("protected_compliance",), names=("соответствие с огнезащитой", "protected compliance"))

    lines = ["## 6. Заключение", ""]
    if tcr:
        lines.extend([f"Критическая температура стали: **{_v089._display(tcr)}**.", ""])
    if runprot:
        lines.extend([f"Фактический предел без огнезащиты: **{_v089._display(runprot)}**.", ""])
    if df and rprot:
        lines.extend([f"При толщине огнезащиты **{_v089._display(df)}** фактический предел: **{_v089._display(rprot)}**.", ""])

    compliance_hit = None
    fact_hit = None
    if prot_ok and isinstance(_v089._row_raw(prot_ok), bool) and rprot:
        compliance_hit, fact_hit = prot_ok, rprot
    elif unprot_ok and isinstance(_v089._row_raw(unprot_ok), bool) and runprot:
        compliance_hit, fact_hit = unprot_ok, runprot

    if rreq:
        lines.extend([f"Требуемый предел: **{_v089._display(rreq)}**.", ""])
    designation = _r_designation(_v089._row_raw(rreq) if rreq else None)

    if compliance_hit and fact_hit and rreq:
        passed = bool(_v089._row_raw(compliance_hit))
        relation = r"\ge" if passed else "<"
        lines.extend([
            f"$R_{{fact}}$ = **{_v089._display(fact_hit)}**;  ",
            f"$R_{{req}}$ = **{_v089._display(rreq)}**.",
            "",
            f"$$ R_{{fact}} {relation} R_{{req}} $$",
            "",
            "**Итог:** "
            + (f"требование **{designation}** выполняется." if passed and designation else
               f"требуемый предел **{designation}** не обеспечен." if (not passed and designation) else
               "требование по огнестойкости выполняется." if passed else
               "требование по огнестойкости не выполняется."),
            "",
        ])
        if designation:
            lines.extend([f"### Результат: **{designation} — {'PASS' if passed else 'FAIL'}**", ""])
    else:
        lines.extend([
            "**PENDING:** явный runtime-результат соответствия $R_{fact}$ требуемому пределу ещё отсутствует. "
            "Presentation-слой не выводит PASS/FAIL из самостоятельного сравнения чисел.",
            "",
        ])
    return lines


def render_expertise_narrative_markdown_v090(report: Mapping[str, Any]) -> str:
    lines = [
        "# Расчёт огнестойкости стального элемента",
        "",
        "**Уровень детализации: Расчётный.**",
        "",
        "Основной отчёт построен по инженерным разделам из выполненного trace. "
        "Внутренняя маршрутизация, нулевые компоненты силового состояния и технические ID вынесены в Audit.",
        "",
    ]
    for builder in (
        _section_inputs_v090,
        _section_material_v090,
        _section_sp16_v090,
        _section_fire_mechanics_v090,
        _v089._section_thermal,
        _section_conclusion_v090,
    ):
        section = builder(report)
        if section:
            lines.extend(section)
    return "\n".join(lines).strip() + "\n"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    # v0.89 renderer resolves these module globals at call time; replacing them
    # upgrades both the on-screen report and Markdown export without touching runtime.
    _v089._section_inputs = _section_inputs_v090
    _v089._section_material = _section_material_v090
    _v089._section_sp16 = _section_sp16_v090
    _v089._section_fire_mechanics = _section_fire_mechanics_v090
    _v089._section_conclusion = _section_conclusion_v090
    _v089.render_expertise_narrative_markdown = render_expertise_narrative_markdown_v090
    setattr(core, _INSTALLED, True)


__all__ = [
    "install",
    "render_expertise_narrative_markdown_v090",
    "_engineering_load_rows",
    "_section_inputs_v090",
    "_section_material_v090",
    "_slenderness_section",
    "_section_sp16_v090",
    "_section_fire_mechanics_v090",
    "_section_conclusion_v090",
    "_fatigue_section",
    "_brittle_section",
]
