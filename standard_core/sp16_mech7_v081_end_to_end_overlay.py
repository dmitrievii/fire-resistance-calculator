"""v0.81 end-to-end handoff from canonical z/y stability to SP554 scalar contract.

The active Stage-N7 contract has been axis-specific since v0.75/v0.76.  The
frozen FIRE DAG still contains an older scalar chain driven by ``i_min`` and a
generic ``l_eff``.  Re-entering that chain after the z/y state is available is
both duplicate authoring and mechanically ambiguous when the effective lengths
of the two principal axes differ.

v0.81 keeps the frozen scalar nodes as historical/normative evidence, removes
all scheduling edges *into* that superseded chain, and adds one calculated
handoff producer.  The handoff carries the already calculated governing SP16
principal-axis state into the legacy scalar quantity names required by the
locked SP554 9.2 consumer.  It never averages axes, invents a resultant, or
reconstructs a scalar effective length.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .fire_ui0 import FireDAGModel
from .sp16_mech7_v080_guided_cleanup_overlay import build_model as build_v080_model

GRAPH_SUFFIX = "_v081_end_to_end_consistency"
HANDOFF_NODE_ID = "SP16_C_V081_GOVERNING_STABILITY_HANDOFF"
GOVERNING_AXIS_QID = "sp16_v081_governing_stability_axis"

# Historical scalar route entered from SP554_C_8_4_COMPRESSION.  These nodes
# remain in ``nodes`` for audit evidence, but no active guided/dependency route
# may schedule them after v0.81.
RETIRED_SCALAR_STABILITY_NODES = {
    "SP16_C_I_MIN",
    "SP16_C_LAMBDA",
    "SP16_C_LBAR",
    "SP16_D_CURVE",
    "SP16_L_TABLE7",
    "SP16_C_DELTA9",
    "SP16_C_PHI8_RAW",
    "SP16_C_PHI_LIMITS",
}


def _governing_axis_quantity() -> dict[str, Any]:
    return {
        "id": GOVERNING_AXIS_QID,
        "symbol": None,
        "name_ru": "Определяющая главная ось устойчивости для передачи СП16 → СП554",
        "data_type": "enum",
        "role": "intermediate",
        "physical_dimension": None,
        "canonical_unit": None,
        "allowed_units": [],
        "source_policy": {
            "primary_source_type": "CALCULATED",
            "allowed_source_types": ["CALCULATED"],
            "override_policy": "forbidden",
        },
        "enum_values": [
            {"value": "z", "label": "z — сильная ось"},
            {"value": "y", "label": "y — слабая ось"},
        ],
    }


def _handoff_node() -> dict[str, Any]:
    return {
        "id": HANDOFF_NODE_ID,
        "node_type": "calculation",
        "owner_standard_id": "SP16_2017",
        "title": "СП16 → СП554: определяющая ось центрального сжатия",
        "normative_refs": [
            {
                "standard_id": "SP16_2017",
                "reference_kind": "clause",
                "section": "7",
                "clause": "7.1.3",
                "formula_ref": "(7)-(9), Table 7",
            },
            {
                "standard_id": "SP554_2026",
                "reference_kind": "clause",
                "section": "9",
                "clause": "9.2",
            },
        ],
        "consumes": [
            {"quantity_id": "lambda_bar_z", "required": True, "binding_role": "input"},
            {"quantity_id": "lambda_bar_y", "required": True, "binding_role": "input"},
            {"quantity_id": "sp16_curve_z", "required": True, "binding_role": "input"},
            {"quantity_id": "sp16_curve_y", "required": True, "binding_role": "input"},
            {"quantity_id": "phi_z_sp16", "required": True, "binding_role": "input"},
            {"quantity_id": "phi_y_sp16", "required": True, "binding_role": "input"},
        ],
        "produces": [
            {"quantity_id": "lambda_bar", "required": True, "binding_role": "output"},
            {"quantity_id": "sp16_buckling_curve_type", "required": True, "binding_role": "output"},
            {"quantity_id": "phi_sp16_formula8", "required": True, "binding_role": "output"},
            {"quantity_id": GOVERNING_AXIS_QID, "required": True, "binding_role": "output"},
        ],
        "applicability": {
            "type": "comparison",
            "quantity_id": "strength_coefficient_method",
            "operator": "eq",
            "value": "section_formulas",
        },
        "notes": {
            "engineering_meaning": (
                "Select the principal axis with the smaller already-qualified SP16 stability "
                "coefficient phi and pass that same axis's lambda-bar/curve/phi tuple to the "
                "locked scalar SP554 consumer."
            ),
            "limitations": (
                "Applies only to the solid central-compression Section-9 scalar handoff. "
                "No scalar effective length, i_min reconstruction, axis averaging or x/z alias is used."
            ),
            "normative_warning": (
                "The governing tuple must come from one and the same principal axis. "
                "Mixing max(lambda-bar) with a curve/phi from the other axis is forbidden."
            ),
        },
        "calculation_spec": {
            "formula_type": "executor",
            "expression_language": "executor_v1",
            "algorithm_id": "sp16_v081_governing_stability_handoff_v1",
            "bindings": [],
            "rounding": {"mode": "none"},
        },
    }


def transform_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(graph))
    if GRAPH_SUFFIX in str(out.get("graph_id") or ""):
        return out

    quantities = {row["id"] for row in out.get("quantities", [])}
    if GOVERNING_AXIS_QID not in quantities:
        out["quantities"].append(_governing_axis_quantity())

    nodes = {row["id"] for row in out.get("nodes", [])}
    if HANDOFF_NODE_ID not in nodes:
        out["nodes"].append(_handoff_node())

    # Unlike v0.80, remove *every* incoming scheduling/dependency edge.  The
    # old chain is therefore unreachable both by navigation and by data-call
    # scheduling.  Outgoing historical edges are deliberately retained as
    # evidence of the frozen source topology.
    out["edges"] = [
        edge
        for edge in out.get("edges", [])
        if edge.get("to_node_id") not in RETIRED_SCALAR_STABILITY_NODES
    ]

    out["graph_id"] = str(out.get("graph_id") or "") + GRAPH_SUFFIX
    out["description"] = str(out.get("description") or "") + (
        " v0.81 retires the complete superseded scalar SP16 central-compression "
        "stability chain and supplies the locked SP554 scalar consumer from the "
        "governing canonical z/y SP16 stability tuple."
    )
    return out


def transform_presentation_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(dict(policy))

    hidden = set(out.get("hidden_normative_nodes") or [])
    hidden.update(RETIRED_SCALAR_STABILITY_NODES)
    out["hidden_normative_nodes"] = sorted(hidden)

    excluded = set(out.get("guided_excluded_nodes") or [])
    excluded.update(RETIRED_SCALAR_STABILITY_NODES)
    out["guided_excluded_nodes"] = sorted(excluded)
    return out


def build_model(model: FireDAGModel) -> FireDAGModel:
    parent = build_v080_model(model)
    if GRAPH_SUFFIX in str(parent.graph.get("graph_id") or ""):
        return parent
    return FireDAGModel(
        transform_graph(parent.graph),
        source_path=parent.source_path,
        presentation_policy=transform_presentation_policy(parent.presentation_policy),
    )


__all__ = [
    "GOVERNING_AXIS_QID",
    "GRAPH_SUFFIX",
    "HANDOFF_NODE_ID",
    "RETIRED_SCALAR_STABILITY_NODES",
    "build_model",
    "transform_graph",
    "transform_presentation_policy",
]
