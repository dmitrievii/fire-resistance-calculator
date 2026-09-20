from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'normative_graph/dag_v0.3.62_sp16_mech2_load_cases_applicability_census.json'
OUT = ROOT / 'normative_graph/dag_v0.3.63_sp16_mech3_axis_shear_pointwise_recovery.json'
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
    qdef('ambient_axis_shear_state',None,'Ambient: axis-specific Qx/Qy shear state',None,None,[],dtype='object'),
    qdef('ambient_qy_runtime_closed',None,'Ambient: Qy mechanics runtime closed',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('ambient_shear_local_pass',None,'Ambient: локальные shear-component checks PASS',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('ambient_shear_governing_utilization','η_Q','Ambient: governing shear utilization','dimensionless','1',['1'],role='diagnostic'),
    qdef('fire_axis_shear_state',None,'Fire: axis-specific Qx/Qy shear state',None,None,[],dtype='object'),
    qdef('fire_qy_mechanics_runtime_closed',None,'Fire: Qy mechanics runtime closed before SP554 handoff',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('fire_shear_local_pass',None,'Fire: локальные shear-component checks PASS at 20°C mechanics basis',None,None,[],role='diagnostic',dtype='boolean'),
    qdef('fire_shear_governing_utilization','η_Q,fire','Fire: governing shear utilization at 20°C mechanics basis','dimensionless','1',['1'],role='diagnostic'),
]: addq(q)

common_geom=['A_gross','J_x','J_y','section_geometry_2d_normalized','Rs_formula','gamma_c_bending_strength','sp16_shear_hole_alpha45']
# Stage N1 already defines material_safety_category and Table 3 gamma_m, but
# the guided DAG historically had no interactive producer for that quantity.
# SP16-MECH3 makes the dependency reachable when a real shear check needs Rs.
addn({
 'id':'SP16_I_MATERIAL_SAFETY_CATEGORY','node_type':'input','owner_standard_id':'SP16_2017','title':'СП16 Таблица 3 — условия контроля свойств проката',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'table','section':'6','clause':'6.1','table_ref':'3'}],
 'consumes':[],
 'produces':[{'quantity_id':'material_safety_category','required':True,'binding_role':'output'}],
 'applicability':None,
 'input_contract':{'fields':[{'quantity_id':'material_safety_category','required':True}]},
 'notes':{'engineering_meaning':'Explicit selector required to obtain gamma_m and hence Rs; no hidden Table 3 default is permitted.','limitations':None,'normative_warning':'Select the actual material-control category.'}
})
addn({
 'id':'SP16_C_AMBIENT_AXIS_SHEAR_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH3 — zero Qx/Qy state (ambient)',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','section':'8','quote_or_note':'No shear recovery is required when Qx=Qy=0.'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['ambient_Q_x','ambient_Q_y']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_axis_shear_state','ambient_qy_runtime_closed','ambient_shear_local_pass','ambient_shear_governing_utilization']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech3_zero_axis_shear_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['ambient_Q_x','ambient_Q_y']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Material-independent zero-shear state avoids requesting unrelated shear dependencies when both transverse actions are zero.','limitations':None,'normative_warning':'Applicable only for Qx=Qy=0.'}
})
addn({
 'id':'SP16_C_FIRE_AXIS_SHEAR_ZERO','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH3 — zero Qx/Qy state (fire load case)',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'derived_graph_logic','section':'8','quote_or_note':'No shear recovery is required when Qx=Qy=0.'}],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['Q_x','Q_y']],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['fire_axis_shear_state','fire_qy_mechanics_runtime_closed','fire_shear_local_pass','fire_shear_governing_utilization']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech3_zero_axis_shear_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['Q_x','Q_y']],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Material-independent zero-shear state for FIRE_LOAD_CASE.','limitations':None,'normative_warning':'Applicable only for Qx=Qy=0.'}
})
addn({
 'id':'SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH3 — Qx/Qy axis-specific shear recovery (ambient)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'clause','section':'8','clause':'8.2.1','quote_or_note':'Axis-specific elastic shear mechanics use Q*S/(I*t) at the checked section point.'},
   {'standard_id':'SP16_2017','reference_kind':'clause','section':'8','clause':'8.2.3','quote_or_note':'For I/box sections the clause explicitly uses tau_x=Qx/Aw and, for biaxial bending, tau_y=Qy/(2Af).'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_B_bimoment',*common_geom]],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_axis_shear_state','ambient_qy_runtime_closed','ambient_shear_local_pass','ambient_shear_governing_utilization']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech3_axis_shear_recovery_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_B_bimoment',*common_geom]],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Keeps Qx and Qy separate, recovers both stress components at the same section points, and materializes explicit SP16 8.2.3 component checks where applicable.','limitations':'No torsion T contribution. Pointwise catalog-profile fields based on nominal sharp dimensions are mechanics provenance only; the explicit 8.2.3 I/box component check remains the normative closure for such catalog sections.','normative_warning':'Never forms sqrt(Qx^2+Qy^2) as a substitute transverse force.'}
})
addn({
 'id':'SP16_C_FIRE_AXIS_SHEAR_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017','title':'SP16-MECH3 — Qx/Qy axis-specific shear recovery (fire load case, 20°C mechanics basis)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'clause','section':'8','clause':'8.2.3'},
   {'standard_id':'SP554_2026','reference_kind':'derived_graph_logic','quote_or_note':'Mechanical action characterization is prepared before the later typed SP16→SP554 fire handoff.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['N_force','M_x','M_y','Q_x','Q_y','B_bimoment',*common_geom]],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['fire_axis_shear_state','fire_qy_mechanics_runtime_closed','fire_shear_local_pass','fire_shear_governing_utilization']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech3_fire_axis_shear_recovery_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['N_force','M_x','M_y','Q_x','Q_y','B_bimoment',*common_geom]],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Prepares the same Qx/Qy mechanical stress state for the FIRE_LOAD_CASE without yet changing SP554 routing.','limitations':'Qy remains fail-closed at the legacy SP554 handoff until FIRE-BRIDGE2/FIRE-MECH2.','normative_warning':'This node is normal-temperature mechanical characterization of the fire action state, not a fire resistance check.'}
})

# Census now consumes the resolved Qy mechanics status.
census=ns['SP16_C_AMBIENT_APPLICABILITY_CENSUS']
if not any(x['quantity_id']=='ambient_qy_runtime_closed' for x in census['consumes']):
    census['consumes'].append({'quantity_id':'ambient_qy_runtime_closed','required':True,'binding_role':'input'})
    census['consumes'].append({'quantity_id':'ambient_axis_shear_state','required':True,'binding_role':'input'})
census['calculation_spec']['bindings'].append({'variable':'ambient_qy_runtime_closed','quantity_id':'ambient_qy_runtime_closed'})
census['calculation_spec']['bindings'].append({'variable':'ambient_axis_shear_state','quantity_id':'ambient_axis_shear_state'})
census['notes']['engineering_meaning']='Enumerates action-driven SP16 check families after SP16-MECH3 Qx/Qy component recovery; context-driven families remain explicit unresolved applicability questions.'
census['notes']['limitations']='This is still a census, not the full SP16_MECHANICAL_PASS gate. T remains deferred to SP16-MECH4.'

# Ambient B branches select a material-independent zero state when Qx=Qy=0;
# otherwise the full axis-specific recovery is executed.
nonzero_ambient_q={'type':'any_of','conditions':[
    {'type':'comparison','quantity_id':'ambient_Q_x','operator':'neq','value':0},
    {'type':'comparison','quantity_id':'ambient_Q_y','operator':'neq','value':0},
]}
zero_ambient_q={'type':'all_of','conditions':[
    {'type':'comparison','quantity_id':'ambient_Q_x','operator':'eq','value':0},
    {'type':'comparison','quantity_id':'ambient_Q_y','operator':'eq','value':0},
]}
for eid in ['MECH2_E_AMBIENT_B_INPUT_TO_CENSUS','MECH2_E_AMBIENT_B_ZERO_TO_CENSUS']:
    es[eid]['to_node_id']='SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY'
    es[eid]['label']='ambient B ready → Qx/Qy recovery'
    es[eid]['condition']=nonzero_ambient_q
adde({'id':'MECH3_E_AMBIENT_B_INPUT_TO_ZERO_SHEAR','from_node_id':'SP16_I_AMBIENT_BIMOMENT_DIRECT','to_node_id':'SP16_C_AMBIENT_AXIS_SHEAR_ZERO','edge_type':'branch','label':'Qx=Qy=0','condition':zero_ambient_q,'quantity_ids':['ambient_B_bimoment']})
adde({'id':'MECH3_E_AMBIENT_B_ZERO_TO_ZERO_SHEAR','from_node_id':'SP16_C_AMBIENT_BIMOMENT_ZERO','to_node_id':'SP16_C_AMBIENT_AXIS_SHEAR_ZERO','edge_type':'branch','label':'Qx=Qy=0','condition':zero_ambient_q,'quantity_ids':['ambient_B_bimoment']})
adde({'id':'MECH3_E_AMBIENT_ZERO_SHEAR_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_AXIS_SHEAR_ZERO','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'zero Qx/Qy state','condition':None,'quantity_ids':['ambient_axis_shear_state','ambient_qy_runtime_closed']})
adde({'id':'MECH3_E_AMBIENT_SHEAR_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'axis-specific Qx/Qy state','condition':None,'quantity_ids':['ambient_axis_shear_state','ambient_qy_runtime_closed']})

# Fire-load-case sources likewise bypass material-dependent shear recovery when
# Qx=Qy=0, while nonzero transverse actions receive the full mechanics state.
nonzero_fire_q={'type':'any_of','conditions':[
    {'type':'comparison','quantity_id':'Q_x','operator':'neq','value':0},
    {'type':'comparison','quantity_id':'Q_y','operator':'neq','value':0},
]}
zero_fire_q={'type':'all_of','conditions':[
    {'type':'comparison','quantity_id':'Q_x','operator':'eq','value':0},
    {'type':'comparison','quantity_id':'Q_y','operator':'eq','value':0},
]}
for eid in ['MECH2_E_FIRE_INHERIT_TO_STATE','MECH2_E_FIRE_FINALIZE_TO_STATE']:
    es[eid]['to_node_id']='SP16_C_FIRE_AXIS_SHEAR_RECOVERY'
    es[eid]['label']='FIRE_LOAD_CASE → Qx/Qy mechanics'
    es[eid]['condition']=nonzero_fire_q
adde({'id':'MECH3_E_FIRE_INHERIT_TO_ZERO_SHEAR','from_node_id':'SP16_C_FIRE_LOADS_INHERIT_AMBIENT','to_node_id':'SP16_C_FIRE_AXIS_SHEAR_ZERO','edge_type':'branch','label':'Qx=Qy=0','condition':zero_fire_q,'quantity_ids':['N_force','M_x','M_y','Q_x','Q_y','T_torsion']})
adde({'id':'MECH3_E_FIRE_FINALIZE_TO_ZERO_SHEAR','from_node_id':'SP16_C_FIRE_LOAD_CASE_FINALIZE','to_node_id':'SP16_C_FIRE_AXIS_SHEAR_ZERO','edge_type':'branch','label':'Qx=Qy=0','condition':zero_fire_q,'quantity_ids':['N_force','M_x','M_y','Q_x','Q_y','T_torsion']})
adde({'id':'MECH3_E_FIRE_ZERO_SHEAR_TO_STATE','from_node_id':'SP16_C_FIRE_AXIS_SHEAR_ZERO','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'zero fire Qx/Qy state ready','condition':None,'quantity_ids':['fire_axis_shear_state','fire_qy_mechanics_runtime_closed']})
adde({'id':'MECH3_E_FIRE_SHEAR_TO_STATE','from_node_id':'SP16_C_FIRE_AXIS_SHEAR_RECOVERY','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'fire mechanical shear state ready','condition':None,'quantity_ids':['fire_axis_shear_state','fire_qy_mechanics_runtime_closed']})

# Legacy SP554 routing must remain strictly fail-closed for Qy/T until the
# later typed SP16->SP554 bridge.  In v0.59 the unconditional main control edge
# could run in parallel with the deferred-result branch; gate it explicitly.
no_qy_t={'type':'all_of','conditions':[
    {'type':'comparison','quantity_id':'Q_y','operator':'eq','value':0},
    {'type':'comparison','quantity_id':'T_torsion','operator':'eq','value':0},
]}
es['E0087']['condition']=no_qy_t
old_tension=es['E0214']['condition']
es['E0214']['condition']={'type':'all_of','conditions':[old_tension,*no_qy_t['conditions']]}
es['UI16_E_PLAN_TO_DEFERRED_RESULT']['label']='Qy mechanics ready, but SP554 handoff deferred / T unsupported'

# Update authored notes/status without claiming the later full gate.
ns['SP16_I_AMBIENT_LOADS']['notes']['limitations']='Qx/Qy component mechanics are resolved by SP16-MECH3 where section geometry is supported; T remains fail-closed until SP16-MECH4.'
ns['SP16_R_AMBIENT_UNSUPPORTED_ACTIONS']['title']='SP16 ambient mechanics — unresolved active branch'
ns['SP16_R_AMBIENT_UNSUPPORTED_ACTIONS']['notes']['engineering_meaning']='Stops before SP554 when an active ambient SP16 branch is still unresolved (currently principally T, or Qy for unsupported section geometry).'

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-63_sp16_mech3_axis_shear_pointwise_recovery'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.63 — SP16-MECH3 Axis-Specific Qx/Qy + Pointwise Recovery'
g['description']='Cumulative v0.3.63 over v0.3.62: Qx/Qy remain separate, SP16 8.2.3 component shear checks are materialized for I/box sections, deterministic same-point shear stress recovery is added, and both ambient/fire load cases receive typed shear states. T remains deferred.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.60_sp16_mech3_axis_shear_pointwise_recovery_r1',
 'parent_graph_id':parent,
 'sp16_mech3_axis_specific_qx_qy_closed':True,
 'sp16_mech3_clause_8_2_3_qy_component_closed':True,
 'sp16_mech3_pointwise_shear_state_closed':True,
 'sp16_mech3_fire_shear_characterization_closed':True,
 'sp16_mech3_torsion_runtime_closed':False,
 'sp16_mech3_full_ambient_gate_closed':False,
 'sp16_mech3_sp554_qy_handoff_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
