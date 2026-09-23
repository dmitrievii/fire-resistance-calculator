from __future__ import annotations

from standard_core.fire_ui0 import ExecutionRegistry
from standard_core.sp16_mech_v092_canonical_actions import (
    canonical_action_contract,
    install_registry_remediation,
)


def _legacy_plan() -> dict:
    return {
        "schema": "sp16_mech1_verification_plan_v1",
        "axis_convention": {
            "member_axis": "s",
            "section_principal_axes": ["x-x", "y-y"],
        },
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
        "branches": [
            {"id": "bending_Mx", "label": "Изгиб Mx относительно главной оси x-x"},
            {"id": "bending_My", "label": "Изгиб My относительно главной оси y-y"},
            {"id": "biaxial_bending", "label": "Двухосный изгиб Mx + My"},
            {"id": "shear_Qx", "label": "Поперечная сила Qx / текущий scalar web-shear route"},
            {"id": "shear_Qy", "label": "Поперечная сила Qy"},
            {
                "id": "torsion_T",
                "label": "Кручение T относительно продольной оси s",
                "status": "deferred",
                "note": "SP16-MECH1 не подменяет T бимоментом B; torsion runtime закрывается отдельным этапом.",
            },
            {"id": "interaction_N_M", "label": "Взаимодействие N + Mx + My"},
            {"id": "interaction_M_Qx", "label": "Взаимодействие M + Qx"},
        ],
        "deferred_branch_ids": ["torsion_T"],
        "compatibility_aliases": {"Q_shear": "Q_x"},
    }


def test_historical_verification_plan_is_fully_canonicalized_for_public_ledger():
    registry = ExecutionRegistry()

    def legacy_executor(values, node):
        return {"verification_plan": _legacy_plan()}

    registry.register("PLAN", legacy_executor)
    install_registry_remediation(registry)
    result = registry.get("PLAN")({}, {"id": "PLAN", "consumes": [], "produces": []})
    plan = result["verification_plan"]

    assert plan["schema"] == "sp16_mech1_verification_plan_v092_canonical_axes"
    assert plan["axis_convention"]["member_axis"] == "x"
    assert plan["axis_convention"]["section_principal_axes"] == ["z-z", "y-y"]
    assert plan["sign_convention"] == {
        "N": "positive=tension, negative=compression",
        "x": "member longitudinal axis",
        "Mz": "bending about SP16 strong principal z-z",
        "My": "bending about SP16 weak principal y-y",
        "Mx": "torsion about longitudinal x",
        "Qz": "SP16 Qz",
        "Qy": "SP16 Qy",
        "B": "bimoment, direct conditional input",
    }
    assert plan["compatibility_aliases"] == {"Q_shear": "Q_z"}
    assert plan["deferred_branch_ids"] == ["torsion_Mx"]

    ids = [row["id"] for row in plan["branches"]]
    assert "bending_Mz" in ids
    assert "bending_Mx" not in ids
    assert "shear_Qz" in ids
    assert "shear_Qx" not in ids
    assert "torsion_Mx" in ids
    assert "torsion_T" not in ids
    assert "interaction_M_Qz" in ids
    assert "interaction_M_Qx" not in ids

    labels = {row["id"]: row["label"] for row in plan["branches"]}
    assert labels["bending_Mz"] == "Изгиб Mz относительно сильной главной оси z-z"
    assert labels["biaxial_bending"] == "Двухосный изгиб Mz + My"
    assert labels["shear_Qz"] == "Поперечная сила Qz"
    assert labels["torsion_Mx"] == "Кручение Mx относительно продольной оси x"
    assert labels["interaction_N_M"] == "Взаимодействие N + Mz + My"
    assert labels["interaction_M_Qz"] == "Взаимодействие M + Qz"
    assert "T " not in next(row for row in plan["branches"] if row["id"] == "torsion_Mx")["note"]


def test_canonical_plan_round_trips_to_historical_contract_for_qualified_consumer():
    registry = ExecutionRegistry()
    captured = {}

    def legacy_producer(values, node):
        return {"verification_plan": _legacy_plan()}

    def legacy_consumer(values, node):
        captured.update(values["verification_plan"])
        return {"consumer_ok": True}

    registry.register("PLAN", legacy_producer)
    registry.register("CONSUMER", legacy_consumer)
    install_registry_remediation(registry)

    canonical = registry.get("PLAN")(
        {},
        {"id": "PLAN", "consumes": [], "produces": [{"quantity_id": "verification_plan"}]},
    )["verification_plan"]
    registry.get("CONSUMER")(
        {"verification_plan": canonical},
        {"id": "CONSUMER", "consumes": [{"quantity_id": "verification_plan"}], "produces": [{"quantity_id": "consumer_ok"}]},
    )

    assert captured["schema"] == "sp16_mech1_verification_plan_v1"
    assert captured["axis_convention"]["member_axis"] == "s"
    assert captured["sign_convention"]["Mx"] == "bending about SP16 principal x-x"
    assert captured["sign_convention"]["T"] == "torsion about longitudinal s"
    assert captured["deferred_branch_ids"] == ["torsion_T"]
    assert captured["compatibility_aliases"] == {"Q_shear": "Q_x"}

    labels = {row["id"]: row["label"] for row in captured["branches"]}
    assert labels["bending_Mx"] == "Изгиб Mx относительно главной оси x-x"
    assert labels["biaxial_bending"] == "Двухосный изгиб Mx + My"
    assert labels["torsion_T"] == "Кручение T относительно продольной оси s"
    assert labels["interaction_N_M"] == "Взаимодействие N + Mx + My"


def test_public_contract_exposes_canonical_verification_plan_ids():
    contract = canonical_action_contract()
    assert contract["verification_plan_branch_ids"] == {
        "strong_axis_bending": "bending_Mz",
        "z_shear": "shear_Qz",
        "torsion": "torsion_Mx",
        "bending_shear_interaction": "interaction_M_Qz",
    }
