"""v0.91 normative remediation for final SP 554.1311500.2026.

The fire branch reuses the qualified SP16 member geometry and buckling-curve
classification.  It does not reuse the ambient SP16 relative slenderness or
ambient phi, because SP554 9.2 defines the fire relative slenderness with
Ryn/E.  The fire phi is evaluated by the same SP16 central-compression
producer used by the ambient engine.

For rolled structural steel and steel castings, E is not a user-dependent
material selection in this route: SP 16.13330.2017 Appendix B, Table B.1 fixes
E = 2.06e5 N/mm2.  v0.91 therefore sources this value normatively instead of
requiring an internal/manual E_norm seed from the guided UI.

Published SP554 Appendix B.1 coefficients are owned exclusively by
``fire_sp554_b1_v091_final``; this module contains no duplicate table rows.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import axial_members as _axial
from . import fire_sp554_runtime as _runtime
from . import fire_bridge2_qualified_state as _bridge2
from .fire_sp554_v091_guided_overlay import (
    PHI_NODE_ID,
    STIFFNESS_TRACE_QID,
    STRENGTH_TRACE_QID,
)
from .sp16_mech7_v083_full_route_overlay import (
    GAMMA_E_INTERNAL_QID,
    GAMMA_E_NODE_ID,
    GAMMA_E_REQUIRED_QID,
)


GAMMA_CT = 1.1
SP16_STEEL_E_N_MM2 = 206000.0
SP16_STEEL_E_NORMATIVE_BASIS = "SP16.13330.2017 Appendix B, Table B.1"


def _fire_stability_state_from_geometry(
    *,
    lambda_geom: float,
    ryn_n_mm2: float,
    elastic_modulus_n_mm2: float,
    curve: str,
) -> tuple[float, float]:
    """Return (lambda_bar_fire, phi_fire) for final SP554 9.2."""
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
    """Final published SP554 9.2 central-compression route."""
    n = abs(_runtime._number(route, "N_n", positive=True))
    area = _runtime._number(route, "A_gross_mm2", positive=True)
    ryn = _runtime._number(case, "fy_norm_n_mm2", positive=True)
    elastic_modulus = SP16_STEEL_E_N_MM2
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
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
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
        "legacy_E_norm_n_mm2_ignored": case.get("E_norm_n_mm2"),
    }
    return [
        _runtime._strength_candidate("9.2", gamma_t, details)
    ], float(gamma_e), {
        "route": "central_compression",
        "phi": float(phi_fire),
        "E_n_mm2": float(elastic_modulus),
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
        "gamma_ct": GAMMA_CT,
        "governing_strength_axis": governing_strength_axis,
        "governing_stiffness_axis": governing_stiffness_axis,
        "axes": axes,
        "normative_basis": "final_SP554_8.1_9.2_plus_SP16_7.1.3_and_Appendix_B_Table_B1",
        "legacy_E_norm_n_mm2_ignored": case.get("E_norm_n_mm2"),
    }


def _number_from_values(values: Mapping[str, Any], key: str, *, positive: bool = False) -> float:
    if key not in values:
        raise ValueError(f"SP554 final runtime requires {key}")
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


def _declared_outputs(node: Mapping[str, Any] | None) -> set[str] | None:
    if not isinstance(node, Mapping) or not node.get("produces"):
        return None
    return {
        str(row["quantity_id"])
        for row in node.get("produces") or []
        if isinstance(row, Mapping) and row.get("quantity_id")
    }


def _phi_9_2_declarative_final(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Final guided phi producer from qualified SP16 z/y fire slenderness."""
    ryn = _number_from_values(values, "fy_norm", positive=True)
    elastic_modulus = SP16_STEEL_E_N_MM2
    axes: dict[str, dict[str, Any]] = {}
    for axis in ("z", "y"):
        lambda_geom, curve = _axis_from_values(values, axis)
        lambda_bar, phi = _fire_stability_state_from_geometry(
            lambda_geom=lambda_geom,
            ryn_n_mm2=ryn,
            elastic_modulus_n_mm2=elastic_modulus,
            curve=curve,
        )
        axes[axis] = {
            "axis": axis,
            "lambda_geom": float(lambda_geom),
            "lambda_bar_fire": float(lambda_bar),
            "phi_fire": float(phi),
            "curve": curve,
        }
    governing_axis = min(
        ("z", "y"),
        key=lambda key: (axes[key]["phi_fire"], 0 if key == "z" else 1),
    )
    trace = {
        "schema": "sp554_v091_strength_trace_v1",
        "route": "central_compression",
        "Ryn_n_mm2": float(ryn),
        "E_n_mm2": float(elastic_modulus),
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
        "governing_strength_axis": governing_axis,
        "axes": axes,
        "legacy_E_norm_ignored": values.get("E_norm"),
    }
    declared = _declared_outputs(node)
    result: dict[str, Any] = {"phi_compression_sp554": float(axes[governing_axis]["phi_fire"])}
    if declared is None or STRENGTH_TRACE_QID in declared:
        result[STRENGTH_TRACE_QID] = trace
    return result


def _gamma_e_8_6_declarative_final(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Final guided gamma_E producer from both qualified SP16 principal axes."""
    n = abs(_number_from_values(values, "N_force"))
    area = _number_from_values(values, "A_gross", positive=True)
    elastic_modulus = SP16_STEEL_E_N_MM2
    axes: dict[str, dict[str, Any]] = {}
    for axis in ("z", "y"):
        l_eff = _number_from_values(values, f"sp16_l_eff_{axis}", positive=True)
        radius = _number_from_values(values, f"sp16_i_{axis}", positive=True)
        inertia = area * radius * radius
        gamma_e = n * l_eff * l_eff / (
            math.pi * math.pi * elastic_modulus * inertia
        )
        if not math.isfinite(gamma_e) or gamma_e < 0.0:
            raise ValueError(f"SP554 8.6 gamma_E for axis {axis} is invalid")
        axes[axis] = {
            "axis": axis,
            "l_eff_mm": float(l_eff),
            "i_mm": float(radius),
            "J_from_qualified_A_i2_mm4": float(inertia),
            "gamma_e": float(gamma_e),
        }
    governing_axis = max(
        ("z", "y"),
        key=lambda key: (axes[key]["gamma_e"], 1 if key == "z" else 0),
    )
    governing = float(axes[governing_axis]["gamma_e"])
    trace = {
        "schema": "sp554_v091_stiffness_trace_v1",
        "route": "central_compression",
        "E_n_mm2": float(elastic_modulus),
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
        "governing_stiffness_axis": governing_axis,
        "axes": axes,
        "legacy_E_norm_ignored": values.get("E_norm"),
        "legacy_ambient_governing_axis_ignored": values.get(
            "sp16_v081_governing_stability_axis"
        ),
    }
    declared = _declared_outputs(node)
    result: dict[str, Any] = {}
    for qid in (GAMMA_E_INTERNAL_QID, GAMMA_E_REQUIRED_QID):
        if declared is None or qid in declared:
            result[qid] = governing
    if declared is None or STIFFNESS_TRACE_QID in declared:
        result[STIFFNESS_TRACE_QID] = trace
    return result


def install_guided_registry_remediation(registry: Any) -> Any:
    """Bind final-SP554 guided §9.2/§8.6 producers to an existing registry."""
    registry.register(PHI_NODE_ID, _phi_9_2_declarative_final)
    registry.register(GAMMA_E_NODE_ID, _gamma_e_8_6_declarative_final)
    return registry


def _install_guided_registry_override() -> None:
    if getattr(_bridge2, "_v091_final_sp554_guided_installed", False):
        return
    original_builder = _bridge2._build_fire_bridge2_registry

    def _build_fire_bridge2_registry_v091(catalog, registry=None):
        reg = original_builder(catalog, registry)
        return install_guided_registry_remediation(reg)

    _bridge2._build_fire_bridge2_registry = _build_fire_bridge2_registry_v091
    _bridge2._v091_final_sp554_guided_installed = True
    _bridge2._v091_final_sp554_phi_installed = True  # retained compatibility marker
    _bridge2._v091_previous_registry_builder = original_builder


def install() -> None:
    """Install the final-SP554 mechanics remediation idempotently."""
    if getattr(_runtime, "_v091_final_sp554_installed", False):
        _install_guided_registry_override()
        return
    _runtime._central_compression = _central_compression_final
    _runtime._v091_final_sp554_installed = True
    _runtime._v091_normative_basis = "published final SP 554.1311500.2026"
    _runtime._v091_gamma_ct = GAMMA_CT
    _runtime._v091_steel_E_n_mm2 = SP16_STEEL_E_N_MM2
    _runtime._v091_steel_E_normative_basis = SP16_STEEL_E_NORMATIVE_BASIS
    _install_guided_registry_override()


__all__ = [
    "GAMMA_CT",
    "SP16_STEEL_E_N_MM2",
    "SP16_STEEL_E_NORMATIVE_BASIS",
    "_gamma_e_8_6_declarative_final",
    "_phi_9_2_declarative_final",
    "install",
    "install_guided_registry_remediation",
]
