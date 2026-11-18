"""Headless, source-backed material regressions. Run directly to write the report."""
from contextlib import ExitStack
from array import array
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZipFile, ZIP_STORED
from unittest.mock import patch
import json
import sys
import warnings

from PIL import Image, ImageChops
from materials import Assets, PASSES, _json
from sprite_renderer import BLOOM_KERNEL, SpriteRenderer
from lighting import shade

ROOT = Path(__file__).resolve().parent


def _reject(name, operation, rejected):
    try:
        operation()
    except (ValueError, RuntimeError, KeyError):
        rejected.append(name)
    else:
        raise AssertionError(f'{name}: invalid input was accepted')


def _different(a, b):
    difference = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
    return sum(bool(r|g|b) for r,g,b in zip(*(difference.getchannel(c).tobytes() for c in 'RGB')))


def _fixture(emission=True, coverage=255, brightness=255):
    maps = {name: Image.new('RGBA', (128,128), (255,255,255,255)) for name in PASSES}
    maps['base'].putalpha(coverage)
    maps['emissive'] = Image.new('RGBA', (128,128), (0,0,0,255))
    if emission:
        maps['emissive'].putpixel((0,64), (brightness,brightness,brightness,255))
    return maps


def _negative_inputs(assets, rejected):
    _reject('duplicate_json_key', lambda: _json('{"clips":{},"clips":{}}'), rejected)
    _reject('nonfinite_json', lambda: _json('{"value":NaN}'), rejected)
    for mode, size, format in (('RGB',(128,640),'PNG'), ('RGBA',(128,128),'PNG'),
                               ('RGBA',(128,640),'TIFF')):
        stream = BytesIO()
        Image.new(mode, size).save(stream, format=format)
        _reject(f'image_{mode}_{size}_{format}', lambda: Assets.decode(stream.getvalue(), ('bad',)), rejected)
    stream = BytesIO()
    Image.new('RGBA', (128,640)).save(stream, format='PNG')
    _reject('truncated_png', lambda: Assets.decode(stream.getvalue()[:-20], ('bad',)), rejected)
    for variant in ('duplicate', 'missing_metadata', 'crc'):
        stream = BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with ZipFile(stream, 'w', compression=ZIP_STORED) as archive:
                if variant != 'missing_metadata':
                    archive.writestr('metadata.json', '{}')
                archive.writestr('cell.png', b'CRC_PAYLOAD')
                if variant == 'duplicate':
                    archive.writestr('cell.png', b'CRC_PAYLOAD')
        blob = stream.getvalue()
        if variant == 'crc':
            blob = blob.replace(b'CRC_PAYLOAD', b'BAD_PAYLOAD', 1)
        with ZipFile(BytesIO(blob)) as archive:
            _reject(f'zip_{variant}', lambda: Assets.validate_archive(archive, 'metadata.json'), rejected)

    # Mutate one field at a time, restoring even after an unexpected assertion failure.
    clip = assets.clips['idle']
    sample = clip['samples'][0]
    left = sample['views']['left']
    changes = (
        ('duplicate_view', clip, 'supported_views', ['left','left']),
        ('unsupported_view', clip, 'supported_views', ['unknown']),
        ('nonpositive_duration', sample, 'duration_s', 0.),
        ('nonfinite_duration', sample, 'duration_s', float('inf')),
        ('missing_view', sample, 'views', {}),
        ('invalid_support', sample, 'support', ['invalid']),
        ('duplicate_support', sample, 'support', ['LF','LF']),
        ('missing_marker', left, 'markers', {}),
        ('nonfinite_marker', left['markers']['foot_contact_LF'], 'xy', [float('nan'),1.]),
        ('out_of_bounds_rect', left, 'rect', [10**9,0,128,128]),
        ('wrong_rect_size', left, 'rect', [0,0,64,128]),
    )
    for name, container, key, invalid in changes:
        original = container[key]
        container[key] = invalid
        try:
            _reject(name, assets.validate_tracks, rejected)
        finally:
            container[key] = original

    with patch.object(assets.bundle, 'open', side_effect=KeyError('missing cell.png')):
        _reject('missing_png', assets.validate_tracks, rejected)
    with patch.object(assets.bundle, 'open', return_value=BytesIO(b'bad PNG header')):
        _reject('invalid_png_header', assets.validate_tracks, rejected)
    track = next(iter(assets.pose_tracks.values()))
    original = track.cells
    track.cells = (('missing_clip','left',0),)
    try:
        _reject('unknown_profile_cell', assets.validate_tracks, rejected)
    finally:
        track.cells = original

    with TemporaryDirectory(prefix='toktogi_material_verify_') as directory:
        path = Path(directory) / 'bad.zip'
        path.write_bytes(b'not the source bundle')
        path.with_suffix('.source.json').write_text(
            (ROOT / 'toktogi_assets.source.json').read_text(encoding='utf-8'), encoding='utf-8')
        _reject('source_checksum', lambda: Assets(path), rejected)


def verify():
    """Execute checks against adjacent bundles; return only measured results."""
    rejected = []
    with ExitStack() as cleanup:
        started = perf_counter()
        assets = Assets(ROOT / 'toktogi_assets.zip', ROOT / 'toktogi_runtime_poses.zip')
        cleanup.callback(assets.close)
        load_ms = (perf_counter()-started)*1000
        base_cells = sum(cell[0] in assets.clips for cell in assets.cells)
        pose_cells = len(assets.cells)-base_cells
        assert (base_cells,pose_cells) == (1444,930)
        assert assets.maps.cache_info().currsize == 0
        assert assets.validate_all_images() == 2374

        maximum, changed, alpha_changed = 0, 0, 0
        palette_before, palette_after, palette_channels = 0, 0, 0
        with ZipFile(ROOT / 'lighting_reference.zip') as reference:
            cases = json.loads(reference.read('cases.json'))
            assert len(cases) == 24
            for index, case in enumerate(cases):
                key = tuple(case['key'])
                surface = assets.surface_fields(key)
                # The BRDF golden remains unchanged; display grading has a separate palette bound.
                actual = shade(surface, case['light'][0], -case['light'][1],
                               case['roughness'], case['metallic'], case['power'],
                               case['emission'], case['ambient'], assets.renderer.emission_scale).tobytes()
                display = assets.render(key, 'lit', (0,0), case['light'],
                                        case['roughness'], case['metallic'], case['power'],
                                        case['emission'], ambient=case['ambient']).tobytes()
                source = surface[0].tobytes()
                assert display[3::4] == source[3::4] == actual[3::4]
                for offset in range(0, len(source), 4):
                    if source[offset+3] == 0:continue
                    for c in range(3):
                        old_error = abs(actual[offset+c]-source[offset+c])
                        new_error = abs(display[offset+c]-source[offset+c])
                        assert new_error <= .20*old_error+1
                        palette_before += old_error;palette_after += new_error;palette_channels += 1
                expected = reference.read(f'{index}.rgba')
                assert len(actual) == len(expected) == 128*128*4
                alpha_changed += sum(a != b for a,b in zip(actual[3::4],expected[3::4]))
                error = [abs(a-b) for a,b in zip(actual,expected)]
                maximum = max(maximum, max(error))
                changed += sum(value != 0 for value in error)
        assert alpha_changed == 0 and maximum <= 1 and changed <= 4

        key = ('idle','left',0)
        normal = assets.render(key, 'lit', (0,0), (16,30))
        flat = assets.render(key, 'lit', (0,0), (16,30), flat_normal=True)
        moved = assets.render(key, 'lit', (0,0), (115,25))
        dark = assets.render(key, 'lit', (0,0), (16,30), emission=False)
        rough = assets.render(key, 'lit', (0,0), (16,30), roughness=.85)
        metal = assets.render(key, 'lit', (0,0), (16,30), metallic=1.)
        changes = {name: _different(normal,image) for name,image in
                   (('normal',flat),('light',moved),('emission',dark),('roughness',rough),('metallic',metal))}
        assert all(value > 0 for value in changes.values())
        assert all(image.getchannel('A').tobytes() == normal.getchannel('A').tobytes()
                   for image in (flat,moved,dark,rough,metal))
        assert assets.render(key, 'lit', (0,0), (16,30)).tobytes() == normal.tobytes()
        assert [image.getextrema() for image in assets.surface_fields(key, True)[4:7]] == [
            (0.,0.), (0.,0.), (1.,1.)]
        maps = assets.maps(key)
        assert set(maps) == set(PASSES)
        for mode in (*PASSES,'outline','lit'):
            image = assets.render(key, mode, (0,0), (16,30))
            assert image.mode == 'RGBA' and image.size == (128,128)
            if mode in ('normal','rm','emissive'):
                assert image.getchannel('A').tobytes() == maps['base'].getchannel('A').tobytes()
                assert assets.render(key, mode, (0,0), (16,30), flat_normal=True).tobytes() == image.tobytes()
        outline = assets.render(key, 'outline', (0,0), (16,30))
        assert outline.getchannel('A').tobytes() == bytes(
            0 if coverage else alpha for coverage,alpha in zip(
                maps['base'].getchannel('A').tobytes(), maps['sprite'].getchannel('A').tobytes()))

        bright = SpriteRenderer(lambda cell: _fixture(), 1.)
        black = SpriteRenderer(lambda cell: _fixture(False), 1.)
        faint = SpriteRenderer(lambda cell: _fixture(brightness=20), 1.)
        half = SpriteRenderer(lambda cell: _fixture(coverage=128), 1.)
        for renderer in (bright,black,faint,half):
            cleanup.callback(renderer.close)
        frame = Image.new('RGBA', (512,512), (100,100,100,111))
        original = frame.tobytes()
        assert black.composite_bloom(frame, key, (30,30)).tobytes() == original
        assert faint.composite_bloom(frame, key, (30,30)).tobytes() == original
        assert bright.composite_bloom(frame, key, (30,30), emission=False).tobytes() == original
        layer = bright.bloom(key)[0]
        assert abs(sum(BLOOM_KERNEL)-1.) < 1e-12
        assert abs(layer.getpixel((6,70))-BLOOM_KERNEL[6]**2) < 1e-7
        assert abs(sum(array('f',layer.tobytes()))-1.) < 1e-6
        assert abs(half.bloom(key)[0].getpixel((6,70))/layer.getpixel((6,70))-128/255) < 1e-6
        bloom_changes = {}
        reference_patch = None
        for scale in (1,2,3):
            output = bright.composite_bloom(frame, key, (30,30), scale)
            assert frame.tobytes() == original
            assert output.getchannel('A').tobytes() == frame.getchannel('A').tobytes()
            assert output.getpixel((29,30+64*scale))[0] > 100
            clip = (30,30,400,400)
            clipped = bright.composite_bloom(frame, key, (30,30), scale, clip=clip)
            difference = ImageChops.difference(clipped.convert('RGB'), frame.convert('RGB')).getbbox()
            assert difference is not None and difference[0] >= 30 and difference[1] >= 30
            assert difference[2] <= 400 and difference[3] <= 400
            patch = output.crop((30-6*scale,30-6*scale,30+134*scale,30+134*scale))
            if reference_patch is None:
                reference_patch = patch
            else:
                assert patch.tobytes() == reference_patch.resize(patch.size, Image.Resampling.NEAREST).tobytes()
            bloom_changes[str(scale)] = _different(output,frame)
            assert bloom_changes[str(scale)] > 0

        actual_frame = Image.new('RGB', (256,256), (17,19,23))
        actual_frame.paste(normal, (64,64), normal.getchannel('A'))
        actual_bloom = assets.renderer.composite_bloom(actual_frame, key, (64,64))
        actual_changes = _different(actual_frame, actual_bloom)
        assert actual_changes > 0
        glow = maps['emissive'].convert('RGB')
        outside_emission = sum(actual_frame.getpixel((x+64,y+64)) != actual_bloom.getpixel((x+64,y+64))
                               and glow.getpixel((x,y)) == (0,0,0)
                               for y in range(128) for x in range(128))
        assert outside_emission > 0

        _negative_inputs(assets, rejected)
        _reject('nonfinite_light', lambda: bright.render(key,'lit',(0,0),(float('nan'),0)), rejected)
        _reject('invalid_bloom_scale', lambda: bright.composite_bloom(frame,key,(0,0),4), rejected)
        _reject('nonfinite_bloom_origin', lambda: bright.composite_bloom(frame,key,(float('inf'),0)), rejected)
        _reject('invalid_bloom_clip', lambda: bright.composite_bloom(frame,key,(0,0),clip=(0,0,1.5,2)), rejected)
        for cell in sorted(assets.cells)[:110]:
            assets.maps(cell)
            assets.surface_fields(cell)
            assets.render(cell, 'lit', (0,0), (16,30))
            assets.renderer.bloom(cell)
        caches = {name: cache.cache_info().currsize for name,cache in (
            ('maps',assets.maps), ('surface_fields',assets.surface_fields),
            ('lit',assets.renderer.lit), ('bloom',assets.renderer.bloom))}
        assert caches == {'maps':36,'surface_fields':24,'lit':96,'bloom':24}
        assets.close()
        assets.close()
        assert all(cache.cache_info().currsize == 0 for cache in
                   (assets.maps,assets.surface_fields,assets.renderer.lit,assets.renderer.bloom))
        _reject('closed_assets', lambda: assets.maps(key), rejected)
        _reject('closed_renderer', lambda: assets.render(key,'lit',(0,0),(16,30)), rejected)
        assert not any(name == 'pygame' or name.startswith('pygame.') for name in sys.modules)
    return {
        'schema': 1, 'passed': True, 'base_cells': base_cells, 'pose_cells': pose_cells,
        'full_decoded_cells': base_cells+pose_cells, 'load_ms': round(load_ms,3),
        'golden': {'cases':len(cases), 'max_channel_error':maximum,
                   'changed_channels':changed, 'alpha_changed':alpha_changed},
        'palette': {'cases':len(cases), 'source_weight':.8, 'light_weight':.2,
                    'before_mean_rgb_error':round(palette_before/palette_channels,3),
                    'after_mean_rgb_error':round(palette_after/palette_channels,3),
                    'error_reduction_percent':round(100*(1-palette_after/palette_before),2),
                    'alpha_changed':0},
        'changed_pixels':changes, 'flat_normal':[0,0,1], 'preview_modes':7,
        'bloom': {'edge_changed_pixels':bloom_changes, 'real_cell_changed_pixels':actual_changes,
                  'outside_emission_changed_pixels':outside_emission,
                  'black_or_disabled_changed_pixels':0, 'alpha_changed':0,
                  'scales':[1,2,3], 'clip_checked':True, 'linear_coverage_checked':True},
        'cache_sizes':caches, 'rejected_inputs':rejected, 'idempotent_close':True,
        'pygame_imported':False, 'scope':'Pillow CPU checks; native SDL output and full-frame timing are separate.'}


if __name__ == '__main__':
    report = verify()
    output = ROOT / 'material_results.json'
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
