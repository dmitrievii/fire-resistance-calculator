from __future__ import annotations

import streamlit_app as ui

from standard_core.fire_bridge2_qualified_state import _build_fire_bridge2_registry
from standard_core.fire_sp554_runtime_v091 import (
    _gamma_e_8_6_declarative_final,
    _phi_9_2_declarative_final,
)
from standard_core.fire_sp554_v091_guided_overlay import PHI_NODE_ID
from standard_core.profile_catalog import InterimProfileCatalog
from standard_core.sp16_mech7_v083_full_route_overlay import GAMMA_E_NODE_ID


def test_v091_package_import_does_not_shadow_frozen_dag_declarative_fallback():
    """Historical DAG nodes without Python executors must retain declarative execution."""
    registry = _build_fire_bridge2_registry(InterimProfileCatalog())

    # These missing registrations are intentional for the frozen v0.3.70 DAG:
    # fire_ui0 then executes each node's immutable calculation_spec.
    assert registry.get(PHI_NODE_ID) is None
    assert registry.get(GAMMA_E_NODE_ID) is None


def test_v091_streamlit_application_binds_final_executors_explicitly():
    """The active v0.91 application still receives the new final-SP554 executors."""
    app = ui._new_application()
    assert app.service.registry.get(PHI_NODE_ID) is _phi_9_2_declarative_final
    assert app.service.registry.get(GAMMA_E_NODE_ID) is _gamma_e_8_6_declarative_final
