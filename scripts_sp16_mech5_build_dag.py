from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.64_sp16_mech4_free_torsion_pointwise_recovery.json'
OUT=ROOT/'normative_graph/dag_v0.3.65_sp16_mech5_direct_bimoment_pointwise_recovery.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

def qdef(qid,name,role='intermediate',dtype='object'):
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

for q in [
    qdef('ambient_direct_bimoment_state','Ambient: direct-B warping mechanics state'),
    qdef('ambient_bimoment_runtime_closed','Ambient: direct-B warping recovery runtime closed',role='diagnostic',dtype='boolean'),
    qdef('ambient_complete_pointwise_stress_state','Ambient: complete same-point N/M/Q/T/B mechanics state'),
    qdef('fire_direct_bimoment_state','Fire: direct-B warping mechanics state at 20°C basis'),
    qdef('fire_bimoment_mechanics_runtime_closed','Fire: direct-B warping recovery runtime closed before SP554 handoff',role='diagnostic',dtype='boolean'),
    qdef('fire_complete_pointwise_stress_state','Fire: complete same-point N/M/Q/T/B mechanics state at 20°C basis'),
]: addq(q)

ambient_inputs=['ambient_B_bimoment','ambient_combined_pointwise_stress_state','section_geometry_2d_normalized']
fire_inputs=['B_bimoment','fire_combined_pointwise_stress_state','section_geometry_2d_normalized']

addn({
 'id':'SP16_C_AMBIENT_BIMOMENT_POINTWISE_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH5 — direct B → σω same-point recovery (ambient)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'formula','section':'8.2.1, формула (43)','quote_or_note':'Combined normal stress includes the signed term B·ω/Iω,n.'},
   {'standard_id':'SP16_2017','reference_kind':'formula','section':'9.1.1, формула (106)','quote_or_note':'Point combined-stress expression includes N/A + Mx·y/Ix + My·x/Iy + B·ω/Iω,n.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ambient_inputs],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['ambient_direct_bimoment_state','ambient_bimoment_runtime_closed','ambient_complete_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech5_direct_bimoment_pointwise_v1','bindings':[{'variable':x,'quantity_id':x} for x in ambient_inputs],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Adds direct signed B warping normal stress to the same material points already carrying N/Mx/My/Qx/Qy/T mechanics.','limitations':'B=0 is universally closed. Nonzero-B sectorial recovery is qualified in v0.62 only for doubly symmetric I-sections; channel/tee/RHS/arbitrary geometry remain fail-closed. No B-from-T solver.','normative_warning':'Direct B and free-torsion T are independent inputs in this project scope.'}
})
addn({
 'id':'SP16_C_FIRE_BIMOMENT_POINTWISE_RECOVERY','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH5 — direct B → σω same-point recovery (fire load case, 20°C mechanics basis)',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'formula','section':'8.2.1, формула (43)'},
   {'standard_id':'SP16_2017','reference_kind':'formula','section':'9.1.1, формула (106)'},
   {'standard_id':'SP554_2026','reference_kind':'derived_graph_logic','quote_or_note':'Normal-temperature mechanical characterization remains upstream of the typed fire handoff.'},
 ],
 'consumes':[{'quantity_id':x,'required':True,'binding_role':'input'} for x in fire_inputs],
 'produces':[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['fire_direct_bimoment_state','fire_bimoment_mechanics_runtime_closed','fire_complete_pointwise_stress_state']],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech5_fire_direct_bimoment_pointwise_v1','bindings':[{'variable':x,'quantity_id':x} for x in fire_inputs],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Prepares the complete same-point N/M/Q/T/B mechanics state for the fire load case on a 20°C SP16 basis.','limitations':'This node does not close the SP554 complex-state handoff; nonzero Qy/T remains gated until FIRE-BRIDGE2. Nonzero B is currently pointwise-qualified only for doubly symmetric I-sections.','normative_warning':'This is a mechanical characterization node, not a fire-resistance PASS criterion.'}
})

# Census now uses MECH5 runtime and complete state.
census=ns['SP16_C_AMBIENT_APPLICABILITY_CENSUS']
for qid in ['ambient_bimoment_runtime_closed','ambient_complete_pointwise_stress_state']:
    if not any(x['quantity_id']==qid for x in census['consumes']):
        census['consumes'].append({'quantity_id':qid,'required':True,'binding_role':'input'})
    if not any(x.get('variable')==qid for x in census['calculation_spec']['bindings']):
        census['calculation_spec']['bindings'].append({'variable':qid,'quantity_id':qid})
census['notes']['engineering_meaning']='Enumerates action-driven SP16 families after MECH3 Qx/Qy, MECH4 free torsion T, and MECH5 direct-B same-point warping-stress recovery.'
census['notes']['limitations']='Census only, not final SP16_MECHANICAL_PASS. Nonzero-B pointwise recovery is currently qualified only for doubly symmetric I-sections.'

# Re-route both ambient MECH4 outcomes through MECH5 before census.
for eid in ['MECH4_E_AMBIENT_ZERO_TORSION_TO_CENSUS','MECH4_E_AMBIENT_TORSION_TO_CENSUS']:
    if eid not in es: raise RuntimeError(f'missing {eid}')
    es[eid]['to_node_id']='SP16_C_AMBIENT_BIMOMENT_POINTWISE_RECOVERY'
    es[eid]['label']='N/M/Q/T state → direct-B pointwise recovery'
    es[eid]['quantity_ids']=list(dict.fromkeys(es[eid].get('quantity_ids',[])+['ambient_B_bimoment','ambient_combined_pointwise_stress_state']))
adde({'id':'MECH5_E_AMBIENT_BIMOMENT_TO_CENSUS','from_node_id':'SP16_C_AMBIENT_BIMOMENT_POINTWISE_RECOVERY','to_node_id':'SP16_C_AMBIENT_APPLICABILITY_CENSUS','edge_type':'control','label':'complete N/M/Q/T/B mechanics state → applicability census','condition':None,'quantity_ids':['ambient_bimoment_runtime_closed','ambient_complete_pointwise_stress_state']})

# Re-route fire MECH4 outcomes through MECH5 before legacy SP554 stress-state planner.
for eid in ['MECH4_E_FIRE_ZERO_TORSION_TO_STATE','MECH4_E_FIRE_TORSION_TO_STATE']:
    if eid not in es: raise RuntimeError(f'missing {eid}')
    es[eid]['to_node_id']='SP16_C_FIRE_BIMOMENT_POINTWISE_RECOVERY'
    es[eid]['label']='fire N/M/Q/T state → direct-B pointwise recovery'
    es[eid]['quantity_ids']=list(dict.fromkeys(es[eid].get('quantity_ids',[])+['B_bimoment','fire_combined_pointwise_stress_state']))
adde({'id':'MECH5_E_FIRE_BIMOMENT_TO_STATE','from_node_id':'SP16_C_FIRE_BIMOMENT_POINTWISE_RECOVERY','to_node_id':'SP554_D_STRESS_STATE','edge_type':'control','label':'complete fire N/M/Q/T/B mechanics state ready; legacy SP554 gate retained','condition':None,'quantity_ids':['fire_bimoment_mechanics_runtime_closed','fire_complete_pointwise_stress_state']})

# Legacy Qy/T SP554 gate must remain intact.
for eid in ['E0087','E0214']:
    text=json.dumps(es[eid].get('condition'),ensure_ascii=False)
    if 'T_torsion' not in text or 'Q_y' not in text:
        raise RuntimeError(f'{eid} lost legacy Qy/T handoff gate')

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-65_sp16_mech5_direct_bimoment_pointwise_recovery'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.65 — SP16-MECH5 Direct Bimoment + Complete Pointwise Recovery'
g['description']='Cumulative v0.3.65 over v0.3.64: project-approved direct signed B is recovered as B*omega/Iomega on the same N/M/Q/T material points for qualified doubly symmetric I-sections; B=0 is universally complete. No restrained-torsion/B-from-T solver is introduced. Full SP16 aggregate PASS and SP554 Qy/T complex-state handoff remain deferred.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.62_sp16_mech5_direct_bimoment_pointwise_recovery_r1',
 'parent_graph_id':parent,
 'sp16_mech5_direct_bimoment_input_policy_preserved':True,
 'sp16_mech5_bimoment_from_t_solver_closed':False,
 'sp16_mech5_i_section_sectorial_pointwise_recovery_closed':True,
 'sp16_mech5_all_section_bimoment_geometry_closed':False,
 'sp16_mech5_complete_nmqtb_pointwise_state_closed_for_supported_geometry':True,
 'sp16_mech5_full_ambient_gate_closed':False,
 'sp16_mech5_sp554_complex_state_handoff_closed':False,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
