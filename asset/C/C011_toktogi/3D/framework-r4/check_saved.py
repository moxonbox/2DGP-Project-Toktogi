"""Check exported keys using the reopened Blender Action."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

out=Path(bpy.data.filepath).parent
select={'__name__':'verify'}
exec(bpy.data.texts['SET_RUNTIME_POSE.py'].as_string(),select)
env={'__name__':'geometry'}
source=bpy.data.texts['EXPORT_PLAYABLE.py'].as_string()
exec(source[:source.index('manifest["source_blend_sha256"]')],env)
rows=json.loads((out/'spin_validation.json').read_text())['cells']
for row in rows:
    select['select_runtime'](row['profile'],(row['frame']-1)/50)
    mesh=env['skin'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    vertices=[mesh.matrix_world@v.co for v in mesh.data.vertices]
    assert hashlib.sha256(np.round(np.array(vertices),6).tobytes()).hexdigest()==row['geometry_hash'],row
assert len(rows)==120
result={'revision':'framework-r4','saved_action_cells':len(rows),'native_step_frames':.25}
(out/'saved_action_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(result,flush=True)
