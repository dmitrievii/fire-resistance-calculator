# FIRE-BRIDGE2 — Qualified SP16 Complex-State Handoff

## Purpose

FIRE-BRIDGE2 is the typed boundary between the completed normal-temperature SP16 verification layer and SP554 fire mechanics. It does not change the upstream canonical action set `N, Mx, My, Qx, Qy, T, B` and does not re-run the ambient SP16 verification.

## Rules

1. `SP16_MECHANICAL_PASS = true` is mandatory before the bridge can execute.
2. The complete FIRE pointwise normal-stress state must be available from MECH5.
3. Existing explicit SP554 Sections 9–11 routes are preserved for supported states.
4. SP554 §8.7 can use the governing absolute normal stress from the qualified internal pointwise state.
5. §8.7 is **not** a substitute for missing shear/torsion fire checks.
6. Therefore `Qy != 0` and/or `T != 0` remain fail-closed in v0.67.
7. Direct `B` is allowed in the normal-stress handoff only where upstream sectorial recovery is complete.

## Route statuses

- `FULLY_SUPPORTED`: current active actions are within the qualified SP554 handoff scope.
- `FAIL_CLOSED_QY`: Qy mechanics exists, but the fire-specific Qy resistance route is not qualified.
- `FAIL_CLOSED_T`: free-torsion mechanics exists, but no universal arbitrary-T SP554 fire route is qualified.
- `FAIL_CLOSED_QY_T`: both unsupported fire-action classes are active.

The bridge still reports the governing normal-stress diagnostic in fail-closed cases, but does not convert that diagnostic into a complete fire-resistance result.
