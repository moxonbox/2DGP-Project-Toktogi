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


def byte(a):
    return np.rint(np.clip(a,0,1)*255).astype(np.uint8)


def linear_to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= .0031308, 12.92*a, 1.055*a**(1/2.4)-.055)


def srgb_to_linear(a):
    return np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)


def rgba(rgb, alpha):
    return np.column_stack((rgb,alpha)).reshape(size,size,4)


def outline(mask):
    padded = np.pad(mask,2)
    halo = np.zeros_like(mask)
    for dy in range(-2,3):
        for dx in range(-2,3):
            if dx*dx+dy*dy<=5:
                halo |= padded[2+dy:2+dy+size,2+dx:2+dx+size]
    return halo


def close_tiny_display_holes(halo):
    # Fully enclosed one- or two-pixel gaps in the post-lighting silhouette only.
    empty = ~halo
    padded = np.pad(empty.astype(np.uint8),1,constant_values=1)
    adjacent = sum(padded[1+dy:129+dy,1+dx:129+dx] for dy in (-1,0,1)
                   for dx in (-1,0,1) if dy or dx)
    singles = empty & (adjacent==0)
    candidates = empty & (adjacent==1)
    pair_pad = np.pad(candidates,1)
    paired = np.zeros_like(halo)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dy or dx:
                paired |= pair_pad[1+dy:129+dy,1+dx:129+dx]
    return halo | singles | (candidates & paired)


def composite(a):
    y,x = np.indices(a.shape[:2])
    checker = np.where(((x//8+y//8)%2)[:,:,None], [222,230,233],[242,244,245]).astype(np.uint8)
    rgb = np.where(a[:,:,3:] != 0,a[:,:,:3],checker)
    return np.dstack((rgb,np.full(a.shape[:2],255,dtype=np.uint8)))


