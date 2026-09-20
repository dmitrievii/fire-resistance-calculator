# FIRE-D2 — governing critical-temperature reconciliation

## Production rule

FIRE-D2 does **not** compare `gamma_T` and `gamma_E` numerically to decide the governing fire temperature. Each applicable coefficient is inverted on its own Appendix-B temperature curve and the earliest critical temperature governs.

For multiple Section-10 or Section-11 strength checks the production rule is equivalent to:

`gamma_T,governing = max(applicable required gamma_T)`

because the published `gamma_T(T)` curve decreases with temperature.

## Locked-draft discrepancies

- **8.6** — the locked draft says to use the smallest of `gamma_T` and `gamma_E`. This is not a valid cross-curve governing rule. The predecessor ARSS method explicitly obtains two temperatures and takes the smaller temperature.
- **10.3** — the locked draft says the smallest Section-10 `gamma_T`; production uses the largest required coefficient, equivalently the smallest critical temperature.
- **11.9** — same issue for Section 11.

The source literals remain in the DAG as provenance/diagnostic evidence; FIRE-D2 does not execute them as production governing logic.

## Numerical discriminator

For the packaged ordinary-steel central-compression case:

- `gamma_T = 0.5208333333` -> `t_cr,T = 560.648148 C`
- `gamma_E = 0.6999768587` -> `t_cr,E = 525.019284 C`

Therefore the member loses capacity first at **525.019284 C**, controlled by the modulus curve. A literal `min(gamma_T,gamma_E)` decision would incorrectly select the later 560.648148 C limit.

## Appendix-B digital policy

Exact Table-B.1 knots are preserved. Linear interpolation is used only as a digital interpretation of the plotted B.1-B.8 curve segments. Extrapolation is forbidden. The unit-coefficient plateau maps `gamma=1` to its upper end at 250 C.
