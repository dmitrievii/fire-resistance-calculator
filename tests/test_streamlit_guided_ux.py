from __future__ import annotations

from pathlib import Path

import streamlit_guided_ux as ux


ROOT = Path(__file__).resolve().parents[1]


def _card(*fields):
    return {
        "node_id": "TEST",
        "submit_shape": "object",
        "fields": list(fields),
        "presentation": {},
    }


def _field(qid: str, data_type: str = "string"):
    return {"quantity_id": qid, "data_type": data_type}


def test_guided_defaults_do_not_classify_table9_or_table10_from_profile_geometry():
    card = _card(
        _field("sp16_mech7_table9_group"),
        _field("sp16_mech7_table10_group"),
        _field("sp16_mech7_flange_edge_stiffened", "boolean"),
        _field("sp16_mech7_fatigue_required", "boolean"),
        _field("sp16_mech7_brittle_required", "boolean"),
    )

    payload = ux._with_guided_defaults(object(), card, {})

    assert "sp16_mech7_table9_group" not in payload
    assert "sp16_mech7_table10_group" not in payload
    assert "sp16_mech7_flange_edge_stiffened" not in payload
    assert payload["sp16_mech7_fatigue_required"] is False
    assert payload["sp16_mech7_brittle_required"] is False


def test_guided_defaults_preserve_explicit_engineering_classification():
    card = _card(
        _field("sp16_mech7_table9_group"),
        _field("sp16_mech7_table10_group"),
        _field("sp16_mech7_flange_edge_stiffened", "boolean"),
    )
    original = {
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    }

    payload = ux._with_guided_defaults(object(), card, original)

    assert payload == original
    assert payload is not original


def test_table9_table10_cards_explain_manual_engineering_classification():
    card = _card(
        _field("sp16_mech7_table9_group"),
        _field("sp16_mech7_table10_group"),
        _field("sp16_mech7_flange_edge_stiffened", "boolean"),
    )

    patched = ux._humanize_mech7_card(card)
    guidance = "\n".join((patched.get("presentation") or {}).get("guidance") or [])

    assert "явной инженерной классификации" in guidance
    assert "не записывает" in guidance
    assert "автоматически" in guidance


def test_sp16_completion_diagnostics_exposes_exact_unresolved_rows():
    env = {
        "state": {
            "ledger": [
                {
                    "quantity_id": "sp16_mechanical_verification",
                    "value": {
                        "gate_status": "INCOMPLETE_FAIL_CLOSED",
                        "unresolved_check_ids": ["local_stability_flange", "fatigue"],
                        "failed_check_ids": [],
                        "rows": [
                            {
                                "id": "section_compression",
                                "label": "Section compression",
                                "status": "PASS",
                            },
                            {
                                "id": "local_stability_flange",
                                "label": "Flange local stability",
                                "status": "DEFERRED",
                                "reason": "Table 10 diagram group/edge-stiffener classification is missing",
                                "evidence_source": "SP16-MECH7",
                                "normative_scope": ["SP16 7.3.8 Table 10"],
                            },
                            {
                                "id": "fatigue",
                                "label": "Fatigue",
                                "status": "CONTEXT_UNRESOLVED",
                                "reason": "fatigue applicability is not classified",
                            },
                        ],
                    },
                }
            ]
        }
    }

    diag = ux._sp16_completion_diagnostics(env)

    assert diag is not None
    assert diag["gate_status"] == "INCOMPLETE_FAIL_CLOSED"
    assert [row["id"] for row in diag["unresolved"]] == ["local_stability_flange", "fatigue"]
    assert diag["unresolved"][0]["reason"].startswith("Table 10")
    assert diag["failed"] == []


def test_sp16_completion_diagnostics_keeps_fail_separate_from_incomplete():
    env = {
        "state": {
            "ledger": [
                {
                    "quantity_id": "sp16_mechanical_verification",
                    "value": {
                        "gate_status": "FAIL",
                        "unresolved_check_ids": [],
                        "failed_check_ids": ["section_compression"],
                        "rows": [
                            {
                                "id": "section_compression",
                                "label": "Section compression",
                                "status": "FAIL",
                                "utilization": 1.12,
                            }
                        ],
                    },
                }
            ]
        }
    }

    diag = ux._sp16_completion_diagnostics(env)

    assert diag is not None
    assert [row["id"] for row in diag["failed"]] == ["section_compression"]
    assert diag["unresolved"] == []


def test_guided_ux_does_not_invent_gamma_ct_or_normative_formula():
    source = (ROOT / "streamlit_guided_ux.py").read_text(encoding="utf-8")

    assert "gamma_ct" not in source.lower()
    assert "SP554_C_GAMMA_CT_8_1" not in source
