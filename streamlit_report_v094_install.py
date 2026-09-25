"""Install cumulative v0.94/v0.95 report remediation."""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v090_install as _report
from streamlit_expertise_report_v094_weakening import _patch_gamma_aliases
from streamlit_report_v095_upstream_closure import _insert_weakening

_INSTALLED = "_fire_v094_material_weakening_report_installed"
_THERMAL_PASSPORT_RE = re.compile(r"(?ms)^### 5\.3 Паспорт воспроизводимости.*?(?=^## 6\. Заключение|^## Текущий незавершённый шаг|\Z)")


def _has_thermal_evidence(report: Mapping[str, Any]) -> bool:
    tokens = ("thermal", "unprotected", "protected", "sp554_12", "fire-d3")
    qids = {"R_unprot", "R_prot", "R_fact", "thermal_unprotected_trace", "thermal_protected_trace"}
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping) or block.get("progress_state") == "PENDING_CURRENT":
            continue
        owner = str(block.get("owner_node_id") or "").lower()
        if any(t in owner for t in tokens):
            return True
        for row in block.get("outputs") or []:
            if isinstance(row, Mapping) and row.get("quantity_id") in qids:
                return True
    return False


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = _report.render_expertise_narrative_markdown_v092

    def render(report: Mapping[str, Any]) -> str:
        patched = _patch_gamma_aliases(report)
        text = previous(patched)
        # v0.95 consumes the exact producer-owned calculation_trace nested in
        # net_section_geometry_2d.  No presentation recomputation is used.
        text = _insert_weakening(text, patched)
        if not _has_thermal_evidence(patched):
            text = _THERMAL_PASSPORT_RE.sub(lambda _m: "", text, count=1)
        return text

    _report.render_expertise_narrative_markdown_v092 = render
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
