from __future__ import annotations

import re

from streamlit_expertise_report_v092 import (
    REPORT_COMPACT_CSS,
    REPORT_MARKER_CLASS,
    compact_engineering_markdown,
    report_marker_html,
)


def _margin_top_for(selector: str) -> float:
    match = re.search(
        rf"\] {re.escape(selector)} \{{[^}}]*margin-top:\s*([0-9.]+)rem",
        REPORT_COMPACT_CSS,
        flags=re.DOTALL,
    )
    assert match, f"no scoped margin-top for {selector}"
    return float(match.group(1))


def test_compact_markdown_collapses_excess_blank_lines_but_preserves_markdown_block_separation():
    source = (
        "## Глава\n\n\n\n"
        "### Подраздел\n\n\n"
        "Пояснение.\n\n\n\n"
        "$$ a=b $$\n\n\n"
        "Подстановка = результат.\n"
    )
    rendered = compact_engineering_markdown(source)

    assert "\n\n\n" not in rendered
    assert "## Глава\n\n### Подраздел" in rendered
    assert "Пояснение.\n\n$$ a=b $$\n\nПодстановка = результат." in rendered


def test_main_engineering_markdown_removes_runtime_report_ir_presentation_and_trace_jargon():
    source = (
        "Механическим runtime получен результат.\n\n"
        "По выполненному runtime получено значение.\n\n"
        "В текущем REPORT-IR значение опубликовано.\n\n"
        "Presentation-слой его не восстанавливает.\n\n"
        "Пошаговый temperature trace остаётся отдельно."
    )
    rendered = compact_engineering_markdown(source)
    lowered = rendered.lower()

    assert "runtime" not in lowered
    assert "report-ir" not in lowered
    assert "presentation-слой" not in lowered
    assert " trace" not in lowered
    assert "механическим расчётом" in lowered
    assert "по выполненному расчёту" in lowered
    assert "расчётном протоколе" in lowered


def test_report_css_is_marker_scoped_and_hierarchy_is_compact_inside_sections():
    assert REPORT_MARKER_CLASS in REPORT_COMPACT_CSS
    assert ":has(.fire-report-v092-marker)" in REPORT_COMPACT_CSS
    assert report_marker_html() == '<span class="fire-report-v092-marker" aria-hidden="true"></span>'

    h2 = _margin_top_for("h2")
    h3 = _margin_top_for("h3")
    h4 = _margin_top_for("h4")
    assert h2 > h3 > h4

    paragraph = re.search(
        r"\] p \{[^}]*margin-top:\s*([0-9.]+)rem[^}]*margin-bottom:\s*([0-9.]+)rem[^}]*line-height:\s*([0-9.]+)",
        REPORT_COMPACT_CSS,
        flags=re.DOTALL,
    )
    assert paragraph
    margin_top, margin_bottom, line_height = map(float, paragraph.groups())
    assert margin_top < h4
    assert margin_bottom < h4
    assert line_height <= 1.3

    katex = re.search(
        r"\.katex-display \{[^}]*margin-top:\s*([0-9.]+)rem[^}]*margin-bottom:\s*([0-9.]+)rem",
        REPORT_COMPACT_CSS,
        flags=re.DOTALL,
    )
    assert katex
    assert max(map(float, katex.groups())) < h4
