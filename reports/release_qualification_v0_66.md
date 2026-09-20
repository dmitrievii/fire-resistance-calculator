# Release qualification — v0.66 SP16-MECH9

- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`
- Package: `0.66.0`
- Parent: `v0.65_sp16_mech8_mq_interaction_torsion_scope_r1`
- Active DAG: `normative_graph/dag_v0.3.69_sp16_mech9_remaining_ambient_closure.json`
- Research-grade only: `ENGINEERING_USE_READY=False`

## Scope closed

SP16-MECH9 closes three bounded ambient gaps without weakening the strict SP16 gate. The class-3 one-plane `Mx+Qx` route is available only after explicit confirmation of the §8.2.7 prerequisite chain and then uses the existing qualified Eq.(50)/(52) + Annex-E machinery. Ordinary fatigue §12.1.2 is executed through Stage N9. Section 13 is executed through Stage N10, including the explicit lamellar/Z-quality branch when required.

Crane-runway fatigue §12.2, low-cycle `<1e5` external-method cases, class-3 biaxial or `N+M+Q` states, unsupported detailed local-stability geometries and universal arbitrary-`T` resistance remain fail-closed. The nonzero-fire-`Qy/T` SP554 complex-state handoff also remains deferred to FIRE-BRIDGE2.

## Active graph

- Raw DAG SHA-256: `34e47facdcd3a6bd362e82e2f8c39d1c70bffb1b38ff4784ee630099224f906e`
- 918 quantities / 39 datasets / 732 nodes / 1242 edges
- UI contract: 176 interactive / 54 result nodes; selector audit PASS; zero empty option sets
- Deterministic DAG rebuild: PASS — byte-identical

## Source-tree evidence

- SP16-MECH1…MECH9: 60/60 PASS
- affected FIRE-UI: 104/104 PASS
- SP16 core A: 170/170 PASS
- SP16 core B + validation: 294/294 PASS
- N1-N10 workflows: 243/243 PASS
- FIRE-D1…D4 runtime: 68/68 PASS
- adjacent DAG/applicability hotfixes: 11/11 PASS
- Phase 0.23: 5/5 PASS
- Phase 0.24: 5/5 PASS
- Phase 0.25: 6/6 PASS
- docstrings: 1/1 PASS
- schemas: 53/53 PASS
- final audit: 3/3 PASS

## Release constraints

`ENGINEERING_USE_READY=False`. Unsupported applicability is represented as `DEFERRED` / fail-closed rather than assumed PASS.
