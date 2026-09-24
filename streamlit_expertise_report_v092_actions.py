"""v0.92 contextual canonical-action presentation overlay.

The retained v0.89 narrative predates the canonical SP16 action migration and
still knows the legacy ``Mx/Qx/T`` vocabulary.  This module changes presentation
only.  It reads already-recorded REPORT-IR values and replaces the load subsection
with the active canonical contract:

* N  - axial force;
* Mz - strong-axis bending;
* My - weak-axis bending;
* Mx - torsion only;
* Qz/Qy - separate shear components;
* B  - direct bimoment.

Only non-zero components that are actually present in the executed evidence are
shown in the main report.  Signs are preserved exactly.  No resultant shear,
legacy-axis translation or engineering recomputation is performed here.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from streamlit_expertise_report_v092 import compact_engineering_markdown
from streamlit_expertise_report_v092_weakening import (
    render_expertise_narrative_markdown_v092_weakening,
)

_ZERO_TOL = 1e-12

# qid, report label.  Ordering is the canonical action-contract ordering used
# throughout the active v0.92 UI and mechanical handoff.
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
    """Return present, non-zero canonical actions from recorded report evidence."""
    active: list[tuple[str, str, Any]] = []
    for qid, label in _CANONICAL_ACTIONS:
        hit = _v089._find_row(report, qids=(qid,))
        value = _numeric_raw(hit)
        if value is None or abs(value) <= _ZERO_TOL:
            continue
        active.append((qid, label, hit))
    return active


def canonical_actions_section(report: Mapping[str, Any]) -> str:
    """Render only active canonical action components; preserve trace signs/units."""
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


def replace_contextual_actions_section(markdown: str, report: Mapping[str, Any]) -> str:
    """Replace legacy force prose without touching executed engineering results."""
    text = str(markdown or "")
    section = canonical_actions_section(report)
    match = _ACTION_SECTION_RE.search(text)
    if match:
        replacement = section + "\n" if section else ""
        text = _ACTION_SECTION_RE.sub(replacement, text, count=1)
    elif section:
        # Chapter 1 can legitimately omit the legacy force subsection. Insert
        # before weakening when present, otherwise directly before Chapter 2.
        anchor = re.search(r"(?m)^### 1\.3\s", text) or re.search(r"(?m)^## 2\.\s", text)
        if anchor:
            text = text[: anchor.start()] + section + "\n\n" + text[anchor.start() :]
        else:
            text = text.rstrip() + "\n\n" + section

    # Retained v0.89 additionally emitted a prose paragraph enumerating zero
    # legacy Mx/Qx/T actions.  That paragraph is presentation-only and must not
    # leak obsolete axis semantics into the active v0.92 main report.
    text = _LEGACY_ZERO_PARAGRAPH_RE.sub("", text)
    return compact_engineering_markdown(text) + "\n"


def render_expertise_narrative_markdown_v092_actions(report: Mapping[str, Any]) -> str:
    base = render_expertise_narrative_markdown_v092_weakening(report)
    return replace_contextual_actions_section(base, report)


__all__ = [
    "canonical_actions_section",
    "replace_contextual_actions_section",
    "render_expertise_narrative_markdown_v092_actions",
]
