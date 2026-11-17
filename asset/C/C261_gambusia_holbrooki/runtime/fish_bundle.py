"""Validated C261 data, bounded cell cache and pose geometry access."""
import hashlib
import json
import math
from collections import OrderedDict
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from PIL import Image
from motion_spec import ASSET_ID,REVISION,VARIANTS,DESIGNS,PHASES,VIEWS

PASSES=('sprite','base','normal','ao','orm','emissive','depth','watermask')

def strict_json(data):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate JSON key: '+key)
            result[key]=value
        return result
    return json.loads(data,object_pairs_hook=unique)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1048576),b''):digest.update(data)
    return digest.hexdigest()


def signature(data):
    return hashlib.sha256(json.dumps({k:v for k,v in data.items() if k!='signature'},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(manifest):
    if manifest.get('schema')!=1 or manifest.get('asset_id')!=ASSET_ID or manifest.get('revision')!=REVISION:
        raise ValueError('manifest.json: unsupported schema/asset/revision')
    if manifest.get('signature')!=signature(manifest):raise ValueError('manifest.json: signature mismatch')
    if manifest.get('passes')!=list(PASSES):raise ValueError('manifest.json: missing/unsupported pass')
    expected={f'{sex}/{action}/{phase}' for sex in VARIANTS for action in DESIGNS for phase in PHASES}
    if set(manifest['clips'])!=expected:raise ValueError('manifest.json: missing/unsupported clip')
    used=set()
    for view,info in manifest['views'].items():
        if len(info['pivot'])!=2 or not all(math.isfinite(v) for v in info['pivot']):raise ValueError(view+': invalid pivot')
    for key,clip in manifest['clips'].items():
        if set(clip['views'])!=set(VIEWS):raise ValueError(key+': missing view')
        if not math.isfinite(clip['duration']) or clip['duration']<=0:raise ValueError(key+': invalid duration')
        count=12 if key.endswith('/mid') else 3
        for view,info in clip['views'].items():
            cell=VARIANTS[key.split('/')[0]]['cell'];stride=cell+4
            if set(info['pass_files'])!=set(PASSES):raise ValueError(key+'/'+view+': missing pass')
            samples=info['samples']
            if len(samples)!=count:raise ValueError(key+'/'+view+': missing sample')
            for i,sample in enumerate(samples):
                context=f'{key}/{view}/{i}'
                if sample['index']!=i:raise ValueError(context+': duplicate/unordered sample')
                if sample['duration']<=0 or not all(math.isfinite(sample[k]) for k in ('u','time','duration')):raise ValueError(context+': invalid sample time')
                if abs(sample['time']-i*clip['duration']/count)>1e-6:raise ValueError(context+': invalid timeline')
                if abs(sample['u']-i/count)>1e-6 or abs(sample['duration']-clip['duration']/count)>1e-6:raise ValueError(context+': invalid sampling')
                if sample['file'] in used:raise ValueError(context+': duplicate cell file')
                used.add(sample['file'])
                x,y,w,h=sample['rect']
                if any(type(v)!=int for v in (x,y,w,h)) or (w,h)!=(cell,cell) or x<0 or y<0 or x+w>stride*6 or y+h>stride*3:raise ValueError(context+': invalid atlas rect')
                for name in ('mouth_tip','body_ref','attack_socket','SL_snout','SL_tail'):
                    if name not in sample['markers']:raise ValueError(context+': missing marker '+name)
                    marker=sample['markers'][name]
                    if len(marker['xy'])!=2 or len(marker['world'])!=3 or not all(math.isfinite(v) for v in marker['xy']+marker['world']):raise ValueError(context+': nonfinite marker '+name)
                required=[sample['file'],*info['pass_files'].values()]
                if any(path not in manifest['files'] for path in required):raise ValueError(context+': missing file hash')
    for path,digest in manifest['files'].items():
        if path.startswith(('/', '\\')) or '..' in path.split('/') or ':' in path or len(digest)!=64:
            raise ValueError('manifest.json: invalid payload path/hash '+path)
    for sequence in manifest['sequences'].values():
        if any(action not in DESIGNS for action in sequence):raise ValueError('manifest.json: invalid transition')


class FishBundle:
    def __init__(self,path):
        self.path=Path(path);self.archive=None;self.cache=OrderedDict();self.geometry={}
        try:
            lock=strict_json(self.path.with_suffix('.source.json').read_text(encoding='utf-8'))
            if sha(self.path)!=lock['bundle_sha256']:raise ValueError('bundle checksum mismatch')
            self.archive=ZipFile(self.path)
            entries=self.archive.namelist()
            if len(entries)!=len(set(entries)):raise ValueError('duplicate archive entry')
            self.manifest=strict_json(self.archive.read('manifest.json'));validate(self.manifest)
            for key in ('schema','asset_id','revision','base_signature','source_blend_sha256','signature'):
                if lock.get(key)!=self.manifest.get(key):raise ValueError('lock/manifest mismatch: '+key)
        except Exception as error:
            self.close();raise ValueError(f'{self.path.name}: {error}') from error

    def close(self):
        if self.archive:self.archive.close()
        self.cache.clear();self.geometry.clear()

    def read(self,path):
        try:
            data=self.archive.read(path)
            if hashlib.sha256(data).hexdigest()!=self.manifest['files'][path]:raise ValueError('payload checksum mismatch')
            return data
        except (KeyError,ValueError) as error:raise ValueError(f'{self.path.name}: {path}: {error}') from error

    def cell(self,variant,action,phase,u,view='left'):
        key=f'{variant}/{action}/{phase}'
        if key not in self.manifest['clips'] or view not in VIEWS or not math.isfinite(u):raise ValueError(f'{self.path.name}: unsupported cell {key}/{view}/{u}')
        info=self.manifest['clips'][key]['views'][view];samples=info['samples']
        return samples[min(len(samples)-1,max(0,int(u*len(samples))))]

    def maps(self,cell):
        path=cell['file']
        if path in self.cache:
            self.cache.move_to_end(path);return self.cache[path]
        with Image.open(BytesIO(self.read(path))) as image:
            size=image.width
            if image.mode!='RGBA' or image.height!=size*len(PASSES):raise ValueError(path+': invalid stacked PNG')
            image.load();maps={p:image.crop((0,i*size,size,(i+1)*size)) for i,p in enumerate(PASSES)}
        self.cache[path]=maps
        while len(self.cache)>4:self.cache.popitem(last=False)
        return maps

    def pose(self,variant,action,phase,u):
        if variant not in self.geometry:
            name=self.manifest['geometry'][variant]['file']
            with np.load(BytesIO(self.read(name)),allow_pickle=False) as archive:
                values={key:archive[key] for key in archive.files}
            values['lookup']={value:i for i,value in enumerate(values['pose_ids'].tolist())};self.geometry[variant]=values
        geometry=self.geometry[variant];cell=self.cell(variant,action,phase,u)
        index=geometry['lookup'][cell['pose_id']]
        return {'vertices':geometry['positions'][index],'triangles':geometry['triangles'],
                'body_count':int(geometry['body_count']),'mouth_tip':np.array(cell['markers']['mouth_tip']['world']),
                'body_ref':np.array(cell['markers']['body_ref']['world']),'bounds':geometry['bounds'][index]}
