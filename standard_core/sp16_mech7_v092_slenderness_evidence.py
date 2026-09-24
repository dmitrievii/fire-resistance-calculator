"""v0.92 traceable SP16 Table-32 limiting-slenderness evidence.

The existing MECH7 binder remains authoritative for PASS/FAIL and utilization.
This module wraps that qualified binder after execution, reproduces its Table-32
chain with the same audited scalar procedures, and validates exact parity before
attaching a typed calculation trace to the existing evidence row.

No report/presentation code evaluates Table 32, chooses an axis, or infers a
verdict. Any mismatch with the binder is fail-closed.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from .effective_lengths_and_limiting_slenderness import (
    compressed_limit_alpha,
    slenderness_check,
    table_32_compressed_limiting_slenderness,
)
from .fire_ui0 import ExecutionRegistry, FireUIError
from .sp16_mech7_v075_zy_runtime import BINDER_NODE_ID

TRACE_SCHEMA = "sp16_v092_limiting_slenderness_evidence_v1"
EVIDENCE_KEY = "effective_length_slenderness"

_TABLE32_FORMULAS: dict[str, dict[str, Any]] = {
    "1a": {"kind": "linear", "constant": 180.0, "alpha_coefficient": -60.0, "expression": "180-60*alpha"},
    "1b": {"kind": "constant", "constant": 120.0, "alpha_coefficient": 0.0, "expression": "120"},
    "2a": {"kind": "linear", "constant": 210.0, "alpha_coefficient": -60.0, "expression": "210-60*alpha"},
    "2b": {"kind": "linear", "constant": 220.0, "alpha_coefficient": -40.0, "expression": "220-40*alpha"},
    "3": {"kind": "constant", "constant": 220.0, "alpha_coefficient": 0.0, "expression": "220"},
    "4": {"kind": "linear", "constant": 180.0, "alpha_coefficient": -60.0, "expression": "180-60*alpha"},
    "5": {"kind": "linear", "constant": 210.0, "alpha_coefficient": -60.0, "expression": "210-60*alpha"},
    "6": {"kind": "constant", "constant": 200.0, "alpha_coefficient": 0.0, "expression": "200"},
    "7": {"kind": "constant", "constant": 150.0, "alpha_coefficient": 0.0, "expression": "150"},
}


def _number(values: Mapping[str, Any], key: str, *, positive: bool = False) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"SP16 limiting-slenderness evidence requires numeric {key}")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        raise FireUIError(f"SP16 limiting-slenderness evidence has invalid {key}")
    return result


def _axis_min(z: float, y: float) -> tuple[str, float]:
    # Deterministic tie policy is evidence-only and mirrors min(z,y).
    return ("z", z) if z <= y else ("y", y)


def _axis_max(z: float, y: float) -> tuple[str, float]:
    # Deterministic tie policy is evidence-only and mirrors max(z,y).
    return ("z", z) if z >= y else ("y", y)


def build_limiting_slenderness_trace(values: Mapping[str, Any]) -> dict[str, Any]:
    """Run the same qualified scalar chain used by the canonical MECH7 binder."""
    row_id = values.get("sp16_mech7_table32_row")
    group4 = values.get("sp16_mech7_group4_slenderness_increase")
    if not isinstance(row_id, str) or row_id not in _TABLE32_FORMULAS:
        raise FireUIError("SP16 limiting-slenderness evidence requires a valid Table-32 row id")
    if not isinstance(group4, bool):
        raise FireUIError("SP16 limiting-slenderness evidence requires explicit group-4 classification")

    n_signed = _number(values, "ambient_N_force")
    n = abs(n_signed)
    lambda_z = _number(values, "sp16_lambda_z_geom", positive=True)
    lambda_y = _number(values, "sp16_lambda_y_geom", positive=True)
    phi_z = _number(values, "phi_z_sp16", positive=True)
    phi_y = _number(values, "phi_y_sp16", positive=True)
    area = _number(values, "A_gross", positive=True)
    ry = _number(values, "Ry_formula", positive=True)
    gamma_c = _number(values, "gamma_c_compression", positive=True)

    phi_axis, phi_governing = _axis_min(phi_z, phi_y)
    lambda_axis, actual_lambda = _axis_max(lambda_z, lambda_y)

    alpha_raw = n / (phi_governing * area * ry * gamma_c)
    alpha = float(compressed_limit_alpha(n, phi_governing, area, ry, gamma_c))
    expected_alpha = max(alpha_raw, 0.5)
    if not math.isclose(alpha, expected_alpha, rel_tol=1e-12, abs_tol=1e-12):
        raise FireUIError("SP16 Table-32 alpha producer is inconsistent with its disclosed formula")

    base_limit = float(table_32_compressed_limiting_slenderness(row_id, alpha, False))
    final_limit = float(table_32_compressed_limiting_slenderness(row_id, alpha, group4))
    group4_factor = 1.1 if group4 else 1.0
    if not math.isclose(final_limit, base_limit * group4_factor, rel_tol=1e-12, abs_tol=1e-12):
        raise FireUIError("SP16 Table-32 group-4 factor is inconsistent with final lambda_u")

    check = slenderness_check(actual_lambda, final_limit)
    formula = copy.deepcopy(_TABLE32_FORMULAS[row_id])

    return {
        "schema": TRACE_SCHEMA,
        "normative_basis": "СП 16.13330.2017 с изм. №1–6, п. 10.4.1, таблица 32; п. 10.4.2 для группы 4",
        "table32_row_id": row_id,
        "table32_row_formula": formula,
        "group4_classification": group4,
        "group4_factor": group4_factor,
        "inputs": {
            "N_signed_n": n_signed,
            "N_magnitude_n": n,
            "A_gross_mm2": area,
            "Ry_n_mm2": ry,
            "gamma_c": gamma_c,
            "phi_z": phi_z,
            "phi_y": phi_y,
            "lambda_z": lambda_z,
            "lambda_y": lambda_y,
        },
        "alpha": {
            "governing_phi_axis": phi_axis,
            "governing_phi": phi_governing,
            "raw": alpha_raw,
            "minimum": 0.5,
            "result": alpha,
            "minimum_applied": alpha_raw < 0.5,
        },
        "limiting_slenderness": {
            "base": base_limit,
            "group4_factor": group4_factor,
            "result": final_limit,
        },
        "actual_slenderness": {
            "governing_axis": lambda_axis,
            "lambda_z": lambda_z,
            "lambda_y": lambda_y,
            "result": actual_lambda,
        },
        "check": {
            "utilization": float(check["utilization"]),
            "pass": bool(check["pass"]),
            "unlimited": bool(check["unlimited"]),
        },
        "presentation_recomputes_values": False,
    }


def _validate_against_binder(trace: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    check = trace.get("check")
    if not isinstance(check, Mapping):
        raise FireUIError("SP16 limiting-slenderness trace has no check block")
    utilization = row.get("utilization")
    passed = row.get("pass")
    status = row.get("status")
    if isinstance(utilization, bool) or not isinstance(utilization, (int, float)):
        raise FireUIError("SP16 limiting-slenderness binder evidence has no numeric utilization")
    if not math.isclose(float(utilization), float(check["utilization"]), rel_tol=1e-11, abs_tol=1e-12):
        raise FireUIError("SP16 limiting-slenderness trace does not reproduce binder utilization")
    if not isinstance(passed, bool) or passed is not bool(check["pass"]):
        raise FireUIError("SP16 limiting-slenderness trace does not reproduce binder PASS/FAIL")
    expected_status = "PASS" if check["pass"] else "FAIL"
    if status != expected_status:
        raise FireUIError("SP16 limiting-slenderness trace does not reproduce binder status")


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Attach validated Table-32 calculation trace to the existing MECH7 binder."""
    previous = registry.get(BINDER_NODE_ID)
    if previous is None:
        raise FireUIError(f"SP16 limiting-slenderness evidence requires registered {BINDER_NODE_ID}")
    if getattr(previous, "_sp16_v092_slenderness_evidence", False):
        return registry

    def executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        outputs = dict(previous(values, node))
        bundle = outputs.get("sp16_mech7_primary_evidence")
        if not isinstance(bundle, Mapping):
            return outputs
        evidence = bundle.get("evidence")
        if not isinstance(evidence, Mapping):
            return outputs
        current = evidence.get(EVIDENCE_KEY)
        if not isinstance(current, Mapping):
            return outputs
        # A deferred branch must remain deferred; no speculative formula trace is
        # generated before its prerequisites/classification exist.
        if current.get("status") not in {"PASS", "FAIL"}:
            return outputs

        trace = build_limiting_slenderness_trace(values)
        _validate_against_binder(trace, current)

        patched_bundle = copy.deepcopy(dict(bundle))
        patched_evidence = dict(patched_bundle.get("evidence") or {})
        patched_row = copy.deepcopy(dict(current))
        patched_row["calculation_trace"] = trace
        patched_row["calculation_trace_validated_against_binder"] = True
        patched_evidence[EVIDENCE_KEY] = patched_row
        patched_bundle["evidence"] = patched_evidence
        outputs["sp16_mech7_primary_evidence"] = patched_bundle
        return outputs

    setattr(executor, "_sp16_v092_slenderness_evidence", True)
    setattr(executor, "_sp16_v092_slenderness_previous", previous)
    registry.register(BINDER_NODE_ID, executor)
    return registry


__all__ = [
    "EVIDENCE_KEY",
    "TRACE_SCHEMA",
    "build_limiting_slenderness_trace",
    "install_registry_remediation",
]
