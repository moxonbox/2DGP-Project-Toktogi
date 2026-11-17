"""Run in a saved r02 Blend, then call select_view('yaw_045') in its namespace."""
import json
import bpy
from mathutils import Matrix

def select_view(name):
    views={item['view']:item for item in json.loads(bpy.data.texts['ENVIRONMENT_VIEWS.json'].as_string())}
    if name not in views:raise ValueError(f'Unknown environment view: {name}; choose {list(views)}')
    item=views[name]
    bpy.data.objects['visual_root'].rotation_euler=(0,0,item['yaw_radians'])
    bpy.context.scene.camera.matrix_world=Matrix(item['camera_matrix_world'])
    bpy.context.scene['asset_view']=name
    bpy.context.view_layer.update()
    return {'view':name,'pivot':item['pivot'],'yaw_radians':item['yaw_radians']}

if __name__=='__main__':
    select_view(bpy.context.scene.get('asset_view','left'))
