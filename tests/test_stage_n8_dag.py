from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / 'normative_graph' / 'dag_v0.3.37_stage_n8.json'


def _d():
    return json.loads(DAG.read_text(encoding='utf-8'))


def _n(d, node_id):
    return next(x for x in d['nodes'] if x['id'] == node_id)


def test_n8_dag_validates_frozen_schema():
    schema = json.loads((ROOT/'normative_graph'/'dag_schema.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema).validate(_d())


def test_n8_dag_identity_counts_and_frozen_n7_parent():
    d = _d()
    assert d['graph_id'] == 'sp16_sp554_dag_v0-3-37_stage_n8'
    assert (len(d['quantities']), len(d['nodes']), len(d['edges']), len(d['datasets'])) == (702,624,1060,30)
    assert _n(d, 'SP16_N7_R_RELEASE_GATE')
    assert _n(d, 'SP16_N8_R_RELEASE_GATE')
    e = next(x for x in d['edges'] if x['id'] == 'N8_E_001')
    assert e['from_node_id'] == 'SP16_N7_R_RELEASE_GATE'
    assert e['label'] == 'N1-N7 frozen'


def test_n8_table34_dataset_is_exact_grid_and_complete():
    d = _d()
    ds = next(x for x in d['datasets'] if x['id'] == 'SP16_N8_TABLE34')
    assert ds['interpolation']['method'] == 'none'
    assert ds['interpolation']['extrapolation'] == 'forbidden'
    rows = ds['storage']['rows']
    assert [(r['r_over_t'],r['c']) for r in rows] == [
        (100,0.22),(200,0.18),(300,0.16),(400,0.14),(600,0.11),
        (800,0.09),(1000,0.08),(1500,0.07),(2500,0.06),
    ]
    lookup = _n(d, 'SP16_N8_L_TABLE34_C')
    assert lookup['lookup_spec']['interpolation']['method'] == 'none'
    assert lookup['lookup_spec']['dataset_id'] == 'SP16_N8_TABLE34'


def test_n8_only_printed_interpolations_are_encoded():
    n = _n(_d(), 'SP16_N8_K_INTERPOLATION_POLICY')
    m = {x['when']['value']: x['output_value'] for x in n['classification_rules']}
    assert m['cylindrical_panel_11_2_3'] == 'printed_panel_0_8Ry_to_Ry'
    assert m['cylinder_external_pressure_11_2_4'] == 'printed_external_pressure_10_to_20'
    assert m['cylinder_combined_11_2_5'] == 'printed_external_pressure_10_to_20'
    assert m['cylinder_axial_11_2_1'] == 'none'
    assert 'Do not generalize' in n['notes']['normative_warning']


def test_n8_external_analysis_gate_is_explicit_for_11_1_4_11_1_5_and_ring():
    n = _n(_d(), 'SP16_N8_I_EXTERNAL_GATE')
    clauses = {r['clause'] for r in n['normative_refs']}
    assert {'11.1.4','11.1.5','11.2.4'} <= clauses
    assert n['input_spec']['allow_default_without_confirmation'] is False


def test_n8_release_gate_consumes_route_interpolation_and_external_status():
    n = _n(_d(), 'SP16_N8_R_RELEASE_GATE')
    q = {x['quantity_id'] for x in n['consumes']}
    assert q == {'sp16_n8_route_policy','sp16_n8_interpolation_policy','sp16_n8_external_gate_status'}
