"""C211 evaluated mesh to aligned Sprite/Base/Normal/AO/RM/Emissive passes."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector, Euler, geometry
from mathutils.bvhtree import BVHTree

ROOT = Path(bpy.data.filepath).resolve().parents[1]
sys.path.insert(0, str(ROOT / '3D/tools'))
from png_codec import png, apng, linear_to_srgb, srgb_to_linear
from select_idle import select_idle

OUT = ROOT / '2D/idle-r02'
OUT.mkdir(parents=True, exist_ok=True)
SIZE, PADDING, COLUMNS = 640, 2, 6
CELL = SIZE + 2 * PADDING
scene = bpy.context.scene
skin = bpy.data.objects['Pardosa_Skinned']
rig = bpy.data.objects['Pardosa_Rig']
camera = scene.camera
camera.data.ortho_scale = SIZE * 1.78 / 128
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.resolution_percentage = 100
texture = bpy.data.images['T_Pardosa_BaseColor_r02']
pixels = np.empty(1024*1024*4, dtype=np.float32)
texture.pixels.foreach_get(pixels)
pixels = pixels.reshape(1024,1024,4)
model = json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string())
pass_names = ('sprite','base','normal','ao','rm','emissive')
manifest = {k:v for k,v in model.items() if k not in ('parts','leg_paths')}
manifest.update({
    'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
    'generator':'evaluated mesh, deterministic orthographic pixel-center BVH rays; C011 PNG codec',
    'layout':{'cell_size':[SIZE,SIZE],'padding_px':PADDING,'filter':'nearest','trim':False,'mirror_allowed':False,
              'stacked_png_size':[SIZE,SIZE*6],'stacked_pass_order':list(pass_names)},
    'channels':{'sprite':'sRGB, straight alpha, 4-band lighting and 2px RGB(34,49,59) external outline',
                'base':'unlit sRGB, binary surface coverage alpha',
                'normal':'linear UNORM, R camera right/G camera up/B toward camera, renormalize, mask Base A',
                'ao':'linear UNORM grayscale, five deterministic hemisphere rays, distance 0.22 BU, mask Base A',
                'rm':'linear UNORM, R roughness/G metallic/B 0, mask Base A',
                'emissive':'linear RGB zero, eyes reflect light, mask Base A'},
    'display_contract':{'world_units_per_pixel':1.78/128,'game_scale':1,'reference':'C011 integrated-r5',
                        'pixel_density_ratio_to_C011':1.0,'outline_px':2,'outline_rgb':[34,49,59]},
    'views':{},'clips':{'idle_scan':{'loop':True,'phase':'mid','duration_s':2.0,'effects':[],'samples':[]}},
})
for index in range(24):
    manifest['clips']['idle_scan']['samples'].append({'index':index,'time_s':index/12,'duration_s':1/12,
        'native_frame':1+index*4,'phase':'mid','phase_u':index/24,'support':[f'{s}{i}' for s in ('L','R') for i in range(1,5)],
        'marker_ids':['foot_'+f'{s}{i}' for s in ('L','R') for i in range(1,5)],'views':{}})
validation={'minimum_margin_px':SIZE,'normal_error_max':0,'visible_eye_pixel_counts':{},'frame_count':0,
            'coverage_equal':True,'unique_sprite_frames':{},'scope':'2D export and numeric material checks'}
light=Vector((-.4,-.6,.7)).normalized()
ao_directions=[Vector((0,0,1)),Vector((.6,0,.8)),Vector((-.6,0,.8)),Vector((0,.6,.8)),Vector((0,-.6,.8))]

for view, yaw in (('left',0.0),('right',2.00151174696589)):
    bpy.data.objects['visual_root'].rotation_euler.z=-math.pi/2+yaw
    camera.rotation_euler=(1.195510983467102,4.938385700370418e-09,-.5700404644012451)
    rotation=camera.rotation_euler.to_quaternion()
    # Balance the asymmetric projected footprint without changing pixels per BU.
    offset_px=-12 if view=='left' else 12
    camera.location=rotation@Vector((offset_px*1.78/128,camera.data.ortho_scale*(88/128-.5),20))
    bpy.context.view_layer.update()
    rotation=camera.matrix_world.to_quaternion()
    right,up,forward=[rotation@Vector(v) for v in ((1,0,0),(0,1,0),(0,0,-1))]
    axes=np.array([tuple(right),tuple(up),tuple(-forward)])
    origins=[camera.location+right*((x+.5)/SIZE-.5)*camera.data.ortho_scale
             +up*(.5-(y+.5)/SIZE)*camera.data.ortho_scale for y in range(SIZE) for x in range(SIZE)]
    pivot=world_to_camera_view(scene,camera,Vector((0,0,0)))
    manifest['views'][view]={'camera_location':list(camera.location),'camera_rotation_euler':list(camera.rotation_euler),
        'ortho_scale':camera.data.ortho_scale,'pivot':[pivot.x*SIZE,(1-pivot.y)*SIZE],'pass_files':{}}
    atlases={name:np.zeros((CELL*4,CELL*COLUMNS,4),dtype=np.uint8) for name in pass_names}
    frames=[]
    hashes=[]
    frame_dir=ROOT/f'2D/idle/idle_scan/{view}'
    frame_dir.mkdir(parents=True,exist_ok=True)
    for sample in manifest['clips']['idle_scan']['samples']:
        index=sample['index']
        select_idle(sample['time_s'])
        evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        mesh.calc_loop_triangles()
        verts=[evaluated.matrix_world@v.co for v in mesh.vertices]
        ray_length=max((vertex-camera.location).dot(forward) for vertex in verts)+1
        tris=[tuple(t.vertices) for t in mesh.loop_triangles]
        tree=BVHTree.FromPolygons(verts,tris,all_triangles=True)
        normal_transform=evaluated.matrix_world.to_3x3().inverted().transposed()
        loops=mesh.uv_layers.active.data
        colors=np.zeros((SIZE*SIZE,3),dtype=np.float32)
        normals=np.zeros_like(colors)
        ao=np.zeros(SIZE*SIZE,dtype=np.float32)
        roughness=np.zeros(SIZE*SIZE,dtype=np.float32)
        mask=np.zeros(SIZE*SIZE,dtype=bool)
        eye_pixels=0
        for pixel,origin in enumerate(origins):
            hit,normal,triangle_id,distance=tree.ray_cast(origin,forward,ray_length)
            if triangle_id is None:
                continue
            triangle=mesh.loop_triangles[triangle_id]
            bary=geometry.barycentric_transform(hit,*[verts[i] for i in triangle.vertices],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
            uv=sum((loops[i].uv*w for i,w in zip(triangle.loops,bary)),Vector((0,0)))
            colors[pixel]=pixels[min(1023,max(0,int(uv.y*1024))),min(1023,max(0,int(uv.x*1024))),:3]
            smooth=(normal_transform@sum((mesh.vertices[i].normal*w for i,w in zip(triangle.vertices,bary)),Vector((0,0,0)))).normalized()
            if smooth.dot(normal)<0:
                smooth.negate()
            normals[pixel]=axes@np.array(smooth)
            roughness[pixel]=skin.data.materials[triangle.material_index]['roughness']
            eye_pixels+=int(triangle.material_index==2)
            tangent=normal.to_track_quat('Z','Y')
            occluded=sum(tree.ray_cast(hit+normal*.002,tangent@direction,.22)[0] is not None for direction in ao_directions)
            ao[pixel]=1-.55*occluded/5
            mask[pixel]=True
        evaluated.to_mesh_clear()
        alpha=mask.astype(np.uint8)*255
        maps={name:np.zeros((SIZE*SIZE,4),dtype=np.uint8) for name in pass_names}
        maps['base'][:,:3]=np.rint(colors*255).astype(np.uint8)
        maps['normal'][:,:3]=np.rint((normals*.5+.5)*255).astype(np.uint8)
        maps['ao'][:,:3]=np.rint(ao[:,None]*255).astype(np.uint8)
        maps['rm'][:,0]=np.rint(roughness*255).astype(np.uint8)
        shade=.34+.82*np.maximum(0,normals@np.array(light))
        shade=np.round(shade*4)/4*(.92+.08*ao)
        lit=srgb_to_linear(colors)*shade[:,None]
        half=(np.array(light)+np.array([0,0,1]))
        half/=np.linalg.norm(half)
        spec=np.maximum(0,normals@half)**24*(roughness<.55)*.5
        lit+=spec[:,None]
        maps['sprite'][:,:3]=np.rint(linear_to_srgb(lit)*255).astype(np.uint8)
        for name in pass_names:
            maps[name][:,3]=alpha
            maps[name]=maps[name].reshape(SIZE,SIZE,4)
        surface=mask.reshape(SIZE,SIZE)
        padded=np.pad(surface,2)
        outline=np.zeros_like(surface)
        for dy in range(-2,3):
            for dx in range(-2,3):
                if dx*dx+dy*dy<=5:
                    outline|=padded[2+dy:2+dy+SIZE,2+dx:2+dx+SIZE]
        ring=outline & ~surface
        maps['sprite'][ring]=[34,49,59,255]
        y,x=np.where(maps['sprite'][:,:,3]>0)
        bbox=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
        validation['minimum_margin_px']=min(validation['minimum_margin_px'],bbox[0],bbox[1],SIZE-bbox[2],SIZE-bbox[3])
        decoded=maps['normal'][:,:,:3][surface].astype(float)/255*2-1
        validation['normal_error_max']=max(validation['normal_error_max'],float(np.max(np.abs(np.linalg.norm(decoded,axis=1)-1))))
        markers={}
        for label in model['leg_paths']:
            part=next(p for p in model['parts'] if p['name']==f'leg_{label}_tarsus')
            position=min(verts[part['first_vertex']:part['first_vertex']+part['vertex_count']],key=lambda p:p.z)
            p=world_to_camera_view(scene,camera,position)
            markers['foot_'+label]={'world':list(position),'xy':[p.x*SIZE,(1-p.y)*SIZE]}
            px,py=round(p.x*SIZE),round((1-p.y)*SIZE)
            assert surface[max(0,py-3):min(SIZE,py+4),max(0,px-3):min(SIZE,px+4)].any(), (view,index,label,'foot missing from Base')
        attack=rig.matrix_world@((rig.pose.bones['chelicera_L'].head+rig.pose.bones['chelicera_R'].head)/2)
        p=world_to_camera_view(scene,camera,attack)
        markers['attack_socket']={'world':list(attack),'xy':[p.x*SIZE,(1-p.y)*SIZE],'enabled':False}
        ax=(index%COLUMNS)*CELL+PADDING
        ay=(index//COLUMNS)*CELL+PADDING
        for name,array in maps.items():
            atlases[name][ay-PADDING:ay+SIZE+PADDING,ax-PADDING:ax+SIZE+PADDING]=np.pad(array,((PADDING,PADDING),(PADDING,PADDING),(0,0)),mode='edge')
        sample['views'][view]={'rect':[ax,ay,SIZE,SIZE],'bbox':bbox,'markers':markers,'eye_pixels':eye_pixels}
        png(frame_dir/f'{index}.png',np.concatenate([maps[name] for name in pass_names]),False)
        frames.append(maps['sprite'])
        hashes.append(hashlib.sha256(maps['sprite'].tobytes()).hexdigest())
        validation['visible_eye_pixel_counts'][f'{view}/{index}']=eye_pixels
        validation['frame_count']+=1
        print(f'EXPORT {view} {index+1}/24',flush=True)
    for name,array in atlases.items():
        filename=f'{view}_{name}.png'
        png(OUT/filename,array,name in ('sprite','base'))
        manifest['views'][view]['pass_files'][name]=filename
    apng(OUT/f'idle_scan_{view}.png',frames,[1/12]*24,True)
    validation['unique_sprite_frames'][view]=len(set(hashes))
assert validation['minimum_margin_px']>=8
assert validation['normal_error_max']<.015
assert all(value>0 for value in validation['visible_eye_pixel_counts'].values())
assert all(value>=12 for value in validation['unique_sprite_frames'].values())
validation['status']='PASS'
validation['foot_marker_surface_check']='all 384 foot projections within 3px of Base coverage'
validation['ray_depth']='evaluated mesh maximum camera depth + 1 BU'
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'export_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
