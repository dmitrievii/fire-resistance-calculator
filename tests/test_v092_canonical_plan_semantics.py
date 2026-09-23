from __future__ import annotations

from standard_core.fire_ui0 import ExecutionRegistry
from standard_core.sp16_mech_v092_canonical_actions import (
    canonical_action_contract,
    install_registry_remediation,
)


def test_historical_verification_plan_ids_and_aliases_are_canonicalized():
    registry = ExecutionRegistry()

    def legacy_executor(values, node):
        return {
            "verification_plan": {
                "schema": "sp16_mech1_verification_plan_v1",
                "axis_convention": {
                    "member_axis": "s",
                    "section_principal_axes": ["x-x", "y-y"],
                },
                "branches": [
                    {"id": "bending_Mx", "label": "Изгиб Mx относительно главной оси x-x"},
                    {"id": "bending_My", "label": "Изгиб My относительно главной оси y-y"},
                    {"id": "shear_Qx", "label": "Поперечная сила Qx"},
                    {"id": "shear_Qy", "label": "Поперечная сила Qy"},
                    {"id": "torsion_T", "label": "Кручение T относительно продольной оси s"},
                    {"id": "interaction_M_Qx", "label": "Взаимодействие M + Qx"},
                ],
                "compatibility_aliases": {"Q_shear": "Q_x"},
            }
        }

    registry.register("PLAN", legacy_executor)
    install_registry_remediation(registry)
    result = registry.get("PLAN")({}, {"id": "PLAN", "consumes": [], "produces": []})
    plan = result["verification_plan"]

    assert plan["axis_convention"]["member_axis"] == "x"
    assert plan["axis_convention"]["section_principal_axes"] == ["z-z", "y-y"]
    assert plan["compatibility_aliases"] == {"Q_shear": "Q_z"}

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
    assert "Mz" in labels["bending_Mz"]
    assert "Qz" in labels["shear_Qz"]
    assert "Mx" in labels["torsion_Mx"]


def test_public_contract_exposes_canonical_verification_plan_ids():
    contract = canonical_action_contract()
    assert contract["verification_plan_branch_ids"] == {
        "strong_axis_bending": "bending_Mz",
        "z_shear": "shear_Qz",
        "torsion": "torsion_Mx",
        "bending_shear_interaction": "interaction_M_Qz",
    }
