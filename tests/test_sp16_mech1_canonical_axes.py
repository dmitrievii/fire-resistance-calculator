from __future__ import annotations

from pathlib import Path

import pytest

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.sp16_mech1_canonical_actions import migrate_v057_actions_to_sp16_mech1
from standard_core.section_model import SectionPropertyModel

ROOT = Path(__file__).resolve().parents[1]


def _seed(s: GuidedCalculationSession, qid: str, value) -> None:
    s._set_quantity(qid, value, node_id="TEST_SEED", source_kind="USER_INPUT")


def test_mech1_graph_identity_and_canonical_quantities():
    app = FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id'] == 'sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md = app.model.graph['metadata']
    assert md['sp16_mech1_canonical_axes_closed'] is True
    assert md['sp16_mech1_qy_runtime_closed'] is False
    assert md['sp16_mech1_torsion_runtime_closed'] is False
    for qid in ['M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment','mechanical_action_state']:
        assert qid in app.model.quantities
    assert app.model.quantities['T_torsion']['symbol'] == 'T'


def test_v057_axis_transform_is_sign_preserving():
    migrated = migrate_v057_actions_to_sp16_mech1({
        'N_force': -400000.0,
        'load_My_local': -30e6,
        'load_Mz_local': 10e6,
        'load_Qz_local': -50e3,
        'load_Qy_local': 7e3,
        'T_torsion': -2e6,
    })
    assert migrated == {
        'N_force': -400000.0,
        'M_x': -30e6,
        'M_y': 10e6,
        'Q_x': -50e3,
        'Q_y': 7e3,
        'T_torsion': -2e6,
    }


def test_fire_load_card_keeps_sp16_axes_and_qy_t_visible_fail_closed():
    app = FireUI1Application.from_package_root(ROOT)
    card = app.model.node_card('SP554_H_SP20_LOADS')
    fields = {f['quantity_id'] for f in card['fields']}
    assert {'N_force','M_x','M_y','Q_x','Q_y','T_torsion'} <= fields
    assert not card['presentation'].get('locked_quantities')
    assert card['presentation']['component'] == 'fire_signed_load_menu'


def _state_session(*, bimoment_required: bool) -> GuidedCalculationSession:
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id='SP16_D_BIMOMENT_REQUIRED', registry=app.service.registry)
    for qid, value in {
        'special_load_combination': {'schema':'sp16_mech1_test'},
        'fire_load_case': {'schema':'sp16_mech2_load_case_v1','kind':'fire'},
        'N_force': -400000.0,
        'M_x': 40e6,
        'M_y': -10e6,
        'Q_x': 50e3,
        'Q_y': 0.0,
        'T_torsion': 0.0,
    }.items():
        _seed(s, qid, value)
    p=SectionPropertyModel.doubly_symmetric_i_sharp(300.0,150.0,8.0,12.0)
    for qid,value in {
        'section_geometry_2d_normalized':{'template':'i_section','h_mm':300.0,'b_mm':150.0,'tw_mm':8.0,'tf_mm':12.0},
        'A_gross':p.area_mm2,'J_x':p.ix_mm4,'J_y':p.iy_mm4,
        'Rs_formula':200.0,'gamma_c_bending_strength':1.0,'sp16_shear_hole_alpha45':1.0,
    }.items():
        s._set_quantity(qid,value,node_id='TEST_SEED',source_kind='CALCULATED')
    s.submit(bimoment_required)
    return s


def test_bimoment_no_materializes_explicit_zero_then_builds_state():
    s = _state_session(bimoment_required=False)
    values = s.plain_values()
    assert values['B_bimoment'] == 0.0
    assert values['Q_shear'] == values['Q_x'] == 50e3
    assert values['mechanical_action_state']['actions']['Mx'] == 40e6
    assert values['mechanical_action_state']['actions']['My'] == -10e6
    assert values['verification_plan']['compatibility_aliases'] == {'Q_shear':'Q_x'}
    assert 'SP16_C_BIMOMENT_ZERO' in s.visited_node_ids
    assert 'SP554_D_STRESS_STATE' in s.visited_node_ids


def test_bimoment_yes_requests_direct_value_and_preserves_sign():
    s = _state_session(bimoment_required=True)
    assert s.current_node_id == 'SP16_I_BIMOMENT_DIRECT'
    s.submit(-2.5e10)
    values = s.plain_values()
    assert values['B_bimoment'] == -2.5e10
    assert values['mechanical_action_state']['actions']['B'] == -2.5e10
    ids = {b['id'] for b in values['verification_plan']['branches']}
    assert 'bimoment_B' in ids


def test_qy_and_t_are_not_silently_collapsed_into_legacy_shear_alias():
    app = FireUI1Application.from_package_root(ROOT)
    s = GuidedCalculationSession(app.model, entry_node_id='SP554_D_STRESS_STATE', registry=app.service.registry)
    for qid, value in {
        'special_load_combination': {'schema':'sp16_mech1_test'}, 'fire_load_case': {'schema':'sp16_mech2_load_case_v1','kind':'fire'}, 'N_force':0.0,
        'M_x':0.0, 'M_y':0.0, 'Q_x':12e3, 'Q_y':9e3, 'T_torsion':3e6, 'B_bimoment':0.0,
    }.items(): _seed(s,qid,value)
    s._auto_progress()
    values=s.plain_values()
    assert values['Q_shear'] == 12e3
    assert set(values['verification_plan']['deferred_branch_ids']) == {'shear_Qy','torsion_T'}
