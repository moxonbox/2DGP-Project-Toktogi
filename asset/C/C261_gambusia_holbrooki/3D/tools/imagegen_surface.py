"""Ingest GPT Image pigment through Blender's standard 1024px texture pipeline."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import numpy as np
from png_codec import png

def texture(root,sex):
    source=root/f'imagegen/{sex}_uv_atlas_raw.png'
    image=bpy.data.images.load(str(source),check_existing=False)
    image.colorspace_settings.name='sRGB'
    raw_size=list(image.size)
    image.scale(1024,1024)
    pixels=np.empty(1024*1024*4,dtype=np.float32);image.pixels.foreach_get(pixels)
    rgba=np.flipud(pixels.reshape(1024,1024,4))
    destination=root/f'3D/textures/gambusia_{sex}_basecolor_r03.png'
    png(destination,np.rint(np.clip(rgba,0,1)*255).astype(np.uint8),True)
    bpy.data.images.remove(image)
    final=bpy.data.images.load(str(destination),check_existing=False)
    final.name='BaseColor_'+sex;final.pack();final.filepath='//textures/'+destination.name
    return final,{'raw_size':raw_size,'working_size':[1024,1024],'conversion':'Blender Image.scale; sRGB RGBA8, filter-zero lossless PNG; generated raw retained'}

def apply():
    import json,hashlib,sys
    root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'runtime'),str(root/'3D/tools')]
    from select_pose import select_pose
    model=json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string());model['revision']='gambusia-r03'
    report={'tool':'built-in GPT Image','variants':{}}
    for sex in ('female','male'):
        old=bpy.data.images.get('BaseColor_'+sex)
        if old:old.name='PreviousBaseColor_'+sex
        image,info=texture(root,sex)
        for material in bpy.data.materials:
            if not material.name.startswith(sex+'_') or not material.use_nodes:continue
            for node in material.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image==old:node.image=image
        if old:bpy.data.images.remove(old)
        report['variants'][sex]={**info,'generated_sha256':hashlib.sha256((root/f'imagegen/{sex}_uv_atlas_raw.png').read_bytes()).hexdigest()}
    for action in bpy.data.actions:
        if action.name.endswith('_r01'):action.name=action.name[:-4]+'_r03'
    bpy.data.texts['ASSET_MANIFEST.json'].clear();bpy.data.texts['ASSET_MANIFEST.json'].write(json.dumps(model,indent=2))
    for filename in ('build_fish.py','select_pose.py','motion_spec.py','export_fish.py','verify_fish.py','imagegen_surface.py'):
        source=root/('runtime' if filename=='motion_spec.py' else '3D/tools')/filename
        text=bpy.data.texts.get(filename) or bpy.data.texts.new(filename);text.clear();text.write(source.read_text(encoding='utf-8'))
    select_pose();bpy.ops.wm.save_as_mainfile(filepath=str(root/'3D/gambusia_holbrooki_r03.blend'))
    (root/'3D/model_manifest.json').write_text(json.dumps(model,indent=2),encoding='utf-8')
    (root/'document/imagegen_ingestion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':apply()
