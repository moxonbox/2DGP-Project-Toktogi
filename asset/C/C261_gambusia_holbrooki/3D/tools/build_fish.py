"""Editable male/female Gambusia, UV textures, fin/jaw rig and all 48 phases."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime'))
sys.path.insert(0,str(ROOT/'3D/tools'))
from motion_spec import VARIANTS,DESIGNS,PHASES,LOOPS,phase_duration,pose,catalog
from png_codec import png
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=60
scene.unit_settings.system='METRIC'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='None'
scene.world=bpy.data.worlds.new('Neutral studio')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
physics=bpy.data.objects.new('physics_root',None);scene.collection.objects.link(physics)
visual=bpy.data.objects.new('visual_root',None);scene.collection.objects.link(visual);visual.parent=physics
manifest={'asset_id':'C261_gambusia_holbrooki','object_id':'predator_gambusia_holbrooki','revision':'gambusia-r03',
          'pipeline':'AssetPipeLine v2.3','blender':bpy.app.version_string,'variants':{},'actions':catalog(),
          'front':'-X','up':'+Z','left':'+Y','physics_owner':'simulation','effects_owner':'simulation',
          'design_scale':.1,'measure_kind':'SL; snout to caudal-fin base; TL measured separately',
          'budgets':{'triangles_per_variant':10000,'bones_per_variant':40,'texture_px':[1024,1024]}}


for sex,profile in VARIANTS.items():
    SL=profile['sl_bu'];female=sex=='female'
    collection=bpy.data.collections.new('Gambusia_'+sex);scene.collection.children.link(collection)
    arm=bpy.data.armatures.new('Armature_'+sex);rig=bpy.data.objects.new('Rig_'+sex,arm);collection.objects.link(rig);rig.parent=visual
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,head,parent=None):
        b=arm.edit_bones.new(name);b.head=Vector(head)*SL;b.tail=b.head+Vector((0,.04*SL,0))
        if parent:b.parent=arm.edit_bones[parent]
    bone('Root',(0,0,0));bone('fish_body',(0,0,0),'Root');bone('head',(-.35,0,0),'fish_body')
    centers=[(-.35,'head'),(-.18,'spine_01'),(0,'spine_02'),(.18,'spine_03'),(.32,'spine_04'),(.46,'tail_peduncle')]
    parent='fish_body'
    for x,name in centers[1:]:bone(name,(x,0,0),parent);parent=name
    bone('caudal_fin',(.50,0,0),'tail_peduncle')
    bone('dorsal_fin',(.20,0,.12),'spine_03');bone('anal_fin',(.06,0,-.17 if female else -.12),'spine_02')
    for side,sign in (('L',1),('R',-1)):
        bone('pectoral_'+side,(-.26,sign*.10,-.015),'head')
        bone('pelvic_'+side,(-.12,sign*.07,-.20 if female else -.14),'spine_02')
        bone('operculum_'+side,(-.30,sign*.12,0),'head')
        bone('eye_'+side,(-.38,sign*.12,.065),'head')
    for name in ('jaw_upper_ctrl','jaw_lower_ctrl'):bone(name,(-.4,0,.035),'head')
    bone('mouth_tip',(-.496,0,.065),'jaw_upper_ctrl');bone('body_ref',(0,0,0),'fish_body')
    bone('attack_socket',(-.496,0,.065),'jaw_upper_ctrl')
    bone('SL_snout',(-.5,0,.065),'head');bone('SL_tail',(.5,0,0),'tail_peduncle')
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in rig.pose.bones:b.rotation_mode='XYZ'
    vertices=[];faces=[];uvfaces=[];slots=[];weights=[];parts=[]
    def add_part(name,points,polygons,uvs,weight,slot):
        first=len(vertices);vertices.extend([tuple(Vector(p)*SL) for p in points])
        weights.extend([weight(p) if callable(weight) else {weight:1.} for p in points])
        for polygon in polygons:
            faces.append(tuple(first+i for i in polygon));uvfaces.append([uvs[i] for i in polygon]);slots.append(slot)
        parts.append({'name':name,'first_vertex':first,'vertex_count':len(points),'material':slot})
    def body_weights(p):
        x=p[0]
        if x<=centers[0][0]:return {centers[0][1]:1}
        for (a,n),(b,m) in zip(centers,centers[1:]):
            if x<=b:
                t=(x-a)/(b-a);return {n:1-t,m:t}
        return {centers[-1][1]:1}
    rings=[(-.487,.018,.055,.012),(-.465,.043,.075,.035),(-.43,.075,.09,.07),(-.37,.13,.12,.11),(-.29,.17,.15,.18),
           (-.18,.17,.16,.22),(-.04,.145,.15,.23),(.10,.115,.13,.20),(.22,.085,.10,.14),
           (.33,.060,.070,.080),(.43,.045,.055,.060),(.50,.040,.045,.045)]
    original_rings=np.array(rings)
    def rounded(values,steps=3):
        values=np.array(values,dtype=float);result=[]
        for i in range(len(values)-1):
            a,b,c,d=values[max(0,i-1)],values[i],values[i+1],values[min(len(values)-1,i+2)]
            for t in np.linspace(0,1,steps,endpoint=False):
                result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
        return [tuple(p) for p in result]+[tuple(values[-1])]
    rings=rounded(rings)
    def body_surface(x,z,side):
        width=np.interp(x,original_rings[:,0],original_rings[:,1])*(1 if female else .78)
        height=np.interp(x,original_rings[:,0],original_rings[:,2 if z>=0 else 3])*(1 if female else .72)
        return side*width*math.sqrt(max(.01,1-(z/height)**2))
    n=20;points=[];uv=[];polys=[]
    for x,width,top,bottom in rings:
        for j in range(n+1):
            theta=math.tau*j/n;c=math.cos(theta)
            points.append((x,math.sin(theta)*width*(1 if female else .78),c*(top if c>=0 else bottom)*(1 if female else .72)))
            uv.append((.02+(x+.5)*.69,.02+.96*j/n))
    for r in range(len(rings)-1):
        for j in range(n):
            a=r*(n+1)+j;b=a+n+1;polys.append((a,b,b+1,a+1))
    polys.extend([tuple(range(n)),tuple((len(rings)-1)*(n+1)+j for j in reversed(range(n)))])
    add_part('body_head_continuous',points,polys,uv,body_weights,0)
    body_vertex_count=len(vertices)
    def ellipsoid(name,center,radii,weight,slot=0,tile=(.76,.02,.10,.18),segments=16,rings_count=8):
        pts=[];uvs=[];polys=[]
        for r in range(rings_count+1):
            theta=math.pi*(r+.001)/(rings_count+.002)
            for j in range(segments+1):
                angle=math.tau*j/segments
                q=(math.sin(theta)*math.cos(angle),math.sin(theta)*math.sin(angle),math.cos(theta))
                pts.append(tuple(center[k]+radii[k]*q[k] for k in range(3)))
                uvs.append((tile[0]+tile[2]*j/segments,tile[1]+tile[3]*r/rings_count))
        for r in range(rings_count):
            for j in range(segments):
                a=r*(segments+1)+j;b=a+segments+1;polys.append((a,b,b+1,a+1))
        add_part(name,pts,polys,uvs,weight,slot)
    def fin(name,center,rim,weight):
        rim=rounded(rim,2);count=len(rim)
        normal=(Vector(rim[1])-Vector(center)).cross(Vector(rim[-2])-Vector(center)).normalized()*.0008
        points=[];uvs=[];polys=[]
        for sign in (-1,1):
            for distance in (.015,.34,.67,1):
                for i,p in enumerate(rim):
                    point=Vector(center)+(Vector(p)-Vector(center))*distance+normal*sign
                    points.append(tuple(point));uvs.append((.76+.22*i/(count-1),.66+.30*distance))
        side=count*4
        for layer in range(2):
            for row in range(3):
                for i in range(count-1):
                    a=layer*side+row*count+i;b=a+count
                    face=(a,a+1,b+1,b);polys.append(face if layer else tuple(reversed(face)))
        boundary=list(range(count))+[r*count+count-1 for r in range(1,4)]+list(reversed(range(3*count,4*count-1)))+[r*count for r in (2,1)]
        for i,a in enumerate(boundary):
            b=boundary[(i+1)%len(boundary)];polys.append((a,b,side+b,side+a))
        add_part(name,points,polys,uvs,weight,1)
    tailrim=[(.48,0,-.035)]+[(.54+.19*math.cos(t),0,.18*math.sin(t)) for t in np.linspace(-1.15,1.15,9)]+[(.48,0,.035)]
    fin('caudal_fin',(.485,0,0),tailrim,'caudal_fin')
    dorsal=[(.19,0,.07),(.22,0,.20),(.27,0,.245),(.32,0,.255),(.37,0,.23),(.40,0,.18),(.43,0,.035)]
    dorsal=[(x,y,z*(1 if female else .75)) for x,y,z in dorsal]
    fin('dorsal_fin',(.27,0,.075*(1 if female else .75)),dorsal,'dorsal_fin')
    if female:
        fin('anal_fin',(.13,0,-.16),[(.065,0,-.19),(.10,0,-.28),(.16,0,-.30),(.23,0,-.26),(.28,0,-.13)],'anal_fin')
    else:
        ellipsoid('gonopodium',(.20,0,-.15),(.155,.012,.018),'anal_fin',1,tile=(.78,.70,.18,.20),segments=12,rings_count=6)
    for side,sign in (('L',1),('R',-1)):
        factor=1 if female else .78
        fin('pectoral_'+side,(-.26,sign*.12*factor,-.02),[(-.26,sign*.13*factor,.01),(-.15,sign*.20*factor,.04),(-.09,sign*.21*factor,.005),(-.11,sign*.19*factor,-.065),(-.24,sign*.13*factor,-.06)],'pectoral_'+side)
        z=-.20 if female else -.14
        fin('pelvic_'+side,(-.12,sign*.07,z),[(-.14,sign*.06,z-.01),(-.10,sign*.14,z-.09),(-.05,sign*.14,z-.11),(-.03,sign*.10,z-.08),(-.07,sign*.05,z-.02)],'pelvic_'+side)
        pts=[];uvs=[];polys=[]
        for r in (.01,.33,.66,1):
            for j in range(21):
                angle=math.tau*j/20;x=-.285+.065*r*math.cos(angle);z=-.005+.10*r*math.sin(angle)*(1 if female else .72)
                y=body_surface(x,z,sign)+sign*(.0025+.008*(1-r*r))
                pts.append((x,y,z))
                height=np.interp(x,original_rings[:,0],original_rings[:,2 if z>=0 else 3])*(1 if female else .72)
                theta=math.acos(max(-1,min(1,z/height)));theta=theta if sign>0 else math.tau-theta
                uvs.append((.02+(x+.5)*.69,.5+(.02+.96*theta/math.tau-.5)*.72))
        for r in range(3):
            for j in range(20):
                a=r*21+j;b=a+21;polys.append((a,a+1,b+1,b) if sign>0 else (a,b,b+1,a+1))
        add_part('operculum_'+side,pts,polys,uvs,'operculum_'+side,0)
        crease=[]
        for angle in np.linspace(-1.2,1.25,14):
            x=-.285+.065*math.cos(angle);z=-.005+.10*math.sin(angle)*(1 if female else .72)
            crease.append(Vector((x,body_surface(x,z,sign)+sign*.004,z)))
        points=[];uvs=[];polys=[]
        for i,p in enumerate(crease):
            tangent=(crease[min(i+1,len(crease)-1)]-crease[max(0,i-1)]).normalized()
            first=tangent.cross(Vector((0,1,0))).normalized();second=tangent.cross(first).normalized()
            for j in range(6):
                points.append(tuple(p+.0028*(first*math.cos(math.tau*j/6)+second*math.sin(math.tau*j/6))))
                uvs.append((.80,.30))
        for i in range(len(crease)-1):
            for j in range(6):polys.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
        add_part('operculum_crease_'+side,points,polys,uvs,'operculum_'+side,0)
        ez=.075*(1 if female else .72);ey=body_surface(-.37,ez,sign)+sign*.002
        ellipsoid('eye_'+side,(-.37,ey,ez),(.050,.024,.047),'eye_'+side,2,tile=(.76,.44,.22,.18))
    ellipsoid('mouth_cavity',(-.474,0,.059),(.016,.022,.012),'head',3,tile=(.90,.02,.06,.10))
    for name,tip,height in [('jaw_upper',-.496,.065),('jaw_lower',-.500,.058)]:
        pts=[];uvs=[];polys=[]
        for r,(x,width,thickness) in enumerate([(tip,.008,.002),(-.487,.020,.003),(-.465,.032,.004),(-.445,.040,.006)]):
            z=height*(1-r/4)+.035*r/4
            for j in range(17):
                theta=math.tau*j/16;pts.append((x,width*math.sin(theta),z+thickness*math.cos(theta)))
                uvs.append((.76+.10*j/16,.02+.18*r/3))
        for r in range(3):
            for j in range(16):
                a=r*17+j;b=a+17;polys.append((a,b,b+1,a+1))
        polys.extend([tuple(range(16)),tuple(51+j for j in reversed(range(16)))])
        add_part(name,pts,polys,uvs,name+'_ctrl',0)
    mesh=bpy.data.meshes.new('Mesh_'+sex);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new('Fish_'+sex,mesh);collection.objects.link(obj);obj.parent=rig
    uvmap=mesh.uv_layers.new(name='UVMap')
    for polygon,uvs,slot in zip(mesh.polygons,uvfaces,slots):
        polygon.material_index=slot;polygon.use_smooth=True
        for loop,value in zip(polygon.loop_indices,uvs):uvmap.data[loop].uv=value
    for b in arm.bones:obj.vertex_groups.new(name=b.name)
    for i,values in enumerate(weights):
        for group,value in values.items():
            if value>0:obj.vertex_groups[group].add([i],float(value),'REPLACE')
    mod=obj.modifiers.new('Editable skeleton','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
    yy,xx=np.mgrid[0:1024,0:1024];u=xx/1023;v=yy/1023
    dorsal=np.clip((np.cos((v-.02)/.96*math.tau)+.15)/1.15,0,1)
    belly=np.clip((-np.cos((v-.02)/.96*math.tau)-.15)/.85,0,1)
    side_color=np.array([.60,.64,.62]);back=np.array([.40,.42,.31]);white=np.array([.82,.82,.74])
    rgb=side_color[None,None,:]*(1-dorsal[:,:,None])+back*dorsal[:,:,None]
    rgb=rgb*(1-belly[:,:,None])+white*belly[:,:,None]
    pattern=(np.cos(31*u+2*np.sin(8*v))*np.cos(22*v+4*u))*.022
    rgb+=pattern[:,:,None]
    if female:
        spot=np.exp(-((u-.44)/.045)**2)*sum(np.exp(-((v-a)/.065)**2) for a in (.36,.64))
        rgb*=1-.48*spot[:,:,None]
    rgb[u>.73]=[.72,.72,.63]
    rgb[(u>.76)&(u<.86)&(v>.24)&(v<.42)]=[.45,.49,.46]
    fin_region=(u>.74)&(v>.64)
    ray_angle=(u-.76)/.22;radial=(v-.66)/.30
    rays=.12*np.maximum(0,np.cos(ray_angle*math.tau*8))**24*np.clip(radial,0,1)
    dots=np.zeros_like(u)
    for angle,distance in ((.13,.70),(.30,.87),(.47,.73),(.64,.90),(.81,.70)):
        dots+=.12*np.exp(-((ray_angle-angle)/.018)**2-((radial-distance)/.045)**2)
    rgb[fin_region]=np.stack([.72-rays-dots,.73-rays-dots,.66-rays-dots],axis=-1)[fin_region]
    eyes=(u>.74)&(v>.43)&(v<.63);rgb[eyes]=[.035,.045,.055]
    cavity=(u>.89)&(v<.14);rgb[cavity]=[.06,.05,.05]
    rgba=np.concatenate((np.clip(rgb,0,1),np.ones((1024,1024,1))),axis=-1)
    texture_path=ROOT/f'3D/textures/gambusia_{sex}_basecolor_r03.png'
    png(texture_path,np.flipud(np.rint(rgba*255).astype(np.uint8)),True)
    from imagegen_surface import texture as imagegen_texture
    texture,_=imagegen_texture(ROOT,sex)
    for name,roughness,opacity in [('Body',.73,1),('Fins',.56,.84),('Eyes',.35,1),('Mouth',.85,1)]:
        material=bpy.data.materials.new(sex+'_'+name);material.use_nodes=True;material['roughness']=roughness;material['opacity']=opacity
        material.diffuse_color=(.6,.64,.62,opacity)
        nodes=material.node_tree.nodes;links=material.node_tree.links
        shader=nodes['Principled BSDF'];shader.inputs['Roughness'].default_value=roughness
        node=nodes.new('ShaderNodeTexImage');node.image=texture;node.name='Baked_BaseColor';links.new(node.outputs['Color'],shader.inputs['Base Color'])
        if name=='Body':
            toon=nodes.new('ShaderNodeBsdfToon');toon.name='NPR_Toon';toon.inputs['Size'].default_value=.55;toon.inputs['Smooth'].default_value=.035
            links.new(node.outputs['Color'],toon.inputs['Color']);links.new(toon.outputs[0],nodes['Material Output'].inputs['Surface'])
        if name=='Fins':shader.inputs['Alpha'].default_value=opacity
        mesh.materials.append(material)
    for action in DESIGNS:
        for phase in PHASES:
            rig.animation_data_clear();duration=phase_duration(action,phase)
            for i in range(25):
                fraction=i/24
                values=pose(action,phase,fraction)
                for b in rig.pose.bones:
                    b.rotation_euler=values.get(b.name,(0,0,0));b.location=(0,0,0);b.scale=(1,1,1)
                    b.keyframe_insert('rotation_euler',frame=1+duration*60*fraction)
            clip=rig.animation_data.action;clip.name=f'GH_{sex}_{action}_{phase}_r03';clip.use_fake_user=True;clip['duration_s']=duration
            loop=phase=='mid' and action in LOOPS
            for layer in clip.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            keys=curve.keyframe_points;step=duration*60/24
                            for i,key in enumerate(keys):
                                slope=(keys[(i+1)%24].co.y-keys[(i-1)%24].co.y)/(2*step) if loop else (keys[min(24,i+1)].co.y-keys[max(0,i-1)].co.y)/(2*step) if 0<i<24 else 0
                                key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='FREE'
                                key.handle_left=(key.co.x-step/3,key.co.y-slope*step/3);key.handle_right=(key.co.x+step/3,key.co.y+slope*step/3)
    mesh.calc_loop_triangles()
    assert len(mesh.loop_triangles)<=10000 and len(arm.bones)<=40
    sheet=bpy.data.images.load(str(ROOT/f'sheet/gambusia_{sex}_sheet_r01.png'));sheet.name='Reference_'+sex;sheet.pack();sheet.filepath='//../sheet/gambusia_'+sex+'_sheet_r01.png'
    ref=bpy.data.objects.new('Reference_'+sex,None);collection.objects.link(ref);ref.empty_display_type='IMAGE';ref.data=sheet;ref.hide_render=True;ref.location=(0,4*SL,0);ref.empty_display_size=SL
    manifest['variants'][sex]={**profile,'rig':rig.name,'mesh':obj.name,'parts':parts,'body_vertices':body_vertex_count,
       'triangles':len(mesh.loop_triangles),'bones':len(arm.bones),'vertices':len(mesh.vertices),
       'SL_bu':SL,'TL_bu':(max(p[0] for p in vertices)-min(p[0] for p in vertices)),
       'sheet_sha256':hashlib.sha256((ROOT/f'sheet/gambusia_{sex}_sheet_r01.png').read_bytes()).hexdigest()}
    rig.select_set(False)

camdata=bpy.data.cameras.new('Orthographic');cam=bpy.data.objects.new('Orthographic',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=8.9;cam.location=(-5,-12,5);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
for name,position,power,size in [('Key',(-5,-5,10),1600,8),('Fill',(4,4,7),1100,7),('FrontFill',(-3,-8,1),1100,10),('BellyFill',(0,-4,-7),900,8)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=960;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.film_transparent=True
text=bpy.data.texts.new('ASSET_MANIFEST.json');text.write(json.dumps(manifest,indent=2))
for path in [Path(__file__),ROOT/'3D/tools/select_pose.py',ROOT/'runtime/motion_spec.py',ROOT/'3D/tools/export_fish.py',ROOT/'3D/tools/verify_fish.py',ROOT/'3D/tools/imagegen_surface.py']:
    bpy.data.texts.load(str(path))
from select_pose import select_pose
select_pose()
scene.frame_end=97
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'3D/gambusia_holbrooki_r03.blend'))
(ROOT/'3D/model_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for sex in VARIANTS:
    select_pose(sex);camdata.ortho_scale=VARIANTS[sex]['sl_bu']*1.55
    scene.render.filepath=str(ROOT/f'3D/model_{sex}.png');bpy.ops.render.render(write_still=True)
print('PASS two models / 96 Actions / editable UV rig')
