"""Low-volume temporary forest ambience using the existing Pico2D mixer."""
from array import array
import ctypes
from math import sin, pi
from random import Random


def ambient_pcm(rate, channels):
    samples = array('h')
    random = Random(11)
    wind = 0.
    duration = 4
    for index in range(rate*duration):
        time = index/rate
        wind = .985*wind+.015*random.uniform(-1,1)
        edge = min(1.,time/.04,(duration-time)/.04)
        chirp = max(0.,sin(2*pi*2*time))**12
        value = round(32767*edge*(.10*wind+.013*chirp*sin(2*pi*3100*time)))
        samples.extend([value]*channels)
    return samples.tobytes()


class StoryAudio:
    def __init__(self, backend):
        self.mixer = backend.pico
        self.chunk = None
        self.buffer = None
        self.channel = -1
        self.playing = False
        self.error = ''
        self.ready = bool(backend.pico.audio_on)
        if not self.ready:
            self.error = ' · 환경음 장치 사용 불가'

    def sync(self, active):
        if not self.ready or active == self.playing:
            return
        mixer = self.mixer
        if active:
            if self.chunk is None:
                rate, fmt, channels = ctypes.c_int(), ctypes.c_uint16(), ctypes.c_int()
                if (not mixer.Mix_QuerySpec(ctypes.byref(rate),ctypes.byref(fmt),ctypes.byref(channels))
                        or fmt.value != mixer.AUDIO_S16SYS or not 8000 <= rate.value <= 192000
                        or channels.value not in (1,2)):
                    self.ready = False
                    self.error = ' · 환경음 형식 사용 불가'
                    return
                data = ambient_pcm(rate.value,channels.value)
                self.buffer = (ctypes.c_ubyte*len(data)).from_buffer_copy(data)
                self.chunk = mixer.Mix_QuickLoad_RAW(self.buffer,len(data))
                if not self.chunk:
                    self.ready = False
                    self.error = ' · 환경음 생성 실패'
                    return
                self.channel = mixer.Mix_PlayChannelTimed(-1,self.chunk,-1,-1)
                if self.channel < 0:
                    self.ready = False
                    self.error = ' · 환경음 재생 실패'
                    return
                mixer.Mix_Volume(self.channel,64)
            else:
                mixer.Mix_Resume(self.channel)
        else:
            mixer.Mix_Pause(self.channel)
        self.playing = active

    def close(self):
        if self.chunk is not None:
            if self.channel >= 0:
                self.mixer.Mix_HaltChannel(self.channel)
            self.mixer.Mix_FreeChunk(self.chunk)
            self.chunk = None
        self.buffer = None
        self.playing = False
        self.ready = False
