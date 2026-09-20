from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.66_sp16_mech6_mechanical_pass_gate.json'
OUT=ROOT/'normative_graph/dag_v0.3.67_sp16_mech7_primary_ambient_binding.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

def qdef(qid,name,role='result',dtype='object',enum_values=None,source='CALCULATED'):
    q={'id':qid,'symbol':None,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
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

for q in [
    qdef('sp16_mech7_fatigue_required','SP16-MECH7 — требуется проверка усталости по разделу 12',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech7_brittle_required','SP16-MECH7 — требуется отдельная проверка хрупкого разрушения по разделу 13',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech7_tension_post_yield_possible','SP16-MECH7 — эксплуатация растянутого элемента возможна после достижения текучести',role='decision_state',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech7_table32_row','SP16-MECH7 — строка таблицы 32 для предельной гибкости',role='input',dtype='enum',enum_values=['1a','1b','2a','2b','3','4','5','6','7'],source='USER_INPUT'),
    qdef('sp16_mech7_group4_slenderness_increase','SP16-MECH7 — применимо увеличение предельной гибкости для группы 4',role='input',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech7_table9_group','SP16-MECH7 — группа диаграммы таблицы 9 для стенки',role='input',dtype='enum',enum_values=['group_1_i_section','group_2_box_section','group_3_channel_section','group_4_tee_section'],source='USER_INPUT'),
    qdef('sp16_mech7_table10_group','SP16-MECH7 — группа диаграммы таблицы 10 для полки',role='input',dtype='enum',enum_values=['group_1','group_2','group_3','group_4'],source='USER_INPUT'),
    qdef('sp16_mech7_flange_edge_stiffened','SP16-MECH7 — свободный край полки усилен',role='input',dtype='boolean',source='USER_INPUT'),
    qdef('sp16_mech7_primary_evidence','SP16-MECH7 — связанный пакет нормативных evidence для ambient case'),
    qdef('sp16_mech7_primary_binding_complete','SP16-MECH7 — все поддерживаемые primary bindings разрешены',dtype='boolean'),
]: addq(q)

addn({
 'id':'SP16_D_MECH7_FATIGUE_REQUIRED','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH7 — применимость усталости',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'section','section':'12','quote_or_note':'Applicability of the Section 12 fatigue route depends on cyclic actions and project context and cannot be inferred from N/M/Q/T alone.'}],
 'consumes':[{'quantity_id':'sp16_applicability_census','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_mech7_fatigue_required','required':True,'binding_role':'output'}],
 'applicability':None,
 'question':'Для данного расчетного состояния требуется проверка усталости по разделу 12 СП16?',
 'decision_quantity_id':'sp16_mech7_fatigue_required',
 'options':[{'value':False,'label':'Нет','description':'Циклическая усталостная проверка для данного расчетного состояния не применима.'},{'value':True,'label':'Да','description':'Требуется полный маршрут Stage N9; без его evidence gate останется fail-closed.'}],
 'notes':{'engineering_meaning':'Explicitly classifies the context-driven fatigue row of the ambient census.','limitations':'A yes answer does not itself constitute a fatigue PASS.','normative_warning':'If fatigue is applicable, Stage N9 evidence is mandatory.'}
})
addn({
 'id':'SP16_D_MECH7_BRITTLE_REQUIRED','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH7 — применимость раздела 13',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'section','section':'13','quote_or_note':'Section 13 applicability depends on service temperature, construction group, thickness and detail context.'}],
 'consumes':[{'quantity_id':'sp16_mech7_fatigue_required','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_mech7_brittle_required','required':True,'binding_role':'output'}],
 'applicability':None,
 'question':'Для данного расчетного состояния требуется отдельная проверка требований раздела 13 СП16?',
 'decision_quantity_id':'sp16_mech7_brittle_required',
 'options':[{'value':False,'label':'Нет','description':'Отдельный Stage N10 для данного расчетного состояния классифицирован как неприменимый.'},{'value':True,'label':'Да','description':'Требуется полный Stage N10; без его evidence gate останется fail-closed.'}],
 'notes':{'engineering_meaning':'Explicit context classification for the Section 13 row.','limitations':'Does not replace steel/product/detail requirements elsewhere in the project.','normative_warning':'A yes answer requires full N10 evidence.'}
})
addn({
 'id':'SP16_D_MECH7_TENSION_POSTYIELD','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH7 — ветвь формулы (5) для растяжения',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'clause','section':'7.1.1','quote_or_note':'Select the Eq.(5) resistance branch using the current-SP16 post-yield-service condition.'}],
 'consumes':[{'quantity_id':'ambient_N_force','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_mech7_tension_post_yield_possible','required':True,'binding_role':'output'}],
 'applicability':cmp('ambient_N_force','gt',0.0),
 'question':'Для растянутого элемента допустима эксплуатация после достижения текучести?',
 'decision_quantity_id':'sp16_mech7_tension_post_yield_possible',
 'options':[{'value':False,'label':'Нет','description':'Ветвь Eq.(5) определяется без допущения эксплуатации после текучести.'},{'value':True,'label':'Да','description':'MECH7 применит соответствующую ветвь Eq.(5) по условиям 7.1.1.'}],
 'notes':{'engineering_meaning':'Direct binding of the N3 Eq.(5) branch-selection condition into the primary ambient flow.','limitations':None,'normative_warning':'No branch is silently assumed.'}
})
addn({
 'id':'SP16_I_MECH7_COMPRESSION_SLENDERNESS','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH7 — классификация предельной гибкости сжатого элемента',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'table','section':'10.4.1','quote_or_note':'Table 32 row and the explicit group-4 increase condition are engineering classifications.'}],
 'consumes':[{'quantity_id':'ambient_N_force','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp16_mech7_table32_row','required':True,'binding_role':'output'},{'quantity_id':'sp16_mech7_group4_slenderness_increase','required':True,'binding_role':'output'},{'quantity_id':'sp16_mech7_table9_group','required':True,'binding_role':'output'},{'quantity_id':'sp16_mech7_table10_group','required':True,'binding_role':'output'},{'quantity_id':'sp16_mech7_flange_edge_stiffened','required':True,'binding_role':'output'}],
 'applicability':cmp('ambient_N_force','lt',0.0),
 'input_specs':{
   'sp16_mech7_table32_row':{'label':'Строка таблицы 32','widget':'select'},
   'sp16_mech7_group4_slenderness_increase':{'label':'Применимо увеличение для группы конструкций 4','widget':'boolean'},
   'sp16_mech7_table9_group':{'label':'Группа диаграммы Table 9 (стенка)','widget':'select'},
   'sp16_mech7_table10_group':{'label':'Группа диаграммы Table 10 (полка)','widget':'select'},
   'sp16_mech7_flange_edge_stiffened':{'label':'Свободный край полки усилен','widget':'boolean'},
 },
 'notes':{'engineering_meaning':'Provides the explicit Table 32 classification needed to bind Stage N7 limiting-slenderness evidence.','limitations':'The row is not inferred from geometry or building purpose.','normative_warning':'Select the actual normative row for the member.'}
})

binder_inputs=[
 'sp16_applicability_census','ambient_N_force','ambient_M_x','ambient_M_y','ambient_B_bimoment',
 'A_gross','A_net','I_xn','I_yn','Ry_formula','Ru_formula','fy_norm','gamma_u','E_norm','section_geometry_2d_normalized',
 'gamma_c_tension','gamma_c_compression','gamma_c_bending_strength','gamma_c_bending_stability','gamma_c_nm_strength','gamma_c_nm_stability',
 'phi_x_sp16','phi_y_sp16','phi_bending','ltb_check_required','sp16_lambda_x_geom','sp16_lambda_y_geom',
 'W_el_x_pos','W_el_x_neg','ambient_complete_pointwise_stress_state','sp16_section_class',
 'phi_e_sp16','phi_ex_sp16','phi_ey_sp16','c_sp16','sp16_m_eff_lookup','sp16_m_x','lambda_bar_x','lambda_bar_y',
 'sp16_mech7_fatigue_required','sp16_mech7_brittle_required','sp16_mech7_tension_post_yield_possible','sp16_mech7_table32_row','sp16_mech7_group4_slenderness_increase','sp16_mech7_table9_group','sp16_mech7_table10_group','sp16_mech7_flange_edge_stiffened',
 'sp16_n6_web_status','sp16_n6_flange_status','sp16_n9_release_gate','sp16_n10_release_gate',
]
binder_inputs=[x for x in binder_inputs if x in qs]
addn({
 'id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH7 — primary ambient normative evidence binding',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'section','section':'7','quote_or_note':'Axial strength and central compression stability.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'8','quote_or_note':'Elastic bending strength and LTB where qualified.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'9','quote_or_note':'N+M section/member checks where required inputs are already present.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'10','quote_or_note':'Table 32 limiting slenderness.'},
 ],
 'consumes':[{'quantity_id':x,'required':x in {'sp16_applicability_census','ambient_N_force','ambient_M_x','ambient_M_y','ambient_B_bimoment'},'binding_role':'input'} for x in binder_inputs],
 'produces':[{'quantity_id':'sp16_mech7_primary_evidence','required':True,'binding_role':'output'},{'quantity_id':'sp16_mech7_primary_binding_complete','required':True,'binding_role':'output'}],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech7_primary_ambient_evidence_v1','bindings':[{'variable':x,'quantity_id':x} for x in binder_inputs],'rounding':{'mode':'none'}},
 'notes':{
   'engineering_meaning':'Executes/binds qualified SP16 evidence already supportable from the primary ambient session instead of requiring dormant N3-N10 stage nodes to have been visited manually.',
   'limitations':'M+Q, universal torsion resistance, detailed local stability and required N9/N10 routes remain fail-closed unless dedicated evidence exists.',
   'normative_warning':'A mechanics field is never converted to PASS without an explicit qualified SP16 equation/procedure.'
 }
})

# Primary flow: census confirmation -> explicit context classifiers -> N-sign-specific
# N3/N7 inputs -> binder -> unchanged strict MECH6 aggregator.
e=es['MECH2_E_CENSUS_TO_FIRE_MODE']
e['to_node_id']='SP16_D_MECH7_FATIGUE_REQUIRED'
e['label']='ambient census resolved → MECH7 primary binding'

adde({'id':'MECH7_E_FATIGUE_TO_BRITTLE','from_node_id':'SP16_D_MECH7_FATIGUE_REQUIRED','to_node_id':'SP16_D_MECH7_BRITTLE_REQUIRED','edge_type':'control','label':'fatigue applicability classified','condition':None,'quantity_ids':['sp16_mech7_fatigue_required']})
adde({'id':'MECH7_E_BRITTLE_TO_TENSION','from_node_id':'SP16_D_MECH7_BRITTLE_REQUIRED','to_node_id':'SP16_D_MECH7_TENSION_POSTYIELD','edge_type':'branch','label':'tension N>0','condition':cmp('ambient_N_force','gt',0.0),'quantity_ids':['sp16_mech7_brittle_required','ambient_N_force']})
adde({'id':'MECH7_E_BRITTLE_TO_COMPRESSION','from_node_id':'SP16_D_MECH7_BRITTLE_REQUIRED','to_node_id':'SP16_I_MECH7_COMPRESSION_SLENDERNESS','edge_type':'branch','label':'compression N<0','condition':cmp('ambient_N_force','lt',0.0),'quantity_ids':['sp16_mech7_brittle_required','ambient_N_force']})
adde({'id':'MECH7_E_BRITTLE_TO_BINDER_N0','from_node_id':'SP16_D_MECH7_BRITTLE_REQUIRED','to_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','edge_type':'branch','label':'N=0','condition':cmp('ambient_N_force','eq',0.0),'quantity_ids':['sp16_mech7_brittle_required','ambient_N_force']})
adde({'id':'MECH7_E_TENSION_TO_BINDER','from_node_id':'SP16_D_MECH7_TENSION_POSTYIELD','to_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','edge_type':'control','label':'Eq.(5) tension branch classified','condition':None,'quantity_ids':['sp16_mech7_tension_post_yield_possible']})
adde({'id':'MECH7_E_COMPRESSION_TO_BINDER','from_node_id':'SP16_I_MECH7_COMPRESSION_SLENDERNESS','to_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','edge_type':'control','label':'Table 32 classified','condition':None,'quantity_ids':['sp16_mech7_table32_row','sp16_mech7_group4_slenderness_increase','sp16_mech7_table9_group','sp16_mech7_table10_group','sp16_mech7_flange_edge_stiffened']})
adde({'id':'MECH7_E_BINDER_TO_GATE','from_node_id':'SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER','to_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','edge_type':'control','label':'primary ambient evidence materialized','condition':None,'quantity_ids':['sp16_mech7_primary_evidence']})

# Make MECH7 evidence explicit in the strict aggregator contract.
agg=ns['SP16_C_AMBIENT_MECHANICAL_AGGREGATOR']
if not any(x.get('quantity_id')=='sp16_mech7_primary_evidence' for x in agg['consumes']):
    agg['consumes'].append({'quantity_id':'sp16_mech7_primary_evidence','required':True,'binding_role':'evidence'})
    agg['calculation_spec']['bindings'].append({'variable':'sp16_mech7_primary_evidence','quantity_id':'sp16_mech7_primary_evidence'})
agg['notes']['limitations']='MECH7 binds qualified primary evidence automatically. Dedicated M+Q, universal torsion resistance, detailed local stability and applicable N9/N10 workflows remain explicit fail-closed boundaries.'

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-67_sp16_mech7_primary_ambient_binding'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.67 — SP16-MECH7 Primary Ambient Verification Binding'
g['description']='Cumulative v0.3.67 over v0.3.66: binds qualified axial, stability, slenderness, elastic bending, N+M and LTB evidence directly into the primary ambient session before the strict SP16_MECHANICAL_PASS gate. Context applicability for fatigue and Section 13 is explicit. Unsupported interactions remain fail-closed.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.64_sp16_mech7_primary_ambient_workflow_binding_r1',
 'parent_graph_id':parent,
 'sp16_mech7_primary_binding_layer_closed':True,
 'sp16_mech7_axial_primary_binding_closed':True,
 'sp16_mech7_bending_primary_binding_closed':True,
 'sp16_mech7_nm_primary_binding_closed_for_supported_routes':True,
 'sp16_mech7_ltb_primary_binding_closed_for_major_axis_route':True,
 'sp16_mech7_context_classification_closed':True,
 'sp16_mech7_all_n3_n10_primary_flow_bindings_closed':False,
 'sp16_mech7_mq_primary_binding_closed':False,
 'sp16_mech7_universal_torsion_normative_check_closed':False,
 'sp16_mech7_central_compression_i_local_stability_binding_closed':True,
 'sp16_mech7_detailed_local_stability_primary_binding_closed':False,
 'sp16_mech7_required_n9_n10_auto_execution_closed':False,
 'sp16_mech7_engineering_use_ready':False,
 'sp16_mech6_sp554_transition_requires_pass':True,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
