from __future__ import annotations
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
src=ROOT/'normative_graph/dag_v0.3.51_fire_ui15_weakening_continuation_hotfix.json'
out=ROOT/'normative_graph/dag_v0.3.52_fire_ui16_signed_load_parallel_scheduler.json'
g=json.loads(src.read_text(encoding='utf-8'))
q={x['id']:x for x in g['quantities']}; n={x['id']:x for x in g['nodes']}

def addq(row):
    if row['id'] not in q:
        g['quantities'].append(row); q[row['id']]=row

def num(qid,symbol,name,dim,unit,allowed,source='LOAD_INPUT'):
    return {'id':qid,'symbol':symbol,'name_ru':name,'data_type':'number','role':'input' if source!='DERIVED' else 'intermediate','physical_dimension':dim,'canonical_unit':unit,'allowed_units':allowed,'source_policy':{'primary_source_type':source if source!='DERIVED' else 'CALCULATED','allowed_source_types':[source if source!='DERIVED' else 'CALCULATED'],'override_policy':'forbidden'}}

def obj(qid,name,source='CALCULATED'):
    return {'id':qid,'symbol':None,'name_ru':name,'data_type':'object','role':'intermediate','physical_dimension':None,'canonical_unit':None,'allowed_units':[],'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}}

# FIRE-UI1.6 weakening quantities
addq({'id':'net_property_reduction_mode','symbol':None,'name_ru':'Учет изменения геометрических характеристик при ослаблении','data_type':'enum','role':'decision_state','physical_dimension':None,'canonical_unit':None,'allowed_units':[],'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'forbidden'},'enum_values':[{'value':'area_only_keep_gross','label':'Уменьшить только площадь A; I/W оставить брутто'},{'value':'manual_net_properties','label':'Учитывать изменение I/W; ввести net-характеристики вручную'}]})
for qid,sym,name,dim,unit in [
 ('manual_I_xn','I_xn','Ixn вручную','second_moment_area','mm4'),('manual_I_yn','I_yn','Iyn вручную','second_moment_area','mm4'),
 ('manual_W_xn_min','W_xn,min','Wxn,min вручную','section_modulus','mm3'),('manual_W_yn_min','W_yn,min','Wyn,min вручную','section_modulus','mm3'),
 ('manual_W_pl_x_eff','W_pl,x,n','Wpl,x,n вручную','section_modulus','mm3'),('manual_W_pl_y_eff','W_pl,y,n','Wpl,y,n вручную','section_modulus','mm3'),
 ('manual_I_omega_n','I_omega,n','Iωn вручную (при необходимости)','sectorial_moment','mm6'),('manual_W_omega_eff','W_omega,n','Wωn вручную (при необходимости)','sectorial_section_modulus','mm4')]:
    addq(num(qid,sym,name,dim,unit,[unit],source='GEOMETRY_INPUT'))

# Signed element-local load menu quantities.
for row in [
 num('load_My_local','M_y','Изгибающий момент My (локальная ось Y)','moment','Nmm',['Nmm','kNm']),
 num('load_Mz_local','M_z','Изгибающий момент Mz (локальная ось Z)','moment','Nmm',['Nmm','kNm']),
 num('load_Qy_local','Q_y','Поперечная сила Qy (локальная ось Y)','force','N',['N','kN']),
 num('load_Qz_local','Q_z','Поперечная сила Qz (локальная ось Z)','force','N',['N','kN']),
 num('T_torsion','T=M_x','Крутящий момент T (= Mx относительно продольной оси X)','moment','Nmm',['Nmm','kNm']),
 obj('verification_plan','Автоматически сформированный план нормативных проверок'),
 {'id':'verification_plan_confirmed','symbol':None,'name_ru':'План проверок подтвержден','data_type':'boolean','role':'decision_state','physical_dimension':None,'canonical_unit':None,'allowed_units':[],'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'forbidden'}}
]: addq(row)

# Update weakening authoring node.
w=n['SP554_I_SECTION_WEAKENING']
w['title']='Круглые болтовые отверстия'
w['input_spec']['user_prompt']='Укажите отсутствие отверстий либо круглые болтовые отверстия: диаметр d и шаг s. Площадь нетто рассчитывается автоматически для любого сечения как A_n=A-d·t_h; локальная толщина t_h берется из модели сечения либо вводится явно.'
w['notes']['normative_warning']='FIRE-UI1.6: primary weakening route supports round bolt holes only. Area loss is universal A_n=A-d·t_h. Change of I/W is a separate explicit user decision. SP16 formula (45) retains s as pitch in one vertical row and requires s>d.'

# Add explicit property-change decision and manual net bundle.
node_dec={
 'id':'SP554_D_NET_PROPERTY_REDUCTION','node_type':'decision','owner_standard_id':'SP554_2026','title':'Влияние отверстия на I и W',
 'normative_refs':copy.deepcopy(w['normative_refs']),'consumes':[{'quantity_id':'sp16_has_weakening','required':True,'binding_role':'condition'}],
 'produces':[{'quantity_id':'net_property_reduction_mode','required':True,'binding_role':'output'}],'applicability':{'type':'comparison','quantity_id':'sp16_has_weakening','operator':'eq','value':True},
 'notes':{'engineering_meaning':'Explicit temporary universal weakening policy.','limitations':'Area reduction is automatic; exact changes of inertia/moduli are either neglected by explicit assumption or supplied manually.','normative_warning':'Choosing gross I/W is an explicit engineering assumption; it is never applied silently.'},
 'question':'Учитывать изменение моментов инерции и моментов сопротивления после ослабления?', 'decision_quantity_id':'net_property_reduction_mode',
 'options':[{'value':'area_only_keep_gross','label':'Нет — уменьшаем только A','description':'A_n=A-d·t_h; I, W, Wpl остаются брутто по принятому допущению отверстия на нейтральной линии.'},{'value':'manual_net_properties','label':'Да — введу net-характеристики','description':'A_n программа считает сама; I/W/Wpl задаются готовыми значениями нетто.'}]
}
node_manual={
 'id':'SP554_I_NET_SECTION_MANUAL_PROPERTIES','node_type':'input','owner_standard_id':'SP554_2026','title':'Готовые геометрические характеристики сечения нетто',
 'normative_refs':copy.deepcopy(w['normative_refs']),'consumes':[{'quantity_id':'net_property_reduction_mode','required':True,'binding_role':'condition'}],
 'produces':[{'quantity_id':x,'required':x not in {'manual_I_omega_n','manual_W_omega_eff'},'binding_role':'output'} for x in ['manual_I_xn','manual_I_yn','manual_W_xn_min','manual_W_yn_min','manual_W_pl_x_eff','manual_W_pl_y_eff','manual_I_omega_n','manual_W_omega_eff']],
 'applicability':{'type':'comparison','quantity_id':'net_property_reduction_mode','operator':'eq','value':'manual_net_properties'},
 'notes':{'engineering_meaning':'Manual net-property handoff; A_n is intentionally excluded because it is calculated from d·t_h.','limitations':'Iωn/Wωn are optional and are required only for warping/bimoment routes.','normative_warning':'Values must be independently calculated for the actual weakened section and use the same section axes/sign convention as the gross model.'},
 'input_spec':{'input_method':'manual_value','required':True,'user_prompt':'Введите готовые характеристики нетто. A_n вводить не нужно: площадь рассчитывается автоматически. Iωn и Wωn нужны только для маршрутов с бимоментом/стесненным кручением.','allow_default_without_confirmation':False}
}
for node in (node_dec,node_manual):
    if node['id'] not in n: g['nodes'].append(node); n[node['id']]=node

net=n['SP554_G_NET_SECTION_PROPERTIES']
net['title']='Net-сечение: универсальная потеря площади + явная политика I/W'
net['notes']['normative_warning']='FIRE-UI1.6 universal temporary rule: A_n=A-d·t_h for a round through-hole; no section-family restriction. I/W are either explicitly kept gross or supplied as independently calculated net values. No automatic arbitrary inertia subtraction is inferred.'
for qid in ['net_property_reduction_mode','manual_I_xn','manual_I_yn','manual_W_xn_min','manual_W_yn_min','manual_W_pl_x_eff','manual_W_pl_y_eff','manual_I_omega_n','manual_W_omega_eff']:
    if not any(b['quantity_id']==qid for b in net['consumes']): net['consumes'].append({'quantity_id':qid,'required':False,'binding_role':'input'})

# Load menu quantity handoff.
load=n['SP554_H_SP20_LOADS']
load['title']='Расчётные усилия'
load['reason']='СП554 8.1 / СП20: задаются signed усилия особого сочетания в локальной системе элемента X-Y-Z; X — продольная ось.'
load['produces']=[
 {'quantity_id':'special_load_combination','required':True,'binding_role':'output'},
 {'quantity_id':'N_force','required':True,'binding_role':'output'},
 {'quantity_id':'load_My_local','required':True,'binding_role':'output'}, {'quantity_id':'load_Mz_local','required':True,'binding_role':'output'},
 {'quantity_id':'load_Qy_local','required':True,'binding_role':'output'}, {'quantity_id':'load_Qz_local','required':True,'binding_role':'output'},
 {'quantity_id':'T_torsion','required':True,'binding_role':'output'}, {'quantity_id':'sp16_local_load_F','required':False,'binding_role':'output'}]
load['required_output_quantity_ids']=['special_load_combination','N_force','load_My_local','load_Mz_local','load_Qy_local','load_Qz_local','T_torsion']
load['notes']['normative_warning']='Signed convention FIRE-UI1.6: N>0 tension, N<0 compression. My/Mz are bending moments about local Y/Z; T=Mx is torsion about longitudinal X. The legacy SP554/SP16 M_x/M_y aliases are produced only by the traceable load adapter; torsion is never silently mapped to bimoment B.'

# Convert former manual stress-state question into automatic adapter/classifier.
ss=n['SP554_D_STRESS_STATE']
ss['node_type']='calculation'; ss['title']='Автоматическая классификация усилий и Verification Plan'
ss['consumes']=[{'quantity_id':x,'required':True,'binding_role':'input'} for x in ['special_load_combination','N_force','load_My_local','load_Mz_local','load_Qy_local','load_Qz_local','T_torsion']]
ss['produces']=[{'quantity_id':x,'required':True,'binding_role':'output'} for x in ['stress_state','M_x','M_y','Q_shear','B_bimoment','verification_plan']]
for k in ['question','decision_quantity_id','options']: ss.pop(k,None)
ss['calculation_spec']={'formula_type':'executor','expression_language':'executor_v1','bindings':[{'variable':x,'quantity_id':x} for x in ['N_force','load_My_local','load_Mz_local','load_Qy_local','load_Qz_local','T_torsion']],'rounding':{'mode':'none'},'algorithm_id':'fire_ui16_signed_load_verification_plan_v1'}
ss['notes']['normative_warning']='Automatic UI/application classification only. Mapping to legacy SP16 axes is explicit: local My -> legacy M_x; local Mz -> legacy M_y. Qz is the currently supported scalar shear route; Qy and torsion T are recorded as separate verification/deferred branches and are never silently discarded.'

confirm={
 'id':'SP554_D_VERIFICATION_PLAN_CONFIRM','node_type':'decision','owner_standard_id':'SP554_2026','title':'План нормативных проверок',
 'normative_refs':copy.deepcopy(ss['normative_refs']),'consumes':[{'quantity_id':'verification_plan','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':'verification_plan_confirmed','required':True,'binding_role':'output'}],'applicability':None,
 'notes':{'engineering_meaning':'Read-only user confirmation of the automatically derived verification plan.','limitations':None,'normative_warning':'The plan is derived from signed loads; the user does not manually choose the stress-state branch.'},
 'question':'План проверок сформирован. Продолжить?', 'decision_quantity_id':'verification_plan_confirmed',
 'options':[{'value':True,'label':'Продолжить расчёт','description':'Выполнить все поддерживаемые ветви последовательно.'}]
}
if confirm['id'] not in n: g['nodes'].append(confirm); n[confirm['id']]=confirm

# Rewire stress-state navigation through confirmation. Keep parallel tension gamma_c branch.
for e in g['edges']:
    if e['id']=='E0087': e['from_node_id']='SP554_D_VERIFICATION_PLAN_CONFIRM'
    if e['id']=='E0214': e['from_node_id']='SP554_D_VERIFICATION_PLAN_CONFIRM'
# Add classifier -> confirmation.
if not any(e['from_node_id']=='SP554_D_STRESS_STATE' and e['to_node_id']=='SP554_D_VERIFICATION_PLAN_CONFIRM' for e in g['edges']):
    g['edges'].append({'id':'UI16_E_PLAN_CONFIRM','from_node_id':'SP554_D_STRESS_STATE','to_node_id':'SP554_D_VERIFICATION_PLAN_CONFIRM','edge_type':'control','label':'automatic verification plan','condition':None,'quantity_ids':['verification_plan']})
# Central tension section-formulas route was missing in v0.48.
if not any(e['from_node_id']=='SP554_D_GAMMA_T_METHOD' and e['to_node_id']=='SP554_C_9_1' for e in g['edges']):
    g['edges'].append({'id':'UI16_E_GAMMAT_TENSION_SECTION','from_node_id':'SP554_D_GAMMA_T_METHOD','to_node_id':'SP554_C_9_1','edge_type':'branch','label':'section formulas / central tension','condition':{'type':'all_of','conditions':[{'type':'comparison','quantity_id':'strength_coefficient_method','operator':'eq','value':'section_formulas'},{'type':'comparison','quantity_id':'stress_state','operator':'eq','value':'central_tension'}]},'quantity_ids':[]})

# Catalog geometry must expose row dimensions used by downstream SP16 formulas.
catalog_node=n.get('SP554_G_CATALOG')
if catalog_node is not None:
    declared={b['quantity_id'] for b in catalog_node.get('produces',[])}
    for qid in ['sec_h','sec_b','t_f','r_root','sp16_ltb_h_axes','sp16_ltb_h1','sp16_ltb_h2','sp16_ltb_b1','sp16_ltb_b2','sp16_ltb_I1','sp16_ltb_I2']:
        if qid not in declared:
            catalog_node['produces'].append({'quantity_id':qid,'required':False,'binding_role':'output'})

# Sectorial properties are conditionally required only when a nonzero bimoment
# branch is active.  The no-weakening identity node must not block ordinary
# B=0 bending/shear cases merely because a catalog does not carry Iω/Wω.
identity=n.get('SP16_C_NET_ADVANCED_IDENTITY')
if identity is not None:
    for b in identity.get('consumes',[]):
        if b['quantity_id'] in {'I_omega_gross','W_omega_gross'}: b['required']=False
    for b in identity.get('produces',[]):
        if b['quantity_id'] in {'I_omega_n','W_omega_eff'}: b['required']=False


# Compression controlling coefficient requires both strength and modulus routes.
# In the frozen graph gamma_T_required was optional, which allowed min(gammaT,
# gammaE) to execute with None while the parallel strength branch was still
# running.  Guided execution must wait for both coefficients.
if "SP554_C_CTRL_COMPRESSION" in n:
    for _b in n["SP554_C_CTRL_COMPRESSION"].get("consumes",[]):
        if _b.get("quantity_id")=="gamma_T_required":
            _b["required"]=True

# FIRE-UI1.6 route-closure hardening discovered by full signed-load census.
# Data edge 8.4->8.3 is a required parallel mechanical formula chain, not a
# passive optional consumer; promote it to explicit navigation so the branch
# queue cannot lose gamma_e while SP16 slenderness proceeds in parallel.
for _eid in ("E0104","E0165"):
    for _e in g["edges"]:
        if _e.get("id")==_eid:
            _e["edge_type"]="control"

# LTB is relevant only when the legacy major-axis bending moment M_x is present.
# Local FIRE-UI1.6 My is mapped to legacy M_x; local Mz-only and pure-shear
# routes must not launch Annex Ж.
if "SP16_D_LTB" in n:
    n["SP16_D_LTB"]["applicability"]={"type":"comparison","quantity_id":"has_Mx","operator":"eq","value":True}

# 9.2.5 coefficient c is an N+M compression-stability branch.  A data edge
# from phi_b must not activate it during pure bending.
if "SP16_C_C113" in n:
    old=n["SP16_C_C113"].get("applicability")
    route={"type":"comparison","quantity_id":"stress_state","operator":"eq","value":"compression_plus_bending"}
    n["SP16_C_C113"]["applicability"]={"type":"all_of","conditions":[route,old]} if old else route

# Monosymmetric/tee Annex-Ж consumers are alternative routes.  Some historical
# nodes lacked their own applicability and were woken by data-only continuations.
for _nid in ("SP16_C_LTB_C_J5","SP16_C_LTB_PHI1_MONO_J6","SP16_C_LTB_PHI2_MONO_J7","SP16_C_LTB_ETA_J13"):
    if _nid in n:
        n[_nid]["applicability"]={"type":"comparison","quantity_id":"sp16_phi_b_section_route","operator":"in","value":["monosymmetric_i","tee"]}

# Independent FIRE-D2 inverse lookups must execute only after the Annex-B
# inverse-domain gate has passed.  This prevents forbidden extrapolation from
# being attempted in parallel before the explicit out-of-range result branch.
if "SP554_FIRE_D2_L_B1_STRENGTH_TCR" in n:
    n["SP554_FIRE_D2_L_B1_STRENGTH_TCR"]["applicability"]={"type":"comparison","quantity_id":"sp554_b1_inverse_domain_ok","operator":"eq","value":True}
if "SP554_FIRE_D2_L_B1_MODULUS_TCR" in n:
    n["SP554_FIRE_D2_L_B1_MODULUS_TCR"]["applicability"]={"type":"all_of","conditions":[
        {"type":"comparison","quantity_id":"sp554_b1_inverse_domain_ok","operator":"eq","value":True},
        {"type":"comparison","quantity_id":"stress_state","operator":"in","value":["central_compression","compression_plus_bending"]}
    ]}
# Explicitly enqueue FIRE-D2 independent lookups from the passed domain gate.
if not any(e.get("id")=="UI16_E_DOMAIN_TO_FIRE_D2_STRENGTH" for e in g["edges"]):
    g["edges"].append({"id":"UI16_E_DOMAIN_TO_FIRE_D2_STRENGTH","from_node_id":"SP554_A_B1_INVERSE_DOMAIN","to_node_id":"SP554_FIRE_D2_L_B1_STRENGTH_TCR","edge_type":"branch","label":"FIRE-D2 strength inverse after domain gate","condition":{"type":"comparison","quantity_id":"sp554_b1_inverse_domain_ok","operator":"eq","value":True},"quantity_ids":["sp554_b1_inverse_domain_ok"]})
if not any(e.get("id")=="UI16_E_DOMAIN_TO_FIRE_D2_MODULUS" for e in g["edges"]):
    g["edges"].append({"id":"UI16_E_DOMAIN_TO_FIRE_D2_MODULUS","from_node_id":"SP554_A_B1_INVERSE_DOMAIN","to_node_id":"SP554_FIRE_D2_L_B1_MODULUS_TCR","edge_type":"branch","label":"FIRE-D2 modulus inverse for compression after domain gate","condition":{"type":"all_of","conditions":[{"type":"comparison","quantity_id":"sp554_b1_inverse_domain_ok","operator":"eq","value":True},{"type":"comparison","quantity_id":"stress_state","operator":"in","value":["central_compression","compression_plus_bending"]}]},"quantity_ids":["sp554_b1_inverse_domain_ok"]})

# Explicit terminal summary for active-but-not-yet-supported Qy/torsion branches.
# Supported branches are still executed first; this result prevents a partial
# supported calculation from being mistaken for an engineering-complete case.
if "SP554_R_UI16_DEFERRED_BRANCHES" not in n:
    _node={
      "id":"SP554_R_UI16_DEFERRED_BRANCHES","node_type":"result","owner_standard_id":"SP554_2026",
      "title":"Механическая проверка неполная — есть отложенные ветви",
      "normative_refs":[{"standard_id":"SP554_2026","reference_kind":"derived_graph_logic","quote_or_note":"FIRE-UI1.6 execution-scope result; no normative resistance formula is invented for unsupported branches."}],
      "consumes":[{"quantity_id":"verification_plan","required":True,"binding_role":"input"}],"produces":[],
      "applicability":{"type":"any_of","conditions":[{"type":"comparison","quantity_id":"load_Qy_local","operator":"neq","value":0},{"type":"comparison","quantity_id":"T_torsion","operator":"neq","value":0}]},
      "notes":{"engineering_meaning":"All currently supported mechanical branches may be calculated, but the overall verification is incomplete because Qy minor-axis shear and/or torsion T is not yet bound to a normative runtime.","limitations":"No silent mapping Qy->Qz and no T->B substitution.","normative_warning":"Fail-closed partial-result summary."}
    }
    g["nodes"].append(_node); n[_node["id"]]=_node
if not any(e.get("id")=="UI16_E_PLAN_TO_DEFERRED_RESULT" for e in g["edges"]):
    g["edges"].append({"id":"UI16_E_PLAN_TO_DEFERRED_RESULT","from_node_id":"SP554_D_VERIFICATION_PLAN_CONFIRM","to_node_id":"SP554_R_UI16_DEFERRED_BRANCHES","edge_type":"branch","label":"unsupported Qy/T branch summary","condition":{"type":"any_of","conditions":[{"type":"comparison","quantity_id":"load_Qy_local","operator":"neq","value":0},{"type":"comparison","quantity_id":"T_torsion","operator":"neq","value":0}]},"quantity_ids":["verification_plan"]})

# DAG metadata.
g['graph_id']='sp16_sp554_dag_v0-3-52_fire_ui16_signed_load_parallel_scheduler'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.52 — FIRE-UI1.6 signed loads, universal weakening and parallel verification plan'
g['description']='Cumulative v0.3.52 over v0.3.51. Adds universal A_net bolt-hole authoring with explicit I/W policy, signed local load menu, automatic verification plan/classification, and routing support for the parallel-branch guided scheduler. Normative formulas remain those of the frozen SP16/SP554 DAG.'
# Update semantic presentation marker if present.
g.setdefault('presentation',{})['fire_ui_stage']='FIRE-UI1.6'
out.write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
print(out)
print('quantities',len(g['quantities']),'nodes',len(g['nodes']),'edges',len(g['edges']))
