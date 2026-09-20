from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'normative_graph/dag_v0.3.63_sp16_mech3_axis_shear_pointwise_recovery.json'
OUT = ROOT / 'normative_graph/dag_v0.3.64_sp16_mech4_free_torsion_pointwise_recovery.json'
g = json.loads(SRC.read_text(encoding='utf-8'))
qs = {q['id']: q for q in g['quantities']}
ns = {n['id']: n for n in g['nodes']}
es = {e['id']: e for e in g['edges']}

def qdef(qid, symbol, name, dimension, unit, allowed, role='intermediate', source='CALCULATED', dtype='number'):
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

for q in [
    qdef('ambient_free_torsion_state',None,'Ambient: free-torsion T mechanics state',None,None,[],dtype='object'),
    qdef('ambient_torsion_runtime_closed',None,'Ambient: supported free-torsion T mechanics runtime closed',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('ambient_combined_pointwise_stress_state',None,'Ambient: combined same-point N/M/Q/T mechanics state',None,None,[],dtype='object'),
    qdef('fire_free_torsion_state',None,'Fire: free-torsion T mechanics state at 20°C basis',None,None,[],dtype='object'),
    qdef('fire_torsion_mechanics_runtime_closed',None,'Fire: supported free-torsion T mechanics runtime closed before SP554 handoff',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('fire_combined_pointwise_stress_state',None,'Fire: combined same-point N/M/Q/T mechanics state at 20°C basis',None,None,[],dtype='object'),
]: addq(q)

ambient_common=['ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment','ambient_axis_shear_state','A_gross','J_x','J_y','section_geometry_2d_normalized']
fire_common=['N_force','M_x','M_y','Q_x','Q_y','T_torsion','B_bimoment','fire_axis_shear_state','A_gross','J_x','J_y','section_geometry_2d_normalized']

addn({
 'id':'SP16_C_AMBIENT_TORSION_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH4 — zero free torsion T state (ambient)',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение А','quote_or_note':'It is the free-torsion section property; no free-torsion stress recovery is required when T=0.'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['ambient_T_torsion','ambient_B_bimoment','ambient_axis_shear_state']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_free_torsion_state','ambient_torsion_runtime_closed','ambient_combined_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech4_zero_torsion_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['ambient_T_torsion','ambient_B_bimoment','ambient_axis_shear_state']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Explicit zero-T producer keeps T distinct from Mx and B and forwards the MECH3 same-point N/M/Q state.','limitations':'B remains a separate direct input; warping normal stress is not recovered in SP16-MECH4.','normative_warning':'Applicable only for T=0.'}
})
addn({
 'id':'SP16_C_AMBIENT_FREE_TORSION_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH4 — free torsion T → τT same-point recovery (ambient)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение А','quote_or_note':'SP16 distinguishes It (free torsion), Iω and B.'},
   {'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение Д','quote_or_note':'For supported open sections It=(k/3)Σ(bi ti^3), with section-family k values.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ambient_common],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_free_torsion_state','ambient_torsion_runtime_closed','ambient_combined_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech4_free_torsion_recovery_v1','bindings':[{'variable':x,'quantity_id':x} for x in ambient_common],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Recovers signed Saint-Venant/free-torsion shear at the same section sampling points used by MECH3 and vectorially combines Qx/Qy/T shear components.','limitations':'Supported templates: I, tee, channel and RHS/SHS. Open-section local τT is a thin-wall Saint-Venant mechanics recovery using SP16 Annex-D It; RHS/SHS uses a labelled single-cell Bredt model. B is not derived from T and σB is not recovered. This state alone is not the final SP16 PASS criterion.','normative_warning':'T is the free-torsion component about +s. Never alias T to Mx or B.'}
})
addn({
 'id':'SP16_C_FIRE_TORSION_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH4 — zero free torsion T state (fire load case)',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение А'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['T_torsion','B_bimoment','fire_axis_shear_state']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['fire_free_torsion_state','fire_torsion_mechanics_runtime_closed','fire_combined_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech4_fire_zero_torsion_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['T_torsion','B_bimoment','fire_axis_shear_state']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Materializes a zero-T mechanics state for the FIRE_LOAD_CASE before the still fail-closed SP16→SP554 complex-state handoff.','limitations':'SP554 T handoff is not closed by this node.','normative_warning':'No fire-resistance claim is made here.'}
})
addn({
 'id':'SP16_C_FIRE_FREE_TORSION_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH4 — free torsion T → τT same-point recovery (fire load case, 20°C mechanics basis)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение А'},
   {'standard_id':'SP16_2017','reference_kind':'appendix','section':'Приложение Д'},
   {'standard_id':'SP554_2026','reference_kind':'derived_graph_logic','quote_or_note':'Normal-temperature mechanical characterization is prepared before the later typed fire handoff.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in fire_common],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['fire_free_torsion_state','fire_torsion_mechanics_runtime_closed','fire_combined_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech4_fire_free_torsion_recovery_v1','bindings':[{'variable':x,'quantity_id':x} for x in fire_common],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Prepares the signed free-torsion field and same-point N/M/Q/T mechanics state for FIRE_LOAD_CASE at the 20°C SP16 basis.','limitations':'Nonzero T remains fail-closed at the legacy SP554 handoff until FIRE-BRIDGE2; B/warping stress remains separate.','normative_warning':'This is not a SP554 fire-resistance check.'}
})

# Census consumes the resolved T-mechanics status/state in addition to MECH3 Qy status.
census=ns['SP16_C_AMBIENT_APPLICABILITY_CENSUS']
for qid in ['ambient_torsion_runtime_closed','ambient_combined_pointwise_stress_state']:
    if not any(x['quantity_id']==qid for x in census['consumes']):
        census['consumes'].append({'quantity_id':qid,'required':True,'binding_role':'input'})
    if not any(x.get('variable')==qid for x in census['calculation_spec']['bindings']):
        census['calculation_spec']['bindings'].append({'variable':qid,'quantity_id':qid})
census['notes']['engineering_meaning']='Enumerates action-driven SP16 check families after SP16-MECH3 Qx/Qy and SP16-MECH4 free-torsion mechanical recovery; context-driven families remain explicit unresolved applicability questions.'
census['notes']['limitations']='Census only, not the final SP16_MECHANICAL_PASS gate. B remains direct-input partial runtime and its warping normal stress is not recovered in MECH4.'

# Ambient: MECH3 shear state -> T=0 passthrough OR nonzero free-torsion recovery -> census.
for eid in ['MECH3_E_AMBIENT_ZERO_SHEAR_TO_CENSUS','MECH3_E_AMBIENT_SHEAR_TO_CENSUS']:
    if eid not in es: raise RuntimeError(f'missing {eid}')
    es[eid]['to_node_id']='SP16_C_AMBIENT_FREE_TORSION_RECOVERY'
    es[eid]['label']='axis shear state → nonzero free torsion recovery'
    es[eid]['condition']={'type':'comparison','quantity_id':'ambient_T_torsion','operator':'neq','value':0}
    es[eid]['quantity_ids']=list(dict.fromkeys(es[eid].get('quantity_ids',[])+['ambient_T_torsion']))
source_for_ambient={
 'MECH3_E_AMBIENT_ZERO_SHEAR_TO_CENSUS':'SP16_C_AMBIENT_AXIS_SHEAR_ZERO',
 'MECH3_E_AMBIENT_SHEAR_TO_CENSUS':'SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY',
}
for base,src in source_for_ambient.items():
    adde({'id':base.replace('_TO_CENSUS','_TO_ZERO_TORSION'),'from_node_id':src,'to_node_id':'SP16_C_AMBIENT_TORSION_ZERO','edge_type':'branch','label':'T=0','condition':{'type':'comparison','quantity_id':'ambient_T_torsion','operator':'eq','value':0},'quantity_ids':['ambient_axis_shear_state','ambient_T_torsion','ambient_B_bimoment']})
adde({'id':'MECH4_E_AMBIENT_ZERO_TORSION_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_TORSION_ZERO','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'zero-T mechanics state ready','condition':None,'quantity_ids':['ambient_torsion_runtime_closed','ambient_combined_pointwise_stress_state']})
adde({'id':'MECH4_E_AMBIENT_TORSION_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_FREE_TORSION_RECOVERY','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'free-torsion mechanics state ready','condition':None,'quantity_ids':['ambient_torsion_runtime_closed','ambient_combined_pointwise_stress_state']})

# Fire: MECH3 shear state -> T=0 passthrough OR nonzero free-torsion recovery -> legacy SP554 stress-state decision.
for eid in ['MECH3_E_FIRE_ZERO_SHEAR_TO_STATE','MECH3_E_FIRE_SHEAR_TO_STATE']:
    if eid not in es: raise RuntimeError(f'missing {eid}')
    es[eid]['to_node_id']='SP16_C_FIRE_FREE_TORSION_RECOVERY'
    es[eid]['label']='fire axis shear state → nonzero free torsion mechanics'
    es[eid]['condition']={'type':'comparison','quantity_id':'T_torsion','operator':'neq','value':0}
    es[eid]['quantity_ids']=list(dict.fromkeys(es[eid].get('quantity_ids',[])+['T_torsion']))
source_for_fire={
 'MECH3_E_FIRE_ZERO_SHEAR_TO_STATE':'SP16_C_FIRE_AXIS_SHEAR_ZERO',
 'MECH3_E_FIRE_SHEAR_TO_STATE':'SP16_C_FIRE_AXIS_SHEAR_RECOVERY',
}
for base,src in source_for_fire.items():
    adde({'id':base.replace('_TO_STATE','_TO_ZERO_TORSION'),'from_node_id':src,'to_node_id':'SP16_C_FIRE_TORSION_ZERO','edge_type':'branch','label':'T=0','condition':{'type':'comparison','quantity_id':'T_torsion','operator':'eq','value':0},'quantity_ids':['fire_axis_shear_state','T_torsion','B_bimoment']})
adde({'id':'MECH4_E_FIRE_ZERO_TORSION_TO_STATE','from_node_id':'SP16_C_FIRE_TORSION_ZERO','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'zero-T fire mechanics state ready','condition':None,'quantity_ids':['fire_torsion_mechanics_runtime_closed','fire_combined_pointwise_stress_state']})
adde({'id':'MECH4_E_FIRE_TORSION_TO_STATE','from_node_id':'SP16_C_FIRE_FREE_TORSION_RECOVERY','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'free-torsion fire mechanics state ready; SP554 handoff still gated','condition':None,'quantity_ids':['fire_torsion_mechanics_runtime_closed','fire_combined_pointwise_stress_state']})

# Legacy SP554 handoff remains fail-closed for Qy/T. Keep v0.60 gate unchanged.
for eid in ['E0087','E0214']:
    text=json.dumps(es[eid].get('condition'),ensure_ascii=False)
    if 'T_torsion' not in text or 'Q_y' not in text:
        raise RuntimeError(f'{eid} lost legacy Qy/T handoff gate')

# Update UI/diagnostic wording: T mechanics is supported for current templates, but SP554 handoff and full SP16 gate remain open.
ns['SP16_I_AMBIENT_LOADS']['notes']['limitations']='Qx/Qy and free-torsion T mechanics are resolved by SP16-MECH3/4 where section geometry is supported. B remains direct conditional input; full SP16 aggregate gate follows in SP16-MECH6.'
ns['SP16_R_AMBIENT_UNSUPPORTED_ACTIONS']['notes']['engineering_meaning']='Stops before SP554 when an active ambient SP16 mechanics branch remains unresolved (e.g. unsupported Qy/T section geometry or another deferred mechanics family).'
if 'UI16_E_PLAN_TO_DEFERRED_RESULT' in es:
    es['UI16_E_PLAN_TO_DEFERRED_RESULT']['label']='Qy/T mechanics may be characterized, but legacy SP554 handoff remains deferred until FIRE-BRIDGE2'

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-64_sp16_mech4_free_torsion_pointwise_recovery'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.64 — SP16-MECH4 Free Torsion T + Pointwise Recovery'
g['description']='Cumulative v0.3.64 over v0.3.63: signed T is resolved as a distinct Saint-Venant/free-torsion mechanics component for supported section templates, merged point-by-point with N/Mx/My/Qx/Qy stresses, while B remains an independent conditional direct input. Full SP16 aggregate PASS and SP554 T/Qy handoff remain deferred.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.61_sp16_mech4_free_torsion_pointwise_recovery_r1',
 'parent_graph_id':parent,
 'sp16_mech4_free_torsion_supported_templates_closed':True,
 'sp16_mech4_t_distinct_from_mx_and_b':True,
 'sp16_mech4_pointwise_nmqt_mechanics_state_closed':True,
 'sp16_mech4_direct_b_policy_preserved':True,
 'sp16_mech4_restrained_torsion_solver_closed':False,
 'sp16_mech4_full_ambient_gate_closed':False,
 'sp16_mech4_sp554_t_handoff_closed':False,
 'sp16_mech4_sp554_qy_handoff_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
