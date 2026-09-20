# Stage N9 — Reconciliation Register

- Release: `v0.35_stage_n9_fatigue_current_sp16_closed_reconstructed_r1`
- Current SP16 is primary; NormCAD is secondary evidence only.

## N9-R01 — Legacy Section-12 source metadata
- Classification: **CURRENT_SP16_REBASELINE_CLOSED**
- Resolution: Section-12 scalar producers, Tables 35-36 and Annex K provenance are rebaselined from Amendments 1-5 wording to the locked current source with Changes 1-6 through 09.12.2024.

## N9-R02 — Clause 12.1.3 after Change No. 6
- Classification: **CURRENT_NORMATIVE_DELETION_REMEDIATED**
- Resolution: 12.1.3 is excluded from 10.01.2025 by Change No. 6. The compatibility API name is retained, but `n<1e5` no longer executes a fabricated current-SP16 low-cycle method and instead returns an explicit fail-closed external-method boundary.

## N9-R03 — Legacy all-routes fatigue wrapper
- Classification: **APPLICABILITY_ORCHESTRATION_CLOSED**
- Resolution: `fatigue_guided` selects ordinary fatigue 12.1.2, crane runway 12.2, or the `n<1e5` external low-cycle boundary; incompatible routes are not evaluated in parallel.

## N9-R04 — Table 35 fatigue resistance
- Classification: **CURRENT_TABLE_EXACT_BIN_POLICY_CLOSED**
- Resolution: Groups 1-2 use the printed `Run` strength bins through 675 N/mm² and groups 3-8 use the printed all-steel constants. No interpolation or extrapolation is invented.

## N9-R05 — Table 36 stress-asymmetry factor
- Classification: **SIGNED_PIECEWISE_POLICY_CLOSED**
- Resolution: `rho=sigma_min/sigma_max` retains the normative sign and the tension/compression piecewise Table-36 expressions are selected explicitly; zero governing stress is rejected rather than assigning a synthetic rho.

## N9-R06 — Clause 12.2 crane-runway cycle factor
- Classification: **CRANE_OVERRIDE_ROUTE_CLOSED**
- Resolution: the 12.2 `alpha=0.77` route for 8K and metallurgical 7K cranes and `alpha=1.1` otherwise is kept distinct from equations (171)-(172).

## N9-R07 — Equation (173) upper web-zone fatigue
- Classification: **STRESS_PROVENANCE_GATE_CLOSED**
- Resolution: equation (173) is available only for the declared built-up crane-runway-beam route, with welded/friction `Rv` values selected explicitly and confirmation that stress components were obtained according to equation (67).

## N9-R08 — Dedicated NormCAD Section-12 fatigue case
- Classification: **NO_DEDICATED_N9_GOLDEN_CASE_FOUND**
- Resolution: no dedicated NormCAD Section-12 end-to-end fatigue oracle was found in the retained library/corpus; no synthetic golden case was created.
