import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

import pytest

from standard_core import axial_members as axial
from standard_core import beam_column_stability as beamcol
from standard_core import bending_members as bending
from standard_core import bolted_and_friction_connections as bolts
from standard_core import brittle_fracture_and_welded_connections as welds
from standard_core import built_up_axial_members as builtup
from standard_core import crane_runway_and_bending_stability as stability
from standard_core.runner import run_case

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def test_validation_registry_has_nine_preserved_cases_and_source_hashes():
    registry = json.loads((ROOT / 'validation/registry/validation_registry.json').read_text(encoding='utf-8'))
    assert registry['schema_version'] == '1.1.0'
    assert registry['corpus_revision'] == '0009'
    assert registry['case_count'] == 9
    ids = [row['case_id'] for row in registry['cases']]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids)) == 9
    for case_id in ids:
        case_dir = ROOT / 'validation/cases' / case_id
        case = json.loads((case_dir / 'case.json').read_text(encoding='utf-8'))
        source_path = ROOT / case['source']['stored_path']
        assert source_path.is_file(), case_id
        assert _sha256(source_path) == case['source']['sha256'], case_id
        for required in ('expected.json', 'production_result.json', 'comparison.json', 'README.md'):
            assert (case_dir / required).is_file(), f'{case_id}: {required}'


def test_table_8_equations_12_to_14_use_first_power_connection_factors():
    # VAL-SP16-BUILTUP-0009: user-supplied Eq. (12) route.
    got12 = builtup.battened_effective_slenderness_type_1(1.25, 44.2007, 27000, 400, 12340000, 400)
    assert got12 == pytest.approx(40.08869299632588)

    # Independent algebraic oracles for Eq. (13) and Eq. (14).
    args13 = (2.0, 1.0, 1.1, 200000, 220000, 350, 450, 500000, 550000, 1000)
    n1 = 200000 * 350 / (500000 * 1000)
    n2 = 220000 * 450 / (550000 * 1000)
    expected13 = math.sqrt(2.0**2 + 0.82 * ((1 + n1) * 1.0**2 + (1 + n2) * 1.1**2))
    assert builtup.battened_effective_slenderness_type_2(*args13) == pytest.approx(expected13)

    args14 = (2.2, 1.2, 180000, 420, 480000, 900)
    n3 = 180000 * 420 / (480000 * 900)
    expected14 = math.sqrt(2.2**2 + 0.82 * (1 + 3 * n3) * 1.2**2)
    assert builtup.battened_effective_slenderness_type_3(*args14) == pytest.approx(expected14)


def test_battened_branch_relative_slenderness_limit_rejects_case_0009():
    lambda_bar_branch = axial.relative_slenderness(44.2007, 245.0, 210000.0)
    assert lambda_bar_branch == pytest.approx(1.5097413224031682)
    check = builtup.batten_branch_slenderness_check(lambda_bar_branch)
    assert check['limit'] == pytest.approx(1.4)
    assert check['pass'] is False


def test_low_slenderness_types_a_b_return_phi_one_before_d1_lower_node():
    assert axial.central_compression_stability_coefficient(0.0026503, 'b') == 1.0
    assert axial.central_compression_stability_coefficient(0.0386, 'b') == 1.0
    assert axial.central_compression_stability_coefficient(0.1, 'a') == 1.0
    with pytest.raises(ValueError):
        axial.central_compression_stability_coefficient(0.2, 'c')


def test_annex_d2_type5_af_aw_ge1_uses_002_coefficient():
    lam = 1.61095111
    m = 4.83990898
    expected = (1.90 - 0.1 * m) - 0.02 * (6.0 - m) * lam
    got = beamcol.annex_d2_shape_influence_coefficient('5', lam, m, 1.0, 0.125)
    assert got == pytest.approx(expected)
    assert got == pytest.approx(1.3786321037, rel=1e-9)


def test_clause_14_1_8_automatic_upper_bound_uses_beta_ratio_once():
    result = welds.welding_consumable_compatibility_clause_14_1_8('automatic', 240.0, 166.5, 1.1, 1.15, 235.0)
    assert result['lower_bound_n_mm2'] == pytest.approx(166.5)
    assert result['upper_bound_n_mm2'] == pytest.approx(166.5 * 1.15 / 1.1)
    assert result['upper_bound_n_mm2'] == pytest.approx(174.0681818181818)
    assert result['pass'] is False


def test_clause_14_1_9_legacy_api_is_fail_closed_for_one_sided_weld():
    result = welds.one_sided_fillet_weld_route_clause_14_1_9(True, False, False)
    assert result['accepted'] is False
    assert result['route'] == 'full_clause_14_1_9_project_conditions_required'
    assert result['full_clause_14_1_9_project_conditions_required'] is True


def test_clause_14_2_14_uses_exact_count_rounding():
    assert bolts.bolt_count_detailing_adjustment_14_2_14(50, 'packing_or_single_cover_plate')['adjusted_bolt_count'] == 55
    assert bolts.bolt_count_detailing_adjustment_14_2_14(100, 'packing_or_single_cover_plate')['adjusted_bolt_count'] == 110
    assert bolts.bolt_count_detailing_adjustment_14_2_14(1, 'packing_or_single_cover_plate')['adjusted_bolt_count'] == 2


def test_table_40_staggered_minimum_and_generic_maximum_are_enforced():
    req = bolts.table_40_distance_requirements(
        20.0, 13.0, 235.0, friction_connection=False, friction_planes=1,
        edge_type='cut', stress_state='tension', row_location='middle_or_edge_with_angles',
        transverse_row_spacing_mm=140.0
    )
    assert req['minimum_staggered_longitudinal_spacing_mm'] == pytest.approx(170.0)
    assert req['maximum_center_spacing_mm'] == pytest.approx(312.0)

    # Ordinary center spacing itself can pass while the staggered longitudinal distance fails.
    staggered_req = dict(req)
    staggered_req['staggered_layout'] = True
    staggered_req['actual_staggered_longitudinal_spacing_mm'] = 100.0
    result = bolts.table_40_check_layout(120.0, 60.0, 80.0, staggered_req)
    assert result['checks']['staggered_longitudinal_min'] is False
    assert result['pass'] is False

    # VAL-SP16-BOLT-0003 also reports a generic spacing s=500 mm, exceeding the 312 mm maximum.
    result2 = bolts.table_40_check_layout(500.0, 60.0, 80.0, req)
    assert result2['checks']['center_max'] is False
    assert result2['pass'] is False


def test_bending_runner_recomputes_equation_44_after_hole_factor(tmp_path):
    source = ROOT / 'examples/bending_member_example.json'
    case = json.loads(source.read_text(encoding='utf-8'))
    local = tmp_path / 'bending.json'
    local.write_text(json.dumps(case), encoding='utf-8')
    shutil.copytree(ROOT / 'schemas', tmp_path / 'schemas')
    result = run_case(local, tmp_path)
    r = result['results']
    alpha = bending.bolt_hole_factor_eq45(case['hole_pitch_mm'], case['hole_diameter_mm'])
    adjusted_tau = case['shear_stress_xy_n_mm2'] * alpha
    expected = bending.elastic_web_equivalent_stress_checks_eq44(
        case['longitudinal_normal_stress_n_mm2'],
        case['transverse_normal_stress_n_mm2'],
        adjusted_tau,
        case['design_yield_resistance_n_mm2'],
        case['design_shear_resistance_n_mm2'],
        case['working_condition_factor'],
    )
    assert r['equation_44_adjusted_shear_stress_n_mm2'] == pytest.approx(adjusted_tau)
    assert r['equation_44_web_checks']['equivalent_utilization'] == pytest.approx(expected['equivalent_utilization'])
    assert r['equation_44_web_checks']['equivalent_utilization'] != pytest.approx(
        r['equation_44_web_checks_unadjusted_diagnostic']['equivalent_utilization']
    )


def test_clause_8_4_6_reduced_limit_is_used_for_exemption(tmp_path):
    case = json.loads((ROOT / 'examples/crane_runway_and_bending_stability_example.json').read_text(encoding='utf-8'))
    case['class_2_3_plastic_region_applies'] = True
    local = tmp_path / 'stability.json'
    local.write_text(json.dumps(case), encoding='utf-8')
    shutil.copytree(ROOT / 'schemas', tmp_path / 'schemas')
    result = run_case(local, tmp_path)['results']
    assert result['class_2_3_plastic_region_applies'] is True
    assert result['effective_limiting_flange_slenderness_for_exemption'] == pytest.approx(
        result['equation_76_delta'] * result['table_11_limiting_flange_slenderness']
    )
    # Directly prove that a value between base and reduced limits is not exempt under the reduced limit.
    base = 1.0
    reduced = 0.4
    assert stability.lateral_stability_check_exemption(False, 0.8, base, 0.8)['exempt'] is True
    assert stability.lateral_stability_check_exemption(False, 0.8, reduced, 0.8)['exempt'] is False


def test_clause_9_2_9_meff_y_gt20_keeps_independent_x_plane_trigger():
    route = beamcol.biaxial_additional_checks_clause_9_2_9(25.8495, 4.83991, 46.6898, 0.07681)
    assert route['equation_116_required'] is False
    assert route['section_8_y_route_required'] is True
    assert route['equation_109_with_ey_zero_required'] is True
    assert route['equation_111_with_ey_zero_required'] is False
    assert route['slenderness_trigger'] is True
