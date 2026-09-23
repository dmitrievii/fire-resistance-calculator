"""v0.92 Streamlit closure for the full SP16 Section-10 effective-length routes."""
from __future__ import annotations

import copy
import json
from typing import Any, Mapping

from standard_core.fire_ui0 import GuidedCalculationService, GuidedCalculationSession, ExecutionRegistry
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


def _old_axis(old: Mapping[str, Any], axis: str) -> Mapping[str, Any]:
    value = old.get(axis)
    return value if isinstance(value, Mapping) else {}


def _number(st, label: str, old: Mapping[str, Any], key: str, widget_key: str, *, positive: bool = False, integer: bool = False):
    raw = old.get(key)
    value = float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
    result = st.number_input(label, value=value, format="%g", key=widget_key)
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


def _text(st, label: str, old: Mapping[str, Any], key: str, widget_key: str, *, placeholder: str = ""):
    value = st.text_input(label, value=str(old.get(key) or ""), placeholder=placeholder, key=widget_key).strip()
    return value, bool(value)


def _external_fields(core: Any, card: Mapping[str, Any], axis: str, route: Mapping[str, Any], mode_key: str):
    st = core.st
    ext = route.get("external_effective_length") if isinstance(route.get("external_effective_length"), Mapping) else {}
    length, ok_l = _number(
        st, f"Подтверждённая расчётная длина l_eff,{axis}, мм", ext, "value_mm",
        core._key(mode_key, card["node_id"], axis, "section10", "external_length"), positive=True,
    )
    basis, ok_b = _text(
        st, "Основание / расчётная модель / нормативный маршрут", ext, "basis",
        core._key(mode_key, card["node_id"], axis, "section10", "external_basis"),
        placeholder="Укажите проверяемый источник результата",
    )
    return ({"value_mm": length, "basis": basis} if ok_l and ok_b else None), bool(ok_l and ok_b)


def _render_section10_route(core: Any, card: Mapping[str, Any], axis: str, prior: Mapping[str, Any], mode_key: str):
    st = core.st
    old_route = prior.get("route") if isinstance(prior.get("route"), Mapping) else {}
    presentation = card.get("presentation") or {}
    options = list(presentation.get("section10_route_options") or [])
    if not options:
        options = [{"value": value, "label": label} for value, label in SECTION10_ROUTE_KINDS]
    values = [str(row["value"]) for row in options]
    labels = {str(row["value"]): str(row.get("label") or row["value"]) for row in options}
    old_kind = str(old_route.get("kind") or "")
    kind = st.selectbox(
        "Нормативный маршрут СП16 §10",
        values,
        index=values.index(old_kind) if old_kind in values else None,
        placeholder="— выберите маршрут —",
        format_func=lambda value: labels.get(value, value),
        key=core._key(mode_key, card["node_id"], axis, "section10", "kind"),
    )
    if kind is None:
        return {}, False
    route: dict[str, Any] = {"kind": kind}
    ready = True

    if kind in {"eq136_truss_chord_in_plane", "eq138_built_up_branch_in_plane"}:
        route["segment_length_mm"], ok1 = _number(st, "Длина участка l, мм", old_route, "segment_length_mm", core._key(mode_key, card["node_id"], axis, kind, "l"), positive=True)
        route["adjacent_force_ratio_alpha"], ok2 = _number(st, "Отношение усилий α", old_route, "adjacent_force_ratio_alpha", core._key(mode_key, card["node_id"], axis, kind, "alpha"))
        ready = ok1 and ok2
    elif kind in {"eq137_truss_chord_out_of_plane", "eq139_built_up_branch_out_of_plane"}:
        route["braced_length_mm"], ok1 = _number(st, "Закреплённая длина l₁, мм", old_route, "braced_length_mm", core._key(mode_key, card["node_id"], axis, kind, "l1"), positive=True)
        route["section_count_k"], ok2 = _number(st, "Число участков k", old_route, "section_count_k", core._key(mode_key, card["node_id"], axis, kind, "k"), positive=True, integer=True)
        route["other_force_sum_ratio_beta"], ok3 = _number(st, "Параметр β", old_route, "other_force_sum_ratio_beta", core._key(mode_key, card["node_id"], axis, kind, "beta"))
        ready = ok1 and ok2 and ok3 and int(route.get("section_count_k") or 0) >= 2
    elif kind == "table24_truss_member":
        route["table24_case"], ok1 = _text(st, "Строка/случай таблицы 24", old_route, "table24_case", core._key(mode_key, card["node_id"], axis, kind, "case"), placeholder="Напр.: single_angle_equal_restraint_distances")
        route["member_role"], ok2 = _text(st, "Роль элемента", old_route, "member_role", core._key(mode_key, card["node_id"], axis, kind, "role"), placeholder="Напр.: chord")
        route["geometric_length_mm"], ok3 = _number(st, "Геометрическая длина l, мм", old_route, "geometric_length_mm", core._key(mode_key, card["node_id"], axis, kind, "l"), positive=True)
        extra = old_route.get("out_of_plane_braced_length_mm")
        use_extra = st.checkbox("Задать отдельную длину из плоскости", value=isinstance(extra, (int, float)), key=core._key(mode_key, card["node_id"], axis, kind, "use_l1"))
        if use_extra:
            route["out_of_plane_braced_length_mm"], ok4 = _number(st, "Длина из плоскости l₁, мм", old_route, "out_of_plane_braced_length_mm", core._key(mode_key, card["node_id"], axis, kind, "l1"), positive=True)
            ready = ok1 and ok2 and ok3 and ok4
        else:
            ready = ok1 and ok2 and ok3
    elif kind == "table25_cross_lattice":
        route["joint_case"], ok1 = _text(st, "Схема узла таблицы 25", old_route, "joint_case", core._key(mode_key, card["node_id"], axis, kind, "joint"), placeholder="Напр.: both_members_continuous")
        route["supporting_state"], ok2 = _text(st, "Состояние поддерживающего элемента", old_route, "supporting_state", core._key(mode_key, card["node_id"], axis, kind, "support"), placeholder="Напр.: inactive")
        route["node_to_intersection_length_mm"], ok3 = _number(st, "От узла до пересечения, мм", old_route, "node_to_intersection_length_mm", core._key(mode_key, card["node_id"], axis, kind, "lint"), positive=True)
        route["full_member_length_mm"], ok4 = _number(st, "Полная длина элемента, мм", old_route, "full_member_length_mm", core._key(mode_key, card["node_id"], axis, kind, "lfull"), positive=True)
        ready = ok1 and ok2 and ok3 and ok4
    elif kind == "table26_structural_member":
        route["member_case"], ok1 = _text(st, "Случай таблицы 26", old_route, "member_case", core._key(mode_key, card["node_id"], axis, kind, "case"), placeholder="Напр.: single_angle_welded_or_two_bolts")
        route["geometric_length_mm"], ok2 = _number(st, "Геометрическая длина, мм", old_route, "geometric_length_mm", core._key(mode_key, card["node_id"], axis, kind, "l"), positive=True)
        route["is_lattice_member"] = st.checkbox("Элемент решётки", value=bool(old_route.get("is_lattice_member")), key=core._key(mode_key, card["node_id"], axis, kind, "lattice"))
        route["is_beam_column"] = st.checkbox("Стержень с N+M", value=bool(old_route.get("is_beam_column")), key=core._key(mode_key, card["node_id"], axis, kind, "beam_column"))
        route["bending_plane_relation"], ok3 = _text(st, "Положение плоскости изгиба", old_route, "bending_plane_relation", core._key(mode_key, card["node_id"], axis, kind, "plane"), placeholder="Напр.: perpendicular_axis_x")
        if "geometric_slenderness_l_over_i_min" in old_route or st.checkbox("Требуется l/i_min для строки таблицы", value="geometric_slenderness_l_over_i_min" in old_route, key=core._key(mode_key, card["node_id"], axis, kind, "use_slender")):
            route["geometric_slenderness_l_over_i_min"], ok4 = _number(st, "Геометрическая гибкость l/i_min", old_route, "geometric_slenderness_l_over_i_min", core._key(mode_key, card["node_id"], axis, kind, "slender"), positive=True)
        else:
            ok4 = True
        ready = ok1 and ok2 and ok3 and ok4
    elif kind == "table27_29_spatial_member":
        route["table27_row"], ok1 = _text(st, "Строка таблицы 27", old_route, "table27_row", core._key(mode_key, card["node_id"], axis, kind, "row27"), placeholder="Напр.: diagonal_15ad")
        route["force_state"], ok2 = _text(st, "Состояние усилия", old_route, "force_state", core._key(mode_key, card["node_id"], axis, kind, "force"), placeholder="compression / tension")
        base_old = old_route.get("base_lengths_mm") if isinstance(old_route.get("base_lengths_mm"), Mapping) else {}
        base_text = st.text_area("Базовые длины таблицы 27, мм", value=json.dumps(base_old, ensure_ascii=False) if base_old else "", placeholder='{"ld": 1000, "ld1": 900}', key=core._key(mode_key, card["node_id"], axis, kind, "base_lengths"))
        try:
            base = json.loads(base_text) if base_text.strip() else None
            ok3 = isinstance(base, dict) and bool(base)
        except Exception:
            base, ok3 = None, False
        if ok3:
            route["base_lengths_mm"] = base
        numeric_keys = (
            ("chord_min_inertia_mm4", "Imin пояса, мм⁴"), ("diagonal_length_mm", "Длина раскоса, мм"),
            ("diagonal_min_inertia_mm4", "Imin раскоса, мм⁴"), ("chord_panel_length_mm", "Панель пояса, мм"),
            ("alternate_diagonal_length_mm", "Альтернативная длина раскоса, мм"),
            ("geometric_slenderness_l_over_i_min", "Геометрическая гибкость l/i_min"),
        )
        oks = [ok1, ok2, ok3]
        for key, label in numeric_keys:
            route[key], ok = _number(st, label, old_route, key, core._key(mode_key, card["node_id"], axis, kind, key), positive=True)
            oks.append(ok)
        for key, label, placeholder in (
            ("table28_joint_case", "Случай таблицы 28", "support_interrupted_fig15d"),
            ("supporting_state", "Состояние поддерживающего элемента", "inactive"),
            ("connection_case", "Соединение таблицы 29", "welded_or_two_bolts"),
            ("gusset_configuration", "Конфигурация фасонки", "no_gusset_ends"),
        ):
            route[key], ok = _text(st, label, old_route, key, core._key(mode_key, card["node_id"], axis, kind, key), placeholder=placeholder)
            oks.append(ok)
        route["out_of_plane_variant"] = st.checkbox("Вариант из плоскости", value=bool(old_route.get("out_of_plane_variant")), key=core._key(mode_key, card["node_id"], axis, kind, "outplane"))
        ready = all(oks)
    elif kind == "table30_column":
        schemes = [f"scheme_{i}" for i in range(1, 9)]
        old_scheme = str(old_route.get("scheme_id") or "")
        route["scheme_id"] = st.selectbox("Схема таблицы 30", schemes, index=schemes.index(old_scheme) if old_scheme in schemes else None, placeholder="— выберите —", key=core._key(mode_key, card["node_id"], axis, kind, "scheme"))
        route["column_length_mm"], ok2 = _number(st, "Геометрическая длина колонны L, мм", old_route, "column_length_mm", core._key(mode_key, card["node_id"], axis, kind, "L"), positive=True)
        ready = route["scheme_id"] is not None and ok2
    elif kind == "table31_frame_column":
        route["same_load_combination_confirmed"] = st.checkbox("Параметры μ определены для той же расчётной комбинации", value=bool(old_route.get("same_load_combination_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "same_combo"))
        methods = ["eq141_sway_p0", "eq142_sway_p_inf", "eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2", "eq145_nonsway", "table31_special_case"]
        old_method = str(old_route.get("mu_method") or "")
        route["mu_method"] = st.selectbox("Определение μ", methods, index=methods.index(old_method) if old_method in methods else None, placeholder="— выберите —", key=core._key(mode_key, card["node_id"], axis, kind, "mu_method"))
        ok_params = route["mu_method"] is not None
        if route["mu_method"] in {"eq141_sway_p0", "eq142_sway_p_inf", "eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2", "eq145_nonsway"}:
            route["n_parameter"], okn = _number(st, "Параметр n", old_route, "n_parameter", core._key(mode_key, card["node_id"], axis, kind, "n"))
            ok_params = ok_params and okn
        if route["mu_method"] in {"eq143_sway_n_le_0_2", "eq144_sway_n_gt_0_2", "eq145_nonsway"}:
            route["p_parameter"], okp = _number(st, "Параметр p", old_route, "p_parameter", core._key(mode_key, card["node_id"], axis, kind, "p"))
            ok_params = ok_params and okp
        if route["mu_method"] == "table31_special_case":
            route["special_case_id"], oka = _text(st, "Специальный случай таблицы 31", old_route, "special_case_id", core._key(mode_key, card["node_id"], axis, kind, "special_id"))
            route["special_case_parameter"], okb = _number(st, "Параметр специального случая", old_route, "special_case_parameter", core._key(mode_key, card["node_id"], axis, kind, "special_parameter"), positive=True)
            ok_params = ok_params and oka and okb
        route["column_length_mm"], ok_l = _number(st, "Геометрическая длина колонны L, мм", old_route, "column_length_mm", core._key(mode_key, card["node_id"], axis, kind, "L"), positive=True)
        route["apply_eq146_nonuniform_loading"] = st.checkbox("Уточнить μ по формуле (146)", value=bool(old_route.get("apply_eq146_nonuniform_loading")), key=core._key(mode_key, card["node_id"], axis, kind, "eq146"))
        if route["apply_eq146_nonuniform_loading"]:
            for key, label in (("checked_column_inertia_mm4", "I проверяемой колонны, мм⁴"), ("total_column_force_n", "ΣN, Н"), ("checked_column_force_n", "N проверяемой колонны, Н"), ("total_column_inertia_mm4", "ΣI, мм⁴")):
                route[key], ok = _number(st, label, old_route, key, core._key(mode_key, card["node_id"], axis, kind, key), positive=True)
                ok_params = ok_params and ok
        route["apply_eq147_deformation_reduction"] = st.checkbox("Учесть деформации по формуле (147)", value=bool(old_route.get("apply_eq147_deformation_reduction")), key=core._key(mode_key, card["node_id"], axis, kind, "eq147"))
        if route["apply_eq147_deformation_reduction"]:
            fields = (("relative_slenderness", "Условная гибкость"), ("moment_n_mm", "M, Н·мм"), ("nonsway_reference_moment_n_mm", "M₀, Н·мм"), ("area_mm2", "A, мм²"), ("axial_force_n", "N, Н"), ("compressed_fibre_section_modulus_mm3", "Wc, мм³"))
            for key, label in fields:
                route[key], ok = _number(st, label, old_route, key, core._key(mode_key, card["node_id"], axis, kind, key), positive=(key != "nonsway_reference_moment_n_mm"))
                ok_params = ok_params and ok
        use_global = st.checkbox("Задать H и B рамы для проверки п. 10.3.5", value="frame_total_height_mm" in old_route or "frame_width_mm" in old_route, key=core._key(mode_key, card["node_id"], axis, kind, "global_dims"))
        if use_global:
            route["frame_total_height_mm"], okh = _number(st, "Полная высота рамы H, мм", old_route, "frame_total_height_mm", core._key(mode_key, card["node_id"], axis, kind, "H"), positive=True)
            route["frame_width_mm"], okb = _number(st, "Ширина рамы B, мм", old_route, "frame_width_mm", core._key(mode_key, card["node_id"], axis, kind, "B"), positive=True)
            route["global_frame_stability_confirmed"] = st.checkbox("Общая устойчивость рамы проверена", value=bool(old_route.get("global_frame_stability_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "global_ok"))
            ok_params = ok_params and okh and okb
        ready = bool(route["same_load_combination_confirmed"] and ok_params and ok_l)
    elif kind == "out_of_plane_column_10_3_9":
        route["use_restraint_spacing"] = st.checkbox("l_eff равна расстоянию между закреплениями", value=bool(old_route.get("use_restraint_spacing", True)), key=core._key(mode_key, card["node_id"], axis, kind, "use_spacing"))
        if route["use_restraint_spacing"]:
            route["restraint_spacing_mm"], ready = _number(st, "Расстояние между закреплениями, мм", old_route, "restraint_spacing_mm", core._key(mode_key, card["node_id"], axis, kind, "spacing"), positive=True)
        else:
            ext, ready = _external_fields(core, card, axis, old_route, mode_key)
            if ext:
                route["external_effective_length"] = ext
    elif kind == "gallery_support_10_3_10":
        dirs = ["longitudinal", "transverse"]
        old_dir = str(old_route.get("direction") or "")
        route["direction"] = st.selectbox("Направление", dirs, index=dirs.index(old_dir) if old_dir in dirs else None, placeholder="— выберите —", key=core._key(mode_key, card["node_id"], axis, kind, "direction"))
        oks = [route["direction"] is not None]
        for key, label in (("support_height_mm", "Высота опоры, мм"), ("node_spacing_mm", "Расстояние между узлами, мм"), ("mu", "Коэффициент μ")):
            route[key], ok = _number(st, label, old_route, key, core._key(mode_key, card["node_id"], axis, kind, key), positive=True)
            oks.append(ok)
        route["overall_built_up_cantilever_stability_confirmed"] = st.checkbox("Устойчивость всей сквозной консольной опоры проверена", value=bool(old_route.get("overall_built_up_cantilever_stability_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "overall_ok"))
        ready = all(oks) and route["overall_built_up_cantilever_stability_confirmed"]
    elif kind in {"stepped_column_10_3_7_external", "crossing_brace_external_10_1_3"}:
        ext, ready = _external_fields(core, card, axis, old_route, mode_key)
        if ext:
            route["external_effective_length"] = ext
    elif kind == "certified_software_10_3_11":
        route["certified_software_confirmed"] = st.checkbox("ПО сертифицировано", value=bool(old_route.get("certified_software_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "certified"))
        route["elastic_steel_confirmed"] = st.checkbox("Расчёт выполнен в упругой стадии стали", value=bool(old_route.get("elastic_steel_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "elastic"))
        route["undeformed_scheme_confirmed"] = st.checkbox("Использована недеформированная расчётная схема", value=bool(old_route.get("undeformed_scheme_confirmed")), key=core._key(mode_key, card["node_id"], axis, kind, "undeformed"))
        ext, ok_ext = _external_fields(core, card, axis, old_route, mode_key)
        if ext:
            route["external_effective_length"] = ext
        ready = bool(route["certified_software_confirmed"] and route["elastic_steel_confirmed"] and route["undeformed_scheme_confirmed"] and ok_ext)

    return route, bool(ready)


def _render_effective_length_editor(core: Any, card: Mapping[str, Any], old_payload: Any, mode_key: str):
    st = core.st
    old = old_payload if isinstance(old_payload, Mapping) else {}
    presentation = card.get("presentation") or {}
    table_options = list(presentation.get("table30_options") or [])
    option_values = [row.get("value") for row in table_options]
    option_labels = {row.get("value"): str(row.get("label") or row.get("value")) for row in table_options}
    option_desc = {row.get("value"): str(row.get("description") or "") for row in table_options}

    methods = ["table30", "verified_analysis", SECTION10_METHOD]
    method_labels = {
        "table30": "Колонна по СП16, таблица 30",
        "verified_analysis": "Задать подтверждённую l_eff напрямую",
        SECTION10_METHOD: "Выбрать полный нормативный маршрут СП16 §10",
    }
    axes: dict[str, dict[str, Any]] = {}
    ready = True
    cols = st.columns(2, gap="large")
    for col, axis, title in zip(cols, ("z", "y"), ("Сильная ось z", "Слабая ось y")):
        prior = _old_axis(old, axis)
        with col:
            st.markdown(f"**{title}**")
            current = prior.get("method") if prior.get("method") in methods else None
            method = st.radio("Как определяется расчётная длина?", methods, index=methods.index(current) if current in methods else None, format_func=lambda value: method_labels[value], key=core._key(mode_key, card["node_id"], axis, "method"))
            axis_payload: dict[str, Any] = {}
            if method == "table30":
                current_scheme = prior.get("scheme_id") if prior.get("scheme_id") in option_values else None
                scheme = st.selectbox("Схема закрепления и вид нагрузки", option_values, index=option_values.index(current_scheme) if current_scheme in option_values else None, placeholder="— выберите фактическую схему —", format_func=lambda value: option_labels.get(value, str(value)), key=core._key(mode_key, card["node_id"], axis, "scheme"))
                if scheme is not None:
                    st.caption(option_desc.get(scheme, ""))
                    axis_payload = {"method": "table30", "scheme_id": scheme}
                else:
                    ready = False
            elif method == "verified_analysis":
                leff, ok_l = _number(st, f"Расчётная длина l_eff,{axis}, мм", prior, "effective_length_mm", core._key(mode_key, card["node_id"], axis, "leff"), positive=True)
                basis, ok_b = _text(st, "Основание / расчётная модель", prior, "basis", core._key(mode_key, card["node_id"], axis, "basis"), placeholder="Например: расчётная схема КЭ, СП16 п. 10.3.11 …")
                if ok_l and ok_b:
                    axis_payload = {"method": "verified_analysis", "effective_length_mm": leff, "basis": basis}
                else:
                    ready = False
            elif method == SECTION10_METHOD:
                route, ok = _render_section10_route(core, card, axis, prior, mode_key)
                if ok:
                    axis_payload = {"method": SECTION10_METHOD, "route": route}
                else:
                    ready = False
            else:
                ready = False
            axes[axis] = axis_payload

    any_table30 = any(payload.get("method") == "table30" for payload in axes.values())
    member_length = None
    if any_table30:
        st.divider()
        st.caption("Для упрощённого режима таблицы 30 коэффициент μ применяется к общей геометрической длине L по формуле (140): l_eff = μL.")
        member_length, ok = _number(st, "Геометрическая длина элемента L, мм", old, "member_length_mm", core._key(mode_key, card["node_id"], "member_length"), positive=True)
        ready = ready and ok

    payload: dict[str, Any] = {"z": axes["z"], "y": axes["y"]}
    if any_table30 and member_length is not None:
        payload["member_length_mm"] = member_length
    st.caption("Оси активного контракта: z — сильная, y — слабая. Расчётные длины не переименовываются через историческую ось x.")
    return payload, None, bool(ready and axes["z"] and axes["y"])


def _replay(source: GuidedCalculationSession, model, registry: ExecutionRegistry) -> GuidedCalculationSession:
    migrated = GuidedCalculationSession(model, entry_node_id=source.entry_node_id, registry=registry)
    for row in copy.deepcopy(source.interaction_history):
        if migrated.current_node_id != row.get("node_id"):
            break
        try:
            migrated.submit(row.get("payload"), provenance=row.get("provenance"))
        except Exception:
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
        except Exception:
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
            return _render_effective_length_editor(core, card, old_payload, mode_key)
        return previous_render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key)

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install"]
