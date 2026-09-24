"""Deployment smoke guard for the v0.92 Streamlit startup import chain.

This test exists because py_compile does not resolve imported symbols.  A module
can therefore compile successfully while Streamlit Cloud fails at startup with
ImportError.  Keep this as an actual import regression.
"""
from __future__ import annotations


def test_manual_net_streamlit_overlay_import_chain_resolves() -> None:
    import streamlit_manual_net_v092 as overlay
    from standard_core import fire_ui14_manual_net_v092 as runtime
    from standard_core import fire_ui14_section_weakening as weakening

    assert callable(overlay.install)
    assert callable(runtime.install_registry_remediation)
    assert isinstance(runtime.MANUAL_MODE, str)
    assert isinstance(weakening.WEAKENING_TRACE_SCHEMA, str)
    assert callable(weakening._finite_positive)
    assert callable(weakening._geometry_dimensions)
    assert callable(weakening._gross_required)
