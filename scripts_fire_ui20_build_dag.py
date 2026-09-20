from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.55_fire_ui19_sp554_table1_heated_perimeter_matrix.json'
OUT=ROOT/'normative_graph/dag_v0.3.56_fire_ui20_conditional_signed_moments_thermal_bindings.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={x['id']:x for x in g['quantities']}
ns={x['id']:x for x in g['nodes']}


def ref923():
    return [{'standard_id':'SP16_2017','reference_kind':'clause','section':'9','clause':'9.2.3'}]

def ref926():
    return [{'standard_id':'SP16_2017','reference_kind':'clause','section':'9','clause':'9.2.6'}]

def input_node(nid,title,quantities,refs,warning):
    return {
      'id':nid,'node_type':'input','owner_standard_id':'SP16_2017','title':title,
      'normative_refs':refs,
      'consumes':[{'quantity_id':'special_load_combination','required':True,'binding_role':'input'}],
      'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in quantities],
      'applicability':None,
      'notes':{
        'engineering_meaning':'Branch-specific signed moments used by the selected SP16 rule.',
        'limitations':'Only moments required by the active normative branch are authored.',
        'normative_warning':warning,
      },
      'input_spec':{'input_method':'user_fields','required':True,'allow_default_without_confirmation':False},
    }

# ---------------------------------------------------------------------------
# General UI/data-model remediation: internal LTB object must not be authored.
# ---------------------------------------------------------------------------
for nid in ('SP554_I_NM_CONTEXT','SP554_I_BENDING_CONTEXT'):
    node=ns[nid]
    node['produces']=[b for b in node.get('produces',[]) if b.get('quantity_id')!='beam_ltb_context']
    node.setdefault('notes',{})['engineering_meaning']='Engineering context only. LTB-specific conditions are collected by the dedicated SP16 selectors; no raw context object is required.'
for nid in ('SP16_D_LTB','SP16_D_PHI_B_SECTION_ROUTE'):
    node=ns[nid]
    node['consumes']=[b for b in node.get('consumes',[]) if b.get('quantity_id')!='beam_ltb_context']

# Signed moment inputs are an invariant; wording must not imply magnitude-only input.
signed_names={
 'M_max_full_length':'Знаковый момент максимального по модулю сечения по полной длине',
 'M_max_constant_segment':'Знаковый момент максимального по модулю сечения участка постоянного сечения',
 'M_fixed_end':'Знаковый момент в заделке',
 'M_at_L_over_3':'Знаковый момент в сечении L/3',
 'M_mid_third_panel_max':'Знаковый максимальный по модулю момент в средней трети панели пояса',
 'M_mid_third_member_raw':'Знаковый максимальный по модулю момент в средней трети стержня до ограничения 0,5Mmax',
 'M_x_mid_third_max':'Знаковый Mx максимального по модулю сечения в средней трети',
 'M_x_full_length_max':'Знаковый Mx максимального по модулю сечения по всей длине',
 'M_x_fixed_end':'Знаковый Mx в заделке',
 'M_x_at_L_over_3':'Знаковый Mx в сечении L/3 от заделки',
}
for qid,name in signed_names.items():
    q=qs[qid]
    q['name_ru']=name
    q['role']='input'
    q.setdefault('source_policy',{})['primary_source_type']='LOAD_INPUT'
    q['description']='FIRE-UI2.0 invariant: the engineer enters the physical moment with its sign. Absolute value is used only by the normative comparison that requires magnitude.'
# Derived signed design moment is no longer a user input.
q=qs['M_x_c_signed']; q['role']='intermediate'; q['name_ru']='Знаковый Mx,c, автоматически сохранённый от определяющего исходного момента'
q['source_policy']={'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'}
q['description']='Derived from the signed source moment selected by SP16 9.2.6; never re-entered by the user.'
qs['M_max_full_length_signed_9_2_3']['role']='intermediate'
qs['M_max_full_length_signed_9_2_3']['description']='Deprecated FIRE-UI2.0 compatibility quantity. Signed Mmax is retained directly in M_max_full_length.'

# ---------------------------------------------------------------------------
# SP16 9.2.3: decision first, then branch-specific signed moment inputs.
# ---------------------------------------------------------------------------
remove_nodes={'SP16_I_MOMENT_DIST','SP16_I_MOMENT_SUMMARY_9_2_3'}
g['nodes']=[n for n in g['nodes'] if n['id'] not in remove_nodes]
for nid in remove_nodes: ns.pop(nid,None)
# Remove every edge touching the obsolete nodes and old direct decision->calculation edges.
old_targets={'SP16_C_M_CONST_FRAME','SP16_C_M_STEPPED','SP16_C_M_FIXED_FREE','SP16_C_M_COMPRESSED_CHORD','SP16_K_TABLE20_WC_SIDE'}
g['edges']=[e for e in g['edges'] if e['from_node_id'] not in remove_nodes and e['to_node_id'] not in remove_nodes and not (e['from_node_id']=='SP16_D_M_RULE' and e['to_node_id'] in old_targets)]
# Existing handoff from NM context now enters the rule selector directly.
for e in g['edges']:
    if e['id']=='E0269':
        e['to_node_id']='SP16_D_M_RULE'; e['label']='SP16 9.2.3 rule selection'; e['quantity_ids']=[]
# Decision no longer depends on a raw object.
d=ns['SP16_D_M_RULE']; d['consumes']=[]
d.setdefault('notes',{})['normative_warning']='N and M must originate from one and the same load combination, from undeformed-system analysis with elastic steel behavior. Moments entered in the selected branch retain their algebraic sign.'

branch_nodes=[
 input_node('SP16_I_M_CONST_FRAME_9_2_3','Момент по 9.2.3 — колонна постоянного сечения',['M_max_full_length'],ref923(),'Введите момент со знаком. Для нормативного выбора используется его модуль; исходный знак сохраняется.'),
 input_node('SP16_I_M_STEPPED_9_2_3','Момент по 9.2.3 — ступенчатая колонна',['M_max_constant_segment'],ref923(),'Введите определяющий момент на рассматриваемом участке постоянного сечения со знаком.'),
 input_node('SP16_I_M_FIXED_FREE_9_2_3','Моменты по 9.2.3 — защемление / свободный конец',['M_fixed_end','M_at_L_over_3'],ref923(),'Оба момента вводятся со знаком. Нормативный выбор выполняется по модулю.'),
 input_node('SP16_I_M_COMPRESSED_CHORD_9_2_3','Момент по 9.2.3 — сжатый пояс с внеузловой нагрузкой',['M_mid_third_panel_max'],ref923(),'Введите знаковый максимальный по модулю момент в средней трети панели, полученный из требуемого упругого расчёта.'),
 input_node('SP16_I_M_TABLE20_9_2_3','Моменты по 9.2.3 — ветвь таблицы 20',['M_max_full_length','M_mid_third_member_raw'],ref923(),'Моменты вводятся со знаком. Отдельный повторный ввод знака Mmax не требуется.'),
]
for n in branch_nodes: g['nodes'].append(n); ns[n['id']]=n
new_edges=[
 ('UI20_E923_1','SP16_D_M_RULE','SP16_I_M_CONST_FRAME_9_2_3','constant_frame_column','constant column'),
 ('UI20_E923_2','SP16_D_M_RULE','SP16_I_M_STEPPED_9_2_3','stepped_column','stepped column'),
 ('UI20_E923_3','SP16_D_M_RULE','SP16_I_M_FIXED_FREE_9_2_3','fixed_free','fixed-free'),
 ('UI20_E923_4','SP16_D_M_RULE','SP16_I_M_COMPRESSED_CHORD_9_2_3','compressed_chord_off_node_load','compressed chord'),
 ('UI20_E923_5','SP16_D_M_RULE','SP16_I_M_TABLE20_9_2_3','pin_pin_monosymmetric_table20','Table 20'),
]
for eid,f,t,val,label in new_edges:
    g['edges'].append({'id':eid,'from_node_id':f,'to_node_id':t,'edge_type':'branch','label':label,'condition':{'type':'comparison','quantity_id':'sp16_moment_rule','operator':'eq','value':val},'quantity_ids':[]})
for eid,f,t,qids in [
 ('UI20_E923_6','SP16_I_M_CONST_FRAME_9_2_3','SP16_C_M_CONST_FRAME',['M_max_full_length']),
 ('UI20_E923_7','SP16_I_M_STEPPED_9_2_3','SP16_C_M_STEPPED',['M_max_constant_segment']),
 ('UI20_E923_8','SP16_I_M_FIXED_FREE_9_2_3','SP16_C_M_FIXED_FREE',['M_fixed_end','M_at_L_over_3']),
 ('UI20_E923_9','SP16_I_M_COMPRESSED_CHORD_9_2_3','SP16_C_M_COMPRESSED_CHORD',['M_mid_third_panel_max']),
 ('UI20_E923_10','SP16_I_M_TABLE20_9_2_3','SP16_K_TABLE20_WC_SIDE',['M_max_full_length','M_mid_third_member_raw']),
]:
    g['edges'].append({'id':eid,'from_node_id':f,'to_node_id':t,'edge_type':'control','label':'signed branch inputs resolved','condition':None,'quantity_ids':qids})
# Table-20 compressed-fibre selection uses the signed source Mmax directly.
k=ns['SP16_K_TABLE20_WC_SIDE']
for b in k['consumes']:
    if b['quantity_id']=='M_max_full_length_signed_9_2_3': b['quantity_id']='M_max_full_length'
for rule in k.get('classification_rules',[]):
    when=rule.get('when') or {}
    if when.get('quantity_id')=='M_max_full_length_signed_9_2_3': when['quantity_id']='M_max_full_length'
k.setdefault('notes',{})['engineering_meaning']='Compressed-fibre side is resolved directly from the algebraic sign of M_max_full_length entered for the active Table-20 branch.'

# ---------------------------------------------------------------------------
# SP16 9.2.6: decision first, branch-specific signed inputs, derive Mx,c sign.
# ---------------------------------------------------------------------------
remove_nodes={'SP16_I_C_MOMENTS_9_2_6','SP16_I_C_SIGNED_MX'}
g['nodes']=[n for n in g['nodes'] if n['id'] not in remove_nodes]
for nid in remove_nodes: ns.pop(nid,None)
g['edges']=[e for e in g['edges'] if e['from_node_id'] not in remove_nodes and e['to_node_id'] not in remove_nodes and not (e['from_node_id']=='SP16_D_C_MOMENT_RULE' and e['to_node_id'] in {'SP16_C_C_MX_RESTRAINED','SP16_C_C_MX_FIXED_FREE'})]
# Route standard 9.2.5 directly to 9.2.6 scheme selector.
for e in g['edges']:
    if e['id']=='E0774':
        e['to_node_id']='SP16_D_C_MOMENT_RULE'; e['label']='9.2.5 -> 9.2.6 scheme'; e['quantity_ids']=[]

n1=input_node('SP16_I_C_M_RESTRAINED_9_2_6','Характерные Mx по 9.2.6 — закреплённый стержень',['M_x_mid_third_max','M_x_full_length_max'],ref926(),'Введите оба Mx со знаком. Сравнение max(|Mmid|, 0,5|Mmax|) не уничтожает знак определяющего источника.')
n2=input_node('SP16_I_C_M_FIXED_FREE_9_2_6','Характерные Mx по 9.2.6 — консоль',['M_x_fixed_end','M_x_at_L_over_3'],ref926(),'Введите оба Mx со знаком. Сравнение выполняется по модулю, знак выбранного исходного момента сохраняется.')
for n in (n1,n2): g['nodes'].append(n); ns[n['id']]=n
for eid,t,val,label in [
 ('UI20_E926_1','SP16_I_C_M_RESTRAINED_9_2_6','restrained_lateral_displacement','restrained'),
 ('UI20_E926_2','SP16_I_C_M_FIXED_FREE_9_2_6','fixed_free','fixed-free'),
]:
    g['edges'].append({'id':eid,'from_node_id':'SP16_D_C_MOMENT_RULE','to_node_id':t,'edge_type':'branch','label':label,'condition':{'type':'comparison','quantity_id':'sp16_c_moment_rule','operator':'eq','value':val},'quantity_ids':[]})
g['edges'] += [
 {'id':'UI20_E926_3','from_node_id':'SP16_I_C_M_RESTRAINED_9_2_6','to_node_id':'SP16_C_C_MX_RESTRAINED','edge_type':'control','label':'signed Mx inputs','condition':None,'quantity_ids':['M_x_mid_third_max','M_x_full_length_max']},
 {'id':'UI20_E926_4','from_node_id':'SP16_I_C_M_FIXED_FREE_9_2_6','to_node_id':'SP16_C_C_MX_FIXED_FREE','edge_type':'control','label':'signed Mx inputs','condition':None,'quantity_ids':['M_x_fixed_end','M_x_at_L_over_3']},
]
# The two existing calculation nodes now materialize both magnitude and selected signed source.
for nid in ('SP16_C_C_MX_RESTRAINED','SP16_C_C_MX_FIXED_FREE'):
    node=ns[nid]
    if not any(b['quantity_id']=='M_x_c_signed' for b in node['produces']):
        node['produces'].append({'quantity_id':'M_x_c_signed','required':True,'binding_role':'output'})
    node.setdefault('notes',{})['engineering_meaning']='Selects the design magnitude according to SP16 9.2.6 while retaining the algebraic sign of the determining source moment.'
    # A custom FIRE-UI2.0 executor returns both outputs.
    node.pop('calculation_spec',None)
# Replace the former interactive sign round-trip by direct consistency check.
for src,eid in [('SP16_C_C_MX_RESTRAINED','UI20_E926_5'),('SP16_C_C_MX_FIXED_FREE','UI20_E926_6')]:
    g['edges'].append({'id':eid,'from_node_id':src,'to_node_id':'SP16_Q_C_SIGNED_MX','edge_type':'data','label':'derived magnitude + signed source','condition':None,'quantity_ids':['M_x_c_design','M_x_c_signed']})
ns['SP16_Q_C_SIGNED_MX'].setdefault('notes',{})['engineering_meaning']='Internal consistency check only; Mx,c sign is derived automatically and is never re-entered by the engineer.'

# ---------------------------------------------------------------------------
# Table 21 explanatory selector and fail-closed diagnostic wording.
# ---------------------------------------------------------------------------
t21=ns['SP16_D_TABLE21_TYPE']
t21['question']='Какой графической схеме сечения и эксцентриситета таблицы 21 соответствует расчётный случай?'
t21['options']=[
 {'value':'1','label':'Тип 1','description':'Сопоставьте форму сечения, оси и направление эксцентриситета со схемой типа 1 таблицы 21.'},
 {'value':'2','label':'Тип 2','description':'Сопоставьте форму сечения, оси и направление эксцентриситета со схемой типа 2 таблицы 21.'},
 {'value':'3','label':'Тип 3','description':'Сопоставьте форму сечения, оси и направление эксцентриситета со схемой типа 3 таблицы 21.'},
 {'value':'4','label':'Тип 4','description':'Тип 4 использует геометрию неравных полок; downstream учитывает отношение I2/I1 по обозначениям таблицы 21.'},
]
t21.setdefault('notes',{})['normative_warning']='Выбор основан на графической схеме таблицы 21, а не только на номере. Если соответствие неоднозначно, не угадывайте тип.'

r=ns['SP554_R_UI16_DEFERRED_BRANCHES']
r['title']='Механическая проверка не завершена — есть неподдержанные воздействия'
r.setdefault('notes',{})['engineering_meaning']='Terminal diagnostic enumerates the actual deferred verification-plan branches and their entered load values. Supported branches are not discarded.'
r['notes']['limitations']='Qy and torsion T remain fail-closed in FIRE-UI2.0; no Qy->Qz and no T->B substitution.'

# Release identity.
g['graph_id']='sp16_sp554_dag_v0-3-56_fire_ui20_conditional_signed_moments_thermal_bindings'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.56 — FIRE-UI2.0 conditional signed moments + thermal bindings'
g['description']='Cumulative v0.3.56 over FIRE-UI1.9: conditional SP16 9.2.3/9.2.6 signed moment authoring, derived sign preservation, raw LTB-object removal, Table-21 explanatory UI support, thermal execution bindings and explicit incomplete-mechanical diagnostics.'
meta=g.setdefault('metadata',{})
meta['release_stage']='v0.53_fire_ui20_conditional_signed_moments_thermal_bindings_r1'
meta['parent_graph_id']='sp16_sp554_dag_v0-3-55_fire_ui19_sp554_table1_heated_perimeter_matrix'
meta['fire_ui20_boolean_selectors']=True
meta['fire_ui20_raw_ltb_object_removed']=True
meta['fire_ui20_sp16_9_2_3_branch_inputs']=True
meta['fire_ui20_sp16_9_2_6_branch_inputs']=True
meta['fire_ui20_signed_moment_provenance']=True
meta['fire_ui20_thermal_execution_bindings']=True
meta['fire_ui20_qy_runtime_closed']=False
meta['fire_ui20_torsion_runtime_closed']=False

# Stable de-duplication / uniqueness check.
node_ids=[n['id'] for n in g['nodes']]; edge_ids=[e['id'] for e in g['edges']]
assert len(node_ids)==len(set(node_ids)), 'duplicate node id'
assert len(edge_ids)==len(set(edge_ids)), 'duplicate edge id'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
