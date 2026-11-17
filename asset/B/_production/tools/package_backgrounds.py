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

ROOT=Path(__file__).resolve().parents[2]
PRODUCTION=ROOT/'_production'
CONFIG=json.loads((PRODUCTION/'assets.json').read_text(encoding='utf-8'))
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
SMALL=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14)


def save_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def board(directory,config):
    canvas=Image.new('RGB',(1200,900),'#e8e9df');d=ImageDraw.Draw(canvas)
    d.text((22,15),f"{config['id']}  {config['name']} / Blender reference / r01",font=FONT,fill='#22313b')
    for i,view in enumerate(('game','front','left','right','back','top','underside')):
        x=20+(i%4)*295;y=60+(i//4)*390
        im=Image.open(directory/f'2D/previews/{view}.png').convert('RGBA')
        scale=min(270/im.width,315/im.height)
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
        d.rectangle((x,y,x+280,y+350),fill='#c9d2c5')
        canvas.paste(im,(x+(280-im.width)//2,y+(320-im.height)//2),im)
        d.text((x+8,y+324),view+f'  preview {scale:.2f}x',font=SMALL,fill='#22313b')
    d.text((25,850),'각 패널은 검수용 맞춤 축소. 실제 표시 크기·피벗은 2D/manifest.json 기준.',font=SMALL,fill='#22313b')
    canvas.save(directory/'sheet'/f'{config["name"]}_blender_reference_r01.png')


def overview():
    canvas=Image.new('RGB',(1600,1120),'#e8e9df');draw=ImageDraw.Draw(canvas)
    for i,config in enumerate(CONFIG):
        directory=ROOT/config['folder'];manifest=json.loads((directory/'2D/manifest.json').read_text(encoding='utf-8'))
        im=Image.open(directory/'2D/previews/game.png').convert('RGBA')
        im.thumbnail((375,270),Image.Resampling.NEAREST);x=(i%4)*400;y=(i//4)*365
        draw.rectangle((x+8,y+8,x+392,y+295),fill='#c6d1c4')
        canvas.paste(im,(x+(400-im.width)//2,y+10+(280-im.height)//2),im)
        draw.text((x+12,y+300),config['id']+' '+config['name'].removeprefix('plant_').removeprefix('env_'),font=FONT,fill='#22313b')
        draw.text((x+12,y+326),str(manifest['views']['game']['cell'])+' px / fit preview',font=FONT,fill='#22313b')
    canvas.save(PRODUCTION/'overview.png')


def package():
    bundle={'schema':'toktogi.background-bundle/1','revision':'background-r01','passes':PASSES,'assets':{},'files':{}}
    for config in CONFIG:
        directory=ROOT/config['folder'];asset=json.loads((directory/'2D/manifest.json').read_text(encoding='utf-8'))
        blend=directory/'3D'/f'{config["name"]}_r01.blend'
        assert sha(blend)==asset['source_blend_sha256'],(config['id'],'stale export: source Blend changed')
        asset['folder']=config['folder'];asset['status']['standalone_loader']='verified_separately'
        for cell in asset['views'].values():
            path=directory/cell['file'];bundle['files'][config['folder']+'/'+cell['file']]=sha(path)
        bundle['assets'][asset['asset_id']]=asset
    bundle['signature']=signature(bundle);validate(bundle)
    dest=PRODUCTION/'backgrounds_r01.zip'
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
        ('nonfinite_pivot',lambda m:next(iter(m['assets'].values()))['views']['game']['pivot'].__setitem__(0,float('nan'))),
        ('out_of_bounds',lambda m:next(iter(m['assets'].values()))['views']['game']['bbox'].__setitem__(2,999999)),
        ('missing_cell',lambda m:m['files'].pop(next(iter(m['files'])))),
        ('duplicate_cell',lambda m:next(iter(m['assets'].values()))['views']['front'].update(file=next(iter(m['assets'].values()))['views']['game']['file'])),
    ):
        bad=copy.deepcopy(reader.manifest);mutate(bad);bad['signature']=signature(bad)
        try:validate(bad)
        except ValueError:negatives.append(label)
        else:raise AssertionError(label)
    key=next(iter(reader.manifest['files']));old=reader.manifest['files'][key]
    first=next(iter(reader.manifest['assets']));reader.cache.clear();reader.manifest['files'][key]='0'*64
    try:reader.maps(first,'game')
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
            cell=reader.manifest['assets'][name]['views']['game'];pivot=cell['pivot']
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
    print(json.dumps(report,ensure_ascii=False,indent=2))
