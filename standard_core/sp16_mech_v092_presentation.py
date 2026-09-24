"""v0.92 presentation overlay for the canonical SP16 action vocabulary.

The frozen FIRE-BRIDGE2 presentation policy predates the v0.92 axis migration
and therefore still describes strong-axis bending as Mx, shear as Qx and free
torsion as T.  This module leaves that historical JSON untouched on disk and
normalizes only the active in-memory presentation contract to:

    Mz strong-axis bending; My weak-axis bending; Mx torsion; Qz/Qy shear.

The transform is presentation/metadata-only.  Numerical action translation is
owned by :mod:`sp16_mech_v092_canonical_actions`.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel

PRESENTATION_MARKER = "sp16_v092_canonical_action_presentation"


def _rename_key(table: dict[str, Any], old: str, new: str, *, transform=lambda value: value) -> None:
    if old in table:
        table[new] = transform(table.pop(old))


def transform_presentation_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a deep-copied active policy using only the v0.92 action semantics."""
    out = copy.deepcopy(dict(policy or {}))
    if out.get(PRESENTATION_MARKER):
        return out

    nodes = out.get("node_presentation")
    if isinstance(nodes, dict):
        if isinstance(nodes.get("SP16_I_C_M_RESTRAINED_9_2_6"), dict):
            nodes["SP16_I_C_M_RESTRAINED_9_2_6"]["title"] = "Характерные Mz по 9.2.6"
        if isinstance(nodes.get("SP16_I_C_M_FIXED_FREE_9_2_6"), dict):
            nodes["SP16_I_C_M_FIXED_FREE_9_2_6"]["title"] = "Характерные Mz по 9.2.6 — консоль"
        if isinstance(nodes.get("SP16_I_MECH9_CLASS3_CONTEXT"), dict):
            nodes["SP16_I_MECH9_CLASS3_CONTEXT"]["summary"] = (
                "Explicit class-3 8.2.7 confirmations for the bounded Mz+Qz route."
            )

    deferred = out.get("deferred_engineering_features")
    if isinstance(deferred, dict):
        _rename_key(
            deferred,
            "torsion_T_runtime",
            "torsion_Mx_runtime",
            transform=lambda value: str(value).replace("T_", "MX_").replace("T_AND", "MX_AND"),
        )

    mech1 = out.get("sp16_mech1")
    if isinstance(mech1, dict):
        mech1["member_longitudinal_axis"] = "x"
        mech1["section_principal_axes"] = ["z-z", "y-y"]
        mech1["canonical_actions"] = ["N", "Mz", "My", "Mx", "Qz", "Qy"]
        mech1["conditional_direct_action"] = ["B"]
        mech1["legacy_v057_mapping"] = {
            "load_My_local": "M_z",
            "load_Mz_local": "M_y",
            "load_Qz_local": "Q_z",
            "load_Qy_local": "Q_y",
        }
        _rename_key(mech1, "T_runtime_closed", "Mx_torsion_runtime_closed")

    mech2 = out.get("sp16_mech2")
    if isinstance(mech2, dict):
        _rename_key(mech2, "T_runtime_closed", "Mx_torsion_runtime_closed")
        _rename_key(
            mech2,
            "Qy_T_visible_but_fail_closed",
            "Qy_Mx_torsion_visible_but_fail_closed",
        )

    mech3 = out.get("sp16_mech3")
    if isinstance(mech3, dict):
        _rename_key(
            mech3,
            "axis_specific_Qx_Qy_supported_geometry_closed",
            "axis_specific_Qz_Qy_supported_geometry_closed",
        )

    mech4 = out.get("sp16_mech4")
    if isinstance(mech4, dict):
        mech4["Mx_semantics"] = "Saint_Venant_free_torsion_component_about_member_axis_x"
        mech4["Mx_distinct_from_B"] = True
        mech4["B_policy"] = "conditional direct signed input; not derived from Mx"
        mech4.pop("T_semantics", None)
        mech4.pop("T_distinct_from_Mx", None)
        mech4.pop("T_distinct_from_B", None)
        _rename_key(mech4, "SP554_T_handoff_closed", "SP554_Mx_handoff_closed")

    mech5 = out.get("sp16_mech5")
    if isinstance(mech5, dict):
        _rename_key(mech5, "automatic_b_from_t", "automatic_b_from_mx")
        _rename_key(
            mech5,
            "sp554_qy_t_complex_state_handoff_closed",
            "sp554_qy_mx_complex_state_handoff_closed",
        )

    for key in ("sp16_mech8", "sp16_mech9"):
        section = out.get(key)
        if isinstance(section, dict):
            _rename_key(section, "torsion_T", "torsion_Mx")

    bridge = out.get("fire_bridge2")
    if isinstance(bridge, dict):
        _rename_key(bridge, "T_fire_handoff", "Mx_fire_handoff")

    out[PRESENTATION_MARKER] = {
        "member_axis": "x",
        "section_principal_axes": ["z-z", "y-y"],
        "strong_axis_bending": "Mz",
        "weak_axis_bending": "My",
        "torsion": "Mx",
        "shear": ["Qz", "Qy"],
        "bimoment": "B",
        "legacy_Mx_bending_or_T_torsion_labels_exposed": False,
    }
    return out


def build_presentation_model(model: FireDAGModel) -> FireDAGModel:
    """Rebuild one model with canonical v0.92 presentation metadata."""
    policy = transform_presentation_policy(model.presentation_policy)
    if policy == model.presentation_policy:
        return model
    return FireDAGModel(
        model.graph,
        source_path=model.source_path,
        presentation_policy=policy,
    )


__all__ = ["PRESENTATION_MARKER", "build_presentation_model", "transform_presentation_policy"]
