"""Internal FIRE-D1 bridge audit between the locked SP554 fire DAG and current SP16 producers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import release_metadata as rm

_DAG_RELATIVE_PATH = Path("normative_graph/dag_v0.3.40_fire_d1.json")

# These are implementation-contract groups, not new normative formulae.  The node
# identifiers already exist in the cumulative SP554+SP16 DAG and are checked here
# so the fire runtime cannot silently fall back to an older/incomplete SP16 route.
_INTERFACE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "interface_id": "FIRE-D1-01-MATERIAL",
        "sp554_refs": ["8.2", "8.3", "8.4", "8.5", "9.1", "9.2", "10.1", "10.2", "11.1-11.8"],
        "sp16_stage": "N1",
        "purpose": "Normative yield strength and elastic modulus on the fire-design basis.",
        "required_node_sets": [
            ["SP16_L_RYN_V3", "SP16_L_RYN_V4", "SP16_L_RYN_V5"],
            ["SP16_L_E"],
        ],
        "policy": "SP554 fire mechanics consumes fy_norm/E; no design-Ry substitution is permitted by the bridge.",
    },
    {
        "interface_id": "FIRE-D1-02-SECTION",
        "sp554_refs": ["8.3", "9.1", "9.2", "10.1", "10.2", "11.1-11.8"],
        "sp16_stage": "N2",
        "purpose": "Gross/net section geometry and section properties required by the fire strength equations.",
        "required_node_sets": [
            ["SP16_C_NET_BASIC_IDENTITY"],
            ["SP16_C_NET_ADVANCED_IDENTITY"],
            ["SP16_C_I_MIN"],
        ],
        "policy": "Exact weakening/net geometry remains explicit; no hidden gross-as-net substitution in the bridge.",
    },
    {
        "interface_id": "FIRE-D1-03-AXIAL",
        "sp554_refs": ["9.1", "9.2", "11.5", "11.6", "11.8"],
        "sp16_stage": "N3",
        "purpose": "Central-compression stability coefficients and current section-type limits.",
        "required_node_sets": [
            ["SP16_C_PHI_FINAL_X"],
            ["SP16_C_PHI_FINAL_Y"],
            ["SP16_C_PHI_LIMITS"],
        ],
        "policy": "The SP16 central-compression route is reused as a coefficient producer, not as a normal-temperature utilization result.",
    },
    {
        "interface_id": "FIRE-D1-04-BENDING",
        "sp554_refs": ["10.1", "10.2"],
        "sp16_stage": "N4",
        "purpose": "Bending class, Annex Ж lateral-torsional stability and local-stress producers.",
        "required_node_sets": [
            ["SP16_C_CLASS_COPY"],
            ["SP16_C_LTB_PHI_B_DOUBLE_I", "SP16_C_LTB_PHI_B_CHANNEL_J7", "SP16_C_LTB_PHI_B_MONO_J3"],
            ["SP16_C_SIGMA_Y_FIELD"],
        ],
        "policy": "Applicable Annex Ж branch must be selected explicitly; alternative phi_b producers are branch alternatives, not values to combine.",
    },
    {
        "interface_id": "FIRE-D1-05-BEAM-COLUMN",
        "sp554_refs": ["11.2", "11.3", "11.5", "11.7"],
        "sp16_stage": "N5",
        "purpose": "phi_e, eta/m_eff and out-of-plane coefficient c for N+M fire checks.",
        "required_node_sets": [
            ["SP16_L_D3_PHI_E"],
            ["SP16_C_MEF_COPY"],
            ["SP16_C_C_FINAL_NO_CMAX", "SP16_C_C_FINAL_WITH_CMAX", "SP16_C_C_D4_ASSIGN"],
        ],
        "policy": "Annex Д.3 uses explicit in-domain bilinear digital-table interpolation with exact-node preservation, no extrapolation, and the normative phi_e<=phi cap.",
    },
    {
        "interface_id": "FIRE-D1-06-BIAXIAL-BOX",
        "sp554_refs": ["11.7", "11.8"],
        "sp16_stage": "N5/N6",
        "purpose": "Biaxial and box-section stability coefficient producers retained by the detailed SP16 Section 9 layer.",
        "required_node_sets": [
            ["SP16_L_D3_PHI_EX"],
            ["SP16_L_D3_PHI_EY"],
            ["SP16_C_LBX"],
            ["SP16_C_LBY"],
        ],
        "policy": "Box/biaxial routes remain selected detailed actions; unsupported geometry or out-of-domain coefficient requests fail closed; in-domain Annex Д.3 interpolation is explicit and deterministic.",
    },
    {
        "interface_id": "FIRE-D1-07-EFFECTIVE-LENGTH",
        "sp554_refs": ["8.2", "8.6", "11.4"],
        "sp16_stage": "N7",
        "purpose": "Effective-length factor mu and effective length needed by compression/fire-stability checks.",
        "required_node_sets": [
            ["SP16_L_MU", "SP16_C_MU_GOVERNING_EQUIV"],
        ],
        "policy": "Current Section 10 selected-route/fail-closed policy governs mu; no legacy guessed effective-length factor is accepted.",
    },
)

_REQUIRED_STAGE_FLAGS: tuple[str, ...] = (
    "N1_MATERIAL_STRENGTH_CLOSED",
    "N2_SECTION_MODEL_CLOSED",
    "N2_PROFILE_CATALOG_RUNTIME_CLOSED",
    "N3_AXIAL_MEMBERS_CLOSED",
    "N4_BENDING_MEMBERS_CLOSED",
    "N5_BEAM_COLUMNS_CLOSED",
    "N6_BUILT_UP_BEAM_COLUMNS_LOCAL_STABILITY_CLOSED",
    "N7_EFFECTIVE_LENGTHS_LIMITING_SLENDERNESS_CLOSED",
)


def _node_sections(node: dict[str, Any]) -> set[str]:
    refs = node["normative_refs"] if "normative_refs" in node else []
    return {str(ref["section"] if "section" in ref else "") for ref in refs}


def _bridge_workflow(package_root: str | Path, require_connection_scope: bool) -> dict[str, Any]:
    """Run the internal FIRE-D1 dependency closure audit."""
    root = Path(package_root)
    graph = json.loads((root / _DAG_RELATIVE_PATH).read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]}

    stage_flags = {name: bool(getattr(rm, name)) for name in _REQUIRED_STAGE_FLAGS}
    stage_gate_pass = all(stage_flags.values())

    group_results: list[dict[str, Any]] = []
    for group in _INTERFACE_GROUPS:
        set_results: list[dict[str, Any]] = []
        group_pass = True
        for alternatives in group["required_node_sets"]:
            present = [node_id for node_id in alternatives if node_id in nodes]
            choice_pass = bool(present)
            if not choice_pass:
                group_pass = False
            set_results.append(
                {
                    "acceptable_node_ids": list(alternatives),
                    "present_node_ids": present,
                    "pass": choice_pass,
                }
            )
        group_results.append(
            {
                "interface_id": group["interface_id"],
                "sp554_refs": list(group["sp554_refs"]),
                "sp16_stage": group["sp16_stage"],
                "purpose": group["purpose"],
                "policy": group["policy"],
                "node_sets": set_results,
                "pass": group_pass,
            }
        )

    sp554_mechanical_ids = {
        node_id
        for node_id, node in nodes.items()
        if (
            node.get("owner_standard_id") == "SP554_2026"
            and not node_id.startswith("SP554_FIRE_D1_")
            and _node_sections(node).intersection({"8", "9", "10", "11"})
        )
    }
    producers: dict[str, list[str]] = {}
    for node_id, node in nodes.items():
        outputs = node["produces"] if "produces" in node else []
        for output in outputs:
            quantity_id = output["quantity_id"]
            if quantity_id not in producers:
                producers[quantity_id] = []
            producers[quantity_id].append(node_id)

    missing_required_producers: list[dict[str, str]] = []
    sp16_quantity_bindings: list[dict[str, Any]] = []
    for node_id in sorted(sp554_mechanical_ids):
        node = nodes[node_id]
        consumes = node["consumes"] if "consumes" in node else []
        for consume in consumes:
            quantity_id = consume["quantity_id"]
            producer_ids = producers[quantity_id] if quantity_id in producers else []
            if bool(consume.get("required")) and not producer_ids:
                missing_required_producers.append({"sp554_node_id": node_id, "quantity_id": quantity_id})
            sp16_ids = [pid for pid in producer_ids if nodes[pid].get("owner_standard_id") == "SP16_2017"]
            if sp16_ids:
                sp16_quantity_bindings.append(
                    {
                        "sp554_node_id": node_id,
                        "quantity_id": quantity_id,
                        "sp16_producer_ids": sp16_ids,
                    }
                )

    cross_edges = []
    for edge in graph["edges"]:
        source_id = edge["from_node_id"]
        target_id = edge["to_node_id"]
        if target_id in sp554_mechanical_ids and source_id in nodes and nodes[source_id].get("owner_standard_id") == "SP16_2017":
            cross_edges.append(edge["id"])

    # Fire-basis guard: structural fire clauses 8-11 must consume normative strength
    # quantity fy_norm.  A direct design-yield-resistance dependency would silently
    # re-introduce gamma_m and is therefore prohibited in this bridge.
    prohibited_quantities = {
        "design_yield_resistance_n_mm2",
        "design_ultimate_resistance_n_mm2",
        "design_shear_resistance_n_mm2",
    }
    prohibited_fire_bindings: list[dict[str, str]] = []
    for node_id in sorted(sp554_mechanical_ids):
        node = nodes[node_id]
        consumes = node["consumes"] if "consumes" in node else []
        for consume in consumes:
            quantity_id = consume["quantity_id"]
            if quantity_id in prohibited_quantities:
                prohibited_fire_bindings.append({"sp554_node_id": node_id, "quantity_id": quantity_id})

    all_groups_pass = all(row["pass"] for row in group_results)
    member_closure_pass = (
        stage_gate_pass
        and all_groups_pass
        and not missing_required_producers
        and not prohibited_fire_bindings
        and bool(sp16_quantity_bindings)
        and bool(cross_edges)
    )

    connection_status = "CLOSED" if require_connection_scope and bool(getattr(rm, "N11_CONNECTIONS_CLOSED", False)) else "DEFERRED"
    if not require_connection_scope:
        connection_status = "OUTSIDE_FIRE_D1_MEMBER_SCOPE"

    return {
        "status": "COMPLETE" if member_closure_pass else "INCOMPLETE_FAIL_CLOSED",
        "bridge_scope": "SP554 Sections 8-11 member mechanical dependencies only",
        "parent_release": rm.PARENT_RELEASE,
        "current_release": rm.RELEASE_STAGE,
        "graph_id": graph["graph_id"],
        "stage_flags": stage_flags,
        "stage_gate_pass": stage_gate_pass,
        "interface_groups": group_results,
        "sp554_mechanical_node_count": len(sp554_mechanical_ids),
        "sp16_quantity_binding_count": len(sp16_quantity_bindings),
        "sp16_unique_producer_count": len({pid for row in sp16_quantity_bindings for pid in row["sp16_producer_ids"]}),
        "cross_standard_edge_count": len(cross_edges),
        "missing_required_producers": missing_required_producers,
        "prohibited_design_resistance_fire_bindings": prohibited_fire_bindings,
        "normative_strength_basis_pass": not prohibited_fire_bindings,
        "member_mechanical_dependency_closure_pass": member_closure_pass,
        "connection_scope_status": connection_status,
        "thermal_scope_status": "NOT_IN_FIRE_D1_SCOPE",
        "next_runtime_boundary": (
            "Execute SP554 fire-side formulas 8.1-11.10 and Appendix B critical-temperature inversion using these closed SP16 coefficient producers."
        ),
    }
