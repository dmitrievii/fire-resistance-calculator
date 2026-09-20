"""Crane-runway beam strength and bending-member stability under SP 16.13330.2017."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .built_up_axial_members import fictitious_shear_force_n
from .bending_members import bimetal_biaxial_bending_utilization_eq60

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_11 = json.loads((_DATA_DIR / "table_11_lateral_torsional_slenderness_limits.json").read_text(encoding="utf-8"))
_TABLE_12 = json.loads((_DATA_DIR / "table_12_web_buckling_c_cr.json").read_text(encoding="utf-8"))
_TABLE_13 = json.loads((_DATA_DIR / "table_13_compressed_flange_beta.json").read_text(encoding="utf-8"))
_ANNEX_ZH = json.loads((_DATA_DIR / "annex_zh_tables.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-8.3.1-CRANE-ROUTING",
    "SP16-PROC-8.3.2-SUPPORT-BETA",
    "SP16-PROC-8.3.3-STRESS-BUNDLE",
    "SP16-PROC-8.3.5-BIMETAL-CRANE-ROUTING",
    "SP16-PROC-8.4.2-EFFECTIVE-LENGTH",
    "SP16-PROC-8.4.3-CRANE-STABILITY-ROUTING",
    "SP16-PROC-8.4.4-STABILITY-EXEMPTION",
    "SP16-PROC-8.4.4-TABLE-11-ROUTING",
    "SP16-PROC-8.4.5-DISCRETE-BRACING-FORCE",
    "SP16-PROC-8.4.6-CLASS-2-3-LIMIT",
    "SP16-PROC-ANNEX-ZH-TABLE-1",
    "SP16-PROC-ANNEX-ZH-TABLE-2",
    "SP16-PROC-ANNEX-ZH-TABLE-3",
    "SP16-PROC-ANNEX-ZH-TABLE-4",
    "SP16-PROC-ANNEX-ZH-TABLE-5",
    "SP16-PROC-ANNEX-ZH-INTERPOLATION",
    "SP16-PROC-ANNEX-ZH-T-SECTION-MODIFIER",
    "SP16-PROC-ANNEX-ZH-SYMMETRIC-I",
    "SP16-PROC-ANNEX-ZH-MONOSYMMETRIC-I",
    "SP16-PROC-ANNEX-ZH-CHANNEL",
    "SP16-PROC-TABLE-12-LOOKUP",
    "SP16-PROC-TABLE-13-LOOKUP",
)


def _real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _nonnegative(value: float, name: str) -> float:
    result = _real(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _positive(value: float, name: str) -> float:
    result = _real(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return result


def _signed(value: float, name: str) -> float:
    return _real(value, name)


def _utilization(numerator: float, resistance: float, resistance_name: str) -> float:
    return _nonnegative(numerator, "numerator") / _positive(resistance, resistance_name)


def crane_runway_equivalent_stress_utilization_eq63(
    beta_factor: float,
    sigma_x_n_mm2: float,
    sigma_local_x_n_mm2: float,
    sigma_local_y_n_mm2: float,
    tau_xy_n_mm2: float,
    tau_local_xy_n_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the equivalent-stress utilization of a crane-runway beam web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (63)
        Audit ID: SP16-EQ-063
        Normative status: normative

    Mathematical form:
        eta = beta/Ry*sqrt((sx+slx)^2-(sx+slx)*sly+sly^2+3*(txy+tlxy)^2).

    Parameters:
        beta_factor:
            Type: float
            Unit: dimensionless
            Meaning: 0.87 for simply supported beams or 0.77 at continuous-beam supports.
            Valid range: > 0
            Source: clause 8.3.3
        sigma_x_n_mm2, sigma_local_x_n_mm2, sigma_local_y_n_mm2, tau_xy_n_mm2, tau_local_xy_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Non-negative stress components from equation (67).
            Valid range: >= 0
            Source: structural analysis and equation (67)
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance Ry.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (63) utilization; pass when <= 1.

    Assumptions:
        - All stress components are taken with the plus sign as required by clause 8.3.3.

    Sign convention:
        - Inputs are non-negative magnitudes.

    Unit convention:
        - N and mm are used without conversion.

    Applicability:
        - Crane groups 7K in metallurgical production and 8K, steel yield strength not above 440 N/mm2.

    Limitations:
        - Local effects outside equation (67) are not inferred.

    Raises:
        ValueError: A stress is negative or a resistance is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> crane_runway_equivalent_stress_utilization_eq63(0.87, 100, 10, 20, 30, 5, 355) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-063

    Implementation notes:
        - No absolute-value substitution is needed because the clause requires plus-sign stress magnitudes.
        - Defaults must be explicit in the input configuration.
    """
    beta = _positive(beta_factor, "beta_factor")
    sx = _nonnegative(sigma_x_n_mm2, "sigma_x_n_mm2") + _nonnegative(sigma_local_x_n_mm2, "sigma_local_x_n_mm2")
    sy = _nonnegative(sigma_local_y_n_mm2, "sigma_local_y_n_mm2")
    tau = _nonnegative(tau_xy_n_mm2, "tau_xy_n_mm2") + _nonnegative(tau_local_xy_n_mm2, "tau_local_xy_n_mm2")
    radicand = sx * sx - sx * sy + sy * sy + 3.0 * tau * tau
    return beta * math.sqrt(max(0.0, radicand)) / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")


def crane_runway_longitudinal_normal_utilization_eq64(
    sigma_x_n_mm2: float, sigma_local_x_n_mm2: float, design_yield_resistance_n_mm2: float
) -> float:
    """
    Summary:
        Calculate the longitudinal normal-stress utilization of the crane-runway web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (64)
        Audit ID: SP16-EQ-064
        Normative status: normative

    Mathematical form:
        eta = (sigma_x + sigma_loc,x)/Ry.

    Parameters:
        sigma_x_n_mm2, sigma_local_x_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Longitudinal stress magnitudes.
            Valid range: >= 0
            Source: equation (67)
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (64) utilization.

    Assumptions:
        - Stress components use the clause-required plus sign.

    Sign convention:
        - Non-negative magnitudes.

    Unit convention:
        - N/mm2.

    Applicability:
        - Clause 8.3.3 crane-runway web checks.

    Limitations:
        - Does not calculate stress components.

    Raises:
        ValueError: Invalid magnitude or resistance.
        TypeError: Non-real input.

    Examples:
        >>> crane_runway_longitudinal_normal_utilization_eq64(100, 20, 300)
        0.4

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-064

    Implementation notes:
        - This function performs no hidden unit conversion.
        - Defaults must be explicit in the input configuration.
    """
    return (_nonnegative(sigma_x_n_mm2, "sigma_x_n_mm2") + _nonnegative(sigma_local_x_n_mm2, "sigma_local_x_n_mm2")) / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")


def crane_runway_transverse_normal_utilization_eq65(
    sigma_local_y_n_mm2: float, sigma_f_y_n_mm2: float, design_yield_resistance_n_mm2: float
) -> float:
    """
    Summary:
        Calculate the transverse normal-stress utilization of the crane-runway web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (65)
        Audit ID: SP16-EQ-065
        Normative status: normative

    Mathematical form:
        eta = (sigma_loc,y + sigma_f,y)/Ry.

    Parameters:
        sigma_local_y_n_mm2, sigma_f_y_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Local transverse and torsion-induced normal stresses.
            Valid range: >= 0
            Source: equation (67)
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (65) utilization.

    Assumptions:
        - Stress components are non-negative magnitudes.

    Sign convention:
        - Plus-sign combination.

    Unit convention:
        - N/mm2.

    Applicability:
        - Clause 8.3.3.

    Limitations:
        - Separate from equivalent and shear checks.

    Raises:
        ValueError: Invalid magnitude or resistance.
        TypeError: Non-real input.

    Examples:
        >>> crane_runway_transverse_normal_utilization_eq65(80, 20, 250)
        0.4

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-065

    Implementation notes:
        - No national-choice defaults are introduced.
        - Defaults must be explicit in the input configuration.
    """
    return (_nonnegative(sigma_local_y_n_mm2, "sigma_local_y_n_mm2") + _nonnegative(sigma_f_y_n_mm2, "sigma_f_y_n_mm2")) / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")


def crane_runway_shear_utilization_eq66(
    tau_xy_n_mm2: float,
    tau_local_xy_n_mm2: float,
    tau_f_xy_n_mm2: float,
    design_shear_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the combined shear-stress utilization of the crane-runway web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (66)
        Audit ID: SP16-EQ-066
        Normative status: normative

    Mathematical form:
        eta = (tau_xy + tau_loc,xy + tau_f,xy)/Rs.

    Parameters:
        tau_xy_n_mm2, tau_local_xy_n_mm2, tau_f_xy_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Shear-stress magnitudes.
            Valid range: >= 0
            Source: equation (67)
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance Rs.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (66) utilization.

    Assumptions:
        - All components are taken with the plus sign.

    Sign convention:
        - Non-negative magnitudes.

    Unit convention:
        - N/mm2.

    Applicability:
        - Clause 8.3.3.

    Limitations:
        - Does not include other local shear sources.

    Raises:
        ValueError: Invalid magnitude or resistance.
        TypeError: Non-real input.

    Examples:
        >>> crane_runway_shear_utilization_eq66(30, 10, 10, 100)
        0.5

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-066

    Implementation notes:
        - Inputs are explicit design stresses.
        - Defaults must be explicit in the input configuration.
    """
    total = sum(_nonnegative(v, n) for v, n in (
        (tau_xy_n_mm2, "tau_xy_n_mm2"),
        (tau_local_xy_n_mm2, "tau_local_xy_n_mm2"),
        (tau_f_xy_n_mm2, "tau_f_xy_n_mm2"),
    ))
    return total / _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")


def crane_runway_stress_components_eq67(
    bending_moment_n_mm: float,
    net_section_modulus_mm3: float,
    load_factor: float,
    wheel_dynamic_factor: float,
    normative_wheel_load_n: float,
    effective_load_length_mm: float,
    web_thickness_mm: float,
    local_torsional_moment_n_mm: float,
    stiffener_spacing_mm: float,
    torsional_inertia_rail_and_flange_mm4: float,
    web_height_mm: float,
    shear_force_n: float,
) -> dict[str, float]:
    """
    Summary:
        Calculate the seven crane-runway web stress components defined by equation (67).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (67)
        Audit ID: SP16-EQ-067
        Normative status: normative

    Mathematical form:
        sigma_x=M/Wxn; sigma_loc,x=0.25 sigma_loc,y; sigma_loc,y=gamma_f gamma_f1 Fn/(lef tw); sigma_f,y=Mt tw a/(0.75 If hw); tau_xy=Q/(tw hw); tau_loc,xy=0.3 sigma_loc,y; tau_f,xy=0.25 sigma_f,y.

    Parameters:
        bending_moment_n_mm, local_torsional_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending and local torsional moments.
            Valid range: >= 0
            Source: structural analysis and equation (68)
        net_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Net section modulus Wxn.
            Valid range: > 0
            Source: section properties
        load_factor, wheel_dynamic_factor:
            Type: float
            Unit: dimensionless
            Meaning: Crane load factors gamma_f and gamma_f1.
            Valid range: > 0
            Source: SP 20.13330
        normative_wheel_load_n, shear_force_n:
            Type: float
            Unit: N
            Meaning: Normative wheel load and design shear force.
            Valid range: >= 0
            Source: load model
        effective_load_length_mm, web_thickness_mm, stiffener_spacing_mm, web_height_mm:
            Type: float
            Unit: mm
            Meaning: Geometric quantities in equation (67).
            Valid range: > 0
            Source: geometry and clause 8.2.2
        torsional_inertia_rail_and_flange_mm4:
            Type: float
            Unit: mm4
            Meaning: If = It + bf*tf^3/3.
            Valid range: > 0
            Source: section properties

    Returns:
        Type: dict[str, float]
        Unit: N/mm2
        Meaning: Named stress components for equations (63)-(66).

    Assumptions:
        - The equation symbol t in sigma_f,y is implemented as web thickness tw, consistent with dimensional homogeneity and the surrounding notation.

    Sign convention:
        - Returned stresses are non-negative magnitudes.

    Unit convention:
        - N and mm are used without conversion.

    Applicability:
        - Clause 8.3.3 crane-runway web checks.

    Limitations:
        - The package does not derive If from rail and flange geometry in this function.

    Raises:
        ValueError: Invalid magnitude or non-positive geometry.
        TypeError: Non-real input.

    Examples:
        >>> crane_runway_stress_components_eq67(1e8, 1e6, 1.1, 1.2, 100000, 200, 10, 1e7, 1000, 1e8, 800, 200000)["sigma_x_n_mm2"]
        100.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-067

    Implementation notes:
        - If is supplied explicitly to keep the rail/flange section-property calculation auditable.
        - Defaults must be explicit in the input configuration.
    """
    m = _nonnegative(bending_moment_n_mm, "bending_moment_n_mm")
    wx = _positive(net_section_modulus_mm3, "net_section_modulus_mm3")
    gamma_f = _positive(load_factor, "load_factor")
    gamma_f1 = _positive(wheel_dynamic_factor, "wheel_dynamic_factor")
    fn = _nonnegative(normative_wheel_load_n, "normative_wheel_load_n")
    lef = _positive(effective_load_length_mm, "effective_load_length_mm")
    tw = _positive(web_thickness_mm, "web_thickness_mm")
    mt = _nonnegative(local_torsional_moment_n_mm, "local_torsional_moment_n_mm")
    a = _positive(stiffener_spacing_mm, "stiffener_spacing_mm")
    i_f = _positive(torsional_inertia_rail_and_flange_mm4, "torsional_inertia_rail_and_flange_mm4")
    hw = _positive(web_height_mm, "web_height_mm")
    q = _nonnegative(shear_force_n, "shear_force_n")
    sigma_x = m / wx
    sigma_loc_y = gamma_f * gamma_f1 * fn / (lef * tw)
    sigma_loc_x = 0.25 * sigma_loc_y
    sigma_f_y = mt * tw * a / (0.75 * i_f * hw)
    tau_xy = q / (tw * hw)
    return {
        "sigma_x_n_mm2": sigma_x,
        "sigma_local_x_n_mm2": sigma_loc_x,
        "sigma_local_y_n_mm2": sigma_loc_y,
        "sigma_f_y_n_mm2": sigma_f_y,
        "tau_xy_n_mm2": tau_xy,
        "tau_local_xy_n_mm2": 0.3 * sigma_loc_y,
        "tau_f_xy_n_mm2": 0.25 * sigma_f_y,
    }


def crane_runway_local_torsional_moment_eq68(
    load_factor: float,
    wheel_dynamic_factor: float,
    normative_wheel_load_n: float,
    eccentricity_mm: float,
    transverse_horizontal_load_n: float,
    rail_height_mm: float,
) -> float:
    """
    Summary:
        Calculate the local torsional moment from vertical wheel eccentricity and transverse crane load.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.3
        Annex: None
        Equation/Table: Equation (68)
        Audit ID: SP16-EQ-068
        Normative status: normative

    Mathematical form:
        Mt = gamma_f*gamma_f1*Fn*e + 0.75*Qt*hr.

    Parameters:
        load_factor, wheel_dynamic_factor:
            Type: float
            Unit: dimensionless
            Meaning: Crane load factors.
            Valid range: > 0
            Source: SP 20.13330
        normative_wheel_load_n, transverse_horizontal_load_n:
            Type: float
            Unit: N
            Meaning: Wheel and transverse crane loads.
            Valid range: >= 0
            Source: load model
        eccentricity_mm, rail_height_mm:
            Type: float
            Unit: mm
            Meaning: e=0.2b and rail height hr.
            Valid range: >= 0
            Source: rail geometry

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Local torsional moment Mt.

    Assumptions:
        - Eccentricity has already been set to 0.2 times the rail-foot width where applicable.

    Sign convention:
        - Both contributions are added as magnitudes.

    Unit convention:
        - N and mm.

    Applicability:
        - Clause 8.3.3.

    Limitations:
        - SP 20.13330 load derivation is external.

    Raises:
        ValueError: Invalid factor or negative magnitude.
        TypeError: Non-real input.

    Examples:
        >>> crane_runway_local_torsional_moment_eq68(1.1, 1.2, 100000, 20, 10000, 150)
        3765000.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_63_to_68
        Validation cases:
            - CRANE-EQ-068

    Implementation notes:
        - Eccentricity is explicit rather than silently calculated.
        - Defaults must be explicit in the input configuration.
    """
    return (
        _positive(load_factor, "load_factor")
        * _positive(wheel_dynamic_factor, "wheel_dynamic_factor")
        * _nonnegative(normative_wheel_load_n, "normative_wheel_load_n")
        * _nonnegative(eccentricity_mm, "eccentricity_mm")
        + 0.75 * _nonnegative(transverse_horizontal_load_n, "transverse_horizontal_load_n") * _nonnegative(rail_height_mm, "rail_height_mm")
    )



def bimetal_crane_runway_strength_utilization(
    major_moment_n_mm: float,
    horizontal_moment_n_mm: float,
    major_axis_coefficient_c_xr: float,
    shear_reduction_beta_r: float,
    major_net_section_modulus_mm3: float,
    upper_flange_minor_section_modulus_mm3: float,
    web_design_yield_resistance_n_mm2: float,
    flange_design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    has_two_symmetry_axes: bool,
) -> float:
    """
    Summary:
        Apply clause 8.3.5 by routing an eligible bimetal crane-runway beam to equation (60) with the prescribed upper-flange substitutions.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.3.5
        Annex: E
        Equation/Table: Equation (60) with c_y=1.15 and W_yn=W_ynf
        Audit ID: SP16-PROC-8.3.5-BIMETAL-CRANE-ROUTING
        Normative status: normative procedure

    Mathematical form:
        eta = Mx/(c_xr beta_r Wxn Ryw gamma_c) + My/(1.15 W_ynf Ryf gamma_c).

    Parameters:
        major_moment_n_mm, horizontal_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-plane moment and horizontal-plane moment fully transferred to the upper flange.
            Valid range: real
            Source: structural analysis
        major_axis_coefficient_c_xr, shear_reduction_beta_r, working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: c_xr, beta_r, and gamma_c.
            Valid range: > 0
            Source: equations (61), (62), and applicable clause
        major_net_section_modulus_mm3, upper_flange_minor_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn and upper-flange W_ynf.
            Valid range: > 0
            Source: section properties
        web_design_yield_resistance_n_mm2, flange_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_yw and R_yf.
            Valid range: > 0 with R_yf/R_yw <= 1.5
            Source: clause 6.1
        has_two_symmetry_axes:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of the clause-required section symmetry.
            Valid range: true
            Source: section classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Clause-8.3.5 strength utilization using equation (60).

    Assumptions:
        - The crane operating group is 1K–5K and equation-(60) prerequisites are satisfied.

    Sign convention:
        - Signed moments are combined by the equation-(60) implementation before the final utilization magnitude.

    Unit convention:
        - N and mm.

    Applicability:
        - Bimetal doubly symmetric I-section crane-runway beams with R_yf/R_yw<=1.5.

    Limitations:
        - Crane operating-group classification and the remaining equation-(60) applicability checks are external verified inputs.

    Raises:
        ValueError: The section symmetry is not confirmed, the resistance ratio exceeds 1.5, or an input is invalid.
        TypeError: has_two_symmetry_axes is not boolean or a numerical input is not real.

    Examples:
        >>> bimetal_crane_runway_strength_utilization(1e8, 2e7, 1.2, 1.0, 1e6, 5e5, 300, 355, 1.0, True) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_bimetal_crane_runway_route
        Validation cases:
            - CRANE-PROC-8.3.5

    Implementation notes:
        - The minor-axis coefficient is fixed to 1.15 and the minor section modulus is explicitly the upper-flange value.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(has_two_symmetry_axes, bool):
        raise TypeError("has_two_symmetry_axes must be bool")
    if not has_two_symmetry_axes:
        raise ValueError("Clause 8.3.5 requires two axes of symmetry")
    ryw = _positive(web_design_yield_resistance_n_mm2, "web_design_yield_resistance_n_mm2")
    ryf = _positive(flange_design_yield_resistance_n_mm2, "flange_design_yield_resistance_n_mm2")
    if ryf / ryw > 1.5:
        raise ValueError("Clause 8.3.5 requires R_yf/R_yw <= 1.5")
    return bimetal_biaxial_bending_utilization_eq60(
        _signed(major_moment_n_mm, "major_moment_n_mm"),
        _signed(horizontal_moment_n_mm, "horizontal_moment_n_mm"),
        _positive(major_axis_coefficient_c_xr, "major_axis_coefficient_c_xr"),
        1.15,
        _positive(shear_reduction_beta_r, "shear_reduction_beta_r"),
        _positive(major_net_section_modulus_mm3, "major_net_section_modulus_mm3"),
        _positive(upper_flange_minor_section_modulus_mm3, "upper_flange_minor_section_modulus_mm3"),
        ryw,
        ryf,
        _positive(working_condition_factor, "working_condition_factor"),
    )

def lateral_torsional_stability_utilization_eq69(
    bending_moment_n_mm: float,
    stability_coefficient_phi_b: float,
    compressed_fibre_section_modulus_mm3: float,
    design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate lateral-torsional stability utilization for one-plane bending.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.1
        Annex: Ж
        Equation/Table: Equation (69)
        Audit ID: SP16-EQ-069
        Normative status: normative

    Mathematical form:
        eta = |Mx|/(phi_b*Wcx*Ry*gamma_c).

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design major-axis bending moment.
            Valid range: real
            Source: structural analysis
        stability_coefficient_phi_b, working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Stability and working-condition coefficients.
            Valid range: > 0
            Source: Annex Ж and applicable clause
        compressed_fibre_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Wcx for the most compressed fibre of the compressed flange.
            Valid range: > 0
            Source: section properties
        design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Ry, or Ryf for bimetal beams.
            Valid range: > 0
            Source: clause 6.1 or 8.4.1 substitution

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (69) utilization.

    Assumptions:
        - Support sections are restrained against lateral displacement and twist.

    Sign convention:
        - Moment magnitude is used.

    Unit convention:
        - N and mm.

    Applicability:
        - Class-1 I beams and applicable class-2 bimetal beams.

    Limitations:
        - Local stability is separate.

    Raises:
        ValueError: Invalid denominator input.
        TypeError: Non-real input.

    Examples:
        >>> lateral_torsional_stability_utilization_eq69(1e8, 0.8, 1e6, 250, 1.0)
        0.5

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_69_and_70
        Validation cases:
            - STAB-EQ-069

    Implementation notes:
        - Bimetal substitution is represented by the explicit design_resistance input.
        - Defaults must be explicit in the input configuration.
    """
    return abs(_signed(bending_moment_n_mm, "bending_moment_n_mm")) / (
        _positive(stability_coefficient_phi_b, "stability_coefficient_phi_b")
        * _positive(compressed_fibre_section_modulus_mm3, "compressed_fibre_section_modulus_mm3")
        * _positive(design_resistance_n_mm2, "design_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def lateral_torsional_combined_utilization_eq70(
    major_moment_n_mm: float,
    minor_moment_n_mm: float,
    bimoment_n_mm2: float,
    stability_coefficient_phi_b: float,
    compressed_major_section_modulus_mm3: float,
    compressed_minor_section_modulus_mm3: float,
    compressed_sectorial_section_modulus_mm4: float,
    design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate combined lateral-torsional stability utilization under biaxial bending and bimoment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.1
        Annex: Ж
        Equation/Table: Equation (70)
        Audit ID: SP16-EQ-070
        Normative status: normative

    Mathematical form:
        eta = |Mx/(phi_b Wcx Ry gamma_c) + My/(Wcy Ry gamma_c) + B/(Wcw Ry gamma_c)|.

    Parameters:
        major_moment_n_mm, minor_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Signed moments; positive terms cause compression at the checked point.
            Valid range: real
            Source: structural analysis
        bimoment_n_mm2:
            Type: float
            Unit: N*mm2
            Meaning: Signed bimoment.
            Valid range: real
            Source: structural analysis
        stability_coefficient_phi_b, working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Stability and working-condition coefficients.
            Valid range: > 0
            Source: Annex Ж and applicable clause
        compressed_major_section_modulus_mm3, compressed_minor_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Section moduli at the checked compressed fibre.
            Valid range: > 0
            Source: section properties
        compressed_sectorial_section_modulus_mm4:
            Type: float
            Unit: mm4
            Meaning: Sectorial section modulus Wcw.
            Valid range: > 0
            Source: section properties
        design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Ry or Ryf.
            Valid range: > 0
            Source: clause 6.1 or 8.4.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Absolute combined utilization.

    Assumptions:
        - Input signs already represent compression or tension at the checked point.

    Sign convention:
        - Positive minor-moment and bimoment terms cause compression.

    Unit convention:
        - N and mm.

    Applicability:
        - Clause 8.4.1 biaxial stability check.

    Limitations:
        - Does not derive section warping properties.

    Raises:
        ValueError: A denominator input is non-positive.
        TypeError: Non-real input.

    Examples:
        >>> lateral_torsional_combined_utilization_eq70(1e8, 0, 0, 0.8, 1e6, 5e5, 1e9, 250, 1.0)
        0.5

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_69_and_70
        Validation cases:
            - STAB-EQ-070

    Implementation notes:
        - The final absolute value provides a utilization magnitude while preserving term signs before summation.
        - Defaults must be explicit in the input configuration.
    """
    ry_gc = _positive(design_resistance_n_mm2, "design_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor")
    value = (
        _signed(major_moment_n_mm, "major_moment_n_mm") / (_positive(stability_coefficient_phi_b, "stability_coefficient_phi_b") * _positive(compressed_major_section_modulus_mm3, "compressed_major_section_modulus_mm3") * ry_gc)
        + _signed(minor_moment_n_mm, "minor_moment_n_mm") / (_positive(compressed_minor_section_modulus_mm3, "compressed_minor_section_modulus_mm3") * ry_gc)
        + _signed(bimoment_n_mm2, "bimoment_n_mm2") / (_positive(compressed_sectorial_section_modulus_mm4, "compressed_sectorial_section_modulus_mm4") * ry_gc)
    )
    return abs(value)



def crane_runway_lateral_torsional_stability_utilization(
    major_moment_n_mm: float,
    horizontal_moment_n_mm: float,
    bimoment_n_mm2: float,
    stability_coefficient_phi_b: float,
    compressed_major_section_modulus_mm3: float,
    upper_flange_minor_section_modulus_mm3: float,
    compressed_sectorial_section_modulus_mm4: float,
    design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Apply clause 8.4.3 by evaluating equation (70) with the horizontal moment and minor-axis modulus of the upper flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.3
        Annex: Ж
        Equation/Table: Equation (70) with crane-runway substitutions
        Audit ID: SP16-PROC-8.4.3-CRANE-STABILITY-ROUTING
        Normative status: normative procedure

    Mathematical form:
        Equation (70), where M_y is fully transferred to the upper flange and W_cy is the upper-flange minor-axis modulus.

    Parameters:
        major_moment_n_mm, horizontal_moment_n_mm, bimoment_n_mm2:
            Type: float
            Unit: N*mm or N*mm2 as named
            Meaning: Signed actions at the checked compressed point.
            Valid range: real
            Source: structural analysis
        stability_coefficient_phi_b, working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Phi_b and gamma_c.
            Valid range: > 0
            Source: Annex Ж and applicable clause
        compressed_major_section_modulus_mm3, upper_flange_minor_section_modulus_mm3, compressed_sectorial_section_modulus_mm4:
            Type: float
            Unit: mm3 or mm4 as named
            Meaning: Section moduli at the compressed point, with the minor-axis value belonging to the upper flange.
            Valid range: > 0
            Source: section properties
        design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design resistance R_y.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Clause-8.4.3 stability utilization.

    Assumptions:
        - The horizontal moment is fully transferred to the upper flange.

    Sign convention:
        - Signs are retained through equation (70), then the final magnitude is returned.

    Unit convention:
        - N and mm.

    Applicability:
        - I-section crane-runway beams under clause 8.4.3.

    Limitations:
        - The function does not calculate the horizontal crane action or upper-flange section properties.

    Raises:
        ValueError: A denominator input is non-positive.
        TypeError: A numerical input is not real.

    Examples:
        >>> crane_runway_lateral_torsional_stability_utilization(1e8, 2e7, 0, 0.8, 1e6, 5e5, 1e10, 355, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_crane_runway_stability_route
        Validation cases:
            - STAB-PROC-8.4.3

    Implementation notes:
        - This wrapper prevents the upper-flange substitution from being implicit at call sites.
        - Defaults must be explicit in the input configuration.
    """
    return lateral_torsional_combined_utilization_eq70(
        major_moment_n_mm,
        horizontal_moment_n_mm,
        bimoment_n_mm2,
        stability_coefficient_phi_b,
        compressed_major_section_modulus_mm3,
        upper_flange_minor_section_modulus_mm3,
        compressed_sectorial_section_modulus_mm4,
        design_resistance_n_mm2,
        working_condition_factor,
    )

def table_11_limit_eq71(flange_width_mm: float, flange_thickness_mm: float, flange_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the Table 11 limiting compressed-flange slenderness for load applied to the upper flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Equation (71), Table 11
        Audit ID: SP16-EQ-071
        Normative status: normative

    Mathematical form:
        lambda_ub = 0.35+0.0032 b/t+(0.76-0.02 b/t)b/h.

    Parameters:
        flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: b, t, and h from Table 11.
            Valid range: > 0; applicability 1<=h/b<=6 and b/t<=35
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Base limiting slenderness before notes 2 and 3 multipliers.

    Assumptions:
        - b/t below 15 is replaced by 15 as required by Note 1.

    Sign convention:
        - Geometric magnitudes are positive.

    Unit convention:
        - Consistent length units; mm used by API.

    Applicability:
        - Rolled or welded I beams covered by Table 11.

    Limitations:
        - Ratios outside the printed applicability range are rejected.

    Raises:
        ValueError: Geometry is outside Table 11 applicability.
        TypeError: Non-real input.

    Examples:
        >>> round(table_11_limit_eq71(300, 20, 600), 3)
        0.626

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_table_11_equations_and_routing
        Validation cases:
            - STAB-EQ-071

    Implementation notes:
        - Friction-connection and stress-level multipliers are applied by table_11_limit.
        - Defaults must be explicit in the input configuration.
    """
    b, t, h, bt = _table11_geometry(flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm)
    return 0.35 + 0.0032 * bt + (0.76 - 0.02 * bt) * b / h


def table_11_limit_eq72(flange_width_mm: float, flange_thickness_mm: float, flange_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the Table 11 limiting compressed-flange slenderness for load applied to the lower flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Equation (72), Table 11
        Audit ID: SP16-EQ-072
        Normative status: normative

    Mathematical form:
        lambda_ub = 0.57+0.0032 b/t+(0.92-0.02 b/t)b/h.

    Parameters:
        flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Table 11 geometry.
            Valid range: > 0 and within Table 11 ratios
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Base limiting slenderness.

    Assumptions:
        - b/t below 15 is replaced by 15.

    Sign convention:
        - Positive geometry.

    Unit convention:
        - mm.

    Applicability:
        - Table 11 lower-flange loading case.

    Limitations:
        - No extrapolation beyond printed ratios.

    Raises:
        ValueError: Invalid geometry or applicability.
        TypeError: Non-real input.

    Examples:
        >>> table_11_limit_eq72(300, 20, 600) > table_11_limit_eq71(300, 20, 600)
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_table_11_equations_and_routing
        Validation cases:
            - STAB-EQ-072

    Implementation notes:
        - Multipliers are applied by the routing function.
        - Defaults must be explicit in the input configuration.
    """
    b, t, h, bt = _table11_geometry(flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm)
    return 0.57 + 0.0032 * bt + (0.92 - 0.02 * bt) * b / h


def table_11_limit_eq73(flange_width_mm: float, flange_thickness_mm: float, flange_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the Table 11 limiting slenderness between braces or under pure bending.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Equation (73), Table 11
        Audit ID: SP16-EQ-073
        Normative status: normative

    Mathematical form:
        lambda_ub = 0.41+0.0032 b/t+(0.73-0.016 b/t)b/h.

    Parameters:
        flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Table 11 geometry.
            Valid range: > 0 and within Table 11 ratios
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Base limiting slenderness.

    Assumptions:
        - b/t below 15 is replaced by 15.

    Sign convention:
        - Positive geometry.

    Unit convention:
        - mm.

    Applicability:
        - Beam segment between restraints or pure bending.

    Limitations:
        - No extrapolation beyond printed ratios.

    Raises:
        ValueError: Invalid geometry or applicability.
        TypeError: Non-real input.

    Examples:
        >>> table_11_limit_eq73(300, 20, 600) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_table_11_equations_and_routing
        Validation cases:
            - STAB-EQ-073

    Implementation notes:
        - Multipliers are applied by the routing function.
        - Defaults must be explicit in the input configuration.
    """
    b, t, h, bt = _table11_geometry(flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm)
    return 0.41 + 0.0032 * bt + (0.73 - 0.016 * bt) * b / h


def _table11_geometry(b: float, t: float, h: float) -> tuple[float, float, float, float]:
    b = _positive(b, "flange_width_mm")
    t = _positive(t, "flange_thickness_mm")
    h = _positive(h, "flange_axis_spacing_mm")
    hb = h / b
    raw_bt = b / t
    if not 1.0 <= hb <= 6.0:
        raise ValueError("Table 11 requires 1 <= h/b <= 6")
    if raw_bt > 35.0:
        raise ValueError("Table 11 requires b/t <= 35; extrapolation is not permitted")
    return b, t, h, max(15.0, raw_bt)


def compressed_flange_equivalent_force_eq74(
    compressed_flange_area_mm2: float,
    web_area_mm2: float,
    compressed_flange_design_resistance_n_mm2: float,
    web_design_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the equivalent compressed-flange axial force used for bracing design.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.5
        Annex: None
        Equation/Table: Equation (74)
        Audit ID: SP16-EQ-074
        Normative status: normative

    Mathematical form:
        N = (Af*r + 0.25Aw)*Ryw, r=Ryf/Ryw>=1.

    Parameters:
        compressed_flange_area_mm2, web_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Areas Af and Aw.
            Valid range: >= 0, with positive total resistance contribution
            Source: section properties
        compressed_flange_design_resistance_n_mm2, web_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Ryf and Ryw.
            Valid range: > 0 and Ryf/Ryw>=1
            Source: clause 6.1

    Returns:
        Type: float
        Unit: N
        Meaning: Equivalent force N.

    Assumptions:
        - The flange identified is the compressed flange.

    Sign convention:
        - Returned force is a positive magnitude.

    Unit convention:
        - N and mm.

    Applicability:
        - Design of discrete or continuous compression-flange restraints.

    Limitations:
        - Connection-force distribution is separate.

    Raises:
        ValueError: Resistance ratio is below 1 or inputs are invalid.
        TypeError: Non-real input.

    Examples:
        >>> compressed_flange_equivalent_force_eq74(2000, 3000, 355, 355)
        976250.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_74_to_77
        Validation cases:
            - STAB-EQ-074

    Implementation notes:
        - The resistance ratio condition is enforced explicitly.
        - Defaults must be explicit in the input configuration.
    """
    af = _nonnegative(compressed_flange_area_mm2, "compressed_flange_area_mm2")
    aw = _nonnegative(web_area_mm2, "web_area_mm2")
    ryf = _positive(compressed_flange_design_resistance_n_mm2, "compressed_flange_design_resistance_n_mm2")
    ryw = _positive(web_design_resistance_n_mm2, "web_design_resistance_n_mm2")
    r = ryf / ryw
    if r < 1.0:
        raise ValueError("Equation (74) requires r = Ryf/Ryw >= 1")
    return (af * r + 0.25 * aw) * ryw


def continuous_bracing_force_per_length_eq75(fictitious_shear_force_n: float, beam_span_mm: float) -> float:
    """
    Summary:
        Calculate the fictitious transverse force per unit length for continuous flange restraint.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.5
        Annex: None
        Equation/Table: Equation (75)
        Audit ID: SP16-EQ-075
        Normative status: normative

    Mathematical form:
        q_fic = 3*Q_fic/l.

    Parameters:
        fictitious_shear_force_n:
            Type: float
            Unit: N
            Meaning: Qfic from equation (18) with phi=1 and N from equation (74).
            Valid range: >= 0
            Source: equations (18) and (74)
        beam_span_mm:
            Type: float
            Unit: mm
            Meaning: Beam span l.
            Valid range: > 0
            Source: geometry

    Returns:
        Type: float
        Unit: N/mm
        Meaning: Continuous restraint design force per unit length.

    Assumptions:
        - Qfic has been calculated with phi=1.

    Sign convention:
        - Positive force magnitude.

    Unit convention:
        - N/mm.

    Applicability:
        - Continuous compression-flange restraint.

    Limitations:
        - Does not distribute force to individual fasteners.

    Raises:
        ValueError: Invalid force or span.
        TypeError: Non-real input.

    Examples:
        >>> continuous_bracing_force_per_length_eq75(10000, 5000)
        6.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_74_to_77
        Validation cases:
            - STAB-EQ-075

    Implementation notes:
        - Span is explicit; no unit conversion is performed.
        - Defaults must be explicit in the input configuration.
    """
    return 3.0 * _nonnegative(fictitious_shear_force_n, "fictitious_shear_force_n") / _positive(beam_span_mm, "beam_span_mm")


def class_2_3_stability_reduction_eq76(c_1x: float, c_x: float) -> float:
    """
    Summary:
        Calculate the reduction multiplier for Table 11 limits in class-2 and class-3 beam regions.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.6
        Annex: None
        Equation/Table: Equation (76)
        Audit ID: SP16-EQ-076
        Normative status: normative

    Mathematical form:
        delta = 1-0.6*(c1x-1)/(cx-1).

    Parameters:
        c_1x, c_x:
            Type: float
            Unit: dimensionless
            Meaning: Coefficients satisfying 1<=c1x<=cx.
            Valid range: c_x>=1 and 1<=c_1x<=c_x
            Source: equation (77) and Table E.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Multiplier delta.

    Assumptions:
        - If cx=1, no plastic enhancement exists and delta is taken as 1 by the continuous limiting interpretation.

    Sign convention:
        - Dimensionless positive coefficients.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 8.4.6.

    Limitations:
        - Requires the correct Table E.1 coefficient.

    Raises:
        ValueError: Coefficient ordering is invalid.
        TypeError: Non-real input.

    Examples:
        >>> class_2_3_stability_reduction_eq76(1.5, 2.0)
        0.7

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_74_to_77
        Validation cases:
            - STAB-EQ-076

    Implementation notes:
        - The cx=1 branch avoids an undefined 0/0 expression.
        - Defaults must be explicit in the input configuration.
    """
    c1 = _positive(c_1x, "c_1x")
    cx = _positive(c_x, "c_x")
    if cx < 1.0 or c1 < 1.0 or c1 > cx:
        raise ValueError("Equation (76) requires 1 <= c_1x <= c_x and c_x >= 1")
    if math.isclose(cx, 1.0, abs_tol=1e-12):
        return 1.0
    return 1.0 - 0.6 * (c1 - 1.0) / (cx - 1.0)


def class_2_3_coefficient_eq77(
    bending_moment_n_mm: float,
    minimum_net_section_modulus_mm3: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    shear_reduction_beta: float,
    plastic_coefficient_cx: float,
) -> float:
    """
    Summary:
        Calculate c1x as the larger clause-8.4.6 expression, bounded to the required interval.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.6
        Annex: None
        Equation/Table: Equation (77)
        Audit ID: SP16-EQ-077
        Normative status: normative

    Mathematical form:
        c1x = max(Mx/(Wxn Ry gamma_c), beta*c_x), constrained to 1<=c1x<=c_x.

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Bending-moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        minimum_net_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Wxn,min.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Ry.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor, shear_reduction_beta, plastic_coefficient_cx:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c, beta from equation (52), and cx from Table E.1.
            Valid range: gamma_c>0, beta>=0, cx>=1
            Source: applicable clause, equation (52), Table E.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Bounded coefficient c1x.

    Assumptions:
        - The Table E.1 coefficient is applicable to the section and loading.

    Sign convention:
        - Moment magnitude is non-negative.

    Unit convention:
        - N and mm.

    Applicability:
        - Clause 8.4.6 class-2 and class-3 stability limits.

    Limitations:
        - Does not calculate beta or cx.

    Raises:
        ValueError: Invalid inputs or cx below 1.
        TypeError: Non-real input.

    Examples:
        >>> class_2_3_coefficient_eq77(250000000, 1000000, 250, 1, 0.8, 1.5)
        1.2

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_equations_74_to_77
        Validation cases:
            - STAB-EQ-077

    Implementation notes:
        - The printed interval is enforced by lower and upper bounds after selecting the larger expression.
        - Defaults must be explicit in the input configuration.
    """
    term_m = _nonnegative(bending_moment_n_mm, "bending_moment_n_mm") / (
        _positive(minimum_net_section_modulus_mm3, "minimum_net_section_modulus_mm3")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )
    beta = _nonnegative(shear_reduction_beta, "shear_reduction_beta")
    cx = _positive(plastic_coefficient_cx, "plastic_coefficient_cx")
    if cx < 1.0:
        raise ValueError("Equation (77) requires c_x >= 1")
    return min(cx, max(1.0, term_m, beta * cx))


def compressed_flange_relative_slenderness(
    effective_length_mm: float,
    flange_width_mm: float,
    compressed_flange_design_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the compressed-flange relative slenderness used by clause 8.4.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Unnumbered definition before Table 11
        Audit ID: SP16-PROC-8.4.4-TABLE-11-ROUTING
        Normative status: normative

    Mathematical form:
        lambda_b = (l_ef/b)*sqrt(Ryf/E).

    Parameters:
        effective_length_mm, flange_width_mm:
            Type: float
            Unit: mm
            Meaning: Unbraced length and compressed-flange width.
            Valid range: > 0
            Source: geometry and clause 8.4.2
        compressed_flange_design_resistance_n_mm2, elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Ryf and E.
            Valid range: > 0
            Source: material properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative compressed-flange slenderness.

    Assumptions:
        - Consistent units are used.

    Sign convention:
        - Positive magnitudes.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Table 11 exemption route.

    Limitations:
        - Does not determine effective length.

    Raises:
        ValueError: Non-positive input.
        TypeError: Non-real input.

    Examples:
        >>> compressed_flange_relative_slenderness(3000, 300, 355, 206000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_table_11_equations_and_routing
        Validation cases:
            - STAB-PROC-LAMBDA-B

    Implementation notes:
        - No unit conversion is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(effective_length_mm, "effective_length_mm") / _positive(flange_width_mm, "flange_width_mm") * math.sqrt(
        _positive(compressed_flange_design_resistance_n_mm2, "compressed_flange_design_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    )


def table_11_limit(
    load_position: str,
    flange_width_mm: float,
    flange_thickness_mm: float,
    flange_axis_spacing_mm: float,
    friction_flange_connections: bool = False,
    compressed_flange_design_resistance_n_mm2: float | None = None,
    compressed_flange_stress_n_mm2: float | None = None,
) -> float:
    """
    Summary:
        Route Table 11 equations and apply the printed connection and stress-level multipliers.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Table 11, equations (71)-(73), Notes 1-3
        Audit ID: SP16-PROC-8.4.4-TABLE-11-ROUTING
        Normative status: normative

    Mathematical form:
        Base equation selected by load position; optional factors 1.2 and sqrt(Ryf/sigma).

    Parameters:
        load_position:
            Type: str
            Unit: categorical
            Meaning: upper_flange, lower_flange, or between_braces_or_pure_bending.
            Valid range: listed values
            Source: loading arrangement
        flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Table 11 geometry.
            Valid range: Table 11 applicability
            Source: section geometry
        friction_flange_connections:
            Type: bool
            Unit: dimensionless
            Meaning: Apply Note 2 factor 1.2.
            Valid range: true or false
            Source: connection definition
        compressed_flange_design_resistance_n_mm2, compressed_flange_stress_n_mm2:
            Type: float or None
            Unit: N/mm2
            Meaning: Ryf and sigma for Note 3; both omitted or both positive.
            Valid range: > 0 when supplied
            Source: material and analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Final limiting slenderness.

    Assumptions:
        - The load-position category is selected from the standard.

    Sign convention:
        - Stress is a positive compression magnitude.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Clause 8.4.4 Table 11 route.

    Limitations:
        - Zero-stress Note 3 cases are not represented as infinity; omit the multiplier when stability is non-governing.

    Raises:
        ValueError: Invalid category, geometry, or partial Note 3 data.
        TypeError: Invalid Boolean or numeric input.

    Examples:
        >>> table_11_limit("upper_flange", 300, 20, 600) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_table_11_equations_and_routing
        Validation cases:
            - STAB-TBL-011

    Implementation notes:
        - Table notes are explicit inputs; no connection type is inferred.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(friction_flange_connections, bool):
        raise TypeError("friction_flange_connections must be bool")
    functions = {
        "upper_flange": table_11_limit_eq71,
        "lower_flange": table_11_limit_eq72,
        "between_braces_or_pure_bending": table_11_limit_eq73,
    }
    try:
        value = functions[load_position](flange_width_mm, flange_thickness_mm, flange_axis_spacing_mm)
    except KeyError as exc:
        raise ValueError(f"Unsupported Table 11 load_position: {load_position}") from exc
    if friction_flange_connections:
        value *= 1.2
    if (compressed_flange_design_resistance_n_mm2 is None) != (compressed_flange_stress_n_mm2 is None):
        raise ValueError("Both Ryf and sigma must be supplied for Table 11 Note 3")
    if compressed_flange_design_resistance_n_mm2 is not None:
        value *= math.sqrt(
            _positive(compressed_flange_design_resistance_n_mm2, "compressed_flange_design_resistance_n_mm2")
            / _positive(compressed_flange_stress_n_mm2, "compressed_flange_stress_n_mm2")
        )
    return value


def effective_length_by_restraint(
    span_or_cantilever_length_mm: float,
    restraint_point_distances_mm: list[float] | None,
    is_cantilever: bool,
    compression_flange_restrained_at_tip: bool,
) -> float:
    """
    Summary:
        Determine the clause-8.4.2 effective length from compression-flange restraint spacing.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.2
        Annex: None
        Equation/Table: Unnumbered effective-length procedure
        Audit ID: SP16-PROC-8.4.2-EFFECTIVE-LENGTH
        Normative status: normative

    Mathematical form:
        Beam: maximum spacing between restraint points, or span without restraints; cantilever: full length unless restrained at the tip, then maximum spacing.

    Parameters:
        span_or_cantilever_length_mm:
            Type: float
            Unit: mm
            Meaning: Span or cantilever length.
            Valid range: > 0
            Source: geometry
        restraint_point_distances_mm:
            Type: list[float] or None
            Unit: mm
            Meaning: Ordered distances from the member start, including end restraint points where present.
            Valid range: within member length
            Source: restraint layout
        is_cantilever, compression_flange_restrained_at_tip:
            Type: bool
            Unit: dimensionless
            Meaning: Member and tip-restraint flags.
            Valid range: true or false
            Source: structural system

    Returns:
        Type: float
        Unit: mm
        Meaning: Effective length lef.

    Assumptions:
        - Each listed point restrains lateral movement of the compressed flange.

    Sign convention:
        - Positive distances.

    Unit convention:
        - mm.

    Applicability:
        - Clause 8.4.2.

    Limitations:
        - Restraint stiffness is not assessed.

    Raises:
        ValueError: Invalid or unordered points.
        TypeError: Invalid flags or list values.

    Examples:
        >>> effective_length_by_restraint(6000, [0, 2000, 4000, 6000], False, False)
        2000.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_effective_length_and_exemption
        Validation cases:
            - STAB-PROC-8.4.2

    Implementation notes:
        - The function uses the largest unbraced segment.
        - Defaults must be explicit in the input configuration.
    """
    length = _positive(span_or_cantilever_length_mm, "span_or_cantilever_length_mm")
    if not isinstance(is_cantilever, bool) or not isinstance(compression_flange_restrained_at_tip, bool):
        raise TypeError("restraint flags must be bool")
    points = [] if restraint_point_distances_mm is None else [_nonnegative(x, "restraint_point") for x in restraint_point_distances_mm]
    if any(x > length for x in points) or points != sorted(points) or len(set(points)) != len(points):
        raise ValueError("restraint points must be unique, ordered, and within the member length")
    if is_cantilever and not compression_flange_restrained_at_tip:
        return length
    required = [0.0, length]
    all_points = sorted(set(points + required))
    return max(b - a for a, b in zip(all_points, all_points[1:]))


def lateral_stability_check_exemption(
    rigid_continuous_deck: bool,
    actual_relative_flange_slenderness: float,
    limiting_relative_flange_slenderness: float,
    tension_to_compression_flange_width_ratio: float,
) -> dict[str, Any]:
    """
    Summary:
        Determine whether the clause-8.4.4 lateral-stability check may be omitted.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.4
        Annex: None
        Equation/Table: Exemption alternatives a and b
        Audit ID: SP16-PROC-8.4.4-STABILITY-EXEMPTION
        Normative status: normative

    Mathematical form:
        Exempt if rigid deck is present, or lambda_b<=lambda_ub with tension/compression flange width ratio>=0.75.

    Parameters:
        rigid_continuous_deck:
            Type: bool
            Unit: dimensionless
            Meaning: Whether a continuously connected rigid deck restrains the compressed flange.
            Valid range: true or false
            Source: structural detailing
        actual_relative_flange_slenderness, limiting_relative_flange_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual and Table 11 limiting values.
            Valid range: >= 0
            Source: calculation
        tension_to_compression_flange_width_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Width ratio required to be at least 0.75 for route b.
            Valid range: >= 0
            Source: section geometry

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Exemption status and governing route.

    Assumptions:
        - The deck connection satisfies the clause and friction is not relied upon.

    Sign convention:
        - Non-negative ratios.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Class-1 beams and applicable class-2 bimetal beams.

    Limitations:
        - Sandwich-panel qualification remains an external engineering demonstration.

    Raises:
        ValueError: Negative ratio.
        TypeError: rigid_continuous_deck is not bool.

    Examples:
        >>> lateral_stability_check_exemption(True, 10, 0, 0)["exempt"]
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_effective_length_and_exemption
        Validation cases:
            - STAB-PROC-8.4.4

    Implementation notes:
        - The function does not treat friction as a restraint mechanism.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(rigid_continuous_deck, bool):
        raise TypeError("rigid_continuous_deck must be bool")
    actual = _nonnegative(actual_relative_flange_slenderness, "actual_relative_flange_slenderness")
    limit = _nonnegative(limiting_relative_flange_slenderness, "limiting_relative_flange_slenderness")
    ratio = _nonnegative(tension_to_compression_flange_width_ratio, "tension_to_compression_flange_width_ratio")
    if rigid_continuous_deck:
        return {"exempt": True, "route": "rigid_continuous_deck"}
    return {"exempt": actual <= limit and ratio >= 0.75, "route": "table_11", "slenderness_ok": actual <= limit, "flange_width_ratio_ok": ratio >= 0.75}


def discrete_bracing_fictitious_force(
    equivalent_force_n: float,
    effective_length_mm: float,
    compressed_flange_radius_of_gyration_mm: float,
    elastic_modulus_n_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> dict[str, float]:
    """
    Summary:
        Calculate the discrete-restraint fictitious force using equation (18) and the clause-8.4.5 type-b stability coefficient.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.4.5
        Annex: None
        Equation/Table: Equations (18), (74), Table 7 type b
        Audit ID: SP16-PROC-8.4.5-DISCRETE-BRACING-FORCE
        Normative status: normative

    Mathematical form:
        lambda=lef/i; lambda_bar=lambda*sqrt(Ry/E); phi=equations (8)-(9), type b; Qfic=equation (18).

    Parameters:
        equivalent_force_n:
            Type: float
            Unit: N
            Meaning: N from equation (74).
            Valid range: >= 0
            Source: equation (74)
        effective_length_mm, compressed_flange_radius_of_gyration_mm:
            Type: float
            Unit: mm
            Meaning: Unbraced length and flange radius of gyration.
            Valid range: > 0
            Source: geometry
        elastic_modulus_n_mm2, design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: E and Ry.
            Valid range: > 0
            Source: material properties

    Returns:
        Type: dict[str, float]
        Unit: mixed
        Meaning: Geometric slenderness, relative slenderness, phi, and Qfic.

    Assumptions:
        - Type-b coefficients apply as required by clause 8.4.5.

    Sign convention:
        - Positive force magnitude.

    Unit convention:
        - N and mm.

    Applicability:
        - Discrete compression-flange restraint design.

    Limitations:
        - Does not check restraint stiffness or connection resistance.

    Raises:
        ValueError: Invalid geometry or material input.
        TypeError: Non-real input.

    Examples:
        >>> discrete_bracing_fictitious_force(1e6, 3000, 100, 206000, 355)["q_fictitious_n"] > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_bracing_force_procedures
        Validation cases:
            - STAB-PROC-8.4.5-DISCRETE

    Implementation notes:
        - The existing audited equation (18) implementation is reused.
        - Defaults must be explicit in the input configuration.
    """
    from .axial_members import central_compression_stability_coefficient
    n = _nonnegative(equivalent_force_n, "equivalent_force_n")
    slenderness = _positive(effective_length_mm, "effective_length_mm") / _positive(compressed_flange_radius_of_gyration_mm, "compressed_flange_radius_of_gyration_mm")
    lambda_bar = slenderness * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))
    phi = central_compression_stability_coefficient(lambda_bar, "b")
    return {"geometric_slenderness": slenderness, "relative_slenderness": lambda_bar, "phi": phi, "q_fictitious_n": fictitious_shear_force_n(n, elastic_modulus_n_mm2, design_yield_resistance_n_mm2, phi)}


def table_12_c_cr_coefficient(connection_type: str, delta_value: float) -> float:
    """
    Summary:
        Look up Table 12 coefficient Ccr at an exact printed delta node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.4
        Annex: None
        Equation/Table: Table 12
        Audit ID: SP16-PROC-TABLE-12-LOOKUP
        Normative status: normative data

    Mathematical form:
        Exact-node lookup; friction connections use constant 35.2.

    Parameters:
        connection_type:
            Type: str
            Unit: categorical
            Meaning: welded or friction.
            Valid range: welded, friction
            Source: detailing
        delta_value:
            Type: float
            Unit: dimensionless
            Meaning: Delta from equation (84).
            Valid range: printed nodes for welded; any finite value for friction
            Source: clause 8.5.4

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Ccr coefficient.

    Assumptions:
        - No interpolation rule is stated in the supplied table.

    Sign convention:
        - Delta is non-negative.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Future clause-8.5 web-stability calculations.

    Limitations:
        - Welded lookup is exact-node only.

    Raises:
        ValueError: Unsupported type or non-node delta.
        TypeError: Non-real input.

    Examples:
        >>> table_12_c_cr_coefficient("welded", 2.0)
        33.3

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_tables_12_and_13
        Validation cases:
            - STAB-TBL-012

    Implementation notes:
        - Table 12 is implemented as data in this release without implementing clause 8.5 equations.
        - Defaults must be explicit in the input configuration.
    """
    delta = _nonnegative(delta_value, "delta_value")
    if connection_type == "friction":
        return float(_TABLE_12["friction_constant"])
    if connection_type != "welded":
        raise ValueError("connection_type must be 'welded' or 'friction'")
    keys = _TABLE_12["welded_nodes"]
    if delta <= 0.8:
        return float(keys["le_0.8"])
    if delta >= 30.0:
        return float(keys["ge_30.0"])
    key = f"{delta:.1f}"
    if key not in keys:
        raise ValueError("Table 12 welded lookup is exact-node only; no interpolation rule is invented")
    return float(keys[key])


def table_13_beta(case_id: str) -> float:
    """
    Summary:
        Look up the compressed-flange working-condition coefficient beta from Table 13.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.5.4
        Annex: None
        Equation/Table: Table 13
        Audit ID: SP16-PROC-TABLE-13-LOOKUP
        Normative status: normative data

    Mathematical form:
        Categorical lookup; unbounded cases are represented by positive infinity.

    Parameters:
        case_id:
            Type: str
            Unit: categorical
            Meaning: crane_rail_not_welded, crane_rail_welded, other_continuous_slab_support, other_case, or crane_tension_flange_note.
            Valid range: listed identifiers
            Source: beam detailing

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 13 beta.

    Assumptions:
        - The user selects the correct table row.

    Sign convention:
        - Positive coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Future clause-8.5 web-stability calculations.

    Limitations:
        - Infinity is a data marker for the printed infinity symbol, not a numerical design result.

    Raises:
        ValueError: Unsupported case identifier.

    Examples:
        >>> table_13_beta("crane_rail_not_welded")
        2.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_tables_12_and_13
        Validation cases:
            - STAB-TBL-013

    Implementation notes:
        - Table 13 is exposed now for traceability; equation (84) is outside this release scope.
        - Defaults must be explicit in the input configuration.
    """
    try:
        value = _TABLE_13["cases"][case_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported Table 13 case_id: {case_id}") from exc
    return math.inf if value == "infinity" else float(value)


# Annex Zh numbered equations and table procedures

def annex_zh_phi_b_eq_zh1(phi_1: float) -> float:
    """
    Summary:
        Return phi_b equal to phi_1 when phi_1 does not exceed 0.85.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.2
        Annex: Ж
        Equation/Table: Equation (Ж.1)
        Audit ID: SP16-EQ-Ж-001
        Normative status: annex normative procedure

    Mathematical form:
        phi_b=phi_1 for phi_1<=0.85.

    Parameters:
        phi_1:
            Type: float
            Unit: dimensionless
            Meaning: Intermediate stability coefficient.
            Valid range: 0<=phi_1<=0.85
            Source: equation (Ж.3)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Stability coefficient phi_b.

    Assumptions:
        - Doubly symmetric I beam or cantilever.

    Sign convention:
        - Non-negative coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Annex Ж.2 lower branch.

    Limitations:
        - Does not calculate phi_1.

    Raises:
        ValueError: phi_1 is outside the branch.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_phi_b_eq_zh1(0.8)
        0.8

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_1_to_5
        Validation cases:
            - ZH-EQ-001

    Implementation notes:
        - Branch applicability is enforced.
        - Defaults must be explicit in the input configuration.
    """
    value = _nonnegative(phi_1, "phi_1")
    if value > 0.85:
        raise ValueError("Equation (Ж.1) applies only when phi_1 <= 0.85")
    return value


def annex_zh_phi_b_eq_zh2(phi_1: float) -> float:
    """
    Summary:
        Calculate phi_b from the upper phi_1 branch and cap it at one.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.2
        Annex: Ж
        Equation/Table: Equation (Ж.2)
        Audit ID: SP16-EQ-Ж-002
        Normative status: annex normative procedure

    Mathematical form:
        phi_b=min(1,0.68+0.21phi_1), phi_1>0.85.

    Parameters:
        phi_1:
            Type: float
            Unit: dimensionless
            Meaning: Intermediate stability coefficient.
            Valid range: >0.85
            Source: equation (Ж.3)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped phi_b.

    Assumptions:
        - Doubly symmetric I beam or cantilever.

    Sign convention:
        - Positive coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Annex Ж.2 upper branch.

    Limitations:
        - Does not calculate phi_1.

    Raises:
        ValueError: phi_1 is outside the branch.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_phi_b_eq_zh2(1.0)
        0.89

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_1_to_5
        Validation cases:
            - ZH-EQ-002

    Implementation notes:
        - The explicit cap at one is applied.
        - Defaults must be explicit in the input configuration.
    """
    value = _positive(phi_1, "phi_1")
    if value <= 0.85:
        raise ValueError("Equation (Ж.2) applies only when phi_1 > 0.85")
    return min(1.0, 0.68 + 0.21 * value)


def annex_zh_phi1_eq_zh3(
    psi: float,
    minor_axis_inertia_mm4: float,
    major_axis_inertia_mm4: float,
    section_height_mm: float,
    effective_length_mm: float,
    elastic_modulus_n_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate phi_1 for a doubly symmetric I beam or cantilever.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.2
        Annex: Ж
        Equation/Table: Equation (Ж.3)
        Audit ID: SP16-EQ-Ж-003
        Normative status: annex normative procedure

    Mathematical form:
        phi_1=psi*(Iy/Ix)*(h/lef)^2*(E/Ry).

    Parameters:
        psi:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient from Tables Ж.1 or Ж.2.
            Valid range: >0
            Source: Annex Ж.3
        minor_axis_inertia_mm4, major_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Iy and Ix.
            Valid range: >0
            Source: section properties
        section_height_mm, effective_length_mm:
            Type: float
            Unit: mm
            Meaning: h and lef.
            Valid range: >0
            Source: geometry and clause 8.4.2
        elastic_modulus_n_mm2, design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: E and Ry.
            Valid range: >0
            Source: material properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Intermediate coefficient phi_1.

    Assumptions:
        - Load acts in the plane of maximum stiffness and support sections are restrained against lateral movement and twist.

    Sign convention:
        - Positive properties.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Doubly symmetric I sections and channel conversion route.

    Limitations:
        - Psi must be obtained from the correct load/restraint table row.

    Raises:
        ValueError: Non-positive input.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_phi1_eq_zh3(10, 1e8, 1e10, 500, 5000, 206000, 355) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_1_to_5
        Validation cases:
            - ZH-EQ-003

    Implementation notes:
        - No cap is applied here; equations (Ж.1) or (Ж.2) provide phi_b.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(psi, "psi") * _positive(minor_axis_inertia_mm4, "minor_axis_inertia_mm4") / _positive(major_axis_inertia_mm4, "major_axis_inertia_mm4") * (_positive(section_height_mm, "section_height_mm") / _positive(effective_length_mm, "effective_length_mm")) ** 2 * _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2") / _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")


def annex_zh_alpha_rolled_eq_zh4(
    torsional_inertia_mm4: float,
    minor_axis_inertia_mm4: float,
    effective_length_mm: float,
    section_height_mm: float,
    compression_flange_braced_in_span: bool,
) -> float:
    """
    Summary:
        Calculate alpha for a rolled I section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.3
        Annex: Ж
        Equation/Table: Equation (Ж.4)
        Audit ID: SP16-EQ-Ж-004
        Normative status: annex normative procedure

    Mathematical form:
        alpha=k*(Jt/Iy)*(lef/h)^2, k=1 without span restraints and 1.54 with restraints.

    Parameters:
        torsional_inertia_mm4, minor_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Jt and Iy.
            Valid range: >0
            Source: section properties and Annex Д
        effective_length_mm, section_height_mm:
            Type: float
            Unit: mm
            Meaning: lef and h.
            Valid range: >0
            Source: geometry
        compression_flange_braced_in_span:
            Type: bool
            Unit: dimensionless
            Meaning: Select k=1.54 instead of 1.
            Valid range: true or false
            Source: restraint layout

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Alpha for Tables Ж.1 or Ж.2.

    Assumptions:
        - Section is a rolled I profile.

    Sign convention:
        - Positive properties.

    Unit convention:
        - Consistent mm units.

    Applicability:
        - Annex Ж.3a.

    Limitations:
        - Jt calculation is external.

    Raises:
        ValueError: Non-positive input.
        TypeError: Invalid flag or non-real input.

    Examples:
        >>> annex_zh_alpha_rolled_eq_zh4(1e6, 1e8, 5000, 500, False)
        1.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_1_to_5
        Validation cases:
            - ZH-EQ-004

    Implementation notes:
        - k is selected only from the explicit restraint flag.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(compression_flange_braced_in_span, bool):
        raise TypeError("compression_flange_braced_in_span must be bool")
    k = 1.54 if compression_flange_braced_in_span else 1.0
    return k * _positive(torsional_inertia_mm4, "torsional_inertia_mm4") / _positive(minor_axis_inertia_mm4, "minor_axis_inertia_mm4") * (_positive(effective_length_mm, "effective_length_mm") / _positive(section_height_mm, "section_height_mm")) ** 2


def annex_zh_alpha_built_up_eq_zh5(
    effective_length_mm: float,
    flange_thickness_mm: float,
    effective_profile_height_mm: float,
    flange_width_mm: float,
    web_thickness_mm: float,
    compression_flange_braced_in_span: bool,
) -> float:
    """
    Summary:
        Calculate alpha for a built-up I section with welded or friction flange connections.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.3
        Annex: Ж
        Equation/Table: Equation (Ж.5)
        Audit ID: SP16-EQ-Ж-005
        Normative status: annex normative procedure

    Mathematical form:
        alpha=k*(lef*tf/(hm*bf))^2*(1+0.5*hm*tw^3/(bf*tf^3)), k=4 or 8.

    Parameters:
        effective_length_mm, flange_thickness_mm, effective_profile_height_mm, flange_width_mm, web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: lef, tf, hm, bf, and tw.
            Valid range: >0
            Source: geometry
        compression_flange_braced_in_span:
            Type: bool
            Unit: dimensionless
            Meaning: Select k=8 instead of 4 and the corresponding hm definition.
            Valid range: true or false
            Source: restraint layout

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Alpha for Annex Ж tables.

    Assumptions:
        - The supplied hm already follows the annex definition for the restraint condition.

    Sign convention:
        - Positive geometry.

    Unit convention:
        - mm.

    Applicability:
        - Built-up I sections from plates.

    Limitations:
        - hm is not derived from overall geometry by this function.

    Raises:
        ValueError: Non-positive geometry.
        TypeError: Invalid flag or non-real input.

    Examples:
        >>> annex_zh_alpha_built_up_eq_zh5(5000, 20, 500, 300, 10, False) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_1_to_5
        Validation cases:
            - ZH-EQ-005

    Implementation notes:
        - The equation is transcribed directly and dimensionally checked.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(compression_flange_braced_in_span, bool):
        raise TypeError("compression_flange_braced_in_span must be bool")
    lef = _positive(effective_length_mm, "effective_length_mm")
    tf = _positive(flange_thickness_mm, "flange_thickness_mm")
    hm = _positive(effective_profile_height_mm, "effective_profile_height_mm")
    bf = _positive(flange_width_mm, "flange_width_mm")
    tw = _positive(web_thickness_mm, "web_thickness_mm")
    k = 8.0 if compression_flange_braced_in_span else 4.0
    return k * (lef * tf / (hm * bf)) ** 2 * (1.0 + 0.5 * hm * tw ** 3 / (bf * tf ** 3))


def annex_zh_monosymmetric_phi1_eq_zh6(psi_a: float, iy_mm4: float, ix_mm4: float, h_mm: float, h1_mm: float, lef_mm: float, e_n_mm2: float, ry_n_mm2: float) -> float:
    """
    Summary:
        Calculate phi_1 for a monosymmetric I section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.4
        Annex: Ж
        Equation/Table: Equation (Ж.6)
        Audit ID: SP16-EQ-Ж-006
        Normative status: annex normative procedure

    Mathematical form:
        phi_1=psi_a*(Iy/Ix)*(2*h*h1/lef^2)*(E/Ry).

    Parameters:
        psi_a, iy_mm4, ix_mm4, h_mm, h1_mm, lef_mm, e_n_mm2, ry_n_mm2:
            Type: float
            Unit: dimensionless, mm4, mm, and N/mm2 as named
            Meaning: Annex Ж monosymmetric-section inputs.
            Valid range: >0
            Source: section properties and equations (Ж.9)-(Ж.13)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Intermediate phi_1.

    Assumptions:
        - h1 is the distance to the more developed flange axis.

    Sign convention:
        - Positive properties.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Monosymmetric I sections.

    Limitations:
        - Does not choose the compressed flange.

    Raises:
        ValueError: Non-positive input.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_monosymmetric_phi1_eq_zh6(5, 1e8, 1e10, 500, 300, 5000, 206000, 355) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-006

    Implementation notes:
        - Named inputs preserve unit traceability.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(psi_a, "psi_a") * _positive(iy_mm4, "iy_mm4") / _positive(ix_mm4, "ix_mm4") * 2.0 * _positive(h_mm, "h_mm") * _positive(h1_mm, "h1_mm") / _positive(lef_mm, "lef_mm") ** 2 * _positive(e_n_mm2, "e_n_mm2") / _positive(ry_n_mm2, "ry_n_mm2")


def annex_zh_monosymmetric_phi2_eq_zh7(psi_a: float, iy_mm4: float, ix_mm4: float, h_mm: float, h2_mm: float, lef_mm: float, e_n_mm2: float, ry_n_mm2: float) -> float:
    """
    Summary:
        Calculate phi_2 for a monosymmetric I section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.4
        Annex: Ж
        Equation/Table: Equation (Ж.7)
        Audit ID: SP16-EQ-Ж-007
        Normative status: annex normative procedure

    Mathematical form:
        phi_2=psi_a*(Iy/Ix)*(2*h*h2/lef^2)*(E/Ry).

    Parameters:
        psi_a, iy_mm4, ix_mm4, h_mm, h2_mm, lef_mm, e_n_mm2, ry_n_mm2:
            Type: float
            Unit: dimensionless, mm4, mm, and N/mm2 as named
            Meaning: Annex Ж monosymmetric-section inputs.
            Valid range: >0
            Source: section properties and equations (Ж.9)-(Ж.13)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Intermediate phi_2.

    Assumptions:
        - h2 is the distance to the less developed flange axis.

    Sign convention:
        - Positive properties.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Monosymmetric I sections.

    Limitations:
        - Does not apply the Ж.6 reduction for a less developed compressed flange.

    Raises:
        ValueError: Non-positive input.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_monosymmetric_phi2_eq_zh7(5, 1e8, 1e10, 500, 200, 5000, 206000, 355) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-007

    Implementation notes:
        - Named inputs preserve unit traceability.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(psi_a, "psi_a") * _positive(iy_mm4, "iy_mm4") / _positive(ix_mm4, "ix_mm4") * 2.0 * _positive(h_mm, "h_mm") * _positive(h2_mm, "h2_mm") / _positive(lef_mm, "lef_mm") ** 2 * _positive(e_n_mm2, "e_n_mm2") / _positive(ry_n_mm2, "ry_n_mm2")


def annex_zh_flange_inertia_ratio_n_eq_zh8(more_developed_flange_inertia_mm4: float, less_developed_flange_inertia_mm4: float) -> float:
    """
    Summary:
        Calculate the monosymmetric flange-inertia ratio n.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.4
        Annex: Ж
        Equation/Table: Equation (Ж.8)
        Audit ID: SP16-EQ-Ж-008
        Normative status: annex normative procedure

    Mathematical form:
        n=I1/(I1+I2).

    Parameters:
        more_developed_flange_inertia_mm4, less_developed_flange_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I1 and I2 about the section symmetry axis.
            Valid range: >0
            Source: flange section properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Ratio n between 0 and 1.

    Assumptions:
        - I1 corresponds to the more developed flange.

    Sign convention:
        - Positive inertias.

    Unit convention:
        - mm4.

    Applicability:
        - Annex Ж monosymmetric I sections.

    Limitations:
        - Does not verify which flange is more developed.

    Raises:
        ValueError: Non-positive inertia.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_flange_inertia_ratio_n_eq_zh8(3, 1)
        0.75

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-008

    Implementation notes:
        - The caller remains responsible for flange classification.
        - Defaults must be explicit in the input configuration.
    """
    i1 = _positive(more_developed_flange_inertia_mm4, "more_developed_flange_inertia_mm4")
    i2 = _positive(less_developed_flange_inertia_mm4, "less_developed_flange_inertia_mm4")
    return i1 / (i1 + i2)


def annex_zh_psi_a_eq_zh9(coefficient_b: float, coefficient_c: float, coefficient_d: float) -> float:
    """
    Summary:
        Calculate the monosymmetric-section coefficient psi_a.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.4-Ж.5
        Annex: Ж
        Equation/Table: Equation (Ж.9)
        Audit ID: SP16-EQ-Ж-009
        Normative status: annex normative procedure

    Mathematical form:
        psi_a=(B+sqrt(B^2+C))*D.

    Parameters:
        coefficient_b:
            Type: float
            Unit: dimensionless
            Meaning: B from Table Ж.4.
            Valid range: real
            Source: Table Ж.4
        coefficient_c, coefficient_d:
            Type: float
            Unit: dimensionless
            Meaning: C and D from Table Ж.5.
            Valid range: C>=0 and D>0
            Source: Table Ж.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Psi_a.

    Assumptions:
        - B, C, and D correspond to the same loading case.

    Sign convention:
        - B may be signed according to Table Ж.4.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Monosymmetric I and T sections.

    Limitations:
        - Ж.6 modifiers are applied separately.

    Raises:
        ValueError: Invalid C or D.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_psi_a_eq_zh9(0, 1, 2)
        2.0

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-009

    Implementation notes:
        - Signed B is retained.
        - Defaults must be explicit in the input configuration.
    """
    b = _signed(coefficient_b, "coefficient_b")
    c = _nonnegative(coefficient_c, "coefficient_c")
    d = _positive(coefficient_d, "coefficient_d")
    return (b + math.sqrt(b * b + c)) * d


def annex_zh_delta_eq_zh10(n_ratio: float, beta_value: float) -> float:
    """
    Summary:
        Calculate delta for Table Ж.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Equation (Ж.10)
        Audit ID: SP16-EQ-Ж-010
        Normative status: annex normative procedure

    Mathematical form:
        delta=n+0.734 beta.

    Parameters:
        n_ratio, beta_value:
            Type: float
            Unit: dimensionless
            Meaning: n and beta.
            Valid range: n in [0,1], beta real
            Source: equations (Ж.8) and (Ж.12)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Delta.

    Assumptions:
        - Inputs correspond to the same section.

    Sign convention:
        - Beta may be signed by its formula.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.4.

    Limitations:
        - None beyond input classification.

    Raises:
        ValueError: n outside [0,1].
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_delta_eq_zh10(0.8, 0.1)
        0.8734000000000001

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-010

    Implementation notes:
        - No rounding is applied.
        - Defaults must be explicit in the input configuration.
    """
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0, 1]")
    return n + 0.734 * _signed(beta_value, "beta_value")


def annex_zh_mu_eq_zh11(n_ratio: float, beta_value: float) -> float:
    """
    Summary:
        Calculate mu for Table Ж.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Equation (Ж.11)
        Audit ID: SP16-EQ-Ж-011
        Normative status: annex normative procedure

    Mathematical form:
        mu=n+1.145 beta.

    Parameters:
        n_ratio, beta_value:
            Type: float
            Unit: dimensionless
            Meaning: n and beta.
            Valid range: n in [0,1], beta real
            Source: equations (Ж.8) and (Ж.12)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Mu.

    Assumptions:
        - Inputs correspond to the same section.

    Sign convention:
        - Beta may be signed.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.4.

    Limitations:
        - None beyond input classification.

    Raises:
        ValueError: n outside [0,1].
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_mu_eq_zh11(0.8, 0.1)
        0.9145000000000001

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-011

    Implementation notes:
        - No rounding is applied.
        - Defaults must be explicit in the input configuration.
    """
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0, 1]")
    return n + 1.145 * _signed(beta_value, "beta_value")


def annex_zh_beta_eq_zh12(n_ratio: float, h1_mm: float, h_mm: float) -> float:
    """
    Summary:
        Calculate beta for the monosymmetric-section Annex Ж coefficients.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Equation (Ж.12)
        Audit ID: SP16-EQ-Ж-012
        Normative status: annex normative procedure

    Mathematical form:
        beta=(2n-1){0.47-0.035(h1/h)[1+h1/h-0.072(h1/h)^2]}.

    Parameters:
        n_ratio:
            Type: float
            Unit: dimensionless
            Meaning: n from equation (Ж.8).
            Valid range: [0,1]
            Source: equation (Ж.8)
        h1_mm, h_mm:
            Type: float
            Unit: mm
            Meaning: Distance to more developed flange and flange-axis spacing.
            Valid range: >0 and h1<=h
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Beta.

    Assumptions:
        - h1 is measured from the section centroid.

    Sign convention:
        - Formula sign is preserved.

    Unit convention:
        - Consistent length units.

    Applicability:
        - Annex Ж.5.

    Limitations:
        - Geometry classification is external.

    Raises:
        ValueError: Invalid n or geometry.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_beta_eq_zh12(0.75, 300, 500) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-012

    Implementation notes:
        - Formula brackets follow the rendered source.
        - Defaults must be explicit in the input configuration.
    """
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0, 1]")
    h1 = _positive(h1_mm, "h1_mm")
    h = _positive(h_mm, "h_mm")
    if h1 > h:
        raise ValueError("h1_mm must not exceed h_mm")
    x = h1 / h
    return (2.0 * n - 1.0) * (0.47 - 0.035 * x * (1.0 + x - 0.072 * x * x))


def annex_zh_eta_eq_zh13(n_ratio: float, i1_mm4: float, i2_mm4: float, effective_length_mm: float, h_mm: float) -> float:
    """
    Summary:
        Calculate eta for Table Ж.5 I-section coefficients.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Equation (Ж.13)
        Audit ID: SP16-EQ-Ж-013
        Normative status: annex normative procedure

    Mathematical form:
        eta=(1-n)[9.87n+0.385(I1/I2)(lef/h)^2].

    Parameters:
        n_ratio:
            Type: float
            Unit: dimensionless
            Meaning: n from equation (Ж.8).
            Valid range: [0,1]
            Source: equation (Ж.8)
        i1_mm4, i2_mm4:
            Type: float
            Unit: mm4
            Meaning: More and less developed flange inertias.
            Valid range: >0
            Source: section properties
        effective_length_mm, h_mm:
            Type: float
            Unit: mm
            Meaning: lef and flange-axis spacing h.
            Valid range: >0
            Source: geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Eta.

    Assumptions:
        - I1 and I2 correspond to the n definition.

    Sign convention:
        - Positive properties.

    Unit convention:
        - Consistent length units.

    Applicability:
        - Table Ж.5 I-section branch.

    Limitations:
        - Does not calculate alpha for the T-section branch.

    Raises:
        ValueError: Invalid n or non-positive property.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_eta_eq_zh13(0.75, 3, 1, 5000, 500) > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_equations_6_to_13
        Validation cases:
            - ZH-EQ-013

    Implementation notes:
        - No hidden unit conversion is used.
        - Defaults must be explicit in the input configuration.
    """
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0, 1]")
    return (1.0 - n) * (9.87 * n + 0.385 * _positive(i1_mm4, "i1_mm4") / _positive(i2_mm4, "i2_mm4") * (_positive(effective_length_mm, "effective_length_mm") / _positive(h_mm, "h_mm")) ** 2)


def annex_zh_table_1_psi(case_id: str, alpha: float, load_flange: str | None = None) -> float:
    """
    Summary:
        Calculate psi from Table Ж.1 for a selected restraint and moment-diagram case.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.3
        Annex: Ж
        Equation/Table: Table Ж.1
        Audit ID: SP16-PROC-ANNEX-ZH-TABLE-1
        Normative status: annex normative data and procedure

    Mathematical form:
        Scenario-specific formulas stored with C1, C2, restraint count, and flange multipliers.

    Parameters:
        case_id:
            Type: str
            Unit: categorical
            Meaning: Exact scenario identifier from the data catalog.
            Valid range: catalog keys
            Source: Table Ж.1 diagrams
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Alpha from equation (Ж.4) or (Ж.5).
            Valid range: 0.1 to 400
            Source: Annex Ж.3
        load_flange:
            Type: str or None
            Unit: categorical
            Meaning: compressed or tension where the selected row distinguishes flange.
            Valid range: compressed, tension, or None
            Source: load application

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Psi.

    Assumptions:
        - The case identifier is selected by comparing the member to the printed diagrams.

    Sign convention:
        - For unbraced transverse-load rows, compressed uses the minus term and tension the plus term.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Doubly symmetric I beams.

    Limitations:
        - Diagram classification is not automated.

    Raises:
        ValueError: Unsupported case, alpha, or flange category.

    Examples:
        >>> annex_zh_table_1_psi("two_or_more_braces", 20) == 3.65
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_tables_1_and_2
        Validation cases:
            - ZH-TBL-001

    Implementation notes:
        - Every scenario is explicitly represented in data/annex_zh_tables.json.
        - Defaults must be explicit in the input configuration.
    """
    a = _real(alpha, "alpha")
    if not 0.1 <= a <= 400.0:
        raise ValueError("Table Ж.1 requires 0.1 <= alpha <= 400")
    cases = _ANNEX_ZH["table_zh1"]["cases"]
    if case_id not in cases:
        raise ValueError(f"Unsupported Table Ж.1 case_id: {case_id}")
    row = cases[case_id]
    kind = row["kind"]
    if kind == "unbraced_transverse":
        if load_flange not in ("compressed", "tension"):
            raise ValueError("This Table Ж.1 row requires load_flange='compressed' or 'tension'")
        c1, c2 = float(row["c1"]), float(row["c2"])
        sign = -1.0 if load_flange == "compressed" else 1.0
        return c1 * (math.sqrt(0.95 * a + 6.09 * c2 * c2 + 5.78) + sign * 2.47 * c2)
    if kind == "unbraced_moment":
        return float(row["c1"]) * math.sqrt(0.95 * a + 5.78)
    if kind == "two_or_more_braces":
        return 2.25 + 0.07 * a if a <= 40.0 else 3.6 + 0.04 * a - 3.5e-5 * a * a
    if kind == "one_mid_brace":
        psi1 = annex_zh_table_1_psi("two_or_more_braces", a)
        if load_flange is None and "multiplier" in row:
            return float(row["multiplier"]) * psi1
        if load_flange not in row["multipliers"]:
            raise ValueError("This Table Ж.1 row requires a valid load_flange")
        return float(row["multipliers"][load_flange]) * psi1
    raise RuntimeError("Unknown Table Ж.1 data kind")


def annex_zh_table_2_psi(load_case: str, load_flange: str, alpha: float) -> float:
    """
    Summary:
        Calculate psi for an unbraced fixed cantilever from Table Ж.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.3
        Annex: Ж
        Equation/Table: Table Ж.2
        Audit ID: SP16-PROC-ANNEX-ZH-TABLE-2
        Normative status: annex normative data and procedure

    Mathematical form:
        Piecewise linear functions for end point load; 1.42*sqrt(alpha) for distributed load on tension flange.

    Parameters:
        load_case:
            Type: str
            Unit: categorical
            Meaning: point_load_at_tip or uniformly_distributed.
            Valid range: listed values
            Source: loading
        load_flange:
            Type: str
            Unit: categorical
            Meaning: compressed or tension.
            Valid range: listed values subject to table row
            Source: load application
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Alpha from equation (Ж.4) or (Ж.5) using the table note k values.
            Valid range: 4 to 100
            Source: Annex Ж.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Psi.

    Assumptions:
        - Cantilever is fixed and has no compression-flange restraint.

    Sign convention:
        - Positive coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.2.

    Limitations:
        - Distributed load on the compressed flange is not provided by the table and is rejected.

    Raises:
        ValueError: Unsupported category or alpha range.

    Examples:
        >>> annex_zh_table_2_psi("point_load_at_tip", "tension", 10)
        2.6

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_tables_1_and_2
        Validation cases:
            - ZH-TBL-002

    Implementation notes:
        - The boundary alpha=28 uses the lower branch; both branches are continuous.
        - Defaults must be explicit in the input configuration.
    """
    a = _real(alpha, "alpha")
    if not 4.0 <= a <= 100.0:
        raise ValueError("Table Ж.2 requires 4 <= alpha <= 100")
    if load_case == "point_load_at_tip":
        if load_flange == "tension":
            return 1.0 + 0.16 * a if a <= 28.0 else 4.0 + 0.05 * a
        if load_flange == "compressed":
            return 6.2 + 0.08 * a if a <= 28.0 else 7.0 + 0.05 * a
        raise ValueError("load_flange must be compressed or tension")
    if load_case == "uniformly_distributed" and load_flange == "tension":
        return 1.42 * math.sqrt(a)
    raise ValueError("Table Ж.2 does not provide this load_case/load_flange combination")


def annex_zh_table_3_phi_b(compressed_flange: str, phi_1: float, phi_2: float, n_ratio: float) -> float:
    """
    Summary:
        Calculate phi_b for a monosymmetric I section from Table Ж.3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.4
        Annex: Ж
        Equation/Table: Table Ж.3
        Audit ID: SP16-PROC-ANNEX-ZH-TABLE-3
        Normative status: annex normative procedure

    Mathematical form:
        Piecewise functions by compressed flange and phi_2 threshold 0.85, capped at one.

    Parameters:
        compressed_flange:
            Type: str
            Unit: categorical
            Meaning: more_developed or less_developed.
            Valid range: listed values
            Source: section and moment sign
        phi_1, phi_2, n_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Equations (Ж.6), (Ж.7), and (Ж.8).
            Valid range: positive phi values and n in [0,1]
            Source: Annex Ж.4

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Phi_b capped at one.

    Assumptions:
        - Inputs correspond to one section and load case.

    Sign convention:
        - Positive coefficients.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.3.

    Limitations:
        - Ж.6 less-developed-flange modifier is applied separately.

    Raises:
        ValueError: Unsupported flange or invalid input.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_table_3_phi_b("less_developed", 1.0, 0.8, 0.75)
        0.8

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_tables_3_to_5
        Validation cases:
            - ZH-TBL-003

    Implementation notes:
        - Table threshold is applied to phi_2 as printed.
        - Defaults must be explicit in the input configuration.
    """
    p1 = _positive(phi_1, "phi_1")
    p2 = _positive(phi_2, "phi_2")
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0,1]")
    if compressed_flange == "more_developed":
        if p2 <= 0.85:
            return min(1.0, p1)
        return min(1.0, p1 * (0.21 + 0.68 * (n / p1 + (1.0 - n) / p2)))
    if compressed_flange == "less_developed":
        return p2 if p2 <= 0.85 else min(1.0, 0.68 + 0.21 * p2)
    raise ValueError("compressed_flange must be more_developed or less_developed")


def annex_zh_table_4_b(row_id: str, load_case: str, delta: float, mu: float, beta: float) -> float:
    """
    Summary:
        Select coefficient B from Table Ж.4 by diagram row and load case.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Table Ж.4
        Audit ID: SP16-PROC-ANNEX-ZH-TABLE-4
        Normative status: annex normative data

    Mathematical form:
        Rows map to delta, delta-1, 1-delta, -delta; similarly for mu; pure bending maps to beta, beta, -beta, -beta.

    Parameters:
        row_id:
            Type: str
            Unit: categorical
            Meaning: diagram_row_1 through diagram_row_4.
            Valid range: listed values
            Source: Table Ж.4 diagram
        load_case:
            Type: str
            Unit: categorical
            Meaning: point_midspan, uniformly_distributed, or pure_bending.
            Valid range: listed values
            Source: loading
        delta, mu, beta:
            Type: float
            Unit: dimensionless
            Meaning: Equations (Ж.10)-(Ж.12).
            Valid range: real
            Source: Annex Ж.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Signed B coefficient.

    Assumptions:
        - The user selects the correct diagram row.

    Sign convention:
        - Table signs are preserved.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.4.

    Limitations:
        - Diagram classification is not automated.

    Raises:
        ValueError: Unsupported row or load case.
        TypeError: Non-real coefficient.

    Examples:
        >>> annex_zh_table_4_b("diagram_row_2", "point_midspan", 1.2, 1.3, 0.1)
        0.19999999999999996

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_tables_3_to_5
        Validation cases:
            - ZH-TBL-004

    Implementation notes:
        - Diagram IDs are documented in the JSON data catalog.
        - Defaults must be explicit in the input configuration.
    """
    d, m, b = _signed(delta, "delta"), _signed(mu, "mu"), _signed(beta, "beta")
    values = {
        "diagram_row_1": {"point_midspan": d, "uniformly_distributed": m, "pure_bending": b},
        "diagram_row_2": {"point_midspan": d - 1.0, "uniformly_distributed": m - 1.0, "pure_bending": b},
        "diagram_row_3": {"point_midspan": 1.0 - d, "uniformly_distributed": 1.0 - m, "pure_bending": -b},
        "diagram_row_4": {"point_midspan": -d, "uniformly_distributed": -m, "pure_bending": -b},
    }
    try:
        return values[row_id][load_case]
    except KeyError as exc:
        raise ValueError("Unsupported Table Ж.4 row_id or load_case") from exc


def annex_zh_table_5_c_d(load_case: str, section_branch: str, eta: float | None = None, alpha: float | None = None) -> tuple[float, float]:
    """
    Summary:
        Calculate coefficients C and D from Table Ж.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.5
        Annex: Ж
        Equation/Table: Table Ж.5
        Audit ID: SP16-PROC-ANNEX-ZH-TABLE-5
        Normative status: annex normative data

    Mathematical form:
        C = tabulated multiplier times eta for I sections or alpha for T sections; D is tabulated.

    Parameters:
        load_case:
            Type: str
            Unit: categorical
            Meaning: point_midspan, uniformly_distributed, or pure_bending.
            Valid range: listed values
            Source: loading
        section_branch:
            Type: str
            Unit: categorical
            Meaning: i_section_n_le_0.9 or t_section_n_eq_1.
            Valid range: listed values
            Source: section classification
        eta, alpha:
            Type: float or None
            Unit: dimensionless
            Meaning: Required variable for the selected branch.
            Valid range: >=0
            Source: equation (Ж.13) or (Ж.4)

    Returns:
        Type: tuple[float, float]
        Unit: dimensionless
        Meaning: C and D.

    Assumptions:
        - The branch matches n.

    Sign convention:
        - Non-negative C and positive D.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Table Ж.5.

    Limitations:
        - For 0.9<n<1, call annex_zh_interpolate_psi_a_for_n with endpoint values calculated for n=0.9 and n=1.0.

    Raises:
        ValueError: Missing branch variable or unsupported category.

    Examples:
        >>> annex_zh_table_5_c_d("point_midspan", "i_section_n_le_0.9", eta=10)
        (3.3, 3.265)

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_tables_3_to_5
        Validation cases:
            - ZH-TBL-005

    Implementation notes:
        - Table values are stored in JSON and multiplied without rounding.
        - Defaults must be explicit in the input configuration.
    """
    try:
        row = _ANNEX_ZH["table_zh5"][load_case]
    except KeyError as exc:
        raise ValueError(f"Unsupported Table Ж.5 load_case: {load_case}") from exc
    if section_branch == "i_section_n_le_0.9":
        c = float(row["c_i_multiplier"]) * _nonnegative(eta if eta is not None else -1.0, "eta")
    elif section_branch == "t_section_n_eq_1":
        c = float(row["c_t_multiplier"]) * _nonnegative(alpha if alpha is not None else -1.0, "alpha")
    else:
        raise ValueError("Unsupported Table Ж.5 section_branch")
    return c, float(row["d"])



def annex_zh_interpolate_psi_a_for_n(
    n_ratio: float,
    psi_a_at_n_0_9: float,
    psi_a_at_n_1_0: float,
) -> float:
    """
    Summary:
        Linearly interpolate the Annex Ж coefficient psi_a for a monosymmetric I section with 0.9<n<1.0.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.6
        Annex: Ж
        Equation/Table: Unnumbered interpolation rule following Table Ж.5
        Audit ID: SP16-PROC-ANNEX-ZH-INTERPOLATION
        Normative status: annex normative procedure

    Mathematical form:
        psi_a = psi_0.9 + (n-0.9)/0.1 * (psi_1.0-psi_0.9).

    Parameters:
        n_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Flange-inertia ratio n from equation (Ж.8).
            Valid range: 0.9 <= n <= 1.0
            Source: equation (Ж.8)
        psi_a_at_n_0_9, psi_a_at_n_1_0:
            Type: float
            Unit: dimensionless
            Meaning: Endpoint values calculated by equation (Ж.9) for the I-section branch at n=0.9 and the T-section branch at n=1.0.
            Valid range: > 0
            Source: equation (Ж.9), Tables Ж.4-Ж.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Interpolated coefficient psi_a.

    Assumptions:
        - Both endpoint values correspond to the same load case and section orientation.

    Sign convention:
        - Psi values are positive coefficients.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause Ж.6 for 0.9<n<1.0; endpoint values are also returned exactly at n=0.9 and n=1.0.

    Limitations:
        - This function does not calculate the endpoint values or classify the section diagrams.

    Raises:
        ValueError: n is outside [0.9, 1.0] or an endpoint value is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> annex_zh_interpolate_psi_a_for_n(0.95, 2.0, 4.0)
        2.999999999999999

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh6_interpolation
        Validation cases:
            - ZH-PROC-INTERPOLATION

    Implementation notes:
        - Interpolation is performed only over the interval explicitly stated in clause Ж.6.
        - Defaults must be explicit in the input configuration.
    """
    n = _real(n_ratio, "n_ratio")
    if not 0.9 <= n <= 1.0:
        raise ValueError("Clause Ж.6 interpolation requires 0.9 <= n_ratio <= 1.0")
    psi_09 = _positive(psi_a_at_n_0_9, "psi_a_at_n_0_9")
    psi_10 = _positive(psi_a_at_n_1_0, "psi_a_at_n_1_0")
    return psi_09 + (n - 0.9) / 0.1 * (psi_10 - psi_09)


def apply_t_section_low_alpha_modifier(
    psi_a: float,
    alpha: float,
    load_case: str,
) -> float:
    """
    Summary:
        Apply the Annex Ж.6 multiplier to T-section psi_a for transverse point or uniformly distributed loading when alpha<40.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.6
        Annex: Ж
        Equation/Table: Unnumbered T-section modifier following Table Ж.5
        Audit ID: SP16-PROC-ANNEX-ZH-T-SECTION-MODIFIER
        Normative status: annex normative procedure

    Mathematical form:
        psi_a,modified = psi_a*(0.8+0.004*alpha) for point or uniform load and alpha<40; otherwise psi_a.

    Parameters:
        psi_a:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient calculated from equation (Ж.9) for the T-section branch.
            Valid range: > 0
            Source: equation (Ж.9)
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient alpha used in Table Ж.5.
            Valid range: > 0
            Source: equation (Ж.4)
        load_case:
            Type: str
            Unit: categorical
            Meaning: point_midspan, uniformly_distributed, or pure_bending.
            Valid range: listed values
            Source: Table Ж.5 loading classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Modified or unchanged psi_a.

    Assumptions:
        - The section is a T section with n=1.0.

    Sign convention:
        - Positive coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause Ж.6 after equation (Ж.9).

    Limitations:
        - The multiplier is not applied to pure bending or when alpha>=40.

    Raises:
        ValueError: An input is non-positive or load_case is unsupported.
        TypeError: A numerical input is not real.

    Examples:
        >>> apply_t_section_low_alpha_modifier(5.0, 20.0, "point_midspan")
        4.4

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh6_t_section_modifier
        Validation cases:
            - ZH-PROC-T-MODIFIER

    Implementation notes:
        - The strict alpha<40 condition is retained; alpha=40 returns the unmodified value.
        - Defaults must be explicit in the input configuration.
    """
    value = _positive(psi_a, "psi_a")
    a = _positive(alpha, "alpha")
    if load_case not in {"point_midspan", "uniformly_distributed", "pure_bending"}:
        raise ValueError("Unsupported Annex Ж.6 load_case")
    if load_case in {"point_midspan", "uniformly_distributed"} and a < 40.0:
        return value * (0.8 + 0.004 * a)
    return value

def annex_zh_symmetric_i_phi_b(
    psi: float,
    minor_axis_inertia_mm4: float,
    major_axis_inertia_mm4: float,
    section_height_mm: float,
    effective_length_mm: float,
    elastic_modulus_n_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> dict[str, float]:
    """
    Summary:
        Calculate phi_1 and phi_b for a doubly symmetric I beam using Annex Ж.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.1-Ж.3
        Annex: Ж
        Equation/Table: Equations (Ж.1)-(Ж.3)
        Audit ID: SP16-PROC-ANNEX-ZH-SYMMETRIC-I
        Normative status: annex normative procedure

    Mathematical form:
        phi_1 from Ж.3, then branch Ж.1 or Ж.2.

    Parameters:
        psi, minor_axis_inertia_mm4, major_axis_inertia_mm4, section_height_mm, effective_length_mm, elastic_modulus_n_mm2, design_yield_resistance_n_mm2:
            Type: float
            Unit: as named
            Meaning: Inputs to equation (Ж.3).
            Valid range: >0
            Source: tables, section properties, geometry, and materials

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: phi_1 and phi_b.

    Assumptions:
        - Doubly symmetric I section.

    Sign convention:
        - Positive properties.

    Unit convention:
        - mm and N/mm2.

    Applicability:
        - Annex Ж.2.

    Limitations:
        - Psi selection is external to this wrapper.

    Raises:
        ValueError: Invalid input.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_symmetric_i_phi_b(10, 1e8, 1e10, 500, 5000, 206000, 355)["phi_b"] > 0
        True

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_wrappers
        Validation cases:
            - ZH-PROC-SYMMETRIC

    Implementation notes:
        - Branch selection is deterministic from phi_1.
        - Defaults must be explicit in the input configuration.
    """
    phi1 = annex_zh_phi1_eq_zh3(psi, minor_axis_inertia_mm4, major_axis_inertia_mm4, section_height_mm, effective_length_mm, elastic_modulus_n_mm2, design_yield_resistance_n_mm2)
    phi_b = annex_zh_phi_b_eq_zh1(phi1) if phi1 <= 0.85 else annex_zh_phi_b_eq_zh2(phi1)
    return {"phi_1": phi1, "phi_b": phi_b}


def annex_zh_channel_phi_b(phi_1: float) -> float:
    """
    Summary:
        Calculate the channel-section stability coefficient from Annex Ж.7.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.7
        Annex: Ж
        Equation/Table: Unnumbered channel rule
        Audit ID: SP16-PROC-ANNEX-ZH-CHANNEL
        Normative status: annex normative procedure

    Mathematical form:
        phi_b=0.7*phi_1.

    Parameters:
        phi_1:
            Type: float
            Unit: dimensionless
            Meaning: Phi_1 calculated as for a doubly symmetric I section with channel properties.
            Valid range: >=0
            Source: equations (Ж.3) and (Ж.4)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Channel stability coefficient.

    Assumptions:
        - Ix, Iy, and Jt used for phi_1 are channel properties.

    Sign convention:
        - Non-negative coefficient.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Channel beams under Annex Ж.7.

    Limitations:
        - Does not calculate phi_1.

    Raises:
        ValueError: Negative phi_1.
        TypeError: Non-real input.

    Examples:
        >>> annex_zh_channel_phi_b(1.0)
        0.7

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_wrappers
        Validation cases:
            - ZH-PROC-CHANNEL

    Implementation notes:
        - No cap beyond the printed 0.7 multiplier is introduced.
        - Defaults must be explicit in the input configuration.
    """
    return 0.7 * _nonnegative(phi_1, "phi_1")


def apply_less_developed_compressed_flange_modifier(phi_2: float, n_ratio: float, effective_length_mm: float, less_developed_flange_width_mm: float) -> float:
    """
    Summary:
        Apply the Annex Ж.6 modifier for a less developed compressed flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Ж.6
        Annex: Ж
        Equation/Table: Unnumbered modifier
        Audit ID: SP16-PROC-ANNEX-ZH-MONOSYMMETRIC-I
        Normative status: annex normative procedure

    Mathematical form:
        For n>0.7 and 5<=lef/b2<=25: phi_2*=1.025-0.015lef/b2 and cap at 0.95; lef/b2>25 is prohibited.

    Parameters:
        phi_2, n_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Phi_2 and n.
            Valid range: phi_2>0, n in [0,1]
            Source: equations (Ж.7)-(Ж.8)
        effective_length_mm, less_developed_flange_width_mm:
            Type: float
            Unit: mm
            Meaning: lef and b2.
            Valid range: >0
            Source: geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Modified phi_2.

    Assumptions:
        - The less developed flange is compressed.

    Sign convention:
        - Positive coefficient.

    Unit convention:
        - Consistent length units.

    Applicability:
        - Annex Ж.6.

    Limitations:
        - No modifier is applied when n<=0.7 or lef/b2<5.

    Raises:
        ValueError: n invalid or lef/b2 exceeds 25 for n>0.7.
        TypeError: Non-real input.

    Examples:
        >>> apply_less_developed_compressed_flange_modifier(1.0, 0.8, 1000, 100)
        0.875

    Tests:
        Unit tests:
            - tests/test_crane_runway_and_bending_stability.py::test_annex_zh_wrappers
        Validation cases:
            - ZH-PROC-LESS-FLANGE

    Implementation notes:
        - The cap at 0.95 is applied after multiplication.
        - Defaults must be explicit in the input configuration.
    """
    p2 = _positive(phi_2, "phi_2")
    n = _real(n_ratio, "n_ratio")
    if not 0.0 <= n <= 1.0:
        raise ValueError("n_ratio must be within [0,1]")
    ratio = _positive(effective_length_mm, "effective_length_mm") / _positive(less_developed_flange_width_mm, "less_developed_flange_width_mm")
    if n > 0.7 and ratio > 25.0:
        raise ValueError("Annex Ж.6 does not permit lef/b2 > 25 for this case")
    if n > 0.7 and ratio >= 5.0:
        return min(0.95, p2 * (1.025 - 0.015 * ratio))
    return p2
