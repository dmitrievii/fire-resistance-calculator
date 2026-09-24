from __future__ import annotations

import copy

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireUIError
from standard_core.fire_ui14_manual_net_v092 import (
    MANUAL_MODE,
    MANUAL_SOURCE_KIND,
    MANUAL_SOURCE_TEXT_RU,
    _manual_net_executor,
    install_registry_remediation,
)
from standard_core.sp16_mech7_primary_workflow import _eq43_governing
import standard_core.sp16_mech8_interactions as mech8
from streamlit_weakening_report_v092 import weakening_section


def _base_values(*, iz=40_000_000.0, iy=4_000_000.0, wz=320_000.0, wy=80_000.0):
    return {
        "section_weakening_model": {
            "schema": "section_weakening_model_v0.92",
            "holes_present": True,
            "model": "central_web_bolt_hole_formula45_v1",
            "hole_diameter_mm": 20.0,
            "hole_pitch_mm": 80.0,
            "net_property_mode": MANUAL_MODE,
            "manual_net_properties": {
                "I_z_n_mm4": iz,
                "I_y_n_mm4": iy,
                "W_z_n_mm3": wz,
                "W_y_n_mm3": wy,
                "W_pl_z_eff_mm3": 360_000.0,
                "W_pl_y_eff_mm3": 90_000.0,
            },
        },
        "A_gross": 5000.0,
        "J_x": 50_000_000.0,
        "J_y": 5_000_000.0,
        "W_el_x_pos": 400_000.0,
        "W_el_x_neg": 400_000.0,
        "W_el_y_pos": 100_000.0,
        "W_el_y_neg": 100_000.0,
        "major_axis_is_x": True,
        "sp16_i_symmetry_class": "double_symmetric",
        "section_geometry_2d_normalized": {
            "template": "i_section",
            "h_mm": 250.0,
            "b_mm": 150.0,
            "tw_mm": 8.0,
            "tf_mm": 12.0,
        },
    }


def _report_row(qid, value, unit=None):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "canonical_unit": unit,
        "name_ru": qid,
        "symbol": None,
    }


def test_manual_net_keeps_area_geometry_derived_while_I_W_change():
    first = _manual_net_executor(_base_values(iz=40e6, iy=4e6, wz=320e3, wy=80e3), {})
    second = _manual_net_executor(_base_values(iz=32e6, iy=3.2e6, wz=250e3, wy=62e3), {})

    assert first["A_net"] == pytest.approx(5000.0 - 20.0 * 8.0)
    assert second["A_net"] == pytest.approx(first["A_net"])
    assert first["sp16_net_removed_area"] == pytest.approx(160.0)
    assert second["sp16_net_removed_area"] == pytest.approx(160.0)

    assert first["I_xn"] == pytest.approx(40e6)
    assert first["I_yn"] == pytest.approx(4e6)
    assert first["W_xn_min"] == pytest.approx(320e3)
    assert first["W_yn_min"] == pytest.approx(80e3)
    assert second["I_xn"] == pytest.approx(32e6)
    assert second["W_xn_min"] == pytest.approx(250e3)

    trace = first["net_section_geometry_2d"]["calculation_trace"]
    assert trace["route"] == "manual_net_properties_with_geometry_area"
    assert trace["manual_area_override_allowed"] is False
    assert trace["automatic_fallback_for_missing_manual_property"] is False
    assert all(row["source_kind"] in {MANUAL_SOURCE_KIND, "DERIVED_FROM_USER_INPUT_NET_PROPERTIES"} for row in trace["manual_properties"])


def test_manual_net_rejects_manual_area_override_and_missing_required_property():
    with_area = _base_values()
    with_area["section_weakening_model"]["manual_net_properties"]["A_net"] = 1234.0
    with pytest.raises(FireUIError, match="A_net is geometry-derived"):
        _manual_net_executor(with_area, {})

    incomplete = _base_values()
    del incomplete["section_weakening_model"]["manual_net_properties"]["W_y_n_mm3"]
    with pytest.raises(FireUIError, match="no automatic fallback"):
        _manual_net_executor(incomplete, {})


def test_manual_net_canonical_axes_are_not_blindly_renamed_when_catalog_major_axis_is_y():
    values = _base_values(iz=40e6, iy=4e6, wz=320e3, wy=80e3)
    values["major_axis_is_x"] = False
    out = _manual_net_executor(values, {})

    # Active z remains the strong user-entered value, but retained internal x
    # is now the weak source axis because explicit geometry evidence says so.
    assert out["I_yn"] == pytest.approx(40e6)
    assert out["I_xn"] == pytest.approx(4e6)
    assert out["W_yn_min"] == pytest.approx(320e3)
    assert out["W_xn_min"] == pytest.approx(80e3)


def test_mech7_eq43_utilization_changes_with_manual_net_inertia():
    common = {
        "ambient_complete_pointwise_stress_state": {
            "runtime_closed": True,
            "points": [{"id": "p1", "x_mm": 0.0, "y_mm": 100.0}],
        },
        "ambient_M_x": 10_000_000.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "Ry_formula": 250.0,
        "gamma_c_bending_strength": 1.0,
    }
    strong = {**common, **_manual_net_executor(_base_values(iz=40e6), {})}
    weak = {**common, **_manual_net_executor(_base_values(iz=20e6), {})}

    u_strong = _eq43_governing(strong, use_mx=True, use_my=False, use_b=False)
    u_weak = _eq43_governing(weak, use_mx=True, use_my=False, use_b=False)
    assert u_weak > u_strong
    assert u_weak == pytest.approx(2.0 * u_strong)


def test_mech8_class2_passes_exact_manual_W_to_eq50(monkeypatch):
    captured = []
    monkeypatch.setattr(mech8, "plastic_bending_applicability", lambda *args, **kwargs: {"permitted": True, "failed_gates": []})
    monkeypatch.setattr(mech8, "_table_e1", lambda values, alpha_f, my_zero: {"c_x": 1.0, "c_y": 1.0})
    monkeypatch.setattr(mech8, "plastic_shear_reduction_factor_eq52", lambda *args, **kwargs: 1.0)

    def fake_eq50(moment, c_x, beta, wx, ry, gamma):
        captured.append(wx)
        return abs(moment) / wx / max(ry * gamma, 1.0)

    monkeypatch.setattr(mech8, "plastic_bending_utilization_eq50", fake_eq50)

    values = {
        **_base_values(wz=321_000.0, wy=81_000.0),
        **_manual_net_executor(_base_values(wz=321_000.0, wy=81_000.0), {}),
        "ambient_N_force": 0.0,
        "ambient_M_x": 10_000_000.0,
        "ambient_M_y": 0.0,
        "ambient_Q_x": 1_000.0,
        "ambient_Q_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "ambient_axis_shear_state": {
            "clause_8_2_3_components": {
                "applicable": True,
                "tau_x_effective_n_mm2": 1.0,
                "tau_y_n_mm2": 0.0,
                "A_w_mm2": 1000.0,
                "A_f_one_flange_mm2": 500.0,
            }
        },
        "Rs_formula": 145.0,
        "fy_norm": 255.0,
        "Ry_formula": 250.0,
        "gamma_c_bending_strength": 1.0,
        "sp16_mech8_required_clause_checks_confirmed": True,
        "sp16_mech8_is_support_section": False,
        "sp16_mech8_annex_e1_section_type": "test-row",
        "sp16_mech8_equivalent_load_safety_factor": 1.0,
    }
    result = mech8._class2_plastic(values)

    assert result["status"] in {"PASS", "FAIL"}
    assert captured == [pytest.approx(321_000.0)]


def test_registry_wrapper_records_exact_manual_values_consumed_by_mech7_and_mech8():
    registry = ExecutionRegistry()
    registry.register("SP554_G_NET_SECTION_PROPERTIES", lambda values, node: {"unused": True})
    registry.register(
        "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER",
        lambda values, node: {
            "sp16_mech7_primary_evidence": {"evidence": {"interaction_N_M": {"status": "PASS"}}},
            "sp16_mech7_primary_binding_complete": True,
        },
    )
    registry.register(
        "SP16_C_MECH8_INTERACTION_BINDER",
        lambda values, node: {
            "sp16_mech8_primary_evidence": {"evidence": {"interaction_M_Q": {"status": "PASS"}}},
            "sp16_mech8_mq_binding_complete": True,
            "sp16_mech8_torsion_scope_reconciled": True,
        },
    )
    install_registry_remediation(registry)

    values = _base_values(wz=321_000.0, wy=81_000.0)
    values.update(_manual_net_executor(values, {}))
    values["sp16_section_class"] = "2"

    m7 = registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"](values, {})
    m7_consumed = m7["sp16_mech7_primary_evidence"]["evidence"]["interaction_N_M"]["details"]["manual_net_property_consumption"]
    assert m7_consumed["source_text_ru"] == MANUAL_SOURCE_TEXT_RU
    assert m7_consumed["consumed_runtime_quantities"]["A_net"] == pytest.approx(4840.0)
    assert m7_consumed["consumed_runtime_quantities"]["I_xn"] == pytest.approx(40_000_000.0)

    m8 = registry.executors["SP16_C_MECH8_INTERACTION_BINDER"](values, {})
    m8_consumed = m8["sp16_mech8_primary_evidence"]["evidence"]["interaction_M_Q"]["details"]["manual_net_property_consumption"]
    assert m8_consumed["source_kind"] == MANUAL_SOURCE_KIND
    assert m8_consumed["consumed_runtime_quantities"] == {
        "W_xn_min": pytest.approx(321_000.0),
        "W_yn_min": pytest.approx(81_000.0),
    }


def test_report_labels_manual_net_values_as_user_input_and_area_as_calculated():
    values = _base_values(wz=321_000.0, wy=81_000.0)
    out = _manual_net_executor(values, {})
    alpha = 80.0 / (80.0 - 20.0)
    consumption = {
        "schema": "sp16_v092_manual_net_consumer_evidence_v1",
        "source_kind": MANUAL_SOURCE_KIND,
        "source_text_ru": MANUAL_SOURCE_TEXT_RU,
        "consumed_runtime_quantities": {"W_xn_min": out["W_xn_min"]},
        "A_net_source": None,
    }
    report = {
        "blocks": [
            {
                "owner_node_id": "SP554_G_NET_SECTION_PROPERTIES",
                "outputs": [
                    _report_row("net_section_geometry_2d", out["net_section_geometry_2d"]),
                    _report_row("A_net", out["A_net"], "mm2"),
                ],
            },
            {
                "owner_node_id": "SP16_C_SHEAR_ALPHA45",
                "normative_refs": [{"standard_id": "SP16_2017", "section": "8", "clause": "8.2.1", "formula_ref": "(45)"}],
                "outputs": [_report_row("sp16_shear_hole_alpha45", alpha, "1")],
            },
            {
                "owner_node_id": "SP16_C_MECH8_INTERACTION_BINDER",
                "outputs": [
                    _report_row(
                        "sp16_mech8_primary_evidence",
                        {"evidence": {"interaction_M_Q": {"details": {"manual_net_property_consumption": consumption}}}},
                    )
                ],
            },
        ]
    }
    text = weakening_section(report)

    assert "Введите" not in text  # report describes evidence, not UI instructions
    assert MANUAL_SOURCE_TEXT_RU in text
    assert r"A_n=A-\Delta A" in text
    assert r"A_n=5 000-160=4 840\;\mathrm{мм^2}" in text
    assert "$I_{z,n}$ = **40 000 000 мм⁴**" in text
    assert "$W_{z,n}$ = **321 000 мм³**" in text
    assert "Использование в выполненных проверках СП 16" in text
    assert "321 000" in text
    assert "Площадь $A_n$ не является ручным параметром" in text
