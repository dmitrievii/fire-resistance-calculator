"""v0.91 normative remediation for final SP 554.1311500.2026.

The fire branch reuses the qualified SP16 member geometry and buckling-curve
classification.  It does not reuse the ambient SP16 relative slenderness or
ambient phi, because SP554 9.2 defines the fire relative slenderness with
Ryn/E.  The fire phi is evaluated by the same SP16 central-compression
producer used by the ambient engine.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import axial_members as _axial
from . import fire_sp554_runtime as _runtime
from . import fire_bridge2_qualified_state as _bridge2


GAMMA_CT = 1.1

# Published final Table B.1 values that differ from the pre-publication
# dataset used by FIRE-D2.  Unlisted rows/groups remain unchanged.
_FINAL_B1_OVERRIDES: dict[str, dict[float, tuple[float, float]]] = {
    "increased": {
        300.0: (0.96, 0.84),
        450.0: (0.81, 0.65),
        500.0: (0.75, 0.60),
        550.0: (0.71, 0.55),
    },
    "high": {
        300.0: (0.95, 0.89),
    },
}


def _install_final_b1() -> None:
    for group, overrides in _FINAL_B1_OVERRIDES.items():
        current = _runtime._B1[group]
        replaced: list[tuple[float, float, float]] = []
        for temperature, gamma_e, gamma_t in current:
            pair = overrides.get(float(temperature))
            if pair is None:
                replaced.append((float(temperature), float(gamma_e), float(gamma_t)))
            else:
                replaced.append((float(temperature), float(pair[0]), float(pair[1])))
        _runtime._B1[group] = tuple(replaced)


def _fire_stability_state_from_geometry(
    *,
    lambda_geom: float,
    ryn_n_mm2: float,
    elastic_modulus_n_mm2: float,
    curve: str,
) -> tuple[float, float]:
    """Return (lambda_bar_fire, phi_fire) for final SP554 9.2.

    The geometry and curve type are qualified SP16 outputs.  Only the
    nondimensional slenderness is formed again because SP554 requires Ryn/E.
    The phi producer itself is the shared SP16 implementation.
    """
    if not math.isfinite(lambda_geom) or lambda_geom < 0.0:
        raise ValueError("geometric slenderness lambda must be finite and >= 0")
    if not math.isfinite(ryn_n_mm2) or ryn_n_mm2 <= 0.0:
        raise ValueError("Ryn must be finite and > 0")
    if not math.isfinite(elastic_modulus_n_mm2) or elastic_modulus_n_mm2 <= 0.0:
        raise ValueError("E must be finite and > 0")
    curve_norm = str(curve).lower()
    if curve_norm not in {"a", "b", "c"}:
        raise ValueError("buckling curve type must be a, b, or c")

    lambda_bar_fire = _axial.relative_slenderness(
        geometric_slenderness=float(lambda_geom),
        design_yield_resistance_n_mm2=float(ryn_n_mm2),
        elastic_modulus_n_mm2=float(elastic_modulus_n_mm2),
    )
    phi_fire = _axial.central_compression_stability_coefficient(
        relative_slenderness_value=lambda_bar_fire,
        section_type=curve_norm,
    )
    return float(lambda_bar_fire), float(phi_fire)


def _qualified_axis(route: Mapping[str, Any], axis: str) -> dict[str, Any]:
    """Read one qualified SP16 stability axis without rebuilding geometry."""
    if axis not in {"z", "y"}:
        raise ValueError("axis must be z or y")
    lambda_geom = _runtime._number(route, f"sp16_lambda_{axis}_geom", nonnegative=True)
    l_eff = _runtime._number(route, f"sp16_l_eff_{axis}", positive=True)
    radius = _runtime._number(route, f"sp16_i_{axis}", positive=True)
    curve = _runtime._string(route, f"sp16_curve_{axis}").lower()
    if curve not in {"a", "b", "c"}:
        raise ValueError(f"sp16_curve_{axis} must be a, b, or c")

    # The three qualified SP16 outputs must describe the same geometry.  This
    # is only a consistency gate; no geometry is reconstructed for engineering
    # use in the fire branch.
    lambda_from_qualified_geometry = l_eff / radius
    tolerance = max(1e-6, 1e-5 * max(abs(lambda_geom), 1.0))
    if abs(lambda_from_qualified_geometry - lambda_geom) > tolerance:
        raise ValueError(
            f"qualified SP16 axis {axis} is inconsistent: "
            f"lambda={lambda_geom}, l_eff/i={lambda_from_qualified_geometry}"
        )
    return {
        "axis": axis,
        "lambda_geom": float(lambda_geom),
        "l_eff_mm": float(l_eff),
        "i_mm": float(radius),
        "curve": curve,
    }


def _fire_axis_state(
    route: Mapping[str, Any],
    *,
    axis: str,
    ryn_n_mm2: float,
    elastic_modulus_n_mm2: float,
    n_n: float,
    area_mm2: float,
) -> dict[str, Any]:
    qualified = _qualified_axis(route, axis)
    lambda_bar_fire, phi_fire = _fire_stability_state_from_geometry(
        lambda_geom=qualified["lambda_geom"],
        ryn_n_mm2=ryn_n_mm2,
        elastic_modulus_n_mm2=elastic_modulus_n_mm2,
        curve=qualified["curve"],
    )

    # J_axis = A*i_axis^2 is an identity based on the already-qualified SP16
    # radius of gyration; it avoids returning to unqualified raw section data.
    j_axis = area_mm2 * qualified["i_mm"] * qualified["i_mm"]
    gamma_e_axis = (
        n_n
        * qualified["l_eff_mm"]
        * qualified["l_eff_mm"]
        / (math.pi * math.pi * elastic_modulus_n_mm2 * j_axis)
    )
    return {
        **qualified,
        "lambda_bar_fire": float(lambda_bar_fire),
        "phi_fire": float(phi_fire),
        "J_from_qualified_A_i2_mm4": float(j_axis),
        "gamma_e": float(gamma_e_axis),
    }


def _central_compression_final(
    case: Mapping[str, Any], route: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    """Final published SP554 9.2 central-compression route.

    Qualified SP16 l_eff, i, geometric lambda and curve type are reused for
    both z and y.  Ambient lambda_bar / phi and raw mu/L/J inputs are ignored.
    """
    n = abs(_runtime._number(route, "N_n", positive=True))
    area = _runtime._number(route, "A_gross_mm2", positive=True)
    # Legacy machine key kept for compatibility.  Normative meaning in SP554
    # is Ryn, not ambient design Ry and not a generic fy design resistance.
    ryn = _runtime._number(case, "fy_norm_n_mm2", positive=True)
    elastic_modulus = _runtime._number(case, "E_norm_n_mm2", positive=True)
    gamma_c = _runtime._number(route, "gamma_c", positive=True)

    axes = {
        axis: _fire_axis_state(
            route,
            axis=axis,
            ryn_n_mm2=ryn,
            elastic_modulus_n_mm2=elastic_modulus,
            n_n=n,
            area_mm2=area,
        )
        for axis in ("z", "y")
    }

    governing_strength_axis = min(axes, key=lambda key: axes[key]["phi_fire"])
    governing_stiffness_axis = max(axes, key=lambda key: axes[key]["gamma_e"])
    phi_fire = axes[governing_strength_axis]["phi_fire"]
    gamma_e = axes[governing_stiffness_axis]["gamma_e"]

    gamma_t = n / (phi_fire * area * ryn * GAMMA_CT * gamma_c)
    details = {
        "phi": float(phi_fire),
        "rule": "SP554_9_2_FIRE_SLENDERNESS_FROM_RYN_OVER_E",
        "Ryn_n_mm2": float(ryn),
        "E_n_mm2": float(elastic_modulus),
        "gamma_ct": GAMMA_CT,
        "gamma_c": float(gamma_c),
        "governing_strength_axis": governing_strength_axis,
        "governing_stiffness_axis": governing_stiffness_axis,
        "axes": axes,
        "legacy_ambient_lambda_bar_ignored": route.get("lambda_bar"),
        "legacy_ambient_phi_sp16_formula8_ignored": route.get("phi_sp16_formula8"),
        "legacy_raw_mu_ignored": route.get("mu_length_sp16"),
        "legacy_raw_member_length_ignored": route.get("member_length_mm"),
        "legacy_raw_J_min_ignored": route.get("J_min_mm4"),
    }
    return [
        _runtime._strength_candidate("9.2", gamma_t, details)
    ], float(gamma_e), {
        "route": "central_compression",
        "phi": float(phi_fire),
        "gamma_ct": GAMMA_CT,
        "governing_strength_axis": governing_strength_axis,
        "governing_stiffness_axis": governing_stiffness_axis,
        "axes": axes,
        "normative_basis": "final_SP554_8.1_9.2_plus_SP16_7.1.3",
    }


def _number_from_values(values: Mapping[str, Any], key: str, *, positive: bool = False) -> float:
    if key not in values:
        raise ValueError(f"SP554 9.2 final runtime requires {key}")
    try:
        value = float(values[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    if positive and value <= 0.0:
        raise ValueError(f"{key} must be > 0")
    return value


def _value_from_aliases(values: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    raise ValueError(f"SP554 9.2 final runtime requires one of: {', '.join(keys)}")


def _axis_from_values(values: Mapping[str, Any], axis: str) -> tuple[float, str]:
    lambda_geom = float(
        _value_from_aliases(
            values,
            f"sp16_lambda_{axis}_geom",
            f"lambda_{axis}_geom_sp16",
        )
    )
    curve = str(
        _value_from_aliases(
            values,
            f"sp16_curve_{axis}",
            f"sp16_buckling_curve_{axis}",
        )
    ).lower()
    if not math.isfinite(lambda_geom) or lambda_geom < 0.0:
        raise ValueError(f"qualified SP16 lambda_{axis} must be finite and >= 0")
    if curve not in {"a", "b", "c"}:
        raise ValueError(f"qualified SP16 curve_{axis} must be a, b, or c")
    return lambda_geom, curve


def _phi_9_2_declarative_final(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Final guided phi producer from qualified SP16 z/y geometry.

    The frozen graph can still carry ambient lambda_bar / phi fields for saved
    session compatibility.  They cannot govern this result.
    """
    ryn = _number_from_values(values, "fy_norm", positive=True)
    elastic_modulus = _number_from_values(values, "E_norm", positive=True)
    states: dict[str, tuple[float, float]] = {}
    for axis in ("z", "y"):
        lambda_geom, curve = _axis_from_values(values, axis)
        states[axis] = _fire_stability_state_from_geometry(
            lambda_geom=lambda_geom,
            ryn_n_mm2=ryn,
            elastic_modulus_n_mm2=elastic_modulus,
            curve=curve,
        )
    governing_axis = min(states, key=lambda key: states[key][1])
    return {"phi_compression_sp554": float(states[governing_axis][1])}


def _install_guided_registry_override() -> None:
    if getattr(_bridge2, "_v091_final_sp554_phi_installed", False):
        return
    original_builder = _bridge2._build_fire_bridge2_registry

    def _build_fire_bridge2_registry_v091(catalog, registry=None):
        reg = original_builder(catalog, registry)
        reg.register("SP554_C_PHI_9_2_RULE", _phi_9_2_declarative_final)
        return reg

    _bridge2._build_fire_bridge2_registry = _build_fire_bridge2_registry_v091
    _bridge2._v091_final_sp554_phi_installed = True
    _bridge2._v091_previous_registry_builder = original_builder


def install() -> None:
    """Install the final-SP554 mechanics remediation idempotently."""
    if getattr(_runtime, "_v091_final_sp554_installed", False):
        _install_guided_registry_override()
        return
    _install_final_b1()
    _runtime._central_compression = _central_compression_final
    _runtime._v091_final_sp554_installed = True
    _runtime._v091_normative_basis = "published final SP 554.1311500.2026"
    _runtime._v091_gamma_ct = GAMMA_CT
    _install_guided_registry_override()


__all__ = ["GAMMA_CT", "install"]
