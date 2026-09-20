from __future__ import annotations
import json, math, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CAP=ROOT/'validation/stage_n2/normcad_capture/normcad_profile_catalog_historical.json'
OUT=ROOT/'data/profile_catalog_interim_v0_28_stage_n2.json'
REG=ROOT/'data/profile_family_registry_v0_28_stage_n2.json'
cap=json.loads(CAP.read_text(encoding='utf-8'))

GROUPS={
 'I_ROLLED_DSYMM': {1,2,3,4,8,9,23,24,25,33,34,35,36,37},
 'RHS_SHS': {5,6,26,27,29,30},
 'Z_SECTION': {10,11},
 'C_LIPPED_SECTION': {12,13},
 'TEE': {14,15,16},
 'CHS': {17,31,32,38},
 'ANGLE': {18,19,28},
 'CHANNEL': {20,21,22},
}
FAMILY_GROUP={fid:g for g,ids in GROUPS.items() for fid in ids}
assert len(FAMILY_GROUP)==37

RULES={
 'I_ROLLED_DSYMM': dict(table7_rule='ROLLED_I_X_B_OR_A_GT500_Y_C', table7_type_x=None, table7_type_y='c', annex_d_k=1.29,
   table7_evidence='Current SP16 Table 7: rolled I strong/web plane type b with Note 1 type-a override for h>500; minor-stiffness plane type c.'),
 'RHS_SHS': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='a', table7_type_y='a', annex_d_k=None,
   table7_evidence='Current SP16 Table 7 type a closed round/rectangular hollow section forms; coefficients independent of calculation plane.'),
 'CHS': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='a', table7_type_y='a', annex_d_k=None,
   table7_evidence='Current SP16 Table 7 type a circular hollow section form; coefficients independent of calculation plane.'),
 'TEE': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='c', table7_type_y='c', annex_d_k=1.20,
   table7_evidence='Current SP16 Table 7 type c tee form; no axis mark on the shown form, therefore plane-independent under Note 2.'),
 'CHANNEL': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='c', table7_type_y='c', annex_d_k=1.12,
   table7_evidence='Current SP16 Table 7 type c channel/U form; no axis mark on the shown form, therefore plane-independent under Note 2.'),
 'C_LIPPED_SECTION': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='c', table7_type_y='c', annex_d_k=None,
   table7_evidence='Mapped to current Table 7 type c open U/C family for interim runtime use; lipped-profile product-standard audit is deferred.'),
 'ANGLE': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='c', table7_type_y='c', annex_d_k=None,
   table7_evidence='Single-angle family assigned to Table 7 type c for interim member stability routing; final product/axis audit remains deferred.'),
 'Z_SECTION': dict(table7_rule='FIXED_BOTH_AXES', table7_type_x='b', table7_type_y='b', annex_d_k=None,
   table7_evidence='Z-family mapped to the Table 7 type b open symmetric/staggered form for interim runtime use; final profile-standard audit remains deferred.'),
}

def standard_label(caption:str):
 m=re.search(r'(ГОСТ(?:\s+Р)?\s+[0-9А-ЯA-Z\.\-]+(?:-\d{2,4})?|СТО\s+АСЧМ\s+20-93|ТУ)',caption)
 return m.group(1) if m else None

families=[]
for f in cap['families']:
 fid=int(f['family_id']); group=FAMILY_GROUP[fid]
 entry={
   'family_id':fid,
   'caption':f['caption'],
   'shape_group':group,
   'product_standard_label_unverified':standard_label(f['caption']),
   'catalog_status':'INTERIM_IMPORTED_FROM_NORMCAD_PENDING_ORIGINAL_GOST_AUDIT',
   'original_gost_audit_complete':False,
   **RULES[group],
 }
 families.append(entry)

profiles=[]
for r in cap['rows']:
 def pos_or_none(k):
  v=r.get(k)
  if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v)) and float(v)>0:
   return float(v)
  return None
 hist_it=pos_or_none('It_mm4_db')
 if hist_it is not None and hist_it>=1e12: hist_it=None
 profiles.append({
   'source_row_id':int(r['id_data']),
   'family_id':int(r['family_id']),
   'designation':str(r['designation']),
   'h_mm':float(r['h_mm']), 'b_mm':float(r['b_mm']), 'tw_mm':float(r['tw_mm']), 'tf_mm':float(r['tf_mm']),
   'r_mm':pos_or_none('r_mm'),
   'A_mm2':float(r['A_mm2']), 'Ix_mm4':float(r['Ix_mm4']), 'Iy_mm4':float(r['Iy_mm4']),
   'Wx1_mm3':float(r['Wx1_mm3']), 'Wx2_mm3':float(r['Wx2_mm3']), 'Wy1_mm3':float(r['Wy1_mm3']), 'Wy2_mm3':float(r['Wy2_mm3']),
   'Sx_mm3':pos_or_none('Sx_mm3'), 'Sy_mm3':pos_or_none('Sy_mm3'),
   'historical_mass_kg_m':r.get('mass_kg_m_db'),
   'historical_it_mm4':hist_it,
   'historical_it_rejected': hist_it is None and r.get('It_mm4_db') is not None,
   'historical_afwx':r.get('afwx'), 'historical_afwy':r.get('afwy'),
 })

payload={
 'schema_version':'1.0',
 'catalog_id':'SP16-INTERIM-PROFILE-CATALOG-N2-001',
 'status':'INTERIM_IMPORTED_FROM_NORMCAD_PENDING_ORIGINAL_GOST_AUDIT',
 'original_gost_audit_complete':False,
 'normcad_source_sha256':cap['source_sha256'],
 'current_sp16_source_sha256':'302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873',
 'family_count':len(families), 'profile_count':len(profiles),
 'runtime_policy':{
   'interim_catalog_fields':['h','b','tw','tf','r','A','Ix','Iy','Wx1','Wx2','Wy1','Wy2','Sx','Sy'],
   'always_recomputed':['mass','ix','iy','imin','minimum section moduli','Table 7 alpha/beta','supported alpha_f ratios','torsional inertia when a current-SP or geometry derivation is implemented'],
   'never_trusted_directly':['NormCAD mass','NormCAD afwx','NormCAD afwy','corrupt/sentinel NormCAD It'],
   'final_gate':'Every imported profile family/row must be checked against its original effective product standard before final engineering-use release.'
 },
 'profiles':profiles,
}
registry={
 'schema_version':'1.0','registry_id':'SP16-PROFILE-FAMILY-REGISTRY-N2-001',
 'current_sp16_source_sha256':payload['current_sp16_source_sha256'],
 'table7_coefficients':{'a':{'alpha':0.03,'beta':0.06},'b':{'alpha':0.04,'beta':0.09},'c':{'alpha':0.04,'beta':0.14}},
 'families':families,
 'notes':[
   'Table 7 coefficients are assigned by section family so the existing stability branches can run from a selected profile.',
   'Original profile dimensions/properties are interim imports and remain pending original-GOST audit.',
   'Current SP16 Annex D torsion k is assigned only where the section family is directly supported by the Annex D rule.'
 ]
}
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
REG.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT, OUT.stat().st_size)
print(REG, REG.stat().st_size)
print('families',len(families),'profiles',len(profiles))
