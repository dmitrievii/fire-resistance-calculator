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
from streamlit_sp554_gamma_ct_v092 import install as _install_gamma_ct_v092
from streamlit_canonical_actions_v092 import install as _install_canonical_actions_v092
from streamlit_effective_length_v092 import install as _install_effective_length_v092
from streamlit_phi_evidence_v092 import install as _install_phi_evidence_v092
from streamlit_thermal_result_v092 import install as _install_thermal_result_v092
from streamlit_section_properties_v092 import install as _install_section_properties_v092
from streamlit_manual_net_v092 import install as _install_manual_net_v092
from streamlit_slenderness_evidence_v092 import install as _install_slenderness_evidence_v092
from streamlit_protection_geometry_v093 import install as _install_protection_geometry_v093
from streamlit_expertise_report_v093_thermal_repro import install as _install_thermal_report_v093
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
# v0.92 section-property preview replaces historical catalogue x/y labels with
# the active physical principal-axis contract: z-z strong, y-y weak. It is a
# presentation-only adapter and does not mutate the selected catalogue row.
_install_section_properties_v092(_core)
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
# v0.92 removes the obsolete boolean gamma_ct question structurally. Final
# SP554 gamma_ct=1.1 is a mandatory runtime constant and cannot be selected or
# overridden by the user. Retained-session replay drops the historical answer.
_install_gamma_ct_v092(_core)
# v0.92 canonical action migration runs on the already-remediated guided graph.
# It rewrites the active contract to Mz strong bending, My weak bending and Mx
# torsion only. Historical Mx/T answers are never semantically replayed across
# this boundary; retained sessions stop before the changed load-input state.
_install_canonical_actions_v092(_core)
# v0.92 MECH7 binds the already audited Stage-N7 Section-10 route census into
# the active z/y effective-length card. The adapter does not duplicate any
# equations; it records typed l_eff -> lambda -> lambda_bar -> phi evidence.
_install_effective_length_v092(_core)
# v0.92 full-phi instrumentation enriches the already-produced z/y state with
# Table-7 alpha/beta, Eq.(9) delta and Eq.(8)/cap evidence. It validates against
# the qualified runtime phi and replays retained sessions through that contract.
_install_phi_evidence_v092(_core)
# v0.92 thermal-result presentation is independent from later R_req input: once
# the protected §12.5 trace exists in the ledger, its FVM curves are shown on
# the current interactive card instead of waiting for another routing step.
_install_thermal_result_v092(_core)
# v0.93 exposes the already-executed FIRE-UI1.9 Table-1 protected perimeter and
# protected reduced thickness on the first card after contour/box selection,
# before the user is asked for protection thickness.
_install_protection_geometry_v093(_core)
# v0.92 restores the explicit manual-net branch only after all ambient runtime
# binders are installed. A_net remains geometry-derived; user I/W values are
# canonical z/y and receive typed downstream-consumption evidence.
_install_manual_net_v092(_core)
# v0.92 Table-32 evidence must be installed after manual-net because manual-net
# also wraps the MECH7 primary binder. This final binder wrapper records
# alpha -> lambda_u -> lambda/lambda_u -> PASS/FAIL and validates exact parity.
_install_slenderness_evidence_v092(_core)
# v0.87 LIVE-REPORT1 is retained underneath as a rollback/audit-capable presentation layer.
_install_live_report(_core)
# v0.88 widens the report pane and remains as the underlying expertise renderer.
_install_expertise_report(_core)
# v0.89 REPORT3 is retained as the semantic narrative base.
_install_expertise_narrative(_core)
# v0.90 REPORT4 + v0.91/v0.92 SP554/report refinements are installed last as an isolated renderer.
_install_expertise_mech9(_core)
# v0.93 adds a runtime-evidence-only thermal reproducibility passport. It does
# not recompute temperatures or normative verdicts and deliberately leaves the
# existing T0 interaction contract unchanged (audit item #17 is out of scope).
_install_thermal_report_v093(_core)

# Re-export the core module API so tests and deployment tooling keep using the
# stable `streamlit_app` entrypoint, including intentionally-private test hooks.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


if __name__ == "__main__":
    _core.main()
