# Stage N1 — Material / Strength

Status: **N1 CLOSED for the declared Material / Strength scope.**

Authoritative source SHA-256: `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`.  
Remediated DAG SHA-256: `230a7332fee87d18dec5f975ec96c9259c62112d56cc7123e61282d34c5e48ce`.

The normative authority is the locked current СП 16 source only. NormCAD is retained as a historical secondary oracle and never overrides the current standard.

## Closed scope

- Clause 4.3.2: `gamma_u = 1.3`.
- Clause 5.1 / Annex Б.1 rolled-steel physical constants: `rho`, `alpha`, `E`, `G`, `nu`.
- Clause 6.1 / Tables 2 and 3: resistance formula contract and explicit `gamma_m` categories.
- Annex В.3, В.4, В.5: exact source-backed `Ryn`, `Run`, printed `Ry`, `Ru` rows and thickness routing.
- Product routing: plate/sheet/strip, rolled bar and tube -> В.3; parallel-flange I-sections -> В.4; shaped rolled products -> В.5.
- No interpolation/extrapolation and no hidden `gamma_m` default.

## Validation evidence

- Current СП -> package: **7/7 source checks PASS_EXACT**.
- Annex В strength rows: **95/95 source rows PASS_EXACT**.
- Exhaustive current-source boundary matrix: **981 probes** (866 expected resolves, 115 expected fail-closed), including every finite endpoint and the immediately adjacent floating-point values via `math.nextafter`.
- NormCAD strength MDB static decode: **62 sheet + 72 shaped + 6 tube rows** with source MDB hashes and raw record evidence.
- NormCAD crosswalk: **111 current grade/range comparisons**; 50 exact static matches, 23 value mismatches, 18 missing thickness routes, 15 boundary-label differences/uncertainties, 5 missing grades.
- Discrepancy register: **19 total, 0 unresolved**. Five package/DAG defects were remediated; NormCAD divergences remain recorded as historical/nonconforming evidence.

## Important limitation

Where old NormCAD static MDB condition labels do not uniquely prove exact runtime/UI behavior at a boundary, that runtime behavior is **not claimed**. This does not weaken the normative package result: current СП remains the source of truth, and production boundary behavior is validated directly against the current-SP source capture.

Stage N1 closure does **not** mean that the entire СП16 package is fully validated. Full package-wide Change 6 rebaseline and later N-stages remain open; `engineering_use_ready = false`.
