"""v0.90 MECH9 UX overlay.

The overlay changes authoring/presentation contracts only where the qualified
N9/N10 runtimes already implement conditional semantics.  It does not change
SP16 equations or convert an unresolved engineering condition into PASS.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireDAGModel
from .sp16_mech9_remaining_ambient import bind_mech9_remaining_ambient_evidence

GRAPH_SUFFIX = "_v090_mech9_ux_report"
BINDER_NODE_ID = "SP16_C_MECH9_REMAINING_AMBIENT_BINDER"

_ENUM_LABELS: dict[str, dict[Any, str]] = {
    "sp16_mech9_fatigue_route_kind": {
        "ordinary_fatigue_12_1_2": "Обычная усталость, §12.1.2",
        "crane_runway_12_2": "Подкрановые конструкции, §12.2",
        "low_cycle_lt_1e5_12_1_1": "Малоцикловая усталость при n < 10⁵, §12.1.1",
    },
    "sp16_mech9_brittle_joint_type": {
        "tee": "Тавровое сварное соединение",
        "corner": "Угловое сварное соединение",
        "full_penetration": "Соединение с полным проплавлением",
        "other_welded": "Другое сварное соединение",
    },
    "sp16_mech9_brittle_connection_form_case": {
        "no_z_direction_stress": "Напряжения по толщине отсутствуют",
        "symmetric_corner_fillet": "Симметричное угловое соединение с угловыми швами",
        "intermediate_buttering_layer": "Соединение с промежуточным наплавленным слоем",
        "ordinary_t_fillet": "Тавровое соединение с угловыми швами",
        "t_full_or_partial_penetration": "Тавровое соединение с полным/частичным проплавлением",
        "fillet_near_free_plate_edge": "Угловой шов у свободной кромки листа",
        "corner_full_penetration": "Угловое соединение с полным проплавлением",
    },
    "sp16_mech9_brittle_restraint_level": {
        "low_free_shrinkage": "Низкая стеснённость — усадка практически свободна",
        "medium_partial_shrinkage": "Средняя стеснённость — усадка частично ограничена",
        "high_rigid_no_shrinkage": "Высокая стеснённость — усадка практически исключена",
    },
    "sp16_mech9_brittle_pass_count": {
        "one": "Один проход",
        "multiple": "Несколько проходов",
    },
    "sp16_mech9_brittle_weld_sequence": {
        "alternating_sides": "Попеременная сварка с двух сторон",
        "one_side_then_other": "Сначала одна сторона, затем другая",
    },
    "sp16_mech9_brittle_preheat": {
        "without_preheat": "Без предварительного подогрева",
        "with_preheat": "С предварительным подогревом",
    },
    "sp16_mech9_brittle_through_thickness_action": {
        "none": "Дополнительное воздействие по толщине отсутствует",
        "static_compression": "Статическое сжатие по толщине",
        "dynamic_or_vibratory": "Динамическое или вибрационное воздействие по толщине",
    },
    "sp16_mech9_brittle_construction_group": {
        1: "Группа конструкции 1",
        2: "Группа конструкции 2",
        3: "Группа конструкции 3",
        4: "Группа конструкции 4",
    },
    "sp16_mech9_brittle_consequence_class": {
        "KS-1": "КС-1",
        "KS-2": "КС-2",
        "KS-3": "КС-3",
    },
    "sp16_mech9_brittle_selected_z_group": {
        "Z15": "Z15",
        "Z25": "Z25",
        "Z35": "Z35",
    },
}

_ANNEX_K_LABELS = {
    "K1-01-ROLLED_OR_MACHINED_EDGE": "К.1, схема 1 — прокатная/механически обработанная кромка (группа 1)",
    "K1-01-MACHINE_GAS_CUT_EDGE": "К.1, схема 1 — машинная газовая резка кромки (группа 2)",
    "K1-02-RADIUS_200": "К.1, схема 2 — переход ширины, r = 200 мм (группа 1)",
    "K1-02-RADIUS_10": "К.1, схема 2 — переход ширины, r = 10 мм (группа 4)",
    "K1-03-FRICTION_CONNECTION": "К.1, схема 3 — фрикционное соединение (группа 1)",
    "K1-04-PAIRED_COVER_PLATES": "К.1, схема 4а — болтовое соединение с парными накладками (группа 4)",
    "K1-04-ONE_SIDED_COVER_PLATE": "К.1, схема 4б — болтовое соединение с односторонней накладкой (группа 5)",
    "K1-05-SMOOTH_TRANSITION": "К.1, схема 5 — плавный обработанный переход (группа 2)",
    "K1-06-RECTANGULAR_GUSSET": "К.1, схема 6 — прямоугольная фасонка без обработки перехода (группа 7)",
    "K1-07-GUSSET_ALPHA_LE_45": "К.1, схема 7 — фасонка, α ≤ 45° (группа 4)",
    "K1-08-LAP_GUSSET_PERIMETER_WELD": "К.1, схема 8 — фасонка внахлёст с обваркой по контуру (группа 7)",
    "K1-09-UNTREATED_BUTT_SAME": "К.1, схема 9 — необработанный стыковой шов, одинаковые сечения (группа 4)",
    "K1-10-UNTREATED_BUTT_DIFFERENT": "К.1, схема 10 — необработанный стыковой шов, разные сечения (группа 5)",
    "K1-11-GROUND_FLUSH_SAME": "К.1, схема 11а — усиление стыкового шва снято, одинаковые сечения (группа 2)",
    "K1-11-GROUND_FLUSH_DIFFERENT": "К.1, схема 11б — усиление стыкового шва снято, разные сечения (группа 3)",
    "K1-12-SHEET_ON_BACKING": "К.1, схема 12а — лист, стыковой шов на подкладке (группа 4)",
    "K1-12-PIPE_ON_BACKING_RING": "К.1, схема 12б — труба, стыковой шов на подкладном кольце (группа 4)",
    "K1-12-ROLLED_PROFILE_BUTT": "К.1, схема 12в — стык прокатных профилей (группа 4)",
    "K1-13-CONTINUOUS_LONGITUDINAL_WELDS": "К.1, схема 13 — непрерывные продольные швы (группа 2)",
    "K1-14-AUXILIARY_ALPHA_LE_45": "К.1, схема 14а — вспомогательный элемент, α ≤ 45° (группа 4)",
    "K1-14-AUXILIARY_ALPHA_90": "К.1, схема 14б — вспомогательный элемент, α = 90° (группа 7)",
    "K1-15-COVER_PLATE_TERMINATION": "К.1, схема 15 — окончание накладки на полке (группа 7)",
    "K1-16-TRANSVERSE_WELD_SMOOTH": "К.1, схема 16 — поперечный шов с плавным переходом (группа 4)",
    "K1-17-DIAPHRAGM_OR_RIB": "К.1, схема 17 — зона диафрагмы/ребра с угловыми швами (группа 5)",
    "K1-18-FIGURE_TOP": "К.1, схема 18 — верхний вариант (группа 6)",
    "K1-18-FIGURE_BOTTOM": "К.1, схема 18 — нижний вариант (группа 5)",
    "K1-19-DOUBLE_FLANK_WELDS": "К.1, схема 19а — два фланговых шва (группа 8)",
    "K1-19-FLANK_AND_END_WELDS": "К.1, схема 19б — фланговые и лобовой швы (группа 7)",
    "K1-19-FORCE_THROUGH_BASE_METAL": "К.1, схема 19в — усилие передаётся через основной металл (группа 7)",
    "K1-19-STEEL_ROPE_ANCHOR_CHEEKS": "К.1, схема 19г — щёки анкера стального каната (группа 8)",
    "K1-20-TM_DM_GE_1_14": "К.1, схема 20а — трубчатый раскос, tm/dm ≥ 1/14 (группа 7)",
    "K1-20-TM_DM_1_20_TO_1_14": "К.1, схема 20б — трубчатый раскос, 1/20 ≤ tm/dm < 1/14 (группа 8)",
    "K1-21-TM_DM_GE_1_14": "К.1, схема 21а — узел трубчатого раскоса, tm/dm ≥ 1/14 (группа 6)",
    "K1-21-TM_DM_1_20_TO_1_14": "К.1, схема 21б — узел трубчатого раскоса, 1/20 ≤ tm/dm < 1/14 (группа 7)",
    "K1-21-TM_DM_1_35_TO_1_20": "К.1, схема 21в — узел трубчатого раскоса, 1/35 ≤ tm/dm < 1/20 (группа 8)",
}


def _localize_enum(quantity: dict[str, Any]) -> None:
    qid = str(quantity.get("id") or "")
    values = quantity.get("enum_values")
    if not isinstance(values, list):
        return
    labels = _ENUM_LABELS.get(qid, {})
    for option in values:
        if not isinstance(option, dict) or "value" not in option:
            continue
        value = option["value"]
        if qid == "sp16_mech9_fatigue_annex_k_case_id":
            option["label"] = _ANNEX_K_LABELS.get(str(value), f"Случай таблицы К.1: {value}")
        elif value in labels:
            option["label"] = labels[value]


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out
    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.90 closes MECH9 authoring UX: Section-13 conditional inputs are truly optional until their "
        "applicability condition is present, the Annex-K selector itself qualifies the selected case, and "
        "all MECH9 enum labels are localized without changing machine values."
    )

    quantities = {str(q.get("id")): q for q in out.get("quantities", []) if isinstance(q, dict)}
    for qid, q in quantities.items():
        if qid.startswith("sp16_mech9_"):
            _localize_enum(q)

    welded = quantities.get("sp16_mech9_brittle_welded_structure")
    if welded is not None:
        welded["name_ru"] = "Имеются ли в рассматриваемом элементе или узле сварные соединения, к которым применяются требования раздела 13 СП 16?"

    nodes = {str(n.get("id")): n for n in out.get("nodes", []) if isinstance(n, dict)}
    cond = nodes.get("SP16_I_MECH9_BRITTLE_CONDITIONAL")
    if cond is not None:
        for binding in cond.get("produces", []):
            if isinstance(binding, dict):
                binding["required"] = False
        cond.setdefault("notes", {})["v090_authoring_policy"] = (
            "Only fields made applicable by welded/detail context are requested by the UI; the qualified N10 runtime remains fail-closed if an applicable value is absent."
        )

    fatigue = nodes.get("SP16_I_MECH9_FATIGUE_ORDINARY")
    if fatigue is not None:
        for binding in fatigue.get("produces", []):
            if isinstance(binding, dict) and binding.get("quantity_id") == "sp16_mech9_fatigue_annex_k_case_confirmed":
                binding["required"] = False
        fatigue.setdefault("notes", {})["v090_annex_k_policy"] = (
            "A value accepted by the typed Annex-K enum selector is itself the explicit case selection; no duplicate user confirmation is requested."
        )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=copy.deepcopy(model.presentation_policy),
    )


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Replace only the MECH9 binder so a validated Annex-K enum selection is its own confirmation."""
    def _executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        effective = dict(values)
        case_id = effective.get("sp16_mech9_fatigue_annex_k_case_id")
        if isinstance(case_id, str) and case_id.strip():
            effective["sp16_mech9_fatigue_annex_k_case_confirmed"] = True
        return bind_mech9_remaining_ambient_evidence(effective)

    registry.register(BINDER_NODE_ID, _executor)
    return registry


__all__ = [
    "GRAPH_SUFFIX",
    "BINDER_NODE_ID",
    "build_model",
    "transform_graph",
    "install_registry_remediation",
]
