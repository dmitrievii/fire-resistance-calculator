# SP16-MECH1 — Canonical Axes + Mechanical State Contract (v0.58)

## Scope

This stage changes the guided mechanical-action contract from the historical local member notation
`N, My, Mz, Qy, Qz, T(=Mx)` to the SP16-oriented notation
`N, Mx, My, Qx, Qy, T`, with `x-x` and `y-y` reserved for the principal axes of the cross-section and `s` used for the member longitudinal axis.

The canonical internal state is extended by a conditional bimoment `B`.

## v0.57 → v0.58 migration

The parent FIRE-UI local convention is migrated without sign reversal:

- `load_My_local → M_x`
- `load_Mz_local → M_y`
- `load_Qz_local → Q_x`
- `load_Qy_local → Q_y`
- `T_torsion → T_torsion`
- `N_force → N_force`

The mapping is implemented by `migrate_v057_actions_to_sp16_mech1()` and is also recorded in `mechanical_action_state`.

## Bimoment policy for v0.58

`B` is not shown as a permanent seventh field in the general load editor.
After the main actions are entered, the guided flow asks whether bimoment must be considered.

- answer **No** → an explicit producer records `B = 0`;
- answer **Yes** → the user enters signed `B` directly in a dedicated screen (`kN·m²` in the browser, converted to canonical `N·mm²`).

v0.58 does **not** infer `B` from torsion `T`, warping restraints, or member boundary conditions. A restrained-torsion solver is deliberately deferred.

## Compatibility alias

The previously qualified scalar web-shear mechanics consume `Q_shear`. In SP16-MECH1 this is retained only as an explicit compatibility alias:

`Q_shear = Q_x`

`Q_y` is never combined into or substituted for `Q_x`.

## Fail-closed scope

v0.58 canonicalizes `Qy` and `T`, but their general production runtimes remain outside this release:

- `Q_y != 0` → explicit deferred/fail-closed branch;
- `T != 0` → explicit deferred/fail-closed branch;
- no `Qy → Qx` substitution;
- no `T → B` substitution.

The full ambient SP16 mechanical gate is the next architectural layer and is not claimed closed by this release.
