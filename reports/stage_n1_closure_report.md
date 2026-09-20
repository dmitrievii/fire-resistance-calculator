# Stage N1 closure report

**Status:** `N1_CLOSED_DECLARED_SCOPE`  
**Release:** `v0.27_stage_n1_material_strength_closed_reconstructed_r1`  
**Engineering-use ready:** **no**

## Authority

The locked current СП 16 source is the sole normative authority. NormCAD, the user package and the atomic DAG are independent computational representations used for cross-validation.

## Closure gates

- Current-SP source/package checks: **7/7 PASS_EXACT**.
- Annex В.3/В.4/В.5 source rows: **95/95 PASS_EXACT**.
- Source-derived boundary matrix: **981 probes** = 866 expected resolutions + 115 required fail-closed outcomes.
- Focused Stage N1 regression: **43/43 PASS**.
- Full package regression before manifest generation: **579/579 PASS**.
- NormCAD static crosswalk: **111** current grade/range comparisons.
- Discrepancies: **19 registered, 0 unresolved**.
- Cumulative `main.py` audit: **PASS**; equations 239, tables 67, procedures 303; legacy validation 1876/1876 PASS.

## NormCAD result

NormCAD is retained as historical evidence. Its decoded material databases contain 62 sheet-strength rows, 72 shaped-strength rows and 6 tube-strength rows. The current-SP crosswalk contains 50 exact static matches, 23 value mismatches, 18 missing thickness routes, 15 boundary-label differences/uncertainties and 5 missing current grades. No NormCAD divergence is allowed to override current СП.

## Scope boundary

This report closes only Stage N1 Material / Strength. Full package-wide Change 6 reconciliation and later N-stages remain open. `ENGINEERING_USE_READY=False`.
