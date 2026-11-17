"""Measured native dummy throughput; this never grants real-device acceptance."""
import argparse
import builtins
from contextlib import ExitStack
import ctypes
from ctypes import wintypes
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter
from unittest.mock import patch
import zipfile


SAMPLES = 120
WARMUP_FRAMES = 30
DT = 1 / 60
P95_BUDGET_MS = 16.7
MAX_BUDGET_MS = 33.4
MIB = 1024 * 1024


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


def memory_reader():
    if sys.platform != 'win32':
        raise RuntimeError('This benchmark records Windows PSAPI memory and loaded DLL handles.')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    process = kernel.GetCurrentProcess()
    def read():
        counters = MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {'rss_bytes': counters.WorkingSetSize, 'peak_rss_bytes': counters.PeakWorkingSetSize,
                'private_bytes': counters.PrivateUsage}
    return read


def summary(values):
    ordered = sorted(values)
    return {'samples': len(values), 'median_ms': round(statistics.median(ordered), 4),
            'p95_ms': round(ordered[math.ceil(.95 * len(ordered)) - 1], 4),
            'max_ms': round(ordered[-1], 4)}


def native_environment(backend):
    import sdl2.sdlimage as image
    import sdl2.sdlmixer as mixer
    sdl, ttf = backend.sdl, backend.ttf
    core_version = sdl.SDL_version()
    sdl.SDL_GetVersion(ctypes.byref(core_version))
    libraries = [('SDL2', sdl.dll.dll, core_version),
                 ('SDL2_image', image.dll, image.IMG_Linked_Version().contents),
                 ('SDL2_ttf', ttf.dll, ttf.TTF_Linked_Version().contents),
                 ('SDL2_mixer', mixer.dll, mixer.Mix_Linked_Version().contents)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetModuleFileNameW.restype = wintypes.DWORD
    dlls = {}
    for name, library, version in libraries:
        path = ctypes.create_unicode_buffer(32768)
        length = kernel.GetModuleFileNameW(library._dll._handle, path, len(path))
        if not 0 < length < len(path):
            raise ctypes.WinError(ctypes.get_last_error())
        actual = Path(path.value).resolve()
        assert actual.is_absolute() and actual.is_file()
        dlls[name] = {'version': f'{version.major}.{version.minor}.{version.patch}',
                      'path': str(actual), 'sha256': hashlib.sha256(actual.read_bytes()).hexdigest()}
    info = sdl.SDL_RendererInfo()
    assert sdl.SDL_GetRendererInfo(backend.renderer, ctypes.byref(info)) == 0
    dpi = [ctypes.c_float() for _ in range(3)]
    display = sdl.SDL_GetWindowDisplayIndex(backend.window)
    dpi_result = sdl.SDL_GetDisplayDPI(display, *(ctypes.byref(value) for value in dpi))
    return {'os': platform.platform(), 'machine': platform.machine(), 'processor': platform.processor(),
            'python': sys.version, 'python_executable': str(Path(sys.executable).resolve()),
            'pointer_bits': ctypes.sizeof(ctypes.c_void_p) * 8,
            'packages': {name: importlib.metadata.version(name) for name in ('pico2d', 'Pillow', 'PySDL2', 'pysdl2-dll')},
            'loaded_dlls': dlls, 'renderer': backend.renderer_name, 'driver': backend.driver,
            'renderer_info_flags': int(info.flags),
            'renderer_supports_vsync': bool(info.flags & sdl.SDL_RENDERER_PRESENTVSYNC),
            'vsync_requested': False,
            'vsync_observation': 'Pico2D open_canvas(sync=False); renderer capability flags are not active sync state.',
            'window_size': backend.window_size, 'output_size': backend.output_size,
            'viewport': backend.viewport, 'logical_scale': backend.scale,
            'window_to_output_ratio': [backend.output_size[i] / backend.window_size[i] for i in (0, 1)],
            'display_dpi': [value.value for value in dpi] if dpi_result == 0 else None,
            'display_dpi_error': None if dpi_result == 0 else sdl.SDL_GetError().decode('utf-8', 'replace'),
            'font': {'path': str(backend.font_path), 'sha256': hashlib.sha256(backend.font_path.read_bytes()).hexdigest()},
            'intentional_wait_ms': 0, 'readback_enabled': False}


def caches(app):
    renderer, backend = app.assets.renderer, app.backend
    counts = {name: function.cache_info()._asdict() for name, function in (
        ('maps', app.assets.maps), ('surface_fields', renderer.surface_fields),
        ('lighting', renderer.lit), ('bloom', renderer.bloom), ('pillow_text', app.viewer.text_surface))}
    expected = {'maps': 36, 'surface_fields': 24, 'lighting': 96, 'bloom': 24, 'pillow_text': 512}
    for name, info in counts.items():
        assert info['maxsize'] == expected[name] and info['currsize'] <= info['maxsize'], (name, info)
    assert len(backend.texts) <= backend.TEXT_LIMIT == 512
    assert len(backend.fonts) <= backend.FONT_LIMIT == 16
    assert backend.text_bytes <= backend.TEXT_BYTES == 32 * MIB
    assert app.play_view.environment.memory_bytes <= 32 * MIB
    return {'counts': counts, 'native_text_count': len(backend.texts), 'native_font_count': len(backend.fonts),
            'native_text_bytes': backend.text_bytes, 'environment_bytes': app.play_view.environment.memory_bytes,
            'streaming_rgba_bytes': backend.width * backend.height * 4,
            'map_rgba_payload_bytes': counts['maps']['currsize'] * 128 * 128 * 5 * 4,
            'lighting_rgba_payload_bytes': counts['lighting']['currsize'] * 128 * 128 * 4,
            'bloom_float_payload_upper_bytes': counts['bloom']['currsize'] * 140 * 140 * 3 * 4,
            'note': 'Payload sizes exclude Python objects, native overhead and temporary images; RSS includes them.'}


def verify(asset_root=None):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    read_memory = memory_reader()
    before = read_memory()
    import_start = perf_counter()
    from app import App
    import environment
    import_ms = (perf_counter() - import_start) * 1000
    load_start = perf_counter()
    app = App(native=True, profile='seamless', asset_root=asset_root)
    load_ms = (perf_counter() - load_start) * 1000
    backend, viewer = app.backend, app.viewer
    assert backend.driver == 'dummy'
    report = {'scope': 'Native SDL dummy throughput; real-device acceptance pending regardless of these results.',
              'policy': {'frames_per_phase': SAMPLES, 'warmup_frames_per_phase': WARMUP_FRAMES,
                         'p95_budget_ms': P95_BUDGET_MS, 'maximum_budget_ms': MAX_BUDGET_MS,
                         'text_memory_limit_bytes': 32 * MIB, 'environment_memory_limit_bytes': 32 * MIB,
                         'percentile': 'nearest rank', 'rss_limit_bytes': None,
                         'rss_policy': 'Measured, not an invented hardware acceptance cap.'},
              'import_ms': round(import_ms, 3), 'app_load_ms': round(load_ms, 3),
              'memory_before_import': before, 'memory_after_load': read_memory(), 'phases': {}}
    present, unlock, update_canvas = backend.present, backend.sdl.SDL_UnlockTexture, backend.pico.update_canvas
    sample = {}
    native_start = 0.

    def timed_unlock(texture):
        result = unlock(texture)
        sample['upload_ms'] = (perf_counter() - native_start) * 1000
        return result

    def timed_canvas():
        start = perf_counter()
        result = update_canvas()
        sample['present_ms'] = (perf_counter() - start) * 1000
        return result

    def timed_backend(frame):
        nonlocal native_start
        native_start = perf_counter()
        result = present(frame)
        sample['backend_ms'] = (perf_counter() - native_start) * 1000
        sample['native_composite_ms'] = max(0., sample['backend_ms'] - sample['upload_ms'] - sample['present_ms'])
        return result

    def frame(update=None):
        sample.clear()
        start = perf_counter()
        if update is None:
            app.update(DT)
        else:
            update()
        drawing = perf_counter()
        sample['update_ms'] = (drawing - start) * 1000
        app.draw()
        end = perf_counter()
        sample['cpu_draw_ms'] = max(0., (end - drawing) * 1000 - sample['backend_ms'])
        sample['total_ms'] = (end - start) * 1000
        return dict(sample)

    try:
        report['environment'] = native_environment(backend)
        # Selected idle maps are warmed explicitly; moving lights still compute new shaded pixels.
        prime_start = perf_counter()
        for view in ('left', 'right'):
            for cell in app.assets.tracks['idle', view].cells:
                app.assets.maps(cell)
                app.assets.renderer.surface_fields(cell)
        report['idle_map_priming_ms'] = round((perf_counter() - prime_start) * 1000, 3)
        with patch.object(backend, 'present', timed_backend), \
                patch.object(backend.sdl, 'SDL_UnlockTexture', timed_unlock), \
                patch.object(backend.pico, 'update_canvas', timed_canvas):
            for name in ('play_idle', 'viewer_moving_light', 'viewer_moving_light_bloom'):
                app.switch('game' if name == 'play_idle' else 'viewer')
                viewer.mode, viewer.light_mode, viewer.playing, viewer.time = 0, 2, False, 0.
                viewer.flat_normal, viewer.bloom, viewer.emission = False, name.endswith('_bloom'), True
                warm_start = perf_counter()
                for _ in range(WARMUP_FRAMES):
                    frame()
                warm_ms = (perf_counter() - warm_start) * 1000
                memory_start, cache_start = read_memory(), caches(app)
                records, rss = [], []
                for _ in range(SAMPLES):
                    records.append(frame())
                    rss.append(read_memory()['rss_bytes'])
                metrics = {key: summary([record[key] for record in records]) for key in records[0]}
                totals = sorted(record['total_ms'] for record in records)
                report['phases'][name] = {'warmup_ms': round(warm_ms, 3), 'metrics': metrics,
                    'budget_met': totals[math.ceil(.95 * SAMPLES) - 1] <= P95_BUDGET_MS and totals[-1] <= MAX_BUDGET_MS,
                    'memory_start': memory_start, 'memory_end': read_memory(), 'sampled_peak_rss_bytes': max(rss),
                    'caches_start': cache_start, 'caches_end': caches(app), 'samples': records}

            app.switch('game')
            game, world = app.game, app.game.world
            game.support = world.course.platforms[4]
            game.x, game.y, game.vx, game.vy, game.view = 995., 125., 0., 0., 'right'
            world.level_id = world.portals[0].left
            app.assets.maps(game.visual())
            app.assets.renderer.surface_fields(game.visual())
            prepared = app.play_view.environment.image
            reads = []
            def forbidden_read(*args, **kwargs):
                reads.append(str(args[0]) if args else 'environment preparation')
                raise AssertionError('Warmed boundary draw performed resource I/O or terrain reconstruction.')
            boundary = []
            with ExitStack() as stack:
                for target, name in ((builtins, 'open'), (io, 'open'), (zipfile.ZipFile, 'open'),
                                     (environment, 'read_png'), (environment.Environment, 'terrain')):
                    stack.enter_context(patch.object(target, name, forbidden_read))
                for x, expected in ((1005., world.portals[0].right), (995., world.portals[0].left)):
                    def cross():
                        previous = game.x, game.y
                        game.x = x
                        world.advance(previous, (game.x, game.y))
                        app.play_view.step(game, DT)
                    boundary.append({'level': expected, 'metrics': frame(cross)})
                    assert world.level_id == expected
                    assert app.play_view.environment.image is prepared
            assert not reads
            report['initialized_boundary'] = {'first_and_reverse': boundary, 'resource_reads': len(reads),
                'note': 'Initialized bridge positions, not a reachability or complete-route benchmark.',
                'same_prepared_environment': True}
            assert not backend.shown
            assert backend.sdl.SDL_GetWindowFlags(backend.window) & backend.sdl.SDL_WINDOW_HIDDEN
        report['memory_before_close'] = read_memory()
        report['all_dummy_budgets_met'] = all(value['budget_met'] for value in report['phases'].values())
        report['real_device_acceptance'] = 'pending'
        report['timing_definitions'] = {
            'upload_ms': 'Backend entry through SDL_UnlockTexture return: validation, RGBA bytes and pitch copy.',
            'native_composite_ms': 'Remaining native backend work, including native text, excluding upload/present.',
            'cpu_draw_ms': 'App.draw excluding the native Backend.present call.',
            'present_ms': 'Actual Pico2D.update_canvas/SDL_RenderPresent; dummy, sync=False requested.',
            'total_ms': 'Update plus complete draw; no intentional sleep, device readback, disk writes or RSS query.'}
    finally:
        app.close()
    report['memory_after_close'] = read_memory()
    assert backend.sdl.SDL_WasInit(0) == 0
    root = Path(__file__).resolve().parent
    report['source_sha256'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                              ('app.py', 'play_view.py', 'motion_viewer.py', 'pico_backend.py', 'sprite_renderer.py', 'verify_performance.py')}
    (root / 'performance_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path)
    result = verify(parser.parse_args().asset_root)
    print(json.dumps({'app_load_ms': result['app_load_ms'],
                      'phases': {name: value['metrics']['total_ms'] for name, value in result['phases'].items()},
                      'all_dummy_budgets_met': result['all_dummy_budgets_met'],
                      'real_device_acceptance': result['real_device_acceptance'],
                      'report': str(Path(__file__).with_name('performance_results.json'))}, indent=2))
