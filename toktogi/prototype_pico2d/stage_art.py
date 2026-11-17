"""Prepare the habitat from authored A/B resources and the shared five-pass BRDF."""
import importlib.util
from pathlib import Path
from math import isfinite
from PIL import Image, ImageDraw, ImageFilter
from environment import confined, read_png
from materials import _json, PASSES
from lighting import fields, shade
from sprite_renderer import SRGB
from stage_world import SURFACES, LIGHTS

ANCHORS = {'A01':'frond_top','A02':'waterline','A03':'slope_path',
           'A04':'walk_top','A05':'top_surface','A06':'leaf_center','A07':'food_point'}


class StageArt:
    def __init__(self, world, asset_root=None):
        self.root = Path(asset_root) if asset_root else Path(__file__).resolve().parents[2]/'asset'
        self.maps, self.anchors, self.records = {}, {}, []
        self.image = None
        self.platform_frames=[]
        self.food_tiles=[]
        self.closed = False
        try:
            for code in ANCHORS:
                folders = sorted((self.root/'A').glob(code+'_*'))
                if len(folders)!=1: raise ValueError('Missing or ambiguous stage asset '+code)
                folder = confined(self.root,folders[0].relative_to(self.root))
                m = _json((folder/'2D/environment-r02/manifest.json').read_bytes())
                w,h = m['cell_size']
                if (m['schema']!='toktogi_environment/1' or m['revision']!='environment-r02'
                        or tuple(m['pass_order'])!=PASSES or not (0<w<=1024 and 0<h<=1024)
                        or m['normal_space']!='camera_R_right_G_up_B_toward_camera'
                        or m['filter']!='nearest' or m['coverage_channel']!='base.alpha'):
                    raise ValueError('Unsupported stage material '+code)
                cell = next(c for c in m['cells'] if c['view']=='left' and c['sample']==0)
                anchor = cell['anchors'][ANCHORS[code]]['xy']
                if len(anchor)!=2 or not all(map(isfinite,anchor)): raise ValueError('Invalid stage anchor')
                packed = read_png(folder/'2D/environment-r02',cell,(w,h*5))
                try:
                    sprite = packed.crop((0,0,w,h)); box = sprite.getbbox(); sprite.close()
                    if box!=tuple(cell['bbox']['sprite']): raise ValueError('Stage coverage mismatch')
                    self.maps[code] = {name:packed.crop((box[0],i*h+box[1],box[2],i*h+box[3]))
                                       for i,name in enumerate(PASSES)}
                finally: packed.close()
                self.anchors[code] = anchor[0]-box[0], anchor[1]-box[1]
                self.records.append({'asset':code,'revision':m['revision'],'view':'left','sha256':cell['sha256']})
            self.image = Image.new('RGBA',(3120,560))
            draw = ImageDraw.Draw(self.image)
            for y in range(560):
                t=y/560
                draw.line((0,y,3120,y),fill=(round(15+13*t),round(30+22*t),round(37+17*t),255))
            shafts=Image.new('RGBA',self.image.size)
            ink=ImageDraw.Draw(shafts)
            for lx,ly in LIGHTS:
                ink.polygon(((lx-170,0),(lx-100,0),(lx+200,470),(lx-80,470)),fill=(178,209,132,18))
                ink.ellipse((lx-170,ly-120,lx+170,ly+160),fill=(113,175,149,15))
            glow=shafts.filter(ImageFilter.GaussianBlur(24));shafts.close()
            self.image.alpha_composite(glow);glow.close()
            self.background_plants()
            # The authored water tile is repeated below one shared gameplay waterline.
            draw = ImageDraw.Draw(self.image)
            draw.rectangle((0,400,3120,560),fill=(25,62,70,255))
            for x in range(-120,3300,440): self.place('A02',(x,475),600,relight=True)
            for x in (160,780,2240,2890): self.place('A03',(x,470),550)
            for x in range(140,3100,370): self.place('A06',(x,492),205)
            self.bindings=[]
            for p,code in zip(world.course.platforms,SURFACES):
                frames=tuple(self.place(code,((p.x0+p.x1)/2,p.y),p.x1-p.x0,
                                        capture=True,light_offset=dx) for dx in (-40,-20,0,20,40))
                self.platform_frames.append(frames)
                self.bindings.append({'asset':code,'anchor':ANCHORS[code],'support':[p.x0,p.x1,p.y],
                                      'scale':(p.x1-p.x0)/self.maps[code]['sprite'].width})
            for e in world.targets('food'):
                self.food_tiles.append((e.key,self.place('A07',(e.point[0],e.point[1]+4),65,capture=True)))
            for maps in self.maps.values():
                for image in maps.values(): image.close()
            self.maps.clear()
        except BaseException:
            self.close(); raise

    def place(self, code, point, width, *, relight=True, capture=False, light_offset=0):
        maps = self.maps[code]
        scale = width/maps['sprite'].width
        size = (round(width),max(1,round(maps['sprite'].height*scale)))
        images = {name:im.resize(size,Image.Resampling.NEAREST) for name,im in maps.items()}
        origin = tuple(round(point[i]-self.anchors[code][i]*scale) for i in (0,1))
        try:
            if relight:
                light = min(LIGHTS,key=lambda p:abs(p[0]-point[0]))
                surface = fields(images,(),SRGB)
                tile = shade(surface,light[0]+light_offset-origin[0],origin[1]-light[1],None,None,1.12,True,.24,1.)
                if capture:return tile,origin
                try: self.image.alpha_composite(tile,origin)
                finally: tile.close()
            else: self.image.alpha_composite(images['sprite'],origin)
        finally:
            for im in images.values(): im.close()

    def background_plants(self):
        tools = confined(self.root,'B/_production/r02/tools/background_bundle.py')
        spec = importlib.util.spec_from_file_location('habitat_background_bundle',tools)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        bundle = module.BackgroundBundle(tools.parent.parent/'backgrounds_r02.zip')
        try:
            placements=(('B06',180,385,250),('B07',720,410,270),('B05',1160,500,230),
                        ('B04',1510,455,210),('B05',1870,505,190),('B06',2220,355,300),
                        ('B07',2600,350,320),('B06',3000,380,270))
            for code,x,y,height in placements:
                name=next(k for k,v in bundle.manifest['assets'].items() if v['folder'].startswith(code+'_'))
                source=bundle.maps(name)['sprite']; tile=source.crop(source.getbbox())
                scaled=tile.resize((max(1,round(tile.width*height/tile.height)),height),Image.Resampling.NEAREST)
                tile.close()
                alpha=scaled.getchannel('A').point(lambda a:round(a*.45));scaled.putalpha(alpha);alpha.close()
                self.image.alpha_composite(scaled,(round(x-scaled.width/2),y-height));scaled.close()
            self.records.append({'asset':'B04/B05/B06/B07','revision':'background-r02','role':'background silhouettes'})
        finally: bundle.close()

    def close(self):
        if self.closed:return
        self.closed=True
        for maps in self.maps.values():
            for image in maps.values():image.close()
        self.maps.clear()
        for frames in self.platform_frames:
            for image,_ in frames:image.close()
        self.platform_frames.clear()
        for _,(image,_) in self.food_tiles:image.close()
        self.food_tiles.clear()
        if self.image:self.image.close();self.image=None
