"""Pillow material previews and CPU lighting; no renderer or texture ownership."""
from functools import lru_cache
from math import exp, isfinite

from PIL import Image, ImageChops
from lighting import calc, fields, shade, srgb

SIZE = 128
SRGB = tuple(i/255/12.92 if i <= 10 else ((i/255+.055)/1.055)**2.4 for i in range(256))
LINEAR = [i/255 for i in range(256)]
BLOOM_RADIUS = 6
_weights = tuple(exp(-x*x/8) for x in range(-BLOOM_RADIUS, BLOOM_RADIUS+1))
BLOOM_KERNEL = tuple(value/sum(_weights) for value in _weights)


class SpriteRenderer:
    def __init__(self, maps, emission_scale, ink=None):
        if not isfinite(emission_scale) or emission_scale < 0:
            raise ValueError('Emission scale must be finite and nonnegative.')
        self.maps = maps
        self.emission_scale = emission_scale
        self.ink = ink
        self.closed = False
        self.surface_fields = lru_cache(maxsize=24)(self.surface_fields)
        self.lit = lru_cache(maxsize=96)(self.lit)
        self.bloom = lru_cache(maxsize=24)(self.bloom)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.lit.cache_clear()
        self.surface_fields.cache_clear()
        self.bloom.cache_clear()

    def render(self, key, mode, origin, light, roughness=None, metallic=None, power=1., emission=True,
               *, ambient=.115, flat_normal=False):
        if self.closed:
            raise RuntimeError('Sprite renderer is closed.')
        if mode == 'lit':
            return self.lit(key, light[0]-origin[0], origin[1]-light[1], roughness, metallic,
                            power, emission, ambient, flat_normal)
        maps = self.maps(key)
        if mode in ('base', 'sprite'):
            return maps[mode]
        coverage = maps['base'].getchannel('A')
        if mode == 'outline':
            image = maps['sprite'].copy()
            image.putalpha(Image.composite(Image.new('L', (SIZE,SIZE)), image.getchannel('A'),
                                           coverage.point([0]+[255]*255)))
        else:
            image = maps[mode].copy()
            image.putalpha(coverage)
        return image

    def surface_fields(self, key, flat_normal=False):
        if self.closed:
            raise RuntimeError('Sprite renderer is closed.')
        return fields(self.maps(key), self.ink(key) if self.ink else (), SRGB, flat_normal=flat_normal)

    def lit(self, key, lx, ly, roughness, metallic, power, emission, ambient, flat_normal=False):
        if self.closed:
            raise RuntimeError('Sprite renderer is closed.')
        if (not all(isfinite(value) for value in (lx,ly,power,ambient)) or min(power,ambient) < 0
                or roughness is not None and (not isfinite(roughness) or not 0 < roughness <= 1)
                or metallic is not None and (not isfinite(metallic) or not 0 <= metallic <= 1)):
            raise ValueError('Invalid lighting parameter.')
        return shade(self.surface_fields(key, flat_normal), lx, ly, roughness, metallic,
                     power, emission, ambient, self.emission_scale)

    def bloom(self, key):
        """Return three padded linear RGB layers; fixed kernel, threshold and emission scale."""
        if self.closed:
            raise RuntimeError('Sprite renderer is closed.')
        maps = self.maps(key)
        coverage = maps['base'].getchannel('A').point(LINEAR, 'F')
        channels = [calc(lambda v: v['e']*v['a']*v['s'],
                         e=maps['emissive'].getchannel(c).point(LINEAR, 'F'),
                         a=coverage, s=float(self.emission_scale)) for c in 'RGB']
        luminance = calc(lambda v: .2126*v['r']+.7152*v['g']+.0722*v['b'],
                         r=channels[0], g=channels[1], b=channels[2])
        threshold = calc(lambda v: v['min'](v['max']((v['y']-.12)/.10, 0.), 1.), y=luminance)
        box=threshold.getbbox()
        if box is None:
            return None
        width,height=box[2]-box[0]+2*BLOOM_RADIUS,box[3]-box[1]+2*BLOOM_RADIUS
        side = SIZE + 2*BLOOM_RADIUS
        layers = []
        for channel in channels:
            layer = Image.new('F', (width,height), 0.)
            layer.paste(calc(lambda v: v['e']*v['t'], e=channel, t=threshold).crop(box), (BLOOM_RADIUS,)*2)
            for axis in (0,1):
                blurred = Image.new('F', (width,height), 0.)
                for offset, weight in zip(range(-BLOOM_RADIUS, BLOOM_RADIUS+1), BLOOM_KERNEL):
                    dx, dy = (offset,0) if axis == 0 else (0,offset)
                    shifted = layer.crop((-dx,-dy,width-dx,height-dy))
                    blurred = calc(lambda v: v['a']+v['b']*v['w'], a=blurred, b=shifted, w=weight)
                layer = blurred
            padded=Image.new('F',(side,side),0.)
            padded.paste(layer,box[:2])
            layers.append(padded)
        return tuple(layers)

    def composite_bloom(self, background, key, origin, scale=1, *, emission=True, clip=None, in_place=False):
        """Add emissive Bloom after the sprite and before overlays.

        Origin is the sprite's screen top-left. Clip is (left, top, right, bottom).
        Scale must be 1, 2 or 3; light power never changes this emissive-only effect.
        Set in_place only for caller-owned frame buffers; otherwise return a copy.
        Disabled/empty Bloom returns the unchanged input without allocating a copy.
        """
        if self.closed:
            raise RuntimeError('Sprite renderer is closed.')
        if background.mode not in ('RGB','RGBA') or type(scale) is not int or scale not in (1,2,3):
            raise ValueError('Bloom requires an RGB/RGBA image and integer scale 1, 2 or 3.')
        if len(origin) != 2 or not all(map(isfinite, origin)):
            raise ValueError('Bloom origin must be a finite pair.')
        if clip is not None and (len(clip) != 4 or any(type(value) is not int for value in clip)):
            raise ValueError('Bloom clip must contain four integer bounds.')
        if not emission:
            return background
        layers = self.bloom(key)
        if layers is None:
            return background
        # Crop the sparse emission before scaling; moving light must not process the whole tile.
        bounds = [layer.getbbox() for layer in layers if layer.getbbox() is not None]
        extent = (min(box[0] for box in bounds), min(box[1] for box in bounds),
                  max(box[2] for box in bounds), max(box[3] for box in bounds))
        x = round(origin[0]) + (extent[0]-BLOOM_RADIUS)*scale
        y = round(origin[1]) + (extent[1]-BLOOM_RADIUS)*scale
        width, height = (extent[2]-extent[0])*scale, (extent[3]-extent[1])*scale
        limits = clip if clip is not None else (0,0,*background.size)
        box = (max(0,x,limits[0]), max(0,y,limits[1]),
               min(background.width,x+width,limits[2]), min(background.height,y+height,limits[3]))
        if box[0] >= box[2] or box[1] >= box[3]:
            return background
        crop = box[0]-x, box[1]-y, box[2]-x, box[3]-y
        original = background.crop(box)
        channels = []
        for component, layer in zip('RGB', layers):
            layer = layer.crop(extent)
            if scale != 1:
                layer = layer.resize((width,height), Image.Resampling.NEAREST)
            glow = layer.crop(crop)
            old = original.getchannel(component)
            linear = old.point(list(SRGB), 'F')
            output = srgb(calc(lambda v: v['c']+.65*v['e'], c=linear, e=glow))
            # Keep additive light monotone despite the original shader's 12-bit gamma quantization.
            output = ImageChops.lighter(output, old)
            mask = calc(lambda v: (v['e'] > 0)*255, e=glow).convert('L')
            channels.append(Image.composite(output, old, mask))
        patch = Image.merge('RGB', channels)
        if background.mode == 'RGBA':
            patch.putalpha(original.getchannel('A'))
        result = background if in_place else background.copy()
        result.paste(patch, box[:2])
        return result
