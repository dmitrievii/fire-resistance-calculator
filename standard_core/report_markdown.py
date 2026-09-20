"""Deterministic engineering-report Markdown renderer over REPORT-IR5.

Presentation only: the renderer receives an already-built REPORT-IR mapping. It
never executes a DAG node, evaluates a formula, interpolates a dataset, chooses
a route, decides a check verdict, or selects a governing value.
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
    out: list[str] = []
    for ref in refs or []:
        if not isinstance(ref, Mapping):
            continue
        standard = ref.get("standard_id") or ref.get("document_id") or ""
        locator = (
            ref.get("clause")
            or ref.get("section")
            or ref.get("table_ref")
            or ref.get("table")
            or ref.get("figure")
            or ""
        )
        text = " ".join(str(x).strip() for x in (standard, locator) if x is not None and str(x).strip())
        if text:
            out.append(text)
    return "; ".join(out) if out else "—"


def _value(row: Mapping[str, Any]) -> str:
    value = _text(row.get("raw_value"))
    unit = row.get("canonical_unit")
    return f"{value} {unit}" if unit else value


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    result = [
        "| " + " | ".join(_escape_cell(x) for x in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    result.extend("| " + " | ".join(_escape_cell(x) for x in row) + " |" for row in rows)
    return result


def _block_lines(block: Mapping[str, Any]) -> list[str]:
    sequence = block.get("sequence")
    kind = block.get("kind") or "STEP"
    title = block.get("title") or block.get("owner_node_id") or "Расчётный шаг"
    lines = [f"#### {sequence}. [{kind}] {title}", ""]
    lines += [
        f"**DAG node:** `{block.get('owner_node_id')}`  ",
        f"**Нормативная ссылка:** {_refs(block.get('normative_refs'))}",
        "",
    ]

    if kind == "FAIL_CLOSED":
        lines.append(f"> **FAIL-CLOSED:** {block.get('message') or 'Ветвь остановлена.'}")
        if block.get("failure"):
            lines += [
                "",
                "```json",
                json.dumps(block["failure"], ensure_ascii=False, indent=2, sort_keys=True, default=str),
                "```",
                "",
            ]
        return lines

    inputs = [row for row in block.get("inputs") or [] if isinstance(row, Mapping)]
    if inputs:
        lines += ["**Исходные величины шага**", ""]
        lines += _table(
            ["Обозначение", "Quantity", "Значение"],
            [[row.get("symbol") or row.get("quantity_id"), row.get("quantity_id"), _value(row)] for row in inputs],
        )
        lines.append("")

    human = block.get("human_readable") or {}
    mode = human.get("mode")
    if mode == "formula_substitution":
        formula = human.get("formula_expression")
        substitution = human.get("substituted_expression")
        if formula:
            lines += ["**Расчётная формула — активное выражение из DAG**", "", "```text", str(formula), "```", ""]
        if substitution:
            lines += ["**Подстановка чисел**", "", "```text", str(substitution), "```", ""]
        if human.get("selected_case_index") is not None:
            lines += [f"Активная piecewise-ветвь: `case #{human.get('selected_case_index')}` (runtime evidence).", ""]
        results = [row for row in human.get("result_lines") or [] if isinstance(row, Mapping)]
        if results:
            lines += ["**Результат production-расчёта**", ""]
            for row in results:
                lines.append(f"- **{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_value')}`")
            lines.append("")

    elif mode == "lookup_substitution":
        evidence = block.get("execution_evidence") or {}
        runtime_rows = [row for row in evidence.get("selected_dataset_rows") or [] if isinstance(row, Mapping)]
        dataset_id = human.get("dataset_id") or (block.get("execution_spec") or {}).get("dataset_id")
        lines += [f"**Dataset:** `{dataset_id}`", ""]
        if runtime_rows:
            lines += ["**Строки нормативной таблицы, зафиксированные runtime**", ""]
            lines += _table(
                ["Роль", "Индекс", "Строка dataset"],
                [
                    [
                        row.get("role"),
                        row.get("row_index"),
                        json.dumps(row.get("row"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str),
                    ]
                    for row in runtime_rows
                ],
            )
            lines.append("")
        for row in human.get("output_lines") or []:
            if not isinstance(row, Mapping):
                continue
            if row.get("formula_expression"):
                lines += ["**Интерполяционная формула**", "", "```text", str(row["formula_expression"]), "```", ""]
            if row.get("substituted_expression"):
                lines += ["**Подстановка по runtime-строкам**", "", "```text", str(row["substituted_expression"]), "```", ""]
            lines += [
                f"- **{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_result')}` — production lookup result",
                "",
            ]

    elif mode == "route_decision":
        edge = human.get("selected_edge_id") or block.get("selected_edge_id")
        if edge:
            target = human.get("to_node_id")
            suffix = f" → `{target}`" if target else ""
            lines += [f"**Выбранная ветвь:** `{edge}`{suffix}", ""]

    outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
    if outputs and mode not in {"formula_substitution", "lookup_substitution"}:
        lines += ["**Результат шага — из execution trace**", ""]
        for row in outputs:
            lines.append(f"- **{row.get('symbol') or row.get('quantity_id')}** = `{_value(row)}`")
        lines.append("")
    return lines


def _governing_lines(governing: Mapping[str, Any]) -> list[str]:
    status = governing.get("status")
    rows = [row for row in governing.get("candidates") or [] if isinstance(row, Mapping)]
    lines = ["### Управляющие нормативные величины", ""]

    if status == "EXECUTED_DECLARATIONS" and rows:
        table_rows = []
        for row in rows:
            quantity = row.get("quantity") or {}
            table_rows.append(
                [
                    row.get("scope_title_ru") or row.get("scope"),
                    row.get("owner_node_id"),
                    quantity.get("symbol") or quantity.get("quantity_id"),
                    quantity.get("display_value"),
                    _refs(row.get("normative_refs")),
                ]
            )
        lines += _table(["Область", "DAG node", "Величина", "Значение", "Норма"], table_rows)
        lines += [
            "",
            "Каждая строка является отдельной governing-областью, объявленной DAG-bound metadata. "
            "Отчёт не сравнивает эти области между собой и не вычисляет глобальный максимум/минимум.",
            "",
        ]
    elif status == "DECLARED_BY_DAG_NOT_EXECUTED":
        lines += [
            "Governing-области объявлены в DAG-bound metadata, но соответствующие producer-узлы ещё не выполнены "
            "на текущем маршруте расчёта.",
            "",
        ]
    else:
        lines += [
            "`NOT_DECLARED_BY_DAG` — governing utilization/criterion не выбирается отчётом эвристически. "
            "Он должен быть явно задан DAG-bound report metadata/runtime.",
            "",
        ]
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

    checks = [row for row in summary.get("checks") or [] if isinstance(row, Mapping)]
    if checks:
        rows = []
        for check in checks:
            result = "; ".join(
                f"{out.get('symbol') or out.get('quantity_id')} = {out.get('display_value')}"
                for out in check.get("outputs") or []
                if isinstance(out, Mapping)
            )
            rows.append([
                check.get("sequence"), check.get("title"), _refs(check.get("normative_refs")),
                check.get("verdict"), result or "—",
            ])
        lines += ["### Выполненные проверки", ""]
        lines += _table(["Шаг", "Проверка", "Норма", "Вердикт", "Результат"], rows)
        lines.append("")

    results = [row for row in summary.get("results") or [] if isinstance(row, Mapping)]
    if results:
        lines += ["### Итоговые result-узлы", ""]
        for result in results:
            lines.append(f"**{result.get('title') or result.get('owner_node_id')}**")
            for output in result.get("outputs") or []:
                if isinstance(output, Mapping):
                    lines.append(f"- {output.get('symbol') or output.get('quantity_id')} = `{output.get('display_value')}`")
            lines.append("")

    failures = [row for row in summary.get("fail_closed") or [] if isinstance(row, Mapping)]
    if failures:
        lines += ["### Fail-closed ограничения", ""]
        for failure in failures:
            lines.append(f"> **{failure.get('title') or failure.get('owner_node_id')}:** {failure.get('message') or 'blocked'}")
        lines.append("")

    lines += _governing_lines(summary.get("governing") or {})

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
        lines += [f"## {section.get('title_ru') or section.get('section_key')}", ""]
        for block_id in ids:
            lines += _block_lines(by_id[block_id])
            rendered.add(block_id)

    remaining = [block for block_id, block in by_id.items() if block_id not in rendered]
    if remaining:
        lines += ["## Дополнительные trace-блоки", ""]
        for block in sorted(remaining, key=lambda row: (int(row.get("sequence") or 0), str(row.get("report_block_id")))):
            lines += _block_lines(block)

    route = [row for row in report.get("selected_route") or [] if isinstance(row, Mapping)]
    if route:
        lines += ["## Активный маршрут DAG", ""]
        lines += _table(
            ["Шаг", "Edge", "От", "К", "Тип"],
            [[row.get("sequence"), row.get("selected_edge_id"), row.get("from_node_id"), row.get("to_node_id"), row.get("edge_type")] for row in route],
        )
        lines.append("")

    lines += [
        "## Аудит отчёта",
        "",
        f"- Markdown contract: `{REPORT_MARKDOWN_CONTRACT}`",
        "- Численные результаты отчётом не пересчитываются.",
        "- Формулы отчётом не вычисляются; подстановка чисел является текстовым представлением.",
        "- Табличная интерполяция отчётом не повторяется.",
        "- Условия маршрутизации отчётом не вычисляются повторно.",
        "- Числовые коэффициенты не интерпретируются как PASS/FAIL без явного boolean-результата runtime.",
        "- Governing-величины показываются только из explicit DAG-bound metadata + execution trace; глобальный governing отчётом не вычисляется.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"
