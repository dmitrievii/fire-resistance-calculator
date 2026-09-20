"""SP16-MECH2 load-case separation and ambient applicability census.

This stage introduces an explicit AMBIENT_LOAD_CASE and FIRE_LOAD_CASE while
retaining the qualified v0.58 downstream SP554 scalar contract.  The ambient
case is used to derive a machine-readable SP16 applicability census.  The fire
case may either inherit the ambient actions explicitly or be entered as a
separate special-combination action state.

SP16-MECH2 deliberately does not claim the full ambient mechanical gate.  Qy
and torsion T remain fail-closed when non-zero; their mechanics are scheduled
for later SP16-MECH stages.
"""
from __future__ import annotations

from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry
from .profile_catalog import InterimProfileCatalog
from .sp16_mech1_canonical_actions import build_sp16_mech1_registry


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def _ambient_zero_bimoment(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"ambient_B_bimoment": 0.0}


def _make_load_case(*, kind: str, source: str, N: float, Mx: float, My: float, Qx: float, Qy: float, T: float, B: float, combination: Any) -> dict[str, Any]:
    return {
        "schema": "sp16_mech2_load_case_v1",
        "kind": kind,
        "source": source,
        "axis_convention": {
            "member_axis": "s",
            "section_principal_axes": ["x-x", "y-y"],
            "N": "positive=tension; negative=compression",
            "T": "torsional moment about member axis s",
            "B": "bimoment; direct conditional input in current scope",
        },
        "combination": combination,
        "actions": {"N": N, "Mx": Mx, "My": My, "Qx": Qx, "Qy": Qy, "T": T, "B": B},
    }


def _ambient_applicability_census(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    N = _number(values["ambient_N_force"], "ambient_N_force")
    Mx = _number(values["ambient_M_x"], "ambient_M_x")
    My = _number(values["ambient_M_y"], "ambient_M_y")
    Qx = _number(values["ambient_Q_x"], "ambient_Q_x")
    Qy = _number(values["ambient_Q_y"], "ambient_Q_y")
    T = _number(values["ambient_T_torsion"], "ambient_T_torsion")
    B = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
    combination = values.get("ambient_load_combination")

    load_case = _make_load_case(
        kind="ambient",
        source="user_input",
        N=N, Mx=Mx, My=My, Qx=Qx, Qy=Qy, T=T, B=B,
        combination=combination,
    )

    active: list[dict[str, Any]] = []
    contextual: list[dict[str, Any]] = []

    def add_active(check_id: str, family: str, label: str, *, runtime: str = "inherited_runtime", reason: str, clauses: list[str] | None = None) -> None:
        active.append({
            "id": check_id,
            "family": family,
            "label": label,
            "applicability": "applicable",
            "reason": reason,
            "runtime_status": runtime,
            "normative_scope": clauses or [],
        })

    def add_context(check_id: str, family: str, label: str, *, trigger: str, runtime: str = "context_resolution_required", clauses: list[str] | None = None) -> None:
        contextual.append({
            "id": check_id,
            "family": family,
            "label": label,
            "applicability": "conditional_context",
            "trigger": trigger,
            "runtime_status": runtime,
            "normative_scope": clauses or [],
        })

    bending = (Mx != 0.0 or My != 0.0)
    shear = (Qx != 0.0 or Qy != 0.0)

    if N > 0:
        add_active("section_tension", "section_strength", "Растяжение / прочность сечения", reason="N > 0", clauses=["SP16 §7"])
    if N < 0:
        add_active("section_compression", "section_strength", "Сжатие / прочность сечения", reason="N < 0", clauses=["SP16 §7"])
        add_active("member_compression_stability", "member_stability", "Общая устойчивость сжатого элемента", reason="N < 0", clauses=["SP16 §7", "SP16 §10"])
        add_active("effective_length_slenderness", "member_stability", "Расчётные длины и предельная гибкость", reason="N < 0", clauses=["SP16 §10"])
    if Mx != 0.0:
        add_active("bending_x", "section_strength", "Изгиб относительно x-x", reason="Mx ≠ 0", clauses=["SP16 §8"])
    if My != 0.0:
        add_active("bending_y", "section_strength", "Изгиб относительно y-y", reason="My ≠ 0", clauses=["SP16 §8"])
    if Mx != 0.0 and My != 0.0:
        add_active("biaxial_bending", "section_strength", "Двухосный изгиб Mx + My", reason="Mx ≠ 0 и My ≠ 0", clauses=["SP16 §8", "SP16 §9"])
    if Qx != 0.0:
        add_active("shear_x", "shear", "Поперечная сила Qx", reason="Qx ≠ 0", clauses=["SP16 8.2"])
    if Qy != 0.0:
        qy_closed = bool(values["ambient_qy_runtime_closed"]) if "ambient_qy_runtime_closed" in values else False
        add_active(
            "shear_y", "shear", "Поперечная сила Qy",
            runtime="sp16_mech3_axis_shear_closed" if qy_closed else "deferred_sp16_mech3",
            reason=(
                "Qy ≠ 0; axis-specific Qy recovery materialized by SP16-MECH3"
                if qy_closed else
                "Qy ≠ 0; требуется axis-specific shear recovery"
            ),
            clauses=["SP16 8.2.3"],
        )
    if N != 0.0 and bending:
        add_active("interaction_N_M", "interaction", "Совместное действие N + Mx + My", reason="N ≠ 0 и имеется изгиб", clauses=["SP16 §9"])
    if bending and shear:
        add_active("interaction_M_Q", "interaction", "Совместное действие изгиба и поперечной силы", reason="M ≠ 0 и Q ≠ 0", clauses=["SP16 §8"])
    if T != 0.0:
        torsion_closed = bool(values["ambient_torsion_runtime_closed"]) if "ambient_torsion_runtime_closed" in values else False
        add_active(
            "torsion_T", "torsion", "Кручение T",
            runtime="sp16_mech4_free_torsion_mechanics_closed" if torsion_closed else "deferred_sp16_mech4",
            reason=(
                "T ≠ 0; свободное кручение T→I_t→τ_T материализовано SP16-MECH4"
                if torsion_closed else
                "T ≠ 0; требуется поддерживаемая free-torsion geometry/mechanics ветвь"
            ),
            clauses=["SP16 Annex A", "SP16 Annex D", "SP16 torsion / section mechanics"],
        )
    if B != 0.0:
        bimoment_closed = bool(values["ambient_bimoment_runtime_closed"]) if "ambient_bimoment_runtime_closed" in values else False
        add_active(
            "bimoment_B", "torsion_warping", "Бимомент B в комбинированном напряжённом состоянии",
            runtime="sp16_mech5_direct_bimoment_pointwise_closed" if bimoment_closed else "deferred_sp16_mech5",
            reason=(
                "B ≠ 0; прямой signed B и B·ω/Iω pointwise recovery материализованы SP16-MECH5"
                if bimoment_closed else
                "B ≠ 0; значение введено напрямую, но sectorial geometry/warping recovery для данного сечения не закрыты"
            ),
            clauses=["SP16 8.2.1 Eq.(43)", "SP16 9.1.1 Eq.(106)"],
        )

    # These families are not inferable from action components alone.  They are
    # retained in the census as explicit context-driven checks rather than
    # silently omitted.
    if bending:
        add_context(
            "beam_ltb", "member_stability", "Общая устойчивость изгибаемого элемента",
            trigger="тип элемента, форма сечения, раскрепления и место приложения нагрузки",
            clauses=["SP16 §8", "SP16 Annex Ж"],
        )
    if N < 0 or bending:
        add_context(
            "local_stability_web", "local_stability", "Местная устойчивость стенки",
            trigger="геометрия пластинчатых элементов и распределение сжатия/касательных напряжений",
            clauses=["SP16 local-stability provisions"],
        )
        add_context(
            "local_stability_flange", "local_stability", "Местная устойчивость пояса",
            trigger="геометрия пояса и уровень сжатия",
            clauses=["SP16 local-stability provisions"],
        )
    add_context(
        "fatigue", "special_limit_state", "Усталость",
        trigger="наличие циклических воздействий и условий применимости раздела 12",
        clauses=["SP16 §12"],
    )
    add_context(
        "brittle_fracture", "special_limit_state", "Хрупкое разрушение",
        trigger="температура эксплуатации, группа конструкции, толщина и требования раздела 13",
        clauses=["SP16 §13"],
    )

    deferred_active = [row["id"] for row in active if str(row["runtime_status"]).startswith("deferred_")]
    partial_active = [row["id"] for row in active if row["runtime_status"] == "direct_input_partial_runtime"]

    census = {
        "schema": "sp16_mech2_applicability_census_v1",
        "load_case_kind": "ambient",
        "actions": load_case["actions"],
        "active_checks": active,
        "context_driven_checks": contextual,
        "active_check_ids": [row["id"] for row in active],
        "deferred_active_check_ids": deferred_active,
        "partial_active_check_ids": partial_active,
        "has_deferred_active_checks": bool(deferred_active),
        "full_ambient_gate_closed": False,
        "statement": "Census only: all action-driven checks are enumerated and context-driven checks remain explicit. The strict aggregate SP16 ambient PASS gate is executed downstream by SP16-MECH6.",
    }
    return {
        "ambient_load_case": load_case,
        "ambient_mechanical_action_state": {
            "schema": "sp16_mech2_ambient_mechanical_action_state_v1",
            "actions": load_case["actions"],
            "axis_convention": load_case["axis_convention"],
        },
        "sp16_applicability_census": census,
        "sp16_census_has_deferred_active": bool(deferred_active),
    }


def _inherit_fire_from_ambient(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    N = _number(values["ambient_N_force"], "ambient_N_force")
    Mx = _number(values["ambient_M_x"], "ambient_M_x")
    My = _number(values["ambient_M_y"], "ambient_M_y")
    Qx = _number(values["ambient_Q_x"], "ambient_Q_x")
    Qy = _number(values["ambient_Q_y"], "ambient_Q_y")
    T = _number(values["ambient_T_torsion"], "ambient_T_torsion")
    B = _number(values["ambient_B_bimoment"], "ambient_B_bimoment")
    ambient_combination = values.get("ambient_load_combination")
    special = {
        "schema": "sp16_mech2_fire_combination_inherited_v1",
        "source": "ambient_load_case",
        "ambient_combination": ambient_combination,
        "explicit_user_choice": "same_as_ambient",
    }
    fire_case = _make_load_case(
        kind="fire", source="inherited_from_ambient",
        N=N, Mx=Mx, My=My, Qx=Qx, Qy=Qy, T=T, B=B,
        combination=special,
    )
    return {
        "special_load_combination": special,
        "N_force": N,
        "M_x": Mx,
        "M_y": My,
        "Q_x": Qx,
        "Q_y": Qy,
        "T_torsion": T,
        "B_bimoment": B,
        "fire_load_case": fire_case,
    }


def _finalize_separate_fire_case(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    N = _number(values["N_force"], "N_force")
    Mx = _number(values["M_x"], "M_x")
    My = _number(values["M_y"], "M_y")
    Qx = _number(values["Q_x"], "Q_x")
    Qy = _number(values["Q_y"], "Q_y")
    T = _number(values["T_torsion"], "T_torsion")
    B = _number(values["B_bimoment"], "B_bimoment")
    combination = values.get("special_load_combination")
    return {
        "fire_load_case": _make_load_case(
            kind="fire", source="separate_user_input",
            N=N, Mx=Mx, My=My, Qx=Qx, Qy=Qy, T=T, B=B,
            combination=combination,
        )
    }


def build_sp16_mech2_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.59 SP16-MECH2 execution registry over the qualified v0.58 registry.

    Standard reference:
        SP 16.13330.2017 mechanical verification layer and SP 554.1311500.2026 fire-action handoff; Audit ID: SP16-MECH2-REG-001.

    Parameters:
        catalog: Frozen interim section-profile catalog used by inherited guided executors.
        registry: Optional registry to extend in place.

    Returns:
        ExecutionRegistry with inherited v0.58 bindings plus ambient census and ambient/fire load-case producers.

    Assumptions:
        The v0.58 canonical-axis contract and inherited SP16/SP554 executors passed their release gates.

    Sign convention:
        Signed N, Mx, My, Qx, Qy, T and B are preserved; N>0 denotes tension.

    Unit convention:
        Uses canonical units declared by the active v0.59 DAG quantities.

    Applicability:
        SP16-MECH2 guided calculations with separate AMBIENT_LOAD_CASE and FIRE_LOAD_CASE states.

    Limitations:
        The applicability census is not the final SP16 mechanical PASS gate; Qy and T remain fail-closed.

    Raises:
        Propagates registry/catalog validation errors from inherited runtime construction.

    Examples:
        ``registry = build_sp16_mech2_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_sp16_mech2_load_cases_census.py`` and cumulative FIRE-UI regression suites.

    Implementation notes:
        Existing downstream scalar N/M/Q/T quantities remain scoped to FIRE_LOAD_CASE until later retyping stages.
    """
    reg = build_sp16_mech1_registry(catalog, registry)
    reg.register("SP16_C_AMBIENT_BIMOMENT_ZERO", _ambient_zero_bimoment)
    reg.register("SP16_C_AMBIENT_APPLICABILITY_CENSUS", _ambient_applicability_census)
    reg.register("SP16_C_FIRE_LOADS_INHERIT_AMBIENT", _inherit_fire_from_ambient)
    reg.register("SP16_C_FIRE_LOAD_CASE_FINALIZE", _finalize_separate_fire_case)
    return reg
