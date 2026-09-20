from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from standard_core import sheet_structure_workflows as n8w
from standard_core import sheet_structures_strength_and_stability as s11
from standard_core.runner import run_case, _prepare_case_for_validation

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples' / 'sheet_structure_guided_example.json'


def _raw():
    return json.loads(EXAMPLE.read_text(encoding='utf-8'))


def _base(route: dict):
    return {
        'case_id': 'N8-TEST',
        'standard': 'СП 16.13330.2017',
        'action': 'sheet_structure_guided',
        'working_condition_factor': 1.0,
        'design_yield_resistance_n_mm2': 350.0,
        'elastic_modulus_n_mm2': 206000.0,
        'route': route,
    }


def test_n8_example_hydrates_current_material_and_exact_table34_node():
    result = run_case(EXAMPLE, ROOT)
    assert result['resolution_trace']['material']['resolved_values']['design_yield_resistance_n_mm2'] == pytest.approx(350.0)
    r = result['results']
    assert r['status'] == 'COMPLETE'
    assert r['critical']['radius_to_thickness_ratio'] == pytest.approx(100.0)
    assert r['critical']['c_coefficient'] == pytest.approx(0.22)
    assert r['critical']['table34_source'] == 'exact_printed_node'
    assert r['equation_154_utilization'] < 1.0


def test_n8_table34_non_node_is_fail_closed_without_hidden_interpolation():
    case = _base({'kind': 'cylinder_axial_11_2_1', 'radius_mm': 1250.0, 'thickness_mm': 10.0, 'axial_compressive_stress_n_mm2': 50.0})
    with pytest.raises(ValueError):
        n8w.sheet_structure_guided_workflow(case)


def test_n8_table34_external_value_requires_and_preserves_provenance():
    route = {
        'kind': 'cylinder_axial_11_2_1', 'radius_mm': 1250.0, 'thickness_mm': 10.0,
        'axial_compressive_stress_n_mm2': 50.0,
        'external_table34_c': {'value': 0.20, 'basis': 'engineer-approved Table 34 determination TEST'},
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['critical']['table34_source'] == 'external_explicit_value'
    assert r['critical']['table34_external_basis'].endswith('TEST')
    assert r['critical']['c_coefficient'] == pytest.approx(0.20)


def test_n8_membrane_general_eq148_and_principal_stress_check():
    r = n8w.sheet_structure_guided_workflow(_base({
        'kind': 'membrane_general_11_1_1', 'sigma_x_n_mm2': 100.0, 'sigma_y_n_mm2': 50.0,
        'tau_xy_n_mm2': 20.0, 'tension_design_resistance_n_mm2': 350.0,
        'compression_design_resistance_n_mm2': 350.0,
    }))
    assert r['status'] == 'COMPLETE'
    assert r['strength']['status'] == 'EVALUATED'
    assert r['strength']['equation_148_utilization'] == pytest.approx(
        s11.membrane_strength_utilization_eq148(100, 50, 20, 350, 1)
    )
    assert r['strength']['principal_stress_check']['pass'] is True


def test_n8_edge_effect_clause_11_1_4_is_fail_closed_until_confirmed():
    route = {
        'kind': 'membrane_general_11_1_1', 'sigma_x_n_mm2': 10.0, 'sigma_y_n_mm2': 5.0,
        'tau_xy_n_mm2': 0.0, 'tension_design_resistance_n_mm2': 350.0,
        'compression_design_resistance_n_mm2': 350.0,
        'has_geometry_thickness_or_load_discontinuity': True,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    assert any('11.1.4' in x for x in r['analysis_gate']['unresolved_requirements'])
    route['local_edge_effect_analysis_confirmed'] = True
    assert n8w.sheet_structure_guided_workflow(_base(route))['status'] == 'COMPLETE'


def test_n8_spatial_clause_11_1_5_requires_certified_software_and_base_clauses():
    route = {
        'kind': 'membrane_general_11_1_1', 'sigma_x_n_mm2': 10.0, 'sigma_y_n_mm2': 5.0,
        'tau_xy_n_mm2': 0.0, 'tension_design_resistance_n_mm2': 350.0,
        'compression_design_resistance_n_mm2': 350.0,
        'arbitrary_configuration_or_spatial_state': True,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    assert len(r['analysis_gate']['unresolved_requirements']) == 2
    route['certified_spatial_software_confirmed'] = True
    route['clauses_11_1_2_to_11_1_4_requirements_confirmed'] = True
    assert n8w.sheet_structure_guided_workflow(_base(route))['status'] == 'COMPLETE'


def test_n8_axisymmetric_membrane_149_150_selected_route():
    route = {
        'kind': 'axisymmetric_membrane_11_1_2', 'projected_pressure_force_n': 100000.0,
        'pressure_n_mm2': 0.2, 'radius_mm': 1000.0, 'thickness_mm': 10.0, 'beta_degrees': 0.0,
        'meridional_radius_mm': 1000.0, 'circumferential_radius_mm': 1000.0,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['stress_equation'] == '149-150'
    assert r['sigma_1_n_mm2'] == pytest.approx(s11.meridional_stress_eq149(100000, 1000, 10, 0))
    assert r['strength']['status'] == 'NOT_REQUESTED'


@pytest.mark.parametrize('kind,equation', [
    ('internal_pressure_cylinder_11_1_3', '151'),
    ('internal_pressure_sphere_11_1_3', '152'),
    ('internal_pressure_cone_11_1_3', '153'),
])
def test_n8_internal_pressure_routes_151_153(kind, equation):
    route = {'kind': kind, 'pressure_n_mm2': 0.5, 'radius_mm': 1000.0, 'thickness_mm': 10.0}
    if kind.endswith('cone_11_1_3'):
        route['beta_degrees'] = 30.0
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['status'] == 'COMPLETE'
    assert r['stress_equation'] == equation
    assert r['sigma_1_n_mm2'] > 0 and r['sigma_2_n_mm2'] > 0


def test_n8_internal_pressure_route_can_explicitly_run_strength_check():
    route = {
        'kind': 'internal_pressure_cylinder_11_1_3', 'pressure_n_mm2': 0.5,
        'radius_mm': 1000.0, 'thickness_mm': 10.0, 'perform_strength_check': True,
        'tension_design_resistance_n_mm2': 350.0, 'compression_design_resistance_n_mm2': 350.0,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['strength']['status'] == 'EVALUATED'
    assert r['strength']['pass'] is True


def test_n8_cylinder_axial_eccentric_multiplier_applies_only_below_shear_limit():
    route = {
        'kind': 'cylinder_axial_11_2_1', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
        'axial_compressive_stress_n_mm2': 100.0, 'eccentric_compression_or_pure_bending': True,
        'minimum_signed_stress_n_mm2': -20.0, 'shear_stress_n_mm2': 0.0,
    }
    a = n8w.sheet_structure_guided_workflow(_base(route))
    assert a['eccentric_adjustment']['applicable'] is True
    assert a['adjusted_critical_stress_n_mm2'] > a['critical']['critical_stress_n_mm2']
    route['shear_stress_n_mm2'] = 100.0
    b = n8w.sheet_structure_guided_workflow(_base(route))
    assert b['eccentric_adjustment']['applicable'] is False
    assert b['adjusted_critical_stress_n_mm2'] == pytest.approx(b['critical']['critical_stress_n_mm2'])


def test_n8_tube_low_ratio_requires_sections_7_and_9_global_stability_confirmation():
    route = {'kind': 'tube_11_2_2', 'radius_mm': 200.0, 'thickness_mm': 10.0, 'relative_slenderness': 0.7}
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['classification']['route'] == 'global_stability_only_sections_7_and_9'
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    route['sections_7_and_9_global_stability_confirmed'] = True
    assert n8w.sheet_structure_guided_workflow(_base(route))['status'] == 'COMPLETE'


def test_n8_tube_equation_156_route_requires_explicit_table34_value_below_printed_grid():
    route = {
        'kind': 'tube_11_2_2', 'radius_mm': 400.0, 'thickness_mm': 10.0, 'relative_slenderness': 0.8,
        'axial_force_n': 100000.0, 'gross_area_mm2': 5000.0, 'relative_eccentricity_m': 0.2,
    }
    with pytest.raises(ValueError):
        n8w.sheet_structure_guided_workflow(_base(route))
    route['external_table34_c'] = {'value': 0.30, 'basis': 'explicit engineering determination for r/t=40 TEST'}
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['classification']['route'] == 'equation_156_local_stability_no_separate_global_check'
    assert r['critical']['table34_source'] == 'external_explicit_value'
    assert r['equation_156_utilization'] >= 0.0


def test_n8_tube_outside_direct_11_2_2_route_is_fail_closed():
    r = n8w.sheet_structure_guided_workflow(_base({'kind': 'tube_11_2_2', 'radius_mm': 800.0, 'thickness_mm': 10.0, 'relative_slenderness': 1.0}))
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    assert 'outside direct' in r['required']


def test_n8_panel_eq157_and_eq158_limits_and_printed_interpolation():
    for sigma, expected_route in [(100.0, 'equation_157'), (300.0, 'linear_interpolation_0.8Ry_to_Ry'), (350.0, 'equation_158')]:
        r = n8w.sheet_structure_guided_workflow(_base({
            'kind': 'cylindrical_panel_11_2_3', 'panel_width_mm': 300.0, 'radius_mm': 1000.0,
            'thickness_mm': 10.0, 'compressive_stress_n_mm2': sigma,
        }))
        assert r['status'] == 'COMPLETE'
        assert r['limit']['route'] == expected_route
        assert r['governing_utilization'] >= 0.0


def test_n8_panel_b2_over_rt_above_20_routes_to_11_2_1_and_requires_confirmation():
    route = {
        'kind': 'cylindrical_panel_11_2_3', 'panel_width_mm': 500.0, 'radius_mm': 1000.0,
        'thickness_mm': 10.0, 'compressive_stress_n_mm2': 100.0,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['classification']['route'] == 'shell_clause_11_2_1'
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    route['shell_clause_11_2_1_confirmed'] = True
    rr = n8w.sheet_structure_guided_workflow(_base(route))
    assert rr['status'] == 'COMPLETE'
    assert rr['critical']['table34_source'] == 'exact_printed_node'


def test_n8_external_pressure_160_interpolation_161_are_selected_exactly_as_printed():
    for lr, route_name in [(10.0, 'equation_160'), (15.0, 'linear_interpolation_10_to_20'), (20.0, 'equation_161')]:
        r = n8w.sheet_structure_guided_workflow(_base({
            'kind': 'cylinder_external_pressure_11_2_4', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
            'length_mm': lr * 1000.0, 'external_pressure_n_mm2': 0.01,
        }))
        assert r['external_pressure_critical']['route'] == route_name
        assert r['status'] == 'COMPLETE'


def test_n8_ring_stiffened_route_requires_actual_ring_section_properties():
    route = {
        'kind': 'cylinder_external_pressure_11_2_4', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
        'external_pressure_n_mm2': 0.001, 'ring_stiffened': True, 'ring_spacing_mm': 1000.0,
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['status'] == 'INCOMPLETE_FAIL_CLOSED'
    assert set(r['ring_check']['missing']) == {'ring_effective_area_mm2','ring_radius_of_gyration_mm','ring_table7_section_type'}


def test_n8_ring_stiffened_route_checks_equation7_and_conditional_slenderness():
    route = {
        'kind': 'cylinder_external_pressure_11_2_4', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
        'external_pressure_n_mm2': 0.001, 'ring_stiffened': True, 'ring_spacing_mm': 1000.0,
        'ring_effective_area_mm2': 5000.0, 'ring_radius_of_gyration_mm': 100.0, 'ring_table7_section_type': 'a',
    }
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['ring_check']['status'] == 'COMPLETE'
    assert r['ring_check']['equation_7_utilization'] >= 0.0
    assert r['ring_check']['relative_slenderness'] <= 6.5


def test_n8_one_sided_ring_requires_nearest_surface_inertia_confirmation():
    route = {
        'kind': 'cylinder_external_pressure_11_2_4', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
        'external_pressure_n_mm2': 0.001, 'ring_stiffened': True, 'ring_spacing_mm': 1000.0,
        'ring_effective_area_mm2': 5000.0, 'ring_radius_of_gyration_mm': 100.0, 'ring_table7_section_type': 'a',
        'ring_is_one_sided': True,
    }
    assert n8w.sheet_structure_guided_workflow(_base(route))['status'] == 'INCOMPLETE_FAIL_CLOSED'
    route['one_sided_ring_inertia_axis_confirmed'] = True
    assert n8w.sheet_structure_guided_workflow(_base(route))['status'] == 'COMPLETE'


def test_n8_combined_cylinder_uses_equation_162():
    r = n8w.sheet_structure_guided_workflow(_base({
        'kind': 'cylinder_combined_11_2_5', 'radius_mm': 1000.0, 'thickness_mm': 10.0,
        'length_mm': 10000.0, 'external_pressure_n_mm2': 0.005, 'axial_compressive_stress_n_mm2': 50.0,
    }))
    assert r['status'] == 'COMPLETE'
    sigma2 = 0.005 * 1000.0 / 10.0
    expected = (50.0 / r['axial_critical']['critical_stress_n_mm2']
                + sigma2 / r['external_pressure_critical']['critical_stress_n_mm2'])
    assert r['equation_162_utilization'] == pytest.approx(expected)
    assert r['governing_utilization'] == r['equation_162_utilization']


@pytest.mark.parametrize('kind', ['cone_axial_11_2_6','cone_external_pressure_11_2_7','cone_combined_11_2_8'])
def test_n8_cone_routes_163_to_168(kind):
    route = {
        'kind': kind, 'top_radius_mm': 800.0, 'bottom_radius_mm': 1000.0,
        'beta_degrees': 30.0, 'thickness_mm': 10.0, 'height_mm': 2000.0,
    }
    # rm/t is non-grid, so axial cone route uses explicit Table-34 c provenance.
    if kind in {'cone_axial_11_2_6','cone_combined_11_2_8'}:
        route['axial_force_n'] = 100000.0
        route['external_table34_c'] = {'value': 0.22, 'basis': 'explicit engineer-approved c for cone rm/t TEST'}
    if kind in {'cone_external_pressure_11_2_7','cone_combined_11_2_8'}:
        route['external_pressure_n_mm2'] = 0.005
    r = n8w.sheet_structure_guided_workflow(_base(route))
    assert r['status'] == 'COMPLETE'
    assert r['equation_165_equivalent_radius_mm'] > 0
    assert r['governing_utilization'] >= 0


def test_n8_cone_beta_over_60_is_rejected():
    case = _base({
        'kind': 'cone_external_pressure_11_2_7', 'top_radius_mm': 800.0, 'bottom_radius_mm': 1000.0,
        'beta_degrees': 61.0, 'thickness_mm': 10.0, 'height_mm': 2000.0, 'external_pressure_n_mm2': 0.005,
    })
    with pytest.raises(ValueError):
        n8w.sheet_structure_guided_workflow(case)


def test_n8_spherical_external_pressure_eq169_and_r_over_t_limit():
    r = n8w.sheet_structure_guided_workflow(_base({
        'kind': 'sphere_external_pressure_11_2_9', 'radius_mm': 5000.0, 'thickness_mm': 10.0,
        'external_pressure_n_mm2': 0.01,
    }))
    assert r['status'] == 'COMPLETE'
    assert r['critical_stress_n_mm2'] == pytest.approx(min(0.1*206000*10/5000,350))
    with pytest.raises(ValueError):
        n8w.sheet_structure_guided_workflow(_base({
            'kind': 'sphere_external_pressure_11_2_9', 'radius_mm': 8000.0, 'thickness_mm': 10.0,
            'external_pressure_n_mm2': 0.01,
        }))


def test_n8_guided_schema_rejects_hidden_extra_field():
    raw = _raw()
    raw['route']['hidden_default'] = 123
    with pytest.raises(ValueError, match='Unexpected property'):
        _prepare_case_for_validation(raw, ROOT)


def test_n8_source_metadata_is_current_change6():
    assert 'Changes No. 1-6 through 09.12.2024' in s11.__doc__
    data = json.loads((ROOT/'data'/'table_34_cylindrical_shell_coefficient.json').read_text(encoding='utf-8'))
    assert '1-6' in json.dumps(data, ensure_ascii=False)
