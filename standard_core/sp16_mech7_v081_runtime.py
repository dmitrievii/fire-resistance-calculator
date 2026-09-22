"""Runtime for the v0.81 canonical z/y -> scalar SP554 stability handoff."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .sp16_mech7_v081_end_to_end_overlay import GOVERNING_AXIS_QID, HANDOFF_NODE_ID


def _positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{name} must be a positive finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise FireUIError(f"{name} must be a positive finite number")
    return result


def _phi(value: Any, name: str) -> float:
    result = _positive(value, name)
    if result > 1.0:
        raise FireUIError(f"{name} must not exceed 1.0")
    return result


def _curve(value: Any, name: str) -> str:
    if value not in {"a", "b", "c"}:
        raise FireUIError(f"{name} must be one of a, b, c")
    return str(value)


def governing_stability_handoff(values: Mapping[str, Any], _node: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Pass one internally consistent governing principal-axis tuple to SP554.

    ``phi_z_sp16`` and ``phi_y_sp16`` are already the final SP16 7.1.3
    coefficients produced by the qualified v0.76 runtime.  The smaller phi is
    the governing central-compression principal-plane check.  lambda-bar and
    curve are then taken from *that same axis*; they are never independently
    maximized/minimized because doing so would fabricate a tuple that does not
    describe either physical buckling plane.
    """
    axes = {
        "z": {
            "lambda_bar": _positive(values.get("lambda_bar_z"), "lambda_bar_z"),
            "curve": _curve(values.get("sp16_curve_z"), "sp16_curve_z"),
            "phi": _phi(values.get("phi_z_sp16"), "phi_z_sp16"),
        },
        "y": {
            "lambda_bar": _positive(values.get("lambda_bar_y"), "lambda_bar_y"),
            "curve": _curve(values.get("sp16_curve_y"), "sp16_curve_y"),
            "phi": _phi(values.get("phi_y_sp16"), "phi_y_sp16"),
        },
    }

    # Deterministic tie policy: z first.  Equal phi means neither principal
    # plane is less favourable in the SP16 central-compression check.
    axis = min(("z", "y"), key=lambda key: (axes[key]["phi"], 0 if key == "z" else 1))
    governing = axes[axis]
    return {
        "lambda_bar": governing["lambda_bar"],
        "sp16_buckling_curve_type": governing["curve"],
        "phi_sp16_formula8": governing["phi"],
        GOVERNING_AXIS_QID: axis,
    }


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    executor = governing_stability_handoff
    setattr(executor, "_sp16_v081_governing_stability_handoff", True)
    registry.register(HANDOFF_NODE_ID, executor)
    return registry


__all__ = ["governing_stability_handoff", "install_registry_remediation"]
