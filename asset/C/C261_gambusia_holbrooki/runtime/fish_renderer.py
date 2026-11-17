"""C011 BRDF, cropped to fish coverage. Screen scaling remains Nearest."""
from collections import OrderedDict
import numpy as np
from PIL import Image
from motion_spec import VARIANTS

def linear(values):
    values=np.asarray(values,dtype=np.float32)/255
    return np.where(values<=.04045,values/12.92,((values+.055)/1.055)**2.4)

_GRID=np.arange(4096,dtype=np.float64)/4095
_SRGB=np.clip(np.floor(np.where(_GRID<=.0031308,_GRID*12.92,1.055*_GRID**(1/2.4)-.055)*255+.5),0,255).astype(np.uint8)
def srgb(values):
    return _SRGB[(np.clip(values,0,1)*4095+.5).astype(np.uint16)]

def prepare(maps,box=None):
    box=box or maps['sprite'].getbbox()
    data={k:np.array(v.crop(box)) for k,v in maps.items()}
    normal=data['normal'][...,:3].astype(np.float32)/127.5-1
    normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-8)
    y,x=np.mgrid[box[1]:box[3],box[0]:box[2]].astype(np.float32)
    mask=data['base'][...,3]>0
    depth=data['depth'];height=(depth[...,0].astype(np.float32)*256+depth[...,1])/65535*2-1
    return {'box':box,'data':data,'mask':mask,'indices':np.flatnonzero(mask),'height':height[mask],'x':x[mask],'y':y[mask],'normal':normal[mask],
            'albedo':linear(data['base'][mask,:3]),'rough':np.maximum(.1,data['orm'][mask,1]/255).astype(np.float32),
            'metal':data['orm'][mask,2].astype(np.float32)/255,'glow':data['emissive'][mask,:3].astype(np.float32)/255}

def shade(fields,lx,ly,*,power=.82,ambient=.34,emission=True,emission_scale=1.,flat=False,roughness=None,metallic=None):
    data=fields['data'];normal=fields['normal'] if not flat else np.broadcast_to(np.array([0.,0.,1.],np.float32),fields['normal'].shape)
    dx=lx-fields['x'];dy=ly+fields['y'];d2=dx*dx+dy*dy+116**2;inv=1/np.sqrt(d2)
    a=dx*inv;c=dy*inv;d=116*inv
    ndl=np.maximum(normal[...,0]*a+normal[...,1]*c+normal[...,2]*d,0)
    hnorm=1/np.sqrt(2+2*d)
    ndh=np.clip((normal[...,0]*a+normal[...,1]*c+normal[...,2]*(d+1))*hnorm,0,1)
    rough=fields['rough'] if roughness is None else max(.1,roughness)
    metal=fields['metal'] if metallic is None else metallic
    gloss=2/(rough*rough)-2;attenuation=power*1.32/(1+d2/32000)
    specular=attenuation*ndl*(gloss+2)/8*ndh**gloss
    fresnel=(1-(1+d)*hnorm)**5;diffuse=ambient+attenuation*ndl*(1-metal)*.88
    rgb=fields['albedo'];metal=np.asarray(metal)
    radiance=rgb*diffuse[...,None]+specular[...,None]*(fresnel[...,None]+(.04*(1-metal[...,None])+rgb*metal[...,None])*(1-fresnel[...,None]))
    if emission:radiance+=fields['glow']*emission_scale
    result=data['sprite'].copy();result.reshape(-1,4)[fields['indices'],:3]=srgb(radiance)
    return result

class FishRenderer:
    def __init__(self,bundle):
        self.bundle=bundle;self.cache=OrderedDict();self.rendered=OrderedDict()

    def fields(self,cell):
        key=(self.bundle.manifest['revision'],cell['file'])
        if key not in self.cache:
            self.cache[key]=prepare(self.bundle.maps(cell))
            while len(self.cache)>24:self.cache.popitem(last=False)
        self.cache.move_to_end(key);return self.cache[key]

    def render(self,cell,variant,*,light=None,root_z=None,surface=0.,mode='relit',flat=False,emission=True):
        key=(self.bundle.manifest['revision'],cell['file'],variant,tuple(light) if light else None,root_z,surface,mode,flat,emission)
        if key in self.rendered:
            self.rendered.move_to_end(key);return self.rendered[key]
        fields=self.fields(cell);data=fields['data'];box=fields['box']
        size=VARIANTS[variant]['cell']
        if mode=='relit':rgba=shade(fields,*(light or (size*.34,-size*.24)),flat=flat,emission=emission)
        elif mode in data:
            rgba=data[mode].copy()
            if mode not in ('sprite','base'):rgba[...,3]=data['base'][...,3]
        else:raise ValueError('unsupported display pass '+mode)
        if root_z is not None and mode in ('sprite','relit'):
            below=fields['indices'][fields['height']*VARIANTS[variant]['sl_bu']+root_z<surface]
            # Water tint is a separate composition, never baked into Base.
            pixels=rgba.reshape(-1,4)
            pixels[below,:3]=np.clip(pixels[below,:3]*np.array([.72,.88,.94],np.float32)+np.array([4,12,16],np.float32),0,255).astype(np.uint8)
        result=Image.fromarray(rgba),box[:2];self.rendered[key]=result
        while len(self.rendered)>24:self.rendered.popitem(last=False)
        return result

    def cache_bytes(self):
        return sum(value.nbytes for fields in self.cache.values() for value in fields.values() if isinstance(value,np.ndarray))+sum(value.nbytes for fields in self.cache.values() for value in fields['data'].values())+sum(pic.width*pic.height*4 for pic,_ in self.rendered.values())
