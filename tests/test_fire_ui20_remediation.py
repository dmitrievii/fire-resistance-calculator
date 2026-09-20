from __future__ import annotations

from pathlib import Path
import math
import pytest

from standard_core.fire_ui0 import GuidedCalculationSession, QuantityValue
from standard_core.fire_ui1_http import FireUI1Application

ROOT=Path(__file__).resolve().parents[1]


def _seed(session: GuidedCalculationSession, qid: str, value) -> None:
    q=session.model.quantities[qid]
    session.values[qid]=QuantityValue(qid,value,q.get('canonical_unit'),'USER_INPUT','TEST_SEED',1,None)


def test_ui20_graph_removes_raw_context_and_obsolete_moment_objects():
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.graph['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    assert 'SP16_I_MOMENT_DIST' not in app.model.nodes
    assert 'SP16_I_MOMENT_SUMMARY_9_2_3' not in app.model.nodes
    assert 'SP16_I_C_MOMENTS_9_2_6' not in app.model.nodes
    assert 'SP16_I_C_SIGNED_MX' not in app.model.nodes
    for nid in ('SP554_I_NM_CONTEXT','SP554_I_BENDING_CONTEXT'):
        assert 'beam_ltb_context' not in {b['quantity_id'] for b in app.model.nodes[nid].get('produces',[])}
    for nid in ('SP16_D_LTB','SP16_D_PHI_B_SECTION_ROUTE'):
        assert 'beam_ltb_context' not in {b['quantity_id'] for b in app.model.nodes[nid].get('consumes',[])}


def test_923_branch_specific_inputs_only_and_signed_table20_source():
    app=FireUI1Application.from_package_root(ROOT)
    expected={
        'SP16_I_M_CONST_FRAME_9_2_3':['M_max_full_length'],
        'SP16_I_M_STEPPED_9_2_3':['M_max_constant_segment'],
        'SP16_I_M_FIXED_FREE_9_2_3':['M_fixed_end','M_at_L_over_3'],
        'SP16_I_M_COMPRESSED_CHORD_9_2_3':['M_mid_third_panel_max'],
        'SP16_I_M_TABLE20_9_2_3':['M_max_full_length','M_mid_third_member_raw'],
    }
    for nid,qids in expected.items():
        assert [b['quantity_id'] for b in app.model.nodes[nid]['produces']]==qids
        assert all(b['required'] for b in app.model.nodes[nid]['produces'])
    side=app.model.nodes['SP16_K_TABLE20_WC_SIDE']
    assert [b['quantity_id'] for b in side['consumes']]==['M_max_full_length']
    assert {r['when']['quantity_id'] for r in side['classification_rules']}=={'M_max_full_length'}
    assert app.model.quantities['M_max_full_length']['description'].startswith('FIRE-UI2.0 invariant')


def test_923_decision_precedes_input_and_constant_branch_uses_abs_without_overwriting_source():
    app=FireUI1Application.from_package_root(ROOT)
    session=GuidedCalculationSession(app.model,entry_node_id='SP16_D_M_RULE',registry=app.service.registry)
    _seed(session,'special_load_combination',{'schema':'test_same_combination'})
    session.submit('constant_frame_column')
    assert session.current_node_id=='SP16_I_M_CONST_FRAME_9_2_3'
    assert [x['quantity_id'] for x in session.current_card()['fields']]==['M_max_full_length']
    session.submit({'M_max_full_length':-32_000_000.0})
    vals=session.plain_values()
    assert vals['M_max_full_length']==-32_000_000.0
    assert vals['M_11_3']==32_000_000.0


def test_926_signed_selector_preserves_determining_source_sign():
    app=FireUI1Application.from_package_root(ROOT)
    reg=app.service.registry
    nr=app.model.nodes['SP16_C_C_MX_RESTRAINED']
    nf=app.model.nodes['SP16_C_C_MX_FIXED_FREE']
    out=reg.get(nr['id'])({'M_x_mid_third_max':-32e6,'M_x_full_length_max':50e6},nr)
    assert out=={'M_x_c_design':32e6,'M_x_c_signed':-32e6}
    out=reg.get(nr['id'])({'M_x_mid_third_max':-20e6,'M_x_full_length_max':60e6},nr)
    assert out=={'M_x_c_design':30e6,'M_x_c_signed':30e6}
    out=reg.get(nf['id'])({'M_x_fixed_end':-40e6,'M_x_at_L_over_3':25e6},nf)
    assert out=={'M_x_c_design':40e6,'M_x_c_signed':-40e6}
    # equality retains the first normative candidate and never asks for sign again
    out=reg.get(nr['id'])({'M_x_mid_third_max':-30e6,'M_x_full_length_max':60e6},nr)
    assert out=={'M_x_c_design':30e6,'M_x_c_signed':-30e6}
    assert app.model.quantities['M_x_c_signed']['role']=='intermediate'


def test_gost30247_curve_and_sp554_figure1_bindings_execute_in_registry():
    app=FireUI1Application.from_package_root(ROOT)
    reg=app.service.registry
    ng=app.model.nodes['GOST30247_C_FORMULA1_STANDARD_FIRE_CURVE']
    curve=reg.get(ng['id'])({'gost30247_initial_furnace_temperature_c':20.0},ng)['gost30247_standard_fire_curve_contract']
    assert curve['schema']=='gost30247_standard_fire_curve_contract_v1'
    assert curve['time_unit']=='min' and curve['initial_temperature_c']==20.0
    nf=app.model.nodes['SP554_C_FIG1_UNPROTECTED_INTERPOLATION']
    out=reg.get(nf['id'])({'delta_pr':4.484,'critical_temperature_c':638.011628,'sp554_fig1_domain_ok':True},nf)
    assert 0.0 < out['unprotected_fire_resistance_min'] < 60.0
    with pytest.raises(Exception):
        reg.get(nf['id'])({'delta_pr':2.9,'critical_temperature_c':638.0,'sp554_fig1_domain_ok':True},nf)


def test_sp554_unprotected_step_binding_executes_with_same_order_as_figure1():
    app=FireUI1Application.from_package_root(ROOT)
    reg=app.service.registry
    ng=app.model.nodes['GOST30247_C_FORMULA1_STANDARD_FIRE_CURVE']
    curve=reg.get(ng['id'])({'gost30247_initial_furnace_temperature_c':20.0},ng)['gost30247_standard_fire_curve_contract']
    ns=app.model.nodes['SP554_C_UNPROTECTED_STEP_12_1_12_4']
    eps=1.0/(1.0/0.85+1.0/0.625-1.0)
    out=reg.get(ns['id'])({
        'delta_pr':4.484,'critical_temperature_c':638.011628,
        'sp554_dt_unprotected_min':0.1,'sp554_steel_density_12_2':7850.0,
        'sp554_steel_c0_12_2':480.0,'sp554_steel_c_temp_coeff_12_2':0.00063,
        'sp554_eps_reduced_12_4':eps,'gost30247_standard_fire_curve_contract':curve,
    },ns)
    assert out['unprotected_fire_resistance_min']==pytest.approx(12.3681128844,rel=1e-8)


def test_frontend_boolean_and_table21_specialized_selector_are_compiled():
    src=(ROOT/'fire_ui1_web/src/app.ts').read_text(encoding='utf-8')
    js=(ROOT/'fire_ui1_web/dist/app.js').read_text(encoding='utf-8')
    assert 'field.data_type === "enum" || field.data_type === "boolean"' in src
    assert 'renderTable21TypeSelector' in src and 'table21_type_selector' in src
    assert 'Механическая проверка не завершена' in src
    assert 'table21_type_selector' in js
    app=FireUI1Application.from_package_root(ROOT)
    assert app.model.ui_policy_for_node('SP16_D_TABLE21_TYPE')['component']=='table21_type_selector'


def test_qy_t_are_still_explicitly_fail_closed_not_silently_remapped():
    app=FireUI1Application.from_package_root(ROOT)
    node=app.model.nodes['SP554_R_UI16_DEFERRED_BRANCHES']
    assert 'Qy and torsion T remain fail-closed' in node['notes']['limitations']
    assert node['applicability']['type']=='any_of'
    qids={c['quantity_id'] for c in node['applicability']['conditions']}
    assert qids=={'Q_y','T_torsion'}
