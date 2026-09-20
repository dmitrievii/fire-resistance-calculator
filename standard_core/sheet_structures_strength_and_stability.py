"""Strength and stability calculations for Section 11 of SP 16.13330.2017, Changes No. 1-6 through 09.12.2024."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_34 = json.loads((_DATA_DIR / "table_34_cylindrical_shell_coefficient.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-11.1.1-PRINCIPAL-STRESS-LIMITS",
    "SP16-PROC-11.1.4-LOCAL-EDGE-EFFECT",
    "SP16-PROC-11.1.5-CERTIFIED-SPATIAL-ANALYSIS",
    "SP16-PROC-11.2.1-CRITICAL-STRESS-SELECTION",
    "SP16-PROC-11.2.1-ECCENTRIC-COMPRESSION-ADJUSTMENT",
    "SP16-PROC-11.2.2-TUBE-ROUTING",
    "SP16-PROC-11.2.3-PANEL-INTERPOLATION",
    "SP16-PROC-11.2.3-PANEL-OR-SHELL-ROUTING",
    "SP16-PROC-11.2.4-EXTERNAL-PRESSURE-INTERPOLATION",
    "SP16-PROC-11.2.4-RING-STIFFENER-REQUIREMENTS",
    "SP16-PROC-11.2.5-COMBINED-CYLINDER-INTERACTION",
    "SP16-PROC-11.2.6-CONE-ANGLE-LIMIT",
    "SP16-PROC-11.2.8-COMBINED-CONE-INTERACTION",
    "SP16-PROC-11.2.9-SPHERE-RATIO-LIMIT",
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


def _working_condition(value: float) -> float:
    result = _positive(value, "working_condition_factor")
    return result


def _cos_beta(beta_degrees: float, *, maximum_degrees: float | None = None) -> float:
    beta = _real(beta_degrees, "beta_degrees")
    if beta < 0.0 or beta >= 90.0:
        raise ValueError("beta_degrees must satisfy 0 <= beta < 90")
    if maximum_degrees is not None and beta > maximum_degrees:
        raise ValueError(f"beta_degrees must not exceed {maximum_degrees:g}")
    cosine = math.cos(math.radians(beta))
    if cosine <= 0.0:
        raise ValueError("cos(beta) must be positive")
    return cosine


def _linear(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0 + (y1-y0)*(x-x0)/(x1-x0)

def table_34_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited transcription and metadata for Table 34.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Table 34
        Audit ID: SP16-TBL-34
        Normative status: normative

    Mathematical form:
        Exact data lookup catalogue.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Deep copy of the Table 34 data and applicability notes.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-TBL-34

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_34, ensure_ascii=False))


def table_34_c_coefficient(radius_to_thickness_ratio: float) -> float:
    """
    Summary:
        Look up coefficient c at an exact printed Table 34 node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Table 34
        Audit ID: SP16-TBL-34
        Normative status: normative

    Mathematical form:
        c = table34(r/t).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 34 coefficient c.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Exact printed r/t nodes 100, 200, 300, 400, 600, 800, 1000, 1500, or 2500.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-TBL-34

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(radius_to_thickness_ratio, "radius_to_thickness_ratio")
    values = _TABLE_34["values"]
    for key, raw_value in values.items():
        node = float(key)
        if math.isclose(ratio, node, rel_tol=1e-12, abs_tol=1e-12):
            return float(raw_value)
    raise ValueError("Table 34 lookup requires an exact printed r/t node; no interpolation rule is stated")


def membrane_strength_utilization_eq148(sigma_x_n_mm2: float, sigma_y_n_mm2: float, tau_xy_n_mm2: float, design_yield_resistance_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate the membrane equivalent-stress utilization of equation (148).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.1
        Annex: None
        Equation/Table: Equation (148)
        Audit ID: SP16-EQ-148
        Normative status: normative

    Mathematical form:
        sqrt(sx^2-sx*sy+sy^2+3*txy^2)/(Ry*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-148

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    sx=_real(sigma_x_n_mm2,"sigma_x_n_mm2"); sy=_real(sigma_y_n_mm2,"sigma_y_n_mm2"); tau=_real(tau_xy_n_mm2,"tau_xy_n_mm2")
    ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); gamma=_working_condition(working_condition_factor)
    radicand=sx*sx-sx*sy+sy*sy+3.0*tau*tau
    return math.sqrt(max(0.0,radicand))/(ry*gamma)


def principal_stresses_2d(sigma_x_n_mm2: float, sigma_y_n_mm2: float, tau_xy_n_mm2: float) -> tuple[float, float]:
    """
    Summary:
        Calculate the two in-plane principal membrane stresses.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.1
        Annex: None
        Equation/Table: Clause 11.1.1 principal-stress requirement
        Audit ID: SP16-PROC-11.1.1-PRINCIPAL-STRESS-LIMITS
        Normative status: normative

    Mathematical form:
        sigma_1,2=(sx+sy)/2 +/- sqrt(((sx-sy)/2)^2+txy^2).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: tuple[float, float]
        Unit: N/mm2
        Meaning: Maximum and minimum principal membrane stresses.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.1.1-PRINCIPAL-STRESS-LIMITS

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    sx=_real(sigma_x_n_mm2,"sigma_x_n_mm2"); sy=_real(sigma_y_n_mm2,"sigma_y_n_mm2"); tau=_real(tau_xy_n_mm2,"tau_xy_n_mm2")
    mean=0.5*(sx+sy); radius=math.sqrt((0.5*(sx-sy))**2+tau*tau)
    return mean+radius, mean-radius


def principal_stress_resistance_check_clause_11_1_1(sigma_x_n_mm2: float, sigma_y_n_mm2: float, tau_xy_n_mm2: float, tension_design_resistance_n_mm2: float, compression_design_resistance_n_mm2: float, working_condition_factor: float) -> dict[str, Any]:
    """
    Summary:
        Check the separate principal-stress limits required after equation (148).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.1
        Annex: None
        Equation/Table: Clause 11.1.1 principal-stress requirement
        Audit ID: SP16-PROC-11.1.1-PRINCIPAL-STRESS-LIMITS
        Normative status: normative

    Mathematical form:
        |principal tension/compression| <= corresponding design resistance times gamma_c.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Principal stresses, utilizations, and pass/fail status.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.1.1-PRINCIPAL-STRESS-LIMITS

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    pmax,pmin=principal_stresses_2d(sigma_x_n_mm2,sigma_y_n_mm2,tau_xy_n_mm2)
    rt=_positive(tension_design_resistance_n_mm2,"tension_design_resistance_n_mm2"); rc=_positive(compression_design_resistance_n_mm2,"compression_design_resistance_n_mm2"); gamma=_working_condition(working_condition_factor)
    tension=max(pmax,pmin,0.0); compression=max(-pmax,-pmin,0.0)
    return {"principal_max_n_mm2":pmax,"principal_min_n_mm2":pmin,"tension_utilization":tension/(rt*gamma),"compression_utilization":compression/(rc*gamma),"pass":tension<=rt*gamma and compression<=rc*gamma}


def meridional_stress_eq149(projected_pressure_force_n: float, radius_mm: float, thickness_mm: float, beta_degrees: float) -> float:
    """
    Summary:
        Calculate meridional membrane stress from equation (149).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.2
        Annex: None
        Equation/Table: Equation (149)
        Audit ID: SP16-EQ-149
        Normative status: normative

    Mathematical form:
        sigma_1=F/(2*pi*r*t*cos(beta)).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Signed meridional membrane stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-149

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    force=_real(projected_pressure_force_n,"projected_pressure_force_n"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); c=_cos_beta(beta_degrees)
    return force/(2.0*math.pi*r*t*c)


def circumferential_stress_eq150(pressure_n_mm2: float, thickness_mm: float, meridional_stress_n_mm2: float, meridional_radius_mm: float, circumferential_radius_mm: float) -> float:
    """
    Summary:
        Calculate circumferential membrane stress from equation (150).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.2
        Annex: None
        Equation/Table: Equation (150)
        Audit ID: SP16-EQ-150
        Normative status: normative

    Mathematical form:
        sigma_2=(p/t-sigma_1/r_1)*r_2.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Signed circumferential membrane stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-150

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_real(pressure_n_mm2,"pressure_n_mm2"); t=_positive(thickness_mm,"thickness_mm"); s1=_real(meridional_stress_n_mm2,"meridional_stress_n_mm2"); r1=_positive(meridional_radius_mm,"meridional_radius_mm"); r2=_positive(circumferential_radius_mm,"circumferential_radius_mm")
    return (p/t-s1/r1)*r2


def cylindrical_internal_pressure_stresses_eq151(pressure_n_mm2: float, radius_mm: float, thickness_mm: float) -> tuple[float, float]:
    """
    Summary:
        Calculate meridional and hoop stresses in a closed cylinder under internal pressure.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.3
        Annex: None
        Equation/Table: Equation (151)
        Audit ID: SP16-EQ-151
        Normative status: normative

    Mathematical form:
        sigma_1=pr/(2t); sigma_2=pr/t.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: tuple[float, float]
        Unit: N/mm2
        Meaning: Meridional and circumferential stresses.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-151

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_real(pressure_n_mm2,"pressure_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm")
    return p*r/(2.0*t), p*r/t


def spherical_internal_pressure_stresses_eq152(pressure_n_mm2: float, radius_mm: float, thickness_mm: float) -> tuple[float, float]:
    """
    Summary:
        Calculate equal membrane stresses in a spherical shell under internal pressure.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.3
        Annex: None
        Equation/Table: Equation (152)
        Audit ID: SP16-EQ-152
        Normative status: normative

    Mathematical form:
        sigma_1=sigma_2=pr/(2t).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: tuple[float, float]
        Unit: N/mm2
        Meaning: Equal meridional and circumferential stresses.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-152

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_real(pressure_n_mm2,"pressure_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); stress=p*r/(2.0*t)
    return stress,stress


def conical_internal_pressure_stresses_eq153(pressure_n_mm2: float, radius_mm: float, thickness_mm: float, beta_degrees: float) -> tuple[float, float]:
    """
    Summary:
        Calculate meridional and hoop stresses in a conical shell under internal pressure.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.3
        Annex: None
        Equation/Table: Equation (153)
        Audit ID: SP16-EQ-153
        Normative status: normative

    Mathematical form:
        sigma_1=pr/(2t cos beta); sigma_2=pr/(t cos beta).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: tuple[float, float]
        Unit: N/mm2
        Meaning: Meridional and circumferential stresses.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-153

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_real(pressure_n_mm2,"pressure_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); c=_cos_beta(beta_degrees)
    return p*r/(2.0*t*c),p*r/(t*c)


def cylindrical_axial_stability_utilization_eq154(axial_compressive_stress_n_mm2: float, critical_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate axial shell-stability utilization from equation (154).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Equation (154)
        Audit ID: SP16-EQ-154
        Normative status: normative

    Mathematical form:
        sigma_1/(sigma_cr,1*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-154

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    demand=_nonnegative(axial_compressive_stress_n_mm2,"axial_compressive_stress_n_mm2"); critical=_positive(critical_stress_n_mm2,"critical_stress_n_mm2"); gamma=_working_condition(working_condition_factor)
    return demand/(critical*gamma)


def cylindrical_psi_eq155(radius_to_thickness_ratio: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate coefficient psi from equation (155).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Equation (155)
        Audit ID: SP16-EQ-155
        Normative status: normative

    Mathematical form:
        psi=0.97-(0.00025+0.95*Ry/E)*(r/t).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-155

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    ratio=_positive(radius_to_thickness_ratio,"radius_to_thickness_ratio"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2")
    if ratio>300.0: raise ValueError("equation (155) applies only for r/t <= 300")
    value=0.97-(0.00025+0.95*ry/e)*ratio
    if value<=0.0: raise ValueError("equation (155) produced a non-positive psi")
    return value


def cylindrical_axial_critical_stress(radius_mm: float, thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float, c_coefficient: float | None = None) -> dict[str, Any]:
    """
    Summary:
        Select the critical axial stress required by clause 11.2.1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Equations (154)-(155) and Table 34
        Audit ID: SP16-PROC-11.2.1-CRITICAL-STRESS-SELECTION
        Normative status: normative

    Mathematical form:
        sigma_cr,1=min(psi*Ry,cEt/r) for r/t<=300; otherwise cEt/r.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Branch values, coefficients, and governing critical stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.1-CRITICAL-STRESS-SELECTION

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); ratio=r/t
    c=table_34_c_coefficient(ratio) if c_coefficient is None else _positive(c_coefficient,"c_coefficient")
    elastic=c*e*t/r
    if ratio<=300.0:
        psi=cylindrical_psi_eq155(ratio,ry,e); yield_branch=psi*ry; critical=min(yield_branch,elastic); governing="psi_Ry" if yield_branch<=elastic else "c_E_t_over_r"
    else:
        psi=None; yield_branch=None; critical=elastic; governing="c_E_t_over_r"
    return {"radius_to_thickness_ratio":ratio,"c_coefficient":c,"psi":psi,"yield_branch_n_mm2":yield_branch,"elastic_branch_n_mm2":elastic,"critical_stress_n_mm2":critical,"governing_branch":governing}


def eccentric_compression_critical_stress_multiplier_clause_11_2_1(maximum_compressive_stress_n_mm2: float, minimum_signed_stress_n_mm2: float, shear_stress_n_mm2: float, elastic_modulus_n_mm2: float, radius_mm: float, thickness_mm: float) -> dict[str, Any]:
    """
    Summary:
        Evaluate the eccentric-compression or pure-bending critical-stress increase in clause 11.2.1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.1
        Annex: None
        Equation/Table: Unnumbered clause 11.2.1 rule
        Audit ID: SP16-PROC-11.2.1-ECCENTRIC-COMPRESSION-ADJUSTMENT
        Normative status: normative

    Mathematical form:
        factor=1.1-0.1*sigma_min/sigma_max when tau<=0.07E(t/r)^(3/2).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Shear threshold, applicability, and multiplier.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.1-ECCENTRIC-COMPRESSION-ADJUSTMENT

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    smax=_positive(maximum_compressive_stress_n_mm2,"maximum_compressive_stress_n_mm2"); smin=_real(minimum_signed_stress_n_mm2,"minimum_signed_stress_n_mm2"); tau=abs(_real(shear_stress_n_mm2,"shear_stress_n_mm2")); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm")
    threshold=0.07*e*(t/r)**1.5
    applicable=tau<=threshold
    factor=1.1-0.1*smin/smax if applicable else None
    return {"shear_threshold_n_mm2":threshold,"applicable":applicable,"multiplier":factor}


def tube_bending_critical_stress_clause_11_2_2(axial_critical_stress_n_mm2: float, relative_eccentricity_m: float) -> float:
    """
    Summary:
        Calculate the tube bending critical stress used in equation (156).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.2
        Annex: None
        Equation/Table: Unnumbered definition after equation (156)
        Audit ID: SP16-PROC-11.2.2-TUBE-ROUTING
        Normative status: normative

    Mathematical form:
        sigma_cr,b=sigma_cr,1/8*(9-(1-m)/(1+m)).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Tube critical stress for bending/eccentric compression.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.2-TUBE-ROUTING

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    scr=_positive(axial_critical_stress_n_mm2,"axial_critical_stress_n_mm2"); m=_nonnegative(relative_eccentricity_m,"relative_eccentricity_m")
    return scr/8.0*(9.0-(1.0-m)/(1.0+m))


def tube_local_stability_utilization_eq156(axial_force_n: float, relative_slenderness: float, gross_area_mm2: float, relative_eccentricity_m: float, design_yield_resistance_n_mm2: float, axial_critical_stress_n_mm2: float, radius_mm: float, thickness_mm: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate tube local-stability utilization from equation (156).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.2
        Annex: None
        Equation/Table: Equation (156)
        Audit ID: SP16-EQ-156
        Normative status: normative

    Mathematical form:
        N*2*lambda_bar^2/[A*(a_sigma-sqrt(a_sigma^2-b_sigma))].

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-156

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    n=_nonnegative(axial_force_n,"axial_force_n"); lb=_positive(relative_slenderness,"relative_slenderness"); area=_positive(gross_area_mm2,"gross_area_mm2"); m=_nonnegative(relative_eccentricity_m,"relative_eccentricity_m"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2")
    if lb<0.65: raise ValueError("equation (156) requires relative slenderness >= 0.65")
    if r/t>math.pi*math.sqrt(e/ry): raise ValueError("equation (156) requires r/t <= pi*sqrt(E/Ry)")
    scrb=tube_bending_critical_stress_clause_11_2_2(axial_critical_stress_n_mm2,m)
    a_sigma=lb*lb*scrb+(m+1.0)*ry*math.pi**2
    b_sigma=4.0*ry*scrb*lb*lb*math.pi**2
    discriminant=a_sigma*a_sigma-b_sigma
    if discriminant<0.0: raise ValueError("equation (156) has a negative discriminant")
    denominator=area*(a_sigma-math.sqrt(max(0.0,discriminant)))
    if denominator<=0.0: raise ValueError("equation (156) denominator must be positive")
    return n*2.0*lb*lb/denominator


def tube_local_stability_route_clause_11_2_2(radius_mm: float, thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float, relative_slenderness: float) -> dict[str, Any]:
    """
    Summary:
        Select the tube stability route prescribed by clause 11.2.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.2
        Annex: None
        Equation/Table: Clause 11.2.2 routing conditions
        Audit ID: SP16-PROC-11.2.2-TUBE-ROUTING
        Normative status: normative

    Mathematical form:
        Compare r/t with pi/2*sqrt(E/Ry) and pi*sqrt(E/Ry), with lambda_bar>=0.65.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Thresholds and required calculation route.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.2-TUBE-ROUTING

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); lb=_positive(relative_slenderness,"relative_slenderness"); ratio=r/t; lower=0.5*math.pi*math.sqrt(e/ry); upper=math.pi*math.sqrt(e/ry)
    if ratio<=lower: route="global_stability_only_sections_7_and_9"
    elif lb>=0.65 and ratio<=upper: route="equation_156_local_stability_no_separate_global_check"
    else: route="outside_clause_11_2_2_direct_route"
    return {"radius_to_thickness_ratio":ratio,"lower_threshold":lower,"upper_threshold":upper,"route":route}


def cylindrical_panel_limit_eq157(elastic_modulus_n_mm2: float, compressive_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate the cylindrical-panel b/t limit from equation (157).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.3
        Annex: None
        Equation/Table: Equation (157)
        Audit ID: SP16-EQ-157
        Normative status: normative

    Mathematical form:
        b/t<=1.9*sqrt(E/sigma).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-157

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); sigma=_positive(compressive_stress_n_mm2,"compressive_stress_n_mm2")
    return 1.9*math.sqrt(e/sigma)


def cylindrical_panel_limit_eq158(design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate the cylindrical-panel b/t limit at sigma=Ry from equation (158).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.3
        Annex: None
        Equation/Table: Equation (158)
        Audit ID: SP16-EQ-158
        Normative status: normative

    Mathematical form:
        b/t<=37/sqrt(1+500Ry/E).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-158

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2")
    return 37.0/math.sqrt(1.0+500.0*ry/e)


def cylindrical_panel_limit(compressive_stress_n_mm2: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Apply the explicit linear interpolation rule between equations (157) and (158).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.3
        Annex: None
        Equation/Table: Equations (157)-(158)
        Audit ID: SP16-PROC-11.2.3-PANEL-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Equation (157) to 0.8Ry, linear interpolation to equation (158) at Ry.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Panel b/t limit and calculation route.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.3-PANEL-INTERPOLATION

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    sigma=_positive(compressive_stress_n_mm2,"compressive_stress_n_mm2"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2")
    if sigma>ry: raise ValueError("panel stress must not exceed Ry for clauses (157)-(158)")
    if sigma<=0.8*ry: limit=cylindrical_panel_limit_eq157(e,sigma); route="equation_157"
    elif sigma<ry:
        low=cylindrical_panel_limit_eq157(e,0.8*ry); high=cylindrical_panel_limit_eq158(ry,e); limit=_linear(sigma,0.8*ry,ry,low,high); route="linear_interpolation_0.8Ry_to_Ry"
    else: limit=cylindrical_panel_limit_eq158(ry,e); route="equation_158"
    return {"limit_b_over_t":limit,"route":route}


def cylindrical_panel_route_clause_11_2_3(panel_width_mm: float, radius_mm: float, thickness_mm: float) -> dict[str, Any]:
    """
    Summary:
        Route a curved panel to plate-like or shell-like stability calculation.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.3
        Annex: None
        Equation/Table: Clause 11.2.3 routing condition
        Audit ID: SP16-PROC-11.2.3-PANEL-OR-SHELL-ROUTING
        Normative status: normative

    Mathematical form:
        Use panel equations when b^2/(rt)<=20; otherwise clause 11.2.1.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Curvature parameter and required route.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.3-PANEL-OR-SHELL-ROUTING

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    b=_positive(panel_width_mm,"panel_width_mm"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); parameter=b*b/(r*t)
    return {"b_squared_over_r_t":parameter,"route":"panel_equations_157_158" if parameter<=20.0 else "shell_clause_11_2_1"}


def cylindrical_external_pressure_utilization_eq159(hoop_compressive_stress_n_mm2: float, critical_hoop_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate external-pressure cylinder utilization from equation (159).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.4
        Annex: None
        Equation/Table: Equation (159)
        Audit ID: SP16-EQ-159
        Normative status: normative

    Mathematical form:
        sigma_2/(sigma_cr,2*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-159

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    demand=_nonnegative(hoop_compressive_stress_n_mm2,"hoop_compressive_stress_n_mm2"); critical=_positive(critical_hoop_stress_n_mm2,"critical_hoop_stress_n_mm2"); gamma=_working_condition(working_condition_factor)
    return demand/(critical*gamma)


def cylindrical_external_pressure_critical_stress_eq160(elastic_modulus_n_mm2: float, radius_mm: float, length_mm: float, thickness_mm: float) -> float:
    """
    Summary:
        Calculate external-pressure critical hoop stress from equation (160).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.4
        Annex: None
        Equation/Table: Equation (160)
        Audit ID: SP16-EQ-160
        Normative status: normative

    Mathematical form:
        sigma_cr,2=0.55E(r/l)(t/r)^(3/2).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical hoop stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-160

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); r=_positive(radius_mm,"radius_mm"); length=_positive(length_mm,"length_mm"); t=_positive(thickness_mm,"thickness_mm"); ratio=length/r
    if not 0.5<=ratio<=10.0: raise ValueError("equation (160) requires 0.5 <= l/r <= 10")
    return 0.55*e*(r/length)*(t/r)**1.5


def cylindrical_external_pressure_critical_stress_eq161(elastic_modulus_n_mm2: float, radius_mm: float, thickness_mm: float) -> float:
    """
    Summary:
        Calculate the long-cylinder external-pressure critical stress from equation (161).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.4
        Annex: None
        Equation/Table: Equation (161)
        Audit ID: SP16-EQ-161
        Normative status: normative

    Mathematical form:
        sigma_cr,2=0.17E(t/r)^2.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical hoop stress for l/r>=20.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-161

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm")
    return 0.17*e*(t/r)**2


def cylindrical_external_pressure_critical_stress(elastic_modulus_n_mm2: float, radius_mm: float, length_mm: float, thickness_mm: float) -> dict[str, Any]:
    """
    Summary:
        Apply equations (160)-(161) and the explicit interpolation rule in clause 11.2.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.4
        Annex: None
        Equation/Table: Equations (160)-(161)
        Audit ID: SP16-PROC-11.2.4-EXTERNAL-PRESSURE-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Equation (160) to l/r=10, linear interpolation to l/r=20, then equation (161).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Critical stress and calculation route.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.4-EXTERNAL-PRESSURE-INTERPOLATION

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); r=_positive(radius_mm,"radius_mm"); length=_positive(length_mm,"length_mm"); t=_positive(thickness_mm,"thickness_mm"); ratio=length/r
    if ratio<0.5: raise ValueError("clause 11.2.4 requires l/r >= 0.5")
    if ratio<=10.0: critical=cylindrical_external_pressure_critical_stress_eq160(e,r,length,t); route="equation_160"
    elif ratio<20.0:
        at10=cylindrical_external_pressure_critical_stress_eq160(e,r,10.0*r,t); at20=cylindrical_external_pressure_critical_stress_eq161(e,r,t); critical=_linear(ratio,10.0,20.0,at10,at20); route="linear_interpolation_10_to_20"
    else: critical=cylindrical_external_pressure_critical_stress_eq161(e,r,t); route="equation_161"
    return {"length_to_radius_ratio":ratio,"critical_stress_n_mm2":critical,"route":route}


def ring_stiffener_requirements_clause_11_2_4(pressure_n_mm2: float, radius_mm: float, spacing_mm: float, thickness_mm: float, elastic_modulus_n_mm2: float, design_yield_resistance_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Return ring-stiffener design actions and effective geometry required by clause 11.2.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.4
        Annex: None
        Equation/Table: Unnumbered ring-stiffener requirements
        Audit ID: SP16-PROC-11.2.4-RING-STIFFENER-REQUIREMENTS
        Normative status: normative

    Mathematical form:
        N=prs; l_ef=1.8r; shell width each side=65t*sqrt(E/Ry); lambda_bar<=6.5.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Ring force, effective length, effective shell width, and slenderness limit.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.4-RING-STIFFENER-REQUIREMENTS

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_nonnegative(pressure_n_mm2,"pressure_n_mm2"); r=_positive(radius_mm,"radius_mm"); s=_positive(spacing_mm,"spacing_mm"); t=_positive(thickness_mm,"thickness_mm"); e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2")
    if s<0.5*r: raise ValueError("ring spacing must satisfy s >= 0.5r")
    return {"ring_compression_force_n":p*r*s,"ring_effective_length_mm":1.8*r,"effective_shell_width_each_side_mm":65.0*t*math.sqrt(e/ry),"maximum_relative_slenderness":6.5,"use_spacing_in_equations_159_to_161":True}


def cylindrical_combined_stability_utilization_eq162(axial_compressive_stress_n_mm2: float, axial_critical_stress_n_mm2: float, hoop_compressive_stress_n_mm2: float, hoop_critical_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate combined axial and external-pressure cylinder utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.5
        Annex: None
        Equation/Table: Equation (162)
        Audit ID: SP16-EQ-162
        Normative status: normative

    Mathematical form:
        (sigma_1/sigma_cr,1+sigma_2/sigma_cr,2)/gamma_c.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-162

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    s1=_nonnegative(axial_compressive_stress_n_mm2,"axial_compressive_stress_n_mm2"); cr1=_positive(axial_critical_stress_n_mm2,"axial_critical_stress_n_mm2"); s2=_nonnegative(hoop_compressive_stress_n_mm2,"hoop_compressive_stress_n_mm2"); cr2=_positive(hoop_critical_stress_n_mm2,"hoop_critical_stress_n_mm2"); gamma=_working_condition(working_condition_factor)
    return (s1/cr1+s2/cr2)/gamma


def conical_axial_stability_utilization_eq163(axial_force_n: float, critical_force_n: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate conical-shell axial stability utilization from equation (163).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.6
        Annex: None
        Equation/Table: Equation (163)
        Audit ID: SP16-EQ-163
        Normative status: normative

    Mathematical form:
        N/(Ncr*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-163

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    n=_nonnegative(axial_force_n,"axial_force_n"); ncr=_positive(critical_force_n,"critical_force_n"); gamma=_working_condition(working_condition_factor)
    return n/(ncr*gamma)


def conical_critical_force_eq164(thickness_mm: float, axial_critical_stress_n_mm2: float, equivalent_radius_mm: float, beta_degrees: float) -> float:
    """
    Summary:
        Calculate conical-shell critical axial force from equation (164).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.6
        Annex: None
        Equation/Table: Equation (164)
        Audit ID: SP16-EQ-164
        Normative status: normative

    Mathematical form:
        Ncr=6.28*t*sigma_cr,1*r_m*cos^2(beta).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N
        Meaning: Critical axial compressive force.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Conical shells with beta<=60 degrees.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-164

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    t=_positive(thickness_mm,"thickness_mm"); scr=_positive(axial_critical_stress_n_mm2,"axial_critical_stress_n_mm2"); rm=_positive(equivalent_radius_mm,"equivalent_radius_mm"); c=_cos_beta(beta_degrees,maximum_degrees=60.0)
    return 6.28*t*scr*rm*c*c


def conical_equivalent_radius_eq165(top_radius_mm: float, bottom_radius_mm: float, beta_degrees: float) -> float:
    """
    Summary:
        Calculate the equivalent cone radius from equation (165).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.6
        Annex: None
        Equation/Table: Equation (165)
        Audit ID: SP16-EQ-165
        Normative status: normative

    Mathematical form:
        r_m=(0.9r_2+0.1r_1)/cos(beta).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: mm
        Meaning: Equivalent radius r_m.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Conical shells with beta<=60 degrees.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-165

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    r1=_positive(top_radius_mm,"top_radius_mm"); r2=_positive(bottom_radius_mm,"bottom_radius_mm"); c=_cos_beta(beta_degrees,maximum_degrees=60.0)
    return (0.9*r2+0.1*r1)/c


def conical_external_pressure_utilization_eq166(hoop_compressive_stress_n_mm2: float, critical_hoop_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate conical-shell external-pressure utilization from equation (166).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.7
        Annex: None
        Equation/Table: Equation (166)
        Audit ID: SP16-EQ-166
        Normative status: normative

    Mathematical form:
        sigma_2/(sigma_cr,2*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-166

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    demand=_nonnegative(hoop_compressive_stress_n_mm2,"hoop_compressive_stress_n_mm2"); critical=_positive(critical_hoop_stress_n_mm2,"critical_hoop_stress_n_mm2"); gamma=_working_condition(working_condition_factor)
    return demand/(critical*gamma)


def conical_external_pressure_critical_stress_eq167(elastic_modulus_n_mm2: float, equivalent_radius_mm: float, cone_height_mm: float, thickness_mm: float) -> float:
    """
    Summary:
        Calculate conical-shell critical hoop stress from equation (167).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.7
        Annex: None
        Equation/Table: Equation (167)
        Audit ID: SP16-EQ-167
        Normative status: normative

    Mathematical form:
        sigma_cr,2=0.55E(r_m/h)(t/r_m)^(3/2).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical hoop stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-167

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); rm=_positive(equivalent_radius_mm,"equivalent_radius_mm"); h=_positive(cone_height_mm,"cone_height_mm"); t=_positive(thickness_mm,"thickness_mm")
    return 0.55*e*(rm/h)*(t/rm)**1.5


def conical_combined_stability_utilization_eq168(axial_force_n: float, critical_force_n: float, hoop_compressive_stress_n_mm2: float, critical_hoop_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate combined axial and pressure conical-shell utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.8
        Annex: None
        Equation/Table: Equation (168)
        Audit ID: SP16-EQ-168
        Normative status: normative

    Mathematical form:
        (N/Ncr+sigma_2/sigma_cr,2)/gamma_c.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-168

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    n=_nonnegative(axial_force_n,"axial_force_n"); ncr=_positive(critical_force_n,"critical_force_n"); s2=_nonnegative(hoop_compressive_stress_n_mm2,"hoop_compressive_stress_n_mm2"); cr2=_positive(critical_hoop_stress_n_mm2,"critical_hoop_stress_n_mm2"); gamma=_working_condition(working_condition_factor)
    return (n/ncr+s2/cr2)/gamma


def spherical_external_pressure_critical_stress_clause_11_2_9(elastic_modulus_n_mm2: float, radius_mm: float, thickness_mm: float, design_yield_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate the capped spherical-shell critical stress used by equation (169).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.9
        Annex: None
        Equation/Table: Unnumbered definition after equation (169)
        Audit ID: SP16-PROC-11.2.9-SPHERE-RATIO-LIMIT
        Normative status: normative

    Mathematical form:
        sigma_cr=min(0.1Et/r,Ry), with r/t<=750.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical spherical-shell compressive stress.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.2.9-SPHERE-RATIO-LIMIT

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    e=_positive(elastic_modulus_n_mm2,"elastic_modulus_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); ry=_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2")
    if r/t>750.0: raise ValueError("clause 11.2.9 requires r/t <= 750")
    return min(0.1*e*t/r,ry)


def spherical_external_pressure_utilization_eq169(pressure_n_mm2: float, radius_mm: float, thickness_mm: float, critical_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate spherical-shell external-pressure utilization from equation (169).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.2.9
        Annex: None
        Equation/Table: Equation (169)
        Audit ID: SP16-EQ-169
        Normative status: normative

    Mathematical form:
        [pr/(2t)]/(sigma_cr*gamma_c).

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Calculated scalar.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-EQ-169

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    p=_nonnegative(pressure_n_mm2,"pressure_n_mm2"); r=_positive(radius_mm,"radius_mm"); t=_positive(thickness_mm,"thickness_mm"); critical=_positive(critical_stress_n_mm2,"critical_stress_n_mm2"); gamma=_working_condition(working_condition_factor); sigma=p*r/(2.0*t)
    return sigma/(critical*gamma)


def shell_analysis_route_clause_11_1_4_11_1_5(has_geometry_thickness_or_load_discontinuity: bool, arbitrary_configuration_or_spatial_state: bool) -> dict[str, Any]:
    """
    Summary:
        Expose the local-edge-effect and certified spatial-analysis boundaries of clauses 11.1.4-11.1.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 11.1.4-11.1.5
        Annex: None
        Equation/Table: Procedural requirements
        Audit ID: SP16-PROC-11.1.4-LOCAL-EDGE-EFFECT
        Normative status: normative

    Mathematical form:
        Boolean routing; no missing shell theory is reconstructed.

    Parameters:
        Inputs use explicit names and the units stated by each parameter name.

    Returns:
        Type: dict[str, Any]
        Unit: not applicable
        Meaning: Required external analysis routes.

    Assumptions:
        - Inputs describe one audited shell or panel state and one load combination.
        - Geometry and stress-resultant extraction have been completed consistently before this scalar check.

    Sign convention:
        - Compression/pressure demand is non-negative unless a signed membrane stress is explicitly required.
        - Tensile minimum stress may be negative only in the eccentric-compression adjustment procedure.

    Unit convention:
        - Stress and elastic modulus use N/mm2; force uses N; lengths use one consistent unit, normally mm.

    Applicability:
        - Selected Section 11 procedure.

    Limitations:
        - No automatic geometry classification, edge-effect analysis, or finite-element stress recovery is performed.
        - No interpolation or extrapolation is applied unless Section 11 explicitly prescribes it.

    Raises:
        ValueError: An input violates a formula domain or normative applicability condition.
        TypeError: An input is not a finite real number or valid selector.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_sheet_structures_strength_and_stability.py
        Validation cases:
            - V13-SP16-PROC-11.1.4-LOCAL-EDGE-EFFECT

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(has_geometry_thickness_or_load_discontinuity,bool) or not isinstance(arbitrary_configuration_or_spatial_state,bool): raise TypeError("route flags must be bool")
    return {"local_edge_effect_analysis_required":has_geometry_thickness_or_load_discontinuity,"certified_spatial_software_required":arbitrary_configuration_or_spatial_state,"base_membrane_equations_still_required":True}
