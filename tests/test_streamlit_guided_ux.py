from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import streamlit_guided_ux as ux
import streamlit_guided_ux_v071 as ux71


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


def test_v071_catalog_labels_cover_indexed_section_properties_without_interpreting_index():
    core = SimpleNamespace(_fmt=lambda value: str(value))

    cases = {
        "Wx1_mm3": ("Момент сопротивления", "Wx1", "mm³"),
        "Wy2_mm3": ("Момент сопротивления", "Wy2", "mm³"),
        "Ix1_mm4": ("Момент инерции", "Ix1", "mm⁴"),
        "Sx1_mm3": ("Статический момент", "Sx1", "mm³"),
        "ix1_mm": ("Радиус инерции", "ix1", "mm"),
    }
    for key, expected in cases.items():
        line = ux71._profile_line(core, key, 123.4)
        for token in expected:
            assert token in line
        assert f"`{key}`" not in line

    assert "`unknown_property`" in ux71._profile_line(core, "unknown_property", 1.0)


def test_v071_gamma_ct_preflight_is_visible_before_special_route_and_preserves_field():
    card = _card(_field("gost27751_special_check", "boolean"))

    patched = ux71._humanize_card(card)
    warning = str((patched.get("notes") or {}).get("normative_warning") or "")

    assert "γct = 1,1" in warning
    assert "формулами (9)–(11) СП 554" in warning
    assert "fail-closed" in warning
    assert "вручную не вводится" in warning
    assert patched["fields"] == card["fields"]


def test_v071_guided_install_is_idempotent_across_streamlit_reruns():
    def generic(*args, **kwargs):
        return args, kwargs

    def options(*args, **kwargs):
        return []

    def noninteractive(*args, **kwargs):
        return None

    core = SimpleNamespace(
        _render_generic=generic,
        _generic_options=options,
        _render_noninteractive=noninteractive,
        _render_profile_catalog=generic,
        _render_material=generic,
    )

    ux71.install(core)
    first = {
        "generic": core._render_generic,
        "options": core._generic_options,
        "noninteractive": core._render_noninteractive,
        "profile": core._render_profile_catalog,
        "material": core._render_material,
    }
    ux71.install(core)

    assert core._render_generic is first["generic"]
    assert core._generic_options is first["options"]
    assert core._render_noninteractive is first["noninteractive"]
    assert core._render_profile_catalog is first["profile"]
    assert core._render_material is first["material"]


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
    base_source = (ROOT / "streamlit_guided_ux.py").read_text(encoding="utf-8")
    hotfix_source = (ROOT / "streamlit_guided_ux_v071.py").read_text(encoding="utf-8")

    assert "gamma_ct" not in base_source.lower()
    assert "SP554_C_GAMMA_CT_8_1" not in base_source
    assert "SP554_C_GAMMA_CT_8_1" not in hotfix_source
