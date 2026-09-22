from __future__ import annotations

import json
from pathlib import Path

from standard_core.sp16_mech9_v090_ux_overlay import GRAPH_SUFFIX, transform_graph
from streamlit_expertise_report_v090 import (
    _brittle_section,
    _engineering_load_rows,
    _fatigue_section,
    _section_conclusion_v090,
    _section_fire_mechanics_v090,
    _section_inputs_v090,
    _slenderness_section,
    render_expertise_narrative_markdown_v090,
)


ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / "normative_graph" / "dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json"


def _graph():
    return transform_graph(json.loads(DAG.read_text(encoding="utf-8")))


def _qmap(graph):
    return {q["id"]: q for q in graph["quantities"]}


def _nmap(graph):
    return {n["id"]: n for n in graph["nodes"]}


def test_v090_graph_identity_and_conditional_requiredness():
    graph = _graph()
    assert GRAPH_SUFFIX in graph["graph_id"]
    node = _nmap(graph)["SP16_I_MECH9_BRITTLE_CONDITIONAL"]
    assert node["produces"]
    assert all(binding["required"] is False for binding in node["produces"])


def test_v090_annex_k_duplicate_confirmation_is_not_required():
    graph = _graph()
    node = _nmap(graph)["SP16_I_MECH9_FATIGUE_ORDINARY"]
    binding = next(b for b in node["produces"] if b["quantity_id"] == "sp16_mech9_fatigue_annex_k_case_confirmed")
    assert binding["required"] is False


def test_v090_all_mech9_textual_enum_values_have_user_labels():
    graph = _graph()
    for qid, quantity in _qmap(graph).items():
        if not qid.startswith("sp16_mech9_"):
            continue
        for option in quantity.get("enum_values") or []:
            value = option["value"]
            label = option["label"]
            if isinstance(value, str) and ("_" in value or value.startswith("K1-")):
                assert label != value, (qid, value)
                assert "_" not in label, (qid, label)


def test_v090_welded_question_uses_joint_semantics_not_profile_manufacture():
    graph = _graph()
    label = _qmap(graph)["sp16_mech9_brittle_welded_structure"]["name_ru"]
    assert "сварные соединения" in label
    assert "элементе или узле" in label


def _report_row(qid, value, *, name=None, symbol=None, unit=None):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "name_ru": name or qid,
        "symbol": symbol,
        "canonical_unit": unit,
    }


def _report(values):
    return {
        "blocks": [{
            "title": "synthetic MECH9 trace block",
            "inputs": [],
            "outputs": [_report_row(k, v) for k, v in values.items()],
            "normative_refs": [],
        }]
    }


def _rows_report(rows):
    return {
        "blocks": [{
            "title": "synthetic engineering trace",
            "inputs": [],
            "outputs": rows,
            "normative_refs": [],
        }]
    }


def test_v090_fatigue_report_exposes_executed_n9_values_and_localized_case():
    report = _report({
        "sp16_mech7_fatigue_required": True,
        "sp16_mech9_fatigue_load_cycles": 1_000_000,
        "sp16_mech9_fatigue_sigma_max": 80.0,
        "sp16_mech9_fatigue_sigma_min": -20.0,
        "sp16_mech9_fatigue_annex_k_case_id": "K1-03-FRICTION_CONNECTION",
    })
    evidence = {
        "fatigue": {
            "status": "PASS",
            "utilization": 0.5,
            "details": {
                "n9_result": {
                    "general_fatigue_check": {
                        "annex_k_case_id": "K1-03-FRICTION_CONNECTION",
                        "annex_k_element_group": 1,
                        "table_35_fatigue_resistance_n_mm2": 100.0,
                        "cycle_factor_alpha": 1.2,
                        "stress_asymmetry_ratio_rho": -0.25,
                        "table_36_asymmetry_factor_gamma_v": 1.3,
                        "equation_170_utilization": 0.5,
                        "fatigue_resistance_cap_check": {"cap_utilization": 0.7, "pass": True},
                    }
                }
            },
        }
    }
    text = "\n".join(_fatigue_section(report, evidence))
    assert "формуле (170)" in text
    assert "коэффициент использования N9" in text
    assert "По приложению К" in text
    assert "фрикционное соединение" in text
    assert "K1-03-FRICTION_CONNECTION" not in text
    assert "PASS" in text


def test_v090_section13_report_shows_only_applicable_checks_and_lamellar_result():
    report = _report({"sp16_mech7_brittle_required": True})
    evidence = {
        "brittle_fracture": {
            "status": "PASS",
            "details": {
                "n10_result": {
                    "general_prevention": {
                        "clause_13_2_checks": {
                            "weld_intersections_avoided": {"applicable": True, "confirmed": True},
                            "minimum_section_thickness_for_guillotine_or_punching": {"applicable": False, "confirmed": True},
                        },
                        "failed_requirements": [],
                    },
                    "lamellar_tearing": {
                        "required": True,
                        "table_37_factors_percent": {
                            "psi_zf": 5.0,
                            "psi_zt": 3.0,
                            "psi_zsh": 2.0,
                            "psi_zj": 4.0,
                            "psi_zs": -2.0,
                        },
                        "equation_174_base_risk_percent": 12.0,
                        "adjusted_risk_percent": 12.0,
                        "required_z_quality_group": "Z15",
                        "selected_z_quality_group": "Z25",
                        "selected_quality_meets_minimum_group": True,
                        "governing_utilization": 0.8,
                    },
                }
            },
        }
    }
    text = "\n".join(_brittle_section(report, evidence))
    assert "Исключение пересечений сварных швов" in text
    assert "Минимальная толщина при гильотинной" not in text
    assert "Формула (174)" in text
    assert "Z15" in text and "Z25" in text


def test_v090_primary_loads_use_sp16_natural_axes_engineering_units_and_drop_zeroes():
    report = _report({
        "ambient_N_force": -1000.0,
        "ambient_M_x": 2_000_000.0,
        "ambient_M_y": 0.0,
        "ambient_T_torsion": 4_000_000.0,
        "ambient_Q_x": 3000.0,
        "ambient_Q_y": 0.0,
        "ambient_B_bimoment": 5_000_000_000.0,
    })
    rows = _engineering_load_rows(report)
    assert rows == [
        ("N", -1.0, "кН"),
        ("M_z", 2.0, "кН·м"),
        ("M_x", 4.0, "кН·м"),
        ("Q_z", 3.0, "кН"),
        ("B", 5.0, "кН·м²"),
    ]


def test_v090_weakening_precedes_actions_and_raw_runtime_axis_ids_do_not_leak():
    report = _rows_report([
        _report_row("hole_d", 30.0, name="Диаметр отверстия стенки", symbol="d", unit="mm"),
        _report_row("hole_s", 100.0, name="Шаг отверстий", symbol="s", unit="mm"),
        _report_row("ambient_M_x", 2_000_000.0, name="ambient: изгибающий момент Mx", unit="Nmm"),
        _report_row("ambient_M_y", 0.0, name="ambient: изгибающий момент My", unit="Nmm"),
    ])
    text = "\n".join(_section_inputs_v090(report))
    assert text.index("Ослабления сечения") < text.index("Расчётные усилия")
    assert "$M_z$ = **2 кН·м**" in text
    assert "$M_y$" not in text
    assert "ambient_M_x" not in text
    assert "Ненулевые силовые факторы" not in text


def test_v090_slenderness_is_explicit_pending_instead_of_empty_section():
    text = "\n".join(_slenderness_section(_report({})))
    assert "Расчётные длины и гибкости" in text
    assert "PENDING" in text
    assert "l_{ef}" in text


def test_v090_sp16_to_sp554_handoff_is_explicit():
    report = _rows_report([
        _report_row("SP16_MECHANICAL_PASS", True, name="SP16_MECHANICAL_PASS"),
        _report_row("eta_governing", 0.72, name="Управляющий коэффициент использования", symbol="η"),
    ])
    text = "\n".join(_section_fire_mechanics_v090(report))
    assert "Передача результатов СП 16 → СП 554" in text
    assert "Механический gate СП 16: **PASS**" in text
    assert "0.72" in text


def test_v090_conclusion_uses_explicit_compliance_boolean_and_r_designation():
    report = _rows_report([
        _report_row("R_protected", 92.4, name="Фактический предел с огнезащитой", symbol="R_prot", unit="min"),
        _report_row("R_required", 90.0, name="Требуемый предел огнестойкости", symbol="R_req", unit="min"),
        _report_row("protected_compliance", True, name="Соответствие с огнезащитой"),
    ])
    text = "\n".join(_section_conclusion_v090(report))
    assert "R_{fact}" in text and "R_{req}" in text
    assert "\\ge" in text
    assert "R90" in text
    assert "R90 — PASS" in text


def test_v090_conclusion_does_not_recompute_pass_fail_from_numbers():
    report = _rows_report([
        _report_row("R_protected", 100.0, name="Фактический предел с огнезащитой", symbol="R_prot", unit="min"),
        _report_row("R_required", 90.0, name="Требуемый предел огнестойкости", symbol="R_req", unit="min"),
        _report_row("protected_compliance", False, name="Соответствие с огнезащитой"),
    ])
    text = "\n".join(_section_conclusion_v090(report))
    assert "$$ R_{fact} < R_{req} $$" in text
    assert "R90 — FAIL" in text
    assert "\\ge" not in text


def test_v090_full_report_has_required_engineering_order_and_default_detail_level():
    text = render_expertise_narrative_markdown_v090(_report({}))
    headings = [
        "## 1. Исходные данные",
        "## 2. Материал и сечение",
        "## 3. Проверка несущей способности по СП 16",
        "## 4. Расчёт при пожаре по СП 554",
        "## 5. Теплотехнический расчёт",
        "## 6. Заключение",
    ]
    positions = [text.index(h) for h in headings]
    assert positions == sorted(positions)
    assert "Уровень детализации: Расчётный" in text
