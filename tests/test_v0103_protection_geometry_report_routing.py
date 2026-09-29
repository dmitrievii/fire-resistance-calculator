from __future__ import annotations

from types import SimpleNamespace

import streamlit_protection_geometry_v093 as card_layer
from streamlit_expertise_report_v093_thermal_repro import _thermal_passport


def test_v0103_protection_geometry_installer_does_not_wrap_card_renderer():
    sentinel = object()
    core = SimpleNamespace(_render_card_body=sentinel)
    card_layer.install(core)
    assert core._render_card_body is sentinel


def test_v0103_protection_geometry_evidence_is_rendered_in_report():
    report = {
        "blocks": [
            {
                "outputs": [
                    {"quantity_id": "fire_protection_perimeter_mode", "raw_value": "contour"},
                    {
                        "quantity_id": "sp554_protected_table1_perimeter_trace",
                        "raw_value": {
                            "formula": "4B + 2D - 2t",
                            "B_mm": 200.0,
                            "D_mm": 195.0,
                            "t_mm": 6.5,
                            "heated_sides": 4,
                        },
                    },
                    {"quantity_id": "P_heated_protected", "raw_value": 1.177},
                    {"quantity_id": "delta_pr_protected", "raw_value": 4.48768},
                ]
            }
        ]
    }
    text = _thermal_passport(report)
    assert "#### Защищённая схема" in text
    assert "$P_{prot}=4B + 2D - 2t$" in text
    assert "B=200 мм" in text
    assert "D=195 мм" in text
    assert "t_w=6.5 мм" in text
    assert "$P_{prot}=1.177$ м" in text
    assert "$δ_{pr,prot}=A/P_{prot}=4.48768$ мм" in text
