# Release qualification — v0.67 FIRE-BRIDGE2

- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`
- Package: `0.67.0`
- Parent: `v0.66_sp16_mech9_remaining_ambient_applicability_closure_r1`
- Active DAG: `normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json`
- Research-grade only: `ENGINEERING_USE_READY=False`

## Scope closed

FIRE-BRIDGE2 inserts a typed handoff after the strict ambient `SP16_MECHANICAL_PASS` production gate. Existing explicit SP554 Sections 9–11 routes remain available for currently supported fire states even when an internal pointwise `sigma_n` has not been recovered. A new internal clause-8.7 option derives governing `|sigma_n|` from the package's complete same-point FIRE normal-stress state when that state is available. Direct `B` may participate in this normal-stress handoff when upstream MECH5 recovery is complete.

Nonzero `Qy` and arbitrary torsion `T` remain fail-closed at the SP554 fire-resistance boundary. Clause 8.7 is not treated as a universal replacement for missing shear/torsion checks. No `Qy→Qx`, resultant-action `Q`, or `T→B` substitution is performed.

## Active graph

- Raw DAG SHA-256: `9026346f32219084eadd0d2f4352322ec41f6a8c5e38ae674c4086d8da882312`
- 922 quantities / 39 datasets / 734 nodes / 1246 edges
- UI contract: 176 interactive / 54 result nodes; selector audit PASS; zero empty option sets
- Deterministic DAG rebuild: PASS — byte-identical

## Source-tree evidence

- MECH1–9 + FIRE-BRIDGE2 + affected FIRE-UI: 171/171 PASS
- N1–N10 workflows: 243/243 PASS
- FIRE-D1…D4 runtime: 68/68 PASS
- Phase 0.23 + 0.24: 10/10 PASS
- Phase 0.25: 6/6 PASS using separately completed tests after the combined batch exceeded the execution window
- docstrings + schemas + UI0 + final audit: 68/68 PASS

## Release constraints

`ENGINEERING_USE_READY=False`. Nonzero fire `Qy/T` remains blocked until a future fire-specific normative closure. The internal clause-8.7 route is available only when complete pointwise normal-stress recovery exists; explicit Sections 9–11 routes do not depend on that diagnostic state.
