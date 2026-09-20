"""Stage N7 applicability-safe orchestration for SP16 Section 10 effective lengths and limiting slenderness."""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import effective_lengths_and_limiting_slenderness as s10


def _num(m: Mapping[str, Any], key: str, *, positive: bool=False, nonnegative: bool=False) -> float:
    if key not in m:
        raise ValueError(f"effective_length_guided requires {key}")
    v=m[key]
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)):
        raise ValueError(f"{key} must be a finite real number")
    x=float(v)
    if positive and x<=0.0: raise ValueError(f"{key} must be greater than zero")
    if nonnegative and x<0.0: raise ValueError(f"{key} must be non-negative")
    return x


def _basis(m: Mapping[str, Any], key: str) -> str:
    if key not in m or not isinstance(m[key],str) or not m[key].strip():
        raise ValueError(f"{key} must be a non-empty provenance string")
    return str(m[key]).strip()


def _external_length(route: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
    ext=route.get("external_effective_length")
    if not isinstance(ext,Mapping):
        return {"status":"EXTERNAL_EFFECTIVE_LENGTH_REQUIRED","effective_length_mm":None,"reason":reason}
    value=_num(ext,"value_mm",positive=True)
    basis=_basis(ext,"basis")
    return {"status":"EXTERNAL_EFFECTIVE_LENGTH_USED","effective_length_mm":value,"source":basis,"reason":reason}


def _table31_mu(route: Mapping[str, Any]) -> dict[str, Any]:
    method=str(route["mu_method"])
    if method=="eq141_sway_p0":
        n=_num(route,"n_parameter",positive=True)
        mu=s10.sway_frame_mu_eq141(n)
        return {"mu":mu,"method":"equation_141_corrected_by_FCS_letter_Исх-8076","n":n}
    if method=="eq142_sway_p_inf":
        n=_num(route,"n_parameter",nonnegative=True)
        mu=s10.sway_frame_mu_eq142(n)
        return {"mu":mu,"method":"equation_142","n":n}
    if method=="eq143_sway_n_le_0_2":
        p=_num(route,"p_parameter",positive=True); n=_num(route,"n_parameter",nonnegative=True)
        mu=s10.sway_frame_mu_eq143(p,n)
        return {"mu":mu,"method":"equation_143","p":p,"n":n}
    if method=="eq144_sway_n_gt_0_2":
        p=_num(route,"p_parameter",positive=True); n=_num(route,"n_parameter",positive=True)
        mu=s10.sway_frame_mu_eq144(p,n)
        return {"mu":mu,"method":"equation_144","p":p,"n":n}
    if method=="eq145_nonsway":
        p=_num(route,"p_parameter",nonnegative=True); n=_num(route,"n_parameter",nonnegative=True)
        mu=s10.nonsway_frame_mu_eq145(p,n)
        return {"mu":mu,"method":"equation_145","p":p,"n":n}
    if method=="table31_special_case":
        cid=str(route["special_case_id"]); x=_num(route,"special_case_parameter",positive=True)
        return {"mu":s10.table_31_special_case_mu(cid,x),"method":"table_31_special_case","case_id":cid,"parameter":x}
    raise ValueError("unsupported Table 31 mu_method")


def _effective_length_route(route: Mapping[str, Any]) -> dict[str, Any]:
    kind=str(route["kind"])
    if kind=="eq136_truss_chord_in_plane":
        l=_num(route,"segment_length_mm",positive=True); a=_num(route,"adjacent_force_ratio_alpha")
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.truss_chord_effective_length_in_plane_eq136(l,a),"equation":"136"}
    if kind=="eq137_truss_chord_out_of_plane":
        l1=_num(route,"braced_length_mm",positive=True); k=int(route["section_count_k"]); b=_num(route,"other_force_sum_ratio_beta")
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.truss_chord_effective_length_out_of_plane_eq137(l1,k,b),"equation":"137"}
    if kind=="eq138_built_up_branch_in_plane":
        l=_num(route,"segment_length_mm",positive=True); a=_num(route,"adjacent_force_ratio_alpha")
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.built_up_column_branch_effective_length_in_plane_eq138(l,a),"equation":"138"}
    if kind=="eq139_built_up_branch_out_of_plane":
        l1=_num(route,"braced_length_mm",positive=True); k=int(route["section_count_k"]); b=_num(route,"other_force_sum_ratio_beta")
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.built_up_column_branch_effective_length_out_of_plane_eq139(l1,k,b),"equation":"139"}
    if kind=="table24_truss_member":
        l=_num(route,"geometric_length_mm",positive=True)
        l1=_num(route,"out_of_plane_braced_length_mm",positive=True) if "out_of_plane_braced_length_mm" in route else None
        val=s10.table_24_effective_length(str(route["table24_case"]),str(route["member_role"]),l,l1)
        return {"status":"RESOLVED","route":kind,"effective_length_mm":val,"table":"24"}
    if kind=="table25_cross_lattice":
        val=s10.table_25_cross_lattice_effective_length(str(route["joint_case"]),str(route["supporting_state"]),_num(route,"node_to_intersection_length_mm",positive=True),_num(route,"full_member_length_mm",positive=True))
        return {"status":"RESOLVED","route":kind,"effective_length_mm":val,"table":"25"}
    if kind=="table26_structural_member":
        slender=_num(route,"geometric_slenderness_l_over_i_min",positive=True) if "geometric_slenderness_l_over_i_min" in route else None
        val=s10.table_26_structural_member_effective_length(str(route["member_case"]),_num(route,"geometric_length_mm",positive=True),slender,bool(route["is_lattice_member"]))
        radius=s10.structural_member_radius_selection_clause_10_2_2(bool(route["is_beam_column"]),str(route["bending_plane_relation"]))
        return {"status":"RESOLVED","route":kind,"effective_length_mm":val,"table":"26","radius_selector":radius}
    if kind=="table27_29_spatial_member":
        base=route["base_lengths_mm"]
        if not isinstance(base,Mapping): raise ValueError("base_lengths_mm must be an object")
        base_num={k:float(v) for k,v in base.items()}
        mu=None; trace={}
        row=str(route["table27_row"]); force=str(route["force_state"])
        if row in {"diagonal_15ad","diagonal_15bcge"} and force=="compression":
            n=s10.table_28_n_parameter(_num(route,"chord_min_inertia_mm4",positive=True),_num(route,"diagonal_length_mm",positive=True),_num(route,"diagonal_min_inertia_mm4",positive=True),_num(route,"chord_panel_length_mm",positive=True))
            conditional=None
            if row=="diagonal_15ad":
                conditional=s10.table_28_intersection_conditional_length(str(route["table28_joint_case"]),str(route["supporting_state"]),_num(route,"diagonal_length_mm",positive=True),_num(route,"alternate_diagonal_length_mm",positive=True),n)
                base_num["ldc"]=conditional
            mu0=s10.table_29_diagonal_length_factor(str(route["connection_case"]),n,_num(route,"geometric_slenderness_l_over_i_min",positive=True))
            mu=s10.table_29_end_connection_adjustment(mu0,str(route["gusset_configuration"]))
            trace={"table28_n":n,"table28_conditional_length_mm":conditional,"table29_base_mu_d":mu0,"table29_adjusted_mu_d":mu}
        props=s10.table_27_spatial_member_properties(row,force,base_num,mu,bool(route["out_of_plane_variant"]))
        return {"status":"RESOLVED","route":kind,"effective_length_mm":props["effective_length"],"radius_selector":props["radius_selector"],"table27":props,**trace}
    if kind=="table30_column":
        mu=s10.table_30_effective_length_factor(str(route["scheme_id"])); l=_num(route,"column_length_mm",positive=True)
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.column_effective_length_eq140(l,mu),"mu":mu,"equation":"140","table":"30"}
    if kind=="table31_frame_column":
        if route.get("same_load_combination_confirmed") is not True:
            return {"status":"INCOMPLETE_FAIL_CLOSED","route":kind,"effective_length_mm":None,"required":"same_load_combination_confirmed_per_10.3.2"}
        mu_info=_table31_mu(route); mu=float(mu_info["mu"])
        if route.get("apply_eq146_nonuniform_loading") is True:
            if str(mu_info["method"]) not in {"equation_141_corrected_by_FCS_letter_Исх-8076","equation_142"}:
                raise ValueError("Equation (146) requires base mu from Equation (141) or (142)")
            mu=s10.nonuniform_sway_frame_effective_length_eq146(mu,_num(route,"checked_column_inertia_mm4",positive=True),_num(route,"total_column_force_n",positive=True),_num(route,"checked_column_force_n",positive=True),_num(route,"total_column_inertia_mm4",positive=True))
            mu_info["equation_146_mu_eff"]=mu
        deformation=None
        if route.get("apply_eq147_deformation_reduction") is True:
            deformation=s10.frame_deformation_reduction_factor_eq147(_num(route,"relative_slenderness",nonnegative=True),_num(route,"moment_n_mm",positive=True),_num(route,"nonsway_reference_moment_n_mm"),_num(route,"area_mm2",positive=True),_num(route,"axial_force_n",positive=True),_num(route,"compressed_fibre_section_modulus_mm3",positive=True))
            mu*=deformation["psi"]
        h=_num(route,"frame_total_height_mm",positive=True) if "frame_total_height_mm" in route else None
        b=_num(route,"frame_width_mm",positive=True) if "frame_width_mm" in route else None
        global_required=bool(h is not None and b is not None and h/b>=6.0)
        global_confirmed=bool(route["global_frame_stability_confirmed"]) if "global_frame_stability_confirmed" in route else False
        if global_required and not global_confirmed:
            return {"status":"INCOMPLETE_FAIL_CLOSED","route":kind,"effective_length_mm":None,"mu":mu,"mu_trace":mu_info,"equation_147":deformation,"global_frame_stability_required":True,"required":"clause_10.3.5_global_frame_stability_check"}
        l=_num(route,"column_length_mm",positive=True)
        return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.column_effective_length_eq140(l,mu),"mu":mu,"mu_trace":mu_info,"equation_147":deformation,"global_frame_stability_required":global_required,"global_frame_stability_confirmed":global_confirmed}
    if kind=="out_of_plane_column_10_3_9":
        if route.get("use_restraint_spacing") is True:
            return {"status":"RESOLVED","route":kind,"effective_length_mm":s10.out_of_plane_column_effective_length_clause_10_3_9(_num(route,"restraint_spacing_mm",positive=True)),"clause":"10.3.9"}
        return _external_length(route,reason="Clause 10.3.9 permits determination from an analysis model reflecting actual end restraints.")|{"route":kind}
    if kind=="gallery_support_10_3_10":
        val=s10.gallery_support_branch_effective_length_clause_10_3_10(str(route["direction"]),_num(route,"support_height_mm",positive=True),_num(route,"node_spacing_mm",positive=True),_num(route,"mu",positive=True))
        if route.get("overall_built_up_cantilever_stability_confirmed") is not True:
            return {"status":"INCOMPLETE_FAIL_CLOSED","route":kind,"effective_length_mm":val,"required":"overall_gallery_support_built_up_cantilever_stability_check"}
        return {"status":"RESOLVED","route":kind,"effective_length_mm":val,"clause":"10.3.10","overall_stability_confirmed":True}
    if kind=="stepped_column_10_3_7_external":
        return _external_length(route,reason="Clause 10.3.7 routes stepped columns to Annex И or an analysis model reflecting actual restraints.")|{"route":kind}
    if kind=="certified_software_10_3_11":
        if not (route.get("certified_software_confirmed") is True and route.get("elastic_steel_confirmed") is True and route.get("undeformed_scheme_confirmed") is True):
            return {"status":"INCOMPLETE_FAIL_CLOSED","route":kind,"effective_length_mm":None,"required":"certified_software_plus_elastic_steel_plus_undeformed_scheme"}
        return _external_length(route,reason="Clause 10.3.11 permits software determination only under the stated certified/elastic/undeformed assumptions.")|{"route":kind,"software_assumptions_confirmed":True}
    if kind=="crossing_brace_external_10_1_3":
        return _external_length(route,reason="Clause 10.1.3 sends the specified crossing-brace cases to the applicable steel-structure design rules.")|{"route":kind}
    raise ValueError(f"unsupported effective_length_route kind: {kind}")


def _radius_value(case: Mapping[str, Any], route_result: Mapping[str, Any]) -> dict[str, Any]:
    radius=case["radius"]
    if not isinstance(radius,Mapping): raise ValueError("radius must be an object")
    selector=route_result.get("radius_selector")
    mode=str(radius["mode"])
    if mode=="explicit":
        return {"selector":"explicit","radius_mm":_num(radius,"value_mm",positive=True)}
    if mode=="selector_values":
        requested=str(selector) if selector else str(radius["selector"])
        map_key={"i_min":"i_min_mm","i_x":"i_x_mm","i_y":"i_y_mm"}.get(requested)
        if map_key is None: raise ValueError("resolved radius selector is unsupported")
        return {"selector":requested,"radius_mm":_num(radius,map_key,positive=True)}
    if mode=="single_angle_10_1_4":
        sel=s10.single_angle_radius_selection_clause_10_1_4(float(route_result["effective_length_mm"]),_num(radius,"node_spacing_mm",positive=True),str(radius["buckling_direction"]))
        key={"i_min":"i_min_mm","i_x":"i_x_mm","i_y":"i_y_mm"}[sel]
        return {"selector":sel,"radius_mm":_num(radius,key,positive=True)}
    raise ValueError("unsupported radius mode")


def _limit(case: Mapping[str, Any], actual: float) -> dict[str, Any]:
    cfg=case["limiting_slenderness"]
    if not isinstance(cfg,Mapping): raise ValueError("limiting_slenderness must be an object")
    mode=str(cfg["mode"])
    group4=bool(cfg["group_4_applies"])
    if mode=="none": return {"status":"NOT_REQUESTED","limit":None,"check":None}
    if mode=="compressed_table32":
        if cfg.get("same_stability_case_confirmed") is not True:
            return {"status":"INCOMPLETE_FAIL_CLOSED","limit":None,"check":None,"required":"same_stability_case_confirmed"}
        alpha=s10.compressed_limit_alpha(_num(cfg,"axial_force_n",nonnegative=True),_num(cfg,"stability_coefficient_phi",positive=True),_num(cfg,"gross_area_mm2",positive=True),_num(cfg,"design_yield_resistance_n_mm2",positive=True),_num(cfg,"working_condition_factor",positive=True))
        limit=s10.table_32_compressed_limiting_slenderness(str(cfg["table32_row"]),alpha,group4)
        return {"status":"RESOLVED","table":"32","alpha":alpha,"limit":limit,"group4_factor_applied":group4,"check":s10.slenderness_check(actual,limit)}
    if mode=="tension_table33":
        limit=s10.table_33_tension_limiting_slenderness(str(cfg["table33_row"]),str(cfg["load_category"]),group4,bool(cfg["low_self_weight_sag_for_row_5"]),bool(cfg["crane_modes_1k_to_6k_for_row_3"]),bool(cfg["prestressed_tension_member"]))
        return {"status":"RESOLVED","table":"33","limit":limit,"group4_factor_applied":group4,"check":s10.slenderness_check(actual,limit)}
    raise ValueError("unsupported limiting_slenderness mode")


def effective_length_guided_workflow(case: dict[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute one applicability-selected current-SP16 Section 10 effective-length route and, when requested, its limiting-slenderness check.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 10.1-10.4
        Equation/Table: Tables 24-33; Equations (136)-(147)
        Normative status: normative orchestration of audited scalar producers, including official FCS correction of Equation (141)

    Parameters:
        case: Strict Stage N7 route object. Only one effective-length route is evaluated.

    Returns:
        Traceable route, effective length, selected radius, actual slenderness and optional Table 32/33 verification.

    Assumptions:
        Diagram/topology classification is supplied explicitly and corresponds to the actual structure.

    Sign convention:
        Compression/tension demands are positive magnitudes unless a ratio is explicitly signed by the referenced equation.

    Unit convention:
        Lengths mm; areas mm2; inertias mm4; forces N; moments N*mm; stresses N/mm2.

    Applicability:
        Selected current-SP16 Section 10 routes represented by Tables 24-33 and Equations (136)-(147).

    Limitations:
        Annex И, external crossing-brace rules, and certified-program global analysis are not fabricated; they require explicit external provenance.

    Raises:
        ValueError: A selected route lacks mandatory applicability data or violates its normative domain.
        TypeError: A route input has an invalid type.

    Examples:
        See examples/effective_length_guided_example.json.

    Tests:
        tests/test_stage_n7_effective_length_workflows.py

    Implementation notes:
        The workflow composes audited Section-10 scalar producers, preserves only interpolation rules printed by the standard, and fails closed for routes requiring external analysis/provenance. Equation (141) uses the official FAU FCS clarification No. Исх-8076 dated 10.11.2023.
    """
    if not isinstance(case,dict): raise TypeError("case must be a dict")
    route=_effective_length_route(case["effective_length_route"])
    unresolved=[]
    if route.get("effective_length_mm") is None:
        unresolved.append(str(route.get("required") or route.get("reason") or "effective_length_route"))
        return {"status":"INCOMPLETE_FAIL_CLOSED","effective_length":route,"radius":None,"actual_slenderness":None,"limiting_slenderness":None,"required_unresolved":unresolved,"pass":None}
    if route.get("status")!="RESOLVED" and route.get("status")!="EXTERNAL_EFFECTIVE_LENGTH_USED":
        unresolved.append(str(route.get("required") or "effective_length_route_confirmation"))
    radius=_radius_value(case,route)
    actual=s10.actual_slenderness(float(route["effective_length_mm"]),float(radius["radius_mm"]))
    limit=_limit(case,actual)
    if limit.get("status")=="INCOMPLETE_FAIL_CLOSED": unresolved.append(str(limit["required"]))
    p=None
    if not unresolved and limit.get("check") is not None:
        p=bool(limit["check"]["pass"])
    elif not unresolved and limit.get("status")=="NOT_REQUESTED":
        p=True
    return {"status":"COMPLETE" if not unresolved else "INCOMPLETE_FAIL_CLOSED","effective_length":route,"radius":radius,"actual_slenderness":actual,"limiting_slenderness":limit,"required_unresolved":unresolved,"pass":p if not unresolved else None}
