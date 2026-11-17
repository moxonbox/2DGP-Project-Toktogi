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
        factor = 1 + .025*np.sin(2*math.pi*(3*u+2*v)) + .018*np.cos(2*math.pi*(u-4*v))
        if pattern == 'frond':
            veins = np.exp(-((v-.5)/.012)**2)
            for sign in (-1,1):
                veins += .55*np.exp(-((v-.5-sign*.17*np.sin(math.pi*u))/.012)**2)
            factor -= .07*veins
        elif pattern == 'leaf':
            veins = np.exp(-((v-.5)/.015)**2)
            for t in (.25,.45,.65,.85):
                veins += .65*np.exp(-((u-t+.55*abs(v-.5))/.013)**2)
            factor += .11*veins
        elif pattern == 'bark':
            factor += .045*np.cos(2*math.pi*(9*v+.3*np.sin(u*8)))
        elif pattern == 'water':
            factor = 1 + .06*np.cos(2*math.pi*(2*v+.15*np.sin(2*math.pi*u)))
        array = byte(rgb[None,None,:]*factor[:,:,None])
        path = asset_dir / '3D/textures' / (name+'.png')
        png(path, np.dstack((array,np.full((256,256),255,dtype=np.uint8))), color=True)
        im = bpy.data.images.load(str(path), check_existing=True)
        im.pack()
        tex = nodes.new('ShaderNodeTexImage'); tex.image=im; tex.interpolation='Linear'
        links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        textures[m.name] = array[::-1].astype(float)/255
    if wetline is not None:
        geo=nodes.new('ShaderNodeNewGeometry'); sep=nodes.new('ShaderNodeSeparateXYZ')
        less=nodes.new('ShaderNodeMath'); less.operation='LESS_THAN'; less.inputs[1].default_value=wetline
        mix=nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[2].default_value=(.62,.68,.73,1)
        if pattern: links.new(tex.outputs['Color'],mix.inputs[1])
        else: mix.inputs[1].default_value=m.diffuse_color
        links.new(geo.outputs['Position'],sep.inputs[0]); links.new(sep.outputs['Z'],less.inputs[0])
        links.new(less.outputs[0],mix.inputs[0]); links.new(mix.outputs[0],bsdf.inputs['Base Color'])
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
    n=32; vs=[]
    for r,z in ((0,thickness*.5),(.55,thickness*.46),(1,0),(.55,-thickness*.46),(0,-thickness*.5)):
        count=1 if r==0 else n
        for i in range(count):
            a=2*math.pi*i/n
            warp=1+irregular*(.5*math.sin(3*a)+.35*math.cos(5*a))
            x=length*.5*r*math.cos(a)*warp
            y=width*.5*r*math.sin(a)*warp
            zz=z+curl*((x/max(length/2,.001))**2+.55*(y/max(width/2,.001))**2)
            vs.append((x+center[0],y+center[1],zz+center[2]))
    fs=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for start in (1,1+n):
        fs.extend((start+i,start+n+i,start+n+(i+1)%n,start+(i+1)%n) for i in range(n))
    end=len(vs)-1
    fs.extend((end,1+2*n+(i+1)%n,1+2*n+i) for i in range(n))
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
    return mesh(name,vs,fs,mat)


def rock(name, dims, center, mat):
    # Rounded cube keeps editable low polygon structure and a broad landing cap.
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object; obj.name=name
    for coll in list(obj.users_collection): coll.objects.unlink(obj)
    model.objects.link(obj); obj.parent=visual
    obj.scale=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=obj.modifiers.new('Rounded_edges','BEVEL'); bevel.width=min(dims)*.29; bevel.segments=3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for v in obj.data.vertices:
        v.co.x *= 1+.025*math.sin(v.co.y*3+v.co.z)
        v.co.y *= 1+.04*math.cos(v.co.x*2-v.co.z*3)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons: poly.use_smooth=True
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.03); bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def create_geometry(c):
    L,W,H=c['length_bu'],c['width_bu'],c['height_bu']
    index=int(c['folder'][1:3])
    pattern={1:'frond',2:'water',3:'soil',4:'bark',5:'stone',6:'leaf',7:'algae'}[index]
    mat=material('M_'+c['asset_id'],c['color'],c['roughness'],pattern,c['wetline_bu'])
    markers={}
    if index==1:
        oval('frond',L,W,H,mat,center=(0,0,H*.5))
        root_mat=material('M_root','#A6AE73',.58)
        root_x=-L*.2
        tube('root_single',[(root_x,0,.01),(root_x-.04,0,-.45),(root_x+.06,.03,-1.3*U)], [.045,.032,.022],root_mat,8)
        oval('root_cap',.095,.07,.09,root_mat,center=(root_x+.06,.03,-1.3*U))
        markers={'frond_top':(0,0,H),'root_tip':(root_x+.06,.03,-1.3*U-.045)}
    elif index==2:
        vs=[(-L/2,-W/2,-H/2),(L/2,-W/2,-H/2),(L/2,W/2,-H/2),(-L/2,W/2,-H/2),
            (-L/2,-W/2,H/2),(L/2,-W/2,H/2),(L/2,W/2,H/2),(-L/2,W/2,H/2)]
        water=mesh('surface_skin',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,True)
        for poly in water.data.polygons: poly.use_smooth=False
        markers={'waterline':(0,0,0),'contact_point':(0,0,0)}
    elif index==3:
        nx,ny=12,6; vs=[]
        for j in range(ny+1):
            for i in range(nx+1):
                x=(i/nx-.5)*L; y=(j/ny-.5)*W
                z=(i/nx)*H+.025*math.sin(i*1.3)*math.sin(j*.8)*(i/nx)
                vs.append((x,y,z))
        fs=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
        edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
        bottom=len(vs); vs.extend((vs[k][0],vs[k][1],-.08) for k in edge)
        fs.extend((edge[k],edge[(k+1)%len(edge)],bottom+(k+1)%len(edge),bottom+k) for k in range(len(edge)))
        fs.append(tuple(reversed(range(bottom,len(vs)))))
        mesh('slope_base',vs,fs,mat,True)
        pebble=material('M_gravel','#969D96',.7)
        for i,(x,y) in enumerate(((-1.8,-.55),(-.5,.65),(.8,-.6),(2,.55))):
            z=(x/L+.5)*H
            rock('gravel_'+str(i),(.25,.21,.17),(x,y,z+.04),pebble)
        puddle=material('M_puddle','#648F9C',.2)
        p=oval('shallow_puddle',.68,.32,.009,puddle,center=(-1.7,.1,(-1.7/L+.5)*H+.009))
        for v in p.data.vertices: v.co.z+=(v.co.x+1.7)*H/L
        markers={'waterline':(-L/2,0,0),'slope_path':(0,0,H/2)}
    elif index==4:
        tube('branch_main',[(-L/2,0,.22),(-L*.3,.025,.26),(0,0,.24),(L*.3,-.02,.25),(L/2,0,.2)],
             [.40,.48,.50,.44,.37],mat,14)
        tube('branch_spur',[(-L*.2,.02,.35),(-L*.24,.18,.65),(-L*.3,.28,H)],[.24,.18,.13],mat,10)
        core=material('M_wood_end','#C2A57B',.75)
        tube('broken_end',[(L/2-.005,0,.2),(L/2+.018,0,.2)],[.29,.28],core,14)
        oval('knot',.43,.32,.07,mat,center=(L*.12,-.08,.72))
        markers={'walk_top':(0,0,.74),'waterline':(0,0,0)}
    elif index==5:
        rock('rock_core',(L,W,H),(0,0,H*.34),mat)
        markers={'top_surface':(0,0,H*.84),'waterline':(0,0,0)}
    elif index==6:
        leaf=oval('leaf_plane_thickened',L,W,.07,mat,center=(0,0,.06),irregular=.055,curl=H*.62)
        for v in leaf.data.vertices:
            if v.co.x>L*.15 and v.co.y<0:
                v.co.y *= 1-.24*math.exp(-((v.co.x-L*.3)/(L*.09))**2)
        markers={'leaf_center':(0,0,.095),'edge':(L*.48,0,.06+H*.62)}
    else:
        oval('patch_decal',L,W,H,mat,irregular=.13)
        markers={'food_point':(0,0,H/2),'substrate_uv':(0,0,0)}
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
    visual.rotation_euler=(0,0,2.00151174696589 if view=='game_right' else 0)
    bpy.context.view_layer.update()
    if view.startswith('game'): camera.rotation_euler=CAM_ROT
    else:
        direction={'front':(-1,0,0),'back':(1,0,0),'left':(0,1,0),'right':(0,-1,0),'top':(0,0,-1)}[view]
        camera.rotation_euler=Vector(direction).to_track_quat('-Z','Y').to_euler()
    q=camera.rotation_euler.to_quaternion()
    axes=np.array([q@Vector((1,0,0)),q@Vector((0,1,0)),q@Vector((0,0,1))])
    world=coords@np.array(visual.matrix_world.to_3x3()).T
    screen=world@axes.T
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
        wet=rows & (hits[:,2]<m['wetline'])
        color[wet]*=[.62,.68,.73]; packed[wet,0]=.25
    levels=np.digitize(np.clip(normal@[-.36,.57,.73],0,1),[.14,.42,.72])
    lit=byte(linear_to_srgb(color*SHADES[levels]))
    # Each material retains its own hue; C011 supplies the four-step value rhythm.
    palette=[]
    for name in np.unique(material_names):
        base=np.array(bpy.data.materials[name].diffuse_color[:3])
        for wet in (np.ones(3),np.array([.62,.68,.73])):
            for shade in SHADES:
                for tone in (.94,1.04): palette.append(byte(linear_to_srgb(base*wet*shade*tone)))
    palette=np.unique(np.array(palette),axis=0)
    nearest=np.argmin(((lit[:,None].astype(float)-palette[None])**2*[.25,.6,.15]).sum(2),axis=1)
    lit=palette[nearest]
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
    record={'view':view,'sample':0,'time_s':0.0,'duration_s':1.0,'phase':'mid','event_marker_ids':[],
            'pivot':project((0,0,0)),'bbox':bbox,'anchors':anchors,'camera_matrix_world':[list(row) for row in camera.matrix_world],
            'palette_rgb':palette.tolist(),'surface_pixels':int(mask.sum())}
    return maps,record


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
    records=[]; out=asset_dir/'2D/environment-r01'
    for view in c['supported_views']:
        maps,record=render(c,view,coords)
        dest=out/c['clip']/view; dest.mkdir(parents=True,exist_ok=True)
        png(dest/'000.png',np.concatenate(list(maps.values()),axis=0))
        png(dest/'sprite.png',maps['sprite'],True)
        record['file']=(dest/'000.png').relative_to(out).as_posix()
        record['sha256']=SHA(dest/'000.png')
        records.append(record)
        print(c['folder'],view,'rendered',flush=True)
    visual.rotation_euler=(0,0,0); setup_camera(c,'game_left',coords)
    scene['asset_id']=c['asset_id']; scene['revision']=c['revision']; scene['DEC_06']='deferred; experiment profile only'
    scene['world_units_per_pixel']=PIXEL
    for source in ('build_assets.py','SPRITE_PNG.py'):
        text=bpy.data.texts.new(source); text.write((HERE/source).read_text(encoding='utf-8'))
    for image in bpy.data.images:
        if image.source=='FILE':
            name=Path(image.filepath).name
            image.filepath='//../sheet/'+name if image==reference.data else '//textures/'+name
    scene.render.image_settings.file_format='PNG'
    save=asset_dir/'3D'/(c['asset_id']+'_r01.blend')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(save),check_existing=False)
    model_report={'blender':bpy.app.version_string,'geometry':counts,'triangle_count':len(tris),'bone_count':0,
                  'bounds_bu':[coords.min(0).tolist(),coords.max(0).tolist()],
                  'extent_bu':(coords.max(0)-coords.min(0)).tolist(),'all_images_packed':all(im.packed_file for im in bpy.data.images if im.source=='FILE'),
                  'uv_policy':'planar per face for hard surfaces; XY projection for fronds/decal; intentional repeating underside',
                  'hidden_face_policy':'closed editable volumes retained; no unproven occluded-face deletion',
                  'rendered_views':len(records),'blend_sha256':SHA(save),'static_root':True}
    (asset_dir/'3D/model_validation.json').write_text(json.dumps(model_report,indent=2),encoding='utf-8')
    manifest={'schema':'toktogi_environment/1','asset_id':c['asset_id'],'revision':c['revision'],
              'source_blend':str(save.relative_to(asset_dir)).replace('\\','/'),'source_blend_sha256':SHA(save),
              'cell_size':[c['cell_size'],c['cell_size']],'pass_order':['sprite','base','normal','rm','emissive'],
              'data_alpha':255,'coverage_channel':'base.alpha','normal_space':'camera_R_right_G_up_B_toward_camera',
              'display_scale':1,'world_units_per_pixel':PIXEL,'mirror_allowed':False,'filter':'nearest',
              'clip':c['clip'],'loop':True,'static':True,'duration_s':1.0,'cells':records,
              'role':c['role'],'production_export_allowed':False,'game_integration':'pending_stage_and_DEC_06',
              'AO':'not baked; neutral 1 in consumer; no AO multiplied into Base',
              'collision_profile':None,'collision_status':'not_bound_to_runtime',
              'generator_sha256':SHA(HERE/'build_assets.py'),'png_helper_sha256':SHA(HERE/'SPRITE_PNG.py')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return model_report


if __name__=='__main__':
    report={c['asset_id']:build_one(c) for c in ASSETS}
    (HERE/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
