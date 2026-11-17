"""Validated environment-r02 art, prepared once in world coordinates."""
from io import BytesIO
from math import ceil, floor, isfinite
from pathlib import Path
import hashlib
import re

from PIL import Image
from materials import PASSES, _json

MAX_MEMORY = 32 * 1024 * 1024
ASSET_DIRECTORY = 'A/A01_plant_lemna_minor'


def confined(root, relative):
    """Resolve metadata paths without allowing absolute paths or directory escape."""
    relative = Path(relative)
    if relative.is_absolute():
        raise ValueError('Environment paths must be relative.')
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Environment path escapes its asset directory.')
    return path


def read_png(root, record, size):
    path = confined(root, record['file'])
    if path.stat().st_size > size[0]*size[1]*4 + 65536:
        raise ValueError(f'Environment PNG exceeds its size budget: {record["file"]}')
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != record['sha256']:
        raise ValueError(f'Environment PNG checksum mismatch: {record["file"]}')
    try:
        with Image.open(BytesIO(blob)) as image:
            if image.format != 'PNG' or image.mode != 'RGBA' or image.size != size:
                raise ValueError(f'Invalid environment PNG format or dimensions: {record["file"]}')
            image.verify()
        with Image.open(BytesIO(blob)) as image:
            image.load()
            return image.copy()
    except (OSError, SyntaxError) as error:
        raise ValueError(f'Invalid environment PNG: {record["file"]}') from error


class Environment:
    """A01 supplies provisional platform art; gameplay retains its horizontal colliders."""
    def __init__(self, asset_root=None):
        self.asset_root = Path(asset_root) if asset_root is not None else Path(__file__).resolve().parents[2] / 'asset'
        self.asset_root = self.asset_root.resolve()
        self.directory = confined(self.asset_root, ASSET_DIRECTORY)
        index = (self.directory / 'ASSET_INDEX.md').read_text(encoding='utf-8')
        links = [('2D/environment-r02/manifest.json','environment-r02')]
        if not links or links[0][1] != 'environment-r02':
            raise ValueError('The current A01 index must select supported environment-r02.')
        manifest_path = confined(self.directory, links[0][0])
        blob = manifest_path.read_bytes()
        self.manifest = manifest = _json(blob)
        self.root = manifest_path.parent
        if (manifest['schema'] != 'toktogi_environment/1' or manifest['revision'] != links[0][1]
                or manifest['asset_id'] != 'plant_lemna_minor' or manifest['cell_size'] != [384,384]
                or tuple(manifest['pass_order']) != PASSES or manifest['data_alpha'] != 255
                or manifest['coverage_channel'] != 'base.alpha' or manifest['filter'] != 'nearest'
                or manifest['normal_space'] != 'camera_R_right_G_up_B_toward_camera'
                or manifest['display_scale'] != 1 or manifest['mirror_allowed'] is not False):
            raise ValueError('Unsupported environment material/coordinate contract.')
        if (not isfinite(manifest['world_units_per_pixel']) or manifest['world_units_per_pixel'] <= 0
                or not isfinite(manifest['duration_s']) or manifest['duration_s'] <= 0):
            raise ValueError('Invalid environment scale or duration.')
        source = confined(self.directory, manifest['source_blend'])
        with source.open('rb') as stream:
            source_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
        if source_hash != manifest['source_blend_sha256']:
            raise ValueError('Environment source Blend checksum mismatch.')
        self.cells = {}
        files = set()
        for cell in manifest['cells']:
            key = cell['view'], cell['sample']
            if key in self.cells or cell['file'] in files or type(cell['sample']) is not int or cell['sample'] < 0:
                raise ValueError('Duplicate or invalid environment cell.')
            if (cell['mirrored'] is not False or not isfinite(cell['duration_s']) or cell['duration_s'] <= 0
                    or not isfinite(cell['time_s']) or not isfinite(cell['yaw_radians'])):
                raise ValueError('Invalid environment cell timing/view.')
            for point in (cell['pivot'], *(anchor['xy'] for anchor in cell['anchors'].values())):
                if len(point) != 2 or not all(map(isfinite, point)):
                    raise ValueError('Invalid environment anchor or pivot.')
            for anchor in cell['anchors'].values():
                if len(anchor['world']) != 3 or not all(map(isfinite, anchor['world'])):
                    raise ValueError('Invalid environment world anchor.')
            if cell['view_kind'] == 'game' and (cell['view'] not in manifest['game_views']
                                              or cell['pivot'] != manifest['game_pivot']):
                raise ValueError('Environment game view/pivot mismatch.')
            for bbox in cell['bbox'].values():
                if (len(bbox) != 4 or any(type(value) is not int for value in bbox)
                        or not 0 <= bbox[0] < bbox[2] <= 384 or not 0 <= bbox[1] < bbox[3] <= 384):
                    raise ValueError('Invalid environment sprite bounds.')
            confined(self.root, cell['file'])
            self.cells[key] = cell
            files.add(cell['file'])
        if {cell['view'] for cell in self.cells.values() if cell['view_kind'] == 'game'} != set(manifest['game_views']):
            raise ValueError('Incomplete environment game views.')
        self.cell = self.cells['left',0]
        self.anchor = tuple(self.cell['anchors']['frond_top']['xy'])
        decoded = read_png(self.root, self.cell, (384,384*5))
        try:
            self.sprite = decoded.crop((0,0,384,384))
            if self.sprite.getbbox() != tuple(self.cell['bbox']['sprite']):
                raise ValueError('Environment sprite coverage differs from its declared bounds.')
        finally:
            decoded.close()
        self.bbox = self.sprite.getbbox()
        cropped = self.sprite.crop(self.bbox)
        self.sprite.close()
        self.sprite = cropped
        self.image = None
        self.origin = (0,0)
        self.bindings = ()
        self.memory_bytes = self.sprite.width*self.sprite.height*4
        ids = set()
        for path in (self.asset_root / 'A').glob('A*/2D/*/manifest.json'):
            metadata = _json(path.read_bytes())
            ids.add(metadata.get('asset_id',''))
        self.lotus_asset_present = any(any(word in asset.lower() for word in ('lotus','nelumbo','nymphaea')) for asset in ids)
        self.metadata = {
            'asset_id':manifest['asset_id'], 'revision':manifest['revision'],
            'manifest':manifest_path.relative_to(self.asset_root).as_posix(),
            'manifest_sha256':hashlib.sha256(blob).hexdigest(),
            'source_blend':source.relative_to(self.asset_root).as_posix(), 'source_blend_sha256':source_hash,
            'production_export_allowed':manifest['production_export_allowed'],
            'game_integration':manifest['game_integration'], 'collision_status':manifest['collision_status'],
            'lotus_asset_present':self.lotus_asset_present,
            'stage_02_art_status':'lotus_binding_pending' if self.lotus_asset_present else 'lotus_asset_missing',
        }

    def terrain(self, world):
        """Prepare all platforms before play; repeated draws require only image/origin."""
        bounds = world.camera_bounds
        if len(bounds) != 4 or not all(map(isfinite, bounds)) or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
            raise ValueError('Invalid terrain world bounds.')
        left, top, right, bottom = bounds
        bindings = []
        stages = {level.level_id:level.stage_id for level in world.levels}
        for platform in world.course.platforms:
            key = world.platform_ids[id(platform)]
            if key[1] not in stages:
                raise ValueError('Platform references an unknown level.')
            width = max(1, round(platform.x1-platform.x0))
            height = max(1, round(self.sprite.height*width/self.sprite.width))
            scale_x, scale_y = width/self.sprite.width, height/self.sprite.height
            target = ((platform.x0+platform.x1)/2, platform.y)
            anchor = ((self.anchor[0]-self.bbox[0])*scale_x, (self.anchor[1]-self.bbox[1])*scale_y)
            x, y = round(target[0]-anchor[0]), round(target[1]-anchor[1])
            left, top = min(left,x), min(top,y)
            right, bottom = max(right,x+width), max(bottom,y+height)
            stage = stages[key[1]]
            bindings.append({'platform_key':key, 'stage_id':stage, 'asset_id':self.manifest['asset_id'],
                             'revision':self.manifest['revision'], 'view':'left', 'sample':0,
                             'anchor':'frond_top', 'anchor_world':target, 'sprite_origin':(x,y),
                             'sprite_size':(width,height), 'scale':(scale_x,scale_y),
                             'anchor_rounding_error':(x+anchor[0]-target[0],y+anchor[1]-target[1]),
                             'horizontal_support':(platform.x0,platform.x1,platform.y),
                             'production_export_allowed':self.manifest['production_export_allowed'],
                             'status':'provisional_duckweed_for_lotus' if stage == 'stage_02' else 'prototype_duckweed',
                             'collision_binding':'existing_horizontal_platform; DEC-06 pending'})
        origin = floor(left), floor(top)
        size = ceil(right)-origin[0], ceil(bottom)-origin[1]
        memory = (size[0]*size[1] + self.sprite.width*self.sprite.height)*4
        if memory > MAX_MEMORY:
            raise ValueError('Prepared environment exceeds the 32 MiB image budget.')
        if self.image is not None:
            self.image.close()
        self.image = Image.new('RGBA', size, (0,0,0,0))
        for binding in bindings:
            tile = self.sprite.resize(binding['sprite_size'], Image.Resampling.NEAREST)
            try:
                x, y = binding['sprite_origin']
                self.image.alpha_composite(tile, (x-origin[0],y-origin[1]))
            finally:
                tile.close()
        self.origin, self.bindings, self.memory_bytes = origin, tuple(bindings), memory
        return self.image

    def close(self):
        if self.image is not None:
            self.image.close()
            self.image = None
        self.sprite.close()
        self.memory_bytes = 0
