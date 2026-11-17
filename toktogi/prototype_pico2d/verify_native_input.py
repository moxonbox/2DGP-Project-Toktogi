"""Native SDL queue tests. Dummy events do not certify real keyboard/IME/DPI."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch


def verify():
    root = Path(__file__).resolve().parent
    subprocess.run([sys.executable, '-c',
                    "import sys; from input_clock import Event, EventClock; "
                    "clock=EventClock(origin=0); event=Event('key_down',key='space'); "
                    "event.input_time=.01; assert event.epoch is None; "
                    "assert not any(n=='sdl2' or n.startswith('sdl2.') or "
                    "n=='pico2d' or n.startswith('pico2d.') for n in sys.modules)"],
                   cwd=root, check=True, capture_output=True, text=True)
    from input_clock import Event, EventClock, CTRL
    from timeline import FixedStepTimeline
    checks = {'lazy_import_dynamic_event_fields': True}

    clock = EventClock(origin=0xffffff00)
    assert clock.normalize(0xffffff20, 0xffffff80) == .032
    assert clock.normalize(0x20, 0x30) == .288
    assert clock.normalize(0xfffffff0, 0x40) == .240
    assert clock.normalize(0x50, 0x60) == .336
    assert EventClock(origin=1000).normalize(990, 1010) == -.010
    assert EventClock(origin=0xfffffff0).normalize(0, 0) == .016
    checks['wrap_delayed_preorigin_and_zero_timestamps'] = True

    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    from pico_backend import Backend
    backend = Backend(96, 48)
    try:
        sdl = backend.sdl
        window_id = sdl.SDL_GetWindowID(backend.window)
        assert backend.driver == 'dummy'
        assert sdl.SDL_GetWindowFlags(backend.window) & sdl.SDL_WINDOW_HIDDEN
        sdl.SDL_PumpEvents()
        sdl.SDL_FlushEvents(sdl.SDL_FIRSTEVENT, sdl.SDL_LASTEVENT)

        def native(kind, stamp):
            raw = sdl.SDL_Event()
            raw.type = kind
            raw.common.timestamp = stamp
            return raw

        def enqueue(events):
            array = (sdl.SDL_Event * len(events))(*events)
            # PushEvent replaces timestamps; PeepEvents preserves fixture times.
            count = sdl.SDL_PeepEvents(array, len(events), sdl.SDL_ADDEVENT,
                                     sdl.SDL_FIRSTEVENT, sdl.SDL_LASTEVENT)
            assert count == len(events), sdl.SDL_GetError()

        def key_event(key, stamp, *, down=True, repeat=False, mod=0):
            raw = native(sdl.SDL_KEYDOWN if down else sdl.SDL_KEYUP, stamp)
            raw.key.windowID = window_id
            raw.key.state = sdl.SDL_PRESSED if down else sdl.SDL_RELEASED
            raw.key.keysym.sym = key
            raw.key.keysym.scancode = sdl.SDL_GetScancodeFromKey(key)
            raw.key.keysym.mod = mod
            raw.key.repeat = repeat
            return raw

        clock = EventClock(origin=1000, position_transform=backend.logical_point)
        keys = ('left', 'right', 'up', 'down', 'space', 'lshift', 'rshift', 'e', 'f',
                'g', 'x', 'q', 'z', 'p', 'escape', 'r', 'f1', 'f2', 'tab', 'm',
                'l', 'f3', 'v', 'backspace', 'return')
        batch = []
        expected = []
        for index, key in enumerate(keys):
            keycode = getattr(sdl, 'SDLK_' + (key.upper() if len(key) > 1 else key))
            down = key_event(keycode, 1010 + index * 2, repeat=index == 0, mod=CTRL if key == 'f' else 0)
            up = key_event(keycode, 1011 + index * 2, down=False)
            batch.extend((down, up))
            expected.extend(((key, 'key_down', down.key.keysym.scancode, (10 + index * 2) / 1000),
                             (key, 'key_up', up.key.keysym.scancode, (11 + index * 2) / 1000)))
        enqueue(batch)
        with patch.object(sdl, 'SDL_GetTicks', return_value=1200), \
                patch.object(backend.pico, 'get_events', side_effect=AssertionError('second queue consumer')):
            events = clock.events()
            assert [(e.key, e.type, e.scancode, e.timestamp) for e in events] == expected
            assert events[0].repeat and not events[1].repeat
            assert next(e for e in events if e.key == 'f' and e.type == 'key_down').mod == CTRL
            assert clock.events() == []
        assert clock.sdl is backend.sdl
        checks['native_keys_repeat_modifier_scancode_single_queue'] = len(events)

        enqueue([key_event(sdl.SDLK_q, 1030), key_event(sdl.SDLK_e, 1010), key_event(sdl.SDLK_f, 1010)])
        with patch.object(sdl, 'SDL_GetTicks', return_value=1300):
            events = clock.events()
        assert [(e.key, e.timestamp) for e in events] == [('q', .03), ('e', .01), ('f', .01)]
        timeline = FixedStepTimeline(1 / 120)
        for event in events:
            event.epoch = None
            event.input_time = event.timestamp
            timeline.push(event, event.timestamp)
        ordered = []
        timeline.advance(.04, lambda e: ordered.append(e.key), lambda dt, apply: apply(), lambda e: 'tick')
        assert ordered == ['e', 'f', 'q']
        checks['original_late_timestamps_and_stable_timeline_order'] = True

        wrap = EventClock(origin=0xfffffff0)
        with patch.object(sdl, 'SDL_GetTicks', return_value=0x10):
            assert wrap.events() == []
        assert wrap.elapsed == 32
        enqueue([key_event(sdl.SDLK_SPACE, 0x20)])
        with patch.object(sdl, 'SDL_GetTicks', return_value=0x30):
            assert wrap.events()[0].timestamp == .048
        checks['empty_queue_advances_wrap_clock'] = True

        text = native(sdl.SDL_TEXTINPUT, 1400)
        text.text.windowID = window_id
        text.text.text = '톡토기 C011'.encode('utf-8')
        editing = native(sdl.SDL_TEXTEDITING, 1390)
        editing.edit.windowID = window_id
        editing.edit.text = '연꽃'.encode('utf-8')
        editing.edit.start, editing.edit.length = 1, 2
        extended = native(sdl.SDL_TEXTEDITING_EXT, 1395)
        extended.editExt.windowID = window_id
        long_text = ('톡토기 연꽃 ' * 8).encode('utf-8')
        allocation = sdl.SDL_malloc(len(long_text) + 1)
        assert allocation
        ctypes.memmove(allocation, long_text + b'\0', len(long_text) + 1)
        extended.editExt.text = ctypes.cast(allocation, ctypes.c_char_p)
        extended.editExt.start, extended.editExt.length = 3, 4
        enqueue([editing, extended, text])
        free = sdl.SDL_free
        with patch.object(sdl, 'SDL_GetTicks', return_value=1500), \
                patch.object(sdl, 'SDL_free', wraps=free) as released:
            events = clock.events()
            assert [(e.type, e.text, e.start, e.length, e.timestamp) for e in events] == [
                ('text_editing', '연꽃', 1, 2, .390),
                ('text_editing', long_text.decode('utf-8'), 3, 4, .395),
                ('text_input', '톡토기 C011', 0, 0, .400)]
            released.assert_called_once_with(allocation)
        checks['native_utf8_commit_composition_extended_text_ownership'] = True

        sdl.SDL_SetWindowSize(backend.window, 240, 96)
        backend.refresh_coordinates()
        sdl.SDL_PumpEvents()
        sdl.SDL_FlushEvents(sdl.SDL_FIRSTEVENT, sdl.SDL_LASTEVENT)
        motion = native(sdl.SDL_MOUSEMOTION, 1600)
        motion.motion.windowID = window_id
        motion.motion.x, motion.motion.y = 50, 14
        down = native(sdl.SDL_MOUSEBUTTONDOWN, 1601)
        down.button.windowID = window_id
        down.button.button = sdl.SDL_BUTTON_LEFT
        down.button.x, down.button.y = 24, 0
        up = native(sdl.SDL_MOUSEBUTTONUP, 1602)
        up.button.windowID = window_id
        up.button.button = sdl.SDL_BUTTON_LEFT
        up.button.x, up.button.y = 0, 0
        wheel = native(sdl.SDL_MOUSEWHEEL, 1603)
        wheel.wheel.windowID = window_id
        wheel.wheel.x, wheel.wheel.y, wheel.wheel.direction = 2, -3, sdl.SDL_MOUSEWHEEL_FLIPPED
        batch = [motion, down, up, wheel]
        for index, kind in enumerate((sdl.SDL_WINDOWEVENT_FOCUS_LOST, sdl.SDL_WINDOWEVENT_FOCUS_GAINED,
                                      sdl.SDL_WINDOWEVENT_SIZE_CHANGED, sdl.SDL_WINDOWEVENT_RESIZED,
                                      sdl.SDL_WINDOWEVENT_CLOSE)):
            event = native(sdl.SDL_WINDOWEVENT, 1604 + index)
            event.window.windowID, event.window.event = window_id, kind
            batch.append(event)
        batch.extend(native(kind, 1610 + index) for index, kind in enumerate(
            (sdl.SDL_RENDER_TARGETS_RESET, sdl.SDL_RENDER_DEVICE_RESET, sdl.SDL_QUIT)))
        enqueue(batch)
        with patch.object(sdl, 'SDL_GetTicks', return_value=1700):
            events = clock.events()
        assert [e.type for e in events] == ['mouse_motion', 'mouse_down', 'mouse_up', 'wheel',
                                           'focus_lost', 'focus_gained', 'window_changed',
                                           'window_changed', 'quit', 'render_reset', 'render_reset', 'quit']
        assert events[0].pos == (13, 7)
        assert events[1].pos == (0, 0) and events[1].button == sdl.SDL_BUTTON_LEFT
        assert events[2].pos[0] < 0 and events[2].button == sdl.SDL_BUTTON_LEFT
        assert (events[3].x, events[3].y) == (-2, 3)
        assert events[-1].timestamp == .612
        checks['native_mouse_letterbox_inverse_wheel_focus_window_reset_quit'] = True

        def half_window(window, width, height):
            ctypes.cast(width, ctypes.POINTER(ctypes.c_int)).contents.value = 120
            ctypes.cast(height, ctypes.POINTER(ctypes.c_int)).contents.value = 48
        with patch.object(sdl, 'SDL_GetWindowSize', half_window):
            backend.refresh_coordinates()
            motion.motion.x, motion.motion.y = 25, 7
            motion.common.timestamp = 1800
            enqueue([motion])
            with patch.object(sdl, 'SDL_GetTicks', return_value=1900):
                assert clock.events()[0].pos == (13, 7)
        backend.refresh_coordinates()
        checks['native_pointer_with_synthetic_2x_dpi'] = True

        failures = []
        def wrong_thread():
            try:
                clock.events()
            except RuntimeError as error:
                failures.append(str(error))
        thread = threading.Thread(target=wrong_thread)
        thread.start()
        thread.join()
        assert failures == ['SDL input must be polled on the canvas thread.']
        backend.close()
        try:
            clock.events()
        except RuntimeError as error:
            assert 'active canvas' in str(error)
        else:
            raise AssertionError('input adapter accepted a closed canvas')
        checks['canvas_thread_and_lifetime_guard'] = True
        return {'driver': 'dummy', 'checks': checks,
                'hardware_deferred': ['physical keyboard/focus', 'Korean IME candidate placement',
                                      'actual OS DPI', 'real device reset'],
                'note': 'Native SDL queue injection; no visible window or hardware acceptance.'}
    finally:
        backend.close()


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
