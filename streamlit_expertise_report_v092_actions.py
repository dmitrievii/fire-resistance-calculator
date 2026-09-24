"""v0.92 contextual canonical-action presentation overlay.

The retained v0.89 narrative predates the canonical SP16 action migration and
still knows the legacy ``Mx/Qx/T`` vocabulary. This module changes presentation
only. It reads already-recorded REPORT-IR values and replaces the load subsection
with the active canonical contract.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from streamlit_expertise_report_v092_weakening import (
    render_expertise_narrative_markdown_v092_weakening,
)

_ZERO_TOL = 1e-12

_CANONICAL_ACTIONS = (
    ("ambient_N_force", r"Продольная сила $N$"),
    ("ambient_M_z", r"Изгибающий момент $M_z$ (сильная ось z)"),
    ("ambient_M_y", r"Изгибающий момент $M_y$ (слабая ось y)"),
    ("ambient_M_x", r"Крутящий момент $M_x$"),
    ("ambient_Q_z", r"Поперечная сила $Q_z$"),
    ("ambient_Q_y", r"Поперечная сила $Q_y$"),
    ("ambient_B_bimoment", r"Бимомент $B$"),
)

_ACTION_SECTION_RE = re.compile(
    r"(?ms)^### 1\.2 Расч[ёе]тные усилия\s*\n.*?(?=^### 1\.3\s|^## 2\.\s|\Z)"
)
_LEGACY_ZERO_PARAGRAPH_RE = re.compile(
    r"(?m)^Для данного сочетания .*?соответствующие проверки изгиба, среза, "
    r"кручения и их сочетаний не являются определяющими\.\s*$"
)


def _numeric_raw(hit: Any) -> float | None:
    if not hit:
        return None
    raw = _v089._row_raw(hit)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    return value if math.isfinite(value) else None


def _canonical_action_hits(report: Mapping[str, Any]) -> list[tuple[str, str, Any]]:
    active: list[tuple[str, str, Any]] = []
    for qid, label in _CANONICAL_ACTIONS:
        hit = _v089._find_row(report, qids=(qid,))
        value = _numeric_raw(hit)
        if value is None or abs(value) <= _ZERO_TOL:
            continue
        active.append((qid, label, hit))
    return active


def canonical_actions_section(report: Mapping[str, Any]) -> str:
    active = _canonical_action_hits(report)
    if not active:
        return ""

    lines = [
        "### 1.2 Расчётные усилия",
        "",
        "Для текущего расчётного сочетания ненулевыми являются только следующие силовые факторы:",
        "",
    ]
    for _, label, hit in active:
        lines.append(f"- {label}: **{_v089._display(hit)}**")
    lines.extend(
        [
            "",
            "Знаки усилий сохранены в соответствии с исходным вводом и расчётным протоколом.",
            "",
        ]
    )
    return "\n".join(lines)


def _normalize_spacing_without_structural_pruning(markdown: str) -> str:
    """Compact whitespace while preserving pre-existing chapter/subchapter headings.

    The action overlay owns only the action subsection. Running the global v0.92
    empty-heading pruner here is unsafe after removal of legacy zero-action prose:
    it can delete otherwise valid neighbouring chapter headings that this overlay
    does not own.
    """
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", str(markdown or ""))
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def replace_contextual_actions_section(markdown: str, report: Mapping[str, Any]) -> str:
    """Replace legacy force prose without touching unrelated report structure."""
    text = str(markdown or "")
    section = canonical_actions_section(report)
    match = _ACTION_SECTION_RE.search(text)
    if match:
        replacement = section + "\n" if section else ""
        text = _ACTION_SECTION_RE.sub(replacement, text, count=1)
    elif section:
        anchor = re.search(r"(?m)^### 1\.3\s", text) or re.search(r"(?m)^## 2\.\s", text)
        if anchor:
            text = text[: anchor.start()] + section + "\n\n" + text[anchor.start() :]
        else:
            text = text.rstrip() + "\n\n" + section

    text = _LEGACY_ZERO_PARAGRAPH_RE.sub("", text)
    return _normalize_spacing_without_structural_pruning(text) + "\n"


def render_expertise_narrative_markdown_v092_actions(report: Mapping[str, Any]) -> str:
    base = render_expertise_narrative_markdown_v092_weakening(report)
    return replace_contextual_actions_section(base, report)


__all__ = [
    "canonical_actions_section",
    "replace_contextual_actions_section",
    "render_expertise_narrative_markdown_v092_actions",
]
