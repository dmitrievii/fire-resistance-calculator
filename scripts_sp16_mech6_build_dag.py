from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.65_sp16_mech5_direct_bimoment_pointwise_recovery.json'
OUT=ROOT/'normative_graph/dag_v0.3.66_sp16_mech6_mechanical_pass_gate.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

def qdef(qid,name,role='result',dtype='object'):
    return {'id':qid,'symbol':None,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
            'source_policy':{'primary_source_type':'CALCULATED','allowed_source_types':['CALCULATED'],'override_policy':'forbidden'}}
def addq(q):
    if q['id'] in qs: raise RuntimeError(q['id'])
    g['quantities'].append(q); qs[q['id']]=q
def addn(n):
    if n['id'] in ns: raise RuntimeError(n['id'])
    g['nodes'].append(n); ns[n['id']]=n
def adde(e):
    if e['id'] in es: raise RuntimeError(e['id'])
    g['edges'].append(e); es[e['id']]=e

def cmp(qid,op,val): return {'type':'comparison','quantity_id':qid,'operator':op,'value':val}

for q in [
    qdef('sp16_mechanical_verification','SP16 ambient — полный агрегированный реестр применимых проверок'),
    qdef('sp16_mechanical_gate_status','SP16 ambient — статус механического gate',dtype='string'),
    qdef('sp16_mechanical_pass','SP16_MECHANICAL_PASS',dtype='boolean'),
    qdef('sp16_mechanical_has_failed','SP16 ambient — имеется явный FAIL',dtype='boolean'),
    qdef('sp16_mechanical_has_unresolved','SP16 ambient — имеются unresolved/deferred обязательные проверки',dtype='boolean'),
    qdef('sp16_mechanical_governing_utilization','SP16 ambient — управляющий коэффициент использования',dtype='number'),
    qdef('sp16_mechanical_gate_confirmed','SP16 mechanical PASS просмотрен',role='decision_state',dtype='boolean'),
]: addq(q)

optional_evidence=[
 'ambient_axis_shear_state','ambient_torsion_runtime_closed','ambient_bimoment_runtime_closed','ambient_complete_pointwise_stress_state',
 'sp16_n3_eq5_eta_yield','sp16_n3_eq5_eta_ultimate','sp16_n3_eta7','sp16_n3_eta7a',
 'sp16_n4_eta41','sp16_n4_eta69','sp16_n4_eta_governing','sp16_n7_slenderness_pass','ltb_check_required',
 'sp16_n5_runtime_status','sp16_n6_web_status','sp16_n6_flange_status',
 'sp16_n9_external_gate_status','sp16_n9_clause1213_status','sp16_n10_general_prevention_status','sp16_n10_external_gate_status',
]
optional_evidence=[x for x in optional_evidence if x in qs]

addn({
 'id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH6 — агрегатор всех применимых проверок ambient case',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'section','section':'7','quote_or_note':'Axial strength/stability evidence.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'8','quote_or_note':'Bending/shear/LTB evidence.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'9','quote_or_note':'N+M / beam-column evidence.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'10','quote_or_note':'Effective lengths and slenderness.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'12','quote_or_note':'Fatigue when applicable.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'13','quote_or_note':'Brittle fracture when applicable.'},
 ],
 'consumes':[{'quantity_id':'sp16_applicability_census','required':True,'binding_role':'input'}]+[
     {'quantity_id':x,'required':False,'binding_role':'evidence'} for x in optional_evidence],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in [
     'sp16_mechanical_verification','sp16_mechanical_gate_status','sp16_mechanical_pass',
     'sp16_mechanical_has_failed','sp16_mechanical_has_unresolved']]+[
     {'quantity_id':'sp16_mechanical_governing_utilization','required':False,'binding_role':'output'}],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech6_aggregate_mechanical_verification_v1','bindings':[{'variable':'sp16_applicability_census','quantity_id':'sp16_applicability_census'}]+[{'variable':x,'quantity_id':x} for x in optional_evidence],'rounding':{'mode':'none'}},
 'notes':{
   'engineering_meaning':'Transforms the applicability census into a strict PASS/FAIL/N.A./DEFERRED ledger and a single SP16_MECHANICAL_PASS gate.',
   'limitations':'This release closes gate semantics, not every missing ambient workflow binding. Missing N3-N10 evidence remains explicit DEFERRED and blocks SP554.',
   'normative_warning':'Stress recovery alone is never accepted as normative PASS. Any unresolved applicable/context check blocks transition to SP554.'
 }
})

addn({
 'id':'SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16 Mechanical Verification — PASS',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Transition gate: all resolved applicable SP16 checks passed.'}],
 'consumes':[{'quantity_id':'sp16_mechanical_verification','required':True,'binding_role':'input'},{'quantity_id':'sp16_mechanical_pass','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_mechanical_gate_confirmed','required':True,'binding_role':'output'}],
 'applicability':cmp('sp16_mechanical_pass','eq',True),
 'question':'Все применимые проверки СП16 имеют нормативный PASS. Перейти к пожарному сочетанию и СП554?',
 'decision_quantity_id':'sp16_mechanical_gate_confirmed',
 'options':[{'value':True,'label':'Продолжить','description':'SP16_MECHANICAL_PASS = TRUE; перейти к FIRE_LOAD_CASE.'}],
 'notes':{'engineering_meaning':'Only reachable after aggregate SP16 PASS.','limitations':None,'normative_warning':'No bypass option is provided.'}
})

addn({
 'id':'SP16_R_AMBIENT_MECHANICAL_FAILED','node_type':'result','owner_standard_id':'SP16_2017',
 'title':'SP16 Mechanical Verification — FAIL',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'At least one applicable SP16 check has utilization > 1 or explicit fail evidence.'}],
 'consumes':[{'quantity_id':'sp16_mechanical_verification','required':True,'binding_role':'input'}],
 'produces':[],'applicability':cmp('sp16_mechanical_gate_status','eq','FAIL'),
 'result_quantity_ids':['sp16_mechanical_verification','sp16_mechanical_governing_utilization'],
 'result_kind':'noncompliance',
 'notes':{'engineering_meaning':'Ambient structural verification failed; fire calculation is not entered.','limitations':None,'normative_warning':'No SP554 transition is permitted.'}
})
addn({
 'id':'SP16_R_AMBIENT_MECHANICAL_INCOMPLETE','node_type':'result','owner_standard_id':'SP16_2017',
 'title':'SP16 Mechanical Verification — INCOMPLETE / fail-closed',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'One or more applicable/context checks lack qualified normative evidence.'}],
 'consumes':[{'quantity_id':'sp16_mechanical_verification','required':True,'binding_role':'input'}],
 'produces':[],'applicability':cmp('sp16_mechanical_gate_status','eq','INCOMPLETE_FAIL_CLOSED'),
 'result_quantity_ids':['sp16_mechanical_verification'],
 'result_kind':'diagnostic',
 'notes':{'engineering_meaning':'Lists exact missing SP16 branches/evidence before fire calculation can continue.','limitations':'Subsequent MECH increments will bind unresolved N3-N10 branches into the primary ambient route.','normative_warning':'INCOMPLETE is not PASS and cannot be overridden in guided mode.'}
})

# Existing census deferred branch remains unchanged.  The former no-deferred edge
# is re-targeted to the aggregate gate instead of directly entering the fire case.
e=es['MECH2_E_CENSUS_TO_FIRE_MODE']
e['to_node_id']='SP16_C_AMBIENT_MECHANICAL_AGGREGATOR'
e['label']='ambient census resolved → strict SP16 mechanical gate'
e['quantity_ids']=list(dict.fromkeys(e.get('quantity_ids',[])+['sp16_applicability_census']))

adde({'id':'MECH6_E_GATE_PASS','from_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','to_node_id':'SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM','edge_type':'branch','label':'SP16_MECHANICAL_PASS','condition':cmp('sp16_mechanical_gate_status','eq','PASS'),'quantity_ids':['sp16_mechanical_verification','sp16_mechanical_pass']})
adde({'id':'MECH6_E_GATE_FAIL','from_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','to_node_id':'SP16_R_AMBIENT_MECHANICAL_FAILED','edge_type':'branch','label':'SP16 explicit FAIL','condition':cmp('sp16_mechanical_gate_status','eq','FAIL'),'quantity_ids':['sp16_mechanical_verification']})
adde({'id':'MECH6_E_GATE_INCOMPLETE','from_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','to_node_id':'SP16_R_AMBIENT_MECHANICAL_INCOMPLETE','edge_type':'branch','label':'SP16 unresolved → fail-closed','condition':cmp('sp16_mechanical_gate_status','eq','INCOMPLETE_FAIL_CLOSED'),'quantity_ids':['sp16_mechanical_verification']})
adde({'id':'MECH6_E_PASS_TO_FIRE_MODE','from_node_id':'SP16_D_AMBIENT_MECHANICAL_PASS_CONFIRM','to_node_id':'SP16_D_FIRE_LOAD_CASE_MODE','edge_type':'control','label':'ambient SP16 gate confirmed','condition':cmp('sp16_mechanical_gate_confirmed','eq',True),'quantity_ids':['sp16_mechanical_pass']})

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-66_sp16_mech6_mechanical_pass_gate'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.66 — SP16-MECH6 Aggregate Mechanical PASS Gate'
g['description']='Cumulative v0.3.66 over v0.3.65: converts the ambient applicability census into a strict evidence-based SP16 mechanical gate. PASS/FAIL/N.A./DEFERRED are explicit; missing normative evidence is fail-closed and SP554 is reachable only when SP16_MECHANICAL_PASS is true. Existing N3-N10 evidence is consumed when present; this release does not fabricate missing workflow execution.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.63_sp16_mech6_mechanical_pass_gate_r1',
 'parent_graph_id':parent,
 'sp16_mech6_aggregate_gate_semantics_closed':True,
 'sp16_mech6_sp16_mechanical_pass_quantity_closed':True,
 'sp16_mech6_sp554_transition_requires_pass':True,
 'sp16_mech6_all_n3_n10_primary_flow_bindings_closed':False,
 'sp16_mech6_engineering_use_ready':False,
 'sp16_mech5_direct_bimoment_input_policy_preserved':True,
 'sp16_mech5_bimoment_from_t_solver_closed':False,
 'sp16_mech5_sp554_complex_state_handoff_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
