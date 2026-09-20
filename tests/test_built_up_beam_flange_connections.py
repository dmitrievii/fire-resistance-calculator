import math
import pytest

from standard_core import built_up_beam_flange_connections as f


def test_table_43_catalog():
    catalog = f.table_43_catalog()
    assert catalog["table"] == "43"
    assert len(catalog["rows"]) == 4
    assert catalog["rows"][0]["equations"] == ["193", "194"]


def test_shear_and_local_pressure_flows():
    assert f.flange_shear_flow_t_n_mm(240000, 1.2e6, 8e8) == pytest.approx(360.0)
    assert f.flange_shear_flow_t_n_mm(-240000, 1.2e6, 8e8) == pytest.approx(-360.0)
    assert f.local_load_line_pressure_v_n_mm(1.2, 1.1, 100000, 250) == pytest.approx(528.0)
    assert f.local_load_line_pressure_v_n_mm(1.2, 1.0, 0, 250) == 0.0


def test_table_43_route():
    assert f.table_43_load_route(
        "stationary", "upper", transverse_stiffener_at_load=True
    )["effective_load_character"] == "stationary"
    assert f.table_43_load_route(
        "stationary", "upper", transverse_stiffener_at_load=False
    )["effective_load_character"] == "moving"
    assert f.table_43_load_route(
        "stationary", "lower", transverse_stiffener_at_load=True
    )["effective_load_character"] == "moving"
    assert f.table_43_load_route(
        "moving", "upper", transverse_stiffener_at_load=True
    )["effective_load_character"] == "moving"


def test_table_43_alpha():
    assert f.table_43_alpha(
        "upper", web_edge_planed_to_loaded_upper_flange=True
    ) == 0.4
    assert f.table_43_alpha(
        "upper", web_edge_planed_to_loaded_upper_flange=False
    ) == 1.0
    assert f.table_43_alpha(
        "lower", web_edge_planed_to_loaded_upper_flange=True
    ) == 1.0


def test_equations_193_to_195():
    assert f.stationary_weld_metal_utilization_eq193(
        360, 2, 0.8, 8, 240, 1
    ) == pytest.approx(360 / (2 * 0.8 * 8 * 240))
    assert f.stationary_fusion_boundary_utilization_eq194(
        360, 2, 1.0, 8, 215, 1
    ) == pytest.approx(360 / (2 * 1.0 * 8 * 215))
    assert f.stationary_friction_utilization_eq195(
        360, 80, 25000, 2, 1
    ) == pytest.approx(360 * 80 / (25000 * 2))


def test_equations_196_to_198():
    assert f.moving_weld_metal_utilization_eq196(
        360, 528, 0.8, 8, 240, 1
    ) == pytest.approx(math.hypot(360, 528) / (2 * 0.8 * 8 * 240))
    assert f.moving_fusion_boundary_utilization_eq197(
        360, 528, 1.0, 8, 215, 1
    ) == pytest.approx(math.hypot(360, 528) / (2 * 1.0 * 8 * 215))
    assert f.moving_friction_utilization_eq198(
        360, 528, 0.4, 80, 25000, 2, 1
    ) == pytest.approx(80 * math.hypot(360, 0.4 * 528) / (25000 * 2))


def test_zero_and_boundary_cases():
    assert f.stationary_weld_metal_utilization_eq193(
        0, 1, 0.8, 8, 240, 1
    ) == 0.0
    assert f.moving_weld_metal_utilization_eq196(
        0, 0, 0.8, 8, 240, 1
    ) == 0.0
    with pytest.raises(ValueError):
        f.moving_friction_utilization_eq198(
            360, 528, 0.5, 80, 25000, 2, 1
        )
    with pytest.raises(ValueError):
        f.stationary_weld_metal_utilization_eq193(
            360, 3, 0.8, 8, 240, 1
        )


def test_full_penetration_and_multilayer_sheet_routes():
    assert f.full_penetration_web_weld_equivalence_14_4_1(True)[
        "equal_strength_with_web"
    ]
    half = f.multilayer_flange_sheet_attachment_force_14_4_2(
        500000, "beyond_theoretical_cutoff"
    )
    full = f.multilayer_flange_sheet_attachment_force_14_4_2(
        500000, "between_actual_and_previous_sheet_cutoff"
    )
    assert half["required_attachment_force_n"] == 250000
    assert full["required_attachment_force_n"] == 500000


def test_invalid_inputs():
    with pytest.raises(ValueError):
        f.flange_shear_flow_t_n_mm(1, 1, 0)
    with pytest.raises(ValueError):
        f.local_load_line_pressure_v_n_mm(1, 1, -1, 10)
    with pytest.raises(TypeError):
        f.table_43_load_route("moving", "upper", transverse_stiffener_at_load=1)
