"""CPU gates deliberately exclude all native libraries and device claims."""
from pathlib import Path
import contextlib,hashlib,json,sys,time

def verify(*,asset_root=None):
    root=Path(__file__).resolve().parent
    started=time.perf_counter()
    from verify_prototype import verify as legacy
    from verify_timeline import verify as timeline
    from verify_world import verify as world
    from verify_input import verify as inputs
    from verify_materials import verify as materials
    with (root/'verification.log').open('w',encoding='utf-8') as output,contextlib.redirect_stdout(output):legacy()
    report={'legacy':'verification.json','timeline':timeline(),'world':world(),'input':inputs(),'materials':materials()}
    from materials import Assets
    from verify_world_game import verify as gameplay
    from verify_replays import verify as replays
    from verify_environment import verify as environment
    from camera import verify as camera
    assets=Assets(root/'toktogi_assets.zip')
    try:
        original=root.parent/'prototype/game.py'
        report['world_game']=gameplay(assets,original if original.is_file() else None)
        report['replays'],trace=replays(assets)
    finally:assets.close()
    report['environment']=environment(asset_root)
    report['camera']=camera()
    from verify_pond import verify as pond
    from verify_controls import verify as controls
    assets=Assets(root/'toktogi_assets.zip')
    try:report['pond']=pond(assets)
    finally:assets.close()
    report['controls']=controls(asset_root)
    from verify_stage_menu import verify as stage_menu
    report['stage_menu']=stage_menu(asset_root=asset_root)
    from verify_storyboard import verify as storyboard
    report['storyboard']=storyboard(asset_root=asset_root)
    assert not any(name in sys.modules for name in ('pygame','sdl2','pico2d'))
    report['no_video_imports']=True
    report['seconds']=round(time.perf_counter()-started,3)
    report['native_acceptance']='Separate verify_backend.py / verify_native_input.py; real device acceptance pending'
    report['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.py'))}
    (root/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'CPU checks passed: {root / "acceptance.json"}')
    return report

if __name__=='__main__':verify()
