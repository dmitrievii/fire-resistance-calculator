"""Brittle-fracture prevention and welded-connection checks for Sections 13 and 14.1.

Stage N10 rebaselines Section 13 clauses 13.1-13.5 against SP16 Changes No. 1-6 through 09.12.2024. Section 14.1 remains a retained downstream legacy layer pending its own stage closure.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .bending_members import elastic_web_equivalent_stress_checks_eq44

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_37 = json.loads((_DATA_DIR / "table_37_lamellar_tearing_risk_factors.json").read_text(encoding="utf-8"))
_TABLE_38 = json.loads((_DATA_DIR / "table_38_minimum_fillet_weld_legs.json").read_text(encoding="utf-8"))
_TABLE_39 = json.loads((_DATA_DIR / "table_39_fillet_weld_coefficients.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-13.1-BRITTLE-FACTORS",
    "SP16-PROC-13.2-PREVENTION-CHECKLIST",
    "SP16-PROC-13.3-LAMELLAR-APPLICABILITY",
    "SP16-PROC-13.4-Z-TEST-ROUTE",
    "SP16-PROC-13.5-RISK-MODIFIER",
    "SP16-PROC-13.5-Z-GROUP-SELECTION",
    "SP16-PROC-13.5-LAMELLAR-CHECK",
    "SP16-PROC-14.1.1-14.1.6-DETAILING",
    "SP16-PROC-14.1.7-MAXIMUM-LEG",
    "SP16-PROC-14.1.7-MINIMUM-LENGTH",
    "SP16-PROC-14.1.7-MAXIMUM-FLANK-LENGTH",
    "SP16-PROC-14.1.7-MINIMUM-LAP",
    "SP16-PROC-14.1.8-CONSUMABLE-COMPATIBILITY",
    "SP16-PROC-14.1.9-ONE-SIDED-ROUTE",
    "SP16-PROC-14.1.10-INTERMITTENT-ROUTE",
    "SP16-PROC-14.1.10-INTERMITTENT-SPACING",
    "SP16-PROC-14.1.10-END-WELD-LENGTH",
    "SP16-PROC-14.1.11-PERIMETER-WELD-ROUTE",
    "SP16-PROC-14.1.12-PLUG-WELD-REQUIREMENTS",
    "SP16-PROC-14.1.13-COMBINED-DISTRIBUTION",
    "SP16-PROC-14.1.14-BUTT-LENGTH",
    "SP16-PROC-14.1.14-RESISTANCE-BRANCH",
    "SP16-PROC-14.1.15-COMBINED-BUTT-STRESS",
    "SP16-PROC-14.1.16-FILLET-LENGTH",
    "SP16-PROC-14.1.16-GOVERNING-PLANE",
    "SP16-PROC-14.1.20-SPOT-BETA",
    "SP16-PROC-14.1.20-SPOT-CAPACITY",
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


def _choice(value: str, allowed: set[str], name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value


def _doc(summary: str, reference: str, audit_id: str, math_form: str, params: str, returns: str,
         assumptions: str, signs: str, units: str, applicability: str, limitations: str,
         raises: str, example: str, tests: str, notes: str) -> str:
    """Private source-generation helper retained only to document the common docstring format."""
    return ""  # pragma: no cover


def table_37_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 37 lamellar-tearing risk-factor catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        Exact geometry factors plus psi_zt=0.2S and psi_zsh=0.3a.

    Parameters:
        No parameters.

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata and percent values
        Meaning: Deep copy of the Table 37 data.

    Assumptions:
        - Diagram selection is performed by an engineer.

    Sign convention:
        - Beneficial factors may be negative; adverse factors are positive.

    Unit convention:
        - Thicknesses are mm and factors are percent.

    Applicability:
        - Clause 13.5 lamellar-tearing risk calculation.

    Limitations:
        - The function does not recognize connection geometry from CAD data.

    Raises:
        RuntimeError: Packaged data are unavailable or malformed at import time.

    Examples:
        >>> table_37_catalog()["quality_group_thresholds_percent"]["Z25"]
        25.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table37_catalog_and_values
        Validation cases:
            - V15-T37

    Implementation notes:
        - Data are returned by deep copy.
        - No unstated interpolation is applied.
    """
    return json.loads(json.dumps(_TABLE_37, ensure_ascii=False))


def table_37_connection_form_factor(connection_form_case: str) -> float:
    """
    Summary:
        Look up the connection-form and weld-location risk factor from Table 37.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        psi_zf = Table37(connection_form_case).

    Parameters:
        connection_form_case: Stable Table 37 geometry-case identifier.

    Returns:
        Type: float
        Unit: percent
        Meaning: Connection-form risk factor psi_zf.

    Assumptions:
        - The selected identifier matches the normative diagram.

    Sign convention:
        - Negative values reduce the summed risk.

    Unit convention:
        - Result is expressed in percent points.

    Applicability:
        - Equation (174) input.

    Limitations:
        - No geometric recognition is performed.

    Raises:
        KeyError: The case identifier is not in Table 37.
        TypeError: The identifier is not a string.

    Examples:
        >>> table_37_connection_form_factor("ordinary_t_fillet")
        0.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table37_catalog_and_values
        Validation cases:
            - V15-T37-FORM

    Implementation notes:
        - Printed values are retained exactly.
        - Defaults are not applied.
    """
    if not isinstance(connection_form_case, str):
        raise TypeError("connection_form_case must be a string")
    try:
        return float(_TABLE_37["connection_form_factors_percent"][connection_form_case])
    except KeyError as exc:
        raise KeyError(f"Unknown Table 37 connection-form case: {connection_form_case}") from exc


def table_37_plate_thickness_factor(plate_thickness_mm: float) -> float:
    """
    Summary:
        Calculate the Table 37 risk factor associated with plate thickness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        psi_zt = 0.2*S.

    Parameters:
        plate_thickness_mm: Plate thickness S in mm; non-negative.

    Returns:
        Type: float
        Unit: percent
        Meaning: Thickness risk factor psi_zt.

    Assumptions:
        - S is the thickness of the plate working in the Z direction.

    Sign convention:
        - Thickness and factor are non-negative.

    Unit convention:
        - Input uses mm; output uses percent points.

    Applicability:
        - Table 37 and equation (174).

    Limitations:
        - No plate-selection logic is included.

    Raises:
        ValueError: Thickness is negative or non-finite.
        TypeError: Thickness is not real.

    Examples:
        >>> table_37_plate_thickness_factor(25.0)
        5.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq174_and_table37_factors
        Validation cases:
            - V15-T37-THICKNESS

    Implementation notes:
        - The printed coefficient 0.2 is used directly.
        - No defaults are applied.
    """
    return 0.2 * _nonnegative(plate_thickness_mm, "plate_thickness_mm")


def table_37_weld_leg_factor(weld_leg_mm: float) -> float:
    """
    Summary:
        Calculate the Table 37 risk factor associated with fillet-weld leg size.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        psi_zsh = 0.3*a.

    Parameters:
        weld_leg_mm: Fillet-weld leg a in mm; non-negative.

    Returns:
        Type: float
        Unit: percent
        Meaning: Weld-size risk factor psi_zsh.

    Assumptions:
        - The weld leg corresponds to the Table 37 sketch.

    Sign convention:
        - Weld leg and factor are non-negative.

    Unit convention:
        - Input uses mm; output uses percent points.

    Applicability:
        - Table 37 and equation (174).

    Limitations:
        - Groove-weld geometry is not inferred.

    Raises:
        ValueError: Weld leg is negative or non-finite.
        TypeError: Weld leg is not real.

    Examples:
        >>> table_37_weld_leg_factor(10.0)
        3.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq174_and_table37_factors
        Validation cases:
            - V15-T37-WELD-LEG

    Implementation notes:
        - The printed coefficient 0.3 is used directly.
        - No defaults are applied.
    """
    return 0.3 * _nonnegative(weld_leg_mm, "weld_leg_mm")


def table_37_restraint_factor(restraint_level: str) -> float:
    """
    Summary:
        Look up the Table 37 connection-restraint risk factor.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        psi_zj = Table37(restraint_level).

    Parameters:
        restraint_level: One of low_free_shrinkage, medium_partial_shrinkage, high_rigid_no_shrinkage.

    Returns:
        Type: float
        Unit: percent
        Meaning: Restraint risk factor.

    Assumptions:
        - Restraint level is selected from the standard descriptions.

    Sign convention:
        - Returned factors are non-negative.

    Unit convention:
        - Percent points.

    Applicability:
        - Equation (174).

    Limitations:
        - Structural stiffness is not calculated automatically.

    Raises:
        KeyError: The restraint identifier is unknown.
        TypeError: The identifier is not a string.

    Examples:
        >>> table_37_restraint_factor("medium_partial_shrinkage")
        3.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table37_catalog_and_values
        Validation cases:
            - V15-T37-RESTRAINT

    Implementation notes:
        - Exact printed values are used.
        - Defaults are not applied.
    """
    if not isinstance(restraint_level, str):
        raise TypeError("restraint_level must be a string")
    try:
        return float(_TABLE_37["restraint_factors_percent"][restraint_level])
    except KeyError as exc:
        raise KeyError(f"Unknown restraint level: {restraint_level}") from exc


def table_37_welding_technology_factor(pass_count: str, weld_sequence: str, preheat: str) -> float:
    """
    Summary:
        Sum the Table 37 welding-technology factors.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Table 37
        Audit ID: SP16-TBL-37
        Normative status: normative

    Mathematical form:
        psi_zs = psi_passes + psi_sequence + psi_preheat.

    Parameters:
        pass_count: one or multiple.
        weld_sequence: alternating_sides or one_side_then_other.
        preheat: without_preheat or with_preheat.

    Returns:
        Type: float
        Unit: percent
        Meaning: Total welding-technology factor psi_zs.

    Assumptions:
        - All three selections correspond to the actual welding procedure.

    Sign convention:
        - Beneficial technology factors are negative.

    Unit convention:
        - Percent points.

    Applicability:
        - Equation (174).

    Limitations:
        - Other process variables are outside Table 37.

    Raises:
        KeyError: A selector is not in Table 37.
        TypeError: A selector is not a string.

    Examples:
        >>> table_37_welding_technology_factor("multiple", "alternating_sides", "with_preheat")
        -12.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table37_technology_factor
        Validation cases:
            - V15-T37-TECHNOLOGY

    Implementation notes:
        - The three printed factors are summed without hidden weighting.
        - Defaults are not applied.
    """
    for value, name in ((pass_count, "pass_count"), (weld_sequence, "weld_sequence"), (preheat, "preheat")):
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
    data = _TABLE_37["welding_technology_factors_percent"]
    try:
        return float(data["pass_count"][pass_count] + data["sequence"][weld_sequence] + data["preheat"][preheat])
    except KeyError as exc:
        raise KeyError("Unknown Table 37 welding-technology selector") from exc


def lamellar_tearing_risk_sum_eq174(
    connection_form_factor_percent: float,
    plate_thickness_factor_percent: float,
    weld_leg_factor_percent: float,
    restraint_factor_percent: float,
    welding_technology_factor_percent: float,
) -> float:
    """
    Summary:
        Calculate the summed lamellar-tearing risk factor.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Equation (174)
        Audit ID: SP16-EQ-174
        Normative status: normative

    Mathematical form:
        psi_zr = psi_zf + psi_zt + psi_zsh + psi_zj + psi_zs.

    Parameters:
        connection_form_factor_percent: Table 37 connection-form factor.
        plate_thickness_factor_percent: Table 37 thickness factor.
        weld_leg_factor_percent: Table 37 weld-leg factor.
        restraint_factor_percent: Table 37 restraint factor.
        welding_technology_factor_percent: Table 37 technology factor.

    Returns:
        Type: float
        Unit: percent
        Meaning: Summed risk factor psi_zr.

    Assumptions:
        - All factors describe the same connection and welding procedure.

    Sign convention:
        - Negative factors reduce and positive factors increase risk.

    Unit convention:
        - All inputs and the output are percent points.

    Applicability:
        - Clause 13.5 lamellar-tearing check.

    Limitations:
        - Load-direction modifiers are applied separately.

    Raises:
        ValueError: Any factor is non-finite.
        TypeError: Any factor is not real.

    Examples:
        >>> lamellar_tearing_risk_sum_eq174(3, 5, 3, 3, -2)
        12.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq174_normal_zero_and_sign
        Validation cases:
            - V15-EQ-174

    Implementation notes:
        - The equation is a direct algebraic sum.
        - No factor is silently clipped.
    """
    values = [
        _real(connection_form_factor_percent, "connection_form_factor_percent"),
        _real(plate_thickness_factor_percent, "plate_thickness_factor_percent"),
        _real(weld_leg_factor_percent, "weld_leg_factor_percent"),
        _real(restraint_factor_percent, "restraint_factor_percent"),
        _real(welding_technology_factor_percent, "welding_technology_factor_percent"),
    ]
    return sum(values)


def lamellar_tearing_adjusted_risk_clause_13_5(base_risk_percent: float, through_thickness_action: str) -> float:
    """
    Summary:
        Apply the clause 13.5 static-compression or dynamic-action modifier to the risk factor.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Text following Equation (174)
        Audit ID: SP16-PROC-13.5-RISK-MODIFIER
        Normative status: normative

    Mathematical form:
        adjusted = 0.5*base for static compression; 1.1*base for dynamic/vibratory action; otherwise base.

    Parameters:
        base_risk_percent: Risk factor from equation (174).
        through_thickness_action: none, static_compression, or dynamic_or_vibratory.

    Returns:
        Type: float
        Unit: percent
        Meaning: Load-modified risk factor.

    Assumptions:
        - The selected action accurately describes the through-thickness material action.

    Sign convention:
        - The multiplier is applied algebraically to the signed factor.

    Unit convention:
        - Percent points.

    Applicability:
        - Clause 13.5 only.

    Limitations:
        - Simultaneous compression and dynamic action is not represented by one selector.

    Raises:
        ValueError: The action selector is unsupported or the risk is non-finite.
        TypeError: Inputs have invalid types.

    Examples:
        >>> lamellar_tearing_adjusted_risk_clause_13_5(20, "static_compression")
        10.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_lamellar_risk_modifier
        Validation cases:
            - V15-PROC-13.5-MODIFIER

    Implementation notes:
        - The literal 50 percent reduction and 10 percent increase are retained.
        - No combined modifier is invented.
    """
    risk = _real(base_risk_percent, "base_risk_percent")
    action = _choice(through_thickness_action, {"none", "static_compression", "dynamic_or_vibratory"}, "through_thickness_action")
    return risk * {"none": 1.0, "static_compression": 0.5, "dynamic_or_vibratory": 1.1}[action]


def required_z_quality_group_clause_13_5(
    construction_group: int,
    consequence_class: str,
    flange_connection_or_normal_force: bool = False,
) -> str:
    """
    Summary:
        Select the minimum Z-quality group explicitly prescribed by clause 13.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: Z15, Z25, Z35 routing text
        Audit ID: SP16-PROC-13.5-Z-GROUP-SELECTION
        Normative status: normative

    Mathematical form:
        Group 1/KS-3 or flange/normal force -> Z35; groups 1-3/KS-2 -> Z25; group 4/KS-1 -> Z15.

    Parameters:
        construction_group: Structural group 1-4 from Annex V.
        consequence_class: KS-1, KS-2, or KS-3.
        flange_connection_or_normal_force: True for clause 15.9.10 flange connections or force normal to plate.

    Returns:
        Type: str
        Unit: quality class
        Meaning: Required Z-quality group.

    Assumptions:
        - Group and consequence class are selected from applicable project documents.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Quality groups are categorical.

    Applicability:
        - Rolled product covered by clause 13.3.

    Limitations:
        - Inconsistent group/class combinations are rejected rather than normalized.

    Raises:
        ValueError: Group/class combination is unsupported.
        TypeError: Inputs have invalid types.

    Examples:
        >>> required_z_quality_group_clause_13_5(2, "KS-2")
        'Z25'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_required_z_group_and_check
        Validation cases:
            - V15-PROC-Z-GROUP

    Implementation notes:
        - The flange/normal-force condition overrides the ordinary group route.
        - Defaults are explicit.
    """
    if isinstance(construction_group, bool) or not isinstance(construction_group, int):
        raise TypeError("construction_group must be an integer")
    if construction_group not in {1, 2, 3, 4}:
        raise ValueError("construction_group must be 1, 2, 3, or 4")
    cc = _choice(consequence_class, {"KS-1", "KS-2", "KS-3"}, "consequence_class")
    if flange_connection_or_normal_force:
        return "Z35"
    if construction_group == 1 and cc == "KS-3":
        return "Z35"
    if construction_group in {1, 2, 3} and cc == "KS-2":
        return "Z25"
    if construction_group == 4 and cc == "KS-1":
        return "Z15"
    raise ValueError("The supplied construction-group and consequence-class combination is not the clause 13.5 route")


def lamellar_tearing_check_clause_13_5(adjusted_risk_percent: float, z_quality_group: str) -> dict[str, float | str | bool]:
    """
    Summary:
        Check the adjusted lamellar-tearing risk against the selected Z-quality threshold.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.5
        Annex: None
        Equation/Table: psi_zr <= psi_zn
        Audit ID: SP16-PROC-13.5-LAMELLAR-CHECK
        Normative status: normative

    Mathematical form:
        utilization = adjusted risk / threshold; pass when adjusted risk <= threshold.

    Parameters:
        adjusted_risk_percent: Risk after optional clause 13.5 load modifier.
        z_quality_group: Z15, Z25, or Z35.

    Returns:
        Type: dict[str, float | str | bool]
        Unit: percent and dimensionless
        Meaning: Threshold, utilization, and pass status.

    Assumptions:
        - The Z group was selected using the applicable clause route.

    Sign convention:
        - Negative risk values satisfy a positive threshold.

    Unit convention:
        - Risk and threshold use percent points.

    Applicability:
        - Clause 13.5.

    Limitations:
        - Certification of material Z properties is external.

    Raises:
        ValueError: Risk is non-finite or quality group is unsupported.
        TypeError: Inputs have invalid types.

    Examples:
        >>> lamellar_tearing_check_clause_13_5(20, "Z25")["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_required_z_group_and_check
        Validation cases:
            - V15-PROC-Z-CHECK

    Implementation notes:
        - The threshold values 15, 25, and 35 percent are taken from clause 13.5.
        - No material acceptance certificate is generated.
    """
    risk = _real(adjusted_risk_percent, "adjusted_risk_percent")
    group = _choice(z_quality_group, {"Z15", "Z25", "Z35"}, "z_quality_group")
    threshold = float(_TABLE_37["quality_group_thresholds_percent"][group])
    return {"z_quality_group": group, "threshold_percent": threshold, "risk_percent": risk,
            "utilization": risk / threshold, "pass": risk <= threshold}


def lamellar_tearing_applicability_clause_13_3(
    steel_grade_number: float,
    plate_thickness_mm: float,
    joint_type: str,
    through_thickness_tension: bool,
) -> dict[str, Any]:
    """
    Summary:
        Route a welded detail to the clause 13.3 lamellar-tearing assessment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.3
        Annex: None
        Equation/Table: Applicability text
        Audit ID: SP16-PROC-13.3-LAMELLAR-APPLICABILITY
        Normative status: normative

    Mathematical form:
        Risk route for C245+ plate at least 25 mm in T/corner/full-penetration details, or other welded plate above 40 mm, with through-thickness tension.

    Parameters:
        steel_grade_number: Numeric grade designation such as 245 or 355.
        plate_thickness_mm: Plate thickness in mm.
        joint_type: tee, corner, full_penetration, or other_welded.
        through_thickness_tension: Whether one element is tensioned through its thickness.

    Returns:
        Type: dict[str, Any]
        Unit: route metadata
        Meaning: Applicability and reasons.

    Assumptions:
        - The numeric grade designation is a valid proxy for C245 and higher.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Thickness uses mm.

    Applicability:
        - Welded rolled products described in clause 13.3.

    Limitations:
        - Ultrasonic inspection and continuity category are external.

    Raises:
        ValueError: Inputs are outside their domains.
        TypeError: Inputs have invalid types.

    Examples:
        >>> lamellar_tearing_applicability_clause_13_3(355, 30, "tee", True)["risk_assessment_required"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_clause13_applicability_and_checklist
        Validation cases:
            - V15-PROC-13.3

    Implementation notes:
        - The function routes the requirement; it does not certify plate quality.
        - No unsupported steel-grade mapping is performed.
    """
    grade = _positive(steel_grade_number, "steel_grade_number")
    thickness = _positive(plate_thickness_mm, "plate_thickness_mm")
    joint = _choice(joint_type, {"tee", "corner", "full_penetration", "other_welded"}, "joint_type")
    primary = grade >= 245.0 and thickness >= 25.0 and joint in {"tee", "corner", "full_penetration"}
    other_thick = thickness > 40.0 and joint == "other_welded"
    required = bool(through_thickness_tension and (primary or other_thick))
    return {"risk_assessment_required": required, "primary_25_mm_route": primary,
            "other_plate_over_40_mm_route": other_thick,
            "ultrasonic_quality_control_relevant": required}


def brittle_fracture_prevention_checklist_clause_13_1_13_2(checks: dict[str, bool]) -> dict[str, Any]:
    """
    Summary:
        Evaluate an explicit checklist of brittle-fracture prevention measures from clauses 13.1-13.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.1-13.2
        Annex: None
        Equation/Table: Qualitative requirements
        Audit ID: SP16-PROC-13.2-PREVENTION-CHECKLIST
        Normative status: normative

    Mathematical form:
        Pass when every explicitly supplied mandatory checklist item is true.

    Parameters:
        checks: Mapping from requirement identifier to boolean confirmation.

    Returns:
        Type: dict[str, Any]
        Unit: checklist status
        Meaning: Missing items and overall pass status.

    Assumptions:
        - The caller supplies all project-relevant requirements.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Boolean confirmations are dimensionless.

    Applicability:
        - Design review under clauses 13.1-13.2.

    Limitations:
        - The function cannot prove material selection, NDT quality, or detailing from drawings.

    Raises:
        ValueError: The mapping is empty or contains non-boolean values.
        TypeError: Input is not a dictionary.

    Examples:
        >>> brittle_fracture_prevention_checklist_clause_13_1_13_2({"steel_selected": True})["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_clause13_applicability_and_checklist
        Validation cases:
            - V15-PROC-13.2

    Implementation notes:
        - This is an auditable confirmation register, not an automatic drawing checker.
        - No omitted item is silently assumed true.
    """
    if not isinstance(checks, dict):
        raise TypeError("checks must be a dictionary")
    if not checks:
        raise ValueError("checks must not be empty")
    invalid = [key for key, value in checks.items() if not isinstance(key, str) or not isinstance(value, bool)]
    if invalid:
        raise ValueError("every checklist key must be a string and every value must be boolean")
    missing = sorted(key for key, value in checks.items() if not value)
    return {"checked_items": sorted(checks), "missing_items": missing, "pass": not missing}


def table_38_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 38 minimum fillet-weld-leg catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7
        Annex: None
        Equation/Table: Table 38
        Audit ID: SP16-TBL-38
        Normative status: normative

    Mathematical form:
        Exact connection-row and thicker-element thickness-bin lookup.

    Parameters:
        No parameters.

    Returns:
        Type: dict[str, Any]
        Unit: mm and metadata
        Meaning: Deep copy of Table 38.

    Assumptions:
        - Connection type and thicknesses are known.

    Sign convention:
        - Weld dimensions are positive.

    Unit convention:
        - All dimensions use mm.

    Applicability:
        - Clause 14.1.7 b.

    Limitations:
        - Routes requiring calculation or manufacturing regulations are not filled with invented values.

    Raises:
        RuntimeError: Packaged data are unavailable or malformed at import time.

    Examples:
        >>> table_38_catalog()["connection_rows"]["single_sided_corner_or_t"]["values_mm"]["17_22"]
        12.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table38_values_and_routes
        Validation cases:
            - V15-T38

    Implementation notes:
        - Data are returned by deep copy.
        - No gap-filling interpolation is used.
    """
    return json.loads(json.dumps(_TABLE_38, ensure_ascii=False))


def minimum_fillet_weld_leg_table38(
    connection_type: str,
    thicker_element_thickness_mm: float,
    thinner_element_thickness_mm: float,
    steel_yield_strength_n_mm2: float,
) -> dict[str, Any]:
    """
    Summary:
        Determine the Table 38 minimum fillet-weld leg or the required external route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7 b
        Annex: None
        Equation/Table: Table 38
        Audit ID: SP16-TBL-38
        Normative status: normative

    Mathematical form:
        Exact thickness-bin lookup when t>=0.6T, T<=40 mm, and fy<=590 N/mm2.

    Parameters:
        connection_type: double_sided_t_lap_or_corner or single_sided_corner_or_t.
        thicker_element_thickness_mm: T in mm.
        thinner_element_thickness_mm: t in mm.
        steel_yield_strength_n_mm2: Steel yield strength in N/mm2.

    Returns:
        Type: dict[str, Any]
        Unit: mm and route metadata
        Meaning: Minimum leg when tabulated or explicit calculation/external route.

    Assumptions:
        - T is not smaller than t.

    Sign convention:
        - Dimensions and strength are positive.

    Unit convention:
        - Dimensions use mm; strength uses N/mm2.

    Applicability:
        - Table 38 connection types.

    Limitations:
        - No value is invented below 4 mm, above 40 mm, for fy>590 N/mm2, or when t<0.6T.

    Raises:
        ValueError: Geometry or selector is invalid.
        TypeError: Inputs have invalid types.

    Examples:
        >>> minimum_fillet_weld_leg_table38("double_sided_t_lap_or_corner", 20, 12, 355)["minimum_weld_leg_mm"]
        10.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table38_values_and_routes
        Validation cases:
            - V15-T38-LOOKUP

    Implementation notes:
        - The thinner-than-0.6T route returns the 1.2t maximum for the externally calculated minimum.
        - Defaults are not applied.
    """
    ctype = _choice(connection_type, set(_TABLE_38["connection_rows"]), "connection_type")
    T = _positive(thicker_element_thickness_mm, "thicker_element_thickness_mm")
    t = _positive(thinner_element_thickness_mm, "thinner_element_thickness_mm")
    fy = _positive(steel_yield_strength_n_mm2, "steel_yield_strength_n_mm2")
    if t > T:
        raise ValueError("thinner_element_thickness_mm must not exceed thicker_element_thickness_mm")
    if fy > 590.0:
        return {"route": "manufacturing_regulation_required", "minimum_weld_leg_mm": None}
    if T > 40.0:
        return {"route": "calculation_required_above_40_mm", "minimum_weld_leg_mm": None}
    if t < 0.6 * T:
        return {"route": "calculation_required_t_below_0_6T", "minimum_weld_leg_mm": None,
                "maximum_permitted_calculated_leg_mm": 1.2 * t}
    for binrow in _TABLE_38["thicker_element_bins_mm"]:
        if float(binrow["min_inclusive"]) <= T <= float(binrow["max_inclusive"]):
            value = float(_TABLE_38["connection_rows"][ctype]["values_mm"][binrow["id"]])
            return {"route": "table_38", "thickness_bin": binrow["id"], "minimum_weld_leg_mm": value}
    return {"route": "calculation_required_outside_printed_bins", "minimum_weld_leg_mm": None}


def maximum_fillet_weld_leg_clause_14_1_7(thinner_element_thickness_mm: float, rounded_rolled_edge: bool = False) -> float:
    """
    Summary:
        Calculate the maximum fillet-weld leg allowed by clause 14.1.7 a.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7 a
        Annex: None
        Equation/Table: Maximum fillet-weld leg rule
        Audit ID: SP16-PROC-14.1.7-MAXIMUM-LEG
        Normative status: normative

    Mathematical form:
        kf,max=1.2t; for a rounded rolled edge kf,max=0.9t.

    Parameters:
        thinner_element_thickness_mm: Smallest connected-element thickness t in mm.
        rounded_rolled_edge: True when the weld is placed on the rounded edge of a rolled shape.

    Returns:
        Type: float
        Unit: mm
        Meaning: Maximum permitted fillet-weld leg.

    Assumptions:
        - The correct edge condition is selected.

    Sign convention:
        - Dimensions are positive.

    Unit convention:
        - mm.

    Applicability:
        - Fillet welds under clause 14.1.7 a.

    Limitations:
        - Does not check the Table 38 minimum.

    Raises:
        ValueError: Thickness is non-positive.
        TypeError: Inputs have invalid types.

    Examples:
        >>> maximum_fillet_weld_leg_clause_14_1_7(10)
        12.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_weld_dimension_rules
        Validation cases:
            - V15-PROC-14.1.7-MAXLEG

    Implementation notes:
        - The two printed multipliers are mutually exclusive.
        - Defaults are explicit.
    """
    t = _positive(thinner_element_thickness_mm, "thinner_element_thickness_mm")
    return (0.9 if rounded_rolled_edge else 1.2) * t


def minimum_fillet_weld_design_length_clause_14_1_7(weld_leg_mm: float) -> float:
    """
    Summary:
        Calculate the minimum design length of a fillet weld.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7 c
        Annex: None
        Equation/Table: Minimum length rule
        Audit ID: SP16-PROC-14.1.7-MINIMUM-LENGTH
        Normative status: normative

    Mathematical form:
        lw,min=max(4kf,40 mm).

    Parameters:
        weld_leg_mm: Fillet-weld leg kf in mm.

    Returns:
        Type: float
        Unit: mm
        Meaning: Minimum design length.

    Assumptions:
        - A continuous weld segment is being checked.

    Sign convention:
        - Length is positive.

    Unit convention:
        - mm.

    Applicability:
        - Fillet welds under clause 14.1.7 c.

    Limitations:
        - Does not calculate effective length reductions under 14.1.16.

    Raises:
        ValueError: Weld leg is non-positive.
        TypeError: Weld leg is not real.

    Examples:
        >>> minimum_fillet_weld_design_length_clause_14_1_7(8)
        40.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_weld_dimension_rules
        Validation cases:
            - V15-PROC-14.1.7-MINLEN

    Implementation notes:
        - The maximum of both printed minima is returned.
        - No default leg is inserted.
    """
    return max(4.0 * _positive(weld_leg_mm, "weld_leg_mm"), 40.0)


def maximum_flank_weld_length_clause_14_1_7(beta_f: float, weld_leg_mm: float, force_acts_along_full_weld: bool) -> float | None:
    """
    Summary:
        Calculate the maximum design length of a flank weld when the clause limit applies.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7 d
        Annex: None
        Equation/Table: Maximum flank-weld length rule
        Audit ID: SP16-PROC-14.1.7-MAXIMUM-FLANK-LENGTH
        Normative status: normative

    Mathematical form:
        lw,max=85*beta_f*kf; no limit from this rule when force acts along the full weld length.

    Parameters:
        beta_f: Table 39 weld-metal coefficient.
        weld_leg_mm: Fillet-weld leg in mm.
        force_acts_along_full_weld: True for the printed exception.

    Returns:
        Type: float | None
        Unit: mm
        Meaning: Maximum length or None when the exception applies.

    Assumptions:
        - beta_f is applicable to the welding process and leg size.

    Sign convention:
        - Coefficients and dimensions are positive.

    Unit convention:
        - mm.

    Applicability:
        - Flank welds under clause 14.1.7 d.

    Limitations:
        - Does not establish the force distribution itself.

    Raises:
        ValueError: beta_f or leg is non-positive.
        TypeError: Inputs have invalid types.

    Examples:
        >>> maximum_flank_weld_length_clause_14_1_7(0.9, 8, False)
        612.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_weld_dimension_rules
        Validation cases:
            - V15-PROC-14.1.7-MAXFLANK

    Implementation notes:
        - None explicitly represents the printed exception.
        - No alternative limit is invented.
    """
    if force_acts_along_full_weld:
        return None
    return 85.0 * _positive(beta_f, "beta_f") * _positive(weld_leg_mm, "weld_leg_mm")


def minimum_lap_length_clause_14_1_7(thinner_element_thickness_mm: float) -> float:
    """
    Summary:
        Calculate the minimum lap length of a welded lap joint.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7 e
        Annex: None
        Equation/Table: Minimum lap rule
        Audit ID: SP16-PROC-14.1.7-MINIMUM-LAP
        Normative status: normative

    Mathematical form:
        lap_min=5t.

    Parameters:
        thinner_element_thickness_mm: Thickness t of the thinner connected element.

    Returns:
        Type: float
        Unit: mm
        Meaning: Minimum lap length.

    Assumptions:
        - t is the thinner connected-element thickness.

    Sign convention:
        - Length is positive.

    Unit convention:
        - mm.

    Applicability:
        - Welded lap joints.

    Limitations:
        - Does not check weld strength or edge distances.

    Raises:
        ValueError: Thickness is non-positive.
        TypeError: Thickness is not real.

    Examples:
        >>> minimum_lap_length_clause_14_1_7(8)
        40.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_weld_dimension_rules
        Validation cases:
            - V15-PROC-14.1.7-LAP

    Implementation notes:
        - The printed factor five is retained.
        - No defaults are applied.
    """
    return 5.0 * _positive(thinner_element_thickness_mm, "thinner_element_thickness_mm")


def table_39_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 39 fillet-weld coefficient catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7-14.1.8
        Annex: None
        Equation/Table: Table 39
        Audit ID: SP16-TBL-39
        Normative status: normative

    Mathematical form:
        Exact beta_f and beta_z lookup by process, position, and weld-leg bin.

    Parameters:
        No parameters.

    Returns:
        Type: dict[str, Any]
        Unit: dimensionless and metadata
        Meaning: Deep copy of Table 39.

    Assumptions:
        - Process and weld position are selected from the printed table.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Weld legs use mm; coefficients are dimensionless.

    Applicability:
        - Fillet-weld design under 14.1.7-14.1.19.

    Limitations:
        - The missing 13 mm column is not interpolated.

    Raises:
        RuntimeError: Packaged data are unavailable or malformed at import time.

    Examples:
        >>> table_39_catalog()["processes"]["automatic_d3_5"]["boat"]["beta_f"]["3_8"]
        1.1

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table39_all_routes
        Validation cases:
            - V15-T39

    Implementation notes:
        - Data are returned by deep copy.
        - No interpolation is added.
    """
    return json.loads(json.dumps(_TABLE_39, ensure_ascii=False))


def table_39_fillet_weld_coefficients(welding_process: str, weld_position: str, weld_leg_mm: float) -> dict[str, float | str]:
    """
    Summary:
        Look up beta_f and beta_z from Table 39.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.7-14.1.8
        Annex: None
        Equation/Table: Table 39
        Audit ID: SP16-TBL-39
        Normative status: normative

    Mathematical form:
        (beta_f,beta_z)=Table39(process,position,kf-bin).

    Parameters:
        welding_process: Stable process identifier from the packaged table.
        weld_position: Stable position identifier for that process.
        weld_leg_mm: Fillet-weld leg in mm.

    Returns:
        Type: dict[str, float | str]
        Unit: dimensionless and bin identifier
        Meaning: beta_f, beta_z, and the applied weld-leg bin.

    Assumptions:
        - The process identifier correctly encodes wire-diameter conditions.

    Sign convention:
        - Coefficients are positive.

    Unit convention:
        - Weld leg uses mm.

    Applicability:
        - Normal welding modes represented in Table 39.

    Limitations:
        - kf=13 mm and kf<3 mm are rejected because no printed column applies.

    Raises:
        ValueError: Process, position, or leg is outside the table.
        TypeError: Inputs have invalid types.

    Examples:
        >>> table_39_fillet_weld_coefficients("automatic_d3_5", "lower", 10)["beta_f"]
        0.9

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_table39_all_routes
        Validation cases:
            - V15-T39-LOOKUP

    Implementation notes:
        - The manual-process row is represented by its printed constant beta_f=0.7 and beta_z=1.0.
        - No unstated interpolation is applied.
    """
    process = _choice(welding_process, set(_TABLE_39["processes"]), "welding_process")
    positions = _TABLE_39["processes"][process]
    position = _choice(weld_position, set(positions), "weld_position")
    kf = _positive(weld_leg_mm, "weld_leg_mm")
    bin_id: str | None = None
    if 3.0 <= kf <= 8.0:
        bin_id = "3_8"
    elif 9.0 <= kf <= 12.0:
        bin_id = "9_12"
    elif 14.0 <= kf <= 16.0:
        bin_id = "14_16"
    elif kf > 16.0:
        bin_id = "over_16"
    if bin_id is None:
        raise ValueError("Table 39 has no applicable printed weld-leg bin for this value")
    row = positions[position]
    return {"weld_leg_bin": bin_id, "beta_f": float(row["beta_f"][bin_id]),
            "beta_z": float(row["beta_z"][bin_id])}


def welding_consumable_compatibility_clause_14_1_8(
    welding_method: str,
    weld_metal_design_shear_resistance_n_mm2: float,
    fusion_boundary_design_shear_resistance_n_mm2: float,
    beta_f: float,
    beta_z: float,
    steel_yield_strength_n_mm2: float,
) -> dict[str, Any]:
    """
    Summary:
        Check the clause 14.1.8 welding-consumable resistance relation.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.8
        Annex: None
        Equation/Table: Three welding-method inequalities
        Audit ID: SP16-PROC-14.1.8-CONSUMABLE-COMPATIBILITY
        Normative status: normative

    Mathematical form:
        Mechanized: Rwf>Rwz; manual: 1.1Rwz<=Rwf<=Rwz*beta_z/beta_f; automatic: Rwz<Rwf<Rwz*beta_z/beta_f.

    Parameters:
        welding_method: mechanized, manual, or automatic.
        weld_metal_design_shear_resistance_n_mm2: Rwf.
        fusion_boundary_design_shear_resistance_n_mm2: Rwz.
        beta_f: Table 39 beta_f.
        beta_z: Table 39 beta_z.
        steel_yield_strength_n_mm2: Connected steel yield strength.

    Returns:
        Type: dict[str, Any]
        Unit: N/mm2 and boolean
        Meaning: Bounds and pass status.

    Assumptions:
        - Weld dimensions were established by calculation.

    Sign convention:
        - Resistances are positive.

    Unit convention:
        - Resistances use N/mm2.

    Applicability:
        - Elements with steel yield strength not exceeding 290 N/mm2.

    Limitations:
        - Material selection and certification remain external.

    Raises:
        ValueError: Method, strength range, or coefficient is invalid.
        TypeError: Inputs have invalid types.

    Examples:
        >>> welding_consumable_compatibility_clause_14_1_8("manual", 210, 180, 0.7, 1.0, 245)["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_consumable_compatibility
        Validation cases:
            - V15-PROC-14.1.8

    Implementation notes:
        - Strict and inclusive inequalities follow the printed mathematical signs.
        - The function rejects fy>290 rather than extending the rule.
    """
    method = _choice(welding_method, {"mechanized", "manual", "automatic"}, "welding_method")
    rwf = _positive(weld_metal_design_shear_resistance_n_mm2, "weld_metal_design_shear_resistance_n_mm2")
    rwz = _positive(fusion_boundary_design_shear_resistance_n_mm2, "fusion_boundary_design_shear_resistance_n_mm2")
    bf = _positive(beta_f, "beta_f")
    bz = _positive(beta_z, "beta_z")
    fy = _positive(steel_yield_strength_n_mm2, "steel_yield_strength_n_mm2")
    if fy > 290.0:
        raise ValueError("Clause 14.1.8 applies to steel yield strength not exceeding 290 N/mm2")
    upper = rwz * bz / bf
    if method == "mechanized":
        passed = rwf > rwz
        lower = rwz
        upper_value: float | None = None
    elif method == "manual":
        lower = 1.1 * rwz
        upper_value = upper
        passed = lower <= rwf <= upper
    else:
        lower = rwz
        upper_value = upper
        passed = lower < rwf < upper
    return {"method": method, "lower_bound_n_mm2": lower, "upper_bound_n_mm2": upper_value,
            "weld_metal_resistance_n_mm2": rwf, "pass": passed}


def intermittent_weld_spacing_limit_clause_14_1_10(
    thinner_element_thickness_mm: float,
    member_state: str,
    construction_group: int,
) -> float:
    """
    Summary:
        Calculate the maximum spacing between intermittent fillet-weld segments.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.10
        Annex: None
        Equation/Table: Intermittent-weld spacing rule
        Audit ID: SP16-PROC-14.1.10-INTERMITTENT-SPACING
        Normative status: normative

    Mathematical form:
        smax=min(200,12t) for compression or min(200,16t) for tension; multiply by 1.5 for group 4.

    Parameters:
        thinner_element_thickness_mm: Thickness t in mm.
        member_state: compression or tension.
        construction_group: Structural group 1-4.

    Returns:
        Type: float
        Unit: mm
        Meaning: Maximum segment spacing.

    Assumptions:
        - Intermittent welds are otherwise permitted by 14.1.10.

    Sign convention:
        - Length is positive.

    Unit convention:
        - mm.

    Applicability:
        - Intermittent fillet welds under static load.

    Limitations:
        - Does not assess environment, temperature, or redundancy.

    Raises:
        ValueError: State, group, or thickness is invalid.
        TypeError: Inputs have invalid types.

    Examples:
        >>> intermittent_weld_spacing_limit_clause_14_1_10(10, "compression", 3)
        120.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_intermittent_and_plug_weld_rules
        Validation cases:
            - V15-PROC-14.1.10-SPACING

    Implementation notes:
        - The group-4 factor is applied after taking the printed minimum.
        - No other group factor is applied.
    """
    t = _positive(thinner_element_thickness_mm, "thinner_element_thickness_mm")
    state = _choice(member_state, {"compression", "tension"}, "member_state")
    if isinstance(construction_group, bool) or not isinstance(construction_group, int) or construction_group not in {1, 2, 3, 4}:
        raise ValueError("construction_group must be an integer from 1 to 4")
    base = min(200.0, (12.0 if state == "compression" else 16.0) * t)
    return base * (1.5 if construction_group == 4 else 1.0)


def end_weld_minimum_length_clause_14_1_10(narrower_plate_width_mm: float) -> float:
    """
    Summary:
        Calculate the minimum end-weld length for built-up plate sections with intermittent welds.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.10
        Annex: None
        Equation/Table: End-weld length rule
        Audit ID: SP16-PROC-14.1.10-END-WELD-LENGTH
        Normative status: normative

    Mathematical form:
        lw1,min=0.75b.

    Parameters:
        narrower_plate_width_mm: Width b of the narrower connected plate.

    Returns:
        Type: float
        Unit: mm
        Meaning: Minimum end-weld length.

    Assumptions:
        - The member is a built-up section made from plates.

    Sign convention:
        - Length is positive.

    Unit convention:
        - mm.

    Applicability:
        - Intermittently welded built-up plate sections.

    Limitations:
        - Does not check the end weld strength.

    Raises:
        ValueError: Width is non-positive.
        TypeError: Width is not real.

    Examples:
        >>> end_weld_minimum_length_clause_14_1_10(200)
        150.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_intermittent_and_plug_weld_rules
        Validation cases:
            - V15-PROC-14.1.10-END

    Implementation notes:
        - The printed factor 0.75 is used directly.
        - No default width is inserted.
    """
    return 0.75 * _positive(narrower_plate_width_mm, "narrower_plate_width_mm")


def plug_weld_requirements_clause_14_1_12(
    drilled_element_thickness_mm: float,
    hole_diameter_mm: float | None = None,
    slot_width_mm: float | None = None,
    slot_length_mm: float | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Calculate the dimensional limits for plug welds in round holes or slots.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.12
        Annex: None
        Equation/Table: Plug-weld dimensional rules
        Audit ID: SP16-PROC-14.1.12-PLUG-WELD-REQUIREMENTS
        Normative status: normative

    Mathematical form:
        thickness >= max(t,0.45d or 0.45b,0.1 slot length) and <=16 mm; spacing >=4d or 4b; d,b>=t+8 mm.

    Parameters:
        drilled_element_thickness_mm: Thickness t of the drilled/slotted element.
        hole_diameter_mm: Round-hole diameter d, or None for a slot.
        slot_width_mm: Slot width b, or None for a round hole.
        slot_length_mm: Slot length, required for a slot.

    Returns:
        Type: dict[str, Any]
        Unit: mm and route metadata
        Meaning: Required weld thickness and minimum spacing checks.

    Assumptions:
        - Exactly one geometry route, round hole or slot, is supplied.

    Sign convention:
        - Dimensions are positive.

    Unit convention:
        - mm.

    Applicability:
        - Plug welds permitted by clauses 14.1.10 and 14.1.12.

    Limitations:
        - Plug welds are not assigned force-transfer resistance by this clause.

    Raises:
        ValueError: Geometry is incomplete or violates printed dimensional minima.
        TypeError: Inputs have invalid types.

    Examples:
        >>> plug_weld_requirements_clause_14_1_12(6, hole_diameter_mm=14)["minimum_center_spacing_mm"]
        56.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_intermittent_and_plug_weld_rules
        Validation cases:
            - V15-PROC-14.1.12

    Implementation notes:
        - The upper weld-thickness limit of 16 mm is returned explicitly.
        - No resistance model is invented.
    """
    t = _positive(drilled_element_thickness_mm, "drilled_element_thickness_mm")
    round_route = hole_diameter_mm is not None
    slot_route = slot_width_mm is not None or slot_length_mm is not None
    if round_route == slot_route:
        raise ValueError("Provide either a round-hole diameter or both slot width and slot length")
    if round_route:
        d = _positive(float(hole_diameter_mm), "hole_diameter_mm")
        if d < t + 8.0:
            raise ValueError("hole diameter must be at least t+8 mm")
        required = max(t, 0.45 * d)
        return {"geometry": "round", "minimum_weld_thickness_mm": required,
                "maximum_weld_thickness_mm": 16.0, "minimum_center_spacing_mm": 4.0 * d,
                "dimension_meets_t_plus_8": True}
    b = _positive(float(slot_width_mm), "slot_width_mm")
    length = _positive(float(slot_length_mm), "slot_length_mm")
    if b < t + 8.0:
        raise ValueError("slot width must be at least t+8 mm")
    required = max(t, 0.45 * b, 0.1 * length)
    return {"geometry": "slot", "minimum_weld_thickness_mm": required,
            "maximum_weld_thickness_mm": 16.0, "minimum_center_spacing_mm": 4.0 * b,
            "dimension_meets_t_plus_8": True}


def combined_connection_force_distribution_clause_14_1_13(
    total_shear_force_n: float,
    friction_connection_capacity_n: float,
    weld_capacity_n: float,
    welding_after_bolt_tightening_confirmed: bool,
    controlled_tension_bolts_confirmed: bool,
) -> dict[str, float | bool]:
    """
    Summary:
        Distribute shear between friction and welded parts in proportion to their capacities.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.13
        Annex: None
        Equation/Table: Proportional force-distribution procedure
        Audit ID: SP16-PROC-14.1.13-COMBINED-DISTRIBUTION
        Normative status: normative

    Mathematical form:
        Nf=N*Qf/(Qf+Qw); Nw=N*Qw/(Qf+Qw).

    Parameters:
        total_shear_force_n: Total connection shear force.
        friction_connection_capacity_n: Friction-connection capacity.
        weld_capacity_n: Weld capacity.
        welding_after_bolt_tightening_confirmed: Confirmation of required sequence.
        controlled_tension_bolts_confirmed: Confirmation that friction bolts have controlled tension.

    Returns:
        Type: dict[str, float | bool]
        Unit: N and boolean
        Meaning: Allocated forces and capacity pass status.

    Assumptions:
        - Capacities are calculated by applicable audited methods.

    Sign convention:
        - Force magnitudes and capacities are non-negative.

    Unit convention:
        - N.

    Applicability:
        - Combined friction-plus-welded connections under 14.1.13.

    Limitations:
        - Slip deformation compatibility is represented only by the prescribed proportional procedure.

    Raises:
        ValueError: Confirmation is false or capacity is invalid.
        TypeError: Inputs have invalid types.

    Examples:
        >>> combined_connection_force_distribution_clause_14_1_13(100, 60, 40, True, True)["weld_force_n"]
        40.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_combined_connection_distribution
        Validation cases:
            - V15-PROC-14.1.13

    Implementation notes:
        - Bolts without controlled tension and bearing-type bolts are not accepted.
        - No default confirmations are inserted.
    """
    total = _nonnegative(total_shear_force_n, "total_shear_force_n")
    friction = _nonnegative(friction_connection_capacity_n, "friction_connection_capacity_n")
    weld = _nonnegative(weld_capacity_n, "weld_capacity_n")
    if not welding_after_bolt_tightening_confirmed or not controlled_tension_bolts_confirmed:
        raise ValueError("Clause 14.1.13 sequence and controlled-tension bolt conditions must be confirmed")
    capacity = friction + weld
    if capacity <= 0.0:
        raise ValueError("combined connection capacity must be greater than zero")
    return {"friction_force_n": total * friction / capacity, "weld_force_n": total * weld / capacity,
            "total_capacity_n": capacity, "pass": total <= capacity}


def effective_butt_weld_length_clause_14_1_14(full_weld_length_mm: float, thickness_mm: float, runout_tabs_used: bool) -> float:
    """
    Summary:
        Calculate the design length of a butt weld for equation (175).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.14
        Annex: None
        Equation/Table: Effective butt-weld length rule
        Audit ID: SP16-PROC-14.1.14-BUTT-LENGTH
        Normative status: normative

    Mathematical form:
        lw=full length with runout tabs; otherwise lw=full length-2t.

    Parameters:
        full_weld_length_mm: Full weld length.
        thickness_mm: Smaller connected-element thickness t.
        runout_tabs_used: Whether weld ends extend beyond the joint on runout tabs.

    Returns:
        Type: float
        Unit: mm
        Meaning: Design weld length lw.

    Assumptions:
        - t is the smaller plate thickness.

    Sign convention:
        - Lengths are positive.

    Unit convention:
        - mm.

    Applicability:
        - Butt-weld axial check under 14.1.14.

    Limitations:
        - Does not inspect weld-end geometry.

    Raises:
        ValueError: Effective length is non-positive.
        TypeError: Inputs have invalid types.

    Examples:
        >>> effective_butt_weld_length_clause_14_1_14(200, 10, False)
        180.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq175_and_butt_weld_routes
        Validation cases:
            - V15-PROC-14.1.14-LENGTH

    Implementation notes:
        - The reduction is exactly 2t.
        - No default tab condition is assumed.
    """
    full = _positive(full_weld_length_mm, "full_weld_length_mm")
    t = _positive(thickness_mm, "thickness_mm")
    effective = full if runout_tabs_used else full - 2.0 * t
    if effective <= 0.0:
        raise ValueError("effective butt-weld length must be greater than zero")
    return effective


def butt_weld_axial_utilization_eq175(
    axial_force_n: float,
    thickness_mm: float,
    design_weld_length_mm: float,
    butt_weld_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate axial utilization of a butt-welded joint.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.14
        Annex: None
        Equation/Table: Equation (175)
        Audit ID: SP16-EQ-175
        Normative status: normative

    Mathematical form:
        eta=|N|/(t*lw*Rwy*gamma_c).

    Parameters:
        axial_force_n: Signed or magnitude axial force N.
        thickness_mm: Smaller plate thickness t.
        design_weld_length_mm: Design length lw.
        butt_weld_design_resistance_n_mm2: Applicable Rwy or Rwu/gamma_u branch.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (175) utilization.

    Assumptions:
        - Force passes through the connection centroid.

    Sign convention:
        - Absolute axial-force magnitude is checked.

    Unit convention:
        - N, mm, and N/mm2.

    Applicability:
        - Butt-welded joint under axial force.

    Limitations:
        - Resistance-branch selection is separate.

    Raises:
        ValueError: Denominator input is non-positive or force is non-finite.
        TypeError: Inputs are not real.

    Examples:
        >>> butt_weld_axial_utilization_eq175(100000, 10, 200, 250, 1)
        0.2

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq175_normal_zero_and_sign
        Validation cases:
            - V15-EQ-175

    Implementation notes:
        - No resistance is selected silently.
        - The result is not clipped at one.
    """
    n = abs(_real(axial_force_n, "axial_force_n"))
    return n / (_positive(thickness_mm, "thickness_mm") * _positive(design_weld_length_mm, "design_weld_length_mm") *
                _positive(butt_weld_design_resistance_n_mm2, "butt_weld_design_resistance_n_mm2") *
                _positive(working_condition_factor, "working_condition_factor"))


def butt_weld_combined_stress_clause_14_1_15(
    sigma_wx_n_mm2: float,
    sigma_wy_n_mm2: float,
    tau_wxy_n_mm2: float,
    butt_weld_yield_resistance_n_mm2: float,
    butt_weld_shear_resistance_n_mm2: float,
    working_condition_factor: float,
) -> dict[str, float | bool]:
    """
    Summary:
        Apply equation (44) to a butt weld without complete NDT as required by clause 14.1.15.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.15
        Annex: None
        Equation/Table: Equation (44) substitution route
        Audit ID: SP16-PROC-14.1.15-COMBINED-BUTT-STRESS
        Normative status: normative

    Mathematical form:
        Use sigma_x=sigma_wx, sigma_y=sigma_wy, tau=tau_wxy, Ry=Rwy, Rs=Rws in equation (44).

    Parameters:
        sigma_wx_n_mm2: Signed normal stress sigma_wx.
        sigma_wy_n_mm2: Signed normal stress sigma_wy.
        tau_wxy_n_mm2: Signed shear stress tau_wxy.
        butt_weld_yield_resistance_n_mm2: Rwy.
        butt_weld_shear_resistance_n_mm2: Rws.
        working_condition_factor: gamma_c.

    Returns:
        Type: dict[str, float | bool]
        Unit: dimensionless utilizations and booleans
        Meaning: Equation (44) equivalent and direct-shear checks.

    Assumptions:
        - All stresses are evaluated in the same weld section.

    Sign convention:
        - Normal-stress signs are retained.

    Unit convention:
        - N/mm2.

    Applicability:
        - Butt weld without complete NDT under combined stresses.

    Limitations:
        - Stress recovery is external.

    Raises:
        ValueError: Resistance or factor is invalid.
        TypeError: Inputs are not real.

    Examples:
        >>> butt_weld_combined_stress_clause_14_1_15(100, 0, 0, 250, 145, 1)["equivalent_pass"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_butt_combined_stress_route
        Validation cases:
            - V15-PROC-14.1.15

    Implementation notes:
        - The audited equation (44) implementation is reused directly.
        - No alternate interaction equation is introduced.
    """
    return elastic_web_equivalent_stress_checks_eq44(
        sigma_wx_n_mm2, sigma_wy_n_mm2, tau_wxy_n_mm2,
        butt_weld_yield_resistance_n_mm2, butt_weld_shear_resistance_n_mm2,
        working_condition_factor,
    )


def fillet_weld_effective_length_clause_14_1_16(total_segment_lengths_mm: list[float]) -> float:
    """
    Summary:
        Calculate total design length of a fillet-weld connection after deducting 10 mm per continuous segment.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.16
        Annex: None
        Equation/Table: Effective fillet-weld length rule
        Audit ID: SP16-PROC-14.1.16-FILLET-LENGTH
        Normative status: normative

    Mathematical form:
        lw=sum(max(Li-10 mm,0)) for each continuous segment.

    Parameters:
        total_segment_lengths_mm: Positive full lengths of all continuous weld segments.

    Returns:
        Type: float
        Unit: mm
        Meaning: Summed design length lw.

    Assumptions:
        - Each list item is one continuous weld segment.

    Sign convention:
        - Lengths are positive.

    Unit convention:
        - mm; the printed 1 cm deduction is represented as 10 mm.

    Applicability:
        - Equations (176)-(177).

    Limitations:
        - Does not verify the minimum 40 mm or 4kf segment length.

    Raises:
        ValueError: List is empty or a segment does not remain positive after deduction.
        TypeError: Input is not a list of real values.

    Examples:
        >>> fillet_weld_effective_length_clause_14_1_16([100, 80])
        160.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_fillet_effective_length_and_plane
        Validation cases:
            - V15-PROC-14.1.16-LENGTH

    Implementation notes:
        - A segment not exceeding 10 mm is rejected rather than assigned zero capacity.
        - No hidden segment merging is performed.
    """
    if not isinstance(total_segment_lengths_mm, list) or not total_segment_lengths_mm:
        raise ValueError("total_segment_lengths_mm must be a non-empty list")
    effective = 0.0
    for index, value in enumerate(total_segment_lengths_mm):
        length = _positive(value, f"total_segment_lengths_mm[{index}]")
        if length <= 10.0:
            raise ValueError("every continuous segment must exceed the 10 mm deduction")
        effective += length - 10.0
    return effective


def fillet_weld_governing_plane_clause_14_1_16(beta_f: float, weld_metal_resistance_n_mm2: float,
                                                beta_z: float, fusion_boundary_resistance_n_mm2: float) -> str:
    """
    Summary:
        Select the governing fillet-weld calculation plane from the clause 14.1.16 ratio.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.16
        Annex: None
        Equation/Table: Routing condition before equations (176)-(177)
        Audit ID: SP16-PROC-14.1.16-GOVERNING-PLANE
        Normative status: normative

    Mathematical form:
        weld metal when beta_f*Rwf/(beta_z*Rwz)<=1; fusion boundary otherwise.

    Parameters:
        beta_f: Table 39 weld-metal coefficient.
        weld_metal_resistance_n_mm2: Rwf.
        beta_z: Table 39 fusion-boundary coefficient.
        fusion_boundary_resistance_n_mm2: Rwz.

    Returns:
        Type: str
        Unit: route identifier
        Meaning: weld_metal or fusion_boundary.

    Assumptions:
        - Coefficients and resistances correspond to the same weld.

    Sign convention:
        - All inputs are positive magnitudes.

    Unit convention:
        - Resistances use N/mm2; ratio is dimensionless.

    Applicability:
        - Clause 14.1.16.

    Limitations:
        - The function selects one plane; both utilizations may still be reported for auditability.

    Raises:
        ValueError: Any denominator input is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_governing_plane_clause_14_1_16(0.7, 180, 1.0, 200)
        'weld_metal'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_fillet_effective_length_and_plane
        Validation cases:
            - V15-PROC-14.1.16-PLANE

    Implementation notes:
        - Equality follows the equation (176) branch.
        - No tolerance is inserted.
    """
    ratio = (_positive(beta_f, "beta_f") * _positive(weld_metal_resistance_n_mm2, "weld_metal_resistance_n_mm2") /
             (_positive(beta_z, "beta_z") * _positive(fusion_boundary_resistance_n_mm2, "fusion_boundary_resistance_n_mm2")))
    return "weld_metal" if ratio <= 1.0 else "fusion_boundary"


def fillet_weld_axial_metal_utilization_eq176(axial_force_n: float, beta_f: float, weld_leg_mm: float,
                                               design_weld_length_mm: float, weld_metal_resistance_n_mm2: float,
                                               working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld axial utilization on the weld-metal plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.16
        Annex: None
        Equation/Table: Equation (176)
        Audit ID: SP16-EQ-176
        Normative status: normative

    Mathematical form:
        eta=|N|/(beta_f*kf*lw*Rwf*gamma_c).

    Parameters:
        axial_force_n: Axial force N.
        beta_f: Table 39 coefficient.
        weld_leg_mm: kf.
        design_weld_length_mm: lw.
        weld_metal_resistance_n_mm2: Rwf.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (176) utilization.

    Assumptions:
        - Force passes through the weld-group centroid.

    Sign convention:
        - Force magnitude is checked.

    Unit convention:
        - N, mm, and N/mm2.

    Applicability:
        - The weld-metal route of clause 14.1.16.

    Limitations:
        - Does not calculate beta_f or effective length.

    Raises:
        ValueError: Denominator input is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_axial_metal_utilization_eq176(100000, 0.7, 8, 200, 180, 1)
        0.49603174603174605

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq176_177_normal_zero_and_sign
        Validation cases:
            - V15-EQ-176

    Implementation notes:
        - The result is not clipped.
        - No defaults are applied.
    """
    return abs(_real(axial_force_n, "axial_force_n")) / (
        _positive(beta_f, "beta_f") * _positive(weld_leg_mm, "weld_leg_mm") *
        _positive(design_weld_length_mm, "design_weld_length_mm") *
        _positive(weld_metal_resistance_n_mm2, "weld_metal_resistance_n_mm2") *
        _positive(working_condition_factor, "working_condition_factor"))


def fillet_weld_axial_fusion_utilization_eq177(axial_force_n: float, beta_z: float, weld_leg_mm: float,
                                                design_weld_length_mm: float, fusion_boundary_resistance_n_mm2: float,
                                                working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld axial utilization on the fusion-boundary plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.16
        Annex: None
        Equation/Table: Equation (177)
        Audit ID: SP16-EQ-177
        Normative status: normative

    Mathematical form:
        eta=|N|/(beta_z*kf*lw*Rwz*gamma_c).

    Parameters:
        axial_force_n: Axial force N.
        beta_z: Table 39 coefficient.
        weld_leg_mm: kf.
        design_weld_length_mm: lw.
        fusion_boundary_resistance_n_mm2: Rwz.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (177) utilization.

    Assumptions:
        - Force passes through the weld-group centroid.

    Sign convention:
        - Force magnitude is checked.

    Unit convention:
        - N, mm, and N/mm2.

    Applicability:
        - The fusion-boundary route of clause 14.1.16.

    Limitations:
        - Does not calculate beta_z or effective length.

    Raises:
        ValueError: Denominator input is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_axial_fusion_utilization_eq177(100000, 1, 8, 200, 200, 1)
        0.3125

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq176_177_normal_zero_and_sign
        Validation cases:
            - V15-EQ-177

    Implementation notes:
        - The result is not clipped.
        - No defaults are applied.
    """
    return abs(_real(axial_force_n, "axial_force_n")) / (
        _positive(beta_z, "beta_z") * _positive(weld_leg_mm, "weld_leg_mm") *
        _positive(design_weld_length_mm, "design_weld_length_mm") *
        _positive(fusion_boundary_resistance_n_mm2, "fusion_boundary_resistance_n_mm2") *
        _positive(working_condition_factor, "working_condition_factor"))


def fillet_weld_out_of_plane_moment_metal_utilization_eq178(moment_n_mm: float, weld_section_modulus_mm3: float,
                                                              weld_metal_resistance_n_mm2: float,
                                                              working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld utilization for a moment perpendicular to the weld plane on the weld-metal section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.17
        Annex: None
        Equation/Table: Equation (178)
        Audit ID: SP16-EQ-178
        Normative status: normative

    Mathematical form:
        eta=|M|/(Wf*Rwf*gamma_c).

    Parameters:
        moment_n_mm: Moment M in N*mm.
        weld_section_modulus_mm3: Wf in mm3.
        weld_metal_resistance_n_mm2: Rwf.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (178) utilization.

    Assumptions:
        - Wf corresponds to the weld-metal design section.

    Sign convention:
        - Moment magnitude is checked.

    Unit convention:
        - N*mm, mm3, N/mm2.

    Applicability:
        - Clause 14.1.17 weld-metal section.

    Limitations:
        - Section modulus recovery is external.

    Raises:
        ValueError: Denominator input is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_out_of_plane_moment_metal_utilization_eq178(1000000, 10000, 200, 1)
        0.5

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq178_179_normal_zero_and_sign
        Validation cases:
            - V15-EQ-178

    Implementation notes:
        - No governing-plane selection is hidden inside this function.
        - The result is not clipped.
    """
    return abs(_real(moment_n_mm, "moment_n_mm")) / (_positive(weld_section_modulus_mm3, "weld_section_modulus_mm3") *
                                                        _positive(weld_metal_resistance_n_mm2, "weld_metal_resistance_n_mm2") *
                                                        _positive(working_condition_factor, "working_condition_factor"))


def fillet_weld_out_of_plane_moment_fusion_utilization_eq179(moment_n_mm: float, fusion_section_modulus_mm3: float,
                                                               fusion_boundary_resistance_n_mm2: float,
                                                               working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld utilization for a moment perpendicular to the weld plane on the fusion-boundary section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.17
        Annex: None
        Equation/Table: Equation (179)
        Audit ID: SP16-EQ-179
        Normative status: normative

    Mathematical form:
        eta=|M|/(Wz*Rwz*gamma_c).

    Parameters:
        moment_n_mm: Moment M in N*mm.
        fusion_section_modulus_mm3: Wz in mm3.
        fusion_boundary_resistance_n_mm2: Rwz.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (179) utilization.

    Assumptions:
        - Wz corresponds to the fusion-boundary design section.

    Sign convention:
        - Moment magnitude is checked.

    Unit convention:
        - N*mm, mm3, N/mm2.

    Applicability:
        - Clause 14.1.17 fusion-boundary section.

    Limitations:
        - Section modulus recovery is external.

    Raises:
        ValueError: Denominator input is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_out_of_plane_moment_fusion_utilization_eq179(1000000, 10000, 200, 1)
        0.5

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq178_179_normal_zero_and_sign
        Validation cases:
            - V15-EQ-179

    Implementation notes:
        - No governing-plane selection is hidden inside this function.
        - The result is not clipped.
    """
    return abs(_real(moment_n_mm, "moment_n_mm")) / (_positive(fusion_section_modulus_mm3, "fusion_section_modulus_mm3") *
                                                        _positive(fusion_boundary_resistance_n_mm2, "fusion_boundary_resistance_n_mm2") *
                                                        _positive(working_condition_factor, "working_condition_factor"))


def _in_plane_moment_utilization(moment_n_mm: float, x_mm: float, y_mm: float, inertia_x_mm4: float,
                                 inertia_y_mm4: float, resistance_n_mm2: float, gamma_c: float) -> float:
    radius = math.hypot(_real(x_mm, "x_mm"), _real(y_mm, "y_mm"))
    return abs(_real(moment_n_mm, "moment_n_mm")) * radius / (
        (_positive(inertia_x_mm4, "inertia_x_mm4") + _positive(inertia_y_mm4, "inertia_y_mm4")) *
        _positive(resistance_n_mm2, "resistance_n_mm2") * _positive(gamma_c, "gamma_c"))


def fillet_weld_in_plane_moment_metal_utilization_eq180(moment_n_mm: float, x_mm: float, y_mm: float,
                                                          inertia_fx_mm4: float, inertia_fy_mm4: float,
                                                          weld_metal_resistance_n_mm2: float,
                                                          working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld in-plane moment utilization on the weld-metal section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.18
        Annex: None
        Equation/Table: Equation (180)
        Audit ID: SP16-EQ-180
        Normative status: normative

    Mathematical form:
        eta=|M|*sqrt(x^2+y^2)/((Ifx+Ify)*Rwf*gamma_c).

    Parameters:
        moment_n_mm: Moment M.
        x_mm: Signed x coordinate of the governing point.
        y_mm: Signed y coordinate of the governing point.
        inertia_fx_mm4: Ifx.
        inertia_fy_mm4: Ify.
        weld_metal_resistance_n_mm2: Rwf.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (180) utilization.

    Assumptions:
        - The point is the most remote point of the weld design section.

    Sign convention:
        - Coordinate signs vanish through the radial distance; moment magnitude is checked.

    Unit convention:
        - N*mm, mm, mm4, N/mm2.

    Applicability:
        - Clause 14.1.18 weld-metal section.

    Limitations:
        - Governing-point search and inertia calculation are external.

    Raises:
        ValueError: Denominator input is non-positive or values are non-finite.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_in_plane_moment_metal_utilization_eq180(1000000, 30, 40, 100000, 100000, 200, 1)
        0.00125

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq180_181_normal_zero_and_sign
        Validation cases:
            - V15-EQ-180

    Implementation notes:
        - The printed sum Ifx+Ify is retained.
        - The result is not clipped.
    """
    return _in_plane_moment_utilization(moment_n_mm, x_mm, y_mm, inertia_fx_mm4, inertia_fy_mm4,
                                        weld_metal_resistance_n_mm2, working_condition_factor)


def fillet_weld_in_plane_moment_fusion_utilization_eq181(moment_n_mm: float, x_mm: float, y_mm: float,
                                                           inertia_zx_mm4: float, inertia_zy_mm4: float,
                                                           fusion_boundary_resistance_n_mm2: float,
                                                           working_condition_factor: float) -> float:
    """
    Summary:
        Calculate fillet-weld in-plane moment utilization on the fusion-boundary section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.18
        Annex: None
        Equation/Table: Equation (181)
        Audit ID: SP16-EQ-181
        Normative status: normative

    Mathematical form:
        eta=|M|*sqrt(x^2+y^2)/((Izx+Izy)*Rwz*gamma_c).

    Parameters:
        moment_n_mm: Moment M.
        x_mm: Signed x coordinate of the governing point.
        y_mm: Signed y coordinate of the governing point.
        inertia_zx_mm4: Izx.
        inertia_zy_mm4: Izy.
        fusion_boundary_resistance_n_mm2: Rwz.
        working_condition_factor: gamma_c.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (181) utilization.

    Assumptions:
        - The point is the most remote point of the fusion-boundary design section.

    Sign convention:
        - Coordinate signs vanish through radial distance; moment magnitude is checked.

    Unit convention:
        - N*mm, mm, mm4, N/mm2.

    Applicability:
        - Clause 14.1.18 fusion-boundary section.

    Limitations:
        - Governing-point search and inertia calculation are external.

    Raises:
        ValueError: Denominator input is non-positive or values are non-finite.
        TypeError: Inputs are not real.

    Examples:
        >>> fillet_weld_in_plane_moment_fusion_utilization_eq181(1000000, 30, 40, 100000, 100000, 200, 1)
        0.00125

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq180_181_normal_zero_and_sign
        Validation cases:
            - V15-EQ-181

    Implementation notes:
        - The printed sum Izx+Izy is retained.
        - The result is not clipped.
    """
    return _in_plane_moment_utilization(moment_n_mm, x_mm, y_mm, inertia_zx_mm4, inertia_zy_mm4,
                                        fusion_boundary_resistance_n_mm2, working_condition_factor)


def combined_fillet_weld_utilizations_eq182(tau_f_n_mm2: float, tau_z_n_mm2: float,
                                              weld_metal_resistance_n_mm2: float,
                                              fusion_boundary_resistance_n_mm2: float,
                                              working_condition_factor: float) -> dict[str, float | bool]:
    """
    Summary:
        Check simultaneous fillet-weld stresses on weld-metal and fusion-boundary sections.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.19
        Annex: None
        Equation/Table: Equation (182)
        Audit ID: SP16-EQ-182
        Normative status: normative

    Mathematical form:
        eta_f=|tau_f|/(Rwf*gamma_c); eta_z=|tau_z|/(Rwz*gamma_c).

    Parameters:
        tau_f_n_mm2: Resultant weld-metal shear stress.
        tau_z_n_mm2: Resultant fusion-boundary shear stress.
        weld_metal_resistance_n_mm2: Rwf.
        fusion_boundary_resistance_n_mm2: Rwz.
        working_condition_factor: gamma_c.

    Returns:
        Type: dict[str, float | bool]
        Unit: dimensionless
        Meaning: Two utilizations and pass statuses.

    Assumptions:
        - Stresses were obtained from equation (183) for each design plane.

    Sign convention:
        - Stress magnitudes are checked.

    Unit convention:
        - N/mm2.

    Applicability:
        - Simultaneous N, V, and M under clause 14.1.19.

    Limitations:
        - Stress components are external inputs.

    Raises:
        ValueError: Resistance or factor is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> combined_fillet_weld_utilizations_eq182(100, 80, 200, 160, 1)["governing_utilization"]
        0.5

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq182_normal_zero_and_sign
        Validation cases:
            - V15-EQ-182

    Implementation notes:
        - Both printed conditions are retained.
        - No single equivalent resistance is invented.
    """
    gamma = _positive(working_condition_factor, "working_condition_factor")
    eta_f = abs(_real(tau_f_n_mm2, "tau_f_n_mm2")) / (_positive(weld_metal_resistance_n_mm2, "weld_metal_resistance_n_mm2") * gamma)
    eta_z = abs(_real(tau_z_n_mm2, "tau_z_n_mm2")) / (_positive(fusion_boundary_resistance_n_mm2, "fusion_boundary_resistance_n_mm2") * gamma)
    return {"weld_metal_utilization": eta_f, "fusion_boundary_utilization": eta_z,
            "governing_utilization": max(eta_f, eta_z), "weld_metal_pass": eta_f <= 1.0,
            "fusion_boundary_pass": eta_z <= 1.0, "pass": eta_f <= 1.0 and eta_z <= 1.0}


def resultant_shear_stress_eq183(tau_n_n_mm2: float, tau_mx_n_mm2: float,
                                  tau_v_n_mm2: float, tau_my_n_mm2: float) -> float:
    """
    Summary:
        Calculate resultant shear stress from axial, transverse-force, and moment components.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.19
        Annex: None
        Equation/Table: Equation (183)
        Audit ID: SP16-EQ-183
        Normative status: normative

    Mathematical form:
        tau=sqrt((tau_N+tau_Mx)^2+(tau_V+tau_My)^2).

    Parameters:
        tau_n_n_mm2: Signed stress component tau_N.
        tau_mx_n_mm2: Signed stress component tau_Mx.
        tau_v_n_mm2: Signed stress component tau_V.
        tau_my_n_mm2: Signed stress component tau_My.

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Resultant shear stress tau.

    Assumptions:
        - Components are evaluated at the same weld-group point and design plane.

    Sign convention:
        - Component signs are retained before vector summation.

    Unit convention:
        - N/mm2.

    Applicability:
        - Equation (182) input under clause 14.1.19.

    Limitations:
        - Component recovery is external.

    Raises:
        ValueError: Any component is non-finite.
        TypeError: Any component is not real.

    Examples:
        >>> resultant_shear_stress_eq183(3, 1, 4, -1)
        5.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq183_normal_zero_and_sign
        Validation cases:
            - V15-EQ-183

    Implementation notes:
        - Algebraic component cancellation is preserved.
        - No absolute value is applied before component addition.
    """
    x = _real(tau_n_n_mm2, "tau_n_n_mm2") + _real(tau_mx_n_mm2, "tau_mx_n_mm2")
    y = _real(tau_v_n_mm2, "tau_v_n_mm2") + _real(tau_my_n_mm2, "tau_my_n_mm2")
    return math.hypot(x, y)


def spot_weld_shear_capacity_eq184(spot_diameter_mm: float, normative_weld_metal_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate the shear limit of one arc spot weld.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.20
        Annex: None
        Equation/Table: Equation (184)
        Audit ID: SP16-EQ-184
        Normative status: normative

    Mathematical form:
        Ns=0.28*d^2*Rwun.

    Parameters:
        spot_diameter_mm: Spot-weld diameter d in the connected-element plane.
        normative_weld_metal_ultimate_resistance_n_mm2: Rwun.

    Returns:
        Type: float
        Unit: N
        Meaning: Shear limit Ns of one spot.

    Assumptions:
        - Diameter is selected from applicable welding standards.

    Sign convention:
        - Capacity is positive.

    Unit convention:
        - mm and N/mm2 produce N.

    Applicability:
        - Through-penetration arc spot weld in elements up to 4 mm thick.

    Limitations:
        - Does not verify the 4 mm thickness applicability.

    Raises:
        ValueError: Diameter or resistance is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> spot_weld_shear_capacity_eq184(10, 400)
        11200.000000000002

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq184_normal_boundary_and_units
        Validation cases:
            - V15-EQ-184

    Implementation notes:
        - The printed coefficient 0.28 is retained.
        - No rounding is applied.
    """
    d = _positive(spot_diameter_mm, "spot_diameter_mm")
    return 0.28 * d * d * _positive(normative_weld_metal_ultimate_resistance_n_mm2, "normative_weld_metal_ultimate_resistance_n_mm2")


def spot_weld_tearout_capacity_eq185(beta: float, spot_diameter_mm: float, thinner_element_thickness_mm: float,
                                     normative_connected_steel_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate the tear-out limit of one arc spot weld.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.20
        Annex: None
        Equation/Table: Equation (185)
        Audit ID: SP16-EQ-185
        Normative status: normative

    Mathematical form:
        Nt=beta*d*t*Run.

    Parameters:
        beta: Thickness-ratio coefficient.
        spot_diameter_mm: Spot diameter d.
        thinner_element_thickness_mm: Smaller thickness t.
        normative_connected_steel_ultimate_resistance_n_mm2: Run.

    Returns:
        Type: float
        Unit: N
        Meaning: Tear-out limit Nt of one spot.

    Assumptions:
        - beta was determined from the connected-element thickness ratio.

    Sign convention:
        - Capacity is positive.

    Unit convention:
        - mm and N/mm2 produce N.

    Applicability:
        - Through-penetration arc spot weld in elements up to 4 mm thick.

    Limitations:
        - Does not select beta or verify thickness applicability.

    Raises:
        ValueError: Any magnitude is non-positive.
        TypeError: Inputs are not real.

    Examples:
        >>> spot_weld_tearout_capacity_eq185(1.1, 10, 2, 400)
        8800.0

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_eq185_normal_boundary_and_units
        Validation cases:
            - V15-EQ-185

    Implementation notes:
        - The capacity is not clipped by equation (184) inside this function.
        - No default beta is inserted.
    """
    return (_positive(beta, "beta") * _positive(spot_diameter_mm, "spot_diameter_mm") *
            _positive(thinner_element_thickness_mm, "thinner_element_thickness_mm") *
            _positive(normative_connected_steel_ultimate_resistance_n_mm2, "normative_connected_steel_ultimate_resistance_n_mm2"))


def spot_weld_beta_clause_14_1_20(first_thickness_mm: float, second_thickness_mm: float) -> float:
    """
    Summary:
        Determine the arc spot-weld beta coefficient by the connected-thickness ratio.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.20
        Annex: None
        Equation/Table: beta=1.1 at equal thickness and beta=1.9 at ratio at least 2, with interpolation between
        Audit ID: SP16-PROC-14.1.20-SPOT-BETA
        Normative status: normative

    Mathematical form:
        beta=1.1+0.8*(ratio-1) for 1<=ratio<2; beta=1.9 for ratio>=2.

    Parameters:
        first_thickness_mm: First element thickness.
        second_thickness_mm: Second element thickness.

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Coefficient beta.

    Assumptions:
        - The clause instruction to interpolate is implemented as linear interpolation.

    Sign convention:
        - Thicknesses and beta are positive.

    Unit convention:
        - Thickness ratio is dimensionless.

    Applicability:
        - Equation (185).

    Limitations:
        - The standard does not separately print an interpolation formula; linear interpolation is explicitly documented here.

    Raises:
        ValueError: Thickness is non-positive.
        TypeError: Thickness is not real.

    Examples:
        >>> spot_weld_beta_clause_14_1_20(2, 3)
        1.5

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_spot_beta_and_governing_capacity
        Validation cases:
            - V15-PROC-14.1.20-BETA

    Implementation notes:
        - Ratio is always larger thickness divided by smaller thickness.
        - The upper branch is capped at the printed value 1.9.
    """
    first = _positive(first_thickness_mm, "first_thickness_mm")
    second = _positive(second_thickness_mm, "second_thickness_mm")
    ratio = max(first, second) / min(first, second)
    if ratio >= 2.0:
        return 1.9
    return 1.1 + 0.8 * (ratio - 1.0)


def spot_weld_governing_capacity_clause_14_1_20(
    first_thickness_mm: float,
    second_thickness_mm: float,
    spot_diameter_mm: float,
    normative_weld_metal_ultimate_resistance_n_mm2: float,
    normative_connected_steel_ultimate_resistance_n_mm2: float,
) -> dict[str, float | str]:
    """
    Summary:
        Calculate both arc spot-weld limits and return the smaller governing capacity.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.20
        Annex: None
        Equation/Table: Equations (184)-(185)
        Audit ID: SP16-PROC-14.1.20-SPOT-CAPACITY
        Normative status: normative

    Mathematical form:
        capacity=min(Ns,Nt).

    Parameters:
        first_thickness_mm: First thickness, not exceeding 4 mm for applicability.
        second_thickness_mm: Second thickness, not exceeding 4 mm for applicability.
        spot_diameter_mm: Spot diameter d.
        normative_weld_metal_ultimate_resistance_n_mm2: Rwun.
        normative_connected_steel_ultimate_resistance_n_mm2: Run.

    Returns:
        Type: dict[str, float | str]
        Unit: N and route identifier
        Meaning: Ns, Nt, beta, governing capacity, and governing mode.

    Assumptions:
        - The spot weld is an arc through-penetration spot covered by 14.1.20.

    Sign convention:
        - Capacities are positive.

    Unit convention:
        - mm, N/mm2, and N.

    Applicability:
        - Both connected elements have thickness not exceeding 4 mm.

    Limitations:
        - Diameter selection from external welding standards remains external.

    Raises:
        ValueError: A thickness exceeds 4 mm or an input is invalid.
        TypeError: Inputs are not real.

    Examples:
        >>> spot_weld_governing_capacity_clause_14_1_20(2, 2, 10, 400, 400)["governing_mode"]
        'tearout'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_spot_beta_and_governing_capacity
        Validation cases:
            - V15-PROC-14.1.20-CAPACITY

    Implementation notes:
        - Both equation results remain visible.
        - No hidden safety factor is added.
    """
    first = _positive(first_thickness_mm, "first_thickness_mm")
    second = _positive(second_thickness_mm, "second_thickness_mm")
    if max(first, second) > 4.0:
        raise ValueError("Clause 14.1.20 applies to connected elements up to 4 mm thick")
    beta = spot_weld_beta_clause_14_1_20(first, second)
    shear = spot_weld_shear_capacity_eq184(spot_diameter_mm, normative_weld_metal_ultimate_resistance_n_mm2)
    tearout = spot_weld_tearout_capacity_eq185(beta, spot_diameter_mm, min(first, second),
                                               normative_connected_steel_ultimate_resistance_n_mm2)
    return {"beta": beta, "shear_capacity_n": shear, "tearout_capacity_n": tearout,
            "governing_capacity_n": min(shear, tearout),
            "governing_mode": "shear" if shear <= tearout else "tearout"}


def brittle_fracture_factor_register_clause_13_1() -> dict[str, str]:
    """
    Summary:
        Return the four factor groups explicitly listed by current SP16 clause 13.1.
    Standard reference:
        СП 16.13330.2017, Changes No. 1-6 through 09.12.2024, clause 13.1.
    Mathematical form:
        Qualitative four-factor register; no scalar equation is defined by clause 13.1.
    Parameters:
        None.
    Returns:
        Stable identifiers for the four printed adverse-factor groups.
    Assumptions:
        Project-specific exposure and detail evidence are supplied by the engineer.
    Sign convention:
        Not applicable.
    Unit convention:
        Not applicable.
    Applicability:
        Current-SP16 brittle-fracture prevention review under clause 13.1.
    Limitations:
        The function does not infer temperature, stress concentration, load dynamics or material toughness from geometry or analysis models.
    Raises:
        No normal-use exceptions.
    Examples:
        >>> len(brittle_fracture_factor_register_clause_13_1())
        4
    Tests:
        tests/test_stage_n10_brittle_fracture_workflows.py and tests/test_brittle_fracture_and_welded_connections.py.
    Implementation notes:
        Previous compatibility code split material toughness, residual welding stress and thickness effects into extra top-level factors. Stage N10 removes that over-classification and retains only the four groups printed in clause 13.1.
    """
    return {
        "low_temperature": "Reduced temperature with steel chemistry, structure and rolled-product thickness effects.",
        "dynamic_or_impact_action": "Moving, dynamic and vibratory actions.",
        "high_local_stress": "High local stresses from concentrated action, connection deformation, welding and residual stresses.",
        "stress_concentration": "Stress concentrators oriented transverse to the direction of tensile stress.",
    }

def through_thickness_property_test_route_clause_13_4(test_result_available: bool) -> dict[str, str | bool]:
    """
    Summary:
        Classify whether through-thickness ductility evidence is available for clause 13.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 13.4
        Annex: None
        Equation/Table: None
        Audit ID: SP16-PROC-13.4-Z-TEST-ROUTE
        Normative status: normative

    Mathematical form:
        Boolean routing to verified test evidence or external-reference requirement.

    Parameters:
        test_result_available:
            Type: bool
            Unit: dimensionless
            Meaning: Whether verified through-thickness tensile-test evidence is available.
            Valid range: True or False
            Source: material certificate or test report

    Returns:
        Type: dict[str, str | bool]
        Unit: not applicable
        Meaning: Route status and required evidence statement.

    Assumptions:
        - The evidence corresponds to the actual product and thickness.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Any Z-property percentage remains in the external test record.

    Applicability:
        - Rolled products susceptible to lamellar tearing.

    Limitations:
        - The function does not interpret laboratory raw data.

    Raises:
        TypeError: The flag is not Boolean.

    Examples:
        >>> through_thickness_property_test_route_clause_13_4(False)["status"]
        'external_reference_required'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_through_thickness_test_route
        Validation cases:
            - V15-PROC-13.4

    Implementation notes:
        - Absence of evidence is not converted to an assumed Z class.
        - Test acceptance remains traceable to the applicable product standard.
    """
    if not isinstance(test_result_available, bool):
        raise TypeError("test_result_available must be bool")
    return {
        "test_result_available": test_result_available,
        "status": "evidence_available" if test_result_available else "external_reference_required",
        "required_evidence": "Verified through-thickness tensile-test result and declared Z quality.",
    }


def welded_connection_detailing_checklist_clause_14_1_1_14_1_6(checks: dict[str, bool]) -> dict[str, Any]:
    """
    Summary:
        Evaluate explicit detailing confirmations required before welded-connection resistance checks.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.1-14.1.6
        Annex: None
        Equation/Table: None
        Audit ID: SP16-PROC-14.1.1-14.1.6-DETAILING
        Normative status: normative

    Mathematical form:
        all(checks.values()).

    Parameters:
        checks:
            Type: dict[str, bool]
            Unit: dimensionless
            Meaning: Named confirmations for weld type, dimensions, consumables, accessibility, and detailing.
            Valid range: Non-empty mapping with Boolean values
            Source: project documentation

    Returns:
        Type: dict[str, Any]
        Unit: counts and Boolean status
        Meaning: Overall status and failed confirmation names.

    Assumptions:
        - Each key identifies a documented project check.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Not applicable.

    Applicability:
        - Welded connections before formula-based resistance verification.

    Limitations:
        - The checklist cannot inspect drawings or welding procedures automatically.

    Raises:
        TypeError: The input is not a mapping or contains non-Boolean values.
        ValueError: The mapping is empty.

    Examples:
        >>> welded_connection_detailing_checklist_clause_14_1_1_14_1_6({"weld_type": True})["passed"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_welded_detailing_checklist
        Validation cases:
            - V15-PROC-14.1.1-14.1.6

    Implementation notes:
        - The function records evidence rather than inferring compliance.
        - Missing checks are not silently treated as passed.
    """
    if not isinstance(checks, dict):
        raise TypeError("checks must be a dict")
    if not checks:
        raise ValueError("checks must not be empty")
    if any(not isinstance(value, bool) for value in checks.values()):
        raise TypeError("all check values must be bool")
    failed = sorted(name for name, value in checks.items() if not value)
    return {"passed": not failed, "checked_count": len(checks), "failed_checks": failed}


def one_sided_fillet_weld_route_clause_14_1_9(
    one_sided_weld: bool,
    cyclic_or_dynamic_action: bool,
    root_tension_or_peeling_possible: bool,
) -> dict[str, str | bool]:
    """
    Summary:
        Route a one-sided fillet-weld proposal through the clause 14.1.9 applicability gate.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.9
        Annex: None
        Equation/Table: None
        Audit ID: SP16-PROC-14.1.9-ONE-SIDED-ROUTE
        Normative status: normative

    Mathematical form:
        Non-one-sided welds pass this gate. One-sided welds are fail-closed because the legacy three-flag API cannot encode the complete current clause 14.1.9 project-condition set.

    Parameters:
        one_sided_weld: Whether the joint uses a one-sided fillet weld.
        cyclic_or_dynamic_action: Whether cyclic or dynamic action governs.
        root_tension_or_peeling_possible: Whether tension across the root or peeling is possible.

    Returns:
        Type: dict[str, str | bool]
        Unit: not applicable
        Meaning: Applicability status and route.

    Assumptions:
        - The flags are established from the actual load path and detail.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Boolean inputs are dimensionless.

    Applicability:
        - Selection of one-sided fillet welds.

    Limitations:
        - The legacy three-argument API cannot establish all current clause 14.1.9 project conditions. One-sided proposals therefore require an external/full applicability assessment and are not positively accepted by this helper.

    Raises:
        TypeError: Any input is not Boolean.

    Examples:
        >>> one_sided_fillet_weld_route_clause_14_1_9(True, True, False)["accepted"]
        False

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_one_sided_weld_route
        Validation cases:
            - V15-PROC-14.1.9

    Implementation notes:
        - Rejection remains an explicit route, not a numerical penalty.
        - No unstated exception is applied.
    """
    values = (one_sided_weld, cyclic_or_dynamic_action, root_tension_or_peeling_possible)
    if any(not isinstance(value, bool) for value in values):
        raise TypeError("all inputs must be bool")
    if not one_sided_weld:
        return {
            "accepted": True,
            "route": "standard_resistance_check",
            "one_sided_weld": False,
            "full_clause_14_1_9_project_conditions_required": False,
        }
    # The current three-flag public API does not carry the complete Change-6
    # project-condition set required by clause 14.1.9 (responsibility class,
    # environment/heated-interior status, construction group/purpose and the
    # enumerated prohibitions). It must therefore not positively accept a
    # one-sided weld. Preserve explicit legacy red flags, but otherwise fail
    # closed and require the full project applicability assessment externally.
    if cyclic_or_dynamic_action or root_tension_or_peeling_possible:
        route = "detail_not_accepted_by_selected_route"
        reason = "legacy_risk_flag_triggered"
    else:
        route = "full_clause_14_1_9_project_conditions_required"
        reason = "insufficient_inputs_for_current_clause_14_1_9_positive_acceptance"
    return {
        "accepted": False,
        "route": route,
        "reason": reason,
        "one_sided_weld": True,
        "full_clause_14_1_9_project_conditions_required": True,
    }


def intermittent_weld_applicability_clause_14_1_10(
    intermittent_weld_requested: bool,
    joint_transfers_force: bool,
    corrosion_or_sealing_requires_continuity: bool,
) -> dict[str, str | bool]:
    """
    Summary:
        Determine whether an intermittent-weld route may proceed to spacing checks.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.10
        Annex: None
        Equation/Table: None
        Audit ID: SP16-PROC-14.1.10-INTERMITTENT-ROUTE
        Normative status: normative

    Mathematical form:
        proceed = not requested or not corrosion_or_sealing_requires_continuity.

    Parameters:
        intermittent_weld_requested: Whether intermittent welds are proposed.
        joint_transfers_force: Whether the joint transfers design force.
        corrosion_or_sealing_requires_continuity: Whether continuous sealing/protection is required.

    Returns:
        Type: dict[str, str | bool]
        Unit: not applicable
        Meaning: Route and whether force/spatial checks remain required.

    Assumptions:
        - Environmental and fabrication requirements have been reviewed.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Boolean inputs are dimensionless.

    Applicability:
        - Intermittent fillet weld detailing.

    Limitations:
        - The procedure does not establish fatigue suitability.

    Raises:
        TypeError: Any input is not Boolean.

    Examples:
        >>> intermittent_weld_applicability_clause_14_1_10(True, True, False)["proceed_to_spacing_check"]
        True

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_intermittent_weld_route
        Validation cases:
            - V15-PROC-14.1.10-ROUTE

    Implementation notes:
        - Resistance and spacing checks remain separate.
        - The function does not assume environmental acceptability.
    """
    values = (intermittent_weld_requested, joint_transfers_force, corrosion_or_sealing_requires_continuity)
    if any(not isinstance(value, bool) for value in values):
        raise TypeError("all inputs must be bool")
    accepted = (not intermittent_weld_requested) or not corrosion_or_sealing_requires_continuity
    return {
        "accepted": accepted,
        "proceed_to_spacing_check": accepted and intermittent_weld_requested,
        "force_resistance_check_required": joint_transfers_force,
        "route": "spacing_and_resistance_checks" if accepted else "continuous_weld_required",
    }


def perimeter_or_plug_weld_route_clause_14_1_11_14_1_12(
    weld_type: str,
    perimeter_is_closed: bool,
) -> dict[str, str | bool]:
    """
    Summary:
        Route perimeter and plug weld details to the applicable clause-specific checks.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.11-14.1.12
        Annex: None
        Equation/Table: None
        Audit ID: SP16-PROC-14.1.11-PERIMETER-WELD-ROUTE
        Normative status: normative

    Mathematical form:
        Discrete route for perimeter or plug weld.

    Parameters:
        weld_type: "perimeter" or "plug".
        perimeter_is_closed: Whether a perimeter weld forms a closed contour.

    Returns:
        Type: dict[str, str | bool]
        Unit: not applicable
        Meaning: Applicable route and required follow-up check.

    Assumptions:
        - The weld type is established from the detail.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Not applicable.

    Applicability:
        - Clauses 14.1.11 and 14.1.12.

    Limitations:
        - Geometric dimensions are checked by the dedicated plug-weld function.

    Raises:
        ValueError: weld_type is unsupported.
        TypeError: Inputs have invalid types.

    Examples:
        >>> perimeter_or_plug_weld_route_clause_14_1_11_14_1_12("plug", False)["route"]
        'plug_weld_dimension_check'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_perimeter_or_plug_route
        Validation cases:
            - V15-PROC-14.1.11-14.1.12

    Implementation notes:
        - A plug weld is never reclassified as a perimeter weld.
        - The route contains no hidden resistance value.
    """
    selected = _choice(weld_type, {"perimeter", "plug"}, "weld_type")
    if not isinstance(perimeter_is_closed, bool):
        raise TypeError("perimeter_is_closed must be bool")
    if selected == "plug":
        return {"accepted": True, "route": "plug_weld_dimension_check", "closed_contour": False}
    return {
        "accepted": perimeter_is_closed,
        "route": "perimeter_weld_check" if perimeter_is_closed else "close_perimeter_or_redesign",
        "closed_contour": perimeter_is_closed,
    }


def butt_weld_resistance_branch_clause_14_1_14(
    full_penetration: bool,
    quality_control_confirmed: bool,
    ultimate_branch_requested: bool,
) -> dict[str, str | bool]:
    """
    Summary:
        Select the auditable resistance branch for an axially loaded butt weld.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.1.14
        Annex: None
        Equation/Table: Equation (175) and text branch
        Audit ID: SP16-PROC-14.1.14-RESISTANCE-BRANCH
        Normative status: normative

    Mathematical form:
        Branch = Rwy for the standard route or Rwu/gamma_u when its stated prerequisites are confirmed.

    Parameters:
        full_penetration: Whether the butt weld has full penetration.
        quality_control_confirmed: Whether the required weld-quality control is confirmed.
        ultimate_branch_requested: Whether the Rwu/gamma_u branch is requested.

    Returns:
        Type: dict[str, str | bool]
        Unit: not applicable
        Meaning: Selected resistance branch and applicability status.

    Assumptions:
        - Material resistances themselves are supplied to equation (175).

    Sign convention:
        - Not applicable.

    Unit convention:
        - Resistance branch identifiers are dimensionless metadata.

    Applicability:
        - Axially loaded butt welds under clause 14.1.14.

    Limitations:
        - The function does not verify NDT records.

    Raises:
        TypeError: Any input is not Boolean.

    Examples:
        >>> butt_weld_resistance_branch_clause_14_1_14(True, True, True)["branch"]
        'ultimate'

    Tests:
        Unit tests:
            - tests/test_brittle_fracture_and_welded_connections.py::test_butt_weld_resistance_branch
        Validation cases:
            - V15-PROC-14.1.14-BRANCH

    Implementation notes:
        - The ultimate branch is rejected unless both prerequisites are explicit.
        - No resistance is substituted automatically.
    """
    values = (full_penetration, quality_control_confirmed, ultimate_branch_requested)
    if any(not isinstance(value, bool) for value in values):
        raise TypeError("all inputs must be bool")
    allowed = full_penetration and quality_control_confirmed
    if ultimate_branch_requested and not allowed:
        return {"accepted": False, "branch": "unavailable", "reason": "ultimate_branch_prerequisites_not_confirmed"}
    return {"accepted": True, "branch": "ultimate" if ultimate_branch_requested else "yield", "reason": "confirmed"}
