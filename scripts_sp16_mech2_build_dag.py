from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'normative_graph/dag_v0.3.61_sp16_mech1_canonical_axes.json'
OUT = ROOT / 'normative_graph/dag_v0.3.62_sp16_mech2_load_cases_applicability_census.json'
g = json.loads(SRC.read_text(encoding='utf-8'))
qs = {q['id']: q for q in g['quantities']}
ns = {n['id']: n for n in g['nodes']}
es = {e['id']: e for e in g['edges']}

def qdef(qid, symbol, name, dimension, unit, allowed, role='input', source='LOAD_INPUT', dtype='number'):
    return {'id':qid,'symbol':symbol,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':dimension,'canonical_unit':unit,'allowed_units':allowed,'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}}

def addq(q):
    if q['id'] in qs: raise RuntimeError(f'duplicate quantity {q["id"]}')
    g['quantities'].append(q); qs[q['id']]=q

def addn(n):
    if n['id'] in ns: raise RuntimeError(f'duplicate node {n["id"]}')
    g['nodes'].append(n); ns[n['id']]=n

def adde(e):
    if e['id'] in es: raise RuntimeError(f'duplicate edge {e["id"]}')
    g['edges'].append(e); es[e['id']]=e

def cmp(qid,op,value): return {'type':'comparison','quantity_id':qid,'operator':op,'value':value}

# Dedicated ambient quantities. Existing N_force/M_x/... remain the FIRE scalar
# compatibility contract until downstream SP554 formulas are fully retyped.
for qid,symbol,name,dim,unit,allowed in [
    ('ambient_N_force','N','Ambient: продольная сила N','force','N',['N','kN']),
    ('ambient_M_x','M_x','Ambient: изгибающий момент Mx','moment','Nmm',['Nmm','kNm']),
    ('ambient_M_y','M_y','Ambient: изгибающий момент My','moment','Nmm',['Nmm','kNm']),
    ('ambient_Q_x','Q_x','Ambient: поперечная сила Qx','force','N',['N','kN']),
    ('ambient_Q_y','Q_y','Ambient: поперечная сила Qy','force','N',['N','kN']),
    ('ambient_T_torsion','T','Ambient: крутящий момент T','moment','Nmm',['Nmm','kNm']),
    ('ambient_B_bimoment','B','Ambient: бимомент B','bimoment','Nmm2',['Nmm2','kNm2']),
]: addq(qdef(qid,symbol,name,dim,unit,allowed))
addq(qdef('ambient_load_combination',None,'Описание обычного расчетного сочетания',None,None,[],source='LOAD_INPUT',dtype='object'))
addq(qdef('ambient_bimoment_required',None,'Ambient: требуется учитывать бимомент B',None,None,[],role='decision_state',source='USER_INPUT',dtype='boolean'))
addq(qdef('ambient_load_case',None,'AMBIENT_LOAD_CASE',None,None,[],role='intermediate',source='CALCULATED',dtype='object'))
addq(qdef('ambient_mechanical_action_state',None,'Ambient canonical mechanical action state',None,None,[],role='intermediate',source='CALCULATED',dtype='object'))
addq(qdef('sp16_applicability_census',None,'SP16 applicability census для ambient case',None,None,[],role='intermediate',source='CALCULATED',dtype='object'))
addq(qdef('sp16_census_has_deferred_active',None,'В ambient census есть активные неподдержанные ветви',None,None,[],role='diagnostic',source='CALCULATED',dtype='boolean'))
addq(qdef('sp16_applicability_census_confirmed',None,'Ambient SP16 applicability census просмотрен',None,None,[],role='decision_state',source='USER_INPUT',dtype='boolean'))
addq(qdef('fire_load_case_mode',None,'Источник усилий пожарной ситуации',None,None,[],role='decision_state',source='USER_INPUT',dtype='string'))
addq(qdef('fire_load_case',None,'FIRE_LOAD_CASE',None,None,[],role='intermediate',source='CALCULATED',dtype='object'))

# Ambient action input.
addn({
 'id':'SP16_I_AMBIENT_LOADS','node_type':'input','owner_standard_id':'SP16_2017','title':'AMBIENT_LOAD_CASE — расчётные усилия при нормальной температуре',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Independent ambient mechanical action state used for the SP16 mechanical verification layer.'}],
 'consumes':[],
 'produces':[
   {'quantity_id':'ambient_load_combination','required':True,'binding_role':'output'},
   *[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion']],
 ],
 'applicability':None,
 'notes':{'engineering_meaning':'Normal-temperature design action state. It is distinct from the fire accidental-design action state.','limitations':'Qy and T may be entered so applicability is not hidden, but non-zero values remain fail-closed until SP16-MECH3/4.','normative_warning':'Do not assume ambient and fire combinations are identical unless explicitly selected later.'},
 'input_spec':{'user_prompt':'Введите расчетные усилия обычной проектной ситуации в канонических осях СП16.'}
})
addn({
 'id':'SP16_D_AMBIENT_BIMOMENT_REQUIRED','node_type':'decision','owner_standard_id':'SP16_2017','title':'AMBIENT_LOAD_CASE — необходимость учета бимомента B',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'annex','annex_ref':'А','quote_or_note':'B — отдельный изгибно-крутящий бимомент.'}],
 'consumes':[], 'produces':[{'quantity_id':'ambient_bimoment_required','required':True,'binding_role':'output'}], 'applicability':None,
 'question':'Для обычного расчетного состояния требуется учитывать бимомент B?', 'decision_quantity_id':'ambient_bimoment_required',
 'options':[{'value':False,'label':'Нет','description':'Принять B = 0 для ambient case.'},{'value':True,'label':'Да','description':'Ввести известное signed B напрямую.'}],
 'notes':{'engineering_meaning':'Same simplified direct-B policy as SP16-MECH1, now scoped to the ambient case.','limitations':'No restrained-torsion solver.','normative_warning':'T and B are not interchangeable.'}
})
addn({
 'id':'SP16_I_AMBIENT_BIMOMENT_DIRECT','node_type':'input','owner_standard_id':'SP16_2017','title':'AMBIENT_LOAD_CASE — прямой ввод B',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'annex','annex_ref':'А'}],
 'consumes':[{'quantity_id':'ambient_bimoment_required','required':True,'binding_role':'condition'}],
 'produces':[{'quantity_id':'ambient_B_bimoment','required':True,'binding_role':'output'}], 'applicability':cmp('ambient_bimoment_required','eq',True),
 'input_spec':{'user_prompt':'Введите известный signed бимомент B для ambient case.'},
 'notes':{'engineering_meaning':'Direct signed ambient bimoment.','limitations':'Not derived from T or restraint conditions.','normative_warning':'Same section/load state as ambient N/M/Q/T.'}
})
addn({
 'id':'SP16_C_AMBIENT_BIMOMENT_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017','title':'AMBIENT_LOAD_CASE — B = 0',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Explicit user decision that B is not required.'}],
 'consumes':[{'quantity_id':'ambient_bimoment_required','required':True,'binding_role':'condition'}],
 'produces':[{'quantity_id':'ambient_B_bimoment','required':True,'binding_role':'output'}], 'applicability':cmp('ambient_bimoment_required','eq',False),
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech2_ambient_zero_bimoment_v1','bindings':[{'variable':'ambient_bimoment_required','quantity_id':'ambient_bimoment_required'}],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Explicit B=0 materialization.','limitations':None,'normative_warning':'Not an inferred free-warping result.'}
})
addn({
 'id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16 Applicability Census — ambient case',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'section','section':'7','quote_or_note':'Axial-member strength/stability family.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'8','quote_or_note':'Bending/shear family.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'9','quote_or_note':'Beam-column / N+M family.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'10','quote_or_note':'Effective-length/slenderness family.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['ambient_load_combination','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_load_case','ambient_mechanical_action_state','sp16_applicability_census','sp16_census_has_deferred_active']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech2_ambient_applicability_census_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['ambient_load_combination','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Enumerates all action-driven SP16 check families and preserves context-driven families as explicit unresolved applicability questions.','limitations':'This is a census, not the full SP16 PASS gate.','normative_warning':'No active check is silently omitted because a dedicated runtime is not yet qualified.'}
})
addn({
 'id':'SP16_D_AMBIENT_CENSUS_CONFIRM','node_type':'decision','owner_standard_id':'SP16_2017','title':'SP16 Applicability Census — проверка состава обязательных ветвей',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Read-only confirmation of automatically derived applicability census.'}],
 'consumes':[{'quantity_id':'sp16_applicability_census','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_applicability_census_confirmed','required':True,'binding_role':'output'}], 'applicability':None,
 'question':'Applicability census сформирован. Продолжить?', 'decision_quantity_id':'sp16_applicability_census_confirmed',
 'options':[{'value':True,'label':'Продолжить','description':'Перейти к определению нагрузок пожарной ситуации.'}],
 'notes':{'engineering_meaning':'The user reviews but does not manually choose/remove mandatory SP16 branches.','limitations':'Full execution gate follows in SP16-MECH6.','normative_warning':'Active deferred branches remain fail-closed.'}
})
addn({
 'id':'SP16_R_AMBIENT_UNSUPPORTED_ACTIONS','node_type':'result','owner_standard_id':'SP16_2017','title':'Ambient SP16 verification deferred — активна неподдержанная механическая ветвь',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Fail-closed SP16-MECH2 staging result.'}],
 'consumes':[{'quantity_id':'sp16_applicability_census','required':True,'binding_role':'input'}], 'produces':[],
 'applicability':cmp('sp16_census_has_deferred_active','eq',True),
 'notes':{'engineering_meaning':'Stops before fire mechanics when ambient Qy/T requires a runtime not yet qualified.','limitations':'SP16-MECH3/4 will close these action components.','normative_warning':'No transition to SP554 is permitted for an unresolved ambient active action branch.'}
})
addn({
 'id':'SP16_D_FIRE_LOAD_CASE_MODE','node_type':'decision','owner_standard_id':'SP16_2017','title':'FIRE_LOAD_CASE — источник усилий',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'8','clause':'8.1','quote_or_note':'Fire calculation uses the accidental/special-combination action state; it need not equal the ordinary design state.'}],
 'consumes':[{'quantity_id':'ambient_load_case','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'fire_load_case_mode','required':True,'binding_role':'output'}], 'applicability':None,
 'question':'Какие усилия использовать для пожарной ситуации?', 'decision_quantity_id':'fire_load_case_mode',
 'options':[
   {'value':'same_as_ambient','label':'Использовать те же усилия','description':'Явно скопировать ambient actions в FIRE_LOAD_CASE.'},
   {'value':'separate','label':'Задать отдельное пожарное сочетание','description':'Ввести отдельные signed N, Mx, My, Qx, Qy, T и затем B.'}
 ],
 'notes':{'engineering_meaning':'Explicit separation of ordinary and fire action states.','limitations':'Combination-factor generation remains external/current SP20 handoff scope.','normative_warning':'The program never assumes equality silently.'}
})
addn({
 'id':'SP16_C_FIRE_LOADS_INHERIT_AMBIENT','node_type':'calculation','owner_standard_id':'SP16_2017','title':'FIRE_LOAD_CASE = AMBIENT_LOAD_CASE — explicit copy',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'derived_graph_logic','quote_or_note':'User explicitly selected same actions for the fire case.'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['fire_load_case_mode','ambient_load_combination','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment','fire_load_case']],
 'applicability':cmp('fire_load_case_mode','eq','same_as_ambient'),
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech2_fire_inherit_ambient_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['ambient_load_combination','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Explicit value-preserving copy into the current downstream fire scalar contract.','limitations':'Does not generate accidental-combination coefficients.','normative_warning':'Equality exists only because the user selected it.'}
})
addn({
 'id':'SP16_C_FIRE_LOAD_CASE_FINALIZE','node_type':'calculation','owner_standard_id':'SP16_2017','title':'FIRE_LOAD_CASE — typed state finalization',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'8','clause':'8.1'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment']],
 'produces':[{'quantity_id':'fire_load_case','required':True,'binding_role':'output'}], 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech2_fire_finalize_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Creates typed FIRE_LOAD_CASE after separate fire actions and B are resolved.','limitations':None,'normative_warning':'This node does not alter signs or values.'}
})

# Existing fire action authoring becomes explicitly the separate fire case.
loads=ns['SP554_H_SP20_LOADS']
loads['title']='FIRE_LOAD_CASE — отдельное пожарное сочетание'
loads['produces']=[
 {'quantity_id':'special_load_combination','required':True,'binding_role':'output'},
 *[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['N_force','M_x','M_y','Q_x','Q_y','T_torsion']],
 {'quantity_id':'sp16_local_load_F','required':False,'binding_role':'output'},
]
loads['required_output_quantity_ids']=['special_load_combination','N_force','M_x','M_y','Q_x','Q_y','T_torsion']
loads['notes']={'engineering_meaning':'Separate fire accidental-design action state in canonical SP16 axes.','limitations':'Qy/T may be entered but remain fail-closed until their dedicated runtimes are qualified.','normative_warning':'This is FIRE_LOAD_CASE, not the ambient SP16 design state.'}

# The existing B branch is now explicitly FIRE-scoped.
ns['SP16_D_BIMOMENT_REQUIRED']['title']='FIRE_LOAD_CASE — необходимость учета бимомента B'
ns['SP16_D_BIMOMENT_REQUIRED']['question']='Для пожарного расчетного состояния требуется учитывать бимомент B?'
ns['SP16_I_BIMOMENT_DIRECT']['title']='FIRE_LOAD_CASE — прямой ввод B'
ns['SP16_C_BIMOMENT_ZERO']['title']='FIRE_LOAD_CASE — B = 0'

# The typed fire case becomes a required input to the existing canonical fire state producer.
stress=ns['SP554_D_STRESS_STATE']
stress['consumes']=[{'quantity_id':'fire_load_case','required':True,'binding_role':'input'}]+[x for x in stress['consumes'] if x['quantity_id']!='special_load_combination']
stress['notes']['engineering_meaning']='Creates the canonical FIRE mechanical action-state contract after explicit ambient/fire load-case separation.'
stress['notes']['normative_warning']='Consumes FIRE_LOAD_CASE only; ambient actions remain separate and are never overwritten.'

# Reroute entry into the load subsystem.
es['E0084']['to_node_id']='SP16_I_AMBIENT_LOADS'; es['E0084']['label']='ambient SP16 load case'
# Remove old direct load -> B path and re-create via fire mode.
es['E0034']['from_node_id']='SP554_H_SP20_LOADS'; es['E0034']['to_node_id']='SP16_D_BIMOMENT_REQUIRED'; es['E0034']['label']='separate fire actions'

adde({'id':'MECH2_E_AMBIENT_LOADS_TO_B','from_node_id':'SP16_I_AMBIENT_LOADS','to_node_id':'SP16_D_AMBIENT_BIMOMENT_REQUIRED','edge_type':'control','label':'ambient actions','condition':None,'quantity_ids':['ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion']})
adde({'id':'MECH2_E_AMBIENT_B_YES','from_node_id':'SP16_D_AMBIENT_BIMOMENT_REQUIRED','to_node_id':'SP16_I_AMBIENT_BIMOMENT_DIRECT','edge_type':'branch','label':'Да → прямой B','condition':cmp('ambient_bimoment_required','eq',True),'quantity_ids':[]})
adde({'id':'MECH2_E_AMBIENT_B_NO','from_node_id':'SP16_D_AMBIENT_BIMOMENT_REQUIRED','to_node_id':'SP16_C_AMBIENT_BIMOMENT_ZERO','edge_type':'branch','label':'Нет → B=0','condition':cmp('ambient_bimoment_required','eq',False),'quantity_ids':[]})
adde({'id':'MECH2_E_AMBIENT_B_INPUT_TO_CENSUS','from_node_id':'SP16_I_AMBIENT_BIMOMENT_DIRECT','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'ambient B ready','condition':None,'quantity_ids':['ambient_B_bimoment']})
adde({'id':'MECH2_E_AMBIENT_B_ZERO_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_BIMOMENT_ZERO','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'ambient B=0','condition':None,'quantity_ids':['ambient_B_bimoment']})
adde({'id':'MECH2_E_CENSUS_TO_CONFIRM','from_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','to_node_id':'SP16_D_AMBIENT_CENSUS_CONFIRM','edge_type':'control','label':'SP16 applicability census','condition':None,'quantity_ids':['sp16_applicability_census']})
adde({'id':'MECH2_E_CENSUS_DEFERRED_STOP','from_node_id':'SP16_D_AMBIENT_CENSUS_CONFIRM','to_node_id':'SP16_R_AMBIENT_UNSUPPORTED_ACTIONS','edge_type':'branch','label':'active deferred mechanics','condition':cmp('sp16_census_has_deferred_active','eq',True),'quantity_ids':['sp16_applicability_census']})
adde({'id':'MECH2_E_CENSUS_TO_FIRE_MODE','from_node_id':'SP16_D_AMBIENT_CENSUS_CONFIRM','to_node_id':'SP16_D_FIRE_LOAD_CASE_MODE','edge_type':'branch','label':'ambient census accepted','condition':cmp('sp16_census_has_deferred_active','eq',False),'quantity_ids':['ambient_load_case']})
adde({'id':'MECH2_E_FIRE_MODE_INHERIT','from_node_id':'SP16_D_FIRE_LOAD_CASE_MODE','to_node_id':'SP16_C_FIRE_LOADS_INHERIT_AMBIENT','edge_type':'branch','label':'same as ambient','condition':cmp('fire_load_case_mode','eq','same_as_ambient'),'quantity_ids':[]})
adde({'id':'MECH2_E_FIRE_MODE_SEPARATE','from_node_id':'SP16_D_FIRE_LOAD_CASE_MODE','to_node_id':'SP554_H_SP20_LOADS','edge_type':'branch','label':'separate fire case','condition':cmp('fire_load_case_mode','eq','separate'),'quantity_ids':[]})
adde({'id':'MECH2_E_FIRE_INHERIT_TO_STATE','from_node_id':'SP16_C_FIRE_LOADS_INHERIT_AMBIENT','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'typed fire case ready','condition':None,'quantity_ids':['fire_load_case']})
# Existing fire B branches finalize the typed case before classification.
es['MECH1_E_B_INPUT_TO_STATE']['to_node_id']='SP16_C_FIRE_LOAD_CASE_FINALIZE'; es['MECH1_E_B_INPUT_TO_STATE']['label']='fire B задан'
es['MECH1_E_B_ZERO_TO_STATE']['to_node_id']='SP16_C_FIRE_LOAD_CASE_FINALIZE'; es['MECH1_E_B_ZERO_TO_STATE']['label']='fire B = 0'
adde({'id':'MECH2_E_FIRE_FINALIZE_TO_STATE','from_node_id':'SP16_C_FIRE_LOAD_CASE_FINALIZE','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'FIRE_LOAD_CASE ready','condition':None,'quantity_ids':['fire_load_case']})

# v0.59 makes Qy/T visible inputs for correct applicability detection; nonzero
# values remain fail-closed via ambient census and existing fire deferred result.
parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-62_sp16_mech2_load_cases_applicability_census'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.62 — SP16-MECH2 Ambient/Fire Load Cases + Applicability Census'
g['description']='Cumulative v0.3.62 over v0.3.61: explicit AMBIENT_LOAD_CASE and FIRE_LOAD_CASE, explicit inheritance/separate-fire choice, and machine-readable SP16 ambient applicability census. Qy/T remain fail-closed.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.59_sp16_mech2_load_cases_applicability_census_r1',
 'parent_graph_id':parent,
 'sp16_mech2_ambient_fire_load_cases_closed':True,
 'sp16_mech2_explicit_fire_inheritance_closed':True,
 'sp16_mech2_applicability_census_closed':True,
 'sp16_mech2_qy_runtime_closed':False,
 'sp16_mech2_torsion_runtime_closed':False,
 'sp16_mech2_full_ambient_gate_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
 ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
