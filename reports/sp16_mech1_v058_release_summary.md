# v0.58 / SP16-MECH1 release summary

- Canonical actions: `N, Mx, My, Qx, Qy, T`; longitudinal member axis: `s`.
- Explicit v0.57 migration: `My_old→Mx`, `Mz_old→My`, `Qz_old→Qx`, `Qy_old→Qy`, signs preserved.
- `B` is conditional: direct signed input after a yes/no question; explicit `B=0` otherwise.
- `Q_shear` remains only as compatibility alias `Q_shear = Qx`.
- `Qy` and `T` remain fail-closed; no silent substitution.
- Full ambient SP16 mechanical gate is not yet claimed closed.
