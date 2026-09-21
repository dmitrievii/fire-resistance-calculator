"""Streamlit deployment entrypoint.

The complete native UI implementation lives in ``streamlit_app_core``. This thin
entrypoint installs presentation-only selector, mobile UX, navigation and report
layers plus the qualified guided-runtime integration adapter.
"""

import streamlit as _streamlit
import streamlit_app_core as _core
from streamlit_graphic_selectors_v072 import install as _install_graphic_selectors
from streamlit_mobile_ux import install as _install_mobile_ux
from streamlit_navigation import install as _install_navigation
from streamlit_report_ui import install as _install_report_ui
from streamlit_report_summary import install as _install_report_summary
from streamlit_guided_ux_v075 import install as _install_guided_ux

# Presentation adapters use the same Streamlit module object as the core UI.
# v0.75 preserves the v0.74 source-backed prerequisite hydration, inserts the
# omitted SP16 Section-10 member-length/restraint route, and upgrades active
# principal-axis stability semantics from legacy x/y to canonical z/y.
_core._st = lambda: _streamlit

_install_graphic_selectors(_core)
_install_mobile_ux(_core)
_install_navigation(_core)
_install_report_ui(_core)
_install_report_summary(_core)
_install_guided_ux(_core)

# Re-export the core module API so tests and deployment tooling keep using the
# stable `streamlit_app` entrypoint, including intentionally-private test hooks.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


if __name__ == "__main__":
    _core.main()
