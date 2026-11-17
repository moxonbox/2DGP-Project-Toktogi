"""Environment-r02 validation and headless world binding proof."""
from pathlib import Path
from unittest.mock import patch
import argparse
import hashlib
import json

from PIL import Image
from environment import Environment, MAX_MEMORY, confined, read_png
from world import World


def verify(asset_root=None):
    environment = Environment(asset_root)
    try:
        manifest = environment.manifest
        assert manifest['revision'] == 'environment-r02'
        assert manifest['production_export_allowed'] is False
        checked = 0
        for cell in environment.cells.values():
            image = read_png(environment.root, cell, (384,384*5))
            try:
                assert image.crop((0,0,384,384)).getbbox() == tuple(cell['bbox']['sprite'])
                for index in (2,3,4):
                    assert image.crop((0,index*384,384,(index+1)*384)).getchannel('A').getextrema() == (255,255)
            finally:
                image.close()
            checked += 1
        atlas = manifest['game_atlas']
        assert set(atlas['passes']) == {'sprite','base','normal','rm','emissive'}
        for material, record in atlas['passes'].items():
            image = read_png(environment.root, record, tuple(record['size']))
            try:
                for view, rect in atlas['rects'].items():
                    x,y,width,height = rect
                    assert (width,height) == (384,384)
                    assert 0 <= x < x+width <= image.width and 0 <= y < y+height <= image.height
                    assert (view,0) in environment.cells
            finally:
                image.close()
        world = World.seamless()
        before = tuple((id(p),p.x0,p.x1,p.y,p.bottom) for p in world.course.platforms)
        image = environment.terrain(world)
        assert image.mode == 'RGBA' and image.getbbox() is not None
        assert len(environment.bindings) == len(world.course.platforms)
        assert environment.memory_bytes <= MAX_MEMORY
        assert all(max(map(abs,b['anchor_rounding_error'])) <= .5 for b in environment.bindings)
        assert any(b['status'] == 'provisional_duckweed_for_lotus' for b in environment.bindings)
        assert before == tuple((id(p),p.x0,p.x1,p.y,p.bottom) for p in world.course.platforms)
        prepared_hash = hashlib.sha256(image.tobytes()).hexdigest()
        with patch.object(Path,'open',side_effect=AssertionError('I/O during prepared terrain draw')):
            for camera in ((0,0),(450,-100),(1000,-250),(0,0)):
                canvas = Image.new('RGBA',(1016,585),(0,0,0,255))
                canvas.alpha_composite(image, (round(environment.origin[0]-camera[0]),round(environment.origin[1]-camera[1])))
                assert canvas.getbbox() is not None
                canvas.close()
            assert hashlib.sha256(image.tobytes()).hexdigest() == prepared_hash
        rejected = []
        for name, operation in (
                ('path_escape', lambda:confined(environment.root,'../../../../outside.png')),
                ('absolute_path', lambda:confined(environment.root,environment.root/'outside.png')),
                ('checksum', lambda:read_png(environment.root,{**environment.cell,'sha256':'0'*64},(384,1920))),
                ('wrong_dimensions', lambda:read_png(environment.root,environment.cell,(384,384)))):
            try:
                operation()
            except ValueError:
                rejected.append(name)
            else:
                raise AssertionError(f'{name}: invalid input accepted')
        original_bounds = world.camera_bounds
        world.camera_bounds = (-10000,-10000,10000,10000)
        try:
            environment.terrain(world)
        except ValueError:
            rejected.append('memory_budget')
        else:
            raise AssertionError('Oversized terrain accepted')
        finally:
            world.camera_bounds = original_bounds
        assert hashlib.sha256(environment.image.tobytes()).hexdigest() == prepared_hash
        return {'schema':1, 'passed':True, 'metadata':environment.metadata,
                'decoded_cells':checked, 'decoded_atlases':len(atlas['passes']),
                'platforms':len(environment.bindings), 'image_size':image.size, 'origin':environment.origin,
                'memory_bytes':environment.memory_bytes, 'memory_limit_bytes':MAX_MEMORY,
                'prepared_sha256':prepared_hash, 'bindings':environment.bindings,
                'horizontal_colliders_unchanged':True, 'draw_io_calls':0, 'rejected_inputs':rejected,
                'scope':'CPU art/binding checks only; production export and DEC-06 remain pending.'}
    finally:
        environment.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset-root', type=Path)
    args = parser.parse_args()
    report = verify(args.asset_root)
    Path(__file__).with_name('environment_results.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
