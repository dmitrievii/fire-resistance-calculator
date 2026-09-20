from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'normative_graph/dag_v0.3.53_fire_ui17_critical_temperature_restraint_ux_hotfix.json'
OUT=ROOT/'normative_graph/dag_v0.3.54_fire_ui18_fire_d2_to_d3_handoff_hotfix.json'
g=json.loads(SRC.read_text(encoding='utf-8'))
n={x['id']:x for x in g['nodes']}
e={x['id']:x for x in g['edges']}

# FIRE-D2 exact critical-temperature result is a mechanical stage summary, not
# the end of the whole fire-resistance calculation.  Only an exact result can
# enter the existing Section-12 runtime because the current FIRE-D3 handoff
# consumes a scalar critical_temperature_c.
edge=e['FIRE_D3_E_001']
edge['edge_type']='handoff'
edge['label']='exact FIRE-D2 Tcr -> FIRE-D3 Section 12'
edge['condition']={
    'type':'comparison',
    'quantity_id':'fire_d2_critical_temperature_status',
    'operator':'eq',
    'value':'COMPLETE',
}
edge['quantity_ids']=['fire_d2_critical_temperature_c']

handoff_edge={
    'id':'FIRE_UI18_E_D3_HANDOFF_TO_EXPOSURE',
    'from_node_id':'SP554_FIRE_D3_C_D2_TCR_HANDOFF',
    'to_node_id':'SP554_I_EXPOSURE',
    'edge_type':'control',
    'label':'FIRE-D3 thermal authoring begins with heated exposure configuration',
    'condition':None,
    'quantity_ids':['critical_temperature_c','fire_d3_critical_temperature_handoff_c'],
}
if handoff_edge['id'] not in e:
    g['edges'].append(handoff_edge)

r=n['SP554_FIRE_D2_R_CRITICAL_TEMPERATURE']
r.setdefault('notes',{})['engineering_meaning']='FIRE-D2 mechanical stage result. Exact Tcr continues into FIRE-D3 Section 12; ambient-capacity failure or lower-bound-only Tcr remains fail-closed until a compatible thermal boundary route exists.'
r['notes']['limitations']='Exact status COMPLETE is handed off to Section 12. AMBIENT_CAPACITY_EXCEEDED and INCOMPLETE_FAIL_CLOSED do not fabricate an exact thermal target.'
r['notes']['normative_warning']='A valid exact critical temperature is not a terminal calculation result: it is the target temperature for the subsequent Section 12 thermal calculation.'

h=n['SP554_FIRE_D3_C_D2_TCR_HANDOFF']
h.setdefault('notes',{})['engineering_meaning']='Copies the exact governing FIRE-D2 critical temperature into the FIRE-D3 thermal target and immediately opens the Section 12 exposure authoring branch.'
h['notes']['limitations']='Requires fire_d2_critical_temperature_status=COMPLETE and exact fire_d2_critical_temperature_c.'

# Release identity.
g['graph_id']='sp16_sp554_dag_v0-3-54_fire_ui18_fire_d2_to_d3_handoff_hotfix'
g['graph_title']='SP16 ↔ SP554 DAG v0.3.54 — FIRE-UI1.8 FIRE-D2 to FIRE-D3 handoff hotfix'
g['description']='Cumulative v0.3.54 over FIRE-UI1.7: exact FIRE-D2 critical-temperature results continue through an explicit FIRE-D3 handoff to Section 12 heated-exposure authoring; ambient-capacity and lower-bound-only results remain fail-closed without extrapolation or fabricated thermal targets.'
meta=g.setdefault('metadata',{})
meta['release_stage']='v0.51_fire_ui18_fire_d2_to_d3_handoff_hotfix_r1'
meta['parent_graph_id']='sp16_sp554_dag_v0-3-53_fire_ui17_critical_temperature_restraint_ux_hotfix'
meta['fire_ui18_exact_tcr_to_fire_d3_handoff']=True
meta['fire_ui18_result_continuation']=True
meta['fire_ui18_bounded_result_fail_closed']=True

OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT)
print(len(g['quantities']),len(g['datasets']),len(g['nodes']),len(g['edges']))
