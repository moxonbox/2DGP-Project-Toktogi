"""Build static B backgrounds in a separate Blender process, from reviewed sheets."""
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from png_codec import png, srgb_to_linear

CONFIG = json.loads((ROOT / '_production/r02/assets.json').read_text(encoding='utf-8'))
COLORS = ['8cac62', 'a5bf79', '637b4a', 'ad9d79', '865777', 'bdce94', 'e3b5c4',
          'f3ddbc', '837464', '625548', '9b9b8b', '54493d', '8c9052', 'bd994f', '8b773e']
ROLES = ['leaf', 'vein', 'stem', 'root', 'underside', 'hair', 'flower', 'pollen',
         'silt', 'stratum', 'gravel', 'detritus', 'film', 'diatom', 'striation']


def mesh(name, vertices, faces, uv, role=0, wrap_u=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    item = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(item)
    item.parent = VISUAL
    for material in MATERIALS:
        data.materials.append(material)
    layer = data.uv_layers.new(name='SurfaceUV')
    for face in data.polygons:
        face.material_index = role
        face.use_smooth = True
        seam=wrap_u and len(face.vertices)==4 and len({uv[i][1] for i in face.vertices})>1 and max(uv[i][0] for i in face.vertices)-min(uv[i][0] for i in face.vertices)>.5
        for loop in face.loop_indices:
            u, v = uv[data.loops[loop].vertex_index]
            if seam and u<.5:u+=1
            layer.data[loop].uv = ((role % 4 + .04 + .92*u)/4, (role//4 + .04 + .92*v)/4)
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    assert all(0<=c<=1 for value in data.uv_layers.active.data for c in value.uv),(name,'UV outside texture')
    return item


def ball(name, center, size, role=0, lower_role=None, asymmetry=0):
    primary=name=='frond' or name.startswith('floating_leaf_')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32 if primary else 12, ring_count=16 if primary else 6, radius=1)
    item = bpy.context.object
    item.name = name
    item.parent = VISUAL
    for material in MATERIALS:
        item.data.materials.append(material)
    for vertex in item.data.vertices:
        x, y, z = vertex.co
        vertex.co = (center[0]+x*size[0]/2,
                     center[1]+y*size[1]/2*(1+asymmetry*x), center[2]+z*size[2]/2)
    for face in item.data.polygons:
        face.use_smooth = True
        mean_z = sum(item.data.vertices[i].co.z for i in face.vertices)/len(face.vertices)
        index = lower_role if lower_role is not None and mean_z < center[2] else role
        face.material_index = index
        for loop in face.loop_indices:
            uv = item.data.uv_layers.active.data[loop].uv.copy()
            item.data.uv_layers.active.data[loop].uv = ((index%4+.04+.92*uv.x)/4, (index//4+.04+.92*uv.y)/4)
    return item


def tube(name, points, radius, role=2, sides=8, taper=.35):
    points = [Vector(p) for p in points]
    vertices, uv, faces = [], [], []
    for i, point in enumerate(points):
        tangent = points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        rotation = tangent.to_track_quat('Z','Y')
        r = radius[i] if isinstance(radius,list) else radius*(1-(1-taper)*i/(len(points)-1))
        for j in range(sides):
            a = j*math.tau/sides
            vertices.append(point+rotation@Vector((r*math.cos(a),r*math.sin(a),0)))
            uv.append((j/sides, i/(len(points)-1)))
    for i in range(len(points)-1):
        for j in range(sides):
            k, n = i*sides+j, i*sides+(j+1)%sides
            faces.append((k,n,n+sides,k+sides))
    faces += [tuple(range(sides-1,-1,-1)), tuple(range((len(points)-1)*sides,len(points)*sides))]
    return mesh(name,vertices,faces,uv,role,wrap_u=True)


def blade(name,start,tip,width,role=0,arch=.2,arrow=False):
    start,tip=Vector(start),Vector(tip);direction=tip-start
    side=Vector((-direction.y,direction.x,0))
    if side.length<.001:side=Vector((1,0,0))
    side.normalize();vertices=[];uv=[];faces=[];steps=16;sides=8
    for i in range(steps+1):
        t=i/steps
        center=start+direction*t+Vector((0,0,arch*math.sin(math.pi*t)))
        profile=np.interp(t,[0,.12,.25,.65,1],[.40,1,.78,.48,.001]) if arrow else math.sin(math.pi*t)**.75
        w=max(.002,width*profile/2);thick=max(.002,width*.065*math.sin(math.pi*t))
        for j in range(sides):
            a=j*math.tau/sides;offset=side*(w*math.cos(a))+Vector((0,0,thick*math.sin(a)))
            if arrow:offset+=direction*(.10*(1-abs(math.cos(a)))*max(0,1-t/.2))
            vertices.append(center+offset);uv.append((t,j/sides))
    for i in range(steps):
        for j in range(sides):
            k,n=i*sides+j,i*sides+(j+1)%sides;faces.append((k,n,n+sides,k+sides))
    faces += [tuple(range(sides-1,-1,-1)),tuple(range(steps*sides,(steps+1)*sides))]
    item=mesh(name,vertices,faces,uv,role)
    item['tip_bu']=list(tip)
    return item


def patch(name,length,depth,role,relief=0):
    n=64;vertices=[(0,0,relief*.8)];uv=[(.5,.5)];faces=[]
    rings=[(.25,None),(.50,None),(.75,None),(1,None),(1,-depth*.48),(.985,-depth)]
    for radius,fixed_z in rings:
        for i in range(n):
            a=i*math.tau/n;r=radius*(1+.052*math.sin(5*a)+.028*math.cos(9*a)+.018*math.sin(13*a))
            x=length/2*r*math.cos(a);y=length*.34*r*math.sin(a)
            z=fixed_z if fixed_z is not None else relief*(.65+.22*math.sin(x*2)+.20*math.cos(y*4)+.12*math.sin(a*3)*radius)
            vertices.append((x,y,z));uv.append((.5+.43*r*math.cos(a),.5+.43*r*math.sin(a)))
    for i in range(n):faces.append((0,1+i,1+(i+1)%n))
    for ring in range(len(rings)-1):
        for i in range(n):
            a=1+ring*n+i;b=1+ring*n+(i+1)%n;faces.append((a,a+n,b+n,b))
    bottom=len(vertices);vertices.append((0,0,-depth));uv.append((.5,.5))
    for i in range(n):faces.append((bottom,1+(len(rings)-1)*n+(i+1)%n,1+(len(rings)-1)*n+i))
    item=mesh(name,vertices,faces,uv,role)
    if role==8:
        for face in item.data.polygons:
            if sum(item.data.vertices[i].co.z for i in face.vertices)/len(face.vertices)<-depth*.3:
                face.material_index=9
                for loop in face.loop_indices:item.data.uv_layers.active.data[loop].uv.x+=.25
    return item


def smooth_path(points, steps=4):
    points=[Vector(p) for p in points];out=[]
    for i in range(len(points)-1):
        a,b,c,d=points[max(0,i-1)],points[i],points[i+1],points[min(i+2,len(points)-1)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out+[points[-1]]


def frond(name,center,length,width,thickness,lower=2,asymmetry=.08,cup=0):
    item=ball(name,center,(length,width,thickness),0,lower,asymmetry)
    for v in item.data.vertices:
        x=(v.co.x-center[0])/(length/2);y=(v.co.y-center[1])/(width/2)
        v.co.z+=cup*length*(y*y+.18*x*x)+.012*length*math.sin(x*3)*y
    item.data.update();bpy.context.view_layer.update()
    return item


def surface_vein(name,leaf,xy,radius,role=1):
    radius=max(.014,radius)
    points=[]
    for x,y in xy:
        hit,location,normal,index=leaf.ray_cast(Vector((x,y,100)),Vector((0,0,-1)))
        assert hit,(name,x,y,'vein must stay on its leaf')
        points.append(location+normal*(radius*.45))
    return tube(name,points,radius,role,6,.75)


def geometry(code,L):
    if code in ('B01','B02','B03'):
        width={'B01':L*1.6/2.5,'B02':L*5/6,'B03':L*.7}[code]
        thick=L*(.44 if code=='B03' else .16 if code=='B01' else .13)
        leaf=frond('frond',(0,0,thick*.12),L,width,thick,4 if code=='B02' else 2,.12,.022 if code!='B03' else 0)
        if code=='B03':
            for v in leaf.data.vertices:
                z=v.co.z/(thick*.62)
                if z>.5:v.co.z-=thick*.10*(z-.5)**2
            leaf.data.update()
        else:
            count=7 if code=='B02' else 3
            for j in range(count):
                a=(j-(count-1)/2)*.28
                xy=[(-.36*L+.70*L*t,width*.42*math.sin(a)*math.sin(t*math.pi/2)) for t in np.linspace(0,1,18)]
                surface_vein(f'vein_{j+1:02}',leaf,xy,max(.006,L*.0032))
            count=7 if code=='B02' else 1
            root_length=35*.965396 if code=='B02' else .90
            for j in range(count):
                x=(j-(count-1)/2)*L*.068;y=.04*L*math.sin(j)
                points=[(x+L*.032*math.sin(t*math.tau+j)*math.sin(t*math.pi),
                         y+L*.025*math.sin(t*5+j)*t,-root_length*t) for t in np.linspace(0,1,23)]
                tube(f'root_{j+1:02}',points,.047 if code=='B02' else .032,3,8,.25)
                ball(f'root_cap_{j+1:02}',points[-1],(.025,.025,.055) if code=='B02' else (.018,.018,.032),3)
            if code=='B01':
                for s in (-1,1):ball('root_sheath_wing_'+str(s),(s*.058,0,-.055),(.16,.11,.08),3)
    elif code=='B04':
        for s in (-1,1):
            cx=s*L*.49
            leaf=frond('floating_leaf_'+('L' if s<0 else 'R'),(cx,0,L*.03),L,L*.6,L*.14,2,.05,.035)
            surface_vein(f'midrib_{s}',leaf,[(cx-L*.39+t*L*.78,0) for t in np.linspace(0,1,20)],L*.003)
            for j in range(5):
                for side in (-1,1):
                    x=cx+L*(-.28+j*.13)
                    xy=[(x+L*.09*t,side*L*.20*t) for t in np.linspace(0,1,10)]
                    surface_vein(f'vein_{s}_{j}_{side}',leaf,xy,L*.002)
            for i in range(4):
                for j in (-1,1):
                    x=cx+(i-1.5)*L*.17;y=j*L*.15
                    hit,p,normal,_=leaf.ray_cast(Vector((x,y,100)),Vector((0,0,-1)))
                    assert hit
                    for k in range(3):
                        a=k*math.tau/3+i*.4
                        points=[p,p+Vector((.012*L*math.cos(a),.012*L*math.sin(a),L*.025)),
                                p+Vector((.024*L*math.cos(a),.024*L*math.sin(a),L*.017))]
                        tube(f'hair_tuft_{s}_{i}_{j}_{k}',smooth_path(points,2),L*.003,5,5,.4)
        tube('joining_stem',smooth_path([(-L*.16,0,0),(0,0,-L*.055),(L*.16,0,0)]),L*.027,2)
        tube('submerged_leaf_mid',[(.018*L*math.sin(t*4),0,-L*.65*t) for t in np.linspace(0,1,12)],L*.018,2)
        for i in range(6):
            for j in range(3):
                a=j*math.tau/3+i*.4;z=-L*(.12+i*.075);r=L*(.28-i*.035)
                start=Vector((0,0,z));end=start+Vector((r*math.cos(a),r*math.sin(a),-.14*L))
                middle=start+(end-start)*.65+Vector((0,0,L*.035))
                tube(f'submerged_leaf_branch_{i}_{j}',smooth_path([start,middle,end]),L*.010,2,6,.25)
                for k in (-1,1):
                    fork=middle+Vector((r*.4*math.cos(a+k*.35),r*.4*math.sin(a+k*.35),-L*.11))
                    tube(f'submerged_leaf_fork_{i}_{j}_{k}',smooth_path([middle,(middle+fork)/2+Vector((0,0,L*.02)),fork]),L*.007,0,6,.25)
    elif code=='B05':
        stem=[(.07*math.sin(t*3),.035*math.sin(t*4),L*t) for t in np.linspace(0,1,16)]
        tube('rootless_stem',stem,L*.020,2,8,.55)
        for n in range(4):
            z=L*(.15+n*.22);center=Vector((.07*math.sin(z/L*3),.035*math.sin(z/L*4),z))
            ball(f'whorl_joint_{n}',center,(L*.056,L*.056,L*.047),2)
            for j in range(6):
                a=j*math.tau/6+n*.28;out=Vector((math.cos(a),math.sin(a),.30+.12*math.sin(j)))
                fork=center+out*(L*.15)
                tube(f'whorl_{n+1}_leaf_{j+1}',smooth_path([center,center+out*L*.07+Vector((0,0,.015*L)),fork]),L*.015,0,6,.7)
                for s in (-1,1):
                    side=Vector((-math.sin(a),math.cos(a),.15))*s;end=fork+out*(L*.12)+side*(L*.055)
                    tube(f'fork1_{n}_{j}_{s}',smooth_path([fork,(fork+end)/2+Vector((0,0,.02*L)),end]),L*.011,0,6,.6)
                    for k in (-1,1):
                        tip=end+out*(L*.09)+side*(k*L*.038)
                        tube(f'fork2_{n}_{j}_{s}_{k}',smooth_path([end,(end+tip)/2+Vector((0,0,.02*L)),tip],2),L*.008,0,6,.25)
    elif code=='B06':
        tube('vertical_stem',[(L*.008*math.sin(t*2),0,L*t) for t in np.linspace(0,1,13)],L*.014,2,10,.65)
        z=[.735,.743,.76,.91,.927,.933]
        tube('cylindrical_inflorescence',[(L*.008,0,L*t) for t in z],[L*r for r in (.012,.032,.043,.043,.031,.012)],11,16)
        for j in range(6):
            a=j*math.tau/6+.3;r=L*(.20+.028*(j%3));z=L*(.48+.075*(j%3))
            start=(.008*L*math.cos(a),.008*L*math.sin(a),0)
            tip=(r*math.cos(a),r*math.sin(a),z)
            blade(f'strap_leaf_{j+1}',start,tip,L*.060,0,L*.30)
            tube(f'leaf_sheath_{j}',smooth_path([start,(start[0]*1.5,start[1]*1.5,L*.07),(r*.12*math.cos(a),r*.12*math.sin(a),L*.18)]),L*.008,2,6,.4)
    elif code=='B07':
        tube('jointed_cane',[(L*.025*math.sin(t*2),0,L*t) for t in np.linspace(0,1,15)],L*.011,2,8,.5)
        for j in range(7):
            z=L*(.12+j*.09);a=(j%2)*math.pi+.25*math.sin(j)
            base=(L*.025*math.sin(z/L*2),0,z)
            tube(f'node_collar_{j}',[(base[0],0,z-L*.006),(base[0],0,z+L*.006)],L*.014,1,10,1)
            blade(f'lance_leaf_{j+1}',base,(base[0]+math.cos(a)*L*(.23-.008*j),math.sin(a)*L*.23,z+L*.07),L*.054,0,L*.10)
        for n in range(5):
            z=L*(.72+n*.052);r=L*(.135-n*.023)
            for j in range(5):
                a=j*math.tau/5+n*.6;start=Vector((.025*L,0,z));out=Vector((math.cos(a),math.sin(a),.40))
                end=start+out*r;mid=(start+end)/2+Vector((0,0,.02*L))
                tube(f'panicle_branch_{n}_{j}',smooth_path([start,mid,end],2),L*.0035,3,6,.3)
                for t in (.35,.60,.85):
                    p=start+(end-start)*t+Vector((0,0,.012*L))
                    for s in (-1,1):
                        tip=p+Vector((math.cos(a+s*.6),math.sin(a+s*.6),1.3))*L*(.025+.01*(1-t))
                        tube(f'panicle_spikelet_{n}_{j}_{t}_{s}',smooth_path([p,(p+tip)/2+Vector((0,0,.008*L)),tip],2),L*.004,3,5,.12)
    elif code=='B08':
        points=[(-L/2+i*L/6,.08*L*math.sin(i*2),L*(.1+.035*(i%2))) for i in range(7)]
        tube('angular_stem',points,L*.011,11,4,.8)
        for i,p in enumerate(points[1:-1]):
            s=(-1)**i;tip=(p[0]+L*.08,p[1]+s*L*.20,p[2]+L*.08)
            leaf=blade(f'arrow_leaf_{i}',p,tip,L*.13,0,L*.04,arrow=True)
            tube(f'ochrea_node_{i}',[(p[0]-.012*L,p[1],p[2]),(p[0]+.012*L,p[1],p[2])],L*.017,3,8,.85)
            tube(f'downward_prickle_{i}',[p,(p[0]-.018*L,p[1],p[2]-.042*L)],L*.008,11,5,.12)
        for k,p in enumerate((points[0],points[-1])):
            top=Vector(p)+Vector(((-1)**k*.025*L,0,.14*L))
            tube(f'flower_peduncle_{k}',smooth_path([p,(Vector(p)+top)/2+Vector((.01*L,.01*L,0)),top]),L*.007,2)
            for j in range(7):
                a=j*2.39996;r=L*.042*math.sqrt(j/7)
                center=top+Vector((r*math.cos(a),r*math.sin(a),L*.018*math.sqrt(1-j/8)))
                ball(f'flower_calyx_{k}_{j}',center-Vector((0,0,L*.008)),(L*.024,L*.024,L*.023),2)
                for petal in range(5):
                    b=petal*math.tau/5+a;pos=center+Vector((math.cos(b)*L*.011,math.sin(b)*L*.011,L*.003))
                    ball(f'flower_{k}_{j}_{petal}',pos,(L*.024,L*.020,L*.022),6 if (j+petal)%3 else 7)
                ball(f'pollen_{k}_{j}',center+Vector((0,0,L*.010)),(L*.010,)*3,7)
    elif code=='B09':
        patch('sediment_floor',L,L*.07,8,relief=.018*L)
        for i,(x,y,s) in enumerate(((-.27,-.10,.13),(.20,.14,.10),(-.13,.22,.075),(.28,-.18,.12),(.02,-.12,.055),(-.33,.13,.05))):
            item=ball(f'gravel_{i+1}',(x*L,y*L,s*L*.23+.02*L),(s*L,s*L*.8,s*L*.67),10)
            for v in item.data.vertices:v.co.x+=.025*s*L*math.sin(v.co.y*20+i);v.co.z+=.018*s*L*math.sin(v.co.x*30)
            item.data.update()
        for i in range(3):
            tube(f'detritus_{i}',smooth_path([(-.18*L+i*.17*L,.02*L,.04*L),(-.14*L+i*.17*L,.05*L,.035*L),(-.10*L+i*.17*L,.09*L,.03*L)]),L*.012,11,6,.5)
        for i in range(14):
            x=.37*L*math.sin(i*2.4);y=.24*L*math.cos(i*1.75)
            ball(f'fine_grain_{i}',(x,y,.020*L),(.018*L,.013*L,.012*L),8 if i%3 else 10)
    elif code=='B0A':
        patch('attached_film',L,.009,12,relief=.006)
        for i in range(7):
            x=L*.31*math.sin(i*2.4);y=L*.20*math.cos(i*1.8)
            ball(f'film_colony_{i}',(x,y,.006),(L*(.07+.02*(i%3)),L*.048,.012),12)
    elif code=='B0B':
        patch('microscopy_substrate_patch',L,.009,12,relief=.004)
        for i in range(8):
            x=L*.33*math.sin(i*2.4);y=L*.22*math.cos(i*1.8);a=i*.8
            length=L*(.12+.025*(i%3));width=length*(.38 if i%3 else .68)
            item=ball(f'illustrative_shell_{i}',(0,0,.028),(length,width,.045),13)
            item.rotation_euler.z=a;item.location=(x,y,0)
            rim=[(length*.46*math.cos(t),width*.46*math.sin(t),.044) for t in np.linspace(0,math.tau,33)]
            ring=tube(f'illustrative_rim_{i}',rim,.006,13,5,1);ring.rotation_euler.z=a;ring.location=(x,y,0)
            for j in range(7):
                px=(j-3)*length*.102;w=width*.36*math.sqrt(max(0,1-(px/(length*.46))**2))
                line=tube(f'illustrative_striation_{i}_{j}',[(px,-w,.047),(px,0,.053),(px,w,.047)],.0035,14,5,.8)
                line.rotation_euler.z=a;line.location=(x,y,0)


def build(config):
    global VISUAL,MATERIALS
    assert bpy.app.background, 'Run in a separate background Blender process.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    code=config['id'];directory=ROOT/config['folder']
    for relative in ('3D/textures','2D','sheet','document'):
        (directory/relative).mkdir(parents=True,exist_ok=True)
    sheet=directory/'sheet'/f'{config["name"]}_sheet_r01.png'
    source=Path(config.get('generated_source',str(sheet)))
    if source.exists() and not sheet.exists():shutil.copy2(source,sheet)
    assert sheet.exists(),sheet
    length=config['details'].get('design_length_bu') or .965396*config['selected_length_mm']*config['presentation_factor']
    scene=bpy.context.scene;scene.name=code+'_background_r02'
    scene.unit_settings.system='NONE'
    physics=bpy.data.objects.new('physics_root',None);scene.collection.objects.link(physics)
    VISUAL=bpy.data.objects.new('visual_root',None);scene.collection.objects.link(VISUAL);VISUAL.parent=physics
    colors=COLORS.copy()
    greens={'B01':'93b56b','B02':'7eaa65','B03':'8db568','B04':'94ad63','B05':'568366','B06':'789764','B07':'84a568','B08':'6c965f'}
    colors[0]=greens.get(code,colors[0])
    tex=np.zeros((512,512,4),np.uint8);tex[:,:,3]=255
    for i,h in enumerate(colors):
        yy,xx=np.mgrid[:128,:128]
        broad=np.sin(xx/21+i)*np.cos(yy/25-i)+.35*np.sin((xx+yy)/16)
        spots=np.maximum(0,np.sin(xx/8+i)*np.cos(yy/11)-.60)
        variation=1+.055*broad-.10*spots
        if i in (2,3,11):variation+=.035*np.sin(xx*.8)*np.sin(yy/25)
        if i==0 and code in ('B06','B07'):variation+=.055*np.cos(yy/128*math.tau*3)
        rgb=np.array(list(bytes.fromhex(h)))*variation[:,:,None]
        if i==12:
            mix=np.clip(.4+.32*broad,0,1)[:,:,None]
            rgb=np.array([110,124,69])*(1-mix)+np.array([149,133,87])*mix
        tile=tex[i//4*128:(i//4+1)*128,i%4*128:(i%4+1)*128]
        tile[:,:,:3]=np.clip(rgb,0,255)
        if i==12:tile[:,:,3]=np.rint(np.clip(.80+.16*broad,.48,1)*255).astype(np.uint8)
    texture_path=directory/'3D/textures'/f'{config["name"]}_basecolor_r02.png'
    png(texture_path,np.flipud(tex),True)
    image=bpy.data.images.load(str(texture_path));image.name='Background_BaseColor_r02';image.pack();image.filepath='//textures/'+texture_path.name
    MATERIALS=[]
    for i,role in enumerate(ROLES):
        material=bpy.data.materials.new(role);material.use_nodes=True
        opacity=178/255 if code=='B0A' else 216/255 if code=='B0B' else 1.
        material.diffuse_color=(*srgb_to_linear(np.array(list(bytes.fromhex(colors[i])))/255),opacity)
        shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.78 if i<12 else .62
        shader.inputs['Alpha'].default_value=opacity
        node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.interpolation='Linear'
        material.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
        if code in ('B0A','B0B'):
            multiply=material.node_tree.nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=opacity
            material.node_tree.links.new(node.outputs['Alpha'],multiply.inputs[0]);material.node_tree.links.new(multiply.outputs[0],shader.inputs['Alpha'])
        material['roughness']=.78 if i<12 else .62
        MATERIALS.append(material)
    geometry(code,length)
    anchors={'origin':[0,0,0]}
    labels={'B01':['frond_center','root_base'],'B02':['upper_frond','root_bundle'],
            'B03':['frond_center'],'B04':['floating_pair','submerged_frond'],
            'B05':['stem_mid'],'B06':['root_base'],'B07':['base','panicle_tip'],
            'B08':[],'B09':['floor_surface','turbidity_origin'],'B0A':['substrate_uv'],
            'B0B':['substrate_uv','microscope_focus']}
    for label in labels[code]:anchors[label]=[0,0,0]
    if code=='B02':anchors['upper_frond']=[0,0,length*.065]
    if code=='B04':anchors['submerged_frond']=[0,0,-length*.1]
    if code=='B05':
        anchors['stem_mid']=[.04,0,length/2]
        for i in range(4):anchors[f'whorl_node_{i+1}']=[0,0,length*(.15+i*.22)]
    if code=='B06':
        for item in bpy.context.scene.objects:
            if item.name.startswith('strap_leaf_'):
                anchors['tip_'+item.name]=list(item['tip_bu'])
    if code=='B07':anchors['panicle_tip']=[length*.02,0,length]
    if code=='B08':
        for i in range(7):anchors[f'stem_node_{i}']=[-length/2+i*length/6,.08*length*math.sin(i*2),length*(.1+.035*(i%2))]
        for i in (0,6):anchors[f'flower_tip_{i}']=[*anchors[f'stem_node_{i}'][:2],length*.235]
    for label,point in anchors.items():
        anchor=bpy.data.objects.new('anchor_'+label,None);scene.collection.objects.link(anchor)
        anchor.parent=VISUAL;anchor.location=point;anchor.empty_display_size=.035
    reference=bpy.data.objects.new('REFERENCE_SHEET_not_geometry',None);scene.collection.objects.link(reference)
    reference.empty_display_type='IMAGE';reference.data=bpy.data.images.load(str(sheet));reference.data.pack()
    reference.data.filepath='//../sheet/'+sheet.name;reference.hide_render=True;reference.hide_viewport=True
    reference['role']='Reviewed concept; dimensions and organ counts come from production contract.'
    camera=bpy.data.objects.new('Camera_C011',bpy.data.cameras.new('Camera_C011'));scene.collection.objects.link(camera)
    camera.data.type='ORTHO';camera.rotation_euler=(1.195510983467102,0,-.5700404644012451)
    camera.location=camera.rotation_euler.to_quaternion()@Vector((0,0,60));camera.data.ortho_scale=max(length*2,4)
    scene.camera=camera;scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.world=bpy.data.worlds.new('Shared_Neutral_World');scene.world.color=(.34,.34,.34)
    light=bpy.data.objects.new('Reference_Key',bpy.data.lights.new('Reference_Key','AREA'));scene.collection.objects.link(light)
    light.location=(-5,-7,10);light.data.energy=700;light.data.shape='DISK';light.data.size=8
    light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    objects=[o for o in scene.objects if o.type=='MESH'];points=np.array([tuple(o.matrix_world@v.co) for o in objects for v in o.data.vertices])
    triangles=0
    for item in objects:
        item.data.calc_loop_triangles();triangles+=len(item.data.loop_triangles)
        assert item.data.uv_layers.active and all(math.isfinite(c) for v in item.data.vertices for c in v.co)
    assert triangles<20000,(code,triangles)
    roots=[o.name for o in objects if o.name.startswith('root_') and o.name[5:].isdigit()]
    assert len(roots)==({'B01':1,'B02':7}.get(code,0)),(code,roots)
    manifest={**{k:v for k,v in config.items() if k not in ('generated_source','prompt')},'schema':1,
              'length_bu':length,'bounds_bu':[points.min(0).tolist(),points.max(0).tolist()],'anchors_bu':anchors,
              'triangles':triangles,'mesh_count':len(objects),'bone_count':0,'root_count':len(roots),
              'axis':'+X leaf/stem extent, +Z up','texture':'textures/'+texture_path.name,
              'texture_size':[512,512],'sheet':'../sheet/'+sheet.name,'blender':bpy.app.version_string,
              'sheet_sha256':hashlib.sha256(sheet.read_bytes()).hexdigest(),'static':True,
              'collision':None,'interactive':False,'animation_status':'not_applicable_static_B',
              'reference_size_mm':1.0,'bu_per_reference_body':.965396,'bu_per_pixel':1.78/128,
              'palette_roles':dict(zip(ROLES,colors)),'uv_policy':'16 padded tiles; intentional reuse per material; fixed broad mottling and role detail; tube seam preserved',
              'source_document_status':'Original biological unknowns remain null; production dimensions are design choices.'}
    text=bpy.data.texts.new('ASSET_MANIFEST.json');text.write(json.dumps(manifest,ensure_ascii=False,indent=2))
    scene['asset_id']=config['name'];scene['revision']='background-r02'
    scene['runtime_note']='Static B background; no player collision, buoyancy or gameplay events.'
    for item in bpy.context.selected_objects:item.select_set(False)
    VISUAL.select_set(True);bpy.context.view_layer.objects.active=VISUAL
    path=directory/'3D'/f'{config["name"]}_r02.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    (directory/'3D/model_manifest_r02.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'id':code,'triangles':triangles,'meshes':len(objects),'blend':str(path)}


if __name__=='__main__':
    selected=globals().get('ONLY',sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    result=[build(c) for c in CONFIG if not selected or c['id'] in selected]
    print(json.dumps(result),flush=True)
