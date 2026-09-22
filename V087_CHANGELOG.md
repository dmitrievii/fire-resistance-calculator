# v0.87 LIVE-REPORT1

- Replaces the overloaded right-hand `Summary -> Report -> Ledger/Trace` stack with one dedicated **Живой расчётный отчёт** pane.
- Keeps REPORT-IR5 as the sole report source; no engineering quantity is recalculated in Streamlit.
- Shows the **latest completed DAG step above the full protocol**, so the consequence of each accepted user decision is immediately visible after rerun.
- Renders the full protocol in a scrollable right-hand container, grouped by existing REPORT-IR5 sections.
- Reuses the existing trace-bound formula renderer (`build_trace_bound_equation`) for symbolic formula, numerical substitution and runtime result.
- PASS/FAIL badges come only from explicit REPORT-IR5 check verdicts; no numeric UI inference is introduced.
- Normative references now expose all explicit locators carried by REPORT-IR: section, clause, formula, table, figure and appendix when present.
- Moves Markdown/Report-IR downloads to a secondary **Сводка / экспорт** tab.
- Moves raw quantity ledger / execution trace / branch failures to a secondary **Audit** tab so they no longer obscure the engineering report.
- Editing an earlier answer remains deterministic: FIRE-UI replays the DAG and LIVE-REPORT1 rebuilds the entire pane from the new execution trace.

Scope: presentation only. SP16/SP554 execution graph, registries, numerical solvers, thermal model and routing are unchanged from production v0.86.
