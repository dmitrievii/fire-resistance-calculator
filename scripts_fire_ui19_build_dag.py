from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.54_fire_ui18_fire_d2_to_d3_handoff_hotfix.json'
OUT=ROOT/'normative_graph/dag_v0.3.55_fire_ui19_sp554_table1_heated_perimeter_matrix.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={x['id']:x for x in g['quantities']}; ns={x['id']:x for x in g['nodes']}; es={x['id']:x for x in g['edges']}

def addq(q):
    if q['id'] not in qs:
        g['quantities'].append(q); qs[q['id']]=q

def addn(n):
    if n['id'] not in ns:
        g['nodes'].append(n); ns[n['id']]=n

def adde(e):
    if e['id'] not in es:
        g['edges'].append(e); es[e['id']]=e

# Separate the two independent Table-1 dimensions: exposed sides and protection geometry.
q=qs['heated_exposure_configuration']
q['name_ru']='Количество обогреваемых сторон'
q['enum_values']=[
    {'value':'three_sides','label':'3 стороны'},
    {'value':'four_sides','label':'4 стороны'},
]
q['description']='FIRE-UI1.9: fire exposure is independent from the protection geometry; contour/box are selected only on the protected route.'

addq({
 'id':'sp554_table1_perimeter_trace','symbol':None,'name_ru':'Трассировка обогреваемого периметра по таблице 1 (без огнезащиты)',
 'data_type':'object','role':'trace','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
 'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT','GEOMETRY_ENGINE_RESULT'],'override_policy':'forbidden'}
})
addq({
 'id':'fire_protection_perimeter_mode','symbol':None,'name_ru':'Схема выполнения огнезащиты по обогреваемому периметру',
 'data_type':'enum','role':'input','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
 'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'forbidden'},
 'enum_values':[{'value':'contour','label':'По контуру сечения'},{'value':'box','label':'В виде короба'}]
})
addq({
 'id':'sp554_protected_perimeter_domain_ok','symbol':None,'name_ru':'Автоматический расчет защищенного обогреваемого периметра применим',
 'data_type':'boolean','role':'intermediate','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
 'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'}
})
addq({
 'id':'P_heated_protected','symbol':'P_prot','name_ru':'Обогреваемый периметр для выбранной схемы огнезащиты',
 'data_type':'number','role':'intermediate','physical_dimension':'length','canonical_unit':'m','allowed_units':['m','mm'],
 'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT','STANDARD_TABLE','GEOMETRY_ENGINE_RESULT','USER_INPUT'],'override_policy':'forbidden'}
})
addq({
 'id':'sp554_protected_table1_perimeter_trace','symbol':None,'name_ru':'Трассировка защищенного обогреваемого периметра по таблице 1',
 'data_type':'object','role':'trace','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
 'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT','GEOMETRY_ENGINE_RESULT'],'override_policy':'forbidden'}
})
addq({
 'id':'delta_pr_protected','symbol':'δ_pr,prot','name_ru':'Приведенная толщина металла для выбранной схемы огнезащиты',
 'data_type':'number','role':'intermediate','physical_dimension':'length','canonical_unit':'mm','allowed_units':['mm','m'],
 'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'}
})

# Unprotected Table-1 domain becomes an automatic-geometry gate with manual fallback.
a=ns['SP554_A_HEATED_PERIMETER_TABLE1']
a['title']='Автоматический обогреваемый периметр без огнезащиты — область таблицы 1'
a['question']='Можно ли определить P автоматически из выбранного сечения и 3/4-сторонней схемы обогрева?'
a['notes']={
 'engineering_meaning':'Checks whether the selected normalized section has an explicit FIRE-UI1.9 SP554 Table-1 mapping. Unprotected steel uses the steel-contour basis.',
 'limitations':'Unsupported/built-up/arbitrary geometry is not approximated; manual P is requested.',
 'normative_warning':'Exposure side count and protection geometry are separate inputs.'
}
# custom executor owns this output; retain the existing produced quantity.
a.pop('check_condition',None); a.pop('result_quantity_id',None)

c=ns['SP554_C_HEATED_PERIMETER_TABLE1']
c['title']='Обогреваемый периметр P без огнезащиты — таблица 1'
c['produces']=[{'quantity_id':'P_heated','required':True,'binding_role':'output'},{'quantity_id':'sp554_table1_perimeter_trace','required':True,'binding_role':'output'}]
c['notes']={
 'engineering_meaning':'Automatic unprotected steel heated perimeter from SP554 Table 1. The unprotected basis is the steel contour.',
 'limitations':'Only explicit mapped section families execute automatically; otherwise use the manual P node.',
 'normative_warning':'For I/channel rows: contour 4 sides = 4B+2D-2t; contour 3 sides = 3B+2D-2t.'
}
c.pop('calculation_spec',None)

manual={
 'id':'SP554_I_HEATED_PERIMETER_MANUAL','node_type':'input','owner_standard_id':'SP554_2026',
 'title':'Обогреваемый периметр P — ручной ввод',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'table','section':'12','clause':'12.2','table_ref':'1'}],
 'consumes':[],'produces':[{'quantity_id':'P_heated','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Fail-closed fallback when automatic Table-1 geometry mapping is unavailable.','limitations':'User must provide the actual heated perimeter for the selected 3/4-sided exposure.','normative_warning':'Do not enter total steel boundary unless it is actually exposed.'},
 'input_spec':{'input_method':'user_number','required':True,'user_prompt':'Обогреваемый периметр P, м','allow_default_without_confirmation':False}
}
addn(manual)

# Existing false branch becomes manual fallback; detach the old terminal result.
for edge in g['edges']:
    if edge['from_node_id']=='SP554_A_HEATED_PERIMETER_TABLE1' and edge.get('condition',{}).get('value') is False:
        edge['to_node_id']='SP554_I_HEATED_PERIMETER_MANUAL'
        edge['label']='automatic Table-1 mapping unavailable -> manual P'
adde({'id':'FIRE_UI19_E_MANUAL_UNPROTECTED_P_TO_DELTA','from_node_id':'SP554_I_HEATED_PERIMETER_MANUAL','to_node_id':'SP554_C_DELTA_PR_12_2','edge_type':'control','label':'manual unprotected P -> reduced thickness','condition':None,'quantity_ids':['P_heated']})

# Protected perimeter-mode authoring and automatic/manual Table-1 matrix.
addn({
 'id':'SP554_D_PROTECTION_PERIMETER_MODE','node_type':'decision','owner_standard_id':'SP554_2026',
 'title':'Схема выполнения огнезащиты',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'table','section':'12','clause':'12.2','table_ref':'1'}],
 'consumes':[],'produces':[{'quantity_id':'fire_protection_perimeter_mode','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Selects the Table-1 protected perimeter column independently of heated-side count.','limitations':None,'normative_warning':'This is the geometry of the fire protection, not the steel section family.'},
 'question':'Как выполнена огнезащита?','decision_quantity_id':'fire_protection_perimeter_mode',
 'options':[{'value':'contour','label':'По контуру сечения','description':'Огнезащита повторяет контур профиля.'},{'value':'box','label':'В виде короба','description':'Огнезащита образует внешний короб.'}]
})
addn({
 'id':'SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1','node_type':'applicability_check','owner_standard_id':'SP554_2026',
 'title':'Автоматический защищенный обогреваемый периметр — область таблицы 1',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'table','section':'12','clause':'12.2','table_ref':'1'}],
 'consumes':[{'quantity_id':'heated_exposure_configuration','required':True,'binding_role':'input'},{'quantity_id':'fire_protection_perimeter_mode','required':True,'binding_role':'input'},{'quantity_id':'section_geometry_2d_normalized','required':True,'binding_role':'input'},{'quantity_id':'section_family','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'sp554_protected_perimeter_domain_ok','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Checks whether Table 1 can calculate the selected contour/box protected perimeter automatically.','limitations':'Unsupported geometry falls back to manual protected P.','normative_warning':'No bounding-box approximation is applied to unmapped section families.'}
})
addn({
 'id':'SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1','node_type':'calculation','owner_standard_id':'SP554_2026',
 'title':'Обогреваемый периметр P с огнезащитой — таблица 1',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'table','section':'12','clause':'12.2','table_ref':'1'},{'standard_id':'SP554_2026','reference_kind':'formula','section':'12','clause':'12.2','formula_ref':'Table 1 protected perimeter expressions — geometric execution'}],
 'consumes':[{'quantity_id':'section_geometry_2d_normalized','required':True,'binding_role':'input'},{'quantity_id':'section_family','required':True,'binding_role':'input'},{'quantity_id':'heated_exposure_configuration','required':True,'binding_role':'input'},{'quantity_id':'fire_protection_perimeter_mode','required':True,'binding_role':'input'},{'quantity_id':'sp554_protected_perimeter_domain_ok','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'P_heated_protected','required':True,'binding_role':'output'},{'quantity_id':'sp554_protected_table1_perimeter_trace','required':True,'binding_role':'output'}],
 'applicability':{'type':'comparison','quantity_id':'sp554_protected_perimeter_domain_ok','operator':'eq','value':True},
 'notes':{'engineering_meaning':'Computes protected P from the exact selected Table-1 contour/box column and 3/4-sided exposure.','limitations':'Requires an explicit mapped section family.','normative_warning':'Contour and box are distinct thermal geometries and must not share one P silently.'}
})
addn({
 'id':'SP554_I_PROTECTED_HEATED_PERIMETER_MANUAL','node_type':'input','owner_standard_id':'SP554_2026',
 'title':'Обогреваемый периметр с огнезащитой — ручной ввод',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'table','section':'12','clause':'12.2','table_ref':'1'}],
 'consumes':[],'produces':[{'quantity_id':'P_heated_protected','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Manual protected P fallback for section/protection geometries without an explicit automatic Table-1 mapping.','limitations':'The entered P must correspond to the selected contour/box protection and 3/4-sided exposure.','normative_warning':'No automatic geometry approximation is applied.'},
 'input_spec':{'input_method':'user_number','required':True,'user_prompt':'Обогреваемый периметр с огнезащитой P, м','allow_default_without_confirmation':False}
})
addn({
 'id':'SP554_C_DELTA_PR_PROTECTED_12_2','node_type':'calculation','owner_standard_id':'SP554_2026',
 'title':'Приведенная толщина металла для выбранной огнезащиты по (12.2)',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'formula','section':'12','clause':'12.2','formula_ref':'(12.2)'}],
 'consumes':[{'quantity_id':'A_gross','required':True,'binding_role':'input'},{'quantity_id':'P_heated_protected','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'delta_pr_protected','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Protected-route A/P using the Table-1 perimeter for the selected contour/box fire-protection geometry.','limitations':None,'normative_warning':'Protected 12.5/12.10 must consume this quantity, not the unprotected contour delta_pr.'},
 'calculation_spec':{'formula_type':'simple','formula_latex':'\\delta_{pr,prot}=A/P_{prot}','expression':'A_mm2/(P_m*1000)','expression_language':'expr_v1','bindings':[{'variable':'A_mm2','quantity_id':'A_gross'},{'variable':'P_m','quantity_id':'P_heated_protected'}],'rounding':{'mode':'none'}}
})

# Route protection authoring through the perimeter matrix before joints/product-data branches.
for edge in g['edges']:
    if edge['id']=='E0049':
        edge['to_node_id']='SP554_D_PROTECTION_PERIMETER_MODE'
        edge['label']='selected protection -> Table 1 perimeter geometry'
adde({'id':'FIRE_UI19_E_PROT_MODE_TO_DOMAIN','from_node_id':'SP554_D_PROTECTION_PERIMETER_MODE','to_node_id':'SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1','edge_type':'control','label':'protected perimeter mode -> automatic-domain check','condition':None,'quantity_ids':['fire_protection_perimeter_mode']})
adde({'id':'FIRE_UI19_E_PROT_DOMAIN_AUTO','from_node_id':'SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1','to_node_id':'SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1','edge_type':'branch','label':'automatic protected Table-1 mapping','condition':{'type':'comparison','quantity_id':'sp554_protected_perimeter_domain_ok','operator':'eq','value':True},'quantity_ids':['sp554_protected_perimeter_domain_ok']})
adde({'id':'FIRE_UI19_E_PROT_DOMAIN_MANUAL','from_node_id':'SP554_A_PROTECTED_HEATED_PERIMETER_TABLE1','to_node_id':'SP554_I_PROTECTED_HEATED_PERIMETER_MANUAL','edge_type':'branch','label':'manual protected perimeter fallback','condition':{'type':'comparison','quantity_id':'sp554_protected_perimeter_domain_ok','operator':'eq','value':False},'quantity_ids':['sp554_protected_perimeter_domain_ok']})
adde({'id':'FIRE_UI19_E_PROT_AUTO_TO_DELTA','from_node_id':'SP554_C_PROTECTED_HEATED_PERIMETER_TABLE1','to_node_id':'SP554_C_DELTA_PR_PROTECTED_12_2','edge_type':'control','label':'protected P -> protected reduced thickness','condition':None,'quantity_ids':['P_heated_protected']})
adde({'id':'FIRE_UI19_E_PROT_MANUAL_TO_DELTA','from_node_id':'SP554_I_PROTECTED_HEATED_PERIMETER_MANUAL','to_node_id':'SP554_C_DELTA_PR_PROTECTED_12_2','edge_type':'control','label':'manual protected P -> protected reduced thickness','condition':None,'quantity_ids':['P_heated_protected']})
adde({'id':'FIRE_UI19_E_PROT_DELTA_TO_JOINTS','from_node_id':'SP554_C_DELTA_PR_PROTECTED_12_2','to_node_id':'SP554_D_JOINTS','edge_type':'control','label':'protected reduced thickness resolved -> joints/protection data','condition':None,'quantity_ids':['delta_pr_protected']})

# Protected thermal/product routes consume the protected A/P quantity.
protected_nodes=['SP554_C_12_5_1D_PERFORMANCE_DATASET','SP554_C_12_10_DOMAIN','SP554_C_12_10_MINIMUM_THICKNESS','SP554_C_12_10_PROTECTED_TIME']
for nid in protected_nodes:
    node=ns[nid]
    for b in node.get('consumes',[]):
        if b.get('quantity_id')=='delta_pr': b['quantity_id']='delta_pr_protected'
    spec=node.get('calculation_spec') or {}
    for b in spec.get('bindings',[]):
        if b.get('quantity_id')=='delta_pr': b['quantity_id']='delta_pr_protected'

annex=ns['SP554_C_ANNEX_A_SCHEDULE']
for b in annex.get('consumes',[]):
    if b.get('quantity_id')=='P_heated': b['quantity_id']='P_heated_protected'
    elif b.get('quantity_id')=='delta_pr': b['quantity_id']='delta_pr_protected'
for b in (annex.get('calculation_spec') or {}).get('bindings',[]):
    if b.get('quantity_id')=='P_heated': b['quantity_id']='P_heated_protected'
    elif b.get('quantity_id')=='delta_pr': b['quantity_id']='delta_pr_protected'

# The thermal workflow is sequential here: reduced thickness must open the method selector.
if 'E0037' in es:
    es['E0037']['edge_type']='control'
    es['E0037']['label']='unprotected reduced thickness -> heating method'

# Clarify existing unprotected delta semantics.
ns['SP554_C_DELTA_PR_12_2']['title']='Приведенная толщина металла без огнезащиты по (12.2)'
ns['SP554_C_DELTA_PR_12_2'].setdefault('notes',{})['engineering_meaning']='Unprotected A/P using the steel-contour heated perimeter for the selected 3/4-sided exposure.'

# Release identity.
g['graph_id']='sp16_sp554_dag_v0-3-55_fire_ui19_sp554_table1_heated_perimeter_matrix'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.55 — FIRE-UI1.9 SP554 Table 1 heated-perimeter matrix'
g['description']='Cumulative v0.3.55 over FIRE-UI1.8: separates heated-side count from fire-protection geometry, calculates unprotected/contour/box heated perimeter from SP554 Table 1, maintains separate protected reduced thickness, and fails closed to manual P for unmapped geometry.'
meta=g.setdefault('metadata',{})
meta['release_stage']='v0.52_fire_ui19_sp554_table1_heated_perimeter_matrix_r1'
meta['parent_graph_id']='sp16_sp554_dag_v0-3-54_fire_ui18_fire_d2_to_d3_handoff_hotfix'
meta['fire_ui19_table1_perimeter_matrix']=True
meta['fire_ui19_protected_delta_separated']=True
meta['fire_ui19_unmapped_geometry_manual_fallback']=True

OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
