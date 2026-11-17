"""Install a verified revision after proving its complete predecessor restoration."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runtime'),str(ROOT/'3D/tools')]
from fish_bundle import sha,FishBundle
from publish_asset import payload

def main():
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);args=parser.parse_args();destination=args.destination.resolve()
    archive=ROOT/'3D/versions/gambusia-r01.7z';restore=json.loads((archive.parent/'restore_map.json').read_text())
    assert restore['restoration_status']=='PASS' and sha(archive)==restore['archive_sha256']
    previous_path=archive.parent/'r01_delivery_manifest.json';previous=json.loads(previous_path.read_text())
    assert sha(destination/'delivery_manifest.json')==sha(previous_path),'live revision changed'
    for relative,info in previous['files'].items():
        path=(destination/relative).resolve();assert path.is_relative_to(destination),relative
        assert sha(path)==info['sha256'],relative
    pixel=json.loads((ROOT/'document/sprite_revision_validation.json').read_text());assert pixel['status']=='PASS' and pixel['frames']==2304
    entries={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(payload())}
    for relative,info in entries.items():
        target=(destination/relative).resolve();assert target.is_relative_to(destination),relative
        if target.exists() and relative not in previous['files']:assert sha(target)==info['sha256'],'unrelated collision: '+relative
    # The verified archive is installed before replacing any live file.
    ordered=sorted(entries,key=lambda name:(name!='3D/versions/gambusia-r01.7z',name))
    copied=0
    for relative in ordered:
        source=ROOT/relative;target=destination/relative
        if target.exists() and sha(target)==entries[relative]['sha256']:continue
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(target.name+'.r03-copying');assert not temporary.exists()
        shutil.copy2(source,temporary);assert sha(temporary)==entries[relative]['sha256'];temporary.replace(target);copied+=1
    assert sha(destination/'3D/versions/gambusia-r01.7z')==restore['archive_sha256']
    retired=[]
    for relative in previous['files'].keys()-entries.keys():
        target=(destination/relative).resolve();assert target.is_relative_to(destination)
        assert sha(target)==previous['files'][relative]['sha256']
        target.unlink();retired.append(relative)
    for folder in sorted({(destination/relative).parent for relative in retired},key=lambda p:len(p.parts),reverse=True):
        while folder!=destination and folder.is_relative_to(destination):
            try:folder.rmdir()
            except OSError:break
            folder=folder.parent
    bundle=FishBundle(destination/'2D/gambusia-r03/gambusia_holbrooki_r03.zip')
    for sex in ('female','male'):assert len(bundle.maps(bundle.cell(sex,'surface_gape','mid',.5)))==8
    signature=bundle.manifest['signature'];bundle.close()
    blender='C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe'
    result=subprocess.run([blender,'-b',str(destination/'3D/gambusia_holbrooki_r03.blend'),'-t','2','--python',str(destination/'3D/tools/verify_relocation.py')],capture_output=True,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
    lines=[line for line in result.stdout.splitlines() if line.startswith('{"status"')];assert lines,(result.stdout,result.stderr)
    native=json.loads(lines[-1]);assert native['status']=='PASS'
    receipt={'status':'PASS','copied_files':copied,'retired_live_files':len(retired),'predecessor_restored_files':restore['restored_and_hash_verified_files'],
             'archive_sha256':restore['archive_sha256'],'runtime_signature':signature,'native_reopen':native}
    rel='document/relocation_validation.json';text=json.dumps(receipt,indent=2)
    (ROOT/rel).write_text(text,encoding='utf-8');(destination/rel).write_text(text,encoding='utf-8')
    entries[rel]={'sha256':sha(ROOT/rel),'bytes':(ROOT/rel).stat().st_size}
    ledger={'schema':1,'asset_id':'C261_gambusia_holbrooki','revision':'gambusia-r03','files':entries,'total_files':len(entries),'total_bytes':sum(v['bytes'] for v in entries.values()),'excludes':['delivery_manifest.json itself','temporary authoring caches']}
    text=json.dumps(ledger,indent=2)
    (ROOT/'delivery_manifest.json').write_text(text,encoding='utf-8');(destination/'delivery_manifest.json').write_text(text,encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
