"""FIRE-UI1.8 cumulative workflow registry for the FIRE-D2 -> FIRE-D3 handoff hotfix."""
from __future__ import annotations
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui17_workflow import build_fire_ui17_registry
from .profile_catalog import InterimProfileCatalog


def _fire_d2_to_d3_exact_tcr_handoff(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Copy one exact qualified FIRE-D2 critical temperature into both FIRE-D3 target quantities."""
    status=values.get("fire_d2_critical_temperature_status")
    tcr=values.get("fire_d2_critical_temperature_c")
    if status != "COMPLETE":
        raise FireUIError("FIRE-D3 exact-temperature handoff requires fire_d2_critical_temperature_status=COMPLETE")
    if isinstance(tcr,bool) or not isinstance(tcr,(int,float)):
        raise FireUIError("exact fire_d2_critical_temperature_c is required for FIRE-D3 handoff")
    value=float(tcr)
    if value <= 20.0:
        raise FireUIError("FIRE-D3 thermal handoff requires an exact critical temperature above ambient")
    return {
        "critical_temperature_c": value,
        "fire_d3_critical_temperature_handoff_c": value,
    }


def build_fire_ui18_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI1.8 execution registry over FIRE-UI1.7 and bind the exact FIRE-D2 to FIRE-D3 critical-temperature handoff.

    Standard reference:
        SP554 Sections 8-11 mechanical critical-temperature result followed by Section 12 thermal calculation; this hotfix changes guided handoff semantics only and introduces no new normative equation.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited executors.
        registry: Optional execution registry to extend.

    Returns:
        ExecutionRegistry containing all FIRE-UI1.7 production bindings plus the FIRE-D3 exact-temperature handoff executor.

    Assumptions:
        FIRE-UI1.7 critical-temperature aggregation remains qualified and an exact Tcr is available when status is COMPLETE.

    Sign convention:
        Inherited FIRE-UI1.7 signed-load convention.

    Unit convention:
        Inherited canonical units; critical temperature is in degrees Celsius.

    Applicability:
        Guided SP16↔SP554 FIRE-UI1.8 calculations.

    Limitations:
        Lower-bound-only critical temperatures are not converted to a fabricated exact Section-12 target. Ambient-capacity failure remains terminal.

    Raises:
        Propagates inherited registry-construction errors; the handoff executor raises FireUIError for non-exact or non-physical handoff states.

    Examples:
        ``registry = build_fire_ui18_registry(InterimProfileCatalog())``.

    Tests:
        FIRE-UI1.8 exact-Tcr handoff and fresh-extraction regression suites.

    Implementation notes:
        The explicit handoff executor is necessary because the frozen FIRE-D3 handoff node produces two trace quantities from one exact scalar temperature, while the generic single-expression declarative runtime intentionally supports one produced quantity only.
    """
    reg=build_fire_ui17_registry(catalog,registry)
    reg.register("SP554_FIRE_D3_C_D2_TCR_HANDOFF",_fire_d2_to_d3_exact_tcr_handoff)
    return reg
