"""Runtime for v0.82 SP554 8.6 gamma_e producer."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .sp16_mech7_v082_guided_route_overlay import GAMMA_E_NODE_ID, GAMMA_E_QID


def _positive(values: Mapping[str, Any], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"SP554 8.6 gamma_e requires {key}")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise FireUIError(f"SP554 8.6 gamma_e requires positive finite {key}")
    return result


def _signed(values: Mapping[str, Any], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"SP554 8.6 gamma_e requires {key}")
    result = float(value)
    if not math.isfinite(result):
        raise FireUIError(f"SP554 8.6 gamma_e requires finite {key}")
    return result


def gamma_e_compression_8_6(values: Mapping[str, Any], _node: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Calculate gamma_e=N/N_E for the exact governing principal-axis state.

    SP554 8.6 uses the Euler denominator pi^2*E*J/l_eff^2.  The active SP16
    route already carries exact principal-axis l_eff and radius i.  For that
    same axis J=A*i^2, so this producer is algebraically identical to the
    published expression and does not reconstruct/average a scalar axis.
    """
    n = abs(_signed(values, "N_force"))
    axis = values.get("sp16_v081_governing_stability_axis")
    if axis not in {"z", "y"}:
        raise FireUIError("SP554 8.6 gamma_e requires the qualified v0.81 governing z/y axis")
    area = _positive(values, "A_gross")
    elastic = _positive(values, "E_norm")
    leff = _positive(values, f"sp16_l_eff_{axis}")
    radius = _positive(values, f"sp16_i_{axis}")
    inertia = area * radius * radius
    gamma_e = n * leff * leff / (math.pi * math.pi * elastic * inertia)
    if not math.isfinite(gamma_e) or gamma_e < 0.0:
        raise FireUIError("SP554 8.6 gamma_e produced an invalid value")
    return {GAMMA_E_QID: gamma_e}


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    executor = gamma_e_compression_8_6
    setattr(executor, "_sp554_v082_gamma_e_8_6", True)
    registry.register(GAMMA_E_NODE_ID, executor)
    return registry


__all__ = ["gamma_e_compression_8_6", "install_registry_remediation"]
