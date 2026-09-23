"""Route-scoped v0.91 workflow remediation for final SP 554 §9.2.

The frozen FIRE-D2 workflow historically required ``E_norm_n_mm2`` for every
member route.  For final-SP554 central compression this is no longer a user or
case input: the v0.91 §9.2 mechanics use the SP16 normative steel modulus
E = 206000 N/mm².  This overlay changes only the central-compression workflow;
all other FIRE-D2 routes delegate to the previous implementation unchanged.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import fire_sp554_runtime as _runtime
from .fire_sp554_runtime_v091 import SP16_STEEL_E_N_MM2, SP16_STEEL_E_NORMATIVE_BASIS


def _central_compression_workflow_v091(case: Mapping[str, Any]) -> dict[str, Any]:
    route_name = _runtime._string(case, "member_route")
    if route_name != "central_compression":
        raise ValueError("v0.91 §9.2 workflow accepts central_compression only")
    if "route" not in case or not isinstance(case["route"], Mapping):
        raise ValueError("FIRE-D2 case requires route object")
    route: Mapping[str, Any] = case["route"]

    group, qualification_notes = _runtime._effective_steel_group(case)
    _runtime._number(case, "fy_norm_n_mm2", positive=True)

    # _central_compression is already replaced by fire_sp554_runtime_v091.install().
    # It derives both fire slenderness and gamma_E from qualified SP16 geometry
    # with the normative E=206000 N/mm² and does not consume E_norm_n_mm2.
    candidates, gamma_e, trace = _runtime._central_compression(case, route)

    governing_candidate = max(candidates, key=lambda row: float(row["gamma_T_required"]))
    gamma_t = float(governing_candidate["gamma_T_required"])
    critical = _runtime._critical_selection(group, gamma_t, gamma_e)
    critical_temperature = critical["critical_temperature_c"]

    result: dict[str, Any] = {
        "status": critical["status"],
        "member_route": route_name,
        "requested_steel_strength_group": case["steel_strength_group"],
        "effective_steel_strength_group": group,
        "qualification_notes": qualification_notes,
        "gamma_T_candidates": candidates,
        "gamma_T_required": gamma_t,
        "gamma_T_governing_formula_ref": governing_candidate["formula_ref"],
        "gamma_E_required": gamma_e,
        "critical_temperature_c": critical_temperature,
        "critical_temperature_controlling_kind": critical["controlling_kind"],
        "strength_curve_inversion": critical["strength_inversion"],
        "modulus_curve_inversion": critical["modulus_inversion"],
        "route_trace": trace,
        "governing_policy": "MIN_CRITICAL_TEMPERATURE_AFTER_INDEPENDENT_CURVE_INVERSION",
        "draft_literal_min_coefficient_policy_executed": False,
        "E_normative_n_mm2": SP16_STEEL_E_N_MM2,
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
        "legacy_E_norm_n_mm2_ignored": case.get("E_norm_n_mm2"),
    }
    if "critical_temperature_lower_bound_c" in critical:
        result["critical_temperature_lower_bound_c"] = critical["critical_temperature_lower_bound_c"]

    if critical_temperature is not None and critical_temperature >= 20.0:
        gamma_t_at = _runtime._forward_b1(group, "gamma_T", float(critical_temperature))
        gamma_e_at = _runtime._forward_b1(group, "gamma_E", float(critical_temperature))
        fy = _runtime._number(case, "fy_norm_n_mm2", positive=True)
        result.update(
            {
                "gamma_T_table_at_critical_temperature": gamma_t_at,
                "gamma_E_table_at_critical_temperature": gamma_e_at,
                "R_yt_critical_n_mm2": fy * gamma_t_at,
                "E_t_critical_n_mm2": SP16_STEEL_E_N_MM2 * gamma_e_at,
            }
        )
    return result


def sp554_fire_mechanical_guided_workflow_v091(case: Mapping[str, Any]) -> dict[str, Any]:
    """Use final-SP554 §9.2 semantics only for central compression."""
    route_name = _runtime._string(case, "member_route")
    if route_name == "central_compression":
        return _central_compression_workflow_v091(case)
    previous = getattr(_runtime, "_v091_previous_sp554_fire_mechanical_guided_workflow")
    return previous(case)


def install() -> None:
    """Install the route-scoped workflow overlay idempotently."""
    if getattr(_runtime, "_v091_sp554_workflow_installed", False):
        return
    _runtime._v091_previous_sp554_fire_mechanical_guided_workflow = (
        _runtime.sp554_fire_mechanical_guided_workflow
    )
    _runtime.sp554_fire_mechanical_guided_workflow = sp554_fire_mechanical_guided_workflow_v091
    _runtime._v091_sp554_workflow_installed = True


__all__ = ["install", "sp554_fire_mechanical_guided_workflow_v091"]
