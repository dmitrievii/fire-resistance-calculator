from __future__ import annotations

"""v0.72 idempotent adapter for the existing graphic selector presentation layer.

Streamlit re-executes the entrypoint on reruns while ``streamlit_app_core`` stays
imported.  The legacy selector installer wraps ``_render_scalar_custom`` every
time it is called.  This adapter guarantees one installation per persistent core
module and changes no selector values, DAG routing or normative semantics.
"""

from typing import Any

import streamlit_graphic_selectors as _base


_INSTALL_SENTINEL = "_fire_graphic_selectors_v072_installed"


def install(core: Any) -> None:
    if getattr(core, _INSTALL_SENTINEL, False):
        return
    _base.install(core)
    setattr(core, _INSTALL_SENTINEL, True)


__all__ = ["install"]
