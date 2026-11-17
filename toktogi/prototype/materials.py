"""Checked sprite bundles, motion metadata and the five material maps."""
from functools import lru_cache
from contextlib import ExitStack
from math import isfinite
from io import BytesIO
import hashlib
import json
from pathlib import Path
from struct import unpack
from zipfile import ZipFile

import pygame as pg
from motion import Track
from sprite_renderer import SpriteRenderer

PASSES = ('sprite', 'base', 'normal', 'rm', 'emissive')
SIZE = 128
PRESS_INK=frozenset(((70,75),(69,76),(70,76),(70,77),(71,77),(70,78)))


def contact_ink(key):
    return PRESS_INK if key[0]=='obs_antenna_clean' and key[2] in (11,17) else ()


class Assets:
    def __init__(self, path, pose_path=None):
        with ExitStack() as handles:
            self.load(Path(path),Path(pose_path) if pose_path is not None else None,handles)
            handles.pop_all()

    def load(self,path,pose_path,handles):
        lock=json.loads(path.with_suffix('.source.json').read_text(encoding='utf-8'))
        with path.open('rb') as stream:
            actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if lock['bundle_sha256']!=actual:
            raise ValueError('Sprite bundle checksum does not match its source lock.')
        self.bundle = handles.enter_context(ZipFile(path))
        self.manifest = json.loads(self.bundle.read('playable_manifest.json'))
        signature = self.manifest.pop('bundle_contract_signature')
        if signature!=hashlib.sha256(json.dumps(self.manifest,sort_keys=True).encode()).hexdigest() or signature!=lock['manifest_signature']:
            raise ValueError('Sprite manifest signature does not match its source lock.')
        self.manifest['bundle_contract_signature'] = signature
        if self.manifest['asset_revision']!='integrated-r5':
            raise ValueError('Unsupported sprite asset revision.')
        self.pivot = self.manifest['coordinate_contract']['pivot_pixels_top_left']
        self.clips = self.manifest['clips']
        self.tracks = {}
        for name, clip in self.clips.items():
            for view in clip['supported_views']:
                self.tracks[name,view] = Track.from_clip(name,view,clip)
        self.sequences = {}
        for name, segments in self.manifest['sequence_previews'].items():
            cells, durations = [], []
            for s in segments:
                start = s.get('start_sample',0)
                stop = start+s['sample_count']
                track=self.tracks.get((s['clip'],s['view']))
                if not track or not 0<=start<stop<=len(track.cells):
                    raise ValueError(f'Invalid sequence segment {name}: {s}')
                cells.extend(track.cells[start:stop])
                durations.extend(track.durations[start:stop])
            self.sequences[name] = Track(cells,durations,name!='transition_antenna_furca.png')
        self.groom = self.sequences.get('transition_antenna_furca.png')
        runtime=pose_path or path.with_name('toktogi_runtime_poses.zip')
        runtime_lock=json.loads(runtime.with_suffix('.source.json').read_text(encoding='utf-8'))
        with runtime.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=runtime_lock['bundle_sha256']:
                raise ValueError('Runtime pose bundle checksum does not match its source lock.')
        self.pose_bundle=handles.enter_context(ZipFile(runtime))
        self.poses=json.loads(self.pose_bundle.read('runtime_poses.json'))
        if self.poses['schema']!=1 or self.poses['base_signature']!=signature or runtime_lock['base_signature']!=signature or self.poses['source_blend_sha256']!=lock['source_blend_sha256']:
            raise ValueError('Runtime poses were built for a different sprite revision.')
        self.pose_clips=self.poses['clips']
        self.pose_tracks={n:Track(map(tuple,p['cells']),p['durations'],False) for n,p in self.poses['profiles'].items()}
        self.validate_tracks()
        self.sequences.update(('runtime_'+name,track) for name,track in self.pose_tracks.items())
        self.maps=lru_cache(maxsize=36)(self.maps)
        self.renderer=SpriteRenderer(self.maps,self.manifest['channels']['emissive']['scale'],contact_ink)
        self.render=self.renderer.render
        self.surface_fields=self.renderer.surface_fields

    def validate_tracks(self):
        base_files=set(self.bundle.namelist())
        pose_files=set(self.pose_bundle.namelist())
        cells={cell for track in self.tracks.values() for cell in track.cells}
        cells.update((name,view,i) for name,clip in self.pose_clips.items()
                     for i,sample in enumerate(clip['samples']) for view in sample['views'])
        if self.clips.keys()&self.pose_clips.keys():
            raise ValueError('Base and supplemental clip names overlap.')
        for track in (*self.sequences.values(),*self.pose_tracks.values()):
            for cell in track.cells:
                if cell not in cells:
                    raise ValueError(f'Unknown cell in motion profile: {cell}')
        for cell in sorted(cells):
            name,view,index=cell
            files=base_files if name in self.clips else pose_files
            path=f'{name}/{view}/{index}.png'
            if path not in files:
                raise ValueError(f'Missing material PNG: {cell}')
            archive=self.bundle if name in self.clips else self.pose_bundle
            with archive.open(path) as image:
                header=image.read(24)
            if (len(header)!=24 or header[:16]!=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' or
                    unpack('>II',header[16:])!=(SIZE,SIZE*len(PASSES))):
                raise ValueError(f'Invalid material PNG header or size: {cell}')
            try:
                markers,support=self.sample(cell)
                names=['foot_contact_'+leg for leg in support]
                if name=='feed_cycle':names.append('mouth_marker')
                if name.startswith(('interact_activate','interact_collect')):
                    names.append('interaction_work_socket_RF' if view=='right' else 'interaction_work_socket')
                for marker in names:
                    x,y=markers[marker]['xy']
                    if not all(map(isfinite,(x,y))):
                        raise ValueError('Nonfinite marker position.')
            except (KeyError,TypeError,ValueError) as error:
                raise ValueError(f'Invalid support/marker data: {cell}') from error

    def close(self):
        self.renderer.close()
        self.maps.cache_clear()
        self.bundle.close()
        self.pose_bundle.close()

    def maps(self, key):
        name, view, index = key
        bundle=self.bundle if name in self.clips else self.pose_bundle
        blob = bundle.read(f'{name}/{view}/{index}.png')
        try:
            image = pg.image.load(BytesIO(blob), 'cell.png').convert_alpha()
        except pg.error as error:
            raise ValueError(f'Invalid material PNG: {key}') from error
        if image.get_size()!=(SIZE,SIZE*len(PASSES)):
            raise ValueError(f'Invalid cell size {key}')
        return {name:image.subsurface((0,i*SIZE,SIZE,SIZE)) for i,name in enumerate(PASSES)}

    def sample(self,key):
        name,view,i = key
        sample = (self.clips if name in self.clips else self.pose_clips)[name]['samples'][i]
        return sample['views'][view]['markers'],sample['support']

