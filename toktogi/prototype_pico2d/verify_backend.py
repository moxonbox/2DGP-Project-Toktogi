"""Native SDL dummy-driver checks; these do not certify real hardware or IME."""
import ctypes
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


def run():
    root = Path(__file__).resolve().parent
    probe = subprocess.run([sys.executable, "-c",
                            "import sys; import pico_backend; "
                            "assert not any(n == 'sdl2' or n.startswith('sdl2.') or "
                            "n == 'pico2d' or n.startswith('pico2d.') for n in sys.modules)"],
                           cwd=root, check=True, capture_output=True, text=True)
    assert probe.returncode == 0
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    from PIL import Image
    import sdl2dll
    import sdl2 as sdl
    from pico_backend import Backend, PLAY_CLEAR
    if sdl.SDL_WasInit(0):
        raise RuntimeError("backend verification requires an uninitialized SDL process")
    pico = importlib.import_module("pico2d.pico2d")
    passed = ["lazy_import"]
    backend = None
    calls = dict(open=0, hide=0, image=0, font=0, present=0, close=0)

    def observed(name, function):
        def call(*args, **kwargs):
            calls[name] += 1
            return function(*args, **kwargs)
        return call

    try:
        with patch.object(pico, "open_canvas", observed("open", pico.open_canvas)), \
                patch.object(pico, "hide_lattice", observed("hide", pico.hide_lattice)), \
                patch.object(pico, "load_font", observed("font", pico.load_font)), \
                patch.object(pico.Image, "draw_to_origin", observed("image", pico.Image.draw_to_origin)), \
                patch.object(pico, "update_canvas", observed("present", pico.update_canvas)):
            backend = Backend(96, 48)
            assert backend.driver == "dummy"
            assert not backend.shown
            assert sdl.SDL_GetWindowFlags(backend.window) & sdl.SDL_WINDOW_HIDDEN
            assert isinstance(backend.image, pico.Image)
            assert backend.renderer is pico.renderer and backend.window is pico.window
            assert not pico.lattice_on
            frame = Image.new("RGBA", backend.size, (0, 0, 0, 0))
            frame.putpixel((0, 0), (255, 0, 0, 255))
            frame.putpixel((95, 47), (0, 0, 255, 255))
            frame.putpixel((40, 20), (200, 40, 10, 128))
            result = backend.present(frame, capture=True)
            assert result.getpixel((0, 0)) == (255, 0, 0, 255)
            assert result.getpixel((95, 47)) == (0, 0, 255, 255)
            assert result.getpixel((1, 0))[:3] == PLAY_CLEAR
            expected = Image.alpha_composite(Image.new("RGBA", backend.size, (*PLAY_CLEAR, 255)), frame)
            assert max(abs(a - b) for a, b in zip(result.getpixel((40, 20)),
                                                  expected.getpixel((40, 20)))) <= 1
            assert calls["open"] == 1 and calls["hide"] == 1 and calls["font"] >= 1
            assert calls["image"] >= 1 and calls["present"] >= 4
            passed.append("actual_pico_canvas_image_font_present_rgba_straight_alpha")

        try:
            Backend(96, 48)
        except RuntimeError as error:
            assert "only one" in str(error)
        else:
            raise AssertionError("second canvas was accepted")
        assert backend.present(frame, capture=True).getpixel((0, 0)) == (255, 0, 0, 255)
        passed.append("single_canvas_ownership")

        pattern = Image.new("RGBA", backend.size, (0, 0, 0, 255))
        for y in range(48):
            for x in range(96):
                pattern.putpixel((x, y), ((255, 0, 0, 255) if (x + y) % 2 else (0, 0, 255, 255)))
        for scale in (1, 2, 3):
            sdl.SDL_SetWindowSize(backend.window, 96 * scale, 48 * scale)
            backend.refresh_coordinates()
            scaled = backend.present(pattern, capture=True)
            assert scaled.size == (96 * scale, 48 * scale)
            assert scaled.tobytes() == pattern.resize(scaled.size, Image.Resampling.NEAREST).tobytes()
            assert backend.logical_point((13 * scale, 7 * scale)) == (13, 7)
        sdl.SDL_SetWindowSize(backend.window, 240, 96)
        backend.refresh_coordinates()
        assert backend.viewport == (24, 0, 192, 96)
        assert backend.logical_point((24, 0)) == (0, 0)
        assert backend.logical_point((50, 14)) == (13, 7)
        assert backend.logical_point((0, 0))[0] < 0
        letterbox = backend.present(pattern, capture=True)
        assert letterbox.getpixel((0, 0))[:3] == PLAY_CLEAR
        assert letterbox.crop((24, 0, 216, 96)).tobytes() == pattern.resize((192, 96), Image.Resampling.NEAREST).tobytes()
        with patch.object(sdl, "SDL_GetWindowSize", lambda window, w, h: (
                setattr(ctypes.cast(w, ctypes.POINTER(ctypes.c_int)).contents, "value", 120),
                setattr(ctypes.cast(h, ctypes.POINTER(ctypes.c_int)).contents, "value", 48))):
            backend.refresh_coordinates()
            assert backend.logical_point((25, 7)) == (13, 7)
            rects = []
            def text_rect(pointer):
                value = ctypes.cast(pointer, ctypes.POINTER(sdl.SDL_Rect)).contents
                rects.append((value.x, value.y, value.w, value.h))
            with patch.object(sdl, "SDL_SetTextInputRect", text_rect):
                backend.set_text_input(True, (13, 7, 20, 10))
                assert rects == [(25, 7, 20, 10)]
        backend.set_text_input(False)
        sdl.SDL_SetWindowSize(backend.window, *backend.size)
        backend.refresh_coordinates()
        passed.append("nearest_1x_2x_3x_letterbox_and_synthetic_dpi_inverse")

        clip = sdl.SDL_Rect(1, 2, 3, 4)
        assert sdl.SDL_RenderSetClipRect(backend.renderer, ctypes.byref(clip)) == 0
        background = Image.new("RGBA", backend.size, (*PLAY_CLEAR, 255))
        backend.draw_text("톡토기←→", 1, 2, size=16)
        text_frame = backend.present(background, capture=True)
        assert text_frame.tobytes() != background.tobytes()
        restored = sdl.SDL_Rect()
        sdl.SDL_RenderGetClipRect(backend.renderer, ctypes.byref(restored))
        assert sdl.SDL_RenderIsClipEnabled(backend.renderer)
        assert (restored.x, restored.y, restored.w, restored.h) == (1, 2, 3, 4)
        with patch.object(backend, "_label", side_effect=RuntimeError("injected text failure")):
            backend.draw_text("exception", 0, 0)
            try:
                backend.present(background)
            except RuntimeError as error:
                assert "injected" in str(error)
            else:
                raise AssertionError("text failure did not escape")
        sdl.SDL_RenderGetClipRect(backend.renderer, ctypes.byref(restored))
        assert (restored.x, restored.y, restored.w, restored.h) == (1, 2, 3, 4)
        sdl.SDL_RenderSetClipRect(backend.renderer, None)
        first = backend._label("eviction sentinel", 16, (255, 255, 255))
        for index in range(backend.TEXT_LIMIT + 1):
            backend._label(f"label {index}", 16, (255, 255, 255))
        assert first.texture is None
        assert len(backend.texts) == backend.TEXT_LIMIT
        assert 0 < backend.text_bytes <= backend.TEXT_BYTES
        for size in range(8, 28):
            backend._font(size)
        assert len(backend.fonts) == backend.FONT_LIMIT
        passed.append("native_korean_font_bounded_cache_clip_exception_restore")

        row_bytes = backend.width * 4
        pitch = row_bytes + 16
        memory = (ctypes.c_ubyte * (pitch * backend.height))(*([165] * (pitch * backend.height)))
        unlocked = []
        def padded_lock(texture, rect, pointer, stride):
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_void_p)).contents.value = ctypes.addressof(memory)
            ctypes.cast(stride, ctypes.POINTER(ctypes.c_int)).contents.value = pitch
            return 0
        with patch.object(sdl, "SDL_LockTexture", padded_lock), \
                patch.object(sdl, "SDL_UnlockTexture", lambda texture: unlocked.append(True)):
            backend.present(pattern)
        assert unlocked == [True]
        raw = pattern.tobytes()
        for row in range(backend.height):
            assert bytes(memory[row * pitch:row * pitch + row_bytes]) == raw[row * row_bytes:(row + 1) * row_bytes]
            assert bytes(memory[row * pitch + row_bytes:(row + 1) * pitch]) == bytes([165] * 16)
        with patch.object(sdl, "SDL_LockTexture", return_value=-1), \
                patch.object(sdl, "SDL_UnlockTexture") as unlock:
            try:
                backend.present(pattern)
            except RuntimeError as error:
                assert "SDL_LockTexture" in str(error)
            else:
                raise AssertionError("lock failure was ignored")
            unlock.assert_not_called()
        lock = sdl.SDL_LockTexture
        for bad_pointer in (False, True):
            def invalid_lock(texture, rect, pointer, stride):
                result = lock(texture, rect, pointer, stride)
                if bad_pointer:
                    ctypes.cast(pointer, ctypes.POINTER(ctypes.c_void_p)).contents.value = None
                else:
                    ctypes.cast(stride, ctypes.POINTER(ctypes.c_int)).contents.value = 1
                return result
            with patch.object(sdl, "SDL_LockTexture", invalid_lock):
                try:
                    backend.present(pattern)
                except RuntimeError as error:
                    assert "pointer/pitch" in str(error)
                else:
                    raise AssertionError("invalid pitch or pointer was accepted")
            assert backend.present(pattern, capture=True).tobytes() == pattern.tobytes()
        passed.append("row_pitch_padding_null_lock_failure_unlock_recovery")

        backend.set_text_input(True, (3, 4, 40, 20))
        assert sdl.SDL_IsTextInputActive()
        backend.set_text_input(False)
        assert not sdl.SDL_IsTextInputActive()
        sdl_version = sdl.SDL_version()
        sdl.SDL_GetVersion(ctypes.byref(sdl_version))
        renderer = backend.renderer_name
        with patch.object(pico, "close_canvas", observed("close", pico.close_canvas)):
            backend.close()
            backend.close()
        assert calls["close"] == 1
        assert not sdl.SDL_WasInit(0)
        assert not pico.renderer and not pico.window
        passed.append("text_input_idempotent_shutdown")

        for name, failure in (("SDL_Init", -1), ("IMG_Init", 0), ("TTF_Init", -1),
                              ("SDL_CreateWindow", None), ("SDL_CreateRenderer", None)):
            original = getattr(pico, name)
            with patch.object(pico, name, return_value=failure):
                try:
                    Backend(16, 16)
                except RuntimeError as error:
                    assert name in str(error), str(error)
                else:
                    raise AssertionError(f"{name} failure was accepted")
            assert getattr(pico, name) is original
            assert not sdl.SDL_WasInit(0), name
            assert not pico.renderer and not pico.window
        with patch.object(pico, "Mix_OpenAudio", return_value=-1):
            backend = Backend(16, 16)
            backend.present(Image.new("RGBA", (16, 16), (*PLAY_CLEAR, 255)))
            backend.close()
            assert not sdl.SDL_WasInit(0)
        passed.append("partial_initialization_failure_recovery_optional_audio")
        return {"passed": passed, "driver": "dummy", "renderer": renderer,
                "sdl": f"{sdl_version.major}.{sdl_version.minor}.{sdl_version.patch}",
                "real_hardware": "not tested", "real_ime": "not tested",
                "real_dpi": "not tested", "performance_acceptance": "not tested"}
    finally:
        if backend is not None:
            backend.close()


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
