"""FIRE-UI1.2 section geometry executor bindings.

The module binds UI geometry authoring nodes to existing catalog/analytic geometry
producers. It intentionally contains geometry algebra only; SP16/SP554 normative
member equations remain in their dedicated production modules.
"""
from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any, Mapping, Sequence

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .section_model import GrossSectionProperties, SectionPropertyModel


def _num(values: Mapping[str, Any], key: str, *, positive: bool = True) -> float:
    if key not in values:
        raise FireUIError(f"missing geometry input {key}")
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FireUIError(f"{key} must be a finite number")
    result = float(value)
    if positive and result <= 0:
        raise FireUIError(f"{key} must be > 0")
    return result


def _rect_composite(rectangles: Sequence[tuple[float, float, float, float]], *, model_name: str) -> GrossSectionProperties:
    """Return centroidal gross properties for non-overlapping axis-aligned rectangles.

    Rectangles are ``(width, height, cx, cy)`` in mm in an arbitrary input frame.
    """
    if not rectangles:
        raise FireUIError("at least one rectangle is required")
    rows=[]
    for width,height,cx,cy in rectangles:
        if min(width,height) <= 0:
            raise FireUIError("rectangle dimensions must be > 0")
        area=width*height
        rows.append((width,height,cx,cy,area))
    area=sum(r[4] for r in rows)
    xbar=sum(r[4]*r[2] for r in rows)/area
    ybar=sum(r[4]*r[3] for r in rows)/area
    ix=sum(w*h**3/12 + a*(cy-ybar)**2 for w,h,cx,cy,a in rows)
    iy=sum(h*w**3/12 + a*(cx-xbar)**2 for w,h,cx,cy,a in rows)
    xmin=min(cx-w/2 for w,h,cx,cy,a in rows); xmax=max(cx+w/2 for w,h,cx,cy,a in rows)
    ymin=min(cy-h/2 for w,h,cx,cy,a in rows); ymax=max(cy+h/2 for w,h,cx,cy,a in rows)
    xp=xmax-xbar; xn=xbar-xmin; yp=ymax-ybar; yn=ybar-ymin
    if min(xp,xn,yp,yn) <= 0:
        raise FireUIError("invalid composite-section extreme-fibre distance")
    return GrossSectionProperties(
        area_mm2=area, ix_mm4=ix, iy_mm4=iy,
        wx_pos_mm3=ix/yp, wx_neg_mm3=ix/yn,
        wy_pos_mm3=iy/xp, wy_neg_mm3=iy/xn,
        radius_x_mm=math.sqrt(ix/area), radius_y_mm=math.sqrt(iy/area),
        mass_kg_m_at_7850=SectionPropertyModel.mass_kg_m_from_area(area),
        geometry_model=model_name,
    )


def _parametric_properties(values: Mapping[str, Any]) -> tuple[GrossSectionProperties, dict[str, Any]]:
    family=str(values["section_family"]) if "section_family" in values else ""
    if family == "i_section":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); tw=_num(values,"t_w"); tf=_num(values,"t_f")
        props=SectionPropertyModel.doubly_symmetric_i_sharp(h,b,tw,tf)
        meta={"section_is_box":False,"section_is_channel":False,"section_is_pipe":False,"sp16_i_symmetry_class":"double_symmetric",
              "sec_b_top":b,"sec_b_bottom":b,"t_f_top":tf,"t_f_bottom":tf,
              "section_geometry_2d_normalized":{"template":"i_section","h_mm":h,"b_mm":b,"tw_mm":tw,"tf_mm":tf}}
        return props,meta
    if family == "rhs_shs":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); t=_num(values,"t_w")
        props=SectionPropertyModel.rectangular_hollow_sharp(b,h,t)
        return props,{"section_is_box":True,"section_is_channel":False,"section_is_pipe":False,"sp16_i_symmetry_class":"not_i",
                      "section_geometry_2d_normalized":{"template":"rhs_shs","h_mm":h,"b_mm":b,"t_mm":t}}
    if family == "chs":
        d=_num(values,"sec_h"); t=_num(values,"t_w")
        props=SectionPropertyModel.circular_hollow(d,t)
        return props,{"section_is_box":False,"section_is_channel":False,"section_is_pipe":True,"sp16_i_symmetry_class":"not_i",
                      "section_geometry_2d_normalized":{"template":"chs","D_mm":d,"t_mm":t}}
    if family == "channel":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); tw=_num(values,"t_w"); tf=_num(values,"t_f")
        if 2*tf>=h or tw>=b: raise FireUIError("invalid channel dimensions")
        # full-height web + non-overlapping flange outstands
        props=_rect_composite([(tw,h,tw/2,h/2),(b-tw,tf,tw+(b-tw)/2,h-tf/2),(b-tw,tf,tw+(b-tw)/2,tf/2)],model_name="channel_sharp_composite")
        return props,{"section_is_box":False,"section_is_channel":True,"section_is_pipe":False,"sp16_i_symmetry_class":"not_i",
                      "section_geometry_2d_normalized":{"template":"channel","h_mm":h,"b_mm":b,"tw_mm":tw,"tf_mm":tf}}
    if family == "tee":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); tw=_num(values,"t_w"); tf=_num(values,"t_f")
        if tf>=h or tw>=b: raise FireUIError("invalid tee dimensions")
        props=_rect_composite([(b,tf,b/2,h-tf/2),(tw,h-tf,b/2,(h-tf)/2)],model_name="tee_sharp_composite")
        return props,{"section_is_box":False,"section_is_channel":False,"section_is_pipe":False,"sp16_i_symmetry_class":"not_i",
                      "section_geometry_2d_normalized":{"template":"tee","h_mm":h,"b_mm":b,"tw_mm":tw,"tf_mm":tf}}
    if family == "angle":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); t=_num(values,"t_w")
        if t>=min(h,b): raise FireUIError("invalid angle dimensions")
        props=_rect_composite([(t,h,t/2,h/2),(b-t,t,t+(b-t)/2,t/2)],model_name="angle_sharp_composite")
        return props,{"section_is_box":False,"section_is_channel":False,"section_is_pipe":False,"sp16_i_symmetry_class":"not_i",
                      "section_geometry_2d_normalized":{"template":"angle","leg1_mm":h,"leg2_mm":b,"t_mm":t}}
    raise FireUIError(f"parametric section family {family!r} is not supported; use manual properties")


def _evaluation_points_from_properties(props: GrossSectionProperties, meta: Mapping[str, Any]) -> dict[str, Any] | None:
    """Material boundary points adequate for linear Mx/My stress envelopes.

    This does not invent sectorial coordinates; omega is set to zero and may be
    used only while B=0.  Unsupported arbitrary/asymmetric shapes return None
    rather than adding false corner points.
    """
    xp=props.iy_mm4/props.wy_pos_mm3; xn=props.iy_mm4/props.wy_neg_mm3
    yp=props.ix_mm4/props.wx_pos_mm3; yn=props.ix_mm4/props.wx_neg_mm3
    geom=meta.get("section_geometry_2d_normalized") if isinstance(meta,Mapping) else None
    shape=str((geom or {}).get("shape_group") or (geom or {}).get("template") or "") if isinstance(geom,Mapping) else ""
    pts=[]
    if shape in {"I_ROLLED_DSYMM","i_section","RHS_SHS","rhs_shs","CHANNEL","channel"}:
        pts=[{"id":"++","x":xp,"y":yp,"omega":0.0,"region":"outer_fibre"},{"id":"-+","x":-xn,"y":yp,"omega":0.0,"region":"outer_fibre"},{"id":"+-","x":xp,"y":-yn,"omega":0.0,"region":"outer_fibre"},{"id":"--","x":-xn,"y":-yn,"omega":0.0,"region":"outer_fibre"}]
    elif shape in {"TEE","tee"}:
        dims=(geom or {}).get("dimensions") if isinstance((geom or {}).get("dimensions"),Mapping) else geom
        tw=float(((dims or {}).get("tw_mm") or 0.0)) if isinstance(dims,Mapping) else 0.0
        pts=[{"id":"top+","x":xp,"y":yp,"omega":0.0,"region":"flange"},{"id":"top-","x":-xn,"y":yp,"omega":0.0,"region":"flange"}]
        if tw>0:
            pts += [{"id":"web_bottom+","x":tw/2,"y":-yn,"omega":0.0,"region":"web"},{"id":"web_bottom-","x":-tw/2,"y":-yn,"omega":0.0,"region":"web"}]
    elif shape in {"CHS","chs"}:
        r=max(xp,xn,yp,yn)
        pts=[{"id":f"p{i:02d}","x":r*math.cos(2*math.pi*i/72),"y":r*math.sin(2*math.pi*i/72),"omega":0.0,"region":"outer_circle"} for i in range(72)]
    if not pts: return None
    return {"schema":"section_evaluation_points_v1","points":pts,"source":"section_geometry_provider","sectorial_coordinate_status":"zero_placeholder_only_valid_when_B_equals_0"}


def _parametric_plastic_moduli(family: str, values: Mapping[str, Any]) -> tuple[float | None,float | None]:
    if family=="i_section":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); tw=_num(values,"t_w"); tf=_num(values,"t_f")
        web_h=h-2*tf
        zpx=2*(b*tf*(h/2-tf/2) + (tw*web_h/2)*(web_h/4))
        zpy=2*((2*tf)*(b/2)*(b/4) + (web_h)*(tw/2)*(tw/4))
        return zpx,zpy
    if family=="rhs_shs":
        h=_num(values,"sec_h"); b=_num(values,"sec_b"); t=_num(values,"t_w")
        bi=b-2*t; hi=h-2*t
        return (b*h*h-bi*hi*hi)/4, (h*b*b-hi*bi*bi)/4
    if family=="chs":
        D=_num(values,"sec_h"); t=_num(values,"t_w"); d=D-2*t
        z=(D**3-d**3)/6
        return z,z
    return None,None


def _base_outputs(props: GrossSectionProperties, meta: Mapping[str, Any]) -> dict[str, Any]:
    out={
        "A_gross":props.area_mm2,"J_x":props.ix_mm4,"J_y":props.iy_mm4,"J_min":min(props.ix_mm4,props.iy_mm4),
        "section_properties_ready":True,"major_axis_is_x":props.ix_mm4>=props.iy_mm4,
        "W_el_x_pos":props.wx_pos_mm3,"W_el_x_neg":props.wx_neg_mm3,"W_el_y_pos":props.wy_pos_mm3,"W_el_y_neg":props.wy_neg_mm3,
        "sp16_gross_geometry_solver_ok":True,
    }
    out.update(meta)
    for key in ("section_is_box","section_is_channel","section_is_pipe"):
        out.setdefault(key,False)
    # y extents can be reconstructed from I/W for the x-axis.
    out["section_y_pos_extent"]=props.ix_mm4/props.wx_pos_mm3
    out["section_y_neg_extent"]=props.ix_mm4/props.wx_neg_mm3
    if props.sx_mm3 is not None:
        out["I_shear_gross"]=props.ix_mm4; out["S_shear_gross"]=props.sx_mm3
    pts=_evaluation_points_from_properties(props,meta)
    if pts is not None: out["section_evaluation_points"]=pts
    return out


def _catalog_executor(catalog: InterimProfileCatalog):
    def run(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        fid=int(_num(values,"section_catalog_family_id")); row=int(_num(values,"section_catalog_source_row_id"))
        designation=str(values["section_designation"])
        r=catalog.resolve(fid,designation,source_row_id=row)
        p=r["catalog_properties_interim"]; d=r["dimensions"]; der=r["derived_properties"]; shape=str(r["shape_group"])
        out={
            "A_gross":float(p["A_mm2"]),"J_x":float(p["Ix_mm4"]),"J_y":float(p["Iy_mm4"]),"J_min":min(float(p["Ix_mm4"]),float(p["Iy_mm4"])),
            "section_properties_ready":True,"major_axis_is_x":float(p["Ix_mm4"])>=float(p["Iy_mm4"]),
            "W_el_x_pos":float(p["Wx1_mm3"]),"W_el_x_neg":float(p["Wx2_mm3"]),"W_el_y_pos":float(p["Wy1_mm3"]),"W_el_y_neg":float(p["Wy2_mm3"]),
            "section_y_pos_extent":float(p["Ix_mm4"])/float(p["Wx1_mm3"]),"section_y_neg_extent":float(p["Ix_mm4"])/float(p["Wx2_mm3"]),
            "section_is_box":shape=="RHS_SHS","section_is_channel":shape=="CHANNEL","section_is_pipe":shape=="CHS",
            "sp16_i_symmetry_class":"double_symmetric" if shape=="I_ROLLED_DSYMM" else "not_i",
            "section_geometry_2d_normalized":{"source":"profile_catalog","shape_group":shape,"family_id":fid,"designation":designation,"source_row_id":row,"dimensions":dict(d)},
            "I_shear_gross":float(p["Ix_mm4"]),"S_shear_gross":float(p["Sx_mm3"]),
        }
        if shape=="I_ROLLED_DSYMM":
            b=float(d["b_mm"]); h=float(d["h_mm"]); tf=float(d["tf_mm"])
            # For a doubly symmetric I-section the two flange weak-axis moments
            # are equal and the centroid is midway between flange axes. These
            # are exact geometry consequences of the selected catalog row.
            Ifl=b**3*tf/12.0
            hfl=h-tf
            out.update({"sec_b_top":b,"sec_b_bottom":b,"t_f_top":tf,"t_f_bottom":tf,
                        "sp16_ltb_h_axes":hfl,"sp16_ltb_h1":hfl/2.0,"sp16_ltb_h2":hfl/2.0,
                        "sp16_ltb_b1":b,"sp16_ltb_b2":b,"sp16_ltb_I1":Ifl,"sp16_ltb_I2":Ifl})
        # Plastic moduli are materialized only where the catalog's static
        # moments and section symmetry make the relation exact.
        if shape in {"I_ROLLED_DSYMM","RHS_SHS","CHS"} and p.get("Sx_mm3") is not None and p.get("Sy_mm3") is not None:
            out["W_pl_x"]=2.0*float(p["Sx_mm3"]); out["W_pl_y"]=2.0*float(p["Sy_mm3"]); out["W_pl_min_gross"]=min(out["W_pl_x"],out["W_pl_y"])
        elif shape=="TEE" and p.get("Sy_mm3") is not None:
            out["W_pl_y"]=2.0*float(p["Sy_mm3"])
        elif shape=="CHANNEL" and p.get("Sx_mm3") is not None:
            out["W_pl_x"]=2.0*float(p["Sx_mm3"])
        # Boundary evaluation points are generated from exact catalog extreme
        # fibres for supported shape families; no false points for angles.
        class _P: pass
        pp=_P(); pp.ix_mm4=float(p["Ix_mm4"]); pp.iy_mm4=float(p["Iy_mm4"]); pp.wx_pos_mm3=float(p["Wx1_mm3"]); pp.wx_neg_mm3=float(p["Wx2_mm3"]); pp.wy_pos_mm3=float(p["Wy1_mm3"]); pp.wy_neg_mm3=float(p["Wy2_mm3"])
        pts=_evaluation_points_from_properties(pp,{"section_geometry_2d_normalized":out["section_geometry_2d_normalized"]})
        if pts is not None: out["section_evaluation_points"]=pts
        declared = {b["quantity_id"] for b in node["produces"]}
        # Materialize catalog dimensions required by downstream SP16 annex/LTB
        # procedures.  These values come from the already selected frozen row;
        # no alternative geometry authoring route is invoked as a dependency.
        dim_map={"sec_h":"h_mm","sec_b":"b_mm","t_w":"tw_mm","t_f":"tf_mm","r_root":"r_mm"}
        for qid,key in dim_map.items():
            if qid in declared and key in d and d[key] is not None:
                out[qid]=float(d[key])
        if "t_w" in declared and "t_w" not in out and "t_mm" in d:
            out["t_w"] = float(d["t_mm"])
        return out
    return run


def _parametric_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    props,meta=_parametric_properties(values)
    out=_base_outputs(props,meta)
    zpx,zpy=_parametric_plastic_moduli(str(values.get("section_family") or ""),values)
    if zpx is not None: out["W_pl_x"]=zpx
    if zpy is not None: out["W_pl_y"]=zpy
    if zpx is not None and zpy is not None: out["W_pl_min_gross"]=min(zpx,zpy)
    return out


def _arbitrary_manual_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    raw=values.get("section_geometry_2d")
    if not isinstance(raw, Mapping): raise FireUIError("manual section properties must be an object")
    def req(k):
        v=raw.get(k)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)) or float(v)<=0: raise FireUIError(f"manual section property {k} must be finite and > 0")
        return float(v)
    A=req("A_gross"); Jx=req("J_x"); Jy=req("J_y")
    out={"A_gross":A,"J_x":Jx,"J_y":Jy,"J_min":min(Jx,Jy),"W_pl_x":req("W_pl_x"),"W_pl_y":req("W_pl_y"),"section_properties_ready":True,
         "W_el_x_pos":req("W_el_x_pos"),"W_el_x_neg":req("W_el_x_neg"),"W_el_y_pos":req("W_el_y_pos"),"W_el_y_neg":req("W_el_y_neg"),
         "section_y_pos_extent":Jx/req("W_el_x_pos"),"section_y_neg_extent":Jx/req("W_el_x_neg"),
         "section_is_box":bool(raw["section_is_box"]) if "section_is_box" in raw else False,"section_is_channel":bool(raw["section_is_channel"]) if "section_is_channel" in raw else False,"section_is_pipe":bool(raw["section_is_pipe"]) if "section_is_pipe" in raw else False,
         "major_axis_is_x":Jx>=Jy,"sp16_i_symmetry_class":str(raw["sp16_i_symmetry_class"]) if "sp16_i_symmetry_class" in raw else "not_i","section_family":str(raw["section_family"]) if "section_family" in raw else "other",
         "section_geometry_2d_normalized":{"source":"manual_properties","user_bundle":dict(raw)},"sp16_gross_geometry_solver_ok":True}
    if "I_omega_gross" in raw and raw["I_omega_gross"] is not None: out["I_omega_gross"]=req("I_omega_gross")
    if "W_omega_gross" in raw and raw["W_omega_gross"] is not None: out["W_omega_gross"]=req("W_omega_gross")
    if "I_shear_gross" in raw and raw["I_shear_gross"] is not None: out["I_shear_gross"]=req("I_shear_gross")
    if "S_shear_gross" in raw and raw["S_shear_gross"] is not None: out["S_shear_gross"]=req("S_shear_gross")
    if "P_heated_m" in raw and raw["P_heated_m"] is not None: out["P_heated"]=req("P_heated_m")
    out["W_pl_min_gross"]=min(out["W_pl_x"],out["W_pl_y"])
    return out


def _double_branch_executor(catalog: InterimProfileCatalog):
    def run(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        axis=str(values["double_branch_symmetry_axis"]); spacing=_num(values,"double_branch_spacing_mm")
        fid=int(_num(values,"double_branch_family_id")); row=int(_num(values,"double_branch_source_row_id")); designation=str(values["double_branch_designation"])
        r=catalog.resolve(fid,designation,source_row_id=row); p=r["catalog_properties_interim"]; d=r["dimensions"]
        A=float(p["A_mm2"]); Ix=float(p["Ix_mm4"]); Iy=float(p["Iy_mm4"]); h=float(d["h_mm"]); b=float(d["b_mm"])
        if axis=="y":
            Jx=2*Ix; Jy=2*(Iy+A*(spacing/2)**2); yext=h/2; xext=spacing/2+b/2
        elif axis=="x":
            Jx=2*(Ix+A*(spacing/2)**2); Jy=2*Iy; yext=spacing/2+h/2; xext=b/2
        else: raise FireUIError("double_branch_symmetry_axis must be x or y")
        return {"A_gross":2*A,"J_x":Jx,"J_y":Jy,"J_min":min(Jx,Jy),"section_properties_ready":True,"section_family":"built_up",
                "section_is_box":False,"section_is_channel":False,"section_is_pipe":False,"major_axis_is_x":Jx>=Jy,
                "section_y_pos_extent":yext,"section_y_neg_extent":yext,"W_el_x_pos":Jx/yext,"W_el_x_neg":Jx/yext,"W_el_y_pos":Jy/xext,"W_el_y_neg":Jy/xext,
                "section_geometry_2d_normalized":{"source":"double_branch_catalog","axis":axis,"spacing_mm":spacing,"branch":r["profile_ref"]},"sp16_gross_geometry_solver_ok":True}
    return run


def build_fire_ui12_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Bind FIRE-UI1.2 section-authoring geometry nodes to deterministic production geometry executors.

    Standard reference:
        Geometry support layer for СП 16.13330.2017 and СП 554.1311500.2026 DAG inputs; no member resistance equation is implemented here.

    Parameters:
        catalog: Frozen interim profile catalog resolver used for exact family/designation/source-row selections.
        registry: Optional existing execution registry to extend without overwriting explicit caller bindings.

    Returns:
        ExecutionRegistry containing catalog, parametric, manual-properties and two-branch geometry bindings.

    Assumptions:
        Profile-catalog identities and UI payloads have already passed their node-level validation.

    Sign convention:
        Section x/y axes follow the packaged DAG and catalog conventions; two-branch spacing is positive centre-to-centre distance.

    Unit convention:
        Section dimensions mm, area mm2, second moments mm4, section moduli mm3 and optional heated perimeter m.

    Applicability:
        FIRE-UI1.2 geometry authoring routes only; lattice/batten mechanics, material resistance and fire equations remain downstream.

    Limitations:
        Parametric sharp-corner templates do not reproduce rolled fillets; catalog rows remain interim pending original-GOST audit.

    Raises:
        Geometry/input errors are raised later by the selected executor as FireUIError; registration itself requires valid callable bindings.

    Examples:
        ``registry = build_fire_ui12_registry(InterimProfileCatalog())``

    Tests:
        tests/test_fire_ui1_frontend.py covers catalog, parametric, arbitrary and two-branch end-to-end continuation.

    Implementation notes:
        Existing caller registrations win; FIRE-UI1.2 defaults are installed only for unbound node IDs.
    """
    reg=registry or ExecutionRegistry()
    defaults={"SP554_G_CATALOG":_catalog_executor(catalog),"SP554_G_PARAMETRIC":_parametric_executor,"SP554_G_ARBITRARY":_arbitrary_manual_executor,"SP554_G_DOUBLE_BRANCH":_double_branch_executor(catalog)}
    for node_id,executor in defaults.items():
        if reg.get(node_id) is None: reg.register(node_id,executor)
    return reg
