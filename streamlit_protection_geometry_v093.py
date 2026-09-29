"""v0.103 protected-geometry report routing.

Protected Table-1 perimeter evidence is calculation evidence, not an interactive
question.  The runtime already publishes the perimeter trace and section factor
to the ledger/REPORT-IR, and the expertise report renders them in the protected
thermal reproducibility section.  This adapter therefore must not inject that
trace into subsequent guided cards.
"""
from __future__ import annotations

from typing import Any

_INSTALLED = "_fire_v093_protection_geometry_evidence_installed"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    # Deliberately no _render_card_body wrapper.  The previous v0.93 adapter
    # appended P_prot / delta_pr,prot evidence to every following interactive
    # card.  v0.103 keeps cards input-only; report rendering consumes the same
    # executed evidence from REPORT-IR.
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
