"""SP16-MECH6 aggregate ambient mechanical verification gate.

The module converts the SP16-MECH2 applicability census into a strict auditable
verification ledger.  A mechanics/stress-recovery state is never treated as a
normative PASS by itself.  Only explicit normative evidence (utilization/pass
results from qualified SP16 stages) can close an applicable check.

The aggregate gate is fail-closed:
- any explicit failed check -> ``FAIL``;
- no failures but any unresolved applicable/context check ->
  ``INCOMPLETE_FAIL_CLOSED``;
- all mandatory rows resolved as PASS or N.A. -> ``PASS``.

This stage deliberately does not fabricate missing N3-N10 execution.  It binds
available evidence and makes every missing branch visible so later increments
can route those workflows before SP554 without changing the gate semantics.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .fire_ui0 import ExecutionRegistry, FireUIError
from .profile_catalog import InterimProfileCatalog
from .sp16_mech5_bimoment import build_sp16_mech5_registry


_EPS = 1e-12


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _numeric_if_present(values: Mapping[str, Any], qid: str) -> float | None:
    if qid not in values or values[qid] is None:
        return None
    try:
        return _finite_number(values[qid], qid)
    except (TypeError, ValueError):
        return None


def _bool_if_present(values: Mapping[str, Any], qid: str) -> bool | None:
    value = values.get(qid)
    return value if isinstance(value, bool) else None


def _status_from_utilization(utilization: float, *, evidence: str, clause: list[str] | None = None) -> dict[str, Any]:
    u = _finite_number(utilization, "utilization")
    return {
        "status": "PASS" if u <= 1.0 + _EPS else "FAIL",
        "utilization": u,
        "pass": u <= 1.0 + _EPS,
        "evidence_source": evidence,
        "evidence_scope": clause or [],
    }


def _status_from_boolean(passed: bool, *, evidence: str, clause: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "PASS" if passed else "FAIL",
        "utilization": None,
        "pass": bool(passed),
        "evidence_source": evidence,
        "evidence_scope": clause or [],
    }


def _deferred(reason: str, *, evidence: str | None = None) -> dict[str, Any]:
    return {
        "status": "DEFERRED",
        "utilization": None,
        "pass": None,
        "evidence_source": evidence,
        "reason": reason,
    }


def _context_unresolved(reason: str) -> dict[str, Any]:
    return {
        "status": "CONTEXT_UNRESOLVED",
        "utilization": None,
        "pass": None,
        "evidence_source": None,
        "reason": reason,
    }


def _na(reason: str, *, evidence: str | None = None) -> dict[str, Any]:
    return {
        "status": "N.A.",
        "utilization": None,
        "pass": None,
        "evidence_source": evidence,
        "reason": reason,
    }


def _resolve_shear(check_id: str, values: Mapping[str, Any]) -> dict[str, Any]:
    state = values.get("ambient_axis_shear_state")
    if not isinstance(state, Mapping):
        return _deferred("SP16-MECH3 axis-shear state is missing", evidence="ambient_axis_shear_state")
    comp = state.get("clause_8_2_3_components")
    mech = state.get("mechanics_component_checks")
    if check_id == "shear_x":
        if isinstance(comp, Mapping) and comp.get("applicable") and isinstance(comp.get("utilization_tau_x_823"), (int, float)):
            return _status_from_utilization(float(comp["utilization_tau_x_823"]), evidence="SP16-MECH3 clause 8.2.3 tau_x", clause=["SP16 8.2.3"])
        if isinstance(mech, Mapping) and mech.get("available") and isinstance(mech.get("utilization_tau_x_Rs_gamma_c"), (int, float)):
            return _status_from_utilization(float(mech["utilization_tau_x_Rs_gamma_c"]), evidence="SP16-MECH3 pointwise Eq.42-style tau_x", clause=["SP16 8.2.1 Eq.(42) mechanics route"])
    if check_id == "shear_y":
        if isinstance(comp, Mapping) and comp.get("applicable") and isinstance(comp.get("utilization_tau_y_823"), (int, float)):
            return _status_from_utilization(float(comp["utilization_tau_y_823"]), evidence="SP16-MECH3 clause 8.2.3 tau_y", clause=["SP16 8.2.3"])
        if isinstance(mech, Mapping) and mech.get("available") and isinstance(mech.get("utilization_tau_y_Rs_gamma_c"), (int, float)):
            return _status_from_utilization(float(mech["utilization_tau_y_Rs_gamma_c"]), evidence="SP16-MECH3 pointwise Eq.42-style tau_y", clause=["SP16 8.2.1 Eq.(42) mechanics route"])
    return _deferred(f"No qualified normative shear evidence is available for {check_id}", evidence="ambient_axis_shear_state")


def _mech7_bound_evidence(check_id: str, values: Mapping[str, Any]) -> dict[str, Any] | None:
    # MECH9 is the latest cumulative evidence overlay. Prefer it when present,
    # then fall back through MECH8/MECH7 for isolated parent-stage tests.
    bundle = values.get("sp16_mech9_primary_evidence")
    if not isinstance(bundle, Mapping):
        bundle = values.get("sp16_mech8_primary_evidence")
    if not isinstance(bundle, Mapping):
        bundle = values.get("sp16_mech7_primary_evidence")
    if not isinstance(bundle, Mapping):
        return None
    evidence = bundle.get("evidence")
    if not isinstance(evidence, Mapping):
        return None
    row = evidence.get(check_id)
    if not isinstance(row, Mapping):
        return None
    status = row.get("status")
    if status not in {"PASS", "FAIL", "N.A.", "DEFERRED", "CONTEXT_UNRESOLVED"}:
        raise FireUIError(f"invalid SP16-MECH7 evidence status for {check_id}: {status}")
    return dict(row)


def _resolve_active(check: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    cid = str(check.get("id"))
    bound = _mech7_bound_evidence(cid, values)
    if bound is not None:
        return bound
    runtime = str(check.get("runtime_status") or "")
    if runtime.startswith("deferred_"):
        return _deferred(f"Applicability census runtime is deferred: {runtime}", evidence="sp16_applicability_census")

    if cid in {"shear_x", "shear_y"}:
        return _resolve_shear(cid, values)

    if cid in {"section_tension", "section_compression"}:
        vals = [
            ("sp16_n3_eq5_eta_yield", _numeric_if_present(values, "sp16_n3_eq5_eta_yield")),
            ("sp16_n3_eq5_eta_ultimate", _numeric_if_present(values, "sp16_n3_eq5_eta_ultimate")),
        ]
        present = [(qid, u) for qid, u in vals if u is not None]
        if present:
            qid, u = max(present, key=lambda x: float(x[1]))
            return _status_from_utilization(float(u), evidence=qid, clause=["SP16 7.1.1 Eq.(5)"])
        return _deferred("Stage N3 axial section-strength result has not been executed/bound in this ambient session", evidence="SP16 N3")

    if cid == "member_compression_stability":
        vals = [
            ("sp16_n3_eta7", _numeric_if_present(values, "sp16_n3_eta7")),
            ("sp16_n3_eta7a", _numeric_if_present(values, "sp16_n3_eta7a")),
        ]
        present = [(qid, u) for qid, u in vals if u is not None]
        if present:
            qid, u = max(present, key=lambda x: float(x[1]))
            return _status_from_utilization(float(u), evidence=qid, clause=["SP16 7.1.3 Eq.(7)/(7a)"])
        return _deferred("Stage N3 compression-stability result is not available in ambient flow", evidence="SP16 N3")

    if cid == "effective_length_slenderness":
        passed = _bool_if_present(values, "sp16_n7_slenderness_pass")
        if passed is not None:
            return _status_from_boolean(passed, evidence="sp16_n7_slenderness_pass", clause=["SP16 §10"])
        return _deferred("Stage N7 effective-length/slenderness result is not available in ambient flow", evidence="SP16 N7")

    if cid in {"bending_x", "bending_y", "biaxial_bending"}:
        u = _numeric_if_present(values, "sp16_n4_eta_governing")
        if u is not None:
            return _status_from_utilization(u, evidence="sp16_n4_eta_governing", clause=["SP16 §8"])
        # For a one-plane N4 session, eta41 is also explicit evidence.
        u41 = _numeric_if_present(values, "sp16_n4_eta41")
        if u41 is not None and cid in {"bending_x", "bending_y"}:
            return _status_from_utilization(u41, evidence="sp16_n4_eta41", clause=["SP16 8.2.1 Eq.(41)"])
        return _deferred("Stage N4 bending-strength workflow has not been executed/bound for this ambient state", evidence="SP16 N4")

    if cid == "interaction_N_M":
        # The current N5 DAG stores route/completeness evidence but not a single
        # governing utilization quantity.  Do not reinterpret release_gate as
        # a structural PASS.
        status = values.get("sp16_n5_runtime_status")
        return _deferred(
            "Stage N5 N+M normative utilization/pass evidence is not yet bound to the aggregate gate"
            + (f" (runtime_status={status})" if status is not None else ""),
            evidence="SP16 N5",
        )

    if cid == "interaction_M_Q":
        return _deferred("Combined M+Q family requires an explicit applicable SP16 interaction result; pointwise mechanics alone is not accepted as PASS", evidence="SP16 §8")

    if cid == "torsion_T":
        closed = _bool_if_present(values, "ambient_torsion_runtime_closed")
        if closed is False:
            return _deferred("Free-torsion mechanics is unresolved for the selected geometry", evidence="SP16-MECH4")
        return _deferred("T→tau_T mechanics is available, but no universal standalone SP16 torsion resistance PASS criterion is bound", evidence="SP16-MECH4")

    if cid == "bimoment_B":
        closed = _bool_if_present(values, "ambient_bimoment_runtime_closed")
        if closed is False:
            return _deferred("B warping recovery is unresolved for the selected geometry", evidence="SP16-MECH5")
        return _deferred("B→sigma_omega mechanics is available, but combined normative section/member verification must still be executed", evidence="SP16-MECH5")

    return _deferred(f"No SP16-MECH6 evidence adapter is defined for active check {cid}")


def _resolve_context(check: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    cid = str(check.get("id"))
    bound = _mech7_bound_evidence(cid, values)
    if bound is not None:
        return bound
    trigger = str(check.get("trigger") or "additional design context")

    if cid == "beam_ltb":
        required = _bool_if_present(values, "ltb_check_required")
        if required is False:
            return _na("LTB explicitly classified as not required", evidence="ltb_check_required")
        if required is True:
            u = _numeric_if_present(values, "sp16_n4_eta69")
            if u is not None:
                return _status_from_utilization(u, evidence="sp16_n4_eta69", clause=["SP16 Eq.(69)"])
            return _deferred("LTB is required, but Stage N4 Eq.(69) evidence is missing", evidence="SP16 N4")
        return _context_unresolved(f"LTB applicability has not been classified: {trigger}")

    if cid == "local_stability_web":
        v = values.get("sp16_n6_web_status")
        if isinstance(v, bool):
            return _status_from_boolean(v, evidence="sp16_n6_web_status", clause=["SP16 local stability"])
        return _context_unresolved(f"Web local-stability applicability/result is unresolved: {trigger}")

    if cid == "local_stability_flange":
        v = values.get("sp16_n6_flange_status")
        if isinstance(v, bool):
            return _status_from_boolean(v, evidence="sp16_n6_flange_status", clause=["SP16 local stability"])
        return _context_unresolved(f"Flange local-stability applicability/result is unresolved: {trigger}")

    if cid == "fatigue":
        # N9 gate booleans can prove completeness of that dedicated stage, but
        # are not automatically present in the primary ambient route.
        gate = values.get("sp16_n9_external_gate_status")
        clause = values.get("sp16_n9_clause1213_status")
        if isinstance(gate, bool) and isinstance(clause, bool):
            return _status_from_boolean(gate and clause, evidence="SP16 N9 completion gates", clause=["SP16 §12"])
        return _context_unresolved(f"Fatigue applicability/result is unresolved: {trigger}")

    if cid == "brittle_fracture":
        general = values.get("sp16_n10_general_prevention_status")
        external = values.get("sp16_n10_external_gate_status")
        if isinstance(general, bool) and isinstance(external, bool):
            return _status_from_boolean(general and external, evidence="SP16 N10 completion gates", clause=["SP16 §13"])
        return _context_unresolved(f"Brittle-fracture applicability/result is unresolved: {trigger}")

    return _context_unresolved(f"No context resolver is bound for {cid}: {trigger}")


def aggregate_sp16_mechanical_verification(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Build the strict fail-closed SP16 ambient verification ledger and aggregate mechanical gate from the applicability census and qualified stage evidence.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; the function aggregates already qualified clause-specific SP16 evidence without inventing a new resistance equation.

    Parameters:
        values: Current guided-session quantity mapping containing the ambient applicability census plus any explicit normative evidence produced by qualified SP16 N3-N10 stages.

    Returns:
        Mapping with the complete verification ledger, gate status, SP16_MECHANICAL_PASS boolean, fail/unresolved flags and governing utilization when available.

    Assumptions:
        Mechanics/stress-recovery states are diagnostic inputs only and never constitute normative PASS evidence unless a qualified SP16 check explicitly produces utilization/pass evidence.

    Sign convention:
        The aggregator preserves the canonical signed action convention established by SP16-MECH1; it does not transform or recompute action signs.

    Unit convention:
        Utilizations are dimensionless; boolean evidence is unitless.  Underlying quantities retain the canonical units declared by their producer stages.

    Applicability:
        Ambient SP16 verification after SP16-MECH2 applicability census generation in the cumulative v0.63 guided workflow.

    Limitations:
        The aggregate gate accepts the latest explicit SP16-MECH8/MECH7 primary evidence when present and otherwise retains the v0.63 stage-evidence adapters; missing applicable evidence still yields INCOMPLETE_FAIL_CLOSED rather than a guessed PASS.

    Raises:
        FireUIError when the applicability census is missing or malformed; TypeError/ValueError when bound utilization evidence is non-finite or otherwise invalid.

    Examples:
        Call ``aggregate_sp16_mechanical_verification(session_values)`` after an ambient census; inspect ``sp16_mechanical_gate_status`` and ``sp16_mechanical_pass`` before permitting SP554.

    Tests:
        tests/test_sp16_mech6_gate.py and cumulative SP16-MECH/FIRE-UI regression suites.

    Implementation notes:
        Explicit FAIL dominates unresolved evidence; otherwise any DEFERRED/CONTEXT_UNRESOLVED row blocks the transition. Only a fully resolved ledger produces PASS.
    """
    census = values.get("sp16_applicability_census")
    if not isinstance(census, Mapping):
        raise FireUIError("sp16_applicability_census is required")
    active = census.get("active_checks")
    contextual = census.get("context_driven_checks")
    if not isinstance(active, list) or not isinstance(contextual, list):
        raise FireUIError("sp16_applicability_census has invalid check lists")

    rows: list[dict[str, Any]] = []
    for item in active:
        if not isinstance(item, Mapping):
            raise FireUIError("active census row must be an object")
        evidence = _resolve_active(item, values)
        rows.append({
            "id": item.get("id"),
            "family": item.get("family"),
            "label": item.get("label"),
            "applicability": "applicable",
            "normative_scope": item.get("normative_scope") or [],
            "census_runtime_status": item.get("runtime_status"),
            **evidence,
        })

    for item in contextual:
        if not isinstance(item, Mapping):
            raise FireUIError("context census row must be an object")
        evidence = _resolve_context(item, values)
        rows.append({
            "id": item.get("id"),
            "family": item.get("family"),
            "label": item.get("label"),
            "applicability": item["applicability"],
            "normative_scope": item.get("normative_scope") or [],
            **evidence,
        })

    failed = [str(r["id"]) for r in rows if r["status"] == "FAIL"]
    unresolved = [str(r["id"]) for r in rows if r["status"] in {"DEFERRED", "CONTEXT_UNRESOLVED"}]
    passed = [str(r["id"]) for r in rows if r["status"] == "PASS"]
    na = [str(r["id"]) for r in rows if r["status"] == "N.A."]
    utils = [float(r["utilization"]) for r in rows if isinstance(r.get("utilization"), (int, float)) and not isinstance(r.get("utilization"), bool)]

    if failed:
        gate_status = "FAIL"
    elif unresolved:
        gate_status = "INCOMPLETE_FAIL_CLOSED"
    else:
        gate_status = "PASS"
    mechanical_pass = gate_status == "PASS"

    report = {
        "schema": "sp16_mech6_mechanical_verification_v1",
        "load_case_kind": "ambient",
        "gate_policy": "all applicable checks must have explicit normative PASS evidence; unresolved context/runtime is fail-closed",
        "rows": rows,
        "passed_check_ids": passed,
        "failed_check_ids": failed,
        "unresolved_check_ids": unresolved,
        "not_applicable_check_ids": na,
        "governing_utilization": max(utils) if utils else None,
        "gate_status": gate_status,
        "SP16_MECHANICAL_PASS": mechanical_pass,
        "transition_to_SP554_permitted": mechanical_pass,
        "statement": (
            "SP16 ambient mechanical verification PASSED; fire-specific calculation may proceed."
            if mechanical_pass else
            "SP16 ambient mechanical verification is not fully passed; transition to SP554 is prohibited."
        ),
    }
    outputs = {
        "sp16_mechanical_verification": report,
        "sp16_mechanical_gate_status": gate_status,
        "sp16_mechanical_pass": mechanical_pass,
        "sp16_mechanical_has_failed": bool(failed),
        "sp16_mechanical_has_unresolved": bool(unresolved),
    }
    if report["governing_utilization"] is not None:
        outputs["sp16_mechanical_governing_utilization"] = report["governing_utilization"]
    return outputs


def _aggregate_executor(values: Mapping[str, Any], node: Mapping[str, Any]) -> Mapping[str, Any]:
    return aggregate_sp16_mechanical_verification(values)


def build_sp16_mech6_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative v0.63 execution registry by extending SP16-MECH5 with the strict ambient SP16 mechanical verification aggregator.

    Standard reference:
        СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024; this registry adds orchestration of qualified SP16 evidence and does not introduce a new normative resistance formula.

    Parameters:
        catalog: Frozen interim profile catalogue used by inherited cumulative SP16/FIRE executors. registry: Optional existing execution registry to extend in place.

    Returns:
        ExecutionRegistry containing all v0.62 executors plus the SP16_C_AMBIENT_MECHANICAL_AGGREGATOR producer required by the v0.63 DAG.

    Assumptions:
        The v0.62 canonical actions, axis-specific shear, free-torsion and direct-bimoment mechanics layers are already available and qualified within their declared scopes.

    Sign convention:
        Signed N, Mx, My, Qx, Qy, T and B semantics are inherited unchanged from SP16-MECH1 through MECH5.

    Unit convention:
        Uses the canonical units declared by the active v0.63 DAG; the gate itself consumes dimensionless utilizations and boolean evidence.

    Applicability:
        Cumulative v0.63 guided/runtime execution with a mandatory ambient SP16 gate before FIRE_LOAD_CASE/SP554 routing.

    Limitations:
        Automatic primary-flow execution/binding of every N3-N10 branch is not closed in v0.63; missing evidence remains fail-closed and ENGINEERING_USE_READY stays false.

    Raises:
        Propagates catalogue, inherited registry construction and duplicate-registration errors from the cumulative runtime.

    Examples:
        ``build_sp16_mech6_registry(catalog)`` constructs the registry used by FireUI1Application for the v0.63 DAG.

    Tests:
        tests/test_sp16_mech6_gate.py, tests/test_docstrings.py and cumulative SP16/FIRE regression suites.

    Implementation notes:
        The new aggregator extends rather than replaces frozen earlier engineering executors; transition permissions are encoded in the v0.63 DAG.
    """
    reg = build_sp16_mech5_registry(catalog, registry)
    reg.register("SP16_C_AMBIENT_MECHANICAL_AGGREGATOR", _aggregate_executor)
    return reg
