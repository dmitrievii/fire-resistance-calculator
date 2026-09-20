from __future__ import annotations
import json
from pathlib import Path
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph/dag_v0.3.34_stage_n5.json'

def _d(): return json.loads(DAG.read_text(encoding='utf-8'))
def _n(d,i): return next(x for x in d['nodes'] if x['id']==i)

def test_n5_dag_validates_frozen_schema():
    schema=json.loads((ROOT/'normative_graph/dag_schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema).validate(_d())

def test_n5_dag_identity_counts_and_parent_content():
    d=_d()
    assert d['graph_id']=='sp16_sp554_dag_v0-3-34_stage_n5'
    assert (len(d['quantities']),len(d['nodes']),len(d['edges']))==(665,598,1039)
    assert _n(d,'SP16_N4_C_EQ41')
    assert _n(d,'SP16_L_D3_PHI_EX')

def test_n5_parent_d3_lookup_remains_exact_grid_no_interpolation():
    d=_d()
    for nid in ('SP16_L_D3_PHI_EX','SP16_L_D3_PHI_EY'):
        interp=_n(d,nid)['lookup_spec']['interpolation']
        assert interp['method']=='none'
        assert interp['extrapolation']=='forbidden'

def test_n5_strength_router_exposes_105_and_106_without_hiding_applicability():
    n=_n(_d(),'SP16_N5_K_STRENGTH_ROUTE')
    vals={x['output_value'] for x in n['classification_rules']}
    assert {'eq106','eq105_if_remaining_gates_pass'} <= vals
    assert 'Ryn' in n['notes']['limitations']

def test_n5_stability_router_retains_specialized_box_and_built_up_actions():
    n=_n(_d(),'SP16_N5_K_STABILITY_ROUTE')
    vals={x['output_value'] for x in n['classification_rules']}
    assert {'specialized_9.3_9.4','specialized_9.2.10','guided_9.2.2_9.2.9'} <= vals

def test_n5_d3_policy_has_explicit_fail_closed_terminal():
    d=_d(); k=_n(d,'SP16_N5_K_D3_POLICY'); r=_n(d,'SP16_N5_R_D3_FAIL_CLOSED')
    assert any(x['output_value']=='fail_closed' for x in k['classification_rules'])
    assert r['applicability']['value']=='fail_closed'
    assert 'NormCAD' in r['notes']['normative_warning']
