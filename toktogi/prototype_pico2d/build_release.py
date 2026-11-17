"""Create a runtime archive with pinned source bytes and restoration baseline."""
from pathlib import Path
import argparse,hashlib,json
from zipfile import ZipFile,ZIP_DEFLATED

def build(project,output):
    project=Path(project).resolve();output=Path(output).resolve()
    candidate=project/'toktogi/prototype_pico2d'
    files=[]
    extensions={'.py','.md','.txt','.cmd','.json','.zip','.html','.png'}
    for folder in (candidate,project/'toktogi/prototype',project/'document/markdown'):
        files.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in extensions
                     and not set(p.relative_to(folder).parts)&{'.venv','__pycache__','dist'})
    environment=project/'asset/A/A01_plant_lemna_minor'
    data=json.loads((environment/'2D/environment-r02/manifest.json').read_bytes())
    files.extend(p for p in (environment/'2D/environment-r02').rglob('*') if p.is_file())
    files.extend((environment/'ASSET_INDEX.md',environment/data['source_blend']))
    architecture=project/'document/ToktogiPico2DArchitecture.html'
    if architecture.is_file():files.append(architecture)
    records={}
    for path in sorted(set(files)):
        path=path.resolve()
        if not path.is_relative_to(project):raise ValueError(f'Release file escapes project: {path}')
        records[path.relative_to(project).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest={'schema':1,'kind':'runtime candidate and legacy rollback',
              'omitted':'venvs, build-time C011 atlases and Blender authoring tools; regenerate catalogs in the source repository',
              'physical_acceptance':'Not tested; Computer-Use declined',
              'files':records}
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.tmp')
    try:
        with ZipFile(temporary,'w',ZIP_DEFLATED,compresslevel=6) as archive:
            for name in records:archive.write(project/name,name)
            archive.writestr('release_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        with ZipFile(temporary) as archive:
            if archive.testzip() is not None:raise ValueError('Release ZIP CRC failure')
            for name,expected in records.items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=expected:raise ValueError(name)
        temporary.replace(output)
    finally:temporary.unlink(missing_ok=True)
    result={'path':str(output),'files':len(records),'bytes':output.stat().st_size,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    output.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'artifact/ToktogiPico2D-runtime.zip')
    args=parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[2],args.output),ensure_ascii=False,indent=2))
