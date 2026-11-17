"""Static background bundle: rectangular five-pass cells and an eight-cell LRU."""
import hashlib
import json
import math
from collections import OrderedDict
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

PASSES=['sprite','base','normal','rm','emissive']
YAW={'left':0.,'right':2.00151174696589,**{f'yaw_{i:03}':math.radians(i) for i in range(45,360,45)}}
VIEWS=set(YAW)|{'ortho_'+v for v in ('front','back','left','right','top','underside')}


def signature(data):
    return hashlib.sha256(json.dumps({k:v for k,v in data.items() if k!='signature'},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(data):
    if data.get('schema')!='toktogi.background-bundle/1' or data.get('revision')!='background-r02':
        raise ValueError('manifest.json: unsupported schema/revision')
    if data.get('signature')!=signature(data):raise ValueError('manifest.json: signature mismatch')
    if data.get('passes')!=PASSES:raise ValueError('manifest.json: unsupported passes')
    used=set()
    for name,asset in data['assets'].items():
        if asset.get('asset_id')!=name or asset.get('revision')!=data['revision'] or not asset.get('static') or asset.get('events'):
            raise ValueError(name+': invalid static asset identity')
        if set(asset['views'])!=VIEWS:raise ValueError(name+': missing/unsupported view')
        if asset.get('passes')!=PASSES:raise ValueError(name+': missing pass')
        for view,cell in asset['views'].items():
            context=name+'/'+view
            w,h=cell['cell'];x0,y0,x1,y1=cell['bbox']
            if any(type(n)!=int for n in (w,h)) or not 0<w<=4096 or not 0<h<=4096:
                raise ValueError(context+': invalid dimensions')
            if not (0<=x0<x1<=w and 0<=y0<y1<=h) or cell['rect']!=[0,0,w,h]:
                raise ValueError(context+': invalid rect/bbox')
            if len(cell['pivot'])!=2 or not all(math.isfinite(n) for n in cell['pivot']):
                raise ValueError(context+': nonfinite pivot')
            if cell['anchors'].get('origin')!=cell['pivot'] or cell.get('sample')!=0 or not cell.get('static_hold'):
                raise ValueError(context+': invalid static sample/anchor')
            if any(len(p)!=2 or not all(math.isfinite(n) for n in p) for p in cell['anchors'].values()):
                raise ValueError(context+': nonfinite anchor')
            if view in YAW and (not math.isfinite(cell['yaw_rad']) or abs(cell['yaw_rad']-YAW[view])>1e-9):
                raise ValueError(context+': incompatible C011 yaw')
            path=asset['folder']+'/'+cell['file']
            if path in used or path not in data['files']:raise ValueError(context+': duplicate/missing cell')
            used.add(path)
    if used!=set(data['files']):raise ValueError('manifest.json: unexpected/missing payload')
    for path,digest in data['files'].items():
        if path.startswith('/') or '..' in path.split('/') or '\\' in path or ':' in path or len(digest)!=64:
            raise ValueError('manifest.json: unsafe path/hash '+path)


class BackgroundBundle:
    def __init__(self,path):
        self.path=Path(path);self.archive=None;self.cache=OrderedDict()
        try:
            lock=json.loads(self.path.with_suffix('.source.json').read_text(encoding='utf-8'))
            if hashlib.sha256(self.path.read_bytes()).hexdigest()!=lock['bundle_sha256']:
                raise ValueError('bundle checksum mismatch')
            self.archive=ZipFile(self.path)
            entries=self.archive.namelist()
            if len(entries)!=len(set(entries)):raise ValueError('duplicate ZIP entry')
            self.manifest=json.loads(self.archive.read('manifest.json'));validate(self.manifest)
            if lock['signature']!=self.manifest['signature']:raise ValueError('lock signature mismatch')
            if set(entries)!=set(self.manifest['files'])|{'manifest.json'}:raise ValueError('unexpected/missing ZIP entries')
        except Exception as error:
            self.close();raise ValueError(f'{self.path.name}: {error}') from error

    def maps(self,asset_id,view='left'):
        context=asset_id+'/'+view
        try:
            asset=self.manifest['assets'][asset_id];cell=asset['views'][view]
            path=asset['folder']+'/'+cell['file']
            if path in self.cache:
                self.cache.move_to_end(path);return self.cache[path]
            payload=self.archive.read(path)
            if hashlib.sha256(payload).hexdigest()!=self.manifest['files'][path]:raise ValueError('cell checksum mismatch')
            w,h=cell['cell']
            with Image.open(BytesIO(payload)) as image:
                if image.mode!='RGBA' or image.size!=(w,h*5):raise ValueError('invalid five-pass PNG')
                image.load();maps={p:image.crop((0,i*h,w,(i+1)*h)) for i,p in enumerate(PASSES)}
            self.cache[path]=maps
            while len(self.cache)>8:self.cache.popitem(last=False)
            return maps
        except (KeyError,ValueError) as error:
            raise ValueError(f'{self.path.name}: {context}: {error}') from error

    def draw(self,canvas,asset_id,world_position,camera=(0,0),view='left'):
        asset=self.manifest['assets'][asset_id]
        if asset['scale']['scale_policy']=='microscopy_only':
            raise ValueError(asset_id+': microscopy-only; use maps() in a separate microscopy viewer')
        cell=asset['views'][view];pivot=cell['pivot']
        at=tuple(round(world_position[i]-camera[i]-pivot[i]) for i in (0,1))
        canvas.alpha_composite(self.maps(asset_id,view)['sprite'],at)

    def close(self):
        if self.archive:self.archive.close()
        self.cache.clear()
