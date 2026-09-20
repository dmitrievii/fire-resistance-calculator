"""Local stability of centrally compressed solid-section members under SP 16.13330.2017 clauses 7.3.1-7.3.11."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_9 = json.loads((_DATA_DIR / "table_9_wall_slenderness_limits.json").read_text(encoding="utf-8"))
_TABLE_10 = json.loads((_DATA_DIR / "table_10_flange_slenderness_limits.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-7.3.1-WEB-GEOMETRY",
    "SP16-PROC-7.3.2-WEB-SLENDERNESS",
    "SP16-PROC-7.3.2-TABLE-9-ROUTING",
    "SP16-PROC-7.3.3-TRANSVERSE-STIFFENERS",
    "SP16-PROC-7.3.4-LONGITUDINAL-STIFFENER",
    "SP16-PROC-7.3.5-REDUCED-AREA-TRIGGER",
    "SP16-PROC-7.3.6-REDUCED-DIMENSIONS",
    "SP16-PROC-7.3.7-FLANGE-GEOMETRY",
    "SP16-PROC-7.3.8-FLANGE-SLENDERNESS",
    "SP16-PROC-7.3.8-TABLE-10-ROUTING",
    "SP16-PROC-7.3.9-BOX-FLANGE",
    "SP16-PROC-7.3.10-EDGE-STIFFENER",
    "SP16-PROC-7.3.11-TWO-PLANE-INCREASE",
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


def _bounded(value: float, name: str, lower: float, upper: float) -> float:
    result = _real(value, name)
    if result < lower or result > upper:
        raise ValueError(f"{name} must be within [{lower}, {upper}]")
    return result


def _validate_reduction_domain(actual: float, limit: float) -> tuple[float, float]:
    actual_value = _positive(actual, "actual_wall_relative_slenderness")
    limit_value = _positive(limit, "limiting_wall_relative_slenderness")
    if actual_value <= limit_value:
        raise ValueError("Reduced dimensions apply only when actual wall slenderness exceeds the limit")
    if actual_value > 2.0 * limit_value:
        raise ValueError("Clause 7.3.5 limits the central-compression reduced-area route to twice the wall limit")
    return actual_value, limit_value


def table_9_wall_slenderness_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 9 formula, diagram-group, boundary, and note metadata.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Table 9; equations (23)-(29)
        Audit ID: SP16-TBL-9
        Normative status: normative

    Mathematical form:
        Immutable catalogue of four diagram groups and their piecewise formulas.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: No runtime input.
            Valid range: not applicable
            Source: data/table_9_wall_slenderness_limits.json

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Detached copy of the Table 9 catalogue.

    Assumptions:
        - Section classification is performed from the printed diagrams by the engineer.

    Sign convention:
        - Slenderness values are non-negative magnitudes.

    Unit convention:
        - Catalogue formulas are dimensionless.

    Applicability:
        - Centrally compressed solid-section members under clause 7.3.2.

    Limitations:
        - Arbitrary section geometry is not classified automatically.

    Raises:
        None: The bundled data are loaded at module import.

    Examples:
        >>> table_9_wall_slenderness_catalog()["table_number"]
        '9'

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_table_catalogues_are_detached_and_complete
        Validation cases:
            - LOCAL-TBL-009

    Implementation notes:
        - A JSON round trip prevents mutation of module state.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_9, ensure_ascii=False))


def table_10_flange_slenderness_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 10 formula, diagram-group, boundary, and multiplier metadata.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8-7.3.9
        Annex: None
        Equation/Table: Table 10; equations (37)-(40)
        Audit ID: SP16-TBL-10
        Normative status: normative

    Mathematical form:
        Immutable catalogue of four diagram groups and their linear formulas.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: No runtime input.
            Valid range: not applicable
            Source: data/table_10_flange_slenderness_limits.json

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Detached copy of the Table 10 catalogue.

    Assumptions:
        - Diagram-group selection is an explicit engineering input.

    Sign convention:
        - Slenderness values are non-negative magnitudes.

    Unit convention:
        - Catalogue formulas and multipliers are dimensionless.

    Applicability:
        - Flange outstands and flange plates under clauses 7.3.8-7.3.9.

    Limitations:
        - No image-recognition or geometry-classification algorithm is included.

    Raises:
        None: The bundled data are loaded at module import.

    Examples:
        >>> table_10_flange_slenderness_catalog()["table_number"]
        '10'

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_table_catalogues_are_detached_and_complete
        Validation cases:
            - LOCAL-TBL-010

    Implementation notes:
        - A JSON round trip prevents mutation of module state.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_10, ensure_ascii=False))


def local_stability_geometry_rule_catalog() -> dict[str, Any]:
    """
    Summary:
        Return concise geometry-reference rules for effective web height and flange outstand width.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.1 and 7.3.7
        Annex: None
        Equation/Table: Figure 5 and unnumbered geometry rules
        Audit ID: SP16-PROC-7.3.1-WEB-GEOMETRY; SP16-PROC-7.3.7-FLANGE-GEOMETRY
        Normative status: normative

    Mathematical form:
        Geometry-source category -> concise measurement rule.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: No runtime input.
            Valid range: not applicable
            Source: clauses 7.3.1 and 7.3.7

    Returns:
        Type: dict[str, Any]
        Unit: descriptive metadata
        Meaning: Measurement rules without reproducing extended standard text.

    Assumptions:
        - The caller measures the selected distance in a verified section model.

    Sign convention:
        - Dimensions are positive lengths.

    Unit convention:
        - The rules are unit-independent; executable calculations use mm.

    Applicability:
        - Welded, friction-connected, rolled, and bent profiles shown in Figure 5.

    Limitations:
        - The function does not extract dimensions from CAD geometry.

    Raises:
        None: The catalogue is generated in memory.

    Examples:
        >>> "welded" in local_stability_geometry_rule_catalog()["effective_web_height"]
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_geometry_rule_catalogue
        Validation cases:
            - LOCAL-PROC-7.3.1-7.3.7

    Implementation notes:
        - Descriptions are deliberately concise for copyright-safe traceability.
        - Defaults must be explicit in the input configuration.
    """
    return {
        "effective_web_height": {
            "welded": "full web height between flange interfaces",
            "friction_flange_connection": "distance between the nearest-to-axis edges of flange angles",
            "rolled": "distance between starts of internal fillets",
            "bent": "distance between edges of bend radii",
        },
        "effective_flange_outstand": {
            "welded": "web face to flange edge",
            "friction_flange_connection": "outermost flange-bolt axis to flange edge",
            "rolled": "start of internal fillet to flange edge",
            "bent": "edge of bend radius to flange edge",
        },
    }


def wall_relative_slenderness(
    effective_web_height_mm: float,
    web_thickness_mm: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the relative web slenderness used by clause 7.3.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Unnumbered definition preceding Table 9
        Audit ID: SP16-PROC-7.3.2-WEB-SLENDERNESS
        Normative status: normative

    Mathematical form:
        lambda_w_bar = (h_eff/t_w)*sqrt(R_y/E).

    Parameters:
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff selected under clause 7.3.1.
            Valid range: > 0
            Source: verified section geometry
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry
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
            Source: material data

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative web slenderness.

    Assumptions:
        - Geometry and material values belong to the same checked plate.

    Sign convention:
        - Dimensions and material properties are positive magnitudes.

    Unit convention:
        - h_eff and t_w use the same length unit; R_y and E use the same stress unit.

    Applicability:
        - Local web stability checks under clauses 7.3.2-7.3.6.

    Limitations:
        - Effective height selection is external to this scalar function.

    Raises:
        ValueError: An input is non-positive or non-finite.
        TypeError: An input is not a real number.

    Examples:
        >>> round(wall_relative_slenderness(500, 8, 355, 206000), 6)
        2.594067

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_wall_and_flange_relative_slenderness
        Validation cases:
            - LOCAL-PROC-WEB-SLENDERNESS

    Implementation notes:
        - No unit conversion is applied.
        - Defaults must be explicit in the input configuration.
    """
    h = _positive(effective_web_height_mm, "effective_web_height_mm")
    t = _positive(web_thickness_mm, "web_thickness_mm")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    return (h / t) * math.sqrt(ry / elastic)


def wall_slenderness_limit_eq23(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the first Table 9 diagram-group limit for member relative slenderness not exceeding 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (23), Table 9
        Audit ID: SP16-EQ-023
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = 1.30 + 0.15*lambda_bar^2.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness used in the overall stability check.
            Valid range: 0 <= value <= 2
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative web slenderness.

    Assumptions:
        - Table 9 diagram group 1 has been selected correctly.

    Sign convention:
        - Slenderness is a non-negative magnitude.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 1 at lambda_bar <= 2.

    Limitations:
        - The section family is not inferred from geometry.

    Raises:
        ValueError: Slenderness is outside the equation branch.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq23(2.0)
        1.9

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-023

    Implementation notes:
        - The branch boundary is enforced explicitly.
        - Defaults must be explicit in the input configuration.
    """
    value = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.0, 2.0)
    return 1.30 + 0.15 * value**2


def wall_slenderness_limit_eq24(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the capped first Table 9 diagram-group limit above member relative slenderness 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (24), Table 9
        Audit ID: SP16-EQ-024
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = min(1.20 + 0.35*lambda_bar, 2.3).

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness.
            Valid range: > 2
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped limiting relative web slenderness.

    Assumptions:
        - Table 9 diagram group 1 has been selected correctly.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 1 at lambda_bar > 2.

    Limitations:
        - No smoothing is applied at the piecewise boundary.

    Raises:
        ValueError: Slenderness is not greater than 2.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq24(4.0)
        2.3

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-024

    Implementation notes:
        - The printed <=2.3 condition is implemented as an upper cap.
        - Defaults must be explicit in the input configuration.
    """
    value = _real(member_relative_slenderness, "member_relative_slenderness")
    if value <= 2.0:
        raise ValueError("equation (24) requires member_relative_slenderness > 2")
    return min(1.20 + 0.35 * value, 2.3)


def wall_slenderness_limit_eq25(member_relative_slenderness: float) -> float:
    """
    Summary:
        Return the second Table 9 diagram-group limit at member relative slenderness not exceeding 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (25), Table 9
        Audit ID: SP16-EQ-025
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = 1.2.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness used to confirm the branch.
            Valid range: 0 <= value <= 1
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative web slenderness 1.2.

    Assumptions:
        - Table 9 diagram group 2 has been selected correctly.

    Sign convention:
        - Slenderness is non-negative.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 2 at lambda_bar <= 1.

    Limitations:
        - Diagram classification remains external.

    Raises:
        ValueError: Slenderness is outside the branch.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq25(1.0)
        1.2

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-025

    Implementation notes:
        - The input exists only to enforce the normative branch.
        - Defaults must be explicit in the input configuration.
    """
    _bounded(member_relative_slenderness, "member_relative_slenderness", 0.0, 1.0)
    return 1.2


def wall_slenderness_limit_eq26(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the capped second Table 9 diagram-group limit above member relative slenderness 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (26), Table 9
        Audit ID: SP16-EQ-026
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = min(1.0 + 0.2*lambda_bar, 1.6).

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness.
            Valid range: > 1
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped limiting relative web slenderness.

    Assumptions:
        - Table 9 diagram group 2 has been selected correctly.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 2 at lambda_bar > 1.

    Limitations:
        - Diagram classification remains external.

    Raises:
        ValueError: Slenderness is not greater than 1.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq26(3.0)
        1.6

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-026

    Implementation notes:
        - The printed <=1.6 condition is implemented as an upper cap.
        - Defaults must be explicit in the input configuration.
    """
    value = _real(member_relative_slenderness, "member_relative_slenderness")
    if value <= 1.0:
        raise ValueError("equation (26) requires member_relative_slenderness > 1")
    return min(1.0 + 0.2 * value, 1.6)


def wall_slenderness_limit_eq27(member_relative_slenderness: float) -> float:
    """
    Summary:
        Return the third Table 9 diagram-group limit at member relative slenderness not exceeding 0.8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (27), Table 9
        Audit ID: SP16-EQ-027
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = 1.0.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness used to confirm the branch.
            Valid range: 0 <= value <= 0.8
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative web slenderness 1.0.

    Assumptions:
        - Table 9 diagram group 3 has been selected correctly.

    Sign convention:
        - Slenderness is non-negative.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 3 at lambda_bar <= 0.8.

    Limitations:
        - Diagram classification remains external.

    Raises:
        ValueError: Slenderness is outside the branch.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq27(0.8)
        1.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-027

    Implementation notes:
        - The input exists only to enforce the normative branch.
        - Defaults must be explicit in the input configuration.
    """
    _bounded(member_relative_slenderness, "member_relative_slenderness", 0.0, 0.8)
    return 1.0


def wall_slenderness_limit_eq28(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the capped third Table 9 diagram-group limit above member relative slenderness 0.8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (28), Table 9
        Audit ID: SP16-EQ-028
        Normative status: normative

    Mathematical form:
        lambda_uw_bar = min(0.85 + 0.19*lambda_bar, 1.6).

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness.
            Valid range: > 0.8
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped limiting relative web slenderness.

    Assumptions:
        - Table 9 diagram group 3 has been selected correctly.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Table 9 group 3 at lambda_bar > 0.8.

    Limitations:
        - Diagram classification remains external.

    Raises:
        ValueError: Slenderness is not greater than 0.8.
        TypeError: Slenderness is not real.

    Examples:
        >>> wall_slenderness_limit_eq28(2.0)
        1.23

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-028

    Implementation notes:
        - The printed <=1.6 condition is implemented as an upper cap.
        - Defaults must be explicit in the input configuration.
    """
    value = _real(member_relative_slenderness, "member_relative_slenderness")
    if value <= 0.8:
        raise ValueError("equation (28) requires member_relative_slenderness > 0.8")
    return min(0.85 + 0.19 * value, 1.6)


def wall_slenderness_limit_eq29(
    member_relative_slenderness: float,
    tee_flange_width_mm: float,
    effective_web_height_mm: float,
) -> float:
    """
    Summary:
        Calculate the Table 9 T-section web-slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Equation (29), Table 9
        Audit ID: SP16-EQ-029
        Normative status: normative

    Mathematical form:
        (0.40+0.07*lambda_bar)*(1+0.25*sqrt(2-b_f/h_eff)).

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness after the Table 9 boundary rule.
            Valid range: 0.8 <= value <= 4
            Source: clause 7.1.3
        tee_flange_width_mm:
            Type: float
            Unit: mm
            Meaning: Tee flange width b_f.
            Valid range: > 0 and 1 <= b_f/h_eff <= 2
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0 and 1 <= b_f/h_eff <= 2
            Source: clause 7.3.1 geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative web slenderness for the T-section diagram group.

    Assumptions:
        - The T-section diagram group and geometric ratio condition are applicable.

    Sign convention:
        - Dimensions and slenderness are positive magnitudes.

    Unit convention:
        - Both dimensions use mm and cancel in the ratio.

    Applicability:
        - Table 9 group 4 with 1 <= b_f/h_eff <= 2.

    Limitations:
        - The wrapper applies the external 0.8/4 slenderness clamping rule; this equation function enforces its domain.

    Raises:
        ValueError: Slenderness or the geometric ratio is outside the prescribed domain.
        TypeError: An input is not real.

    Examples:
        >>> wall_slenderness_limit_eq29(2.0, 500, 500)
        0.675

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-EQ-029

    Implementation notes:
        - No extrapolation beyond the printed ratio interval is allowed.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.8, 4.0)
    flange = _positive(tee_flange_width_mm, "tee_flange_width_mm")
    height = _positive(effective_web_height_mm, "effective_web_height_mm")
    ratio = flange / height
    if ratio < 1.0 or ratio > 2.0:
        raise ValueError("tee_flange_width_mm/effective_web_height_mm must be within [1, 2]")
    return (0.40 + 0.07 * slenderness) * (1.0 + 0.25 * math.sqrt(2.0 - ratio))


def wall_slenderness_limit(
    table_9_diagram_group: str,
    member_relative_slenderness: float,
    tee_flange_width_mm: float = 1.0,
    effective_web_height_mm: float = 1.0,
) -> float:
    """
    Summary:
        Route a Table 9 local-web-stability limit to the applicable audited equation branch.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.2
        Annex: None
        Equation/Table: Table 9; equations (23)-(29)
        Audit ID: SP16-PROC-7.3.2-TABLE-9-ROUTING
        Normative status: normative

    Mathematical form:
        Explicit diagram group + piecewise branch -> limiting relative web slenderness.

    Parameters:
        table_9_diagram_group:
            Type: str
            Unit: selector
            Meaning: Explicit diagram group from the package Table 9 catalogue.
            Valid range: group_1_i_section | group_2_box_section | group_3_channel_section | group_4_tee_section
            Source: engineering comparison with Table 9 diagrams
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness.
            Valid range: >= 0
            Source: overall stability calculation
        tee_flange_width_mm:
            Type: float
            Unit: mm
            Meaning: Tee flange width used only for group 4.
            Valid range: > 0
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Tee effective web height used only for group 4.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting relative web slenderness.

    Assumptions:
        - The caller has selected the correct diagram group.

    Sign convention:
        - Slenderness and dimensions are non-negative/positive magnitudes.

    Unit convention:
        - Tee dimensions use the same length unit.

    Applicability:
        - Centrally compressed solid-section members under Table 9.

    Limitations:
        - Default tee dimensions are placeholders unused by groups 1-3 and must not be relied on for group 4.

    Raises:
        ValueError: The diagram group or numerical domain is invalid.
        TypeError: A numerical input is not real.

    Examples:
        >>> wall_slenderness_limit("group_1_i_section", 2.5)
        2.075

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_23_to_29_and_table_9_router
        Validation cases:
            - LOCAL-PROC-TABLE-9

    Implementation notes:
        - Group 4 clamps member slenderness to 0.8 or 4 exactly as the table note requires.
        - Defaults must be explicit in user-facing input configuration; function defaults are unused compatibility placeholders for non-tee groups.
    """
    value = _nonnegative(member_relative_slenderness, "member_relative_slenderness")
    if table_9_diagram_group == "group_1_i_section":
        return wall_slenderness_limit_eq23(value) if value <= 2.0 else wall_slenderness_limit_eq24(value)
    if table_9_diagram_group == "group_2_box_section":
        return wall_slenderness_limit_eq25(value) if value <= 1.0 else wall_slenderness_limit_eq26(value)
    if table_9_diagram_group == "group_3_channel_section":
        return wall_slenderness_limit_eq27(value) if value <= 0.8 else wall_slenderness_limit_eq28(value)
    if table_9_diagram_group == "group_4_tee_section":
        clamped = min(max(value, 0.8), 4.0)
        return wall_slenderness_limit_eq29(clamped, tee_flange_width_mm, effective_web_height_mm)
    raise ValueError("Unsupported table_9_diagram_group")


def transverse_stiffener_requirements(
    wall_relative_slenderness_value: float,
    effective_web_height_mm: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
    stiffener_arrangement: str,
    provided_stiffener_outstand_mm: float,
    geometrically_nonlinear_design: bool,
    solid_branch_of_built_up_column: bool,
) -> dict[str, Any]:
    """
    Summary:
        Evaluate the clause 7.3.3 transverse-stiffener trigger, spacing, width, thickness, and location rules.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.3.3
        Annex: None
        Equation/Table: Unnumbered stiffener requirements
        Audit ID: SP16-PROC-7.3.3-TRANSVERSE-STIFFENERS
        Normative status: normative

    Mathematical form:
        Trigger lambda_w_bar >= 2.3; spacing 2.5h_eff to 3h_eff; width and thickness inequalities.

    Parameters:
        wall_relative_slenderness_value:
            Type: float
            Unit: dimensionless
            Meaning: Actual relative web slenderness.
            Valid range: >= 0
            Source: clause 7.3.2 definition
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0
            Source: clause 7.3.1
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
            Source: material data
        stiffener_arrangement:
            Type: str
            Unit: selector
            Meaning: Paired symmetric or one-sided transverse stiffener.
            Valid range: paired_symmetric | one_sided
            Source: design geometry
        provided_stiffener_outstand_mm:
            Type: float
            Unit: mm
            Meaning: Actual protruding stiffener width b_r used for the thickness rule.
            Valid range: > 0
            Source: proposed section
        geometrically_nonlinear_design:
            Type: bool
            Unit: boolean
            Meaning: Whether the clause 7.3.3 trigger exception applies.
            Valid range: true | false
            Source: analysis method confirmation
        solid_branch_of_built_up_column:
            Type: bool
            Unit: boolean
            Meaning: Whether stiffeners are restricted to lattice/batten connection nodes.
            Valid range: true | false
            Source: member topology

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Trigger, spacing range, minimum dimensions, checks, and location rule.

    Assumptions:
        - The geometry and material inputs refer to the same web and stiffener.

    Sign convention:
        - Dimensions and slenderness are positive magnitudes.

    Unit convention:
        - Lengths use mm; stresses use N/mm2.

    Applicability:
        - Centrally compressed columns, posts, supports, and similar solid-web elements.

    Limitations:
        - Weld design and complete stiffener stability are outside this function.

    Raises:
        ValueError: Numerical domains or arrangement are invalid.
        TypeError: Inputs have invalid types.

    Examples:
        >>> transverse_stiffener_requirements(2.4, 600, 355, 206000, "paired_symmetric", 60, False, False)["required"]
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_transverse_stiffener_requirements
        Validation cases:
            - LOCAL-PROC-7.3.3

    Implementation notes:
        - The thickness limit uses the provided b_r, not only the minimum b_r.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _nonnegative(wall_relative_slenderness_value, "wall_relative_slenderness_value")
    height = _positive(effective_web_height_mm, "effective_web_height_mm")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    outstand = _positive(provided_stiffener_outstand_mm, "provided_stiffener_outstand_mm")
    if not isinstance(geometrically_nonlinear_design, bool) or not isinstance(solid_branch_of_built_up_column, bool):
        raise TypeError("geometrically_nonlinear_design and solid_branch_of_built_up_column must be bool")
    if stiffener_arrangement == "paired_symmetric":
        minimum_outstand = height / 30.0 + 40.0
    elif stiffener_arrangement == "one_sided":
        minimum_outstand = height / 20.0 + 50.0
    else:
        raise ValueError("stiffener_arrangement must be 'paired_symmetric' or 'one_sided'")
    required = slenderness >= 2.3 and not geometrically_nonlinear_design
    return {
        "required": required,
        "trigger_exception_geometrically_nonlinear": geometrically_nonlinear_design,
        "minimum_spacing_mm": 2.5 * height if required else None,
        "maximum_spacing_mm": 3.0 * height if required else None,
        "minimum_outstand_mm": minimum_outstand,
        "provided_outstand_mm": outstand,
        "outstand_pass": outstand >= minimum_outstand,
        "minimum_thickness_mm": 2.0 * outstand * math.sqrt(ry / elastic),
        "location_rule": (
            "only_at_lattice_or_batten_connection_nodes"
            if solid_branch_of_built_up_column
            else "general_transverse_stiffener_layout"
        ),
        "one_sided_angle_weld_orientation": "angle_toe_to_web" if stiffener_arrangement == "one_sided" else None,
    }


def longitudinal_stiffener_wall_limit_multiplier_eq30(
    longitudinal_stiffener_inertia_mm4: float,
    effective_web_height_mm: float,
    web_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate the multiplier for a mid-depth longitudinal web stiffener in a centrally compressed I-section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.4
        Annex: None
        Equation/Table: Equation (30)
        Audit ID: SP16-EQ-030
        Normative status: normative

    Mathematical form:
        beta = 1 + 0.4*x*(1 - 0.1*x), x = I_r1/(h_eff*t_w^3), x <= 6.

    Parameters:
        longitudinal_stiffener_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Longitudinal stiffener second moment I_r1 about the prescribed axis.
            Valid range: >= 0 and I_r1/(h_eff*t_w^3) <= 6
            Source: stiffener geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0
            Source: clause 7.3.1
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Multiplier beta applied to the Table 9 web limit.

    Assumptions:
        - The stiffener is at web mid-depth and satisfies the clause geometry rules.

    Sign convention:
        - Inertia and dimensions are non-negative/positive magnitudes.

    Unit convention:
        - I_r1 uses mm4 and h_eff*t_w^3 uses mm4.

    Applicability:
        - Centrally compressed I-sections under clause 7.3.4.

    Limitations:
        - One-sided stiffener-axis and minimum-inertia equivalence checks remain explicit geometry responsibilities.

    Raises:
        ValueError: The dimensionless ratio exceeds 6 or an input is invalid.
        TypeError: An input is not real.

    Examples:
        >>> longitudinal_stiffener_wall_limit_multiplier_eq30(1536000, 600, 8)
        2.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equation_30_and_stiffener_domain
        Validation cases:
            - LOCAL-EQ-030

    Implementation notes:
        - Values above the printed applicability limit are rejected rather than capped.
        - Defaults must be explicit in the input configuration.
    """
    inertia = _nonnegative(longitudinal_stiffener_inertia_mm4, "longitudinal_stiffener_inertia_mm4")
    height = _positive(effective_web_height_mm, "effective_web_height_mm")
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    ratio = inertia / (height * thickness**3)
    if ratio > 6.0:
        raise ValueError("I_r1/(h_eff*t_w^3) must not exceed 6 for equation (30)")
    return 1.0 + 0.4 * ratio * (1.0 - 0.1 * ratio)


def reduced_area_required(
    actual_wall_relative_slenderness: float,
    limiting_wall_relative_slenderness: float,
) -> dict[str, Any]:
    """
    Summary:
        Classify whether clause 7.3.5 requires and permits the reduced-area route for central compression.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.5
        Annex: None
        Equation/Table: Reduced-area trigger preceding equations (31)-(36)
        Audit ID: SP16-PROC-7.3.5-REDUCED-AREA-TRIGGER
        Normative status: normative

    Mathematical form:
        Required if lambda_w_bar > lambda_uw_bar; central-compression route limited to lambda_w_bar <= 2*lambda_uw_bar.

    Parameters:
        actual_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual relative web slenderness.
            Valid range: > 0
            Source: clause 7.3.2 definition
        limiting_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Applicable Table 9 limit including any audited multiplier.
            Valid range: > 0
            Source: clauses 7.3.2 and 7.3.4

    Returns:
        Type: dict[str, Any]
        Unit: dimensionless statuses and ratio
        Meaning: Whether reduction is required and whether the central-compression route is within its limit.

    Assumptions:
        - The member is centrally compressed.

    Sign convention:
        - Slenderness values are positive magnitudes.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Solid-section central compression under clause 7.3.5.

    Limitations:
        - Eccentric-compression applicability is not determined by this helper.

    Raises:
        ValueError: An input is non-positive or non-finite.
        TypeError: An input is not real.

    Examples:
        >>> reduced_area_required(2.4, 2.0)["required"]
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_reduced_area_trigger
        Validation cases:
            - LOCAL-PROC-7.3.5

    Implementation notes:
        - Exceeding twice the limit is reported explicitly and not silently clipped.
        - Defaults must be explicit in the input configuration.
    """
    actual = _positive(actual_wall_relative_slenderness, "actual_wall_relative_slenderness")
    limit = _positive(limiting_wall_relative_slenderness, "limiting_wall_relative_slenderness")
    ratio = actual / limit
    return {
        "actual_to_limit_ratio": ratio,
        "required": actual > limit,
        "within_central_compression_reduction_domain": ratio <= 2.0,
        "formula_route_permitted": actual <= limit or ratio <= 2.0,
    }


def reduced_area_i_or_channel_eq31(
    gross_area_mm2: float,
    effective_web_height_mm: float,
    reduced_web_height_mm: float,
    web_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate the reduced area for I- or channel-section members.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (31)
        Audit ID: SP16-EQ-031
        Normative status: normative

    Mathematical form:
        A_d = A - (h_eff - h_d)*t_w.

    Parameters:
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross member area A.
            Valid range: > 0
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0
            Source: clause 7.3.1
        reduced_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Reduced web height h_d.
            Valid range: 0 <= h_d <= h_eff
            Source: equation (34) or (36)
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: mm2
        Meaning: Reduced design area A_d.

    Assumptions:
        - Only the web-area reduction represented by equation (31) is applicable.

    Sign convention:
        - Areas and dimensions are non-negative/positive magnitudes.

    Unit convention:
        - Lengths use mm and area uses mm2.

    Applicability:
        - I- and channel-section reduced-area calculations under clause 7.3.6.

    Limitations:
        - The function does not itself test the clause 7.3.5 trigger.

    Raises:
        ValueError: Dimensions are inconsistent or the resulting area is non-positive.
        TypeError: An input is not real.

    Examples:
        >>> reduced_area_i_or_channel_eq31(10000, 500, 400, 8)
        9200.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_31_to_33_reduced_areas
        Validation cases:
            - LOCAL-EQ-031

    Implementation notes:
        - No implicit unit conversion is applied.
        - Defaults must be explicit in the input configuration.
    """
    area = _positive(gross_area_mm2, "gross_area_mm2")
    h_eff = _positive(effective_web_height_mm, "effective_web_height_mm")
    h_d = _nonnegative(reduced_web_height_mm, "reduced_web_height_mm")
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    if h_d > h_eff:
        raise ValueError("reduced_web_height_mm must not exceed effective_web_height_mm")
    result = area - (h_eff - h_d) * thickness
    if result <= 0.0 or result > area:
        raise ValueError("Equation (31) produced an invalid reduced area")
    return result


def reduced_area_box_central_eq32(
    gross_area_mm2: float,
    effective_web_height_mm: float,
    reduced_web_height_mm: float,
    web_thickness_mm: float,
    effective_flange_plate_width_mm: float,
    reduced_flange_plate_width_mm: float,
    flange_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate the reduced area of a centrally compressed box section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (32)
        Audit ID: SP16-EQ-032
        Normative status: normative

    Mathematical form:
        A_d = A - 2(h_eff-h_d)t_w - 2(b_eff,1-b_d)t_f.

    Parameters:
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross box-section area A.
            Valid range: > 0
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0
            Source: section geometry
        reduced_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Reduced web height h_d.
            Valid range: 0 <= h_d <= h_eff
            Source: equation (35)
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry
        effective_flange_plate_width_mm:
            Type: float
            Unit: mm
            Meaning: Effective flange-plate width b_eff,1.
            Valid range: > 0
            Source: section geometry
        reduced_flange_plate_width_mm:
            Type: float
            Unit: mm
            Meaning: Reduced flange-plate width b_d.
            Valid range: 0 <= b_d <= b_eff,1
            Source: equation (35) by clause substitution
        flange_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Flange thickness t_f.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: mm2
        Meaning: Reduced design area A_d.

    Assumptions:
        - Two equivalent webs and two equivalent flange plates are represented.

    Sign convention:
        - Areas and dimensions are non-negative/positive magnitudes.

    Unit convention:
        - Lengths use mm and area uses mm2.

    Applicability:
        - Centrally compressed box sections under clause 7.3.6.

    Limitations:
        - Unequal plate pairs require a more explicit section decomposition.

    Raises:
        ValueError: Reduced dimensions exceed effective dimensions or area is invalid.
        TypeError: An input is not real.

    Examples:
        >>> reduced_area_box_central_eq32(12000, 500, 450, 8, 300, 270, 10)
        10600.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_31_to_33_reduced_areas
        Validation cases:
            - LOCAL-EQ-032

    Implementation notes:
        - The factors of two are retained exactly.
        - Defaults must be explicit in the input configuration.
    """
    area = _positive(gross_area_mm2, "gross_area_mm2")
    h_eff = _positive(effective_web_height_mm, "effective_web_height_mm")
    h_d = _nonnegative(reduced_web_height_mm, "reduced_web_height_mm")
    t_w = _positive(web_thickness_mm, "web_thickness_mm")
    b_eff = _positive(effective_flange_plate_width_mm, "effective_flange_plate_width_mm")
    b_d = _nonnegative(reduced_flange_plate_width_mm, "reduced_flange_plate_width_mm")
    t_f = _positive(flange_thickness_mm, "flange_thickness_mm")
    if h_d > h_eff or b_d > b_eff:
        raise ValueError("Reduced dimensions must not exceed effective dimensions")
    result = area - 2.0 * (h_eff - h_d) * t_w - 2.0 * (b_eff - b_d) * t_f
    if result <= 0.0 or result > area:
        raise ValueError("Equation (32) produced an invalid reduced area")
    return result


def reduced_area_box_eccentric_eq33(
    gross_area_mm2: float,
    effective_web_height_mm: float,
    reduced_web_height_mm: float,
    web_thickness_mm: float,
) -> float:
    """
    Summary:
        Calculate the box-section reduced area expression printed for eccentric compression.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (33)
        Audit ID: SP16-EQ-033
        Normative status: normative

    Mathematical form:
        A_d = A - 2(h_eff-h_d)t_w.

    Parameters:
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross box-section area A.
            Valid range: > 0
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: > 0
            Source: section geometry
        reduced_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Reduced web height h_d.
            Valid range: 0 <= h_d <= h_eff
            Source: equation (35)
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry

    Returns:
        Type: float
        Unit: mm2
        Meaning: Reduced design area A_d.

    Assumptions:
        - The eccentric-compression branch is applicable and has been confirmed externally.

    Sign convention:
        - Areas and dimensions are non-negative/positive magnitudes.

    Unit convention:
        - Lengths use mm and area uses mm2.

    Applicability:
        - Box sections under the eccentric-compression branch of clause 7.3.6.

    Limitations:
        - v0.5 does not implement the complete eccentric-compression member check.

    Raises:
        ValueError: Dimensions are inconsistent or area is invalid.
        TypeError: An input is not real.

    Examples:
        >>> reduced_area_box_eccentric_eq33(12000, 500, 450, 8)
        11200.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_31_to_33_reduced_areas
        Validation cases:
            - LOCAL-EQ-033

    Implementation notes:
        - The function is exposed for inventory completeness but is not called by the central-compression runner.
        - Defaults must be explicit in the input configuration.
    """
    area = _positive(gross_area_mm2, "gross_area_mm2")
    h_eff = _positive(effective_web_height_mm, "effective_web_height_mm")
    h_d = _nonnegative(reduced_web_height_mm, "reduced_web_height_mm")
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    if h_d > h_eff:
        raise ValueError("reduced_web_height_mm must not exceed effective_web_height_mm")
    result = area - 2.0 * (h_eff - h_d) * thickness
    if result <= 0.0 or result > area:
        raise ValueError("Equation (33) produced an invalid reduced area")
    return result


def reduced_web_height_i_section_eq34(
    web_thickness_mm: float,
    actual_wall_relative_slenderness: float,
    limiting_wall_relative_slenderness: float,
    member_relative_slenderness: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the reduced web height for a centrally compressed I-section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (34)
        Audit ID: SP16-EQ-034
        Normative status: normative

    Mathematical form:
        h_d=t_w[lambda_uw-(lambda_w/lambda_uw-1)(lambda_uw-1.2-0.15lambda)]sqrt(E/R_y), with lambda<=3.5.

    Parameters:
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry
        actual_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual lambda_w_bar.
            Valid range: lambda_uw_bar < value <= 2*lambda_uw_bar
            Source: clause 7.3.2
        limiting_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Applicable lambda_uw_bar.
            Valid range: > 0
            Source: Table 9
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member lambda_bar, capped at 3.5 by the equation note.
            Valid range: >= 0
            Source: overall stability check
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
            Source: material data

    Returns:
        Type: float
        Unit: mm
        Meaning: Reduced web height h_d.

    Assumptions:
        - The reduced-area route of clause 7.3.5 is applicable.

    Sign convention:
        - Dimensions and slenderness values are positive magnitudes.

    Unit convention:
        - Stress units cancel; the result uses the web-thickness unit mm.

    Applicability:
        - Centrally compressed I-sections under equation (34).

    Limitations:
        - Eccentric-compression limit selection under clause 9.4.2 is outside this release.

    Raises:
        ValueError: The reduction domain or material inputs are invalid.
        TypeError: An input is not real.

    Examples:
        >>> reduced_web_height_i_section_eq34(8, 2.5, 2.0, 2.5, 355, 206000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_34_to_36_reduced_dimensions
        Validation cases:
            - LOCAL-EQ-034

    Implementation notes:
        - Member slenderness above 3.5 is replaced by 3.5 exactly as stated.
        - Defaults must be explicit in the input configuration.
    """
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    actual, limit = _validate_reduction_domain(actual_wall_relative_slenderness, limiting_wall_relative_slenderness)
    member = min(_nonnegative(member_relative_slenderness, "member_relative_slenderness"), 3.5)
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    bracket = limit - (actual / limit - 1.0) * (limit - 1.2 - 0.15 * member)
    result = thickness * bracket * math.sqrt(elastic / ry)
    effective_height = thickness * actual * math.sqrt(elastic / ry)
    if result <= 0.0 or result > effective_height:
        raise ValueError("Equation (34) produced a reduced height outside (0, h_eff]")
    return result


def reduced_plate_dimension_box_eq35(
    plate_thickness_mm: float,
    actual_plate_relative_slenderness: float,
    limiting_plate_relative_slenderness: float,
    member_relative_slenderness: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate a reduced box-section web height or flange-plate width by equation (35).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (35)
        Audit ID: SP16-EQ-035
        Normative status: normative

    Mathematical form:
        d=t[lambda_u-(lambda_p/lambda_u-1)(lambda_u-2.9-0.2lambda+0.7lambda_u)]sqrt(E/R_y), lambda<=2.3.

    Parameters:
        plate_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web or flange-plate thickness used by the clause substitution.
            Valid range: > 0
            Source: section geometry
        actual_plate_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual web or flange-plate relative slenderness.
            Valid range: limit < value <= 2*limit for the central-compression route
            Source: clauses 7.3.2 or 7.3.9
        limiting_plate_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Applicable limiting plate slenderness.
            Valid range: > 0
            Source: Tables 9 or 10
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member lambda_bar, capped at 2.3.
            Valid range: >= 0
            Source: overall stability check
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
            Source: material data

    Returns:
        Type: float
        Unit: mm
        Meaning: Reduced plate dimension h_d or b_d.

    Assumptions:
        - The caller applies the equation substitution specified for the chosen box plate.

    Sign convention:
        - Dimensions and slenderness values are positive magnitudes.

    Unit convention:
        - Stress units cancel; the result uses mm.

    Applicability:
        - Centrally compressed box-section webs and flange plates under clause 7.3.6.

    Limitations:
        - The function does not select which physical plate is parallel to the checked stability plane.

    Raises:
        ValueError: The reduction domain or material inputs are invalid.
        TypeError: An input is not real.

    Examples:
        >>> reduced_plate_dimension_box_eq35(8, 2.0, 1.5, 2.0, 355, 206000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_34_to_36_reduced_dimensions
        Validation cases:
            - LOCAL-EQ-035

    Implementation notes:
        - The same audited function supports h_d and b_d because the clause explicitly prescribes variable substitution.
        - Defaults must be explicit in the input configuration.
    """
    thickness = _positive(plate_thickness_mm, "plate_thickness_mm")
    actual, limit = _validate_reduction_domain(actual_plate_relative_slenderness, limiting_plate_relative_slenderness)
    member = min(_nonnegative(member_relative_slenderness, "member_relative_slenderness"), 2.3)
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    bracket = limit - (actual / limit - 1.0) * (limit - 2.9 - 0.2 * member + 0.7 * limit)
    result = thickness * bracket * math.sqrt(elastic / ry)
    effective_dimension = thickness * actual * math.sqrt(elastic / ry)
    if result <= 0.0 or result > effective_dimension:
        raise ValueError("Equation (35) produced a reduced dimension outside (0, effective dimension]")
    return result


def reduced_web_height_channel_eq36(
    web_thickness_mm: float,
    actual_wall_relative_slenderness: float,
    limiting_wall_relative_slenderness: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the reduced web height for a centrally compressed channel section.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.6
        Annex: None
        Equation/Table: Equation (36)
        Audit ID: SP16-EQ-036
        Normative status: normative

    Mathematical form:
        h_d = t_w*lambda_uw_bar*sqrt(E/R_y).

    Parameters:
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness t_w.
            Valid range: > 0
            Source: section geometry
        actual_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual web slenderness used to verify the reduction domain.
            Valid range: limit < value <= 2*limit
            Source: clause 7.3.2
        limiting_wall_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Applicable lambda_uw_bar.
            Valid range: > 0
            Source: Table 9
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
            Source: material data

    Returns:
        Type: float
        Unit: mm
        Meaning: Reduced channel web height h_d.

    Assumptions:
        - The channel-section reduced-area route is applicable.

    Sign convention:
        - Dimensions and slenderness are positive magnitudes.

    Unit convention:
        - Stress units cancel; the result uses mm.

    Applicability:
        - Centrally compressed channel sections under equation (36).

    Limitations:
        - Complete section stability and connection checks are outside this function.

    Raises:
        ValueError: The reduction domain or material inputs are invalid.
        TypeError: An input is not real.

    Examples:
        >>> reduced_web_height_channel_eq36(8, 1.5, 1.2, 355, 206000) > 0
        True

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_34_to_36_reduced_dimensions
        Validation cases:
            - LOCAL-EQ-036

    Implementation notes:
        - Actual slenderness is used only for the clause 7.3.5 applicability guard.
        - Defaults must be explicit in the input configuration.
    """
    thickness = _positive(web_thickness_mm, "web_thickness_mm")
    actual, limit = _validate_reduction_domain(actual_wall_relative_slenderness, limiting_wall_relative_slenderness)
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    result = thickness * limit * math.sqrt(elastic / ry)
    effective_height = thickness * actual * math.sqrt(elastic / ry)
    if result <= 0.0 or result > effective_height:
        raise ValueError("Equation (36) produced a reduced height outside (0, h_eff]")
    return result


def flange_relative_slenderness(
    effective_flange_outstand_mm: float,
    flange_thickness_mm: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
) -> float:
    """
    Summary:
        Calculate the relative slenderness of a flange outstand or flange plate.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8 and 7.3.9
        Annex: None
        Equation/Table: Unnumbered definitions associated with Table 10
        Audit ID: SP16-PROC-7.3.8-FLANGE-SLENDERNESS; SP16-PROC-7.3.9-BOX-FLANGE
        Normative status: normative

    Mathematical form:
        lambda_f_bar = (b_eff/t_f)*sqrt(R_y/E).

    Parameters:
        effective_flange_outstand_mm:
            Type: float
            Unit: mm
            Meaning: Effective flange outstand or box flange-plate width.
            Valid range: > 0
            Source: clauses 7.3.7 or 7.3.9
        flange_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Flange thickness t_f.
            Valid range: > 0
            Source: section geometry
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
            Source: material data

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative flange slenderness.

    Assumptions:
        - Effective width and thickness belong to the same plate/outstand.

    Sign convention:
        - Dimensions and material properties are positive magnitudes.

    Unit convention:
        - Width and thickness use the same length unit; stresses use the same unit.

    Applicability:
        - Table 10 and box-flange checks under clauses 7.3.8-7.3.9.

    Limitations:
        - Diagram-group selection is external.

    Raises:
        ValueError: An input is non-positive or non-finite.
        TypeError: An input is not real.

    Examples:
        >>> round(flange_relative_slenderness(120, 12, 355, 206000), 6)
        0.415051

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_wall_and_flange_relative_slenderness
        Validation cases:
            - LOCAL-PROC-FLANGE-SLENDERNESS

    Implementation notes:
        - Clause 7.3.9 uses the same scalar definition for a box flange plate.
        - Defaults must be explicit in the input configuration.
    """
    width = _positive(effective_flange_outstand_mm, "effective_flange_outstand_mm")
    thickness = _positive(flange_thickness_mm, "flange_thickness_mm")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    return (width / thickness) * math.sqrt(ry / elastic)


def flange_slenderness_limit_eq37(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the first Table 10 diagram-group flange-slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8
        Annex: None
        Equation/Table: Equation (37), Table 10
        Audit ID: SP16-EQ-037
        Normative status: normative

    Mathematical form:
        lambda_uf_bar = 0.36 + 0.10*lambda_bar.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness after the table boundary rule.
            Valid range: 0.8 <= value <= 4
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting flange relative slenderness.

    Assumptions:
        - Table 10 diagram group 1 is applicable.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - First diagram group in Table 10.

    Limitations:
        - The diagram group is not inferred.

    Raises:
        ValueError: Slenderness is outside [0.8, 4].
        TypeError: Slenderness is not real.

    Examples:
        >>> flange_slenderness_limit_eq37(2.0)
        0.56

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_37_to_40_and_table_10_router
        Validation cases:
            - LOCAL-EQ-037

    Implementation notes:
        - Boundary clamping is handled by the wrapper.
        - Defaults must be explicit in the input configuration.
    """
    value = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.8, 4.0)
    return 0.36 + 0.10 * value


def flange_slenderness_limit_eq38(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the second Table 10 diagram-group flange-slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8
        Annex: None
        Equation/Table: Equation (38), Table 10
        Audit ID: SP16-EQ-038
        Normative status: normative

    Mathematical form:
        lambda_uf_bar = 0.43 + 0.08*lambda_bar.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness after the table boundary rule.
            Valid range: 0.8 <= value <= 4
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting flange relative slenderness.

    Assumptions:
        - Table 10 diagram group 2 is applicable.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Second diagram group in Table 10.

    Limitations:
        - The diagram group is not inferred.

    Raises:
        ValueError: Slenderness is outside [0.8, 4].
        TypeError: Slenderness is not real.

    Examples:
        >>> flange_slenderness_limit_eq38(2.0)
        0.59

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_37_to_40_and_table_10_router
        Validation cases:
            - LOCAL-EQ-038

    Implementation notes:
        - Boundary clamping is handled by the wrapper.
        - Defaults must be explicit in the input configuration.
    """
    value = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.8, 4.0)
    return 0.43 + 0.08 * value


def flange_slenderness_limit_eq39(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the third Table 10 diagram-group flange-slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8
        Annex: None
        Equation/Table: Equation (39), Table 10
        Audit ID: SP16-EQ-039
        Normative status: normative

    Mathematical form:
        lambda_uf_bar = 0.40 + 0.07*lambda_bar.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness after the table boundary rule.
            Valid range: 0.8 <= value <= 4
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting flange relative slenderness.

    Assumptions:
        - Table 10 diagram group 3 is applicable.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Third diagram group in Table 10.

    Limitations:
        - The diagram group is not inferred.

    Raises:
        ValueError: Slenderness is outside [0.8, 4].
        TypeError: Slenderness is not real.

    Examples:
        >>> flange_slenderness_limit_eq39(2.0)
        0.54

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_37_to_40_and_table_10_router
        Validation cases:
            - LOCAL-EQ-039

    Implementation notes:
        - Boundary clamping is handled by the wrapper.
        - Defaults must be explicit in the input configuration.
    """
    value = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.8, 4.0)
    return 0.40 + 0.07 * value


def flange_slenderness_limit_eq40(member_relative_slenderness: float) -> float:
    """
    Summary:
        Calculate the fourth Table 10 diagram-group flange-slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8
        Annex: None
        Equation/Table: Equation (40), Table 10
        Audit ID: SP16-EQ-040
        Normative status: normative

    Mathematical form:
        lambda_uf_bar = 0.85 + 0.19*lambda_bar.

    Parameters:
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness after the table boundary rule.
            Valid range: 0.8 <= value <= 4
            Source: clause 7.1.3

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting flange relative slenderness.

    Assumptions:
        - Table 10 diagram group 4 is applicable.

    Sign convention:
        - Slenderness is positive.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Fourth diagram group in Table 10.

    Limitations:
        - The table note does not assign an additional edge-stiffener multiplier to equation (40).

    Raises:
        ValueError: Slenderness is outside [0.8, 4].
        TypeError: Slenderness is not real.

    Examples:
        >>> flange_slenderness_limit_eq40(2.0)
        1.23

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_37_to_40_and_table_10_router
        Validation cases:
            - LOCAL-EQ-040

    Implementation notes:
        - Boundary clamping is handled by the wrapper.
        - Defaults must be explicit in the input configuration.
    """
    value = _bounded(member_relative_slenderness, "member_relative_slenderness", 0.8, 4.0)
    return 0.85 + 0.19 * value


def flange_slenderness_limit(
    table_10_diagram_group: str,
    member_relative_slenderness: float,
    edge_stiffened: bool,
) -> float:
    """
    Summary:
        Route a Table 10 flange limit, apply the 0.8/4 boundary rule, and apply only the printed edge-stiffener multiplier.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.8
        Annex: None
        Equation/Table: Table 10; equations (37)-(40)
        Audit ID: SP16-PROC-7.3.8-TABLE-10-ROUTING
        Normative status: normative

    Mathematical form:
        clamp(lambda_bar,0.8,4) -> equation group -> optional multiplier 1.5 or 1.6 where stated.

    Parameters:
        table_10_diagram_group:
            Type: str
            Unit: selector
            Meaning: Explicit group_1, group_2, group_3, or group_4 diagram selection.
            Valid range: group_1 | group_2 | group_3 | group_4
            Source: engineering comparison with Table 10 diagrams
        member_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness before the table boundary rule.
            Valid range: >= 0
            Source: overall stability calculation
        edge_stiffened:
            Type: bool
            Unit: boolean
            Meaning: Whether the flange outstand is edged by a stiffener under the Table 10 note.
            Valid range: true | false
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Applicable limiting flange relative slenderness.

    Assumptions:
        - The diagram group and edge-stiffener classification are correct.

    Sign convention:
        - Slenderness is non-negative.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Centrally compressed solid-section flange checks under Table 10.

    Limitations:
        - edge_stiffened=true is rejected for group 4 because the printed note assigns no extra multiplier there.

    Raises:
        ValueError: Group or edge-stiffener combination is unsupported.
        TypeError: edge_stiffened is not bool or slenderness is not real.

    Examples:
        >>> flange_slenderness_limit("group_1", 2.0, False)
        0.56

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_equations_37_to_40_and_table_10_router
        Validation cases:
            - LOCAL-PROC-TABLE-10

    Implementation notes:
        - The standard's boundary substitution is explicit and no extrapolation is used.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(edge_stiffened, bool):
        raise TypeError("edge_stiffened must be bool")
    clamped = min(max(_nonnegative(member_relative_slenderness, "member_relative_slenderness"), 0.8), 4.0)
    functions = {
        "group_1": flange_slenderness_limit_eq37,
        "group_2": flange_slenderness_limit_eq38,
        "group_3": flange_slenderness_limit_eq39,
        "group_4": flange_slenderness_limit_eq40,
    }
    try:
        base = functions[table_10_diagram_group](clamped)
    except KeyError as exc:
        raise ValueError("Unsupported table_10_diagram_group") from exc
    if not edge_stiffened:
        return base
    multipliers = {"group_1": 1.5, "group_2": 1.5, "group_3": 1.6}
    if table_10_diagram_group not in multipliers:
        raise ValueError("Table 10 assigns no additional edge-stiffener multiplier to group_4")
    return base * multipliers[table_10_diagram_group]


def edge_stiffener_requirements(
    effective_flange_outstand_mm: float,
    design_yield_resistance_n_mm2: float,
    elastic_modulus_n_mm2: float,
    member_reinforced_with_battens: bool,
) -> dict[str, float]:
    """
    Summary:
        Calculate minimum edge-return height and edge-stiffener thickness under clause 7.3.10.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.10
        Annex: None
        Equation/Table: Unnumbered edge-stiffener requirements following Table 10
        Audit ID: SP16-PROC-7.3.10-EDGE-STIFFENER
        Normative status: normative

    Mathematical form:
        a_eff,min = 0.3b_eff without battens or 0.2b_eff with battens; t_min=2a_eff*sqrt(R_y/E).

    Parameters:
        effective_flange_outstand_mm:
            Type: float
            Unit: mm
            Meaning: Effective flange outstand b_eff.
            Valid range: > 0
            Source: clause 7.3.7
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
            Source: material data
        member_reinforced_with_battens:
            Type: bool
            Unit: boolean
            Meaning: Whether the 0.2b_eff branch applies instead of 0.3b_eff.
            Valid range: true | false
            Source: member configuration

    Returns:
        Type: dict[str, float]
        Unit: mm
        Meaning: Minimum edge-return height and corresponding minimum thickness.

    Assumptions:
        - The edge return or stiffener is the geometry addressed by clause 7.3.10.

    Sign convention:
        - Dimensions and material values are positive magnitudes.

    Unit convention:
        - Lengths use mm; stress units cancel in the square root.

    Applicability:
        - Edge returns/stiffeners associated with the Table 10 flange outstands.

    Limitations:
        - Connection detailing and local stress concentrations are not checked.

    Raises:
        ValueError: Numerical inputs are non-positive or non-finite.
        TypeError: The boolean or numerical input type is invalid.

    Examples:
        >>> edge_stiffener_requirements(100, 355, 206000, False)["minimum_edge_height_mm"]
        30.0

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_edge_stiffener_requirements
        Validation cases:
            - LOCAL-PROC-7.3.10

    Implementation notes:
        - Minimum thickness is calculated from the minimum required edge height.
        - Defaults must be explicit in the input configuration.
    """
    width = _positive(effective_flange_outstand_mm, "effective_flange_outstand_mm")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    if not isinstance(member_reinforced_with_battens, bool):
        raise TypeError("member_reinforced_with_battens must be bool")
    minimum_height = (0.2 if member_reinforced_with_battens else 0.3) * width
    return {
        "minimum_edge_height_mm": minimum_height,
        "minimum_edge_thickness_mm": 2.0 * minimum_height * math.sqrt(ry / elastic),
    }


def two_plane_slenderness_increase_factor(
    stability_coefficient_phi: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    axial_force_n: float,
) -> float:
    """
    Summary:
        Calculate the capped clause 7.3.11 increase factor for wall and flange slenderness limits.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.11
        Annex: None
        Equation/Table: Unnumbered factor after Table 10
        Audit ID: SP16-PROC-7.3.11-TWO-PLANE-INCREASE
        Normative status: normative

    Mathematical form:
        factor = min(sqrt(phi*A*R_y/N), 1.25), with the raw value required to represent an increase.

    Parameters:
        stability_coefficient_phi:
            Type: float
            Unit: dimensionless
            Meaning: Applicable central-compression stability coefficient phi.
            Valid range: 0 < value <= 1
            Source: equation (8)
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross area A.
            Valid range: > 0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Central compression force N.
            Valid range: > 0 and N <= phi*A*R_y for this increase rule
            Source: structural analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Increase factor between 1 and 1.25.

    Assumptions:
        - The two-plane limiting-slenderness check governs section selection as stated in clause 7.3.11.

    Sign convention:
        - Compression force is supplied as a positive magnitude.

    Unit convention:
        - A*R_y and N both use N.

    Applicability:
        - Centrally compressed members for which the clause 10.4 two-plane slenderness condition governs.

    Limitations:
        - The function does not determine whether the clause 10.4 condition is governing.

    Raises:
        ValueError: Inputs are invalid or the raw factor is below 1 and therefore is not an increase.
        TypeError: An input is not real.

    Examples:
        >>> two_plane_slenderness_increase_factor(0.8, 10000, 355, 2000000)
        1.1916375287812984

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_two_plane_increase_factor
        Validation cases:
            - LOCAL-PROC-7.3.11

    Implementation notes:
        - A raw factor below 1 is rejected rather than silently changed to 1.
        - Defaults must be explicit in the input configuration.
    """
    phi = _positive(stability_coefficient_phi, "stability_coefficient_phi")
    if phi > 1.0:
        raise ValueError("stability_coefficient_phi must not exceed 1")
    area = _positive(gross_area_mm2, "gross_area_mm2")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    force = _positive(axial_force_n, "axial_force_n")
    raw = math.sqrt(phi * area * ry / force)
    if raw < 1.0:
        raise ValueError("Clause 7.3.11 factor would be below 1 and would not increase the limits")
    return min(raw, 1.25)


def apply_two_plane_slenderness_increase(
    base_limiting_relative_slenderness: float,
    increase_factor: float,
) -> float:
    """
    Summary:
        Apply a verified clause 7.3.11 increase factor to a wall or flange slenderness limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 7.3.11
        Annex: None
        Equation/Table: Unnumbered multiplication rule
        Audit ID: SP16-PROC-7.3.11-TWO-PLANE-INCREASE
        Normative status: normative

    Mathematical form:
        increased_limit = base_limit*factor, 1 <= factor <= 1.25.

    Parameters:
        base_limiting_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Table 9 or Table 10 limit before the clause 7.3.11 increase.
            Valid range: > 0
            Source: audited table function
        increase_factor:
            Type: float
            Unit: dimensionless
            Meaning: Verified factor from two_plane_slenderness_increase_factor.
            Valid range: 1 <= value <= 1.25
            Source: clause 7.3.11

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Increased limiting relative slenderness.

    Assumptions:
        - The clause 7.3.11 applicability condition has been confirmed.

    Sign convention:
        - Limits and factors are positive magnitudes.

    Unit convention:
        - All values are dimensionless.

    Applicability:
        - Wall and flange limits under clause 7.3.11.

    Limitations:
        - This scalar function does not decide whether the increase is permitted.

    Raises:
        ValueError: The base limit or factor is outside its domain.
        TypeError: An input is not real.

    Examples:
        >>> apply_two_plane_slenderness_increase(2.0, 1.2)
        2.4

    Tests:
        Unit tests:
            - tests/test_local_stability.py::test_two_plane_increase_factor
        Validation cases:
            - LOCAL-PROC-7.3.11-APPLY

    Implementation notes:
        - The 1.25 cap must be applied when calculating the factor, and is rechecked here.
        - Defaults must be explicit in the input configuration.
    """
    base = _positive(base_limiting_relative_slenderness, "base_limiting_relative_slenderness")
    factor = _bounded(increase_factor, "increase_factor", 1.0, 1.25)
    return base * factor
