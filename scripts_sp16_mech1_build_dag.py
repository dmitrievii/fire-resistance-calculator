from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'normative_graph/dag_v0.3.60_fire_ui24_fire_val1_routing_remediation.json'
OUT = ROOT / 'normative_graph/dag_v0.3.61_sp16_mech1_canonical_axes.json'
g = json.loads(SRC.read_text(encoding='utf-8'))
qs = {q['id']: q for q in g['quantities']}
ns = {n['id']: n for n in g['nodes']}
es = {e['id']: e for e in g['edges']}

def qdef(qid, symbol, name, dimension, unit, allowed, role='input', source='LOAD_INPUT', dtype='number'):
    return {
        'id': qid, 'symbol': symbol, 'name_ru': name, 'data_type': dtype, 'role': role,
        'physical_dimension': dimension, 'canonical_unit': unit, 'allowed_units': allowed,
        'source_policy': {'primary_source_type': source, 'allowed_source_types': [source], 'override_policy': 'forbidden'}
    }

def add_quantity(q):
    if q['id'] in qs: raise RuntimeError(f"duplicate quantity {q['id']}")
    g['quantities'].append(q); qs[q['id']] = q

def add_node(n):
    if n['id'] in ns: raise RuntimeError(f"duplicate node {n['id']}")
    g['nodes'].append(n); ns[n['id']] = n

def add_edge(e):
    if e['id'] in es: raise RuntimeError(f"duplicate edge {e['id']}")
    g['edges'].append(e); es[e['id']] = e

def cmp(qid, op, value): return {'type':'comparison','quantity_id':qid,'operator':op,'value':value}

# Canonical SP16 action quantities. M_x/M_y already exist and become direct inputs.
for qid, symbol, name in [
    ('M_x','M_x','Изгибающий момент Mx относительно главной оси x-x СП16'),
    ('M_y','M_y','Изгибающий момент My относительно главной оси y-y СП16'),
]:
    q = qs[qid]
    q['role'] = 'input'; q['name_ru'] = name
    q['source_policy'] = {'primary_source_type':'LOAD_INPUT','allowed_source_types':['LOAD_INPUT'],'override_policy':'forbidden'}

add_quantity(qdef('Q_x','Q_x','Поперечная сила Qx по СП16','force','N',['N','kN']))
add_quantity(qdef('Q_y','Q_y','Поперечная сила Qy по СП16','force','N',['N','kN']))
add_quantity(qdef('bimoment_required',None,'Требуется учитывать бимомент B',None,None,[],role='decision_state',source='USER_INPUT',dtype='boolean'))
add_quantity(qdef('mechanical_action_state',None,'Каноническое механическое состояние SP16-MECH1',None,None,[],role='intermediate',source='CALCULATED',dtype='object'))

# Update T/B semantics. B is a conditional input, not an implicit zero load.
qs['T_torsion']['symbol'] = 'T'
qs['T_torsion']['name_ru'] = 'Крутящий момент T относительно продольной оси элемента s'
qs['B_bimoment']['role'] = 'input'
qs['B_bimoment']['name_ru'] = 'Бимомент B (условный прямой ввод)'
qs['B_bimoment']['allowed_units'] = ['Nmm2','kNm2']
qs['B_bimoment']['source_policy'] = {'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT','CALCULATED'],'override_policy':'forbidden'}

# Author canonical actions directly at the load handoff.
loads = ns['SP554_H_SP20_LOADS']
loads['title'] = 'Расчётные усилия — канонические оси СП16'
loads['produces'] = [
    {'quantity_id':'special_load_combination','required':True,'binding_role':'output'},
    {'quantity_id':'N_force','required':True,'binding_role':'output'},
    {'quantity_id':'M_x','required':True,'binding_role':'output'},
    {'quantity_id':'M_y','required':True,'binding_role':'output'},
    {'quantity_id':'Q_x','required':True,'binding_role':'output'},
    {'quantity_id':'Q_y','required':True,'binding_role':'output'},
    {'quantity_id':'T_torsion','required':True,'binding_role':'output'},
    {'quantity_id':'sp16_local_load_F','required':False,'binding_role':'output'},
]
loads['required_output_quantity_ids'] = ['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion']
loads['reason'] = 'СП554 8.1 / СП20: signed усилия особого сочетания; SP16-MECH1 хранит изгиб и поперечные силы в обозначениях главных осей x-x/y-y СП16, а продольную ось элемента обозначает s.'
loads['notes'] = {
    'engineering_meaning':'Canonical SP16 action authoring contract. Member longitudinal axis is s; x-x/y-y are section principal axes.',
    'limitations':'Qy and torsion T are canonicalized but remain fail-closed in v0.58 until their dedicated runtimes are qualified.',
    'normative_warning':'v0.57 migration is sign-preserving: old local My→Mx, old local Mz→My, old local Qz→Qx, old local Qy→Qy. T is not Mx and is never mapped to B.'
}

# B applicability question and direct input.
add_node({
    'id':'SP16_D_BIMOMENT_REQUIRED','node_type':'decision','owner_standard_id':'SP16_2017',
    'title':'Необходимость учета бимомента B',
    'normative_refs':[
        {'standard_id':'SP16_2017','reference_kind':'annex','annex_ref':'А','quote_or_note':'B — бимомент, изгибно-крутящий бимомент; отдельная величина от Mx/My.'},
        {'standard_id':'SP554_2026','reference_kind':'formula','section':'10','clause':'10.1','formula_ref':'(10.3)','quote_or_note':'B входит в проверку двухосного изгиба при его наличии.'}
    ],
    'consumes':[],
    'produces':[{'quantity_id':'bimoment_required','required':True,'binding_role':'output'}],
    'applicability':None,
    'notes':{
        'engineering_meaning':'SP16-MECH1 deliberately asks only whether B must be present. It does not infer restrained torsion.',
        'limitations':'No restrained-torsion solver in v0.58. If B is required, the user supplies it directly.',
        'normative_warning':'Do not infer B from T. T and B are independent quantities in this release.'
    },
    'question':'Требуется ли учитывать бимомент B в рассматриваемом расчетном состоянии?',
    'decision_quantity_id':'bimoment_required',
    'options':[
        {'value':False,'label':'Нет','description':'Принять B = 0 для этого расчетного состояния.'},
        {'value':True,'label':'Да','description':'Ввести известное значение B напрямую.'}
    ]
})
add_node({
    'id':'SP16_I_BIMOMENT_DIRECT','node_type':'input','owner_standard_id':'SP16_2017',
    'title':'Прямой ввод бимомента B',
    'normative_refs':[
        {'standard_id':'SP16_2017','reference_kind':'annex','annex_ref':'А','quote_or_note':'B — бимомент, изгибно-крутящий бимомент.'},
        {'standard_id':'SP554_2026','reference_kind':'formula','section':'10','clause':'10.1','formula_ref':'(10.3)'}
    ],
    'consumes':[{'quantity_id':'bimoment_required','required':True,'binding_role':'condition'}],
    'produces':[{'quantity_id':'B_bimoment','required':True,'binding_role':'output'}],
    'applicability':cmp('bimoment_required','eq',True),
    'notes':{
        'engineering_meaning':'Direct signed B supplied by the user for the same section/load state as N, Mx and My.',
        'limitations':'The program does not derive B from torsional restraints in SP16-MECH1.',
        'normative_warning':'Use an externally determined signed bimoment. Do not enter torsional moment T here.'
    },
    'input_spec':{'user_prompt':'Введите известный бимомент B. В SP16-MECH1 он не вычисляется автоматически.'}
})
add_node({
    'id':'SP16_C_BIMOMENT_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017',
    'title':'B = 0 при отсутствии необходимости учета бимомента',
    'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'User explicitly states that bimoment is not required for this calculation state.'}],
    'consumes':[{'quantity_id':'bimoment_required','required':True,'binding_role':'condition'}],
    'produces':[{'quantity_id':'B_bimoment','required':True,'binding_role':'output'}],
    'applicability':cmp('bimoment_required','eq',False),
    'notes':{'engineering_meaning':'Explicit zero materialization after user decision.','limitations':None,'normative_warning':'This is not an automatic free-warping inference.'},
    'calculation_spec':{
        'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech1_explicit_zero_bimoment_v1',
        'bindings':[{'variable':'bimoment_required','quantity_id':'bimoment_required'}], 'rounding':{'mode':'none'}
    }
})

# Canonical stress-state classifier now consumes canonical actions + conditionally produced B.
stress = ns['SP554_D_STRESS_STATE']
stress['title'] = 'SP16-MECH1: каноническое механическое состояние и Verification Plan'
stress['consumes'] = [
    {'quantity_id':'special_load_combination','required':True,'binding_role':'input'},
    {'quantity_id':'N_force','required':True,'binding_role':'input'},
    {'quantity_id':'M_x','required':True,'binding_role':'input'},
    {'quantity_id':'M_y','required':True,'binding_role':'input'},
    {'quantity_id':'Q_x','required':True,'binding_role':'input'},
    {'quantity_id':'Q_y','required':True,'binding_role':'input'},
    {'quantity_id':'T_torsion','required':True,'binding_role':'input'},
    {'quantity_id':'B_bimoment','required':True,'binding_role':'input'},
]
stress['produces'] = [
    {'quantity_id':'stress_state','required':True,'binding_role':'output'},
    {'quantity_id':'Q_shear','required':True,'binding_role':'output'},
    {'quantity_id':'mechanical_action_state','required':True,'binding_role':'output'},
    {'quantity_id':'verification_plan','required':True,'binding_role':'output'},
]
stress['notes'] = {
    'engineering_meaning':'Creates the canonical SP16 action-state contract before downstream SP16/SP554 checks.',
    'limitations':'Q_shear is an explicit compatibility alias equal to Qx only. Qy is never collapsed into Qx/Q_shear. T remains a deferred calculation branch.',
    'normative_warning':'x-x/y-y are principal section axes per SP16. The longitudinal member axis is s. B is consumed as a distinct quantity and is never derived from T in v0.58.'
}
stress['calculation_spec'] = {
    'formula_type':'executor','expression_language':'executor_v1',
    'bindings':[{'variable':x,'quantity_id':x} for x in ['N_force','M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment']],
    'rounding':{'mode':'none'},'algorithm_id':'sp16_mech1_canonical_action_state_v1'
}

# Reroute load authoring through B decision before automatic classification.
e = es['E0034']
e['to_node_id'] = 'SP16_D_BIMOMENT_REQUIRED'
e['label'] = 'canonical actions'
e['quantity_ids'] = ['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion']
add_edge({'id':'MECH1_E_B_REQUIRED_TO_INPUT','from_node_id':'SP16_D_BIMOMENT_REQUIRED','to_node_id':'SP16_I_BIMOMENT_DIRECT','edge_type':'branch','label':'Да → прямой ввод B','condition':cmp('bimoment_required','eq',True),'quantity_ids':[]})
add_edge({'id':'MECH1_E_B_NOT_REQUIRED_TO_ZERO','from_node_id':'SP16_D_BIMOMENT_REQUIRED','to_node_id':'SP16_C_BIMOMENT_ZERO','edge_type':'branch','label':'Нет → B = 0','condition':cmp('bimoment_required','eq',False),'quantity_ids':[]})
add_edge({'id':'MECH1_E_B_INPUT_TO_STATE','from_node_id':'SP16_I_BIMOMENT_DIRECT','to_node_id':'SP554_D_STRESS_STATE','edge_type':'handoff','label':'B задан','condition':None,'quantity_ids':['B_bimoment']})
add_edge({'id':'MECH1_E_B_ZERO_TO_STATE','from_node_id':'SP16_C_BIMOMENT_ZERO','to_node_id':'SP554_D_STRESS_STATE','edge_type':'handoff','label':'B = 0','condition':None,'quantity_ids':['B_bimoment']})

# Deferred unsupported branch now keys off canonical Qy/T.
if 'UI16_E_PLAN_TO_DEFERRED_RESULT' in es:
    es['UI16_E_PLAN_TO_DEFERRED_RESULT']['condition'] = {
        'type':'any_of','conditions':[cmp('Q_y','neq',0),cmp('T_torsion','neq',0)]
    }
deferred_result = ns['SP554_R_UI16_DEFERRED_BRANCHES']
deferred_result['applicability'] = {'type':'any_of','conditions':[cmp('Q_y','neq',0),cmp('T_torsion','neq',0)]}
deferred_result['notes'] = {
    'engineering_meaning':'Terminal diagnostic for canonical Qy/T branches that remain outside the qualified runtime.',
    'limitations':'Qy and torsion T remain fail-closed in SP16-MECH1; they are canonicalized but not yet calculated. No Qy→Qx and no T→B substitution is permitted.',
    'normative_warning':'Fail-closed partial-result summary.'
}

# Keep old local quantities in the graph only as explicit deprecated import vocabulary.
for qid in ['load_My_local','load_Mz_local','load_Qy_local','load_Qz_local']:
    qs[qid]['role'] = 'deprecated_compatibility_input'
    qs[qid]['name_ru'] = qs[qid]['name_ru'] + ' [v0.57 legacy import only]'

parent = g['graph_id']
g['graph_id'] = 'sp16_sp554_dag_v0-3-61_sp16_mech1_canonical_axes'
g['graph_title'] = 'SP16 ↔ SP554 DAG v0.3.61 — SP16-MECH1 Canonical Axes + Mechanical State Contract'
g['description'] = 'Cumulative v0.3.61 over v0.3.60: canonical SP16 Mx/My/Qx/Qy axes with member axis s, explicit v0.57 axis migration, conditional direct bimoment input, and typed canonical mechanical-action state. Qy and torsion T remain fail-closed.'
md = g.setdefault('metadata',{})
md.update({
    'release_stage':'v0.58_sp16_mech1_canonical_axes_mechanical_state_contract_r1',
    'parent_graph_id':parent,
    'sp16_mech1_canonical_axes_closed':True,
    'sp16_mech1_member_axis_s_closed':True,
    'sp16_mech1_v057_axis_transform_closed':True,
    'sp16_mech1_direct_bimoment_input_closed':True,
    'sp16_mech1_qx_legacy_shear_alias_closed':True,
    'sp16_mech1_qy_runtime_closed':False,
    'sp16_mech1_torsion_runtime_closed':False,
    'sp16_mech1_full_ambient_gate_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]
    assert len(ids)==len(set(ids)), f'duplicate {key} id'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
