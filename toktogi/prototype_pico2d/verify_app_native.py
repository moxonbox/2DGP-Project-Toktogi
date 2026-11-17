"""Whole-App native dummy checks; real window, IME, DPI and timing remain deferred."""
import ctypes
import argparse
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch


def verify(asset_root=None):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    from app import App, CONTROL_KEYS
    from input_clock import EventClock
    from motion_viewer import MODES
    from physics import STEP
    from timeline import FixedStepTimeline
    root = Path(__file__).resolve().parent
    artifacts = root / 'native_app_artifacts'
    artifacts.mkdir(exist_ok=True)
    checks, screenshots = {}, {}
    app = App(native=True)
    backend, viewer = app.backend, app.viewer
    sdl = backend.sdl
    assert backend.driver == 'dummy'
    present, image_draw = backend.present, backend.Image.draw_to_origin
    rendered, queued, positions = [], [], {}

    def capture(frame):
        queued[:] = backend.text_queue
        positions.clear()
        rendered[:] = [present(frame, capture=True)]
        return rendered[0]

    def observe(image, x, y, w=None, h=None):
        positions[id(image)] = (x, backend.height - y - image.h, image.w, image.h)
        return image_draw(image, x, y, w, h)

    def save(name, frame):
        path = artifacts / name
        frame.save(path)
        screenshots[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def preview_hash():
        return hashlib.sha256(rendered[0].crop((430, 159, 918, 544)).tobytes()).hexdigest()

    def fresh():
        app.scene, app.focused, app.running = 'game', True, True
        app.game.reset()
        app.timeline = FixedStepTimeline(STEP)
        app.physical_keys.clear()
        app.control_keys.clear()
        app.viewer_keys.clear()
        app.epoch, app.context_cutoff, app.dispatch_time = 0, float('-inf'), 0.
        viewer.search, viewer.composition, viewer.searching = '', '', False
        viewer.filter()
        backend.set_text_input(False)

    def raw(kind, milliseconds):
        event = sdl.SDL_Event()
        event.type, event.common.timestamp = kind, 1000 + milliseconds
        return event

    def key(name, milliseconds, down=True):
        event = raw(sdl.SDL_KEYDOWN if down else sdl.SDL_KEYUP, milliseconds)
        event.key.windowID = sdl.SDL_GetWindowID(backend.window)
        event.key.keysym.sym = getattr(sdl, 'SDLK_' + (name.upper() if len(name) > 1 else name))
        event.key.keysym.scancode = sdl.SDL_GetScancodeFromKey(event.key.keysym.sym)
        event.key.state = sdl.SDL_PRESSED if down else sdl.SDL_RELEASED
        return event

    def window(kind, milliseconds):
        event = raw(sdl.SDL_WINDOWEVENT, milliseconds)
        event.window.windowID, event.window.event = sdl.SDL_GetWindowID(backend.window), kind
        return event

    def collect(batch, now=1200):
        sdl.SDL_PumpEvents()
        sdl.SDL_FlushEvents(sdl.SDL_FIRSTEVENT, sdl.SDL_LASTEVENT)
        array = (sdl.SDL_Event * len(batch))(*batch)
        assert sdl.SDL_PeepEvents(array, len(batch), sdl.SDL_ADDEVENT,
                                 sdl.SDL_FIRSTEVENT, sdl.SDL_LASTEVENT) == len(batch)
        clock = EventClock(origin=1000, position_transform=backend.logical_point)
        with patch.object(sdl, 'SDL_GetTicks', return_value=now):
            return clock.events()

    def dispatch(batch, dt, *, epoch=None):
        for event in collect(batch):
            event.epoch = epoch
            app.event(event, at=event.timestamp)
        app.update(dt)

    try:
        with patch.object(backend, 'present', capture), patch.object(backend.Image, 'draw_to_origin', observe):
            app.draw()
            assert rendered[0].size == (1280, 744)
            save('game_legacy.png', rendered[0])
            dispatch([key('f2', 10), key('f2', 11, False)], .02)
            assert app.scene == 'viewer'
            hashes = {}
            for mode, (name, _) in enumerate(MODES):
                viewer.mode = mode
                app.draw()
                hashes[name] = preview_hash()
            assert len(set(hashes.values())) == 7
            viewer.mode = 0
            viewer.flat_normal = True
            app.draw()
            assert preview_hash() != hashes['lit']
            flat_hash = preview_hash()
            viewer.bloom = True
            app.draw()
            assert preview_hash() != flat_hash
            viewer.flat_normal = viewer.bloom = False
            app.draw()
            assert preview_hash() == hashes['lit']
            checks['seven_modes_flat_bloom_and_exact_return'] = hashes
            save('viewer_native.png', rendered[0])

            centered = 0
            for text, x, y, size, color, center in queued:
                if not center:
                    continue
                label = backend.texts[text, size, color]
                left, top, width, height = positions[id(label)]
                assert abs(left + width / 2 - x) <= 1, (text, left, width, x)
                assert abs(top + height / 2 - y) <= 1, (text, top, height, y)
                matching = [rect for rect, _ in viewer.buttons if rect.center == (x, y)]
                assert matching, text
                rect = matching[0]
                assert rect.top + 1 <= top and top + height <= rect.bottom - 1, (text, top, height, rect)
                centered += 1
            assert centered >= 20
            checks['native_button_text_centered_inside_hit_rect'] = centered

            viewer.focus_search()
            committed = raw(sdl.SDL_TEXTINPUT, 30)
            committed.text.text = '한글'.encode('utf-8')
            composing = raw(sdl.SDL_TEXTEDITING, 31)
            composing.edit.text = '연꽃'.encode('utf-8')
            composing.edit.start, composing.edit.length = 1, 1
            dispatch([committed, composing], .02)
            assert viewer.search == '한글' and viewer.composition == '연꽃'
            viewer.search, viewer.composition = '한' * 100, '연꽃'
            viewer.filter()
            app.draw()
            assert viewer.search == '한' * 100 and viewer.composition == '연꽃'
            assert not viewer.filtered
            search_label = next(item for item in queued if item[1:3] == (44, 99))
            text, _, _, size, color, _ = search_label
            assert backend.texts[text, size, color].w <= 286, (text, backend.texts[text, size, color].w)
            font = backend._font(size)
            assert all(backend.ttf.TTF_GlyphIsProvided32(font.font, ord(character)) for character in text), text
            assert sdl.SDL_IsTextInputActive()
            save('search_korean_fit.png', rendered[0])
            checks['native_korean_commit_composition_long_search_fit'] = True

            fresh()
            dispatch([key('p', 10), key('p', 10, False)], .02)
            assert app.game.run == 'Paused' and 'p' not in app.control_keys
            dispatch([key('p', 30), key('p', 31, False)], .02)
            assert app.game.run == 'Playing' and 'p' not in app.control_keys
            checks['same_timestamp_pause_release_then_first_resume'] = True

            fresh()
            dispatch([key('f2', 10), key('space', 20)], .1)
            assert app.scene == 'viewer' and not viewer.playing
            fresh()
            dispatch([key('f2', 10), key('space', 10)], .1)
            assert app.scene == 'viewer' and viewer.playing
            fresh()
            dispatch([key('f2', 10), key('f2', 11, False)], .02)
            assert app.epoch == 1 and viewer.playing
            dispatch([key('space', 5)], 0)
            assert viewer.playing and 'space' not in app.viewer_keys
            dispatch([key('space', 30)], .02, epoch=0)
            assert viewer.playing
            dispatch([key('space', 50)], .02)
            assert not viewer.playing
            checks['native_late_timestamp_stale_epoch_and_fresh_context'] = True

            fresh()
            dispatch([key('space', 5), window(sdl.SDL_WINDOWEVENT_FOCUS_LOST, 10),
                      window(sdl.SDL_WINDOWEVENT_FOCUS_GAINED, 20), key('space', 30, False)], .04)
            assert app.focused and app.game.run == 'Paused'
            assert app.game.launch_count == 0 and not app.game.held
            dispatch([key('p', 50), key('p', 51, False), key('d', 60)], .04)
            assert app.game.run == 'Playing' and 'right' in app.game.held
            checks['native_focus_cancel_orphan_up_and_new_down'] = True

            fresh()
            app.switch('viewer')
            sdl.SDL_SetWindowSize(backend.window, 2560, 1488)
            motion = raw(sdl.SDL_MOUSEMOTION, 11)
            motion.motion.x, motion.motion.y = 200, 400
            mouse = raw(sdl.SDL_MOUSEBUTTONDOWN, 12)
            mouse.button.button, mouse.button.x, mouse.button.y = sdl.SDL_BUTTON_LEFT, 200, 400
            dispatch([window(sdl.SDL_WINDOWEVENT_SIZE_CHANGED, 10), motion, mouse], .02)
            assert backend.output_size == (2560, 1488)
            assert viewer.pointer == (100, 200), viewer.pointer
            sdl.SDL_SetWindowSize(backend.window, *backend.size)
            backend.refresh_coordinates()
            checks['native_resize_and_mouse_same_queue_dispatch_inverse'] = True
            assert not backend.shown
            assert sdl.SDL_GetWindowFlags(backend.window) & sdl.SDL_WINDOW_HIDDEN

            fresh()
            dispatch([key('f2', 10)], .02)
            viewer.focus_search()
            app.draw()
            assert sdl.SDL_IsTextInputActive()
            dispatch([key('f1', 30)], .02)
            assert app.scene == 'game' and not viewer.searching and not sdl.SDL_IsTextInputActive()
            checks['scene_exit_stops_text_input'] = True
    finally:
        app.close()
        app.close()
    assert sdl.SDL_WasInit(0) == 0
    checks['idempotent_app_close_no_live_sdl'] = True

    seamless = App(native=True, profile='seamless', asset_root=asset_root)
    try:
        seamless_backend = seamless.backend
        original_present = seamless_backend.present
        frame = []
        def capture_seamless(image):
            frame[:] = [original_present(image, capture=True)]
        with patch.object(seamless_backend, 'present', capture_seamless):
            seamless.draw()
        assert frame[0].size == (1280, 744) and not seamless.game.world.legacy
        save('game_seamless.png', frame[0])
        checks['seamless_native_game_draw'] = True
    finally:
        seamless.close()
    assert sdl.SDL_WasInit(0) == 0
    report = {'driver': 'dummy', 'renderer': backend.renderer_name, 'checks': checks,
              'screenshots': screenshots, 'source_sha256': {
                  name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in ('app.py', 'motion_viewer.py', 'input_clock.py', 'pico_backend.py')},
              'hardware_deferred': ['physical window/keyboard/focus', 'Korean IME candidate placement',
                                    'actual monitor DPI', 'hardware renderer performance']}
    (root / 'native_app_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', type=Path)
    print(json.dumps(verify(parser.parse_args().asset_root), ensure_ascii=False, indent=2))
