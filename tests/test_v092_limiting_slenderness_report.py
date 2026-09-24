from __future__ import annotations

import copy

import pytest

from standard_core.sp16_mech7_v092_slenderness_evidence import (
    EVIDENCE_KEY,
    build_limiting_slenderness_trace,
)
from streamlit_expertise_report_v092_slenderness import limiting_slenderness_section


def _values(*, row_id: str = "2b", group4: bool = False, lambda_y: float = 100.0) -> dict:
    return {
        "ambient_N_force": -600_000.0,
        "sp16_lambda_z_geom": 80.0,
        "sp16_lambda_y_geom": lambda_y,
        "phi_z_sp16": 0.60,
        "phi_y_sp16": 0.50,
        "A_gross": 5000.0,
        "Ry_formula": 240.0,
        "gamma_c_compression": 1.0,
        "sp16_mech7_table32_row": row_id,
        "sp16_mech7_group4_slenderness_increase": group4,
    }


def _report(trace: dict, *, status: str | None = None, passed: bool | None = None, validated: bool = True) -> dict:
    check = trace["check"]
    binder_pass = bool(check["pass"]) if passed is None else passed
    binder_status = ("PASS" if binder_pass else "FAIL") if status is None else status
    row = {
        "status": binder_status,
        "utilization": check["utilization"],
        "pass": binder_pass,
        "calculation_trace": trace,
        "calculation_trace_validated_against_binder": validated,
    }
    bundle = {"evidence": {EVIDENCE_KEY: row}}
    return {
        "blocks": [{
            "owner_node_id": "SP16_C_MECH7_PRIMARY_BINDER",
            "inputs": [],
            "outputs": [{
                "quantity_id": "sp16_mech7_primary_evidence",
                "raw_value": bundle,
                "canonical_unit": None,
                "name_ru": "SP16 MECH7 primary evidence",
                "symbol": None,
            }],
        }]
    }


def test_table32_report_renders_full_alpha_limit_utilization_and_binder_verdict_chain():
    trace = build_limiting_slenderness_trace(_values())
    section = limiting_slenderness_section(_report(trace))

    assert "таблица 32, строка 2b" in section
    assert "минимальный коэффициент устойчивости по оси **y**" in section
    assert "максимальную $\\lambda$ по оси **y**" in section
    assert r"\alpha_{raw}=\frac{|N|}{\varphi A R_y\gamma_c}" in section
    assert r"=\frac{600000}{0.5\cdot 5000\cdot 240\cdot 1}=1" in section
    assert r"\alpha=\max(\alpha_{raw},\alpha_{min})=\max(1,0.5)=1" in section
    assert "Строка 2b таблицы 32: `220-40*alpha`" in section
    assert r"\lambda_{u,base}=220-40\alpha=220-40\cdot 1=180" in section
    assert r"\lambda_u=\lambda_{u,base}=180" in section
    assert r"\lambda=\max(\lambda_z,\lambda_y)=\max(80,100)=100" in section
    assert r"\eta_\lambda=\frac{\lambda}{\lambda_u}=\frac{100}{180}=0.555556" in section
    assert r"**PASS:** $\lambda \le \lambda_u$" in section
    assert "Статус взят из MECH7 binder evidence" in section


def test_table32_report_explains_explicit_member_classification_and_uses_only_canonical_z_y_axes():
    trace = build_limiting_slenderness_trace(_values(row_id="4"))
    section = limiting_slenderness_section(_report(trace))

    assert "**Классификация элемента:** 4 — Основные колонны." in section
    assert "явной инженерной классификацией пользователя" in section
    assert "не выводит её из типа профиля" in section
    assert "скрытое значение по умолчанию" in section
    assert "увеличение для группы 4 не применяется" in section
    assert r"\lambda_z" in section and r"\lambda_y" in section
    assert r"\lambda_x" not in section
    assert "ось **x**" not in section


def test_group4_factor_is_rendered_only_when_runtime_trace_says_it_applies():
    trace = build_limiting_slenderness_trace(_values(group4=True))
    section = limiting_slenderness_section(_report(trace))

    assert "группа 4" in section
    assert r"\lambda_u=1.1\lambda_{u,base}=1.1\cdot 180=198" in section
    assert r"\frac{100}{198}=0.505051" in section


def test_renderer_projects_alpha_min_from_trace_and_has_no_hidden_point_five_constant():
    trace = copy.deepcopy(build_limiting_slenderness_trace(_values()))
    trace["alpha"]["raw"] = 0.4
    trace["alpha"]["minimum"] = 0.6
    trace["alpha"]["result"] = 0.6

    section = limiting_slenderness_section(_report(trace))

    assert r"\max(0.4,0.6)=0.6" in section
    assert r"\max(0.4,0.5)" not in section


def test_fail_verdict_is_projected_from_binder_evidence_not_inferred_by_renderer():
    trace = build_limiting_slenderness_trace(_values(lambda_y=220.0))
    assert trace["check"]["pass"] is False

    section = limiting_slenderness_section(_report(trace))

    assert r"**FAIL:** $\lambda > \lambda_u$" in section
    assert "Статус взят из MECH7 binder evidence" in section


def test_deferred_or_absent_completed_evidence_produces_no_table32_report_section():
    report = {
        "blocks": [{
            "outputs": [{
                "quantity_id": "sp16_mech7_primary_evidence",
                "raw_value": {"evidence": {EVIDENCE_KEY: {"status": "DEFERRED"}}},
            }]
        }]
    }
    assert limiting_slenderness_section(report) == ""


def test_report_fails_closed_if_trace_is_not_binder_validated():
    trace = build_limiting_slenderness_trace(_values())
    with pytest.raises(ValueError, match="trace is not validated against binder"):
        limiting_slenderness_section(_report(trace, validated=False))


def test_report_fails_closed_on_trace_binder_verdict_mismatch():
    trace = build_limiting_slenderness_trace(_values())
    with pytest.raises(ValueError, match="trace/binder verdict mismatch"):
        limiting_slenderness_section(_report(trace, status="FAIL", passed=False))


def test_report_fails_closed_when_binder_status_and_pass_flag_disagree():
    trace = build_limiting_slenderness_trace(_values())
    with pytest.raises(ValueError, match="binder status/pass fields are inconsistent"):
        limiting_slenderness_section(_report(trace, status="FAIL", passed=True))
