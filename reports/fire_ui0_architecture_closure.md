# FIRE-UI0 — DAG-driven Guided Calculation Architecture — closure report

Release: `v0.42_fire_ui0_dag_driven_guided_calculation_architecture_r1`  
Parent: `v0.41_fire_d4_sp554_section13_result_assessment_runtime_r1`

## Result

FIRE-UI0 closes the framework-independent application architecture required for
a sequential NormCAD-style fire-resistance calculator over the frozen SP16 ↔
SP554 DAG. It does not introduce new normative formulas and does not alter the
FIRE-D1/D2/D3/D3.1/D4 production results.

### Frozen DAG consumed by the UI compiler

- graph: `sp16_sp554_dag_v0-3-44_fire_d4`
- quantities: 748
- nodes: 657
- edges: 1108
- interactive UI nodes: 139
  - inputs: 69
  - decisions: 65
  - standard handoffs: 5
- result nodes exposed as terminal/read-only cards: 48

## Closed architecture contracts

1. **DAG → UI contract** — widget type, unit, options, source policy,
   normative references and prompt are derived from graph metadata.
2. **Guided session state machine** — one current question/node at a time.
3. **Control-flow navigation** — only `control`, `branch` and `handoff` edges
   navigate the wizard. `data` edges never change question order.
4. **Parallel supporting-standard policy** — if the same condition fans into a
   primary owner-standard path and a supporting-standard subgraph, the guided
   path preserves owner-standard continuity; explicit handoff metadata remains
   the only automatic standard transition. Unresolved ambiguity blocks.
5. **External provenance gate** — values whose DAG source policy is external
   cannot be accepted as bare numbers.
6. **Edit/replay invalidation** — editing an earlier answer replays the valid
   prefix from the frozen entry node; quantities and traces from the abandoned
   downstream branch disappear.
7. **Live quantity ledger** — value, symbol, unit, source kind, producer node,
   provenance and normative references are preserved for the right-hand panel.
8. **Report-ready deterministic trace** — every accepted answer/calculation and
   selected edge has a deterministic sequence record. No separate report-only
   calculation engine is permitted.
9. **Explicit executor registry** — calculation nodes without a registered
   production executor block; the UI layer never guesses or silently skips a
   normative calculation.
10. **Save/load identity** — sessions are locked to graph ID plus canonical
    graph SHA-256 and reject replay against a different DAG.

## Integrated production proof

`run_integrated_member_fire_case()` composes the existing frozen production
runtimes instead of copying equations into UI code.

Control chain:

- FIRE-D2 critical temperature: `525.0192844353662 °C`
- reduced thickness: `10 mm`
- FIRE-D3 actual unprotected fire resistance: `14.326394173167056 min`
- required fire resistance: `15 min`
- FIRE-D4 compliance: `FAIL`

This proves the application seam can populate a live ledger from the current
integrated calculation code while retaining the exact previously qualified
results.

## Deliberately open after UI0

- Full mapping of every guided SP16/SP554 node to a production executor.
- Browser/desktop visual frontend.
- Interactive DAG audit pane.
- Rendered DOCX/PDF calculation report.
- FIRE-D5 automatic fire-protection design.
- FIRE-D7 alternative fire.
- Fire resistance of bolts/connections.

These are not silently simulated by UI0.

## Qualification

Focused UI0 architecture tests: `11/11 PASS`.

Retained focused fire runtimes independently rerun during the stage:

- FIRE-D1: `11/11 PASS`
- FIRE-D2: `32/32 PASS`
- FIRE-D3: `23/23 PASS`
- FIRE-D3.1: `12/12 PASS`
- FIRE-D4: `15/15 PASS`

`main.py` cumulative audit after UI0 integration: `PASS`; 1876 validation cases
PASS, 6/6 external golden cases PASS, no unresolved equations/tables, public API
docstring gate PASS, independent normative rebaseline PASS.

`ENGINEERING_USE_READY` remains `False`.
