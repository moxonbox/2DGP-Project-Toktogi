"""Orthographic triangle export: eight aligned passes, all actions and phases."""
import hashlib
import json
import math
import struct
import sys
import time
import zlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(bpy.data.filepath).resolve().parents[1]
sys.path[:0]=[str(ROOT/'3D/tools'),str(ROOT/'runtime')]
from select_pose import select_pose
from motion_spec import VARIANTS,DESIGNS,PHASES,samples,PIXELS_PER_BU
from png_codec import png,apng,srgb_to_linear,linear_to_srgb
args=sys.argv[sys.argv.index('--')+1:]
SEX,VIEW=args[:2]
ONLY=args[2] if len(args)>2 else None
assert SEX in VARIANTS and VIEW in ('left','right','front','top')
MODEL=json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string())
PROFILE=MODEL['variants'][SEX];SIZE=PROFILE['cell'];SL=PROFILE['sl_bu'];PAD=2;CELL=SIZE+4
PASSES=('sprite','base','normal','ao','orm','emissive','depth','watermask')
OUT=ROOT/'2D/gambusia-r03';OUT.mkdir(exist_ok=True)
PALETTE=np.array([list(bytes.fromhex(h)) for h in '24302d 39443d 50594a 68715f 808a7a 9aa495 aeb7ac c1c9bf d2d7cb e0e3d5 eaeadb f3f1e3 fbf7e9'.split()])
scene=bpy.context.scene;camera=scene.camera;skin=bpy.data.objects['Fish_'+SEX]
yaw=2.00151174696589 if VIEW=='right' else 0.
bpy.data.objects['visual_root'].rotation_euler.z=yaw
if VIEW in ('left','right'):camera.rotation_euler=(1.195510983467102,4.938385700370418e-09,-.5700404644012451)
else:camera.rotation_euler=Vector((1,0,0) if VIEW=='front' else (0,0,-1)).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=SIZE/PIXELS_PER_BU
q=camera.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));back=q@Vector((0,0,1))
origin=bpy.data.objects['visual_root'].rotation_euler.to_matrix()@Vector((.10*SL,0,0))
camera.location=origin+back*20
bpy.context.view_layer.update()
axes=np.array([right,up,back]);cam=np.array(camera.location)
pivot=[float(SIZE/2-(origin@right)*PIXELS_PER_BU),float(SIZE/2+(origin@up)*PIXELS_PER_BU)]
inverse_yaw=bpy.data.objects['visual_root'].matrix_world.inverted()


def read_texture(path):
    data=path.read_bytes();offset=8;payload=b''
    while offset<len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0];tag=data[offset+4:offset+8];blob=data[offset+8:offset+8+length]
        if tag==b'IHDR':width,height=struct.unpack('>II',blob[:8])
        if tag==b'IDAT':payload+=blob
        offset+=length+12
    rows=np.frombuffer(zlib.decompress(payload),np.uint8).reshape(height,width*4+1)
    assert not rows[:,0].any(),'source codec must use filter zero'
    return srgb_to_linear(np.flipud(rows[:,1:].reshape(height,width,4))[:,:,:3]/255.)


texture=read_texture(ROOT/f'3D/textures/gambusia_{SEX}_basecolor_r03.png')


def sample_texture(uv):
    xy=np.clip(uv,0,1)*1023;x=np.floor(xy[:,0]).astype(int);y=np.floor(xy[:,1]).astype(int)
    tx=(xy[:,0]-x)[:,None];ty=(xy[:,1]-y)[:,None];x1=np.minimum(x+1,1023);y1=np.minimum(y+1,1023)
    return (texture[y,x]*(1-tx)+texture[y,x1]*tx)*(1-ty)+(texture[y1,x]*(1-tx)+texture[y1,x1]*tx)*ty


def raster(projected,triangles,indices):
    z=np.full((SIZE,SIZE),np.inf,np.float32);ids=np.full((SIZE,SIZE),-1,np.int32);bary=np.zeros((SIZE,SIZE,3),np.float32)
    for index in indices:
        a,b,c=projected[triangles[index]]
        low=np.maximum(0,np.floor(np.minimum(np.minimum(a,b),c)[:2]).astype(int))
        high=np.minimum(SIZE,np.ceil(np.maximum(np.maximum(a,b),c)[:2]).astype(int))
        x0,y0=low;x1,y1=high
        if x1<=x0 or y1<=y0:continue
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
        w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1
        depth=w0*a[2]+w1*b[2]+w2*c[2]
        hit=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)&(depth<z[y0:y1,x0:x1])
        if not hit.any():continue
        z[y0:y1,x0:x1][hit]=depth[hit];ids[y0:y1,x0:x1][hit]=index
        bary[y0:y1,x0:x1][hit]=np.stack((w0,w1,w2),axis=-1)[hit]
    return z,ids,bary


report={'variant':SEX,'view':VIEW,'frames':0,'minimum_margin':SIZE,'normal_error':0.,'clips':{},
        'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()}
record={'variant':SEX,'view':VIEW,'cell':SIZE,'pivot':pivot,'camera_rotation':list(camera.rotation_euler),
        'camera_location':list(camera.location),'ortho_scale':camera.data.ortho_scale,'yaw':yaw,
        'height_range':[-SL,SL],'passes':PASSES,'clips':{},'physics_poses':{}}
started=time.perf_counter()
for action in DESIGNS:
    if ONLY and ONLY!=action:continue
    atlases={p:np.zeros((CELL*3,CELL*6,4),np.uint8) for p in PASSES}
    family='surface' if action.startswith('surface_') else 'air' if action in ('breach_launch','airborne_arc','water_reentry','out_of_water') else 'swim'
    cell_index=0
    for phase in PHASES:
        clip_key=f'{SEX}/{action}/{phase}';motion_id=f'{SEX}_{action}_{phase}'
        directory=ROOT/f'2D/{family}/{motion_id}/{VIEW}';directory.mkdir(parents=True,exist_ok=True)
        cell_records=[];preview=[]
        for sample in samples(action,phase):
            rig=select_pose(SEX,action,phase,sample['u'])
            evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
            points=[evaluated.matrix_world@v.co for v in mesh.vertices];verts=np.array(points)
            triangles=np.array([t.vertices[:] for t in mesh.loop_triangles]);loops=np.array([t.loops[:] for t in mesh.loop_triangles])
            uv=np.array([d.uv[:] for d in mesh.uv_layers.active.data]);material=np.array([t.material_index for t in mesh.loop_triangles])
            normal_matrix=np.array(evaluated.matrix_world.to_3x3().inverted().transposed())
            normals=np.array([v.normal[:] for v in mesh.vertices])@normal_matrix.T
            normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-9)
            coords=(verts-cam)@axes.T;projected=np.column_stack((SIZE/2+coords[:,0]*PIXELS_PER_BU,SIZE/2-coords[:,1]*PIXELS_PER_BU,-coords[:,2]))
            tree=BVHTree.FromPolygons(points,[tuple(t) for t in triangles],all_triangles=True)
            ao=np.ones(len(verts),np.float32)
            directions=[Vector((0,0,1)),Vector((.6,0,.8)),Vector((-.6,0,.8)),Vector((0,.6,.8)),Vector((0,-.6,.8))]
            for i,point in enumerate(points):
                normal=Vector(normals[i]);rotation=normal.to_track_quat('Z','Y')
                ao[i]=1-.5*sum(tree.ray_cast(point+normal*.0003*SL,rotation@direction,.035*SL)[0] is not None for direction in directions)/5
            z_opaque,id_opaque,b_opaque=raster(projected,triangles,np.flatnonzero(material!=1))
            z_fin,id_fin,b_fin=raster(projected,triangles,np.flatnonzero(material==1))
            mask=id_opaque>=0;fin=(id_fin>=0)&(z_fin<z_opaque);coverage=mask|fin
            lin=np.zeros((SIZE,SIZE,3));normal=np.zeros_like(lin);height=np.zeros((SIZE,SIZE));ambient=np.ones((SIZE,SIZE));rough=np.zeros((SIZE,SIZE));eye=np.zeros((SIZE,SIZE),bool);texuv=np.zeros((SIZE,SIZE,2))
            alpha=mask.astype(float)
            for ids,bary,active,is_fin in ((id_opaque,b_opaque,mask,False),(id_fin,b_fin,fin,True)):
                ii=ids[active];weights=bary[active];tt=triangles[ii]
                tex=np.sum(uv[loops[ii]]*weights[:,:,None],axis=1);colors=sample_texture(tex)
                nn=np.sum(normals[tt]*weights[:,:,None],axis=1)@axes.T;nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-9)
                if is_fin:
                    amount=np.where(mask[active],.84,1.)[:,None];lin[active]=colors*amount+lin[active]*(1-amount)
                    alpha[active]=np.where(mask[active],1,.84)
                else:lin[active]=colors
                normal[active]=nn;height[active]=np.sum(verts[tt,2]*weights,axis=1)
                ambient[active]=np.sum(ao[tt]*weights,axis=1)
                rough[active]=.56 if is_fin else np.choose(material[ii],[.73,.56,.35,.85])
                eye[active]=material[ii]==2;texuv[active]=tex
            maps={p:np.zeros((SIZE,SIZE,4),np.uint8) for p in PASSES}
            for p in PASSES[2:]:maps[p][:,:,3]=255
            surface_alpha=np.rint(alpha*255).astype(np.uint8)
            maps['base'][:,:,:3]=np.rint(linear_to_srgb(lin)*255).astype(np.uint8);maps['base'][:,:,3]=surface_alpha
            maps['normal'][:,:,:3]=np.rint((normal*.5+.5)*255).astype(np.uint8)
            maps['ao'][:,:,:3]=np.rint(ambient[:,:,None]*255).astype(np.uint8)
            maps['orm'][:,:,0]=np.rint(ambient*255).astype(np.uint8);maps['orm'][:,:,1]=np.rint(rough*255).astype(np.uint8)
            depth=np.rint(np.clip((height+SL)/(2*SL),0,1)*65535).astype(np.uint16)
            maps['depth'][:,:,0]=(depth>>8).astype(np.uint8);maps['depth'][:,:,1]=(depth&255).astype(np.uint8)
            maps['watermask'][:,:,0]=np.where(coverage&(height>0),255,0);maps['watermask'][:,:,1]=np.where(coverage&(height<=0),255,0)
            # Reference-directed soft fill affects Sprite only; data normals stay physical.
            light=np.array([.10,-.35,.93]);light/=np.linalg.norm(light)
            wrap=np.where(fin,2.,.25)
            dot=np.clip((normal@light+wrap)/(1+wrap),0,1);band=np.digitize(dot,[.14,.42,.72])
            multipliers=np.array([[.36,.42,.51],[.53,.60,.66],[.73,.77,.80],[.95,.95,.92]])
            colors=np.rint(linear_to_srgb(lin*multipliers[band])*255).astype(np.uint8)
            body=mask&~fin&~eye&(id_opaque>=0)
            indices=id_opaque[body];body_values=colors[body]
            nearest=np.argmin(np.sum((body_values[:,None,:].astype(float)-PALETTE[None,:,:])**2*np.array([.25,.60,.15]),axis=2),axis=1)
            body_values[material[indices]==0]=PALETTE[nearest[material[indices]==0]];colors[body]=body_values
            glint=eye&((((texuv[:,:,0]-.815)/.017)**2+((texuv[:,:,1]-.48)/.022)**2<1)|(((texuv[:,:,0]-.925)/.017)**2+((texuv[:,:,1]-.48)/.022)**2<1))
            gain=min(1,float(eye.sum())/32)
            colors[glint]=np.rint(np.array([243,241,230])*gain).astype(np.uint8)
            maps['emissive'][glint,:3]=np.rint(255*.12*gain).astype(np.uint8)
            maps['sprite'][:,:,:3]=colors;maps['sprite'][:,:,3]=surface_alpha
            padded=np.pad(coverage,2);dilated=np.zeros_like(coverage)
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if dx*dx+dy*dy<=5:dilated|=padded[2+dy:2+dy+SIZE,2+dx:2+dx+SIZE]
            maps['sprite'][dilated&~coverage]=[34,49,59,255]
            yy,xx=np.where(dilated);bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
            yy,xx=np.where(coverage);basebox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
            margin=min(bbox[0],bbox[1],SIZE-bbox[2],SIZE-bbox[3]);assert margin>=8,(clip_key,VIEW,sample['index'],margin)
            report['minimum_margin']=min(report['minimum_margin'],margin)
            decoded=maps['normal'][:,:,:3][coverage]/255*2-1;error=float(np.max(abs(np.linalg.norm(decoded,axis=1)-1)))
            assert error<.015;report['normal_error']=max(report['normal_error'],error)
            markers={}
            for name in ('mouth_tip','body_ref','attack_socket','SL_snout','SL_tail'):
                world=rig.matrix_world@rig.pose.bones[name].head;p=(np.array(world)-cam)@axes.T
                markers[name]={'world':list(inverse_yaw@world),'xy':[float(SIZE/2+p[0]*PIXELS_PER_BU),float(SIZE/2-p[1]*PIXELS_PER_BU)]}
            ax=cell_index%6*CELL+2;ay=cell_index//6*CELL+2
            for p,array in maps.items():atlases[p][ay:ay+SIZE,ax:ax+SIZE]=array
            relative=f'2D/{family}/{motion_id}/{VIEW}/{sample["index"]}.png'
            png(ROOT/relative,np.concatenate(list(maps.values())),False)
            preview.append(maps['sprite'])
            pose_id=f'{SEX}/{action}/{phase}/{sample["index"]}'
            cell_records.append({**sample,'file':relative,'rect':[ax,ay,SIZE,SIZE],'bbox':bbox,'base_bbox':basebox,
                                 'markers':markers,'eye_pixels':int(eye.sum()),'glint_pixels':int(glint.sum()),'pose_id':pose_id})
            if VIEW=='left':
                body_points=np.array([inverse_yaw@p for p in points[:PROFILE['body_vertices']]])
                all_points=np.array([inverse_yaw@p for p in points])
                body_tris=[list(map(int,t)) for t in triangles if max(t)<PROFILE['body_vertices']]
                record['physics_poses'][pose_id]={'vertices':all_points.round(6).tolist(),'bounds':[all_points.min(axis=0).tolist(),all_points.max(axis=0).tolist()],
                    'body_bounds':[body_points.min(axis=0).tolist(),body_points.max(axis=0).tolist()],
                    'mouth_tip':markers['mouth_tip']['world'],'body_ref':markers['body_ref']['world']}
                record['body_triangles']=body_tris
                record['triangles']=triangles.tolist()
            evaluated.to_mesh_clear();cell_index+=1;report['frames']+=1
        apng(OUT/f'{motion_id}_{VIEW}.png',preview,[s['duration'] for s in samples(action,phase)],phase=='mid' and action in ('hover_or_school','cruise','forage_cruise','surface_gape'))
        record['clips'][clip_key]={'samples':cell_records,'pass_files':{p:f'{SEX}_{action}_{VIEW}_{p}.png' for p in PASSES}}
    for p,array in atlases.items():png(OUT/f'{SEX}_{action}_{VIEW}_{p}.png',array,p in ('sprite','base'))
    report['clips'][action]=cell_index
    print(f'EXPORT {SEX}/{VIEW}/{action}: {cell_index} cells',flush=True)
report.update(status='PASS',seconds=time.perf_counter()-started)
suffix=f'{SEX}_{VIEW}'+('_'+ONLY if ONLY else '')
(OUT/f'part_{suffix}.json').write_text(json.dumps(record,separators=(',',':')),encoding='utf-8')
(OUT/f'validation_{suffix}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
