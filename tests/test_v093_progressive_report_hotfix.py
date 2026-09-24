from __future__ import annotations

import streamlit_expertise_report_v093_progressive_hotfix as hotfix


def _row(qid, value, *, name=None, symbol=None, unit="MPa", presentation=None):
    row = {
        "quantity_id": qid,
        "raw_value": value,
        "name_ru": name or qid,
        "symbol": symbol,
        "canonical_unit": unit,
    }
    if presentation:
        row["presentation_semantics"] = presentation
        row["display_value"] = f"{value} {unit}".strip()
    return row


def _block(owner, outputs, *, title="completed"):
    return {
        "owner_node_id": owner,
        "title": title,
        "inputs": [],
        "outputs": outputs,
        "progress_state": "COMPLETE",
        "normative_refs": [],
    }


def _legacy_skeleton():
    return """# Расчёт огнестойкости стального элемента

## 1. Исходные данные

legacy input

## 2. Материал и расчётные характеристики

legacy material

## 3. Проверка несущей способности по СП 16

FUTURE SP16 FORMULA

## 4. Расчёт при пожаре по СП 554

FUTURE FIRE FORMULA

## 5. Теплотехнический расчёт

FUTURE THERMAL FORMULA

## 6. Заключение

FUTURE VERDICT

## Текущий незавершённый шаг

### Круглые болтовые отверстия

**Статус: PENDING.**
"""


def test_after_steel_selection_future_chapters_are_absent(monkeypatch):
    report = {
        "blocks": [
            _block("FIRE_UI13_MATERIAL", [
                _row("steel_grade", "С255Б", unit="1"),
                _row("fy_norm", 255.0, symbol="R_yn"),
                _row("fu_norm", 380.0, symbol="R_un"),
                # Legacy/preview design values may exist in evidence, but without
                # gamma_m they must not be presented as completed Table-2 results.
                _row("Ry_formula", 250.0, symbol="R_y"),
                _row("Ru_formula", 370.0, symbol="R_u"),
            ]),
            {
                "owner_node_id": "FIRE_UI14_HOLES",
                "title": "Круглые болтовые отверстия",
                "inputs": [], "outputs": [],
                "progress_state": "PENDING_CURRENT",
            },
        ]
    }
    monkeypatch.setattr(hotfix, "_render_base", lambda _: _legacy_skeleton())
    text = hotfix.render_expertise_narrative_markdown_v093_progressive(report)

    assert "## 3." not in text
    assert "## 4." not in text
    assert "## 5." not in text
    assert "## 6." not in text
    assert "FUTURE SP16 FORMULA" not in text
    assert "FUTURE THERMAL FORMULA" not in text
    assert "Круглые болтовые отверстия" in text
    assert "$R_y$" not in text
    assert "$R_u$" not in text
    assert "$R_{yn}$" in text
    assert "$R_{un}$" in text


def test_gamma_m_unlocks_explicit_table2_formula_substitution(monkeypatch):
    report = {
        "blocks": [
            _block("SP16_L_GAMMA_M", [
                _row("material_safety_category", "statistical_control", unit="1"),
                _row("gamma_m", 1.025, symbol="γ_m", unit="1"),
            ]),
            _block("SP16_C_RY_TABLE2", [
                _row("steel_grade", "С255Б", unit="1"),
                _row("fy_norm", 255.0, symbol="R_yn"),
                _row("fu_norm", 380.0, symbol="R_un"),
                _row("Ry_formula", 250.0, symbol="R_y"),
                _row("Ru_formula", 370.0, symbol="R_u"),
            ]),
        ]
    }
    monkeypatch.setattr(hotfix, "_render_base", lambda _: _legacy_skeleton())
    text = hotfix.render_expertise_narrative_markdown_v093_progressive(report)

    assert "Статистический контроль свойств проката" in text
    assert "\\gamma_m=1.025" in text
    assert "R_y=\\frac{R_{yn}}{\\gamma_m}" in text
    assert "R_y=\\frac{255}{1.025}=250" in text
    assert "R_u=\\frac{R_{un}}{\\gamma_m}" in text
    assert "R_u=\\frac{380}{1.025}=370" in text


def test_executed_humanised_profile_properties_are_visible(monkeypatch):
    report = {
        "blocks": [
            _block("FIRE_UI12_SECTION", [
                _row("A_gross", 5282.0, name="Площадь поперечного сечения", symbol="A", unit="mm²", presentation="active_v092_engineering_label"),
                _row("J_x", 100000000.0, name="Момент инерции относительно сильной главной оси z-z", symbol="I_z", unit="mm⁴", presentation="active_v092_engineering_label"),
                _row("J_y", 10000000.0, name="Момент инерции относительно слабой главной оси y-y", symbol="I_y", unit="mm⁴", presentation="active_v092_engineering_label"),
            ]),
        ]
    }
    monkeypatch.setattr(hotfix, "_render_base", lambda _: _legacy_skeleton())
    text = hotfix.render_expertise_narrative_markdown_v093_progressive(report)

    assert "### 1.1 Характеристики поперечного сечения" in text
    assert "Площадь поперечного сечения $A$" in text
    assert "сильной главной оси z-z $I_z$" in text
    assert "слабой главной оси y-y $I_y$" in text
    assert "неиспользованные свойства остаются в Audit" in text
