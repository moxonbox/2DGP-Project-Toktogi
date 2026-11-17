"""Run against a reopened blend, including between-key contact and seek checks."""
import hashlib
import json
import random
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(bpy.data.filepath).resolve().parents[1]
sys.path.insert(0,str(ROOT/'3D/tools'))
from select_idle import select_idle

scene=bpy.context.scene
rig=bpy.data.objects['Pardosa_Rig']
skin=bpy.data.objects['Pardosa_Skinned']
model=json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string())
parts=model['parts']
labels=list(model['leg_paths'])
assert len(labels)==8
assert sum(p['name'].startswith('eye_') for p in parts)==8
assert len([p for p in parts if 'eye_anterior' in p['name']])==4
assert len([p for p in parts if 'eye_PME' in p['name']])==2
assert len([p for p in parts if 'eye_PLE' in p['name']])==2
assert len([b for b in rig.data.bones if b.name.startswith('leg_')])==56
assert len([c for b in rig.pose.bones for c in b.constraints if c.type=='IK'])==8
assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in skin.data.vertices)
assert all(tuple(o.scale)==(1,1,1) for o in (rig,skin,bpy.data.objects['visual_root'],bpy.data.objects['physics_root']))
assert all(im.packed_file or not im.filepath or Path(bpy.path.abspath(im.filepath)).is_file() for im in bpy.data.images)
skin.data.calc_loop_triangles()
uvs=skin.data.uv_layers.active.data
uv_areas=[]
for tri in skin.data.loop_triangles:
    a,b,c=[uvs[i].uv for i in tri.loops]
    uv_areas.append((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))
assert all(abs(area)>1e-10 for area in uv_areas)
assert all(0<=value<=1 for loop in uvs for value in loop.uv)
assert len({tuple(p['tile']) for p in parts})==len(parts)


def snapshot(frame):
    scene.frame_set(int(frame),subframe=frame%1)
    bpy.context.view_layer.update()
    evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    positions=np.array([tuple(evaluated.matrix_world@v.co) for v in evaluated.data.vertices])
    feet=np.array([tuple(rig.matrix_world@rig.pose.bones[f'leg_{label}_tarsus'].tail) for label in labels])
    return positions,feet


first,first_feet=snapshot(1)
last,last_feet=snapshot(97)
loop_error=float(np.max(np.abs(last-first)))
assert loop_error<1e-5,loop_error
maximum_drift=0
minimum_height=10
max_sole_drift=0
collision_frames=[]
tip_indices=[]
for label in labels:
    part=next(p for p in parts if p['name']==f'leg_{label}_tarsus')
    indices=list(range(part['first_vertex'],part['first_vertex']+part['vertex_count']))
    tip_indices.append(min(indices,key=lambda i:first[i,2]))
frame_count=0
for frame in np.arange(1,97.01,.5):
    positions,feet=snapshot(float(frame))
    maximum_drift=max(maximum_drift,float(np.max(np.linalg.norm(feet-first_feet,axis=1))))
    max_sole_drift=max(max_sole_drift,float(np.max(np.linalg.norm(positions[tip_indices]-first[tip_indices],axis=1))))
    minimum_height=min(minimum_height,float(positions[:,2].min()))
    # Detect cross-leg surface intersections, excluding intentional body attachment joints.
    if frame%4==1:
        trees=[]
        for label in labels:
            indices=set()
            for p in parts:
                if p['name'].startswith(f'leg_{label}_') and not p['name'].endswith(('coxa','trochanter')):
                    indices.update(range(p['first_vertex'],p['first_vertex']+p['vertex_count']))
            triangles=[tuple(t.vertices) for t in skin.data.loop_triangles if all(i in indices for i in t.vertices)]
            trees.append(BVHTree.FromPolygons(positions.tolist(),triangles,all_triangles=True))
        for i in range(8):
            for j in range(i+1,8):
                if trees[i].overlap(trees[j]):
                    collision_frames.append({'frame':float(frame),'legs':[labels[i],labels[j]]})
    frame_count+=1
assert maximum_drift<.015,maximum_drift
assert max_sole_drift<.035,max_sole_drift
assert minimum_height>=-.005,minimum_height
assert not collision_frames,collision_frames[:8]
seek_frames=[1,5.5,17,33.5,49,65.5,81,96.5]
baseline={f:snapshot(f)[0] for f in seek_frames}
orders=[list(reversed(seek_frames)),random.Random(211).sample(seek_frames,len(seek_frames))]
seek_error=max(float(np.max(np.abs(snapshot(f)[0]-baseline[f]))) for order in orders for f in order)
assert seek_error<1e-5,seek_error
select_idle(0)
selected=snapshot(1)[0]
select_idle(2)
current=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
assert np.max(np.abs(np.array([tuple(v.co) for v in current.data.vertices])-selected))<1e-5
report={'status':'PASS','blender_version':bpy.app.version_string,'saved_file':Path(bpy.data.filepath).name,
        'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
        'measured':model['measured'],'eye_layout':[4,2,2],'legs':8,'ik_chains':8,
        'loop_max_vertex_error_bu':loop_error,'seek_max_vertex_error_bu':seek_error,
        'between_key_samples':frame_count,'max_foot_target_drift_bu':maximum_drift,
        'max_sole_vertex_drift_bu':max_sole_drift,'minimum_mesh_height_bu':minimum_height,
        'cross_leg_surface_intersections':collision_frames,'uv_zero_area_faces':0,'unweighted_vertices':0,
        'missing_external_files':[],'limitations':['Cross-leg test at 4 native-frame spacing; contact every 0.5 frame.',
            'UV islands are per-part padded charts. Texture density intentionally varies by anatomical part.',
            'This verifies idle only; game physics, AI and other motion transitions remain outside this revision.']}
(ROOT/'3D/saved_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
