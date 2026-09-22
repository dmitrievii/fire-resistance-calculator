from __future__ import annotations

from streamlit_expertise_report_v090_fire_coeffs import (
    _section_fire_coefficients,
    render_expertise_narrative_markdown_v090_fire_coeffs,
)


def _row(name, symbol, value, unit=None, qid=None):
    return {
        "name_ru": name,
        "symbol": symbol,
        "raw_value": value,
        "canonical_unit": unit,
        "quantity_id": qid or symbol,
    }


def _block(title, *, outputs=None, human=None, refs=None):
    return {
        "report_block_id": title + "#1",
        "title": title,
        "kind": "FORMULA",
        "inputs": [],
        "outputs": outputs or [],
        "human_readable": human or {},
        "normative_refs": refs or [],
        "presentation": {},
    }


def _report():
    return {
        "blocks": [
            _block(
                "γT при центральном сжатии",
                outputs=[_row("Температурный коэффициент по формуле 9.2", "γ_T", 0.8498)],
                human={
                    "mode": "formula_substitution",
                    "formula_expression": "abs(N_force)/(phi_compression_sp554*A_gross*fy_norm*gamma_c_compression)",
                    "substituted_expression": "abs((-400000))/((0.388288295579)*(5282)*(255)*(0.9))",
                },
                refs=[{"standard_id": "SP554_2026", "section": "9", "clause": "9.2", "equation": "9.2"}],
            ),
            _block(
                "γe для критической температуры",
                outputs=[_row("Требуемый температурный коэффициент снижения модуля упругости", "γ_e", 0.5309)],
                refs=[
                    {"standard_id": "SP554_2026", "section": "8", "clause": "8.6"},
                    {"standard_id": "SP554_2026", "table": "Б.1"},
                    {"standard_id": "SP554_2026", "figure": "Б.1–Б.8"},
                    {"standard_id": "SP554_2026", "equation": "FIRE-D2-R2 earliest critical temperature"},
                ],
            ),
        ],
        "summary": {"checks": []},
    }


def test_fire_coefficients_are_engineering_narrative_not_raw_runtime_trace():
    text = "\n".join(_section_fire_coefficients(_report()))

    assert "Требуемые коэффициенты снижения прочности и жёсткости" in text
    assert "Коэффициент $γ_T$ — требование по прочности" in text
    assert r"\gamma_T=\frac{|N|}{\varphi\,A\,f_y\,\gamma_c}" in text
    assert r"\gamma_T=\frac{\left|-400000\right|}{0.388288295579\cdot 5282\cdot 255\cdot 0.9}=0.8498" in text
    assert "**$γ_T=0.8498$**" in text

    assert "Коэффициент $γ_e$ — требование по устойчивости" in text
    assert "**$γ_e=0.5309$**" in text
    assert "модуля упругости" in text
    assert "более низкой температуре" in text

    assert "N_force" not in text
    assert "phi_compression_sp554" not in text
    assert "A_gross" not in text
    assert "fy_norm" not in text
    assert "gamma_c_compression" not in text
    assert "FIRE-D2-R2" not in text
    assert "SP554_2026" not in text

    assert "СП 554.1311500.2026, раздел 9, п. 9.2, формула (9.2)" in text
    assert "СП 554.1311500.2026, п. 8.6; приложение Б, таблица Б.1 и рисунки Б.1–Б.8" in text


def test_full_report_replaces_old_coefficient_subsection_only():
    text = render_expertise_narrative_markdown_v090_fire_coeffs(_report())
    assert "### 4.2 Требуемые коэффициенты снижения прочности и жёсткости" in text
    assert "### 4.3 Критическая температура стали" in text
    assert "### 4.2 Коэффициенты $γ_T$ и $γ_e$" not in text
    assert "N_force" not in text
    assert "FIRE-D2-R2" not in text
