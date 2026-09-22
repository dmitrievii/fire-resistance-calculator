"""v0.90 REPORT4 refinement for critical-temperature and thermal sections.

Presentation only.  All temperatures, fire-resistance times and validation
verdicts are read from executed REPORT-IR5/runtime evidence.  The module removes
raw Python helper calls from the main report and presents the same evidence as an
engineering calculation.  It never derives a new normative PASS/FAIL verdict.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

import streamlit_expertise_report_v089 as _v089
from streamlit_expertise_report_v090_fire_coeffs import (
    render_expertise_narrative_markdown_v090_fire_coeffs as _render_previous,
)

_CRITICAL_HEADING = "### 4.3 Критическая температура стали"
_THERMAL_HEADING = "## 5. Теплотехнический расчёт"
_CONCLUSION_HEADING = "## 6. Заключение"


def _walk_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_mappings(child)


def _report_mappings(report: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for row, _block, _kind in _v089._all_rows(report):
        yield from _walk_mappings(row.get("raw_value"))


def _mapping_with(report: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    wanted = set(keys)
    for mapping in _report_mappings(report):
        if wanted.issubset(mapping.keys()):
            return mapping
    return None


def _row_mapping(report: Mapping[str, Any], qid: str) -> Mapping[str, Any] | None:
    hit = _v089._find_row(report, qids=(qid,))
    raw = _v089._row_raw(hit)
    return raw if isinstance(raw, Mapping) else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _fmt(value: Any) -> str:
    return _v089._fmt_number(value)


def _temp_from_inversion(value: Any) -> float | None:
    if not isinstance(value, Mapping):
        return None
    return _number(value.get("temperature_c"))


def _mechanical_fire_result(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    direct = _mapping_with(
        report,
        "critical_temperature_c",
        "critical_temperature_controlling_kind",
        "strength_curve_inversion",
        "modulus_curve_inversion",
    )
    if direct:
        return direct
    strength = _row_mapping(report, "strength_curve_inversion")
    modulus = _row_mapping(report, "modulus_curve_inversion")
    if strength or modulus:
        branch_hit = _v089._find_row(
            report,
            qids=("critical_temperature_controlling_kind",),
            names=("определяющая температурная ветвь",),
        )
        tcr_hit = _v089._find_row(
            report,
            qids=("critical_temperature_c",),
            names=("критическая температура стали", "управляющая критическая температура"),
        )
        return {
            "critical_temperature_c": _v089._row_raw(tcr_hit),
            "critical_temperature_controlling_kind": _v089._row_raw(branch_hit),
            "strength_curve_inversion": strength,
            "modulus_curve_inversion": modulus,
        }
    return None


def _critical_temperature_section(report: Mapping[str, Any]) -> list[str]:
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
    tcr_hit = _v089._find_row(
        report,
        qids=("critical_temperature_c",),
        names=("критическая температура стали", "управляющая критическая температура"),
    )
    branch_hit = _v089._find_row(
        report,
        qids=("critical_temperature_controlling_kind",),
        names=("определяющая температурная ветвь",),
    )
    result = _mechanical_fire_result(report) or {}
    strength = result.get("strength_curve_inversion")
    modulus = result.get("modulus_curve_inversion")
    t_strength = _temp_from_inversion(strength)
    t_modulus = _temp_from_inversion(modulus)
    tcr = _number(result.get("critical_temperature_c"))
    if tcr is None:
        tcr = _number(_v089._row_raw(tcr_hit))
    controlling = result.get("critical_temperature_controlling_kind") or _v089._row_raw(branch_hit)
    labels = {
        "gamma_T": "критерий прочности ($γ_T$)",
        "gamma_E": "критерий устойчивости / жёсткости ($γ_e$)",
        "gamma_e": "критерий устойчивости / жёсткости ($γ_e$)",
    }

    lines = [
        _CRITICAL_HEADING,
        "",
        "Критическая температура определяется не непосредственно из одного коэффициента, а отдельной инверсией "
        "температурных зависимостей прочности и модуля упругости. Для каждого применимого критерия определяется "
        "собственная предельная температура; в теплотехнический расчёт передаётся результат определяющей ветви, "
        "зафиксированный механическим runtime.",
        "",
    ]
    if gamma_t:
        gt = _v089._row_raw(gamma_t)
        if t_strength is not None:
            lines.extend([
                "#### По критерию прочности",
                "",
                f"Требуемому коэффициенту **$γ_T={_fmt(gt)}$** по приложению Б соответствует критическая температура "
                f"**$T_{{cr,T}}={_fmt(t_strength)}\,{{^\circ}}\mathrm{{C}}$**.",
                "",
            ])
        else:
            lines.extend([
                "#### По критерию прочности",
                "",
                f"Для **$γ_T={_fmt(gt)}$** точная температура инверсии в текущем REPORT-IR не опубликована; "
                "presentation-слой её не восстанавливает самостоятельно.",
                "",
            ])
    if gamma_e:
        ge = _v089._row_raw(gamma_e)
        if t_modulus is not None:
            lines.extend([
                "#### По критерию устойчивости",
                "",
                f"Требуемому коэффициенту **$γ_e={_fmt(ge)}$** по температурной зависимости модуля упругости соответствует "
                f"**$T_{{cr,e}}={_fmt(t_modulus)}\,{{^\circ}}\mathrm{{C}}$**.",
                "",
            ])
        elif modulus is None:
            lines.extend([
                "#### По критерию устойчивости",
                "",
                "Для данного маршрута отдельная инверсия по $γ_e$ не применялась.",
                "",
            ])
        else:
            lines.extend([
                "#### По критерию устойчивости",
                "",
                f"Для **$γ_e={_fmt(ge)}$** точная температура инверсии в текущем REPORT-IR не опубликована; "
                "presentation-слой не выполняет экстраполяцию.",
                "",
            ])

    if tcr is not None:
        branch_text = labels.get(str(controlling), "определяющий критерий, сохранённый runtime")
        lines.extend([
            "#### Принятая критическая температура",
            "",
            f"Определяющим является **{branch_text}**. Для дальнейшего теплотехнического расчёта принято:",
            "",
            f"$$ T_{{cr}}={_fmt(tcr)}\,{{^\circ}}\mathrm{{C}} $$",
            "",
            "Именно достижение этой температуры сталью используется как момент наступления предельного состояния "
            "при последующем расчёте прогрева.",
            "",
        ])
    else:
        lines.extend([
            "#### Принятая критическая температура",
            "",
            "**PENDING:** механический runtime ещё не сформировал точную критическую температуру; теплотехнический результат не считается завершённым.",
            "",
        ])
    lines.extend([
        "*Нормативное основание: СП 554.1311500.2026, п. 8.6; для активной механической ветви — соответствующая формула разделов 9–11; приложение Б, таблица Б.1 и рисунки Б.1–Б.8.*",
        "",
    ])
    return lines


def _find_unprotected_result(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for mapping in _report_mappings(report):
        if (
            "actual_fire_resistance_min" in mapping
            and "reduced_emissivity" in mapping
            and "material_parameters" in mapping
            and "validation_12_6" not in mapping
        ):
            return mapping
    return None


def _find_protected_result(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    return _mapping_with(report, "actual_fire_resistance_min", "validation_12_6", "material_parameters")


def _row(report: Mapping[str, Any], *, qids=(), symbols=(), names=()):
    return _v089._find_row(report, qids=qids, symbols=symbols, names=names)


def _thermal_section(report: Mapping[str, Any]) -> list[str]:
    A = _row(report, symbols=("A",), names=("площадь сечения брутто",))
    P = _row(report, symbols=("P",), names=("обогреваемый периметр",))
    delta = _row(report, symbols=("δ_pr",), names=("приведенная толщина металла", "приведённая толщина металла"))
    eps = _row(
        report,
        qids=("sp554_eps_reduced_12_4",),
        symbols=("ε_pr",),
        names=("приведенная степень черноты", "приведённая степень черноты"),
    )
    t0 = _row(report, symbols=("T0",), names=("начальная температура печи",))
    tcr = _row(report, qids=("critical_temperature_c",), names=("критическая температура стали", "управляющая критическая температура"))
    runprot = _row(report, symbols=("R_unprot",), names=("фактический предел без огнезащиты",))
    dt_unprot = _row(report, qids=("sp554_dt_unprotected_min", "time_step_min"), names=("шаг интегрирования незащищ",))
    eps_fire = _row(report, qids=("sp554_eps_fire_12_4", "furnace_emissivity"), names=("степень черноты пожара", "степень чёрноты пожара"))
    eps_steel = _row(report, qids=("sp554_eps_steel_12_4", "steel_emissivity"), names=("степень черноты стали", "степень чёрноты стали"))
    unprotected = _find_unprotected_result(report) or {}
    params = unprotected.get("material_parameters") if isinstance(unprotected.get("material_parameters"), Mapping) else {}

    lines = [_THERMAL_HEADING, "", "### 5.1 Незащищённый стальной элемент", ""]
    lines.extend([
        "Расчёт выполняется до момента, когда температура стали достигает принятой критической температуры $T_{cr}$. "
        "В основном отчёте приведена расчётная схема; пошаговый температурный trace остаётся в Audit.",
        "",
        "#### Геометрический параметр прогрева",
        "",
        "Приведённая толщина металла определяется по формуле (12.2):",
        "",
        r"$$ \delta_{pr}=\frac{A}{P}. $$",
        "",
    ])
    if A and P:
        a_raw = _number(_v089._row_raw(A))
        p_raw = _number(_v089._row_raw(P))
        lines.extend([f"Исходные значения: $A$ = **{_v089._display(A)}**, $P$ = **{_v089._display(P)}**.", ""])
        if a_raw is not None and p_raw is not None and str(P[0].get("canonical_unit")) == "m" and delta:
            lines.extend([
                f"Для согласования единиц $P={_fmt(p_raw)}$ м = ${_fmt(p_raw * 1000.0)}$ мм; "
                f"по выполненному runtime получено **$δ_{{pr}}={_v089._display(delta)}$**.",
                "",
            ])
        elif delta:
            lines.extend([f"По выполненному runtime получено **$δ_{{pr}}={_v089._display(delta)}$**.", ""])
    elif delta:
        lines.extend([f"По выполненному runtime получено **$δ_{{pr}}={_v089._display(delta)}$**.", ""])

    lines.extend([
        "#### Лучистый теплообмен",
        "",
        "Приведённая степень чёрноты определяется выражением:",
        "",
        r"$$ \varepsilon_{pr}=\frac{1}{1/\varepsilon_f+1/\varepsilon_s-1}. $$",
        "",
    ])
    ef = _number(_v089._row_raw(eps_fire)) if eps_fire else _number(params.get("eps_fire"))
    es = _number(_v089._row_raw(eps_steel)) if eps_steel else _number(params.get("eps_steel"))
    eps_value = _number(_v089._row_raw(eps)) if eps else _number(unprotected.get("reduced_emissivity"))
    if ef is not None and es is not None and eps_value is not None:
        lines.extend([
            f"Подстановка выполненного расчёта: $ε_f={_fmt(ef)}$, $ε_s={_fmt(es)}$; результат **$ε_{{pr}}={_fmt(eps_value)}$**.",
            "",
        ])
    elif eps_value is not None:
        lines.extend([f"По выполненному расчёту **$ε_{{pr}}={_fmt(eps_value)}$**.", ""])

    lines.extend([
        "#### Температурный режим и пошаговый прогрев",
        "",
        "Для стандартного температурного режима используется зависимость ГОСТ 30247.0-94:",
        "",
        r"$$ T_g(t)=T_0+345\log_{10}(8t+1), $$",
        "",
        "где $t$ задаётся в минутах.",
        "",
    ])
    if t0:
        lines.extend([f"Начальная температура: $T_0$ = **{_v089._display(t0)}**.", ""])
    dt_value = _number(_v089._row_raw(dt_unprot)) if dt_unprot else None
    if dt_value is not None:
        lines.extend([f"Шаг численного интегрирования: $Δt$ = **{_fmt(dt_value)} мин**.", ""])
    lines.extend([
        "На каждом шаге температура стали обновляется из теплового баланса:",
        "",
        r"$$ T_{s,n+1}=T_{s,n}+\frac{\Delta t_s\,\alpha_n\,(T_{g,n+1}-T_{s,n})}{\rho_s\,\delta_{pr}\,c_s(T_{s,n})}, $$",
        "",
        r"$$ c_s(T_s)=c_0(1+k_cT_s), $$",
        "",
        "а коэффициент теплоотдачи включает конвективную и лучистую составляющие:",
        "",
        r"$$ \alpha=29+5.77\,\varepsilon_{pr}\,\frac{[(T_g+273.15)/100]^4-[(T_s+273.15)/100]^4}{T_g-T_s}. $$",
        "",
        "Здесь $Δt_s$ — шаг времени в секундах. Расчёт прекращается при первом достижении $T_s=T_{cr}$; "
        "момент пересечения уточняется внутри последнего временного шага.",
        "",
    ])
    if tcr:
        lines.extend([f"Для данного расчёта целевая температура: **$T_{{cr}}={_v089._display(tcr)}$**.", ""])
    if runprot:
        lines.extend([
            f"**Результат:** критическая температура достигается через **{_v089._display(runprot)}**. "
            "Это фактический предел огнестойкости незащищённого элемента для выполненного маршрута.",
            "",
        ])
    lines.extend([
        "*Нормативное основание: СП 554.1311500.2026, пп. 12.1–12.4, в том числе формула (12.2); ГОСТ 30247.0-94, п. 6.1, формула (1).*
",
    ])

    lines.extend(["### 5.2 Защищённый элемент", ""])
    df = _row(report, symbols=("δ_f",), names=("толщина огнезащитного покрытия", "проверяемая толщина огнезащиты"))
    rprot = _row(report, symbols=("R_prot",), names=("фактический предел с огнезащитой",))
    rho_f = _row(report, symbols=("ρ_f",), names=("плотность огнезащиты",))
    kA = _row(report, names=("коэффициент a теплопроводности",))
    kB = _row(report, names=("коэффициент b теплопроводности",))
    cC = _row(report, symbols=("C",), names=("коэффициент c теплоемкости", "коэффициент c теплоёмкости"))
    cD = _row(report, symbols=("D",), names=("коэффициент d теплоемкости", "коэффициент d теплоёмкости"))
    protected = _find_protected_result(report) or {}
    if df:
        lines.extend([f"Проверяется огнезащита толщиной **$δ_f={_v089._display(df)}$**.", ""])
    props = []
    for label, hit in (("ρ_f", rho_f), ("A_λ", kA), ("B_λ", kB), ("C_c", cC), ("D_c", cD)):
        if hit:
            props.append(f"${label}$ = **{_v089._display(hit)}**")
    if props:
        lines.extend(["Расчётные теплофизические параметры: " + ";  ".join(props) + ".", ""])
    lines.extend([
        "Температурные зависимости свойств огнезащиты задаются в виде:",
        "",
        r"$$ \lambda_f(T)=A_\lambda+B_\lambda T,\qquad c_f(T)=C_c+D_cT. $$",
        "",
        "Толщина огнезащиты разбивается на одномерную расчётную сетку. Для внутренних узлов используется явная "
        "дискретизация уравнения теплопроводности с температурно-зависимыми $λ_f$ и $c_f$:",
        "",
        r"$$ T_i^{n+1}=T_i^n+\frac{\Delta t}{\rho_f\Delta x^2c_f(T_i^n)}\left[A_\lambda(T_{i-1}^n-2T_i^n+T_{i+1}^n)+\frac{B_\lambda}{2}\left((T_{i-1}^n)^2-2(T_i^n)^2+(T_{i+1}^n)^2\right)\right]. $$",
        "",
        "На границе «огнезащита–сталь» применяется баланс теплоёмкостей защитного слоя и приведённого стального сечения по формуле (12.7):",
        "",
        r"$$ T_s^{n+1}=T_s^n+\frac{2\Delta t\left[A_\lambda(T_p^n-T_s^n)+\frac{B_\lambda}{2}\left((T_p^n)^2-(T_s^n)^2\right)\right]}{\Delta x\left[\rho_f\Delta x\,c_f(T_s^n)+2\rho_s\delta_{pr}c_s(T_s^n)\right]}. $$",
        "",
        "Расчёт ведётся до достижения сталью принятой критической температуры; подробный узловой trace и контроль устойчивости временного шага остаются в Audit.",
        "",
    ])
    validation = protected.get("validation_12_6") if isinstance(protected.get("validation_12_6"), Mapping) else None
    if rprot:
        lines.extend([f"**Результат:** фактический предел огнестойкости защищённого элемента составляет **{_v089._display(rprot)}**.", ""])
    if validation is not None:
        ok = validation.get("result_valid")
        cases = validation.get("cases") if isinstance(validation.get("cases"), list) else []
        max_dev = None
        for case in cases:
            if isinstance(case, Mapping):
                candidate = _number(case.get("maximum_reported_deviation_pct"))
                if candidate is not None:
                    max_dev = candidate if max_dev is None else max(max_dev, candidate)
        if isinstance(ok, bool):
            text = "выполняется" if ok else "не выполняется"
            suffix = f"; максимальное подтверждённое отклонение **{_fmt(max_dev)} %**" if max_dev is not None else ""
            lines.extend([f"**Валидация п. 12.6:** условие допустимого отклонения **{text}**{suffix}.", ""])
    else:
        validation_row = _row(
            report,
            names=("отклонение расчета от испытаний не более 20", "отклонение расчёта от испытаний не более 20"),
        )
        if validation_row and isinstance(_v089._row_raw(validation_row), bool):
            lines.extend([
                "**Валидация п. 12.6:** условие допустимого отклонения **"
                + ("выполняется" if _v089._row_raw(validation_row) else "не выполняется")
                + "**.",
                "",
            ])
    lines.extend([
        "В production-модели используются зафиксированные проектом исправления подтверждённых опечаток п. 12.5: "
        "в формуле (12.5) применяется член $+t_0-t_φ$, а теплоёмкость локального узла в (12.6) определяется при его текущей температуре. "
        "Ошибочные буквальные варианты в расчёте не исполняются.",
        "",
        "*Нормативное основание: СП 554.1311500.2026, пп. 12.5–12.6 и формула (12.7); результат предела огнестойкости — по п. 13.2.*",
        "",
    ])
    return lines


def render_expertise_narrative_markdown_v090_thermal_refinement(report: Mapping[str, Any]) -> str:
    markdown = _render_previous(report)
    critical_start = markdown.find(_CRITICAL_HEADING)
    thermal_start = markdown.find(_THERMAL_HEADING, critical_start if critical_start >= 0 else 0)
    conclusion_start = markdown.find(_CONCLUSION_HEADING, thermal_start if thermal_start >= 0 else 0)
    if critical_start < 0 or thermal_start < 0 or conclusion_start < 0:
        return markdown
    critical = "\n".join(_critical_temperature_section(report)).rstrip() + "\n\n"
    thermal = "\n".join(_thermal_section(report)).rstrip() + "\n\n"
    return markdown[:critical_start] + critical + thermal + markdown[conclusion_start:]


__all__ = [
    "render_expertise_narrative_markdown_v090_thermal_refinement",
    "_critical_temperature_section",
    "_thermal_section",
]
