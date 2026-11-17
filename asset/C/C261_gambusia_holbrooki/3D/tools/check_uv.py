"""Visual UV-density proof from the final saved mesh; does not resave source."""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(bpy.data.filepath).resolve().parents[1]
sys.path[:0]=[str(ROOT/'3D/tools'),str(ROOT/'runtime')]
from select_pose import select_pose
from motion_spec import VARIANTS
folder=ROOT/'comparison';folder.mkdir(exist_ok=True)
mat=bpy.data.materials.new('QA_UV_Checker');mat.use_nodes=True;nodes=mat.node_tree.nodes
tex=nodes.new('ShaderNodeTexChecker');tex.inputs['Scale'].default_value=32
tex.inputs['Color1'].default_value=(.12,.3,.48,1);tex.inputs['Color2'].default_value=(.8,.87,.73,1)
uv=nodes.new('ShaderNodeTexCoord');mat.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector'])
mat.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
scene=bpy.context.scene;camera=scene.camera;scene.render.resolution_x=640;scene.render.resolution_y=480;scene.cycles.samples=16
result={}
for sex,profile in VARIANTS.items():
    select_pose(sex);bpy.data.objects['Rig_'+sex].data.pose_position='REST'
    mesh=bpy.data.objects['Fish_'+sex].data
    for i in range(len(mesh.materials)):mesh.materials[i]=mat
    camera.location=(profile['sl_bu']*.1,-20,0);camera.rotation_euler=Matrix([(1,0,0),(0,0,1),(0,-1,0)]).transposed().to_euler();camera.data.ortho_scale=profile['sl_bu']*1.5
    scene.render.filepath=str(folder/f'{sex}_uv_checker.png');bpy.ops.render.render(write_still=True)
    uvdata=mesh.uv_layers.active.data;mesh.calc_loop_triangles();zero=0;negative=0;by_part={}
    parts=json.loads((ROOT/'3D/model_manifest.json').read_text())['variants'][sex]['parts']
    for tri in mesh.loop_triangles:
        a,b,c=[uvdata[i].uv for i in tri.loops];area=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)
        zero+=abs(area)<1e-10;negative+=area<0
        if abs(area)<1e-10:
            part=next(p['name'] for p in parts if p['first_vertex']<=tri.vertices[0]<p['first_vertex']+p['vertex_count'])
            by_part[part]=by_part.get(part,0)+1
    result[sex]={'triangles':len(mesh.loop_triangles),'zero_UV_area':zero,'negative_UV_winding':negative,
                 'zero_UV_by_part':by_part,
                 'intentional_reuse':['fin front/back charts; thin edge walls share rim UVs','bilateral eye charts','gill creases use one flat-color palette texel','hidden body/jaw end caps collapse to seam'],
                 'note':'Signed winding includes intentional reverse fin faces; checker images are the visual density evidence. No detailed painting supported on thin fin edges or flat-color crease strips.'}
(folder/'uv_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
