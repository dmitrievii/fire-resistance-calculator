from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from typing import Any

REL=Path(__file__).resolve().parents[3]
CAP=REL/'validation/stage_n1/normcad_capture'


def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))

def norm_grade(s:str)->str:
    s=s.strip().replace('C','С').replace('K','К')
    s=re.sub(r'\s+по\s+ГОСТ\s+27772.*$','',s,flags=re.I).strip()
    s=re.sub(r'\s*\(для двутавров.*$','',s,flags=re.I).strip()
    return s

def parse_nc_interval(raw:str)->dict[str,Any]:
    # Decode the human-readable condition only; trailing record artifacts are ignored by regex.
    s=raw.replace(',','.').replace('≤','<=').replace('≥','>=').strip()
    nums=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)]
    sl=s.lower()
    if '<=' in s and nums:
        return {'min_mm':None,'max_mm':nums[0],'min_inclusive':False,'max_inclusive':True,'confidence':'HIGH','raw':raw}
    if re.search(r'(?<!<)>\s*\d',s) and nums:
        return {'min_mm':nums[0],'max_mm':None,'min_inclusive':False,'max_inclusive':False,'confidence':'HIGH','raw':raw}
    if 'свыше' in sl and len(nums)>=2:
        return {'min_mm':nums[0],'max_mm':nums[1],'min_inclusive':False,'max_inclusive':True,'confidence':'HIGH_FOR_LOWER_MEDIUM_FOR_UPPER','raw':raw}
    if 'от ' in sl and len(nums)>=2:
        return {'min_mm':nums[0],'max_mm':nums[1],'min_inclusive':True,'max_inclusive':('включ' in sl),'confidence':'HIGH' if 'включ' in sl else 'MEDIUM','raw':raw}
    if sl.startswith('до ') and nums:
        return {'min_mm':None,'max_mm':nums[0],'min_inclusive':False,'max_inclusive':True,'confidence':'MEDIUM','raw':raw}
    if len(nums)>=2 and '-' in s:
        return {'min_mm':nums[0],'max_mm':nums[1],'min_inclusive':True,'max_inclusive':True,'confidence':'MEDIUM','raw':raw}
    return {'min_mm':None,'max_mm':None,'min_inclusive':False,'max_inclusive':False,'confidence':'UNRESOLVED','raw':raw}

def contains(iv,t):
    lo,hi=iv['min_mm'],iv['max_mm']
    if lo is not None:
        if t<lo or (t==lo and not iv['min_inclusive']): return False
    if hi is not None:
        if t>hi or (t==hi and not iv['max_inclusive']): return False
    return True

def probe(iv):
    lo,hi=iv['min_mm'],iv['max_mm']
    if lo is None and hi is not None: return max(0.1, hi*0.5)
    if hi is None and lo is not None: return lo+max(1.0,abs(lo)*0.1)
    if lo is not None and hi is not None:
        return (lo+hi)/2.0
    return 1.0

def iv_signature(iv):
    return (iv['min_mm'],iv['max_mm'],bool(iv['min_inclusive']),bool(iv['max_inclusive']))

def vals(r): return (r['Ryn_MPa'],r['Run_MPa'],r.get('Ry_MPa'),r.get('Ru_MPa'))

def select_rows(capture, table, grade):
    rows=capture['rows']
    if table=='V3':
        # Current СП V.3 covers plate/sheet/strip/bar/tubes. For the sheet/rolled material
        # database, prefer the later explicit ГОСТ 27772 family when present.
        cand=[r for r in rows if norm_grade(r['caption'])==grade and 'по ГОСТ 27772' in r['caption']]
        if cand: return cand,'PREFERRED_GOST27772_FAMILY'
        cand=[r for r in rows if norm_grade(r['caption'])==grade]
        return cand,'LEGACY_FALLBACK' if cand else 'NO_GRADE'
    if table=='V4':
        cand=[r for r in rows if norm_grade(r['caption'])==grade and 'двутавров' in r['caption']]
        return cand,'PARALLEL_FLANGE_FAMILY' if cand else 'NO_GRADE'
    if table=='V5':
        cand=[r for r in rows if norm_grade(r['caption'])==grade and 'по ГОСТ 27772' in r['caption']]
        if cand: return cand,'PREFERRED_GOST27772_FAMILY'
        # Do not silently use a legacy generic family if the current grade is absent from the later family.
        # It is still retained in evidence, but comparison is marked legacy fallback.
        cand=[r for r in rows if norm_grade(r['caption'])==grade and 'двутавров' not in r['caption']]
        return cand,'LEGACY_FALLBACK' if cand else 'NO_GRADE'
    return [],'NO_GRADE'

def compare_table(table, current_file, capture_file):
    current=load(REL/'data'/current_file)
    capture=load(CAP/capture_file)
    out=[]
    for ridx,row in enumerate(current['rows'],1):
        for grade in row['grades']:
            iv=row['thickness_interval']; t=probe(iv)
            cand,family=select_rows(capture,table,grade)
            cand2=[]
            for r in cand:
                niv=parse_nc_interval(r['condition_raw'])
                if niv['confidence']!='UNRESOLVED' and contains(niv,t):
                    cand2.append((r,niv))
            rec={
                'table':table,
                'current_row_index':ridx,
                'steel_grade':grade,
                'current_interval':iv,
                'probe_thickness_mm':t,
                'current_values':{'Ryn_MPa':row['Ryn_MPa'],'Run_MPa':row['Run_MPa'],'Ry_MPa':row['Ry_MPa'],'Ru_MPa':row['Ru_MPa']},
                'normcad_family_selection':family,
                'normcad_candidates_at_probe':[],
            }
            for r,niv in cand2:
                rec['normcad_candidates_at_probe'].append({
                    'id_data':r['id_data'],'caption':r['caption'],'condition_raw':r['condition_raw'],'parsed_interval':niv,
                    'values':{'Ryn_MPa':r['Ryn_MPa'],'Run_MPa':r['Run_MPa'],'Ry_MPa':r['Ry_MPa'],'Ru_MPa':r['Ru_MPa'],'Rs_MPa':r['Rs_MPa']},
                    'page':r['page'],'row':r['row'],'record_hex':r['record_hex']
                })
            if not cand:
                rec['status']='NORMCAD_GRADE_MISSING'
                rec['first_divergent_atomic_step']='grade_availability'
                rec['primary_class']='TABLE_LOOKUP_MISMATCH'
                rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING']
            elif not cand2:
                rec['status']='NORMCAD_THICKNESS_ROUTE_MISSING'
                rec['first_divergent_atomic_step']='thickness_interval_selection'
                rec['primary_class']='TABLE_LOOKUP_MISMATCH'
                rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING']
            elif len(cand2)>1:
                rec['status']='NORMCAD_OVERLAPPING_ROWS_AT_PROBE'
                rec['first_divergent_atomic_step']='thickness_interval_selection'
                rec['primary_class']='BRANCH_LOGIC_MISMATCH'
                rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING']
            else:
                nr,niv=cand2[0]
                vmatch=vals(row)==vals(nr)
                ivmatch=iv_signature(iv)==iv_signature(niv)
                if vmatch and ivmatch and family!='LEGACY_FALLBACK':
                    rec['status']='MATCH_STATIC_ROW_AND_BOUNDARY_LABEL'
                    rec['first_divergent_atomic_step']=None
                    rec['primary_class']='PASS_ALL'
                    rec['secondary_classes']=[]
                elif vmatch and not ivmatch:
                    rec['status']='VALUES_MATCH_BOUNDARY_LABEL_DIFFERS_OR_UNCERTAIN'
                    rec['first_divergent_atomic_step']='thickness_interval_boundary'
                    rec['primary_class']='BRANCH_LOGIC_MISMATCH'
                    rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING'] if family=='LEGACY_FALLBACK' else []
                elif not vmatch:
                    diffs=[]
                    for k in ('Ryn_MPa','Run_MPa','Ry_MPa','Ru_MPa'):
                        if row[k]!=nr[k]: diffs.append({'quantity':k,'sp16':row[k],'normcad':nr[k]})
                    rec['status']='VALUE_MISMATCH'
                    rec['value_differences']=diffs
                    rec['first_divergent_atomic_step']=diffs[0]['quantity'] if diffs else 'strength_row'
                    rec['primary_class']='TABLE_LOOKUP_MISMATCH'
                    rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING']
                else:
                    rec['status']='MATCH_VALUES_LEGACY_FAMILY_ONLY'
                    rec['first_divergent_atomic_step']='dataset_identity'
                    rec['primary_class']='PROFILE_DATABASE_MISMATCH'
                    rec['secondary_classes']=['NORMCAD_OUTDATED_OR_NONCONFORMING']
            out.append(rec)
    return out

v3=compare_table('V3','annex_v3_strength_resistances.json','Прочность листовой стали.json')
v4=compare_table('V4','annex_v4_parallel_flange_i_strength_resistances.json','Прочность фасонной стали.json')
v5=compare_table('V5','annex_v5_shaped_strength_resistances.json','Прочность фасонной стали.json')

# Tube database: taxonomy-level comparison, not falsely matched to the plate database.
tube=load(CAP/'Прочность труб.json')
tube_summary={
    'normcad_file':tube['file'],'sha256':tube['sha256'],'rows':len(tube['rows']),
    'normcad_grade_captions':[m['caption'] for m in tube['main']],
    'current_sp16_route':'Table В.3; current steel grades / governing product thickness',
    'status':'NORMCAD_TUBE_DATABASE_USES_OBSOLETE_NON_CURRENT_GRADE_TAXONOMY',
    'primary_class':'PROFILE_DATABASE_MISMATCH',
    'secondary_classes':['NORMCAD_OUTDATED_OR_NONCONFORMING'],
    'rows_evidence':tube['rows'],
}

allrows=v3+v4+v5
from collections import Counter
summary=Counter(r['status'] for r in allrows)
primary=Counter(r['primary_class'] for r in allrows)
report={
    'schema_version':'1.0.0',
    'stage':'N1 — Material / Strength',
    'normative_source':{'designation':'СП 16.13330.2017, Changes 1–6 through 09.12.2024','sha256':'302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873'},
    'comparison_policy':{
        'authority':'current SP16 only',
        'normcad_role':'historical secondary oracle',
        'normcad_family_preference':'explicit “по ГОСТ 27772” rows where present; otherwise legacy evidence is labelled, not promoted silently',
        'probe_policy':'one interior thickness probe per current grade-row to avoid inventing runtime boundary semantics from static labels',
        'boundary_policy':'raw NormCAD condition labels are preserved and parsed separately; ambiguous exact-boundary runtime selection is not claimed without UI/runtime evidence',
        'values_compared':['Ryn','Run','Ry','Ru']
    },
    'normcad_sources':{
        'sheet_strength':{'file':'Прочность листовой стали.mdb','sha256':load(CAP/'Прочность листовой стали.json')['sha256']},
        'shaped_strength':{'file':'Прочность фасонной стали.mdb','sha256':load(CAP/'Прочность фасонной стали.json')['sha256']},
        'tube_strength':{'file':'Прочность труб.mdb','sha256':tube['sha256']},
    },
    'summary':{'current_grade_rows_compared':len(allrows),'by_status':dict(summary),'by_primary_class':dict(primary)},
    'tables':{'V3_plate_bar_static_oracle':v3,'V4_parallel_flange_i':v4,'V5_shaped_rolled':v5,'tube_database':tube_summary},
}
outdir=REL/'validation/stage_n1'
outdir.mkdir(parents=True,exist_ok=True)
(outdir/'normcad_strength_crosswalk_stage_n1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('rows',len(allrows)); print('summary',summary); print('primary',primary)
for r in allrows:
    if r['status']!='MATCH_STATIC_ROW_AND_BOUNDARY_LABEL':
        print(r['table'],r['steel_grade'],r['current_interval'],r['status'],r.get('value_differences'),r['normcad_family_selection'])
