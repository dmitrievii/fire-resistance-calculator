from __future__ import annotations

import pytest

from standard_core.fire_ui14_section_weakening import (
    WEAKENING_TRACE_SCHEMA,
    _alpha45_executor,
    _net_geometry_executor,
)
from streamlit_weakening_report_v092 import weakening_section


def _base_values():
    return {
        "A_gross": 5000.0,
        "J_x": 50_000_000.0,
        "J_y": 5_000_000.0,
        "W_el_x_pos": 400_000.0,
        "W_el_x_neg": 400_000.0,
        "W_el_y_pos": 100_000.0,
        "W_el_y_neg": 100_000.0,
        "major_axis_is_x": True,
        "sp16_i_symmetry_class": "double_symmetric",
        "t_w": 8.0,
        "section_geometry_2d_normalized": {
            "template": "i_section",
            "h_mm": 250.0,
            "b_mm": 150.0,
            "tw_mm": 8.0,
            "tf_mm": 12.0,
        },
    }


def _row(qid, value, unit=None):
    return {
        "quantity_id": qid,
        "raw_value": value,
        "canonical_unit": unit,
        "name_ru": qid,
        "symbol": None,
    }


def test_ui14_hole_executor_publishes_structured_evidence_without_relabelling_geometry_as_eq45():
    values = _base_values()
    values["section_weakening_model"] = {
        "schema": "section_weakening_model_v0.47",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
    }

    out = _net_geometry_executor(values, {})
    trace = out["net_section_geometry_2d"]["calculation_trace"]

    assert trace["schema"] == WEAKENING_TRACE_SCHEMA
    assert trace["route"] == "representative_central_web_hole"
    assert trace["major_axis_is_x"] is True
    assert "not labelled as SP16 formula (45)" in trace["engineering_basis"]
    assert trace["presentation_recomputes_values"] is False

    steps = {row["formula_id"]: row for row in trace["steps"]}
    assert steps["REMOVED_AREA_CENTRAL_WEB_HOLE"]["formula_latex"] == r"\Delta A=d\,t_w"
    assert steps["REMOVED_AREA_CENTRAL_WEB_HOLE"]["result"]["value"] == pytest.approx(160.0)
    assert steps["A_NET_CENTRAL_WEB_HOLE"]["result"]["value"] == pytest.approx(4840.0)
    assert steps["I_XN_CENTRAL_WEB_HOLE"]["result"]["value"] == pytest.approx(
        50_000_000.0 - 8.0 * 20.0**3 / 12.0
    )
    assert steps["I_YN_CENTRAL_WEB_HOLE"]["result"]["value"] == pytest.approx(
        5_000_000.0 - 20.0 * 8.0**3 / 12.0
    )

    eq45 = trace["sp16_formula45"]
    assert eq45["normative_scope"] == "SP16 8.2.1 Eq.(45)"
    assert eq45["formula_latex"] == r"\alpha_h=\frac{s}{s-d}"
    assert eq45["result_quantity_id"] == "sp16_shear_hole_alpha45"
    assert "result" not in eq45


def test_weakening_report_renders_formula_numeric_substitution_and_recorded_result_for_geometry_and_eq45():
    values = _base_values()
    values["section_weakening_model"] = {
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": 20.0,
        "hole_pitch_mm": 80.0,
    }
    out = _net_geometry_executor(values, {})
    alpha = _alpha45_executor(out, {})["sp16_shear_hole_alpha45"]

    report = {
        "blocks": [
            {
                "owner_node_id": "SP554_G_NET_SECTION_PROPERTIES",
                "normative_refs": [],
                "inputs": [],
                "outputs": [
                    _row("net_section_geometry_2d", out["net_section_geometry_2d"]),
                    _row("A_net", out["A_net"], "mm2"),
                    _row("I_xn", out["I_xn"], "mm4"),
                    _row("I_yn", out["I_yn"], "mm4"),
                    _row("W_xn_min", out["W_xn_min"], "mm3"),
                    _row("W_yn_min", out["W_yn_min"], "mm3"),
                    _row("sp16_net_removed_area", out["sp16_net_removed_area"], "mm2"),
                ],
            },
            {
                "owner_node_id": "SP16_C_SHEAR_ALPHA45",
                "normative_refs": [
                    {
                        "standard_id": "SP16_2017",
                        "section": "8",
                        "clause": "8.2.1",
                        "formula_ref": "(45)",
                    }
                ],
                "inputs": [],
                "outputs": [_row("sp16_shear_hole_alpha45", alpha, "1")],
            },
        ]
    }

    text = weakening_section(report)

    assert "### 1.3 Ослабления сечения" in text
    assert "геометрическое уменьшение $A$, $I$ и $W$" in text
    assert "Формула (45) используется только для коэффициента ослабления при сдвиге" in text

    assert r"\Delta A=d\,t_w" in text
    assert r"\Delta A=20\cdot 8=160\;\mathrm{мм^2}" in text
    assert r"A_n=A-\Delta A" in text
    assert r"A_n=5 000-160=4 840\;\mathrm{мм^2}" in text

    # Runtime axis evidence major_axis_is_x=True must be rendered as active z/y.
    assert "сильной главной оси **z-z**" in text
    assert "слабой главной оси **y-y**" in text
    assert r"I_{z,n}=I_z-\frac{t_w d^3}{12}" in text
    assert r"I_{y,n}=I_y-\frac{d t_w^3}{12}" in text

    assert "#### Коэффициент ослабления стенки при сдвиге по формуле (45) СП 16" in text
    assert r"\alpha_h=\frac{s}{s-d}" in text
    assert r"\alpha_h=\frac{80}{80-20}=1.333" in text
    assert "8.2.1" in text


def test_no_weakening_trace_and_report_keep_identity_without_inventing_hole_formula():
    values = _base_values()
    values["section_weakening_model"] = {"holes_present": False, "model": "none"}
    out = _net_geometry_executor(values, {})
    trace = out["net_section_geometry_2d"]["calculation_trace"]
    assert trace["route"] == "identity_no_weakening"
    assert trace["sp16_formula45"]["applicable"] is False

    report = {
        "blocks": [
            {
                "owner_node_id": "SP554_G_NET_SECTION_PROPERTIES",
                "normative_refs": [],
                "inputs": [],
                "outputs": [_row("net_section_geometry_2d", out["net_section_geometry_2d"])],
            }
        ]
    }
    text = weakening_section(report)
    assert "Ослабления в активном поперечном сечении отсутствуют" in text
    assert r"A_n=A" in text
    assert "$α_h=1$" in text
    assert r"\frac{s}{s-d}" not in text
