"""Final v0.92 expertise narrative wrapper for section weakening."""
from __future__ import annotations

from typing import Any, Mapping

from streamlit_expertise_report_v092 import render_expertise_narrative_markdown_v092
from streamlit_weakening_report_v092 import replace_weakening_section


def render_expertise_narrative_markdown_v092_weakening(report: Mapping[str, Any]) -> str:
    base = render_expertise_narrative_markdown_v092(report)
    return replace_weakening_section(base, report)


__all__ = ["render_expertise_narrative_markdown_v092_weakening"]
