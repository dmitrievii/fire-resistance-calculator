from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/release_manifest_v0_61_sp16_mech4_free_torsion_pointwise_recovery_r1.json'
RELEASE='v0.61_sp16_mech4_free_torsion_pointwise_recovery_r1'
def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()
files=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or p==OUT: continue
 if '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc' or p.name=='.coverage': continue
 files.append({'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha256(p)})
manifest={'schema':'standard_package_release_manifest_v1','release_stage':RELEASE,'package_version':'0.61.0','parent_release':'v0.60_sp16_mech3_axis_shear_pointwise_recovery_r1','active_dag':'normative_graph/dag_v0.3.64_sp16_mech4_free_torsion_pointwise_recovery.json','file_count_excluding_manifest':len(files),'files':files}
OUT.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(OUT);print(len(files))
