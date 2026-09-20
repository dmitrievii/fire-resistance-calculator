from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui0 import GuidedCalculationSession
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui23_protection_route import build_fire_ui23_registry
from standard_core.profile_catalog import InterimProfileCatalog

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph/dag_v0.3.59_fire_ui23_protection_route_closure.json'
POLICY=ROOT/'data/fire_ui23_presentation_policy.json'


def graph(): return json.loads(DAG.read_text(encoding='utf-8'))

def seed(s, qid, value): s._set_quantity(qid,value,node_id='TEST_SEED',source_kind='USER_INPUT')


def test_v056_graph_identity_and_source_selector_first():
    g=graph(); edges=g['edges']
    assert g['graph_id']=='sp16_sp554_dag_v0-3-59_fire_ui23_protection_route_closure'
    for eid in ('E0047','E0048','UI22_E_POST_PROTECTION'):
        e=next(x for x in edges if x['id']==eid)
        assert e['to_node_id']=='SP554_D_PROTECTION_SOURCE_MODE'
    source=next(n for n in g['nodes'] if n['id']=='SP554_D_PROTECTION_SOURCE_MODE')
    assert [o['value'] for o in source['options']]==['sto_arss_library','manual_properties','documented_product_matrix']


def test_source_selector_skips_commercial_fields_for_arss_and_manual():
    app=FireUI1Application.from_package_root(ROOT); reg=build_fire_ui23_registry(InterimProfileCatalog())
    for choice in ('sto_arss_library','manual_properties'):
        s=GuidedCalculationSession(app.model,entry_node_id='SP554_D_PROTECTION_SOURCE_MODE',registry=reg)
        s.submit(choice)
        assert s.current_node_id=='SP554_D_PROTECTION_PERIMETER_MODE'
        assert 'SP554_I_PROTECTION' not in s.visited_node_ids
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_D_PROTECTION_SOURCE_MODE',registry=reg)
    s.submit('documented_product_matrix')
    assert s.current_node_id=='SP554_I_PROTECTION'


def test_mineral_wool_library_density_is_fixed_100_with_source_range_preserved():
    g=graph(); ds=next(x for x in g['datasets'] if x['id']=='STO_ARSS_11251254_001_018_03_THERMAL_PROPERTIES')
    wool=next(x for x in ds['storage']['rows'] if x['material_id']=='mineral_wool_board')
    assert wool['density_kg_m3']==100.0
    assert wool['source_density_range_kg_m3']==[80.0,100.0]
    assert wool['lambda_A']+wool['lambda_B']*273.0==pytest.approx(0.05134)


def test_arss_direct_route_reaches_protected_result_without_raw_performance_object():
    app=FireUI1Application.from_package_root(ROOT); reg=app.service.registry
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_D_12_5_ARSS_MATERIAL',registry=reg)
    for q,v in [('protection_source_mode','sto_arss_library'),('delta_pr_protected',10.0),('critical_temperature_c',600.0),('fire_temperature_regime','standard')]: seed(s,q,v)
    s.submit('mineral_wool_board')
    assert s.current_node_id=='SP554_I_12_6_VALIDATION_EVIDENCE'
    assert 'protection_performance_dataset_raw' not in s.plain_values()
    s.submit({'protection_12_6_max_deviation_pct':15.0,'protection_12_6_validation_evidence_complete':True})
    assert s.current_node_id=='SP554_D_12_10_MODE'
    s.submit('verify_given_thickness')
    assert s.current_node_id=='SP554_I_12_10_GIVEN_THICKNESS'
    s.submit(20.0)
    assert s.current_node_id=='SP554_D_AFTER_PROTECTED'
    assert s.plain_values()['protection_thickness_mm']==pytest.approx(20.0)
    assert s.plain_values()['protected_fire_resistance_min']>0
    assert 'protection_performance_dataset_raw' not in s.plain_values()


def test_arss_and_manual_property_routes_retain_explicit_12_6_gate():
    g=graph(); n={x['id']:x for x in g['nodes']}
    for nid in ('SP554_I_12_6_VALIDATION_EVIDENCE','SP554_Q_12_6_VALIDATION'):
        app=n[nid]['applicability']
        assert app['type']=='comparison' and app['operator']=='in'
        assert set(app['value'])=={'sto_arss_library','manual_properties'}
    # There is no automatic ARSS pass node in the active graph.
    assert 'SP554_C_12_6_ARSS_LIBRARY_VALIDATION' not in n


def test_arss_inverse_route_is_bounded_and_reaches_result():
    app=FireUI1Application.from_package_root(ROOT); reg=app.service.registry
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_D_12_10_MODE',registry=reg)
    values={
      'protection_source_mode':'sto_arss_library','protection_arss_material_id':'mineral_wool_board',
      'delta_pr_protected':10.0,'critical_temperature_c':600.0,'fire_temperature_regime':'standard',
      'protection_material_density_kg_m3':100.0,'protection_material_moisture_percent':0.5,'protection_material_emissivity':0.92,
      'protection_material_lambda_A':-0.107,'protection_material_lambda_B':0.00058,'protection_material_cp_C':582.0,'protection_material_cp_D':0.63,'protection_material_temperature_basis':'K',
      'protection_12_6_max_deviation_pct':15.0,'protection_12_6_validation_evidence_complete':True,'validation_within_20_percent_all_cases':True,
      'required_fire_resistance_min':60.0,
    }
    for q,v in values.items(): seed(s,q,v)
    model_node=app.model.nodes['SP554_C_12_5_BUILD_MODEL_PARAMETERS']
    for q,v in reg.get(model_node['id'])(s.plain_values(),model_node).items(): s._set_quantity(q,v,node_id=model_node['id'],source_kind='CALCULATED')
    s.submit('determine_minimum_thickness')
    assert s.current_node_id=='SP554_I_12_5_SEARCH_BOUNDS'
    s.submit({'protection_search_min_thickness_mm':5.0,'protection_search_max_thickness_mm':40.0})
    assert s.current_node_id=='SP554_D_AFTER_PROTECTED'
    assert 5.0<=s.plain_values()['protection_thickness_mm']<=40.0
    assert s.plain_values()['protected_fire_resistance_min']>=60.0-1e-6


def test_manual_validation_failure_is_terminal_before_thermal_result():
    app=FireUI1Application.from_package_root(ROOT); reg=app.service.registry
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_I_12_6_VALIDATION_EVIDENCE',registry=reg)
    seed(s,'protection_source_mode','manual_properties')
    s.submit({'protection_12_6_max_deviation_pct':21.0,'protection_12_6_validation_evidence_complete':True})
    assert s.current_node_id=='SP554_R_12_6_VALIDATION_RESULT_INVALID'
    assert s.status=='RESULT'


def test_documented_matrix_mapping_not_string_reaches_12_10_mode_and_direct_result():
    app=FireUI1Application.from_package_root(ROOT); reg=app.service.registry
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED',registry=reg)
    for q,v in [('protection_source_mode','documented_product_matrix'),('protection_product_id','TEST-PROD'),('steel_strength_group','ordinary'),('fire_temperature_regime','standard'),('critical_temperature_c',500.0),('delta_pr_protected',10.0)]: seed(s,q,v)
    raw={'product_id':'TEST-PROD','source_kind':'technical_documentation_12_7_9','critical_temperature_c':500.0,'steel_group':'ordinary','fire_regime':'standard','technical_documentation_12_7_9_confirmed':True,'reduced_thickness_axis_mm':[5.0,10.0,20.0],'protection_thickness_axis_mm':[10.0,20.0,30.0],'time_matrix_min':[[20,40,60],[25,50,75],[30,60,90]]}
    s.submit(raw)
    assert s.current_node_id=='SP554_D_12_10_MODE'
    assert isinstance(s.plain_values()['protection_performance_dataset_raw'],dict)
    s.submit('verify_given_thickness'); s.submit(20.0)
    assert s.current_node_id=='SP554_D_AFTER_PROTECTED'
    assert s.plain_values()['protected_fire_resistance_min']==pytest.approx(50.0)


def test_documented_matrix_has_specialized_frontend_component_and_legacy_raw_routes_excluded():
    p=json.loads(POLICY.read_text(encoding='utf-8'))
    assert p['node_presentation']['SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED']['component']=='documented_performance_matrix_editor'
    excluded=set(p['guided_excluded_nodes'])
    for nid in ('SP554_D_PROTECTION_DATA','SP554_D_PROTECTION_DATA_METHOD','SP554_D_12_5_MATERIAL_SOURCE','SP554_I_12_5_GENERATION_GRID','SP554_C_12_5_1D_PERFORMANCE_DATASET','SP554_I_12_4_TEST_SERIES'):
        assert nid in excluded
    ts=(ROOT/'fire_ui1_web/src/app.ts').read_text(encoding='utf-8')
    assert 'renderDocumentedPerformanceMatrixEditor' in ts
    assert 'documented_performance_matrix_editor' in ts


def test_primary_protection_routes_have_no_generic_object_text_input():
    g=graph(); p=json.loads(POLICY.read_text(encoding='utf-8'))
    q={x['id']:x for x in g['quantities']}; excluded=set(p.get('guided_excluded_nodes',[]))
    active_protection=[]
    for n in g['nodes']:
        if n['id'] in excluded: continue
        if n['node_type'] not in {'input','decision','standard_handoff'}: continue
        if not (n['id'].startswith('SP554_I_PROTECTION') or n['id'].startswith('SP554_I_12_5') or n['id'].startswith('SP554_D_PROTECTION') or n['id']=='SP554_D_12_5_ARSS_MATERIAL'):
            continue
        for b in n.get('produces',[]):
            if q[b['quantity_id']].get('data_type')=='object':
                active_protection.append((n['id'],p.get('node_presentation',{}).get(n['id'],{}).get('component')))
    assert active_protection==[('SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED','documented_performance_matrix_editor')]
