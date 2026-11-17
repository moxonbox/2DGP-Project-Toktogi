"""PNG/APNG codec reused from C011 release_gameplay_r4/export_source.py."""
import struct
import zlib
from fractions import Fraction
import numpy as np

def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag+data)&0xffffffff)


def image_header(a):
    h,w = a.shape[:2]
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w,h,8,6,0,0,0))


def compressed(a):
    return zlib.compress(b"".join(b"\0"+row.tobytes() for row in a), 6)


def png(path, a, color=False):
    color_chunk = chunk(b"sRGB", b"\x00") if color else b""
    path.write_bytes(image_header(a)+color_chunk+chunk(b"IDAT",compressed(a))+chunk(b"IEND",b""))


def apng(path, frames, durations, loop):
    height,width = frames[0].shape[:2]
    parts = [image_header(frames[0]), chunk(b"sRGB", b"\x00"),
             chunk(b"acTL", struct.pack(">II", len(frames), 0 if loop else 1))]
    seq = 0
    for i,(frame,duration) in enumerate(zip(frames,durations)):
        delay = Fraction(duration).limit_denominator(60000)
        parts.append(chunk(b"fcTL", struct.pack(">IIIIIHHBB",seq,width,height,0,0,delay.numerator,delay.denominator,0,0)))
        seq += 1
        data = compressed(frame)
        if i == 0:
            parts.append(chunk(b"IDAT",data))
        else:
            parts.append(chunk(b"fdAT",struct.pack(">I",seq)+data))
            seq += 1
    path.write_bytes(b"".join(parts)+chunk(b"IEND",b""))



def linear_to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= .0031308, 12.92*a, 1.055*a**(1/2.4)-.055)


def srgb_to_linear(a):
    return np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)



