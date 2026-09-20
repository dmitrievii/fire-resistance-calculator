# Stage N7 — Effective Lengths + Limiting Slenderness / Current SP16 Closure

- Release: `v0.33_stage_n7_effective_lengths_limiting_slenderness_current_sp16_closed_reconstructed_r1`
- Verdict: **STAGE_N7_EFFECTIVE_LENGTHS_LIMITING_SLENDERNESS_CURRENT_SP16_CLOSED**
- Authoritative SP16 SHA-256: `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`
- DAG: `dag_v0.3.36_stage_n7.json` / `83df0991cc709ca22d9d345bf4049a6dd2a7d97844310788e06e659930d9aa16`
- Stage N7 focused runtime + DAG tests: **45/45 PASS**
- Cumulative pytest excluding release-manifest gate: **751/751 PASS**
- Full pytest including release-manifest gate: **752/752 PASS**
- `main.py` release audit: **PASS**
- Generated current-release outputs: **27/27**
- Validation corpus: **1876/1876 PASS**
- Independent function oracles: **60/581 retained**
- External golden cases: **6/6 retained**

## Closed scope

Clauses 10.1-10.4 are closed in the declared guided scope. Tables 24-33 and equations (136)-(147) are routed through a selected applicability-safe workflow. Equation (138) uses the current printed lower bound `0.6*l`; equation (139) uses `0.5*l1`; equation (141) executes the official FAU FCS clarification `mu=2*sqrt(1+0.38/n)`. Table 29 interpolation is used only where explicitly printed for `2<=n<=6`. Special Section-10 routes that require Annex И, certified-software analysis, or explicit restraint modelling remain fail-closed unless the external result and provenance are supplied.

## NormCAD reconciliation

No dedicated NormCAD calculation suitable as an end-to-end Stage N7 golden case for clauses 10.1-10.3 was found in the retained corpus. Historical NormCAD Section-10/Table-32 evidence remains secondary triangulation only and does not override the current SP16 source or official clarification. No synthetic golden case has been created.

## Explicitly not claimed

`ENGINEERING_USE_READY=False`. Full package-wide Change-6 rebaseline, original/effective GOST/GOST R audit of the interim imported profile catalog, and final external engineering certification remain deferred gates. N1-N7 are frozen cumulative dependencies unless a source-backed remediation is explicitly opened.
