"""Validate and inspect the separate environment bundle without changing the game."""
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PASSES=['sprite','base','normal','rm','emissive']
FONT=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
SRGB=[i/255/12.92 if i<=10 else ((i/255+.055)/1.055)**2.4 for i in range(256)]


def load_cell(folder, manifest, cell):
    key=f"{manifest['asset_id']}/{cell['view']}/{cell['sample']}"
    root=(folder/'2D/environment-r01').resolve()
    path=(root/cell['file']).resolve()
    if not path.is_relative_to(root): raise ValueError(f'{key}: path outside bundle')
    if manifest['schema']!='toktogi_environment/1' or manifest['pass_order']!=PASSES:
        raise ValueError(f'{key}: unsupported schema or pass order')
    width,height=manifest['cell_size']
    if not all(isinstance(v,int) and 16<=v<=1024 for v in (width,height)):
        raise ValueError(f'{key}: unsupported size')
    if sha256(path.read_bytes()).hexdigest()!=cell['sha256']: raise ValueError(f'{key}: checksum mismatch')
    with Image.open(path) as image:
        if image.mode!='RGBA' or image.size!=(width,height*5): raise ValueError(f'{key}: invalid material PNG')
        maps={p:image.crop((0,i*height,width,(i+1)*height)).copy() for i,p in enumerate(PASSES)}
    if not all(math.isfinite(v) for v in cell['pivot']): raise ValueError(f'{key}: nonfinite pivot')
    if not math.isfinite(cell['duration_s']) or cell['duration_s']<=0: raise ValueError(f'{key}: invalid duration')
    return maps


def fields_for_size(maps):
    import lighting
    fields=list(lighting.fields(maps,(),SRGB))
    w,h=maps['sprite'].size
    y,x=np.mgrid[:h,:w].astype(np.float32)
    fields[2]=Image.fromarray(x); fields[3]=Image.fromarray(y)
    return tuple(fields)


def composite(cells, backgrounds, light=None):
    import lighting
    rows=[]
    for start in range(0,len(cells),2):
        group=cells[start:start+2]
        above=max(88,*(e[2]['pivot'][1]-e[1]['sprite'].getbbox()[1] for e in group))
        below=max(40,*(e[1]['sprite'].getbbox()[3]-e[2]['pivot'][1] for e in group))
        rows.append((round(above),round(above+below+85)))
    canvas=Image.new('RGBA',(1660,50+sum(r[1] for r in rows)),'#E8ECE9')
    draw=ImageDraw.Draw(canvas)
    draw.text((24,12),'A01–A07 · environment-r01 · 1× / C011 scale · production candidate',font=FONT,fill='#22313B')
    for i,entry in enumerate(cells):
        c,maps,cell,fields=entry
        col,row=i%2,i//2
        box=(col*830+20,50+sum(r[1] for r in rows[:row]))
        sprite=maps['sprite']
        if light:
            sprite=lighting.shade(fields,light[0],light[1],None,None,.82,True,.34,1)
        bounds=sprite.getbbox()
        crop=sprite.crop(bounds)
        x,y=box
        draw.text((x,y),c['folder']+' · '+str(c['cell_size'])+'px cell',font=FONT,fill='#22313B')
        # Cropping removes only transparent margins; every displayed asset pixel stays 1×.
        baseline=y+35+rows[row][0]
        crop_pivot=cell['pivot'][1]-bounds[1]
        cy=round(baseline-crop_pivot)
        canvas.alpha_composite(crop,(x+12,cy))
        ref=backgrounds.copy()
        canvas.alpha_composite(ref,(x+crop.width+38,baseline-88))
        draw.line((x,baseline,x+790,baseline),fill='#ADB8B3')
        draw.text((x+570,y+rows[row][1]-26),'C011 / same BU per px',font=FONT,fill='#435361')
    return canvas


def verify():
    import lighting
    configs=json.loads((HERE/'assets.json').read_text(encoding='utf-8'))
    refs=Image.open(HERE/'reference/C011_idle.png').convert('RGBA')
    # The source preview includes a checker background; retrieve the genuine transparent sprite.
    reference_sprite=HERE/'reference/C011_idle_sprite.png'
    if reference_sprite.exists(): refs=Image.open(reference_sprite).convert('RGBA')
    reference_maps={p:Image.open(HERE/'reference'/f'C011_idle_{p}.png').convert('RGBA') for p in PASSES}
    reference_fields=fields_for_size(reference_maps)
    reference_emission=json.loads((HERE/'reference/C011_channels.json').read_text(encoding='utf-8'))['emissive']['scale']
    results=[]; preview=[]; file_lock={}; raw_bytes=0
    for c in configs:
        folder=ROOT/c['folder']; out=folder/'2D/environment-r01'
        manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
        assert manifest['asset_id']==c['asset_id'] and manifest['revision']==c['revision']
        assert len(manifest['cells'])==len(c['supported_views'])==7
        assert len({(v['view'],v['sample']) for v in manifest['cells']})==7
        assert {v['view'] for v in manifest['cells']}==set(c['supported_views'])
        assert manifest['world_units_per_pixel']==1.78/128
        assert sha256((folder/manifest['source_blend']).read_bytes()).hexdigest()==manifest['source_blend_sha256']
        samples=[]
        for cell in manifest['cells']:
            maps=load_cell(folder,manifest,cell)
            arrays={p:np.array(im) for p,im in maps.items()}
            coverage=arrays['base'][:,:,3]>0
            assert coverage.any() and set(np.unique(arrays['sprite'][:,:,3])).issubset({0,255})
            assert np.all(arrays['sprite'][:,:,3][coverage]==255)
            for p in ('normal','rm','emissive'): assert np.all(arrays[p][:,:,3]==255)
            normal=arrays['normal'][:,:,:3][coverage]/255*2-1
            normal_error=float(np.max(abs(np.linalg.norm(normal,axis=1)-1)))
            assert normal_error<.008, (c['folder'],cell['view'],normal_error)
            assert not arrays['rm'][:,:,1:3].any() and not arrays['emissive'][:,:,:3].any()
            for p in ('sprite','base'):
                assert list(maps[p].getbbox())==cell['bbox'][p]
                x0,y0,x1,y1=cell['bbox'][p]; w,h=maps[p].size
                assert min(x0,y0,w-x1,h-y1)>=8
                outside=arrays[p][:,:,3]==0
                assert not arrays[p][:,:,:3][outside].any(), 'hidden RGB in transparent pixels'
            for key,marker in cell['anchors'].items():
                assert all(math.isfinite(v) for v in marker['xy']+marker['world']),key
            samples.append({'view':cell['view'],'sprite_bbox':cell['bbox']['sprite'],'normal_unit_error':normal_error})
            raw_bytes+=c['cell_size']**2*5*4
            if cell['view']=='game_left': preview.append((c,maps,cell,fields_for_size(maps)))
        # Trust-boundary regressions: stale hash, traversal and invalid duration must fail.
        original=manifest['cells'][0]
        for mutation in ({'sha256':'0'*64},{'file':'../../escape.png'},{'duration_s':0},{'pivot':[float('nan'),0]}):
            try: load_cell(folder,manifest,dict(original,**mutation))
            except ValueError: pass
            else: raise AssertionError(('invalid input accepted',mutation))
        results.append({'asset_id':c['asset_id'],'cells':len(samples),'views':samples,'pixel_validation':'PASS','negative_input_checks':4})
    assert len(results)==7
    composite(preview,refs).save(HERE/'overview_1x.png')
    ImageOps.grayscale(composite(preview,refs)).save(HERE/'overview_grayscale.png')
    # Same world light for the asset and C011; the paired plates are built below.
    for c,maps,cell,fields in preview:
        folder=ROOT/c['folder']; sprite=maps['sprite']; x0,y0,x1,y1=cell['bbox']['sprite']
        w=max(560,x1-x0+210); h=max(260,y1-y0+110)
        board=Image.new('RGBA',(w,h*2),'#E8ECE9'); draw=ImageDraw.Draw(board)
        draw.text((16,12),c['folder']+' / 1× / C011 body 1.0 mm reference',font=FONT,fill='#22313B')
        pivot=cell['pivot']; base_y=max(100,45+round(pivot[1]-y0))
        origin=(20-x0,base_y-round(pivot[1]))
        board.alpha_composite(sprite,origin)
        board.alpha_composite(refs,(w-145,base_y-88))
        draw.line((10,base_y,w-10,base_y),fill='#ADB8B3')
        row=board.crop((0,0,w,h)).convert('RGB'); gray=ImageOps.grayscale(row).convert('RGBA')
        board.alpha_composite(gray,(0,h))
        board.save(folder/'2D/environment-r01/style_compare.png')
        lighting_board=Image.new('RGBA',(w,h*2),'#E8ECE9')
        reference_origin=(w-145,base_y-88)
        for row,light in enumerate(((w*.25,20),(w*.8,20))):
            asset_lit=lighting.shade(fields,light[0]-origin[0],origin[1]-light[1],None,None,.82,True,.34,1)
            actor_lit=lighting.shade(reference_fields,light[0]-reference_origin[0],reference_origin[1]-light[1],None,None,.82,True,.34,reference_emission)
            lighting_board.alpha_composite(asset_lit,(origin[0],origin[1]+row*h))
            lighting_board.alpha_composite(actor_lit,(reference_origin[0],reference_origin[1]+row*h))
            ImageDraw.Draw(lighting_board).text((16,row*h+12),f'Shared scene light {row+1} / power .82 / ambient .34',font=FONT,fill='#22313B')
        lighting_board.save(folder/'2D/environment-r01/shared_light_compare.png')
        # Native 3D view comparison uses the same pixel density in every camera.
        m=json.loads((folder/'2D/environment-r01/manifest.json').read_text(encoding='utf-8'))
        sheet=Image.new('RGBA',(3*c['cell_size'],2*(c['cell_size']+30)),'#F4F2E9')
        d=ImageDraw.Draw(sheet)
        for i,view in enumerate(['front','left','right','back','top','game_left']):
            cl=next(cl for cl in m['cells'] if cl['view']==view)
            im=load_cell(folder,m,cl)['sprite']
            x=(i%3)*c['cell_size']; y=(i//3)*(c['cell_size']+30)
            d.text((x+12,y+6),view,font=FONT,fill='#22313B'); sheet.alpha_composite(im,(x,y+30))
        sheet.save(folder/'sheet'/f"{c['asset_id']}_blender_views_r01.png")
    # Check Pygame's actual decoder and alpha composition without opening a window.
    os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
    import pygame as pg
    pg.init(); screen=pg.display.set_mode((1280,1000))
    surfaces=[pg.image.frombytes(maps['sprite'].tobytes(),maps['sprite'].size,'RGBA').convert_alpha() for _,maps,_,_ in preview]
    for c,_,cell,_ in preview:
        path=ROOT/c['folder']/'2D/environment-r01'/cell['file']
        decoded=pg.image.load(str(path)).convert_alpha()
        assert decoded.get_size()==(c['cell_size'],5*c['cell_size'])
    blit=[]
    for frame in range(121):
        start=time.perf_counter(); screen.fill((232,236,233))
        for i,surface in enumerate(surfaces): screen.blit(surface,((i%2)*610,(i//2)*220))
        pg.display.flip()
        if frame: blit.append((time.perf_counter()-start)*1000)
    pg.quit()
    # Benchmark one 320px stone's changing-light path with the unchanged game BRDF.
    entry=preview[4]; timings=[]
    for frame in range(121):
        start=time.perf_counter()
        lit=lighting.shade(entry[3],60+frame,240,None,None,.82,True,.34,1)
        if frame: timings.append((time.perf_counter()-start)*1000)
        if frame==60: lit.save(HERE/'stone_relight.png')
    perf={'frames':120,'backend':'Pygame SDL dummy; no GPU/window measurement',
          'seven_static_blit_p95_ms':sorted(blit)[113],'seven_static_blit_max_ms':max(blit),
          'single_stone_320px_relight_p95_ms':sorted(timings)[113],'single_stone_320px_relight_max_ms':max(timings),
          'relight_16_7ms_pass':sorted(timings)[113]<=16.7,'display_hardware_validation':'NOT_RUN'}
    report={'date':'2026-11-17','assets':results,'asset_count':7,'cell_count':49,'pass_count':5,
            'raw_rgba_bytes':raw_bytes,'performance':perf,'game_integration':'NOT_RUN; existing C011 Assets only accepts 128px',
            'DEC_06':'DEFERRED','physics_and_action_effects':'NOT_RUN; static export has no events'}
    (HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='assets'},indent=2))


if __name__=='__main__': verify()
