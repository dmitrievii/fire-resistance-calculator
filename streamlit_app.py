"""Streamlit deployment entrypoint.

The complete native UI implementation lives in ``streamlit_app_core``. This thin
entrypoint installs presentation-only selector and mobile UX layers without
coupling normative runtime code to Streamlit layout details.
"""

import streamlit_app_core as _core
from streamlit_graphic_selectors import install as _install_graphic_selectors
from streamlit_mobile_ux import install as _install_mobile_ux

_install_graphic_selectors(_core)
_install_mobile_ux(_core)

# Re-export the core module API so tests and deployment tooling keep using the
# stable `streamlit_app` entrypoint, including intentionally-private test hooks.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


if __name__ == "__main__":
    _core.main()
