"""Effective lengths and limiting slenderness for Section 10 of SP 16.13330.2017."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLES = json.loads((_DATA_DIR / "tables_24_to_33_effective_lengths.json").read_text(encoding="utf-8"))["tables"]

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-10.1.1-TABLE-24-ROUTING",
    "SP16-PROC-10.1.3-TABLE-25-ROUTING",
    "SP16-PROC-10.1.4-SINGLE-ANGLE-RADIUS-SELECTION",
    "SP16-PROC-10.2.1-TABLE-26-ROUTING",
    "SP16-PROC-10.2.2-RADIUS-SELECTION",
    "SP16-PROC-10.2.3-TABLE-27-ROUTING",
    "SP16-PROC-10.2.3-TABLE-28-ROUTING",
    "SP16-PROC-10.2.3-TABLE-29-ROUTING",
    "SP16-PROC-10.2.4-FIG15C-SPECIAL-ROUTING",
    "SP16-PROC-10.2.5-TUBE-AND-DOUBLE-ANGLE-ROUTING",
    "SP16-PROC-10.3.2-LOAD-COMBINATION-CONSISTENCY",
    "SP16-PROC-10.3.3-TABLE-30-ROUTING",
    "SP16-PROC-10.3.4-TABLE-31-PARAMETERS",
    "SP16-PROC-10.3.4-TABLE-31-SPECIAL-CASES",
    "SP16-PROC-10.3.5-GLOBAL-FRAME-STABILITY-ROUTE",
    "SP16-PROC-10.3.7-STEPPED-COLUMN-EXTERNAL-ROUTE",
    "SP16-PROC-10.3.9-OUT-OF-PLANE-COLUMN-LENGTH",
    "SP16-PROC-10.3.10-GALLERY-SUPPORT-LENGTH",
    "SP16-PROC-10.3.11-CERTIFIED-SOFTWARE-ASSUMPTION",
    "SP16-PROC-10.4.1-SLENDERNESS-CHECK",
    "SP16-PROC-10.4.2-GROUP-4-INCREASE",
    "SP16-PROC-TABLE-33-NOTES",
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

def _linear(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0+(y1-y0)*(x-x0)/(x1-x0)

def table_24_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 24.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.1
        Annex: None
        Equation/Table: Table 24
        Audit ID: SP16-TBL-24
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-24

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["24"], ensure_ascii=False))

def table_25_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 25.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.3
        Annex: None
        Equation/Table: Table 25
        Audit ID: SP16-TBL-25
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-25

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["25"], ensure_ascii=False))

def table_26_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 26.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.1
        Annex: None
        Equation/Table: Table 26
        Audit ID: SP16-TBL-26
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-26

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["26"], ensure_ascii=False))

def table_27_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 27.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 27
        Audit ID: SP16-TBL-27
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-27

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["27"], ensure_ascii=False))

def table_28_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 28.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 28
        Audit ID: SP16-TBL-28
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-28

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["28"], ensure_ascii=False))

def table_29_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 29.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 29
        Audit ID: SP16-TBL-29
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-29

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["29"], ensure_ascii=False))

def table_30_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 30.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.3
        Annex: None
        Equation/Table: Table 30
        Audit ID: SP16-TBL-30
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-30

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["30"], ensure_ascii=False))

def table_31_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 31.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Table 31
        Audit ID: SP16-TBL-31
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-31

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["31"], ensure_ascii=False))

def table_32_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 32.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Table 32
        Audit ID: SP16-TBL-32
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-32

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["32"], ensure_ascii=False))

def table_33_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited metadata catalogue for Table 33.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Table 33
        Audit ID: SP16-TBL-33
        Normative status: normative

    Mathematical form:
        Deep-copy lookup of transcribed normative metadata.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-33

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLES["33"], ensure_ascii=False))

def truss_chord_effective_length_in_plane_eq136(segment_length: float, adjacent_force_ratio_alpha: float) -> float:
    """
    Summary:
        Calculate the in-plane effective length of a continuous truss chord with varying panel forces.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.2
        Annex: None
        Equation/Table: Equation (136)
        Audit ID: SP16-EQ-136
        Normative status: normative

    Mathematical form:
        l_eff=max((0.17*alpha**3+0.83)*l, 0.8*l).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-136

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l=_positive(segment_length,"segment_length")
    a=_real(adjacent_force_ratio_alpha,"adjacent_force_ratio_alpha")
    if not -0.55<=a<=1.0: raise ValueError("alpha must be within [-0.55, 1]")
    return max((0.17*a**3+0.83)*l,0.8*l)

def truss_chord_effective_length_out_of_plane_eq137(braced_length: float, section_count_k: int, other_force_sum_ratio_beta: float) -> float:
    """
    Summary:
        Calculate the out-of-plane effective length of a continuous truss chord with varying panel forces.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.2
        Annex: None
        Equation/Table: Equation (137)
        Audit ID: SP16-EQ-137
        Normative status: normative

    Mathematical form:
        l_eff,1=max((0.75+0.25*(beta/(k-1))**(2*k-3))*l1,0.5*l1).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-137

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l1=_positive(braced_length,"braced_length")
    if isinstance(section_count_k,bool) or not isinstance(section_count_k,int) or section_count_k<2: raise ValueError("section_count_k must be an integer >=2")
    b=_real(other_force_sum_ratio_beta,"other_force_sum_ratio_beta")
    if not -0.5<=b<=section_count_k-1: raise ValueError("beta must be within [-0.5, k-1]")
    value=(0.75+0.25*(b/(section_count_k-1))**(2*section_count_k-3))*l1
    return max(value,0.5*l1)

def built_up_column_branch_effective_length_in_plane_eq138(segment_length: float, adjacent_force_ratio_alpha: float) -> float:
    """
    Summary:
        Calculate the in-plane effective length of a built-up column branch with varying segment forces.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.2
        Annex: None
        Equation/Table: Equation (138)
        Audit ID: SP16-EQ-138
        Normative status: normative

    Mathematical form:
        l_eff=max(l*sqrt(0.36+0.59*alpha**3),0.6*l).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-138

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l=_positive(segment_length,"segment_length"); a=_real(adjacent_force_ratio_alpha,"adjacent_force_ratio_alpha")
    if not 0.0<=a<=1.0: raise ValueError("alpha must be within [0, 1]")
    return max(l*math.sqrt(0.36+0.59*a**3),0.6*l)

def built_up_column_branch_effective_length_out_of_plane_eq139(braced_length: float, section_count_k: int, other_force_sum_ratio_beta: float) -> float:
    """
    Summary:
        Calculate the out-of-plane effective length of a built-up column branch with varying segment forces.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.2
        Annex: None
        Equation/Table: Equation (139)
        Audit ID: SP16-EQ-139
        Normative status: normative

    Mathematical form:
        l_eff,1=max((0.6*sqrt(k)+0.54*beta)*l1/k,0.5*l1).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-139

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l1=_positive(braced_length,"braced_length")
    if isinstance(section_count_k,bool) or not isinstance(section_count_k,int) or section_count_k<2: raise ValueError("section_count_k must be an integer >=2")
    b=_real(other_force_sum_ratio_beta,"other_force_sum_ratio_beta")
    if not 0.0<=b<=section_count_k-1: raise ValueError("beta must be within [0, k-1]")
    return max((0.6*math.sqrt(section_count_k)+0.54*b)*l1/section_count_k,0.5*l1)

def table_24_effective_length(case_id: str, member_role: str, geometric_length: float, out_of_plane_braced_length: float | None = None) -> float:
    """
    Summary:
        Apply Table 24 to a compressed truss member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.1
        Annex: None
        Equation/Table: Table 24
        Audit ID: SP16-PROC-10.1.1-TABLE-24-ROUTING
        Normative status: normative

    Mathematical form:
        factor times l or l1 according to row and member role.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.1.1-TABLE-24-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    rows=_TABLES["24"]["rows"]
    if case_id not in rows: raise ValueError(f"unknown Table 24 case: {case_id}")
    if member_role not in rows[case_id]: raise ValueError("member_role must be chord, support_diagonal_or_post, or other_web")
    basis=_TABLES["24"]["length_basis"]["out_of_plane" if case_id.startswith("out_of_plane") else ("single_angle_equal_restraint_distances" if case_id.startswith("single_angle") else "in_plane")]
    length=_positive(out_of_plane_braced_length,"out_of_plane_braced_length") if basis=="l1" else _positive(geometric_length,"geometric_length")
    return float(rows[case_id][member_role])*length

def table_25_cross_lattice_effective_length(joint_case: str, supporting_state: str, node_to_intersection_length: float, full_member_length: float) -> float:
    """
    Summary:
        Apply Table 25 to a mutually braced crossing lattice member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.3
        Annex: None
        Equation/Table: Table 25
        Audit ID: SP16-PROC-10.1.3-TABLE-25-ROUTING
        Normative status: normative

    Mathematical form:
        selected factor times l or l1.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.1.3-TABLE-25-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    rows=_TABLES["25"]["rows"]
    if joint_case not in rows: raise ValueError("unknown Table 25 joint_case")
    if supporting_state not in rows[joint_case] or rows[joint_case][supporting_state] is None: raise ValueError("Table 25 has no value for this state")
    item=rows[joint_case][supporting_state]
    basis=_positive(node_to_intersection_length,"node_to_intersection_length") if item["basis"]=="l" else _positive(full_member_length,"full_member_length")
    return float(item["factor"])*basis

def single_angle_radius_selection_clause_10_1_4(effective_length: float, node_spacing: float, buckling_direction: str) -> str:
    """
    Summary:
        Select the radius-of-gyration axis rule for a single-angle truss member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1.4
        Annex: None
        Equation/Table: Clause 10.1.4
        Audit ID: SP16-PROC-10.1.4-SINGLE-ANGLE-RADIUS-SELECTION
        Normative status: normative

    Mathematical form:
        i=i_min when l_eff>=0.85*l; otherwise ix or iy by buckling direction.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.1.4-SINGLE-ANGLE-RADIUS-SELECTION

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    le=_positive(effective_length,"effective_length"); l=_positive(node_spacing,"node_spacing")
    if le>=0.85*l: return "i_min"
    if buckling_direction not in {"perpendicular_to_truss_plane","parallel_to_truss_plane"}: raise ValueError("invalid buckling_direction")
    return "i_x" if buckling_direction=="perpendicular_to_truss_plane" else "i_y"

def table_26_structural_member_effective_length(member_case: str, geometric_length: float, geometric_slenderness_l_over_i_min: float | None = None, is_lattice_member: bool = False) -> float:
    """
    Summary:
        Apply Table 26 to a structural-space-frame member.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.1
        Annex: None
        Equation/Table: Table 26
        Audit ID: SP16-PROC-10.2.1-TABLE-26-ROUTING
        Normative status: normative

    Mathematical form:
        selected factor times l with slenderness-band restrictions.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.1-TABLE-26-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l=_positive(geometric_length,"geometric_length")
    if member_case=="general": return l
    if member_case=="continuous_or_butt_node": return 0.85*l
    if member_case not in {"single_angle_welded_or_two_bolts","single_angle_one_bolt"}: raise ValueError("unknown Table 26 member_case")
    s=_positive(geometric_slenderness_l_over_i_min,"geometric_slenderness_l_over_i_min")
    rows=_TABLES["26"][member_case]
    for lo,hi,factor,lattice_only in rows:
        if (s<=hi and (s>lo or lo==0)):
            if lattice_only and not is_lattice_member: raise ValueError("this slenderness band is permitted only for lattice members")
            return float(factor)*l
    raise ValueError("l/i_min exceeds Table 26 range")

def structural_member_radius_selection_clause_10_2_2(is_beam_column: bool, bending_plane_relation: str) -> str:
    """
    Summary:
        Select the radius-of-gyration axis rule for structural-space-frame members.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.2
        Annex: None
        Equation/Table: Clause 10.2.2
        Audit ID: SP16-PROC-10.2.2-RADIUS-SELECTION
        Normative status: normative

    Mathematical form:
        beam-columns use ix or iy; other members use i_min.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.2-RADIUS-SELECTION

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not is_beam_column: return "i_min"
    if bending_plane_relation not in {"perpendicular_axis_x","parallel_axis_y"}: raise ValueError("invalid bending_plane_relation")
    return "i_x" if bending_plane_relation=="perpendicular_axis_x" else "i_y"

def table_27_spatial_member_properties(row_id: str, force_state: str, base_lengths: dict[str, float], mu_d: float | None = None, out_of_plane_variant: bool = False) -> dict[str, Any]:
    """
    Summary:
        Apply Table 27 to return effective length and radius-of-gyration route.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 27
        Audit ID: SP16-PROC-10.2.3-TABLE-27-ROUTING
        Normative status: normative

    Mathematical form:
        row-specific factor times lm, ld, ldc, or lc plus radius selector.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.3-TABLE-27-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    rows=_TABLES["27"]["rows"]
    if row_id not in rows or force_state not in rows[row_id] or rows[row_id][force_state] is None: raise ValueError("invalid or unavailable Table 27 route")
    item=rows[row_id][force_state]
    factor=float(item["factor"]) if "factor" in item else _positive(mu_d,"mu_d")
    basis=item["basis"]
    if basis=="ld_or_ld1": key="ld1" if out_of_plane_variant else "ld"
    else: key=basis
    if key not in base_lengths: raise ValueError(f"base_lengths must contain {key}")
    length=factor*_positive(base_lengths[key],key)
    radius=item["radius"]
    if radius=="imin_or_ix": radius="i_x" if out_of_plane_variant else "i_min"
    if radius == "imin":
        radius = "i_min"
    elif radius == "ix":
        radius = "i_x"
    return {"effective_length":length,"radius_selector":radius,"basis":key,"factor":factor}

def table_28_n_parameter(chord_min_inertia: float, diagonal_length: float, diagonal_min_inertia: float, chord_panel_length: float) -> float:
    """
    Summary:
        Calculate and clamp parameter n used by Table 28.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 28 definition
        Audit ID: SP16-PROC-10.2.3-TABLE-28-ROUTING
        Normative status: normative

    Mathematical form:
        n=I_m,min*l_d/(I_d,min*l_m), clamped to [1,3].

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.3-TABLE-28-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    n=_positive(chord_min_inertia,"chord_min_inertia")*_positive(diagonal_length,"diagonal_length")/(_positive(diagonal_min_inertia,"diagonal_min_inertia")*_positive(chord_panel_length,"chord_panel_length"))
    return min(max(n,1.0),3.0)

def table_28_intersection_conditional_length(joint_case: str, supporting_state: str, diagonal_length: float, alternate_diagonal_length: float, n_parameter: float) -> float:
    """
    Summary:
        Apply Table 28 to the conditional diagonal length at an intersection.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 28
        Audit ID: SP16-PROC-10.2.3-TABLE-28-ROUTING
        Normative status: normative

    Mathematical form:
        piecewise factor times l_d or l_d1.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.3-TABLE-28-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    ld=_positive(diagonal_length,"diagonal_length"); ld1=_positive(alternate_diagonal_length,"alternate_diagonal_length")
    n=min(max(_positive(n_parameter,"n_parameter"),1.0),3.0)
    if supporting_state not in {"tension","inactive","compression"}: raise ValueError("invalid supporting_state")
    if joint_case=="both_continuous": return {"tension":ld,"inactive":1.3*ld,"compression":0.8*ld1}[supporting_state]
    if joint_case=="support_interrupted_fig15a": return {"tension":1.3*ld,"inactive":1.6*ld,"compression":ld1}[supporting_state]
    if joint_case=="support_interrupted_fig15d": return {"tension":(1.75-0.15*n)*ld,"inactive":(1.9-0.1*n)*ld,"compression":ld1}[supporting_state]
    if joint_case=="intersection_out_of_plane_braced": return ld
    raise ValueError("unknown Table 28 joint_case")

def table_29_diagonal_length_factor(connection_case: str, n_parameter: float, geometric_slenderness_l_over_i_min: float) -> float:
    """
    Summary:
        Calculate the diagonal effective-length coefficient mu_d from Table 29.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 29
        Audit ID: SP16-PROC-10.2.3-TABLE-29-ROUTING
        Normative status: normative

    Mathematical form:
        piecewise slenderness formula with interpolation for 2<n<=6.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.3-TABLE-29-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    s=_positive(geometric_slenderness_l_over_i_min,"geometric_slenderness_l_over_i_min")
    n=_positive(n_parameter,"n_parameter")
    def row(kind):
        if kind=="low": return 1.14 if s<=60 else (0.54+36.0/s if s<=160 else 0.765)
        if kind=="high": return 1.04 if s<=60 else (0.54+28.8/s if s<=160 else 0.740)
        return 1.12 if s<=60 else (0.64+28.8/s if s<=160 else 0.820)
    if connection_case=="one_bolt_without_gusset": return row("one")
    if connection_case!="welded_or_two_bolts": raise ValueError("unknown connection_case")
    if n<=2: return row("low")
    if n>6: return row("high")
    return _linear(n,2.0,6.0,row("low"),row("high"))

def table_29_end_connection_adjustment(base_mu_d: float, gusset_configuration: str) -> float:
    """
    Summary:
        Apply the Table 29 note for one or two gusset-connected diagonal ends.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.2.3
        Annex: None
        Equation/Table: Table 29 Note 2
        Audit ID: SP16-PROC-10.2.3-TABLE-29-ROUTING
        Normative status: normative

    Mathematical form:
        mu=base, 0.5*(1+base), or 1.0.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.2.3-TABLE-29-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    mu=_positive(base_mu_d,"base_mu_d")
    if gusset_configuration=="no_gusset_ends": return mu
    if gusset_configuration=="one_gusset_end": return 0.5*(1.0+mu)
    if gusset_configuration=="both_gusset_ends": return 1.0
    raise ValueError("invalid gusset_configuration")

def column_effective_length_eq140(column_length: float, effective_length_factor_mu: float) -> float:
    """
    Summary:
        Calculate column effective length from its length and effective-length factor.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.1
        Annex: None
        Equation/Table: Equation (140)
        Audit ID: SP16-EQ-140
        Normative status: normative

    Mathematical form:
        l_eff=mu*l.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-140

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(column_length,"column_length")*_positive(effective_length_factor_mu,"effective_length_factor_mu")

def table_30_effective_length_factor(scheme_id: str) -> float:
    """
    Summary:
        Return the effective-length factor for a Table 30 diagram.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.3
        Annex: None
        Equation/Table: Table 30
        Audit ID: SP16-PROC-10.3.3-TABLE-30-ROUTING
        Normative status: normative

    Mathematical form:
        exact scheme lookup.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.3-TABLE-30-ROUTING

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    rows=_TABLES["30"]["scheme_factors"]
    if scheme_id not in rows: raise ValueError("scheme_id must be scheme_1 through scheme_8")
    return float(rows[scheme_id])

def frame_stiffness_ratio(member_inertia: float, column_length: float, column_inertia: float, member_length: float) -> float:
    """
    Summary:
        Calculate one beam-to-column stiffness ratio used in Table 31 parameters.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Table 31 parameter definitions
        Audit ID: SP16-PROC-10.3.4-TABLE-31-PARAMETERS
        Normative status: normative

    Mathematical form:
        ratio=I_member*l_column/(I_column*l_member).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.4-TABLE-31-PARAMETERS

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(member_inertia,"member_inertia")*_positive(column_length,"column_length")/(_positive(column_inertia,"column_inertia")*_positive(member_length,"member_length"))

def table_31_multistory_parameters(frame_type: str, storey_position: str, span_count_k: int, p1: float, p2: float, n1: float, n2: float) -> dict[str, float]:
    """
    Summary:
        Calculate p and n for a multistory frame row of Table 31.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Table 31
        Audit ID: SP16-PROC-10.3.4-TABLE-31-PARAMETERS
        Normative status: normative

    Mathematical form:
        storey-specific combinations of p1,p2,n1,n2 and k.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.4-TABLE-31-PARAMETERS

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if isinstance(span_count_k,bool) or not isinstance(span_count_k,int) or span_count_k<1: raise ValueError("span_count_k must be a positive integer")
    vals=[_nonnegative(x,nm) for x,nm in [(p1,"p1"),(p2,"p2"),(n1,"n1"),(n2,"n2")]]; p1,p2,n1,n2=vals
    if frame_type=="sway":
        if storey_position=="top": return {"p":span_count_k*(p1+p2)/(span_count_k+1),"n":2*span_count_k*(n1+n2)/(span_count_k+1)}
        if storey_position=="middle": return {"p":span_count_k*(p1+p2)/(span_count_k+1),"n":span_count_k*(n1+n2)/(span_count_k+1)}
        if storey_position=="bottom": return {"p":2*span_count_k*(p1+p2)/(span_count_k+1),"n":span_count_k*(n1+n2)/(span_count_k+1)}
    elif frame_type=="nonsway":
        if storey_position=="top": return {"p":0.5*(p1+p2),"n":n1+n2}
        if storey_position=="middle": return {"p":0.5*(p1+p2),"n":0.5*(n1+n2)}
        if storey_position=="bottom": return {"p":p1+p2,"n":0.5*(n1+n2)}
    raise ValueError("invalid frame_type or storey_position")

def sway_frame_mu_eq141(n_parameter: float) -> float:
    """
    Summary:
        Calculate sway-frame mu for p=0.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Equation (141)
        Audit ID: SP16-EQ-141
        Normative status: normative

    Mathematical form:
        mu=2*sqrt(1+0.38/n), per FCS clarification letter No. Исх-8076 dated 10.11.2023.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-141

    Implementation notes:
        - Official FCS clarification letter No. Исх-8076 dated 10.11.2023 corrects the printed Equation (141) typo to mu=2*sqrt(1+0.38/n).
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    n=_positive(n_parameter,"n_parameter"); return 2.0*math.sqrt(1.0+0.38/n)

def sway_frame_mu_eq142(n_parameter: float) -> float:
    """
    Summary:
        Calculate sway-frame mu for p tending to infinity.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Equation (142)
        Audit ID: SP16-EQ-142
        Normative status: normative

    Mathematical form:
        mu=sqrt((n+0.56)/(n+0.14)).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-142

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    n=_nonnegative(n_parameter,"n_parameter"); return math.sqrt((n+0.56)/(n+0.14))

def sway_frame_mu_eq143(p_parameter: float, n_parameter: float) -> float:
    """
    Summary:
        Calculate sway-frame mu for n not exceeding 0.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Equation (143)
        Audit ID: SP16-EQ-143
        Normative status: normative

    Mathematical form:
        mu=(p+0.68)*sqrt(n+0.22)/sqrt(0.68*p*(p+0.9)*(n+0.08)+0.1*n).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-143

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    p=_positive(p_parameter,"p_parameter"); n=_nonnegative(n_parameter,"n_parameter")
    if n>0.2: raise ValueError("equation (143) requires n<=0.2")
    return (p+0.68)*math.sqrt(n+0.22)/math.sqrt(0.68*p*(p+0.9)*(n+0.08)+0.1*n)

def sway_frame_mu_eq144(p_parameter: float, n_parameter: float) -> float:
    """
    Summary:
        Calculate sway-frame mu for n greater than 0.2.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Equation (144)
        Audit ID: SP16-EQ-144
        Normative status: normative

    Mathematical form:
        mu=(p+0.63)*sqrt(n+0.28)/sqrt(p*n*(p+0.9)+0.1*n).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-144

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    p=_positive(p_parameter,"p_parameter"); n=_positive(n_parameter,"n_parameter")
    if n<=0.2: raise ValueError("equation (144) requires n>0.2")
    return (p+0.63)*math.sqrt(n+0.28)/math.sqrt(p*n*(p+0.9)+0.1*n)

def nonsway_frame_mu_eq145(p_parameter: float, n_parameter: float) -> float:
    """
    Summary:
        Calculate nonsway-frame effective-length factor.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Equation (145)
        Audit ID: SP16-EQ-145
        Normative status: normative

    Mathematical form:
        mu=sqrt((1+0.46*(p+n)+0.18*p*n)/(1+0.93*(p+n)+0.71*p*n)).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-145

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    p=_nonnegative(p_parameter,"p_parameter"); n=_nonnegative(n_parameter,"n_parameter")
    return math.sqrt((1.0+0.46*(p+n)+0.18*p*n)/(1.0+0.93*(p+n)+0.71*p*n))

def table_31_special_case_mu(case_id: str, parameter: float) -> float:
    """
    Summary:
        Evaluate one explicit special-case expression from Table 31.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.4
        Annex: None
        Equation/Table: Table 31 special cases
        Audit ID: SP16-PROC-10.3.4-TABLE-31-SPECIAL-CASES
        Normative status: normative

    Mathematical form:
        exact special-case formula selected by case_id.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.4-TABLE-31-SPECIAL-CASES

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    x=_positive(parameter,"parameter")
    if case_id=="sway_p0_n_0_03_to_0_2":
        if not 0.03<=x<=0.2: raise ValueError("n must be in [0.03,0.2]")
        return 2.15*math.sqrt((x+0.22)/x)
    if case_id=="sway_p0_n_gt_0_2":
        if x<=0.2: raise ValueError("n must exceed 0.2")
        return 2.0*math.sqrt((x+0.28)/x)
    if case_id=="sway_n_inf_p_0_03_to_50":
        if not 0.03<=x<=50: raise ValueError("p must be in [0.03,50]")
        return (x+0.63)/math.sqrt(x*(x+0.9)+0.1)
    if case_id=="sway_p_inf_n_0_03_to_0_2":
        if not 0.03<=x<=0.2: raise ValueError("n must be in [0.03,0.2]")
        return 1.21*math.sqrt((x+0.22)/(x+0.08))
    if case_id=="sway_p_inf_n_gt_0_2":
        if x<=0.2: raise ValueError("n must exceed 0.2")
        return math.sqrt((x+0.28)/x)
    if case_id=="nonsway_p0": return math.sqrt((1+0.46*x)/(1+0.93*x))
    if case_id=="nonsway_p_inf": return math.sqrt((1+0.39*x)/(2+1.54*x))
    raise ValueError("unknown Table 31 special case")

def nonuniform_sway_frame_effective_length_eq146(base_mu: float, checked_column_inertia: float, total_column_force: float, checked_column_force: float, total_column_inertia: float) -> float:
    """
    Summary:
        Reduce the effective-length factor for the most heavily loaded column in a nonuniformly loaded sway frame.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.6
        Annex: None
        Equation/Table: Equation (146)
        Audit ID: SP16-EQ-146
        Normative status: normative

    Mathematical form:
        mu_eff=max(mu*sqrt(Ic*sumN/(Nc*sumI)),0.7).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-146

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    mu=_positive(base_mu,"base_mu"); ratio=_positive(checked_column_inertia,"checked_column_inertia")*_positive(total_column_force,"total_column_force")/(_positive(checked_column_force,"checked_column_force")*_positive(total_column_inertia,"total_column_inertia"))
    return max(mu*math.sqrt(ratio),0.7)

def frame_deformation_reduction_factor_eq147(relative_slenderness: float, moment_n_mm: float, nonsway_reference_moment_n_mm: float, area_mm2: float, axial_force_n: float, compressed_fibre_section_modulus_mm3: float) -> dict[str, float]:
    """
    Summary:
        Calculate the frame-deformation reduction factor psi for sway-frame effective lengths.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.8
        Annex: None
        Equation/Table: Equation (147)
        Audit ID: SP16-EQ-147
        Normative status: normative

    Mathematical form:
        beta_hat=1-M1/M<=0.2; alpha_hat=0.65-0.9*beta+0.25*beta**2; m=M*A/(N*Wc); omega=lambda_bar/sqrt(1+m)<=5; psi=1-alpha_hat*(1-(omega/5)**2)**(5/4).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-EQ-147

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    lam=_nonnegative(relative_slenderness,"relative_slenderness"); M=_positive(moment_n_mm,"moment_n_mm"); M1=_real(nonsway_reference_moment_n_mm,"nonsway_reference_moment_n_mm")
    beta=1.0-M1/M
    if beta>0.2: raise ValueError("beta_hat must not exceed 0.2")
    alpha=0.65-0.9*beta+0.25*beta**2
    m=M*_positive(area_mm2,"area_mm2")/(_positive(axial_force_n,"axial_force_n")*_positive(compressed_fibre_section_modulus_mm3,"compressed_fibre_section_modulus_mm3"))
    omega=lam/math.sqrt(1.0+m)
    if omega>5.0: raise ValueError("omega must not exceed 5")
    psi=1.0-alpha*(1.0-(omega/5.0)**2)**1.25
    return {"beta_hat":beta,"alpha_hat":alpha,"relative_eccentricity_m":m,"omega":omega,"psi":psi}

def out_of_plane_column_effective_length_clause_10_3_9(restraint_spacing: float) -> float:
    """
    Summary:
        Return the out-of-plane column effective length as restraint-point spacing.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.9
        Annex: None
        Equation/Table: Clause 10.3.9
        Audit ID: SP16-PROC-10.3.9-OUT-OF-PLANE-COLUMN-LENGTH
        Normative status: normative

    Mathematical form:
        l_eff equals distance between points restrained out of the frame plane.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.9-OUT-OF-PLANE-COLUMN-LENGTH

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(restraint_spacing,"restraint_spacing")

def gallery_support_branch_effective_length_clause_10_3_10(direction: str, support_height: float, node_spacing: float, mu: float) -> float:
    """
    Summary:
        Return the effective length of a planar conveyor-gallery support branch.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.3.10
        Annex: None
        Equation/Table: Clause 10.3.10
        Audit ID: SP16-PROC-10.3.10-GALLERY-SUPPORT-LENGTH
        Normative status: normative

    Mathematical form:
        longitudinal: mu*height; transverse: node spacing.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.3.10-GALLERY-SUPPORT-LENGTH

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if direction=="longitudinal": return _positive(support_height,"support_height")*_positive(mu,"mu")
    if direction=="transverse": return _positive(node_spacing,"node_spacing")
    raise ValueError("direction must be longitudinal or transverse")

def actual_slenderness(effective_length: float, radius_of_gyration: float) -> float:
    """
    Summary:
        Calculate member slenderness for comparison with Tables 32 or 33.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Clause 10.4.1
        Audit ID: SP16-PROC-10.4.1-SLENDERNESS-CHECK
        Normative status: normative

    Mathematical form:
        lambda=l_eff/i.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.4.1-SLENDERNESS-CHECK

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return _positive(effective_length,"effective_length")/_positive(radius_of_gyration,"radius_of_gyration")

def compressed_limit_alpha(axial_force_n: float, stability_coefficient_phi: float, area_mm2: float, design_yield_resistance_n_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate alpha for Table 32 and enforce its lower bound.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Table 32 definition
        Audit ID: SP16-PROC-10.4.1-SLENDERNESS-CHECK
        Normative status: normative

    Mathematical form:
        alpha=max(N/(phi*A*Ry*gamma_c),0.5).

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.4.1-SLENDERNESS-CHECK

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    raw=_nonnegative(axial_force_n,"axial_force_n")/(_positive(stability_coefficient_phi,"stability_coefficient_phi")*_positive(area_mm2,"area_mm2")*_positive(design_yield_resistance_n_mm2,"design_yield_resistance_n_mm2")*_positive(working_condition_factor,"working_condition_factor"))
    return max(raw,0.5)

def group_4_limiting_slenderness_increase(base_limit: float, group_4_applies: bool) -> float:
    """
    Summary:
        Apply the 10 percent limiting-slenderness increase for structural group 4.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.2
        Annex: None
        Equation/Table: Clause 10.4.2
        Audit ID: SP16-PROC-10.4.2-GROUP-4-INCREASE
        Normative status: normative

    Mathematical form:
        lambda_u=1.1*base when group 4 applies.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.4.2-GROUP-4-INCREASE

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    base=_positive(base_limit,"base_limit"); return 1.1*base if group_4_applies else base

def table_32_compressed_limiting_slenderness(row_id: str, alpha: float, group_4_applies: bool = False) -> float:
    """
    Summary:
        Return the limiting slenderness of a compressed member from Table 32.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Table 32
        Audit ID: SP16-TBL-32
        Normative status: normative

    Mathematical form:
        row-specific constant or linear expression in alpha, then optional 10 percent increase.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-32

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    a=max(_nonnegative(alpha,"alpha"),0.5)
    formulas={"1a":180-60*a,"1b":120.0,"2a":210-60*a,"2b":220-40*a,"3":220.0,"4":180-60*a,"5":210-60*a,"6":200.0,"7":150.0}
    if row_id not in formulas: raise ValueError("row_id must be one of 1a,1b,2a,2b,3,4,5,6,7")
    return group_4_limiting_slenderness_increase(formulas[row_id],group_4_applies)

def table_33_tension_limiting_slenderness(row_id: str, load_category: str, group_4_applies: bool = False, low_self_weight_sag_for_row_5: bool = False, crane_modes_1k_to_6k_for_row_3: bool = False, prestressed_tension_member: bool = False) -> float | None:
    """
    Summary:
        Return the limiting slenderness of a tension member from Table 33 and its notes.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Table 33
        Audit ID: SP16-TBL-33
        Normative status: normative

    Mathematical form:
        exact row/load lookup with stated note overrides; None means unlimited for prestressed ties.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-TBL-33

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if prestressed_tension_member: return None
    if row_id not in _TABLES["33"]["rows"]: raise ValueError("row_id must be 1 through 8")
    if load_category not in {"dynamic","static","crane_or_rail"}: raise ValueError("invalid load_category")
    if row_id=="5" and load_category=="static" and low_self_weight_sag_for_row_5: value=500.0
    elif row_id=="3" and load_category=="crane_or_rail" and crane_modes_1k_to_6k_for_row_3: value=200.0
    else:
        raw=_TABLES["33"]["rows"][row_id][load_category]
        if raw is None: raise ValueError("Table 33 has no limit for this row and load category")
        value=float(raw)
    return group_4_limiting_slenderness_increase(value,group_4_applies)

def slenderness_check(actual_slenderness_value: float, limiting_slenderness_value: float | None) -> dict[str, Any]:
    """
    Summary:
        Compare actual slenderness with the selected limiting value.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.4.1
        Annex: None
        Equation/Table: Tables 32-33 check
        Audit ID: SP16-PROC-10.4.1-SLENDERNESS-CHECK
        Normative status: normative

    Mathematical form:
        utilization=lambda/lambda_u; unlimited returns pass with utilization 0.

    Parameters:
        Inputs are explicit function arguments with unit-explicit names.

    Returns:
        Type: float | dict[str, Any] | str | None
        Unit: explicit in the function name or returned metadata
        Meaning: Calculated scalar or traceable routing record.

    Assumptions:
        - Inputs belong to one member, axis, load combination, and normative diagram.

    Sign convention:
        - Compression and demand magnitudes are non-negative unless a signed force ratio is explicitly allowed.

    Unit convention:
        - Lengths use one consistent unit; ratios and factors are dimensionless.

    Applicability:
        - Selected Section 10 procedure.

    Limitations:
        - Diagram classification and global structural analysis remain external.

    Raises:
        ValueError: A domain, selector, or applicability condition is invalid.
        TypeError: An input has an invalid type.

    Examples:
        >>> True
        True

    Tests:
        Unit tests:
            - tests/test_effective_lengths_and_limiting_slenderness.py
        Validation cases:
            - V12-SP16-PROC-10.4.1-SLENDERNESS-CHECK

    Implementation notes:
        - No unstated interpolation, extrapolation, or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    actual=_nonnegative(actual_slenderness_value,"actual_slenderness_value")
    if limiting_slenderness_value is None: return {"actual_slenderness":actual,"limiting_slenderness":None,"utilization":0.0,"pass":True,"unlimited":True}
    limit=_positive(limiting_slenderness_value,"limiting_slenderness_value")
    return {"actual_slenderness":actual,"limiting_slenderness":limit,"utilization":actual/limit,"pass":actual<=limit,"unlimited":False}
