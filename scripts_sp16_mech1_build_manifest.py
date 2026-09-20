from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/release_manifest_v0_58_sp16_mech1_canonical_axes_mechanical_state_contract_r1.json'
RELEASE='v0.58_sp16_mech1_canonical_axes_mechanical_state_contract_r1'

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

files=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p==OUT: continue
    if '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc' or p.name=='.coverage': continue
    files.append({'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha256(p)})
manifest={
    'schema':'standard_package_release_manifest_v1',
    'release_stage':RELEASE,
    'package_version':'0.58.0',
    'parent_release':'v0.57_fire_ui24_fire_val1_routing_remediation_r1',
    'active_dag':'normative_graph/dag_v0.3.61_sp16_mech1_canonical_axes.json',
    'file_count_excluding_manifest':len(files),
    'files':files,
}
OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT)
print(len(files))
