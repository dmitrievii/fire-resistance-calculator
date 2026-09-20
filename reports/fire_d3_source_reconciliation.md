# FIRE-D3 source reconciliation — SP554 Section 12

Release: `v0.39_fire_d3_sp554_section12_thermal_runtime_r1`

## Source lock

- SP554 locked package source SHA-256: `86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3`.
- SP16 current source SHA-256: `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`.
- Parent release: `v0.38_fire_d2_sp554_critical_temperature_runtime_r1`.
- FIRE-D1/FIRE-D2 mechanical producers are frozen and are consumed only through the critical-temperature handoff.

## Executable Section 12 routes

1. `UNPROTECTED_STEP_12_2` — formulas 12.1–12.4, standard fire curve, explicit stepping to the FIRE-D2 critical temperature.
2. `UNPROTECTED_FIGURE1_12_2` — frozen reconstructed Figure 1 curves for reduced thickness 3/5/10/15/20 mm, with linear interpolation only inside the printed domain.
3. `PROTECTED_MATRIX_12_10` — documented 12.7–12.9 nomogram/matrix data, direct fire-resistance lookup and inverse minimum-protection-thickness task.
4. `PROTECTED_FDM_12_5` — dry (`W=0`) one-dimensional protected-steel finite-difference runtime, with mandatory clause 12.6 validation.

## Confirmed draft errata overlay

The source literals are preserved as provenance and are **not** silently rewritten. Production applies these explicit corrections in the 12.5 FDM route:

- Formula (12.5): source-literal moisture/source term `+ t_n - t_phi`; production term `+ t_0 - t_phi`.
- Formula (12.6): source-literal heat-capacity denominator uses `C + D*t_0`; production denominator uses the local-node temperature `C + D*t_n`.

These corrections are emitted in runtime results as an `errata_overlay` so a calculation report can identify both the printed source and the executed expression.

## Conservative policies

- No extrapolation of Figure 1 outside reduced thickness 3–20 mm.
- No interpolation between critical-temperature matrix levels is invented. A 12.10 matrix route requires an exact documented critical-temperature level on the 50 °C grid.
- No protection-thickness extrapolation is permitted.
- Clause 12.4 greater-reduced-thickness extension is implemented only when the dataset explicitly authorizes it; the maximum documented row is carried forward rather than slope-extrapolated.
- Product matrices are not smoothed. Non-monotonic experimental values are preserved, and inverse thickness search uses the first qualifying piecewise-linear crossing.
- Formula (12.8) defines a fictitious moisture temperature, but the locked text does not unambiguously define the phase-change activation/energy bookkeeping needed for an executable wet (`W>0`) explicit scheme. FIRE-D3 r1 therefore fails closed for `W>0` rather than inventing a numerical rule.

## Control handoff

Frozen FIRE-D2 critical temperature:

`Tcr = 525.0192844353662 °C`

FIRE-D3 unprotected calculation at `delta_pr = 10 mm`, default Section-12 thermal properties and `dt = 0.1 min`:

`R_actual = 14.326394173167056 min`

Crossing bracket: `14.3–14.4 min`.
