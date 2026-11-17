"""Select a saved fish Action without executing simulation or VFX."""
import math
import bpy


def select_pose(variant='female',action='hover_or_school',phase='mid',u=0.):
    if not math.isfinite(u) or not 0<=u<=1:
        raise ValueError('pose fraction must be finite and within 0..1')
    name=f'GH_{variant}_{action}_{phase}_r03'
    if name not in bpy.data.actions:
        raise ValueError('unsupported Action: '+name)
    for sex in ('female','male'):
        for obj in bpy.data.collections['Gambusia_'+sex].objects:
            obj.hide_render=sex!=variant
            obj.hide_set(sex!=variant)
    rig=bpy.data.objects['Rig_'+variant]
    clip=bpy.data.actions[name]
    rig.animation_data_create()
    rig.animation_data.action=clip
    rig.animation_data.action_slot=clip.slots[0]
    frame=1+clip['duration_s']*60*u
    bpy.context.scene.frame_set(int(frame),subframe=frame%1)
    bpy.context.view_layer.update()
    return rig


if __name__=='__main__':
    select_pose()
