# SP16-MECH6 v0.63 Release Qualification

- Release: `v0.63_sp16_mech6_mechanical_pass_gate_r1`
- Package: `0.63.0`
- Parent: `v0.62_sp16_mech5_direct_bimoment_pointwise_recovery_r1`
- Active DAG: `normative_graph/dag_v0.3.66_sp16_mech6_mechanical_pass_gate.json`
- Active DAG SHA-256: `fb916afc7c30c136c0be44f1ce618aaf57049767608ae727a32c0ffc1760685b`
- DAG counts: **848 quantities / 39 datasets / 717 nodes / 1212 edges**
- UI contract: **164 interactive / 54 result nodes**

## Closed scope

- Strict evidence-based ambient `SP16_MECHANICAL_PASS` gate.
- Explicit `PASS / FAIL / N.A. / DEFERRED / CONTEXT_UNRESOLVED` ledger.
- Any explicit failure blocks SP554.
- Any unresolved applicable/context-driven check yields `INCOMPLETE_FAIL_CLOSED` and blocks SP554.
- Stress recovery alone is never treated as normative PASS.
- Existing N3-N10 evidence is consumed when present.

## Deliberately open

- Automatic primary-flow execution/binding of every N3-N10 workflow is not closed.
- Therefore many ordinary guided ambient cases intentionally terminate at `SP16_R_AMBIENT_MECHANICAL_INCOMPLETE` until the following binding stage.
- SP554 complex-state handoff for fire `Qy/T` remains fail-closed.
- `ENGINEERING_USE_READY = False`.

## Source-tree qualification

- SP16-MECH1..6: **39/39 PASS**
- FIRE-UI frontend + UI16..24: **104/104 PASS**
- SP16 core mechanics A: **121/121 PASS**
- SP16 core mechanics B: **299/299 PASS**
- N1-N10 workflows: **243/243 PASS**
- FIRE-D1..D4 + SP554 routing runtime: **76/76 PASS**
- Phase 0.23: **5/5 PASS**
- Phase 0.24: **5/5 PASS**
- Phase 0.25 + docstrings + schemas + UI0: **71/71 PASS**

Fresh-extraction and deterministic ZIP gates are added during final packaging.
