"""v0.95: make section_weakening_model authoritative for all legacy weakening questions."""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v095_weakening_atomic_installed"


def _is_redundant_weakening_question(step: Mapping[str, Any]) -> bool:
    title = str(step.get("title") or "").lower()
    qids = {str(x) for x in step.get("input_quantity_ids") or []}
    # v0.94 already handled the repeated holes-present boolean.  v0.95 also
    # handles the retained choice asking whether I/W net properties are used.
    title_tokens = (
        "учитывать изменение моментов инерции",
        "моментов сопротивления после ослабления",
        "изменение моментов инерции и моментов сопротивления",
    )
    qid_tokens = ("net", "weakening", "inertia", "section_modulus", "moment_resistance")
    return any(t in title for t in title_tokens) or (
        len(qids) == 1 and any(any(t in q.lower() for t in qid_tokens) for q in qids)
    )


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = core._render_input_node

    def render_input_node(app, sid, step):
        session = app.service.get_session(sid)
        values = dict(session.snapshot().get("values") or {})
        model = values.get("section_weakening_model")
        if isinstance(model, Mapping) and _is_redundant_weakening_question(step):
            qids = list(step.get("input_quantity_ids") or [])
            if len(qids) == 1:
                qid = qids[0]
                # The structured model is authoritative.  Holes route uses the
                # qualified net I/W calculation; no-weakening route uses gross
                # identity properties.  This is replay of an already explicit
                # user choice, not a new engineering assumption.
                answer = bool(model.get("holes_present"))
                try:
                    app.answer(sid, qid, answer)
                    core.st.rerun()
                    return
                except Exception:
                    # Fail back to the native card if this is not a boolean
                    # compatibility node; never seed an incompatible value.
                    pass
        return previous(app, sid, step)

    core._render_input_node = render_input_node
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
