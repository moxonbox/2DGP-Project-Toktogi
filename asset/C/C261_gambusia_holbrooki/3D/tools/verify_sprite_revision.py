"""Pixel-level r03 contract: palette, registration and measured model/data changes."""
import hashlib,json,sys,time,zlib,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2]
OLD=Path(sys.argv[1])
def pixels(path):
    data=path.read_bytes();offset=8;parts=[]
    while offset<len(data):
        n=struct.unpack('>I',data[offset:offset+4])[0];tag=data[offset+4:offset+8];blob=data[offset+8:offset+8+n]
        if tag==b'IHDR':w,h=struct.unpack('>II',blob[:8]);assert blob[8:10]==b'\x08\x06'
        if tag==b'IDAT':parts.append(blob)
        offset+=n+12
    raw=np.frombuffer(zlib.decompress(b''.join(parts)),np.uint8).reshape(h,w*4+1)
    assert not raw[:,0].any()
    return raw[:,1:].reshape(8,w,w,4)

old=json.loads((OLD/'2D/gambusia-r01/manifest.json').read_text())
new=json.loads((ROOT/'2D/gambusia-r03/manifest.json').read_text())
palette=np.array([list(bytes.fromhex(h)) for h in new['contract']['palette']['sRGB']],np.uint8)
assert old['variants']==new['variants'] and old['views']==new['views']
assert old['contract']['palette']==new['contract']['palette']
report={'status':'PASS','frames':0,'changed_pixels_by_pass':dict.fromkeys(new['passes'],0),
        'alpha_changed_pixels':0,'max_alpha_change_fraction':0.,'markers_pivots_time_equal':True,'body_palette_invalid_pixels':0,'outline_invalid_pixels':0,'body_mean_luma_gain':{},'changed_frames':0,
        'expected_changes':'GPT pigment, larger eyes, outward gill normals, Sprite soft fill and brighter glints; data passes regenerated from corrected model'}
model=json.loads((ROOT/'3D/model_manifest.json').read_text())
report['geometry_outside_eyes_and_gills_max_error_bu']={}
for sex in new['variants']:
    with np.load(OLD/old['geometry'][sex]['file']) as old_data,np.load(ROOT/new['geometry'][sex]['file']) as new_data:
        a=old_data['positions'];b=new_data['positions'];assert a.shape==b.shape
        assert np.array_equal(old_data['pose_ids'],new_data['pose_ids'])
        allowed=np.zeros(a.shape[1],bool)
        for part in model['variants'][sex]['parts']:
            if part['name'].startswith(('eye_','operculum_')):allowed[part['first_vertex']:part['first_vertex']+part['vertex_count']]=True
        error=float(np.max(abs(a[:,~allowed]-b[:,~allowed])));assert error<1e-6,(sex,error)
        report['geometry_outside_eyes_and_gills_max_error_bu'][sex]=error
totals={sex:[0.,0.,0] for sex in new['variants']};started=time.perf_counter()
for key,clip in new['clips'].items():
    sex=key.split('/')[0];prior=old['clips'][key]
    assert clip['duration']==prior['duration'] and clip['loop']==prior['loop']
    for view,info in clip['views'].items():
        before=prior['views'][view]
        for sample,old_sample in zip(info['samples'],before['samples'],strict=True):
            for field in ('index','u','duration','file','rect','markers','pose_id'):
                assert sample[field]==old_sample[field],(key,view,field)
            name=sample['file'];a=pixels(OLD/name);b=pixels(ROOT/name)
            for i,p in enumerate(new['passes']):report['changed_pixels_by_pass'][p]+=int(np.count_nonzero(np.any(a[i]!=b[i],axis=-1)))
            alpha_change=a[1,...,3]!=b[1,...,3]
            fraction=float(np.count_nonzero(alpha_change)/np.count_nonzero(b[1,...,3]))
            assert fraction<.05,(name,'silhouette drift',fraction)
            report['max_alpha_change_fraction']=max(report['max_alpha_change_fraction'],fraction)
            report['alpha_changed_pixels']+=int(np.count_nonzero(alpha_change))
            assert np.all(b[2:,...,3]==255),(name,'data alpha')
            body=(b[1,...,3]>0)&(b[4,...,1]==round(.73*255))
            colors=b[0,...,:3][body]
            invalid=np.count_nonzero(~np.any(np.all(colors[:,None,:]==palette[None,:,:],axis=2),axis=1))
            assert invalid==0,(name,'palette',invalid)
            outline=(b[0,...,3]>0)&(b[1,...,3]==0)
            assert np.all(b[0,...,:3][outline]==[34,49,59]),(name,'outline')
            assert np.any(a[0]!=b[0]),(name,'no visual change')
            totals[sex][0]+=float(np.sum(a[0,...,:3][body]*np.array([.2126,.7152,.0722])))
            totals[sex][1]+=float(np.sum(colors*np.array([.2126,.7152,.0722])));totals[sex][2]+=len(colors)
            report['frames']+=1;report['changed_frames']+=1
for sex,(a,b,count) in totals.items():
    assert b>a;report['body_mean_luma_gain'][sex]={'r01':a/count,'r03':b/count,'gain':(b-a)/count}
report['seconds']=time.perf_counter()-started
(ROOT/'document/sprite_revision_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
board=Image.new('RGBA',(1280,1280),(58,71,78,255));d=ImageDraw.Draw(board)
for row,(sex,action,view) in enumerate((('female','hover_or_school','left'),('male','hover_or_school','right'))):
    for col,root in enumerate((OLD,ROOT)):
        sample=new['clips'][f'{sex}/{action}/mid']['views'][view]['samples'][0]
        im=Image.fromarray(pixels(root/sample['file'])[0]);ox=col*640+(640-im.width)//2;oy=row*640+(640-im.height)//2+20
        board.alpha_composite(im,(ox,oy));d.text((col*640+20,row*640+18),f'{sex.upper()} | {"R01 ORIGINAL" if col==0 else "R03 GPT IMAGE / PIPELINE"} | 1x',font=font,fill='white')
board.convert('RGB').save(ROOT/'comparison/sprite_imagegen_before_after.png')
ImageOps.grayscale(board).save(ROOT/'comparison/sprite_imagegen_before_after_gray.png')
print(json.dumps(report,indent=2))
