# Stage N7 reconciliation register

- Release: `v0.33_stage_n7_effective_lengths_limiting_slenderness_current_sp16_closed_reconstructed_r1`
- Primary authority: current СП 16.13330.2017 with Changes No. 1-6 through 09.12.2024
- Historical NormCAD role: secondary evidence only

## N7-R01 — Equation (138) lower bound
- Classification: `CURRENT_SP16_REMEDIATION_CLOSED`
- Resolution: legacy 0.61*l transcription replaced by the current printed 0.6*l lower bound

## N7-R02 — Equation (139) lower bound
- Classification: `CURRENT_SP16_REMEDIATION_CLOSED`
- Resolution: legacy 0.51*l1 transcription replaced by the current printed 0.5*l1 lower bound

## N7-R03 — Equation (141) printed typo
- Classification: `OFFICIAL_CLARIFICATION_APPLIED`
- Resolution: execute mu=2*sqrt(1+0.38/n) per FAU FCS letter No. Исх-8076 dated 10.11.2023; printed typo is retained as source history only

## N7-R04 — Table 29 interpolation
- Classification: `NORMATIVE_RULE_IMPLEMENTED`
- Resolution: linear interpolation is used only for the explicitly printed interval 2<=n<=6; end-connection adjustments follow the printed notes

## N7-R05 — Clause 10.3.7 stepped columns
- Classification: `APPLICABILITY_FAIL_CLOSED`
- Resolution: Annex И or an analysis reflecting actual restraints is required; no implicit stepped-column formula is fabricated

## N7-R06 — Clause 10.3.11 certified software route
- Classification: `EXTERNAL_ANALYSIS_ASSUMPTIONS_EXPLICIT`
- Resolution: certified software, elastic steel and undeformed-scheme assumptions must be confirmed and the resulting effective length must carry provenance

## N7-R07 — Historical NormCAD Table 32 check
- Classification: `HISTORICAL_SECONDARY_EVIDENCE_ONLY`
- Resolution: old NormCAD Table-32/SP16.13330.2010 calculation is retained for triangulation but cannot override current-SP16 routing

## N7-R08 — Dedicated NormCAD Section-10 effective-length case
- Classification: `NO_DEDICATED_N7_GOLDEN_CASE_FOUND`
- Resolution: no synthetic NormCAD golden case was created for clauses 10.1-10.3

## Closure
- Open package/DAG defects: **0**
- Runtime unresolved in declared closed routes: **0**
