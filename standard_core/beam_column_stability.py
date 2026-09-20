"""Beam-column stability checks for Section 9.2 and Annex D of SP 16.13330.2017."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_ANNEX_D = json.loads((_DATA_DIR / "annex_d_tables_d2_to_d6.json").read_text(encoding="utf-8"))
_TABLE_20 = json.loads((_DATA_DIR / "table_20_effective_moment_rules.json").read_text(encoding="utf-8"))
_TABLE_21 = json.loads((_DATA_DIR / "table_21_out_of_plane_coefficients.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-9.2.1-TWO-PLANE-STABILITY",
    "SP16-PROC-9.2.2-D3-LOOKUP-AND-CAP",
    "SP16-PROC-9.2.2-BENDING-ROUTE-MEFF-GT20",
    "SP16-PROC-9.2.3-SAME-LOAD-COMBINATION",
    "SP16-PROC-9.2.3-DESIGN-MOMENT-SELECTION",
    "SP16-PROC-9.2.3-TABLE-20-ROUTING",
    "SP16-PROC-9.2.3-TABLE-D5-ROUTING",
    "SP16-PROC-9.2.5-TABLE-21-ROUTING",
    "SP16-PROC-9.2.5-CMAX-CAP-AND-MINIMUM",
    "SP16-PROC-9.2.6-DESIGN-MOMENT-SELECTION",
    "SP16-PROC-9.2.7-CONTINUOUS-FLANGE-BRACING",
    "SP16-PROC-9.2.8-MINOR-AXIS-ROUTING",
    "SP16-PROC-9.2.9-BIAXIAL-ADDITIONAL-CHECKS",
    "SP16-PROC-9.2.9-NONSYMMETRIC-MX-INCREASE",
    "SP16-PROC-9.2.10-BOX-MAJOR-AXIS-SUBSTITUTION",
    "SP16-PROC-ANNEX-D2-SHAPE-COEFFICIENT",
    "SP16-PROC-ANNEX-D3-EXACT-LOOKUP",
    "SP16-PROC-ANNEX-D4-EXACT-LOOKUP",
    "SP16-PROC-ANNEX-D5-EXACT-LOOKUP",
    "SP16-PROC-ANNEX-D6-SECTION-PARAMETERS",
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


def _ratio_0_1(value: float, name: str) -> float:
    result = _real(value, name)
    if not 0.0 < result <= 1.0:
        raise ValueError(f"{name} must be in (0, 1]")
    return result


def _exact_key(value: float, allowed: list[float], name: str) -> str:
    number = _real(value, name)
    for item in allowed:
        if math.isclose(number, float(item), rel_tol=0.0, abs_tol=1e-12):
            return str(float(item))
    raise ValueError(f"{name} must equal a printed table node: {allowed}")


def _doc_table_raw(table_id: str, row_value: float, column_value: float) -> float:
    table = _ANNEX_D["tables"][table_id]
    row_key = _exact_key(row_value, [float(x) for x in table["rows"].keys()], "row_value")
    row = table["rows"][row_key]
    column_key = _exact_key(column_value, [float(x) for x in row.keys()], "column_value")
    return float(row[column_key]) / float(table["scale_divisor"])



def _axis_bracket(value: float, nodes: list[float], name: str) -> tuple[float, float]:
    """Return an enclosing printed-node pair without extrapolation."""
    x = _real(value, name)
    ordered = sorted(float(v) for v in nodes)
    if x < ordered[0] - 1e-12 or x > ordered[-1] + 1e-12:
        raise ValueError(f"{name}={x} lies outside the printed table domain [{ordered[0]}, {ordered[-1]}]")
    for node in ordered:
        if math.isclose(x, node, rel_tol=0.0, abs_tol=1e-12):
            return node, node
    for lo, hi in zip(ordered, ordered[1:]):
        if lo < x < hi:
            return lo, hi
    raise ValueError(f"Unable to bracket {name}={x} inside the printed table domain")


def _annex_d3_interpolated_table_coefficient(relative_slenderness: float, effective_relative_eccentricity: float) -> float:
    """
    Summary:
        Resolve Table D.3 at an arbitrary in-domain point by explicit bilinear interpolation between surrounding printed nodes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.2.2
        Annex: D
        Equation/Table: Table D.3
        Audit ID: SP16-TBL-Д-3-INTERP-HF1
        Normative status: engineering digital-table interpolation policy over normative printed data

    Mathematical form:
        Exact-node return when both coordinates are printed nodes; one-dimensional linear interpolation when one coordinate is exact; otherwise bilinear interpolation over the four enclosing printed cells.

    Parameters:
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar.
            Valid range: within the printed Table D.3 row domain.
            Source: clause 9.2.2.
        effective_relative_eccentricity:
            Type: float
            Unit: dimensionless
            Meaning: Effective relative eccentricity m_eff.
            Valid range: within the printed Table D.3 column domain.
            Source: equation (110).

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Interpolated raw Table D.3 stability coefficient before the central-compression cap.

    Assumptions:
        - Linear interpolation is applied independently on the two tabulated coordinates.
        - The policy is an explicit digital implementation rule; the printed SP16 table itself does not state a separate interpolation formula.
        - Historical NormCAD evidence VAL-SP16-BEAMCOL-0008 is retained as a secondary oracle and reproduces this bilinear policy to the reported precision.

    Sign convention:
        - lambda_bar and m_eff are non-negative dimensionless magnitudes.

    Unit convention:
        - Printed integer coefficients are divided by 1000 before interpolation.

    Applicability:
        - Table D.3 solid-member in-plane eccentric-compression stability, only inside the printed table domain.

    Limitations:
        - Extrapolation outside the printed row or column domain is forbidden.
        - The normative cap phi_e <= phi is applied separately by annex_d3_stability_coefficient.

    Raises:
        ValueError: Either coordinate lies outside the printed table domain.
        TypeError: Either coordinate is not real.

    Examples:
        >>> round(_annex_d3_interpolated_table_coefficient(1.61095, 6.67245), 5)
        0.18771

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py
            - tests/test_stage_n5_beam_column_workflows.py
        Validation cases:
            - VAL-SP16-BEAMCOL-0008 (historical NormCAD secondary oracle)

    Implementation notes:
        - No hidden nearest-node rounding or extrapolation is permitted.
        - The interpolation is deterministic and exact-node compatible.
    """
    table = _ANNEX_D["tables"]["D3"]
    lambda_value = _real(relative_slenderness, "relative_slenderness")
    m_value = _real(effective_relative_eccentricity, "effective_relative_eccentricity")
    lambda_nodes = [float(x) for x in table["rows"].keys()]
    m_nodes = [float(x) for x in table["m_eff_nodes"]]
    l0, l1 = _axis_bracket(lambda_value, lambda_nodes, "relative_slenderness")
    m0, m1 = _axis_bracket(m_value, m_nodes, "effective_relative_eccentricity")

    divisor = float(table["scale_divisor"])
    def cell(lam: float, meff: float) -> float:
        return float(table["rows"][str(float(lam))][str(float(meff))]) / divisor

    if l0 == l1 and m0 == m1:
        return cell(l0, m0)
    if l0 == l1:
        v0, v1 = cell(l0, m0), cell(l0, m1)
        t = (m_value - m0) / (m1 - m0)
        return v0 + t * (v1 - v0)
    if m0 == m1:
        v0, v1 = cell(l0, m0), cell(l1, m0)
        t = (lambda_value - l0) / (l1 - l0)
        return v0 + t * (v1 - v0)

    q00, q01 = cell(l0, m0), cell(l0, m1)
    q10, q11 = cell(l1, m0), cell(l1, m1)
    tx = (lambda_value - l0) / (l1 - l0)
    ty = (m_value - m0) / (m1 - m0)
    return (
        (1.0 - tx) * (1.0 - ty) * q00
        + (1.0 - tx) * ty * q01
        + tx * (1.0 - ty) * q10
        + tx * ty * q11
    )

def beam_column_in_plane_utilization_eq109(
    axial_force_n: float,
    stability_coefficient_phi_e: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate in-plane stability utilization of an eccentrically compressed solid member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.2
        Annex: D
        Equation/Table: Equation (109), Table D.3
        Audit ID: SP16-EQ-109
        Normative status: normative

    Mathematical form:
        eta_109 = N/(phi_e*A*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Design compressive axial force N.
            Valid range: >= 0
            Source: same load combination as the design moment under 9.2.3
        stability_coefficient_phi_e:
            Type: float
            Unit: dimensionless
            Meaning: Eccentric-compression stability coefficient phi_e.
            Valid range: (0, 1]
            Source: Table D.3 with the central-compression cap
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross section area A or audited reduced area where required by linked clauses.
            Valid range: > 0
            Source: section model
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
        Meaning: Utilization ratio; values not greater than one satisfy equation (109).

    Assumptions:
        - Force, area, resistance, and coefficient correspond to the same member and load combination.
        - Local-stability reductions are supplied explicitly when applicable.

    Sign convention:
        - Compression is supplied as a non-negative magnitude.

    Unit convention:
        - N and mm are used consistently without implicit conversion.

    Applicability:
        - Constant-section solid beam-columns in the symmetry plane of bending.

    Limitations:
        - This scalar function does not select Table D.3 inputs or perform global analysis.

    Raises:
        ValueError: A denominator input is non-positive or axial force is negative.
        TypeError: An input is not real.

    Examples:
        >>> beam_column_in_plane_utilization_eq109(200000.0, 0.8, 3000.0, 250.0, 1.0)
        0.3333333333333333

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equation_109_normal_zero_and_units
        Validation cases:
            - BC-EQ-109

    Implementation notes:
        - No resistance or stability coefficient is inferred silently.
        - Defaults must be explicit in the input configuration.
    """
    force = _nonnegative(axial_force_n, "axial_force_n")
    phi = _ratio_0_1(stability_coefficient_phi_e, "stability_coefficient_phi_e")
    return force / (
        phi
        * _positive(gross_area_mm2, "gross_area_mm2")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def effective_relative_eccentricity_eq110(shape_influence_coefficient_eta: float, relative_eccentricity_m: float) -> float:
    """
    Summary:
        Calculate the effective relative eccentricity used for Table D.3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.2
        Annex: D
        Equation/Table: Equation (110), Table D.2
        Audit ID: SP16-EQ-110
        Normative status: normative

    Mathematical form:
        m_eff = eta*m.

    Parameters:
        shape_influence_coefficient_eta:
            Type: float
            Unit: dimensionless
            Meaning: Section-shape influence coefficient eta.
            Valid range: > 0
            Source: Table D.2
        relative_eccentricity_m:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m=e*A/W_c=M*A/(N*W_c).
            Valid range: >= 0
            Source: member force and section properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective relative eccentricity m_eff.

    Assumptions:
        - Eta and m correspond to the same bending plane and section orientation.

    Sign convention:
        - The Table D.3 route uses a non-negative relative eccentricity magnitude.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - In-plane eccentric-compression stability under clause 9.2.2.

    Limitations:
        - Values above 20 require routing to bending-member design under Section 8.

    Raises:
        ValueError: Eta is non-positive or m is negative.
        TypeError: An input is not real.

    Examples:
        >>> effective_relative_eccentricity_eq110(1.2, 2.0)
        2.4

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equation_110_and_bending_route
        Validation cases:
            - BC-EQ-110

    Implementation notes:
        - The function does not round to a Table D.3 node.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(shape_influence_coefficient_eta, "shape_influence_coefficient_eta") * _nonnegative(
        relative_eccentricity_m, "relative_eccentricity_m"
    )


def beam_column_out_of_plane_utilization_eq111(
    axial_force_n: float,
    out_of_plane_coefficient_c: float,
    central_compression_phi_y: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate out-of-plane flexural-torsional stability utilization of a beam-column.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.4
        Annex: D and Ж
        Equation/Table: Equation (111)
        Audit ID: SP16-EQ-111
        Normative status: normative

    Mathematical form:
        eta_111 = N/(c*phi_y*A*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Design compressive axial force N.
            Valid range: >= 0
            Source: structural analysis
        out_of_plane_coefficient_c:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c from 9.2.5 including the c_max and 0.3 limits.
            Valid range: [0.3, 1]
            Source: equations (112)-(114) and Annex D
        central_compression_phi_y:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient phi_y.
            Valid range: (0, 1]
            Source: clause 7.1.3
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross or explicitly reduced area A.
            Valid range: > 0
            Source: section model
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
        Meaning: Utilization ratio under equation (111).

    Assumptions:
        - The member is within the scope of 9.2.4 or 9.2.7.

    Sign convention:
        - Compression is supplied as a non-negative magnitude.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Solid constant-section members other than box sections, bent in the major-stiffness symmetry plane, and channels.

    Limitations:
        - Section classification and moment selection remain explicit inputs.

    Raises:
        ValueError: A denominator input is invalid or c is outside [0.3, 1].
        TypeError: An input is not real.

    Examples:
        >>> beam_column_out_of_plane_utilization_eq111(150000.0, 0.8, 0.9, 3000.0, 250.0, 1.0)
        0.2777777777777778

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equation_111_normal_zero_and_c_range
        Validation cases:
            - BC-EQ-111

    Implementation notes:
        - The lower bound c>=0.3 is enforced as printed in 9.2.5.
        - Defaults must be explicit in the input configuration.
    """
    c = _real(out_of_plane_coefficient_c, "out_of_plane_coefficient_c")
    if c < 0.3 or c > 1.0:
        raise ValueError("out_of_plane_coefficient_c must be in [0.3, 1]")
    return _nonnegative(axial_force_n, "axial_force_n") / (
        c
        * _ratio_0_1(central_compression_phi_y, "central_compression_phi_y")
        * _positive(gross_area_mm2, "gross_area_mm2")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def out_of_plane_coefficient_c_eq112(alpha: float, beta: float, relative_eccentricity_mx: float) -> float:
    """
    Summary:
        Calculate coefficient c for relative eccentricity m_x not greater than five.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: None
        Equation/Table: Equation (112), Table 21
        Audit ID: SP16-EQ-112
        Normative status: normative

    Mathematical form:
        c = beta/(1+alpha*m_x), limited to not more than 1.

    Parameters:
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Table 21 coefficient alpha.
            Valid range: >= 0
            Source: Table 21
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Table 21 coefficient beta.
            Valid range: > 0
            Source: Table 21
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: 0 <= m_x <= 5
            Source: clause 9.2.5

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Uncapped-by-c_max coefficient c, already limited to not more than one.

    Assumptions:
        - Alpha and beta correspond to the same Table 21 section type.

    Sign convention:
        - m_x is a non-negative magnitude.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - Equation (112) branch only.

    Limitations:
        - The Annex D c_max cap and minimum c=0.3 are applied by the router function.

    Raises:
        ValueError: Inputs are outside the stated domain.
        TypeError: An input is not real.

    Examples:
        >>> out_of_plane_coefficient_c_eq112(0.7, 1.0, 1.0)
        0.5882352941176471

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_112_to_114_and_router
        Validation cases:
            - BC-EQ-112

    Implementation notes:
        - The printed upper limit c<=1 is applied directly.
        - Defaults must be explicit in the input configuration.
    """
    a = _nonnegative(alpha, "alpha")
    b = _positive(beta, "beta")
    mx = _nonnegative(relative_eccentricity_mx, "relative_eccentricity_mx")
    if mx > 5.0:
        raise ValueError("equation (112) requires relative_eccentricity_mx <= 5")
    return min(1.0, b / (1.0 + a * mx))


def out_of_plane_coefficient_c_eq113(relative_eccentricity_mx: float, central_phi_y: float, bending_phi_b: float) -> float:
    """
    Summary:
        Calculate coefficient c for relative eccentricity m_x not less than ten.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: Ж
        Equation/Table: Equation (113)
        Audit ID: SP16-EQ-113
        Normative status: normative

    Mathematical form:
        c = 1/(1+m_x*phi_y/phi_b).

    Parameters:
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: >= 10
            Source: clause 9.2.5
        central_phi_y:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient phi_y.
            Valid range: (0, 1]
            Source: clause 7.1.3
        bending_phi_b:
            Type: float
            Unit: dimensionless
            Meaning: Bending stability coefficient phi_b for a beam with at least two compression-flange restraints.
            Valid range: > 0
            Source: clause 8.4.1 and Annex Ж

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Coefficient c before the Annex D c_max and minimum limits.

    Assumptions:
        - Phi_b has been evaluated for the required restraint arrangement.

    Sign convention:
        - m_x is non-negative.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - Equation (113) branch only.

    Limitations:
        - This function does not calculate phi_b.

    Raises:
        ValueError: The branch domain or coefficient domain is violated.
        TypeError: An input is not real.

    Examples:
        >>> out_of_plane_coefficient_c_eq113(10.0, 0.8, 0.9)
        0.10112359550561797

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_112_to_114_and_router
        Validation cases:
            - BC-EQ-113

    Implementation notes:
        - No phi_b model is substituted silently.
        - Defaults must be explicit in the input configuration.
    """
    mx = _nonnegative(relative_eccentricity_mx, "relative_eccentricity_mx")
    if mx < 10.0:
        raise ValueError("equation (113) requires relative_eccentricity_mx >= 10")
    return 1.0 / (
        1.0
        + mx
        * _ratio_0_1(central_phi_y, "central_phi_y")
        / _positive(bending_phi_b, "bending_phi_b")
    )


def out_of_plane_coefficient_c_eq114(relative_eccentricity_mx: float, c_at_5: float, c_at_10: float) -> float:
    """
    Summary:
        Interpolate coefficient c between the equation (112) value at m_x=5 and equation (113) value at m_x=10.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: None
        Equation/Table: Equation (114)
        Audit ID: SP16-EQ-114
        Normative status: normative

    Mathematical form:
        c = c_5*(2-0.2*m_x)+c_10*(0.2*m_x-1).

    Parameters:
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: 5 < m_x < 10
            Source: clause 9.2.5
        c_at_5:
            Type: float
            Unit: dimensionless
            Meaning: Equation (112) value evaluated at m_x=5.
            Valid range: > 0
            Source: equation (112)
        c_at_10:
            Type: float
            Unit: dimensionless
            Meaning: Equation (113) value evaluated at m_x=10.
            Valid range: > 0
            Source: equation (113)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Interpolated coefficient c.

    Assumptions:
        - c_at_5 and c_at_10 use the same member properties.

    Sign convention:
        - m_x is a non-negative magnitude.

    Unit convention:
        - All quantities are dimensionless.

    Applicability:
        - Intermediate branch of clause 9.2.5.

    Limitations:
        - Annex D and minimum limits are applied separately.

    Raises:
        ValueError: m_x is outside the open interval (5, 10) or a coefficient is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> out_of_plane_coefficient_c_eq114(7.5, 0.4, 0.2)
        0.30000000000000004

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_112_to_114_and_router
        Validation cases:
            - BC-EQ-114

    Implementation notes:
        - This is the explicit interpolation printed in equation (114), not an inferred table interpolation.
        - Defaults must be explicit in the input configuration.
    """
    mx = _real(relative_eccentricity_mx, "relative_eccentricity_mx")
    if not 5.0 < mx < 10.0:
        raise ValueError("equation (114) requires 5 < relative_eccentricity_mx < 10")
    c5 = _positive(c_at_5, "c_at_5")
    c10 = _positive(c_at_10, "c_at_10")
    return c5 * (2.0 - 0.2 * mx) + c10 * (0.2 * mx - 1.0)


def central_compression_out_of_plane_utilization_eq115(
    axial_force_n: float,
    central_compression_phi_x: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the additional central-compression stability check outside the minor-axis bending plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.8
        Annex: None
        Equation/Table: Equation (115)
        Audit ID: SP16-EQ-115
        Normative status: normative

    Mathematical form:
        eta_115 = N/(phi_x*A*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Design compressive axial force N.
            Valid range: >= 0
            Source: structural analysis
        central_compression_phi_x:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient phi_x.
            Valid range: (0, 1]
            Source: clause 7.1.3
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross or explicitly reduced section area A.
            Valid range: > 0
            Source: section model
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
        Meaning: Utilization ratio under equation (115).

    Assumptions:
        - The route condition lambda_x>lambda_y has been evaluated separately.

    Sign convention:
        - Compression is a non-negative magnitude.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Members bent in the minor-stiffness plane under clause 9.2.8.

    Limitations:
        - The route condition is not inferred from section geometry.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> central_compression_out_of_plane_utilization_eq115(100000.0, 0.8, 2500.0, 250.0, 1.0)
        0.2

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equation_115_and_clause_9_2_8_route
        Validation cases:
            - BC-EQ-115

    Implementation notes:
        - The equation is algebraically the central-compression check with phi_x.
        - Defaults must be explicit in the input configuration.
    """
    return beam_column_in_plane_utilization_eq109(
        axial_force_n,
        central_compression_phi_x,
        gross_area_mm2,
        design_yield_resistance_n_mm2,
        working_condition_factor,
    )


def biaxial_beam_column_utilization_eq116(
    axial_force_n: float,
    biaxial_stability_coefficient_phi_exy: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate stability utilization for a solid member compressed and bent in both principal planes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: D
        Equation/Table: Equation (116)
        Audit ID: SP16-EQ-116
        Normative status: normative

    Mathematical form:
        eta_116 = N/(phi_exy*A*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Design compressive axial force.
            Valid range: >= 0
            Source: structural analysis
        biaxial_stability_coefficient_phi_exy:
            Type: float
            Unit: dimensionless
            Meaning: Combined stability coefficient phi_exy from equation (117).
            Valid range: (0, 1]
            Source: equation (117)
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross or explicitly reduced section area.
            Valid range: > 0
            Source: section model
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor.
            Valid range: > 0
            Source: applicable standard provision

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization ratio under equation (116).

    Assumptions:
        - The section is not box-shaped and meets the symmetry conditions of 9.2.9 or is Table 21 type 3.

    Sign convention:
        - Compression is non-negative.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Biaxially bent solid beam-columns under clause 9.2.9.

    Limitations:
        - Additional checks required by 9.2.9 are returned by a separate route function.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> biaxial_beam_column_utilization_eq116(120000.0, 0.6, 3000.0, 250.0, 1.0)
        0.26666666666666666

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-EQ-116

    Implementation notes:
        - No section-type classification is inferred.
        - Defaults must be explicit in the input configuration.
    """
    return beam_column_in_plane_utilization_eq109(
        axial_force_n,
        biaxial_stability_coefficient_phi_exy,
        gross_area_mm2,
        design_yield_resistance_n_mm2,
        working_condition_factor,
    )


def biaxial_stability_coefficient_eq117(in_plane_phi_ey: float, out_of_plane_coefficient_c: float) -> float:
    """
    Summary:
        Calculate the combined biaxial stability coefficient phi_exy.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: None
        Equation/Table: Equation (117)
        Audit ID: SP16-EQ-117
        Normative status: normative

    Mathematical form:
        phi_exy = phi_ey*(0.6*c^(1/3)+0.4*c^(1/4)).

    Parameters:
        in_plane_phi_ey:
            Type: float
            Unit: dimensionless
            Meaning: In-plane eccentric-compression stability coefficient phi_ey.
            Valid range: (0, 1]
            Source: clause 9.2.2 using m_y and lambda_bar_y
        out_of_plane_coefficient_c:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c from clause 9.2.5.
            Valid range: [0.3, 1]
            Source: equations (112)-(114) with limits

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Combined stability coefficient phi_exy.

    Assumptions:
        - Both coefficients refer to the same member and load combination.

    Sign convention:
        - Coefficients are positive scalars.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (117) under clause 9.2.9.

    Limitations:
        - The equation does not apply to box sections.

    Raises:
        ValueError: A coefficient is outside its stated range.
        TypeError: An input is not real.

    Examples:
        >>> round(biaxial_stability_coefficient_eq117(0.7, 0.5), 6)
        0.580149

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-EQ-117

    Implementation notes:
        - Real positive roots are evaluated directly.
        - Defaults must be explicit in the input configuration.
    """
    phi = _ratio_0_1(in_plane_phi_ey, "in_plane_phi_ey")
    c = _real(out_of_plane_coefficient_c, "out_of_plane_coefficient_c")
    if c < 0.3 or c > 1.0:
        raise ValueError("out_of_plane_coefficient_c must be in [0.3, 1]")
    return phi * (0.6 * c ** (1.0 / 3.0) + 0.4 * c ** 0.25)


def relative_eccentricity_x_eq118(eccentricity_x_mm: float, gross_area_mm2: float, compressed_section_modulus_x_mm3: float) -> float:
    """
    Summary:
        Calculate relative eccentricity m_x for the most compressed fiber about x-x.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: None
        Equation/Table: Equation (118)
        Audit ID: SP16-EQ-118
        Normative status: normative

    Mathematical form:
        m_x = e_x*A/W_cx.

    Parameters:
        eccentricity_x_mm:
            Type: float
            Unit: mm
            Meaning: Eccentricity e_x=M_x/N.
            Valid range: >= 0 for the magnitude-based stability route
            Source: structural analysis
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
        compressed_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: Section modulus W_cx for the most compressed fiber.
            Valid range: > 0
            Source: section model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative eccentricity m_x.

    Assumptions:
        - The compressed fiber is identified consistently with the moment sign.

    Sign convention:
        - A non-negative eccentricity magnitude is used.

    Unit convention:
        - mm, mm2, and mm3 cancel to a dimensionless ratio.

    Applicability:
        - Clause 9.2.9 and the m_x definition in 9.2.5.

    Limitations:
        - The 25% increase for a noncoincident symmetry plane is separate.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> relative_eccentricity_x_eq118(20.0, 3000.0, 600000.0)
        0.1

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-EQ-118

    Implementation notes:
        - The equation is implemented with readable unit-explicit inputs.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(eccentricity_x_mm, "eccentricity_x_mm") * _positive(gross_area_mm2, "gross_area_mm2") / _positive(
        compressed_section_modulus_x_mm3, "compressed_section_modulus_x_mm3"
    )


def relative_eccentricity_y_eq119(eccentricity_y_mm: float, gross_area_mm2: float, compressed_section_modulus_y_mm3: float) -> float:
    """
    Summary:
        Calculate relative eccentricity m_y for the most compressed fiber about y-y.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: None
        Equation/Table: Equation (119)
        Audit ID: SP16-EQ-119
        Normative status: normative

    Mathematical form:
        m_y = e_y*A/W_cy.

    Parameters:
        eccentricity_y_mm:
            Type: float
            Unit: mm
            Meaning: Eccentricity e_y=M_y/N.
            Valid range: >= 0 for the magnitude-based stability route
            Source: structural analysis
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
        compressed_section_modulus_y_mm3:
            Type: float
            Unit: mm3
            Meaning: Section modulus W_cy for the most compressed fiber.
            Valid range: > 0
            Source: section model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative eccentricity m_y.

    Assumptions:
        - The compressed fiber is identified consistently with the moment sign.

    Sign convention:
        - A non-negative eccentricity magnitude is used.

    Unit convention:
        - mm, mm2, and mm3 cancel to a dimensionless ratio.

    Applicability:
        - Clause 9.2.9.

    Limitations:
        - Section-shape coefficient eta remains a separate Table D.2 input.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> relative_eccentricity_y_eq119(10.0, 3000.0, 300000.0)
        0.1

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-EQ-119

    Implementation notes:
        - The equation is kept separate from equation (118) for traceability.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(eccentricity_y_mm, "eccentricity_y_mm") * _positive(gross_area_mm2, "gross_area_mm2") / _positive(
        compressed_section_modulus_y_mm3, "compressed_section_modulus_y_mm3"
    )


def box_major_axis_utilization_eq120(
    axial_force_n: float,
    stability_phi_ex: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    major_axis_moment_n_mm: float,
    plastic_coefficient_cx: float,
    delta_x: float,
    minimum_section_modulus_x_mm3: float,
) -> float:
    """
    Summary:
        Calculate the major-axis box-section beam-column utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.10
        Annex: D and E
        Equation/Table: Equation (120)
        Audit ID: SP16-EQ-120
        Normative status: normative

    Mathematical form:
        eta_120=N/(phi_ex*A*R_y*gamma_c)+M_x/(c_x*delta_x*W_x,min*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Positive compressive axial force N.
            Valid range: >= 0
            Source: structural analysis
        stability_phi_ex:
            Type: float
            Unit: dimensionless
            Meaning: In-plane eccentric-compression coefficient phi_ex, or phi_ey for the printed major-axis substitution.
            Valid range: (0, 1]
            Source: Table D.3 and clause 9.2.10 routing
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
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
        major_axis_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Absolute major-axis bending moment M_x.
            Valid range: >= 0
            Source: structural analysis
        plastic_coefficient_cx:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c_x from Table E.1.
            Valid range: > 0
            Source: Table E.1
        delta_x:
            Type: float
            Unit: dimensionless
            Meaning: Reduction coefficient delta_x from equation (122).
            Valid range: > 0
            Source: equation (122)
        minimum_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: Minimum section modulus W_x,min.
            Valid range: > 0
            Source: section model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization under equation (120).

    Assumptions:
        - The box section is constant along the member.

    Sign convention:
        - Compression and bending moment are supplied as non-negative magnitudes.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Box-section beam-columns under clause 9.2.10.

    Limitations:
        - The phi_ex to phi_ey substitution is selected externally by the route helper.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> round(box_major_axis_utilization_eq120(100000,0.8,3000,250,1,10000000,1.1,0.95,600000),6)
        0.238596

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_120_to_122_and_major_axis_substitution
        Validation cases:
            - BC-EQ-120

    Implementation notes:
        - No sign cancellation is permitted in the interaction sum.
        - Defaults must be explicit in the input configuration.
    """
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    gc = _positive(working_condition_factor, "working_condition_factor")
    return _nonnegative(axial_force_n, "axial_force_n") / (
        _ratio_0_1(stability_phi_ex, "stability_phi_ex") * _positive(gross_area_mm2, "gross_area_mm2") * ry * gc
    ) + _nonnegative(major_axis_moment_n_mm, "major_axis_moment_n_mm") / (
        _positive(plastic_coefficient_cx, "plastic_coefficient_cx")
        * _positive(delta_x, "delta_x")
        * _positive(minimum_section_modulus_x_mm3, "minimum_section_modulus_x_mm3")
        * ry
        * gc
    )


def box_minor_axis_utilization_eq121(
    axial_force_n: float,
    stability_phi_ey: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    minor_axis_moment_n_mm: float,
    plastic_coefficient_cy: float,
    delta_y: float,
    minimum_section_modulus_y_mm3: float,
) -> float:
    """
    Summary:
        Calculate the minor-axis box-section beam-column utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.10
        Annex: D and E
        Equation/Table: Equation (121)
        Audit ID: SP16-EQ-121
        Normative status: normative

    Mathematical form:
        eta_121=N/(phi_ey*A*R_y*gamma_c)+M_y/(c_y*delta_y*W_y,min*R_y*gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Positive compressive axial force N.
            Valid range: >= 0
            Source: structural analysis
        stability_phi_ey:
            Type: float
            Unit: dimensionless
            Meaning: Minor-axis eccentric-compression stability coefficient phi_ey.
            Valid range: (0, 1]
            Source: Table D.3
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
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
        minor_axis_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Absolute minor-axis bending moment M_y.
            Valid range: >= 0
            Source: structural analysis
        plastic_coefficient_cy:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient c_y from Table E.1.
            Valid range: > 0
            Source: Table E.1
        delta_y:
            Type: float
            Unit: dimensionless
            Meaning: Reduction coefficient delta_y from equation (122).
            Valid range: > 0
            Source: equation (122)
        minimum_section_modulus_y_mm3:
            Type: float
            Unit: mm3
            Meaning: Minimum section modulus W_y,min.
            Valid range: > 0
            Source: section model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Utilization under equation (121).

    Assumptions:
        - The box section is constant along the member.

    Sign convention:
        - Compression and bending moment are non-negative magnitudes.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Box-section beam-columns under clause 9.2.10.

    Limitations:
        - The function does not derive Table E.1 coefficients.

    Raises:
        ValueError: An input is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> round(box_minor_axis_utilization_eq121(100000,0.75,3000,250,1,5000000,1.2,0.96,300000),6)
        0.237037

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_120_to_122_and_major_axis_substitution
        Validation cases:
            - BC-EQ-121

    Implementation notes:
        - The interaction terms are added as printed.
        - Defaults must be explicit in the input configuration.
    """
    return box_major_axis_utilization_eq120(
        axial_force_n,
        stability_phi_ey,
        gross_area_mm2,
        design_yield_resistance_n_mm2,
        working_condition_factor,
        minor_axis_moment_n_mm,
        plastic_coefficient_cy,
        delta_y,
        minimum_section_modulus_y_mm3,
    )


def box_delta_eq122(
    axial_force_n: float,
    relative_slenderness: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the box-section reduction coefficient delta_x or delta_y.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.10
        Annex: None
        Equation/Table: Equation (122)
        Audit ID: SP16-EQ-122
        Normative status: normative

    Mathematical form:
        delta=1 for lambda_bar<=1; otherwise delta=1-0.1*N*lambda_bar^2/(A*R_y).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Positive compressive force N.
            Valid range: >= 0
            Source: structural analysis
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_x or lambda_bar_y.
            Valid range: >= 0
            Source: clause 7.1.3 definitions
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Positive reduction coefficient delta.

    Assumptions:
        - N is taken with the positive compression sign as required by the clause.

    Sign convention:
        - Compression is positive.

    Unit convention:
        - N, mm2, and N/mm2 form a dimensionless ratio.

    Applicability:
        - Equations (120) and (121) for box-section beam-columns.

    Limitations:
        - A non-positive calculated delta is rejected rather than clipped.

    Raises:
        ValueError: An input is outside its domain or the calculated delta is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> box_delta_eq122(100000.0, 1.0, 3000.0, 250.0)
        1.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_120_to_122_and_major_axis_substitution
        Validation cases:
            - BC-EQ-122

    Implementation notes:
        - The exact lambda_bar<=1 override is applied before equation evaluation.
        - Defaults must be explicit in the input configuration.
    """
    force = _nonnegative(axial_force_n, "axial_force_n")
    slenderness = _nonnegative(relative_slenderness, "relative_slenderness")
    if slenderness <= 1.0:
        return 1.0
    delta = 1.0 - 0.1 * force * slenderness * slenderness / (
        _positive(gross_area_mm2, "gross_area_mm2")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    )
    if delta <= 0.0:
        raise ValueError("equation (122) produced a non-positive delta")
    return delta


def table_20_design_moment(
    maximum_moment_n_mm: float,
    middle_third_moment_n_mm: float,
    auxiliary_moment_m2_n_mm: float,
    relative_eccentricity_m_max: float,
    relative_slenderness: float,
) -> float:
    """
    Summary:
        Select the design moment M for the pinned-ended one-symmetry-axis member case in Table 20.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.3
        Annex: None
        Equation/Table: Table 20
        Audit ID: SP16-TBL-20
        Normative status: normative

    Mathematical form:
        Piecewise Table 20 expressions for m_max<=3 and 3<m_max<=20 at lambda_bar<4 or >=4.

    Parameters:
        maximum_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Largest moment M_max along the member.
            Valid range: >= 0
            Source: elastic first-order analysis
        middle_third_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Largest moment M_1 in the middle third, not less than 0.5*M_max.
            Valid range: 0.5*M_max <= M_1 <= M_max
            Source: elastic first-order analysis
        auxiliary_moment_m2_n_mm:
            Type: float
            Unit: N*mm
            Meaning: M_2 defined by Table 20 for the low-m_max, low-slenderness branch and not less than 0.5*M_max.
            Valid range: 0.5*M_max <= M_2 <= M_max
            Source: Table 20 construction
        relative_eccentricity_m_max:
            Type: float
            Unit: dimensionless
            Meaning: m_max=M_max*A/(N*W_c).
            Valid range: 0 <= m_max <= 20
            Source: member force and section properties
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness lambda_bar.
            Valid range: >= 0
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Design moment M selected by Table 20.

    Assumptions:
        - The member has pinned ends and one symmetry axis coinciding with the bending plane.
        - Input moments are absolute magnitudes from the same load combination.

    Sign convention:
        - Moment magnitudes are non-negative.

    Unit convention:
        - All moment inputs and output use N*mm.

    Applicability:
        - The specific member case stated in 9.2.3.

    Limitations:
        - m_max>20 is outside the table and routes to Section 8.

    Raises:
        ValueError: A domain or Table 20 ordering rule is violated.
        TypeError: An input is not real.

    Examples:
        >>> table_20_design_moment(100.0, 60.0, 70.0, 2.0, 2.0)
        80.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_table_20_all_branches_and_boundaries
        Validation cases:
            - BC-TBL-20-*

    Implementation notes:
        - The auxiliary M_2 is explicit because Table 20 defines it through a prior M result.
        - Defaults must be explicit in the input configuration.
    """
    mmax = _nonnegative(maximum_moment_n_mm, "maximum_moment_n_mm")
    m1 = _nonnegative(middle_third_moment_n_mm, "middle_third_moment_n_mm")
    m2 = _nonnegative(auxiliary_moment_m2_n_mm, "auxiliary_moment_m2_n_mm")
    rel_e = _nonnegative(relative_eccentricity_m_max, "relative_eccentricity_m_max")
    lam = _nonnegative(relative_slenderness, "relative_slenderness")
    if rel_e > 20.0:
        raise ValueError("Table 20 is limited to relative_eccentricity_m_max <= 20")
    if m1 + 1e-12 < 0.5 * mmax or m1 > mmax + 1e-12:
        raise ValueError("middle_third_moment_n_mm must be between 0.5*M_max and M_max")
    if m2 + 1e-12 < 0.5 * mmax or m2 > mmax + 1e-12:
        raise ValueError("auxiliary_moment_m2_n_mm must be between 0.5*M_max and M_max")
    if rel_e <= 3.0:
        return mmax - 0.25 * lam * (mmax - m1) if lam < 4.0 else m1
    if lam < 4.0:
        return m2 + (rel_e - 3.0) * (mmax - m2) / 17.0
    return m1 + (rel_e - 3.0) * (mmax - m1) / 17.0


def table_21_alpha(section_type: str, relative_eccentricity_mx: float, smaller_to_larger_flange_inertia_ratio: float | None) -> float:
    """
    Summary:
        Evaluate coefficient alpha from Table 21.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: None
        Equation/Table: Table 21
        Audit ID: SP16-TBL-21
        Normative status: normative

    Mathematical form:
        Types 1-3: 0.7 or 0.65+0.05*m_x; type 4 uses I_2/I_1 modifiers.

    Parameters:
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Diagram type 1, 2, 3, or 4 from Table 21.
            Valid range: one of '1', '2', '3', '4'
            Source: engineer classification from the diagram
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: 0 <= m_x <= 5
            Source: clause 9.2.5
        smaller_to_larger_flange_inertia_ratio:
            Type: float or None
            Unit: dimensionless
            Meaning: I_2/I_1 for type 4; unused for types 1-3.
            Valid range: (0, 1] for type 4
            Source: flange section properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 21 coefficient alpha.

    Assumptions:
        - Section type is selected from the printed diagrams.

    Sign convention:
        - m_x is non-negative.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (112) branch under clause 9.2.5.

    Limitations:
        - The function does not classify arbitrary geometry.

    Raises:
        ValueError: Type or input domain is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> table_21_alpha('1', 2.0, None)
        0.75

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_table_21_alpha_beta_all_types
        Validation cases:
            - BC-TBL-21-ALPHA-*

    Implementation notes:
        - The two printed m_x ranges are implemented exactly.
        - Defaults must be explicit in the input configuration.
    """
    if section_type not in {"1", "2", "3", "4"}:
        raise ValueError("section_type must be one of '1', '2', '3', '4'")
    mx = _nonnegative(relative_eccentricity_mx, "relative_eccentricity_mx")
    if mx > 5.0:
        raise ValueError("Table 21 alpha requires relative_eccentricity_mx <= 5")
    if section_type in {"1", "2", "3"}:
        return 0.7 if mx <= 1.0 else 0.65 + 0.05 * mx
    if smaller_to_larger_flange_inertia_ratio is None:
        raise ValueError("type 4 requires smaller_to_larger_flange_inertia_ratio")
    ratio = _ratio_0_1(smaller_to_larger_flange_inertia_ratio, "smaller_to_larger_flange_inertia_ratio")
    return 1.0 - 0.3 * ratio if mx <= 1.0 else 1.0 - (0.35 - 0.05 * mx) * ratio


def table_21_beta(
    section_type: str,
    relative_slenderness_y: float,
    central_phi_y: float,
    central_phi_at_3_14: float,
    smaller_to_larger_flange_inertia_ratio: float | None,
) -> float:
    """
    Summary:
        Evaluate coefficient beta from Table 21.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: None
        Equation/Table: Table 21
        Audit ID: SP16-TBL-21
        Normative status: normative

    Mathematical form:
        beta=1 for lambda_bar_y<=3.14; otherwise uses sqrt(phi_c/phi_y), with a type-4 flange-inertia modifier.

    Parameters:
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Diagram type 1-4 from Table 21.
            Valid range: one of '1', '2', '3', '4'
            Source: engineer classification
        relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_y.
            Valid range: >= 0
            Source: clause 7.1.3
        central_phi_y:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression phi_y at the actual lambda_bar_y.
            Valid range: (0, 1]
            Source: clause 7.1.3
        central_phi_at_3_14:
            Type: float
            Unit: dimensionless
            Meaning: phi_c, equal to phi_y evaluated at lambda_bar_y=3.14.
            Valid range: (0, 1]
            Source: Table 21 note
        smaller_to_larger_flange_inertia_ratio:
            Type: float or None
            Unit: dimensionless
            Meaning: I_2/I_1 for type 4.
            Valid range: (0, 1] for type 4
            Source: flange properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 21 coefficient beta.

    Assumptions:
        - Phi values use the same central-compression buckling curve.

    Sign convention:
        - Coefficients and slenderness are non-negative.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (112) under clause 9.2.5.

    Limitations:
        - The function does not calculate central-compression phi values.

    Raises:
        ValueError: A domain condition is violated.
        TypeError: An input type is invalid.

    Examples:
        >>> table_21_beta('1', 3.0, 0.8, 0.7, None)
        1.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_table_21_alpha_beta_all_types
        Validation cases:
            - BC-TBL-21-BETA-*

    Implementation notes:
        - The printed I_2/I_1<0.5 override for type 4 is applied.
        - Defaults must be explicit in the input configuration.
    """
    if section_type not in {"1", "2", "3", "4"}:
        raise ValueError("section_type must be one of '1', '2', '3', '4'")
    lam = _nonnegative(relative_slenderness_y, "relative_slenderness_y")
    phi_y = _ratio_0_1(central_phi_y, "central_phi_y")
    phi_c = _ratio_0_1(central_phi_at_3_14, "central_phi_at_3_14")
    if lam <= 3.14:
        return 1.0
    root = math.sqrt(phi_c / phi_y)
    if section_type in {"1", "2", "3"}:
        return root
    if smaller_to_larger_flange_inertia_ratio is None:
        raise ValueError("type 4 requires smaller_to_larger_flange_inertia_ratio")
    ratio = _ratio_0_1(smaller_to_larger_flange_inertia_ratio, "smaller_to_larger_flange_inertia_ratio")
    if ratio < 0.5:
        return 1.0
    return 1.0 - (1.0 - root) * (2.0 * ratio - 1.0)


def annex_d2_shape_influence_coefficient(
    section_type: str,
    relative_slenderness: float,
    relative_eccentricity_m: float,
    flange_to_web_area_ratio: float | None,
    offset_ratio_a1_to_h: float | None,
) -> float:
    """
    Summary:
        Evaluate section-shape influence coefficient eta from Table D.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.2 and 9.2.9
        Annex: D
        Equation/Table: Table D.2
        Audit ID: SP16-TBL-Д-2
        Normative status: normative

    Mathematical form:
        Audited piecewise expressions by section type, lambda_bar, m, A_f/A_w, and a_1/h.

    Parameters:
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Table D.2 section type 1-11.
            Valid range: string '1' through '11'
            Source: engineer classification from diagrams
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar.
            Valid range: >= 0
            Source: clause 7.1.3
        relative_eccentricity_m:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m.
            Valid range: 0.1 <= m <= 20
            Source: equation definition in 9.2.2
        flange_to_web_area_ratio:
            Type: float or None
            Unit: dimensionless
            Meaning: A_f/A_w where required by Table D.2.
            Valid range: positive printed category or threshold
            Source: section properties and Table D.2 notes
        offset_ratio_a1_to_h:
            Type: float or None
            Unit: dimensionless
            Meaning: a_1/h for types 6 and 7.
            Valid range: 0 <= a_1/h <= 0.15
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Shape influence coefficient eta.

    Assumptions:
        - Section type and area convention follow the Table D.2 diagrams and notes.

    Sign convention:
        - m is a non-negative magnitude.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Effective eccentricity calculations for solid beam-columns.

    Limitations:
        - No interpolation is used between printed A_f/A_w categories.

    Raises:
        ValueError: The section type, branch, or required geometry input is invalid.
        TypeError: An input is not real or section_type is invalid.

    Examples:
        >>> annex_d2_shape_influence_coefficient('1', 2.0, 3.0, None, None)
        1.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d2_all_section_type_families
        Validation cases:
            - BC-D2-*

    Implementation notes:
        - Types 6 and 7 derive eta_5 exactly as stated in the Table D.2 note.
        - Defaults must be explicit in the input configuration.
    """
    if section_type not in {str(i) for i in range(1, 12)}:
        raise ValueError("section_type must be a string from '1' to '11'")
    lam = _nonnegative(relative_slenderness, "relative_slenderness")
    m = _real(relative_eccentricity_m, "relative_eccentricity_m")
    if not 0.1 <= m <= 20.0:
        raise ValueError("relative_eccentricity_m must be in [0.1, 20]")
    low_lam = lam <= 5.0
    low_m = m <= 5.0

    if section_type == "1":
        return 1.0
    if section_type == "2":
        return 0.85
    if section_type == "3":
        return 0.75 + 0.02 * lam if low_lam else 0.85
    if section_type == "4":
        return (1.35 - 0.05 * m) - 0.01 * (5.0 - m) * lam if low_lam and low_m else 1.1

    def ratio_required() -> float:
        if flange_to_web_area_ratio is None:
            raise ValueError(f"section type {section_type} requires flange_to_web_area_ratio")
        return _positive(flange_to_web_area_ratio, "flange_to_web_area_ratio")

    if section_type in {"5", "6", "7"}:
        ratio = ratio_required()
        if ratio <= 0.25 + 1e-12:
            base = (1.45 - 0.05 * m) - 0.01 * (5.0 - m) * lam if low_lam and low_m else 1.2
        elif math.isclose(ratio, 0.5, abs_tol=1e-12):
            base = (1.75 - 0.1 * m) - 0.02 * (5.0 - m) * lam if low_lam and low_m else 1.25
        elif ratio >= 1.0 - 1e-12:
            if low_lam and low_m:
                base = (1.90 - 0.1 * m) - 0.02 * (6.0 - m) * lam
            elif low_lam:
                base = 1.4 - 0.02 * lam
            else:
                base = 1.3
        else:
            raise ValueError("types 5-7 require A_f/A_w category 0.25, 0.5, or >=1.0")
        if section_type == "5":
            return base
        if offset_ratio_a1_to_h is None:
            raise ValueError(f"section type {section_type} requires offset_ratio_a1_to_h")
        offset = _nonnegative(offset_ratio_a1_to_h, "offset_ratio_a1_to_h")
        if offset > 0.15 + 1e-12:
            raise ValueError("offset_ratio_a1_to_h must not exceed 0.15")
        if section_type == "6":
            return base * (1.0 - 0.3 * (5.0 - m) * offset) if low_lam and low_m else base
        return base * (1.0 - 0.8 * offset)

    if section_type == "8":
        ratio = ratio_required()
        if low_lam and low_m:
            if ratio <= 0.25 + 1e-12:
                return (0.75 + 0.05 * m) + 0.01 * (5.0 - m) * lam
            if math.isclose(ratio, 0.5, abs_tol=1e-12):
                return (0.5 + 0.1 * m) + 0.02 * (5.0 - m) * lam
            if ratio >= 1.0 - 1e-12:
                return (0.25 + 0.15 * m) + 0.03 * (5.0 - m) * lam
            raise ValueError("type 8 requires A_f/A_w category 0.25, 0.5, or >=1.0")
        return 1.0

    if section_type == "9":
        ratio = ratio_required()
        if low_lam and low_m:
            if math.isclose(ratio, 0.5, abs_tol=1e-12):
                return (1.25 - 0.05 * m) - 0.01 * (5.0 - m) * lam
            if ratio >= 1.0 - 1e-12:
                return (1.5 - 0.1 * m) - 0.02 * (5.0 - m) * lam
            raise ValueError("type 9 requires A_f/A_w category 0.5 or >=1.0")
        return 1.0

    if section_type == "10":
        ratio = ratio_required()
        if math.isclose(ratio, 0.5, abs_tol=1e-12):
            return 1.4
        if math.isclose(ratio, 1.0, abs_tol=1e-12):
            if low_lam and low_m:
                return 1.6 - 0.01 * (5.0 - m) * lam
            if low_lam:
                return 1.6
            return 1.35 + 0.05 * m if low_m else 1.6
        if math.isclose(ratio, 2.0, abs_tol=1e-12):
            if low_lam and low_m:
                return 1.8 - 0.02 * (5.0 - m) * lam
            if low_lam:
                return 1.8
            return 1.3 + 0.1 * m if low_m else 1.8
        raise ValueError("type 10 requires A_f/A_w equal to 0.5, 1.0, or 2.0")

    ratio = ratio_required()
    if math.isclose(ratio, 0.5, abs_tol=1e-12):
        return 1.45 + 0.04 * m if low_m else 1.65
    if math.isclose(ratio, 1.0, abs_tol=1e-12):
        return 1.8 + 0.12 * m if low_m else 2.4
    if math.isclose(ratio, 1.5, abs_tol=1e-12):
        if not (low_lam and low_m):
            raise ValueError("type 11 A_f/A_w=1.5 is defined only for lambda_bar<=5 and m<=5")
        return 2.0 + 0.25 * m + 0.1 * lam
    if math.isclose(ratio, 2.0, abs_tol=1e-12):
        if not (low_lam and low_m):
            raise ValueError("type 11 A_f/A_w=2.0 is defined only for lambda_bar<=5 and m<=5")
        return 3.0 + 0.25 * m + 0.1 * lam
    raise ValueError("type 11 requires A_f/A_w equal to 0.5, 1.0, 1.5, or 2.0")


def annex_d3_table_coefficient(relative_slenderness: float, effective_relative_eccentricity: float) -> float:
    """
    Summary:
        Return the exact printed Table D.3 coefficient before the central-compression cap.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.2
        Annex: D
        Equation/Table: Table D.3
        Audit ID: SP16-TBL-Д-3
        Normative status: normative

    Mathematical form:
        Exact-node lookup; printed integer value divided by 1000.

    Parameters:
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar.
            Valid range: exact printed row node
            Source: Table D.3
        effective_relative_eccentricity:
            Type: float
            Unit: dimensionless
            Meaning: Effective relative eccentricity m_eff.
            Valid range: exact printed column node available in the selected row
            Source: equation (110)

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Raw printed Table D.3 coefficient phi_e.

    Assumptions:
        - The requested node exists in the printed table.

    Sign convention:
        - m_eff is non-negative.

    Unit convention:
        - Values are divided by 1000 according to the table note.

    Applicability:
        - Solid-member in-plane stability.

    Limitations:
        - No interpolation or extrapolation is performed.

    Raises:
        ValueError: The requested node is not printed.
        TypeError: An input is not real.

    Examples:
        >>> annex_d3_table_coefficient(1.0, 1.0)
        0.653

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_all_annex_d3_cells_match_json
        Validation cases:
            - BC-D3-*

    Implementation notes:
        - The central-compression cap is applied by annex_d3_stability_coefficient.
        - Defaults must be explicit in the input configuration.
    """
    return _doc_table_raw("D3", relative_slenderness, effective_relative_eccentricity)


def annex_d3_stability_coefficient(
    relative_slenderness: float,
    effective_relative_eccentricity: float,
    central_compression_phi: float,
) -> float:
    """
    Summary:
        Apply the Table D.3 in-domain interpolation and its requirement that phi_e not exceed central-compression phi.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.2
        Annex: D
        Equation/Table: Table D.3, note 2
        Audit ID: SP16-TBL-Д-3
        Normative status: normative

    Mathematical form:
        phi_e = min(Table D.3 value, phi).

    Parameters:
        relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness coordinate.
            Valid range: within the printed Table D.3 row domain
            Source: Table D.3
        effective_relative_eccentricity:
            Type: float
            Unit: dimensionless
            Meaning: Effective relative eccentricity coordinate.
            Valid range: within the printed Table D.3 column domain
            Source: equation (110)
        central_compression_phi:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient phi for the same slenderness and section type.
            Valid range: (0, 1]
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Normatively capped phi_e.

    Assumptions:
        - Central phi is evaluated for the same member plane.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (109).

    Limitations:
        - Interpolation is confined to the printed Table D.3 domain; extrapolation is forbidden.
        - The interpolation rule is a documented digital-table implementation policy, not an additional printed SP16 equation.

    Raises:
        ValueError: A coordinate lies outside the printed table domain or central phi is invalid.
        TypeError: An input is not real.

    Examples:
        >>> annex_d3_stability_coefficient(1.0, 1.0, 0.6)
        0.6

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d3_and_d4_central_phi_caps
        Validation cases:
            - BC-D3-CAP

    Implementation notes:
        - The raw table value remains separately available for audit comparison.
        - Defaults must be explicit in the input configuration.
    """
    return min(_annex_d3_interpolated_table_coefficient(relative_slenderness, effective_relative_eccentricity), _ratio_0_1(central_compression_phi, "central_compression_phi"))


def annex_d4_table_coefficient(relative_effective_slenderness: float, relative_eccentricity_m: float) -> float:
    """
    Summary:
        Return the exact printed Table D.4 coefficient for a built-up member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.2
        Annex: D
        Equation/Table: Table D.4
        Audit ID: SP16-TBL-Д-4
        Normative status: normative

    Mathematical form:
        Exact-node lookup; printed integer divided by 1000.

    Parameters:
        relative_effective_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Built-up-member relative effective slenderness lambda_bar_ef.
            Valid range: exact printed row node
            Source: Table D.4
        relative_eccentricity_m:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m.
            Valid range: exact printed column node available in the row
            Source: clause 9.3.2

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Raw Table D.4 coefficient phi_e.

    Assumptions:
        - The requested node is printed.

    Sign convention:
        - m is non-negative.

    Unit convention:
        - Table integers are divided by 1000.

    Applicability:
        - Section 9.3.2 built-up-member stability route in the plane of the free axis.

    Limitations:
        - No interpolation or extrapolation.

    Raises:
        ValueError: The requested node is unavailable.
        TypeError: An input is not real.

    Examples:
        >>> annex_d4_table_coefficient(1.0, 1.0)
        0.483

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_all_annex_d4_cells_match_json
        Validation cases:
            - BC-D4-*

    Implementation notes:
        - Stage N6 consumes this exact-node lookup directly; no general interpolation rule is inferred.
        - Defaults must be explicit in the input configuration.
    """
    return _doc_table_raw("D4", relative_effective_slenderness, relative_eccentricity_m)


def annex_d4_stability_coefficient(
    relative_effective_slenderness: float,
    relative_eccentricity_m: float,
    central_compression_phi: float,
) -> float:
    """
    Summary:
        Apply the Table D.4 lookup and cap the result by central-compression phi.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.2
        Annex: D
        Equation/Table: Table D.4, note 2
        Audit ID: SP16-TBL-Д-4
        Normative status: normative

    Mathematical form:
        phi_e = min(Table D.4 value, phi).

    Parameters:
        relative_effective_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Exact Table D.4 row node.
            Valid range: printed node
            Source: Table D.4
        relative_eccentricity_m:
            Type: float
            Unit: dimensionless
            Meaning: Exact Table D.4 column node.
            Valid range: printed node available in row
            Source: clause 9.3.2
        central_compression_phi:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression coefficient for the same effective slenderness.
            Valid range: (0, 1]
            Source: clause 7.2 and 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped Table D.4 stability coefficient.

    Assumptions:
        - Central phi is evaluated consistently.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Built-up eccentric-compression members.

    Limitations:
        - Non-node Table D.4 requests require explicit external provenance or remain fail-closed in Stage N6.

    Raises:
        ValueError: An input or node is invalid.
        TypeError: An input is not real.

    Examples:
        >>> annex_d4_stability_coefficient(1.0, 1.0, 0.45)
        0.45

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d3_and_d4_central_phi_caps
        Validation cases:
            - BC-D4-CAP

    Implementation notes:
        - Raw and capped APIs are separated for traceability.
        - Defaults must be explicit in the input configuration.
    """
    return min(annex_d4_table_coefficient(relative_effective_slenderness, relative_eccentricity_m), _ratio_0_1(central_compression_phi, "central_compression_phi"))


def annex_d5_effective_relative_eccentricity(
    end_moment_ratio_delta: float,
    geometric_slenderness: float,
    reference_effective_eccentricity_m_eff_1: float,
) -> float:
    """
    Summary:
        Return effective relative eccentricity m_eff from Table D.5 for a pinned-ended doubly symmetric member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.3
        Annex: D
        Equation/Table: Table D.5
        Audit ID: SP16-TBL-Д-5
        Normative status: normative

    Mathematical form:
        Exact lookup by delta=M_2/M_1, geometric lambda, and m_eff,1=eta*(M_1/N)*(A/W_c).

    Parameters:
        end_moment_ratio_delta:
            Type: float
            Unit: dimensionless
            Meaning: End-moment ratio delta=M_2/M_1 with the printed diagram sign convention.
            Valid range: one of -1.0, -0.5, 0.0, 0.5
            Source: Table D.5 moment diagram
        geometric_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Geometric slenderness lambda.
            Valid range: integer node 1-7
            Source: Table D.5
        reference_effective_eccentricity_m_eff_1:
            Type: float
            Unit: dimensionless
            Meaning: m_eff,1 at end moment M_1.
            Valid range: exact printed node
            Source: Table D.5 definition

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective relative eccentricity m_eff.

    Assumptions:
        - The member is pinned-ended and doubly symmetric.

    Sign convention:
        - Delta follows the four printed moment diagrams.

    Unit convention:
        - Dimensionless.

    Applicability:
        - The 9.2.3 special route for doubly symmetric solid members with end moments.

    Limitations:
        - No interpolation or diagram recognition is performed.

    Raises:
        ValueError: A requested node is unavailable.
        TypeError: An input is not real.

    Examples:
        >>> annex_d5_effective_relative_eccentricity(-1.0, 2.0, 1.0)
        0.39

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_all_annex_d5_cells_match_json
        Validation cases:
            - BC-D5-*

    Implementation notes:
        - The printed 2.55 value at delta=0, lambda=1, m_eff,1=4 is preserved without editorial correction.
        - Defaults must be explicit in the input configuration.
    """
    table = _ANNEX_D["tables"]["D5"]
    delta_key = _exact_key(end_moment_ratio_delta, [float(x) for x in table["rows"].keys()], "end_moment_ratio_delta")
    rows = table["rows"][delta_key]
    lambda_value = _real(geometric_slenderness, "geometric_slenderness")
    lambda_key = next(
        (key for key in rows if math.isclose(lambda_value, float(key), rel_tol=0.0, abs_tol=1e-12)),
        None,
    )
    if lambda_key is None:
        raise ValueError(f"geometric_slenderness must equal a printed table node: {[float(x) for x in rows]}")
    row = rows[lambda_key]
    m_value = _real(reference_effective_eccentricity_m_eff_1, "reference_effective_eccentricity_m_eff_1")
    m_key = next(
        (key for key in row if math.isclose(m_value, float(key), rel_tol=0.0, abs_tol=1e-12)),
        None,
    )
    if m_key is None:
        raise ValueError(
            "reference_effective_eccentricity_m_eff_1 must equal a printed table node: "
            f"{[float(x) for x in row]}"
        )
    return float(row[m_key])


def annex_d6_section_parameters(section_type: str) -> dict[str, str]:
    """
    Summary:
        Return the audited symbolic parameter definitions from Table D.6.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: Annex D open-section c_max procedure
        Annex: D
        Equation/Table: Table D.6
        Audit ID: SP16-TBL-Д-6
        Normative status: normative

    Mathematical form:
        Symbolic omega*, alpha*, and beta* definitions by diagram type.

    Parameters:
        section_type:
            Type: str
            Unit: not applicable
            Meaning: Table D.6 diagram type.
            Valid range: '1', '2', '3', or '4'; type 5 is excluded
            Source: engineer classification

    Returns:
        Type: dict[str, str]
        Unit: symbolic metadata
        Meaning: Audited formulas or constants for the selected row.

    Assumptions:
        - The section is classified from the printed diagrams.

    Sign convention:
        - Sign-sensitive eccentricity remains an input to equation (D.1), not this metadata lookup.

    Unit convention:
        - Returned formulas are dimensionless symbolic ratios.

    Applicability:
        - Open-section c_max calculations.

    Limitations:
        - The function does not evaluate section properties or equation (Ж.12).

    Raises:
        ValueError: The type is unsupported or excluded.
        TypeError: section_type is not a string.

    Examples:
        >>> annex_d6_section_parameters('1')['omega_star']
        '0.25'

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d6_metadata
        Validation cases:
            - BC-D6-*

    Implementation notes:
        - Table D.6 is exposed as metadata because diagram geometry and Ж.12 dependencies remain explicit.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(section_type, str):
        raise TypeError("section_type must be str")
    rows = _ANNEX_D["tables"]["D6"]["rows"]
    if section_type not in rows:
        raise ValueError("section_type must be one of '1', '2', '3', '4'")
    row = rows[section_type]
    if row.get("status"):
        raise ValueError(f"Table D.6 type {section_type} is {row['status']}")
    return dict(row)


def annex_d_open_section_parameters_eq_d2(
    alpha_shear_center_ratio: float,
    beta_section_parameter: float,
    major_axis_inertia_mm4: float,
    minor_axis_inertia_mm4: float,
    sectorial_inertia_mm6: float,
    torsional_inertia_mm4: float,
    geometric_slenderness_y: float,
    gross_area_mm2: float,
    section_height_mm: float,
    eccentricity_x_mm: float,
) -> dict[str, float]:
    """
    Summary:
        Calculate rho, omega, delta, B, and mu for the Annex D open-section c_max equation.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: Annex D, open-section stability coefficient procedure
        Annex: D
        Equation/Table: Equation (D.2)
        Audit ID: SP16-EQ-Д-002
        Normative status: normative

    Mathematical form:
        rho=(I_x+I_y)/(A*h^2)+alpha^2; omega=I_omega/(I_y*h^2); mu=8*omega+0.156*I_t*lambda_y^2/(A*h^2); delta=4*rho/mu; B=1+2*(beta/rho)*(e_x/h).

    Parameters:
        alpha_shear_center_ratio:
            Type: float
            Unit: dimensionless
            Meaning: alpha=a_x/h, signed shear-center offset ratio.
            Valid range: finite real
            Source: section geometry
        beta_section_parameter:
            Type: float
            Unit: dimensionless
            Meaning: Section parameter beta from Table D.6 and linked Annex Ж expression.
            Valid range: finite real
            Source: Table D.6
        major_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_x.
            Valid range: > 0
            Source: section model
        minor_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_y.
            Valid range: > 0
            Source: section model
        sectorial_inertia_mm6:
            Type: float
            Unit: mm6
            Meaning: I_omega.
            Valid range: >= 0
            Source: section model
        torsional_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_t for free torsion.
            Valid range: >= 0
            Source: section model or Annex D plate-sum rule
        geometric_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Geometric slenderness lambda_y.
            Valid range: >= 0
            Source: effective length and radius of gyration
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Section area A.
            Valid range: > 0
            Source: section model
        section_height_mm:
            Type: float
            Unit: mm
            Meaning: Section height h.
            Valid range: > 0
            Source: section model
        eccentricity_x_mm:
            Type: float
            Unit: mm
            Meaning: Signed eccentricity e_x=M_x/N.
            Valid range: finite real
            Source: structural analysis

    Returns:
        Type: dict[str, float]
        Unit: dimensionless parameter bundle
        Meaning: rho, omega, mu, delta, B, alpha, and e_x/h.

    Assumptions:
        - Section properties use consistent axes and units.

    Sign convention:
        - e_x and alpha retain their signs; the standard states e_x is positive in the direction shown in Table D.6.

    Unit convention:
        - mm-based section properties produce dimensionless ratios.

    Applicability:
        - Annex D equation (D.1) for open sections.

    Limitations:
        - Beta and diagram classification are not inferred.

    Raises:
        ValueError: A required positive property is invalid or mu is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> round(annex_d_open_section_parameters_eq_d2(0,0,8e6,2e6,4e10,1e4,50,3000,300,0)['rho'],6)
        0.037037

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d_equations_d1_d2_and_d4
        Validation cases:
            - BC-EQ-D2

    Implementation notes:
        - Geometric lambda_y, not relative slenderness, is used as printed.
        - Defaults must be explicit in the input configuration.
    """
    alpha = _real(alpha_shear_center_ratio, "alpha_shear_center_ratio")
    beta = _real(beta_section_parameter, "beta_section_parameter")
    ix = _positive(major_axis_inertia_mm4, "major_axis_inertia_mm4")
    iy = _positive(minor_axis_inertia_mm4, "minor_axis_inertia_mm4")
    iw = _nonnegative(sectorial_inertia_mm6, "sectorial_inertia_mm6")
    it = _nonnegative(torsional_inertia_mm4, "torsional_inertia_mm4")
    lam = _nonnegative(geometric_slenderness_y, "geometric_slenderness_y")
    area = _positive(gross_area_mm2, "gross_area_mm2")
    height = _positive(section_height_mm, "section_height_mm")
    ex = _real(eccentricity_x_mm, "eccentricity_x_mm")
    rho = (ix + iy) / (area * height * height) + alpha * alpha
    omega = iw / (iy * height * height)
    mu = 8.0 * omega + 0.156 * it * lam * lam / (area * height * height)
    if mu <= 0.0:
        raise ValueError("equation (D.2) requires positive mu")
    if rho <= 0.0:
        raise ValueError("equation (D.2) requires positive rho")
    delta = 4.0 * rho / mu
    ex_ratio = ex / height
    capital_b = 1.0 + 2.0 * (beta / rho) * ex_ratio
    return {"rho": rho, "omega": omega, "mu": mu, "delta": delta, "B": capital_b, "alpha": alpha, "eccentricity_ratio": ex_ratio}


def annex_d_open_section_cmax_eq_d1(parameter_bundle: dict[str, float]) -> float:
    """
    Summary:
        Calculate c_max for open-section compressed members from the Annex D parameter bundle.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: Annex D, open-section stability coefficient procedure
        Annex: D
        Equation/Table: Equation (D.1)
        Audit ID: SP16-EQ-Д-001
        Normative status: normative

    Mathematical form:
        c_max=2/[1+delta*B+sqrt((1-delta*B)^2+16/mu*(alpha-e_x/h)^2)].

    Parameters:
        parameter_bundle:
            Type: dict[str, float]
            Unit: dimensionless
            Meaning: Bundle containing delta, B, mu, alpha, and eccentricity_ratio from equation (D.2).
            Valid range: positive mu and non-negative radicand
            Source: annex_d_open_section_parameters_eq_d2

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Maximum permitted coefficient c_max.

    Assumptions:
        - The bundle was formed from consistent section properties.

    Sign convention:
        - Signed alpha and eccentricity ratio are preserved in their difference.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Open-section types addressed by Annex D.

    Limitations:
        - Section type and beta remain external audited inputs.

    Raises:
        ValueError: Required keys are missing or the denominator is non-positive.
        TypeError: parameter_bundle is not a dictionary.

    Examples:
        >>> p={'delta':1.0,'B':1.0,'mu':4.0,'alpha':0.0,'eccentricity_ratio':0.0}
        >>> annex_d_open_section_cmax_eq_d1(p)
        1.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d_equations_d1_d2_and_d4
        Validation cases:
            - BC-EQ-D1

    Implementation notes:
        - The function does not clip c_max to one because clause 9.2.5 applies c<=1 separately.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(parameter_bundle, dict):
        raise TypeError("parameter_bundle must be dict")
    try:
        delta = _real(parameter_bundle["delta"], "parameter_bundle['delta']")
        capital_b = _real(parameter_bundle["B"], "parameter_bundle['B']")
        mu = _positive(parameter_bundle["mu"], "parameter_bundle['mu']")
        alpha = _real(parameter_bundle["alpha"], "parameter_bundle['alpha']")
        ex_ratio = _real(parameter_bundle["eccentricity_ratio"], "parameter_bundle['eccentricity_ratio']")
    except KeyError as exc:
        raise ValueError(f"parameter_bundle missing key: {exc.args[0]}") from exc
    radicand = (1.0 - delta * capital_b) ** 2 + 16.0 / mu * (alpha - ex_ratio) ** 2
    denominator = 1.0 + delta * capital_b + math.sqrt(radicand)
    if denominator <= 0.0:
        raise ValueError("equation (D.1) produced a non-positive denominator")
    return 2.0 / denominator


def annex_d_continuous_bracing_cmax_eq_d4(
    major_axis_inertia_mm4: float,
    minor_axis_inertia_mm4: float,
    major_axis_radius_mm: float,
    minor_axis_radius_mm: float,
    section_height_mm: float,
    eccentricity_x_mm: float,
    annex_zh_alpha_parameter: float,
) -> float:
    """
    Summary:
        Calculate c_max for a doubly symmetric I-section continuously braced along one flange.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.7 and Annex D paragraph 4
        Annex: D
        Equation/Table: Equation (D.4)
        Audit ID: SP16-EQ-Д-004
        Normative status: normative

    Mathematical form:
        c_max=(1+I_x/I_y+alpha/9.87)/[1+4*((i_x^2+i_y^2)/h^2+e_x/h)].

    Parameters:
        major_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_x.
            Valid range: > 0
            Source: section model
        minor_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_y.
            Valid range: > 0
            Source: section model
        major_axis_radius_mm:
            Type: float
            Unit: mm
            Meaning: Radius of gyration i_x.
            Valid range: > 0
            Source: section model
        minor_axis_radius_mm:
            Type: float
            Unit: mm
            Meaning: Radius of gyration i_y.
            Valid range: > 0
            Source: section model
        section_height_mm:
            Type: float
            Unit: mm
            Meaning: Section height h.
            Valid range: > 0
            Source: section model
        eccentricity_x_mm:
            Type: float
            Unit: mm
            Meaning: e_x=M_x/N, positive toward the unbraced flange as specified in Annex D.
            Valid range: finite real
            Source: structural analysis
        annex_zh_alpha_parameter:
            Type: float
            Unit: dimensionless
            Meaning: Alpha determined by equation (Ж.1) as referenced below equation (D.4).
            Valid range: finite real consistent with Annex Ж
            Source: Annex Ж

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c_max for the continuous-flange-bracing case.

    Assumptions:
        - The element is continuously braced along one flange and the effective length follows the Annex D rule.

    Sign convention:
        - e_x is positive toward the unbraced flange.

    Unit convention:
        - mm-based ratios are dimensionless.

    Applicability:
        - Clause 9.2.7.

    Limitations:
        - The function does not calculate the Annex Ж alpha parameter.

    Raises:
        ValueError: A required property is non-positive or the denominator is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> round(annex_d_continuous_bracing_cmax_eq_d4(8e6,2e6,50,25,300,0,20),6)
        3.118878

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_annex_d_equations_d1_d2_and_d4
        Validation cases:
            - BC-EQ-D4

    Implementation notes:
        - Clause 9.2.5 still applies c<=c_max, c<=1, and c>=0.3.
        - Defaults must be explicit in the input configuration.
    """
    ix = _positive(major_axis_inertia_mm4, "major_axis_inertia_mm4")
    iy = _positive(minor_axis_inertia_mm4, "minor_axis_inertia_mm4")
    rx = _positive(major_axis_radius_mm, "major_axis_radius_mm")
    ry = _positive(minor_axis_radius_mm, "minor_axis_radius_mm")
    h = _positive(section_height_mm, "section_height_mm")
    ex = _real(eccentricity_x_mm, "eccentricity_x_mm")
    alpha = _real(annex_zh_alpha_parameter, "annex_zh_alpha_parameter")
    denominator = 1.0 + 4.0 * ((rx * rx + ry * ry) / (h * h) + ex / h)
    if denominator <= 0.0:
        raise ValueError("equation (D.4) produced a non-positive denominator")
    return (1.0 + ix / iy + alpha / 9.87) / denominator


def out_of_plane_coefficient_c(
    relative_eccentricity_mx: float,
    alpha: float,
    beta: float,
    central_phi_y: float,
    bending_phi_b: float,
    c_max: float,
) -> dict[str, float | str]:
    """
    Summary:
        Route equations (112)-(114) and apply the printed c_max, upper, and lower limits.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.5
        Annex: D and Ж
        Equation/Table: Equations (112)-(114)
        Audit ID: SP16-PROC-9.2.5-CMAX-CAP-AND-MINIMUM
        Normative status: normative

    Mathematical form:
        Select c_raw by m_x branch; c=min(c_raw,c_max,1); then c=max(c,0.3).

    Parameters:
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: >= 0
            Source: clause 9.2.5
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Table 21 alpha used for equation (112).
            Valid range: >= 0
            Source: Table 21
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Table 21 beta used for equation (112).
            Valid range: > 0
            Source: Table 21
        central_phi_y:
            Type: float
            Unit: dimensionless
            Meaning: phi_y for equation (113).
            Valid range: (0, 1]
            Source: clause 7.1.3
        bending_phi_b:
            Type: float
            Unit: dimensionless
            Meaning: phi_b for equation (113).
            Valid range: > 0
            Source: Annex Ж
        c_max:
            Type: float
            Unit: dimensionless
            Meaning: Annex D maximum c where lambda_bar_y>3.14; pass a justified value also for lower slenderness for deterministic routing.
            Valid range: > 0
            Source: Annex D

    Returns:
        Type: dict[str, float | str]
        Unit: dimensionless values and branch label
        Meaning: raw coefficient, final coefficient, c_max, and selected branch.

    Assumptions:
        - All coefficients refer to the same member.

    Sign convention:
        - m_x is non-negative.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 9.2.5.

    Limitations:
        - The caller supplies c_max because multiple Annex D section routes exist.

    Raises:
        ValueError: A branch or coefficient input is invalid.
        TypeError: An input is not real.

    Examples:
        >>> out_of_plane_coefficient_c(2,0.7,1,0.8,0.9,0.9)['c']
        0.4166666666666667

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_112_to_114_and_router
        Validation cases:
            - BC-PROC-C-ROUTER

    Implementation notes:
        - c=0.3 is a minimum even if the calculated or capped value is lower.
        - Defaults must be explicit in the input configuration.
    """
    mx = _nonnegative(relative_eccentricity_mx, "relative_eccentricity_mx")
    cmax = _positive(c_max, "c_max")
    if mx <= 5.0:
        raw = out_of_plane_coefficient_c_eq112(alpha, beta, mx)
        branch = "equation_112"
    elif mx >= 10.0:
        raw = out_of_plane_coefficient_c_eq113(mx, central_phi_y, bending_phi_b)
        branch = "equation_113"
    else:
        c5 = out_of_plane_coefficient_c_eq112(alpha, beta, 5.0)
        c10 = out_of_plane_coefficient_c_eq113(10.0, central_phi_y, bending_phi_b)
        raw = out_of_plane_coefficient_c_eq114(mx, c5, c10)
        branch = "equation_114"
    final = max(0.3, min(raw, cmax, 1.0))
    return {"branch": branch, "c_raw": raw, "c_max": cmax, "c": final}


def design_moment_clause_9_2_6(
    member_end_condition: str,
    maximum_moment_n_mm: float,
    middle_third_maximum_moment_n_mm: float,
    fixed_end_moment_n_mm: float,
    one_third_from_fixed_moment_n_mm: float,
) -> float:
    """
    Summary:
        Select the design moment M_x used to calculate m_x in equations (112)-(114).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.6
        Annex: None
        Equation/Table: Moment-selection procedure
        Audit ID: SP16-PROC-9.2.6-DESIGN-MOMENT-SELECTION
        Normative status: normative

    Mathematical form:
        Restrained ends: max(M_middle_third,0.5*M_max); cantilever: max(M_fixed,M_at_L_over_3).

    Parameters:
        member_end_condition:
            Type: str
            Unit: not applicable
            Meaning: 'laterally_restrained_ends' or 'cantilever'.
            Valid range: one of the two identifiers
            Source: structural system
        maximum_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Largest moment along the member.
            Valid range: >= 0
            Source: elastic analysis
        middle_third_maximum_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Largest moment in the middle third.
            Valid range: >= 0
            Source: elastic analysis
        fixed_end_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Moment at the cantilever fixing.
            Valid range: >= 0
            Source: elastic analysis
        one_third_from_fixed_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Moment at one third of member length from the fixing.
            Valid range: >= 0
            Source: elastic analysis

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Design moment M_x for m_x.

    Assumptions:
        - Inputs are absolute moment magnitudes from the same load combination.

    Sign convention:
        - Moment magnitudes are non-negative.

    Unit convention:
        - N*mm.

    Applicability:
        - Clause 9.2.6.

    Limitations:
        - Other end conditions are not defined by the clause and are rejected.

    Raises:
        ValueError: End condition or moment input is invalid.
        TypeError: A moment is not real.

    Examples:
        >>> design_moment_clause_9_2_6('laterally_restrained_ends',100,40,0,0)
        50.0

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_clause_9_2_6_moment_selection
        Validation cases:
            - BC-PROC-9.2.6-*

    Implementation notes:
        - Unused branch inputs remain explicit so a single schema can cover both cases.
        - Defaults must be explicit in the input configuration.
    """
    mmax = _nonnegative(maximum_moment_n_mm, "maximum_moment_n_mm")
    middle = _nonnegative(middle_third_maximum_moment_n_mm, "middle_third_maximum_moment_n_mm")
    fixed = _nonnegative(fixed_end_moment_n_mm, "fixed_end_moment_n_mm")
    third = _nonnegative(one_third_from_fixed_moment_n_mm, "one_third_from_fixed_moment_n_mm")
    if member_end_condition == "laterally_restrained_ends":
        return max(middle, 0.5 * mmax)
    if member_end_condition == "cantilever":
        return max(fixed, third)
    raise ValueError("member_end_condition must be 'laterally_restrained_ends' or 'cantilever'")


def stability_check_route_clause_9_2_1(moment_in_one_principal_plane: bool) -> dict[str, bool]:
    """
    Summary:
        Return the required in-plane and out-of-plane stability checks under clause 9.2.1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.1
        Annex: None
        Equation/Table: Procedure
        Audit ID: SP16-PROC-9.2.1-TWO-PLANE-STABILITY
        Normative status: normative

    Mathematical form:
        A moment acting in one principal plane requires both in-plane and out-of-plane checks.

    Parameters:
        moment_in_one_principal_plane:
            Type: bool
            Unit: not applicable
            Meaning: Confirms the clause 9.2.1 loading case.
            Valid range: bool
            Source: force state

    Returns:
        Type: dict[str, bool]
        Unit: flags
        Meaning: Required check flags.

    Assumptions:
        - The member is eccentrically compressed or compression-bent.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Not applicable.

    Applicability:
        - Clause 9.2.1.

    Limitations:
        - The function reports requirements but does not perform the checks.

    Raises:
        TypeError: The input is not bool.

    Examples:
        >>> stability_check_route_clause_9_2_1(True)['out_of_plane_required']
        True

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_clause_routes
        Validation cases:
            - BC-PROC-9.2.1

    Implementation notes:
        - Both checks remain mandatory for the stated case.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(moment_in_one_principal_plane, bool):
        raise TypeError("moment_in_one_principal_plane must be bool")
    return {
        "in_plane_required": bool(moment_in_one_principal_plane),
        "out_of_plane_required": bool(moment_in_one_principal_plane),
    }


def minor_axis_bending_route_clause_9_2_8(relative_slenderness_x: float, relative_slenderness_y: float) -> dict[str, bool]:
    """
    Summary:
        Determine whether equation (115) is additionally required for minor-axis bending.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.8
        Annex: None
        Equation/Table: Procedure and equation (115)
        Audit ID: SP16-PROC-9.2.8-MINOR-AXIS-ROUTING
        Normative status: normative

    Mathematical form:
        Equation (109) is required; equation (115) is additionally required only if lambda_x>lambda_y.

    Parameters:
        relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_x.
            Valid range: >= 0
            Source: member geometry
        relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness lambda_bar_y.
            Valid range: >= 0
            Source: member geometry

    Returns:
        Type: dict[str, bool]
        Unit: flags
        Meaning: Required equation (109) and equation (115) checks.

    Assumptions:
        - I_y<I_x and e_y is nonzero as stated in the clause.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Dimensionless slendernesses.

    Applicability:
        - Clause 9.2.8.

    Limitations:
        - The section and bending plane conditions are explicit engineering classifications.

    Raises:
        ValueError: A slenderness is negative.
        TypeError: An input is not real.

    Examples:
        >>> minor_axis_bending_route_clause_9_2_8(3.0,2.0)['equation_115_required']
        True

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equation_115_and_clause_9_2_8_route
        Validation cases:
            - BC-PROC-9.2.8

    Implementation notes:
        - Equality does not trigger equation (115), matching lambda_x<=lambda_y text.
        - Defaults must be explicit in the input configuration.
    """
    lx = _nonnegative(relative_slenderness_x, "relative_slenderness_x")
    ly = _nonnegative(relative_slenderness_y, "relative_slenderness_y")
    return {"equation_109_required": True, "equation_115_required": lx > ly}


def biaxial_additional_checks_clause_9_2_9(
    effective_relative_eccentricity_y: float,
    relative_eccentricity_x: float,
    relative_slenderness_x: float,
    relative_slenderness_y: float,
) -> dict[str, bool]:
    """
    Summary:
        Determine the clause 9.2.9 biaxial route and any additional equation (109)/(111) checks.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: None
        Equation/Table: Procedure following equations (116)-(117)
        Audit ID: SP16-PROC-9.2.9-BIAXIAL-ADDITIONAL-CHECKS
        Normative status: normative

    Mathematical form:
        If m_eff,y<m_x, require (109) and (111) with e_y=0; if lambda_x>lambda_y, require (109) with e_y=0.

    Parameters:
        effective_relative_eccentricity_y:
            Type: float
            Unit: dimensionless
            Meaning: m_eff,y=eta*m_y.
            Valid range: >= 0
            Source: equation (110) applied to y
        relative_eccentricity_x:
            Type: float
            Unit: dimensionless
            Meaning: m_x.
            Valid range: >= 0
            Source: equation (118)
        relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: lambda_bar_x.
            Valid range: >= 0
            Source: member geometry
        relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: lambda_bar_y.
            Valid range: >= 0
            Source: member geometry

    Returns:
        Type: dict[str, bool]
        Unit: flags
        Meaning: Additional check requirements.

    Assumptions:
        - Equation (116) applies only while m_eff,y<=20; when m_eff,y>20 the y-route is transferred to Section 8, while independent additional triggers are still surfaced.

    Sign convention:
        - Eccentricities are non-negative magnitudes.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 9.2.9.

    Limitations:
        - The function does not execute the additional checks.

    Raises:
        ValueError: An input is negative.
        TypeError: An input is not real.

    Examples:
        >>> biaxial_additional_checks_clause_9_2_9(0.5,1.0,2.0,3.0)['equation_111_with_ey_zero_required']
        True

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-PROC-9.2.9

    Implementation notes:
        - The two triggers are preserved separately in the result.
        - Defaults must be explicit in the input configuration.
    """
    mefy = _nonnegative(effective_relative_eccentricity_y, "effective_relative_eccentricity_y")
    mx = _nonnegative(relative_eccentricity_x, "relative_eccentricity_x")
    lx = _nonnegative(relative_slenderness_x, "relative_slenderness_x")
    ly = _nonnegative(relative_slenderness_y, "relative_slenderness_y")
    eccentricity_trigger = mefy < mx
    slenderness_trigger = lx > ly
    equation_116_required = mefy <= 20.0
    return {
        "equation_116_required": equation_116_required,
        "section_8_y_route_required": mefy > 20.0,
        # The additional x-plane checks are evaluated from their own triggers.
        # A meff_y>20 Section-8 route does not erase a lambda_x>lambda_y trigger.
        "equation_109_with_ey_zero_required": eccentricity_trigger or slenderness_trigger,
        "equation_111_with_ey_zero_required": eccentricity_trigger,
        "eccentricity_trigger": eccentricity_trigger,
        "slenderness_trigger": slenderness_trigger,
    }


def adjusted_relative_eccentricity_x_clause_9_2_9(
    relative_eccentricity_x: float,
    major_stiffness_plane_coincides_with_symmetry_plane: bool,
    table_21_section_type: str,
) -> float:
    """
    Summary:
        Apply the 25% increase to m_x when the major-stiffness plane does not coincide with a symmetry plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.9
        Annex: None
        Equation/Table: Procedure after equation (119)
        Audit ID: SP16-PROC-9.2.9-NONSYMMETRIC-MX-INCREASE
        Normative status: normative

    Mathematical form:
        m_x,design=1.25*m_x if planes do not coincide, except Table 21 type 3; otherwise m_x.

    Parameters:
        relative_eccentricity_x:
            Type: float
            Unit: dimensionless
            Meaning: Calculated m_x.
            Valid range: >= 0
            Source: equation (118)
        major_stiffness_plane_coincides_with_symmetry_plane:
            Type: bool
            Unit: not applicable
            Meaning: Section-axis classification.
            Valid range: bool
            Source: section geometry
        table_21_section_type:
            Type: str
            Unit: not applicable
            Meaning: Table 21 type, with type 3 exempt from the increase.
            Valid range: '1', '2', '3', or '4'
            Source: engineer classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Adjusted m_x.

    Assumptions:
        - Section type is correctly classified.

    Sign convention:
        - m_x is a non-negative magnitude.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Clause 9.2.9.

    Limitations:
        - Geometry classification is not automated.

    Raises:
        ValueError: Section type is invalid or m_x is negative.
        TypeError: The plane flag is not bool.

    Examples:
        >>> adjusted_relative_eccentricity_x_clause_9_2_9(2.0,False,'1')
        2.5

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_116_to_119_and_additional_routes
        Validation cases:
            - BC-PROC-9.2.9-MX

    Implementation notes:
        - The type-3 exception is explicit.
        - Defaults must be explicit in the input configuration.
    """
    mx = _nonnegative(relative_eccentricity_x, "relative_eccentricity_x")
    if not isinstance(major_stiffness_plane_coincides_with_symmetry_plane, bool):
        raise TypeError("major_stiffness_plane_coincides_with_symmetry_plane must be bool")
    if table_21_section_type not in {"1", "2", "3", "4"}:
        raise ValueError("table_21_section_type must be one of '1', '2', '3', '4'")
    if major_stiffness_plane_coincides_with_symmetry_plane or table_21_section_type == "3":
        return mx
    return 1.25 * mx


def box_major_axis_phi_clause_9_2_10(
    bending_in_major_stiffness_plane: bool,
    minor_axis_moment_is_zero: bool,
    phi_ex: float,
    phi_ey: float,
) -> float:
    """
    Summary:
        Select phi_ex or the printed phi_ey substitution for equation (120).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.10
        Annex: None
        Equation/Table: Procedure after equation (122)
        Audit ID: SP16-PROC-9.2.10-BOX-MAJOR-AXIS-SUBSTITUTION
        Normative status: normative

    Mathematical form:
        Use phi_ey instead of phi_ex when I_x>I_y and M_y=0; otherwise use phi_ex.

    Parameters:
        bending_in_major_stiffness_plane:
            Type: bool
            Unit: not applicable
            Meaning: Confirms I_x>I_y and bending in the major-stiffness plane.
            Valid range: bool
            Source: section and force state
        minor_axis_moment_is_zero:
            Type: bool
            Unit: not applicable
            Meaning: Confirms M_y=0.
            Valid range: bool
            Source: structural analysis
        phi_ex:
            Type: float
            Unit: dimensionless
            Meaning: Major-plane eccentric-compression coefficient.
            Valid range: (0, 1]
            Source: Table D.3
        phi_ey:
            Type: float
            Unit: dimensionless
            Meaning: Minor-plane eccentric-compression coefficient.
            Valid range: (0, 1]
            Source: Table D.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Coefficient to use in the axial term of equation (120).

    Assumptions:
        - The box-section route of clause 9.2.10 applies.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (120).

    Limitations:
        - The function does not infer I_x>I_y or numerical zero tolerance.

    Raises:
        TypeError: A flag is not bool.
        ValueError: A coefficient is invalid.

    Examples:
        >>> box_major_axis_phi_clause_9_2_10(True,True,0.7,0.8)
        0.8

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_equations_120_to_122_and_major_axis_substitution
        Validation cases:
            - BC-PROC-9.2.10-PHI

    Implementation notes:
        - Zero-moment classification is an explicit boolean to avoid hidden tolerances.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(bending_in_major_stiffness_plane, bool) or not isinstance(minor_axis_moment_is_zero, bool):
        raise TypeError("bending and moment flags must be bool")
    ex = _ratio_0_1(phi_ex, "phi_ex")
    ey = _ratio_0_1(phi_ey, "phi_ey")
    return ey if bending_in_major_stiffness_plane and minor_axis_moment_is_zero else ex


def beam_column_section_9_2_route(
    effective_relative_eccentricity: float,
    section_is_box: bool,
    bending_in_one_plane: bool,
    bending_in_two_planes: bool,
) -> dict[str, Any]:
    """
    Summary:
        Provide a deterministic high-level route among Section 9.2 equation families.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 9.2.1-9.2.10
        Annex: D
        Equation/Table: Procedure wrapper
        Audit ID: SP16-PROC-9.2.2-BENDING-ROUTE-MEFF-GT20
        Normative status: normative

    Mathematical form:
        m_eff>20 routes to Section 8; box sections route to (120)-(122); biaxial non-box sections route to (116)-(119).

    Parameters:
        effective_relative_eccentricity:
            Type: float
            Unit: dimensionless
            Meaning: Governing effective relative eccentricity.
            Valid range: >= 0
            Source: equation (110) or Table D.5
        section_is_box:
            Type: bool
            Unit: not applicable
            Meaning: Box-section classification.
            Valid range: bool
            Source: section geometry
        bending_in_one_plane:
            Type: bool
            Unit: not applicable
            Meaning: Confirms one-plane bending state.
            Valid range: bool
            Source: force state
        bending_in_two_planes:
            Type: bool
            Unit: not applicable
            Meaning: Confirms biaxial bending state.
            Valid range: bool
            Source: force state

    Returns:
        Type: dict[str, Any]
        Unit: route identifiers and flags
        Meaning: Required equation family or Section 8 route.

    Assumptions:
        - Exactly one bending-state flag is true.

    Sign convention:
        - Effective eccentricity is non-negative.

    Unit convention:
        - Dimensionless route input.

    Applicability:
        - User-facing Section 9.2 orchestration.

    Limitations:
        - The wrapper does not replace clause-specific applicability checks.

    Raises:
        ValueError: Bending-state flags are inconsistent or m_eff is negative.
        TypeError: A classification flag is not bool.

    Examples:
        >>> beam_column_section_9_2_route(2.0,False,False,True)['route']
        'equations_116_to_119'

    Tests:
        Unit tests:
            - tests/test_beam_column_stability.py::test_clause_routes
        Validation cases:
            - BC-PROC-ROUTE

    Implementation notes:
        - Section 8 routing is surfaced rather than silently applying a beam equation.
        - Defaults must be explicit in the input configuration.
    """
    meff = _nonnegative(effective_relative_eccentricity, "effective_relative_eccentricity")
    for value, name in ((section_is_box, "section_is_box"), (bending_in_one_plane, "bending_in_one_plane"), (bending_in_two_planes, "bending_in_two_planes")):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be bool")
    if bending_in_one_plane == bending_in_two_planes:
        raise ValueError("exactly one of bending_in_one_plane and bending_in_two_planes must be true")
    if meff > 20.0:
        return {"route": "section_8_bending_member", "section_9_2_stability_required": False}
    if section_is_box:
        return {"route": "equations_120_to_122", "section_9_2_stability_required": True}
    if bending_in_two_planes:
        return {"route": "equations_116_to_119", "section_9_2_stability_required": True}
    return {"route": "equations_109_to_115", "section_9_2_stability_required": True}
