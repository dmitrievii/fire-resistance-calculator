# Release qualification — v0.62 SP16-MECH5

- Release: `v0.62_sp16_mech5_direct_bimoment_pointwise_recovery_r1`
- Package: `0.62.0`
- Parent: `v0.61_sp16_mech4_free_torsion_pointwise_recovery_r1`
- Active DAG SHA-256: `a4a882728a41361a211e3d3b9e6963f72d84061eb17363edda20af81b1a99407`
- DAG: 841 quantities / 39 datasets / 713 nodes / 1208 edges
- UI: 163 interactive / 52 result nodes

## Closed scope

The agreed direct-input bimoment policy is preserved. For `B != 0`, doubly-symmetric I-sections now obtain a deterministic same-point sectorial field `omega(P)`, derived `I_omega`, and `sigma_B=B*omega/I_omega`; this is merged with the existing N/Mx/My/Qx/Qy/T pointwise state. `B=0` is complete for every already-supported MECH4 geometry.

## Deliberately open

No restrained-torsion solver and no automatic `B(T)` derivation are introduced. Nonzero-B channel/tee/RHS/arbitrary warping geometry remains fail-closed. The aggregate `SP16_MECHANICAL_PASS` gate and typed SP554 complex-state handoff for Qy/T remain open.

## Source-tree qualification

| Group | Result |
|---|---:|
| MECH1-5 + affected FIRE-UI | 146/146 PASS |
| SP16 core mechanics A | 180/180 PASS |
| SP16 core mechanics B | 244/244 PASS |
| Stage N1-N10 workflows | 243/243 PASS |
| FIRE-D1..D4 runtime | 68/68 PASS |
| Phase 0.23 | 5/5 PASS |
| Phase 0.24 | 6/6 PASS |
| Phase 0.25 + docstrings + schemas + FIRE-UI0 | 71/71 PASS |

Active-DAG deterministic rebuild and fresh-extraction gates are performed during packaging. `ENGINEERING_USE_READY=False` remains unchanged.
