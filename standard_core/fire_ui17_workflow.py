"""FIRE-UI1.7 critical-temperature aggregation and restraint UX execution bindings."""
from __future__ import annotations
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui16_workflow import build_fire_ui16_registry
from .fire_sp554_runtime import sp554_appendix_b_critical_temperature_selection
from .profile_catalog import InterimProfileCatalog


def _critical_temperature_selection(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Execute the qualified independent Appendix-B inversion policy for one FIRE-UI1.7 selector node."""
    group=values.get("steel_strength_group")
    gamma_t=values.get("gamma_T_required")
    if not isinstance(group,str) or not group:
        raise FireUIError("steel_strength_group is required for Appendix-B inversion")
    if isinstance(gamma_t,bool) or not isinstance(gamma_t,(int,float)):
        raise FireUIError("gamma_T_required must be numeric")
    compression=node["id"].endswith("_COMPRESSION")
    gamma_e=values.get("gamma_E_required") if compression else None
    if compression and (isinstance(gamma_e,bool) or not isinstance(gamma_e,(int,float))):
        raise FireUIError("gamma_E_required is required for compression critical-temperature selection")
    try:
        selected=sp554_appendix_b_critical_temperature_selection(group,float(gamma_t),None if gamma_e is None else float(gamma_e))
    except ValueError as exc:
        raise FireUIError(str(exc)) from exc
    out:dict[str,Any]={
        "fire_d2_strength_inversion_result":selected["strength_inversion"],
        "fire_d2_critical_temperature_status":selected["status"],
    }
    if selected.get("modulus_inversion") is not None:
        out["fire_d2_modulus_inversion_result"]=selected["modulus_inversion"]
    if selected.get("critical_temperature_c") is not None:
        out["fire_d2_critical_temperature_c"]=float(selected["critical_temperature_c"])
    if selected.get("critical_temperature_lower_bound_c") is not None:
        out["fire_d2_critical_temperature_lower_bound_c"]=float(selected["critical_temperature_lower_bound_c"])
    kind=selected.get("controlling_kind")
    if kind is None:
        kind="bounded"
    out["fire_d2_critical_temperature_controlling_kind"]=kind
    return out


def build_fire_ui17_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI1.7 execution registry over FIRE-UI1.6 and bind independent Appendix-B critical-temperature selectors.

    Standard reference:
        SP554 8.6 and Appendix B Table B.1 / Figures B.1-B.8; SP16 restraint/Table-7 changes in FIRE-UI1.7 are presentation-only and remain DAG-driven.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited section/material executors.
        registry: Optional existing execution registry to extend.

    Returns:
        ExecutionRegistry containing all FIRE-UI1.6 bindings plus strength-only and compression critical-temperature selector executors.

    Assumptions:
        FIRE-UI1.6 registry qualification and frozen Appendix-B source data remain valid.

    Sign convention:
        Inherited signed-load convention is unchanged; critical-temperature selectors consume positive reduction coefficients only.

    Unit convention:
        Inherited canonical units; selector temperatures are degrees Celsius.

    Applicability:
        Guided SP16↔SP554 FIRE-UI1.7 calculations.

    Limitations:
        No Appendix-B extrapolation. Unsupported mechanical branches inherited from FIRE-UI1.6 remain explicit fail-closed terminals.

    Raises:
        Propagates FireUIError from inherited construction or selector execution.

    Examples:
        ``registry = build_fire_ui17_registry(InterimProfileCatalog())``.

    Tests:
        FIRE-UI1.7 end-to-end and critical-temperature regression suites.

    Implementation notes:
        The two selector nodes deliberately share one qualified production function; the compression node makes gamma_e a required dependency while the strength-only node does not.
    """
    reg=build_fire_ui16_registry(catalog,registry)
    reg.register("SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY",_critical_temperature_selection)
    reg.register("SP554_FIRE_UI17_C_TCR_COMPRESSION",_critical_temperature_selection)
    return reg
