from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui22_routing_protection import _build_protection_model_parameters
from standard_core.fire_sp554_thermal import sp554_fire_thermal_guided_workflow

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph/dag_v0.3.58_fire_ui22_routing_protection_library_hotfix.json'


def _graph():
    return json.loads(DAG.read_text(encoding='utf-8'))


def test_ui22_graph_identity_and_routing_edges():
    g=_graph()
    assert g['graph_id']=='sp16_sp554_dag_v0-3-58_fire_ui22_routing_protection_library_hotfix'
    edges={(e['from_node_id'],e['to_node_id'],e['edge_type']) for e in g['edges']}
    assert ('SP554_C_GAMMAE_OUTPUT','SP554_FIRE_UI17_C_TCR_COMPRESSION','control') in edges
    assert any(a=='SP554_I_NM_CONTEXT' and b=='SP16_D_M_RULE' for a,b,_ in edges)
    assert any(a=='SP16_D_C_ROUTE_MODE' and b=='SP16_D_C_MOMENT_RULE' for a,b,_ in edges)
    assert any(a=='SP554_R_UNPROTECTED' and b=='SP554_D_AFTER_UNPROTECTED' for a,b,_ in edges)
    assert any(a=='SP554_D_AFTER_UNPROTECTED' and b=='SP554_I_PROTECTION' for a,b,_ in edges)


def test_ui22_arss_library_has_exact_four_rows_and_mineral_wool_density_100():
    g=_graph()
    ds=next(d for d in g['datasets'] if d['id']=='STO_ARSS_11251254_001_018_03_THERMAL_PROPERTIES')
    rows=ds['storage']['rows']
    assert len(rows)==4
    wool=next(r for r in rows if r['material_id']=='mineral_wool_board')
    assert wool['density_kg_m3']==100.0
    assert wool['source_density_range_kg_m3']==[80.0,100.0]
    assert wool['temperature_basis']=='K'
    assert wool['lambda_A']==pytest.approx(-0.107)
    assert wool['lambda_B']==pytest.approx(0.00058)
    # At the source validity limit the conductivity is positive; using 273 C
    # instead of 273 K would be a category error that this provenance prevents.
    assert wool['lambda_A']+wool['lambda_B']*273.0==pytest.approx(0.05134)


def test_ui22_arss_lookup_and_model_builder_preserve_kelvin_basis():
    values={
        'protection_12_5_material_source':'sto_arss_library',
        'protection_arss_material_id':'mineral_wool_board',
        'protection_material_density_kg_m3':100.0,
        'protection_material_moisture_percent':0.5,
        'protection_material_emissivity':0.92,
        'protection_material_lambda_A':-0.107,
        'protection_material_lambda_B':0.00058,
        'protection_material_cp_C':582.0,
        'protection_material_cp_D':0.63,
        'protection_material_temperature_basis':'K',
    }
    out=_build_protection_model_parameters(values,{})
    model=out['protection_12_5_model_parameters']
    assert model['density_kg_m3']==100.0
    assert model['temperature_basis']=='K'
    assert out['protection_material_provenance']['source_density_range_kg_m3']==[80.0,100.0]


def test_protected_fdm_kelvin_material_coefficients_are_shifted_exactly_to_celsius_solver_basis():
    # Dry synthetic control avoids moisture-policy concerns and isolates the
    # temperature-basis transformation.
    case={
      'thermal_route':'PROTECTED_FDM_12_5','critical_temperature_c':200.0,'reduced_thickness_mm':10.0,
      'time_step_min':0.0005,'max_time_min':30.0,
      'protection_model':{
        'thickness_mm':5.0,'layer_count':2,'density_kg_m3':100.0,
        'conductivity_A_w_mk':-0.107,'conductivity_B_w_mk2':0.00058,
        'heat_capacity_C_j_kgk':582.0,'heat_capacity_D_j_kgk2':0.63,
        'initial_moisture_percent':0.0,'surface_emissivity':0.92,'temperature_basis':'K',
      },
      'validation_reference_times_min':[5.0],
    }
    result=sp554_fire_thermal_guided_workflow(case)
    coeff=result['material_parameters']['protection_solver_coefficients_degC_basis']
    assert coeff['conductivity_A_w_mk']==pytest.approx(-0.107+0.00058*273.15)
    assert coeff['heat_capacity_C_j_kgk']==pytest.approx(582.0+0.63*273.15)


def test_ui22_contract_has_nonempty_material_selectors():
    app=FireUI1Application.from_package_root(ROOT)
    contract=app.model.build_ui_contract()
    by={f['quantity_id']:f for card in contract['node_cards'] for f in card.get('fields',[])}
    assert [x['value'] for x in by['protection_12_5_material_source']['enum_values']]==['sto_arss_library','manual_properties']
    assert len(by['protection_arss_material_id']['enum_values'])==4


def test_ui22_library_guided_path_materializes_wool_properties_without_raw_json():
    from standard_core.fire_ui0 import GuidedCalculationSession
    app=FireUI1Application.from_package_root(ROOT)
    # FIRE-UI2.3 supersedes the old source selector, but the inherited ARSS
    # lookup/model builder must still materialize the same canonical data.
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_D_12_5_ARSS_MATERIAL',registry=app.service.registry)
    s._set_quantity('protection_source_mode','sto_arss_library',node_id='TEST_SEED',source_kind='USER_INPUT')
    s.submit('mineral_wool_board')
    assert s.current_node_id=='SP554_I_12_6_VALIDATION_EVIDENCE'
    vals=s.plain_values()
    assert vals['protection_material_density_kg_m3']==100.0
    model=vals['protection_12_5_model_parameters']
    assert model['density_kg_m3']==100.0
    assert model['temperature_basis']=='K'
    assert model['source_provenance']['source_density_range_kg_m3']==[80.0,100.0]
    assert 'protection_performance_dataset_raw' not in vals


def test_ui22_manual_material_route_builds_same_canonical_model_without_raw_json():
    from standard_core.fire_ui0 import GuidedCalculationSession
    app=FireUI1Application.from_package_root(ROOT)
    s=GuidedCalculationSession(app.model,entry_node_id='SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES',registry=app.service.registry)
    s._set_quantity('protection_source_mode','manual_properties',node_id='TEST_SEED',source_kind='USER_INPUT')
    s.submit({
        'protection_material_density_kg_m3':450.0,
        'protection_material_moisture_percent':1.0,
        'protection_material_emissivity':0.9,
        'protection_material_lambda_A':0.12,
        'protection_material_lambda_B':0.0002,
        'protection_material_cp_C':800.0,
        'protection_material_cp_D':0.4,
        'protection_material_temperature_basis':'K',
    })
    assert s.current_node_id=='SP554_I_12_6_VALIDATION_EVIDENCE'
    model=s.plain_values()['protection_12_5_model_parameters']
    assert model['density_kg_m3']==450.0
    assert model['temperature_basis']=='K'
    assert model['source_provenance']['source_kind']=='manual_properties'
    assert 'SP554_I_12_5_MODEL_PARAMETERS' not in s.visited_node_ids


def _documented_matrix_dataset():
    return {
        'product_id':'TEST-PROTECTION',
        'source_kind':'technical_documentation_12_7_9',
        'critical_temperature_c':500.0,
        'steel_group':'ordinary',
        'fire_regime':'standard',
        'technical_documentation_12_7_9_confirmed':True,
        'reduced_thickness_axis_mm':[5.0,10.0],
        'protection_thickness_axis_mm':[5.0,10.0],
        'time_matrix_min':[[30.0,60.0],[20.0,50.0]],
        'allow_greater_delta_carry_forward':False,
    }


def test_ui22_direct_12_10_domain_does_not_require_rreq_but_inverse_does():
    from standard_core.fire_ui22_routing_protection import _direct_domain_12_10, _inverse_domain_12_10
    direct={
        'protection_performance_dataset_normalized':_documented_matrix_dataset(),
        'critical_temperature_c':500.0,
        'delta_pr_protected':7.5,
        'protection_candidate_thickness_mm':7.5,
    }
    assert _direct_domain_12_10(direct,{})['sp554_12_10_query_domain_ok'] is True
    # The inverse executor reports an unresolved/out-of-domain state without inventing Rreq;
    # the DAG itself declares Rreq required and schedules its handoff before execution.
    assert _inverse_domain_12_10({k:v for k,v in direct.items() if k!='protection_candidate_thickness_mm'}, {})['sp554_12_10_inverse_query_domain_ok'] is False
    inverse={
        'protection_performance_dataset_normalized':_documented_matrix_dataset(),
        'critical_temperature_c':500.0,
        'delta_pr_protected':7.5,
        'required_fire_resistance_min':40.0,
    }
    assert _inverse_domain_12_10(inverse,{})['sp554_12_10_inverse_query_domain_ok'] is True


def test_ui22_graph_defers_rreq_and_allows_protected_finish_without_compliance():
    g=_graph(); nodes={n['id']:n for n in g['nodes']}
    edges={(e['from_node_id'],e['to_node_id'],e['edge_type']) for e in g['edges']}
    assert ('SP554_D_PRODUCT_ROUTE','SP554_D_METHOD','branch') in edges
    assert not any(a=='SP554_D_PRODUCT_ROUTE' and b=='SP554_H_REQUIRED_R' for a,b,_ in edges)
    direct=nodes['SP554_C_12_10_DOMAIN']
    assert 'required_fire_resistance_min' not in {b['quantity_id'] for b in direct['consumes']}
    inverse=nodes['SP554_C_12_10_DOMAIN_INVERSE']
    assert 'required_fire_resistance_min' in {b['quantity_id'] for b in inverse['consumes'] if b['required']}
    assert ('SP554_R_PROTECTED','SP554_D_AFTER_PROTECTED','control') in edges
    assert ('SP554_D_AFTER_PROTECTED','SP554_R_PROTECTED_CALCULATION_COMPLETE','branch') in edges
    assert ('SP554_D_AFTER_PROTECTED','SP554_Q_PROTECTED','branch') in edges


def test_ui22_all_nontrivial_expression_helpers_are_bound_or_whitelisted():
    import ast
    from standard_core.fire_ui16_declarative import _SIMPLE_FUNCS
    app=FireUI1Application.from_package_root(ROOT)
    registry=set(app.service.registry.executors)
    special={'field_over_section_points','max_abs_over_section_points','max_abs_field','max_over_common_section_points'}
    failures=[]
    for node in _graph()['nodes']:
        expr=node.get('calculation_spec',{}).get('expression')
        if not expr:
            continue
        tree=ast.parse(expr,mode='eval')
        helpers={x.func.id for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name)}
        unsupported=helpers-set(_SIMPLE_FUNCS)-special
        if unsupported and node['id'] not in registry:
            failures.append((node['id'],sorted(unsupported)))
    assert failures==[]


def test_ui22_unpromoted_12_4_and_12_5_dataset_builders_fail_with_specific_diagnostic_not_missing_helper():
    app=FireUI1Application.from_package_root(ROOT)
    reg=app.service.registry
    for nid in ('SP554_C_12_4_BUILD_PERFORMANCE_DATASET','SP554_C_12_5_1D_PERFORMANCE_DATASET'):
        fn=reg.get(nid)
        assert fn is not None
        with pytest.raises(Exception) as exc:
            fn({}, next(n for n in _graph()['nodes'] if n['id']==nid))
        text=str(exc.value)
        assert 'unsupported expression helper' not in text
        assert 'not yet' in text
