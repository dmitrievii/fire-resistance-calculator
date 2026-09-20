from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'normative_graph/dag_v0.3.32_stage_n3.json'
OUT=ROOT/'normative_graph/dag_v0.3.33_stage_n4.json'
SCHEMA=ROOT/'normative_graph/dag_schema.json'

d=json.loads(SRC.read_text(encoding='utf-8'))
d['graph_id']='sp16_sp554_dag_v0-3-33_stage_n4'
d['graph_title']='SP16/SP554 atomic normative DAG — Stage N4 bending members current-SP16 closure'
d['description']=(d.get('description') or '') + (' Stage N4 adds an applicability-safe current-SP16 bending-member orchestration for Section 8, including the ordinary class-1 elastic route, class-2/3 plastic route boundary, lateral-stability exemptions/calculation, current Annex Ж Ry-based phi nodes, equation (69), and local-stability screening. Pre-existing Ryn-based shared Annex Ж nodes are retained only for historical SP554 transformed invocation; the current-SP16 route does not consume them.')

qids={q['id'] for q in d['quantities']}
def qnum(id,symbol,name,dim='dimensionless',unit='1',role='intermediate',source='FORMULA_RESULT'):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':symbol,'name_ru':name,'data_type':'number','role':role,'physical_dimension':dim,'canonical_unit':unit,'allowed_units':[unit], 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'required_explicit' if source=='USER_INPUT' else 'forbidden'}});qids.add(id)
def qbool(id,name,role='input',source='USER_INPUT'):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':None,'name_ru':name,'data_type':'boolean','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[], 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'required_explicit' if source=='USER_INPUT' else 'forbidden'}});qids.add(id)
def qenum(id,name,vals,role='input',source='USER_INPUT'):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':None,'name_ru':name,'data_type':'enum','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[], 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'required_explicit' if source=='USER_INPUT' else 'forbidden'},'enum_values':[{'value':v,'label':lab} for v,lab in vals]});qids.add(id)

qenum('sp16_n4_beam_category','Категория изгибаемого элемента',[('ordinary','обычная балка'),('crane_runway','балка кранового пути'),('bimetal','бистальная балка')])
qnum('sp16_n4_member_class','class','Класс сечения по 4.2.7','count','1',role='input',source='USER_INPUT')
qbool('sp16_n4_load_is_static','Статическая нагрузка')
qenum('sp16_n4_strength_route','Выбранная ветвь прочности раздела 8',[('eq41','формула (41)'),('eq43','формула (43)'),('eq50','формула (50)'),('eq51','формула (51)'),('eq53','формула (53)'),('specialized','специализированная ветвь')],role='classification',source='CLASSIFICATION_RESULT')
qenum('sp16_n4_lateral_mode','Режим общей устойчивости',[('rigid_deck_exemption','8.4.4a — жесткий настил'),('table11_exemption','8.4.4b — таблица 11'),('calculate_phi_b','расчет phi_b'),('not_assessed','отдельная оценка')])
qenum('sp16_n4_local_mode','Режим местной устойчивости',[('geometry_and_stiffener_screen','screen 8.5.1/8.5.9'),('not_assessed','отдельная оценка')])
qnum('sp16_n4_eta41','η41','Использование прочности при одноосном изгибе по (41)',role='result')
qnum('sp16_n4_eta42','η42','Использование по поперечной силе по (42)',role='result')
qnum('sp16_n4_cxr61','c_xr','Коэффициент бистальной балки по (61)')
qnum('sp16_n4_alpha_f','αf','Отношение площади пояса к площади стенки',role='input',source='USER_INPUT')
qnum('sp16_n4_r_bimetal','r','Отношение Ryf/Ryw',role='input',source='USER_INPUT')
qnum('sp16_n4_phi1_current','φ1','Текущий SP16 коэффициент φ1 по Ж.3')
qnum('sp16_n4_phi1_mono_current','φ1','Текущий SP16 φ1 односимметричного I по Ж.6')
qnum('sp16_n4_phi2_mono_current','φ2','Текущий SP16 φ2 односимметричного I по Ж.7')
qnum('sp16_n4_phi_b_current','φb','Текущий SP16 коэффициент устойчивости при изгибе')
qnum('sp16_n4_eta69','η69','Использование общей устойчивости по (69)',role='result')
qnum('sp16_n4_lambda_w','λ̄w','Условная гибкость стенки балки')
qnum('sp16_n4_eta_governing','ηgov','Управляющее использование Stage N4',role='result')
qnum('sp16_n4_Wxn_min','Wxn,min','Минимальный момент сопротивления нетто x','section_modulus','mm3',role='input',source='USER_INPUT')
qnum('sp16_n4_S','S','Статический момент для сдвига','static_moment','mm3',role='input',source='USER_INPUT')
qnum('sp16_n4_I','I','Момент инерции для сдвига','inertia','mm4',role='input',source='USER_INPUT')
qnum('sp16_n4_tw','tw','Толщина стенки','length','mm',role='input',source='USER_INPUT')
qnum('sp16_n4_hef','hef','Расчетная высота стенки','length','mm',role='input',source='USER_INPUT')
qnum('sp16_n4_h1','h1','Расстояние до оси развитого пояса','length','mm',role='input',source='USER_INPUT')
qnum('sp16_n4_h2','h2','Расстояние до оси менее развитого пояса','length','mm',role='input',source='USER_INPUT')
qnum('sp16_n4_sigma_loc_cr1','σloc,cr,1','Критическое местное напряжение по (92)','stress','MPa',role='result')
qnum('sp16_n4_psi93','ψ','Коэффициент ψ по (93)',role='input',source='USER_INPUT')
qnum('sp16_n4_mu1','μ1','Отношение a/h1',role='input',source='USER_INPUT')
qnum('sp16_n4_lambda_a','λ̄a','Условная гибкость по a',role='input',source='USER_INPUT')

nids={n['id'] for n in d['nodes']}
def bind(qid,role='input'):return {'quantity_id':qid,'required':True,'binding_role':role}
def ref_formula(clause,formula,annex=None):
    r={'standard_id':'SP16_2017','reference_kind':'formula','formula_ref':formula}
    if annex:r['annex_ref']=annex
    else:r.update({'section':'8','clause':clause})
    return r
def ref_clause(clause):return {'standard_id':'SP16_2017','reference_kind':'clause','section':'8','clause':clause}
def notes(meaning=None,limitations=None,warning=None):return {'engineering_meaning':meaning,'limitations':limitations,'normative_warning':warning}
def simple(id,title,refs,inputs,output,latex,expr,bindings,app=None,nt=None):
    if id in nids: raise ValueError(id)
    d['nodes'].append({'id':id,'node_type':'calculation','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[bind(x) for x in inputs],'produces':[bind(output,'output')],'applicability':app,'notes':nt or notes(),'calculation_spec':{'formula_type':'simple','formula_latex':latex,'expression':expr,'expression_language':'expr_v1','bindings':[{'variable':v,'quantity_id':q} for v,q in bindings],'rounding':{'mode':'none'}}});nids.add(id)
def piece(id,title,refs,inputs,output,latex,bindings,cases,nt=None):
    d['nodes'].append({'id':id,'node_type':'calculation','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[bind(x) for x in inputs],'produces':[bind(output,'output')],'applicability':None,'notes':nt or notes(),'calculation_spec':{'formula_type':'piecewise','formula_latex':latex,'expression_language':'expr_v1','bindings':[{'variable':v,'quantity_id':q} for v,q in bindings],'cases':cases,'rounding':{'mode':'none'}}});nids.add(id)
def cmp(q,op,val):return {'type':'comparison','quantity_id':q,'operator':op,'value':val}
def allof(*conds):return {'type':'all_of','conditions':list(conds)}

# Explicit guided inputs
for id,title,outs,clause in [
 ('SP16_N4_I_BEAM_STATE','Исходное состояние изгибаемого элемента',['sp16_n4_beam_category','sp16_n4_member_class','sp16_n4_load_is_static'],'8.1'),
 ('SP16_N4_I_STABILITY_MODES','Явно выбранные режимы общей и местной устойчивости',['sp16_n4_lateral_mode','sp16_n4_local_mode'],'8.4-8.5')]:
    d['nodes'].append({'id':id,'node_type':'input','owner_standard_id':'SP16_2017','title':title,'normative_refs':[ref_clause(clause)],'consumes':[],'produces':[bind(x,'output') for x in outs],'applicability':None,'notes':notes(),'input_spec':{'input_method':'external_system','required':True,'user_prompt':title}});nids.add(id)

# Common elastic checks.
simple('SP16_N4_C_EQ41','Прочность балки 1-го класса при изгибе — (41)',[ref_formula('8.2.1','(41)')],['M_x','sp16_n4_Wxn_min','Ry_annex','gamma_c_sp16'],'sp16_n4_eta41',r'\eta_{41}=M/(W_{n,min}R_y\gamma_c)','abs(M)/(W*Ry*gc)',[('M','M_x'),('W','sp16_n4_Wxn_min'),('Ry','Ry_annex'),('gc','gamma_c_sp16')])
simple('SP16_N4_C_EQ42','Прочность стенки по поперечной силе — (42)',[ref_formula('8.2.1','(42)')],['Q_shear','sp16_n4_S','sp16_n4_I','sp16_n4_tw','Rs','gamma_c_sp16'],'sp16_n4_eta42',r'\eta_{42}=QS/(It_wR_s\gamma_c)','abs(Q)*S/(I*tw*Rs*gc)',[('Q','Q_shear'),('S','sp16_n4_S'),('I','sp16_n4_I'),('tw','sp16_n4_tw'),('Rs','Rs'),('gc','gamma_c_sp16')])
# Current equation (61) remediation.
simple('SP16_N4_C_EQ61_CURRENT','Бистальная балка — коэффициент c_xr по (61)',[ref_formula('8.2.8','(61)')],['sp16_n4_alpha_f','sp16_n4_r_bimetal'],'sp16_n4_cxr61',r'c_{xr}=(\alpha_fr+0.25-0.0833/r^2)/(\alpha_f+0.167)','(af*r+0.25-0.0833/r^2)/(af+0.167)',[('af','sp16_n4_alpha_f'),('r','sp16_n4_r_bimetal')])

# Dedicated current-SP16 Annex Ж nodes. The historical shared nodes intentionally use Ryn for SP554 transformed invocation.
simple('SP16_N4_C_LTB_PHI1_J3_RY','Текущий SP16: φ1 по Ж.3 с расчетным Ry',[ref_formula('Ж.2','(Ж.3)','Ж')],['sp16_psi_ltb','J_y','J_x','sp16_ltb_h','sp16_ltb_l_eff','E_norm','Ry_annex'],'sp16_n4_phi1_current',r'\varphi_1=\psi(I_y/I_x)(h/l_{ef})^2(E/R_y)','psi*(Iy/Ix)*(h/lef)^2*(E/Ry)',[('psi','sp16_psi_ltb'),('Iy','J_y'),('Ix','J_x'),('h','sp16_ltb_h'),('lef','sp16_ltb_l_eff'),('E','E_norm'),('Ry','Ry_annex')],nt=notes(warning='Dedicated current-SP16 node. Do not substitute Ryn; the Ryn-based shared node belongs only to the transformed SP554 invocation context.'))
simple('SP16_N4_C_LTB_PHI1_MONO_J6_RY','Текущий SP16: φ1 по Ж.6 с расчетным Ry',[ref_formula('Ж.4','(Ж.6)','Ж')],['sp16_ltb_psi_a_effective','J_y','J_x','sp16_ltb_h_axes','sp16_ltb_h1','sp16_ltb_l_eff','E_norm','Ry_annex'],'sp16_n4_phi1_mono_current',r'\varphi_1=\psi_a(I_y/I_x)(2hh_1/l_{ef}^2)(E/R_y)','psi_a*(Iy/Ix)*(2*h*h1/lef^2)*(E/Ry)',[('psi_a','sp16_ltb_psi_a_effective'),('Iy','J_y'),('Ix','J_x'),('h','sp16_ltb_h_axes'),('h1','sp16_ltb_h1'),('lef','sp16_ltb_l_eff'),('E','E_norm'),('Ry','Ry_annex')])
simple('SP16_N4_C_LTB_PHI2_MONO_J7_RY','Текущий SP16: φ2 по Ж.7 с расчетным Ry',[ref_formula('Ж.4','(Ж.7)','Ж')],['sp16_ltb_psi_a_effective','J_y','J_x','sp16_ltb_h_axes','sp16_ltb_h2','sp16_ltb_l_eff','E_norm','Ry_annex'],'sp16_n4_phi2_mono_current',r'\varphi_2=\psi_a(I_y/I_x)(2hh_2/l_{ef}^2)(E/R_y)','psi_a*(Iy/Ix)*(2*h*h2/lef^2)*(E/Ry)',[('psi_a','sp16_ltb_psi_a_effective'),('Iy','J_y'),('Ix','J_x'),('h','sp16_ltb_h_axes'),('h2','sp16_ltb_h2'),('lef','sp16_ltb_l_eff'),('E','E_norm'),('Ry','Ry_annex')])
piece('SP16_N4_C_LTB_PHI_B_DOUBLE_I_CURRENT','Текущий SP16: φb двоякосимметричного двутавра по Ж.1-Ж.2',[ref_formula('Ж.2','(Ж.1)','Ж'),ref_formula('Ж.2','(Ж.2)','Ж')],['sp16_n4_phi1_current'],'sp16_n4_phi_b_current',r'\varphi_b=\varphi_1\;(\varphi_1\le0.85);\ 0.68+0.21\varphi_1\le1\;(>0.85)',[('phi1','sp16_n4_phi1_current')],[{'when':cmp('sp16_n4_phi1_current','lte',0.85),'formula_latex':'phi1','expression':'phi1'},{'when':cmp('sp16_n4_phi1_current','gt',0.85),'formula_latex':'min(1,0.68+0.21phi1)','expression':'min(1,0.68+0.21*phi1)'}])
simple('SP16_N4_C_EQ69_CURRENT','Общая устойчивость при изгибе — (69)',[ref_formula('8.4.1','(69)')],['M_x','sp16_n4_phi_b_current','W_cx','Ry_annex','gamma_c_sp16'],'sp16_n4_eta69',r'\eta_{69}=M_x/(\varphi_bW_{cx}R_y\gamma_c)','abs(M)/(phib*Wc*Ry*gc)',[('M','M_x'),('phib','sp16_n4_phi_b_current'),('Wc','W_cx'),('Ry','Ry_annex'),('gc','gamma_c_sp16')])
# Local-stability screen quantity and exact Eq.92 representation.
simple('SP16_N4_C_LAMBDA_W','Условная гибкость стенки для 8.5',[ref_formula('8.5.1','unnumbered lambda_w definition')],['sp16_n4_hef','sp16_n4_tw','Ry_annex','E_norm'],'sp16_n4_lambda_w',r'\bar\lambda_w=(h_{ef}/t_w)\sqrt{R_y/E}','hef/tw*sqrt(Ry/E)',[('hef','sp16_n4_hef'),('tw','sp16_n4_tw'),('Ry','Ry_annex'),('E','E_norm')])
simple('SP16_N4_C_EQ92_CURRENT','Критическое местное напряжение — (92)',[ref_formula('8.5.12','(92)')],['sp16_n4_psi93','sp16_n4_mu1','Ry_annex','sp16_n4_lambda_a'],'sp16_n4_sigma_loc_cr1',r'\sigma_{loc,cr,1}=\psi(1.24+0.476\mu_1)R_y/\bar\lambda_a^2','psi*(1.24+0.476*mu1)*Ry/(la^2)',[('psi','sp16_n4_psi93'),('mu1','sp16_n4_mu1'),('Ry','Ry_annex'),('la','sp16_n4_lambda_a')],nt=notes(warning='NormCAD historical DSL was captured with first-power lambda_a in this route; current source requires lambda_a squared.'))

# Orchestration classification is deliberately coarse: detailed numerical branches remain atomic nodes/actions.
rules=[
 {'when':cmp('sp16_n4_beam_category','eq','crane_runway'),'output_value':'specialized','label':'8.3 dedicated crane route'},
 {'when':cmp('sp16_n4_beam_category','eq','bimetal'),'output_value':'specialized','label':'8.2.8 dedicated bimetal route'},
 {'when':allof(cmp('sp16_n4_beam_category','eq','ordinary'),cmp('sp16_n4_member_class','eq',1)),'output_value':'eq41','label':'ordinary class 1 baseline elastic route'},
 {'when':allof(cmp('sp16_n4_beam_category','eq','ordinary'),cmp('sp16_n4_member_class','eq',2)),'output_value':'eq50','label':'ordinary class 2 plastic route after applicability checks'},
 {'when':allof(cmp('sp16_n4_beam_category','eq','ordinary'),cmp('sp16_n4_member_class','eq',3)),'output_value':'eq50','label':'ordinary class 3 plastic-hinge route after applicability checks'}]
d['nodes'].append({'id':'SP16_N4_K_STRENGTH_ROUTE','node_type':'classification','owner_standard_id':'SP16_2017','title':'Stage N4 — выбор ветви прочности изгибаемого элемента','normative_refs':[ref_clause('8.1'),ref_clause('8.2')],'consumes':[bind(x) for x in ['sp16_n4_beam_category','sp16_n4_member_class','sp16_n4_load_is_static']],'produces':[bind('sp16_n4_strength_route','output')],'applicability':None,'notes':notes(limitations='Eq43/Eq51/Eq53 selection depends additionally on My/B and explicit point/applicability data; the runtime guided workflow performs those sub-branches and fails closed when data are absent.'),'output_quantity_id':'sp16_n4_strength_route','classification_rules':rules,'fallback_behavior':'error'});nids.add('SP16_N4_K_STRENGTH_ROUTE')

# Minimal trace edges.
def edge(fr,to,qs=None,etype='data',label=None):
    i=sum(1 for x in d['edges'] if x['id'].startswith('N4_E_'))+1
    d['edges'].append({'id':f'N4_E_{i:03d}','from_node_id':fr,'to_node_id':to,'edge_type':etype,'label':label,'condition':None,'quantity_ids':qs or []})
edge('SP16_N4_I_BEAM_STATE','SP16_N4_K_STRENGTH_ROUTE',['sp16_n4_beam_category','sp16_n4_member_class','sp16_n4_load_is_static'])
edge('SP16_C_LTB_ALPHA_J4','SP16_N4_C_LTB_PHI1_J3_RY',['sp16_ltb_alpha'])
edge('SP16_N4_C_LTB_PHI1_J3_RY','SP16_N4_C_LTB_PHI_B_DOUBLE_I_CURRENT',['sp16_n4_phi1_current'])
edge('SP16_N4_C_LTB_PHI_B_DOUBLE_I_CURRENT','SP16_N4_C_EQ69_CURRENT',['sp16_n4_phi_b_current'])
edge('SP16_N4_C_LAMBDA_W','SP16_N4_I_STABILITY_MODES',['sp16_n4_lambda_w'],'data','local stability screen context')

OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
import jsonschema
jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding='utf-8'))).validate(d)
print('schema PASS')
print('wrote',OUT)
print('sha256',hashlib.sha256(OUT.read_bytes()).hexdigest())
print('quantities',len(d['quantities']),'nodes',len(d['nodes']),'edges',len(d['edges']))
