# FIRE-UI1 — Guided Wizard + Live Calculation Ledger Frontend

## Purpose

FIRE-UI1 is the first executable browser presentation layer over the frozen
SP16 ↔ SP554 DAG application architecture introduced in FIRE-UI0. It is a
local-only engineering QA frontend, not a second calculation engine.

```text
frozen DAG v0.3.44
       |
       v
FireDAGModel / GuidedCalculationSession       (FIRE-UI0)
       |
       v
GuidedCalculationService                      (FIRE-UI0)
       |
       v
loopback HTTP adapter                         (FIRE-UI1)
       |
       v
TypeScript browser frontend                   (FIRE-UI1)
       |
       +-- guided question card
       +-- Back / edit / deterministic replay
       +-- live quantity ledger
       +-- normative provenance
       +-- execution trace
       +-- save / restore JSON session
```

No SP16 or SP554 equation is implemented in TypeScript or in the HTTP adapter.
Calculation nodes remain executable only through explicit production executor
bindings in `ExecutionRegistry`.

## Local deployment

The first acceptance target intentionally uses no public application server and
no Streamlit dependency.

```text
browser
   |
http://127.0.0.1:<port>
   |
Python ThreadingHTTPServer
   |
GuidedCalculationService
```

The server binds to `127.0.0.1` only. Static files, API and session state use one
same-origin endpoint. There are no CDN resources and no network fonts.

## API

```text
GET    /api/health
GET    /api/ui-contract
POST   /api/sessions
GET    /api/sessions/{id}
POST   /api/sessions/{id}/answer
PUT    /api/sessions/{id}/answers/{node_id}
GET    /api/sessions/{id}/ledger
GET    /api/sessions/{id}/trace
POST   /api/sessions/restore
DELETE /api/sessions/{id}
```

### Fail-closed rules

- missing or invalid provenance is rejected by FIRE-UI0;
- changing an earlier answer replays the valid prefix and invalidates all old
  downstream quantities;
- missing calculation executor remains `BLOCKED_EXECUTOR_REQUIRED:*`;
- the frontend never substitutes a fallback formula or default result;
- saved sessions are graph-ID and graph-SHA locked.

## Frontend layout

Desktop uses two persistent columns:

```text
+---------------------------------------------------------------+
| Guided question / decision          | Live quantity ledger     |
|                                      | / execution trace        |
| question                             |                          |
| options / field                      | quantity      value unit |
| provenance when needed               | producer / source        |
|                                      |                          |
| Back                         Next    |                          |
+---------------------------------------------------------------+
| normative references                              scope status |
+---------------------------------------------------------------+
```

Below 1050 px the ledger moves below the guided card. Below 720 px decision
cards and provenance fields become one-column.

## Scope boundary

FIRE-UI1 closes the presentation and local transport architecture only.

Closed:

- real DAG-generated question rendering;
- select, boolean, number and text input widgets;
- external standard handoff provenance;
- live ledger and source/producer labels;
- deterministic Back/edit/replay;
- trace tab;
- session JSON save/restore;
- loopback-only static/API server;
- offline static resources;
- TypeScript source plus materialized JavaScript build.

Deferred to FIRE-UI2:

- complete SP16 → FIRE-D4 executor binding across the guided route;
- automated production calculation after every sufficient input set;
- route-level acceptance cases for tension/compression/bending/N+M/biaxial.

Deferred further:

- FIRE-D5 automatic protection design;
- connections / bolts;
- non-standard fire route;
- calculation-report renderer.
