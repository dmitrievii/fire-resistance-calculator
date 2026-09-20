# Release qualification — v0.65 SP16-MECH8

- Release: `v0.65_sp16_mech8_mq_interaction_torsion_scope_r1`
- Package: `0.65.0`
- Parent: `v0.64_sp16_mech7_primary_ambient_workflow_binding_r1`
- Active DAG: `normative_graph/dag_v0.3.68_sp16_mech8_mq_torsion_scope.json`
- Research-grade only: `ENGINEERING_USE_READY=False`

## Scope closed

SP16-MECH8 adds normative evidence for supported bending-plus-shear states without weakening the strict ambient SP16 gate. Class-1 closure is limited to the explicitly classified I-beam `Mx+Qx` route of §8.2.1 Eq.(44), including same-point signed stresses and Eq.(45) shear amplification where applicable. Class-2 closure uses §8.2.3 Eqs.(50)-(53), Eq.(52), Annex E Table E.1 and Table 10a for qualified I/box routes.

Free-torsion `T→tau_T(P)` mechanics from MECH4 remains available, but this release does not invent a universal arbitrary-`T` SP16 resistance equation. `torsion_T` remains fail-closed unless a clause-specific normative route is available. Class-3 M+Q, unresolved transverse/local web stress, unsupported combined interaction routes, remaining detailed N3-N10 bindings and the complex-state SP554 handoff remain fail-closed.

## Active graph

- Raw DAG SHA-256: `53e49875026507632472568dcea2d1feafbeded5cae3e8dd2068d7e7d99e9dd0`
- 866 quantities / 39 datasets / 725 nodes / 1224 edges
- UI contract: 170 interactive / 54 result nodes; selector audit PASS; zero empty option sets
- Deterministic DAG rebuild: PASS — byte-identical

## Source-tree evidence

- MECH1-MECH8 + affected FIRE-UI: 156/156 PASS (155 inherited/affected + 1 corrected contract in final rerun; MECH8 dedicated 7/7 included)
- SP16 core A: 155/155 PASS
- SP16 core B: 237/237 PASS
- N1-N10 workflows: 243/243 PASS
- FIRE-D1...D4 / SP554 runtime: 76/76 PASS
- Phase 0.23: 5/5 PASS
- Phase 0.24: 5/5 PASS
- Phase 0.25: 6/6 PASS
- docstrings + schemas + UI0 + final audit: 68/68 PASS

## Release constraints

`ENGINEERING_USE_READY=False`. The release is suitable for cumulative research/validation development. Unsupported applicability is represented as `DEFERRED`/fail-closed rather than assumed PASS.
