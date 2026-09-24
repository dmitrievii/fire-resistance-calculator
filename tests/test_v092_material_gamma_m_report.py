from __future__ import annotations

from streamlit_expertise_report_v092 import _material_chapter


def _row(qid, value, *, symbol=None, name=None, unit="1"):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "canonical_unit": unit,
        "symbol": symbol,
        "name_ru": name or qid,
    }


def _formula_block(node_id, formula, template, bindings, output_row):
    return {
        "owner_node_id": node_id,
        "normative_refs": [
            {
                "standard_id": "SP16_2017",
                "section": "6",
                "clause": "6.1",
                "table_ref": "2",
            }
        ],
        "inputs": [],
        "outputs": [output_row],
        "presentation": {
            "formula_latex": formula,
            "substitution_template_latex": template,
            "display_precision": 3,
        },
        "execution_evidence": {
            "bindings": [
                {
                    "variable": variable,
                    "present_in_trace": True,
                    "raw_value": value,
                }
                for variable, value in bindings.items()
            ]
        },
    }


def _material_report():
    ry = _row(
        "Ry_formula",
        255.0 / 1.025,
        symbol="R_y",
        name="Расчётное сопротивление по пределу текучести",
        unit="MPa",
    )
    ru = _row(
        "Ru_formula",
        380.0 / 1.025,
        symbol="R_u",
        name="Расчётное сопротивление по временному сопротивлению",
        unit="MPa",
    )
    rs = _row(
        "Rs_formula",
        0.58 * 255.0 / 1.025,
        symbol="R_s",
        name="Расчётное сопротивление сдвигу",
        unit="MPa",
    )
    return {
        "blocks": [
            {
                "owner_node_id": "SP554_I_STEEL_STRENGTH_EDITOR",
                "normative_refs": [],
                "inputs": [],
                "outputs": [
                    _row("steel_grade", "С255Б", name="Марка/класс стали"),
                    _row("material_safety_category", "statistical_control", name="Категория коэффициента надежности по материалу"),
                    _row("fy_norm", 255.0, symbol="R_yn", name="Нормативный предел текучести", unit="MPa"),
                    _row("fu_norm", 380.0, symbol="R_un", name="Нормативное временное сопротивление", unit="MPa"),
                ],
            },
            {
                "owner_node_id": "SP16_L_GAMMA_M",
                "normative_refs": [
                    {
                        "standard_id": "SP16_2017",
                        "section": "6",
                        "clause": "6.1",
                        "table_ref": "3",
                    }
                ],
                "inputs": [_row("material_safety_category", "statistical_control")],
                "outputs": [_row("gamma_m", 1.025, symbol="γ_m", name="Коэффициент надежности по материалу")],
            },
            _formula_block(
                "SP16_C_RY_TABLE2",
                r"R_y=R_{yn}/\gamma_m",
                r"R_y={fy_norm}/{gamma_m}",
                {"fy_norm": 255.0, "gamma_m": 1.025},
                ry,
            ),
            _formula_block(
                "SP16_C_RU_TABLE2",
                r"R_u=R_{un}/\gamma_m",
                r"R_u={fu_norm}/{gamma_m}",
                {"fu_norm": 380.0, "gamma_m": 1.025},
                ru,
            ),
            _formula_block(
                "SP16_C_RS_TABLE2",
                r"R_s=0.58R_{yn}/\gamma_m",
                r"R_s=0.58\cdot {fy_norm}/{gamma_m}",
                {"fy_norm": 255.0, "gamma_m": 1.025},
                rs,
            ),
        ]
    }


def test_material_chapter_preserves_table3_choice_gamma_m_and_table2_formula_substitutions():
    chapter = _material_chapter(_material_report())

    assert "## 2. Материал и расчётные характеристики" in chapter
    assert "### 2.1 Коэффициент надёжности по материалу" in chapter
    assert "Статистический контроль свойств проката" in chapter
    assert "$γ_m=1,025$" in chapter
    assert "table_ref" not in chapter
    assert "скрытое значение $γ_m$ не применяется" in chapter

    assert r"R_y=R_{yn}/\gamma_m" in chapter
    assert r"R_y=255/1.025=\boxed{" in chapter
    assert r"R_u=R_{un}/\gamma_m" in chapter
    assert r"R_u=380/1.025=\boxed{" in chapter
    assert r"R_s=0.58R_{yn}/\gamma_m" in chapter
    assert r"R_s=0.58\cdot 255/1.025=\boxed{" in chapter

    assert "Расчётное сопротивление по пределу текучести $R_y$" in chapter
    assert "Расчётное сопротивление по временному сопротивлению $R_u$" in chapter
    assert "Расчётное сопротивление сдвигу $R_s$" in chapter


def test_material_chapter_does_not_invent_gamma_m_when_category_and_lookup_are_absent():
    report = {
        "blocks": [
            {
                "owner_node_id": "SP554_I_STEEL_STRENGTH_EDITOR",
                "normative_refs": [],
                "inputs": [],
                "outputs": [
                    _row("steel_grade", "С255Б", name="Марка/класс стали"),
                    _row("fy_norm", 255.0, symbol="R_yn", name="Нормативный предел текучести", unit="MPa"),
                    _row("fu_norm", 380.0, symbol="R_un", name="Нормативное временное сопротивление", unit="MPa"),
                ],
            }
        ]
    }
    chapter = _material_chapter(report)

    assert "Марка стали" in chapter
    assert "Статистический контроль" not in chapter
    assert "1,025" not in chapter
    assert "### 2.1 Коэффициент надёжности по материалу" not in chapter
    assert r"R_y=R_{yn}/\gamma_m" not in chapter
