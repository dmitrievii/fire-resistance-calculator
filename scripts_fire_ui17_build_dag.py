from __future__ import annotations
import copy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.52_fire_ui16_signed_load_parallel_scheduler.json'
OUT=ROOT/'normative_graph/dag_v0.3.53_fire_ui17_critical_temperature_restraint_ux_hotfix.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
q={x['id']:x for x in g['quantities']}; n={x['id']:x for x in g['nodes']}

def addq(row):
    if row['id'] not in q:
        g['quantities'].append(row); q[row['id']]=row

def obj(qid,name):
    return {'id':qid,'symbol':None,'name_ru':name,'data_type':'object','role':'intermediate','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
            'source_policy':{'primary_source_type':'CALCULATED','allowed_source_types':['CALCULATED'],'override_policy':'forbidden'}}
def num(qid,sym,name):
    return {'id':qid,'symbol':sym,'name_ru':name,'data_type':'number','role':'result','physical_dimension':'temperature','canonical_unit':'degC','allowed_units':['degC'],
            'source_policy':{'primary_source_type':'CALCULATED','allowed_source_types':['CALCULATED'],'override_policy':'forbidden'}}
def enum(qid,name,vals):
    return {'id':qid,'symbol':None,'name_ru':name,'data_type':'enum','role':'result','physical_dimension':None,'canonical_unit':None,'allowed_units':[],
            'source_policy':{'primary_source_type':'CALCULATED','allowed_source_types':['CALCULATED'],'override_policy':'forbidden'},
            'enum_values':[{'value':v,'label':lab} for v,lab in vals]}

addq(obj('fire_d2_strength_inversion_result','FIRE-D2 обратная зависимость γT → температура'))
addq(obj('fire_d2_modulus_inversion_result','FIRE-D2 обратная зависимость γe → температура'))
addq(enum('fire_d2_critical_temperature_status','Статус определения критической температуры',[
    ('COMPLETE','Точная критическая температура внутри опубликованной области'),
    ('AMBIENT_CAPACITY_EXCEEDED','Несущая способность не обеспечена уже при нормальной температуре'),
    ('INCOMPLETE_FAIL_CLOSED','Точная температура выше опубликованного диапазона; известна нижняя граница')]))
addq(enum('fire_d2_critical_temperature_controlling_kind','Определяющая температурная ветвь',[
    ('gamma_T','прочность γT'),('gamma_E','модуль упругости γe'),('bounded','обе ветви выше опубликованного диапазона')]))
addq(num('fire_d2_critical_temperature_lower_bound_c','t_cr,lower','Нижняя нормативно подтвержденная граница критической температуры'))

# Keep source-literal controller/domain nodes for audit only, but make their status unmistakably diagnostic.
for nid in ['SP554_C_CTRL_COMPRESSION','SP554_K_CTRL_KIND_COMPRESSION','SP554_C_CTRL_STRENGTH_ONLY','SP554_K_CTRL_KIND_STRENGTH','SP554_A_B1_INVERSE_DOMAIN']:
    if nid in n:
        n[nid].setdefault('notes',{})['normative_warning']='Diagnostic/source-literal trace only. FIRE-UI1.7 production critical-temperature selection independently inverts γT and γe and selects the earliest limit-state temperature; this node does not control production routing.'
        n[nid]['title']='Диагностический source-literal узел — не управляет FIRE-D2 production'

# New independent critical-temperature selector nodes.
refs=copy.deepcopy(n['SP554_FIRE_D2_C_CRITICAL_TEMPERATURE_GOV']['normative_refs'])
base_notes={
  'engineering_meaning':'Independent Appendix-B inversion for strength and, where applicable, elastic-modulus criteria followed by earliest-temperature selection.',
  'limitations':'No extrapolation. γ>1 means ambient capacity exceeded; γ below the published minimum yields a lower-bound temperature result.',
  'normative_warning':'Do not compare γT and γe numerically before inversion: they belong to different Appendix-B curves.'}

def selector_node(nid,title,compression):
    consumes=[{'quantity_id':'steel_strength_group','required':True,'binding_role':'input'},
              {'quantity_id':'gamma_T_required','required':True,'binding_role':'input'}]
    if compression:
        consumes.append({'quantity_id':'gamma_E_required','required':True,'binding_role':'input'})
    consumes.append({'quantity_id':'fire_d2_temperature_governing_policy_reconciled','required':True,'binding_role':'input'})
    prod=[
      {'quantity_id':'fire_d2_strength_inversion_result','required':True,'binding_role':'output'},
      {'quantity_id':'fire_d2_modulus_inversion_result','required':False,'binding_role':'output'},
      {'quantity_id':'fire_d2_critical_temperature_status','required':True,'binding_role':'output'},
      {'quantity_id':'fire_d2_critical_temperature_c','required':False,'binding_role':'output'},
      {'quantity_id':'fire_d2_critical_temperature_lower_bound_c','required':False,'binding_role':'output'},
      {'quantity_id':'fire_d2_critical_temperature_controlling_kind','required':True,'binding_role':'output'}]
    applicability={'type':'comparison','quantity_id':'stress_state','operator':'in','value':['central_compression','compression_plus_bending']} if compression else {'type':'comparison','quantity_id':'stress_state','operator':'in','value':['central_tension','bending','tension_plus_bending']}
    return {'id':nid,'node_type':'calculation','owner_standard_id':'SP554_2026','title':title,'normative_refs':refs,
            'consumes':consumes,'produces':prod,'applicability':applicability,'notes':copy.deepcopy(base_notes),
            'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'fire_ui17_independent_appendix_b_inversion_v1','bindings':[{'variable':x['quantity_id'],'quantity_id':x['quantity_id']} for x in consumes],'rounding':{'mode':'none'}}}
for row in [selector_node('SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY','FIRE-UI1.7 критическая температура — независимая инверсия γT',False),
            selector_node('SP554_FIRE_UI17_C_TCR_COMPRESSION','FIRE-UI1.7 критическая температура — независимые γT и γe',True)]:
    if row['id'] not in n: g['nodes'].append(row); n[row['id']]=row

# Result accepts exact or bounded/ambient result and exposes branch trace.
r=n['SP554_FIRE_D2_R_CRITICAL_TEMPERATURE']
r['title']='Критическая температура стали — FIRE-UI1.7 агрегированный результат'
r['consumes']=[
 {'quantity_id':'fire_d2_critical_temperature_status','required':True,'binding_role':'input'},
 {'quantity_id':'fire_d2_critical_temperature_c','required':False,'binding_role':'input'},
 {'quantity_id':'fire_d2_critical_temperature_lower_bound_c','required':False,'binding_role':'input'},
 {'quantity_id':'fire_d2_critical_temperature_controlling_kind','required':True,'binding_role':'input'},
 {'quantity_id':'fire_d2_strength_inversion_result','required':True,'binding_role':'input'},
 {'quantity_id':'fire_d2_modulus_inversion_result','required':False,'binding_role':'input'},
 {'quantity_id':'fire_d2_runtime_closed','required':True,'binding_role':'input'}]
r['result_quantity_ids']=[x['quantity_id'] for x in r['consumes']]
r['notes']['engineering_meaning']='Exact, ambient-failure, or lower-bound critical-temperature result after independent γT/γe Appendix-B inversion.'
r['notes']['limitations']='A lower-bound result is not extrapolated and must remain relational (Tcr > published Tmax).'
r['notes']['normative_warning']='Branch temperatures are diagnostic unless selected as governing. A γ>1 branch means ambient capacity exceeded and governs over any higher-temperature branch.'

# Retire the older exact-temperature min node from guided production (kept frozen for audit).
n['SP554_FIRE_D2_C_CRITICAL_TEMPERATURE_GOV']['title']='FIRE-D2 legacy exact-temperature min — retained for audit, superseded by FIRE-UI1.7'
n['SP554_FIRE_D2_C_CRITICAL_TEMPERATURE_GOV']['notes']['normative_warning']='Superseded in guided production by FIRE-UI1.7 independent-domain selectors that also handle ambient-capacity and bounded-above-range statuses.'

# Add data dependency edges from every γT producer to both selectors, and from selectors to result.
existing={e['id'] for e in g['edges']}
for prod in [x for x in g['nodes'] if any(b['quantity_id']=='gamma_T_required' for b in x.get('produces',[]))]:
    for suffix,target in [('S','SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY'),('C','SP554_FIRE_UI17_C_TCR_COMPRESSION')]:
        eid=f'UI17_E_{prod["id"]}_TO_TCR_{suffix}'
        if eid not in existing:
            g['edges'].append({'id':eid,'from_node_id':prod['id'],'to_node_id':target,'edge_type':'data','label':'independent Appendix-B critical-temperature selector','condition':None,'quantity_ids':['gamma_T_required']}); existing.add(eid)
for source in ['SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY','SP554_FIRE_UI17_C_TCR_COMPRESSION']:
    eid=f'UI17_E_{source}_TO_RESULT'
    if eid not in existing:
        g['edges'].append({'id':eid,'from_node_id':source,'to_node_id':'SP554_FIRE_D2_R_CRITICAL_TEMPERATURE','edge_type':'data','label':'aggregated critical-temperature status/result','condition':None,'quantity_ids':['fire_d2_critical_temperature_status']}); existing.add(eid)

# FIRE-UI1.7 removes the raw member_restraint_model object from the ordinary guided authoring path.
# The user chooses the effective-length route and Table-30 scheme explicitly instead. Advanced
# 10.3 branches already carry their own dedicated normative method selectors, so this opaque
# transport object is not a prerequisite for those decisions.
for nid in ['SP554_I_COMPRESSION_CONTEXT','SP554_I_NM_CONTEXT']:
    if nid in n:
        n[nid]['produces']=[b for b in n[nid].get('produces',[]) if b['quantity_id']!='member_restraint_model']
        if nid=='SP554_I_COMPRESSION_CONTEXT':
            n[nid]['title']='Геометрическая длина сжатого элемента'
            n[nid]['input_spec']['user_prompt']='Введите геометрическую длину элемента. Схема закрепления и коэффициент μ выбираются далее из нормативного меню СП16.'
        else:
            n[nid]['input_spec']['user_prompt']='Введите длину и оставшийся контекст устойчивости N+M. Схемы μx/μy выбираются далее отдельными нормативными меню СП16.'
for nid in ['SP16_D_MU_ROUTE','SP16_D_MU_ROUTE_X','SP16_D_MU_ROUTE_Y','SP16_D_MU_ADV_METHOD_X','SP16_D_MU_ADV_METHOD_Y']:
    if nid in n:
        n[nid]['consumes']=[b for b in n[nid].get('consumes',[]) if b['quantity_id']!='member_restraint_model']

# Improve Table 30 decision semantics. S1-S4 are the common classical cases; S5-S8 retain exact normative IDs/value without guessing their figure/load semantics.
mu_labels={
 'S1':('Шарнир — шарнир','μ = 1,00'),
 'S2':('Защемление — шарнир','μ = 0,70'),
 'S3':('Защемление — защемление','μ = 0,50'),
 'S4':('Защемление — свободный конец (консоль)','μ = 2,00'),
 'S5':('Схема 5 таблицы 30','μ = 1,00 · зависит от схемы нагрузки на рисунке таблицы'),
 'S6':('Схема 6 таблицы 30','μ = 2,00 · зависит от схемы нагрузки на рисунке таблицы'),
 'S7':('Схема 7 таблицы 30','μ = 0,725 · зависит от схемы нагрузки на рисунке таблицы'),
 'S8':('Схема 8 таблицы 30','μ = 1,12 · зависит от схемы нагрузки на рисунке таблицы')}
for nid in ['SP16_D_MU_SCHEME','SP16_D_MU_SCHEME_X','SP16_D_MU_SCHEME_Y']:
    if nid not in n: continue
    node=n[nid]
    axis=''
    if nid.endswith('_X'): axis=' по оси x'
    elif nid.endswith('_Y'): axis=' по оси y'
    node['title']='Нормативная схема расчётной длины по таблице 30'+axis
    node['question']='Выберите схему закрепления/нагружения по таблице 30 СП 16'+axis+'. Для обычных стержней используйте четыре именованные схемы; для схем 5–8 сверяйте рисунок нагрузки таблицы 30.'
    node.setdefault('notes',{})['engineering_meaning']='СП16 10.3.3: μ определяется в зависимости от условий закрепления концов и вида нагрузки.'
    node['notes']['normative_warning']='Два типа опор сами по себе не определяют все 8 вариантов таблицы 30: схемы 5–8 включают вид/положение нагрузки. UI не угадывает их по опорам.'
    for o in node.get('options',[]):
        if o['value'] in mu_labels:
            o['label'],o['description']=mu_labels[o['value']]

# Improve Table 7 decisions with actual coefficients and UI redraw guidance.
curve_desc={
 'a':'α = 0,03; β = 0,06. Наиболее благоприятная кривая из таблицы 7; применимость определяется формой сечения и плоскостью потери устойчивости.',
 'b':'α = 0,04; β = 0,09. Типичная ветвь для ряда двутавров в соответствующей расчётной плоскости.',
 'c':'α = 0,04; β = 0,14. Менее благоприятная кривая; часто применяется к открытым/слабым направлениям согласно таблице 7.'}
for nid in ['SP16_D_CURVE','SP16_D_CURVE_X','SP16_D_CURVE_Y']:
    if nid not in n: continue
    node=n[nid]
    node['title']='Тип кривой устойчивости a/b/c по таблице 7 СП 16'
    node['question']='Выберите тип a/b/c по таблице 7 для рассматриваемой плоскости. Схематическая перерисовка и коэффициенты показаны на карточках.'
    node.setdefault('notes',{})['engineering_meaning']='Оси x-x / y-y в таблице 7 задают плоскость расчёта; тип зависит от формы сечения и направления потери устойчивости.'
    node['notes']['normative_warning']='Схемы в UI являются собственной схематической перерисовкой для навигации, а не заменой нормативной таблицы 7.'
    for o in node.get('options',[]):
        if o['value'] in curve_desc: o['description']=curve_desc[o['value']]
        if o['value']=='other': o['description']='Нет однозначного типа a/b/c в текущем маршруте — требуется отдельная нормативная ветвь.'

# Release identity.
g['graph_id']='sp16_sp554_dag_v0-3-53_fire_ui17_critical_temperature_restraint_ux_hotfix'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.53 — FIRE-UI1.7 critical-temperature and restraint UX hotfix'
g['description']='Cumulative v0.3.53 over FIRE-UI1.6: independent Appendix-B inversion/aggregation of gamma_T and gamma_e with ambient-capacity and bounded-above-range statuses; Table 30 restraint selector semantics; Table 7 visual selector semantics.'
meta=g.setdefault('metadata',{})
meta['release_stage']='v0.50_fire_ui17_critical_temperature_restraint_ux_hotfix_r1'
meta['parent_graph_id']='sp16_sp554_dag_v0-3-52_fire_ui16_signed_load_parallel_scheduler'
meta['fire_ui17_independent_critical_temperature_inversion']=True
meta['fire_ui17_table30_selector']=True
meta['fire_ui17_table7_visual_selector']=True

OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
