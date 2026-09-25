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
from streamlit_optional_actions_v095 import install as _install_optional_actions_v095
from streamlit_effective_length_v092 import install as _install_effective_length_v092
from streamlit_phi_evidence_v092 import install as _install_phi_evidence_v092
from streamlit_thermal_result_v092 import install as _install_thermal_result_v092
from streamlit_section_properties_v092 import install as _install_section_properties_v092
from streamlit_manual_net_v092 import install as _install_manual_net_v092
from streamlit_slenderness_evidence_v092 import install as _install_slenderness_evidence_v092
from streamlit_protection_geometry_v093 import install as _install_protection_geometry_v093
from streamlit_expertise_report_v093_thermal_repro import install as _install_thermal_report_v093
from streamlit_weakening_single_card_v094 import install as _install_weakening_single_card_v094
from streamlit_weakening_atomic_v095 import install as _install_weakening_atomic_v095
from streamlit_report_v094_install import install as _install_report_v094
from streamlit_ui_polish_v090 import install as _install_ui_polish_v090
from streamlit_guided_ux_v086 import install as _install_guided_ux

_core._st = lambda: _streamlit

_install_graphic_selectors(_core)
_install_mobile_ux(_core)
_install_navigation(_core)
_install_report_ui(_core)
_install_report_summary(_core)
_install_guided_ux(_core)
_install_section_properties_v092(_core)
_install_ui_polish_v090(_core)
_install_mech9_ux(_core)
_install_fire_sp554_v091(_core)
_install_gamma_ct_v092(_core)
_install_canonical_actions_v092(_core)
# v0.95: canonical action components not selected by the user are explicit
# physical zeros.  In particular, an N-only case must not require ambient_M_z.
_install_optional_actions_v095(_core)
_install_effective_length_v092(_core)
_install_phi_evidence_v092(_core)
_install_thermal_result_v092(_core)
_install_protection_geometry_v093(_core)
_install_manual_net_v092(_core)
_install_slenderness_evidence_v092(_core)
_install_weakening_single_card_v094(_core)
# v0.95 closes the remaining legacy I/W weakening compatibility question after
# the structured weakening model has already been accepted.
_install_weakening_atomic_v095(_core)
_install_live_report(_core)
_install_expertise_report(_core)
_install_expertise_narrative(_core)
_install_expertise_mech9(_core)
_install_thermal_report_v093(_core)
_install_report_v094(_core)

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

if __name__ == "__main__":
    _core.main()
