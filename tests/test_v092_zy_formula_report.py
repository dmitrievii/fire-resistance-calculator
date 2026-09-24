from __future__ import annotations

import pytest

from standard_core.sp16_mech7_v092_effective_length import EVIDENCE_QID
from streamlit_expertise_report_v092_zy import (
    replace_zy_stability_section,
    zy_stability_section,
)


def _row(qid: str, value, unit: str | None = None) -> dict:
    return {
        "quantity_id": qid,
        "raw_value": value,
        "canonical_unit": unit,
        "name_ru": qid,
        "symbol": qid,
    }


def _trace() -> dict:
    return {
        "schema": "sp16_v092_effective_length_zy_trace_v1",
        "normative_basis": "СП 16.13330.2017 с изменениями 1–6, раздел 10",
        "axis_convention": {
            "z": "strong principal axis",
            "y": "weak principal axis",
        },
        "z": {
            "route": {
                "method": "table30",
                "scheme_id": "S2",
                "mu": 0.7,
                "member_length_mm": 4500.0,
                "normative_scope": "SP16 10.3.3 Table 30 + Eq.(140)",
            },
            "radius_mm": 70.0,
            "effective_length_mm": 3150.0,
            "lambda": 45.0,
            "lambda_bar": 1.53694,
            "curve": "b",
            "phi": 0.612345,
        },
        "y": {
            "route": {
                "method": "verified_analysis",
                "effective_length_mm": 3600.0,
                "basis": "qualified frame analysis",
                "normative_scope": "explicit source-traced SP16 Section 10 route",
            },
            "radius_mm": 35.0,
            "effective_length_mm": 3600.0,
            "lambda": 102.857,
            "lambda_bar": 3.51301,
            "curve": "c",
            "phi": 0.238765,
        },
        "governing_axis_by_phi": "y",
        "formula_chain": [
            "l_eff = Section-10 route result",
            "lambda = l_eff / i",
            "lambda_bar = lambda * sqrt(Ry/E)",
            "phi = SP16 Table 7 stability curve",
        ],
    }


def _report(*, include_trace: bool = True, trace: dict | None = None) -> dict:
    rows = [
        _row("Ry_formula", 240.0, "MPa"),
        _row("E_norm", 206000.0, "MPa"),
    ]
    if include_trace:
        rows.append(_row(EVIDENCE_QID, trace or _trace()))
    return {
        "blocks": [
            {
                "owner_node_id": "SP16_C_V075_EFFECTIVE_LENGTH_ZY_STATE",
                "inputs": [],
                "outputs": rows,
            }
        ]
    }


def test_no_runtime_trace_removes_retained_premature_formula_section():
    old = r"""## 3. Проверка несущей способности по СП 16

### 3.1 Расчётные длины и гибкости

$$i=\sqrt{I/A},\qquad l_{ef}=\mu L$$

### 3.2 Проверка центрального сжатия и определяющий результат

Результат появится позже.
"""

    rendered = replace_zy_stability_section(old, _report(include_trace=False))

    assert "### 3.1" not in rendered
    assert r"l_{ef}=\mu L" not in rendered
    assert "### 3.2 Проверка центрального сжатия" in rendered


def test_executed_trace_renders_formula_substitution_result_for_both_canonical_axes():
    section = zy_stability_section(_report())

    assert "Ось z — сильная главная ось" in section
    assert "Ось y — слабая главная ось" in section
    assert "$I_z$, $W_z$, $i_z$" in section
    assert "$I_y$, $W_y$, $i_y$" in section

    assert r"l_{ef,z}=\mu_{z}L=0.7\cdot 4500=3150\;\mathrm{mm}" in section
    assert r"\lambda_{z}=\frac{l_{ef,z}}{i_{z}}=\frac{3150}{70}=45" in section
    assert r"\bar{\lambda}_{z}=\lambda_{z}\sqrt{\frac{R_y}{E}}=45\sqrt{\frac{240}{206000}}=1.53694" in section
    assert r"\varphi_{z}=\varphi(\bar{\lambda}_{z},\;\text{кривая }b)=\varphi(1.53694,\;b)=0.612345" in section

    assert "verified_analysis" in section
    assert r"\lambda_{y}=\frac{l_{ef,y}}{i_{y}}=\frac{3600}{35}=102.857" in section
    assert r"\bar{\lambda}_{y}=\lambda_{y}\sqrt{\frac{R_y}{E}}=102.857\sqrt{\frac{240}{206000}}=3.51301" in section
    assert r"\varphi_{y}=\varphi(\bar{\lambda}_{y},\;\text{кривая }c)=\varphi(3.51301,\;c)=0.238765" in section

    assert "Определяющая по $\\varphi$ ось:** **y (слабая главная ось)**" in section
    assert "presentation-слой их не пересчитывает" in section


def test_active_zy_report_does_not_reintroduce_legacy_principal_x_semantics():
    section = zy_stability_section(_report())

    forbidden = ("I_x", "W_x", "i_x", "ось x", "principal x")
    assert all(token not in section for token in forbidden)
    assert "I_z" in section and "I_y" in section


def test_runtime_trace_schema_and_axis_convention_are_fail_closed():
    bad = _trace()
    bad["axis_convention"] = {"z": "legacy x alias", "y": "weak principal axis"}
    with pytest.raises(ValueError, match="non-canonical principal-axis evidence"):
        zy_stability_section(_report(trace=bad))


def test_governing_axis_is_read_from_runtime_trace_not_selected_by_report():
    trace = _trace()
    # Deliberately make phi_z numerically smaller while retaining runtime's
    # governing-axis field = y. A presentation layer that recomputes/min-selects
    # would switch to z; the correct renderer must continue to report y.
    trace["z"]["phi"] = 0.01
    trace["y"]["phi"] = 0.99
    trace["governing_axis_by_phi"] = "y"

    section = zy_stability_section(_report(trace=trace))
    assert "Определяющая по $\\varphi$ ось:** **y (слабая главная ось)**" in section
