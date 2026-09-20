"""Section 17 checks for antenna structures up to 500 m high."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_47 = json.loads((_DATA_DIR / "table_47_antenna_structure_working_conditions.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-17.1-MATERIAL-GROUP",
    "SP16-PROC-17.2-ROPE-SELECTION",
    "SP16-PROC-17.3-ZINC-TERMINATION",
    "SP16-PROC-17.4-WIRE-ROUTE",
    "SP16-PROC-17.5-GAMMA-M",
    "SP16-PROC-17.5-DESIGN-TENSION",
    "SP16-PROC-17.6-TABLE-47",
    "SP16-PROC-17.7-DEVIATION",
    "SP16-PROC-17.8-ERECTION-CONNECTION",
    "SP16-PROC-17.9-LATTICE-AND-DEFLECTION",
    "SP16-PROC-17.10-DIAPHRAGM",
    "SP16-PROC-17.11-FLANGE-BOLTS",
    "SP16-PROC-17.12-NODE-DETAILING",
    "SP16-PROC-17.13-GUY-ATTACHMENT",
    "SP16-PROC-17.14-FLEXIBLE-INSERT",
    "SP16-PROC-17.15-MECHANICAL-EVIDENCE",
    "SP16-PROC-17.16-DAMPER-ROUTE",
    "SP16-PROC-17.17-MARKING",
    "SP16-PROC-17.18-GALVANIZING",
    "SP16-PROC-17-EXTERNAL-LOADS",
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


def table_47_catalog() -> dict[str, Any]:
    """Audit ID: SP16-TBL-47. Summary: Return audited Table 47 data. Standard reference: СП 16.13330.2017, 17.6, Table 47, page 116. Parameters: None. Returns: Deep-copied catalogue. Assumptions: Explicit row selection. Sign convention: Not applicable. Unit convention: Dimensionless coefficients. Applicability: Antenna-structure elements listed in Table 47. Limitations: No geometry recognition. Raises: RuntimeError on damaged packaged data. Examples: ``table_47_catalog()['table']``. Tests: tests/test_antenna_structures.py. Implementation notes: Exact categorical transcription without interpolation."""
    return json.loads(json.dumps(_TABLE_47, ensure_ascii=False))


def antenna_structure_material_group_route_clause_17_1(
    component_group: int,
    steel_grade: str,
    *,
    is_pipe: bool,
    annex_v_grade_selection_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check the Section 17.1 group and basic steel exclusions. Standard reference: СП 16.13330.2017, 17.1, page 115. Parameters: Group 1-3, grade, pipe flag, and Annex V confirmation. Returns: Group description and compliance route. Assumptions: Component classification is engineer-selected. Sign convention: Not applicable. Unit convention: Metadata only. Applicability: Steel antenna structures up to 500 m. Limitations: Does not reproduce Annex V steel-selection tables. Raises: ValueError for excluded or unsupported selections. Examples: ``antenna_structure_material_group_route_clause_17_1(2,'C345',is_pipe=True,annex_v_grade_selection_confirmed=True)``. Tests: tests/test_antenna_structures.py. Implementation notes: C390K, C590, and C590K are explicitly excluded; pipe grades are limited to the printed list."""
    if isinstance(component_group, bool) or not isinstance(component_group, int) or component_group not in {1, 2, 3}:
        raise ValueError("component_group must be integer 1, 2, or 3")
    if not isinstance(steel_grade, str) or not steel_grade.strip():
        raise TypeError("steel_grade must be a non-empty string")
    _boolean(is_pipe, "is_pipe")
    _boolean(annex_v_grade_selection_confirmed, "annex_v_grade_selection_confirmed")
    grade = steel_grade.strip().upper().replace("С", "C")
    excluded = {"C390K", "C590", "C590K"}
    if grade in excluded:
        raise ValueError(f"steel grade {steel_grade} is excluded by clause 17.1")
    if is_pipe and grade not in {"C245", "C255", "C345", "C355"}:
        raise ValueError("straight-seam welded or seamless pipes require C245, C255, C345, or C355")
    if not annex_v_grade_selection_confirmed:
        raise ValueError("Annex V steel-grade selection must be confirmed")
    descriptions = {
        1: "guys, antenna wires, mechanical guy details, flanges and base shoes",
        2: "solid-web and lattice mast/tower shafts, lattice and diaphragms",
        3: "ladders, access platforms and antenna-equipment support steelwork",
    }
    return {
        "component_group": component_group,
        "group_description": descriptions[component_group],
        "steel_grade": grade,
        "is_pipe": is_pipe,
        "annex_v_route_confirmed": True,
        "connection_material_route": "Section 5; resistances by Section 6 and Annexes V and G",
        "pass": True,
    }


def steel_rope_selection_clause_17_2(
    design_force_kn: float,
    environment: str,
    rope_construction: str,
    core_type: str,
    *,
    built_in_nut_insulator: bool,
    radio_allows_nonmetallic_core: bool,
    round_wire_rope_capacity_kn: float,
    end_binding_length_increased_25_percent: bool,
) -> dict[str, Any]:
    """Summary: Route steel-rope selection requirements. Standard reference: СП 16.13330.2017, 17.2, page 115. Parameters: Force, environment, construction, core, insulator and capacity evidence. Returns: Required zinc group, rope route and pass status. Assumptions: Capacity is externally verified. Sign convention: Tensile-force magnitudes are positive. Unit convention: kN. Applicability: Guys and antenna-field elements. Limitations: Does not select a rope product or wire diameter. Raises: ValueError for inconsistent selections. Examples: ``steel_rope_selection_clause_17_2(300,'non_aggressive','spiral_nonspinning','metallic',built_in_nut_insulator=False,radio_allows_nonmetallic_core=False,round_wire_rope_capacity_kn=400,end_binding_length_increased_25_percent=False)``. Tests: tests/test_antenna_structures.py. Implementation notes: Spiral ropes are limited to 325 kN; locked-coil rope is required above round-wire capacity."""
    force = _positive(design_force_kn, "design_force_kn")
    env = _choice(environment, {"non_aggressive", "mild", "medium", "strong"}, "environment")
    construction = _choice(
        rope_construction,
        {"spiral_nonspinning", "round_strand_nonspinning_double_cross", "locked_coil", "spinning"},
        "rope_construction",
    )
    core = _choice(core_type, {"metallic", "nonmetallic"}, "core_type")
    _boolean(built_in_nut_insulator, "built_in_nut_insulator")
    _boolean(radio_allows_nonmetallic_core, "radio_allows_nonmetallic_core")
    _boolean(end_binding_length_increased_25_percent, "end_binding_length_increased_25_percent")
    round_capacity = _positive(round_wire_rope_capacity_kn, "round_wire_rope_capacity_kn")
    required_zinc_group = "ЖС" if env in {"medium", "strong"} else "СС"
    locked_coil_required = force > round_capacity
    errors: list[str] = []
    if construction == "spiral_nonspinning" and force > 325.0:
        errors.append("spiral rope is limited to design forces not exceeding 325 kN")
    if locked_coil_required and construction != "locked_coil":
        errors.append("locked-coil rope with Z-shaped or wedge-shaped galvanized wires is required")
    if construction == "spinning" and not end_binding_length_increased_25_percent:
        errors.append("spinning rope requires end bindings increased in length by 25 percent")
    if built_in_nut_insulator and radio_allows_nonmetallic_core and core != "nonmetallic":
        errors.append("nonmetallic core is required where radio requirements permit")
    return {
        "required_zinc_group": required_zinc_group,
        "required_wire_grade": 1,
        "use_largest_available_round_wire_diameters": True,
        "locked_coil_required": locked_coil_required,
        "selected_construction": construction,
        "selected_core": core,
        "errors": errors,
        "pass": not errors,
    }


def rope_end_zinc_alloy_check_clause_17_3(selected_alloy: str) -> dict[str, Any]:
    """Summary: Check the specified zinc alloy for socket or sleeve terminations. Standard reference: СП 16.13330.2017, 17.3, page 115. Parameters: Selected alloy designation. Returns: Required alloy and pass status. Assumptions: Termination uses zinc-alloy casting. Sign convention: Not applicable. Unit convention: Material designation. Applicability: Steel-rope ends in sockets or sleeves. Limitations: Does not qualify the casting process. Raises: TypeError for non-string input. Examples: ``rope_end_zinc_alloy_check_clause_17_3('ЦАМ9-1,5Л')``. Tests: tests/test_antenna_structures.py. Implementation notes: Exact printed alloy designation is retained."""
    if not isinstance(selected_alloy, str):
        raise TypeError("selected_alloy must be a string")
    normalized = selected_alloy.strip().upper().replace(" ", "")
    passed = normalized in {"ЦАМ9-1,5Л", "ZAM9-1.5L", "CAM9-1,5L"}
    return {"required_alloy": "ЦАМ9-1,5Л", "selected_alloy": selected_alloy, "pass": passed}


def antenna_wire_material_route_clause_17_4(
    *,
    annex_b_table_b2_selection_confirmed: bool,
    copper_wire_used: bool,
    technological_necessity_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check the antenna-wire material route. Standard reference: СП 16.13330.2017, 17.4, page 115. Parameters: Table B.2, copper-use, and necessity confirmations. Returns: Compliance status. Assumptions: Wire product is selected externally. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Antenna-field wires. Limitations: Table B.2 product data are not reproduced here. Raises: TypeError for non-boolean inputs. Examples: ``antenna_wire_material_route_clause_17_4(annex_b_table_b2_selection_confirmed=True,copper_wire_used=False,technological_necessity_confirmed=False)``. Tests: tests/test_antenna_structures.py. Implementation notes: Copper wire is allowed only for confirmed technological necessity."""
    _boolean(annex_b_table_b2_selection_confirmed, "annex_b_table_b2_selection_confirmed")
    _boolean(copper_wire_used, "copper_wire_used")
    _boolean(technological_necessity_confirmed, "technological_necessity_confirmed")
    passed = annex_b_table_b2_selection_confirmed and (not copper_wire_used or technological_necessity_confirmed)
    return {
        "annex_b_table_b2_selection_confirmed": annex_b_table_b2_selection_confirmed,
        "copper_wire_used": copper_wire_used,
        "technological_necessity_required": copper_wire_used,
        "technological_necessity_confirmed": technological_necessity_confirmed,
        "pass": passed,
    }


def wire_material_safety_factor_clause_17_5(wire_type: str, nominal_area_mm2: float | None = None) -> float:
    """Summary: Return gamma_m for antenna wires. Standard reference: СП 16.13330.2017, 17.5, pages 115-116. Parameters: Wire type and optional nominal area. Returns: Material safety factor gamma_m. Assumptions: Nominal sizes match the standard product catalogue. Sign convention: Positive coefficient. Unit convention: Dimensionless; nominal area in mm2. Applicability: Aluminium, copper, steel-aluminium, and bimetal steel-copper wires. Limitations: Unlisted steel-aluminium nominal-size gaps are rejected. Raises: ValueError for unsupported type or size. Examples: ``wire_material_safety_factor_clause_17_5('steel_aluminium',95)``. Tests: tests/test_antenna_structures.py. Implementation notes: No interpolation between printed size groups."""
    kind = _choice(wire_type, {"aluminium", "copper", "steel_aluminium", "bimetal_steel_copper"}, "wire_type")
    if kind in {"aluminium", "copper"}:
        return 2.5
    if kind == "bimetal_steel_copper":
        return 2.0
    if nominal_area_mm2 is None:
        raise ValueError("nominal_area_mm2 is required for steel-aluminium wire")
    area = _positive(nominal_area_mm2, "nominal_area_mm2")
    if math.isclose(area, 16.0, abs_tol=1e-12) or math.isclose(area, 25.0, abs_tol=1e-12):
        return 2.8
    if 35.0 <= area <= 95.0:
        return 2.5
    if area >= 120.0:
        return 2.2
    raise ValueError("steel-aluminium nominal area is not covered by the printed clause 17.5 ranges")


def wire_design_tension_force_clause_17_5(
    breaking_force_n: float,
    wire_type: str,
    nominal_area_mm2: float | None = None,
) -> dict[str, float]:
    """Summary: Calculate design tensile force as breaking force divided by gamma_m. Standard reference: СП 16.13330.2017, 17.5, pages 115-116. Parameters: Breaking force, wire type, and optional area. Returns: Gamma_m and design force. Assumptions: Breaking force comes from the governing product standard. Sign convention: Tensile-force magnitudes are positive. Unit convention: N and mm2. Applicability: Antenna wires covered by clause 17.5. Limitations: Does not verify the product certificate. Raises: ValueError for non-positive force or unsupported category. Examples: ``wire_design_tension_force_clause_17_5(250000,'aluminium')``. Tests: tests/test_antenna_structures.py. Implementation notes: Direct clause calculation."""
    force = _positive(breaking_force_n, "breaking_force_n")
    gamma_m = wire_material_safety_factor_clause_17_5(wire_type, nominal_area_mm2)
    return {"gamma_m": gamma_m, "design_tension_force_n": force / gamma_m}


def table_47_working_condition_factor(case_id: str) -> float:
    """Summary: Look up gamma_c from Table 47. Standard reference: СП 16.13330.2017, 17.6, Table 47, page 116. Parameters: Stable categorical case identifier. Returns: Working-condition factor gamma_c. Assumptions: Engineer selects the matching printed row. Sign convention: Positive coefficient. Unit convention: Dimensionless. Applicability: Listed antenna-structure elements and details. Limitations: No combined-row inference. Raises: KeyError for unknown case. Examples: ``table_47_working_condition_factor('RING_TYPE_FLANGE')``. Tests: tests/test_antenna_structures.py. Implementation notes: Exact lookup only."""
    if not isinstance(case_id, str):
        raise TypeError("case_id must be a string")
    for row in _TABLE_47["rows"]:
        if row["case_id"] == case_id:
            return float(row["gamma_c"])
    raise KeyError(f"Unknown Table 47 case_id: {case_id}")


def support_relative_deviation_check_clause_17_7(
    actual_deviation_mm: float,
    support_height_mm: float,
    load_case: str,
) -> dict[str, Any]:
    """Summary: Check relative support deviation. Standard reference: СП 16.13330.2017, 17.7, page 116. Parameters: Deviation, height, and load case. Returns: Limit, utilization, and pass status. Assumptions: No stricter project brief limit applies. Sign convention: Absolute deviation magnitude. Unit convention: Consistent lengths. Applicability: Wind/ice or unilateral antenna suspension without wind. Limitations: Other project-specific limits remain external. Raises: ValueError for invalid inputs. Examples: ``support_relative_deviation_check_clause_17_7(250,30000,'wind_or_ice')``. Tests: tests/test_antenna_structures.py. Implementation notes: Limits are 1/100 and 1/300."""
    deviation = abs(_real(actual_deviation_mm, "actual_deviation_mm"))
    height = _positive(support_height_mm, "support_height_mm")
    case = _choice(load_case, {"wind_or_ice", "unilateral_antenna_no_wind"}, "load_case")
    denominator = 100.0 if case == "wind_or_ice" else 300.0
    relative = deviation / height
    limit = 1.0 / denominator
    return {
        "load_case": case,
        "actual_relative_deviation": relative,
        "limit_denominator": denominator,
        "limit_relative_deviation": limit,
        "utilization": relative / limit,
        "pass": relative <= limit,
    }


def erection_connection_check_clause_17_8(
    accuracy_class: str,
    strength_class: str,
    *,
    sign_changing_force: bool,
    controlled_pretension_confirmed: bool,
    erection_weld_used: bool,
    installer_agreement_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check erection-connection requirements. Standard reference: СП 16.13330.2017, 17.8, page 116. Parameters: Bolt classes, force character, pretension, weld, and installer agreement. Returns: Compliance reasons and pass status. Assumptions: Connection transfers design action. Sign convention: Force sign classification is explicit. Unit convention: Categorical evidence. Applicability: Erection and flange connections of antenna structures. Limitations: Does not design the connection. Raises: ValueError for unsupported classes. Examples: ``erection_connection_check_clause_17_8('B','8.8',sign_changing_force=True,controlled_pretension_confirmed=True,erection_weld_used=False,installer_agreement_confirmed=False)``. Tests: tests/test_antenna_structures.py. Implementation notes: Accuracy class A or erection welding requires installer agreement."""
    accuracy = _choice(accuracy_class.upper(), {"A", "B"}, "accuracy_class")
    strength = _choice(strength_class, {"8.8", "10.9"}, "strength_class")
    _boolean(sign_changing_force, "sign_changing_force")
    _boolean(controlled_pretension_confirmed, "controlled_pretension_confirmed")
    _boolean(erection_weld_used, "erection_weld_used")
    _boolean(installer_agreement_confirmed, "installer_agreement_confirmed")
    errors: list[str] = []
    if sign_changing_force and not (controlled_pretension_confirmed or erection_weld_used):
        errors.append("sign-changing force requires controlled bolt pretension or erection welding")
    if (accuracy == "A" or erection_weld_used) and not installer_agreement_confirmed:
        errors.append("accuracy class A or erection welding requires installer agreement")
    return {
        "accuracy_class": accuracy,
        "strength_class": strength,
        "controlled_pretension_required": sign_changing_force and not erection_weld_used,
        "installer_agreement_required": accuracy == "A" or erection_weld_used,
        "errors": errors,
        "pass": not errors,
    }


def cross_lattice_and_platform_checks_clause_17_9(
    brace_slenderness: float,
    tied_at_intersection: bool,
    vertical_deflection_mm: float,
    horizontal_deflection_mm: float,
    span_mm: float,
) -> dict[str, Any]:
    """Summary: Check crossed-brace tying and 1/250 deflection limits. Standard reference: СП 16.13330.2017, 17.9, pages 116-117. Parameters: Slenderness, tie evidence, two deflections, and span. Returns: Separate compliance checks. Assumptions: Deflections are service values. Sign convention: Deflection magnitudes are absolute. Unit convention: Consistent lengths. Applicability: Crossed lattice, diaphragm struts, and platform members. Limitations: Does not calculate deflections. Raises: ValueError for invalid inputs. Examples: ``cross_lattice_and_platform_checks_clause_17_9(260,True,10,8,3000)``. Tests: tests/test_antenna_structures.py. Implementation notes: Intersection tying is mandatory only above slenderness 250."""
    slenderness = _nonnegative(brace_slenderness, "brace_slenderness")
    _boolean(tied_at_intersection, "tied_at_intersection")
    span = _positive(span_mm, "span_mm")
    vertical = abs(_real(vertical_deflection_mm, "vertical_deflection_mm"))
    horizontal = abs(_real(horizontal_deflection_mm, "horizontal_deflection_mm"))
    tie_required = slenderness > 250.0
    limit = span / 250.0
    return {
        "intersection_tie_required": tie_required,
        "intersection_tie_pass": (not tie_required) or tied_at_intersection,
        "deflection_limit_mm": limit,
        "vertical_utilization": vertical / limit,
        "horizontal_utilization": horizontal / limit,
        "vertical_pass": vertical <= limit,
        "horizontal_pass": horizontal <= limit,
        "pass": ((not tie_required) or tied_at_intersection) and vertical <= limit and horizontal <= limit,
    }


def diaphragm_check_clause_17_10(
    actual_spacing_mm: float,
    mean_section_size_mm: float,
    *,
    diaphragm_at_concentrated_loads: bool,
    diaphragm_at_chord_breaks: bool,
) -> dict[str, Any]:
    """Summary: Check lattice-support diaphragm spacing and locations. Standard reference: СП 16.13330.2017, 17.10, page 117. Parameters: Spacing, mean section size, and required-location evidence. Returns: Maximum spacing and pass status. Assumptions: Mean transverse size is externally determined. Sign convention: Positive dimensions. Unit convention: Consistent lengths. Applicability: Lattice antenna supports. Limitations: Does not design diaphragms. Raises: ValueError for non-positive dimensions. Examples: ``diaphragm_check_clause_17_10(6000,2500,diaphragm_at_concentrated_loads=True,diaphragm_at_chord_breaks=True)``. Tests: tests/test_antenna_structures.py. Implementation notes: Maximum spacing is three mean transverse-section sizes."""
    spacing = _positive(actual_spacing_mm, "actual_spacing_mm")
    mean_size = _positive(mean_section_size_mm, "mean_section_size_mm")
    _boolean(diaphragm_at_concentrated_loads, "diaphragm_at_concentrated_loads")
    _boolean(diaphragm_at_chord_breaks, "diaphragm_at_chord_breaks")
    maximum = 3.0 * mean_size
    return {
        "maximum_spacing_mm": maximum,
        "spacing_utilization": spacing / maximum,
        "spacing_pass": spacing <= maximum,
        "location_pass": diaphragm_at_concentrated_loads and diaphragm_at_chord_breaks,
        "pass": spacing <= maximum and diaphragm_at_concentrated_loads and diaphragm_at_chord_breaks,
    }


def pipe_flange_bolt_layout_check_clause_17_11(
    *,
    one_circle: bool,
    minimum_possible_circle_diameter: bool,
    equal_spacing: bool,
) -> dict[str, Any]:
    """Summary: Check pipe-flange bolt arrangement. Standard reference: СП 16.13330.2017, 17.11, page 117. Parameters: One-circle, minimum-diameter, and equal-spacing evidence. Returns: Pass status and missing conditions. Assumptions: Geometric evidence is supplied from drawings. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Bolted flange connections of pipes. Limitations: Does not calculate flange strength. Raises: TypeError for non-boolean inputs. Examples: ``pipe_flange_bolt_layout_check_clause_17_11(one_circle=True,minimum_possible_circle_diameter=True,equal_spacing=True)``. Tests: tests/test_antenna_structures.py. Implementation notes: All three printed requirements are conjunctive."""
    _boolean(one_circle, "one_circle")
    _boolean(minimum_possible_circle_diameter, "minimum_possible_circle_diameter")
    _boolean(equal_spacing, "equal_spacing")
    missing = [
        label
        for label, ok in [
            ("one_circle", one_circle),
            ("minimum_possible_circle_diameter", minimum_possible_circle_diameter),
            ("equal_spacing", equal_spacing),
        ]
        if not ok
    ]
    return {"missing_requirements": missing, "pass": not missing}


def truss_node_detailing_checks_clause_17_12(
    *,
    members_centered_on_chord_axis: bool,
    eccentricity_mm: float,
    chord_cross_section_size_mm: float,
    node_moment_analysis_performed: bool,
    slot_end_hole_diameter_mm: float,
    round_brace_diameter_mm: float,
) -> dict[str, Any]:
    """Summary: Check node centering, eccentricity, and drilled slot-end hole. Standard reference: СП 16.13330.2017, 17.12, page 117. Parameters: Centering evidence, eccentricity, chord size, moment analysis, and diameters. Returns: Thresholds and pass status. Assumptions: Dimensions refer to the printed node geometry. Sign convention: Eccentricity magnitude is non-negative. Unit convention: Consistent lengths. Applicability: Lattice nodes and slotted gussets for round bars. Limitations: Does not calculate node moments. Raises: ValueError for invalid dimensions. Examples: ``truss_node_detailing_checks_clause_17_12(members_centered_on_chord_axis=True,eccentricity_mm=20,chord_cross_section_size_mm=90,node_moment_analysis_performed=False,slot_end_hole_diameter_mm=24,round_brace_diameter_mm=20)``. Tests: tests/test_antenna_structures.py. Implementation notes: Eccentricity above one third is accepted only with node-moment analysis; hole diameter minimum is 1.2d."""
    _boolean(members_centered_on_chord_axis, "members_centered_on_chord_axis")
    _boolean(node_moment_analysis_performed, "node_moment_analysis_performed")
    ecc = _nonnegative(eccentricity_mm, "eccentricity_mm")
    chord = _positive(chord_cross_section_size_mm, "chord_cross_section_size_mm")
    hole = _positive(slot_end_hole_diameter_mm, "slot_end_hole_diameter_mm")
    brace = _positive(round_brace_diameter_mm, "round_brace_diameter_mm")
    eccentricity_limit = chord / 3.0
    eccentricity_pass = ecc <= eccentricity_limit or node_moment_analysis_performed
    hole_minimum = 1.2 * brace
    return {
        "members_centering_pass": members_centered_on_chord_axis,
        "eccentricity_limit_mm": eccentricity_limit,
        "eccentricity_requires_node_moment_analysis": ecc > eccentricity_limit,
        "eccentricity_pass": eccentricity_pass,
        "slot_end_hole_minimum_mm": hole_minimum,
        "slot_end_hole_pass": hole >= hole_minimum,
        "pass": members_centered_on_chord_axis and eccentricity_pass and hole >= hole_minimum,
    }


def guy_attachment_detailing_checks_clause_17_13(
    *,
    guy_centered_at_chord_strut_intersection: bool,
    eye_plate_stiffened_against_bending: bool,
    attachment_exceeds_transport_envelope: bool,
    separate_rigid_insert_provided: bool,
) -> dict[str, Any]:
    """Summary: Check guy centering, eye-plate stiffening, and transport insert route. Standard reference: СП 16.13330.2017, 17.13, page 117. Parameters: Four drawing-evidence flags. Returns: Requirements and pass status. Assumptions: Guy axis is represented by its chord. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Guy attachment nodes on lattice masts. Limitations: Does not design the eye plate or rigid diaphragm. Raises: TypeError for non-boolean inputs. Examples: ``guy_attachment_detailing_checks_clause_17_13(guy_centered_at_chord_strut_intersection=True,eye_plate_stiffened_against_bending=True,attachment_exceeds_transport_envelope=False,separate_rigid_insert_provided=False)``. Tests: tests/test_antenna_structures.py. Implementation notes: A separate rigid insert is required only when the attachment exceeds transport dimensions."""
    _boolean(guy_centered_at_chord_strut_intersection, "guy_centered_at_chord_strut_intersection")
    _boolean(eye_plate_stiffened_against_bending, "eye_plate_stiffened_against_bending")
    _boolean(attachment_exceeds_transport_envelope, "attachment_exceeds_transport_envelope")
    _boolean(separate_rigid_insert_provided, "separate_rigid_insert_provided")
    insert_required = attachment_exceeds_transport_envelope
    return {
        "guy_centering_pass": guy_centered_at_chord_strut_intersection,
        "eye_plate_stiffening_pass": eye_plate_stiffened_against_bending,
        "separate_rigid_insert_required": insert_required,
        "separate_rigid_insert_pass": (not insert_required) or separate_rigid_insert_provided,
        "pass": guy_centered_at_chord_strut_intersection and eye_plate_stiffened_against_bending and ((not insert_required) or separate_rigid_insert_provided),
    }


def flexible_cable_insert_check_clause_17_14(clear_length_mm: float, rope_diameter_mm: float) -> dict[str, float | bool]:
    """Summary: Check the flexible cable insert length. Standard reference: СП 16.13330.2017, 17.14, page 117. Parameters: Clear length between sleeve ends and rope diameter. Returns: Minimum length, utilization, and pass status. Assumptions: The insert connects the turnbuckle to the anchor device. Sign convention: Positive dimensions. Unit convention: Consistent lengths. Applicability: Guy-mast tensioning devices. Limitations: Does not design sockets or turnbuckles. Raises: ValueError for non-positive dimensions. Examples: ``flexible_cable_insert_check_clause_17_14(500,20)``. Tests: tests/test_antenna_structures.py. Implementation notes: Minimum clear length is 20 rope diameters."""
    length = _positive(clear_length_mm, "clear_length_mm")
    diameter = _positive(rope_diameter_mm, "rope_diameter_mm")
    minimum = 20.0 * diameter
    return {"minimum_clear_length_mm": minimum, "utilization": minimum / length, "pass": length >= minimum}


def mechanical_detail_evidence_clause_17_15(
    *,
    standard_detail_used: bool,
    strength_tested: bool,
    fatigue_tested: bool,
    threaded_tension_element: bool,
    rounded_thread_root_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check evidence for mechanical details and tension threads. Standard reference: СП 16.13330.2017, 17.15, page 117. Parameters: Standard-detail, test, threaded-element, and thread-root evidence. Returns: Missing evidence and pass status. Assumptions: Test records are authentic and applicable. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Mechanical antenna-structure details. Limitations: Does not inspect test reports or thread geometry. Raises: TypeError for non-boolean inputs. Examples: ``mechanical_detail_evidence_clause_17_15(standard_detail_used=True,strength_tested=True,fatigue_tested=True,threaded_tension_element=True,rounded_thread_root_confirmed=True)``. Tests: tests/test_antenna_structures.py. Implementation notes: Rounded root evidence is conditional on a threaded tension element."""
    flags = {
        "standard_detail_used": _boolean(standard_detail_used, "standard_detail_used"),
        "strength_tested": _boolean(strength_tested, "strength_tested"),
        "fatigue_tested": _boolean(fatigue_tested, "fatigue_tested"),
        "threaded_tension_element": _boolean(threaded_tension_element, "threaded_tension_element"),
        "rounded_thread_root_confirmed": _boolean(rounded_thread_root_confirmed, "rounded_thread_root_confirmed"),
    }
    missing = [name for name in ("standard_detail_used", "strength_tested", "fatigue_tested") if not flags[name]]
    if flags["threaded_tension_element"] and not flags["rounded_thread_root_confirmed"]:
        missing.append("rounded_thread_root_confirmed")
    return {**flags, "missing_evidence": missing, "pass": not missing}


def vibration_damper_distance_eq215(
    rope_or_wire_diameter_mm: float,
    pretension_n: float,
    mass_per_length_kg_m: float,
) -> float:
    """Summary: Calculate minimum damper distance s. Standard reference: СП 16.13330.2017, 17.16, equation (215), page 117. Parameters: Diameter d, pretension P, and mass per metre m. Returns: Minimum distance s. Assumptions: Inputs follow the printed units. Sign convention: Pretension is a positive magnitude. Unit convention: d in mm, P in N, m in kg/m, result s in m. Applicability: Guys, wires, and horizontal antenna-field ropes. Limitations: Empirical coefficient and units are retained exactly from the standard. Raises: ValueError for non-positive inputs. Examples: ``vibration_damper_distance_eq215(20,100000,2)``. Tests: tests/test_antenna_structures.py. Implementation notes: Implements s >= 0.41e-3 d sqrt(P/m); returned value is the minimum equality value."""
    d = _positive(rope_or_wire_diameter_mm, "rope_or_wire_diameter_mm")
    p = _positive(pretension_n, "pretension_n")
    m = _positive(mass_per_length_kg_m, "mass_per_length_kg_m")
    return 0.41e-3 * d * math.sqrt(p / m)


def vibration_damper_design_clause_17_16(
    rope_or_wire_diameter_mm: float,
    pretension_n: float,
    mass_per_length_kg_m: float,
    span_m: float,
    *,
    low_frequency_hz: float,
    high_frequency_hz: float,
    paired_sequential_dampers: bool,
    low_frequency_selected_from_fundamental_mode: bool,
    high_frequency_damper_above_low_at_distance_s: bool,
    dampers_installed: bool,
    galloping_risk_present: bool,
    free_length_modified_with_leashes: bool,
) -> dict[str, Any]:
    """Summary: Check the complete vibration-damper route. Standard reference: СП 16.13330.2017, 17.16, equation (215), page 117. Parameters: Equation inputs, span, frequencies, arrangement, installation, and galloping evidence. Returns: Minimum s and compliance status. Assumptions: Fundamental frequency is determined externally. Sign convention: Positive frequencies and dimensions. Unit convention: mm, N, kg/m, m, and Hz. Applicability: Guys and antenna-field wires/ropes. Limitations: Does not perform aeroelastic vibration analysis. Raises: ValueError for invalid ranges. Examples: ``vibration_damper_design_clause_17_16(20,100000,2,350,low_frequency_hz=2,high_frequency_hz=10,paired_sequential_dampers=True,low_frequency_selected_from_fundamental_mode=True,high_frequency_damper_above_low_at_distance_s=True,dampers_installed=True,galloping_risk_present=False,free_length_modified_with_leashes=False)``. Tests: tests/test_antenna_structures.py. Implementation notes: Low-frequency range is 1-2.5 Hz, high-frequency range is 4-40 Hz, and spans over 300 m require dampers regardless of calculation."""
    span = _positive(span_m, "span_m")
    low = _positive(low_frequency_hz, "low_frequency_hz")
    high = _positive(high_frequency_hz, "high_frequency_hz")
    for name, value in [
        ("paired_sequential_dampers", paired_sequential_dampers),
        ("low_frequency_selected_from_fundamental_mode", low_frequency_selected_from_fundamental_mode),
        ("high_frequency_damper_above_low_at_distance_s", high_frequency_damper_above_low_at_distance_s),
        ("dampers_installed", dampers_installed),
        ("galloping_risk_present", galloping_risk_present),
        ("free_length_modified_with_leashes", free_length_modified_with_leashes),
    ]:
        _boolean(value, name)
    minimum_s = vibration_damper_distance_eq215(rope_or_wire_diameter_mm, pretension_n, mass_per_length_kg_m)
    mandatory_by_span = span > 300.0
    errors: list[str] = []
    if not 1.0 <= low <= 2.5:
        errors.append("low-frequency damper must be within 1-2.5 Hz")
    if not 4.0 <= high <= 40.0:
        errors.append("high-frequency damper must be within 4-40 Hz")
    if not paired_sequential_dampers:
        errors.append("paired low- and high-frequency dampers must be installed sequentially")
    if not low_frequency_selected_from_fundamental_mode:
        errors.append("low-frequency damper must be selected from the fundamental frequency")
    if not high_frequency_damper_above_low_at_distance_s:
        errors.append("high-frequency damper must be above the low-frequency damper at distance s")
    if mandatory_by_span and not dampers_installed:
        errors.append("span above 300 m requires dampers regardless of calculation")
    if galloping_risk_present and not free_length_modified_with_leashes:
        errors.append("galloping mitigation requires modification of free length with leashes")
    return {
        "equation_215_minimum_distance_s_m": minimum_s,
        "mandatory_by_span_over_300_m": mandatory_by_span,
        "errors": errors,
        "pass": not errors,
    }


def obstruction_marking_and_lighting_check_clause_17_17(confirmed: bool) -> dict[str, Any]:
    """Summary: Record evidence of obstacle marking and lighting. Standard reference: СП 16.13330.2017, 17.17, page 117. Parameters: Compliance confirmation. Returns: External-reference route and pass status. Assumptions: Governing marking rules are identified externally. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Radio antenna structures. Limitations: Does not reproduce aviation-marking regulations. Raises: TypeError for non-boolean input. Examples: ``obstruction_marking_and_lighting_check_clause_17_17(True)``. Tests: tests/test_antenna_structures.py. Implementation notes: This is an evidence gate, not a design calculation."""
    value = _boolean(confirmed, "confirmed")
    return {"external_marking_and_lighting_requirements_confirmed": value, "pass": value}


def galvanizing_check_clause_17_18(
    *,
    guy_mechanical_details_galvanized: bool,
    insulator_fittings_galvanized: bool,
    fasteners_galvanized: bool,
) -> dict[str, Any]:
    """Summary: Check galvanizing evidence for specified details. Standard reference: СП 16.13330.2017, 17.18, pages 117-118. Parameters: Galvanizing evidence for three categories. Returns: Missing categories and pass status. Assumptions: Coating specifications are externally verified. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Guy details, insulator fittings, and fasteners. Limitations: Does not inspect coating thickness or quality. Raises: TypeError for non-boolean inputs. Examples: ``galvanizing_check_clause_17_18(guy_mechanical_details_galvanized=True,insulator_fittings_galvanized=True,fasteners_galvanized=True)``. Tests: tests/test_antenna_structures.py. Implementation notes: All three categories are mandatory."""
    values = {
        "guy_mechanical_details_galvanized": _boolean(guy_mechanical_details_galvanized, "guy_mechanical_details_galvanized"),
        "insulator_fittings_galvanized": _boolean(insulator_fittings_galvanized, "insulator_fittings_galvanized"),
        "fasteners_galvanized": _boolean(fasteners_galvanized, "fasteners_galvanized"),
    }
    missing = [name for name, ok in values.items() if not ok]
    return {**values, "missing_categories": missing, "pass": not missing}
