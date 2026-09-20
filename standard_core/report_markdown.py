"""Deterministic engineering-report Markdown renderer over REPORT-IR5.

The renderer is intentionally presentation-only. It consumes a completed
REPORT-IR5 mapping and never receives the normative model/session, so it cannot
execute a DAG node, evaluate an expression, interpolate a dataset, choose a
route, or decide a check verdict.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

REPORT_MARKDOWN_CONTRACT = "report_ir5_markdown_projection_v1"

_STATUS_RU = {
    "FAIL_CLOSED": "Расчёт остановлен fail-closed",
    "EXECUTED_CHECK_FAILED": "Есть невыполненная проверка",
    "CHECK_VERDICT_NOT_EXPLICIT": "Часть проверок не имеет явного boolean-вердикта",
    "EXECUTED_BOOLEAN_CHECKS_PASS": "Все выполненные boolean-проверки пройдены",
    "NO_COMPLETED_CHECKS_YET": "Проверки ещё не выполнены",
}


def _text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return str(value)


def _escape_cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", "<br>")


def _refs(refs: Any) -> str:
    rendered: list[str] = []
    for ref in refs or []:
        if not isinstance(ref, Mapping):
            continue
        standard = ref.get("standard_id") or ref.get("document_id") or ""
        section = ref.get("section") or ref.get("clause") or ref.get("table") or ref.get("figure") or ""
        tail = " ".join(str(x).strip() for x in (standard, section) if x is not None and str(x).strip())
        if tail:
            rendered.append(tail)
    return "; ".join(rendered) if rendered else "—"


def _value(row: Mapping[str, Any]) -> str:
    value = _text(row.get("raw_value"))
    unit = row.get("canonical_unit")
    return f"{value} {unit}" if unit else value


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    out = [
        "| " + " | ".join(_escape_cell(cell) for cell in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    out.extend("| " + " | ".join(_escape_cell(cell) for cell in row) + " |" for row in rows)
    return out


def _block_lines(block: Mapping[str, Any]) -> list[str]:
    sequence = block.get("sequence")
    kind = block.get("kind") or "STEP"
    title = block.get("title") or block.get("owner_node_id") or "Расчётный шаг"
    lines = [f"#### {sequence}. [{kind}] {title}", ""]
    lines.append(f"**DAG node:** `{block.get('owner_node_id')}`  ")
    lines.append(f"**Нормативная ссылка:** {_refs(block.get('normative_refs'))}")
    lines.append("")

    if kind == "FAIL_CLOSED":
        lines.append(f"> **FAIL-CLOSED:** {block.get('message') or 'Ветвь остановлена.'}")
        failure = block.get("failure")
        if failure:
            lines.extend(["", "```json", json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True, default=str), "```", ""])
        return lines

    inputs = [row for row in block.get("inputs") or [] if isinstance(row, Mapping)]
    if inputs:
        lines.append("**Исходные величины шага**")
        lines.append("")
        lines.extend(
            _table(
                ["Обозначение", "Quantity", "Значение"],
                [
                    [row.get("symbol") or row.get("quantity_id"), row.get("quantity_id"), _value(row)]
                    for row in inputs
                ],
            )
        )
        lines.append("")

    human = block.get("human_readable") or {}
    mode = human.get("mode")
    if mode == "formula_substitution":
        formula = human.get("formula_expression")
        substitution = human.get("substituted_expression")
        if formula:
            lines.extend(["**Расчётная формула — активное выражение из DAG**", "", "```text", str(formula), "```", ""])
        if substitution:
            lines.extend(["**Подстановка чисел**", "", "```text", str(substitution), "```", ""])
        if human.get("selected_case_index") is not None:
            lines.append(f"Активная piecewise-ветвь: `case #{human.get('selected_case_index')}` (runtime evidence).")
            lines.append("")
        results = human.get("result_lines") or []
        if results:
            lines.append("**Результат production-расчёта**")
            lines.append("")
            for row in results:
                if isinstance(row, Mapping):
                    lines.append(f"- **{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_value')}`")
            lines.append("")
    elif mode == "lookup_substitution":
        evidence = block.get("execution_evidence") or {}
        runtime_rows = evidence.get("selected_dataset_rows") or []
        lines.append(f"**Dataset:** `{human.get('dataset_id') or (block.get('execution_spec') or {}).get('dataset_id')}`")
        lines.append("")
        if runtime_rows:
            role_rows: list[list[Any]] = []
            for item in runtime_rows:
                if isinstance(item, Mapping):
                    role_rows.append(
                        [
                            item.get("role"),
                            item.get("row_index"),
                            json.dumps(item.get("row"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str),
                        ]
                    )
            lines.append("**Строки нормативной таблицы, зафиксированные runtime**")
            lines.append("")
            lines.extend(_table(["Роль", "Индекс", "Строка dataset"], role_rows))
            lines.append("")
        for row in human.get("output_lines") or []:
            if not isinstance(row, Mapping):
                continue
            if row.get("formula_expression"):
                lines.extend(["**Интерполяционная формула**", "", "```text", str(row.get("formula_expression")), "```", ""])
            if row.get("substituted_expression"):
                lines.extend(["**Подстановка по runtime-строкам**", "", "```text", str(row.get("substituted_expression")), "```", ""])
            lines.append(
                f"- **{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_result')}` — production lookup result"
            )
            lines.append("")
    elif mode == "route_decision":
        edge = human.get("selected_edge_id") or block.get("selected_edge_id")
        if edge:
            target = human.get("to_node_id")
            suffix = f" → `{target}`" if target else ""
            lines.append(f"**Выбранная ветвь:** `{edge}`{suffix}")
            lines.append("")

    outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
    if outputs and mode not in {"formula_substitution", "lookup_substitution"}:
        lines.append("**Результат шага — из execution trace**")
        lines.append("")
        for row in outputs:
            lines.append(f"- **{row.get('symbol') or row.get('quantity_id')}** = `{_value(row)}`")
        lines.append("")
    return lines


def render_report_markdown(report: Mapping[str, Any], *, title: str = "Расчёт огнестойкости стальной конструкции") -> str:
    """Render an already-built REPORT-IR5 mapping as deterministic Markdown."""
    if report.get("schema") != "fire_report_ir_v4":
        raise ValueError("Markdown renderer requires fire_report_ir_v4 / REPORT-IR5")

    summary = report.get("summary") or {}
    counts = summary.get("check_counts") or {}
    lines: list[str] = [
        f"# {title}",
        "",
        "## Идентификация расчёта",
        "",
        f"- **DAG:** `{report.get('graph_id')}`",
        f"- **DAG SHA-256:** `{report.get('graph_sha256')}`",
        f"- **Report IR:** `{report.get('schema')}` / `{report.get('contract')}`",
        f"- **Report SHA-256:** `{report.get('report_sha256')}`",
        f"- **Статус сессии:** `{report.get('session_status')}`",
        f"- **Текущий DAG node:** `{report.get('current_node_id')}`",
        "",
        "## Итоговая расчётная сводка",
        "",
        f"**Статус:** {_STATUS_RU.get(str(summary.get('summary_status')), _text(summary.get('summary_status')))}  ",
        f"**Область статуса:** `{summary.get('summary_status_scope')}`",
        "",
        f"Выполнено проверок: **{summary.get('check_count', 0)}**; PASS: **{counts.get('PASS', 0)}**; "
        f"FAIL: **{counts.get('FAIL', 0)}**; неоднозначно: **{counts.get('UNRESOLVED', 0)}**.",
        "",
    ]

    checks = summary.get("checks") or []
    if checks:
        lines.append("### Выполненные проверки")
        lines.append("")
        rows = []
        for check in checks:
            results = "; ".join(
                f"{out.get('symbol') or out.get('quantity_id')} = {out.get('display_value')}"
                for out in check.get("outputs") or []
                if isinstance(out, Mapping)
            )
            rows.append(
                [
                    check.get("sequence"),
                    check.get("title"),
                    _refs(check.get("normative_refs")),
                    check.get("verdict"),
                    results or "—",
                ]
            )
        lines.extend(_table(["Шаг", "Проверка", "Норма", "Вердикт", "Результат"], rows))
        lines.append("")

    results = summary.get("results") or []
    if results:
        lines.append("### Итоговые result-узлы")
        lines.append("")
        for result in results:
            lines.append(f"**{result.get('title') or result.get('owner_node_id')}**")
            for output in result.get("outputs") or []:
                if isinstance(output, Mapping):
                    lines.append(f"- {output.get('symbol') or output.get('quantity_id')} = `{output.get('display_value')}`")
            lines.append("")

    failures = summary.get("fail_closed") or []
    if failures:
        lines.append("### Fail-closed ограничения")
        lines.append("")
        for failure in failures:
            lines.append(f"> **{failure.get('title') or failure.get('owner_node_id')}:** {failure.get('message') or 'blocked'}")
        lines.append("")

    governing = summary.get("governing") or {}
    if governing.get("status") == "NOT_DECLARED_BY_DAG":
        lines.extend(
            [
                "### Governing result",
                "",
                "`NOT_DECLARED_BY_DAG` — governing utilization/criterion не выбирается отчётом эвристически. "
                "Он должен быть явно задан нормативным DAG/runtime.",
                "",
            ]
        )

    by_id = {
        str(block.get("report_block_id")): block
        for block in report.get("blocks") or []
        if isinstance(block, Mapping)
    }
    rendered: set[str] = set()
    for section in report.get("sections") or []:
        if not isinstance(section, Mapping):
            continue
        ids = [str(x) for x in section.get("block_ids") or [] if str(x) in by_id]
        if not ids:
            continue
        lines.extend([f"## {section.get('title_ru') or section.get('section_key')}", ""])
        for block_id in ids:
            lines.extend(_block_lines(by_id[block_id]))
            rendered.add(block_id)

    remaining = [block for block_id, block in by_id.items() if block_id not in rendered]
    if remaining:
        lines.extend(["## Дополнительные trace-блоки", ""])
        for block in sorted(remaining, key=lambda row: (int(row.get("sequence") or 0), str(row.get("report_block_id")))):
            lines.extend(_block_lines(block))

    route = report.get("selected_route") or []
    if route:
        lines.extend(["## Активный маршрут DAG", ""])
        lines.extend(
            _table(
                ["Шаг", "Edge", "От", "К", "Тип"],
                [
                    [
                        row.get("sequence"),
                        row.get("selected_edge_id"),
                        row.get("from_node_id"),
                        row.get("to_node_id"),
                        row.get("edge_type"),
                    ]
                    for row in route
                    if isinstance(row, Mapping)
                ],
            )
        )
        lines.append("")

    lines.extend(
        [
            "## Аудит отчёта",
            "",
            f"- Markdown contract: `{REPORT_MARKDOWN_CONTRACT}`",
            "- Численные результаты отчётом не пересчитываются.",
            "- Формулы отчётом не вычисляются; подстановка чисел является текстовым представлением.",
            "- Табличная интерполяция отчётом не повторяется.",
            "- Условия маршрутизации отчётом не вычисляются повторно.",
            "- Числовые коэффициенты не интерпретируются как PASS/FAIL без явного boolean-результата runtime.",
            "- Governing result не выбирается эвристически.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
