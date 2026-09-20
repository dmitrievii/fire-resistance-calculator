# FIRE-D4 — SP554 Section 13 Result Assessment Runtime

Release: `v0.41_fire_d4_sp554_section13_result_assessment_runtime_r1`  
Parent: `v0.40_fire_d31_sp554_section12_full_scope_reconciliation_r1`

## Verdict

**FIRE-D4 SP554 Section 13 standard-fire result-assessment runtime is CLOSED in the declared scope.**

## Closed scope

- **13.1:** the mechanical result is the critical steel temperature delivered by the frozen FIRE-D2 producer.
- **13.2:** the thermal result is the valid FIRE-D3 time from heat-exposure start to that critical temperature.
- **13.3:** the standard-fire result is represented as `R + exact calculated time`; the runtime performs no nearest-class rounding, flooring or ceiling.
- Compliance is an independent exact comparison `R_fact >= R_req` using unrounded numerical values.
- `R_req` remains an **external normative/project input** and is rejected unless source provenance is supplied and its `value_min` exactly matches the calculation input.
- **13.4:** valid protected thermal tuples can be emitted as fire-protection-efficiency indicator records; this does not constitute product certification and does not invent/extrapolate missing points.
- Failed unprotected assessment routes to `FIRE_PROTECTION_DESIGN_REQUIRED`; failed protected assessment routes to `FIRE_PROTECTION_REDESIGN_REQUIRED`.

## Architectural reconciliation

The pre-existing conceptual DAG gated the 13.3 R-designation nodes on a successful compliance result. FIRE-D4 removes that dependency: the actual fire-resistance result exists even when it is below the external requirement. PASS/FAIL remains a separate compliance check.

The generic `critical_temperature_c` quantity also now admits `FORMULA_RESULT` provenance so it is consistent with the closed FIRE-D2 Appendix-B inversion producer.

## Numerical control

For `Tcr = 525.0192844353662 °C` and `delta_pr = 10 mm`, FIRE-D3 gives `R_fact = 14.326394173167056 min`. Against explicit `R_req = 15 min`:

- actual notation: `R 14.3263941732`;
- required notation: `R 15`;
- margin: `-0.6736058268329437 min`;
- assessment: **FAIL**;
- next action: `FIRE_PROTECTION_DESIGN_REQUIRED`.

No rounding is allowed to transform this result into R15.

## Explicit open boundaries

- Real/alternative fire assessment remains fail-closed until FIRE-D7.
- Automatic derivation of `R_req` from SP2/building classification is not part of FIRE-D4.
- Annex A schedule and protection-design synthesis are deferred to FIRE-D5.
- Connection fire resistance remains deferred.
- `ENGINEERING_USE_READY = False`.

## DAG

`normative_graph/dag_v0.3.44_fire_d4.json`

- quantities: **748**
- nodes: **657**
- edges: **1108**
- datasets: **38**
- SHA-256: `cb5143967c7503c5280283e227d6ab63fcfd305782fff2d3c26e4f1c43e5dfed`
