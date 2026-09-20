"""Stage N9 applicability-safe orchestration for current SP16 Section 12 fatigue design."""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import fatigue_design as s12

CURRENT_SP16_SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def _num(m: Mapping[str, Any], key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if key not in m:
        raise ValueError(f"fatigue_guided requires {key}")
    value = m[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{key} must be a finite real number")
    if positive and result <= 0.0:
        raise ValueError(f"{key} must be greater than zero")
    if nonnegative and result < 0.0:
        raise ValueError(f"{key} must be non-negative")
    return result


def _bool(m: Mapping[str, Any], key: str) -> bool:
    if key not in m or not isinstance(m[key], bool):
        raise ValueError(f"{key} must be boolean")
    return bool(m[key])


def _text(m: Mapping[str, Any], key: str) -> str:
    if key not in m or not isinstance(m[key], str) or not m[key].strip():
        raise ValueError(f"{key} must be a non-empty string")
    return str(m[key]).strip()


def _current_applicability(route: Mapping[str, Any]) -> dict[str, Any]:
    cycles = _num(route, "load_cycles", nonnegative=True)
    resonant = _bool(route, "resonant_vortex_excitation")
    return s12.fatigue_applicability_route_clause_12_1_1_12_1_3(cycles, resonant)


def _prerequisite_gate(route: Mapping[str, Any], *, crane: bool) -> list[str]:
    missing: list[str] = []
    required = [
        ("sp20_load_basis_confirmed", "12.1.1 loads established under SP 20.13330"),
        ("net_section_stress_without_dynamic_and_stability_coefficients_confirmed", "12.1.2 net-section stress basis without dynamic and phi/phi_b/phi_e"),
        ("same_loading_for_extreme_stresses_confirmed", "12.1.2 sigma_min and sigma_max from the same loading"),
        ("annex_k_case_selection_confirmed", "Annex K Table K.1 detail/group selection"),
    ]
    if crane:
        required.append(("crane_loads_sp20_confirmed", "12.2 crane loads established under SP 20.13330"))
    for key, label in required:
        if key not in route or route[key] is not True:
            missing.append(label)
    return missing


def _general_eq170_bundle(route: Mapping[str, Any], *, alpha_override: float | None = None) -> dict[str, Any]:
    case_id = _text(route, "annex_k_case_id")
    group = s12.annex_k_group(case_id)
    run = _num(route, "normative_ultimate_resistance_n_mm2", positive=True)
    ru = _num(route, "design_ultimate_resistance_n_mm2", positive=True)
    gamma_u = _num(route, "ultimate_resistance_safety_factor", positive=True)
    sigma_max = _num(route, "maximum_signed_stress_n_mm2")
    sigma_min = _num(route, "minimum_signed_stress_n_mm2")
    if sigma_max == 0.0:
        raise ValueError("maximum_signed_stress_n_mm2 must be non-zero for Table 36 rho/gamma_v")
    resistance = s12.fatigue_design_resistance_table35(group, run)
    if alpha_override is None:
        alpha = s12.fatigue_cycle_factor_alpha(_num(route, "load_cycles", positive=True), group)
        alpha_source = "12.1.2 equations (171)/(172) or alpha=0.77 at n>=3.9e6"
    else:
        alpha = float(alpha_override)
        alpha_source = "12.2 crane-runway alpha override"
    rho = s12.stress_asymmetry_ratio(sigma_max, sigma_min)
    gamma_v = s12.fatigue_asymmetry_factor_table36(sigma_max, sigma_min)
    eq170 = s12.fatigue_utilization_eq170(abs(sigma_max), alpha, resistance, gamma_v)
    cap = s12.fatigue_resistance_cap_check_clause_12_1_2(alpha, resistance, gamma_v, ru, gamma_u)
    return {
        "annex_k_case_id": case_id,
        "annex_k_element_group": group,
        "table_35_fatigue_resistance_n_mm2": resistance,
        "cycle_factor_alpha": alpha,
        "cycle_factor_source": alpha_source,
        "stress_asymmetry_ratio_rho": rho,
        "table_36_asymmetry_factor_gamma_v": gamma_v,
        "equation_170_utilization": eq170,
        "equation_170_pass": eq170 <= 1.0,
        "fatigue_resistance_cap_check": cap,
        "pass": eq170 <= 1.0 and bool(cap["pass"]),
        "governing_utilization": max(eq170, float(cap["cap_utilization"])),
    }


def _ordinary_route(route: Mapping[str, Any]) -> dict[str, Any]:
    applicability = _current_applicability(route)
    if not bool(applicability["ordinary_fatigue_required"]):
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "ordinary_fatigue_12_1_2",
            "applicability": applicability,
            "required": "current 12.1.1 low-cycle-fatigue method external; 12.1.3 is excluded by Change No. 6",
            "governing_utilization": None,
        }
    missing = _prerequisite_gate(route, crane=False)
    if missing:
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "ordinary_fatigue_12_1_2",
            "applicability": applicability,
            "missing_confirmations": missing,
            "governing_utilization": None,
        }
    general = _general_eq170_bundle(route)
    return {
        "status": "COMPLETE",
        "route": "ordinary_fatigue_12_1_2",
        "applicability": applicability,
        "general_fatigue_check": general,
        "governing_utilization": general["governing_utilization"],
        "pass": bool(general["pass"]),
    }


def _crane_route(route: Mapping[str, Any]) -> dict[str, Any]:
    applicability = _current_applicability(route)
    if not bool(applicability["ordinary_fatigue_required"]):
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "crane_runway_12_2",
            "applicability": applicability,
            "required": "n<1e5 remains a current-SP16 low-cycle-fatigue external boundary before 12.2 ordinary-fatigue evaluation",
            "governing_utilization": None,
        }
    missing = _prerequisite_gate(route, crane=True)
    if missing:
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "crane_runway_12_2",
            "applicability": applicability,
            "missing_confirmations": missing,
            "governing_utilization": None,
        }
    crane_group = _text(route, "crane_group")
    metallurgical = _bool(route, "crane_in_metallurgical_shop")
    alpha = s12.crane_runway_cycle_factor_clause_12_2(crane_group, metallurgical)
    general = _general_eq170_bundle(route, alpha_override=alpha)
    built_up = _bool(route, "built_up_crane_runway_beam")
    web: dict[str, Any] | None = None
    unresolved: list[str] = []
    governing = float(general["governing_utilization"])
    passed = bool(general["pass"])
    if built_up:
        if "equation_67_stresses_confirmed" not in route or route["equation_67_stresses_confirmed"] is not True:
            unresolved.append("12.2 equation (173) stresses must be determined by equations (67)")
        required_values = (
            "crane_flange_connection_type",
            "crane_web_zone_state",
            "crane_sigma_x_n_mm2",
            "crane_sigma_xy_n_mm2",
            "crane_local_sigma_y_n_mm2",
            "crane_flange_sigma_y_n_mm2",
        )
        missing_values = [key for key in required_values if key not in route]
        if missing_values:
            unresolved.append("missing equation-(173) inputs: " + ", ".join(missing_values))
        if not unresolved:
            connection = _text(route, "crane_flange_connection_type")
            state = _text(route, "crane_web_zone_state")
            rv_web = s12.crane_runway_web_fatigue_resistance_clause_12_2(connection, state)
            eta173 = s12.crane_runway_web_fatigue_utilization_eq173(
                _num(route, "crane_sigma_x_n_mm2", nonnegative=True),
                _num(route, "crane_sigma_xy_n_mm2", nonnegative=True),
                _num(route, "crane_local_sigma_y_n_mm2", nonnegative=True),
                _num(route, "crane_flange_sigma_y_n_mm2", nonnegative=True),
                rv_web,
            )
            web = {
                "fatigue_resistance_n_mm2": rv_web,
                "equation_173_utilization": eta173,
                "equation_173_pass": eta173 <= 1.0,
                "stress_source": "equations (67) confirmed",
            }
            governing = max(governing, eta173)
            passed = passed and eta173 <= 1.0
    if unresolved:
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": "crane_runway_12_2",
            "applicability": applicability,
            "general_fatigue_check": general,
            "crane_cycle_factor_alpha": alpha,
            "unresolved_requirements": unresolved,
            "governing_utilization": None,
        }
    return {
        "status": "COMPLETE",
        "route": "crane_runway_12_2",
        "applicability": applicability,
        "general_fatigue_check": general,
        "crane_cycle_factor_alpha": alpha,
        "built_up_upper_web_check": web,
        "governing_utilization": governing,
        "pass": passed,
    }


def fatigue_guided_workflow(case: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Evaluate exactly one current-SP16 Section 12 fatigue route with explicit fail-closed applicability gates.
    Standard reference:
        СП 16.13330.2017, Changes 1-6 through 09.12.2024, clauses 12.1-12.2, equations (170)-(173), Tables 35-36 and Annex K Table K.1.
    Parameters:
        case is a validated fatigue_guided mapping containing one selected route and the route-specific stress, material, cycle and provenance inputs.
    Returns:
        Auditable route result with applicability status, intermediate normative quantities, utilization checks, governing utilization and pass/fail where the route is complete.
    Assumptions:
        Stress ranges and load-cycle counts are supplied by the structural/loading analysis; Annex K detail classification is explicitly confirmed by the caller.
    Sign convention:
        Tensile and compressive stresses retain their supplied signs so rho=sigma_min/sigma_max is evaluated according to Table 36; utilization uses the governing stress magnitude required by equation (170).
    Unit convention:
        Stresses and resistances are N/mm2; load_cycles is a dimensionless count; alpha, rho, gamma_v and utilizations are dimensionless.
    Applicability:
        Ordinary fatigue under 12.1.2, crane-runway fatigue under 12.2, and the current low-cycle boundary of 12.1.1.
    Limitations:
        Does not derive SP20 load spectra, rainflow histories or cumulative damage, does not infer Annex K geometry classification, and does not invent a low-cycle-fatigue method after clause 12.1.3 was excluded by Change No. 6.
    Raises:
        ValueError for missing, non-finite, inconsistent or unsupported route inputs.
    Examples:
        See examples/fatigue_guided_example.json.
    Tests:
        tests/test_stage_n9_fatigue_workflows.py and tests/test_fatigue_design.py.
    Implementation notes:
        Crane alpha overrides and equation-(173) Eq-(67) stress provenance are explicit; resistance caps and external low-cycle obligations are never silently substituted.
    """
    if not isinstance(case, Mapping):
        raise ValueError("fatigue_guided case must be an object")
    if "route" not in case or not isinstance(case["route"], Mapping):
        raise ValueError("fatigue_guided requires route object")
    route = case["route"]
    kind = _text(route, "kind")
    if kind == "ordinary_fatigue_12_1_2":
        return _ordinary_route(route)
    if kind == "crane_runway_12_2":
        return _crane_route(route)
    if kind == "low_cycle_lt_1e5_12_1_1":
        applicability = _current_applicability(route)
        if bool(applicability["ordinary_fatigue_required"]):
            raise ValueError("low_cycle_lt_1e5_12_1_1 requires load_cycles < 1e5")
        return {
            "status": "INCOMPLETE_FAIL_CLOSED",
            "route": kind,
            "applicability": applicability,
            "required": "external low-cycle-fatigue calculation method; current clause 12.1.3 is excluded",
            "governing_utilization": None,
        }
    raise ValueError(f"Unsupported Stage N9 fatigue route: {kind}")
