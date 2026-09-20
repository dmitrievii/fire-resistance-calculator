"""Clause 6 material and connection resistance calculations for СП 16.13330.2017."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))


_TABLE_2 = _load_json("table_2_resistance_formulas.json")
_TABLE_3 = _load_json("table_3_material_safety_factors.json")
_TABLE_4 = _load_json("table_4_weld_resistance_formulas.json")
_TABLE_5 = _load_json("table_5_bolt_resistance_factors.json")
_B1_PHYSICAL = _load_json("annex_b1_physical_properties.json")
_V3_STRENGTH = _load_json("annex_v3_strength_resistances.json")
_V4_STRENGTH = _load_json("annex_v4_parallel_flange_i_strength_resistances.json")
_V5_STRENGTH = _load_json("annex_v5_shaped_strength_resistances.json")
_GAMMA_U = _load_json("clause_4_3_2_gamma_u.json")

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-6.2",
    "SP16-PROC-6.4-DISSIMILAR",
    "SP16-PROC-6.4-GAMMA-WM",
    "SP16-PROC-6.9",
)


def _require_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _require_positive(value: float, name: str) -> float:
    value = _require_nonnegative(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _table_2_resistance(input_resistance_n_mm2: float, material_safety_factor: float, key: str) -> float:
    resistance = _require_nonnegative(input_resistance_n_mm2, "input_resistance_n_mm2")
    gamma_m = _require_positive(material_safety_factor, "material_safety_factor")
    coefficient = float(_TABLE_2["formulas"][key]["coefficient"])
    return coefficient * resistance / gamma_m

def design_yield_resistance_n_mm2(normative_yield_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate design resistance for tension, compression, and bending by yield strength.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Ry = Ryn/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Ry = Ryn / gamma_m

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance Ryn.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design yield resistance Ry.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Rolled products, cold-formed sections, and tubes covered by clause 6.1.

    Limitations:
        - Does not select Ryn from Annex B/V tables.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_yield_resistance_n_mm2(355.0, 1.05)
        338.0952380952381

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_design_yield_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_yield_resistance_n_mm2, material_safety_factor, "design_yield_resistance")

def design_ultimate_resistance_n_mm2(normative_ultimate_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate design resistance for tension, compression, and bending by ultimate strength.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Ru = Run/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Ru = Run / gamma_m

    Parameters:
        normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance Run.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design ultimate resistance Ru.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Rolled products, cold-formed sections, and tubes covered by clause 6.1.

    Limitations:
        - Does not select Run from Annex B/V tables.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_ultimate_resistance_n_mm2(510.0, 1.05)
        485.7142857142857

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_design_ultimate_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_ultimate_resistance_n_mm2, material_safety_factor, "design_ultimate_resistance")

def design_shear_resistance_n_mm2(normative_yield_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate design shear resistance of rolled products and tubes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Rs = 0.58*Ryn/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Rs = 0.58 * Ryn / gamma_m

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance Ryn.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design shear resistance Rs.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Shear resistance under Table 2.

    Limitations:
        - No temperature or fatigue reduction is included.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_shear_resistance_n_mm2(355.0, 1.05)
        196.09523809523807

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_design_shear_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_yield_resistance_n_mm2, material_safety_factor, "design_shear_resistance")

def design_end_bearing_resistance_n_mm2(normative_ultimate_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate design resistance for bearing of a fitted end surface.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Rp = Run/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Rp = Run / gamma_m

    Parameters:
        normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance Run.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design end-bearing resistance Rp.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Fitted end surfaces as stated in Table 2.

    Limitations:
        - Geometric fit verification is outside this function.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_end_bearing_resistance_n_mm2(510.0, 1.05)
        485.7142857142857

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_end_bearing_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_ultimate_resistance_n_mm2, material_safety_factor, "design_end_bearing_resistance")

def design_pin_local_bearing_resistance_n_mm2(normative_ultimate_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate local bearing resistance in cylindrical hinges or pins under close contact.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Rlp = 0.5*Run/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Rlp = 0.5 * Run / gamma_m

    Parameters:
        normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance Run.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design local pin-bearing resistance Rlp.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Cylindrical hinges/pins with close contact.

    Limitations:
        - Contact geometry and actual bearing stress are outside this function.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_pin_local_bearing_resistance_n_mm2(510.0, 1.05)
        242.85714285714286

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_pin_bearing_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_ultimate_resistance_n_mm2, material_safety_factor, "design_pin_local_bearing_resistance")

def design_roller_diametral_compression_resistance_n_mm2(normative_ultimate_resistance_n_mm2: float, material_safety_factor: float) -> float:
    """
    Summary:
        Calculate diametral compression resistance of rollers under free contact.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 2, Rcd = 0.025*Run/gamma_m
        Audit ID: SP16-TBL-2
        Normative status: normative

    Mathematical form:
        Rcd = 0.025 * Run / gamma_m

    Parameters:
        normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance Run.
            Valid range: >= 0
            Source: standard annex/input
        material_safety_factor:
            Type: float
            Unit: dimensionless
            Meaning: Material safety factor gamma_m.
            Valid range: > 0
            Source: Table 3 or explicit audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Design roller diametral-compression resistance Rcd.

    Assumptions:
        - The normative resistance supplied by the caller is applicable to the selected product and thickness.
        - The material safety factor is selected according to Table 3 or supplied from an audited source.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Free-contact rollers in structures with limited mobility.

    Limitations:
        - Contact mechanics beyond the tabulated resistance is outside this function.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> design_roller_diametral_compression_resistance_n_mm2(510.0, 1.05)
        12.142857142857142

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_2_roller_compression_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _table_2_resistance(normative_ultimate_resistance_n_mm2, material_safety_factor, "design_roller_diametral_compression_resistance")

def material_safety_factor(control_category: str) -> float:
    """
    Summary:
        Look up the material safety factor gamma_m from an explicitly selected Table 3 category.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.1
        Annex: None
        Equation/Table: Table 3
        Audit ID: SP16-TBL-3
        Normative status: normative

    Mathematical form:
        gamma_m = lookup(control_category)

    Parameters:
        control_category:
            Type: str
            Unit: dimensionless
            Meaning: Explicit Table 3 product/control category key.
            Valid range: One of the keys documented in data/table_3_material_safety_factors.json
            Source: user input after engineering classification

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Material safety factor gamma_m.

    Assumptions:
        - The engineer has already classified the product/control condition.
        - The category key is not inferred from steel grade alone.

    Sign convention:
        - The factor is positive.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Products and control conditions explicitly covered by Table 3.

    Limitations:
        - Does not infer category from incomplete metadata and does not verify product certificates.

    Raises:
        TypeError: The category is not a string.
        ValueError: The category is unknown.

    Examples:
        >>> material_safety_factor("other_conforming")
        1.05

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_3_exists_lookup_and_consistency
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(control_category, str):
        raise TypeError("control_category must be a string")
    try:
        return float(_TABLE_3["categories"][control_category])
    except KeyError as exc:
        allowed = ", ".join(sorted(_TABLE_3["categories"]))
        raise ValueError(f"Unknown control_category {control_category!r}; allowed: {allowed}") from exc

def cold_formed_section_design_resistance_n_mm2(source_sheet_design_resistance_n_mm2: float) -> float:
    """
    Summary:
        Adopt the design resistance of a cold-formed section equal to that of its source sheet.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.2
        Annex: None
        Equation/Table: Clause procedure
        Audit ID: SP16-PROC-6.2
        Normative status: normative

    Mathematical form:
        R_cold_formed = R_source_sheet

    Parameters:
        source_sheet_design_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Audited design resistance of the sheet used to form the section.
            Valid range: >= 0
            Source: calculated or tabulated source-sheet resistance

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Adopted design resistance for the cold-formed section.

    Assumptions:
        - The section is made from the referenced sheet product.
        - No forming-induced modification is introduced by clause 6.2.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Cold-formed sections addressed by clause 6.2.

    Limitations:
        - Does not determine the source-sheet value or check local buckling.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> cold_formed_section_design_resistance_n_mm2(338.0)
        338.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_clause_6_2_identity_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _require_nonnegative(source_sheet_design_resistance_n_mm2, "source_sheet_design_resistance_n_mm2")

def butt_weld_design_yield_resistance_with_ndt_n_mm2(base_design_yield_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate butt-weld design yield resistance when weld quality is controlled by nondestructive methods.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rwy = Ry
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rwy = Ry

    Parameters:
        base_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Base-metal design yield resistance Ry.
            Valid range: >= 0
            Source: Table 2 or Annex B/V data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Butt-weld design yield resistance Rwy.

    Assumptions:
        - The specified welding process and nondestructive quality control satisfy Table 4.
        - For dissimilar steels the lower applicable resistance is used separately.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Butt welds with nondestructive quality control.

    Limitations:
        - Does not verify weld procedure qualification or inspection records.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> butt_weld_design_yield_resistance_with_ndt_n_mm2(338.0)
        338.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_butt_weld_yield_with_ndt
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _require_nonnegative(base_design_yield_resistance_n_mm2, "base_design_yield_resistance_n_mm2")

def butt_weld_design_ultimate_resistance_with_ndt_n_mm2(base_design_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate butt-weld design ultimate resistance when weld quality is controlled by nondestructive methods.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rwu = Ru
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rwu = Ru

    Parameters:
        base_design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Base-metal design ultimate resistance Ru.
            Valid range: >= 0
            Source: Table 2 or Annex B/V data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Butt-weld design ultimate resistance Rwu.

    Assumptions:
        - The specified welding process and nondestructive quality control satisfy Table 4.
        - For dissimilar steels the lower applicable resistance is used separately.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Butt welds with nondestructive quality control.

    Limitations:
        - Does not verify inspection scope or acceptance criteria.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> butt_weld_design_ultimate_resistance_with_ndt_n_mm2(486.0)
        486.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_butt_weld_ultimate_with_ndt
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _require_nonnegative(base_design_ultimate_resistance_n_mm2, "base_design_ultimate_resistance_n_mm2")

def butt_weld_design_yield_resistance_without_ndt_n_mm2(base_design_yield_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate butt-weld design yield resistance without the Table 4 nondestructive quality-control condition.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rwy = 0.85*Ry
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rwy = 0.85 * Ry

    Parameters:
        base_design_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Base-metal design yield resistance Ry.
            Valid range: >= 0
            Source: Table 2 or Annex B/V data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Reduced butt-weld design yield resistance Rwy.

    Assumptions:
        - The weld is in the Table 4 row for tension/bending without the stated nondestructive quality-control condition.
        - The supplied Ry is already a design resistance.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Butt-weld tension and bending case stated in Table 4.

    Limitations:
        - Does not determine whether a particular inspection regime qualifies as NDT control.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> butt_weld_design_yield_resistance_without_ndt_n_mm2(338.0)
        287.3

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_butt_weld_yield_without_ndt
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(base_design_yield_resistance_n_mm2, "base_design_yield_resistance_n_mm2")
    return 0.85 * value

def butt_weld_design_shear_resistance_n_mm2(base_design_shear_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate butt-weld design shear resistance.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rws = Rs
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rws = Rs

    Parameters:
        base_design_shear_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Base-metal design shear resistance Rs.
            Valid range: >= 0
            Source: Table 2

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Butt-weld design shear resistance Rws.

    Assumptions:
        - The weld and loading correspond to the Table 4 shear row.
        - The supplied Rs is already a design resistance.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Butt welds in shear under clause 6.4.

    Limitations:
        - Does not calculate weld stresses or effective throat area.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> butt_weld_design_shear_resistance_n_mm2(196.0)
        196.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_butt_weld_shear
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return _require_nonnegative(base_design_shear_resistance_n_mm2, "base_design_shear_resistance_n_mm2")

def weld_metal_safety_factor(normative_weld_metal_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Select the weld-metal safety factor gamma_wm at the explicit Table 4 boundary ranges.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4 note
        Audit ID: SP16-PROC-6.4-GAMMA-WM
        Normative status: normative

    Mathematical form:
        gamma_wm = 1.25 for Rwun <= 490; 1.35 for Rwun >= 590

    Parameters:
        normative_weld_metal_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance of weld metal Rwun.
            Valid range: >= 0
            Source: Table G.2 or explicit audited input

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Weld-metal safety factor gamma_wm.

    Assumptions:
        - No interpolation is permitted unless another audited source explicitly supplies it.
        - The resistance is expressed in N/mm2.

    Sign convention:
        - The factor is positive.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Explicit endpoint ranges stated in the note to Table 4.

    Limitations:
        - The interval 490 < Rwun < 590 N/mm2 is not specified in the supplied Table 4 and therefore raises an error.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative or lies in the unspecified interval.

    Examples:
        >>> weld_metal_safety_factor(490.0)
        1.25

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_weld_metal_safety_factor_boundaries_and_gap
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(normative_weld_metal_ultimate_resistance_n_mm2, "normative_weld_metal_ultimate_resistance_n_mm2")
    if value <= 490.0:
        return 1.25
    if value >= 590.0:
        return 1.35
    raise ValueError("Table 4 does not specify gamma_wm for 490 < Rwun < 590 N/mm2; provide an explicit audited factor to the fillet-weld function")

def fillet_weld_metal_design_shear_resistance_n_mm2(normative_weld_metal_ultimate_resistance_n_mm2: float, weld_metal_safety_factor_value: float) -> float:
    """
    Summary:
        Calculate fillet-weld design shear resistance governed by weld metal.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rwf = 0.55*Rwun/gamma_wm
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rwf = 0.55 * Rwun / gamma_wm

    Parameters:
        normative_weld_metal_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance of weld metal Rwun.
            Valid range: >= 0
            Source: Table G.2 or explicit audited input
        weld_metal_safety_factor_value:
            Type: float
            Unit: dimensionless
            Meaning: Explicit weld-metal safety factor gamma_wm.
            Valid range: > 0
            Source: Table 4 note or explicit audited source

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Fillet-weld metal design shear resistance Rwf.

    Assumptions:
        - The caller supplies a valid gamma_wm.
        - The selected weld material is applicable to the joint.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Fillet welds governed by weld metal.

    Limitations:
        - Does not select welding consumables or check effective weld length.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is outside its valid range.

    Examples:
        >>> fillet_weld_metal_design_shear_resistance_n_mm2(490.0, 1.25)
        215.60000000000002

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_fillet_weld_metal_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    resistance = _require_nonnegative(normative_weld_metal_ultimate_resistance_n_mm2, "normative_weld_metal_ultimate_resistance_n_mm2")
    gamma_wm = _require_positive(weld_metal_safety_factor_value, "weld_metal_safety_factor_value")
    return 0.55 * resistance / gamma_wm

def fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(base_normative_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate fillet-weld design shear resistance governed by the fusion boundary.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Table 4, Rwz = 0.45*Run
        Audit ID: SP16-TBL-4
        Normative status: normative

    Mathematical form:
        Rwz = 0.45 * Run

    Parameters:
        base_normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance of base metal Run.
            Valid range: >= 0
            Source: standard annex/input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Fusion-boundary design shear resistance Rwz.

    Assumptions:
        - The base-metal normative ultimate resistance is applicable to the joint.
        - The weld is checked under the fusion-boundary model of Table 4.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Fillet welds governed by the fusion boundary.

    Limitations:
        - Does not calculate weld utilization.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> fillet_weld_fusion_boundary_design_shear_resistance_n_mm2(510.0)
        229.5

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_4_fusion_boundary_normal_boundary_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(base_normative_ultimate_resistance_n_mm2, "base_normative_ultimate_resistance_n_mm2")
    return 0.45 * value

def dissimilar_steel_butt_weld_governing_resistance_n_mm2(first_steel_resistance_n_mm2: float, second_steel_resistance_n_mm2: float) -> float:
    """
    Summary:
        Select the lower applicable butt-weld resistance for elements made from steels with different normative resistances.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.4
        Annex: None
        Equation/Table: Clause procedure after Table 4
        Audit ID: SP16-PROC-6.4-DISSIMILAR
        Normative status: normative

    Mathematical form:
        R_governing = min(R_first, R_second)

    Parameters:
        first_steel_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Applicable resistance for the first steel.
            Valid range: >= 0
            Source: calculated/audited input
        second_steel_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Applicable resistance for the second steel.
            Valid range: >= 0
            Source: calculated/audited input

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Lower governing resistance.

    Assumptions:
        - Both inputs represent the same resistance type and limit state.
        - Both values are already applicable design or normative values as required by the caller.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Butt welds joining steels with different resistance values.

    Limitations:
        - Does not reconcile mismatched resistance types or units.

    Raises:
        TypeError: An input is not numeric.
        ValueError: An input is negative.

    Examples:
        >>> dissimilar_steel_butt_weld_governing_resistance_n_mm2(338.0, 315.0)
        315.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_clause_6_4_dissimilar_steel_minimum
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    first = _require_nonnegative(first_steel_resistance_n_mm2, "first_steel_resistance_n_mm2")
    second = _require_nonnegative(second_steel_resistance_n_mm2, "second_steel_resistance_n_mm2")
    return min(first, second)

def bolt_shear_design_resistance_n_mm2(normative_bolt_ultimate_resistance_n_mm2: float, bolt_strength_class: str) -> float:
    """
    Summary:
        Calculate one-bolt design shear resistance from bolt class and normative bolt ultimate resistance.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.5
        Annex: None
        Equation/Table: Table 5, Rbs
        Audit ID: SP16-TBL-5
        Normative status: normative

    Mathematical form:
        Rbs = k_bs(class) * Rbun

    Parameters:
        normative_bolt_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance of bolt steel Rbun.
            Valid range: >= 0
            Source: Table G.5 or explicit audited input
        bolt_strength_class:
            Type: str
            Unit: dimensionless
            Meaning: Bolt strength class.
            Valid range: 5.6, 5.8, 8.8, 10.9, or 12.9
            Source: user input/product specification

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: One-bolt design shear resistance Rbs.

    Assumptions:
        - The bolt class is one of the classes listed in Table 5.
        - Rbun is applicable to the bolt product.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - One-bolt shear resistance under clause 6.5.

    Limitations:
        - Does not calculate bolt capacity from area or number of shear planes.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: Resistance is negative or the class is unsupported.

    Examples:
        >>> bolt_shear_design_resistance_n_mm2(800.0, "8.8")
        320.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_5_shear_exists_lookup_and_consistency
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    resistance = _require_nonnegative(normative_bolt_ultimate_resistance_n_mm2, "normative_bolt_ultimate_resistance_n_mm2")
    if not isinstance(bolt_strength_class, str):
        raise TypeError("bolt_strength_class must be a string")
    try:
        factor = float(_TABLE_5["shear_factors_by_strength_class"][bolt_strength_class])
    except KeyError as exc:
        raise ValueError(f"Unsupported bolt strength class: {bolt_strength_class!r}") from exc
    return factor * resistance

def bolt_tension_design_resistance_n_mm2(normative_bolt_ultimate_resistance_n_mm2: float, bolt_strength_class: str) -> float:
    """
    Summary:
        Calculate one-bolt design tension resistance from bolt class and normative bolt ultimate resistance.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.5
        Annex: None
        Equation/Table: Table 5, Rbt
        Audit ID: SP16-TBL-5
        Normative status: normative

    Mathematical form:
        Rbt = k_bt(class) * Rbun

    Parameters:
        normative_bolt_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance of bolt steel Rbun.
            Valid range: >= 0
            Source: Table G.5 or explicit audited input
        bolt_strength_class:
            Type: str
            Unit: dimensionless
            Meaning: Bolt strength class.
            Valid range: 5.6, 5.8, 8.8, 10.9, or 12.9
            Source: user input/product specification

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: One-bolt design tension resistance Rbt.

    Assumptions:
        - The bolt class is one of the classes listed in Table 5.
        - Rbun is applicable to the bolt product.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - One-bolt tension resistance under clause 6.5.

    Limitations:
        - Does not calculate bolt force capacity from tensile area.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: Resistance is negative or the class is unsupported.

    Examples:
        >>> bolt_tension_design_resistance_n_mm2(800.0, "8.8")
        432.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_5_tension_exists_lookup_and_consistency
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    resistance = _require_nonnegative(normative_bolt_ultimate_resistance_n_mm2, "normative_bolt_ultimate_resistance_n_mm2")
    if not isinstance(bolt_strength_class, str):
        raise TypeError("bolt_strength_class must be a string")
    try:
        factor = float(_TABLE_5["tension_factors_by_strength_class"][bolt_strength_class])
    except KeyError as exc:
        raise ValueError(f"Unsupported bolt strength class: {bolt_strength_class!r}") from exc
    return factor * resistance

def connected_element_bearing_design_resistance_n_mm2(base_design_ultimate_resistance_n_mm2: float, bolt_hole_accuracy_class: str, connected_steel_yield_strength_n_mm2: float) -> float:
    """
    Summary:
        Calculate connected-element bearing design resistance for bolt-hole accuracy class A or B.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.5
        Annex: None
        Equation/Table: Table 5, Rbp
        Audit ID: SP16-TBL-5
        Normative status: normative

    Mathematical form:
        Rbp = 1.60*Ru for class A; 1.35*Ru for class B

    Parameters:
        base_design_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Design ultimate resistance Ru of connected steel.
            Valid range: >= 0
            Source: Table 2 or annex data
        bolt_hole_accuracy_class:
            Type: str
            Unit: dimensionless
            Meaning: Bolt-hole accuracy class.
            Valid range: A or B
            Source: user input/detailing specification
        connected_steel_yield_strength_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Yield strength used to verify Table 5 applicability.
            Valid range: 0 to 450 inclusive
            Source: steel product data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Connected-element bearing design resistance Rbp.

    Assumptions:
        - The connected steel yield strength does not exceed 450 N/mm2.
        - The selected accuracy class corresponds to the joint detailing.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Bearing of elements connected by bolts under Table 5.

    Limitations:
        - Not applicable above 450 N/mm2 yield strength; Table G.6 remains outside this release.

    Raises:
        TypeError: An input has the wrong type.
        ValueError: An input is outside the Table 5 applicability domain.

    Examples:
        >>> connected_element_bearing_design_resistance_n_mm2(485.0, "A", 355.0)
        776.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_table_5_bearing_lookup_boundary_and_applicability
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    resistance = _require_nonnegative(base_design_ultimate_resistance_n_mm2, "base_design_ultimate_resistance_n_mm2")
    yield_strength = _require_nonnegative(connected_steel_yield_strength_n_mm2, "connected_steel_yield_strength_n_mm2")
    if yield_strength > 450.0:
        raise ValueError("Table 5 bearing formula is limited to connected steel with yield strength <= 450 N/mm2")
    if not isinstance(bolt_hole_accuracy_class, str):
        raise TypeError("bolt_hole_accuracy_class must be a string")
    try:
        factor = float(_TABLE_5["bearing_factors_by_accuracy_class"][bolt_hole_accuracy_class.upper()])
    except KeyError as exc:
        raise ValueError("bolt_hole_accuracy_class must be A or B") from exc
    return factor * resistance

def foundation_anchor_bolt_tension_design_resistance_n_mm2(normative_yield_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate tensile design resistance of foundation and anchor bolts.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.6
        Annex: None
        Equation/Table: Equation (1), Rba = 0.8*Ryn
        Audit ID: SP16-EQ-001
        Normative status: normative

    Mathematical form:
        Rba = 0.8 * Ryn

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance Ryn of the bolt steel.
            Valid range: >= 0
            Source: steel product data/Table G.7 support

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Tensile design resistance Rba.

    Assumptions:
        - Ryn is applicable to the selected foundation or anchor bolt steel.
        - The connection is within clause 6.6.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Foundation and anchor bolts under clause 6.6.

    Limitations:
        - Does not select the bolt steel or table G.7 row.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> foundation_anchor_bolt_tension_design_resistance_n_mm2(355.0)
        284.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_equation_1_normal_zero_and_sign_unit_convention
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2")
    return 0.8 * value

def u_bolt_tension_design_resistance_n_mm2(normative_yield_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate tensile design resistance of U-bolts specified in clause 5.8.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.6
        Annex: None
        Equation/Table: Equation (2), RbU = 0.85*Ryn
        Audit ID: SP16-EQ-002
        Normative status: normative

    Mathematical form:
        RbU = 0.85 * Ryn

    Parameters:
        normative_yield_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative yield resistance Ryn of the U-bolt steel.
            Valid range: >= 0
            Source: steel product data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Tensile design resistance RbU.

    Assumptions:
        - Ryn is applicable to the selected U-bolt steel.
        - The U-bolt is within clause 5.8.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - U-bolts under clauses 5.8 and 6.6.

    Limitations:
        - Does not verify U-bolt geometry or anchorage.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> u_bolt_tension_design_resistance_n_mm2(355.0)
        301.75

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_equation_2_normal_zero_and_sign_unit_convention
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(normative_yield_resistance_n_mm2, "normative_yield_resistance_n_mm2")
    return 0.85 * value

def high_strength_wire_tension_design_resistance_n_mm2(normative_ultimate_resistance_n_mm2: float) -> float:
    """
    Summary:
        Calculate tensile design resistance of high-strength steel wire used in bundles or strands.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.8
        Annex: None
        Equation/Table: Equation (4), Rdh = 0.63*Run
        Audit ID: SP16-EQ-004
        Normative status: normative

    Mathematical form:
        Rdh = 0.63 * Run

    Parameters:
        normative_ultimate_resistance_n_mm2:
            Type: float
            Unit: N/mm2
            Meaning: Normative ultimate resistance Run of high-strength wire.
            Valid range: >= 0
            Source: wire product data

    Returns:
        Type: float
        Unit: N/mm2
        Meaning: Tensile design resistance Rdh.

    Assumptions:
        - Run is applicable to the selected high-strength wire.
        - The wire is used as bundles or strands under clause 6.8.

    Sign convention:
        - Resistance is represented as a non-negative magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - High-strength steel wire under clause 6.8.

    Limitations:
        - Does not determine bundle efficiency or anchorage capacity.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> high_strength_wire_tension_design_resistance_n_mm2(510.0)
        321.3

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_equation_4_normal_zero_and_sign_unit_convention
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(normative_ultimate_resistance_n_mm2, "normative_ultimate_resistance_n_mm2")
    return 0.63 * value

def steel_rope_design_tension_force_n(rope_breaking_force_n: float) -> float:
    """
    Summary:
        Calculate design tensile force of a steel rope from its whole-rope breaking force.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: 6.9
        Annex: None
        Equation/Table: Clause procedure, gamma_m = 1.6
        Audit ID: SP16-PROC-6.9
        Normative status: normative

    Mathematical form:
        R_rope = F_breaking / 1.6

    Parameters:
        rope_breaking_force_n:
            Type: float
            Unit: N
            Meaning: Whole-rope breaking force specified by the applicable product standard.
            Valid range: >= 0
            Source: external product standard/certificate

    Returns:
        Type: float
        Unit: N
        Meaning: Design tensile force of the steel rope.

    Assumptions:
        - The breaking force refers to the entire rope, not an individual wire.
        - The product standard value is valid for the supplied rope.

    Sign convention:
        - Tension capacity is represented as a non-negative force magnitude.

    Unit convention:
        - Resistance inputs and outputs use N/mm2; force inputs and outputs use N where stated.

    Applicability:
        - Steel ropes covered by clause 6.9.

    Limitations:
        - The breaking force comes from an external normative document and is not selected by this package.

    Raises:
        TypeError: The input is not numeric.
        ValueError: The input is negative.

    Examples:
        >>> steel_rope_design_tension_force_n(1600000.0)
        1000000.0

    Tests:
        Unit tests:
            - tests/test_material_resistance.py::test_clause_6_9_rope_normal_zero_and_units
        Validation cases:
            - CORE-SELF-CHECK-v0.2

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    value = _require_nonnegative(rope_breaking_force_n, "rope_breaking_force_n")
    return value / 1.6


class SteelMaterialStrengthResolver:
    """
    Summary:
        Resolve the Stage N1 rolled-steel material/strength route against the current
        СП 16 Annex B.1 and Annex V.3-V.5 datasets without interpolation or hidden defaults.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Consolidated source with Changes No. 1-6 through 09.12.2024
        Clauses: 4.3.2, 5.1, 6.1
        Tables: 2, 3, Б.1, В.3, В.4, В.5
        Audit IDs: SP16-TBL-2, SP16-TBL-3, SP16-TBL-Б-1, SP16-TBL-В-3, SP16-TBL-В-4, SP16-TBL-В-5

    Fields:
        The resolver owns no mutable engineering state. All selections are supplied
        explicitly to its methods. Current normative source identity is embedded in
        the materialized datasets and returned with every lookup.

    Validation:
        Stage N1 source transcription, exact-row, boundary, alias, routing and
        fail-closed tests are in tests/test_stage_n1_material_strength.py. NormCAD
        comparisons are preserved separately as secondary validation evidence.

    Used by:
        Material selection UX, downstream СП 16 member checks, fire-resistance
        coupling, and Stage N1 validation/crosswalk tooling.
    """

    _ROUTES = {
        "plate_sheet_strip": ("В.3", _V3_STRENGTH),
        "bar_rolled": ("В.3", _V3_STRENGTH),
        "tube": ("В.3", _V3_STRENGTH),
        "parallel_flange_i": ("В.4", _V4_STRENGTH),
        "shaped_rolled": ("В.5", _V5_STRENGTH),
    }

    @staticmethod
    def _normalize_grade(steel_grade: str) -> str:
        if not isinstance(steel_grade, str) or not steel_grade.strip():
            raise TypeError("steel_grade must be a non-empty string")
        value = steel_grade.strip().upper().replace("–", "-").replace("—", "-")
        # User-facing tolerance only: Russian steel designations are often typed
        # with a Latin leading C. The returned trace always exposes normalization.
        if value.startswith("C"):
            value = "С" + value[1:]
        return value

    @staticmethod
    def _interval_contains(interval: dict[str, Any], thickness_mm: float) -> bool:
        lo = interval.get("min_mm")
        hi = interval.get("max_mm")
        if lo is not None:
            if thickness_mm < float(lo) or (thickness_mm == float(lo) and not interval["min_inclusive"]):
                return False
        if hi is not None:
            if thickness_mm > float(hi) or (thickness_mm == float(hi) and not interval["max_inclusive"]):
                return False
        return True

    @staticmethod
    def _interval_key(interval: Mapping[str, Any]) -> str:
        """Return a stable exact key for one printed Annex В thickness interval."""
        lo = interval.get("min_mm")
        hi = interval.get("max_mm")
        linc = bool(interval.get("min_inclusive"))
        hinc = bool(interval.get("max_inclusive"))
        def fmt(value: Any) -> str:
            if value is None:
                return "*"
            x = float(value)
            return str(int(x)) if x.is_integer() else (f"{x:.12g}")
        return f"{fmt(lo)}:{1 if linc else 0}|{fmt(hi)}:{1 if hinc else 0}"

    @staticmethod
    def _interval_label(interval: Mapping[str, Any]) -> str:
        """Return a compact Russian label preserving the printed bound logic."""
        lo = interval.get("min_mm")
        hi = interval.get("max_mm")
        linc = bool(interval.get("min_inclusive"))
        hinc = bool(interval.get("max_inclusive"))
        def fmt(value: Any) -> str:
            x = float(value)
            return str(int(x)) if x.is_integer() else (f"{x:g}").replace(".", ",")
        if lo is None and hi is not None:
            return f"до {fmt(hi)} мм{' включ.' if hinc else ''}"
        if hi is None and lo is not None:
            return f"{'от ' if linc else 'св. '}{fmt(lo)} мм"
        if lo is not None and hi is not None:
            if linc:
                left = f"от {fmt(lo)}"
            else:
                left = f"св. {fmt(lo)}"
            return f"{left} до {fmt(hi)} мм{' включ.' if hinc else ''}"
        raise ValueError("invalid unbounded thickness interval")

    def strength_selection_catalog(self, product_form: str) -> dict[str, Any]:
        """Return user-selectable grades and exact printed thickness intervals for one materialized Annex В route."""
        if product_form not in self._ROUTES:
            self.material_table_route(product_form)
        table_ref, dataset = self._ROUTES[product_form]
        grades: dict[str, list[dict[str, Any]]] = {}
        for index, row in enumerate(dataset["rows"], start=1):
            interval = dict(row["thickness_interval"])
            option = {
                "interval_key": self._interval_key(interval),
                "interval_label": self._interval_label(interval),
                "thickness_interval": interval,
                "source_row_index": index,
                "Ryn_MPa": row["Ryn_MPa"],
                "Run_MPa": row["Run_MPa"],
                "Ry_MPa": row["Ry_MPa"],
                "Ru_MPa": row["Ru_MPa"],
                "Rs_from_tabulated_Ry_MPa": None if row["Ry_MPa"] is None else 0.58 * float(row["Ry_MPa"]),
                "note": row.get("note"),
            }
            for grade in row["grades"]:
                grades.setdefault(str(grade), []).append(dict(option))
        return {
            "product_form": product_form,
            "source_table": table_ref,
            "source_sha256": dataset["normative_source"]["source_sha256"],
            "grades": [
                {"steel_grade": grade, "intervals": rows}
                for grade, rows in sorted(grades.items(), key=lambda item: item[0])
            ],
        }

    def lookup_strength_row_by_interval_key(self, product_form: str, steel_grade: str, interval_key: str) -> dict[str, Any]:
        """Resolve one exact Annex В row by normalized grade and stable printed-interval key."""
        if not isinstance(interval_key, str) or not interval_key.strip():
            raise TypeError("interval_key must be a non-empty string")
        if product_form not in self._ROUTES:
            self.material_table_route(product_form)
        table_ref, dataset = self._ROUTES[product_form]
        normalized = self._normalize_grade(steel_grade)
        matches = []
        for index, row in enumerate(dataset["rows"], start=1):
            if normalized in row["grades"] and self._interval_key(row["thickness_interval"]) == interval_key:
                matches.append((index, row))
        if not matches:
            raise ValueError(
                f"No exact {table_ref} row for grade={normalized!r}, interval_key={interval_key!r}; "
                "interpolation and extrapolation are forbidden."
            )
        if len(matches) != 1:
            raise RuntimeError(f"Dataset integrity error: {len(matches)} rows match {table_ref} {normalized} interval={interval_key}")
        index, row = matches[0]
        return {
            "product_form": product_form,
            "steel_grade_input": steel_grade,
            "steel_grade_normalized": normalized,
            "source_table": table_ref,
            "source_row_index": index,
            "source_sha256": dataset["normative_source"]["source_sha256"],
            "thickness_interval": dict(row["thickness_interval"]),
            "thickness_interval_key": self._interval_key(row["thickness_interval"]),
            "thickness_interval_label": self._interval_label(row["thickness_interval"]),
            "Ryn_MPa": row["Ryn_MPa"],
            "Run_MPa": row["Run_MPa"],
            "Ry_tabulated_MPa": row["Ry_MPa"],
            "Ru_tabulated_MPa": row["Ru_MPa"],
            "Rs_from_tabulated_Ry_MPa": None if row["Ry_MPa"] is None else 0.58 * float(row["Ry_MPa"]),
            "note": row.get("note"),
        }

    def physical_properties(self) -> dict[str, Any]:
        """Return the source-backed Table Б.1 physical constants for rolled steel."""
        return {
            **dict(_B1_PHYSICAL["rolled_steel"]),
            "source_table": "Б.1",
            "source_sha256": _B1_PHYSICAL["normative_source"]["source_sha256"],
        }

    def material_table_route(self, product_form: str) -> str:
        """Return the Annex В table route for a supported product form."""
        if product_form not in self._ROUTES:
            raise ValueError(
                f"No current-SP16 material table route is materialized for product_form={product_form!r}; "
                "resolve Ryn/Run from the applicable external product standard and use Table 2 explicitly."
            )
        return self._ROUTES[product_form][0]

    def lookup_strength_row(self, product_form: str, steel_grade: str, thickness_mm: float) -> dict[str, Any]:
        """Resolve one exact Annex В.3/В.4/В.5 row; interpolation/extrapolation are forbidden."""
        thickness = _require_positive(thickness_mm, "thickness_mm")
        if product_form not in self._ROUTES:
            self.material_table_route(product_form)  # raises the canonical fail-closed error
        table_ref, dataset = self._ROUTES[product_form]
        normalized = self._normalize_grade(steel_grade)
        matches=[]
        for index, row in enumerate(dataset["rows"], start=1):
            if normalized in row["grades"] and self._interval_contains(row["thickness_interval"], thickness):
                matches.append((index,row))
        if not matches:
            raise ValueError(
                f"No exact {table_ref} row for grade={normalized!r}, thickness_mm={thickness:g}; "
                "interpolation and extrapolation are forbidden."
            )
        if len(matches) != 1:
            raise RuntimeError(f"Dataset integrity error: {len(matches)} rows match {table_ref} {normalized} t={thickness}")
        index,row=matches[0]
        return {
            "product_form": product_form,
            "steel_grade_input": steel_grade,
            "steel_grade_normalized": normalized,
            "governing_thickness_mm": thickness,
            "source_table": table_ref,
            "source_row_index": index,
            "source_sha256": dataset["normative_source"]["source_sha256"],
            "thickness_interval": dict(row["thickness_interval"]),
            "Ryn_MPa": row["Ryn_MPa"],
            "Run_MPa": row["Run_MPa"],
            "Ry_tabulated_MPa": row["Ry_MPa"],
            "Ru_tabulated_MPa": row["Ru_MPa"],
            "note": row.get("note"),
        }

    def formula_resistances(self, Ryn_MPa: float, Run_MPa: float, material_safety_category: str) -> dict[str, float]:
        """Evaluate current Table 2 using an explicit Table 3 material-safety category."""
        gamma_m = material_safety_factor(material_safety_category)
        return {
            "gamma_m": gamma_m,
            "Ry_formula_MPa": design_yield_resistance_n_mm2(Ryn_MPa, gamma_m),
            "Ru_formula_MPa": design_ultimate_resistance_n_mm2(Run_MPa, gamma_m),
            "Rs_formula_MPa": design_shear_resistance_n_mm2(Ryn_MPa, gamma_m),
            "Rp_formula_MPa": design_end_bearing_resistance_n_mm2(Run_MPa, gamma_m),
            "Rlp_formula_MPa": design_pin_local_bearing_resistance_n_mm2(Run_MPa, gamma_m),
            "Rcd_formula_MPa": design_roller_diametral_compression_resistance_n_mm2(Run_MPa, gamma_m),
        }

    def resolve(self, product_form: str, steel_grade: str, thickness_mm: float, material_safety_category: str) -> dict[str, Any]:
        """Return the complete auditable N1 bundle while keeping tabulated and formula-derived design values distinct."""
        row = self.lookup_strength_row(product_form, steel_grade, thickness_mm)
        physical = self.physical_properties()
        formula = self.formula_resistances(float(row["Ryn_MPa"]), float(row["Run_MPa"]), material_safety_category)
        return {
            "stage": "N1_MATERIAL_STRENGTH",
            "normative_source_sha256": row["source_sha256"],
            "annex_strength": row,
            "physical_properties": physical,
            "table_2_formula_resistances": formula,
            "gamma_u": float(_GAMMA_U["gamma_u"]),
            "gamma_u_source": "СП 16 4.3.2",
            "selection_warning": (
                "Ry/Ru printed in Annex В and values recomputed from Table 2 + an explicitly selected gamma_m "
                "are preserved as separate quantities; this resolver does not silently substitute one for the other."
            ),
        }
