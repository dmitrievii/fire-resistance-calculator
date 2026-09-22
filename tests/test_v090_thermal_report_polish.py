from __future__ import annotations

from contextlib import nullcontext

import streamlit_ui_polish_v090 as ui
from streamlit_expertise_report_v090_thermal_refinement import (
    _critical_temperature_section,
    _thermal_section,
)


def _row(qid, value, *, name=None, symbol=None, unit=None):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "name_ru": name or qid,
        "symbol": symbol,
        "canonical_unit": unit,
    }


def _report(rows):
    return {
        "blocks": [{
            "report_block_id": "synthetic#1",
            "title": "synthetic",
            "kind": "RESULT",
            "inputs": [],
            "outputs": rows,
            "human_readable": {},
            "normative_refs": [],
            "presentation": {},
        }],
        "summary": {"checks": []},
    }


def _sample_report():
    fire_mechanics = {
        "gamma_T_required": 0.8498,
        "gamma_E_required": 0.5309,
        "critical_temperature_c": 296.93268253,
        "critical_temperature_controlling_kind": "gamma_T",
        "strength_curve_inversion": {"status": "EXACT_WITHIN_PUBLISHED_CURVE", "temperature_c": 296.93268253},
        "modulus_curve_inversion": {"status": "EXACT_WITHIN_PUBLISHED_CURVE", "temperature_c": 642.214285714},
    }
    unprotected = {
        "status": "COMPLETE",
        "actual_fire_resistance_min": 5.52,
        "reduced_emissivity": 0.562913907285,
        "material_parameters": {"eps_fire": 0.85, "eps_steel": 0.625, "rho": 7850.0, "c0": 480.0, "kc": 0.00063},
    }
    protected = {
        "status": "COMPLETE",
        "actual_fire_resistance_min": 14.36,
        "critical_temperature_c": 296.93268253,
        "validation_12_6": {
            "all_within_20_percent": True,
            "result_valid": True,
            "cases": [{"maximum_reported_deviation_pct": 12.4, "within_20_percent": True}],
        },
        "material_parameters": {"rho": 7850.0},
    }
    return _report([
        _row("gamma_t", 0.8498, name="Температурный коэффициент по формуле 9.2", symbol="γ_T"),
        _row("gamma_e", 0.5309, name="Требуемый температурный коэффициент снижения модуля упругости", symbol="γ_e"),
        _row("critical_temperature_c", 296.93268253, name="Критическая температура стали", unit="degC"),
        _row("critical_temperature_controlling_kind", "gamma_T", name="Определяющая температурная ветвь"),
        _row("fire_mechanical_result", fire_mechanics),
        _row("section_area_gross", 5282.0, name="Площадь сечения брутто", symbol="A", unit="mm2"),
        _row("heated_perimeter", 0.977, name="Обогреваемый периметр", symbol="P", unit="m"),
        _row("delta_pr", 5.40634595701, name="Приведённая толщина металла", symbol="δ_pr", unit="mm"),
        _row("sp554_eps_reduced_12_4", 0.562913907285, name="Приведённая степень черноты", symbol="ε_pr"),
        _row("initial_temperature", 20.0, name="Начальная температура печи", symbol="T0", unit="degC"),
        _row("R_unprotected", 5.52, name="Фактический предел без огнезащиты", symbol="R_unprot", unit="min"),
        _row("unprotected_trace", unprotected),
        _row("protection_thickness", 15.0, name="Толщина огнезащитного покрытия", symbol="δ_f", unit="mm"),
        _row("protection_density", 1930.0, name="Плотность огнезащиты", symbol="ρ_f", unit="kg/m3"),
        _row("conductivity_a", 0.96, name="Коэффициент A теплопроводности", unit="W/(m*K)"),
        _row("conductivity_b", -0.00044, name="Коэффициент B теплопроводности", unit="W/(m*K2)"),
        _row("heat_capacity_c", 598.0, name="Коэффициент C теплоёмкости", symbol="C", unit="J/(kg*K)"),
        _row("heat_capacity_d", 0.63, name="Коэффициент D теплоёмкости", symbol="D", unit="J/(kg*K2)"),
        _row("R_protected", 14.36, name="Фактический предел с огнезащитой", symbol="R_prot", unit="min"),
        _row("protected_trace", protected),
    ])


def test_critical_temperature_lists_both_independent_criteria_and_runtime_governing_branch():
    text = "\n".join(_critical_temperature_section(_sample_report()))
    assert "T_{cr,T}" in text
    assert "296.93" in text
    assert "T_{cr,e}" in text
    assert "642.21" in text
    assert "критерий прочности" in text
    assert "gamma_T" not in text
    assert "FIRE-D2-R2" not in text


def test_thermal_report_uses_engineering_equations_not_runtime_helper_dump():
    text = "\n".join(_thermal_section(_sample_report()))
    assert r"\delta_{pr}=\frac{A}{P}" in text
    assert r"\varepsilon_{pr}=\frac{1}{1/\varepsilon_f+1/\varepsilon_s-1}" in text
    assert r"T_g(t)=T_0+345\log_{10}(8t+1)" in text
    assert "5.52 мин" in text
    assert "14.36 мин" in text
    assert r"\lambda_f(T)=A_\lambda+B_\lambda T" in text
    assert "Валидация п. 12.6" in text
    assert "12.4 %" in text
    assert "unprotected_step_time_12_1_12_4" not in text
    assert "protection_model" not in text
    assert "schema" not in text


def test_reference_unprotected_curves_have_distinct_colour_and_dash_identities():
    styles = [ui._series_style_v090(f"δпр={value:g} мм", actual_group="actual", fire_group="fire", style_map=None) for value in (3.0, 5.0, 10.0, 15.0, 20.0)]
    assert len({style[0] for style in styles}) == 5
    assert len({style[2] for style in styles}) >= 4
    assert ui._series_style_v090("actual", actual_group="actual", fire_group="fire", style_map=None)[0] == "#d62728"
    assert ui._series_style_v090("fire", actual_group="actual", fire_group="fire", style_map=None)[2] == "8 5"


class _FakeSt:
    def __init__(self):
        self.session_state = {}
        self._click = True
        self.reruns = 0
        self.messages = []

    def columns(self, n):
        return [nullcontext() for _ in range(n)]

    def markdown(self, value, **_kwargs):
        self.messages.append(str(value))

    def success(self, value, **_kwargs):
        self.messages.append(str(value))

    def caption(self, value):
        self.messages.append(str(value))

    def button(self, *_args, **_kwargs):
        if self._click:
            self._click = False
            return True
        return False

    def rerun(self):
        self.reruns += 1


class _Core:
    @staticmethod
    def _key(*parts):
        return ":".join(str(x) for x in parts)


def test_graphic_choice_first_click_updates_state_and_requests_immediate_rerun(monkeypatch):
    fake = _FakeSt()
    monkeypatch.setattr(ui._graphics, "st", fake)
    card = {"node_id": "SP554_I_UI_HEATING_SCHEME"}
    rows = [
        {"value": "four_sides", "title": "Обогрев с 4 сторон", "svg": "<svg/>", "note": "four"},
        {"value": "three_sides", "title": "Обогрев с 3 сторон", "svg": "<svg/>", "note": "three"},
    ]
    selected, _prov, ready = ui._choice_cards_v090(_Core(), card, None, "mode", rows, columns=2)
    assert selected == "four_sides"
    assert ready is True
    assert fake.reruns == 1
    state_key = _Core._key("mode", card["node_id"], "graphic-choice")
    assert fake.session_state[state_key] == "four_sides"

    fake._click = False
    ui._choice_cards_v090(_Core(), card, "four_sides", "mode", rows, columns=2)
    assert any("✓ ВЫБРАНО" in message for message in fake.messages)
