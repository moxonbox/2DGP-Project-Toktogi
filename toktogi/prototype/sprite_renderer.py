"""Render 128px material sprites from any compatible five-pass map provider."""
from functools import lru_cache
import pygame as pg
from PIL import Image
from lighting import fields, shade

SIZE=128
SRGB=tuple(i/255/12.92 if i<=10 else ((i/255+.055)/1.055)**2.4 for i in range(256))


class SpriteRenderer:
    def __init__(self, maps, emission_scale, ink=None):
        self.maps=maps
        self.emission_scale=emission_scale
        self.ink=ink
        self.surface_fields=lru_cache(maxsize=24)(self.surface_fields)
        self.lit=lru_cache(maxsize=96)(self.lit)

    def close(self):
        self.lit.cache_clear()
        self.surface_fields.cache_clear()

    def render(self,key,mode,origin,light,roughness=None,metallic=None,power=1.,emission=True,*,ambient=.115):
        if mode=='lit':
            return self.lit(key,light[0]-origin[0],origin[1]-light[1],roughness,metallic,power,emission,ambient)
        maps=self.maps(key)
        if mode in ('base','sprite'):
            return maps[mode]
        coverage=pg.image.tobytes(maps['base'],'RGBA')[3::4]
        if mode=='outline':
            data=bytearray(pg.image.tobytes(maps['sprite'],'RGBA'))
            data[3::4]=bytes(0 if alpha else src for alpha,src in zip(coverage,data[3::4]))
        else:
            data=bytearray(pg.image.tobytes(maps[mode],'RGBA'))
            data[3::4]=coverage
        return pg.image.frombytes(bytes(data),(SIZE,SIZE),'RGBA')

    def surface_fields(self,key):
        images={name:Image.frombytes('RGBA',(SIZE,SIZE),pg.image.tobytes(image,'RGBA'))
                for name,image in self.maps(key).items()}
        return fields(images,self.ink(key) if self.ink else (),SRGB)

    def lit(self,key,lx,ly,roughness,metallic,power,emission,ambient):
        image=shade(self.surface_fields(key),lx,ly,roughness,metallic,power,emission,ambient,self.emission_scale)
        return pg.image.frombytes(image.tobytes(),(SIZE,SIZE),'RGBA')
