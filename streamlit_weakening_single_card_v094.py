"""v0.94 UX remediation: suppress the redundant second yes/no hole card.

The structured section-weakening editor is authoritative.  If a later legacy
card asks only whether circular bolt holes exist, reuse the already accepted
section_weakening_model and submit that boolean automatically.  Numeric/detail
cards are never bypassed.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v094_single_hole_card_installed"


def _ledger_value(env: Mapping[str, Any], qid: str):
    for row in reversed(list((env.get("state") or {}).get("ledger") or [])):
        if row.get("quantity_id") == qid:
            return row.get("value")
    return None


def _is_redundant_hole_boolean(card: Mapping[str, Any]) -> bool:
    text = " ".join(str(card.get(k) or "") for k in ("title", "prompt")).lower()
    fields = list(card.get("fields") or [])
    if not fields or not all(f.get("data_type") == "boolean" for f in fields):
        return False
    return ("отверст" in text and ("болт" in text or "кругл" in text)) or "bolt hole" in text


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = core._render_card_body

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        if mode_key == "current" and _is_redundant_hole_boolean(card):
            model = _ledger_value(env, "section_weakening_model")
            if model in {"no_weakening", "circular_bolt_holes"}:
                answer = model == "circular_bolt_holes"
                fields = list(card.get("fields") or [])
                scalar = card.get("submit_shape") == "scalar"
                payload = answer if scalar else {f["quantity_id"]: answer for f in fields}
                # Submit before Streamlit renders the legacy duplicate card.  The
                # accepted structured weakening choice is the sole user input.
                app.service.submit(sid, payload, provenance={
                    "source": "section_weakening_model",
                    "ux_remediation": "v0.94_single_card",
                })
                core.st.rerun()
        return previous(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
