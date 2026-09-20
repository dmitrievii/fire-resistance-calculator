"""Section 15 detailing classification, Table 44, and support-bearing checks."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_44 = json.loads((_DATA_DIR / "table_44_temperature_joint_distances.json").read_text(encoding="utf-8"))
_SECTION_15 = json.loads((_DATA_DIR / "section_15_requirement_classification.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-15-CLASSIFICATION",
    "SP16-PROC-15.1-TABLE-44-LOOKUP",
    "SP16-PROC-15.1-SPACING-ASSESSMENT",
    "SP16-PROC-15.1-PAIRED-BRACING",
    "SP16-PROC-15.12.1-BEARING-SELECTION",
    "SP16-PROC-15.12.1-FRICTION",
    "SP16-PROC-15.12.2-ANGLE-APPLICABILITY",
    "SP16-PROC-15.12.3-ROLLER-CHECK",
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


def _bool(value: bool, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be boolean")
    return value


def _choice(value: str, allowed: set[str], name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value


def table_44_catalog() -> dict[str, Any]:
    """Audit ID: SP16-TBL-44. 
    Summary:
        Return the audited Table 44 temperature-joint distance catalogue.
    Standard reference:
        СП 16.13330.2017, clause 15.1, Table 44, pages 97-98; Audit ID SP16-TBL-44.
    Parameters:
        None: Packaged audited data are used.
    Returns:
        dict[str, Any]: Deep copy of Table 44 metadata, rows, note, and boundary rules.
    Assumptions:
        The supplied consolidated PDF is the governing source for this package release.
    Sign convention:
        Distances are non-negative magnitudes.
    Unit convention:
        Distances are metres and temperature is degrees Celsius.
    Applicability:
        Steel frames of heated buildings, unheated buildings or hot shops, and open trestles.
    Limitations:
        The function does not classify a building automatically from BIM geometry.
    Raises:
        RuntimeError: Packaged JSON could not be decoded during import.
    Examples:
        >>> table_44_catalog()["table"]
        '44'
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_table_44_catalog_and_exact_values.
    Implementation notes:
        No interpolation is introduced; the printed boundary is t = -45 degrees C.
    """
    return json.loads(json.dumps(_TABLE_44, ensure_ascii=False))


def section_15_requirement_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the clause-by-clause execution classification for Section 15.
    Standard reference:
        СП 16.13330.2017, Section 15, pages 97-108; Audit ID SP16-PROC-15-CLASSIFICATION.
    Parameters:
        None: Packaged classification data are used.
    Returns:
        dict[str, Any]: Deep copy containing all Section 15 clause routes and categories.
    Assumptions:
        Classification separates formulas, direct detailing checks, evidence routes, and external analyses.
    Sign convention:
        Not applicable.
    Unit convention:
        Mixed metadata; no engineering value is calculated.
    Applicability:
        Audit and software-routing workflows for Section 15 requirements.
    Limitations:
        Classification is not proof that every drawing or external calculation complies.
    Raises:
        RuntimeError: Packaged JSON could not be decoded during import.
    Examples:
        >>> section_15_requirement_catalog()["section"]
        '15'
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_section_15_catalog_and_route.
    Implementation notes:
        Missing calculation methods are not reconstructed from engineering custom.
    """
    return json.loads(json.dumps(_SECTION_15, ensure_ascii=False))


def section_15_requirement_route(clause: str) -> dict[str, Any]:
    """Audit ID: SP16-PROC-15-CLASSIFICATION. 
    Summary:
        Return the classified implementation route for one Section 15 clause.
    Standard reference:
        СП 16.13330.2017, Section 15; Audit ID SP16-PROC-15-CLASSIFICATION.
    Parameters:
        clause: String clause identifier such as ``15.9.7`` or ``15.12.2``.
    Returns:
        dict[str, Any]: Matching clause record with category, package status, and required route.
    Assumptions:
        The caller uses the exact clause identifier printed in the standard.
    Sign convention:
        Not applicable.
    Unit convention:
        Not applicable.
    Applicability:
        Section 15 requirement routing and audit reporting.
    Limitations:
        The route does not perform external finite-element analysis or evidence review.
    Raises:
        TypeError: Clause is not a string.
        KeyError: Clause is not present in the Section 15 catalogue.
    Examples:
        >>> section_15_requirement_route("15.12.2")["category"]
        'implemented_formula'
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_section_15_catalog_and_route.
    Implementation notes:
        Parent section headings are catalogued separately from executable subordinate clauses.
    """
    if not isinstance(clause, str):
        raise TypeError("clause must be a string")
    for row in _SECTION_15["entries"]:
        if row["clause"] == clause:
            return json.loads(json.dumps(row, ensure_ascii=False))
    raise KeyError(f"Section 15 clause not catalogued: {clause}")


def table_44_maximum_spacing_m(
    building_type: str,
    direction: str,
    design_air_temperature_c: float,
) -> float:
    """
    Summary:
        Look up the maximum Table 44 distance for the selected frame category and direction.
    Standard reference:
        СП 16.13330.2017, clause 15.1, Table 44; Audit ID SP16-PROC-15.1-TABLE-44-LOOKUP.
    Parameters:
        building_type: ``heated_building``, ``unheated_building_or_hot_shop``, or ``open_trestle``.
        direction: Exact row direction identifier from the packaged Table 44 data.
        design_air_temperature_c: Design air temperature in degrees Celsius.
    Returns:
        float: Maximum permitted distance in metres.
    Assumptions:
        Building category and direction are selected by the responsible engineer.
    Sign convention:
        Negative temperature denotes below zero Celsius.
    Unit convention:
        Input temperature is degrees Celsius; output distance is metres.
    Applicability:
        Temperature-block and nearest-vertical-bracing distances covered by Table 44.
    Limitations:
        No interpolation or climatic-temperature analysis is performed by this lookup.
    Raises:
        TypeError: A string or numerical input has the wrong type.
        ValueError: The category/direction pair does not exist or temperature is non-finite.
    Examples:
        >>> table_44_maximum_spacing_m("heated_building", "between_joints_along_block", -30)
        230.0
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_table_44_catalog_and_exact_values.
    Implementation notes:
        The t >= -45 column is used at equality; t < -45 selects the colder column.
    """
    bt = _choice(building_type, {"heated_building", "unheated_building_or_hot_shop", "open_trestle"}, "building_type")
    if not isinstance(direction, str):
        raise TypeError("direction must be a string")
    temperature = _real(design_air_temperature_c, "design_air_temperature_c")
    for row in _TABLE_44["rows"]:
        if row["building_type"] == bt and row["direction"] == direction:
            key = "at_or_above_minus_45_c_m" if temperature >= -45.0 else "below_minus_45_c_m"
            return float(row[key])
    raise ValueError(f"No Table 44 row for building_type={bt!r}, direction={direction!r}")


def temperature_joint_spacing_assessment_15_1(
    actual_distance_m: float,
    building_type: str,
    direction: str,
    design_air_temperature_c: float,
    frame_stiffness_increased_by_walls_or_other_structures: bool,
) -> dict[str, Any]:
    """
    Summary:
        Assess Table 44 compliance and the separate clause 15.1 enhanced-analysis trigger.
    Standard reference:
        СП 16.13330.2017, clause 15.1 and Table 44; Audit ID SP16-PROC-15.1-SPACING-ASSESSMENT.
    Parameters:
        actual_distance_m: Actual temperature-block or bracing distance in metres.
        building_type: Table 44 building category.
        direction: Table 44 direction identifier.
        design_air_temperature_c: Design air temperature in degrees Celsius.
        frame_stiffness_increased_by_walls_or_other_structures: Whether walls or other structures increase frame stiffness.
    Returns:
        dict[str, Any]: Limit, utilization, compliance, exceedance, and enhanced-analysis requirement.
    Assumptions:
        Actual and tabulated distances refer to the same geometric definition.
    Sign convention:
        Distances are positive magnitudes.
    Unit convention:
        Distances are metres and utilization is dimensionless.
    Applicability:
        Clause 15.1 temperature-joint spacing assessment.
    Limitations:
        The function only identifies when climatic temperature effects, inelasticity, and joint flexibility must be included; it does not perform that analysis.
    Raises:
        TypeError: Boolean or numerical inputs have invalid types.
        ValueError: Distance is negative or the Table 44 route is invalid.
    Examples:
        >>> temperature_joint_spacing_assessment_15_1(220, "heated_building", "between_joints_along_block", -30, False)["table_compliance_pass"]
        True
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_temperature_joint_spacing_assessment_separates_limit_and_five_percent_trigger.
    Implementation notes:
        A distance between 100% and 105% of the limit still fails Table 44; 5% is an analysis trigger, not a tolerance.
    """
    actual = _nonnegative(actual_distance_m, "actual_distance_m")
    stiffened = _bool(frame_stiffness_increased_by_walls_or_other_structures, "frame_stiffness_increased_by_walls_or_other_structures")
    limit = table_44_maximum_spacing_m(building_type, direction, design_air_temperature_c)
    utilization = actual / limit
    more_than_five = actual > 1.05 * limit
    return {
        "maximum_table_44_distance_m": limit,
        "actual_distance_m": actual,
        "utilization": utilization,
        "table_compliance_pass": actual <= limit,
        "exceeds_table_value": actual > limit,
        "exceeds_table_value_by_more_than_five_percent": more_than_five,
        "frame_stiffness_increased_by_walls_or_other_structures": stiffened,
        "climatic_temperature_effects_inelastic_deformations_and_joint_flexibility_analysis_required": more_than_five or stiffened,
    }


def paired_vertical_bracing_max_spacing_m_15_1(
    structure_type: str,
    design_air_temperature_c: float,
) -> float:
    """
    Summary:
        Return the Table 44 note limit between two vertical bracing systems within one temperature block.
    Standard reference:
        СП 16.13330.2017, clause 15.1, note to Table 44; Audit ID SP16-PROC-15.1-PAIRED-BRACING.
    Parameters:
        structure_type: ``building`` or ``open_trestle``.
        design_air_temperature_c: Design air temperature in degrees Celsius.
    Returns:
        float: Maximum spacing between bracing axes in metres.
    Assumptions:
        Two vertical bracing systems occur between the temperature joints.
    Sign convention:
        Negative temperature denotes below zero Celsius.
    Unit convention:
        Temperature is degrees Celsius and spacing is metres.
    Applicability:
        Note to Table 44 only.
    Limitations:
        The function does not verify that two bracing systems exist or that their structural design is adequate.
    Raises:
        TypeError: Invalid input type.
        ValueError: Unsupported structure type or non-finite temperature.
    Examples:
        >>> paired_vertical_bracing_max_spacing_m_15_1("building", -50)
        40.0
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_paired_vertical_bracing_note_limits.
    Implementation notes:
        The smaller printed range value is used for t < -45 degrees C, as required by the note.
    """
    kind = _choice(structure_type, {"building", "open_trestle"}, "structure_type")
    temperature = _real(design_air_temperature_c, "design_air_temperature_c")
    cold = temperature < -45.0
    if kind == "building":
        return 40.0 if cold else 50.0
    return 25.0 if cold else 30.0


def support_bearing_friction_coefficient_15_12_1(bearing_type: str) -> float:
    """
    Summary:
        Return the fixed friction coefficient for a movable support type.
    Standard reference:
        СП 16.13330.2017, clause 15.12.1; Audit ID SP16-PROC-15.12.1-FRICTION.
    Parameters:
        bearing_type: ``flat_sliding`` or ``roller``.
    Returns:
        float: Friction coefficient, 0.3 or 0.03.
    Assumptions:
        The bearing matches the standard's flat movable or roller movable support category.
    Sign convention:
        Friction coefficient is a positive magnitude.
    Unit convention:
        Dimensionless.
    Applicability:
        Horizontal-force assessment for movable supports under clause 15.12.1.
    Limitations:
        No dependence on lubrication, contamination, temperature, wear, or manufacturer data is introduced.
    Raises:
        TypeError: Bearing type is not a string.
        ValueError: Bearing type is unsupported.
    Examples:
        >>> support_bearing_friction_coefficient_15_12_1("roller")
        0.03
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_support_bearing_selection_and_friction.
    Implementation notes:
        Values are transcribed directly; no range or probabilistic model is added.
    """
    kind = _choice(bearing_type, {"flat_sliding", "roller"}, "bearing_type")
    return 0.3 if kind == "flat_sliding" else 0.03


def support_bearing_selection_15_12_1(
    strict_uniform_pressure_distribution_required: bool,
    reaction_class: str,
    relieve_substructure_from_horizontal_forces: bool,
) -> dict[str, Any]:
    """
    Summary:
        Route clause 15.12.1 support-bearing selection requirements without inventing a product design.
    Standard reference:
        СП 16.13330.2017, clause 15.12.1; Audit ID SP16-PROC-15.12.1-BEARING-SELECTION.
    Parameters:
        strict_uniform_pressure_distribution_required: Whether strictly uniform bearing pressure is required.
        reaction_class: ``ordinary`` or ``very_large``.
        relieve_substructure_from_horizontal_forces: Whether a movable support is required to reduce horizontal actions.
    Returns:
        dict[str, Any]: Recommended normative support categories and evidence boundaries.
    Assumptions:
        The engineer has established the structural function of fixed and movable supports.
    Sign convention:
        Not applicable.
    Unit convention:
        Not applicable.
    Applicability:
        Initial support-type routing under clause 15.12.1.
    Limitations:
        The function does not size the bearing, check stability, or select a certified product.
    Raises:
        TypeError: Boolean inputs are not boolean.
        ValueError: Reaction class is unsupported.
    Examples:
        >>> support_bearing_selection_15_12_1(True, "very_large", True)["fixed_support_category"]
        'balancing_fixed_hinged_support'
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_support_bearing_selection_and_friction.
    Implementation notes:
        Fixed and movable recommendations may both be returned because a support system commonly requires both functions.
    """
    uniform = _bool(strict_uniform_pressure_distribution_required, "strict_uniform_pressure_distribution_required")
    relief = _bool(relieve_substructure_from_horizontal_forces, "relieve_substructure_from_horizontal_forces")
    reaction = _choice(reaction_class, {"ordinary", "very_large"}, "reaction_class")
    fixed = None
    if uniform:
        fixed = "balancing_fixed_hinged_support" if reaction == "very_large" else "centering_pad_or_tangential_fixed_hinged_support"
    movable = "flat_sliding_or_roller_movable_support" if relief else None
    return {
        "fixed_support_category": fixed,
        "movable_support_category": movable,
        "strict_uniform_pressure_distribution_required": uniform,
        "reaction_class": reaction,
        "relieve_substructure_from_horizontal_forces": relief,
        "detailed_geometry_material_product_and_anchor_design_required": True,
    }


def cylindrical_hinge_local_bearing_utilization_eq199(
    support_force_n: float,
    hinge_radius_mm: float,
    hinge_length_mm: float,
    local_bearing_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate cylindrical-hinge local-bearing utilization by equation (199).
    Standard reference:
        СП 16.13330.2017, clause 15.12.2, equation (199), page 108; Audit ID SP16-EQ-199.
    Parameters:
        support_force_n: Support force F in newtons.
        hinge_radius_mm: Cylindrical hinge radius r in millimetres.
        hinge_length_mm: Hinge length l in millimetres.
        local_bearing_design_resistance_n_mm2: R_lp from clause 6.1 in N/mm2.
        working_condition_factor: Working-condition factor gamma_c.
    Returns:
        float: Dimensionless utilization F/(1.25*r*l*R_lp*gamma_c).
    Assumptions:
        Contact is dense and the central contact angle is at least 90 degrees.
    Sign convention:
        Support force is a non-negative compressive magnitude.
    Unit convention:
        N, mm, and N/mm2 produce a dimensionless utilization.
    Applicability:
        Cylindrical hinges or trunnions of balancing supports under clause 15.12.2.
    Limitations:
        Contact geometry, edge effects, wear, local yielding distribution, and bearing stability are not modelled.
    Raises:
        TypeError: Invalid numerical input type.
        ValueError: Force is negative or a denominator term is non-positive/non-finite.
    Examples:
        >>> round(cylindrical_hinge_local_bearing_utilization_eq199(1000000, 150, 300, 240, 1), 6)
        0.074074
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_equation_199_and_contact_angle_wrapper.
    Implementation notes:
        The printed factor 1.25 is preserved exactly.
    """
    force = _nonnegative(support_force_n, "support_force_n")
    radius = _positive(hinge_radius_mm, "hinge_radius_mm")
    length = _positive(hinge_length_mm, "hinge_length_mm")
    resistance = _positive(local_bearing_design_resistance_n_mm2, "local_bearing_design_resistance_n_mm2")
    gamma_c = _positive(working_condition_factor, "working_condition_factor")
    return force / (1.25 * radius * length * resistance * gamma_c)


def cylindrical_hinge_bearing_check_15_12_2(
    support_force_n: float,
    contact_central_angle_deg: float,
    hinge_radius_mm: float,
    hinge_length_mm: float,
    local_bearing_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> dict[str, Any]:
    """
    Summary:
        Apply equation (199) only when the printed central contact-angle condition is satisfied.
    Standard reference:
        СП 16.13330.2017, clause 15.12.2 and equation (199); Audit ID SP16-PROC-15.12.2-ANGLE-APPLICABILITY.
    Parameters:
        support_force_n: Support force F in newtons.
        contact_central_angle_deg: Central angle of contacting surfaces in degrees.
        hinge_radius_mm: Hinge radius r in millimetres.
        hinge_length_mm: Hinge length l in millimetres.
        local_bearing_design_resistance_n_mm2: R_lp from clause 6.1 in N/mm2.
        working_condition_factor: Working-condition factor gamma_c.
    Returns:
        dict[str, Any]: Applicability, utilization, pass/fail, and governing formula metadata.
    Assumptions:
        The angle represents the actual design contact geometry.
    Sign convention:
        Force is a non-negative compression magnitude.
    Unit convention:
        Degrees, N, mm, N/mm2, and dimensionless utilization.
    Applicability:
        Equation (199) requires a central contact angle equal to or greater than 90 degrees.
    Limitations:
        When the angle is below 90 degrees, the function rejects the calculation rather than extrapolating it.
    Raises:
        TypeError: Invalid numerical input type.
        ValueError: Contact angle is below 90 degrees or another input is outside its domain.
    Examples:
        >>> cylindrical_hinge_bearing_check_15_12_2(1000000, 90, 150, 300, 240, 1)["equation_199_pass"]
        True
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_equation_199_and_contact_angle_wrapper.
    Implementation notes:
        Equality at 90 degrees is accepted exactly as printed.
    """
    angle = _real(contact_central_angle_deg, "contact_central_angle_deg")
    if angle < 90.0:
        raise ValueError("equation (199) applies only when contact_central_angle_deg >= 90")
    utilization = cylindrical_hinge_local_bearing_utilization_eq199(
        support_force_n,
        hinge_radius_mm,
        hinge_length_mm,
        local_bearing_design_resistance_n_mm2,
        working_condition_factor,
    )
    return {
        "contact_central_angle_deg": angle,
        "equation_199_applicable": True,
        "equation_199_utilization": utilization,
        "equation_199_pass": utilization <= 1.0,
    }


def roller_diametral_compression_utilization_eq200(
    support_force_n: float,
    roller_count: int,
    roller_diameter_mm: float,
    roller_length_mm: float,
    diametral_compression_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate roller diametral-compression utilization by equation (200).
    Standard reference:
        СП 16.13330.2017, clause 15.12.3, equation (200), page 108; Audit ID SP16-EQ-200.
    Parameters:
        support_force_n: Support force F in newtons.
        roller_count: Number of rollers n.
        roller_diameter_mm: Roller diameter d in millimetres.
        roller_length_mm: Roller length l in millimetres.
        diametral_compression_design_resistance_n_mm2: R_cd from clause 6.1 in N/mm2.
        working_condition_factor: Working-condition factor gamma_c.
    Returns:
        float: Dimensionless utilization F/(n*d*l*R_cd*gamma_c).
    Assumptions:
        Rollers share the design force according to the clause model and contact is free.
    Sign convention:
        Support force is a non-negative compressive magnitude.
    Unit convention:
        N, mm, and N/mm2 produce dimensionless utilization.
    Applicability:
        Diametral compression of support rollers under clause 15.12.3.
    Limitations:
        Load-distribution imperfections, roller skew, track bending, wear, and contact nonlinearity are not modelled.
    Raises:
        TypeError: Roller count is not an integer or another input has invalid type.
        ValueError: Roller count is less than one, force is negative, or a denominator term is non-positive.
    Examples:
        >>> round(roller_diametral_compression_utilization_eq200(1200000, 4, 120, 300, 12.5, 1), 6)
        0.666667
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_equation_200_and_roller_wrapper.
    Implementation notes:
        No hidden load-distribution coefficient is added to the printed equation.
    """
    force = _nonnegative(support_force_n, "support_force_n")
    if isinstance(roller_count, bool) or not isinstance(roller_count, int):
        raise TypeError("roller_count must be an integer")
    if roller_count < 1:
        raise ValueError("roller_count must be at least one")
    diameter = _positive(roller_diameter_mm, "roller_diameter_mm")
    length = _positive(roller_length_mm, "roller_length_mm")
    resistance = _positive(diametral_compression_design_resistance_n_mm2, "diametral_compression_design_resistance_n_mm2")
    gamma_c = _positive(working_condition_factor, "working_condition_factor")
    return force / (roller_count * diameter * length * resistance * gamma_c)


def roller_bearing_check_15_12_3(
    support_force_n: float,
    roller_count: int,
    roller_diameter_mm: float,
    roller_length_mm: float,
    diametral_compression_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> dict[str, Any]:
    """
    Summary:
        Return equation (200) utilization and pass/fail for a roller support.
    Standard reference:
        СП 16.13330.2017, clause 15.12.3 and equation (200); Audit ID SP16-PROC-15.12.3-ROLLER-CHECK.
    Parameters:
        support_force_n: Support force F in newtons.
        roller_count: Number of rollers n.
        roller_diameter_mm: Roller diameter d in millimetres.
        roller_length_mm: Roller length l in millimetres.
        diametral_compression_design_resistance_n_mm2: R_cd from clause 6.1 in N/mm2.
        working_condition_factor: Working-condition factor gamma_c.
    Returns:
        dict[str, Any]: Equation (200) utilization, capacity, and pass/fail.
    Assumptions:
        All equation (200) inputs correspond to the same support and design combination.
    Sign convention:
        Force and capacity are positive compression magnitudes.
    Unit convention:
        Force is N; capacity is N; utilization is dimensionless.
    Applicability:
        Roller supports governed by clause 15.12.3.
    Limitations:
        The result is not a complete bearing, track, anchorage, or substructure design.
    Raises:
        TypeError: Invalid integer or numerical input type.
        ValueError: An input is outside the equation domain.
    Examples:
        >>> roller_bearing_check_15_12_3(1200000, 4, 120, 300, 12.5, 1)["equation_200_pass"]
        True
    Tests:
        tests/test_structural_detailing_and_support_bearings.py::test_equation_200_and_roller_wrapper.
    Implementation notes:
        Capacity is reconstructed from the exact denominator of equation (200) for reporting.
    """
    utilization = roller_diametral_compression_utilization_eq200(
        support_force_n,
        roller_count,
        roller_diameter_mm,
        roller_length_mm,
        diametral_compression_design_resistance_n_mm2,
        working_condition_factor,
    )
    force = _nonnegative(support_force_n, "support_force_n")
    capacity = math.inf if utilization == 0.0 and force == 0.0 else force / utilization
    return {
        "equation_200_utilization": utilization,
        "equation_200_capacity_n": capacity,
        "equation_200_pass": utilization <= 1.0,
    }
