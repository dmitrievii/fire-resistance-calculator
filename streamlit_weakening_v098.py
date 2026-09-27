"""v0.98 weakening UI/report closure.

Closes three retained defects without changing the engineering runtime:
* the legacy standalone I/W weakening boolean is hidden after the authoritative
  section_weakening_model has been accepted;
* REPORT-IR is reconciled with the canonical weakening executor trace;
* the final narrative uses the typed v0.92 weakening renderer, including manual
  net properties and the distinct purpose of SP16 formula (45).
"""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v090_install as _report
from standard_core.weakening_report_v098 import augment_from_session
from streamlit_weakening_atomic_v095 import _is_redundant_weakening_question
from streamlit_weakening_report_v092 import weakening_section as _typed_weakening_section

_INSTALLED = "_fire_v098_weakening_ui_report_closure_installed"
_WEAKENING_SECTION_RE = re.compile(
    r"(?ms)^### 1\.(?:2|3)\s+Ослабления(?: поперечного сечения| сечения)?\s*.*?"
    r"(?=^### 1\.[3-9]\s|^## 2\.\s|\Z)"
)
_ALPHA_HEADING = "#### Коэффициент ослабления стенки при сдвиге по формуле (45) СП 16"
_ALPHA_EXPLANATION = (
    "$\\alpha_h$ — отдельный коэффициент ослабления стенки **при сдвиге** по формуле (45) СП 16. "
    "Он не используется для определения площади нетто: $A_n$ получается независимо из геометрии ослабления."
)


def _ledger_value(env: Mapping[str, Any], qid: str):
    for row in reversed(list((env.get("state") or {}).get("ledger") or [])):
        if isinstance(row, Mapping) and row.get("quantity_id") == qid:
            return row.get("value")
    return None


def _redundant_answer(model: Any) -> bool | None:
    if isinstance(model, Mapping):
        holes = model.get("holes_present")
        return bool(holes) if isinstance(holes, bool) else None
    if model in {"no_weakening", "circular_bolt_holes"}:
        return model == "circular_bolt_holes"
    return None


def _normalized_weakening_section(report: Mapping[str, Any]) -> str:
    section = _typed_weakening_section(report)
    if not section:
        return ""
    section = section.replace(
        "### 1.3 Ослабления сечения",
        "### 1.2 Ослабления поперечного сечения",
        1,
    )
    if _ALPHA_HEADING in section and _ALPHA_EXPLANATION not in section:
        section = section.replace(
            _ALPHA_HEADING,
            _ALPHA_HEADING + "\n\n" + _ALPHA_EXPLANATION,
            1,
        )
    return section


def _replace_weakening(text: str, report: Mapping[str, Any]) -> str:
    section = _normalized_weakening_section(report)
    if not section:
        return text
    # Remove any retained v0.94/v0.95 weakening subsection.  Run repeatedly in
    # case an older session/narrative contains both historical 1.2 and 1.3 forms.
    while _WEAKENING_SECTION_RE.search(text):
        text = _WEAKENING_SECTION_RE.sub("", text, count=1)
    anchor = re.search(r"(?m)^## 2\.\s", text)
    if anchor:
        return text[:anchor.start()].rstrip() + "\n\n" + section + "\n\n" + text[anchor.start():]
    return text.rstrip() + "\n\n" + section + "\n"


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_card = core._render_card_body
    previous_build = _report.build_report_ir_v092
    previous_render = _report.render_expertise_narrative_markdown_v092

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        if _is_redundant_weakening_question(card):
            # Historical/edit cards are presentation-only here: the accepted
            # section_weakening_model is the single source of truth and this
            # legacy boolean must not be shown as a second engineering choice.
            if mode_key != "current":
                return None
            answer = _redundant_answer(_ledger_value(env, "section_weakening_model"))
            if answer is not None:
                fields = list(card.get("fields") or [])
                scalar = card.get("submit_shape") == "scalar"
                payload = answer if scalar else {fields[0]["quantity_id"]: answer}
                app.service.submit(
                    sid,
                    payload,
                    provenance={
                        "source": "section_weakening_model",
                        "ux_remediation": "v0.98_single_weakening_card",
                    },
                )
                core.st.rerun()
                return None
        return previous_card(app, sid, env, card, old_payload, old_provenance, mode_key)

    def build(model: Any, session_or_snapshot: Any) -> dict[str, Any]:
        base = previous_build(model, session_or_snapshot)
        return augment_from_session(base, session_or_snapshot)

    def render(report: Mapping[str, Any]) -> str:
        return _replace_weakening(previous_render(report), report)

    core._render_card_body = _render_card_body
    _report.build_report_ir_v092 = build
    _report.render_expertise_narrative_markdown_v092 = render
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_redundant_answer", "_normalized_weakening_section", "_replace_weakening"]
