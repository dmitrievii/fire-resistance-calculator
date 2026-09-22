"""v0.78 explicit SP16 Table-1 working-condition factor for compression.

`gamma_c_compression` is a normative classification, not a physical constant and
not a safe default.  The caller must choose an applicable Table-1 case (including
Note 5 when the case is not listed).  This module performs an exact lookup in the
qualified project dataset and never infers a case from geometry or building use.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "table_1_working_condition_factors.json"
INPUT_QID = "sp16_table1_compression_case_id"
OUTPUT_QID = "gamma_c_compression"
EVIDENCE_QID = "sp16_table1_compression_evidence"
CALC_NODE_ID = "SP16_C_V078_GAMMA_C_COMPRESSION"

# Rows whose gamma_c can govern the central-compression/member-stability checks
# bound by MECH7.  Strength-only tension, net-section-hole and bearing-plate rows
# are intentionally excluded because one scalar gamma_c_compression must not
# silently leak those narrower applicability rules into member stability.
COMPRESSION_CASE_IDS = (
    "1_floor_beams_and_compressed_floor_truss_members",
    "2_public_residential_columns_permanent_load_ratio_ge_0_8",
    "2_multistorey_columns_height_le_150m",
    "2_multistorey_i_section_height_gt_150m",
    "2_multistorey_box_section_height_gt_150m",
    "2_water_tower_supports",
    "3_single_storey_industrial_columns_with_overhead_cranes",
    "4_compressed_main_built_up_tee_lattice_members_slenderness_gt_60",
    "7a_first_brace_and_strut_group_per_table_1",
    "7a_second_brace_group_per_table_1",
    "7b_single_bolt_or_gusset",
    "8_single_angle_compressed_members_one_leg_except_exclusions",
    "default_unlisted_case_note_5",
)


def _dataset() -> dict[str, Any]:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FireUIError("cannot load qualified SP16 Table-1 working-condition dataset") from exc
    if data.get("lookup_policy") != "exact_categorical_only":
        raise FireUIError("SP16 Table-1 dataset must remain exact-categorical")
    return data


def compression_case_options() -> list[dict[str, Any]]:
    data = _dataset()
    rows = {str(row.get("case_id")): row for row in data.get("rows", []) if isinstance(row, Mapping)}
    options: list[dict[str, Any]] = []
    for case_id in COMPRESSION_CASE_IDS:
        row = rows.get(case_id)
        if row is None:
            raise FireUIError(f"qualified SP16 Table-1 dataset misses compression case {case_id}")
        gamma = row.get("gamma_c")
        if isinstance(gamma, bool) or not isinstance(gamma, (int, float)) or not math.isfinite(float(gamma)) or float(gamma) <= 0.0:
            raise FireUIError(f"invalid gamma_c for SP16 Table-1 case {case_id}")
        options.append({
            "value": case_id,
            "gamma_c": float(gamma),
            "description_ru": str(row.get("description_ru") or case_id),
        })
    return options


def resolve_gamma_c_compression(case_id: str) -> dict[str, Any]:
    if not isinstance(case_id, str) or not case_id.strip():
        raise FireUIError("gamma_c_compression requires an explicit SP16 Table-1 classification")
    options = {row["value"]: row for row in compression_case_options()}
    if case_id not in options:
        raise FireUIError(f"unsupported SP16 Table-1 compression case: {case_id}")
    row = options[case_id]
    data = _dataset()
    return {
        OUTPUT_QID: row["gamma_c"],
        EVIDENCE_QID: {
            "case_id": case_id,
            "gamma_c": row["gamma_c"],
            "description_ru": row["description_ru"],
            "standard": data.get("standard"),
            "clause": data.get("clause"),
            "table": data.get("table"),
            "version_basis": data.get("version_basis"),
            "lookup_policy": data.get("lookup_policy"),
            "classification_source": "explicit_user_selection",
        },
    }


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    def executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> dict[str, Any]:
        return resolve_gamma_c_compression(values.get(INPUT_QID))

    setattr(executor, "_sp16_v078_gamma_c_compression", True)
    registry.register(CALC_NODE_ID, executor)
    return registry


__all__ = [
    "CALC_NODE_ID", "COMPRESSION_CASE_IDS", "EVIDENCE_QID", "INPUT_QID", "OUTPUT_QID",
    "compression_case_options", "install_registry_remediation", "resolve_gamma_c_compression",
]
