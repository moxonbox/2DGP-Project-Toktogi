import bpy,json
scope={}
exec(bpy.data.texts['PLAYABLE_POSE.py'].as_string(),scope)
base=json.loads(bpy.data.texts['PLAYABLE_MANIFEST.json'].as_string())
runtime=json.loads(bpy.data.texts['RUNTIME_R2_MANIFEST.json'].as_string())

def select_runtime(name,seconds=0.):
    profile=runtime['profiles'][name]
    scope['select_pose'](base,'idle',profile['source'][1],1)
    rig=bpy.data.objects['Toktogi_Rig'];visual=bpy.data.objects['visual_root']
    for obj in (rig,visual,*rig.pose.bones):obj.rotation_mode='QUATERNION'
    for obj,key in ((rig,'action'),(visual,'heading_action')):
        obj.animation_data_create();action=bpy.data.actions[profile[key]]
        obj.animation_data.action=action;obj.animation_data.action_slot=action.slots[0]
    scene=bpy.context.scene;scene.render.fps=50;scene.render.fps_base=1
    scene.frame_start=1;scene.frame_end=round(profile['native_frame_end'])
    frame=min(profile['native_frame_end'],1+max(0.,seconds)*50)
    scene.frame_set(int(frame),subframe=frame%1)
    bpy.context.view_layer.update()

if __name__=='__main__':
    select_runtime(bpy.context.scene.get('runtime_profile','edge_right_right'))
