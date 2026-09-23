from __future__ import annotations

import json
from pathlib import Path

from standard_core.sp16_mech_v092_presentation import (
    PRESENTATION_MARKER,
    transform_presentation_policy,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "fire_bridge2_presentation_policy.json"


def _policy() -> dict:
    with POLICY.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_frozen_policy_proves_pre_v092_axis_vocabulary_is_present():
    source = _policy()
    assert source["sp16_mech1"]["member_longitudinal_axis"] == "s"
    assert source["sp16_mech1"]["section_principal_axes"] == ["x-x", "y-y"]
    assert source["sp16_mech1"]["canonical_actions"] == ["N", "Mx", "My", "Qx", "Qy", "T"]
    assert "Mx" in source["node_presentation"]["SP16_I_C_M_RESTRAINED_9_2_6"]["title"]


def test_active_policy_uses_mz_my_mx_qz_qy_contract_everywhere_it_declares_axes():
    policy = transform_presentation_policy(_policy())

    marker = policy[PRESENTATION_MARKER]
    assert marker["member_axis"] == "x"
    assert marker["section_principal_axes"] == ["z-z", "y-y"]
    assert marker["strong_axis_bending"] == "Mz"
    assert marker["weak_axis_bending"] == "My"
    assert marker["torsion"] == "Mx"
    assert marker["shear"] == ["Qz", "Qy"]

    mech1 = policy["sp16_mech1"]
    assert mech1["member_longitudinal_axis"] == "x"
    assert mech1["section_principal_axes"] == ["z-z", "y-y"]
    assert mech1["canonical_actions"] == ["N", "Mz", "My", "Mx", "Qz", "Qy"]
    assert mech1["legacy_v057_mapping"] == {
        "load_My_local": "M_z",
        "load_Mz_local": "M_y",
        "load_Qz_local": "Q_z",
        "load_Qy_local": "Q_y",
    }
    assert "T_runtime_closed" not in mech1
    assert "Mx_torsion_runtime_closed" in mech1

    assert "T_runtime_closed" not in policy["sp16_mech2"]
    assert "Mx_torsion_runtime_closed" in policy["sp16_mech2"]
    assert "axis_specific_Qx_Qy_supported_geometry_closed" not in policy["sp16_mech3"]
    assert "axis_specific_Qz_Qy_supported_geometry_closed" in policy["sp16_mech3"]

    mech4 = policy["sp16_mech4"]
    assert mech4["Mx_semantics"] == "Saint_Venant_free_torsion_component_about_member_axis_x"
    assert mech4["Mx_distinct_from_B"] is True
    assert "T_semantics" not in mech4
    assert "T_distinct_from_Mx" not in mech4
    assert "SP554_T_handoff_closed" not in mech4
    assert "SP554_Mx_handoff_closed" in mech4

    assert "automatic_b_from_t" not in policy["sp16_mech5"]
    assert "automatic_b_from_mx" in policy["sp16_mech5"]
    assert "torsion_T" not in policy["sp16_mech8"]
    assert "torsion_Mx" in policy["sp16_mech8"]
    assert "torsion_T" not in policy["sp16_mech9"]
    assert "torsion_Mx" in policy["sp16_mech9"]
    assert "T_fire_handoff" not in policy["fire_bridge2"]
    assert "Mx_fire_handoff" in policy["fire_bridge2"]


def test_active_card_titles_and_mech9_summary_do_not_call_bending_moment_mx():
    policy = transform_presentation_policy(_policy())
    nodes = policy["node_presentation"]

    assert nodes["SP16_I_C_M_RESTRAINED_9_2_6"]["title"] == "Характерные Mz по 9.2.6"
    assert nodes["SP16_I_C_M_FIXED_FREE_9_2_6"]["title"] == "Характерные Mz по 9.2.6 — консоль"
    assert "Mz+Qz" in nodes["SP16_I_MECH9_CLASS3_CONTEXT"]["summary"]
    assert "Mx+Qx" not in nodes["SP16_I_MECH9_CLASS3_CONTEXT"]["summary"]


def test_presentation_transform_is_idempotent():
    once = transform_presentation_policy(_policy())
    twice = transform_presentation_policy(once)
    assert twice == once
