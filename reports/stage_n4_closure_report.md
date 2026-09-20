# Stage N4 — Bending Members / Current SP16 Closure

- Release: `v0.30_stage_n4_bending_members_current_sp16_closed_reconstructed_r1`
- Verdict: **STAGE_N4_BENDING_MEMBERS_CURRENT_SP16_CLOSED**
- Authoritative SP16 SHA-256: `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`
- DAG: `dag_v0.3.33_stage_n4.json` / `4de76fe047e435baff34a03db8496200f37be75993623af770548081ee4064fc`
- Stage N4 focused tests: **20/20 PASS**
- Full pytest excluding release-manifest gate: **665/665 PASS**
- Full pytest with release-manifest gate: **666/666 PASS**
- Release-manifest gate: **1/1 PASS**
- `main.py` release audit: **PASS**
- Generated current-release outputs: **24/24**
- N4 discrepancies: **7 total; 0 open package/DAG defects; 0 runtime unresolved**

## Closed scope

Section 8 guided bending-member orchestration is branch-safe for the declared scope: class-1 equations (41)/(42) and conditional (43), explicit class-2/3 routes, corrected equation (61), current-SP16 Annex Ж design-`Ry` path, supported rolled-I `phi_b -> equation (69)` calculation, lateral-stability exemption routing, and explicit 8.5.1/8.5.9 screening.

## Explicitly not claimed

The guided local-stability result is a **screen**, not a silent full 8.5 pass; equations (80)-(100) remain in the dedicated detailed action. `ENGINEERING_USE_READY=False`. Full package-wide Change-6 rebaseline and the user-deferred original/effective GOST/GOST R audit of all interim imported profile rows remain mandatory final-package gates. NormCAD remains secondary historical evidence only.
