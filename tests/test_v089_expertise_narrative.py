from __future__ import annotations

import streamlit_expertise_report_v089 as v089


def _row(name, symbol, value, unit=None, qid=None):
    return {
        "name_ru": name,
        "symbol": symbol,
        "raw_value": value,
        "canonical_unit": unit,
        "quantity_id": qid or symbol,
    }


def _block(title, kind="FORMULA", inputs=None, outputs=None, human=None, refs=None, presentation=None):
    return {
        "report_block_id": title + "#1",
        "title": title,
        "kind": kind,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "human_readable": human or {},
        "normative_refs": refs or [],
        "presentation": presentation or {},
    }


def _report(*blocks):
    return {"blocks": list(blocks), "summary": {"checks": []}}


def test_formula_fallback_uses_human_readable_execution_evidence_without_evaluation():
    block = _block(
        "γT при центральном сжатии",
        outputs=[_row("Температурный коэффициент по формуле 9.2", "γ_T", 0.4275)],
        human={
            "mode": "formula_substitution",
            "formula_expression": "gamma_T=abs(N)/(phi*A*Ryn*gamma_c)",
            "substituted_expression": "gamma_T=abs(-400000)/(0.731*5282*255*0.95)",
        },
    )
    evidence = v089._formula_evidence(block)
    assert [x["text"] for x in evidence] == [
        "gamma_T=abs(N)/(phi*A*Ryn*gamma_c)",
        "gamma_T=abs(-400000)/(0.731*5282*255*0.95)",
    ]
    assert all(x["kind"] == "code" for x in evidence)


def test_report_is_semantic_not_block_by_block_and_suppresses_runtime_titles():
    report = _report(
        _block("Наличие Mx", kind="DECISION", outputs=[_row("Mx присутствует", "mx_present", False)]),
        _block("SP16-MECH8 — M+Q normative interaction binding", outputs=[_row("route ok", "ok", True)]),
        _block("FIRE-BRIDGE2 — qualified handoff", outputs=[_row("handoff", "handoff", True)]),
        _block(
            "AMBIENT_LOAD_CASE",
            kind="DECISION",
            outputs=[
                _row("Ambient: продольная сила N", "N", -400000.0, "N", "ambient_N_force"),
                _row("Ambient: изгибающий момент Mx", "M_x", 0.0, "Nmm", "ambient_M_x"),
                _row("Ambient: изгибающий момент My", "M_y", 0.0, "Nmm", "ambient_M_y"),
                _row("Ambient: поперечная сила Qx", "Q_x", 0.0, "N", "ambient_Q_x"),
                _row("Ambient: поперечная сила Qy", "Q_y", 0.0, "N", "ambient_Q_y"),
                _row("Ambient: крутящий момент T", "T", 0.0, "Nmm", "ambient_T_torsion"),
            ],
        ),
    )
    text = v089.render_expertise_narrative_markdown(report)
    assert "#### Наличие Mx" not in text
    assert "SP16-MECH8" not in text
    assert "FIRE-BRIDGE2" not in text
    assert "соответствующие проверки изгиба, среза, кручения" in text
    assert "## 3. Проверка несущей способности по СП 16" in text


def test_stability_is_consolidated_with_engineering_formulas_and_axis_results():
    report = _report(
        _block(
            "СП16 — расчётные длины, гибкости и φ",
            outputs=[
                _row("Радиус инерции iz по сильной оси z", "i_z", 85.04, "mm"),
                _row("iy", "i_y", 50.25, "mm"),
                _row("Расчётная длина l_eff,z", "l_ef,z", 3000.0, "mm"),
                _row("lef,y", "l_ef,y", 3000.0, "mm"),
                _row("Геометрическая гибкость λz", "λ_z", 35.28),
                _row("Геометрическая гибкость λy", "λ_y", 59.70),
                _row("Условная гибкость λ̄z", "λ̄_z", 1.226),
                _row("Условная гибкость по y", "λ̄_y", 2.075),
                _row("Коэффициент устойчивости φz", "φ_z", 0.924),
                _row("Коэффициент устойчивости φy", "φ_y", 0.731),
            ],
            human={
                "mode": "formula_substitution",
                "formula_expression": "lambda=l_eff/i",
                "substituted_expression": "lambda_y=3000/50.25",
            },
            refs=[{"standard_id": "SP16_2017", "clause": "7.1.3"}],
        )
    )
    text = v089.render_expertise_narrative_markdown(report)
    assert r"i=\sqrt{\frac{I}{A}}" in text
    assert r"l_{ef}=\mu L" in text
    assert r"\lambda=\frac{l_{ef}}{i}" in text
    assert "$λ_y$=59.7" in text
    assert "$φ_y$=0.731" in text
    assert "lambda_y=3000/50.25" in text


def test_reduced_thickness_formula_is_correct_and_malformed_v088_formula_is_suppressed():
    report = _report(
        _block(
            "Приведенная толщина металла без огнезащиты по (12.2)",
            inputs=[
                _row("Площадь сечения брутто", "A", 5282.0, "mm2"),
                _row("Обогреваемый периметр", "P", 1.177, "m"),
            ],
            outputs=[_row("Приведённая толщина металла", "δ_pr", 4.48768, "mm")],
            presentation={
                "formula_latex": "δpr=AP",
                "substitution_result_latex": "δpr=52821.177\\cdot1000=4.488",
            },
            refs=[{"standard_id": "SP554_2026", "clause": "12.2", "formula_ref": "(12.2)"}],
        )
    )
    text = v089.render_expertise_narrative_markdown(report)
    assert r"\delta_{pr}=\frac{A}{P}" in text
    assert "δpr=AP" not in text
    assert "52821.177" not in text
    assert "4.488" in text


def test_final_section_surfaces_actual_fire_results_and_never_infers_pass_from_numbers():
    report = _report(
        _block("Critical", kind="RESULT", outputs=[_row("Критическая температура стали", "t_cr", 610.21, "degC", "critical_temperature_c")]),
        _block("Unprotected", outputs=[_row("Фактический предел без огнезащиты", "R_unprot", 11.39, "min")]),
        _block("Protected", outputs=[
            _row("Фактический предел с огнезащитой", "R_prot", 23.26, "min"),
            _row("Толщина огнезащитного покрытия", "δ_f", 10.0, "mm"),
            _row("Требуемый предел огнестойкости", "R_req", 20.0, "min"),
        ]),
    )
    text = v089.render_expertise_narrative_markdown(report)
    assert "610.21 °C" in text
    assert "11.39 мин" in text
    assert "23.26 мин" in text
    assert "10 мм" in text
    assert "20 мин" in text
    assert "не выводится по сравнению чисел самостоятельно" in text
    assert "требование по огнестойкости защищённого элемента выполняется" not in text


def test_final_section_uses_explicit_boolean_compliance_when_trace_provides_it():
    report = _report(
        _block("Protected", outputs=[
            _row("Фактический предел с огнезащитой", "R_prot", 23.26, "min"),
            _row("Protected compliance", "ok", True, None, "protected_compliance"),
        ]),
    )
    text = v089.render_expertise_narrative_markdown(report)
    assert "требование по огнестойкости защищённого элемента выполняется" in text
