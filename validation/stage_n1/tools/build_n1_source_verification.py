from __future__ import annotations
import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/'validation/stage_n1'

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def core_iv(iv):
    return {k:iv[k] for k in ('min_mm','max_mm','min_inclusive','max_inclusive')}

def core_row(r):
    return {
        'grades':r['grades'],
        'thickness_interval':core_iv(r['thickness_interval']),
        'Ryn_MPa':r['Ryn_MPa'],'Run_MPa':r['Run_MPa'],
        'Ry_MPa':r['Ry_MPa'],'Ru_MPa':r['Ru_MPa']
    }

cap=load(STAGE/'current_sp16_source_capture_stage_n1.json')
checks=[]
for key,file in [('V3','annex_v3_strength_resistances.json'),('V4','annex_v4_parallel_flange_i_strength_resistances.json'),('V5','annex_v5_shaped_strength_resistances.json')]:
    src=[core_row(r) for r in cap[key]['rows']]
    pkg=[core_row(r) for r in load(ROOT/'data'/file)['rows']]
    mism=[]
    for i in range(max(len(src),len(pkg))):
        a=src[i] if i<len(src) else None; b=pkg[i] if i<len(pkg) else None
        if a!=b:mism.append({'row_index':i+1,'source':a,'package':b})
    checks.append({'id':f'SOURCE_VS_PACKAGE_{key}','source_rows':len(src),'package_rows':len(pkg),'mismatch_count':len(mism),'status':'PASS_EXACT' if not mism else 'FAIL','mismatches':mism})

b1_pkg=load(ROOT/'data/annex_b1_physical_properties.json')['rolled_steel']
b1_src=cap['B1']['rolled_steel']
checks.append({'id':'SOURCE_VS_PACKAGE_B1','status':'PASS_EXACT' if b1_pkg==b1_src else 'FAIL','source':b1_src,'package':b1_pkg})

t2_pkg=load(ROOT/'data/table_2_resistance_formulas.json')['formulas']
t2_expected={
 'design_yield_resistance': {'symbol':'Ry','input_symbol':'Ryn','coefficient':1.0,'divide_by':'gamma_m'},
 'design_ultimate_resistance': {'symbol':'Ru','input_symbol':'Run','coefficient':1.0,'divide_by':'gamma_m'},
 'design_shear_resistance': {'symbol':'Rs','input_symbol':'Ryn','coefficient':0.58,'divide_by':'gamma_m'},
 'design_end_bearing_resistance': {'symbol':'Rp','input_symbol':'Run','coefficient':1.0,'divide_by':'gamma_m'},
 'design_pin_local_bearing_resistance': {'symbol':'Rlp','input_symbol':'Run','coefficient':0.5,'divide_by':'gamma_m'},
 'design_roller_diametral_compression_resistance': {'symbol':'Rcd','input_symbol':'Run','coefficient':0.025,'divide_by':'gamma_m'},
}
checks.append({'id':'SOURCE_VS_PACKAGE_TABLE_2','status':'PASS_EXACT' if t2_pkg==t2_expected else 'FAIL','source_formula_contract':cap['table_2']['formula_contract'],'package_formulas':t2_pkg})

t3_pkg=load(ROOT/'data/table_3_material_safety_factors.json')['categories']
t3_src={x['id']:x['gamma_m'] for x in cap['table_3']['categories_in_source_order']}
checks.append({'id':'SOURCE_VS_PACKAGE_TABLE_3','status':'PASS_EXACT' if t3_pkg==t3_src else 'FAIL','source':t3_src,'package':t3_pkg})

gu_pkg=load(ROOT/'data/clause_4_3_2_gamma_u.json')['gamma_u']; gu_src=cap['gamma_u']['gamma_u']
checks.append({'id':'SOURCE_VS_PACKAGE_GAMMA_U','status':'PASS_EXACT' if gu_pkg==gu_src else 'FAIL','source':gu_src,'package':gu_pkg})

report={
 'schema_version':'1.0.0','stage':'N1 — Material / Strength',
 'normative_source':cap['normative_source'],
 'method':'Independent extraction from LibreOffice HTML structure of the locked current DOC, then exact comparison to production material datasets.',
 'checks':checks,
 'summary':{
   'checks':len(checks),
   'passed':sum(c['status']=='PASS_EXACT' for c in checks),
   'failed':sum(c['status']!='PASS_EXACT' for c in checks),
   'strength_table_rows_exactly_verified':sum(c.get('source_rows',0) for c in checks if c['status']=='PASS_EXACT'),
 },
 'verdict':'PASS' if all(c['status']=='PASS_EXACT' for c in checks) else 'FAIL'
}
(STAGE/'source_vs_package_verification_stage_n1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['summary'],ensure_ascii=False));print(report['verdict'])
