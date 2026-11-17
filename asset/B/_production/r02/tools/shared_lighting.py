"""The existing sprite BRDF evaluated by Pillow's C image arithmetic."""
from PIL import Image,ImageMath
from array import array



def calc(expression,**values):
    return ImageMath.lambda_eval(expression,**values)


def fields(images,ink,srgb_table):
    sprite=images['sprite'];base=images['base'].copy()
    width,height=sprite.size
    X=Image.frombytes('F',sprite.size,array('f',(x for y in range(height) for x in range(width))).tobytes())
    Y=Image.frombytes('F',sprite.size,array('f',(y for y in range(height) for x in range(width))).tobytes())
    for xy in ink:base.putpixel(xy,sprite.getpixel(xy))
    normal=[images['normal'].getchannel(c).point([i*2/255-1 for i in range(256)],'F') for c in 'RGB']
    inv=calc(lambda v:(v['x']*v['x']+v['y']*v['y']+v['z']*v['z'])**-.5,x=normal[0],y=normal[1],z=normal[2])
    normal=[calc(lambda v:v['n']*v['u'],n=n,u=inv) for n in normal]
    albedo=[base.getchannel(c).point(list(srgb_table),'F') for c in 'RGB']
    rough=images['rm'].getchannel('R').point([max(.10,i/255) for i in range(256)],'F')
    metal=images['rm'].getchannel('G').point([i/255 for i in range(256)],'F')
    glow=[images['emissive'].getchannel(c).point([i/255 for i in range(256)],'F') for c in 'RGB']
    mask=images['base'].getchannel('A').point([0]+[255]*255)
    return sprite,mask,X,Y,*normal,albedo,rough,metal,glow


def srgb(value):
    value=calc(lambda v:v['min'](v['max'](v['x'],0.),1.)*4095+.5,x=value).convert('I').convert('F')
    value=calc(lambda v:v['x']/4095.,x=value)
    return calc(lambda v:((v['x']<=.0031308)*v['x']*12.92+(v['x']>.0031308)*(1.055*(v['x']**(1/2.4))-.055))*255+.5,x=value).convert('L')


def shade(fields,lx,ly,roughness,metallic,power,emission,ambient,emission_scale):
    sprite,mask,x,y,nx,ny,nz,rgb,rough,metal,glow=fields
    dx=calc(lambda v:v['a']-v['x'],a=float(lx),x=x)
    dy=calc(lambda v:v['a']+v['y'],a=float(ly),y=y)
    d2=calc(lambda v:v['x']*v['x']+v['y']*v['y']+116.*116.,x=dx,y=dy)
    inv=calc(lambda v:v['d']**-.5,d=d2)
    a=calc(lambda v:v['x']*v['u'],x=dx,u=inv)
    c=calc(lambda v:v['y']*v['u'],y=dy,u=inv)
    d=calc(lambda v:116.*v['u'],u=inv)
    ndl=calc(lambda v:v['max'](v['nx']*v['a']+v['ny']*v['c']+v['nz']*v['d'],0.),nx=nx,ny=ny,nz=nz,a=a,c=c,d=d)
    hnorm=calc(lambda v:(2.+2.*v['d'])**-.5,d=d)
    ndh=calc(lambda v:v['min'](v['max']((v['nx']*v['a']+v['ny']*v['c']+v['nz']*(v['d']+1.))*v['h'],0.),1.),nx=nx,ny=ny,nz=nz,a=a,c=c,d=d,h=hnorm)
    if roughness is not None:rough=Image.new('F',mask.size,roughness)
    if metallic is not None:metal=Image.new('F',mask.size,metallic)
    gloss=calc(lambda v:2./(v['r']*v['r'])-2.,r=rough)
    attenuation=calc(lambda v:v['p']*1.32/(1.+v['d']/32000.),p=float(power),d=d2)
    specular=calc(lambda v:v['a']*v['n']*(v['g']+2.)/8.*(v['h']**v['g']),a=attenuation,n=ndl,g=gloss,h=ndh)
    fresnel=calc(lambda v:(1.-(1.+v['d'])*v['h'])**5.,d=d,h=hnorm)
    diffuse=calc(lambda v:v['ambient']+v['a']*v['n']*(1.-v['m'])*.88,ambient=float(ambient),a=attenuation,n=ndl,m=metal)
    dielectric=calc(lambda v:.04*(1.-v['m']),m=metal)
    channels=[]
    for albedo,emit in zip(rgb,glow):
        radiance=calc(lambda v:v['r']*v['df']+v['s']*(v['f']+(v['di']+v['r']*v['m'])*(1.-v['f']))+v['e']*v['es'],
                      r=albedo,df=diffuse,s=specular,f=fresnel,di=dielectric,m=metal,e=emit,es=float(emission_scale if emission else 0.))
        channels.append(srgb(radiance))
    color=Image.composite(Image.merge('RGB',channels),sprite.convert('RGB'),mask)
    color.putalpha(sprite.getchannel('A'))
    return color
