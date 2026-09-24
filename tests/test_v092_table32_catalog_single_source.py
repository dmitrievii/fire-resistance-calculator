from __future__ import annotations

import pytest

from standard_core.effective_lengths_and_limiting_slenderness import table_32_catalog
from standard_core.sp16_mech7_v092_slenderness_evidence import build_limiting_slenderness_trace


def _values(row_id: str) -> dict:
    return {
        "ambient_N_force": -600_000.0,
        "sp16_lambda_z_geom": 80.0,
        "sp16_lambda_y_geom": 100.0,
        "phi_z_sp16": 0.60,
        "phi_y_sp16": 0.50,
        "A_gross": 5000.0,
        "Ry_formula": 240.0,
        "gamma_c_compression": 1.0,
        "sp16_mech7_table32_row": row_id,
        "sp16_mech7_group4_slenderness_increase": False,
    }


def _catalog_expression(raw) -> str:
    if isinstance(raw, str):
        return raw
    return format(float(raw), "g")


def test_every_table32_trace_row_is_sourced_from_audited_catalog_without_shadow_table():
    catalog = table_32_catalog()
    assert catalog["clause"] == "10.4.1"
    assert catalog["pages"] == [70, 71]
    assert catalog["alpha_min"] == pytest.approx(0.5)

    rows = catalog["rows"]
    assert set(rows) == {"1a", "1b", "2a", "2b", "3", "4", "5", "6", "7"}

    for row_id, raw_formula in rows.items():
        trace = build_limiting_slenderness_trace(_values(row_id))
        source = trace["table32_catalog_source"]

        assert trace["table32_row_id"] == row_id
        assert trace["table32_row_formula"]["expression"] == _catalog_expression(raw_formula)
        assert trace["alpha"]["minimum"] == pytest.approx(float(catalog["alpha_min"]))
        assert source["provider"] == "table_32_catalog"
        assert source["clause"] == catalog["clause"]
        assert source["pages"] == catalog["pages"]
        assert source["row_id"] == row_id
        assert source["raw_row_value"] == raw_formula
        assert source["alpha_min"] == pytest.approx(float(catalog["alpha_min"]))


def test_catalog_formula_metadata_and_authoritative_scalar_result_are_guarded_against_drift():
    # Row 2b is intentionally chosen because it has coefficients different from
    # the repeated 180-60*alpha / 210-60*alpha forms.
    trace = build_limiting_slenderness_trace(_values("2b"))

    assert trace["table32_row_formula"] == {
        "kind": "linear",
        "constant": 220.0,
        "alpha_coefficient": -40.0,
        "expression": "220-40*alpha",
    }
    # alpha = 1.0 for this fixture, hence Table 32 row 2b gives 180.
    assert trace["alpha"]["result"] == pytest.approx(1.0)
    assert trace["limiting_slenderness"]["base"] == pytest.approx(180.0)
    assert trace["limiting_slenderness"]["result"] == pytest.approx(180.0)
