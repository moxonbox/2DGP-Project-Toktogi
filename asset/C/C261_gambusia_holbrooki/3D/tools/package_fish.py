"""Merge all exporters, pack compact pose geometry and lock the asset bundle."""
import hashlib
import gzip
import json
import sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime'))
from motion_spec import ASSET_ID,REVISION,VARIANTS,VIEWS,DESIGNS,PHASES,SEQUENCES,LOOPS,phase_duration
from fish_bundle import PASSES,signature,validate,sha
OUT=ROOT/'2D/gambusia-r01'
model=json.loads((ROOT/'3D/model_manifest.json').read_text())
contract=json.loads((ROOT/'document/source_contract.json').read_text(encoding='utf-8'))
source=sha(ROOT/'3D/gambusia_holbrooki_r01.blend')
manifest={'schema':1,'asset_id':ASSET_ID,'object_id':'predator_gambusia_holbrooki','revision':REVISION,
 'base_signature':contract['reference']['base_signature'],'source_blend_sha256':source,'passes':list(PASSES),
 'variants':VARIANTS,'views':{},'clips':{},'sequences':SEQUENCES,'files':{},'geometry':{},'contract':contract,
 'channels':{'sprite':'sRGB straight alpha, body palette quantization only, outline #22313B',
 'base':'unlit sRGB and linear coverage A; fins opacity .84',
 'normal':'linear RGB UNORM camera right/up/toward camera; A255; mask Base.A; renormalize',
 'ao':'linear grayscale vertex visibility from five .035 SL hemisphere rays; A255',
 'orm':'linear R=AO G=roughness B=metallic0; A255',
 'emissive':'linear RGB UV-fixed eye accent, scale1, A255, mask Base.A',
 'depth':'R high byte / G low byte UNORM16 world relative Z in [-SL,+SL], A255, mask Base.A',
 'watermask':'diagnostic local Z0: R above/G below. Runtime recomputes from Depth and physics root; A255'},
 'event_policy':{'surface_gape':'no attack or feed','surface_snap':'contact and active interval only, once per target per attack instance',
                 'splash/ripple':'actual deformed mesh water crossing, once per event/cycle','seek':'pose only, no event replay'}}
payload=set();reports=[]
for sex in VARIANTS:
    for view in VIEWS:
        part_path=OUT/f'part_{sex}_{view}.json'
        part=json.loads(part_path.read_text() if part_path.exists() else gzip.decompress(part_path.with_suffix('.json.gz').read_bytes()).decode('utf-8'))
        report=json.loads((OUT/f'validation_{sex}_{view}.json').read_text())
        assert report['status']=='PASS' and report['source_blend_sha256']==source
        reports.append(report)
        manifest['views'][sex+'/'+view]={k:part[k] for k in ('cell','pivot','camera_rotation','camera_location','ortho_scale','yaw','height_range')}
        for key,info in part['clips'].items():
            variant,action,phase=key.split('/')
            clip=manifest['clips'].setdefault(key,{'duration':phase_duration(action,phase),'loop':action in LOOPS and phase=='mid','views':{}})
            info['pass_files']={p:'2D/gambusia-r01/'+path for p,path in info['pass_files'].items()}
            clip['views'][view]=info
            payload.update(info['pass_files'].values())
            payload.add(f'2D/gambusia-r01/{sex}_{action}_{phase}_{view}.png')
            for sample in info['samples']:
                payload.add(sample['file'])
                sample.update(waterline_state='computed from pose + physics water level',splash_marker=None,cycle_id=None)
        if view=='left':
            ids=list(part['physics_poses']);poses=[part['physics_poses'][key] for key in ids]
            geometry_path=OUT/f'geometry_{sex}.npz'
            np.savez_compressed(geometry_path,pose_ids=np.array(ids),positions=np.array([p['vertices'] for p in poses],np.float32),
                triangles=np.array(part['triangles'],np.int32),body_count=model['variants'][sex]['body_vertices'],
                bounds=np.array([p['bounds'] for p in poses],np.float32))
            relative=geometry_path.relative_to(ROOT).as_posix();payload.add(relative)
            manifest['geometry'][sex]={'file':relative,'pose_count':len(ids),'mesh':'evaluated posed mesh, includes jaw and fins'}
for path in sorted(payload):manifest['files'][path]=sha(ROOT/path)
manifest['memory']={'raw_rgba_bytes':sum(v['cell']**2*4*len(PASSES)*len(DESIGNS)*18*len(VIEWS) for v in VARIANTS.values()),
 'cell_cache_entries':4,'decoded_cell_cache_max_bytes':4*640**2*4*len(PASSES),'renderer_cache_entries':24,'shaded_cache_entries':24,
 'policy':'stream individual cells; do not decode all atlases simultaneously','working_set_budget_bytes':512*1024**2}
manifest['signature']=signature(manifest);validate(manifest)
(OUT/'manifest.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
archive=OUT/'gambusia_holbrooki_r01.zip'
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=3) as z:
    z.write(OUT/'manifest.json','manifest.json')
    for path in sorted(payload):z.write(ROOT/path,path)
lock={k:manifest[k] for k in ('schema','asset_id','revision','base_signature','source_blend_sha256','signature')};lock['bundle_sha256']=sha(archive)
archive.with_suffix('.source.json').write_text(json.dumps(lock,indent=2))
report={'status':'PASS','variants':2,'actions':16,'phases':48,'views':4,'stacked_frames':2304,'passes':8,
 'source_blend_sha256':source,'payload_files':len(payload),'minimum_margin':min(r['minimum_margin'] for r in reports),
 'normal_error_max':max(r['normal_error'] for r in reports),'raw_rgba_bytes':manifest['memory']['raw_rgba_bytes'],
 'zip_bytes':archive.stat().st_size,'bundle_sha256':lock['bundle_sha256']}
(OUT/'package_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
