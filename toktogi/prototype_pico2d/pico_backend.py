"""Pinned Pico2D 1.5.1 renderer adapter; importing this module opens no device."""
from collections import OrderedDict
import ctypes
import importlib
from importlib.metadata import version
import math
import os
from pathlib import Path
import threading


PLAY_CLEAR = (99, 108, 112)
_active = None


class Backend:
    TEXT_LIMIT = 512
    TEXT_BYTES = 32 * 1024 * 1024
    FONT_LIMIT = 16

    def __init__(self, width=1280, height=744, font_path=None):
        if any(type(v) is not int or not 0 < v <= 4096 for v in (width, height)):
            raise ValueError("canvas dimensions must be integers in [1, 4096]")
        self.width, self.height = self.size = width, height
        self.thread = threading.get_ident()
        self.closed = False
        self.canvas_started = False
        self.shown = False
        self.image = None
        self.fonts, self.texts = OrderedDict(), OrderedDict()
        self.text_bytes = 0
        self.text_queue = []
        candidates = [Path(font_path or os.environ.get("TOKTOGI_FONT", ""))]
        if not font_path and not os.environ.get("TOKTOGI_FONT"):
            candidates = [Path(__file__).parent / "fonts" / "malgun.ttf",
                          Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf"]
        self.font_path = next((p.resolve() for p in candidates if p.is_file()), None)
        if self.font_path is None:
            raise FileNotFoundError(f"Korean font not found: {candidates}")
        try:
            self._open()
        except BaseException:
            self.close()
            raise

    def _check(self, result, stage):
        if result < 0:
            error = self.sdl.SDL_GetError().decode("utf-8", "replace")
            raise RuntimeError(f"{stage}: {error}")
        return result

    def _pointer(self, pointer, stage):
        if not pointer:
            self._check(-1, stage)
        return pointer

    def _alive(self):
        if self.closed:
            raise RuntimeError("Pico2D backend is closed")
        if threading.get_ident() != self.thread:
            raise RuntimeError("Pico2D calls must stay on the canvas thread")

    def _open(self):
        global _active
        if _active is not None:
            raise RuntimeError("only one Pico2D canvas may be active")
        if version("pico2d") != "1.5.1":
            raise RuntimeError("this adapter requires pico2d==1.5.1")
        import sdl2dll  # Select the packaged SDL libraries before importing PySDL2.
        import sdl2
        import sdl2.sdlttf as ttf
        self.sdl, self.ttf = sdl2, ttf
        self.pico = importlib.import_module("pico2d.pico2d")
        sdl, pico = self.sdl, self.pico
        native_version = sdl.SDL_version()
        sdl.SDL_GetVersion(ctypes.byref(native_version))
        if native_version.major != 2:
            raise RuntimeError("Pico2D requires SDL2")
        for name in ("SDL_SetTextureScaleMode", "SDL_GetTextureScaleMode",
                     "SDL_LockTexture", "SDL_GetRendererOutputSize"):
            if not callable(getattr(sdl, name, None)):
                raise RuntimeError(f"required SDL function missing: {name}")
        if getattr(pico, "renderer", None) or getattr(pico, "window", None):
            raise RuntimeError("an external Pico2D canvas already exists")
        _active = self
        pico.renderer, pico.window, pico.audio_on = None, None, False
        names = ("SDL_Init", "IMG_Init", "TTF_Init", "SDL_CreateWindow",
                 "SDL_CreateRenderer", "clear_canvas")
        originals = {name: getattr(pico, name) for name in names}

        def init(flags):
            # Pico2D's mixer handles optional audio failure separately.
            return self._check(originals["SDL_Init"](flags & ~sdl.SDL_INIT_AUDIO), "SDL_Init")

        def image_init(flags):
            result = originals["IMG_Init"](flags)
            if not result & pico.IMG_INIT_PNG:
                self._check(-1, "IMG_Init(PNG)")
            return result

        def create_window(title, x, y, w, h, flags):
            flags = (flags & ~sdl.SDL_WINDOW_SHOWN) | sdl.SDL_WINDOW_HIDDEN | sdl.SDL_WINDOW_ALLOW_HIGHDPI
            return self._pointer(originals["SDL_CreateWindow"](title, x, y, w, h, flags), "SDL_CreateWindow")

        def create_renderer(window, index, flags):
            renderer = originals["SDL_CreateRenderer"](window, index, flags)
            if not renderer:
                renderer = originals["SDL_CreateRenderer"](window, index, sdl.SDL_RENDERER_SOFTWARE)
            return self._pointer(renderer, "SDL_CreateRenderer")

        def clear():
            self._pointer(pico.renderer, "initial renderer")
            self._check(sdl.SDL_SetRenderDrawColor(pico.renderer, *PLAY_CLEAR, 255), "initial color")
            self._check(sdl.SDL_RenderClear(pico.renderer), "initial clear")

        replacements = dict(SDL_Init=init, IMG_Init=image_init,
                            TTF_Init=lambda: self._check(originals["TTF_Init"](), "TTF_Init"),
                            SDL_CreateWindow=create_window, SDL_CreateRenderer=create_renderer,
                            clear_canvas=clear)
        self.canvas_started = True
        try:
            for name, function in replacements.items():
                setattr(pico, name, function)
            pico.open_canvas(self.width, self.height, sync=False)
            pico.hide_lattice()
        finally:
            for name, function in originals.items():
                setattr(pico, name, function)
        self.window, self.renderer = pico.window, pico.renderer
        self.driver = sdl.SDL_GetCurrentVideoDriver().decode("utf-8", "replace")
        info = sdl.SDL_RendererInfo()
        self._check(sdl.SDL_GetRendererInfo(self.renderer, ctypes.byref(info)), "SDL_GetRendererInfo")
        self.renderer_name = info.name.decode("utf-8", "replace")
        self.texture_limit = (info.max_texture_width, info.max_texture_height)
        sdl.SDL_SetWindowTitle(self.window, "Toktogi · Pico2D".encode("utf-8"))
        destroy = sdl.SDL_DestroyTexture

        class OwnedImage(pico.Image):
            def close(image):
                texture, image.texture = getattr(image, "texture", None), None
                if texture:
                    destroy(texture)

            __del__ = close

        self.Image = OwnedImage
        texture = self._pointer(sdl.SDL_CreateTexture(self.renderer, sdl.SDL_PIXELFORMAT_RGBA32,
                                                    sdl.SDL_TEXTUREACCESS_STREAMING, *self.size),
                                "SDL_CreateTexture(RGBA32 streaming)")
        self.image = OwnedImage(texture)
        fmt, access, w, h = ctypes.c_uint32(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
        self._check(sdl.SDL_QueryTexture(texture, ctypes.byref(fmt), ctypes.byref(access),
                                        ctypes.byref(w), ctypes.byref(h)), "SDL_QueryTexture")
        if (fmt.value, access.value, w.value, h.value) != (sdl.SDL_PIXELFORMAT_RGBA32,
                                                        sdl.SDL_TEXTUREACCESS_STREAMING, *self.size):
            raise RuntimeError("renderer did not create the requested RGBA32 streaming texture")
        self._texture_settings(texture)
        self.refresh_coordinates()
        self._font(16)

    def _texture_settings(self, texture):
        sdl = self.sdl
        self._check(sdl.SDL_SetTextureScaleMode(texture, sdl.SDL_ScaleModeNearest), "texture Nearest")
        mode = ctypes.c_int()
        self._check(sdl.SDL_GetTextureScaleMode(texture, ctypes.byref(mode)), "query Nearest")
        if mode.value != sdl.SDL_ScaleModeNearest:
            raise RuntimeError("renderer does not support Nearest textures")
        self._check(sdl.SDL_SetTextureBlendMode(texture, sdl.SDL_BLENDMODE_BLEND), "straight alpha")
        self._check(sdl.SDL_SetTextureColorMod(texture, 255, 255, 255), "texture RGB modulation")
        self._check(sdl.SDL_SetTextureAlphaMod(texture, 255), "texture alpha modulation")

    def _mapping(self):
        sdl = self.sdl
        self._check(sdl.SDL_RenderSetScale(self.renderer, 1.0, 1.0), "reset renderer scale")
        rect = sdl.SDL_Rect(*self.viewport)
        self._check(sdl.SDL_RenderSetViewport(self.renderer, ctypes.byref(rect)), "renderer viewport")
        self._check(sdl.SDL_RenderSetScale(self.renderer, self.scale, self.scale), "renderer scale")

    def refresh_coordinates(self):
        self._alive()
        sdl = self.sdl
        ww, wh, ow, oh = (ctypes.c_int() for _ in range(4))
        sdl.SDL_GetWindowSize(self.window, ctypes.byref(ww), ctypes.byref(wh))
        self._check(sdl.SDL_GetRendererOutputSize(self.renderer, ctypes.byref(ow), ctypes.byref(oh)),
                    "renderer output size")
        if min(ww.value, wh.value, ow.value, oh.value) <= 0:
            raise RuntimeError("window/renderer dimensions are not positive")
        self.window_size, self.output_size = (ww.value, wh.value), (ow.value, oh.value)
        self.scale = min(ow.value / self.width, oh.value / self.height)
        vw, vh = round(self.width * self.scale), round(self.height * self.scale)
        self.viewport = ((ow.value - vw) // 2, (oh.value - vh) // 2, vw, vh)
        self._mapping()

    def logical_point(self, point):
        self._alive()
        x, y = point
        return ((x * self.output_size[0] / self.window_size[0] - self.viewport[0]) / self.scale,
                (y * self.output_size[1] / self.window_size[1] - self.viewport[1]) / self.scale)

    def set_text_input(self, active, rect=None):
        self._alive()
        if active:
            if rect is not None:
                x, y, w, h = rect
                if not all(math.isfinite(v) for v in rect) or min(w, h) <= 0:
                    raise ValueError("text input rectangle must be finite and positive")
                sx, sy = (self.window_size[i] / self.output_size[i] for i in range(2))
                native_rect = self.sdl.SDL_Rect(round((x * self.scale + self.viewport[0]) * sx),
                                               round((y * self.scale + self.viewport[1]) * sy),
                                               max(1, round(w * self.scale * sx)),
                                               max(1, round(h * self.scale * sy)))
                self.sdl.SDL_SetTextInputRect(ctypes.byref(native_rect))
            self.sdl.SDL_StartTextInput()
        else:
            self.sdl.SDL_StopTextInput()

    def _font(self, size):
        if size not in self.fonts:
            font = self.pico.load_font(str(self.font_path), size)
            self.fonts[size] = font
            for character in "톡토기0123456789←→↑↓":
                if not self.ttf.TTF_GlyphIsProvided32(font.font, ord(character)):
                    raise RuntimeError(f"font lacks required glyph {character!r}: {self.font_path}")
            while len(self.fonts) > self.FONT_LIMIT:
                _, old = self.fonts.popitem(last=False)
                self.ttf.TTF_CloseFont(old.font)
                old.font = None
        self.fonts.move_to_end(size)
        return self.fonts[size]

    def draw_text(self, text, x, y, size=16, color=(219, 232, 218), center=False):
        self._alive()
        if not isinstance(text, str) or len(text) > 1000 or "\0" in text:
            raise ValueError("text must contain at most 1000 characters and no NUL")
        if type(size) is not int or not 8 <= size <= 64:
            raise ValueError("font size must be an integer in [8, 64]")
        if not all(math.isfinite(v) for v in (x, y)):
            raise ValueError("text position must be finite")
        color = tuple(color)
        if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
            raise ValueError("text color must be three bytes")
        if text:
            self.text_queue.append((text, x, y, size, color, center))

    def _label(self, text, size, color):
        key = (text, size, color)
        if key not in self.texts:
            font = self._font(size)
            surface = self._pointer(self.ttf.TTF_RenderUTF8_Blended(
                font.font, text.encode("utf-8"), self.sdl.SDL_Color(*color, 255)), "TTF_RenderUTF8_Blended")
            try:
                w, h = surface.contents.w, surface.contents.h
                cost = w * h * 4
                if cost > self.TEXT_BYTES or any(limit and actual > limit for actual, limit in
                                                zip((w, h), self.texture_limit)):
                    raise ValueError("text texture exceeds renderer/cache limits")
                texture = self._pointer(self.sdl.SDL_CreateTextureFromSurface(self.renderer, surface),
                                        "SDL_CreateTextureFromSurface(text)")
            finally:
                self.sdl.SDL_FreeSurface(surface)
            image = self.Image(texture)
            try:
                self._texture_settings(texture)
            except BaseException:
                image.close()
                raise
            self.texts[key] = image
            self.text_bytes += cost
            while len(self.texts) > self.TEXT_LIMIT or self.text_bytes > self.TEXT_BYTES:
                _, old = self.texts.popitem(last=False)
                self.text_bytes -= old.w * old.h * 4
                old.close()
        self.texts.move_to_end(key)
        return self.texts[key]

    def present(self, image, capture=False):
        self._alive()
        if image.mode != "RGBA" or image.size != self.size:
            raise ValueError(f"present requires RGBA image of size {self.size}")
        raw = image.tobytes()
        row_bytes = self.width * 4
        if len(raw) != row_bytes * self.height:
            raise ValueError("RGBA byte count differs from canvas dimensions")
        sdl = self.sdl
        pixels, pitch = ctypes.c_void_p(), ctypes.c_int()
        self._check(sdl.SDL_LockTexture(self.image.texture, None, ctypes.byref(pixels),
                                       ctypes.byref(pitch)), "SDL_LockTexture")
        try:
            if not pixels.value or pitch.value < row_bytes:
                raise RuntimeError(f"invalid locked texture pointer/pitch: {pitch.value}")
            source = ctypes.c_char_p(raw)
            source_address = ctypes.cast(source, ctypes.c_void_p).value
            for row in range(self.height):
                ctypes.memmove(pixels.value + row * pitch.value, source_address + row * row_bytes, row_bytes)
        finally:
            sdl.SDL_UnlockTexture(self.image.texture)
        clip = sdl.SDL_Rect()
        clipped = sdl.SDL_RenderIsClipEnabled(self.renderer)
        sdl.SDL_RenderGetClipRect(self.renderer, ctypes.byref(clip))
        queue, self.text_queue = self.text_queue, []
        try:
            self._check(sdl.SDL_RenderSetClipRect(self.renderer, None), "clear frame clip")
            self._check(sdl.SDL_SetRenderDrawColor(self.renderer, *PLAY_CLEAR, 255), "frame color")
            self._check(sdl.SDL_RenderClear(self.renderer), "frame clear")
            self.image.draw_to_origin(0, 0, *self.size)
            for text, x, y, size, color, center in queue:
                label = self._label(text, size, color)
                if center:
                    x -= label.w / 2
                label.draw_to_origin(round(x), self.height - round(y) - label.h)
            result = self._capture() if capture else None
            self.pico.update_canvas()
            if not self.shown and self.driver != "dummy":
                sdl.SDL_ShowWindow(self.window)
                self.shown = True
            return result
        finally:
            self._check(sdl.SDL_RenderSetClipRect(self.renderer, ctypes.byref(clip) if clipped else None),
                        "restore frame clip")

    def _capture(self):
        from PIL import Image
        w, h = self.output_size
        buffer = (ctypes.c_ubyte * (w * h * 4))()
        try:
            self._check(self.sdl.SDL_RenderSetScale(self.renderer, 1, 1), "capture scale")
            self._check(self.sdl.SDL_RenderSetViewport(self.renderer, None), "capture viewport")
            self._check(self.sdl.SDL_RenderReadPixels(self.renderer, None, self.sdl.SDL_PIXELFORMAT_RGBA32,
                                                     buffer, w * 4), "SDL_RenderReadPixels")
            return Image.frombytes("RGBA", (w, h), bytes(buffer))
        finally:
            self._mapping()

    def close(self):
        global _active
        if self.closed:
            return
        self.closed = True
        self.text_queue.clear()
        for image in self.texts.values():
            image.close()
        self.texts.clear()
        self.text_bytes = 0
        if self.image is not None:
            self.image.close()
            self.image = None
        for font in self.fonts.values():
            self.ttf.TTF_CloseFont(font.font)
            font.font = None
        self.fonts.clear()
        if self.canvas_started:
            self.sdl.SDL_StopTextInput()
            try:
                self.pico.close_canvas()
            finally:
                # Pico2D omits Mix_Quit when opening the audio device failed.
                if not self.pico.audio_on:
                    self.pico.Mix_Quit()
                self.pico.renderer, self.pico.window, self.pico.audio_on = None, None, False
                self.canvas_started = False
        if _active is self:
            _active = None
