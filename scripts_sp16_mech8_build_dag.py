from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.67_sp16_mech7_primary_ambient_binding.json'
OUT=ROOT/'normative_graph/dag_v0.3.68_sp16_mech8_mq_torsion_scope.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

def qdef(qid,name,role='result',dtype='object',enum_values=None,source='CALCULATED',unit=None):
    q={'id':qid,'symbol':None,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':None,'canonical_unit':unit,'allowed_units':[] if unit is None else [unit],
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

for q in [
    qdef('sp16_mech8_eq44_no_transverse_local_stress','SP16-MECH8 — поперечное/местное нормальное напряжение σy в стенке отсутствует',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech8_annex_e1_section_type','SP16-MECH8 — тип сечения по таблице Е.1',role='input',dtype='enum',enum_values=['1','2','3','4','5a','5b','6','7','8a','8b','9a','9b'],source='USER_INPUT'),
    qdef('sp16_mech8_equivalent_load_safety_factor','SP16-MECH8 — эквивалентный коэффициент надежности по нагрузке γf для примечания 2 таблицы Е.1',role='input',dtype='number',source='USER_INPUT',unit='1'),
    qdef('sp16_mech8_required_clause_checks_confirmed','SP16-MECH8 — выполнены требования 8.4.6, 8.5.8, 8.5.9 и 8.5.18',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech8_is_support_section','SP16-MECH8 — рассматриваемое сечение является опорным',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech8_primary_evidence','SP16-MECH8 — cumulative ambient evidence после M+Q/T scope reconciliation'),
    qdef('sp16_mech8_mq_binding_complete','SP16-MECH8 — применимый M+Q route нормативно разрешен',dtype='boolean'),
    qdef('sp16_mech8_torsion_scope_reconciled','SP16-MECH8 — нормативная область T явно классифицирована',dtype='boolean'),
]: addq(q)

addn({
 'id':'SP16_D_MECH8_EQ44_LOCAL_STRESS','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH8 — локальное поперечное напряжение для M+Q класса 1',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'equation','section':'8.2.1','quote_or_note':'Equation (44) uses signed sigma_x and sigma_y plus tau_xy at the same web point; sigma_y includes local stress from Eq.(47).'}],
 'consumes':[{'quantity_id':'sp16_mech7_primary_evidence','required':True,'binding_role':'evidence'}],
 'produces':[{'quantity_id':'sp16_mech8_eq44_no_transverse_local_stress','required':True,'binding_role':'output'}],
 'applicability':None,
 'question':'Для проверки M+Q по формуле (44) поперечное/местное нормальное напряжение σy в стенке отсутствует?',
 'decision_quantity_id':'sp16_mech8_eq44_no_transverse_local_stress',
 'options':[{'value':True,'label':'Да, σy = 0','description':'MECH8 выполнит same-point Eq.(44) для поддерживаемого Mx+Qx I-beam route.'},{'value':False,'label':'Нет, σy присутствует','description':'Требуется отдельное pointwise восстановление σy/σloc; gate останется fail-closed.'}],
 'notes':{'engineering_meaning':'Explicitly resolves the sigma_y term of SP16 Eq.(44) rather than silently setting it to zero.','limitations':'Current qualified Eq.(44) binder is one-plane Mx+Qx on the parametric I-section.','normative_warning':'If sigma_y is present, it must be evaluated at the same point as sigma_x and tau_xy.'}
})
addn({
 'id':'SP16_I_MECH8_PLASTIC_MQ_CONTEXT','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH8 — контекст M+Q по 8.2.3 для сечения 2-го класса',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'clause','section':'8.2.3','quote_or_note':'Class-2/3 I/box route requires the referenced 8.4.6, 8.5.8, 8.5.9, 8.5.18 checks and excludes support sections from Eqs.(50)-(53).'},
   {'standard_id':'SP16_2017','reference_kind':'table','section':'Annex E Table E.1','quote_or_note':'Section diagram row is an explicit engineering classification; it is not inferred.'},
 ],
 'consumes':[{'quantity_id':'sp16_mech7_primary_evidence','required':True,'binding_role':'evidence'}],
 'produces':[
   {'quantity_id':'sp16_mech8_annex_e1_section_type','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech8_equivalent_load_safety_factor','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech8_required_clause_checks_confirmed','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech8_is_support_section','required':True,'binding_role':'output'},
 ],
 'applicability':None,
 'input_specs':{
   'sp16_mech8_annex_e1_section_type':{'label':'Тип/схема сечения по таблице Е.1','widget':'select'},
   'sp16_mech8_equivalent_load_safety_factor':{'label':'Эквивалентный γf для примечания 2 таблицы Е.1','widget':'number','min_exclusive':0.0},
   'sp16_mech8_required_clause_checks_confirmed':{'label':'Требования 8.4.6, 8.5.8, 8.5.9 и 8.5.18 выполнены','widget':'boolean'},
   'sp16_mech8_is_support_section':{'label':'Это опорное сечение','widget':'boolean'},
 },
 'notes':{'engineering_meaning':'Supplies only the applicability/table classifications that cannot be inferred from section forces.','limitations':'Class 3 redistribution and support-section Eqs.(54)-(55) are not closed by this stage.','normative_warning':'A false referenced-check confirmation keeps the route fail-closed.'}
})

binder_inputs=[
 'sp16_mech7_primary_evidence','sp16_applicability_census','sp16_section_class',
 'ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment',
 'section_geometry_2d_normalized','ambient_axis_shear_state','ambient_complete_pointwise_stress_state','ambient_torsion_runtime_closed',
 'I_xn','W_xn_min','W_yn_min','W_omega_eff','Ry_formula','Rs_formula','fy_norm','gamma_c_bending_strength',
 'sp16_mech8_eq44_no_transverse_local_stress','sp16_mech8_annex_e1_section_type','sp16_mech8_equivalent_load_safety_factor','sp16_mech8_required_clause_checks_confirmed','sp16_mech8_is_support_section',
]
binder_inputs=[x for x in binder_inputs if x in qs]
addn({
 'id':'SP16_C_MECH8_INTERACTION_BINDER','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH8 — M+Q normative interaction binding and T scope reconciliation',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'equation','section':'8.2.1','quote_or_note':'Eq.(44) class-1 same-point web M+Q interaction.'},
   {'standard_id':'SP16_2017','reference_kind':'equations','section':'8.2.3','quote_or_note':'Eqs.(50)-(53), beta Eq.(52), Table E.1 and Table 10a where applicable.'},
   {'standard_id':'SP16_2017','reference_kind':'annex','section':'Appendix A','quote_or_note':'It, Iomega and B are defined; no universal arbitrary-T member resistance equation is inferred by MECH8.'},
 ],
 'consumes':[{'quantity_id':x,'required':x in {'sp16_mech7_primary_evidence','sp16_applicability_census','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment'},'binding_role':'input'} for x in binder_inputs],
 'produces':[
   {'quantity_id':'sp16_mech8_primary_evidence','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech8_mq_binding_complete','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech8_torsion_scope_reconciled','required':True,'binding_role':'output'},
 ],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech8_interaction_evidence_v1','bindings':[{'variable':x,'quantity_id':x} for x in binder_inputs],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Overlays explicit M+Q normative evidence on MECH7 and records the audited limit of generic free-torsion resistance in current SP16.','limitations':'Class-1 closure is one-plane Eq.(44); class-2 closure uses explicit 8.2.3 routes. Class 3 and universal arbitrary T remain fail-closed.','normative_warning':'Pointwise T mechanics is never re-labelled as normative PASS.'}
})

# Replace the direct MECH7 binder -> MECH6 gate jump with a MECH8 layer.
old=es['MECH7_E_BINDER_TO_GATE']
g['edges'].remove(old); del es['MECH7_E_BINDER_TO_GATE']

has_bend=anyof(cmp('ambient_M_x','neq',0.0),cmp('ambient_M_y','neq',0.0))
has_shear=anyof(cmp('ambient_Q_x','neq',0.0),cmp('ambient_Q_y','neq',0.0))
no_bend=allof(cmp('ambient_M_x','eq',0.0),cmp('ambient_M_y','eq',0.0))
no_shear=allof(cmp('ambient_Q_x','eq',0.0),cmp('ambient_Q_y','eq',0.0))
mq=allof(has_bend,has_shear)

adde({'id':'MECH8_E_BINDER_TO_EQ44','from_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','to_node_id':'SP16_D_MECH8_EQ44_LOCAL_STRESS','edge_type':'branch','label':'class 1 M+Q','condition':allof(mq,cmp('sp16_section_class','eq','1')),'quantity_ids':['sp16_mech7_primary_evidence','sp16_section_class','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y']})
adde({'id':'MECH8_E_BINDER_TO_PLASTIC','from_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','to_node_id':'SP16_I_MECH8_PLASTIC_MQ_CONTEXT','edge_type':'branch','label':'class 2 M+Q','condition':allof(mq,cmp('sp16_section_class','eq','2')),'quantity_ids':['sp16_mech7_primary_evidence','sp16_section_class','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y']})
adde({'id':'MECH8_E_BINDER_TO_CALC_OTHER','from_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','to_node_id':'SP16_C_MECH8_INTERACTION_BINDER','edge_type':'branch','label':'no M+Q or unsupported class → explicit scope result','condition':anyof(no_bend,no_shear,cmp('sp16_section_class','in',['3','other'])),'quantity_ids':['sp16_mech7_primary_evidence','sp16_section_class','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y']})
adde({'id':'MECH8_E_EQ44_TO_CALC','from_node_id':'SP16_D_MECH8_EQ44_LOCAL_STRESS','to_node_id':'SP16_C_MECH8_INTERACTION_BINDER','edge_type':'control','label':'Eq.(44) sigma_y context classified','condition':None,'quantity_ids':['sp16_mech8_eq44_no_transverse_local_stress']})
adde({'id':'MECH8_E_PLASTIC_TO_CALC','from_node_id':'SP16_I_MECH8_PLASTIC_MQ_CONTEXT','to_node_id':'SP16_C_MECH8_INTERACTION_BINDER','edge_type':'control','label':'8.2.3 context classified','condition':None,'quantity_ids':['sp16_mech8_annex_e1_section_type','sp16_mech8_equivalent_load_safety_factor','sp16_mech8_required_clause_checks_confirmed','sp16_mech8_is_support_section']})
adde({'id':'MECH8_E_CALC_TO_GATE','from_node_id':'SP16_C_MECH8_INTERACTION_BINDER','to_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','edge_type':'control','label':'MECH8 evidence materialized','condition':None,'quantity_ids':['sp16_mech8_primary_evidence']})

agg=ns['SP16_C_AMBIENT_MECHANICAL_AGGREGATOR']
# MECH8 replaces MECH7 as the required cumulative primary evidence input.
for row in agg['consumes']:
    if row.get('quantity_id')=='sp16_mech7_primary_evidence': row['required']=False
if not any(x.get('quantity_id')=='sp16_mech8_primary_evidence' for x in agg['consumes']):
    agg['consumes'].append({'quantity_id':'sp16_mech8_primary_evidence','required':True,'binding_role':'evidence'})
    agg['calculation_spec']['bindings'].append({'variable':'sp16_mech8_primary_evidence','quantity_id':'sp16_mech8_primary_evidence'})
agg['notes']['limitations']='MECH8 closes supported M+Q routes while preserving a strict fail-closed boundary for class-3 interaction, unresolved local stress and universal arbitrary free-torsion resistance. Required N9/N10 and remaining detailed routes stay explicit.'

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-68_sp16_mech8_mq_torsion_scope'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.68 — SP16-MECH8 M+Q Interaction + Torsion Scope Reconciliation'
g['description']='Cumulative v0.3.68 over v0.3.67: binds qualified class-1 Eq.(44) and class-2 8.2.3 M+Q routes into the strict ambient gate and explicitly reconciles the absence of a generic universal arbitrary-T resistance equation without weakening fail-closed semantics.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.65_sp16_mech8_mq_interaction_torsion_scope_r1',
 'parent_graph_id':parent,
 'sp16_mech8_mq_interaction_layer_closed':True,
 'sp16_mech8_class1_eq44_i_mx_qx_closed':True,
 'sp16_mech8_class2_823_i_box_closed_for_supported_routes':True,
 'sp16_mech8_class3_mq_closed':False,
 'sp16_mech8_torsion_scope_reconciled':True,
 'sp16_mech8_universal_torsion_normative_check_closed':False,
 'sp16_mech8_all_n3_n10_primary_flow_bindings_closed':False,
 'sp16_mech8_engineering_use_ready':False,
 'sp16_mech6_sp554_transition_requires_pass':True,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
