from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.68_sp16_mech8_mq_torsion_scope.json'
OUT=ROOT/'normative_graph/dag_v0.3.69_sp16_mech9_remaining_ambient_closure.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
qs={q['id']:q for q in g['quantities']}; ns={n['id']:n for n in g['nodes']}; es={e['id']:e for e in g['edges']}

annex_k=json.loads((ROOT/'data/annex_k_table_k1_fatigue_groups.json').read_text(encoding='utf-8'))
ANNEX_K_IDS=[str(row['case_id']) for row in annex_k['entries']]

def qdef(qid,name,role='result',dtype='object',enum_values=None,source='CALCULATED',unit=None):
    q={'id':qid,'symbol':None,'name_ru':name,'data_type':dtype,'role':role,'physical_dimension':None,'canonical_unit':unit,'allowed_units':[] if unit is None else [unit],
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
def allof(*conds): return {'type':'all_of','conditions':list(conds)}
def anyof(*conds): return {'type':'any_of','conditions':list(conds)}

# Class-3 explicit confirmations.
for qid,label in [
 ('sp16_mech9_c3_clause_8_2_5_confirmed','SP16-MECH9 — класс 3: выполнен п.8.2.5'),
 ('sp16_mech9_c3_clause_8_4_6_confirmed','SP16-MECH9 — класс 3: выполнен п.8.4.6'),
 ('sp16_mech9_c3_clause_8_5_8_confirmed','SP16-MECH9 — класс 3: выполнен п.8.5.8'),
 ('sp16_mech9_c3_clause_8_5_9_confirmed','SP16-MECH9 — класс 3: выполнен п.8.5.9'),
 ('sp16_mech9_c3_clause_8_5_18_confirmed','SP16-MECH9 — класс 3: выполнен п.8.5.18'),
 ('sp16_mech9_c3_max_moment_shear_effect_confirmed','SP16-MECH9 — класс 3: влияние Q учтено в сечениях максимального M'),
]: addq(qdef(qid,label,role='input',dtype='boolean',source='USER_INPUT'))

# N9 primary ordinary-fatigue authoring.
addq(qdef('sp16_mech9_fatigue_route_kind','SP16-MECH9 — маршрут усталости',role='decision_state',dtype='enum',enum_values=['ordinary_fatigue_12_1_2','crane_runway_12_2','low_cycle_lt_1e5_12_1_1'],source='USER_INPUT'))
for q in [
 qdef('sp16_mech9_fatigue_load_cycles','SP16-MECH9 — число циклов n',role='input',dtype='number',source='USER_INPUT',unit='1'),
 qdef('sp16_mech9_fatigue_resonant_vortex_excitation','SP16-MECH9 — резонансное вихревое возбуждение',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_sp20_load_basis_confirmed','SP16-MECH9 — нагрузки определены по СП20',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_net_stress_basis_confirmed','SP16-MECH9 — напряжения в нетто-сечении без динамических и stability коэффициентов',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_same_loading_extremes_confirmed','SP16-MECH9 — σmin и σmax от одного загружения',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_annex_k_case_confirmed','SP16-MECH9 — случай приложения К выбран и подтвержден',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_annex_k_case_id','SP16-MECH9 — случай таблицы К.1',role='input',dtype='enum',enum_values=ANNEX_K_IDS,source='USER_INPUT'),
 qdef('sp16_mech9_fatigue_sigma_max','SP16-MECH9 — максимальное signed напряжение σmax',role='input',dtype='number',source='USER_INPUT',unit='MPa'),
 qdef('sp16_mech9_fatigue_sigma_min','SP16-MECH9 — минимальное signed напряжение σmin',role='input',dtype='number',source='USER_INPUT',unit='MPa'),
]: addq(q)

# N10 base classification and prevention inputs.
for q in [
 qdef('sp16_mech9_brittle_welded_structure','SP16-MECH9 — конструкция сварная',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_steel_selection_confirmed','SP16-MECH9 — выбор стали по 5.2 / таблице В.1 подтвержден',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_stress_concentration_confirmed','SP16-MECH9 — меры по снижению концентрации/наклепа подтверждены',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_solid_web_lattice_considered','SP16-MECH9 — различие сплошностенчатых/решетчатых деталей учтено',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_cover_plate_flank_welds','SP16-MECH9 — есть стык накладкой с фланговыми швами',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_guillotine_or_punched','SP16-MECH9 — применена гильотинная резка или пробивка отверстий',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_secondary_gusset','SP16-MECH9 — фасонка второстепенной детали к растянутому элементу',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_steel_grade_number','SP16-MECH9 — числовой класс/марка стали для screening §13.3',role='input',dtype='number',source='USER_INPUT',unit='MPa'),
 qdef('sp16_mech9_brittle_joint_type','SP16-MECH9 — тип сварного соединения для screening §13.3',role='input',dtype='enum',enum_values=['tee','corner','full_penetration','other_welded'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_through_thickness_tension','SP16-MECH9 — растяжение по толщине проката',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_13_3_review_confirmed','SP16-MECH9 — инженерная оценка применимости §13.3 выполнена',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_lamellar_required','SP16-MECH9 — требуется расчет ламеллярного разрушения §13.3–13.5',role='decision_state',dtype='boolean',source='USER_INPUT'),
 # conditional prevention details; supplied in one compact secondary card
 qdef('sp16_mech9_brittle_weld_sigma_t','SP16-MECH9 — растягивающее напряжение в зоне шва',role='input',dtype='number',source='USER_INPUT',unit='MPa'),
 qdef('sp16_mech9_brittle_enhanced_ndt_confirmed','SP16-MECH9 — усиленный НК при σt>0.4Ry подтвержден',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_weld_intersections_avoided','SP16-MECH9 — пересечения сварных швов исключены',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_runoff_tabs_ndt_confirmed','SP16-MECH9 — выводные планки/НК швов подтверждены',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_flank_termination','SP16-MECH9 — выпуск флангового шва с каждой стороны',role='input',dtype='number',source='USER_INPUT',unit='mm'),
 qdef('sp16_mech9_brittle_min_thickness_confirmed','SP16-MECH9 — минимальная толщина при гильотине/пробивке подтверждена',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_gusset_bolted_confirmed','SP16-MECH9 — второстепенная фасонка закреплена болтами',role='input',dtype='boolean',source='USER_INPUT'),
]: addq(q)

# N10 lamellar detailed route.
for q in [
 qdef('sp16_mech9_brittle_z_test_available','SP16-MECH9 — есть подтвержденные испытания/Z-свойства по толщине',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_z_certificate_confirmed','SP16-MECH9 — сертификат выбранной Z-группы подтвержден',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_connection_form_case','SP16-MECH9 — форма соединения по таблице 37',role='input',dtype='enum',enum_values=['no_z_direction_stress','symmetric_corner_fillet','intermediate_buttering_layer','ordinary_t_fillet','t_full_or_partial_penetration','fillet_near_free_plate_edge','corner_full_penetration'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_risk_weld_leg','SP16-MECH9 — катет шва для таблицы 37',role='input',dtype='number',source='USER_INPUT',unit='mm'),
 qdef('sp16_mech9_brittle_restraint_level','SP16-MECH9 — степень стеснения деформаций',role='input',dtype='enum',enum_values=['low_free_shrinkage','medium_partial_shrinkage','high_rigid_no_shrinkage'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_pass_count','SP16-MECH9 — число проходов',role='input',dtype='enum',enum_values=['one','multiple'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_weld_sequence','SP16-MECH9 — последовательность сварки',role='input',dtype='enum',enum_values=['alternating_sides','one_side_then_other'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_preheat','SP16-MECH9 — предварительный подогрев',role='input',dtype='enum',enum_values=['without_preheat','with_preheat'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_through_thickness_action','SP16-MECH9 — характер воздействия по толщине',role='input',dtype='enum',enum_values=['none','static_compression','dynamic_or_vibratory'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_construction_group','SP16-MECH9 — группа конструкции',role='input',dtype='enum',enum_values=['1','2','3','4'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_consequence_class','SP16-MECH9 — класс последствий',role='input',dtype='enum',enum_values=['KS-1','KS-2','KS-3'],source='USER_INPUT'),
 qdef('sp16_mech9_brittle_special_flange_or_normal_force','SP16-MECH9 — условие п.15.9.10 / сила нормальна плоскости проката',role='input',dtype='boolean',source='USER_INPUT'),
 qdef('sp16_mech9_brittle_selected_z_group','SP16-MECH9 — выбранная Z-группа',role='input',dtype='enum',enum_values=['Z15','Z25','Z35'],source='USER_INPUT'),
]: addq(q)

for q in [
 qdef('sp16_mech9_primary_evidence','SP16-MECH9 — cumulative ambient evidence после class-3/N9/N10 closure'),
 qdef('sp16_mech9_class3_mq_binding_complete','SP16-MECH9 — class-3 M+Q binding resolved',dtype='boolean'),
 qdef('sp16_mech9_n9_primary_execution_complete','SP16-MECH9 — required N9 primary route resolved',dtype='boolean'),
 qdef('sp16_mech9_n10_primary_execution_complete','SP16-MECH9 — required N10 primary route resolved',dtype='boolean'),
]: addq(q)

addn({
 'id':'SP16_I_MECH9_CLASS3_CONTEXT','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — условия применения M+Q для сечения 3-го класса',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'clause','section':'8.2.7','quote_or_note':'Class-3 plastic-hinge route requires explicit confirmations of 8.2.5, 8.4.6, 8.5.8, 8.5.9, 8.5.18 and shear effect at maximum-moment sections.'}],
 'consumes':[{'quantity_id':'sp16_mech8_primary_evidence','required':True,'binding_role':'evidence'}],
 'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in [
   'sp16_mech9_c3_clause_8_2_5_confirmed','sp16_mech9_c3_clause_8_4_6_confirmed','sp16_mech9_c3_clause_8_5_8_confirmed','sp16_mech9_c3_clause_8_5_9_confirmed','sp16_mech9_c3_clause_8_5_18_confirmed','sp16_mech9_c3_max_moment_shear_effect_confirmed']],
 'applicability':None,
 'input_specs':{qid:{'label':qs[qid]['name_ru'],'widget':'boolean'} for qid in [
   'sp16_mech9_c3_clause_8_2_5_confirmed','sp16_mech9_c3_clause_8_4_6_confirmed','sp16_mech9_c3_clause_8_5_8_confirmed','sp16_mech9_c3_clause_8_5_9_confirmed','sp16_mech9_c3_clause_8_5_18_confirmed','sp16_mech9_c3_max_moment_shear_effect_confirmed']},
 'notes':{'engineering_meaning':'Explicit class-3 routing gate; confirmations are not inferred from stress recovery.','limitations':'Current qualified route is one-plane Mx+Qx only.','normative_warning':'Any unconfirmed referenced clause keeps M+Q fail-closed.'}
})

addn({
 'id':'SP16_D_MECH9_FATIGUE_ROUTE','node_type':'decision','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — маршрут проверки усталости',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'section','section':'12','quote_or_note':'Select ordinary fatigue, crane-runway fatigue, or the current low-cycle external-method boundary.'}],
 'consumes':[{'quantity_id':'sp16_mech8_primary_evidence','required':True,'binding_role':'evidence'}],
 'produces':[{'quantity_id':'sp16_mech9_fatigue_route_kind','required':True,'binding_role':'output'}],
 'applicability':cmp('sp16_mech7_fatigue_required','eq',True),
 'question':'Какой маршрут раздела 12 требуется для этого элемента?',
 'decision_quantity_id':'sp16_mech9_fatigue_route_kind',
 'options':[
   {'value':'ordinary_fatigue_12_1_2','label':'Обычная усталость — §12.1.2','description':'MECH9 выполнит qualified N9 route автоматически.'},
   {'value':'crane_runway_12_2','label':'Подкрановая балка — §12.2','description':'Пока требуется специализированный N9 crane route; primary gate останется fail-closed.'},
   {'value':'low_cycle_lt_1e5_12_1_1','label':'n < 10^5 — low-cycle boundary','description':'Текущий СП16 не содержит заменяющей формулы после исключения 12.1.3; требуется внешний метод.'},
 ],
 'notes':{'engineering_meaning':'Routes an applicable fatigue context into the correct current-SP16 procedure.','limitations':'MECH9 auto-executes only ordinary 12.1.2.','normative_warning':'Crane and low-cycle routes are not silently reduced to ordinary fatigue.'}
})

fatigue_fields=['sp16_mech9_fatigue_load_cycles','sp16_mech9_fatigue_resonant_vortex_excitation','sp16_mech9_fatigue_sp20_load_basis_confirmed','sp16_mech9_fatigue_net_stress_basis_confirmed','sp16_mech9_fatigue_same_loading_extremes_confirmed','sp16_mech9_fatigue_annex_k_case_confirmed','sp16_mech9_fatigue_annex_k_case_id','sp16_mech9_fatigue_sigma_max','sp16_mech9_fatigue_sigma_min']
addn({
 'id':'SP16_I_MECH9_FATIGUE_ORDINARY','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — обычная усталость §12.1.2',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'section','section':'12.1.2','quote_or_note':'Equations (170)-(172), Tables 35-36 and Annex K classification require explicit cyclic-stress and detail data.'}],
 'consumes':[{'quantity_id':'sp16_mech9_fatigue_route_kind','required':True,'binding_role':'input'},{'quantity_id':'fu_norm','required':True,'binding_role':'input'},{'quantity_id':'Ru_formula','required':True,'binding_role':'input'},{'quantity_id':'gamma_u','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in fatigue_fields],
 'applicability':cmp('sp16_mech9_fatigue_route_kind','eq','ordinary_fatigue_12_1_2'),
 'input_specs':{qid:{'label':qs[qid]['name_ru'],'widget':'select' if qs[qid]['data_type']=='enum' else 'boolean' if qs[qid]['data_type']=='boolean' else 'number'} for qid in fatigue_fields},
 'notes':{'engineering_meaning':'Supplies the explicit Stage-N9 ordinary-fatigue inputs that cannot be inferred from the static ambient load case.','limitations':'Stress extrema are entered from the cyclic structural/load analysis.','normative_warning':'Annex K detail classification and SP20 load basis must be explicitly confirmed.'}
})

brittle_base=['sp16_mech9_brittle_welded_structure','sp16_mech9_brittle_steel_selection_confirmed','sp16_mech9_brittle_stress_concentration_confirmed','sp16_mech9_brittle_solid_web_lattice_considered','sp16_mech9_brittle_cover_plate_flank_welds','sp16_mech9_brittle_guillotine_or_punched','sp16_mech9_brittle_secondary_gusset','sp16_mech9_brittle_steel_grade_number','sp16_mech9_brittle_joint_type','sp16_mech9_brittle_through_thickness_tension','sp16_mech9_brittle_13_3_review_confirmed','sp16_mech9_brittle_lamellar_required']
addn({
 'id':'SP16_I_MECH9_BRITTLE_BASE','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — Section 13: основные условия',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'section','section':'13.1-13.3','quote_or_note':'General brittle-fracture prevention and lamellar-tearing applicability require explicit project/detail classifications.'}],
 'consumes':[{'quantity_id':'sp16_mech8_primary_evidence','required':True,'binding_role':'evidence'},{'quantity_id':'Ry_formula','required':True,'binding_role':'input'},{'quantity_id':'governing_product_thickness_mm','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in brittle_base],
 'applicability':cmp('sp16_mech7_brittle_required','eq',True),
 'input_specs':{qid:{'label':qs[qid]['name_ru'],'widget':'select' if qs[qid]['data_type']=='enum' else 'boolean' if qs[qid]['data_type']=='boolean' else 'number'} for qid in brittle_base},
 'notes':{'engineering_meaning':'Primary Section-13 classification without hiding project-specific detail information.','limitations':'Conditional prevention details are supplied on the next card.','normative_warning':'The §13.3 engineering review must be explicit.'}
})

brittle_cond=['sp16_mech9_brittle_weld_sigma_t','sp16_mech9_brittle_enhanced_ndt_confirmed','sp16_mech9_brittle_weld_intersections_avoided','sp16_mech9_brittle_runoff_tabs_ndt_confirmed','sp16_mech9_brittle_flank_termination','sp16_mech9_brittle_min_thickness_confirmed','sp16_mech9_brittle_gusset_bolted_confirmed']
addn({
 'id':'SP16_I_MECH9_BRITTLE_CONDITIONAL','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — Section 13: условные конструктивные требования',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'clause','section':'13.2','quote_or_note':'Weld/NDT, cover-plate, cutting and gusset requirements are applied only when their project condition is present.'}],
 'consumes':[{'quantity_id':qid,'required':True,'binding_role':'input'} for qid in ['sp16_mech9_brittle_welded_structure','sp16_mech9_brittle_cover_plate_flank_welds','sp16_mech9_brittle_guillotine_or_punched','sp16_mech9_brittle_secondary_gusset']],
 # Required on the UI card for deterministic authoring; irrelevant values are ignored by the N10 workflow.
 'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in brittle_cond],
 'applicability':cmp('sp16_mech7_brittle_required','eq',True),
 'input_specs':{qid:{'label':qs[qid]['name_ru'],'widget':'boolean' if qs[qid]['data_type']=='boolean' else 'number'} for qid in brittle_cond},
 'notes':{'engineering_meaning':'Collects compact conditional Section-13 confirmations; values for non-applicable conditions are ignored by the qualified N10 workflow.','limitations':'The card is intentionally explicit rather than guessing fabrication/detail state.','normative_warning':'For applicable conditions, false confirmations produce FAIL rather than N.A.'}
})

lamellar=['sp16_mech9_brittle_z_test_available','sp16_mech9_brittle_z_certificate_confirmed','sp16_mech9_brittle_connection_form_case','sp16_mech9_brittle_risk_weld_leg','sp16_mech9_brittle_restraint_level','sp16_mech9_brittle_pass_count','sp16_mech9_brittle_weld_sequence','sp16_mech9_brittle_preheat','sp16_mech9_brittle_through_thickness_action','sp16_mech9_brittle_construction_group','sp16_mech9_brittle_consequence_class','sp16_mech9_brittle_special_flange_or_normal_force','sp16_mech9_brittle_selected_z_group']
addn({
 'id':'SP16_I_MECH9_BRITTLE_LAMELLAR','node_type':'input','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — ламеллярное разрушение §13.3–13.5',
 'normative_refs':[{'standard_id':'SP16_2017','reference_kind':'equation_table','section':'13.3-13.5','quote_or_note':'Equation (174), Table 37 and Z-quality routing require explicit detail, restraint, welding and certificate data.'}],
 'consumes':[{'quantity_id':'sp16_mech9_brittle_lamellar_required','required':True,'binding_role':'input'}],
 'produces':[{'quantity_id':qid,'required':True,'binding_role':'output'} for qid in lamellar],
 'applicability':cmp('sp16_mech9_brittle_lamellar_required','eq',True),
 'input_specs':{qid:{'label':qs[qid]['name_ru'],'widget':'select' if qs[qid]['data_type']=='enum' else 'boolean' if qs[qid]['data_type']=='boolean' else 'number'} for qid in lamellar},
 'notes':{'engineering_meaning':'Executes the existing qualified Stage-N10 lamellar-tearing route in the primary ambient flow.','limitations':'Certificate/test evidence remains an explicit user/project input.','normative_warning':'Missing Z evidence is fail-closed.'}
})

binder_inputs=[
 'sp16_mech8_primary_evidence','sp16_applicability_census','sp16_section_class',
 'ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment',
 'section_geometry_2d_normalized','ambient_axis_shear_state','W_xn_min','Ry_formula','Rs_formula','fy_norm','gamma_c_bending_strength',
 'sp16_mech8_annex_e1_section_type','sp16_mech8_equivalent_load_safety_factor','sp16_mech8_is_support_section',
 'sp16_mech7_fatigue_required','sp16_mech7_brittle_required','fu_norm','Ru_formula','gamma_u','governing_product_thickness_mm',
] + [q for q in qs if q.startswith('sp16_mech9_') and q not in {'sp16_mech9_primary_evidence','sp16_mech9_class3_mq_binding_complete','sp16_mech9_n9_primary_execution_complete','sp16_mech9_n10_primary_execution_complete'}]
binder_inputs=[x for x in binder_inputs if x in qs]
addn({
 'id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','node_type':'calculation','owner_standard_id':'SP16_2017',
 'title':'SP16-MECH9 — class-3 M+Q and N9/N10 primary execution',
 'normative_refs':[
   {'standard_id':'SP16_2017','reference_kind':'clause','section':'8.2.7','quote_or_note':'Explicit class-3 plastic-hinge applicability and shear-effect confirmation.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'12','quote_or_note':'Ordinary fatigue 12.1.2 using existing Stage-N9 workflow.'},
   {'standard_id':'SP16_2017','reference_kind':'section','section':'13','quote_or_note':'Section-13 review using existing Stage-N10 workflow.'},
 ],
 'consumes':[{'quantity_id':x,'required':x in {'sp16_mech8_primary_evidence','sp16_applicability_census','ambient_N_force','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y','ambient_T_torsion','ambient_B_bimoment'},'binding_role':'input'} for x in binder_inputs],
 'produces':[
   {'quantity_id':'sp16_mech9_primary_evidence','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech9_class3_mq_binding_complete','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech9_n9_primary_execution_complete','required':True,'binding_role':'output'},
   {'quantity_id':'sp16_mech9_n10_primary_execution_complete','required':True,'binding_role':'output'},
 ],
 'applicability':None,
 'calculation_spec':{'formula_type':'executor','expression_language':'executor_v1','algorithm_id':'sp16_mech9_remaining_ambient_evidence_v1','bindings':[{'variable':x,'quantity_id':x} for x in binder_inputs],'rounding':{'mode':'none'}},
 'notes':{'engineering_meaning':'Overlays bounded class-3 M+Q and executes common N9/N10 routes before the unchanged strict SP16 mechanical gate.','limitations':'Universal T, class-3 biaxial/N+M+Q, crane fatigue, low-cycle external-method boundary and unsupported detailed local-stability geometries remain fail-closed.','normative_warning':'Only COMPLETE qualified N9/N10 results become PASS/FAIL evidence.'}
})

# MECH9 is inserted between the MECH8 binder and the strict MECH6 aggregator.
old=es['MECH8_E_CALC_TO_GATE']; g['edges'].remove(old); del es['MECH8_E_CALC_TO_GATE']
has_bend=anyof(cmp('ambient_M_x','neq',0.0),cmp('ambient_M_y','neq',0.0))
has_shear=anyof(cmp('ambient_Q_x','neq',0.0),cmp('ambient_Q_y','neq',0.0))
c3_mq=allof(has_bend,has_shear,cmp('sp16_section_class','eq','3'))
no_bend=allof(cmp('ambient_M_x','eq',0.0),cmp('ambient_M_y','eq',0.0))
no_shear=allof(cmp('ambient_Q_x','eq',0.0),cmp('ambient_Q_y','eq',0.0))
not_c3_mq=anyof(no_bend,no_shear,cmp('sp16_section_class','in',['1','2','other']))

adde({'id':'MECH9_E_MECH8_TO_C3','from_node_id':'SP16_C_MECH8_INTERACTION_BINDER','to_node_id':'SP16_I_MECH9_CLASS3_CONTEXT','edge_type':'branch','label':'class 3 M+Q → explicit 8.2.7 context','condition':c3_mq,'quantity_ids':['sp16_mech8_primary_evidence','sp16_section_class','ambient_M_x','ambient_M_y','ambient_Q_x','ambient_Q_y']})
adde({'id':'MECH9_E_MECH8_TO_FATIGUE_REQUIRED','from_node_id':'SP16_C_MECH8_INTERACTION_BINDER','to_node_id':'SP16_D_MECH9_FATIGUE_ROUTE','edge_type':'branch','label':'fatigue required','condition':allof(not_c3_mq,cmp('sp16_mech7_fatigue_required','eq',True)),'quantity_ids':['sp16_mech8_primary_evidence','sp16_mech7_fatigue_required']})
adde({'id':'MECH9_E_MECH8_TO_BRITTLE_REQUIRED','from_node_id':'SP16_C_MECH8_INTERACTION_BINDER','to_node_id':'SP16_I_MECH9_BRITTLE_BASE','edge_type':'branch','label':'no class-3 context; fatigue N.A.; Section 13 required','condition':allof(not_c3_mq,cmp('sp16_mech7_fatigue_required','eq',False),cmp('sp16_mech7_brittle_required','eq',True)),'quantity_ids':['sp16_mech8_primary_evidence','sp16_mech7_fatigue_required','sp16_mech7_brittle_required']})
adde({'id':'MECH9_E_MECH8_TO_CALC_NONE','from_node_id':'SP16_C_MECH8_INTERACTION_BINDER','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'branch','label':'no MECH9 interactive route required','condition':allof(not_c3_mq,cmp('sp16_mech7_fatigue_required','eq',False),cmp('sp16_mech7_brittle_required','eq',False)),'quantity_ids':['sp16_mech8_primary_evidence','sp16_mech7_fatigue_required','sp16_mech7_brittle_required']})

# After class-3 context, continue through optional N9 then N10.
adde({'id':'MECH9_E_C3_TO_FATIGUE','from_node_id':'SP16_I_MECH9_CLASS3_CONTEXT','to_node_id':'SP16_D_MECH9_FATIGUE_ROUTE','edge_type':'branch','label':'fatigue required','condition':cmp('sp16_mech7_fatigue_required','eq',True),'quantity_ids':['sp16_mech7_fatigue_required']})
adde({'id':'MECH9_E_C3_TO_BRITTLE','from_node_id':'SP16_I_MECH9_CLASS3_CONTEXT','to_node_id':'SP16_I_MECH9_BRITTLE_BASE','edge_type':'branch','label':'fatigue N.A.; Section 13 required','condition':allof(cmp('sp16_mech7_fatigue_required','eq',False),cmp('sp16_mech7_brittle_required','eq',True)),'quantity_ids':['sp16_mech7_fatigue_required','sp16_mech7_brittle_required']})
adde({'id':'MECH9_E_C3_TO_CALC','from_node_id':'SP16_I_MECH9_CLASS3_CONTEXT','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'branch','label':'no N9/N10 inputs required','condition':allof(cmp('sp16_mech7_fatigue_required','eq',False),cmp('sp16_mech7_brittle_required','eq',False)),'quantity_ids':['sp16_mech7_fatigue_required','sp16_mech7_brittle_required']})

# N9 route selection.
adde({'id':'MECH9_E_FATIGUE_ROUTE_TO_ORDINARY','from_node_id':'SP16_D_MECH9_FATIGUE_ROUTE','to_node_id':'SP16_I_MECH9_FATIGUE_ORDINARY','edge_type':'branch','label':'ordinary fatigue 12.1.2','condition':cmp('sp16_mech9_fatigue_route_kind','eq','ordinary_fatigue_12_1_2'),'quantity_ids':['sp16_mech9_fatigue_route_kind']})
for route in ['crane_runway_12_2','low_cycle_lt_1e5_12_1_1']:
    adde({'id':'MECH9_E_FATIGUE_ROUTE_TO_BRITTLE_'+route.upper().replace('.','_'), 'from_node_id':'SP16_D_MECH9_FATIGUE_ROUTE','to_node_id':'SP16_I_MECH9_BRITTLE_BASE','edge_type':'branch','label':route+'; continue to Section 13','condition':allof(cmp('sp16_mech9_fatigue_route_kind','eq',route),cmp('sp16_mech7_brittle_required','eq',True)),'quantity_ids':['sp16_mech9_fatigue_route_kind','sp16_mech7_brittle_required']})
    adde({'id':'MECH9_E_FATIGUE_ROUTE_TO_CALC_'+route.upper().replace('.','_'), 'from_node_id':'SP16_D_MECH9_FATIGUE_ROUTE','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'branch','label':route+'; no Section 13','condition':allof(cmp('sp16_mech9_fatigue_route_kind','eq',route),cmp('sp16_mech7_brittle_required','eq',False)),'quantity_ids':['sp16_mech9_fatigue_route_kind','sp16_mech7_brittle_required']})
adde({'id':'MECH9_E_FATIGUE_INPUT_TO_BRITTLE','from_node_id':'SP16_I_MECH9_FATIGUE_ORDINARY','to_node_id':'SP16_I_MECH9_BRITTLE_BASE','edge_type':'branch','label':'ordinary N9 inputs complete; Section 13 required','condition':cmp('sp16_mech7_brittle_required','eq',True),'quantity_ids':fatigue_fields+['sp16_mech7_brittle_required']})
adde({'id':'MECH9_E_FATIGUE_INPUT_TO_CALC','from_node_id':'SP16_I_MECH9_FATIGUE_ORDINARY','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'branch','label':'ordinary N9 inputs complete; Section 13 N.A.','condition':cmp('sp16_mech7_brittle_required','eq',False),'quantity_ids':fatigue_fields+['sp16_mech7_brittle_required']})

# N10 base -> prevention detail -> optional lamellar detail -> binder.
adde({'id':'MECH9_E_BRITTLE_BASE_TO_CONDITIONAL','from_node_id':'SP16_I_MECH9_BRITTLE_BASE','to_node_id':'SP16_I_MECH9_BRITTLE_CONDITIONAL','edge_type':'control','label':'Section 13 base classified','condition':None,'quantity_ids':brittle_base})
adde({'id':'MECH9_E_BRITTLE_COND_TO_LAMELLAR','from_node_id':'SP16_I_MECH9_BRITTLE_CONDITIONAL','to_node_id':'SP16_I_MECH9_BRITTLE_LAMELLAR','edge_type':'branch','label':'lamellar route required','condition':cmp('sp16_mech9_brittle_lamellar_required','eq',True),'quantity_ids':brittle_cond+['sp16_mech9_brittle_lamellar_required']})
adde({'id':'MECH9_E_BRITTLE_COND_TO_CALC','from_node_id':'SP16_I_MECH9_BRITTLE_CONDITIONAL','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'branch','label':'lamellar route not required','condition':cmp('sp16_mech9_brittle_lamellar_required','eq',False),'quantity_ids':brittle_cond+['sp16_mech9_brittle_lamellar_required']})
adde({'id':'MECH9_E_LAMELLAR_TO_CALC','from_node_id':'SP16_I_MECH9_BRITTLE_LAMELLAR','to_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','edge_type':'control','label':'Section 13 lamellar inputs complete','condition':None,'quantity_ids':lamellar})
adde({'id':'MECH9_E_CALC_TO_GATE','from_node_id':'SP16_C_MECH9_REMAINING_AMBIENT_BINDER','to_node_id':'SP16_C_AMBIENT_MECHANICAL_AGGREGATOR','edge_type':'control','label':'MECH9 evidence materialized','condition':None,'quantity_ids':['sp16_mech9_primary_evidence']})

agg=ns['SP16_C_AMBIENT_MECHANICAL_AGGREGATOR']
for row in agg['consumes']:
    if row.get('quantity_id')=='sp16_mech8_primary_evidence': row['required']=False
if not any(x.get('quantity_id')=='sp16_mech9_primary_evidence' for x in agg['consumes']):
    agg['consumes'].append({'quantity_id':'sp16_mech9_primary_evidence','required':True,'binding_role':'evidence'})
    agg['calculation_spec']['bindings'].append({'variable':'sp16_mech9_primary_evidence','quantity_id':'sp16_mech9_primary_evidence'})
agg['notes']['limitations']='MECH9 closes bounded class-3 M+Q, ordinary fatigue and Section-13 primary execution. Universal T, class-3 biaxial/N+M+Q, crane/low-cycle fatigue and unsupported detailed local-stability geometries remain fail-closed.'

parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-69_sp16_mech9_remaining_ambient_closure'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.69 — SP16-MECH9 Remaining Ambient Applicability Closure'
g['description']='Cumulative v0.3.69 over v0.3.68: closes bounded class-3 one-plane M+Q through explicit 8.2.7 confirmations and auto-executes ordinary N9 fatigue plus explicit N10 Section-13 review in the primary ambient flow, while keeping unsupported routes fail-closed.'
md=g.setdefault('metadata',{})
md.update({
 'release_stage':'v0.66_sp16_mech9_remaining_ambient_applicability_closure_r1',
 'parent_graph_id':parent,
 'sp16_mech9_class3_mq_one_plane_closed':True,
 'sp16_mech9_n9_ordinary_primary_auto_execution_closed':True,
 'sp16_mech9_n9_crane_primary_auto_execution_closed':False,
 'sp16_mech9_low_cycle_external_boundary_reconciled':True,
 'sp16_mech9_n10_section13_primary_auto_execution_closed':True,
 'sp16_mech9_universal_torsion_normative_check_closed':False,
 'sp16_mech9_remaining_detailed_local_stability_all_geometries_closed':False,
 'sp16_mech9_all_n3_n10_primary_flow_bindings_closed':False,
 'sp16_mech9_engineering_use_ready':False,
 'sp16_mech6_sp554_transition_requires_pass':True,
})
for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]; assert len(ids)==len(set(ids)),f'duplicate {key}'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT); print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
