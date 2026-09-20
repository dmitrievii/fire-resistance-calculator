import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows():
    with (ROOT / "audit_inventory/equation_inventory.csv").open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_equation_inventory_shape_and_unique_ids():
    rows = _rows()
    assert len(rows) == 241
    assert len({row["audit_id"] for row in rows}) == len(rows)


def test_numbered_equations_through_224_and_annex_d_zh_are_implemented_and_mapped():
    rows = {row["audit_id"]: row for row in _rows()}
    implemented = {"SP16-EQ-001", "SP16-EQ-002", "SP16-EQ-004", "SP16-EQ-005", "SP16-EQ-006", "SP16-EQ-007", "SP16-EQ-007A", "SP16-EQ-008", "SP16-EQ-009", *{f"SP16-EQ-{number:03d}" for number in range(10, 225)}, "SP16-EQ-Д-001", "SP16-EQ-Д-002", "SP16-EQ-Д-004", *{f"SP16-EQ-Ж-{number:03d}" for number in range(1, 14)}}
    assert {rows[item]["implementation_status"] for item in implemented} == {"implemented"}
    assert all(rows[item]["planned_function"] for item in implemented)


def test_excluded_equation_three_is_not_invented():
    row = next(row for row in _rows() if row["audit_id"] == "SP16-EQ-003")
    assert row["implementation_status"] == "no_code_explanatory"
    assert row["planned_function"] == ""


def test_all_numbered_equations_are_implemented_or_explicitly_classified():
    excluded = {"SP16-EQ-001", "SP16-EQ-002", "SP16-EQ-003", "SP16-EQ-004", "SP16-EQ-005", "SP16-EQ-006", "SP16-EQ-007", "SP16-EQ-007A", "SP16-EQ-008", "SP16-EQ-009", *{f"SP16-EQ-{number:03d}" for number in range(10, 225)}, "SP16-EQ-Д-001", "SP16-EQ-Д-002", "SP16-EQ-Д-004", *{f"SP16-EQ-Ж-{number:03d}" for number in range(1, 14)}}
    rows = [row for row in _rows() if row["audit_id"] not in excluded]
    assert rows == []
