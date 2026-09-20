"""Current-SP16 fatigue design calculations for Section 12 and Annex K.

Rebaselined against СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024.
Clause 12.1.3 is excluded from 10.01.2025 by Change No. 6; no low-cycle
calculation formula is invented in its place.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_35 = json.loads((_DATA_DIR / "table_35_fatigue_resistance.json").read_text(encoding="utf-8"))
_TABLE_36 = json.loads((_DATA_DIR / "table_36_fatigue_asymmetry_factor.json").read_text(encoding="utf-8"))
_TABLE_K1 = json.loads((_DATA_DIR / "annex_k_table_k1_fatigue_groups.json").read_text(encoding="utf-8"))
_K1_BY_ID = {entry["case_id"]: entry for entry in _TABLE_K1["entries"]}

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-12.1.1-APPLICABILITY",
    "SP16-PROC-12.1.2-STRESS-ASYMMETRY-RATIO",
    "SP16-PROC-12.1.2-CYCLE-FACTOR-ROUTING",
    "SP16-PROC-12.1.2-RESISTANCE-CAP",
    "SP16-PROC-12.1.1-LOW-CYCLE-BOUNDARY-CURRENT",
    "SP16-PROC-12.2-CRANE-CYCLE-FACTOR",
    "SP16-PROC-12.2-WEB-FATIGUE-RESISTANCE",
    "SP16-PROC-K.1-GROUP-LOOKUP",
    "SP16-PROC-K.1-TUBE-CASE-20",
    "SP16-PROC-K.1-TUBE-CASE-21",
)


def _real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive(value: float, name: str) -> float:
    result = _real(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return result


def _nonnegative(value: float, name: str) -> float:
    result = _real(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _group(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("element_group must be an integer")
    if value not in range(1, 9):
        raise ValueError("element_group must be from 1 to 8")
    return value



def table_35_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 35 fatigue-resistance catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Table 35
        Audit ID: SP16-TBL-35
        Normative status: normative

    Mathematical form:
        Exact group and Run-bin catalogue.

    Parameters:
        No parameters.

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata and N/mm2 values
        Meaning: Deep copy of Table 35 data.

    Assumptions:
        - The supplied consolidated standard is the source of the printed values.

    Sign convention:
        - Resistances are positive.

    Unit convention:
        - Resistance values use N/mm2.

    Applicability:
        - Fatigue calculation under clause 12.1.2.

    Limitations:
        - No automatic Annex K classification or extrapolation beyond Run=675 N/mm2.

    Raises:
        RuntimeError: The packaged data file is unavailable or malformed at import time.

    Examples:
        >>> table_35_catalog()["all_steel_values"]["4"]
        75.0

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_table35_catalog_exists
        Validation cases:
            - V14-TBL-35

    Implementation notes:
        - Data are returned by deep copy.
        - Defaults are not applied.
    """
    return json.loads(json.dumps(_TABLE_35, ensure_ascii=False))


def fatigue_design_resistance_table35(element_group: int, normative_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Look up fatigue design resistance Rv from Table 35.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Table 35
        Audit ID: SP16-TBL-35
        Normative status: normative

    Mathematical form:
        Rv = Table35(group, Run).

    Parameters:
        element_group: Integer group 1-8 selected from Annex K.
        normative_ultimate_resistance_n_mm2: Positive normative ultimate resistance Run in N/mm2.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Fatigue design resistance Rv.

    Assumptions:
        - The element group has been selected from the matching Table K.1 diagram.

    Sign convention:
        - Resistance is positive.

    Unit convention:
        - Run and Rv use N/mm2.

    Applicability:
        - Groups 1-8; groups 1-2 require Run not exceeding 675 N/mm2.

    Limitations:
        - No interpolation or extrapolation is used.

    Raises:
        ValueError: Group or Run is outside Table 35.
        TypeError: Group or Run has invalid type.

    Examples:
        >>> fatigue_design_resistance_table35(1, 440.0)
        128.0

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_table35_all_values
        Validation cases:
            - V14-TBL-35

    Implementation notes:
        - Printed upper boundaries are inclusive.
        - No national choice is applied.
    """
    group = _group(element_group)
    run = _positive(normative_ultimate_resistance_n_mm2, "normative_ultimate_resistance_n_mm2")
    if group >= 3:
        return float(_TABLE_35["all_steel_values"][str(group)])
    for row in _TABLE_35["steel_bins"]:
        lower = row["lower_exclusive"]
        upper = float(row["upper_inclusive"])
        if (lower is None or run > float(lower)) and run <= upper:
            return float(row[f"group_{group}"])
    raise ValueError("Table 35 does not provide a value for groups 1-2 above Run=675 N/mm2")


def cycle_factor_group_1_2_eq171(load_cycles: float) -> float:
    """
    Summary:
        Calculate cycle factor alpha for fatigue groups 1 and 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Equation (171)
        Audit ID: SP16-EQ-171
        Normative status: normative

    Mathematical form:
        alpha = 0.064(n/10^6)^2 - 0.5(n/10^6) + 1.75.

    Parameters:
        load_cycles: Number of cycles n, dimensionless.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Cycle factor alpha.

    Assumptions:
        - The element belongs to fatigue group 1 or 2.

    Sign convention:
        - Cycle count and alpha are positive.

    Unit convention:
        - Cycle count is dimensionless.

    Applicability:
        - 10^5 <= n < 3.9*10^6.

    Limitations:
        - At and above 3.9*10^6 the clause fixes alpha=0.77 instead.

    Raises:
        ValueError: Cycle count is outside the equation range.
        TypeError: Cycle count is not a finite real number.

    Examples:
        >>> cycle_factor_group_1_2_eq171(1_000_000)
        1.314

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_eq171_normal
        Validation cases:
            - V14-EQ-171

    Implementation notes:
        - The literal printed coefficients are retained.
        - No cycle-spectrum accumulation is implied.
    """
    n = _positive(load_cycles, "load_cycles")
    if n < 1.0e5 or n >= 3.9e6:
        raise ValueError("Equation (171) requires 1e5 <= n < 3.9e6")
    x = n / 1.0e6
    return 0.064*x*x - 0.5*x + 1.75


def cycle_factor_group_3_8_eq172(load_cycles: float) -> float:
    """
    Summary:
        Calculate cycle factor alpha for fatigue groups 3 through 8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Equation (172)
        Audit ID: SP16-EQ-172
        Normative status: normative

    Mathematical form:
        alpha = 0.07(n/10^6)^2 - 0.64(n/10^6) + 2.2.

    Parameters:
        load_cycles: Number of cycles n, dimensionless.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Cycle factor alpha.

    Assumptions:
        - The element belongs to fatigue group 3-8.

    Sign convention:
        - Cycle count and alpha are positive.

    Unit convention:
        - Cycle count is dimensionless.

    Applicability:
        - 10^5 <= n < 3.9*10^6.

    Limitations:
        - At and above 3.9*10^6 the clause fixes alpha=0.77 instead.

    Raises:
        ValueError: Cycle count is outside the equation range.
        TypeError: Cycle count is not a finite real number.

    Examples:
        >>> cycle_factor_group_3_8_eq172(1_000_000)
        1.63

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_eq172_normal
        Validation cases:
            - V14-EQ-172

    Implementation notes:
        - The literal printed coefficients are retained.
        - No cycle-spectrum accumulation is implied.
    """
    n = _positive(load_cycles, "load_cycles")
    if n < 1.0e5 or n >= 3.9e6:
        raise ValueError("Equation (172) requires 1e5 <= n < 3.9e6")
    x = n / 1.0e6
    return 0.07*x*x - 0.64*x + 2.2


def fatigue_cycle_factor_alpha(load_cycles: float, element_group: int) -> float:
    """
    Summary:
        Route the cycle-dependent fatigue factor to equation (171), equation (172), or alpha=0.77.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Equations (171)-(172) and high-cycle rule
        Audit ID: SP16-PROC-12.1.2-CYCLE-FACTOR-ROUTING
        Normative status: normative

    Mathematical form:
        alpha=eq171 for groups 1-2, eq172 for groups 3-8, and 0.77 for n>=3.9e6.

    Parameters:
        load_cycles: Number of load cycles n.
        element_group: Fatigue group 1-8.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Applicable cycle factor alpha.

    Assumptions:
        - Group is selected from Annex K.

    Sign convention:
        - Cycle count and factor are positive.

    Unit convention:
        - Cycle count is dimensionless.

    Applicability:
        - n >= 10^5 under the ordinary Section 12 fatigue route.

    Limitations:
        - Variable-amplitude damage accumulation is not provided by Section 12.1.2.

    Raises:
        ValueError: n<10^5 or group outside 1-8.
        TypeError: Invalid scalar or group type.

    Examples:
        >>> fatigue_cycle_factor_alpha(3_900_000, 1)
        0.77

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_cycle_factor_routing
        Validation cases:
            - V14-PROC-CYCLE-ROUTE

    Implementation notes:
        - Equality at 3.9e6 follows the printed fixed-value branch.
        - No hidden lower-cycle rule is used.
    """
    n = _positive(load_cycles, "load_cycles")
    group = _group(element_group)
    if n < 1.0e5:
        raise ValueError("Section 12.1.2 ordinary fatigue calculation requires at least 1e5 cycles")
    if n >= 3.9e6:
        return 0.77
    return cycle_factor_group_1_2_eq171(n) if group <= 2 else cycle_factor_group_3_8_eq172(n)


def stress_asymmetry_ratio(maximum_signed_stress_n_mm2: float, minimum_signed_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate signed stress asymmetry ratio rho for Table 36.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Table 36 definition of rho
        Audit ID: SP16-PROC-12.1.2-STRESS-ASYMMETRY-RATIO
        Normative status: normative

    Mathematical form:
        rho = sigma_min/sigma_max, with opposite signs producing negative rho.

    Parameters:
        maximum_signed_stress_n_mm2: Governing stress by absolute value; tension positive, compression negative.
        minimum_signed_stress_n_mm2: Smaller stress by absolute value at the same loading.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Signed asymmetry ratio rho.

    Assumptions:
        - Both stresses refer to the same section and loading.

    Sign convention:
        - Tension positive, compression negative; opposite signs give negative rho.

    Unit convention:
        - Both stresses use N/mm2.

    Applicability:
        - |sigma_min| <= |sigma_max| and sigma_max != 0.

    Limitations:
        - The function does not search a stress history for extrema.

    Raises:
        ValueError: Governing stress is zero or ordering/range is invalid.
        TypeError: A stress is not finite real.

    Examples:
        >>> stress_asymmetry_ratio(100.0, -50.0)
        -0.5

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_stress_asymmetry_ratio
        Validation cases:
            - V14-PROC-RHO

    Implementation notes:
        - The ordering requirement prevents silently swapping user inputs.
        - Signed values are retained.
    """
    maximum = _real(maximum_signed_stress_n_mm2, "maximum_signed_stress_n_mm2")
    minimum = _real(minimum_signed_stress_n_mm2, "minimum_signed_stress_n_mm2")
    if maximum == 0.0:
        raise ValueError("maximum_signed_stress_n_mm2 must be non-zero for rho")
    if abs(minimum) > abs(maximum) + 1e-12:
        raise ValueError("minimum stress must not exceed maximum stress in absolute value")
    rho = minimum / maximum
    if rho < -1.0-1e-12 or rho > 1.0+1e-12:
        raise ValueError("rho must lie within [-1, 1]")
    return max(-1.0, min(1.0, rho))


def fatigue_asymmetry_factor_table36(maximum_signed_stress_n_mm2: float, minimum_signed_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate fatigue asymmetry factor gamma_v from Table 36.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Table 36
        Audit ID: SP16-TBL-36
        Normative status: normative

    Mathematical form:
        Piecewise analytic gamma_v(rho) for tension- or compression-governing stress.

    Parameters:
        maximum_signed_stress_n_mm2: Governing signed stress by absolute value.
        minimum_signed_stress_n_mm2: Smaller signed stress at the same loading.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 36 factor gamma_v.

    Assumptions:
        - Positive governing stress denotes tension; negative denotes compression.

    Sign convention:
        - Tension positive and compression negative.

    Unit convention:
        - Input stresses use N/mm2.

    Applicability:
        - -1 <= rho < 1 with the Table 36 row selected by governing stress sign.

    Limitations:
        - rho=1 is excluded because the printed expressions are singular.

    Raises:
        ValueError: Stress ordering, zero maximum, or rho range is invalid.
        TypeError: Invalid stress type.

    Examples:
        >>> round(fatigue_asymmetry_factor_table36(100.0, -50.0), 6)
        1.25

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_table36_piecewise_values
        Validation cases:
            - V14-TBL-36

    Implementation notes:
        - Piecewise boundaries follow the printed inclusive/exclusive signs exactly.
        - No interpolation is required because the table gives formulas.
    """
    maximum = _real(maximum_signed_stress_n_mm2, "maximum_signed_stress_n_mm2")
    rho = stress_asymmetry_ratio(maximum, minimum_signed_stress_n_mm2)
    if rho >= 1.0:
        raise ValueError("Table 36 requires rho < 1")
    if maximum > 0.0:
        if rho <= 0.0:
            return 2.5/(1.5-rho)
        if rho <= 0.8:
            return 2.0/(1.2-rho)
        return 1.0/(1.0-rho)
    if maximum < 0.0:
        return 2.0/(1.0-rho)
    raise ValueError("governing stress must be non-zero")


def fatigue_utilization_eq170(maximum_absolute_stress_n_mm2: float, cycle_factor_alpha: float, fatigue_resistance_n_mm2: float, asymmetry_factor_gamma_v: float) -> float:
    """
    Summary:
        Calculate general fatigue utilization according to equation (170).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: Equation (170)
        Audit ID: SP16-EQ-170
        Normative status: normative

    Mathematical form:
        eta = |sigma_max|/(alpha*Rv*gamma_v).

    Parameters:
        maximum_absolute_stress_n_mm2: Non-negative governing stress magnitude.
        cycle_factor_alpha: Positive cycle factor alpha.
        fatigue_resistance_n_mm2: Positive fatigue resistance Rv.
        asymmetry_factor_gamma_v: Positive Table 36 factor gamma_v.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Fatigue utilization; pass when <=1.

    Assumptions:
        - Stress is calculated on the net section without dynamic and listed stability coefficients.

    Sign convention:
        - Demand is supplied as an absolute non-negative magnitude.

    Unit convention:
        - Stress and Rv use N/mm2.

    Applicability:
        - Ordinary high-cycle fatigue under clause 12.1.2.

    Limitations:
        - The function does not calculate alpha, Rv, gamma_v, or stress extrema.

    Raises:
        ValueError: Demand is negative or a denominator factor is non-positive.
        TypeError: Invalid scalar type.

    Examples:
        >>> fatigue_utilization_eq170(50.0, 1.0, 100.0, 1.0)
        0.5

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_eq170_normal
        Validation cases:
            - V14-EQ-170

    Implementation notes:
        - Equation factors remain separate for traceability.
        - The resistance-cap condition is checked by a separate function.
    """
    stress = _nonnegative(maximum_absolute_stress_n_mm2, "maximum_absolute_stress_n_mm2")
    alpha = _positive(cycle_factor_alpha, "cycle_factor_alpha")
    resistance = _positive(fatigue_resistance_n_mm2, "fatigue_resistance_n_mm2")
    gamma = _positive(asymmetry_factor_gamma_v, "asymmetry_factor_gamma_v")
    return stress/(alpha*resistance*gamma)


def fatigue_resistance_cap_check_clause_12_1_2(cycle_factor_alpha: float, fatigue_resistance_n_mm2: float, asymmetry_factor_gamma_v: float, design_ultimate_resistance_n_mm2: float, ultimate_resistance_safety_factor: float) -> dict[str, float | bool]:
    """
    Summary:
        Check the clause 12.1.2 upper condition on fatigue resistance.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.2
        Annex: None
        Equation/Table: alpha*Rv*gamma_v <= Ru/gamma_u
        Audit ID: SP16-PROC-12.1.2-RESISTANCE-CAP
        Normative status: normative

    Mathematical form:
        lhs=alpha*Rv*gamma_v; rhs=Ru/gamma_u.

    Parameters:
        cycle_factor_alpha: Positive alpha.
        fatigue_resistance_n_mm2: Positive Rv.
        asymmetry_factor_gamma_v: Positive gamma_v.
        design_ultimate_resistance_n_mm2: Positive Ru.
        ultimate_resistance_safety_factor: Positive gamma_u.

    Returns:
        Type: dict[str, float | bool]
        Unit: N/mm2 and boolean
        Meaning: Left side, right side, utilization, and pass/fail.

    Assumptions:
        - Ru and gamma_u correspond to the same steel and design basis.

    Sign convention:
        - Resistances and factors are positive.

    Unit convention:
        - Resistance values use N/mm2.

    Applicability:
        - Every equation (170) check.

    Limitations:
        - The function reports failure; it does not silently cap the denominator.

    Raises:
        ValueError: A factor or resistance is non-positive.
        TypeError: Invalid scalar type.

    Examples:
        >>> fatigue_resistance_cap_check_clause_12_1_2(1.0, 100.0, 1.0, 400.0, 1.3)["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_resistance_cap_check
        Validation cases:
            - V14-PROC-CAP

    Implementation notes:
        - No hidden minimum with Ru/gamma_u is taken.
        - Failure remains visible to the caller.
    """
    lhs = _positive(cycle_factor_alpha, "cycle_factor_alpha")*_positive(fatigue_resistance_n_mm2, "fatigue_resistance_n_mm2")*_positive(asymmetry_factor_gamma_v, "asymmetry_factor_gamma_v")
    rhs = _positive(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2")/_positive(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor")
    return {"fatigue_denominator_n_mm2":lhs,"ultimate_limit_n_mm2":rhs,"cap_utilization":lhs/rhs,"pass":lhs<=rhs}


def fatigue_applicability_route_clause_12_1_1_12_1_3(load_cycles: float, resonant_vortex_excitation: bool = False) -> dict[str, Any]:
    """
    Summary:
        Route a case at the current clause-12.1.1 fatigue/low-cycle boundary.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.1.1; 12.1.3 is excluded from 10.01.2025 by Change No. 6
        Annex: None
        Equation/Table: Applicability boundary
        Audit ID: SP16-PROC-12.1.1-APPLICABILITY; SP16-PROC-12.1.1-LOW-CYCLE-BOUNDARY-CURRENT
        Normative status: normative applicability / explicit external boundary

    Mathematical form:
        n >= 1e5 -> ordinary fatigue route under 12.1.2; n < 1e5 -> low-cycle-fatigue
        method required externally because current Section 12 contains no replacement for excluded 12.1.3.

    Parameters:
        load_cycles: Non-negative number of cycles from technological operating requirements.
        resonant_vortex_excitation: Whether a high structure is subject to resonant vortex excitation.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Current-SP16 applicability route and external obligations.

    Assumptions:
        - Cycle count is supplied from technological operating requirements.
        - Loads/actions are established under SP 20.13330 externally.

    Sign convention:
        - Cycle count is non-negative.

    Unit convention:
        - Cycle count is dimensionless.

    Applicability:
        - Section 12.1.1.

    Limitations:
        - Change No. 6 excluded clause 12.1.3. The package does not recreate its former low-cycle formula.
        - Resonant vortex excitation is an independent trigger for a fatigue assessment, but it does not
          authorize using equations (170)-(172) below the ordinary-fatigue cycle boundary.

    Raises:
        ValueError: Cycle count is negative.
        TypeError: Cycle count or resonance flag has invalid type.

    Examples:
        >>> fatigue_applicability_route_clause_12_1_1_12_1_3(100000)["route"]
        'section_12_ordinary_fatigue'

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_fatigue_applicability_route
            - tests/test_stage_n9_fatigue_workflows.py::test_n9_low_cycle_boundary_is_current_change6_fail_closed

    Implementation notes:
        - The function name is retained for backward API compatibility only; 12.1.3 is not executed.
        - Stress-concentration-minimizing detailing remains required.
    """
    n = _nonnegative(load_cycles, "load_cycles")
    if not isinstance(resonant_vortex_excitation, bool):
        raise TypeError("resonant_vortex_excitation must be boolean")
    ordinary = n >= 1.0e5
    if ordinary:
        route = "section_12_ordinary_fatigue"
    else:
        route = "external_low_cycle_fatigue_rules"
    return {
        "route": route,
        "ordinary_fatigue_required": ordinary,
        "low_cycle_method_external": not ordinary,
        "clause_12_1_3_current_status": "EXCLUDED_FROM_2025_01_10_CHANGE_6",
        "resonant_vortex_fatigue_assessment_required": resonant_vortex_excitation,
        "stress_concentration_minimizing_detailing_required": True,
        "cycle_count_source": "technological operating requirements",
        "load_source": "SP 20.13330 external input",
    }


def annex_k_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Annex K Table K.1 fatigue-group catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: Annex K
        Annex: К
        Equation/Table: Table K.1
        Audit ID: SP16-TBL-К-1
        Normative status: annex reference table

    Mathematical form:
        Explicit case identifier -> element group 1-8.

    Parameters:
        No parameters.

    Returns:
        Type: dict[str, Any]
        Unit: metadata
        Meaning: Deep copy of transcribed Table K.1 entries.

    Assumptions:
        - User compares the standard diagram and description before selecting a case.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Geometry conditions use mm, degrees, or dimensionless ratios as stated.

    Applicability:
        - Fatigue group selection for Table 35.

    Limitations:
        - Diagrams are represented by stable identifiers and short descriptions, not reproduced images.

    Raises:
        RuntimeError: Packaged catalogue is unavailable or malformed at import time.

    Examples:
        >>> len(annex_k_catalog()["entries"]) >= 30
        True

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_annex_k_catalog_complete
        Validation cases:
            - V14-TBL-K1

    Implementation notes:
        - Copyright-sensitive figures are not embedded.
        - No automatic geometry recognition is claimed.
    """
    return json.loads(json.dumps(_TABLE_K1, ensure_ascii=False))


def annex_k_group(case_id: str) -> int:
    """
    Summary:
        Look up the fatigue element group for an explicit Table K.1 case identifier.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: Annex K
        Annex: К
        Equation/Table: Table K.1
        Audit ID: SP16-PROC-K.1-GROUP-LOOKUP
        Normative status: annex reference table

    Mathematical form:
        group = K1[case_id].

    Parameters:
        case_id: Stable identifier from annex_k_catalog().

    Returns:
        Type: int
        Unit: dimensionless category
        Meaning: Fatigue group 1-8.

    Assumptions:
        - The selected identifier matches the actual detail and calculation section.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Group is dimensionless.

    Applicability:
        - Exact transcribed Table K.1 cases.

    Limitations:
        - The function does not verify geometry or weld quality.

    Raises:
        ValueError: Unknown case identifier.
        TypeError: case_id is not a string.

    Examples:
        >>> annex_k_group("K1-16-TRANSVERSE_WELD_SMOOTH")
        4

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_annex_k_lookup
        Validation cases:
            - V14-TBL-K1

    Implementation notes:
        - Unknown cases are rejected rather than approximated.
        - Diagram selection remains an engineering responsibility.
    """
    if not isinstance(case_id, str):
        raise TypeError("case_id must be a string")
    try:
        return int(_K1_BY_ID[case_id]["group"])
    except KeyError as exc:
        raise ValueError(f"Unknown Annex K Table K.1 case_id: {case_id}") from exc


def annex_k_tube_joint_group_case20(chord_thickness_to_diameter_ratio: float) -> dict[str, Any]:
    """
    Summary:
        Classify Annex K Table K.1 diagram 20 by chord thickness ratio.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: Annex K
        Annex: К
        Equation/Table: Table K.1, diagram 20
        Audit ID: SP16-PROC-K.1-TUBE-CASE-20
        Normative status: annex reference table

    Mathematical form:
        tm/dm>=1/14 -> group 7; 1/20<=tm/dm<1/14 -> group 8.

    Parameters:
        chord_thickness_to_diameter_ratio: Positive tm/dm.

    Returns:
        Type: dict[str, Any]
        Unit: dimensionless
        Meaning: Matching case identifier and fatigue group.

    Assumptions:
        - Geometry otherwise matches diagram 20.

    Sign convention:
        - Ratio is positive.

    Unit convention:
        - Ratio is dimensionless.

    Applicability:
        - Diagram 20 and printed ratio ranges.

    Limitations:
        - Ratios below 1/20 are not covered and are rejected.

    Raises:
        ValueError: Ratio lies outside the printed domain.
        TypeError: Ratio is invalid.

    Examples:
        >>> annex_k_tube_joint_group_case20(1/14)["group"]
        7

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_annex_k_tube_case20_boundaries
        Validation cases:
            - V14-PROC-K20

    Implementation notes:
        - Boundary equality follows the printed inequality signs.
        - No extrapolation below 1/20 is used.
    """
    ratio = _positive(chord_thickness_to_diameter_ratio, "chord_thickness_to_diameter_ratio")
    if ratio >= 1.0/14.0:
        case_id = "K1-20-TM_DM_GE_1_14"
    elif ratio >= 1.0/20.0:
        case_id = "K1-20-TM_DM_1_20_TO_1_14"
    else:
        raise ValueError("Table K.1 diagram 20 does not classify tm/dm below 1/20")
    return {"case_id":case_id,"group":annex_k_group(case_id),"chord_thickness_to_diameter_ratio":ratio}


def annex_k_tube_joint_group_case21(brace_to_chord_diameter_ratio: float, chord_thickness_to_diameter_ratio: float) -> dict[str, Any]:
    """
    Summary:
        Classify Annex K Table K.1 diagram 21 by brace and chord ratios.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: Annex K
        Annex: К
        Equation/Table: Table K.1, diagram 21
        Audit ID: SP16-PROC-K.1-TUBE-CASE-21
        Normative status: annex reference table

    Mathematical form:
        dd/dm in [0.4,0.7]; thickness bands map to groups 6, 7, or 8.

    Parameters:
        brace_to_chord_diameter_ratio: Positive dd/dm.
        chord_thickness_to_diameter_ratio: Positive tm/dm.

    Returns:
        Type: dict[str, Any]
        Unit: dimensionless
        Meaning: Matching case identifier and fatigue group.

    Assumptions:
        - Geometry and 45-60 degree brace angle match diagram 21.

    Sign convention:
        - Ratios are positive.

    Unit convention:
        - Ratios are dimensionless.

    Applicability:
        - 0.4<=dd/dm<=0.7 and tm/dm>=1/35.

    Limitations:
        - Other diameter ratios, thickness ratios, or angles are not classified.

    Raises:
        ValueError: A ratio lies outside the printed domain.
        TypeError: A ratio is invalid.

    Examples:
        >>> annex_k_tube_joint_group_case21(0.5, 1/14)["group"]
        6

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_annex_k_tube_case21_boundaries
        Validation cases:
            - V14-PROC-K21

    Implementation notes:
        - Boundary equality follows the printed inequalities.
        - Brace angle remains an explicit applicability prerequisite.
    """
    diameter = _positive(brace_to_chord_diameter_ratio, "brace_to_chord_diameter_ratio")
    thickness = _positive(chord_thickness_to_diameter_ratio, "chord_thickness_to_diameter_ratio")
    if diameter < 0.4 or diameter > 0.7:
        raise ValueError("Table K.1 diagram 21 requires 0.4 <= dd/dm <= 0.7")
    if thickness >= 1.0/14.0:
        case_id = "K1-21-TM_DM_GE_1_14"
    elif thickness >= 1.0/20.0:
        case_id = "K1-21-TM_DM_1_20_TO_1_14"
    elif thickness >= 1.0/35.0:
        case_id = "K1-21-TM_DM_1_35_TO_1_20"
    else:
        raise ValueError("Table K.1 diagram 21 does not classify tm/dm below 1/35")
    return {"case_id":case_id,"group":annex_k_group(case_id),"brace_to_chord_diameter_ratio":diameter,"chord_thickness_to_diameter_ratio":thickness}


def crane_runway_cycle_factor_clause_12_2(crane_group: str, metallurgical_shop: bool) -> float:
    """
    Summary:
        Select clause 12.2 cycle factor alpha for crane-runway fatigue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.2
        Annex: None
        Equation/Table: Crane-runway alpha rule
        Audit ID: SP16-PROC-12.2-CRANE-CYCLE-FACTOR
        Normative status: normative

    Mathematical form:
        alpha=0.77 for group 7K in metallurgical shops and group 8K; alpha=1.1 otherwise.

    Parameters:
        crane_group: Crane operating group, such as 7K or 8K.
        metallurgical_shop: Whether the crane operates in a metallurgical-production shop.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Clause 12.2 alpha.

    Assumptions:
        - Crane group is determined under the applicable crane/load standard.

    Sign convention:
        - Factor is positive.

    Unit convention:
        - Factor is dimensionless.

    Applicability:
        - Crane-runway fatigue under clause 12.2.

    Limitations:
        - Crane loads remain external inputs from SP 20.13330.

    Raises:
        ValueError: crane_group is empty.
        TypeError: Selector types are invalid.

    Examples:
        >>> crane_runway_cycle_factor_clause_12_2("8K", False)
        0.77

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_crane_cycle_factor
        Validation cases:
            - V14-PROC-CRANE-ALPHA

    Implementation notes:
        - Group 7K receives 0.77 only in metallurgical-production shops.
        - Other groups receive 1.1.
    """
    if not isinstance(crane_group, str) or not crane_group.strip():
        raise TypeError("crane_group must be a non-empty string")
    if not isinstance(metallurgical_shop, bool):
        raise TypeError("metallurgical_shop must be boolean")
    group = crane_group.strip().upper().replace("К", "K")
    return 0.77 if group == "8K" or (group == "7K" and metallurgical_shop) else 1.1


def crane_runway_web_fatigue_resistance_clause_12_2(flange_connection_type: str, web_zone_state: str) -> float:
    """
    Summary:
        Select fatigue resistance Rv for the upper web zone of a built-up crane-runway beam.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.2
        Annex: None
        Equation/Table: Resistance values accompanying equation (173)
        Audit ID: SP16-PROC-12.2-WEB-FATIGUE-RESISTANCE
        Normative status: normative

    Mathematical form:
        Welded/friction flange connection x compression/tension zone -> Rv.

    Parameters:
        flange_connection_type: 'welded' or 'friction'.
        web_zone_state: 'compression' or 'tension'.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Rv for equation (173).

    Assumptions:
        - The checked zone is the upper web zone of a built-up crane-runway beam.

    Sign convention:
        - State is categorical; returned resistance is positive.

    Unit convention:
        - Rv uses N/mm2.

    Applicability:
        - Span compression zone or continuous-beam support tension zone as stated in clause 12.2.

    Limitations:
        - Other connection types or web zones are not covered.

    Raises:
        ValueError: A selector is unsupported.
        TypeError: A selector is not a string.

    Examples:
        >>> crane_runway_web_fatigue_resistance_clause_12_2("welded", "compression")
        75.0

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_crane_web_resistance_values
        Validation cases:
            - V14-PROC-CRANE-RV

    Implementation notes:
        - Values are independent of steel grade in the printed clause.
        - Selection remains explicit.
    """
    if not isinstance(flange_connection_type, str) or not isinstance(web_zone_state, str):
        raise TypeError("connection type and web zone state must be strings")
    connection = flange_connection_type.strip().lower()
    state = web_zone_state.strip().lower()
    values = {("welded","compression"):75.0,("friction","compression"):96.0,("welded","tension"):65.0,("friction","tension"):89.0}
    try:
        return values[(connection,state)]
    except KeyError as exc:
        raise ValueError("supported selectors are welded/friction and compression/tension") from exc


def crane_runway_web_fatigue_utilization_eq173(sigma_x_n_mm2: float, sigma_xy_n_mm2: float, local_sigma_y_n_mm2: float, flange_sigma_y_n_mm2: float, fatigue_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate upper-web-zone fatigue utilization of a built-up crane-runway beam.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Current consolidated text, Changes No. 1-6 through 09.12.2024
        Clause: 12.2
        Annex: None
        Equation/Table: Equation (173)
        Audit ID: SP16-EQ-173
        Normative status: normative

    Mathematical form:
        eta=[0.5*sqrt(sigma_x^2+0.36*sigma_xy^2)+0.4*sigma_loc,y+0.5*sigma_f,y]/Rv.

    Parameters:
        sigma_x_n_mm2: Non-negative longitudinal stress magnitude from equation (67).
        sigma_xy_n_mm2: Non-negative shear-related stress magnitude from equation (67).
        local_sigma_y_n_mm2: Non-negative local transverse stress from equation (67).
        flange_sigma_y_n_mm2: Non-negative flange-related stress from equation (67).
        fatigue_resistance_n_mm2: Positive clause 12.2 Rv.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (173) fatigue utilization; pass when <=1.

    Assumptions:
        - Stress components are determined according to equation (67) from crane loads under SP 20.13330.

    Sign convention:
        - Equation (173) uses non-negative stress magnitudes in additive terms.

    Unit convention:
        - Stresses and Rv use N/mm2.

    Applicability:
        - Upper web zone of built-up crane-runway beams.

    Limitations:
        - This function does not calculate the equation (67) stresses or crane loads.

    Raises:
        ValueError: A demand is negative or resistance is non-positive.
        TypeError: Invalid scalar type.

    Examples:
        >>> round(crane_runway_web_fatigue_utilization_eq173(40,20,10,5,75), 6)
        0.365223

    Tests:
        Unit tests:
            - tests/test_fatigue_design.py::test_eq173_normal
        Validation cases:
            - V14-EQ-173

    Implementation notes:
        - Literal coefficients 0.5, 0.36, 0.4, and 0.5 are retained.
        - No alpha multiplier is inserted into equation (173).
    """
    sx = _nonnegative(sigma_x_n_mm2, "sigma_x_n_mm2")
    sxy = _nonnegative(sigma_xy_n_mm2, "sigma_xy_n_mm2")
    sloc = _nonnegative(local_sigma_y_n_mm2, "local_sigma_y_n_mm2")
    sf = _nonnegative(flange_sigma_y_n_mm2, "flange_sigma_y_n_mm2")
    resistance = _positive(fatigue_resistance_n_mm2, "fatigue_resistance_n_mm2")
    return (0.5*math.sqrt(sx*sx+0.36*sxy*sxy)+0.4*sloc+0.5*sf)/resistance
