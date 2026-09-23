"""v0.91 guided-DAG remediation for final SP 554 §§8.6 and 9.2.

The public Python workflow was already remediated in v0.91, but the retained
DAG route still carried the v0.82 gamma-e contract: it consumed ``E_norm`` and
one ambient-SP16 governing axis.  Final-SP554 guided execution must instead use
the normative structural-steel modulus E=206000 N/mm² and evaluate stiffness
on both qualified principal axes independently.

This overlay also publishes typed calculation evidence from the §9.2 strength
and §8.6 stiffness producers.  REPORT-IR can therefore render the exact runtime
substitutions without recalculating engineering values in the presentation
layer.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v083_full_route_overlay import GAMMA_E_NODE_ID


GRAPH_SUFFIX = "_v091_final_sp554_guided_evidence"
PHI_NODE_ID = "SP554_C_PHI_9_2_RULE"
STRENGTH_TRACE_QID = "sp554_9_2_fire_stability_trace"
STIFFNESS_TRACE_QID = "sp554_8_6_fire_stiffness_trace"


def _binding(qid: str, role: str, *, required: bool = True) -> dict[str, Any]:
    return {"quantity_id": qid, "required": required, "binding_role": role}


def _trace_quantity(qid: str, name_ru: str) -> dict[str, Any]:
    return {
        "id": qid,
        "symbol": None,
        "name_ru": name_ru,
        "data_type": "object",
        "canonical_unit": None,
        "allowed_units": [],
        "role": "calculation_evidence",
        "source_policy": {"primary_source_type": "CALCULATED"},
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    quantities = {row["id"]: row for row in out.get("quantities", [])}
    nodes = {row["id"]: row for row in out.get("nodes", [])}
    phi = nodes.get(PHI_NODE_ID)
    gamma = nodes.get(GAMMA_E_NODE_ID)
    if phi is None:
        raise ValueError(f"v0.91 requires {PHI_NODE_ID}")
    if gamma is None:
        raise ValueError(f"v0.91 requires {GAMMA_E_NODE_ID}")

    if STRENGTH_TRACE_QID not in quantities:
        out["quantities"].append(_trace_quantity(
            STRENGTH_TRACE_QID,
            "Расчётный trace продольной устойчивости при пожаре по СП 554 п. 9.2",
        ))
    if STIFFNESS_TRACE_QID not in quantities:
        out["quantities"].append(_trace_quantity(
            STIFFNESS_TRACE_QID,
            "Расчётный trace снижения жёсткости при пожаре по СП 554 п. 8.6",
        ))

    phi_produced = {row.get("quantity_id") for row in phi.get("produces", [])}
    if STRENGTH_TRACE_QID not in phi_produced:
        phi.setdefault("produces", []).append(_binding(STRENGTH_TRACE_QID, "output"))
    phi_spec = dict(phi.get("calculation_spec") or {})
    phi_spec["algorithm_id"] = "sp554_v091_phi_9_2_two_axis_ryn_over_normative_E_v1"
    phi["calculation_spec"] = phi_spec

    # Replace the retained v0.82/v0.83 scalar-axis contract.  Both qualified
    # axes are consumed; E is a normative runtime constant, not a ledger input.
    gamma["node_type"] = "calculation"
    gamma["consumes"] = [
        _binding("N_force", "input"),
        _binding("sp16_l_eff_z", "input"),
        _binding("sp16_l_eff_y", "input"),
        _binding("sp16_i_z", "input"),
        _binding("sp16_i_y", "input"),
        _binding("A_gross", "input"),
    ]
    gamma_produced = [
        row for row in gamma.get("produces", [])
        if row.get("quantity_id") != STIFFNESS_TRACE_QID
    ]
    gamma_produced.append(_binding(STIFFNESS_TRACE_QID, "output"))
    gamma["produces"] = gamma_produced
    gamma_spec = dict(gamma.get("calculation_spec") or {})
    gamma_spec["algorithm_id"] = "sp554_v091_gamma_e_8_6_two_axis_normative_E_v1"
    gamma["calculation_spec"] = gamma_spec
    notes = dict(gamma.get("notes") or {})
    notes.update({
        "engineering_meaning": (
            "SP554 8.6 gamma_E is evaluated independently for both qualified "
            "SP16 principal axes z/y; the larger gamma_E governs."
        ),
        "normative_warning": (
            "E=206000 N/mm² is sourced from SP16 Appendix B, Table B.1. "
            "Legacy E_norm and ambient governing-axis quantities do not govern."
        ),
    })
    gamma["notes"] = notes

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.91 remediates guided SP554 8.6/9.2 to normative E=206000, "
        "independent z/y fire checks, and typed runtime evidence for REPORT-IR."
    )
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    if GRAPH_SUFFIX in str(model.graph.get("graph_id") or ""):
        return model
    return FireDAGModel(
        transform_graph(model.graph),
        source_path=model.source_path,
        presentation_policy=model.presentation_policy,
    )


__all__ = [
    "GRAPH_SUFFIX",
    "PHI_NODE_ID",
    "STIFFNESS_TRACE_QID",
    "STRENGTH_TRACE_QID",
    "build_model",
    "transform_graph",
]
