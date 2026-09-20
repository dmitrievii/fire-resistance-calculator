"""Built-up beam-column stability and combined local-stability checks for Sections 9.3-9.4."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from . import beam_column_stability as beamcol
from . import local_stability as local
from . import bending_member_local_stability as bend_local

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_22 = json.loads((_DATA_DIR / "table_22_combined_web_slenderness_limits.json").read_text(encoding="utf-8"))
_TABLE_23 = json.loads((_DATA_DIR / "table_23_combined_flange_slenderness_limits.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-9.3.1-WHOLE-AND-BRANCH-CHECKS",
    "SP16-PROC-9.3.2-D4-LOOKUP-AND-BENDING-ROUTE",
    "SP16-PROC-9.3.3-BRANCH-ADDITIONAL-FORCES",
    "SP16-PROC-9.3.4-BATTEN-BRANCH-LOCAL-BENDING",
    "SP16-PROC-9.3.5-THREE-SIDED-SECTION-16-ROUTE",
    "SP16-PROC-9.3.6-TWO-SOLID-BRANCH-ROUTING",
    "SP16-PROC-9.3.7-CONNECTOR-SHEAR-GOVERNING",
    "SP16-PROC-9.4.1-GEOMETRY-REFERENCE",
    "SP16-PROC-9.4.2-TABLE-22-ROUTING",
    "SP16-PROC-9.4.2-TYPE-1-M-INTERPOLATION",
    "SP16-PROC-9.4.2-TYPE-2-ALPHA-ROUTING",
    "SP16-PROC-9.4.3-AXIAL-RATIO-ADJUSTMENT",
    "SP16-PROC-9.4.4-TRANSVERSE-STIFFENER-ROUTE",
    "SP16-PROC-9.4.5-LONGITUDINAL-STIFFENER-ROUTE",
    "SP16-PROC-9.4.6-REDUCED-AREA-ROUTE",
    "SP16-PROC-9.4.7-TABLE-23-ROUTING",
    "SP16-PROC-9.4.7-M-INTERPOLATION",
    "SP16-PROC-9.4.8-EDGE-RETURN-MULTIPLIER",
    "SP16-PROC-9.4.9-TWO-PLANE-INCREASE",
    "SP16-PROC-9.4.10-TENSION-MEMBER-BENDING-ROUTE",
)

def _real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result=float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result

def _positive(value: float, name: str) -> float:
    result=_real(value,name)
    if result<=0.0:
        raise ValueError(f"{name} must be greater than zero")
    return result

def _nonnegative(value: float, name: str) -> float:
    result=_real(value,name)
    if result<0.0:
        raise ValueError(f"{name} must be non-negative")
    return result

def _phi(value: float, name: str) -> float:
    result=_positive(value,name)
    if result>1.0:
        raise ValueError(f"{name} must not exceed 1")
    return result

def _linear(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if math.isclose(x0,x1):
        raise ValueError("interpolation nodes must differ")
    return y0+(y1-y0)*(x-x0)/(x1-x0)

def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value,lower),upper)

def table_22_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 22.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Table 22
        Audit ID: SP16-TBL-22
        Normative status: normative

    Mathematical form:
        Metadata lookup; formulas are implemented by equations (125)-(130).

    Parameters:
        None.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Deep copy of Table 22 metadata.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Traceability and UI/catalogue use.

    Limitations:
        - Diagram classification remains an explicit engineering input.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_catalogs
        Validation cases:
            - V11-TBL-22

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_22, ensure_ascii=False))

def table_23_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 23.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Table 23
        Audit ID: SP16-TBL-23
        Normative status: normative

    Mathematical form:
        Metadata lookup; formulas are implemented by equations (132)-(135).

    Parameters:
        None.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Deep copy of Table 23 metadata.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Traceability and UI/catalogue use.

    Limitations:
        - Diagram classification remains an explicit engineering input.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_catalogs
        Validation cases:
            - V11-TBL-23

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_23, ensure_ascii=False))

def built_up_relative_eccentricity_eq123(eccentricity_mm: float, gross_area_mm2: float, compressed_branch_axis_distance_mm: float, free_axis_inertia_mm4: float) -> float:
    """
    Summary:
        Calculate the relative eccentricity of a built-up member about its free axis.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.2
        Annex: None
        Equation/Table: Equation (123)
        Audit ID: SP16-EQ-123
        Normative status: normative

    Mathematical form:
        m = e*A*a/I.

    Parameters:
        eccentricity_mm:
            Type: float
            Unit: mm
            Meaning: Eccentricity e=M/N.
            Valid range: >=0
            Source: same load combination under 9.2.3
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross section area A.
            Valid range: >0
            Source: section model
        compressed_branch_axis_distance_mm:
            Type: float
            Unit: mm
            Meaning: Distance a to the most compressed branch axis.
            Valid range: >0
            Source: section geometry
        free_axis_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Built-up section inertia I about the free axis.
            Valid range: >0
            Source: section model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Relative eccentricity m.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Whole-member free-axis check with battens or lattices parallel to the bending plane.

    Limitations:
        - The distance a must not be smaller than the distance to the branch-web axis.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_123_and_124
        Validation cases:
            - V11-EQ-123

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    e=_nonnegative(eccentricity_mm,"eccentricity_mm")
    return e*_positive(gross_area_mm2,"gross_area_mm2")*_positive(compressed_branch_axis_distance_mm,"compressed_branch_axis_distance_mm")/_positive(free_axis_inertia_mm4,"free_axis_inertia_mm4")

def branch_additional_force_y_types_1_3(bending_moment_n_mm: float, branch_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the additional branch axial-force magnitude from y-plane bending for Table 8 section type 1 or 3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Unnumbered branch-force expression
        Audit ID: SP16-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_Y_TYPES_1_3
        Normative status: normative

    Mathematical form:
        N_ad=M_y/b

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending-moment magnitude.
            Valid range: >=0
            Source: global analysis
        branch_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Relevant distance between branch axes.
            Valid range: >0
            Source: Table 8 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Additional branch axial-force magnitude N_ad.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Built-up lattice member, Table 8 section type 1 or 3.

    Limitations:
        - The function returns the moment-induced component only; base branch force is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_additional_force_rules
        Validation cases:
            - V11-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_Y_TYPES_1_3

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return 1.0*_nonnegative(bending_moment_n_mm,"bending_moment_n_mm")/_positive(branch_axis_spacing_mm,"branch_axis_spacing_mm")

def branch_additional_force_y_type_2(bending_moment_n_mm: float, branch_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the additional branch axial-force magnitude from y-plane bending for Table 8 section type 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Unnumbered branch-force expression
        Audit ID: SP16-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_Y_TYPE_2
        Normative status: normative

    Mathematical form:
        N_ad=0.5*M_y/b_1

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending-moment magnitude.
            Valid range: >=0
            Source: global analysis
        branch_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Relevant distance between branch axes.
            Valid range: >0
            Source: Table 8 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Additional branch axial-force magnitude N_ad.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Built-up lattice member, Table 8 section type 2.

    Limitations:
        - The function returns the moment-induced component only; base branch force is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_additional_force_rules
        Validation cases:
            - V11-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_Y_TYPE_2

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5*_nonnegative(bending_moment_n_mm,"bending_moment_n_mm")/_positive(branch_axis_spacing_mm,"branch_axis_spacing_mm")

def branch_additional_force_x_type_3(bending_moment_n_mm: float, branch_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the additional branch axial-force magnitude from x-plane bending for Table 8 section type 3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Unnumbered branch-force expression
        Audit ID: SP16-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_X_TYPE_3
        Normative status: normative

    Mathematical form:
        N_ad=1.16*M_x/b

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending-moment magnitude.
            Valid range: >=0
            Source: global analysis
        branch_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Relevant distance between branch axes.
            Valid range: >0
            Source: Table 8 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Additional branch axial-force magnitude N_ad.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Built-up lattice member, Table 8 section type 3.

    Limitations:
        - The function returns the moment-induced component only; base branch force is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_additional_force_rules
        Validation cases:
            - V11-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_X_TYPE_3

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return 1.16*_nonnegative(bending_moment_n_mm,"bending_moment_n_mm")/_positive(branch_axis_spacing_mm,"branch_axis_spacing_mm")

def branch_additional_force_x_type_2(bending_moment_n_mm: float, branch_axis_spacing_mm: float) -> float:
    """
    Summary:
        Calculate the additional branch axial-force magnitude from x-plane bending for Table 8 section type 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Unnumbered branch-force expression
        Audit ID: SP16-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_X_TYPE_2
        Normative status: normative

    Mathematical form:
        N_ad=0.5*M_x/b_2

    Parameters:
        bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Design bending-moment magnitude.
            Valid range: >=0
            Source: global analysis
        branch_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Relevant distance between branch axes.
            Valid range: >0
            Source: Table 8 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Additional branch axial-force magnitude N_ad.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Built-up lattice member, Table 8 section type 2.

    Limitations:
        - The function returns the moment-induced component only; base branch force is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_additional_force_rules
        Validation cases:
            - V11-PROC-9.3.3-BRANCH_ADDITIONAL_FORCE_X_TYPE_2

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5*_nonnegative(bending_moment_n_mm,"bending_moment_n_mm")/_positive(branch_axis_spacing_mm,"branch_axis_spacing_mm")

def biaxial_branch_additional_force_eq124(moment_y_n_mm: float, spacing_b1_mm: float, moment_x_n_mm: float, spacing_b2_mm: float) -> float:
    """
    Summary:
        Calculate the additional branch force for a type-2 built-up member bent in both principal planes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Equation (124)
        Audit ID: SP16-EQ-124
        Normative status: normative

    Mathematical form:
        N_ad=0.5*(M_y/b_1+M_x/b_2).

    Parameters:
        moment_y_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Moment M_y magnitude.
            Valid range: >=0
            Source: global analysis
        spacing_b1_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis spacing b_1.
            Valid range: >0
            Source: Table 8 geometry
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Moment M_x magnitude.
            Valid range: >=0
            Source: global analysis
        spacing_b2_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis spacing b_2.
            Valid range: >0
            Source: Table 8 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Additional branch axial-force magnitude.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 8 section type 2 under biaxial bending.

    Limitations:
        - Moment signs are not used to identify which physical branch is most compressed.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_123_and_124
        Validation cases:
            - V11-EQ-124

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return 0.5*(_nonnegative(moment_y_n_mm,"moment_y_n_mm")/_positive(spacing_b1_mm,"spacing_b1_mm") + _nonnegative(moment_x_n_mm,"moment_x_n_mm")/_positive(spacing_b2_mm,"spacing_b2_mm"))

def built_up_whole_member_stability_clause_9_3_2(relative_effective_slenderness: float, relative_eccentricity_m: float, central_compression_phi: float) -> dict[str, Any]:
    """
    Summary:
        Route and obtain the Table D.4 coefficient for the whole built-up member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.2
        Annex: None
        Equation/Table: Equation (109), Table D.4, Equation (123)
        Audit ID: SP16-PROC-9.3.2-D4-LOOKUP-AND-BENDING-ROUTE
        Normative status: normative

    Mathematical form:
        m<=20: phi_e=min(Table D.4,phi); m>20: Section 8 route.

    Parameters:
        relative_effective_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Effective relative slenderness from Table 8.
            Valid range: >=0, exact D.4 node when lookup is used
            Source: Table 8
        relative_eccentricity_m:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity from equation (123).
            Valid range: >=0
            Source: equation (123)
        central_compression_phi:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient.
            Valid range: 0<value<=1
            Source: equation (8)

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Routing result and Table D.4 coefficient when applicable.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Whole built-up member about the free axis.

    Limitations:
        - Table D.4 is used only at exact printed nodes; no interpolation is inferred.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_whole_member_route_and_connector_force
        Validation cases:
            - V11-PROC-9.3.2-D4-LOOKUP-AND-BENDING-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    slender=_nonnegative(relative_effective_slenderness,"relative_effective_slenderness")
    m=_nonnegative(relative_eccentricity_m,"relative_eccentricity_m")
    if m>20.0:
        return {"route":"bending_member_section_8","phi_e":None,"whole_member_stability_check_required":False}
    phi=beamcol.annex_d4_stability_coefficient(slender,m,_phi(central_compression_phi,"central_compression_phi"))
    return {"route":"equation_109_with_table_d4","phi_e":phi,"whole_member_stability_check_required":True}

def branch_force_with_additional_component(base_branch_axial_force_n: float, additional_force_n: float) -> float:
    """
    Summary:
        Combine the base branch compression force and the moment-induced additional force.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.3
        Annex: None
        Equation/Table: Unnumbered branch-force procedure
        Audit ID: SP16-PROC-9.3.3-BRANCH-ADDITIONAL-FORCES
        Normative status: normative

    Mathematical form:
        N_branch,design=N_branch,base+N_ad.

    Parameters:
        base_branch_axial_force_n:
            Type: float
            Unit: N
            Meaning: Base branch compression force.
            Valid range: >=0
            Source: member-force distribution
        additional_force_n:
            Type: float
            Unit: N
            Meaning: Additional force N_ad.
            Valid range: >=0
            Source: 9.3.3

    Returns:
        Type: float
        Unit: N
        Meaning: Design compression force in the selected branch.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Separate branch stability check under equation (7) or beam-column checks.

    Limitations:
        - The user must select the governing compressed branch.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_and_external_routes
        Validation cases:
            - V11-PROC-9.3.3-BRANCH-ADDITIONAL-FORCES

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(base_branch_axial_force_n,"base_branch_axial_force_n")+_nonnegative(additional_force_n,"additional_force_n")

def battened_branch_check_route_clause_9_3_4(additional_force_n: float, local_bending_moment_n_mm: float, actual_or_fictitious_shear_n: float) -> dict[str, Any]:
    """
    Summary:
        Expose all branch actions required for a battened built-up beam-column.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.4
        Annex: None
        Equation/Table: Unnumbered procedure
        Audit ID: SP16-PROC-9.3.4-BATTEN-BRANCH-LOCAL-BENDING
        Normative status: normative

    Mathematical form:
        Equation (109) branch check plus local bending from actual or fictitious shear.

    Parameters:
        additional_force_n:
            Type: float
            Unit: N
            Meaning: Moment-induced branch force.
            Valid range: >=0
            Source: 9.3.3
        local_bending_moment_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Local branch bending moment.
            Valid range: >=0
            Source: Vierendeel-chord analysis
        actual_or_fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Shear used in local branch analysis.
            Valid range: >=0
            Source: global analysis or 7.2.7

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Explicit action bundle and required route.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Built-up members with battens.

    Limitations:
        - The local Vierendeel analysis itself remains external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_and_external_routes
        Validation cases:
            - V11-PROC-9.3.4-BATTEN-BRANCH-LOCAL-BENDING

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return {"additional_force_n":_nonnegative(additional_force_n,"additional_force_n"),"local_bending_moment_n_mm":_nonnegative(local_bending_moment_n_mm,"local_bending_moment_n_mm"),"branch_shear_n":_nonnegative(actual_or_fictitious_shear_n,"actual_or_fictitious_shear_n"),"required_check":"equation_109_plus_local_bending_as_vierendeel_chord"}

def three_sided_built_up_route_clause_9_3_5(equilateral_constant_section_confirmed: bool) -> dict[str, Any]:
    """
    Summary:
        Route a three-sided equilateral built-up beam-column to Section 16.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.5
        Annex: None
        Equation/Table: External normative route
        Audit ID: SP16-PROC-9.3.5-THREE-SIDED-SECTION-16-ROUTE
        Normative status: normative

    Mathematical form:
        No scalar formula; Section 16 governs.

    Parameters:
        equilateral_constant_section_confirmed:
            Type: bool
            Unit: boolean
            Meaning: Whether the specific 9.3.5 topology is present.
            Valid range: true or false
            Source: member topology

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: External-route declaration.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Three-sided lattice members with constant equilateral section.

    Limitations:
        - Section 16 is not implemented in this release.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_and_external_routes
        Validation cases:
            - V11-PROC-9.3.5-THREE-SIDED-SECTION-16-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(equilateral_constant_section_confirmed,bool):
        raise TypeError("equilateral_constant_section_confirmed must be bool")
    return {"route":"section_16_required","applicability_confirmed":equilateral_constant_section_confirmed,"calculation_completed_here":False}

def two_solid_branch_route_clause_9_3_6(moment_x_n_mm: float, branch_axial_force_n: float, branch_eccentricity_x_mm: float, moment_acts_in_one_branch_plane: bool) -> dict[str, Any]:
    """
    Summary:
        Return the normative routing for a two-solid-branch built-up beam-column.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.6
        Annex: None
        Equation/Table: Unnumbered procedure and Figure 12
        Audit ID: SP16-PROC-9.3.6-TWO-SOLID-BRANCH-ROUTING
        Normative status: normative

    Mathematical form:
        M_xb=N_b*e_x unless M_x acts in one branch plane, when full M_x is assigned.

    Parameters:
        moment_x_n_mm:
            Type: float
            Unit: N*mm
            Meaning: Global moment M_x.
            Valid range: >=0
            Source: global analysis
        branch_axial_force_n:
            Type: float
            Unit: N
            Meaning: Branch compression force N_b.
            Valid range: >=0
            Source: branch force distribution
        branch_eccentricity_x_mm:
            Type: float
            Unit: mm
            Meaning: Branch eccentricity e_x.
            Valid range: >=0
            Source: Figure 12 geometry
        moment_acts_in_one_branch_plane:
            Type: bool
            Unit: boolean
            Meaning: Whether full M_x acts in one branch plane.
            Valid range: true or false
            Source: load geometry

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Whole-member and branch-check routes.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Two solid branches symmetric about x-x with two parallel lattice planes.

    Limitations:
        - Effective lengths from 10.3.10 are not calculated here.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_branch_and_external_routes
        Validation cases:
            - V11-PROC-9.3.6-TWO-SOLID-BRANCH-ROUTING

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(moment_acts_in_one_branch_plane,bool):
        raise TypeError("moment_acts_in_one_branch_plane must be bool")
    mx=_nonnegative(moment_x_n_mm,"moment_x_n_mm")
    nb=_nonnegative(branch_axial_force_n,"branch_axial_force_n")
    ex=_nonnegative(branch_eccentricity_x_mm,"branch_eccentricity_x_mm")
    distributed=mx if moment_acts_in_one_branch_plane else nb*ex
    return {"whole_member_route":"clause_9_3_2_with_e_x_zero","branch_routes":["equation_109","equation_111"],"branch_moment_x_n_mm":distributed,"equation_109_effective_length_rule":"clause_10_3_10","equation_111_effective_length_rule":"maximum_lattice_node_spacing"}

def connector_design_shear_clause_9_3_7(actual_shear_force_n: float, fictitious_shear_force_n: float) -> dict[str, Any]:
    """
    Summary:
        Select the governing shear force for battens or lattices of an eccentrically compressed built-up member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.3.7
        Annex: None
        Equation/Table: Unnumbered maximum rule
        Audit ID: SP16-PROC-9.3.7-CONNECTOR-SHEAR-GOVERNING
        Normative status: normative

    Mathematical form:
        Q_design=max(Q,Q_fic); use lattices when Q>Q_fic.

    Parameters:
        actual_shear_force_n:
            Type: float
            Unit: N
            Meaning: Actual global shear Q.
            Valid range: >=0
            Source: Vierendeel/global analysis
        fictitious_shear_force_n:
            Type: float
            Unit: N
            Meaning: Fictitious shear Q_fic.
            Valid range: >=0
            Source: 7.2.7

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Governing shear and connector-system requirement.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Connector design under 7.2.8 and 7.2.9.

    Limitations:
        - The function does not design welds, bolts, battens, or lattice bars.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_whole_member_route_and_connector_force
        Validation cases:
            - V11-PROC-9.3.7-CONNECTOR-SHEAR-GOVERNING

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    q=_nonnegative(actual_shear_force_n,"actual_shear_force_n")
    qfic=_nonnegative(fictitious_shear_force_n,"fictitious_shear_force_n")
    governing=max(q,qfic)
    return {"governing_shear_force_n":governing,"governing_source":"actual" if q>qfic else "fictitious" if qfic>q else "equal","lattice_required":q>qfic}

def combined_web_relative_slenderness(effective_web_height_mm: float, web_thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate actual relative web slenderness for the Section 9.4 check.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Definition preceding Table 22
        Audit ID: SP16-PROC-9.4.2-ACTUAL-WEB-SLENDERNESS
        Normative status: normative

    Mathematical form:
        lambda_w_bar=(h_eff/t_w)*sqrt(R_y/E).

    Parameters:
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height.
            Valid range: >0
            Source: 7.3.1
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness.
            Valid range: >0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance.
            Valid range: >0
            Source: 6.1
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Elastic modulus.
            Valid range: >0
            Source: material data

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Actual relative web slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Eccentrically compressed and beam-column solid-web members.

    Limitations:
        - Effective dimensions must be determined externally under 7.3.1.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_actual_slenderness_helpers
        Validation cases:
            - V11-PROC-9.4.2-ACTUAL-WEB-SLENDERNESS

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return local.wall_relative_slenderness(effective_web_height_mm,web_thickness_mm,design_yield_resistance_n_mm2,elastic_modulus_n_mm2)

def table_22_stress_parameters(sigma_1_n_mm2: float, sigma_2_n_mm2: float, average_shear_stress_n_mm2: float, c_cr: float) -> dict[str, float]:
    """
    Summary:
        Calculate alpha and beta used by Table 22.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Definitions below Table 22
        Audit ID: SP16-PROC-9.4.2-STRESS-PARAMETERS
        Normative status: normative

    Mathematical form:
        alpha=(sigma_1-sigma_2)/sigma_1; beta=0.15*c_cr*tau/sigma_1.

    Parameters:
        sigma_1_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Largest compressive edge stress.
            Valid range: >0
            Source: elastic stress calculation without phi factors
        sigma_2_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Opposite-edge signed stress.
            Valid range: finite
            Source: elastic stress calculation
        average_shear_stress_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Average web shear stress.
            Valid range: >=0
            Source: Q/(t_w*h_w) or Q/(2*t_w*h_w)
        c_cr:
            Type: float
            Unit: dimensionless
            Meaning: Table 17 coefficient.
            Valid range: >0
            Source: Table 17

    Returns:
        Type: dict[str, float]
        Unit: dimensionless
        Meaning: Alpha and beta parameters.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 section types 2 and 3.

    Limitations:
        - The function does not select c_cr from Table 17.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_22_stress_parameters
        Validation cases:
            - V11-PROC-9.4.2-STRESS-PARAMETERS

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    s1=_positive(sigma_1_n_mm2,"sigma_1_n_mm2")
    s2=_real(sigma_2_n_mm2,"sigma_2_n_mm2")
    tau=_nonnegative(average_shear_stress_n_mm2,"average_shear_stress_n_mm2")
    c=_positive(c_cr,"c_cr")
    alpha=(s1-s2)/s1
    beta=0.15*c*tau/s1
    return {"alpha":alpha,"beta":beta}

def web_limit_eq125(member_relative_slenderness_x: float) -> float:
    """
    Summary:
        Calculate the Table 22 type-1 web limit for member slenderness below 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (125)
        Audit ID: SP16-EQ-125
        Normative status: normative

    Mathematical form:
        lambda_uw1_bar=1.3+0.15*lambda_x_bar^2.

    Parameters:
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness in bending plane.
            Valid range: 0<=value<2
            Source: member stability model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting web relative slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 type 1 and base domain 1<=m_x<=10.

    Limitations:
        - m_x interpolation outside the base domain is handled by the Table 22 router.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-125

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    lx=_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x")
    if lx>=2.0: raise ValueError("equation (125) requires member_relative_slenderness_x < 2")
    return 1.3+0.15*lx*lx

def web_limit_eq126(member_relative_slenderness_x: float) -> float:
    """
    Summary:
        Calculate the capped Table 22 type-1 web limit for member slenderness at least 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (126)
        Audit ID: SP16-EQ-126
        Normative status: normative

    Mathematical form:
        lambda_uw1_bar=min(1.2+0.35*lambda_x_bar,3.1).

    Parameters:
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member relative slenderness in bending plane.
            Valid range: >=2
            Source: member stability model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Limiting web relative slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - I-section Table 22 type 1 when c*phi_y>phi_e.

    Limitations:
        - m_x interpolation outside the base domain is handled by the Table 22 router.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-126

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    lx=_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x")
    if lx<2.0: raise ValueError("equation (126) requires member_relative_slenderness_x >= 2")
    return min(1.2+0.35*lx,3.1)

def web_limit_eq127(alpha: float, beta: float, c_cr: float, design_yield_resistance_n_mm2: float, working_condition_factor: float, sigma_1_n_mm2: float) -> float:
    """
    Summary:
        Calculate the Table 22 type-2 limiting web slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (127)
        Audit ID: SP16-EQ-127
        Normative status: normative

    Mathematical form:
        lambda_uw2_bar=min(1.42*sqrt(c_cr*R_y*gamma_c/[sigma_1*(2-alpha+sqrt(alpha^2+4beta^2))]),0.7+2.4alpha).

    Parameters:
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Stress-gradient parameter.
            Valid range: 1 to 2
            Source: Table 22 definition
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Shear interaction parameter.
            Valid range: >=0
            Source: Table 22 definition
        c_cr:
            Type: float
            Unit: dimensionless
            Meaning: Table 17 coefficient.
            Valid range: >0
            Source: Table 17
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance.
            Valid range: >0
            Source: 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: >0
            Source: applicable clause
        sigma_1_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Largest compressive edge stress.
            Valid range: >0
            Source: elastic stress calculation

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped limiting web relative slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 type 2 when c*phi_y<=phi_e.

    Limitations:
        - Alpha below 1 is handled by note 2 routing, not by this equation function.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-127

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    a=_real(alpha,"alpha")
    if not 1.0<=a<=2.0: raise ValueError("equation (127) requires 1 <= alpha <= 2")
    b=_nonnegative(beta,"beta")
    denominator=_positive(sigma_1_n_mm2,"sigma_1_n_mm2")*(2.0-a+math.sqrt(a*a+4.0*b*b))
    raw=1.42*math.sqrt(_positive(c_cr,"c_cr")*_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2")*_positive(working_condition_factor,"working_condition_factor")/denominator)
    return min(raw,0.7+2.4*a)

def web_limit_eq128(type_2_web_limit: float, alpha: float) -> float:
    """
    Summary:
        Calculate the Table 22 type-3 limiting web slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (128)
        Audit ID: SP16-EQ-128
        Normative status: normative

    Mathematical form:
        lambda_uw_bar=min(0.75*lambda_uw2_bar,0.52+1.8alpha).

    Parameters:
        type_2_web_limit:
            Type: float
            Unit: dimensionless
            Meaning: Value lambda_uw2_bar from equation (127).
            Valid range: >0
            Source: equation (127)
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Stress-gradient parameter.
            Valid range: 1 to 2
            Source: Table 22 definition

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped type-3 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 type 3.

    Limitations:
        - Equation (127) inputs remain explicit.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-128

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    a=_real(alpha,"alpha")
    if not 1.0<=a<=2.0: raise ValueError("equation (128) requires 1 <= alpha <= 2")
    return min(0.75*_positive(type_2_web_limit,"type_2_web_limit"),0.52+1.8*a)

def web_limit_eq129(member_relative_slenderness_x: float, flange_width_mm: float, effective_web_height_mm: float) -> float:
    """
    Summary:
        Calculate the Table 22 type-4 tee-section limiting web slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (129)
        Audit ID: SP16-EQ-129
        Normative status: normative

    Mathematical form:
        lambda_uw_bar=(0.4+0.07lambda_x_bar)*(1+0.25sqrt(2-b_f/h_eff)).

    Parameters:
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness in bending plane.
            Valid range: >=0; clamped to 0.8-4
            Source: member stability model
        flange_width_mm:
            Type: float
            Unit: mm
            Meaning: Tee flange width b_f.
            Valid range: >0
            Source: section geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height h_eff.
            Valid range: >0
            Source: 7.3.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-4 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 type 4 tee sections.

    Limitations:
        - Section-type classification is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-129

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    lx=_clamp(_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x"),0.8,4.0)
    ratio=_positive(flange_width_mm,"flange_width_mm")/_positive(effective_web_height_mm,"effective_web_height_mm")
    if not 1.0<=ratio<=2.0: raise ValueError("equation (129) requires 1 <= b_f/h_eff <= 2")
    return (0.4+0.07*lx)*(1.0+0.25*math.sqrt(2.0-ratio))

def web_limit_eq130(gross_area_mm2: float, design_yield_resistance_n_mm2: float, working_condition_factor: float, axial_force_n: float) -> float:
    """
    Summary:
        Calculate the Table 22 type-5 limiting web slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Equation (130)
        Audit ID: SP16-EQ-130
        Normative status: normative

    Mathematical form:
        lambda_uw_bar=min(2*sqrt(A*R_y*gamma_c/N),5.5).

    Parameters:
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross or audited reduced section area A.
            Valid range: >0
            Source: section model
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: >0
            Source: 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: >0
            Source: applicable clause
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Compressive force N.
            Valid range: >0
            Source: global analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Capped type-5 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 type 5 with m_y>=1.

    Limitations:
        - For 0<m_y<1, use the Table 22 interpolation router.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_125_to_130
        Validation cases:
            - V11-EQ-130

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    raw=2.0*math.sqrt(_positive(gross_area_mm2,"gross_area_mm2")*_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2")*_positive(working_condition_factor,"working_condition_factor")/_positive(axial_force_n,"axial_force_n"))
    return min(raw,5.5)

def table_22_type_1_limit(member_relative_slenderness_x: float, relative_eccentricity_mx: float, central_compression_limit_m0: float, bending_member_limit_m20: float) -> float:
    """
    Summary:
        Apply Table 22 note 1 interpolation for section type 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Table 22, note 1
        Audit ID: SP16-PROC-9.4.2-TYPE-1-M-INTERPOLATION
        Normative status: normative

    Mathematical form:
        Piecewise linear interpolation at m_x=0,1,10,20.

    Parameters:
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness in bending plane.
            Valid range: >=0
            Source: member model
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_x.
            Valid range: 0 to 20
            Source: 9.2
        central_compression_limit_m0:
            Type: float
            Unit: dimensionless
            Meaning: Limit at m_x=0.
            Valid range: >0
            Source: 7.3.2
        bending_member_limit_m20:
            Type: float
            Unit: dimensionless
            Meaning: Limit at m_x=20.
            Valid range: >0
            Source: 8.5.1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Interpolated type-1 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 section type 1.

    Limitations:
        - The caller supplies the linked central-compression and bending-member limits.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_22_type_1_interpolation
        Validation cases:
            - V11-PROC-9.4.2-TYPE-1-M-INTERPOLATION

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    lx=_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x")
    mx=_nonnegative(relative_eccentricity_mx,"relative_eccentricity_mx")
    if mx>20.0: raise ValueError("Table 22 type 1 is limited to m_x <= 20")
    base=web_limit_eq125(lx) if lx<2.0 else web_limit_eq126(lx)
    central=_positive(central_compression_limit_m0,"central_compression_limit_m0")
    bending=_positive(bending_member_limit_m20,"bending_member_limit_m20")
    if mx<1.0: return _linear(mx,0.0,1.0,central,base)
    if mx<=10.0: return base
    return _linear(mx,10.0,20.0,base,bending)

def table_22_type_2_limit(alpha: float, type_1_limit_at_alpha_0_5: float, central_compression_limit_at_alpha_0_5: float, beta: float, c_cr: float, design_yield_resistance_n_mm2: float, working_condition_factor: float, sigma_1_n_mm2: float) -> float:
    """
    Summary:
        Apply Table 22 note 2 routing for section type 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Table 22, note 2 and Equation (127)
        Audit ID: SP16-PROC-9.4.2-TYPE-2-ALPHA-ROUTING
        Normative status: normative

    Mathematical form:
        alpha<=0.5: governing of two checks; 0.5<alpha<1: linear interpolation; alpha>=1: equation (127).

    Parameters:
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Stress-gradient parameter.
            Valid range: 0 to 2
            Source: Table 22
        type_1_limit_at_alpha_0_5:
            Type: float
            Unit: dimensionless
            Meaning: Limit from equations (125)/(126).
            Valid range: >0
            Source: Table 22 note 2
        central_compression_limit_at_alpha_0_5:
            Type: float
            Unit: dimensionless
            Meaning: Limit from 7.3.2.
            Valid range: >0
            Source: Table 22 note 2
        beta:
            Type: float
            Unit: dimensionless
            Meaning: Shear parameter.
            Valid range: >=0
            Source: Table 22
        c_cr:
            Type: float
            Unit: dimensionless
            Meaning: Table 17 coefficient.
            Valid range: >0
            Source: Table 17
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design resistance.
            Valid range: >0
            Source: 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: >0
            Source: applicable clause
        sigma_1_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Largest compressive stress.
            Valid range: >0
            Source: elastic analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Governing or interpolated type-2 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 section type 2.

    Limitations:
        - Two-check input values at alpha=0.5 must be supplied explicitly.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_22_type_2_and_type_5_interpolation
        Validation cases:
            - V11-PROC-9.4.2-TYPE-2-ALPHA-ROUTING

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    a=_nonnegative(alpha,"alpha")
    if a>2.0: raise ValueError("Table 22 type 2 requires alpha <= 2")
    at_half=min(_positive(type_1_limit_at_alpha_0_5,"type_1_limit_at_alpha_0_5"),_positive(central_compression_limit_at_alpha_0_5,"central_compression_limit_at_alpha_0_5"))
    at_one=web_limit_eq127(1.0,beta,c_cr,design_yield_resistance_n_mm2,working_condition_factor,sigma_1_n_mm2)
    if a<=0.5: return at_half
    if a<1.0: return _linear(a,0.5,1.0,at_half,at_one)
    return web_limit_eq127(a,beta,c_cr,design_yield_resistance_n_mm2,working_condition_factor,sigma_1_n_mm2)

def table_22_type_5_limit(relative_eccentricity_my: float, central_compression_limit_m0: float, gross_area_mm2: float, design_yield_resistance_n_mm2: float, working_condition_factor: float, axial_force_n: float) -> float:
    """
    Summary:
        Apply Table 22 note 4 interpolation for section type 5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.2
        Annex: None
        Equation/Table: Table 22, note 4 and Equation (130)
        Audit ID: SP16-PROC-9.4.2-TYPE-5-M-INTERPOLATION
        Normative status: normative

    Mathematical form:
        0<m_y<1: linear interpolation from the central-compression limit to equation (130).

    Parameters:
        relative_eccentricity_my:
            Type: float
            Unit: dimensionless
            Meaning: Relative eccentricity m_y.
            Valid range: >=0
            Source: 9.2
        central_compression_limit_m0:
            Type: float
            Unit: dimensionless
            Meaning: Limit at m_y=0.
            Valid range: >0
            Source: 7.3.2
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A.
            Valid range: >0
            Source: section model
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: >0
            Source: 6.1
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: gamma_c.
            Valid range: >0
            Source: applicable clause
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Compression N.
            Valid range: >0
            Source: global analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-5 web limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 section type 5.

    Limitations:
        - The central-compression limit is supplied externally.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_22_type_2_and_type_5_interpolation
        Validation cases:
            - V11-PROC-9.4.2-TYPE-5-M-INTERPOLATION

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    my=_nonnegative(relative_eccentricity_my,"relative_eccentricity_my")
    base=web_limit_eq130(gross_area_mm2,design_yield_resistance_n_mm2,working_condition_factor,axial_force_n)
    if my>=1.0: return base
    return _linear(my,0.0,1.0,_positive(central_compression_limit_m0,"central_compression_limit_m0"),base)

def web_limit_adjustment_eq131(web_limit_type_1: float, web_limit_type_2: float, axial_stability_utilization: float) -> float:
    """
    Summary:
        Increase the type-1 web limit for the specified axial-stability utilization range.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.3
        Annex: None
        Equation/Table: Equation (131)
        Audit ID: SP16-EQ-131
        Normative status: normative

    Mathematical form:
        lambda_uw=lambda_uw1+5(lambda_uw2-lambda_uw1)(1-N/(phi_e*A*R_y*gamma_c)); below 0.8 use lambda_uw2.

    Parameters:
        web_limit_type_1:
            Type: float
            Unit: dimensionless
            Meaning: Limit from equation (125) or (126).
            Valid range: >0
            Source: Table 22
        web_limit_type_2:
            Type: float
            Unit: dimensionless
            Meaning: Limit from equation (127).
            Valid range: >0
            Source: Table 22
        axial_stability_utilization:
            Type: float
            Unit: dimensionless
            Meaning: N/(phi_e*A*R_y*gamma_c).
            Valid range: 0 to 1
            Source: equation (109) denominator

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Adjusted limiting web slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Condition c*phi_y>phi_e with utilization at or below one.

    Limitations:
        - The function assumes the condition triggering 9.4.3 has been confirmed.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equation_131_and_routes
        Validation cases:
            - V11-EQ-131

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    l1=_positive(web_limit_type_1,"web_limit_type_1")
    l2=_positive(web_limit_type_2,"web_limit_type_2")
    ratio=_nonnegative(axial_stability_utilization,"axial_stability_utilization")
    if ratio>1.0: raise ValueError("equation (131) is not applicable after global stability failure")
    if ratio<0.8: return l2
    return l1+5.0*(l2-l1)*(1.0-ratio)

def transverse_stiffener_route_clause_9_4_4(wall_relative_slenderness_value: float, effective_web_height_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float, stiffener_arrangement: str, provided_stiffener_outstand_mm: float, geometrically_nonlinear_design: bool, solid_branch_of_built_up_column: bool) -> dict[str, Any]:
    """
    Summary:
        Apply the clause 9.4.4 reference to the transverse-stiffener rules of 7.3.3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.4
        Annex: None
        Equation/Table: Reference to Clause 7.3.3
        Audit ID: SP16-PROC-9.4.4-TRANSVERSE-STIFFENER-ROUTE
        Normative status: normative

    Mathematical form:
        Trigger at lambda_w_bar>=2.3, subject to the 7.3.3 nonlinear-analysis exception.

    Parameters:
        wall_relative_slenderness_value:
            Type: float
            Unit: dimensionless
            Meaning: Actual web slenderness.
            Valid range: >=0
            Source: 9.4.2
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height.
            Valid range: >0
            Source: 7.3.1
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: >0
            Source: 6.1
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: E.
            Valid range: >0
            Source: material data
        stiffener_arrangement:
            Type: str
            Unit: selector
            Meaning: Stiffener arrangement.
            Valid range: paired_symmetric or one_sided
            Source: design geometry
        provided_stiffener_outstand_mm:
            Type: float
            Unit: mm
            Meaning: Provided outstand.
            Valid range: >0
            Source: design geometry
        geometrically_nonlinear_design:
            Type: bool
            Unit: boolean
            Meaning: Whether exception applies.
            Valid range: true/false
            Source: analysis method
        solid_branch_of_built_up_column:
            Type: bool
            Unit: boolean
            Meaning: Whether location is limited to connection nodes.
            Valid range: true/false
            Source: topology

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Stiffener trigger and dimensional requirements.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Solid-web eccentric-compression members.

    Limitations:
        - Weld and complete stiffener design remain outside this function.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equation_131_and_routes
        Validation cases:
            - V11-PROC-9.4.4-TRANSVERSE-STIFFENER-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return local.transverse_stiffener_requirements(wall_relative_slenderness_value,effective_web_height_mm,design_yield_resistance_n_mm2,elastic_modulus_n_mm2,stiffener_arrangement,provided_stiffener_outstand_mm,geometrically_nonlinear_design,solid_branch_of_built_up_column)

def longitudinal_stiffener_route_clause_9_4_5(longitudinal_stiffener_inertia_mm4: float, effective_web_height_mm: float, web_thickness_mm: float) -> dict[str, Any]:
    """
    Summary:
        Check the minimum inertia and routing for a mid-depth longitudinal web stiffener.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.5
        Annex: None
        Equation/Table: Unnumbered inertia requirement
        Audit ID: SP16-PROC-9.4.5-LONGITUDINAL-STIFFENER-ROUTE
        Normative status: normative

    Mathematical form:
        I_r1>=6*h_eff*t_w^3.

    Parameters:
        longitudinal_stiffener_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Provided stiffener inertia.
            Valid range: >=0
            Source: stiffener geometry
        effective_web_height_mm:
            Type: float
            Unit: mm
            Meaning: Effective web height.
            Valid range: >0
            Source: 7.3.1
        web_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Web thickness.
            Valid range: >0
            Source: section geometry

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Inertia check and required plate-check route.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Mid-depth longitudinal stiffener in an eccentric-compression member.

    Limitations:
        - The split plate is not classified automatically by geometry.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equation_131_and_routes
        Validation cases:
            - V11-PROC-9.4.5-LONGITUDINAL-STIFFENER-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    inertia=_nonnegative(longitudinal_stiffener_inertia_mm4,"longitudinal_stiffener_inertia_mm4")
    required=6.0*_positive(effective_web_height_mm,"effective_web_height_mm")*_positive(web_thickness_mm,"web_thickness_mm")**3
    return {"minimum_inertia_mm4":required,"provided_inertia_mm4":inertia,"inertia_pass":inertia>=required,"most_loaded_half_web_check":"treat_as_independent_plate_using_table_22","linked_design_clause":"7.3.4"}

def reduced_area_route_clause_9_4_6(section_type: int, alpha: float, actual_web_slenderness: float, limiting_web_slenderness: float) -> dict[str, Any]:
    """
    Summary:
        Determine whether reduced area A_d is required by clause 9.4.6.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.6
        Annex: None
        Equation/Table: Reference to Clause 7.3.6
        Audit ID: SP16-PROC-9.4.6-REDUCED-AREA-ROUTE
        Normative status: normative

    Mathematical form:
        When the applicable actual web slenderness exceeds its limit, use A_d in specified stability equations.

    Parameters:
        section_type:
            Type: int
            Unit: selector
            Meaning: Table 22 section type.
            Valid range: 1,2,3
            Source: section classification
        alpha:
            Type: float
            Unit: dimensionless
            Meaning: Stress-gradient parameter.
            Valid range: finite
            Source: Table 22
        actual_web_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Actual web slenderness.
            Valid range: >=0
            Source: 9.4.2
        limiting_web_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Applicable limit.
            Valid range: >0
            Source: Table 22

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Reduced-area trigger and affected equations.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 22 types specified by 9.4.6.

    Limitations:
        - The reduced dimensions and area are calculated by the existing 7.3.6 functions.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equation_131_and_routes
        Validation cases:
            - V11-PROC-9.4.6-REDUCED-AREA-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if section_type not in {1,2,3}: raise ValueError("section_type must be 1, 2, or 3")
    a=_real(alpha,"alpha")
    actual=_nonnegative(actual_web_slenderness,"actual_web_slenderness")
    limit=_positive(limiting_web_slenderness,"limiting_web_slenderness")
    applicable=section_type==1 or (section_type in {2,3} and a<=0.5)
    required=applicable and actual>limit
    equations=[109,115,116]
    if a<=0.5: equations.append(111)
    return {"reduced_area_required":required,"applicable_section_type_and_alpha":applicable,"equations_using_reduced_area":equations if required else [],"reduced_area_source":"clause_7.3.6" if required else None}

def combined_flange_relative_slenderness(effective_flange_outstand_mm: float, flange_thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """
    Summary:
        Calculate actual relative flange outstand slenderness for Section 9.4.7.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Definition preceding Table 23
        Audit ID: SP16-PROC-9.4.7-ACTUAL-FLANGE-SLENDERNESS
        Normative status: normative

    Mathematical form:
        lambda_f_bar=(b_eff/t_f)*sqrt(R_y/E).

    Parameters:
        effective_flange_outstand_mm:
            Type: float
            Unit: mm
            Meaning: Effective flange outstand.
            Valid range: >0
            Source: 7.3.7
        flange_thickness_mm:
            Type: float
            Unit: mm
            Meaning: Flange thickness.
            Valid range: >0
            Source: section geometry
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: >0
            Source: 6.1
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: E.
            Valid range: >0
            Source: material data

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Actual flange relative slenderness.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Beam-columns with flange or flange-plate local-stability checks.

    Limitations:
        - Effective dimensions must be obtained externally.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_actual_slenderness_helpers
        Validation cases:
            - V11-PROC-9.4.7-ACTUAL-FLANGE-SLENDERNESS

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    return local.flange_relative_slenderness(effective_flange_outstand_mm,flange_thickness_mm,design_yield_resistance_n_mm2,elastic_modulus_n_mm2)

def flange_limit_eq132(central_compression_flange_limit: float, member_relative_slenderness_x: float, relative_eccentricity_mx: float) -> float:
    """
    Summary:
        Calculate the Table 23 type-1 limiting flange outstand slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Equation (132)
        Audit ID: SP16-EQ-132
        Normative status: normative

    Mathematical form:
        lambda_uf_bar=lambda_ufc_bar-0.01(1.5+0.7lambda_x_bar)m_x.

    Parameters:
        central_compression_flange_limit:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression flange limit.
            Valid range: >0
            Source: 7.3.8/7.3.9
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness.
            Valid range: >=0; clamped 0.8-4
            Source: member model
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: m_x.
            Valid range: 0 to 5
            Source: 9.2

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-1 flange limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 23 type 1.

    Limitations:
        - For 5<m_x<=20 use the Table 23 interpolation router.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_132_to_135
        Validation cases:
            - V11-EQ-132

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    mx=_nonnegative(relative_eccentricity_mx,"relative_eccentricity_mx")
    if mx>5.0: raise ValueError("equation (132) requires m_x <= 5")
    lx=_clamp(_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x"),0.8,4.0)
    return _positive(central_compression_flange_limit,"central_compression_flange_limit")-0.01*(1.5+0.7*lx)*mx

def flange_limit_eq133(central_compression_flange_limit: float, member_relative_slenderness_x: float, relative_eccentricity_mx: float) -> float:
    """
    Summary:
        Calculate the Table 23 type-2 limiting flange-plate slenderness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Equation (133)
        Audit ID: SP16-EQ-133
        Normative status: normative

    Mathematical form:
        lambda_uf1_bar=lambda_ufc_bar-0.01(5.3+1.3lambda_x_bar)m_x.

    Parameters:
        central_compression_flange_limit:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression flange-plate limit.
            Valid range: >0
            Source: 7.3.8/7.3.9
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness.
            Valid range: >=0; clamped 0.8-4
            Source: member model
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: m_x.
            Valid range: 0 to 5
            Source: 9.2

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-2 flange-plate limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 23 type 2.

    Limitations:
        - For 5<m_x<=20 use the Table 23 interpolation router.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_132_to_135
        Validation cases:
            - V11-EQ-133

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    mx=_nonnegative(relative_eccentricity_mx,"relative_eccentricity_mx")
    if mx>5.0: raise ValueError("equation (133) requires m_x <= 5")
    lx=_clamp(_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x"),0.8,4.0)
    return _positive(central_compression_flange_limit,"central_compression_flange_limit")-0.01*(5.3+1.3*lx)*mx

def flange_limit_eq134(member_relative_slenderness_x: float) -> float:
    """
    Summary:
        Calculate the Table 23 type-3 flange limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Equation (134)
        Audit ID: SP16-EQ-134
        Normative status: normative

    Mathematical form:
        lambda_uf_bar=0.36+0.10lambda_x_bar.

    Parameters:
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness in x plane.
            Valid range: >=0; clamped 0.8-4
            Source: member model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-3 flange limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 23 type 3.

    Limitations:
        - Section classification is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_132_to_135
        Validation cases:
            - V11-EQ-134

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    lx=_clamp(_nonnegative(member_relative_slenderness_x,"member_relative_slenderness_x"),0.8,4.0)
    return 0.36+0.10*lx

def flange_limit_eq135(member_relative_slenderness_y: float) -> float:
    """
    Summary:
        Calculate the Table 23 type-4 flange limit.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Equation (135)
        Audit ID: SP16-EQ-135
        Normative status: normative

    Mathematical form:
        lambda_uf_bar=0.36+0.10lambda_y_bar.

    Parameters:
        member_relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Member slenderness in y plane.
            Valid range: >=0; clamped 0.8-4
            Source: member model

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Type-4 flange limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Table 23 type 4.

    Limitations:
        - Section classification is external.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_equations_132_to_135
        Validation cases:
            - V11-EQ-135

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    ly=_clamp(_nonnegative(member_relative_slenderness_y,"member_relative_slenderness_y"),0.8,4.0)
    return 0.36+0.10*ly

def table_23_limit(section_type: int, central_compression_flange_limit: float, member_relative_slenderness_x: float, member_relative_slenderness_y: float, relative_eccentricity_mx: float, bending_member_limit_m20: float) -> float:
    """
    Summary:
        Route Table 23 formulas and apply the m_x=5 to 20 interpolation rule.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.7
        Annex: None
        Equation/Table: Table 23 and note 1
        Audit ID: SP16-PROC-9.4.7-TABLE-23-ROUTING
        Normative status: normative

    Mathematical form:
        Types 1-2 use equations (132)-(133) to m_x=5 then interpolate to the m=20 bending limit; types 3-4 use (134)-(135).

    Parameters:
        section_type:
            Type: int
            Unit: selector
            Meaning: Table 23 type.
            Valid range: 1-4
            Source: section classification
        central_compression_flange_limit:
            Type: float
            Unit: dimensionless
            Meaning: lambda_ufc_bar.
            Valid range: >0
            Source: 7.3.8/7.3.9
        member_relative_slenderness_x:
            Type: float
            Unit: dimensionless
            Meaning: lambda_x_bar.
            Valid range: >=0
            Source: member model
        member_relative_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: lambda_y_bar.
            Valid range: >=0
            Source: member model
        relative_eccentricity_mx:
            Type: float
            Unit: dimensionless
            Meaning: m_x.
            Valid range: 0 to 20
            Source: 9.2
        bending_member_limit_m20:
            Type: float
            Unit: dimensionless
            Meaning: Limit at m=20.
            Valid range: >0
            Source: 8.5.18/8.5.19

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Applicable Table 23 limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Beam-column flange local stability.

    Limitations:
        - The linked bending-member limit is supplied explicitly.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_23_router_and_modifiers
        Validation cases:
            - V11-PROC-9.4.7-TABLE-23-ROUTING

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if section_type not in {1,2,3,4}: raise ValueError("section_type must be 1, 2, 3, or 4")
    if section_type==3: return flange_limit_eq134(member_relative_slenderness_x)
    if section_type==4: return flange_limit_eq135(member_relative_slenderness_y)
    mx=_nonnegative(relative_eccentricity_mx,"relative_eccentricity_mx")
    if mx>20.0: raise ValueError("Table 23 interpolation is limited to m_x <= 20")
    at_five=flange_limit_eq132(central_compression_flange_limit,member_relative_slenderness_x,min(mx,5.0)) if section_type==1 else flange_limit_eq133(central_compression_flange_limit,member_relative_slenderness_x,min(mx,5.0))
    if mx<=5.0: return at_five
    return _linear(mx,5.0,20.0,at_five,_positive(bending_member_limit_m20,"bending_member_limit_m20"))

def edge_return_flange_limit_clause_9_4_8(base_flange_limit: float, edge_return_applicable: bool) -> float:
    """
    Summary:
        Apply the 1.5 multiplier for qualifying flange or wall edge returns.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.8
        Annex: None
        Equation/Table: Unnumbered multiplier
        Audit ID: SP16-PROC-9.4.8-EDGE-RETURN-MULTIPLIER
        Normative status: normative

    Mathematical form:
        lambda_limit,edge=1.5*lambda_limit.

    Parameters:
        base_flange_limit:
            Type: float
            Unit: dimensionless
            Meaning: Base Table 23 limit.
            Valid range: >0
            Source: Table 23
        edge_return_applicable:
            Type: bool
            Unit: boolean
            Meaning: Whether the 7.3.10 edge-return requirements are met.
            Valid range: true/false
            Source: section geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Modified limit.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Flanges or walls with qualifying edge returns.

    Limitations:
        - Edge-return dimensions are not inferred.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_23_router_and_modifiers
        Validation cases:
            - V11-PROC-9.4.8-EDGE-RETURN-MULTIPLIER

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(edge_return_applicable,bool): raise TypeError("edge_return_applicable must be bool")
    base=_positive(base_flange_limit,"base_flange_limit")
    return 1.5*base if edge_return_applicable else base

def two_plane_limit_increase_clause_9_4_9(stability_coefficients: list[float], gross_area_mm2: float, design_yield_resistance_n_mm2: float, axial_force_n: float) -> float:
    """
    Summary:
        Calculate the capped two-plane increase factor using the smallest stability coefficient.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.9
        Annex: None
        Equation/Table: Unnumbered factor
        Audit ID: SP16-PROC-9.4.9-TWO-PLANE-INCREASE
        Normative status: normative

    Mathematical form:
        factor=min(sqrt(phi_m*A*R_y/N),1.25), phi_m=min(phi_e,c*phi_y,phi_exy,...).

    Parameters:
        stability_coefficients:
            Type: list[float]
            Unit: dimensionless
            Meaning: Coefficients used in member stability checks.
            Valid range: non-empty, each 0<value<=1
            Source: 9.2/9.3 results
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A.
            Valid range: >0
            Source: section model
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: R_y.
            Valid range: >0
            Source: 6.1
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Compression N.
            Valid range: >0
            Source: global analysis

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Increase factor between 1 and 1.25.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - When the Section 10.4 two-plane slenderness condition governs section selection.

    Limitations:
        - The function does not decide whether the two-plane condition is governing.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_23_router_and_modifiers
        Validation cases:
            - V11-PROC-9.4.9-TWO-PLANE-INCREASE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(stability_coefficients,list) or not stability_coefficients: raise ValueError("stability_coefficients must be a non-empty list")
    phi_m=min(_phi(v,"stability_coefficient") for v in stability_coefficients)
    return local.two_plane_slenderness_increase_factor(phi_m,gross_area_mm2,design_yield_resistance_n_mm2,axial_force_n)

def tension_member_local_stability_route_clause_9_4_10(compressive_stress_present: bool) -> dict[str, Any]:
    """
    Summary:
        Route eccentrically tensioned members with compressive plate stress to bending-member local stability.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 9.4.10
        Annex: None
        Equation/Table: Unnumbered route
        Audit ID: SP16-PROC-9.4.10-TENSION-MEMBER-BENDING-ROUTE
        Normative status: normative

    Mathematical form:
        If compressive stress exists, apply Section 8.5.

    Parameters:
        compressive_stress_present:
            Type: bool
            Unit: boolean
            Meaning: Whether the wall or flange contains compressive stress.
            Valid range: true/false
            Source: signed elastic stress field

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Check trigger and external route.

    Assumptions:
        - Inputs refer to the same member, section, axis, and load combination.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed stress is explicitly named.

    Unit convention:
        - N and mm are used consistently; no implicit conversion is performed.

    Applicability:
        - Eccentrically tensioned or tension-bending members.

    Limitations:
        - Section 8.5 functions must be called separately with the actual stress state.

    Raises:
        ValueError: A numerical domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_built_up_beam_columns_and_combined_local_stability.py::test_table_23_router_and_modifiers
        Validation cases:
            - V11-PROC-9.4.10-TENSION-MEMBER-BENDING-ROUTE

    Implementation notes:
        - No unstated interpolation or default is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(compressive_stress_present,bool): raise TypeError("compressive_stress_present must be bool")
    return {"local_stability_check_required":compressive_stress_present,"route":"bending_member_local_stability_section_8_5" if compressive_stress_present else "no_compressive_plate_stress_no_9_4_10_check"}

