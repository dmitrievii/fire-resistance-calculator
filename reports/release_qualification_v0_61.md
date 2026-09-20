# Release qualification — v0.61 SP16-MECH4

- Release: `v0.61_sp16_mech4_free_torsion_pointwise_recovery_r1`
- Package: `0.61.0`
- Parent: `v0.60_sp16_mech3_axis_shear_pointwise_recovery_r1`
- Active DAG SHA-256: `c30aca4b5cd658d0eb9635d30062cfdb776007ee3c83a8c50e11ca5af96c10d1`
- DAG: 835 quantities / 39 datasets / 711 nodes / 1206 edges
- UI: 163 interactive / 52 result nodes

## Closed scope

Signed free torsion `T` is recovered as a distinct Saint-Venant mechanics field for supported I/tee/channel/RHS-SHS templates and merged point-by-point with the MECH3 N/M/Q state. `B` remains a direct conditional signed input and is never derived from `T`.

## Deliberately open

Restrained torsion, automatic `B`, warping normal stress from `B`, the aggregate `SP16_MECHANICAL_PASS` gate, and the SP554 complex-state handoff for nonzero Qy/T remain fail-closed/deferred.

## Source-tree qualification

| Group | Result |
|---|---:|
| MECH1-4 + affected UI | 64/64 PASS |
| SP16 core mechanics A | 229/229 PASS |
| SP16 core mechanics B | 320/320 PASS |
| FIRE-D1..D4 runtime | 68/68 PASS |
| FIRE-UI16..24 | 80/80 PASS |
| Phase 0.23 | 5/5 PASS |
| Phase 0.24 | 5/5 PASS |
| Phase 0.25 | 6/6 PASS |
| docstrings + schemas + FIRE-UI0 | 65/65 PASS |

Historical stage `*_dag.py` batches are **not claimed PASS** here because those batch processes do not terminate inside the execution window despite emitting passing progress. The active v0.61 DAG is instead subject to deterministic byte-identical rebuild and fresh-extraction gates during packaging.
