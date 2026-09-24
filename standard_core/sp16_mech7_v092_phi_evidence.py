"""v0.92 full SP16 central-compression phi evidence over the qualified producer.

This module does not replace the authoritative scalar stability producer.  The
active MECH7 state first obtains ``phi_z``/``phi_y`` from the existing qualified
runtime.  This evidence layer then reconstructs the explicit Table-7 / Eq.(9) /
Eq.(8) intermediates and validates that the disclosed chain reproduces that
already-produced final phi.  A mismatch is fail-closed.

The purpose is report traceability, not a second engineering decision path.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from .axial_members import stability_delta, table_7_section_coefficients
from .fire_ui0 import ExecutionRegistry, FireUIError
from .sp16_mech7_v076_graph_overlay import STATE_NODE_ID
from .sp16_mech7_v092_effective_length import EVIDENCE_QID

PHI_TRACE_SCHEMA = "sp16_v092_phi_evidence_v1"


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FireUIError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise FireUIError(f"{name} must be finite")
    return result


def build_phi_evidence(
    relative_slenderness: float,
    curve: str,
    final_phi: float,
) -> dict[str, Any]:
    """Build and validate full Table-7 / delta / phi evidence for one axis."""
    lambda_bar = _finite(relative_slenderness, "lambda_bar")
    phi_runtime = _finite(final_phi, "phi_runtime")
    if lambda_bar < 0.0 or phi_runtime <= 0.0:
        raise FireUIError("SP16 phi evidence requires lambda_bar >= 0 and phi > 0")
    curve_id = str(curve)
    try:
        alpha, beta = table_7_section_coefficients(curve_id)
    except (TypeError, ValueError) as exc:
        raise FireUIError(f"SP16 phi evidence has invalid Table-7 curve: {curve_id!r}") from exc

    threshold = {"a": 3.8, "b": 4.4, "c": 5.8}[curve_id]
    base = {
        "schema": PHI_TRACE_SCHEMA,
        "normative_basis": "СП 16.13330.2017 с изм. №1–6, п. 7.1.3, формулы (8)–(9), таблица 7",
        "curve": curve_id,
        "alpha": float(alpha),
        "beta": float(beta),
        "lambda_bar": lambda_bar,
        "cap_threshold_lambda_bar": float(threshold),
        "final_phi": phi_runtime,
        "final_phi_source": "qualified_MECH7_runtime",
    }

    # Clause 7.1.3 prescribes phi=1 directly for types a/b when lambda_bar<0.6.
    # Eq.(8)/(9) is not the governing branch there, so delta is deliberately not
    # fabricated merely to make the report look uniform.
    if curve_id in {"a", "b"} and lambda_bar < 0.6:
        if not math.isclose(phi_runtime, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise FireUIError("SP16 low-slenderness phi evidence does not match runtime phi=1 rule")
        return {
            **base,
            "branch": "low_slenderness_direct_phi_1",
            "delta": None,
            "eq8_radicand": None,
            "phi_eq8": None,
            "cap_candidate": None,
            "cap_applied": False,
            "validated_against_runtime": True,
        }

    if curve_id == "c" and lambda_bar < 0.4:
        raise FireUIError("SP16 type-c phi evidence is unresolved below lambda_bar=0.4")

    delta = float(stability_delta(lambda_bar, alpha, beta))
    radicand = delta * delta - 39.48 * lambda_bar * lambda_bar
    if radicand < -1e-12:
        raise FireUIError("SP16 Eq.(8) evidence radicand is negative")
    radicand = max(radicand, 0.0)
    phi_eq8 = 19.74 / (delta + math.sqrt(radicand))
    cap_applied = lambda_bar >= threshold
    cap_candidate = 7.6 / (lambda_bar * lambda_bar) if cap_applied else None
    expected = min(phi_eq8, cap_candidate) if cap_candidate is not None else phi_eq8
    if not math.isclose(expected, phi_runtime, rel_tol=1e-11, abs_tol=1e-12):
        raise FireUIError(
            "SP16 full-phi evidence does not reproduce the qualified runtime result: "
            f"evidence={expected:.15g}, runtime={phi_runtime:.15g}"
        )

    return {
        **base,
        "branch": "eq8_eq9_with_table7",
        "delta": delta,
        "eq8_radicand": radicand,
        "phi_eq8": phi_eq8,
        "cap_candidate": cap_candidate,
        "cap_applied": cap_applied,
        "validated_against_runtime": True,
    }


def _enrich_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    enriched = copy.deepcopy(dict(trace))
    for axis in ("z", "y"):
        state = enriched.get(axis)
        if not isinstance(state, dict):
            raise FireUIError(f"SP16 full-phi evidence requires axis {axis}")
        state["phi_evidence"] = build_phi_evidence(
            state.get("lambda_bar"),
            str(state.get("curve") or ""),
            state.get("phi"),
        )
    enriched["full_phi_evidence_contract"] = PHI_TRACE_SCHEMA
    return enriched


def install_registry_remediation(registry: ExecutionRegistry) -> ExecutionRegistry:
    """Wrap the existing MECH7 state executor with validated evidence enrichment."""
    previous = registry.get(STATE_NODE_ID)
    if previous is None:
        raise FireUIError(f"SP16 full-phi evidence requires registered executor {STATE_NODE_ID}")
    if getattr(previous, "_sp16_v092_full_phi_evidence", False):
        return registry

    def executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
        outputs = dict(previous(values, node))
        trace = outputs.get(EVIDENCE_QID)
        if not isinstance(trace, Mapping):
            raise FireUIError("SP16 full-phi evidence requires effective-length z/y runtime trace")
        outputs[EVIDENCE_QID] = _enrich_trace(trace)
        return outputs

    setattr(executor, "_sp16_v092_full_phi_evidence", True)
    setattr(executor, "_sp16_v092_full_phi_previous", previous)
    registry.register(STATE_NODE_ID, executor)
    return registry


__all__ = [
    "PHI_TRACE_SCHEMA",
    "build_phi_evidence",
    "install_registry_remediation",
]
