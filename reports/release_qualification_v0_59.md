# Release qualification — v0.59 SP16-MECH2

Release: `v0.59_sp16_mech2_load_cases_applicability_census_r1`

Parent: `v0.58_sp16_mech1_canonical_axes_mechanical_state_contract_r1`

## Scope closed in this increment

- explicit `AMBIENT_LOAD_CASE` / `FIRE_LOAD_CASE` separation;
- explicit fire-load source choice: inherit ambient or enter a separate fire state;
- independent direct-input bimoment decision for ambient and fire cases;
- machine-readable ambient `SP16_APPLICABILITY_CENSUS`;
- visible but fail-closed ambient `Qy` and `T` branches;
- preservation of the qualified downstream SP554 fire scalar contract.

## Scope intentionally still open

- axis-specific `Qy` mechanics: SP16-MECH3;
- torsion `T` runtime: SP16-MECH4;
- automatic restrained-torsion / bimoment derivation: not in current agreed scope;
- final all-applicable-check aggregator and `SP16_MECHANICAL_PASS`: SP16-MECH6.

## Executed qualification groups

| Group | Result |
|---|---:|
| SP16-MECH2 new tests | 7 / 7 PASS |
| Cumulative UI/FIRE-UI16…24 affected routes | 117 / 117 PASS |
| Base steel calculation tests | 413 / 413 PASS |
| Stage N1–N5 workflows/DAG | 152 / 152 PASS |
| Stage N6–N8 workflows/DAG | 99 / 99 PASS |
| Stage N9–N10 workflows/DAG | 47 / 47 PASS |
| FIRE-D1/D2 + applicability | 51 / 51 PASS |
| FIRE-D3.1/D3/D4 + interpolation hotfix | 53 / 53 PASS |
| Phase 0.23 provenance/rebaseline | 5 / 5 PASS |
| Release API hardening | 5 / 5 PASS |
| Phase 0.25 validation | 6 / 6 PASS |
| Public API docstring audit | PASS |

A single monolithic historical pytest invocation is not claimed as a release gate because some large historical/oracle batches exceed the execution window when combined. The functional groups above were executed separately and passed.
