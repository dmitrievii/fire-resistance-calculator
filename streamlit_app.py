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
from streamlit_expertise_report_v089 import install as _install_expertise_narrative
from streamlit_expertise_report_v090_install import install as _install_expertise_mech9
from streamlit_mech9_v090 import install as _install_mech9_ux
from streamlit_fire_sp554_v091 import install as _install_fire_sp554_v091
from streamlit_canonical_actions_v092 import install as _install_canonical_actions_v092
from streamlit_ui_polish_v090 import install as _install_ui_polish_v090
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
# v0.90 presentation polish is deliberately installed after v0.86 so the final
# selector feedback and thermal-series styles are the active UI behavior.
_install_ui_polish_v090(_core)
# v0.90 MECH9 UX overlays the cumulative v0.86 guided application after all
# prior graph/runtime upgrades so both fresh and retained sessions receive it.
_install_mech9_ux(_core)
# v0.91 final-SP554 guided remediation is installed after MECH9 so the active
# DAG/runtime removes legacy E_norm/ambient-axis control from §§8.6/9.2 and
# publishes typed calculation evidence for the report layer.
_install_fire_sp554_v091(_core)
# v0.92 canonical action migration is installed after v0.91.  It rewrites the
# active graph/runtime contract to Mz strong bending, My weak bending and Mx
# torsion only.  Historical Mx/T answers are never semantically replayed across
# this boundary; retained sessions stop before the changed load-input state.
_install_canonical_actions_v092(_core)
# v0.87 LIVE-REPORT1 is retained underneath as a rollback/audit-capable presentation layer.
_install_live_report(_core)
# v0.88 widens the report pane and remains as the underlying expertise renderer.
_install_expertise_report(_core)
# v0.89 REPORT3 is retained as the semantic narrative base.
_install_expertise_narrative(_core)
# v0.90 REPORT4 + v0.91 SP554 refinement are installed last as an isolated renderer.
_install_expertise_mech9(_core)

# Re-export the core module API so tests and deployment tooling keep using the
# stable `streamlit_app` entrypoint, including intentionally-private test hooks.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


if __name__ == "__main__":
    _core.main()
