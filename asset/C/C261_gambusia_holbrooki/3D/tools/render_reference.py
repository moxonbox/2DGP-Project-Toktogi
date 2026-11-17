"""Render six neutral views from the actual editable geometry."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(bpy.data.filepath).resolve().parents[1]
sys.path[:0]=[str(ROOT/'3D/tools'),str(ROOT/'runtime')]
from select_pose import select_pose
from motion_spec import VARIANTS
scene=bpy.context.scene;camera=scene.camera
scene.render.resolution_x=640;scene.render.resolution_y=480
scene.render.resolution_percentage=100;scene.cycles.samples=24
for sex,profile in VARIANTS.items():
    select_pose(sex)
    rig=bpy.data.objects['Rig_'+sex];rig.data.pose_position='REST'
    folder=ROOT/f'sheet/blender_{sex}';folder.mkdir(exist_ok=True)
    length=profile['sl_bu'];target=Vector((.1*length,0,0))
    for view,direction in [('front',(-1,0,0)),('left',(0,-1,0)),('right',(0,1,0)),('rear',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:
        back=Vector(direction);up=Vector((-1,0,0) if view in ('top','bottom') else (0,0,1));right=up.cross(back).normalized();up=back.cross(right)
        camera.rotation_euler=Matrix([right,up,back]).transposed().to_euler()
        camera.location=target+back*20;camera.data.ortho_scale=length*1.5
        scene.render.filepath=str(folder/(view+'.png'));bpy.ops.render.render(write_still=True)
    rig.data.pose_position='POSE'
print('PASS 12 neutral anatomy renders')
