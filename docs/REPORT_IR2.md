# REPORT-IR2 — DAG-bound calculation report

## Priority

The normative DAG remains the calculation authority. REPORT-IR2 is a projection layer and must not become a second engineering engine.

Current production graph:

`normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json`

The focused regression freezes the expected graph census at 922 quantities / 39 datasets / 734 nodes.

## Data path

```text
DAG node
  -> production/declarative executor
  -> QuantityValue + TraceRecord
  -> REPORT-IR1 raw trace projection
  -> REPORT-IR2 binding evidence
  -> Streamlit "Ход расчёта"
```

REPORT-IR2 never evaluates the DAG expression and never repeats table interpolation.

## Formula evidence

For a node with `calculation_spec` or `check_spec`, REPORT-IR2 records:

- the frozen DAG expression;
- every `variable -> quantity_id` binding;
- the exact raw value and canonical unit present in the execution trace;
- the actual result value from the trace.

This is sufficient to show the user which values were substituted without creating a second calculation path.

## Lookup/interpolation evidence

For a lookup node REPORT-IR2 records:

- dataset id and normative provenance from REPORT-IR1;
- selector bindings and actual selector values from the trace;
- output bindings and actual result values from the trace;
- interpolation method and axis from the frozen DAG.

REPORT-IR2 intentionally does **not** reconstruct lower/upper table rows after execution. The field
`selected_dataset_rows_status = NOT_CAPTURED_BY_RUNTIME_YET` is an explicit gate. Exact bracket rows must later be emitted by the lookup executor itself; the report renderer is forbidden to infer them.

## Full-DAG reportability census

`reportability_census(model)` classifies every node in the active DAG by:

- node type;
- report block kind;
- execution-spec mode;
- explicit `report_spec` availability;
- normative-reference completeness.

Unsupported/failing routes remain reportable as explicit `FAIL_CLOSED` blocks; they are not omitted.

## Streamlit live report

The right-side panel now contains a primary **Ход расчёта** tab. Each completed DAG trace event appears as a report block containing inputs, normative references, formula/lookup metadata and trace result. REPORT-IR2 JSON can be downloaded directly. PDF/DOCX rendering is deliberately deferred.

## Navigation UX

The Streamlit presentation now exposes deterministic replay directly:

- `← Назад` opens the previous answered interactive DAG question;
- `Перейти к шагу / вопросу` opens any answered question;
- the existing full history remains available below;
- applying an edited answer uses `GuidedCalculationSession.edit_answer()` and therefore replays all downstream state from the DAG.

No UI-local back stack or mutable report state is introduced.
