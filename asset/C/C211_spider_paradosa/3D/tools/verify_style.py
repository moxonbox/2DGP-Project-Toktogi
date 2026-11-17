"""Measure the selected body-size profile and periodic idle motion."""
import json
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(bpy.data.filepath).resolve().parents[1]
scope={'__name__':'saved_validation'}
exec(compile((ROOT/'3D/tools/verify_saved.py').read_text(encoding='utf-8'),'verify_saved.py','exec'),scope)
model=scope['model']
snapshot=scope['snapshot']
first,_=snapshot(1)
body_indices=[]
for part in model['parts']:
    if part['name'] in ('cephalothorax','abdomen'):
        body_indices.extend(range(part['first_vertex'],part['first_vertex']+part['vertex_count']))
body=first[body_indices]
length=float(np.ptp(body[:,1]))
assert abs(length-4.82698)<1e-5,length
assert abs(length/.965396-5)<1e-5
points=[]
for frame in np.linspace(1,97,193):
    positions,_=snapshot(float(frame))
    points.append(positions[body_indices].mean(axis=0))
amplitude=np.ptp(np.array(points),axis=0)
h=.01
before,_=snapshot(97-h)
after,_=snapshot(1+h)
velocity_error=float(np.max(np.linalg.norm(((first-before)-(after-first))/(h/48),axis=1)))
assert velocity_error<.025,velocity_error
visibility={}
for fps in (10,15,20,30,60):
    visits=[]
    for phase in (0,.017,.041,.079):
        visits.append(len({int(((i/fps+phase)%2)*12)%24 for i in range(2*fps)}))
    visibility[str(fps)]=visits
assert min(visibility['10'])>=20
result={'status':'PASS','reference':'AssetSize v1.1, C011 idle/left body proxy .965396 BU',
        'body_measurement':'prosoma front to abdomen rear along local Y, excludes appendages and eyes',
        'body_length_bu':length,'ratio_to_toktogi':length/.965396,'body_length_mm':5.0,
        'stage':'adult female','taxon':'Pardosa agrestis','art_scale':1.0,
        'full_bounds_bu':np.ptp(first,axis=0).tolist(),'pixel_density':128/1.78,
        'body_centroid_range_bu':amplitude.tolist(),'body_centroid_range_px':(amplitude*128/1.78).tolist(),
        'loop_velocity_discontinuity_bu_s':velocity_error,'loop_velocity_tolerance_bu_s':.025,
        'sample_visits_at_four_start_phases':visibility,'reference_idle_s':1.6,'spider_idle_s':2,
        'rhythm_reason':'slower grounded scanning with stable eight-foot support; species speed is a design choice'}
(ROOT/'3D/style_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
