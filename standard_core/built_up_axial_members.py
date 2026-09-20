"""Built-up axial member calculations for СП 16.13330.2017 clauses 7.2.1-7.2.10."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .axial_members import (
    axial_strength_utilization_ultimate,
    axial_strength_utilization_yield,
    central_compression_stability_coefficient,
    central_compression_stability_utilization,
)

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_8 = json.loads((_DATA_DIR / "table_8_built_up_effective_slenderness.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-7.2.1-STRENGTH",
    "SP16-PROC-7.2.2-METHOD-SELECTION",
    "SP16-PROC-7.2.2-OVERALL-STABILITY",
    "SP16-PROC-7.2.3-BATTEN-BRANCH-LIMIT",
    "SP16-PROC-7.2.4-LATTICE-BRANCH-LIMIT",
    "SP16-PROC-7.2.5-BRANCH-PHI",
    "SP16-PROC-7.2.5-REDUCED-RESISTANCE",
    "SP16-PROC-7.2.6-CONNECTION-SPACING",
    "SP16-PROC-7.2.7-SHEAR-DISTRIBUTION",
    "SP16-PROC-7.2.10-RESTRAINT-FORCE",
    "SP16-PROC-7.2.10-COLUMN-SPACER",
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


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def table_8_formula_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited formula and symbol metadata transcribed from Table 8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2-7.2.5
        Annex: None
        Equation/Table: Table 8; equations (12)-(17)
        Audit ID: SP16-TBL-8
        Normative status: normative

    Mathematical form:
        Immutable JSON catalogue of the six effective-slenderness expressions and symbol notes.

    Parameters:
        None:
            Type: not applicable
            Unit: not applicable
            Meaning: The catalogue has no runtime inputs.
            Valid range: not applicable
            Source: data/table_8_built_up_effective_slenderness.json

    Returns:
        Type: dict[str, Any]
        Unit: mixed metadata
        Meaning: Deep copy of the Table 8 transcription catalogue.

    Assumptions:
        - The section type and connector system are selected externally from the table diagrams.

    Sign convention:
        - Slenderness and geometric quantities are non-negative magnitudes.

    Unit convention:
        - Formula metadata preserves the standard symbols; executable functions use explicit mm and mm4 names.

    Applicability:
        - Built-up members with at least six panels under clause 7.2.2.

    Limitations:
        - The function does not classify arbitrary cross-section geometry from a model.

    Raises:
        None: The bundled data file is loaded when the module is imported.

    Examples:
        >>> table_8_formula_catalog()["table_number"]
        '8'

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_table_8_catalog_exists_and_is_consistent
        Validation cases:
            - BUILTUP-TBL-008

    Implementation notes:
        - A JSON round trip returns a detached copy and prevents mutation of module state.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_8, ensure_ascii=False))


def built_up_axial_strength_utilization(
    axial_force_n: float,
    total_net_area_mm2: float,
    resistance_branch: str,
    design_yield_resistance_n_mm2: float,
    design_ultimate_resistance_n_mm2: float,
    ultimate_resistance_safety_factor: float,
    working_condition_factor: float,
) -> float:
    """
    Summary:
        Calculate clause 7.2.1 built-up-member strength by the applicable equation (5) branch.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.1 with reference to 7.1.1
        Annex: None
        Equation/Table: Equation (5)
        Audit ID: SP16-PROC-7.2.1-STRENGTH
        Normative status: normative

    Mathematical form:
        yield: N/(A_n R_y gamma_c); ultimate: N gamma_u/(A_n R_u gamma_c).

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Magnitude of the central tensile or compressive force.
            Valid range: >= 0
            Source: structural analysis
        total_net_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Net area of the complete built-up member.
            Valid range: > 0
            Source: section geometry
        resistance_branch:
            Type: str
            Unit: dimensionless selector
            Meaning: Explicit equation (5) branch: yield or ultimate.
            Valid range: yield | ultimate
            Source: clause-applicability decision
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design ultimate resistance R_u.
            Valid range: > 0
            Source: clause 6.1
        ultimate_resistance_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Explicit gamma_u for the ultimate branch.
            Valid range: > 0
            Source: clause 4.3.2 or project input
        working_condition_factor:
            Type: float
            Unit: dimensionless
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: Table 1 or applicable clause

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Strength utilization; compliance requires a value not greater than 1.

    Assumptions:
        - The selected resistance branch is applicable to the member and material.

    Sign convention:
        - axial_force_n is a non-negative magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used without implicit conversion.

    Applicability:
        - Central tension or compression of built-up sections under clause 7.2.1.

    Limitations:
        - The function does not infer branch applicability or net-section deductions.

    Raises:
        ValueError: The branch is unsupported or numerical inputs are outside their domains.
        TypeError: A numerical input is not a real number.

    Examples:
        >>> built_up_axial_strength_utilization(500000, 2500, "yield", 355, 485, 1.3, 1.0)
        0.5633802816901409

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_clause_7_2_1_strength_branches
        Validation cases:
            - BUILTUP-PROC-7.2.1

    Implementation notes:
        - No branch is selected from steel grade automatically.
        - Defaults must be explicit in the input configuration.
    """
    if resistance_branch == "yield":
        return axial_strength_utilization_yield(
            axial_force_n, total_net_area_mm2, design_yield_resistance_n_mm2, working_condition_factor
        )
    if resistance_branch == "ultimate":
        return axial_strength_utilization_ultimate(
            axial_force_n,
            total_net_area_mm2,
            design_ultimate_resistance_n_mm2,
            ultimate_resistance_safety_factor,
            working_condition_factor,
        )
    raise ValueError("resistance_branch must be 'yield' or 'ultimate'")


def built_up_stability_method(panel_count: int, connector_system: str) -> str:
    """
    Summary:
        Select the clause 7.2.2 stability route from panel count and connector system.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2
        Annex: None
        Equation/Table: Table 8 applicability rule
        Audit ID: SP16-PROC-7.2.2-METHOD-SELECTION
        Normative status: normative

    Mathematical form:
        panels >= 6 -> Table 8; panels < 6 with battens -> frame analysis; panels < 6 with lattice -> clause 7.2.5.

    Parameters:
        panel_count:
            Type: int
            Unit: panels
            Meaning: Number of connector panels along the member.
            Valid range: >= 1
            Source: member geometry
        connector_system:
            Type: str
            Unit: categorical
            Meaning: Connector system between branches.
            Valid range: battens | lattice
            Source: structural detailing

    Returns:
        Type: str
        Unit: categorical
        Meaning: Required calculation route identifier.

    Assumptions:
        - Panel count is counted consistently along the checked member length.

    Sign convention:
        - Panel count is positive.

    Unit convention:
        - Panel count is dimensionless.

    Applicability:
        - Built-up compressed members with battens or lattice.

    Limitations:
        - The returned frame-analysis route is not solved by this package.

    Raises:
        TypeError: panel_count is not an integer.
        ValueError: panel_count or connector_system is invalid.

    Examples:
        >>> built_up_stability_method(8, "battens")
        'table_8_effective_slenderness'

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_stability_method_selection
        Validation cases:
            - BUILTUP-PROC-7.2.2-METHOD

    Implementation notes:
        - A frame-analysis requirement is surfaced rather than approximated.
        - Defaults must be explicit in the input configuration.
    """
    count = _positive_integer(panel_count, "panel_count")
    if connector_system not in {"battens", "lattice"}:
        raise ValueError("connector_system must be 'battens' or 'lattice'")
    if count >= 6:
        return "table_8_effective_slenderness"
    if connector_system == "battens":
        return "frame_system_analysis_required"
    return "clause_7_2_5_lattice_branch_method"


def battened_effective_slenderness_type_1(
    whole_member_slenderness_y: float,
    branch_slenderness_1: float,
    branch_inertia_axis_1_mm4: float,
    branch_axis_spacing_b_mm: float,
    batten_inertia_mm4: float,
    batten_pitch_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (12) effective slenderness for battened section type 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2-7.2.3
        Annex: None
        Equation/Table: Equation (12), Table 8
        Audit ID: SP16-EQ-012
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_y^2 + 0.82(1+n) lambda_b1^2), n = I_b1 b/(I_s l_b).

    Parameters:
        whole_member_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Slenderness of the complete member in the plane perpendicular to y-y.
            Valid range: >= 0
            Source: member geometry
        branch_slenderness_1:
            Type: float
            Unit: dimensionless
            Meaning: Slenderness of one branch between battens about axis 1-1.
            Valid range: >= 0
            Source: branch geometry
        branch_inertia_axis_1_mm4:
            Type: float
            Unit: mm4
            Meaning: Branch second moment of area I_b1.
            Valid range: > 0
            Source: branch section
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Distance b between branch axes.
            Valid range: > 0
            Source: built-up geometry
        batten_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Second moment of area I_s of one batten about its own x-x axis.
            Valid range: > 0
            Source: batten geometry
        batten_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Distance l_b between battens.
            Valid range: > 0
            Source: built-up geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - Section type 1 and batten arrangement match the Table 8 diagram.
        - At least six panels are present.

    Sign convention:
        - All geometric quantities and slenderness values are positive magnitudes.

    Unit convention:
        - Lengths use mm and inertias use mm4; their ratio n is dimensionless.

    Applicability:
        - Battened built-up section type 1 under Table 8.

    Limitations:
        - The function does not derive branch or member slenderness from geometry.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> round(battened_effective_slenderness_type_1(2, 1, 200000, 400, 500000, 1000), 6)
        2.324569

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_12_type_1_battened
        Validation cases:
            - BUILTUP-EQ-012

    Implementation notes:
        - The coefficient 0.82 is transcribed directly from Table 8.
        - Defaults must be explicit in the input configuration.
    """
    ly = _nonnegative(whole_member_slenderness_y, "whole_member_slenderness_y")
    lb1 = _nonnegative(branch_slenderness_1, "branch_slenderness_1")
    ib1 = _positive(branch_inertia_axis_1_mm4, "branch_inertia_axis_1_mm4")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    is_ = _positive(batten_inertia_mm4, "batten_inertia_mm4")
    pitch = _positive(batten_pitch_mm, "batten_pitch_mm")
    n = ib1 * b / (is_ * pitch)
    return math.sqrt(ly * ly + 0.82 * (1.0 + n) * lb1 * lb1)


def battened_effective_slenderness_type_2(
    whole_member_max_slenderness: float,
    branch_slenderness_1: float,
    branch_slenderness_2: float,
    branch_inertia_axis_1_mm4: float,
    branch_inertia_axis_2_mm4: float,
    branch_axis_spacing_b1_mm: float,
    branch_axis_spacing_b2_mm: float,
    batten_inertia_plane_1_mm4: float,
    batten_inertia_plane_2_mm4: float,
    batten_pitch_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (13) effective slenderness for battened section type 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2-7.2.3
        Annex: None
        Equation/Table: Equation (13), Table 8
        Audit ID: SP16-EQ-013
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_max^2 + 0.82[(1+n1) lambda_b1^2 + (1+n2) lambda_b2^2]).

    Parameters:
        whole_member_max_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Greater complete-member slenderness lambda_max.
            Valid range: >= 0
            Source: member geometry
        branch_slenderness_1:
            Type: float
            Unit: dimensionless
            Meaning: Branch slenderness about axis 1-1.
            Valid range: >= 0
            Source: branch geometry
        branch_slenderness_2:
            Type: float
            Unit: dimensionless
            Meaning: Branch slenderness about axis 2-2.
            Valid range: >= 0
            Source: branch geometry
        branch_inertia_axis_1_mm4:
            Type: float
            Unit: mm4
            Meaning: Second moment of area I_b1 of two angles about 1-1.
            Valid range: > 0
            Source: branch section
        branch_inertia_axis_2_mm4:
            Type: float
            Unit: mm4
            Meaning: Second moment of area I_b2 of two angles about 2-2.
            Valid range: > 0
            Source: branch section
        branch_axis_spacing_b1_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis distance b1.
            Valid range: > 0
            Source: built-up geometry
        branch_axis_spacing_b2_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis distance b2.
            Valid range: > 0
            Source: built-up geometry
        batten_inertia_plane_1_mm4:
            Type: float
            Unit: mm4
            Meaning: Batten inertia I_s1 for the plane perpendicular to 1-1.
            Valid range: > 0
            Source: batten geometry
        batten_inertia_plane_2_mm4:
            Type: float
            Unit: mm4
            Meaning: Batten inertia I_s2 for the plane perpendicular to 2-2.
            Valid range: > 0
            Source: batten geometry
        batten_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Distance l_b between battens.
            Valid range: > 0
            Source: built-up geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - Section type 2 and both batten systems match Table 8.
        - At least six panels are present.

    Sign convention:
        - Inputs are non-negative magnitudes.

    Unit convention:
        - Lengths use mm and inertias use mm4.

    Applicability:
        - Battened built-up section type 2 under Table 8.

    Limitations:
        - No geometric section classification is performed.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> value = battened_effective_slenderness_type_2(2, 1, 1.1, 200000, 220000, 350, 450, 500000, 550000, 1000)
        >>> value > 2
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_13_type_2_battened
        Validation cases:
            - BUILTUP-EQ-013

    Implementation notes:
        - n1 and n2 are evaluated independently as printed in Table 8.
        - Defaults must be explicit in the input configuration.
    """
    lm = _nonnegative(whole_member_max_slenderness, "whole_member_max_slenderness")
    lb1 = _nonnegative(branch_slenderness_1, "branch_slenderness_1")
    lb2 = _nonnegative(branch_slenderness_2, "branch_slenderness_2")
    ib1 = _positive(branch_inertia_axis_1_mm4, "branch_inertia_axis_1_mm4")
    ib2 = _positive(branch_inertia_axis_2_mm4, "branch_inertia_axis_2_mm4")
    b1 = _positive(branch_axis_spacing_b1_mm, "branch_axis_spacing_b1_mm")
    b2 = _positive(branch_axis_spacing_b2_mm, "branch_axis_spacing_b2_mm")
    is1 = _positive(batten_inertia_plane_1_mm4, "batten_inertia_plane_1_mm4")
    is2 = _positive(batten_inertia_plane_2_mm4, "batten_inertia_plane_2_mm4")
    pitch = _positive(batten_pitch_mm, "batten_pitch_mm")
    n1 = ib1 * b1 / (is1 * pitch)
    n2 = ib2 * b2 / (is2 * pitch)
    return math.sqrt(lm * lm + 0.82 * ((1.0 + n1) * lb1 * lb1 + (1.0 + n2) * lb2 * lb2))


def battened_effective_slenderness_type_3(
    whole_member_max_slenderness: float,
    branch_slenderness_3: float,
    branch_inertia_axis_3_mm4: float,
    branch_axis_spacing_b_mm: float,
    batten_inertia_mm4: float,
    batten_pitch_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (14) effective slenderness for battened section type 3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2-7.2.3
        Annex: None
        Equation/Table: Equation (14), Table 8
        Audit ID: SP16-EQ-014
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_max^2 + 0.82(1+3n3) lambda_b3^2), n3 = I_b3 b/(I_s l_b).

    Parameters:
        whole_member_max_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Greater complete-member slenderness lambda_max.
            Valid range: >= 0
            Source: member geometry
        branch_slenderness_3:
            Type: float
            Unit: dimensionless
            Meaning: Branch slenderness about axis 3-3.
            Valid range: >= 0
            Source: branch geometry
        branch_inertia_axis_3_mm4:
            Type: float
            Unit: mm4
            Meaning: Branch second moment of area I_b3.
            Valid range: > 0
            Source: branch section
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Distance b between branch axes.
            Valid range: > 0
            Source: built-up geometry
        batten_inertia_mm4:
            Type: float
            Unit: mm4
            Meaning: Batten second moment of area I_s.
            Valid range: > 0
            Source: batten geometry
        batten_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Distance l_b between battens.
            Valid range: > 0
            Source: built-up geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - The three-sided section matches Table 8 type 3.
        - At least six panels are present.

    Sign convention:
        - Inputs are non-negative magnitudes.

    Unit convention:
        - Lengths use mm and inertias use mm4.

    Applicability:
        - Battened built-up section type 3.

    Limitations:
        - No check of geometric equality of the three sides is performed.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> battened_effective_slenderness_type_3(2, 1, 180000, 400, 500000, 1000) > 2
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_14_type_3_battened
        Validation cases:
            - BUILTUP-EQ-014

    Implementation notes:
        - The multiplier 3 on n3 is part of the printed equation.
        - Defaults must be explicit in the input configuration.
    """
    lm = _nonnegative(whole_member_max_slenderness, "whole_member_max_slenderness")
    lb3 = _nonnegative(branch_slenderness_3, "branch_slenderness_3")
    ib3 = _positive(branch_inertia_axis_3_mm4, "branch_inertia_axis_3_mm4")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    is_ = _positive(batten_inertia_mm4, "batten_inertia_mm4")
    pitch = _positive(batten_pitch_mm, "batten_pitch_mm")
    n3 = ib3 * b / (is_ * pitch)
    return math.sqrt(lm * lm + 0.82 * (1.0 + 3.0 * n3) * lb3 * lb3)


def lattice_effective_slenderness_type_1(
    whole_member_slenderness_y: float,
    total_area_mm2: float,
    diagonal_area_plane_1_mm2: float,
    diagonal_length_d_mm: float,
    branch_axis_spacing_b_mm: float,
    panel_length_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (15) effective slenderness for lattice section type 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2 and 7.2.4-7.2.5
        Annex: None
        Equation/Table: Equation (15), Table 8
        Audit ID: SP16-EQ-015
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_y^2 + alpha A/A_d1), alpha = 10 d^3/(b^2 l_b).

    Parameters:
        whole_member_slenderness_y:
            Type: float
            Unit: dimensionless
            Meaning: Complete-member slenderness perpendicular to y-y.
            Valid range: >= 0
            Source: member geometry
        total_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A of the complete built-up member.
            Valid range: > 0
            Source: section geometry
        diagonal_area_plane_1_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_d1 of one diagonal, or two diagonals for cross lattice, in the specified plane.
            Valid range: > 0
            Source: lattice geometry
        diagonal_length_d_mm:
            Type: float
            Unit: mm
            Meaning: Dimension d from Figure 3.
            Valid range: > 0
            Source: panel geometry
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Distance b between branch axes.
            Valid range: > 0
            Source: built-up geometry
        panel_length_mm:
            Type: float
            Unit: mm
            Meaning: Panel dimension l_b from Figure 3.
            Valid range: > 0
            Source: panel geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - Section type 1 and lattice arrangement match Table 8.
        - A_d1 is assembled according to the Table 8 note for cross lattice.

    Sign convention:
        - All inputs are positive magnitudes.

    Unit convention:
        - Lengths use mm and areas use mm2.

    Applicability:
        - Lattice-connected built-up section type 1 with at least six panels.

    Limitations:
        - The function does not infer whether one or two diagonal areas must be supplied.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> lattice_effective_slenderness_type_1(2, 5000, 500, 600, 400, 1000) > 2
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_15_type_1_lattice
        Validation cases:
            - BUILTUP-EQ-015

    Implementation notes:
        - The factor 10 is transcribed directly from Table 8.
        - Defaults must be explicit in the input configuration.
    """
    ly = _nonnegative(whole_member_slenderness_y, "whole_member_slenderness_y")
    area = _positive(total_area_mm2, "total_area_mm2")
    ad = _positive(diagonal_area_plane_1_mm2, "diagonal_area_plane_1_mm2")
    d = _positive(diagonal_length_d_mm, "diagonal_length_d_mm")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    panel = _positive(panel_length_mm, "panel_length_mm")
    alpha = 10.0 * d**3 / (b**2 * panel)
    return math.sqrt(ly * ly + alpha * area / ad)


def lattice_effective_slenderness_type_2(
    whole_member_max_slenderness: float,
    total_area_mm2: float,
    diagonal_area_plane_1_mm2: float,
    diagonal_area_plane_2_mm2: float,
    diagonal_length_d1_mm: float,
    diagonal_length_d2_mm: float,
    branch_axis_spacing_b1_mm: float,
    branch_axis_spacing_b2_mm: float,
    panel_length_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (16) effective slenderness for lattice section type 2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2 and 7.2.4-7.2.5
        Annex: None
        Equation/Table: Equation (16), Table 8
        Audit ID: SP16-EQ-016
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_max^2 + (alpha1 + alpha2 A_d1/A_d2) A/A_d1).

    Parameters:
        whole_member_max_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Greater complete-member slenderness lambda_max.
            Valid range: >= 0
            Source: member geometry
        total_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A of the complete built-up member.
            Valid range: > 0
            Source: section geometry
        diagonal_area_plane_1_mm2:
            Type: float
            Unit: mm2
            Meaning: Lattice diagonal area A_d1 for plane 1.
            Valid range: > 0
            Source: lattice geometry
        diagonal_area_plane_2_mm2:
            Type: float
            Unit: mm2
            Meaning: Lattice diagonal area A_d2 for plane 2.
            Valid range: > 0
            Source: lattice geometry
        diagonal_length_d1_mm:
            Type: float
            Unit: mm
            Meaning: Diagonal dimension d1 associated with side b1.
            Valid range: > 0
            Source: panel geometry
        diagonal_length_d2_mm:
            Type: float
            Unit: mm
            Meaning: Diagonal dimension d2 associated with side b2.
            Valid range: > 0
            Source: panel geometry
        branch_axis_spacing_b1_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis spacing b1.
            Valid range: > 0
            Source: built-up geometry
        branch_axis_spacing_b2_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis spacing b2.
            Valid range: > 0
            Source: built-up geometry
        panel_length_mm:
            Type: float
            Unit: mm
            Meaning: Common panel dimension l_b.
            Valid range: > 0
            Source: panel geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - d1 and d2 correspond to b1 and b2 respectively, as required by Table 8.

    Sign convention:
        - Inputs are positive magnitudes.

    Unit convention:
        - Lengths use mm and areas use mm2.

    Applicability:
        - Lattice-connected built-up section type 2 with at least six panels.

    Limitations:
        - The function does not validate the diagram-level orientation of the two lattice planes.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> lattice_effective_slenderness_type_2(2, 5000, 500, 550, 600, 650, 350, 450, 1000) > 2
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_16_type_2_lattice
        Validation cases:
            - BUILTUP-EQ-016

    Implementation notes:
        - alpha1 and alpha2 use their corresponding d and b dimensions independently.
        - Defaults must be explicit in the input configuration.
    """
    lm = _nonnegative(whole_member_max_slenderness, "whole_member_max_slenderness")
    area = _positive(total_area_mm2, "total_area_mm2")
    ad1 = _positive(diagonal_area_plane_1_mm2, "diagonal_area_plane_1_mm2")
    ad2 = _positive(diagonal_area_plane_2_mm2, "diagonal_area_plane_2_mm2")
    d1 = _positive(diagonal_length_d1_mm, "diagonal_length_d1_mm")
    d2 = _positive(diagonal_length_d2_mm, "diagonal_length_d2_mm")
    b1 = _positive(branch_axis_spacing_b1_mm, "branch_axis_spacing_b1_mm")
    b2 = _positive(branch_axis_spacing_b2_mm, "branch_axis_spacing_b2_mm")
    panel = _positive(panel_length_mm, "panel_length_mm")
    alpha1 = 10.0 * d1**3 / (b1**2 * panel)
    alpha2 = 10.0 * d2**3 / (b2**2 * panel)
    return math.sqrt(lm * lm + (alpha1 + alpha2 * ad1 / ad2) * area / ad1)


def lattice_effective_slenderness_type_3(
    whole_member_max_slenderness: float,
    total_area_mm2: float,
    diagonal_area_one_face_mm2: float,
    diagonal_length_d_mm: float,
    branch_axis_spacing_b_mm: float,
    panel_length_mm: float,
) -> float:
    """
    Summary:
        Calculate Table 8 equation (17) effective slenderness for lattice section type 3.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2 and 7.2.4-7.2.5
        Annex: None
        Equation/Table: Equation (17), Table 8
        Audit ID: SP16-EQ-017
        Normative status: normative

    Mathematical form:
        lambda_ef = sqrt(lambda_max^2 + 0.67 alpha A/A_d3), alpha = 10 d^3/(b^2 l_b).

    Parameters:
        whole_member_max_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Greater complete-member slenderness lambda_max.
            Valid range: >= 0
            Source: member geometry
        total_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A of the complete member.
            Valid range: > 0
            Source: section geometry
        diagonal_area_one_face_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_d3 in one face, with the Table 8 cross-lattice area convention.
            Valid range: > 0
            Source: lattice geometry
        diagonal_length_d_mm:
            Type: float
            Unit: mm
            Meaning: Dimension d from Figure 3.
            Valid range: > 0
            Source: panel geometry
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Branch-axis spacing b.
            Valid range: > 0
            Source: built-up geometry
        panel_length_mm:
            Type: float
            Unit: mm
            Meaning: Panel dimension l_b.
            Valid range: > 0
            Source: panel geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Effective geometrical slenderness lambda_ef.

    Assumptions:
        - The section is the equilateral three-sided type shown in Table 8.

    Sign convention:
        - Inputs are positive magnitudes.

    Unit convention:
        - Lengths use mm and areas use mm2.

    Applicability:
        - Lattice-connected built-up section type 3 with at least six panels.

    Limitations:
        - Geometric equality of the three faces is an external prerequisite.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: A numerical input is non-finite or outside its valid range.

    Examples:
        >>> lattice_effective_slenderness_type_3(2, 5000, 500, 600, 400, 1000) > 2
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_17_type_3_lattice
        Validation cases:
            - BUILTUP-EQ-017

    Implementation notes:
        - The coefficient 0.67 is transcribed directly from Table 8.
        - Defaults must be explicit in the input configuration.
    """
    lm = _nonnegative(whole_member_max_slenderness, "whole_member_max_slenderness")
    area = _positive(total_area_mm2, "total_area_mm2")
    ad3 = _positive(diagonal_area_one_face_mm2, "diagonal_area_one_face_mm2")
    d = _positive(diagonal_length_d_mm, "diagonal_length_d_mm")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    panel = _positive(panel_length_mm, "panel_length_mm")
    alpha = 10.0 * d**3 / (b**2 * panel)
    return math.sqrt(lm * lm + 0.67 * alpha * area / ad3)


def batten_branch_slenderness_check(branch_relative_slenderness: float) -> dict[str, Any]:
    """
    Summary:
        Check the clause 7.2.3 branch relative-slenderness limit for battened members.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.3
        Annex: None
        Equation/Table: Table 8 branch quantities
        Audit ID: SP16-PROC-7.2.3-BATTEN-BRANCH-LIMIT
        Normative status: normative

    Mathematical form:
        branch relative slenderness <= 1.4.

    Parameters:
        branch_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness of a branch between batten attachments.
            Valid range: >= 0
            Source: branch calculation

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Limit, input value, and pass/fail result.

    Assumptions:
        - The branch slenderness is based on the axis required by clause 7.2.3.

    Sign convention:
        - Slenderness is non-negative.

    Unit convention:
        - Relative slenderness is dimensionless.

    Applicability:
        - Battened built-up members.

    Limitations:
        - The alternative half-section radius rule for a solid sheet must be applied before calling.

    Raises:
        TypeError: The value is not real.
        ValueError: The value is negative or non-finite.

    Examples:
        >>> batten_branch_slenderness_check(1.4)["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_batten_branch_limit
        Validation cases:
            - BUILTUP-PROC-7.2.3

    Implementation notes:
        - Equality is accepted because the clause says not greater than 1.4.
        - Defaults must be explicit in the input configuration.
    """
    value = _nonnegative(branch_relative_slenderness, "branch_relative_slenderness")
    return {"branch_relative_slenderness": value, "limit": 1.4, "pass": value <= 1.4}


def lattice_branch_slenderness_assessment(
    branch_relative_slenderness: float,
    member_effective_relative_slenderness: float,
    clause_7_2_5_check_performed: bool,
) -> dict[str, Any]:
    """
    Summary:
        Classify lattice-branch slenderness under the basic and extended limits of clause 7.2.4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.4-7.2.5
        Annex: None
        Equation/Table: Unnumbered branch-slenderness limits
        Audit ID: SP16-PROC-7.2.4-LATTICE-BRANCH-LIMIT
        Normative status: normative

    Mathematical form:
        Basic: lambda_b <= 2.7 and lambda_b <= lambda_ef; extended: lambda_b <= 4.1 only with clause 7.2.5 calculation.

    Parameters:
        branch_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative slenderness of an individual branch between lattice nodes.
            Valid range: >= 0
            Source: branch calculation
        member_effective_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Relative effective slenderness of the complete built-up member.
            Valid range: >= 0
            Source: Table 8 plus material normalization
        clause_7_2_5_check_performed:
            Type: bool
            Unit: boolean
            Meaning: Whether the enhanced branch-resistance procedure of 7.2.5 was performed.
            Valid range: true | false
            Source: calculation workflow

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Basic-limit status, relation-to-member status, extended-route status, and overall classification.

    Assumptions:
        - The supplied values use the same material normalization.

    Sign convention:
        - Slenderness values are non-negative.

    Unit convention:
        - Relative slenderness is dimensionless.

    Applicability:
        - Individual branches of lattice-connected built-up members.

    Limitations:
        - For the extended 2.7-4.1 range, the standard wording does not explicitly restate the lambda_b <= lambda_ef condition; both facts are reported separately rather than silently inferred.

    Raises:
        TypeError: Inputs have invalid types.
        ValueError: Slenderness values are negative or non-finite.

    Examples:
        >>> lattice_branch_slenderness_assessment(3.0, 2.5, True)["classification"]
        'permitted_only_with_clause_7_2_5'

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_lattice_branch_assessment
        Validation cases:
            - BUILTUP-PROC-7.2.4

    Implementation notes:
        - The 4.1 upper bound is enforced exactly.
        - Defaults must be explicit in the input configuration.
    """
    branch = _nonnegative(branch_relative_slenderness, "branch_relative_slenderness")
    member = _nonnegative(member_effective_relative_slenderness, "member_effective_relative_slenderness")
    if not isinstance(clause_7_2_5_check_performed, bool):
        raise TypeError("clause_7_2_5_check_performed must be boolean")
    basic_limit = branch <= 2.7
    not_above_member = branch <= member
    if basic_limit and not_above_member:
        classification = "basic_limits_satisfied"
        permitted = True
    elif branch <= 4.1 and branch > 2.7 and clause_7_2_5_check_performed:
        classification = "permitted_only_with_clause_7_2_5"
        permitted = True
    elif branch > 4.1:
        classification = "exceeds_absolute_4_1_limit"
        permitted = False
    elif branch <= 2.7 and not not_above_member:
        classification = "exceeds_member_effective_slenderness"
        permitted = False
    else:
        classification = "clause_7_2_5_check_required"
        permitted = False
    return {
        "branch_relative_slenderness": branch,
        "member_effective_relative_slenderness": member,
        "basic_2_7_limit_pass": basic_limit,
        "not_above_member_effective_slenderness": not_above_member,
        "absolute_4_1_limit_pass": branch <= 4.1,
        "clause_7_2_5_check_performed": clause_7_2_5_check_performed,
        "classification": classification,
        "permitted": permitted,
    }


def lattice_branch_stability_coefficient(branch_relative_slenderness: float, branch_section_type: str) -> float:
    """
    Summary:
        Calculate the branch stability coefficient phi_1 required by clause 7.2.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.5
        Annex: None
        Equation/Table: Equation (8) with effective branch length 0.7 l_b
        Audit ID: SP16-PROC-7.2.5-BRANCH-PHI
        Normative status: normative

    Mathematical form:
        phi_1=1 for lambda_b<=2.7; equation (8) at 0.7 lambda_b for lambda_b>=3.2; linear interpolation in between.

    Parameters:
        branch_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Branch relative slenderness based on branch length l_b.
            Valid range: >= 0
            Source: branch calculation
        branch_section_type:
            Type: str
            Unit: categorical
            Meaning: Section type a, b, or c used by equation (8).
            Valid range: a | b | c
            Source: Table 7 classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Branch stability coefficient phi_1.

    Assumptions:
        - Relative slenderness scales linearly with effective length, so 0.7 l_b is represented by 0.7 lambda_b.

    Sign convention:
        - Slenderness is non-negative.

    Unit convention:
        - Relative slenderness and phi_1 are dimensionless.

    Applicability:
        - Lattice-member branch check under clause 7.2.5.

    Limitations:
        - Section-type classification remains an explicit engineering input.

    Raises:
        TypeError: The slenderness is not real.
        ValueError: The slenderness or section type is invalid.

    Examples:
        >>> lattice_branch_stability_coefficient(2.7, "b")
        1.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_lattice_branch_phi_rules
        Validation cases:
            - BUILTUP-PROC-7.2.5-PHI1

    Implementation notes:
        - The interpolation endpoint at 3.2 is evaluated once at 0.7*3.2.
        - Defaults must be explicit in the input configuration.
    """
    slenderness = _nonnegative(branch_relative_slenderness, "branch_relative_slenderness")
    if slenderness <= 2.7:
        return 1.0
    endpoint_phi = central_compression_stability_coefficient(0.7 * 3.2, branch_section_type)
    if slenderness < 3.2:
        fraction = (slenderness - 2.7) / 0.5
        return 1.0 + fraction * (endpoint_phi - 1.0)
    return central_compression_stability_coefficient(0.7 * slenderness, branch_section_type)


def lattice_built_up_stability_utilization(
    axial_force_n: float,
    gross_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    working_condition_factor: float,
    member_effective_relative_slenderness: float,
    branch_relative_slenderness: float,
    branch_section_type: str,
) -> dict[str, float]:
    """
    Summary:
        Apply equation (7) to a lattice built-up member using the reduced resistance phi_1 R_y from clause 7.2.5.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.2 and 7.2.5
        Annex: None
        Equation/Table: Equations (7)-(9), Table 8
        Audit ID: SP16-PROC-7.2.5-REDUCED-RESISTANCE
        Normative status: normative

    Mathematical form:
        utilization=N/[phi(lambda_ef,type b) A (phi_1 R_y) gamma_c].

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Compressive force magnitude N.
            Valid range: >= 0
            Source: structural analysis
        gross_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Gross area A of the complete member.
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
            Meaning: Working-condition factor gamma_c.
            Valid range: > 0
            Source: applicable clause or Table 1
        member_effective_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Complete-member relative effective slenderness.
            Valid range: >= 0
            Source: Table 8 and material normalization
        branch_relative_slenderness:
            Type: float
            Unit: dimensionless
            Meaning: Branch relative slenderness based on l_b.
            Valid range: >= 0
            Source: branch geometry
        branch_section_type:
            Type: str
            Unit: categorical
            Meaning: Table 7 type of the individual branch.
            Valid range: a | b | c
            Source: engineering classification

    Returns:
        Type: dict[str, float]
        Unit: mixed
        Meaning: Overall phi, branch phi_1, reduced resistance, and equation (7) utilization.

    Assumptions:
        - Overall built-up-member phi is evaluated as section type b, as required by clause 7.2.2.
        - The member satisfies the geometric and branch checks required by clauses 7.2.2-7.2.5.

    Sign convention:
        - axial_force_n is a non-negative compression magnitude.

    Unit convention:
        - N, mm2, and N/mm2 are used directly.

    Applicability:
        - Lattice-connected built-up compressed members.

    Limitations:
        - The function does not calculate the member relative slenderness from geometric lambda_ef.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is invalid.

    Examples:
        >>> result = lattice_built_up_stability_utilization(500000, 5000, 355, 1, 2, 3, "b")
        >>> result["utilization"] > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_lattice_built_up_stability_utilization
        Validation cases:
            - BUILTUP-PROC-7.2.5-STABILITY

    Implementation notes:
        - Reduced resistance is exposed in the return value for auditability.
        - Defaults must be explicit in the input configuration.
    """
    member_lambda = _nonnegative(member_effective_relative_slenderness, "member_effective_relative_slenderness")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    phi_overall = central_compression_stability_coefficient(member_lambda, "b")
    phi_branch = lattice_branch_stability_coefficient(branch_relative_slenderness, branch_section_type)
    reduced_ry = phi_branch * ry
    utilization = central_compression_stability_utilization(
        axial_force_n, gross_area_mm2, reduced_ry, working_condition_factor, phi_overall
    )
    return {
        "overall_stability_coefficient_phi": phi_overall,
        "branch_stability_coefficient_phi_1": phi_branch,
        "reduced_design_resistance_phi_1_ry_n_mm2": reduced_ry,
        "utilization": utilization,
    }


def close_contact_connection_spacing_check(
    connection_spacing_mm: float,
    selected_radius_of_gyration_mm: float,
    force_state: str,
    intermediate_connection_count: int,
) -> dict[str, Any]:
    """
    Summary:
        Check clause 7.2.6 connector spacing and the minimum intermediate-connection count for compressed members.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.6
        Annex: None
        Equation/Table: Unnumbered 40i and 80i limits
        Audit ID: SP16-PROC-7.2.6-CONNECTION-SPACING
        Normative status: normative

    Mathematical form:
        compression spacing <=40i and at least two intermediate connections; tension spacing <=80i.

    Parameters:
        connection_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Distance between connecting welds or centers of extreme bolts.
            Valid range: >= 0
            Source: detailing
        selected_radius_of_gyration_mm:
            Type: float
            Unit: mm
            Meaning: Radius i selected according to the section configuration stated in 7.2.6.
            Valid range: > 0
            Source: section geometry
        force_state:
            Type: str
            Unit: categorical
            Meaning: Member force state.
            Valid range: compression | tension
            Source: structural analysis
        intermediate_connection_count:
            Type: int
            Unit: connections
            Meaning: Number of intermediate ties or packings within a compressed-member length.
            Valid range: >= 0
            Source: detailing

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Spacing limit, spacing result, count result, and overall pass status.

    Assumptions:
        - The correct radius of gyration has been selected externally from the clause rule.

    Sign convention:
        - Spacing and radius are positive magnitudes.

    Unit convention:
        - Spacing and radius use the same length unit, here mm.

    Applicability:
        - Angles, channels, and similar components connected in contact or through packings.

    Limitations:
        - The function does not determine the appropriate principal or minimum radius automatically.

    Raises:
        TypeError: Numeric or count inputs have invalid types.
        ValueError: Inputs are outside their domains.

    Examples:
        >>> close_contact_connection_spacing_check(300, 10, "compression", 2)["pass"]
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_close_contact_spacing_check
        Validation cases:
            - BUILTUP-PROC-7.2.6

    Implementation notes:
        - The intermediate-connection requirement is reported as not applicable for tension.
        - Defaults must be explicit in the input configuration.
    """
    spacing = _nonnegative(connection_spacing_mm, "connection_spacing_mm")
    radius = _positive(selected_radius_of_gyration_mm, "selected_radius_of_gyration_mm")
    if isinstance(intermediate_connection_count, bool) or not isinstance(intermediate_connection_count, int):
        raise TypeError("intermediate_connection_count must be an integer")
    if intermediate_connection_count < 0:
        raise ValueError("intermediate_connection_count must be non-negative")
    if force_state == "compression":
        factor = 40.0
        count_pass: bool | None = intermediate_connection_count >= 2
    elif force_state == "tension":
        factor = 80.0
        count_pass = None
    else:
        raise ValueError("force_state must be 'compression' or 'tension'")
    limit = factor * radius
    spacing_pass = spacing <= limit
    overall = spacing_pass and (count_pass is not False)
    return {
        "force_state": force_state,
        "maximum_spacing_mm": limit,
        "spacing_pass": spacing_pass,
        "intermediate_connection_count": intermediate_connection_count,
        "intermediate_connection_count_pass": count_pass,
        "pass": overall,
    }


def fictitious_shear_force_n(
    axial_force_n: float,
    elastic_modulus_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    stability_coefficient_phi: float,
) -> float:
    """
    Summary:
        Calculate the constant fictitious transverse force from equation (18).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.7
        Annex: None
        Equation/Table: Equation (18)
        Audit ID: SP16-EQ-018
        Normative status: normative

    Mathematical form:
        Q_fic = 7.15e-6 (2330 - E/R_y) N / phi.

    Parameters:
        axial_force_n:
            Type: float
            Unit: N
            Meaning: Longitudinal compression force N in the built-up member.
            Valid range: >= 0
            Source: structural analysis
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Elastic modulus E.
            Valid range: > 0
            Source: material data
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0 and E/R_y <= 2330
            Source: clause 6.1
        stability_coefficient_phi:
            Type: float
            Unit: dimensionless
            Meaning: Central-compression stability coefficient for type b in the connector plane.
            Valid range: 0 < phi <= 1
            Source: equations (8)-(9)

    Returns:
        Type: float
        Unit: N
        Meaning: Fictitious transverse force Q_fic, constant along the member.

    Assumptions:
        - E and R_y use identical stress units.
        - phi corresponds to the plane of the battens or lattice.

    Sign convention:
        - axial_force_n is a non-negative compression magnitude.

    Unit convention:
        - E and R_y use N/mm2 and force uses N.

    Applicability:
        - Connector design for compressed built-up members under clause 7.2.7.

    Limitations:
        - A negative bracket is rejected as a unit or applicability error rather than converted to a negative design force.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is invalid or E/R_y exceeds 2330.

    Examples:
        >>> round(fictitious_shear_force_n(1000000, 206000, 355, 0.8), 3)
        15637.192

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_18_fictitious_shear
        Validation cases:
            - BUILTUP-EQ-018

    Implementation notes:
        - The numerical constant is transcribed without hidden unit conversion.
        - Defaults must be explicit in the input configuration.
    """
    force = _nonnegative(axial_force_n, "axial_force_n")
    elastic = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    resistance = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    phi = _positive(stability_coefficient_phi, "stability_coefficient_phi")
    if phi > 1.0:
        raise ValueError("stability_coefficient_phi must not exceed 1")
    bracket = 2330.0 - elastic / resistance
    if bracket < 0.0:
        raise ValueError("equation (18) requires 2330 - E/R_y to be non-negative; verify units and applicability")
    return 7.15e-6 * bracket * force / phi


def distribute_fictitious_shear(
    fictitious_shear_n: float,
    distribution_mode: str,
    connector_system_count: int,
) -> dict[str, Any]:
    """
    Summary:
        Distribute equation (18) force among battens, lattice systems, or a solid sheet according to clause 7.2.7.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.7
        Annex: None
        Equation/Table: Post-equation (18) distribution rules
        Audit ID: SP16-PROC-7.2.7-SHEAR-DISTRIBUTION
        Normative status: normative

    Mathematical form:
        connectors_only: Q/system_count; solid_sheet_and_connectors: Q/2 to sheet and Q/(2 system_count) to each system; three_sided: 0.8Q per face.

    Parameters:
        fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Total fictitious transverse force Q_fic.
            Valid range: >= 0
            Source: equation (18)
        distribution_mode:
            Type: str
            Unit: categorical
            Meaning: Detailing arrangement.
            Valid range: connectors_only | solid_sheet_and_connectors | equilateral_three_sided
            Source: built-up member configuration
        connector_system_count:
            Type: int
            Unit: systems
            Meaning: Number of connector systems in the checked orientation; ignored for the fixed three-sided rule.
            Valid range: >= 1
            Source: detailing

    Returns:
        Type: dict[str, Any]
        Unit: N and counts
        Meaning: Force assigned to each connector system and, where applicable, the solid sheet.

    Assumptions:
        - connector_system_count includes only systems participating in the checked plane.

    Sign convention:
        - Forces are non-negative magnitudes.

    Unit convention:
        - All force outputs use N.

    Applicability:
        - Distribution rules listed immediately after equation (18).

    Limitations:
        - The three-sided 0.8Q-per-face rule is returned as printed even though the sum over three faces exceeds Q.

    Raises:
        TypeError: Inputs have invalid types.
        ValueError: Mode or numerical inputs are invalid.

    Examples:
        >>> distribute_fictitious_shear(1000, "connectors_only", 2)["per_connector_system_force_n"]
        500.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_fictitious_shear_distribution
        Validation cases:
            - BUILTUP-PROC-7.2.7-DISTRIBUTION

    Implementation notes:
        - No equilibrium reinterpretation is applied to the printed 0.8 rule.
        - Defaults must be explicit in the input configuration.
    """
    force = _nonnegative(fictitious_shear_n, "fictitious_shear_n")
    count = _positive_integer(connector_system_count, "connector_system_count")
    if distribution_mode == "connectors_only":
        per = force / count
        return {
            "distribution_mode": distribution_mode,
            "connector_system_count": count,
            "per_connector_system_force_n": per,
            "solid_sheet_force_n": 0.0,
            "total_assigned_force_n": per * count,
        }
    if distribution_mode == "solid_sheet_and_connectors":
        per = 0.5 * force / count
        return {
            "distribution_mode": distribution_mode,
            "connector_system_count": count,
            "per_connector_system_force_n": per,
            "solid_sheet_force_n": 0.5 * force,
            "total_assigned_force_n": per * count + 0.5 * force,
        }
    if distribution_mode == "equilateral_three_sided":
        per = 0.8 * force
        return {
            "distribution_mode": distribution_mode,
            "connector_system_count": 3,
            "per_connector_system_force_n": per,
            "solid_sheet_force_n": 0.0,
            "total_assigned_force_n": 3.0 * per,
        }
    raise ValueError(
        "distribution_mode must be 'connectors_only', 'solid_sheet_and_connectors', or 'equilateral_three_sided'"
    )


def batten_shear_force_n(
    one_face_fictitious_shear_n: float,
    batten_pitch_mm: float,
    branch_axis_spacing_mm: float,
) -> float:
    """
    Summary:
        Calculate the shear force acting on one batten from equation (19).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.8
        Annex: None
        Equation/Table: Equation (19)
        Audit ID: SP16-EQ-019
        Normative status: normative

    Mathematical form:
        F_s = Q_s l_b / b.

    Parameters:
        one_face_fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Fictitious shear Q_s assigned to battens in one face.
            Valid range: >= 0
            Source: clause 7.2.7 distribution
        batten_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Distance l_b between battens.
            Valid range: > 0
            Source: Figure 4 geometry
        branch_axis_spacing_mm:
            Type: float
            Unit: mm
            Meaning: Distance b between branch axes.
            Valid range: > 0
            Source: Figure 4 geometry

    Returns:
        Type: float
        Unit: N
        Meaning: Batten shear force F_s.

    Assumptions:
        - Q_s is the force for one face, not total Q_fic before distribution.

    Sign convention:
        - Force is returned as a non-negative design magnitude.

    Unit convention:
        - Both geometric inputs use mm, so their ratio is dimensionless.

    Applicability:
        - Batten and batten-connection design as a Vierendeel-type panel.

    Limitations:
        - The function does not check batten strength or connection capacity.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is outside its valid range.

    Examples:
        >>> batten_shear_force_n(1000, 800, 400)
        2000.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_19_batten_shear
        Validation cases:
            - BUILTUP-EQ-019

    Implementation notes:
        - Input naming distinguishes Q_s from total Q_fic.
        - Defaults must be explicit in the input configuration.
    """
    qs = _nonnegative(one_face_fictitious_shear_n, "one_face_fictitious_shear_n")
    pitch = _positive(batten_pitch_mm, "batten_pitch_mm")
    b = _positive(branch_axis_spacing_mm, "branch_axis_spacing_mm")
    return qs * pitch / b


def batten_bending_moment_n_mm(one_face_fictitious_shear_n: float, batten_pitch_mm: float) -> float:
    """
    Summary:
        Calculate the in-plane batten bending moment from equation (20).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.8
        Annex: None
        Equation/Table: Equation (20)
        Audit ID: SP16-EQ-020
        Normative status: normative

    Mathematical form:
        M_s = Q_s l_b / 2.

    Parameters:
        one_face_fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Fictitious shear Q_s assigned to one face.
            Valid range: >= 0
            Source: clause 7.2.7 distribution
        batten_pitch_mm:
            Type: float
            Unit: mm
            Meaning: Distance l_b between battens.
            Valid range: > 0
            Source: Figure 4 geometry

    Returns:
        Type: float
        Unit: N*mm
        Meaning: Batten bending moment M_s.

    Assumptions:
        - Q_s is constant over the considered panel.

    Sign convention:
        - The returned moment is a non-negative design magnitude.

    Unit convention:
        - N multiplied by mm gives N*mm.

    Applicability:
        - Batten and batten-connection design under clause 7.2.8.

    Limitations:
        - No interaction or connection resistance check is included.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is outside its valid range.

    Examples:
        >>> batten_bending_moment_n_mm(1000, 800)
        400000.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_20_batten_moment
        Validation cases:
            - BUILTUP-EQ-020

    Implementation notes:
        - The result unit is explicit in the function name.
        - Defaults must be explicit in the input configuration.
    """
    qs = _nonnegative(one_face_fictitious_shear_n, "one_face_fictitious_shear_n")
    pitch = _positive(batten_pitch_mm, "batten_pitch_mm")
    return qs * pitch / 2.0


def lattice_diagonal_force_n(
    one_plane_fictitious_shear_n: float,
    diagonal_length_d_mm: float,
    branch_axis_spacing_b_mm: float,
    lattice_force_coefficient_alpha_1: float,
) -> float:
    """
    Summary:
        Calculate the lattice diagonal force from equation (21).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.9
        Annex: None
        Equation/Table: Equation (21), Figure 3
        Audit ID: SP16-EQ-021
        Normative status: normative

    Mathematical form:
        N_d = alpha_1 Q_s d / b.

    Parameters:
        one_plane_fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Fictitious shear Q_s assigned to one lattice plane.
            Valid range: >= 0
            Source: clause 7.2.7 distribution
        diagonal_length_d_mm:
            Type: float
            Unit: mm
            Meaning: Dimension d from Figure 3.
            Valid range: > 0
            Source: lattice geometry
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Distance b from Figure 3.
            Valid range: > 0
            Source: lattice geometry
        lattice_force_coefficient_alpha_1:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient alpha_1: 1.0 for Figure 3 a,b and 0.5 for Figure 3 v.
            Valid range: 0.5 | 1.0
            Source: clause 7.2.9

    Returns:
        Type: float
        Unit: N
        Meaning: Axial force N_d in a diagonal.

    Assumptions:
        - The caller selects alpha_1 from an explicitly covered Figure 3 arrangement.

    Sign convention:
        - The result is a non-negative design-force magnitude.

    Unit convention:
        - d and b use the same unit, here mm.

    Applicability:
        - Figure 3 a, b, or v lattice arrangements.

    Limitations:
        - Clause 7.2.9 does not explicitly state alpha_1 for Figure 3 g; no value is inferred for that arrangement.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input or alpha_1 is invalid.

    Examples:
        >>> lattice_diagonal_force_n(1000, 600, 400, 0.5)
        750.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_21_lattice_diagonal_force
        Validation cases:
            - BUILTUP-EQ-021

    Implementation notes:
        - alpha_1 is explicit to avoid silently assigning an unstated value to Figure 3 g.
        - Defaults must be explicit in the input configuration.
    """
    qs = _nonnegative(one_plane_fictitious_shear_n, "one_plane_fictitious_shear_n")
    d = _positive(diagonal_length_d_mm, "diagonal_length_d_mm")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    alpha1 = _positive(lattice_force_coefficient_alpha_1, "lattice_force_coefficient_alpha_1")
    if alpha1 not in {0.5, 1.0}:
        raise ValueError("lattice_force_coefficient_alpha_1 must be 0.5 or 1.0")
    return alpha1 * qs * d / b


def cross_lattice_alpha_2(
    diagonal_length_d_mm: float,
    panel_length_mm: float,
    branch_axis_spacing_b_mm: float,
) -> float:
    """
    Summary:
        Calculate the unnumbered alpha_2 coefficient used by equation (22).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.9
        Annex: None
        Equation/Table: Coefficient below equation (22)
        Audit ID: SP16-EQ-022
        Normative status: normative

    Mathematical form:
        alpha_2 = d l_b^2 / (2 b^3 + d^3).

    Parameters:
        diagonal_length_d_mm:
            Type: float
            Unit: mm
            Meaning: Dimension d from Figure 3.
            Valid range: > 0
            Source: lattice geometry
        panel_length_mm:
            Type: float
            Unit: mm
            Meaning: Dimension l_b from Figure 3.
            Valid range: > 0
            Source: lattice geometry
        branch_axis_spacing_b_mm:
            Type: float
            Unit: mm
            Meaning: Dimension b from Figure 3.
            Valid range: > 0
            Source: lattice geometry

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Coefficient alpha_2.

    Assumptions:
        - Dimensions correspond to the cross lattice with struts in Figure 3 g.

    Sign convention:
        - Dimensions are positive magnitudes.

    Unit convention:
        - All dimensions use the same unit, here mm.

    Applicability:
        - Additional diagonal force in Figure 3 g.

    Limitations:
        - The function does not check geometric compatibility among d, l_b, and b.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is non-positive or non-finite.

    Examples:
        >>> cross_lattice_alpha_2(600, 800, 400) > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_22_alpha_2_and_additional_force
        Validation cases:
            - BUILTUP-EQ-022-ALPHA2

    Implementation notes:
        - The coefficient is dimensionless when consistent length units are used.
        - Defaults must be explicit in the input configuration.
    """
    d = _positive(diagonal_length_d_mm, "diagonal_length_d_mm")
    panel = _positive(panel_length_mm, "panel_length_mm")
    b = _positive(branch_axis_spacing_b_mm, "branch_axis_spacing_b_mm")
    return d * panel**2 / (2.0 * b**3 + d**3)


def cross_lattice_additional_diagonal_force_n(
    one_branch_force_n: float,
    one_diagonal_area_mm2: float,
    one_branch_area_mm2: float,
    coefficient_alpha_2: float,
) -> float:
    """
    Summary:
        Calculate the additional diagonal force caused by branch shortening from equation (22).

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.9
        Annex: None
        Equation/Table: Equation (22)
        Audit ID: SP16-EQ-022
        Normative status: normative

    Mathematical form:
        N_ad = alpha_2 N_b A_d / A_b.

    Parameters:
        one_branch_force_n:
            Type: float
            Unit: N
            Meaning: Force N_b in one branch.
            Valid range: >= 0
            Source: member-force distribution
        one_diagonal_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_d of one diagonal.
            Valid range: > 0
            Source: lattice section
        one_branch_area_mm2:
            Type: float
            Unit: mm2
            Meaning: Area A_b of one branch.
            Valid range: > 0
            Source: branch section
        coefficient_alpha_2:
            Type: float
            Unit: dimensionless
            Meaning: Coefficient alpha_2 from the expression below equation (22).
            Valid range: >= 0
            Source: cross_lattice_alpha_2

    Returns:
        Type: float
        Unit: N
        Meaning: Additional force N_ad in each diagonal.

    Assumptions:
        - The arrangement is the cross lattice with struts in Figure 3 g.

    Sign convention:
        - Forces are returned as non-negative magnitudes.

    Unit convention:
        - Areas use mm2 and cancel as a ratio.

    Applicability:
        - Additional diagonal-force component required by clause 7.2.9.

    Limitations:
        - This function returns only the additional component; combination with equation (21) is an external design step.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is outside its valid range.

    Examples:
        >>> cross_lattice_additional_diagonal_force_n(200000, 500, 2500, 0.5)
        20000.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_equation_22_alpha_2_and_additional_force
        Validation cases:
            - BUILTUP-EQ-022

    Implementation notes:
        - Base and additional diagonal forces remain separate for transparent load combination.
        - Defaults must be explicit in the input configuration.
    """
    nb = _nonnegative(one_branch_force_n, "one_branch_force_n")
    ad = _positive(one_diagonal_area_mm2, "one_diagonal_area_mm2")
    ab = _positive(one_branch_area_mm2, "one_branch_area_mm2")
    alpha2 = _nonnegative(coefficient_alpha_2, "coefficient_alpha_2")
    return alpha2 * nb * ad / ab


def reduced_length_brace_design_force_n(fictitious_shear_n: float) -> float:
    """
    Summary:
        Return the clause 7.2.10 design force for a brace that reduces the effective length of a compressed member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.10
        Annex: None
        Equation/Table: Reference to equation (18)
        Audit ID: SP16-PROC-7.2.10-RESTRAINT-FORCE
        Normative status: normative

    Mathematical form:
        brace design force = Q_fic of the restrained compressed member.

    Parameters:
        fictitious_shear_n:
            Type: float
            Unit: N
            Meaning: Fictitious transverse force of the main compressed member.
            Valid range: >= 0
            Source: equation (18)

    Returns:
        Type: float
        Unit: N
        Meaning: Required brace design-force magnitude.

    Assumptions:
        - The brace is intended specifically to reduce the effective length of the compressed element.

    Sign convention:
        - Force is a non-negative magnitude.

    Unit convention:
        - Force uses N.

    Applicability:
        - First paragraph of clause 7.2.10.

    Limitations:
        - Brace strength, stability, and connection design are not performed.

    Raises:
        TypeError: The input is not real.
        ValueError: The input is negative or non-finite.

    Examples:
        >>> reduced_length_brace_design_force_n(12000)
        12000.0

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_clause_7_2_10_restraint_forces
        Validation cases:
            - BUILTUP-PROC-7.2.10-BRACE

    Implementation notes:
        - The identity operation is kept as a named audited procedure.
        - Defaults must be explicit in the input configuration.
    """
    return _nonnegative(fictitious_shear_n, "fictitious_shear_n")


def column_branch_spacer_fictitious_shear_n(
    branch_force_1_n: float,
    branch_force_2_n: float,
    elastic_modulus_n_mm2: float,
    design_yield_resistance_n_mm2: float,
    stability_coefficient_phi: float,
) -> float:
    """
    Summary:
        Calculate clause 7.2.10 spacer force using equation (18) with the sum of two column-branch forces.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 7.2.10
        Annex: None
        Equation/Table: Equation (18) with N=N_b1+N_b2
        Audit ID: SP16-PROC-7.2.10-COLUMN-SPACER
        Normative status: normative

    Mathematical form:
        N = N_b1 + N_b2, followed by equation (18).

    Parameters:
        branch_force_1_n:
            Type: float
            Unit: N
            Meaning: Longitudinal force in the first connected column branch.
            Valid range: >= 0
            Source: structural analysis
        branch_force_2_n:
            Type: float
            Unit: N
            Meaning: Longitudinal force in the second connected column branch.
            Valid range: >= 0
            Source: structural analysis
        elastic_modulus_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Elastic modulus E.
            Valid range: > 0
            Source: material data
        design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design yield resistance R_y.
            Valid range: > 0
            Source: clause 6.1
        stability_coefficient_phi:
            Type: float
            Unit: dimensionless
            Meaning: Stability coefficient used by equation (18).
            Valid range: 0 < phi <= 1
            Source: member stability calculation

    Returns:
        Type: float
        Unit: N
        Meaning: Fictitious transverse force for the spacer.

    Assumptions:
        - Both supplied branch forces act in the combination governing the spacer.

    Sign convention:
        - Branch forces are non-negative compression magnitudes.

    Unit convention:
        - Forces use N and stresses use N/mm2.

    Applicability:
        - Column-branch spacers described in the second paragraph of clause 7.2.10.

    Limitations:
        - Crane-load applicability and complete spacer design remain external.

    Raises:
        TypeError: A numerical input is not real.
        ValueError: An input is outside its valid range.

    Examples:
        >>> column_branch_spacer_fictitious_shear_n(400000, 600000, 206000, 355, 0.8) > 0
        True

    Tests:
        Unit tests:
            - tests/test_built_up_axial_members.py::test_clause_7_2_10_restraint_forces
        Validation cases:
            - BUILTUP-PROC-7.2.10-SPACER

    Implementation notes:
        - The force summation is explicit before calling equation (18).
        - Defaults must be explicit in the input configuration.
    """
    force_1 = _nonnegative(branch_force_1_n, "branch_force_1_n")
    force_2 = _nonnegative(branch_force_2_n, "branch_force_2_n")
    return fictitious_shear_force_n(
        force_1 + force_2,
        elastic_modulus_n_mm2,
        design_yield_resistance_n_mm2,
        stability_coefficient_phi,
    )
