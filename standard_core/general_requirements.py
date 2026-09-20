"""General СП 16.13330.2017 requirements that are safely expressible as exact categorical data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_1: dict[str, Any] = json.loads((_DATA_DIR / "table_1_working_condition_factors.json").read_text(encoding="utf-8"))
_TABLE_1_BY_ID = {row["case_id"]: row for row in _TABLE_1["rows"]}


def table_1_working_condition_factor(case_id: str) -> float:
    """
    Summary:
        Return the exact working-condition factor gamma_c for an explicitly classified Table 1 case.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Amendments No. 1-5
        Clause: 4.3.2
        Annex: None
        Equation/Table: Table 1, including Note 5 default
        Audit ID: SP16-TBL-1
        Normative status: normative

    Mathematical form:
        Exact categorical lookup; no interpolation, geometry recognition, or automatic combination of factors.

    Parameters:
        case_id:
            Type: str
            Unit: not applicable
            Meaning: Explicit audited identifier of the applicable Table 1 row or Note 5 default.
            Valid range: one of the case_id values in data/table_1_working_condition_factors.json
            Source: engineering classification against Table 1

    Returns:
        Type: float
        Unit: dimensionless
        Meaning: Working-condition factor gamma_c.

    Assumptions:
        - The engineer/caller has selected the correct Table 1 category and considered the notes on combined use.

    Sign convention:
        - Not applicable.

    Unit convention:
        - gamma_c is dimensionless.

    Applicability:
        - Table 1 cases and the explicit Note 5 default of clause 4.3.2.

    Limitations:
        - Does not infer the case from building type, geometry, loading, figure classification, steel grade, or connection details.
        - Does not multiply multiple factors; the Table 1 notes remain an explicit engineering routing requirement.

    Raises:
        TypeError: case_id is not a string.
        ValueError: case_id is unknown.

    Examples:
        >>> table_1_working_condition_factor("default_unlisted_case_note_5")
        1.0

    Tests:
        Unit tests:
            - tests/test_final_annex_and_release_consolidation.py::test_table_1_note_5_and_representative_rows
        Validation cases:
            - none; exact normative data are covered by direct transcription tests

    Implementation notes:
        - Note 5 is represented explicitly rather than as a silent package-wide default.
        - Exact categorical lookup is fail-closed for unrecognized cases.
    """
    if not isinstance(case_id, str):
        raise TypeError("case_id must be a string")
    try:
        return float(_TABLE_1_BY_ID[case_id]["gamma_c"])
    except KeyError as exc:
        allowed = ", ".join(sorted(_TABLE_1_BY_ID))
        raise ValueError(f"Unknown Table 1 case_id {case_id!r}; allowed values: {allowed}") from exc
