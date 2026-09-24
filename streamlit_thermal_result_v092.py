"""v0.92 UI remediation: render completed protected FVM results immediately.

The protected SP554 §12.5 calculation is complete once
``protection_12_5_calculation_trace`` exists in the guided ledger.  The thermal
curve and FVM visualisation depend on that trace only; ``R_req`` is a later
assessment/design input and must not gate rendering of an already completed
thermal calculation.

Older UI layers rendered FVM output only while a non-interactive calculation
card was being rendered.  Automatic progression can move the session directly
to the next interactive card, so the trace is already available but the graph
is hidden until a later rerun.  This installer also renders the completed trace
from the current interactive card.
"""
from __future__ import annotations

from typing import Any, Mapping

import streamlit_guided_ux_v084 as _v084
import streamlit_guided_ux_v086 as _v086

_INSTALLED = "_fire_v092_completed_thermal_result_installed"


def completed_protected_trace(core: Any, env: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return a completed protected thermal trace without consulting R_req."""
    trace = _v084._fdm_trace_from_env(core, env)
    if not isinstance(trace, Mapping):
        return None
    # Direct §12.5 result carries the visualisation at the top level.  Inverse
    # routes may expose a selected result; _fdm_trace_from_env already unwraps
    # that representation.
    if not isinstance(trace.get("visualization"), Mapping):
        return None
    return trace


def should_render_completed_protected_result(core: Any, env: Mapping[str, Any]) -> bool:
    """Pure topology predicate: completed trace => render, independent of R_req."""
    return completed_protected_trace(core, env) is not None


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_body = core._render_card_body

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        # Render before the next question so a finished thermal calculation is
        # visible immediately.  Deliberately do not inspect
        # required_fire_resistance_min / R_req here.
        if should_render_completed_protected_result(core, env):
            _v086._render_fdm_visualizations(core, env)
        return previous_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = [
    "completed_protected_trace",
    "install",
    "should_render_completed_protected_result",
]
