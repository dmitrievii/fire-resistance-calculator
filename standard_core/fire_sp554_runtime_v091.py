"""v0.91 normative remediation for final SP 554.1311500.2026.

This overlay deliberately separates the ambient SP16 stability state from the
fire SP554 state.  SP16 ambient relative slenderness uses design resistance
Ry, while SP554 9.2 defines the fire relative slenderness with Ryn/E and then
requires phi to be evaluated by the SP16 central-compression rules.

The module is installed from standard_core.__init__ so both the standalone
FIRE-D2 workflow and the guided declarative registry use the same final-SP554
mechanics.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import axial_members as _axial
from . import fire_sp554_runtime as _runtime
from . import fire_bridge2_qualified_state as _bridge2


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
        slenderness=float(lambda_geom),
        yield_strength=float(ryn_n_mm2),
        elastic_modulus=float(elastic_modulus_n_mm2),
    )
    phi_fire = _axial.central_compression_stability_coefficient(
        relative_slenderness_value=lambda_bar_fire,
        section_type=curve_norm,
    )
    return float(lambda_bar_fire), float(phi_fire)


def _central_compression_final(
    case: Mapping[str, Any], route: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    """Final published SP554 9.2 central-compression route.

    Legacy route fields ``lambda_bar`` and ``phi_sp16_formula8`` are accepted
    for saved-case compatibility but are not engineering inputs here.
    """
    n = abs(_runtime._number(route, "N_n", positive=True))
    area = _runtime._number(route, "A_gross_mm2", positive=True)
    ryn = _runtime._number(case, "fy_norm_n_mm2", positive=True)
    elastic_modulus = _runtime._number(case, "E_norm_n_mm2", positive=True)
    gamma_c = _runtime._number(route, "gamma_c", positive=True)
    mu = _runtime._number(route, "mu_length_sp16", positive=True)
    member_length = _runtime._number(route, "member_length_mm", positive=True)
    j_min = _runtime._number(route, "J_min_mm4", positive=True)
    curve = _runtime._string(route, "buckling_curve_type").lower()

    l_eff = mu * member_length
    i_min = math.sqrt(j_min / area)
    lambda_geom = l_eff / i_min
    lambda_bar_fire, phi_fire = _fire_stability_state_from_geometry(
        lambda_geom=lambda_geom,
        ryn_n_mm2=ryn,
        elastic_modulus_n_mm2=elastic_modulus,
        curve=curve,
    )

    gamma_t = n / (phi_fire * area * ryn * gamma_c)
    gamma_e = n * l_eff * l_eff / (math.pi * math.pi * elastic_modulus * j_min)
    threshold = {"a": 3.8, "b": 4.4, "c": 5.8}[curve]
    details = {
        "phi": phi_fire,
        "rule": "SP554_9_2_FIRE_SLENDERNESS_FROM_RYN_OVER_E",
        "lambda_geom": lambda_geom,
        "lambda_bar_fire": lambda_bar_fire,
        "buckling_curve_type": curve,
        "Ryn_n_mm2": ryn,
        "E_n_mm2": elastic_modulus,
        "i_min_mm": i_min,
        "l_eff_mm": l_eff,
        "low_slenderness_phi_equals_1_applicable": bool(lambda_bar_fire < 0.6 and curve in {"a", "b"}),
        "high_slenderness_cap_applicable": bool(lambda_bar_fire > threshold),
        "legacy_ambient_lambda_bar_ignored": route.get("lambda_bar"),
        "legacy_ambient_phi_sp16_formula8_ignored": route.get("phi_sp16_formula8"),
    }
    return [
        _runtime._strength_candidate("9.2", gamma_t, details)
    ], gamma_e, {
        "route": "central_compression",
        "phi": phi_fire,
        "lambda_geom": lambda_geom,
        "lambda_bar_fire": lambda_bar_fire,
        "l_eff_mm": l_eff,
        "normative_basis": "final_SP554_9.2_plus_SP16_7.1.3",
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


def _phi_9_2_declarative_final(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Replacement executor for the guided SP554_C_PHI_9_2_RULE node.

    The frozen graph still carries legacy ambient phi/lambda quantities for
    backward-compatible saved sessions.  The final value is recomputed from
    geometric lambda, Ryn and E and therefore cannot inherit ambient Ry-based
    stability coefficients.
    """
    lambda_geom = _number_from_values(values, "sp16_lambda_geom")
    ryn = _number_from_values(values, "fy_norm", positive=True)
    elastic_modulus = _number_from_values(values, "E_norm", positive=True)
    if "sp16_buckling_curve_type" not in values:
        raise ValueError("SP554 9.2 final runtime requires sp16_buckling_curve_type")
    curve = str(values["sp16_buckling_curve_type"]).lower()
    _, phi_fire = _fire_stability_state_from_geometry(
        lambda_geom=lambda_geom,
        ryn_n_mm2=ryn,
        elastic_modulus_n_mm2=elastic_modulus,
        curve=curve,
    )
    return {"phi_compression_sp554": phi_fire}


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
    _install_guided_registry_override()


__all__ = ["install"]
