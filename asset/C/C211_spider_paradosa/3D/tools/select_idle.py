"""Run from Blender's Text Editor. Time is wrapped to the idle loop."""
import math
import bpy

TIME_S = 0.0


def select_idle(time_s=0.0):
    if not math.isfinite(time_s):
        raise ValueError('time_s must be finite')
    rig = bpy.data.objects['Pardosa_Rig']
    action = bpy.data.actions['C211_idle_scan_mid_r02']
    rig.animation_data_create()
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    frame = 1 + (time_s % 2.0) * 48
    bpy.context.scene.frame_set(int(frame), subframe=frame % 1)
    bpy.context.view_layer.update()


if __name__ == '__main__':
    select_idle(TIME_S)
