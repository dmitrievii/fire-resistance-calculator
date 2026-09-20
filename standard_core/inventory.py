"""Inventory loading and summarisation utilities."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any


def load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    """
    Summary:
        Load a UTF-8 CSV audit inventory into a list of dictionaries.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Amendments No. 1-5
        Clause: Audit infrastructure
        Annex: None
        Equation/Table: None
        Audit ID: AUDIT-INFRA-CSV-001
        Normative status: no_code_explanatory

    Mathematical form:
        Not applicable; deterministic CSV deserialization.

    Parameters:
        path:
            Type: str | pathlib.Path
            Unit: not applicable
            Meaning: Path to an audit inventory CSV file.
            Valid range: Existing readable file.
            Source: package layout

    Returns:
        Type: list[dict[str, str]]
        Unit: not applicable
        Meaning: Inventory rows keyed by CSV headers.

    Assumptions:
        - The file uses UTF-8 or UTF-8 with BOM.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Units remain textual metadata in inventory columns.

    Applicability:
        - Audit inventory and report generation only.

    Limitations:
        - Does not validate semantic correctness of extracted standard content.

    Raises:
        FileNotFoundError: The requested inventory file does not exist.

    Examples:
        >>> rows = load_csv_rows("audit_inventory/equation_inventory.csv")
        >>> len(rows) > 0
        True

    Tests:
        Unit tests:
            - tests/test_equations.py::test_equation_inventory_shape
        Validation cases:
            - AUDIT-RUN-001

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def summarize_inventory(
    equation_rows: list[dict[str, str]],
    table_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Summary:
        Count equation and table inventory rows by implementation status.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Amendments No. 1-5
        Clause: Audit infrastructure
        Annex: None
        Equation/Table: Inventory summary
        Audit ID: AUDIT-INFRA-SUM-001
        Normative status: no_code_explanatory

    Mathematical form:
        count(status) for equation and table registries.

    Parameters:
        equation_rows:
            Type: list[dict[str, str]]
            Unit: rows
            Meaning: Equation inventory records.
            Valid range: Zero or more uniquely identified rows.
            Source: audit_inventory/equation_inventory.csv
        table_rows:
            Type: list[dict[str, str]]
            Unit: rows
            Meaning: Table inventory records.
            Valid range: Zero or more uniquely identified rows.
            Source: audit_inventory/table_inventory.csv

    Returns:
        Type: dict[str, Any]
        Unit: counts
        Meaning: Totals and status histograms.

    Assumptions:
        - Each row has an implementation_status field.

    Sign convention:
        - Counts are non-negative.

    Unit convention:
        - All returned numerical values are item counts.

    Applicability:
        - Release audit reporting.

    Limitations:
        - A classified row is not evidence that its technical extraction is correct.

    Raises:
        KeyError: A row omits implementation_status.

    Examples:
        >>> summarize_inventory([], [{{"implementation_status": "not_yet_implemented"}}])["total_tables"]
        1

    Tests:
        Unit tests:
            - tests/test_final_audit.py::test_final_audit_reports_unresolved_rows
        Validation cases:
            - AUDIT-RUN-001

    Implementation notes:
        - This function must not silently apply national choices.
        - Defaults must be explicit in the input configuration.
    """
    return {
        "total_equations": len(equation_rows),
        "equation_status_counts": dict(Counter(row["implementation_status"] for row in equation_rows)),
        "total_tables": len(table_rows),
        "table_status_counts": dict(Counter(row["implementation_status"] for row in table_rows)),
    }
