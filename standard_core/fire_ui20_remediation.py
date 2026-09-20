"""FIRE-UI2.0 conditional signed-moment and thermal execution remediation.

This layer is cumulative over FIRE-UI1.9.  It does not change SP16/SP554
formulae; it repairs UI/DAG authoring semantics and registers production
executors for thermal nodes whose formula helpers were previously unbound.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui19_heated_perimeter import build_fire_ui19_registry
from .profile_catalog import InterimProfileCatalog
from .fire_sp554_thermal import (
    _figure1_time,
    _standard_fire_temperature_c,
    _heat_transfer_coefficient_w_m2k,
    _steel_heat_capacity_j_kgk,
)


def _num(values: Mapping[str, Any], qid: str, *, positive: bool = False) -> float:
    v=values.get(qid)
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)):
        raise FireUIError(f"{qid} must be a finite number")
    x=float(v)
    if positive and x<=0.0:
        raise FireUIError(f"{qid} must be > 0")
    return x


def _mx_restrained(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """SP16 9.2.6: max(|Mmid|, 0.5|Mmax|), retaining source sign."""
    mmid=_num(values,"M_x_mid_third_max")
    mmax=_num(values,"M_x_full_length_max")
    candidate_mid=abs(mmid)
    candidate_half=0.5*abs(mmax)
    # On exact equality retain the first normative candidate (middle third).
    if candidate_mid >= candidate_half:
        signed=mmid
        design=candidate_mid
    else:
        signed=math.copysign(candidate_half,mmax)
        design=candidate_half
    return {"M_x_c_design":design,"M_x_c_signed":signed}


def _mx_fixed_free(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """SP16 9.2.6: max(|Mfix|, |ML/3|), retaining source sign."""
    mfix=_num(values,"M_x_fixed_end")
    ml3=_num(values,"M_x_at_L_over_3")
    if abs(mfix) >= abs(ml3):
        return {"M_x_c_design":abs(mfix),"M_x_c_signed":mfix}
    return {"M_x_c_design":abs(ml3),"M_x_c_signed":ml3}


def _gost30247_curve(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    t0=_num(values,"gost30247_initial_furnace_temperature_c")
    # JSON-serializable contract.  Consumers retain the source formula and time unit.
    contract={
        "schema":"gost30247_standard_fire_curve_contract_v1",
        "standard":"GOST30247_0",
        "clause":"6.1",
        "formula":"(1)",
        "initial_temperature_c":t0,
        "time_unit":"min",
        "temperature_unit":"degC",
        "expression":"T=T0+345*log10(8*t+1)",
    }
    return {"gost30247_standard_fire_curve_contract":contract}


def _figure1_unprotected(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    delta=_num(values,"delta_pr",positive=True)
    target=_num(values,"critical_temperature_c")
    try:
        result=_figure1_time({"critical_temperature_c":target},delta)
    except ValueError as exc:
        raise FireUIError(str(exc)) from exc
    if result.get("status")!="COMPLETE" or result.get("actual_fire_resistance_min") is None:
        raise FireUIError(str(result.get("diagnostic") or "SP554 Figure 1 route incomplete"))
    return {"unprotected_fire_resistance_min":float(result["actual_fire_resistance_min"])}


def _unprotected_step(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Execute SP554 (12.1)-(12.4) with the DAG-provided reduced emissivity.

    The FIRE-D3 core has the verified recurrence.  This binding is intentionally
    explicit because the DAG supplies epsilon_reduced directly rather than the
    two emissivities used by the older case API.
    """
    delta_mm=_num(values,"delta_pr",positive=True)
    target=_num(values,"critical_temperature_c")
    dt_min=_num(values,"sp554_dt_unprotected_min",positive=True)
    rho=_num(values,"sp554_steel_density_12_2",positive=True)
    c0=_num(values,"sp554_steel_c0_12_2",positive=True)
    kc=_num(values,"sp554_steel_c_temp_coeff_12_2")
    eps=_num(values,"sp554_eps_reduced_12_4",positive=True)
    if dt_min > 0.1 + 1e-12:
        raise FireUIError("SP554 unprotected explicit route requires time step <= 0.1 min")
    if not (0.0 < eps <= 1.0):
        raise FireUIError("sp554_eps_reduced_12_4 must be in (0,1]")
    contract=values.get("gost30247_standard_fire_curve_contract")
    if not isinstance(contract,Mapping) or contract.get("schema")!="gost30247_standard_fire_curve_contract_v1":
        raise FireUIError("standard-fire curve contract is missing or incompatible")
    initial=contract.get("initial_temperature_c")
    if isinstance(initial,bool) or not isinstance(initial,(int,float)) or not math.isfinite(float(initial)):
        raise FireUIError("standard-fire curve contract has invalid initial temperature")
    initial=float(initial)
    if target <= initial:
        return {"unprotected_fire_resistance_min":0.0}
    delta_m=delta_mm/1000.0
    steel_t=initial
    time_min=0.0
    max_time_min=360.0
    while time_min < max_time_min-1e-12:
        next_time=min(time_min+dt_min,max_time_min)
        actual_dt=next_time-time_min
        fire_t=_standard_fire_temperature_c(next_time,initial)
        alpha=_heat_transfer_coefficient_w_m2k(fire_t,steel_t,eps)
        cp=_steel_heat_capacity_j_kgk(c0,kc,steel_t)
        next_steel=steel_t+(actual_dt*60.0)*alpha*(fire_t-steel_t)/(rho*delta_m*cp)
        if not math.isfinite(next_steel) or next_steel < steel_t-1e-9:
            raise FireUIError("SP554 unprotected thermal step became unstable/non-monotone")
        if next_steel >= target:
            frac=(target-steel_t)/(next_steel-steel_t) if next_steel>steel_t else 0.0
            return {"unprotected_fire_resistance_min":float(time_min+frac*actual_dt)}
        steel_t=next_steel
        time_min=next_time
    raise FireUIError("critical temperature was not reached within 360 min; extrapolation is forbidden")


def build_fire_ui20_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI2.0 executor registry over the FIRE-UI1.9 baseline.

    Standard reference:
        SP16 9.2.6 signed moment selection; GOST 30247.0 clause 6.1 formula (1); SP554 Section 12.2 formulas (12.1)-(12.4) and Figure 1.

    Parameters:
        catalog: Frozen interim section-profile catalog inherited by earlier FIRE-UI registry layers.
        registry: Optional registry to extend in place.

    Returns:
        ExecutionRegistry with inherited executors plus FIRE-UI2.0 signed-moment and thermal bindings.

    Assumptions:
        The active DAG is v0.3.56 and supplies quantities with the units declared by that graph.

    Sign convention:
        User-authored moments retain their algebraic sign; modulus is used only for the normative comparison.

    Unit convention:
        Mechanical moments use N*mm; thermal time uses minutes and temperature uses degrees Celsius.

    Applicability:
        FIRE-UI2.0 guided SP16-to-SP554 workflow.

    Limitations:
        This registry does not close the general Qy or torsion-T branches; those remain explicit fail-closed routes.

    Raises:
        Executor calls raise FireUIError for invalid domains or incomplete thermal contracts.

    Examples:
        ``registry = build_fire_ui20_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_fire_ui20_remediation.py`` plus cumulative FIRE-UI regression suites.

    Implementation notes:
        Thermal bindings delegate to the verified FIRE-D3 core where possible and preserve no-extrapolation gates.
    """
    reg=build_fire_ui19_registry(catalog,registry)
    bindings={
        "SP16_C_C_MX_RESTRAINED":_mx_restrained,
        "SP16_C_C_MX_FIXED_FREE":_mx_fixed_free,
        "GOST30247_C_FORMULA1_STANDARD_FIRE_CURVE":_gost30247_curve,
        "SP554_C_FIG1_UNPROTECTED_INTERPOLATION":_figure1_unprotected,
        "SP554_C_UNPROTECTED_STEP_12_1_12_4":_unprotected_step,
    }
    for node_id,fn in bindings.items():
        reg.register(node_id,fn)
    return reg
