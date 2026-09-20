from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.59_fire_ui23_protection_route_closure.json'
OUT=ROOT/'normative_graph/dag_v0.3.60_fire_ui24_fire_val1_routing_remediation.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
ns={n['id']:n for n in g['nodes']}
es={e['id']:e for e in g['edges']}


def cmp(qid,op,value): return {'type':'comparison','quantity_id':qid,'operator':op,'value':value}
def allof(*conds): return {'type':'all_of','conditions':list(conds)}
def add_edge(e):
    if e['id'] in es: raise RuntimeError(f"duplicate edge {e['id']}")
    g['edges'].append(e); es[e['id']]=e

# FIRE-VAL1-D001: static-stress route under compression still needs gamma_e.
# Queue the existing compression-length/SP16-mu route in parallel with the 8.7 stress handoff.
add_edge({
    'id':'UI24_E_8_7_COMPRESSION_TO_GAMMAE_CONTEXT',
    'from_node_id':'SP554_D_GAMMA_T_METHOD','to_node_id':'SP554_I_COMPRESSION_CONTEXT',
    'edge_type':'branch','label':'П.8.7 + сжатие -> определить γe устойчивости',
    'condition':allof(cmp('strength_coefficient_method','eq','software_static_stress'),
                      cmp('stress_state','in',['central_compression','compression_plus_bending'])),
    'quantity_ids':[]
})
# The downstream SP16 slenderness/buckling-curve branch is likewise a section-formula concern.
if 'E0226' in es:
    es['E0226']['condition']=cmp('strength_coefficient_method','eq','section_formulas')
    es['E0226']['edge_type']='branch'
    es['E0226']['label']='Формулы разделов 9–11 -> slenderness/curve'

# Gamma-e itself is needed on the 8.7 compression route, but the phi-cap/stability
# branch fed by E0105 belongs to the section-formula route.
if 'E0105' in es:
    es['E0105']['condition']=cmp('strength_coefficient_method','eq','section_formulas')

# The gamma_c branch is a section-formula concern; do not ask it on the 8.7 alternative route.
if 'E0217' in es:
    es['E0217']['condition']=cmp('strength_coefficient_method','eq','section_formulas')
    es['E0217']['edge_type']='branch'
    es['E0217']['label']='Формулы разделов 9–11 -> γc'

# FIRE-VAL1-D001/D005 continuation: the legacy compression-control nodes are
# diagnostic source-literal helpers.  Do not let their diagnostic delta branch
# become the guided production continuation.  Preserve that relation as data and
# continue explicitly to the independent Appendix-B inversion once gamma_T/gamma_e
# are both resolved.
if 'E1098' in es:
    es['E1098']['edge_type']='data'
    es['E1098']['label']='diagnostic compression control-kind relation (not guided production)'
add_edge({
    'id':'UI24_E_CTRL_COMPRESSION_TO_TCR',
    'from_node_id':'SP554_C_CTRL_COMPRESSION','to_node_id':'SP554_FIRE_UI17_C_TCR_COMPRESSION',
    'edge_type':'control','label':'γT and γe resolved -> independent critical-temperature inversion',
    'condition':cmp('stress_state','in',['central_compression','compression_plus_bending']),
    'quantity_ids':['controlling_reduction_coefficient']
})

# FIRE-VAL1-D002: strength-only diagnostic node must not be a guided dead end.
add_edge({
    'id':'UI24_E_CTRL_STRENGTH_TO_TCR',
    'from_node_id':'SP554_C_CTRL_STRENGTH_ONLY','to_node_id':'SP554_FIRE_UI17_C_TCR_STRENGTH_ONLY',
    'edge_type':'control','label':'γT resolved -> критическая температура по прочности',
    'condition':cmp('stress_state','in',['central_tension','bending','tension_plus_bending']),
    'quantity_ids':['controlling_reduction_coefficient']
})

# FIRE-VAL1-D003: do not expose an unsupported "other" Table-1 choice that exact lookup cannot resolve.
# This is fail-closed authoring: only source-traced rows presently modeled by SP16_TABLE1_GAMMA_C are selectable.
for nid in ['SP16_D_GC_T','SP16_D_GC_C','SP16_D_GC_B','SP16_D_GC_NM']:
    n=ns[nid]
    n['options']=[o for o in n.get('options',[]) if o.get('value')!='other']
    n.setdefault('notes',{})['limitations']='FIRE-VAL1: only Table 1 cases explicitly represented by SP16_TABLE1_GAMMA_C are selectable; unsupported cases are not exposed as a dead option.'
    n['notes']['normative_warning']='If the applicable Table 1 case is absent from this selector, this release is not applicable to that case; do not substitute a neighboring γc.'

# FIRE-VAL1-D005 follow-up: Table 7 exact lookup only defines curves a/b/c.
# The previously exposed 'other' choice was a dead selector outcome and could
# reach the fire critical-temperature node with gamma_T unresolved.  Keep the
# route fail-closed by not exposing a value with no normative dataset row.
curve=ns['SP16_D_CURVE']
curve['options']=[o for o in curve.get('options',[]) if o.get('value')!='other']
curve.setdefault('notes',{})['limitations']='FIRE-VAL1: Table 7 lookup in this release supports only explicit normative curves a, b and c. Unsupported curve classification is not exposed as a selectable dead outcome.'
curve['notes']['normative_warning']='If the applicable stability curve cannot be classified as a/b/c under SP16 Table 7, stop the calculation; do not substitute a neighboring curve.'

# FIRE-VAL1-D004: selecting local stress must author the concentrated local force F before Eq. (47).
loc=ns['SP16_I_LOCAL_STRESS_CONTEXT']
if not any(b['quantity_id']=='sp16_local_load_F' for b in loc.get('produces',[])):
    loc['produces'].insert(1,{'quantity_id':'sp16_local_load_F','required':True,'binding_role':'output'})
loc['input_spec']['user_prompt']='Введите сосредоточенную силу F и задайте схему рисунка 6 с требуемыми геометрическими параметрами местной нагрузки по СП16 8.2.2.'
loc['notes']['normative_warning']='F, lef and tw must refer to the same physical load-introduction detail. F is required whenever σloc is selected; no implicit value is taken from the global load vector.'

# FIRE-VAL1-D005 is expected to close as a derivative of D001/D002; annotate the compression Tcr node.
ns['SP554_FIRE_UI17_C_TCR_COMPRESSION'].setdefault('notes',{})['engineering_meaning']='Independent Appendix-B inversion of γT and γe. FIRE-VAL1 ensures every compression route, including 8.7 static-stress, resolves both coefficients before this node executes.'

# Release identity.
parent=g['graph_id']
g['graph_id']='sp16_sp554_dag_v0-3-60_fire_ui24_fire_val1_routing_remediation'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.60 — FIRE-UI2.4 FIRE-VAL1 routing remediation'
g['description']='Cumulative v0.3.60 over v0.3.59: remediates FIRE-VAL1 D001-D005 routing/conditional-input defects, removes unsupported γc dead choices, and requires local-load F before SP16 Eq. (47).'
md=g.setdefault('metadata',{})
md.update({
    'release_stage':'v0.57_fire_ui24_fire_val1_routing_remediation_r1',
    'parent_graph_id':parent,
    'fire_ui24_val1_d001_static_stress_compression_gammae_closed':True,
    'fire_ui24_val1_d002_strength_only_continuation_closed':True,
    'fire_ui24_val1_d003_gamma_c_dead_other_removed':True,
    'fire_ui24_val1_d004_local_load_f_authoring_closed':True,
    'fire_ui24_val1_d005_gamma_t_dependency_reconciled':True,
    'fire_ui24_qy_runtime_closed':False,
    'fire_ui24_torsion_runtime_closed':False,
})

for key in ['quantities','datasets','nodes','edges']:
    ids=[x['id'] for x in g[key]]
    assert len(ids)==len(set(ids)), f'duplicate {key} id'
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
