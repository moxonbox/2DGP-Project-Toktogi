"""Engine-neutral input; SDL is loaded only by the native queue adapter."""
from dataclasses import dataclass
import threading

CTRL=0x00c0

@dataclass
class Event:
    type: str
    key: str|None=None
    mod: int=0
    repeat: bool=False
    timestamp: float|None=None
    scancode: int|None=None
    pos: tuple=(0,0)
    text: str=''
    epoch: int|None=None
    button: int=0
    x: int=0
    y: int=0
    start: int=0
    length: int=0

class EventClock:
    def __init__(self,origin=None,position_transform=None):
        if origin is not None and (type(origin) is not int or not 0<=origin<=0xffffffff):
            raise ValueError('SDL tick origin must be an unsigned 32-bit integer.')
        self.sdl=None
        self.thread=threading.get_ident()
        self.position_transform=position_transform or (lambda p:p)
        self.origin=origin
        self.last=self.origin
        self.elapsed=0

    def _advance(self,now):
        if self.last is None:self.origin=self.last=now
        self.elapsed+=(now-self.last)&0xffffffff
        self.last=now

    def normalize(self,stamp,now):
        self._advance(now)
        # Signed age keeps late events on their original side of the wrap.
        age=((now-stamp+0x80000000)&0xffffffff)-0x80000000
        return (self.elapsed-age)/1000

    def events(self):
        import ctypes
        if threading.get_ident()!=self.thread:
            raise RuntimeError('SDL input must be polled on the canvas thread.')
        if self.sdl is None:
            import sdl2dll
            import sdl2
            self.sdl=sdl2
        s=self.sdl
        if not s.SDL_WasInit(s.SDL_INIT_VIDEO):
            raise RuntimeError('SDL input requires an active canvas.')
        self._advance(int(s.SDL_GetTicks()))
        raw=s.SDL_Event()
        result=[]
        while s.SDL_PollEvent(ctypes.byref(raw)):
            stamp=self.normalize(int(raw.common.timestamp),int(s.SDL_GetTicks()))
            kind=int(raw.type); e=None
            if kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
                sym=raw.key.keysym
                name=s.SDL_GetKeyName(sym.sym).decode('utf-8').lower()
                name={'left shift':'lshift','right shift':'rshift','return':'return'}.get(name,name)
                e=Event('key_down' if kind==s.SDL_KEYDOWN else 'key_up',name,int(sym.mod),bool(raw.key.repeat),scancode=int(sym.scancode))
            elif kind==s.SDL_QUIT: e=Event('quit')
            elif kind==s.SDL_WINDOWEVENT:
                event=int(raw.window.event)
                names={s.SDL_WINDOWEVENT_FOCUS_LOST:'focus_lost',s.SDL_WINDOWEVENT_FOCUS_GAINED:'focus_gained',s.SDL_WINDOWEVENT_SIZE_CHANGED:'window_changed',s.SDL_WINDOWEVENT_RESIZED:'window_changed',s.SDL_WINDOWEVENT_CLOSE:'quit'}
                if event in names:e=Event(names[event])
            elif kind in (s.SDL_TEXTINPUT,s.SDL_TEXTEDITING):
                data=raw.text if kind==s.SDL_TEXTINPUT else raw.edit
                e=Event('text_input' if kind==s.SDL_TEXTINPUT else 'text_editing',text=bytes(data.text).split(b'\0',1)[0].decode('utf-8'))
                if kind==s.SDL_TEXTEDITING:e.start,e.length=int(data.start),int(data.length)
            elif kind==s.SDL_TEXTEDITING_EXT:
                data=raw.editExt
                pointer=ctypes.cast(ctypes.byref(data,s.SDL_TextEditingExtEvent.text.offset),
                                    ctypes.POINTER(ctypes.c_void_p)).contents.value
                try:
                    e=Event('text_editing',text=(data.text or b'').decode('utf-8'),
                            start=int(data.start),length=int(data.length))
                finally:
                    s.SDL_free(pointer)
            elif kind in (s.SDL_MOUSEBUTTONDOWN,s.SDL_MOUSEBUTTONUP):
                e=Event('mouse_down' if kind==s.SDL_MOUSEBUTTONDOWN else 'mouse_up',button=int(raw.button.button),pos=self.position_transform((raw.button.x,raw.button.y)))
                e.raw_pos=(raw.button.x,raw.button.y)
            elif kind==s.SDL_MOUSEMOTION:
                e=Event('mouse_motion',pos=self.position_transform((raw.motion.x,raw.motion.y)))
                e.raw_pos=(raw.motion.x,raw.motion.y)
            elif kind==s.SDL_MOUSEWHEEL:
                sign=-1 if raw.wheel.direction==s.SDL_MOUSEWHEEL_FLIPPED else 1
                e=Event('wheel',x=int(raw.wheel.x)*sign,y=int(raw.wheel.y)*sign)
            elif kind in (s.SDL_RENDER_TARGETS_RESET,s.SDL_RENDER_DEVICE_RESET):e=Event('render_reset')
            if e is not None:
                e.timestamp=stamp
                result.append(e)
        return result
