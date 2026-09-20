"""FIRE-UI1.6 universal weakening + signed-load verification-plan bindings."""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui14_section_weakening import build_fire_ui14_registry
from .profile_catalog import InterimProfileCatalog


def _positive(v: Any, name: str) -> float:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)) or float(v)<=0:
        raise FireUIError(f"{name} must be a finite number > 0")
    return float(v)


def _number(v: Any, name: str) -> float:
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)):
        raise FireUIError(f"{name} must be a finite number")
    return float(v)


def _weakening_model(values: Mapping[str, Any]) -> dict[str, Any]:
    raw=values.get("section_weakening_model")
    if not isinstance(raw,Mapping): raise FireUIError("section_weakening_model must be an object")
    holes=bool(raw.get("holes_present"))
    if not holes: return {"holes_present":False,"model":"none"}
    d=_positive(raw.get("hole_diameter_mm"),"hole_diameter_mm")
    s=_positive(raw.get("hole_pitch_mm"),"hole_pitch_mm")
    if s<=d: raise FireUIError("SP16 8.2.1 formula (45) requires hole pitch s > hole diameter d")
    t=raw.get("local_thickness_mm")
    return {"holes_present":True,"model":"round_bolt_hole_universal_v1","d":d,"s":s,"local_thickness_mm":None if t in (None,"") else _positive(t,"local_thickness_mm")}


def _weakening_flag(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"sp16_has_weakening":_weakening_model(values)["holes_present"]}


def _local_thickness(values: Mapping[str, Any], model: Mapping[str, Any]) -> float:
    if model.get("local_thickness_mm") is not None:
        return float(model["local_thickness_mm"])
    if "t_w" in values:
        try: return _positive(values["t_w"],"t_w")
        except FireUIError: pass
    geom=values.get("section_geometry_2d_normalized")
    if isinstance(geom,Mapping):
        dims=geom.get("dimensions") if isinstance(geom.get("dimensions"),Mapping) else geom
        for key in ("tw_mm","t_mm","web_thickness_mm"):
            if key in dims and dims[key] is not None:
                return _positive(dims[key],f"section geometry {key}")
        bundle=geom.get("user_bundle")
        if isinstance(bundle,Mapping):
            for key in ("t_w","local_thickness_mm","wall_thickness_mm"):
                if key in bundle and bundle[key] is not None:
                    return _positive(bundle[key],key)
    raise FireUIError("local thickness t_h cannot be inferred for this section; enter local_thickness_mm in the weakening editor")


def _gross(values: Mapping[str, Any], qid: str) -> float:
    if qid not in values: raise FireUIError(f"gross section property {qid} is required")
    return _positive(values[qid],qid)


def _evaluation_points(values: Mapping[str, Any]) -> dict[str, Any] | None:
    existing=values.get("section_evaluation_points")
    if isinstance(existing,Mapping) and existing.get("points"):
        return dict(existing)
    ix=values.get("J_x"); iy=values.get("J_y")
    wxp=values.get("W_el_x_pos"); wxn=values.get("W_el_x_neg"); wyp=values.get("W_el_y_pos"); wyn=values.get("W_el_y_neg")
    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and float(v)>0 for v in (ix,iy,wxp,wxn,wyp,wyn)):
        return None
    yp=float(ix)/float(wxp); yn=float(ix)/float(wxn); xp=float(iy)/float(wyp); xn=float(iy)/float(wyn)
    geom=values.get("section_geometry_2d_normalized")
    shape=""
    if isinstance(geom,Mapping): shape=str(geom.get("shape_group") or geom.get("template") or "")
    points=[]
    if shape in {"I_ROLLED_DSYMM","i_section","RHS_SHS","rhs_shs","CHANNEL","channel"}:
        for name,x,y in (("++",xp,yp),("-+",-xn,yp),("+-",xp,-yn),("--",-xn,-yn)):
            points.append({"id":name,"x":x,"y":y,"omega":0.0,"region":"outer_fibre"})
    elif shape in {"TEE","tee"}:
        dims=geom.get("dimensions") if isinstance(geom,Mapping) and isinstance(geom.get("dimensions"),Mapping) else geom
        tw=float(dims.get("tw_mm") if dims.get("tw_mm") is not None else (values.get("t_w") or 0.0)) if isinstance(dims,Mapping) else 0.0
        points=[{"id":"top+","x":xp,"y":yp,"omega":0.0,"region":"flange"},{"id":"top-","x":-xn,"y":yp,"omega":0.0,"region":"flange"}]
        if tw>0:
            points += [{"id":"web_bottom+","x":tw/2,"y":-yn,"omega":0.0,"region":"web"},{"id":"web_bottom-","x":-tw/2,"y":-yn,"omega":0.0,"region":"web"}]
    elif shape in {"CHS","chs"}:
        r=max(xp,xn,yp,yn)
        points=[{"id":f"p{i:02d}","x":r*math.cos(2*math.pi*i/72),"y":r*math.sin(2*math.pi*i/72),"omega":0.0,"region":"outer_circle"} for i in range(72)]
    if not points: return None
    return {"schema":"section_evaluation_points_v1","points":points,"source":"outer_geometry_extrema","sectorial_coordinate_status":"zero_placeholder_only_valid_when_B_equals_0"}


def _net_geometry(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    model=_weakening_model(values)
    area=_gross(values,"A_gross"); ix=_gross(values,"J_x"); iy=_gross(values,"J_y")
    wxmin=min(_gross(values,"W_el_x_pos"),_gross(values,"W_el_x_neg")); wymin=min(_gross(values,"W_el_y_pos"),_gross(values,"W_el_y_neg"))
    out:dict[str,Any]={"sp16_weakening_model_valid":True,"sp16_net_geometry_solver_ok":True}
    points=_evaluation_points(values)
    if not model["holes_present"]:
        out.update({"net_section_geometry_2d":{"schema":"fire_ui16_net_section_v1","mode":"identity_no_weakening"},"A_net":area,"I_xn":ix,"I_yn":iy,"W_xn_min":wxmin,"W_yn_min":wymin,"sp16_net_removed_area":0.0,"sp16_shear_weakening_mode":"none"})
        for src,dst in (("W_pl_x","W_pl_x_eff"),("W_pl_y","W_pl_y_eff"),("W_pl_min_gross","W_pl_min_eff"),("I_omega_gross","I_omega_n"),("W_omega_gross","W_omega_eff")):
            if src in values and values[src] is not None: out[dst]=_positive(values[src],src)
        if points is not None: out["section_evaluation_points"]=points
        return out
    t=_local_thickness(values,model); removed=model["d"]*t; an=area-removed
    if an<=0: raise FireUIError("bolt hole produces non-positive A_net")
    mode=values.get("net_property_reduction_mode")
    if mode not in {"area_only_keep_gross","manual_net_properties"}:
        raise FireUIError("net_property_reduction_mode must be resolved when holes are present")
    out.update({"net_section_geometry_2d":{"schema":"fire_ui16_net_section_v1","mode":mode,"hole_diameter_mm":model['d'],"local_thickness_mm":t,"removed_area_mm2":removed,"assumption":"round through-hole; area loss d*t_h"},"A_net":an,"sp16_net_removed_area":removed,"sp16_shear_weakening_mode":"formula45","sp16_wall_hole_pitch_s":model["s"],"sp16_wall_hole_diameter_d":model["d"]})
    if mode=="area_only_keep_gross":
        out.update({"I_xn":ix,"I_yn":iy,"W_xn_min":wxmin,"W_yn_min":wymin,"net_centroid_x":0.0,"net_centroid_y":0.0})
        for src,dst in (("W_pl_x","W_pl_x_eff"),("W_pl_y","W_pl_y_eff"),("W_pl_min_gross","W_pl_min_eff"),("I_omega_gross","I_omega_n"),("W_omega_gross","W_omega_eff")):
            if src in values and values[src] is not None: out[dst]=_positive(values[src],src)
    else:
        mapping={"manual_I_xn":"I_xn","manual_I_yn":"I_yn","manual_W_xn_min":"W_xn_min","manual_W_yn_min":"W_yn_min","manual_W_pl_x_eff":"W_pl_x_eff","manual_W_pl_y_eff":"W_pl_y_eff"}
        for src,dst in mapping.items(): out[dst]=_gross(values,src)
        out["W_pl_min_eff"]=min(out["W_pl_x_eff"],out["W_pl_y_eff"])
        if "manual_I_omega_n" in values: out["I_omega_n"]=_positive(values["manual_I_omega_n"],"manual_I_omega_n")
        if "manual_W_omega_eff" in values: out["W_omega_eff"]=_positive(values["manual_W_omega_eff"],"manual_W_omega_eff")
    if points is not None: out["section_evaluation_points"]=points
    return out


def _shear_gross(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    # Current scalar shear route is Qz / strong-axis web shear.  The load plan
    # explicitly defers Qy until axis-specific shear properties are bound.
    return {"I_shear_eff":_gross(values,"I_shear_gross"),"S_shear_eff":_gross(values,"S_shear_gross"),"t_w_eff":_local_thickness(values,_weakening_model(values))}


def _load_plan(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    N=_number(values["N_force"],"N_force"); My=_number(values["load_My_local"],"load_My_local"); Mz=_number(values["load_Mz_local"],"load_Mz_local")
    Qy=_number(values["load_Qy_local"],"load_Qy_local"); Qz=_number(values["load_Qz_local"],"load_Qz_local"); T=_number(values["T_torsion"],"T_torsion")
    bend=(My!=0.0 or Mz!=0.0)
    if N>0 and not bend: stress="central_tension"
    elif N<0 and not bend: stress="central_compression"
    elif N<0 and bend: stress="compression_plus_bending"
    elif N>0 and bend: stress="tension_plus_bending"
    else: stress="bending"
    branches=[]
    def add(id,label,status="supported",note=None):
        row={"id":id,"label":label,"status":status}
        if note: row["note"]=note
        branches.append(row)
    if N>0: add("axial_tension","Центральное/внецентренное растяжение")
    if N<0: add("axial_compression","Сжатие и устойчивость")
    if My!=0: add("bending_My","Изгиб My → SP16/SP554 legacy Mx")
    if Mz!=0: add("bending_Mz","Изгиб Mz → SP16/SP554 legacy My")
    if My!=0 and Mz!=0: add("biaxial_bending","Двухосный изгиб")
    if Qz!=0: add("shear_Qz","Поперечная сила Qz / текущий scalar web-shear route")
    if Qy!=0: add("shear_Qy","Поперечная сила Qy","deferred","Требуется отдельное axis-specific I/S/t shear binding; Qy не сворачивается в Qz.")
    if T!=0: add("torsion_T","Кручение T=Mx","deferred","T не является бимоментом B и не подставляется в существующие формулы B.")
    if N!=0 and bend: add("interaction_N_M","Взаимодействие N+M")
    if bend and Qz!=0: add("interaction_M_Qz","Взаимодействие M+Qz")
    if not branches: add("zero_loads","Нулевые усилия","deferred","Расчётный случай не содержит силовых воздействий.")
    deferred=[b["id"] for b in branches if b["status"]=="deferred"]
    plan={"schema":"fire_ui16_verification_plan_v1","sign_convention":{"N":"positive=tension, negative=compression","X":"member longitudinal axis","My":"bending about local Y","Mz":"bending about local Z","T":"torsion about longitudinal X"},"legacy_mapping":{"M_x":"load_My_local","M_y":"load_Mz_local","Q_shear":"load_Qz_local only","B_bimoment":"0; torsion is not bimoment"},"stress_state":stress,"branches":branches,"deferred_branch_ids":deferred,"all_branches_supported":not deferred}
    return {"stress_state":stress,"M_x":My,"M_y":Mz,"Q_shear":Qz,"B_bimoment":0.0,"verification_plan":plan}



def _advanced_identity_no_weakening(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    """Materialize advanced gross properties on the no-weakening route.

    This is an identity producer, not a new normative formula: gross shear,
    plastic and optional sectorial properties become the effective/net values,
    and the SP16 8.2.1 hole factor is exactly 1.0.
    """
    out:dict[str,Any]={
        "W_pl_min_eff": _gross(values,"W_pl_min_gross"),
        "I_shear_eff": _gross(values,"I_shear_gross"),
        "S_shear_eff": _gross(values,"S_shear_gross"),
        "t_w_eff": _gross(values,"t_w"),
        "sp16_shear_hole_alpha45": 1.0,
    }
    if values.get("I_omega_gross") is not None:
        out["I_omega_n"]=_positive(values["I_omega_gross"],"I_omega_gross")
    if values.get("W_omega_gross") is not None:
        out["W_omega_eff"]=_positive(values["W_omega_gross"],"W_omega_gross")
    return out

def build_fire_ui16_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI1.6 execution registry over the frozen FIRE-UI1.4/1.5 registry.

    Standard reference:
        SP16/SP554 guided execution binding for signed loads, universal section weakening, and verification-plan routing; normative equations remain in frozen producers/DAG specs. Audit ID: FIRE-UI16-WF-001.

    Parameters:
        catalog: Frozen interim profile catalog used by inherited section/material executors.
        registry: Optional existing execution registry to extend in place.

    Returns:
        ExecutionRegistry containing inherited bindings plus FIRE-UI1.6 weakening and signed-load producers.

    Assumptions:
        Catalog and inherited FIRE-UI1.4 registry passed their release qualification gates.

    Sign convention:
        Signed loads are preserved; positive ``N`` denotes tension and negative ``N`` compression in the FIRE-UI1.6 load plan.

    Unit convention:
        Registry functions consume the canonical package units declared by their DAG quantities.

    Applicability:
        FIRE-UI1.6 guided mechanical verification sessions.

    Limitations:
        Registration does not by itself make an unsupported normative branch executable; unsupported cases remain explicit fail-closed terminals.

    Raises:
        Propagates validation errors from inherited registry/catalog construction and duplicate/invalid registry operations.

    Examples:
        ``registry = build_fire_ui16_registry(InterimProfileCatalog())``.

    Tests:
        FIRE-UI1.6 weakening, signed-load, verification-plan, and end-to-end route qualification suites.

    Implementation notes:
        FIRE-UI1.6 deliberately overrides only the bindings whose semantics changed; all unrelated frozen production executors are inherited.
    """
    reg=build_fire_ui14_registry(catalog,registry)
    reg.register("SP16_D_WEAKENING",_weakening_flag)
    reg.register("SP554_G_NET_SECTION_PROPERTIES",_net_geometry)
    reg.register("SP16_C_SHEAR_GROSS_PROPERTIES_WEAK",_shear_gross)
    reg.register("SP16_C_NET_ADVANCED_IDENTITY",_advanced_identity_no_weakening)
    reg.register("SP554_D_STRESS_STATE",_load_plan)
    return reg
