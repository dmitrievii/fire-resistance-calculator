"""Axial-member strength and central-compression stability for СП 16.13330.2017 clauses 7.1.1-7.1.3."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))


_TABLE_6 = _load_json("table_6_single_angle_coefficients.json")
_TABLE_7 = _load_json("table_7_section_type_coefficients.json")
_TABLE_D1 = _load_json("annex_d_table_d1_stability_coefficients.json")

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-7.1.1-RESISTANCE-BASIS",
    "SP16-PROC-7.1.2-GAMMA-C1",
    "SP16-PROC-7.1.2-SPECIAL-REDUCTION",
    "SP16-PROC-7.1.3-RELATIVE-SLENDERNESS",
    "SP16-PROC-7.1.3-PHI-RULES",
)


def _require_real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _require_nonnegative(value: float, name: str) -> float:
    value = _require_real(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _require_positive(value: float, name: str) -> float:
    value = _require_real(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _require_section_type(section_type: str) -> str:
    if section_type not in _TABLE_7["section_types"]:
        raise ValueError("section_type must be one of: a, b, c")
    return section_type


def axial_strength_utilization_yield(
    axial_force_n: float,
    net_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate equation (5) utilization using design yield resistance.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.1
        Annex: None
        Equation/Table: Equation (5)
        Audit ID: SP16-EQ-005
        Normative status: normative

    Mathematical form:
        utilization = N / (A_n * R_y * gamma_c)

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Magnitude of central tensile or compressive force N.
            Valid range: >= 0
            Source: structural analysis
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net cross-sectional area A_n.
            Valid range: > 0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1 / audited input
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: Table 1 or applicable clause

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (5) utilization; compliance requires a value <= 1.

    Assumptions:
        - The yield-resistance branch is applicable under clause 7.1.1.
        - Net area and gamma_c have been selected outside this function.

    Sign convention:
        - axial_force_n is supplied as a non-negative magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used without implicit conversion.

    Applicability:
        - Central tension or compression checked by R_y under clause 7.1.1.

    Limitations:
        - Does not decide whether the R_y or R_u/gamma_u branch governs.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> axial_strength_utilization_yield(500000.0, 2000.0, 355.0, 1.0)
        0.704225352112676

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_5_yield_normal_zero_and_units
        Validation cases:
            - AXIAL-EQ-005-YIELD

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    force = _require_nonnegative(axial_force_n, "axial_force_n")
    area = _require_positive(net_area_mm2, "net_area_mm2")
    resistance = _require_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    gamma_c = _require_positive(working_condition_factor, "working_condition_factor")
    return force / (area * resistance * gamma_c)


def axial_strength_utilization_ultimate(
    axial_force_n: float,
    net_area_mm2: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate equation (5) after the clause 7.1.1 replacement R_y -> R_u/gamma_u.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.1 and 4.3.2
        Annex: None
        Equation/Table: Equation (5), ultimate-resistance branch
        Audit ID: SP16-EQ-005
        Normative status: normative

    Mathematical form:
        utilization = N * gamma_u / (A_n * R_u * gamma_c)

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Magnitude of central force N.
            Valid range: >= 0
            Source: structural analysis
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net area A_n.
            Valid range: > 0
            Source: section geometry
        design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design ultimate resistance R_u.
            Valid range: > 0
            Source: clause 6.1 / audited input
        ultimate_resistance_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Safety factor gamma_u; clause 4.3.2 gives 1.3 for the cited use.
            Valid range: > 0
            Source: explicit input
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: Table 1 or applicable clause

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Ultimate-branch utilization; compliance requires <= 1.

    Assumptions:
        - The caller has established that the ultimate-resistance branch applies.

    Sign convention:
        - axial_force_n is a non-negative magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used directly.

    Applicability:
        - Members described by the second paragraph of clause 7.1.1.

    Limitations:
        - Does not infer applicability from steel grade or post-yield service requirements.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> axial_strength_utilization_ultimate(500000.0, 2000.0, 485.0, 1.3, 1.0)
        0.6701030927835051

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_5_ultimate_branch_and_sign_rejection
        Validation cases:
            - AXIAL-EQ-005-ULTIMATE

    Implementation notes:
        - gamma_u has no hidden default.
        - Defaults must be explicit in the input configuration.
    """
    force = _require_nonnegative(axial_force_n, "axial_force_n")
    area = _require_positive(net_area_mm2, "net_area_mm2")
    resistance = _require_positive(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2")
    gamma_u = _require_positive(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor")
    gamma_c = _require_positive(working_condition_factor, "working_condition_factor")
    return force * gamma_u / (area * resistance * gamma_c)




def open_u_section_phi_1(c_max: float, relative_slenderness_y: float) -> float:
    """
    Summary:
        Calculate the auxiliary coefficient phi_1 from equation (11) for the open U-shaped section route of clause 7.1.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.5
        Annex: Д for the externally selected c_max coefficient
        Equation/Table: Equation (11)
        Audit ID: SP16-EQ-011
        Normative status: normative

    Mathematical form:
        phi_1 = 7.6 * c_max / lambda_bar_y**2

    Parameters:
        c_max:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c_max selected from the applicable Annex Д route.
            Valid range: > 0
            Source: explicit audited engineering input from Annex Д
        relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_y about the y axis.
            Valid range: > 0
            Source: section/global stability calculation

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Auxiliary coefficient phi_1 used by equation (10).

    Assumptions:
        - The caller has established applicability of clause 7.1.5 and supplied the correct c_max.

    Sign convention:
        - c_max and relative slenderness are positive magnitudes.

    Unit convention:
        - All inputs and the result are dimensionless.

    Applicability:
        - Solid-web compressed members of open U-shaped section governed by clause 7.1.5.

    Limitations:
        - This function does not infer section topology, determine c_max from geometry, or replace the principal-plane stability checks required elsewhere in clause 7.1.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or not greater than zero.

    Examples:
        >>> open_u_section_phi_1(0.8, 2.0)
        1.52

    Tests:
        Unit tests:
            - tests/test_final_annex_and_release_consolidation.py::test_equation_11
        Validation cases:
            - AXIAL-EQ-011-RECONSTRUCTION

    Implementation notes:
        - The historical v0.22 public API exposed c_max explicitly; this reconstruction preserves that fail-closed boundary.
        - No interpolation or geometry classification is invented for Annex Д.
    """
    c_value = _require_positive(c_max, "c_max")
    slenderness = _require_positive(relative_slenderness_y, "relative_slenderness_y")
    return 7.6 * c_value / (slenderness * slenderness)


def open_u_section_torsional_flexural_utilization(
    axial_force_n: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    c_max: float,
    relative_slenderness_y: float,
) -> float:
    """
    Summary:
        Calculate the clause 7.1.5 open-U-section stability utilization from equation (10), including the equation (11) coefficient route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.5
        Annex: Д for c_max
        Equation/Table: Equations (10) and (11)
        Audit ID: SP16-EQ-010
        Normative status: normative

    Mathematical form:
        phi_1 = 7.6*c_max/lambda_bar_y**2;
        phi_c = phi_1 for phi_1 <= 0.85;
        phi_c = min(1, 0.68 + 0.21*phi_1) for phi_1 > 0.85;
        utilization = N/(phi_c*A*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Magnitude of the compressive force N.
            Valid range: >= 0
            Source: structural analysis
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross section area A.
            Valid range: > 0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1 / audited input
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: Table 1 or applicable clause
        c_max:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c_max selected using the applicable Annex Д route.
            Valid range: > 0
            Source: explicit audited engineering input
        relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_y.
            Valid range: > 0
            Source: section/global stability calculation

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (10) utilization; compliance with this scalar check requires a value <= 1.

    Assumptions:
        - The caller has established the open-U-section applicability of clause 7.1.5.
        - c_max has been selected correctly from the applicable normative Annex Д route.

    Sign convention:
        - axial_force_n is supplied as a non-negative compression magnitude.

    Unit convention:
        - N, mm2 and N/mm2 are used directly; coefficients are dimensionless.

    Applicability:
        - The dedicated torsional-flexural stability check for compressed open U-shaped solid-web members in clause 7.1.5.

    Limitations:
        - Does not derive c_max, recognize arbitrary geometry, calculate global actions, or replace the separate stability checks in the principal planes.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> round(open_u_section_torsional_flexural_utilization(500000, 3000, 340, 1.05, 0.8, 2.0), 12)
        0.467227189782

    Tests:
        Unit tests:
            - tests/test_final_annex_and_release_consolidation.py::test_equation_10_historical_seed
        Validation cases:
            - AXIAL-EQ-010-RECONSTRUCTION

    Implementation notes:
        - The piecewise phi_c route and upper cap are explicit; no hidden section classification or c_max lookup is performed.
        - The public signature follows the surviving historical v0.22 API freeze evidence.
    """
    force = _require_nonnegative(axial_force_n, "axial_force_n")
    area = _require_positive(gross_area_mm2, "gross_area_mm2")
    resistance = _require_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    gamma_c = _require_positive(working_condition_factor, "working_condition_factor")
    phi_1 = open_u_section_phi_1(c_max, relative_slenderness_y)
    phi_c = phi_1 if phi_1 <= 0.85 else min(1.0, 0.68 + 0.21 * phi_1)
    if phi_c <= 0.0:
        raise ValueError("calculated phi_c must be greater than zero")
    return force / (phi_c * area * resistance * gamma_c)


def table_6_angle_coefficients(table_case: str) -> tuple[float, float, float]:
    """
    Summary:
        Return the discrete alpha_1, alpha_2, and beta coefficients from Table 6.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.2
        Annex: None
        Equation/Table: Table 6
        Audit ID: SP16-TBL-6
        Normative status: normative

    Mathematical form:
        Exact categorical lookup; no interpolation or extrapolation.

    Parameters:
        table_case:
            Type: str
            Unit: not applicable
            Meaning: Audited Table 6 case identifier.
            Valid range: one_bolt_a_1_35d, one_bolt_a_1_5d, one_bolt_a_2d, multi_bolt_2, multi_bolt_3, multi_bolt_4
            Source: geometry classified against Table 6

    Returns:
        Type: tuple[float, float, float]
        Unit: dimensionless
        Meaning: alpha_1, alpha_2, beta.

    Assumptions:
        - The user has confirmed all geometry and applicability conditions for the selected row.

    Sign convention:
        - Coefficients are positive magnitudes.

    Unit convention:
        - Coefficients are dimensionless.

    Applicability:
        - Single angles bolted through one leg under clause 7.1.2.

    Limitations:
        - The function does not classify bolt geometry from coordinates.

    Raises:
        ValueError: table_case is not a listed Table 6 case.

    Examples:
        >>> table_6_angle_coefficients("multi_bolt_3")
        (1.45, 0.36, 1.0)

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_table_6_lookup_existence_and_values
        Validation cases:
            - AXIAL-TBL-006

    Implementation notes:
        - The 1.35d case retains its restrictive table footnote in the data file.
        - No intermediate bolt count or distance is invented.
    """
    try:
        row = _TABLE_6["values"][table_case]
    except KeyError as exc:
        raise ValueError(f"Unknown Table 6 case: {table_case}") from exc
    return float(row["alpha1"]), float(row["alpha2"]), float(row["beta"])


def single_angle_working_condition_factor(
    net_area_mm2: float,
    attached_leg_net_strip_area_mm2: float,
    alpha1: float,
    alpha2: float,
    beta: float,
    special_ten_percent_reduction_applies: bool,
) -> float:
    """
    Summary:
        Calculate gamma_c1 for a bolted single-angle connection and apply the explicit 10% reduction when required.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.2
        Annex: None
        Equation/Table: Unnumbered gamma_c1 expression following equation (6), Table 6, page 15 reduction rule
        Audit ID: SP16-PROC-7.1.2-GAMMA-C1
        Normative status: normative

    Mathematical form:
        gamma_c1 = (alpha_1 * A_n1 / A_n + alpha_2) * beta; optionally gamma_c1 := 0.9*gamma_c1.

    Parameters:
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net area A_n of the angle.
            Valid range: > 0
            Source: section geometry
        attached_leg_net_strip_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_n1 between the hole edge and angle toe.
            Valid range: 0 <= A_n1 <= A_n
            Source: section geometry
        alpha1:
            Type: float
            Unit: dimensionless
            Meaning: Table 6 coefficient alpha_1.
            Valid range: > 0
            Source: Table 6
        alpha2:
            Type: float
            Unit: dimensionless
            Meaning: Table 6 coefficient alpha_2.
            Valid range: >= 0
            Source: Table 6
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Table 6 coefficient beta.
            Valid range: > 0
            Source: Table 6
        special_ten_percent_reduction_applies:
            Type: bool
            Unit: not applicable
            Meaning: True only for the explicitly listed tower/cross-arm/support elements on page 15.
            Valid range: true or false
            Source: project classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: gamma_c1 after any required explicit reduction.

    Assumptions:
        - A_n1 is measured as defined directly below equation (6).

    Sign convention:
        - Areas and coefficients are non-negative magnitudes.

    Unit convention:
        - Area ratio cancels; output is dimensionless.

    Applicability:
        - Clause 7.1.2 single-angle connection check.

    Limitations:
        - The special reduction is not inferred from member names.

    Raises:
        TypeError: Inputs are invalid types.
        ValueError: Areas or coefficients violate the documented domain.

    Examples:
        >>> single_angle_working_condition_factor(1000.0, 200.0, 1.45, 0.36, 1.0, False)
        0.65

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_gamma_c1_formula_boundary_and_special_reduction
        Validation cases:
            - AXIAL-PROC-GAMMA-C1

    Implementation notes:
        - The reduction flag is mandatory and has no default.
        - Defaults must be explicit in the input configuration.
    """
    area = _require_positive(net_area_mm2, "net_area_mm2")
    area1 = _require_nonnegative(attached_leg_net_strip_area_mm2, "attached_leg_net_strip_area_mm2")
    if area1 > area:
        raise ValueError("attached_leg_net_strip_area_mm2 must not exceed net_area_mm2")
    a1 = _require_positive(alpha1, "alpha1")
    a2 = _require_nonnegative(alpha2, "alpha2")
    b = _require_positive(beta, "beta")
    if not isinstance(special_ten_percent_reduction_applies, bool):
        raise TypeError("special_ten_percent_reduction_applies must be bool")
    gamma_c1 = (a1 * area1 / area + a2) * b
    return gamma_c1 * (0.9 if special_ten_percent_reduction_applies else 1.0)


def single_angle_connection_strength_utilization(
    axial_force_n: float,
    net_area_mm2: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    angle_working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the bolted single-angle connection utilization from equation (6).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.2
        Annex: None
        Equation/Table: Equation (6)
        Audit ID: SP16-EQ-006
        Normative status: normative

    Mathematical form:
        utilization = N * gamma_u / (A_n * R_u * gamma_c1)

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Tensile-force magnitude N.
            Valid range: >= 0
            Source: structural analysis
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Angle net area A_n.
            Valid range: > 0
            Source: section geometry
        design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design ultimate resistance R_u.
            Valid range: > 0
            Source: clause 6.1 / audited input
        ultimate_resistance_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_u.
            Valid range: > 0
            Source: clause 4.3.2 / explicit input
        angle_working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c1 computed from Table 6 and the area ratio.
            Valid range: > 0
            Source: single_angle_working_condition_factor

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (6) utilization; compliance requires <= 1.

    Assumptions:
        - All geometric restrictions in clause 7.1.2 are satisfied.

    Sign convention:
        - Tensile force is a non-negative magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used directly.

    Applicability:
        - The specified one-leg bolted single-angle case with steel yield strength <= 380 N/mm2.

    Limitations:
        - Applicability restrictions are not reconstructed from geometry by this scalar function.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> single_angle_connection_strength_utilization(200000.0, 1000.0, 485.0, 1.3, 0.65)
        0.8243453608247423

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_6_normal_zero_and_invalid_domains
        Validation cases:
            - AXIAL-EQ-006

    Implementation notes:
        - gamma_c1 is an explicit input to keep Table 6 selection traceable.
        - Defaults must be explicit in the input configuration.
    """
    force = _require_nonnegative(axial_force_n, "axial_force_n")
    area = _require_positive(net_area_mm2, "net_area_mm2")
    resistance = _require_positive(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2")
    gamma_u = _require_positive(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor")
    gamma_c1 = _require_positive(angle_working_condition_factor, "angle_working_condition_factor")
    return force * gamma_u / (area * resistance * gamma_c1)


def relative_slenderness(
    geometric_slenderness: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the nondimensional relative slenderness used in clause 7.1.3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: None
        Equation/Table: Definition below equation (9)
        Audit ID: SP16-PROC-7.1.3-RELATIVE-SLENDERNESS
        Normative status: normative

    Mathematical form:
        lambda_bar = lambda * sqrt(R_y / E)

    Parameters:
        geometric_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Geometric member slenderness lambda, normally l_eff/i.
            Valid range: >= 0
            Source: geometry and effective length
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Elastic modulus E.
            Valid range: > 0
            Source: applicable material data

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative slenderness lambda_bar.

    Assumptions:
        - R_y and E use the same stress unit.

    Sign convention:
        - Slenderness and material properties are non-negative magnitudes.

    Unit convention:
        - R_y and E are both N/mm2; no conversion is performed.

    Applicability:
        - Central-compression stability under clause 7.1.3.

    Limitations:
        - Does not calculate effective length or radius of gyration.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> round(relative_slenderness(100.0, 355.0, 206000.0), 6)
        4.151512

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_relative_slenderness_normal_zero_and_unit_consistency
        Validation cases:
            - AXIAL-PROC-RELATIVE-SLENDERNESS

    Implementation notes:
        - Unit suffixes make the stress-unit contract explicit.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _require_nonnegative(geometric_slenderness, "geometric_slenderness")
    resistance = _require_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    modulus = _require_positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    return slenderness * math.sqrt(resistance / modulus)


def table_7_section_coefficients(section_type: str) -> tuple[float, float]:
    """
    Summary:
        Return alpha and beta for a user-classified section type from Table 7.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: None
        Equation/Table: Table 7
        Audit ID: SP16-TBL-7
        Normative status: normative

    Mathematical form:
        type a -> (0.03, 0.06); type b -> (0.04, 0.09); type c -> (0.04, 0.14).

    Parameters:
        section_type:
            Type: str
            Unit: not applicable
            Meaning: User-selected normative type a, b, or c.
            Valid range: a, b, c
            Source: visual classification using Table 7

    Returns:
        Type: tuple[float, float]
        Unit: dimensionless
        Meaning: alpha and beta.

    Assumptions:
        - The section and calculation plane were classified using the normative figures.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Coefficients are dimensionless.

    Applicability:
        - Equation (9) in clause 7.1.3.

    Limitations:
        - Arbitrary geometry is not automatically classified.

    Raises:
        ValueError: section_type is not a, b, or c.

    Examples:
        >>> table_7_section_coefficients("b")
        (0.04, 0.09)

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_table_7_lookup_and_rejection
        Validation cases:
            - AXIAL-TBL-007

    Implementation notes:
        - Table 7 visual notes remain in the JSON data file.
        - Defaults must be explicit in the input configuration.
    """
    key = _require_section_type(section_type)
    row = _TABLE_7["section_types"][key]
    return float(row["alpha"]), float(row["beta"])


def stability_delta(relative_slenderness_value: float, alpha: float, beta: float) -> float:
    """
    Summary:
        Calculate delta in equation (9).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: None
        Equation/Table: Equation (9)
        Audit ID: SP16-EQ-009
        Normative status: normative

    Mathematical form:
        delta = 9.87 * (1 - alpha + beta*lambda_bar) + lambda_bar^2

    Parameters:
        relative_slenderness_value:
            Type: float
            Unit: dimensionless
            Meaning: lambda_bar.
            Valid range: >= 0
            Source: relative_slenderness or explicit audited input
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Table 7 alpha.
            Valid range: >= 0
            Source: Table 7
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Table 7 beta.
            Valid range: >= 0
            Source: Table 7

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: delta for equation (8).

    Assumptions:
        - alpha and beta correspond to the selected section type.

    Sign convention:
        - Inputs are non-negative magnitudes.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - Clause 7.1.3 stability coefficient calculation.

    Limitations:
        - Does not apply low-slenderness or upper-cap rules.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or negative.

    Examples:
        >>> stability_delta(2.0, 0.04, 0.09)
        15.2518

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_9_delta_normal_boundary_and_sign
        Validation cases:
            - AXIAL-EQ-009

    Implementation notes:
        - Coefficients are explicit inputs to preserve equation-level traceability.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _require_nonnegative(relative_slenderness_value, "relative_slenderness_value")
    a = _require_nonnegative(alpha, "alpha")
    b = _require_nonnegative(beta, "beta")
    return 9.87 * (1.0 - a + b * slenderness) + slenderness * slenderness


def central_compression_stability_coefficient(
    relative_slenderness_value: float,
    section_type: str,
) -> float:
    """
    Summary:
        Calculate phi by equations (8)-(9), including the stated low-slenderness and upper-cap rules.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: D
        Equation/Table: Equations (8), (9), Table 7, and Table D.1 consistency
        Audit ID: SP16-EQ-008
        Normative status: normative

    Mathematical form:
        phi = 0.5*(delta - sqrt(delta^2 - 39.48*lambda_bar^2))/lambda_bar^2, with clause rules.

    Parameters:
        relative_slenderness_value:
            Type: float
            Unit: dimensionless
            Meaning: lambda_bar.
            Valid range: >= 0 for types a/b; >= 0.4 for type c
            Source: relative_slenderness or explicit audited input
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Table 7 type a, b, or c.
            Valid range: a, b, c
            Source: visual classification using Table 7

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Central-compression stability coefficient phi.

    Assumptions:
        - Section type and calculation plane are correctly classified.
        - For types a and b, clause 7.1.3 governs directly with phi=1 when lambda_bar<0.6. For type c, the supplied clause/table combination does not define a complete route below 0.4.

    Sign convention:
        - lambda_bar and phi are non-negative magnitudes.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - Solid-section centrally compressed elements satisfying clauses 7.3.2-7.3.9.

    Limitations:
        - Does not verify local-stability prerequisites.
        - Does not infer section type from geometry.

    Raises:
        TypeError: relative_slenderness_value is not numeric.
        ValueError: lambda_bar is negative, is below 0.4 for type c, section_type is invalid, or the radicand is inconsistent.

    Examples:
        >>> round(central_compression_stability_coefficient(2.0, "b"), 6)
        0.825795

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_8_low_slenderness_formula_and_caps
        Validation cases:
            - AXIAL-EQ-008
            - AXIAL-D1-*

    Implementation notes:
        - A rationalized equivalent of equation (8) is used to reduce cancellation error.
        - The cap 7.6/lambda_bar^2 is applied from the tabulated boundary nodes 3.8, 4.4, or 5.8 for a, b, or c respectively, matching Table D.1; this boundary interpretation is documented as a text/table ambiguity.
    """
    slenderness = _require_real(relative_slenderness_value, "relative_slenderness_value")
    if slenderness < 0.0:
        raise ValueError("relative_slenderness_value must be non-negative")
    key = _require_section_type(section_type)
    # Clause 7.1.3 explicitly prescribes phi=1 for section types a and b when
    # lambda_bar < 0.6. This rule applies below the first printed Table D.1 node.
    if key in {"a", "b"} and slenderness < 0.6:
        return 1.0
    # For type c the supplied text does not provide a separate below-0.4 rule
    # and Table D.1 starts at 0.4; keep this route fail-closed.
    if slenderness < 0.4:
        raise ValueError("relative_slenderness_value below 0.4 is not resolved for section type c")
    alpha, beta = table_7_section_coefficients(key)
    delta = stability_delta(slenderness, alpha, beta)
    radicand = delta * delta - 39.48 * slenderness * slenderness
    if radicand < -1e-12:
        raise ValueError("Equation (8) radicand is negative")
    radicand = max(radicand, 0.0)
    phi = 19.74 / (delta + math.sqrt(radicand))
    threshold = {"a": 3.8, "b": 4.4, "c": 5.8}[key]
    if slenderness >= threshold:
        phi = min(phi, 7.6 / (slenderness * slenderness))
    return phi


def annex_d1_stability_coefficient(
    relative_slenderness_value: float,
    section_type: str,
) -> float:
    """
    Summary:
        Return an exact printed Table D.1 stability coefficient at a tabulated slenderness node.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: D
        Equation/Table: Table D.1
        Audit ID: SP16-TBL-Д-1
        Normative status: annex reference table

    Mathematical form:
        phi = printed_integer / 1000 at an exact Table D.1 lambda_bar node.

    Parameters:
        relative_slenderness_value:
            Type: float
            Unit: dimensionless
            Meaning: Tabulated lambda_bar.
            Valid range: exact node from 0.4 to 10.0
            Source: user input
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Table 7 type a, b, or c.
            Valid range: a, b, c
            Source: visual classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Printed Table D.1 value divided by 1000.

    Assumptions:
        - The caller requests an exact table node.

    Sign convention:
        - Coefficients are non-negative.

    Unit convention:
        - The published integer is divided by the stated scale factor 1000.

    Applicability:
        - Exact reference lookup and formula cross-checking.

    Limitations:
        - No interpolation is performed because the supplied standard gives no interpolation rule for Table D.1.

    Raises:
        TypeError: relative_slenderness_value is not numeric.
        ValueError: section_type or slenderness node is not tabulated.

    Examples:
        >>> annex_d1_stability_coefficient(2.0, "b")
        0.826

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_annex_d1_exact_lookup_and_no_interpolation
        Validation cases:
            - AXIAL-D1-*

    Implementation notes:
        - Values are stored as the printed integers to retain source fidelity.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _require_real(relative_slenderness_value, "relative_slenderness_value")
    key = _require_section_type(section_type)
    for row in _TABLE_D1["rows"]:
        if math.isclose(slenderness, float(row["relative_slenderness"]), rel_tol=0.0, abs_tol=1e-12):
            return float(row[key]) / float(_TABLE_D1["scale_factor"])
    raise ValueError("relative_slenderness_value is not an exact Table D.1 node; interpolation is not implemented")


def central_compression_stability_utilization(
    axial_force_n: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    stability_coefficient: float,
) -> float:
    """
    Summary:
        Calculate the central-compression stability utilization from equation (7).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.1.3
        Annex: None
        Equation/Table: Equation (7)
        Audit ID: SP16-EQ-007
        Normative status: normative

    Mathematical form:
        utilization = N / (phi * A * R_y * gamma_c)

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Central compressive-force magnitude N.
            Valid range: >= 0
            Source: structural analysis
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross cross-sectional area A.
            Valid range: > 0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: Table 1 or applicable clause
        stability_coefficient:
            Type: float
            Unit: dimensionless
            Meaning: phi from equation (8) and its clause rules.
            Valid range: 0 < phi <= 1
            Source: central_compression_stability_coefficient

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (7) utilization; compliance requires <= 1.

    Assumptions:
        - Local stability requirements 7.3.2-7.3.9 are satisfied.

    Sign convention:
        - Compression force is a non-negative magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used directly.

    Applicability:
        - Centrally compressed solid-section members under clause 7.1.3.

    Limitations:
        - Does not perform local plate slenderness checks.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is non-finite or outside its valid range.

    Examples:
        >>> central_compression_stability_utilization(500000.0, 2500.0, 355.0, 1.0, 0.8)
        0.704225352112676

    Tests:
        Unit tests:
            - tests/test_axial_members.py::test_equation_7_normal_zero_and_phi_domain
        Validation cases:
            - AXIAL-EQ-007

    Implementation notes:
        - phi is explicit so equation (7) and equation (8) remain independently testable.
        - Defaults must be explicit in the input configuration.
    """
    force = _require_nonnegative(axial_force_n, "axial_force_n")
    area = _require_positive(gross_area_mm2, "gross_area_mm2")
    resistance = _require_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    gamma_c = _require_positive(working_condition_factor, "working_condition_factor")
    phi = _require_positive(stability_coefficient, "stability_coefficient")
    if phi > 1.0:
        raise ValueError("stability_coefficient must not exceed 1.0")
    return force / (phi * area * resistance * gamma_c)
