"""Saved model measurements, geometry, all phase boundaries and seek determinism."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(bpy.data.filepath).resolve().parents[1]
sys.path[:0]=[str(ROOT/'3D/tools'),str(ROOT/'runtime')]
from select_pose import select_pose
from motion_spec import VARIANTS,DESIGNS,PHASES,LOOPS,SEQUENCES
model=json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string())
report={'status':'PASS','source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'variants':{},'limits':[
    'Body-fin/gill/jaw hinge overlaps are intentional attachments; arbitrary inter-part collision is not a no-intersection claim.',
    'UV fin reverse faces and bilateral eye charts intentionally reuse texture regions.']}


def snapshot(sex,action,phase,u):
    rig=select_pose(sex,action,phase,u)
    evaluated=bpy.data.objects['Fish_'+sex].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    xyz=np.array([evaluated.matrix_world@v.co for v in mesh.vertices]);evaluated.to_mesh_clear()
    assert np.isfinite(xyz).all()
    assert all(tuple(b.scale)==(1,1,1) for b in rig.pose.bones)
    return xyz


for sex,profile in VARIANTS.items():
    obj=bpy.data.objects['Fish_'+sex];rig=bpy.data.objects['Rig_'+sex];data=model['variants'][sex]
    assert len(rig.data.bones)==26 and tuple(obj.scale)==tuple(rig.scale)==(1,1,1)
    assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in obj.data.vertices)
    names=[p['name'] for p in data['parts']]
    gill_normals={}
    for side,sign in (('L',1),('R',-1)):
        part=next(p for p in data['parts'] if p['name']=='operculum_'+side)
        vertices=list(obj.data.vertices)[part['first_vertex']:part['first_vertex']+part['vertex_count']]
        mean=float(np.mean([v.normal.y for v in vertices]));assert mean*sign>.8,(sex,side,mean)
        gill_normals[side]=mean
    assert sum(n.startswith('eye_') for n in names)==2
    required=['dorsal_fin','caudal_fin','pectoral_L','pectoral_R','pelvic_L','pelvic_R','anal_fin' if sex=='female' else 'gonopodium']
    assert all(n in names for n in required)
    assert ('gonopodium' in names)==(sex=='male')
    snout=rig.data.bones['SL_snout'].head_local.x;tail=rig.data.bones['SL_tail'].head_local.x
    length=float(tail-snout);assert abs(length-profile['sl_bu'])<1e-5
    uv=obj.data.uv_layers.active.data
    assert all(0<=value<=1 for loop in uv for value in loop.uv)
    max_join=0.;max_loop=0.;max_seek=0.;max_velocity=0.;checked=0
    for action in DESIGNS:
        for phase in PHASES:
            for fraction in np.linspace(0,1,17):snapshot(sex,action,phase,float(fraction));checked+=1
            first=snapshot(sex,action,phase,.37)
            snapshot(sex,action,phase,.9);snapshot(sex,action,phase,.1)
            again=snapshot(sex,action,phase,.37);max_seek=max(max_seek,float(np.max(abs(first-again))))
        for a,b in [('pre','mid'),('mid','end')]:
            error=float(np.max(abs(snapshot(sex,action,a,1)-snapshot(sex,action,b,0))))
            max_join=max(max_join,error)
        if action in LOOPS:
            first=snapshot(sex,action,'mid',0);last=snapshot(sex,action,'mid',1)
            max_loop=max(max_loop,float(np.max(abs(first-last))))
            start=(snapshot(sex,action,'mid',.001)-first)/.001
            end=(last-snapshot(sex,action,'mid',.999))/.001
            max_velocity=max(max_velocity,float(np.max(abs(start-end))))
    for sequence in SEQUENCES.values():
        for before,after in zip(sequence,sequence[1:]):
            max_join=max(max_join,float(np.max(abs(snapshot(sex,before,'end',1)-snapshot(sex,after,'pre',0)))))
    assert max_join<1e-4 and max_loop<1e-4 and max_seek<1e-7,(sex,max_join,max_loop,max_seek)
    assert max_velocity<.08*profile['sl_bu'],max_velocity
    closed=snapshot(sex,'surface_gape','mid',0);opened=snapshot(sex,'surface_gape','mid',.5)
    jaw=next(p for p in data['parts'] if p['name']=='jaw_lower');section=slice(jaw['first_vertex'],jaw['first_vertex']+jaw['vertex_count'])
    jaw_motion=float(np.linalg.norm(opened[section]-closed[section],axis=1).max())
    assert jaw_motion>.025*profile['sl_bu']
    report['variants'][sex]={'SL_bu':length,'TL_bu':data['TL_bu'],'triangles':data['triangles'],'bones':26,
        'poses_checked':checked,'phase_and_sequence_join_error_bu':max_join,'loop_error_bu':max_loop,'seek_error_bu':max_seek,
        'loop_derivative_error_bu_per_cycle':max_velocity,'jaw_open_displacement_bu':jaw_motion,
        'required_fins':required,'unweighted_vertices':0,'normalized_weights':True,'UV_bounds':'PASS','outward_gill_normal_y':gill_normals}
assert len(bpy.data.actions)==96
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
(ROOT/'3D/saved_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
