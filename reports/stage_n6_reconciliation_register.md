# Stage N6 reconciliation register

- Release: `v0.32_stage_n6_built_up_beam_columns_local_stability_current_sp16_closed_reconstructed_r1`
- Items: **7**
- Open package/DAG defects: **0**
- Runtime unresolved in declared closed routes: **0**

## N6-R01 — Table D.4 interpolation
- Classification: `NORMATIVE_BOUNDARY_CLOSED`
- Resolution: exact printed nodes only; arbitrary point requires explicit external coefficient/provenance; phi_e<=central phi enforced

## N6-R02 — Tables 22/23 interpolation
- Classification: `NORMATIVE_RULE_IMPLEMENTED`
- Resolution: only interpolation intervals explicitly printed in table notes are encoded

## N6-R03 — 9.3.3 biaxial branch force
- Classification: `APPLICABILITY_FAIL_CLOSED`
- Resolution: equation (124) only for type 2; no fabricated type-1/type-3 combination

## N6-R04 — individual lattice branch stability
- Classification: `ROUTE_SEPARATION_CLOSED`
- Resolution: equation (7) uses branch phi; conditional 7.2.5 extended range remains separate dependency

## N6-R05 — 9.4.4 transverse stiffeners
- Classification: `PROVIDED_GEOMETRY_CHECK_CLOSED`
- Resolution: outstand, thickness and spacing are checked explicitly when required

## N6-R06 — 9.4.5 longitudinal stiffener
- Classification: `MULTI_OBLIGATION_CHECK_CLOSED`
- Resolution: Ir1 requirement plus most-loaded-half-web Table 22 evidence and 7.3.4 confirmation are required

## N6-R07 — NormCAD triangulation
- Classification: `NO_DEDICATED_N6_GOLDEN_CASE_FOUND`
- Resolution: no synthetic NormCAD 9.3-9.4 golden case created; existing historical corpus remains secondary only
