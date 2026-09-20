# REPORT-IR4 — human-readable calculation report

## Goal

Turn the existing DAG-first audit trace into a calculation report that can be read as an engineering calculation sheet **before** any PDF/DOCX work is attempted.

The report must show, for every executed calculation step:

1. normative reference;
2. active formula/expression from the frozen DAG;
3. the actual numerical values bound to its variables;
4. a textual formula with those numbers substituted;
5. the actual result returned by the production executor;
6. the selected route/case that made this formula applicable.

REPORT-IR4 remains a projection layer. It does not become a second SP16/SP554 engine.

## Runtime case evidence

`standard_core/declarative_case_evidence.py` wraps the already-installed declarative executor **after successful production execution** and records only selection evidence:

- selected `calculation_spec.cases[]` case and its expression;
- selected classification rule or explicit fallback;
- executed check condition.

The engineering expression is not evaluated a second time. The evidence key includes graph SHA, node id, the trace-visible consumed inputs, and the actual production outputs, so deterministic replay after editing an earlier answer cannot reuse stale case evidence.

Lookup row/interpolation evidence remains owned by `declarative_runtime_evidence.py`.

## Numerical substitution

`standard_core/report_ir4.py` performs **text-only token substitution**. Example:

```text
DAG expression
x * 2

Substitution
(3) * 2

Production result
y = 6 kN
```

The substituted expression is never evaluated by REPORT-IR4. The result is copied from the completed execution trace.

Variable replacement uses identifier boundaries, so a variable `x` cannot accidentally replace the `x` inside `xx`, `max`, or another identifier.

## Table interpolation

For a runtime-captured linear bracket the live report shows:

```text
b = b0 + f·(b1 - b0)
b = 10 + 0.5·(20 - 10)
b = 15 min   ← production lookup result
```

The lower/upper rows and fraction are the runtime audit evidence already captured around the production lookup. REPORT-IR4 does not repeat the interpolation numerically.

Exact-knot and bilinear evidence are rendered in the same fail-transparent manner.

## Selected DAG route

Every trace block that carries `selected_edge_id` contributes a route row containing:

- execution sequence;
- source report block;
- selected edge id;
- source node;
- destination node;
- frozen edge condition.

The condition is displayed but not evaluated again. The route authority is `completed_execution_trace.selected_edge_id`.

## Streamlit

The **Ход расчёта** tab now uses REPORT-IR4 and groups executed blocks into:

- Исходные данные;
- Расчётная схема, применимость и принятые ветви;
- Геометрические характеристики;
- Расчёт;
- Проверки;
- Результаты;
- Диагностика и ограничения.

Formula blocks show the active expression, numeric substitution, and production result together. Lookup blocks show the exact runtime-selected table rows plus interpolation substitution. A collapsed **Активный маршрут DAG** table is available at the bottom.

The existing deterministic navigation remains unchanged: **← Назад** and **Перейти к шагу / вопросу** call session replay rather than maintaining a separate UI history stack.

## Non-negotiable audit flags

REPORT-IR4 freezes these assertions in the IR:

- `calculation_values_recomputed_by_report = false`;
- `formula_expressions_evaluated_by_report = false`;
- `table_interpolation_recomputed_by_report = false`;
- `route_conditions_recomputed_by_report = false`;
- `numeric_substitution_is_text_only = true`.

PDF/DOCX rendering remains intentionally deferred until the live calculation report has sufficient content and route coverage.
