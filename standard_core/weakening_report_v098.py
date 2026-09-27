"""v0.98 canonical weakening evidence reconciliation for REPORT-IR.

The runtime weakening executors already own the qualified geometry/manual-net
calculation traces.  This module republishes that same executor-owned evidence
into REPORT-IR from the accepted session state so retained sessions cannot fall
back to a final A_n value without its derivation.  It does not change mechanical
state or introduce presentation-side engineering calculations.
"""
from __future__ import annotations

import copy
import json
from hashlib import sha256
from typing import Any, Mapping

from .fire_ui0 import FireUIError
from .fire_ui14_manual_net_v092 import MANUAL_MODE, _manual_net_executor
from .fire_ui14_section_weakening import _alpha45_executor, _net_geometry_executor
from .report_ir5 import _rebuild_sections

BLOCK_ID = "V098:SP16_SECTION_WEAKENING_RECONCILIATION"
OWNER_NODE_ID = "SP16_SECTION_WEAKENING_RECONCILIATION_V098"


def _session_values(session_or_snapshot: Any) -> Mapping[str, Any]:
    plain = getattr(session_or_snapshot, "plain_values", None)
    if callable(plain):
        values = plain()
        return values if isinstance(values, Mapping) else {}
    if isinstance(session_or_snapshot, Mapping):
        if "section_weakening_model" in session_or_snapshot:
            return session_or_snapshot
        values = session_or_snapshot.get("values")
        if isinstance(values, Mapping):
            return values
    return {}


def reconcile_weakening_outputs(values: Mapping[str, Any]) -> dict[str, Any] | None:
    """Re-run the canonical weakening executor solely to recover typed evidence.

    The returned values are report evidence only.  They are not written back to
    the calculation session and therefore cannot alter downstream mechanics.
    """
    model = values.get("section_weakening_model")
    if not isinstance(model, Mapping):
        return None
    try:
        if model.get("holes_present") is True and model.get("net_property_mode") == MANUAL_MODE:
            out = dict(_manual_net_executor(values, {}))
        else:
            out = dict(_net_geometry_executor(values, {}))
    except (FireUIError, KeyError, TypeError, ValueError):
        return None

    geometry = out.get("net_section_geometry_2d")
    if not isinstance(geometry, Mapping) or not isinstance(geometry.get("calculation_trace"), Mapping):
        return None

    if geometry["calculation_trace"].get("sp16_formula45", {}).get("applicable") is True:
        try:
            alpha = _alpha45_executor({**values, **out}, {})
            out.update(alpha)
        except (FireUIError, KeyError, TypeError, ValueError):
            # Existing executed alpha evidence, if present, remains available in
            # the original report blocks.  Do not invent a replacement here.
            pass
    return out


def _row(qid: str, value: Any, unit: str | None = None) -> dict[str, Any]:
    display = str(value)
    if unit:
        display += f" {unit}"
    return {
        "quantity_id": qid,
        "symbol": qid,
        "name_ru": qid,
        "raw_value": copy.deepcopy(value),
        "canonical_unit": unit,
        "display_value": display,
    }


def augment_weakening_report_ir_v098(report: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    reconciled = reconcile_weakening_outputs(values)
    if reconciled is None:
        return copy.deepcopy(dict(report))

    out = copy.deepcopy(dict(report))
    blocks = [
        block for block in (out.get("blocks") or [])
        if not (isinstance(block, Mapping) and block.get("report_block_id") == BLOCK_ID)
    ]
    sequence = max((int(block.get("sequence") or 0) for block in blocks if isinstance(block, Mapping)), default=0) + 1

    outputs: list[dict[str, Any]] = []
    units = {
        "A_net": "mm2",
        "sp16_net_removed_area": "mm2",
        "I_xn": "mm4",
        "I_yn": "mm4",
        "W_xn_min": "mm3",
        "W_yn_min": "mm3",
        "W_pl_x_eff": "mm3",
        "W_pl_y_eff": "mm3",
        "W_pl_min_eff": "mm3",
        "I_omega_n": "mm6",
        "W_omega_eff": "mm4",
        "sp16_wall_hole_pitch_s": "mm",
        "sp16_wall_hole_diameter_d": "mm",
        "sp16_shear_hole_alpha45": "1",
    }
    ordered_qids = [
        "net_section_geometry_2d", "A_net", "sp16_net_removed_area",
        "I_xn", "I_yn", "W_xn_min", "W_yn_min",
        "W_pl_x_eff", "W_pl_y_eff", "W_pl_min_eff", "I_omega_n", "W_omega_eff",
        "sp16_wall_hole_pitch_s", "sp16_wall_hole_diameter_d", "sp16_shear_hole_alpha45",
    ]
    for qid in ordered_qids:
        if qid in reconciled:
            outputs.append(_row(qid, reconciled[qid], units.get(qid)))

    block = {
        "schema": "fire_report_block_v1",
        "report_block_id": BLOCK_ID,
        "owner_node_id": OWNER_NODE_ID,
        "owner_standard_id": "SP16_2017",
        "sequence": sequence,
        "event_kind": "active_report_reconciliation",
        "kind": "FORMULA",
        "section_key": "input_data",
        "title": "Ослабления поперечного сечения — воспроизводимый trace",
        "normative_refs": [{"standard_id": "SP16_2017", "reference": "8.2.1, формула (45)"}],
        "inputs": [],
        "outputs": outputs,
        "selected_edge_id": None,
        "execution_spec": {"mode": "canonical_weakening_executor_evidence_replay"},
        "execution_evidence": {
            "evidence_mode": "shared_runtime_weakening_executor",
            "report_recomputed_mechanical_state": False,
            "mechanical_values_overridden": False,
        },
        "progress_state": "COMPLETE",
    }
    blocks.append(block)
    blocks.sort(key=lambda row: (int(row.get("sequence") or 0), str(row.get("report_block_id") or "")))
    out["blocks"] = blocks
    out["block_count"] = len(blocks)
    out["sections"] = _rebuild_sections([row for row in blocks if isinstance(row, Mapping)])
    audit = dict(out.get("audit") or {})
    audit.update({
        "v098_weakening_trace_reconciled": True,
        "v098_weakening_source": "shared_runtime_weakening_executor",
        "v098_mechanical_values_changed": False,
    })
    out["audit"] = audit
    out.pop("report_sha256", None)
    canonical = json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    out["report_sha256"] = sha256(canonical).hexdigest()
    return out


def augment_from_session(report: Mapping[str, Any], session_or_snapshot: Any) -> dict[str, Any]:
    return augment_weakening_report_ir_v098(report, _session_values(session_or_snapshot))


__all__ = [
    "BLOCK_ID", "OWNER_NODE_ID", "reconcile_weakening_outputs",
    "augment_weakening_report_ir_v098", "augment_from_session",
]
