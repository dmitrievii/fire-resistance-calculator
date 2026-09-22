# v0.88 LIVE-REPORT2 — Expertise-style engineering report

- Replaces the technical REPORT-IR presentation in the primary pane with a human-readable calculation document intended to resemble an engineering report submitted for review/expertise.
- Preserves REPORT-IR5 and `build_trace_bound_equation` as the sole sources of values, formulas, substitutions and explicit verdicts; no engineering calculation is repeated in the presentation layer.
- Structures the document into: исходные данные; расчётная схема и предпосылки; проверки по СП 16; расчёт огнестойкости по СП 554; результаты и заключение.
- Each calculation block is presented as: purpose -> input quantities -> normative formula -> numerical substitution/result -> engineering conclusion -> normative basis.
- Internal node/quantity/edge identifiers are removed from the primary document and remain available only in Audit.
- Markdown export is generated from the same expertise-style composition.
- Desktop layout is widened from 1500 px to 1800 px and the main split changes from approximately 62/38 to approximately 42/58 in favour of the report pane.
- The layout overlay intercepts only the main `[1.65, 1]` two-pane column call; nested forms, metrics and other column layouts are unchanged.
- Mobile behaviour remains inherited from Streamlit's responsive column stacking.

Scope: presentation only. SP16/SP554 graph, registries, solvers, thermal model, routing and calculation state are unchanged from v0.87/v0.86.
