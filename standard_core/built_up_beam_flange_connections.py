"""Built-up beam flange-connection checks for clause 14.4 and Table 43."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_43 = json.loads((_DATA_DIR / "table_43_built_up_beam_flange_connections.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-14.4.1-SHEAR-FLOW",
    "SP16-PROC-14.4.1-LOCAL-PRESSURE-FLOW",
    "SP16-PROC-14.4.1-LOAD-ROUTE",
    "SP16-PROC-14.4.1-ALPHA",
    "SP16-PROC-14.4.1-FULL-PENETRATION-WELD",
    "SP16-PROC-14.4.2-MULTILAYER-FLANGE-SHEET",
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


def table_43_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited Table 43 load and flange-connection formula catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Table 43
        Audit ID: SP16-TBL-43
        Normative status: normative

    Mathematical form:
        Exact Table 43 rows for stationary and moving concentrated loads with welded or friction flange connections.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: The packaged audited data file is returned.
            Valid range: not applicable
            Source: data/table_43_built_up_beam_flange_connections.json

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Deep-copied Table 43 catalogue.

    Assumptions:
        - Formula symbols follow the definitions printed below Table 43.

    Sign convention:
        - Table formulas use force-per-length magnitudes.

    Unit convention:
        - Force uses N, length uses mm, stress uses N/mm2, and utilization is dimensionless.

    Applicability:
        - Built-up I-beam flange connections governed by clause 14.4.

    Limitations:
        - The function does not classify a physical connection from CAD/BIM geometry.

    Raises:
        RuntimeError: The packaged data file cannot be decoded during module import.

    Examples:
        >>> table_43_catalog()["table"]
        '43'

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_table_43_catalog
        Validation cases:
            - V17-SP16-TBL-43

    Implementation notes:
        - No unstated interpolation or formula substitution is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_43, ensure_ascii=False))


def flange_shear_flow_t_n_mm(
    transverse_shear_force_n: float,
    flange_static_moment_mm3: float,
    gross_section_moment_inertia_mm4: float,
) -> float:
    """
    Summary:
        Calculate the flange shear flow T caused by the beam transverse shear force.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1, definitions below Table 43
        Annex: None
        Equation/Table: T = Q S / I
        Audit ID: SP16-PROC-14.4.1-SHEAR-FLOW
        Normative status: normative

    Mathematical form:
        T = Q*S/I.

    Parameters:
        transverse_shear_force_n:
            Type: float
            Unit: N
            Meaning: Beam transverse force Q.
            Valid range: finite signed value
            Source: global structural analysis
        flange_static_moment_mm3:
            Type: float
            Unit: mm3
            Meaning: Gross static moment S of the flange about the section centroidal axis.
            Valid range: greater than zero
            Source: gross section properties
        gross_section_moment_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Gross moment of inertia I of the beam section.
            Valid range: greater than zero
            Source: gross section properties

    Returns:
        Type: float
        Unit: N/mm
        Meaning: Signed flange shear flow T.

    Assumptions:
        - Q, S, and I refer to the same beam section and axis.
        - Gross section properties are used as stated by Table 43.

    Sign convention:
        - The sign of T follows the sign of Q; utilization functions use its magnitude.

    Unit convention:
        - N*mm3/mm4 gives N/mm.

    Applicability:
        - Flange-to-web connections of built-up beams under transverse shear.

    Limitations:
        - The function does not determine the governing section or load combination.

    Raises:
        TypeError: An input is not a real number.
        ValueError: A geometric property is non-positive or an input is non-finite.

    Examples:
        >>> flange_shear_flow_t_n_mm(240000.0, 1.2e6, 8.0e8)
        360.0

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_shear_and_local_pressure_flows
        Validation cases:
            - V17-SP16-PROC-14.4.1-SHEAR-FLOW

    Implementation notes:
        - No unit conversion is performed.
        - Defaults must be explicit in the input configuration.
    """
    q = _real(transverse_shear_force_n, "transverse_shear_force_n")
    s = _positive(flange_static_moment_mm3, "flange_static_moment_mm3")
    inertia = _positive(gross_section_moment_inertia_mm4, "gross_section_moment_inertia_mm4")
    return q * s / inertia


def local_load_line_pressure_v_n_mm(
    load_factor_gamma_f: float,
    local_load_factor_gamma_f1: float,
    concentrated_load_n: float,
    effective_distribution_length_mm: float,
) -> float:
    """
    Summary:
        Calculate the concentrated-load pressure V per unit beam length.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1, definitions below Table 43
        Annex: None
        Equation/Table: V = gamma_f*gamma_f1*F_n/l_ef
        Audit ID: SP16-PROC-14.4.1-LOCAL-PRESSURE-FLOW
        Normative status: normative

    Mathematical form:
        V = gamma_f*gamma_f1*F_n/l_ef.

    Parameters:
        load_factor_gamma_f:
            Type: float
            Unit: dimensionless
            Meaning: Load reliability factor gamma_f.
            Valid range: greater than zero
            Source: SP 20.13330
        local_load_factor_gamma_f1:
            Type: float
            Unit: dimensionless
            Meaning: Additional load factor gamma_f1; equals 1 for stationary loads.
            Valid range: greater than zero
            Source: SP 20.13330 and Table 43 definition
        concentrated_load_n:
            Type: float
            Unit: N
            Meaning: Normative concentrated load F_n.
            Valid range: non-negative
            Source: loading model
        effective_distribution_length_mm:
            Type: float
            Unit: mm
            Meaning: Effective length l_ef from clauses 8.2.2 or 8.3.3.
            Valid range: greater than zero
            Source: linked audited calculation

    Returns:
        Type: float
        Unit: N/mm
        Meaning: Non-negative local pressure V per unit beam length.

    Assumptions:
        - The effective length has been determined under the linked beam-web rules.
        - For a stationary load, the caller supplies gamma_f1 = 1 explicitly.

    Sign convention:
        - V is a non-negative pressure magnitude.

    Unit convention:
        - Dimensionless factors times N divided by mm gives N/mm.

    Applicability:
        - Concentrated loads transferred through built-up beam flange connections.

    Limitations:
        - The function does not derive load factors or l_ef.

    Raises:
        TypeError: An input is not a real number.
        ValueError: A factor or length is non-positive, or the load is negative.

    Examples:
        >>> local_load_line_pressure_v_n_mm(1.2, 1.1, 100000.0, 250.0)
        528.0

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_shear_and_local_pressure_flows
        Validation cases:
            - V17-SP16-PROC-14.4.1-LOCAL-PRESSURE-FLOW

    Implementation notes:
        - The stationary-load gamma_f1 rule is not inserted silently.
        - Defaults must be explicit in the input configuration.
    """
    gamma_f = _positive(load_factor_gamma_f, "load_factor_gamma_f")
    gamma_f1 = _positive(local_load_factor_gamma_f1, "local_load_factor_gamma_f1")
    force = _nonnegative(concentrated_load_n, "concentrated_load_n")
    length = _positive(effective_distribution_length_mm, "effective_distribution_length_mm")
    return gamma_f * gamma_f1 * force / length


def table_43_load_route(
    nominal_load_character: str,
    loaded_flange: str,
    *,
    transverse_stiffener_at_load: bool,
) -> dict[str, Any]:
    """
    Summary:
        Select the stationary or moving Table 43 calculation route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Table 43 routing paragraph
        Audit ID: SP16-PROC-14.4.1-LOAD-ROUTE
        Normative status: normative

    Mathematical form:
        Stationary upper-flange load without a transverse stiffener and every stationary lower-flange load use the moving-load formulas.

    Parameters:
        nominal_load_character:
            Type: str
            Unit: not applicable
            Meaning: Nominal load character.
            Valid range: stationary | moving
            Source: loading definition
        loaded_flange:
            Type: str
            Unit: not applicable
            Meaning: Flange receiving the concentrated load.
            Valid range: upper | lower
            Source: beam geometry and load application
        transverse_stiffener_at_load:
            Type: bool
            Unit: not applicable
            Meaning: Whether a transverse stiffener transfers the load at the application point.
            Valid range: true or false
            Source: connection detailing

    Returns:
        Type: dict[str, Any]
        Unit: categorical result
        Meaning: Effective Table 43 route and reason.

    Assumptions:
        - The load is a concentrated action relevant to the flange connection.

    Sign convention:
        - Not applicable.

    Unit convention:
        - No numerical units.

    Applicability:
        - Route selection immediately above Table 43.

    Limitations:
        - This does not assess the capacity of the transverse stiffener.

    Raises:
        TypeError: A categorical input has the wrong type.
        ValueError: A categorical value is unsupported.

    Examples:
        >>> table_43_load_route("stationary", "lower", transverse_stiffener_at_load=True)["effective_load_character"]
        'moving'

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_table_43_route
        Validation cases:
            - V17-SP16-PROC-14.4.1-LOAD-ROUTE

    Implementation notes:
        - The standard's conservative re-routing is explicit in the returned reason.
        - Defaults must be explicit in the input configuration.
    """
    nominal = _choice(nominal_load_character, {"stationary", "moving"}, "nominal_load_character")
    flange = _choice(loaded_flange, {"upper", "lower"}, "loaded_flange")
    if not isinstance(transverse_stiffener_at_load, bool):
        raise TypeError("transverse_stiffener_at_load must be boolean")
    if nominal == "moving":
        return {
            "nominal_load_character": nominal,
            "effective_load_character": "moving",
            "reason": "nominal_moving_load",
        }
    if flange == "lower":
        return {
            "nominal_load_character": nominal,
            "effective_load_character": "moving",
            "reason": "stationary_lower_flange_load_is_checked_as_moving_regardless_of_stiffener",
        }
    if not transverse_stiffener_at_load:
        return {
            "nominal_load_character": nominal,
            "effective_load_character": "moving",
            "reason": "stationary_upper_flange_load_without_transverse_stiffener_is_checked_as_moving",
        }
    return {
        "nominal_load_character": nominal,
        "effective_load_character": "stationary",
        "reason": "stationary_upper_flange_load_transferred_by_transverse_stiffener",
    }


def table_43_alpha(
    loaded_flange: str,
    *,
    web_edge_planed_to_loaded_upper_flange: bool,
) -> float:
    """
    Summary:
        Determine the Table 43 coefficient alpha for a moving-load friction connection.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1, definitions below Table 43
        Annex: None
        Equation/Table: alpha definition for equation (198)
        Audit ID: SP16-PROC-14.4.1-ALPHA
        Normative status: normative

    Mathematical form:
        alpha = 0.4 for an upper-flange load when the web edge is planed to that flange; otherwise alpha = 1.0.

    Parameters:
        loaded_flange:
            Type: str
            Unit: not applicable
            Meaning: Loaded flange.
            Valid range: upper | lower
            Source: beam geometry and load application
        web_edge_planed_to_loaded_upper_flange:
            Type: bool
            Unit: not applicable
            Meaning: Whether the web edge is planed for bearing against the loaded upper flange.
            Valid range: true or false
            Source: fabrication detailing

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Table 43 alpha coefficient.

    Assumptions:
        - The boolean describes the "пристрожка стенки" condition stated in the standard.

    Sign convention:
        - Alpha is positive.

    Unit convention:
        - Dimensionless.

    Applicability:
        - Equation (198).

    Limitations:
        - Fabrication quality and actual contact are not verified.

    Raises:
        TypeError: The boolean input has the wrong type.
        ValueError: The flange category is unsupported.

    Examples:
        >>> table_43_alpha("upper", web_edge_planed_to_loaded_upper_flange=True)
        0.4

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_table_43_alpha
        Validation cases:
            - V17-SP16-PROC-14.4.1-ALPHA

    Implementation notes:
        - Alpha is not inferred from the transverse-stiffener condition.
        - Defaults must be explicit in the input configuration.
    """
    flange = _choice(loaded_flange, {"upper", "lower"}, "loaded_flange")
    if not isinstance(web_edge_planed_to_loaded_upper_flange, bool):
        raise TypeError("web_edge_planed_to_loaded_upper_flange must be boolean")
    if flange == "upper" and web_edge_planed_to_loaded_upper_flange:
        return 0.4
    return 1.0


def stationary_weld_metal_utilization_eq193(
    shear_flow_t_n_mm: float,
    weld_line_count: int,
    weld_coefficient_beta_f: float,
    weld_leg_mm: float,
    weld_metal_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a welded flange connection under a stationary load along the weld-metal plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (193), Table 43
        Audit ID: SP16-EQ-193
        Normative status: normative

    Mathematical form:
        eta = |T|/(n*beta_f*k_f*R_wf*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        weld_line_count:
            Type: int
            Unit: count
            Meaning: Number n of fillet weld lines.
            Valid range: 1 or 2
            Source: connection detailing
        weld_coefficient_beta_f:
            Type: float
            Unit: dimensionless
            Meaning: Weld coefficient beta_f.
            Valid range: greater than zero
            Source: Table 39
        weld_leg_mm:
            Type: float
            Unit: mm
            Meaning: Fillet weld leg k_f.
            Valid range: greater than zero
            Source: connection detailing
        weld_metal_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_wf of weld metal.
            Valid range: greater than zero
            Source: Table 4 or audited material block
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (193) utilization.

    Assumptions:
        - The stationary-load Table 43 route is applicable.

    Sign convention:
        - T may be signed; utilization uses |T|.

    Unit convention:
        - N/mm divided by mm*N/mm2 gives dimensionless utilization.

    Applicability:
        - Stationary-load welded flange connection.

    Limitations:
        - Weld size, detailing, and connected-element strength require their separate checks.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: A denominator input is non-positive or n is not 1 or 2.

    Examples:
        >>> round(stationary_weld_metal_utilization_eq193(360, 2, 0.8, 8, 240, 1.0), 6)
        0.117188

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_193_to_195
        Validation cases:
            - V17-SP16-EQ-193

    Implementation notes:
        - Pass/fail is eta <= 1.
        - Defaults must be explicit in the input configuration.
    """
    if isinstance(weld_line_count, bool) or not isinstance(weld_line_count, int) or weld_line_count not in {1, 2}:
        raise ValueError("weld_line_count must be 1 or 2")
    denominator = (
        weld_line_count
        * _positive(weld_coefficient_beta_f, "weld_coefficient_beta_f")
        * _positive(weld_leg_mm, "weld_leg_mm")
        * _positive(weld_metal_design_resistance_n_mm2, "weld_metal_design_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return abs(_real(shear_flow_t_n_mm, "shear_flow_t_n_mm")) / denominator


def stationary_fusion_boundary_utilization_eq194(
    shear_flow_t_n_mm: float,
    weld_line_count: int,
    weld_coefficient_beta_z: float,
    weld_leg_mm: float,
    fusion_boundary_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a welded flange connection under a stationary load along the fusion-boundary plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (194), Table 43
        Audit ID: SP16-EQ-194
        Normative status: normative

    Mathematical form:
        eta = |T|/(n*beta_z*k_f*R_wz*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        weld_line_count:
            Type: int
            Unit: count
            Meaning: Number n of fillet weld lines.
            Valid range: 1 or 2
            Source: connection detailing
        weld_coefficient_beta_z:
            Type: float
            Unit: dimensionless
            Meaning: Weld coefficient beta_z.
            Valid range: greater than zero
            Source: Table 39
        weld_leg_mm:
            Type: float
            Unit: mm
            Meaning: Fillet weld leg k_f.
            Valid range: greater than zero
            Source: connection detailing
        fusion_boundary_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_wz along the fusion boundary.
            Valid range: greater than zero
            Source: Table 4 or audited material block
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (194) utilization.

    Assumptions:
        - The stationary-load Table 43 route is applicable.

    Sign convention:
        - T may be signed; utilization uses |T|.

    Unit convention:
        - N/mm divided by mm*N/mm2 gives dimensionless utilization.

    Applicability:
        - Stationary-load welded flange connection.

    Limitations:
        - The function does not replace weld detailing or base-metal checks.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: A denominator input is non-positive or n is not 1 or 2.

    Examples:
        >>> round(stationary_fusion_boundary_utilization_eq194(360, 2, 1.0, 8, 215, 1.0), 6)
        0.104651

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_193_to_195
        Validation cases:
            - V17-SP16-EQ-194

    Implementation notes:
        - Pass/fail is eta <= 1.
        - Defaults must be explicit in the input configuration.
    """
    if isinstance(weld_line_count, bool) or not isinstance(weld_line_count, int) or weld_line_count not in {1, 2}:
        raise ValueError("weld_line_count must be 1 or 2")
    denominator = (
        weld_line_count
        * _positive(weld_coefficient_beta_z, "weld_coefficient_beta_z")
        * _positive(weld_leg_mm, "weld_leg_mm")
        * _positive(fusion_boundary_design_resistance_n_mm2, "fusion_boundary_design_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return abs(_real(shear_flow_t_n_mm, "shear_flow_t_n_mm")) / denominator


def stationary_friction_utilization_eq195(
    shear_flow_t_n_mm: float,
    bolt_pitch_mm: float,
    friction_plane_capacity_n: float,
    friction_plane_count: int,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a friction flange connection under a stationary load.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (195), Table 43
        Audit ID: SP16-EQ-195
        Normative status: normative

    Mathematical form:
        eta = |T|*s/(Q_bh*k*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        bolt_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Pitch s of flange bolts.
            Valid range: greater than zero
            Source: connection geometry
        friction_plane_capacity_n:
            Type: float
            Unit: N
            Meaning: Q_bh capacity of one friction plane tightened by one bolt.
            Valid range: greater than zero
            Source: equation (191)
        friction_plane_count:
            Type: int
            Unit: count
            Meaning: Number k of friction planes.
            Valid range: positive integer
            Source: connection geometry
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (195) utilization.

    Assumptions:
        - Q_bh and k are determined consistently under clauses 14.3.3-14.3.4.

    Sign convention:
        - T may be signed; utilization uses |T|.

    Unit convention:
        - N/mm times mm divided by N gives dimensionless utilization.

    Applicability:
        - Stationary-load friction flange connection.

    Limitations:
        - Bolt spacing and installation requirements remain separate checks.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: A denominator input is non-positive or k is not a positive integer.

    Examples:
        >>> stationary_friction_utilization_eq195(360, 80, 25000, 2, 1.0)
        0.576

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_193_to_195
        Validation cases:
            - V17-SP16-EQ-195

    Implementation notes:
        - Pass/fail is eta <= 1.
        - Defaults must be explicit in the input configuration.
    """
    if isinstance(friction_plane_count, bool) or not isinstance(friction_plane_count, int) or friction_plane_count <= 0:
        raise ValueError("friction_plane_count must be a positive integer")
    numerator = abs(_real(shear_flow_t_n_mm, "shear_flow_t_n_mm")) * _positive(bolt_pitch_mm, "bolt_pitch_mm")
    denominator = (
        _positive(friction_plane_capacity_n, "friction_plane_capacity_n")
        * friction_plane_count
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return numerator / denominator


def moving_weld_metal_utilization_eq196(
    shear_flow_t_n_mm: float,
    local_pressure_v_n_mm: float,
    weld_coefficient_beta_f: float,
    weld_leg_mm: float,
    weld_metal_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a two-sided welded flange connection under a moving-load route along the weld-metal plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (196), Table 43
        Audit ID: SP16-EQ-196
        Normative status: normative

    Mathematical form:
        eta = sqrt(T^2+V^2)/(2*beta_f*k_f*R_wf*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        local_pressure_v_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Local concentrated-load pressure V.
            Valid range: non-negative
            Source: V = gamma_f*gamma_f1*F_n/l_ef
        weld_coefficient_beta_f:
            Type: float
            Unit: dimensionless
            Meaning: Weld coefficient beta_f.
            Valid range: greater than zero
            Source: Table 39
        weld_leg_mm:
            Type: float
            Unit: mm
            Meaning: Fillet weld leg k_f.
            Valid range: greater than zero
            Source: connection detailing
        weld_metal_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_wf of weld metal.
            Valid range: greater than zero
            Source: Table 4 or audited material block
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (196) utilization.

    Assumptions:
        - Two-sided fillet welds are provided as required by the Table 43 row.
        - The moving-load route is applicable.

    Sign convention:
        - T may be signed; the quadratic interaction removes its sign.
        - V is a non-negative magnitude.

    Unit convention:
        - All line forces use N/mm.

    Applicability:
        - Moving-load welded flange connection with two-sided welds.

    Limitations:
        - One-sided welds are not covered by this Table 43 row.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: A denominator input is non-positive or V is negative.

    Examples:
        >>> moving_weld_metal_utilization_eq196(360, 528, 0.8, 8, 240, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_196_to_198
        Validation cases:
            - V17-SP16-EQ-196

    Implementation notes:
        - The factor 2 is fixed by the two-sided-weld Table 43 row.
        - Defaults must be explicit in the input configuration.
    """
    resultant = math.hypot(
        _real(shear_flow_t_n_mm, "shear_flow_t_n_mm"),
        _nonnegative(local_pressure_v_n_mm, "local_pressure_v_n_mm"),
    )
    denominator = (
        2.0
        * _positive(weld_coefficient_beta_f, "weld_coefficient_beta_f")
        * _positive(weld_leg_mm, "weld_leg_mm")
        * _positive(weld_metal_design_resistance_n_mm2, "weld_metal_design_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return resultant / denominator


def moving_fusion_boundary_utilization_eq197(
    shear_flow_t_n_mm: float,
    local_pressure_v_n_mm: float,
    weld_coefficient_beta_z: float,
    weld_leg_mm: float,
    fusion_boundary_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a two-sided welded flange connection under a moving-load route along the fusion-boundary plane.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (197), Table 43
        Audit ID: SP16-EQ-197
        Normative status: normative

    Mathematical form:
        eta = sqrt(T^2+V^2)/(2*beta_z*k_f*R_wz*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        local_pressure_v_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Local concentrated-load pressure V.
            Valid range: non-negative
            Source: V = gamma_f*gamma_f1*F_n/l_ef
        weld_coefficient_beta_z:
            Type: float
            Unit: dimensionless
            Meaning: Weld coefficient beta_z.
            Valid range: greater than zero
            Source: Table 39
        weld_leg_mm:
            Type: float
            Unit: mm
            Meaning: Fillet weld leg k_f.
            Valid range: greater than zero
            Source: connection detailing
        fusion_boundary_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design shear resistance R_wz along the fusion boundary.
            Valid range: greater than zero
            Source: Table 4 or audited material block
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (197) utilization.

    Assumptions:
        - Two-sided fillet welds are provided as required by the Table 43 row.
        - The moving-load route is applicable.

    Sign convention:
        - T may be signed; the quadratic interaction removes its sign.
        - V is a non-negative magnitude.

    Unit convention:
        - All line forces use N/mm.

    Applicability:
        - Moving-load welded flange connection with two-sided welds.

    Limitations:
        - One-sided welds are not covered by this Table 43 row.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: A denominator input is non-positive or V is negative.

    Examples:
        >>> moving_fusion_boundary_utilization_eq197(360, 528, 1.0, 8, 215, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_196_to_198
        Validation cases:
            - V17-SP16-EQ-197

    Implementation notes:
        - The factor 2 is fixed by the two-sided-weld Table 43 row.
        - Defaults must be explicit in the input configuration.
    """
    resultant = math.hypot(
        _real(shear_flow_t_n_mm, "shear_flow_t_n_mm"),
        _nonnegative(local_pressure_v_n_mm, "local_pressure_v_n_mm"),
    )
    denominator = (
        2.0
        * _positive(weld_coefficient_beta_z, "weld_coefficient_beta_z")
        * _positive(weld_leg_mm, "weld_leg_mm")
        * _positive(fusion_boundary_design_resistance_n_mm2, "fusion_boundary_design_resistance_n_mm2")
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return resultant / denominator


def moving_friction_utilization_eq198(
    shear_flow_t_n_mm: float,
    local_pressure_v_n_mm: float,
    alpha: float,
    bolt_pitch_mm: float,
    friction_plane_capacity_n: float,
    friction_plane_count: int,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Check a friction flange connection under a moving-load route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Equation (198), Table 43
        Audit ID: SP16-EQ-198
        Normative status: normative

    Mathematical form:
        eta = s*sqrt(T^2+alpha^2*V^2)/(Q_bh*k*gamma_c).

    Parameters:
        shear_flow_t_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Flange shear flow T.
            Valid range: finite signed value
            Source: T = Q*S/I
        local_pressure_v_n_mm:
            Type: float
            Unit: N/mm
            Meaning: Local concentrated-load pressure V.
            Valid range: non-negative
            Source: V = gamma_f*gamma_f1*F_n/l_ef
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Table 43 alpha coefficient.
            Valid range: 0.4 or 1.0
            Source: table_43_alpha
        bolt_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Pitch s of flange bolts.
            Valid range: greater than zero
            Source: connection geometry
        friction_plane_capacity_n:
            Type: float
            Unit: N
            Meaning: Q_bh capacity of one friction plane tightened by one bolt.
            Valid range: greater than zero
            Source: equation (191)
        friction_plane_count:
            Type: int
            Unit: count
            Meaning: Number k of friction planes.
            Valid range: positive integer
            Source: connection geometry
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: greater than zero
            Source: project input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Equation (198) utilization.

    Assumptions:
        - Q_bh and k are determined consistently under clauses 14.3.3-14.3.4.
        - The moving-load route is applicable.

    Sign convention:
        - T may be signed; the quadratic interaction removes its sign.
        - V is a non-negative magnitude.

    Unit convention:
        - N/mm times mm divided by N gives dimensionless utilization.

    Applicability:
        - Moving-load friction flange connection.

    Limitations:
        - The function does not verify the physical planing/contact condition used to select alpha.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: Alpha is not 0.4 or 1.0, k is invalid, or a denominator input is non-positive.

    Examples:
        >>> moving_friction_utilization_eq198(360, 528, 0.4, 80, 25000, 2, 1.0) > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_equations_196_to_198
        Validation cases:
            - V17-SP16-EQ-198

    Implementation notes:
        - Pass/fail is eta <= 1.
        - Defaults must be explicit in the input configuration.
    """
    alpha_value = _real(alpha, "alpha")
    if alpha_value not in {0.4, 1.0}:
        raise ValueError("alpha must be exactly 0.4 or 1.0 under Table 43")
    if isinstance(friction_plane_count, bool) or not isinstance(friction_plane_count, int) or friction_plane_count <= 0:
        raise ValueError("friction_plane_count must be a positive integer")
    resultant = math.hypot(
        _real(shear_flow_t_n_mm, "shear_flow_t_n_mm"),
        alpha_value * _nonnegative(local_pressure_v_n_mm, "local_pressure_v_n_mm"),
    )
    numerator = _positive(bolt_pitch_mm, "bolt_pitch_mm") * resultant
    denominator = (
        _positive(friction_plane_capacity_n, "friction_plane_capacity_n")
        * friction_plane_count
        * _positive(working_condition_factor, "working_condition_factor")
    )
    return numerator / denominator


def full_penetration_web_weld_equivalence_14_4_1(
    full_penetration_through_web_thickness: bool,
) -> dict[str, Any]:
    """
    Summary:
        Classify a full-penetration flange-to-web weld as equal-strength with the web.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.1
        Annex: None
        Equation/Table: Paragraph after Table 43 routing rule
        Audit ID: SP16-PROC-14.4.1-FULL-PENETRATION-WELD
        Normative status: normative

    Mathematical form:
        A weld made with penetration through the full web thickness is treated as equal-strength with the web.

    Parameters:
        full_penetration_through_web_thickness:
            Type: bool
            Unit: not applicable
            Meaning: Whether the weld penetrates the full web thickness.
            Valid range: true or false
            Source: weld detail and fabrication specification

    Returns:
        Type: dict[str, Any]
        Unit: categorical result
        Meaning: Equal-strength classification and limitation note.

    Assumptions:
        - The full-penetration condition is supported by the welding specification and quality control.

    Sign convention:
        - Not applicable.

    Unit convention:
        - No numerical units.

    Applicability:
        - Flange-to-web welded connection in clause 14.4.1.

    Limitations:
        - The function does not verify weld quality, NDT evidence, or procedure qualification.

    Raises:
        TypeError: The input is not boolean.

    Examples:
        >>> full_penetration_web_weld_equivalence_14_4_1(True)["equal_strength_with_web"]
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_full_penetration_and_multilayer_sheet_routes
        Validation cases:
            - V17-SP16-PROC-14.4.1-FULL-PENETRATION-WELD

    Implementation notes:
        - The result is an evidence-based classification, not an inspection record.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(full_penetration_through_web_thickness, bool):
        raise TypeError("full_penetration_through_web_thickness must be boolean")
    return {
        "full_penetration_through_web_thickness": full_penetration_through_web_thickness,
        "equal_strength_with_web": full_penetration_through_web_thickness,
        "evidence_required": "weld_detail_procedure_and_quality_control",
    }


def multilayer_flange_sheet_attachment_force_14_4_2(
    sheet_section_force_capacity_n: float,
    attachment_segment: str,
) -> dict[str, Any]:
    """
    Summary:
        Determine the attachment force for one sheet in a multilayer friction-connected flange package.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.4.2
        Annex: None
        Equation/Table: Multilayer flange-sheet attachment procedure
        Audit ID: SP16-PROC-14.4.2-MULTILAYER-FLANGE-SHEET
        Normative status: normative

    Mathematical form:
        Beyond the theoretical cutoff use 0.5*N_sheet; between the actual cutoff and the previous sheet cutoff use 1.0*N_sheet.

    Parameters:
        sheet_section_force_capacity_n:
            Type: float
            Unit: N
            Meaning: Force that can be resisted by the sheet section.
            Valid range: non-negative
            Source: audited sheet-section resistance calculation
        attachment_segment:
            Type: str
            Unit: not applicable
            Meaning: Segment of the sheet attachment being designed.
            Valid range: beyond_theoretical_cutoff | between_actual_and_previous_sheet_cutoff
            Source: multilayer flange detailing

    Returns:
        Type: dict[str, Any]
        Unit: N and dimensionless factor
        Meaning: Required attachment force and applicable fraction.

    Assumptions:
        - The flange uses friction connections and a multilayer flange package.
        - The sheet-section force capacity is already established.

    Sign convention:
        - Force capacity and required attachment force are non-negative magnitudes.

    Unit convention:
        - Force uses N.

    Applicability:
        - Clause 14.4.2.

    Limitations:
        - The function does not locate theoretical or actual cutoff points from a beam-force diagram.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: The force is negative or the segment category is unsupported.

    Examples:
        >>> multilayer_flange_sheet_attachment_force_14_4_2(500000, "beyond_theoretical_cutoff")["required_attachment_force_n"]
        250000.0

    Tests:
        Unit tests:
            - tests/test_built_up_beam_flange_connections.py::test_full_penetration_and_multilayer_sheet_routes
        Validation cases:
            - V17-SP16-PROC-14.4.2-MULTILAYER-FLANGE-SHEET

    Implementation notes:
        - No sheet sequence or cutoff geometry is inferred.
        - Defaults must be explicit in the input configuration.
    """
    capacity = _nonnegative(sheet_section_force_capacity_n, "sheet_section_force_capacity_n")
    segment = _choice(
        attachment_segment,
        {"beyond_theoretical_cutoff", "between_actual_and_previous_sheet_cutoff"},
        "attachment_segment",
    )
    factor = 0.5 if segment == "beyond_theoretical_cutoff" else 1.0
    return {
        "attachment_segment": segment,
        "force_fraction": factor,
        "sheet_section_force_capacity_n": capacity,
        "required_attachment_force_n": factor * capacity,
    }


__all__ = [
    "IMPLEMENTED_PROCEDURE_IDS",
    "table_43_catalog",
    "flange_shear_flow_t_n_mm",
    "local_load_line_pressure_v_n_mm",
    "table_43_load_route",
    "table_43_alpha",
    "stationary_weld_metal_utilization_eq193",
    "stationary_fusion_boundary_utilization_eq194",
    "stationary_friction_utilization_eq195",
    "moving_weld_metal_utilization_eq196",
    "moving_fusion_boundary_utilization_eq197",
    "moving_friction_utilization_eq198",
    "full_penetration_web_weld_equivalence_14_4_1",
    "multilayer_flange_sheet_attachment_force_14_4_2",
]
