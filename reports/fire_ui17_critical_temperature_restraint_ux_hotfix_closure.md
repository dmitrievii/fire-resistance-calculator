# FIRE-UI1.7 — Critical Temperature / Restraint UX Hotfix Closure

Release: `v0.50_fire_ui17_critical_temperature_restraint_ux_hotfix_r1`  
Parent: `v0.49_fire_ui16_signed_load_verification_plan_parallel_dag_r1`

## Closed defects

1. **Independent Appendix-B inversion** — `gamma_T` and `gamma_e` are inverted on their own published curves before governing-temperature selection.
2. **Ambient overload** — any required coefficient above 1.0 is classified as `AMBIENT_CAPACITY_EXCEEDED`; no extrapolation is attempted.
3. **Published-range lower bound** — coefficient below the published minimum returns `Tcr > Tmax`, preserving a bounded normative result without extrapolation.
4. **Legacy single-domain gate removed from guided production** — source-literal `min(gamma_T,gamma_e)` and its single inverse-domain gate remain diagnostic/audit-only.
5. **Table 30 UX** — common restraint schemes are named and show `mu`; S5–S8 explicitly retain the normative load-diagram dependency instead of being guessed from support conditions.
6. **Table 7 UX** — a/b/c cards show `alpha/beta`, a schematic redraw, calculation-plane guidance, and the rolled-I h>500 mm note.

## Governing-temperature policy

For strength-only routes, invert `gamma_T` only. For compression routes, invert both `gamma_T` and `gamma_e` independently. An ambient-capacity failure governs immediately. Otherwise the lowest exact temperature governs. If no exact temperature exists because every applicable coefficient lies below the published curve minimum, return the minimum published-temperature lower bound relationally (`Tcr > bound`) and fail closed against any need for an exact value.

`ENGINEERING_USE_READY` remains `False`; this release is research-grade and the previously deferred Qy/torsion routes remain deferred.
