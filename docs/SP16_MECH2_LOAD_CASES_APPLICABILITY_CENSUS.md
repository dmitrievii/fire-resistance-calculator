# SP16-MECH2 — Ambient / Fire Load Cases + Applicability Census

Release: `v0.59_sp16_mech2_load_cases_applicability_census_r1`

## Purpose

SP16-MECH2 separates the normal-temperature mechanical design action state from the accidental fire-design action state. The program no longer relies on one shared unnamed action vector.

Canonical section actions remain:

`N, Mx, My, Qx, Qy, T`, with conditional direct `B`.

- `x-x`, `y-y` are the SP16 principal axes of the section.
- `s` is the member longitudinal axis.
- `T` is torsion about `s` and is not `Mx` or `B`.
- `B` remains a direct conditional input in the current scope; restrained-torsion derivation is not implemented.

## Load-case contract

Two typed states now exist:

1. `AMBIENT_LOAD_CASE` — ordinary design actions used by the SP16 mechanical layer.
2. `FIRE_LOAD_CASE` — accidental/special fire-design actions consumed by downstream SP554 mechanics.

After the ambient state is authored, the user must explicitly select one of two fire modes:

- `same_as_ambient` — value-preserving explicit copy;
- `separate` — enter a separate signed fire action state.

There is no silent ambient-to-fire copy.

## SP16 applicability census

The ambient state produces `sp16_applicability_census`. It enumerates action-driven check families and retains checks that depend on additional member/design context as explicit conditional items rather than omitting them.

Action-driven examples include axial strength/stability, bending, biaxial bending, Qx/Qy shear, N+M interaction, M+Q interaction, torsion and direct bimoment participation.

Context-driven examples include beam LTB, local web/flange stability, fatigue and brittle-fracture applicability.

The census is not yet the final SP16 PASS gate. `full_ambient_gate_closed = false` remains explicit.

## Fail-closed scope

`Qy` and `T` are now visible in the load editor so that applicability is not hidden. If either is non-zero in the ambient case, the run terminates before the fire stage:

- `Qy != 0` -> `deferred_sp16_mech3`;
- `T != 0` -> `deferred_sp16_mech4`.

No `Qy -> Qx` and no `T -> B` substitution is allowed.
