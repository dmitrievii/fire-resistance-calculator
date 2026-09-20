"""FIRE-UI0 reference adapter proving reuse of frozen FIRE-D2/D3/D4 runtimes."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .fire_sp554_runtime import sp554_fire_mechanical_guided_workflow
from .fire_sp554_assessment import sp554_fire_result_assessment_workflow


def run_integrated_member_fire_case(
    mechanical_case: Mapping[str, Any],
    thermal_assessment_case: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Summary:
        Run the frozen FIRE-D2 mechanical runtime followed by FIRE-D3/FIRE-D4 and expose key values for the UI ledger.

    Standard reference:
        SP554 Sections 8-13 as already implemented and qualified by FIRE-D2, FIRE-D3, FIRE-D3.1 and FIRE-D4.

    Parameters:
        mechanical_case: Mapping accepted by sp554_fire_mechanical_guided_workflow.
        thermal_assessment_case: Mapping accepted by sp554_fire_result_assessment_workflow except critical_temperature_c, which is injected from FIRE-D2.

    Returns:
        Dictionary containing the untouched FIRE-D2 and FIRE-D4 results plus a small quantity-ID ledger projection.

    Assumptions:
        Both input mappings have already been collected/validated by a future guided UI binding layer.

    Sign convention:
        Inherited without modification from the frozen production runtimes.

    Unit convention:
        Inherited from FIRE-D2/D3/D4; temperatures in degC and fire-resistance times in minutes.

    Applicability:
        Reference integration seam for currently supported SP554 member routes; connections remain outside scope.

    Limitations:
        Does not infer mechanical inputs from UI answers and does not implement FIRE-D5 protection design or FIRE-D7 alternative fire.

    Raises:
        TypeError for non-mapping inputs; production runtime validation exceptions are propagated unchanged.

    Examples:
        See examples/fire_ui0_integrated_fire_d2_d4_control.json.

    Tests:
        tests/test_fire_ui0_architecture.py::test_integrated_reference_adapter_reuses_frozen_fire_d2_d3_d4.

    Implementation notes:
        No normative equation is duplicated here; the function composes existing frozen production workflows only.
    """
    if not isinstance(mechanical_case, Mapping) or not isinstance(thermal_assessment_case, Mapping):
        raise TypeError("both cases must be mappings")
    d2 = sp554_fire_mechanical_guided_workflow(mechanical_case)
    if d2.get("status") != "COMPLETE" or d2.get("critical_temperature_c") is None:
        return {"status": "INCOMPLETE_FAIL_CLOSED", "fire_d2": d2, "fire_d4": None, "ledger_outputs": {}}
    downstream = deepcopy(dict(thermal_assessment_case))
    downstream["critical_temperature_c"] = float(d2["critical_temperature_c"])
    d4 = sp554_fire_result_assessment_workflow(downstream)
    assessment = d4["assessment"]
    thermal = d4["upstream_thermal_result"]
    protected = str(thermal["thermal_route"]).startswith("PROTECTED_")
    ledger = {
        "gamma_T_required": float(d2["gamma_T_required"]),
        "critical_temperature_c": float(d2["critical_temperature_c"]),
        "required_fire_resistance_min": float(assessment["required_fire_resistance_min"]),
        "protected_fire_resistance_min" if protected else "unprotected_fire_resistance_min": float(assessment["actual_fire_resistance_min"]),
        "protected_compliance" if protected else "unprotected_compliance": assessment["compliance"] == "PASS",
    }
    return {
        "status": "COMPLETE",
        "fire_d2": d2,
        "fire_d4": d4,
        "ledger_outputs": ledger,
    }
