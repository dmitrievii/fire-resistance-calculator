"""Section 18 assessment and strengthening checks for existing steel structures."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_48 = json.loads((_DATA_DIR / "table_48_riveted_connection_resistances.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-18.1.1-CONDITION-CATEGORY",
    "SP16-PROC-18.1.2-MONITORING-AND-STRENGTHENING",
    "SP16-PROC-18.1.3-CALCULATION-EXEMPTION",
    "SP16-PROC-18.2.1-MATERIAL-EVIDENCE",
    "SP16-PROC-18.2.2-TEST-PROGRAM",
    "SP16-PROC-18.2.3-PRE1950-INSTITUTE",
    "SP16-PROC-18.2.4-EXISTING-STEEL-RESISTANCE",
    "SP16-PROC-18.2.5-EXISTING-WELD-RESISTANCE",
    "SP16-PROC-18.2.6-UNKNOWN-BOLT-RESISTANCE",
    "SP16-PROC-18.2.7-RIVETED-CONNECTION",
    "SP16-PROC-18.3.1-BRITTLE-STEEL-ROUTE",
    "SP16-PROC-18.3.2-ACTUAL-SCHEME-AND-DEFECTS",
    "SP16-PROC-18.3.3-STRENGTHEN-OR-REPLACE",
    "SP16-PROC-18.3.4-NO-STRENGTHENING-EXCEPTIONS",
    "SP16-PROC-18.3.5-18.3.10-STRENGTHENING-EXECUTION",
    "SP16-PROC-18.3.9-WELD-HEATING-STRESS-LIMIT",
    "SP16-PROC-18.3.11-COMMON-RESISTANCE",
    "SP16-PROC-18.3.12-INITIAL-STRESS-AND-WELD-CURVATURE",
    "SP16-PROC-18.3.13-GAMMA-N-GAMMA-M",
    "SP16-PROC-18.3.14-ALPHA-N-AND-WELD-DEFLECTION",
    "SP16-PROC-18.3.16-DEVIATION-ACCEPTANCE",
    "SP16-PROC-18-EXTERNAL-SURVEY-BOUNDARIES",
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


def _doc(summary: str, reference: str, mathematical: str, parameters: str, returns: str, applicability: str, limitations: str) -> str:
    return f"""Summary: {summary}\n\nStandard reference: СП 16.13330.2017, {reference}.\n\nMathematical form: {mathematical}\n\nParameters: {parameters}\n\nReturns: {returns}\n\nAssumptions: Engineer-selected survey evidence and categories are truthful.\n\nSign convention: Compression and governing stress magnitudes are positive unless a signed coordinate or stress is explicitly requested.\n\nUnit convention: N, mm, N/mm2 and dimensionless coefficients unless stated otherwise.\n\nApplicability: {applicability}\n\nLimitations: {limitations}\n\nRaises: TypeError for invalid types; ValueError for invalid domains or unsupported normative routes.\n\nExamples: See examples/reconstruction_assessment_example.json.\n\nTests: tests/test_reconstruction_assessment.py.\n\nImplementation notes: No missing survey, material, welding or Figure 24 data are inferred."""


def technical_condition_category_clause_18_1_1(
    *,
    defects_or_damage_present: bool,
    local_character_only: bool,
    restricts_normal_operation: bool,
    requires_monitoring_or_strengthening: bool,
    sudden_failure_or_global_instability_risk: bool,
) -> dict[str, Any]:
    """Summary: Classify the surveyed technical condition. Standard reference: СП 16.13330.2017, 18.1.1, page 118. Mathematical form: Deterministic decision route among normative, serviceable, limited-serviceable and emergency categories. Parameters: Five explicit survey findings. Returns: Category and required action. Assumptions: Findings come from a competent survey. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Existing buildings and structures under reconstruction. Limitations: Does not perform the survey. Raises: TypeError for non-boolean inputs. Examples: ``technical_condition_category_clause_18_1_1(defects_or_damage_present=False,local_character_only=True,restricts_normal_operation=False,requires_monitoring_or_strengthening=False,sudden_failure_or_global_instability_risk=False)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The most severe supported category governs."""
    values = {
        "defects_or_damage_present": defects_or_damage_present,
        "local_character_only": local_character_only,
        "restricts_normal_operation": restricts_normal_operation,
        "requires_monitoring_or_strengthening": requires_monitoring_or_strengthening,
        "sudden_failure_or_global_instability_risk": sudden_failure_or_global_instability_risk,
    }
    for name, value in values.items():
        _boolean(value, name)
    if sudden_failure_or_global_instability_risk:
        category = "emergency"
        action = "immediate safety measures and engineering decision on unloading, shoring, strengthening or replacement"
    elif requires_monitoring_or_strengthening or restricts_normal_operation:
        category = "limited_serviceable"
        action = "monitoring and/or strengthening with controlled continued operation"
    elif defects_or_damage_present:
        if not local_character_only:
            category = "limited_serviceable"
            action = "monitoring and engineering assessment because damage is not confirmed local"
        else:
            category = "serviceable"
            action = "normal operation permitted subject to documented local-defect assessment"
    else:
        category = "normative"
        action = "normal operation"
    return {"category": category, "required_action": action, "pass_for_unrestricted_operation": category in {"normative", "serviceable"}}


def strengthening_and_monitoring_route_clause_18_1_2(
    current_category: str,
    *,
    monitoring_program_confirmed: bool,
    smooth_load_transfer_to_strengthening_confirmed: bool,
    construction_stage_capacity_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check monitoring and strengthening-process obligations. Standard reference: СП 16.13330.2017, 18.1.2, page 118. Mathematical form: Evidence gate. Parameters: Technical category and three confirmations. Returns: Required actions and pass status. Assumptions: Category was established under 18.1.1. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Preserved structures before and during strengthening. Limitations: Does not design monitoring or temporary works. Raises: ValueError for an unsupported category. Examples: ``strengthening_and_monitoring_route_clause_18_1_2('limited_serviceable',monitoring_program_confirmed=True,smooth_load_transfer_to_strengthening_confirmed=True,construction_stage_capacity_confirmed=True)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Monitoring is mandatory for limited-serviceable structures before strengthening."""
    category = _choice(current_category, {"normative", "serviceable", "limited_serviceable", "emergency"}, "current_category")
    _boolean(monitoring_program_confirmed, "monitoring_program_confirmed")
    _boolean(smooth_load_transfer_to_strengthening_confirmed, "smooth_load_transfer_to_strengthening_confirmed")
    _boolean(construction_stage_capacity_confirmed, "construction_stage_capacity_confirmed")
    errors: list[str] = []
    if category == "limited_serviceable" and not monitoring_program_confirmed:
        errors.append("continuous or otherwise justified monitoring is required before strengthening")
    if category == "emergency":
        errors.append("emergency condition requires immediate safety measures before ordinary strengthening work")
    if not smooth_load_transfer_to_strengthening_confirmed:
        errors.append("smooth engagement of strengthening components is not confirmed")
    if not construction_stage_capacity_confirmed:
        errors.append("capacity during strengthening works is not confirmed")
    return {"category": category, "errors": errors, "pass": not errors}


def verification_calculation_exemption_clause_18_1_3(
    years_in_service: float,
    *,
    defects_or_damage_present: bool,
    operating_conditions_worsened: bool,
    loads_increased: bool,
    main_member_strengthening_required: bool,
) -> dict[str, Any]:
    """Summary: Determine whether a verification calculation may be omitted. Standard reference: СП 16.13330.2017, 18.1.3, page 118. Mathematical form: Exemption if service is at least 15 years and no adverse trigger exists. Parameters: Service duration and four triggers. Returns: Exemption decision and reasons. Assumptions: Original design used previously applicable rules. Sign convention: Not applicable. Unit convention: years. Applicability: Existing structures designed to former rules. Limitations: Does not waive survey obligations. Raises: ValueError for negative duration. Examples: ``verification_calculation_exemption_clause_18_1_3(20,defects_or_damage_present=False,operating_conditions_worsened=False,loads_increased=False,main_member_strengthening_required=False)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Any trigger requires calculation."""
    years = _nonnegative(years_in_service, "years_in_service")
    triggers = {
        "service_less_than_15_years": years < 15.0,
        "defects_or_damage_present": _boolean(defects_or_damage_present, "defects_or_damage_present"),
        "operating_conditions_worsened": _boolean(operating_conditions_worsened, "operating_conditions_worsened"),
        "loads_increased": _boolean(loads_increased, "loads_increased"),
        "main_member_strengthening_required": _boolean(main_member_strengthening_required, "main_member_strengthening_required"),
    }
    reasons = [name for name, active in triggers.items() if active]
    return {"verification_calculation_may_be_omitted": not reasons, "calculation_required_reasons": reasons}


def material_evidence_route_clause_18_2_1(
    *,
    factory_certificate_available: bool,
    sample_tests_completed: bool,
    executive_documentation_complete: bool,
    metal_quality_doubt_present: bool,
) -> dict[str, Any]:
    """Summary: Check the material-quality evidence route. Standard reference: СП 16.13330.2017, 18.2.1, page 118. Mathematical form: Certificate or testing evidence gate. Parameters: Four evidence flags. Returns: Required test route and pass status. Assumptions: Certificates are authentic and applicable. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Preserved steel structures. Limitations: Does not validate certificates or laboratory competence. Raises: TypeError for non-boolean input. Examples: ``material_evidence_route_clause_18_2_1(factory_certificate_available=True,sample_tests_completed=False,executive_documentation_complete=True,metal_quality_doubt_present=False)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Testing is required when documentation is insufficient or quality doubt exists."""
    for name, value in {
        "factory_certificate_available": factory_certificate_available,
        "sample_tests_completed": sample_tests_completed,
        "executive_documentation_complete": executive_documentation_complete,
        "metal_quality_doubt_present": metal_quality_doubt_present,
    }.items():
        _boolean(value, name)
    testing_required = (not factory_certificate_available) or (not executive_documentation_complete) or metal_quality_doubt_present
    return {"testing_required": testing_required, "pass": (not testing_required) or sample_tests_completed}


def metal_test_program_clause_18_2_2(
    steel_process: str,
    *,
    chemical_composition_tested: bool,
    tensile_properties_tested: bool,
    stress_strain_diagram_obtained: bool,
    impact_toughness_tested_if_required: bool,
    macro_microstructure_tested_if_required: bool,
    sulfur_percent: float,
    phosphorus_percent: float,
) -> dict[str, Any]:
    """Summary: Check the prescribed metal investigation program. Standard reference: СП 16.13330.2017, 18.2.2, pages 118-119. Mathematical form: Evidence checklist with impact-test exception. Parameters: Steel process, test evidence and S/P mass fractions. Returns: Missing tests and chemistry warnings. Assumptions: Laboratory measurements are valid. Sign convention: Not applicable. Unit convention: mass percent. Applicability: Existing steel under material investigation. Limitations: Does not set sample locations or counts. Raises: ValueError for unsupported process or negative percentages. Examples: ``metal_test_program_clause_18_2_2('open_hearth',chemical_composition_tested=True,tensile_properties_tested=True,stress_strain_diagram_obtained=True,impact_toughness_tested_if_required=True,macro_microstructure_tested_if_required=True,sulfur_percent=.03,phosphorus_percent=.03)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Impact toughness is not demanded for puddled or Bessemer steel and specified high-S/P carbon steel."""
    process = _choice(steel_process, {"puddled", "bessemer", "thomas", "open_hearth", "electric", "unknown_carbon"}, "steel_process")
    for name, value in {
        "chemical_composition_tested": chemical_composition_tested,
        "tensile_properties_tested": tensile_properties_tested,
        "stress_strain_diagram_obtained": stress_strain_diagram_obtained,
        "impact_toughness_tested_if_required": impact_toughness_tested_if_required,
        "macro_microstructure_tested_if_required": macro_microstructure_tested_if_required,
    }.items():
        _boolean(value, name)
    sulfur = _nonnegative(sulfur_percent, "sulfur_percent")
    phosphorus = _nonnegative(phosphorus_percent, "phosphorus_percent")
    impact_required = process not in {"puddled", "bessemer"} and not (sulfur > 0.55 or phosphorus > 0.050)
    missing: list[str] = []
    if not chemical_composition_tested:
        missing.append("chemical_composition")
    if not tensile_properties_tested:
        missing.append("tensile_properties")
    if not stress_strain_diagram_obtained:
        missing.append("stress_strain_diagram")
    if impact_required and not impact_toughness_tested_if_required:
        missing.append("impact_toughness")
    if not macro_microstructure_tested_if_required:
        missing.append("macro_microstructure_when_required")
    return {"impact_toughness_required": impact_required, "missing_evidence": missing, "pass": not missing}


def pre_1950_specialized_institute_route_clause_18_2_3(
    manufacture_period: str,
    *,
    specialized_research_institute_confirmed: bool,
    steel_production_method_identified: bool,
) -> dict[str, Any]:
    """Summary: Enforce the pre-1950 specialized-institute route. Standard reference: СП 16.13330.2017, 18.2.3, page 119. Mathematical form: Evidence gate. Parameters: Period and two confirmations. Returns: Requirement and pass status. Assumptions: Manufacture period is known. Sign convention: Not applicable. Unit convention: Categorical evidence. Applicability: Structures made before 1950. Limitations: Does not qualify institutions. Raises: ValueError for unsupported period. Examples: ``pre_1950_specialized_institute_route_clause_18_2_3('before_1950',specialized_research_institute_confirmed=True,steel_production_method_identified=True)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The route is not required for later construction."""
    period = _choice(manufacture_period, {"before_1950", "after_1950"}, "manufacture_period")
    _boolean(specialized_research_institute_confirmed, "specialized_research_institute_confirmed")
    _boolean(steel_production_method_identified, "steel_production_method_identified")
    required = period == "before_1950"
    passed = (not required) or (specialized_research_institute_confirmed and steel_production_method_identified)
    return {"specialized_institute_required": required, "pass": passed}


def existing_steel_design_resistances_clause_18_2_4(
    route: str,
    normative_or_test_yield_n_mm2: float,
    normative_or_test_ultimate_n_mm2: float,
    *,
    steel_process: str = "open_hearth",
) -> dict[str, float | str]:
    """Summary: Determine design resistances for preserved steel. Standard reference: СП 16.13330.2017, 18.2.4, page 119. Mathematical form: Ry=Ryn/gamma_m and Ru=Run/gamma_m with printed route-specific gamma_m and pre-1950 Ry cap. Parameters: Explicit evidence route, yield/ultimate values and process. Returns: gamma_m, Ry and Ru. Assumptions: Input minima correspond to the applicable certificate, standard or tests. Sign convention: Resistances are positive magnitudes. Unit convention: N/mm2. Applicability: Rolled products, cold-formed sections and tubes retained in reconstruction. Limitations: Does not identify the grade or governing product standard. Raises: ValueError for unsupported route or cap violation domain. Examples: ``existing_steel_design_resistances_clause_18_2_4('after_1982_certificate',355,510)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Ambiguous calendar boundary years are avoided by explicit route selection."""
    selected = _choice(route, {
        "before_1950_tests", "before_1982_certificate", "after_1982_certificate",
        "after_1988_statistical_certificate", "no_certificate_grade_identified", "steel_unidentified_tests",
    }, "route")
    ryn = _positive(normative_or_test_yield_n_mm2, "normative_or_test_yield_n_mm2")
    run = _positive(normative_or_test_ultimate_n_mm2, "normative_or_test_ultimate_n_mm2")
    gamma_by_route = {
        "before_1950_tests": 1.2,
        "before_1982_certificate": 1.15,
        "after_1982_certificate": 1.1,
        "after_1988_statistical_certificate": 1.05,
        "no_certificate_grade_identified": 1.15,
        "steel_unidentified_tests": 1.15,
    }
    gamma_m = gamma_by_route[selected]
    ry = ryn / gamma_m
    if selected == "before_1950_tests":
        process = _choice(steel_process, {"puddled", "bessemer", "thomas", "open_hearth", "electric"}, "steel_process")
        ry = min(ry, 170.0 if process == "puddled" else 210.0)
    elif selected == "steel_unidentified_tests":
        ry = min(ry, 210.0)
    return {"route": selected, "gamma_m": gamma_m, "design_yield_resistance_n_mm2": ry, "design_ultimate_resistance_n_mm2": run / gamma_m}


def existing_weld_resistance_defaults_clause_18_2_5(
    base_normative_ultimate_n_mm2: float,
    base_design_yield_n_mm2: float,
    construction_period: str,
) -> dict[str, float]:
    """Summary: Return conservative weld defaults when historical welding data are absent. Standard reference: СП 16.13330.2017, 18.2.5, page 119. Mathematical form: Rwf=Rwz=0.44Run; beta_f=0.7; beta_z=1.0; gamma_c=0.8; Rwy=0.55Ry or 0.85Ry. Parameters: Base Run, Ry and explicit before/after-1972 route. Returns: Default weld resistances and coefficients. Assumptions: Necessary historical welding data are unavailable. Sign convention: Resistances are positive magnitudes. Unit convention: N/mm2 and dimensionless coefficients. Applicability: Preserved welded connections under reconstruction. Limitations: Testing may justify refined values. Raises: ValueError for unsupported period. Examples: ``existing_weld_resistance_defaults_clause_18_2_5(510,345,'after_1972')``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The printed boundary is represented by categorical selection rather than invented calendar interpolation."""
    run = _positive(base_normative_ultimate_n_mm2, "base_normative_ultimate_n_mm2")
    ry = _positive(base_design_yield_n_mm2, "base_design_yield_n_mm2")
    period = _choice(construction_period, {"before_1972", "after_1972"}, "construction_period")
    return {
        "fillet_weld_metal_resistance_n_mm2": 0.44 * run,
        "fillet_fusion_boundary_resistance_n_mm2": 0.44 * run,
        "beta_f": 0.7,
        "beta_z": 1.0,
        "working_condition_factor": 0.8,
        "tension_butt_weld_resistance_n_mm2": (0.55 if period == "before_1972" else 0.85) * ry,
    }


def unknown_bolt_resistance_defaults_clause_18_2_6() -> dict[str, float]:
    """Summary: Return one-bolt resistance defaults when bolt strength class cannot be established. Standard reference: СП 16.13330.2017, 18.2.6, page 119. Mathematical form: Rbs=150 N/mm2 and Rbt=160 N/mm2. Parameters: None. Returns: Shear and tension design resistances. Assumptions: Bolt strength class is genuinely unidentifiable. Sign convention: Positive resistance magnitudes. Unit convention: N/mm2. Applicability: Preserved bolted connections. Limitations: Bearing resistance remains governed by clause 6.5. Raises: None. Examples: ``unknown_bolt_resistance_defaults_clause_18_2_6()``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Values are exact printed defaults."""
    return {"bolt_shear_design_resistance_n_mm2": 150.0, "bolt_tension_design_resistance_n_mm2": 160.0}


def table_48_catalog() -> dict[str, Any]:
    """Audit ID: SP16-TBL-48. Summary: Return audited Table 48 riveted-connection data. Standard reference: СП 16.13330.2017, 18.2.7, Table 48, page 120. Mathematical form: Exact categorical table. Parameters: None. Returns: Deep copy of the packaged table. Assumptions: Explicit group and steel selection. Sign convention: Positive resistance magnitudes. Unit convention: N/mm2. Applicability: Existing riveted connections. Limitations: No interpolation. Raises: RuntimeError if packaged data are damaged. Examples: ``table_48_catalog()['table']``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Group B/C definitions and head-type reduction are preserved as metadata."""
    return json.loads(json.dumps(_TABLE_48, ensure_ascii=False))


def table_48_rivet_resistance(
    limit_state: str,
    connection_group: str,
    rivet_steel: str,
    *,
    connected_steel_design_yield_n_mm2: float | None = None,
    countersunk_or_semicountersunk_head: bool = False,
) -> float:
    """Audit ID: SP16-TBL-48; SP16-PROC-18.2.7-RIVETED-CONNECTION. Summary: Look up Table 48 rivet shear, tension or bearing resistance. Standard reference: СП 16.13330.2017, 18.2.7, Table 48, page 120. Mathematical form: Exact lookup with 0.8 reduction for countersunk-head shear/bearing and prohibition of head tension. Parameters: Limit state, group, steel, optional connected Ry and head type. Returns: Design resistance. Assumptions: Group classification is correct. Sign convention: Positive resistance magnitude. Unit convention: N/mm2. Applicability: Existing riveted connections. Limitations: Unsupported table cells are rejected. Raises: ValueError for unavailable combinations. Examples: ``table_48_rivet_resistance('shear','B','St2_St3')``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Unknown hole/material evidence should be routed to group C and St2 externally."""
    state = _choice(limit_state, {"shear", "tension_head_pull_off", "bearing"}, "limit_state")
    group = _choice(connection_group, {"B", "C"}, "connection_group")
    steel = _choice(rivet_steel, {"St2_St3", "09G2"}, "rivet_steel")
    _boolean(countersunk_or_semicountersunk_head, "countersunk_or_semicountersunk_head")
    if state == "bearing":
        if connected_steel_design_yield_n_mm2 is None:
            raise ValueError("connected_steel_design_yield_n_mm2 is required for bearing")
        value = (2.0 if group == "B" else 1.7) * _positive(connected_steel_design_yield_n_mm2, "connected_steel_design_yield_n_mm2")
    elif state == "shear":
        values = {("B", "St2_St3"): 180.0, ("B", "09G2"): 220.0, ("C", "St2_St3"): 160.0}
        if (group, steel) not in values:
            raise ValueError("Table 48 has no shear value for the selected group and rivet steel")
        value = values[(group, steel)]
    else:
        if countersunk_or_semicountersunk_head:
            raise ValueError("countersunk or semicountersunk rivets are not permitted in tension")
        value = 120.0 if steel == "St2_St3" else 150.0
    if countersunk_or_semicountersunk_head and state in {"shear", "bearing"}:
        value *= 0.8
    return value


def rivet_connection_capacity_clause_18_2_7(
    limit_state: str,
    design_resistance_n_mm2: float,
    rivet_diameter_mm: float,
    *,
    shear_planes: int = 1,
    connected_thickness_sum_mm: float | None = None,
    working_condition_factor: float = 1.0,
) -> dict[str, float]:
    """Summary: Calculate one-rivet capacity using the clause 14.2.9 form referenced by 18.2.7. Standard reference: СП 16.13330.2017, 18.2.7 and 14.2.9, page 120. Mathematical form: Shear/tension use 0.785d2 area; bearing uses d sum(t); gamma_b=1. Parameters: Limit state, resistance, diameter, planes/thickness and gamma_c. Returns: Area and capacity. Assumptions: Table 48 resistance was selected correctly. Sign convention: Capacity is positive. Unit convention: N, mm and N/mm2. Applicability: Existing riveted connections. Limitations: Does not distribute forces in a rivet group. Raises: ValueError for invalid domains. Examples: ``rivet_connection_capacity_clause_18_2_7('shear',180,20,shear_planes=2)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The standard's substitutions Ab=Abn=Ar=0.785dr2 and db=dr are explicit."""
    state = _choice(limit_state, {"shear", "tension_head_pull_off", "bearing"}, "limit_state")
    resistance = _positive(design_resistance_n_mm2, "design_resistance_n_mm2")
    diameter = _positive(rivet_diameter_mm, "rivet_diameter_mm")
    gamma_c = _positive(working_condition_factor, "working_condition_factor")
    area = 0.785 * diameter * diameter
    if state == "shear":
        if isinstance(shear_planes, bool) or not isinstance(shear_planes, int) or shear_planes <= 0:
            raise ValueError("shear_planes must be a positive integer")
        capacity = resistance * area * shear_planes * gamma_c
    elif state == "tension_head_pull_off":
        capacity = resistance * area * gamma_c
    else:
        if connected_thickness_sum_mm is None:
            raise ValueError("connected_thickness_sum_mm is required for bearing")
        capacity = resistance * diameter * _positive(connected_thickness_sum_mm, "connected_thickness_sum_mm") * gamma_c
    return {"rivet_area_mm2": area, "capacity_n": capacity}


def existing_structure_strengthening_route_clauses_18_3_1_to_18_3_4(
    *,
    brittle_steel_temperature_condition_triggered: bool,
    post_reconstruction_stress_not_above_existing_confirmed: bool,
    actual_geometry_supports_and_defects_in_model_confirmed: bool,
    mandatory_code_checks_pass: bool,
    serviceability_exceedance_blocks_operation: bool,
    slenderness_exceedance_acceptable_by_test_or_calculation: bool,
) -> dict[str, Any]:
    """Summary: Route retain, strengthen or replace decisions under clauses 18.3.1-18.3.4. Standard reference: СП 16.13330.2017, 18.3.1-18.3.4, pages 120-121. Mathematical form: Evidence-based decision route. Parameters: Six explicit findings. Returns: Decision and errors. Assumptions: Survey and calculations are competent. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Existing structures under reconstruction. Limitations: Does not issue a professional survey conclusion. Raises: TypeError for non-boolean input. Examples: ``existing_structure_strengthening_route_clauses_18_3_1_to_18_3_4(...)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Brittle historical steel may remain only under the printed stress condition and formal conclusion route."""
    values = locals().copy()
    for name, value in values.items():
        _boolean(value, name)
    errors: list[str] = []
    if brittle_steel_temperature_condition_triggered and not post_reconstruction_stress_not_above_existing_confirmed:
        errors.append("brittle historical steel requires a formal conclusion on use, strengthening or replacement")
    if not actual_geometry_supports_and_defects_in_model_confirmed:
        errors.append("actual geometry, support conditions, defects, damage and corrosion are not reflected in the model")
    strengthening_required = not mandatory_code_checks_pass
    if serviceability_exceedance_blocks_operation:
        strengthening_required = True
    if not mandatory_code_checks_pass and slenderness_exceedance_acceptable_by_test_or_calculation:
        # The exception can apply only to a slenderness/serviceability issue, not arbitrary failed checks.
        errors.append("a generic failed mandatory check cannot be waived solely by the slenderness exception")
    decision = "strengthen_or_replace" if strengthening_required else "retain_without_strengthening"
    return {"decision": decision, "errors": errors, "pass": not errors}


def strengthening_execution_checks_clauses_18_3_5_to_18_3_10(
    *,
    construction_stage_capacity_confirmed: bool,
    additional_holes_and_welding_effects_included: bool,
    load_state_during_work_defined: bool,
    intermittent_flange_weld_used: bool,
    structure_group: int,
    design_temperature_c: float,
    environment: str,
    combined_connection_type: str,
) -> dict[str, Any]:
    """Summary: Check selected strengthening execution rules. Standard reference: СП 16.13330.2017, 18.3.5-18.3.10, page 121. Mathematical form: Evidence and applicability gate. Parameters: Construction-stage evidence, weld route, group, temperature, environment and combined connection. Returns: Errors and pass status. Assumptions: Strengthening method is engineer-selected. Sign convention: Temperature may be negative. Unit convention: degrees C and categorical evidence. Applicability: Strengthening works. Limitations: Does not design temporary supports, prestress or connections. Raises: ValueError for unsupported categories. Examples: ``strengthening_execution_checks_clauses_18_3_5_to_18_3_10(...)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Intermittent flange welds are restricted to groups 3-4, temperature at least -45 C, and non-/mildly aggressive environment."""
    for name, value in {
        "construction_stage_capacity_confirmed": construction_stage_capacity_confirmed,
        "additional_holes_and_welding_effects_included": additional_holes_and_welding_effects_included,
        "load_state_during_work_defined": load_state_during_work_defined,
        "intermittent_flange_weld_used": intermittent_flange_weld_used,
    }.items():
        _boolean(value, name)
    if isinstance(structure_group, bool) or not isinstance(structure_group, int) or structure_group not in {1, 2, 3, 4}:
        raise ValueError("structure_group must be 1, 2, 3, or 4")
    temperature = _real(design_temperature_c, "design_temperature_c")
    env = _choice(environment, {"non_aggressive", "mild", "medium", "strong"}, "environment")
    connection = _choice(combined_connection_type, {"none", "rivets_plus_friction", "rivets_plus_accuracy_A_bolts"}, "combined_connection_type")
    errors: list[str] = []
    if not construction_stage_capacity_confirmed:
        errors.append("construction-stage capacity is not confirmed")
    if not additional_holes_and_welding_effects_included:
        errors.append("section weakening and welding effects are not included")
    if not load_state_during_work_defined:
        errors.append("full, partial or complete unloading state is not defined")
    if intermittent_flange_weld_used and not (structure_group in {3, 4} and temperature >= -45.0 and env in {"non_aggressive", "mild"}):
        errors.append("intermittent flange weld is outside clause 18.3.7 applicability")
    return {"combined_connection_type": connection, "errors": errors, "pass": not errors}


def weld_heating_stress_limit_clause_18_3_9(structure_group: int, design_yield_resistance_n_mm2: float) -> float:
    """Summary: Return the maximum stress during welding-related heating. Standard reference: СП 16.13330.2017, 18.3.9, page 121. Mathematical form: 0.2Ry for group 1, 0.4Ry for group 2 and 0.8Ry for groups 3-4. Parameters: Structure group and Ry. Returns: Stress limit. Assumptions: The member is heated by welding during strengthening. Sign convention: Stress magnitude is positive. Unit convention: N/mm2. Applicability: Groups 1-4 under Annex V classification. Limitations: Does not calculate transient thermal stress. Raises: ValueError for unsupported group. Examples: ``weld_heating_stress_limit_clause_18_3_9(2,345)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Exact printed multipliers are used."""
    if isinstance(structure_group, bool) or not isinstance(structure_group, int) or structure_group not in {1, 2, 3, 4}:
        raise ValueError("structure_group must be 1, 2, 3, or 4")
    factor = {1: 0.2, 2: 0.4, 3: 0.8, 4: 0.8}[structure_group]
    return factor * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")


def common_or_separate_design_resistance_clause_18_3_11(
    existing_design_resistance_n_mm2: float,
    reinforcement_design_resistance_n_mm2: float,
) -> dict[str, Any]:
    """Summary: Decide whether one common design resistance may be used. Standard reference: СП 16.13330.2017, 18.3.11, page 122. Mathematical form: Use the lower resistance when the relative difference does not exceed 15 percent. Parameters: Existing and reinforcement resistances. Returns: Common/separate route. Assumptions: Resistances are applicable to the same check. Sign convention: Positive resistance magnitudes. Unit convention: N/mm2. Applicability: Members strengthened by section enlargement. Limitations: The clause does not prescribe a hidden averaging rule. Raises: ValueError for non-positive resistance. Examples: ``common_or_separate_design_resistance_clause_18_3_11(300,330)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Relative difference is referenced to the lower value, a conservative explicit interpretation."""
    old = _positive(existing_design_resistance_n_mm2, "existing_design_resistance_n_mm2")
    new = _positive(reinforcement_design_resistance_n_mm2, "reinforcement_design_resistance_n_mm2")
    low, high = sorted((old, new))
    relative_difference = (high - low) / low
    common = relative_difference <= 0.15 + 1e-12
    return {"relative_difference": relative_difference, "use_one_common_resistance": common, "common_resistance_n_mm2": low if common else None, "route": "common_lower_resistance" if common else "separate_material_resistances"}


def gamma_n_clause_18_3_13(
    *,
    welding_used: bool,
    initial_design_stress_n_mm2: float,
    design_yield_resistance_n_mm2: float,
) -> float:
    """Summary: Calculate gamma_N for equation (216). Standard reference: СП 16.13330.2017, 18.3.13, equation (216), page 122. Mathematical form: 0.95 without welding; 0.95-0.25 sigma_d/Ry with welding. Parameters: Welding flag, initial design stress and Ry. Returns: gamma_N. Assumptions: sigma_d is the clause-defined initial design stress magnitude. Sign convention: Stress magnitude is non-negative. Unit convention: N/mm2 and dimensionless. Applicability: Symmetrically strengthened centrally compressed members. Limitations: Does not derive sigma_d from a global model. Raises: ValueError if gamma_N is non-positive. Examples: ``gamma_n_clause_18_3_13(welding_used=True,initial_design_stress_n_mm2=100,design_yield_resistance_n_mm2=345)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: No undocumented lower bound is added."""
    _boolean(welding_used, "welding_used")
    sigma_d = _nonnegative(initial_design_stress_n_mm2, "initial_design_stress_n_mm2")
    ry = _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2")
    gamma_n = 0.95 if not welding_used else 0.95 - 0.25 * sigma_d / ry
    if gamma_n <= 0.0:
        raise ValueError("equation (216) gamma_N is non-positive")
    return gamma_n


def symmetric_compression_strength_utilization_eq216(
    axial_force_n: float,
    strengthened_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    gamma_n: float,
    working_condition_factor: float,
) -> float:
    """Summary: Check symmetric strengthening under central compression. Standard reference: СП 16.13330.2017, 18.3.13, equation (216), page 122. Mathematical form: N/(A Ry gamma_N gamma_c). Parameters: N, strengthened A, Ry, gamma_N and gamma_c. Returns: Utilization. Assumptions: Symmetric section enlargement and governing design force. Sign convention: Compression magnitude is positive. Unit convention: N, mm2 and N/mm2. Applicability: Centrally compressed symmetrically strengthened members. Limitations: Stability remains a separate check. Raises: ValueError for invalid denominators. Examples: ``symmetric_compression_strength_utilization_eq216(500000,3000,345,.9,1)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Pass criterion is utilization <=1."""
    return _nonnegative(axial_force_n, "axial_force_n") / (_positive(strengthened_area_mm2, "strengthened_area_mm2") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(gamma_n, "gamma_n") * _positive(working_condition_factor, "working_condition_factor"))


def gamma_m_clause_18_3_13(
    structure_group: int,
    axial_force_n: float,
    strengthened_area_mm2: float,
    design_yield_resistance_n_mm2: float,
    gamma_n: float,
) -> float:
    """Summary: Select gamma_M for equation (217). Standard reference: СП 16.13330.2017, 18.3.13, page 122. Mathematical form: 0.95 for group 1, 1.0 for groups 2-4; use gamma_N when N/(A Ry)>=0.6. Parameters: Group, N, A, Ry and gamma_N. Returns: gamma_M. Assumptions: Inputs refer to strengthened section. Sign convention: Compression magnitude is positive. Unit convention: N, mm2, N/mm2 and dimensionless. Applicability: Asymmetrically strengthened members. Limitations: Does not select the governing section point. Raises: ValueError for unsupported group. Examples: ``gamma_m_clause_18_3_13(1,500000,3000,345,.9)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The 0.6 boundary is included as printed."""
    if isinstance(structure_group, bool) or not isinstance(structure_group, int) or structure_group not in {1, 2, 3, 4}:
        raise ValueError("structure_group must be 1, 2, 3, or 4")
    ratio = _nonnegative(axial_force_n, "axial_force_n") / (_positive(strengthened_area_mm2, "strengthened_area_mm2") * _positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2"))
    return _positive(gamma_n, "gamma_n") if ratio >= 0.6 else (0.95 if structure_group == 1 else 1.0)


def asymmetric_strength_utilization_eq217(
    axial_force_n: float,
    strengthened_area_mm2: float,
    moment_x_n_mm: float,
    inertia_x_mm4: float,
    point_y_mm: float,
    moment_y_n_mm: float,
    inertia_y_mm4: float,
    point_x_mm: float,
    design_yield_resistance_n_mm2: float,
    gamma_m: float,
    working_condition_factor: float,
) -> dict[str, float]:
    """Summary: Check a governing point of an asymmetrically strengthened member. Standard reference: СП 16.13330.2017, 18.3.13, equation (217), page 122. Mathematical form: |N/A+Mx*y/Ix+My*x/Iy|/(Ry gamma_M gamma_c). Parameters: Axial force, section properties, signed moments/coordinates, Ry and factors. Returns: Signed stress and utilization. Assumptions: Moments are about strengthened-section principal axes and the caller supplies a governing point. Sign convention: Moment and coordinate signs are algebraic; utilization uses absolute stress. Unit convention: N, mm, mm2, mm4 and N/mm2. Applicability: Asymmetrically strengthened tension, compression and eccentric compression members. Limitations: Does not search the full section contour. Raises: ValueError for invalid denominators. Examples: ``asymmetric_strength_utilization_eq217(...)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Absolute stress prevents a signed favorable point from masking the governing check."""
    n = _real(axial_force_n, "axial_force_n")
    a = _positive(strengthened_area_mm2, "strengthened_area_mm2")
    stress = n / a + _real(moment_x_n_mm, "moment_x_n_mm") * _real(point_y_mm, "point_y_mm") / _positive(inertia_x_mm4, "inertia_x_mm4") + _real(moment_y_n_mm, "moment_y_n_mm") * _real(point_x_mm, "point_x_mm") / _positive(inertia_y_mm4, "inertia_y_mm4")
    utilization = abs(stress) / (_positive(design_yield_resistance_n_mm2, "design_yield_resistance_n_mm2") * _positive(gamma_m, "gamma_m") * _positive(working_condition_factor, "working_condition_factor"))
    return {"signed_stress_n_mm2": stress, "utilization": utilization}


def strengthened_member_stability_utilization_eq218(
    axial_force_n: float,
    phi_e: float,
    strengthened_area_mm2: float,
    effective_design_resistance_n_mm2: float,
    working_condition_factor: float,
) -> float:
    """Summary: Check in-plane stability of a strengthened solid-section member. Standard reference: СП 16.13330.2017, 18.3.14, equation (218), pages 122-123. Mathematical form: N/(phi_e A Ry,ef gamma_c). Parameters: N, phi_e, A, effective Ry and gamma_c. Returns: Utilization. Assumptions: phi_e is obtained from Table D.3 using strengthened-section slenderness and m_ef. Sign convention: Compression magnitude is positive. Unit convention: N, mm2 and N/mm2. Applicability: Centrally compressed or beam-column strengthened solid sections. Limitations: gamma_c must not exceed 0.9 and global analysis remains external. Raises: ValueError for gamma_c above 0.9. Examples: ``strengthened_member_stability_utilization_eq218(500000,.8,3000,320,.9)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Table D.3 lookup is available in the Section 9.2 module."""
    gamma_c = _positive(working_condition_factor, "working_condition_factor")
    if gamma_c > 0.9 + 1e-12:
        raise ValueError("clause 18.3.14 working-condition factor must not exceed 0.9")
    return _nonnegative(axial_force_n, "axial_force_n") / (_positive(phi_e, "phi_e") * _positive(strengthened_area_mm2, "strengthened_area_mm2") * _positive(effective_design_resistance_n_mm2, "effective_design_resistance_n_mm2") * gamma_c)


def reduced_relative_eccentricity_eq219(
    equivalent_eccentricity_mm: float,
    strengthened_area_mm2: float,
    compressed_fiber_section_modulus_mm3: float,
) -> float:
    """Summary: Calculate the relative eccentricity m_f. Standard reference: СП 16.13330.2017, 18.3.14, equation (219), page 123. Mathematical form: m_f=e_f A/W_c. Parameters: Equivalent eccentricity, area and compressed-fiber modulus. Returns: Relative eccentricity. Assumptions: W_c is for the most compressed fiber of the strengthened section. Sign convention: e_f may be signed. Unit convention: mm, mm2 and mm3. Applicability: Equation (218) Table D.3 route. Limitations: Does not apply the Table D.2 shape factor eta. Raises: ValueError for invalid section modulus. Examples: ``reduced_relative_eccentricity_eq219(10,3000,300000)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The output is the printed m_f before multiplication by eta."""
    return _real(equivalent_eccentricity_mm, "equivalent_eccentricity_mm") * _positive(strengthened_area_mm2, "strengthened_area_mm2") / _positive(compressed_fiber_section_modulus_mm3, "compressed_fiber_section_modulus_mm3")


def equivalent_eccentricity_eq220(
    axial_force_eccentricity_mm: float,
    post_strengthening_initial_deflection_mm: float,
    welding_deflection_factor: float,
    welding_residual_deflection_mm: float,
) -> float:
    """Summary: Calculate equivalent eccentricity of the strengthened member. Standard reference: СП 16.13330.2017, 18.3.14, equation (220), page 123. Mathematical form: e_f=e+f_j+k_fw f_w. Parameters: Axial-force eccentricity, post-strengthening initial deflection, k_fw and welding deflection. Returns: Signed equivalent eccentricity. Assumptions: All terms use one bending plane and sign convention. Sign convention: Algebraic signs are retained. Unit convention: mm. Applicability: Strengthened member stability. Limitations: Does not derive eccentricity from loads or centroid shift. Raises: ValueError for non-finite inputs. Examples: ``equivalent_eccentricity_eq220(5,8,.5,-2)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: k_fw is selected separately from the beneficial/adverse sign rule."""
    return _real(axial_force_eccentricity_mm, "axial_force_eccentricity_mm") + _real(post_strengthening_initial_deflection_mm, "post_strengthening_initial_deflection_mm") + _real(welding_deflection_factor, "welding_deflection_factor") * _real(welding_residual_deflection_mm, "welding_residual_deflection_mm")


def longitudinal_force_influence_alpha_n_clause_18_3_14(
    euler_critical_force_n: float,
    initial_axial_force_n: float,
    *,
    bending_member: bool = False,
) -> float:
    """Summary: Calculate alpha_N used in equations (221)-(222). Standard reference: СП 16.13330.2017, 18.3.14, page 123. Mathematical form: alpha_N=N_E/(N_E-N_0), or 1 for bending members. Parameters: Euler force, initial axial force and member route. Returns: alpha_N. Assumptions: N_E and N_0 refer to one bending plane. Sign convention: Compressive N_0 is positive. Unit convention: N and dimensionless. Applicability: Deflection terms of strengthened members. Limitations: Does not calculate N_E. Raises: ValueError when N_0>=N_E. Examples: ``longitudinal_force_influence_alpha_n_clause_18_3_14(1e6,2e5)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The printed bending-member exception is explicit."""
    _boolean(bending_member, "bending_member")
    if bending_member:
        return 1.0
    ne = _positive(euler_critical_force_n, "euler_critical_force_n")
    n0 = _nonnegative(initial_axial_force_n, "initial_axial_force_n")
    if n0 >= ne:
        raise ValueError("initial axial force must be below Euler critical force")
    return ne / (ne - n0)


def post_strengthening_initial_deflection_eq221(
    initial_deflection_mm: float,
    alpha_n: float,
    reinforcement_own_centroidal_inertia_sum_mm4: float,
    original_inertia_mm4: float,
    *,
    ignore_deformation_by_small_inertia_rule: bool = False,
    reinforcement_on_flat_surfaces_parallel_to_bending_plane: bool = False,
) -> float:
    """Summary: Calculate the retained initial deflection after strengthening. Standard reference: СП 16.13330.2017, 18.3.14, equation (221), pages 123-124. Mathematical form: f_j=f0[1-alpha_N sum(Ir)/(I0+sum(Ir))]. Parameters: f0, alpha_N, inertia sum, original inertia and two printed exceptions. Returns: Signed f_j. Assumptions: Simultaneously attached reinforcement components are included. Sign convention: Initial deflection sign is retained. Unit convention: mm and mm4. Applicability: Strengthened member equivalent eccentricity. Limitations: The caller confirms the small-inertia or flat-surface exception. Raises: ValueError for invalid inertia. Examples: ``post_strengthening_initial_deflection_eq221(10,1.2,1000,9000)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: No automatic geometry inference is performed."""
    f0 = _real(initial_deflection_mm, "initial_deflection_mm")
    _boolean(ignore_deformation_by_small_inertia_rule, "ignore_deformation_by_small_inertia_rule")
    _boolean(reinforcement_on_flat_surfaces_parallel_to_bending_plane, "reinforcement_on_flat_surfaces_parallel_to_bending_plane")
    if ignore_deformation_by_small_inertia_rule or reinforcement_on_flat_surfaces_parallel_to_bending_plane:
        return f0
    ir = _nonnegative(reinforcement_own_centroidal_inertia_sum_mm4, "reinforcement_own_centroidal_inertia_sum_mm4")
    i0 = _positive(original_inertia_mm4, "original_inertia_mm4")
    return f0 * (1.0 - _positive(alpha_n, "alpha_n") * ir / (i0 + ir))


def weld_shortening_parameter_v(kf_cm: float) -> float:
    """Audit ID: SP16-PROC-18.3.14-ALPHA-N-AND-WELD-DEFLECTION. Summary: Calculate the longitudinal-shortening parameter V for one weld. Standard reference: СП 16.13330.2017, 18.3.14, definition under equation (222), page 124. Mathematical form: V=0.04 k_f^2. Parameters: Weld leg in cm. Returns: V in the unit system required by equation (222). Assumptions: The printed centimeter convention is followed. Sign convention: Positive magnitude. Unit convention: k_f in cm. Applicability: Welding-induced residual deflection. Limitations: Does not model heat input or weld sequence. Raises: ValueError for non-positive leg. Examples: ``weld_shortening_parameter_v(.8)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The standard's explicit centimeter input is preserved."""
    kf = _positive(kf_cm, "kf_cm")
    return 0.04 * kf * kf


def welding_residual_deflection_eq222(
    average_weld_continuity_factor: float,
    alpha_n: float,
    effective_length: float,
    weld_terms: Iterable[dict[str, float]],
) -> float:
    """Summary: Calculate welding-induced residual deflection. Standard reference: СП 16.13330.2017, 18.3.14, equation (222), page 124. Mathematical form: f_w=alpha_w alpha_N l0^2/8 sum(n_i V_i y_i). Parameters: Continuity factor, alpha_N, length and iterable of n_i/V_i/y_i terms. Returns: Signed f_w. Assumptions: Figure 24 n_i values and compatible units are supplied explicitly. Sign convention: y_i and therefore each term are signed. Unit convention: One internally consistent equation-(222) unit system; the standard defines k_f in cm. Applicability: Welded section enlargement. Limitations: Figure 24 curves are not digitized or interpolated. Raises: ValueError for empty or malformed terms. Examples: ``welding_residual_deflection_eq222(1,1,100,[{'n_i':1,'v_i':.02,'y_i':2}])``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: This function implements the printed summation without inventing n_i."""
    alpha_w = _positive(average_weld_continuity_factor, "average_weld_continuity_factor")
    alpha = _positive(alpha_n, "alpha_n")
    length = _positive(effective_length, "effective_length")
    total = 0.0
    count = 0
    for term in weld_terms:
        if not isinstance(term, dict):
            raise TypeError("each weld term must be a dictionary")
        total += _real(term["n_i"], "n_i") * _real(term["v_i"], "v_i") * _real(term["y_i"], "y_i")
        count += 1
    if count == 0:
        raise ValueError("at least one weld term is required")
    return alpha_w * alpha * length * length * total / 8.0


def welding_deflection_factor_k_fw_clause_18_3_14(
    base_eccentricity_plus_initial_deflection_mm: float,
    welding_residual_deflection_mm: float,
) -> float:
    """Audit ID: SP16-PROC-18.3.14-ALPHA-N-AND-WELD-DEFLECTION. Summary: Select k_fw from the beneficial/adverse welding-deflection rule. Standard reference: СП 16.13330.2017, 18.3.14, page 125. Mathematical form: k_fw=0.5 when f_w has opposite sign and reduces absolute equivalent eccentricity; otherwise 1. Parameters: Base term and f_w. Returns: 0.5 or 1.0. Assumptions: Signs refer to one bending plane. Sign convention: Algebraic. Unit convention: mm. Applicability: Equation (220). Limitations: Zero terms are treated as not demonstrably unloading. Raises: ValueError for non-finite input. Examples: ``welding_deflection_factor_k_fw_clause_18_3_14(10,-2)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: Both opposite sign and actual absolute-value reduction are required."""
    base = _real(base_eccentricity_plus_initial_deflection_mm, "base_eccentricity_plus_initial_deflection_mm")
    fw = _real(welding_residual_deflection_mm, "welding_residual_deflection_mm")
    unloading = base * fw < 0.0 and abs(base + fw) < abs(base)
    return 0.5 if unloading else 1.0


def effective_design_resistance_eq223(existing_design_yield_resistance_n_mm2: float, composite_factor_k: float) -> float:
    """Summary: Calculate effective design resistance of the strengthened section. Standard reference: СП 16.13330.2017, 18.3.15, equation (223), page 125. Mathematical form: Ry,ef=Ry sqrt(k). Parameters: Existing-metal Ry and k. Returns: Effective Ry. Assumptions: k is obtained from equation (224). Sign convention: Positive resistance. Unit convention: N/mm2. Applicability: Stability of strengthened members. Limitations: Does not replace separate strength checks. Raises: ValueError for non-positive inputs. Examples: ``effective_design_resistance_eq223(300,1.1)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: No cap is introduced beyond the printed formula."""
    return _positive(existing_design_yield_resistance_n_mm2, "existing_design_yield_resistance_n_mm2") * math.sqrt(_positive(composite_factor_k, "composite_factor_k"))


def composite_resistance_factor_eq224(
    reinforcement_design_yield_resistance_n_mm2: float,
    existing_design_yield_resistance_n_mm2: float,
    original_area_mm2: float,
    strengthened_area_mm2: float,
    original_inertia_mm4: float,
    strengthened_inertia_mm4: float,
) -> float:
    """Summary: Calculate the composite resistance factor k. Standard reference: СП 16.13330.2017, 18.3.15, equation (224), page 125. Mathematical form: [Rya/Ry(1-A/Aa)+A/Aa][Rya/Ry(1-I/Ia)+I/Ia]. Parameters: Two resistances, original/strengthened areas and inertias. Returns: Dimensionless k. Assumptions: Properties use one stability plane and the strengthened values include the original member. Sign convention: Positive properties. Unit convention: N/mm2, mm2 and mm4. Applicability: Equation (223). Limitations: Does not account for partial composite action. Raises: ValueError if original properties exceed strengthened properties. Examples: ``composite_resistance_factor_eq224(345,300,2000,3000,8e6,12e6)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: The two printed brackets are retained exactly."""
    rya = _positive(reinforcement_design_yield_resistance_n_mm2, "reinforcement_design_yield_resistance_n_mm2")
    ry = _positive(existing_design_yield_resistance_n_mm2, "existing_design_yield_resistance_n_mm2")
    a = _positive(original_area_mm2, "original_area_mm2")
    aa = _positive(strengthened_area_mm2, "strengthened_area_mm2")
    i = _positive(original_inertia_mm4, "original_inertia_mm4")
    ia = _positive(strengthened_inertia_mm4, "strengthened_inertia_mm4")
    if a > aa or i > ia:
        raise ValueError("original area and inertia must not exceed strengthened values")
    ratio = rya / ry
    return (ratio * (1.0 - a / aa) + a / aa) * (ratio * (1.0 - i / ia) + i / ia)


def existing_deviation_acceptance_clause_18_3_16(
    *,
    listed_deviation_only: bool,
    damage_caused_by_deviation_absent: bool,
    adverse_operating_change_excluded: bool,
    capacity_and_stiffness_justified: bool,
    fatigue_and_brittle_fracture_measures_confirmed: bool,
) -> dict[str, Any]:
    """Summary: Check whether listed historical detailing deviations may remain without strengthening. Standard reference: СП 16.13330.2017, 18.3.16, page 125. Mathematical form: Five-condition evidence gate; section type b replaces c for central-compression stability when accepted. Parameters: Five confirmations. Returns: Acceptance and section-type substitution. Assumptions: The deviation is one of the clauses explicitly listed in 18.3.16. Sign convention: Not applicable. Unit convention: Boolean evidence. Applicability: Existing steel structures with specified historical deviations. Limitations: Does not verify the underlying drawings or fatigue assessment. Raises: TypeError for non-boolean input. Examples: ``existing_deviation_acceptance_clause_18_3_16(listed_deviation_only=True,damage_caused_by_deviation_absent=True,adverse_operating_change_excluded=True,capacity_and_stiffness_justified=True,fatigue_and_brittle_fracture_measures_confirmed=True)``. Tests: tests/test_reconstruction_assessment.py. Implementation notes: All conditions are mandatory."""
    values = locals().copy()
    for name, value in values.items():
        _boolean(value, name)
    accepted = all(values.values())
    return {"accepted_without_strengthening": accepted, "central_compression_section_type_substitution": "b_instead_of_c" if accepted else None, "pass": accepted}
