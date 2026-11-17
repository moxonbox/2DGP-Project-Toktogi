"""Build the seven static habitat candidates in an isolated Blender process.

Reuses C011 PNG/color/outline helpers. Never run in a user's editable scene.
"""
import hashlib
import json
import math
import struct
import zlib
from fractions import Fraction
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
exec((HERE / 'SPRITE_PNG.py').read_text(encoding='utf-8'))
ASSETS = json.loads((HERE / 'assets.json').read_text(encoding='utf-8'))
U = .965396
PIXEL = 1.78 / 128
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
SHADES = np.array([[.36,.42,.51],[.53,.60,.66],[.73,.77,.80],[.95,.95,.92]])
CAM_ROT = Euler((1.195510983467102, 4.938385700370418e-9, -.5700404644012451))
GAME_VIEWS = json.loads((HERE/'reference/C011_views.json').read_text(encoding='utf-8'))
textures = {}


def material(name, hexcolor, roughness=.7, pattern=None, wetline=None):
    rgb = np.array(list(bytes.fromhex(hexcolor.lstrip('#')))) / 255
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*srgb_to_linear(rgb), 1)
    m.roughness, m.metallic = roughness, 0
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = m.diffuse_color
    bsdf.inputs['Roughness'].default_value = roughness
    m['wetline'] = -1000 if wetline is None else wetline
    if pattern:
        v,u = np.mgrid[0:256,0:256] / 256
        rng=np.random.default_rng(int(hashlib.sha256(name.encode()).hexdigest()[:8],16))
        factor=np.ones_like(u)
        for _ in range(18):
            x,y=rng.uniform(.05,.95,2); rx,ry=rng.uniform(.045,.15,2)
            factor+=rng.uniform(-.045,.025)*np.exp(-((u-x)/rx)**2-((v-y)/ry)**2)
        if pattern == 'frond':
            veins = np.exp(-((v-.5)/.012)**2)
            for sign in (-1,1):
                veins += .55*np.exp(-((v-.5-sign*.17*np.sin(math.pi*u))/.012)**2)
            factor -= .085*veins
        elif pattern == 'leaf':
            veins = np.exp(-((v-.5)/.015)**2)
            for t in (.25,.45,.65,.85):
                veins += .65*np.exp(-((u-t+.55*abs(v-.5))/.013)**2)
            factor += .095*veins
        elif pattern == 'bark':
            grooves=np.sin(2*math.pi*(8*v+.08*np.sin(u*10)))
            factor -= .09*np.exp(-((grooves+.8)/.14)**2)
            factor += .02*np.cos(2*math.pi*(4*v+.08*np.sin(u*10)))
        elif pattern == 'water':
            factor=1+.015*np.cos(2*math.pi*(2*v+.15*np.sin(2*math.pi*u)))
            for x,y,a,b in ((.2,.3,.15,.055),(.68,.7,.18,.065),(.78,.18,.09,.035)):
                du=np.minimum(abs(u-x),1-abs(u-x)); dv=np.minimum(abs(v-y),1-abs(v-y))
                ring=np.sqrt((du/a)**2+(dv/b)**2)
                factor+=.065*np.exp(-((ring-1)/.075)**2)
        elif pattern=='stone':
            for a,b in (((.46,.72),(.55,.65)),((.55,.65),(.64,.66)),((.64,.66),(.69,.56))):
                dx,dy=b[0]-a[0],b[1]-a[1]
                t=np.clip(((u-a[0])*dx+(v-a[1])*dy)/(dx*dx+dy*dy),0,1)
                distance=(u-a[0]-t*dx)**2+(v-a[1]-t*dy)**2
                factor-=.16*np.exp(-distance/.000024)
        elif pattern=='grain':
            r=np.sqrt(((u-.48)*1.05)**2+((v-.52)*.97)**2)
            factor-=.14*np.exp(-(np.sin(r*55+.25*np.sin(u*13))/.22)**2)
        elif pattern=='algae':
            for x,y in ((.3,.6),(.7,.48),(.48,.23)):
                factor-=.10*np.exp(-((u-x)/.14)**2-((v-y)/.12)**2)
        array = byte(rgb[None,None,:]*factor[:,:,None])
        path = asset_dir / '3D/textures/r02' / (name+'.png')
        png(path, np.dstack((array,np.full((256,256),255,dtype=np.uint8))), color=True)
        im = bpy.data.images.load(str(path), check_existing=True)
        im.pack()
        tex = nodes.new('ShaderNodeTexImage'); tex.image=im; tex.interpolation='Linear'
        links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        textures[m.name] = array[::-1].astype(float)/255
    if wetline is not None:
        geo=nodes.new('ShaderNodeNewGeometry'); sep=nodes.new('ShaderNodeSeparateXYZ')
        wet=nodes.new('ShaderNodeMapRange')
        wet.inputs['From Min'].default_value=wetline-.04; wet.inputs['From Max'].default_value=wetline+.04
        wet.inputs['To Min'].default_value=1; wet.inputs['To Max'].default_value=0
        mix=nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[2].default_value=(.62,.68,.73,1)
        if pattern: links.new(tex.outputs['Color'],mix.inputs[1])
        else: mix.inputs[1].default_value=m.diffuse_color
        links.new(geo.outputs['Position'],sep.inputs[0]); links.new(sep.outputs['Z'],wet.inputs['Value'])
        links.new(wet.outputs['Result'],mix.inputs[0]); links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        rough=nodes.new('ShaderNodeMath'); rough.operation='MULTIPLY_ADD'
        rough.inputs[1].default_value=.25-roughness; rough.inputs[2].default_value=roughness
        links.new(wet.outputs['Result'],rough.inputs[0]); links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    return m


def mesh(name, verts, faces, mat, uv_xy=False):
    data=bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces); data.update()
    bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free()
    obj=bpy.data.objects.new(name,data); model.objects.link(obj); obj.parent=visual
    data.materials.append(mat)
    uv=data.uv_layers.new(name='UVMap')
    coords=np.array(verts); lo=coords.min(0); extent=np.maximum(coords.max(0)-lo,.001)
    for poly in data.polygons:
        poly.use_smooth=True
        axes=(0,1) if uv_xy else sorted(range(3),key=lambda i:abs(poly.normal[i]))[:2]
        for loop in poly.loop_indices:
            p=(coords[data.loops[loop].vertex_index]-lo)/extent
            uv.data[loop].uv=(float(p[axes[0]]),float(p[axes[1]]))
    return obj


def oval(name, length, width, thickness, mat, center=(0,0,0), irregular=0, curl=0):
    n=48; vs=[]
    for r,z in ((0,thickness*.5),(.32,thickness*.49),(.72,thickness*.36),(1,0),(.72,-thickness*.36),(.32,-thickness*.49),(0,-thickness*.5)):
        count=1 if r==0 else n
        for i in range(count):
            a=2*math.pi*i/n
            warp=1+irregular*(.5*math.sin(3*a)+.35*math.cos(5*a))
            x=length*.5*r*math.cos(a)*warp
            y=width*.5*r*math.sin(a)*warp
            zz=z+curl*((x/max(length/2,.001))**2+.55*(y/max(width/2,.001))**2)
            vs.append((x+center[0],y+center[1],zz+center[2]))
    fs=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for start in (1,1+n,1+2*n,1+3*n):
        fs.extend((start+i,start+n+i,start+n+(i+1)%n,start+(i+1)%n) for i in range(n))
    end=len(vs)-1
    fs.extend((end,1+4*n+(i+1)%n,1+4*n+i) for i in range(n))
    return mesh(name,vs,fs,mat,uv_xy=True)


def tube(name, points, radii, mat, sides=10):
    vs=[]
    for i,(p,r) in enumerate(zip(points,radii)):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize(); axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.01: axis=tangent.cross(Vector((0,1,0)))
        axis.normalize(); other=tangent.cross(axis).normalized()
        for j in range(sides):
            a=j*2*math.pi/sides
            vs.append(tuple(Vector(p)+r*(math.cos(a)*axis+math.sin(a)*other)))
    fs=[tuple(reversed(range(sides)))]
    for i in range(len(points)-1):
        fs.extend((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j) for j in range(sides))
    fs.append(tuple(range(len(vs)-sides,len(vs))))
    obj=mesh(name,vs,fs,mat)
    uv=obj.data.uv_layers.active
    for face in obj.data.polygons:
        if face.index in (0,len(fs)-1):
            for loop in face.loop_indices:
                j=obj.data.loops[loop].vertex_index%sides
                uv.data[loop].uv=(.5+.48*math.cos(j*2*math.pi/sides),.5+.48*math.sin(j*2*math.pi/sides))
        else:
            j=(face.index-1)%sides
            for loop in face.loop_indices:
                vertex=obj.data.loops[loop].vertex_index
                v=vertex%sides
                uv.data[loop].uv=(vertex//sides/(len(points)-1),(sides if j==sides-1 and v==0 else v)/sides)
    return obj


def rock(name, dims, center, mat):
    n=32; vs=[]
    rings=((0,-.5),(.65,-.48),(.96,-.26),(1,.03),(.91,.29),(.65,.47),(0,.5))
    for r,z in rings:
        for j in range(1 if r==0 else n):
            a=j*2*math.pi/n
            warp=1+.065*math.sin(3*a+.7)+.035*math.cos(5*a)
            vs.append((dims[0]*.5*r*math.cos(a)*warp,
                       dims[1]*.5*r*math.sin(a)*(1+.06*math.cos(2*a)),
                       dims[2]*(z+.035*r*math.sin(3*a+.2))))
    arr=np.array(vs);lo=arr.min(0);hi=arr.max(0)
    arr=(arr-(lo+hi)/2)/(hi-lo)*np.array(dims)+center
    fs=[(0,1+(j+1)%n,1+j) for j in range(n)]
    for start in (1,1+n,1+2*n,1+3*n):
        fs.extend((start+j,start+(j+1)%n,start+n+(j+1)%n,start+n+j) for j in range(n))
    fs.extend((len(vs)-1,1+4*n+j,1+4*n+(j+1)%n) for j in range(n))
    return mesh(name,arr.tolist(),fs,mat,True)


def surface_curve(name, xy, substrate, mat, radius):
    surface=BVHTree.FromPolygons([v.co for v in substrate.data.vertices],[list(p.vertices) for p in substrate.data.polygons])
    points=[]
    for x,y in xy:
        hit,_,_,_=surface.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),20)
        assert hit is not None,(name,x,y)
        points.append((x,y,hit.z-radius*.55))
    return tube(name,points,[radius]*len(points),mat,6)


def create_geometry(c):
    L,W,H=c['length_bu'],c['width_bu'],c['height_bu']
    index=int(c['folder'][1:3])
    pattern={1:'frond',2:'water',3:'soil',4:'bark',5:'stone',6:'leaf',7:'algae'}[index]
    mat=material('M_'+c['asset_id'],c['color'],c['roughness'],pattern,c['wetline_bu'])
    markers={}
    if index==1:
        frond=oval('frond',L,W,H,mat,center=(0,0,H*.5))
        for v in frond.data.vertices:
            x=v.co.x/(L*.5); y=v.co.y/(W*.5)
            v.co.y*=.88+.12*x
            v.co.z+=.035*y*y+.012*x*y
        frond.data.update()
        # Three faint UV veins stay continuous at 1×; subpixel raised tubes flicker between headings.
        root_mat=material('M_root','#B2B985',.58)
        root_x=-L*.2
        tube('root_single',[(root_x,0,.025),(root_x-.025,0,-.16),(root_x-.055,.02,-.45),
                          (root_x-.02,.045,-.78),(root_x+.05,.04,-1.05),(root_x+.06,.03,-1.3*U)],
             [.046,.036,.029,.024,.021,.017],root_mat,10)
        oval('root_cap',.056,.047,.065,root_mat,center=(root_x+.06,.03,-1.3*U))
        oval('root_attachment',.15,.12,.045,root_mat,center=(root_x,0,.005))
        markers={'frond_top':(0,0,H),'root_tip':(root_x+.06,.03,-1.3*U-.0325)}
    elif index==2:
        nx,ny=40,24; vs=[]
        for j in range(ny+1):
            for i in range(nx+1):
                u,v=i/nx,j/ny
                z=.008*math.sin(2*math.pi*(2*u+v))+.004*math.sin(2*math.pi*(u-2*v))
                vs.append(((u-.5)*L,(v-.5)*W,z))
        fs=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
        water=mesh('surface_skin',vs,fs,mat,True)
        # A separate thin boundary keeps orthographic edge views visible without smoothing the water normals into a box.
        edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
        side=[vs[k] for k in edge]+[(vs[k][0],vs[k][1],-H) for k in edge]
        n=len(edge); side_faces=[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
        side_faces.append(tuple(reversed(range(n,2*n))))
        rim=mesh('surface_boundary',side,side_faces,mat,True)
        for poly in rim.data.polygons:poly.use_smooth=False
        markers={'waterline':(0,0,0),'contact_point':(0,0,0)}
    elif index==3:
        nx,ny=20,10; vs=[]
        def soil_height(x,y):
            u=x/L+.5
            return H*(u**1.15)+.055*math.sin(x*2.1)*math.sin(y*2.6)*math.sin(math.pi*u)-.055*math.exp(-((y+.28)/.22)**2)*math.sin(math.pi*u)
        for j in range(ny+1):
            for i in range(nx+1):
                x=(i/nx-.5)*L; y=(j/ny-.5)*W
                y*=.91+.055*math.sin(i/nx*math.pi)+.025*math.sin(i*1.7)
                z=soil_height(x,y)
                vs.append((x,y,z))
        fs=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
        edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
        bottom=len(vs); vs.extend((vs[k][0],vs[k][1],-.08) for k in edge)
        fs.extend((edge[k],edge[(k+1)%len(edge)],bottom+(k+1)%len(edge),bottom+k) for k in range(len(edge)))
        fs.append(tuple(reversed(range(bottom,len(vs)))))
        soil=mesh('slope_base',vs,fs,mat,True)
        pebble=material('M_gravel','#A3AAA1',.72,'soil')
        for i,(x,y,s) in enumerate(((-2.2,-.58,.18),(-1.65,.7,.28),(-.6,.82,.20),(.45,-.78,.33),(1.35,.6,.36),(2.1,-.45,.25),(1.84,.92,.16))):
            rock('gravel_'+str(i),(s,s*.73,s*.48),(x,y,soil_height(x,y)+s*.13),pebble)
        puddle=material('M_puddle','#789EA6',.2,'water')
        p=oval('shallow_puddle',.85,.44,.012,puddle,center=(-1.65,.05,0),irregular=.12)
        for v in p.data.vertices:v.co.z+=soil_height(v.co.x,v.co.y)+.009
        markers={'waterline':(-L/2,0,0),'slope_path':(0,0,soil_height(0,0))}
    elif index==4:
        points=[(-L/2,0,.22),(-L*.38,.045,.29),(-L*.24,.08,.3),(-L*.08,.03,.27),
                (L*.1,-.02,.24),(L*.29,-.065,.24),(L*.42,-.04,.20),(L/2,-.02,.18)]
        radii=[.34,.40,.46,.47,.45,.41,.36,.33]
        main=tube('branch_main',points,radii,mat,20)
        for v in main.data.vertices:
            v.co.y*=1+.035*math.sin(v.co.x*3.1)
        tube('branch_spur',[(-L*.2,.04,.4),(-L*.23,.13,.6),(-L*.26,.21,.83),(-L*.31,.27,H)], [.24,.20,.15,.10],mat,12)
        core=material('M_wood_end','#C4A77D',.75,'grain')
        tube('broken_end',[(L/2-.005,-.02,.18),(L/2+.016,-.02,.18)],[.27,.26],core,24)
        tube('rear_end',[(-L/2-.012,0,.22),(-L/2+.004,0,.22)],[.265,.27],core,24)
        bark=material('M_bark_ridge','#947B63',.7)
        for i,angle in enumerate((.35,.82,1.3,1.9,2.5,2.85)):
            xs=np.linspace(-L*.42+(i%2)*.2,L*.42-(i%3)*.25,12)
            ridge=[]
            for x in xs:
                radius=np.interp(x,[p[0] for p in points],radii)
                y=np.interp(x,[p[0] for p in points],[p[1] for p in points])
                z=np.interp(x,[p[0] for p in points],[p[2] for p in points])
                a=angle+.045*math.sin(x*2+i)
                ridge.append((x,y+(radius-.026)*math.cos(a),z+(radius-.026)*math.sin(a)))
            tube('bark_ridge_'+str(i),ridge,[.042]*len(ridge),bark,8)
        knot=material('M_knot','#78654F',.72)
        ring=[(L*.09+.20*math.cos(a),-.18+.12*math.sin(a)) for a in np.linspace(0,2*math.pi,17)]
        surface_curve('knot_ring',ring,main,knot,.034)
        markers={'walk_top':(0,0,.72),'waterline':(0,0,0)}
    elif index==5:
        core=rock('rock_core',(L,W,H),(0,0,H*.34),mat)
        for v in core.data.vertices:
            if v.co.z>H*.45:
                v.co.z-=.04*math.exp(-((v.co.x-L*.1)/.2)**2-((v.co.y-W*.13)/.3)**2)
        markers={'top_surface':(0,0,H*.84),'waterline':(0,0,0)}
    elif index==6:
        leaf=oval('leaf_plane_thickened',L,W,.075,mat,center=(0,0,.075))
        for v in leaf.data.vertices:
            x=v.co.x/(L/2); y=v.co.y/(W/2)
            v.co.y*=(.84-.18*x)*(1-.22*abs(x))
            if y<0:v.co.y*=1-.38*math.exp(-((x-.42)/.11)**2)-.15*math.exp(-((x+.48)/.09)**2)
            v.co.z+=H*(.55*x*x+1.65*y*y*(.65+.35*math.sin(x*2+.5)))+.035*x*y
        leaf.data.update()
        vein=material('M_leaf_vein','#B49A64',.7)
        surface_curve('leaf_midrib',[(x,.025*math.sin(x)) for x in np.linspace(-L*.43,L*.43,18)],leaf,vein,.036)
        stem=material('M_leaf_stem','#8E7751',.74)
        tube('broken_petiole',[(-L*.43,0,H*.28),(-L*.51,-.025,H*.35),(-L*.57,-.07,H*.5)],[.045,.033,.022],stem,8)
        markers={'leaf_center':(0,0,.1125),'edge':(L*.48,0,H*.38+.075)}
    else:
        patch=oval('patch_decal',L,W,H,mat,irregular=.38)
        arr=np.array([v.co[:] for v in patch.data.vertices]); lo=arr[:,:2].min(0); hi=arr[:,:2].max(0)
        for v in patch.data.vertices:
            v.co.x=(v.co.x-(lo[0]+hi[0])/2)/(hi[0]-lo[0])*L
            v.co.y=(v.co.y-(lo[1]+hi[1])/2)/(hi[1]-lo[1])*W
        mat2=material('M_algae_ochre','#99965A',.82,'algae')
        for i,(x,y,scale) in enumerate(((-.25,.1,.38),(.28,-.08,.30),(.08,.23,.18))):
            island=oval('biofilm_lobe_'+str(i),scale,scale*.62,H*.3,mat2,center=(x,y,H*.48),irregular=.25)
        markers={'food_point':(0,0,H/2),'substrate_uv':(0,0,0)}
    bpy.context.view_layer.update()
    vertices,triangles,*_=evaluated_geometry()
    surface=BVHTree.FromPolygons([Vector(v) for v in vertices],triangles.tolist(),all_triangles=True)
    for key in ('frond_top','slope_path','walk_top','top_surface','leaf_center','food_point'):
        if key in markers:
            x,y,_=markers[key]
            hit,_,_,_=surface.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),20)
            assert hit is not None,key
            markers[key]=tuple(hit)
    for key,point in markers.items():
        marker=bpy.data.objects.new(key,None); model.objects.link(marker); marker.parent=visual
        marker.location=point; marker.empty_display_size=.05
    return markers


def evaluated_geometry():
    dg=bpy.context.evaluated_depsgraph_get()
    verts=[]; tris=[]; normals=[]; uvs=[]; materials=[]; counts={}
    for source in model.objects:
        if source.type!='MESH': continue
        obj=source.evaluated_get(dg); data=obj.to_mesh(); data.calc_loop_triangles()
        offset=len(verts); points=[obj.matrix_world@v.co for v in data.vertices]; verts.extend(points)
        loops=np.array([list(t.loops) for t in data.loop_triangles])
        tris.extend(tuple(offset+i for i in t.vertices) for t in data.loop_triangles)
        transform=np.array(obj.matrix_world.to_3x3().inverted().transposed())
        normals.extend(np.array([list(n.vector) for n in data.corner_normals])[loops]@transform.T)
        uvs.extend(np.array([list(v.uv) for v in data.uv_layers.active.data])[loops])
        materials.extend(data.materials[t.material_index].original for t in data.loop_triangles)
        counts[source.name]={'vertices':len(data.vertices),'triangles':len(data.loop_triangles)}
        assert len(data.uv_layers)==1,source.name
        assert all(len(poly.vertices)>=3 for poly in data.polygons)
        obj.to_mesh_clear()
    return np.array(verts),np.array(tris),np.array(normals),np.array(uvs),materials,counts


def setup_camera(c, view, coords):
    visual.rotation_euler=(0,0,GAME_VIEWS.get(view,0))
    bpy.context.view_layer.update()
    if view in GAME_VIEWS: camera.rotation_euler=CAM_ROT
    else:
        direction={'ortho_front':(-1,0,0),'ortho_back':(1,0,0),'ortho_left':(0,1,0),
                   'ortho_right':(0,-1,0),'ortho_top':(0,0,-1),'ortho_bottom':(0,0,1)}[view]
        camera.rotation_euler=Vector(direction).to_track_quat('-Z','Y').to_euler()
    q=camera.rotation_euler.to_quaternion()
    axes=np.array([q@Vector((1,0,0)),q@Vector((0,1,0)),q@Vector((0,0,1))])
    if view in GAME_VIEWS:
        if 'game_camera_target' not in c:
            screen=np.concatenate([coords@np.array(Matrix.Rotation(yaw,3,'Z')).T@axes.T for yaw in GAME_VIEWS.values()])
            c['game_camera_target']=(axes.T@np.array([(screen[:,0].min()+screen[:,0].max())/2,(screen[:,1].min()+screen[:,1].max())/2,0])).tolist()
        target=np.array(c['game_camera_target'])
    else:
        screen=coords@axes.T
        target=axes.T@np.array([(screen[:,0].min()+screen[:,0].max())/2,(screen[:,1].min()+screen[:,1].max())/2,0])
    camera.location=Vector(target)+q@Vector((0,0,30))
    camera.data.ortho_scale=c['cell_size']*PIXEL
    bpy.context.view_layer.update()
    return axes,target


def render(c, view, coords):
    global size
    size=c['cell_size']
    axes,target=setup_camera(c,view,coords)
    verts,tris,normals,uvs,mats,_=evaluated_geometry()
    bvh=BVHTree.FromPolygons([Vector(v) for v in verts],tris.tolist(),all_triangles=True)
    projected=(verts-target)@axes.T
    x0=max(0,math.floor(projected[:,0].min()/PIXEL+size/2)-1)
    x1=min(size,math.ceil(projected[:,0].max()/PIXEL+size/2)+1)
    y0=max(0,math.floor(size/2-projected[:,1].max()/PIXEL)-1)
    y1=min(size,math.ceil(size/2-projected[:,1].min()/PIXEL)+1)
    ids=[]; triangle_ids=[]; hits=[]
    right,up,forward=Vector(axes[0]),Vector(axes[1]),-Vector(axes[2])
    for y in range(y0,y1):
        row=camera.location+up*(size/2-y-.5)*PIXEL
        for x in range(x0,x1):
            point,normal,idx,dist=bvh.ray_cast(row+right*(x+.5-size/2)*PIXEL,forward,80)
            if idx is not None:
                ids.append(y*size+x); triangle_ids.append(idx); hits.append(tuple(point))
    assert ids,(c['asset_id'],view,'empty render')
    ids=np.array(ids); ti=np.array(triangle_ids); hits=np.array(hits)
    p0,p1,p2=np.moveaxis(verts[tris[ti]],1,0)
    a,b,p=p1-p0,p2-p0,hits-p0
    dot=lambda x,y:np.sum(x*y,axis=1)
    aa,bb,ab,ap,bp=dot(a,a),dot(b,b),dot(a,b),dot(a,p),dot(b,p)
    denom=aa*bb-ab*ab
    assert (abs(denom)>1e-15).all()
    u,v=(bb*ap-ab*bp)/denom,(aa*bp-ab*ap)/denom
    bary=np.stack((1-u-v,u,v),axis=1)
    uv=(uvs[ti]*bary[:,:,None]).sum(1)
    normal=(normals[ti]*bary[:,:,None]).sum(1)@axes.T
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
    material_names=np.array([mats[i].name for i in ti])
    color=np.zeros((len(ids),3)); packed=np.zeros_like(color)
    for name in np.unique(material_names):
        m=bpy.data.materials[name]; rows=material_names==name
        color[rows]=m.diffuse_color[:3]
        if name in textures:
            tex=textures[name]; xy=uv[rows]*256-.5; lo=np.floor(xy).astype(int); f=xy-lo
            sample=np.zeros((rows.sum(),3))
            for dx in (0,1):
                for dy in (0,1):
                    w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])
                    sample+=srgb_to_linear(tex[(lo[:,1]+dy)%256,(lo[:,0]+dx)%256])*w[:,None]
            color[rows]=sample
        packed[rows,0]=m.roughness
        wet=np.clip((m['wetline']+.04-hits[rows,2])/.08,0,1)
        color[rows]*=1-wet[:,None]*(1-np.array([.62,.68,.73]))
        packed[rows,0]=m.roughness+wet*(.25-m.roughness)
    levels=np.digitize(np.clip(normal@[-.36,.57,.73],0,1),[.14,.42,.72])
    lit=byte(linear_to_srgb(color*SHADES[levels]))
    # Each material retains its own hue; C011 supplies the four-step value rhythm.
    palette=[]
    for name in np.unique(material_names):
        base=np.array(bpy.data.materials[name].diffuse_color[:3])
        role_palette=[]
        for wet in (np.ones(3),np.array([.62,.68,.73])):
            for shade in SHADES:
                for tone in (.88,.96,1.04): role_palette.append(byte(linear_to_srgb(base*wet*shade*tone)))
        role_palette=np.unique(np.array(role_palette),axis=0)
        rows=material_names==name
        nearest=np.argmin(((lit[rows,None].astype(float)-role_palette[None])**2*[.25,.6,.15]).sum(2),axis=1)
        lit[rows]=role_palette[nearest]
        palette.extend(role_palette)
    palette=np.unique(np.array(palette),axis=0)
    mask=np.zeros(size*size,dtype=bool); mask[ids]=True
    alpha=mask.astype(np.uint8)*255; full=np.full(size*size,255,dtype=np.uint8)
    def scatter(rgb):
        array=np.zeros((size*size,3),dtype=np.uint8); array[ids]=rgb; return array
    halo=outline(mask.reshape(size,size)).ravel() if c['outline_radius_px'] else mask
    display=scatter(lit); display[halo&~mask]=[34,49,59]
    maps={'sprite':rgba(display,halo.astype(np.uint8)*255),'base':rgba(scatter(byte(linear_to_srgb(color))),alpha),
          'normal':rgba(scatter(byte(normal*.5+.5)),full),'rm':rgba(scatter(byte(packed)),full),
          'emissive':rgba(np.zeros((size*size,3),dtype=np.uint8),full)}
    def project(point):
        x,y,z=(np.array(point)-target)@axes.T
        return [round(size/2+x/PIXEL,4),round(size/2-y/PIXEL,4)]
    anchors={o.name:{'world':list(o.matrix_world.translation),'xy':project(o.matrix_world.translation)} for o in model.objects if o.type=='EMPTY'}
    bbox={}
    for channel in ('sprite','base'):
        ys,xs=np.nonzero(maps[channel][:,:,3]); rect=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        bbox[channel]=rect
        assert min(rect[0],rect[1],size-rect[2],size-rect[3])>=c['minimum_margin_px'],(c['asset_id'],view,rect,size)
    record={'view':view,'view_kind':'game' if view in GAME_VIEWS else 'inspection','yaw_radians':GAME_VIEWS.get(view,0),
            'mirrored':False,'sample':0,'time_s':0.0,'duration_s':1.0,'phase':'mid','event_marker_ids':[],
            'pivot':project((0,0,0)),'bbox':bbox,'anchors':anchors,'camera_matrix_world':[list(row) for row in camera.matrix_world],
            'palette_rgb':palette.tolist(),'surface_pixels':int(mask.sum())}
    checks=(np.floor(uv[:,0]*12).astype(int)+np.floor(uv[:,1]*12).astype(int))%2
    checker_rgb=np.where(checks[:,None],np.array([205,208,200]),np.array([75,101,115]))
    checker=rgba(scatter(checker_rgb.astype(np.uint8)),alpha)
    return maps,record,checker


def build_one(c):
    global model,visual,camera,asset_dir,textures
    assert bpy.app.background,'This script requires an isolated background process.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    textures={}; asset_dir=ROOT/c['folder']
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
    lighting=json.loads((HERE/'reference/C011_scene.json').read_text(encoding='utf-8'))
    for key in ('view_transform','look','exposure','gamma'):
        setattr(scene.view_settings,key,lighting[key])
    world=bpy.data.worlds.new('C011_Preview_World'); scene.world=world; world.use_nodes=True
    background=world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=lighting['world']['color']
    background.inputs['Strength'].default_value=lighting['world']['strength']
    for source in lighting['lights']:
        data=bpy.data.lights.new(source['name'],source['type'])
        data.energy=source['energy']; data.color=source['color']
        if source['size'] is not None: data.size=source['size']; data.shape=source['shape']
        light=bpy.data.objects.new(source['name'],data); scene.collection.objects.link(light)
        light.location=source['location']; light.rotation_euler=source['rotation']
    scene.render.film_transparent=True; scene.render.resolution_x=c['cell_size']; scene.render.resolution_y=c['cell_size']
    scene.render.resolution_percentage=100
    model=bpy.data.collections.new(c['asset_id']); scene.collection.children.link(model)
    physics=bpy.data.objects.new('physics_root',None); model.objects.link(physics)
    visual=bpy.data.objects.new('visual_root',None); model.objects.link(visual); visual.parent=physics
    visual['motion_scope']='static; world movement and collision owned by environment system'
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Orthographic')); scene.collection.objects.link(camera)
    camera.data.type='ORTHO'; camera.data.clip_end=100; scene.camera=camera
    create_geometry(c); bpy.context.view_layer.update()
    reference=bpy.data.objects.new('GPT_reference_sheet',None); scene.collection.objects.link(reference)
    reference.empty_display_type='IMAGE'; reference.data=bpy.data.images.load(str(asset_dir/'sheet'/(c['asset_id']+'_sheet_r01.png')))
    reference.data.pack(); reference.hide_render=True; reference.hide_viewport=True
    coords,tris,normals,uvs,mats,counts=evaluated_geometry()
    assert len(tris)<=c['triangle_budget'],(c['folder'],len(tris))
    assert np.isfinite(coords).all() and np.isfinite(uvs).all()
    assert len([o for o in model.objects if o.name=='root_single'])==(1 if c['folder'].startswith('A01') else 0)
    records=[]; out=asset_dir/'2D/environment-r02'
    for view in c['supported_views']:
        maps,record,checker=render(c,view,coords)
        dest=out/c['clip']/view; dest.mkdir(parents=True,exist_ok=True)
        png(dest/'000.png',np.concatenate(list(maps.values()),axis=0))
        png(dest/'sprite.png',maps['sprite'],True)
        if view in ('left','ortho_top'):png(dest/'uv_checker.png',checker,True)
        record['file']=(dest/'000.png').relative_to(out).as_posix()
        record['sha256']=SHA(dest/'000.png')
        records.append(record)
        print(c['folder'],view,'rendered',flush=True)
    visual.rotation_euler=(0,0,0); setup_camera(c,'left',coords)
    scene['asset_id']=c['asset_id']; scene['revision']=c['revision']; scene['DEC_06']='deferred; experiment profile only'
    scene['world_units_per_pixel']=PIXEL
    scene['asset_view']='left'
    view_text=bpy.data.texts.new('ENVIRONMENT_VIEWS.json'); view_text.write(json.dumps(records))
    for source in ('build_assets.py','SPRITE_PNG.py','SELECT_ENVIRONMENT_VIEW.py'):
        text=bpy.data.texts.new(source); text.write((HERE/source).read_text(encoding='utf-8'))
    for image in bpy.data.images:
        if image.source=='FILE':
            name=Path(image.filepath).name
            image.filepath='//../sheet/'+name if image==reference.data else '//textures/r02/'+name
    scene.render.image_settings.file_format='PNG'
    save=asset_dir/'3D'/(c['asset_id']+'_r02.blend')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(save),check_existing=False)
    model_report={'blender':bpy.app.version_string,'geometry':counts,'triangle_count':len(tris),'bone_count':0,
                  'bounds_bu':[coords.min(0).tolist(),coords.max(0).tolist()],
                  'extent_bu':(coords.max(0)-coords.min(0)).tolist(),'all_images_packed':all(im.packed_file for im in bpy.data.images if im.source=='FILE'),
                  'uv_policy':'planar projection for slabs, fronds and rounded stones; longitudinal seam for tubes, planar caps; intentional repeated underside and separate detail islands with higher checker density',
                  'hidden_face_policy':'closed editable volumes retained; no unproven occluded-face deletion',
                  'rendered_views':len(records),'blend_sha256':SHA(save),'static_root':True}
    (asset_dir/'3D/model_validation_r02.json').write_text(json.dumps(model_report,indent=2),encoding='utf-8')
    manifest={'schema':'toktogi_environment/1','asset_id':c['asset_id'],'revision':c['revision'],
              'source_blend':str(save.relative_to(asset_dir)).replace('\\','/'),'source_blend_sha256':SHA(save),
              'cell_size':[c['cell_size'],c['cell_size']],'pass_order':['sprite','base','normal','rm','emissive'],
              'data_alpha':255,'coverage_channel':'base.alpha','normal_space':'camera_R_right_G_up_B_toward_camera',
              'display_scale':1,'world_units_per_pixel':PIXEL,'mirror_allowed':False,'filter':'nearest',
              'clip':c['clip'],'loop':True,'static':True,'duration_s':1.0,'cells':records,
              'game_views':GAME_VIEWS,'game_pivot':next(r['pivot'] for r in records if r['view']=='left'),
              'game_camera_target':c['game_camera_target'],'view_selector':'SELECT_ENVIRONMENT_VIEW.py',
              'role':c['role'],'production_export_allowed':False,'game_integration':'pending_stage_and_DEC_06',
              'AO':'not baked; neutral 1 in consumer; no AO multiplied into Base',
              'collision_profile':None,'collision_status':'not_bound_to_runtime',
              'generator_sha256':SHA(HERE/'build_assets.py'),'png_helper_sha256':SHA(HERE/'SPRITE_PNG.py')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return model_report


if __name__=='__main__':
    report={c['asset_id']:build_one(c) for c in ASSETS}
    (HERE/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
