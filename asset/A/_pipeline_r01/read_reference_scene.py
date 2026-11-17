import bpy
import json
from pathlib import Path
scene=bpy.context.scene
data={'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,
      'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,'lights':[],'world':None}
for obj in scene.objects:
    if obj.type=='LIGHT':
        light=obj.data
        data['lights'].append({'name':obj.name,'type':light.type,'location':list(obj.location),
            'rotation':list(obj.rotation_euler),'energy':light.energy,'color':list(light.color),
            'size':getattr(light,'size',None),'shape':getattr(light,'shape',None)})
if scene.world:
    data['world']={'color':list(scene.world.color)}
    if scene.world.node_tree:
        bg=next((n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'),None)
        if bg:data['world'].update(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value)
out=Path(__file__).resolve().parent/'reference/C011_scene.json'
out.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data),flush=True)
