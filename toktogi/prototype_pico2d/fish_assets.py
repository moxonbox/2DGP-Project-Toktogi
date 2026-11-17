"""Predecoded authored C261 male/right sprites; no geometry or eight-pass BRDF."""
from bisect import bisect_right
from io import BytesIO
from math import isfinite
from pathlib import Path
import hashlib
import json

from PIL import Image
from environment import confined
from materials import _json

ACTIONS = ('surface_peek','surface_snap','breach_launch','airborne_arc','surface_fall','water_reentry')
PASSES = ('sprite','base','normal','ao','orm','emissive','depth','watermask')
SIZE = 384
MAX_MEMORY = 64 * 1024 * 1024


class FishAssets:
    def __init__(self, asset_root=None):
        self.asset_root = Path(asset_root) if asset_root is not None else Path(__file__).resolve().parents[2] / 'asset'
        self.root = confined(self.asset_root, 'C/C261_gambusia_holbrooki')
        self.frames = {}
        self.samples = {}
        self.memory_bytes = 0
        self.closed = False
        try:
            manifest_path = self.root / '2D/gambusia-r03/manifest.json'
            self.manifest = manifest = _json(manifest_path.read_bytes())
            signature = hashlib.sha256(json.dumps({k:v for k,v in manifest.items() if k != 'signature'},
                                                  sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if (manifest['schema'] != 1 or manifest['asset_id'] != 'C261_gambusia_holbrooki'
                    or manifest['revision'] != 'gambusia-r03' or manifest['signature'] != signature
                    or tuple(manifest['passes']) != PASSES or manifest['variants']['male']['cell'] != SIZE):
                raise ValueError('Unsupported fish manifest or signature mismatch.')
            base_path = confined(self.asset_root, 'C/C011_toktogi/2D/integrated-r5/playable_manifest.json')
            base = _json(base_path.read_bytes())
            self.base_signature = base['bundle_contract_signature']
            if (manifest['base_signature'] != self.base_signature
                    or manifest['contract']['reference']['base_signature'] != self.base_signature):
                raise ValueError('Fish was authored against a different C011 signature.')
            self.pivot = tuple(manifest['views']['male/right']['pivot'])
            if len(self.pivot) != 2 or not all(map(isfinite,self.pivot)):
                raise ValueError('Invalid fish pivot.')
            used = set()
            for action in ACTIONS:
                clip = manifest['clips'][f'male/{action}/mid']
                info = clip['views']['right']
                samples = info['samples']
                if (len(samples) != 12 or set(info['pass_files']) != set(PASSES)
                        or not isfinite(clip['duration']) or clip['duration'] <= 0):
                    raise ValueError(f'Invalid fish clip: {action}')
                self.samples[action] = tuple(sample['u'] for sample in samples)
                frames = self.frames[action] = []
                for index, sample in enumerate(samples):
                    if (sample['index'] != index or not all(isfinite(sample[k]) for k in ('u','time','duration'))
                            or sample['duration'] <= 0 or abs(sample['u']-index/12) > 1e-6
                            or abs(sample['time']-index*clip['duration']/12) > 1e-6
                            or sample['file'] in used):
                        raise ValueError(f'Invalid fish sample: {action}/{index}')
                    used.add(sample['file'])
                    for marker in sample['markers'].values():
                        if (len(marker['xy']) != 2 or len(marker['world']) != 3
                                or not all(map(isfinite,(*marker['xy'],*marker['world'])))):
                            raise ValueError('Nonfinite fish marker.')
                    mouth = tuple(sample['markers']['mouth_tip']['xy'])
                    path = confined(self.root, sample['file'])
                    if path.stat().st_size > SIZE*SIZE*8*4 + 65536:
                        raise ValueError('Fish PNG exceeds the cell byte budget.')
                    blob = path.read_bytes()
                    if hashlib.sha256(blob).hexdigest() != manifest['files'][sample['file']]:
                        raise ValueError(f'Fish PNG checksum mismatch: {sample["file"]}')
                    with Image.open(BytesIO(blob)) as image:
                        if image.format != 'PNG' or image.mode != 'RGBA' or image.size != (SIZE,SIZE*8):
                            raise ValueError('Fish PNG must be RGBA 384 x 3072.')
                        image.verify()
                    with Image.open(BytesIO(blob)) as image:
                        image.load()
                        sprite = image.crop((0,0,SIZE,SIZE))
                    frames.append((sprite,mouth))
                    self.memory_bytes += SIZE*SIZE*4
                    if self.memory_bytes + SIZE*SIZE*8*4*2 > MAX_MEMORY:
                        raise ValueError('Fish sprite preparation exceeds the 64 MiB image budget.')
            self.metadata = {'asset_id':manifest['asset_id'], 'revision':manifest['revision'],
                             'signature':signature, 'base_signature':self.base_signature,
                             'source_blend_sha256':manifest['source_blend_sha256'],
                             'variant':'male', 'view':'right', 'frames':sum(map(len,self.frames.values())),
                             'rendering':'authored Sprite pass; eight-pass BRDF conversion not implemented'}
        except Exception:
            self.close()
            raise

    def frame(self, action, u):
        """Return the authored sprite and local mouth marker without file I/O."""
        if self.closed:
            raise RuntimeError('Fish assets are closed.')
        if action not in self.frames or not isfinite(u):
            raise ValueError('Unknown fish action or nonfinite clip progress.')
        u = max(0.,min(1.,u))
        index = max(0,min(11,bisect_right(self.samples[action],u)-1))
        return self.frames[action][index]

    def close(self):
        if self.closed:
            return
        self.closed = True
        for frames in self.frames.values():
            for image, _ in frames:
                image.close()
        self.frames.clear()
        self.memory_bytes = 0
