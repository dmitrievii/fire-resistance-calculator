from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph'/'dag_v0.3.36_stage_n7.json'

def _d(): return json.loads(DAG.read_text(encoding='utf-8'))
def _n(d,i): return next(x for x in d['nodes'] if x['id']==i)

def test_n7_dag_validates_frozen_schema():
    schema=json.loads((ROOT/'normative_graph'/'dag_schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema).validate(_d())

def test_n7_dag_identity_counts_and_frozen_parent():
    d=_d()
    assert d['graph_id']=='sp16_sp554_dag_v0-3-36_stage_n7'
    assert (len(d['quantities']),len(d['nodes']),len(d['edges']),len(d['datasets']))==(694,618,1054,29)
    assert _n(d,'SP16_N6_R_RELEASE_GATE')
    assert _n(d,'SP16_N7_R_RELEASE_GATE')

def test_n7_eq141_dag_uses_official_corrected_expression():
    n=_n(_d(),'SP16_N7_C_EQ141_CORRECTED')
    assert n['calculation_spec']['expression']=='2*sqrt(1+0.38/n)'
    assert 'Исх-8076' in n['notes']['normative_warning']
    assert '2+sqrt' in n['notes']['normative_warning']

def test_n7_table_inventory_covers_24_through_33_and_table29_interpolation_only_where_printed():
    d=_d(); ds=next(x for x in d['datasets'] if x['id']=='SP16_N7_TABLES_24_33_INVENTORY')
    rows=ds['storage']['rows']
    assert {r['table'] for r in rows}==set(range(24,34))
    p29=next(r['policy'] for r in rows if r['table']==29)
    assert '2<=n<=6' in p29 and 'interpolation' in p29

def test_n7_external_routes_are_explicit_in_route_policy():
    n=_n(_d(),'SP16_N7_K_ROUTE_POLICY')
    m={x['when']['value']:x['output_value'] for x in n['classification_rules']}
    assert m['10.3.7_external']=='external_provenance_required'
    assert m['10.1.3_external']=='external_provenance_required'
    assert m['10.3.11_software']=='certified_software_conditions'

def test_n7_actual_slenderness_and_limit_compliance_are_explicit_nodes():
    d=_d(); c=_n(d,'SP16_N7_C_ACTUAL_SLENDERNESS'); a=_n(d,'SP16_N7_A_SLENDERNESS')
    assert c['calculation_spec']['expression']=='lef/i'
    assert a['check_spec']['expression']=='lambda_actual <= lambda_u'
