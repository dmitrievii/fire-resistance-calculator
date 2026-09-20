import json
from pathlib import Path

import pytest

from standard_core.fire_bridge2_qualified_state import _classify_fire_bridge2_handoff
from standard_core.fire_ui0 import FireUIError

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json'


def _state(sigmas=(-80.0,120.0,35.0)):
    return {
        'schema':'sp16_mech5_complete_pointwise_state_v1',
        'normal_stress_complete':True,
        'points':[{'x_mm':float(i),'y_mm':0.0,'sigma_N_Mx_My_B_n_mm2':float(s)} for i,s in enumerate(sigmas)],
    }


def _values(qy=0.0,t=0.0,passed=True):
    return {
        'sp16_mechanical_pass':passed,
        'Q_y':qy,
        'T_torsion':t,
        'fire_complete_pointwise_stress_state':_state(),
    }


def test_bridge2_dag_metadata_and_internal_8_7_option():
    g=json.loads(DAG.read_text(encoding='utf8'))
    assert g['graph_id']=='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
    md=g['metadata']
    assert md['fire_bridge2_qualified_sp16_state_contract_closed'] is True
    assert md['fire_bridge2_internal_8_7_pointwise_normal_stress_route_closed'] is True
    assert md['fire_bridge2_qy_full_fire_handoff_closed'] is False
    assert md['fire_bridge2_t_full_fire_handoff_closed'] is False
    q={row['id']:row for row in g['quantities']}
    assert 'qualified_sp16_pointwise_stress' in [v['value'] for v in q['strength_coefficient_method']['enum_values']]
    n={row['id']:row for row in g['nodes']}
    opts=[o['value'] for o in n['SP554_D_GAMMA_T_METHOD']['options']]
    assert 'qualified_sp16_pointwise_stress' in opts


def test_bridge2_full_route_and_governing_normal_stress():
    out=_classify_fire_bridge2_handoff(_values())
    assert out['fire_bridge2_route_status']=='FULLY_SUPPORTED'
    assert out['fire_bridge2_full_handoff_closed'] is True
    assert out['fire_bridge2_sigma_n_static']==pytest.approx(120.0)
    c=out['fire_bridge2_contract']
    assert c['internal_8_7_full_route_allowed'] is True
    assert c['unsupported_fire_actions']==[]
    assert c['Qy_to_Qx_substitution_forbidden'] is True
    assert c['T_to_B_substitution_forbidden'] is True


def test_bridge2_qy_remains_fire_fail_closed_but_normal_diagnostic_preserved():
    out=_classify_fire_bridge2_handoff(_values(qy=15_000.0))
    assert out['fire_bridge2_route_status']=='FAIL_CLOSED_QY'
    assert out['fire_bridge2_full_handoff_closed'] is False
    assert out['fire_bridge2_sigma_n_static']==pytest.approx(120.0)
    c=out['fire_bridge2_contract']
    assert c['internal_8_7_normal_stress_available'] is True
    assert c['internal_8_7_full_route_allowed'] is False
    assert c['unsupported_fire_actions']==['Qy']


def test_bridge2_torsion_remains_fire_fail_closed():
    out=_classify_fire_bridge2_handoff(_values(t=2_000_000.0))
    assert out['fire_bridge2_route_status']=='FAIL_CLOSED_T'
    assert out['fire_bridge2_full_handoff_closed'] is False
    assert out['fire_bridge2_contract']['clause_8_7_not_universal_shear_or_torsion_bypass'] is True


def test_bridge2_qy_and_t_combined_remain_fail_closed():
    out=_classify_fire_bridge2_handoff(_values(qy=10.0,t=20.0))
    assert out['fire_bridge2_route_status']=='FAIL_CLOSED_QY_T'
    assert out['fire_bridge2_contract']['unsupported_fire_actions']==['Qy','T']


def test_bridge2_requires_strict_sp16_pass():
    with pytest.raises(FireUIError, match='SP16_MECHANICAL_PASS'):
        _classify_fire_bridge2_handoff(_values(passed=False))


def test_bridge2_explicit_sections_route_does_not_require_internal_8_7_pointwise_state():
    v=_values(); v['fire_complete_pointwise_stress_state']={'normal_stress_complete':False,'points':[]}
    out=_classify_fire_bridge2_handoff(v)
    assert out['fire_bridge2_route_status']=='FULLY_SUPPORTED'
    assert out['fire_bridge2_full_handoff_closed'] is True
    assert 'fire_bridge2_sigma_n_static' not in out
    c=out['fire_bridge2_contract']
    assert c['explicit_sections_9_11_route_allowed'] is True
    assert c['internal_8_7_normal_stress_available'] is False
    assert c['internal_8_7_full_route_allowed'] is False
