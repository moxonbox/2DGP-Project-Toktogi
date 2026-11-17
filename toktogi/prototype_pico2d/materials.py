"""Source-locked sprite bundles, checked metadata and Pillow material maps."""
from contextlib import ExitStack
from functools import lru_cache
from io import BytesIO
from math import isfinite
from pathlib import Path
from struct import unpack
from zipfile import BadZipFile, ZipFile
import hashlib
import json

from PIL import Image
from motion import Track
from sprite_renderer import SpriteRenderer

PASSES = ('sprite', 'base', 'normal', 'rm', 'emissive')
SIZE = 128
PRESS_INK = frozenset(((70,75),(69,76),(70,76),(70,77),(71,77),(70,78)))


def contact_ink(key):
    return PRESS_INK if key[0] == 'obs_antenna_clean' and key[2] in (11,17) else ()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate metadata key: {key}')
        result[key] = value
    return result


def _json(blob):
    def invalid_constant(value):
        raise ValueError(f'Nonfinite metadata constant: {value}')
    return json.loads(blob, object_pairs_hook=_unique_object, parse_constant=invalid_constant)


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


class Assets:
    def __init__(self, path, pose_path=None):
        self.closed = False
        with ExitStack() as handles:
            try:
                self.load(Path(path), Path(pose_path) if pose_path is not None else None, handles)
            except (KeyError, TypeError, IndexError, OverflowError, BadZipFile) as error:
                raise ValueError(f'Invalid sprite bundle metadata: {error}') from error
            handles.pop_all()

    @staticmethod
    def validate_archive(archive, metadata):
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP member name.')
        if metadata not in names or len(entries) > 65536:
            raise ValueError('Missing metadata or excessive ZIP member count.')
        for entry in entries:
            limit = 64 * 1024 * 1024 if entry.filename == metadata else SIZE * SIZE * 5 * 4 + 65536
            if entry.is_dir() or entry.file_size > limit or entry.flag_bits & 1:
                raise ValueError(f'Unsupported ZIP member: {entry.filename}')
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f'Invalid ZIP CRC: {bad}')

    def load(self, path, pose_path, handles):
        lock = _json(path.with_suffix('.source.json').read_text(encoding='utf-8'))
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if lock['bundle_sha256'] != actual:
            raise ValueError('Sprite bundle checksum does not match its source lock.')
        self.bundle = handles.enter_context(ZipFile(path))
        self.validate_archive(self.bundle, 'playable_manifest.json')
        self.manifest = _json(self.bundle.read('playable_manifest.json'))
        signature = self.manifest.pop('bundle_contract_signature')
        if (signature != hashlib.sha256(json.dumps(self.manifest, sort_keys=True).encode()).hexdigest()
                or signature != lock['manifest_signature']):
            raise ValueError('Sprite manifest signature does not match its source lock.')
        self.manifest['bundle_contract_signature'] = signature
        if (lock['schema'] != 1 or lock['asset_revision'] != 'integrated-r5'
                or self.manifest['asset_revision'] != lock['asset_revision']
                or self.manifest['source_blend_sha256'] != lock['source_blend_sha256']):
            raise ValueError('Unsupported sprite revision or mismatched source provenance.')
        self.pivot = self.manifest['coordinate_contract']['pivot_pixels_top_left']
        if len(self.pivot) != 2 or not all(map(_finite, self.pivot)):
            raise ValueError('Invalid sprite pivot.')
        if set(self.manifest['channels']) != set(PASSES):
            raise ValueError('Material contract must define exactly five passes.')
        if not self.manifest['views'] or not all(map(_finite, self.manifest['views'].values())):
            raise ValueError('Invalid view headings.')
        self.clips = self.manifest['clips']
        self.tracks = {}
        for name, clip in self.clips.items():
            for view in clip['supported_views']:
                if (name, view) in self.tracks:
                    raise ValueError(f'Duplicate clip/view key: {(name, view)}')
                self.tracks[name, view] = Track.from_clip(name, view, clip)
        self.sequences = {}
        for name, segments in self.manifest['sequence_previews'].items():
            cells, durations = [], []
            for segment in segments:
                start = segment.get('start_sample', 0)
                count = segment['sample_count']
                if type(start) is not int or type(count) is not int:
                    raise ValueError(f'Invalid sequence indices: {name}')
                stop = start + count
                track = self.tracks.get((segment['clip'], segment['view']))
                if not track or not 0 <= start < stop <= len(track.cells):
                    raise ValueError(f'Invalid sequence segment {name}: {segment}')
                cells.extend(track.cells[start:stop])
                durations.extend(track.durations[start:stop])
            self.sequences[name] = Track(cells, durations, name != 'transition_antenna_furca.png')
        self.groom = self.sequences.get('transition_antenna_furca.png')
        runtime = pose_path or path.with_name('toktogi_runtime_poses.zip')
        runtime_lock = _json(runtime.with_suffix('.source.json').read_text(encoding='utf-8'))
        with runtime.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != runtime_lock['bundle_sha256']:
                raise ValueError('Runtime pose bundle checksum does not match its source lock.')
        self.pose_bundle = handles.enter_context(ZipFile(runtime))
        self.validate_archive(self.pose_bundle, 'runtime_poses.json')
        self.poses = _json(self.pose_bundle.read('runtime_poses.json'))
        if (self.poses['schema'] != 1 or self.poses['base_signature'] != signature
                or runtime_lock['base_signature'] != signature
                or self.poses['source_blend_sha256'] != lock['source_blend_sha256']
                or runtime_lock['source_blend_sha256'] != lock['source_blend_sha256']
                or self.poses['revision'] != runtime_lock['revision']):
            raise ValueError('Runtime poses were built for a different sprite revision.')
        self.pose_clips = self.poses['clips']
        self.pose_tracks = {name: Track(map(tuple, profile['cells']), profile['durations'], False)
                            for name, profile in self.poses['profiles'].items()}
        self.validate_tracks()
        self.sequences.update(('runtime_' + name, track) for name, track in self.pose_tracks.items())
        self.maps = lru_cache(maxsize=36)(self.maps)
        self.renderer = SpriteRenderer(self.maps, self.manifest['channels']['emissive']['scale'], contact_ink)
        self.render = self.renderer.render
        self.surface_fields = self.renderer.surface_fields

    def validate_tracks(self):
        if self.clips.keys() & self.pose_clips.keys():
            raise ValueError('Base and supplemental clip names overlap.')
        cells = set()
        for clips, archive, metadata in ((self.clips, self.bundle, 'playable_manifest.json'),
                                         (self.pose_clips, self.pose_bundle, 'runtime_poses.json')):
            expected = {metadata}
            for name, clip in clips.items():
                views = clip['supported_views']
                if (not views or len(views) != len(set(views)) or not set(views) <= self.manifest['views'].keys()
                        or not clip['samples'] or not _finite(clip['duration_s']) or clip['duration_s'] <= 0):
                    raise ValueError(f'Invalid clip timing/views: {name}')
                for index, sample in enumerate(clip['samples']):
                    if (set(sample['views']) != set(views) or not _finite(sample['duration_s'])
                            or sample['duration_s'] <= 0):
                        raise ValueError(f'Invalid sample timing/views: {(name, index)}')
                    support = sample['support']
                    if len(support) != len(set(support)) or not set(support) <= {'LF','LM','LH','RF','RM','RH'}:
                        raise ValueError(f'Invalid support legs: {(name, index)}')
                    for view, data in sample['views'].items():
                        cell = name, view, index
                        if cell in cells:
                            raise ValueError(f'Duplicate material cell: {cell}')
                        cells.add(cell)
                        member = f'{name}/{view}/{index}.png'
                        expected.add(member)
                        if clips is self.clips:
                            x, y, width, height = data['rect']
                            if (any(type(n) is not int for n in (x,y,width,height))
                                    or min(x,y) < 0 or (width,height) != (SIZE,SIZE)):
                                raise ValueError(f'Invalid atlas rect: {cell}')
                            passes = self.manifest['pass_files'][view]
                            if set(passes) != set(PASSES):
                                raise ValueError(f'Missing atlas pass: {view}')
                            for material in passes.values():
                                aw, ah = material['size']
                                if (type(aw) is not int or type(ah) is not int
                                        or x+width > aw or y+height > ah):
                                    raise ValueError(f'Atlas rect out of bounds: {cell}')
                        markers = data['markers']
                        required = ['foot_contact_' + leg for leg in support]
                        if name == 'feed_cycle':
                            required.append('mouth_marker')
                        if name.startswith(('interact_activate', 'interact_collect')):
                            required.append('interaction_work_socket_RF' if view == 'right' else 'interaction_work_socket')
                        if not set(required) <= markers.keys():
                            raise ValueError(f'Missing support/work marker: {cell}')
                        for marker in markers.values():
                            xy = marker['xy']
                            world = marker.get('world', (0,0,0))
                            if len(xy) != 2 or len(world) != 3 or not all(map(_finite, (*xy,*world))):
                                raise ValueError(f'Invalid marker position: {cell}')
                        with archive.open(member) as image:
                            header = image.read(29)
                        if (len(header) != 29 or header[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
                                or unpack('>II', header[16:24]) != (SIZE, SIZE*len(PASSES))
                                or header[24:26] != b'\x08\x06'):
                            raise ValueError(f'Invalid material PNG header or size: {cell}')
            if set(archive.namelist()) != expected:
                raise ValueError('ZIP members do not match the declared material cells.')
        for track in (*self.sequences.values(), *self.pose_tracks.values()):
            for cell in track.cells:
                if (len(cell) != 3 or type(cell[2]) is not int or cell not in cells):
                    raise ValueError(f'Unknown cell in motion profile: {cell}')
        self.cells = frozenset(cells)
        self.validate_all_images()

    @staticmethod
    def decode(blob, key):
        try:
            with Image.open(BytesIO(blob)) as image:
                if image.format != 'PNG' or image.mode != 'RGBA' or image.size != (SIZE, SIZE*len(PASSES)):
                    raise ValueError(f'Invalid material PNG format or size: {key}')
                image.verify()
            with Image.open(BytesIO(blob)) as image:
                image.load()
                return image.copy()
        except (OSError, SyntaxError) as error:
            raise ValueError(f'Invalid material PNG: {key}') from error

    def validate_all_images(self):
        """Decode every declared cell without retaining images in the runtime cache."""
        if self.closed:
            raise RuntimeError('Assets are closed.')
        for name, view, index in sorted(self.cells):
            archive = self.bundle if name in self.clips else self.pose_bundle
            self.decode(archive.read(f'{name}/{view}/{index}.png'), (name,view,index))
        return len(self.cells)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.renderer.close()
        self.maps.cache_clear()
        self.bundle.close()
        self.pose_bundle.close()

    def maps(self, key):
        if self.closed:
            raise RuntimeError('Assets are closed.')
        if key not in self.cells:
            raise ValueError(f'Unknown material cell: {key}')
        name, view, index = key
        archive = self.bundle if name in self.clips else self.pose_bundle
        image = self.decode(archive.read(f'{name}/{view}/{index}.png'), key)
        return {material: image.crop((0, i*SIZE, SIZE, (i+1)*SIZE)) for i, material in enumerate(PASSES)}

    def sample(self, key):
        name, view, index = key
        if type(index) is not int or index < 0:
            raise ValueError(f'Invalid material cell index: {key}')
        sample = (self.clips if name in self.clips else self.pose_clips)[name]['samples'][index]
        return sample['views'][view]['markers'], sample['support']
