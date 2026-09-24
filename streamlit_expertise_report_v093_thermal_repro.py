"""v0.93 thermal-report reproducibility refinement (audit item #16).

Presentation only: values are read from REPORT-IR/runtime evidence. No thermal
quantity or PASS/FAIL verdict is recomputed here.
"""
from __future__ import annotations

from typing import Any, Mapping

import streamlit_expertise_report_v090_install as _install_mod
from streamlit_expertise_report_v090_thermal_refinement import (
    _find_protected_result,
    _find_unprotected_result,
)

_INSTALLED = "_fire_v093_thermal_repro_report_installed"
_CONCLUSION = "## 6. Заключение"


def _rows(report: Mapping[str, Any]):
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        for row in block.get("outputs") or []:
            if isinstance(row, Mapping):
                yield row


def _value(report: Mapping[str, Any], *qids: str) -> Any:
    wanted = set(qids)
    for row in _rows(report):
        if row.get("quantity_id") in wanted:
            return row.get("raw_value")
    return None


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "Да" if v else "Нет"
    if isinstance(v, (int, float)):
        return f"{float(v):.6g}"
    return str(v)


def _first(mapping: Mapping[str, Any] | None, *keys: str) -> Any:
    if not isinstance(mapping, Mapping):
        return None
    for key in keys:
        if mapping.get(key) is not None:
            return mapping.get(key)
    return None


def _thermal_passport(report: Mapping[str, Any]) -> str:
    unprotected = _find_unprotected_result(report) or {}
    protected = _find_protected_result(report) or {}
    up = unprotected.get("material_parameters") if isinstance(unprotected.get("material_parameters"), Mapping) else {}
    pp = protected.get("material_parameters") if isinstance(protected.get("material_parameters"), Mapping) else {}
    vis = protected.get("visualization") if isinstance(protected.get("visualization"), Mapping) else {}

    pprot = _value(report, "P_heated_protected")
    dprot = _value(report, "delta_pr_protected", "delta_pr_prot")
    ptrace = _value(report, "sp554_protected_table1_perimeter_trace")
    ptrace = ptrace if isinstance(ptrace, Mapping) else {}

    t0 = _value(report, "gost30247_initial_furnace_temperature_c")
    if t0 is None:
        contract = _value(report, "gost30247_standard_fire_curve_contract")
        t0 = _first(contract, "initial_temperature_c")
    rho_s = _value(report, "sp554_steel_density_12_2")
    c0 = _value(report, "sp554_steel_c0_12_2")
    kc = _value(report, "sp554_steel_c_temp_coeff_12_2")
    dt_u = _value(report, "sp554_dt_unprotected_min")
    dt_p = _value(report, "sp554_dt_protected_s", "sp554_dt_protected_min", "protection_time_step_s")
    if dt_p is None:
        dt_p = _first(protected, "time_step_s", "dt_s")

    r_un = _value(report, "unprotected_fire_resistance_min")
    if r_un is None:
        r_un = _first(unprotected, "actual_fire_resistance_min")
    r_pr = _value(report, "protected_fire_resistance_min")
    if r_pr is None:
        r_pr = _first(protected, "actual_fire_resistance_min")
    r_req = _value(report, "required_fire_resistance_min", "R_required", "R_req")
    verdict = _value(report, "fire_resistance_requirement_pass", "fire_resistance_pass", "R_requirement_pass")

    lines = [
        "### 5.3 Паспорт воспроизводимости теплотехнического расчёта",
        "",
        "Ниже сведены исходные данные и параметры **фактически выполненного runtime**. Этот блок не пересчитывает результат, а делает расчёт воспроизводимым по тем же формулам и дискретизации.",
        "",
        "#### Общие параметры",
        "",
    ]
    common = [
        ("Начальная температура $T_0$", t0, "°C"),
        ("Плотность стали $ρ_s$", rho_s if rho_s is not None else _first(up, "rho_steel", "steel_density_kg_m3"), "кг/м³"),
        ("Коэффициент $c_0$", c0 if c0 is not None else _first(up, "steel_c0", "c0"), "Дж/(кг·К)"),
        ("Температурный коэффициент $k_c$", kc if kc is not None else _first(up, "steel_c_temp_coeff", "kc"), "1/°C"),
        ("Шаг незащищённого расчёта $Δt$", dt_u, "мин"),
    ]
    for label, value, unit in common:
        if value is not None:
            lines.append(f"- {label}: **{_fmt(value)} {unit}**.")
    lines += ["", "#### Защищённая схема", ""]
    if ptrace:
        formula = ptrace.get("formula")
        vals = []
        for symbol, key in (("B", "B_mm"), ("D", "D_mm"), ("t_w", "t_mm")):
            if ptrace.get(key) is not None:
                vals.append(f"{symbol}={_fmt(ptrace[key])} мм")
        lines.append(f"- Таблица 1: **$P_{{prot}}={formula}$**" + (f" при {', '.join(vals)}." if vals else "."))
    if pprot is not None:
        lines.append(f"- Обогреваемый периметр защиты: **$P_{{prot}}={_fmt(pprot)}$ м**.")
    if dprot is not None:
        lines.append(f"- Формула (12.2): **$δ_{{pr,prot}}=A/P_{{prot}}={_fmt(dprot)}$ мм**.")
    if dt_p is not None:
        unit = "с" if "s" in str(next((k for k in ("sp554_dt_protected_s", "protection_time_step_s") if _value(report, k) is not None), "s")) else "мин"
        lines.append(f"- Шаг защищённого расчёта: **$Δt={_fmt(dt_p)}$ {unit}**.")
    if vis:
        if vis.get("layer_count") is not None:
            lines.append(f"- Расчётная сетка: **n={_fmt(vis['layer_count'])}** интервалов.")
        if vis.get("dx_mm") is not None:
            lines.append(f"- Пространственный шаг: **$Δx={_fmt(vis['dx_mm'])}$ мм**.")
    for label, key, unit in (("Плотность огнезащиты $ρ_f$", "rho_f", "кг/м³"), ("$A_λ$", "A_lambda", "Вт/(м·К)"), ("$B_λ$", "B_lambda", "Вт/(м·К·°C)"), ("$C_c$", "C_c", "Дж/(кг·К)"), ("$D_c$", "D_c", "Дж/(кг·К·°C)")):
        value = _first(pp, key)
        if value is not None:
            lines.append(f"- {label}: **{_fmt(value)} {unit}**.")

    lines += ["", "#### Терминальный результат", ""]
    if r_un is not None:
        lines.append(f"- Без огнезащиты: **$R_{{fact}}={_fmt(r_un)}$ мин**.")
    if r_pr is not None:
        lines.append(f"- С огнезащитой: **$R_{{fact}}={_fmt(r_pr)}$ мин**.")
    if r_req is not None:
        lines.append(f"- Требование: **$R_{{req}}={_fmt(r_req)}$ мин**.")
    if isinstance(verdict, bool):
        lines.append(f"- Runtime-verdict: **{'PASS' if verdict else 'FAIL'}**.")
    elif r_req is not None:
        lines.append("- PASS/FAIL в этом presentation-блоке самостоятельно не выводится: показывается только опубликованный runtime-verdict, чтобы не создавать второй источник нормативной логики.")
    lines += ["", "Пошаговый температурный trace и узловые температуры остаются в Audit; приведённых здесь параметров достаточно для повторного запуска той же численной схемы без скрытых presentation-допущений.", ""]
    return "\n".join(lines)


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = _install_mod.render_expertise_narrative_markdown_v092

    def render(report: Mapping[str, Any]) -> str:
        markdown = previous(report)
        block = _thermal_passport(report)
        if _CONCLUSION in markdown:
            return markdown.replace(_CONCLUSION, block + "\n\n" + _CONCLUSION, 1)
        return markdown + "\n\n" + block

    _install_mod.render_expertise_narrative_markdown_v092 = render
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_thermal_passport"]
