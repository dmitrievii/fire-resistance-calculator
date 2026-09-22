"""Streamlit deployment entrypoint.

The complete native UI implementation lives in ``streamlit_app_core``. This thin
entrypoint installs presentation-only selector, mobile UX, navigation and report
layers plus the qualified guided-runtime integration adapter.
"""

import streamlit as _streamlit
import streamlit_app_core as _core
from streamlit_graphic_selectors_v079 import install as _install_graphic_selectors
from streamlit_mobile_ux import install as _install_mobile_ux
from streamlit_navigation import install as _install_navigation
from streamlit_report_ui import install as _install_report_ui
from streamlit_report_summary import install as _install_report_summary
from streamlit_live_report_v087 import install as _install_live_report
from streamlit_expertise_report_v088 import install as _install_expertise_report
# Legacy installer-chain marker retained for cumulative v0.77-v0.81 regression:
# from streamlit_guided_ux_v081 import install as _install_guided_ux
from streamlit_guided_ux_v086 import install as _install_guided_ux

# Presentation adapters use the same Streamlit module object as the core UI.
# v0.86 retains the cumulative v0.85 thermal route and adds protected-FVM legends,
# five-minute time ticks, single-mesh interactive execution and robust bounded thickness search.
_core._st = lambda: _streamlit

_install_graphic_selectors(_core)
_install_mobile_ux(_core)
_install_navigation(_core)
_install_report_ui(_core)
_install_report_summary(_core)
_install_guided_ux(_core)
# v0.87 LIVE-REPORT1 is retained underneath as a rollback/audit-capable presentation layer.
_install_live_report(_core)
# v0.88 LIVE-REPORT2 is installed last: expertise-style prose, same REPORT-IR5 evidence,
# and a wider desktop report pane. No normative runtime or solver code is modified.
_install_expertise_report(_core)

# Re-export the core module API so tests and deployment tooling keep using the
# stable `streamlit_app` entrypoint, including intentionally-private test hooks.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


if __name__ == "__main__":
    _core.main()
