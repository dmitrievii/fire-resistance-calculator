"""Stage N6 applicability-safe orchestration for SP16 clauses 9.3-9.4."""
from __future__ import annotations

import math
from typing import Any, Mapping

from . import axial_members as axial
from . import axial_workflows as axw
from . import built_up_axial_members as bua
from . import built_up_beam_columns_and_combined_local_stability as n6
from . import beam_column_stability as bc


def _num(mapping: Mapping[str, Any], key: str, *, positive: bool=False, nonnegative: bool=False) -> float:
    if key not in mapping:
        raise ValueError(f"built_up_beam_column_guided requires {key}")
    value=mapping[key]
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(float(value)):
        raise ValueError(f"{key} must be a finite real number")
    value=float(value)
    if positive and value<=0: raise ValueError(f"{key} must be greater than zero")
    if nonnegative and value<0: raise ValueError(f"{key} must be non-negative")
    return value


def _resolve_d4(lambda_eff_bar: float, m: float, central_phi: float, stability: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve Table D.4 only at printed nodes unless an explicitly sourced external value is supplied."""
    if m>20.0:
        return {"status":"SECTION_8_REQUIRED_M_GT_20","phi_e":None,"route":"bending_member_section_8"}
    if m==0.0:
        return {"status":"CENTRAL_COMPRESSION_LIMITING_CASE","phi_e":central_phi,"route":"central_compression_limit"}
    try:
        phi_e=bc.annex_d4_stability_coefficient(lambda_eff_bar,m,central_phi)
        return {"status":"D4_EXACT_NODE","phi_e":phi_e,"route":"equation_109_with_table_d4","source":"table_D.4_exact_node_no_interpolation"}
    except ValueError as exc:
        ext=stability.get("external_phi_e_d4")
        if isinstance(ext,Mapping):
            value=float(ext["value"]); basis=str(ext["basis"]).strip()
            if not basis: raise ValueError("stability.external_phi_e_d4.basis must be non-empty")
            if not 0.0<value<=central_phi+1e-12:
                raise ValueError("external Table D.4 phi_e must satisfy 0 < phi_e <= central compression phi")
            return {"status":"EXTERNAL_D4_COEFFICIENT_USED","phi_e":min(value,central_phi),"route":"equation_109_with_external_phi_e","source":basis,"exact_lookup_error":str(exc)}
        return {"status":"EXTERNAL_D4_COEFFICIENT_REQUIRED","phi_e":None,"route":"fail_closed","source":"table_D.4_non_node_no_normative_interpolation_rule_encoded","exact_lookup_error":str(exc)}


def _branch_additional_force(case: Mapping[str, Any], section_type: int, mx: float, my: float) -> dict[str, Any]:
    branch=case["branch"]
    if section_type==1:
        if mx>0.0 and my>0.0:
            return {"status":"EXTERNAL_BRANCH_FORCE_REQUIRED","value_n":None,"reason":"Clause 9.3.3 prints no biaxial combination expression for Table 8 type 1."}
        if my>0.0:
            return {"status":"RESOLVED_9.3.3","value_n":n6.branch_additional_force_y_types_1_3(my,_num(branch,"spacing_b_mm",positive=True)),"formula":"Nad=My/b"}
        if mx>0.0:
            return {"status":"EXTERNAL_BRANCH_FORCE_REQUIRED","value_n":None,"reason":"Clause 9.3.3 does not print an x-plane branch-force expression for Table 8 type 1."}
        return {"status":"ZERO_MOMENT","value_n":0.0}
    if section_type==2:
        b1=_num(branch,"spacing_b1_mm",positive=True); b2=_num(branch,"spacing_b2_mm",positive=True)
        if mx>0.0 and my>0.0:
            return {"status":"RESOLVED_EQ124","value_n":n6.biaxial_branch_additional_force_eq124(my,b1,mx,b2),"formula":"124"}
        if my>0.0:
            return {"status":"RESOLVED_9.3.3","value_n":n6.branch_additional_force_y_type_2(my,b1),"formula":"0.5My/b1"}
        if mx>0.0:
            return {"status":"RESOLVED_9.3.3","value_n":n6.branch_additional_force_x_type_2(mx,b2),"formula":"0.5Mx/b2"}
        return {"status":"ZERO_MOMENT","value_n":0.0}
    if section_type==3:
        if mx>0.0 and my>0.0:
            ext=branch.get("external_additional_force_n")
            if isinstance(ext,Mapping):
                val=float(ext["value"]); basis=str(ext["basis"]).strip()
                if val<0 or not basis: raise ValueError("branch.external_additional_force_n requires non-negative value and non-empty basis")
                return {"status":"EXTERNAL_BIAXIAL_TYPE3_FORCE_USED","value_n":val,"source":basis}
            return {"status":"EXTERNAL_BRANCH_FORCE_REQUIRED","value_n":None,"reason":"Clause 9.3.3 provides separate My/b and 1.16Mx/b expressions but no explicit type-3 biaxial combination rule."}
        if my>0.0:
            return {"status":"RESOLVED_9.3.3","value_n":n6.branch_additional_force_y_types_1_3(my,_num(branch,"spacing_b_mm",positive=True)),"formula":"My/b"}
        if mx>0.0:
            return {"status":"RESOLVED_9.3.3","value_n":n6.branch_additional_force_x_type_3(mx,_num(branch,"spacing_b_mm",positive=True)),"formula":"1.16Mx/b"}
        return {"status":"ZERO_MOMENT","value_n":0.0}
    raise ValueError("built_up_section_type must be 1, 2, or 3")


def _branch_check(case: Mapping[str, Any], connector_system: str, nad: dict[str, Any], lambda_eff_bar: float, ry: float, gamma_c: float) -> dict[str, Any]:
    branch=case["branch"]
    if nad.get("value_n") is None:
        return {"status":"INCOMPLETE_FAIL_CLOSED","required":"branch_additional_force"}
    base=_num(branch,"base_branch_axial_force_n",nonnegative=True)
    design_n=n6.branch_force_with_additional_component(base,float(nad["value_n"]))
    if connector_system=="lattice":
        area=_num(branch,"gross_area_mm2",positive=True)
        lb=_num(branch,"relative_slenderness",nonnegative=True)
        st=str(branch["table7_section_type"])
        # Clause 9.3.3 requires the individual lattice branch itself to be checked by Eq. (7).
        # For the ordinary 7.2.4 branch domain (lambda_b <= 2.7 and lambda_b <= lambda_eff)
        # this uses the branch's own Eq. (8) stability coefficient.  The extended 2.7..4.1
        # permission is conditional on the separate clause 7.2.5 whole-built-up-member procedure;
        # this Stage N6 beam-column route does not silently substitute that central-compression
        # reduced-resistance procedure into Eq. (109), so it fails closed instead.
        basic_assessment=bua.lattice_branch_slenderness_assessment(lb,lambda_eff_bar,False)
        if basic_assessment["permitted"]:
            phi=axial.central_compression_stability_coefficient(lb,st)
            util=axial.central_compression_stability_utilization(design_n,area,ry,gamma_c,phi)
            return {"status":"EVALUATED_9.3.3_EQ7","design_force_n":design_n,"assessment":basic_assessment,"phi_branch":phi,"phi_source":"clause_9.3.3_equation_7_with_clause_7.1.3_equation_8","utilization":util,"pass":util<=1.0}
        extended_assessment=bua.lattice_branch_slenderness_assessment(lb,lambda_eff_bar,True)
        if extended_assessment["classification"]=="permitted_only_with_clause_7_2_5":
            return {"status":"CLAUSE_7.2.5_WHOLE_MEMBER_COUPLING_REQUIRED","design_force_n":design_n,"assessment":extended_assessment,"required":"explicit_clause_7.2.5_compatible_whole_member_route","pass":None}
        return {"status":"BRANCH_SLENDERNESS_NOT_PERMITTED","design_force_n":design_n,"assessment":basic_assessment,"pass":False}
    # Clause 9.3.4 requires Eq.109 plus local Vierendeel bending.  Effective lengths and branch moment distribution
    # are topology-specific and are not inferred by this guided layer.
    return {"status":"DETAILED_BRANCH_EQ109_LOCAL_BENDING_REQUIRED","design_force_n":design_n,"specialized_action":"built_up_beam_columns_and_combined_local_stability","pass":None}


def _web_local(case: Mapping[str, Any], lambda_eff_bar: float, whole_phi_e: float|None, ry: float, elastic: float, gamma_c: float, axial_force: float, area: float) -> dict[str, Any]:
    cfg=case["local_stability"]
    if cfg.get("enabled") is not True:
        return {"status":"NOT_REQUESTED","pass":None}
    w=cfg["web"]
    st=int(w["section_type"])
    actual=n6.combined_web_relative_slenderness(_num(w,"effective_height_mm",positive=True),_num(w,"thickness_mm",positive=True),ry,elastic)
    lx=_num(w,"member_relative_slenderness_x",nonnegative=True)
    mx=_num(w,"relative_eccentricity_mx",nonnegative=True)
    alpha=float(w["alpha"]) if "alpha" in w else 0.0
    stress=None
    if st==1:
        limit=n6.table_22_type_1_limit(lx,mx,_num(w,"central_compression_limit_m0",positive=True),_num(w,"bending_member_limit_m20",positive=True))
    elif st in {2,3}:
        stress=n6.table_22_stress_parameters(_num(w,"sigma_1_n_mm2",positive=True),_num(w,"sigma_2_n_mm2"),_num(w,"average_shear_stress_n_mm2",nonnegative=True),_num(w,"c_cr",positive=True))
        alpha=stress["alpha"]
        base1=n6.table_22_type_1_limit(lx,mx,_num(w,"central_compression_limit_m0",positive=True),_num(w,"bending_member_limit_m20",positive=True))
        limit2=n6.table_22_type_2_limit(alpha,base1,_num(w,"central_compression_limit_at_alpha_0_5",positive=True),stress["beta"],_num(w,"c_cr",positive=True),ry,gamma_c,_num(w,"sigma_1_n_mm2",positive=True))
        limit=limit2 if st==2 else n6.web_limit_eq128(limit2,alpha)
    elif st==4:
        limit=n6.web_limit_eq129(lx,_num(w,"flange_width_mm",positive=True),_num(w,"effective_height_mm",positive=True))
    elif st==5:
        limit=n6.table_22_type_5_limit(_num(w,"relative_eccentricity_my",nonnegative=True),_num(w,"central_compression_limit_m0",positive=True),area,ry,gamma_c,axial_force)
    else:
        raise ValueError("local_stability.web.section_type must be 1..5")

    eq131=None
    if w.get("apply_clause_9_4_3") is True:
        if st!=1: raise ValueError("Clause 9.4.3 guided adjustment is only enabled for Table 22 type 1")
        if whole_phi_e is None: raise ValueError("Clause 9.4.3 requires resolved phi_e")
        util=axial_force/(whole_phi_e*area*ry*gamma_c)
        type2=_num(w,"type_2_limit_for_eq131",positive=True)
        limit=n6.web_limit_adjustment_eq131(limit,type2,util)
        eq131={"axial_stability_utilization":util,"adjusted_limit":limit}

    two_plane_factor=1.0
    if cfg.get("two_plane_condition_governing") is True:
        coeffs=cfg.get("stability_coefficients")
        if not isinstance(coeffs,list) or not coeffs: raise ValueError("two-plane governing route requires stability_coefficients")
        two_plane_factor=n6.two_plane_limit_increase_clause_9_4_9([float(x) for x in coeffs],area,ry,axial_force)
        limit*=two_plane_factor
    passed=actual<=limit+1e-12
    reduced=None
    unresolved=[]
    if st in {1,2,3}:
        reduced=n6.reduced_area_route_clause_9_4_6(st,alpha,actual,limit)
        if reduced["reduced_area_required"]:
            unresolved.append("clause_7.3.6_reduced_area_and_member_stability_recheck")
    stiffener=None
    if actual>=2.3:
        tcfg=cfg.get("transverse_stiffener")
        if not isinstance(tcfg,Mapping):
            unresolved.append("clause_9.4.4_transverse_stiffener_data")
        else:
            stiffener=n6.transverse_stiffener_route_clause_9_4_4(actual,_num(w,"effective_height_mm",positive=True),ry,elastic,str(tcfg["arrangement"]),float(tcfg["provided_outstand_mm"]),bool(tcfg["geometrically_nonlinear_design"]),bool(tcfg["solid_branch_of_built_up_column"]))
            provided_thickness=_num(tcfg,"provided_thickness_mm",positive=True)
            provided_spacing=_num(tcfg,"provided_spacing_mm",positive=True)
            stiffener["provided_thickness_mm"]=provided_thickness
            stiffener["thickness_pass"]=provided_thickness+1e-12>=float(stiffener["minimum_thickness_mm"])
            if stiffener["required"]:
                stiffener["provided_spacing_mm"]=provided_spacing
                stiffener["spacing_pass"]=float(stiffener["minimum_spacing_mm"])-1e-12<=provided_spacing<=float(stiffener["maximum_spacing_mm"])+1e-12
                stiffener["pass"]=bool(stiffener["outstand_pass"] and stiffener["thickness_pass"] and stiffener["spacing_pass"])
            else:
                stiffener["provided_spacing_mm"]=provided_spacing
                stiffener["spacing_pass"]=None
                stiffener["pass"]=True
            if stiffener["pass"] is False:
                unresolved.append("clause_9.4.4_transverse_stiffener_noncompliance")

    longitudinal=None
    lcfg=cfg.get("longitudinal_stiffener")
    if isinstance(lcfg,Mapping):
        longitudinal=n6.longitudinal_stiffener_route_clause_9_4_5(_num(lcfg,"provided_inertia_mm4",nonnegative=True),_num(w,"effective_height_mm",positive=True),_num(w,"thickness_mm",positive=True))
        half=lcfg["most_loaded_half_web_table22_check"]
        design=lcfg["clause_7_3_4_design_confirmation"]
        longitudinal["most_loaded_half_web_table22_check"]={"pass":bool(half["pass"]),"basis":str(half["basis"])}
        longitudinal["clause_7_3_4_design_confirmation"]={"confirmed":bool(design["confirmed"]),"basis":str(design["basis"])}
        longitudinal["pass"]=bool(longitudinal["inertia_pass"] and half["pass"] and design["confirmed"])
        if longitudinal["pass"] is False:
            unresolved.append("clause_9.4.5_longitudinal_stiffener_or_half_web_check_noncompliance")

    return {"status":"COMPLETE" if not unresolved else "INCOMPLETE_FAIL_CLOSED","section_type":st,"actual_relative_slenderness":actual,"limit":limit,"base_table22_limit_before_two_plane_factor":limit/two_plane_factor,"stress_parameters":stress,"equation_131":eq131,"two_plane_factor":two_plane_factor,"reduced_area_route":reduced,"transverse_stiffener":stiffener,"longitudinal_stiffener":longitudinal,"required_unresolved":unresolved,"pass":passed if not unresolved else None}


def _flange_local(case: Mapping[str, Any], ry: float, elastic: float, axial_force: float, area: float) -> dict[str, Any]:
    cfg=case["local_stability"]
    if cfg.get("enabled") is not True:
        return {"status":"NOT_REQUESTED","pass":None}
    f=cfg["flange"]
    actual=n6.combined_flange_relative_slenderness(_num(f,"effective_outstand_mm",positive=True),_num(f,"thickness_mm",positive=True),ry,elastic)
    limit=n6.table_23_limit(int(f["section_type"]),_num(f,"central_compression_limit",positive=True),_num(f,"member_relative_slenderness_x",nonnegative=True),_num(f,"member_relative_slenderness_y",nonnegative=True),_num(f,"relative_eccentricity_mx",nonnegative=True),_num(f,"bending_member_limit_m20",positive=True))
    limit=n6.edge_return_flange_limit_clause_9_4_8(limit,bool(f["edge_return_qualified"]) if "edge_return_qualified" in f else False)
    factor=1.0
    if cfg.get("two_plane_condition_governing") is True:
        coeffs=cfg.get("stability_coefficients")
        if not isinstance(coeffs,list) or not coeffs: raise ValueError("two-plane governing route requires stability_coefficients")
        factor=n6.two_plane_limit_increase_clause_9_4_9([float(x) for x in coeffs],area,ry,axial_force)
        limit*=factor
    return {"status":"COMPLETE","section_type":int(f["section_type"]),"actual_relative_slenderness":actual,"limit":limit,"two_plane_factor":factor,"pass":actual<=limit+1e-12}


def built_up_beam_column_guided_workflow(case: dict[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Compose an applicability-safe current-SP16 built-up beam-column and combined local-stability calculation.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Changes No. 1-6 through 09.12.2024
        Clause: 9.3-9.4
        Equation/Table: Equations (123)-(135), Tables 22-23 and Annex D.4
        Normative status: normative orchestration of retained audited scalar producers

    Parameters:
        case:
            Type: dict[str, Any]
            Unit: mixed, explicitly named
            Meaning: Strict Stage N6 case after optional N1 material hydration.

    Returns:
        Type: dict[str, Any]
        Unit: mixed
        Meaning: Whole-member, branch, connector and local-stability trace with fail-closed unresolved requirements.

    Assumptions:
        - N and M belong to the same load combination.
        - Table 8/22/23 topology classifications supplied by the caller match the actual section geometry.

    Sign convention:
        - axial_force_n is a positive compression magnitude; stability moments are used by magnitude.

    Unit convention:
        - Forces N, moments N*mm, lengths mm, areas mm2, inertias mm4, stresses N/mm2.

    Applicability:
        - Built-up eccentrically compressed or beam-column members within clauses 9.3-9.4.

    Limitations:
        - Fewer-than-six-panel frame analysis, unstated type-1/type-3 biaxial branch-force combinations, arbitrary geometry classification, and reduced-area reanalysis are not inferred.
        - Table D.4 is exact-node only unless an externally sourced coefficient with provenance is supplied.

    Raises:
        ValueError: Required branch data are absent, inconsistent, or outside an encoded normative domain.
        TypeError: case is not a mapping.

    Examples:
        See examples/built_up_beam_column_guided_example.json.

    Tests:
        tests/test_stage_n6_built_up_beam_column_workflows.py and tests/test_stage_n6_dag.py.

    Implementation notes:
        - Frozen Stage N3 Table-8/equation-18 and Stage N5 equation-109 primitives are reused.
        - Table D.4 has no encoded general interpolation; Tables 22 and 23 retain only the explicit linear interpolation rules printed in their notes.
    """
    if not isinstance(case,dict): raise TypeError("case must be a dictionary")
    for flag in ("same_load_combination_confirmed","built_up_geometry_classified_confirmed"):
        if case.get(flag) is not True: raise ValueError(f"{flag} must be explicitly true")
    topology=str(case["member_topology"])
    if topology=="three_sided_equilateral":
        return {"status":"INCOMPLETE_FAIL_CLOSED","route":"CLAUSE_9.3.5_SECTION_16_REQUIRED","required_unresolved":["section_16_three_sided_stability_check"],"governing_utilization":None,"pass":None}
    if topology=="two_solid_branches":
        return {"status":"INCOMPLETE_FAIL_CLOSED","route":"CLAUSE_9.3.6_DETAILED_TWO_SOLID_BRANCH_CHECK_REQUIRED","specialized_action":"built_up_beam_columns_and_combined_local_stability","required_unresolved":["whole_member_9.3.2_with_ex_zero","branch_eq109_eq111_and_effective_lengths"],"governing_utilization":None,"pass":None}
    if topology!="general_built_up":
        raise ValueError("member_topology must be general_built_up, three_sided_equilateral, or two_solid_branches")
    n=_num(case,"axial_force_n",positive=True); mx=abs(_num(case,"moment_x_n_mm")); my=abs(_num(case,"moment_y_n_mm"))
    area=_num(case,"gross_area_mm2",positive=True); ry=_num(case,"design_yield_resistance_n_mm2",positive=True); elastic=_num(case,"elastic_modulus_n_mm2",positive=True); gc=_num(case,"working_condition_factor",positive=True)
    whole=case["whole_member"]
    panels=int(whole["panel_count"]); connector=str(whole["connector_system"]); st=int(whole["built_up_section_type"])
    if panels<6:
        return {"status":"INCOMPLETE_FAIL_CLOSED","route":"LESS_THAN_SIX_PANELS","required_unresolved":["frame_system_analysis_or_clause_7.2.5_external_effective_slenderness"],"governing_utilization":None,"pass":None}
    table8=dict(whole["table8_data"]); table8.setdefault("total_area_mm2",area)
    selected=axw.selected_table8_effective_slenderness(st,connector,table8)
    lambda_eff_bar=axial.relative_slenderness(float(selected["effective_slenderness"]),ry,elastic)
    central_phi=axial.central_compression_stability_coefficient(lambda_eff_bar,"b")
    free_moment=abs(_num(whole,"free_axis_moment_n_mm"))
    ecc=free_moment/n
    m=n6.built_up_relative_eccentricity_eq123(ecc,area,_num(whole,"compressed_branch_axis_distance_mm",positive=True),_num(whole,"free_axis_inertia_mm4",positive=True))
    stability_cfg=case["stability"] if "stability" in case else {}
    d4=_resolve_d4(lambda_eff_bar,m,central_phi,stability_cfg)
    whole_check=None; unresolved=[]; utils=[]
    if d4["phi_e"] is not None:
        u=bc.beam_column_in_plane_utilization_eq109(n,float(d4["phi_e"]),area,ry,gc)
        whole_check={"equation":"109","utilization":u,"pass":u<=1.0}; utils.append(u)
    elif d4["status"]=="EXTERNAL_D4_COEFFICIENT_REQUIRED": unresolved.append("table_D4_phi_e")
    elif d4["status"]=="SECTION_8_REQUIRED_M_GT_20": unresolved.append("section_8_bending_member_check_for_m_gt_20")

    nad=_branch_additional_force(case,st,mx,my)
    branch_check=_branch_check(case,connector,nad,lambda_eff_bar,ry,gc)
    if branch_check.get("utilization") is not None: utils.append(float(branch_check["utilization"]))
    if branch_check.get("pass") is None: unresolved.append("branch_detailed_check")
    if branch_check.get("pass") is False: pass

    qfic=bua.fictitious_shear_force_n(n,elastic,ry,central_phi)
    connector_check=n6.connector_design_shear_clause_9_3_7(_num(whole,"actual_shear_force_n",nonnegative=True),qfic)
    if connector_check["lattice_required"] and connector!="lattice":
        unresolved.append("clause_9.3.7_actual_shear_exceeds_qfic_lattice_required")

    web=_web_local(case,lambda_eff_bar,d4.get("phi_e"),ry,elastic,gc,n,area)
    flange=_flange_local(case,ry,elastic,n,area)
    for name,item in (("web_local_stability",web),("flange_local_stability",flange)):
        if item.get("pass") is False: pass
        if item.get("pass") is None and item.get("status") not in {"NOT_REQUESTED"}: unresolved.append(name)

    checks=[whole_check,branch_check,web,flange]
    definite_fail=any(c is not None and c.get("pass") is False for c in checks)
    complete=not unresolved
    if whole_check is not None: pass
    governing=max(utils) if utils and complete else None
    pass_flag=(not definite_fail and all(c.get("pass") is not False for c in checks if c is not None)) if complete else None
    return {
        "status":"COMPLETE" if complete else "INCOMPLETE_FAIL_CLOSED",
        "whole_member":{"table8_selected_route":selected,"effective_relative_slenderness":lambda_eff_bar,"central_phi_type_b":central_phi,"eccentricity_mm":ecc,"relative_eccentricity_m_eq123":m,"d4":d4,"stability_check":whole_check},
        "branch":{"additional_force":nad,"check":branch_check},
        "connectors":{"fictitious_shear_force_n":qfic,**connector_check},
        "local_stability":{"web":web,"flange":flange},
        "required_unresolved":sorted(set(unresolved)),
        "governing_utilization":governing,
        "pass":pass_flag,
        "trace_policy":"SELECTED_9.3_TOPOLOGY_ONLY_EXACT_D4_EXPLICIT_TABLE22_TABLE23_INTERPOLATION",
    }
