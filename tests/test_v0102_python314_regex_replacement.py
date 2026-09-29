from __future__ import annotations

import streamlit_expertise_report_v092_zy as zy


def test_v0102_zy_section_replacement_treats_latex_backslashes_verbatim(monkeypatch):
    section = (
        "### 3.1 Расчётные длины, гибкости и коэффициенты устойчивости\n\n"
        r"$$\varphi_z=\frac{19.74}{\delta_z+\sqrt{\delta_z^2}}$$"
        "\n\n"
        r"$$\bar{\lambda}_z=1.25$$"
        "\n"
    )
    monkeypatch.setattr(zy, "zy_stability_section", lambda report: section)

    original = (
        "## 3. Устойчивость\n\n"
        "### 3.1 Расчётные длины и гибкости\n\n"
        "old section\n\n"
        "### 3.2 Проверка устойчивости\n\n"
        "next section\n"
    )

    result = zy.replace_zy_stability_section(original, {})

    assert r"\varphi_z" in result
    assert r"\frac{19.74}" in result
    assert r"\sqrt{\delta_z^2}" in result
    assert r"\bar{\lambda}_z" in result
    assert "old section" not in result
    assert "### 3.2 Проверка устойчивости" in result


def test_v0102_no_replacement_template_escape_parsing_regression():
    # Minimal direct reproduction of the Streamlit crash path: a generated
    # report section containing LaTeX \varphi must replace an existing §3.1.
    section = r"### 3.1 Расчётные длины и гибкости\n\n$\varphi_y=0.8$"
    text = "### 3.1 Расчётные длины и гибкости\nold\n## 4. Fire\n"

    replacement = section + "\n"
    result = zy._SECTION_RE.sub(lambda _match: replacement, text, count=1)

    assert r"$\varphi_y=0.8$" in result
    assert "## 4. Fire" in result
