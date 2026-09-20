"""Local stability of bending-member webs and compressed flanges under SP 16.13330.2017."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLES = json.loads((_DATA_DIR / "tables_14_to_19_bending_local_stability.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-8.5.1-PRELIMINARY-WEB-ROUTING",
    "SP16-PROC-8.5.5-DOUBLE-CHECK-ROUTING",
    "SP16-PROC-8.5.6-ASYMMETRIC-COMPRESSED-FLANGE-ROUTING",
    "SP16-PROC-8.5.9-TRANSVERSE-STIFFENER-ROUTING",
    "SP16-PROC-8.5.9-TRANSVERSE-STIFFENER-DIMENSIONS",
    "SP16-PROC-8.5.10-LOAD-STIFFENER-SECTION",
    "SP16-PROC-8.5.11-LONGITUDINAL-STIFFENER-ROUTING",
    "SP16-PROC-8.5.12-SPLIT-WEB-PLATES",
    "SP16-PROC-8.5.13-INTERMEDIATE-STIFFENERS",
    "SP16-PROC-8.5.14-ASYMMETRIC-SPLIT-WEB",
    "SP16-PROC-8.5.15-STIFFENER-INERTIA",
    "SP16-PROC-8.5.16-FLEXIBLE-WEB-ROUTING",
    "SP16-PROC-8.5.17-SUPPORT-STIFFENER",
    "SP16-PROC-8.5.20-EDGE-STIFFENING-MODIFIER",
    "SP16-PROC-TABLE-14-LOOKUP",
    "SP16-PROC-TABLE-15-LOOKUP",
    "SP16-PROC-TABLE-16-LOOKUP",
    "SP16-PROC-TABLE-17-LOOKUP",
    "SP16-PROC-TABLE-18-LOOKUP",
    "SP16-PROC-TABLE-19-INTERPOLATION",
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


def _signed(value: float, name: str) -> float:
    return _real(value, name)


def _doc() -> None:
    # Private marker only; public functions contain literal structured docstrings for AST auditing.
    return None


def bending_normal_stress_eq78(moment_n_mm: float, distance_from_neutral_axis_mm: float, major_inertia_mm4: float) -> float:
    """
    Summary:
        Calculate the bending normal stress at the checked web edge.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.2
        Annex: None
        Equation/Table: Equation (78)
        Audit ID: SP16-EQ-078
        Normative status: normative

    Mathematical form:
        sigma = M*y/Ix.

    Parameters:
        moment_n_mm, distance_from_neutral_axis_mm, major_inertia_mm4:
            Type: float
            Unit: N*mm, mm, mm4
            Meaning: Section moment, checked-edge distance, and major-axis inertia.
            Valid range: moment signed; distance and inertia positive
            Source: structural analysis and section properties

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Signed normal stress.

    Assumptions:
        - Elastic section stress distribution is used.

    Sign convention:
        - Compression is supplied with a positive moment-distance product for stability checks.

    Unit convention:
        - N and mm are used without silent conversion.

    Applicability:
        - Clause 8.5.2 web-panel checks.

    Limitations:
        - Averaging of M over the governing panel segment is external to this scalar function.

    Raises:
        ValueError: A geometric denominator is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> bending_normal_stress_eq78(1e8, 300, 2e8)
        150.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-078

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _signed(moment_n_mm, "moment_n_mm") * _signed(distance_from_neutral_axis_mm, "distance_from_neutral_axis_mm") / _positive(major_inertia_mm4, "major_inertia_mm4")


def average_web_shear_stress_eq79(shear_force_n: float, web_thickness_mm: float, full_web_height_mm: float) -> float:
    """
    Summary:
        Calculate the average web shear stress.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.2
        Annex: None
        Equation/Table: Equation (79)
        Audit ID: SP16-EQ-079
        Normative status: normative

    Mathematical form:
        tau = Q/(tw*hw).

    Parameters:
        shear_force_n, web_thickness_mm, full_web_height_mm:
            Type: float
            Unit: N, mm, mm
            Meaning: Panel shear force, web thickness, and full web height.
            Valid range: shear magnitude non-negative; dimensions positive
            Source: structural analysis and geometry

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Average shear stress.

    Assumptions:
        - Equation (79) average stress is used, not a detailed shear-flow distribution.

    Sign convention:
        - Shear is a non-negative magnitude.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Clause 8.5.2.

    Limitations:
        - Panel averaging is external.

    Raises:
        ValueError: Force is negative or dimensions are non-positive.
        TypeError: An input is not real.

    Examples:
        >>> average_web_shear_stress_eq79(200000, 10, 1000)
        20.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-079

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(shear_force_n, "shear_force_n") / (_positive(web_thickness_mm, "web_thickness_mm") * _positive(full_web_height_mm, "full_web_height_mm"))


def symmetric_web_buckling_utilization_eq80(sigma_n_mm2: float, sigma_local_n_mm2: float, tau_n_mm2: float, sigma_cr_n_mm2: float, sigma_local_cr_n_mm2: float, tau_cr_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate the interaction utilization for a symmetric class-1 beam web panel.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.3
        Annex: None
        Equation/Table: Equation (80)
        Audit ID: SP16-EQ-080
        Normative status: normative

    Mathematical form:
        eta = sqrt((sigma/sigma_cr + sigma_loc/sigma_loc_cr)^2 + (tau/tau_cr)^2)/gamma_c.

    Parameters:
        sigma_n_mm2, sigma_local_n_mm2, tau_n_mm2, sigma_cr_n_mm2, sigma_local_cr_n_mm2, tau_cr_n_mm2, working_condition_factor:
            Type: float
            Unit: N/mm2 and dimensionless
            Meaning: Applied and critical stresses and gamma_c.
            Valid range: applied magnitudes non-negative; critical stresses and gamma_c positive
            Source: equations (78)-(83)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization; pass when not above one.

    Assumptions:
        - The panel and loading satisfy clauses 8.5.3-8.5.6.

    Sign convention:
        - Compression, local compression, and shear are magnitudes.

    Unit convention:
        - All stresses use N/mm2.

    Applicability:
        - Symmetric class-1 I-section web panels with transverse stiffeners.

    Limitations:
        - Routing for the second check of 8.5.5 is a separate procedure.

    Raises:
        ValueError: A critical value is non-positive or applied magnitude is negative.
        TypeError: An input is not real.

    Examples:
        >>> symmetric_web_buckling_utilization_eq80(50, 10, 20, 200, 100, 80, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-080

    Implementation notes:
        - The outer 1/gamma_c factor follows the printed equation.
        - Defaults must be explicit in the input configuration.
    """
    normal = _nonnegative(sigma_n_mm2, "sigma_n_mm2") / _positive(sigma_cr_n_mm2, "sigma_cr_n_mm2") + _nonnegative(sigma_local_n_mm2, "sigma_local_n_mm2") / _positive(sigma_local_cr_n_mm2, "sigma_local_cr_n_mm2")
    shear = _nonnegative(tau_n_mm2, "tau_n_mm2") / _positive(tau_cr_n_mm2, "tau_cr_n_mm2")
    return math.sqrt(normal * normal + shear * shear) / _positive(working_condition_factor, "working_condition_factor")


def critical_normal_web_stress_eq81(c_cr: float, design_yield_resistance_n_mm2: float, web_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the critical normal stress of a web panel.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.3
        Annex: None
        Equation/Table: Equation (81)
        Audit ID: SP16-EQ-081
        Normative status: normative

    Mathematical form:
        sigma_cr = c_cr*Ry/lambda_w_bar^2.

    Parameters:
        c_cr, design_yield_resistance_n_mm2, web_relative_slenderness:
            Type: float
            Unit: dimensionless, N/mm2, dimensionless
            Meaning: Buckling coefficient, design resistance, and relative web slenderness.
            Valid range: positive
            Source: Tables 12 or 16 and geometry

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical normal stress.

    Assumptions:
        - c_cr is selected by the applicable table route.

    Sign convention:
        - Returned compression resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Equations (80), (85), and split-panel procedures.

    Limitations:
        - Table routing is not inferred from geometry.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> critical_normal_web_stress_eq81(30, 355, 3)
        1183.3333333333333

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-081

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _positive(web_relative_slenderness, "web_relative_slenderness")
    return _positive(c_cr, "c_cr") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / (slenderness * slenderness)


def critical_local_web_stress_eq82(c1: float, c2: float, design_yield_resistance_n_mm2: float, web_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the critical local compression stress beneath a concentrated load.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.3 and 8.5.5
        Annex: None
        Equation/Table: Equation (82)
        Audit ID: SP16-EQ-082
        Normative status: normative

    Mathematical form:
        sigma_loc_cr = c1*c2*Ry/lambda_w_bar^2.

    Parameters:
        c1, c2, design_yield_resistance_n_mm2, web_relative_slenderness:
            Type: float
            Unit: dimensionless, dimensionless, N/mm2, dimensionless
            Meaning: Table 14 and 15 coefficients, resistance, and web slenderness.
            Valid range: positive
            Source: Tables 14-15 and geometry

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical local stress.

    Assumptions:
        - Coefficients correspond to the same panel route.

    Sign convention:
        - Returned resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Concentrated-load web checks.

    Limitations:
        - Table interpolation is not invented.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> critical_local_web_stress_eq82(28.5, 1.56, 355, 3) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-082

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _positive(web_relative_slenderness, "web_relative_slenderness")
    return _positive(c1, "c1") * _positive(c2, "c2") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / (slenderness * slenderness)


def critical_web_shear_stress_eq83(panel_aspect_ratio_mu: float, design_shear_resistance_n_mm2: float, plate_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the critical shear stress of a rectangular web panel.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.3
        Annex: None
        Equation/Table: Equation (83)
        Audit ID: SP16-EQ-083
        Normative status: normative

    Mathematical form:
        tau_cr = 10.3*(1+0.76/mu^2)*Rs/lambda_d_bar^2.

    Parameters:
        panel_aspect_ratio_mu, design_shear_resistance_n_mm2, plate_relative_slenderness:
            Type: float
            Unit: dimensionless, N/mm2, dimensionless
            Meaning: Greater-to-smaller panel side ratio, Rs, and smaller-side relative slenderness.
            Valid range: mu >= 1; resistance and slenderness positive
            Source: panel geometry and clause 6.1

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical shear stress.

    Assumptions:
        - mu is the greater side divided by the smaller side.

    Sign convention:
        - Returned resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Web panels under shear.

    Limitations:
        - Plate slenderness must be calculated for the smaller panel side.

    Raises:
        ValueError: mu is below one or another input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> critical_web_shear_stress_eq83(2, 205, 3) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-083

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    mu = _positive(panel_aspect_ratio_mu, "panel_aspect_ratio_mu")
    if mu < 1.0:
        raise ValueError("panel_aspect_ratio_mu must be at least 1")
    slenderness = _positive(plate_relative_slenderness, "plate_relative_slenderness")
    return 10.3 * (1.0 + 0.76 / (mu * mu)) * _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2") / (slenderness * slenderness)


def flange_restraint_parameter_eq84(beta_factor: float, flange_width_mm: float, effective_web_height_mm: float, flange_thickness_mm: float, web_thickness_mm: float) -> float:
    """
    Summary:
        Calculate the flange-restraint parameter delta.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.4
        Annex: None
        Equation/Table: Equation (84)
        Audit ID: SP16-EQ-084
        Normative status: normative

    Mathematical form:
        delta = beta*(bf/hef)*(tf/tw)^3.

    Parameters:
        beta_factor, flange_width_mm, effective_web_height_mm, flange_thickness_mm, web_thickness_mm:
            Type: float
            Unit: dimensionless and mm
            Meaning: Table 13 beta and section dimensions.
            Valid range: positive; beta may be mathematical infinity only outside this finite scalar API
            Source: Table 13 and geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Delta parameter for Tables 12 and 15.

    Assumptions:
        - The applicable flange is selected by clause 8.5.4 or 8.5.5.

    Sign convention:
        - All dimensions are positive.

    Unit convention:
        - All lengths use the same unit.

    Applicability:
        - Finite-beta Table 13 cases.

    Limitations:
        - Infinite-beta cases are represented by the routing result rather than this finite formula.

    Raises:
        ValueError: An input is non-positive or non-finite.
        TypeError: An input is not real.

    Examples:
        >>> flange_restraint_parameter_eq84(0.8, 300, 1000, 20, 10)
        1.92

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_78_84
        Validation cases:
            - BLS-EQ-084

    Implementation notes:
        - Infinity entries in Table 13 are handled by table_13 logic from the previous release.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(beta_factor, "beta_factor") * (_positive(flange_width_mm, "flange_width_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")) * (_positive(flange_thickness_mm, "flange_thickness_mm") / _positive(web_thickness_mm, "web_thickness_mm")) ** 3


def asymmetric_tension_flange_web_utilization_eq85(sigma_1_n_mm2: float, sigma_2_n_mm2: float, tau_n_mm2: float, sigma_cr_n_mm2: float, tau_cr_n_mm2: float, c_cr: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate web stability utilization for an asymmetric I-beam with the larger tension flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.7
        Annex: None
        Equation/Table: Equation (85)
        Audit ID: SP16-EQ-085
        Normative status: normative

    Mathematical form:
        alpha=(sigma1-sigma2)/sigma1; beta=(sigma_cr/sigma1)*(tau/tau_cr); eta=0.5*sigma1*(2-alpha+sqrt(alpha^2+4*beta^2))/(sigma_cr*gamma_c).

    Parameters:
        sigma_1_n_mm2, sigma_2_n_mm2, tau_n_mm2, sigma_cr_n_mm2, tau_cr_n_mm2, c_cr, working_condition_factor:
            Type: float
            Unit: N/mm2 and dimensionless
            Meaning: Compression-edge stress, opposite signed edge stress, shear, critical stresses, Table 17 coefficient, and gamma_c.
            Valid range: sigma1, critical stresses, c_cr, gamma_c positive; tau non-negative; sigma2 signed
            Source: equations (78), (79), (81), (83), Table 17

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (85) utilization.

    Assumptions:
        - Local stress is absent.

    Sign convention:
        - sigma1 is positive compression and sigma2 may be negative tension.

    Unit convention:
        - All stresses use N/mm2.

    Applicability:
        - Clause 8.5.7 geometry and loading.

    Limitations:
        - c_cr is checked for positivity but alpha-to-table consistency remains a routing responsibility.

    Raises:
        ValueError: A required positive value is non-positive or shear is negative.
        TypeError: An input is not real.

    Examples:
        >>> asymmetric_tension_flange_web_utilization_eq85(200, -100, 30, 300, 100, 20, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_85_88
        Validation cases:
            - BLS-EQ-085

    Implementation notes:
        - c_cr is an explicit traced input from Table 17.
        - Defaults must be explicit in the input configuration.
    """
    sigma1 = _positive(sigma_1_n_mm2, "sigma_1_n_mm2")
    sigma2 = _signed(sigma_2_n_mm2, "sigma_2_n_mm2")
    sigma_cr = _positive(sigma_cr_n_mm2, "sigma_cr_n_mm2")
    alpha = (sigma1 - sigma2) / sigma1
    beta = (sigma_cr / sigma1) * (_nonnegative(tau_n_mm2, "tau_n_mm2") / _positive(tau_cr_n_mm2, "tau_cr_n_mm2"))
    _positive(c_cr, "c_cr")
    return 0.5 * sigma1 * (2.0 - alpha + math.sqrt(alpha * alpha + 4.0 * beta * beta)) / (sigma_cr * _positive(working_condition_factor, "working_condition_factor"))


def class_2_3_symmetric_web_utilization_eq86(moment_n_mm: float, design_yield_resistance_n_mm2: float, working_condition_factor: float, effective_web_height_mm: float, web_thickness_mm: float, flange_to_web_area_ratio: float, flange_resistance_ratio_r: float, alpha_coefficient: float) -> float:
    """
    Summary:
        Calculate web stability utilization for class-2 or class-3 symmetric I or box beams.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.8(a)
        Annex: None
        Equation/Table: Equation (86)
        Audit ID: SP16-EQ-086
        Normative status: normative

    Mathematical form:
        eta = M/[Ry*gamma_c*hef^2*tw*(r*alpha_f+alpha)].

    Parameters:
        moment_n_mm, design_yield_resistance_n_mm2, working_condition_factor, effective_web_height_mm, web_thickness_mm, flange_to_web_area_ratio, flange_resistance_ratio_r, alpha_coefficient:
            Type: float
            Unit: N*mm, N/mm2, dimensionless, mm, mm, dimensionless
            Meaning: Moment, resistance, gamma_c, geometry, area ratio, resistance ratio, and Table 18 alpha.
            Valid range: moment non-negative; all denominator terms positive or non-negative as physically applicable
            Source: structural analysis, clause 8.4.5, Table 18

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization.

    Assumptions:
        - Local stress is zero and linked clause requirements are satisfied.

    Sign convention:
        - Moment is a non-negative magnitude.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Doubly symmetric I and box sections.

    Limitations:
        - Section classification and area-ratio definition are external.

    Raises:
        ValueError: A denominator input is invalid.
        TypeError: An input is not real.

    Examples:
        >>> class_2_3_symmetric_web_utilization_eq86(1e9, 355, 1, 1000, 10, 0.5, 1, 0.2) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_85_88
        Validation cases:
            - BLS-EQ-086

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    factor = _nonnegative(flange_resistance_ratio_r, "flange_resistance_ratio_r") * _nonnegative(flange_to_web_area_ratio, "flange_to_web_area_ratio") + _positive(alpha_coefficient, "alpha_coefficient")
    denominator = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor") * _positive(effective_web_height_mm, "effective_web_height_mm") ** 2 * _positive(web_thickness_mm, "web_thickness_mm") * factor
    return _nonnegative(moment_n_mm, "moment_n_mm") / denominator


def compressed_web_zone_height_eq88(web_area_mm2: float, web_thickness_mm: float, tension_flange_area_mm2: float, tension_flange_stress_n_mm2: float, compression_flange_area_mm2: float, compression_flange_stress_n_mm2: float, web_design_yield_resistance_n_mm2: float, shear_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate the compressed-zone height of an asymmetric web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.8(b)
        Annex: None
        Equation/Table: Equation (88)
        Audit ID: SP16-EQ-088
        Normative status: normative

    Mathematical form:
        h1=Aw/(2tw)+(Af2*sigma2-Af1*sigma1)/(2tw*sqrt(Ryw^2-3*tau^2)).

    Parameters:
        web_area_mm2, web_thickness_mm, tension_flange_area_mm2, tension_flange_stress_n_mm2, compression_flange_area_mm2, compression_flange_stress_n_mm2, web_design_yield_resistance_n_mm2, shear_stress_n_mm2:
            Type: float
            Unit: mm2, mm, N/mm2
            Meaning: Section areas, stresses, web resistance, and shear stress.
            Valid range: areas and thickness positive; stresses non-negative; Ryw^2>3*tau^2
            Source: section analysis

    Returns:
        Type: float
        Unit: mm
        Meaning: Compressed web-zone height h1.

    Assumptions:
        - Flange stresses are capped according to clause 8.5.8 before calling when required.

    Sign convention:
        - sigma1 and sigma2 are positive flange-stress magnitudes.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Asymmetric I-sections with the larger compression flange.

    Limitations:
        - Physical bounds against full web height are checked by the caller.

    Raises:
        ValueError: The square-root domain or a positive input is invalid.
        TypeError: An input is not real.

    Examples:
        >>> compressed_web_zone_height_eq88(10000, 10, 4000, 100, 5000, 150, 355, 50) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_85_88
        Validation cases:
            - BLS-EQ-088

    Implementation notes:
        - This function must not silently cap flange stresses.
        - Defaults must be explicit in the input configuration.
    """
    ry = _positive(web_design_yield_resistance_n_mm2, "web_design_yield_resistance_n_mm2")
    tau = _nonnegative(shear_stress_n_mm2, "shear_stress_n_mm2")
    rad = ry * ry - 3.0 * tau * tau
    if rad <= 0.0:
        raise ValueError("web_design_yield_resistance_n_mm2^2 must exceed 3*shear_stress_n_mm2^2")
    tw = _positive(web_thickness_mm, "web_thickness_mm")
    return _positive(web_area_mm2, "web_area_mm2") / (2.0 * tw) + (_positive(tension_flange_area_mm2, "tension_flange_area_mm2") * _nonnegative(tension_flange_stress_n_mm2, "tension_flange_stress_n_mm2") - _positive(compression_flange_area_mm2, "compression_flange_area_mm2") * _nonnegative(compression_flange_stress_n_mm2, "compression_flange_stress_n_mm2")) / (2.0 * tw * math.sqrt(rad))


def class_2_3_asymmetric_web_utilization_eq87(moment_n_mm: float, compression_flange_stress_n_mm2: float, compression_flange_area_mm2: float, compressed_zone_height_mm: float, tension_flange_stress_n_mm2: float, tension_flange_area_mm2: float, full_web_height_mm: float, web_thickness_mm: float, alpha_coefficient: float, web_design_yield_resistance_n_mm2: float, shear_stress_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate class-2 or class-3 asymmetric web stability utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.8(b)
        Annex: None
        Equation/Table: Equation (87)
        Audit ID: SP16-EQ-087
        Normative status: normative

    Mathematical form:
        eta=M/{[sigma1*Af1*h1+sigma2*Af2*(hw-h1)+4*h1^2*tw*alpha*Ryw+hw*tw*(hw-2*h1)*sqrt(Ryw^2-3*tau^2)/2]*gamma_c}.

    Parameters:
        moment_n_mm, compression_flange_stress_n_mm2, compression_flange_area_mm2, compressed_zone_height_mm, tension_flange_stress_n_mm2, tension_flange_area_mm2, full_web_height_mm, web_thickness_mm, alpha_coefficient, web_design_yield_resistance_n_mm2, shear_stress_n_mm2, working_condition_factor:
            Type: float
            Unit: N*mm, N/mm2, mm2, mm, dimensionless
            Meaning: Equation (87) actions, stresses, geometry, coefficient, resistance, and gamma_c.
            Valid range: moment and stresses non-negative; dimensions, areas, resistance and gamma_c positive; h1 within hw
            Source: structural and section analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization.

    Assumptions:
        - M and Q are evaluated in the same section.

    Sign convention:
        - Flange stresses are positive magnitudes.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Clause 8.5.8(b).

    Limitations:
        - Stress caps required by the clause are not silently applied.

    Raises:
        ValueError: A domain or geometric condition is invalid.
        TypeError: An input is not real.

    Examples:
        >>> class_2_3_asymmetric_web_utilization_eq87(1e9, 200, 5000, 400, 100, 4000, 1000, 10, 0.2, 355, 50, 1) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_85_88
        Validation cases:
            - BLS-EQ-087

    Implementation notes:
        - The printed half-factor applies to the final web term.
        - Defaults must be explicit in the input configuration.
    """
    hw = _positive(full_web_height_mm, "full_web_height_mm")
    h1 = _positive(compressed_zone_height_mm, "compressed_zone_height_mm")
    if h1 >= hw:
        raise ValueError("compressed_zone_height_mm must be below full_web_height_mm")
    ry = _positive(web_design_yield_resistance_n_mm2, "web_design_yield_resistance_n_mm2")
    tau = _nonnegative(shear_stress_n_mm2, "shear_stress_n_mm2")
    rad = ry * ry - 3.0 * tau * tau
    if rad <= 0.0:
        raise ValueError("web resistance domain invalid")
    tw = _positive(web_thickness_mm, "web_thickness_mm")
    capacity = (
        _nonnegative(compression_flange_stress_n_mm2, "compression_flange_stress_n_mm2") * _positive(compression_flange_area_mm2, "compression_flange_area_mm2") * h1
        + _nonnegative(tension_flange_stress_n_mm2, "tension_flange_stress_n_mm2") * _positive(tension_flange_area_mm2, "tension_flange_area_mm2") * (hw - h1)
        + 4.0 * h1 * h1 * tw * _positive(alpha_coefficient, "alpha_coefficient") * ry
        + hw * tw * (hw - 2.0 * h1) * math.sqrt(rad) / 2.0
    ) * _positive(working_condition_factor, "working_condition_factor")
    if capacity <= 0.0:
        raise ValueError("equation (87) capacity must be positive")
    return _nonnegative(moment_n_mm, "moment_n_mm") / capacity


def upper_plate_utilization_eq89(sigma_n_mm2: float, sigma_local_n_mm2: float, tau_n_mm2: float, sigma_cr_1_n_mm2: float, sigma_local_cr_1_n_mm2: float, tau_cr_1_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate utilization of plate 1 between compression flange and longitudinal stiffener.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(a)
        Annex: None
        Equation/Table: Equation (89)
        Audit ID: SP16-EQ-089
        Normative status: normative

    Mathematical form:
        eta=[sigma/sigma_cr1+sigma_loc/sigma_loc_cr1+(tau/tau_cr1)^2]/gamma_c.

    Parameters:
        sigma_n_mm2, sigma_local_n_mm2, tau_n_mm2, sigma_cr_1_n_mm2, sigma_local_cr_1_n_mm2, tau_cr_1_n_mm2, working_condition_factor:
            Type: float
            Unit: N/mm2 and dimensionless
            Meaning: Applied and critical plate-1 stresses and gamma_c.
            Valid range: applied magnitudes non-negative; denominators positive
            Source: clauses 8.5.2 and 8.5.12

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (89) utilization.

    Assumptions:
        - Plate dimensions correspond to plate 1.

    Sign convention:
        - Applied stresses are positive magnitudes.

    Unit convention:
        - Stresses use N/mm2.

    Applicability:
        - Symmetric I-beam web with paired longitudinal stiffener.

    Limitations:
        - Intermediate stiffener substitution is external.

    Raises:
        ValueError: A value is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> upper_plate_utilization_eq89(50, 10, 20, 200, 100, 80, 1) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-089

    Implementation notes:
        - Only the shear ratio is squared in equation (89).
        - Defaults must be explicit in the input configuration.
    """
    return (_nonnegative(sigma_n_mm2, "sigma_n_mm2") / _positive(sigma_cr_1_n_mm2, "sigma_cr_1_n_mm2") + _nonnegative(sigma_local_n_mm2, "sigma_local_n_mm2") / _positive(sigma_local_cr_1_n_mm2, "sigma_local_cr_1_n_mm2") + (_nonnegative(tau_n_mm2, "tau_n_mm2") / _positive(tau_cr_1_n_mm2, "tau_cr_1_n_mm2")) ** 2) / _positive(working_condition_factor, "working_condition_factor")


def upper_plate_critical_normal_no_local_eq90(design_yield_resistance_n_mm2: float, plate_1_relative_slenderness: float, plate_1_height_mm: float, effective_web_height_mm: float) -> float:
    """
    Summary:
        Calculate plate-1 critical normal stress when local stress is zero.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(a)
        Annex: None
        Equation/Table: Equation (90)
        Audit ID: SP16-EQ-090
        Normative status: normative

    Mathematical form:
        sigma_cr1=4.76*Ry/[(1-h1/hef)*lambda1_bar^2].

    Parameters:
        design_yield_resistance_n_mm2, plate_1_relative_slenderness, plate_1_height_mm, effective_web_height_mm:
            Type: float
            Unit: N/mm2, dimensionless, mm, mm
            Meaning: Resistance, plate slenderness, and heights.
            Valid range: positive and h1<hef
            Source: geometry and material

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical stress.

    Assumptions:
        - sigma_loc equals zero.

    Sign convention:
        - Resistance is positive.

    Unit convention:
        - Consistent length units.

    Applicability:
        - Equation (89) no-local-stress branch.

    Limitations:
        - Slenderness calculation is separate.

    Raises:
        ValueError: Geometry or a denominator is invalid.
        TypeError: An input is not real.

    Examples:
        >>> upper_plate_critical_normal_no_local_eq90(355, 2, 200, 1000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-090

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(plate_1_height_mm, "plate_1_height_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")
    if ratio >= 1.0:
        raise ValueError("plate_1_height_mm/effective_web_height_mm must be below one")
    lam = _positive(plate_1_relative_slenderness, "plate_1_relative_slenderness")
    return 4.76 * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / ((1.0 - ratio) * lam * lam)


def upper_plate_critical_normal_with_local_eq91(psi: float, design_yield_resistance_n_mm2: float, plate_1_relative_slenderness: float, plate_1_height_mm: float, effective_web_height_mm: float) -> float:
    """
    Summary:
        Calculate plate-1 critical normal stress when local stress is present.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(a)
        Annex: None
        Equation/Table: Equation (91)
        Audit ID: SP16-EQ-091
        Normative status: normative

    Mathematical form:
        sigma_cr1=1.19*psi*Ry/[(1-h1/hef)*lambda1_bar^2].

    Parameters:
        psi, design_yield_resistance_n_mm2, plate_1_relative_slenderness, plate_1_height_mm, effective_web_height_mm:
            Type: float
            Unit: dimensionless, N/mm2, dimensionless, mm, mm
            Meaning: Equation (93) psi, resistance, slenderness, and geometry.
            Valid range: positive and h1<hef
            Source: equation (93) and geometry

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical stress.

    Assumptions:
        - Local stress is non-zero and mu1 is capped at two before psi is evaluated.

    Sign convention:
        - Resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Equation (89) local-stress branch.

    Limitations:
        - Applicability routing is separate.

    Raises:
        ValueError: Geometry or an input is invalid.
        TypeError: An input is not real.

    Examples:
        >>> upper_plate_critical_normal_with_local_eq91(4, 355, 2, 200, 1000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-091

    Implementation notes:
        - This function must not silently cap mu1 because psi is already an input.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(plate_1_height_mm, "plate_1_height_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")
    if ratio >= 1.0:
        raise ValueError("plate height ratio must be below one")
    lam = _positive(plate_1_relative_slenderness, "plate_1_relative_slenderness")
    return 1.19 * _positive(psi, "psi") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / ((1.0 - ratio) * lam * lam)


def upper_plate_critical_local_eq92(psi: float, panel_aspect_ratio_mu_1: float, design_yield_resistance_n_mm2: float, web_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the critical local stress of plate 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(a)
        Annex: None
        Equation/Table: Equation (92)
        Audit ID: SP16-EQ-092
        Normative status: normative

    Mathematical form:
        sigma_loc_cr1=psi*(1.24+0.476*mu1)*Ry/lambda_w_bar^2.

    Parameters:
        psi, panel_aspect_ratio_mu_1, design_yield_resistance_n_mm2, web_relative_slenderness:
            Type: float
            Unit: dimensionless, dimensionless, N/mm2, dimensionless
            Meaning: Equation (93) parameters, resistance, and slenderness.
            Valid range: positive; mu1 not above two for this branch
            Source: equation (93)

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical local stress.

    Assumptions:
        - mu1 is the panel length divided by plate-1 height.

    Sign convention:
        - Resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Plate 1 with local stress.

    Limitations:
        - The caller selects actual or intermediate-stiffener panel length.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> upper_plate_critical_local_eq92(4, 2, 355, 3) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-092

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    mu = _positive(panel_aspect_ratio_mu_1, "panel_aspect_ratio_mu_1")
    if mu > 2.0:
        raise ValueError("panel_aspect_ratio_mu_1 must not exceed 2 for equation (92)")
    lam = _positive(web_relative_slenderness, "web_relative_slenderness")
    return _positive(psi, "psi") * (1.24 + 0.476 * mu) * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / (lam * lam)


def upper_plate_psi_and_slenderness_eq93(panel_length_mm: float, plate_1_height_mm: float, web_thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> dict[str, float]:
    """
    Summary:
        Calculate mu1, psi, and the equation (93) web slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(a)
        Annex: None
        Equation/Table: Equation (93)
        Audit ID: SP16-EQ-093
        Normative status: normative

    Mathematical form:
        mu1=min(a/h1,2); psi=(mu1+1/mu1)^2; lambda_w_bar=(a/tw)*sqrt(Ry/E).

    Parameters:
        panel_length_mm, plate_1_height_mm, web_thickness_mm, design_yield_resistance_n_mm2, elastic_modulus_n_mm2:
            Type: float
            Unit: mm, mm, mm, N/mm2, N/mm2
            Meaning: Plate-1 panel geometry and material properties.
            Valid range: positive
            Source: geometry and material

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: mu1_raw, mu1_used, psi, and lambda_w_bar.

    Assumptions:
        - The printed cap mu1=2 is applied when a/h1 exceeds two.

    Sign convention:
        - All quantities are positive.

    Unit convention:
        - Length units cancel consistently.

    Applicability:
        - Equations (91)-(93).

    Limitations:
        - The returned lambda uses panel length a as printed.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> upper_plate_psi_and_slenderness_eq93(400, 200, 10, 355, 206000)['mu1_used']
        2.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-093

    Implementation notes:
        - The cap is explicit in the returned bundle.
        - Defaults must be explicit in the input configuration.
    """
    a = _positive(panel_length_mm, "panel_length_mm")
    h1 = _positive(plate_1_height_mm, "plate_1_height_mm")
    mu_raw = a / h1
    mu = min(mu_raw, 2.0)
    psi = (mu + 1.0 / mu) ** 2
    slenderness = (a / _positive(web_thickness_mm, "web_thickness_mm")) * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))
    return {"mu1_raw": mu_raw, "mu1_used": mu, "psi": psi, "web_relative_slenderness": slenderness}


def lower_plate_utilization_eq94(sigma_n_mm2: float, sigma_local_2_n_mm2: float, tau_n_mm2: float, plate_1_height_mm: float, effective_web_height_mm: float, sigma_cr_2_n_mm2: float, sigma_local_cr_2_n_mm2: float, tau_cr_2_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate utilization of plate 2 between the longitudinal stiffener and tension flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(b)
        Annex: None
        Equation/Table: Equation (94)
        Audit ID: SP16-EQ-094
        Normative status: normative

    Mathematical form:
        eta=sqrt([sigma*(1-2h1/hef)/sigma_cr2+sigma_loc2/sigma_loc_cr2]^2+(tau/tau_cr2)^2)/gamma_c.

    Parameters:
        sigma_n_mm2, sigma_local_2_n_mm2, tau_n_mm2, plate_1_height_mm, effective_web_height_mm, sigma_cr_2_n_mm2, sigma_local_cr_2_n_mm2, tau_cr_2_n_mm2, working_condition_factor:
            Type: float
            Unit: N/mm2, mm, dimensionless
            Meaning: Applied stresses, split geometry, critical stresses, and gamma_c.
            Valid range: applied magnitudes non-negative; geometry and critical values positive
            Source: clause 8.5.12(b)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (94) utilization.

    Assumptions:
        - Local stress for plate 2 is selected per the loaded flange.

    Sign convention:
        - Applied stresses are magnitudes.

    Unit convention:
        - Stress units are consistent.

    Applicability:
        - Plate 2 of a split web panel.

    Limitations:
        - Asymmetric-section substitutions of 8.5.14 are external.

    Raises:
        ValueError: An input or geometry is invalid.
        TypeError: An input is not real.

    Examples:
        >>> lower_plate_utilization_eq94(50, 5, 20, 200, 1000, 200, 100, 80, 1) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-094

    Implementation notes:
        - The normal/local sum is squared as printed.
        - Defaults must be explicit in the input configuration.
    """
    factor = 1.0 - 2.0 * _positive(plate_1_height_mm, "plate_1_height_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")
    normal = _nonnegative(sigma_n_mm2, "sigma_n_mm2") * factor / _positive(sigma_cr_2_n_mm2, "sigma_cr_2_n_mm2") + _nonnegative(sigma_local_2_n_mm2, "sigma_local_2_n_mm2") / _positive(sigma_local_cr_2_n_mm2, "sigma_local_cr_2_n_mm2")
    shear = _nonnegative(tau_n_mm2, "tau_n_mm2") / _positive(tau_cr_2_n_mm2, "tau_cr_2_n_mm2")
    return math.sqrt(normal * normal + shear * shear) / _positive(working_condition_factor, "working_condition_factor")


def lower_plate_critical_normal_eq95(design_yield_resistance_n_mm2: float, lower_plate_relative_slenderness: float, plate_1_height_mm: float, effective_web_height_mm: float) -> float:
    """
    Summary:
        Calculate critical normal stress of plate 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(b)
        Annex: None
        Equation/Table: Equation (95)
        Audit ID: SP16-EQ-095
        Normative status: normative

    Mathematical form:
        sigma_cr2=5.43*Ry/[(0.5-h1/hef)^2*lambda_w_bar^2].

    Parameters:
        design_yield_resistance_n_mm2, lower_plate_relative_slenderness, plate_1_height_mm, effective_web_height_mm:
            Type: float
            Unit: N/mm2, dimensionless, mm, mm
            Meaning: Resistance, plate-2 slenderness, and split geometry.
            Valid range: positive and h1/hef not equal 0.5
            Source: geometry and material

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Critical normal stress.

    Assumptions:
        - Symmetric-section equation (95) is used without 8.5.14 substitution.

    Sign convention:
        - Resistance is positive.

    Unit convention:
        - Stress is N/mm2.

    Applicability:
        - Plate 2 of the symmetric split web.

    Limitations:
        - The singular h1/hef=0.5 geometry is rejected.

    Raises:
        ValueError: An input or geometry is invalid.
        TypeError: An input is not real.

    Examples:
        >>> lower_plate_critical_normal_eq95(355, 2, 200, 1000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-095

    Implementation notes:
        - This function must not silently apply the asymmetric-section replacement.
        - Defaults must be explicit in the input configuration.
    """
    denominator_factor = 0.5 - _positive(plate_1_height_mm, "plate_1_height_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")
    if abs(denominator_factor) < 1e-15:
        raise ValueError("0.5-h1/hef must not be zero")
    lam = _positive(lower_plate_relative_slenderness, "lower_plate_relative_slenderness")
    return 5.43 * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / (denominator_factor * denominator_factor * lam * lam)


def lower_plate_relative_slenderness_eq96(lower_plate_height_mm: float, web_thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate the relative slenderness of plate 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.12(b)
        Annex: None
        Equation/Table: Equation (96)
        Audit ID: SP16-EQ-096
        Normative status: normative

    Mathematical form:
        lambda_w_bar=(h2/tw)*sqrt(Ry/E).

    Parameters:
        lower_plate_height_mm, web_thickness_mm, design_yield_resistance_n_mm2, elastic_modulus_n_mm2:
            Type: float
            Unit: mm, mm, N/mm2, N/mm2
            Meaning: Plate-2 height, web thickness, resistance, and elastic modulus.
            Valid range: positive
            Source: geometry and material

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative plate slenderness.

    Assumptions:
        - h2 is measured per Figure 9.

    Sign convention:
        - All inputs are positive.

    Unit convention:
        - Length and stress ratios are dimensionless.

    Applicability:
        - Equations (94)-(96).

    Limitations:
        - Geometry extraction is external.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> lower_plate_relative_slenderness_eq96(800, 10, 355, 206000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_89_96
        Validation cases:
            - BLS-EQ-096

    Implementation notes:
        - This function must not silently convert units.
        - Defaults must be explicit in the input configuration.
    """
    return (_positive(lower_plate_height_mm, "lower_plate_height_mm") / _positive(web_thickness_mm, "web_thickness_mm")) * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))


def flange_outstand_limit_eq97(flange_design_yield_resistance_n_mm2: float, compressed_flange_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate the limiting relative slenderness of an I-section flange outstand.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.18
        Annex: None
        Equation/Table: Equation (97)
        Audit ID: SP16-EQ-097
        Normative status: normative

    Mathematical form:
        lambda_uf_bar=0.5*sqrt(Ryf/sigma_c).

    Parameters:
        flange_design_yield_resistance_n_mm2, compressed_flange_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Flange design resistance and compressive stress.
            Valid range: positive
            Source: clause 8.5.18

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative slenderness.

    Assumptions:
        - The stress has been capped at Ryf when required.

    Sign convention:
        - Compression stress is a positive magnitude.

    Unit convention:
        - Stress ratio is dimensionless.

    Applicability:
        - Class-1 homogeneous and applicable bimetal beams.

    Limitations:
        - Stress calculation formulas are external to this scalar function.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> flange_outstand_limit_eq97(355, 200) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_97_100
        Validation cases:
            - BLS-EQ-097

    Implementation notes:
        - This function must not silently cap stress.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5 * math.sqrt(_positive(flange_design_yield_resistance_n_mm2, "flange_design_yield_resistance_n_mm2") / _positive(compressed_flange_stress_n_mm2, "compressed_flange_stress_n_mm2"))


def box_flange_plate_limit_eq98(flange_design_yield_resistance_n_mm2: float, compressed_flange_stress_n_mm2: float) -> float:
    """
    Summary:
        Calculate the limiting relative slenderness of a box-section flange plate.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.18
        Annex: None
        Equation/Table: Equation (98)
        Audit ID: SP16-EQ-098
        Normative status: normative

    Mathematical form:
        lambda_uf1_bar=1.5*sqrt(Ryf/sigma_c).

    Parameters:
        flange_design_yield_resistance_n_mm2, compressed_flange_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Flange resistance and compression stress.
            Valid range: positive
            Source: clause 8.5.18

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative slenderness.

    Assumptions:
        - Applicable linked clauses are satisfied.

    Sign convention:
        - Compression is positive.

    Unit convention:
        - Stress ratio is dimensionless.

    Applicability:
        - Box-section flange plates.

    Limitations:
        - Actual plate slenderness is calculated separately.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> box_flange_plate_limit_eq98(355, 200) > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_97_100
        Validation cases:
            - BLS-EQ-098

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return 1.5 * math.sqrt(_positive(flange_design_yield_resistance_n_mm2, "flange_design_yield_resistance_n_mm2") / _positive(compressed_flange_stress_n_mm2, "compressed_flange_stress_n_mm2"))


def class_2_3_flange_outstand_limit_eq99(web_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the class-2 or class-3 I-section flange-outstand limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.19
        Annex: None
        Equation/Table: Equation (99)
        Audit ID: SP16-EQ-099
        Normative status: normative

    Mathematical form:
        lambda_uf_bar=0.17+0.06*clamp(lambda_w_bar,2.2,5.5).

    Parameters:
        web_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Web relative slenderness.
            Valid range: positive; clamped by the clause to 2.2-5.5
            Source: clause 8.5.19

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting outstand slenderness.

    Assumptions:
        - Class-2 or class-3 homogeneous beam route applies.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - I-section flange outstand without edge stiffening or fold.

    Limitations:
        - Edge-stiffening multiplier is separate.

    Raises:
        ValueError: Slenderness is non-positive.
        TypeError: Input is not real.

    Examples:
        >>> class_2_3_flange_outstand_limit_eq99(3)
        0.35

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_97_100
        Validation cases:
            - BLS-EQ-099

    Implementation notes:
        - The printed lower and upper substitutions are applied explicitly.
        - Defaults must be explicit in the input configuration.
    """
    lam = min(5.5, max(2.2, _positive(web_relative_slenderness, "web_relative_slenderness")))
    return 0.17 + 0.06 * lam


def class_2_3_box_flange_limit_eq100(web_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the class-2 or class-3 box-section flange-plate limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.19
        Annex: None
        Equation/Table: Equation (100)
        Audit ID: SP16-EQ-100
        Normative status: normative

    Mathematical form:
        lambda_uf1_bar=0.675+0.15*clamp(lambda_w_bar,2.2,5.5).

    Parameters:
        web_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Web relative slenderness.
            Valid range: positive; clamped to 2.2-5.5
            Source: clause 8.5.19

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting box-flange slenderness.

    Assumptions:
        - The class-2 or class-3 homogeneous route applies.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Box-section flange plates.

    Limitations:
        - Edge-stiffening provisions are separate.

    Raises:
        ValueError: Slenderness is non-positive.
        TypeError: Input is not real.

    Examples:
        >>> class_2_3_box_flange_limit_eq100(3)
        1.125

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_equations_97_100
        Validation cases:
            - BLS-EQ-100

    Implementation notes:
        - The printed lower and upper substitutions are applied explicitly.
        - Defaults must be explicit in the input configuration.
    """
    lam = min(5.5, max(2.2, _positive(web_relative_slenderness, "web_relative_slenderness")))
    return 0.675 + 0.15 * lam


# Table lookups and clause procedures use the same structured audit contract.
def table_14_c1(rho: float, panel_ratio: float) -> float:
    """
    Summary:
        Look up coefficient c1 from Table 14 at an exact printed node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.5
        Annex: None
        Equation/Table: Table 14
        Audit ID: SP16-PROC-TABLE-14-LOOKUP
        Normative status: normative

    Mathematical form:
        Exact two-dimensional table lookup with the printed >=2.0 terminal column.

    Parameters:
        rho, panel_ratio:
            Type: float
            Unit: dimensionless
            Meaning: rho=1.04*l_ef/h_ef and a/h_ef or a1/h_ef.
            Valid range: exact printed rho node; exact ratio node or ratio >=2
            Source: clause 8.5.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c1.

    Assumptions:
        - No interpolation rule is stated in the table.

    Sign convention:
        - Inputs are positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (82).

    Limitations:
        - Non-node interpolation is rejected.

    Raises:
        ValueError: A requested node is unavailable.
        TypeError: Input is not real.

    Examples:
        >>> table_14_c1(0.1, 1.0)
        28.5

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_tables_14_to_18
        Validation cases:
            - BLS-T14

    Implementation notes:
        - Terminal >= values are applied only where printed.
        - Defaults must be explicit in the input configuration.
    """
    return _exact_2d("table_14", rho, panel_ratio, cap_x=2.0)


def table_15_c2(delta: float, panel_ratio: float) -> float:
    """
    Summary:
        Look up coefficient c2 from Table 15 at an exact printed node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.5
        Annex: None
        Equation/Table: Table 15
        Audit ID: SP16-PROC-TABLE-15-LOOKUP
        Normative status: normative

    Mathematical form:
        Exact lookup with delta <=1, delta >=30, and ratio >=1.6 terminal rules.

    Parameters:
        delta, panel_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Equation (84) delta and panel ratio.
            Valid range: positive; exact interior nodes or printed terminal regions
            Source: clause 8.5.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c2.

    Assumptions:
        - No interpolation is inferred.

    Sign convention:
        - Inputs are positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (82).

    Limitations:
        - Interior non-node values are rejected.

    Raises:
        ValueError: A node is unavailable.
        TypeError: Input is not real.

    Examples:
        >>> table_15_c2(1, 1.0)
        1.56

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_tables_14_to_18
        Validation cases:
            - BLS-T15

    Implementation notes:
        - Table terminal inequalities are honored.
        - Defaults must be explicit in the input configuration.
    """
    d = _positive(delta, "delta")
    d_key = 1.0 if d <= 1.0 else 30.0 if d >= 30.0 else d
    return _exact_2d("table_15", d_key, panel_ratio, cap_x=1.6)


def table_16_c_cr(panel_ratio: float, table_12_value_when_not_above_0_8: float) -> float:
    """
    Summary:
        Select c_cr from Table 16 or retain the Table 12 value for ratios not above 0.8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.5(b)
        Annex: None
        Equation/Table: Table 16
        Audit ID: SP16-PROC-TABLE-16-LOOKUP
        Normative status: normative

    Mathematical form:
        c_cr=Table12 when ratio<=0.8; otherwise exact Table16 node, with >=2 terminal value.

    Parameters:
        panel_ratio, table_12_value_when_not_above_0_8:
            Type: float
            Unit: dimensionless
            Meaning: a/h_ef or a/(2h_c), and applicable Table 12 c_cr.
            Valid range: positive
            Source: clause 8.5.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c_cr.

    Assumptions:
        - The supplied Table 12 value was independently selected correctly.

    Sign convention:
        - Positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Second check of 8.5.5 and 8.5.6.

    Limitations:
        - Interior interpolation is not stated and is rejected.

    Raises:
        ValueError: A node is unavailable.
        TypeError: Input is not real.

    Examples:
        >>> table_16_c_cr(0.8, 34.6)
        34.6

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_tables_14_to_18
        Validation cases:
            - BLS-T16

    Implementation notes:
        - This function does not recalculate Table 12.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(panel_ratio, "panel_ratio")
    if ratio <= 0.8:
        return _positive(table_12_value_when_not_above_0_8, "table_12_value_when_not_above_0_8")
    x = 2.0 if ratio >= 2.0 else ratio
    nodes = _TABLES["table_16"]["ratio_nodes"]
    values = _TABLES["table_16"]["c_cr"]
    return _exact_1d(nodes, values, x, "panel_ratio")


def table_17_c_cr(alpha: float) -> float:
    """
    Summary:
        Look up c_cr from Table 17 at an exact printed alpha node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.7
        Annex: None
        Equation/Table: Table 17
        Audit ID: SP16-PROC-TABLE-17-LOOKUP
        Normative status: normative

    Mathematical form:
        Exact one-dimensional table lookup.

    Parameters:
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Stress-gradient parameter of equation (85).
            Valid range: exact printed nodes 1.0-2.0
            Source: equation (85)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c_cr.

    Assumptions:
        - No interpolation rule is stated.

    Sign convention:
        - Positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (85).

    Limitations:
        - Non-node values are rejected.

    Raises:
        ValueError: Alpha is not a printed node.
        TypeError: Input is not real.

    Examples:
        >>> table_17_c_cr(1.4)
        15.5

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_tables_14_to_18
        Validation cases:
            - BLS-T17

    Implementation notes:
        - This function must not invent interpolation.
        - Defaults must be explicit in the input configuration.
    """
    row = _TABLES["table_17"]
    return _exact_1d(row["alpha_nodes"], row["c_cr"], _positive(alpha, "alpha"), "alpha")


def table_18_alpha(shear_ratio_tau_over_rsw: float, web_relative_slenderness: float) -> float:
    """
    Summary:
        Look up alpha from Table 18 at an exact printed node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.8
        Annex: None
        Equation/Table: Table 18
        Audit ID: SP16-PROC-TABLE-18-LOOKUP
        Normative status: normative

    Mathematical form:
        Exact two-dimensional lookup by tau/Rsw and lambda_w_bar.

    Parameters:
        shear_ratio_tau_over_rsw, web_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Shear ratio and web relative slenderness.
            Valid range: exact printed nodes
            Source: clause 8.5.8

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: alpha coefficient.

    Assumptions:
        - No interpolation rule is printed.

    Sign convention:
        - Ratios are non-negative.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equations (86)-(88) and clause 8.5.18 bimetal stress expression.

    Limitations:
        - Non-node values are rejected.

    Raises:
        ValueError: A requested node is unavailable.
        TypeError: Input is not real.

    Examples:
        >>> table_18_alpha(0.5, 3.0)
        0.197

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_tables_14_to_18
        Validation cases:
            - BLS-T18

    Implementation notes:
        - This function must not invent interpolation.
        - Defaults must be explicit in the input configuration.
    """
    return _exact_2d("table_18", _nonnegative(shear_ratio_tau_over_rsw, "shear_ratio_tau_over_rsw"), _positive(web_relative_slenderness, "web_relative_slenderness"))


def table_19_stiffener_inertias(plate_1_height_ratio: float, panel_length_mm: float, effective_web_height_mm: float, web_thickness_mm: float) -> dict[str, float | None]:
    """
    Summary:
        Calculate required transverse and longitudinal stiffener inertias from Table 19.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.15
        Annex: None
        Equation/Table: Table 19
        Audit ID: SP16-PROC-TABLE-19-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Table formulas at h1/hef=0.20,0.25,0.30; linear interpolation of required Ir1 between nodes.

    Parameters:
        plate_1_height_ratio, panel_length_mm, effective_web_height_mm, web_thickness_mm:
            Type: float
            Unit: dimensionless, mm, mm, mm
            Meaning: h1/hef, panel length a, effective web height, and web thickness.
            Valid range: ratio 0.20-0.30; dimensions positive
            Source: Table 19

    Returns:
        Type: dict[str, float | None]
        Unit: mm4
        Meaning: Required transverse inertia, required longitudinal inertia, and printed min/max bounds where present.

    Assumptions:
        - Linear interpolation applies only to required Ir1 as stated in the note.

    Sign convention:
        - Inertias are positive.

    Unit convention:
        - All lengths must use mm to return mm4.

    Applicability:
        - Paired longitudinal and transverse stiffeners under 8.5.15.

    Limitations:
        - Min/max bounds are returned only at exact printed nodes because their interpolation is not stated.

    Raises:
        ValueError: Ratio or dimensions are outside the table domain.
        TypeError: Input is not real.

    Examples:
        >>> table_19_stiffener_inertias(0.25, 1000, 1000, 10)['transverse_required_mm4']
        3000000.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-T19

    Implementation notes:
        - The table note explicitly authorizes linear interpolation only for required longitudinal inertia.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _real(plate_1_height_ratio, "plate_1_height_ratio")
    if ratio < 0.20 or ratio > 0.30:
        raise ValueError("plate_1_height_ratio must be within 0.20 to 0.30")
    a = _positive(panel_length_mm, "panel_length_mm")
    h = _positive(effective_web_height_mm, "effective_web_height_mm")
    tw = _positive(web_thickness_mm, "web_thickness_mm")
    transverse = 3.0 * h * tw ** 3
    def req(r: float) -> float:
        if abs(r - 0.20) < 1e-12:
            return (2.5 - 0.5 * a / h) * a * a * tw ** 3 / h
        if abs(r - 0.25) < 1e-12:
            return (1.5 - 0.4 * a / h) * a * a * tw ** 3 / h
        return 1.5 * h * tw ** 3
    nodes = [0.20, 0.25, 0.30]
    if ratio in nodes:
        required = req(ratio)
    elif ratio < 0.25:
        required = _linear(ratio, 0.20, 0.25, req(0.20), req(0.25))
    else:
        required = _linear(ratio, 0.25, 0.30, req(0.25), req(0.30))
    min_i = None
    max_i = None
    if abs(ratio - 0.20) < 1e-12:
        min_i, max_i = 1.5 * h * tw ** 3, 7.0 * h * tw ** 3
    elif abs(ratio - 0.25) < 1e-12:
        min_i, max_i = 1.5 * h * tw ** 3, 8.5 * h * tw ** 3
    return {"transverse_required_mm4": transverse, "longitudinal_required_mm4": required, "longitudinal_minimum_mm4": min_i, "longitudinal_maximum_mm4": max_i}


def preliminary_web_check_exemption_8_5_1(web_relative_slenderness: float, local_stress_present: bool, double_sided_flange_welds: bool) -> dict[str, Any]:
    """
    Summary:
        Evaluate the clause 8.5.1 preliminary threshold for omitting a detailed class-1 web check.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.1
        Annex: None
        Equation/Table: Threshold procedure
        Audit ID: SP16-PROC-8.5.1-PRELIMINARY-WEB-ROUTING
        Normative status: normative

    Mathematical form:
        Limit=3.5 without local stress and double-sided welds; 3.2 without local stress and one-sided welds; 2.5 with local stress and double-sided welds.

    Parameters:
        web_relative_slenderness, local_stress_present, double_sided_flange_welds:
            Type: float, bool, bool
            Unit: dimensionless
            Meaning: Web slenderness and construction/loading flags.
            Valid range: slenderness positive
            Source: clause 8.5.1

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Limit and whether the detailed web check may be omitted on this criterion.

    Assumptions:
        - Other clause 8.5.1 conditions are satisfied.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Class-1 beams.

    Limitations:
        - The standard does not state a threshold for local stress with one-sided flange welds; that combination is rejected.

    Raises:
        ValueError: The combination is not specified or slenderness is invalid.
        TypeError: Input is invalid.

    Examples:
        >>> preliminary_web_check_exemption_8_5_1(3.0, False, True)['detailed_check_may_be_omitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-851

    Implementation notes:
        - No unspecified threshold is inferred.
        - Defaults must be explicit in the input configuration.
    """
    lam = _positive(web_relative_slenderness, "web_relative_slenderness")
    if local_stress_present:
        if not double_sided_flange_welds:
            raise ValueError("clause 8.5.1 gives no threshold for local stress with one-sided flange welds")
        limit = 2.5
    else:
        limit = 3.5 if double_sided_flange_welds else 3.2
    return {"limit": limit, "detailed_check_may_be_omitted": lam <= limit}


def transverse_stiffener_requirements_8_5_9(section_class: int, web_relative_slenderness: float, moving_flange_load_present: bool, plastic_deformation_region: bool, effective_web_height_mm: float, class_1_extended_spacing_conditions_met: bool = False) -> dict[str, Any]:
    """
    Summary:
        Determine whether transverse stiffeners are required and the maximum spacing.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.9
        Annex: None
        Equation/Table: Stiffener routing
        Audit ID: SP16-PROC-8.5.9-TRANSVERSE-STIFFENER-ROUTING
        Normative status: normative

    Mathematical form:
        Class-1 threshold 3.2 or 2.2; class 2-3 always in plastic zones; spacing 2hef for lambda>=3.2, otherwise 2.5hef, optionally 3hef under stated class-1 conditions.

    Parameters:
        section_class, web_relative_slenderness, moving_flange_load_present, plastic_deformation_region, effective_web_height_mm, class_1_extended_spacing_conditions_met:
            Type: int, float, bool, bool, float, bool
            Unit: dimensionless and mm
            Meaning: Classification, loading/region flags, geometry, and verified extension condition.
            Valid range: class 1-3; positive slenderness and height
            Source: clause 8.5.9

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Requirement flag and maximum spacing.

    Assumptions:
        - The extension flag represents all linked conditions, including formula (71).

    Sign convention:
        - Positive geometry.

    Unit convention:
        - Spacing uses the same length unit as hef.

    Applicability:
        - Beam webs.

    Limitations:
        - Fixed concentrated-load and support locations must still receive stiffeners.

    Raises:
        ValueError: Class or dimensions are invalid.
        TypeError: Input is invalid.

    Examples:
        >>> transverse_stiffener_requirements_8_5_9(1, 3.3, False, False, 1000)['required']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-859

    Implementation notes:
        - The function reports general spacing only.
        - Defaults must be explicit in the input configuration.
    """
    if section_class not in {1, 2, 3}:
        raise ValueError("section_class must be 1, 2, or 3")
    lam = _positive(web_relative_slenderness, "web_relative_slenderness")
    h = _positive(effective_web_height_mm, "effective_web_height_mm")
    if section_class == 1:
        threshold = 2.2 if moving_flange_load_present else 3.2
        required = lam > threshold
    else:
        threshold = 2.2 if moving_flange_load_present else 3.2
        required = True if plastic_deformation_region else lam > threshold
    spacing_factor = 2.0 if lam >= 3.2 else 2.5
    if section_class == 1 and class_1_extended_spacing_conditions_met:
        spacing_factor = 3.0
    return {"required": required, "threshold": threshold, "maximum_spacing_mm": spacing_factor * h, "spacing_factor": spacing_factor}


def transverse_stiffener_dimensions_8_5_9(full_web_height_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float, one_sided: bool) -> dict[str, float]:
    """
    Summary:
        Calculate minimum projecting width and thickness of a transverse web stiffener.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.9
        Annex: None
        Equation/Table: Dimensional procedure
        Audit ID: SP16-PROC-8.5.9-TRANSVERSE-STIFFENER-DIMENSIONS
        Normative status: normative

    Mathematical form:
        br>=hw/30+25 paired or hw/24+40 one-sided; tr>=2br*sqrt(Ry/E).

    Parameters:
        full_web_height_mm, design_yield_resistance_n_mm2, elastic_modulus_n_mm2, one_sided:
            Type: float, float, float, bool
            Unit: mm, N/mm2, N/mm2, dimensionless
            Meaning: Full web height, material properties, and stiffener arrangement.
            Valid range: positive
            Source: clause 8.5.9

    Returns:
        Type: dict[str, float]
        Unit: mm
        Meaning: Minimum projecting width and thickness.

    Assumptions:
        - Width is the projecting part of one stiffener component.

    Sign convention:
        - Positive dimensions.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Webs strengthened only by transverse stiffeners.

    Limitations:
        - One-sided inertia equivalence to a paired stiffener is not computed.

    Raises:
        ValueError: An input is non-positive.
        TypeError: Input is invalid.

    Examples:
        >>> transverse_stiffener_dimensions_8_5_9(1000, 355, 206000, False)['minimum_projection_mm'] > 0
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-859-DIM

    Implementation notes:
        - This function must not silently apply fabrication tolerances.
        - Defaults must be explicit in the input configuration.
    """
    hw = _positive(full_web_height_mm, "full_web_height_mm")
    br = hw / 24.0 + 40.0 if one_sided else hw / 30.0 + 25.0
    tr = 2.0 * br * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))
    return {"minimum_projection_mm": br, "minimum_thickness_mm": tr}


def concentrated_load_stiffener_effective_section_8_5_10(web_thickness_mm: float, elastic_modulus_n_mm2: float, design_yield_resistance_n_mm2: float, effective_web_height_mm: float, one_sided: bool, eccentricity_mm: float = 0.0) -> dict[str, Any]:
    """
    Summary:
        Define the effective web strip and stability model for a stiffener under a concentrated load.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.10
        Annex: None
        Equation/Table: Effective-section procedure
        Audit ID: SP16-PROC-8.5.10-LOAD-STIFFENER-SECTION
        Normative status: normative

    Mathematical form:
        Effective web width on each side = 0.65*tw*sqrt(E/Ry); effective length=hef.

    Parameters:
        web_thickness_mm, elastic_modulus_n_mm2, design_yield_resistance_n_mm2, effective_web_height_mm, one_sided, eccentricity_mm:
            Type: float, float, float, float, bool, float
            Unit: mm, N/mm2, N/mm2, mm, dimensionless, mm
            Meaning: Web/material geometry and one-sided eccentricity.
            Valid range: positive except eccentricity non-negative
            Source: clause 8.5.10

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Effective strip width, effective length, and stability model.

    Assumptions:
        - The actual stiffener area and inertia are added externally.

    Sign convention:
        - Eccentricity is a non-negative magnitude.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Stiffeners at upper-flange concentrated loads.

    Limitations:
        - This function does not solve the column stability check.

    Raises:
        ValueError: Input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> concentrated_load_stiffener_effective_section_8_5_10(10, 206000, 355, 1000, False)['model']
        'centrally_compressed_column'

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-8510

    Implementation notes:
        - The one-sided model is eccentric compression.
        - Defaults must be explicit in the input configuration.
    """
    width = 0.65 * _positive(web_thickness_mm, "web_thickness_mm") * math.sqrt(_positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2") / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2"))
    return {"effective_web_strip_each_side_mm": width, "effective_length_mm": _positive(effective_web_height_mm, "effective_web_height_mm"), "model": "eccentrically_compressed_column" if one_sided else "centrally_compressed_column", "eccentricity_mm": _nonnegative(eccentricity_mm, "eccentricity_mm") if one_sided else 0.0}


def longitudinal_stiffener_required_8_5_11(web_relative_slenderness: float, design_yield_resistance_n_mm2: float, compressed_flange_stress_n_mm2: float, normal_stress_buckling_not_satisfied: bool) -> dict[str, Any]:
    """
    Summary:
        Determine whether a class-1 beam web requires a longitudinal stiffener.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.11
        Annex: None
        Equation/Table: Routing criterion
        Audit ID: SP16-PROC-8.5.11-LONGITUDINAL-STIFFENER-ROUTING
        Normative status: normative

    Mathematical form:
        Required if normal-stress stability fails or lambda_w_bar>5.5*sqrt(Ry/sigma).

    Parameters:
        web_relative_slenderness, design_yield_resistance_n_mm2, compressed_flange_stress_n_mm2, normal_stress_buckling_not_satisfied:
            Type: float, float, float, bool
            Unit: dimensionless, N/mm2, N/mm2, dimensionless
            Meaning: Web slenderness, material/stress values, and result of normal-stress stability check.
            Valid range: positive
            Source: clause 8.5.11

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Threshold and requirement flag.

    Assumptions:
        - Beam belongs to class 1.

    Sign convention:
        - Compression stress is positive.

    Unit convention:
        - Dimensionless threshold.

    Applicability:
        - Class-1 beam webs.

    Limitations:
        - The actual longitudinal stiffener design is separate.

    Raises:
        ValueError: Input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> longitudinal_stiffener_required_8_5_11(8, 355, 200, False)['required']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-8511

    Implementation notes:
        - This function must not infer the normal-stress buckling result.
        - Defaults must be explicit in the input configuration.
    """
    threshold = 5.5 * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(compressed_flange_stress_n_mm2, "compressed_flange_stress_n_mm2"))
    lam = _positive(web_relative_slenderness, "web_relative_slenderness")
    return {"threshold": threshold, "required": bool(normal_stress_buckling_not_satisfied) or lam > threshold}


def flexible_web_route_8_5_16(web_relative_slenderness: float, design_yield_resistance_n_mm2: float, compressed_flange_stress_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Determine whether the web must be designed as a class-2 beam with a flexible web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.16
        Annex: None
        Equation/Table: Routing criterion
        Audit ID: SP16-PROC-8.5.16-FLEXIBLE-WEB-ROUTING
        Normative status: normative

    Mathematical form:
        Flexible-web route when lambda_w_bar>6*sqrt(Ry/sigma).

    Parameters:
        web_relative_slenderness, design_yield_resistance_n_mm2, compressed_flange_stress_n_mm2:
            Type: float
            Unit: dimensionless, N/mm2, N/mm2
            Meaning: Web slenderness, resistance, and compression stress.
            Valid range: positive
            Source: clause 8.5.16

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Threshold and route flag.

    Assumptions:
        - Symmetric I-section.

    Sign convention:
        - Compression stress is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 8.5.16.

    Limitations:
        - The external flexible-web design rules are not implemented in this stage.

    Raises:
        ValueError: Input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> flexible_web_route_8_5_16(9, 355, 200)['external_flexible_web_rules_required']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-8516

    Implementation notes:
        - The external rule set is surfaced explicitly.
        - Defaults must be explicit in the input configuration.
    """
    threshold = 6.0 * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(compressed_flange_stress_n_mm2, "compressed_flange_stress_n_mm2"))
    return {"threshold": threshold, "external_flexible_web_rules_required": _positive(web_relative_slenderness, "web_relative_slenderness") > threshold}


def support_stiffener_effective_section_8_5_17(web_thickness_mm: float, elastic_modulus_n_mm2: float, design_yield_resistance_n_mm2: float, effective_web_height_mm: float, lower_flange_width_mm: float, stiffener_projection_mm: float | None) -> dict[str, Any]:
    """
    Summary:
        Define the effective support-stiffener column section and geometric requirement.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.17
        Annex: None
        Equation/Table: Support-stiffener procedure
        Audit ID: SP16-PROC-8.5.17-SUPPORT-STIFFENER
        Normative status: normative

    Mathematical form:
        Web strip each side <=0.65*tw*sqrt(E/Ry); effective length=hef; projection>=0.5*bf_lower when stiffener exists.

    Parameters:
        web_thickness_mm, elastic_modulus_n_mm2, design_yield_resistance_n_mm2, effective_web_height_mm, lower_flange_width_mm, stiffener_projection_mm:
            Type: float or None
            Unit: mm and N/mm2
            Meaning: Geometry/material and optional support-stiffener projection.
            Valid range: positive; projection None denotes no support stiffener
            Source: clause 8.5.17

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Effective width/length and projection compliance.

    Assumptions:
        - Actual stability and bearing checks are performed separately.

    Sign convention:
        - Positive dimensions.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Beam support web region.

    Limitations:
        - Weld and end-bearing checks are not solved here.

    Raises:
        ValueError: Input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> support_stiffener_effective_section_8_5_17(10, 206000, 355, 1000, 300, 160)['projection_ok']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-8517

    Implementation notes:
        - No-stiffener rolled-beam route is explicitly identified.
        - Defaults must be explicit in the input configuration.
    """
    width = 0.65 * _positive(web_thickness_mm, "web_thickness_mm") * math.sqrt(_positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2") / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2"))
    bf = _positive(lower_flange_width_mm, "lower_flange_width_mm")
    if stiffener_projection_mm is None:
        return {"has_support_stiffener": False, "rolled_beam_effective_web_width_equals_bearing_length": True, "effective_web_strip_each_side_mm": width, "effective_length_mm": _positive(effective_web_height_mm, "effective_web_height_mm"), "projection_ok": None}
    projection = _positive(stiffener_projection_mm, "stiffener_projection_mm")
    return {"has_support_stiffener": True, "rolled_beam_effective_web_width_equals_bearing_length": False, "effective_web_strip_each_side_mm": width, "effective_length_mm": _positive(effective_web_height_mm, "effective_web_height_mm"), "minimum_projection_mm": 0.5 * bf, "projection_ok": projection >= 0.5 * bf}


def edge_stiffened_flange_limit_8_5_20(base_limit: float, edge_stiffener_height_mm: float, effective_flange_outstand_mm: float, edge_stiffener_thickness_mm: float, flange_design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Apply the clause 8.5.20 multiplier to eligible I-section flange limits.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.20
        Annex: None
        Equation/Table: Edge-stiffening procedure
        Audit ID: SP16-PROC-8.5.20-EDGE-STIFFENING-MODIFIER
        Normative status: normative

    Mathematical form:
        Eligibility: a_ef>=0.3*b_ef and t>2*a_ef*sqrt(Ryf/E); modified limit=1.5*base limit.

    Parameters:
        base_limit, edge_stiffener_height_mm, effective_flange_outstand_mm, edge_stiffener_thickness_mm, flange_design_yield_resistance_n_mm2, elastic_modulus_n_mm2:
            Type: float
            Unit: dimensionless, mm, mm, mm, N/mm2, N/mm2
            Meaning: Base equation (97) or (99) limit and edge-stiffener properties.
            Valid range: positive
            Source: clause 8.5.20

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Eligibility checks and modified limit.

    Assumptions:
        - The base limit is from equation (97) or (99), not equations (98) or (100).

    Sign convention:
        - Positive dimensions.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Edge-stiffened or folded I-section flange outstand.

    Limitations:
        - Geometry type is not recognized automatically.

    Raises:
        ValueError: Input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> edge_stiffened_flange_limit_8_5_20(0.5, 40, 100, 5, 355, 206000)['eligible']
        True

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_table_19_and_procedures
        Validation cases:
            - BLS-PROC-8520

    Implementation notes:
        - The multiplier is applied only when both printed geometric conditions pass.
        - Defaults must be explicit in the input configuration.
    """
    base = _positive(base_limit, "base_limit")
    aef = _positive(edge_stiffener_height_mm, "edge_stiffener_height_mm")
    bef = _positive(effective_flange_outstand_mm, "effective_flange_outstand_mm")
    thickness_min = 2.0 * aef * math.sqrt(_positive(flange_design_yield_resistance_n_mm2, "flange_design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))
    geometry_ok = aef >= 0.3 * bef
    thickness_ok = _positive(edge_stiffener_thickness_mm, "edge_stiffener_thickness_mm") > thickness_min
    eligible = geometry_ok and thickness_ok
    return {"geometry_ok": geometry_ok, "minimum_thickness_mm": thickness_min, "thickness_ok": thickness_ok, "eligible": eligible, "modified_limit": 1.5 * base if eligible else base}


def _exact_1d(nodes: list[float], values: list[float], x: float, name: str) -> float:
    for node, value in zip(nodes, values):
        if abs(float(node) - float(x)) <= 1e-12:
            return float(value)
    raise ValueError(f"{name}={x:g} is not an exact printed table node")


def _exact_2d(table_name: str, row_x: float, column_x: float, cap_x: float | None = None) -> float:
    table = _TABLES[table_name]
    rows = [float(x) for x in table["row_nodes"]]
    cols = [float(x) for x in table["column_nodes"]]
    col = float(column_x)
    if cap_x is not None and col >= cap_x:
        col = cap_x
    row_index = next((i for i, x in enumerate(rows) if abs(x - float(row_x)) <= 1e-12), None)
    col_index = next((i for i, x in enumerate(cols) if abs(x - col) <= 1e-12), None)
    if row_index is None or col_index is None:
        raise ValueError(f"Requested ({row_x:g}, {column_x:g}) is not an exact printed {table_name} node")
    return float(table["values"][row_index][col_index])


def _linear(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def panel_check_routing_8_5_5(panel_ratio: float, local_stress_present: bool) -> dict[str, Any]:
    """
    Summary:
        Define the one-check or two-check route for a transversely stiffened class-1 web panel.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.5
        Annex: None
        Equation/Table: Equation (80), Tables 14-16
        Audit ID: SP16-PROC-8.5.5-DOUBLE-CHECK-ROUTING
        Normative status: normative

    Mathematical form:
        For local stress and a/hef>0.8, perform the actual-panel check and a second reduced-panel check; otherwise one check.

    Parameters:
        panel_ratio, local_stress_present:
            Type: float, bool
            Unit: dimensionless
            Meaning: a/hef and whether sigma_loc is non-zero.
            Valid range: panel_ratio positive
            Source: clause 8.5.5

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Required checks and reduced-panel substitution a1/hef.

    Assumptions:
        - The caller applies the actual critical-stress formulas to each returned route.

    Sign convention:
        - Ratio is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 8.5.5 symmetric class-1 web panels.

    Limitations:
        - This function does not evaluate equation (80) itself.

    Raises:
        ValueError: panel_ratio is non-positive.
        TypeError: panel_ratio is not real.

    Examples:
        >>> panel_check_routing_8_5_5(1.0, True)['number_of_checks']
        2

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_clause_specific_routing_helpers
        Validation cases:
            - BLS-PROC-855

    Implementation notes:
        - The second-check substitution follows the printed 0.5a and 0.67hef rules.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(panel_ratio, "panel_ratio")
    actual_ratio = min(ratio, 2.0)
    checks: list[dict[str, float | str]] = [{"name": "actual_panel", "ratio_for_c1_c2": actual_ratio, "ratio_for_tau": ratio, "c_cr_source": "table_12"}]
    if local_stress_present and ratio > 0.8:
        reduced_ratio = 0.5 * ratio if ratio <= 1.33 else 0.67
        checks.append({"name": "reduced_panel", "ratio_for_c1_c2": reduced_ratio, "ratio_for_tau": ratio, "c_cr_source": "table_16"})
    return {"number_of_checks": len(checks), "checks": checks}


def asymmetric_compressed_flange_substitution_8_5_6(effective_web_height_mm: float, compressed_web_zone_height_mm: float) -> dict[str, float]:
    """
    Summary:
        Return the effective-height substitution for an asymmetric I-beam with the larger compression flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.6
        Annex: None
        Equation/Table: Equations (81), (84), Table 16
        Audit ID: SP16-PROC-8.5.6-ASYMMETRIC-COMPRESSED-FLANGE-ROUTING
        Normative status: normative

    Mathematical form:
        Replace hef by 2hc in equations (81), (84), and the specified Table 16 route.

    Parameters:
        effective_web_height_mm, compressed_web_zone_height_mm:
            Type: float
            Unit: mm
            Meaning: Actual effective web height and compressed-zone height.
            Valid range: positive; 2hc not above the actual geometry unless justified by the section state
            Source: clause 8.5.6

    Returns:
        Type: dict[str, float]
        Unit: mm and dimensionless
        Meaning: Substituted height and actual/substituted ratios.

    Assumptions:
        - The section has the larger compression flange and meets clause 8.5.6.

    Sign convention:
        - Heights are positive.

    Unit convention:
        - Consistent length unit.

    Applicability:
        - Clause 8.5.6.

    Limitations:
        - hc must come from a verified stress distribution.

    Raises:
        ValueError: A height is non-positive.
        TypeError: Input is not real.

    Examples:
        >>> asymmetric_compressed_flange_substitution_8_5_6(1000, 350)['substituted_height_mm']
        700.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_clause_specific_routing_helpers
        Validation cases:
            - BLS-PROC-856

    Implementation notes:
        - The substitution is returned explicitly rather than silently applied.
        - Defaults must be explicit in the input configuration.
    """
    hef = _positive(effective_web_height_mm, "effective_web_height_mm")
    hc = _positive(compressed_web_zone_height_mm, "compressed_web_zone_height_mm")
    return {"actual_height_mm": hef, "substituted_height_mm": 2.0 * hc, "substitution_ratio": 2.0 * hc / hef}


def intermediate_stiffener_panel_length_8_5_13(transverse_panel_length_mm: float, intermediate_stiffener_spacing_mm: float | None) -> dict[str, Any]:
    """
    Summary:
        Select the panel length used for plate-1 equations when intermediate stiffeners are present.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.13
        Annex: None
        Equation/Table: Equations (89)-(93)
        Audit ID: SP16-PROC-8.5.13-INTERMEDIATE-STIFFENERS
        Normative status: normative

    Mathematical form:
        Use a1, the spacing between intermediate stiffeners, instead of a for plate 1; plate 2 retains clause 8.5.12(b).

    Parameters:
        transverse_panel_length_mm, intermediate_stiffener_spacing_mm:
            Type: float, float or None
            Unit: mm
            Meaning: Main transverse-stiffener spacing and optional intermediate spacing.
            Valid range: positive; when provided, a1 must not exceed a
            Source: clause 8.5.13

    Returns:
        Type: dict[str, Any]
        Unit: mm and categorical
        Meaning: Plate-1 calculation length and plate-2 route.

    Assumptions:
        - Intermediate stiffeners extend to the longitudinal stiffener as required.

    Sign convention:
        - Positive lengths.

    Unit convention:
        - Consistent length unit.

    Applicability:
        - Plate 1 between compression flange and longitudinal stiffener.

    Limitations:
        - Stiffener continuity is an external detailing confirmation.

    Raises:
        ValueError: Spacing is invalid.
        TypeError: Input is not real.

    Examples:
        >>> intermediate_stiffener_panel_length_8_5_13(1200, 400)['plate_1_length_mm']
        400.0

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_clause_specific_routing_helpers
        Validation cases:
            - BLS-PROC-8513

    Implementation notes:
        - The function preserves the separate plate-2 route.
        - Defaults must be explicit in the input configuration.
    """
    a = _positive(transverse_panel_length_mm, "transverse_panel_length_mm")
    if intermediate_stiffener_spacing_mm is None:
        return {"plate_1_length_mm": a, "source": "transverse_panel_length", "plate_2_route": "clause_8.5.12_b"}
    a1 = _positive(intermediate_stiffener_spacing_mm, "intermediate_stiffener_spacing_mm")
    if a1 > a:
        raise ValueError("intermediate stiffener spacing must not exceed the transverse panel length")
    return {"plate_1_length_mm": a1, "source": "intermediate_stiffener_spacing", "plate_2_route": "clause_8.5.12_b"}


def asymmetric_split_web_substitutions_8_5_14(sigma_1_n_mm2: float, sigma_2_n_mm2: float, plate_1_height_mm: float, effective_web_height_mm: float) -> dict[str, float]:
    """
    Summary:
        Calculate the printed ratio substitutions for an asymmetric split web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.14
        Annex: None
        Equation/Table: Equations (90), (91), (94), and (95)
        Audit ID: SP16-PROC-8.5.14-ASYMMETRIC-SPLIT-WEB
        Normative status: normative

    Mathematical form:
        Replace h1/hef by ((sigma1-sigma2)/(2sigma1))*(h1/hef); replace 0.5-h1/hef by sigma1/(sigma1-sigma2)-h1/hef.

    Parameters:
        sigma_1_n_mm2, sigma_2_n_mm2, plate_1_height_mm, effective_web_height_mm:
            Type: float
            Unit: N/mm2, N/mm2, mm, mm
            Meaning: Compression-edge stress, signed opposite-edge stress, and split geometry.
            Valid range: sigma1 positive; sigma1-sigma2 non-zero; heights positive
            Source: clause 8.5.14

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: Both substitution factors.

    Assumptions:
        - sigma2 is signed and is negative for edge tension as specified.

    Sign convention:
        - sigma1 positive compression; sigma2 signed.

    Unit convention:
        - Dimensionless ratios.

    Applicability:
        - Asymmetric I-section with paired longitudinal stiffener in the compression zone.

    Limitations:
        - This function returns substitutions; it does not rerun equations (89)-(95).

    Raises:
        ValueError: Stress or geometry creates a singular substitution.
        TypeError: Input is not real.

    Examples:
        >>> asymmetric_split_web_substitutions_8_5_14(200, -100, 200, 1000)['upper_ratio_replacement']
        0.15

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_clause_specific_routing_helpers
        Validation cases:
            - BLS-PROC-8514

    Implementation notes:
        - The signed tensile stress is preserved.
        - Defaults must be explicit in the input configuration.
    """
    sigma1 = _positive(sigma_1_n_mm2, "sigma_1_n_mm2")
    sigma2 = _signed(sigma_2_n_mm2, "sigma_2_n_mm2")
    difference = sigma1 - sigma2
    if abs(difference) < 1e-15:
        raise ValueError("sigma1-sigma2 must not be zero")
    ratio = _positive(plate_1_height_mm, "plate_1_height_mm") / _positive(effective_web_height_mm, "effective_web_height_mm")
    return {"upper_ratio_replacement": (difference / (2.0 * sigma1)) * ratio, "lower_denominator_replacement": sigma1 / difference - ratio}


def support_stiffener_end_resistance_8_5_17(end_arrangement: str, projection_a_mm: float, plate_thickness_mm: float, bearing_resistance_n_mm2: float, compression_resistance_n_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Select the support-stiffener end resistance check specified by clause 8.5.17.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.17
        Annex: None
        Equation/Table: Figure 11 end-check procedure
        Audit ID: SP16-PROC-8.5.17-SUPPORT-STIFFENER
        Normative status: normative

    Mathematical form:
        Milled end: bearing for a<=1.5t and compression for a>1.5t; fitted/welded remote end: bearing.

    Parameters:
        end_arrangement, projection_a_mm, plate_thickness_mm, bearing_resistance_n_mm2, compression_resistance_n_mm2:
            Type: str, float
            Unit: categorical, mm, N/mm2
            Meaning: Figure 11 arrangement, projection, thickness, and design resistances.
            Valid range: arrangement milled_end or fitted_or_welded_remote; positive values
            Source: clause 8.5.17

    Returns:
        Type: dict[str, Any]
        Unit: N/mm2 and categorical
        Meaning: Governing resistance type and value.

    Assumptions:
        - Actual stress is checked separately.

    Sign convention:
        - Resistances are positive.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Lower ends of support stiffeners.

    Limitations:
        - Weld resistance is not designed here.

    Raises:
        ValueError: Arrangement or a positive input is invalid.
        TypeError: Input is not real.

    Examples:
        >>> support_stiffener_end_resistance_8_5_17('milled_end', 12, 10, 400, 355)['resistance_type']
        'bearing'

    Tests:
        Unit tests:
            - tests/test_bending_member_local_stability.py::test_clause_specific_routing_helpers
        Validation cases:
            - BLS-PROC-8517-END

    Implementation notes:
        - The selected resistance is explicit and auditable.
        - Defaults must be explicit in the input configuration.
    """
    a = _positive(projection_a_mm, "projection_a_mm")
    t = _positive(plate_thickness_mm, "plate_thickness_mm")
    rp = _positive(bearing_resistance_n_mm2, "bearing_resistance_n_mm2")
    ry = _positive(compression_resistance_n_mm2, "compression_resistance_n_mm2")
    if end_arrangement == "fitted_or_welded_remote":
        return {"resistance_type": "bearing", "design_resistance_n_mm2": rp}
    if end_arrangement != "milled_end":
        raise ValueError("end_arrangement must be 'milled_end' or 'fitted_or_welded_remote'")
    return {"resistance_type": "bearing", "design_resistance_n_mm2": rp} if a <= 1.5 * t else {"resistance_type": "compression", "design_resistance_n_mm2": ry}
