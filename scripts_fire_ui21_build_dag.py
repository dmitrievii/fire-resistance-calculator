from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"normative_graph/dag_v0.3.56_fire_ui20_conditional_signed_moments_thermal_bindings.json"
OUT=ROOT/"normative_graph/dag_v0.3.57_fire_ui21_selector_hardening_qy_t_lock.json"
RELEASE="v0.54_fire_ui21_selector_hardening_qy_t_lock_r1"

g=json.loads(SRC.read_text(encoding="utf-8"))
parent_graph_id=g["graph_id"]
g["graph_id"]="sp16_sp554_dag_v0-3-57_fire_ui21_selector_hardening_qy_t_lock"
g["graph_title"]="SP16 ↔ SP554 DAG v0.3.57 — FIRE-UI2.1 selector hardening + Qy/T primary-UI lock"
g["description"]="Cumulative v0.3.57 over FIRE-UI2.0: global selector-option hardening, explicit boolean choices in the generated UI contract, and primary-UI locking of unsupported Qy/torsion inputs to zero while retaining fail-closed runtime guards for externally supplied nonzero values."
md=g.setdefault("metadata",{})
md.update({
  "release_stage":RELEASE,
  "parent_graph_id":parent_graph_id,
  "fire_ui21_global_selector_option_audit":True,
  "fire_ui21_boolean_contract_options_synthesized":True,
  "fire_ui21_qy_primary_ui_locked_zero":True,
  "fire_ui21_torsion_primary_ui_locked_zero":True,
  "fire_ui21_qy_runtime_closed":False,
  "fire_ui21_torsion_runtime_closed":False,
})
for node in g["nodes"]:
    if node["id"]=="SP554_H_SP20_LOADS":
        notes=node.setdefault("notes",{})
        extra="FIRE-UI2.1 primary UI locks Qy and torsion T to zero because their general production runtimes are not closed. External/non-UI nonzero values remain explicit fail-closed inputs and are never remapped to Qz or bimoment B."
        notes["limitations"]=((notes.get("limitations") or "")+" "+extra).strip()
        notes["engineering_meaning"]="Signed special-combination actions in the local member system. Primary UI currently authors N, My, Mz and Qz; Qy and T are shown locked at zero until their production routes are closed."
        break
OUT.write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(OUT)
