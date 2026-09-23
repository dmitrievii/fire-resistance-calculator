"""v0.92 progressive expertise-report presentation.

Executed engineering narrative remains owned by the retained v0.91 renderer.
This wrapper handles only the active ``PENDING_CURRENT`` projection introduced
by REPORT-IR v0.92: the current unfinished card is shown explicitly, while its
formula/substitution/result are withheld until a COMPLETE execution trace
exists.  No future DAG node is rendered.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from standard_core.report_ir_v092 import PENDING_CURRENT_STATE
from streamlit_expertise_report_v091 import render_expertise_narrative_markdown_v091


def _pending_blocks(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in report.get("blocks") or []
        if isinstance(row, Mapping) and row.get("progress_state") == PENDING_CURRENT_STATE
    ]


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
    markdown = render_expertise_narrative_markdown_v091(executed).rstrip()

    if not pending:
        return markdown + "\n"

    block = pending[0]
    title = str(block.get("title") or block.get("owner_node_id") or "Текущий шаг")
    pending_text = "\n".join(
        [
            "## Текущий незавершённый шаг",
            "",
            f"### {title}",
            "",
            "**Статус: PENDING.** Текущий шаг уже открыт и ожидает ввода данных.",
            "",
            "Расчётная формула, числовая подстановка и результат будут добавлены в отчёт только после фактического выполнения этого шага.",
            "",
        ]
    )
    if markdown:
        return markdown + "\n\n" + pending_text
    return "# Расчёт огнестойкости стального элемента\n\n" + pending_text


__all__ = ["render_expertise_narrative_markdown_v092"]
