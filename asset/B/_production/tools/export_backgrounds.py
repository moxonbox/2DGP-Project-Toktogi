"""Static rectangular five-pass cells; raster math reused from C261 export_fish.py."""
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
from mathutils import Vector, Euler

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from png_codec import png, srgb_to_linear, linear_to_srgb

PASSES=('sprite','base','normal','rm','emissive')
PPBU=128/1.78
VIEWS={'game':Euler((1.195510983467102,0,-.5700404644012451)).to_quaternion()}
for name,direction in [('front',(-1,0,0)),('back',(1,0,0)),('left',(0,1,0)),('right',(0,-1,0)),('top',(0,0,-1)),('underside',(0,0,1))]:
    VIEWS[name]=Vector(direction).to_track_quat('-Z','Y')


def raster(projected, triangles, width, height):
    z=np.full((height,width),np.inf,np.float32)
    ids=np.full((height,width),-1,np.int32)
    bary=np.zeros((height,width,3),np.float32)
    for index,(a,b,c) in enumerate(projected[triangles]):
        x0,y0=np.maximum(0,np.floor(np.minimum(np.minimum(a,b),c)[:2]).astype(int))
        x1,y1=np.minimum([width,height],np.ceil(np.maximum(np.maximum(a,b),c)[:2]).astype(int))
        if x1<=x0 or y1<=y0:continue
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
        w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        w2=1-w0-w1;depth=w0*a[2]+w1*b[2]+w2*c[2]
        hit=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7)&(depth<z[y0:y1,x0:x1])
        if hit.any():
            z[y0:y1,x0:x1][hit]=depth[hit];ids[y0:y1,x0:x1][hit]=index
            bary[y0:y1,x0:x1][hit]=np.stack((w0,w1,w2),axis=-1)[hit]
    return ids,bary


def texture_read(path):
    data=path.read_bytes();offset=8;payload=b''
    while offset<len(data):
        n=struct.unpack('>I',data[offset:offset+4])[0];tag=data[offset+4:offset+8];blob=data[offset+8:offset+8+n]
        if tag==b'IHDR':w,h=struct.unpack('>II',blob[:8])
        if tag==b'IDAT':payload+=blob
        offset+=n+12
    rows=np.frombuffer(zlib.decompress(payload),np.uint8).reshape(h,w*4+1)
    assert not rows[:,0].any(),'Source PNG must use the preserved zero-filter codec.'
    return srgb_to_linear(np.flipud(rows[:,1:].reshape(h,w,4))[:,:,:3]/255.)


def bounds(mask):
    yy,xx=np.where(mask)
    assert len(xx),'Empty render'
    return [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]


def export(config):
    directory=ROOT/config['folder'];blend=directory/'3D'/f'{config["name"]}_r01.blend'
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    model=json.loads(bpy.data.texts['ASSET_MANIFEST.json'].as_string())
    texture=texture_read(directory/'3D'/model['texture'])
    verts=[];normals=[];triangles=[];uvs=[];roles=[];parts=[]
    for item in sorted(bpy.context.scene.objects,key=lambda o:o.name):
        if item.type!='MESH':continue
        data=item.data;data.calc_loop_triangles();offset=len(verts)
        verts.extend(tuple(item.matrix_world@v.co) for v in data.vertices)
        normal_matrix=item.matrix_world.to_3x3().inverted().transposed()
        normals.extend(tuple((normal_matrix@v.normal).normalized()) for v in data.vertices)
        for tri in data.loop_triangles:
            triangles.append(tuple(offset+i for i in tri.vertices));roles.append(tri.material_index)
            uvs.append([tuple(data.uv_layers.active.data[i].uv) for i in tri.loops])
        parts.append({'name':item.name,'vertices':len(data.vertices),'triangles':len(data.loop_triangles)})
    verts=np.array(verts);normals=np.array(normals);triangles=np.array(triangles);uvs=np.array(uvs);roles=np.array(roles)
    assert np.isfinite(verts).all() and np.isfinite(uvs).all()
    assert uvs.min()>=0 and uvs.max()<=1
    assert len(triangles)==model['triangles']
    cross=np.cross(verts[triangles[:,1]]-verts[triangles[:,0]],verts[triangles[:,2]]-verts[triangles[:,0]])
    assert np.min(np.linalg.norm(cross,axis=1))>1e-12,'Degenerate triangle'
    manifest={'schema':'toktogi.background/1','asset_id':config['name'],'folder_id':config['id'],
              'revision':'background-r01','passes':PASSES,'source_blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
              'static':True,'interaction':False,'collision':None,'events':[],
              'scale':{k:model[k] for k in ('selected_length_mm','presentation_factor','measure_kind','scale_policy','length_bu','bu_per_pixel','game_scale')},
              'filter':'nearest','alpha':'straight','mirror_allowed':False,'views':{},'files':{},
              'channels':{'sprite':'sRGB, four bands, role palette; outline #22313B radius 2 except attached coatings',
                          'base':'unlit sRGB + surface coverage Alpha',
                          'normal':'linear UNORM; R right, G up, B toward camera; A=255; mask Base A',
                          'rm':'linear R roughness G metallic=0 B=0 A=255; mask Base A',
                          'emissive':'linear black RGB A=255; mask Base A'},
              'lighting':{'direction':[-.36,.57,.73],'thresholds':[.14,.42,.72],
                          'linear_multipliers':[[.36,.42,.51],[.53,.60,.66],[.73,.77,.80],[.95,.95,.92]],
                          'shared_runtime_comparison':{'power':.82,'ambient':.34}},
              'status':{'production':'exported','standalone_loader':'pending','main_game':'not_integrated','DEC-06':'deferred'}}
    report={'reopened_blend':True,'parts':parts,'triangles':len(triangles),'bones':0,'views':{},
            'uv_finite_in_bounds':True,'degenerate_triangles':0,'external_files':{},'mcp':'connection_timeout_cli_fallback'}
    for image in bpy.data.images:
        if image.source=='FILE':
            resolved=Path(bpy.path.abspath(image.filepath))
            assert resolved.exists(),str(resolved)
            assert image.packed_file,'Packed image missing'
            digest=hashlib.sha256(resolved.read_bytes()).hexdigest()
            assert hashlib.sha256(bytes(image.packed_file.data)).hexdigest()==digest,'Packed/external image mismatch'
            report['external_files'][image.name]={'relative':image.filepath,'sha256':digest,'packed_matches':True}
    palette_colors=np.array([list(bytes.fromhex(c)) for c in model['palette_roles'].values()])/255
    band_gains=np.array(manifest['lighting']['linear_multipliers'])
    palettes=np.rint(linear_to_srgb(srgb_to_linear(palette_colors)[:,None,:]*band_gains[None,:,:])*255).astype(np.uint8)
    for view,q in VIEWS.items():
        started=time.perf_counter();axes=np.array([q@Vector(v) for v in ((1,0,0),(0,1,0),(0,0,1))])
        coords=verts@axes.T;low=coords[:,:2].min(0);high=coords[:,:2].max(0);center=(low+high)/2
        width,height=(np.ceil(((high-low)*PPBU+28)/16)*16).astype(int)
        width,height=int(width),int(height)
        assert width<=4096 and height<=4096,(view,width,height)
        projected=np.column_stack((width/2+(coords[:,0]-center[0])*PPBU,height/2-(coords[:,1]-center[1])*PPBU,-coords[:,2]))
        ids,bary=raster(projected,triangles,width,height);coverage=ids>=0
        ii=ids[coverage];weights=bary[coverage];active_uv=np.sum(uvs[ii]*weights[:,:,None],axis=1)
        xy=np.clip(active_uv,0,1)*511;x=np.floor(xy[:,0]).astype(int);y=np.floor(xy[:,1]).astype(int)
        tx=(xy[:,0]-x)[:,None];ty=(xy[:,1]-y)[:,None];x1=np.minimum(x+1,511);y1=np.minimum(y+1,511)
        linear=(texture[y,x]*(1-tx)+texture[y,x1]*tx)*(1-ty)+(texture[y1,x]*(1-tx)+texture[y1,x1]*tx)*ty
        nn=np.sum(normals[triangles[ii]]*weights[:,:,None],axis=1)@axes.T
        nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-10)
        nn[nn[:,2]<0]*=-1
        maps={p:np.zeros((height,width,4),np.uint8) for p in PASSES}
        alpha=178 if config['id']=='B0A' else 216 if config['id']=='B0B' else 255
        maps['base'][coverage,:3]=np.rint(linear_to_srgb(linear)*255).astype(np.uint8);maps['base'][coverage,3]=alpha
        for p in PASSES[2:]:maps[p][:,:,3]=255
        maps['normal'][:,:,:3]=(128,128,255);maps['normal'][coverage,:3]=np.rint((nn*.5+.5)*255).astype(np.uint8)
        maps['rm'][coverage,0]=np.where(roles[ii]<12,199,158)
        band=np.digitize(np.clip(nn@np.array([-.36,.57,.73]),0,1),[.14,.42,.72])
        raw=np.rint(linear_to_srgb(linear*band_gains[band])*255).astype(np.uint8)
        options=palettes[roles[ii]]
        nearest=np.argmin(np.sum((raw[:,None,:].astype(float)-options)**2*np.array([.25,.60,.15]),axis=2),axis=1)
        maps['sprite'][coverage,:3]=options[np.arange(len(ii)),nearest];maps['sprite'][coverage,3]=alpha
        outline=config['id'] not in ('B0A','B0B');dilated=coverage.copy()
        if outline:
            padded=np.pad(coverage,2)
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if dx*dx+dy*dy<=5:dilated|=padded[2+dy:2+dy+height,2+dx:2+dx+width]
            maps['sprite'][dilated&~coverage]=(34,49,59,255)
        box= bounds(dilated);basebox=bounds(coverage);margin=min(box[0],box[1],width-box[2],height-box[3])
        assert margin>=8,(config['id'],view,margin)
        decoded=maps['normal'][coverage,:3]/255*2-1;error=float(np.max(abs(np.linalg.norm(decoded,axis=1)-1)))
        assert error<.015
        pivot=[float(width/2-center[0]*PPBU),float(height/2+center[1]*PPBU)]
        anchors={}
        for label,point in model['anchors_bu'].items():
            plane=np.array(point)@axes.T
            anchors[label]=[float(width/2+(plane[0]-center[0])*PPBU),float(height/2-(plane[1]-center[1])*PPBU)]
        folder=directory/f'2D/static/static/{view}';folder.mkdir(parents=True,exist_ok=True)
        stacked=folder/'0.png';png(stacked,np.concatenate([maps[p] for p in PASSES]),False)
        display=directory/f'2D/previews/{view}.png';display.parent.mkdir(exist_ok=True);png(display,maps['sprite'],True)
        if view in ('game','top'):
            checker=np.zeros((height,width,4),np.uint8)
            stripe=(np.floor(active_uv[:,0]*64)+np.floor(active_uv[:,1]*64)).astype(int)%2
            checker[coverage,:3]=np.where(stripe[:,None],np.array([52,101,151]),np.array([226,229,212]))
            checker[coverage,3]=255
            checkpath=directory/f'2D/review/uv_checker_{view}.png';checkpath.parent.mkdir(exist_ok=True);png(checkpath,checker,True)
        files={}
        for p in PASSES:
            path=directory/f'2D/passes/{view}/{p}.png';path.parent.mkdir(parents=True,exist_ok=True);png(path,maps[p],p in ('base','sprite'))
            relative=path.relative_to(directory).as_posix();files[p]=relative;manifest['files'][relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        relative=stacked.relative_to(directory).as_posix();manifest['files'][relative]=hashlib.sha256(stacked.read_bytes()).hexdigest()
        manifest['views'][view]={'file':relative,'cell':[width,height],'pass_files':files,'pivot':pivot,'bbox':box,'base_bbox':basebox,
                                 'sample':0,'sample_time_s':0,'phase':'mid','duration_s':None,'static_hold':True,
                                 'anchors':anchors,'rotation_quaternion':list(q),'camera_center_plane_bu':center.tolist(),
                                 'ortho_scale':max(width,height)/PPBU,'rect':[0,0,width,height],'outline_px':2 if outline else 0}
        report['views'][view]={'cell':[width,height],'margin':margin,'normal_error':error,'surface_pixels':int(coverage.sum()),'seconds':time.perf_counter()-started}
        print(config['id'],view,width,height,flush=True)
    report['decoded_rgba_bytes']=sum(v['cell'][0]*v['cell'][1]*4*5 for v in manifest['views'].values())
    report['status']='PASS_NUMERIC_PRODUCTION'
    (directory/'2D/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'2D/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'id':config['id'],'views':len(VIEWS),'decoded_rgba_bytes':report['decoded_rgba_bytes']}


if __name__=='__main__':
    selected=globals().get('ONLY',sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    configs=json.loads((ROOT/'_production/assets.json').read_text(encoding='utf-8'))
    result=[export(c) for c in configs if not selected or c['id'] in selected]
    print(json.dumps(result),flush=True)
