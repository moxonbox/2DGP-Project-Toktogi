"""Validated C211 bundle reader for the standalone asset preview."""
import hashlib
import json
import math
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile,BadZipFile
from PIL import Image

PASSES=('sprite','base','normal','ao','rm','emissive')


def signature(manifest):
    unsigned={k:v for k,v in manifest.items() if k!='bundle_contract_signature'}
    return hashlib.sha256(json.dumps(unsigned,sort_keys=True).encode()).hexdigest()


def validate_manifest(manifest):
    if manifest.get('schema')!=1 or manifest.get('revision')!='idle-r02':
        raise ValueError('manifest.json: unsupported schema/revision')
    if manifest.get('asset_id')!='C211_spider_paradosa':
        raise ValueError('manifest.json: unexpected asset_id')
    if manifest.get('bundle_contract_signature')!=signature(manifest):
        raise ValueError('manifest.json: signature mismatch')
    if manifest['layout']['stacked_pass_order']!=list(PASSES):
        raise ValueError('manifest.json: missing or unsupported passes')
    width,height=manifest['layout']['cell_size']
    if (width,height)!=(640,640):
        raise ValueError('manifest.json: unsupported cell dimensions')
    if set(manifest['views'])!={'left','right'}:
        raise ValueError('manifest.json: missing or unsupported view')
    if set(manifest['clips'])!={'idle_scan'} or manifest.get('transitions')!={}:
        raise ValueError('manifest.json: unsupported clip or transition')
    samples=manifest['clips']['idle_scan']['samples']
    if len(samples)!=24:
        raise ValueError('idle_scan: missing sample')
    keys=set()
    elapsed=0.0
    for sample in samples:
        index=sample['index']
        key=f'idle_scan/{index}'
        if not isinstance(index,int) or index in keys or index!=len(keys):
            raise ValueError(f'{key}: duplicate or unordered sample key')
        keys.add(index)
        duration=sample['duration_s']
        if not math.isfinite(duration) or duration<=0 or not math.isfinite(sample['time_s']):
            raise ValueError(f'{key}: invalid sample time')
        if abs(sample['time_s']-elapsed)>1e-7:
            raise ValueError(f'{key}: discontinuous timeline')
        elapsed+=duration
        if set(sample['views'])!=set(manifest['views']):
            raise ValueError(f'{key}: missing view')
        for view,record in sample['views'].items():
            cell=f'idle_scan/{view}/{index}'
            if record['frame_file']!=f'{cell}.png':
                raise ValueError(f'{cell}: invalid frame path')
            x,y,w,h=record['rect']
            if any(not isinstance(v,int) for v in (x,y,w,h)) or (w,h)!=(width,height) or x<0 or y<0 or x+w>3864 or y+h>2576:
                raise ValueError(f'{cell}: atlas rect outside bounds')
            if set(manifest['views'][view]['pass_files'])!=set(PASSES):
                raise ValueError(f'{cell}: missing material pass')
            pivot=manifest['views'][view]['pivot']
            if len(pivot)!=2 or not all(math.isfinite(v) for v in pivot):
                raise ValueError(f'{cell}: invalid pivot')
            for marker in sample['marker_ids']:
                if marker not in record['markers']:
                    raise ValueError(f'{cell}: missing marker {marker}')
            for marker,data in record['markers'].items():
                if len(data['xy'])!=2 or len(data['world'])!=3 or not all(math.isfinite(v) for v in data['xy']+data['world']):
                    raise ValueError(f'{cell}: invalid marker {marker}')
    if abs(elapsed-2)>1e-7:
        raise ValueError('idle_scan: invalid loop duration')


class IdleBundle:
    def __init__(self,path):
        self.path=Path(path)
        self.archive=None
        try:
            lock=json.loads(self.path.with_suffix('.source.json').read_text(encoding='utf-8'))
            if hashlib.sha256(self.path.read_bytes()).hexdigest()!=lock['bundle_sha256']:
                raise ValueError('bundle checksum mismatch')
            self.archive=ZipFile(self.path)
            self.manifest=json.loads(self.archive.read('manifest.json'))
            validate_manifest(self.manifest)
            if self.manifest['bundle_contract_signature']!=lock['manifest_signature'] or self.manifest['base_signature']!=lock['base_signature']:
                raise ValueError('lock/manifest signature mismatch')
            if any(lock.get(key)!=self.manifest[key] for key in ('schema','asset_id','revision','source_blend_sha256')):
                raise ValueError('lock/manifest identity mismatch')
            entries=self.archive.namelist()
            if len(entries)!=len(set(entries)):
                raise ValueError('duplicate archive entry')
            for name,digest in self.manifest['file_hashes'].items():
                if hashlib.sha256(self.archive.read(name)).hexdigest()!=digest:
                    raise ValueError(f'{name}: payload checksum mismatch')
            for sample in self.manifest['clips']['idle_scan']['samples']:
                for view,record in sample['views'].items():
                    if record['frame_file'] not in self.manifest['file_hashes']:
                        raise ValueError(f'idle_scan/{view}/{sample["index"]}: missing frame hash')
                    for filename in self.manifest['views'][view]['pass_files'].values():
                        if filename not in self.manifest['file_hashes']:
                            raise ValueError(f'{filename}: missing pass hash')
        except (OSError,ValueError,KeyError,TypeError,BadZipFile) as error:
            self.close()
            raise ValueError(f'{self.path.name}: {error}') from error

    def close(self):
        if self.archive is not None:
            self.archive.close()

    def maps(self,view,index):
        key=f'idle_scan/{view}/{index}'
        if view not in self.manifest['views'] or not isinstance(index,int) or not 0<=index<24:
            raise ValueError(f'{self.path.name}: unsupported cell {key}')
        try:
            blob=self.archive.read(key+'.png')
            with Image.open(BytesIO(blob)) as image:
                if image.mode!='RGBA' or image.size!=(640,3840):
                    raise ValueError('invalid stacked PNG dimensions/format')
                image.load()
                return {name:image.crop((0,i*640,640,(i+1)*640)) for i,name in enumerate(PASSES)}
        except (OSError,ValueError,KeyError,BadZipFile) as error:
            raise ValueError(f'{self.path.name}: {key}: {error}') from error

    def sample_at(self,time_s):
        if not math.isfinite(time_s):
            raise ValueError('idle_scan: nonfinite playback time')
        return self.manifest['clips']['idle_scan']['samples'][int((time_s%2)*12+1e-9)%24]
