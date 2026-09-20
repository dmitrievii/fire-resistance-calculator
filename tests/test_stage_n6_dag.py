from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph'/'dag_v0.3.35_stage_n6.json'

def _d(): return json.loads(DAG.read_text(encoding='utf-8'))
def _n(d,i): return next(x for x in d['nodes'] if x['id']==i)

def test_n6_dag_validates_frozen_schema():
    schema=json.loads((ROOT/'normative_graph'/'dag_schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema).validate(_d())

def test_n6_dag_identity_counts_and_parent_content():
    d=_d()
    assert d['graph_id']=='sp16_sp554_dag_v0-3-35_stage_n6'
    assert (len(d['quantities']),len(d['nodes']),len(d['edges']))==(682,612,1049)
    assert _n(d,'SP16_N5_K_STABILITY_ROUTE')
    assert _n(d,'SP16_N6_K_TOPOLOGY_ROUTE')

def test_n6_topology_router_keeps_9_3_5_and_9_3_6_out_of_general_route():
    n=_n(_d(),'SP16_N6_K_TOPOLOGY_ROUTE')
    vals={x['output_value'] for x in n['classification_rules']}
    assert {'guided_general_9.3','section16_9.3.5','detailed_9.3.6','less_than_6_panels_external'} <= vals

def test_n6_d4_policy_has_no_hidden_interpolation():
    d=_d(); n=_n(d,'SP16_N6_K_D4_POLICY'); r=_n(d,'SP16_N6_R_D4_FAIL_CLOSED')
    vals={x['output_value'] for x in n['classification_rules']}
    assert {'exact_grid','external_explicit','fail_closed','section8_route'} <= vals
    assert r['applicability']['value']=='fail_closed'
    assert 'hidden D4 interpolation' in r['notes']['normative_warning']

def test_n6_parent_d4_lookup_remains_exact_grid():
    d=_d(); lookup=_n(d,'SP16_L_D4_PHI_E')
    assert lookup['lookup_spec']['interpolation']['method']=='none'
    assert lookup['lookup_spec']['interpolation']['extrapolation']=='forbidden'
    ds=next(x for x in d['datasets'] if x['id']=='SP16_TABLE_D4')
    cell=next(x for x in ds['storage']['rows'] if x['lambda_bar']==1.5 and x['m']==1.0)
    assert cell['phi_e']==0.454
    assert ds['interpolation']['method']=='none'

def test_n6_table22_table23_policy_explicitly_differs_from_d4():
    n=_n(_d(),'SP16_N6_K_LOCAL_INTERPOLATION_POLICY')
    assert 'прямо указанные' in n['notes']['limitations']
    assert all(x['output_value']=='both_explicit' for x in n['classification_rules'])

def test_n6_biaxial_branch_force_fail_closed_is_explicit():
    r=_n(_d(),'SP16_N6_R_BRANCH_FORCE_FAIL_CLOSED')
    assert r['applicability']['quantity_id']=='sp16_n6_branch_force_status'
    assert r['applicability']['value']=='external_required'
    assert 'Do not sum' in r['notes']['normative_warning']

def test_n6_reduced_area_recheck_is_terminal_requirement():
    r=_n(_d(),'SP16_N6_R_REDUCED_AREA_RECHECK')
    assert r['applicability']['quantity_id']=='sp16_n6_reduced_area_required'
    assert r['applicability']['value'] is True
    assert '109/115/116' in r['notes']['limitations']
