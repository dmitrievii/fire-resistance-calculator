from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.69_sp16_mech9_remaining_ambient_closure.json'
OUT=ROOT/'normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

def qdef(qid,name,role='result',dtype='object',enum_values=None,source='CALCULATED',unit=None):
    q={'id':qid,'symbol':None,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':'stress' if unit=='MPa' else None,'canonical_unit':unit,'allowed_units':[] if unit is None else [unit],
       'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}}
    if enum_values is not None:
        q['enum_values']=[{'value':v,'label':str(v)} for v in enum_values]
    return q

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
def allof(*conds): return {'type':'all_of','conditions':list(conds)}
def anyof(*conds): return {'type':'any_of','conditions':list(conds)}

addq(qdef('fire_bridge2_contract','FIRE-BRIDGE2 — квалифицированный контракт SP16 → SP554'))
addq(qdef('fire_bridge2_route_status','FIRE-BRIDGE2 — статус маршрута',dtype='enum',enum_values=['FULLY_SUPPORTED','FAIL_CLOSED_QY','FAIL_CLOSED_T','FAIL_CLOSED_QY_T']))
addq(qdef('fire_bridge2_full_handoff_closed','FIRE-BRIDGE2 — полный переход в SP554 разрешен',dtype='boolean'))
addq(qdef('fire_bridge2_sigma_n_static','FIRE-BRIDGE2 — управляющее |σn| из квалифицированного pointwise state',dtype='number',unit='MPa'))

# Existing sigma_n_static can now also be produced internally from the qualified SP16 pointwise state.
sp=qs['sigma_n_static']['source_policy']
sp['allowed_source_types']=['EXTERNAL_STANDARD_RESULT','CALCULATED']
sp['primary_source_type']='EXTERNAL_STANDARD_RESULT'

# Add a third method choice: qualified pointwise stress generated inside this package.
method_q=qs['strength_coefficient_method']
vals=[row['value'] for row in method_q['enum_values']]
if 'qualified_sp16_pointwise_stress' not in vals:
    method_q['enum_values'].append({'value':'qualified_sp16_pointwise_stress','label':'по квалифицированному pointwise SP16 state, п.8.7'})
method_node=ns['SP554_D_GAMMA_T_METHOD']
if not any(o.get('value')=='qualified_sp16_pointwise_stress' for o in method_node['options']):
    method_node['options'].append({
        'value':'qualified_sp16_pointwise_stress',
        'label':'П.8.7: из квалифицированного SP16 pointwise state',
        'description':'Автоматически использовать максимальное |σn| из полного FIRE pointwise N/Mx/My/B state. Разрешено только после FIRE-BRIDGE2 и только без неподдержанных Qy/T.'
    })
method_node['notes']['normative_warning']='П.8.7 является маршрутом нормального напряжения. Он не заменяет отдельные проверки поперечной силы или кручения; FIRE-BRIDGE2 блокирует внутренний маршрут при Qy≠0 или T≠0.'

addn({
 'id':'SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE','node_type':'calculation','owner_standard_id':'SP554_2026',
 'title':'FIRE-BRIDGE2 — квалифицированный SP16 complex-state handoff',
 'normative_refs':[
   {'standard_id':'SP554_2026','reference_kind':'clause','section':'4','clause':'4.1'},
   {'standard_id':'SP554_2026','reference_kind':'clause','section':'8','clause':'8.7'},
   {'standard_id':'SP554_2026','reference_kind':'section','section':'9-11'},
   {'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','quote_or_note':'Consumes only a state reached after the strict SP16_MECHANICAL_PASS gate and the FIRE_LOAD_CASE mechanics recovery.'}
 ],
 'consumes':[
   {'quantity_id':'Q_y','required':True,'binding_role':'input'},
   {'quantity_id':'T_torsion','required':True,'binding_role':'input'},
   {'quantity_id':'fire_complete_pointwise_stress_state','required':True,'binding_role':'input'},
   {'quantity_id':'verification_plan','required':True,'binding_role':'input'},
 ],
 'produces':[
   {'quantity_id':'fire_bridge2_contract','required':True,'binding_role':'output'},
   {'quantity_id':'fire_bridge2_route_status','required':True,'binding_role':'output'},
   {'quantity_id':'fire_bridge2_full_handoff_closed','required':True,'binding_role':'output'},
   {'quantity_id':'fire_bridge2_sigma_n_static','required':False,'binding_role':'output'},
 ],
 'applicability':None,
 'calculation_spec':{
   'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'fire_bridge2_qualified_sp16_state_v1',
   'bindings':[
      {'variable':'Q_y','quantity_id':'Q_y'},
      {'variable':'T_torsion','quantity_id':'T_torsion'},
      {'variable':'fire_complete_pointwise_stress_state','quantity_id':'fire_complete_pointwise_stress_state'},
      {'variable':'verification_plan','quantity_id':'verification_plan'},
   ],'rounding':{'mode':'none'}
 },
 'notes':{
   'engineering_meaning':'Typed FIRE handoff after a qualified SP16 ambient gate. Derives the governing normal stress from the complete same-point FIRE mechanics state and classifies whether every active action has a current SP554 fire route.',
   'limitations':'Nonzero Qy and general T remain fail-closed. Biaxial Mx/My and direct B may participate in the complete normal-stress state when upstream MECH5 recovery is closed.',
   'normative_warning':'SP554 8.7 is not a universal bypass for missing shear/torsion fire checks. No Qy→Qx and no T→B substitution is permitted.'
 }
})

addn({
 'id':'SP554_FIRE_BRIDGE2_C_INTERNAL_8_7_STRESS','node_type':'calculation','owner_standard_id':'SP554_2026',
 'title':'FIRE-BRIDGE2 — σn из квалифицированного SP16 pointwise state для п.8.7',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'8','clause':'8.7'}],
 'consumes':[
   {'quantity_id':'fire_bridge2_contract','required':True,'binding_role':'gate'},
   {'quantity_id':'fire_bridge2_sigma_n_static','required':True,'binding_role':'input'},
 ],
 'produces':[{'quantity_id':'sigma_n_static','required':True,'binding_role':'output'}],
 'applicability':None,
 'calculation_spec':{
    'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'fire_bridge2_internal_8_7_stress_v1',
    'bindings':[
       {'variable':'fire_bridge2_contract','quantity_id':'fire_bridge2_contract'},
       {'variable':'fire_bridge2_sigma_n_static','quantity_id':'fire_bridge2_sigma_n_static'},
    ],'rounding':{'mode':'none'}
 },
 'notes':{
   'engineering_meaning':'Materializes σn for the existing SP554 8.7 gamma_T formula directly from the qualified package pointwise state.',
   'limitations':'Available only when FIRE-BRIDGE2 declares the full route supported; blocked for nonzero Qy/T.',
   'normative_warning':'This node does not combine shear/torsion into an equivalent normal stress.'
 }
})

# Rewire the old post-plan split through the typed bridge. The old direct routes are removed/recreated from the bridge node.
remove_ids={'E0087','E0214','UI16_E_PLAN_TO_DEFERRED_RESULT'}
g['edges']=[e for e in g['edges'] if e['id'] not in remove_ids]
es={e['id']:e for e in g['edges']}
adde({'id':'FIRE_BRIDGE2_E_PLAN_TO_CLASSIFIER','from_node_id':'SP554_D_VERIFICATION_PLAN_CONFIRM','to_node_id':'SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE','edge_type':'control','label':'confirmed fire verification plan → typed SP16/SP554 bridge','condition':cmp('verification_plan_confirmed','eq',True),'quantity_ids':['verification_plan','fire_complete_pointwise_stress_state']})
adde({'id':'FIRE_BRIDGE2_E_FULL_TO_HAS_MX','from_node_id':'SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE','to_node_id':'SP554_K_HAS_MX','edge_type':'control','label':'FIRE-BRIDGE2 full supported route','condition':cmp('fire_bridge2_full_handoff_closed','eq',True),'quantity_ids':['fire_bridge2_contract']})
adde({'id':'FIRE_BRIDGE2_E_TENSION_TO_GC','from_node_id':'SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE','to_node_id':'SP16_D_GC_T','edge_type':'branch','label':'FIRE-BRIDGE2 full route / central tension','condition':allof(cmp('fire_bridge2_full_handoff_closed','eq',True),cmp('stress_state','eq','central_tension')),'quantity_ids':['fire_bridge2_contract']})
adde({'id':'FIRE_BRIDGE2_E_BLOCKED_TO_RESULT','from_node_id':'SP554_FIRE_BRIDGE2_C_QUALIFIED_STATE','to_node_id':'SP554_R_UI16_DEFERRED_BRANCHES','edge_type':'branch','label':'FIRE-BRIDGE2: Qy/T requires unclosed fire-specific route','condition':cmp('fire_bridge2_full_handoff_closed','eq',False),'quantity_ids':['fire_bridge2_contract','fire_bridge2_route_status']})

# Improve the terminal semantics: mechanics exists, but the fire-specific handoff is not closed.
r=ns['SP554_R_UI16_DEFERRED_BRANCHES']
r['title']='FIRE-BRIDGE2 — полный расчет огнестойкости заблокирован неподдержанным Qy/T'
r['consumes']=[{'quantity_id':'fire_bridge2_contract','required':True,'binding_role':'input'}]
r['applicability']=anyof(cmp('Q_y','neq',0.0),cmp('T_torsion','neq',0.0))
r['notes']={
 'engineering_meaning':'Terminal diagnostic after typed SP16→SP554 classification. Pointwise mechanics and normal-stress diagnostics are preserved, but the fire result is not completed while an active Qy/T action lacks a qualified SP554 fire route.',
 'limitations':'Qy and torsion T remain fail-closed for the full SP554 handoff. The diagnostic normal stress from clause 8.7 may exist, but it cannot qualify the whole member when these fire checks are unresolved.',
 'normative_warning':'Fail closed. Clause 8.7 is not used to bypass unsupported shear or torsion.'
}

# Internal pointwise-stress option joins the existing clause-8.7 calculation.
adde({'id':'FIRE_BRIDGE2_E_METHOD_TO_INTERNAL_8_7','from_node_id':'SP554_D_GAMMA_T_METHOD','to_node_id':'SP554_FIRE_BRIDGE2_C_INTERNAL_8_7_STRESS','edge_type':'branch','label':'п.8.7 / qualified SP16 pointwise state','condition':cmp('strength_coefficient_method','eq','qualified_sp16_pointwise_stress'),'quantity_ids':['fire_bridge2_contract','fire_bridge2_sigma_n_static']})
adde({'id':'FIRE_BRIDGE2_E_INTERNAL_SIGMA_TO_8_7','from_node_id':'SP554_FIRE_BRIDGE2_C_INTERNAL_8_7_STRESS','to_node_id':'SP554_C_8_7','edge_type':'data','label':'qualified σn','condition':None,'quantity_ids':['sigma_n_static']})
adde({'id':'FIRE_BRIDGE2_E_INTERNAL_8_7_COMPRESSION_CONTEXT','from_node_id':'SP554_D_GAMMA_T_METHOD','to_node_id':'SP554_I_COMPRESSION_CONTEXT','edge_type':'branch','label':'qualified internal п.8.7 + compression → γe context','condition':allof(cmp('strength_coefficient_method','eq','qualified_sp16_pointwise_stress'),cmp('stress_state','in',['central_compression','compression_plus_bending'])),'quantity_ids':['fire_bridge2_contract']})

# Update legacy notes which still claimed the later bridge did not exist.
for nid in ['SP16_C_FIRE_AXIS_SHEAR_RECOVERY','SP16_C_FIRE_FREE_TORSION_RECOVERY','SP16_C_FIRE_TORSION_ZERO','SP16_C_FIRE_BIMOMENT_POINTWISE_RECOVERY']:
    n=ns[nid]
    text=n['notes']['limitations']
    if text:
        text=text.replace('until FIRE-BRIDGE2/FIRE-MECH2','and is classified by FIRE-BRIDGE2')
        text=text.replace('until FIRE-BRIDGE2','and is classified by FIRE-BRIDGE2')
        text=text.replace('still fail-closed SP16→SP554 complex-state handoff','typed FIRE-BRIDGE2 SP16→SP554 handoff')
        text=text.replace('This node does not close the SP554 complex-state handoff; nonzero Qy/T remains gated','FIRE-BRIDGE2 consumes this state; nonzero Qy/T remains fire-specific fail-closed')
        n['notes']['limitations']=text

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-70_fire_bridge2_qualified_sp16_complex_state_handoff'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.70 — FIRE-BRIDGE2 Qualified SP16 Complex-State Handoff'
g['description']='Cumulative v0.3.70 over v0.3.69: inserts a typed post-SP16-PASS fire handoff, derives a qualified internal clause-8.7 normal-stress route from the complete pointwise FIRE state, preserves explicit Sections 9-11 routes, and keeps nonzero Qy/T fail-closed instead of treating clause 8.7 as a universal bypass.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1',
 'parent_graph_id':parent,
 'fire_bridge2_qualified_sp16_state_contract_closed':True,
 'fire_bridge2_sp16_mechanical_pass_required':True,
 'fire_bridge2_internal_8_7_pointwise_normal_stress_route_closed':True,
 'fire_bridge2_explicit_sections_9_11_handoff_preserved':True,
 'fire_bridge2_bimoment_normal_stress_handoff_closed':True,
 'fire_bridge2_qy_full_fire_handoff_closed':False,
 'fire_bridge2_t_full_fire_handoff_closed':False,
 'fire_bridge2_clause_8_7_universal_shear_torsion_bypass_forbidden':True,
 'fire_bridge2_engineering_use_ready':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
