"""Pack static cells, record provenance, build review boards and verify the bundle."""
import copy
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from background_bundle import BackgroundBundle, PASSES, signature, validate
from shared_lighting import fields, shade

ROOT=Path(__file__).resolve().parents[3]
PRODUCTION=ROOT/'_production/r02'
CONFIG=json.loads((PRODUCTION/'assets.json').read_text(encoding='utf-8'))
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
SMALL=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14)


def save_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def board(directory,config):
    manifest=json.loads((directory/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
    views=list(manifest['views'])
    canvas=Image.new('RGB',(1600,1380),'#e8e9df');draw=ImageDraw.Draw(canvas)
    draw.text((20,15),config['id']+' / C011 matched yaw + orthographic inspection / r02',font=FONT,fill='#22313b')
    for i,view in enumerate(views):
        x=16+(i%5)*318;y=55+(i//5)*430
        im=Image.open(directory/f'2D/background-r02/previews/{view}.png').convert('RGBA')
        scale=min(294/im.width,355/im.height)
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
        draw.rectangle((x,y,x+302,y+398),fill='#c9d2c5')
        canvas.paste(im,(x+(302-im.width)//2,y+8+(360-im.height)//2),im)
        draw.text((x+8,y+368),view+f' / fit {scale:.2f}x',font=SMALL,fill='#22313b')
    draw.text((20,1350),'각 셀은 검수판에 맞춘 축소. 게임 표시 배율은 모든 방향에서 1×.',font=SMALL,fill='#22313b')
    canvas.save(directory/'sheet'/f'{config["name"]}_blender_reference_r02.png')


def overview():
    canvas=Image.new('RGB',(1600,1120),'#e8e9df');draw=ImageDraw.Draw(canvas)
    for i,config in enumerate(CONFIG):
        directory=ROOT/config['folder'];manifest=json.loads((directory/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
        im=Image.open(directory/'2D/background-r02/previews/left.png').convert('RGBA')
        im.thumbnail((375,270),Image.Resampling.NEAREST);x=(i%4)*400;y=(i//4)*365
        draw.rectangle((x+8,y+8,x+392,y+295),fill='#c6d1c4')
        canvas.paste(im,(x+(400-im.width)//2,y+10+(280-im.height)//2),im)
        draw.text((x+12,y+300),config['id']+' '+config['name'].removeprefix('plant_').removeprefix('env_'),font=FONT,fill='#22313b')
        draw.text((x+12,y+326),str(manifest['views']['left']['cell'])+' px / fit preview',font=FONT,fill='#22313b')
    canvas.save(PRODUCTION/'overview.png')


def direction_review():
    contract=json.loads((PRODUCTION/'reference/c011_view_contract.json').read_text(encoding='utf-8'))
    x,y,z=contract['coordinate_contract']['camera_rotation_euler']
    cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    camera=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]]) @ np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    error=0.;checked=0
    for config in CONFIG:
        directory=ROOT/config['folder']
        manifest=json.loads((directory/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
        model=json.loads((directory/'3D/model_manifest_r02.json').read_text(encoding='utf-8'))
        assert manifest['view_contract_source_sha256']==contract['source_sha256']
        for view,yaw in contract['views'].items():
            cell=manifest['views'][view];assert abs(cell['yaw_rad']-yaw)<1e-10
            c,s=np.cos(yaw),np.sin(yaw);rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
            for label,point in model['anchors_bu'].items():
                plane=camera.T@rotation@np.array(point)
                delta=(plane[:2]-cell['camera_center_plane_bu'])*128/1.78
                expected=np.array(cell['cell'])/2+delta*[1,-1]
                error=max(error,float(np.max(abs(expected-cell['anchors'][label]))));checked+=1
    assert error<.002,('anchor projection',error)
    save_json(PRODUCTION/'direction_validation.json',{'status':'PASS','assets':11,'game_views_per_asset':9,
        'anchors_checked':checked,'maximum_anchor_error_px':error,'tolerance_px':.002,
        'method':'Independent NumPy Euler-camera and world-Z-yaw projection from model anchors.',
        'source_sha256':contract['source_sha256'],'right_is_yaw_180':False})
    board=Image.new('RGB',(1920,960),'#e8e9df');draw=ImageDraw.Draw(board)
    for i,view in enumerate(contract['views']):
        ox=(i%3)*640;oy=(i//3)*320
        draw.rectangle((ox+5,oy+5,ox+635,oy+295),fill='#c6d1c4')
        draw.text((ox+12,oy+12),view+' / 1x / C011 + B01 + B03',font=FONT,fill='#22313b')
        stack=Image.open(PRODUCTION/f'reference/C011_idle_{view}_0_stacked.png').convert('RGBA')
        im=stack.crop((0,0,128,128));board.paste(im,(ox+85,oy+100),im)
        for config,px in ((CONFIG[0],355),(CONFIG[2],545)):
            d=ROOT/config['folder'];m=json.loads((d/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
            im=Image.open(d/f'2D/background-r02/previews/{view}.png').convert('RGBA');pivot=m['views'][view]['pivot']
            board.paste(im,(ox+round(px-pivot[0]),oy+round(180-pivot[1])),im)
    board.save(PRODUCTION/'c011_directions_1x.png')
    before_after=Image.new('RGB',(1600,1140),'#e8e9df');draw=ImageDraw.Draw(before_after)
    for i,config in enumerate(CONFIG):
        x=(i%4)*400;y=(i//4)*380
        paths=[PRODUCTION/'before'/config['folder']/'game.png',ROOT/config['folder']/'2D/background-r02/previews/left.png']
        for j,path in enumerate(paths):
            im=Image.open(path).convert('RGBA');im.thumbnail((182,285),Image.Resampling.NEAREST)
            draw.rectangle((x+j*198+5,y+5,x+j*198+195,y+305),fill='#c6d1c4')
            before_after.paste(im,(x+j*198+(198-im.width)//2,y+12+(285-im.height)//2),im)
            draw.text((x+j*198+12,y+310),('r01' if j==0 else 'r02')+' / fit',font=SMALL,fill='#22313b')
        draw.text((x+12,y+338),config['id']+' '+config['name'].removeprefix('plant_').removeprefix('env_'),font=SMALL,fill='#22313b')
    before_after.save(PRODUCTION/'before_after.png')


def package():
    bundle={'schema':'toktogi.background-bundle/1','revision':'background-r02','passes':PASSES,'assets':{},'files':{}}
    for config in CONFIG:
        directory=ROOT/config['folder'];asset=json.loads((directory/'2D/background-r02/manifest.json').read_text(encoding='utf-8'))
        blend=directory/'3D'/f'{config["name"]}_r02.blend'
        assert sha(blend)==asset['source_blend_sha256'],(config['id'],'stale export: source Blend changed')
        asset['folder']=config['folder'];asset['status']['standalone_loader']='verified_separately'
        for cell in asset['views'].values():
            path=directory/cell['file'];bundle['files'][config['folder']+'/'+cell['file']]=sha(path)
        bundle['assets'][asset['asset_id']]=asset
    bundle['signature']=signature(bundle);validate(bundle)
    dest=PRODUCTION/'backgrounds_r02.zip'
    with ZipFile(dest,'w',ZIP_STORED) as archive:
        archive.writestr('manifest.json',json.dumps(bundle,ensure_ascii=False,separators=(',',':')))
        for path in sorted(bundle['files']):archive.write(ROOT/path,path)
    save_json(dest.with_suffix('.source.json'),{'schema':bundle['schema'],'revision':bundle['revision'],
              'signature':bundle['signature'],'bundle_sha256':sha(dest),'files':len(bundle['files'])})
    return dest


def verify(dest):
    start=time.perf_counter();reader=BackgroundBundle(dest);load_ms=(time.perf_counter()-start)*1000
    checks=[];total=0
    for name,asset in reader.manifest['assets'].items():
        for view,cell in asset['views'].items():
            maps=reader.maps(name,view);arrays={p:np.asarray(v) for p,v in maps.items()};base=arrays['base'];mask=base[:,:,3]>0
            assert mask.any(),(name,view)
            for p in PASSES:
                direct=np.asarray(Image.open(ROOT/asset['folder']/cell['pass_files'][p]))
                assert np.array_equal(arrays[p],direct),(name,view,p,'stack/pass mismatch')
            assert all(np.all(arrays[p][:,:,3]==255) for p in PASSES[2:])
            normal=arrays['normal'][mask,:3]/255*2-1
            assert np.max(abs(np.linalg.norm(normal,axis=1)-1))<.015
            assert not arrays['emissive'][:,:,:3].any()
            assert not arrays['rm'][:,:,1:3].any()
            for p in ('sprite','base'):
                transparent=arrays[p][:,:,3]==0
                assert not arrays[p][transparent,:3].any(),'Transparent RGB must be zero'
            total+=cell['cell'][0]*cell['cell'][1]*4*5
            checks.append(name+'/'+view)
    negatives=[]
    for label,mutate in (
        ('schema',lambda m:m.update(schema='unknown')),
        ('missing_pass',lambda m:m['passes'].pop()),
        ('nonfinite_pivot',lambda m:next(iter(m['assets'].values()))['views']['left']['pivot'].__setitem__(0,float('nan'))),
        ('out_of_bounds',lambda m:next(iter(m['assets'].values()))['views']['left']['bbox'].__setitem__(2,999999)),
        ('wrong_yaw',lambda m:next(iter(m['assets'].values()))['views']['right'].update(yaw_rad=3.14159265)),
        ('missing_cell',lambda m:m['files'].pop(next(iter(m['files'])))),
        ('duplicate_cell',lambda m:next(iter(m['assets'].values()))['views']['right'].update(file=next(iter(m['assets'].values()))['views']['left']['file'])),
    ):
        bad=copy.deepcopy(reader.manifest);mutate(bad);bad['signature']=signature(bad)
        try:validate(bad)
        except ValueError:negatives.append(label)
        else:raise AssertionError(label)
    key=next(iter(reader.manifest['files']));old=reader.manifest['files'][key]
    first=next(iter(reader.manifest['assets']));reader.cache.clear();reader.manifest['files'][key]='0'*64
    try:reader.maps(first,'left')
    except ValueError:negatives.append('payload_hash_mismatch')
    else:raise AssertionError('Corrupted payload accepted')
    reader.manifest['files'][key]=old
    try:reader.draw(Image.new('RGBA',(960,560)), 'env_diatoms_micro',(0,0))
    except ValueError:negatives.append('microscopy_gameplay_rejected')
    else:raise AssertionError('Microscopy asset entered world')
    # Representative independent background scene; no main-game integration claim.
    placements=[('plant_typha_orientalis',(220,530)),('plant_phragmites_australis',(720,615)),
                ('plant_lemna_perpusilla',(350,320)),('plant_wolffia_arrhiza',(600,345))]
    def frame(camera=(0,0)):
        canvas=Image.new('RGBA',(960,560),'#c6d1c4')
        for name,pos in placements:reader.draw(canvas,name,pos,camera)
        return canvas
    c011stack=Image.open(PRODUCTION/'reference/C011_idle_left_0_stacked.png').convert('RGBA')
    c011maps={p:c011stack.crop((0,i*128,128,(i+1)*128)) for i,p in enumerate(PASSES)}
    canvas=frame();c011=c011maps['sprite']
    canvas.alpha_composite(c011,(420,230));canvas.save(PRODUCTION/'comparison_1x.png')
    gray=canvas.convert('L').convert('RGB');gray.save(PRODUCTION/'comparison_grayscale_1x.png')
    srgb_table=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in range(256)]
    light_frames=[]
    for lx,ly in ((260,100),(680,120)):
        lit=Image.new('RGBA',(960,560),'#c6d1c4')
        for name,pos in placements:
            cell=reader.manifest['assets'][name]['views']['left'];pivot=cell['pivot']
            at=(round(pos[0]-pivot[0]),round(pos[1]-pivot[1]))
            im=shade(fields(reader.maps(name),[],srgb_table),lx-at[0],at[1]-ly,None,None,.82,True,.34,1.)
            lit.alpha_composite(im,at)
        lit.alpha_composite(shade(fields(c011maps,[],srgb_table),lx-420,230-ly,None,None,.82,True,.34,1.),(420,230))
        lit.save(PRODUCTION/f'comparison_light_{lx}.png');light_frames.append(lit)
    assert light_frames[0].tobytes()!=light_frames[1].tobytes(),'Moving light produced identical frame'
    for name,_ in placements:reader.maps(name)
    timings=[]
    for _ in range(120):
        start=time.perf_counter();frame();timings.append((time.perf_counter()-start)*1000)
    report={'status':'PASS_STANDALONE_STATIC','assets':len(CONFIG),'cells':len(checks),'passes':5,
            'decoded_rgba_bytes_all_views':total,'bundle_bytes':dest.stat().st_size,'negative_tests':negatives,
            'startup_ms':load_ms,'p95_composite_ms':float(np.percentile(timings,95)),'max_composite_ms':max(timings),
            'frames':120,'sample_scene_assets':len(placements),'device':platform.platform(),
            'scope':'Pillow CPU decode + static alpha composite. No SDL upload, main game, Pico2D or final device frame-budget claim.',
            'cache_limit_cells':8,'main_game':'NOT_INTEGRATED','DEC-06':'DEFERRED','mcp':'TIMEOUT_CLI_FALLBACK'}
    report['shared_light_comparison']={'positions_px':[[260,100],[680,120]],'power':.82,'ambient':.34,'same_world_light_per_object':True}
    save_json(PRODUCTION/'runtime_validation.json',report)
    reader.close();return report


if __name__=='__main__':
    dest=package();report=verify(dest)
    for config in CONFIG:board(ROOT/config['folder'],config)
    overview()
    direction_review()
    print(json.dumps(report,ensure_ascii=False,indent=2))
