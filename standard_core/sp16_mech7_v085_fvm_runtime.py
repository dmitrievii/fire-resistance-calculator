"""v0.85 registry installer for the qualified protected FVM discretization."""
from __future__ import annotations

from .fire_ui0 import ExecutionRegistry
from .fire_sp554_thermal_v085 import install_thermal_solver_patch, mesh_convergence_check
from . import fire_ui23_protection_route as _route
from .fire_sp554_thermal import sp554_fire_thermal_guided_workflow
from .fire_ui0 import FireUIError
from .sp16_mech7_v084_thermal_visual_runtime import install_registry_remediation as _install_v084_registry


def _qualified_refined_result(values, thickness_mm: float):
    case = _route._fdm_case(values, float(thickness_mm))
    try:
        coarse = sp554_fire_thermal_guided_workflow(case)
        if coarse.get("status") != "COMPLETE" or coarse.get("calculated_time_min") is None:
            raise FireUIError(coarse.get("diagnostic") or "SP554 12.5 coarse FVM did not produce a valid result")
        evidence, refined = mesh_convergence_check(
            case,
            float(case["reduced_thickness_mm"]),
            coarse_result=coarse,
            keep_visualization_on_refined=True,
        )
    except (ValueError, TypeError, KeyError) as exc:
        raise FireUIError(str(exc)) from exc
    if refined.get("status") != "COMPLETE" or refined.get("calculated_time_min") is None:
        raise FireUIError(refined.get("diagnostic") or "SP554 12.5 refined FVM did not produce a valid result")
    return evidence, refined


def _direct_fdm_12_5_v085(values, node):
    thickness = _route._finite(values, "protection_candidate_thickness_mm", positive=True)
    evidence, refined = _qualified_refined_result(values, thickness)
    return {
        "protection_thickness_mm": float(thickness),
        "protected_fire_resistance_min": float(refined["actual_fire_resistance_min"]),
        "protection_12_5_calculation_trace": refined,
    }


def _inverse_fdm_12_5_v085(values, node):
    # Keep the existing bounded monotonic search on the economical base mesh,
    # then qualify the selected thickness on the doubled mesh.  This avoids
    # multiplying every bisection evaluation while still making the reported
    # engineering result a refined, convergence-checked solution.
    base = _route._inverse_fdm_12_5(values, node)
    thickness = float(base["protection_thickness_mm"])
    required = _route._finite(values, "required_fire_resistance_min", positive=True)
    evidence, refined = _qualified_refined_result(values, thickness)
    refined_time = float(refined["actual_fire_resistance_min"])
    if refined_time < required - 1e-9:
        raise FireUIError(
            "Refined FVM result falls below the required fire resistance at the coarse-grid selected thickness; "
            "automatic result is fail-closed instead of hiding the mesh effect"
        )
    trace = dict(base.get("protection_12_5_calculation_trace") or {})
    trace["selected_result"] = refined
    trace["mesh_convergence"] = evidence
    trace["selected_result_basis"] = "refined_2n_mesh_after_base_mesh_inverse_search"
    return {
        "protection_thickness_mm": thickness,
        "protected_fire_resistance_min": refined_time,
        "protection_12_5_calculation_trace": trace,
    }


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    _install_v084_registry(registry)
    install_thermal_solver_patch()
    registry.register("SP554_C_12_5_DIRECT_PROTECTED_TIME", _direct_fdm_12_5_v085)
    registry.register("SP554_C_12_5_MINIMUM_THICKNESS_SEARCH", _inverse_fdm_12_5_v085)
    return registry


__all__ = ["install_registry_remediation", "_direct_fdm_12_5_v085", "_inverse_fdm_12_5_v085"]
