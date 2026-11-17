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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from png_codec import png, srgb_to_linear

CONFIG = json.loads((ROOT / '_production/assets.json').read_text(encoding='utf-8'))
COLORS = ['82a548', 'b6c96c', '61783d', 'b4a079', '825476', 'c8d58d', 'e5b5c7',
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
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24 if primary else 12, ring_count=12 if primary else 6, radius=1)
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
        r = radius*(1-(1-taper)*i/(len(points)-1))
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


def blade(name, start, tip, width, role=0, arch=.2):
    start, tip = Vector(start), Vector(tip)
    direction = tip-start
    side = Vector((-direction.y,direction.x,0))
    if side.length < .001:
        side = Vector((1,0,0))
    side.normalize()
    vertices, uv, faces = [], [], []
    for i in range(13):
        t=i/12
        center=start+direction*t+Vector((0,0,arch*math.sin(math.pi*t)))
        w=max(.002,width*math.sin(math.pi*t)**.85/2)
        thick=max(.002,width*.075*math.sin(math.pi*t))
        for j,offset in enumerate((-side*w,Vector((0,0,thick)),side*w,Vector((0,0,-thick)))):
            vertices.append(center+offset)
            uv.append((t,j/3))
    for i in range(12):
        for j in range(4):
            k,n=i*4+j,i*4+(j+1)%4
            faces.append((k,n,n+4,k+4))
    faces += [(3,2,1,0),(48,49,50,51)]
    return mesh(name,vertices,faces,uv,role)


def patch(name, length, depth, role):
    n=48
    vertices,uv,faces=[],[],[]
    for z in (0,-depth):
        vertices.append((0,0,z));uv.append((.5,.5))
        for i in range(n):
            a=i*math.tau/n;r=1+.065*math.sin(5*a)+.025*math.cos(9*a)
            vertices.append((length/2*r*math.cos(a),length*.34*r*math.sin(a),z))
            uv.append((.5+.44*r*math.cos(a),.5+.44*r*math.sin(a)))
    for i in range(n):
        a,b=1+i,1+(i+1)%n;c,d=a+n+1,b+n+1
        faces.extend(((0,a,b),(n+1,d,c),(a,c,d,b)))
    return mesh(name,vertices,faces,uv,role)


def geometry(code, L):
    if code in ('B01','B02','B03'):
        width={'B01':L*1.6/2.5,'B02':L*5/6,'B03':L*.7}[code]
        thick=L*(.32 if code=='B03' else .10)
        ball('frond', (0,0,thick*.15), (L,width,thick),0,4 if code=='B02' else None,.14 if code=='B01' else 0)
        if code!='B03':
            count=7 if code=='B02' else 3
            for j in range(count):
                a=(j-(count-1)/2)*.30
                tube(f'vein_{j+1:02}',[(-L*.35,0,thick*.40),(L*.05,width*.27*math.sin(a),thick*.65),(L*.35*math.cos(a),width*.42*math.sin(a),thick*.43)],L*.007,1,6,.35)
            count=7 if code=='B02' else 1
            root_length=35*.965396 if code=='B02' else .90
            for j in range(count):
                x=(j-(count-1)/2)*L*.07;y=.06*L*math.sin(j)
                tube(f'root_{j+1:02}',[(x,y,0),(x+.04*L,y,-root_length*.32),(x-.03*L,y+.04*L,-root_length*.68),(x+.03*L,y,-root_length)],.04 if code=='B02' else .025,3,8,.18)
            if code=='B01':
                for s in (-1,1):
                    ball('root_sheath_wing_'+str(s),(s*.065,0,-.045),(.18,.10,.06),3)
    elif code=='B04':
        for s in (-1,1):
            cx=s*L*.49
            ball('floating_leaf_'+('L' if s<0 else 'R'),(cx,0,L*.03),(L,L*.6,L*.12),0,2)
            for i in range(5):
                for j in range(3):
                    x=cx+(i-2)*L*.14;y=(j-1)*L*.13
                    z=L*(.03+.06*math.sqrt(max(0,1-((x-cx)/(L/2))**2-(y/(L*.3))**2)))
                    tube(f'hair_{s}_{i}_{j}',[(x,y,z),(x+.018*L,y,z+.025*L)],.006*L,5,5,.2)
        tube('joining_stem',[(-L*.15,0,0),(0,0,-L*.1),(L*.15,0,0)],L*.025,2)
        tube('submerged_leaf_mid',[(0,0,0),(0,0,-L*.6)],L*.018,2)
        for i in range(5):
            for s in (-1,1):
                a=(0,0,-L*(.12+i*.08));b=(s*L*(.26-i*.035),0,a[2]-L*.12)
                tube(f'submerged_leaf_branch_{i}_{s}',[a,b,(b[0]*1.12,L*.06,b[2]-L*.06)],L*.012,2)
                tube(f'submerged_leaf_fork_{i}_{s}',[b,(b[0]*.9,-L*.09,b[2]-L*.09)],L*.008,2)
    elif code=='B05':
        tube('rootless_stem',[(0,0,0),(.08,0,L)],L*.019,2)
        for n in range(4):
            z=L*(.15+n*.22)
            for j in range(6):
                a=j*math.tau/6+n*.23;out=Vector((math.cos(a),math.sin(a),.50))
                start=Vector((0,0,z));fork=start+out*(L*.14)
                tube(f'whorl_{n+1}_leaf_{j+1}',[start,fork],L*.012,0)
                for s in (-1,1):
                    side=Vector((-math.sin(a),math.cos(a),.1))*s
                    end=fork+out*(L*.11)+side*(L*.045)
                    tube(f'fork1_{n}_{j}_{s}',[fork,end],L*.009,0)
                    for k in (-1,1):
                        tube(f'fork2_{n}_{j}_{s}_{k}',[end,end+out*(L*.08)+side*(k*L*.03)],L*.006,0)
    elif code=='B06':
        tube('vertical_stem',[(0,0,0),(0,0,L)],L*.014,2,10,.65)
        tube('cylindrical_inflorescence',[(0,0,L*.74),(0,0,L*.76),(0,0,L*.91),(0,0,L*.93)],L*.040,11,16,.95)
        for j in range(6):
            a=j*math.tau/6+.3;r=L*(.19+.025*(j%3));z=L*(.52+.06*(j%3))
            blade(f'strap_leaf_{j+1}',(0,0,0),(r*math.cos(a),r*math.sin(a),z),L*.048,0,L*.23)
    elif code=='B07':
        tube('jointed_cane',[(0,0,0),(L*.02,0,L)],L*.010,2,8,.5)
        for j in range(7):
            z=L*(.12+j*.09);s=(-1)**j
            ball(f'node_{j+1}',(L*.02*z/L,0,z),(L*.025,L*.025,L*.018),1)
            blade(f'lance_leaf_{j+1}',(0,0,z),(s*L*.23,.04*L*math.sin(j),z+L*.10),L*.045,0,L*.07)
        for n in range(5):
            z=L*(.75+n*.048);r=L*(.115-n*.020)
            for j in range(6):
                a=j*math.tau/6+n*.4;start=Vector((.02*L,0,z));end=start+Vector((r*math.cos(a),r*math.sin(a),L*.035))
                tube(f'panicle_branch_{n}_{j}',[start,end],L*.003,3,6,.3)
                for t in (.5,.8,1):
                    p=start+(end-start)*t
                    ball(f'panicle_spikelet_{n}_{j}_{t}',p,(L*.015,L*.012,L*.038),3)
    elif code=='B08':
        points=[(-L/2+i*L/6,.08*L*math.sin(i*2),L*(.1+.035*(i%2))) for i in range(7)]
        tube('angular_stem',points,L*.012,11,4,.8)
        for i,p in enumerate(points[1:-1]):
            s=(-1)**i
            tip=(p[0]+L*.07,p[1]+s*L*.18,p[2]+L*.05)
            blade(f'arrow_leaf_{i}',p,tip,L*.10,0,L*.035)
            for k in (-1,1):
                blade(f'basal_leaf_lobe_{i}_{k}',p,(p[0]+k*L*.045,p[1]-s*L*.035,p[2]),L*.05,0,.01)
            tube(f'downward_prickle_{i}',[p,(p[0]-.02*L,p[1],p[2]-.06*L)],L*.012,11,4,.05)
        for k,p in enumerate((points[0],points[-1])):
            top=Vector(p)+Vector((0,0,.12*L))
            tube(f'flower_peduncle_{k}',[p,top],L*.007,2)
            for j in range(5):
                a=j*math.tau/5
                center=top+Vector((math.cos(a)*L*.028,math.sin(a)*L*.028,L*.015))
                for petal in range(5):
                    b=petal*math.tau/5
                    ball(f'flower_{k}_{j}_{petal}',center+Vector((math.cos(b)*L*.012,math.sin(b)*L*.012,0)),(L*.025,L*.025,L*.016),6)
                ball(f'pollen_{k}_{j}',center,(L*.012,)*3,7)
    elif code=='B09':
        patch('sediment_floor',L,L*.07,8)
        layer=patch('sediment_stratum',L*.995,L*.025,9);layer.location.z=-L*.05
        for i,(x,y,s) in enumerate(((-.27,-.1,.13),(.2,.14,.1),(-.13,.22,.075),(.28,-.18,.12),(.02,-.12,.055),(-.33,.13,.05))):
            ball(f'gravel_{i+1}',(x*L,y*L,s*L*.2),(s*L,s*L*.8,s*L*.65),10)
        for i in range(3):
            tube(f'detritus_{i}',[(-.18*L+i*.17*L,.02*L,.02),(-.10*L+i*.17*L,.09*L,.04)],L*.01,11,6,.7)
    elif code=='B0A':
        patch('attached_film',L,.012,12)
        for i in range(16):
            x=L*.35*math.sin(i*2.4);y=L*.23*math.cos(i*1.8)
            ball(f'film_colony_{i}',(x,y,.007),(L*.045,L*.032,.018),12)
    elif code=='B0B':
        patch('microscopy_substrate_patch',L,.012,12)
        for i in range(8):
            x=L*.33*math.sin(i*2.4);y=L*.22*math.cos(i*1.8);a=i*.8
            item=ball(f'illustrative_shell_{i}',(0,0,.025),(L*.14,L*.055,.045),13)
            item.rotation_euler.z=a;item.location=(x,y,0)
            for j in range(5):
                px=(j-2)*L*.020;w=L*.018*math.sqrt(max(0,1-(px/(L*.07))**2))
                line=tube(f'illustrative_striation_{i}_{j}',[(px,-w,.046),(px,w,.046)],.005,14,5,.8)
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
    scene=bpy.context.scene;scene.name=code+'_background_r01'
    scene.unit_settings.system='NONE'
    physics=bpy.data.objects.new('physics_root',None);scene.collection.objects.link(physics)
    VISUAL=bpy.data.objects.new('visual_root',None);scene.collection.objects.link(VISUAL);VISUAL.parent=physics
    tex=np.zeros((512,512,4),np.uint8);tex[:,:,3]=255
    for i,h in enumerate(COLORS):
        yy,xx=np.mgrid[:128,:128]
        variation=1+.025*np.sin(xx/20+i)*np.cos(yy/23-i)+.012*np.sin((xx+yy)/11)
        tex[i//4*128:(i//4+1)*128,i%4*128:(i%4+1)*128,:3]=np.clip(np.array(list(bytes.fromhex(h)))*variation[:,:,None],0,255)
    texture_path=directory/'3D/textures'/f'{config["name"]}_basecolor_r01.png'
    png(texture_path,np.flipud(tex),True)
    image=bpy.data.images.load(str(texture_path));image.name='Background_BaseColor_r01';image.pack();image.filepath='//textures/'+texture_path.name
    MATERIALS=[]
    for i,role in enumerate(ROLES):
        material=bpy.data.materials.new(role);material.use_nodes=True
        opacity=178/255 if code=='B0A' else 216/255 if code=='B0B' else 1.
        material.diffuse_color=(*srgb_to_linear(np.array(list(bytes.fromhex(COLORS[i])))/255),opacity)
        shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.78 if i<12 else .62
        shader.inputs['Alpha'].default_value=opacity
        node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.interpolation='Linear'
        material.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
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
                anchors['tip_'+item.name]=list(sum((v.co for v in list(item.data.vertices)[-4:]),Vector())/4)
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
              'palette_roles':dict(zip(ROLES,COLORS)),'uv_policy':'16 padded tiles; intentional reuse per material; no asymmetric measured texture',
              'source_document_status':'Original biological unknowns remain null; production dimensions are design choices.'}
    text=bpy.data.texts.new('ASSET_MANIFEST.json');text.write(json.dumps(manifest,ensure_ascii=False,indent=2))
    scene['asset_id']=config['name'];scene['revision']='background-r01'
    scene['runtime_note']='Static B background; no player collision, buoyancy or gameplay events.'
    for item in bpy.context.selected_objects:item.select_set(False)
    VISUAL.select_set(True);bpy.context.view_layer.objects.active=VISUAL
    path=directory/'3D'/f'{config["name"]}_r01.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    (directory/'3D/model_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'id':code,'triangles':triangles,'meshes':len(objects),'blend':str(path)}


if __name__=='__main__':
    selected=globals().get('ONLY',sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    result=[build(c) for c in CONFIG if not selected or c['id'] in selected]
    print(json.dumps(result),flush=True)
