"""v0.83 runtime bridge for the SP554 8.6 gamma-e dual quantity contract."""
from __future__ import annotations

from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry
from .sp16_mech7_v082_runtime import gamma_e_compression_8_6
from .sp16_mech7_v083_full_route_overlay import (
    GAMMA_E_INTERNAL_QID,
    GAMMA_E_NODE_ID,
    GAMMA_E_REQUIRED_QID,
)


def gamma_e_8_6_dual_contract(values: Mapping[str, Any], node: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Expose one exact SP554 8.6 gamma_e under both internal and consumer IDs."""
    internal = gamma_e_compression_8_6(values, node)[GAMMA_E_INTERNAL_QID]
    return {
        GAMMA_E_INTERNAL_QID: internal,
        GAMMA_E_REQUIRED_QID: internal,
    }


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    executor = gamma_e_8_6_dual_contract
    setattr(executor, "_sp554_v083_gamma_e_dual_contract", True)
    registry.register(GAMMA_E_NODE_ID, executor)
    return registry


__all__ = ["gamma_e_8_6_dual_contract", "install_registry_remediation"]
