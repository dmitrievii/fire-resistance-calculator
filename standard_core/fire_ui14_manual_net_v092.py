"""v0.92 manual net-section property remediation.

This overlay restores the explicit ``manual_net_properties`` branch without
changing the frozen DAG.  The branch remains inside the already-declared
``section_weakening_model`` object.

Contract
--------
* ``A_net`` is NEVER user supplied.  It is always evaluated by the qualified
  UI1.4 weakening geometry as ``A - d*t_w``.
* User net inertias/moduli are entered in active canonical axes z/y and mapped
  to the retained internal x/y quantities only when ``major_axis_is_x`` is
  explicitly available from section geometry.
* Required manual values are ``I_z,n``, ``I_y,n``, ``W_z,n`` and ``W_y,n``.
* Plastic and sectorial/warping net properties are optional because not every
  active SP16 route consumes them.
* No missing manual value falls back to the automatically reduced value.
* Typed provenance is embedded in ``net_section_geometry_2d.calculation_trace``
  so REPORT-IR and downstream binders can prove which values came from the
  user and which value (A_net) remained geometry-derived.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Callable, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui14_section_weakening import (
    WEAKENING_TRACE_SCHEMA,
    _finite_positive,
    _geometry_dimensions,
    _gross_required,
)

MANUAL_MODE = "manual_net_properties"
MANUAL_SOURCE_KIND = "USER_INPUT_NET_PROPERTY"
MANUAL_SOURCE_TEXT_RU = "введено пользователем как характеристики нетто"
MANUAL_TRACE_SCHEMA = "fire_ui14_manual_net_properties_v092"

_REQUIRED_CANONICAL = {
    "I_z_n_mm4": ("I_xn", "I_yn", "mm4"),
    "I_y_n_mm4": ("I_yn", "I_xn", "mm4"),
    "W_z_n_mm3": ("W_xn_min", "W_yn_min", "mm3"),
    "W_y_n_mm3": ("W_yn_min", "W_xn_min", "mm3"),
}
_OPTIONAL_CANONICAL = {
    "W_pl_z_eff_mm3": ("W_pl_x_eff", "W_pl_y_eff", "mm3"),
    "W_pl_y_eff_mm3": ("W_pl_y_eff", "W_pl_x_eff", "mm3"),
    "I_omega_n_mm6": ("I_omega_n", "I_omega_n", "mm6"),
    "W_omega_eff_mm4": ("W_omega_eff", "W_omega_eff", "mm4"),
}
_FORBIDDEN_AREA_KEYS = {"A_net", "A_n", "A_net_mm2", "area_net_mm2"}


def _manual_raw(values: Mapping[str, Any]) -> Mapping[str, Any] | None:
    model = values.get("section_weakening_model")
    if not isinstance(model, Mapping) or model.get("holes_present") is not True:
        return None
    if model.get("net_property_mode") != MANUAL_MODE:
        return None
    bundle = model.get("manual_net_properties")
    if not isinstance(bundle, Mapping):
        raise FireUIError("manual_net_properties mode requires manual_net_properties object")
    return bundle


def _manual_bundle(values: Mapping[str, Any]) -> tuple[dict[str, float], bool]:
    raw = _manual_raw(values)
    if raw is None:
        raise FireUIError("manual net bundle requested outside manual_net_properties mode")
    forbidden = sorted(_FORBIDDEN_AREA_KEYS.intersection(str(key) for key in raw))
    if forbidden:
        raise FireUIError(
            "A_net is geometry-derived and cannot be supplied in manual_net_properties: "
            + ", ".join(forbidden)
        )

    major_axis_is_x = values.get("major_axis_is_x")
    if not isinstance(major_axis_is_x, bool):
        raise FireUIError(
            "manual net properties require explicit major_axis_is_x evidence before canonical z/y values can be mapped"
        )

    result: dict[str, float] = {}
    for key in _REQUIRED_CANONICAL:
        if key not in raw:
            raise FireUIError(f"manual_net_properties requires {key}; no automatic fallback is allowed")
        result[key] = _finite_positive(raw[key], f"manual_net_properties.{key}")

    for key in _OPTIONAL_CANONICAL:
        if key in raw and raw[key] is not None:
            result[key] = _finite_positive(raw[key], f"manual_net_properties.{key}")

    plastic_present = {key for key in ("W_pl_z_eff_mm3", "W_pl_y_eff_mm3") if key in result}
    if plastic_present and len(plastic_present) != 2:
        raise FireUIError(
            "manual plastic net properties must provide both W_pl_z_eff_mm3 and W_pl_y_eff_mm3"
        )
    return result, major_axis_is_x


def _map_canonical_to_runtime(bundle: Mapping[str, float], major_axis_is_x: bool) -> tuple[dict[str, float], list[dict[str, Any]]]:
    runtime: dict[str, float] = {}
    evidence: list[dict[str, Any]] = []
    all_specs = {**_REQUIRED_CANONICAL, **_OPTIONAL_CANONICAL}
    for canonical_key, value in bundle.items():
        first, second, unit = all_specs[canonical_key]
        runtime_key = first if major_axis_is_x else second
        # Sectorial/warping values are axis-independent in this transport
        # contract; first == second for those keys.
        runtime[runtime_key] = float(value)
        symbol = {
            "I_z_n_mm4": "I_{z,n}",
            "I_y_n_mm4": "I_{y,n}",
            "W_z_n_mm3": "W_{z,n}",
            "W_y_n_mm3": "W_{y,n}",
            "W_pl_z_eff_mm3": "W_{pl,z,eff}",
            "W_pl_y_eff_mm3": "W_{pl,y,eff}",
            "I_omega_n_mm6": "I_{\\omega,n}",
            "W_omega_eff_mm4": "W_{\\omega,eff}",
        }[canonical_key]
        evidence.append(
            {
                "canonical_input_id": canonical_key,
                "canonical_symbol": symbol,
                "runtime_quantity_id": runtime_key,
                "value": float(value),
                "unit": unit,
                "source_kind": MANUAL_SOURCE_KIND,
                "source_text_ru": MANUAL_SOURCE_TEXT_RU,
            }
        )
    if "W_pl_x_eff" in runtime and "W_pl_y_eff" in runtime:
        runtime["W_pl_min_eff"] = min(runtime["W_pl_x_eff"], runtime["W_pl_y_eff"])
        evidence.append(
            {
                "canonical_input_id": "derived_min_from_manual_plastic_pair",
                "canonical_symbol": "W_{pl,min,eff}",
                "runtime_quantity_id": "W_pl_min_eff",
                "value": runtime["W_pl_min_eff"],
                "unit": "mm3",
                "source_kind": "DERIVED_FROM_USER_INPUT_NET_PROPERTIES",
                "source_text_ru": "минимум из введённых пользователем пластических характеристик нетто",
            }
        )
    return runtime, evidence


def _manual_net_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    model = values.get("section_weakening_model")
    if not isinstance(model, Mapping):
        raise FireUIError("section_weakening_model must be an object")
    d = _finite_positive(model.get("hole_diameter_mm"), "hole_diameter_mm")
    s = _finite_positive(model.get("hole_pitch_mm"), "hole_pitch_mm")
    if s <= d:
        raise FireUIError("SP16 8.2.1 formula (45) requires hole pitch s > hole diameter d")

    area = _gross_required(values, "A_gross")
    tw, h, tf = _geometry_dimensions(values)
    if h is not None and tf is not None:
        clear_web = h - 2.0 * tf
        if clear_web <= 0.0 or d >= clear_web:
            raise FireUIError("hole diameter d must fit entirely inside the clear web depth")

    manual, major_axis_is_x = _manual_bundle(values)
    runtime, manual_evidence = _map_canonical_to_runtime(manual, major_axis_is_x)

    removed_area = d * tw
    a_net = area - removed_area
    if a_net <= 0.0:
        raise FireUIError("bolt hole produces non-positive net area")

    # The required manual I/W pair must itself remain physically meaningful.
    for key in ("I_xn", "I_yn", "W_xn_min", "W_yn_min"):
        if key not in runtime or not math.isfinite(runtime[key]) or runtime[key] <= 0.0:
            raise FireUIError(f"manual net runtime mapping did not produce positive {key}")

    trace = {
        "schema": WEAKENING_TRACE_SCHEMA,
        "manual_schema": MANUAL_TRACE_SCHEMA,
        "route": "manual_net_properties_with_geometry_area",
        "engineering_basis": (
            "A_net is calculated from the accepted central web-hole geometry; I_n/W_n and optional effective plastic/warping "
            "properties are user-supplied net characteristics and are not recalculated by the application"
        ),
        "major_axis_is_x": major_axis_is_x,
        "inputs": {"A_gross": area, "d": d, "s": s, "t_w": tw},
        "steps": [
            {
                "formula_id": "REMOVED_AREA_CENTRAL_WEB_HOLE",
                "formula_latex": r"\Delta A=d\,t_w",
                "inputs": {"d": d, "t_w": tw},
                "result": {"quantity_id": "sp16_net_removed_area", "value": removed_area, "unit": "mm2"},
            },
            {
                "formula_id": "A_NET_CENTRAL_WEB_HOLE",
                "formula_latex": r"A_n=A-\Delta A",
                "inputs": {"A": area, "Delta_A": removed_area},
                "result": {"quantity_id": "A_net", "value": a_net, "unit": "mm2"},
            },
        ],
        "manual_properties": manual_evidence,
        "area_source_kind": "CALCULATED_FROM_WEAKENING_GEOMETRY",
        "manual_area_override_allowed": False,
        "automatic_fallback_for_missing_manual_property": False,
        "sp16_formula45": {
            "applicable": True,
            "formula_id": "SP16_EQ_45_SHEAR_HOLE_FACTOR",
            "normative_scope": "SP16 8.2.1 Eq.(45)",
            "formula_latex": r"\alpha_h=\frac{s}{s-d}",
            "inputs": {"s": s, "d": d},
            "result_quantity_id": "sp16_shear_hole_alpha45",
        },
        "presentation_recomputes_values": False,
    }

    result: dict[str, Any] = {
        "sp16_weakening_model_valid": True,
        "sp16_net_geometry_solver_ok": True,
        "net_section_geometry_2d": {
            "schema": "fire_ui14_net_section_v1",
            "mode": MANUAL_MODE,
            "hole_diameter_mm": d,
            "web_thickness_mm": tw,
            "hole_center_x_mm": 0.0,
            "hole_center_y_mm": 0.0,
            "removed_cross_section_shape": "rectangle_d_by_tw",
            "calculation_trace": trace,
            "limitations": [
                "A_net uses one representative active transverse-section hole",
                "manual I/W properties are accepted as user-supplied net characteristics",
                "flange holes/cut-outs/multiple active holes are not generated by this authoring model",
            ],
        },
        "A_net": a_net,
        "sp16_net_removed_area": removed_area,
        "sp16_shear_weakening_mode": "formula45",
        "sp16_wall_hole_pitch_s": s,
        "sp16_wall_hole_diameter_d": d,
        **runtime,
    }
    return result


def _manual_consumption(values: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any] | None:
    raw = _manual_raw(values)
    if raw is None:
        return None
    selected = {
        key: float(values[key])
        for key in keys
        if key in values
        and isinstance(values[key], (int, float))
        and not isinstance(values[key], bool)
        and math.isfinite(float(values[key]))
    }
    return {
        "schema": "sp16_v092_manual_net_consumer_evidence_v1",
        "source_kind": MANUAL_SOURCE_KIND,
        "source_text_ru": MANUAL_SOURCE_TEXT_RU,
        "consumed_runtime_quantities": selected,
        "A_net_source": "CALCULATED_FROM_WEAKENING_GEOMETRY" if "A_net" in keys else None,
    }


def _wrap_evidence_executor(
    original: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
    *,
    output_qid: str,
    evidence_key: str,
    property_selector: Callable[[Mapping[str, Any]], tuple[str, ...]],
    marker: str,
):
    if getattr(original, marker, False):
        return original

    def wrapped(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        result = dict(original(values, node))
        consumption = _manual_consumption(values, property_selector(values))
        bundle = result.get(output_qid)
        if consumption is not None and isinstance(bundle, Mapping):
            patched = copy.deepcopy(dict(bundle))
            evidence = patched.get("evidence")
            if isinstance(evidence, Mapping) and evidence_key in evidence and isinstance(evidence[evidence_key], Mapping):
                rows = dict(evidence)
                row = copy.deepcopy(dict(rows[evidence_key]))
                details = row.get("details")
                details = dict(details) if isinstance(details, Mapping) else {}
                details["manual_net_property_consumption"] = consumption
                row["details"] = details
                rows[evidence_key] = row
                patched["evidence"] = rows
            else:
                patched["manual_net_property_consumption"] = consumption
            result[output_qid] = patched
        return result

    setattr(wrapped, marker, True)
    setattr(wrapped, f"{marker}_original", original)
    return wrapped


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Install manual-net execution and downstream consumption evidence once."""
    net_node = "SP554_G_NET_SECTION_PROPERTIES"
    original_net = registry.executors.get(net_node)
    if original_net is None:
        raise FireUIError(f"v0.92 manual-net remediation requires registered {net_node}")
    if not getattr(original_net, "_fire_ui14_manual_net_v092", False):
        def net_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
            if _manual_raw(values) is not None:
                return _manual_net_executor(values, node)
            return original_net(values, node)
        setattr(net_executor, "_fire_ui14_manual_net_v092", True)
        setattr(net_executor, "_fire_ui14_manual_net_v092_original", original_net)
        registry.executors[net_node] = net_executor

    mech7 = registry.executors.get("SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER")
    if mech7 is not None:
        def mech7_keys(values: Mapping[str, Any]) -> tuple[str, ...]:
            return ("A_net", "I_xn", "I_yn", "I_omega_n")
        registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"] = _wrap_evidence_executor(
            mech7,
            output_qid="sp16_mech7_primary_evidence",
            evidence_key="interaction_N_M",
            property_selector=mech7_keys,
            marker="_fire_ui14_manual_net_mech7_v092",
        )

    mech8 = registry.executors.get("SP16_C_MECH8_INTERACTION_BINDER")
    if mech8 is not None:
        def mech8_keys(values: Mapping[str, Any]) -> tuple[str, ...]:
            section_class = str(values.get("sp16_section_class") or "")
            if section_class == "1":
                return ("I_xn", "I_yn")
            if section_class == "2":
                return ("W_xn_min", "W_yn_min")
            return ()
        registry.executors["SP16_C_MECH8_INTERACTION_BINDER"] = _wrap_evidence_executor(
            mech8,
            output_qid="sp16_mech8_primary_evidence",
            evidence_key="interaction_M_Q",
            property_selector=mech8_keys,
            marker="_fire_ui14_manual_net_mech8_v092",
        )

    mech9 = registry.executors.get("SP16_C_MECH9_REMAINING_AMBIENT_BINDER")
    if mech9 is not None:
        registry.executors["SP16_C_MECH9_REMAINING_AMBIENT_BINDER"] = _wrap_evidence_executor(
            mech9,
            output_qid="sp16_mech9_primary_evidence",
            evidence_key="interaction_M_Q",
            property_selector=lambda values: ("W_xn_min",),
            marker="_fire_ui14_manual_net_mech9_v092",
        )

    return registry


__all__ = [
    "MANUAL_MODE",
    "MANUAL_SOURCE_KIND",
    "MANUAL_SOURCE_TEXT_RU",
    "MANUAL_TRACE_SCHEMA",
    "_manual_bundle",
    "_manual_net_executor",
    "install_registry_remediation",
]
