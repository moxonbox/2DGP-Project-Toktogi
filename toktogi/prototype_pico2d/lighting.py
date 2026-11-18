"""The existing sprite BRDF evaluated by Pillow's C image arithmetic."""
from PIL import Image,ImageChops,ImageMath
from array import array

X=Image.frombytes('F',(128,128),array('f',(x for y in range(128) for x in range(128))).tobytes())
Y=Image.frombytes('F',(128,128),array('f',(y for y in range(128) for x in range(128))).tobytes())


def calc(expression,**values):
    return ImageMath.lambda_eval(expression,**values)


def fields(images,ink,srgb_table,*,flat_normal=False):
    sprite=images['sprite'];base=images['base'].copy()
    for xy in ink:base.putpixel(xy,sprite.getpixel(xy))
    # Shade only covered pixels; keep their original coordinates for the light vector.
    box=base.getchannel('A').getbbox() or (0,0,1,1)
    base=base.crop(box)
    normal=[images['normal'].crop(box).getchannel(c).point([i*2/255-1 for i in range(256)],'F') for c in 'RGB']
    inv=calc(lambda v:(v['x']*v['x']+v['y']*v['y']+v['z']*v['z'])**-.5,x=normal[0],y=normal[1],z=normal[2])
    normal=[calc(lambda v:v['n']*v['u'],n=n,u=inv) for n in normal]
    if flat_normal:
        normal=[Image.new('F',base.size,value) for value in (0.,0.,1.)]
    albedo=[base.getchannel(c).point(list(srgb_table),'F') for c in 'RGB']
    rough=images['rm'].crop(box).getchannel('R').point([max(.10,i/255) for i in range(256)],'F')
    metal=images['rm'].crop(box).getchannel('G').point([i/255 for i in range(256)],'F')
    glow=[images['emissive'].crop(box).getchannel(c).point([i/255 for i in range(256)],'F') for c in 'RGB']
    mask=images['base'].getchannel('A').crop(box).point([0]+[255]*255)
    if sprite.size == (128,128):
        x,y=X.crop(box),Y.crop(box)
    else:
        w,h=base.size
        x=Image.frombytes('F',(w,h),array('f',(i+box[0] for _ in range(h) for i in range(w))).tobytes())
        y=Image.frombytes('F',(w,h),array('f',(j+box[1] for j in range(h) for _ in range(w))).tobytes())
    return sprite,mask,x,y,*normal,albedo,rough,metal,glow,box


def srgb(value):
    value=calc(lambda v:v['min'](v['max'](v['x'],0.),1.)*4095+.5,x=value).convert('I').convert('F')
    value=calc(lambda v:v['x']/4095.,x=value)
    return calc(lambda v:((v['x']<=.0031308)*v['x']*12.92+(v['x']>.0031308)*(1.055*(v['x']**(1/2.4))-.055))*255+.5,x=value).convert('L')


# Neutral reference and maximum tonal shift in 8-bit display space.
PALETTE_NEUTRAL = [round(.72 * value) for value in range(256)]
PALETTE_SHIFT = [128 + round(max(-32, min(32, .68 * (value - 128)))) for value in range(256)]
PALETTE_HIGHLIGHT_LIMIT = [128 + (255 - value) * 2 // 3 for value in range(256)]
PALETTE_SHADOW_LIMIT = [128 - value * 2 // 3 for value in range(256)]


def point_light(x,y,nx,ny,nz,lx,ly,power):
    dx=calc(lambda v:v['a']-v['x'],a=float(lx),x=x)
    dy=calc(lambda v:v['a']+v['y'],a=float(ly),y=y)
    d2=calc(lambda v:v['x']*v['x']+v['y']*v['y']+116.*116.,x=dx,y=dy)
    inv=calc(lambda v:v['d']**-.5,d=d2)
    a=calc(lambda v:v['x']*v['u'],x=dx,u=inv)
    c=calc(lambda v:v['y']*v['u'],y=dy,u=inv)
    d=calc(lambda v:116.*v['u'],u=inv)
    ndl=calc(lambda v:v['max'](v['nx']*v['a']+v['ny']*v['c']+v['nz']*v['d'],0.),nx=nx,ny=ny,nz=nz,a=a,c=c,d=d)
    attenuation=calc(lambda v:v['p']*1.32/(1.+v['d']/32000.),p=float(power),d=d2)
    return a,c,d,ndl,attenuation


def shade(fields,lx,ly,roughness,metallic,power,emission,ambient,emission_scale,*,palette_base=None):
    sprite,mask,x,y,nx,ny,nz,rgb,rough,metal,glow,box=fields
    a,c,d,ndl,attenuation=point_light(x,y,nx,ny,nz,lx,ly,power)
    hnorm=calc(lambda v:(2.+2.*v['d'])**-.5,d=d)
    ndh=calc(lambda v:v['min'](v['max']((v['nx']*v['a']+v['ny']*v['c']+v['nz']*(v['d']+1.))*v['h'],0.),1.),nx=nx,ny=ny,nz=nz,a=a,c=c,d=d,h=hnorm)
    if roughness is not None:rough=Image.new('F',mask.size,roughness)
    if metallic is not None:metal=Image.new('F',mask.size,metallic)
    gloss=calc(lambda v:2./(v['r']*v['r'])-2.,r=rough)
    specular=calc(lambda v:v['a']*v['n']*(v['g']+2.)/8.*(v['h']**v['g']),a=attenuation,n=ndl,g=gloss,h=ndh)
    fresnel=calc(lambda v:(1.-(1.+v['d'])*v['h'])**5.,d=d,h=hnorm)
    diffuse=calc(lambda v:v['ambient']+v['a']*v['n']*(1.-v['m'])*.88,ambient=float(ambient),a=attenuation,n=ndl,m=metal)
    dielectric=calc(lambda v:.04*(1.-v['m']),m=metal)
    channels=[]
    for albedo,emit in zip(rgb,glow):
        radiance=calc(lambda v:v['r']*v['df']+v['s']*(v['f']+(v['di']+v['r']*v['m'])*(1.-v['f']))+v['e']*v['es'],
                      r=albedo,df=diffuse,s=specular,f=fresnel,di=dielectric,m=metal,e=emit,es=float(emission_scale if emission else 0.))
        channels.append(srgb(radiance))
    original=sprite.crop(box)
    authored = original.convert('RGB')
    material = Image.merge('RGB', channels)
    color = material
    if palette_base is not None:
        # Apply the same signed light shift to all authored channels to retain the toon colors.
        neutral = palette_base.crop(box).convert('L').point(PALETTE_NEUTRAL)
        shift = ImageChops.subtract(color.convert('L'), neutral, offset=128).point(PALETTE_SHIFT)
        # Leave headroom at both ends so highlights retain their drawn detail and hue.
        r, g, b = authored.split()
        brightest = ImageChops.lighter(ImageChops.lighter(r, g), b)
        darkest = ImageChops.darker(ImageChops.darker(r, g), b)
        shift = ImageChops.darker(shift, brightest.point(PALETTE_HIGHLIGHT_LIMIT))
        shift = ImageChops.lighter(shift, darkest.point(PALETTE_SHADOW_LIMIT))
        color = ImageChops.add(authored, shift.convert('RGB'), offset=-128)
        # Below the preview's usual ambient level, let unlit material approach its actual radiance.
        if ambient < .115:
            visibility = calc(lambda v: v['min']((v['ambient'] + v['a'] * v['n']) / .115, 1.) * 255.,
                              ambient=float(ambient), a=attenuation, n=ndl).convert('L')
            color = Image.composite(color, material, visibility)
    color = Image.composite(color, authored, mask)
    color.putalpha(original.getchannel('A'))
    result=sprite.copy();result.paste(color,box[:2])
    return result
