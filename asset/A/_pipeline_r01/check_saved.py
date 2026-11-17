"""Reopen each deliverable and verify packed textures and static seek invariance."""
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
report=[]
for c in json.loads((HERE/'assets.json').read_text(encoding='utf-8')):
    folder=ROOT/c['folder']; blend=folder/'3D'/(c['asset_id']+'_r01.blend')
    bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False)
    snapshots=[]; triangles=0; packed=[]
    for frame in (1,30,12,60,1):
        bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get(); h=hashlib.sha256(); triangles=0
        for obj in sorted(bpy.data.objects,key=lambda obj:obj.name):
            if obj.type!='MESH': continue
            ev=obj.evaluated_get(dg); mesh=ev.to_mesh(); mesh.calc_loop_triangles()
            coords=np.array([ev.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
            h.update(obj.name.encode()); h.update(coords.tobytes()); triangles+=len(mesh.loop_triangles)
            assert np.isfinite(coords).all() and mesh.uv_layers.active
            ev.to_mesh_clear()
        snapshots.append(h.hexdigest())
    assert len(set(snapshots))==1
    assert max(abs(v) for v in bpy.data.objects['visual_root'].rotation_euler)<1e-6
    for image in bpy.data.images:
        if image.source!='FILE': continue
        assert image.packed_file,image.name
        file=Path(bpy.path.abspath(image.filepath))
        # External copies are optional at playback, but must agree at handoff.
        assert file.exists(),file
        assert hashlib.sha256(bytes(image.packed_file.data)).digest()==hashlib.sha256(file.read_bytes()).digest(),image.name
        packed.append({'image':image.name,'bytes':len(image.packed_file.data),'external_matches':True})
    assert triangles<=c['triangle_budget']
    cameras=[o for o in bpy.data.objects if o.type=='CAMERA']
    assert len(cameras)==1 and abs(cameras[0].data.ortho_scale-c['cell_size']*1.78/128)<1e-6
    report.append({'asset_id':c['asset_id'],'saved_reopen':'PASS','seek_frames':[1,30,12,60,1],
                   'seek_mesh_hashes':snapshots,'triangles':triangles,'packed_images':packed,
                   'bones':len([o for o in bpy.data.objects if o.type=='ARMATURE']),
                   'source_blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest()})
(HERE/'saved_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Saved-file checks passed:',len(report),flush=True)
