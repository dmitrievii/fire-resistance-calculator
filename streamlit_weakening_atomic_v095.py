"""v0.95: make section_weakening_model authoritative for legacy I/W questions.

The current Streamlit core renders interactive input through ``_render_card_body``.
This overlay therefore operates on the card contract, not the removed historical
``_render_input_node`` hook.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v095_weakening_atomic_installed"


def _ledger_value(env: Mapping[str, Any], qid: str):
    for row in reversed(list((env.get("state") or {}).get("ledger") or [])):
        if row.get("quantity_id") == qid:
            return row.get("value")
    return None


def _is_redundant_weakening_question(card: Mapping[str, Any]) -> bool:
    text = " ".join(str(card.get(k) or "") for k in ("title", "prompt")).lower()
    fields = list(card.get("fields") or [])
    if len(fields) != 1 or fields[0].get("data_type") != "boolean":
        return False
    qid = str(fields[0].get("quantity_id") or "").lower()
    title_tokens = (
        "учитывать изменение моментов инерции",
        "моментов сопротивления после ослабления",
        "изменение моментов инерции и моментов сопротивления",
    )
    qid_tokens = ("net", "weakening", "inertia", "section_modulus", "moment_resistance")
    return any(t in text for t in title_tokens) or any(t in qid for t in qid_tokens)


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = core._render_card_body

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        if mode_key == "current" and _is_redundant_weakening_question(card):
            model = _ledger_value(env, "section_weakening_model")
            if isinstance(model, Mapping):
                answer = bool(model.get("holes_present"))
            elif model in {"no_weakening", "circular_bolt_holes"}:
                answer = model == "circular_bolt_holes"
            else:
                answer = None
            if answer is not None:
                fields = list(card.get("fields") or [])
                scalar = card.get("submit_shape") == "scalar"
                payload = answer if scalar else {fields[0]["quantity_id"]: answer}
                app.service.submit(sid, payload, provenance={
                    "source": "section_weakening_model",
                    "ux_remediation": "v0.95_atomic_weakening",
                })
                core.st.rerun()
                return
        return previous(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
