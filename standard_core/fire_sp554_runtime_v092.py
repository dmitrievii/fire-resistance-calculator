"""v0.92 P0 remediation for final SP 554.1311500.2026 §§9-11.

This overlay closes the residual final-publication gap left by v0.91:

* §9.1 central tension is migrated to the mandatory special-limit-state
  coefficient gamma_ct = 1.1 from SP554 §8.1;
* §9.2 central compression remains owned by the v0.91 final runtime, including
  the separate fire slenderness/phi state built from qualified SP16 z/y
  geometry, Ryn and E = 206000 N/mm²;
* legacy Section 10 bending and Section 11 N+M routes are fail-closed until the
  canonical action migration is complete.  The historical Mx/Ix bending
  vocabulary is never reinterpreted as canonical strong-axis Mz.

The canonical active action contract is:
    Mz -> strong-axis bending,
    My -> weak-axis bending,
    Mx -> torsion only.

This module intentionally does not attempt a mechanical old-Mx -> new-Mz
translation.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from . import fire_sp554_runtime as _runtime
from .fire_sp554_runtime_v091 import (
    GAMMA_CT,
    SP16_STEEL_E_N_MM2,
    SP16_STEEL_E_NORMATIVE_BASIS,
    _number_from_values,
)


GAMMA_CT_NORMATIVE_BASIS = "SP 554.1311500.2026 §8.1"
TENSION_NODE_ID = "SP554_C_9_1"
TENSION_TRACE_QID = "sp554_9_1_central_tension_trace"
TENSION_TRACE_SCHEMA = "sp554_v092_central_tension_trace_v1"
TENSION_FORMULA_ID = "SP554_9_1_GAMMA_T_FINAL"
TENSION_EXPRESSION = "abs(N_force)/(A_net*fy_norm*1.1*gamma_c_tension)"
TENSION_FORMULA_LATEX = r"\gamma_T=\frac{|N|}{A_n R_{yn}\gamma_{ct}\gamma_c}"
CANONICAL_ACTION_CONTRACT = {
    "strong_axis_bending": "M_z",
    "weak_axis_bending": "M_y",
    "torsion": "M_x",
    "legacy_Mx_to_Mz_translation_allowed": False,
}

# Executable-census status for the final-publication §§9-11 routes exposed by
# the retained FIRE-D2 workflow.  A route marked FAIL_CLOSED must not delegate
# into the legacy equation implementation.
SP554_V092_ROUTE_CENSUS: dict[str, dict[str, Any]] = {
    "central_tension": {
        "clause": "9.1",
        "status": "MIGRATED",
        "gamma_ct": GAMMA_CT,
        "axis_contract": "axis_free",
    },
    "central_compression": {
        "clause": "9.2",
        "status": "MIGRATED_V091",
        "gamma_ct": GAMMA_CT,
        "axis_contract": "canonical_z_y_fire_state",
    },
    "bending": {
        "clause": "10",
        "status": "FAIL_CLOSED_PENDING_CANONICAL_ACTION_MIGRATION",
        "gamma_ct": GAMMA_CT,
        "axis_contract": "Mz_strong_My_weak_Mx_torsion",
    },
    "combined_nm": {
        "clause": "11",
        "status": "FAIL_CLOSED_PENDING_CANONICAL_ACTION_MIGRATION",
        "gamma_ct": GAMMA_CT,
        "axis_contract": "Mz_strong_My_weak_Mx_torsion",
    },
}


def _central_tension_trace(
    *,
    n_force_n: float,
    area_net_mm2: float,
    ryn_n_mm2: float,
    gamma_c: float,
    gamma_t: float,
) -> dict[str, Any]:
    """Build one typed §9.1 evidence object shared by standalone and guided routes."""
    n_abs = abs(float(n_force_n))
    area = float(area_net_mm2)
    ryn = float(ryn_n_mm2)
    gamma_c_value = float(gamma_c)
    gamma_t_value = float(gamma_t)
    return {
        "schema": TENSION_TRACE_SCHEMA,
        "route": "central_tension",
        "standard": "SP 554.1311500.2026",
        "clause": "9.1",
        "formula_id": TENSION_FORMULA_ID,
        "formula_latex": TENSION_FORMULA_LATEX,
        "expression": TENSION_EXPRESSION,
        "inputs": {
            "N_force": {"value": float(n_force_n), "absolute_value": n_abs, "unit": "N"},
            "A_net": {"value": area, "unit": "mm2"},
            "fy_norm": {"value": ryn, "unit": "N/mm2"},
            "gamma_ct": {
                "value": GAMMA_CT,
                "unit": "1",
                "source": "mandatory_normative_constant",
                "normative_basis": GAMMA_CT_NORMATIVE_BASIS,
            },
            "gamma_c_tension": {"value": gamma_c_value, "unit": "1"},
        },
        "substitution_latex": (
            rf"\gamma_T=\frac{{|{float(n_force_n):.12g}|}}"
            rf"{{{area:.12g}\cdot {ryn:.12g}\cdot {GAMMA_CT:.12g}\cdot {gamma_c_value:.12g}}}"
        ),
        "result": {
            "quantity_id": "gamma_T_9_1",
            "value": gamma_t_value,
            "unit": "1",
        },
        "normative_basis": "final_SP554_8.1_and_9.1",
        "report_contract": "formula_equals_substitution_equals_result",
    }


def _central_tension_final(
    case: Mapping[str, Any], route: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], float | None, dict[str, Any]]:
    """Final SP554 §9.1 with mandatory gamma_ct=1.1."""
    n_signed = _runtime._number(route, "N_n")
    n = abs(n_signed)
    if n <= 0.0:
        raise ValueError("N_n must be non-zero for SP554 §9.1 central tension")
    area = _runtime._number(route, "A_net_mm2", positive=True)
    ryn = _runtime._number(case, "fy_norm_n_mm2", positive=True)
    gamma_c = _runtime._number(route, "gamma_c", positive=True)
    gamma_t = n / (area * ryn * GAMMA_CT * gamma_c)
    calculation_trace = _central_tension_trace(
        n_force_n=n_signed,
        area_net_mm2=area,
        ryn_n_mm2=ryn,
        gamma_c=gamma_c,
        gamma_t=gamma_t,
    )
    details = {
        "rule": "FINAL_SP554_9_1_WITH_MANDATORY_GAMMA_CT",
        "Ryn_n_mm2": float(ryn),
        "gamma_ct": GAMMA_CT,
        "gamma_ct_normative_basis": GAMMA_CT_NORMATIVE_BASIS,
        "gamma_c": float(gamma_c),
        "calculation_trace": copy.deepcopy(calculation_trace),
        "legacy_user_gamma_ct_ignored": route.get("gamma_ct"),
    }
    trace = copy.deepcopy(calculation_trace)
    trace.update(
        {
            "Ryn_n_mm2": float(ryn),
            "gamma_ct": GAMMA_CT,
            "gamma_ct_normative_basis": GAMMA_CT_NORMATIVE_BASIS,
            "gamma_c": float(gamma_c),
            "legacy_user_gamma_ct_ignored": route.get("gamma_ct"),
        }
    )
    return [
        _runtime._strength_candidate("9.1", gamma_t, details)
    ], None, trace


def _central_tension_guided_final(
    values: Mapping[str, Any], node: Mapping[str, Any] | None = None
) -> Mapping[str, Any]:
    """Final guided §9.1 producer using the same mandatory-γct equation as standalone."""
    n_signed = _number_from_values(values, "N_force")
    n = abs(n_signed)
    if n <= 0.0:
        raise ValueError("N_force must be non-zero for SP554 §9.1 central tension")
    area = _number_from_values(values, "A_net", positive=True)
    ryn = _number_from_values(values, "fy_norm", positive=True)
    gamma_c = _number_from_values(values, "gamma_c_tension", positive=True)
    gamma_t = n / (area * ryn * GAMMA_CT * gamma_c)
    trace = _central_tension_trace(
        n_force_n=n_signed,
        area_net_mm2=area,
        ryn_n_mm2=ryn,
        gamma_c=gamma_c,
        gamma_t=gamma_t,
    )

    declared: set[str] | None = None
    if isinstance(node, Mapping) and node.get("produces"):
        declared = {
            str(row["quantity_id"])
            for row in node.get("produces") or []
            if isinstance(row, Mapping) and row.get("quantity_id")
        }
    result: dict[str, Any] = {}
    if declared is None or "gamma_T_9_1" in declared:
        result["gamma_T_9_1"] = float(gamma_t)
    if declared is None or TENSION_TRACE_QID in declared:
        result[TENSION_TRACE_QID] = trace
    return result


def install_guided_registry_remediation_v092(registry: Any) -> Any:
    """Bind final-SP554 guided §9.1 to the same v0.92 producer used by standalone."""
    registry.register(TENSION_NODE_ID, _central_tension_guided_final)
    return registry


def _finalize_central_tension(case: Mapping[str, Any]) -> dict[str, Any]:
    route_name = _runtime._string(case, "member_route")
    if route_name != "central_tension":
        raise ValueError("v0.92 §9.1 workflow accepts central_tension only")
    if "route" not in case or not isinstance(case["route"], Mapping):
        raise ValueError("SP554 final case requires route object")
    route: Mapping[str, Any] = case["route"]

    group, qualification_notes = _runtime._effective_steel_group(case)
    _runtime._number(case, "fy_norm_n_mm2", positive=True)
    candidates, gamma_e, trace = _central_tension_final(case, route)

    governing_candidate = max(
        candidates, key=lambda row: float(row["gamma_T_required"])
    )
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
        "gamma_E_required": None,
        "critical_temperature_c": critical_temperature,
        "critical_temperature_controlling_kind": critical["controlling_kind"],
        "strength_curve_inversion": critical["strength_inversion"],
        "modulus_curve_inversion": critical["modulus_inversion"],
        "route_trace": trace,
        "gamma_ct": GAMMA_CT,
        "gamma_ct_normative_basis": GAMMA_CT_NORMATIVE_BASIS,
        "route_census": SP554_V092_ROUTE_CENSUS["central_tension"],
        "governing_policy": "MIN_CRITICAL_TEMPERATURE_AFTER_INDEPENDENT_CURVE_INVERSION",
        "draft_literal_min_coefficient_policy_executed": False,
        "E_normative_n_mm2": SP16_STEEL_E_N_MM2,
        "E_normative_basis": SP16_STEEL_E_NORMATIVE_BASIS,
        "legacy_E_norm_n_mm2_ignored": case.get("E_norm_n_mm2"),
    }
    if "critical_temperature_lower_bound_c" in critical:
        result["critical_temperature_lower_bound_c"] = critical[
            "critical_temperature_lower_bound_c"
        ]

    if critical_temperature is not None and critical_temperature >= 20.0:
        gamma_t_at = _runtime._forward_b1(
            group, "gamma_T", float(critical_temperature)
        )
        gamma_e_at = _runtime._forward_b1(
            group, "gamma_E", float(critical_temperature)
        )
        ryn = _runtime._number(case, "fy_norm_n_mm2", positive=True)
        result.update(
            {
                "gamma_T_table_at_critical_temperature": gamma_t_at,
                "gamma_E_table_at_critical_temperature": gamma_e_at,
                "R_yt_critical_n_mm2": ryn * gamma_t_at,
                "E_t_critical_n_mm2": SP16_STEEL_E_N_MM2 * gamma_e_at,
            }
        )
    return result


def _canonical_action_fail_closed(route_name: str) -> None:
    census = SP554_V092_ROUTE_CENSUS[route_name]
    raise ValueError(
        "SP554 v0.92 fail-closed: final-publication Section "
        f"{census['clause']} route {route_name!r} is not executable through the "
        "legacy Mx/Ix bending contract. Complete the canonical action migration "
        "first: M_z = strong-axis bending, M_y = weak-axis bending, "
        "M_x = torsion only. Mechanical old Mx -> new Mz translation is forbidden."
    )


def sp554_fire_mechanical_guided_workflow_v092(
    case: Mapping[str, Any]
) -> dict[str, Any]:
    """Final-publication route gate for SP554 §§9-11."""
    route_name = _runtime._string(case, "member_route")
    if route_name == "central_tension":
        return _finalize_central_tension(case)
    if route_name == "central_compression":
        # Delegate to the v0.91 final §9.2 route.  That route owns the separate
        # fire lambda-bar/phi state and the z/y governing-axis evidence.
        return _runtime._v092_previous_sp554_fire_mechanical_guided_workflow(case)
    if route_name in {"bending", "combined_nm"}:
        _canonical_action_fail_closed(route_name)
    # §8.7 is outside the §§9-11 P0 census and remains delegated unchanged.
    return _runtime._v092_previous_sp554_fire_mechanical_guided_workflow(case)


def install() -> None:
    """Install the v0.92 P0 route census and §9.1 remediation idempotently."""
    if getattr(_runtime, "_v092_sp554_p0_installed", False):
        return
    _runtime._central_tension = _central_tension_final
    _runtime._v092_previous_sp554_fire_mechanical_guided_workflow = (
        _runtime.sp554_fire_mechanical_guided_workflow
    )
    _runtime.sp554_fire_mechanical_guided_workflow = (
        sp554_fire_mechanical_guided_workflow_v092
    )
    _runtime._v092_sp554_route_census = SP554_V092_ROUTE_CENSUS
    _runtime._v092_gamma_ct = GAMMA_CT
    _runtime._v092_gamma_ct_normative_basis = GAMMA_CT_NORMATIVE_BASIS
    _runtime._v092_canonical_action_contract = CANONICAL_ACTION_CONTRACT
    _runtime._v092_sp554_p0_installed = True


__all__ = [
    "CANONICAL_ACTION_CONTRACT",
    "GAMMA_CT_NORMATIVE_BASIS",
    "SP554_V092_ROUTE_CENSUS",
    "TENSION_EXPRESSION",
    "TENSION_FORMULA_ID",
    "TENSION_FORMULA_LATEX",
    "TENSION_NODE_ID",
    "TENSION_TRACE_QID",
    "TENSION_TRACE_SCHEMA",
    "_central_tension_final",
    "_central_tension_guided_final",
    "_central_tension_trace",
    "install",
    "install_guided_registry_remediation_v092",
    "sp554_fire_mechanical_guided_workflow_v092",
]
