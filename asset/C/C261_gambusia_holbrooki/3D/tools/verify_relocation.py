"""Read-only native reopen and embedded/external authoring parity."""
import json,hashlib,sys
from pathlib import Path
import bpy
ROOT=Path(bpy.data.filepath).resolve().parents[1];sys.path[:0]=[str(ROOT/'runtime'),str(ROOT/'3D/tools')]
from select_pose import select_pose
for sex in ('female','male'):
    select_pose(sex,'surface_gape','mid',.5)
    assert bpy.data.objects['Rig_'+sex].animation_data.action.name==f'GH_{sex}_surface_gape_mid_r03'
images=[]
for im in bpy.data.images:
    if im.source!='FILE':continue
    assert im.packed_file,im.name
    path=Path(bpy.path.abspath(im.filepath));assert path.is_file(),path
    assert hashlib.sha256(im.packed_file.data).hexdigest()==hashlib.sha256(path.read_bytes()).hexdigest(),im.name
    images.append(im.name)
scripts=[]
for filename in ('build_fish.py','select_pose.py','motion_spec.py','export_fish.py','verify_fish.py','imagegen_surface.py'):
    external=ROOT/('runtime' if filename=='motion_spec.py' else '3D/tools')/filename
    assert bpy.data.texts[filename].as_string().rstrip()==external.read_text(encoding='utf-8').rstrip(),filename
    scripts.append(filename)
print(json.dumps({'status':'PASS','packed_images':images,'embedded_tools':scripts,'relocated_file':bpy.data.filepath,'saved_changes':False}))
