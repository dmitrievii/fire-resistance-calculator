from pathlib import Path
import json, math, traceback
from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui0 import FireUIError, GuidedCalculationSession
from standard_core.sp16_mech1_canonical_actions import migrate_v057_actions_to_sp16_mech1
ROOT=Path(__file__).resolve().parents[1]

# conservative generic engineering authoring answers for route qualification, not normative validation values
NODE_ANSWERS={
 'SP16_D_GC_T':'default',
 'SP16_D_GC_C':'default',
 'SP554_D_GAMMA_T_METHOD':'section_formulas',
 'SP554_D_EXPOSURE':'four_sided',
 'SP554_I_EXPOSURE':'four_sided',
 'SP16_D_MU_ROUTE':'table30',
 'SP16_D_SECTION_CLASS':'class_1',
 'SP16_D_LTB_REQUIRED':False,
 'SP16_D_LOCAL_LOAD':False,
 'SP16_D_LOCAL_STABILITY_REQUIRED':False,
 'SP16_D_GC_B':'default',
}
Q_DEFAULTS={
 'material_safety_category':'statistical_control',
 'sp16_gamma_c_case_bending':'default',
 'gamma_c':1.0,'gamma_c_tension':1.0,'gamma_c_compression':1.0,
 'sp16_gamma_c_case_tension':'default','sp16_gamma_c_case_compression':'default',
 'gamma_t_method':'section_formulas','sp554_gamma_t_method':'section_formulas',
 'mu_x':1.0,'mu_y':1.0,'mu_z':1.0,'effective_length_factor':1.0,
 'L_member':3000.0,'member_length':3000.0,'L_x':3000.0,'L_y':3000.0,
 'M_x_max':1.0,'M_y_max':1.0,
 'local_load_present':False,'has_local_load':False,
 'member_restraint_model': {'schema':'route_qualification_restraint_v1','lateral_restraint':'continuous','warping_restraint':'free'},
}

def app_session(loads, holes=False):
    app=FireUI1Application.from_package_root(ROOT)
    s=app.service.get_session(app.service.create_session()['session_id'])
    for a in [True,False,'hot_rolled_section','catalog_section']: s.submit(a)
    r=next(x for x in app.profile_catalog.list_profiles(35) if x['designation']=='20К1')
    s.submit({'section_catalog_standard':'ГОСТ Р 57837-2017','section_designation':'20К1','section_family':'i_section','sp16_i_symmetry_class':'double_symmetric','section_catalog_family_id':35,'section_catalog_source_row_id':r['source_row_id']})
    cat=app.material_strength_catalog(); p=next(x for x in cat['products'] if x['value']=='parallel_flange_i'); g=next(x for x in p['grades'] if x['steel_grade']=='С255Б'); i=next(x for x in g['intervals'] if x['thickness_interval']['max_mm']==10)
    s.submit({'steel_product_form':'parallel_flange_i','steel_grade':'С255Б','steel_strength_interval_key':i['interval_key'],'governing_product_thickness_mm':10.0})
    if holes:
        s.submit({'schema':'section_weakening_model_v0.49','holes_present':True,'model':'bolt_hole_neutral_line_universal_v1','hole_diameter_mm':20.0,'hole_pitch_mm':80.0})
        s.submit('area_only_keep_gross')
    else:
        s.submit({'schema':'section_weakening_model_v0.49','holes_present':False,'model':'none'})
    s.submit(False) # gamma_ct extra
    canonical = dict(loads)
    if any(k in canonical for k in ('load_My_local','load_Mz_local','load_Qy_local','load_Qz_local')):
        canonical = migrate_v057_actions_to_sp16_mech1(canonical)
    # This historical FIRE-UI1.6 route census qualifies the downstream fire
    # subsystem.  Since v0.63 the real guided route is protected by the strict
    # SP16_MECHANICAL_PASS gate.  To keep this regression suite scoped to the
    # already-qualified fire runtime, create an isolated downstream subflow and
    # copy the completed section/material authoring state into it.  This is a
    # test/example harness only; production DAG routing still requires MECH6 PASS.
    upstream=s
    s=GuidedCalculationSession(app.model,entry_node_id='SP16_D_FIRE_LOAD_CASE_MODE',registry=app.service.registry)
    for qid,qv in upstream.values.items():
        s._set_quantity(qid,qv.value,node_id='FIRE_UI16_UPSTREAM_SP16_PASSED',source_kind=qv.source_kind,provenance=qv.provenance)
    s.submit('separate')
    assert s.current_node_id=='SP554_H_SP20_LOADS', s.current_node_id
    payload={'special_load_combination':{'schema':'sp16_mech2_route_census_fire_v1','description':'route census','source':'legacy-adapted when applicable'}, **canonical}
    s.submit(payload)
    # Fire B is independently scoped in SP16-MECH2. Historical route-census
    # cases contain no B, so answer the fire question explicitly.
    if s.current_node_id == 'SP16_D_BIMOMENT_REQUIRED':
        s.submit(False)
    while s.current_node_id!='SP554_D_VERIFICATION_PLAN_CONFIRM':
        if s.current_node_id is None or s.status.startswith('BLOCKED'):
            raise AssertionError((s.status,s.current_node_id,s.branch_failures[-3:]))
        ans,prov=auto_answer(s)
        if ans is None:
            raise AssertionError(('UNANSWERED_FIRE_DEPENDENCY',s.current_node_id,s.current_card()))
        s.submit(ans,provenance=prov)
    s.submit(True)
    return app,s

def auto_answer(s):
    nid=s.current_node_id; card=s.current_card()
    if nid in NODE_ANSWERS:
        return NODE_ANSWERS[nid], None
    fields=card.get('fields') or []
    options=card.get('options') or []
    shape=card.get('submit_shape')
    if shape=='scalar' and options:
        # choose common safe options by label/value
        vals=[o['value'] for o in options]
        prefs=['default','no','false','section_formulas','user_value','class_1','not_required','none','standard','four_sided']
        for p in prefs:
            if p in vals: return p,None
        return vals[0],None
    if shape=='scalar' and len(fields)==1:
        f=fields[0]; q=f['quantity_id']; dt=f.get('data_type')
        if q in Q_DEFAULTS:return Q_DEFAULTS[q], prov_if(card,q)
        if dt=='boolean':return False,None
        if dt=='enum' and f.get('enum_values'):
            return f['enum_values'][0]['value'],None
        if dt in ('number','integer'):
            # units based guesses
            unit=f.get('canonical_unit')
            return (3000.0 if unit=='mm' else 1.0),prov_if(card,q)
        if dt=='object':
            return {'schema':'route_qualification_object_v1'},prov_if(card,q)
        if dt=='string': return 'route_qualification',prov_if(card,q)
    # multi-field payload
    if fields:
        out={}
        for f in fields:
            q=f['quantity_id']; dt=f.get('data_type'); ev=f.get('enum_values') or []
            if q in Q_DEFAULTS: out[q]=Q_DEFAULTS[q]
            elif dt=='boolean': out[q]=False
            elif dt=='enum' and ev: out[q]=ev[0]['value']
            elif dt in ('number','integer'): out[q]=3000.0 if f.get('canonical_unit')=='mm' else 1.0
            elif dt=='object': out[q]={'schema':'route_qualification_object_v1'}
            elif dt=='string': out[q]='route_qualification'
            elif f.get('required'): return None,None
        return out,None
    return None,None

def prov_if(card,q=None):
    if card.get('external_handoff'):
        return {'source_document':'route qualification input','source_reference':q or card.get('node_id')}
    return None

def run(name, loads, holes=False,maxsteps=120):
    app,s=app_session(loads,holes)
    rows=[]
    for k in range(maxsteps):
        rows.append((k,s.status,s.current_node_id,len(s.pending_node_ids),list(s.branch_failures[-2:])))
        # Mechanical qualification boundary: stop before any Section 12+/protection stage,
        # but only after no mechanical node remains queued. A FIRE-D2 result is also a valid boundary.
        if s.current_node_id=='SP554_FIRE_D2_R_CRITICAL_TEMPERATURE' and not any(s._stage_rank(n)<50 for n in s.pending_node_ids):
            return 'MECHANICAL_RESULT',s,rows
        if s.current_node_id is not None and s._stage_rank(s.current_node_id)>=50 and not any(s._stage_rank(n)<50 for n in s.pending_node_ids):
            return 'THERMAL_ENTRY',s,rows
        if s.status in ('RESULT','COMPLETE') or s.status.startswith('BLOCKED'):
            return s.status,s,rows
        ans,prov=auto_answer(s)
        if ans is None:
            return 'UNKNOWN_INTERACTIVE',s,rows
        try:
            s.submit(ans,provenance=prov)
        except Exception as e:
            return f'EXCEPTION:{type(e).__name__}:{e}',s,rows
    return 'STEP_LIMIT',s,rows

if __name__=='__main__':
    cases={
      'tension': dict(N_force=400000.0,load_My_local=0.0,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'compression': dict(N_force=-400000.0,load_My_local=0.0,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'My': dict(N_force=0.0,load_My_local=30e6,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'Mz': dict(N_force=0.0,load_My_local=0.0,load_Mz_local=10e6,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'biax': dict(N_force=0.0,load_My_local=30e6,load_Mz_local=10e6,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'Qz': dict(N_force=0.0,load_My_local=0.0,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=50e3,T_torsion=0.0),
      'MyQz': dict(N_force=0.0,load_My_local=30e6,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=50e3,T_torsion=0.0),
      'NcMy': dict(N_force=-400e3,load_My_local=30e6,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'NtMy': dict(N_force=400e3,load_My_local=30e6,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=0.0),
      'general': dict(N_force=-400e3,load_My_local=30e6,load_Mz_local=10e6,load_Qy_local=0.0,load_Qz_local=50e3,T_torsion=0.0),
      'Qy_deferred': dict(N_force=400e3,load_My_local=0.0,load_Mz_local=0.0,load_Qy_local=50e3,load_Qz_local=0.0,T_torsion=0.0),
      'T_deferred': dict(N_force=400e3,load_My_local=0.0,load_Mz_local=0.0,load_Qy_local=0.0,load_Qz_local=0.0,T_torsion=5e6),
    }
    for name,loads in cases.items():
        status,s,rows=run(name,loads)
        print('\nCASE',name,'=>',status,'node',s.current_node_id,'pending',len(s.pending_node_ids),'failures',s.branch_failures[-5:])
        print('last route:', ' -> '.join(str(r[2]) for r in rows[-12:]))
        if status not in ('MECHANICAL_RESULT','THERMAL_ENTRY'):
            print('card',json.dumps(s.current_card(),ensure_ascii=False)[:1800])
