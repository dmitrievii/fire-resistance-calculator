import math

import pytest

from standard_core import local_stability as ls


def test_table_catalogues_are_detached_and_complete():
    table9 = ls.table_9_wall_slenderness_catalog()
    table10 = ls.table_10_flange_slenderness_catalog()
    assert table9["table_number"] == "9"
    assert set(table9["diagram_groups"]) == {
        "group_1_i_section", "group_2_box_section", "group_3_channel_section", "group_4_tee_section"
    }
    assert table10["table_number"] == "10"
    assert len(table10["diagram_groups"]) == 4
    table9["table_number"] = "changed"
    assert ls.table_9_wall_slenderness_catalog()["table_number"] == "9"


def test_geometry_rule_catalogue():
    rules = ls.local_stability_geometry_rule_catalog()
    assert "welded" in rules["effective_web_height"]
    assert "rolled" in rules["effective_flange_outstand"]


def test_wall_and_flange_relative_slenderness():
    expected_wall = (500.0 / 8.0) * math.sqrt(355.0 / 206000.0)
    expected_flange = (120.0 / 12.0) * math.sqrt(355.0 / 206000.0)
    assert ls.wall_relative_slenderness(500, 8, 355, 206000) == pytest.approx(expected_wall)
    assert ls.flange_relative_slenderness(120, 12, 355, 206000) == pytest.approx(expected_flange)
    with pytest.raises(ValueError):
        ls.wall_relative_slenderness(500, 0, 355, 206000)
    with pytest.raises(ValueError):
        ls.flange_relative_slenderness(-1, 12, 355, 206000)


def test_equations_23_to_29_and_table_9_router():
    assert ls.wall_slenderness_limit_eq23(0.0) == 1.3
    assert ls.wall_slenderness_limit_eq23(2.0) == pytest.approx(1.9)
    assert ls.wall_slenderness_limit_eq24(2.5) == pytest.approx(2.075)
    assert ls.wall_slenderness_limit_eq24(10.0) == 2.3
    assert ls.wall_slenderness_limit_eq25(1.0) == 1.2
    assert ls.wall_slenderness_limit_eq26(2.0) == pytest.approx(1.4)
    assert ls.wall_slenderness_limit_eq26(5.0) == 1.6
    assert ls.wall_slenderness_limit_eq27(0.8) == 1.0
    assert ls.wall_slenderness_limit_eq28(2.0) == pytest.approx(1.23)
    assert ls.wall_slenderness_limit_eq28(10.0) == 1.6
    assert ls.wall_slenderness_limit_eq29(2.0, 500, 500) == pytest.approx(0.675)
    assert ls.wall_slenderness_limit("group_1_i_section", 2.0) == pytest.approx(1.9)
    assert ls.wall_slenderness_limit("group_1_i_section", 2.000001) == pytest.approx(1.20 + 0.35 * 2.000001)
    assert ls.wall_slenderness_limit("group_2_box_section", 1.0) == 1.2
    assert ls.wall_slenderness_limit("group_3_channel_section", 0.8) == 1.0
    # Table 9 note clamps the T-section member slenderness to 0.8 and 4.0.
    assert ls.wall_slenderness_limit("group_4_tee_section", 0.1, 500, 500) == pytest.approx(
        ls.wall_slenderness_limit_eq29(0.8, 500, 500)
    )
    with pytest.raises(ValueError):
        ls.wall_slenderness_limit_eq24(2.0)
    with pytest.raises(ValueError):
        ls.wall_slenderness_limit_eq29(2.0, 1100, 500)
    with pytest.raises(ValueError):
        ls.wall_slenderness_limit("unknown", 1.0)


def test_transverse_stiffener_requirements():
    result = ls.transverse_stiffener_requirements(2.3, 600, 355, 206000, "paired_symmetric", 60, False, False)
    assert result["required"] is True
    assert result["minimum_spacing_mm"] == 1500.0
    assert result["maximum_spacing_mm"] == 1800.0
    assert result["minimum_outstand_mm"] == 60.0
    assert result["outstand_pass"] is True
    assert result["minimum_thickness_mm"] == pytest.approx(2.0 * 60.0 * math.sqrt(355.0 / 206000.0))
    one_sided = ls.transverse_stiffener_requirements(2.4, 600, 355, 206000, "one_sided", 80, True, True)
    assert one_sided["required"] is False
    assert one_sided["location_rule"] == "only_at_lattice_or_batten_connection_nodes"
    assert one_sided["one_sided_angle_weld_orientation"] == "angle_toe_to_web"
    with pytest.raises(ValueError):
        ls.transverse_stiffener_requirements(2.4, 600, 355, 206000, "invalid", 80, False, False)


def test_equation_30_and_stiffener_domain():
    # x = 5 gives beta = 2.0.
    inertia = 5.0 * 600.0 * 8.0**3
    assert ls.longitudinal_stiffener_wall_limit_multiplier_eq30(inertia, 600, 8) == 2.0
    assert ls.longitudinal_stiffener_wall_limit_multiplier_eq30(0, 600, 8) == 1.0
    with pytest.raises(ValueError):
        ls.longitudinal_stiffener_wall_limit_multiplier_eq30(6.0001 * 600 * 8**3, 600, 8)


def test_reduced_area_trigger():
    assert ls.reduced_area_required(2.0, 2.0)["required"] is False
    assessment = ls.reduced_area_required(3.0, 2.0)
    assert assessment["required"] is True
    assert assessment["within_central_compression_reduction_domain"] is True
    assert ls.reduced_area_required(4.0001, 2.0)["formula_route_permitted"] is False
    with pytest.raises(ValueError):
        ls.reduced_area_required(1.0, 0.0)


def test_equations_31_to_33_reduced_areas():
    assert ls.reduced_area_i_or_channel_eq31(10000, 500, 400, 8) == 9200.0
    assert ls.reduced_area_box_central_eq32(12000, 500, 450, 8, 300, 270, 10) == 10600.0
    assert ls.reduced_area_box_eccentric_eq33(12000, 500, 450, 8) == 11200.0
    with pytest.raises(ValueError):
        ls.reduced_area_i_or_channel_eq31(10000, 500, 501, 8)
    with pytest.raises(ValueError):
        ls.reduced_area_box_central_eq32(1000, 500, 0, 8, 300, 0, 10)


def test_equations_34_to_36_reduced_dimensions():
    eq34_expected = 8.0 * (
        2.0 - (2.5 / 2.0 - 1.0) * (2.0 - 1.2 - 0.15 * 2.5)
    ) * math.sqrt(206000.0 / 355.0)
    assert ls.reduced_web_height_i_section_eq34(8, 2.5, 2.0, 2.5, 355, 206000) == pytest.approx(eq34_expected)
    # Member slenderness is capped at 3.5.
    assert ls.reduced_web_height_i_section_eq34(8, 2.5, 2.0, 10, 355, 206000) == pytest.approx(
        8.0 * (2.0 - (2.5 / 2.0 - 1.0) * (2.0 - 1.2 - 0.15 * 3.5)) * math.sqrt(206000.0 / 355.0)
    )
    eq35_expected = 8.0 * (
        1.5 - (2.0 / 1.5 - 1.0) * (1.5 - 2.9 - 0.2 * 2.0 + 0.7 * 1.5)
    ) * math.sqrt(206000.0 / 355.0)
    assert ls.reduced_plate_dimension_box_eq35(8, 2.0, 1.5, 2.0, 355, 206000) == pytest.approx(eq35_expected)
    eq36_expected = 8.0 * 1.2 * math.sqrt(206000.0 / 355.0)
    assert ls.reduced_web_height_channel_eq36(8, 1.5, 1.2, 355, 206000) == pytest.approx(eq36_expected)
    with pytest.raises(ValueError):
        ls.reduced_web_height_i_section_eq34(8, 2.0, 2.0, 2.0, 355, 206000)
    with pytest.raises(ValueError):
        ls.reduced_web_height_channel_eq36(8, 2.5, 1.2, 355, 206000)


def test_equations_37_to_40_and_table_10_router():
    assert ls.flange_slenderness_limit_eq37(2.0) == pytest.approx(0.56)
    assert ls.flange_slenderness_limit_eq38(2.0) == pytest.approx(0.59)
    assert ls.flange_slenderness_limit_eq39(2.0) == pytest.approx(0.54)
    assert ls.flange_slenderness_limit_eq40(2.0) == pytest.approx(1.23)
    # Wrapper applies table boundary substitution.
    assert ls.flange_slenderness_limit("group_1", 0.1, False) == pytest.approx(0.36 + 0.10 * 0.8)
    assert ls.flange_slenderness_limit("group_2", 10.0, False) == pytest.approx(0.43 + 0.08 * 4.0)
    assert ls.flange_slenderness_limit("group_1", 2.0, True) == pytest.approx(0.56 * 1.5)
    assert ls.flange_slenderness_limit("group_3", 2.0, True) == pytest.approx(0.54 * 1.6)
    with pytest.raises(ValueError):
        ls.flange_slenderness_limit_eq37(0.79)
    with pytest.raises(ValueError):
        ls.flange_slenderness_limit("group_4", 2.0, True)


def test_edge_stiffener_requirements():
    plain = ls.edge_stiffener_requirements(100, 355, 206000, False)
    assert plain["minimum_edge_height_mm"] == 30.0
    assert plain["minimum_edge_thickness_mm"] == pytest.approx(60.0 * math.sqrt(355.0 / 206000.0))
    battened = ls.edge_stiffener_requirements(100, 355, 206000, True)
    assert battened["minimum_edge_height_mm"] == 20.0
    with pytest.raises(TypeError):
        ls.edge_stiffener_requirements(100, 355, 206000, 1)


def test_two_plane_increase_factor():
    raw = math.sqrt(0.8 * 10000.0 * 355.0 / 2000000.0)
    assert ls.two_plane_slenderness_increase_factor(0.8, 10000, 355, 2000000) == pytest.approx(raw)
    assert ls.two_plane_slenderness_increase_factor(1.0, 10000, 355, 1000000) == 1.25
    assert ls.apply_two_plane_slenderness_increase(2.0, 1.2) == 2.4
    with pytest.raises(ValueError):
        ls.two_plane_slenderness_increase_factor(0.5, 1000, 355, 1000000)
    with pytest.raises(ValueError):
        ls.apply_two_plane_slenderness_increase(2.0, 1.251)
