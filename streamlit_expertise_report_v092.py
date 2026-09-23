"""v0.92 progressive/compact expertise-report presentation.

Executed engineering narrative remains owned by the retained v0.91 renderer.
This wrapper adds active-v0.92 presentation guarantees without recalculating any
engineering value:

* only completed evidence plus one current ``PENDING_CURRENT`` step is shown;
* technical implementation vocabulary (runtime / REPORT-IR / presentation
  layer / trace) is removed from the main engineering narrative;
* excessive blank lines are collapsed; visual hierarchy is then controlled by
  report-scoped CSS so formula -> substitution -> result forms one compact
  block while subsection/chapter boundaries remain clearly separated.
"""
from __future__ import annotations

import copy
import re
from typing import Any, Mapping

from standard_core.report_ir_v092 import PENDING_CURRENT_STATE
from streamlit_expertise_report_v091 import render_expertise_narrative_markdown_v091

REPORT_MARKER_CLASS = "fire-report-v092-marker"
REPORT_COMPACT_CSS = r"""
<style>
/* Scoped by a marker placed inside the bordered report container. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] p {
    margin-top: 0.12rem !important;
    margin-bottom: 0.18rem !important;
    line-height: 1.28 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] ul,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] ol {
    margin-top: 0.18rem !important;
    margin-bottom: 0.28rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] li {
    margin-top: 0.04rem !important;
    margin-bottom: 0.04rem !important;
    line-height: 1.28 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h2 {
    margin-top: 1.65rem !important;
    margin-bottom: 0.52rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h3 {
    margin-top: 1.05rem !important;
    margin-bottom: 0.36rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) [data-testid="stMarkdownContainer"] h4 {
    margin-top: 0.68rem !important;
    margin-bottom: 0.24rem !important;
    padding-top: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) .katex-display {
    margin-top: 0.24rem !important;
    margin-bottom: 0.30rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.fire-report-v092-marker) hr {
    margin-top: 0.85rem !important;
    margin-bottom: 0.85rem !important;
}
</style>
""".strip()

_TECHNICAL_WORDING = (
    (re.compile(r"\bмеханическим\s+runtime\b", re.IGNORECASE), "механическим расчётом"),
    (re.compile(r"\bпо\s+выполненному\s+runtime\b", re.IGNORECASE), "по выполненному расчёту"),
    (re.compile(r"\bruntime\s+получил\b", re.IGNORECASE), "в расчёте получен"),
    (re.compile(r"\bruntime\b", re.IGNORECASE), "расчёт"),
    (re.compile(r"\bREPORT-IR\b", re.IGNORECASE), "расчётном протоколе"),
    (re.compile(r"\bpresentation-слой\b", re.IGNORECASE), "отчёт"),
    (re.compile(r"\bpresentation layer\b", re.IGNORECASE), "отчёт"),
    (re.compile(r"\btrace\b", re.IGNORECASE), "расчётный протокол"),
)


def _pending_blocks(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in report.get("blocks") or []
        if isinstance(row, Mapping) and row.get("progress_state") == PENDING_CURRENT_STATE
    ]


def compact_engineering_markdown(markdown: str) -> str:
    """Remove implementation jargon and excessive vertical whitespace only."""
    text = str(markdown or "")
    for pattern, replacement in _TECHNICAL_WORDING:
        text = pattern.sub(replacement, text)
    # Markdown requires one empty line between block elements; more than one is
    # visual noise and conflicts with the compact-report contract.
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    # Remove trailing spaces without rewriting equation/text content.
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def report_marker_html() -> str:
    return f'<span class="{REPORT_MARKER_CLASS}" aria-hidden="true"></span>'


def render_expertise_narrative_markdown_v092(report: Mapping[str, Any]) -> str:
    pending = _pending_blocks(report)
    if len(pending) > 1:
        raise ValueError("v0.92 progressive report may contain at most one PENDING_CURRENT block")

    # The retained renderer was written for completed trace evidence. Feed it
    # completed blocks only so it cannot describe an unfinished node as already
    # executed or expose a future formula from presentation metadata.
    executed = copy.deepcopy(dict(report))
    executed["blocks"] = [
        row
        for row in executed.get("blocks") or []
        if not (isinstance(row, Mapping) and row.get("progress_state") == PENDING_CURRENT_STATE)
    ]
    executed["block_count"] = len(executed["blocks"])
    markdown = compact_engineering_markdown(
        render_expertise_narrative_markdown_v091(executed)
    )

    if not pending:
        return markdown + ("\n" if markdown else "")

    block = pending[0]
    title = str(block.get("title") or block.get("owner_node_id") or "Текущий шаг")
    pending_text = compact_engineering_markdown(
        "\n".join(
            [
                "## Текущий незавершённый шаг",
                "",
                f"### {title}",
                "",
                "**Статус: PENDING.** Текущий шаг уже открыт и ожидает ввода данных.",
                "",
                "Расчётная формула, числовая подстановка и результат будут добавлены в отчёт только после фактического выполнения этого шага.",
            ]
        )
    )
    if markdown:
        return compact_engineering_markdown(markdown + "\n\n" + pending_text) + "\n"
    return "# Расчёт огнестойкости стального элемента\n\n" + pending_text + "\n"


__all__ = [
    "REPORT_COMPACT_CSS",
    "REPORT_MARKER_CLASS",
    "compact_engineering_markdown",
    "render_expertise_narrative_markdown_v092",
    "report_marker_html",
]
