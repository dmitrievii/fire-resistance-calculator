"""v0.110 regression: unified weakening editor must execute actual net properties.

These cases exercise the production FIRE-UI1.6 executor, the retained v0.92
manual-net adapter and the v0.109 guided bypass in a real calculation session.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import FireUIError
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui14_manual_net_v092 import install_registry_remediation
from standard_core.fire_ui16_workflow import _net_geometry
from streamlit_weakening_route_v0109 import (
    CANONICAL_HOLE_MODEL,
    _apply_atomic_route,
    _normalize_weakening_payload,
)

ROOT = Path(__file__).resolve().parents[1]
CARD = {"presentation": {"component": "section_weakening_editor"}}


def _values(*, holes=True, mode="automatic_geometry"):
    weakening = {
        "schema": "section_weakening_model_v0.49",
        "holes_present": holes,
        "model": CANONICAL_HOLE_MODEL if holes else "none",
    }
    if holes:
        weakening.update(
            hole_diameter_mm=22.0,
            hole_pitch_mm=80.0,
            net_property_mode=mode,
        )
    return {
        "section_weakening_model": weakening,
        "sp16_i_symmetry_class": "double_symmetric",
        "major_axis_is_x": True,
        "A_gross": 5000.0,
        "J_x": 80_000_000.0,
        "J_y": 10_000_000.0,
        "W_el_x_pos": 400_000.0,
        "W_el_x_neg": 400_000.0,
        "W_el_y_pos": 100_000.0,
        "W_el_y_neg": 100_000.0,
        "t_w": 8.0,
        "section_geometry_2d_normalized": {
            "template": "i_section",
            "tw_mm": 8.0,
            "h_mm": 400.0,
            "tf_mm": 12.0,
        },
    }


def _manual_bundle():
    return {
        "I_z_n_mm4": 70_000_000.0,
        "I_y_n_mm4": 9_000_000.0,
        "W_z_n_mm3": 350_000.0,
        "W_y_n_mm3": 90_000.0,
    }


def test_inline_automatic_geometry_deducts_area_inertias_and_moduli():
    values = _values()
    result = _net_geometry(values, {})
    expected_ix = 80_000_000.0 - 8.0 * 22.0**3 / 12.0
    expected_iy = 10_000_000.0 - 22.0 * 8.0**3 / 12.0

    assert result["A_net"] == pytest.approx(5000.0 - 22.0 * 8.0)
    assert result["I_xn"] == pytest.approx(expected_ix)
    assert result["I_yn"] == pytest.approx(expected_iy)
    assert result["W_xn_min"] == pytest.approx(expected_ix / 200.0)
    assert result["W_yn_min"] == pytest.approx(expected_iy / 100.0)
    assert result["I_xn"] < values["J_x"]
    assert result["I_yn"] < values["J_y"]
    trace = result["net_section_geometry_2d"]
    assert trace["mode"] == "representative_central_web_hole"
    assert trace["calculation_trace"]["presentation_recomputes_values"] is False
    assert result["sp16_shear_weakening_mode"] == "formula45"


def test_inline_mode_overrides_stale_legacy_area_only_quantity():
    values = _values()
    values["net_property_reduction_mode"] = "area_only_keep_gross"
    result = _net_geometry(values, {})
    assert result["I_xn"] < values["J_x"]
    assert result["W_xn_min"] < values["W_el_x_pos"]


def test_manual_inline_mode_consumes_canonical_net_values_not_gross():
    values = _values(mode="manual_net_properties")
    values["section_weakening_model"]["manual_net_properties"] = _manual_bundle()
    result = _net_geometry(values, {})

    assert result["A_net"] == pytest.approx(4824.0)
    assert result["I_xn"] == pytest.approx(70_000_000.0)
    assert result["I_yn"] == pytest.approx(9_000_000.0)
    assert result["W_xn_min"] == pytest.approx(350_000.0)
    assert result["W_yn_min"] == pytest.approx(90_000.0)
    assert result["net_section_geometry_2d"]["mode"] == "manual_net_properties"


def test_without_holes_keeps_gross_properties_and_needs_no_mode():
    values = _values(holes=False)
    result = _net_geometry(values, {})
    assert result["A_net"] == values["A_gross"]
    assert result["I_xn"] == values["J_x"]
    assert result["W_yn_min"] == values["W_el_y_neg"]
    assert result["sp16_shear_weakening_mode"] == "none"


def test_legacy_separate_area_only_mode_remains_compatible():
    values = _values(mode="automatic_geometry")
    del values["section_weakening_model"]["net_property_mode"]
    values["sp16_i_symmetry_class"] = "not_i"
    values["net_property_reduction_mode"] = "area_only_keep_gross"
    result = _net_geometry(values, {})
    assert result["A_net"] == pytest.approx(4824.0)
    assert result["I_xn"] == values["J_x"]
    assert result["W_xn_min"] == values["W_el_x_pos"]


def test_invalid_mode_and_unsupported_auto_geometry_fail_closed():
    values = _values(mode="typo_mode")
    with pytest.raises(FireUIError, match="unsupported section_weakening_model.net_property_mode"):
        _net_geometry(values, {})

    values = _values()
    values["sp16_i_symmetry_class"] = "not_i"
    with pytest.raises(FireUIError, match="doubly symmetric I-sections"):
        _net_geometry(values, {})


@pytest.mark.parametrize("mode", ["automatic_geometry", "manual_net_properties"])
def test_central_hole_cannot_silently_use_other_local_thickness(mode):
    values = _values(mode=mode)
    values["section_weakening_model"]["local_thickness_mm"] = 6.0
    if mode == "manual_net_properties":
        values["section_weakening_model"]["manual_net_properties"] = _manual_bundle()
    with pytest.raises(FireUIError, match="local_thickness_mm"):
        _net_geometry(values, {})


def _production_session_through_weakening(payload):
    app = FireUI1Application.from_package_root(ROOT)
    _apply_atomic_route(app)
    install_registry_remediation(app.service.registry)
    session_id = app.service.create_session()["session_id"]
    s = app.service.get_session(session_id)

    for answer in (True, False, "hot_rolled_section", "catalog_section"):
        s.submit(answer)
    row = next(
        item for item in app.profile_catalog.list_profiles(35)
        if item["designation"] == "20К1"
    )
    s.submit({
        "section_catalog_standard": "ГОСТ Р 57837-2017",
        "section_designation": "20К1",
        "section_family": "i_section",
        "sp16_i_symmetry_class": "double_symmetric",
        "section_catalog_family_id": 35,
        "section_catalog_source_row_id": row["source_row_id"],
    })
    catalog = app.material_strength_catalog()
    product = next(item for item in catalog["products"] if item["value"] == "parallel_flange_i")
    grade = next(item for item in product["grades"] if item["steel_grade"] == "С255Б")
    interval = next(
        item for item in grade["intervals"]
        if item["thickness_interval"]["max_mm"] == 10
    )
    s.submit({
        "steel_product_form": "parallel_flange_i",
        "steel_grade": "С255Б",
        "steel_strength_interval_key": interval["interval_key"],
        "governing_product_thickness_mm": 10.0,
    })
    assert s.current_node_id == "SP554_I_SECTION_WEAKENING"
    normalized = _normalize_weakening_payload(CARD, payload)
    s.submit(normalized)
    assert not s.status.startswith("BLOCKED"), (s.status, s.branch_failures)
    assert s.current_node_id != "SP554_D_NET_PROPERTY_REDUCTION"
    assert s.current_node_id != "SP554_I_NET_SECTION_MANUAL_PROPERTIES"
    return s.plain_values()


def test_v0109_real_guided_session_auto_weakening_reaches_net_solver():
    values = _production_session_through_weakening({
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "automatic_geometry",
    })
    assert values["A_net"] == pytest.approx(values["A_gross"] - 20.0 * values["t_w"])
    assert values["I_xn"] < values["J_x"]
    assert values["I_yn"] < values["J_y"]
    assert values["W_xn_min"] < min(values["W_el_x_pos"], values["W_el_x_neg"])


def test_v0109_real_guided_session_manual_weakening_consumes_inline_values():
    bundle = _manual_bundle()
    values = _production_session_through_weakening({
        "schema": "section_weakening_model_v0.49",
        "holes_present": True,
        "model": "round_bolt_hole_universal_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
        "net_property_mode": "manual_net_properties",
        "manual_net_properties": bundle,
    })
    major_axis_is_x = values["major_axis_is_x"]
    assert isinstance(major_axis_is_x, bool)
    assert values["I_xn"] == pytest.approx(
        bundle["I_z_n_mm4"] if major_axis_is_x else bundle["I_y_n_mm4"]
    )
    assert values["W_xn_min"] == pytest.approx(
        bundle["W_z_n_mm3"] if major_axis_is_x else bundle["W_y_n_mm3"]
    )
    assert values["A_net"] == pytest.approx(values["A_gross"] - 20.0 * values["t_w"])
