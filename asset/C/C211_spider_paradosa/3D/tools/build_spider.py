"""Build the C211 design prototype in an isolated Blender process."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / '3D'
TAU = 2 * math.pi
SCALE = .965396 * 5 / 2.25


def make_material(name, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = 0
    material['roughness'] = roughness
    return material


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'C211_Pardosa_Idle_r02'
scene.unit_settings.system = 'NONE'
scene.render.fps = 48
scene.frame_start = 1
scene.frame_end = 96
physics = bpy.data.objects.new('physics_root', None)
scene.collection.objects.link(physics)
visual = bpy.data.objects.new('visual_root', None)
scene.collection.objects.link(visual)
visual.parent = physics
arm = bpy.data.armatures.new('Pardosa_Skeleton')
rig = bpy.data.objects.new('Pardosa_Rig', arm)
scene.collection.objects.link(rig)
rig.parent = visual
rig.show_in_front = True
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')


def bone(name, head, tail, parent=None):
    item = arm.edit_bones.new(name)
    item.head, item.tail = head, tail
    if parent:
        item.parent = arm.edit_bones[parent]
    return item


bone('Root', (0, 0, 0), (0, 0, .18))
bone('cephalothorax', (0, -.48, .56), (0, -.83, .56), 'Root')
bone('abdomen', (0, .08, .56), (0, .66, .6), 'cephalothorax')
leg_paths = {}
segment_names = ('coxa', 'trochanter', 'femur', 'patella', 'tibia', 'metatarsus', 'tarsus')
for side, sign in (('L', 1), ('R', -1)):
    for index, (hip_y, knee_x, knee_y, foot_x, foot_y) in enumerate((
        (-.76, .89, -1.12, 1.28, -1.58),
        (-.53, 1.13, -.63, 1.66, -.92),
        (-.29, 1.16, .08, 1.77, .32),
        (-.08, 1.00, .66, 1.48, 1.27)), 1):
        label = f'{side}{index}'
        hip = Vector((sign * .34, hip_y, .49))
        knee = Vector((sign * knee_x, knee_y, .76))
        toe = Vector((sign * foot_x, foot_y, .026))
        upper = knee - hip
        lower = toe - knee
        points = [hip, hip + upper * .14, hip + upper * .23, knee,
                  knee + lower * .13, knee + lower * .63, knee + lower * .87, toe]
        leg_paths[label] = points
        parent = 'cephalothorax'
        for segment, (a, b) in zip(segment_names, zip(points, points[1:])):
            name = f'leg_{label}_{segment}'
            bone(name, a, b, parent)
            parent = name
        target = bone(f'foot_IK_{label}', toe, toe + Vector((0, 0, .12)), 'Root')
        target.use_deform = False
for side, sign in (('L', 1), ('R', -1)):
    a, b, c = (sign * .25, -.87, .43), (sign * .30, -1.10, .35), (sign * .25, -1.23, .25)
    bone(f'pedipalp_{side}', a, b, 'cephalothorax')
    bone(f'pedipalp_tip_{side}', b, c, f'pedipalp_{side}')
    bone(f'chelicera_{side}', (sign * .11, -.91, .38), (sign * .11, -1.05, .27), 'cephalothorax')
    bone(f'fang_{side}', (sign * .11, -1.05, .27), (sign * .07, -1.11, .20), f'chelicera_{side}')
    bone(f'spinneret_{side}', (sign * .08, 1.16, .39), (sign * .08, 1.30, .34), 'abdomen')
bpy.ops.object.mode_set(mode='OBJECT')
for label in leg_paths:
    constraint = rig.pose.bones[f'leg_{label}_tarsus'].constraints.new('IK')
    constraint.name = 'Planted foot'
    constraint.target = rig
    constraint.subtarget = f'foot_IK_{label}'
    constraint.chain_count = 7
    constraint.iterations = 128
    constraint.use_stretch = False
for pose_bone in rig.pose.bones:
    pose_bone.rotation_mode = 'XYZ'
    pose_bone.ik_stretch = 0

materials = [make_material('Pardosa_Carapace', .77), make_material('Pardosa_Abdomen', .84),
             make_material('Pardosa_Eyes', .48), make_material('Pardosa_Limbs', .77)]
vertices, faces, face_uvs, material_ids, weights, parts = [], [], [], [], [], []
texture = np.ones((1024, 1024, 4), dtype=np.float32)
texture[:, :, :3] = (.16, .10, .065)
tiles = 12


def ellipsoid(name, center, scale, group, kind='limb', rotation=None, segments=12, rings=8):
    """Closed UV ellipsoid with a separate padded atlas island per part."""
    part = len(parts)
    assert part < tiles * tiles
    col, row = part % tiles, part // tiles
    x0, y0 = col * 84 + 4, row * 84 + 4
    yy, xx = np.mgrid[0:80, 0:80]
    u, v = xx / 79, yy / 79
    phi, theta = TAU * u, math.pi * v
    color = np.empty((80, 80, 3), dtype=np.float32)
    color[:] = (.53, .45, .37)
    if kind == 'body':
        color[:] = (.48, .39, .31)
        stripe = (np.abs(np.cos(phi)) < .22) & (v < .53)
        color[stripe] = (.65, .57, .46)
    elif kind == 'abdomen':
        color[:] = (.42, .35, .29)
        mottles = np.sin(phi * 3 + np.cos(theta * 2)) * np.cos(theta * 4) > .72
        color[mottles] = (.49, .42, .34)
        heart = (np.abs(np.cos(phi)) < (.26 - .15 * np.cos(theta * 2))) & (v < .38)
        color[heart] = (.35, .29, .24)
    elif kind == 'eye':
        color[:] = (.018, .012, .009)
    elif kind == 'dark':
        color[:] = (.23, .19, .16)
    else:
        color[(v > .38) & (v < .58)] = (.43, .36, .30)
    if kind != 'eye':
        grain = np.sin(xx * .12 + yy * .15) * np.cos(xx * .08 - yy * .11) * .006
        color += grain[:, :, None]
    texture[y0:y0+80, x0:x0+80, :3] = np.clip(color, 0, 1)
    texture[y0-2:y0+82, x0-2:x0+82] = np.pad(texture[y0:y0+80, x0:x0+80], ((2, 2), (2, 2), (0, 0)), mode='edge')
    start = len(vertices)
    center, scale = Vector(center), Vector(scale)
    local = [Vector((0, 0, scale.z))]
    for j in range(1, rings):
        theta = math.pi * j / rings
        for i in range(segments):
            phi = TAU * i / segments
            local.append(Vector((scale.x * math.sin(theta) * math.cos(phi),
                                 scale.y * math.sin(theta) * math.sin(phi), scale.z * math.cos(theta))))
    local.append(Vector((0, 0, -scale.z)))
    vertices.extend(tuple(center + (rotation @ p if rotation else p)) for p in local)
    weights.extend([group] * len(local))
    part_faces, part_uvs = [], []
    for i in range(segments):
        ni = (i + 1) % segments
        part_faces.append((0, 1+i, 1+ni))
        part_uvs.append(((i+.5)/segments, 0, i/segments, 1/rings, (i+1)/segments, 1/rings))
        for j in range(rings-2):
            a, b = 1+j*segments+i, 1+j*segments+ni
            part_faces.append((a, a+segments, b+segments, b))
            part_uvs.append((i/segments,(j+1)/rings,i/segments,(j+2)/rings,(i+1)/segments,(j+2)/rings,(i+1)/segments,(j+1)/rings))
        a, b = 1+(rings-2)*segments+i, 1+(rings-2)*segments+ni
        part_faces.append((a, len(local)-1, b))
        part_uvs.append((i/segments,(rings-1)/rings,(i+.5)/segments,1,(i+1)/segments,(rings-1)/rings))
    material = {'body':0,'abdomen':1,'eye':2}.get(kind,3)
    for face, uv in zip(part_faces,part_uvs):
        faces.append(tuple(start + i for i in face))
        face_uvs.append([((x0 + 79*uv[k])/1024, (y0 + 79*uv[k+1])/1024) for k in range(0,len(uv),2)])
        material_ids.append(material)
    parts.append({'name':name,'bone':group,'first_vertex':start,'vertex_count':len(local),'tile':[x0,y0,80,80]})


def segment(name, a, b, radius, group, kind='limb'):
    a, b = Vector(a), Vector(b)
    direction = b - a
    ellipsoid(name, (a+b)/2, (radius,radius,direction.length*.5+radius*.55), group, kind,
              direction.to_track_quat('Z','Y'), segments=8, rings=6)


ellipsoid('cephalothorax', (0,-.48,.56), (.47,.52,.31), 'cephalothorax','body',segments=24,rings=16)
ellipsoid('abdomen', (0,.60,.59), (.55,.65,.41), 'abdomen','abdomen',segments=24,rings=16)
ellipsoid('pedicel', (0,.065,.53), (.11,.16,.10), 'abdomen','dark')
for label, points in leg_paths.items():
    for i, (name,a,b) in enumerate(zip(segment_names,points,points[1:])):
        segment(f'leg_{label}_{name}',a,b,(.090,.085,.081,.081,.065,.045,.031)[i],f'leg_{label}_{name}')
for side, sign in (('L',1),('R',-1)):
    for name,radius,kind in ((f'pedipalp_{side}',.065,'limb'),(f'pedipalp_tip_{side}',.058,'limb'),
                             (f'chelicera_{side}',.075,'limb'),(f'fang_{side}',.024,'dark'),
                             (f'spinneret_{side}',.035,'limb')):
        b=arm.bones[name]
        segment(name,b.head_local,b.tail_local,radius,name,kind)
eye_centers=[]
for index,x in enumerate((-.19,-.065,.065,.19)):
    eye_centers.append((f'eye_anterior_{index+1}',(x,-.972,.60),(.036,.029,.036)))
for side,sign in (('L',1),('R',-1)):
    eye_centers.append((f'eye_PME_{side}',(sign*.125,-.928,.745),(.086,.065,.087)))
    eye_centers.append((f'eye_PLE_{side}',(sign*.292,-.704,.782),(.057,.053,.057)))
for name,center,scale in eye_centers:
    ellipsoid(name,center,scale,'cephalothorax','eye',segments=16,rings=10)

mesh=bpy.data.meshes.new('Pardosa_SkinnedMesh')
mesh.from_pydata(vertices,[],faces)
mesh.update()
skin=bpy.data.objects.new('Pardosa_Skinned',mesh)
scene.collection.objects.link(skin)
skin.parent=rig
for material in materials:
    mesh.materials.append(material)
uv_layer=mesh.uv_layers.new(name='UVMap')
for polygon,uvs,material in zip(mesh.polygons,face_uvs,material_ids):
    polygon.material_index=material
    polygon.use_smooth=True
    for loop,uv in zip(polygon.loop_indices,uvs):
        uv_layer.data[loop].uv=uv
for name in sorted(set(weights)):
    group=skin.vertex_groups.new(name=name)
    group.add([i for i,w in enumerate(weights) if w==name],1.0,'REPLACE')
modifier=skin.modifiers.new('Deform','ARMATURE')
modifier.object=rig
mesh.transform(Matrix.Scale(SCALE,4))
arm.transform(Matrix.Scale(SCALE,4))
leg_paths={label:[p*SCALE for p in points] for label,points in leg_paths.items()}
ground_offset=min(vertex.co.z for vertex in mesh.vertices)
ground_transform=Matrix.Translation((0,0,-ground_offset))
mesh.transform(ground_transform)
arm.transform(ground_transform)
leg_paths={label:[ground_transform@p for p in points] for label,points in leg_paths.items()}
image=bpy.data.images.new('T_Pardosa_BaseColor_r02',1024,1024,alpha=True)
image.colorspace_settings.name='sRGB'
image.pixels.foreach_set(texture.ravel())
image.filepath_raw=str(DEST/'textures/spider_pardosa_basecolor_r02.png')
image.file_format='PNG'
image.save()
image.pack()
image.filepath='//textures/spider_pardosa_basecolor_r02.png'
for material in materials:
    node=material.node_tree.nodes.new('ShaderNodeTexImage')
    node.name='Baked_BaseColor'
    node.image=image
    material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    if material.name != 'Pardosa_Eyes':
        toon=material.node_tree.nodes.new('ShaderNodeBsdfToon')
        toon.name='NPR_Toon'
        toon.inputs['Size'].default_value=.55
        toon.inputs['Smooth'].default_value=.035
        material.node_tree.links.new(node.outputs['Color'],toon.inputs['Color'])
        material.node_tree.links.new(toon.outputs[0],material.node_tree.nodes['Material Output'].inputs['Surface'])

for frame in range(1,98,4):
    phase=TAU*(frame-1)/96
    body=rig.pose.bones['cephalothorax']
    body.location=(SCALE*.004*math.sin(phase),0,SCALE*.010*(1-math.cos(phase)))
    body.rotation_euler=(0,.014*math.sin(phase),.020*math.sin(phase))
    body.keyframe_insert('location',frame=frame)
    body.keyframe_insert('rotation_euler',frame=frame)
    abdomen=rig.pose.bones['abdomen']
    abdomen.rotation_euler=(.018*math.sin(phase),0,0)
    abdomen.keyframe_insert('rotation_euler',frame=frame)
    for side,sign in (('L',1),('R',-1)):
        palp=rig.pose.bones[f'pedipalp_{side}']
        palp.rotation_euler=(.05*math.sin(2*phase),0,sign*.08*math.sin(phase))
        palp.keyframe_insert('rotation_euler',frame=frame)
action=rig.animation_data.action
action.name='C211_idle_scan_mid_r02'
action.use_fake_user=True
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                keys=curve.keyframe_points
                for i,key in enumerate(keys):
                    previous=keys[i-1] if i>0 else keys[-2]
                    following=keys[i+1] if i<len(keys)-1 else keys[1]
                    before=previous.co.x if i>0 else previous.co.x-96
                    after=following.co.x if i<len(keys)-1 else following.co.x+96
                    slope=(following.co.y-previous.co.y)/(after-before)
                    key.interpolation='BEZIER'
                    key.handle_left_type=key.handle_right_type='FREE'
                    key.handle_left=(key.co.x-4/3,key.co.y-slope*4/3)
                    key.handle_right=(key.co.x+4/3,key.co.y+slope*4/3)
scene.frame_set(1)

camera_data=bpy.data.cameras.new('Pardosa_Orthographic')
camera=bpy.data.objects.new('Pardosa_Orthographic',camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera.location=Vector((4,-6,3.2))*SCALE
camera.rotation_euler=(Vector((0,0,.36*SCALE))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO'
camera_data.ortho_scale=4.2*SCALE
scene.render.resolution_x=scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.view_settings.view_transform='AgX'
scene.view_settings.look='None'
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
world=bpy.data.worlds.new('Pardosa_Studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.45,.45,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.5
scene.world=world
for name,location,power,size in (('Key',(-3,-4,6),500,4),('Fill',(4,-1,3),220,4),('Rim',(0,4,5),350,3)):
    data=bpy.data.lights.new(name,'AREA')
    data.energy,data.shape,data.size=power*SCALE*SCALE,'DISK',size*SCALE
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location=Vector(location)*SCALE
    obj.rotation_euler=(Vector((0,0,.4*SCALE))-obj.location).to_track_quat('-Z','Y').to_euler()

reference=bpy.data.objects.new('Reference_approved_sheet_r02',None)
scene.collection.objects.link(reference)
reference.empty_display_type='IMAGE'
reference.data=bpy.data.images.load(str(ROOT/'sheet/spider_pardosa_sheet_r02.png'))
reference.data.pack()
reference.data.filepath='//../sheet/spider_pardosa_sheet_r02.png'
reference.empty_display_size=5
reference.location=(0,4,2)
reference.hide_render=True
reference.hide_set(True)

manifest={
    'asset_id':'C211_spider_paradosa','object_id':'spider_pardosa','revision':'idle-r02',
    'taxon':'Pardosa agrestis','stage':'adult','sex':'female',
    'biological_body_length_mm':5.0,'relative_size_to_toktogi':5.0,
    'design_body_length_bu':4.82698,'status':'asset_experiment','production_export_allowed':False,
    'size_profile':json.loads((ROOT/'document/source_contract.json').read_text(encoding='utf-8'))['selection'],
    'style_reference':'C011 integrated-r5, AssetPipeLine v2.2',
    'ground_alignment_offset_bu':ground_offset,
    'preview_surface':{'body_shader':'NPR_Toon','size':.55,'smooth':.035,'eye_roughness':.48,
                       'color_management':'AgX / None','lighting':'isolated proportional studio; shared game lighting verified in comparison'},
    'motion_design':{'easing':'periodic cubic Hermite via Bezier handles','cycle_s':2,
                     'reference_idle_s':1.6,'body_lateral_amplitude_bu':.004*SCALE,
                     'body_height_range_bu':.020*SCALE,'body_yaw_rad':.020,
                     'palp_yaw_rad':.08,'palp_double_frequency':True},
    'coordinate_contract':'DEC-06-deferred','front_axis':'-Y','up_axis':'+Z','left_axis':'+X',
    'physics_owner':'simulation','effect_owner':'simulation','effects':[],
    'parts':parts,'leg_paths':{k:[list(v) for v in p] for k,p in leg_paths.items()},
    'eye_layout':[4,2,2],'budgets':{'triangles':16000,'bones':96,'texture':[1024,1024]},
    'clip':{'state':'idle_scan','id':'idle_scan','phase':'mid','loop':True,'duration_s':2,
            'action':action.name,'native_fps':48,'frame_start':1,'loop_endpoint':97,
            'playback_frames':96,'sample_count':24,'sample_fps':12,'pre_end':'neutral boundary pose shared at frame 1'},
    'sheet_sha256':hashlib.sha256((ROOT/'sheet/spider_pardosa_sheet_r02.png').read_bytes()).hexdigest(),
    'blender_version':bpy.app.version_string,
}
mesh.calc_loop_triangles()
manifest['measured']={'triangles':len(mesh.loop_triangles),'vertices':len(mesh.vertices),'bones':len(arm.bones)}
assert manifest['measured']['triangles']<=16000 and len(arm.bones)<=96
assert len(eye_centers)==8 and len(leg_paths)==8
text=bpy.data.texts.new('ASSET_MANIFEST.json')
text.write(json.dumps(manifest,ensure_ascii=False,indent=2))
for name in ('build_spider.py','export_idle.py','verify_saved.py','png_codec.py','select_idle.py'):
    source=DEST/'tools'/name
    if source.exists():
        bpy.data.texts.load(str(source))
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=5
        area.spaces.active.region_3d.view_location=(0,0,.4)
bpy.context.view_layer.objects.active=rig
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'spider_pardosa_idle_r02.blend'))
(DEST/'model_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.filepath=str(DEST/'model_preview.png')
bpy.ops.render.render(write_still=True)
result=manifest['measured']
