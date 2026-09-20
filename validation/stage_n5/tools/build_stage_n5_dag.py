import json
from pathlib import Path
import jsonschema
root=Path('/mnt/data/stage_n5_work')
parent=json.loads((root/'normative_graph/dag_v0.3.33_stage_n4.json').read_text())
d=json.loads(json.dumps(parent))
d['graph_id']='sp16_sp554_dag_v0-3-34_stage_n5'
d['graph_title']='SP16 + SP554 atomic normative DAG v0.3.34 — Stage N5 beam-column guided closure'
d['description']=parent['description'] + ' Stage N5 adds an explicit current-SP16 Section 9 guided orchestration layer; existing Section 9 atomic formula/table nodes remain the normative producers. Table D.3 remains exact-grid, interpolation=none.'

def sp_user(role='input'):
 return {'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'required_explicit'}
def sp_runtime():
 return {'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'}
def q(id,name,typ='string',role='input',dim=None,unit=None,enum=None,source=None):
 x={'id':id,'symbol':None,'name_ru':name,'data_type':typ,'role':role,'physical_dimension':dim,'canonical_unit':unit,'allowed_units':[] if unit is None else [unit],'source_policy':source or (sp_user(role) if role=='input' else sp_runtime())}
 if enum is not None:
  x['data_type']='enum'; x['enum_values']=[{'value':v,'label':lab} for v,lab in enum]
 return x
qs=[
 q('sp16_n5_member_form','Stage N5 — форма сечения/стержня',enum=[('solid_open','сплошное открытое'),('solid_box','коробчатое'),('built_up','сквозное')]),
 q('sp16_n5_same_combo_confirmed','N и M приняты из одного сочетания по 9.2.3','boolean'),
 q('sp16_n5_section_classification_confirmed','Классификация сечения подтверждена','boolean'),
 q('sp16_n5_major_symmetry_confirmed','Плоскость наибольшей жесткости совпадает с плоскостью симметрии','boolean'),
 q('sp16_n5_strength_method','Запрошенный метод прочности 9.1.1',enum=[('auto','автовыбор (105)/(106)'),('equation_106','явно (106)')]),
 q('sp16_n5_direct_dynamic','Непосредственное динамическое воздействие','boolean'),
 q('sp16_n5_shear_stress','Касательное напряжение для применимости (105)','number','input','stress','MPa'),
 q('sp16_n5_strength_route','Stage N5 — выбранная ветвь прочности','string','classification',source=sp_runtime()),
 q('sp16_n5_stability_route','Stage N5 — выбранная ветвь устойчивости','string','classification',source=sp_runtime()),
 q('sp16_n5_d3_x_status','Статус разрешения таблицы Д.3 по x','string','diagnostic',source=sp_runtime()),
 q('sp16_n5_d3_y_status','Статус разрешения таблицы Д.3 по y','string','diagnostic',source=sp_runtime()),
 q('sp16_n5_d3_policy','Stage N5 — политика Д.3','string','classification',source=sp_runtime()),
 q('sp16_n5_external_d3_basis','Явное основание внешнего коэффициента Д.3','string','input'),
 q('sp16_n5_required_unresolved','Неразрешенные обязательные входы Stage N5','string','diagnostic',source=sp_runtime()),
 q('sp16_n5_runtime_status','Итоговый статус guided runtime Stage N5','string','result',source=sp_runtime()),
 q('sp16_n5_release_gate','Gate закрытия Stage N5','boolean','result',source=sp_runtime()),
]
d['quantities'].extend(qs)

def ref(clause,kind='clause',formula=None,table=None,annex=None):
 r={'standard_id':'SP16_2017','reference_kind':kind,'section':'9','clause':clause}
 if formula:r['formula_ref']=formula
 if table:r['table_ref']=table
 if annex:r['annex_ref']=annex
 return r
def binding(qid,role): return {'quantity_id':qid,'required':True,'binding_role':role}
def notes(lim=None,warn=None): return {'engineering_meaning':None,'limitations':lim,'normative_warning':warn}
def inode(id,title,qids,prompt,refs):
 return {'id':id,'node_type':'input','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[],'produces':[binding(x,'output') for x in qids],'applicability':None,'notes':notes(),'input_spec':{'input_method':'user_selection','required':True,'user_prompt':prompt,'allow_default_without_confirmation':False}}

def classnode(id,title,consumes,out,rules,refs,lim=None):
 return {'id':id,'node_type':'classification','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[binding(x,'input') for x in consumes],'produces':[binding(out,'output')],'applicability':None,'notes':notes(lim),'output_quantity_id':out,'classification_rules':rules,'fallback_behavior':'error'}

nodes=[
 inode('SP16_N5_I_MEMBER_FORM','Stage N5 — тип beam-column',['sp16_n5_member_form'],'Выберите форму стержня/сечения',[ref('9.2')]),
 inode('SP16_N5_I_SAME_COMBO','Stage N5 — подтверждение сочетания',['sp16_n5_same_combo_confirmed'],'Подтвердите одно сочетание N,M',[ref('9.2.3')]),
 inode('SP16_N5_I_SECTION_CLASS','Stage N5 — классификация сечения',['sp16_n5_section_classification_confirmed'],'Подтвердите классификацию сечения',[ref('9.1'),ref('9.2')]),
 inode('SP16_N5_I_SYMMETRY','Stage N5 — геометрическая применимость',['sp16_n5_major_symmetry_confirmed'],'Подтвердите плоскость симметрии',[ref('9.2.4'),ref('9.2.9')]),
 inode('SP16_N5_I_STRENGTH_CONTROL','Stage N5 — условия выбора (105)/(106)',['sp16_n5_strength_method','sp16_n5_direct_dynamic','sp16_n5_shear_stress'],'Задайте условия прочности 9.1.1',[ref('9.1.1')]),
 classnode('SP16_N5_K_STRENGTH_ROUTE','Stage N5 — ветвление прочности 9.1.1',['sp16_n5_strength_method','sp16_n5_direct_dynamic'],'sp16_n5_strength_route',[
  {'when':{'type':'comparison','quantity_id':'sp16_n5_strength_method','operator':'eq','value':'equation_106'},'output_value':'eq106','label':'явно формула (106)'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_direct_dynamic','operator':'eq','value':True},'output_value':'eq106','label':'динамика исключает (105)'},
  {'when':{'type':'all_of','conditions':[{'type':'comparison','quantity_id':'sp16_n5_strength_method','operator':'eq','value':'auto'},{'type':'comparison','quantity_id':'sp16_n5_direct_dynamic','operator':'eq','value':False}]},'output_value':'eq105_if_remaining_gates_pass','label':'(105) при остальных условиях 9.1.1'}
 ],[ref('9.1.1','formula','(105)'),ref('9.1.1','formula','(106)')],'Полная применимость (105) дополнительно зависит от Ryn, tau/Rs и условий 8.5.8/8.5.18; runtime проверяет их атомарной процедурой.'),
 classnode('SP16_N5_K_STABILITY_ROUTE','Stage N5 — ветвление устойчивости 9.2',['sp16_n5_member_form','sp16_n5_major_symmetry_confirmed'],'sp16_n5_stability_route',[
  {'when':{'type':'comparison','quantity_id':'sp16_n5_member_form','operator':'eq','value':'built_up'},'output_value':'specialized_9.3_9.4','label':'сквозные — dedicated action'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_member_form','operator':'eq','value':'solid_box'},'output_value':'specialized_9.2.10','label':'коробчатые — detailed action'},
  {'when':{'type':'all_of','conditions':[{'type':'comparison','quantity_id':'sp16_n5_member_form','operator':'eq','value':'solid_open'},{'type':'comparison','quantity_id':'sp16_n5_major_symmetry_confirmed','operator':'eq','value':True}]},'output_value':'guided_9.2.2_9.2.9','label':'квалифицированный solid-open маршрут'}
 ],[ref('9.2.1'),ref('9.2.2'),ref('9.2.9')],'Подветви по Mx/My, meff и lambda выполняет runtime на существующих атомарных узлах.'),
 inode('SP16_N5_I_D3_X_STATUS','Stage N5 — статус lookup Д.3 x',['sp16_n5_d3_x_status'],'Runtime status D.3 x',[ref('9.2.2','table',table='Д.3',annex='Д')]),
 inode('SP16_N5_I_D3_Y_STATUS','Stage N5 — статус lookup Д.3 y',['sp16_n5_d3_y_status'],'Runtime status D.3 y',[ref('9.2.2','table',table='Д.3',annex='Д')]),
 classnode('SP16_N5_K_D3_POLICY','Stage N5 — политика неузловых значений Д.3',['sp16_n5_d3_x_status','sp16_n5_d3_y_status'],'sp16_n5_d3_policy',[
  {'when':{'type':'all_of','conditions':[{'type':'comparison','quantity_id':'sp16_n5_d3_x_status','operator':'eq','value':'D3_EXACT_NODE'},{'type':'comparison','quantity_id':'sp16_n5_d3_y_status','operator':'eq','value':'D3_EXACT_NODE'}]},'output_value':'exact_grid','label':'оба lookup в узлах'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_d3_x_status','operator':'eq','value':'EXTERNAL_D3_COEFFICIENT_USED'},'output_value':'external_explicit','label':'внешний явно атрибутированный x'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_d3_y_status','operator':'eq','value':'EXTERNAL_D3_COEFFICIENT_USED'},'output_value':'external_explicit','label':'внешний явно атрибутированный y'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_d3_x_status','operator':'eq','value':'EXTERNAL_D3_COEFFICIENT_REQUIRED'},'output_value':'fail_closed','label':'неузловой x без политики'},
  {'when':{'type':'comparison','quantity_id':'sp16_n5_d3_y_status','operator':'eq','value':'EXTERNAL_D3_COEFFICIENT_REQUIRED'},'output_value':'fail_closed','label':'неузловой y без политики'}
 ],[ref('9.2.2','table',table='Д.3',annex='Д')],'Родительские SP16_L_D3_PHI_EX/EY имеют interpolation.method=none; этот узел не вводит интерполяцию.'),
 {'id':'SP16_N5_R_D3_FAIL_CLOSED','node_type':'result','owner_standard_id':'SP16_2017','title':'Stage N5 — Д.3 не разрешена без явной внешней политики','normative_refs':[ref('9.2.2','table',table='Д.3',annex='Д')],'consumes':[binding('sp16_n5_d3_policy','input')],'produces':[],'applicability':{'type':'comparison','quantity_id':'sp16_n5_d3_policy','operator':'eq','value':'fail_closed'},'notes':notes('Расчетная ветвь останавливается; численная интерполяция не предполагается.','NormCAD может интерполировать, но это не становится нормативным producer без отдельного правила.'),'result_quantity_ids':['sp16_n5_d3_policy'],'result_kind':'diagnostic'}
]
d['nodes'].extend(nodes)
edges=[
 ('N5_E_001','SP16_N5_I_MEMBER_FORM','SP16_N5_K_STABILITY_ROUTE',['sp16_n5_member_form']),
 ('N5_E_002','SP16_N5_I_SYMMETRY','SP16_N5_K_STABILITY_ROUTE',['sp16_n5_major_symmetry_confirmed']),
 ('N5_E_003','SP16_N5_I_STRENGTH_CONTROL','SP16_N5_K_STRENGTH_ROUTE',['sp16_n5_strength_method']),
 ('N5_E_004','SP16_N5_I_STRENGTH_CONTROL','SP16_N5_K_STRENGTH_ROUTE',['sp16_n5_direct_dynamic']),
 ('N5_E_005','SP16_N5_I_D3_X_STATUS','SP16_N5_K_D3_POLICY',['sp16_n5_d3_x_status']),
 ('N5_E_006','SP16_N5_I_D3_Y_STATUS','SP16_N5_K_D3_POLICY',['sp16_n5_d3_y_status']),
 ('N5_E_007','SP16_N5_K_D3_POLICY','SP16_N5_R_D3_FAIL_CLOSED',['sp16_n5_d3_policy']),
 ('N5_E_008','SP16_N5_I_SAME_COMBO','SP16_N5_K_STABILITY_ROUTE',['sp16_n5_same_combo_confirmed']),
 ('N5_E_009','SP16_N5_I_SECTION_CLASS','SP16_N5_K_STABILITY_ROUTE',['sp16_n5_section_classification_confirmed']),
 ('N5_E_010','SP16_N5_K_STRENGTH_ROUTE','SP16_N5_K_STABILITY_ROUTE',['sp16_n5_strength_route']),
]
for eid,a,b,qs in edges:
 d['edges'].append({'id':eid,'from_node_id':a,'to_node_id':b,'edge_type':'data','label':None,'condition':None,'quantity_ids':qs})
out=root/'normative_graph/dag_v0.3.34_stage_n5.json'
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
schema=json.loads((root/'normative_graph/dag_schema.json').read_text())
jsonschema.Draft202012Validator(schema).validate(d)
print('VALID',len(d['quantities']),len(d['nodes']),len(d['edges']))
