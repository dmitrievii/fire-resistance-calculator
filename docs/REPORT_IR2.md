# REPORT-IR2/3 — DAG-bound calculation report

## Priority

The normative DAG remains the calculation authority. REPORT-IR is a projection/audit layer and must not become a second engineering engine.

Current production graph:

`normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json`

The focused regression freezes the expected graph census at **922 quantities / 39 datasets / 734 nodes**.

## Data path

```text
DAG node
  -> production/declarative executor
  -> QuantityValue + TraceRecord
  -> runtime dataset-row audit evidence
  -> REPORT-IR1 raw trace projection
  -> REPORT-IR2/3 binding evidence
  -> Streamlit "Ход расчёта"
```

The report renderer never evaluates the DAG expression and never repeats table interpolation.

## Formula evidence

For a node with `calculation_spec` or `check_spec`, REPORT-IR records:

- the frozen DAG expression;
- every `variable -> quantity_id` binding;
- the exact raw value and canonical unit present in the execution trace;
- the actual result value from the trace.

## Lookup/interpolation evidence

The existing declarative executor remains the sole calculation path. After a successful lookup, transparent runtime audit instrumentation records the immutable dataset rows corresponding to the already-resolved selector. It does **not** interpolate the result a second time.

For linear interpolation the evidence includes:

- dataset id;
- selector fields and quantity values;
- lower and upper dataset rows with their source row indices;
- interpolation axis and resolved selector position;
- interval fraction;
- the actual output already returned by the production lookup.

For an exact knot, the exact row is recorded. Bilinear routes record the four grid roles and both axis fractions.

The evidence cache key contains graph SHA, owning DAG node, selector values and actual executor outputs. Therefore an edited earlier answer cannot accidentally reuse stale table evidence after deterministic DAG replay.

If matching runtime evidence is unavailable, REPORT-IR remains transparent: `selected_dataset_rows_status = NOT_CAPTURED_BY_RUNTIME`; the renderer does not reconstruct rows itself.

## Full-DAG reportability census

`reportability_census(model)` classifies every node in the active DAG by node type, report block kind, execution-spec mode, explicit `report_spec` availability and normative-reference completeness. Unsupported/failing routes remain visible as explicit `FAIL_CLOSED` blocks.

## Streamlit live report

The right-side panel contains a primary **Ход расчёта** tab. Each completed DAG trace event appears as a report block containing inputs, normative references, formula/lookup metadata and trace result. Lookup blocks additionally show runtime-captured table rows. REPORT-IR JSON can be downloaded directly. PDF/DOCX rendering remains deliberately deferred.

## Navigation UX

The Streamlit presentation exposes deterministic replay directly:

- `← Назад` opens the previous answered interactive DAG question;
- `Перейти к шагу / вопросу` opens any answered question;
- the full history remains available below;
- applying an edited answer uses `GuidedCalculationSession.edit_answer()` and therefore replays all downstream state from the DAG.

No UI-local back stack or mutable report state is introduced.
