from __future__ import annotations

import json
from pathlib import Path

from standard_core.sp16_mech9_v090_ux_overlay import GRAPH_SUFFIX, transform_graph
from streamlit_expertise_report_v090 import _brittle_section, _fatigue_section


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
    binding = next(
        b for b in node["produces"]
        if b["quantity_id"] == "sp16_mech9_fatigue_annex_k_case_confirmed"
    )
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


def _report_row(qid, value):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "name_ru": qid,
        "symbol": None,
        "canonical_unit": None,
    }


def _report(values):
    return {
        "blocks": [
            {
                "title": "synthetic MECH9 trace block",
                "inputs": [],
                "outputs": [_report_row(k, v) for k, v in values.items()],
                "normative_refs": [],
            }
        ]
    }


def test_v090_fatigue_report_exposes_executed_n9_values():
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
    assert "приложения К" in text
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
    assert "формула (174)" in text
    assert "Z15" in text and "Z25" in text
