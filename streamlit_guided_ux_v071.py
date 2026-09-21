from __future__ import annotations

"""v0.71 presentation-only hardening for the guided Streamlit UX.

This adapter deliberately leaves normative equations, DAG routing, quantities and
PASS/FAIL gates untouched. It hardens three UI concerns discovered after v0.70:
section-property labels, gamma_ct preflight visibility, and idempotent guided UX
installation across Streamlit reruns.
"""

from copy import deepcopy
import re
from typing import Any, Mapping

import streamlit_guided_ux as _base


_INSTALL_SENTINEL = "_guided_ux_v071_installed"
_BASE_HUMANIZE = _base._humanize_mech7_card

_PROPERTY_PATTERNS = (
    (re.compile(r"^I([A-Za-z0-9]+)_mm4$"), "Момент инерции", "mm⁴"),
    (re.compile(r"^W([A-Za-z0-9]+)_mm3$"), "Момент сопротивления", "mm³"),
    (re.compile(r"^S([A-Za-z0-9]+)_mm3$"), "Статический момент", "mm³"),
    (re.compile(r"^i([A-Za-z0-9]+)_mm$"), "Радиус инерции", "mm"),
)

_GAMMA_CT_PREFLIGHT = (
    "При выборе «Да» система нормативно устанавливает γct = 1,1. "
    "Правило совместного применения γct с формулами (9)–(11) СП 554 "
    "в текущей квалифицированной реализации не закрыто: маршрут будет "
    "остановлен fail-closed до нормативного толкования. γct вручную не вводится."
)


def _derived_profile_label(key: str) -> tuple[str, str, str] | None:
    """Humanize only dimensionally unambiguous catalogue-property families.

    The suffix is preserved literally. For example, ``Wx1_mm3`` becomes symbol
    ``Wx1``; the UI does not invent an engineering interpretation for index 1.
    """
    for pattern, name, unit in _PROPERTY_PATTERNS:
        if pattern.fullmatch(key):
            symbol = key.rsplit("_", 1)[0]
            return name, symbol, unit
    return None


def _profile_line(core: Any, key: str, value: Any) -> str:
    label = _base.PROFILE_LABELS.get(key) or _derived_profile_label(key)
    if label:
        name, symbol, unit = label
        return f"- {name} **{symbol} = {core._fmt(value)} {unit}**"
    return f"- `{key}` = **{core._fmt(value)}**"


def _humanize_card(card: Mapping[str, Any]) -> dict[str, Any]:
    """Retain v0.70 humanization and expose the gamma_ct dead-end up front."""
    patched = _BASE_HUMANIZE(card)
    qids = {
        str(field.get("quantity_id") or "")
        for field in list(patched.get("fields") or [])
        if isinstance(field, Mapping)
    }
    if "gost27751_special_check" not in qids:
        return patched

    notes = deepcopy(dict(patched.get("notes") or {}))
    existing = str(notes.get("normative_warning") or "").strip()
    if _GAMMA_CT_PREFLIGHT not in existing:
        notes["normative_warning"] = (
            f"{existing}\n\n{_GAMMA_CT_PREFLIGHT}" if existing else _GAMMA_CT_PREFLIGHT
        )
    patched["notes"] = notes
    return patched


def install(core: Any) -> None:
    """Install v0.70 guided UX once per persistent Streamlit core module."""
    if getattr(core, _INSTALL_SENTINEL, False):
        return

    # The v0.70 closures resolve these module globals at render time, so the
    # presentation corrections remain isolated from standard_core and the DAG.
    _base._profile_line = _profile_line
    _base._humanize_mech7_card = _humanize_card
    _base.install(core)
    setattr(core, _INSTALL_SENTINEL, True)
