"""v0.92 Streamlit editor for the audited SP16 Section-10 effective-length routes.

This layer collects engineering selectors only.  All Section-10 formulae remain
owned by ``standard_core.effective_length_workflows``; invalid/incomplete routes
are rejected there fail-closed.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from standard_core.fire_ui0 import (
    ExecutionRegistry,
    FireUIError,
    GuidedCalculationService,
    GuidedCalculationSession,
)
from standard_core.sp16_mech7_v076_graph_overlay import INPUT_NODE_ID
from standard_core.sp16_mech7_v092_effective_length import (
    GRAPH_SUFFIX,
    SECTION10_METHOD,
    SECTION10_ROUTE_KINDS,
    build_model,
    install_registry_remediation,
)

_INSTALLED = "_fire_v092_effective_length_installed"
_COMPONENT = "effective_length_zy_editor"

_TABLE24_CASES = (
    "in_plane_general",
    "in_plane_single_angle_or_butt_web",
    "out_of_plane_general",
    "out_of_plane_butt_web",
    "single_angle_equal_restraint_distances",
)
_TABLE24_ROLES = ("chord", "support_diagonal_or_post", "other_web")
_TABLE25_JOINTS = (
    "both_members_continuous",
    "support_interrupted_considered_continuous",
    "both_interrupted_with_gusset",
)
_TABLE25_STATES = ("tension", "inactive", "compression")
_TABLE26_CASES = (
    "general",
    "continuous_chord_or_butt_node",
    "single_angle_welded_or_two_bolts",
    "single_angle_one_bolt",
)
_TABLE27_ROWS = (
    "chord_15abc",
    "chord_15gd",
    "chord_15e",
    "diagonal_15ad",
    "diagonal_15bcge",
    "strut_15be",
    "strut_15c",
)
_TABLE28_JOINTS = (
    "both_continuous",
    "support_interrupted_fig15a",
    "support_interrupted_fig15d",
    "intersection_out_of_plane_braced",
)
_TABLE29_CONNECTIONS = (
    "welded_or_two_bolts",
    "one_bolt_without_gusset",
)
_TABLE29_GUSSETS = ("no_gusset_ends", "one_end_gusset", "both_ends_gusset")
_TABLE31_METHODS = (
    "eq141_sway_p0",
    "eq142_sway_p_inf",
    "eq143_sway_n_le_0_2",
    "eq144_sway_n_gt_0_2",
    "eq145_nonsway",
    "table31_special_case",
)
_TABLE31_SPECIAL_CASES = (
    "sway_p0_n_0_03_to_0_2",
    "sway_p0_n_gt_0_2",
    "sway_n_inf_p_0_03_to_50",
    "sway_p_inf_n_0_03_to_0_2",
    "sway_p_inf_n_gt_0_2",
    "nonsway_p0",
    "nonsway_p_inf",
)


def _prior_map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _num(core: Any, label: str, old: Mapping[str, Any], name: str, key: str, *, positive: bool = False, integer: bool = False):
    raw = old.get(name)
    value = float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
    result = core.st.number_input(label, value=value, format="%g", key=key)
    if result is None:
        return None, False
    x = float(result)
    if positive and x <= 0.0:
        return None, False
    if integer:
        if int(x) != x:
            return None, False
        return int(x), True
    return x, True


def _txt(core: Any, label: str, old: Mapping[str, Any], name: str, key: str, *, placeholder: str = ""):
    value = core.st.text_input(label, value=str(old.get(name) or ""), placeholder=placeholder, key=key).strip()
    return value, bool(value)


def _sel(core: Any, label: str, options: tuple[str, ...] | list[str], current: Any, key: str):
    values = list(options)
    cur = str(current) if current is not None else ""
    return core.st.selectbox(
        label,
        values,
        index=values.index(cur) if cur in values else None,
        placeholder="— выберите —",
        key=key,
    )


def _external(core: Any, card: Mapping[str, Any], axis: str, old_route: Mapping[str, Any], mode_key: str):
    old = _prior_map(old_route.get("external_effective_length"))
    value, ok1 = _num(
        core,
        f"Подтверждённая расчётная длина l_eff,{axis}, мм",
        old,
        "value_mm",
        core._key(mode_key, card["node_id"], axis, "ext", "value"),
        positive=True,
    )
    basis, ok2 = _txt(
        core,
        "Основание результата / расчётная модель",
        old,
        "basis",
        core._key(mode_key, card["node_id"], axis, "ext", "basis"),
        placeholder="Нормативный маршрут, модель, версия ПО или расчётный документ",
    )
    return ({"value_mm": value, "basis": basis} if ok1 and ok2 else None), bool(ok1 and ok2)


def _optional_positive(core: Any, label: str, old: Mapping[str, Any], name: str, key: str):
    enabled = core.st.checkbox(
        f"Задать: {label}",
        value=name in old,
        key=f"{key}:enabled",
    )
    if not enabled:
        return None, True
    return _num(core, label, old, name, key, positive=True)


def _section10_route(core: Any, card: Mapping[str, Any], axis: str, prior: Mapping[str, Any], mode_key: str):
    st = core.st
    old = _prior_map(prior.get("route"))
    presentation = card.get("presentation") or {}
    option_rows = presentation.get("section10_route_options") or [
        {"value": value, "label": label} for value, label in SECTION10_ROUTE_KINDS
    ]
    values = [str(row["value"]) for row in option_rows]
    labels = {str(row["value"]): str(row.get("label") or row["value"]) for row in option_rows}
    kind = st.selectbox(
        "Нормативный маршрут СП16 §10",
        values,
        index=values.index(str(old.get("kind"))) if str(old.get("kind")) in values else None,
        placeholder="— выберите маршрут —",
        format_func=lambda x: labels[x],
        key=core._key(mode_key, card["node_id"], axis, "s10", "kind"),
    )
    if kind is None:
        return {}, False
    route: dict[str, Any] = {"kind": kind}
    k = lambda name: core._key(mode_key, card["node_id"], axis, "s10", kind, name)

    if kind in {"eq136_truss_chord_in_plane", "eq138_built_up_branch_in_plane"}:
        route["segment_length_mm"], a = _num(core, "Длина участка l, мм", old, "segment_length_mm", k("l"), positive=True)
        route["adjacent_force_ratio_alpha"], b = _num(core, "Отношение усилий α", old, "adjacent_force_ratio_alpha", k("alpha"))
        return route, a and b

    if kind in {"eq137_truss_chord_out_of_plane", "eq139_built_up_branch_out_of_plane"}:
        route["braced_length_mm"], a = _num(core, "Закреплённая длина l₁, мм", old, "braced_length_mm", k("l1"), positive=True)
        route["section_count_k"], b = _num(core, "Число участков k", old, "section_count_k", k("count"), positive=True, integer=True)
        route["other_force_sum_ratio_beta"], c = _num(core, "Параметр β", old, "other_force_sum_ratio_beta", k("beta"))
        return route, bool(a and b and c and int(route.get("section_count_k") or 0) >= 2)

    if kind == "table24_truss_member":
        route["table24_case"] = _sel(core, "Случай таблицы 24", _TABLE24_CASES, old.get("table24_case"), k("case"))
        route["member_role"] = _sel(core, "Роль элемента", _TABLE24_ROLES, old.get("member_role"), k("role"))
        route["geometric_length_mm"], a = _num(core, "Геометрическая длина l, мм", old, "geometric_length_mm", k("l"), positive=True)
        extra, b = _optional_positive(core, "Длина из плоскости l₁, мм", old, "out_of_plane_braced_length_mm", k("l1"))
        if extra is not None:
            route["out_of_plane_braced_length_mm"] = extra
        return route, bool(route["table24_case"] and route["member_role"] and a and b)

    if kind == "table25_cross_lattice":
        route["joint_case"] = _sel(core, "Схема узла таблицы 25", _TABLE25_JOINTS, old.get("joint_case"), k("joint"))
        route["supporting_state"] = _sel(core, "Состояние поддерживающего элемента", _TABLE25_STATES, old.get("supporting_state"), k("state"))
        route["node_to_intersection_length_mm"], a = _num(core, "От узла до пересечения l₁, мм", old, "node_to_intersection_length_mm", k("l1"), positive=True)
        route["full_member_length_mm"], b = _num(core, "Полная длина l, мм", old, "full_member_length_mm", k("l"), positive=True)
        return route, bool(route["joint_case"] and route["supporting_state"] and a and b)

    if kind == "table26_structural_member":
        route["member_case"] = _sel(core, "Случай таблицы 26", _TABLE26_CASES, old.get("member_case"), k("case"))
        route["geometric_length_mm"], a = _num(core, "Геометрическая длина l, мм", old, "geometric_length_mm", k("l"), positive=True)
        route["is_lattice_member"] = st.checkbox("Элемент решётки", value=bool(old.get("is_lattice_member")), key=k("lattice"))
        route["is_beam_column"] = st.checkbox("Стержень с N+M", value=bool(old.get("is_beam_column")), key=k("beam_column"))
        route["bending_plane_relation"], b = _txt(core, "Положение плоскости изгиба", old, "bending_plane_relation", k("plane"), placeholder="Напр.: perpendicular_axis_x")
        slender, c = _optional_positive(core, "Геометрическая гибкость l/i_min", old, "geometric_slenderness_l_over_i_min", k("slender"))
        if slender is not None:
            route["geometric_slenderness_l_over_i_min"] = slender
        return route, bool(route["member_case"] and a and b and c)

    if kind == "table27_29_spatial_member":
        row = _sel(core, "Строка таблицы 27", _TABLE27_ROWS, old.get("table27_row"), k("row"))
        force = _sel(core, "Состояние усилия", ["compression", "tension"], old.get("force_state"), k("force"))
        route["table27_row"] = row
        route["force_state"] = force
        route["out_of_plane_variant"] = st.checkbox("Вариант из плоскости", value=bool(old.get("out_of_plane_variant")), key=k("outplane"))
        old_base = _prior_map(old.get("base_lengths_mm"))
        base: dict[str, float] = {}
        required_basis: list[str] = []
        if row in {"chord_15abc", "chord_15gd", "chord_15e"}:
            required_basis = ["lm"]
        elif row == "diagonal_15ad" and force == "tension":
            required_basis = ["ld", "ld1"]
        elif row == "diagonal_15bcge":
            required_basis = ["ld"]
        elif row in {"strut_15be", "strut_15c"}:
            required_basis = ["lc"]
        ready = bool(row and force)
        for name in required_basis:
            value, ok = _num(core, f"Базовая длина {name}, мм", old_base, name, k(f"base_{name}"), positive=True)
            if ok:
                base[name] = value
            ready = ready and ok
        compression_diagonal = row in {"diagonal_15ad", "diagonal_15bcge"} and force == "compression"
        if compression_diagonal:
            fields = (
                ("chord_min_inertia_mm4", "Imin пояса, мм⁴"),
                ("diagonal_length_mm", "Длина раскоса ld, мм"),
                ("diagonal_min_inertia_mm4", "Imin раскоса, мм⁴"),
                ("chord_panel_length_mm", "Панель пояса lm, мм"),
                ("geometric_slenderness_l_over_i_min", "Геометрическая гибкость l/i_min"),
            )
            for name, label in fields:
                route[name], ok = _num(core, label, old, name, k(name), positive=True)
                ready = ready and ok
            route["connection_case"] = _sel(core, "Соединение таблицы 29", _TABLE29_CONNECTIONS, old.get("connection_case"), k("connection"))
            route["gusset_configuration"] = _sel(core, "Фасонки на концах", _TABLE29_GUSSETS, old.get("gusset_configuration"), k("gusset"))
            ready = ready and bool(route["connection_case"] and route["gusset_configuration"])
            if row == "diagonal_15ad":
                route["table28_joint_case"] = _sel(core, "Случай таблицы 28", _TABLE28_JOINTS, old.get("table28_joint_case"), k("t28"))
                route["supporting_state"] = _sel(core, "Состояние поддерживающего раскоса", _TABLE25_STATES, old.get("supporting_state"), k("support"))
                route["alternate_diagonal_length_mm"], ok = _num(core, "Длина второго раскоса ld₁, мм", old, "alternate_diagonal_length_mm", k("ld1"), positive=True)
                ready = ready and bool(route["table28_joint_case"] and route["supporting_state"] and ok)
        route["base_lengths_mm"] = base
        return route, bool(ready)

    if kind == "table30_column":
        route["scheme_id"] = _sel(core, "Схема таблицы 30", [f"scheme_{i}" for i in range(1, 9)], old.get("scheme_id"), k("scheme"))
        route["column_length_mm"], a = _num(core, "Геометрическая длина колонны L, мм", old, "column_length_mm", k("L"), positive=True)
        return route, bool(route["scheme_id"] and a)

    if kind == "table31_frame_column":
        route["same_load_combination_confirmed"] = st.checkbox(
            "Параметры μ относятся к той же расчётной комбинации",
            value=bool(old.get("same_load_combination_confirmed")),
            key=k("same_combo"),
        )
        method = _sel(core, "Определение μ", _TABLE31_METHODS, old.get("mu_method"), k("method"))
        route["mu_method"] = method
        ready = bool(route["same_load_combination_confirmed"] and method)
        if method in {"eq141_sway_p0", "eq142_sway_p_inf", "eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2", "eq145_nonsway"}:
            route["n_parameter"], ok = _num(core, "Параметр n", old, "n_parameter", k("n"), positive=method in {"eq141_sway_p0", "eq144_sway_n_gt_0_2"})
            ready = ready and ok
        if method in {"eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2", "eq145_nonsway"}:
            route["p_parameter"], ok = _num(core, "Параметр p", old, "p_parameter", k("p"), positive=method in {"eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2"})
            ready = ready and ok
        if method == "table31_special_case":
            route["special_case_id"] = _sel(core, "Специальный случай таблицы 31", _TABLE31_SPECIAL_CASES, old.get("special_case_id"), k("special"))
            route["special_case_parameter"], ok = _num(core, "Параметр специального случая", old, "special_case_parameter", k("parameter"), positive=True)
            ready = ready and bool(route["special_case_id"] and ok)
        route["column_length_mm"], ok = _num(core, "Геометрическая длина колонны L, мм", old, "column_length_mm", k("L"), positive=True)
        ready = ready and ok
        route["apply_eq146_nonuniform_loading"] = st.checkbox("Уточнить μ по формуле (146)", value=bool(old.get("apply_eq146_nonuniform_loading")), key=k("eq146"))
        if route["apply_eq146_nonuniform_loading"]:
            for name, label in (
                ("checked_column_inertia_mm4", "I проверяемой колонны, мм⁴"),
                ("total_column_force_n", "ΣN, Н"),
                ("checked_column_force_n", "N проверяемой колонны, Н"),
                ("total_column_inertia_mm4", "ΣI, мм⁴"),
            ):
                route[name], ok = _num(core, label, old, name, k(name), positive=True)
                ready = ready and ok
        route["apply_eq147_deformation_reduction"] = st.checkbox("Учесть деформации по формуле (147)", value=bool(old.get("apply_eq147_deformation_reduction")), key=k("eq147"))
        if route["apply_eq147_deformation_reduction"]:
            for name, label, positive in (
                ("relative_slenderness", "Условная гибкость", False),
                ("moment_n_mm", "M, Н·мм", True),
                ("nonsway_reference_moment_n_mm", "M₀, Н·мм", False),
                ("area_mm2", "A, мм²", True),
                ("axial_force_n", "N, Н", True),
                ("compressed_fibre_section_modulus_mm3", "Wc, мм³", True),
            ):
                route[name], ok = _num(core, label, old, name, k(name), positive=positive)
                ready = ready and ok
        use_global = st.checkbox("Задать H/B рамы для проверки п. 10.3.5", value="frame_total_height_mm" in old or "frame_width_mm" in old, key=k("use_global"))
        if use_global:
            route["frame_total_height_mm"], a = _num(core, "Полная высота рамы H, мм", old, "frame_total_height_mm", k("H"), positive=True)
            route["frame_width_mm"], b = _num(core, "Ширина рамы B, мм", old, "frame_width_mm", k("B"), positive=True)
            route["global_frame_stability_confirmed"] = st.checkbox("Общая устойчивость рамы проверена", value=bool(old.get("global_frame_stability_confirmed")), key=k("global_ok"))
            ready = ready and a and b
        return route, bool(ready)

    if kind == "out_of_plane_column_10_3_9":
        use_spacing = st.checkbox("l_eff равна расстоянию между закреплениями", value=bool(old.get("use_restraint_spacing", True)), key=k("spacing_mode"))
        route["use_restraint_spacing"] = use_spacing
        if use_spacing:
            route["restraint_spacing_mm"], ok = _num(core, "Расстояние между закреплениями, мм", old, "restraint_spacing_mm", k("spacing"), positive=True)
            return route, ok
        ext, ok = _external(core, card, axis, old, mode_key)
        if ext:
            route["external_effective_length"] = ext
        return route, ok

    if kind == "gallery_support_10_3_10":
        route["direction"] = _sel(core, "Направление", ["longitudinal", "transverse"], old.get("direction"), k("direction"))
        ready = bool(route["direction"])
        for name, label in (("support_height_mm", "Высота опоры, мм"), ("node_spacing_mm", "Расстояние между узлами, мм"), ("mu", "Коэффициент μ")):
            route[name], ok = _num(core, label, old, name, k(name), positive=True)
            ready = ready and ok
        route["overall_built_up_cantilever_stability_confirmed"] = st.checkbox("Устойчивость всей сквозной консольной опоры проверена", value=bool(old.get("overall_built_up_cantilever_stability_confirmed")), key=k("overall"))
        return route, bool(ready and route["overall_built_up_cantilever_stability_confirmed"])

    if kind in {"stepped_column_10_3_7_external", "crossing_brace_external_10_1_3"}:
        ext, ok = _external(core, card, axis, old, mode_key)
        if ext:
            route["external_effective_length"] = ext
        return route, ok

    if kind == "certified_software_10_3_11":
        route["certified_software_confirmed"] = st.checkbox("ПО сертифицировано", value=bool(old.get("certified_software_confirmed")), key=k("certified"))
        route["elastic_steel_confirmed"] = st.checkbox("Расчёт выполнен в упругой стадии стали", value=bool(old.get("elastic_steel_confirmed")), key=k("elastic"))
        route["undeformed_scheme_confirmed"] = st.checkbox("Использована недеформированная расчётная схема", value=bool(old.get("undeformed_scheme_confirmed")), key=k("undeformed"))
        ext, ok = _external(core, card, axis, old, mode_key)
        if ext:
            route["external_effective_length"] = ext
        confirmations = route["certified_software_confirmed"] and route["elastic_steel_confirmed"] and route["undeformed_scheme_confirmed"]
        return route, bool(ok and confirmations)

    return route, False


def _render_editor(core: Any, card: Mapping[str, Any], old_payload: Any, mode_key: str):
    st = core.st
    old = _prior_map(old_payload)
    presentation = card.get("presentation") or {}
    table_options = list(presentation.get("table30_options") or [])
    table_ids = [str(row["value"]) for row in table_options]
    table_labels = {str(row["value"]): str(row.get("label") or row["value"]) for row in table_options}
    methods = ["table30", "verified_analysis", SECTION10_METHOD]
    method_labels = {
        "table30": "Колонна по таблице 30 — быстрый режим",
        "verified_analysis": "Подтверждённая l_eff напрямую",
        SECTION10_METHOD: "Полный нормативный маршрут СП16 §10",
    }
    axes: dict[str, dict[str, Any]] = {}
    ready = True
    cols = st.columns(2, gap="large")
    for col, axis, title in zip(cols, ("z", "y"), ("Сильная ось z", "Слабая ось y")):
        prior = _prior_map(old.get(axis))
        with col:
            st.markdown(f"**{title}**")
            method = st.radio(
                "Определение расчётной длины",
                methods,
                index=methods.index(str(prior.get("method"))) if str(prior.get("method")) in methods else None,
                format_func=lambda x: method_labels[x],
                key=core._key(mode_key, card["node_id"], axis, "method"),
            )
            payload: dict[str, Any] = {}
            if method == "table30":
                scheme = st.selectbox(
                    "Схема таблицы 30",
                    table_ids,
                    index=table_ids.index(str(prior.get("scheme_id"))) if str(prior.get("scheme_id")) in table_ids else None,
                    placeholder="— выберите —",
                    format_func=lambda x: table_labels.get(x, x),
                    key=core._key(mode_key, card["node_id"], axis, "scheme"),
                )
                if scheme:
                    payload = {"method": "table30", "scheme_id": scheme}
                else:
                    ready = False
            elif method == "verified_analysis":
                leff, a = _num(core, f"Расчётная длина l_eff,{axis}, мм", prior, "effective_length_mm", core._key(mode_key, card["node_id"], axis, "leff"), positive=True)
                basis, b = _txt(core, "Основание / расчётная модель", prior, "basis", core._key(mode_key, card["node_id"], axis, "basis"))
                if a and b:
                    payload = {"method": "verified_analysis", "effective_length_mm": leff, "basis": basis}
                else:
                    ready = False
            elif method == SECTION10_METHOD:
                route, ok = _section10_route(core, card, axis, prior, mode_key)
                if ok:
                    payload = {"method": SECTION10_METHOD, "route": route}
                else:
                    ready = False
            else:
                ready = False
            axes[axis] = payload

    any_fast_table30 = any(row.get("method") == "table30" for row in axes.values())
    member_length = None
    if any_fast_table30:
        st.divider()
        member_length, ok = _num(core, "Геометрическая длина элемента L, мм", old, "member_length_mm", core._key(mode_key, card["node_id"], "member_length"), positive=True)
        ready = ready and ok
    result: dict[str, Any] = {"z": axes["z"], "y": axes["y"]}
    if member_length is not None:
        result["member_length_mm"] = member_length
    st.caption("Активные оси: z — сильная, y — слабая. Историческая ось x не используется как транспортный псевдоним.")
    return result, None, bool(ready and axes["z"] and axes["y"])


def _replay(source: GuidedCalculationSession, model, registry: ExecutionRegistry) -> GuidedCalculationSession:
    migrated = GuidedCalculationSession(model, entry_node_id=source.entry_node_id, registry=registry)
    for row in copy.deepcopy(source.interaction_history):
        if migrated.current_node_id != row.get("node_id"):
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except (FireUIError, ValueError, TypeError):
            break
    return migrated


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app
    previous_render_card_body = core._render_card_body

    def _invalidate_contract() -> None:
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except (AttributeError, KeyError, TypeError):
            pass

    def _upgrade(app):
        registry = app.service.registry
        install_registry_remediation(registry, app.profile_catalog)
        if GRAPH_SUFFIX in str(app.model.graph.get("graph_id") or ""):
            return app
        old_sessions = dict(app.service.sessions)
        new_model = build_model(app.model)
        new_service = GuidedCalculationService(new_model, registry=registry)
        for sid, old_session in old_sessions.items():
            new_service.sessions[sid] = _replay(old_session, new_model, registry)
        app.model = new_model
        app.service = new_service
        _invalidate_contract()
        return app

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        component = str((card.get("presentation") or {}).get("component") or "generic")
        if card.get("node_id") == INPUT_NODE_ID and component == _COMPONENT:
            return _render_editor(core, card, old_payload, mode_key)
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
