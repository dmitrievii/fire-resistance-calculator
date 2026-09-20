from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.58_fire_ui22_routing_protection_library_hotfix.json'
OUT=ROOT/'normative_graph/dag_v0.3.59_fire_ui23_protection_route_closure.json'
RELEASE='v0.56_fire_ui23_protection_route_closure_r1'

g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}

def addq(q):
    if q['id'] not in qs:
        g['quantities'].append(q); qs[q['id']]=q
    return qs[q['id']]

def enumq(qid,name,rows,role='decision_state'):
    return addq({'id':qid,'symbol':None,'name_ru':name,'data_type':'enum','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
                 'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'forbidden'},
                 'enum_values':[{'value':v,'label':lab} for v,lab in rows]})

def numq(qid,symbol,name,unit,role='input',source='USER_INPUT'):
    return addq({'id':qid,'symbol':symbol,'name_ru':name,'data_type':'number','role':role,'physical_dimension':'length' if unit=='mm' else None,'canonical_unit':unit,'allowed_units':[unit],
                 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}})

def strq(qid,name,role='diagnostic',source='FORMULA_RESULT'):
    return addq({'id':qid,'symbol':None,'name_ru':name,'data_type':'string','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
                 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}})

def objq(qid,name,role='trace',source='FORMULA_RESULT'):
    return addq({'id':qid,'symbol':None,'name_ru':name,'data_type':'object','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
                 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}})

def addn(n):
    if n['id'] not in ns:
        g['nodes'].append(n);ns[n['id']]=n
    return ns[n['id']]

def addedge(e):
    ids={x['id'] for x in g['edges']}
    if e['id'] not in ids:g['edges'].append(e)

def cmp(qid,value): return {'type':'comparison','quantity_id':qid,'operator':'eq','value':value}
def anysrc(*vals): return {'type':'comparison','quantity_id':'protection_source_mode','operator':'in','value':list(vals)}
def allof(*conds): return {'type':'all_of','conditions':list(conds)}

# ---------------------------------------------------------------------------
# 1. One clear source choice before commercial metadata or material properties.
# ---------------------------------------------------------------------------
enumq('protection_source_mode','Источник расчётных данных огнезащиты',[
 ('sto_arss_library','Материал из библиотеки СТО АРСС'),
 ('manual_properties','Ввести теплофизические свойства вручную'),
 ('documented_product_matrix','Конкретное средство с готовой номограммой/матрицей'),
])
source=addn({
 'id':'SP554_D_PROTECTION_SOURCE_MODE','node_type':'decision','owner_standard_id':'SP554_2026','title':'Источник данных огнезащиты',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'5','clause':'5.8'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.7'}],
 'consumes':[],'produces':[{'quantity_id':'protection_source_mode','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Separates a generic calculation material from a concrete certified product and its documented performance matrix.','limitations':'STO ARSS/manual thermal properties do not assert product compliance under SP554 5.8-5.9.','normative_warning':'Do not substitute another product’s nomogram/matrix.'},
 'question':'Какой источник данных огнезащиты использовать?','decision_quantity_id':'protection_source_mode','options':[
   {'value':'sto_arss_library','label':'Материал из библиотеки СТО АРСС','description':'Выбрать source-traced ρ, W, ε, A, B, C, D и выполнить расчёт по 12.5.'},
   {'value':'manual_properties','label':'Ввести теплофизические свойства вручную','description':'Задать ρ, W, ε, A, B, C, D; требуется собственное подтверждение валидации 12.6.'},
   {'value':'documented_product_matrix','label':'Конкретное средство с готовой номограммой/матрицей','description':'Марка/сертификат + product-specific данные 12.7-12.10.'},
 ]
})
# Incoming routes formerly jumped directly to commercial product metadata.
for e in g['edges']:
    if e['id'] in {'E0047','E0048','UI22_E_POST_PROTECTION'}:
        e['to_node_id']='SP554_D_PROTECTION_SOURCE_MODE'
        e['label']='Перейти к выбору источника огнезащиты'
        e['quantity_ids']=[]
# Commercial fields are conditional now.
if 'SP554_I_PROTECTION' in ns:
    ns['SP554_I_PROTECTION']['applicability']=cmp('protection_source_mode','documented_product_matrix')
    ns['SP554_I_PROTECTION']['notes']={
      'engineering_meaning':'Identification/compliance data of a concrete commercial fire-protection product.',
      'limitations':'Not requested for generic STO ARSS material models or manually authored thermal properties.',
      'normative_warning':'Enter only values documented for the selected product; do not infer fire-hazard class, service life or conformity.'
    }
# New branches: only documented product asks SP554_I_PROTECTION; generic routes go straight to common geometry.
addedge({'id':'UI23_E_SOURCE_PRODUCT','from_node_id':'SP554_D_PROTECTION_SOURCE_MODE','to_node_id':'SP554_I_PROTECTION','edge_type':'branch','label':'Конкретное средство','condition':cmp('protection_source_mode','documented_product_matrix'),'quantity_ids':[]})
addedge({'id':'UI23_E_SOURCE_ARSS_GEOM','from_node_id':'SP554_D_PROTECTION_SOURCE_MODE','to_node_id':'SP554_D_PROTECTION_PERIMETER_MODE','edge_type':'branch','label':'СТО АРСС -> геометрия огнезащиты','condition':cmp('protection_source_mode','sto_arss_library'),'quantity_ids':[]})
addedge({'id':'UI23_E_SOURCE_MAN_GEOM','from_node_id':'SP554_D_PROTECTION_SOURCE_MODE','to_node_id':'SP554_D_PROTECTION_PERIMETER_MODE','edge_type':'branch','label':'Ручные свойства -> геометрия огнезащиты','condition':cmp('protection_source_mode','manual_properties'),'quantity_ids':[]})

# ---------------------------------------------------------------------------
# 2. Dispatch after common geometry/joint questions, without the old confusing
#    "do you have data? -> how generate data?" sequence.
# ---------------------------------------------------------------------------
# Remove old guided exits from the three geometry completion points.
g['edges']=[e for e in g['edges'] if e['id'] not in {'E0051','E0052','E0054'}]
completions=[
 ('SP554_D_JOINTS',cmp('joints_present',False),'NO_JOINTS'),
 ('SP554_D_JOINT_SAME',cmp('joint_protection_same_as_members',True),'SAME_JOINTS'),
 ('SP554_D_JOINT_JUST',cmp('joint_alternative_solution_justified',True),'JUSTIFIED_JOINTS'),
]
for from_id,base,tag in completions:
    addedge({'id':f'UI23_E_{tag}_PRODUCT','from_node_id':from_id,'to_node_id':'SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED','edge_type':'branch','label':'Готовая матрица продукта','condition':allof(base,cmp('protection_source_mode','documented_product_matrix')),'quantity_ids':[]})
    addedge({'id':f'UI23_E_{tag}_ARSS','from_node_id':from_id,'to_node_id':'SP554_D_12_5_ARSS_MATERIAL','edge_type':'branch','label':'Библиотека СТО АРСС','condition':allof(base,cmp('protection_source_mode','sto_arss_library')),'quantity_ids':[]})
    addedge({'id':f'UI23_E_{tag}_MAN','from_node_id':from_id,'to_node_id':'SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES','edge_type':'branch','label':'Ручные свойства','condition':allof(base,cmp('protection_source_mode','manual_properties')),'quantity_ids':[]})

# Old method/source nodes are retained for audit history but cannot participate
# in the primary guided route.
for nid in ['SP554_D_PROTECTION_DATA','SP554_D_PROTECTION_DATA_METHOD','SP554_D_12_5_MATERIAL_SOURCE','SP554_K_PROTECTION_SOURCE_12_5','SP554_I_12_5_GENERATION_GRID','SP554_C_12_5_1D_PERFORMANCE_DATASET']:
    if nid in ns:
        ns[nid].setdefault('notes',{})['limitations']='Legacy/deprecated FIRE-UI2.2 authoring node; excluded from FIRE-UI2.3 primary guided route.'

# Rebase applicability of 12.5 material nodes onto the new source choice.
if 'SP554_D_12_5_ARSS_MATERIAL' in ns: ns['SP554_D_12_5_ARSS_MATERIAL']['applicability']=cmp('protection_source_mode','sto_arss_library')
if 'SP554_C_12_5_ARSS_MATERIAL_LOOKUP' in ns: ns['SP554_C_12_5_ARSS_MATERIAL_LOOKUP']['applicability']=cmp('protection_source_mode','sto_arss_library')
if 'SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES' in ns: ns['SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES']['applicability']=cmp('protection_source_mode','manual_properties')
if 'SP554_C_12_5_BUILD_MODEL_PARAMETERS' in ns:
    n=ns['SP554_C_12_5_BUILD_MODEL_PARAMETERS']
    n['consumes']=[b for b in n['consumes'] if b['quantity_id']!='protection_12_5_material_source']
    n['consumes'].insert(0,{'quantity_id':'protection_source_mode','required':True,'binding_role':'input'})
    n['applicability']=anysrc('sto_arss_library','manual_properties')
    n['notes']['engineering_meaning']='Internal 12.5 material model built from scalar UI/library data; no raw JSON authoring.'
# Old control/material edges: keep lookup/manual -> model, but replace model -> grid/FDM with validation routing.
g['edges']=[e for e in g['edges'] if e['id'] not in {'UI22_E_MODEL_TO_GRID','UI22_E_GRID_TO_FDM','UI22_E_MODEL_TO_FDM','E1159','E1160'}]
# Ensure lookup/manual explicitly continue to model (convert data to control for guided continuity).
for eid in ['UI22_E_MAT_LOOKUP_BUILD','UI22_E_MAT_MAN_BUILD']:
    for e in g['edges']:
        if e['id']==eid:
            e['edge_type']='control'; e['label']='Свойства готовы -> сформировать модель 12.5'

# ---------------------------------------------------------------------------
# 3. SP554 12.6 validation.  Thermal-property sources never bypass this gate:
#    the library supplies properties, not product-specific proof of validation.
# ---------------------------------------------------------------------------
if 'SP554_I_12_6_VALIDATION_EVIDENCE' in ns:
    ns['SP554_I_12_6_VALIDATION_EVIDENCE']['applicability']=anysrc('sto_arss_library','manual_properties')
    ns['SP554_I_12_6_VALIDATION_EVIDENCE']['input_spec']['user_prompt']='Введите максимальное отклонение модели от испытаний, %, и подтвердите полноту набора валидационных случаев 12.6.'
    ns['SP554_I_12_6_VALIDATION_EVIDENCE']['notes']['normative_warning']='Теплофизические свойства из библиотеки СТО АРСС сами по себе не заменяют подтверждение применимости/валидации выбранной расчётной модели по СП554 12.6.'
if 'SP554_Q_12_6_VALIDATION' in ns:
    ns['SP554_Q_12_6_VALIDATION']['applicability']=anysrc('sto_arss_library','manual_properties')
# Build model -> explicit validation evidence for both property-based routes.
addedge({'id':'UI23_E_MODEL_TO_VALIDATION','from_node_id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','to_node_id':'SP554_I_12_6_VALIDATION_EVIDENCE','edge_type':'control','label':'Модель 12.5 готова -> валидация 12.6','condition':None,'quantity_ids':['protection_12_5_model_parameters']})
addedge({'id':'UI23_E_EVIDENCE_CHECK','from_node_id':'SP554_I_12_6_VALIDATION_EVIDENCE','to_node_id':'SP554_Q_12_6_VALIDATION','edge_type':'control','label':'Проверить критерий 20%','condition':None,'quantity_ids':['protection_12_6_max_deviation_pct','protection_12_6_validation_evidence_complete']})
# PASS now goes to direct/inverse task selector instead of matrix normalization.
for e in g['edges']:
    if e['from_node_id']=='SP554_Q_12_6_VALIDATION' and e.get('condition',{}).get('value') is True:
        e['to_node_id']='SP554_D_12_10_MODE'; e['label']='12.6 PASS -> выбрать прямую/обратную задачу'; e['quantity_ids']=['validation_within_20_percent_all_cases']

# ---------------------------------------------------------------------------
# 4. Direct and inverse 12.5 tasks calculate Rprotected directly; no synthetic
#    protection_performance_dataset_raw is required.
# ---------------------------------------------------------------------------
objq('protection_12_5_calculation_trace','Трасса расчёта 12.5')
numq('protection_search_min_thickness_mm','δf,min,search','Нижняя граница поиска толщины огнезащиты','mm')
numq('protection_search_max_thickness_mm','δf,max,search','Верхняя граница поиска толщины огнезащиты','mm')
for qid in ['protection_search_min_thickness_mm','protection_search_max_thickness_mm']:
    qs[qid]['value_constraints']={'min_exclusive':0.0}
addn({
 'id':'SP554_I_12_5_SEARCH_BOUNDS','node_type':'input','owner_standard_id':'SP554_2026','title':'Диапазон поиска минимальной толщины огнезащиты',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.10'}],
 'consumes':[],'produces':[{'quantity_id':'protection_search_min_thickness_mm','required':True,'binding_role':'output'},{'quantity_id':'protection_search_max_thickness_mm','required':True,'binding_role':'output'}],
 'applicability':allof(anysrc('sto_arss_library','manual_properties'),cmp('protected_task_mode','determine_minimum_thickness')),
 'notes':{'engineering_meaning':'Engineer-defined bounded search domain for the 12.5 inverse problem.','limitations':'No result is extrapolated beyond the upper bound.','normative_warning':'Choose bounds compatible with the material/system being studied.'},
 'input_spec':{'input_method':'user_number','required':True,'user_prompt':'Введите нижнюю и верхнюю границы поиска толщины, мм.','allow_default_without_confirmation':False}
})
addn({
 'id':'SP554_C_12_5_DIRECT_PROTECTED_TIME','node_type':'calculation','owner_standard_id':'SP554_2026','title':'Фактический предел при заданной толщине — модель 12.5',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.6'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'13','clause':'13.2'}],
 'consumes':[{'quantity_id':q,'required':True,'binding_role':'input'} for q in ['protection_source_mode','protection_12_5_model_parameters','protection_12_6_validation_evidence_complete','validation_within_20_percent_all_cases','protection_12_6_max_deviation_pct','delta_pr_protected','critical_temperature_c','fire_temperature_regime','protection_candidate_thickness_mm']],
 'produces':[{'quantity_id':'protection_thickness_mm','required':True,'binding_role':'output'},{'quantity_id':'protected_fire_resistance_min','required':True,'binding_role':'output'},{'quantity_id':'protection_12_5_calculation_trace','required':True,'binding_role':'output'}],
 'applicability':allof(anysrc('sto_arss_library','manual_properties'),cmp('protected_task_mode','verify_given_thickness')),
 'notes':{'engineering_meaning':'Executes the validated 1D protected-steel model directly for the specified thickness.','limitations':'Standard-fire route; no substitution by a synthetic 12.7-12.9 matrix.','normative_warning':'Both STO ARSS-library and manual-property routes require explicit 12.6 validation evidence before use.'}
})
addn({
 'id':'SP554_C_12_5_MINIMUM_THICKNESS_SEARCH','node_type':'calculation','owner_standard_id':'SP554_2026','title':'Минимальная толщина огнезащиты — модель 12.5',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.6'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.10'}],
 'consumes':[{'quantity_id':q,'required':True,'binding_role':'input'} for q in ['protection_source_mode','protection_12_5_model_parameters','protection_12_6_validation_evidence_complete','validation_within_20_percent_all_cases','protection_12_6_max_deviation_pct','delta_pr_protected','critical_temperature_c','fire_temperature_regime','required_fire_resistance_min','protection_search_min_thickness_mm','protection_search_max_thickness_mm']],
 'produces':[{'quantity_id':'protection_thickness_mm','required':True,'binding_role':'output'},{'quantity_id':'protected_fire_resistance_min','required':True,'binding_role':'output'},{'quantity_id':'protection_12_5_calculation_trace','required':True,'binding_role':'output'}],
 'applicability':allof(anysrc('sto_arss_library','manual_properties'),cmp('protected_task_mode','determine_minimum_thickness')),
 'notes':{'engineering_meaning':'Bounded inverse search using the same validated 12.5 solver.','limitations':'No extrapolation beyond engineer-defined bounds; non-monotonic response fails closed.','normative_warning':'Rreq is requested only for the inverse task.'}
})
# Task selector: documented matrices retain old 12.10 paths; FDM sources get direct calculation/search.
# Restrict old inverse branch E1165 to documented product route.
for e in g['edges']:
    if e['id']=='E1165':
        e['condition']=allof(cmp('protected_task_mode','determine_minimum_thickness'),cmp('protection_source_mode','documented_product_matrix'))
# Existing E1164 can still lead to the common given-thickness input for all sources.
# From that input branch explicitly by source.
for e in g['edges']:
    if e['id']=='E1167':
        e['edge_type']='branch'; e['condition']=cmp('protection_source_mode','documented_product_matrix'); e['label']='Готовая матрица -> проверка области 12.10'
addedge({'id':'UI23_E_GIVEN_TO_FDM','from_node_id':'SP554_I_12_10_GIVEN_THICKNESS','to_node_id':'SP554_C_12_5_DIRECT_PROTECTED_TIME','edge_type':'branch','label':'Модель 12.5 -> прямой расчёт','condition':anysrc('sto_arss_library','manual_properties'),'quantity_ids':['protection_candidate_thickness_mm']})
# FDM inverse task asks bounds, then calculation.  Matrix inverse goes via E1165.
addedge({'id':'UI23_E_MODE_FDM_INVERSE','from_node_id':'SP554_D_12_10_MODE','to_node_id':'SP554_I_12_5_SEARCH_BOUNDS','edge_type':'branch','label':'12.5 -> диапазон поиска толщины','condition':allof(cmp('protected_task_mode','determine_minimum_thickness'),anysrc('sto_arss_library','manual_properties')),'quantity_ids':[]})
addedge({'id':'UI23_E_BOUNDS_TO_FDM_INVERSE','from_node_id':'SP554_I_12_5_SEARCH_BOUNDS','to_node_id':'SP554_C_12_5_MINIMUM_THICKNESS_SEARCH','edge_type':'control','label':'Выполнить ограниченный поиск','condition':None,'quantity_ids':['protection_search_min_thickness_mm','protection_search_max_thickness_mm']})
# Both FDM results go straight to protected result stage.
addedge({'id':'UI23_E_FDM_DIRECT_RESULT','from_node_id':'SP554_C_12_5_DIRECT_PROTECTED_TIME','to_node_id':'SP554_R_PROTECTED','edge_type':'control','label':'Rprotected рассчитан','condition':None,'quantity_ids':['protected_fire_resistance_min','protection_thickness_mm']})
addedge({'id':'UI23_E_FDM_INVERSE_RESULT','from_node_id':'SP554_C_12_5_MINIMUM_THICKNESS_SEARCH','to_node_id':'SP554_R_PROTECTED','edge_type':'control','label':'Минимальная толщина и Rprotected рассчитаны','condition':None,'quantity_ids':['protected_fire_resistance_min','protection_thickness_mm']})

# ---------------------------------------------------------------------------
# 5. Documented-product matrix remains product-specific, but the input is a
#    specialized editor in the presentation layer rather than raw JSON text.
# ---------------------------------------------------------------------------
if 'SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED' in ns:
    n=ns['SP554_I_PROTECTION_PERFORMANCE_DOCUMENTED']
    n['applicability']=cmp('protection_source_mode','documented_product_matrix')
    n['notes']['engineering_meaning']='Structured editor/import for a concrete product-specific matrix/nomogram; internally materialized as protection_performance_dataset_raw.'
    n['notes']['limitations']='Critical-temperature level, reduced-thickness axis, protection-thickness axis and time matrix must come from the selected product documentation.'
# Normalizer must not be activated by legacy 12.5 source/data edges.
g['edges']=[e for e in g['edges'] if e['id'] not in {'E1159','E1160'}]
# The structured payload carries source_kind itself; the legacy source-kind
# producer is no longer a required dependency.
if 'SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET' in ns:
    ns['SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET']['consumes']=[b for b in ns['SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET']['consumes'] if b['quantity_id']!='protection_performance_source_kind']
# Make the raw documented matrix input explicitly navigate to normalizer.
for e in g['edges']:
    if e['id']=='E1140':
        e['edge_type']='control'; e['label']='Структурированная матрица -> нормализация'
# Normalizer default source is supplied by payload/editor; no K-source dependency required.

# Strengthen old 12.10 nodes so only documented-product route can execute.
for nid in ['SP554_C_12_10_DOMAIN','SP554_C_12_10_DOMAIN_INVERSE','SP554_C_12_10_MINIMUM_THICKNESS','SP554_C_12_10_PROTECTED_TIME']:
    if nid in ns:
        old=ns[nid].get('applicability')
        ns[nid]['applicability']=allof(cmp('protection_source_mode','documented_product_matrix'), old) if old else cmp('protection_source_mode','documented_product_matrix')

# ---------------------------------------------------------------------------
# Release identity.
# ---------------------------------------------------------------------------
parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-59_fire_ui23_protection_route_closure'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.59 — FIRE-UI2.3 fire-protection route closure'
g['description']='Cumulative v0.3.59 over v0.3.58: makes fire-protection source selection explicit; commercial metadata is product-only; STO ARSS/manual properties route through validated SP554 12.5 FDM without raw object authoring; documented product matrices use a structured editor; inverse 12.5 search is bounded and fail-closed.'
md=g.setdefault('metadata',{})
md.update({'release_stage':RELEASE,'parent_graph_id':parent,
 'fire_ui23_protection_source_selector_closed':True,
 'fire_ui23_product_metadata_conditional_closed':True,
 'fire_ui23_sto_arss_direct_12_5_route_closed':True,
 'fire_ui23_manual_properties_direct_12_5_route_closed':True,
 'fire_ui23_raw_object_primary_ui_removed':True,
 'fire_ui23_bounded_inverse_12_5_closed':True,
 'fire_ui23_qy_runtime_closed':False,'fire_ui23_torsion_runtime_closed':False})

# Integrity.
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]
    assert len(ids)==len(set(ids)), f'duplicate {key} id'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
