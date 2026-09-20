# SP16 Annex D.3 interpolation hotfix

- Release: `v0.43.1_fire_ui1_sp16_annex_d3_interpolation_hotfix_r1`
- Parent: `v0.43_fire_ui1_guided_wizard_live_calculation_ledger_frontend_r1`
- Status: **CLOSED for in-domain Table D.3 points**
- Extrapolation: **forbidden**

## Digital-table policy

SP16 Table D.3 remains the normative data source. The current source does not print a separate interpolation equation. The hotfix therefore records interpolation explicitly as an audited digital-table policy rather than pretending it is a printed formula: exact-node preservation; one-dimensional linear interpolation when one coordinate is exact; otherwise bilinear interpolation over the four surrounding printed nodes. The final value is capped by the central-compression coefficient `phi`.

NormCAD is used only as a secondary cross-implementation oracle. The retained case at `lambda_bar=1.61095`, `m_eff=6.67245` gives `phi_e=0.18771`; the implemented policy gives `0.18770813331`.

## 20K1 blocker closure

For the baked walkthrough, `lambda_bar_x=0.856272034981` and `m_eff=5.893855863950` now resolve to `phi_e=0.232121983423` with status `D3_BILINEAR_INTERPOLATED`. The SP16 cold route is complete and passes with governing utilization `0.003270510290`.

The very low user-demo load remains too small for an exact FIRE-D2 critical temperature within the published Appendix-B reduction range. A separate acceptance case preserves the same eccentricity ratio but scales the actions by 58: `N=58 kN`, `Mx=17.4 kN*m`. It yields `Tcr=697.259199 C`, `Rfact=15.169254 min`, and `PASS` against `R15`.

## Boundaries

No Table D.3 extrapolation is permitted. Tables D.4 and D.5 retain their existing exact-node policies. This hotfix does not change `ENGINEERING_USE_READY=False`.
