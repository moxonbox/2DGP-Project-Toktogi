"""Build nine-heading sprite sheets, turntables and verified five-pass atlases."""
from hashlib import sha256
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from verify_assets import load_cell, FONT, PASSES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
ORDER=['left','yaw_045','yaw_090','yaw_135','yaw_180','yaw_225','yaw_270','yaw_315','right']
reports=[]
for c in json.loads((HERE/'assets.json').read_text(encoding='utf-8')):
    folder=ROOT/c['folder']; out=folder/'2D/environment-r02'
    path=out/'manifest.json'; manifest=json.loads(path.read_text(encoding='utf-8'))
    by_view={v['view']:v for v in manifest['cells']}
    sprites={view:load_cell(folder,manifest,by_view[view])['sprite'] for view in ORDER}
    bounds={view:sprites[view].getbbox() for view in ORDER}
    pivot=manifest['game_pivot']
    max_width=max(b[2]-b[0] for b in bounds.values())
    above=max(88,max(pivot[1]-b[1] for b in bounds.values()))
    below=max(40,max(b[3]-pivot[1] for b in bounds.values()))
    tile_w=max(390,max_width+185);tile_h=math.ceil(above+below+65)
    sheet=Image.new('RGBA',(tile_w*3,tile_h*3),'#E8ECE9'); draw=ImageDraw.Draw(sheet)
    frames=[]
    for i,view in enumerate(ORDER):
        x=i%3*tile_w;y=i//3*tile_h
        b=bounds[view]; baseline=round(y+35+above)
        draw.text((x+14,y+9),f"{view} / {math.degrees(manifest['game_views'][view]):.1f}° / 1×",font=FONT,fill='#22313B')
        sheet.alpha_composite(sprites[view].crop(b),(x+12,round(baseline-(pivot[1]-b[1]))))
        actor=Image.open(HERE/'reference'/f'C011_{view}_sprite.png').convert('RGBA')
        sheet.alpha_composite(actor,(x+max_width+35,baseline-88))
        if view!='right':
            frame=Image.new('RGBA',(c['cell_size']+170,c['cell_size']+38),'#E8ECE9')
            frame.alpha_composite(sprites[view],(0,28))
            frame.alpha_composite(actor,(c['cell_size']+20,round(pivot[1]+28-88)))
            ImageDraw.Draw(frame).text((14,8),c['folder']+' / '+view+' / C011 yaw match',font=FONT,fill='#22313B')
            frames.append(frame)
    sheet.save(out/'game_views_C011.png')
    ImageOps.grayscale(sheet).save(out/'game_views_grayscale.png')
    frames[0].save(out/'turntable.png',save_all=True,append_images=frames[1:],duration=350,loop=0,disposal=1,blend=0)
    with Image.open(out/'turntable.png') as animation:
        assert animation.n_frames==8
        for i in range(8):
            animation.seek(i);assert animation.convert('RGBA').tobytes()==frames[i].tobytes()
    # Preserve native texels and a two-pixel gutter; atlas use is optional for consumers.
    size=c['cell_size']; step=size+4; atlas_size=step*3
    atlas={'padding':2,'grid':[3,3],'order':ORDER,'rects':{},'passes':{}}
    for i,view in enumerate(ORDER):atlas['rects'][view]=[i%3*step+2,i//3*step+2,size,size]
    for channel in PASSES:
        canvas=Image.new('RGBA',(atlas_size,atlas_size))
        for view in ORDER:
            rect=atlas['rects'][view]
            source=load_cell(folder,manifest,by_view[view])[channel]
            canvas.paste(source,(rect[0],rect[1]))
        target=out/('game_atlas_'+channel+'.png');canvas.save(target)
        with Image.open(target) as restored:
            for view in ORDER:
                x,y,w,h=atlas['rects'][view]
                assert restored.crop((x,y,x+w,y+h)).tobytes()==load_cell(folder,manifest,by_view[view])[channel].tobytes()
        atlas['passes'][channel]={'file':target.name,'size':[atlas_size,atlas_size],'sha256':sha256(target.read_bytes()).hexdigest()}
    manifest['game_atlas']=atlas
    manifest['preview_generator_sha256']=sha256(Path(__file__).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Equal scale and aligned world origin expose real model/detail changes.
    before=HERE/'before'/c['folder'];old=Image.open(before/'sprite.png').convert('RGBA')
    old_meta=json.loads((before/'manifest.json').read_text(encoding='utf-8'))
    old_cell=next(v for v in old_meta['cells'] if v['view']=='game_left')
    ob=old.getbbox();nb=bounds['left']
    aw=max(old_cell['pivot'][1]-ob[1],pivot[1]-nb[1],88)
    bh=max(ob[3]-old_cell['pivot'][1],nb[3]-pivot[1],40)
    col=max(ob[2]-ob[0],nb[2]-nb[0])+35
    comparison=Image.new('RGBA',(col*2+170,math.ceil(aw+bh+65)),'#E8ECE9')
    d=ImageDraw.Draw(comparison);baseline=round(aw+40)
    for i,(image,bb,pv,label) in enumerate(((old,ob,old_cell['pivot'],'r01'),(sprites['left'],nb,pivot,'r02'))):
        comparison.alpha_composite(image.crop(bb),(i*col+14,round(baseline-pv[1]+bb[1])))
        d.text((i*col+14,10),label+' / '+c['folder'],font=FONT,fill='#22313B')
    comparison.alpha_composite(Image.open(HERE/'reference/C011_left_sprite.png').convert('RGBA'),(col*2+20,baseline-88))
    comparison.save(out/'before_after.png')
    # UV diagnostic uses the final mesh and the exact sprite cameras.
    uv_panel=Image.new('RGBA',(size*2,size+32),'#E8ECE9')
    d=ImageDraw.Draw(uv_panel)
    for i,view in enumerate(('left','ortho_top')):
        uv=Image.open(out/c['clip']/view/'uv_checker.png').convert('RGBA')
        uv_panel.alpha_composite(uv,(i*size,32));d.text((i*size+12,8),view+' / UV checker',font=FONT,fill='#22313B')
    uv_panel.save(out/'uv_checker_compare.png')
    reports.append({'asset_id':c['asset_id'],'game_views':9,'atlas_rect_roundtrips':45,'turntable_frames_verified':8,
                    'game_pivot':pivot,'view_camera':'one fixed camera for all game headings'})
(HERE/'atlas_preview_validation.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('Built and checked 7 × (9-view sheet, 8-view turntable, 5 atlases).')
