# Release qualification — v0.60 SP16-MECH3

Release: `v0.60_sp16_mech3_axis_shear_pointwise_recovery_r1`  
Parent: `v0.59_sp16_mech2_load_cases_applicability_census_r1`

## Closed

- axis-specific signed `Qx` / `Qy` mechanics for supported geometry;
- SP16 8.2.3 I/box component checks;
- same-point `sigma`, `tau_x`, `tau_y` mechanics recovery;
- ambient Qy census closure for supported geometry;
- fire Qy mechanical characterization;
- fail-closed legacy SP554 handoff for non-zero fire Qy until FIRE-BRIDGE2.

## Still open

- torsion `T`: SP16-MECH4;
- typed fire Qy handoff into SP554: FIRE-BRIDGE2;
- final `SP16_MECHANICAL_PASS`: SP16-MECH6.

## Qualification

| Group | Result |
|---|---:|
| MECH1/2/3 + affected UI | 87 / 87 PASS |
| FIRE-UI16–19 | 35 / 35 PASS |
| Base steel | 428 / 428 PASS |
| N1–N5 | 152 / 152 PASS |
| N6–N8 | 99 / 99 PASS |
| N9–N10 | 47 / 47 PASS |
| FIRE-D1/D2 | 51 / 51 PASS |
| FIRE-D3.1/D3/D4 | 53 / 53 PASS |
| Phase 0.23 | 5 / 5 PASS |
| API hardening | 5 / 5 PASS |
| Phase 0.25 | 6 / 6 PASS |
| Schemas/UI0 | 64 / 64 PASS |
| Public API docstring audit | PASS |

A monolithic historical pytest run is not claimed; large historical/oracle groups are qualified separately.
