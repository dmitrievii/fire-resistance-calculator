from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.57_fire_ui21_selector_hardening_qy_t_lock.json'
OUT=ROOT/'normative_graph/dag_v0.3.58_fire_ui22_routing_protection_library_hotfix.json'
RELEASE='v0.55_fire_ui22_routing_protection_library_hotfix_r1'

g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}
ns={n['id']:n for n in g['nodes']}


def add_quantity(q):
    if q['id'] in qs:
        return qs[q['id']]
    g['quantities'].append(q); qs[q['id']]=q; return q

def q_enum(qid,name,values,role='decision_state'):
    return add_quantity({
      'id':qid,'symbol':None,'name_ru':name,'data_type':'enum','role':role,
      'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
      'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'forbidden'},
      'enum_values':[{'value':v,'label':lab} for v,lab in values],
    })

def q_num(qid,symbol,name,unit,role='input',source='USER_INPUT'):
    dim={'kg/m3':'density','%':'percent','1':'dimensionless','W/(m*K)':'thermal_conductivity','W/(m*K2)':'thermal_conductivity_temperature_coefficient','J/(kg*K)':'specific_heat_capacity','J/(kg*K2)':'specific_heat_capacity_temperature_coefficient'}.get(unit)
    return add_quantity({
      'id':qid,'symbol':symbol,'name_ru':name,'data_type':'number','role':role,
      'physical_dimension':dim,'canonical_unit':unit,'allowed_units':[unit],
      'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'},
    })

def q_obj(qid,name,role='intermediate',source='FORMULA_RESULT'):
    return add_quantity({
      'id':qid,'symbol':None,'name_ru':name,'data_type':'object','role':role,
      'physical_dimension':None,'canonical_unit':None,'allowed_units':[],
      'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'},
    })

# ---------------------------------------------------------------------------
# Routing continuity: gamma_e output, 9.2.3 and 9.2.6 decision-first nodes.
# ---------------------------------------------------------------------------
# The calculated gamma_e output had only data edges; guided navigation needs an
# explicit continuation into the independent Appendix-B compression selector.
if not any(e['from_node_id']=='SP554_C_GAMMAE_OUTPUT' and e['to_node_id']=='SP554_FIRE_UI17_C_TCR_COMPRESSION' and e['edge_type'] in ('control','branch','handoff') for e in g['edges']):
    g['edges'].append({
      'id':'UI22_E_GAMMAE_NAV','from_node_id':'SP554_C_GAMMAE_OUTPUT','to_node_id':'SP554_FIRE_UI17_C_TCR_COMPRESSION',
      'edge_type':'control','label':'γe resolved -> independent Appendix-B critical-temperature selector','condition':None,
      'quantity_ids':['gamma_E_required']
    })

# FIRE-UI2.0 removed obsolete aggregate inputs but accidentally orphaned their
# replacement decision nodes. Restore ordinary guided control edges.
if not any(e['to_node_id']=='SP16_D_M_RULE' for e in g['edges']):
    g['edges'].append({
      'id':'UI22_E_923_ENTRY','from_node_id':'SP554_I_NM_CONTEXT','to_node_id':'SP16_D_M_RULE','edge_type':'branch',
      'label':'SP16 9.2.3 moment rule','condition':{'type':'comparison','quantity_id':'stress_state','operator':'eq','value':'compression_plus_bending'},
      'quantity_ids':[]
    })
if not any(e['to_node_id']=='SP16_D_C_MOMENT_RULE' for e in g['edges']):
    g['edges'].append({
      'id':'UI22_E_926_ENTRY','from_node_id':'SP16_D_C_ROUTE_MODE','to_node_id':'SP16_D_C_MOMENT_RULE','edge_type':'branch',
      'label':'ordinary 9.2.5 -> 9.2.6 moment rule','condition':{'type':'comparison','quantity_id':'sp16_c_route_mode','operator':'eq','value':'standard_9_2_5'},
      'quantity_ids':[]
    })

# Alternative 9.2.3 M producers are mutually exclusive. Make that explicit so
# M_11_3 dependency resolution is deterministic.
producer_rules={
 'SP16_C_M_CONST_FRAME':'constant_frame_column',
 'SP16_C_M_STEPPED':'stepped_column',
 'SP16_C_M_FIXED_FREE':'fixed_free',
 'SP16_C_M_COMPRESSED_CHORD':'compressed_chord_off_node_load',
 'SP16_C_M_TABLE20':'pin_pin_monosymmetric_table20',
}
for nid,val in producer_rules.items():
    if nid in ns:
        ns[nid]['applicability']={'type':'comparison','quantity_id':'sp16_moment_rule','operator':'eq','value':val}

for nid in ('SP554_C_E_11_3','SP554_C_M_11_3','SP554_C_11_3','SP554_K_MEF_GT20'):
    if nid in ns:
        ns[nid]['applicability']={'type':'comparison','quantity_id':'stress_state','operator':'eq','value':'compression_plus_bending'}

# ---------------------------------------------------------------------------
# Post-unprotected result: calculation of Rfact is not the end of the session.
# Allow protection design independently of PASS/FAIL against Rreq.
# ---------------------------------------------------------------------------
q_enum('unprotected_post_action','Дальнейшее действие после расчёта незащищённой конструкции',[
 ('check_requirement','Проверить относительно Rreq'),
 ('design_fire_protection','Перейти к расчёту огнезащиты'),
 ('finish_unprotected','Завершить без расчёта огнезащиты'),
])
post_node={
 'id':'SP554_D_AFTER_UNPROTECTED','node_type':'decision','owner_standard_id':'SP554_2026',
 'title':'Что делать после расчёта фактического предела без огнезащиты?',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'5','clause':'5.3'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.10'}],
 'consumes':[{'quantity_id':'unprotected_fire_resistance_min','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'unprotected_post_action','required':True,'binding_role':'output'}],
 'applicability':None,
 'notes':{
   'engineering_meaning':'The calculated unprotected fire-resistance time is a stage result. The engineer may compare it with Rreq, continue to fire-protection design, or finish the unprotected study.',
   'limitations':'Entering fire-protection design does not require intentionally failing the unprotected Rreq check.',
   'normative_warning':None,
 },
 'question':'Что требуется сделать дальше?',
 'decision_quantity_id':'unprotected_post_action',
 'options':[
   {'value':'check_requirement','label':'Проверить соответствие требуемому пределу Rreq','description':'Rreq будет использован только для проверки соответствия.'},
   {'value':'design_fire_protection','label':'Перейти к расчёту огнезащиты','description':'Продолжить с уже рассчитанными Tcr, геометрией и Rfact без повторного механического расчёта.'},
   {'value':'finish_unprotected','label':'Завершить расчёт без огнезащиты','description':'Сохранить фактический предел без проверки/проектирования огнезащиты.'},
 ]
}
if post_node['id'] not in ns:
    g['nodes'].append(post_node); ns[post_node['id']]=post_node

finish_node={
 'id':'SP554_R_UNPROTECTED_CALCULATION_COMPLETE','node_type':'result','owner_standard_id':'SP554_2026',
 'title':'Расчёт фактического предела без огнезащиты завершён',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'13','clause':'13.2'}],
 'consumes':[{'quantity_id':'critical_temperature_c','required':True,'binding_role':'input'},{'quantity_id':'unprotected_fire_resistance_min','required':True,'binding_role':'input'}],
 'produces':[],'applicability':{'type':'comparison','quantity_id':'unprotected_post_action','operator':'eq','value':'finish_unprotected'},
 'notes':{'engineering_meaning':'Terminal result without an asserted external Rreq comparison.','limitations':None,'normative_warning':'No PASS/FAIL against a required class is claimed.'},
 'result_quantity_ids':['critical_temperature_c','unprotected_fire_resistance_min'],'result_kind':'fire_resistance_time'
}
if finish_node['id'] not in ns:
    g['nodes'].append(finish_node); ns[finish_node['id']]=finish_node

# Replace the unconditional R_UNPROTECTED -> compliance transition.
g['edges']=[e for e in g['edges'] if not (e['from_node_id']=='SP554_R_UNPROTECTED' and e['to_node_id']=='SP554_Q_UNPROTECTED')]
new_post_edges=[
 {'id':'UI22_E_POST_R','from_node_id':'SP554_R_UNPROTECTED','to_node_id':'SP554_D_AFTER_UNPROTECTED','edge_type':'control','label':'Rfact available','condition':None,'quantity_ids':['unprotected_fire_resistance_min']},
 {'id':'UI22_E_POST_CHECK','from_node_id':'SP554_D_AFTER_UNPROTECTED','to_node_id':'SP554_Q_UNPROTECTED','edge_type':'branch','label':'Проверить Rreq','condition':{'type':'comparison','quantity_id':'unprotected_post_action','operator':'eq','value':'check_requirement'},'quantity_ids':[]},
 {'id':'UI22_E_POST_PROTECTION','from_node_id':'SP554_D_AFTER_UNPROTECTED','to_node_id':'SP554_I_PROTECTION','edge_type':'branch','label':'Перейти к огнезащите','condition':{'type':'comparison','quantity_id':'unprotected_post_action','operator':'eq','value':'design_fire_protection'},'quantity_ids':[]},
 {'id':'UI22_E_POST_FINISH','from_node_id':'SP554_D_AFTER_UNPROTECTED','to_node_id':'SP554_R_UNPROTECTED_CALCULATION_COMPLETE','edge_type':'branch','label':'Завершить без огнезащиты','condition':{'type':'comparison','quantity_id':'unprotected_post_action','operator':'eq','value':'finish_unprotected'},'quantity_ids':[]},
]
existing_edge_ids={e['id'] for e in g['edges']}
for e in new_post_edges:
    if e['id'] not in existing_edge_ids: g['edges'].append(e)

# If Rreq check passes, allow optional protection design instead of forcing the
# terminal final-unprotected node. Reuse the same post-result choice by sending
# the designation calculation back to the decision.
for e in g['edges']:
    if e['from_node_id']=='SP554_C_R_DESIGNATION_UNPROTECTED' and e['to_node_id']=='SP554_R_FINAL_UNPROTECTED':
        e['to_node_id']='SP554_D_AFTER_UNPROTECTED'; e['edge_type']='control'; e['label']='R designation ready -> choose next action'; e['quantity_ids']=['fire_resistance_designation']

# ---------------------------------------------------------------------------
# STO ARSS thermal-property library + manual property input for SP554 12.5.
# The source table uses t in kelvins (valid t >= 273 K). Mineral-wool source
# density is 80-100 kg/m3; project/UI fixed value is explicitly 100 kg/m3 by
# user decision, while the source range remains in provenance.
# ---------------------------------------------------------------------------
q_enum('protection_12_5_material_source','Источник теплофизических свойств огнезащиты',[
 ('sto_arss_library','Библиотека СТО АРСС 11251254.001-018-03'),
 ('manual_properties','Ввести свойства вручную'),
])
q_enum('protection_arss_material_id','Материал огнезащиты по СТО АРСС',[
 ('cement_sand_plaster','Цементно-песчаная штукатурка'),
 ('dry_gypsum_plaster','Сухая гипсовая штукатурка (ГКЛ/ГВЛ/КНАУФ-Файерборд)'),
 ('cellular_foam_concrete','Ячеистый бетон / пенобетон'),
 ('mineral_wool_board','Минераловатные плиты'),
])
q_num('protection_material_density_kg_m3','ρ_f','Плотность огнезащиты','kg/m3',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_moisture_percent','W','Начальная влажность огнезащиты','%',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_emissivity','ε_f','Степень черноты поверхности огнезащиты','1',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_lambda_A','A','Коэффициент A теплопроводности λ=A+B·t','W/(m*K)',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_lambda_B','B','Коэффициент B теплопроводности λ=A+B·t','W/(m*K2)',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_cp_C','C','Коэффициент C теплоёмкости c=C+D·t','J/(kg*K)',role='intermediate',source='FORMULA_RESULT')
q_num('protection_material_cp_D','D','Коэффициент D теплоёмкости c=C+D·t','J/(kg*K2)',role='intermediate',source='FORMULA_RESULT')
q_enum('protection_material_temperature_basis','Температурная шкала коэффициентов A/B/C/D',[
 ('K','Кельвин (K)'),('degC','Градусы Цельсия (°C)')
],role='intermediate')
q_obj('protection_material_provenance','Источник теплофизических свойств огнезащиты')
# Existing model-parameter object remains the downstream canonical quantity.
if 'protection_12_5_model_parameters' in qs:
    qs['protection_12_5_model_parameters']['role']='intermediate'
    qs['protection_12_5_model_parameters']['source_policy']={'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'}

# Inline source-traced table.
if not any(ds['id']=='STO_ARSS_11251254_001_018_03_THERMAL_PROPERTIES' for ds in g['datasets']):
    g['datasets'].append({
      'id':'STO_ARSS_11251254_001_018_03_THERMAL_PROPERTIES','dataset_type':'reference_material_properties','owner_standard_id':'STO_ARSS_11251254_001_018_03',
      'title':'СТО АРСС 11251254.001-018-03 — теплофизические характеристики огнезащитных материалов',
      'normative_refs':[{'standard_id':'STO_ARSS_11251254_001_018_03','reference_kind':'table','quote_or_note':'Теплофизические характеристики огнезащитных материалов; λ_t=A+B·t, c_t=C+D·t; зависимости справедливы для t>=273 K.'}],
      'axes':['material_id'],'output_quantity_ids':['protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis'],
      'interpolation':{'method':'none','extrapolation':'forbidden'},
      'storage':{'mode':'inline','rows':[
        {'material_id':'cement_sand_plaster','label_ru':'Цементно-песчаная штукатурка','density_kg_m3':1930.0,'source_density_range_kg_m3':None,'moisture_percent':2.0,'emissivity':0.87,'lambda_A':0.96,'lambda_B':-0.00044,'cp_C':598.0,'cp_D':0.63,'temperature_basis':'K','valid_min_temperature_k':273.0},
        {'material_id':'dry_gypsum_plaster','label_ru':'Сухая гипсовая штукатурка (ГКЛ/ГВЛ/КНАУФ-Файерборд)','density_kg_m3':900.0,'source_density_range_kg_m3':None,'moisture_percent':15.0,'emissivity':0.86,'lambda_A':0.135,'lambda_B':0.00035,'cp_C':849.0,'cp_D':0.59,'temperature_basis':'K','valid_min_temperature_k':273.0},
        {'material_id':'cellular_foam_concrete','label_ru':'Ячеистый бетон / пенобетон','density_kg_m3':600.0,'source_density_range_kg_m3':None,'moisture_percent':2.0,'emissivity':0.80,'lambda_A':0.041,'lambda_B':0.00019,'cp_C':748.0,'cp_D':0.63,'temperature_basis':'K','valid_min_temperature_k':273.0},
        {'material_id':'mineral_wool_board','label_ru':'Минераловатные плиты','density_kg_m3':100.0,'source_density_range_kg_m3':[80.0,100.0],'project_density_selection_kg_m3':100.0,'project_density_selection_basis':'user-fixed upper value for FIRE-UI2.2','moisture_percent':0.5,'emissivity':0.92,'lambda_A':-0.107,'lambda_B':0.00058,'cp_C':582.0,'cp_D':0.63,'temperature_basis':'K','valid_min_temperature_k':273.0},
      ]},
      'notes':'Source table coefficients retained literally in kelvin form. Mineral-wool source density range 80-100 kg/m3 is retained in provenance; active library value is fixed at 100 kg/m3 per project/user decision.'
    })

source_node={
 'id':'SP554_D_12_5_MATERIAL_SOURCE','node_type':'decision','owner_standard_id':'SP554_2026','title':'Источник свойств огнезащиты для модели 12.5',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'STO_ARSS_11251254_001_018_03','reference_kind':'table'}],
 'consumes':[],'produces':[{'quantity_id':'protection_12_5_material_source','required':True,'binding_role':'output'}],
 'applicability':{'type':'comparison','quantity_id':'protection_data_generation_method','operator':'eq','value':'thermal_model_12_5'},
 'notes':{'engineering_meaning':'Select source-traced STO ARSS thermal properties or author certified properties manually.','limitations':'STO ARSS library values do not waive the SP554 12.6 validation gate for a generated performance dataset.','normative_warning':'Do not mix coefficients expressed versus kelvin with a Celsius temperature variable.'},
 'question':'Откуда взять теплофизические свойства огнезащиты?','decision_quantity_id':'protection_12_5_material_source',
 'options':[{'value':'sto_arss_library','label':'Выбрать из библиотеки СТО АРСС','description':'Четыре source-traced материала из таблицы теплофизических характеристик.'},{'value':'manual_properties','label':'Ввести свойства вручную','description':'ρ, W, ε, A, B, C, D и температурная шкала.'}]
}
material_decision={
 'id':'SP554_D_12_5_ARSS_MATERIAL','node_type':'decision','owner_standard_id':'STO_ARSS_11251254_001_018_03','title':'Огнезащитный материал — библиотека СТО АРСС',
 'normative_refs':[{'standard_id':'STO_ARSS_11251254_001_018_03','reference_kind':'table'}],
 'consumes':[],'produces':[{'quantity_id':'protection_arss_material_id','required':True,'binding_role':'output'}],
 'applicability':{'type':'comparison','quantity_id':'protection_12_5_material_source','operator':'eq','value':'sto_arss_library'},
 'notes':{'engineering_meaning':'Direct selection of the material row; no interpolation between materials.','limitations':'Mineral-wool density uses the project-fixed 100 kg/m3 value while retaining the printed 80-100 kg/m3 range in provenance.','normative_warning':'A/B/C/D are defined against absolute temperature t in kelvins, t>=273 K.'},
 'question':'Выберите материал огнезащиты','decision_quantity_id':'protection_arss_material_id',
 'options':[
   {'value':'cement_sand_plaster','label':'Цементно-песчаная штукатурка','description':'ρ=1930 кг/м³; W=2%; ε=0,87.'},
   {'value':'dry_gypsum_plaster','label':'Сухая гипсовая штукатурка (ГКЛ/ГВЛ/КНАУФ-Файерборд)','description':'ρ=900 кг/м³; W=15%; ε=0,86.'},
   {'value':'cellular_foam_concrete','label':'Ячеистый бетон / пенобетон','description':'ρ=600 кг/м³; W=2%; ε=0,80.'},
   {'value':'mineral_wool_board','label':'Минераловатные плиты','description':'ρ=100 кг/м³ (в СТО указан диапазон 80–100); W=0,5%; ε=0,92.'},
 ]
}
lookup_node={
 'id':'SP554_C_12_5_ARSS_MATERIAL_LOOKUP','node_type':'lookup','owner_standard_id':'STO_ARSS_11251254_001_018_03','title':'Свойства выбранного материала по СТО АРСС',
 'normative_refs':[{'standard_id':'STO_ARSS_11251254_001_018_03','reference_kind':'table'}],
 'consumes':[{'quantity_id':'protection_arss_material_id','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':q,'required':True,'binding_role':'output'} for q in ['protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis']],
 'applicability':{'type':'comparison','quantity_id':'protection_12_5_material_source','operator':'eq','value':'sto_arss_library'},
 'notes':{'engineering_meaning':'Exact material-row lookup.','limitations':'No interpolation/extrapolation.','normative_warning':'Kelvin basis is preserved explicitly.'},
 'lookup_spec':{
   'dataset_id':'STO_ARSS_11251254_001_018_03_THERMAL_PROPERTIES',
   'selector_bindings':[{'quantity_id':'protection_arss_material_id','dataset_field':'material_id'}],
   'output_bindings':[
     {'quantity_id':'protection_material_density_kg_m3','dataset_field':'density_kg_m3'},
     {'quantity_id':'protection_material_moisture_percent','dataset_field':'moisture_percent'},
     {'quantity_id':'protection_material_emissivity','dataset_field':'emissivity'},
     {'quantity_id':'protection_material_lambda_A','dataset_field':'lambda_A'},
     {'quantity_id':'protection_material_lambda_B','dataset_field':'lambda_B'},
     {'quantity_id':'protection_material_cp_C','dataset_field':'cp_C'},
     {'quantity_id':'protection_material_cp_D','dataset_field':'cp_D'},
     {'quantity_id':'protection_material_temperature_basis','dataset_field':'temperature_basis'},
   ],
   'interpolation':{'method':'none','extrapolation':'forbidden'}
 }
}
manual_node={
 'id':'SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES','node_type':'input','owner_standard_id':'SP554_2026','title':'Теплофизические свойства огнезащиты — ручной ввод',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'}],
 'consumes':[],'produces':[{'quantity_id':q,'required':True,'binding_role':'output'} for q in ['protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis']],
 'applicability':{'type':'comparison','quantity_id':'protection_12_5_material_source','operator':'eq','value':'manual_properties'},
 'notes':{'engineering_meaning':'Author certified/source-traced material coefficients for λ=A+B·t and c=C+D·t.','limitations':'The engineer must use the same temperature basis as the source coefficients.','normative_warning':'If the source coefficients use kelvin, select K; if they were identified directly versus °C, select °C.'},
 'input_spec':{'input_method':'user_fields','required':True,'user_prompt':'Введите ρ, W, ε, A, B, C, D и температурную шкалу коэффициентов.','allow_default_without_confirmation':False}
}
build_node={
 'id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','node_type':'calculation','owner_standard_id':'SP554_2026','title':'Сформировать source-traced модель теплофизических свойств 12.5',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'}],
 'consumes':[{'quantity_id':q,'required':True,'binding_role':'input'} for q in ['protection_12_5_material_source','protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis']],
 'produces':[{'quantity_id':'protection_12_5_model_parameters','required':True,'binding_role':'output'},{'quantity_id':'protection_material_provenance','required':True,'binding_role':'output'}],
 'applicability':{'type':'comparison','quantity_id':'protection_data_generation_method','operator':'eq','value':'thermal_model_12_5'},
 'notes':{'engineering_meaning':'Internal object builder; the user never authors raw JSON model parameters.','limitations':'Thickness/discretization/generation-grid data remain separate because they are calculation-case data, not intrinsic material properties.','normative_warning':'Temperature basis is retained explicitly for correct A/B/C/D evaluation.'}
}
# Split the former raw model+grid object input: material properties are now
# engineered; the calculation grid stays an explicit imported/source-traced object.
grid_node={
 'id':'SP554_I_12_5_GENERATION_GRID','node_type':'input','owner_standard_id':'SP554_2026','title':'Расчётная сетка/валидационные данные модели 12.5',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.5'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.6'}],
 'consumes':[],'produces':[{'quantity_id':'protection_12_5_generation_grid','required':True,'binding_role':'output'}],
 'applicability':{'type':'comparison','quantity_id':'protection_data_generation_method','operator':'eq','value':'thermal_model_12_5'},
 'notes':{'engineering_meaning':'Source-traced calculation grid and mandatory 12.6 validation evidence.','limitations':'FIRE-UI2.2 does not fabricate fire-test validation data from the material-property library.','normative_warning':'Library material properties do not bypass the 12.6 validation requirement.'},
 'input_spec':{'input_method':'imported_value','required':True,'user_prompt':'Передайте расчётную сетку и данные валидации 12.6.','allow_default_without_confirmation':False}
}
for n in [source_node,material_decision,lookup_node,manual_node,build_node,grid_node]:
    if n['id'] not in ns: g['nodes'].append(n); ns[n['id']]=n

# Remove obsolete raw object input from active graph and its touching edges.
old='SP554_I_12_5_MODEL_PARAMETERS'
g['nodes']=[n for n in g['nodes'] if n['id']!=old]
ns.pop(old,None)
g['edges']=[e for e in g['edges'] if e['from_node_id']!=old and e['to_node_id']!=old]
# Replace 12.5 branch edge from method selector.
for e in g['edges']:
    if e['from_node_id']=='SP554_D_PROTECTION_DATA_METHOD' and e.get('condition',{}).get('value')=='thermal_model_12_5' and e['to_node_id'] not in {'SP554_K_PROTECTION_SOURCE_12_5'}:
        e['to_node_id']='SP554_D_12_5_MATERIAL_SOURCE'; e['label']='Расчёт 12.5 — выбрать свойства материала'; e['quantity_ids']=[]

material_edges=[
 {'id':'UI22_E_MAT_LIB','from_node_id':'SP554_D_12_5_MATERIAL_SOURCE','to_node_id':'SP554_D_12_5_ARSS_MATERIAL','edge_type':'branch','label':'Библиотека СТО АРСС','condition':{'type':'comparison','quantity_id':'protection_12_5_material_source','operator':'eq','value':'sto_arss_library'},'quantity_ids':[]},
 {'id':'UI22_E_MAT_MAN','from_node_id':'SP554_D_12_5_MATERIAL_SOURCE','to_node_id':'SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES','edge_type':'branch','label':'Ручной ввод','condition':{'type':'comparison','quantity_id':'protection_12_5_material_source','operator':'eq','value':'manual_properties'},'quantity_ids':[]},
 {'id':'UI22_E_MAT_LOOKUP','from_node_id':'SP554_D_12_5_ARSS_MATERIAL','to_node_id':'SP554_C_12_5_ARSS_MATERIAL_LOOKUP','edge_type':'control','label':'точная строка СТО АРСС','condition':None,'quantity_ids':['protection_arss_material_id']},
 {'id':'UI22_E_MAT_LOOKUP_BUILD','from_node_id':'SP554_C_12_5_ARSS_MATERIAL_LOOKUP','to_node_id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','edge_type':'data','label':'библиотечные свойства','condition':None,'quantity_ids':['protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis']},
 {'id':'UI22_E_MAT_MAN_BUILD','from_node_id':'SP554_I_12_5_MANUAL_MATERIAL_PROPERTIES','to_node_id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','edge_type':'data','label':'ручные свойства','condition':None,'quantity_ids':['protection_material_density_kg_m3','protection_material_moisture_percent','protection_material_emissivity','protection_material_lambda_A','protection_material_lambda_B','protection_material_cp_C','protection_material_cp_D','protection_material_temperature_basis']},
 {'id':'UI22_E_MODEL_TO_GRID','from_node_id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','to_node_id':'SP554_I_12_5_GENERATION_GRID','edge_type':'control','label':'свойства готовы -> сетка/валидация','condition':None,'quantity_ids':['protection_12_5_model_parameters']},
 {'id':'UI22_E_GRID_TO_FDM','from_node_id':'SP554_I_12_5_GENERATION_GRID','to_node_id':'SP554_C_12_5_1D_PERFORMANCE_DATASET','edge_type':'data','label':'grid + 12.6 validation evidence','condition':None,'quantity_ids':['protection_12_5_generation_grid']},
 {'id':'UI22_E_MODEL_TO_FDM','from_node_id':'SP554_C_12_5_BUILD_MODEL_PARAMETERS','to_node_id':'SP554_C_12_5_1D_PERFORMANCE_DATASET','edge_type':'data','label':'material model','condition':None,'quantity_ids':['protection_12_5_model_parameters']},
]
edge_ids={e['id'] for e in g['edges']}
for e in material_edges:
    if e['id'] not in edge_ids: g['edges'].append(e)


# ---------------------------------------------------------------------------
# FIRE-UI2.2 closure hardening found during full-route audit.
# Rreq is a post-result/check input, not a prerequisite for starting the
# analytical route.  Direct protected-R calculation also must not require Rreq.
# ---------------------------------------------------------------------------
# Keep the external Rreq handoff as a dependency producer, but remove it from
# the primary navigation chain before Rfact exists.
for e in g['edges']:
    if e['from_node_id']=='SP554_D_PRODUCT_ROUTE' and e['to_node_id']=='SP554_H_REQUIRED_R' and e['id'] in {'E0006','E0007'}:
        e['to_node_id']='SP554_D_METHOD'
        e['label']=('Горячекатаное -> расчётный метод' if e['id']=='E0006' else 'Сварное -> расчётный метод')
        e['quantity_ids']=[]
g['edges']=[e for e in g['edges'] if e['id']!='E0010']

# Split 12.10 query-domain checks: the direct task needs only a documented
# matrix + delta_pr + Tcr + a given thickness; the inverse task additionally
# requires Rreq.
add_quantity({
  'id':'sp554_12_10_inverse_query_domain_ok','symbol':None,
  'name_ru':'Область применимости обратной задачи 12.10 подтверждена',
  'data_type':'boolean','role':'diagnostic','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
  'source_policy':{'primary_source_type':'FORMULA_RESULT','allowed_source_types':['FORMULA_RESULT'],'override_policy':'forbidden'},
})
if 'SP554_C_12_10_DOMAIN' in ns:
    n=ns['SP554_C_12_10_DOMAIN']
    n['title']='Область применимости прямой задачи 12.10'
    n['consumes']=[b for b in n['consumes'] if b['quantity_id']!='required_fire_resistance_min']
    n['applicability']={'type':'all_of','conditions':[
      {'type':'comparison','quantity_id':'protection_performance_dataset_ready','operator':'eq','value':True},
      {'type':'comparison','quantity_id':'protected_task_mode','operator':'eq','value':'verify_given_thickness'},
    ]}
    n['notes']['engineering_meaning']='Checks exact Tcr slice, reduced-thickness domain and the engineer-specified protection thickness for the direct 12.10 task.'
    n['notes']['limitations']='Direct Rfact calculation does not require Rreq. No critical-temperature interpolation or protection-thickness extrapolation.'
    n['calculation_spec']['formula_latex']='domain_{12.10,direct}=Q(D,\\delta_{pr},T_{cr},\\delta_f)'
    n['calculation_spec']['expression']='protected_query_domain_12_10_direct(dataset,delta_pr_mm,Tcrit,given_thickness_mm)'
    n['calculation_spec']['bindings']=[b for b in n['calculation_spec']['bindings'] if b['quantity_id']!='required_fire_resistance_min' and b['quantity_id']!='protected_task_mode']

inv_node={
 'id':'SP554_C_12_10_DOMAIN_INVERSE','node_type':'calculation','owner_standard_id':'SP554_2026',
 'title':'Область применимости обратной задачи 12.10',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'formula','section':'12','clause':'12.10','formula_ref':'12.10 inverse query-domain execution'}],
 'consumes':[
   {'quantity_id':'protection_performance_dataset_normalized','required':True,'binding_role':'input'},
   {'quantity_id':'protection_performance_dataset_ready','required':True,'binding_role':'input'},
   {'quantity_id':'delta_pr_protected','required':True,'binding_role':'input'},
   {'quantity_id':'critical_temperature_c','required':True,'binding_role':'input'},
   {'quantity_id':'protected_task_mode','required':True,'binding_role':'input'},
   {'quantity_id':'required_fire_resistance_min','required':True,'binding_role':'input'},
 ],
 'produces':[{'quantity_id':'sp554_12_10_inverse_query_domain_ok','required':True,'binding_role':'output'}],
 'applicability':{'type':'all_of','conditions':[
   {'type':'comparison','quantity_id':'protection_performance_dataset_ready','operator':'eq','value':True},
   {'type':'comparison','quantity_id':'protected_task_mode','operator':'eq','value':'determine_minimum_thickness'},
 ]},
 'notes':{
   'engineering_meaning':'Checks exact Tcr slice, reduced-thickness domain and whether Rreq is reachable within the documented protection-thickness domain.',
   'limitations':'No extrapolation beyond the documented protection-thickness domain.',
   'normative_warning':'Rreq is required only for the inverse minimum-thickness task or a later compliance check.'
 },
 'calculation_spec':{
   'formula_type':'simple','formula_latex':'domain_{12.10,inverse}=Q(D,\\delta_{pr},T_{cr},R_{req})',
   'expression':'protected_query_domain_12_10_inverse(dataset,delta_pr_mm,Tcrit,required_time_min)','expression_language':'expr_v1',
   'bindings':[
     {'variable':'dataset','quantity_id':'protection_performance_dataset_normalized'},
     {'variable':'delta_pr_mm','quantity_id':'delta_pr_protected'},
     {'variable':'Tcrit','quantity_id':'critical_temperature_c'},
     {'variable':'required_time_min','quantity_id':'required_fire_resistance_min'},
   ],'rounding':{'mode':'none'}
 }
}
if inv_node['id'] not in ns:
    g['nodes'].append(inv_node); ns[inv_node['id']]=inv_node

# The mode decision now branches explicitly: direct -> thickness input -> direct
# domain; inverse -> inverse domain (which schedules Rreq only then).
for e in g['edges']:
    if e['id']=='E1165':
        e['to_node_id']='SP554_C_12_10_DOMAIN_INVERSE'; e['edge_type']='branch'; e['label']='Определить минимальную толщину'
        e['condition']={'type':'comparison','quantity_id':'protected_task_mode','operator':'eq','value':'determine_minimum_thickness'}; e['quantity_ids']=[]
# Direct domain must not feed inverse minimum-thickness calculation.
g['edges']=[e for e in g['edges'] if not (e['from_node_id']=='SP554_C_12_10_DOMAIN' and e['to_node_id']=='SP554_C_12_10_MINIMUM_THICKNESS')]
# Add inverse-domain data/control dependencies and outcome branches.
ui22_inverse_edges=[
 {'id':'UI22_E_NORM_TO_INV_DOMAIN','from_node_id':'SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET','to_node_id':'SP554_C_12_10_DOMAIN_INVERSE','edge_type':'data','label':'normalized dataset','condition':None,'quantity_ids':['protection_performance_dataset_normalized']},
 {'id':'UI22_E_INV_DOMAIN_OUT','from_node_id':'SP554_C_12_10_DOMAIN_INVERSE','to_node_id':'SP554_R_12_10_OUT_OF_DOMAIN','edge_type':'branch','label':'outside inverse domain','condition':{'type':'comparison','quantity_id':'sp554_12_10_inverse_query_domain_ok','operator':'eq','value':False},'quantity_ids':[]},
 {'id':'UI22_E_INV_DOMAIN_OK','from_node_id':'SP554_C_12_10_DOMAIN_INVERSE','to_node_id':'SP554_C_12_10_MINIMUM_THICKNESS','edge_type':'branch','label':'inverse domain confirmed','condition':{'type':'comparison','quantity_id':'sp554_12_10_inverse_query_domain_ok','operator':'eq','value':True},'quantity_ids':[]},
]
edge_ids={e['id'] for e in g['edges']}
for e in ui22_inverse_edges:
    if e['id'] not in edge_ids: g['edges'].append(e)
if 'SP554_C_12_10_MINIMUM_THICKNESS' in ns:
    n=ns['SP554_C_12_10_MINIMUM_THICKNESS']
    n['consumes']=[({**b,'quantity_id':'sp554_12_10_inverse_query_domain_ok'} if b['quantity_id']=='sp554_12_10_query_domain_ok' else b) for b in n['consumes']]
    n['applicability']={'type':'all_of','conditions':[
      {'type':'comparison','quantity_id':'protected_task_mode','operator':'eq','value':'determine_minimum_thickness'},
      {'type':'comparison','quantity_id':'sp554_12_10_inverse_query_domain_ok','operator':'eq','value':True},
    ]}

# Protected Rfact is also a stage result.  Let the engineer finish without
# asserting Rreq compliance, or request the Rreq check explicitly.
q_enum('protected_post_action','Дальнейшее действие после расчёта огнезащищённой конструкции',[
 ('check_requirement','Проверить относительно Rreq'),
 ('finish_protected','Завершить расчёт огнезащищённой конструкции без проверки Rreq'),
])
protected_post={
 'id':'SP554_D_AFTER_PROTECTED','node_type':'decision','owner_standard_id':'SP554_2026',
 'title':'Что делать после расчёта фактического предела с огнезащитой?',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'12','clause':'12.10'},{'standard_id':'SP554_2026','reference_kind':'clause','section':'13','clause':'13.2'}],
 'consumes':[{'quantity_id':'protected_fire_resistance_min','required':True,'binding_role':'input'},{'quantity_id':'protection_thickness_mm','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'protected_post_action','required':True,'binding_role':'output'}],
 'applicability':None,
 'notes':{'engineering_meaning':'Rfact with protection is a valid calculation result even before an external Rreq comparison.','limitations':None,'normative_warning':'Choose the compliance check only when Rreq and its provenance are available.'},
 'question':'Что требуется сделать дальше?', 'decision_quantity_id':'protected_post_action',
 'options':[
   {'value':'check_requirement','label':'Проверить соответствие требуемому пределу Rreq','description':'Запросить/использовать Rreq и выполнить проверку соответствия.'},
   {'value':'finish_protected','label':'Завершить без проверки Rreq','description':'Сохранить рассчитанный Rfact и толщину огнезащиты без утверждения PASS/FAIL.'},
 ]
}
if protected_post['id'] not in ns:
    g['nodes'].append(protected_post); ns[protected_post['id']]=protected_post
protected_finish={
 'id':'SP554_R_PROTECTED_CALCULATION_COMPLETE','node_type':'result','owner_standard_id':'SP554_2026',
 'title':'Расчёт фактического предела с огнезащитой завершён',
 'normative_refs':[{'standard_id':'SP554_2026','reference_kind':'clause','section':'13','clause':'13.2'}],
 'consumes':[{'quantity_id':'critical_temperature_c','required':True,'binding_role':'input'},{'quantity_id':'protected_fire_resistance_min','required':True,'binding_role':'input'},{'quantity_id':'protection_thickness_mm','required':True,'binding_role':'input'}],
 'produces':[],'applicability':{'type':'comparison','quantity_id':'protected_post_action','operator':'eq','value':'finish_protected'},
 'notes':{'engineering_meaning':'Terminal protected Rfact result without an external Rreq compliance assertion.','limitations':None,'normative_warning':'No PASS/FAIL against Rreq is claimed.'},
 'result_quantity_ids':['critical_temperature_c','protected_fire_resistance_min','protection_thickness_mm'],'result_kind':'fire_resistance_time'
}
if protected_finish['id'] not in ns:
    g['nodes'].append(protected_finish); ns[protected_finish['id']]=protected_finish
# Replace unconditional protected compliance transition.
g['edges']=[e for e in g['edges'] if not (e['from_node_id']=='SP554_R_PROTECTED' and e['to_node_id']=='SP554_Q_PROTECTED')]
post_protected_edges=[
 {'id':'UI22_E_POST_PROTECTED','from_node_id':'SP554_R_PROTECTED','to_node_id':'SP554_D_AFTER_PROTECTED','edge_type':'control','label':'protected Rfact available','condition':None,'quantity_ids':['protected_fire_resistance_min','protection_thickness_mm']},
 {'id':'UI22_E_POST_PROTECTED_CHECK','from_node_id':'SP554_D_AFTER_PROTECTED','to_node_id':'SP554_Q_PROTECTED','edge_type':'branch','label':'Проверить Rreq','condition':{'type':'comparison','quantity_id':'protected_post_action','operator':'eq','value':'check_requirement'},'quantity_ids':[]},
 {'id':'UI22_E_POST_PROTECTED_FINISH','from_node_id':'SP554_D_AFTER_PROTECTED','to_node_id':'SP554_R_PROTECTED_CALCULATION_COMPLETE','edge_type':'branch','label':'Завершить без проверки Rreq','condition':{'type':'comparison','quantity_id':'protected_post_action','operator':'eq','value':'finish_protected'},'quantity_ids':[]},
]
edge_ids={e['id'] for e in g['edges']}
for e in post_protected_edges:
    if e['id'] not in edge_ids: g['edges'].append(e)

# Remove the last presentation-policy-only navigation island: weakening with
# holes must be structurally connected in the DAG itself, not only by frontend
# overrides.
for e in g['edges']:
    if e['id']=='E0971' and e['from_node_id']=='SP16_D_WEAKENING':
        e['to_node_id']='SP554_D_NET_PROPERTY_REDUCTION'
        e['label']='Ослабление есть -> выбрать политику I/W нетто'
weakening_edges=[
 {'id':'UI22_E_NET_AREA_ONLY','from_node_id':'SP554_D_NET_PROPERTY_REDUCTION','to_node_id':'SP554_G_NET_SECTION_PROPERTIES','edge_type':'branch','label':'Уменьшить только A','condition':{'type':'comparison','quantity_id':'net_property_reduction_mode','operator':'eq','value':'area_only_keep_gross'},'quantity_ids':[]},
 {'id':'UI22_E_NET_MANUAL','from_node_id':'SP554_D_NET_PROPERTY_REDUCTION','to_node_id':'SP554_I_NET_SECTION_MANUAL_PROPERTIES','edge_type':'branch','label':'Ввести net-характеристики','condition':{'type':'comparison','quantity_id':'net_property_reduction_mode','operator':'eq','value':'manual_net_properties'},'quantity_ids':[]},
 {'id':'UI22_E_NET_MANUAL_TO_RESOLVER','from_node_id':'SP554_I_NET_SECTION_MANUAL_PROPERTIES','to_node_id':'SP554_G_NET_SECTION_PROPERTIES','edge_type':'control','label':'net-характеристики введены','condition':None,'quantity_ids':[]},
]
edge_ids={e['id'] for e in g['edges']}
for e in weakening_edges:
    if e['id'] not in edge_ids: g['edges'].append(e)

# Release identity.
parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-58_fire_ui22_routing_protection_library_hotfix'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.58 — FIRE-UI2.2 routing continuity + STO ARSS protection-property library'
g['description']='Cumulative v0.3.58 over FIRE-UI2.1: restores orphaned SP16 9.2.3/9.2.6 guided entries and gamma_e downstream navigation, adds an explicit post-unprotected continuation into fire-protection design, and replaces raw 12.5 material-object authoring with a source-traced STO ARSS library or manual scalar properties. Mineral-wool library density is fixed at 100 kg/m3 while retaining the printed 80-100 kg/m3 provenance range.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':RELEASE,'parent_graph_id':parent,
 'fire_ui22_gammae_navigation_closed':True,'fire_ui22_sp16_923_entry_restored':True,'fire_ui22_sp16_926_entry_restored':True,
 'fire_ui22_unprotected_post_result_protection_entry_closed':True,
 'fire_ui22_sto_arss_material_library_added':True,'fire_ui22_sto_arss_mineral_wool_density_kg_m3':100.0,
 'fire_ui22_manual_protection_material_properties_added':True,
 'fire_ui22_qy_runtime_closed':False,'fire_ui22_torsion_runtime_closed':False,
})

# Stable identity checks.
node_ids=[n['id'] for n in g['nodes']]; edge_ids=[e['id'] for e in g['edges']]; qty_ids=[q['id'] for q in g['quantities']]; ds_ids=[d['id'] for d in g['datasets']]
assert len(node_ids)==len(set(node_ids)), 'duplicate node id'
assert len(edge_ids)==len(set(edge_ids)), 'duplicate edge id'
assert len(qty_ids)==len(set(qty_ids)), 'duplicate quantity id'
assert len(ds_ids)==len(set(ds_ids)), 'duplicate dataset id'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
