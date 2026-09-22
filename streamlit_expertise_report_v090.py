"""v0.90 REPORT4: expose MECH9 / N9 / N10 evidence in the expertise report.

Presentation only. Every numerical result rendered here comes from REPORT-IR5
rows or the already executed MECH9 evidence bundle; this module evaluates no
SP16 equation and does not infer PASS/FAIL from numerical comparisons.
"""
from __future__ import annotations

from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.sp16_mech9_v090_ux_overlay import _ANNEX_K_LABELS

_INSTALLED = "_fire_expertise_report_v090_installed"
_BASE_SECTION_SP16 = _v089._section_sp16

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


def _evidence_bundle(report: Mapping[str, Any]) -> Mapping[str, Any]:
    hit = _v089._find_row(report, qids=("sp16_mech9_primary_evidence",))
    raw = _v089._row_raw(hit)
    return raw if isinstance(raw, Mapping) else {}


def _required(report: Mapping[str, Any], qid: str) -> bool | None:
    raw = _v089._row_raw(_v089._find_row(report, qids=(qid,)))
    return raw if isinstance(raw, bool) else None


def _input(report: Mapping[str, Any], qid: str) -> Any:
    return _v089._row_raw(_v089._find_row(report, qids=(qid,)))


def _status_text(row: Mapping[str, Any]) -> str:
    status = str(row.get("status") or "—")
    return {
        "PASS": "PASS — проверка выполнена",
        "FAIL": "FAIL — проверка не выполнена",
        "N.A.": "не применимо",
        "DEFERRED": "не закрыто; переход далее блокируется",
        "CONTEXT_UNRESOLVED": "контекст не разрешён; переход далее блокируется",
    }.get(status, status)


def _fatigue_section(report: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[str]:
    lines = ["### 3.3 Усталость, раздел 12 СП 16", ""]
    required = _required(report, "sp16_mech7_fatigue_required")
    if required is False:
        return lines + ["По принятой классификации отдельная проверка усталости раздела 12 для данного расчётного случая **не требуется**.", ""]

    row = evidence.get("fatigue") if isinstance(evidence.get("fatigue"), Mapping) else None
    if row is None:
        return lines + ["Проверка усталости требуется, но исполнимое evidence N9 в текущем расчёте ещё не сформировано.", ""]

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
            f"По приложению К определена группа элемента **{_num(group)}**; по таблице 35 $R_v$ = **{_num(rv)} МПа**.", "",
            f"Коэффициент числа циклов $α$ = **{_num(alpha)}**; отношение асимметрии $ρ=σ_{{min}}/σ_{{max}}$ = **{_num(rho)}**; по таблице 36 $γ_v$ = **{_num(gamma_v)}**.", "",
            "Проверка по формуле (170):", "",
            "$$ \\eta_{170}=\\frac{|\\sigma_{max}|}{\\alpha R_v \\gamma_v} \\le 1.0 $$", "",
        ])
        if all(v is not None for v in (sigma_max, alpha, rv, gamma_v, eta)):
            lines.extend([
                f"В выполненном N9 использованы $σ_{{max}}={_num(sigma_max)}$ МПа, $α={_num(alpha)}$, $R_v={_num(rv)}$ МПа и $γ_v={_num(gamma_v)}$; сохранённый результат runtime $η_{{170}}$ = **{_num(eta)}**.", "",
            ])
        cap = general.get("fatigue_resistance_cap_check")
        if isinstance(cap, Mapping):
            cap_pass = cap.get("pass")
            lines.extend([
                f"Дополнительное ограничение п. 12.1.2 $αR_vγ_v ≤ R_u/γ_u$: коэффициент использования **{_num(cap.get('cap_utilization'))}**, результат **{'PASS' if cap_pass is True else 'FAIL' if cap_pass is False else '—'}**.", "",
            ])
        if row.get("utilization") is not None:
            lines.extend([f"Определяющий коэффициент использования N9: **{_num(row.get('utilization'))}**.", ""])
    lines.extend(["*Нормативное основание: СП 16.13330.2017, п. 12.1.1–12.1.2, формулы (170)–(172), таблицы 35–36, приложение К.*", ""])
    return lines


def _brittle_section(report: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[str]:
    lines = ["### 3.4 Требования раздела 13 и ламеллярное разрушение", ""]
    required = _required(report, "sp16_mech7_brittle_required")
    if required is False:
        return lines + ["По принятой классификации отдельная проверка требований раздела 13 для данного расчётного случая **не требуется**.", ""]

    row = evidence.get("brittle_fracture") if isinstance(evidence.get("brittle_fracture"), Mapping) else None
    if row is None:
        return lines + ["Проверка раздела 13 требуется, но исполнимое evidence N10 в текущем расчёте ещё не сформировано.", ""]

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
            lines.extend(["По подтверждённому screening §13.3 отдельный расчёт ламеллярного разрушения **не требуется**.", ""])
        elif lam.get("required") is True:
            lines.extend(["**Ламеллярное разрушение, §13.3–13.5**", ""])
            factors = lam.get("table_37_factors_percent") if isinstance(lam.get("table_37_factors_percent"), Mapping) else {}
            if factors:
                lines.extend([
                    "Коэффициенты риска по таблице 37 из выполненного N10:", "",
                    ";  ".join(f"${k}$ = **{_num(v)} %**" for k, v in factors.items()) + ".", "",
                    "Формула (174) представлена в отчёте без повторного вычисления presentation-слоем:", "",
                    "$$ \\psi_z=\\psi_{zf}+\\psi_{zt}+\\psi_{zsh}+\\psi_{zj}+\\psi_{zs} $$", "",
                    f"Результат Eq.(174) из runtime: **{_num(lam.get('equation_174_base_risk_percent'))} %**; после применимого воздействия по толщине: **{_num(lam.get('adjusted_risk_percent'))} %**.", "",
                ])
            required_z = lam.get("required_z_quality_group")
            selected_z = lam.get("selected_z_quality_group")
            if required_z is not None or selected_z is not None:
                lines.extend([
                    f"Требуемая Z-группа: **{_num(required_z)}**; принятая по сертификату: **{_num(selected_z)}**; достаточность группы: **{'PASS' if lam.get('selected_quality_meets_minimum_group') is True else 'FAIL' if lam.get('selected_quality_meets_minimum_group') is False else '—'}**.", "",
                ])
            if lam.get("governing_utilization") is not None:
                lines.extend([f"Определяющий коэффициент использования проверки ламеллярного разрушения: **{_num(lam.get('governing_utilization'))}**.", ""])

    failed = general.get("failed_requirements") if isinstance(general.get("failed_requirements"), list) else []
    if failed:
        lines.extend(["Невыполненные применимые требования: **" + ", ".join(_CHECK_LABELS.get(str(x), str(x)) for x in failed) + "**.", ""])
    lines.extend(["*Нормативное основание: СП 16.13330.2017, раздел 13, в том числе пп. 13.1–13.5, формула (174), таблица 37.*", ""])
    return lines


def _section_sp16_v090(report: Mapping[str, Any]) -> list[str]:
    lines = list(_BASE_SECTION_SP16(report))
    evidence = _evidence_bundle(report)
    lines.extend(_fatigue_section(report, evidence))
    lines.extend(_brittle_section(report, evidence))
    return lines


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    _v089._section_sp16 = _section_sp16_v090
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_section_sp16_v090", "_fatigue_section", "_brittle_section"]
