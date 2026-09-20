# FIRE-D3.1 — SP554 Section 12 full-scope reconciliation

- Release: `v0.40_fire_d31_sp554_section12_full_scope_reconciliation_r1`.
- Parent: `v0.39_fire_d3_sp554_section12_thermal_runtime_r1`.
- Enacted baseline identity: `СП 554.1311500.2026`, effective 2026-09-01.
- `FIRE_D31_SP554_SECTION12_FULL_SCOPE_RECONCILED = True`.
- Formula (12.8) scalar `t_phi` is executable.
- `W>0` embedded-properties route is executable only with explicit confirmation and mandatory 12.6 validation; separate `t_phi` is not added in that mode.
- Literal repeated `t_phi` recurrence remains fail-closed: `FIRE_D31_SP554_LITERAL_T_PHI_RECURRENCE_CLOSED = False`.
- Therefore the older literal-runtime flag remains `FIRE_D3_SP554_SECTION12_FULL_SCOPE_CLOSED = False`; this is intentionally distinct from reconciliation closure.
- Current DAG: `normative_graph/dag_v0.3.43_fire_d31.json`.
- `ENGINEERING_USE_READY = False`.

# Stage N9 fatigue current-SP16 closure

- Release: `v0.35_stage_n9_fatigue_current_sp16_closed_reconstructed_r1`.
- Section 12 guided route, Change-6 exclusion of 12.1.3, Tables 35-36, Annex K K.1 and crane-runway 12.2 routing are current-SP16 rebaselined.
- N1-N9 are frozen cumulative dependencies in the declared closed scopes.

# Implementation status — Stage N1 Material / Strength

Release: `v0.27_stage_n1_material_strength_closed_reconstructed_r1`  
Qualification: `research_grade_stage_n1_closed_current_source_triangulated`  
Engineering-use ready: **no**

## Normative inventory

- Equations: 240 total; 239 implemented; 1 explanatory/no-code; 0 unresolved.
- Tables: 88 total; 67 implemented as code/data; 20 `external_reference_required`; 1 explanatory/no-code; 0 unresolved.
- Procedures: 304 total; 303 implemented; 1 explanatory/no-code; 0 unresolved.

The canonical item-by-item trace remains in `audit_inventory/` and generated audit reports. Phase 0.26 changes selected implementations/routing exposed by external user validation; it does not claim a new complete equation/table census.

## Validation evidence

- User validation corpus: **9 cases**, corpus revision `0009`.
- Dedicated Phase 0.26 remediation regressions: **12/12 PASS** before final packaging.
- Legacy validation/self-check corpus: **1876/1876 PASS**.
- Phase 0.23 independent route layer retained.
- Independent direct function oracles retained: **60/581** engineering functions.
- External vendor-published comparator cases retained: **6/6 PASS across 5 functions**.
- Full independent function validation: **not complete**.
- Full external cross-implementation validation: **not complete**.

## Retained Phase 0.26 corrections

- Table 8 equations (12)-(14) connection factors.
- Clause 7.1.3 low-slenderness `a/b` branch.
- Annex D.2 Type 5 validated coefficient branch.
- Clause 14.1.8 weld-consumable compatibility bound.
- Clause 14.1.9 one-sided-weld positive-acceptance gate changed to fail-closed in the legacy API.
- Table 40 staggered longitudinal minimum layout check.
- Clause 14.2.14 exact integer bolt-count detailing adjustment.
- Equation (44) hole-factor integration in the bending runner.
- Clause 8.4.6 reduced limiting slenderness integration in the lateral-stability exemption route.
- Clause 9.2.9 mixed biaxial route / conditional D.3 invocation.

## Open boundaries

- D.3 arbitrary-point interpolation remains an explicit policy gap.
- 20 Annex Б/В/Г/И tables remain external-reference boundaries; Б.1 and В.3/В.4/В.5 are materialized in Stage N1.
- User validation cases with inconsistent source data remain partial and do not become golden simply because individual scalar equations replay.
- Full Change 6 rebaseline: **false**.
- Global structural analysis, load combinations, geometry recognition/classification, inspection/NDT and professional acceptance remain external where required.


## Stage N1 additions

- Current-source physical constants from Annex Б.1: `rho`, `alpha`, `E`, `G`, `nu`.
- Current-source strength tables В.3, В.4, В.5 with exact interval semantics and fail-closed out-of-range handling.
- Explicit Table 3 `gamma_m` route and clause 4.3.2 `gamma_u = 1.3`.
- High-level `SteelMaterialStrengthResolver` with explicit product-form routing, no hidden `gamma_m` default, and separate table-rounded versus formula-derived resistances.
- Atomic DAG v0.3.30 Stage N1 repairs: tubes/bars route to В.3, restored C355 100<t<=160 band, aliases, full Ryn/Run/Ry/Ru outputs, physical constants, gamma factors and Table-2 derived resistances.
- NormCAD E/G divergence is captured as historical nonconformance; its three material-strength MDBs are statically decoded and row-level crosswalked against the current source. Exact runtime/UI boundary selection is not claimed where old static labels are ambiguous.

## Stage N1 closure gates

- Current-SP source/package exact checks: 7/7 PASS.
- Strength-table row equality: 95/95 PASS.
- Source-derived boundary matrix: 981 probes, including every finite endpoint and `math.nextafter` immediately below/above.
- NormCAD static material-strength crosswalk: 111 current grade/range comparisons; all deviations classified.
- N1 discrepancy register: 19 total, 0 unresolved.
- Stage state: `N1_CLOSED_DECLARED_SCOPE`.

This closure is intentionally narrower than full-SP16 validation; `FULL_CHANGE_6_REBASELINED = False` and `ENGINEERING_USE_READY = False` remain explicit.


# FIRE-D3 — SP554 Section 12 thermal runtime

- Release: `v0.39_fire_d3_sp554_section12_thermal_runtime_r1`.
- Parent: `v0.38_fire_d2_sp554_critical_temperature_runtime_r1`.
- `sp554_fire_thermal_guided` executes unprotected formula/Figure-1 routes, documented protected matrix direct/inverse routes, and dry validated 12.5 FDM.
- FIRE-D2 critical-temperature handoff is materialized in DAG `v0.3.42_fire_d3`.
- Confirmed 12.5/12.6 errata are applied as an explicit auditable overlay.
- 12.6 validation is mandatory for 12.5-generated protected performance results.
- Wet `W>0` protected FDM remains fail-closed; therefore `FIRE_D3_SP554_SECTION12_FULL_SCOPE_CLOSED = False`.
- Connection fire resistance is not part of FIRE-D3.
- `ENGINEERING_USE_READY = False`.
