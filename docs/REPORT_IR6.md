# REPORT-IR6 — deterministic Markdown calculation report

## Purpose

REPORT-IR6 is the first downloadable human-readable calculation document built from the live REPORT-IR stack. It deliberately targets Markdown rather than PDF/DOCX so the report structure and engineering content can be stabilized before print-layout work begins.

The renderer accepts **only an already-built `fire_report_ir_v4` / REPORT-IR5 mapping**. It does not receive the normative DAG model or calculation session, so it cannot execute calculations by construction.

## Report structure

The generated `.md` document contains:

1. calculation identification and DAG/report hashes;
2. conservative calculation summary;
3. table of executed compliance checks and explicit trace verdicts;
4. completed RESULT-node outputs;
5. current fail-closed limitations;
6. explicit governing-result status;
7. every executed report section/block in deterministic trace order;
8. normative references;
9. input quantities used by each step;
10. active frozen-DAG formula;
11. numerical substitution text;
12. production trace result;
13. runtime-captured table rows and interpolation substitution;
14. active DAG route;
15. audit statement.

## Calculation authority

Markdown rendering is presentation-only:

- formulas are copied from REPORT-IR4 evidence;
- numerical substitution is copied/rendered as text and is not evaluated;
- results are copied from the production execution trace;
- table rows/fractions come from runtime lookup evidence;
- route edges come from `TraceRecord.selected_edge_id`;
- PASS/FAIL comes only from REPORT-IR5 explicit boolean-check policy;
- governing utilization is not inferred.

The renderer mutates neither REPORT-IR nor the calculation session.

## Streamlit

The live summary now exposes two primary downloads:

- **Скачать расчётный отчёт (.md)** — human-readable engineering report;
- **Скачать полный Report IR (.json)** — machine-readable REPORT-IR5 evidence.

The existing detailed `Ход расчёта` tab remains the interactive report view.

## Future print output

PDF/DOCX should be implemented as a renderer over the stabilized report representation/Markdown structure, not by calling SP16/SP554 calculation functions again. This keeps one calculation authority and prevents divergence between screen, Markdown and future print reports.
