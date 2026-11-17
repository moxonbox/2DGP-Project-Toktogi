"""Compare both assets at one density, root plane, clock and shared point light."""
import hashlib
import importlib.util
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
import shared_lighting

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path(sys.argv[1]).resolve()
REFERENCE=PROJECT/'asset/C/C011_toktogi'
OUT=ROOT/'comparison'
OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'2D/idle-r02/manifest.json').read_text(encoding='utf-8'))
toktogi=json.loads((REFERENCE/'2D/integrated-r5/playable_manifest.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
TABLE=[c/255/12.92 if c/255<=.04045 else ((c/255+.055)/1.055)**2.4 for c in range(256)]
names=('sprite','base','normal','ao','rm','emissive')


@lru_cache(maxsize=3)
def maps(asset,view,index):
    if asset=='spider':
        path=ROOT/f'2D/idle/idle_scan/{view}/{index}.png'
        size=640
        passes=names
    else:
        path=REFERENCE/f'2D/idle/idle/{view}/{index}.png'
        size=128
        passes=('sprite','base','normal','rm','emissive')
    with Image.open(path) as image:
        image.load()
        return {name:image.crop((0,i*size,size,(i+1)*size)) for i,name in enumerate(passes)}


def composite(view,time_s,mode='sprite',moving=False,flat=False):
    canvas=Image.new('RGBA',(960,640),'#727e87')
    draw=ImageDraw.Draw(canvas)
    draw.line((32,480,928,480),fill='#aeb9c2',width=1)
    draw.text((32,24),'C011 + C211  |  body length 1 : 5  |  71.91 px / BU',font=font,fill='white')
    draw.text((32,52),f'{view.upper()} / {mode.upper()} / {time_s:.2f}s',font=small,fill='white')
    light_x=480+220*math.sin(time_s*math.pi) if moving else 480
    light_y=230
    layout=(('toktogi',int((time_s%1.6)/.2)%8,(140,480),(64,88)),
            ('spider',int((time_s%2)*12+1e-9)%24,(580,480),manifest['views'][view]['pivot']))
    for asset,index,position,pivot in layout:
        images=maps(asset,view,index)
        origin=(round(position[0]-pivot[0]),round(position[1]-pivot[1]))
        if mode=='relit':
            if flat:
                images={**images,'normal':Image.new('RGBA',images['base'].size,(128,128,255,255))}
            fields=shared_lighting.fields(images,(),TABLE)
            image=shared_lighting.shade(fields,light_x-origin[0],origin[1]-light_y,None,None,.82,True,.34,1.)
        else:
            image=images['sprite']
        canvas.alpha_composite(image,origin)
        draw.text((position[0]-60,610),'C011  1.0mm' if asset=='toktogi' else 'C211  P. agrestis female ~5mm',font=small,fill='white')
        draw.ellipse((position[0]-2,478,position[0]+2,482),fill='#f4db9d')
    if mode=='relit':
        draw.ellipse((light_x-4,light_y-4,light_x+4,light_y+4),fill='#f4db9d')
    return canvas


results={}
for view in ('left','right'):
    board=composite(view,0)
    board.save(OUT/f'scale_color_{view}.png')
    gray=board.convert('L').convert('RGB')
    gray.save(OUT/f'scale_gray_{view}.png')
    frames=[composite(view,i/10) for i in range(80)]
    frames[0].save(OUT/f'idle_comparison_{view}.png',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=0,blend=0)
    frames=[composite(view,i/10,'relit',True) for i in range(80)]
    frames[0].save(OUT/f'shared_light_{view}.png',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=0,blend=0)
    normal=composite(view,0,'relit')
    flat=composite(view,0,'relit',flat=True)
    normal.save(OUT/f'relit_{view}.png')
    flat.save(OUT/f'flat_normal_{view}.png')
    results[view]={'flat_normal_mean_rgb_difference':ImageStat.Stat(ImageChops.difference(normal.convert('RGB'),flat.convert('RGB'))).mean}
    assert sum(results[view]['flat_normal_mean_rgb_difference'])>1

# The only renderer change is dynamic coordinate-array size. Check 128px parity.
module_spec=importlib.util.spec_from_file_location('original_lighting',PROJECT/'toktogi/prototype/lighting.py')
original=importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(original)
images=maps('toktogi','left',0)
args=(64,-32,None,None,.82,True,.34,1.)
a=original.shade(original.fields(images,(),TABLE),*args)
b=shared_lighting.shade(shared_lighting.fields(images,(),TABLE),*args)
assert a.tobytes()==b.tobytes()
first=maps('spider','left',0)
assert first['base'].size==(640,640)
assert all(image.size==(640,640) for image in first.values())
results.update({'renderer':'C011 lighting.py BRDF reused with dynamic size coordinate fields',
                'reference_renderer_sha256':hashlib.sha256((PROJECT/'toktogi/prototype/lighting.py').read_bytes()).hexdigest(),
                'C011_128px_parity':'byte-identical','C211_640px_load_and_shade':'PASS',
                'light':{'power':.82,'ambient':.34,'z_pixels':116},'clock':'common seconds, own clip durations',
                'collision':'visual comparison only, game collision profile unchanged',
                'game_loader':'existing materials.Assets has fixed SIZE=128 and revision integrated-r5; C211 uses this standalone manifest-driven comparison loader'})
(OUT/'comparison_validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('PASS shared renderer 128px parity / 640px maps / common-light comparisons')
