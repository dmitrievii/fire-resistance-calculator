from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'normative_graph/dag_v0.3.31_stage_n2.json'
OUT=ROOT/'normative_graph/dag_v0.3.32_stage_n3.json'
SCHEMA=ROOT/'normative_graph/dag_schema.json'

d=json.loads(SRC.read_text(encoding='utf-8'))
d['graph_id']='sp16_sp554_dag_v0-3-32_stage_n3'
d['graph_title']='SP16/SP554 atomic normative DAG — Stage N3 axial members current-SP16 closure'
d['description']=(d.get('description') or '') + ' Stage N3 adds a current-SP16 axial-member route for 7.1/7.2: equation-(5) resistance branching, lambda/lambda_bar/phi equations (8)-(9), current equation (7a) with gamma_res, and branch-safe Table 8 formulas (12)-(17). The dedicated Stage N3 lambda_bar uses design Ry, not the separate SP554/Ryn invocation quantity.'

qids={q['id'] for q in d['quantities']}

def qnum(id,symbol,name,dim='dimensionless',unit='1',role='intermediate',source='FORMULA_RESULT', allowed=None):
    if id in qids: return
    d['quantities'].append({'id':id,'symbol':symbol,'name_ru':name,'data_type':'number','role':role,'physical_dimension':dim,'canonical_unit':unit,'allowed_units':allowed or [unit], 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden'}}); qids.add(id)

def qint(id,symbol,name,role='input',source='USER_INPUT'):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':symbol,'name_ru':name,'data_type':'integer','role':role,'physical_dimension':'count','canonical_unit':'1','allowed_units':['1'],'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'required_explicit' if source=='USER_INPUT' else 'forbidden'}}); qids.add(id)

def qbool(id,name):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':None,'name_ru':name,'data_type':'boolean','role':'input','physical_dimension':None,'canonical_unit':None,'allowed_units':[], 'source_policy':{'primary_source_type':'USER_INPUT','allowed_source_types':['USER_INPUT'],'override_policy':'required_explicit'}}); qids.add(id)

def qenum(id,name,vals,role='classification',source='CLASSIFICATION_RESULT'):
    if id in qids:return
    d['quantities'].append({'id':id,'symbol':None,'name_ru':name,'data_type':'enum','role':role,'physical_dimension':None,'canonical_unit':None,'allowed_units':[], 'source_policy':{'primary_source_type':source,'allowed_source_types':[source],'override_policy':'forbidden' if source!='USER_INPUT' else 'required_explicit'},'enum_values':[{'value':v,'label':lab} for v,lab in vals]}); qids.add(id)

qenum('sp16_n3_force_state','Центральное растяжение/сжатие',[('tension','растяжение'),('compression','сжатие')],role='input',source='USER_INPUT')
qbool('sp16_n3_post_yield_service_possible','Эксплуатация растянутого элемента возможна после достижения текучести')
qenum('sp16_n3_eq5_branch','Ветвь сопротивления формулы (5)',[('yield','Ry'),('ultimate','Ru/gamma_u')])
qnum('sp16_n3_eq5_eta_yield','η5,y','Использование формулы (5) по Ry',role='result')
qnum('sp16_n3_eq5_eta_ultimate','η5,u','Использование формулы (5) по Ru/gamma_u',role='result')
qnum('sp16_n3_lambda_geom','λ','Геометрическая гибкость Stage N3')
qnum('sp16_n3_lambda_bar','λ̄','Условная гибкость Stage N3 по расчетному Ry')
qnum('sp16_n3_delta','δ','Параметр δ формулы (9)')
qnum('sp16_n3_phi_raw','φraw','Коэффициент φ по формуле (8) до нормативных ограничений')
qnum('sp16_n3_phi','φ','Итоговый коэффициент устойчивости при центральном сжатии')
qnum('sp16_n3_eta7','η7','Использование формулы (7)',role='result')
qnum('sp16_n3_gamma_res_245','γres,245','γres по конечной ветви Ry=245 МПа')
qnum('sp16_n3_gamma_res_390','γres,390','γres по конечной ветви Ry=390 МПа')
qnum('sp16_n3_gamma_res','γres','Коэффициент учета распределения остаточных напряжений')
qnum('sp16_n3_eta7a','η7a','Использование формулы (7а)',role='result')
qint('sp16_n3_panel_count','n_pan','Число панелей сквозного стержня')
qenum('sp16_n3_connector_system','Система соединения ветвей',[('battens','планки'),('lattice','решетка')],role='input',source='USER_INPUT')
qint('sp16_n3_builtup_type',None,'Тип сквозного сечения по таблице 8')
qenum('sp16_n3_table8_route','Выбранная формула таблицы 8',[(f'eq{i}',f'формула ({i})') for i in range(12,18)])
# Table 8 inputs/outputs
for id,sym,name in [
 ('sp16_n3_lambda_y','λy','Гибкость сквозного стержня в целом по y'),('sp16_n3_lambda_max','λmax','Максимальная гибкость сквозного стержня в целом'),
 ('sp16_n3_lambda_b1','λb1','Гибкость ветви 1'),('sp16_n3_lambda_b2','λb2','Гибкость ветви 2'),('sp16_n3_lambda_b3','λb3','Гибкость ветви 3')]: qnum(id,sym,name,role='input',source='USER_INPUT')
for id,sym,name,dim,unit in [
 ('sp16_n3_Ib1','Ib1','Момент инерции ветви 1','inertia','mm4'),('sp16_n3_Ib2','Ib2','Момент инерции ветви 2','inertia','mm4'),('sp16_n3_Ib3','Ib3','Момент инерции ветви 3','inertia','mm4'),
 ('sp16_n3_Is','Is','Момент инерции планки','inertia','mm4'),('sp16_n3_Is1','Is1','Момент инерции планки в плоскости 1','inertia','mm4'),('sp16_n3_Is2','Is2','Момент инерции планки в плоскости 2','inertia','mm4'),
 ('sp16_n3_b','b','Расстояние между осями ветвей','length','mm'),('sp16_n3_b1','b1','Расстояние между осями ветвей b1','length','mm'),('sp16_n3_b2','b2','Расстояние между осями ветвей b2','length','mm'),('sp16_n3_lb','lb','Шаг/длина панели','length','mm'),('sp16_n3_d','d','Длина раскоса d','length','mm'),('sp16_n3_d1','d1','Длина раскоса d1','length','mm'),('sp16_n3_d2','d2','Длина раскоса d2','length','mm'),
 ('sp16_n3_Ad1','Ad1','Площадь раскосов в плоскости 1','area','mm2'),('sp16_n3_Ad2','Ad2','Площадь раскосов в плоскости 2','area','mm2'),('sp16_n3_Ad3','Ad3','Площадь раскосов одной грани','area','mm2')]: qnum(id,sym,name,dim,unit,role='input',source='USER_INPUT')
for i in range(12,18): qnum(f'sp16_n3_lambda_ef_eq{i}','λef',f'Приведенная гибкость по формуле ({i})')
qnum('sp16_n3_Qfic','Qfic','Условная поперечная сила по формуле (18)','force','N')

# node helpers
nids={n['id'] for n in d['nodes']}
def bind(qid,role='input'): return {'quantity_id':qid,'required':True,'binding_role':role}
def ref_formula(clause,formula,table=None,note=None):
    r={'standard_id':'SP16_2017','reference_kind':'formula','section':'7','clause':clause,'formula_ref':formula}
    if note:r['quote_or_note']=note
    return r
def ref_table(clause,table): return {'standard_id':'SP16_2017','reference_kind':'table','section':'7','clause':clause,'table_ref':table}
def notes(meaning=None,limitations=None,warning=None): return {'engineering_meaning':meaning,'limitations':limitations,'normative_warning':warning}
def simple(id,title,refs,inputs,output,latex,expr,bindings,app=None,nt=None):
    d['nodes'].append({'id':id,'node_type':'calculation','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[bind(x) for x in inputs],'produces':[bind(output,'output')],'applicability':app,'notes':nt or notes(),'calculation_spec':{'formula_type':'simple','formula_latex':latex,'expression':expr,'expression_language':'expr_v1','bindings':[{'variable':v,'quantity_id':q} for v,q in bindings],'rounding':{'mode':'none'}}}); nids.add(id)
def piece(id,title,refs,inputs,output,latex,bindings,cases,app=None,nt=None):
    d['nodes'].append({'id':id,'node_type':'calculation','owner_standard_id':'SP16_2017','title':title,'normative_refs':refs,'consumes':[bind(x) for x in inputs],'produces':[bind(output,'output')],'applicability':app,'notes':nt or notes(),'calculation_spec':{'formula_type':'piecewise','formula_latex':latex,'expression_language':'expr_v1','bindings':[{'variable':v,'quantity_id':q} for v,q in bindings],'cases':cases,'rounding':{'mode':'none'}}}); nids.add(id)
def cmp(q,op,val): return {'type':'comparison','quantity_id':q,'operator':op,'value':val}
def allof(*conds): return {'type':'all_of','conditions':list(conds)}

# Stage N3 explicit state inputs
for id,title,outs in [
 ('SP16_N3_I_AXIAL_STATE','Исходные branch-условия 7.1',[ 'sp16_n3_force_state','sp16_n3_post_yield_service_possible']),
 ('SP16_N3_I_BUILTUP_TOPOLOGY','Топология сквозного стержня для таблицы 8',['sp16_n3_panel_count','sp16_n3_connector_system','sp16_n3_builtup_type'])]:
    d['nodes'].append({'id':id,'node_type':'input','owner_standard_id':'SP16_2017','title':title,'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'clause','section':'7','clause':'7.1.1' if 'AXIAL' in id else '7.2.2'}],'consumes':[],'produces':[bind(x,'output') for x in outs],'applicability':None,'notes':notes(),'input_spec':{'input_method':'external_system','required':True,'user_prompt':title}})

# Eq 5 branch classification
rules=[
 {'when':allof(cmp('sp16_n3_force_state','eq','tension'),cmp('sp16_n3_post_yield_service_possible','eq',True)),'output_value':'ultimate','label':'растяжение с допустимой эксплуатацией после текучести'},
 {'when':cmp('fy_norm','gt',440.0),'output_value':'ultimate','label':'Ryn > 440'},
 {'when':cmp('fy_norm','lte',440.0),'output_value':'yield','label':'Ryn <= 440 и нет исключения'}]
d['nodes'].append({'id':'SP16_N3_K_EQ5_BRANCH','node_type':'classification','owner_standard_id':'SP16_2017','title':'Выбор сопротивления в формуле (5)','normative_refs':[ref_formula('7.1.1','(5) branch rule')],'consumes':[bind(x) for x in ['sp16_n3_force_state','sp16_n3_post_yield_service_possible','fy_norm']],'produces':[bind('sp16_n3_eq5_branch','output')],'applicability':None,'notes':notes(),'output_quantity_id':'sp16_n3_eq5_branch','classification_rules':rules,'fallback_behavior':'error'})

simple('SP16_N3_C_EQ5_YIELD','Формула (5) по Ry',[ref_formula('7.1.1','(5)')],['N_force','A_net','Ry_annex','gamma_c_sp16'],'sp16_n3_eq5_eta_yield',r'\eta_5=N/(A_nR_y\gamma_c)','N/(An*Ry*gc)',[('N','N_force'),('An','A_net'),('Ry','Ry_annex'),('gc','gamma_c_sp16')],app=cmp('sp16_n3_eq5_branch','eq','yield'))
simple('SP16_N3_C_EQ5_ULTIMATE','Формула (5) с заменой Ry на Ru/gamma_u',[ref_formula('7.1.1','(5), Ru/gamma_u branch')],['N_force','A_net','Ru_annex','gamma_u','gamma_c_sp16'],'sp16_n3_eq5_eta_ultimate',r'\eta_{5,u}=N\gamma_u/(A_nR_u\gamma_c)','N*gu/(An*Ru*gc)',[('N','N_force'),('gu','gamma_u'),('An','A_net'),('Ru','Ru_annex'),('gc','gamma_c_sp16')],app=cmp('sp16_n3_eq5_branch','eq','ultimate'))

simple('SP16_N3_C_LAMBDA','Геометрическая гибкость lambda=l_eff/i',[ref_formula('7.1.3','definition lambda=l_eff/i')],['l_eff','sp16_i_min'],'sp16_n3_lambda_geom',r'\lambda=l_{ef}/i','leff/i',[('leff','l_eff'),('i','sp16_i_min')])
simple('SP16_N3_C_LBAR_RY','Условная гибкость по расчетному Ry',[ref_formula('7.1.3','definition lambda_bar')],['sp16_n3_lambda_geom','Ry_annex','E_norm'],'sp16_n3_lambda_bar',r'\bar\lambda=\lambda\sqrt{R_y/E}','lam*sqrt(Ry/E)',[('lam','sp16_n3_lambda_geom'),('Ry','Ry_annex'),('E','E_norm')],nt=notes(warning='Stage N3 current-SP16 route intentionally uses design Ry. Do not substitute the separate SP554/Ryn invocation quantity.'))
simple('SP16_N3_C_DELTA9','Параметр delta по формуле (9)',[ref_formula('7.1.3','(9)')],['sp16_n3_lambda_bar','sp16_alpha_buckling','sp16_beta_buckling'],'sp16_n3_delta',r'\delta=9.87(1-\alpha+\beta\bar\lambda)+\bar\lambda^2','9.87*(1-alpha+beta*lbar)+(lbar^2)',[('alpha','sp16_alpha_buckling'),('beta','sp16_beta_buckling'),('lbar','sp16_n3_lambda_bar')])
simple('SP16_N3_C_PHI8_RAW','Коэффициент phi по формуле (8) до ограничений',[ref_formula('7.1.3','(8)')],['sp16_n3_delta','sp16_n3_lambda_bar'],'sp16_n3_phi_raw',r'\varphi=0.5(\delta-\sqrt{\delta^2-39.48\bar\lambda^2})/\bar\lambda^2','0.5*(delta-sqrt(delta^2-39.48*(lbar^2)))/(lbar^2)',[('delta','sp16_n3_delta'),('lbar','sp16_n3_lambda_bar')])
phi_cases=[
 {'when':allof(cmp('sp16_buckling_curve_type','in',['a','b']),cmp('sp16_n3_lambda_bar','lt',0.6)),'formula_latex':'\\varphi=1','expression':'1'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','a'),cmp('sp16_n3_lambda_bar','gte',3.8)),'formula_latex':'\\varphi=min(\\varphi_8,7.6/\\bar\\lambda^2)','expression':'min(phi_raw,7.6/(lbar^2))'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','b'),cmp('sp16_n3_lambda_bar','gte',4.4)),'formula_latex':'\\varphi=min(\\varphi_8,7.6/\\bar\\lambda^2)','expression':'min(phi_raw,7.6/(lbar^2))'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','c'),cmp('sp16_n3_lambda_bar','gte',5.8)),'formula_latex':'\\varphi=min(\\varphi_8,7.6/\\bar\\lambda^2)','expression':'min(phi_raw,7.6/(lbar^2))'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','a'),cmp('sp16_n3_lambda_bar','gte',0.6),cmp('sp16_n3_lambda_bar','lt',3.8)),'formula_latex':'\\varphi=\\varphi_8','expression':'phi_raw'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','b'),cmp('sp16_n3_lambda_bar','gte',0.6),cmp('sp16_n3_lambda_bar','lt',4.4)),'formula_latex':'\\varphi=\\varphi_8','expression':'phi_raw'},
 {'when':allof(cmp('sp16_buckling_curve_type','eq','c'),cmp('sp16_n3_lambda_bar','gte',0.4),cmp('sp16_n3_lambda_bar','lt',5.8)),'formula_latex':'\\varphi=\\varphi_8','expression':'phi_raw'}]
piece('SP16_N3_C_PHI_FINAL','Итоговый phi с правилами 7.1.3',[ref_formula('7.1.3','(8)-(9) with cap rule')],['sp16_n3_phi_raw','sp16_n3_lambda_bar','sp16_buckling_curve_type'],'sp16_n3_phi',r'\varphi=\varphi(\bar\lambda,\mathrm{type})',[('phi_raw','sp16_n3_phi_raw'),('lbar','sp16_n3_lambda_bar')],phi_cases,nt=notes(limitations='Type c below lambda_bar=0.4 is fail-closed in production.',warning='Current text says cap for values above 3.8/4.4/5.8; printed Table D.1 exact boundary nodes indicate the capped values. Production keeps the exact-table boundary policy and records this as SOURCE_AMBIGUITY.'))
simple('SP16_N3_C_EQ7','Устойчивость при центральном сжатии — формула (7)',[ref_formula('7.1.3','(7)')],['N_force','sp16_n3_phi','A_gross','Ry_annex','gamma_c_sp16'],'sp16_n3_eta7',r'\eta_7=N/(\varphi A R_y\gamma_c)','N/(phi*A*Ry*gc)',[('N','N_force'),('phi','sp16_n3_phi'),('A','A_gross'),('Ry','Ry_annex'),('gc','gamma_c_sp16')])
# gamma_res endpoints and interpolation
piece('SP16_N3_C_GAMMA_RES_245','gamma_res при Ry=245 МПа',[ref_formula('7.1.3','(7a) gamma_res rule')],['sp16_n3_lambda_bar'],'sp16_n3_gamma_res_245',r'\gamma_{res,245}=1\;(\bar\lambda\le3);\;0.1\bar\lambda+0.7\;(>3)',[('lbar','sp16_n3_lambda_bar')],[{'when':cmp('sp16_n3_lambda_bar','lte',3.0),'formula_latex':'1','expression':'1'},{'when':cmp('sp16_n3_lambda_bar','gt',3.0),'formula_latex':'0.1\\bar\\lambda+0.7','expression':'0.1*lbar+0.7'}])
piece('SP16_N3_C_GAMMA_RES_390','gamma_res при Ry=390 МПа',[ref_formula('7.1.3','(7a) gamma_res rule')],['sp16_n3_lambda_bar'],'sp16_n3_gamma_res_390',r'\gamma_{res,390}=1\;(\bar\lambda\le5);\;0.2\bar\lambda+0.9\;(>5)',[('lbar','sp16_n3_lambda_bar')],[{'when':cmp('sp16_n3_lambda_bar','lte',5.0),'formula_latex':'1','expression':'1'},{'when':cmp('sp16_n3_lambda_bar','gt',5.0),'formula_latex':'0.2\\bar\\lambda+0.9','expression':'0.2*lbar+0.9'}],nt=notes(warning='Literal current consolidated source transcription retained: 0.2*lambda_bar+0.9 above 5.'))
gres_cases=[
 {'when':cmp('Ry_annex','lte',245.0),'formula_latex':'\\gamma_{res}=\\gamma_{res,245}','expression':'g245'},
 {'when':cmp('Ry_annex','gte',390.0),'formula_latex':'\\gamma_{res}=\\gamma_{res,390}','expression':'g390'},
 {'when':allof(cmp('Ry_annex','gt',245.0),cmp('Ry_annex','lt',390.0)),'formula_latex':'\\gamma_{res}=\\gamma_{245}+(R_y-245)(\\gamma_{390}-\\gamma_{245})/145','expression':'g245+(Ry-245)*(g390-g245)/145'}]
piece('SP16_N3_C_GAMMA_RES','Интерполяция gamma_res по Ry',[ref_formula('7.1.3','(7a) gamma_res interpolation')],['Ry_annex','sp16_n3_gamma_res_245','sp16_n3_gamma_res_390'],'sp16_n3_gamma_res',r'\gamma_{res}=f(R_y,\bar\lambda)',[('Ry','Ry_annex'),('g245','sp16_n3_gamma_res_245'),('g390','sp16_n3_gamma_res_390')],gres_cases)
simple('SP16_N3_C_EQ7A','Прокатный двутавр — формула (7а)',[ref_formula('7.1.3','(7a)')],['N_force','sp16_n3_gamma_res','sp16_n3_phi','A_gross','Ry_annex','gamma_c_sp16'],'sp16_n3_eta7a',r'\eta_{7a}=N/(\gamma_{res}\varphi A R_y\gamma_c)','N/(gres*phi*A*Ry*gc)',[('N','N_force'),('gres','sp16_n3_gamma_res'),('phi','sp16_n3_phi'),('A','A_gross'),('Ry','Ry_annex'),('gc','gamma_c_sp16')],nt=notes(meaning='Optional current-SP16 rolled-I central-compression route.'))

# Table 8 route classifier: section type x connector, Table route only for >=6 panels
r=[]
for typ in (1,2,3):
 for conn,eq in [('battens',11+typ),('lattice',14+typ)]:
  r.append({'when':allof(cmp('sp16_n3_panel_count','gte',6),cmp('sp16_n3_builtup_type','eq',typ),cmp('sp16_n3_connector_system','eq',conn)),'output_value':f'eq{eq}','label':f'type {typ} / {conn} -> ({eq})'})
d['nodes'].append({'id':'SP16_N3_K_TABLE8_ROUTE','node_type':'classification','owner_standard_id':'SP16_2017','title':'Выбор единственной формулы таблицы 8','normative_refs':[ref_table('7.2.2','8')],'consumes':[bind(x) for x in ['sp16_n3_panel_count','sp16_n3_connector_system','sp16_n3_builtup_type']],'produces':[bind('sp16_n3_table8_route','output')],'applicability':cmp('sp16_n3_panel_count','gte',6),'notes':notes(limitations='For fewer than six panels Table 8 is not used: battens require frame-system analysis; lattice routes to 7.2.5.'),'output_quantity_id':'sp16_n3_table8_route','classification_rules':r,'fallback_behavior':'error'})
# Table 8 formula calculations
simple('SP16_N3_C_EQ12','Таблица 8 — формула (12)',[ref_formula('7.2.2','(12)'),ref_table('7.2.2','8')],['sp16_n3_lambda_y','sp16_n3_lambda_b1','sp16_n3_Ib1','sp16_n3_b','sp16_n3_Is','sp16_n3_lb'],'sp16_n3_lambda_ef_eq12',r'\lambda_{ef}=\sqrt{\lambda_y^2+0.82(1+n)\lambda_{b1}^2},\ n=I_{b1}b/(I_sl_b)','sqrt(ly^2+0.82*(1+(Ib1*b/(Is*lb)))*(lb1^2))',[('ly','sp16_n3_lambda_y'),('lb1','sp16_n3_lambda_b1'),('Ib1','sp16_n3_Ib1'),('b','sp16_n3_b'),('Is','sp16_n3_Is'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq12'))
simple('SP16_N3_C_EQ13','Таблица 8 — формула (13)',[ref_formula('7.2.2','(13)'),ref_table('7.2.2','8')],['sp16_n3_lambda_max','sp16_n3_lambda_b1','sp16_n3_lambda_b2','sp16_n3_Ib1','sp16_n3_Ib2','sp16_n3_b1','sp16_n3_b2','sp16_n3_Is1','sp16_n3_Is2','sp16_n3_lb'],'sp16_n3_lambda_ef_eq13',r'\lambda_{ef}=\sqrt{\lambda_{max}^2+0.82[(1+n_1)\lambda_{b1}^2+(1+n_2)\lambda_{b2}^2]}','sqrt(lmax^2+0.82*((1+Ib1*b1/(Is1*lb))*(lb1^2)+(1+Ib2*b2/(Is2*lb))*(lb2^2)))',[('lmax','sp16_n3_lambda_max'),('lb1','sp16_n3_lambda_b1'),('lb2','sp16_n3_lambda_b2'),('Ib1','sp16_n3_Ib1'),('Ib2','sp16_n3_Ib2'),('b1','sp16_n3_b1'),('b2','sp16_n3_b2'),('Is1','sp16_n3_Is1'),('Is2','sp16_n3_Is2'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq13'))
simple('SP16_N3_C_EQ14','Таблица 8 — формула (14)',[ref_formula('7.2.2','(14)'),ref_table('7.2.2','8')],['sp16_n3_lambda_max','sp16_n3_lambda_b3','sp16_n3_Ib3','sp16_n3_b','sp16_n3_Is','sp16_n3_lb'],'sp16_n3_lambda_ef_eq14',r'\lambda_{ef}=\sqrt{\lambda_{max}^2+0.82(1+3n_3)\lambda_{b3}^2}','sqrt(lmax^2+0.82*(1+3*Ib3*b/(Is*lb))*(lb3^2))',[('lmax','sp16_n3_lambda_max'),('lb3','sp16_n3_lambda_b3'),('Ib3','sp16_n3_Ib3'),('b','sp16_n3_b'),('Is','sp16_n3_Is'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq14'))
simple('SP16_N3_C_EQ15','Таблица 8 — формула (15)',[ref_formula('7.2.2','(15)'),ref_table('7.2.2','8')],['sp16_n3_lambda_y','A_gross','sp16_n3_Ad1','sp16_n3_d','sp16_n3_b','sp16_n3_lb'],'sp16_n3_lambda_ef_eq15',r'\lambda_{ef}=\sqrt{\lambda_y^2+\alpha A/A_{d1}},\ \alpha=10d^3/(b^2l_b)','sqrt(ly^2+(10*d^3/(b^2*lb))*A/Ad1)',[('ly','sp16_n3_lambda_y'),('A','A_gross'),('Ad1','sp16_n3_Ad1'),('d','sp16_n3_d'),('b','sp16_n3_b'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq15'))
simple('SP16_N3_C_EQ16','Таблица 8 — формула (16)',[ref_formula('7.2.2','(16)'),ref_table('7.2.2','8')],['sp16_n3_lambda_max','A_gross','sp16_n3_Ad1','sp16_n3_Ad2','sp16_n3_d1','sp16_n3_d2','sp16_n3_b1','sp16_n3_b2','sp16_n3_lb'],'sp16_n3_lambda_ef_eq16',r'\lambda_{ef}=\sqrt{\lambda_{max}^2+(\alpha_1+\alpha_2A_{d1}/A_{d2})A/A_{d1}}','sqrt(lmax^2+((10*d1^3/(b1^2*lb))+(10*d2^3/(b2^2*lb))*Ad1/Ad2)*A/Ad1)',[('lmax','sp16_n3_lambda_max'),('A','A_gross'),('Ad1','sp16_n3_Ad1'),('Ad2','sp16_n3_Ad2'),('d1','sp16_n3_d1'),('d2','sp16_n3_d2'),('b1','sp16_n3_b1'),('b2','sp16_n3_b2'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq16'))
simple('SP16_N3_C_EQ17','Таблица 8 — формула (17)',[ref_formula('7.2.2','(17)'),ref_table('7.2.2','8')],['sp16_n3_lambda_max','A_gross','sp16_n3_Ad3','sp16_n3_d','sp16_n3_b','sp16_n3_lb'],'sp16_n3_lambda_ef_eq17',r'\lambda_{ef}=\sqrt{\lambda_{max}^2+0.67\alpha A/A_{d3}},\ \alpha=10d^3/(b^2l_b)','sqrt(lmax^2+0.67*(10*d^3/(b^2*lb))*A/Ad3)',[('lmax','sp16_n3_lambda_max'),('A','A_gross'),('Ad3','sp16_n3_Ad3'),('d','sp16_n3_d'),('b','sp16_n3_b'),('lb','sp16_n3_lb')],app=cmp('sp16_n3_table8_route','eq','eq17'))
simple('SP16_N3_C_EQ18_QFIC','Условная поперечная сила Qfic — формула (18)',[ref_formula('7.2.7','(18)')],['E_norm','Ry_annex','N_force','sp16_n3_phi'],'sp16_n3_Qfic',r'Q_{fic}=7.15\cdot10^{-6}(2330-E/R_y)N/\varphi','7.15e-6*(2330-E/Ry)*N/phi',[('E','E_norm'),('Ry','Ry_annex'),('N','N_force'),('phi','sp16_n3_phi')],app=cmp('sp16_n3_force_state','eq','compression'))

# Data/control edges for the main solid chain and table-8 selector.
def edge(fr,to,etype='data',qs=None,label=None,condition=None):
    eid=f'N3_E_{len([x for x in d["edges"] if x["id"].startswith("N3_E_")])+1:03d}'
    d['edges'].append({'id':eid,'from_node_id':fr,'to_node_id':to,'edge_type':etype,'label':label,'condition':condition,'quantity_ids':qs or []})
edge('SP16_N3_I_AXIAL_STATE','SP16_N3_K_EQ5_BRANCH','data',['sp16_n3_force_state','sp16_n3_post_yield_service_possible'])
edge('SP16_N3_C_LAMBDA','SP16_N3_C_LBAR_RY','data',['sp16_n3_lambda_geom'])
edge('SP16_N3_C_LBAR_RY','SP16_N3_C_DELTA9','data',['sp16_n3_lambda_bar'])
edge('SP16_L_TABLE7','SP16_N3_C_DELTA9','data',['sp16_alpha_buckling','sp16_beta_buckling'])
edge('SP16_N3_C_DELTA9','SP16_N3_C_PHI8_RAW','data',['sp16_n3_delta'])
edge('SP16_N3_C_PHI8_RAW','SP16_N3_C_PHI_FINAL','data',['sp16_n3_phi_raw'])
edge('SP16_N3_C_LBAR_RY','SP16_N3_C_GAMMA_RES_245','data',['sp16_n3_lambda_bar'])
edge('SP16_N3_C_LBAR_RY','SP16_N3_C_GAMMA_RES_390','data',['sp16_n3_lambda_bar'])
edge('SP16_N3_C_GAMMA_RES_245','SP16_N3_C_GAMMA_RES','data',['sp16_n3_gamma_res_245'])
edge('SP16_N3_C_GAMMA_RES_390','SP16_N3_C_GAMMA_RES','data',['sp16_n3_gamma_res_390'])
edge('SP16_N3_C_PHI_FINAL','SP16_N3_C_EQ7','data',['sp16_n3_phi'])
edge('SP16_N3_C_GAMMA_RES','SP16_N3_C_EQ7A','data',['sp16_n3_gamma_res'])
edge('SP16_N3_C_PHI_FINAL','SP16_N3_C_EQ7A','data',['sp16_n3_phi'])
edge('SP16_N3_I_BUILTUP_TOPOLOGY','SP16_N3_K_TABLE8_ROUTE','data',['sp16_n3_panel_count','sp16_n3_connector_system','sp16_n3_builtup_type'])

OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
try:
 import jsonschema
 jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding='utf-8'))).validate(d)
 print('schema PASS')
except Exception as e:
 print('schema FAIL',e)
 raise
print('wrote',OUT)
print('sha256',hashlib.sha256(OUT.read_bytes()).hexdigest())
print('quantities',len(d['quantities']),'nodes',len(d['nodes']),'edges',len(d['edges']))
