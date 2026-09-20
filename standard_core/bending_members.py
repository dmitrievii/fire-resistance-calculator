"""Strength checks for bending members under SP 16.13330.2017 clauses 8.1-8.2."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_10A = json.loads((_DATA_DIR / "table_10a_constrained_torsion_coefficients.json").read_text(encoding="utf-8"))
_TABLE_E1 = json.loads((_DATA_DIR / "annex_e_table_e1_plastic_coefficients.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-8.1-CLASS-ROUTING",
    "SP16-PROC-8.2.1-ELASTIC-STRESS-POINT",
    "SP16-PROC-8.2.1-BOLT-HOLE-ADJUSTMENT",
    "SP16-PROC-8.2.2-LOCAL-LOAD-LENGTH",
    "SP16-PROC-8.2.3-PLASTIC-APPLICABILITY",
    "SP16-PROC-8.2.3-ANNEX-E1-INTERPOLATION",
    "SP16-PROC-8.2.3-ANNEX-E1-CAP",
    "SP16-PROC-8.2.3-TABLE-10A-INTERPOLATION",
    "SP16-PROC-8.2.3-PURE-BENDING-COEFFICIENTS",
    "SP16-PROC-8.2.4-VARIABLE-SECTION-ROUTING",
    "SP16-PROC-8.2.5-CONTINUOUS-BEAM-APPLICABILITY",
    "SP16-PROC-8.2.5-EFFECTIVE-MOMENT-ROUTING",
    "SP16-PROC-8.2.6-BIAXIAL-REDISTRIBUTION",
    "SP16-PROC-8.2.7-CLASS-3-ROUTING",
    "SP16-PROC-8.2.8-BIMETAL-APPLICABILITY",
    "SP16-PROC-8.2.8-BIMETAL-MINOR-COEFFICIENT",
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


def _ratio(numerator: float, denominator: float, numerator_name: str, denominator_name: str) -> float:
    return _nonnegative(numerator, numerator_name) / _positive(denominator, denominator_name)


def _linear_interpolate(x: float, xs: Sequence[float], ys: Sequence[float], name: str) -> float:
    value = _real(x, name)
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Interpolation data are inconsistent")
    if value < xs[0] or value > xs[-1]:
        raise ValueError(f"{name} must be within [{xs[0]}, {xs[-1]}]; extrapolation is not permitted")
    for index, node in enumerate(xs):
        if math.isclose(value, node, rel_tol=0.0, abs_tol=1e-12):
            return float(ys[index])
    for index in range(len(xs) - 1):
        x0, x1 = float(xs[index]), float(xs[index + 1])
        if x0 < value < x1:
            y0, y1 = float(ys[index]), float(ys[index + 1])
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)
    raise RuntimeError("Interpolation interval was not found")


def bending_member_class_requirements(
    member_class: int,
    load_is_static: bool,
    is_crane_runway_beam: bool,
    is_bimetal_beam: bool,
) -> dict[str, Any]:
    """
    Summary:
        Classify the permitted strength-analysis route for a bending member under clause 8.1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.1
        Annex: None
        Equation/Table: Unnumbered class rules
        Audit ID: SP16-PROC-8.1-CLASS-ROUTING
        Normative status: normative

    Mathematical form:
        Explicit class and loading flags -> elastic or plastic route and applicability diagnostics.

    Parameters:
        member_class:
            Type: int
            Unit: dimensionless
            Meaning: Section class 1, 2, or 3 under clause 4.2.7.
            Valid range: 1, 2, or 3
            Source: engineering classification
        load_is_static:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the governing load is static.
            Valid range: true or false
            Source: load model
        is_crane_runway_beam:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the member is a crane-runway beam covered by the clause 8.1 class-1 rule.
            Valid range: true or false
            Source: structural system
        is_bimetal_beam:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the member is a bimetal beam.
            Valid range: true or false
            Source: section definition

    Returns:
        Type: dict[str, Any]
        Unit: mixed status data
        Meaning: Required route, permitted status, and diagnostic message.

    Assumptions:
        - The section class has already been established correctly.

    Sign convention:
        - No signed mechanical quantity is used.

    Unit convention:
        - All inputs are categorical or dimensionless.

    Applicability:
        - Initial routing for bending-member strength calculations.

    Limitations:
        - This function does not determine section class from geometry.

    Raises:
        ValueError: member_class is outside 1-3 or mutually inconsistent bimetal/class data are supplied.
        TypeError: Boolean flags are not bool values.

    Examples:
        >>> bending_member_class_requirements(1, False, False, False)["required_route"]
        'elastic'

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_bending_member_class_requirements
        Validation cases:
            - BEND-PROC-8.1

    Implementation notes:
        - Crane-runway beams are routed to class 1; bimetal beams are routed to class 2.
        - Defaults must be explicit in the input configuration.
    """
    if member_class not in (1, 2, 3):
        raise ValueError("member_class must be 1, 2, or 3")
    if not all(isinstance(v, bool) for v in (load_is_static, is_crane_runway_beam, is_bimetal_beam)):
        raise TypeError("routing flags must be bool values")
    if is_crane_runway_beam and member_class != 1:
        return {"permitted": False, "required_route": "elastic", "reason": "crane_runway_beam_requires_class_1"}
    if is_bimetal_beam and member_class != 2:
        return {"permitted": False, "required_route": "limited_plastic", "reason": "bimetal_beam_requires_class_2"}
    if member_class == 1:
        return {"permitted": True, "required_route": "elastic", "reason": "class_1"}
    return {
        "permitted": bool(load_is_static),
        "required_route": "limited_plastic" if member_class == 2 else "plastic_hinge",
        "reason": "static_load_required" if not load_is_static else f"class_{member_class}",
    }


def elastic_bending_utilization_eq41(
    bending_moment_n_mm: float,
    minimum_net_section_modulus_mm3: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the class-1 one-plane bending strength utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1
        Annex: None
        Equation/Table: Equation (41)
        Audit ID: SP16-EQ-041
        Normative status: normative

    Mathematical form:
        eta = |M|/(W_n,min*R_y*gamma_c).

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending-moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        minimum_net_section_modulus_mm3:
            Type: float
            Unit: mm3
            Meaning: Minimum net section modulus W_n,min.
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
            Source: applicable standard table or clause

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (41) utilization; pass when <= 1.

    Assumptions:
        - The member is class 1 and the correct net section modulus has been selected.

    Sign convention:
        - Moment is treated as a non-negative magnitude.

    Unit convention:
        - N, mm, and N/mm2 are used without conversion.

    Applicability:
        - Class-1 beams under one principal-plane bending.

    Limitations:
        - Stability and local-stability checks are separate.

    Raises:
        ValueError: A magnitude is negative or a denominator input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> elastic_bending_utilization_eq41(1e8, 1e6, 250, 1.0)
        0.4

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_41_normal_zero_and_units
        Validation cases:
            - BEND-EQ-041

    Implementation notes:
        - No automatic unit conversion is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(bending_moment_n_mm, "bending_moment_n_mm") / (
        _positive(minimum_net_section_modulus_mm3, "minimum_net_section_modulus_mm3")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def elastic_shear_utilization_eq42(
    shear_force_n: float,
    first_moment_area_mm3: float,
    gross_second_moment_area_mm4: float,
    web_thickness_mm: float,
    design_shear_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the class-1 beam shear-strength utilization at a selected web point.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1
        Annex: None
        Equation/Table: Equation (42)
        Audit ID: SP16-EQ-042
        Normative status: normative

    Mathematical form:
        eta = |Q|*S/(I*t_w*R_s*gamma_c).

    Parameters:
        shear_force_n:
            Type: float
            Unit: N
            Meaning: Design shear-force magnitude Q.
            Valid range: >= 0
            Source: structural analysis
        first_moment_area_mm3:
            Type: float
            Unit: mm3
            Meaning: First moment of area S at the checked point.
            Valid range: >= 0
            Source: section properties
        gross_second_moment_area_mm4:
            Type: float
            Unit: mm4
            Meaning: Gross second moment of area I.
            Valid range: > 0
            Source: section properties
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w at the checked point.
            Valid range: > 0
            Source: section geometry
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_s.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable standard rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (42) utilization.

    Assumptions:
        - S, I, and t_w refer to the same checked section and point.

    Sign convention:
        - Shear force and S are non-negative magnitudes.

    Unit convention:
        - N and mm units are used consistently.

    Applicability:
        - Elastic shear check for class-1 beams.

    Limitations:
        - At simple supports of simply supported beams, flange participation must be excluded externally.

    Raises:
        ValueError: Input domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> elastic_shear_utilization_eq42(100000, 200000, 2e8, 8, 145, 1.0)
        0.08620689655172414

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_42_normal_zero_and_units
        Validation cases:
            - BEND-EQ-042

    Implementation notes:
        - The bolt-hole factor from equation (45) is applied separately.
        - Defaults must be explicit in the input configuration.
    """
    q = _nonnegative(shear_force_n, "shear_force_n")
    s = _nonnegative(first_moment_area_mm3, "first_moment_area_mm3")
    return q * s / (
        _positive(gross_second_moment_area_mm4, "gross_second_moment_area_mm4")
        * _positive(web_thickness_mm, "web_thickness_mm")
        * _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def elastic_combined_normal_utilization_eq43(
    moment_x_n_mm: float,
    moment_y_n_mm: float,
    bimoment_n_mm2: float,
    net_inertia_x_mm4: float,
    net_inertia_y_mm4: float,
    net_sectorial_inertia_mm6: float,
    point_y_mm: float,
    point_x_mm: float,
    sectorial_coordinate_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate the absolute normalized normal stress from biaxial bending and bimoment at one section point.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1
        Annex: None
        Equation/Table: Equation (43)
        Audit ID: SP16-EQ-043
        Normative status: normative

    Mathematical form:
        eta = abs(M_x*y/I_xn + M_y*x/I_yn + B*omega/I_omega,n)/(R_y*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Signed moment about x.
            Valid range: finite
            Source: structural analysis
        moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Signed moment about y.
            Valid range: finite
            Source: structural analysis
        bimoment_n_mm2:
            Type: float
            Unit: N*mm2
            Meaning: Signed bimoment B.
            Valid range: finite
            Source: structural analysis
        net_inertia_x_mm4:
            Type: float
            Unit: mm4
            Meaning: Net second moment of area I_xn.
            Valid range: > 0
            Source: section properties
        net_inertia_y_mm4:
            Type: float
            Unit: mm4
            Meaning: Net second moment of area I_yn.
            Valid range: > 0
            Source: section properties
        net_sectorial_inertia_mm6:
            Type: float
            Unit: mm6
            Meaning: Net sectorial moment of inertia I_omega,n.
            Valid range: > 0
            Source: section properties
        point_y_mm:
            Type: float
            Unit: mm
            Meaning: Signed y coordinate of the checked point.
            Valid range: finite
            Source: section geometry
        point_x_mm:
            Type: float
            Unit: mm
            Meaning: Signed x coordinate of the checked point.
            Valid range: finite
            Source: section geometry
        sectorial_coordinate_mm2:
            Type: float
            Unit: mm2
            Meaning: Signed sectorial coordinate omega.
            Valid range: finite
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
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Absolute utilization at the selected point.

    Assumptions:
        - Coordinate, moment, and sectorial-coordinate signs follow one consistent local-axis convention.

    Sign convention:
        - Signed components are summed before the absolute strength comparison.

    Unit convention:
        - N and mm units are used consistently.

    Applicability:
        - Class-1 biaxial bending with optional constrained torsion.

    Limitations:
        - The caller must search all governing section points and both principal planes.

    Raises:
        ValueError: An inertia or resistance is non-positive, or any input is non-finite.
        TypeError: An input is not real.

    Examples:
        >>> round(elastic_combined_normal_utilization_eq43(1e8, 0, 0, 2e8, 1e8, 1e12, 200, 0, 0, 250, 1), 6)
        0.4

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_43_sign_and_units
        Validation cases:
            - BEND-EQ-043

    Implementation notes:
        - Absolute utilization is returned after signed stress assembly.
        - Defaults must be explicit in the input configuration.
    """
    normal_stress = (
        _real(moment_x_n_mm, "moment_x_n_mm") * _real(point_y_mm, "point_y_mm") / _positive(net_inertia_x_mm4, "net_inertia_x_mm4")
        + _real(moment_y_n_mm, "moment_y_n_mm") * _real(point_x_mm, "point_x_mm") / _positive(net_inertia_y_mm4, "net_inertia_y_mm4")
        + _real(bimoment_n_mm2, "bimoment_n_mm2") * _real(sectorial_coordinate_mm2, "sectorial_coordinate_mm2") / _positive(net_sectorial_inertia_mm6, "net_sectorial_inertia_mm6")
    )
    return abs(normal_stress) / (
        _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def elastic_web_equivalent_stress_checks_eq44(
    longitudinal_normal_stress_n_mm2: float,
    transverse_normal_stress_n_mm2: float,
    shear_stress_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    design_shear_resistance_n_mm2: float,
    working_condition_factor: float,
) -> dict[str, float | bool]:
    """
    Summary:
        Evaluate both class-1 web interaction conditions printed in equation (44).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1
        Annex: None
        Equation/Table: Equation (44)
        Audit ID: SP16-EQ-044
        Normative status: normative

    Mathematical form:
        eta_vm=0.87*sqrt(sigma_x^2-sigma_x*sigma_y+sigma_y^2+3*tau^2)/(R_y*gamma_c); eta_tau=|tau|/(R_s*gamma_c).

    Parameters:
        longitudinal_normal_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Signed sigma_x in the web mid-plane.
            Valid range: finite
            Source: stress recovery
        transverse_normal_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Signed sigma_y, including local stress where applicable.
            Valid range: finite
            Source: stress recovery
        shear_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Signed tau_xy at the same point.
            Valid range: finite
            Source: stress recovery
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_s.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: dict[str, float | bool]
        Unit: dimensionless ratios and booleans
        Meaning: Equivalent-stress and direct-shear utilizations and pass statuses.

    Assumptions:
        - All three stress components are evaluated at the same web point.

    Sign convention:
        - Normal stresses retain signs; shear sign does not affect the squared interaction.

    Unit convention:
        - All stresses use N/mm2.

    Applicability:
        - Class-1 web under simultaneous bending and shear.

    Limitations:
        - Does not recover stresses from forces and section geometry.

    Raises:
        ValueError: Resistance or working factor is non-positive, or a stress is non-finite.
        TypeError: An input is not real.

    Examples:
        >>> elastic_web_equivalent_stress_checks_eq44(100, 0, 0, 250, 145, 1)["equivalent_utilization"]
        0.348

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_44_normal_zero_and_sign
        Validation cases:
            - BEND-EQ-044

    Implementation notes:
        - Both inequalities are retained; neither is replaced by the other.
        - Defaults must be explicit in the input configuration.
    """
    sx = _real(longitudinal_normal_stress_n_mm2, "longitudinal_normal_stress_n_mm2")
    sy = _real(transverse_normal_stress_n_mm2, "transverse_normal_stress_n_mm2")
    tau = _real(shear_stress_n_mm2, "shear_stress_n_mm2")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    rs = _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
    gamma = _positive(working_condition_factor, "working_condition_factor")
    equivalent = 0.87 * math.sqrt(max(0.0, sx * sx - sx * sy + sy * sy + 3.0 * tau * tau)) / (ry * gamma)
    shear = abs(tau) / (rs * gamma)
    return {
        "equivalent_utilization": equivalent,
        "shear_utilization": shear,
        "equivalent_pass": equivalent <= 1.0,
        "shear_pass": shear <= 1.0,
        "governing_utilization": max(equivalent, shear),
    }


def bolt_hole_factor_eq45(hole_pitch_mm: float, hole_diameter_mm: float) -> float:
    """
    Summary:
        Calculate the bolt-hole amplification factor for web shear checks.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1
        Annex: None
        Equation/Table: Equation (45)
        Audit ID: SP16-EQ-045
        Normative status: normative

    Mathematical form:
        alpha = s/(s-d).

    Parameters:
        hole_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Hole pitch s in one vertical row.
            Valid range: > hole_diameter_mm
            Source: connection geometry
        hole_diameter_mm:
            Type: float
            Unit: mm
            Meaning: Hole diameter d.
            Valid range: >= 0 and < hole_pitch_mm
            Source: connection geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Multiplicative factor alpha.

    Assumptions:
        - Holes form one vertical row as covered by the clause.

    Sign convention:
        - Lengths are positive magnitudes.

    Unit convention:
        - s and d use the same length unit.

    Applicability:
        - Equation (42), equation (44) shear stress, and support checks (54)-(55) when the web is weakened by bolt holes.

    Limitations:
        - Staggered or nonstandard hole patterns are outside this scalar rule.

    Raises:
        ValueError: s is not positive, d is negative, or s <= d.
        TypeError: An input is not real.

    Examples:
        >>> bolt_hole_factor_eq45(100, 20)
        1.25

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_45_normal_boundary_and_units
        Validation cases:
            - BEND-EQ-045

    Implementation notes:
        - The function returns the factor only; application remains explicit.
        - Defaults must be explicit in the input configuration.
    """
    s = _positive(hole_pitch_mm, "hole_pitch_mm")
    d = _nonnegative(hole_diameter_mm, "hole_diameter_mm")
    if s <= d:
        raise ValueError("hole_pitch_mm must exceed hole_diameter_mm")
    return s / (s - d)


def local_web_compression_utilization_eq46(
    local_compressive_stress_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate local web-compression utilization under a concentrated load.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.2
        Annex: None
        Equation/Table: Equation (46)
        Audit ID: SP16-EQ-046
        Normative status: normative

    Mathematical form:
        eta = sigma_loc/(R_y*gamma_c).

    Parameters:
        local_compressive_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Local compressive stress sigma_loc.
            Valid range: >= 0
            Source: equation (47)
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
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (46) utilization.

    Assumptions:
        - The web is not stiffened at the local-load position.

    Sign convention:
        - Compression is supplied as a positive magnitude.

    Unit convention:
        - Stresses use N/mm2.

    Applicability:
        - Clause 8.2.2 local web strength check.

    Limitations:
        - Does not determine whether a stiffener is required by other clauses.

    Raises:
        ValueError: Input domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> local_web_compression_utilization_eq46(100, 250, 1)
        0.4

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_46_and_47
        Validation cases:
            - BEND-EQ-046

    Implementation notes:
        - No hidden sign conversion is performed.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(local_compressive_stress_n_mm2, "local_compressive_stress_n_mm2") / (
        _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def local_web_compression_stress_eq47(
    concentrated_force_n: float,
    effective_load_length_mm: float,
    web_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate local web stress from a concentrated force and effective distribution length.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.2
        Annex: None
        Equation/Table: Equation (47)
        Audit ID: SP16-EQ-047
        Normative status: normative

    Mathematical form:
        sigma_loc = F/(l_eff*t_w).

    Parameters:
        concentrated_force_n:
            Type: float
            Unit: N
            Meaning: Design concentrated-force magnitude F.
            Valid range: >= 0
            Source: load model
        effective_load_length_mm:
            Type: float
            Unit: mm
            Meaning: Effective distribution length l_eff.
            Valid range: > 0
            Source: equation (48) or (49)
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Local compressive stress sigma_loc.

    Assumptions:
        - Force is uniformly represented over l_eff*t_w by the standard rule.

    Sign convention:
        - Compression force is a positive magnitude.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Local web loading under clause 8.2.2.

    Limitations:
        - No load-spreading outside the standard formula is added.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> local_web_compression_stress_eq47(80000, 100, 8)
        100.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_46_and_47
        Validation cases:
            - BEND-EQ-047

    Implementation notes:
        - No unit conversion is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(concentrated_force_n, "concentrated_force_n") / (
        _positive(effective_load_length_mm, "effective_load_length_mm")
        * _positive(web_thickness_mm, "web_thickness_mm")
    )


def effective_load_length_eq48(
    bearing_width_mm: float,
    flange_and_weld_or_fillet_height_mm: float,
) -> float:
    """
    Summary:
        Calculate effective load distribution length for Figure 6 cases a and b.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.2
        Annex: None
        Equation/Table: Equation (48), Figure 6 a-b
        Audit ID: SP16-EQ-048
        Normative status: normative

    Mathematical form:
        l_eff = b + 2*h.

    Parameters:
        bearing_width_mm:
            Type: float
            Unit: mm
            Meaning: Bearing width b of the upper element.
            Valid range: >= 0
            Source: geometry
        flange_and_weld_or_fillet_height_mm:
            Type: float
            Unit: mm
            Meaning: Dimension h defined for welded or rolled lower beams.
            Valid range: >= 0
            Source: verified Figure 6 geometry

    Returns:
        Type: float
        Unit: mm
        Meaning: Effective load length l_eff.

    Assumptions:
        - Figure 6 case a or b is applicable.

    Sign convention:
        - Dimensions are non-negative magnitudes.

    Unit convention:
        - Both dimensions use mm.

    Applicability:
        - Welded or rolled lower beams under Figure 6 a-b.

    Limitations:
        - Crane-wheel case c uses equation (49), not this function.

    Raises:
        ValueError: A dimension is negative or the resulting length is zero.
        TypeError: An input is not real.

    Examples:
        >>> effective_load_length_eq48(100, 20)
        140.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_48_and_49
        Validation cases:
            - BEND-EQ-048

    Implementation notes:
        - The geometric meaning of h is retained in the parameter name.
        - Defaults must be explicit in the input configuration.
    """
    result = _nonnegative(bearing_width_mm, "bearing_width_mm") + 2.0 * _nonnegative(
        flange_and_weld_or_fillet_height_mm, "flange_and_weld_or_fillet_height_mm"
    )
    if result <= 0.0:
        raise ValueError("effective load length must be greater than zero")
    return result


def effective_load_length_crane_eq49(
    distribution_coefficient_psi: float,
    flange_and_rail_inertia_mm4: float,
    web_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate effective load distribution length for the crane-wheel case in Figure 6 c.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.2
        Annex: None
        Equation/Table: Equation (49), Figure 6 c
        Audit ID: SP16-EQ-049
        Normative status: normative

    Mathematical form:
        l_eff = psi*cuberoot(I_1f/t_w).

    Parameters:
        distribution_coefficient_psi:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient psi, typically 3.25 or 4.5 for the listed connection cases.
            Valid range: > 0
            Source: clause 8.2.2
        flange_and_rail_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: I_1f for the flange/rail system as defined by the clause.
            Valid range: > 0
            Source: section and rail properties
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: mm
        Meaning: Effective load length l_eff.

    Assumptions:
        - The chosen I_1f representation matches the rail attachment condition.

    Sign convention:
        - All inputs are positive magnitudes.

    Unit convention:
        - I_1f uses mm4 and t_w uses mm.

    Applicability:
        - Crane-wheel load distribution in Figure 6 c.

    Limitations:
        - psi is not inferred from connection geometry.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> round(effective_load_length_crane_eq49(3.25, 8e6, 8), 6)
        325.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_48_and_49
        Validation cases:
            - BEND-EQ-049

    Implementation notes:
        - The real cube root is positive because the domain is positive.
        - Defaults must be explicit in the input configuration.
    """
    psi = _positive(distribution_coefficient_psi, "distribution_coefficient_psi")
    inertia = _positive(flange_and_rail_inertia_mm4, "flange_and_rail_inertia_mm4")
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    return psi * (inertia / thickness) ** (1.0 / 3.0)


def annex_e1_plastic_coefficient_catalog() -> dict[str, Any]:
    """
    Summary:
        Return a detached copy of the audited Annex E Table E.1 coefficient data.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3 and Annex E
        Annex: E
        Equation/Table: Table E.1
        Audit ID: SP16-TBL-Е-1
        Normative status: normative

    Mathematical form:
        Section type and A_f/A_w nodes -> c_x, c_y, and n data.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: No runtime input.
            Valid range: not applicable
            Source: bundled audited JSON

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Detached catalogue of Table E.1.

    Assumptions:
        - Visual section-type selection is performed by the engineer.

    Sign convention:
        - Ratios and coefficients are positive.

    Unit convention:
        - All table variables are dimensionless.

    Applicability:
        - Plastic-strength coefficients used by clauses 8.2.3-8.2.8.

    Limitations:
        - Section diagrams are represented by stable type identifiers rather than reproduced images.

    Raises:
        None: Bundled data are loaded at import.

    Examples:
        >>> annex_e1_plastic_coefficient_catalog()["table_number"]
        'Е.1'

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_annex_e1_catalogue_and_exact_nodes
        Validation cases:
            - BEND-TBL-E1

    Implementation notes:
        - A JSON round trip prevents mutation of module state.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_E1, ensure_ascii=False))


def annex_e1_base_coefficients(
    section_type: str,
    flange_to_web_area_ratio: float | None,
    minor_axis_moment_is_zero: bool,
) -> dict[str, float]:
    """
    Summary:
        Interpolate uncapped c_x and c_y and select n from Annex E Table E.1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3 and Annex E
        Annex: E
        Equation/Table: Table E.1 and footnote
        Audit ID: SP16-PROC-8.2.3-ANNEX-E1-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Piecewise linear interpolation in A_f/A_w; constant rows remain constant; n follows the printed footnote.

    Parameters:
        section_type:
            Type: str
            Unit: dimensionless
            Meaning: Stable table identifier 1,2,3,4,5a,5b,6,7,8a,8b,9a, or 9b.
            Valid range: one bundled identifier
            Source: engineer from Table E.1 diagram
        flange_to_web_area_ratio:
            Type: float or None
            Unit: dimensionless
            Meaning: A_f/A_w for rows with ratio nodes; None for constant rows.
            Valid range: inside the printed node range
            Source: section properties
        minor_axis_moment_is_zero:
            Type: bool
            Unit: dimensionless
            Meaning: Whether M_y equals zero for selecting n.
            Valid range: true or false
            Source: force result

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: Uncapped c_x, c_y, and n.

    Assumptions:
        - section_type is selected from the printed section diagram.

    Sign convention:
        - Area ratio and coefficients are positive magnitudes.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table E.1 coefficient lookup before the load-factor cap.

    Limitations:
        - Extrapolation outside printed ratio ranges is prohibited.

    Raises:
        ValueError: Identifier, ratio, or None usage is invalid.
        TypeError: minor_axis_moment_is_zero is not bool or a ratio is not real.

    Examples:
        >>> annex_e1_base_coefficients('1', 0.5, True)
        {'c_x': 1.12, 'c_y': 1.47, 'n': 1.5}

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_annex_e1_interpolation_and_footnote
        Validation cases:
            - BEND-PROC-E1-INTERP

    Implementation notes:
        - The printed rule for M_y != 0 is implemented exactly, including the two type-5 exceptions.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(section_type, str) or section_type not in _TABLE_E1["section_types"]:
        raise ValueError(f"Unsupported Annex E Table E.1 section_type: {section_type}")
    if not isinstance(minor_axis_moment_is_zero, bool):
        raise TypeError("minor_axis_moment_is_zero must be bool")
    row = _TABLE_E1["section_types"][section_type]
    nodes = row.get("ratio_nodes")
    if nodes is None:
        if flange_to_web_area_ratio is not None:
            raise ValueError(f"section_type {section_type} is a constant row and requires flange_to_web_area_ratio=None")
        c_x = float(row["c_x_constant"])
        c_y = float(row["c_y_constant"])
    else:
        if flange_to_web_area_ratio is None:
            raise ValueError(f"section_type {section_type} requires flange_to_web_area_ratio")
        ratio = _positive(flange_to_web_area_ratio, "flange_to_web_area_ratio")
        c_x = _linear_interpolate(ratio, nodes, row["c_x"], "flange_to_web_area_ratio")
        c_y = _linear_interpolate(ratio, nodes, row["c_y"], "flange_to_web_area_ratio")
    if minor_axis_moment_is_zero:
        n = float(row["n_when_my_zero"])
    elif section_type == "5a":
        n = 2.0
    elif section_type == "5b":
        n = 3.0
    else:
        n = 1.5
    return {"c_x": c_x, "c_y": c_y, "n": n}


def apply_annex_e1_load_factor_cap(coefficient: float, equivalent_load_safety_factor: float) -> float:
    """
    Summary:
        Apply the Annex E Table E.1 note limiting c_x and c_y to 1.15 times gamma_f.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Annex E note 2
        Annex: E
        Equation/Table: Table E.1 note 2
        Audit ID: SP16-PROC-8.2.3-ANNEX-E1-CAP
        Normative status: normative

    Mathematical form:
        c_design = min(c_table, 1.15*gamma_f).

    Parameters:
        coefficient:
            Type: float
            Unit: dimensionless
            Meaning: Interpolated table coefficient c_x or c_y.
            Valid range: > 0
            Source: Table E.1
        equivalent_load_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_f defined by the note as design-to-normative equivalent load ratio.
            Valid range: > 0
            Source: load model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped coefficient.

    Assumptions:
        - gamma_f corresponds to the equivalent bending-moment load used in the check.

    Sign convention:
        - Inputs are positive magnitudes.

    Unit convention:
        - Dimensionless.

    Applicability:
        - c_x and c_y from Annex E Table E.1.

    Limitations:
        - The function does not derive gamma_f from load combinations.

    Raises:
        ValueError: An input is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> apply_annex_e1_load_factor_cap(1.47, 1.1)
        1.265

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_annex_e1_cap
        Validation cases:
            - BEND-PROC-E1-CAP

    Implementation notes:
        - The cap is explicit and never silently omitted by the combined lookup.
        - Defaults must be explicit in the input configuration.
    """
    return min(
        _positive(coefficient, "coefficient"),
        1.15 * _positive(equivalent_load_safety_factor, "equivalent_load_safety_factor"),
    )


def annex_e1_design_coefficients(
    section_type: str,
    flange_to_web_area_ratio: float | None,
    minor_axis_moment_is_zero: bool,
    equivalent_load_safety_factor: float,
) -> dict[str, float]:
    """
    Summary:
        Return Table E.1 coefficients with interpolation, n selection, and the mandatory load-factor cap.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3 and Annex E
        Annex: E
        Equation/Table: Table E.1 and notes
        Audit ID: SP16-PROC-8.2.3-ANNEX-E1-INTERPOLATION; SP16-PROC-8.2.3-ANNEX-E1-CAP
        Normative status: normative

    Mathematical form:
        Base lookup/interpolation followed by c_x,c_y=min(c,1.15*gamma_f).

    Parameters:
        section_type:
            Type: str
            Unit: dimensionless
            Meaning: Table E.1 section identifier.
            Valid range: bundled identifier
            Source: section classification
        flange_to_web_area_ratio:
            Type: float or None
            Unit: dimensionless
            Meaning: A_f/A_w or None for constant rows.
            Valid range: row-specific
            Source: section properties
        minor_axis_moment_is_zero:
            Type: bool
            Unit: dimensionless
            Meaning: M_y zero flag for n.
            Valid range: true or false
            Source: force result
        equivalent_load_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_f for the note-2 cap.
            Valid range: > 0
            Source: load model

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: Design c_x, c_y, n, plus uncapped coefficients.

    Assumptions:
        - Table row and gamma_f are applicable to the same load case.

    Sign convention:
        - All numerical inputs are positive magnitudes.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Plastic bending checks requiring Table E.1.

    Limitations:
        - Section type is not inferred.

    Raises:
        ValueError: Lookup or factor domain is invalid.
        TypeError: Input types are invalid.

    Examples:
        >>> annex_e1_design_coefficients('1', 0.5, True, 2.0)['c_x']
        1.12

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_annex_e1_design_coefficients
        Validation cases:
            - BEND-PROC-E1-DESIGN

    Implementation notes:
        - Uncapped values remain visible for traceability.
        - Defaults must be explicit in the input configuration.
    """
    base = annex_e1_base_coefficients(section_type, flange_to_web_area_ratio, minor_axis_moment_is_zero)
    return {
        "c_x": apply_annex_e1_load_factor_cap(base["c_x"], equivalent_load_safety_factor),
        "c_y": apply_annex_e1_load_factor_cap(base["c_y"], equivalent_load_safety_factor),
        "n": base["n"],
        "uncapped_c_x": base["c_x"],
        "uncapped_c_y": base["c_y"],
    }


def plastic_bending_applicability(
    member_class: int,
    section_family: str,
    normative_yield_resistance_n_mm2: float,
    shear_stress_x_n_mm2: float,
    design_shear_resistance_n_mm2: float,
    required_clause_checks_confirmed: bool,
    is_support_section: bool,
) -> dict[str, Any]:
    """
    Summary:
        Check explicit applicability gates for the clause 8.2.3 plastic-strength route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Applicability text preceding equations (50)-(52)
        Audit ID: SP16-PROC-8.2.3-PLASTIC-APPLICABILITY
        Normative status: normative

    Mathematical form:
        Boolean conjunction of class, section family, R_yn<=440, tau_x<=0.9R_s, non-support, and referenced checks.

    Parameters:
        member_class:
            Type: int
            Unit: dimensionless
            Meaning: Section class.
            Valid range: 2 or 3
            Source: clause 4.2.7
        section_family:
            Type: str
            Unit: dimensionless
            Meaning: i_section or box_section.
            Valid range: i_section, box_section
            Source: section geometry
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance R_yn.
            Valid range: > 0
            Source: material data
        shear_stress_x_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Shear stress tau_x magnitude.
            Valid range: >= 0
            Source: force and section properties
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_s.
            Valid range: > 0
            Source: clause 6.1
        required_clause_checks_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of clauses 8.4.6, 8.5.8, 8.5.9, and 8.5.18.
            Valid range: true or false
            Source: engineering workflow
        is_support_section:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the checked section is a support section.
            Valid range: true or false
            Source: model topology

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Permitted flag and failed gates.

    Assumptions:
        - The caller has performed the referenced stability checks.

    Sign convention:
        - Shear stress is a non-negative magnitude.

    Unit convention:
        - Stress values use N/mm2.

    Applicability:
        - Routing to equations (50)-(52).

    Limitations:
        - Does not itself calculate the referenced local/global stability checks.

    Raises:
        ValueError: Class, family, or numeric domain is invalid.
        TypeError: Confirmation flags are not bool.

    Examples:
        >>> plastic_bending_applicability(2, 'i_section', 355, 100, 145, True, False)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_plastic_bending_applicability
        Validation cases:
            - BEND-PROC-8.2.3

    Implementation notes:
        - Support sections are routed to equations (54)-(55).
        - Defaults must be explicit in the input configuration.
    """
    if member_class not in (2, 3):
        raise ValueError("member_class must be 2 or 3")
    if section_family not in {"i_section", "box_section"}:
        raise ValueError("section_family must be i_section or box_section")
    if not isinstance(required_clause_checks_confirmed, bool) or not isinstance(is_support_section, bool):
        raise TypeError("applicability flags must be bool")
    ryn = _positive(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2")
    tau = _nonnegative(shear_stress_x_n_mm2, "shear_stress_x_n_mm2")
    rs = _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
    failed: list[str] = []
    if ryn > 440.0:
        failed.append("normative_yield_resistance_above_440")
    if tau > 0.9 * rs:
        failed.append("shear_stress_above_0.9_Rs")
    if not required_clause_checks_confirmed:
        failed.append("referenced_stability_checks_not_confirmed")
    if is_support_section:
        failed.append("support_section_requires_equations_54_55")
    return {"permitted": not failed, "failed_gates": failed}


def plastic_shear_reduction_factor_eq52(
    shear_stress_x_n_mm2: float,
    design_shear_resistance_n_mm2: float,
    flange_to_web_area_ratio: float,
) -> float:
    """
    Summary:
        Calculate the shear-reduction factor beta for plastic bending strength.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (52)
        Audit ID: SP16-EQ-052
        Normative status: normative

    Mathematical form:
        beta=1 for tau_x<=0.5R_s; otherwise beta=1-[0.20/(alpha_f+0.25)]*(tau_x/R_s)^4 up to 0.9R_s.

    Parameters:
        shear_stress_x_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: tau_x magnitude.
            Valid range: 0 <= tau_x <= 0.9R_s
            Source: Q_x/A_w
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_s.
            Valid range: > 0
            Source: clause 6.1
        flange_to_web_area_ratio:
            Type: float
            Unit: dimensionless
            Meaning: alpha_f=A_f/A_w using the clause definition.
            Valid range: >= 0
            Source: section properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: beta.

    Assumptions:
        - For asymmetric sections A_f is the smaller flange area; for boxes A_w is both webs combined.

    Sign convention:
        - Shear stress is a positive magnitude.

    Unit convention:
        - tau_x and R_s use the same stress unit.

    Applicability:
        - Equations (50), (51), and (53).

    Limitations:
        - Values above 0.9R_s are rejected rather than extrapolated.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> plastic_shear_reduction_factor_eq52(50, 100, 1)
        1.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_52_branches_and_limits
        Validation cases:
            - BEND-EQ-052

    Implementation notes:
        - The branch boundary at 0.5R_s is included in beta=1.
        - Defaults must be explicit in the input configuration.
    """
    tau = _nonnegative(shear_stress_x_n_mm2, "shear_stress_x_n_mm2")
    rs = _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
    alpha = _nonnegative(flange_to_web_area_ratio, "flange_to_web_area_ratio")
    if tau > 0.9 * rs + 1e-12:
        raise ValueError("equation (52) requires shear_stress_x_n_mm2 <= 0.9*design_shear_resistance_n_mm2")
    if tau <= 0.5 * rs:
        return 1.0
    return 1.0 - 0.20 / (alpha + 0.25) * (tau / rs) ** 4


def plastic_bending_utilization_eq50(
    moment_x_n_mm: float,
    coefficient_c_x: float,
    shear_reduction_beta: float,
    minimum_net_section_modulus_x_mm3: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate one-plane plastic bending utilization for class-2 or class-3 beams.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (50)
        Audit ID: SP16-EQ-050
        Normative status: normative

    Mathematical form:
        eta=|M_x|/(c_x*beta*W_xn,min*R_y*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-axis bending moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        coefficient_c_x:
            Type: float
            Unit: dimensionless
            Meaning: c_x from Annex E Table E.1 or permitted reduced value.
            Valid range: > 0
            Source: table lookup
        shear_reduction_beta:
            Type: float
            Unit: dimensionless
            Meaning: beta from equation (52).
            Valid range: > 0
            Source: equation (52)
        minimum_net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn,min.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (50) utilization.

    Assumptions:
        - Clause 8.2.3 applicability gates are satisfied.

    Sign convention:
        - Moment is a non-negative magnitude.

    Unit convention:
        - N and mm are used consistently.

    Applicability:
        - Major-axis plastic bending of I or box sections.

    Limitations:
        - Does not select c_x or beta automatically.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> plastic_bending_utilization_eq50(1e8, 1.2, 1, 1e6, 250, 1)
        0.3333333333333333

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_50_and_51
        Validation cases:
            - BEND-EQ-050

    Implementation notes:
        - Coefficient reduction for minimum-section sizing remains explicit.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(moment_x_n_mm, "moment_x_n_mm") / (
        _positive(coefficient_c_x, "coefficient_c_x")
        * _positive(shear_reduction_beta, "shear_reduction_beta")
        * _positive(minimum_net_section_modulus_x_mm3, "minimum_net_section_modulus_x_mm3")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def plastic_biaxial_bending_utilization_eq51(
    moment_x_n_mm: float,
    moment_y_n_mm: float,
    coefficient_c_x: float,
    coefficient_c_y: float,
    shear_reduction_beta: float,
    minimum_net_section_modulus_x_mm3: float,
    minimum_net_section_modulus_y_mm3: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate biaxial plastic bending utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (51)
        Audit ID: SP16-EQ-051
        Normative status: normative

    Mathematical form:
        eta=|M_x|/(c_x*beta*W_xn,min*R_y*gamma_c)+|M_y|/(c_y*W_yn,min*R_y*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Minor-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        coefficient_c_x:
            Type: float
            Unit: dimensionless
            Meaning: c_x.
            Valid range: > 0
            Source: Table E.1
        coefficient_c_y:
            Type: float
            Unit: dimensionless
            Meaning: c_y.
            Valid range: > 0
            Source: Table E.1
        shear_reduction_beta:
            Type: float
            Unit: dimensionless
            Meaning: beta affecting the major-axis term.
            Valid range: > 0
            Source: equation (52)
        minimum_net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn,min.
            Valid range: > 0
            Source: section properties
        minimum_net_section_modulus_y_mm3:
            Type: float
            Unit: mm3
            Meaning: W_yn,min.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (51) utilization.

    Assumptions:
        - tau_y <= 0.5R_s and other clause 8.2.3 conditions are checked externally.

    Sign convention:
        - Both moments are non-negative magnitudes.

    Unit convention:
        - N and mm are used.

    Applicability:
        - Biaxial plastic bending under clause 8.2.3.

    Limitations:
        - Does not enforce tau_y in this scalar function.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> plastic_biaxial_bending_utilization_eq51(1e8, 2e7, 1.2, 1.2, 1, 1e6, 5e5, 250, 1)
        0.4666666666666667

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_50_and_51
        Validation cases:
            - BEND-EQ-051

    Implementation notes:
        - Major-axis beta is not applied to the minor-axis term, matching the printed formula.
        - Defaults must be explicit in the input configuration.
    """
    return plastic_bending_utilization_eq50(
        moment_x_n_mm,
        coefficient_c_x,
        shear_reduction_beta,
        minimum_net_section_modulus_x_mm3,
        design_yield_resistance_n_mm2,
        working_condition_factor,
    ) + _nonnegative(moment_y_n_mm, "moment_y_n_mm") / (
        _positive(coefficient_c_y, "coefficient_c_y")
        * _positive(minimum_net_section_modulus_y_mm3, "minimum_net_section_modulus_y_mm3")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def table_10a_constrained_torsion_catalog() -> dict[str, Any]:
    """
    Summary:
        Return a detached copy of Table 10a constrained-torsion coefficient nodes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Table 10a
        Audit ID: SP16-TBL-10а
        Normative status: normative

    Mathematical form:
        Major-axis normalized ratio nodes -> c_omega values.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: No runtime input.
            Valid range: not applicable
            Source: bundled audited JSON

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Detached Table 10a catalogue.

    Assumptions:
        - The independent ratio is evaluated without beta as printed in the table header.

    Sign convention:
        - Ratio uses moment magnitude.

    Unit convention:
        - Ratio and c_omega are dimensionless.

    Applicability:
        - Symmetric I-sections under constrained torsion, equation (53).

    Limitations:
        - Extrapolation above 0.99 is not defined.

    Raises:
        None: Bundled data are loaded at import.

    Examples:
        >>> table_10a_constrained_torsion_catalog()["nodes"][0]["c_omega"]
        1.47

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_table_10a_catalogue_and_nodes
        Validation cases:
            - BEND-TBL-10A

    Implementation notes:
        - Data are returned by deep copy.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_10A, ensure_ascii=False))


def constrained_torsion_coefficient_table_10a(major_axis_normalized_ratio: float) -> float:
    """
    Summary:
        Interpolate c_omega from Table 10a.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Table 10a
        Audit ID: SP16-PROC-8.2.3-TABLE-10A-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Linear interpolation of c_omega versus M_x/(c_x*W_xn,min*R_y*gamma_c).

    Parameters:
        major_axis_normalized_ratio:
            Type: float
            Unit: dimensionless
            Meaning: Table-header independent ratio.
            Valid range: 0 <= value <= 0.99
            Source: equation (50) denominator without beta

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Interpolated c_omega.

    Assumptions:
        - Symmetric I-section and constrained-torsion route apply.

    Sign convention:
        - Ratio is a non-negative magnitude.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (53).

    Limitations:
        - No extrapolation beyond printed nodes.

    Raises:
        ValueError: Ratio is outside 0-0.99.
        TypeError: Ratio is not real.

    Examples:
        >>> constrained_torsion_coefficient_table_10a(0.15)
        1.7405

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_table_10a_interpolation_and_bounds
        Validation cases:
            - BEND-PROC-10A-INTERP

    Implementation notes:
        - Exact printed nodes are returned without interpolation drift.
        - Defaults must be explicit in the input configuration.
    """
    nodes = _TABLE_10A["nodes"]
    xs = [float(item["ratio"]) for item in nodes]
    ys = [float(item["c_omega"]) for item in nodes]
    return _linear_interpolate(major_axis_normalized_ratio, xs, ys, "major_axis_normalized_ratio")


def constrained_torsion_utilization_eq53(
    moment_x_n_mm: float,
    bimoment_n_mm2: float,
    coefficient_c_x: float,
    shear_reduction_beta: float,
    minimum_net_section_modulus_x_mm3: float,
    coefficient_c_omega: float,
    minimum_net_sectorial_section_modulus_mm4: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate plastic major-axis bending plus constrained-torsion utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (53), Table 10a
        Audit ID: SP16-EQ-053
        Normative status: normative

    Mathematical form:
        eta=|M_x|/(c_x*beta*W_xn,min*R_y*gamma_c)+|B|/(c_omega*W_omega,n,min*R_y*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        bimoment_n_mm2:
            Type: float
            Unit: N*mm2
            Meaning: Bimoment magnitude B.
            Valid range: >= 0
            Source: structural analysis
        coefficient_c_x:
            Type: float
            Unit: dimensionless
            Meaning: c_x.
            Valid range: > 0
            Source: Table E.1
        shear_reduction_beta:
            Type: float
            Unit: dimensionless
            Meaning: beta.
            Valid range: > 0
            Source: equation (52)
        minimum_net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn,min.
            Valid range: > 0
            Source: section properties
        coefficient_c_omega:
            Type: float
            Unit: dimensionless
            Meaning: c_omega from Table 10a.
            Valid range: > 0
            Source: Table 10a
        minimum_net_sectorial_section_modulus_mm4:
            Type: float
            Unit: mm4
            Meaning: W_omega,n,min.
            Valid range: > 0
            Source: section properties
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (53) utilization.

    Assumptions:
        - The section is a symmetric I-section with I_x>I_y.

    Sign convention:
        - M_x and B are non-negative magnitudes.

    Unit convention:
        - N and mm units are used.

    Applicability:
        - Plastic strength under major-axis bending and constrained torsion.

    Limitations:
        - c_omega lookup is external to this scalar function.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> constrained_torsion_utilization_eq53(1e8, 1e10, 1.2, 1, 1e6, 2, 1e8, 250, 1)
        0.5333333333333333

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_53
        Validation cases:
            - BEND-EQ-053

    Implementation notes:
        - Bimoment modulus has mm4 so B/W_omega has stress units.
        - Defaults must be explicit in the input configuration.
    """
    return plastic_bending_utilization_eq50(
        moment_x_n_mm,
        coefficient_c_x,
        shear_reduction_beta,
        minimum_net_section_modulus_x_mm3,
        design_yield_resistance_n_mm2,
        working_condition_factor,
    ) + _nonnegative(bimoment_n_mm2, "bimoment_n_mm2") / (
        _positive(coefficient_c_omega, "coefficient_c_omega")
        * _positive(minimum_net_sectorial_section_modulus_mm4, "minimum_net_sectorial_section_modulus_mm4")
        * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def pure_bending_modified_coefficients(coefficient_c_x: float, coefficient_c_y: float) -> dict[str, float]:
    """
    Summary:
        Calculate the modified c_xm and c_ym coefficients for a pure-bending zone.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Unnumbered formulas following Table 10a
        Audit ID: SP16-PROC-8.2.3-PURE-BENDING-COEFFICIENTS
        Normative status: normative

    Mathematical form:
        c_xm=0.5*(1+c_x); c_ym=0.5*(1+c_y).

    Parameters:
        coefficient_c_x:
            Type: float
            Unit: dimensionless
            Meaning: c_x from Table E.1.
            Valid range: > 0
            Source: table lookup
        coefficient_c_y:
            Type: float
            Unit: dimensionless
            Meaning: c_y from Table E.1.
            Valid range: > 0
            Source: table lookup

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: c_xm and c_ym.

    Assumptions:
        - The checked section lies in a pure-bending zone.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equations (50)-(51) in a pure-bending zone.

    Limitations:
        - Does not identify the pure-bending zone from force diagrams.

    Raises:
        ValueError: A coefficient is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> pure_bending_modified_coefficients(1.2, 1.4)
        {'c_xm': 1.1, 'c_ym': 1.2}

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_pure_bending_modified_coefficients
        Validation cases:
            - BEND-PROC-PURE

    Implementation notes:
        - beta is set to 1 separately as required by the clause.
        - Defaults must be explicit in the input configuration.
    """
    return {
        "c_xm": 0.5 * (1.0 + _positive(coefficient_c_x, "coefficient_c_x")),
        "c_ym": 0.5 * (1.0 + _positive(coefficient_c_y, "coefficient_c_y")),
    }


def support_shear_x_utilization_eq54(
    shear_force_x_n: float,
    web_area_mm2: float,
    design_shear_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate support-section x-direction shear utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (54)
        Audit ID: SP16-EQ-054
        Normative status: normative

    Mathematical form:
        eta=|Q_x|/(A_w*R_s*gamma_c).

    Parameters:
        shear_force_x_n:
            Type: float
            Unit: N
            Meaning: Q_x magnitude.
            Valid range: >= 0
            Source: structural analysis
        web_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Web area A_w.
            Valid range: > 0
            Source: section properties
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_s.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (54) utilization before any equation (45) factor.

    Assumptions:
        - Support section has M_x=M_y=0 for this route.

    Sign convention:
        - Q_x is a magnitude.

    Unit convention:
        - N and mm2 are used.

    Applicability:
        - Support sections under clause 8.2.3.

    Limitations:
        - Bolt-hole amplification is separate.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> support_shear_x_utilization_eq54(100000, 1000, 100, 1)
        1.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_54_and_55
        Validation cases:
            - BEND-EQ-054

    Implementation notes:
        - The formula uses web area directly.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(shear_force_x_n, "shear_force_x_n") / (
        _positive(web_area_mm2, "web_area_mm2")
        * _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def support_shear_y_utilization_eq55(
    shear_force_y_n: float,
    one_flange_area_mm2: float,
    design_shear_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate support-section y-direction shear utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.3
        Annex: None
        Equation/Table: Equation (55)
        Audit ID: SP16-EQ-055
        Normative status: normative

    Mathematical form:
        eta=|Q_y|/(2*A_f*R_s*gamma_c).

    Parameters:
        shear_force_y_n:
            Type: float
            Unit: N
            Meaning: Q_y magnitude.
            Valid range: >= 0
            Source: structural analysis
        one_flange_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_f of one flange.
            Valid range: > 0
            Source: section properties
        design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_s.
            Valid range: > 0
            Source: clause 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (55) utilization before any equation (45) factor.

    Assumptions:
        - Two flanges share Q_y as represented by the formula.

    Sign convention:
        - Q_y is a magnitude.

    Unit convention:
        - N and mm2 are used.

    Applicability:
        - Support sections under clause 8.2.3.

    Limitations:
        - Bolt-hole amplification is separate.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> support_shear_y_utilization_eq55(100000, 500, 100, 1)
        1.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_54_and_55
        Validation cases:
            - BEND-EQ-055

    Implementation notes:
        - A_f is one flange area, matching the printed denominator 2A_f.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(shear_force_y_n, "shear_force_y_n") / (
        2.0
        * _positive(one_flange_area_mm2, "one_flange_area_mm2")
        * _positive(design_shear_resistance_n_mm2, "design_shear_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def variable_section_plastic_routing(
    is_most_unfavourable_moment_shear_section: bool,
    reduced_coefficients_explicitly_selected: bool,
) -> dict[str, str]:
    """
    Summary:
        Route a variable-section beam section under clause 8.2.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.4
        Annex: None
        Equation/Table: Procedure referring to equations (50)-(51)
        Audit ID: SP16-PROC-8.2.4-VARIABLE-SECTION-ROUTING
        Normative status: normative

    Mathematical form:
        Governing M-Q section -> full clause 8.2.3 route; other sections -> reduced c coefficients or elastic route.

    Parameters:
        is_most_unfavourable_moment_shear_section:
            Type: bool
            Unit: dimensionless
            Meaning: Whether this is the single governing M-Q section.
            Valid range: true or false
            Source: force-envelope assessment
        reduced_coefficients_explicitly_selected:
            Type: bool
            Unit: dimensionless
            Meaning: Whether reduced c_x/c_y values were explicitly selected for a non-governing section.
            Valid range: true or false
            Source: engineering choice

    Returns:
        Type: dict[str, str]
        Unit: status data
        Meaning: Required calculation route.

    Assumptions:
        - The governing section was determined from the complete beam force envelope.

    Sign convention:
        - No signed quantity is used.

    Unit convention:
        - Categorical.

    Applicability:
        - Variable-section beams considered with plastic deformation.

    Limitations:
        - Does not identify the governing section automatically.

    Raises:
        TypeError: Inputs are not bool.

    Examples:
        >>> variable_section_plastic_routing(True, False)["route"]
        'full_clause_8_2_3'

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_variable_section_routing
        Validation cases:
            - BEND-PROC-8.2.4

    Implementation notes:
        - Non-governing sections default to the elastic route unless reduced coefficients were explicitly selected.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(is_most_unfavourable_moment_shear_section, bool) or not isinstance(
        reduced_coefficients_explicitly_selected, bool
    ):
        raise TypeError("routing inputs must be bool")
    if is_most_unfavourable_moment_shear_section:
        return {"route": "full_clause_8_2_3"}
    return {"route": "reduced_plastic_coefficients" if reduced_coefficients_explicitly_selected else "elastic_clause_8_2_1"}


def continuous_beam_partial_redistribution_applicability(
    adjacent_span_1_mm: float,
    adjacent_span_2_mm: float,
    constant_section: bool,
    doubly_symmetric_section: bool,
    required_clause_checks_confirmed: bool,
) -> dict[str, Any]:
    """
    Summary:
        Check clause 8.2.5 applicability for partial moment redistribution.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.5
        Annex: None
        Equation/Table: Applicability text and equations (56)-(58)
        Audit ID: SP16-PROC-8.2.5-CONTINUOUS-BEAM-APPLICABILITY
        Normative status: normative

    Mathematical form:
        Relative adjacent-span difference <=20% plus constant doubly symmetric section and referenced checks.

    Parameters:
        adjacent_span_1_mm:
            Type: float
            Unit: mm
            Meaning: First adjacent span.
            Valid range: > 0
            Source: beam geometry
        adjacent_span_2_mm:
            Type: float
            Unit: mm
            Meaning: Second adjacent span.
            Valid range: > 0
            Source: beam geometry
        constant_section:
            Type: bool
            Unit: dimensionless
            Meaning: Constant-section confirmation.
            Valid range: true or false
            Source: model definition
        doubly_symmetric_section:
            Type: bool
            Unit: dimensionless
            Meaning: Two-axis symmetry confirmation.
            Valid range: true or false
            Source: section geometry
        required_clause_checks_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of 8.4.6, 8.5.8, 8.5.9, and 8.5.18.
            Valid range: true or false
            Source: engineering workflow

    Returns:
        Type: dict[str, Any]
        Unit: status and dimensionless ratio
        Meaning: Permitted flag, span difference, and failed gates.

    Assumptions:
        - The two supplied spans are the relevant adjacent spans.

    Sign convention:
        - Lengths are positive.

    Unit convention:
        - Both spans use the same length unit.

    Applicability:
        - Continuous and fixed-ended I or box beams under clause 8.2.5.

    Limitations:
        - End-restraint category is handled by the effective-moment functions.

    Raises:
        ValueError: A span is non-positive.
        TypeError: Flags are not bool.

    Examples:
        >>> continuous_beam_partial_redistribution_applicability(10000, 11000, True, True, True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_continuous_beam_applicability
        Validation cases:
            - BEND-PROC-8.2.5

    Implementation notes:
        - Relative difference is evaluated against the larger span, yielding a symmetric test.
        - Defaults must be explicit in the input configuration.
    """
    l1 = _positive(adjacent_span_1_mm, "adjacent_span_1_mm")
    l2 = _positive(adjacent_span_2_mm, "adjacent_span_2_mm")
    if not all(isinstance(v, bool) for v in (constant_section, doubly_symmetric_section, required_clause_checks_confirmed)):
        raise TypeError("applicability flags must be bool")
    difference = abs(l1 - l2) / max(l1, l2)
    failed: list[str] = []
    if difference > 0.20 + 1e-12:
        failed.append("adjacent_span_difference_above_20_percent")
    if not constant_section:
        failed.append("section_not_constant")
    if not doubly_symmetric_section:
        failed.append("section_not_doubly_symmetric")
    if not required_clause_checks_confirmed:
        failed.append("referenced_stability_checks_not_confirmed")
    return {"permitted": not failed, "relative_span_difference": difference, "failed_gates": failed}


def redistributed_design_moment_eq56(maximum_elastic_moment_n_mm: float, effective_moment_n_mm: float) -> float:
    """
    Summary:
        Calculate the redistributed design moment for clause 8.2.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.5
        Annex: None
        Equation/Table: Equation (56)
        Audit ID: SP16-EQ-056
        Normative status: normative

    Mathematical form:
        M=0.5*(M_max+M_eff).

    Parameters:
        maximum_elastic_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Largest elastic-analysis moment M_max.
            Valid range: >= 0
            Source: elastic continuous-beam analysis
        effective_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: M_eff from equation (57), (58), or the fixed-end rule.
            Valid range: >= 0
            Source: clause 8.2.5

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Redistributed design moment M.

    Assumptions:
        - Inputs are governing moment magnitudes for the same load combination.

    Sign convention:
        - Moments are magnitudes.

    Unit convention:
        - Both moments use N*mm.

    Applicability:
        - Clause 8.2.5 partial redistribution.

    Limitations:
        - Does not calculate M_max or determine end-restraint category.

    Raises:
        ValueError: A moment is negative.
        TypeError: An input is not real.

    Examples:
        >>> redistributed_design_moment_eq56(100, 60)
        80.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_56_to_58
        Validation cases:
            - BEND-EQ-056

    Implementation notes:
        - No sign cancellation is permitted because the clause uses governing magnitudes.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5 * (
        _nonnegative(maximum_elastic_moment_n_mm, "maximum_elastic_moment_n_mm")
        + _nonnegative(effective_moment_n_mm, "effective_moment_n_mm")
    )


def effective_moment_hinged_end_eq57(
    end_span_simple_beam_moments_n_mm: Sequence[float],
    distances_to_end_support_mm: Sequence[float],
    end_span_length_mm: float,
) -> float:
    """
    Summary:
        Calculate M_eff as the maximum of M_1/(1+a/l) for an end span with a hinged end.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.5
        Annex: None
        Equation/Table: Equation (57)
        Audit ID: SP16-EQ-057
        Normative status: normative

    Mathematical form:
        M_eff=max_i[M_1,i/(1+a_i/l)].

    Parameters:
        end_span_simple_beam_moments_n_mm:
            Type: sequence[float]
            Unit: N*mm
            Meaning: Candidate M_1 values from the corresponding simply supported span model.
            Valid range: non-empty, each >= 0
            Source: load analysis
        distances_to_end_support_mm:
            Type: sequence[float]
            Unit: mm
            Meaning: Matching distances a from each candidate section to the end support.
            Valid range: same length, each between 0 and l
            Source: geometry
        end_span_length_mm:
            Type: float
            Unit: mm
            Meaning: End-span length l.
            Valid range: > 0
            Source: geometry

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Maximum effective moment M_eff.

    Assumptions:
        - Candidate arrays cover all sections needed to evaluate the maximum operator.

    Sign convention:
        - Moments and distances are non-negative magnitudes.

    Unit convention:
        - Moments use N*mm and distances use mm.

    Applicability:
        - Continuous beams with hinged ends and beams with one fixed and one freely supported end.

    Limitations:
        - Continuous maximization is approximated by the caller-supplied candidate set.

    Raises:
        ValueError: Arrays are empty, mismatched, or a distance is outside 0-l.
        TypeError: Values are not real sequences.

    Examples:
        >>> effective_moment_hinged_end_eq57([100, 120], [0, 5], 10)
        100.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_56_to_58
        Validation cases:
            - BEND-EQ-057

    Implementation notes:
        - The standard max operator is implemented over explicit samples.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(end_span_simple_beam_moments_n_mm, Sequence) or isinstance(end_span_simple_beam_moments_n_mm, (str, bytes)):
        raise TypeError("end_span_simple_beam_moments_n_mm must be a sequence")
    if not isinstance(distances_to_end_support_mm, Sequence) or isinstance(distances_to_end_support_mm, (str, bytes)):
        raise TypeError("distances_to_end_support_mm must be a sequence")
    if len(end_span_simple_beam_moments_n_mm) == 0 or len(end_span_simple_beam_moments_n_mm) != len(distances_to_end_support_mm):
        raise ValueError("moment and distance sequences must be non-empty and have equal length")
    length = _positive(end_span_length_mm, "end_span_length_mm")
    values: list[float] = []
    for index, (moment, distance) in enumerate(zip(end_span_simple_beam_moments_n_mm, distances_to_end_support_mm)):
        m = _nonnegative(moment, f"end_span_simple_beam_moments_n_mm[{index}]")
        a = _nonnegative(distance, f"distances_to_end_support_mm[{index}]")
        if a > length:
            raise ValueError("each distance must not exceed end_span_length_mm")
        values.append(m / (1.0 + a / length))
    return max(values)


def effective_moment_intermediate_span_eq58(maximum_intermediate_simple_beam_moment_n_mm: float) -> float:
    """
    Summary:
        Calculate M_eff for an intermediate span as one half of M_2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.5
        Annex: None
        Equation/Table: Equation (58)
        Audit ID: SP16-EQ-058
        Normative status: normative

    Mathematical form:
        M_eff=0.5*M_2.

    Parameters:
        maximum_intermediate_simple_beam_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Maximum M_2 in an intermediate span from the simply supported model.
            Valid range: >= 0
            Source: load analysis

    Returns:
        Type: float
        Unit: N*mm
        Meaning: M_eff.

    Assumptions:
        - The input is the governing intermediate-span moment.

    Sign convention:
        - Moment is a magnitude.

    Unit convention:
        - N*mm.

    Applicability:
        - Clause 8.2.5 intermediate spans.

    Limitations:
        - Fixed-end M_3 uses the same one-half factor but is tracked by a separate procedure in the runner.

    Raises:
        ValueError: Moment is negative.
        TypeError: Moment is not real.

    Examples:
        >>> effective_moment_intermediate_span_eq58(100)
        50.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_56_to_58
        Validation cases:
            - BEND-EQ-058

    Implementation notes:
        - Exact scalar transcription.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5 * _nonnegative(maximum_intermediate_simple_beam_moment_n_mm, "maximum_intermediate_simple_beam_moment_n_mm")


def effective_moment_by_end_condition(
    end_condition: str,
    candidate_moments_n_mm: Sequence[float],
    candidate_distances_mm: Sequence[float] | None,
    span_length_mm: float | None,
) -> float:
    """
    Summary:
        Route M_eff calculation among hinged-end, intermediate-span, and fixed-end cases.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.5
        Annex: None
        Equation/Table: Equations (57)-(58) and unnumbered fixed-end rule
        Audit ID: SP16-PROC-8.2.5-EFFECTIVE-MOMENT-ROUTING
        Normative status: normative

    Mathematical form:
        End-condition selector -> equation (57), 0.5M_2, or 0.5M_3.

    Parameters:
        end_condition:
            Type: str
            Unit: dimensionless
            Meaning: hinged_end, intermediate_span, or fixed_ends.
            Valid range: listed identifiers
            Source: structural topology
        candidate_moments_n_mm:
            Type: sequence[float]
            Unit: N*mm
            Meaning: Candidate moments; one value for intermediate/fixed routes.
            Valid range: non-empty, non-negative
            Source: load analysis
        candidate_distances_mm:
            Type: sequence[float] or None
            Unit: mm
            Meaning: Distances a for hinged_end; None otherwise.
            Valid range: route-specific
            Source: geometry
        span_length_mm:
            Type: float or None
            Unit: mm
            Meaning: l for hinged_end; None otherwise.
            Valid range: route-specific
            Source: geometry

    Returns:
        Type: float
        Unit: N*mm
        Meaning: M_eff.

    Assumptions:
        - End-condition category is identified correctly.

    Sign convention:
        - Moments are magnitudes.

    Unit convention:
        - N*mm and mm.

    Applicability:
        - Clause 8.2.5 moment redistribution.

    Limitations:
        - No topology inference is performed.

    Raises:
        ValueError: Route inputs are inconsistent.
        TypeError: Sequence inputs are invalid.

    Examples:
        >>> effective_moment_by_end_condition('intermediate_span', [100], None, None)
        50.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_effective_moment_router
        Validation cases:
            - BEND-PROC-MEFF

    Implementation notes:
        - Fixed-end and intermediate routes share the one-half scalar but retain distinct route labels.
        - Defaults must be explicit in the input configuration.
    """
    if end_condition == "hinged_end":
        if candidate_distances_mm is None or span_length_mm is None:
            raise ValueError("hinged_end requires candidate_distances_mm and span_length_mm")
        return effective_moment_hinged_end_eq57(candidate_moments_n_mm, candidate_distances_mm, span_length_mm)
    if end_condition not in {"intermediate_span", "fixed_ends"}:
        raise ValueError("Unsupported end_condition")
    if candidate_distances_mm is not None or span_length_mm is not None:
        raise ValueError("intermediate_span and fixed_ends require distances and span length to be None")
    if len(candidate_moments_n_mm) != 1:
        raise ValueError("intermediate_span and fixed_ends require exactly one moment")
    return effective_moment_intermediate_span_eq58(candidate_moments_n_mm[0])


def bimetal_major_axis_coefficient_eq61(
    flange_reference_coefficient_c_xf: float,
    flange_to_web_area_ratio: float,
    flange_to_web_yield_resistance_ratio: float,
) -> float:
    """
    Summary:
        Calculate c_xr for a bimetal beam.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Equation (61)
        Audit ID: SP16-EQ-061
        Normative status: normative

    Mathematical form:
        c_xr=(alpha_f*r+0.25-0.0833/r^2)/(alpha_f+0.167).

    Parameters:
        flange_reference_coefficient_c_xf:
            Type: float
            Unit: dimensionless
            Meaning: Legacy API parameter retained for backward call compatibility; it is not present in current equation (61) and is not used in the calculation.
            Valid range: > 0
            Source: legacy package API compatibility only
        flange_to_web_area_ratio:
            Type: float
            Unit: dimensionless
            Meaning: alpha_f=A_f/A_w.
            Valid range: >= 0
            Source: section properties
        flange_to_web_yield_resistance_ratio:
            Type: float
            Unit: dimensionless
            Meaning: r=R_yf/R_yw.
            Valid range: > 0
            Source: material properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c_xr.

    Assumptions:
        - alpha_f=A_f/A_w and r=R_yf/R_yw follow clause 8.2.8 definitions.

    Sign convention:
        - Ratios are positive magnitudes.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Bimetal I or box beams with two symmetry axes.

    Limitations:
        - The first legacy parameter is intentionally ignored by the current-SP16 formula; it remains only to preserve the frozen public call shape.

    Raises:
        ValueError: Domain is invalid or the computed coefficient is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> round(bimetal_major_axis_coefficient_eq61(99.0, 1.0, 1.2), 6)
        1.192557

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_61
        Validation cases:
            - BEND-EQ-061

    Implementation notes:
        - Decimal 0.0833 is retained as printed rather than replaced by 1/12.
        - The frozen legacy first parameter is validated but ignored; current equation (61) contains alpha_f*r, not c_xf*r.
        - Defaults must be explicit in the input configuration.
    """
    _positive(flange_reference_coefficient_c_xf, "flange_reference_coefficient_c_xf")  # legacy compatibility parameter
    alpha = _nonnegative(flange_to_web_area_ratio, "flange_to_web_area_ratio")
    ratio = _positive(flange_to_web_yield_resistance_ratio, "flange_to_web_yield_resistance_ratio")
    result = (alpha * ratio + 0.25 - 0.0833 / ratio**2) / (alpha + 0.167)
    if result <= 0.0:
        raise ValueError("equation (61) produced a non-positive coefficient")
    return result


def bimetal_shear_reduction_factor_eq62(
    shear_stress_x_n_mm2: float,
    web_design_shear_resistance_n_mm2: float,
    flange_to_web_area_ratio: float,
    flange_to_web_yield_resistance_ratio: float,
) -> float:
    """
    Summary:
        Calculate beta_r for a bimetal beam.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Equation (62)
        Audit ID: SP16-EQ-062
        Normative status: normative

    Mathematical form:
        beta_r=1 for tau_x<=0.5R_sw; otherwise 1-[0.2/(alpha_f*r+0.25)]*(tau_x/R_sw)^4 up to 0.9R_sw.

    Parameters:
        shear_stress_x_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: tau_x magnitude.
            Valid range: 0 <= tau_x <= 0.9R_sw
            Source: force and web area
        web_design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Web shear resistance R_sw.
            Valid range: > 0
            Source: web material
        flange_to_web_area_ratio:
            Type: float
            Unit: dimensionless
            Meaning: alpha_f=A_f/A_w.
            Valid range: >= 0
            Source: section properties
        flange_to_web_yield_resistance_ratio:
            Type: float
            Unit: dimensionless
            Meaning: r=R_yf/R_yw.
            Valid range: > 0
            Source: material properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: beta_r.

    Assumptions:
        - The web material defines R_sw.

    Sign convention:
        - Shear stress is a magnitude.

    Unit convention:
        - tau_x and R_sw use the same stress unit.

    Applicability:
        - Equations (59)-(60).

    Limitations:
        - Values above 0.9R_sw are rejected.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> bimetal_shear_reduction_factor_eq62(50, 100, 1, 1.2)
        1.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equation_62_branches
        Validation cases:
            - BEND-EQ-062

    Implementation notes:
        - The exact 0.9 boundary is accepted to reconcile the clause applicability statement with the printed branch.
        - Defaults must be explicit in the input configuration.
    """
    tau = _nonnegative(shear_stress_x_n_mm2, "shear_stress_x_n_mm2")
    resistance = _positive(web_design_shear_resistance_n_mm2, "web_design_shear_resistance_n_mm2")
    alpha = _nonnegative(flange_to_web_area_ratio, "flange_to_web_area_ratio")
    ratio = _positive(flange_to_web_yield_resistance_ratio, "flange_to_web_yield_resistance_ratio")
    if tau > 0.9 * resistance + 1e-12:
        raise ValueError("equation (62) requires shear_stress_x_n_mm2 <= 0.9*web_design_shear_resistance_n_mm2")
    if tau <= 0.5 * resistance:
        return 1.0
    return 1.0 - 0.2 / (alpha * ratio + 0.25) * (tau / resistance) ** 4


def bimetal_minor_axis_coefficient(section_family: str, flange_to_web_yield_resistance_ratio: float) -> float:
    """
    Summary:
        Return c_yr for a bimetal I-section or box section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Unnumbered rule following equation (62)
        Audit ID: SP16-PROC-8.2.8-BIMETAL-MINOR-COEFFICIENT
        Normative status: normative

    Mathematical form:
        c_yr=1.15 for I-sections; c_yr=1.05/r for box sections.

    Parameters:
        section_family:
            Type: str
            Unit: dimensionless
            Meaning: i_section or box_section.
            Valid range: i_section, box_section
            Source: section geometry
        flange_to_web_yield_resistance_ratio:
            Type: float
            Unit: dimensionless
            Meaning: r=R_yf/R_yw.
            Valid range: > 0
            Source: material properties

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: c_yr.

    Assumptions:
        - The section has two axes of symmetry as required by clause 8.2.8.

    Sign convention:
        - r is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Minor-axis term in equation (60).

    Limitations:
        - No other section family is supported.

    Raises:
        ValueError: section_family is unsupported or r is non-positive.
        TypeError: r is not real.

    Examples:
        >>> bimetal_minor_axis_coefficient('box_section', 1.5)
        0.7000000000000001

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_bimetal_minor_axis_coefficient
        Validation cases:
            - BEND-PROC-CYR

    Implementation notes:
        - r is validated for both branches to keep the interface uniform.
        - Defaults must be explicit in the input configuration.
    """
    ratio = _positive(flange_to_web_yield_resistance_ratio, "flange_to_web_yield_resistance_ratio")
    if section_family == "i_section":
        return 1.15
    if section_family == "box_section":
        return 1.05 / ratio
    raise ValueError("section_family must be i_section or box_section")


def bimetal_bending_applicability(
    section_family: str,
    has_two_symmetry_axes: bool,
    required_clause_checks_confirmed: bool,
    shear_stress_x_n_mm2: float,
    web_design_shear_resistance_n_mm2: float,
    shear_stress_y_n_mm2: float,
    flange_design_shear_resistance_n_mm2: float,
    is_support_section: bool,
) -> dict[str, Any]:
    """
    Summary:
        Check explicit applicability gates for bimetal beam equations (59)-(62).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Applicability text preceding equation (59)
        Audit ID: SP16-PROC-8.2.8-BIMETAL-APPLICABILITY
        Normative status: normative

    Mathematical form:
        I/box + two symmetry axes + referenced checks + tau_x<=0.9R_sw + tau_y<=0.5R_sf + non-support.

    Parameters:
        section_family:
            Type: str
            Unit: dimensionless
            Meaning: i_section or box_section.
            Valid range: listed values
            Source: section geometry
        has_two_symmetry_axes:
            Type: bool
            Unit: dimensionless
            Meaning: Symmetry confirmation.
            Valid range: true or false
            Source: section geometry
        required_clause_checks_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation of 8.4.4, 8.5.9, and 8.5.17.
            Valid range: true or false
            Source: engineering workflow
        shear_stress_x_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: tau_x magnitude.
            Valid range: >= 0
            Source: force and web area
        web_design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Web shear resistance.
            Valid range: > 0
            Source: web material
        shear_stress_y_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: tau_y magnitude.
            Valid range: >= 0
            Source: force and flange area
        flange_design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Flange shear resistance.
            Valid range: > 0
            Source: flange material
        is_support_section:
            Type: bool
            Unit: dimensionless
            Meaning: Whether the section is a support section.
            Valid range: true or false
            Source: model topology

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Permitted flag and failed gates.

    Assumptions:
        - The referenced stability checks were performed for the same member.

    Sign convention:
        - Shear stresses are magnitudes.

    Unit convention:
        - Stress inputs use one consistent unit.

    Applicability:
        - Bimetal class-2 beam strength route.

    Limitations:
        - Pure-bending and support-section special routes remain external.

    Raises:
        ValueError: Family or numeric domain is invalid.
        TypeError: Flags are not bool.

    Examples:
        >>> bimetal_bending_applicability('i_section', True, True, 100, 145, 50, 145, False)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_bimetal_applicability
        Validation cases:
            - BEND-PROC-8.2.8

    Implementation notes:
        - Support and pure-bending cases are deliberately not folded into one opaque route.
        - Defaults must be explicit in the input configuration.
    """
    if section_family not in {"i_section", "box_section"}:
        raise ValueError("section_family must be i_section or box_section")
    if not all(isinstance(v, bool) for v in (has_two_symmetry_axes, required_clause_checks_confirmed, is_support_section)):
        raise TypeError("applicability flags must be bool")
    tx = _nonnegative(shear_stress_x_n_mm2, "shear_stress_x_n_mm2")
    rsw = _positive(web_design_shear_resistance_n_mm2, "web_design_shear_resistance_n_mm2")
    ty = _nonnegative(shear_stress_y_n_mm2, "shear_stress_y_n_mm2")
    rsf = _positive(flange_design_shear_resistance_n_mm2, "flange_design_shear_resistance_n_mm2")
    failed: list[str] = []
    if not has_two_symmetry_axes:
        failed.append("section_not_doubly_symmetric")
    if not required_clause_checks_confirmed:
        failed.append("referenced_stability_checks_not_confirmed")
    if tx > 0.9 * rsw:
        failed.append("tau_x_above_0.9_Rsw")
    if ty > 0.5 * rsf:
        failed.append("tau_y_above_0.5_Rsf")
    if is_support_section:
        failed.append("support_section_special_route_required")
    return {"permitted": not failed, "failed_gates": failed}


def bimetal_bending_utilization_eq59(
    moment_x_n_mm: float,
    coefficient_c_xr: float,
    shear_reduction_beta_r: float,
    net_section_modulus_x_mm3: float,
    web_design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate one-plane bimetal beam bending utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Equation (59)
        Audit ID: SP16-EQ-059
        Normative status: normative

    Mathematical form:
        eta=|M_x|/(c_xr*beta_r*W_xn*R_yw*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        coefficient_c_xr:
            Type: float
            Unit: dimensionless
            Meaning: c_xr from equation (61).
            Valid range: > 0
            Source: equation (61)
        shear_reduction_beta_r:
            Type: float
            Unit: dimensionless
            Meaning: beta_r from equation (62).
            Valid range: > 0
            Source: equation (62)
        net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn.
            Valid range: > 0
            Source: section properties
        web_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_yw of the web steel.
            Valid range: > 0
            Source: material data
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (59) utilization.

    Assumptions:
        - Clause 8.2.8 applicability is confirmed.

    Sign convention:
        - Moment is a magnitude.

    Unit convention:
        - N and mm units are used.

    Applicability:
        - One-plane bending of bimetal I or box beams.

    Limitations:
        - Does not compute c_xr or beta_r internally.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> bimetal_bending_utilization_eq59(1e8, 1.2, 1, 1e6, 250, 1)
        0.3333333333333333

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_59_and_60
        Validation cases:
            - BEND-EQ-059

    Implementation notes:
        - Web yield resistance appears in the denominator exactly as printed.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(moment_x_n_mm, "moment_x_n_mm") / (
        _positive(coefficient_c_xr, "coefficient_c_xr")
        * _positive(shear_reduction_beta_r, "shear_reduction_beta_r")
        * _positive(net_section_modulus_x_mm3, "net_section_modulus_x_mm3")
        * _positive(web_design_yield_resistance_n_mm2, "web_design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def bimetal_biaxial_bending_utilization_eq60(
    moment_x_n_mm: float,
    moment_y_n_mm: float,
    coefficient_c_xr: float,
    coefficient_c_yr: float,
    shear_reduction_beta_r: float,
    net_section_modulus_x_mm3: float,
    net_section_modulus_y_mm3: float,
    web_design_yield_resistance_n_mm2: float,
    flange_design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate biaxial bimetal beam bending utilization.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.8
        Annex: None
        Equation/Table: Equation (60)
        Audit ID: SP16-EQ-060
        Normative status: normative

    Mathematical form:
        eta=|M_x|/(c_xr*beta_r*W_xn*R_yw*gamma_c)+|M_y|/(c_yr*W_yn*R_yf*gamma_c).

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Major-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Minor-axis moment magnitude.
            Valid range: >= 0
            Source: structural analysis
        coefficient_c_xr:
            Type: float
            Unit: dimensionless
            Meaning: c_xr.
            Valid range: > 0
            Source: equation (61)
        coefficient_c_yr:
            Type: float
            Unit: dimensionless
            Meaning: c_yr.
            Valid range: > 0
            Source: clause 8.2.8
        shear_reduction_beta_r:
            Type: float
            Unit: dimensionless
            Meaning: beta_r.
            Valid range: > 0
            Source: equation (62)
        net_section_modulus_x_mm3:
            Type: float
            Unit: mm3
            Meaning: W_xn.
            Valid range: > 0
            Source: section properties
        net_section_modulus_y_mm3:
            Type: float
            Unit: mm3
            Meaning: W_yn.
            Valid range: > 0
            Source: section properties
        web_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_yw.
            Valid range: > 0
            Source: web material
        flange_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_yf.
            Valid range: > 0
            Source: flange material
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: > 0
            Source: applicable rule

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (60) utilization.

    Assumptions:
        - Clause 8.2.8 applicability is confirmed.

    Sign convention:
        - Moments are magnitudes.

    Unit convention:
        - N and mm units are used.

    Applicability:
        - Biaxial bending of bimetal I or box beams.

    Limitations:
        - Does not calculate c_xr, c_yr, or beta_r.

    Raises:
        ValueError: Domain is invalid.
        TypeError: An input is not real.

    Examples:
        >>> bimetal_biaxial_bending_utilization_eq60(1e8, 2e7, 1.2, 1.15, 1, 1e6, 5e5, 250, 300, 1)
        0.4492753623188406

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_equations_59_and_60
        Validation cases:
            - BEND-EQ-060

    Implementation notes:
        - Web resistance is used in the major-axis term and flange resistance in the minor-axis term.
        - Defaults must be explicit in the input configuration.
    """
    return bimetal_bending_utilization_eq59(
        moment_x_n_mm,
        coefficient_c_xr,
        shear_reduction_beta_r,
        net_section_modulus_x_mm3,
        web_design_yield_resistance_n_mm2,
        working_condition_factor,
    ) + _nonnegative(moment_y_n_mm, "moment_y_n_mm") / (
        _positive(coefficient_c_yr, "coefficient_c_yr")
        * _positive(net_section_modulus_y_mm3, "net_section_modulus_y_mm3")
        * _positive(flange_design_yield_resistance_n_mm2, "flange_design_yield_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )


def apply_bolt_hole_factor(base_utilization_or_shear_stress: float, bolt_hole_factor: float) -> float:
    """
    Summary:
        Apply equation (45) explicitly to a shear utilization or shear stress affected by web bolt holes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.1 and 8.2.3
        Annex: None
        Equation/Table: Equation (45) application rule
        Audit ID: SP16-PROC-8.2.1-BOLT-HOLE-ADJUSTMENT
        Normative status: normative

    Mathematical form:
        adjusted_value = alpha*base_value.

    Parameters:
        base_utilization_or_shear_stress:
            Type: float
            Unit: dimensionless or N/mm2
            Meaning: Unamplified equation (42), (44), (54), or (55) quantity.
            Valid range: >= 0
            Source: audited equation result
        bolt_hole_factor:
            Type: float
            Unit: dimensionless
            Meaning: alpha from equation (45).
            Valid range: >= 1
            Source: equation (45)

    Returns:
        Type: float
        Unit: same as base input
        Meaning: Explicitly amplified quantity.

    Assumptions:
        - The checked web is weakened by the bolt-hole pattern covered by equation (45).

    Sign convention:
        - The base quantity is a non-negative magnitude.

    Unit convention:
        - Multiplication by alpha preserves the base unit.

    Applicability:
        - Shear-related checks explicitly identified by clauses 8.2.1 and 8.2.3.

    Limitations:
        - Does not determine whether bolt holes affect the checked plane.

    Raises:
        ValueError: The base is negative or alpha is below one.
        TypeError: An input is not real.

    Examples:
        >>> apply_bolt_hole_factor(0.8, 1.25)
        1.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_apply_bolt_hole_factor
        Validation cases:
            - BEND-PROC-HOLES

    Implementation notes:
        - The factor remains visible rather than being silently embedded in equation functions.
        - Defaults must be explicit in the input configuration.
    """
    base = _nonnegative(base_utilization_or_shear_stress, "base_utilization_or_shear_stress")
    factor = _positive(bolt_hole_factor, "bolt_hole_factor")
    if factor < 1.0:
        raise ValueError("bolt_hole_factor must be at least 1")
    return base * factor


def effective_load_length_by_case(
    figure_6_case: str,
    bearing_width_mm: float | None,
    flange_and_weld_or_fillet_height_mm: float | None,
    distribution_coefficient_psi: float | None,
    flange_and_rail_inertia_mm4: float | None,
    web_thickness_mm: float | None,
) -> float:
    """
    Summary:
        Route effective load-length calculation to equation (48) or (49) by Figure 6 case.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.2
        Annex: None
        Equation/Table: Equations (48)-(49), Figure 6
        Audit ID: SP16-PROC-8.2.2-LOCAL-LOAD-LENGTH
        Normative status: normative

    Mathematical form:
        welded_or_rolled -> b+2h; crane_wheel -> psi*cuberoot(I_1f/t_w).

    Parameters:
        figure_6_case:
            Type: str
            Unit: dimensionless
            Meaning: welded_or_rolled or crane_wheel.
            Valid range: listed identifiers
            Source: verified load-transfer geometry
        bearing_width_mm:
            Type: float or None
            Unit: mm
            Meaning: b for equation (48), None for crane_wheel.
            Valid range: route-specific
            Source: geometry
        flange_and_weld_or_fillet_height_mm:
            Type: float or None
            Unit: mm
            Meaning: h for equation (48), None for crane_wheel.
            Valid range: route-specific
            Source: geometry
        distribution_coefficient_psi:
            Type: float or None
            Unit: dimensionless
            Meaning: psi for equation (49), None otherwise.
            Valid range: route-specific
            Source: clause 8.2.2
        flange_and_rail_inertia_mm4:
            Type: float or None
            Unit: mm4
            Meaning: I_1f for equation (49), None otherwise.
            Valid range: route-specific
            Source: section/rail properties
        web_thickness_mm:
            Type: float or None
            Unit: mm
            Meaning: t_w for equation (49), None otherwise.
            Valid range: route-specific
            Source: section geometry

    Returns:
        Type: float
        Unit: mm
        Meaning: Effective distribution length l_eff.

    Assumptions:
        - Figure 6 case is identified correctly.

    Sign convention:
        - Dimensions and properties are positive magnitudes.

    Unit convention:
        - Length-based inputs use mm.

    Applicability:
        - Local web compression under clause 8.2.2.

    Limitations:
        - Figure recognition is not automated.

    Raises:
        ValueError: Route identifier or route-specific inputs are inconsistent.
        TypeError: Numeric route inputs are invalid.

    Examples:
        >>> effective_load_length_by_case('welded_or_rolled', 100, 20, None, None, None)
        140.0

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_effective_load_length_router
        Validation cases:
            - BEND-PROC-LEF

    Implementation notes:
        - None is used only to prove that parameters irrelevant to the selected route were not silently applied.
        - Defaults must be explicit in the input configuration.
    """
    if figure_6_case == "welded_or_rolled":
        if bearing_width_mm is None or flange_and_weld_or_fillet_height_mm is None:
            raise ValueError("welded_or_rolled requires bearing_width_mm and flange_and_weld_or_fillet_height_mm")
        if any(value is not None for value in (distribution_coefficient_psi, flange_and_rail_inertia_mm4, web_thickness_mm)):
            raise ValueError("crane-wheel inputs must be None for welded_or_rolled")
        return effective_load_length_eq48(bearing_width_mm, flange_and_weld_or_fillet_height_mm)
    if figure_6_case == "crane_wheel":
        if distribution_coefficient_psi is None or flange_and_rail_inertia_mm4 is None or web_thickness_mm is None:
            raise ValueError("crane_wheel requires psi, I_1f, and web thickness")
        if bearing_width_mm is not None or flange_and_weld_or_fillet_height_mm is not None:
            raise ValueError("equation (48) inputs must be None for crane_wheel")
        return effective_load_length_crane_eq49(
            distribution_coefficient_psi, flange_and_rail_inertia_mm4, web_thickness_mm
        )
    raise ValueError("figure_6_case must be welded_or_rolled or crane_wheel")


def biaxial_redistribution_route(
    redistribution_completed_in_x_plane: bool,
    redistribution_completed_in_y_plane: bool,
) -> dict[str, Any]:
    """
    Summary:
        Confirm the clause 8.2.6 route for biaxial bending with redistributed moments in both principal planes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.6
        Annex: None
        Equation/Table: Equation (51) with clause 8.2.5 redistribution in both planes
        Audit ID: SP16-PROC-8.2.6-BIAXIAL-REDISTRIBUTION
        Normative status: normative

    Mathematical form:
        permitted = redistribution_x and redistribution_y.

    Parameters:
        redistribution_completed_in_x_plane:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation that clause 8.2.5 was applied in the x plane.
            Valid range: true or false
            Source: engineering workflow
        redistribution_completed_in_y_plane:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation that clause 8.2.5 was applied in the y plane.
            Valid range: true or false
            Source: engineering workflow

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Permission to use equation (51) with redistributed moments.

    Assumptions:
        - Clause 8.2.5 applicability has already been established.

    Sign convention:
        - No signed quantity is used.

    Unit convention:
        - Boolean status only.

    Applicability:
        - Biaxially bent continuous or fixed-ended beams under clause 8.2.6.

    Limitations:
        - Does not perform redistribution itself.

    Raises:
        TypeError: Inputs are not bool.

    Examples:
        >>> biaxial_redistribution_route(True, True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_biaxial_redistribution_route
        Validation cases:
            - BEND-PROC-8.2.6

    Implementation notes:
        - Both planes are required explicitly.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(redistribution_completed_in_x_plane, bool) or not isinstance(
        redistribution_completed_in_y_plane, bool
    ):
        raise TypeError("redistribution flags must be bool")
    return {
        "permitted": redistribution_completed_in_x_plane and redistribution_completed_in_y_plane,
        "required_formula": "equation_51",
    }


def class_3_plastic_hinge_route(
    clause_8_2_5_confirmed: bool,
    clause_8_4_6_confirmed: bool,
    clause_8_5_8_confirmed: bool,
    clause_8_5_9_confirmed: bool,
    clause_8_5_18_confirmed: bool,
    maximum_moment_sections_include_shear_effect: bool,
) -> dict[str, Any]:
    """
    Summary:
        Check the explicit clause 8.2.7 gates for the class-3 plastic-hinge route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 8.2.7
        Annex: None
        Equation/Table: Equation (50) with conditional plastic hinges and clause 8.2.3 shear effect
        Audit ID: SP16-PROC-8.2.7-CLASS-3-ROUTING
        Normative status: normative

    Mathematical form:
        permitted = conjunction of five referenced-clause confirmations and shear-effect confirmation.

    Parameters:
        clause_8_2_5_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Clause 8.2.5 applicability confirmed.
            Valid range: true or false
            Source: engineering workflow
        clause_8_4_6_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Clause 8.4.6 confirmed.
            Valid range: true or false
            Source: stability check
        clause_8_5_8_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Clause 8.5.8 confirmed.
            Valid range: true or false
            Source: local-stability check
        clause_8_5_9_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Clause 8.5.9 confirmed.
            Valid range: true or false
            Source: stiffener check
        clause_8_5_18_confirmed:
            Type: bool
            Unit: dimensionless
            Meaning: Clause 8.5.18 confirmed.
            Valid range: true or false
            Source: flange-stability check
        maximum_moment_sections_include_shear_effect:
            Type: bool
            Unit: dimensionless
            Meaning: Confirmation that clause 8.2.3 shear influence is included at maximum-moment sections.
            Valid range: true or false
            Source: calculation workflow

    Returns:
        Type: dict[str, Any]
        Unit: status data
        Meaning: Permitted flag and missing confirmations.

    Assumptions:
        - The member has already been classified as class 3.

    Sign convention:
        - No signed quantity is used.

    Unit convention:
        - Boolean status only.

    Applicability:
        - Class-3 continuous and fixed-ended beams under clause 8.2.7.

    Limitations:
        - Does not locate or form plastic hinges.

    Raises:
        TypeError: Any confirmation is not bool.

    Examples:
        >>> class_3_plastic_hinge_route(True, True, True, True, True, True)['permitted']
        True

    Tests:
        Unit tests:
            - tests/test_bending_members.py::test_class_3_route
        Validation cases:
            - BEND-PROC-8.2.7

    Implementation notes:
        - Missing confirmations remain visible in the result.
        - Defaults must be explicit in the input configuration.
    """
    confirmations = {
        "8.2.5": clause_8_2_5_confirmed,
        "8.4.6": clause_8_4_6_confirmed,
        "8.5.8": clause_8_5_8_confirmed,
        "8.5.9": clause_8_5_9_confirmed,
        "8.5.18": clause_8_5_18_confirmed,
        "shear_effect": maximum_moment_sections_include_shear_effect,
    }
    if not all(isinstance(value, bool) for value in confirmations.values()):
        raise TypeError("all confirmations must be bool")
    missing = [key for key, value in confirmations.items() if not value]
    return {"permitted": not missing, "missing_confirmations": missing, "required_formula": "equation_50"}
