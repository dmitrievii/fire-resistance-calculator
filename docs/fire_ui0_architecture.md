# FIRE-UI0 — DAG-driven Guided Calculation Architecture

## Purpose

FIRE-UI0 introduces a UI-framework-independent application layer over the frozen
SP16 ↔ SP554 DAG.  It does **not** copy normative equations into frontend code.
The only permitted computation path is an explicitly registered production
executor from `standard_core`.

## Runtime layers

```text
frozen normative DAG v0.3.44
        ↓
FireDAGModel
        ↓
UI contract compiler
        ↓
GuidedCalculationSession
   ├─ question card
   ├─ branch resolver
   ├─ dependency/history replay on edit
   ├─ live quantity ledger
   └─ deterministic trace
        ↓
GuidedCalculationService
        ↓
future local HTTP / desktop / browser adapter
```

The frontend is therefore replaceable. React/TypeScript, a desktop shell, or a
QA CLI may consume the same service contract. Streamlit is not a dependency.

## Safety / audit invariants

1. The session is locked to both `graph_id` and canonical DAG SHA-256.
2. User decisions are type/enum validated against DAG quantity metadata.
3. External-standard values require explicit provenance.
4. Branch conditions execute the DAG expression subset (`eq`, `in`, `lt`,
   `lte`, `gt`, `gte`, `all_of`).
5. Calculation nodes without a registered production executor block. They are
   never skipped and no formula is reimplemented in the UI engine.
6. Editing an earlier answer deterministically replays the valid prefix and
   removes all downstream values/trace records from the abandoned branch.
7. Every value in the right-side ledger retains its producer, unit, source kind,
   provenance and normative references.
8. Trace order uses deterministic sequence numbers; wall-clock timestamps are
   deliberately outside the calculation trace.

## Frontend contract

The left/main pane renders `current_card`.

- `decision` → radio/select from DAG options.
- one-output `input` → scalar widget inferred from quantity metadata.
- grouped `input` → object form with one field per produced quantity.
- `standard_handoff` → external-source form with provenance.
- `result` → terminal/read-only card.
- calculation/classification/lookup/compliance nodes execute only through the
  registry. Missing executor → explicit blocked state.

The right pane renders `ledger`, which is updated after every accepted answer or
calculation execution.

## Report path

The future report generator consumes the exact same `trace` used by the UI.
There is no second report-only calculation implementation.

```text
answer/executor
    ↓
TraceRecord
    ├─ inputs
    ├─ outputs
    ├─ normative_refs
    ├─ selected DAG edge
    └─ status
       ↓
UI audit view / JSON case / DOCX-PDF report
```

## Scope boundary

FIRE-UI0 closes architecture only. Full node-to-production-executor binding of
the SP16 → FIRE-D4 member walkthrough belongs to FIRE-UI2. Bolts/connections are
excluded until their fire runtime is implemented. FIRE-D5 protection design and
FIRE-D7 alternative fire are likewise not invented by the UI.
