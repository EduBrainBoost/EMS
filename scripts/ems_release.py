from __future__ import annotations
import argparse, hashlib, json, os, zipfile
from pathlib import Path

EXCLUDED={'.git','.pytest_cache','__pycache__','state','Runs','release','dist','build','.venv','venv'}
EXCLUDED_NAMES={'terminal3_ems_recovery_sha256.json','terminal3_ems_manifest_idempotency.json','terminal3_ems_release.json','terminal3_ems_rollback.json','terminal3_ems_sbom.json','ems_first_push_manifest.json','ems_phase2_push_gate.json'}

def files(root:Path):
    result=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if any(part in EXCLUDED for part in p.relative_to(root).parts) or p.name in EXCLUDED_NAMES: continue
        if rel.endswith(('.zip','.pyc','.log','.har','.mp4','.webm')): continue
        result.append((rel,p))
    return sorted(result)

def build(root:Path, out:Path):
    entries=files(root); fixed=(1980,1,1,0,0,0)
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel,path in entries:
            info=zipfile.ZipInfo(rel,date_time=fixed); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            z.writestr(info,path.read_bytes())
    return entries

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('root',type=Path); parser.add_argument('output',type=Path); args=parser.parse_args()
    root=args.root.resolve(); entries=build(root,args.output.resolve())
    print(json.dumps({'status':'PASS','zip':args.output.as_posix(),'sha256':sha(args.output),'size_bytes':args.output.stat().st_size,'files':len(entries)},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
__all__=['build']
# ponytail: stdlib zipfile with fixed metadata is sufficient; no release framework added.
