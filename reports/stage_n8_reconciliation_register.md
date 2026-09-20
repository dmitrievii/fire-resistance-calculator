# Stage N8 — Reconciliation Register

- Release: `v0.34_stage_n8_sheet_structures_current_sp16_closed_reconstructed_r1`
- Current SP16 is primary; NormCAD is secondary evidence only.

## N8-R01 — Legacy Section-11 source metadata
- Classification: **CURRENT_SP16_REBASELINE_CLOSED**
- Resolution: Section-11 scalar producers and Table 34 provenance are rebaselined from Amendments 1-5 wording to the locked current source with Changes 1-6 through 09.12.2024.

## N8-R02 — Legacy all-routes Section-11 wrapper
- Classification: **APPLICABILITY_ORCHESTRATION_CLOSED**
- Resolution: new sheet_structure_guided selects exactly one applicable 11.1/11.2 route; the old all-routes demo action is retained only for backward compatibility.

## N8-R03 — Table 34 non-node c values
- Classification: **EXACT_GRID_FAIL_CLOSED**
- Resolution: printed nodes are exact lookup only; no hidden interpolation or extrapolation. A non-node c requires an explicit external value and provenance.

## N8-R04 — Printed interpolation rules in 11.2.3 and 11.2.4
- Classification: **NORMATIVE_RULES_IMPLEMENTED**
- Resolution: linear interpolation is encoded only for 0.8Ry<sigma<Ry in the cylindrical-panel limit and for 10<l/r<20 in external-pressure critical stress.

## N8-R05 — Clauses 11.1.4 and 11.1.5
- Classification: **EXTERNAL_ANALYSIS_FAIL_CLOSED**
- Resolution: local edge effects and arbitrary/spatial shell analysis are not inferred; required local analysis, certified software, and linked clause compliance must be explicitly confirmed.

## N8-R06 — Clause 11.2.2 equation (156) below first Table-34 printed node
- Classification: **EXTERNAL_PROVENANCE_BOUNDARY**
- Resolution: when the direct tube route needs axial shell critical stress at an r/t not printed in Table 34, the package requires explicit c provenance rather than extrapolating the table.

## N8-R07 — Clause 11.2.4 ring-stiffened shell
- Classification: **ACTUAL_SECTION_CHECK_CLOSED**
- Resolution: ring spacing substitution is coupled to actual effective area/radius of gyration/section type, equation-(7) branch stability, relative slenderness <=6.5, and one-sided inertia-axis confirmation where applicable.

## N8-R08 — Dedicated NormCAD Section-11 shell case
- Classification: **NO_DEDICATED_N8_GOLDEN_CASE_FOUND**
- Resolution: no dedicated NormCAD Section-11 end-to-end oracle was found; no synthetic golden case was created.

