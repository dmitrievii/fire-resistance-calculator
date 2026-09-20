"""Engineering Markdown renderer for REPORT-IR5.

The renderer is presentation-only. It never evaluates formulae or interpolates
normative data. LaTeX substitutions are text projections from trace-bound
REPORT-META templates via :mod:`standard_core.report_equations`.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from .report_equations import build_trace_bound_equation

REPORT_MARKDOWN_CONTRACT = "report_ir5_markdown_projection_v2"

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
        locator = ref.get("clause") or ref.get("section") or ref.get("table_ref") or ref.get("table") or ref.get("figure") or ""
        text = " ".join(str(x).strip() for x in (standard, locator) if x is not None and str(x).strip())
        if text:
            out.append(text)
    return "; ".join(out) if out else "—"


def _value(row: Mapping[str, Any]) -> str:
    value = _text(row.get("raw_value"))
    unit = row.get("canonical_unit")
    return f"{value} {unit}" if unit else value


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(_escape_cell(x) for x in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_escape_cell(x) for x in row) + " |" for row in rows)
    return lines


def _latex_equation_lines(block: Mapping[str, Any]) -> tuple[list[str], bool]:
    equation = build_trace_bound_equation(block)
    if not equation:
        return [], False
    lines: list[str] = []
    formula = equation.get("formula_latex")
    substitution = equation.get("substitution_result_latex") or equation.get("substitution_latex")
    if formula:
        lines += ["**Нормативная формула**", "", "$$", str(formula), "$$", ""]
    if substitution:
        lines += ["**Подстановка**", "", "$$", str(substitution), "$$", ""]
    missing = equation.get("missing_trace_bindings") or []
    if missing:
        lines += [f"> Не удалось заполнить trace-подстановку для: {', '.join(map(str, missing))}", ""]
    return lines, bool(substitution and equation.get("result_latex"))


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
            lines += ["", "```json", json.dumps(block["failure"], ensure_ascii=False, indent=2, sort_keys=True, default=str), "```", ""]
        return lines

    inputs = [row for row in block.get("inputs") or [] if isinstance(row, Mapping)]
    if inputs:
        lines += ["**Исходные величины шага**", ""]
        lines += _table(
            ["Обозначение", "Quantity", "Значение"],
            [[row.get("symbol") or row.get("quantity_id"), row.get("quantity_id"), _value(row)] for row in inputs],
        )
        lines.append("")

    latex_lines, latex_has_result = _latex_equation_lines(block)
    lines += latex_lines

    human = block.get("human_readable") or {}
    mode = human.get("mode")
    if mode == "formula_substitution":
        # If REPORT-META supplied a publication formula, the raw expression stays
        # in JSON audit evidence instead of cluttering the normal report. Legacy
        # nodes without metadata retain the old expression/substitution display.
        if not latex_lines:
            formula = human.get("formula_expression")
            substitution = human.get("substituted_expression")
            if formula:
                lines += ["**Расчётная формула — активное выражение из DAG**", "", "```text", str(formula), "```", ""]
            if substitution:
                lines += ["**Подстановка чисел**", "", "```text", str(substitution), "```", ""]
        if human.get("selected_case_index") is not None:
            lines += [f"Активная piecewise-ветвь: `case #{human.get('selected_case_index')}` (runtime evidence).", ""]
        results = [row for row in human.get("result_lines") or [] if isinstance(row, Mapping)]
        if results and not latex_has_result:
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
                [[row.get("role"), row.get("row_index"), json.dumps(row.get("row"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)] for row in runtime_rows],
            )
            lines.append("")
        for row in human.get("output_lines") or []:
            if not isinstance(row, Mapping):
                continue
            if row.get("formula_expression"):
                lines += ["**Интерполяционная формула**", "", "```text", str(row["formula_expression"]), "```", ""]
            if row.get("substituted_expression"):
                lines += ["**Подстановка по runtime-строкам**", "", "```text", str(row["substituted_expression"]), "```", ""]
            lines += [f"- **{row.get('symbol') or row.get('quantity_id')}** = `{row.get('display_result')}` — production lookup result", ""]

    elif mode == "route_decision":
        edge = human.get("selected_edge_id") or block.get("selected_edge_id")
        if edge:
            target = human.get("to_node_id")
            lines += [f"**Выбранная ветвь:** `{edge}`" + (f" → `{target}`" if target else ""), ""]

    outputs = [row for row in block.get("outputs") or [] if isinstance(row, Mapping)]
    if outputs and mode not in {"formula_substitution", "lookup_substitution"} and not latex_has_result:
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
        lines += _table(
            ["Область", "DAG node", "Величина", "Значение", "Норма"],
            [[row.get("scope_title_ru") or row.get("scope"), row.get("owner_node_id"), (row.get("quantity") or {}).get("symbol") or (row.get("quantity") or {}).get("quantity_id"), (row.get("quantity") or {}).get("display_value"), _refs(row.get("normative_refs"))] for row in rows],
        )
        lines += ["", "Каждая строка является отдельной governing-областью. Отчёт не вычисляет глобальный максимум/минимум.", ""]
    elif status == "DECLARED_BY_DAG_NOT_EXECUTED":
        lines += ["Governing-области объявлены в DAG-bound metadata, но соответствующие producer-узлы ещё не выполнены на текущем маршруте расчёта.", ""]
    else:
        lines += ["`NOT_DECLARED_BY_DAG` — governing criterion не выбирается отчётом эвристически.", ""]
    return lines


def render_report_markdown(report: Mapping[str, Any], *, title: str = "Расчёт огнестойкости стальной конструкции") -> str:
    if report.get("schema") != "fire_report_ir_v4":
        raise ValueError("Markdown renderer requires fire_report_ir_v4 / REPORT-IR5")

    summary = report.get("summary") or {}
    counts = summary.get("check_counts") or {}
    lines: list[str] = [
        f"# {title}", "", "## Идентификация расчёта", "",
        f"- **DAG:** `{report.get('graph_id')}`",
        f"- **DAG SHA-256:** `{report.get('graph_sha256')}`",
        f"- **Report IR:** `{report.get('schema')}` / `{report.get('contract')}`",
        f"- **Report SHA-256:** `{report.get('report_sha256')}`",
        f"- **Статус сессии:** `{report.get('session_status')}`",
        f"- **Текущий DAG node:** `{report.get('current_node_id')}`",
        "", "## Итоговая расчётная сводка", "",
        f"**Статус:** {_STATUS_RU.get(str(summary.get('summary_status')), _text(summary.get('summary_status')))}  ",
        f"**Область статуса:** `{summary.get('summary_status_scope')}`", "",
        f"Выполнено проверок: **{summary.get('check_count', 0)}**; PASS: **{counts.get('PASS', 0)}**; FAIL: **{counts.get('FAIL', 0)}**; неоднозначно: **{counts.get('UNRESOLVED', 0)}**.", "",
    ]

    checks = [row for row in summary.get("checks") or [] if isinstance(row, Mapping)]
    if checks:
        lines += ["### Выполненные проверки", ""]
        lines += _table(
            ["Шаг", "Проверка", "Норма", "Вердикт", "Результат"],
            [[row.get("sequence"), row.get("title"), _refs(row.get("normative_refs")), row.get("verdict"), "; ".join(f"{out.get('symbol') or out.get('quantity_id')} = {out.get('display_value')}" for out in row.get("outputs") or [] if isinstance(out, Mapping)) or "—"] for row in checks],
        )
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

    by_id = {str(block.get("report_block_id")): block for block in report.get("blocks") or [] if isinstance(block, Mapping)}
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
        lines += _table(["Шаг", "Edge", "От", "К", "Тип"], [[row.get("sequence"), row.get("selected_edge_id"), row.get("from_node_id"), row.get("to_node_id"), row.get("edge_type")] for row in route])
        lines.append("")

    lines += [
        "## Аудит отчёта", "",
        f"- Markdown contract: `{REPORT_MARKDOWN_CONTRACT}`",
        "- Численные результаты отчётом не пересчитываются.",
        "- LaTeX-подстановка формируется только текстовой заменой trace-bound placeholders.",
        "- Формулы отчётом не вычисляются; raw execution expression остаётся в Report IR JSON.",
        "- Табличная интерполяция отчётом не повторяется.",
        "- Условия маршрутизации отчётом не вычисляются повторно.",
        "- Числовые коэффициенты не интерпретируются как PASS/FAIL без явного boolean-результата runtime.",
        "- Governing-величины показываются только из explicit DAG-bound metadata + execution trace.", "",
    ]
    return "\n".join(lines).rstrip() + "\n"
