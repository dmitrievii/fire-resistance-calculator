"""Base-plate bending and combined axial-force/bending strength checks for SP 16.13330.2017."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .bending_members import annex_e1_base_coefficients

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_E2 = json.loads((_DATA_DIR / "annex_e_table_e2_base_plate_coefficients.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-8.6.1-FOUNDATION-AREA-BOUNDARY",
    "SP16-PROC-8.6.2-TABLE-E2-LOOKUP",
    "SP16-PROC-8.6.2-MAXIMUM-PLATE-MOMENT",
    "SP16-PROC-8.6.2-TWO-SIDE-GEOMETRY",
    "SP16-PROC-9.1.1-EQ105-APPLICABILITY",
    "SP16-PROC-9.1.1-ANNEX-E1-COEFFICIENTS",
    "SP16-PROC-9.1.2-EQ105-OMISSION",
    "SP16-PROC-9.1.3-EQ107-APPLICABILITY",
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


def _bool(value: bool, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")
    return value


def base_plate_required_thickness_eq101(
    maximum_unit_width_moment_n_mm_per_mm: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the required base-plate thickness from the governing unit-width bending moment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: None
        Equation/Table: Equation (101)
        Audit ID: SP16-EQ-101
        Normative status: normative

    Mathematical form:
        t = sqrt(6*M_max/(R_y*gamma_c)).

    Parameters:
        maximum_unit_width_moment_n_mm_per_mm:
            Type: float
            Unit: N*mm/mm
            Meaning: Largest bending moment acting on a unit-width strip of any base-plate region.
            Valid range: >= 0
            Source: equations (102)-(104)
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y of the base-plate steel.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable standard provision

    Returns:
        Type: float
        Unit: mm
        Meaning: Required calculated plate thickness before constructional or product-thickness rounding.

    Assumptions:
        - The governing moment is calculated for a unit-width strip.
        - Foundation bearing pressure and plate-region geometry are already established.

    Sign convention:
        - The governing bending moment is a non-negative magnitude.

    Unit convention:
        - N and mm are used consistently without implicit conversion.

    Applicability:
        - Steel base plates checked as bent plates under clause 8.6.2.

    Limitations:
        - This function does not select a commercial thickness or check foundation resistance.

    Raises:
        ValueError: The moment is negative or a denominator input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> round(base_plate_required_thickness_eq101(125000.0, 250.0, 1.0), 6)
        54.772256

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_101_normal_zero_and_units
        Validation cases:
            - BPCS-EQ-101

    Implementation notes:
        - No corrosion allowance or minimum product thickness is inserted silently.
        - Defaults must be explicit in the input configuration.
    """
    moment = _nonnegative(maximum_unit_width_moment_n_mm_per_mm, "maximum_unit_width_moment_n_mm_per_mm")
    return math.sqrt(6.0 * moment / (_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor")))


def base_plate_cantilever_moment_eq102(
    foundation_pressure_n_mm2: float,
    cantilever_projection_mm: float,
) -> float:
    """
    Summary:
        Calculate the unit-width bending moment of a cantilever base-plate region.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: None
        Equation/Table: Equation (102)
        Audit ID: SP16-EQ-102
        Normative status: normative

    Mathematical form:
        M_1 = 0.5*q*c^2.

    Parameters:
        foundation_pressure_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Reactive foundation bearing pressure q under the plate region.
            Valid range: >= 0
            Source: foundation analysis
        cantilever_projection_mm:
            Type: float
            Unit: mm
            Meaning: Cantilever projection c.
            Valid range: >= 0
            Source: base-plate geometry

    Returns:
        Type: float
        Unit: N*mm/mm
        Meaning: Unit-width cantilever bending moment M_1.

    Assumptions:
        - Bearing pressure is uniform over the considered region.

    Sign convention:
        - Pressure and projection are non-negative magnitudes.

    Unit convention:
        - q in N/mm2 and c in mm produce N*mm per mm strip width.

    Applicability:
        - Cantilever plate regions under clause 8.6.2.

    Limitations:
        - Nonuniform contact pressure is not represented.

    Raises:
        ValueError: An input is negative.
        TypeError: An input is not real.

    Examples:
        >>> base_plate_cantilever_moment_eq102(1.0, 100.0)
        5000.0

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_102_normal_zero_and_quadratic_scaling
        Validation cases:
            - BPCS-EQ-102

    Implementation notes:
        - The coefficient 0.5 is transcribed directly from equation (102).
        - Defaults must be explicit in the input configuration.
    """
    q = _nonnegative(foundation_pressure_n_mm2, "foundation_pressure_n_mm2")
    c = _nonnegative(cantilever_projection_mm, "cantilever_projection_mm")
    return 0.5 * q * c * c


def base_plate_four_side_moments_eq103(
    foundation_pressure_n_mm2: float,
    short_side_mm: float,
    alpha_1: float,
    alpha_2: float,
) -> dict[str, float]:
    """
    Summary:
        Calculate unit-width moments in the short- and long-side directions of a four-side-supported plate region.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: E
        Equation/Table: Equation (103), Table E.2
        Audit ID: SP16-EQ-103
        Normative status: normative

    Mathematical form:
        M_2a = alpha_1*q*a^2; M_2b = alpha_2*q*a^2.

    Parameters:
        foundation_pressure_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Reactive foundation bearing pressure q.
            Valid range: >= 0
            Source: foundation analysis
        short_side_mm:
            Type: float
            Unit: mm
            Meaning: Short side a of the rectangular region.
            Valid range: > 0
            Source: base-plate geometry
        alpha_1:
            Type: float
            Unit: dimensionless
            Meaning: Table E.2 coefficient for the short-side moment direction.
            Valid range: >= 0
            Source: Table E.2
        alpha_2:
            Type: float
            Unit: dimensionless
            Meaning: Table E.2 coefficient for the long-side moment direction.
            Valid range: >= 0
            Source: Table E.2

    Returns:
        Type: dict[str, float]
        Unit: N*mm/mm
        Meaning: Moments M_2a and M_2b.

    Assumptions:
        - The plate region is rectangular and supported on four sides.

    Sign convention:
        - Returned moments are non-negative magnitudes.

    Unit convention:
        - q in N/mm2 and a in mm produce N*mm per mm strip width.

    Applicability:
        - Four-side-supported base-plate regions.

    Limitations:
        - Coefficients must come from an audited Table E.2 lookup.

    Raises:
        ValueError: Pressure or coefficients are negative, or the side length is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> base_plate_four_side_moments_eq103(1.0, 100.0, 0.048, 0.048)
        {'moment_short_direction_n_mm_per_mm': 480.0, 'moment_long_direction_n_mm_per_mm': 480.0}

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_103_normal_zero_and_direction_mapping
        Validation cases:
            - BPCS-EQ-103

    Implementation notes:
        - The function does not infer alpha values from geometry.
        - Defaults must be explicit in the input configuration.
    """
    q = _nonnegative(foundation_pressure_n_mm2, "foundation_pressure_n_mm2")
    a = _positive(short_side_mm, "short_side_mm")
    base = q * a * a
    return {
        "moment_short_direction_n_mm_per_mm": _nonnegative(alpha_1, "alpha_1") * base,
        "moment_long_direction_n_mm_per_mm": _nonnegative(alpha_2, "alpha_2") * base,
    }


def base_plate_three_side_moment_eq104(
    foundation_pressure_n_mm2: float,
    free_side_length_mm: float,
    alpha_3: float,
) -> float:
    """
    Summary:
        Calculate the unit-width bending moment of a plate region supported on three sides.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: E
        Equation/Table: Equation (104), Table E.2
        Audit ID: SP16-EQ-104
        Normative status: normative

    Mathematical form:
        M_3 = alpha_3*q*d_1^2.

    Parameters:
        foundation_pressure_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Reactive foundation bearing pressure q.
            Valid range: >= 0
            Source: foundation analysis
        free_side_length_mm:
            Type: float
            Unit: mm
            Meaning: Free-side length d_1; for two adjacent supported sides, the rectangle diagonal.
            Valid range: > 0
            Source: base-plate geometry
        alpha_3:
            Type: float
            Unit: dimensionless
            Meaning: Table E.2 coefficient based on a_1/d_1.
            Valid range: >= 0
            Source: Table E.2

    Returns:
        Type: float
        Unit: N*mm/mm
        Meaning: Unit-width moment M_3.

    Assumptions:
        - The plate region is supported on three sides or transformed as prescribed for two adjacent sides.

    Sign convention:
        - Returned moment is a non-negative magnitude.

    Unit convention:
        - q in N/mm2 and d_1 in mm produce N*mm per mm strip width.

    Applicability:
        - Three-side-supported and prescribed two-adjacent-side plate regions.

    Limitations:
        - The support configuration must be classified externally.

    Raises:
        ValueError: Pressure or coefficient is negative, or d_1 is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> base_plate_three_side_moment_eq104(1.0, 100.0, 0.112)
        1120.0

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_104_normal_zero_and_quadratic_scaling
        Validation cases:
            - BPCS-EQ-104

    Implementation notes:
        - The two-adjacent-side geometry transformation is provided by a separate audited helper.
        - Defaults must be explicit in the input configuration.
    """
    q = _nonnegative(foundation_pressure_n_mm2, "foundation_pressure_n_mm2")
    d1 = _positive(free_side_length_mm, "free_side_length_mm")
    return _nonnegative(alpha_3, "alpha_3") * q * d1 * d1


def annex_e2_base_plate_coefficients(
    support_condition: str,
    geometric_ratio: float,
) -> dict[str, float]:
    """
    Summary:
        Return exact-node base-plate bending coefficients from Table E.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: E
        Equation/Table: Table E.2
        Audit ID: SP16-PROC-8.6.2-TABLE-E2-LOOKUP
        Normative status: annex reference table

    Mathematical form:
        support condition and printed ratio node -> alpha_1/alpha_2 or alpha_3.

    Parameters:
        support_condition:
            Type: str
            Unit: dimensionless
            Meaning: four_sides or three_sides.
            Valid range: listed values
            Source: engineering support classification
        geometric_ratio:
            Type: float
            Unit: dimensionless
            Meaning: b/a for four sides or a_1/d_1 for three sides.
            Valid range: exact printed node, or a value greater than 2 for the terminal column
            Source: base-plate geometry

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: Applicable Table E.2 coefficient set.

    Assumptions:
        - The support condition is classified correctly.

    Sign convention:
        - Ratios and coefficients are positive.

    Unit convention:
        - The ratio is dimensionless and uses consistent length units.

    Applicability:
        - Equations (103) and (104).

    Limitations:
        - No interpolation is performed because Table E.2 provides no interpolation instruction.

    Raises:
        ValueError: The support condition or ratio is unsupported.
        TypeError: The ratio is not real.

    Examples:
        >>> annex_e2_base_plate_coefficients('four_sides', 1.0)['alpha_1']
        0.048

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_table_e2_exact_lookup_terminal_and_no_interpolation
        Validation cases:
            - BPCS-TBL-E2

    Implementation notes:
        - Values greater than 2 use the printed terminal >2 column.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(geometric_ratio, "geometric_ratio")
    if support_condition not in {"four_sides", "three_sides"}:
        raise ValueError("support_condition must be 'four_sides' or 'three_sides'")
    record = _TABLE_E2[support_condition]
    nodes = [float(x) for x in record["ratio_nodes"]]
    if ratio > 2.0:
        return {key: float(value) for key, value in record["terminal_gt_2"].items()}
    for index, node in enumerate(nodes):
        if math.isclose(ratio, node, rel_tol=0.0, abs_tol=1e-12):
            return {key: float(values[index]) for key, values in record["coefficients"].items()}
    raise ValueError("geometric_ratio must equal a printed Table E.2 node; interpolation is not specified")


def base_plate_two_adjacent_sides_geometry(
    rectangle_side_1_mm: float,
    rectangle_side_2_mm: float,
) -> dict[str, float]:
    """
    Summary:
        Derive the diagonal and perpendicular vertex-to-diagonal distance for the two-adjacent-side rule.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: E
        Equation/Table: Text following equation (104), Table E.2 geometry symbols
        Audit ID: SP16-PROC-8.6.2-TWO-SIDE-GEOMETRY
        Normative status: normative procedure

    Mathematical form:
        d_1 = sqrt(a^2+b^2); a_1 = a*b/d_1; ratio = a_1/d_1.

    Parameters:
        rectangle_side_1_mm:
            Type: float
            Unit: mm
            Meaning: First side of the rectangular region.
            Valid range: > 0
            Source: base-plate geometry
        rectangle_side_2_mm:
            Type: float
            Unit: mm
            Meaning: Second side of the rectangular region.
            Valid range: > 0
            Source: base-plate geometry

    Returns:
        Type: dict[str, float]
        Unit: mm and dimensionless
        Meaning: Diagonal d_1, perpendicular distance a_1, and ratio a_1/d_1.

    Assumptions:
        - The region is rectangular and the diagonal connects the ends of the two supported sides.

    Sign convention:
        - Lengths are positive.

    Unit convention:
        - Both sides use the same length unit, returned as mm.

    Applicability:
        - Plate regions supported on two adjacent sides and treated by equation (104).

    Limitations:
        - Irregular polygonal regions require an external geometric model.

    Raises:
        ValueError: A side length is non-positive.
        TypeError: A side length is not real.

    Examples:
        >>> round(base_plate_two_adjacent_sides_geometry(300.0, 400.0)['diagonal_d1_mm'], 6)
        500.0

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_two_adjacent_side_geometry
        Validation cases:
            - BPCS-PROC-TWO-SIDE

    Implementation notes:
        - The geometric relation is a direct Euclidean derivation of the dimensions named by clause 8.6.2.
        - Defaults must be explicit in the input configuration.
    """
    side_1 = _positive(rectangle_side_1_mm, "rectangle_side_1_mm")
    side_2 = _positive(rectangle_side_2_mm, "rectangle_side_2_mm")
    diagonal = math.hypot(side_1, side_2)
    perpendicular = side_1 * side_2 / diagonal
    return {
        "diagonal_d1_mm": diagonal,
        "perpendicular_distance_a1_mm": perpendicular,
        "ratio_a1_over_d1": perpendicular / diagonal,
    }


def base_plate_maximum_unit_width_moment(moment_values_n_mm_per_mm: list[float] | tuple[float, ...]) -> float:
    """
    Summary:
        Select the governing base-plate unit-width moment from all considered regions and directions.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: None
        Equation/Table: Definition of M_max preceding equations (102)-(104)
        Audit ID: SP16-PROC-8.6.2-MAXIMUM-PLATE-MOMENT
        Normative status: normative procedure

    Mathematical form:
        M_max = max(M_i).

    Parameters:
        moment_values_n_mm_per_mm:
            Type: list[float] | tuple[float, ...]
            Unit: N*mm/mm
            Meaning: Candidate unit-width moment magnitudes from all plate regions and directions.
            Valid range: non-empty sequence of values >= 0
            Source: equations (102)-(104)

    Returns:
        Type: float
        Unit: N*mm/mm
        Meaning: Governing moment M_max for equation (101).

    Assumptions:
        - Every relevant plate region and direction is represented.

    Sign convention:
        - Candidate moments are non-negative magnitudes.

    Unit convention:
        - All candidates use the same unit-width moment unit.

    Applicability:
        - Base-plate thickness calculation.

    Limitations:
        - Missing regions cannot be detected automatically.

    Raises:
        ValueError: The sequence is empty or contains a negative/non-finite value.
        TypeError: The input is not a list or tuple of real values.

    Examples:
        >>> base_plate_maximum_unit_width_moment([100.0, 250.0, 200.0])
        250.0

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_maximum_plate_moment
        Validation cases:
            - BPCS-PROC-MAX-MOMENT

    Implementation notes:
        - No candidate is generated or omitted implicitly.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(moment_values_n_mm_per_mm, (list, tuple)):
        raise TypeError("moment_values_n_mm_per_mm must be a list or tuple")
    if not moment_values_n_mm_per_mm:
        raise ValueError("moment_values_n_mm_per_mm must not be empty")
    return max(_nonnegative(value, f"moment_values_n_mm_per_mm[{index}]") for index, value in enumerate(moment_values_n_mm_per_mm))


def base_plate_foundation_area_boundary(
    foundation_strength_check_confirmed: bool,
) -> dict[str, Any]:
    """
    Summary:
        Record the clause 8.6.1 external foundation-strength boundary for base-plate area.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.1
        Annex: None
        Equation/Table: Unnumbered requirement
        Audit ID: SP16-PROC-8.6.1-FOUNDATION-AREA-BOUNDARY
        Normative status: normative external boundary

    Mathematical form:
        Explicit confirmation -> permitted status; no foundation formula is invented.

    Parameters:
        foundation_strength_check_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation that plate area satisfies the applicable foundation-strength calculation.
            Valid range: true or false
            Source: external foundation design

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Confirmation status and external-boundary explanation.

    Assumptions:
        - The external foundation calculation is independently verified.

    Sign convention:
        - No signed quantity is used.

    Unit convention:
        - No numerical unit is used.

    Applicability:
        - All base-plate calculations under clause 8.6.

    Limitations:
        - The package does not calculate concrete/foundation bearing resistance in this release.

    Raises:
        TypeError: The confirmation is not bool.

    Examples:
        >>> base_plate_foundation_area_boundary(True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_foundation_area_boundary
        Validation cases:
            - BPCS-PROC-8.6.1

    Implementation notes:
        - This function preserves the external dependency instead of fabricating a foundation model.
        - Defaults must be explicit in the input configuration.
    """
    confirmed = _bool(foundation_strength_check_confirmed, "foundation_strength_check_confirmed")
    return {
        "permitted": confirmed,
        "status": "external_foundation_strength_check_confirmed" if confirmed else "external_foundation_strength_check_required",
    }


def combined_force_strength_utilization_eq105(
    axial_force_n: float,
    net_area_mm2: float,
    bending_moment_x_n_mm: float,
    bending_moment_y_n_mm: float,
    bimoment_n_mm2: float,
    coefficient_n: float,
    coefficient_cx: float,
    coefficient_cy: float,
    minimum_net_section_modulus_x_mm3: float,
    minimum_net_section_modulus_y_mm3: float,
    minimum_net_sectorial_section_modulus_mm4: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the section-strength utilization for combined axial force, biaxial bending, and bimoment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.1
        Annex: E
        Equation/Table: Equation (105), Table E.1
        Audit ID: SP16-EQ-105
        Normative status: normative

    Mathematical form:
        eta = (N/(A_n*R_y*gamma_c))^n + M_x/(c_x*W_xn,min*R_y*gamma_c) + M_y/(c_y*W_yn,min*R_y*gamma_c) + B/(W_omega,n,min*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Absolute axial-force value N.
            Valid range: >= 0
            Source: governing load combination
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net section area A_n.
            Valid range: > 0
            Source: section properties
        bending_moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Absolute major-axis bending moment M_x.
            Valid range: >= 0
            Source: governing load combination
        bending_moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Absolute minor-axis bending moment M_y.
            Valid range: >= 0
            Source: governing load combination
        bimoment_n_mm2:
            Type: float
            Unit: N*mm2
            Meaning: Absolute bimoment B.
            Valid range: >= 0
            Source: governing load combination
        coefficient_n:
            Type: float
            Unit: dimensionless
            Meaning: Exponent n from Table E.1.
            Valid range: > 0
            Source: Table E.1
        coefficient_cx:
            Type: float
            Unit: dimensionless
            Meaning: Major-axis coefficient c_x from Table E.1.
            Valid range: > 0
            Source: Table E.1
        coefficient_cy:
            Type: float
            Unit: dimensionless
            Meaning: Minor-axis coefficient c_y from Table E.1.
            Valid range: > 0
            Source: Table E.1
        minimum_net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: Minimum net section modulus W_xn,min.
            Valid range: > 0
            Source: section properties
        minimum_net_section_modulus_y_mm3:
            Type: float
            Unit: mm3
            Meaning: Minimum net section modulus W_yn,min.
            Valid range: > 0
            Source: section properties
        minimum_net_sectorial_section_modulus_mm4:
            Type: float
            Unit: mm4
            Meaning: Minimum net sectorial section modulus W_omega,n,min.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable standard provision

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (105) utilization; pass when <= 1.

    Assumptions:
        - All action values belong to one governing combination.
        - Applicability conditions in clause 9.1.1 are satisfied.

    Sign convention:
        - N, M_x, M_y, and B are absolute values as stated in clause 9.1.1.

    Unit convention:
        - N and mm units are used consistently without conversion.

    Applicability:
        - Eccentrically compressed/tensioned solid-section members covered by equation (105).

    Limitations:
        - Stability and local-stability checks remain separate.

    Raises:
        ValueError: An action is negative or a denominator/coefficient input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> combined_force_strength_utilization_eq105(100000.0, 2000.0, 1e7, 0.0, 0.0, 1.0, 1.0, 1.0, 1e6, 1e6, 1e9, 250.0, 1.0)
        0.24

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_105_normal_zero_and_units
        Validation cases:
            - BPCS-EQ-105

    Implementation notes:
        - Table E.1 coefficients are explicit inputs or obtained through the audited helper.
        - Defaults must be explicit in the input configuration.
    """
    resistance = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor")
    axial_ratio = _nonnegative(axial_force_n, "axial_force_n") / (_positive(net_area_mm2, "net_area_mm2") * resistance)
    axial_term = axial_ratio ** _positive(coefficient_n, "coefficient_n")
    mx_term = _nonnegative(bending_moment_x_n_mm, "bending_moment_x_n_mm") / (_positive(coefficient_cx, "coefficient_cx") * _positive(minimum_net_section_modulus_x_mm3, "minimum_net_section_modulus_x_mm3") * resistance)
    my_term = _nonnegative(bending_moment_y_n_mm, "bending_moment_y_n_mm") / (_positive(coefficient_cy, "coefficient_cy") * _positive(minimum_net_section_modulus_y_mm3, "minimum_net_section_modulus_y_mm3") * resistance)
    b_term = _nonnegative(bimoment_n_mm2, "bimoment_n_mm2") / (_positive(minimum_net_sectorial_section_modulus_mm4, "minimum_net_sectorial_section_modulus_mm4") * resistance)
    return axial_term + mx_term + my_term + b_term


def combined_force_point_utilization_eq106(
    signed_axial_force_n: float,
    net_area_mm2: float,
    signed_bending_moment_x_n_mm: float,
    point_y_mm: float,
    net_inertia_x_mm4: float,
    signed_bending_moment_y_n_mm: float,
    point_x_mm: float,
    net_inertia_y_mm4: float,
    signed_bimoment_n_mm2: float,
    sectorial_coordinate_mm2: float,
    net_sectorial_inertia_mm6: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the elastic point-stress utilization for combined axial force, biaxial bending, and bimoment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.1
        Annex: None
        Equation/Table: Equation (106)
        Audit ID: SP16-EQ-106
        Normative status: normative

    Mathematical form:
        eta = |N/A_n + M_x*y/I_xn + M_y*x/I_yn + B*omega/I_omega,n|/(R_y*gamma_c).

    Parameters:
        signed_axial_force_n:
            Type: float
            Unit: N
            Meaning: Signed axial force N.
            Valid range: any finite real
            Source: governing load combination
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net area A_n.
            Valid range: > 0
            Source: section properties
        signed_bending_moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Signed major-axis moment M_x.
            Valid range: any finite real
            Source: governing load combination
        point_y_mm:
            Type: float
            Unit: mm
            Meaning: Signed point coordinate y.
            Valid range: any finite real
            Source: section geometry
        net_inertia_x_mm4:
            Type: float
            Unit: mm4
            Meaning: Net second moment of area I_xn.
            Valid range: > 0
            Source: section properties
        signed_bending_moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Signed minor-axis moment M_y.
            Valid range: any finite real
            Source: governing load combination
        point_x_mm:
            Type: float
            Unit: mm
            Meaning: Signed point coordinate x.
            Valid range: any finite real
            Source: section geometry
        net_inertia_y_mm4:
            Type: float
            Unit: mm4
            Meaning: Net second moment of area I_yn.
            Valid range: > 0
            Source: section properties
        signed_bimoment_n_mm2:
            Type: float
            Unit: N*mm2
            Meaning: Signed bimoment B.
            Valid range: any finite real
            Source: governing load combination
        sectorial_coordinate_mm2:
            Type: float
            Unit: mm2
            Meaning: Signed sectorial coordinate omega of the checked point.
            Valid range: any finite real
            Source: section geometry
        net_sectorial_inertia_mm6:
            Type: float
            Unit: mm6
            Meaning: Net sectorial moment of inertia I_omega,n.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable standard provision

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Absolute point-stress utilization; pass when <= 1.

    Assumptions:
        - All signs and coordinates use one consistent section convention.

    Sign convention:
        - Stress contributions are summed algebraically before taking the absolute value.

    Unit convention:
        - N and mm units are used consistently without conversion.

    Applicability:
        - Cases not covered by equation (105).

    Limitations:
        - The function checks one section point; all governing points must be evaluated externally.

    Raises:
        ValueError: A denominator input is non-positive or any value is non-finite.
        TypeError: An input is not real.

    Examples:
        >>> combined_force_point_utilization_eq106(100000.0, 2000.0, 1e7, 100.0, 1e9, 0.0, 0.0, 1e9, 0.0, 0.0, 1e12, 250.0, 1.0)
        0.204

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_106_sign_superposition_zero_and_units
        Validation cases:
            - BPCS-EQ-106

    Implementation notes:
        - The printed plus/minus alternatives are represented by signed actions and coordinates.
        - Defaults must be explicit in the input configuration.
    """
    stress = (
        _real(signed_axial_force_n, "signed_axial_force_n") / _positive(net_area_mm2, "net_area_mm2")
        + _real(signed_bending_moment_x_n_mm, "signed_bending_moment_x_n_mm") * _real(point_y_mm, "point_y_mm") / _positive(net_inertia_x_mm4, "net_inertia_x_mm4")
        + _real(signed_bending_moment_y_n_mm, "signed_bending_moment_y_n_mm") * _real(point_x_mm, "point_x_mm") / _positive(net_inertia_y_mm4, "net_inertia_y_mm4")
        + _real(signed_bimoment_n_mm2, "signed_bimoment_n_mm2") * _real(sectorial_coordinate_mm2, "sectorial_coordinate_mm2") / _positive(net_sectorial_inertia_mm6, "net_sectorial_inertia_mm6")
    )
    return abs(stress) / (_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor"))


def high_strength_asymmetric_delta_eq108(
    compression_force_n: float,
    relative_slenderness: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the delta coefficient for the high-strength asymmetric-section tension-fiber check.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.3
        Annex: None
        Equation/Table: Equation (108)
        Audit ID: SP16-EQ-108
        Normative status: normative

    Mathematical form:
        delta = 1 - 0.1*N*lambda_bar^2/(A*R_y).

    Parameters:
        compression_force_n:
            Type: float
            Unit: N
            Meaning: Compression force N, taken with a positive sign.
            Valid range: >= 0
            Source: governing load combination
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar.
            Valid range: >= 0
            Source: stability model
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross area A.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Delta coefficient used in equation (107).

    Assumptions:
        - N is supplied as a positive compression magnitude.

    Sign convention:
        - Compression force is positive exactly as specified after equation (108).

    Unit convention:
        - N, mm2, and N/mm2 are used consistently.

    Applicability:
        - Clause 9.1.3 high-strength asymmetric solid sections.

    Limitations:
        - Equation (107) additionally requires delta > 0.

    Raises:
        ValueError: N or lambda_bar is negative, or a denominator input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> high_strength_asymmetric_delta_eq108(100000.0, 2.0, 2000.0, 250.0)
        0.92

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_108_normal_zero_and_dimensionless_scaling
        Validation cases:
            - BPCS-EQ-108

    Implementation notes:
        - No lower cap is introduced; a non-positive delta is rejected by equation (107).
        - Defaults must be explicit in the input configuration.
    """
    force = _nonnegative(compression_force_n, "compression_force_n")
    slenderness = _nonnegative(relative_slenderness, "relative_slenderness")
    return 1.0 - 0.1 * force * slenderness * slenderness / (_positive(gross_area_mm2, "gross_area_mm2") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2"))


def high_strength_asymmetric_tension_fiber_utilization_eq107(
    compression_force_n: float,
    net_area_mm2: float,
    bending_moment_n_mm: float,
    delta_coefficient: float,
    tension_fiber_section_modulus_mm3: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the tension-fiber strength utilization of a high-strength asymmetric compressed member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.3
        Annex: None
        Equation/Table: Equation (107)
        Audit ID: SP16-EQ-107
        Normative status: normative

    Mathematical form:
        eta = gamma_u/(R_u*gamma_c)*|N/A_n - M/(delta*W_tn)|.

    Parameters:
        compression_force_n:
            Type: float
            Unit: N
            Meaning: Compression force N, taken with a positive sign.
            Valid range: >= 0
            Source: governing load combination
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net area A_n.
            Valid range: > 0
            Source: section properties
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Bending-moment magnitude M in the symmetry plane.
            Valid range: >= 0
            Source: governing load combination
        delta_coefficient:
            Type: float
            Unit: dimensionless
            Meaning: Delta from equation (108).
            Valid range: > 0
            Source: equation (108)
        tension_fiber_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Section modulus W_tn for the tension fiber.
            Valid range: > 0
            Source: net section properties
        design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design ultimate resistance R_u.
            Valid range: > 0
            Source: clause 6.1
        ultimate_resistance_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Safety factor gamma_u.
            Valid range: > 0
            Source: clause 4.3.2
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable standard provision

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (107) utilization; pass when <= 1.

    Assumptions:
        - The applicability conditions of clause 9.1.3 are satisfied.

    Sign convention:
        - N is positive in compression and M is a non-negative magnitude; the printed subtraction is preserved.

    Unit convention:
        - N and mm units are used consistently without conversion.

    Applicability:
        - High-strength steel with R_yn > 440 N/mm2 and the specified asymmetric section condition.

    Limitations:
        - Stability and other section points are not checked by this equation.

    Raises:
        ValueError: A magnitude is negative or a denominator/coefficient input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> high_strength_asymmetric_tension_fiber_utilization_eq107(100000.0, 2000.0, 2e7, 0.8, 1e6, 500.0, 1.3, 1.0)
        0.065

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_107_normal_zero_and_subtraction_sign
        Validation cases:
            - BPCS-EQ-107

    Implementation notes:
        - A non-positive delta is rejected rather than clipped.
        - Defaults must be explicit in the input configuration.
    """
    stress = _nonnegative(compression_force_n, "compression_force_n") / _positive(net_area_mm2, "net_area_mm2") - _nonnegative(bending_moment_n_mm, "bending_moment_n_mm") / (_positive(delta_coefficient, "delta_coefficient") * _positive(tension_fiber_section_modulus_mm3, "tension_fiber_section_modulus_mm3"))
    return _positive(ultimate_resistance_safety_factor, "ultimate_resistance_safety_factor") * abs(stress) / (_positive(design_ultimate_resistance_n_mm2, "design_ultimate_resistance_n_mm2") * _positive(working_condition_factor, "working_condition_factor"))


def equation_105_applicability(
    normative_yield_resistance_n_mm2: float,
    direct_dynamic_load: bool,
    shear_stress_n_mm2: float,
    design_shear_resistance_n_mm2: float,
    axial_force_n: float,
    net_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    clause_8_5_8_confirmed: bool,
    clause_8_5_18_confirmed: bool,
) -> dict[str, Any]:
    """
    Summary:
        Evaluate the explicit applicability conditions surrounding equation (105).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.1
        Annex: None
        Equation/Table: Conditions preceding and following equation (105)
        Audit ID: SP16-PROC-9.1.1-EQ105-APPLICABILITY
        Normative status: normative procedure

    Mathematical form:
        R_yn <= 440; no direct dynamic load; tau < 0.5*R_s; low axial stress requires clauses 8.5.8 and 8.5.18.

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance R_yn.
            Valid range: > 0
            Source: material specification
        direct_dynamic_load:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the member is directly subjected to dynamic load.
            Valid range: true or false
            Source: load classification
        shear_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Shear-stress magnitude tau.
            Valid range: >= 0
            Source: section analysis
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_s.
            Valid range: > 0
            Source: clause 6.1
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Axial-force magnitude N.
            Valid range: >= 0
            Source: governing load combination
        net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net section area A_n.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        clause_8_5_8_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of clause 8.5.8 when axial stress is <= 0.1 R_y.
            Valid range: true or false
            Source: separate local-stability check
        clause_8_5_18_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of clause 8.5.18 when axial stress is <= 0.1 R_y.
            Valid range: true or false
            Source: separate local-stability check

    Returns:
        Type: dict[str, Any]
        Unit: status and N/mm2
        Meaning: Applicability status, axial stress, and explicit reasons.

    Assumptions:
        - Input stresses and resistances refer to the same design situation.

    Sign convention:
        - N and tau are non-negative magnitudes.

    Unit convention:
        - Stress quantities use N/mm2.

    Applicability:
        - Routing between equation (105) and other strength procedures.

    Limitations:
        - This function does not prove the truth of external confirmations.

    Raises:
        ValueError: A magnitude is negative or a denominator input is non-positive.
        TypeError: A flag is not bool or a numerical input is not real.

    Examples:
        >>> equation_105_applicability(355.0, False, 40.0, 100.0, 100000.0, 2000.0, 250.0, True, True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_105_applicability_boundaries
        Validation cases:
            - BPCS-PROC-9.1.1

    Implementation notes:
        - The strict tau < 0.5 R_s inequality is preserved.
        - Defaults must be explicit in the input configuration.
    """
    ryn = _positive(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2")
    dynamic = _bool(direct_dynamic_load, "direct_dynamic_load")
    tau = _nonnegative(shear_stress_n_mm2, "shear_stress_n_mm2")
    rs = _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
    sigma = _nonnegative(axial_force_n, "axial_force_n") / _positive(net_area_mm2, "net_area_mm2")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    local_ok = _bool(clause_8_5_8_confirmed, "clause_8_5_8_confirmed") and _bool(clause_8_5_18_confirmed, "clause_8_5_18_confirmed")
    reasons: list[str] = []
    if ryn > 440.0:
        reasons.append("normative_yield_resistance_exceeds_440")
    if dynamic:
        reasons.append("direct_dynamic_load_not_permitted")
    if not tau < 0.5 * rs:
        reasons.append("shear_stress_must_be_less_than_0_5_Rs")
    low_axial = sigma <= 0.1 * ry
    if low_axial and not local_ok:
        reasons.append("low_axial_stress_requires_clauses_8_5_8_and_8_5_18")
    return {"permitted": not reasons, "axial_stress_n_mm2": sigma, "low_axial_stress_branch": low_axial, "reasons": reasons}


def combined_force_coefficients_from_annex_e1(
    section_type: str,
    flange_to_web_area_ratio: float,
    minor_axis_moment_nonzero: bool,
) -> dict[str, float]:
    """
    Summary:
        Obtain equation (105) coefficients c_x, c_y, and n from the audited Table E.1 implementation.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.1
        Annex: E
        Equation/Table: Equation (105), Table E.1
        Audit ID: SP16-PROC-9.1.1-ANNEX-E1-COEFFICIENTS
        Normative status: normative procedure

    Mathematical form:
        Table E.1 section type and A_f/A_w -> c_x, c_y, n.

    Parameters:
        section_type:
            Type: str
            Unit: dimensionless
            Meaning: Audited Table E.1 section-type identifier.
            Valid range: identifiers supported by annex_e1_base_coefficients
            Source: engineering section classification
        flange_to_web_area_ratio:
            Type: float
            Unit: dimensionless
            Meaning: A_f/A_w ratio used by Table E.1.
            Valid range: table-specific interval
            Source: section properties
        minor_axis_moment_nonzero:
            Type: bool
            Unit: dimensionless
            Meaning: Whether M_y is nonzero for the Table E.1 exponent note.
            Valid range: true or false
            Source: governing load combination

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: c_x, c_y, and n values.

    Assumptions:
        - The section type is selected from the annex diagram correctly.

    Sign convention:
        - No signed action is used.

    Unit convention:
        - The area ratio is dimensionless.

    Applicability:
        - Equation (105).

    Limitations:
        - Arbitrary geometry classification remains external.

    Raises:
        ValueError: The section type or area ratio is outside Table E.1.
        TypeError: The moment flag is not bool or the ratio is not real.

    Examples:
        >>> combined_force_coefficients_from_annex_e1('1', 0.75, False)['c_x']
        1.095

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_combined_force_coefficients_use_annex_e1
        Validation cases:
            - BPCS-PROC-E1

    Implementation notes:
        - This function delegates to the already audited v0.6 Table E.1 implementation.
        - Defaults must be explicit in the input configuration.
    """
    _bool(minor_axis_moment_nonzero, "minor_axis_moment_nonzero")
    result = annex_e1_base_coefficients(section_type, _positive(flange_to_web_area_ratio, "flange_to_web_area_ratio"), minor_axis_moment_nonzero)
    return {"c_x": float(result["c_x"]), "c_y": float(result["c_y"]), "n": float(result["n"])}


def equation_105_omission_rule_clause_9_1_2(
    reduced_relative_eccentricity: float,
    section_is_unweakened: bool,
    strength_and_stability_moments_are_equal: bool,
) -> dict[str, Any]:
    """
    Summary:
        Determine whether clause 9.1.2 permits omission of the equation (105) strength check.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.2
        Annex: None
        Equation/Table: Unnumbered omission rule referring to equation (105)
        Audit ID: SP16-PROC-9.1.2-EQ105-OMISSION
        Normative status: normative procedure

    Mathematical form:
        Omit when m_ef <= 20, section is unweakened, and strength/stability moments are equal.

    Parameters:
        reduced_relative_eccentricity:
            Type: float
            Unit: dimensionless
            Meaning: Reduced relative eccentricity m_ef from clause 9.2.2.
            Valid range: >= 0
            Source: stability calculation
        section_is_unweakened:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the section has no weakening.
            Valid range: true or false
            Source: section model
        strength_and_stability_moments_are_equal:
            Type: bool
            Unit: dimensionless
            Meaning: Whether identical bending moments are used in strength and stability checks.
            Valid range: true or false
            Source: analysis model

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Whether the equation (105) check may be omitted and the reason.

    Assumptions:
        - m_ef has been calculated according to clause 9.2.2.

    Sign convention:
        - Eccentricity is a non-negative magnitude.

    Unit convention:
        - m_ef is dimensionless.

    Applicability:
        - Eccentrically compressed members considered under equation (105).

    Limitations:
        - This procedure does not perform the stability check that remains necessary.

    Raises:
        ValueError: m_ef is negative.
        TypeError: A flag is not bool or m_ef is not real.

    Examples:
        >>> equation_105_omission_rule_clause_9_1_2(10.0, True, True)['may_omit_equation_105']
        True

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_105_omission_rule
        Validation cases:
            - BPCS-PROC-9.1.2

    Implementation notes:
        - The <= 20 condition is transcribed exactly from the supplied consolidated text.
        - Defaults must be explicit in the input configuration.
    """
    eccentricity = _nonnegative(reduced_relative_eccentricity, "reduced_relative_eccentricity")
    unweakened = _bool(section_is_unweakened, "section_is_unweakened")
    equal_moments = _bool(strength_and_stability_moments_are_equal, "strength_and_stability_moments_are_equal")
    allowed = eccentricity <= 20.0 and unweakened and equal_moments
    return {"may_omit_equation_105": allowed, "reason": "all_clause_9_1_2_conditions_met" if allowed else "equation_105_required"}


def equation_107_applicability(
    normative_yield_resistance_n_mm2: float,
    section_is_asymmetric_about_axis_perpendicular_to_bending_plane: bool,
) -> dict[str, Any]:
    """
    Summary:
        Evaluate the material-strength and section-symmetry conditions for equation (107).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.1.3
        Annex: D
        Equation/Table: Equation (107), example section types 10 and 11 of Table D.2
        Audit ID: SP16-PROC-9.1.3-EQ107-APPLICABILITY
        Normative status: normative procedure

    Mathematical form:
        Permitted when R_yn > 440 N/mm2 and the section is asymmetric about the axis perpendicular to bending.

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance R_yn.
            Valid range: > 0
            Source: material specification
        section_is_asymmetric_about_axis_perpendicular_to_bending_plane:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the section meets the specified asymmetry condition.
            Valid range: true or false
            Source: engineering section classification

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Applicability status and explicit reasons.

    Assumptions:
        - The section symmetry classification is correct.

    Sign convention:
        - No signed action is used.

    Unit convention:
        - Material resistance uses N/mm2.

    Applicability:
        - Clause 9.1.3 tension-fiber check.

    Limitations:
        - Table D.2 geometry classification is not automated.

    Raises:
        ValueError: R_yn is non-positive.
        TypeError: The symmetry flag is not bool or R_yn is not real.

    Examples:
        >>> equation_107_applicability(460.0, True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_equation_107_applicability
        Validation cases:
            - BPCS-PROC-9.1.3

    Implementation notes:
        - The function does not infer section type 10 or 11 from geometry.
        - Defaults must be explicit in the input configuration.
    """
    ryn = _positive(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2")
    asymmetric = _bool(section_is_asymmetric_about_axis_perpendicular_to_bending_plane, "section_is_asymmetric_about_axis_perpendicular_to_bending_plane")
    reasons: list[str] = []
    if ryn <= 440.0:
        reasons.append("normative_yield_resistance_must_exceed_440")
    if not asymmetric:
        reasons.append("required_section_asymmetry_not_confirmed")
    return {"permitted": not reasons, "reasons": reasons}


def annex_e2_catalog() -> dict[str, Any]:
    """
    Summary:
        Return a defensive copy of the transcribed Table E.2 data and extraction metadata.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 8.6.2
        Annex: E
        Equation/Table: Table E.2
        Audit ID: SP16-TBL-Е-2
        Normative status: annex reference table

    Mathematical form:
        Stored JSON data -> independent Python dictionary copy.

    Parameters:
        None:
            Type: None
            Unit: not applicable
            Meaning: No input.
            Valid range: not applicable
            Source: not applicable

    Returns:
        Type: dict[str, Any]
        Unit: dimensionless coefficients and metadata
        Meaning: Complete transcribed Table E.2 dataset.

    Assumptions:
        - The packaged JSON file has passed release-manifest verification.

    Sign convention:
        - Coefficients and ratios are positive.

    Unit convention:
        - Ratios and coefficients are dimensionless.

    Applicability:
        - Audit, tests, documentation, and exact-node lookup.

    Limitations:
        - The table contains no interpolation instruction.

    Raises:
        OSError: The packaged data file cannot be read during module import.

    Examples:
        >>> len(annex_e2_catalog()['four_sides']['ratio_nodes'])
        11

    Tests:
        Unit tests:
            - tests/test_base_plates_and_combined_force_strength.py::test_table_e2_catalog_consistency
        Validation cases:
            - BPCS-TBL-E2-CATALOG

    Implementation notes:
        - JSON round-tripping prevents callers from mutating module-level data.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_E2, ensure_ascii=False))
