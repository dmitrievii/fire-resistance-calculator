# FIRE-UI1.8 — FIRE-D2 → FIRE-D3 Thermal Handoff Hotfix Closure

Release: `v0.51_fire_ui18_fire_d2_to_d3_handoff_hotfix_r1`  
Package: `0.51.0`  
Parent: `v0.50_fire_ui17_critical_temperature_restraint_ux_hotfix_r1`

## Closed defect

A valid exact FIRE-D2 critical temperature was previously presented as a terminal guided result, so the session did not enter SP554 Section 12 even though the frozen DAG already contained a FIRE-D3 handoff.

FIRE-UI1.8 closes the defect at three layers:

1. `SP554_FIRE_D2_R_CRITICAL_TEMPERATURE` is a non-terminal **stage result** when its status is `COMPLETE`.
2. `FIRE_D3_E_001` is an explicit conditional handoff to `SP554_FIRE_D3_C_D2_TCR_HANDOFF` only for an exact `COMPLETE` result.
3. The FIRE-D3 handoff has a dedicated two-output executor and an explicit navigation edge to `SP554_I_EXPOSURE` (`Схема обогрева`).

The parallel scheduler preserves the mechanical-to-thermal barrier: an exact thermal handoff is queued behind any still-active mechanical branch.

## Fail-closed cases retained

- `AMBIENT_CAPACITY_EXCEEDED`: no Section-12 handoff.
- `INCOMPLETE_FAIL_CLOSED`: lower-bound-only `Tcr > Tmax` remains relational; no fabricated exact thermal target.
- No Appendix-B extrapolation is introduced.

## User regression

The reported exact result `tcr = 638.011628 °C` is seeded as the FIRE-D2 stage result and qualified to continue to `SP554_I_EXPOSURE` with:

- `critical_temperature_c = 638.011628 °C`;
- `fire_d3_critical_temperature_handoff_c = 638.011628 °C`;
- `pending_node_ids = []`;
- `branch_failures = []`.

## Frozen DAG

`normative_graph/dag_v0.3.54_fire_ui18_fire_d2_to_d3_handoff_hotfix.json`

Counts: 777 quantities / 38 datasets / 666 nodes / 1136 edges.
