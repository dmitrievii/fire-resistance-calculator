from pathlib import Path

from standard_core.final_audit import audit_public_docstrings

ROOT=Path(__file__).resolve().parents[1]


def test_public_api_docstrings():
    result=audit_public_docstrings(ROOT/"standard_core")
    assert result["docstrings_failed"]==0,result["missing_sections"]
    assert result["public_functions_checked"]>=25
