"""Publish a hash-locked additive delivery; never overwrite an unrelated file."""
import argparse,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime'))
from fish_bundle import sha

def payload():
    for folder in ('2D','3D','comparison','document','previews','runtime','sheet'):
        for path in (ROOT/folder).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix in ('.pyc','.blend1'):continue
            if path.name.startswith('part_') and path.suffix=='.json':continue
            if path.name in ('validation_female_left_surface_gape.json','part_female_left_surface_gape.json'):continue
            yield path
    for name in ('ASSET_INDEX.md','GambusiaMotionPreview.html','PlayGambusia.cmd','requirements.txt'):yield ROOT/name

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path);args=parser.parse_args()
    files={path.relative_to(ROOT).as_posix():{'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(payload())}
    ledger={'schema':1,'asset_id':'C261_gambusia_holbrooki','revision':'gambusia-r01','files':files,
            'total_files':len(files),'total_bytes':sum(v['bytes'] for v in files.values()),'excludes':['delivery_manifest.json itself','temporary logs/caches/plain export-worker JSON/unarchived drafts']}
    ledger_path=ROOT/'delivery_manifest.json';ledger_path.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
    if not args.destination:print(json.dumps({k:v for k,v in ledger.items() if k!='files'},indent=2));return
    destination=args.destination.resolve()
    original=json.loads((ROOT/'document/original_spec_hashes.json').read_text())
    for relative,digest in original.items():
        if sha(destination/relative)!=digest:raise ValueError('original specification changed: '+relative)
    files['delivery_manifest.json']={'sha256':sha(ledger_path),'bytes':ledger_path.stat().st_size}
    # Complete collision and path preflight before the first write.
    for relative,info in files.items():
        target=(destination/relative).resolve()
        if not target.is_relative_to(destination):raise ValueError('outside destination: '+relative)
        if target.exists() and sha(target)!=info['sha256']:raise ValueError('refusing unrelated overwrite: '+relative)
    copied=0
    for relative,info in files.items():
        source=ROOT/relative;target=destination/relative
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied+=1
        if sha(target)!=info['sha256']:raise ValueError('copy hash mismatch: '+relative)
    print(json.dumps({'status':'PASS','destination':str(destination),'copied_files':copied,'verified_files':len(files),'bytes':ledger['total_bytes']},indent=2))

if __name__=='__main__':main()
