"""FIRE-UI1.3 material/strength editor support.

This module binds the guided UI material-selection block to the existing
current-SP16 Annex B/V material datasets. It does not introduce new steel
resistance formulas; exact normative strength rows are resolved by
:class:`SteelMaterialStrengthResolver`.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .fire_ui12_section_geometry import build_fire_ui12_registry
from .material_resistance import SteelMaterialStrengthResolver
from .profile_catalog import InterimProfileCatalog


PRODUCT_FORM_LABELS: dict[str, str] = {
    "parallel_flange_i": "Двутавр с параллельными гранями полок",
    "shaped_rolled": "Фасонный прокат",
    "plate_sheet_strip": "Листовой / широкополосный прокат",
    "bar_rolled": "Сортовой прокат",
    "tube": "Труба",
}

PRODUCT_FORM_TABLES: dict[str, str] = {
    "parallel_flange_i": "В.4",
    "shaped_rolled": "В.5",
    "plate_sheet_strip": "В.3",
    "bar_rolled": "В.3",
    "tube": "В.3",
}


def material_strength_catalog(resolver: SteelMaterialStrengthResolver | None = None) -> dict[str, Any]:
    """
    Summary:
        Build the compact FIRE-UI1.3 material-selection catalogue from exact materialized Annex В rows.

    Standard reference:
        Standard: СП 16.13330.2017, Changes No. 1-6 through 09.12.2024.
        Tables: В.3, В.4 and В.5.

    Parameters:
        resolver: Optional preconstructed SteelMaterialStrengthResolver; when omitted a stateless resolver is created.

    Returns:
        UI-ready product-form, grade and exact printed thickness-interval options with tabulated strengths.

    Assumptions:
        The materialized Annex В datasets are the current package source of truth.

    Sign convention:
        Strengths are non-negative magnitudes.

    Unit convention:
        Thickness is in mm and strengths are in MPa.

    Applicability:
        Supported product forms routed to СП16 Tables В.3, В.4 or В.5.

    Limitations:
        Does not infer product form from geometry and does not calculate Table 2 design resistances.

    Raises:
        ValueError when a requested materialized route is unavailable.

    Examples:
        ``material_strength_catalog()["products"]`` returns the compact selector data.

    Tests:
        tests/test_fire_ui1_frontend.py and tests/test_stage_n1_material_strength.py.

    Implementation notes:
        Thickness options preserve printed interval boundaries; no interpolation or extrapolation is introduced.
    """
    r = resolver or SteelMaterialStrengthResolver()
    products=[]
    for product_form in ("parallel_flange_i", "shaped_rolled", "plate_sheet_strip", "bar_rolled", "tube"):
        cat=r.strength_selection_catalog(product_form)
        products.append({
            "value": product_form,
            "label": PRODUCT_FORM_LABELS[product_form],
            "source_table": cat["source_table"],
            "source_sha256": cat["source_sha256"],
            "grades": cat["grades"],
        })
    return {"schema":"fire_ui13_material_strength_catalog_v1","products":products}


def resolve_material_preview(product_form: str, steel_grade: str, interval_key: str, resolver: SteelMaterialStrengthResolver | None = None) -> dict[str, Any]:
    """
    Summary:
        Resolve one exact Annex В row for the read-only material-strength preview in FIRE-UI1.3.

    Standard reference:
        Standard: СП 16.13330.2017, Changes No. 1-6 through 09.12.2024.
        Tables: В.3, В.4 and В.5; the displayed Rs value is explicitly only a preview, not the final Table 2 result.

    Parameters:
        product_form: Supported product-form route.
        steel_grade: Selected steel grade.
        interval_key: Stable key of one exact printed thickness interval.
        resolver: Optional preconstructed material resolver.

    Returns:
        Exact source-row identity and Ryn, Run, tabulated Ry/Ru plus a clearly labelled Rs preview.

    Assumptions:
        The user selects a materialized grade/interval pair exposed by the catalogue endpoint.

    Sign convention:
        Strengths are non-negative magnitudes.

    Unit convention:
        Strengths are in MPa; thickness interval bounds are in mm.

    Applicability:
        UI preview for product forms covered by current materialized Annex В tables.

    Limitations:
        Does not apply gamma_m and therefore does not replace production Table 2 resistance calculation.

    Raises:
        TypeError or ValueError for invalid or unsupported exact selections.

    Examples:
        ``resolve_material_preview("parallel_flange_i", "С255Б", "*:0|10:1")``.

    Tests:
        tests/test_fire_ui1_frontend.py and tests/test_stage_n1_material_strength.py.

    Implementation notes:
        Exact row resolution is fail-closed; no interval interpolation or extrapolation is allowed.
    """
    r=resolver or SteelMaterialStrengthResolver()
    row=r.lookup_strength_row_by_interval_key(product_form,steel_grade,interval_key)
    return {
        "schema":"fire_ui13_material_strength_preview_v1",
        "product_form":product_form,
        "product_form_label":PRODUCT_FORM_LABELS[product_form],
        "source_table":row["source_table"],
        "steel_grade":row["steel_grade_normalized"],
        "interval_key":row["thickness_interval_key"],
        "interval_label":row["thickness_interval_label"],
        "thickness_interval":row["thickness_interval"],
        "Ryn_MPa":row["Ryn_MPa"],
        "Run_MPa":row["Run_MPa"],
        "Ry_MPa":row["Ry_tabulated_MPa"],
        "Ru_MPa":row["Ru_tabulated_MPa"],
        "Rs_preview_MPa":row["Rs_from_tabulated_Ry_MPa"],
        "rs_preview_note":"Предварительный UI-показ 0.58·Ry(tabulated); production Rs по таблице 2 требует явного gamma_m и не подменяется этим preview.",
        "source_row_index":row["source_row_index"],
        "source_sha256":row["source_sha256"],
    }


def _interval_contains(interval: Mapping[str, Any], value: float) -> bool:
    lo=interval.get("min_mm"); hi=interval.get("max_mm")
    if lo is not None:
        lo=float(lo)
        if value < lo or (value == lo and not bool(interval.get("min_inclusive"))): return False
    if hi is not None:
        hi=float(hi)
        if value > hi or (value == hi and not bool(interval.get("max_inclusive"))): return False
    return True


def infer_material_context(values: Mapping[str, Any], resolver: SteelMaterialStrengthResolver | None = None) -> dict[str, Any]:
    """
    Summary:
        Infer safe product-form and governing-thickness suggestions from already resolved section geometry.

    Standard reference:
        Standard: СП 16.13330.2017, Changes No. 1-6 through 09.12.2024.
        Tables: В.3, В.4 and В.5 selection context.

    Parameters:
        values: Current guided-session quantity ledger containing normalized section geometry and product route.
        resolver: Optional material resolver used to confirm that an inferred product route is materialized.

    Returns:
        UI suggestion metadata including product form, reason and exact governing thickness when directly known.

    Assumptions:
        Normalized geometry was produced by the package SectionModel/geometry provider.

    Sign convention:
        Not applicable; this function performs categorical routing only.

    Unit convention:
        Any inferred thickness is returned in mm.

    Applicability:
        Catalog and supported parametric I, channel, angle, tee, CHS/RHS/SHS and welded-from-hot-rolled routes.

    Limitations:
        Suggestions never override user confirmation. For welded sections a single governing thickness is deliberately not invented when web and flange can differ.

    Raises:
        Resolver errors only if an inferred route is inconsistent with the materialized material tables.

    Examples:
        A catalog I-section with ``tf_mm=10`` suggests ``parallel_flange_i`` and 10 mm.

    Tests:
        tests/test_fire_ui1_frontend.py material-context endpoint cases.

    Implementation notes:
        Exact thickness is returned only when directly available from selected/parametric geometry; no geometric guessing is performed.
    """
    r=resolver or SteelMaterialStrengthResolver()
    geom=values.get("section_geometry_2d_normalized")
    route=values.get("section_product_route")
    product_form: str | None=None
    thickness: float | None=None
    reason: str | None=None
    shape: str | None=None
    dims: Mapping[str,Any]={}
    template: str | None=None
    if isinstance(geom,Mapping):
        shape=str(geom.get("shape_group")) if geom.get("shape_group") is not None else None
        template=str(geom.get("template")) if geom.get("template") is not None else None
        maybe_dims=geom.get("dimensions")
        if isinstance(maybe_dims,Mapping): dims=maybe_dims
        else: dims=geom

    if route == "welded_from_hot_rolled_product":
        product_form="plate_sheet_strip"
        reason="Сварное сечение из горячекатаного листового/полосового проката"
        # For welded sections one governing row may not represent all components.
        # Do not invent a single thickness when flange/web thicknesses can differ.
        thickness=None
    else:
        if shape == "I_ROLLED_DSYMM" or template == "i_section":
            product_form="parallel_flange_i"; reason="Двутавр с параллельными гранями полок"
            if dims.get("tf_mm") is not None: thickness=float(dims["tf_mm"])
        elif shape in {"CHANNEL","ANGLE","TEE"} or template in {"channel","angle","tee"}:
            product_form="shaped_rolled"; reason="Фасонный прокат"
            # Annex V.5 selector follows flange/shelf thickness where available.
            if dims.get("tf_mm") is not None: thickness=float(dims["tf_mm"])
            elif dims.get("t_mm") is not None: thickness=float(dims["t_mm"])
        elif shape in {"CHS","RHS_SHS"} or template in {"chs","rhs_shs"}:
            product_form="tube"; reason="Трубный профиль"
            if dims.get("t_mm") is not None: thickness=float(dims["t_mm"])
            elif dims.get("tw_mm") is not None: thickness=float(dims["tw_mm"])

    suggested_interval_key=None
    suggested_interval_label=None
    if product_form and thickness is not None and thickness > 0:
        cat=r.strength_selection_catalog(product_form)
        # Interval can only be preselected once grade is known; expose thickness now.
        # Frontend matches it against intervals of the selected grade.
        _=cat
    return {
        "schema":"fire_ui13_material_context_v1",
        "suggested_product_form":product_form,
        "suggested_product_form_label":PRODUCT_FORM_LABELS.get(product_form) if product_form else None,
        "exact_governing_thickness_mm":thickness,
        "suggestion_reason":reason,
        "section_product_route":route,
        "shape_group":shape,
        "template":template,
        "suggested_interval_key":suggested_interval_key,
        "suggested_interval_label":suggested_interval_label,
    }


def _material_route_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    product=str(values["steel_product_form"])
    table=SteelMaterialStrengthResolver().material_table_route(product)
    return {"sp16_material_table_route":{"В.3":"V3","В.4":"V4","В.5":"V5"}[table]}


def _lookup_executor(expected_route: str):
    resolver=SteelMaterialStrengthResolver()
    def run(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        route=str(values["sp16_material_table_route"])
        if route != expected_route:
            raise FireUIError(f"{node['id']} received route {route!r}, expected {expected_route!r}")
        row=resolver.lookup_strength_row_by_interval_key(
            str(values["steel_product_form"]), str(values["steel_grade"]), str(values["steel_strength_interval_key"])
        )
        return {
            "fy_norm":float(row["Ryn_MPa"]),
            "fu_norm":float(row["Run_MPa"]),
            **({"Ry_annex":float(row["Ry_tabulated_MPa"])} if row["Ry_tabulated_MPa"] is not None else {}),
            **({"Ru_annex":float(row["Ru_tabulated_MPa"])} if row["Ru_tabulated_MPa"] is not None else {}),
        }
    return run


def _normalize_grade(value: Any) -> str:
    if not isinstance(value,str) or not value.strip(): raise FireUIError("steel_grade must be text")
    return SteelMaterialStrengthResolver._normalize_grade(value)


def _steel_group_pre_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    grade=_normalize_grade(values["steel_grade"])
    if re.fullmatch(r"С(235|245|255)(?:Б|-?Б-?1)?",grade):
        # SP554 group mapping historically names plain grades; V.4 adds Б suffix.
        result="ordinary"
    elif re.fullmatch(r"С(345|345К|355|355-1|355-К|375)(?:Б|-?Б-?1)?",grade):
        result="increased"
    elif re.fullmatch(r"С(390|390-1|440|550|590)(?:Б|-?Б-?1)?",grade):
        result="high"
    elif re.fullmatch(r"С(355П|390П)",grade):
        result="fire_resistant"
    else:
        result="other"
    return {"steel_strength_group_preliminary":result}


def _steel_group_final_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    pre=str(values["steel_strength_group_preliminary"])
    if pre in {"ordinary","increased","fire_resistant"}:
        return {"steel_strength_group":pre}
    if pre == "high":
        if "high_strength_gost9651_qualified" not in values:
            raise FireUIError("high_strength_gost9651_qualified is required for high-strength steel")
        return {"steel_strength_group":"high" if bool(values["high_strength_gost9651_qualified"]) else "increased"}
    raise FireUIError(f"unsupported preliminary steel group {pre!r}")


def build_fire_ui13_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Extend the FIRE-UI1.2 geometry execution registry with FIRE-UI1.3 current-SP16 material-selection executors.

    Standard reference:
        Standard: СП 16.13330.2017, Changes No. 1-6 through 09.12.2024.
        Tables: В.3, В.4 and В.5; downstream resistance calculation remains governed by Table 2 and Table 3.

    Parameters:
        catalog: Profile catalog used by the parent section-geometry registry.
        registry: Optional existing registry; caller registrations take precedence.

    Returns:
        ExecutionRegistry containing geometry plus material-route, exact Annex В lookup and SP554 steel-group continuation bindings.

    Assumptions:
        The supplied DAG uses the FIRE-UI1.3 node identifiers frozen by v0.46.

    Sign convention:
        Not applicable to registry construction.

    Unit convention:
        Runtime lookup outputs use MPa for strengths and mm for material thickness metadata.

    Applicability:
        Guided FIRE-UI1.3 sessions that use the current package profile/material datasets.

    Limitations:
        This binding does not by itself close the full SP16-to-FIRE-D4 executor chain.

    Raises:
        FireUIError from bound executors when route prerequisites or exact material rows are invalid.

    Examples:
        ``build_fire_ui13_registry(InterimProfileCatalog())`` returns the default application registry.

    Tests:
        tests/test_fire_ui1_frontend.py end-to-end catalog-to-material continuation cases.

    Implementation notes:
        Existing caller registrations win; FIRE-UI1.3 defaults are installed only for currently unbound node IDs.
    """
    reg=build_fire_ui12_registry(catalog,registry)
    defaults={
        "SP16_K_MATERIAL_ROUTE":_material_route_executor,
        "SP16_L_RYN_V3":_lookup_executor("V3"),
        "SP16_L_RYN_V4":_lookup_executor("V4"),
        "SP16_L_RYN_V5":_lookup_executor("V5"),
        "SP554_K_STEEL_GROUP_PRE":_steel_group_pre_executor,
        "SP554_K_STEEL_GROUP_FINAL":_steel_group_final_executor,
    }
    for node_id,executor in defaults.items():
        if reg.get(node_id) is None: reg.register(node_id,executor)
    return reg
