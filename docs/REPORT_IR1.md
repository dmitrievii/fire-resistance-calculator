# REPORT-IR1 — DAG-first auditable calculation report

## Status

Initial implementation slice for the v0.67+ SP16 ↔ SP554 guided calculation engine.

The report is **not a second calculation engine**. `standard_core/report_ir.py` projects the already executed guided-calculation state into a deterministic intermediate representation (`fire_report_ir_v1`). Numerical values in ordinary report blocks are copied from completed session trace events; formula, lookup and normative provenance are copied from the immutable DAG node that actually owned the execution step.

## Authoritative data flow

```text
user answer
    ↓
GuidedCalculationSession
    ↓
DAG routing / production executor / declarative executor
    ↓
QuantityValue ledger + TraceRecord
    ↓
REPORT-IR1 pure projection
    ↓
JSON / future Streamlit / HTML / PDF / DOCX renderers
```

REPORT-IR1 must not evaluate `calculation_spec.expression`, must not repeat table interpolation, and must not infer a replacement normative route. A report renderer is therefore incapable of changing the engineering result.

## Current contract

Canonical schema: `schemas/fire_report_ir_v1.schema.json`.

Block kinds:

- `INPUT`
- `ASSUMPTION`
- `GEOMETRY`
- `FORMULA`
- `TABLE_LOOKUP`
- `INTERPOLATION`
- `BRANCH_DECISION`
- `CHECK`
- `WARNING`
- `FAIL_CLOSED`
- `RESULT`

Each normal block records at minimum:

- stable `report_block_id` for the current replay route;
- `owner_node_id` and `owner_standard_id`;
- actual execution sequence and event kind;
- normative references from the owning DAG node;
- actual input/output values from the completed trace record;
- quantity units/symbols and available ledger provenance;
- selected navigation edge where recorded;
- the frozen DAG execution specification used by the engine (`calculation_spec`, `lookup_spec`, `check_spec`, classification or geometry metadata);
- referenced dataset identity/provenance where the DAG supplies it.

The IR also has a deterministic SHA-256 identity. Wall-clock timestamps are intentionally excluded from report identity.

## Replay/edit invariant

`GuidedCalculationSession.edit_answer()` already clears state and deterministically replays prior answers. REPORT-IR1 is rebuilt from that state rather than maintained as mutable parallel state. Therefore stale downstream report blocks cannot survive an edit: if a DAG node is not present in the new completed trace, it is not present in the new report.

## Fail-closed invariant

A node that fails before producing a completed calculation trace cannot receive a normal `FORMULA`/`LOOKUP` calculation block. Current branch failures are represented as `FAIL_CLOSED` audit blocks with no fabricated outputs.

## Presentation contract

The initial implementation automatically infers a generic report kind and section from the DAG node type. It is prepared to consume an optional future `report_spec` attached to a DAG node for **presentation metadata only** (section, title, LaTeX form, display precision, visibility). Such metadata may never supply or override engineering calculation values.

The required engineering style for future renderers is:

> one normative formula → one numerical substitution → one result

Display rounding must remain separate from raw runtime precision.

## Next slice

1. Validate REPORT-IR1 directly against the active `dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json`.
2. Add an explicit, backwards-compatible DAG `report_spec` schema only after the generic projection is qualified.
3. Instrument declarative lookup execution with **execution evidence** (selected row/interpolation bracket) so table/interpolation reports can show the exact points used without recomputing the lookup.
4. Add the central-tension SP554 example as the first golden engineering report case.
5. Bind the IR to the guided UI as a live “Ход расчёта” view; render HTML first, then DOCX/PDF from the same IR.
