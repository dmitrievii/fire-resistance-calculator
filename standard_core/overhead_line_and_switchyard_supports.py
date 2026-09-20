"""Section 16 checks for overhead-line, switchyard, and transport-contact-network supports."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_45 = json.loads((_DATA_DIR / "table_45_overhead_line_working_conditions.json").read_text(encoding="utf-8"))
_TABLE_46 = json.loads((_DATA_DIR / "table_46_support_deformation_limits.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-16.1-MATERIAL-ROUTE",
    "SP16-PROC-16.1A-GROUP",
    "SP16-PROC-16.2-BOLT-ROUTE",
    "SP16-PROC-16.4-TABLE-45",
    "SP16-PROC-16.4-NO-RY-RU-SUBSTITUTION",
    "SP16-PROC-16.5-PYRAMIDAL-MU",
    "SP16-PROC-16.7-BOLT-ECCENTRICITY",
    "SP16-PROC-16.8-AUXILIARIES",
    "SP16-PROC-16.10-BIAXIAL-GOVERNING",
    "SP16-PROC-16.11-TRIANGULAR-SHEAR-ROUTE",
    "SP16-PROC-16.12-ANGLE-ROUTING",
    "SP16-PROC-16.13-TRAVERSE-LENGTHS",
    "SP16-PROC-16.14-SLENDERNESS",
    "SP16-PROC-16.15-TABLE-46",
    "SP16-PROC-16.16-DIAPHRAGM",
    "SP16-PROC-16.17-SINGLE-BOLT-EDGE",
    "SP16-PROC-16.18-BRACE-SIDES",
    "SP16-PROC-16.19-SPLICE-BOLTS",
    "SP16-PROC-16.20-POLYGONAL-TUBE",
    "SP16-PROC-16-EXTERNAL-LOADS",
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


def _boolean(value: bool, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be boolean")
    return value


def _choice(value: str, allowed: set[str], name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value


def table_45_catalog() -> dict[str, Any]:
    """Audit ID: SP16-TBL-45. Summary: Return audited Table 45 data. Standard reference: СП 16.13330.2017, 16.4, Table 45, page 109. Parameters: None. Returns: Deep-copied catalogue. Assumptions: Explicit case selection. Sign convention: Not applicable. Unit convention: Dimensionless coefficients. Applicability: Elements listed in Table 45. Limitations: Coefficients do not apply to node connections. Raises: RuntimeError on damaged packaged data. Examples: ``table_45_catalog()['table']``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: No interpolation is required."""
    return json.loads(json.dumps(_TABLE_45, ensure_ascii=False))


def table_46_catalog() -> dict[str, Any]:
    """Audit ID: SP16-TBL-46. Summary: Return audited Table 46 deformation limits. Standard reference: СП 16.13330.2017, 16.15, Table 46, pages 113-114. Parameters: None. Returns: Deep-copied catalogue. Assumptions: Row and direction are engineer-selected. Sign convention: Deflections are magnitudes. Unit convention: Numerical cells are denominators of 1/n. Applicability: Listed VL and ORU supports, traverses, posts, and beams. Limitations: Equipment specifications may govern more strictly. Raises: RuntimeError on damaged packaged data. Examples: ``table_46_catalog()['table']``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Null cells preserve not-limited or not-applicable meanings."""
    return json.loads(json.dumps(_TABLE_46, ensure_ascii=False))


def section_16_applicability_route(structure_case: str) -> dict[str, Any]:
    """Summary: Classify Section 16 structure group and external references. Standard reference: СП 16.13330.2017, 16.1-16.2, page 108. Parameters: ``structure_case`` explicit normative category. Returns: Group and material/bolt routes. Assumptions: The engineer identifies function, voltage, height, welds, and connection type. Sign convention: Not applicable. Unit convention: Metadata only. Applicability: VL, ORU, and KS structures. Limitations: Steel grade, loads, and bolt class are not selected automatically. Raises: ValueError for unknown cases. Examples: ``section_16_applicability_route('GROUP_1_SPECIAL_WELDED_CROSSING_OVER_60M')``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Clause 16.3 remains explicitly excluded."""
    groups = {
        "GROUP_1_SPECIAL_WELDED_CROSSING_OVER_60M": 1,
        "GROUP_2_WELDED_VL_OR_HIGH_VOLTAGE_ORU_OR_KS_TENSION": 2,
        "GROUP_3_ORU_UP_TO_330KV_OR_KS_SUPPORTING": 3,
        "GROUP_4_AUXILIARY": 4,
    }
    case = _choice(structure_case, set(groups), "structure_case")
    group = groups[case]
    return {
        "group": group,
        "material_route": "Section 5 and Annex V",
        "bolt_route": "Table G.3 fatigue route for flange joints and VL supports over 60 m; otherwise non-fatigue route",
        "clause_16_3_status": "excluded_by_amendment_2",
        "external_loads_required": True,
    }


def table_45_working_condition_factor(case_id: str, *, applied_to_node_connection: bool = False) -> float:
    """Summary: Look up gamma_c from Table 45. Standard reference: СП 16.13330.2017, 16.4, Table 45. Parameters: Case identifier and node-connection flag. Returns: Dimensionless gamma_c. Assumptions: The case matches the printed row. Sign convention: Positive coefficient. Unit convention: Dimensionless. Applicability: Listed members only. Limitations: The table expressly excludes node connections. Raises: ValueError for excluded or unknown selection. Examples: ``table_45_working_condition_factor('FLAT_TRAVERSE_DIAGONAL_OR_STRUT')``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Exact lookup without interpolation."""
    _boolean(applied_to_node_connection, "applied_to_node_connection")
    if applied_to_node_connection:
        raise ValueError("Table 45 coefficients do not apply to element connections in nodes")
    if not isinstance(case_id, str):
        raise TypeError("case_id must be a string")
    for row in _TABLE_45["rows"]:
        if row["case_id"] == case_id:
            return float(row["gamma_c"])
    raise KeyError(f"Unknown Table 45 case_id: {case_id}")


def maximum_slenderness_eq201(length_mm: float, chord_axis_spacing_mm: float) -> float:
    """Summary: Calculate lambda_max = 2l/b. Standard reference: СП 16.13330.2017, 16.5, equation (201). Parameters: Geometric length and narrow-face chord-axis spacing. Returns: Geometric slenderness. Assumptions: Four-sided parallel-chord pin-ended member. Sign convention: Positive magnitudes. Unit convention: Consistent lengths, dimensionless result. Applicability: Equation (201). Limitations: Table 8 reduced-slenderness assembly remains separate. Raises: ValueError for non-positive inputs. Examples: ``maximum_slenderness_eq201(12000,2000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Direct transcription."""
    return 2.0 * _positive(length_mm, "length_mm") / _positive(chord_axis_spacing_mm, "chord_axis_spacing_mm")


def maximum_slenderness_eq202(length_mm: float, chord_axis_spacing_mm: float) -> float:
    """Summary: Calculate lambda_max = 2.5l/b. Standard reference: СП 16.13330.2017, 16.5, equation (202). Parameters: Geometric length and face chord-axis spacing. Returns: Geometric slenderness. Assumptions: Equilateral three-sided parallel-chord pin-ended member. Sign convention: Positive magnitudes. Unit convention: Consistent lengths, dimensionless result. Applicability: Equation (202). Limitations: Table 8 reduced-slenderness assembly remains separate. Raises: ValueError for non-positive inputs. Examples: ``maximum_slenderness_eq202(12000,2000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Direct transcription."""
    return 2.5 * _positive(length_mm, "length_mm") / _positive(chord_axis_spacing_mm, "chord_axis_spacing_mm")


def pyramidal_effective_length_factor_clause_16_5(upper_spacing_mm: float, lower_spacing_mm: float) -> float:
    """Summary: Calculate mu for a free-standing pyramidal support. Standard reference: СП 16.13330.2017, definition following equation (203). Parameters: Upper and lower narrow-face chord-axis spacings. Returns: Dimensionless mu. Assumptions: Lower spacing is the base spacing b_n. Sign convention: Positive lengths. Unit convention: Consistent lengths. Applicability: Clause 16.5 pyramidal route. Limitations: Irregular or non-pyramidal geometry is outside scope. Raises: ValueError for non-positive inputs. Examples: ``pyramidal_effective_length_factor_clause_16_5(1000,3000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: mu=1.25r^2-2.75r+3.5."""
    ratio = _positive(upper_spacing_mm, "upper_spacing_mm") / _positive(lower_spacing_mm, "lower_spacing_mm")
    return 1.25 * ratio * ratio - 2.75 * ratio + 3.5


def maximum_slenderness_eq203(height_mm: float, upper_spacing_mm: float, lower_spacing_mm: float) -> float:
    """Summary: Calculate lambda_max = 2 mu h / b_n. Standard reference: СП 16.13330.2017, 16.5, equation (203). Parameters: Height and upper/lower narrow-face spacings. Returns: Geometric slenderness. Assumptions: Free-standing pyramidal support. Sign convention: Positive magnitudes. Unit convention: Consistent lengths, dimensionless result. Applicability: Equation (203). Limitations: Does not derive geometry from a model. Raises: ValueError for non-positive inputs. Examples: ``maximum_slenderness_eq203(30000,1000,3000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Uses the printed mu polynomial."""
    h = _positive(height_mm, "height_mm")
    lower = _positive(lower_spacing_mm, "lower_spacing_mm")
    mu = pyramidal_effective_length_factor_clause_16_5(upper_spacing_mm, lower)
    return 2.0 * mu * h / lower


def relative_eccentricity_eq204(moment_n_mm: float, axial_force_n: float, chord_axis_spacing_mm: float, connection_beta: float) -> float:
    """Summary: Calculate m=3.46 beta M/(Nb). Standard reference: СП 16.13330.2017, 16.6, equation (204). Parameters: Moment, compression force, face spacing, and beta. Returns: Relative eccentricity. Assumptions: Bending plane is perpendicular to one face of an equilateral triangular member. Sign convention: Design magnitudes are non-negative. Unit convention: N, mm, Nmm; dimensionless result. Applicability: Equation (204). Limitations: Section 9 stability check remains separate. Raises: ValueError for invalid inputs. Examples: ``relative_eccentricity_eq204(1e8,1e6,1000,1.2)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: beta is 1.2 bolted and 1.0 welded."""
    return 3.46 * _positive(connection_beta, "connection_beta") * _nonnegative(moment_n_mm, "moment_n_mm") / (_positive(axial_force_n, "axial_force_n") * _positive(chord_axis_spacing_mm, "chord_axis_spacing_mm"))


def relative_eccentricity_eq205(moment_n_mm: float, axial_force_n: float, chord_axis_spacing_mm: float, connection_beta: float) -> float:
    """Summary: Calculate m=3 beta M/(Nb). Standard reference: СП 16.13330.2017, 16.6, equation (205). Parameters: Moment, compression force, face spacing, and beta. Returns: Relative eccentricity. Assumptions: Bending plane is parallel to one face of an equilateral triangular member. Sign convention: Design magnitudes are non-negative. Unit convention: N, mm, Nmm; dimensionless result. Applicability: Equation (205). Limitations: Section 9 stability check remains separate. Raises: ValueError for invalid inputs. Examples: ``relative_eccentricity_eq205(1e8,1e6,1000,1.2)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: beta is explicit."""
    return 3.0 * _positive(connection_beta, "connection_beta") * _nonnegative(moment_n_mm, "moment_n_mm") / (_positive(axial_force_n, "axial_force_n") * _positive(chord_axis_spacing_mm, "chord_axis_spacing_mm"))


def guyed_support_second_order_auxiliaries(length_mm: float, area_mm2: float, reduced_slenderness: float, axial_force_n: float, elastic_modulus_n_mm2: float) -> dict[str, float]:
    """Summary: Calculate f_n, I_ef, and delta used by equations (206)-(207). Standard reference: СП 16.13330.2017, 16.8-16.9, definitions following equation (206). Parameters: Length, area, reduced slenderness, axial force, and E. Returns: Auxiliary values. Assumptions: Compression force is positive and the printed equivalent-inertia relation applies. Sign convention: Positive compression. Unit convention: mm, mm2, N, N/mm2. Applicability: Guyed lattice posts of clauses 16.8-16.11. Limitations: f_q must be supplied by a beam calculation. Raises: ValueError when delta is non-positive. Examples: ``guyed_support_second_order_auxiliaries(12000,8000,120,1e6,206000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: f_n=0.0013l; I_ef=Al^2/lambda_ef^2; delta=1-0.1Nl^2/(EI_ef)."""
    length = _positive(length_mm, "length_mm")
    area = _positive(area_mm2, "area_mm2")
    slenderness = _positive(reduced_slenderness, "reduced_slenderness")
    force = _nonnegative(axial_force_n, "axial_force_n")
    modulus = _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2")
    inertia = area * length * length / (slenderness * slenderness)
    delta = 1.0 - 0.1 * force * length * length / (modulus * inertia)
    if delta <= 0.0:
        raise ValueError("Second-order delta must be greater than zero")
    return {"initial_bow_mm": 0.0013 * length, "equivalent_inertia_mm4": inertia, "delta": delta}


def guyed_rectangular_moment_eq206(first_order_midspan_moment_n_mm: float, connection_beta: float, axial_force_n: float, delta: float, transverse_deflection_mm: float, initial_bow_mm: float) -> float:
    """Summary: Calculate M=M_q+(beta N/delta)(f_q+f_n). Standard reference: СП 16.13330.2017, 16.8, equation (206). Parameters: First-order moment, beta, N, delta, and deflections. Returns: Amplified moment. Assumptions: All quantities refer to one bending plane and one load combination. Sign convention: Design magnitudes are non-negative. Unit convention: N, mm, Nmm. Applicability: Pin-ended rectangular lattice post with guys. Limitations: Beam deflection and first-order moment are external. Raises: ValueError for invalid inputs. Examples: ``guyed_rectangular_moment_eq206(1e8,1.2,1e6,0.9,10,15.6)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Direct equation (206)."""
    return _nonnegative(first_order_midspan_moment_n_mm, "first_order_midspan_moment_n_mm") + (_positive(connection_beta, "connection_beta") * _nonnegative(axial_force_n, "axial_force_n") / _positive(delta, "delta")) * (_nonnegative(transverse_deflection_mm, "transverse_deflection_mm") + _nonnegative(initial_bow_mm, "initial_bow_mm"))


def guyed_rectangular_shear_eq207(first_order_max_shear_n: float, connection_beta: float, axial_force_n: float, delta: float, length_mm: float, transverse_deflection_mm: float, initial_bow_mm: float) -> float:
    """Summary: Calculate Q=Q_max+3.14 beta N(f_q+f_n)/(delta l). Standard reference: СП 16.13330.2017, 16.9, equation (207). Parameters: First-order shear, beta, N, delta, length, and deflections. Returns: Constant design shear. Assumptions: Same plane and load combination as equation (206). Sign convention: Design magnitudes are non-negative. Unit convention: N and mm. Applicability: Rectangular lattice guyed post. Limitations: Does not distribute shear among lattice members. Raises: ValueError for invalid inputs. Examples: ``guyed_rectangular_shear_eq207(50000,1.2,1e6,0.9,12000,10,15.6)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Printed 3.14 is retained."""
    return _nonnegative(first_order_max_shear_n, "first_order_max_shear_n") + 3.14 * _positive(connection_beta, "connection_beta") * _nonnegative(axial_force_n, "axial_force_n") * (_nonnegative(transverse_deflection_mm, "transverse_deflection_mm") + _nonnegative(initial_bow_mm, "initial_bow_mm")) / (_positive(delta, "delta") * _positive(length_mm, "length_mm"))


def triangular_additional_chord_force_eq208(moment_x_n_mm: float, moment_y_n_mm: float, chord_axis_spacing_mm: float) -> dict[str, float]:
    """Summary: Evaluate both equation (208) candidates and select the larger N_ad. Standard reference: СП 16.13330.2017, 16.10, equation (208). Parameters: Biaxial moments and chord spacing. Returns: Two candidates and governing force. Assumptions: Moments are design magnitudes. Sign convention: Non-negative magnitudes. Unit convention: Nmm and mm produce N. Applicability: Equilateral triangular lattice guyed post. Limitations: Initial bow selection by plane remains an engineering route. Raises: ValueError for invalid inputs. Examples: ``triangular_additional_chord_force_eq208(1e8,5e7,1000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: The larger of 1.16Mx/b and 0.58Mx/b+My/b governs."""
    mx = _nonnegative(moment_x_n_mm, "moment_x_n_mm")
    my = _nonnegative(moment_y_n_mm, "moment_y_n_mm")
    b = _positive(chord_axis_spacing_mm, "chord_axis_spacing_mm")
    first = 1.16 * mx / b
    second = 0.58 * mx / b + my / b
    return {"candidate_1_n": first, "candidate_2_n": second, "governing_n": max(first, second)}


def bolted_angle_chord_factor_eq209(c_over_b: float, reduced_slenderness: float, n_md_over_n_m: float) -> float:
    """Summary: Calculate alpha_m by equation (209). Standard reference: СП 16.13330.2017, 16.12, equation (209). Parameters: c/b, reduced slenderness, and N_md/N_m. Returns: Force multiplier. Assumptions: Bolted equal-leg angle chord and printed geometry. Sign convention: Compression ratios are non-negative. Unit convention: Dimensionless. Applicability: 0.55<=c/b<=0.66, lambda<=3.5, ratio<=0.7. Limitations: Figure 15 case selection is external. Raises: ValueError outside domain. Examples: ``bolted_angle_chord_factor_eq209(0.6,2,0.3)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Lambda is capped at 3.5 as required."""
    x = _real(c_over_b, "c_over_b")
    if not 0.55 <= x <= 0.66:
        raise ValueError("equation (209) requires 0.55 <= c/b <= 0.66")
    lam = min(_nonnegative(reduced_slenderness, "reduced_slenderness"), 3.5)
    ratio = _nonnegative(n_md_over_n_m, "n_md_over_n_m")
    if ratio > 0.7:
        raise ValueError("equation (209) requires N_md/N_m <= 0.7")
    return 1.0 + (x - 0.55 + lam * (0.2 - 0.05 * lam)) * ratio


def bolted_angle_chord_factor_eq210(c_over_b: float, reduced_slenderness: float, n_md_over_n_m: float, *, figure_15_g_or_d: bool = False) -> float:
    """Summary: Calculate alpha_m by equation (210). Standard reference: СП 16.13330.2017, 16.12, equation (210). Parameters: c/b, reduced slenderness, force ratio, and figure-case flag. Returns: Force multiplier. Assumptions: Bolted equal-leg angle chord. Sign convention: Non-negative force ratio. Unit convention: Dimensionless. Applicability: 0.4<=c/b<0.55, or 0.45<=c/b<0.55 for Figure 15 g/d. Limitations: Node geometry is not inferred. Raises: ValueError outside domain. Examples: ``bolted_angle_chord_factor_eq210(0.5,2,0.2)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Printed ratio ceiling 2.33c/b-0.58 is enforced."""
    _boolean(figure_15_g_or_d, "figure_15_g_or_d")
    x = _real(c_over_b, "c_over_b")
    lower = 0.45 if figure_15_g_or_d else 0.4
    if not lower <= x < 0.55:
        raise ValueError(f"equation (210) requires {lower} <= c/b < 0.55")
    lam = min(_nonnegative(reduced_slenderness, "reduced_slenderness"), 3.5)
    ratio = _nonnegative(n_md_over_n_m, "n_md_over_n_m")
    if ratio > 2.33 * x - 0.58:
        raise ValueError("N_md/N_m exceeds the equation (210) domain")
    return 0.95 + 0.1 * x + (0.34 - 0.62 * x + lam * (0.2 - 0.05 * lam)) * ratio


def bolted_angle_brace_factor_eq211(c_over_b: float, n_md_over_n_m: float, *, bolt_line_ratio: float = 0.57) -> float:
    """Summary: Calculate alpha_d by equation (211). Standard reference: СП 16.13330.2017, 16.12, equation (211). Parameters: Chord c/b, force ratio, and brace bolt-line ratio. Returns: Force multiplier. Assumptions: Bolted brace attached on both sides of the chord leg. Sign convention: Non-negative force ratio. Unit convention: Dimensionless. Applicability: 0.55<=c/b<=0.66 and ratio<0.7. Limitations: Formula assumes brace bolt-line ratio 0.54-0.60; exactly 0.50 invokes a 5% increase. Raises: ValueError for unsupported geometry. Examples: ``bolted_angle_brace_factor_eq211(0.6,0.3)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: The 5% clause modifier is applied only at 0.50."""
    x = _real(c_over_b, "c_over_b")
    if not 0.55 <= x <= 0.66:
        raise ValueError("equation (211) requires 0.55 <= c/b <= 0.66")
    ratio = _nonnegative(n_md_over_n_m, "n_md_over_n_m")
    if ratio >= 0.7:
        raise ValueError("equation (211) requires N_md/N_m < 0.7")
    line = _real(bolt_line_ratio, "bolt_line_ratio")
    if not (0.54 <= line <= 0.60 or math.isclose(line, 0.5, abs_tol=1e-12)):
        raise ValueError("brace bolt-line ratio must be 0.54-0.60 or exactly 0.50")
    value = 1.18 - 0.36 * x + (1.8 * x - 0.86) * ratio
    return value * (1.05 if math.isclose(line, 0.5, abs_tol=1e-12) else 1.0)


def bolted_angle_brace_factor_eq212(c_over_b: float, n_md_over_n_m: float, *, bolt_line_ratio: float = 0.57, figure_15_g_or_d: bool = False) -> float:
    """Summary: Calculate alpha_d by equation (212). Standard reference: СП 16.13330.2017, 16.12, equation (212). Parameters: Chord c/b, force ratio, brace bolt-line ratio, and figure flag. Returns: Force multiplier. Assumptions: Bolted equal-leg angle brace. Sign convention: Non-negative ratio. Unit convention: Dimensionless. Applicability: Lower c/b branch. Limitations: Geometry classification is explicit. Raises: ValueError outside domain. Examples: ``bolted_angle_brace_factor_eq212(0.5,0.2)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Includes the printed 5% modifier at bolt-line ratio 0.50."""
    _boolean(figure_15_g_or_d, "figure_15_g_or_d")
    x = _real(c_over_b, "c_over_b")
    lower = 0.45 if figure_15_g_or_d else 0.4
    if not lower <= x < 0.55:
        raise ValueError(f"equation (212) requires {lower} <= c/b < 0.55")
    ratio = _nonnegative(n_md_over_n_m, "n_md_over_n_m")
    if ratio > 2.33 * x - 0.58:
        raise ValueError("N_md/N_m exceeds the equation (212) domain")
    line = _real(bolt_line_ratio, "bolt_line_ratio")
    if not (0.54 <= line <= 0.60 or math.isclose(line, 0.5, abs_tol=1e-12)):
        raise ValueError("brace bolt-line ratio must be 0.54-0.60 or exactly 0.50")
    value = 1.0 - 0.04 * x + (0.36 - 0.41 * x) * ratio
    return value * (1.05 if math.isclose(line, 0.5, abs_tol=1e-12) else 1.0)


def angle_member_eccentricity_factors_clause_16_12(member: str, connection: str, c_over_b: float, reduced_slenderness: float, n_md_over_n_m: float, *, bolt_line_ratio: float = 0.57, figure_15_g_or_d: bool = False, welded_centering: str = "centroids", broken_wire_combination: bool = False) -> dict[str, Any]:
    """Summary: Route clause 16.12 angle-member multipliers. Standard reference: СП 16.13330.2017, 16.12, equations (209)-(212) and following rules. Parameters: Member, connection, geometry, force ratio, and welded/accidental options. Returns: alpha_m/alpha_d and route. Assumptions: Explicit Figure 15 classification. Sign convention: Compression magnitudes. Unit convention: Dimensionless. Applicability: Single equal-leg angles in spatial supports. Limitations: Central-compression equation (7) is external. Raises: ValueError for inconsistent selections. Examples: ``angle_member_eccentricity_factors_clause_16_12('chord','bolted',0.6,2,0.3)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Multipliers are never permitted below 1.0."""
    kind = _choice(member, {"chord", "brace"}, "member")
    conn = _choice(connection, {"bolted", "welded"}, "connection")
    _boolean(broken_wire_combination, "broken_wire_combination")
    if conn == "welded":
        centering = _choice(welded_centering, {"centroids", "brace_axes_to_chord_heel"}, "welded_centering")
        if broken_wire_combination or centering == "centroids":
            value = 1.0
        else:
            value = 1.0 + 0.12 * _nonnegative(n_md_over_n_m, "n_md_over_n_m")
        return {"route": "welded", "alpha_m": max(1.0, value), "alpha_d": max(1.0, value)}
    if kind == "chord":
        value = bolted_angle_chord_factor_eq209(c_over_b, reduced_slenderness, n_md_over_n_m) if c_over_b >= 0.55 else bolted_angle_chord_factor_eq210(c_over_b, reduced_slenderness, n_md_over_n_m, figure_15_g_or_d=figure_15_g_or_d)
        return {"route": "equation_209" if c_over_b >= 0.55 else "equation_210", "alpha_m": max(1.0, value), "alpha_d": None}
    value = bolted_angle_brace_factor_eq211(c_over_b, n_md_over_n_m, bolt_line_ratio=bolt_line_ratio) if c_over_b >= 0.55 else bolted_angle_brace_factor_eq212(c_over_b, n_md_over_n_m, bolt_line_ratio=bolt_line_ratio, figure_15_g_or_d=figure_15_g_or_d)
    return {"route": "equation_211" if c_over_b >= 0.55 else "equation_212", "alpha_m": None, "alpha_d": max(1.0, value)}


def table_46_deformation_check(row_id: str, measure: str, actual_relative_deformation: float, *, load_mode: str = "normal", stricter_equipment_limit_denominator: float | None = None) -> dict[str, Any]:
    """Summary: Check a Table 46 relative deformation. Standard reference: СП 16.13330.2017, 16.15, Table 46. Parameters: Row, measure, actual ratio, mode, and optional stricter equipment denominator. Returns: Applicability, limit, utilization, and pass. Assumptions: Actual ratio is delta/height, delta/span, or delta/cantilever length as appropriate. Sign convention: Magnitude. Unit convention: Dimensionless. Applicability: Table 46 rows. Limitations: Emergency/mounting note and equipment specifications are explicit. Raises: KeyError or ValueError for unknown inputs. Examples: ``table_46_deformation_check('VL_ANCHOR_UNDER_60_ALONG_WIRES','top_deviation',0.008)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Numerical cells are interpreted as 1/n limits."""
    mode = _choice(load_mode, {"normal", "emergency", "erection"}, "load_mode")
    measure = _choice(measure, {"top_deviation", "vertical_span", "vertical_cantilever", "horizontal_span", "horizontal_cantilever"}, "measure")
    actual = _nonnegative(actual_relative_deformation, "actual_relative_deformation")
    row = next((r for r in _TABLE_46["rows"] if r["row_id"] == row_id), None)
    if row is None:
        raise KeyError(f"Unknown Table 46 row_id: {row_id}")
    is_vl = row_id.startswith("VL_")
    is_oru = row_id.startswith("SWITCHYARD_")
    if mode in {"emergency", "erection"} and ((is_oru and measure == "top_deviation") or (is_vl and measure != "top_deviation")):
        return {"applicable": False, "status": "not_limited_by_table_46_note_1", "limit_denominator": None, "utilization": None, "pass": None}
    denominator = row["limits"][measure]
    if denominator is None:
        null_meaning = row.get("null_meaning")
        if not isinstance(null_meaning, dict) or measure not in null_meaning:
            raise ValueError(
                f"Table 46 row {row_id!r} has a blank {measure!r} cell without explicit audited null semantics"
            )
        meaning = null_meaning[measure]
        if meaning not in {"not_limited", "not_applicable"}:
            raise ValueError(f"Unsupported Table 46 null semantics: {meaning!r}")
        return {"applicable": meaning != "not_applicable", "status": meaning, "limit_denominator": None, "utilization": None, "pass": None if meaning == "not_applicable" else True}
    governing = float(denominator)
    if stricter_equipment_limit_denominator is not None:
        extra = _positive(stricter_equipment_limit_denominator, "stricter_equipment_limit_denominator")
        if row_id not in {"EQUIPMENT_SUPPORT_POST", "EQUIPMENT_BEAM"}:
            raise ValueError("stricter equipment limit is only applicable to Table 46 rows 7 and 8")
        governing = max(governing, extra)
    utilization = actual * governing
    return {"applicable": True, "status": "checked", "limit_denominator": governing, "limit_relative_deformation": 1.0 / governing, "utilization": utilization, "pass": utilization <= 1.0}


def section_16_detailing_checks(*, traverse_member: str, panel_length_mm: float, alternate_chord_length_mm: float, actual_first_lower_brace_slenderness: float, support_system: str, actual_diaphragm_spacing_m: float, diaphragm_at_concentrated_loads: bool, diaphragm_at_chord_breaks: bool, edge_distance_mm: float, bolt_diameter_mm: float, permanently_tensioned_single_bolt_element: bool, braces_on_both_sides_of_chord_leg: bool, splice_total_bolts: int, splice_bolts_per_leg_each_side: int, splice_rows_per_leg_each_side: int, use_seven_bolt_exception: bool) -> dict[str, Any]:
    """Summary: Execute clauses 16.13-16.19 direct detailing checks. Standard reference: СП 16.13330.2017, 16.13-16.19, pages 113-114. Parameters: Traverse, slenderness, diaphragm, edge-distance, brace, and splice data. Returns: Structured checks and effective-length routes. Assumptions: Dimensions correspond to the printed definitions. Sign convention: Positive magnitudes. Unit convention: mm, m, and dimensionless slenderness. Applicability: Single-angle VL/ORU support detailing. Limitations: Table 40 bearing resistance and specific section radii remain linked checks. Raises: ValueError for invalid enumerations or counts. Examples: ``section_16_detailing_checks(...)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Seven-bolt exception reports gamma_b multiplier 0.85."""
    member = _choice(traverse_member, {"chord_primary", "chord_alternate", "diagonal", "strut"}, "traverse_member")
    panel = _positive(panel_length_mm, "panel_length_mm")
    alternate = _positive(alternate_chord_length_mm, "alternate_chord_length_mm")
    effective_routes = {
        "chord_primary": {"effective_length_mm": panel, "radius": "i_min"},
        "chord_alternate": {"effective_length_mm": alternate, "radius": "i_x"},
        "diagonal": {"effective_length_mm": panel, "radius": "i_min"},
        "strut": {"effective_length_mm": panel, "radius": "i_min"},
    }
    slenderness = _nonnegative(actual_first_lower_brace_slenderness, "actual_first_lower_brace_slenderness")
    system = _choice(support_system, {"free_standing", "guyed"}, "support_system")
    diaphragm_limit = 25.0 if system == "free_standing" else 15.0
    spacing = _nonnegative(actual_diaphragm_spacing_m, "actual_diaphragm_spacing_m")
    _boolean(diaphragm_at_concentrated_loads, "diaphragm_at_concentrated_loads")
    _boolean(diaphragm_at_chord_breaks, "diaphragm_at_chord_breaks")
    edge = _nonnegative(edge_distance_mm, "edge_distance_mm")
    diameter = _positive(bolt_diameter_mm, "bolt_diameter_mm")
    permanent = _boolean(permanently_tensioned_single_bolt_element, "permanently_tensioned_single_bolt_element")
    required_edge = 2.0 * diameter if permanent else 1.5 * diameter
    both = _boolean(braces_on_both_sides_of_chord_leg, "braces_on_both_sides_of_chord_leg")
    if isinstance(splice_total_bolts, bool) or not isinstance(splice_total_bolts, int) or splice_total_bolts < 2:
        raise ValueError("splice_total_bolts must be an integer of at least two")
    if isinstance(splice_bolts_per_leg_each_side, bool) or not isinstance(splice_bolts_per_leg_each_side, int) or splice_bolts_per_leg_each_side < 1:
        raise ValueError("splice_bolts_per_leg_each_side must be a positive integer")
    if isinstance(splice_rows_per_leg_each_side, bool) or not isinstance(splice_rows_per_leg_each_side, int) or splice_rows_per_leg_each_side < 1:
        raise ValueError("splice_rows_per_leg_each_side must be a positive integer")
    seven = _boolean(use_seven_bolt_exception, "use_seven_bolt_exception")
    row_limit = 7 if seven else 5
    splice_pass = splice_total_bolts % 2 == 0 and splice_bolts_per_leg_each_side <= row_limit and splice_rows_per_leg_each_side <= row_limit
    return {
        "clause_16_13_effective_length_route": effective_routes[member],
        "clause_16_14_first_lower_brace": {"limit": 160.0, "actual": slenderness, "utilization": slenderness / 160.0, "pass": slenderness <= 160.0},
        "clause_16_16_diaphragms": {"maximum_spacing_m": diaphragm_limit, "actual_spacing_m": spacing, "spacing_pass": spacing <= diaphragm_limit, "concentrated_load_locations_pass": diaphragm_at_concentrated_loads, "chord_break_locations_pass": diaphragm_at_chord_breaks, "pass": spacing <= diaphragm_limit and diaphragm_at_concentrated_loads and diaphragm_at_chord_breaks},
        "clause_16_17_single_bolt_edge": {"required_minimum_edge_distance_mm": required_edge, "actual_edge_distance_mm": edge, "bearing_note_2_table_40_required": edge < 1.5 * diameter, "pass": edge >= required_edge},
        "clause_16_18_brace_arrangement": {"pass": both},
        "clause_16_19_splice": {"even_total_bolt_count_pass": splice_total_bolts % 2 == 0, "maximum_per_leg_each_side": row_limit, "gamma_b_multiplier": 0.85 if seven else 1.0, "pass": splice_pass},
    }


def polygonal_tube_wall_relative_slenderness(width_mm: float, thickness_mm: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float) -> float:
    """Audit ID: SP16-PROC-16.20-POLYGONAL-TUBE. Summary: Calculate wall relative slenderness (b/t)sqrt(Ry/E). Standard reference: СП 16.13330.2017, 16.20, definition under equation (214). Parameters: Face width, thickness, Ry, and E. Returns: Relative wall slenderness. Assumptions: Effective flat face width is supplied. Sign convention: Positive magnitudes. Unit convention: mm and N/mm2; dimensionless result. Applicability: 8-12-sided tubes. Limitations: Does not calculate effective width from corner geometry. Raises: ValueError for non-positive inputs. Examples: ``polygonal_tube_wall_relative_slenderness(500,10,345,206000)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Direct definition."""
    return _positive(width_mm, "width_mm") / _positive(thickness_mm, "thickness_mm") * math.sqrt(_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") / _positive(elastic_modulus_n_mm2, "elastic_modulus_n_mm2"))


def polygonal_tube_critical_stress_eq214(relative_wall_slenderness: float, maximum_compressive_stress_n_mm2: float, minimum_stress_n_mm2: float, design_yield_resistance_n_mm2: float) -> dict[str, float]:
    """Summary: Calculate sigma_cr by equation (214). Standard reference: СП 16.13330.2017, 16.20, equation (214). Parameters: Wall slenderness, sigma1, sigma2, and Ry. Returns: beta, psi, used slenderness, raw and capped critical stress. Assumptions: Sigma1 is the largest compression; sigma2 is signed and may be tensile. Sign convention: Compression sigma1 positive; tension sigma2 negative. Unit convention: N/mm2 and dimensionless parameters. Applicability: 8-12-sided tubes. Limitations: Circular-tube requirements 11.2.1-11.2.2 remain separate. Raises: ValueError for invalid stress or radicand. Examples: ``polygonal_tube_critical_stress_eq214(1.5,100,-20,345)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Lambda is capped at 2.4 and sigma_cr at Ry exactly as printed."""
    lam = min(_nonnegative(relative_wall_slenderness, "relative_wall_slenderness"), 2.4)
    sigma1 = _positive(maximum_compressive_stress_n_mm2, "maximum_compressive_stress_n_mm2")
    sigma2 = _real(minimum_stress_n_mm2, "minimum_stress_n_mm2")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    beta = 0.58 + 1.81 * lam * lam
    radicand = beta * beta - 3.8 * lam * lam
    if radicand < -1e-12:
        raise ValueError("equation (214) square-root radicand is negative")
    radicand = max(0.0, radicand)
    psi = 1.0 + 0.033 * lam * (1.0 - sigma2 / sigma1)
    if psi <= 0.0:
        raise ValueError("equation (214) psi must be positive")
    raw = (beta - math.sqrt(radicand)) * psi * ry
    critical = min(raw, ry)
    return {"relative_wall_slenderness_used": lam, "beta": beta, "psi": psi, "raw_critical_stress_n_mm2": raw, "critical_stress_n_mm2": critical}


def polygonal_tube_wall_stability_utilization_eq213(maximum_compressive_stress_n_mm2: float, critical_stress_n_mm2: float, working_condition_factor: float) -> float:
    """Summary: Calculate sigma1/(sigma_cr gamma_c). Standard reference: СП 16.13330.2017, 16.20, equation (213). Parameters: Maximum compression, critical stress, and gamma_c. Returns: Utilization. Assumptions: Sigma_cr comes from equation (214). Sign convention: Compression magnitude positive. Unit convention: N/mm2; dimensionless result. Applicability: Polygonal tube wall stability. Limitations: Global support analysis is external. Raises: ValueError for invalid inputs. Examples: ``polygonal_tube_wall_stability_utilization_eq213(100,200,1)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: Pass criterion is utilization <=1."""
    return _nonnegative(maximum_compressive_stress_n_mm2, "maximum_compressive_stress_n_mm2") / (_positive(critical_stress_n_mm2, "critical_stress_n_mm2") * _positive(working_condition_factor, "working_condition_factor"))


def polygonal_tube_wall_stability_check(face_count: int, width_mm: float, thickness_mm: float, maximum_compressive_stress_n_mm2: float, minimum_stress_n_mm2: float, design_yield_resistance_n_mm2: float, elastic_modulus_n_mm2: float, working_condition_factor: float) -> dict[str, Any]:
    """Summary: Execute clauses 16.20 equations (213)-(214). Standard reference: СП 16.13330.2017, 16.20, equations (213)-(214), page 114. Parameters: Face count, wall geometry, stresses, material, and gamma_c. Returns: Slenderness, critical stress, utilization, and pass. Assumptions: Deformed-scheme stresses are supplied. Sign convention: Compression positive, tension negative. Unit convention: mm and N/mm2. Applicability: Polygonal tubes with 8-12 faces. Limitations: Round-tube clauses 11.2.1 and 11.2.2 require separate confirmation. Raises: ValueError outside face-count range. Examples: ``polygonal_tube_wall_stability_check(10,500,10,100,-20,345,206000,1)``. Tests: tests/test_overhead_line_and_switchyard_supports.py. Implementation notes: No interpolation is involved."""
    if isinstance(face_count, bool) or not isinstance(face_count, int) or not 8 <= face_count <= 12:
        raise ValueError("face_count must be an integer from 8 to 12")
    lam = polygonal_tube_wall_relative_slenderness(width_mm, thickness_mm, design_yield_resistance_n_mm2, elastic_modulus_n_mm2)
    critical = polygonal_tube_critical_stress_eq214(lam, maximum_compressive_stress_n_mm2, minimum_stress_n_mm2, design_yield_resistance_n_mm2)
    utilization = polygonal_tube_wall_stability_utilization_eq213(maximum_compressive_stress_n_mm2, critical["critical_stress_n_mm2"], working_condition_factor)
    return {"face_count": face_count, "relative_wall_slenderness": lam, **critical, "equation_213_utilization": utilization, "equation_213_pass": utilization <= 1.0, "linked_round_tube_requirements": ["11.2.1", "11.2.2"]}
