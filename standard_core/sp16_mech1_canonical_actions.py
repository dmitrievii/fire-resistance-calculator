"""SP16-MECH1 canonical action axes and mechanical-state contract.

This stage changes the *action semantics* of the guided calculation without
claiming new Qy or torsion-T resistance mechanics.  The canonical transverse
section axes are the SP16 principal axes x-x and y-y; the member longitudinal
axis is named ``s`` to avoid overloading ``x``.  Bimoment B is conditionally
entered directly when the user states that it is required.
"""
from __future__ import annotations

from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry
from .fire_ui24_val1_remediation import build_fire_ui24_registry
from .profile_catalog import InterimProfileCatalog


LEGACY_AXIS_MAPPING = {
    "load_My_local": "M_x",
    "load_Mz_local": "M_y",
    "load_Qz_local": "Q_x",
    "load_Qy_local": "Q_y",
    "T_torsion": "T_torsion",
    "N_force": "N_force",
}


def migrate_v057_actions_to_sp16_mech1(payload: Mapping[str, Any]) -> dict[str, float]:
    """
    Summary:
        Convert a v0.57 local-X/Y/Z action payload to the SP16-MECH1 canonical action vocabulary.

    Standard reference:
        SP 16.13330.2017 Appendix A notation for Mx/My and clause 8.2.3 notation for Qx/Qy; Audit ID: SP16-MECH1-AXIS-001.

    Parameters:
        payload: Mapping containing any v0.57 action keys N_force, load_My_local, load_Mz_local, load_Qy_local, load_Qz_local and T_torsion.

    Returns:
        Dictionary containing the corresponding canonical keys N_force, M_x, M_y, Q_x, Q_y and T_torsion that were present in the input.

    Assumptions:
        The v0.57 local-axis convention is the frozen parent convention recorded by FIRE-UI1.6.

    Sign convention:
        Algebraic signs are preserved exactly; no absolute-value operation or axis reversal is performed.

    Unit convention:
        Values are passed through numerically in their existing canonical package units.

    Applicability:
        Migration/import of v0.57 action payloads into v0.58 SP16-MECH1.

    Limitations:
        This is a semantic axis adapter only; it does not rotate arbitrary external FEA coordinate systems.

    Raises:
        TypeError: If a present action value is non-numeric or boolean.

    Examples:
        ``migrate_v057_actions_to_sp16_mech1({"load_My_local": 1.0}) == {"M_x": 1.0}``.

    Tests:
        ``tests/test_sp16_mech1_canonical_axes.py::test_v057_axis_transform_is_sign_preserving``.

    Implementation notes:
        The mapping is explicit and intentionally does not reinterpret torsion T as Mx or bimoment B.
    """
    out: dict[str, float] = {}
    for old, new in LEGACY_AXIS_MAPPING.items():
        if old in payload:
            value = payload[old]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{old} must be numeric")
            out[new] = float(value)
    return out


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def _zero_bimoment(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"B_bimoment": 0.0}


def _canonical_load_plan(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    N = _number(values["N_force"], "N_force")
    Mx = _number(values["M_x"], "M_x")
    My = _number(values["M_y"], "M_y")
    Qx = _number(values["Q_x"], "Q_x")
    Qy = _number(values["Q_y"], "Q_y")
    T = _number(values["T_torsion"], "T_torsion")
    B = _number(values["B_bimoment"], "B_bimoment")

    bend = Mx != 0.0 or My != 0.0
    if N > 0 and not bend:
        stress = "central_tension"
    elif N < 0 and not bend:
        stress = "central_compression"
    elif N < 0 and bend:
        stress = "compression_plus_bending"
    elif N > 0 and bend:
        stress = "tension_plus_bending"
    else:
        stress = "bending"

    branches: list[dict[str, Any]] = []

    def add(branch_id: str, label: str, status: str = "supported", note: str | None = None) -> None:
        row: dict[str, Any] = {"id": branch_id, "label": label, "status": status}
        if note:
            row["note"] = note
        branches.append(row)

    if N > 0:
        add("axial_tension", "Центральное/внецентренное растяжение")
    if N < 0:
        add("axial_compression", "Сжатие и устойчивость")
    if Mx != 0:
        add("bending_Mx", "Изгиб Mx относительно главной оси x-x")
    if My != 0:
        add("bending_My", "Изгиб My относительно главной оси y-y")
    if Mx != 0 and My != 0:
        add("biaxial_bending", "Двухосный изгиб Mx + My")
    if Qx != 0:
        add("shear_Qx", "Поперечная сила Qx / текущий scalar web-shear route")
    if Qy != 0:
        add(
            "shear_Qy",
            "Поперечная сила Qy",
            "deferred",
            "SP16-MECH1 фиксирует canonical Qy, но axis-specific Qy runtime закрывается на SP16-MECH3.",
        )
    if T != 0:
        add(
            "torsion_T",
            "Кручение T относительно продольной оси s",
            "deferred",
            "SP16-MECH1 не подменяет T бимоментом B; torsion runtime закрывается отдельным этапом.",
        )
    if B != 0:
        add("bimoment_B", "Бимомент B — прямой ввод пользователя")
    if N != 0 and bend:
        add("interaction_N_M", "Взаимодействие N + Mx + My")
    if bend and Qx != 0:
        add("interaction_M_Qx", "Взаимодействие M + Qx")
    if not branches:
        add("zero_loads", "Нулевые усилия", "deferred", "Расчётный случай не содержит силовых воздействий.")

    deferred = [b["id"] for b in branches if b["status"] == "deferred"]
    state = {
        "schema": "sp16_mech1_canonical_mechanical_action_state_v1",
        "axis_convention": {
            "member_axis": "s",
            "section_principal_axes": ["x-x", "y-y"],
            "Mx": "bending moment about x-x",
            "My": "bending moment about y-y",
            "Qx": "SP16 Qx; paired with current web-shear route",
            "Qy": "SP16 Qy",
            "T": "torsional moment about member axis s",
            "B": "bimoment; conditionally direct user input in SP16-MECH1",
        },
        "actions": {"N": N, "Mx": Mx, "My": My, "Qx": Qx, "Qy": Qy, "T": T, "B": B},
        "legacy_v057_mapping": dict(LEGACY_AXIS_MAPPING),
    }
    plan = {
        "schema": "sp16_mech1_verification_plan_v1",
        "sign_convention": {
            "N": "positive=tension, negative=compression",
            "s": "member longitudinal axis",
            "Mx": "bending about SP16 principal x-x",
            "My": "bending about SP16 principal y-y",
            "Qx": "SP16 Qx",
            "Qy": "SP16 Qy",
            "T": "torsion about longitudinal s",
            "B": "bimoment, direct conditional input",
        },
        "stress_state": stress,
        "branches": branches,
        "deferred_branch_ids": deferred,
        "all_branches_supported": not deferred,
        "compatibility_aliases": {"Q_shear": "Q_x"},
    }
    # Q_shear is retained only as an explicit compatibility alias for the
    # already-qualified scalar SP16/SP554 web-shear mechanics.  It is not a new
    # resultant and must never include Qy.
    return {
        "stress_state": stress,
        "Q_shear": Qx,
        "mechanical_action_state": state,
        "verification_plan": plan,
    }


def build_sp16_mech1_registry(
    catalog: InterimProfileCatalog,
    registry: ExecutionRegistry | None = None,
) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.58 SP16-MECH1 execution registry over the frozen v0.57 registry.

    Standard reference:
        SP 16.13330.2017 canonical Mx/My/Qx/Qy action semantics and SP554 use of B as a distinct bimoment; Audit ID: SP16-MECH1-REG-001.

    Parameters:
        catalog: Frozen interim section-profile catalog used by inherited guided executors.
        registry: Optional registry to extend in place.

    Returns:
        ExecutionRegistry with inherited v0.57 executors plus explicit B=0 and canonical action-state executors.

    Assumptions:
        The parent v0.57 registry and profile catalog passed their release qualification gates.

    Sign convention:
        Signed N, Mx, My, Qx, Qy, T and B values are preserved; N>0 denotes tension.

    Unit convention:
        Uses the canonical units declared by the active v0.58 DAG quantities.

    Applicability:
        SP16-MECH1 guided calculations using DAG v0.3.61.

    Limitations:
        Qy and torsion T remain fail-closed; restrained-torsion derivation of B is not implemented.

    Raises:
        Propagates registry/catalog validation errors from the inherited runtime.

    Examples:
        ``registry = build_sp16_mech1_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_sp16_mech1_canonical_axes.py`` and cumulative FIRE-UI regression suites.

    Implementation notes:
        The existing SP554_D_STRESS_STATE binding is deliberately overridden by the canonical action-state producer.
    """
    reg = build_fire_ui24_registry(catalog, registry)
    reg.register("SP16_C_BIMOMENT_ZERO", _zero_bimoment)
    # Override the old FIRE-UI1.6 load adapter with canonical SP16 action semantics.
    reg.register("SP554_D_STRESS_STATE", _canonical_load_plan)
    return reg
