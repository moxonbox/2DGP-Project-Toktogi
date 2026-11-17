"""Preserve SDL2 queue timestamps that Pygame's keyboard adapter omits."""
from collections import defaultdict, deque
import ctypes
from pathlib import Path

import pygame as pg


class SDLEvent(ctypes.Union):
    # SDL2's public ABI pads SDL_Event to 56 bytes on the supported Windows builds.
    _fields_ = [('words', ctypes.c_uint32*14), ('alignment', ctypes.c_uint64)]


class EventClock:
    def __init__(self):
        if pg.get_sdl_version()[0]!=2:
            raise RuntimeError('This input clock requires SDL2.')
        self.sdl=ctypes.CDLL(str(Path(pg.__file__).parent/'SDL2.dll'))
        self.sdl.SDL_PeepEvents.argtypes=[ctypes.POINTER(SDLEvent),ctypes.c_int,ctypes.c_int,ctypes.c_uint32,ctypes.c_uint32]
        self.sdl.SDL_PeepEvents.restype=ctypes.c_int

    def events(self):
        pg.event.pump()
        size=64
        while True:
            native=(SDLEvent*size)()
            count=self.sdl.SDL_PeepEvents(native,size,1,0,0xffff)
            if count<0:
                raise RuntimeError('SDL_PeepEvents failed while reading input timestamps.')
            if count<size:
                break
            size*=2
        stamps=defaultdict(deque)
        for raw in native[:count]:
            kind,stamp=raw.words[0],raw.words[1]
            if kind in (pg.KEYDOWN,pg.KEYUP):
                stamps[kind,raw.words[4]].append(stamp)
            elif kind==0x200 and raw.words[3]&255 in (12,13):
                focus=pg.WINDOWFOCUSGAINED if raw.words[3]&255==12 else pg.WINDOWFOCUSLOST
                stamps[focus,None].append(stamp)
            elif kind==pg.QUIT:
                stamps[kind,None].append(stamp)
        events=pg.event.get(pump=False)
        for event in events:
            queue=stamps[event.type,getattr(event,'scancode',None)]
            if queue and not hasattr(event,'timestamp'):
                event.timestamp=queue.popleft()
        return events
