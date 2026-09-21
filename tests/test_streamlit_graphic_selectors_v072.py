from __future__ import annotations

from types import SimpleNamespace

import streamlit_graphic_selectors_v072 as selectors


def test_v072_graphic_selector_install_is_idempotent_across_streamlit_reruns():
    def original(*args, **kwargs):
        return args, kwargs

    core = SimpleNamespace(_render_scalar_custom=original)

    selectors.install(core)
    first = core._render_scalar_custom
    selectors.install(core)

    assert core._render_scalar_custom is first
    assert first is not original
    assert getattr(core, "_fire_graphic_selectors_v072_installed") is True
