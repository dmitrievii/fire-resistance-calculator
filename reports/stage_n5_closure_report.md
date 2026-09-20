# Stage N5 — Beam-Columns / Current SP16 Closure

- Release: `v0.31_stage_n5_beam_columns_current_sp16_closed_reconstructed_r1`
- Verdict: **STAGE_N5_BEAM_COLUMNS_CURRENT_SP16_CLOSED**
- Authoritative SP16 SHA-256: `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`
- DAG: `dag_v0.3.34_stage_n5.json` / `c60c9baaea65a577537dc4e3fb4e98ee0e85c4efa8048c0e351f07a3fe180765`
- Stage N5 focused tests: **20/20 PASS**
- Cumulative pytest excluding release-manifest gate: **685/685 PASS**
- Full pytest including release-manifest gate: **686/686 PASS**
- Release-manifest gate: **1/1 PASS**
- `main.py` release audit: **PASS**
- Generated current-release outputs: **25/25**
- N5 discrepancies: **7 total; 0 open package/DAG defects; 0 runtime unresolved**

## Closed scope

The declared Section 9 guided route now composes current N1 material and N2 profile hydration with frozen N3/N4 dependencies, routes equations (105)/(106), derives Section 9.2 slenderness/eccentricity quantities and Annex D.2 coefficients, retains the clause 9.2.9 mixed trigger, and uses Annex D.3 only at exact printed nodes unless an externally sourced coefficient is explicitly attributed. Box and built-up beam-columns remain routed to the existing detailed actions.

## NormCAD reconciliation

The retained 15K4 report remains historical secondary evidence. Its `Ryn/Ry/E/G = 255/250/210000/78500 MPa`, `lefy=2.95 mm`, old `It=385333 mm4`, and interpolated `phi_e=0.18771` do not override current-SP16 production inputs or create a hidden D.3 interpolation rule. The current resolver produces `245/240/206000/79000 MPa` and the current Annex-D torsional policy produces `It=497080 mm4`.

## Explicitly not claimed

`ENGINEERING_USE_READY=False`. Full package-wide Change-6 rebaseline, original/effective GOST/GOST R audit of the interim profile catalog, arbitrary-point D.3 interpolation as a normative rule, and final external engineering certification are not claimed.


## HOTFIX v0.43.1 overlay

The historical Stage N5 exact-grid boundary for Annex D.3 is superseded in the current cumulative runtime by the audited in-domain bilinear digital-table interpolation policy. Exact printed nodes are preserved, extrapolation is forbidden, and the result remains capped by central-compression phi.
