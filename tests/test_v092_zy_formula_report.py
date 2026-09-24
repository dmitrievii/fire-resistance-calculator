from __future__ import annotations

import pytest

from standard_core.sp16_mech7_v092_effective_length import EVIDENCE_QID
from standard_core.sp16_mech7_v092_phi_evidence import PHI_TRACE_SCHEMA
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


def _phi_evidence(curve: str, lambda_bar: float, final_phi: float, *, delta: float, radicand: float) -> dict:
    coefficients = {"a": (0.03, 0.06, 3.8), "b": (0.04, 0.09, 4.4), "c": (0.04, 0.14, 5.8)}
    alpha, beta, threshold = coefficients[curve]
    return {
        "schema": PHI_TRACE_SCHEMA,
        "normative_basis": "СП 16.13330.2017 с изм. №1–6, п. 7.1.3, формулы (8)–(9), таблица 7",
        "curve": curve,
        "alpha": alpha,
        "beta": beta,
        "lambda_bar": lambda_bar,
        "cap_threshold_lambda_bar": threshold,
        "final_phi": final_phi,
        "final_phi_source": "qualified_MECH7_runtime",
        "branch": "eq8_eq9_with_table7",
        "delta": delta,
        "eq8_radicand": radicand,
        "phi_eq8": final_phi,
        "cap_candidate": None,
        "cap_applied": False,
        "validated_against_runtime": True,
    }


def _trace() -> dict:
    return {
        "schema": "sp16_v092_effective_length_zy_trace_v1",
        "normative_basis": "СП 16.13330.2017 с изменениями 1–6, раздел 10",
        "axis_convention": {"z": "strong principal axis", "y": "weak principal axis"},
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
            "phi_evidence": _phi_evidence("b", 1.53694, 0.612345, delta=13.9876, radicand=102.345),
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
            "phi_evidence": _phi_evidence("c", 3.51301, 0.238765, delta=28.7654, radicand=341.234),
        },
        "governing_axis_by_phi": "y",
        "formula_chain": [
            "l_eff = Section-10 route result",
            "lambda = l_eff / i",
            "lambda_bar = lambda * sqrt(Ry/E)",
            "phi = SP16 Table 7 stability curve",
        ],
        "full_phi_evidence_contract": PHI_TRACE_SCHEMA,
    }


def _report(*, include_trace: bool = True, trace: dict | None = None) -> dict:
    rows = [_row("Ry_formula", 240.0, "MPa"), _row("E_norm", 206000.0, "MPa")]
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
    assert "По таблице 7 для оси z: $\\alpha=0.04$, $\\beta=0.09$, тип кривой **b**" in section
    assert r"\delta_{z}=9.87\left(1-\alpha+\beta\bar{\lambda}_{z}\right)+\bar{\lambda}_{z}^2" in section
    assert r"=9.87\left(1-0.04+0.09\cdot 1.53694\right)+1.53694^2=13.9876" in section
    assert r"\varphi_{8,z}=\frac{19.74}{\delta_{z}+\sqrt{\delta_{z}^2-39.48\bar{\lambda}_{z}^2}}" in section
    assert r"\varphi_{z}=\varphi_{8,z}=0.612345" in section
    assert "verified_analysis" in section
    assert r"\lambda_{y}=\frac{l_{ef,y}}{i_{y}}=\frac{3600}{35}=102.857" in section
    assert r"\bar{\lambda}_{y}=\lambda_{y}\sqrt{\frac{R_y}{E}}=102.857\sqrt{\frac{240}{206000}}=3.51301" in section
    assert "По таблице 7 для оси y: $\\alpha=0.04$, $\\beta=0.14$, тип кривой **c**" in section
    assert r"\delta_{y}=9.87\left(1-\alpha+\beta\bar{\lambda}_{y}\right)+\bar{\lambda}_{y}^2" in section
    assert r"\varphi_{y}=\varphi_{8,y}=0.238765" in section
    assert "**Определяющая по $\\varphi$ ось:** **y (слабая главная ось)**" in section
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


def test_full_phi_evidence_is_required_after_state_execution():
    bad = _trace()
    bad["z"].pop("phi_evidence")
    with pytest.raises(ValueError, match="full phi evidence for axis z is absent"):
        zy_stability_section(_report(trace=bad))


def test_governing_axis_is_read_from_runtime_trace_not_selected_by_report():
    trace = _trace()
    trace["z"]["phi"] = 0.01
    trace["z"]["phi_evidence"]["final_phi"] = 0.01
    trace["y"]["phi"] = 0.99
    trace["y"]["phi_evidence"]["final_phi"] = 0.99
    trace["governing_axis_by_phi"] = "y"
    section = zy_stability_section(_report(trace=trace))
    assert "**Определяющая по $\\varphi$ ось:** **y (слабая главная ось)**" in section
