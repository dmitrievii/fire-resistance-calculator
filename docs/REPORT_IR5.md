# REPORT-IR5 — conservative engineering summary

## Purpose

REPORT-IR4 makes every executed DAG step readable as `formula → numerical substitution → production result`. REPORT-IR5 adds the report front matter that an engineer needs before reading those details:

- which compliance checks actually executed;
- their explicit trace verdicts where such a verdict exists;
- final `RESULT` node outputs;
- current fail-closed limitations;
- the number of executed route edges.

PDF/DOCX remains out of scope.

## Deliberately conservative verdict policy

The summary is **not** a second normative engine.

A `CHECK` block is labelled `PASS` or `FAIL` only when its completed production trace exposes an unambiguous boolean output. A numeric value such as a utilization, resistance ratio, temperature or reserve is never interpreted by REPORT-IR5 from its name or magnitude.

If a completed check has no unambiguous boolean output, the summary records:

`UNRESOLVED — no_unambiguous_boolean_verdict_in_trace`

This is intentional. The normative DAG/executor must own the pass/fail semantics.

## Summary status

`summary_status` classifies the **report execution state**, not the global engineering certification of the member:

- `FAIL_CLOSED` — the active route contains a current fail-closed block;
- `EXECUTED_CHECK_FAILED` — at least one completed check has an explicit false boolean verdict;
- `CHECK_VERDICT_NOT_EXPLICIT` — no explicit failure exists, but at least one completed check has no unambiguous boolean verdict;
- `EXECUTED_BOOLEAN_CHECKS_PASS` — all completed check blocks expose true boolean verdicts;
- `NO_COMPLETED_CHECKS_YET` — no check block has completed yet.

The fixed scope string is `report_execution_state_not_global_engineering_certification`.

## Governing result

REPORT-IR5 intentionally does **not** choose a governing utilization by scanning quantity names or selecting the largest numeric value. Until the frozen DAG explicitly declares the governing quantity/criterion in presentation metadata, the summary returns:

`governing.status = NOT_DECLARED_BY_DAG`

This prevents the report layer from silently creating engineering logic outside SP16/SP554 runtime.

## Streamlit

A live `Итоговая расчётная сводка` is rendered immediately before the existing report/trace tabs. It contains:

- summary execution status;
- PASS / FAIL / unresolved check counts;
- a table of executed checks with normative references and trace results;
- outputs from completed result nodes;
- active fail-closed limitations;
- an explicit note when governing selection is not yet declared by the DAG.

The detailed `Ход расчёта` below remains REPORT-IR4 and continues to show formula substitutions, runtime table rows and the selected DAG route.

## Audit invariants

REPORT-IR5 freezes the following additional assertions:

- `summary_recomputed_engineering_checks = false`;
- `summary_inferred_numeric_check_verdicts = false`;
- `summary_inferred_governing_result = false`.

All REPORT-IR4 no-recalculation assertions remain inherited.
